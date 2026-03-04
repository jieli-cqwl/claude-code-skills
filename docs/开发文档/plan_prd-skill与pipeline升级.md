# 计划：/prd Skill + Pipeline 全链路升级 + Skill-Agent 架构重构

## Context

**问题**：
1. `/prd` 缺少产品经理思维——只输出离散 Rules，缺少业务流程和背景分析
2. 现有文档拆解（`context_gate.sh`）是事后机械拆分，语义完整性不可控
3. 能力散落三层（User Skill + Agent + Methodology Skill），修改一个方法论要在 2-3 处同步
4. Pipeline runtime 硬编码 `master.md`，无法接入新格式

**目标**：
1. 新建 `/prd` Skill 输出 `master.md + units/` 格式
2. Runtime 支持双格式（master.md 或 master.md）
3. **Skill = 完整能力**（含方法论），**Agent = 薄上下文包装**
4. 删除独立 Methodology Skills

**架构原则**：
- Skill 自包含完整能力，Agent 只管上下文（model/tools/Step Contract）
- 不为兼容旧格式打折扣
- `/prd` 做语义拆解替代 `context_gate.sh` 的脚本拆解

**实施约束**：
- 本次涵盖 Codex 侧同步优化（注意 Claude/Codex 的 model、sandbox_mode 等差异）
- 优化现有文档而非新建——文件内不保留版本号、变更日志等噪音
- 系统性维护，保持文档干净可读

---

## Codex 评审 5 条反馈处理

| # | 问题 | 验证 | 处理 |
|---|------|------|------|
| 1 | Runtime 根目录不一致 | 实锤 | Phase 2 改 runtime |
| 2 | Runtime 硬契约未接入 | 实锤 | Phase 2 改 contracts/entry/context_gate |
| 3 | QA 方法论矛盾 | 实锤 | Phase 3-5 Skill-Agent 重构根治 |
| 4 | 简单模式格式不闭环 | 部分成立 | 补充锚点格式规范 |
| 5 | 依赖重构未对齐 | 不成立 | 忽略（越界评审） |

---

## 能力吸收映射表

| Agent | User Skill | 吸收的 Methodology | Agent→Skill 迁移内容 |
|-------|-----------|-------------------|---------------------|
| pipeline-designer | design | arch-methodology | 角色身份、设计原则(简单/合适/演化)、设计思维框架、锚定偏差对抗、负向约束 |
| pipeline-planner | plan | review-standard(Design评审)、arch-methodology(部分) | 角色身份、精度意识、负向约束 |
| pipeline-implementer | run-plan | tdd-methodology、code-quality(子集) | 角色身份、TDD行为准则、提交前自检、负向约束 |
| pipeline-checker | check | code-quality、review-standard(对抗性思维+偏差检测) | 角色身份、竞争框架、认知偏差对抗、负向约束 |
| pipeline-qa | qa | qa-methodology | 角色身份、用户共情+竞争框架、偏差对抗、验证顺序、负向约束 |
| pipeline-fixer | fix | tdd-methodology(修复变体)、code-quality(子集) | 角色身份、紧迫感框架、修复三问、N>1策略、负向约束 |

**Agent 保留内容**（~25行/个）：frontmatter + Step Contract（双格式输入）+ 交付模板

---

## 全部文件变更清单

### Phase 1：/prd Skill（4 个新文件 + 后续遗留修复）

| # | 文件 | 操作 |
|---|------|------|
| 1 | `~/.claude/skills/prd/SKILL.md` | 新建 → 后续重构（输出格式改为条件引用 output-simple/output-complex，清理 /prd 引用） |
| 2 | `~/.claude/skills/prd/references/product-methodology.md` | 新建 → 后续修改（删除"与 /prd 的关系"章节） |
| 3 | `~/.claude/skills/prd/references/unit-spec.md` | 新建 → 后续修改（标题改为"与旧格式"） |
| 4 | `~/.claude/skills/prd/references/examples.md` | 新建 → **已删除**（内容拆分到 output-simple/output-complex） |
| 4a | `~/.claude/skills/prd/references/output-simple.md` | 新建（简单模式输出规范） |
| 4b | `~/.claude/skills/prd/references/output-complex.md` | 新建（复杂模式输出规范） |

### Phase 2：Runtime 双格式适配（3 个文件修改）

| # | 文件 | 改动要点 |
|---|------|---------|
| 5 | `~/.codex/bin/pipeline-runtime/entry.sh` | `cmd_start()`: 检查 master.md OR master.md |
| 6 | `~/.codex/bin/pipeline-runtime/steps/contracts.sh` | `step_required_input()`: 优先返回 master.md，回退 master.md |
| 7 | `~/.codex/bin/pipeline-runtime/steps/context_gate.sh` | `context_prepare_for_step()`: master.md 存在时跳过脚本拆解 |

### Phase 3：Skill 能力吸收（6 个 Skill 重写）

| # | 文件 | 吸收来源 |
|---|------|---------|
| 8 | `~/.claude/skills/design/SKILL.md` | 当前 SKILL + pipeline-designer 能力 + arch-methodology |
| 9 | `~/.claude/skills/plan/SKILL.md` | 当前 SKILL + pipeline-planner 能力 + review-standard(Design评审) |
| 10 | `~/.claude/skills/run-plan/SKILL.md` | 当前 SKILL + pipeline-implementer 能力 + tdd-methodology + code-quality(自检子集) |
| 11 | `~/.claude/skills/check/SKILL.md` | 当前 SKILL + pipeline-checker 能力 + code-quality + review-standard(对抗性+偏差) |
| 12 | `~/.claude/skills/qa/SKILL.md` | 当前 SKILL + pipeline-qa 能力 + qa-methodology + 双格式验收 |
| 13 | `~/.claude/skills/fix/SKILL.md` | 当前 SKILL + pipeline-fixer 能力 + tdd-methodology(修复变体) + code-quality(子集) |

### Phase 4：Agent 瘦身（6 个 Agent 重写，~25行/个）

| # | 文件 | skills 引用 |
|---|------|------------|
| 14 | `~/.claude/agents/pipeline-designer.md` | `skills: [design]` |
| 15 | `~/.claude/agents/pipeline-planner.md` | `skills: [plan]` |
| 16 | `~/.claude/agents/pipeline-implementer.md` | `skills: [run-plan]` |
| 17 | `~/.claude/agents/pipeline-checker.md` | `skills: [check]` |
| 18 | `~/.claude/agents/pipeline-qa.md` | `skills: [qa]` |
| 19 | `~/.claude/agents/pipeline-fixer.md` | `skills: [fix]` |

### Phase 5：Methodology Skills 删除（10 个目录）

| # | Claude 侧目录 | Codex 侧目录 | 已吸收到 |
|---|--------------|-------------|---------|
| 20 | `~/.claude/skills/_验收方法论_qa-methodology/` | `~/.codex/skills/_验收方法论_qa-methodology/` | qa |
| 21 | `~/.claude/skills/_架构方法论_arch-methodology/` | `~/.codex/skills/_架构方法论_arch-methodology/` | design + plan |
| 22 | `~/.claude/skills/_TDD方法论_tdd-methodology/` | `~/.codex/skills/_TDD方法论_tdd-methodology/` | run-plan + fix |
| 23 | `~/.claude/skills/_质量标准_code-quality/` | `~/.codex/skills/_质量标准_code-quality/` | check + run-plan + fix |
| 24 | `~/.claude/skills/_评审标准_review-standard/` | `~/.codex/skills/_评审标准_review-standard/` | plan + check |

### Phase 6：下游适配（2 个文件修改）

| # | 文件 | 改动 |
|---|------|------|
| 25 | `~/.claude/skills/auto-dev/SKILL.md` | 前置条件双格式 + /prd 入口 |
| 26 | `~/.claude/skills/run-plan-parallel/SKILL.md` | 输入说明更新 |

### Phase 7：Codex 同步

| # | 操作 | 平台差异处理 |
|---|------|-------------|
| 27 | 同步 6 个 Agent .md 到 `~/.codex/agents/` | model 改为 `gpt-5.3-codex`，sandbox_mode 保留 `workspace-write` |
| 28 | 同步新建/重写的 Skills 到 `~/.codex/skills/` | 内容相同，无平台差异 |
| 29 | 删除 Codex 侧 5 个 Methodology Skill 目录 | 与 Claude 侧同步删除 |
| 30 | 清理 Codex 侧 Agent 中的旧 Methodology 引用 | 与 Claude 侧保持一致 |
| 31 | 清理设计文档和学习笔记中的旧引用 | `L1_三层架构与Skills.md`、`skills 学习笔记.md` |

### Phase 8：Bug 修复 — Agent `skills:` 字段

在 6 个 Claude Agent + 6 个 Codex Agent 的 frontmatter 中添加 `skills:` 字段。

| Agent | `skills:` 值 |
|-------|-------------|
| pipeline-designer | `[design]` |
| pipeline-planner | `[plan]` |
| pipeline-implementer | `[run-plan]` |
| pipeline-checker | `[check]` |
| pipeline-qa | `[qa]` |
| pipeline-fixer | `[fix]` |

### Phase 9：输出格式模板提取

为 4 个 Skill 创建 `references/output-templates.md`，将多套输出模板从 SKILL.md 提取到独立文件。

| Skill | 模板数 | 提取文件 |
|-------|--------|---------|
| design | 2（精简版+完整版） | `references/output-templates.md` |
| plan | 2（Plan输出+Design评审输出） | `references/output-templates.md` |
| run-plan | 2（执行输出+Plan评审输出） | `references/output-templates.md` |
| qa | 2（master.md格式+prd格式） | `references/output-templates.md` |

不提取：check（单一输出格式）、fix（单一输出格式）。

### Phase 10：删除 legacy + product Skills

**删除目录（4 个）**：

| 目录 | 侧 |
|------|-----|
| `~/.claude/skills/prd/` | Claude |
| `~/.claude/skills/产品设计_product/` | Claude |
| `~/.codex/skills/prd/` | Codex |
| `~/.codex/skills/产品设计_product/` | Codex |

**引用更新（统一到 `/prd`）**：8 个 SKILL.md 文件中的命令引用已标准化。保留 `master.md` 文件名引用（双格式向后兼容）。

---

## 简单模式格式规范（修复 Codex Issue 4）

简单需求（≤3 规则）内联在 master.md 时，使用与 UNIT 相同的规则锚点：

```markdown
## 功能规则

### 规则 1：[标题]
**描述**: [规则描述]
- 正例：[输入] → [期望输出]
- 反例：[输入] → [期望错误]
- 边界：[边界条件] → [期望行为]
```

---

## 执行状态

| Phase | 状态 | 说明 |
|-------|------|------|
| Phase 1 | ✅ 完成 | /prd Skill 4 个新文件已创建；遗留修复完成：删除 examples.md，新建 output-simple.md + output-complex.md（按模式拆分输出规范），SKILL.md 输出格式重构为条件引用，product-methodology.md 删除 /prd 关系章节，unit-spec.md 标题修正，Codex 同步完成 |
| Phase 2 | ✅ 完成 | Runtime 3 个文件已修改，双格式适配完成 |
| Phase 3 | ✅ 完成 | 6 个 Skill 已吸收方法论重写 |
| Phase 4 | ✅ 完成 | 6 Agent 已瘦身至 ~25 行 |
| Phase 5 | ✅ 完成 | 10 个 Methodology Skill 目录已删除（Claude + Codex 双侧） |
| Phase 6 | ✅ 完成 | auto-dev + run-plan-parallel 已适配 |
| Phase 7 | ✅ 完成 | Codex Agent 同步（含 skills 字段）+ 8 个 Codex Skills + 4 个 references 同步 + 设计文档/学习笔记清理 |
| Phase 8 | ✅ 完成 | 12 个 Agent 文件（Claude 6 + Codex 6）添加 `skills:` 字段 |
| Phase 9 | ✅ 完成 | 4 个 Skill 的输出模板提取到 `references/output-templates.md` + Codex 同步 |
| Phase 10 | ✅ 完成 | 4 个目录删除（prd + product 双侧）+ 8 个 Skill 引用更新 `/prd` → `/prd` + Codex 同步 |

---

## 验证方案

| # | 验证项 | 方法 |
|---|--------|------|
| 1 | /prd 简单需求 | 运行 `/prd` → 确认 master.md 含内联规则 |
| 2 | /prd 复杂需求 | 运行 `/prd` → 确认 master.md + units/ 完整 |
| 3 | Runtime 双格式 | `pipeline.sh start` 分别用两种格式测试 |
| 4 | Agent 瘦身 | 每个 Agent ≤30行，含 `skills:` 字段 |
| 5 | Skill 完整性 | 每个 Skill 包含：角色+方法论+工作流+约束+输出格式 |
| 6 | 全链路新格式 | `/prd` → `/design` → 确认正常读取 master.md |
| 7 | 全链路旧格式 | 旧 `master.md` → `/design` → 确认向后兼容 |
| 8 | QA 双格式 | `/prd` → ... → `/qa` → 确认逐 Unit 验证 |
