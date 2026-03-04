---
name: auto-dev
user-invocable: true
description: |
  全流程自动开发编排。依次触发 SubAgent 完成 design → plan → run-plan/run-plan-parallel → check → qa 全流程。
  Use when: 一键自动化完整开发流程。
---

# /auto-dev -- 全流程自动开发

> 在主对话中编排完整的开发流程，通过 Task 工具依次启动各 pipeline agent 执行。
> 适用于中大型需求的完整开发流程。小需求请直接使用单个 Skill。

## 熔断机制

| 循环 | 最大轮次 | 触发动作 |
|------|---------|---------|
| Design 评审 | 3 | 暂停，请用户介入 |
| Plan 评审 | 3 | 暂停，请用户介入 |
| Implement-Check | 3 | 暂停，请用户介入 |
| QA-Fix | 5 | 暂停，请用户确认 |
| QA-Fix | 10 | 终止，输出 FAIL 报告 |

## 前置条件

1. `docs/pipeline/{feature}/prd.md`（由 `/prd` 生成）必须存在。请先执行 `/prd` 完成需求文档化。
2. 用户确认需求后说"开始"或"执行"。
3. 若走 Plan Ready 快速入口，需额外满足：
   - `handoff_design.md` + `handoff_plan.md` 已存在
   - 用户已完成人工评审并明确同意"从 implement 开始"

## 编排流程

ultrathink

### 快速入口：Plan Ready（跳过设计与计划）

当 `handoff_plan.md` 已生成且评审通过时，可直接进入执行交付阶段：

```
Fast Path:
  A. 检查 prd.md / handoff_design.md / handoff_plan.md 均存在
  B. 标记 design=SKIPPED, plan=SKIPPED
  C. 直接进入步骤 7（/run-plan 或 /run-plan-parallel）
```

适用场景：你已人工把关需求、设计、计划，不希望重复评审，希望自动完成开发/测试/修复。

### 阶段 1：方向决策（Design-Plan 评审循环）

```
Design 评审循环（最多 3 轮）:
  1. Task(pipeline-designer) 输出 handoff_design.md
  2. Task(pipeline-planner, 评审模式) 评审 Design
     - DESIGN_OK → 进入下一步
     - DESIGN_ISSUE → 回到步骤 1（传入评审反馈）
  3. 循环超过 3 轮 → 暂停，请用户介入

[人工确认检查点] 展示 Design 产出，等待用户确认后继续

Plan 评审循环（最多 3 轮）:
  4. Task(pipeline-planner) 输出 handoff_plan.md
  5. Task(pipeline-implementer, 评审模式) 评审 Plan
     - PLAN_OK → 进入下一步
     - PLAN_ISSUE → 回到步骤 4（传入评审反馈）
  6. 循环超过 3 轮 → 暂停，请用户介入

[人工确认检查点] 展示 Plan 产出，等待用户确认后继续
```

### 阶段 2：执行交付（Implement-Check 循环）

#### 执行模式路由（步骤 7 之前）

分析 handoff_plan.md 的 DAG 结构，选择执行模式：

| 条件 | 路由 | 说明 |
|------|------|------|
| Tasks <= 3 | Task(pipeline-implementer)（串行） | 小任务串行更简单可靠 |
| Tasks > 3 且有并行候选组（同 Layer 无 shared_files 交集的 >= 2 Tasks） | /run-plan-parallel（并行） | 大任务并行提效 |
| Tasks > 3 但全链式依赖 | Task(pipeline-implementer)（串行） | 无并行机会 |

```
Implement-Check 循环（最多 3 轮）:
  7. 按路由结果执行 Task(pipeline-implementer) 或 /run-plan-parallel → 输出 handoff_run.md
  8. Task(pipeline-checker) 输出 handoff_check.md
     - 全部 PASS → 进入 QA
     - 有 FAIL → Task(pipeline-fixer) 修复 → 回到步骤 7
  9. 循环超过 3 轮 → 暂停，请用户介入
```

### 阶段 3：验收修复（QA-Fix 循环）

```
QA-Fix 循环（最多 10 轮）:
  10. Task(pipeline-qa) 输出 handoff_qa.md
      - PASS → 流程完成
      - FAIL → 进入修复
  11. Task(pipeline-fixer) 修复 FAIL 项
  12. Task(pipeline-checker) 验证修复
  13. 回到步骤 10
  14. >= 5 轮 → 暂停，请用户介入
  15. >= 10 轮 → 终止，报告无法自动修复
```

## 人工确认检查点

以下时机必须暂停并等待用户确认（默认确认型）：

| 检查点 | 时机 | 展示内容 |
|--------|------|---------|
| Design 确认 | Design 评审通过后 | handoff_design.md 摘要（技术选型/决策状态 + MOD 索引） |
| Plan 确认 | Plan 评审通过后 | handoff_plan.md 的任务清单和依赖关系 |
| QA >= 5 轮 | QA-Fix 循环达到 5 轮 | 历次修复记录和当前 FAIL 项 |

若用户明确要求“无人值守/无需确认直接执行”，可跳过上述确认等待。
确认方式：用户回复"继续"/"确认" 则继续，回复"停止"/"修改" 则暂停。

## 失败处理策略

| 失败场景 | 处理方式 |
|---------|---------|
| Design 评审 3 轮未通过 | 暂停，展示所有评审 Issue，请用户介入调整需求或手动修正设计 |
| Plan 评审 3 轮未通过 | 暂停，展示所有评审 Issue，请用户介入 |
| Check 循环 3 轮未通过 | 暂停，展示 FAIL 项清单和 3 次修复记录，请用户手动修复后继续 |
| QA 循环 10 轮未通过 | 终止，输出完整的 FAIL 报告和所有修复尝试记录 |
| SubAgent 执行失败 | 立即暂停，展示错误信息，请用户介入 |

## 进度展示

每个阶段完成后，在主对话中展示进度：

```
[auto-dev] 进度: design(DONE) -> plan(DONE) -> run-plan[-parallel](IN PROGRESS) -> check -> qa
当前阶段: 执行开发（Task 3/5）
```

Plan Ready 快速入口展示：

```
[auto-dev] 进度: design(SKIPPED) -> plan(SKIPPED) -> run-plan[-parallel](IN PROGRESS) -> check -> qa
当前阶段: 执行开发（Task 1/N）
```

## 注意事项

- 每个阶段通过 Task 工具启动对应 pipeline agent 执行，不会污染主对话
- 阶段间通过 Handoff 文件传递信息
- 评审循环确保上游产出质量，避免低质量产出传递到下游
- pipeline.sh 提供更强的加固能力（超时/费用/锁），适合无人值守场景
- 与脚本编排对齐：使用单版本命令 `bash ~/.claude/pipeline.sh start <feature> <simple|complex>`，随后循环 `run-step`，最后 `finalize`
- 统一入口层不再接受旧版环境变量式流程参数，避免误触发历史行为
- 统一格式：`/prd` 输出 `prd.md + units/`，下游阶段按单一格式读取
