---
name: design
description: 架构设计。在隔离上下文中启动 pipeline-designer SubAgent。
context: fork
agent: pipeline-designer
---

# /design

架构设计入口。SubAgent pipeline-designer 将在隔离上下文中执行：
1. 读取 docs/pipeline/{feature}/handoff_clarify.md
2. 执行架构设计（方法论由 SubAgent 的 skills 字段引入）
3. 输出到 docs/pipeline/{feature}/handoff_design.md

> 如 handoff_clarify.md 不存在，请先执行 /clarify。

**手动模式**：直接在会话中输入 `/design`，Claude Code 自动加载 SubAgent 及其 skills。
**自动模式**：由 pipeline.sh 通过 `claude -p` 调用，自动拼接 SubAgent + Skills。
