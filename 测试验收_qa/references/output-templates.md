# 输出模板

## master.md 格式（按 UNIT 验收）

适用条件：master.md 存在时使用此格式

```markdown
# handoff_qa.md

## 输入分析
[master.md 全局约束理解 + UNIT 列表 + design 接口信息获取]

## 决策
[验收方法和流程说明：按 UNIT 逐个验收]

## 产出
INFRA_ERROR: yes|no

### 服务启动
[启动命令 + 健康检查结果]

### 全局约束验证
| # | 约束 | 状态 | 证据 |
[全局约束逐条验证记录]

### UNIT-1: [UNIT 名称]
| # | 规则 | 类型 | 期望 | 实际 | 状态 |
[逐条验证记录]

### UNIT-2: [UNIT 名称]
| # | 规则 | 类型 | 期望 | 实际 | 状态 |
[逐条验证记录]

### FAIL 详情（如有）
### FAIL: [UNIT-N/规则编号] [描述]
期望行为: [需求文档定义的预期]
实际行为: [实际观察结果]
复现命令: [完整可运行命令]

### 偏差自检
- 信任偏差：无 / 发现 -> [...]
- 正常路径偏差：无 / 发现 -> [...]
- 结果确认偏差：无 / 发现 -> [...]

### 结果

RESULT: PASS | FAIL
[FAIL 汇总]

### 交接项清单
- 逐条规则的 PASS/FAIL 与证据
- 反例/边界/正例的验证顺序说明
- INFRA_ERROR 标记与触发原因（如 yes）

<metadata>{"status": "PASS|FAIL", "units_total": N, "units_passed": N, "units_failed": N, "rules_total": N, "rules_passed": N, "rules_failed": N}</metadata>

### 交接项（FAIL 时）
- FAIL 项清单（期望行为 + 实际行为 + 复现命令）
```

## handoff_clarify.md 格式（按规则验收，向后兼容）

适用条件：仅 handoff_clarify.md 存在时使用此格式

```markdown
# handoff_qa.md

## 输入分析
[clarify 规则理解 + design 接口信息获取]

## 决策
[验收方法和流程说明]

## 产出
INFRA_ERROR: yes|no

### 服务启动
[启动命令 + 健康检查结果]

### 验收表
| # | 规则 | 类型 | 期望 | 实际 | 状态 |
[逐条验证记录]

### FAIL 详情（如有）
### FAIL: [规则编号] [描述]
期望行为: [clarify 定义的预期]
实际行为: [实际观察结果]
复现命令: [完整可运行命令]

### 偏差自检
- 信任偏差：无 / 发现 -> [...]
- 正常路径偏差：无 / 发现 -> [...]
- 结果确认偏差：无 / 发现 -> [...]

### 结果

RESULT: PASS | FAIL
[FAIL 汇总]

### 交接项清单
- 逐条规则的 PASS/FAIL 与证据
- 反例/边界/正例的验证顺序说明
- INFRA_ERROR 标记与触发原因（如 yes）

<metadata>{"status": "PASS|FAIL", "rules_total": N, "rules_passed": N, "rules_failed": N}</metadata>

### 交接项（FAIL 时）
- FAIL 项清单（期望行为 + 实际行为 + 复现命令）
```
