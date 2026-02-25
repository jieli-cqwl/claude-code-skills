---
name: plan
description: |
  编写实施计划。在隔离上下文中启动 pipeline-planner SubAgent 进行任务拆分。
  Use when: 拆分任务、写开发计划、/design 完成后进入计划阶段。前置条件：需先完成 /design。
context: fork
agent: pipeline-planner
---

<!-- 权限说明：本 Skill 通过 SubAgent pipeline-planner 执行。SubAgent 可用工具：Read, Write, Glob, Grep。参见 agents/pipeline-planner.md 的 allowedTools 定义 -->

# /plan -- 编写实施计划

> 在隔离上下文中将架构蓝图拆分为可执行的开发任务。同时负责评审 Design 文档。

## 前置条件

`docs/pipeline/{feature}/handoff_design.md` 必须存在。缺失时直接终止 /plan，并提示先执行 `/design`。

## 执行流程

### Plan 模式
1. 读取 `docs/pipeline/{feature}/handoff_clarify.md` + `handoff_design.md`
2. 用 Glob 扫描验证任务中引用的文件路径
3. 将架构设计拆分为可执行的 Tasks
4. 每个 Task 包含：具体文件路径、可 assert 的 AC、依赖关系、共享文件标注
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
- shared_files: []

### Task-2: [标题]
- 文件: [具体文件路径列表]
- AC1: [可 assert 的验收标准]
- depends_on: [Task-1]
- shared_files: [被多个 Task 同时修改的文件路径列表]

...

## 覆盖表
[clarify 规则 -> design 接口 -> Task -> 覆盖状态]

## 交接项
- 任务执行顺序
- 文件改动清单
- 每任务 AC
- 测试策略
```

**`shared_files` 字段说明**：
- 含义：该 Task 修改的文件中，可能被其他 Task 也修改的文件列表
- 填写规则：planner 在拆分任务时，对比各 Task 的文件列表，将交叉文件标注到 `shared_files`
- 用途：run-plan-parallel 用此字段判断两个 Task 是否存在文件冲突，决定是否可以并行执行
- 无交叉文件时为空列表 `[]`

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
