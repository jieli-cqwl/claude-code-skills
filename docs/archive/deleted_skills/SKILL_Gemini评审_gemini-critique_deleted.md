---
name: gemini-critique
command: gemini-critique
user_invocable: true
allowed-tools: Bash(gemini *)
description: Gemini 需求/设计评审。用 Gemini CLI 作为"第二双眼睛"独立评审 Claude 输出的需求澄清和架构设计，提供外部视角。在 /clarify 或 /design 之后使用，防止 Claude 评审 Claude 的盲点。
---

# Gemini 需求/设计评审 (Gemini Critique)

> **角色**：独立评审员（第二双眼睛）
> **目标**：用 Gemini CLI 对 Claude 生成的需求和设计进行独立评审，提供外部视角
> **原则**：AI 监督 AI，防止同一模型的认知盲点
> **适用场景**：/clarify 之后、/design 之后、重大决策前

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**Gemini 评审**"或"**交叉评审**"（主触发词）
- 使用命令：`/gemini-critique`
- 说"让 Gemini 看看需求"、"让 Gemini 看看设计"
- 说"用 Gemini 检查下"、"外部评审"
- 说"第二意见"、"独立评审"、"交叉检查"

**参数支持**：
- `/gemini-critique` — 自动检测最新的 clarify 或 design 文档
- `/gemini-critique clarify` — 评审需求澄清文档
- `/gemini-critique design` — 评审架构设计文档
- `/gemini-critique [文档路径]` — 评审指定文档

---

## 为什么需要 Gemini 评审

| 问题 | Claude 自评的局限 | Gemini 外部评审的价值 |
|------|------------------|---------------------|
| 认知盲点 | Claude 评审 Claude，可能有相同的思维模式 | 不同模型，不同的分析角度 |
| 确认偏误 | 倾向于认可自己的输出 | 全新视角，无先入之见 |
| 遗漏检测 | 可能遗漏相同类型的问题 | 不同的检测能力和关注点 |

---

## 执行流程

### Phase 0: 前置检查（Gemini CLI 安装检测）

```bash
# 检测 Gemini CLI 是否安装
check_gemini_cli() {
    if ! command -v gemini &> /dev/null; then
        echo "❌ Gemini CLI 未安装"
        echo ""
        echo "📦 安装方法："
        echo "   npm install -g @google/gemini-cli"
        echo ""
        echo "🔑 安装后需要认证："
        echo "   gemini auth"
        echo ""
        echo "💡 或者使用 /critique 进行 Claude 自评审（无需 Gemini）"
        return 1
    fi

    # 检测是否已认证
    if ! gemini --version &> /dev/null; then
        echo "⚠️ Gemini CLI 可能未认证"
        echo "   请运行: gemini auth"
        return 1
    fi

    echo "✅ Gemini CLI 已就绪"
    return 0
}

# 执行检测
if ! check_gemini_cli; then
    exit 1
fi
```

### Phase 1: 确定评审范围

```bash
# 自动检测评审目标
if [ "$ARGUMENTS" = "clarify" ]; then
    DOC=$(ls docs/需求澄清/clarify_*.md 2>/dev/null | head -1)
    TYPE="需求澄清"
elif [ "$ARGUMENTS" = "design" ]; then
    DOC=$(ls docs/设计文档/设计_*.md 2>/dev/null | head -1)
    TYPE="架构设计"
elif [ -n "$ARGUMENTS" ]; then
    DOC="$ARGUMENTS"
    TYPE="指定文档"
else
    # 自动检测最新文档
    CLARIFY=$(ls -t docs/需求澄清/clarify_*.md 2>/dev/null | head -1)
    DESIGN=$(ls -t docs/设计文档/设计_*.md 2>/dev/null | head -1)

    # 选择最新的
    if [ -n "$DESIGN" ] && [ "$DESIGN" -nt "$CLARIFY" ]; then
        DOC="$DESIGN"
        TYPE="架构设计"
    else
        DOC="$CLARIFY"
        TYPE="需求澄清"
    fi
fi

if [ -z "$DOC" ]; then
    echo "❌ 未找到可评审的文档"
    echo "   请先执行 /clarify 或 /design"
    exit 1
fi

echo "📋 评审目标：$TYPE"
echo "📄 文档路径：$DOC"
```

---

### Phase 2: 调用 Gemini CLI 评审

> **核心原则**：Claude 是被评审者，不应该决定评审者看什么。让 Gemini 自己读文件、自己理解上下文、自己对照规范。这样才是真正独立的"第二双眼睛"。

**关键点**：
| 要求 | 说明 |
|------|------|
| **Pin 模型** | 必须用 `-m gemini-2.5-pro`，防止静默降级到 Flash |
| **自主探索** | `--yolo` 让 Gemini 自动执行只读操作（读文件、ls 目录等） |
| **不喂上下文** | 禁止 `cat 文档 \| gemini` 的方式，让 Gemini 自己读取和探索 |
| **超时控制** | Bash 调用设置 120 秒超时 |

**需求澄清评审**：

```bash
cd <项目根目录> && gemini -m gemini-2.5-pro -p "你是独立需求评审员。请在当前项目中：
1. 读取需求文档：$DOC
2. 读取 CLAUDE.md 了解项目规范和铁律
3. 读取现有代码结构了解技术约束（ls src/ 等）
4. 基于你自己的理解独立评审

评审维度：
- 完整性：AC 是否覆盖正常/异常/边界？是否有遗漏场景？非功能需求是否明确？
- 清晰度：需求是否有歧义？AC 是否可测试可验证？术语是否一致？
- 可行性：技术实现是否可行？是否有隐藏复杂度？依赖是否明确？
- 一致性：AC 之间是否冲突？与现有系统是否兼容？
- 项目规范：是否违反 CLAUDE.md 中的铁律或规范？

输出格式：按 CRITICAL/WARNING/INFO 分级列出问题，每个问题包含：问题描述、影响分析、改进建议。最后给出总结论（通过/需要补充/需要重做）。" --yolo -o text 2>&1
```

**架构设计评审**：

```bash
cd <项目根目录> && gemini -m gemini-2.5-pro -p "你是独立架构评审员。请在当前项目中：
1. 读取设计文档：$DOC
2. 读取 CLAUDE.md 了解项目规范和铁律
3. 读取相关的需求文档作为对照（ls docs/需求澄清/ 等）
4. 读取现有代码结构了解技术现状
5. 基于你自己的理解独立评审

评审维度：
- 架构合理性：模块划分、职责清晰度、是否过度设计或设计不足
- 接口设计：API 规范、接口契约完整性、版本兼容
- 数据模型：数据结构合理性、冗余/缺失、索引设计
- 可扩展性：扩展难度、单点故障、未来需求考虑
- 安全性：安全漏洞风险、权限控制、敏感数据处理
- 项目规范：是否违反 CLAUDE.md 中的铁律或规范？

输出格式：按 CRITICAL/WARNING/INFO 分级列出问题，每个问题包含：问题描述、影响分析、改进建议。最后给出总结论（通过/需要调整/需要重新设计）。" --yolo -o text 2>&1
```

**通用文档评审**（当指定了非 clarify/design 的文档路径时）：

```bash
cd <项目根目录> && gemini -m gemini-2.5-pro -p "你是独立需求/设计评审员。请在当前项目中：
1. 读取指定的文档：$DOC
2. 读取 CLAUDE.md 了解项目规范和铁律
3. 如果是设计文档，读取相关的需求文档作为对照
4. 如果是需求文档，读取现有代码结构了解技术约束
5. 基于你自己的理解独立评审
聚焦：完整性、一致性、可行性、风险、项目规范违反。按 CRITICAL/WARNING/INFO 分级。" --yolo -o text 2>&1
```

---

### Phase 3: 整合评审结果

```markdown
## Gemini 需求/设计评审报告

**评审时间**：YYYY-MM-DD HH:mm
**评审类型**：[需求澄清 / 架构设计]
**评审文档**：[文档路径]
**评审模型**：gemini-2.5-pro

---

### 发现的问题

| # | 类型 | 问题描述 | 影响 | 改进建议 |
|---|------|---------|------|---------|
| 1 | 完整性 | [描述] | 高/中/低 | [建议] |
| 2 | 清晰度 | [描述] | 高/中/低 | [建议] |

### 做得好的地方

1. [优点 1]
2. [优点 2]

---

### 结论

- ✅ **评审通过** - 可以进入下一阶段
- ⚠️ **需要补充** - 有 X 个问题需要解决
- ❌ **需要重做** - 有严重问题

### 下一步

- 如有问题：修复后可再次 `/gemini-critique` 确认
- 如无问题：继续下一阶段（/design 或 /plan）
```

---

## 与其他 Skills 的关系

```
/clarify（需求澄清）
    ↓ Claude 输出 AC 文档
/gemini-critique clarify ← 当前（外部评审需求）
    ↓ 评审通过
/explore（方案探索）
    ↓
/design（架构设计）
    ↓ Claude 输出设计文档
/gemini-critique design ← 当前（外部评审设计）
    ↓ 评审通过
/plan（写计划）
    ↓
/run-plan（执行计划）
    ↓
/check（开发检查）
    ↓
/qa（测试验收）
```

---

## 使用建议

| 需求规模 | 建议 |
|---------|------|
| 小需求（AC ≤ 3） | 可跳过，/critique 足够 |
| 中需求（AC 4-8） | 建议评审设计 |
| 大需求（AC > 8） | 强烈建议评审需求和设计 |

---

## 错误处理

| 错误 | 原因 | 解决方法 |
|------|------|---------|
| `gemini: command not found` | Gemini CLI 未安装 | `npm install -g @google/gemini-cli` |
| `Authentication required` | 未认证 | `gemini auth` |
| 未找到文档 | 文档不存在 | 先执行 /clarify 或 /design |

---

## 禁止行为

| 禁止 | 原因 |
|------|------|
| 盲目信任 Gemini 输出 | 仍需人工判断，AI 可能误报 |
| 替代 /critique 使用 | /critique 是 Claude 自检，/gemini-critique 是外部补充 |
| 跳过所有评审 | 至少使用一种评审方式 |

---

## 完成提示

```
✅ Gemini 需求/设计评审完成

📊 评审结果：
- 评审类型：[需求澄清 / 架构设计]
- 评审文档：[文档路径]
- 发现问题：X 个
- 建议项：Y 个
- 评审结论：[通过 / 需要补充 / 需要重做]

🎯 下一步：
- 如有问题：修复后可再次 /gemini-critique
- 如无问题：继续下一阶段
  - 需求评审后 → /explore 或 /design
  - 设计评审后 → /plan
```
