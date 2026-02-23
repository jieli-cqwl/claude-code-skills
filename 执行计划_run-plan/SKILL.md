---
name: run-plan
description: 执行计划。在隔离上下文中启动 pipeline-implementer SubAgent。
context: fork
agent: pipeline-implementer
---

# /run-plan -- 执行开发计划

> 在隔离上下文中按 Plan 任务清单严格 TDD 执行开发。同时负责评审 Plan 文档。

## 前置条件

`docs/pipeline/{feature}/handoff_plan.md` 必须存在。如不存在，请先执行 `/plan`。

## 执行流程

### 执行模式
1. 读取 `docs/pipeline/{feature}/handoff_plan.md` + `handoff_design.md`
2. 按 Task 拓扑顺序逐个执行（严格 TDD：红-绿-重构）
3. 每个 Task 完成一个 commit：`feat(Task-N): 描述`
4. 输出到 `docs/pipeline/{feature}/handoff_run.md`

### Plan 评审模式
1. 读取 `docs/pipeline/{feature}/handoff_plan.md`
2. 以"文件路径是否存在、AC 是否可测、依赖是否合理"的视角审视
3. 输出 PLAN_OK 或 PLAN_ISSUE
4. 输出到 `docs/pipeline/{feature}/review_plan_N.md`

## Few-shot 示例

### 好的执行输出

```
Task-1: 创建用户数据模型

1. 写测试:
   - test_create_user_success
   - test_create_user_short_username
   - test_create_user_duplicate

2. 红阶段:
   $ pytest tests/test_models/test_user.py
   3 failed, 0 passed (ImportError: cannot import 'User')

3. 实现:
   - src/models/user.py: User 模型 + validate_username()
   - src/models/__init__.py: 导出 User

4. 绿阶段:
   $ pytest tests/test_models/test_user.py
   3 passed, 0 failed

5. 全量测试:
   $ pytest tests/
   47 passed, 0 failed

Commit: feat(Task-1): 添加用户数据模型及校验

---

Task-commit 对照表:
| Task | Commit | 含测试 | 状态 |
|---|---|---|---|
| Task-1 | feat(Task-1): 添加用户数据模型及校验 | tests/test_models/test_user.py | DONE |
| Task-2 | feat(Task-2): 实现用户注册 API | tests/test_api/test_users.py | DONE |

TEST_CMD: pytest tests/
```

### 坏的执行输出

```
已完成用户模型开发，测试通过。
（没有 TDD 红/绿证据、没有具体测试命令、没有 commit 记录、没有 TEST_CMD）
```

## 自检清单

### 执行模式
1. 每个 Task 是否都有对应的 commit？（列出 Task-commit 对照表）
2. 每个 commit 是否包含测试文件？
3. 是否有跳过 TDD 流程（先写实现再补测试）的情况？
4. 是否有标记 BLOCKED 但未说明原因的任务？
5. 实现是否偏离了 design 文档的接口定义？（逐接口核对）
6. 如果有遗留问题，是否已在 Handoff 中明确标注？
7. 是否在 Handoff 交接项中明确写出了 TEST_CMD？

### Plan 评审
1. 是否逐条核对了每个任务的文件路径是否真实存在（通过 Glob 验证）？
2. 是否以"能否翻译为 assert"的视角审视每个 AC？
3. PLAN_ISSUE 是否给出了具体位置和修改建议？

## 输出格式

### 执行输出

```markdown
# handoff_run.md

## 输入分析
[Plan 任务理解 + Design 接口理解]

## 执行记录

### Task-1: [标题]
- 测试先行: [测试文件和用例]
- 红阶段: [测试运行失败输出]
- 实现: [修改的文件]
- 绿阶段: [测试运行通过输出]
- 全量测试: [全量测试结果]
- Commit: feat(Task-1): [描述]

### Task-2: [标题]
...

## Task-Commit 对照表
| Task | Commit | 含测试 | 状态 |

## 交接项
- commit 列表（含 hash）
- TEST_CMD: [测试命令]
- 测试运行结果摘要
- 已知遗留问题
- BLOCKED 任务（如有）
```

### Plan 评审输出

```markdown
REVIEW: PLAN_OK | PLAN_ISSUE

## 评审摘要
[总结评审结果]

## Issues（如有）
1. [ISSUE-1] [具体问题]
   - 类型：[文件路径/AC可测性/依赖拓扑/任务粒度/设计一致性]
   - 建议：[具体修改建议]

## 检查明细
[逐项检查结果]
```
