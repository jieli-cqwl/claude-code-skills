---
name: plan
description: 编写实施计划。在隔离上下文中启动 pipeline-planner SubAgent。
context: fork
agent: pipeline-planner
---

# /plan

实施计划入口。SubAgent pipeline-planner 将在隔离上下文中执行：
1. 读取 docs/pipeline/{feature}/handoff_design.md
2. 将架构蓝图拆分为可执行的 Tasks（支持依赖链/多人协作两种模式）
3. 输出到 docs/pipeline/{feature}/handoff_plan.md

> 如 handoff_design.md 不存在，请先执行 /design。

**手动模式**：直接在会话中输入 `/plan`，Claude Code 自动加载 SubAgent 及其 skills。
**自动模式**：由 pipeline.sh 通过 `claude -p` 调用，自动拼接 SubAgent + Skills。
