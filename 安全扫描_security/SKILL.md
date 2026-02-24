---
name: security
command: security
user_invocable: true
parallel_mode: true
description: |
  安全漏洞扫描。自动激活场景：
  1) 用户问"安全吗"、"有漏洞吗"、"安全检查"、"有没有注入风险"时
  2) 准备发布或提交 PR 前讨论安全问题时
  3) 用户提到 SQL 注入、XSS、CSRF 等安全关键词时
  使用专业工具（Bandit/Semgrep/Gitleaks）系统检查 OWASP Top 10 漏洞，每个漏洞提供可执行修复代码。
---

# 安全扫描 (Security)

> **角色**：安全工程师
> **目标**：使用专业工具发现安全漏洞，提供可执行的修复方案
> **原则**：工具先行、OWASP 覆盖、修复完整
> **思考模式**：启用 ultrathink 深度思考，系统分析安全风险

---

## 核心原则

**"人工审查找不到的漏洞，工具能找到；工具找不到的漏洞，AI 能找到"**

安全检查必须分层：专业工具扫描 + AI 语义分析 + 人工复核高危项。

---

### 支持的语言和框架

| 语言 | 支持程度 | 主要工具 |
|------|----------|----------|
| **Python** | ✅ 完整支持 | Bandit + pip-audit + Semgrep |
| **JavaScript/TypeScript** | ✅ 完整支持 | Semgrep + npm audit + eslint-plugin-security |
| **Java** | ⚠️ 基础支持 | Semgrep + SpotBugs |
| **Go** | ⚠️ 基础支持 | Semgrep + govulncheck |
| **其他语言** | ⚠️ 通用规则 | Semgrep (auto config) + Gitleaks |

**说明**：Python 和 JavaScript 项目有最完整的工具链支持，其他语言使用 Semgrep 通用规则。

---

## 与 /scan 的区别

| 维度 | /scan | /security |
|------|-------|-----------|
| **目标** | 代码质量（技术债） | 安全漏洞 |
| **检测方式** | Grep 模式匹配 | 专业安全工具 |
| **深度** | 表面模式 | AST 语义分析 |
| **覆盖范围** | 代码规范、技术债 | OWASP Top 10 |
| **工具** | 无外部依赖 | Bandit/Semgrep/Gitleaks |

---

## 执行模式

```bash
/security              # 默认：完整扫描
/security quick        # 快速：仅 Bandit + Gitleaks (<30s)
/security full         # 全面：所有工具 + AI 审查
/security deps         # 依赖：pip-audit / npm audit
/security docker       # 容器：Trivy 镜像扫描
/security fix          # 修复：扫描 + 自动修复高置信度问题
/security diff         # 对比：与上次扫描结果对比
```

---

## 执行流程

```
/security [mode]
    ↓
Phase 1: 环境检测
    - 检测项目语言和框架
    - 检查工具可用性
    ↓
Phase 2: 工具扫描（并行）
    ┌──────────────────────────────────────────┐
    │  SAST: Bandit (Python) / Semgrep (全栈)  │
    │  密钥: Gitleaks                          │
    │  依赖: pip-audit / npm audit             │
    └──────────────────────────────────────────┘
    ↓
Phase 3: AI 语义分析
    - 复核工具结果，过滤误报
    - 检查工具遗漏的逻辑漏洞
    ↓
Phase 4: 生成报告
    - 按严重程度分级
    - 每个漏洞附修复代码
    ↓
Phase 5: (可选) 自动修复
    - 高置信度问题自动修复
    - 需用户确认
```

---

## 并行架构

> **设计目标**：通过 8 Agent 并行扫描 + 8 Agent 并行修复建议，大幅提升安全扫描效率。

### Phase 1: 并行扫描（8 Agent，subagent_type=Bash）

同时启动以下 8 个扫描任务，每个 Agent 负责特定的安全检测领域：

| Agent | 扫描任务 | 工具/方法 | 检测目标 |
|-------|---------|----------|---------|
| Agent 1 | Bandit 扫描 | `bandit -r . -f json` | Python 安全漏洞 |
| Agent 2 | Semgrep 扫描 | `semgrep scan --config=auto` | 多语言 SAST |
| Agent 3 | Gitleaks 扫描 | `gitleaks detect` | 密钥泄露 |
| Agent 4 | 依赖漏洞扫描 | `pip-audit` / `npm audit` | 已知 CVE |
| Agent 5 | SQL 注入检测 | Grep + AST 分析 | CWE-89 |
| Agent 6 | XSS 检测 | Grep + 模板分析 | CWE-79 |
| Agent 7 | 认证授权审查 | 代码模式匹配 | CWE-287/CWE-862 |
| Agent 8 | 敏感数据暴露检测 | 正则 + 上下文分析 | CWE-200/CWE-312 |

**Agent 指令模板**：

```markdown
你是安全扫描 Agent，负责 [具体任务]。

**任务**：
1. 执行 [工具/方法]
2. 解析扫描结果
3. 输出标准化格式

**输出格式**：
```json
{
  "agent_id": "[1-8]",
  "task": "[任务名]",
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "cwe": "CWE-XXX",
      "location": "file:line",
      "description": "漏洞描述",
      "evidence": "问题代码片段"
    }
  ],
  "error": null
}
```

**超时**：120 秒
```

**等待所有 Agent 完成后继续。**

### Phase 2: 并行修复建议（8 Agent，subagent_type=general-purpose）

各 Agent 为 Phase 1 发现的漏洞生成修复代码，按漏洞类型分配：

| Agent | 修复领域 | 负责的漏洞类型 |
|-------|---------|---------------|
| Agent 1 | 注入漏洞修复 | SQL 注入、命令注入、LDAP 注入 |
| Agent 2 | XSS/输出编码修复 | XSS、模板注入、HTML 注入 |
| Agent 3 | 认证授权修复 | 弱认证、越权访问、会话管理 |
| Agent 4 | 密钥处理修复 | 硬编码密钥、密钥泄露、弱加密 |
| Agent 5 | 依赖升级建议 | 已知 CVE、过期依赖 |
| Agent 6 | 配置安全修复 | 不安全配置、调试模式、默认凭证 |
| Agent 7 | 数据保护修复 | 敏感数据暴露、日志泄露、明文存储 |
| Agent 8 | 其他漏洞修复 | SSRF、反序列化、业务逻辑 |

**Agent 指令模板**：

```markdown
你是安全修复 Agent，负责为 [漏洞类型] 生成修复代码。

**输入**：Phase 1 扫描结果中属于你负责的漏洞

**要求**：
1. 每个漏洞提供可直接使用的修复代码
2. 包含 Before/After 对比
3. 说明修复原理
4. 标注修复置信度（高/中/低）

**输出格式**：
```json
{
  "agent_id": "[1-8]",
  "fixes": [
    {
      "vulnerability_ref": "Phase1-AgentX-FindingY",
      "location": "file:line",
      "confidence": "high|medium|low",
      "fix_code": {
        "before": "原始代码",
        "after": "修复后代码"
      },
      "explanation": "修复原理说明"
    }
  ]
}
```
```

**等待所有 Agent 完成后继续。**

### Phase 3: 汇总报告（串行）

主 Agent 汇总所有并行 Agent 的结果：

1. **合并扫描结果**
   - 去重：相同位置的相同漏洞只保留一条
   - 关联：将漏洞与修复建议关联

2. **按 OWASP Top 10 分类**
   - A01-A10 分类整理
   - 统计各类别漏洞数量

3. **生成报告**
   - 安全评分计算
   - 严重程度分级汇总
   - 修复优先级排序
   - 输出完整报告到 `docs/安全扫描/`

4. **输出终端摘要**

### 并行错误处理

**单个 Agent 失败**：
- 记录失败原因
- 其他 Agent 继续执行
- 报告中标注"[部分扫描]"及失败的 Agent

**超时处理**：
- 单个 Agent 超时（120 秒）：标记超时，继续汇总已完成结果
- 报告中标注超时的扫描任务

**工具不可用**：
- Agent 检测到工具缺失时，输出 `{"error": "tool_not_found", "tool": "xxx"}`
- 主 Agent 汇总时提示用户安装缺失工具

**结果冲突**：
- 多个 Agent 对同一位置报告不同严重程度：取最高严重程度
- 相同漏洞不同描述：合并去重，保留最详细的描述

---

> OWASP Top 10 详细规则清单、环境检测、工具扫描命令、AI 语义分析（含误报处理和 .security-ignore 格式）详见 `references/security-rules.md`

---

## Phase 4: 报告格式

### 终端输出

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 安全扫描报告 - [项目名]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 安全评分: XX/100

┌─────────────────────────────────────────────────┐
│  🔴 严重漏洞    X 个  (必须立即修复)            │
│  🟠 高危漏洞    X 个  (尽快修复)                │
│  🟡 中危漏洞    X 个  (计划修复)                │
│  🔵 低危漏洞    X 个  (可选修复)                │
└─────────────────────────────────────────────────┘

🔴 严重漏洞:
  1. [CWE-89] SQL 注入 - src/api/users.py:45
     → 修复: 使用参数化查询
  2. [CWE-798] 硬编码密钥 - config/settings.py:12
     → 修复: 移至环境变量

📄 完整报告: docs/安全扫描/[日期]_安全扫描报告.md
```

### Markdown 报告结构

```markdown
# 安全扫描报告

## 概览
- 扫描时间: YYYY-MM-DD HH:MM
- 项目: [项目名]
- 安全评分: XX/100
- 与上次对比: +X 新增 / -X 已修复 / X 未变

## 漏洞详情

### 🔴 严重漏洞

#### 1. [CWE-89] SQL 注入
- **位置**: `src/api/users.py:45`
- **描述**: 用户输入直接拼接到 SQL 查询中
- **风险**: 攻击者可读取/修改/删除数据库
- **修复代码**:
```python
# Before (危险)
query = f"SELECT * FROM users WHERE id = {user_id}"

# After (安全)
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

## 修复优先级
1. 立即修复严重漏洞
2. 本周修复高危漏洞
3. 计划修复中危漏洞
```

---

## Phase 5: 自动修复

> 自动修复流程、可自动修复的漏洞类型、需人工确认的漏洞类型、工具安装指南详见 `references/security-rules.md`

---

## 危险信号（停止并报告）

- 发现已泄露的生产密钥（立即通知用户轮换）
- 发现已被利用的漏洞痕迹
- 发现恶意代码或后门
- 扫描工具本身报错（可能是对抗性代码）

---

## 与其他 Skills 的关系

```
/clarify → /explore → /design → /plan
                                   ↓
                        /run-plan (开发)
                                   ↓
/scan (代码质量) ←──────→ /security (安全专项)
         │                        │
         └────────────┬───────────┘
                      ↓
                   /check
                      ↓
                    /qa
                      ↓
                   /ship
```

---

## 完成检查清单

- [ ] 工具环境已检测
- [ ] SAST 扫描已完成 (Bandit/Semgrep)
- [ ] 密钥扫描已完成 (Gitleaks)
- [ ] 依赖扫描已完成 (pip-audit/npm audit)
- [ ] AI 语义分析已完成
- [ ] OWASP Top 10 已覆盖
- [ ] 每个漏洞有修复代码
- [ ] 报告已保存到 `docs/安全扫描/`

---

## ⛔ 铁律约束

| 约束 | 要求 |
|------|------|
| **工具优先** | 必须优先尝试专业工具，降级需用户确认且标注不完整 |
| **修复完整** | 每个漏洞必须附可执行的修复代码 |
| **不隐瞒** | 发现严重漏洞必须立即报告，禁止淡化 |
| **报告位置** | 必须保存到 `docs/安全扫描/` 目录（自动创建） |
| **修复安全** | 自动修复前必须展示 diff 预览，用户确认后才应用 |

### 报告目录处理

保存报告前自动创建目录：
```bash
mkdir -p docs/安全扫描
```

如果项目根目录没有 `docs/` 文件夹，先创建完整路径。

---

## ✅ 完成提示

```
✅ 安全扫描完成

🛡️ 安全评分: XX/100
   🔴 严重: X 个
   🟠 高危: X 个
   🟡 中危: X 个
   🔵 低危: X 个

📄 报告: docs/安全扫描/[日期]_安全扫描报告.md

🎯 下一步:
1. 立即修复严重漏洞（必须在发布前）
2. 使用 /security fix 自动修复高置信度问题
3. 人工复核业务逻辑相关漏洞
```
