---
name: gemini-review
command: gemini-review
user_invocable: true
allowed-tools: Bash(gemini *)
description: Gemini 代码审查。用 Gemini CLI 作为"第二双眼睛"独立审查 Claude 写的代码，提供外部视角。可在 /check 之后或代码变更后使用，监督代码质量。
---

# Gemini 代码审查 (Gemini Review)

> **角色**：独立审查员（第二双眼睛）
> **目标**：用 Gemini CLI 对 Claude 生成的代码进行独立审查，提供外部视角
> **原则**：AI 监督 AI，双重保障代码质量
> **适用场景**：/check 之后、代码变更后、合并前审查

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**Gemini 审查**"或"**让 Gemini 看看代码**"（主触发词）
- 使用命令：`/gemini-review`
- 说"用 Gemini 检查代码"、"交叉审查代码"
- 说"外部审查"、"独立审查"
- 说"让 Gemini review 下"、"第二意见"

**参数支持**：
- `/gemini-review` — 审查所有未提交的变更
- `/gemini-review [文件路径]` — 审查指定文件
- `/gemini-review --staged` — 审查已暂存的变更

---

## 为什么需要 Gemini 审查

| 问题 | Claude 自检的局限 | Gemini 外部审查的价值 |
|------|------------------|---------------------|
| 盲点 | 可能对自己写的代码有认知偏见 | 全新视角，无先入之见 |
| 上下文窗口 | 受限于当前会话上下文 | 1M token 上下文，可分析整个代码库 |
| 模式识别 | 可能重复相同的错误模式 | 不同模型有不同的检测能力 |

---

## 执行流程

### Phase 1: 确定审查范围

```bash
# 获取变更范围
if [ "$ARGUMENTS" = "--staged" ]; then
    # 审查已暂存的变更
    DIFF=$(git diff --cached)
    SCOPE="已暂存变更"
elif [ -n "$ARGUMENTS" ]; then
    # 审查指定文件
    DIFF=$(cat "$ARGUMENTS")
    SCOPE="指定文件: $ARGUMENTS"
else
    # 审查所有未提交变更
    DIFF=$(git diff HEAD)
    SCOPE="未提交变更"
fi
```

**输出**：
```markdown
## 审查范围
- 模式：[未提交变更 / 已暂存变更 / 指定文件]
- 变更文件：[文件列表]
- 变更行数：+X / -Y
```

---

### Phase 2: 调用 Gemini CLI 审查

**执行命令**：

```bash
# 方式一：审查 git diff（推荐）
git diff HEAD | gemini -p "
你是资深代码审查员。请审查以下代码变更：

## 审查维度
1. **安全性**：注入漏洞、敏感信息泄露、权限问题
2. **正确性**：逻辑错误、边界条件、异常处理
3. **性能**：N+1 查询、无效循环、资源泄漏
4. **可维护性**：代码清晰度、命名规范、过度复杂
5. **最佳实践**：设计模式、代码规范、类型安全

## 输出格式
对每个问题：
- 文件:行号
- 问题类型（安全/正确性/性能/可维护性/最佳实践）
- 问题描述
- 修复建议

如果代码质量良好，说明做得好的地方。
" --yolo -o text

# 方式二：审查指定文件
cat [文件路径] | gemini -p "审查这段代码..." --yolo -o text

# 方式三：审查整个项目（大规模分析）
gemini --all-files -p "分析项目代码质量，重点关注..." --yolo -o text
```

**命令参数说明**：
| 参数 | 作用 |
|------|------|
| `--yolo` | 自动批准工具调用（只读操作安全） |
| `-o text` | 纯文本输出，便于阅读 |
| `--all-files` | 包含所有项目文件（大规模分析用） |
| `-p` | 非交互模式，直接传入 prompt |

---

### Phase 3: 整合审查结果

**将 Gemini 的输出整理为标准报告格式**：

```markdown
## Gemini 代码审查报告

**审查时间**：YYYY-MM-DD HH:mm
**审查范围**：[未提交变更 / 指定文件]
**审查模型**：Gemini CLI

---

### 发现的问题

| # | 文件:行号 | 类型 | 问题描述 | 修复建议 |
|---|----------|------|---------|---------|
| 1 | xxx.py:42 | 安全性 | [描述] | [建议] |
| 2 | xxx.ts:18 | 性能 | [描述] | [建议] |

### 做得好的地方

1. [优点 1]
2. [优点 2]

---

### 结论

- ✅ **审查通过** - 代码质量良好
- ⚠️ **需要关注** - 有 X 个建议项
- ❌ **需要修复** - 有 X 个严重问题

### 下一步

- 如有问题：修复后可再次 `/gemini-review` 确认
- 如无问题：继续 `/qa` 或 `/ship`
```

---

## 审查类型

### 快速审查（默认）

```bash
git diff HEAD | gemini -p "快速审查这些代码变更，关注安全和正确性问题" --yolo -o text
```

适用：日常开发、小变更

### 深度审查

```bash
gemini --all-files -p "深度分析整个代码库，包括：
1. 架构设计问题
2. 代码重复
3. 潜在的性能瓶颈
4. 安全漏洞
5. 技术债务" --yolo -o text
```

适用：大型重构、发布前审查、安全审计

### 专项审查

```bash
# 安全审查
gemini --all-files -p "专注安全审查：注入、XSS、CSRF、敏感信息泄露" --yolo -o text

# 性能审查
gemini --all-files -p "专注性能审查：N+1、慢查询、内存泄漏、无效循环" --yolo -o text

# API 审查
gemini --all-files -p "审查 API 设计：RESTful 规范、错误处理、版本控制" --yolo -o text
```

---

## 与其他 Skills 的关系

```
/run-plan（执行计划）
    ↓ 开发完成后
/check（开发检查）← Claude 自检
    ↓ 可选
/gemini-review（Gemini 审查）← 当前（外部审查）
    ↓
/qa（测试验收）
    ↓
/ship（代码交付）
```

**使用建议**：
- **小需求**：/check 足够，可跳过 /gemini-review
- **中/大需求**：建议使用 /gemini-review 双重保障
- **安全敏感**：强烈建议使用 /gemini-review

---

## 错误处理

| 错误 | 原因 | 解决方法 |
|------|------|---------|
| `gemini: command not found` | Gemini CLI 未安装 | `npm install -g @google/gemini-cli` |
| `Authentication required` | 未认证 | `gemini auth` |
| `Rate limit exceeded` | 超出频率限制 | 等待后重试，或使用 API Key |
| 无输出 | 管道传输问题 | 检查 git diff 是否有内容 |

---

## 安全说明

- `--yolo` 模式仅用于**只读操作**（代码审查）
- Gemini 不会修改你的代码，只提供审查意见
- 如需 Gemini 执行写操作，请手动确认

---

## 禁止行为

| 禁止 | 原因 |
|------|------|
| 盲目信任 Gemini 输出 | 仍需人工判断，AI 可能误报 |
| 替代 /check 使用 | /check 是必要环节，/gemini-review 是补充 |
| 用于生产环境自动修复 | 外部审查仅供参考，不应自动执行修复 |

---

## 完成提示

```
✅ Gemini 代码审查完成

📊 审查结果：
- 审查范围：[未提交变更 / X 个文件]
- 发现问题：X 个
- 建议项：Y 个
- 审查结论：[通过 / 需要关注 / 需要修复]

🎯 下一步：
- 如有问题：修复后可再次 /gemini-review
- 如无问题：继续 /qa（测试验收）
```
