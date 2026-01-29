---
name: qa
command: qa
user_invocable: true
description: 测试验收。独立于开发的测试专家角色，使用金字塔门控架构（单元→集成→E2E），确保测试完成后功能真正可用。在开发检查（/check）之后使用。
---

# 测试验收 (QA) - 金字塔门控版

> **角色**：独立于开发的测试专家，为最终交付质量负责
> **架构**：金字塔门控（Layer 1 → 2 → 3），每层必过才能继续
> **核心改进**：解决"测试通过但功能不可用"的问题
> **前置条件**：已通过 `/check` 开发检查

---

## 文档契约（铁律）

> **原则**：没有输入文档 → 不能执行；没有输出文档 → 不算完成

### 输入文档（门控检查）

| 文档 | 路径 | 必须 | 检查命令 |
|------|------|------|---------|
| **AC 文档** | `docs/需求文档/clarify_[功能名].md` | ✅ 必须 | `ls docs/需求文档/clarify_*.md` |
| **计划文档** | `docs/开发文档/plan_[功能名].md` | ⚠️ 推荐 | `ls docs/开发文档/plan_*.md` |

**门控规则**：
```bash
# 门控检查：AC 文档必须存在（验收基准）
CLARIFY_DOC=$(ls docs/需求文档/clarify_*.md 2>/dev/null | head -1)
if [ -z "$CLARIFY_DOC" ]; then
  echo "❌ 门控失败: AC 文档不存在"
  echo "   修复: 先执行 /clarify 生成需求文档"
  exit 1
fi
echo "✅ AC 文档: $CLARIFY_DOC"

# 检查计划文档（推荐）
PLAN_DOC=$(ls docs/开发文档/plan_*.md 2>/dev/null | head -1)
if [ -z "$PLAN_DOC" ]; then
  echo "⚠️ 计划文档不存在"
else
  echo "✅ 计划文档: $PLAN_DOC"
fi
```

**门控失败处理**：
- AC 文档不存在 → **停止执行**，先执行 `/clarify`

### 输出文档（强制）

| 文档 | 路径 | 用途 |
|------|------|------|
| **QA 报告** | `docs/qa-reports/qa_[功能名].md` | 验收记录和截图证据 |

**输出规则**：
- 未输出 QA 报告 → **不算完成**
- 报告必须包含：金字塔门控结果 + E2E 截图证据

**下游依赖**：
- `/ship` 依赖 QA 通过

---

## 核心理念

**"E2E 是最终仲裁"**：单元测试过了 + 集成测试过了 + E2E 失败 = 整体失败

```
旧架构（并行，问题：各层独立，无最终验收）：
  Agent1 ←→ Agent2 ←→ Agent3 ←→ Agent4
                    ↓
              汇总报告（可能全过但功能不可用）

新架构（金字塔门控，每层必过）：
  Layer 1: 单元测试 ─必须全过─→
  Layer 2: 集成测试 ─必须全过─→
  Layer 3: E2E 验收 ─必须全过─→ ✅ 可交付
                ↑
          任何一层失败 = 整体失败
```

---

## 依赖规范

| 规范文件 | 覆盖内容 |
|---------|---------|
| `~/.claude/reference/测试用例模板.md` | 用例设计方法和模板 |
| `~/.claude/reference/测试Hooks配置.md` | Hooks 配置说明 |
| `~/.claude/reference/代码质量.md` | 项目铁律（禁止 Mock） |

---

## 执行流程

### Phase 0: 测试前审问（快速）

```markdown
## 测试前审问

1. **AC 来源文档？** → [docs/需求文档/clarify_xxx.md]（单一来源）
2. 计划文档路径？→ [docs/开发文档/plan_xxx.md]
3. 涉及哪些模块？→ [前端/后端/数据库]
4. 测试环境就绪？→ [后端端口/前端端口]
5. 测试数据准备好了？→ [真实数据，禁止 Mock]
6. E2E 工具就绪？→ [Claude in Chrome MCP 可用]
```

**任何答案不确定，必须先澄清。**

---

### AC 来源说明（铁律）

> ⚠️ **AC 单一来源**：验收标准来自 `/clarify` 的 AC 表格，不是 `/plan` 的验收场景
> `/plan` 只是引用 `/clarify` 的 AC，不能作为验收的权威来源

**AC 来源文档**：`docs/需求文档/clarify_[功能名].md`

```markdown
## 验收基准（从 /clarify 提取）

| AC-ID | Given | When | Then | 测试方法 |
|-------|-------|------|------|---------|
| AC-1 | 用户已注册 | 正确密码登录 | 跳转首页 | E2E |
| AC-3 | 用户已注册 | 错误密码登录 | 显示错误 | API + E2E |
| AC-5 | 密码=最小值 | 注册 | 成功 | 单元测试 |

**来源**：docs/需求文档/clarify_xxx.md → 4. 验收标准（AC）
```

**铁律**：
- 如果 `/clarify` 的 AC 文档不存在，必须先执行 `/clarify` 生成
- 禁止使用 `/plan` 的验收场景作为唯一验收基准

**测试数据准备（铁律：禁止 Mock）**：

| 准备方式 | 实现 | 适用场景 |
|---------|------|---------|
| **Seed 脚本**（推荐） | `python scripts/seed_test_data.py` | 标准化测试数据，可重复执行 |
| **Fixture 文件** | `tests/fixtures/test_users.json` | 静态测试数据，配合导入脚本 |
| **API 创建** | 在 E2E 前通过 API 创建测试用户 | 动态数据，每次测试前创建 |

**测试账号规范**：
```bash
# 测试账号必须由 seed 脚本或 fixture 创建，禁止手动创建后硬编码
# 示例 seed 脚本：
python -c "
from app.models import User
from app.database import SessionLocal
db = SessionLocal()
test_user = User(email='test@example.com', password_hash='hashed_TestPass123!')
db.add(test_user)
db.commit()
print('✅ 测试用户已创建')
"
```

---

### Phase 1: Layer 1 - 单元测试（门控 1）

**执行内容**：

```bash
# Python 后端
cd backend && pytest tests/unit/ -v --cov=app --cov-report=term-missing

# TypeScript 前端（如有）
cd frontend && npm test -- --coverage
```

**门控条件**（必须全部满足）：

| 条件 | 要求 | 说明 |
|------|------|------|
| 相关测试通过率 | 100% | 本次变更相关的测试必须全过 |
| 代码覆盖率 | ≥ 80% | 变更代码的覆盖率 |
| 无跳过测试 | 0 个 skip | 不允许跳过测试蒙混过关 |

**相关测试识别**：
1. 变更文件对应的测试文件（`login.py` → `test_login.py`）
2. import 了变更模块的测试
3. 变更函数/类被调用的测试

**已知失败处理**：
- 非本次变更相关的测试失败 → 允许标记为 `@pytest.mark.skip(reason="已知问题 #123")`
- 本次变更相关的测试失败 → **阻塞，必须修复**

**失败处理**：
```markdown
❌ Layer 1 单元测试失败

**失败测试**：
- test_login_invalid_email: AssertionError: expected 422, got 400

**处理**：
1. 修复失败的测试或代码
2. 重新执行 /qa
3. 禁止跳过失败测试继续
```

---

### Phase 2: Layer 2 - 集成测试（门控 2）

**前提**：Layer 1 通过

**执行内容**：

```markdown
## 集成测试清单

### 2.1 环境准备

1. **启动后端服务**（测试专用端口 9xxx）
   ```bash
   cd backend && python -m uvicorn app.main:app --port 9000 &
   sleep 3
   curl -f http://localhost:9000/health
   ```

2. **测试数据库隔离**
   - 方式 A：使用独立测试库（推荐）
   - 方式 B：事务回滚（每个测试后回滚）

### 2.2 API 集成测试

对每个 API 端点执行真实调用：
```

**测试端口规范**：
- 开发环境：8xxx（如 8000, 8080）
- 测试环境：9xxx（如 9000, 9080）

**测试数据隔离策略**：

| 方式 | 实现 | 适用场景 |
|------|------|---------|
| 独立测试库 | `DATABASE_URL=test_db` | 推荐，完全隔离 |
| 事务回滚 | 每个测试用事务包裹 | 速度快，但可能有副作用 |
| 数据清理 | teardown 清理测试数据 | 简单，但可能遗漏 |

**执行方式**：

```bash
# 启动测试环境
export DATABASE_URL=postgresql://localhost/test_db
export PORT=9000
cd backend && python -m uvicorn app.main:app --port $PORT &
sleep 3

# 执行集成测试
pytest tests/integration/ -v

# 或手动 API 测试（按用例模板执行）
curl -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123!"}'
```

**门控条件**：

| 条件 | 要求 |
|------|------|
| 所有 API 端点返回预期状态码 | 200/201/400/401 等 |
| 数据库操作正确执行 | CRUD 验证 |
| 无超时、无连接错误 | 响应时间 < 5s |

**失败处理**：
```markdown
❌ Layer 2 集成测试失败

**失败项**：
- POST /api/v1/users: 超时（10s 无响应）

**处理**：
1. 检查服务是否启动
2. 检查数据库连接
3. 使用 /debug 分析原因
4. 修复后重新执行
```

---

### Phase 3: Layer 3 - E2E 验收（最终门控）

**前提**：Layer 1 + Layer 2 通过

**核心理念**：**E2E 是最终仲裁，模拟真实用户操作**

**执行内容**：

```markdown
## E2E 验收测试

### 3.1 环境准备（全栈项目启动顺序）

**启动顺序（严格按此顺序）**：

1. **数据库**（如需要）
   ```bash
   # 确保测试数据库运行
   docker-compose up -d test-db
   sleep 3
   ```

2. **后端服务**（必须先于前端）
   ```bash
   # 使用测试端口，避免与开发环境冲突
   export DATABASE_URL=postgresql://localhost/test_db
   cd backend && python -m uvicorn app.main:app --port 9000 &
   sleep 3
   curl -f http://localhost:9000/health || echo "❌ 后端启动失败，停止 E2E"
   ```

3. **前端服务**（后端就绪后启动）
   ```bash
   # 配置前端 API 地址指向测试后端
   export VITE_API_URL=http://localhost:9000
   cd frontend && npm run dev -- --port 3000 &
   sleep 5
   curl -f http://localhost:3000/ || echo "❌ 前端启动失败，停止 E2E"
   ```

4. **健康检查汇总**
   ```bash
   echo "=== 环境检查 ==="
   curl -sf http://localhost:9000/health && echo "✅ 后端正常" || echo "❌ 后端异常"
   curl -sf http://localhost:3000/ && echo "✅ 前端正常" || echo "❌ 前端异常"
   ```

**环境检查失败处理**：
- 任何服务启动失败 → **停止 E2E**，先修复环境问题
- 禁止在环境不完整时执行 E2E

**E2E 工具不可用处理（铁律）**：

如果 Claude in Chrome MCP 不可用（未安装、连接失败、浏览器崩溃）：

```markdown
❌ E2E 环境不可用

**问题**：Claude in Chrome MCP [具体错误]

**必须解决后才能继续**：
1. 检查 Claude in Chrome 扩展是否已安装
2. 检查 MCP 服务是否正常运行
3. 尝试重启浏览器
4. 参考：https://github.com/anthropics/claude-code/blob/main/docs/mcp.md

**禁止行为**：
- ❌ 跳过 E2E 测试
- ❌ 降级为手动验收
- ❌ 假装 E2E 通过

E2E 是最终仲裁，不可绕过。解决环境问题后重新执行 /qa。
```

### 3.2 执行用户流程

使用 Claude in Chrome MCP 进行真实浏览器测试：

1. 获取浏览器上下文：mcp__claude-in-chrome__tabs_context_mcp
2. 创建新标签页：mcp__claude-in-chrome__tabs_create_mcp
3. 按用例执行操作
4. 每个关键步骤截图留证（按截图存储规范保存）
```

**E2E 重试机制**：

| 失败类型 | 处理 |
|---------|------|
| 页面加载超时 | 等待 3s → 重试（最多 2 次） |
| 元素定位失败 | 等待 3s → 重试（最多 2 次） |
| 断言失败（逻辑错误） | **不重试**，直接失败 |
| 连续 3 次失败 | **真失败**，输出最后错误 |

**截图存储规范**：

| 项目 | 规范 |
|------|------|
| 存储目录 | `docs/qa-reports/` |
| 命名格式 | `[用例ID]_step[N]_[描述].png` |
| 示例 | `E2E-001_step1_login-page.png` |
| 保留策略 | **只保留最新一次**（与 RULES.md 一致：旧版测试报告在新版发布时删除） |

**执行示例**：

```markdown
### E2E 用例：用户登录完整流程

**步骤**：
1. 打开 http://localhost:3000/login
2. 输入邮箱：test@example.com
3. 输入密码：TestPass123!
4. 点击"登录"按钮
5. 等待跳转（最多 5s）
6. 验证：页面显示"欢迎回来"

**执行**：
- mcp__claude-in-chrome__navigate: url="http://localhost:3000/login"
- mcp__claude-in-chrome__computer: action="screenshot" → 保存为 E2E-001_step1_login-page.png
- mcp__claude-in-chrome__find: query="email input"
- mcp__claude-in-chrome__form_input: ref=<ref>, value="test@example.com"
- mcp__claude-in-chrome__find: query="password input"
- mcp__claude-in-chrome__form_input: ref=<ref>, value="TestPass123!"
- mcp__claude-in-chrome__find: query="login button"
- mcp__claude-in-chrome__computer: action="left_click", ref=<ref>
- mcp__claude-in-chrome__computer: action="wait", duration=3
- mcp__claude-in-chrome__computer: action="screenshot" → 保存为 E2E-001_step2_after-login.png
- mcp__claude-in-chrome__get_page_text: 验证包含"欢迎回来"

**结果**：✅ 通过 / ❌ 失败
**截图**：docs/qa-reports/2026-01-28/E2E-001_step*.png
```

**门控条件**：

| 条件 | 要求 |
|------|------|
| 核心用户流程全部走通 | 100% |
| 页面无 console.error | 0 个错误 |
| 有截图证据 | 关键步骤都有截图 |

---

### Phase 4: 汇总测试报告

```markdown
# /qa 测试报告（金字塔门控版）

**测试日期**：YYYY-MM-DD HH:mm
**关联文档**：PRD_xxx.md / plan_xxx.md

---

## 金字塔门控结果

| Layer | 测试类型 | 结果 | 详情 |
|-------|---------|------|------|
| 1 | 单元测试 | ✅ 通过 | 15/15 passed, 覆盖率 85% |
| 2 | 集成测试 | ✅ 通过 | 8/8 API 端点正常 |
| 3 | E2E 验收 | ✅ 通过 | 3/3 用户流程走通 |

---

## Layer 1: 单元测试详情

```
$ pytest tests/unit/ -v --cov=app
==================== 15 passed in 2.3s ====================
Coverage: 85%
```

**相关测试**：全部通过
**覆盖率**：85% ≥ 80% ✅

---

## Layer 2: 集成测试详情

| API 端点 | 方法 | 预期 | 实际 | 状态 |
|---------|------|------|------|------|
| /api/v1/auth/login | POST | 200 | 200 | ✅ |
| /api/v1/users | GET | 200 | 200 | ✅ |
| /api/v1/users | POST | 201 | 201 | ✅ |

**测试端口**：9000
**数据库**：test_db（隔离）

---

## Layer 3: E2E 验收详情

| 用例 | 描述 | 结果 | 截图 |
|------|------|------|------|
| E2E-001 | 用户登录流程 | ✅ | [img_001, img_002] |
| E2E-002 | 用户注册流程 | ✅ | [img_003, img_004] |
| E2E-003 | 密码重置流程 | ✅ | [img_005, img_006] |

**重试次数**：0（一次通过）

---

## 质量签字

| 条件 | 要求 | 结果 |
|------|------|------|
| Layer 1 单元测试 | 相关测试 100% 通过 | ✅ |
| Layer 1 覆盖率 | ≥ 80% | ✅ 85% |
| Layer 2 集成测试 | 所有 API 正常 | ✅ |
| Layer 3 E2E | 核心流程走通 | ✅ |
| 阻塞性缺陷 | 0 个 | ✅ |

---

## 结论

✅ **测试通过** - 可以执行 `/ship`

或

❌ **测试不通过** - 需要修复：

| Layer | 问题 | 修复方式 |
|-------|------|---------|
| 1 | test_xxx 失败 | 修复代码或测试 |
| 2 | API /xxx 超时 | 检查数据库连接 |
| 3 | 登录后未跳转 | 检查前端路由 |
```

---

## 测试用例设计

### 从验收场景到测试用例（核心流程）

**分工**：

| 阶段 | 内容 | 格式 | 编写者 |
|------|------|------|--------|
| **/plan** | 验收场景（业务语言） | Given-When-Then | 业务+开发+QA 协作 |
| **/qa** | 测试用例（技术执行） | 具体输入/输出/命令 | QA/开发 |

**转化示例**：

```
/plan 验收场景（AC-1）：
  Given: 用户已注册，邮箱 test@example.com
  When: 输入正确密码，点击登录
  Then: 跳转首页，显示"欢迎回来"

    ↓ /qa 转化为测试用例

API 用例（API-001）：
  curl -X POST http://localhost:9000/api/auth/login \
    -d '{"email":"test@example.com","password":"TestPass123!"}'
  预期：200, {"access_token": "..."}

E2E 用例（E2E-001）：
  1. 打开 http://localhost:3000/login
  2. 输入邮箱、密码
  3. 点击登录
  4. 验证页面包含"欢迎回来"
```

### 用例设计清单

**必须使用专业方法设计用例**，参考 `~/.claude/reference/测试用例模板.md`：

| 方法 | 必须覆盖 | 对应 AC 类型 |
|------|---------|-------------|
| 正常流程 | Happy Path，核心功能 | AC 正常流程 |
| 等价类 | 有效/无效输入类 | AC 异常流程 |
| 边界值 | min-1, min, min+1, max-1, max, max+1 | AC 边界情况 |
| 异常场景 | 空值、特殊字符、超长输入 | AC 异常流程 |

### 用例格式要求

**每个用例必须包含**：
- 具体输入（不是描述）
- 具体预期（不是描述）
- 可执行命令

**示例**：
```markdown
### 用例 API-001: 正常登录

**输入**：
- email: "test@example.com"
- password: "ValidPass123!"

**预期**：
- status_code: 200
- body.access_token: 非空字符串

**命令**：
curl -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "ValidPass123!"}'
```

---

## ⛔ 边界约束（铁律）

> **`/qa` 的职责边界：只做测试验收，不能跳过验收失败**

| 禁止行为 | 说明 |
|---------|------|
| ❌ 验收失败时继续进入 `/ship` | 必须全部测试通过才能交付 |
| ❌ 跳过某个 Layer 的失败 | 金字塔门控：每层必过 |

**正确的完成动作**：
1. 输出 QA 报告到 `docs/qa-reports/qa_[功能名].md`
2. 展示完成提示
3. 进入下一环节 `/ship`（正常流转）或等待用户指令

**跳过环节的处理**：
- 验收失败不能跳过，必须修复后重新验收

---

## 禁止行为

| 禁止行为 | 原因 |
|---------|------|
| **使用 Mock 数据** | 无法证明真实功能可用 |
| **跳过失败的 Layer** | 门控原则：每层必过 |
| **只测 Happy Path** | 遗漏边界和异常 |
| **用描述代替具体值** | 用例不可执行 |
| **复制预期当实际** | 必须真实执行 |
| **E2E 失败不重试** | 浏览器测试有偶发性 |
| **E2E 断言失败重试** | 逻辑错误不应重试 |

---

## 与其他 Skills 的关系

```
/clarify（需求澄清）
    ↓ 输出 AC 表格（单一来源）
/plan（写计划）
    ↓ 引用 AC
/test-gen from-clarify
    ↓ 从 AC 生成测试
/run-plan（执行计划）
    ↓ 基于测试开发
/check（开发检查）
    ↓ 检查通过后
/qa（测试验收）← 当前（金字塔门控版）
    ↓ **基于 /clarify 的 AC 验收**
/ship（代码交付）
```

### AC 流转链路

```
/clarify 定义 AC（单一来源）
    ↓
/test-gen 从 AC 生成测试
    ↓
/run-plan 基于测试开发
    ↓
/qa 基于 AC 验收 ← 当前
```

**核心原则**：AC 只在 /clarify 定义一次，/qa 验收时必须引用 /clarify 的 AC，不能使用 /plan 重新定义的版本。

---

## Phase 5: 文档清理检查

> **目的**：确保 plan 文档在 /qa 通过后被归档，避免过时文档干扰后续工作

**检查步骤**：

```bash
# 扫描工作目录中的 plan 文档
ls docs/开发文档/plan_*.md 2>/dev/null
```

**处理规则**：

| 情况 | 处理 |
|------|------|
| 存在 plan 文档且 /qa 已通过 | 提示归档到 `docs/archive/` |
| plan 文档是其他功能的（不是本次 /qa 的） | 提示用户确认是否需要归档 |
| 无 plan 文档 | 跳过 |

**归档操作**：
1. 移动文件到 `docs/archive/`
2. 在文件头部添加归档标记：`<!-- ARCHIVED: YYYY-MM-DD | 仅供追溯，不作为当前参考 -->`

**输出示例**：
```
📋 文档清理检查：
- 检测到计划文档：docs/开发文档/plan_用户认证.md
- /qa 已通过，建议归档到 docs/archive/
- 是否执行归档？[Y/n]
```

---

## ✅ 完成提示

```
✅ 测试验收通过（金字塔门控）

📁 输出文档：docs/qa-reports/qa_[功能名].md
📎 前置文档：
   - AC 文档：docs/需求文档/clarify_[功能名].md
   - 计划文档：docs/开发文档/plan_[功能名].md

📊 门控结果：
- Layer 1 单元测试：✅ 15/15 passed, 覆盖率 85%
- Layer 2 集成测试：✅ 8/8 API 端点正常
- Layer 3 E2E 验收：✅ 3/3 用户流程走通

🔒 质量保证：
- E2E 作为最终仲裁：功能确实可用
- 测试数据隔离：不影响生产环境
- 截图证据：docs/qa-reports/ 目录

🎯 下一步：/ship（代码交付）
```

---

**版本**：v3.4（文档生命周期管理）
**更新日期**：2026-01-29
**核心改进**：
- 金字塔架构：Layer 1 → 2 → 3，每层必过
- E2E 最终仲裁：解决"测试过但功能不可用"
- 相关测试识别：区分本次变更和存量测试
- E2E 重试机制：应对浏览器测试不稳定
- 测试数据隔离：避免污染生产环境
- 测试用例模板：具体输入输出，可直接执行
**v3.4 新增**：
- Phase 5 文档清理检查：/qa 通过后提示归档 plan 文档
- 遵循 RULES.md 文档生命周期规范
**v3.3 新增**：
- 从 /plan 验收测试场景提取验收基准
- 验收场景 → 测试用例的转化流程
- 铁律：无验收场景则先补充再执行 /qa
**v3.2 修复**：
- E2E 工具不可用处理：必须解决后才能继续，禁止跳过或降级
- 截图保留策略：与 RULES.md 统一，只保留最新一次
- 测试数据准备：添加 seed 脚本/fixture 规范，禁止硬编码测试账号
**v3.1 修复**：
- 截图存储规范：统一目录和命名格式
- 全栈启动顺序：数据库→后端→前端，严格按序
