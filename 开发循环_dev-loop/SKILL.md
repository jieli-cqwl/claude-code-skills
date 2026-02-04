---
name: dev-loop
command: dev-loop
user_invocable: true
version: 1.0
description: 开发阶段自动化。自动执行 run-plan → check → gemini-review 的完整循环，评审失败时自动修复重试（最多 3 次）。在 /plan 之后、/qa 之前使用。
---

# 开发阶段自动化 (dev-loop)

> **角色**：开发阶段协调者，自动化执行开发流程
> **目标**：run-plan → check → gemini-review，自动修复直到通过
> **核心机制**：状态机驱动 + 分层自动修复 + 检查点恢复
> **流程**：`/plan` 之后 → `/qa` 之前

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**开发循环**"或"**dev-loop**"（主触发词）
- 使用命令：`/dev-loop [plan_doc_path]`
- 说"开始开发"、"自动完成开发"
- 说"帮我把代码写完"、"按计划开发"
- 说"开发阶段自动化"、"执行计划并检查"
- 说"开发 + 检查 + 评审"

**适用场景**：
- plan 文档已存在，需要自动执行开发
- 希望自动修复 check/review 发现的问题（自动修复 + Gemini 审查）
- 需要完整的开发阶段自动化

---

## 核心铁律

| 铁律 | 说明 |
|------|------|
| **最大重试 3 次** | check 和 gemini-review 失败共享重试计数，超过 3 次停止 |
| **禁止降级** | 修复失败必须报告，不能静默跳过 |
| **检查点恢复** | 中断后可从上次状态恢复 |
| **先 check 后 review** | gemini-review 必须在 check 通过后执行 |

---

## 文档契约

### 输入文档（门控检查）

| 文档 | 路径 | 必须 | 检查命令 |
|------|------|------|---------|
| **Plan 文档** | `docs/开发文档/plan_[功能名].md` | ✅ 必须 | `ls docs/开发文档/plan_*.md` |

### 输出

| 输出 | 说明 |
|------|------|
| **成功报告** | 执行统计、重试次数、下一步建议 |
| **失败报告** | 未解决问题列表、人工介入提示 |
| **检查点** | `docs/.checkpoint/dev_loop.json` |

---

## 执行流程

### Phase 0: 门控检查

```bash
# 1. 检查 plan 文档（支持用户指定或自动选择）
if [ -n "$USER_SPECIFIED_PLAN" ]; then
  # 用户通过 /dev-loop [path] 指定了 plan 文档
  PLAN_DOC="$USER_SPECIFIED_PLAN"
  if [ ! -f "$PLAN_DOC" ]; then
    echo "❌ 门控失败: 指定的 Plan 文档不存在: $PLAN_DOC"
    exit 1
  fi
else
  # 自动检测 plan 文档
  PLAN_COUNT=$(ls docs/开发文档/plan_*.md 2>/dev/null | wc -l)

  if [ "$PLAN_COUNT" -eq 0 ]; then
    echo "❌ 门控失败: Plan 文档不存在"
    echo "   修复: 先执行 /plan 生成计划文档"
    exit 1
  elif [ "$PLAN_COUNT" -eq 1 ]; then
    # 仅有一个，直接使用
    PLAN_DOC=$(ls docs/开发文档/plan_*.md)
  else
    # 有多个，按修改时间取最新的
    PLAN_DOC=$(ls -t docs/开发文档/plan_*.md | head -1)
    echo "⚠️ 检测到多个 Plan 文档（共 $PLAN_COUNT 个），自动选择最新的"
    echo "   如需指定其他文档，请使用: /dev-loop [plan_doc_path]"
  fi
fi
echo "✅ Plan 文档: $PLAN_DOC"

# 2. 检查 gemini CLI 可用性
which gemini >/dev/null 2>&1
GEMINI_AVAILABLE=$?
if [ $GEMINI_AVAILABLE -ne 0 ]; then
  echo "⚠️ Gemini CLI 不可用，将跳过 gemini-review（降级模式）"
  DEGRADE_MODE=true
else
  echo "✅ Gemini CLI 可用"
  DEGRADE_MODE=false
fi

# 3. 检查检查点（恢复机制）
if [ -f "docs/.checkpoint/dev_loop.json" ]; then
  echo "🔄 检测到未完成的执行，自动恢复..."
  RESUME=true
else
  RESUME=false
fi
```

**门控失败处理**：
- Plan 文档不存在 → **停止执行**，提示先执行 `/plan`
- Gemini CLI 不可用 → **降级模式**，跳过 gemini-review（AC-11）

---

### Phase 1: 执行 /run-plan

**状态**：`RUN_PLAN`

```markdown
📋 执行 /run-plan

读取 plan 文档，执行开发任务...

**执行方式**：
1. 读取 run-plan Skill 的指令
2. 按 plan 文档中的 Task 顺序执行
3. 每个 Task 完成后保存检查点

✅ /run-plan 完成，进入 /check
```

**保存检查点**：
```json
{
  "version": 1,
  "current_state": "RUN_PLAN",
  "retry_count": 0,
  "plan_doc": "docs/开发文档/plan_xxx.md",
  "gemini_available": true,
  "started_at": "2026-02-04T15:30:00Z"
}
```

---

### Phase 2: 执行 /check

**状态**：`CHECK`

```markdown
🔍 执行 /check

运行代码检查（lint、类型、测试）...

**检查项**：
- Lint 检查（ruff/eslint）
- 类型检查（mypy/tsc）
- 单元测试（pytest/vitest）
- 集成测试

✅ /check 通过 → 进入 /gemini-review
❌ /check 失败 → 进入自动修复
```

**失败处理**：
```
/check 失败
    ↓
分析错误类型（L1-L4）
    ↓
执行自动修复
    ↓
重新 /check
    ↓
retry_count < 3？
    ├─ 是 → 继续修复循环
    └─ 否 → FAILED，输出失败报告
```

---

### Phase 3: 自动修复（FIXING）

**状态**：`FIXING`（check 失败）或 `REVIEW_FIX`（review 失败）

#### 错误分类

| 类型 | 识别规则 | 修复策略 | 成功率 |
|------|---------|---------|--------|
| **L1_LINT** | 包含 "ruff"/"eslint"/"lint"/"format" | `ruff check --fix . && ruff format .` | >95% |
| **L2_TYPE** | 包含 "mypy"/"type"/"annotation"/"TypeScript" | LLM 分析 + 添加类型注解 | ~80% |
| **L3_TEST** | 包含 "pytest"/"test"/"assert"/"FAILED" | LLM 分析失败原因 + 修复代码 | ~60% |
| **L4_REVIEW** | 来自 gemini-review 输出 | LLM 逐条分析评审意见 + 修复 | ~70% |

#### 修复流程

```markdown
## 自动修复流程

### Step 1: 错误分类
分析错误信息，确定错误类型（L1-L4）

### Step 2: 按类型修复

**L1 Lint 错误**：
\`\`\`bash
# 自动修复 lint 和格式问题
ruff check --fix .
ruff format .
# 或 JavaScript/TypeScript
npm run lint -- --fix
\`\`\`

**L2 类型错误**：
\`\`\`markdown
分析错误信息：
- 缺少返回类型 → 添加返回类型注解
- 参数类型不匹配 → 修正参数类型
- 导入类型缺失 → 添加类型导入
\`\`\`

**L3 测试失败**：
\`\`\`markdown
分析测试失败原因：
- 断言失败 → 检查期望值和实际值
- 异常未捕获 → 添加异常处理
- Mock 问题 → 检查 Mock 配置（注意：禁止 Mock 内部服务）
\`\`\`

**L4 Review 问题**：
\`\`\`markdown
逐条分析 gemini-review 的评审意见：
- 代码风格问题 → 按建议修改
- 潜在 Bug → 修复逻辑
- 性能问题 → 优化代码
- 安全问题 → 修复漏洞
\`\`\`

### Step 3: 应用修复
使用 Edit 工具应用修复补丁

### Step 4: 更新检查点
\`\`\`json
{
  "fix_history": [
    {
      "attempt": 1,
      "error_type": "L1_LINT",
      "fixed_count": 3,
      "remaining_count": 0,
      "actions": ["ruff --fix backend/"]
    }
  ]
}
\`\`\`

### Step 5: 重新检查
修复完成后，重新执行 /check
```

---

### Phase 4: 执行 /gemini-review

**状态**：`REVIEW`

**前提**：/check 通过 且 gemini CLI 可用

```markdown
🔎 执行 /gemini-review

使用 Gemini CLI 进行代码评审...

**执行命令**：
\`\`\`bash
gemini -p "请评审以下代码变更，指出潜在问题：
$(git diff HEAD~1)
"
\`\`\`

**结果处理**：
- 无严重问题 → SUCCESS
- 发现问题 → 进入 REVIEW_FIX 修复循环
```

**降级模式**（Gemini CLI 不可用）：
```markdown
⚠️ Gemini CLI 不可用，跳过 gemini-review

降级原因：gemini 命令未找到
影响：跳过外部代码评审，仅依赖 /check 结果

继续执行 → SUCCESS（带警告）
```

---

### Phase 5: 输出报告

#### 成功报告（SUCCESS）

```markdown
✅ 开发阶段完成

📊 执行统计：
   - 总耗时：X 分钟
   - 重试次数：Y 次
   - 自动修复：Z 个问题

📋 执行阶段：
   ✅ 门控检查
   ✅ /run-plan
   ✅ /check
   ✅ /gemini-review（或 ⚠️ 已跳过）

🎯 下一步：执行 /qa（测试验收）
```

#### 失败报告（FAILED）

```markdown
❌ 开发阶段失败

📊 执行统计：
   - 总耗时：X 分钟
   - 重试次数：3 次（已达上限）

📋 未解决的问题：
   1. [问题描述]
   2. [问题描述]

💡 建议：
   - 人工检查上述问题
   - 修复后重新执行 /dev-loop

📁 检查点已保存，下次执行可恢复
```

---

## 状态机

### 状态定义

```
┌─────────────────────────────────────────────────────────────────┐
│                         状态转换图                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐                                                    │
│  │  INIT   │ ─────────────────────────────────────┐             │
│  └────┬────┘                                      │             │
│       │ gate_check()                              │             │
│       ↓                                           ↓             │
│  ┌─────────┐    失败                         ┌─────────┐        │
│  │  GATE   │ ───────────────────────────────→│ FAILED  │        │
│  └────┬────┘                                 └─────────┘        │
│       │ 通过                                      ↑             │
│       ↓                                           │             │
│  ┌─────────┐    失败（重试<3）  ┌─────────┐      │             │
│  │RUN_PLAN │ ←─────────────────│ FIXING  │      │             │
│  └────┬────┘                   └────┬────┘      │             │
│       │ 完成                        ↑           │             │
│       ↓                             │ 分析+修复  │             │
│  ┌─────────┐    失败               │            │             │
│  │ CHECK   │ ──────────────────────┘            │             │
│  └────┬────┘                                    │             │
│       │ 通过                                    │             │
│       ↓                                         │             │
│  ┌─────────┐    发现问题    ┌─────────┐        │             │
│  │ REVIEW  │ ──────────────→│REVIEW_FIX│───────┘             │
│  └────┬────┘               └─────────┘  重试>=3              │
│       │ 通过                                                   │
│       ↓                                                        │
│  ┌─────────┐                                                   │
│  │ SUCCESS │                                                   │
│  └─────────┘                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 状态转换规则

| 状态 | 可转换到 | 触发条件 |
|------|---------|---------|
| INIT | GATE | 启动 |
| GATE | RUN_PLAN | 门控通过 |
| GATE | FAILED | 门控失败（plan 不存在） |
| RUN_PLAN | CHECK | run-plan 完成 |
| CHECK | REVIEW | check 通过 |
| CHECK | FIXING | check 失败且 retry < 3 |
| CHECK | FAILED | check 失败且 retry >= 3 |
| FIXING | CHECK | 修复完成 |
| REVIEW | SUCCESS | review 通过或降级模式 |
| REVIEW | REVIEW_FIX | review 发现问题且 retry < 3 |
| REVIEW | FAILED | review 失败且 retry >= 3 |
| REVIEW_FIX | CHECK | 修复完成，重新检查 |

---

## 检查点机制

### 检查点文件

**路径**：`docs/.checkpoint/dev_loop.json`

```json
{
  "version": 1,
  "current_state": "CHECK",
  "retry_count": 1,
  "plan_doc": "docs/开发文档/plan_xxx.md",
  "gemini_available": true,
  "last_errors": [
    "ruff: E501 line too long",
    "mypy: Missing return type"
  ],
  "fix_history": [
    {
      "attempt": 1,
      "error_type": "L1_LINT",
      "fixed_count": 3,
      "remaining_count": 2,
      "actions": ["ruff --fix backend/"]
    }
  ],
  "started_at": "2026-02-04T15:30:00Z",
  "updated_at": "2026-02-04T15:35:00Z"
}
```

### 恢复流程

```
启动 /dev-loop
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
/clarify（需求澄清）
    ↓
/explore（方案探索）
    ↓
/design（架构设计）
    ↓
/plan（写计划）
    ↓
/dev-loop（本 Skill）← 封装 run-plan + check + gemini-review + 修复循环
    ├─ 调用 /run-plan
    ├─ 调用 /check
    └─ 调用 /gemini-review
    ↓
/qa（测试验收）
```

---

## 边界约束（铁律）

| 禁止行为 | 说明 |
|---------|------|
| ❌ 跳过 /check 直接进入 /gemini-review | check 是必经环节 |
| ❌ 超过 3 次重试继续执行 | 必须停止并报告 |
| ❌ 修复失败静默跳过 | 必须记录并报告 |
| ❌ 不保存检查点 | 每次状态变更必须保存 |

---

## 使用示例

### 示例 1：正常执行

```
用户：/dev-loop

Claude：
  📋 dev-loop 启动

  ✅ Plan 文档: docs/开发文档/plan_用户认证.md
  ✅ Gemini CLI 可用

  🚀 执行 /run-plan...
  ✅ /run-plan 完成

  🔍 执行 /check...
  ✅ /check 通过

  🔎 执行 /gemini-review...
  ✅ /gemini-review 通过

  ✅ 开发阶段完成！

  📊 执行统计：
     - 总耗时：15 分钟
     - 重试次数：0 次

  🎯 下一步：执行 /qa（测试验收）
```

### 示例 2：自动修复

```
用户：/dev-loop

Claude：
  📋 dev-loop 启动

  🚀 执行 /run-plan...
  ✅ /run-plan 完成

  🔍 执行 /check...
  ❌ /check 失败（lint 错误）

  🔧 自动修复（尝试 1/3）...
  - 错误类型：L1_LINT
  - 执行：ruff check --fix .
  - 修复：3 个错误

  🔍 重新执行 /check...
  ✅ /check 通过

  🔎 执行 /gemini-review...
  ✅ /gemini-review 通过

  ✅ 开发阶段完成！

  📊 执行统计：
     - 总耗时：20 分钟
     - 重试次数：1 次
     - 自动修复：3 个问题
```

### 示例 3：达到重试上限

```
用户：/dev-loop

Claude：
  📋 dev-loop 启动

  🚀 执行 /run-plan...
  ✅ /run-plan 完成

  🔍 执行 /check...
  ❌ /check 失败

  🔧 自动修复（尝试 1/3）...
  🔍 重新执行 /check...
  ❌ 仍失败

  🔧 自动修复（尝试 2/3）...
  🔍 重新执行 /check...
  ❌ 仍失败

  🔧 自动修复（尝试 3/3）...
  🔍 重新执行 /check...
  ❌ 仍失败

  ❌ 开发阶段失败

  📊 执行统计：
     - 总耗时：45 分钟
     - 重试次数：3 次（已达上限）

  📋 未解决的问题：
     1. tests/test_auth.py::test_login - AssertionError
     2. mypy: Incompatible return type

  💡 建议：
     - 人工检查上述问题
     - 修复后重新执行 /dev-loop

  📁 检查点已保存: docs/.checkpoint/dev_loop.json
```

---

## 完成检查清单

- [ ] Plan 文档存在
- [ ] /run-plan 执行完成
- [ ] /check 通过（或重试后通过）
- [ ] /gemini-review 通过（或降级跳过）
- [ ] 检查点已清除
- [ ] 输出完成报告
