---
name: auto-dev
command: auto-dev
user_invocable: true
description: 全流程自动开发编排。在主对话中依次触发 SubAgent 完成 design -> plan -> run-plan -> check -> qa 全流程。
---

# /auto-dev -- 全流程自动开发

> 在主对话中编排完整的开发流程，依次触发各阶段 SubAgent 在隔离上下文中执行。
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

1. `docs/pipeline/{feature}/handoff_clarify.md` 必须存在。请先执行 `/clarify` 完成需求澄清。
2. 用户确认需求后说"开始"或"执行"。

## 编排流程

ultrathink

### 阶段 1：方向决策（Design-Plan 评审循环）

```
Design 评审循环（最多 3 轮）:
  1. /design → pipeline-designer 输出 handoff_design.md
  2. /plan（评审模式）→ pipeline-planner 评审 Design
     - DESIGN_OK → 进入下一步
     - DESIGN_ISSUE → 回到步骤 1（传入评审反馈）
  3. 循环超过 3 轮 → 暂停，请用户介入

[人工确认检查点] 展示 Design 产出，等待用户确认后继续

Plan 评审循环（最多 3 轮）:
  4. /plan → pipeline-planner 输出 handoff_plan.md
  5. /run-plan（评审模式）→ pipeline-implementer 评审 Plan
     - PLAN_OK → 进入下一步
     - PLAN_ISSUE → 回到步骤 4（传入评审反馈）
  6. 循环超过 3 轮 → 暂停，请用户介入

[人工确认检查点] 展示 Plan 产出，等待用户确认后继续
```

### 阶段 2：执行交付（Implement-Check 循环）

```
Implement-Check 循环（最多 3 轮）:
  7. /run-plan → pipeline-implementer 输出 handoff_run.md
  8. /check → pipeline-checker 输出 handoff_check.md
     - 全部 PASS → 进入 QA
     - 有 FAIL → /fix 修复 → 回到步骤 7
  9. 循环超过 3 轮 → 暂停，请用户介入
```

### 阶段 3：验收修复（QA-Fix 循环）

```
QA-Fix 循环（最多 10 轮）:
  10. /qa → pipeline-qa 输出 handoff_qa.md
      - PASS → 流程完成
      - FAIL → 进入修复
  11. /fix → pipeline-fixer 修复 FAIL 项
  12. /check → pipeline-checker 验证修复
  13. 回到步骤 10
  14. >= 5 轮 → 暂停，请用户介入
  15. >= 10 轮 → 终止，报告无法自动修复
```

## 人工确认检查点

以下时机必须暂停并等待用户确认（默认确认型）：

| 检查点 | 时机 | 展示内容 |
|--------|------|---------|
| Design 确认 | Design 评审通过后 | handoff_design.md 摘要 + Key_Decisions.md |
| Plan 确认 | Plan 评审通过后 | handoff_plan.md 的任务清单和依赖关系 |
| QA >= 5 轮 | QA-Fix 循环达到 5 轮 | 历次修复记录和当前 FAIL 项 |

UNATTENDED_MODE=true 时：跳过上述确认等待（与 pipeline.sh 行为一致）。
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
[auto-dev] 进度: design(DONE) -> plan(DONE) -> run-plan(IN PROGRESS) -> check -> qa
当前阶段: 执行开发（Task 3/5）
```

## 注意事项

- 每个阶段都在隔离上下文中执行（context: fork），不会污染主对话
- 阶段间通过 Handoff 文件传递信息
- 评审循环确保上游产出质量，避免低质量产出传递到下游
- pipeline.sh 提供更强的加固能力（超时/费用/锁），适合无人值守场景
