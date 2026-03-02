---
name: new-skills
description: |
  Use when: 创建新 Skill、改进现有 Skill 质量、检查 Skill 是否符合官方标准。
user-invocable: true
---

# Skill 创建指南

> ultrathink
>
> 融合官方 Agent Skills 标准、superpowers TDD 验证法、实证提示词工程技巧。
> 详细技巧见 references/prompt-engineering.md，反模式见 references/anti-patterns.md。

---

## 1. 格式规范速查（Agent Skills 标准）

### Frontmatter 字段

| 字段 | 必填 | 说明 |
|------|:---:|------|
| `name` | Y | Skill 名称，自动决定 `/斜杠命令名` |
| `description` | Y | 触发条件描述（遵循 CSO 原则，见 §3） |
| `user-invocable` | - | `true` = 用户可通过 `/name` 调用 |
| `context` | - | `fork` = 在 SubAgent 中隔离执行 |
| `agent` | - | SubAgent 类型（需配合 `context: fork`） |
| `model` | - | 指定模型（如 `sonnet`） |
| `allowed-tools` | - | 限制可用工具列表 |
| `hooks` | - | 生命周期钩子 |
| `disable-model-invocation` | - | `true` = 纯文本 Skill，不触发模型 |
| `argument-hint` | - | 参数提示（如 `[项目路径]`） |

**注意**：`command` 字段已废弃（由 `name` 自动决定）；字段用连字符写法（`user-invocable`，非下划线）。

### 目录结构

```
skills/my-skill/
├── SKILL.md          # 主文件（<500 行）
├── references/       # 详细参考文档（按需加载）
├── scripts/          # 可执行脚本
└── assets/           # 静态资源
```

### Token 效率标准

| 加载频率 | 上限 |
|---------|------|
| 频繁加载（自动触发） | <200 words |
| 按需加载（用户调用） | <500 words |
| SKILL.md 总行数 | <500 行 |
| 详细内容 | 拆到 references/ 按需加载 |

---

## 2. Skill 类型决策树

### Task content（步骤指令，`user-invocable: true`）

用于：部署、提交、代码生成等需要执行步骤的任务。

```yaml
---
name: my-task
description: |
  一句话能力描述（≤50字）。
  Use when: 触发条件。
user-invocable: true
---
```

### Fork subagent（`context: fork` + `agent`）

用于：需要隔离执行的复杂任务，由 SubAgent 代理执行。

```yaml
---
name: my-pipeline
description: |
  一句话能力描述。
  Use when: 触发条件。前置条件：需先完成 /xxx。
context: fork
agent: pipeline-xxx
user-invocable: true
---
```

**关键**：入口 Skill 只负责"驱动"，领域知识放在知识 Skill 中由 SubAgent 的 `skills` 引用。

### Reference content（知识指南，`user-invocable: false`）

用于：约定、模式、领域知识，被其他 Skill/Agent 引用。

```yaml
---
name: my-knowledge
description: 一句话描述
user-invocable: false
---
```

**关键**：必须有 Few-shot 对比示例（好/坏成对）、检查清单、反模式列表。

---

## 3. CSO 原则（Content Summary Optimization）

> 来自 superpowers（obra/Jesse Vincent）

**核心规则**：description 只写"何时触发"，**不写**"做什么的摘要"。

**原因**：写了摘要会导致 Agent 认为已了解全部内容，跳过阅读 SKILL.md 正文。

| 写法 | 效果 |
|------|------|
| `Use when: 创建新 Skill、改进 Skill 质量` | Agent 会读全文 |
| `提供模板、技巧、清单用于创建高质量 Skill` | Agent 可能跳过全文 |

---

## 4. 核心提示词工程技巧（Top 4 精选）

### 4.1 角色身份三要素

每个 Skill 应定义清晰的角色身份：

1. **角色定位** — 你是谁（专业身份）
2. **心理驱动** — 为什么在意（使命/竞争/责任）
3. **质量锚点** — 对标谁的标准（最高水平参照）

任务类型-身份匹配速查：

| 任务类型 | 推荐身份 | 驱动方式 |
|---------|---------|---------|
| 分析型（审查、检测） | 竞争对手 | 使命感 + 对抗 |
| 创造型（设计、架构） | 资深专家 | 最高标准对标 |
| 执行型（编码、修复） | 工匠 | 质量预期 + 对抗审查 |
| 验证型（QA、测试） | 付费用户 | 零信任 + 甲方视角 |

### 4.2 约束前置

- FORBIDDEN / REQUIRED 放在文档前部（首因效应）
- 负向约束（FORBIDDEN）比正向约束更有效
- 约束用独立章节列出，不嵌入正文段落

标记强度：`FORBIDDEN` > `REQUIRED` > `SHOULD` > 建议

### 4.3 Few-shot 对比教学

好/坏示例必须成对出现，坏示例附"为什么坏"的解释：

```markdown
### 好的输出
[具体的高质量范例]

### 坏的输出
[具体的低质量范例]
（为什么坏：没有 X、缺少 Y、违反了 Z）
```

### 4.4 文档位置优化

```
┌─────────────────────────┐
│ 角色身份 + 核心约束       │ ← 首因效应：最重要放最前
├─────────────────────────┤
│ 方法论 / 参考知识         │ ← 中间区域
├─────────────────────────┤
│ Few-shot 示例            │ ← 中间偏后
├─────────────────────────┤
│ 检查清单 + 输出模板       │ ← 近因效应：执行时最先回忆
└─────────────────────────┘
```

> 完整 7 项技巧详解 → references/prompt-engineering.md

---

## 5. TDD 验证流程

> 来自 superpowers（obra/Jesse Vincent）

对 Skill 质量进行 RED-GREEN-REFACTOR 验证：

| 阶段 | 操作 | 目的 |
|------|------|------|
| **RED** | 无 Skill 时让 Agent 执行同一任务 | 记录基线失败表现 |
| **GREEN** | 加载 Skill 后重新执行 | 验证 Skill 使 Agent 达标 |
| **REFACTOR** | 审查 Agent 输出中的"合理化借口" | 堵住 Skill 漏洞 |

### 合理化借口反制

Agent 可能编造借口跳过 Skill 要求。识别方法：

1. 观察 Agent 跳过某步骤时给出的理由
2. 将该理由记录到"反合理化表格"
3. 在 Skill 中添加显式反制条款

> 详细反合理化表格方法 → references/anti-patterns.md

---

## 6. 质量自检清单（10 项核心）

创建完 Skill 后逐项检查：

- [ ] frontmatter 含 `name` + `description`？字段用连字符写法？
- [ ] description 遵循 CSO 原则（写"何时触发"不写"做什么摘要"）？
- [ ] SKILL.md <500 行？频繁加载 Skill <200 words？
- [ ] 有 Few-shot 对比示例（好/坏成对，坏的附解释）？
- [ ] 约束前置且用 FORBIDDEN/REQUIRED 格式？
- [ ] 分析/验证型 Skill 有认知偏差对抗清单？
- [ ] 输出格式有明确模板（含所有必填字段）？
- [ ] 每步可无歧义执行（非"输出分析结果"的模糊描述）？
- [ ] 跑过 TDD 基线测试（RED-GREEN-REFACTOR）？
- [ ] 角色身份含三要素（定位 + 驱动 + 锚点）？

---

## 执行流程

当用户触发 `/new-skills` 时：

1. **确认 Skill 类型**：Task / Fork subagent / Reference（见 §2 决策树）
2. **收集信息**：Skill 名称、用途、目标任务类型（分析/创造/执行/验证）
3. **选择技巧组合**：根据任务类型从 §4 选择最相关技巧，详细参考 references/
4. **生成 Skill**：使用对应类型模板 + 选中技巧 + CSO description
5. **质量自检**：对照 §6 清单逐项验证
6. **TDD 验证**：建议用户跑 RED-GREEN 基线测试（§5）
7. **输出**：展示创建的文件路径和自检结果
