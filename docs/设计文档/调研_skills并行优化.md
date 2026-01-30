# Skills 并行优化 方案调研

**日期**：2026-01-29
**状态**：已确认
**文档路径**：docs/设计文档/调研_skills并行优化.md

---

## 1. 背景

当前多数 Skills 采用串行执行模式，效率低下。用户有"很多员工"（子 Agent 可用），希望每个应该并行的地方都开 8-10 个 Agent 来提高效率。需要调研业界最佳实践，确定最优的并行执行方案。

**AC 来源文档**：`docs/需求文档/clarify_skills并行优化.md`

**核心 AC 摘要**：
- AC-1.x: `/explore` 需要 8 Agent 并行信息收集 + 8 Agent 并行方案分析
- AC-2.x: `/test-gen` 需要 10 Agent 并行代码分析 + 10 Agent 并行测试生成
- AC-3.x: `/qa` 需要 Layer1=4 + Layer2=3 + Layer3=串行（与 PRD 对齐）
- AC-4~10: 其他 Skills 的并行化需求

---

## 2. 需求概述

### 2.1 优化范围

| 优先级 | Skill | 当前状态 | 目标 Agent 数 | 预期提升 |
|--------|-------|----------|--------------|----------|
| P0 | `/explore` | 串行 | 8+8 | 5x |
| P0 | `/test-gen` | 串行 | 10+10 | 4-5x |
| P0 | `/qa` | 串行门控 | 4+3+1 | 2-3x |
| P1 | `/critique` | 串行 | 10 | 3-4x |
| P1 | `/design` | 串行 | 9 | 3x |
| P1 | `/experts` | 设计并行但未实现 | 8+2 | 4-5x |
| P2 | `/security` | 部分并行 | 8+8 | 2-3x |
| P2 | `/perf` | 部分并行 | 8+8 | 2-3x |
| P2 | `/overview` | 串行 | 8 | 2x |
| P2 | `/refactor` | 串行 | 10+10 | 2-3x |

### 2.2 项目约束

- **禁止 Mock**：测试必须连接真实服务
- **缓存需人工确认**：不自动添加缓存
- **架构对齐**：与 `/check`、`/run-plan` 保持一致的并行模式

---

## 3. 业界调研

### 3.1 内部参考实现（高优先级）

| # | 来源 | 核心思路 | 优势 | 劣势 | 适用场景 |
|---|------|---------|------|------|---------|
| 1 | `/check` SKILL.md (9 Agent 并行) | Phase 0→1→2→3，Phase 2 并行 9 Agent | 已验证可行，与项目架构一致 | 需要 Phase 间数据传递 | 多维度并行检查 |
| 2 | `/run-plan` tech-lead.md | 多人协作模式（Alice/Bob/Charlie） | 文件隔离，冲突最小化 | 需要 Tech Lead 协调 | 功能开发并行 |
| 3 | `/scan` SKILL.md (4 Agent 并行) | 按扫描类型分 Agent | 简单直接 | Agent 数量固定 | 扫描类任务 |

### 3.2 外部调研来源

| # | 来源 | 核心思路 | 优势 | 劣势 | 适用场景 |
|---|------|---------|------|------|---------|
| 4 | Claude Code Task Tool 官方文档 | 单消息多 Task 调用，最多 7-10 并发 | 官方支持，20k token overhead | 上下文膨胀快 | 所有并行场景 |
| 5 | LangGraph 并行模式 | Scatter-Gather + Pipeline 并行 | 状态管理完善，DAG 支持 | 学习成本高，需额外框架 | 复杂工作流 |
| 6 | Multi-Agent 协调模式 | Orchestrator-Worker 模式 | 灵活，支持动态任务分配 | 协调开销大 | 动态任务分配 |
| 7 | Anthropic Best Practices | 3-Task Rule：少于 3 步直接做 | 避免不必要的 Task 开销 | 需要判断任务复杂度 | 任务复杂度评估 |

### 3.3 调研详情

#### 来源 1: `/check` SKILL.md - 9 Agent 并行架构

**核心架构**：
```
Phase 0: 自我审问（串行）
    ↓
Phase 1: 变更范围检查（串行，快速）
    ↓
Phase 2: 并行检查（9 Agent 同时）
    ├── Agent1: 铁律检查 (Explore)
    ├── Agent2: 后端自动化 (Bash)
    ├── Agent3: 前端自动化 (Bash)
    ├── Agent4: 代码质量审查 (Explore)
    ├── Agent5: 文档同步检查 (Explore)
    ├── Agent6: 服务启动验证 (Bash)
    ├── Agent7: 需求覆盖检查 (Explore)
    ├── Agent8: TDD 流程验证 (Explore)
    └── Agent9: Hooks 配置检测 (Bash)
    ↓
Phase 3: 汇总报告（串行）
```

**关键实现细节**：
- 使用 Task tool 在同一消息中发送多个调用
- 每个 Agent 有明确的 subagent_type（Explore/Bash）
- Phase 间通过主 Agent 传递数据

#### 来源 2: `/run-plan` 多人协作模式

**核心架构**：
```
第一批（串行）: Tech Lead 前置工作
  └─ T0: 基础设施

第二批（并行）: 开发者并行
  ├─ T1: Alice - 登录功能
  ├─ T2: Bob - 注册功能
  └─ T3: Charlie - 密码重置

第三批（串行）: Tech Lead 后置工作
  └─ T4: 集成验证
```

**关键实现细节**：
- 文件范围隔离，避免冲突
- Tech Lead 负责协调和集成
- 支持中断恢复（checkpoint）

#### 来源 4: Claude Code Task Tool 最佳实践

**核心发现**：
- **最大并发**：7-10 个 Agent（实际测试上限）
- **Token 开销**：每个 Task 约 20k token overhead
- **3-Task Rule**：少于 3 步的任务直接做，不用 Task
- **调用方式**：必须在同一消息中发送多个 Task 调用

**代码示例**：
```markdown
同时启动多个 Task（在一条消息中）：

<Task subagent_type="Explore" description="Agent1 任务">
[prompt]
</Task>

<Task subagent_type="Explore" description="Agent2 任务">
[prompt]
</Task>

... 最多 10 个
```

#### 来源 5: LangGraph 并行模式

**Scatter-Gather 模式**：
1. Scatter：将任务分发给多个 Worker
2. 并行执行：各 Worker 独立处理
3. Gather：收集所有结果并汇总

**Pipeline 并行**：
1. 多个阶段串行
2. 每个阶段内部并行
3. 适合有依赖关系的任务

#### 来源 6: Multi-Agent 协调模式

**Orchestrator-Worker 模式**：
- Orchestrator（主 Agent）：任务分发、结果收集、错误处理
- Worker（子 Agent）：专注单一任务
- 通信机制：通过返回值传递

**推荐团队规模**：3-7 个 Agent per workflow

#### 来源 7: Anthropic 3-Task Rule

**规则**：
- 少于 3 个步骤 → 直接执行，不用 Task
- 3-10 个步骤 → 使用 Task
- 超过 10 个步骤 → 考虑分层或分批

**原因**：每个 Task 有 20k token overhead，小任务不划算

---

## 4. 方案选择

### 4.1 可行方案对比

#### 方案 A：Phase 模式 + 同消息多 Task（推荐）

**来源**：`/check` SKILL.md + Claude Code 官方实践

**概述**：采用 Phase 0→1→2→3 架构，Phase 2 使用同一消息多 Task 并行

**核心思路**：
```
Phase 0/1: 串行准备（数据收集、前置检查）
    ↓ 主 Agent 汇总数据
Phase 2: 并行执行（8-10 Agent 同时启动）
    ↓ 主 Agent 收集结果
Phase 3: 串行汇总（合并、去重、输出）
```

**优势**：
- 与现有 `/check`、`/run-plan` 架构一致
- 已在项目中验证可行
- 支持灵活的 subagent_type 选择
- Phase 间数据传递清晰

**劣势**：
- Phase 间有串行等待
- 需要主 Agent 协调

**工作量**：每个 Skill 约 2-4 小时改造

**风险**：
- 上下文膨胀：10 Agent × 20k = 200k token
- 缓解：控制每个 Agent 的输出量

#### 方案 B：纯 Scatter-Gather 模式

**来源**：LangGraph 并行模式

**概述**：单次 Scatter 分发所有任务，等待全部完成后 Gather

**核心思路**：
```
Scatter: 一次性启动所有 Agent
    ↓ 并行执行
Gather: 等待全部完成，一次性汇总
```

**优势**：
- 实现简单，逻辑清晰
- 最大化并行度

**劣势**：
- 无法处理阶段依赖（如 Phase 1 输出作为 Phase 2 输入）
- 不支持门控（如 `/qa` 的 Layer 门控）
- 与现有架构不一致

**工作量**：每个 Skill 约 1-2 小时改造

**风险**：
- 无法满足 `/qa` 的门控需求
- 缓解：无法缓解，该方案不适用于门控场景

#### 方案 C：动态 Orchestrator-Worker 模式

**来源**：Multi-Agent 协调模式

**概述**：Orchestrator 动态分配任务，Worker 按需启动

**核心思路**：
```
Orchestrator: 分析任务，动态决定启动哪些 Worker
    ↓ 按需启动
Workers: 各自执行，返回结果
    ↓ 动态调整
Orchestrator: 根据结果决定下一步
```

**优势**：
- 灵活，支持动态任务
- 可以根据中间结果调整

**劣势**：
- 实现复杂
- 与现有静态 Phase 模式不一致
- 调试困难

**工作量**：每个 Skill 约 4-6 小时改造

**风险**：
- 复杂度高，可能引入 bug
- 缓解：从简单 Skill 开始试点

### 4.2 推荐理由

**选择方案 A（Phase 模式 + 同消息多 Task）**，理由如下：

1. **架构对齐**：与现有 `/check`、`/run-plan` 完全一致，无需学习新模式
2. **已验证可行**：`/check` 的 9 Agent 并行已在生产环境运行
3. **支持门控**：Phase 间可以加入门控检查（满足 `/qa` 需求）
4. **数据传递清晰**：Phase N → 主 Agent 汇总 → Phase N+1
5. **工作量适中**：每个 Skill 2-4 小时，可控

---

## 5. 实施规范

### 5.1 subagent_type 选择规范

| 任务类型 | subagent_type | 适用场景 |
|---------|---------------|---------|
| `Explore` | 代码分析、文档搜索、方案调研 | 需要读取多文件、搜索代码库 |
| `Bash` | 命令执行、工具运行、测试执行 | 需要运行 shell 命令 |
| `general-purpose` | 复杂推理、方案设计、综合分析 | 需要多步骤推理和决策 |

### 5.2 并行调用模式（统一标准）

所有并行 Agent 必须在**同一条消息**中通过多个 Task tool 调用发出：

```markdown
同时启动以下 N 个检查任务（使用 Task 工具）：

<Task subagent_type="..." description="Agent1 描述">
[Agent1 的 prompt]
</Task>

<Task subagent_type="..." description="Agent2 描述">
[Agent2 的 prompt]
</Task>

... 最多 10 个
```

### 5.3 Phase 间数据传递机制

1. Phase N 完成后，主 Agent 收集所有返回结果
2. 主 Agent 整理为统一格式（JSON 或 Markdown）
3. 将整理后的数据作为 Phase N+1 各 Agent 的输入

```markdown
## Phase 1 输出（主 Agent 汇总）

```json
{
  "source_1": { "title": "...", "summary": "..." },
  "source_2": { "title": "...", "summary": "..." },
  ...
}
```

## Phase 2 输入（传递给各 Agent）

Agent 1-8 各自分析一个来源，从上述 JSON 中获取分配的数据。
```

### 5.4 错误处理机制

| 场景 | 处理方式 |
|------|---------|
| 单个 Agent 超时（>120s） | 标记失败，继续处理其他结果 |
| 单个 Agent 崩溃 | 标记失败，继续处理其他结果 |
| 失败 Agent 数量 > 50% | 整体任务标记为失败 |
| 门控检查失败（如 `/qa`） | 停止后续 Phase，输出失败报告 |

### 5.5 3-Task Rule 应用

**评估标准**：
- 任务步骤 < 3 → 直接执行，不用 Task
- 任务步骤 ≥ 3 → 使用 Task

**示例**：
- `/overview` 的"配置文件分析" → 可能只需 2 步（读取 + 解析），直接做
- `/test-gen` 的"边界值测试生成" → 需要多步（分析 + 设计 + 生成），用 Task

---

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 上下文膨胀 | 10 Agent × 20k = 200k token | 见下方「6.1 上下文膨胀控制标准」 |
| 并行 Agent 设计冲突 | `/design` 各层设计不一致 | 主 Agent 在汇总阶段做一致性校验 |
| Token 超限 | 复杂任务可能超出限制 | 分批执行，或减少 Agent 数量 |
| 调试困难 | 并行执行难以定位问题 | 每个 Agent 输出详细日志 |
| 并行化效果不佳 | 需要快速恢复到稳定状态 | 见下方「6.2 回滚方案」 |

### 6.1 上下文膨胀控制标准

| 控制项 | 标准 | 说明 |
|--------|------|------|
| Agent 输出长度 | ≤ 2000 字符 | 超长输出使用摘要 |
| 输出格式 | 结构化 JSON | 避免冗长文本描述 |
| 中间结果 | 只保留关键信息 | Phase 间传递精简数据 |
| 错误信息 | ≤ 500 字符 | 只保留错误类型和关键堆栈 |

**示例**：
```json
// ✅ 好的输出格式（结构化、精简）
{
  "status": "success",
  "findings": ["issue1", "issue2"],
  "summary": "发现 2 个问题"
}

// ❌ 差的输出格式（冗长、非结构化）
"经过详细分析，我发现了以下问题...（500字描述）"
```

### 6.2 回滚方案

**原则**：保留原串行实现，通过配置开关切换

**实施方式**：

1. **代码层面**：
   - 保留原串行执行函数（重命名为 `_serial_execute`）
   - 新增并行执行函数（命名为 `_parallel_execute`）
   - 主函数通过配置决定调用哪个

2. **配置开关**：
   ```markdown
   # 在 SKILL.md 头部添加
   parallel_mode: true  # false 则回退到串行
   ```

3. **回滚触发条件**：
   - 并行执行失败率 > 30%
   - 用户明确要求回滚
   - 发现严重 bug 需要紧急修复

4. **回滚操作**：
   - 修改 `parallel_mode: false`
   - 无需修改代码，立即生效

---

## 7. 实施优先级

| 批次 | Skills | 原因 |
|------|--------|------|
| P0（第一批） | `/explore`, `/test-gen`, `/qa` | 使用频率高，收益大 |
| P1（第二批） | `/critique`, `/design`, `/experts` | 设计阶段核心 Skill |
| P2（第三批） | `/security`, `/perf`, `/overview`, `/refactor` | 辅助类 Skill |

---

## 8. 调研结论

基于以上调研，推荐采用 **Phase 模式 + 同消息多 Task**（方案 A）：

1. **与项目现有架构完全对齐**（`/check` 9 Agent、`/run-plan` 多人协作）
2. **已验证可行**，风险可控
3. **支持门控和阶段依赖**，满足 `/qa` 等复杂场景
4. **工作量适中**，可按优先级分批实施

---

下一步：/design（架构设计）
