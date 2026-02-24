---
name: run-plan
description: |
  执行计划。自动激活场景：
  1) 用户说"开始开发"、"执行计划"、"按计划实现"时
  2) /plan 完成后用户准备进入开发阶段时
  在隔离上下文中启动 pipeline-implementer SubAgent。前置条件：需先完成 /plan。
context: fork
agent: pipeline-implementer
---

<!-- 权限说明：本 Skill 通过 SubAgent pipeline-implementer 执行。SubAgent 可用工具：Read, Write, Edit, Bash, Glob, Grep。参见 agents/pipeline-implementer.md 的 allowedTools 定义 -->

# /run-plan -- 执行开发计划

> 在隔离上下文中按 Plan 任务清单严格 TDD 执行开发。同时负责评审 Plan 文档。

## 前置条件

`docs/pipeline/{feature}/handoff_plan.md` 必须存在。如不存在，请先执行 `/plan`。

## 执行流程

### 执行模式
1. 读取 `docs/pipeline/{feature}/handoff_plan.md` + `handoff_design.md`
2. 执行并行化分析（见下方）
3. 按 Task 拓扑顺序逐个执行（严格 TDD：红-绿-重构），或按并行组并行执行
4. 每个 Task 完成一个 commit：`feat(Task-N): 描述`
5. 输出到 `docs/pipeline/{feature}/handoff_run.md`

### 并行化分析（执行 Task 前）

在开始逐 Task 执行之前，分析任务依赖图以识别可并行的任务组：

**步骤 1：构建 DAG**

从 handoff_plan.md 提取所有 Task 的 `depends_on` 和 `shared_files`，构建有向无环图。

**步骤 2：识别并行候选**

并行候选组必须同时满足以下三个条件：
1. 组内 Task 之间无 `depends_on` 关系（无显式依赖）
2. 组内 Task 之间无 `shared_files` 交集（无文件冲突）
3. 至少 2 个 Task 可同时执行

**步骤 3：用户确认**

如果存在并行候选组，向用户展示：

```
发现可并行执行的任务组：

并行组 1: Task-X + Task-Y
  - Task-X 修改: [文件列表]
  - Task-Y 修改: [文件列表]
  - 无共享文件，无依赖关系

是否启用并行执行？(y/n)
  - 并行：预计节省 ~30% 时间，Token 消耗增加 ~50%
  - 串行：按原计划顺序执行
```

**步骤 4：执行策略**

- 用户同意并行：使用 `Task(isolation: "worktree")` 为每个并行 Task 创建隔离 agent
- 用户拒绝或无并行候选：按原有串行模式逐 Task 执行
- 并行组内所有 Task 完成后，合并 worktree 到主分支
- 合并后运行全量测试验证
- 合并失败：回退并行结果，对冲突 Task 回退到串行模式重新执行

**降级策略**：

| 场景 | 处理方式 |
|------|---------|
| 并行组仅 1 个 Task | 不启用并行，串行执行 |
| 用户拒绝并行 | 串行执行 |
| Worktree 创建失败 | 降级为串行执行，输出警告 |
| 合并测试失败 | 回退并行结果，串行重新执行冲突 Task |
| 并行 agent 异常退出 | 该 Task 回退串行，其余并行结果保留 |

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
