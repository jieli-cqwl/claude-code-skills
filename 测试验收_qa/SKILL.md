---
name: qa
description: 测试验收。在隔离上下文中启动 pipeline-qa SubAgent。
context: fork
agent: pipeline-qa
---

# /qa -- 测试验收

> 在隔离上下文中从用户视角端到端验证功能是否满足需求。

## 前置条件

`docs/pipeline/{feature}/handoff_clarify.md` 必须存在。如不存在，请先执行 `/clarify`。

## 执行流程

1. 读取 `docs/pipeline/{feature}/handoff_clarify.md`（唯一验收标准）+ `handoff_design.md`（接口信息）
2. 启动真实服务 -> 健康检查
3. 逐条验证 clarify 中的每条规则（正例/反例/边界/排除项）
4. 停止服务
5. 输出到 `docs/pipeline/{feature}/handoff_qa.md`

## Few-shot 示例

### 好的输出

```
输入分析：
- clarify 定义 F1 用户注册，3 条规则 + 2 个排除项
- 从 design 获取接口：POST /api/v1/users

验收决策：
- 以 clarify 为唯一标准，独立端到端验证
- 启动服务 -> 健康检查 -> 逐条验证 -> 停止服务

服务启动：
  $ python -m uvicorn src.main:app --port 8000
  健康检查: curl localhost:8000/health -> 200 OK

验收表：
| # | 规则 | 类型 | 期望 | 实际 | 状态 |
|---|---|---|---|---|---|
| R1 | 用户名3-20字符 | 正例 | "alice"->201 | 201 | PASS |
| R1 | 用户名3-20字符 | 反例 | "ab"->422 | 422 | PASS |
| R1 | 用户名3-20字符 | 边界 | "abc"(3字符)->201 | 201 | PASS |
| R2 | 密码>=8字符 | 正例 | "12345678"->201 | 201 | PASS |
| R2 | 密码>=8字符 | 反例 | "1234567"->422 | 500 | FAIL |
| E1 | 排除头像上传 | 排除 | 无此接口 | 无 | PASS |

FAIL 详情：
### FAIL: R2 密码>=8字符
期望行为: 密码"1234567"(7字符) -> 422 VALIDATION_ERROR
实际行为: 500 Internal Server Error
复现命令:
  curl -X POST localhost:8000/api/v1/users \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"1234567","email":"t@t.com"}'

RESULT: FAIL（1/5 规则验证未通过）
```

### 坏的输出

```
测试全部通过，功能正常。PASS
（没有逐条验收、没有端到端验证、没有正例/反例/边界、没有复现命令）
```

## 自检清单

1. 验收标准是否以 clarify 为唯一来源？（未参考 Plan/代码作为标准）
2. 是否逐条验证了 clarify 中的每条规则？
3. 每条规则是否覆盖了正例、反例、边界？
4. 排除项是否也进行了验证（确认未实现）？
5. FAIL 项是否包含三要素（期望行为/实际行为/复现命令）？
6. 是否进行了端到端验证（而非只看单元测试结果）？
7. 是否与 Check 做了差异化（未重复 Lint/测试/代码审查）？
8. 是否独立验证（未读取 handoff_run.md 或 handoff_check.md）？

## 输出格式

```markdown
# handoff_qa.md

## 输入分析
[clarify 规则理解 + design 接口信息获取]

## 验收决策
[验收方法和流程说明]

## 服务启动
[启动命令 + 健康检查结果]

## 验收表
| # | 规则 | 类型 | 期望 | 实际 | 状态 |
[逐条验证记录]

## FAIL 详情（如有）
### FAIL: [规则编号] [描述]
期望行为: [clarify 定义的预期]
实际行为: [实际观察结果]
复现命令: [完整可运行命令]

## 结果

RESULT: PASS | FAIL
[FAIL 汇总]

<metadata>{"status": "PASS|FAIL", "rules_total": N, "rules_passed": N, "rules_failed": N}</metadata>

## 交接项（FAIL 时）
- FAIL 项清单（期望行为 + 实际行为 + 复现命令）
```
