---
name: fix
description: |
  修复问题。自动激活场景：
  1) /check 或 /qa 发现 FAIL 项后用户说"修一下"、"修复这些问题"时
  2) 用户指出具体 bug 要求修复时
  在隔离上下文中启动 pipeline-fixer SubAgent。前置条件：需有 /check 或 /qa 的 FAIL 报告。
context: fork
agent: pipeline-fixer
---

# /fix -- 问题修复

> 在隔离上下文中修复 QA 和 Check 发现的问题。每个修复经过根因分析，附带回归测试。

## 前置条件

`docs/pipeline/{feature}/handoff_check.md` 或 `handoff_qa.md` 必须存在。如不存在，请先执行 `/check` 或 `/qa`。

## 执行流程

1. 读取 `docs/pipeline/{feature}/handoff_check.md` 和/或 `handoff_qa.md`
2. 逐个分析 FAIL 项的根因（定位到文件:行号）
3. 按 TDD 变体流程修复（写回归测试 -> 确认失败 -> 修复 -> 确认通过）
4. 运行全量测试确认无回归
5. 输出到 `docs/pipeline/{feature}/handoff_fix_N.md`

## 输出格式

```markdown
# handoff_fix_N.md

## 修复轮次: N

## 输入分析
[FAIL 项清单理解]

## 差异说明（N > 1 时必须）
- 上次修复方案：[方案描述]
- 上次失败原因：[为什么没修好]
- 本次方案差异：[有什么不同]

## 修复记录

### FAIL-1: [问题描述]
- 根因: [文件:行号 + 原因分析]
- 回归测试: [测试文件::测试函数名]
- 红阶段: [回归测试失败输出]
- 修复: [修改的文件和内容]
- 绿阶段: [回归测试通过输出]

### FAIL-2: [问题描述]
...

## 测试结果

修复前: X passed, Y failed
修复后: X+Z passed, 0 failed

全量测试: [全量测试命令 + 结果]

## 交接项
- 修复内容摘要
- 回归测试清单
- 修复前后测试 diff
- Commit 列表

<metadata>{"status": "FIXED|PARTIAL", "fixes_attempted": N, "fixes_successful": N, "regression_tests_added": N}</metadata>
```
