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
