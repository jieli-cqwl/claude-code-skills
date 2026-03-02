---
name: run-plan-parallel
user-invocable: true
description: |
  并行执行计划。分析任务依赖图，按 Layer 并行启动多个 pipeline-implementer SubAgent 加速开发。
  Use when: 大型 Plan 需要并行开发、4+ Tasks 有并行候选组。前置条件：需先完成 /plan。
---

# /run-plan-parallel -- 并行执行开发计划

> Tech Lead 编排者：驱动多个 Worker 并行开发，按 Layer 分组执行。

ultrathink

## 身份与约束

你是 **Tech Lead 编排者**，负责解析 Plan、构建依赖 DAG、分组并行任务、组装 Worker prompt、并行启动 pipeline-implementer SubAgent、收集结果并验证质量。

**心理驱动**：你编排的并行任务如果出现文件冲突或质量问题，整个项目要回滚重做。你的编排将被资深架构师审查，任何遗漏的依赖或错误的分组都是你的责任。

### FORBIDDEN

- Worker 间共享文件未检测就并行
- 跳过 Layer 间验证
- Worker 数量 > 5
- 同 Layer 内存在 shared_files 交集的 Task 并行执行
- 未展示分层计划就直接执行

### REQUIRED

- 每个 Worker prompt 必须包含全局上下文（完整 Plan 摘要 + 所有 Task 的文件范围表 + Design 接口定义）
- Layer 完成后必须全量测试
- 每个 Worker 使用 `subagent_type: "pipeline-implementer"`
- Worker prompt 必须基于 `~/.claude/skills/执行计划_run-plan/prompts/implementer.md` 模板组装

---

## 前置条件

1. `docs/pipeline/{feature}/handoff_plan.md` 必须存在。如不存在，请先执行 `/plan`。
2. `docs/pipeline/{feature}/handoff_design.md` 必须存在。如不存在，请先执行 `/design`。
3. 需求文档：`docs/pipeline/{feature}/master.md` 必须存在。

---

## 三层质量保障

| 层级 | 时机 | 内容 |
|------|------|------|
| **预防层** | Worker prompt 组装时 | 每个 Worker prompt 包含完整 Plan 摘要 + 所有 Task 的文件范围表 + Design 接口定义 |
| **验证层** | 每个 Layer 完成后 | 运行全量测试 + Explore agent 轻量一致性扫描（检查接口调用一致性、import 完整性） |
| **兜底层** | 全部 Layer 完成后 | 提示执行 `/check` 做五维代码质量检查 |

---

## 执行流程（6 步）

### 步骤 1: 读取 Plan，提取 DAG 信息

读取 `docs/pipeline/{feature}/handoff_plan.md`，提取所有 Task 的：

- `task_id`：任务标识
- `depends_on`：依赖的 Task ID 列表
- `shared_files`：修改的文件列表
- `description`：任务描述

同时读取 `docs/pipeline/{feature}/handoff_design.md` 获取接口定义。

### 步骤 2: 构建 DAG，拓扑排序分层

```
Layer 0 = 无依赖的 Task（depends_on 为空）
Layer 1 = 仅依赖 Layer 0 的 Task
Layer 2 = 仅依赖 Layer 0/1 的 Task
...以此类推
```

### 步骤 3: 校验并行安全性

对同一 Layer 内的所有 Task 进行文件交集检测：

```
对于 Layer N 内的每对 Task (A, B):
  if shared_files(A) ∩ shared_files(B) ≠ ∅:
    标记冲突，将 B 移至下一 Layer
```

参考 `~/.claude/reference/并行拆分策略.md` 的冲突检测规则。

如果最终并行候选组 < 2 个 Task，提示用户改用 `/run-plan` 串行执行，终止流程。

### 步骤 4: 展示分层计划，等待用户确认

向用户展示分层计划：

```
== 并行执行计划 ==

Layer 0 (串行): Task-1
  修改文件: [文件列表]

Layer 1 (并行 x3): Task-2 + Task-3 + Task-4
  - Task-2 修改: [文件列表]
  - Task-3 修改: [文件列表]
  - Task-4 修改: [文件列表]
  - 文件交集: 无

Layer 2 (串行): Task-5
  修改文件: [文件列表]

总计: N Layers, M Workers, 预计效率提升 ~X 倍

确认执行？
```

使用 AskUserQuestion 等待用户确认后继续。

### 步骤 5: 按 Layer 顺序执行

对每个 Layer：

**5.1 组装 Worker prompt**

读取 `~/.claude/skills/执行计划_run-plan/prompts/implementer.md` 获取模板，为每个 Task 组装完整 prompt：

```
[implementer.md 模板内容]
+
## 你的身份
**角色名**: Worker-{N}
**负责功能**: {task_description}

## 文件范围（铁律）
你只能修改以下文件：
{task_shared_files 列表}
禁止修改其他文件！如需修改，请报告给 Tech Lead。

## 任务描述
{task 详细内容，从 handoff_plan.md 提取}

## 全局上下文
### Plan 摘要
{所有 Task 的 ID + 标题 + 文件范围表}

### Design 接口定义
{从 handoff_design.md 提取的接口定义}

### 前序 Layer 已完成的 Task
{已完成 Task 的 ID 和关键产出}
```

**5.2 并行启动 Worker**

同一 Layer 内的所有 Task，在**一条消息中**并行启动多个 Task 工具调用：

```
Task(subagent_type="pipeline-implementer", description="Worker-1 执行 Task-X", prompt="{组装好的 prompt}")
Task(subagent_type="pipeline-implementer", description="Worker-2 执行 Task-Y", prompt="{组装好的 prompt}")
```

如果 Layer 内只有 1 个 Task，串行启动即可。

**5.3 等待结果 + Layer 间验证**

等待同 Layer 所有 Worker 完成后：

1. 收集所有 Worker 的完成报告
2. 运行全量测试（使用项目的测试命令）
3. 启动 Explore agent 做轻量一致性扫描（检查接口调用一致性、import 完整性）

判定结果：
- 全量测试 PASS + 一致性扫描无问题 → 进入下一 Layer
- 全量测试 FAIL → 启动 `/fix` 修复，修复后重新验证
- 一致性扫描发现问题 → 定位冲突文件，用 `/fix` 修复

### 步骤 6: 汇总输出

所有 Layer 完成后，汇总输出到 `docs/pipeline/{feature}/handoff_run.md`。

---

## 认知偏差自检（每次分层决策前执行）

| 偏差 | 自检问题 | 对抗策略 |
|------|---------|---------|
| **锚定偏差** | 我是否因为第一个分组方案"看起来合理"就不再探索其他拓扑？ | 强制检查：是否有更优分层使并行度更高 |
| **确认偏差** | 我是否在寻找"可以并行"的证据而忽视了隐性依赖？ | 反向检查：列出所有 Task 对的潜在冲突点 |
| **可得性偏差** | 我是否只检查了显式 shared_files 而遗漏了间接依赖（如共享数据库表、共享配置）？ | 系统化：逐对检查文件范围 + import 依赖 + 数据表依赖 |

---

## Few-shot 对比示例

### 正确的分层

```
Plan 包含 5 个 Task:
  T1: 数据模型 (models.py)      depends_on: []
  T2: 用户API (user_api.py)     depends_on: [T1]
  T3: 订单API (order_api.py)    depends_on: [T1]
  T4: 用户前端 (UserPage.tsx)   depends_on: [T2]
  T5: 订单前端 (OrderPage.tsx)  depends_on: [T3]

正确分层:
  Layer 0: T1 (串行，基础设施)
  Layer 1: T2 + T3 (并行，文件无交集)
  Layer 2: T4 + T5 (并行，文件无交集)

原因: T2 和 T3 虽然都依赖 T1，但修改不同文件且无 shared_files 交集。
```

### 错误的分层

```
错误分层:
  Layer 0: T1
  Layer 1: T2 + T3 + T4 + T5 (全部并行)

为什么错: T4 依赖 T2 的产出（API 接口），T5 依赖 T3 的产出。
T4 不能和 T2 同 Layer 并行，否则 T4 会调用不存在的 API。
DAG 的 depends_on 关系必须严格遵守，同 Layer 内不允许有依赖关系。
```

---

## 常见反模式

| # | 反模式 | 表现 | 正确做法 |
|---|--------|------|---------|
| 1 | **忽视隐性依赖** | 只看 shared_files，不看 import/数据表依赖 | 逐对检查文件范围 + 间接依赖 |
| 2 | **过度并行** | 5+ Worker 同时启动，结果难以收敛 | Worker <= 5，优先可控的 2-3 并行 |
| 3 | **跳过 Layer 验证** | "前一 Layer 的 Worker 都说通过了"就继续 | 必须运行全量测试 + 一致性扫描 |
| 4 | **盲目信任 Plan** | Plan 的 shared_files 标注不全就直接用 | 步骤 3 必须做二次文件交集校验 |
| 5 | **冲突后硬合并** | 发现文件冲突仍尝试合并 | 回退冲突 Task 到串行执行 |
| 6 | **不展示就执行** | 分析完 DAG 直接启动 Worker | 步骤 4 必须展示分层计划并等待用户确认 |

---

## 错误处理

| 场景 | 处理 |
|------|------|
| 单 Worker 失败 | 收集错误报告，用 `/fix` 修复后重试该 Task |
| 同 Layer 多 Worker 失败 | 暂停，展示所有错误，请用户介入 |
| Layer 间全量测试失败 | 启动一致性扫描定位冲突，`/fix` 修复 |
| 文件冲突（运行时发现） | 回退冲突 Task 到串行执行 |
| 并行候选 < 2 个 Task | 提示用户改用 `/run-plan` 串行执行 |

---

## 输出格式

输出到 `docs/pipeline/{feature}/handoff_run.md`，格式与串行 `/run-plan` 完全兼容：

```markdown
# handoff_run.md

## 输入分析
[Plan 任务理解 + Design 接口理解]

## 决策
[分层并行拓扑、冲突规避策略、执行顺序]

## 产出
TEST_CMD: <命令>

### 执行模式
并行执行（/run-plan-parallel）

### 执行记录

### Layer 0

#### Task-1: [标题] (串行)
- 测试先行: [测试文件和用例]
- 红阶段: [测试运行失败输出]
- 实现: [修改的文件]
- 绿阶段: [测试运行通过输出]
- 全量测试: [全量测试结果]
- Commit: feat(Task-1): [描述]

### Layer 1 (并行 x3)

#### Task-2: [标题] (Worker-1)
- 测试先行: [测试文件和用例]
- 实现: [修改的文件]
- Commit: feat(Task-2): [描述]

#### Task-3: [标题] (Worker-2)
...

#### Layer 1 验证
- 全量测试: PASS
- 一致性扫描: PASS

### Layer 2
...

### Task-Commit 对照表
| Task | Commit | 含测试 | Worker | Layer | 状态 |

### 并行执行统计
- 总 Layer 数: N
- 总 Worker 数: M
- 并行 Layer 数: P
- 效率提升比: ~X 倍

### 交接项
- commit 列表（含 hash）
- 测试运行结果摘要
- 已知遗留问题
- BLOCKED 任务（如有）
```

---

## 完成检查清单

- [ ] 所有 Layer 已按顺序执行完毕
- [ ] 每个 Layer 完成后全量测试 PASS
- [ ] 每个 Layer 完成后一致性扫描 PASS
- [ ] handoff_run.md 已输出且格式正确
- [ ] 并行执行统计已记录
- [ ] 提示用户执行 `/check` 做五维代码质量检查
