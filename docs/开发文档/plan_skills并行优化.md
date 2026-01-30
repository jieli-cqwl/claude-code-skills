# Skills 并行优化 实施计划

## 目标

为 10 个 Skill 添加 8-10 个子 Agent 并行执行点，效率提升 2-5 倍。

## 前置文档

- AC 文档：`docs/需求文档/clarify_skills并行优化.md`
- 设计文档：`docs/设计文档/设计_skills并行优化.md`
- 调研文档：`docs/设计文档/调研_skills并行优化.md`

## 技术栈

- Skill 定义：Markdown（SKILL.md）
- 并行执行：Claude Code Task Tool
- 配置：YAML frontmatter

---

## 拆分模式

**选择**：多人协作模式

**原因**：
1. 10 个 Skill 完全独立，各自有独立的 SKILL.md 文件
2. 每个 Skill 改造互不影响，文件零重叠
3. 可以让多个开发者同时改造不同 Skill，效率最大化
4. 按优先级分 3 批（P0/P1/P2），每批内部并行

---

## Tasks 执行清单（多人协作版）

> 每个"开发者"负责一个或多个 Skill 的并行化改造

| Task | 负责人 | 描述 | 文件范围 | 依赖 | 优先级 |
|------|--------|------|---------|------|--------|
| T0 | Tech Lead | 通用模块设计确认 | 无代码，确认设计 | 无 | 前置 |
| T1 | Alice | `/explore` 并行化 | 方案探索_explore/SKILL.md | T0 | P0 |
| T2 | Bob | `/test-gen` 并行化 | 测试生成_test-gen/SKILL.md | T0 | P0 |
| T3 | Charlie | `/qa` 并行化 | 测试验收_qa/SKILL.md | T0 | P0 |
| T4 | Alice | `/critique` 并行化 | 方案评审_critique/SKILL.md | T1 | P1 |
| T5 | Bob | `/design` 并行化 | 架构设计_design/SKILL.md | T2 | P1 |
| T6 | Charlie | `/experts` 并行化 | 专家协作_experts/SKILL.md | T3 | P1 |
| T7 | Alice | `/security` 并行化 | 安全扫描_security/SKILL.md | T4 | P2 |
| T8 | Bob | `/perf` 并行化 | 性能分析_perf/SKILL.md | T5 | P2 |
| T9 | Charlie | `/overview` 并行化 | 项目概览_overview/SKILL.md | T6 | P2 |
| T10 | Alice | `/refactor` 并行化 | 重构_refactor/SKILL.md | T7 | P2 |
| T11 | Tech Lead | 集成验证 | 全部 Skill | T7,T8,T9,T10 | 后置 |

### 并行执行分组

```
第一批（串行）: T0 - Tech Lead 确认设计
    ↓
第二批（并行，P0）: T1, T2, T3 - 三个开发者同时改造核心 Skill
    ↓
第三批（并行，P1）: T4, T5, T6 - 三个开发者同时改造设计阶段 Skill
    ↓
第四批（并行，P2）: T7, T8, T9, T10 - 四个任务（Alice 做 T7+T10，Bob 做 T8，Charlie 做 T9）
    ↓
第五批（串行）: T11 - Tech Lead 集成验证
```

### 效率预估

- 串行耗时：~20 小时（10 个 Skill × 2 小时）
- 并行耗时：~6 小时（3 批并行 × 2 小时）
- **效率提升：~3.3 倍**

---

## 验收测试场景（引用 /clarify AC）

> ⚠️ **禁止重新定义 AC**：此处只能引用 /clarify 输出的 AC 表格，不能修改或新增。

**AC 来源文档**：`docs/需求文档/clarify_skills并行优化.md`

**引用的 AC 列表**：

### P0 优先级（第一批）
- AC-1.1: `/explore` Phase 1 启动 8 Agent 并行信息收集
- AC-1.2: `/explore` Phase 2 启动 8 Agent 并行方案分析
- AC-1.3: `/explore` 主 Agent 汇总输出结构化对比报告
- AC-2.1: `/test-gen` Phase 1 启动 2-10 Agent 动态分配（按代码单元数量）
- AC-2.2: `/test-gen` Phase 2 启动 2-10 Agent 动态分配（与 Phase 1 相同）
- AC-2.3: `/test-gen` 主 Agent 合并去重输出
- AC-3.1: `/qa` Layer 1 启动 4 Agent 并行单元测试
- AC-3.2: `/qa` Layer 2 启动 3 Agent 并行集成测试
- AC-3.3: `/qa` Layer 3 串行执行 E2E 测试

### P1 优先级（第二批）
- AC-4.1: `/critique` 启动 5 个评审组 Agent（每组 2 维度）
- AC-5.1: `/design` Phase 1a 串行 + Phase 1b 启动 6 Agent 并行设计（共 7 Agent）
- AC-6.1: `/experts` 启动 8 必选专家 Agent
- AC-6.2: `/experts` 业务流程时启动业务分析师
- AC-6.3: `/experts` 特定领域时启动领域专家

### P2 优先级（第三批）
- AC-7.1: `/security` 启动 8 Agent 并行扫描
- AC-8.1: `/perf` 启动 8 Agent 并行分析
- AC-9.1: `/overview` 启动 8 Agent 并行收集
- AC-10.1: `/refactor` 启动 10 Agent 并行检测

### 异常流程
- AC-ERR-1: Agent 超时标记失败，继续其他
- AC-ERR-2: Agent 崩溃标记失败，继续其他
- AC-ERR-3: 失败 > 50% 整体任务失败
- AC-ERR-4: `/qa` Layer 失败停止后续

### 边界情况
- AC-EDGE-1: `/test-gen` 禁止 Mock
- AC-EDGE-2: `/perf` 缓存标注"需人工确认"
- AC-EDGE-3: `/design` 一致性校验
- AC-EDGE-4: `/experts` 分歧处理

**完整 AC 表格见**：[clarify_skills并行优化.md](docs/需求文档/clarify_skills并行优化.md#4-验收标准)

---

## 测试设计状态（/run-plan 执行前检查）

> ⚠️ **门控要求**：测试必须在开发之前生成

- [x] AC 来源文档存在：`docs/需求文档/clarify_skills并行优化.md`
- [ ] 已执行 `/test-gen from-clarify` 生成测试
- [ ] FAILING 测试文件存在：`tests/test_skills_parallel_acceptance.py`

**特殊说明**：本项目是 SKILL.md 文件修改，验收方式通过 `/check` 验证并行架构

---

## 验收完成确认（/qa 执行后勾选）

- [ ] 所有 AC 场景验收通过
- [ ] 每个 Skill 并行模式可正常工作
- [ ] 回滚开关（parallel_mode）可正常切换
- [ ] **所有 Skill 可正常执行**

---

## Task 详情

### T0: 通用模块设计确认（Tech Lead）

- [x] T0: 通用模块设计确认 ✅ 已完成

**负责人**：Tech Lead
**依赖**：无（前置任务）
**预估**：15 分钟

**职责**：
- 确认设计文档中的接口格式
- 确认 SKILL.md 配置格式
- 确认错误处理规范

**详细步骤**：

#### Step 0.1: 确认 Agent 输出格式

确认所有 Agent 返回统一 JSON 格式：
```json
{
  "agent_id": "agent_1",
  "agent_name": "描述",
  "status": "success | failed | timeout",
  "output": { /* ≤2000字符 */ },
  "error": null | { "type": "...", "message": "≤500字符" }
}
```

#### Step 0.2: 确认 parallel_mode 配置

确认 SKILL.md frontmatter 格式：
```yaml
---
parallel_mode: true  # 回滚开关
---
```

#### Step 0.3: 确认错误处理规范

- 单 Agent 超时（>120s）：标记失败，继续其他
- 单 Agent 崩溃：标记失败，继续其他
- 失败 > 50%：整体任务失败

**验证**：确认后勾选完成

---

### T1: `/explore` 并行化（Alice）

- [x] T1: `/explore` 并行化 ✅ 已完成（含候选方案冻结机制）

**负责人**：Alice
**依赖**：T0
**预估**：2 小时
**优先级**：P0

**文件边界**：
- `方案探索_explore/SKILL.md`
- ⚠️ **禁止修改其他文件**

**AC 覆盖**：AC-1.1, AC-1.2, AC-1.3

**详细步骤**：

#### Step 1.1: 添加 parallel_mode 配置

在 SKILL.md frontmatter 添加：
```yaml
parallel_mode: true
```

#### Step 1.2: 实现 Phase 1 并行信息收集

将原有串行调研改为并行：

```markdown
## Phase 1: 并行信息收集（8 Agent）

同时启动以下 8 个调研任务（使用 Task 工具，subagent_type=Explore）：

<Task subagent_type="Explore" description="GitHub 仓库搜索">
搜索 GitHub 上相关项目，返回结构化 JSON：
{
  "agent_id": "agent_1",
  "agent_name": "GitHub 仓库搜索",
  "status": "success",
  "output": {
    "sources": [{"title": "...", "url": "...", "summary": "..."}]
  }
}
</Task>

<Task subagent_type="Explore" description="Claude Code 最佳实践">
[prompt]
</Task>

... 共 8 个 Agent
```

#### Step 1.3: 实现 Phase 2 并行方案分析

```markdown
## Phase 2: 并行方案分析（8 Agent）

主 Agent 汇总 Phase 1 结果后，启动 8 个 Agent 各分析一个候选方案：

<Task subagent_type="general-purpose" description="方案1分析">
[prompt，包含从 Phase 1 汇总的数据]
</Task>

... 共 8 个 Agent
```

#### Step 1.4: 实现 Phase 3 汇总输出

```markdown
## Phase 3: 汇总输出（串行）

主 Agent 收集所有 Phase 2 结果，综合对比，输出：
- 调研对比表（至少 5 个来源）
- 可行方案对比（2-3 个）
- 推荐方案及理由
```

**验证**：手动触发 `/explore`，确认 8 个 Agent 并行启动

---

### T2: `/test-gen` 并行化（Bob）

- [x] T2: `/test-gen` 并行化 ✅ 已完成（含 fixture 冲突检测算法）

**负责人**：Bob
**依赖**：T0
**预估**：2.5 小时
**优先级**：P0

**文件边界**：
- `测试生成_test-gen/SKILL.md`
- ⚠️ **禁止修改其他文件**

**AC 覆盖**：AC-2.1, AC-2.2, AC-2.3, AC-EDGE-1

**详细步骤**：

#### Step 2.1: 添加 parallel_mode 配置

#### Step 2.2: 实现 Phase 1 并行代码分析（10 Agent）

```markdown
## Phase 1: 并行代码分析（10 Agent，subagent_type=Explore）

<Task subagent_type="Explore" description="函数签名分析">...</Task>
<Task subagent_type="Explore" description="边界值识别">...</Task>
<Task subagent_type="Explore" description="异常路径分析">...</Task>
<Task subagent_type="Explore" description="依赖关系分析">...</Task>
<Task subagent_type="Explore" description="状态变化分析">...</Task>
<Task subagent_type="Explore" description="输入组合分析">...</Task>
<Task subagent_type="Explore" description="并发场景分析">...</Task>
<Task subagent_type="Explore" description="性能边界分析">...</Task>
<Task subagent_type="Explore" description="安全输入分析">...</Task>
<Task subagent_type="Explore" description="业务规则分析">...</Task>
```

#### Step 2.3: 实现 Phase 2 并行测试生成（10 Agent）

```markdown
## Phase 2: 并行测试生成（10 Agent，subagent_type=general-purpose）

**约束**：Agent 4（契约测试）禁止使用 Mock，必须连接真实服务

<Task subagent_type="general-purpose" description="正常路径测试">...</Task>
<Task subagent_type="general-purpose" description="边界值测试">...</Task>
<Task subagent_type="general-purpose" description="异常处理测试">...</Task>
<Task subagent_type="general-purpose" description="服务契约测试（禁止Mock）">
生成契约测试，验证接口契约，必须连接真实服务。
禁止使用：@patch, MagicMock, Mock(, mock_, vi.fn, vi.mock, jest.fn, jest.mock
</Task>
... 共 10 个
```

#### Step 2.4: 实现 Phase 3 汇总去重

主 Agent 合并所有测试，去除重复，格式化输出。

**验证**：手动触发 `/test-gen`，确认 10 个 Agent 并行启动，输出不含 Mock

---

### T3: `/qa` 并行化（Charlie）

- [x] T3: `/qa` 并行化

**负责人**：Charlie
**依赖**：T0
**预估**：2 小时
**优先级**：P0

**文件边界**：
- `测试验收_qa/SKILL.md`
- ⚠️ **禁止修改其他文件**

**AC 覆盖**：AC-3.1, AC-3.2, AC-3.3, AC-ERR-4

**PRD 对齐**：`测试验收_qa/docs/PRD_qa并行优化.md`

**详细步骤**：

#### Step 3.1: 添加 parallel_mode 配置

#### Step 3.2: 实现 Layer 1 并行单元测试（4 Agent）

```markdown
## Layer 1: 单元测试（4 Agent 并行，subagent_type=Bash）

同时启动 4 个 Agent 按模块分组执行单元测试：

<Task subagent_type="Bash" description="模块A单元测试">
pytest tests/unit/module_a/ -v
</Task>
... 共 4 个

**门控**：全部通过才进入 Layer 2
```

#### Step 3.3: 实现 Layer 2 并行集成测试（3 Agent）

```markdown
## Layer 2: 集成测试（3 Agent 并行，subagent_type=Bash）

**门控**：Layer 1 全部通过才执行

<Task subagent_type="Bash" description="服务A集成测试">
pytest tests/integration/service_a/ -v
</Task>
... 共 3 个

**门控**：全部通过才进入 Layer 3
```

#### Step 3.4: 实现 Layer 3 串行 E2E 测试

```markdown
## Layer 3: E2E 测试（串行，1 Agent）

**门控**：Layer 2 全部通过才执行
**原因**：浏览器资源限制，Claude in Chrome MCP 不支持多会话

按顺序执行 E2E 测试流程。
```

**验证**：手动触发 `/qa`，确认 Layer 门控正常工作

---

### T4-T6: P1 优先级 Skill 并行化

**格式同 T1-T3，简要说明**：

#### T4: `/critique` 并行化（Alice）
- [x] T4: `/critique` 并行化
- 10 Agent 并行评审（完整性/一致性/可行性/风险/遗漏/技术债务/安全性/性能/可维护性/UX）
- AC 覆盖：AC-4.1

#### T5: `/design` 并行化（Bob）
- [x] T5: `/design` 并行化
- 9 Agent 按层次并行（数据层3 + 业务层3 + 接口层3）
- Phase 2 一致性校验
- AC 覆盖：AC-5.1, AC-EDGE-3

#### T6: `/experts` 并行化（Charlie）
- [x] T6: `/experts` 并行化 ✅ 已完成（含量化决策检查清单）
- 8 必选专家 + 2 可选专家
- 可选启动条件：业务流程→业务分析师，特定领域→领域专家
- AC 覆盖：AC-6.1, AC-6.2, AC-6.3, AC-EDGE-4

---

### T7-T10: P2 优先级 Skill 并行化

#### T7: `/security` 并行化（Alice）
- [x] T7: `/security` 并行化
- Phase 1: 8 Agent 并行扫描（Bandit/Semgrep/Gitleaks/依赖漏洞/SQL注入/XSS/认证授权/敏感数据）
- Phase 2: 8 Agent 并行生成修复建议
- AC 覆盖：AC-7.1

#### T8: `/perf` 并行化（Bob）
- [x] T8: `/perf` 并行化
- Phase 1: 8 Agent 并行分析（CPU/内存/IO/N+1/查询优化/并发/网络/资源泄漏）
- Phase 2: 8 Agent 并行生成优化建议
- **约束**：涉及缓存必须标注"需人工确认"
- AC 覆盖：AC-8.1, AC-EDGE-2

#### T9: `/overview` 并行化（Charlie）
- [x] T9: `/overview` 并行化
- 单 Phase: 8 Agent 并行收集（目录/技术栈/依赖/核心模块/API/数据模型/配置/文档）
- AC 覆盖：AC-9.1

#### T10: `/refactor` 并行化（Alice）
- [x] T10: `/refactor` 并行化
- Phase 1: 10 Agent 并行检测（God Class/长方法/重复代码/过度耦合/接口膨胀/魔法数字/死代码/命名/复杂度/依赖循环）
- Phase 2: 10 Agent 并行生成重构建议
- AC 覆盖：AC-10.1

---

### T11: 集成验证（Tech Lead）

- [ ] T11: 集成验证（待执行）

**负责人**：Tech Lead
**依赖**：T7, T8, T9, T10（所有 Skill 改造完成后）
**预估**：1 小时

**职责**：
- 验证所有 Skill 并行模式正常工作
- 验证回滚开关正常工作
- 验证错误处理机制

**详细步骤**：

#### Step 11.1: 逐个 Skill 验证

```bash
# 验证每个 Skill 并行模式
# P0
/explore [测试项目]
/test-gen [测试代码]
/qa

# P1
/critique
/design
/experts [测试问题]

# P2
/security [测试项目]
/perf [测试代码]
/overview [测试项目]
/refactor [测试代码]
```

#### Step 11.2: 验证回滚开关

修改 `parallel_mode: false`，确认回退到串行模式。

#### Step 11.3: 验证错误处理

模拟 Agent 超时/崩溃，确认错误处理机制正常。

**验证**：所有 Skill 并行模式正常，回滚正常，错误处理正常

---

## 通用改造模板

每个 Skill 改造遵循以下模板：

```markdown
## 并行架构

**parallel_mode**: true

### Phase 1: [阶段名称]（N Agent 并行，subagent_type=X）

同时启动以下 N 个任务（使用 Task 工具）：

<Task subagent_type="X" description="Agent1 描述">
[Agent1 的详细 prompt]
返回格式：
{
  "agent_id": "agent_1",
  "agent_name": "Agent1 描述",
  "status": "success",
  "output": { /* 业务数据，≤2000字符 */ }
}
</Task>

<Task subagent_type="X" description="Agent2 描述">
[Agent2 的详细 prompt]
</Task>

... 共 N 个

**等待所有 Agent 完成后继续。**

### Phase 2: [阶段名称]（M Agent 并行 或 串行）

[根据设计文档实现]

### Phase 3: 汇总输出（串行）

主 Agent 收集所有结果，合并、去重、格式化输出。

---

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 单个 Agent 超时（>120s） | 标记失败，继续其他 |
| 单个 Agent 崩溃 | 标记失败，继续其他 |
| 失败 Agent > 50% | 整体任务失败 |
```

---

计划已完成。

**当前状态**：T0-T10 已完成（10 个 Skill 并行架构全部就位），T11 集成验证待执行。

**下一步**：`/check`（集成验证）或 `/qa`（测试验收）
