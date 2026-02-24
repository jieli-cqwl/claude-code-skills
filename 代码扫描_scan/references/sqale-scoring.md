# SQALE Scoring & Detection Rules Reference

> 本文件从 `SKILL.md` 拆出，包含 SQALE 评分标准和各维度详细检测规则。

---

### Agent1: 铁律检测

> 检测规则来源：`~/.claude/reference/代码质量.md`

**降级逻辑**：

| 语言 | 检测模式 |
|------|---------|
| Java | `orElse(null)`, `orElseGet(() -> null)`, `catch.*return null` |
| Python | `except:.*pass`, `except.*return None`, `or None$` |
| TypeScript | `?? null`, `\|\| null`, `catch.*return null` |

**修复建议**：
```
❌ 错误：return user or None
✅ 正确：
   if not user:
       raise UserNotFoundError(f"用户 {user_id} 不存在")
   return user

说明：禁止降级是项目铁律。遇到异常应该明确失败，不要静默返回空值。
```

---

**硬编码**：

| 类型 | 检测模式 |
|------|---------|
| URL | `http://localhost`, `127.0.0.1`, `://.*:\d{4,5}` |
| 密钥 | `(api_key\|secret\|password\|token)\s*=\s*"[^"]+"` |
| 配置文件 | `.yml`, `.properties`, `.env` 中的敏感值 |

**修复建议**：
```
❌ 错误：api_key = "sk-xxxx"
✅ 正确：
   # Python
   api_key = os.environ.get("API_KEY")

   # TypeScript
   const apiKey = process.env.API_KEY

   # Java
   @Value("${api.key}") private String apiKey;

说明：敏感配置必须从环境变量或配置中心读取，禁止写在代码里。
```

---

**常量分层**（详见 `~/.claude/reference/硬编码治理规范.md`）：

| 类型 | 检测模式 | 严重程度 |
|------|---------|---------|
| 跨模块导入 | `from src.{module_a}.constants import` 在其他模块中出现 | 🟡 警告 |
| 缺少前缀 | 模块 constants.py 中 `^[A-Z_]+ =` 不带模块前缀 | 🟡 警告 |
| 常量膨胀 | constants.py 行数 > 200 | 🟡 警告 |

**修复建议**：
```
❌ 错误：from src.user.constants import MAX_RETRY  # 在 order 模块中
✅ 正确：
   # 跨模块常量放 src/constants.py
   # 模块内常量放 src/{module}/constants.py 并加前缀
   USER_MAX_RETRY = 3  # 在 src/user/constants.py

说明：常量分层存放，避免模块间耦合。
```

---

**Mock（非测试目录）**：

| 语言 | 检测模式 |
|------|---------|
| Python | `@patch`, `MagicMock`, `Mock(` |
| TypeScript | `vi.fn`, `vi.mock`, `jest.fn`, `jest.mock` |
| Java | `@Mock`, `Mockito.`, `when().thenReturn` |

**修复建议**：
```
❌ 错误：在 src/ 目录下使用 Mock
✅ 正确：
   1. Mock 只能出现在 tests/ 目录
   2. 生产代码必须连接真实服务
   3. 如需隔离，使用依赖注入而非 Mock

说明：禁止 Mock 是项目铁律。测试必须连接真实数据库和服务。
```

---

**输出格式**（含修复建议）：
```
🔴 AuthService.java:45 [硬编码密钥]
   代码：apiKey = "sk-xxx"
   修复：将密钥移到环境变量，使用 @Value("${api.key}") 注入
```

---

### Agent2: 安全漏洞检测

| 类型 | 检测模式 | 严重程度 |
|------|---------|---------|
| SQL 注入 | 字符串拼接 SQL（`"SELECT" +`） | 🔴 严重 |
| XSS | `dangerouslySetInnerHTML`, `innerHTML =` | 🔴 严重 |
| 敏感信息日志 | `log.*(password\|token\|secret)` | 🔴 严重 |
| 未授权接口 | 无权限校验的危险操作 | 🔴 严重 |

**修复建议**：

**SQL 注入**：
```
❌ 错误：query = "SELECT * FROM users WHERE id = " + user_id
✅ 正确：
   # 使用参数化查询
   cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
   # 或使用 ORM
   User.objects.get(id=user_id)
```

**XSS**：
```
❌ 错误：<div dangerouslySetInnerHTML={{__html: userInput}} />
✅ 正确：
   # 使用文本渲染，自动转义
   <div>{userInput}</div>
   # 如必须渲染 HTML，先用 DOMPurify 清洗
   <div dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(userInput)}} />
```

**敏感信息日志**：
```
❌ 错误：logger.info(f"用户登录: password={password}")
✅ 正确：
   logger.info(f"用户登录: user_id={user_id}")  # 只记录非敏感信息
   # 或脱敏处理
   logger.info(f"用户登录: password={password[:2]}***")
```

**未授权接口**：
```
❌ 错误：
   @app.delete("/users/{id}")
   def delete_user(id): ...  # 无权限校验

✅ 正确：
   @app.delete("/users/{id}")
   @require_permission("user:delete")  # 加权限校验
   def delete_user(id, current_user: User = Depends(get_current_user)): ...
```

---

### Agent3: 代码规范检测

| 规则 | 阈值 | 严重程度 |
|------|------|---------|
| 函数长度 | > 40 行 | 🟡 警告 |
| 文件长度 | > 500 行 | 🟡 警告 |
| 空 catch 块 | 存在 | 🟡 警告 |
| 裸 except | 存在 | 🟡 警告 |
| System.out 使用 | 存在 | 🟡 警告 |

**修复建议**：

**函数过长**：
```
❌ 问题：函数超过 40 行
✅ 修复：
   1. 提取子函数：将逻辑块抽成独立函数
   2. 减少嵌套：用 early return 替代多层 if-else
   3. 单一职责：一个函数只做一件事
```

**文件过长**：
```
❌ 问题：文件超过 500 行
✅ 修复：
   1. 按职责拆分：Service、Repository、Utils 分开
   2. 按领域拆分：不同业务逻辑放不同文件
   3. 检查是否有重复代码可抽取
```

**空 catch 块**：
```
❌ 错误：
   try:
       do_something()
   except:
       pass  # 静默吞掉异常

✅ 正确：
   try:
       do_something()
   except SpecificError as e:
       logger.error(f"操作失败: {e}")
       raise  # 或返回明确错误
```

**裸 except**：
```
❌ 错误：except:  # 捕获所有异常，包括 KeyboardInterrupt
✅ 正确：except Exception as e:  # 只捕获业务异常
```

**System.out 使用**：
```
❌ 错误：System.out.println("debug info");
✅ 正确：
   // 使用日志框架
   logger.debug("debug info");
   logger.info("业务信息");
```

---

### Agent4: 技术债统计

| 类型 | 检测模式 | 严重程度 |
|------|---------|---------|
| FIXME | `FIXME:` | 🟡 警告 |
| HACK | `HACK:` | 🟡 警告 |
| TODO | `TODO:` | 🔵 建议 |
| XXX | `XXX:` | 🔵 建议 |
| @Deprecated | 废弃代码 | 🔵 建议 |
| @Disabled 测试 | 禁用的测试 | 🔵 建议 |

**修复建议**：

**FIXME/HACK**：
```
这些标记表示已知的临时方案或问题，应优先处理：
1. 创建 Issue 跟踪，设定修复期限
2. 如果超过 2 周未修复，升级为技术债任务
3. 修复后删除标记
```

**TODO**：
```
TODO 表示待办事项：
1. 评估是否真的需要做
2. 需要的话创建 Issue 或任务
3. 不需要的话直接删除 TODO 注释
4. 禁止留下无人认领的 TODO
```

**@Deprecated 废弃代码**：
```
❌ 问题：废弃代码仍在项目中
✅ 修复：
   1. 检查是否还有调用方
   2. 无调用则直接删除
   3. 有调用则迁移到新 API 后删除
   4. 设定废弃代码的清理期限（建议 1 个月内）
```

**@Disabled 测试**：
```
❌ 问题：测试被禁用，可能掩盖 bug
✅ 修复：
   1. 检查禁用原因（注释里应该有说明）
   2. 如果是临时禁用，修复后启用
   3. 如果测试不再需要，直接删除
   4. 禁止长期保留禁用的测试
```


---

## Phase 3: 汇总报告 - 健康度评分算法

> **设计原则**：采用业界标准的技术债比率（SQALE 模型），考虑代码规模，大项目和小项目公平对待。

**Step 0: 统计代码行数**

```
代码行数统计规则：
- 只统计源代码文件（按语言过滤：.py, .java, .ts, .js, .go, .rs 等）
- 排除空行和纯注释行
- 排除自动忽略目录（node_modules, dist, __pycache__ 等）
- 排除测试目录（tests/, test/, __tests__/）

统计方法：使用 Grep 工具遍历源文件，统计非空行数
```

**Step 1: 计算技术债（修复总时间）**

```
技术债 = Σ(严重问题 × 60分钟) + Σ(警告 × 15分钟) + Σ(建议 × 5分钟)
```

| 问题类型 | 默认修复时间 | 说明 |
|---------|-------------|------|
| 🔴 严重 | 60 分钟 | 安全漏洞、铁律违反，需要仔细修复 |
| 🟡 警告 | 15 分钟 | 代码规范问题，相对简单 |
| 🔵 建议 | 5 分钟 | TODO/FIXME，快速处理 |

**Step 2: 计算技术债比率**

```
技术债比率 = 技术债(分钟) / (有效代码行数 × 0.5分钟/行) × 100%

其中：
- 0.5分钟/行 是业界标准的代码开发成本估算
- 有效代码行数 = max(实际代码行数, 500)
```

> **小项目保护**：代码行数不足 500 行时，按 500 行计算。
> 避免小项目因少量 TODO 就被评为 F 级的不合理情况。

**Step 3: 映射评级（对齐 SonarQube SQALE 标准）**

| 技术债比率 | 评级 | 说明 |
|-----------|------|------|
| ≤5% | A (优秀) | 代码健康，技术债可控 |
| >5% 且 ≤10% | B (良好) | 少量技术债，建议定期清理 |
| >10% 且 ≤20% | C (一般) | 技术债较多，需要计划清理 |
| >20% 且 ≤50% | D (较差) | 技术债严重，影响开发效率 |
| >50% | F (需重构) | 技术债失控，建议重构 |

**示例**：

```
项目 A：1000 行代码，5 个严重问题
- 技术债 = 5 × 60 = 300 分钟
- 开发成本 = 1000 × 0.5 = 500 分钟
- 技术债比率 = 300 / 500 = 60% → F 级

项目 B：10000 行代码，5 个严重问题
- 技术债 = 5 × 60 = 300 分钟
- 开发成本 = 10000 × 0.5 = 5000 分钟
- 技术债比率 = 300 / 5000 = 6% → B 级
```

> 同样 5 个问题，小项目评级低（问题占比高），大项目评级高（问题占比低），这才公平。
