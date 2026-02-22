---
name: fix
description: 修复问题。在隔离上下文中启动 pipeline-fixer SubAgent。
context: fork
agent: pipeline-fixer
---

# /fix

问题修复入口。SubAgent pipeline-fixer 将在隔离上下文中执行：
1. 读取 docs/pipeline/{feature}/handoff_check.md 或 handoff_qa.md（检查/验收报告）
2. 针对报告中的 FAIL 项逐一修复（每个修复附回归测试，严格 TDD）
3. 输出到 docs/pipeline/{feature}/handoff_fix.md

> 如检查报告不存在，请先执行 /check 或 /qa。

**手动模式**：直接在会话中输入 `/fix`，Claude Code 自动加载 SubAgent 及其 skills。
**自动模式**：由 pipeline.sh 通过 `claude -p` 调用，自动拼接 SubAgent + Skills。
