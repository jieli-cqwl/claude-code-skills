---
name: check
description: 开发检查。在隔离上下文中启动 pipeline-checker SubAgent。
context: fork
agent: pipeline-checker
---

# /check

开发检查入口。SubAgent pipeline-checker 将在隔离上下文中执行：
1. 读取 docs/pipeline/{feature}/handoff_impl.md
2. 执行多维检查（铁律、Lint、类型、测试、代码质量、需求覆盖）
3. 输出到 docs/pipeline/{feature}/handoff_check.md

> 如 handoff_impl.md 不存在，请先执行 /run-plan。

**手动模式**：直接在会话中输入 `/check`，Claude Code 自动加载 SubAgent 及其 skills。
**自动模式**：由 pipeline.sh 通过 `claude -p` 调用，自动拼接 SubAgent + Skills。
