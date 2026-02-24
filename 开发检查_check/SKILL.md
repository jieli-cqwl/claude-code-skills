---
name: check
description: 开发检查。在隔离上下文中启动 pipeline-checker SubAgent。
context: fork
agent: pipeline-checker
---

# /check -- 开发检查

> 在隔离上下文中执行五维代码质量检查，以对抗性思维找出问题。

## 前置条件

`docs/pipeline/{feature}/handoff_run.md` 必须存在。如不存在，请先执行 `/run-plan`。

## 执行流程

1. 读取 `docs/pipeline/{feature}/handoff_plan.md` + `handoff_run.md`
2. 五维逐一检查：测试、Lint、类型检查、代码质量规则、AC 覆盖
3. 每个维度附带客观证据（命令输出、文件路径:行号、数值）
4. 输出到 `docs/pipeline/{feature}/handoff_check.md`

## 输出格式

```markdown
# handoff_check.md

## 五维检查结果

### 1. 测试
[测试命令 + 结果 + FAIL 详情]

### 2. Lint
[Lint 命令 + 结果 + 每条问题的路径:行号]

### 3. 类型检查
[类型检查命令 + 结果]

### 4. 代码质量规则
[逐规则检查结果 + 违规项路径:行号]

### 5. AC 覆盖
[逐条 AC 核对表格]

## 结果

RESULT: PASS | FAIL
[FAIL 原因汇总]

<metadata>{"status": "PASS|FAIL", "test_passed": N, "test_failed": N, "lint_warnings": N, "quality_issues": N}</metadata>
```
