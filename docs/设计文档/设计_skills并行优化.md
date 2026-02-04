# Skills 并行优化 架构设计

**设计日期**：2026-01-29
**状态**：已确认
**文档路径**：docs/设计文档/设计_skills并行优化.md
**前置文档**：
- AC 文档：docs/需求澄清/clarify_skills并行优化.md
- 调研文档：docs/设计文档/调研_skills并行优化.md

---

## 1. 技术方案

**选定方案**：Phase 模式 + 同消息多 Task（方案 A）

**来源**：`/check` SKILL.md + Claude Code 官方实践

**核心架构**：
```
Phase 0/1: 串行准备（门控检查、数据收集）
    ↓ 主 Agent 汇总数据
Phase 2: 并行执行（8-10 Agent 同时启动）
    ↓ 主 Agent 收集结果
Phase 3: 串行汇总（合并、去重、输出）
```

**选择理由**：
1. 与现有 `/check`、`/run-plan` 架构完全一致
2. 已在生产环境验证可行
3. 支持门控和阶段依赖

---

## 2. 模块划分

### 2.1 系统边界图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Skills 并行执行框架                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Phase      │  │   Agent      │  │   Result     │          │
│  │   Controller │──│   Dispatcher │──│   Aggregator │          │
│  │   (主控)     │  │   (分发器)   │  │   (汇总器)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                    Common Layer                       │      │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐      │      │
│  │  │ Error      │  │ Output     │  │ Config     │      │      │
│  │  │ Handler    │  │ Formatter  │  │ Manager    │      │      │
│  │  └────────────┘  └────────────┘  └────────────┘      │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

| 模块 | 职责 | 对外接口 | 依赖 |
|------|------|---------|------|
| Phase Controller | 管理 Phase 流转、门控检查 | `execute_phase()` | Agent Dispatcher |
| Agent Dispatcher | 并行启动 Agent、收集返回 | `dispatch_agents()` | Task Tool |
| Result Aggregator | 合并结果、去重、格式化 | `aggregate_results()` | Output Formatter |
| Error Handler | 超时处理、失败标记、阈值判断 | `handle_error()` | - |
| Output Formatter | 输出格式化（JSON/Markdown） | `format_output()` | - |
| Config Manager | 读取并行配置、回滚开关 | `get_config()` | - |

### 2.3 模块边界检查

- [x] 每个模块职责单一
- [x] 模块间无循环依赖
- [x] 依赖方向正确（Controller → Dispatcher → Aggregator）

---

## 3. 接口设计

### 3.1 SKILL.md 配置接口

每个 Skill 的 SKILL.md 头部新增并行配置：

```yaml
---
name: explore
command: explore
parallel_mode: true           # 并行模式开关（回滚用）
parallel_config:
  phase_count: 3              # Phase 数量
  phases:
    - name: "信息收集"
      agent_count: 8
      subagent_type: "Explore"
      timeout: 120
    - name: "方案分析"
      agent_count: 8
      subagent_type: "general-purpose"
      timeout: 120
    - name: "汇总输出"
      agent_count: 1          # 串行
      subagent_type: null
      timeout: 60
---
```

### 3.2 Agent 输出接口

所有 Agent 必须返回统一格式的 JSON：

```json
{
  "agent_id": "agent_1",
  "agent_name": "GitHub 仓库搜索",
  "status": "success | failed | timeout",
  "execution_time_ms": 5000,
  "output": {
    // 业务数据，结构化
  },
  "error": null | {
    "type": "TimeoutError | ExecutionError",
    "message": "错误描述（≤500字符）"
  }
}
```

**输出约束**：
- `output` 字段总长度 ≤ 2000 字符
- 超长内容使用摘要

### 3.3 Phase 间数据传递接口

```json
{
  "phase_id": "phase_1",
  "phase_name": "信息收集",
  "status": "completed | partial | failed",
  "completed_agents": 8,
  "failed_agents": 0,
  "aggregated_data": {
    // 汇总后的业务数据
  },
  "pass_to_next_phase": true | false
}
```

### 3.4 错误处理接口

| 错误码 | 名称 | 触发条件 | 处理方式 |
|--------|------|---------|---------|
| E001 | AgentTimeout | 单个 Agent 超时（>120s） | 标记失败，继续其他 |
| E002 | AgentCrash | Agent 执行异常 | 标记失败，继续其他 |
| E003 | PhaseThresholdFailed | 失败 Agent > 50% | 整体任务失败 |
| E004 | GateCheckFailed | 门控检查不通过 | 停止后续 Phase |

---

## 4. 数据模型

### 4.1 并行执行状态模型

```
┌─────────────────────────────────────────────────────┐
│                  ExecutionState                      │
├─────────────────────────────────────────────────────┤
│ skill_name: string         # Skill 名称             │
│ execution_id: string       # 执行 ID                │
│ parallel_mode: boolean     # 是否并行模式           │
│ current_phase: int         # 当前 Phase             │
│ phases: Phase[]            # Phase 列表             │
│ status: ExecutionStatus    # 整体状态               │
│ started_at: datetime       # 开始时间               │
│ completed_at: datetime     # 完成时间               │
└─────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────────────────────────────────┐
│                      Phase                           │
├─────────────────────────────────────────────────────┤
│ phase_id: int              # Phase ID               │
│ phase_name: string         # Phase 名称             │
│ agent_count: int           # Agent 数量             │
│ subagent_type: string      # Agent 类型             │
│ agents: AgentResult[]      # Agent 结果列表         │
│ status: PhaseStatus        # Phase 状态             │
│ aggregated_output: object  # 汇总输出               │
└─────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────────────────────────────────┐
│                    AgentResult                       │
├─────────────────────────────────────────────────────┤
│ agent_id: string           # Agent ID               │
│ agent_name: string         # Agent 名称             │
│ status: AgentStatus        # success/failed/timeout │
│ execution_time_ms: int     # 执行时间               │
│ output: object             # 业务输出               │
│ error: ErrorInfo | null    # 错误信息               │
└─────────────────────────────────────────────────────┘
```

### 4.2 状态枚举

```typescript
enum ExecutionStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  PARTIAL = "partial",      // 部分成功
  FAILED = "failed"
}

enum PhaseStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  SKIPPED = "skipped",      // 被门控跳过
  FAILED = "failed"
}

enum AgentStatus {
  SUCCESS = "success",
  FAILED = "failed",
  TIMEOUT = "timeout"
}
```

---

## 5. 详细架构设计（10 个 Skill）

### 5.1 P0 优先级（第一批）

#### 5.1.1 `/explore` 方案探索

```
┌─────────────────────────────────────────────────────────────────┐
│                        /explore                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: 并行信息收集（8 Agent, Explore）                       │
│  ┌────────┬────────┬────────┬────────┐                         │
│  │GitHub  │Claude  │Cursor  │Gemini  │                         │
│  │仓库搜索│Code    │方案    │方案    │                         │
│  ├────────┼────────┼────────┼────────┤                         │
│  │Google  │Stack   │官方    │开源    │                         │
│  │搜索    │Overflow│文档    │案例    │                         │
│  └────────┴────────┴────────┴────────┘                         │
│         ↓ 主 Agent 汇总为候选方案列表                            │
│                                                                 │
│  Phase 2: 并行方案分析（8 Agent, general-purpose）               │
│  ┌────────┬────────┬────────┬────────┐                         │
│  │方案1   │方案2   │方案3   │方案4   │                         │
│  │分析    │分析    │分析    │分析    │                         │
│  ├────────┼────────┼────────┼────────┤                         │
│  │方案5   │方案6   │方案7   │方案8   │                         │
│  │分析    │分析    │分析    │分析    │                         │
│  └────────┴────────┴────────┴────────┘                         │
│         ↓ 主 Agent 综合对比                                     │
│                                                                 │
│  Phase 3: 汇总输出（串行）                                       │
│  └── 输出结构化对比报告 + 推荐方案                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**AC 覆盖**：AC-1.1, AC-1.2, AC-1.3

#### 5.1.2 `/test-gen` 测试生成

```
┌─────────────────────────────────────────────────────────────────┐
│                        /test-gen                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: 并行代码分析（10 Agent, Explore）                      │
│  ┌────────┬────────┬────────┬────────┬────────┐                │
│  │函数    │边界值  │异常    │依赖    │状态    │                │
│  │签名    │识别    │路径    │关系    │变化    │                │
│  ├────────┼────────┼────────┼────────┼────────┤                │
│  │输入    │并发    │性能    │安全    │业务    │                │
│  │组合    │场景    │边界    │输入    │规则    │                │
│  └────────┴────────┴────────┴────────┴────────┘                │
│         ↓ 主 Agent 汇总分析结果                                  │
│                                                                 │
│  Phase 2: 并行测试生成（10 Agent, general-purpose）              │
│  ┌────────┬────────┬────────┬────────┬────────┐                │
│  │正常    │边界值  │异常    │契约    │参数化  │                │
│  │路径    │测试    │处理    │测试    │测试    │                │
│  ├────────┼────────┼────────┼────────┼────────┤                │
│  │属性    │集成    │性能    │安全    │回归    │                │
│  │测试    │测试    │测试    │测试    │测试    │                │
│  └────────┴────────┴────────┴────────┴────────┘                │
│         ↓ 主 Agent 合并去重                                      │
│                                                                 │
│  Phase 3: 汇总输出（串行）                                       │
│  └── 输出完整测试文件（禁止 Mock）                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**AC 覆盖**：AC-2.1, AC-2.2, AC-2.3, AC-EDGE-1
**约束**：Agent 4 契约测试禁止使用 Mock

#### 5.1.3 `/qa` 测试验收

```
┌─────────────────────────────────────────────────────────────────┐
│                          /qa                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: 单元测试（4 Agent 并行, Bash）                         │
│  ┌──────────┬──────────┬──────────┬──────────┐                  │
│  │ 模块 A   │ 模块 B   │ 模块 C   │ 模块 D   │                  │
│  │ 单元测试 │ 单元测试 │ 单元测试 │ 单元测试 │                  │
│  └──────────┴──────────┴──────────┴──────────┘                  │
│         ↓ 门控：全部通过才继续                                   │
│                                                                 │
│  Layer 2: 集成测试（3 Agent 并行, Bash）                         │
│  ┌──────────────┬──────────────┬──────────────┐                 │
│  │   服务 A     │   服务 B     │   服务 C     │                 │
│  │   集成测试   │   集成测试   │   集成测试   │                 │
│  └──────────────┴──────────────┴──────────────┘                 │
│         ↓ 门控：全部通过才继续                                   │
│                                                                 │
│  Layer 3: E2E 测试（串行, 1 Agent）                              │
│  └── 按顺序执行（浏览器资源限制）                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**AC 覆盖**：AC-3.1, AC-3.2, AC-3.3, AC-ERR-4
**PRD 对齐**：Layer1=4, Layer2=3, Layer3=串行

### 5.2 P1 优先级（第二批）

#### 5.2.1 `/critique` 方案评审

- 10 Agent 并行评审不同维度
- Phase 1: 完整性/一致性/可行性/风险/遗漏/技术债务/安全性/性能/可维护性/UX
- Phase 2: 串行汇总输出评审报告

**AC 覆盖**：AC-4.1

#### 5.2.2 `/design` 架构设计

- 9 Agent 按层次并行设计
- 数据层（3）: 数据模型/数据访问层/数据迁移
- 业务层（3）: 核心逻辑/业务规则/状态管理
- 接口层（3）: API 设计/错误处理/安全机制
- Phase 2: 一致性校验

**AC 覆盖**：AC-5.1, AC-EDGE-3

#### 5.2.3 `/experts` 专家协作

- 8 必选专家 + 2 可选专家
- 可选专家启动条件：业务流程 → 业务分析师；特定领域 → 领域专家

**AC 覆盖**：AC-6.1, AC-6.2, AC-6.3, AC-EDGE-4

### 5.3 P2 优先级（第三批）

| Skill | Agent 数 | 架构 | AC 覆盖 |
|-------|---------|------|--------|
| `/security` | 8+8 | Phase1 扫描 + Phase2 修复建议 | AC-7.1 |
| `/perf` | 8+8 | Phase1 分析 + Phase2 优化建议（缓存标注） | AC-8.1, AC-EDGE-2 |
| `/overview` | 8 | 单 Phase 信息收集 | AC-9.1 |
| `/refactor` | 10+10 | Phase1 检测 + Phase2 重构建议 | AC-10.1 |

---

## 6. 设计约束

### 6.1 性能约束

| 约束项 | 标准 | 说明 |
|--------|------|------|
| 最大并发 Agent | 10 | Claude Code Task Tool 限制 |
| 单 Agent 超时 | 120s | 超时标记失败 |
| Agent 输出长度 | ≤ 2000 字符 | 控制上下文膨胀 |
| 错误信息长度 | ≤ 500 字符 | 只保留关键堆栈 |

### 6.2 项目铁律约束

| 约束 | 影响 Skill | 处理方式 |
|------|-----------|---------|
| 禁止 Mock | `/test-gen` | 契约测试连接真实服务 |
| 缓存需人工确认 | `/perf` | 缓存建议标注"需人工确认" |
| 架构对齐 | 所有 | 与 `/check`、`/run-plan` 一致 |

### 6.3 兼容性约束

- 与现有串行版本兼容（通过 `parallel_mode` 开关）
- 回滚无需修改代码

---

## 7. AC 覆盖验证

| AC-ID | 设计模块 | 验证点 |
|-------|---------|-------|
| AC-1.1 | /explore Phase 1 | 8 Agent 并行信息收集 |
| AC-1.2 | /explore Phase 2 | 8 Agent 并行方案分析 |
| AC-1.3 | /explore Phase 3 | 结构化对比报告 |
| AC-2.1 | /test-gen Phase 1 | 2-10 Agent 动态分配（按代码单元数量） |
| AC-2.2 | /test-gen Phase 2 | 2-10 Agent 动态分配（与 Phase 1 相同） |
| AC-2.3 | /test-gen Phase 3 | 合并去重输出 |
| AC-3.1 | /qa Layer 1 | 4 Agent 并行单元测试 |
| AC-3.2 | /qa Layer 2 | 3 Agent 并行集成测试 |
| AC-3.3 | /qa Layer 3 | 串行 E2E 测试 |
| AC-4.1 | /critique | 5 个评审组 Agent（每组 2 维度） |
| AC-5.1 | /design | 1+6=7 Agent（Phase 1a 串行 + Phase 1b 并行） |
| AC-6.1~6.3 | /experts | 8 必选 + 2 可选专家 |
| AC-7.1 | /security | 8 Agent 并行扫描 |
| AC-8.1 | /perf | 8 Agent 并行分析 |
| AC-9.1 | /overview | 8 Agent 并行收集 |
| AC-10.1 | /refactor | 10 Agent 并行检测 |
| AC-ERR-1~3 | Error Handler | 超时/崩溃/阈值处理 |
| AC-ERR-4 | /qa 门控 | Layer 失败停止 |
| AC-EDGE-1 | /test-gen | 禁止 Mock |
| AC-EDGE-2 | /perf | 缓存标注 |
| AC-EDGE-3 | /design | 一致性校验 |
| AC-EDGE-4 | /experts | 分歧处理 |

---

设计已完成，下一步：`/critique`（评审架构设计）
