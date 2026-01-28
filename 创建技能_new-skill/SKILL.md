---
name: new-skill
command: new-skill
user_invocable: true
description: 技能创作。用 TDD 方法创建和验证新的 Skills，确保 AI 代理在有技能时遵守规则。适用于发现需要标准化的重复模式或问题。
---

> **角色**：技能萃取师，将隐性知识显性化
> **目标**：创建高效可复用的 Skill，让 AI 遵守规则
> **原则**：TDD 验证、迭代优化、场景覆盖
> **流程**：发现重复模式时触发

# 技能创作 (Writing Skills)

> **来源**: 基于 [obra/superpowers](https://github.com/obra/superpowers) 的 writing-skills 方法论

---

## 核心理念

**"TDD 不只适用于代码，也适用于技能/文档"**

传统方式：写文档 → 希望 AI 遵守 → 发现不遵守 → 改文档
TDD 方式：设计测试 → 验证 AI 违反 → 写文档 → 验证 AI 遵守

---

## TDD 与 Skill 创建的映射

| TDD 概念 | Skill 创建对应 |
|---------|---------------|
| 测试用例 | 压力场景 + 子代理测试 |
| 生产代码 | SKILL.md 文档 |
| 测试失败 (RED) | 无技能时 AI 违反规则 |
| 测试通过 (GREEN) | 有技能时 AI 遵守规则 |
| 重构 | 插入漏洞、保持遵守 |

---

## 何时使用

| 场景 | 使用 |
|------|------|
| 发现 AI 重复犯同样错误 | ✅ 创建技能约束 |
| 有特定领域的最佳实践 | ✅ 编纂为技能 |
| 需要标准化的工作流程 | ✅ 创建流程技能 |
| 一次性的特殊情况 | ❌ 直接指导 |
| 通用的基础知识 | ❌ 不需要技能 |

---

## Skill 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **Technique** | 具体的步骤方法 | systematic-debugging |
| **Pattern** | 思考方式和原则 | test-driven-development |
| **Workflow** | 工作流程编排 | subagent-driven-dev |
| **Reference** | API 或文档参考 | h5-interaction |

---

## 执行流程

```
Phase 1: 识别需求
    ↓
Phase 2: 设计压力测试
    ↓
Phase 3: 运行 RED 测试（验证 AI 违反）
    ↓
Phase 4: 编写 SKILL.md
    ↓
Phase 5: 运行 GREEN 测试（验证 AI 遵守）
    ↓
Phase 6: 迭代完善
```

### Phase 1: 识别需求

**问自己**：
- AI 经常在什么地方犯错？
- 有什么规则需要反复强调？
- 有什么流程需要标准化？

**输出**：
```markdown
## Skill 需求描述

### 问题模式
AI 在 [场景] 时经常 [错误行为]，而正确的做法应该是 [正确行为]。

### 触发条件
当 [条件] 时，应该使用这个 Skill。

### 预期效果
使用 Skill 后，AI 应该 [正确行为]，而不是 [错误行为]。
```

### Phase 2: 设计压力测试

创建会让 AI 违反规则的场景：

```markdown
## 压力测试场景

### 场景 1: [名称]
**输入**: [用户请求]
**期望的错误行为**: [AI 可能的错误反应]
**期望的正确行为**: [AI 应该的正确反应]

### 场景 2: [名称]
...
```

**好的压力测试特征**：
- 场景真实（来自实际遇到的问题）
- 诱惑明显（AI 很容易犯错）
- 判定清晰（对错容易判断）

### Phase 3: 运行 RED 测试

**目的**：验证在没有 Skill 的情况下，AI 确实会犯错。

**方法**：
1. 启动新的对话（无 Skill 加载）
2. 给出压力测试场景
3. 观察 AI 的反应
4. 记录违反规则的行为

```markdown
## RED 测试结果

### 场景 1
- **AI 反应**: [实际反应]
- **是否违反**: ✅ 是 / ❌ 否
- **违反方式**: [具体描述]

### 场景 2
- **AI 反应**: [实际反应]
- **是否违反**: ✅ 是 / ❌ 否
- **违反方式**: [具体描述]
```

如果 AI 没有违反 → 这个 Skill 可能不需要，或场景设计不够有挑战性。

### Phase 4: 编写 SKILL.md

基于观察到的违反模式，编写 SKILL.md：

**⚠️ 必须包含 YAML Front Matter**（否则命令无法正确显示）：

```yaml
---
name: skill-name           # Skill 标识符
command: skill-command     # 触发命令（不含 /）
user_invocable: true       # 用户可通过命令触发
description: 描述何时使用   # 触发条件，非功能描述
---
```

**内容关键要素**：
1. **针对性**：直接解决观察到的问题
2. **具体性**：提供具体的做法，不是抽象原则
3. **可验证**：有明确的通过/不通过标准
4. **有说服力**：解释为什么这样做

**必须参照** `reference/skill-template.md` 模板结构。

### Phase 5: 运行 GREEN 测试

**目的**：验证有了 Skill 后，AI 能正确行为。

**方法**：
1. 启动新的对话，加载新创建的 Skill
2. 给出相同的压力测试场景
3. 观察 AI 的反应
4. 验证是否正确行为

```markdown
## GREEN 测试结果

### 场景 1
- **AI 反应**: [实际反应]
- **是否正确**: ✅ 是 / ❌ 否
- **正确表现**: [具体描述]

### 场景 2
- **AI 反应**: [实际反应]
- **是否正确**: ✅ 是 / ❌ 否
- **正确表现**: [具体描述]
```

如果 AI 仍然违反 → 回到 Phase 4，加强 SKILL.md。

### Phase 6: 迭代完善

1. **插入漏洞**：设计更刁钻的场景，测试 Skill 的边界
2. **加强防护**：针对发现的漏洞，完善 SKILL.md
3. **重复测试**：直到 Skill 足够稳健

---

## SKILL.md 结构规范

详见 `reference/skill-template.md`，关键要素：

```yaml
---
name: skill-name-with-hyphens      # 只用字母、数字、连字符
command: skill-command              # 触发命令
user_invocable: true/false          # 是否用户可调用
description: 第三人称描述何时使用   # < 1024 字符
---
```

**description 写法**：
- ❌ 错误："使用这个技能来实现 TDD"（说的是做什么）
- ✅ 正确："在编写任何功能或 bug 修复前使用，确保测试先行"（说的是何时用）

**原因**：description 决定 AI 何时自动触发技能，必须描述触发条件。

---

## 目录结构规范

```
.claude/skills/
├── skill-name/                   # 目录名 = skill name
│   ├── SKILL.md                  # 必须：主文档
│   ├── reference/                # 可选：参考资料
│   │   └── xxx.md
│   ├── prompts/                  # 可选：子代理提示词
│   │   └── xxx.md
│   └── templates/                # 可选：模板文件
│       └── xxx.md
```

---

## 危险信号

- Skill 过于笼统，什么都覆盖
- 没有经过 RED 测试就写 SKILL.md
- GREEN 测试通过但没有迭代完善
- description 描述的是"做什么"而非"何时用"
- Skill 内容与现有规范（.claude/rules/）冲突

---

## 与其他 Skills 的关系

```
发现问题模式
    ↓
/new-skill  ← 本技能
    ↓
新 Skill 创建完成
    ↓
更新 STANDARD.md
```

---

## 完成检查清单

- [ ] 需求已明确（问题模式、触发条件、预期效果）
- [ ] 压力测试已设计
- [ ] RED 测试已通过（AI 确实违反）
- [ ] SKILL.md 已编写
- [ ] **YAML Front Matter 完整**（name、command、user_invocable、description）
- [ ] GREEN 测试已通过（AI 正确行为）
- [ ] 至少迭代一次（插入漏洞、加强防护）
- [ ] STANDARD.md 已更新
