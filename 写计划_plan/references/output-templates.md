# 输出模板

## Plan 输出模板

```markdown
# handoff_plan.md

## 输入分析
[需求规则理解 + design 接口理解 + 现有代码扫描]

## 决策
[任务拆分策略及理由]

## 产出

### 任务清单

### Task-1: [标题]
- 文件: [具体文件路径列表]
- AC1: [可 assert 的验收标准]
- AC2: [可 assert 的验收标准]
- depends_on: []
- shared_files: []

### Task-2: [标题]
- 文件: [具体文件路径列表]
- AC1: [可 assert 的验收标准]
- depends_on: [Task-1]
- shared_files: [被多个 Task 同时修改的文件路径列表]

...

### 覆盖表
[需求规则 -> design 接口 -> Task -> 覆盖状态]

### 交接项
- 任务执行顺序
- 文件改动清单
- 每任务 AC
- 测试策略
```

**`shared_files` 字段说明**：
- 含义：该 Task 修改的文件中，可能被其他 Task 也修改的文件列表
- 填写规则：planner 在拆分任务时，对比各 Task 的文件列表，将交叉文件标注到 `shared_files`
- 用途：run-plan-parallel 用此字段判断两个 Task 是否存在文件冲突，决定是否可以并行执行
- 无交叉文件时为空列表 `[]`

## Design 评审输出模板

```markdown
## 输入分析
[设计文档可执行性分析]

## 决策
[评审结论依据]

## 产出
REVIEW: DESIGN_OK
（如有问题则输出：REVIEW: DESIGN_ISSUE）

### 评审摘要
[总结评审结果]

### Issues（如有）
1. [ISSUE-1] [具体问题]
   - 位置：[文件/章节]
   - 建议：[具体修改建议]

### 检查明细
[逐项检查结果表格]
```
