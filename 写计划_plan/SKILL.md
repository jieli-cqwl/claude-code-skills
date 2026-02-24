---
name: plan
description: |
  编写实施计划。自动激活场景：
  1) 用户说"拆分任务"、"写个计划"、"开发计划"时
  2) /design 完成后用户准备进入计划阶段时
  在隔离上下文中启动 pipeline-planner SubAgent。前置条件：需先完成 /design。
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
