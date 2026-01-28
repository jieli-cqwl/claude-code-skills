---
name: test-gen
command: test-gen
user_invocable: true
description: 测试生成。在 TDD 开发、补充测试、提升覆盖率时使用。分析代码生成 FAILING 测试作为 TDD 起点，支持属性测试、边界值分析、规范驱动。
---

# 测试生成 (Test Generation)

> **角色**：测试工程师
> **目标**：生成高质量的 FAILING 测试，作为 TDD 的起点
> **原则**：TDD 先行、属性测试优先、禁止过度 Mock
> **思考模式**：启用 ultrathink 深度思考，系统分析测试边界

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
/test-gen ac <plan_file>     # 验收：从 /plan 验收场景生成测试框架（新增）
```

---

## 执行流程

```
/test-gen [mode] [target]
    ↓
Phase 0: 目标识别
    - 识别要测试的函数/模块
    - 检测是否已有测试（增量模式）
    - 检测依赖工具是否安装
    ↓
Phase 1: 代码分析
    - 识别函数签名、参数类型、返回类型
    - 检测是否有 API 文档 (OpenAPI/Swagger)
    - 评估风险等级 (critical/medium/low)
    ↓
Phase 2: 策略选择
    - 根据函数类型推荐测试方法
    - 确定覆盖率目标 (60%/80%/90%)
    - 生成边界值候选集
    - 决定 Mock 策略
    ↓
Phase 3: 测试生成
    - 生成 FAILING 测试（TDD 起点）
    - 每条路径 ≥3 个测试用例
    - 包含正常路径 + 错误路径 + 边界情况
    ↓
Phase 4: 质量验证
    - 运行测试（确认全部失败）
    - 检查编译成功率 (目标 100%)
    - Mock 合理性检查
    ↓
Phase 5: 输出报告
    - 测试文件
    - 预期覆盖率（需运行 coverage 验证）
    - 下一步建议
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
  2. 补充边界用例
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

### 3.4 验收场景模式（AC 模式）

从 /plan 的验收测试场景生成测试框架：

```bash
/test-gen ac docs/开发文档/plan_用户认证.md
```

**输入**：/plan 文档中的验收测试场景表格

```markdown
| AC ID | Given | When | Then |
|-------|-------|------|------|
| AC-1 | 用户已注册，邮箱 test@example.com | 正确密码登录 | 跳转首页 |
| AC-3 | 用户已注册 | 错误密码登录 | 显示"密码错误" |
```

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

```
/clarify → /design → /plan
                        ↓
              /run-plan (TDD 模式)
                   ↓
              /test-gen ← 当前
              ┌────┴────┐
              ↓         ↓
         实现代码    运行测试
              └────┬────┘
                   ↓
                /check
                   ↓
                 /qa
                   ↓
                /ship
```

**与 `/run-plan` 配合**：

```
/run-plan 执行时（TDD 模式）：
    ↓
对每个任务：
    1. 开发者调用 /test-gen --function {目标函数}
    2. /test-gen 生成 FAILING 测试
    3. 开发者实现函数
    4. 运行测试直到通过
    5. 标记任务完成
```

**触发机制**：手动触发，由开发者在实现前调用
- `/run-plan` 的 TDD 模式会提示："请先运行 `/test-gen` 生成测试"
- 开发者执行 `/test-gen --function xxx`
- 测试生成后继续实现

**上下文传递**：
- `/run-plan` 传递当前任务的目标函数名
- `/test-gen` 自动定位函数位置
- 生成的测试放在 `tests/` 对应目录

**与 `/qa` 的区别**：
| 维度 | `/test-gen` | `/qa` |
|------|-------------|-------|
| 时机 | 实现前 | 实现后 |
| 目的 | 生成测试 | 运行测试 + 验收 |
| 测试状态 | FAILING | PASSING |
| 角色 | 开发者 | 测试员 |

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

## ✅ 完成提示

```
✅ 测试生成完成

🧪 生成统计:
   - 测试文件: X 个
   - 测试用例: X 个
   - 预期覆盖: XX%（需 coverage 验证）

📁 输出:
   - tests/test_xxx.py（追加/新建）
   - tests/test_xxx_property.py（如适用）

🎯 下一步:
   1. 实现被测函数
   2. 运行 pytest 确保测试通过
   3. 运行 coverage run -m pytest && coverage report 验证覆盖率
   4. 运行 /test-gen verify 检查质量
   5. 继续 /check → /qa → /ship
```

---

**版本**：v1.2
**创建日期**：2026-01-28
**更新日期**：2026-01-28
**参考**：[调研报告](docs/设计文档/调研_test-gen.md)

**更新日志**：
- v1.2: 新增 AC 模式（从 /plan 验收场景生成测试框架）
- v1.1: 新增 Phase 0 目标识别、增量模式、依赖检测、测试命名规范、文件策略、Mock 策略与铁律对齐、/run-plan 集成说明
