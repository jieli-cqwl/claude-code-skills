# Security Rules Reference

> 本文件从 `SKILL.md` 拆出，包含 OWASP Top 10 规则清单、检测模式、修复建议和工具配置详情。

---

## Phase 1: 环境检测

### 语言检测

| 标识文件 | 语言 | 推荐工具 |
|---------|------|----------|
| `pyproject.toml` / `requirements.txt` | Python | Bandit + pip-audit |
| `package.json` | JavaScript/TypeScript | Semgrep + npm audit + eslint-plugin-security |
| `pom.xml` / `build.gradle` | Java | Semgrep + SpotBugs |
| `go.mod` | Go | Semgrep + govulncheck |
| `Dockerfile` / `docker-compose.yml` | 容器 | Trivy |
| 混合项目 | 多语言 | Semgrep (全栈) + Trivy (容器) |

### 工具检测

检查工具是否已安装，未安装时提示安装命令：

```bash
# Python
pip install bandit pip-audit semgrep gitleaks

# macOS
brew install gitleaks semgrep

# npm
npm install -g snyk
```

---

## Phase 2: 工具扫描

### 2.1 SAST 扫描

**Bandit (Python 专项)**:
```bash
bandit -r . -f json -o bandit_report.json --severity-level medium
```

**Semgrep (多语言)**:
```bash
semgrep scan --config=auto --json -o semgrep_report.json
```

### 2.2 密钥扫描

**Gitleaks**:
```bash
gitleaks detect --source . --report-format json --report-path gitleaks_report.json
```

### 2.3 依赖扫描

**Python**:
```bash
pip-audit --format json --output pip_audit_report.json
```

**Node.js**:
```bash
npm audit --json > npm_audit_report.json
```

### 2.4 容器扫描

**Trivy (Docker 镜像)**:
```bash
trivy image --format json --output trivy_report.json [image_name]
```

**Trivy (Dockerfile)**:
```bash
trivy config --format json --output trivy_config.json .
```

---

## Phase 3: AI 语义分析

工具扫描后，AI 执行以下检查：

### OWASP Top 10 检查清单

| 编号 | 类别 | 检查项 |
|------|------|--------|
| A01 | 访问控制缺陷 | 权限校验缺失、越权访问 |
| A02 | 加密失败 | 明文存储、弱加密算法 |
| A03 | 注入攻击 | SQL/命令/XSS 注入 |
| A04 | 不安全设计 | 业务逻辑漏洞 |
| A05 | 安全配置错误 | 默认配置、调试模式 |
| A06 | 易受攻击组件 | 已知漏洞依赖 |
| A07 | 身份认证失败 | 弱密码、会话管理 |
| A08 | 数据完整性 | 不安全的反序列化 |
| A09 | 日志监控失败 | 敏感信息日志 |
| A10 | SSRF | 服务端请求伪造 |

### 工具无法检测的漏洞

AI 重点检查：
- **业务逻辑漏洞**：如支付绕过、权限提升
- **上下文相关漏洞**：如特定框架的配置问题
- **组合漏洞**：多个低危漏洞组合成高危

### 误报处理

AI 复核工具结果时：
1. **标记误报**：确认为误报的问题标记 `[误报]`，说明原因
2. **降级处理**：风险被高估的问题降低严重程度
3. **记录白名单**：已确认的误报记录到 `.security-ignore`，下次扫描跳过

### `.security-ignore` 文件格式

```yaml
# .security-ignore - 安全扫描白名单
# 格式：每行一条规则，支持以下格式

# 1. 忽略特定文件的特定规则
src/tests/test_auth.py:B101  # 忽略测试文件中的 assert 警告

# 2. 忽略整个文件
src/migrations/*             # 忽略迁移文件

# 3. 忽略特定规则（全局）
RULE:B311                    # 忽略所有 random 模块警告

# 4. 忽略特定行（推荐在代码中使用注释）
# Python: password = "test"  # nosec B105
# JS:     // security-ignore: hardcoded-password

# 5. 带原因的忽略（推荐）
src/config/defaults.py:B105  # 原因：这是默认值模板，不是真实密钥
```

**最佳实践**：
- 每条忽略规则必须注明原因
- 定期审查白名单，移除过期条目
- 白名单应纳入代码审查流程

---

## Phase 5: 自动修复详情

当使用 `/security fix` 时：

### 修复流程（安全优先）

```
/security fix
    ↓
1. 扫描发现漏洞
    ↓
2. 自动创建 git stash（保存当前工作）
    ↓
3. 生成修复预览（不自动应用）
    ↓
4. 展示 diff 供用户确认
    ┌─────────────────────────────────────────────┐
    │ 🔧 修复预览 (1/3)                           │
    │                                             │
    │ 文件: src/api/users.py:45                   │
    │ 漏洞: [CWE-89] SQL 注入                     │
    │                                             │
    │ - query = f"SELECT * FROM users WHERE..."   │
    │ + query = "SELECT * FROM users WHERE %s"    │
    │ + cursor.execute(query, (user_id,))         │
    │                                             │
    │ [Y] 应用  [N] 跳过  [A] 全部应用  [Q] 退出  │
    └─────────────────────────────────────────────┘
    ↓
5. 用户确认后应用修复
    ↓
6. 运行测试验证（如有）
    ↓
7. 如测试失败，自动回滚 (git stash pop)
```

### 可自动修复的漏洞

| 漏洞类型 | 修复方式 | 置信度 |
|---------|---------|--------|
| 硬编码密钥 | 移至环境变量 | 高 |
| SQL 注入 | 参数化查询 | 高 |
| 弱哈希算法 | 替换为安全算法 | 高 |
| 不安全依赖 | 升级到安全版本 | 中 |

### 需人工确认的漏洞

| 漏洞类型 | 原因 |
|---------|------|
| 业务逻辑漏洞 | 需理解业务上下文 |
| 权限控制问题 | 可能影响功能 |
| 配置变更 | 可能影响其他环境 |

---

## 工具安装指南

### 一键安装 (推荐)

```bash
# Python 项目
pip install bandit pip-audit semgrep

# macOS
brew install gitleaks

# 验证安装
bandit --version && semgrep --version && gitleaks version
```

### 工具不可用时的处理

**检测到工具缺失时的交互流程**：

```
⚠️ 检测到以下工具未安装:
   - bandit (SAST 扫描)
   - gitleaks (密钥扫描)

🔧 是否自动安装？
   1. 自动安装 (pip install bandit && brew install gitleaks)
   2. 跳过缺失工具，继续扫描（结果不完整）
   3. 使用降级模式（仅 Grep 扫描，漏报率高）
   4. 取消扫描

请选择 [1/2/3/4]:
```

**降级模式触发条件**（必须同时满足）：
1. 专业工具安装失败或不可用
2. 用户明确选择"降级模式"
3. 报告中必须标注"⚠️ 降级模式：仅使用 Grep 扫描，结果不完整，漏报率高"

**降级模式的 Grep 扫描**：
```bash
# 密钥扫描
grep -rn "password\|secret\|api_key\|token" --include="*.py" .

# SQL 注入
grep -rn "execute.*f\"" --include="*.py" .
```

**铁律说明**："工具优先"铁律的含义是：必须**优先尝试**使用专业工具，而非禁止一切降级。但降级必须是用户主动选择，且结果必须标注不完整。

---

## 常见借口（都是错的）

| 借口 | 现实 |
|------|------|
| "这是内部系统，不需要安全" | 内部系统被攻破后是跳板 |
| "我们有防火墙" | 防火墙不防应用层漏洞 |
| "这个漏洞很难利用" | 自动化工具让利用变得简单 |
| "修复会影响功能" | 安全修复不应改变正常功能 |
| "我们以后再修" | 漏洞每多存在一天风险都在累积 |
