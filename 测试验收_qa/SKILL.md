---
name: qa
description: 测试验收。在隔离上下文中启动 pipeline-qa SubAgent。
context: fork
agent: pipeline-qa
---

# /qa

测试验收入口。SubAgent pipeline-qa 将在隔离上下文中执行：
1. 读取 docs/pipeline/{feature}/handoff_check.md
2. 执行金字塔门控验收（单元测试 -> 集成测试 -> E2E）
3. 输出到 docs/pipeline/{feature}/handoff_qa.md

> 如 handoff_check.md 不存在，请先执行 /check。

**手动模式**：直接在会话中输入 `/qa`，Claude Code 自动加载 SubAgent 及其 skills。
**自动模式**：由 pipeline.sh 通过 `claude -p` 调用，自动拼接 SubAgent + Skills。
