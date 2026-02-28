# /design 架构设计升级 — 修订版 v3

> 更新于 2026-02-28，基于当前仓库实况核验（含双目录差异与运行时门控）

## Context

**核心问题**：当前 `/design` 只输出 HLD（高层设计），缺少 DDS（详细设计规范），导致信息传递衰减 70-90%。

**三个关键改进**（来自用户反馈）：
1. 设计过程必须遵循项目规范（代码质量、性能、硬编码治理等）
2. 技术选型必须与用户对齐（三阶段流程，支持交互与降级）
3. 新增技术选型和数据模型设计的方法论支撑

---

## 当前架构现状

### 关键变更（其他窗口优化后）

| 变更 | 说明 |
|------|------|
| 知识 Skills 全部删除 | `_架构方法论`、`_TDD方法论`、`_评审标准`、`_质量标准`、`_验收方法论` 均不存在，方法论已合并进对应 pipeline Skill |
| `/prd` 兼容保留 | `/prd` 为主入口（输出 `master.md` + `units/`），下游继续兼容 `master.md` |
| Agent 结构不变 | 6 个 pipeline agent 保持不变 |
| 双目录关系 | `~/.codex` 与 `~/.claude` 的 pipeline 核心结构一致，但 reference 存在少量平台特化差异 |

### 当前 Agent → Skill → Tools 映射

```
pipeline-designer    → skills: [design]    → Read, Write, Glob, Grep, WebSearch
pipeline-planner     → skills: [plan]      → Read, Write, Glob, Grep
pipeline-implementer → skills: [run-plan]  → Read, Write, Edit, Bash, Glob, Grep
pipeline-checker     → skills: [check]     → Read, Bash, Glob, Grep
pipeline-qa          → skills: [qa]        → Read, Bash, Glob, Grep
pipeline-fixer       → skills: [fix]       → Read, Write, Edit, Bash, Glob, Grep
```

### 当前 Handoff 数据流

```
/prd → master.md + units/
  ↓
/design → handoff_design.md + Key_Decisions.md
  ↓
/plan → review_design_N.md (DESIGN_OK/ISSUE) + handoff_plan.md
  ↓
/run-plan or /run-plan-parallel → review_plan_N.md (PLAN_OK/ISSUE) + handoff_run.md
  ↓
/check → handoff_check.md (五维 PASS/FAIL)
  ↓
/qa → handoff_qa.md (逐条 AC PASS/FAIL)
  ↓ (if FAIL)
/fix → handoff_fix_N.md
```

### 当前各 Agent 输入输出

| Agent | 输入 | 输出 |
|-------|------|------|
| designer | master.md / master.md | handoff_design.md + Key_Decisions.md |
| planner | master.md / master.md + handoff_design.md | review_design_N.md + handoff_plan.md |
| implementer | handoff_plan.md + handoff_design.md | review_plan_N.md + handoff_run.md |
| checker | handoff_plan.md + handoff_run.md | handoff_check.md |
| qa | master.md / master.md + handoff_design.md | handoff_qa.md |
| fixer | handoff_qa.md + handoff_check.md | handoff_fix_N.md |

### 双目录同步要求

`.claude` 和 `.codex` 在 pipeline 主链上保持一致，但不是“完全镜像”。同步需要白名单化，避免覆盖平台特化内容。

**对比结果**：
- Pipeline Skills（design/plan/run-plan/check/qa/fix/auto-dev/run-plan-parallel）：当前内容一致
- Agents（6 个 pipeline Agent）：核心内容一致，唯一稳定差异为 `model: opus`（.claude）vs `model: gpt-5.3-codex`（.codex）
- Reference 文件：大部分一致，但存在平台文案差异（如 `~/.claude/settings.json` vs `~/.codex/settings.json`、措辞差异）

**同步策略**：先在 `.claude` 修改 pipeline 白名单文件，再按白名单同步到 `.codex`，最后做 diff 门禁（允许差异白名单）。

---

## 用户反馈分析与决策

### 反馈 1：设计必须遵循规范

**现状**：pipeline-designer 不感知项目规范（代码质量、硬编码治理、性能效率等）。设计决策可能与规范冲突，实现阶段才暴露问题。

**方案**：
- 在 /design 扫描阶段，增加"适用规范识别"步骤
- pipeline-designer 根据需求类型，按需读取 `~/.claude/reference/` 下的规范文件
- MOD 模板新增"适用规范"章节，标注该模块需遵循的规范及关键约束

**规范适用矩阵**（designer 参考）：

| 设计场景 | 必读规范 |
|---------|---------|
| 涉及 API 设计 | `reference/代码质量.md`（函数设计、错误处理） |
| 涉及数据库 | `reference/数据模型设计.md`（新建） |
| 涉及配置/消息 | `reference/硬编码治理规范.md`、`reference/消息配置规范.md` |
| 涉及性能要求 | `reference/性能效率.md` |
| 涉及前后端 | `reference/全栈开发.md` |
| 新增代码前 | `reference/代码复用.md` |

### 反馈 2：技术选型与用户对齐

**现状**：pipeline-designer 作为 SubAgent（context: fork）运行，无法与用户交互。技术选型由 AI 单方面决定。

**方案**：将 /design 重构为**三阶段流程**——前两阶段在主对话执行（可交互，可降级），第三阶段委托 SubAgent：

```
/design 触发
  ↓ 主对话上下文（优先交互，不依赖特定提问工具）
阶段 1：上下文扫描（自动）
  - 读取需求文档（master.md + units/ 或 master.md）
  - 扫描现有代码
  - 识别适用规范
  ↓
阶段 2：技术选型对齐（交互）
  - 识别需要做选型的技术决策点
  - 每个决策：2-3 方案 + 对比矩阵
  - 可交互时：用户逐个确认选择
  - 不可交互时：按默认策略自动决策并标记 AUTO_DECISION
  - 输出确认后的技术决策清单
  ↓ SubAgent（pipeline-designer，context: fork）
阶段 3：架构设计（HLD + DDS）
  - 输入：需求 + 已确认技术决策 + 适用规范
  - 输出：handoff_design.md + design/MOD-*.md
```

**交互方式**：
- 优先使用主对话提问能力（AskUserQuestion 或等价机制）展示方案对比
- 每轮聚焦 1-2 个决策点
- 用户可选择推荐方案或提出其他方案
- 若当前运行模式无法中途等待用户（如 runtime 自动步进），按默认策略继续并记录 `AUTO_DECISION`
- 所有关键决策都必须带确认状态：`USER_CONFIRMED` 或 `AUTO_DECISION`

**无需选型的情况**：跳过阶段 2，直接进入阶段 3
- 项目技术栈已确定，无新技术引入
- 所有决策点只有唯一合理选择

**默认策略（用于 AUTO_DECISION）**：
1. 优先与现有代码一致性最高的方案
2. 一致性相同时，优先实现复杂度更低的方案
3. 仍无法区分时，优先可逆性更高（迁移成本更低）的方案

### 反馈 3：方法论载体选择

**用户原始建议**：拆分为独立知识 Skills（`_技术选型`、`_数据模型设计`）

**现状变化**：知识 Skills 模式已被废弃（全部合并进 pipeline Skill）

**最终决策**：改为 reference 文件（与现有 `reference/代码质量.md`、`reference/硬编码治理规范.md` 等一致）

| 原方案 | 调整后 | 理由 |
|--------|--------|------|
| `skills/_技术选型_tech-selection/SKILL.md` | `reference/技术选型.md` | 知识 Skills 模式已废弃，统一用 reference |
| `skills/_数据模型设计_data-model-design/SKILL.md` | `reference/数据模型设计.md` | 同上 |
| 修改 `skills/_架构方法论_arch-methodology/SKILL.md` | 直接修改 `skills/架构设计_design/SKILL.md` | 该文件不存在，方法论已合并 |

**不新增的方法论（以及理由）**：
- 接口设计：`架构设计_design/SKILL.md` §6.4 已有"接口定义完整性标准"
- 错误处理设计：`reference/代码质量.md` 已覆盖
- 安全设计：过于领域化，按需通过 reference/ 读取

---

## 新增 Reference 1：`reference/技术选型.md`

内容要点（~130 行）：

### 1. 触发条件

以下设计决策需要技术选型流程：
- 引入新技术栈/框架/库
- 存在 2+ 可行方案的架构模式选择
- 技术债务偿还方案选择
- 基础设施/部署方案选择

以下不需要（直接决定）：
- 项目已有统一方案（如已用 FastAPI 则不重新选型）
- 只有唯一合理选择
- 纯实现细节（函数命名、变量类型）

### 2. 选型流程

**步骤 1：识别决策点**
- 从需求和扫描结果中提取需要选型的技术点
- 每个决策点标注：影响范围（全局/模块级）、可逆性（高/低）

**步骤 2：方案调研**
- 每个决策至少 2 个方案（高影响决策 3 个）
- 优先 WebSearch 调研最佳实践和社区共识
- 来源优先级：官方文档 > 技术博客 > 社区讨论

**步骤 3：对比矩阵**

| 维度 | 方案 A | 方案 B | 方案 C |
|------|--------|--------|--------|
| 与现有代码一致性 | ... | ... | ... |
| 实现复杂度 | ... | ... | ... |
| 社区生态/维护状态 | ... | ... | ... |
| 性能影响 | ... | ... | ... |
| 学习成本 | ... | ... | ... |
| 锁定风险 | ... | ... | ... |

**推荐**：方案 X，理由：...

**步骤 4：用户对齐**
- 展示对比矩阵 + 推荐方案
- 可交互时等待用户确认；不可交互时执行默认策略并标记 `AUTO_DECISION`
- 记录最终选择、理由、确认状态（`USER_CONFIRMED` / `AUTO_DECISION`）

### 3. 决策记录格式

合并到 handoff_design.md 的"技术选型"章节（含方案对比和决策理由）。

### 4. 反模式

- 只提供一个方案让用户"确认"（实质上是绕过对齐）
- 未调研就凭经验推荐
- 忽略"与现有代码一致性"维度
- 把用户确认当走过场

---

## 新增 Reference 2：`reference/数据模型设计.md`

内容要点（~150 行）：

### 1. 命名规范
- 表名：snake_case，复数形式（users, orders）
- 字段名：snake_case（user_name, created_at）
- 索引名：idx_{table}_{field}（idx_users_email）
- 外键名：fk_{table}_{ref_table}（fk_orders_users）
- 约束名：uq_{table}_{field}（唯一约束）、ck_{table}_{field}（检查约束）

### 2. 表结构标准

**基础字段（每张表必含）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInt/UUID | 主键，策略需在选型阶段确认 |
| created_at | DateTime | 创建时间，默认 now() |
| updated_at | DateTime | 更新时间，默认 now()，on update |

**软删除（如需要）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| deleted_at | DateTime? | NULL=未删除，非NULL=删除时间 |
| is_deleted | Boolean | 冗余字段，加速查询 |

**字段设计原则**：
- 字段类型选择最小够用原则（tinyint vs int vs bigint）
- 字符串字段必须指定最大长度
- 金额字段用 Decimal，禁止 Float
- 时间字段统一 UTC 存储

### 3. 索引设计

**必建索引**：外键字段、频繁 WHERE 条件字段、ORDER BY 字段（高频查询）、唯一约束字段

**索引原则**：
- 遵循最左前缀原则
- 单表索引数 ≤ 5（特殊情况说明理由）
- 避免在低基数字段上建索引（如 gender）
- 覆盖索引优先（减少回表）

**反模式**：所有字段都建索引、索引顺序不考虑查询模式、冗余索引（A,B 和 A 同时存在）

### 4. 关系建模

**一对多**：外键在"多"的一方、必须建索引、考虑级联策略（CASCADE/SET NULL/RESTRICT）

**多对多**：通过关联表实现、关联表命名 `{table_a}_{table_b}`（字母序）、联合主键或独立主键 + 联合唯一约束

**自关联**：明确最大层级深度、考虑是否需要物化路径（大量层级遍历时）

### 5. 迁移规范
- 每次迁移必须可回滚（提供 upgrade + downgrade）
- 大表 DDL 变更标注"需人工确认"（可能锁表）
- 数据迁移与结构迁移分开（不在同一个 migration 文件）

### 6. 检查清单
- 表名、字段名符合命名规范
- 基础字段（id, created_at, updated_at）存在
- 外键字段有索引
- 无冗余索引
- 金额用 Decimal
- 字符串有最大长度
- 关系类型和级联策略明确
- 迁移可回滚

---

## 核心方案：UNIT → MOD 映射

产品需求（UNIT）定义 WHAT，架构设计（MOD）定义 HOW。

```
UNIT-001（需求：用户认证规则）  →  MOD-001（设计：认证模块实现方案）
```

### 输出结构

```
docs/pipeline/{feature}/
├── master.md                       ← 需求文档（/prd 输出）
├── handoff_design.md               ← HLD（全局架构 + 模块索引 + 技术决策 + 跨模块约束）
└── design/                         ← DDS（模块蓝图，复杂需求时）
    ├── MOD-001_{name}.md
    └── MOD-002_{name}.md
```

**Key_Decisions.md 已移除**：技术决策合并到 handoff_design.md 的"技术选型"章节（含方案对比和决策理由）。阶段 2 交互已完成对齐，无需额外文件。

简单需求（≤2 模块且接口 ≤3 个）：DDS 内联在 handoff_design.md，不创建 design/ 目录。

---

## HLD：handoff_design.md 模板

```markdown
# handoff_design.md

## Goals / Non-Goals
### Goals
- [G1: ...]
### Non-Goals
- [NG1: ...]

## 输入分析
[扫描现有代码的发现 + 需求规则逐条理解 + 适用规范识别]

## 架构视图
[C4 Level 1-2]

## 技术选型（含决策记录）
### {决策点 1}
- **方案对比**:
  | 维度 | 方案 A | 方案 B |
  |------|--------|--------|
  | ... | ... | ... |
- **决策**: 方案 X
- **理由**: [为什么选择此方案]
- **影响**: [对系统的影响]

## 模块索引
| MOD | 模块名 | 对应需求 | 文件 | 依赖 |
|-----|--------|---------|------|------|
| MOD-001 | {名称} | UNIT-001 | design/MOD-001_{name}.md | 无 |

## 信息流
[Mermaid sequence/flowchart]

## 跨模块约束
- 安全策略：...
- 错误处理策略：...
- 可观测性：...
- 性能目标：...

## 适用规范索引
| 规范 | 适用模块 | 关键约束摘要 |
|------|---------|-------------|
| 代码质量.md | 全部 | 函数 ≤40行，参数 ≤5个 |
| 数据模型设计.md | MOD-001 | 表命名 snake_case，基础字段必含 |

## 决策摘要
| # | 决策点 | 选择 | 理由（一句话） |
|---|--------|------|---------------|
| D1 | {决策点} | {方案} | {理由} |

## 覆盖表
[需求规则 → 模块 → 覆盖状态]

## 交接项
```

---

## DDS：MOD-N.md 模板

```markdown
# MOD-001: {模块名}

**对应需求**: UNIT-001 ({需求名})
**在流程中的位置**: [上游模块] → [本模块] → [下游模块]

---

## 1. 模块职责
**负责**: [1-2 句话核心职责]
**不负责**: [明确排除的职责]

## 2. 现有代码集成点
**复用**:
- `{file_path}` 的 `{function/class}` — [用途]
**参考模式**:
- `{file_path}` — [遵循此文件的组织模式]
**新建文件**:
- `{file_path}` — [用途]

## 3. 适用规范
| 规范 | 关键约束 |
|------|---------|
| {规范名} | {该模块必须遵循的具体条目} |

## 4. 接口设计
### 4.1 {METHOD} {path}
**入参**: [字段/类型/必填/校验规则/说明]
**成功响应**: [JSON 示例]
**错误响应**: [状态码/error_code/触发条件/用户消息]

## 5. 数据模型
### 5.1 {ModelName}
[遵循 reference/数据模型设计.md 的规范]
| 字段 | 类型 | 约束 | 说明 |
**索引**: [名称 + 用途]
**关系**: [类型 + 外键]

## 6. 运行时视图
### 6.1 主流程序列图
### 6.2 分支/异常活动图
### 6.3 状态机（如有状态实体）

## 7. 错误处理
| 场景 | 触发条件 | 处理方式 | 是否重试 | 用户影响 |

## 8. 实施约束（铁律）
1. [具体、可检查的约束]

## 9. 模块依赖
- **依赖**: MOD-{N} 的 `{具体接口/服务}`
- **被依赖**: MOD-{N} 使用本模块的 `{具体接口/服务}`
```

---

## /design SKILL.md 流程重构（三阶段）

### 角色
```
> 角色：资深架构师
> 核心方法：先扫描再设计 + 技术选型对齐 + UNIT→MOD 映射 + 运行时视图驱动
> 目标：输出 HLD + DDS，精度达到"两个独立开发者阅读 MOD 能直接编码且实现一致"
```

### 阶段 1：上下文扫描（主对话，自动）

1. 读取需求文档（master.md + units/ 或 master.md）
2. Glob/Grep 扫描现有代码结构、命名模式、框架版本
3. 识别适用规范（参考规范适用矩阵），按需读取 `reference/` 下的规范文件
4. 产出：内部整理扫描摘要（不输出文件）

### 阶段 2：技术选型对齐（主对话，交互优先）

1. 从需求和扫描结果中提取技术决策点
2. 对每个决策点，参考 `reference/技术选型.md` 方法论：
   - 调研 2-3 方案
   - 构建对比矩阵
   - 给出推荐 + 理由
3. 使用主对话交互能力逐个与用户对齐（AskUserQuestion 或等价方式）
4. 若运行环境不支持中途等待用户，按默认策略自动决策并标记 `AUTO_DECISION`
5. 记录确认结果（含确认状态）

**无需选型的情况**：跳过此阶段，直接进入阶段 3

### 运行时门控兼容（新增）

- 会话直调 `/design`：可在阶段 2 多轮交互确认
- `pipeline.sh run-step design`：当前运行时不会在 design 阶段进入 `WAITING_USER`，因此阶段 2 必须支持自动降级
- 自动降级时，`handoff_design.md` 的“技术选型”章节必须输出：
  - 推荐方案
  - 自动决策依据
  - `decision_status: AUTO_DECISION`
  - `follow_up: plan 前需人工确认（yes/no）`

### 阶段 3：架构设计（SubAgent，自动）

启动 pipeline-designer SubAgent，输入：
- 需求文档路径
- 已确认的技术决策清单
- 适用规范清单 + 关键约束
- 扫描摘要

SubAgent 执行：
1. 全局架构设计 → handoff_design.md（HLD，含技术决策记录）
2. 模块蓝图设计 → design/MOD-N.md（DDS）

**分模式**：

| 模式 | 条件 | 执行方式 |
|------|------|---------|
| 简单 | ≤2 模块且接口 ≤3 个 | DDS 内联在 handoff_design.md |
| 复杂 | >2 模块或接口 >3 个 | 创建 design/ 目录，各 MOD 独立文件 |

### 质量门控

| 检查项 | 全部 | 复杂需求 |
|--------|------|---------|
| 每个 UNIT 有对应 MOD | ✓ | ✓ |
| 每个接口有完整入参+出参+错误码 | ✓ | ✓ |
| 主流程有序列图 | ✓ | ✓ |
| 分支/异常有活动图或伪代码 | | ✓ |
| 每个 MOD 有"适用规范"章节 | ✓ | ✓ |
| 每个 MOD 有"现有代码集成点" | ✓ | ✓ |
| 实施约束可翻译为 assert | ✓ | ✓ |
| 技术选型已完成确认或自动决策标记 | ✓ | ✓ |
| 数据模型遵循设计规范 | ✓ | ✓ |
| 覆盖表 100% | ✓ | ✓ |
| Non-Goals 存在且有效 | ✓ | ✓ |

---

## 主对话输出规范

/design 完成时，主对话**只输出摘要**（细节在文档中）：

```markdown
## /design 完成

**功能**: {feature_name}
**模块数量**: N

**技术选型**:
- {决策点1}: {选择}
- {决策点2}: {选择}

**输出文件**:
- `handoff_design.md` — HLD
- `design/MOD-001_{name}.md` — {一句话描述}
- `design/MOD-002_{name}.md` — {一句话描述}

**下一步**: `/plan`
```

**禁止**：在主对话中展示模板内容、接口详情、数据模型、序列图等细节。

---

## Pipeline 下游适配

### 信息传递

| 环节 | 读什么 | 用来做什么 |
|------|--------|----------|
| /plan | handoff_design.md + 各 MOD | Task 按 MOD 组织，AC 覆盖实施约束 |
| /run-plan | handoff_plan.md + 对应 MOD | Task 标注 design_ref: MOD-N |
| /check | handoff_plan.md + handoff_run.md + 对应 MOD | 保持五维 + 新增“设计约束合规”专项核查 |
| /qa | 需求文档 + 各 MOD 的实施约束 | 双层验收：需求规则 + 实施约束 |

### 兼容策略

```
if design/MOD-*.md 存在 → 新格式（读 MOD）
else → 旧格式（只读 handoff_design.md）

if Key_Decisions.md 存在 → 视为历史兼容输入（可选读取）
else → 以 handoff_design.md 的“技术选型/决策摘要”为唯一决策来源
```

---

## 修改文件清单（13 个 + Codex 同步）

### Phase 1：新增 reference 文件（2 个新文件，可并行）

| # | 文件 | 操作 | 说明 |
|---|------|------|------|
| 1a | `~/.claude/reference/技术选型.md` | 新建 | 技术选型方法论 + 对比矩阵标准 + 决策记录格式 |
| 1b | `~/.claude/reference/数据模型设计.md` | 新建 | 表设计规范 + 索引策略 + 关系建模 + 命名规范 |

### Phase 2：核心设计重构（2 文件，可并行）

| # | 文件 | 操作 | 说明 |
|---|------|------|------|
| 2a | `agents/pipeline-designer.md` | 修改 | 新增 MOD 输出 + 移除 Key_Decisions.md + 新增 design/ 目录输出 |
| 2b | `skills/架构设计_design/SKILL.md` | 修改 | 三阶段流程 + DDS 方法论 + 规范感知 + reference 引用 + HLD/DDS 模板 + 质量门控 + 移除 Key_Decisions 相关（§5 §6.7） |

### Phase 3：下游 pipeline 适配（9 文件，可全并行）

| # | 文件 | 操作 | 说明 |
|---|------|------|------|
| 3a | `agents/pipeline-planner.md` | 修改 | 输入新增 design/MOD-*.md + 输出 Task 含 design_ref |
| 3b | `agents/pipeline-implementer.md` | 修改 | 输入新增对应 MOD + 开发时参考 MOD 实施约束 |
| 3c | `agents/pipeline-qa.md` | 修改 | 输入新增 MOD 实施约束 → 双层验收 |
| 3d | `agents/pipeline-checker.md` | 修改 | 输入新增 MOD → 保持五维并增加“设计约束合规”专项核查 |
| 3e | `skills/写计划_plan/SKILL.md` | 修改 | Task 组织按 MOD + AC 覆盖实施约束 + 输入说明更新 |
| 3f | `skills/执行计划_run-plan/SKILL.md` | 修改 | 强制读 MOD + 规范自检 + 输入说明更新 |
| 3g | `skills/测试验收_qa/SKILL.md` | 修改 | 双层验收标准来源 + 输入说明更新 |
| 3h | `skills/开发检查_check/SKILL.md` | 修改 | 保持五维框架，新增“设计约束合规”专项核查条目 |
| 3i | `skills/自动开发_auto-dev/SKILL.md` | 修改 | 移除对 Key_Decisions.md 的强依赖，改读 handoff_design 决策摘要 |

### Phase 4：同步到 .codex

```bash
# Skills 直接复制
for skill in 架构设计_design 写计划_plan 执行计划_run-plan 测试验收_qa 开发检查_check 自动开发_auto-dev; do
  cp ~/.claude/skills/$skill/SKILL.md ~/.codex/skills/$skill/SKILL.md
done

# Agents 复制后替换 model 字段
for agent in pipeline-designer pipeline-planner pipeline-implementer pipeline-checker pipeline-qa; do
  sed 's/model: opus/model: gpt-5.3-codex/' ~/.claude/agents/$agent.md > ~/.codex/agents/$agent.md
done

# Reference 文件复制
cp ~/.claude/reference/技术选型.md ~/.codex/reference/技术选型.md
cp ~/.claude/reference/数据模型设计.md ~/.codex/reference/数据模型设计.md

# 白名单 diff 验证（允许 model 字段差异；保留 reference 平台特化差异）
diff -ru ~/.claude/agents ~/.codex/agents | rg -v '^[-+]model:'
```

### 不修改

| 文件 | 理由 |
|------|------|
| pipeline-fixer.md | 读 qa + check，不直接读 design |
| 并行开发_run-plan-parallel | MOD 信息通过 plan 的 Task 继承 |
| reference/性能效率.md、reference/测试Hooks配置.md 等 | 保持目录平台特化差异，不做互相覆盖 |

---

## 实施步骤

### Phase 1：新增 reference 文件（可并行，独立）
- 1a: 创建 `reference/技术选型.md`
- 1b: 创建 `reference/数据模型设计.md`

### Phase 2：核心设计重构（可与 Phase 1 并行）
- 2a: 修改 `agents/pipeline-designer.md`
- 2b: 修改 `skills/架构设计_design/SKILL.md`（最大变更）

### Phase 3：下游适配（依赖 Phase 2 的 MOD 格式定义，9 文件全并行）
- 3a-3i: 各 pipeline agent 和 skill 适配

### Phase 4：同步到 .codex
- 执行同步脚本

### Phase 5：验证
- 引用一致性：Grep pipeline 生效文件中的 `Key_Decisions` 引用，确认已无强依赖（历史兼容说明除外）
- MOD 引用一致性：确认所有引用 `design/MOD-*.md` 的文件使用相同的兼容检测逻辑
- 输入输出链路：design → plan → run-plan → check → qa 数据传递完整
- 运行时兼容：`pipeline.sh run-step design` 在无交互等待能力时可完成并正确写入 `AUTO_DECISION`
- 双目录同步：diff 确认“白名单文件一致 + 允许差异白名单生效”
- 功能测试：对一个简单需求执行 `/design`，确认三阶段流程（含降级路径）正确

---

## 风险控制

| 风险 | 等级 | 缓解 |
|------|------|------|
| 技术选型交互轮次过多 | 中 | 无需选型时跳过；按决策影响度排序，低影响可合并 |
| 运行时自动降级导致偏离用户偏好 | 中 | 仅对无法等待场景启用 AUTO_DECISION；在 handoff_design 显式标记并在 plan 前人工确认 |
| designer 输出 MOD 时间过长 | 中 | 简单需求内联；复杂需求子代理并行写各 MOD |
| MOD 模板过于死板 | 中 | 所有章节按需裁剪（如无状态实体则跳过状态机） |
| .codex 同步遗漏或误覆盖平台特化内容 | 低 | Phase 4 白名单同步 + 允许差异白名单校验 |
| 兼容旧格式 | 低 | 检测逻辑简单（design/ 目录是否存在） |
