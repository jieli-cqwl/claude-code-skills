---
name: run-plan
description: 执行计划。在隔离上下文中启动 pipeline-implementer SubAgent。
context: fork
agent: pipeline-implementer
---

# /run-plan -- 执行开发计划

> 在隔离上下文中按 Plan 任务清单严格 TDD 执行开发。同时负责评审 Plan 文档。

## 前置条件

`docs/pipeline/{feature}/handoff_plan.md` 必须存在。如不存在，请先执行 `/plan`。

## 执行流程

### 执行模式
1. 读取 `docs/pipeline/{feature}/handoff_plan.md` + `handoff_design.md`
2. 按 Task 拓扑顺序逐个执行（严格 TDD：红-绿-重构）
3. 每个 Task 完成一个 commit：`feat(Task-N): 描述`
4. 输出到 `docs/pipeline/{feature}/handoff_run.md`

### Plan 评审模式
1. 读取 `docs/pipeline/{feature}/handoff_plan.md`
2. 以"文件路径是否存在、AC 是否可测、依赖是否合理"的视角审视
3. 输出 PLAN_OK 或 PLAN_ISSUE
4. 输出到 `docs/pipeline/{feature}/review_plan_N.md`

## 输出格式

### 执行输出

```markdown
# handoff_run.md

## 输入分析
[Plan 任务理解 + Design 接口理解]

## 执行记录

### Task-1: [标题]
- 测试先行: [测试文件和用例]
- 红阶段: [测试运行失败输出]
- 实现: [修改的文件]
- 绿阶段: [测试运行通过输出]
- 全量测试: [全量测试结果]
- Commit: feat(Task-1): [描述]

### Task-2: [标题]
...

## Task-Commit 对照表
| Task | Commit | 含测试 | 状态 |

## 交接项
- commit 列表（含 hash）
- TEST_CMD: [测试命令]
- 测试运行结果摘要
- 已知遗留问题
- BLOCKED 任务（如有）
```

### Plan 评审输出

```markdown
REVIEW: PLAN_OK | PLAN_ISSUE

## 评审摘要
[总结评审结果]

## Issues（如有）
1. [ISSUE-1] [具体问题]
   - 类型：[文件路径/AC可测性/依赖拓扑/任务粒度/设计一致性]
   - 建议：[具体修改建议]

## 检查明细
[逐项检查结果]
```
