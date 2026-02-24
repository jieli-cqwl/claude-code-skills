---
name: code-quality
description: 代码质量标准。五维检查框架（测试/Lint/类型/代码质量规则/AC覆盖）、客观证据要求。
user_invocable: false
---

# Code Quality - 代码质量标准

> 引用者：pipeline-checker（主用）、pipeline-implementer（引用）、pipeline-fixer（引用）

---

## 1. 五维检查框架

代码质量检查必须覆盖五个维度，缺一不可。五维全 PASS 才是 PASS。

### 维度 1：测试

- 运行全量测试（非部分测试）
- 记录：总数、通过数、失败数
- FAIL 项列出具体失败的测试名称和错误信息

```
测试: pytest tests/ -> 47 passed, 2 failed
  FAIL: test_create_user_short_username - AssertionError: expected 422, got 500
  FAIL: test_create_user_duplicate - IntegrityError not raised
```

### 维度 2：Lint

- 运行项目配置的 Lint 工具（ruff/eslint/golangci-lint 等）
- 记录：错误数、警告数
- 每条 Lint 问题列出文件路径:行号和规则名

```
Lint: ruff check src/ -> 0 errors, 3 warnings
  W1: src/api/users.py:15 - E501 line too long (92 > 88)
  W2: src/models/user.py:8 - F401 unused import 'datetime'
  W3: src/utils/hash.py:22 - E501 line too long (95 > 88)
```

### 维度 3：类型检查

- 运行项目配置的类型检查器（mypy/tsc/pyright 等）
- 如项目未配置类型检查器，标注"项目未配置，跳过"
- 记录：错误数、具体错误位置

```
类型检查: mypy src/ -> 0 errors
```

### 维度 4：代码质量规则

逐项检查以下量化规则：

| 规则 | 标准 | 检查方式 |
|------|------|---------|
| 函数长度 | <= 40 行 | 逐函数统计 |
| 函数参数 | <= 5 个 | 逐函数统计 |
| 嵌套层级 | <= 3 层 | 逐函数检查 |
| 空 catch/except | 0 个 | Grep 搜索 |
| 裸 except | 0 个 | Grep 搜索 |
| 硬编码密钥/密码 | 0 个 | Grep 搜索 |
| 占位符代码 | 0 个（NotImplementedError, TODO, FIXME） | Grep 搜索 |
| 文档同步 | 必要文档已更新/归档 | 依据 reference/文档规范.md |
| 消息 key | 无硬编码消息，新增 key 已登记 | 依据 reference/消息配置规范.md |
| 跨模块常量 | 无跨模块导入模块常量 | 依据 reference/硬编码治理规范.md |

每个违规项必须列出具体位置：

```
代码质量:
  FAIL: src/api/users.py:35 create_user() 有 6 个参数（标准 <= 5）
  FAIL: src/services/auth.py:12-68 authenticate() 共 57 行（标准 <= 40）
  PASS: 无空 catch、无裸 except、无硬编码
```

新增三类扫描同样必须给出证据：

```
文档同步:
  PASS: docs/API/接口_用户.md 已更新（git diff 证据）
消息 key:
  FAIL: 新增错误提示未登记 messages.yaml（src/api/users.py:88）
跨模块常量:
  FAIL: src/services/user.py 跨模块导入 adapters 常量（路径证据）
```

### 维度 5：AC 覆盖

逐条核对 Plan 中每个 Task 的 AC（Acceptance Criteria）：

```markdown
| Task | AC | 状态 | 证据 |
|------|-----|------|------|
| Task-1 | AC1: User.create() 返回实例 | PASS | test_create_user_success 通过 |
| Task-1 | AC2: 短用户名抛 ValidationError | FAIL | test 通过但 API 返回 500 非 422 |
| Task-2 | AC1: POST /users 返回 201 | PASS | curl 测试确认 |
```

---

## 2. 客观证据要求

每项检查结果必须附带客观证据，禁止主观描述。

### 合格的证据

- 命令输出（完整或关键片段）
- 文件路径:行号
- 具体数值（测试数量、Lint 告警数、函数行数等）
- 可复现的命令

### 不合格的证据

- "代码质量良好"
- "测试基本通过"
- "看起来没问题"
- "符合规范"
- 任何不附带具体数据的结论

---

## 3. PASS/FAIL 判定标准

### 前置步骤：偏差检测

REQUIRED：在给出 PASS 或 FAIL 结论前，必须先完成偏差自检（第 7 节）。未完成偏差自检的结论视为无效。

### 判定规则

```
偏差自检通过 + 五维全 PASS + 三类新增扫描全 PASS -> RESULT: PASS
任何一维 FAIL 或 任一新增扫描 FAIL -> RESULT: FAIL
偏差自检发现问题 -> 回到对应维度重新检查
```

FAIL 结果必须附带：
- 哪些维度 FAIL
- 每个 FAIL 的具体问题列表
- 每个问题的文件路径:行号

---

## 4. Few-shot 对比示例

### 好的检查输出

```
1. 测试: pytest tests/ -> 47 passed, 2 failed
   FAIL: test_short_username - expected ValidationError, got 500
   FAIL: test_duplicate_user - IntegrityError not caught

2. Lint: ruff check src/ -> 0 errors, 3 warnings
   W1: src/api/users.py:15 E501
   W2: src/models/user.py:8 F401
   W3: src/utils/hash.py:22 E501

3. 类型检查: mypy src/ -> 0 errors

4. 代码质量:
   FAIL: src/api/users.py:35 create_user() 6 个参数（标准 <= 5）
   PASS: 函数长度、嵌套层级、无空 catch、无裸 except、无硬编码

5. AC 覆盖:
   | Task-1/AC1 | PASS | test_create_user 通过 |
   | Task-1/AC2 | FAIL | 返回 500 非 422 |
   | Task-2/AC1 | PASS | curl 201 确认 |

RESULT: FAIL（测试 2 FAIL + 代码质量 1 FAIL）
```

### 坏的检查输出

```
代码质量良好，测试基本通过，没有明显问题。PASS
（没有五维检查、没有客观证据、没有具体数值）
```

---

## 5. 检查清单

代码质量检查完成前必须确认：

1. [ ] 五个维度是否全部检查？（测试、Lint、类型、代码质量、AC）
2. [ ] 每个 FAIL 项是否有文件路径:行号？
3. [ ] 每个结论是否有客观证据（命令输出/数值）？
4. [ ] 是否存在主观描述替代客观证据？
5. [ ] AC 是否逐条核对（而非抽查）？
6. [ ] PASS/FAIL 判定是否严格按"五维全 PASS 才 PASS"执行？

---

## 6. 常见反模式

| 反模式 | 表现 | 正确做法 |
|--------|------|---------|
| 只跑测试 | 测试通过就 PASS | 必须五维全检查 |
| 主观判断 | "代码看起来不错" | 用命令输出和数值说话 |
| 不对照 AC | 只做通用代码检查 | 逐条核对 Plan 中的 AC |
| 漏掉维度 | 忘了 Lint 或类型检查 | 五维逐一检查并记录 |
| 模糊 FAIL | "有些小问题" | 具体列出每个问题的位置和内容 |
| 跳过偏差自检 | 直接给出 PASS/FAIL 结论 | 先完成第 7 节偏差自检再判定 |

---

## 7. 检查偏差自检

> REQUIRED：在输出最终 PASS/FAIL 结论前，必须完成以下偏差检测步骤。

### 步骤 1：暂停判断

完成五维检查后，在输出结论前**暂停**。不要让检查过程中的印象主导最终判断。

### 步骤 2：逐项偏差检测

| # | 偏差 | 自检问题 | 如果回答"是" |
|---|------|---------|-------------|
| 1 | **确认偏差** | "我是否在下意识地寻找支持 PASS 的证据？" | 回到五维检查，重点审视被标为 PASS 的维度 |
| 2 | **光环效应** | "我是否因为某个维度表现好（如测试全通过）就对其他维度放松？" | 重新独立评估每个维度，不受其他维度影响 |
| 3 | **锚定偏差** | "我的判断是否受到第一个检查结果的过度影响？" | 从最后一个维度反向重新审视 |
| 4 | **可得性偏差** | "我是否只关注了最近常见的问题类型，遗漏了罕见但严重的问题？" | 逐项核对检查清单，确认每项都有客观证据 |

### 步骤 3：记录自检结果

在输出文件中记录偏差自检结果：

```
## 偏差自检
- 确认偏差：无 / 发现 -> [重新检查了 X 维度]
- 光环效应：无 / 发现 -> [重新检查了 X 维度]
- 锚定偏差：无 / 发现 -> [反向审视后调整了 X]
- 可得性偏差：无 / 发现 -> [补充检查了 X]
```

### 步骤 4：输出最终结论

偏差自检通过后，才可输出 RESULT: PASS 或 RESULT: FAIL。
