# 需求澄清结果

**需求名称**：Skills 并行优化
**澄清日期**：2026-01-29
**状态**：已确认（评审修复版 v1.1）
**文档路径**：docs/需求澄清/clarify_skills并行优化.md

---

## 0. 项目上下文

**功能类型**：[Skills开发]

> ⚠️ **重要**：此标记决定是否应用全栈开发规范
> - 全栈：需要前后端同步完成
> - 纯后端/纯前端/CLI/Skills：不强制要求全栈

**相关规范**：
- `~/.claude/rules/RULES.md` - 核心开发规范（铁律：禁止降级、禁止硬编码、禁止 Mock）
- `~/.claude/reference/性能效率.md` - 性能规范（缓存需人工确认）

**相关代码**：
- `开发检查_check/SKILL.md` - 已有 9 Agent 并行架构（参考标杆）
- `执行计划_run-plan/SKILL.md` - 多人协作模式（Alice/Bob/Charlie）
- `测试验收_qa/docs/PRD_qa并行优化.md` - `/qa` 的并行优化 PRD（v1.2）

**关键约束**：
- 项目铁律：禁止 Mock（测试必须连接真实服务）
- 性能规范：缓存需人工确认，不自动添加
- 架构对齐：与 `/check`、`/run-plan` 保持一致的并行模式

---

## 1. 背景

当前多数 Skills 采用串行执行模式，效率低下。用户有"很多员工"（子 Agent 可用），希望每个应该并行的地方都开 8-10 个 Agent 来提高效率。

**现状分析**（已完成）：
- 全部 27 个 Skills 已分析
- 识别出 10 个可优化的 Skill
- 识别出 4 个应保持串行的 Skill（有明确理由）

---

## 2. 目标

- **功能目标**：为 10 个 Skill 添加 8-10 个子 Agent 并行执行点
- **质量目标**：效率提升 2-5 倍，单点失败不影响整体
- **时间目标**：按 P0 → P1 → P2 分批实施
- **规范要求**：与 `/check`、`/run-plan` 架构对齐

---

## 3. 技术方案要点

### 3.1 架构参考（与现有并行 Skill 对齐）

| 参考 Skill | 并行模式 | 本方案对齐点 |
|------------|---------|-------------|
| `/check` | 9 Agent 并行（Phase 2），同一消息多 Task 调用 | 所有并行点采用相同调用模式 |
| `/run-plan` | 多人协作模式（Alice/Bob/Charlie 并行） | 参考开发者并行的隔离机制 |
| `/scan` | 4 Agent 并行扫描 | 参考扫描类任务的 Agent 划分 |

### 3.2 subagent_type 选择规范

| 任务类型 | subagent_type | 适用场景 |
|---------|---------------|---------|
| `Explore` | 代码分析、文档搜索、方案调研 | 需要读取多文件、搜索代码库 |
| `Bash` | 命令执行、工具运行、测试执行 | 需要运行 shell 命令 |
| `general-purpose` | 复杂推理、方案设计、综合分析 | 需要多步骤推理和决策 |

### 3.3 Phase 间数据传递机制

1. Phase N 完成后，主 Agent 收集所有返回结果
2. 主 Agent 整理为统一格式（JSON 或 Markdown）
3. 将整理后的数据作为 Phase N+1 各 Agent 的输入

### 3.4 优化范围

| 优先级 | Skill | 当前状态 | 预期提升 |
|--------|-------|----------|----------|
| P0 | `/explore` | 串行 | 5x |
| P0 | `/test-gen` | 串行 | 4-5x |
| P0 | `/qa` | 串行门控 | 2-3x |
| P1 | `/critique` | 串行 | 3-4x |
| P1 | `/design` | 串行 | 3x |
| P1 | `/experts` | 设计并行但未实现 | 4-5x |
| P2 | `/security` | 部分并行 | 2-3x |
| P2 | `/perf` | 部分并行 | 2-3x |
| P2 | `/overview` | 串行 | 2x |
| P2 | `/refactor` | 串行 | 2-3x |

### 3.5 保持串行的 Skills（有明确理由）

| Skill | 理由 |
|-------|------|
| `/clarify` | 需要用户交互，无法并行 |
| `/debug` | 阶段依赖性强，需要上一步结果 |
| `/ship` | 交互式确认流程 |
| `/plan` | 需要全局理解后统一规划 |

**风险点**：
- 并行 Agent 间可能产生设计冲突（如 `/design` 各层设计不一致）
- 需要主 Agent 在汇总阶段做一致性校验

---

## 4. 验收标准（Acceptance Criteria）

> ⚠️ **AC 单一来源声明**：此处定义的 AC 是整个开发流程的唯一验收标准。
> `/plan`、`/test-gen`、`/qa` 必须引用此 AC，禁止重新定义。

### 4.1 AC 表格（Given-When-Then 格式）

#### 正常流程

| AC-ID | Given（前置条件） | When（操作） | Then（预期结果） | 优先级 | 测试方法 |
|-------|------------------|-------------|-----------------|--------|---------|
| AC-1.1 | 用户触发 `/explore` | 进入信息收集阶段 | 同时启动 8 个 Agent（subagent_type=Explore）并行调研不同信息源 | P0 | 集成测试 |
| AC-1.2 | `/explore` Phase 1 完成 | 进入方案分析阶段 | 主 Agent 汇总后，按候选方案数量启动 N 个 Agent（N≤8，subagent_type=general-purpose）并行分析 | P0 | 集成测试 |
| AC-1.3 | `/explore` 所有并行 Agent 完成 | 汇总输出 | 主 Agent 综合所有结果，输出结构化对比报告 | P0 | E2E |
| AC-2.1 | 用户触发 `/test-gen` | 进入代码分析阶段 | 按代码单元数量启动 N 个 Agent（2≤N≤10，subagent_type=Explore）并行分析各自负责的代码单元 | P0 | 集成测试 |
| AC-2.2 | `/test-gen` Phase 1 完成 | 进入测试生成阶段 | 启动 N 个 Agent（与 Phase 1 相同，subagent_type=general-purpose）并行生成各自负责的代码单元测试 | P0 | 集成测试 |
| AC-2.3 | `/test-gen` 所有测试生成完成 | 汇总输出 | 主 Agent 合并去重，输出完整测试文件 | P0 | E2E |
| AC-3.1 | 用户触发 `/qa` | 进入 Layer 1 | 同时启动 4 个 Agent（subagent_type=Bash）并行执行单元测试（与 PRD 对齐） | P0 | 集成测试 |
| AC-3.2 | `/qa` Layer 1 全部通过 | 进入 Layer 2 | 同时启动 3 个 Agent（subagent_type=Bash）并行执行集成测试（与 PRD 对齐） | P0 | 集成测试 |
| AC-3.3 | `/qa` Layer 2 全部通过 | 进入 Layer 3 | 串行执行 E2E 测试（浏览器资源限制，与 PRD 对齐） | P0 | E2E |
| AC-4.1 | 用户触发 `/critique` | 进入评审阶段 | 同时启动 5 个评审组 Agent（subagent_type=general-purpose），每组覆盖 2 个相关维度 | P1 | 集成测试 |
| AC-5.1 | 用户触发 `/design` | 进入设计阶段 | Phase 1a 串行执行数据模型设计，Phase 1b 同时启动 6 个 Agent（subagent_type=general-purpose）并行设计数据层/业务层/接口层 | P1 | 集成测试 |
| AC-6.1 | 用户触发 `/experts` | 进入分析阶段 | 同时启动 8 个必选专家 Agent（subagent_type=general-purpose）并行分析 | P1 | 集成测试 |
| AC-6.2 | `/experts` 任务涉及业务流程 | 启动可选专家 | 额外启动业务分析师 Agent | P1 | 单元测试 |
| AC-6.3 | `/experts` 任务涉及特定领域 | 启动可选专家 | 额外启动领域专家 Agent | P1 | 单元测试 |
| AC-7.1 | 用户触发 `/security` | 进入扫描阶段 | 同时启动 8 个 Agent（subagent_type=Bash）并行执行不同安全检测 | P2 | 集成测试 |
| AC-8.1 | 用户触发 `/perf` | 进入分析阶段 | 同时启动 8 个 Agent（subagent_type=Bash）并行分析不同性能维度 | P2 | 集成测试 |
| AC-9.1 | 用户触发 `/overview` | 进入信息收集阶段 | 同时启动 8 个 Agent（subagent_type=Explore）并行收集不同类型信息 | P2 | 集成测试 |
| AC-10.1 | 用户触发 `/refactor` | 进入分析阶段 | 同时启动 10 个 Agent（subagent_type=Explore）并行检测不同代码坏味道 | P2 | 集成测试 |

#### 异常流程

| AC-ID | Given | When | Then | 优先级 | 测试方法 |
|-------|-------|------|------|--------|---------|
| AC-ERR-1 | 任一并行 Agent 超时（超过该 Skill 定义的超时阈值） | 等待 Agent 结果 | 标记该 Agent 失败，继续处理其他结果，最终报告标注数据完整性 | P1 | API 测试 |
| AC-ERR-2 | 任一并行 Agent 崩溃 | 等待 Agent 结果 | 标记该 Agent 失败，继续处理其他结果 | P1 | API 测试 |
| AC-ERR-3 | 失败 Agent 数量超过 50% | 汇总阶段 | 整体任务标记为失败，输出失败报告 | P1 | 单元测试 |
| AC-ERR-4 | `/qa` 任一 Layer 有失败 | 门控检查 | 停止后续 Layer，输出失败报告，等待修复 | P0 | 集成测试 |

#### 边界情况

| AC-ID | Given | When | Then | 优先级 | 测试方法 |
|-------|-------|------|------|--------|---------|
| AC-EDGE-1 | `/test-gen` 生成的测试 | 铁律检查 | 不包含 Mock/MagicMock/patch 等禁止用法（遵循项目铁律） | P0 | 单元测试 |
| AC-EDGE-2 | `/perf` 优化建议涉及缓存 | 生成建议 | 标注"需人工确认"，不自动添加缓存代码（遵循性能规范） | P1 | 单元测试 |
| AC-EDGE-3 | `/design` Phase 1 完成 | 一致性校验 | 检查数据层/业务层/接口层设计是否一致，发现冲突则列出并给出解决建议 | P1 | 集成测试 |
| AC-EDGE-4 | `/experts` 存在专家分歧 | 会诊阶段 | 列出分歧点，给出权衡建议 | P2 | 单元测试 |

### 4.2 质量验收（可量化指标）

| 指标 | 标准 |
|------|------|
| 并行调用 | 并行点启动的 Agent 数量符合各 Skill 规范定义（如 /test-gen 动态 2-10，/qa Layer1=4 等） |
| 效率提升 | 优化后执行时间相比串行版本减少 50%+ |
| 稳定性 | 错误处理完善，单点失败不影响整体 |
| 兼容性 | 与现有工作流（`/check`、`/run-plan`）无缝衔接 |

### 4.3 规范验收（来自项目规范）

| 规范 | 验收点 |
|------|-------|
| 禁止 Mock | `/test-gen` 生成的测试不包含 Mock 相关代码 |
| 缓存需人工确认 | `/perf` 的缓存建议标注"需人工确认" |
| 架构对齐 | 并行模式与 `/check`、`/run-plan` 一致 |
| PRD 对齐 | `/qa` 的 Agent 数量与 `PRD_qa并行优化.md` 一致（Layer1=4，Layer2=3，Layer3=串行） |

---

## 5. 实施顺序

1. **第一批（P0）**：`/explore`、`/test-gen`、`/qa`
2. **第二批（P1）**：`/critique`、`/design`、`/experts`
3. **第三批（P2）**：`/security`、`/perf`、`/overview`、`/refactor`

---

## 6. 详细架构设计

### 6.1 `/explore` 方案探索并行化

```
Phase 1: 并行信息收集（8 Agent，subagent_type=Explore）
├── Agent 1: GitHub 仓库搜索
├── Agent 2: Claude Code 最佳实践
├── Agent 3: Cursor 方案调研
├── Agent 4: Gemini 方案调研
├── Agent 5: Google 搜索（技术博客）
├── Agent 6: Stack Overflow 调研
├── Agent 7: 官方文档搜索
└── Agent 8: 开源项目案例
    ↓
    数据传递：各 Agent 返回结构化 JSON，主 Agent 汇总为候选方案列表
    ↓
Phase 2: 并行方案分析（N Agent，N≤8，subagent_type=general-purpose）
├── Agent 1-N: 各自分析一个候选方案（从 Phase 1 汇总的列表中分配，按候选方案数量动态确定 N）
    ↓
Phase 3: 汇总输出（串行，主 Agent）
└── 综合对比，输出推荐方案
```

### 6.2 `/test-gen` 测试生成并行化

```
Phase 0: 代码范围识别（串行）
└── 主 Agent: 识别待测函数/类，输出代码单元列表

代码单元数量与 Agent 分配规则：
| 代码单元数量 | Agent 数量 | 分配策略 |
|-------------|-----------|---------|
| 1-2         | 2         | 最小 Agent 数 |
| 3-10        | N (=单元数) | 每个 Agent 1 个代码单元 |
| 11-20       | 10        | 每个 Agent 1-2 个代码单元 |
| 21-30       | 10        | 每个 Agent 2-3 个代码单元 |
| >30         | 10        | 按模块分组 |

Phase 1: 并行代码分析（N Agent，按代码单元拆分，subagent_type=Explore）
├── Agent 1: 分析 function_a（签名、边界、异常、依赖全维度）
├── Agent 2: 分析 function_b（签名、边界、异常、依赖全维度）
├── Agent 3: 分析 class_c（签名、边界、异常、依赖全维度）
└── ...（每个 Agent 负责独立代码单元，避免重复）

Phase 2: 并行测试生成（N Agent，按代码单元拆分，subagent_type=general-purpose）
├── Agent 1: 为 function_a 生成测试（正常路径+边界值+异常+属性测试）
├── Agent 2: 为 function_b 生成测试（正常路径+边界值+异常+属性测试）
├── Agent 3: 为 class_c 生成测试（正常路径+边界值+异常+集成测试）
└── ...（每个 Agent 为其负责的代码单元生成全类型测试）

Phase 3: 汇总合并（串行）
└── 主 Agent: 合并测试文件（无需去重，各 Agent 负责独立代码单元）
```

### 6.3 `/qa` 测试验收并行化（与 PRD 对齐）

```
Layer 1: 单元测试（4 Agent 并行，subagent_type=Bash）
├── Agent 1-4: 按模块分组执行单元测试
│
│   门控：全部通过才进入 Layer 2
│
Layer 2: 集成测试（3 Agent 并行，subagent_type=Bash）
├── Agent 1-3: 按模块分组执行集成测试
│
│   门控：全部通过才进入 Layer 3
│
Layer 3: E2E 测试（串行执行，1 Agent）
└── 按顺序执行 E2E 流程（浏览器资源限制）
```

**与 PRD 对齐说明**：
- Layer 1 最大并行数：4（与 PRD_qa并行优化.md 一致）
- Layer 2 最大并行数：3（与 PRD_qa并行优化.md 一致）
- Layer 3 串行执行（与 PRD_qa并行优化.md 一致，Claude in Chrome MCP 不支持多会话）

### 6.4 `/critique` 方案评审并行化

```
Phase 1: 并行评审（5 评审组，subagent_type=general-purpose）
├── Agent 1: 需求覆盖组（完整性 + 遗漏分析）
├── Agent 2: 方案一致性组（一致性 + 可行性）
├── Agent 3: 风险安全组（风险识别 + 安全性）
├── Agent 4: 工程质量组（技术债务 + 可维护性 + 性能）
└── Agent 5: 用户视角组（用户体验）

Phase 2: 汇总（串行）
└── 主 Agent: 综合所有评审意见，输出评审报告
```

### 6.5 `/design` 架构设计并行化（分层串行+并行）

```
Phase 1a: 数据模型设计（串行，1 Agent）
└── Agent 1: 数据模型设计（实体、关系、ER 图）
    ↓ 数据模型完成后传递给 Phase 1b
Phase 1b: 并行设计（6 Agent，subagent_type=general-purpose）
├── Agent 2: 数据访问层设计（Repository、DAO）
├── Agent 3: 业务逻辑设计（Service、状态机、验证规则）
├── Agent 4: API 接口设计（REST 端点、DTO）
├── Agent 5: 错误处理设计（异常、响应码）
├── Agent 6: 安全机制设计（认证、授权）
└── Agent 7: 数据迁移设计（Schema 变更）

Phase 2: 一致性校验（串行）
└── 主 Agent: 检查各层设计间的一致性，解决冲突

Phase 3: 输出设计文档（串行）
└── 主 Agent: 整合输出完整设计文档
```

### 6.6 `/experts` 专家协作并行化（固定 8 必选 + 2 可选）

```
Phase 1: 并行专家分析
├── 必选专家（8 Agent，始终启动，subagent_type=general-purpose）
│   ├── Agent 1: 后端架构师
│   ├── Agent 2: 前端架构师
│   ├── Agent 3: 数据库专家
│   ├── Agent 4: 安全专家
│   ├── Agent 5: 性能专家
│   ├── Agent 6: DevOps 专家
│   ├── Agent 7: 测试专家
│   └── Agent 8: UX 专家
└── 可选专家（2 Agent，按需启动）
    ├── Agent 9: 业务分析师（当涉及业务流程时启动）
    └── Agent 10: 领域专家（当涉及特定领域知识时启动）

Phase 2: 专家会诊（串行）
└── 主 Agent: 模拟圆桌会议，整合各专家意见

Phase 3: 输出决策（串行）
└── 主 Agent: 输出综合建议和行动项
```

**可选专家启动条件**：
- Agent 9（业务分析师）：任务涉及业务流程、工作流、审批流程
- Agent 10（领域专家）：任务涉及特定领域（金融、医疗、法律等）

### 6.7 `/security` 安全扫描并行化

```
Phase 1: 并行扫描（8 Agent，subagent_type=Bash）
├── Agent 1: Bandit 扫描
├── Agent 2: Semgrep 扫描
├── Agent 3: Gitleaks 扫描
├── Agent 4: 依赖漏洞扫描
├── Agent 5: SQL 注入检测
├── Agent 6: XSS 检测
├── Agent 7: 认证授权审查
└── Agent 8: 敏感数据暴露检测

Phase 2: 并行修复建议（8 Agent，subagent_type=general-purpose）
├── Agent 1-8: 各自为发现的漏洞生成修复代码

Phase 3: 汇总报告（串行）
└── 主 Agent: 按 OWASP Top 10 分类，输出报告
```

### 6.8 `/perf` 性能分析并行化

```
Phase 1: 并行分析（8 Agent，subagent_type=Bash）
├── Agent 1: CPU 热点分析
├── Agent 2: 内存使用分析
├── Agent 3: I/O 瓶颈分析
├── Agent 4: N+1 查询检测
├── Agent 5: 查询优化分析（索引使用、慢查询，不涉及缓存）
├── Agent 6: 并发性能分析
├── Agent 7: 网络延迟分析
└── Agent 8: 资源泄漏检测

Phase 2: 并行优化建议（8 Agent，subagent_type=general-purpose）
├── Agent 1-8: 各自为发现的问题生成优化方案
│   注意：涉及缓存的建议必须标注"需人工确认"

Phase 3: 汇总报告（串行）
└── 主 Agent: 按影响程度排序，输出火焰图和优化建议
```

### 6.9 `/overview` 项目概览并行化

```
Phase 1: 并行信息收集（8 Agent，subagent_type=Explore）
├── Agent 1: 目录结构分析
├── Agent 2: 技术栈识别
├── Agent 3: 依赖关系分析
├── Agent 4: 核心模块识别
├── Agent 5: API 端点收集
├── Agent 6: 数据模型分析
├── Agent 7: 配置文件分析
└── Agent 8: 文档收集

Phase 2: 汇总输出（串行）
└── 主 Agent: 整合信息，输出项目概览
```

### 6.10 `/refactor` 重构分析并行化

```
Phase 1: 并行分析（10 Agent，subagent_type=Explore）
├── Agent 1: God Class 检测
├── Agent 2: 长方法检测
├── Agent 3: 重复代码检测
├── Agent 4: 过度耦合检测
├── Agent 5: 接口膨胀检测
├── Agent 6: 魔法数字检测
├── Agent 7: 死代码检测
├── Agent 8: 命名规范检测
├── Agent 9: 复杂度分析
└── Agent 10: 依赖循环检测

Phase 2: 并行重构建议（10 Agent，subagent_type=general-purpose）
├── Agent 1-10: 各自生成重构方案

Phase 3: 汇总计划（串行）
└── 主 Agent: 整合为重构计划，交给 /run-plan 执行
```

---

## 7. 通用实现规范

### 7.1 并行调用模式

所有并行 Agent 必须在同一条消息中通过多个 Task tool 调用发出（参考 `/check` 的实现）。

### 7.2 错误处理

- 单个 Agent 失败不影响其他 Agent
- 最终汇总时标注失败 Agent 和原因
- 失败 Agent 数量超过 50% 时，整体任务标记为失败

### 7.3 超时控制

- 单个 Agent 超时：120 秒（默认值，各 Skill 可根据任务特点自定义，见下表）

**各 Skill 超时配置表**：

| Skill | 超时值 | 说明 |
|-------|--------|------|
| 默认 | 120 秒 | 适用于未特别声明的 Skill |
| `/explore` | 120 秒 | 默认值，信息收集和方案分析任务 |
| `/test-gen` | 60 秒 | 代码分析和测试生成任务较轻量 |
| `/experts` | 60 秒 | 单个专家分析任务较聚焦 |
| `/design` Phase 1a | 90 秒 | 数据模型设计较复杂，是其他 Agent 的基础依赖 |
| `/design` Phase 1b | 60 秒 | 各层并行设计任务 |
| 整体阶段 | 300 秒 | 所有 Skill 的单阶段超时上限 |

- 超时后强制进入下一阶段，标注超时 Agent

---

以上理解是否正确？确认后进入方案探索 (`/explore`)
