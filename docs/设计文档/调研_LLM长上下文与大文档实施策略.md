# 调研：LLM 长上下文与大文档实施策略

**调研日期**：2026-02-21
**调研目的**：解决 3000 行设计文档的可靠实施问题，建立大型文档 + LLM 协作的通用方法论

---

## 一、LLM 长上下文的质量瓶颈

### 1.1 "Lost in the Middle" 现象

**核心发现**（Liu et al., 2024, Stanford/Anthropic）：

LLM 的性能呈现 **U 型曲线**——当关键信息位于输入的开头或结尾时表现最好，位于中间时显著下降。具体数据：

- 关键信息从首尾移至中部时，**性能下降可达 30% 以上**
- GPT-3.5-Turbo 中部性能甚至低于无文档的闭卷测试（56.1%）
- 即使是专门的长上下文模型也无法完全消除此偏差
- 额外微调仅能将最差情况改善约 10 个百分点，偏差仍然显著

**影响范围**：该问题在多文档问答和键值检索任务中均得到验证。

### 1.2 Context Rot（上下文腐烂）

**核心发现**（Chroma Research, 2025，测试 18 个 SOTA 模型）：

- 即使在最简条件下，**模型性能也随输入长度增加而退化**，且退化方式是非均匀的
- 从 10k 到 100k+ tokens，NIAH 任务准确率下降 **20-50%**
- **干扰内容类型很重要**：不同类型的无关内容对性能的影响不同（如逻辑操作比打印语句更有害）
- **Claude 模型的优势**：Claude 在所有测试模型中"衰减最慢"，且幻觉率最低
- Claude Sonnet 4 和 Opus 4 在不确定时倾向于明确表示无法找到答案，而不是编造

**关键洞察**：实际应用场景通常比测试更复杂，输入长度的影响可能更显著。

### 1.3 Claude 的实际上下文可靠范围

| 模型 | 标称窗口 | 可靠范围 | 备注 |
|------|---------|---------|------|
| Claude Sonnet 4 | 200K | 全窗口（<5% 精度退化） | 标准可靠选择 |
| Claude Opus 4.6 | 200K（1M beta） | 长上下文检索基准 76%（前代仅 18.5%） | 质变级改进 |
| Claude Code 有效空间 | 200K | ~167K（33K 留给 compaction buffer） | 工程实际值 |

**结论**：Claude 在 200K 范围内的可靠性在主流 LLM 中属于领先水平，但"可靠"不等于"完美"——随上下文增长，质量仍会下降。3000 行设计文档（约 15,000-20,000 tokens 中文）本身在安全范围内，但加上代码上下文、对话历史等，实际占用远超文档本身。

### 1.4 已知的缓解策略

1. **关键信息置于首尾**：利用 U 型注意力曲线
2. **二阶段检索**：粗召回 + 精排（cross-encoder reranking）
3. **控制上下文大小**：只保留最相关的 3-5 个文档
4. **注意力校准（Ms-PoE）**：通过注意力权重修正减少位置偏差
5. **IN2 训练**：通过指令微调增强中部信息利用
6. **上下文工程**：精心策划输入内容，而非简单堆积

---

## 二、大型设计文档的分治策略

### 2.1 分治的学术基础

**理论框架**（University of Chicago / Google DeepMind / Stanford, 2025）：

将长上下文任务的失败模式分为三类：
1. **跨块依赖（Task Noise）**：分块后丢失跨块信息
2. **模型困惑（Model Noise）**：上下文越大，模型越困惑
3. **聚合不完美（Aggregator Noise）**：合并子结果时的信息损失

**结论**：当跨块依赖可控时，分治策略显著优于单次长上下文处理。

### 2.2 分治提示（D&C Prompting）

**三组件架构**：
1. **Problem Decomposer**（问题分解器）：将复杂问题拆为子问题
2. **Sub-Problem Solver**（子问题求解器）：用 LLM 逐个解决
3. **Solution Composer**（解决方案组合器）：合并子解得到总解

**效果**：通过解耦分解、求解、组装三个过程，避免交叉干扰，减少中间错误。

### 2.3 层次化规划（GLIDER, ICML 2025）

- 高层策略制定抽象的分步计划
- 低层控制器根据计划执行具体推理子任务
- 适用于长周期、复杂任务

### 2.4 复合错误率问题

**关键数学洞察**：
- 单步 99% 准确率 → 100 步流程的成功率约 36%
- 单步 99% 准确率 → 1000 步流程的成功率约 0%

**应对策略**：
- 每步尽可能原子化（一个动作、一个决策）
- 每步只给必要的上下文信息
- 步骤间有验证检查点

### 2.5 Spec-Driven Development（规格驱动开发）

**核心原则**（Addy Osmani, 2026; XB Software, 2025）：

> "分解不是可选的。AI 的上下文窗口虽大但有限。一次性处理复杂的多页应用会导致遗忘需求和不一致的结果。"

**推荐流程**：
1. 先写清晰、结构化、可测试的规格文档
2. 按功能逐个构建，而非一次性全部
3. 每个功能块只加载相关的规格段落 + 全局约束
4. 完成后再处理下一个，每个主要任务之间刷新上下文

---

## 三、Claude Code 特有的大文档处理机制

### 3.1 Compact/Summarization 机制

**工作原理**：
- 上下文使用到约 **167K tokens**（200K 窗口的 83.5%）时触发自动压缩
- 33K tokens 留作压缩缓冲区（2026 年从 45K 减至 33K）
- `/compact` 手动触发：将对话历史摘要化，作为新上下文的前置信息
- `/clear` 则完全清除，重新开始

**信息损失**：压缩过程中，具体变量名、精确错误信息、早期决策细节都会被压缩为概要，丢失精度。

**优化建议**：
- 在 CLAUDE.md 中定制压缩行为："When compacting, always preserve the full list of modified files and any test commands"
- 在完成主要功能后主动压缩，而非等待自动触发
- 在 50% 上下文使用时主动备份关键状态

### 3.2 Sub-Agent 上下文隔离

**核心价值**：每个 sub-agent 拥有独立的上下文窗口，执行完毕后只返回摘要给主对话。

**适合委派的任务类型**：
- 产生大量输出的操作（测试运行、日志处理、文档获取）
- 切面型任务（验证、审查等）
- 大量数据加载的研究任务（Web 搜索、文档抓取）

**内建 Sub-Agent**：
- **Explore Agent**：只读型，用于搜索和分析代码库
- **Plan Agent**：研究模式下收集上下文，制定计划
- **Summarization Agent**：用于上下文摘要和生成新主题

**关键机制**：Plan Agent 不继承主 Agent 的完整上下文，只包含 Explore sub-agent 发现的摘要。这种"新鲜起点"设计避免了上下文污染。

**局限性**：
- 摘要返回是有损压缩——Opus 直接阅读所有相关上下文可能了解更多细节
- Sub-agent 的思考过程和代理循环对用户不透明
- Sub-agent 之间无法直接通信（需要主 Agent 中转）

### 3.3 Agent Teams（2026.02 新特性）

**与 Sub-Agent 的区别**：
- Sub-agent 在单会话内运行，只能向主 Agent 报告
- Agent Teams 的成员可以**直接互相通信**、共享发现、自主协调

**架构**：
- 一个 Team Lead 负责编排、分配任务、综合结果
- 多个 Teammate 独立工作，各有自己的上下文窗口
- 任务通过依赖链分波次执行
- 文件锁定防止重复认领

**最佳场景**：
- 可并行的研究与审查
- 新模块/功能（每人负责一个独立部分）
- 跨层协调（前端、后端、测试各由不同成员负责）

**实战案例**：16 个 Agent 编写 10 万行 Rust C 编译器，可编译 Linux 内核（~2000 个 Claude Code 会话）。

### 3.4 Skills 的渐进式加载（Progressive Disclosure）

**原理**：不要一次告诉 Claude 所有信息，而是告诉它如何找到信息——需要时再加载。

**实现方式**：
- Skills 以目录形式存在，包含 `SKILL.md`
- 用户通过 `/command` 触发特定 Skill
- Skill 执行时按需读取 `reference/` 下的详细规范
- 主 CLAUDE.md 只包含映射表，不包含详细内容

**效果**：大幅降低基线上下文负载，只在需要时加载相关规范。

### 3.5 CLAUDE.md 大项目最佳实践

**核心原则**：
1. **简洁为王**：每行都与实际工作竞争注意力
2. **渐进披露**：告诉 Claude 如何找到信息，而非把信息全部放入
3. **护栏而非手册**：高层指引 + 指针，不是面面俱到的文档
4. **提供替代方案**：不要只说"不要做 X"，要说"改用 Y"

**规则分层**：
- `CLAUDE.md`（根目录）：全局规则
- `.claude/rules/`：按主题分文件（代码风格、测试、安全等）
- 路径作用域规则：通过 YAML frontmatter 的 `paths` 字段限制生效范围
- 子目录 `CLAUDE.md`：按需加载（Claude 读取该目录文件时才加载）

---

## 四、Plan-Driven 实施策略

### 4.1 将设计文档转化为实施计划

**推荐的两阶段方法**（Self-Planning Code Generation）：

1. **Planning Phase**：LLM 生成实施计划（可用较便宜的模型）
2. **Implementation Phase**：LLM 按计划逐步生成代码

**效果**：Pass@1 相对提升 25.4%（对比直接生成），11.9%（对比 CoT 生成）。

**Manus 风格的计划模块**：
- 生成编号的步骤列表（含描述和状态）
- 作为 "Plan" 事件注入 Agent 上下文
- 计划可以独立于执行阶段生成

### 4.2 每步应给 LLM 多少上下文

**核心原则**：小而聚焦的上下文胜过一个巨大的 prompt。

**具体建议**（综合多个来源）：

| 上下文类型 | 建议 |
|-----------|------|
| 总上下文利用率 | **控制在 40% 以下** |
| 每步加载内容 | 当前步骤的规格段落 + 全局约束 + 已完成步骤的摘要 |
| 无关信息 | 主动排除，不要"万一有用"就保留 |
| 刷新时机 | 每个主要功能完成后刷新上下文 |

### 4.3 步骤间依赖处理

**文件持久化模式**（Fresh Context Pattern / Ralph Loop）：

三个持久化文件：
1. **TASK.md**：不可变的任务定义，Claude 只读不写
2. **PROGRESS.md**：跨迭代累积状态，记录完成状态、阻塞点、下一步
3. **Git commits**：提供审计和回滚能力

**每个 TASK.md 应代表 30-90 分钟的工作，跨 3-10 次迭代。**

### 4.4 "摘要+局部详情"的混合加载模式

**层次化摘要法**（Addy Osmani 推荐）：

1. 先让 Agent 将完整规格摘要为简洁大纲（含关键点和引用标签）
2. 摘要保留在 system/assistant message 中作为"心智地图"
3. 实施每步时，只加载该步骤对应的详细段落
4. Agent 始终保持对全局结构的感知，同时聚焦局部细节

**实际操作**：
```
Step 1: 实施数据库 Schema
  → 加载：Schema 规格段落 + 全局约束

Step 2: 实施认证功能
  → 加载：认证规格段落 + Schema 相关部分（如需要）

Step 3: 实施 API 端点
  → 加载：API 规格段落 + 已完成模块的接口定义
```

### 4.5 Scratchpad / 进度文件模式

**核心原则**：不要强迫模型记住一切，将关键信息持久化到上下文窗口之外。

**模式变体**：

| 模式 | 机制 | 适用场景 |
|------|------|---------|
| **SCRATCHPAD.md** | Claude 将思考和决策写入文件 | 复杂分析、跨会话任务 |
| **plan_*.md** | 结构化的任务分解和进度跟踪 | 大型功能实施 |
| **Checklist Method** | Markdown 文件列出所有任务，逐项勾选 | 迁移、批量重构 |
| **Hydration Pattern** | 持久化任务层级，按需加载到会话中 | 跨日/跨周长期项目 |

### 4.6 RTADev 多 Agent 流水线（ACL 2025）

**五个 Agent 顺序协作**：
1. 需求分析 Agent → PRD
2. 架构 Agent → 系统架构
3. 实现 Agent → 代码
4. 审查 Agent → 代码审查
5. 对齐检查 → 确保每步产出与前序产出一致

**关键机制**：共享上下文仓库（SCR）存储所有 Agent 的产出，新产出必须与 SCR 中的前序产出对齐。

---

## 五、社区最佳实践与工具

### 5.1 主流 AI 编码工具的大文档处理对比

| 工具 | 上下文窗口 | 大文档策略 | 特点 |
|------|-----------|-----------|------|
| **Claude Code** | 200K（1M beta） | Sub-agent 隔离 + Skills 渐进加载 + Agent Teams | 上下文管理最灵活 |
| **Cursor** | 依赖底层模型 | 手动 @ 引用 + 云端 embedding 索引 | 精确但需手动策划 |
| **Windsurf** | 依赖底层模型 | 自动仓库索引 + Cascade 自动爬取 | 自动但可能遗漏 |

### 5.2 Claude Chunks MCP Server

专门为大文档分块设计的 MCP 服务器，支持：
- 将大文档智能分块为有意义的段落
- 每段生成摘要
- 段落间保持上下文关联
- 兼容 Claude Code、Cursor 等多个工具

### 5.3 Context Engineering 方法论

**定义**（Andrej Karpathy）：
> "Context engineering 是为任务提供所有上下文，使 LLM 有可能解决它的艺术。"

**三个核心维度**：
1. **指令 vs 指引**：指令告诉做什么，指引建立惯例
2. **加载决策权**：LLM 自主决定（Skills）、人工决定（Slash 命令）、软件触发（Hooks）
3. **渐进构建**：从最小上下文开始，根据需要逐步扩展

**Martin Fowler 团队的核心观点**：
> "Context engineering is curating what the model sees so that you get a better result."

当 Agent 系统失败时，通常不是因为底层模型能力不足，而是因为**模型没有收到做出好决策所需的上下文**。

### 5.4 Addy Osmani 的 2026 工作流

**核心实践**：
1. 将 LLM 视为需要明确方向的强力结对编程伙伴
2. 将项目分解为迭代步骤/工单，逐个处理
3. 生成结构化的 "prompt plan" 文件，逐步执行
4. 将规格摘要为简洁大纲作为 Agent 的"心智地图"
5. 在规格和提示流中整合测试计划
6. 让 Agent 自动根据规格验证自己的输出

### 5.5 40% 上下文利用率规则

多个来源一致建议：**将上下文利用率控制在 40% 以下**。

原因：
- 超过 40% 后，Agent 容易失去对任务的追踪
- "循环直到解决"的方法在高上下文负载下会导致 Agent 迷失
- 低利用率为压缩、工具输出等保留充足空间

---

## 六、针对 3000 行设计文档的具体推荐方案

### 6.1 文档预处理

**Step 1：结构化分层**

将 3000 行文档拆分为三层：

```
L0 - 全局概览（约 200 行）
├── 项目目标和约束
├── 核心架构图
├── 模块依赖关系
└── 技术栈和全局规约

L1 - 模块规格（每模块 200-500 行，共 N 个模块）
├── 模块 A 的接口定义、数据模型、业务规则
├── 模块 B 的接口定义、数据模型、业务规则
└── ...

L2 - 实施细节（保留在原文档中，按需引用）
├── 具体算法、边界情况、配置项
└── 迁移步骤、兼容性处理
```

**Step 2：生成摘要索引**

创建 `plan_实施索引.md`，包含：
- L0 全局概览（完整保留）
- 每个 L1 模块的一句话摘要 + 原文档行号范围
- 模块间依赖关系图
- 实施顺序建议

### 6.2 实施流程

```
Phase 0: 准备
├── 创建 L0 概览 + L1 摘要索引
├── 确定实施顺序（拓扑排序依赖关系）
└── 创建 plan_实施.md（checklist 格式）

Phase 1: 逐模块实施（循环）
├── 读取 L0 概览 + 当前模块 L1 规格
├── 读取已完成模块的接口定义（仅接口，非实现）
├── 实施当前模块
├── 运行测试验证
├── 更新 plan_实施.md 进度
└── 主动 /compact 或开新会话

Phase 2: 集成验证
├── 加载 L0 概览 + 所有模块接口定义
├── 运行集成测试
└── 修复跨模块问题

Phase 3: 全局审查
├── 使用 Agent Teams 并行审查各模块
├── 对照 L0 概览检查完整性
└── 最终验证
```

### 6.3 上下文加载策略

**每步实施时的上下文组成**：

```
[系统提示 + CLAUDE.md]           ~5K tokens（固定开销）
[L0 全局概览]                     ~3K tokens（始终加载）
[当前模块 L1 规格]                ~5-8K tokens（当前焦点）
[已完成模块接口摘要]              ~2-5K tokens（按需）
[相关代码文件]                    ~10-20K tokens（按需）
[对话历史]                       ~动态增长

总计初始负载：~25-40K tokens（200K 的 12-20%）
```

这确保每步实施时上下文利用率远低于 40% 警戒线。

### 6.4 关键实践

1. **永远不要一次性加载完整 3000 行文档** —— 分层按需加载
2. **L0 概览始终在上下文中** —— 保持全局架构意识
3. **每完成一个模块后 /compact 或开新会话** —— 避免上下文腐烂
4. **使用 PROGRESS.md 跨会话持久化状态** —— 不依赖上下文记忆
5. **关键设计决策写入文件** —— 而非仅存在于对话中
6. **模块间依赖通过接口定义传递** —— 而非完整实现代码
7. **集成阶段使用 Agent Teams** —— 并行验证各模块

---

## 七、通用"大型文档 + LLM 实施"最佳实践框架

### 7.1 文档分层加载模型

```
┌─────────────────────────────────┐
│  L0: Global Overview            │  始终加载（<500 行）
│  目标、架构、约束、技术栈         │
├─────────────────────────────────┤
│  L1: Module Specs               │  按需加载（每个 200-500 行）
│  接口、数据模型、业务规则         │
├─────────────────────────────────┤
│  L2: Implementation Details     │  精确引用（行号范围）
│  算法、边界、配置、迁移           │
└─────────────────────────────────┘
```

### 7.2 实施工作流标准

```
Research → Plan → Implement(loop) → Integrate → Review
   │          │         │               │          │
   │          │         │               │          └─ Agent Teams 并行审查
   │          │         │               └─ 加载全局接口 + 集成测试
   │          │         └─ 每模块：L0+L1+相关代码 → 实施 → 验证 → 持久化
   │          └─ 拓扑排序、Checklist、上下文预算
   └─ Sub-agent 探索代码库，生成摘要
```

### 7.3 上下文预算管理

| 阶段 | 目标利用率 | 上下文组成 |
|------|-----------|-----------|
| 研究 | <30% | Sub-agent 隔离探索 |
| 规划 | <20% | L0 概览 + 模块摘要 |
| 实施 | <40% | L0 + 当前模块 L1 + 相关代码 |
| 集成 | <40% | L0 + 所有接口定义 + 测试结果 |
| 审查 | <30% | Agent Teams 各自独立上下文 |

### 7.4 持久化策略

| 持久化对象 | 存储位置 | 更新时机 |
|-----------|---------|---------|
| 实施计划和进度 | `plan_*.md` | 每完成一个模块 |
| 设计决策和理由 | `SCRATCHPAD.md` | 做出重要决策时 |
| 模块接口定义 | 代码文件本身 | 模块完成时 |
| 测试状态 | `PROGRESS.md` | 每次测试运行后 |
| 全局摘要 | `L0_overview.md` | 架构变更时 |

### 7.5 防御性实践

1. **每 30-90 分钟或完成一个模块后刷新上下文**
2. **在 CLAUDE.md 中指定压缩保留项**（修改文件列表、测试命令、当前进度）
3. **不信任长会话后期的上下文记忆**——关键信息必须持久化
4. **使用 git commit 作为检查点**——每步可回滚
5. **集成验证在独立会话中进行**——不在实施会话中累积

### 7.6 团队协作模式（适用于超大规模文档）

```
Team Lead（编排者）
├── Researcher（Sub-agent）: 探索代码库，生成摘要
├── Module Agent A: 负责模块 A 实施
├── Module Agent B: 负责模块 B 实施
├── Test Agent: 持续运行测试
└── Reviewer: 审查已完成模块
```

**启用条件**：
- 模块间依赖低，可并行实施
- 文档超过 5000 行或涉及 50+ 文件改动
- 需要跨层（前端/后端/数据库）同时推进

---

## 八、关键量化指标速查

| 指标 | 数值 | 来源 |
|------|------|------|
| Lost in the Middle 最大性能降幅 | >30% | Liu et al., 2024 |
| Context Rot 准确率降幅（10k→100k+） | 20-50% | Chroma Research, 2025 |
| Claude Sonnet 4 全窗口精度退化 | <5% | Anthropic 官方 |
| Claude Code 有效上下文空间 | ~167K tokens | Claude Code 文档 |
| Self-Planning Pass@1 提升 | +25.4% | ACM TSE, 2024 |
| 推荐上下文利用率 | <40% | 多来源共识 |
| Fresh Context Pattern 每任务时长 | 30-90 min | Ralph Loop 社区实践 |
| 复合 100 步 99% 准确率的总成功率 | ~36% | 计算推导 |

---

## 来源

### 学术研究
- [Lost in the Middle: How Language Models Use Long Contexts (Liu et al., 2024)](https://arxiv.org/abs/2307.03172)
- [Context Rot: How Increasing Input Tokens Impacts LLM Performance (Chroma, 2025)](https://research.trychroma.com/context-rot)
- [When Does Divide and Conquer Work for Long Context LLM? (2025)](https://arxiv.org/html/2506.16411v1)
- [GLIDER: Divide and Conquer for Decision-Making (ICML 2025)](https://icml.cc/virtual/2025/poster/43989)
- [Divide-and-Conquer Prompting in LLMs](https://arxiv.org/abs/2402.05359)
- [Self-Planning Code Generation with LLMs (ACM TSE)](https://dl.acm.org/doi/10.1145/3672456)
- [RTADev: Intention Aligned Multi-Agent Framework (ACL 2025)](https://aclanthology.org/2025.findings-acl.80.pdf)
- [Context Engineering for Multi-Agent LLM Code Assistants](https://arxiv.org/html/2508.08322v1)

### 官方文档与工程博客
- [Claude Context Windows (Anthropic API Docs)](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [Claude Code Best Practices (Official)](https://code.claude.com/docs/en/best-practices)
- [Claude Code Memory Management](https://code.claude.com/docs/en/memory)
- [Claude Code Sub-Agents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Claude 3 Family Announcement (Anthropic)](https://www.anthropic.com/news/claude-3-family)

### 社区实践与深度文章
- [Context Engineering for Coding Agents (Martin Fowler)](https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html)
- [My LLM Coding Workflow Going into 2026 (Addy Osmani)](https://addyosmani.com/blog/ai-coding-workflow/)
- [How to Write a Good Spec for AI Agents (Addy Osmani)](https://addyosmani.com/blog/good-spec/)
- [Context Management with Subagents in Claude Code (RichSnapp)](https://www.richsnapp.com/article/2025/10-05-context-management-with-subagents-in-claude-code)
- [Context Engineering & Reuse Pattern Under the Hood of Claude Code (LMCache)](https://blog.lmcache.ai/en/2025/12/23/context-engineering-reuse-pattern-under-the-hood-of-claude-code/)
- [Claude Code Context Buffer: The 33K-45K Token Problem](https://claudefa.st/blog/guide/mechanics/context-buffer-management)
- [Fresh Context Pattern (Ralph Loop)](https://deepwiki.com/FlorianBruniaux/claude-code-ultimate-guide/7.3-fresh-context-pattern-(ralph-loop))
- [Planning-with-Files (Manus-style Persistent Planning)](https://github.com/OthmanAdi/planning-with-files)
- [Writing a Good CLAUDE.md (HumanLayer)](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Modular Rules in Claude Code (.claude/rules/)](https://claude-blog.setec.rs/blog/claude-code-rules-directory)
- [Spec-Driven Development with Claude Code](https://alexop.dev/posts/spec-driven-development-claude-code-in-action/)
- [Building a C Compiler with Parallel Claudes (Anthropic)](https://www.anthropic.com/engineering/building-c-compiler)
- [Claude Code Agent Teams Guide](https://claudefa.st/blog/guide/agents/agent-teams)
- [Solving the Lost in the Middle Problem (GetMaxim)](https://www.getmaxim.ai/articles/solving-the-lost-in-the-middle-problem-advanced-rag-techniques-for-long-context-llms/)
- [Databricks Long Context RAG Performance](https://www.databricks.com/blog/long-context-rag-performance-llms)
- [Spec-Driven Development (XB Software)](https://xbsoftware.com/blog/spec-driven-development-ai-assisted-software-engineering/)
- [Mastering Spec-Driven Development (Augment Code)](https://www.augmentcode.com/guides/mastering-spec-driven-development-with-prompted-ai-workflows-a-step-by-step-implementation-guide)
- [Claude Chunks MCP Server](https://playbooks.com/mcp/vetlefo-claude-chunks)
- [Decomposition Beats Intelligence (Medium)](https://medium.com/@ihoyos_48023/the-big-short-of-ai-architecture-ccd46f92b86f)
