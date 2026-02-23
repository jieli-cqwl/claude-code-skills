---
name: fix
description: 修复问题。在隔离上下文中启动 pipeline-fixer SubAgent。
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

## Few-shot 示例

### 好的输出

```
修复轮次: 1

FAIL-1: R2 密码<8字符返回 500（期望 422）
  根因: src/api/v1/users.py:35 create_user() 在调用 User.create() 前
        未调用 validate_password()，密码校验异常未被捕获
  回归测试: tests/test_api/test_users.py::test_short_password_returns_422

  修复 TDD:
  1. 写回归测试 test_short_password_returns_422
  2. 红阶段: pytest tests/test_api/test_users.py::test_short_password -> FAILED (500 != 422)
  3. 修复: src/api/v1/users.py:35 添加 validate_password(data["password"])
  4. 绿阶段: pytest tests/test_api/test_users.py::test_short_password -> PASSED
  5. 全量测试: pytest tests/ -> 49 passed, 0 failed

修复前: 47 passed, 2 failed
修复后: 49 passed, 0 failed（含 2 个新增回归测试）

Commit: fix(FAIL-1): 用户注册添加密码校验
```

### 坏的输出

```
已修复密码校验问题。测试通过。
（没有根因分析、没有回归测试、没有修复前后 diff、没有全量测试结果）
```

## 自检清单

1. 每个 FAIL 项是否都有根因分析（具体文件:行号 + 原因）？
2. 每个修复是否附带回归测试？
3. 回归测试是否先确认失败（红）再修复确认通过（绿）？
4. 修复后全量测试是否通过（无新增失败）？
5. 修复前后测试结果 diff 是否记录？
6. 是否存在删除测试或降低标准的行为？
7. N > 1 时是否说明了与上次修复的差异？
8. 修改范围是否最小（只改必要代码）？

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
