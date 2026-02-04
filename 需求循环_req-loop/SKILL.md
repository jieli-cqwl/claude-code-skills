---
name: req-loop
command: req-loop
user_invocable: true
version: 1.0
description: 需求阶段自动化。执行 clarify → gemini-critique，评审有问题时提示用户补充。在提出新需求时使用，输出经评审的 AC 文档。
---

# 需求阶段自动化 (req-loop)

> **角色**：需求阶段协调者，确保需求完整且经过外部评审
> **目标**：clarify → gemini-critique，评审有问题时提示用户补充
> **核心机制**：需求交互 + 外部评审 + 用户补充循环
> **流程**：用户提出需求 → `/design-loop` 之前

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**需求循环**"或"**req-loop**"（主触发词）
- 使用命令：`/req-loop [需求描述]`
- 说"我有个新需求"、"帮我理一下需求"
- 说"帮我澄清需求并评审"
- 说"需求阶段自动化"
- 说"需求走一遍"、"澄清 + 评审"

**适用场景**：
- 有新需求需要澄清
- 希望需求经过外部评审（Gemini 交叉检查）
- 需要完整的 AC 文档

---

## 核心铁律

| 铁律 | 说明 |
|------|------|
| **必须用户交互** | clarify 环节需要用户回答问题 |
| **评审问题必须提示** | gemini-critique 发现问题必须告知用户 |
| **降级不阻塞** | gemini 不可用时跳过评审，输出警告 |

---

## 文档契约

### 输入

| 输入 | 说明 |
|------|------|
| 用户需求描述 | 口头或文字描述的需求 |

### 输出

| 输出 | 路径 | 说明 |
|------|------|------|
| **AC 文档** | `docs/需求澄清/clarify_[功能名].md` | 经评审的需求文档 |

---

## 执行流程

### Phase 0: 门控检查

```bash
# 检查 gemini CLI 可用性
which gemini >/dev/null 2>&1
GEMINI_AVAILABLE=$?
if [ $GEMINI_AVAILABLE -ne 0 ]; then
  echo "⚠️ Gemini CLI 不可用，将跳过外部评审（降级模式）"
  DEGRADE_MODE=true
else
  echo "✅ Gemini CLI 可用"
  DEGRADE_MODE=false
fi
```

---

### Phase 1: 执行 /clarify

**状态**：`CLARIFY`

```markdown
📋 执行 /clarify

与用户交互，澄清需求...

**执行方式**：
1. 读取 clarify Skill 的指令
2. 与用户交互，收集需求信息
3. 生成 AC 文档

✅ /clarify 完成，AC 文档已生成
```

**输出**：`docs/需求澄清/clarify_[功能名].md`

---

### Phase 2: 执行 /gemini-critique

**状态**：`REVIEW`

**前提**：clarify 完成 且 gemini CLI 可用

```markdown
🔎 执行 /gemini-critique clarify

使用 Gemini CLI 评审 AC 文档...

**执行命令**：
\`\`\`bash
cat "$CLARIFY_DOC" | gemini -p "
你是资深产品经理。请评审以下需求澄清文档：

## 评审维度
1. 完整性：AC 是否覆盖正常/异常/边界？
2. 清晰度：需求是否有歧义？
3. 可行性：技术实现是否可行？
4. 一致性：AC 之间是否有冲突？

## 输出格式
- 发现的问题（类型 + 描述 + 改进建议）
- 做得好的地方
- 结论：✅ 通过 / ⚠️ 需要补充 / ❌ 需要重做
" --yolo -o text
\`\`\`

**结果处理**：
- 通过 → SUCCESS
- 发现问题 → 提示用户补充
```

**降级模式**（Gemini CLI 不可用）：
```markdown
⚠️ Gemini CLI 不可用，跳过外部评审

降级原因：gemini 命令未找到
影响：跳过外部评审，AC 文档未经第三方验证

继续执行 → SUCCESS（带警告）
```

---

### Phase 3: 用户补充循环

**状态**：`USER_FIX`

当 gemini-critique 发现问题时：

```markdown
⚠️ 需求评审发现问题

## Gemini 评审意见

[显示 Gemini 的评审结果]

## 需要补充的内容

1. [问题 1] - 建议：[改进建议]
2. [问题 2] - 建议：[改进建议]

---

请补充或修改需求，然后：
- 回答补充问题，我将更新 AC 文档
- 或执行 `/req-loop` 重新评审
```

**用户补充后**：
1. 回到 CLARIFY 状态，更新 AC 文档
2. 自动流转到 REVIEW，重新执行 gemini-critique
3. 直到通过或用户选择跳过

---

### Phase 4: 输出报告

#### 成功报告（SUCCESS）

```markdown
✅ 需求阶段完成

📋 输出文档：docs/需求澄清/clarify_[功能名].md

📊 执行统计：
   - clarify 轮次：X 轮
   - 评审状态：✅ 通过（或 ⚠️ 已跳过）

🎯 下一步：执行 /design-loop（设计阶段自动化）
```

---

## 状态机

```
┌─────────────────────────────────────────────────┐
│                    状态转换图                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────┐                                    │
│  │  INIT   │                                    │
│  └────┬────┘                                    │
│       │                                         │
│       ↓                                         │
│  ┌─────────┐                                    │
│  │ CLARIFY │ ←───────────────┐                  │
│  └────┬────┘                 │                  │
│       │ AC 文档生成           │ 用户补充后       │
│       ↓                      │ 更新文档         │
│  ┌─────────┐    发现问题  ┌──────────┐          │
│  │ REVIEW  │ ───────────→│ USER_FIX │──────────┘
│  └────┬────┘             └──────────┘           │
│       │ 通过                                    │
│       ↓                                         │
│  ┌─────────┐                                    │
│  │ SUCCESS │                                    │
│  └─────────┘                                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 与其他 Skills 的关系

```
用户需求
    ↓
/req-loop（本 Skill）← clarify + gemini-critique
    ↓ AC 文档
/design-loop
    ↓ 设计文档
/plan
    ↓
/dev-loop
    ↓
/qa
```

---

## 边界约束（铁律）

| 禁止行为 | 说明 |
|---------|------|
| ❌ 跳过 clarify | 必须与用户交互澄清需求 |
| ❌ 隐藏评审问题 | 必须告知用户 Gemini 发现的问题 |
| ❌ 强制用户修改 | 用户可选择跳过评审问题 |

---

## 使用示例

```
用户：/req-loop 我要做一个用户登录功能

Claude：
  📋 req-loop 启动

  ✅ Gemini CLI 可用

  🔍 执行 /clarify...

  [与用户交互澄清需求]

  ✅ AC 文档已生成: docs/需求澄清/clarify_用户登录.md

  🔎 执行 /gemini-critique...

  ✅ 评审通过

  ✅ 需求阶段完成！

  📋 输出文档：docs/需求澄清/clarify_用户登录.md

  🎯 下一步：执行 /design-loop（设计阶段自动化）
```

---

## 完成检查清单

- [ ] clarify 与用户交互完成
- [ ] AC 文档已生成
- [ ] gemini-critique 评审完成（或降级跳过）
- [ ] 评审问题已告知用户（如有）
- [ ] 输出完成报告
