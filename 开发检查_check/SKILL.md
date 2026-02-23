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

## Few-shot 示例

### 好的输出

```
1. 测试: pytest tests/ -> 47 passed, 2 failed
   FAIL: test_short_username - expected ValidationError, got InternalServerError
   FAIL: test_duplicate_user - IntegrityError not caught at src/api/users.py:42

2. Lint: ruff check src/ -> 0 errors, 3 warnings
   W1: src/api/users.py:15 E501 line too long (92 > 88)
   W2: src/models/user.py:8 F401 unused import
   W3: src/utils/hash.py:22 E501 line too long

3. 类型检查: mypy src/ -> 0 errors

4. 代码质量:
   FAIL: src/api/users.py:35 create_user() 6 个参数（标准 <= 5）
   PASS: 函数长度 <= 40 行
   PASS: 嵌套 <= 3 层
   PASS: 无空 catch、无裸 except、无硬编码

5. AC 覆盖:
   | Task | AC | 状态 | 证据 |
   |---|---|---|---|
   | Task-1/AC1 | User.create() 返回实例 | PASS | test_create_user_success |
   | Task-1/AC2 | 短用户名抛 ValidationError | FAIL | 返回 500 非 422 |
   | Task-2/AC1 | POST /users 201 | PASS | test_register_success |

RESULT: FAIL（测试 2 FAIL + 代码质量 1 FAIL）
```

### 坏的输出

```
代码质量良好，测试基本通过，没有明显问题。PASS
（没有五维检查、没有客观证据、没有具体数值、橡皮图章）
```

## 自检清单

1. 五个维度是否全部检查？（测试、Lint、类型检查、代码质量、AC 覆盖）
2. 每个 FAIL 项是否有文件路径:行号？
3. 每个结论是否有客观证据（命令输出/数值）？
4. 是否存在主观描述替代客观证据（如"代码不错"）？
5. AC 是否逐条核对（而非抽查）？
6. PASS/FAIL 判定是否严格按"五维全 PASS 才 PASS"执行？
7. 是否存在橡皮图章式的模糊结论？

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
