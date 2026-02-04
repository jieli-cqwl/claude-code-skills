# 开发阶段自动化 (dev-loop) 实施计划

**创建日期**：2026-02-04
**文档路径**：`docs/开发文档/plan_开发阶段自动化.md`

---

## 目标

创建 `/dev-loop` Skill，自动化开发阶段的完整流程：run-plan → check → gemini-review → 自动修复循环。

---

## 前置文档

- AC 文档：`docs/需求澄清/clarify_开发阶段自动化.md`
- 调研文档：`docs/设计文档/调研_开发阶段自动化.md`
- 设计文档：`docs/设计文档/设计_开发阶段自动化.md`

---

## 技术栈

- 类型：Skills 开发（纯后端/CLI）
- 格式：Markdown（SKILL.md）
- 复用：现有 auto-dev、run-plan、check 模式

---

## 拆分决策分析

### 1. 功能独立性分析

- 模块 1：门控检查（Gate）→ `SKILL.md` 门控部分
- 模块 2：状态机（StateMachine）→ `SKILL.md` 执行流程部分
- 模块 3：修复器（Fixer）→ `SKILL.md` 或 `prompts/fixer.md`
- 模块 4：检查点（Checkpoint）→ `SKILL.md` 检查点部分
- **结论**：单一 Skill 文件，模块内聚，不适合拆分

### 2. 数据依赖分析

- 所有模块都围绕同一个状态流转
- 检查点贯穿整个流程
- **结论**：数据高度耦合

### 3. 时间前置分析

- 无需基础设施搭建
- 直接编写 SKILL.md 即可
- **结论**：无明显前置依赖

### 4. 通信成本分析

- 单一 SKILL.md 文件，无模块间通信
- **结论**：通信成本为零

### 最终决策

- **模式**：依赖链模式
- **原因**：单一 Skill 文件，内容紧密耦合，无法按功能拆分

---

## Tasks 执行清单（依赖链版）

| Task | 描述 | 依赖 | 预估 |
|------|------|------|------|
| T1 | 创建 SKILL.md 基础结构 | 无 | 15 分钟 |
| T2 | 实现门控检查逻辑 | T1 | 10 分钟 |
| T3 | 实现状态机执行流程 | T2 | 20 分钟 |
| T4 | 实现自动修复逻辑 | T3 | 20 分钟 |
| T5 | 实现检查点机制 | T4 | 15 分钟 |
| T6 | 实现完成报告输出 | T5 | 10 分钟 |
| T7 | 端到端验证 | T6 | 15 分钟 |

### 并行执行分组

```
依赖关系图：

T1 (基础结构)
 ↓
T2 (门控检查)
 ↓
T3 (状态机)
 ↓
T4 (自动修复)
 ↓
T5 (检查点)
 ↓
T6 (完成报告)
 ↓
T7 (端到端验证)
```

**串行执行**：T1 → T2 → T3 → T4 → T5 → T6 → T7

---

## 验收测试场景（引用 /clarify AC）

**AC 来源文档**：`docs/需求澄清/clarify_开发阶段自动化.md`
**AC 指纹**：`AC-HASH-7B3F2E1A`

**引用的 AC 列表**：

正常流程：
- [AC-1 → clarify_开发阶段自动化.md] 存在 plan 文档，代码质量良好 → 执行 run-plan → check → gemini-review，全部通过后输出成功报告
- [AC-2 → clarify_开发阶段自动化.md] run-plan 执行完成 → 自动进入 check
- [AC-3 → clarify_开发阶段自动化.md] check 通过 → 自动进入 gemini-review
- [AC-4 → clarify_开发阶段自动化.md] gemini-review 通过 → 输出完成报告

异常流程：
- [AC-5 → clarify_开发阶段自动化.md] check 失败 → 自动分析并修复，重新执行 check
- [AC-6 → clarify_开发阶段自动化.md] gemini-review 发现问题 → 自动修复，重新执行 check → gemini-review
- [AC-7 → clarify_开发阶段自动化.md] 修复后重新评审通过 → 退出修复循环，输出成功报告
- [AC-8 → clarify_开发阶段自动化.md] 修复失败需再次修复 → 累计重试次数，继续尝试

边界情况：
- [AC-9 → clarify_开发阶段自动化.md] 达到最大重试次数（3 次）→ 停止循环，输出失败报告
- [AC-10 → clarify_开发阶段自动化.md] plan 文档不存在 → 门控失败，提示先执行 /plan
- [AC-11 → clarify_开发阶段自动化.md] gemini CLI 不可用 → 跳过 gemini-review，降级为仅 check
- [AC-12 → clarify_开发阶段自动化.md] 用户中断执行 → 保存检查点，下次可恢复

**完整 AC 表格见**：[clarify_开发阶段自动化.md](docs/需求澄清/clarify_开发阶段自动化.md#3-验收标准)

---

## 测试设计状态

> 本需求为 Skills 开发，测试方式为手动 E2E 验证，不需要 /test-gen

- [x] AC 来源文档存在：`docs/需求澄清/clarify_开发阶段自动化.md`
- [x] 测试方式确定：手动 E2E 验证（Skills 开发）

---

## Task 详情

### T1: 创建 SKILL.md 基础结构

- [x] T1: 创建 SKILL.md 基础结构

**依赖**：无
**预估**：15 分钟

**文件**：`~/.claude/skills/开发循环_dev-loop/SKILL.md`

**步骤**：

#### Step 1.1: 创建目录结构

```bash
mkdir -p ~/.claude/skills/开发循环_dev-loop/prompts
```

#### Step 1.2: 创建 SKILL.md 头部

**内容**：
- frontmatter（name, command, user_invocable, description）
- 角色定义
- 触发条件
- 文档契约

**验证**：文件存在且格式正确

---

### T2: 实现门控检查逻辑

- [x] T2: 实现门控检查逻辑

**依赖**：T1
**预估**：10 分钟

**步骤**：

#### Step 2.1: 添加门控检查章节

**检查项**：
1. plan 文档存在检查
2. gemini CLI 可用性检查

**逻辑**：
```markdown
## 门控检查

### 1. Plan 文档检查

PLAN_DOC=$(ls docs/开发文档/plan_*.md 2>/dev/null | head -1)
if [ -z "$PLAN_DOC" ]; then
  echo "❌ 门控失败: Plan 文档不存在"
  echo "   修复: 先执行 /plan 生成计划文档"
  # 停止执行
fi

### 2. Gemini CLI 检查

which gemini >/dev/null 2>&1
GEMINI_AVAILABLE=$?
if [ $GEMINI_AVAILABLE -ne 0 ]; then
  echo "⚠️ Gemini CLI 不可用，将跳过 gemini-review（降级模式）"
fi
```

**验证**：门控逻辑完整

---

### T3: 实现状态机执行流程

- [x] T3: 实现状态机执行流程

**依赖**：T2
**预估**：20 分钟

**步骤**：

#### Step 3.1: 定义状态和转换

**状态列表**：
- INIT → GATE → RUN_PLAN → CHECK → REVIEW → SUCCESS
- 失败路径：→ FIXING → CHECK（重试）
- 失败路径：→ REVIEW_FIX → CHECK → REVIEW（重试）
- 终止状态：SUCCESS / FAILED

#### Step 3.2: 实现执行流程

**主流程**：
```markdown
## 执行流程

### Phase 1: 门控检查
[调用门控检查逻辑]

### Phase 2: 执行 /run-plan
读取 SKILL.md 指令，执行开发任务

### Phase 3: 执行 /check
读取 SKILL.md 指令，执行代码检查
- 通过 → 继续
- 失败 → 进入修复循环

### Phase 4: 执行 /gemini-review（如果可用）
读取 SKILL.md 指令，执行代码评审
- 通过 → SUCCESS
- 发现问题 → 进入修复循环

### Phase 5: 输出报告
```

**验证**：流程覆盖所有状态转换

---

### T4: 实现自动修复逻辑

- [x] T4: 实现自动修复逻辑

**依赖**：T3
**预估**：20 分钟

**步骤**：

#### Step 4.1: 实现错误分类

**分类规则**：
- L1_LINT：包含 "ruff"/"eslint"/"lint"
- L2_TYPE：包含 "mypy"/"type"/"annotation"
- L3_TEST：包含 "pytest"/"test"/"assert"
- L4_REVIEW：来自 gemini-review

#### Step 4.2: 实现分层修复策略

**修复逻辑**：
```markdown
## 自动修复

### L1: Lint 错误
执行：ruff check --fix . && ruff format .

### L2: 类型错误
分析错误信息，生成类型注解补丁

### L3: 测试失败
分析测试失败原因，修复代码或测试

### L4: Review 问题
逐条分析评审意见，生成修复补丁
```

#### Step 4.3: 实现重试计数

**逻辑**：
- 全局重试计数（check 和 review 共享）
- MAX_RETRY = 3
- 达到上限 → FAILED

**验证**：修复逻辑完整，重试计数正确

---

### T5: 实现检查点机制

- [x] T5: 实现检查点机制

**依赖**：T4
**预估**：15 分钟

**步骤**：

#### Step 5.1: 定义检查点格式

**路径**：`docs/.checkpoint/dev_loop.json`

**格式**：
```json
{
  "version": 1,
  "current_state": "CHECK",
  "retry_count": 1,
  "plan_doc": "docs/开发文档/plan_xxx.md",
  "gemini_available": true,
  "last_errors": [],
  "fix_history": [],
  "started_at": "2026-02-04T15:30:00Z",
  "updated_at": "2026-02-04T15:35:00Z"
}
```

#### Step 5.2: 实现保存/恢复逻辑

**保存时机**：每次状态变更
**恢复时机**：启动时检测检查点存在
**清除时机**：执行完成（SUCCESS 或 FAILED）

**验证**：检查点可正确保存和恢复

---

### T6: 实现完成报告输出

- [x] T6: 实现完成报告输出

**依赖**：T5
**预估**：10 分钟

**步骤**：

#### Step 6.1: 实现成功报告

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
   ✅ /gemini-review

🎯 下一步：执行 /qa（测试验收）
```

#### Step 6.2: 实现失败报告

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
```

**验证**：报告格式正确，信息完整

---

### T7: 端到端验证

- [x] T7: 端到端验证

**依赖**：T6
**预估**：15 分钟

**步骤**：

#### Step 7.1: 验证正常流程

**场景**：存在 plan 文档，代码质量良好
**操作**：执行 `/dev-loop`
**预期**：run-plan → check → gemini-review → 成功报告

#### Step 7.2: 验证修复循环

**场景**：代码有 lint 错误
**操作**：执行 `/dev-loop`
**预期**：check 失败 → 自动修复 → 重新 check → 通过

#### Step 7.3: 验证门控失败

**场景**：plan 文档不存在
**操作**：执行 `/dev-loop`
**预期**：门控失败，提示先执行 /plan

#### Step 7.4: 验证降级模式

**场景**：gemini CLI 不可用
**操作**：执行 `/dev-loop`
**预期**：跳过 gemini-review，仅执行 check

**验证**：所有 AC 场景通过

---

## 验收完成确认（/qa 执行后勾选）

- [ ] 所有 AC 场景验收通过
- [ ] SKILL.md 语法正确
- [ ] 门控检查正常工作
- [ ] 状态机流转正确
- [ ] 自动修复功能可用
- [ ] 检查点可保存/恢复
- [ ] 报告输出完整

---

## 下一步

1. 评审计划（可选）：`/critique`
2. 执行计划：`/run-plan docs/开发文档/plan_开发阶段自动化.md`

---

## 📋 /clear 后可直接执行

```
/run-plan docs/开发文档/plan_开发阶段自动化.md
```
