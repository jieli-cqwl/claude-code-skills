# 文档同步治理 实施计划

## 目标

建立文档同步机制，确保代码改动后相关文档同步更新，避免过时文档干扰 Claude Code。

## 前置文档

- 需求澄清：2026-01-26 `/clarify` 会话确认

## 涉及项目

- `/Users/lijieli/project/qft-pai`
- `/Users/lijieli/project/ai/agent/qft-tools`

---

## Phase 1: 建立增量机制

### Step 1.1: 修改 RULES.md 添加文档同步规范

**目标**：在核心规范中定义文档同步要求

**文件**：
- `~/.claude/rules/RULES.md` - 新增文档同步规范条目

**代码**：

在 `## 文档要求` 部分后新增：

```markdown
---

## 文档同步（铁律级）

> 代码与文档必须同步更新，过时文档视为 Bug。

### 触发条件

| 代码改动类型 | 需要更新的文档 |
|-------------|---------------|
| 新增 API 接口 | API 文档（`docs/API文档/`） |
| 修改 API 参数/返回值 | API 文档 |
| 新增功能 | PRD/需求文档（如有） |
| 修改现有功能行为 | PRD/需求文档 |
| 架构变更 | 设计文档（`docs/设计文档/`） |
| 配置项变更 | 配置说明文档 |
| 技术栈变更 | CLAUDE.md |

### 执行标准

- **改代码时**：检查是否有相关文档需要更新
- **无相关文档**：无需创建新文档（除非复杂改动 >10 文件）
- **有相关文档但过时**：更新或删除
- **完成标准**：代码 + 文档同步完成才算完成

### 禁止行为

- 改了 API 不更新 API 文档
- 改了功能不更新需求文档
- 文档描述与代码实现不一致
```

**验证命令**：

```bash
cat ~/.claude/rules/RULES.md | grep -A 20 "文档同步"
```

**预期输出**：显示新增的文档同步规范内容

---

### Step 1.2: 修改 /check 技能添加文档同步检查

**目标**：在开发检查中加入文档同步验证环节

**文件**：
- `~/.claude/skills/开发检查_check/SKILL.md` - 新增 Agent5: 文档同步检查

**代码**：

在 Phase 2 的 4 个 Agent 后新增第 5 个：

```markdown
5. **Agent5: 文档同步检查**
   - 分析变更文件，识别代码改动类型
   - 检查是否有相关文档需要同步更新
   - 验证文档内容与代码是否一致
```

在并行检查模板中新增：

```markdown
<Task>
  subagent_type: Explore
  description: "文档同步检查"
  prompt: "检查代码变更是否需要同步更新文档：
    1. 分析变更文件列表：[文件列表]
    2. 识别改动类型（API/功能/配置/架构）
    3. 搜索 docs/ 目录下相关文档
    4. 验证文档内容与代码是否一致
    返回：
    - 需要更新但未更新的文档列表
    - 文档与代码不一致的具体位置
    - 或'文档已同步'"
</Task>
```

在汇总报告模板中新增：

```markdown
## Agent5: 文档同步
- [ ] 相关文档已识别
- [ ] 文档内容与代码一致
- 需要更新的文档：（无/列表）
```

**验证命令**：

```bash
cat ~/.claude/skills/开发检查_check/SKILL.md | grep -A 10 "文档同步"
```

**预期输出**：显示新增的文档同步检查内容

---

## Phase 2: 清理 qft-pai 存量文档

### Step 2.1: 扫描 qft-pai 文档与代码一致性

**目标**：识别 qft-pai 项目中过时的文档

**执行**：使用 Task 工具并行检查各类文档

```markdown
<Task>
  subagent_type: Explore
  description: "qft-pai 文档扫描"
  prompt: "扫描 /Users/lijieli/project/qft-pai/docs/ 下所有文档，逐个检查：
    1. API 文档：对比 docs/API文档/ 与实际 API 代码
    2. 设计文档：检查描述的架构是否与当前代码一致
    3. 开发文档：plan_*.md 是否已完成可归档
    4. 配置文档：配置说明是否与实际配置一致

    输出：
    - 过时文档列表（需删除）
    - 可能过时文档列表（需人工确认）
    - 最新文档列表（保留）"
</Task>
```

**预期输出**：分类的文档清单

---

### Step 2.2: 删除 qft-pai 过时文档

**目标**：删除确认过时的文档

**执行**：根据 Step 2.1 输出，删除过时文档

```bash
# 示例（实际文件根据扫描结果确定）
cd /Users/lijieli/project/qft-pai
rm docs/开发文档/plan_已完成功能1.md
rm docs/API文档/API_已废弃接口.md
# ...
```

**验证命令**：

```bash
ls /Users/lijieli/project/qft-pai/docs/
```

**预期输出**：只剩有效文档

---

### Step 2.3: 提交 qft-pai 文档清理

**目标**：提交文档清理变更

```bash
cd /Users/lijieli/project/qft-pai
git add docs/
git commit -m "docs: 清理过时文档

- 删除已完成的计划文档
- 删除已废弃的 API 文档
- 删除与代码不一致的设计文档

相关需求：文档同步治理"
```

---

## Phase 3: 清理 qft-tools 存量文档

### Step 3.1: 扫描 qft-tools 文档与代码一致性

**目标**：识别 qft-tools 项目中过时的文档

**执行**：使用 Task 工具并行检查各类文档

```markdown
<Task>
  subagent_type: Explore
  description: "qft-tools 文档扫描"
  prompt: "扫描 /Users/lijieli/project/ai/agent/qft-tools/docs/ 下所有文档，逐个检查：
    1. API 文档：对比 docs/API/ 与实际 API 代码
    2. 设计文档：检查描述的架构是否与当前代码一致
    3. 需求文档：Story_*.md 描述是否与实现一致
    4. 测试文档：测试计划和报告是否对应最新代码

    输出：
    - 过时文档列表（需删除）
    - 可能过时文档列表（需人工确认）
    - 最新文档列表（保留）"
</Task>
```

**预期输出**：分类的文档清单

---

### Step 3.2: 删除 qft-tools 过时文档

**目标**：删除确认过时的文档

**执行**：根据 Step 3.1 输出，删除过时文档

```bash
# 示例（实际文件根据扫描结果确定）
cd /Users/lijieli/project/ai/agent/qft-tools
rm docs/开发文档/plan_已完成功能1.md
rm docs/API/已废弃接口.md
# ...
```

**验证命令**：

```bash
ls /Users/lijieli/project/ai/agent/qft-tools/docs/
```

**预期输出**：只剩有效文档

---

### Step 3.3: 提交 qft-tools 文档清理

**目标**：提交文档清理变更

```bash
cd /Users/lijieli/project/ai/agent/qft-tools
git add docs/
git commit -m "docs: 清理过时文档

- 删除已完成的计划文档
- 删除已废弃的 API 文档
- 删除与代码不一致的设计文档
- 删除过时的测试报告

相关需求：文档同步治理"
```

---

## Phase 4: 验证机制生效

### Step 4.1: 在 qft-pai 测试 /check 文档同步检查

**目标**：验证新增的文档同步检查能正常工作

**执行**：

1. 在 qft-pai 做一个小改动（如修改一个 API 参数）
2. 不更新相关文档
3. 执行 `/check`
4. 验证 Agent5 能识别出「需要更新但未更新的文档」

**预期输出**：/check 报告中显示文档同步问题

---

### Step 4.2: 在 qft-tools 测试 /check 文档同步检查

**目标**：验证 qft-tools 项目也能正常检查

**执行**：同 Step 4.1

**预期输出**：/check 报告中显示文档同步问题

---

## 执行顺序总结

| Phase | 步骤 | 说明 | 预估时间 |
|-------|------|------|---------|
| 1 | 1.1 | 修改 RULES.md | 2 分钟 |
| 1 | 1.2 | 修改 /check 技能 | 3 分钟 |
| 2 | 2.1 | 扫描 qft-pai 文档 | 5 分钟 |
| 2 | 2.2 | 删除过时文档 | 3 分钟 |
| 2 | 2.3 | 提交变更 | 1 分钟 |
| 3 | 3.1 | 扫描 qft-tools 文档 | 5 分钟 |
| 3 | 3.2 | 删除过时文档 | 3 分钟 |
| 3 | 3.3 | 提交变更 | 1 分钟 |
| 4 | 4.1-4.2 | 验证机制 | 5 分钟 |

**总计**：约 28 分钟

---

## 验收标准

### 增量机制验收

- [x] `RULES.md` 包含文档同步规范
- [x] `/check` 技能包含 Agent5 文档同步检查
- [ ] 执行 `/check` 能识别文档同步问题（待验证）

### qft-pai 存量清理验收

- [x] 过时文档已删除（4 个）
- [x] 保留文档与代码一致
- [x] 变更已提交（commit: defa031）

### qft-tools 存量清理验收

- [x] 过时文档已删除（4 个）
- [x] 保留文档与代码一致
- [x] 变更已提交（commit: 6b5bd2d）
