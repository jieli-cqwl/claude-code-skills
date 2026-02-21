# 调研：Claude Code SubAgent 与 Skills 协作最佳实践

**调研日期**：2026-02-21
**调研目的**：为"人机协作模式重建"方案优化提供依据，确定 Skills 与 SubAgents 的最佳协作模式

---

## 1. SubAgent 完整配置字段

SubAgent 定义文件为 Markdown + YAML frontmatter，存放于 `.claude/agents/*.md`。

### 文件位置与优先级

| 位置 | 作用域 | 优先级 |
|------|--------|--------|
| `--agents` CLI 参数（JSON） | 当前会话 | 1（最高） |
| `.claude/agents/` | 当前项目 | 2 |
| `~/.claude/agents/` | 全局所有项目 | 3 |
| 插件的 `agents/` 目录 | 插件启用范围 | 4（最低） |

同名时高优先级覆盖低优先级。

### YAML Frontmatter 完整字段

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | 是 | 唯一标识，小写字母+连字符 |
| `description` | 是 | Claude 据此判断何时委派（影响自动委派决策） |
| `tools` | 否 | 可用工具白名单（不声明=继承全部，有安全风险） |
| `disallowedTools` | 否 | 工具黑名单，从继承或指定列表中移除 |
| `model` | 否 | `sonnet` / `opus` / `haiku` / `inherit`（默认 `inherit`） |
| `permissionMode` | 否 | `default` / `acceptEdits` / `dontAsk` / `bypassPermissions` / `plan` |
| `maxTurns` | 否 | 最大轮次上限 |
| `skills` | 否 | 启动时预加载的 Skills 列表（完整内容注入上下文） |
| `memory` | 否 | 持久记忆范围：`user` / `project` / `local` |
| `mcpServers` | 否 | 可用的 MCP 服务器 |
| `hooks` | 否 | 此 SubAgent 专属的生命周期钩子 |
| `background` | 否 | `true` 表示始终后台运行（默认 `false`） |
| `isolation` | 否 | `worktree` 表示在独立 git worktree 中运行 |
| `color` | 否 | UI 背景色标识 |

### 关键机制说明

- **`skills` 字段**：声明式引用 Skills，启动时 Skill 的完整内容自动注入 SubAgent 上下文。不需要运行时 Read，不需要手动拼接 prompt
- **`memory` 字段**：SubAgent 可拥有持久记忆（`MEMORY.md`），启动时自动加载前 200 行
  - `user`：`~/.claude/agent-memory/<agent-name>/`（跨项目）
  - `project`：`.claude/agent-memory/<agent-name>/`（项目级，可版本控制）
  - `local`：`.claude/agent-memory-local/<agent-name>/`（项目级，不入版本控制）
- **`tools` 不声明的风险**：SubAgent 会继承所有工具，包括 Bash、Write 等危险权限，必须显式声明

---

## 2. Skills 与 SubAgents 的双向集成

### 方向 1：SubAgent 引用 Skills（SubAgent 驱动）

SubAgent 通过 `skills` 字段声明需要的方法论，启动时自动注入：

```yaml
# .claude/agents/pipeline-implementer.md
---
name: pipeline-implementer
skills:
  - tdd-methodology
  - code-quality
tools: Read, Write, Edit, Bash, Glob, Grep
---
你是开发者。遵循预加载 Skills 中的 TDD 流程实现功能。
```

### 方向 2：Skill 指定 SubAgent 执行（Skill 驱动）

Skill 通过 `context: fork` + `agent` 字段指定在哪个 SubAgent 身份下执行：

```yaml
# .claude/skills/架构设计_design/SKILL.md
---
name: design
description: 架构设计
context: fork
agent: pipeline-designer
---
读取需求文档，执行架构设计。
```

### Skill 额外字段（相比 SubAgent）

| 字段 | 说明 |
|------|------|
| `user-invocable` | `false` 时从 `/` 菜单隐藏（仅供 Claude 后台调用） |
| `disable-model-invocation` | `true` 时禁止 Claude 自动加载（仅手动 `/name` 触发） |
| `argument-hint` | 自动补全时显示的参数提示 |
| `context` | `fork` 时在隔离子上下文中执行 |
| `agent` | 配合 `context: fork` 指定执行用的 SubAgent |

### Skills vs SubAgents 关键区别

| 属性 | Skills | SubAgents |
|------|--------|-----------|
| 运行在主对话上下文 | 是（默认） | 否（独立上下文） |
| 有独立上下文窗口 | 否（除非 `context: fork`） | 是 |
| 可被 Claude 自动触发 | 是（根据 description） | 是（根据 description） |
| 可手动调用 | 是（`/skill-name`） | 是（通过 Task 工具） |
| 继承对话历史 | 是 | 否 |
| 可嵌套调用子代理 | 是（如果有 Task 工具） | 否（SubAgent 不能嵌套） |

---

## 3. SubAgent Prompt 设计最佳实践

### 轻量化原则（< 3k tokens）

来源：PubNub 生产实践

- 重型 SubAgent（25k+ tokens）是流水线瓶颈
- 轻量 SubAgent（< 3k tokens）实现流畅编排
- 方法论放 Skills，SubAgent 只定义角色身份和行为边界
- 类似 CPU 的 big.LITTLE 架构：关键环节用 opus，常规环节用 sonnet/haiku

### Prompt 结构公式

来源：ClaudeLog Agent Engineering

> 好的 SubAgent prompt 读起来像一份短合同："你是：[角色]，目标：[成功是什么样]，约束：[列表]，不确定时：明确说出来。"

### 好的 SubAgent 定义模式

```yaml
---
name: pipeline-checker
description: 独立代码审查员，审查代码质量和测试覆盖
tools: Read, Bash, Glob, Grep
model: sonnet
skills:
  - review-standard
  - code-quality
maxTurns: 20
---

# 角色
你是独立的代码审计员。目标是找问题，而非证明没问题。

# 边界
- 只读 + 运行测试，不修改代码
- 发现问题时描述问题，不尝试修复

# 输入输出
- 输入: docs/pipeline/{feature}/handoff_run.md
- 输出: docs/pipeline/{feature}/handoff_check.md
```

### 差的 SubAgent 定义特征

- 模糊的 description（"帮忙处理东西"）
- 不限制工具（继承全部权限 = 安全风险）
- 没有 HITL（Human-in-the-loop）检查点
- 成功标准不清晰
- 系统 prompt 过大（25k+ tokens）

### Model 选择策略

| Model | 适用场景 | 成本 |
|-------|---------|------|
| `haiku` | 轻量高频任务（文件探索、简单分析） | 最低 |
| `sonnet` | 均衡任务（代码审查、中等复杂度） | 中等 |
| `opus` | 复杂分析、深度推理、关键决策 | 最高 |

---

## 4. 知识复用的 5 种机制

### 机制 1：`skills` 字段（推荐）

SubAgent frontmatter 中声明，启动时完整内容注入。最干净的复用方式。

### 机制 2：Memory 持久记忆

SubAgent 跨会话积累经验，下次启动自动加载。适合"项目常见问题模式"类知识。

### 机制 3：Skill 目录支撑文件

```
my-skill/
├── SKILL.md           # 主指令
├── reference.md       # 详细参考（按需加载）
├── examples.md        # 使用示例
└── scripts/helper.py  # 工具脚本
```

### 机制 4：动态上下文注入

Skill 中使用 `` !`command` `` 语法在发送前执行 shell 命令注入上下文：
```yaml
## 上下文
- PR diff: !`gh pr diff`
```

### 机制 5：CLAUDE.md 继承

SubAgent 和 `context: fork` 的 Skill 都会加载 CLAUDE.md 文件链。全局规则自动生效。

---

## 5. 生产级 Pipeline 架构参考（PubNub 模式）

```
.claude/
  agents/
    orchestrator.md       # 路由分发，维护计划
    architect.md          # 设计验证，ADR 创建
    implementer.md        # 代码+测试（context: fork）
    qa-engineer.md        # 回归检查（context: fork）
  skills/
    git-utils/SKILL.md    # 可复用 git 操作
    test-suite/SKILL.md   # 测试执行模式
  hooks/
    validate-safe-ops.sh  # PreToolUse 安全验证
    log-agent-activity.sh # SubagentStop 日志
  plans/
    active-plan.md        # 当前工作契约
```

关键决策：
- Implementer 和 QA 使用 `context: fork` 防止上下文被冗长输出污染
- Hook（`SubagentStop`）提供治理而不阻塞自动化
- Plans 目录是进行中工作的单一事实来源
- Skills 是多个 Agent 共享的原子化能力

---

## 6. 对"人机协作模式重建"的优化方向

### 当前设计的问题

1. Skills 被降级为薄路由层，失去方法论沉淀的价值
2. SubAgent 文件臃肿（角色+方法论+质量标准混在一起）
3. 方法论无法跨 SubAgent 复用（TDD 写多份）
4. 未使用 `skills` 字段、`memory`、`context: fork` 等原生机制

### 建议架构

```
Skills（知识层）= 方法论、经验、标准的沉淀
    ↑ skills 字段引用
SubAgents（执行层）= 精简角色卡（< 3k tokens）
    ↑ claude -p 或 Task 工具调用
pipeline.sh（编排层）= 确定性流程控制
```

### 知识复用矩阵

| Skill | Designer | Planner | Implementer | Checker | QA | Fixer |
|-------|:--------:|:-------:|:-----------:|:-------:|:--:|:-----:|
| architecture | x | x | | | | |
| tdd-methodology | | | x | | | x |
| code-quality | x | | x | x | | x |
| review-standard | | | | x | x | |
| qa-methodology | | | | | x | |

---

## 来源

- [Create Custom Subagents - Official Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Extend Claude with Skills - Official Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Best Practices for Claude Code Subagents - PubNub](https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/)
- [Best Practices Part II: From Prompts to Pipelines - PubNub](https://www.pubnub.com/blog/best-practices-claude-code-subagents-part-two-from-prompts-to-pipelines/)
- [Claude Code Customization Guide - alexop.dev](https://alexop.dev/posts/claude-code-customization-guide-claudemd-skills-subagents/)
- [Understanding Skills, Agents, Subagents, and MCP - Colin McNamara](https://colinmcnamara.com/blog/understanding-skills-agents-and-mcp-in-claude-code)
- [VoltAgent/awesome-claude-code-subagents (100+ examples)](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [ClaudeLog Custom Agents Guide](https://claudelog.com/mechanics/custom-agents/)
- [ClaudeLog Agent Engineering](https://claudelog.com/mechanics/agent-engineering/)
