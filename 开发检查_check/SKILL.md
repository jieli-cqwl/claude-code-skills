---
name: check
description: |
  开发检查。在隔离上下文中启动 pipeline-checker SubAgent 做五维代码质量检查。
  Use when: 检查代码质量、开发完成准备验证。前置条件：需先完成 /run-plan 或 /run-plan-parallel。
context: fork
agent: pipeline-checker
---

<!-- 权限说明：本 Skill 通过 SubAgent pipeline-checker 执行。SubAgent 可用工具：Read, Bash, Glob, Grep。参见 agents/pipeline-checker.md 的 allowedTools 定义 -->

# /check -- 开发检查

> 在隔离上下文中执行五维代码质量检查，以对抗性思维找出问题。

## 前置条件

`docs/pipeline/{feature}/handoff_run.md` 必须存在。如不存在，请先执行 `/run-plan` 或 `/run-plan-parallel`。

## 执行流程

1. 读取 `docs/pipeline/{feature}/handoff_plan.md` + `handoff_run.md`
2. 五维逐一检查：测试、Lint、类型检查、代码质量规则、AC 覆盖
3. 新增三类扫描：文档同步、消息 key、跨模块常量
4. 每个维度/扫描附带客观证据（命令输出、文件路径:行号、数值）
5. 输出到 `docs/pipeline/{feature}/handoff_check.md`

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

### 6. 文档同步（依据 reference/文档规范.md）
[涉及的文档更新/归档清单 + 证据]

### 7. 消息 key（依据 reference/消息配置规范.md）
[新增/变更消息 key 清单 + 配置位置证据]

### 8. 跨模块常量（依据 reference/硬编码治理规范.md）
[跨模块常量提升/校验清单 + 导入路径证据]

## 结果

RESULT: PASS | FAIL
[FAIL 原因汇总]

<metadata>{"status": "PASS|FAIL", "test_passed": N, "test_failed": N, "lint_warnings": N, "quality_issues": N, "doc_sync": "PASS|FAIL", "message_keys": "PASS|FAIL", "cross_module_constants": "PASS|FAIL"}</metadata>
```
