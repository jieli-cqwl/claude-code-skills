<!-- L1 模块规格 - 按需加载 -->
<!-- 来源：设计_人机协作模式重建.md 行 2264-2522 -->
<!-- 生成日期：2026-02-21 -->

# L1: 三层架构与 Skills

**本模块依赖**：无（架构定义是基础模块）
**本模块被依赖**：L1_SubAgent质量设计.md（SubAgent 引用 Skills）、L1_pipeline编排器.md（编排器拼接 Skills）、L1_配置与权限.md（配置引用架构定义）

---

## 1. 三层架构总览

```
+-------------------------------------------------------------+
|  编排层：pipeline.sh / Skill (context: fork)                    |
|  职责：确定性流程控制、触发执行                                    |
|  不关心方法论内容                                                 |
+-------------------------------------------------------------+
|  执行层：SubAgents（精简角色卡，< 3k tokens）                     |
|  职责：角色身份 + 行为边界 + 输入输出规范 + 负向约束                |
|  通过 skills 字段引用知识层                                       |
+-------------------------------------------------------------+
|  知识层：Skills（可复用方法论沉淀）                                 |
|  职责：方法论、经验、质量标准                                       |
|  跨 SubAgent 共享复用                                             |
+-------------------------------------------------------------+
```

### 为什么拆分三层

| 问题 | 旧方案（All-in-one） | 新方案（三层分离） |
|------|---------------------|------------------|
| SubAgent 臃肿 | 角色+方法论+标准混一起，25k+ tokens | < 3k tokens，方法论通过 skills 引用 |
| 方法论无法复用 | TDD 在 Implementer 和 Fixer 各写一份 | 抽取为 Skill，两个 SubAgent 共享 |
| 修改要改多处 | 更新标准需改多个 SubAgent | 修改 Skill 一处，所有引用者生效 |
| Skills 价值被稀释 | Skill 变成薄路由层 | 回归方法论本质 |

---

## 2. 知识复用矩阵

| Skill（知识层） | Designer | Planner | Implementer | Checker | QA | Fixer |
|----------------|:--------:|:-------:|:-----------:|:-------:|:--:|:-----:|
| `architecture` | **主用** | 引用 | - | - | - | - |
| `tdd-methodology` | - | - | **主用** | - | - | **主用** |
| `code-quality` | - | - | 引用 | **主用** | - | 引用 |
| `review-standard` | - | 引用 | - | **主用** | - | - |
| `qa-methodology` | - | - | - | - | **主用** | - |

**主用** = 核心方法论依据
**引用** = 需了解但非核心

---

## 3. 两种调用路径

同一份 SubAgent + 同一套 Skills，两种调用方式：

### 手动模式

```
/design Skill (context: fork, agent: pipeline-designer)
  -> Claude Code 自动加载 SubAgent + 其 skills 字段声明的所有 Skills
  -> 在隔离上下文中执行
```

### 自动模式

```
pipeline.sh
  -> claude -p "$(build_prompt pipeline-designer.md) ..." ...
  -> pipeline.sh 手动拼接 SubAgent + Skills 内容（CLI 模式不支持 skills 字段自动解析）
  -> 独立进程执行
```

### Skills 加载差异及解决方案

| 机制 | 手动模式 | 自动模式（CLI） |
|------|---------|----------------|
| SubAgent 加载 | `agent` 字段自动加载 | `$(cat agent.md)` 手动注入 |
| Skills 加载 | `skills` 字段自动注入 | pipeline.sh 解析 `skills` 行，拼接对应 Skill 内容 |
| context 隔离 | `context: fork` 原生隔离 | 每次 `claude -p` 天然独立上下文 |

### build_prompt 实现

```bash
build_prompt() {
  local agent_file="$1"
  local prompt="$(cat "${AGENTS_DIR}/${agent_file}")"
  # 解析 SubAgent 文件头部的 skills 字段
  local skills=$(sed -n '/^skills:/,/^[^ -]/p' "${AGENTS_DIR}/${agent_file}" | grep '^ *- ' | sed 's/^ *- //')
  for skill in $skills; do
    local skill_file="${SKILLS_DIR}/${skill}/SKILL.md"
    if [ -f "$skill_file" ]; then
      prompt="${prompt}\n\n$(cat "$skill_file")"
    fi
  done
  echo "$prompt"
}
```

### 模型选择在 CLI 模式下的处理

```bash
get_model() {
  local agent_file="$1"
  local model=$(grep '^model:' "${AGENTS_DIR}/${agent_file}" | awk '{print $2}')
  echo "${model:-opus}"
}
# 在 run_step 中使用 --model "$(get_model "${agent_file}")"
```

> 注意：`maxTurns` 和 `memory` 是交互式会话原生机制，CLI 模式不适用。CLI 通过 `--max-budget-usd` 和 `STEP_TIMEOUT` 控制边界。

---

## 4. Skill 改造方式

### 改造前后对比

```
改造前: /design Skill -> 内部直接定义执行逻辑（方法论+质量标准混在 Skill 中）
改造后: /design Skill -> 声明 context: fork + agent -> SubAgent 隔离执行
                                                          |
                                                  SubAgent 通过 skills 字段
                                                  引用方法论 Skill
```

Skill 文件只保留：
- YAML frontmatter（name/description/context: fork/agent）
- 简要说明（用于菜单展示）

角色定义、行为准则在 SubAgent 文件中。方法论、质量标准在 Skills 知识层中。

### 改造后 Skill 文件示例（/design）

```yaml
---
name: design
description: 架构设计。在隔离上下文中启动 pipeline-designer SubAgent。
context: fork
agent: pipeline-designer
---

# /design

架构设计入口。SubAgent pipeline-designer 将在隔离上下文中执行：
1. 读取 docs/pipeline/{feature}/handoff_clarify.md
2. 执行架构设计（方法论由 SubAgent 的 skills 字段引入）
3. 输出到 docs/pipeline/{feature}/handoff_design.md

> 如 handoff_clarify.md 不存在，请先执行 /clarify。
```

**原生机制**：
- `context: fork`：独立上下文窗口，不污染当前会话
- `agent: pipeline-designer`：加载 `.claude/agents/pipeline-designer.md`
- SubAgent 的 `skills` 字段被自动解析，Skills 内容启动时完整注入
- 无需 Bash 权限或 `claude -p`

---

## 5. Skills 知识层设计（5 个）

### 5.1 `architecture`（架构设计方法论）

**引用者**：pipeline-designer（主用）、pipeline-planner（引用）
**路径**：`~/.claude/skills/pipeline-architecture/SKILL.md`

**应包含的内容**：
- 先扫描现有代码再设计的方法论（Glob/Grep 了解项目结构）
- 多方案对比方法论（Tree of Thoughts）：关键决策必须 2-3 备选方案，对比实现复杂度/一致性/可维护性
- 接口定义完整性标准：入参（类型+校验）、出参（成功+失败）、错误码
- 模块边界设计原则："负责什么"和"不负责什么"
- 设计可追溯性：每个设计决策对应需求中的功能点
- Few-shot 对比示例

**来源**：从 L2 原文 4.1 节 Designer 的"质量标准"、"多方案对比"、"Few-shot 示例"中提取

### 5.2 `tdd-methodology`（TDD 流程）

**引用者**：pipeline-implementer（主用）、pipeline-fixer（主用）
**路径**：`~/.claude/skills/pipeline-tdd-methodology/SKILL.md`

**应包含的内容**：
- 严格 TDD 执行顺序：写测试 -> 运行确认失败（红）-> 写实现 -> 确认通过（绿）-> 重构
- 一任务一 commit 规范：`feat(Task-N): 描述`，每 commit 必须包含测试
- 阻塞标注规范：BLOCKED + 原因
- 测试先行的验证证据要求：Handoff 必须包含测试运行记录
- Few-shot 对比示例
- 修复场景 TDD 变体：每个修复附回归测试，修复前后 diff 测试结果

**来源**：从 L2 原文 4.3 节 Implementer 和 4.6 节 Fixer 中提取

### 5.3 `code-quality`（代码质量标准）

**引用者**：pipeline-checker（主用）、pipeline-implementer（引用）、pipeline-fixer（引用）
**路径**：`~/.claude/skills/pipeline-code-quality/SKILL.md`

**应包含的内容**：
- 五维检查框架：测试、Lint、类型检查、代码质量规则、AC 覆盖
- 代码质量量化规则：函数 <= 40 行、参数 <= 5 个、嵌套 <= 3 层、无空 catch、无裸 except、无硬编码
- 客观证据要求：命令输出、文件路径:行号、具体数值
- PASS/FAIL 判定标准：五维全 PASS 才是 PASS
- Few-shot 对比示例

**来源**：从 L2 原文 4.4 节 Checker 的"质量标准"中提取

### 5.4 `review-standard`（代码审查标准）

**引用者**：pipeline-checker（主用）、pipeline-planner（引用，用于 Design 评审）
**路径**：`~/.claude/skills/pipeline-review-standard/SKILL.md`

**应包含的内容**：
- 对抗性审查思维（Adversarial Mindset）：有罪推定，假设代码有漏洞
- Design 评审标准（DESIGN_OK vs DESIGN_ISSUE）：clarify 规则覆盖、接口完整性、可执行性、过度设计、数据模型
- Plan 评审标准（PLAN_OK vs PLAN_ISSUE）：文件路径验证、AC 可测性、依赖拓扑、任务粒度、设计一致性
- 评审输出格式规范：REVIEW 行 + Issues 列表
- 橡皮图章检测：禁止"看起来没问题"的模糊结论

**来源**：从 L2 原文 4.2 节 Planner 评审 和 4.4 节 Checker 对抗性审查中提取

### 5.5 `qa-methodology`（QA 验收方法论）

**引用者**：pipeline-qa（主用）
**路径**：`~/.claude/skills/pipeline-qa-methodology/SKILL.md`

**应包含的内容**：
- 验收标准唯一来源原则：clarify 是唯一标准
- 与 Check 差异化：Check 验"代码质量"，QA 验"功能是否满足需求"
- 逐条需求覆盖方法：每条规则及正例/反例逐条 PASS/FAIL + 证据
- 端到端验证方法：启动真实服务 -> 健康检查 -> 端到端测试 -> 停止服务
- 边界条件和排除项必测
- FAIL 项三要素：期望行为 + 实际行为 + 复现命令
- Few-shot 对比示例

**来源**：从 L2 原文 4.5 节 QA 的"质量标准"和"Few-shot 示例"中提取

---

## 6. Skills 完整清单（19 个）

### Pipeline 核心（9 个）

| Skill | 对应 SubAgent | 说明 |
|-------|--------------|------|
| /clarify | 无（交互式） | 保持现有，升级输出为 Rules+Examples |
| /design | pipeline-designer | `context: fork` + `agent`，引用 architecture |
| /plan | pipeline-planner | `context: fork` + `agent`，引用 architecture + review-standard |
| /run-plan | pipeline-implementer | `context: fork` + `agent`，引用 tdd-methodology + code-quality |
| /check | pipeline-checker | `context: fork` + `agent`，引用 code-quality + review-standard |
| /qa | pipeline-qa | `context: fork` + `agent`，引用 qa-methodology |
| /fix | pipeline-fixer（新增） | `context: fork` + `agent`，引用 tdd-methodology + code-quality |
| /ship | 无（需用户确认） | 保持现有 |
| /status | 无（直接读取进度文件） | 新增 |

### 独立工具（6 个，与 Pipeline 无关）

| Skill | 说明 |
|-------|------|
| /refactor | 代码重构 |
| /scan | 代码质量巡检 |
| /security | 安全漏洞扫描 |
| /perf | 性能分析诊断 |
| /worktree | Git Worktree 分支隔离 |
| /overview | 接手新项目理解全貌 |

### 领域专用（4 个，建议按项目配置）

| Skill | 说明 |
|-------|------|
| /product | 产品设计心理学分析 |
| /h5 | H5 移动端开发 |
| /mcp-builder | MCP 服务器开发 |
| /admin-ui | 后台管理 UI 开发 |

> 领域专用 Skills 建议从全局移到项目级 `.claude/skills/`。

### 已删除（5 个）

| Skill | 删除原因 |
|-------|---------|
| /gemini-critique | Pipeline Checker+QA 双重门控替代 |
| /critique | LLM 评审 LLM，质量来自角色张力非加评审层 |
| /test-gen | 被 Implementer 严格 TDD 吸收 |
| /explore | Designer 已包含多方案对比 |
| /debug | 合并到 /fix |
