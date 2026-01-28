---
name: debug
command: debug
user_invocable: true
description: 系统化调试。五阶段实证分析，禁止推测，自动诊断。
---

> **角色**：技术侦探，用证据说话
> **目标**：快速定位根因，自主调查，减少交互
> **核心改进**：禁止推测 + 自动诊断 + 假设驱动
> **适用场景**：后端 API 错误、全栈联调问题
> **来源**：[obra/superpowers](https://github.com/obra/superpowers) + [Cursor Debug Mode](https://cursor.com/blog/debug-mode)
> **思考模式**：启用 ultrathink 深度思考，系统性排查复杂问题

---

## 快速判断：是否需要完整流程？

> **不是所有问题都需要五阶段流程**

| 情况 | 处理方式 |
|------|---------|
| **明显错误**：typo、语法错误、缺少 import | ❌ 不用本流程，直接修复 |
| **错误信息明确指向具体行**：`NameError: name 'xxx' is not defined` | ❌ 不用本流程，直接修复 |
| **简单配置问题**：环境变量缺失、端口冲突 | ⚠️ 简化流程，快速诊断 |
| **复杂问题**：原因不明、涉及多组件、已尝试修复失败 | ✅ 使用完整五阶段流程 |
| **间歇性问题**：时好时坏、难以复现 | ✅ 使用完整五阶段流程 |

**判断标准**：
- 如果 30 秒内能定位原因 → 直接修复
- 如果需要调查 → 使用本流程

---

## 铁律（零容忍）

| 铁律 | 说明 | 违反信号 |
|------|------|---------|
| **禁止推测** | 没有证据就不能下结论 | 使用禁用词汇 |
| **先诊断再分析** | 必须先执行诊断命令 | 没看日志就提假设 |
| **一次一处** | 只改一个地方，验证后再改下一个 | 同时改多处 |
| **阶段强制** | 完成前一阶段才能进入下一阶段 | 跳过诊断直接修复 |

### 禁用词汇

以下词汇**禁止出现**在调试分析中：

```
可能、应该、大概、估计、猜测、也许、或许、
似乎、看起来像、我认为、我觉得、存在可能、
有可能、不排除、推测是、怀疑是、基本上、差不多
```

**正确表述**：
- ❌ "可能是数据库连接问题"
- ✅ "日志显示 `Connection refused`，确认是数据库连接问题"

---

## 五阶段调试流程

### Phase 0: 自动读取错误信息

> **这一步 AI 自动执行，不需要用户参与**

**必须读取的信息**：
1. 完整错误堆栈（用户提供或从日志读取）
2. 相关日志文件
3. 最近 git 改动

**自动执行**（根据项目实际情况选择）：

```bash
# 1. 读取最近 git 改动
git log --oneline -5
git diff HEAD~3 --stat

# 2. 读取日志（根据项目选择路径）
# 常见日志位置：
#   - backend/logs/app.log
#   - logs/app.log
#   - /var/log/app.log
#   - 控制台输出（用户提供）
tail -50 [日志路径] 2>/dev/null || echo "请提供日志路径或错误信息"
```

**注意**：日志路径因项目而异，优先从 CLAUDE.md 或项目配置中获取。

---

### Phase 1: 发散假设（强制）

> **必须列出 5-7 种可能原因，避免单点聚焦**

**为什么要发散**：
- 当陷入调试循环时，往往是因为反复聚焦同一个可能的原因
- 强制列出多种可能，能发现被忽略的真正问题

**输出格式**（严格遵循）：

```markdown
## 可能原因分析

基于错误信息 `[错误内容]`，列出可能原因：

1. **[原因1]** - [简要说明]
2. **[原因2]** - [简要说明]
3. **[原因3]** - [简要说明]
4. **[原因4]** - [简要说明]
5. **[原因5]** - [简要说明]

**聚焦验证**：优先验证 #X 和 #Y
```

**示例**：

```markdown
## 可能原因分析

基于错误信息 `500 Internal Server Error`，列出可能原因：

1. **数据库连接失败** - 连接池耗尽或服务未启动
2. **API 参数校验失败** - 缺少必填字段或类型错误
3. **依赖服务超时** - Redis/外部 API 响应慢
4. **代码异常未捕获** - 空指针或类型转换错误
5. **配置错误** - 环境变量缺失或错误
6. **权限问题** - Token 过期或权限不足
7. **并发冲突** - 数据库锁或竞态条件

**聚焦验证**：优先验证 #1 和 #4
```

---

### Phase 2: 自动诊断（核心改进）

> **AI 自主执行诊断命令，不问用户，直接跑**

**端口说明**：以下命令使用占位符 `[PORT]`，请根据项目实际端口替换：
- 后端常见端口：8000、8080、3000、5000
- 前端常见端口：3000、5173、8080
- 从 CLAUDE.md 或 `.env` 获取准确端口

#### 后端 API 诊断命令

```bash
# 1. 检查服务状态（替换 [PORT] 为实际端口）
curl -s http://localhost:[PORT]/health || echo "服务未启动"

# 2. 读取最近日志（替换 [日志路径] 为实际路径）
tail -50 [日志路径] 2>/dev/null || echo "未找到日志文件"

# 3. 测试 API 调用
curl -v http://localhost:[PORT]/api/v1/[endpoint] 2>&1

# 4. 检查数据库连接（Python/FastAPI 项目）
cd backend && python -c "
from app.core.database import engine
with engine.connect() as conn:
    print('数据库连接正常')
" 2>&1
```

#### 全栈联调诊断命令

```bash
# 1. 后端服务状态
curl -s http://localhost:[后端PORT]/health

# 2. 前端服务状态
curl -s http://localhost:[前端PORT]/ > /dev/null && echo "前端正常" || echo "前端异常"

# 3. API 调用链路
curl -v http://localhost:[后端PORT]/api/v1/[endpoint] \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}' 2>&1

# 4. 检查 CORS 配置
curl -v -X OPTIONS http://localhost:[后端PORT]/api/v1/[endpoint] \
  -H "Origin: http://localhost:[前端PORT]" 2>&1 | grep -i "access-control"
```

#### 通用诊断命令

```bash
# 环境变量检查
env | grep -E "(DATABASE|REDIS|API|SECRET|PORT)" | head -10

# 端口占用检查（替换 [PORT]）
lsof -i :[PORT] 2>/dev/null || netstat -tlnp 2>/dev/null | grep [PORT]

# 进程检查
ps aux | grep -E "(python|node|uvicorn|npm)" | head -5

# 最近改动
git log --oneline -10
git diff HEAD~5 --stat
```

---

### Phase 3: 实证分析

> **基于诊断结果，用证据说话**

**输出格式**（严格遵循）：

```markdown
## 诊断结果

**执行的命令**：
[列出执行的诊断命令]

**发现的证据**：
1. [证据1]：`[具体日志/输出]`
2. [证据2]：`[具体日志/输出]`

**根因定位**：
基于证据 #1 和 #2，确认根因是：[具体原因]

**修复方案**：
[基于证据的具体修复步骤]
```

**示例**：

```markdown
## 诊断结果

**执行的命令**：
- `tail -50 backend/logs/app.log`
- `curl -v http://localhost:8000/api/v1/users`

**发现的证据**：
1. 日志显示：`sqlalchemy.exc.OperationalError: connection refused to localhost:5432`
2. API 返回：`{"error": "Database connection failed"}`

**根因定位**：
基于证据 #1 和 #2，确认根因是：PostgreSQL 服务未启动

**修复方案**：
1. 启动 PostgreSQL：`sudo systemctl start postgresql`
2. 验证连接：`psql -h localhost -U postgres -c "SELECT 1"`
3. 重启应用：`cd backend && uvicorn app.main:app --reload`
```

---

### Phase 4: 实施修复

> **单一修复，验证有效**

**修复原则**：
1. 只改一处，验证后再改下一处
2. 改动前记录当前状态
3. 改动后立即验证

**输出格式**：

```markdown
## 修复实施

**修复操作**：
[具体操作步骤]

**验证结果**：
- [ ] 原问题不再复现
- [ ] 无新增错误
- [ ] 相关功能正常
```

---

### Phase 5: 验证完成

> **确认修复有效，关闭调试**

**验证清单**：

```markdown
## 修复验证

- [ ] 原问题不再复现
- [ ] 执行 API 调用返回正常
- [ ] 日志无新增错误
- [ ] 相关功能端到端测试通过

✅ 调试完成
```

---

## 红线信号（必须停下来）

| 信号 | 行动 |
|------|------|
| 使用了禁用词汇 | **停下来**，重新收集证据 |
| 没看日志就提假设 | **停下来**，先执行诊断命令 |
| 尝试了 3+ 次修复都失败 | **停下来**，质疑架构而非继续尝试 |
| 想着"先试试看" | **停下来**，这是猜测行为 |
| 同时改了多处 | **停下来**，回滚到只改一处 |

---

## 升级机制：假设都排除了怎么办？

> **当 5-7 种假设都验证排除后，需要升级处理**

### 升级条件

- 所有假设都通过诊断命令排除
- 3+ 次修复尝试都失败
- 问题复现条件不稳定

### 升级步骤

```markdown
## 升级处理

**已排除的假设**：
1. ❌ [假设1] - 诊断结果：[排除原因]
2. ❌ [假设2] - 诊断结果：[排除原因]
...

**升级行动**（按顺序尝试）：

1. **扩大假设范围**
   - 是否有遗漏的可能原因？
   - 是否是多个问题叠加？
   - 是否是环境/配置差异？

2. **增加诊断深度**
   - 添加更多日志点
   - 使用调试器单步执行
   - 对比正常和异常环境

3. **寻求外部帮助**
   - 搜索错误信息（Google/Stack Overflow）
   - 查阅官方文档
   - 询问用户是否有更多上下文

4. **质疑架构**
   - 这个功能的设计是否有问题？
   - 是否需要重构而非修补？
   - 报告给用户，建议重新评估
```

### 升级输出

```markdown
## ⚠️ 调试升级

**状态**：常规假设已排除，需要升级处理

**已尝试**：
- [列出已排除的假设和尝试]

**建议行动**：
- [ ] [具体下一步建议]

**需要用户提供**：
- [需要的额外信息或权限]
```

---

## 常见问题速查

### 后端 500 错误

```bash
# 诊断三板斧（替换 [PORT] 和 [日志路径]）
tail -50 [日志路径]
curl -v http://localhost:[PORT]/api/v1/[endpoint]
cd backend && python -c "from app.main import app; print('OK')"
```

### 前端调用后端失败

```bash
# CORS 检查
curl -v -X OPTIONS http://localhost:[后端PORT]/api/v1/[endpoint] \
  -H "Origin: http://localhost:[前端PORT]"

# 后端是否启动
curl -s http://localhost:[后端PORT]/health

# 前端代理配置
cat frontend/vite.config.ts | grep -A5 proxy
```

### 数据库连接问题

```bash
# 检查数据库服务
sudo systemctl status postgresql  # 或 mysql
psql -h localhost -U postgres -c "SELECT 1"

# 检查连接字符串
env | grep DATABASE
```

### 导入/模块错误

```bash
# 检查 Python 路径
cd backend && python -c "import sys; print(sys.path)"

# 检查模块是否存在
cd backend && python -c "from app.xxx import yyy"

# 检查依赖安装
pip list | grep [package-name]
```

---

## 效率对比

| 方法 | 耗时 | 成功率 | 副作用 |
|------|------|--------|--------|
| 盲猜修复 | 2-3 小时 | 40% | 可能引入新 bug |
| 系统调试 | 15-30 分钟 | 95% | 无 |

> "系统化调试比盲目猜测更快"，尤其是在时间压力下。
> — [obra/superpowers](https://github.com/obra/superpowers)

---

## 与其他 Skills 的关系

```
发现 bug / 测试失败 / 服务异常
    ↓
快速判断：是否需要完整流程？
    ├─ 明显错误 → 直接修复
    └─ 复杂问题 → /debug（本 skill）
                      ↓ 修复后
                  /check（开发检查）
```

---

## ✅ 完成提示

```
✅ 调试完成，问题已修复

📋 根因：[一句话描述]
🔧 修复：[一句话描述]
✅ 验证：原问题不再复现

下一步：/check（开发检查）
```

---

**版本**：v2.1（通用性优化版）
**更新日期**：2026-01-28
**改进要点**：
- 禁止推测词汇，必须有证据
- 强制列出 5-7 种可能原因
- 自动执行诊断命令，减少交互
- 专注后端 API + 全栈联调场景
- **新增**：快速判断章节（避免简单问题走完整流程）
- **新增**：升级机制（假设都排除后的逃生通道）
- **优化**：端口/路径使用占位符，适配不同项目
- 来源：obra/superpowers + Cursor Debug Mode
