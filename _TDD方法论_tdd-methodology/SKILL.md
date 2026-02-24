---
name: tdd-methodology
description: TDD 方法论。严格红绿重构流程、一任务一 Commit、阻塞标注、修复 TDD 变体。
user-invocable: false
---

# TDD Methodology - TDD 方法论

> 引用者：pipeline-implementer（主用）、pipeline-fixer（主用）

---

## 1. 严格 TDD 执行顺序

每个任务必须严格按照以下顺序执行，不可跳过或调换：

```
写测试 -> 运行确认失败（红） -> 写实现 -> 运行确认通过（绿） -> 重构（可选）
```

### 红阶段（Red）

1. 根据 Plan 中的 AC 编写测试用例
2. 运行测试，确认全部 FAILED
3. 记录失败输出作为证据

### 绿阶段（Green）

1. 编写最小实现使测试通过
2. 运行测试，确认全部 PASSED
3. 记录通过输出作为证据

### 重构阶段（Refactor，可选）

1. 测试通过后，优化代码结构
2. 再次运行测试，确认仍然 PASSED
3. 重构不改变外部行为

### 禁止行为

- 先写实现再补测试（假 TDD）
- 跳过红阶段直接写实现
- 删除失败的测试使其"通过"
- 修改测试使其与错误实现匹配

---

## 2. 一任务一 Commit 规范

### Commit Message 格式

```
feat(Task-N): 描述
```

### 规则

- 每个 Plan 中的 Task 对应恰好一个 commit
- 每个 commit 必须包含测试文件
- commit 时所有测试必须通过
- commit message 中的描述必须与 Task 内容一致

### Commit 前检查

1. 本次 commit 是否包含测试文件？
2. 运行全量测试是否通过？
3. commit message 格式是否正确？
4. 改动范围是否与 Task 匹配（不多不少）？

---

## 3. 阻塞标注规范

当任务无法完成时，必须明确标注而非假装完成。

### 格式

```
BLOCKED: Task-N
原因: [具体阻塞原因]
影响: [对后续任务的影响]
建议: [解决方向]
```

### 常见阻塞场景

- 上游接口定义与实际代码不一致
- 依赖的外部服务不可用
- 设计文档中的假设不成立
- 需要的权限或配置缺失

---

## 4. 测试先行的验证证据要求

Handoff 文档必须包含测试运行的客观证据，不接受"测试通过"的自述声明。

### 必须记录的信息

```
TEST_CMD: pytest tests/ 或 npm test
测试运行结果:
- 红阶段: X tests, Y FAILED, Z PASSED
- 绿阶段: X tests, 0 FAILED, X PASSED
```

### 证据格式

每个 Task 的记录必须包含：
1. 运行的测试命令
2. 红阶段的失败输出（证明测试先于实现）
3. 绿阶段的通过输出（证明实现正确）
4. 全量测试结果（证明没有回归）

---

## 5. 修复场景 TDD 变体

Fixer 使用 TDD 的变体流程：

### 修复 TDD 流程

```
分析 FAIL 项 -> 写回归测试 -> 确认回归测试失败（红） -> 修复代码 -> 确认回归测试通过（绿） -> 运行全量测试
```

### 修复前后 Diff 要求

每个修复必须记录：

```
修复项: [FAIL 项描述]
根因: [具体文件:行号，原因分析]
回归测试: [新增测试文件:测试函数名]
修复前: [测试运行结果，含 FAIL 数]
修复后: [测试运行结果，含 PASS 数]
全量测试: [全量测试结果]
```

### 差异说明（N > 1 时必须）

第 2 次及以后的修复，必须说明：
- 上次修复方案是什么
- 上次为什么失败
- 这次方案有什么不同
- 为什么这次会成功

---

## 6. Few-shot 对比示例

### 好的 TDD 执行记录

```
Task-1: 创建用户数据模型

1. 写测试:
   - test_create_user_success: 验证正常创建
   - test_create_user_short_username: 验证用户名<3字符被拒绝
   - test_create_user_duplicate: 验证重复用户名被拒绝

2. 红阶段:
   $ pytest tests/test_models/test_user.py
   3 failed, 0 passed (ImportError: cannot import 'User' from 'src.models')

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
```

### 坏的 TDD 执行记录

```
Task-1: 创建用户数据模型
已完成用户模型开发，测试通过。
（没有红/绿阶段证据、没有具体测试命令、没有测试数量）
```

---

## 7. 检查清单

### Implementer 自检

1. [ ] 每个 Task 是否都有对应的 commit？
2. [ ] 每个 commit 是否包含测试文件？
3. [ ] 是否有跳过 TDD 流程（先写实现再补测试）的情况？
4. [ ] 是否有标记 BLOCKED 但未说明原因的任务？
5. [ ] Handoff 中是否明确写出了 TEST_CMD？
6. [ ] 每个 Task 是否都有红/绿阶段的测试运行记录？

### Fixer 自检

1. [ ] 每个 FAIL 项是否都有根因分析？
2. [ ] 每个修复是否附带回归测试？
3. [ ] 修复前后测试结果是否都有记录？
4. [ ] 全量测试是否通过（无回归）？
5. [ ] N > 1 时是否说明了与上次的差异？
6. [ ] 是否存在删除测试或降低标准的行为？
