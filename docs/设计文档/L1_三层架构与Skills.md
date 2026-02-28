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
|  知识层：方法论（内置于业务 Skill）                                   |
|  职责：方法论、经验、质量标准                                       |
|  直接内置于业务 Skill，不再作为独立 Skill 存在                       |
+-------------------------------------------------------------+
```

> **架构演进说明**：原设计中知识层有 5 个独立 Methodology Skill，经实践验证后已合并到业务 Skill 中。方法论不再独立存在，而是直接内置于对应的业务 Skill（详见第 2 节和第 5 节）。

### 为什么拆分三层（及后续演进）

| 问题 | 旧方案（All-in-one） | 三层分离（初版） | 当前方案（方法论内置） |
|------|---------------------|------------------|---------------------|
| SubAgent 臃肿 | 角色+方法论+标准混一起，25k+ tokens | < 3k tokens，方法论通过 skills 引用 | 同左，方法论内置于业务 Skill |
| 方法论无法复用 | TDD 在 Implementer 和 Fixer 各写一份 | 抽取为独立 Skill，跨 SubAgent 共享 | 内置到各业务 Skill，消除间接引用层 |
| 修改要改多处 | 更新标准需改多个 SubAgent | 修改 Skill 一处，所有引用者生效 | 方法论与业务 Skill 一体维护 |
| Skills 价值被稀释 | Skill 变成薄路由层 | 回归方法论本质 | 业务 Skill 自包含方法论 |

---

## 2. 方法论内置说明

原架构中知识层有 5 个独立 Methodology Skill（`arch-methodology`、`tdd-methodology`、`code-quality`、`review-standard`、`qa-methodology`），已全部删除。方法论现在直接内置于对应的业务 Skill 中，不再作为独立 Skill 存在。

### 方法论吸收关系

| 原 Methodology Skill | 吸收到的业务 Skill |
|----------------------|-------------------|
| `arch-methodology` | 架构设计_design + 写计划_plan |
| `tdd-methodology` | 执行计划_run-plan + 修复_fix |
| `code-quality` | 开发检查_check + 执行计划_run-plan + 修复_fix |
| `review-standard` | 写计划_plan + 开发检查_check |
| `qa-methodology` | 测试验收_qa |

**优势**：消除了独立方法论 Skill 的间接引用层，每个业务 Skill 自包含所需的方法论知识，减少加载开销和上下文碎片化。

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
1. 读取 docs/pipeline/{feature}/master.md
2. 执行架构设计（方法论直接内置于业务 Skill 中）
3. 输出到 docs/pipeline/{feature}/handoff_design.md

> 如 master.md 不存在，请先执行 /prd。

注：方法论知识直接内置在业务 Skill 中，不再通过独立 methodology Skill 引用。
```

**原生机制**：
- `context: fork`：独立上下文窗口，不污染当前会话
- `agent: pipeline-designer`：加载 `.claude/agents/pipeline-designer.md`
- SubAgent 的 `skills` 字段被自动解析，Skills 内容启动时完整注入
- 无需 Bash 权限或 `claude -p`

---

## 5. 方法论内置架构（替代原独立知识层）

原架构中此处定义了 5 个独立的 Methodology Skill（`architecture`、`tdd-methodology`、`code-quality`、`review-standard`、`qa-methodology`），作为知识层被 SubAgent 通过 `skills` 字段引用。

**现状**：这 5 个独立 Methodology Skill 已全部删除，方法论内容直接内置到对应的业务 Skill 中。

### 变更原因

- **减少间接层**：独立方法论 Skill 增加了加载和解析开销，实际上每个方法论只被 1-2 个业务 Skill 使用
- **降低维护成本**：方法论与业务 Skill 紧耦合，分开维护反而容易不一致
- **简化架构**：三层架构中的知识层现在合并到执行层，变为更扁平的结构

### 方法论内容去向

| 原 Methodology Skill | 核心内容 | 内置到的业务 Skill |
|----------------------|---------|-------------------|
| `architecture`（架构设计方法论） | 多方案对比、接口定义、模块边界 | 架构设计_design、写计划_plan |
| `tdd-methodology`（TDD 流程） | 红绿重构、一任务一 commit、阻塞标注 | 执行计划_run-plan、修复_fix |
| `code-quality`（代码质量标准） | 五维检查、量化规则、PASS/FAIL 判定 | 开发检查_check、执行计划_run-plan、修复_fix |
| `review-standard`（代码审查标准） | 对抗性审查、Design/Plan 评审标准 | 写计划_plan、开发检查_check |
| `qa-methodology`（QA 验收方法论） | 验收标准来源、端到端验证、FAIL 三要素 | 测试验收_qa |

---

## 6. Skills 完整清单

### Pipeline 核心（10 个）

| Skill | 对应 SubAgent | 说明 |
|-------|--------------|------|
| /prd | 无（交互式） | 需求澄清，升级输出为 Rules+Examples |
| /prd | 无（交互式） | 产品需求文档化，输出 master.md + units/ 格式（替代 context_gate.sh 的机械拆解） |
| /design | pipeline-designer | `context: fork` + `agent`，架构设计方法论内置 |
| /plan | pipeline-planner | `context: fork` + `agent`，架构方法论 + 审查标准内置 |
| /run-plan | pipeline-implementer | `context: fork` + `agent`，TDD + 代码质量标准内置 |
| /check | pipeline-checker | `context: fork` + `agent`，代码质量 + 审查标准内置 |
| /qa | pipeline-qa | `context: fork` + `agent`，QA 验收方法论内置 |
| /fix | pipeline-fixer | `context: fork` + `agent`，TDD + 代码质量标准内置 |
| /ship | 无（需用户确认） | 代码交付 |
| /status | 无（直接读取进度文件） | 进度查询 |

> 方法论不再通过独立 Skill 引用，而是直接内置在各业务 Skill 中（参见第 5 节）。

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

### 已删除（10 个）

| Skill | 删除原因 |
|-------|---------|
| /gemini-critique | Pipeline Checker+QA 双重门控替代 |
| /critique | LLM 评审 LLM，质量来自角色张力非加评审层 |
| /test-gen | 被 Implementer 严格 TDD 吸收 |
| /explore | Designer 已包含多方案对比 |
| /debug | 合并到 /fix |
| /architecture（Methodology） | 内置到 架构设计_design + 写计划_plan |
| /tdd-methodology（Methodology） | 内置到 执行计划_run-plan + 修复_fix |
| /code-quality（Methodology） | 内置到 开发检查_check + 执行计划_run-plan + 修复_fix |
| /review-standard（Methodology） | 内置到 写计划_plan + 开发检查_check |
| /qa-methodology（Methodology） | 内置到 测试验收_qa |
