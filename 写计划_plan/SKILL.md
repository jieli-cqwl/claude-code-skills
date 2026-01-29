---
name: plan
command: plan
user_invocable: true
description: 编写实施计划。为多步骤开发任务创建详细的实施路线图，支持两种拆分模式：依赖链模式（适合强耦合）和多人协作模式（适合独立功能，效率提升2-5倍）。在架构设计（/design）之后、执行计划（/run-plan）之前使用。
---

# 写计划 (Plan)

> **角色**：项目经理，将架构蓝图转化为可执行的步骤清单
> **目标**：输出高效可并行的 Tasks，让 /run-plan 最大化并行执行
> **核心改进**：新增多人协作拆分模式，效率提升 2-5 倍
> **流程**：`/design` 之后 → `/run-plan` 之前

---

## 核心概念

| 概念 | 粒度 | 用途 | 格式 |
|------|------|------|------|
| **Task** | 15-30 分钟 | /run-plan 执行单元 | `- [ ] T1: 描述` |
| **Step** | 2-5 分钟 | Task 内部指导 | `#### Step 1.1: 描述` |

**关系**：一个 Task 包含多个 Steps，/run-plan 按 Task 调度子代理，子代理按 Steps 执行。

---

## 文档契约（铁律）

> **原则**：没有输入文档 → 不能执行；没有输出文档 → 不算完成

### 输入文档（门控检查）

| 文档 | 路径 | 必须 | 检查命令 |
|------|------|------|---------|
| **AC 文档** | `docs/需求文档/clarify_[功能名].md` | ✅ 必须 | `ls docs/需求文档/clarify_*.md` |
| **设计文档** | `docs/设计文档/设计_[功能名].md` | ✅ 必须 | `ls docs/设计文档/设计_*.md` |

**门控规则**：
```bash
# 门控检查：AC 文档必须存在
CLARIFY_DOC=$(ls docs/需求文档/clarify_*.md 2>/dev/null | head -1)
if [ -z "$CLARIFY_DOC" ]; then
  echo "❌ 门控失败: AC 文档不存在"
  echo "   修复: 先执行 /clarify 生成需求文档"
  exit 1
fi
echo "✅ AC 文档: $CLARIFY_DOC"

# 门控检查：设计文档必须存在
DESIGN_DOC=$(ls docs/设计文档/设计_*.md 2>/dev/null | head -1)
if [ -z "$DESIGN_DOC" ]; then
  echo "❌ 门控失败: 设计文档不存在"
  echo "   修复: 先执行 /design 生成架构设计"
  exit 1
fi
echo "✅ 设计文档: $DESIGN_DOC"
```

**门控失败处理**：
- AC 文档不存在 → **停止执行**，先执行 `/clarify`
- 设计文档不存在 → **停止执行**，先执行 `/design`

### 输出文档（强制）

| 文档 | 路径 | 用途 |
|------|------|------|
| **计划文档** | `docs/开发文档/plan_[功能名].md` | /test-gen 和 /run-plan 依赖 |

**输出规则**：
- 未输出计划文档 → **不算完成**
- 完成提示必须包含输出文档的完整路径
- 计划文档必须引用 AC（禁止重新定义）

**下游依赖**：
- `/test-gen` 依赖此文档
- `/run-plan` 依赖此文档
- `/check` 依赖此文档

---

## 依赖规范

| 规范文件 | 覆盖内容 |
|---------|---------|
| `~/.claude/rules/RULES.md` | 项目铁律（计划不能违反） |
| `~/.claude/reference/全栈开发.md` | 先后端后前端、联调验证 |
| `~/.claude/reference/并行拆分策略.md` | **多人协作拆分策略** |
| `~/.claude/reference/TDD规范.md` | 测试驱动开发 |
| `~/.claude/reference/文档规范.md` | 计划文档模板和存放位置 |

---

## 核心原则

| 原则 | 说明 |
|------|------|
| **DRY** | 不重复自己 |
| **YAGNI** | 不做不需要的事 |
| **并行优先** | 优先选择可并行的拆分方式 |
| **功能完整** | 每个 Task 尽量包含完整功能（前+后+测试） |
| **Step 可验证** | 每个 Step 有明确的验证方式 |

---

## 🚀 拆分策略选择（核心改进）

### 两种拆分模式对比

| 维度 | 依赖链模式 | 多人协作模式 |
|------|-----------|-------------|
| **拆分方式** | 按技术层（Model→Service→API→前端） | 按功能（Alice 登录、Bob 注册） |
| **并行效率** | 依赖链长，等待多 | 功能独立，并行度高 |
| **冲突风险** | 联调时可能冲突 | 文件隔离，冲突少 |
| **适用场景** | 强耦合、单一功能 | 多个独立功能 |
| **效率提升** | 1-1.5 倍 | **2-5 倍** |

### 决策树

```
分析需求
    ↓
识别功能模块数量
    ↓
    ┌─── 单一功能？───→ 使用【依赖链模式】
    │
    └─→ 多个独立功能（≥2）
            ↓
        文件独立性分析
            ↓
        ┌─── 文件高度重叠？───→ 使用【依赖链模式】
        │
        └─→ 文件可隔离 ✅
                ↓
            使用【多人协作模式】（推荐）
```

### 判断标准

**适合多人协作模式**：
- ✅ 有 2 个以上独立功能（如：登录、注册、密码重置）
- ✅ 每个功能有自己独立的文件（如：login.py vs register.py）
- ✅ 功能间通过接口交互，不共享内部状态

**适合依赖链模式**：
- ✅ 单一功能需要多层实现
- ✅ 文件高度耦合，无法隔离
- ✅ 必须严格按顺序执行

---

## 计划文档结构

### 模式一：多人协作模式（推荐）

```markdown
# [功能名称] 实施计划

## 目标
[一句话描述要实现什么]

## 前置文档
- 需求文档：`docs/需求文档/PRD_xxx.md`
- 架构设计：`docs/设计文档/设计_xxx.md`

## 技术栈
- 后端：Python + FastAPI / Node.js / Java Spring
- 前端：React + TypeScript / Vue3
- 数据库：MySQL / PostgreSQL

---

## 拆分模式

**选择**：多人协作模式
**原因**：有 3 个独立功能（登录、注册、密码重置），文件可隔离

---

## Tasks 执行清单（多人协作版）

> 每个"开发者"负责一个完整功能（前端+后端+测试）

| Task | 负责人 | 描述 | 文件范围 | 依赖 |
|------|--------|------|---------|------|
| T0 | Tech Lead | 基础设施搭建 | schema.py, routes.py, AuthContext.tsx | 无（前置） |
| T1 | Alice | 用户登录功能 | login.py, LoginForm.tsx, test_login.py | T0 |
| T2 | Bob | 用户注册功能 | register.py, RegisterForm.tsx, test_register.py | T0 |
| T3 | Charlie | 密码重置功能 | reset.py, ResetForm.tsx, test_reset.py | T0 |
| T4 | Tech Lead | 集成验证 | tests/integration/, e2e/ | T1,T2,T3（后置） |

### 并行执行分组

```
第一批（串行）: T0 - Tech Lead 搭建基础设施
    ↓
第二批（并行）: T1, T2, T3 - 三个开发者同时工作
    ↓
第三批（串行）: T4 - Tech Lead 集成验证
```

### 效率预估
- 串行耗时：6-8 小时
- 并行耗时：2-3 小时
- **效率提升：2.5-3 倍**

### 验收测试场景（引用 /clarify AC）

> ⚠️ **禁止重新定义 AC**：此处只能引用 /clarify 输出的 AC 表格，不能修改或新增。
> **AC 单一来源**：`docs/需求文档/clarify_[功能名].md` 中的 AC 表格
> **用途**：/qa 执行时基于此场景验收

**引用方式**：

```markdown
**AC 来源文档**：`docs/需求文档/clarify_用户认证.md`

**引用的 AC 列表**：
- AC-1: 正确密码登录 → 跳转首页
- AC-2: 注册成功 → 自动登录
- AC-3: 错误密码 → 显示密码错误
- AC-4: 邮箱未注册 → 显示用户不存在
- AC-5: 密码最小长度 → 注册成功
- AC-6: 密码过短 → 显示错误

**完整 AC 表格见**：[clarify_用户认证.md](docs/需求文档/clarify_用户认证.md#4-验收标准)
```

> 💡 **为什么不在 /plan 重新定义 AC？**
> 1. 避免 AC 在多个地方不一致
> 2. 保证测试和验收用同一套标准
> 3. 减少维护成本，修改只需改一处

### 测试设计状态（/run-plan 执行前检查）

> ⚠️ **门控要求**：测试必须在开发之前生成

- [ ] AC 来源文档存在：`docs/需求文档/clarify_[功能名].md`
- [ ] 已执行 `/test-gen from-clarify` 生成测试
- [ ] FAILING 测试文件存在：`tests/test_[功能名]_acceptance.py`

**如未完成**：先执行 `/test-gen from-clarify <clarify_doc>` 生成测试

---

### 验收完成确认（/qa 执行后勾选）
- [ ] 所有 AC 场景验收通过
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试通过
- [ ] **服务可正常启动**

---

## Task 详情

### T0: 基础设施搭建（Tech Lead）

- [ ] T0: 基础设施搭建

**负责人**：Tech Lead
**依赖**：无（前置任务）
**预估**：30 分钟

**职责**：
- 搭建所有开发者共享的基础设施
- 完成后其他开发者可以并行开始

**详细步骤**：

#### Step 0.1: 创建数据库 Schema

**文件**：`backend/app/models/user.py`
**代码**：[具体代码]
**验证**：`python -c "from app.models.user import User; print('OK')"`

#### Step 0.2: 配置路由

**文件**：`backend/app/api/routes.py`
...

#### Step 0.3: 创建 Auth Context

**文件**：`frontend/src/contexts/AuthContext.tsx`
...

---

### T1: 用户登录功能（Alice）

- [ ] T1: 用户登录功能

**负责人**：Alice
**依赖**：T0
**预估**：1.5 小时

**文件边界**（只能修改这些文件）：
- 后端：`backend/app/api/auth/login.py`
- 前端：`frontend/src/components/LoginForm.tsx`
- 测试：`backend/tests/auth/test_login.py`
- ⚠️ **禁止修改其他文件**

**职责**：
- 完整的登录功能（后端 API + 前端 UI + 测试）
- 自己编写测试，自己联调验证

**详细步骤**：

#### Step 1.1: 实现登录 API

**文件**：`backend/app/api/auth/login.py`
**TDD**：先写测试 → 看到失败 → 写实现 → 看到通过
**代码**：[具体代码]
**验证**：`pytest tests/auth/test_login.py -v`

#### Step 1.2: 实现登录表单

**文件**：`frontend/src/components/LoginForm.tsx`
...

---

### T2: 用户注册功能（Bob）

- [ ] T2: 用户注册功能

**负责人**：Bob
**依赖**：T0
**预估**：2 小时

**文件边界**：
- 后端：`backend/app/api/auth/register.py`
- 前端：`frontend/src/components/RegisterForm.tsx`
- 测试：`backend/tests/auth/test_register.py`

（格式同 T1）

---

### T3: 密码重置功能（Charlie）

（格式同上）

---

### T4: 集成验证（Tech Lead）

- [ ] T4: 集成验证

**负责人**：Tech Lead
**依赖**：T1, T2, T3（所有开发者完成后）
**预估**：1 小时

**职责**：
- 合并所有开发者的代码
- 检测并解决冲突
- 运行集成测试
- **验证服务可正常启动**

**详细步骤**：

#### Step 4.1: 合并代码

检查文件冲突，自动合并或手动解决

#### Step 4.2: 运行集成测试

```bash
pytest tests/integration/ -v
```

#### Step 4.3: 服务启动验证

```bash
# 启动后端
python manage.py runserver &
curl http://localhost:8000/health

# 启动前端
npm run dev &
curl http://localhost:3000/

# API 功能验证
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```
```

---

### 模式二：依赖链模式

```markdown
# [功能名称] 实施计划

## 拆分模式

**选择**：依赖链模式
**原因**：单一功能，各层强耦合

---

## Tasks 执行清单（依赖链版）

| Task | 描述 | 依赖 | 预估 |
|------|------|------|------|
| T1 | 实现用户模型和 Schema | 无 | 15min |
| T2 | 实现用户 Service | T1 | 20min |
| T3 | 实现用户 API | T2 | 15min |
| T4 | 编写后端单元测试 | T3 | 20min |
| T5 | 实现前端页面 | T3 | 25min |
| T6 | 联调验证 | T4, T5 | 15min |

### 并行执行分组

```
T1 → T2 → T3 ─┬→ T4（测试）─┬→ T6（联调）
              └→ T5（前端）─┘
```

（后续 Task 详情格式与之前相同）
```

---

## Task 设计原则

### 多人协作模式原则

| 原则 | 说明 |
|------|------|
| **功能完整** | 每个开发者负责完整功能（前+后+测试） |
| **文件隔离** | 开发者之间文件不重叠 |
| **自测自验** | 每个开发者自己写测试、自己联调 |
| **TDD 强制** | 每个 Task 必须遵循 TDD |

### 依赖链模式原则

| 规则 | 说明 |
|------|------|
| **后端先于前端** | 前端 Task 依赖对应的后端 API Task |
| **Model → Service → API** | 后端内部按层依赖 |
| **测试可并行** | 后端测试和前端开发可以并行 |

### 并行冲突检测（必须）

**同一批次内的 Tasks 不能修改同一文件**：

```markdown
❌ 有冲突
| Task | 负责人 | 文件范围 |
|------|--------|---------|
| T1 | Alice | login.py, __init__.py |
| T2 | Bob | register.py, __init__.py |  ← 都改 __init__.py

✅ 无冲突
| Task | 负责人 | 文件范围 |
|------|--------|---------|
| T1 | Alice | login.py |
| T2 | Bob | register.py |  ← 文件完全隔离
```

---

## 粒度控制

| 粒度 | Task 数量 | 适用场景 |
|------|----------|---------|
| 太粗 | 1-2 个 | ❌ 失去并行优势 |
| 合适 | 3-7 个 | ✅ 常规功能 |
| 太细 | >10 个 | ❌ 调度开销大 |

---

## 计划文件位置

```
docs/开发文档/plan_[功能名].md
```

---

## 检查清单

### 拆分模式检查
- [ ] 分析了功能数量和文件独立性
- [ ] 选择了合适的拆分模式（多人协作/依赖链）
- [ ] 写明了选择原因

### 验收测试场景检查（AC 引用）
- [ ] 有"验收测试场景"章节
- [ ] **引用** /clarify 的 AC 表格（禁止重新定义）
- [ ] AC 来源文档路径正确
- [ ] 引用的 AC 列表完整（正常+异常+边界）
- [ ] 有"测试设计状态"检查点

### 结构检查
- [ ] 有 Tasks 执行清单表格
- [ ] 每个 Task 有明确的依赖关系
- [ ] 有并行执行分组
- [ ] 有验收完成确认

### 多人协作模式额外检查
- [ ] 每个 Task 有明确的负责人（Alice/Bob/Charlie/Tech Lead）
- [ ] 每个 Task 有明确的文件边界
- [ ] 开发者之间文件不重叠
- [ ] 有 Tech Lead 前置和后置任务

### Task 检查
- [ ] 每个 Task 有 `- [ ] T{N}: 描述` 格式的 checkbox
- [ ] 每个 Task 有依赖、预估、验收标准
- [ ] 每个 Task 有详细的 Steps
- [ ] 每个 Step 有 TDD 要求

### Step 检查
- [ ] 每个 Step 有明确的文件路径
- [ ] 每个 Step 有完整的代码（不是描述）
- [ ] 每个 Step 有验证命令

---

## 与其他 Skills 的关系

```
/clarify（需求澄清）
    ↓ 输出：AC 表格（单一来源）
    ↓ [评审点: 需求评审]
/explore（方案探索）
    ↓ 方案确定后
/design（架构设计）
    ↓ [评审点: 架构评审]
/plan（写计划）← 当前
    ├─ 选择拆分模式
    ├─ 引用 /clarify 的 AC（禁止重新定义）
    └─ 输出 Task 详情
    ↓ [评审点: 计划评审]
/test-gen from-clarify  ← 🆕 测试先行
    ↓ 从 AC 生成 FAILING 测试
    ↓ [门控: 测试必须存在才能开发]
/run-plan（执行计划）
    ├─ 基于已有测试，严格 TDD
    ├─ 按负责人分派（多人协作）
    └─ 或按依赖分组（依赖链）
    ↓
/check（开发检查）
    ↓
/qa（测试验收）
    ↓ 基于 AC 验收
/ship（代码交付）
```

### AC 流转链路

```
/clarify 定义 AC（单一来源）
    ↓
/plan 引用 AC（禁止重新定义）
    ↓
/test-gen 从 AC 生成测试
    ↓
/run-plan 基于测试开发（TDD）
    ↓
/qa 基于 AC 验收
```

---

## ⛔ 边界约束（铁律）

> **`/plan` 的职责边界：只做计划编写，不能跳过后续环节**

| 禁止行为 | 说明 |
|---------|------|
| ❌ 跳过 `/test-gen` 直接进入 `/run-plan` | 测试先行是铁律，必须先生成测试 |
| ❌ 跳过整个流程直接修改代码 | 必须走 test-gen → run-plan |
| ❌ 在计划阶段写任何实现代码 | 只输出计划文档，不输出代码 |

**正确的完成动作**：
1. 输出计划文档到 `docs/开发文档/plan_[功能名].md`
2. 展示完成提示
3. 进入下一环节（`/critique` 或 `/test-gen`）或等待用户指令

**跳过环节的处理**：
- `/critique` 可以跳过（非强制），但建议执行
- `/test-gen` 不能跳过（铁律：测试先行）

**正常流转顺序**：
```
/plan → /critique（可选）→ /test-gen → /run-plan
```

---

## 禁止行为

| 禁止 | 原因 |
|------|------|
| **重新定义 AC** | AC 只在 /clarify 定义，/plan 只能引用 |
| 不分析直接用依赖链模式 | 可能错过 2-5 倍效率提升 |
| 多人协作模式文件重叠 | 会导致合并冲突 |
| Task 没有 TDD 要求 | 质量无保证 |
| 跳过服务启动验证 | 测试过但服务跑不起来 |
| **未生成测试就执行 /run-plan** | 违反测试先行原则 |

---

## ✅ 完成提示

```
✅ 计划编写完成

📁 输出文档：docs/开发文档/plan_[功能名].md
📎 前置文档：
   - AC 文档：docs/需求文档/clarify_[功能名].md
   - 设计文档：docs/设计文档/设计_[功能名].md

📋 计划内容：
   - 拆分模式：多人协作 / 依赖链
   - 开发者数量：X 人
   - 共 X 个 Tasks
   - 可并行批次：Y 批
   - 效率提升：X 倍

🎯 下一步：
   1. 自动执行 /critique 评审计划
   2. 评审通过后执行 /test-gen from-clarify（测试先行）
   3. 测试生成后执行 /run-plan（执行计划）

📋 /clear 后可直接执行（复制粘贴）：
   /test-gen from-clarify docs/需求文档/clarify_[功能名].md
   /run-plan docs/开发文档/plan_[功能名].md
```
