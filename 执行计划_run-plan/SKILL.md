---
name: run-plan
description: 执行计划。在隔离上下文中启动 pipeline-implementer SubAgent。
context: fork
agent: pipeline-implementer
---

# /run-plan

计划执行入口。SubAgent pipeline-implementer 将在隔离上下文中执行：
1. 读取 docs/pipeline/{feature}/handoff_plan.md
2. 按 Task 拓扑顺序执行开发（严格 TDD，支持并行派发）
3. 输出到 docs/pipeline/{feature}/handoff_impl.md

> 如 handoff_plan.md 不存在，请先执行 /plan。

**手动模式**：直接在会话中输入 `/run-plan`，Claude Code 自动加载 SubAgent 及其 skills。
**自动模式**：由 pipeline.sh 通过 `claude -p` 调用，自动拼接 SubAgent + Skills。
