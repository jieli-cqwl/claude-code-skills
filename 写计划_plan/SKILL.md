---
name: plan
description: 编写实施计划。在隔离上下文中启动 pipeline-planner SubAgent。
context: fork
agent: pipeline-planner
---

# /plan -- 编写实施计划

> 在隔离上下文中将架构蓝图拆分为可执行的开发任务。同时负责评审 Design 文档。

## 前置条件

`docs/pipeline/{feature}/handoff_design.md` 必须存在。如不存在，请先执行 `/design`。

## 执行流程

### Plan 模式
1. 读取 `docs/pipeline/{feature}/handoff_clarify.md` + `handoff_design.md`
2. 用 Glob 扫描验证任务中引用的文件路径
3. 将架构设计拆分为可执行的 Tasks
4. 每个 Task 包含：具体文件路径、可 assert 的 AC、依赖关系
5. 输出到 `docs/pipeline/{feature}/handoff_plan.md`

### Design 评审模式
1. 读取 `docs/pipeline/{feature}/handoff_design.md`
2. 以"能否拆分为可执行任务"的视角审视设计
3. 输出 DESIGN_OK 或 DESIGN_ISSUE
4. 输出到 `docs/pipeline/{feature}/review_design_N.md`

## Few-shot 示例

### 好的 Plan 输出

```
输入分析：
- clarify 3 条规则，design 定义 3 个接口、1 个数据模型
- 扫描 src/models/ 有 5 个模型文件，src/api/v1/ 有 12 个路由文件

决策：
- 拆为 3 个任务（数据模型 -> API 路由 -> 集成测试），因为三者改动不同文件且有依赖关系

Task-1: 创建用户数据模型
  文件: src/models/user.py（新建）, tests/test_models/test_user.py（新建）
  AC1: User.create(username="alice",...) 返回 User 实例
  AC2: User.create(username="ab",...) 抛出 ValidationError
  AC3: User.create(重复username,...) 抛出 IntegrityError
  depends_on: []

Task-2: 实现用户注册 API
  文件: src/api/v1/users.py（新建）, tests/test_api/test_users.py（新建）
  AC1: POST /users 有效数据 -> 201
  AC2: POST /users 无效用户名 -> 422 VALIDATION_ERROR
  depends_on: [Task-1]

覆盖表：
| clarify 规则 | design 接口 | Task | 状态 |
|---|---|---|---|
| R1 用户名3-20字符 | POST /users | Task-1 AC2, Task-2 AC2 | 已覆盖 |
```

### 坏的 Plan 输出

```
Task-1: 实现用户注册功能
  AC: 界面友好，性能良好
  涉及文件: 用户相关文件
（任务粒度太大、AC 不可测、文件不具体、无依赖关系）
```

## 自检清单

### Plan 模式
1. 每条 clarify 规则是否都有对应的 Task 覆盖？（列出覆盖表）
2. 每个 AC 是否能翻译成一条 assert 语句或具体测试场景？
3. 每个 Task 是否列出了具体文件路径（基于 Glob 扫描验证）？
4. Task 之间是否有循环依赖？（画出依赖链确认）
5. 单个 Task 改动是否超过 5 个文件？（超过则拆分）
6. 如果做了任何假设，是否已标注？

### Design 评审
1. 是否逐条核对了 clarify 规则与 design 接口的对应关系？
2. 是否以"能否拆分为可执行任务"的视角审视设计粒度？
3. DESIGN_ISSUE 是否给出了具体位置和修改建议？

## 输出格式

### Plan 输出

```markdown
# handoff_plan.md

## 输入分析
[clarify 规则理解 + design 接口理解 + 现有代码扫描]

## 决策
[任务拆分策略及理由]

## 任务清单

### Task-1: [标题]
- 文件: [具体文件路径列表]
- AC1: [可 assert 的验收标准]
- AC2: [可 assert 的验收标准]
- depends_on: []

### Task-2: [标题]
...

## 覆盖表
[clarify 规则 -> design 接口 -> Task -> 覆盖状态]

## 交接项
- 任务执行顺序
- 文件改动清单
- 每任务 AC
- 测试策略
```

### Design 评审输出

```markdown
REVIEW: DESIGN_OK | DESIGN_ISSUE

## 评审摘要
[总结评审结果]

## Issues（如有）
1. [ISSUE-1] [具体问题]
   - 位置：[文件/章节]
   - 建议：[具体修改建议]

## 检查明细
[逐项检查结果表格]
```
