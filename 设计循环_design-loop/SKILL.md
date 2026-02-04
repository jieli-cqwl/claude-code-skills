---
name: design-loop
command: design-loop
user_invocable: true
version: 1.0
description: 设计阶段自动化。执行 explore → design → critique → gemini-critique，评审失败时自动修复重试（最多 2 次）。在 /req-loop 或 /clarify 之后、/plan 之前使用。
---

# 设计阶段自动化 (design-loop)

> **角色**：设计阶段协调者，自动化执行设计流程
> **目标**：explore → design → critique → gemini-critique，自动修复直到通过
> **核心机制**：状态机驱动 + 双重评审 + 自动修复 + 检查点恢复
> **流程**：`/req-loop` 或 `/clarify` 之后 → `/plan` 之前

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**设计循环**"或"**design-loop**"（主触发词）
- 使用命令：`/design-loop [clarify_doc_path]`
- 说"开始设计"、"自动完成设计"
- 说"帮我设计一下"、"从调研到设计走一遍"
- 说"设计阶段自动化"、"explore 到评审"
- 说"调研 + 设计 + 评审"

**适用场景**：
- AC 文档已存在，需要自动执行设计
- 希望自动修复评审发现的问题（双重评审 + 自动修复）
- 需要完整的设计阶段自动化

---

## 核心铁律

| 铁律 | 说明 |
|------|------|
| **最大重试 2 次** | critique 和 gemini-critique 失败共享重试计数，超过 2 次停止 |
| **双重评审** | Claude 自评审（critique）+ Gemini 外部评审（gemini-critique） |
| **禁止降级** | 修复失败必须报告，不能静默跳过 |
| **检查点恢复** | 中断后可从上次状态恢复 |
| **先 Claude 后 Gemini** | gemini-critique 必须在 critique 通过后执行 |

---

## 文档契约

### 输入文档（门控检查）

| 文档 | 路径 | 必须 | 检查命令 |
|------|------|------|---------|
| **AC 文档** | `docs/需求澄清/clarify_[功能名].md` | ✅ 必须 | `ls docs/需求澄清/clarify_*.md` |

### 输出

| 输出 | 路径 | 说明 |
|------|------|------|
| **调研文档** | `docs/设计文档/调研_[功能名].md` | explore 输出 |
| **设计文档** | `docs/设计文档/设计_[功能名].md` | design 输出（经评审） |
| **检查点** | `docs/.checkpoint/design_loop.json` | 中断恢复 |

---

## 执行流程

### Phase 0: 门控检查

```bash
# 1. 检查 AC 文档（支持用户指定或自动选择）
if [ -n "$USER_SPECIFIED_DOC" ]; then
  CLARIFY_DOC="$USER_SPECIFIED_DOC"
  if [ ! -f "$CLARIFY_DOC" ]; then
    echo "❌ 门控失败: 指定的 AC 文档不存在: $CLARIFY_DOC"
    exit 1
  fi
else
  # 自动检测 AC 文档
  DOC_COUNT=$(ls docs/需求澄清/clarify_*.md 2>/dev/null | wc -l)

  if [ "$DOC_COUNT" -eq 0 ]; then
    echo "❌ 门控失败: AC 文档不存在"
    echo "   修复: 先执行 /clarify 或 /req-loop"
    exit 1
  elif [ "$DOC_COUNT" -eq 1 ]; then
    CLARIFY_DOC=$(ls docs/需求澄清/clarify_*.md)
  else
    CLARIFY_DOC=$(ls -t docs/需求澄清/clarify_*.md | head -1)
    echo "⚠️ 检测到多个 AC 文档（共 $DOC_COUNT 个），自动选择最新的"
    echo "   如需指定其他文档，请使用: /design-loop [clarify_doc_path]"
  fi
fi
echo "✅ AC 文档: $CLARIFY_DOC"

# 2. 检查 gemini CLI 可用性
which gemini >/dev/null 2>&1
GEMINI_AVAILABLE=$?
if [ $GEMINI_AVAILABLE -ne 0 ]; then
  echo "⚠️ Gemini CLI 不可用，将跳过 gemini-critique（降级模式）"
  DEGRADE_MODE=true
else
  echo "✅ Gemini CLI 可用"
  DEGRADE_MODE=false
fi

# 3. 检查检查点（恢复机制）
if [ -f "docs/.checkpoint/design_loop.json" ]; then
  echo "🔄 检测到未完成的执行，自动恢复..."
  RESUME=true
else
  RESUME=false
fi
```

**门控失败处理**：
- AC 文档不存在 → **停止执行**，提示先执行 `/clarify` 或 `/req-loop`
- Gemini CLI 不可用 → **降级模式**，跳过 gemini-critique

---

### Phase 1: 执行 /explore

**状态**：`EXPLORE`

```markdown
📋 执行 /explore

调研业界最佳实践...

**执行方式**：
1. 读取 explore Skill 的指令
2. 8 Agent 并行调研
3. 生成调研文档

✅ /explore 完成，进入 /design
```

**输出**：`docs/设计文档/调研_[功能名].md`

**保存检查点**：
```json
{
  "version": 1,
  "current_state": "EXPLORE",
  "retry_count": 0,
  "clarify_doc": "docs/需求澄清/clarify_xxx.md",
  "gemini_available": true,
  "started_at": "2026-02-04T15:30:00Z"
}
```

---

### Phase 2: 执行 /design

**状态**：`DESIGN`

```markdown
📐 执行 /design

生成架构设计...

**执行方式**：
1. 读取 design Skill 的指令
2. 7 Agent 并行设计
3. 生成设计文档

✅ /design 完成，进入评审
```

**输出**：`docs/设计文档/设计_[功能名].md`

---

### Phase 3: 执行 /critique（Claude 自评审）

**状态**：`CRITIQUE`

```markdown
🔍 执行 /critique

Claude 自评审设计文档...

**评审维度**：
- 架构合理性
- 接口设计
- 数据模型
- 可扩展性

✅ /critique 通过 → 进入 /gemini-critique
❌ /critique 发现问题 → 进入自动修复
```

**失败处理**：
```
/critique 失败
    ↓
分析评审意见
    ↓
自动修复设计
    ↓
重新 /critique
    ↓
retry_count < 2？
    ├─ 是 → 继续修复循环
    └─ 否 → FAILED，输出失败报告
```

---

### Phase 4: 执行 /gemini-critique（外部评审）

**状态**：`GEMINI_CRITIQUE`

**前提**：/critique 通过 且 gemini CLI 可用

```markdown
🔎 执行 /gemini-critique design

使用 Gemini CLI 进行外部评审...

**执行命令**：
\`\`\`bash
cat "$DESIGN_DOC" | gemini -p "
你是资深架构师。请评审以下架构设计文档：

## 评审维度
1. 架构合理性：模块划分是否合理？
2. 接口设计：API 是否符合规范？
3. 数据模型：数据结构是否合理？
4. 可扩展性：是否易于扩展？
5. 安全性：是否有安全漏洞风险？

## 输出格式
- 发现的问题（类型 + 描述 + 改进建议）
- 做得好的地方
- 结论：✅ 通过 / ⚠️ 需要调整 / ❌ 需要重新设计
" --yolo -o text
\`\`\`

**结果处理**：
- 通过 → SUCCESS
- 发现问题 → 进入 GEMINI_FIX 修复循环
```

**降级模式**（Gemini CLI 不可用）：
```markdown
⚠️ Gemini CLI 不可用，跳过 gemini-critique

降级原因：gemini 命令未找到
影响：跳过外部评审，仅依赖 /critique 结果

继续执行 → SUCCESS（带警告）
```

---

### Phase 5: 自动修复（FIXING / GEMINI_FIX）

**状态**：`FIXING`（critique 失败）或 `GEMINI_FIX`（gemini-critique 失败）

#### 修复流程

```markdown
## 自动修复流程

### Step 1: 分析评审意见
解析评审输出，提取具体问题

### Step 2: 生成修复方案
针对每个问题，生成修复补丁：
- 架构问题 → 调整模块划分
- 接口问题 → 修改 API 定义
- 数据问题 → 调整数据模型
- 安全问题 → 添加安全措施

### Step 3: 应用修复
使用 Edit 工具修改设计文档

### Step 4: 更新检查点
\`\`\`json
{
  "fix_history": [
    {
      "attempt": 1,
      "source": "critique",
      "issues_count": 2,
      "fixed_count": 2,
      "actions": ["调整模块划分", "修改 API 定义"]
    }
  ]
}
\`\`\`

### Step 5: 重新评审
- FIXING 后 → 重新执行 /critique
- GEMINI_FIX 后 → 重新执行 /critique → /gemini-critique
```

---

### Phase 6: 输出报告

#### 成功报告（SUCCESS）

```markdown
✅ 设计阶段完成

📊 执行统计：
   - 总耗时：X 分钟
   - 重试次数：Y 次
   - 自动修复：Z 个问题

📋 执行阶段：
   ✅ 门控检查
   ✅ /explore
   ✅ /design
   ✅ /critique
   ✅ /gemini-critique（或 ⚠️ 已跳过）

📁 输出文档：
   - 调研文档：docs/设计文档/调研_[功能名].md
   - 设计文档：docs/设计文档/设计_[功能名].md

🎯 下一步：执行 /plan（写计划）
```

#### 失败报告（FAILED）

```markdown
❌ 设计阶段失败

📊 执行统计：
   - 总耗时：X 分钟
   - 重试次数：2 次（已达上限）

📋 未解决的问题：
   1. [问题描述]
   2. [问题描述]

💡 建议：
   - 人工检查上述问题
   - 修复后重新执行 /design-loop

📁 检查点已保存: docs/.checkpoint/design_loop.json
```

---

## 状态机

```
┌─────────────────────────────────────────────────────────────────────┐
│                            状态转换图                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┐                                                        │
│  │  INIT   │                                                        │
│  └────┬────┘                                                        │
│       │ gate_check()                                                │
│       ↓                                                             │
│  ┌─────────┐    失败                         ┌─────────┐            │
│  │  GATE   │ ───────────────────────────────→│ FAILED  │            │
│  └────┬────┘                                 └─────────┘            │
│       │ 通过                                      ↑                 │
│       ↓                                          │                 │
│  ┌─────────┐                                     │                 │
│  │ EXPLORE │                                     │                 │
│  └────┬────┘                                     │                 │
│       │ 完成                                     │                 │
│       ↓                                          │                 │
│  ┌─────────┐                                     │                 │
│  │ DESIGN  │                                     │                 │
│  └────┬────┘                                     │                 │
│       │ 完成                                     │                 │
│       ↓                                          │ 重试>=2         │
│  ┌─────────┐    失败    ┌─────────┐             │                 │
│  │CRITIQUE │ ──────────→│ FIXING  │─────────────┘                 │
│  └────┬────┘           └────┬────┘                                │
│       │ 通过                 │ 修复后                               │
│       │                     └────────→ 回到 CRITIQUE               │
│       ↓                                                             │
│  ┌───────────────┐    失败    ┌────────────┐                       │
│  │GEMINI_CRITIQUE│ ──────────→│ GEMINI_FIX │──→ 回到 CRITIQUE      │
│  └───────┬───────┘           └────────────┘     重试>=2 → FAILED   │
│          │ 通过                                                     │
│          ↓                                                          │
│     ┌─────────┐                                                     │
│     │ SUCCESS │                                                     │
│     └─────────┘                                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 状态转换规则

| 状态 | 可转换到 | 触发条件 |
|------|---------|---------|
| INIT | GATE | 启动 |
| GATE | EXPLORE | 门控通过 |
| GATE | FAILED | 门控失败（AC 不存在） |
| EXPLORE | DESIGN | explore 完成 |
| DESIGN | CRITIQUE | design 完成 |
| CRITIQUE | GEMINI_CRITIQUE | critique 通过 |
| CRITIQUE | FIXING | critique 失败且 retry < 2 |
| CRITIQUE | FAILED | critique 失败且 retry >= 2 |
| FIXING | CRITIQUE | 修复完成 |
| GEMINI_CRITIQUE | SUCCESS | gemini-critique 通过或降级模式 |
| GEMINI_CRITIQUE | GEMINI_FIX | gemini-critique 失败且 retry < 2 |
| GEMINI_CRITIQUE | FAILED | gemini-critique 失败且 retry >= 2 |
| GEMINI_FIX | CRITIQUE | 修复完成，重新从 Claude 评审开始 |

---

## 检查点机制

### 检查点文件

**路径**：`docs/.checkpoint/design_loop.json`

```json
{
  "version": 1,
  "current_state": "CRITIQUE",
  "retry_count": 1,
  "clarify_doc": "docs/需求澄清/clarify_xxx.md",
  "explore_doc": "docs/设计文档/调研_xxx.md",
  "design_doc": "docs/设计文档/设计_xxx.md",
  "gemini_available": true,
  "last_review_issues": [],
  "fix_history": [],
  "started_at": "2026-02-04T15:30:00Z",
  "updated_at": "2026-02-04T15:35:00Z"
}
```

### 恢复流程

```
启动 /design-loop
    ↓
检测检查点存在？
    ├─ 是 → 读取检查点，从 current_state 恢复
    └─ 否 → 初始化新执行
    ↓
执行完成（SUCCESS/FAILED）
    ↓
清除检查点
```

---

## 与其他 Skills 的关系

```
/clarify 或 /req-loop
    ↓ AC 文档
/design-loop（本 Skill）← explore + design + critique + gemini-critique
    ├─ 调用 /explore
    ├─ 调用 /design
    ├─ 调用 /critique
    └─ 调用 /gemini-critique
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
| ❌ 跳过 /explore 直接进入 /design | explore 是必经环节 |
| ❌ 跳过 /critique 直接进入 /gemini-critique | Claude 评审是第一道门 |
| ❌ 超过 2 次重试继续执行 | 必须停止并报告 |
| ❌ 修复失败静默跳过 | 必须记录并报告 |
| ❌ 不保存检查点 | 每次状态变更必须保存 |

---

## 使用示例

### 示例 1：正常执行

```
用户：/design-loop

Claude：
  📋 design-loop 启动

  ✅ AC 文档: docs/需求澄清/clarify_用户认证.md
  ✅ Gemini CLI 可用

  🔍 执行 /explore...
  ✅ /explore 完成

  📐 执行 /design...
  ✅ /design 完成

  🔍 执行 /critique...
  ✅ /critique 通过

  🔎 执行 /gemini-critique...
  ✅ /gemini-critique 通过

  ✅ 设计阶段完成！

  📁 输出文档：
     - 调研文档：docs/设计文档/调研_用户认证.md
     - 设计文档：docs/设计文档/设计_用户认证.md

  🎯 下一步：执行 /plan（写计划）
```

### 示例 2：自动修复

```
用户：/design-loop

Claude：
  📋 design-loop 启动

  🔍 执行 /explore...
  ✅ /explore 完成

  📐 执行 /design...
  ✅ /design 完成

  🔍 执行 /critique...
  ⚠️ /critique 发现 2 个问题

  🔧 自动修复（尝试 1/2）...
  - 问题 1：模块职责不清晰 → 已修复
  - 问题 2：API 缺少错误码 → 已修复

  🔍 重新执行 /critique...
  ✅ /critique 通过

  🔎 执行 /gemini-critique...
  ✅ /gemini-critique 通过

  ✅ 设计阶段完成！

  📊 执行统计：
     - 重试次数：1 次
     - 自动修复：2 个问题
```

---

## 完成检查清单

- [ ] AC 文档存在
- [ ] /explore 执行完成
- [ ] /design 执行完成
- [ ] /critique 通过（或重试后通过）
- [ ] /gemini-critique 通过（或降级跳过）
- [ ] 检查点已清除
- [ ] 输出完成报告
