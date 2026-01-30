---
name: test-gen
command: test-gen
user_invocable: true
parallel_mode: true
description: 测试生成。在 TDD 开发、补充测试、提升覆盖率时使用。分析代码生成 FAILING 测试作为 TDD 起点，支持属性测试、边界值分析、规范驱动。
---

# 测试生成 (Test Generation)

> **角色**：测试工程师
> **目标**：生成高质量的 FAILING 测试，作为 TDD 的起点
> **原则**：TDD 先行、属性测试优先、禁止过度 Mock
> **思考模式**：启用 ultrathink 深度思考，系统分析测试边界

---

## 并行架构

> **并行模式**：按代码范围（函数/文件）拆分任务，每个 Agent 负责独立的代码单元
> **核心原则**：工作范围互斥，避免多个 Agent 分析同一段代码

### Phase 0: 代码范围识别（串行，快速）

主 Agent 快速扫描目标代码，识别需要测试的函数/类：

```bash
# 识别目标代码中的函数和类
grep -E "^(def |async def |class )" <target_file> | head -20
```

**输出**：待测试的函数/类列表（按风险等级排序）

```json
{
  "target_units": [
    {"name": "validate_email", "file": "validators.py", "line": 15, "risk": "medium"},
    {"name": "process_payment", "file": "payment.py", "line": 42, "risk": "critical"},
    {"name": "UserService", "file": "user_service.py", "line": 1, "risk": "high"}
  ],
  "total_count": 10
}
```

**⚠️ Agent 数量限制**：
- **最小 Agent 数**：2（至少需要拆分任务）
- **最大 Agent 数**：10（超过此数量收益递减，管理开销增加）
- **推荐 Agent 数**：每个 Agent 负责 1-3 个函数/类

**代码单元数量与 Agent 分配规则**：

| 代码单元数量 | Agent 数量 | 分配策略 |
|-------------|-----------|---------|
| 1-2 | 2 | 最小 Agent 数，每个 Agent 1 个代码单元 |
| 3-10 | N（=代码单元数） | 每个 Agent 1 个代码单元 |
| 11-20 | 10 | 每个 Agent 1-2 个代码单元（按风险等级分组） |
| 21-30 | 10 | 每个 Agent 2-3 个代码单元（按模块相关性分组） |
| >30 | 10 | 按模块分组，每组作为一个 Agent 任务 |

**11-30 代码单元的分组原则**：
1. **优先按模块相关性**：同一文件或同一业务模块的代码单元分到同一 Agent
2. **次优按风险等级**：相同风险等级的代码单元分到同一 Agent
3. **平衡原则**：确保每个 Agent 的工作量大致相等

---

### Phase 1: 并行代码分析（N Agent，按函数/文件拆分）

**拆分策略**：每个 Agent 负责 1-3 个函数/类（按代码范围拆分，非按维度拆分）

| Agent | 负责范围（示例） | 分析内容（全维度） |
|-------|-----------------|-------------------|
| Agent 1 | `validate_email()` | 签名、边界值、异常、依赖、状态、安全 |
| Agent 2 | `validate_phone()` | 签名、边界值、异常、依赖、状态、安全 |
| Agent 3 | `process_payment()` | 签名、边界值、异常、依赖、状态、安全 |
| Agent 4 | `UserService` 类 | 签名、边界值、异常、依赖、状态、安全 |
| ... | ... | ... |

**每个 Agent 对其负责的代码单元进行全维度分析**：
- 函数签名（参数类型、返回类型）
- 边界值（数值、字符串、集合边界）
- 异常路径（可能的异常、错误码）
- 依赖关系（外部/内部依赖）
- 状态变化（副作用、数据变更）
- 安全输入（注入风险、越权场景）

**每个 Agent 返回结构化 JSON**：
```json
{
  "agent_id": "agent_1",
  "code_unit": "validate_email",
  "file": "validators.py",
  "analysis": {
    "signature": {"params": [...], "return_type": "bool"},
    "boundaries": ["空字符串", "@符号缺失", "超长邮箱"],
    "exceptions": ["ValueError"],
    "dependencies": [],
    "state_changes": [],
    "security_risks": ["无输入校验"]
  },
  "test_scenarios": [
    {"name": "valid_email", "type": "happy_path", "priority": "P0"},
    {"name": "empty_string", "type": "boundary", "priority": "P0"},
    {"name": "no_at_symbol", "type": "boundary", "priority": "P1"}
  ],
  "risk_level": "medium"
}
```

**⏳ 等待所有 Agent 完成后继续。**

---

### Phase 2: 并行测试生成（N Agent，按函数/文件拆分）

**拆分策略**：与 Phase 1 相同，每个 Agent 为其负责的代码单元生成完整测试

| Agent | 负责范围 | 生成内容（全类型测试） |
|-------|---------|----------------------|
| Agent 1 | `validate_email()` | 正常路径 + 边界值 + 异常处理 + 属性测试 |
| Agent 2 | `validate_phone()` | 正常路径 + 边界值 + 异常处理 + 属性测试 |
| Agent 3 | `process_payment()` | 正常路径 + 边界值 + 异常处理 + 契约测试（禁 Mock） |
| Agent 4 | `UserService` 类 | 正常路径 + 边界值 + 异常处理 + 集成测试 |
| ... | ... | ... |

**每个 Agent 为其负责的代码单元生成全类型测试**：
- 正常路径测试（Happy path）
- 边界值测试（临界值、极限场景）
- 异常处理测试（错误恢复、失败处理）
- 属性测试（Hypothesis/fast-check，如适用）

#### ⛔ 禁止 Mock 约束（铁律）

**所有涉及服务调用的测试必须连接真实服务，禁止使用 Mock**

禁止使用以下 Mock 相关代码：
- Python: `@patch`, `MagicMock`, `Mock(`, `mock_`, `unittest.mock`
- JavaScript/TypeScript: `vi.fn`, `vi.mock`, `jest.fn`, `jest.mock`, `sinon.stub`
- 通用: 任何形式的 mock、stub、fake 对内部服务的替代

**例外**：仅允许对外部第三方 API（微信支付、短信网关等）进行 Mock

**检测规则**：
```bash
# 检测禁止的 Mock 用法
grep -E "@patch|MagicMock|Mock\(|mock_|vi\.fn|vi\.mock|jest\.fn|jest\.mock" tests/
# 如果检测到，测试生成失败
```

**每个 Agent 返回结构化 JSON**：
```json
{
  "agent_id": "agent_1",
  "code_unit": "validate_email",
  "file": "validators.py",
  "tests_generated": [
    {"name": "test_validate_email_with_valid_email", "type": "happy_path"},
    {"name": "test_validate_email_with_empty_string", "type": "boundary"},
    {"name": "test_validate_email_with_no_at_symbol", "type": "boundary"},
    {"name": "test_validate_email_property", "type": "property"}
  ],
  "test_code": "...",
  "required_fixtures": ["db_session", "test_client"],
  "mock_violations": []
}
```

**⏳ 等待所有 Agent 完成后继续。**

---

### Phase 3: 汇总合并（串行）

> **用户进度提示**：在执行每个 Phase 前输出进度信息

```markdown
📊 /test-gen 执行进度

⏳ Phase 0: 代码范围识别... ✅ 完成（识别 X 个函数/类）
⏳ Phase 1: 代码分析（X 个代码单元并行）... ⏳ 执行中
⏳ Phase 2: 测试生成
⏳ Phase 3: 汇总合并
```

主 Agent 执行以下汇总任务：

1. **收集所有测试**：合并各 Agent 生成的测试用例（每个 Agent 负责独立代码单元，无需去重）
   - **fixture 统一生成**：Agent 只生成测试函数代码，不生成 conftest.py 或 fixture 定义。主 Agent 根据所有 Agent 返回的 `required_fixtures` 字段，集中生成统一的 fixture 定义，避免多 Agent 并行生成导致的 fixture 重复冲突
   - **fixture 冲突处理规则**：
     - 同名 fixture 合并：保留功能最完整的版本（含更多参数化配置的优先）
     - 依赖冲突：按依赖链顺序排列（被依赖的 fixture 在前）
     - scope 冲突：取最宽 scope（session > module > function）
     - 类型冲突：保留与项目技术栈一致的版本（同步/异步根据项目配置决定）
   - **fixture 冲突检测算法**：
     ```python
     # 主 Agent 汇总时执行
     def merge_fixtures(all_agent_fixtures):
         grouped = group_by_name(all_agent_fixtures)
         for name, fixtures in grouped.items():
             if len(fixtures) > 1:
                 # 1. 检查类型兼容性（见下方详细规则）
                 # 2. 按参数化配置数量排序，取最完整版本
                 # 3. 记录合并日志
         return merged_fixtures, merge_log
     ```
   - **类型兼容性检测详细规则**：
     ```python
     def check_type_compatibility(fixtures: list[Fixture]) -> CompatibilityResult:
         """
         检测同名 fixture 的类型兼容性

         返回：
           - compatible: bool - 是否兼容
           - winner: Fixture - 应保留的版本
           - reason: str - 决策原因
         """
         # 1. 识别 fixture 类型
         types = []
         for f in fixtures:
             if is_async_fixture(f):
                 types.append("async")
             else:
                 types.append("sync")

         # 2. 类型冲突检测
         unique_types = set(types)
         if len(unique_types) == 1:
             # 类型一致，无冲突
             return CompatibilityResult(compatible=True, ...)

         # 3. 类型不一致时的决策规则
         # 检查项目配置（pyproject.toml / pytest.ini）
         project_async_mode = detect_project_async_mode()

         if project_async_mode == "strict_async":
             # 项目强制异步模式：选择 async fixture
             winner = select_by_type(fixtures, "async")
         elif project_async_mode == "sync_only":
             # 项目不支持异步：选择 sync fixture
             winner = select_by_type(fixtures, "sync")
         else:
             # 默认：选择与大多数测试兼容的版本
             winner = select_by_majority_usage(fixtures)

         return CompatibilityResult(
             compatible=False,
             winner=winner,
             reason=f"类型冲突：{unique_types}，选择 {winner.type}（项目配置：{project_async_mode}）"
         )

     def is_async_fixture(fixture: Fixture) -> bool:
         """
         识别 async fixture 的规则：
         1. 函数定义包含 `async def`
         2. 使用 `@pytest.fixture` 且装饰器链包含 `@pytest_asyncio.fixture`
         3. fixture 返回类型为 AsyncGenerator 或 Coroutine
         """
         # 规则 1：检查函数定义
         if "async def" in fixture.source_code:
             return True

         # 规则 2：检查装饰器
         if "@pytest_asyncio.fixture" in fixture.decorators:
             return True

         # 规则 3：检查返回类型注解
         async_return_types = ["AsyncGenerator", "Coroutine", "Awaitable"]
         if any(t in fixture.return_type for t in async_return_types):
             return True

         return False

     def detect_project_async_mode() -> str:
         """
         检测项目的异步测试配置

         检查位置（按优先级）：
         1. pyproject.toml [tool.pytest.ini_options] asyncio_mode
         2. pytest.ini asyncio_mode
         3. conftest.py 中的 pytest_plugins 是否包含 pytest_asyncio

         返回值：
         - "strict_async": 项目使用 asyncio_mode=strict
         - "auto_async": 项目使用 asyncio_mode=auto
         - "sync_only": 项目未配置异步测试
         """
         ...
     ```
2. **Mock 合规检查**：
   - 扫描所有生成的测试代码
   - **输出不得包含 Mock 相关代码**（对内部服务）
   - 发现违规立即删除并记录
3. **格式化输出**：
   - 统一测试命名规范
   - 按代码单元分组（每个函数/类的测试在一起）
   - 添加测试文档注释
4. **生成测试文件**：
   - 输出到 `tests/test_[功能名]_acceptance.py`

**汇总输出**：
```
📊 并行生成统计：
   - 识别代码单元: X 个函数/类
   - Phase 1 分析 Agent: X 个全部完成
   - Phase 2 生成 Agent: X 个全部完成
   - 生成测试用例: XX 个（无重复，每个 Agent 负责独立代码）
   - Mock 合规检查: ✅ 通过（无禁止的 Mock 用法）

📁 输出文件: tests/test_[功能名]_acceptance.py
```

---

### 错误处理规范

#### Agent 失败处理

| 失败类型 | 处理策略 |
|---------|---------|
| 单个 Agent 超时 | 等待 60 秒（见 AC 文档超时配置表）后跳过该代码单元，记录警告，继续执行 |
| 单个 Agent 异常 | 记录错误日志，该代码单元标记为"未生成测试" |
| 多个 Agent 失败（≥50%） | 停止执行，报告失败原因，建议重试 |
| 全部 Agent 失败 | 停止执行，报告失败原因，等待用户决策 |

#### 错误恢复

```
⚠️ 并行执行异常：

失败 Agent（按代码单元）:
  - Agent 2 (validate_phone): 超时
  - Agent 4 (UserService): 依赖缺失

处理策略: 跳过失败 Agent，继续执行
影响评估: validate_phone 和 UserService 未生成测试，建议后续单独补充

继续执行? [Y/n]（推荐 Y，已失败的代码单元可后续单独补充）
```

#### Phase 间依赖检查

```
Phase 0 → Phase 1 门控检查:
  - Phase 0 代码识别: 必须成功识别至少 1 个代码单元
  - 失败时: 停止并报告，提示用户指定目标代码

Phase 1 → Phase 2 门控检查:
  - Phase 1 完成率: ≥50%（至少一半代码单元分析成功）
  - 失败时: 仅对成功分析的代码单元生成测试
```

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**生成测试**"或"**测试生成**"（主触发词）
- 使用命令：`/test-gen`
- 说"写测试"、"补测试"
- 说"TDD"、"先写测试"
- 说"提升测试覆盖率"

**适用场景**：
- TDD 开发，先写失败测试
- 已有代码需要补充测试
- 提升测试覆盖率

---

## 文档契约（铁律）

> **原则**：没有输入文档 → 不能执行；没有输出文档 → 不算完成

### 输入文档（门控检查）

**from-clarify 模式（推荐）**：

| 文档 | 路径 | 必须 | 检查命令 |
|------|------|------|---------|
| **AC 文档** | `docs/需求文档/clarify_[功能名].md` | ✅ 必须 | `ls docs/需求文档/clarify_*.md` |
| **计划文档** | `docs/开发文档/plan_[功能名].md` | ⚠️ 推荐 | `ls docs/开发文档/plan_*.md` |

**门控规则**：
```bash
# 门控检查：AC 文档必须存在
CLARIFY_DOC=$(ls docs/需求文档/clarify_*.md 2>/dev/null | head -1)
if [ -z "$CLARIFY_DOC" ]; then
  echo "❌ 门控失败: AC 文档不存在"
  echo "   修复: 先执行 /clarify 生成需求文档"
  exit 1
fi
echo "✅ AC 文档: $CLARIFY_DOC"

# 检查计划文档（推荐）
PLAN_DOC=$(ls docs/开发文档/plan_*.md 2>/dev/null | head -1)
if [ -z "$PLAN_DOC" ]; then
  echo "⚠️ 计划文档不存在，建议先执行 /plan"
else
  echo "✅ 计划文档: $PLAN_DOC"
fi
```

**门控失败处理**：
- AC 文档不存在 → **停止执行**，先执行 `/clarify`
- 计划文档不存在 → 警告，建议先执行 `/plan`

### 输出文档（强制）

| 文档 | 路径 | 用途 |
|------|------|------|
| **测试文件** | `tests/test_[功能名]_acceptance.py` | /run-plan 门控依赖 |

**输出规则**：
- 未输出测试文件 → **不算完成**
- 完成提示必须包含输出文件的完整路径
- 测试必须是 FAILING 状态（TDD 起点）

**下游依赖**：
- `/run-plan` 依赖此文件（门控3）

---

## 核心原则

**"没有先失败的测试，就没有生产代码"**

测试生成的目标不是让测试通过，而是生成**会失败的测试**，驱动正确的实现。

**"覆盖率 80% 是工程甜点"**

追求 100% 覆盖率收益递减，80% 是性价比最高的目标。关键路径（支付/认证）除外。

---

## 何时使用

| 场景 | 使用 |
|------|------|
| TDD 开发新功能 | ✅ 必须（先生成 FAILING 测试） |
| 补充现有代码测试 | ✅ 推荐 |
| 提升测试覆盖率 | ✅ 推荐 |
| 重构前补测试 | ✅ 必须（确保行为不变） |
| 从 API 文档生成测试 | ✅ 用 `/test-gen spec` |
| 代码审查 | ❌ 用 `/check` |
| 最终验收 | ❌ 用 `/qa` |

### 支持的语言和框架

| 语言 | 支持程度 | 测试框架 | 属性测试 |
|------|----------|----------|----------|
| **Python** | ✅ 完整支持 | pytest | Hypothesis |
| **JavaScript/TypeScript** | ✅ 完整支持 | Jest/Vitest | fast-check |
| **Java** | ⚠️ 基础支持 | JUnit | QuickCheck |
| **Go** | ⚠️ 基础支持 | testing | rapid |

---

## 执行模式

```bash
/test-gen                    # 默认：分析 + 生成 FAILING 测试
/test-gen quick <function>   # 快速：单函数测试 (<1min)
/test-gen full <module>      # 全面：模块级 + 覆盖率报告
/test-gen spec <openapi>     # 规范：从 OpenAPI/Swagger 生成
/test-gen property <function> # 属性：生成属性测试 (Hypothesis/fast-check)
/test-gen verify             # 验证：检查现有测试质量
/test-gen boundary <function> # 边界：专注边界值分析
/test-gen ac <plan_file>     # ⚠️ 已废弃，请使用 from-clarify
/test-gen from-clarify <clarify_doc>  # ✅ 推荐：从 /clarify AC 表格生成测试
```

### 🆕 推荐流程：测试先行

```
/clarify 输出 AC 表格
    ↓
/design 输出架构设计
    ↓
/plan 输出实施计划（引用 AC）
    ↓
/test-gen from-clarify <clarify_doc>  ← 在开发之前执行
    ↓ 输出：FAILING 测试（开发的验收标准）
    ↓
/run-plan 执行开发（基于已有测试，严格 TDD）
```

**为什么测试要在开发之前？**
- 测试是开发的验收标准，先有标准才有实现
- 避免"先写代码后补测试"的假 TDD
- 测试之后写的测试会被实现偏见影响

---

## 执行流程

> **Phase 编号说明**：并行架构使用 Phase 0-3（代码范围识别→并行分析→并行生成→汇总），
> 下方是完整执行视角的细分步骤。

```
/test-gen [mode] [target]
    ↓
Phase 0: 代码范围识别（并行架构 Phase 0）
    - 识别要测试的函数/模块（按代码范围拆分）
    - 检测是否已有测试（增量模式）
    - 检测依赖工具是否安装
    - 输出：待测代码单元列表（最多 10 个 Agent）
    ↓
Phase 1: 并行代码分析（并行架构 Phase 1）
    - N 个 Agent 并行分析各自负责的代码单元
    - 每个 Agent 做全维度分析：签名、边界、异常、依赖
    - 评估风险等级 (critical/medium/low)
    ↓
Phase 2: 并行测试生成（并行架构 Phase 2）
    - N 个 Agent 并行生成各自负责的测试
    - 每个 Agent 生成全类型测试：正常路径、边界值、异常处理
    - 检测 Mock 合规（禁止 Mock 内部服务）
    ↓
Phase 3: 汇总与输出（并行架构 Phase 3）
    - 合并各 Agent 生成的测试用例
    - Mock 合规最终检查
    - 格式化输出测试文件
    - 运行测试确认全部 FAILING（TDD 起点）
```

---

## Phase 0: 目标识别

### 目标定位方式

```bash
# 方式 1：指定文件
/test-gen --file src/services/user_service.py

# 方式 2：指定函数
/test-gen --function validate_email

# 方式 3：指定模块
/test-gen --module src/services/

# 方式 4：自动识别（默认）
/test-gen  # 分析最近修改的文件
```

### 增量模式检测

**检测已有测试**：
```
检测到 validate_email() 已有测试：
  - tests/test_validators.py::test_validate_email_basic (3 个用例)

选择操作：
  1. 跳过（已有测试）
  2. 补充边界用例（推荐，增量提升覆盖率）
  3. 重新生成（覆盖）
  4. 生成属性测试（补充）

请选择 [1/2/3/4]:
```

### 依赖检测

**检测必要工具**：

| 工具 | 用途 | 安装命令 |
|------|------|---------|
| pytest | 测试框架 | `pip install pytest` |
| hypothesis | 属性测试 | `pip install hypothesis` |
| coverage | 覆盖率 | `pip install coverage` |
| fast-check | JS 属性测试 | `npm install fast-check` |

**未安装时提示**：
```
⚠️ 检测到以下工具未安装：
   - hypothesis (属性测试需要)

🔧 是否自动安装？
   1. 自动安装 (pip install hypothesis)
   2. 跳过属性测试，仅生成普通测试
   3. 取消

请选择 [1/2/3]:
```

---

## Phase 1: 代码分析

### 风险等级评估

| 关键词 | 风险等级 | 覆盖率目标 | 说明 |
|--------|----------|------------|------|
| `payment`, `pay`, `charge` | 🔴 关键 | 90%+ | 支付相关，不能出错 |
| `auth`, `login`, `token` | 🔴 关键 | 90%+ | 认证相关，安全敏感 |
| `password`, `secret`, `key` | 🔴 关键 | 90%+ | 密钥相关 |
| `validate`, `check`, `verify` | 🟡 中等 | 80% | 验证逻辑 |
| `calculate`, `compute`, `process` | 🟡 中等 | 80% | 计算逻辑 |
| `format`, `convert`, `parse` | 🔵 基础 | 70% | 转换工具 |
| `log`, `print`, `debug` | ⚪ 低 | 60% | 辅助功能 |

### 类型分析

```python
# 示例：分析函数签名
def validate_email(email: str) -> bool:
    ...

# 分析结果：
# - 输入：str（需测试空串、特殊字符、超长）
# - 输出：bool（需测试 True/False 两条路径）
# - 关键词：validate（中等风险，80% 覆盖）
```

---

## Phase 2: 策略选择

### 测试方法推荐矩阵

| 函数类型 | 推荐方法 | 示例 |
|---------|---------|------|
| 纯函数（输入→输出） | **属性测试** | 排序、计算、转换 |
| 验证函数 | 边界值 + 等价类 | email 验证、表单校验 |
| 状态机 | 状态转换测试 | 订单状态、工作流 |
| API 端点 | 规范驱动 + 集成 | REST API |
| 数据库操作 | 集成测试（真实 DB） | CRUD 操作 |
| 复杂业务规则 | 决策表 | 折扣计算、权限判断 |

### 边界值候选生成

| 类型 | 边界值 |
|------|--------|
| **字符串** | `""`（空）、`" "`（空格）、`"a"*1000`（超长）、特殊字符、Unicode |
| **数字** | `0`、`-1`、`MAX_INT`、`MIN_INT`、小数边界 |
| **列表** | `[]`（空）、`[1]`（单元素）、大列表、嵌套列表 |
| **日期** | 闰年、月末、跨年、时区边界 |
| **None/null** | 所有可选参数 |

### Mock 策略决策

> **与 RULES.md 铁律对齐**：测试必须连接真实数据库和服务

| 依赖类型 | Mock 策略 | 原因 |
|---------|----------|------|
| **数据库** | ❌ 禁止 Mock | 测试真实 SQL 行为（铁律） |
| **内部服务** | ❌ 禁止 Mock | 测试真实服务交互（铁律） |
| **外部第三方 API** | ✅ 可以 Mock | 微信支付、短信网关等不可控、有成本 |
| **文件系统** | ⚠️ 视情况 | 简单读写可真实，复杂场景 Mock |
| **时间** | ✅ 建议 Mock | 确保可重复 |
| **随机数** | ✅ 建议固定种子 | 确保可重复 |

**内部服务 vs 外部第三方的区分**：

| 类型 | 示例 | Mock 策略 |
|------|------|----------|
| **内部服务** | 用户服务、订单服务、消息队列 | ❌ 禁止 Mock |
| **外部第三方** | 微信支付、支付宝、短信网关、地图 API | ✅ 可以 Mock |

**原因**：内部服务是我们能控制的，Mock 会隐藏真实问题；外部第三方不可控且有成本。

---

## Phase 3: 测试生成

### 测试命名规范

**命名模板**：`test_{function}_{scenario}_{expected}`

| 组成部分 | 说明 | 示例 |
|---------|------|------|
| `{function}` | 被测函数名 | `validate_email` |
| `{scenario}` | 测试场景 | `with_empty_string` |
| `{expected}` | 预期结果（可选） | `returns_false` |

**示例**：
```python
# 完整格式
def test_validate_email_with_empty_string_returns_false():
    ...

# 简化格式（场景已隐含预期）
def test_validate_email_with_valid_email():
    ...

# 边界值格式
def test_validate_email_boundary_max_length():
    ...
```

### 测试文件策略

| 场景 | 文件策略 |
|------|---------|
| 新模块 | 创建 `tests/test_{module}.py` |
| 已有测试文件 | 追加到现有文件末尾 |
| 属性测试 | 单独创建 `tests/test_{module}_property.py` |
| 集成测试 | 创建 `tests/integration/test_{module}.py` |

**文件存在时的处理**：
```
检测到测试文件已存在：tests/test_validators.py

选择操作：
  1. 追加到文件末尾
  2. 创建新文件 tests/test_validators_new.py
  3. 覆盖现有文件（危险）

请选择 [1/2/3]:
```

### 3.1 TDD 模式（默认）

生成 **FAILING** 测试，作为 TDD 起点：

```python
# 生成的测试（函数尚未实现）
def test_validate_email_with_valid_email():
    """有效邮箱应返回 True"""
    assert validate_email("user@example.com") == True  # 会失败

def test_validate_email_with_empty_string():
    """空字符串应返回 False"""
    assert validate_email("") == False  # 会失败

def test_validate_email_with_no_at_symbol():
    """无 @ 符号应返回 False"""
    assert validate_email("userexample.com") == False  # 会失败
```

### 3.2 属性测试模式

使用 Hypothesis/fast-check 生成属性测试：

```python
from hypothesis import given, strategies as st

@given(st.emails())
def test_valid_emails_should_pass(email):
    """所有有效邮箱格式都应通过验证"""
    assert validate_email(email) == True

@given(st.text().filter(lambda x: "@" not in x))
def test_strings_without_at_should_fail(text):
    """不含 @ 的字符串都应失败"""
    assert validate_email(text) == False
```

### 3.3 边界值模式

专注边界情况：

```python
import pytest

class TestValidateEmailBoundary:
    """边界值测试"""

    @pytest.mark.parametrize("email,expected", [
        ("", False),                      # 空字符串
        ("@", False),                     # 只有 @
        ("a@b", False),                   # 最短无效
        ("a@b.c", True),                  # 最短有效
        ("a" * 64 + "@example.com", True), # 本地部分最大长度
        ("a" * 65 + "@example.com", False), # 超过最大长度
        ("user@" + "a" * 255 + ".com", False), # 域名超长
    ])
    def test_boundary_values(self, email, expected):
        assert validate_email(email) == expected
```

### 3.4 从 /clarify AC 生成测试（推荐）

> 🆕 **测试先行模式**：在 /plan 之后、/run-plan 之前执行

```bash
/test-gen from-clarify docs/需求文档/clarify_用户认证.md
```

**输入**：/clarify 文档中的 AC 表格（单一来源）

```markdown
##### 正常流程
| AC-ID | Given（前置条件） | When（操作） | Then（预期结果） | 优先级 |
|-------|------------------|-------------|-----------------|--------|
| AC-1 | 用户已注册，邮箱 test@example.com | 正确密码登录 | 跳转首页，显示"欢迎回来" | P0 |

##### 异常流程
| AC-ID | Given | When | Then | 优先级 |
|-------|-------|------|------|--------|
| AC-3 | 用户已注册 | 错误密码登录 | 显示"密码错误"，停留登录页 | P1 |
```

**特点**：
- 直接从 /clarify 的 AC 单一来源生成，确保一致性
- 测试名直接引用 AC-ID，便于追溯
- 生成的是 FAILING 测试，作为开发的验收标准

---

### 3.5 验收场景模式（AC 模式 - ⚠️ 已废弃）

> ⚠️ **此模式已废弃**：请使用 `from-clarify` 模式，直接从 AC 单一来源生成
> **废弃原因**：/plan 的验收场景是引用 /clarify 的 AC，不是单一来源

```bash
# ⚠️ 已废弃
/test-gen ac docs/开发文档/plan_用户认证.md

# ✅ 推荐
/test-gen from-clarify docs/需求文档/clarify_用户认证.md
```

**如果仍需使用**（仅用于兼容旧项目）：

```markdown
| AC ID | Given | When | Then |
|-------|-------|------|------|
| AC-1 | 用户已注册，邮箱 test@example.com | 正确密码登录 | 跳转首页 |
| AC-3 | 用户已注册 | 错误密码登录 | 显示"密码错误" |
```

**迁移建议**：将 /plan 中的验收场景移到 /clarify 输出的 AC 表格，然后使用 `from-clarify` 模式

**输出**：测试框架代码

```python
# tests/test_auth_acceptance.py
# 从 plan_用户认证.md 验收场景自动生成

import pytest

class TestAuthAcceptance:
    """验收测试：用户认证"""

    def test_ac1_login_with_correct_password(self, test_db):
        """AC-1: 用户已注册，正确密码登录 → 跳转首页"""
        # Given: 用户已注册，邮箱 test@example.com
        user = create_test_user(email="test@example.com", password="TestPass123!")

        # When: 正确密码登录
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })

        # Then: 跳转首页（返回 token）
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_ac3_login_with_wrong_password(self, test_db):
        """AC-3: 用户已注册，错误密码登录 → 显示密码错误"""
        # Given: 用户已注册
        user = create_test_user(email="test@example.com", password="TestPass123!")

        # When: 错误密码登录
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword!"
        })

        # Then: 显示"密码错误"
        assert response.status_code == 401
        assert "密码错误" in response.json()["detail"]
```

**特点**：
- 测试名直接引用 AC ID，便于追溯
- Given/When/Then 作为注释，与验收场景对应
- 生成的是 FAILING 测试（函数未实现时）

---

### 3.5 决策表模式

复杂业务规则使用决策表：

```python
import pytest

class TestDiscountCalculation:
    """折扣计算决策表测试"""

    @pytest.mark.parametrize("is_member,order_amount,coupon,expected_discount", [
        # 会员 | 金额 | 优惠券 | 预期折扣
        (True,  100,  None,   0.1),   # 会员无券：10%
        (True,  100,  "VIP",  0.2),   # 会员+VIP券：20%
        (False, 100,  None,   0.0),   # 非会员无券：0%
        (False, 100,  "NEW",  0.05),  # 非会员+新人券：5%
        (True,  500,  "VIP",  0.25),  # 会员+VIP券+大额：25%
    ])
    def test_discount_decision_table(self, is_member, order_amount, coupon, expected_discount):
        result = calculate_discount(is_member, order_amount, coupon)
        assert result == expected_discount
```

---

## Phase 4: 质量验证

### 测试质量检查清单

**编译检查**：
- [ ] 所有测试文件能正确导入
- [ ] 所有测试能运行（即使失败）
- [ ] 无语法错误

**TDD 检查**（仅限 TDD 模式）：
- [ ] 所有测试确实失败（函数未实现）
- [ ] 失败原因是断言失败，不是导入错误

**Mock 检查**：
- [ ] 未 Mock 数据库（除非有充分理由）
- [ ] Mock 对象有交互验证
- [ ] 无"测试 Mock 本身"的情况

**覆盖检查**：
- [ ] 正常路径有测试
- [ ] 错误路径有测试
- [ ] 边界情况有测试
- [ ] 异常情况有测试

### Mock 过度检测

**危险信号**：
```python
# ❌ 过度 Mock：测试了什么？
def test_save_user(mock_db, mock_validator, mock_logger):
    mock_validator.return_value = True
    mock_db.save.return_value = True
    result = save_user({"name": "test"})
    assert result == True  # 测试的是 Mock，不是真实逻辑
```

**正确做法**：
```python
# ✅ 真实数据库测试
def test_save_user(test_db):  # test_db 是真实的测试数据库
    result = save_user({"name": "test"})
    assert result == True
    # 验证数据库中确实存在
    user = test_db.query(User).filter_by(name="test").first()
    assert user is not None
```

---

## Phase 5: 输出报告

### 终端输出

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 测试生成报告 - validate_email
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 分析结果:
   风险等级: 🟡 中等 (validate)
   覆盖目标: 80%
   推荐方法: 边界值 + 属性测试

🧪 生成的测试:
   ✗ test_validate_email_with_valid_email (FAILING)
   ✗ test_validate_email_with_empty_string_returns_false (FAILING)
   ✗ test_validate_email_with_no_at_symbol_returns_false (FAILING)
   ✗ test_validate_email_boundary_max_length (FAILING)
   ✗ test_valid_emails_property (FAILING)
   共 5 个测试，全部失败（符合 TDD 预期）

📁 输出文件: tests/test_validate_email.py（追加到现有文件）
📈 预期覆盖率: ~80%（实际需运行 coverage 验证）

🎯 下一步:
   1. 实现 validate_email() 函数
   2. 运行 pytest tests/test_validate_email.py
   3. 确保所有测试通过
   4. 运行 coverage run -m pytest && coverage report 验证实际覆盖率
   5. 运行 /test-gen verify 检查测试质量
```

### 测试文件结构

```
tests/
├── test_validate_email.py      # 单元测试
├── test_validate_email_property.py  # 属性测试（如适用）
└── conftest.py                 # fixtures（如需要）
```

---

## 危险信号（停止并报告）

- 函数有 10+ 个参数（需要先重构）
- 函数超过 100 行（需要先拆分）
- 无法确定函数的预期行为（需要先澄清需求）
- 测试需要 Mock 5+ 个依赖（设计可能有问题）

---

## 常见借口（都是错的）

| 借口 | 现实 |
|------|------|
| "先写代码再补测试" | 补的测试往往是为了覆盖率，不是为了质量 |
| "这个函数太简单不用测" | 简单函数的 Bug 往往最难发现 |
| "测试太花时间" | 没有测试的代码花更多时间调试 |
| "Mock 一切更快" | Mock 的测试不测真实逻辑，没有价值 |
| "100% 覆盖率才放心" | 80% 高质量测试 > 100% 低质量测试 |

---

## 与其他 Skills 的关系

### 🆕 推荐流程（测试先行）

```
/clarify（需求澄清）
    ↓ 输出：AC 表格（单一来源）
/explore（方案探索）
    ↓
/design（架构设计）
    ↓
/plan（写计划）
    ↓ 引用 AC，输出实施计划
/test-gen from-clarify ← 当前（测试先行）
    ↓ 从 AC 生成 FAILING 测试
    ↓ [门控：测试必须存在才能开发]
/run-plan（执行计划）
    ↓ 基于已有测试，严格 TDD
/check（开发检查）
    ↓
/qa（测试验收）
    ↓ 基于 AC 验收
/ship（代码交付）
```

### 为什么测试要在 /plan 之后、/run-plan 之前？

1. **测试是开发的验收标准**：先有标准，才有实现
2. **避免假 TDD**：先写代码后补测试 ≠ TDD
3. **保证 AC 一致性**：测试直接从 AC 生成，不会偏离需求

### 两种使用方式

#### 方式一：测试先行（推荐）

```
/plan 完成后，/run-plan 之前：
    ↓
/test-gen from-clarify <clarify_doc>
    ↓ 生成所有 AC 对应的 FAILING 测试
    ↓
/run-plan 执行
    ↓ 开发者基于已有测试实现功能
    ↓ RED → GREEN → REFACTOR
```

#### 方式二：开发中生成（兼容旧流程）

```
/run-plan 执行时（TDD 模式）：
    ↓
对每个任务：
    1. 开发者调用 /test-gen --function {目标函数}
    2. /test-gen 生成 FAILING 测试
    3. 开发者实现函数
    4. 运行测试直到通过
```

### 与 `/qa` 的区别

| 维度 | `/test-gen` | `/qa` |
|------|-------------|-------|
| 时机 | 实现前 | 实现后 |
| 目的 | 生成测试 | 运行测试 + 验收 |
| 测试状态 | FAILING | PASSING |
| 角色 | 测试工程师（前置） | 测试员（验收） |
| AC 使用 | 从 AC 生成测试 | 基于 AC 验收 |

---

## 完成检查清单

- [ ] 目标识别完成（函数/模块定位）
- [ ] 依赖检测通过（pytest/hypothesis 等）
- [ ] 增量检测完成（已有测试处理）
- [ ] 代码分析完成（类型、风险、边界）
- [ ] 测试策略已选择
- [ ] 测试命名符合规范
- [ ] 测试文件已生成（追加/新建）
- [ ] 测试能编译运行
- [ ] TDD 模式：测试全部失败
- [ ] Mock 检查通过（内部服务未 Mock）
- [ ] 边界情况已覆盖

---

## ⛔ 边界约束（铁律）

> **`/test-gen` 的职责边界：只做测试生成，不能跳过测试**

| 禁止行为 | 说明 |
|---------|------|
| ❌ 跳过测试生成直接进入 `/run-plan` | 测试先行是铁律 |
| ❌ 生成测试后直接写实现代码 | 实现代码是 `/run-plan` 的职责 |

**正确的完成动作**：
1. 输出测试文件到 `tests/test_[功能名]_acceptance.py`
2. 展示完成提示
3. 进入下一环节 `/run-plan`（正常流转）或等待用户指令

**跳过环节的处理**：
- 测试生成不能跳过（铁律：测试先行）

---

## ⛔ 铁律约束

| 约束 | 要求 |
|------|------|
| **TDD 优先** | 默认生成 FAILING 测试，驱动实现 |
| **禁止 Mock 数据库** | 测试必须连接真实测试数据库（铁律） |
| **禁止 Mock 内部服务** | 内部服务必须真实调用（铁律） |
| **外部第三方可 Mock** | 微信支付、短信网关等不可控服务可以 Mock |
| **覆盖率务实** | 80% 是目标，关键路径 90%+（预期值，需 coverage 验证） |
| **质量 > 数量** | 5 个高质量测试 > 20 个低质量测试 |
| **测试位置** | 必须放在 `tests/` 目录 |
| **命名规范** | `test_{function}_{scenario}_{expected}` |

---

## 🔴 TDD 铁律

> 详细规范见：`~/.claude/reference/TDD规范.md`

### 核心原则

```
没有先失败的测试，就没有生产代码
```

**测试之前就写了代码？删掉它。重新开始。**

### Red-Green-Refactor 循环

```
🔴 RED（写失败测试）→ 🟢 GREEN（最小实现）→ 🔄 REFACTOR（清理）→ 重复
```

### 快速检查清单

- [ ] 看到测试失败了吗？（RED）
- [ ] 写的是最小实现吗？（GREEN）
- [ ] 所有测试仍然通过吗？（REFACTOR）

### 危险信号

- 测试之前写代码 → **删除代码，重新开始**
- 测试立即通过 → 修复测试
- 无法解释失败原因 → 重新理解需求

**完整的 TDD 流程、常见借口、测试反模式，请阅读**：`~/.claude/reference/TDD规范.md`

---

## ✅ 完成提示

```
✅ 测试生成完成

📁 输出文件：tests/test_[功能名]_acceptance.py
📎 前置文档：
   - AC 文档：docs/需求文档/clarify_[功能名].md
   - 计划文档：docs/开发文档/plan_[功能名].md

🧪 生成统计:
   - 测试文件: X 个
   - 测试用例: X 个（全部 FAILING）
   - 预期覆盖: XX%（需 coverage 验证）

🔴 测试状态：FAILING（符合 TDD 预期）
   - 这些测试是开发的验收标准
   - /run-plan 将基于这些测试进行 TDD 开发

🎯 下一步：
   1. 执行 /run-plan（基于已有测试，严格 TDD）
   2. 开发完成后执行 /check
   3. 检查通过后执行 /qa

📋 /clear 后可直接执行（复制粘贴）：
   /run-plan docs/开发文档/plan_[功能名].md
```
