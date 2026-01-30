---
name: auto-dev
command: auto-dev
user_invocable: true
version: 2.0
description: 自动循环开发（往死里干模式）。输入需求文档或 plan 文档，自动执行完整开发链路，循环迭代直到可交付。内置严格 TDD、完成前验证、服务启动验证。效率提升 2-5 倍。
---

# 往死里干（并行自主开发模式）

> **核心理念**：往死里干，不达目标不罢休
> **技术架构**：Coordinator + Worker 模式，最大化并行执行
> **效率提升**：2-5 倍（相比串行）
> **术语约定**：Coordinator = Tech Lead = 主 Agent（协调角色）

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**往死里干**"（主触发词）
- 使用命令：`/auto-dev [文档路径]`
- 说"自动完成所有开发"
- 说"晚上跑完整个开发"
- 说"无人值守开发"

---

## 核心铁律

| 铁律 | 说明 |
|------|------|
| **AC 单一来源** | 验收标准只在 AC 文档定义，后续只能引用不能重新定义 |
| **严格 TDD** | 没有先失败的测试，就没有生产代码 |
| **完成前验证** | 只有亲眼看到验证命令成功，才能声称完成 |
| **服务启动验证** | 必须亲眼看到服务正常启动并响应请求 |
| **文件边界** | 多人协作时，每个开发者只修改分配的文件 |
| **禁止降级** | 只有成功或失败，禁止静默切换备选方案 |
| **禁止 Mock** | 测试必须连接真实数据库和服务，禁止使用 Mock |
| **禁止硬编码** | 密钥/消息/常量必须从配置读取（与 RULES.md 一致） |

---

## 核心优势：并行加速

```
传统串行模式：Phase 1 → Phase 2 → Phase 3 （耗时：6小时）
           ↓
并行模式：Phase 1 ┐
        Phase 2 ├→ 同时执行 （耗时：2小时）
        Phase 3 ┘

效率提升：2-5 倍
```

---

## 执行流程

### 阶段 0：启动与任务拆分

#### 0.1 读取并解析文档

**支持两种启动方式**：

| 方式 | 输入 | 说明 |
|------|------|------|
| 方式 A | plan 文档 | 直接执行，跳过设计阶段 |
| 方式 B | 需求文档 | 先设计再执行 |

```bash
# 路径安全校验（防止路径穿越）
validate_doc_path() {
    local input_path="$1"
    local resolved_path=$(realpath -m "$input_path" 2>/dev/null)
    local project_root=$(pwd)

    # 检查路径穿越
    if [[ "$resolved_path" != "$project_root"* ]]; then
        echo "[ERR_PATH_001] ❌ 安全错误: 路径超出项目目录"
        echo "   输入: $input_path"
        echo "   解析: $resolved_path"
        exit 1
    fi

    # 检查是否在允许的目录内
    if [[ "$resolved_path" != *"/docs/"* ]]; then
        echo "[ERR_PATH_002] ⚠️ 警告: 文档路径应在 docs/ 目录下"
    fi

    echo "$resolved_path"
}

# 空输入处理
if [ -z "$DOC" ]; then
    echo "[ERR_INPUT_001] ⚠️ 未指定文档路径，自动扫描..."
    # 优先查找 plan 文档
    DOC=$(ls docs/开发文档/plan_*.md 2>/dev/null | head -1)
    if [ -z "$DOC" ]; then
        # 其次查找需求文档
        DOC=$(ls docs/需求文档/PRD_*.md 2>/dev/null | head -1)
    fi
    if [ -z "$DOC" ]; then
        echo "[ERR_INPUT_002] ❌ 未找到任何可用文档"
        echo "   请指定文档路径: /auto-dev docs/开发文档/plan_xxx.md"
        exit 1
    fi
    echo "✅ 自动选择文档: $DOC"
fi

# 校验路径
DOC=$(validate_doc_path "$DOC")

# 检查输入文档类型
if [[ "$DOC" == *"plan_"* ]]; then
    echo "✅ 检测到 plan 文档，直接进入执行阶段"
    SKIP_DESIGN=true
else
    echo "✅ 检测到需求文档，需要先完成设计"
    SKIP_DESIGN=false
fi
```

#### 0.2 门控检查（必须通过）

```bash
# 门控 1：AC 文档存在
CLARIFY_DOC=$(ls docs/需求文档/clarify_*.md 2>/dev/null | head -1)
if [ -z "$CLARIFY_DOC" ]; then
    echo "[ERR_GATE_001] ❌ 门控失败: AC 文档不存在"
    echo ""
    echo "🔧 自动修复选项："
    echo "   1. 运行 /clarify 生成 AC 文档（推荐）"
    echo "   2. 手动创建 docs/需求文档/clarify_[功能名].md"
    echo ""
    echo "💡 提示: AC 文档是验收标准的单一来源，必须先定义"

    # 无人值守模式：自动调用 /clarify
    if [ "$AUTO_MODE" = true ]; then
        echo "🤖 无人值守模式：自动调用 /clarify..."
        # 调用 /clarify skill 生成 AC 文档
        # （实际执行时由主 Agent 调用 Skill 工具）
    fi
    exit 1
fi
echo "✅ AC 文档: $CLARIFY_DOC"

# 门控 2（方式 A）：plan 文档存在
if [ "$SKIP_DESIGN" = true ]; then
    PLAN_DOC=$(ls docs/开发文档/plan_*.md 2>/dev/null | head -1)
    if [ -z "$PLAN_DOC" ]; then
        echo "[ERR_GATE_002] ❌ 门控失败: plan 文档不存在"
        echo "   修复: 先运行 /plan 生成实施计划"
        exit 1
    fi
    echo "✅ plan 文档: $PLAN_DOC"
fi

# 门控 3：依赖服务检查（禁止 Mock 铁律配套）
echo "🔍 检查依赖服务可用性..."
check_dependency() {
    local name="$1"
    local check_cmd="$2"
    if ! eval "$check_cmd" > /dev/null 2>&1; then
        echo "[ERR_GATE_003] ❌ 依赖服务不可用: $name"
        echo "   禁止 Mock 铁律要求真实服务必须可用"
        return 1
    fi
    echo "✅ $name 可用"
    return 0
}

# 检测项目类型并验证依赖
if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    # Python 项目常见依赖
    check_dependency "PostgreSQL" "pg_isready -h localhost" || true
    check_dependency "Redis" "redis-cli ping" || true
fi
```

#### 0.3 依赖关系分析（多人协作视角）

**使用 Task 工具调用 Explore agent** 分析：
```
像真实团队一样拆分任务：
- 哪些功能可以分配给不同"开发者"并行？（完整功能，前+后）
- 每个"开发者"负责哪些文件？（确保不重叠）
- 哪些是基础设施？（需要 Tech Lead 先完成）
- 是否有共享资源冲突？（同一文件、同一数据表）

示例：
开发者 Alice → 用户登录功能（login.py, LoginForm.tsx）
开发者 Bob → 用户注册功能（register.py, RegisterForm.tsx）
开发者 Charlie → 密码重置功能（reset.py, ResetForm.tsx）
```

**决策树**：
```
Phase 数量 ≤ 2
    → 不拆分，直接串行执行

Phase 数量 > 2
    ↓
依赖分析
    ↓
    ├─ 所有串行 → 不拆分
    │
    └─ 有并行机会
        ↓
    文件冲突检测
        ↓
        ├─ 严重冲突 → 部分拆分
        │
        └─ 文件独立 ✅
            ↓
        拆分为 N 个 Worker（N = 2-5）
```

#### 0.4 生成执行计划并确认

向用户展示：
```markdown
📋 往死里干模式已激活

目标文档：docs/plan_用户认证系统.md
总计 Phase：5 个

👥 团队分工（多人协作模式）：
┌─────────────────────────────────────────┐
│ 并行开发组（3 个开发者同时工作）        │
├─────────────────────────────────────────┤
│ 👤 开发者 Alice: 用户登录功能           │
│   负责：完整的登录功能（前端+后端）     │
│   文件：src/api/auth/login.py           │
│         src/components/LoginForm.tsx    │
│         tests/auth/test_login.py        │
│                                         │
│ 👤 开发者 Bob: 用户注册功能             │
│   负责：完整的注册功能（前端+后端）     │
│   文件：src/api/auth/register.py        │
│         src/components/RegisterForm.tsx │
│         tests/auth/test_register.py     │
│                                         │
│ 👤 开发者 Charlie: 密码重置功能         │
│   负责：完整的密码重置（前端+后端）     │
│   文件：src/api/auth/reset.py           │
│         src/components/ResetForm.tsx    │
│         tests/auth/test_reset.py        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Tech Lead 工作（串行）                  │
├─────────────────────────────────────────┤
│ Phase 0: 搭建基础设施（前置）           │
│   - 数据库 Schema (users 表)            │
│   - 路由配置                            │
│   - JWT 中间件                          │
│   - Auth Context                        │
│                                         │
│ Phase 4: 集成与验证（后置）             │
│   - 代码合并与冲突检测                  │
│   - 集成测试                            │
│   - 服务启动验证                        │
│   - E2E 测试                            │
└─────────────────────────────────────────┘

执行策略：
- ✅ 协作模式：3 个开发者并行（模拟真实团队）
- ✅ 测试失败必须修复（最多5次）
- ✅ 服务启动验证（确保能正常运行）
- ✅ 并行组统一 commit

确认启动？（输入 yes 开始）
```

#### 0.5 用户确认
- 用户输入 `yes` → 进入无人值守模式
- 用户输入其他 → 询问调整意见

---

### 阶段 1：设计（方式 B 需要，方式 A 跳过）

如果输入是需求文档（非 plan 文档），执行设计阶段：

1. **方案探索**：调研业界最佳实践（至少 5 个来源）
2. **架构设计**：输出模块划分、接口契约、数据模型
3. **设计评审**：批评者视角审查，找出遗漏和风险
4. **写计划**：输出多人协作实施计划
   - 识别可并行的独立功能
   - 分配开发者（Alice/Bob/Charlie）
   - 指定文件范围（避免冲突）
   - **引用 AC 文档**（禁止重新定义）
5. **计划评审**：批评者视角审查计划
6. **保存文档到 docs/ 目录**

---

### 阶段 2：测试先行（TDD 铁律）

> ⚠️ **铁律**：没有测试就没有开发，测试是开发的验收标准

1. **调用 /test-gen 生成 FAILING 测试**
   - 使用 Skill 工具调用：`/test-gen from-clarify <clarify_doc>`
   - /test-gen 会执行并行代码分析和测试生成
   - 包含 Mock 合规检查（禁止 Mock 内部服务）

2. **验证测试文件存在**：`tests/test_[功能名]_acceptance.py`

3. **运行测试确认失败**：符合 TDD 预期

```bash
# 运行测试，必须看到失败
pytest tests/test_*_acceptance.py
# 预期：FAILED（这是正确的，因为还没写实现）
```

**如果 /test-gen 失败**：停止执行，报告失败原因，等待用户决策

**如果跳过此阶段**：后续开发将无法通过 TDD 验证

---

### 阶段 3：Tech Lead 前置工作（串行）

如果有基础设施类 Phase，主 Agent（Tech Lead）先执行：

```
Tech Lead 搭建基础设施

正在创建基础设施：
- ✅ 数据库表 users (src/models/user.py)
- ✅ 路由配置 /api/auth/* (src/api/routes.py)
- ✅ JWT 中间件 (src/middleware/auth.py)
- ✅ Auth Context (src/contexts/AuthContext.tsx)

✅ 基础设施完成，Commit: abc123d

👥 基础就绪，开始派发任务给开发团队...
```

---

### 阶段 4：派发开发者任务（并行，多人协作）

> **Worker 超时配置**：每个 Worker 默认 2 小时超时，超时后自动终止并标记失败。

**关键**：使用 Task 工具同时启动多个 agent，每个扮演一个"开发者"：

```python
# 必须在一个响应中发送多个 Task 工具调用，以实现真正并行
# Worker 超时：2 小时（7200 秒）

Task(
  subagent_type="general-purpose",
  description="开发者 Alice 实现登录功能",
  prompt="""
  你是团队中的**开发者 Alice**，负责实现用户登录功能。

  ⏱️ **超时限制**：2 小时内必须完成，否则任务自动终止

  👤 你的职责：
  - 完整的用户登录功能（前端 + 后端 + 测试）
  - 像一个真实的全栈开发者一样工作

  📁 你负责的文件（只能修改这些）：
  - 后端：src/api/auth/login.py
  - 前端：src/components/LoginForm.tsx
  - 测试：tests/auth/test_login.py
  - ⚠️ 禁止修改其他文件（避免与 Bob、Charlie 冲突）

  📋 任务清单：
  1. 后端实现 POST /api/auth/login
     - 验证邮箱密码
     - 返回 JWT token（⚠️ Secret 从环境变量读取）
  2. 前端实现 LoginForm 组件
     - 表单验证
     - 错误提示
  3. 编写单元测试（登录成功、失败场景）
  4. 测试通过后完成

  🔴 TDD 铁律（必须遵守）：
  - 先运行测试，看到 FAILED
  - 写最小代码让测试通过
  - 看到 PASSED 才算完成
  - 没有先失败的测试 = 删除代码重来

  🔴 禁止 Mock 铁律：
  - 测试必须连接真实数据库
  - 禁止 mock.patch 或 jest.mock

  🎯 完成前验证（必须执行）：
  - 亲眼看到 pytest 输出 PASSED
  - 亲眼看到服务能正常响应
  - "应该有效" 不是验证，必须运行命令

  📝 完成后输出：
  - 在 docs/notes_alice.md 记录开发日志
  - 在 docs/result_alice.md 记录结果报告
  """
)

Task(
  subagent_type="general-purpose",
  description="开发者 Bob 实现注册功能",
  prompt="""
  你是团队中的**开发者 Bob**，负责实现用户注册功能。
  你与 Alice、Charlie 并行工作，互不干扰。

  📁 你负责的文件（只能修改这些）：
  - 后端：src/api/auth/register.py
  - 前端：src/components/RegisterForm.tsx
  - 测试：tests/auth/test_register.py
  - ⚠️ 禁止修改其他文件

  （TDD 铁律、完成前验证 同 Alice）

  📝 完成后输出到 docs/notes_bob.md 和 docs/result_bob.md
  """
)

Task(
  subagent_type="general-purpose",
  description="开发者 Charlie 实现密码重置",
  prompt="""
  你是团队中的**开发者 Charlie**，负责实现密码重置功能。
  你与 Alice、Bob 并行工作，互不干扰。

  📁 你负责的文件（只能修改这些）：
  - 后端：src/api/auth/reset.py
  - 前端：src/components/ResetForm.tsx
  - 测试：tests/auth/test_reset.py
  - ⚠️ 禁止修改其他文件

  （TDD 铁律、完成前验证 同 Alice）

  📝 完成后输出到 docs/notes_charlie.md 和 docs/result_charlie.md
  """
)
```

**重要**：必须在一个响应中发送多个 Task 工具调用，以实现真正并行。

---

### 阶段 5：Tech Lead 后置工作（集成 + 服务验证）

所有开发者完成后，Tech Lead 负责集成和验证：

#### 5.1 收集开发者成果

读取各开发者的输出文档：
- `docs/notes_alice.md`：Alice 的开发日志
- `docs/result_alice.md`：Alice 的成果报告
- 同理 Bob、Charlie

#### 5.2 代码合并与冲突检测

**文件边界技术强制**：

> 依赖 Worker 自律不可靠，需要技术手段强制

**⭐ 方案 A：Git Worktree 隔离（默认推荐）**

> 适用场景：所有项目（最安全的隔离方式）

```bash
# 每个 Worker 在独立 worktree 中工作，物理隔离
git worktree add ../worktree-alice feature-alice
git worktree add ../worktree-bob feature-bob
git worktree add ../worktree-charlie feature-charlie

# Worker 只能在自己的 worktree 中工作
# 合并时由 Tech Lead 统一处理
```

**方案 B：Pre-commit Hook 检查（备选）**

> 适用场景：无法使用 worktree 时（如 CI 环境、磁盘空间受限）

```bash
# 在 .git/hooks/pre-commit 中添加：
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# [ERR_BOUNDARY_001] 检查当前 Worker 是否修改了他人的文件

WORKER="${WORKER_ID:-$(git config user.name)}"  # 优先使用环境变量
ALLOWED_FILES=""

case "$WORKER" in
    "Alice") ALLOWED_FILES="src/api/auth/login.py|src/components/LoginForm.tsx|tests/auth/test_login.py" ;;
    "Bob") ALLOWED_FILES="src/api/auth/register.py|src/components/RegisterForm.tsx|tests/auth/test_register.py" ;;
    "Charlie") ALLOWED_FILES="src/api/auth/reset.py|src/components/ResetForm.tsx|tests/auth/test_reset.py" ;;
esac

if [ -n "$ALLOWED_FILES" ]; then
    MODIFIED=$(git diff --cached --name-only)
    for file in $MODIFIED; do
        if ! echo "$file" | grep -qE "^($ALLOWED_FILES|docs/notes_|docs/result_)"; then
            echo "[ERR_BOUNDARY_001] ❌ 错误: $WORKER 不允许修改 $file"
            exit 1
        fi
    done
fi
EOF
chmod +x .git/hooks/pre-commit
```

**方案选择决策**：
| 条件 | 选择 |
|------|------|
| 默认 | 方案 A（Worktree） |
| CI/CD 环境 | 方案 B（Hook） |
| 磁盘空间 < 500MB | 方案 B（Hook） |
| 项目有自定义 hook | 方案 A（避免覆盖） |

**合并时检查**：

```bash
# 检查是否有开发者意外修改了他人的文件
Alice 的文件：src/api/auth/login.py, src/components/LoginForm.tsx
Bob 的文件：src/api/auth/register.py, src/components/RegisterForm.tsx
Charlie 的文件：src/api/auth/reset.py, src/components/ResetForm.tsx

→ 无重叠 ✅（多人协作视角拆分的优势）
```

冲突处理：
- 无冲突 → 自动合并 ✅
- Import/依赖冲突 → Tech Lead 自动调整
- 逻辑冲突 → 生成报告，停止执行，等待用户

#### 5.3 服务启动验证（铁律）

> ⚠️ **重要**：以下脚本必须在**单次 Bash 调用**中完整执行，否则 PID 变量会丢失。

```bash
#!/bin/bash
# 服务启动验证脚本 - 必须作为整体执行

set -e  # 遇错即停

# 配置
MAX_WAIT=30          # 最大等待秒数
POLL_INTERVAL=2      # 轮询间隔
BACKEND_PORT=8000
FRONTEND_PORT=3000
CURL_TIMEOUT=10      # curl 超时秒数

# 端口占用检测
check_port_available() {
    local port=$1
    if lsof -i ":$port" > /dev/null 2>&1; then
        echo "[ERR_PORT_001] ❌ 端口 $port 已被占用"
        lsof -i ":$port" | head -5
        echo ""
        echo "🔧 修复建议："
        echo "   1. 停止占用进程: kill \$(lsof -t -i:$port)"
        echo "   2. 或使用其他端口: BACKEND_PORT=8001 /auto-dev ..."
        return 1
    fi
    echo "✅ 端口 $port 可用"
    return 0
}

# 辅助函数：轮询等待服务就绪（带超时和重定向限制）
wait_for_service() {
    local url=$1
    local waited=0
    echo "⏳ 等待服务就绪: $url"
    while [ $waited -lt $MAX_WAIT ]; do
        if curl --max-time $CURL_TIMEOUT --max-redirs 3 -sf "$url" > /dev/null 2>&1; then
            echo "✅ 服务就绪 (${waited}s)"
            return 0
        fi
        sleep $POLL_INTERVAL
        waited=$((waited + POLL_INTERVAL))
        echo "   等待中... ${waited}/${MAX_WAIT}s"
    done
    echo "[ERR_SERVICE_001] ❌ 服务启动超时 (${MAX_WAIT}s)"
    return 1
}

# 清理函数（确保清理所有子进程）
cleanup() {
    echo "🧹 清理进程..."
    # 使用进程组 kill 确保清理子进程
    [ -n "$BACKEND_PID" ] && kill -- -$BACKEND_PID 2>/dev/null || kill $BACKEND_PID 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill -- -$FRONTEND_PID 2>/dev/null || kill $FRONTEND_PID 2>/dev/null || true
}
trap cleanup EXIT

# 0. 端口占用检测
check_port_available $BACKEND_PORT || exit 1
check_port_available $FRONTEND_PORT || true  # 前端端口可选

# 1. 启动后端服务（绑定 127.0.0.1 而非 0.0.0.0）
echo "🚀 启动后端服务..."
if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    python -m uvicorn app.main:app --host 127.0.0.1 --port $BACKEND_PORT &
    BACKEND_PID=$!
elif [ -f "package.json" ]; then
    npm run dev &
    BACKEND_PID=$!
fi

# 2. 轮询等待后端就绪
if ! wait_for_service "http://127.0.0.1:${BACKEND_PORT}/health"; then
    echo "❌ 后端服务启动失败"
    tail -n 50 logs/error.log 2>/dev/null || echo "无日志文件"
    exit 1
fi
echo "✅ 后端服务启动成功"

# 3. 启动前端服务（如果有）
if [ -f "package.json" ] && grep -q '"start"' package.json; then
    echo "🚀 启动前端服务..."
    npm start &
    FRONTEND_PID=$!

    if ! wait_for_service "http://127.0.0.1:${FRONTEND_PORT}/"; then
        echo "❌ 前端服务启动失败"
        exit 1
    fi
    echo "✅ 前端服务启动成功"
fi

# 4. 简单功能验证
echo "🧪 快速功能验证..."
curl -sf -X POST "http://127.0.0.1:${BACKEND_PORT}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' || echo "⚠️ 功能验证返回非200"

echo "✅ 服务启动验证通过"
# cleanup 会在 EXIT trap 中自动执行
```

#### 5.4 暂存变更（不 Commit）

> ⚠️ **注意**：此时只暂存，不 Commit。Commit 在阶段 6 质量检查通过后执行。

```bash
# 暂存所有 Worker 的变更
git add src/api/auth/*.py src/components/*.tsx tests/auth/*.py

# 检查暂存内容
git status
echo "📋 暂存完成，等待质量检查..."
```

---

### 阶段 6：并行质量检查（强制执行）

> ⚠️ **此阶段必须执行，不可跳过**

#### 6.0 检测项目质量工具（前置必做）

```bash
echo "🔍 检测项目质量工具配置..."

# JavaScript/TypeScript 项目
if [ -f "package.json" ]; then
    echo "📦 检测到 package.json"

    # 测试命令
    if grep -q '"test"' package.json; then
        echo "✅ 测试命令: npm test"
        TEST_CMD="npm test"
    fi

    # Lint 命令
    if grep -q '"lint"' package.json; then
        echo "✅ Lint 命令: npm run lint"
        LINT_CMD="npm run lint"
    fi

    # TypeScript
    if [ -f "tsconfig.json" ]; then
        echo "✅ TypeScript: npx tsc --noEmit"
        TYPE_CMD="npx tsc --noEmit"
    fi
fi

# Python 项目
if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    echo "🐍 检测到 Python 项目"

    # pytest
    if [ -d "tests" ] || [ -d "test" ]; then
        echo "✅ 测试命令: pytest"
        TEST_CMD="pytest"
    fi

    # ruff/pylint
    if grep -q "ruff" pyproject.toml 2>/dev/null; then
        echo "✅ Lint 命令: ruff check ."
        LINT_CMD="ruff check ."
    fi

    # mypy
    if grep -q "mypy" pyproject.toml 2>/dev/null; then
        echo "✅ 类型检查: mypy ."
        TYPE_CMD="mypy ."
    fi
fi

# 检测结果判断
if [ -z "$TEST_CMD" ] && [ -z "$LINT_CMD" ]; then
    echo "⚠️ 质量检查阻塞：未找到任何质量工具配置"
    echo "请先配置测试或 Lint 工具"
    exit 1
fi
```

#### 6.1 并行执行质量检查

使用 Task 工具同时启动多个检查 agent：

```python
Task(
    subagent_type="general-purpose",
    description="执行单元测试",
    prompt="执行项目测试，记录通过数、失败数"
)

Task(
    subagent_type="general-purpose",
    description="执行代码规范检查",
    prompt="执行 Lint 检查，记录错误数、警告数"
)

Task(
    subagent_type="general-purpose",
    description="执行类型检查",
    prompt="执行类型检查（TypeScript/mypy），记录错误数"
)
```

#### 6.2 质量检查结果汇总

```
🧪 并行质量检查结果
┌─────────────────┬────────┬─────────────────────────┐
│ 检查项          │ 状态   │ 详情                    │
├─────────────────┼────────┼─────────────────────────┤
│ 单元测试        │ ✅/❌  │ 87/87 通过 或 失败原因  │
│ 集成测试        │ ✅/❌  │ 45/45 通过 或 失败原因  │
│ 代码规范(Lint)  │ ✅/❌  │ 0 错误 或 错误数量      │
│ 类型检查        │ ✅/➖  │ 0 错误 或 不适用        │
│ 测试覆盖率      │ ✅/⚠️  │ ≥80% 或 低于阈值        │
└─────────────────┴────────┴─────────────────────────┘
```

#### 6.2.1 测试覆盖率检查（TDD 配套）

> 强调 TDD 必须配套覆盖率检查，否则 TDD 形同虚设

```bash
# 检测并执行覆盖率检查
echo "📊 检查测试覆盖率..."

COVERAGE_THRESHOLD=80  # 最低覆盖率要求

# Python 项目
if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    pytest --cov=src --cov-report=term --cov-fail-under=$COVERAGE_THRESHOLD
    if [ $? -ne 0 ]; then
        echo "❌ 覆盖率低于 ${COVERAGE_THRESHOLD}%"
        exit 1
    fi
fi

# JavaScript/TypeScript 项目
if [ -f "package.json" ]; then
    # 检查是否配置了覆盖率
    if grep -q '"coverage"' package.json || [ -f "jest.config.js" ]; then
        npm run test -- --coverage --coverageThreshold='{"global":{"lines":'$COVERAGE_THRESHOLD'}}'
    else
        echo "⚠️ 未配置覆盖率检查，建议添加"
    fi
fi
```

#### 6.3 质量检查失败处理

```python
MAX_RETRY = 5  # 与文档描述保持一致

for attempt in range(1, MAX_RETRY + 1):  # 最多 5 次
    print(f"🔧 自动修复尝试 {attempt}/{MAX_RETRY}")

    # 分析失败原因
    analyze_failure()

    # 尝试修复
    apply_fix()

    # 重新运行失败的测试
    result = run_failed_tests()

    if result.passed:
        print("✅ 修复成功")
        break
    else:
        print(f"❌ 尝试 {attempt} 失败")

if not result.passed:
    print("⚠️ 自动修复失败，停止执行")
    print("请人工检查以下测试：")
    print(result.failed_tests)
    exit(1)  # 不能继续
```

#### 6.4 质量通过后统一 Commit

> ⚠️ Commit 必须在质量检查全部通过后执行。如果质量检查失败，不会有脏 Commit。

```bash
git add -A
git commit -m "feat(auto): 完成团队并行开发（3个功能）

团队成员：
- 👤 Alice: 用户登录功能（src/api/auth/login.py）
- 👤 Bob: 用户注册功能（src/api/auth/register.py）
- 👤 Charlie: 密码重置功能（src/api/auth/reset.py）

质量检查：
- 单元测试：全部通过 ✅
- Lint：0 错误 ✅
- 类型检查：0 错误 ✅
- 覆盖率：≥80% ✅

[AUTO-DEV] 往死里干并行模式（多人协作）
相关文档: docs/plan_用户认证系统.md"
```

---

### 阶段 7：生成验收报告

创建 `docs/report_[主题]_验收.md`：

```markdown
# [功能名称] 并行开发验收报告

> 开发模式：往死里干（并行自主开发）
> 报告生成时间：2025-01-26 02:30

---

## 📊 执行概要

| 指标 | 数值 |
|------|------|
| 开始时间 | 2025-01-25 22:00 |
| 结束时间 | 2025-01-26 02:30 |
| 总耗时 | 4.5 小时 |
| 并行度 | 3 个 Worker |
| 效率提升 | 2.7 倍 |

---

## 🚀 并行执行明细

**Worker 1: Alice - 用户登录功能** ✅
- 耗时：1.2 小时
- 文件：src/api/auth/login.py、src/components/LoginForm.tsx
- 测试：12/12 通过

**Worker 2: Bob - 用户注册功能** ✅
- 耗时：2.5 小时（测试修复 2 次）
- 文件：src/api/auth/register.py、src/components/RegisterForm.tsx
- 测试：18/18 通过

**Worker 3: Charlie - 密码重置功能** ✅
- 耗时：2 小时
- 文件：src/api/auth/reset.py、src/components/ResetForm.tsx
- 测试：10/10 通过

---

## 🧪 质量检查

- 单元测试：✅ 40/40 通过
- 集成测试：✅ 5/5 通过
- 代码规范：✅ 0 错误
- 类型检查：✅ 0 错误
- 服务启动：✅ 健康检查通过

---

## ✅ 验收检查清单

- [x] 所有 Phase 已完成
- [x] 所有测试已通过
- [x] 代码质量检查通过
- [x] 无文件冲突
- [x] 服务启动验证通过
- [x] 效率提升：2.7 倍 ✅
```

---

## 完成条件（铁律）

以下条件**全部满足**时才算完成：

```markdown
## 开发质量
- [ ] 遵循了严格 TDD（每个测试都先看到失败）
- [ ] 完成前验证都通过（亲眼看到验证命令成功）
- [ ] 文件边界约束遵守（每个开发者只改自己的文件）

## 自动化验证
- [ ] 所有测试通过（pytest/vitest 输出 PASSED）
- [ ] 无 lint 错误
- [ ] 无类型错误

## 服务验证
- [ ] 服务启动验证通过（亲眼看到服务正常运行）
- [ ] 健康检查端点响应 200
- [ ] 核心 API 能正常响应

## 最终确认
- [ ] 质量检查全部通过
- [ ] 验收报告已生成
- [ ] 输出完成标记：<promise>COMPLETE</promise>
```

---

## 错误处理

### Worker 失败

```
Worker 2 测试失败（尝试 3/5）
    ↓
Worker 2 自动修复
    ↓
仍失败（尝试 5/5）
    ↓
Worker 2 标记为失败，记录到报告
    ↓
其他 Worker 继续执行 ✅
    ↓
所有 Worker 完成后，报告中列出失败的 Worker
```

### 合并冲突

```
检测到文件冲突
    ↓
分析冲突类型
    ↓
    ├─ Import/依赖冲突 → Tech Lead 自动调整
    │
    └─ 逻辑冲突 → 生成冲突报告，停止执行
```

### 致命错误

- 依赖安装失败
- 数据库连接失败
- 文件系统错误
→ 立即停止所有 Worker，生成报告

---

## 退出条件

1. ✅ 所有 Phase 完成 + 质量检查通过
2. ⚠️ 无法解决的合并冲突
3. ⚠️ 多数 Worker 失败（≥50%）
4. 🛑 致命错误

---

## 与其他 Skills 的关系

```
/clarify（需求澄清）→ AC 文档
    ↓
/explore（方案探索）→ 可选
    ↓
/design（架构设计）→ 可选
    ↓
/plan（写计划）→ plan 文档
    ↓
/auto-dev（本 Skill）← 从这里开始执行
    ↓
/check（开发检查）→ 内置于阶段 6
    ↓
/qa（测试验收）→ 可选后续
    ↓
/ship（代码交付）→ 可选后续
```

| Skill | 关系 | 说明 |
|-------|------|------|
| `/clarify` | 前置依赖 | AC 文档必须存在，门控检查会验证 |
| `/explore` | 可选前置 | 方式 B 设计阶段会调用 |
| `/design` | 可选前置 | 方式 B 设计阶段会调用 |
| `/plan` | 前置依赖 | 方式 A 直接使用，方式 B 设计阶段生成 |
| `/test-gen` | 内置调用 | 阶段 2 测试先行，调用 /test-gen from-clarify 生成 FAILING 测试 |
| `/check` | 内置调用 | 阶段 6 质量检查包含 /check 部分能力 |
| `/qa` | 后续可选 | 验收通过后可独立验收 |
| `/ship` | 后续可选 | 验收通过后可交付代码 |

---

## 使用示例

### 示例 1：从 plan 文档启动（推荐）

```
用户：/auto-dev docs/开发文档/plan_用户认证系统.md

Claude：
  📋 往死里干模式已激活

  ✅ 检测到 plan 文档，直接进入执行阶段
  ✅ AC 文档存在：docs/需求文档/clarify_用户认证.md

  分析依赖关系...
  检测到 3 个独立 Phase 可并行执行 ✅

  确认启动？

用户：yes

Claude：
  🔧 Tech Lead 搭建基础设施...
  🚀 启动并行组（3 个 Worker）...

  ✅ Alice 完成（1.2h）
  ✅ Bob 完成（2.5h）
  ✅ Charlie 完成（2h）

  🔗 合并代码... 无冲突 ✅
  🧪 服务启动验证... ✅
  🧪 质量检查... ✅

  🎉 全部完成！
  报告：docs/report_用户认证_验收.md
```

### 示例 2：从需求文档启动

```
用户：往死里干，完成 docs/需求文档/PRD_用户认证.md

Claude：
  📋 往死里干模式已激活

  ✅ 检测到需求文档，需要先完成设计
  ✅ AC 文档存在

  阶段 1：设计中...
  → 方案探索 ✅
  → 架构设计 ✅
  → 写计划 ✅
  → 计划保存：docs/开发文档/plan_用户认证.md

  阶段 2：测试先行...
  → 生成 FAILING 测试 ✅

  阶段 3-7：执行开发...
  （同示例 1）
```

---

## 注意事项

1. **并行不是银弹**：如果 Phase 高度耦合，串行反而更快
2. **拆分需谨慎**：主 Agent 会自动分析依赖，但人工审核 plan 能确保依赖分析准确
3. **冲突有代价**：如果合并冲突复杂，会降低效率
4. **测试要充分**：并行开发更依赖自动化测试

---

## 中断恢复机制

> 长时间运行的任务可能因网络、超时等原因中断，需要恢复能力

### 检查点保存

每个关键阶段完成后，自动保存检查点到 `docs/.checkpoint/`：

> ⚠️ **重要**：必须将 `docs/.checkpoint/` 添加到 `.gitignore`，避免检查点被提交

```bash
# 添加到 .gitignore
echo "docs/.checkpoint/" >> .gitignore

# 检查点文件结构
docs/.checkpoint/
├── stage.json           # 当前阶段
├── workers_status.json  # 各 Worker 状态
├── last_commit.txt      # 最后一次 commit hash
└── version              # 检查点格式版本（用于未来兼容）
```

```json
// stage.json 示例（v1 格式）
{
  "version": 1,
  "current_stage": 4,
  "stage_name": "派发开发者任务",
  "started_at": "2025-01-26T22:00:00Z",
  "workers": ["alice", "bob", "charlie"],
  "completed_workers": ["alice"],
  "auto_resume": true
}
```

### 恢复执行

> **无人值守兼容**：默认自动恢复，无需人工确认

```bash
# 检测是否存在检查点
if [ -f "docs/.checkpoint/stage.json" ]; then
    echo "🔄 检测到未完成的执行"
    echo "   阶段：$(jq -r '.stage_name' docs/.checkpoint/stage.json)"
    echo "   已完成：$(jq -r '.completed_workers | join(", ")' docs/.checkpoint/stage.json)"

    # 检查是否为无人值守模式或自动恢复
    AUTO_RESUME=$(jq -r '.auto_resume // true' docs/.checkpoint/stage.json)

    if [ "$AUTO_RESUME" = "true" ] || [ "$AUTO_MODE" = "true" ]; then
        echo "🤖 自动恢复模式启用，继续执行..."
        RESUME="y"
    else
        # 非自动模式：检查命令行参数
        if [ "$1" = "--no-resume" ]; then
            echo "⏭️ 跳过恢复，重新开始..."
            rm -rf docs/.checkpoint/
            RESUME="n"
        else
            # 默认自动恢复
            echo "🔄 默认自动恢复（使用 --no-resume 可跳过）"
            RESUME="y"
        fi
    fi

    if [ "$RESUME" = "y" ]; then
        CURRENT_STAGE=$(jq -r '.current_stage' docs/.checkpoint/stage.json)
        echo "🔄 从阶段 $CURRENT_STAGE 恢复执行..."
    fi
fi
```

### 恢复流程

```
检测到检查点
    ↓
读取 stage.json
    ↓
    ├─ 阶段 4（Worker 执行中）
    │   → 跳过已完成的 Worker
    │   → 只启动未完成的 Worker
    │
    └─ 其他阶段
        → 从该阶段重新开始
    ↓
完成后删除检查点
```

---

## 性能预期

| 场景 | 并行度 | 效率提升 |
|------|--------|---------|
| 5 个独立功能 | 3-5 Worker | 2-5 倍 |
| 3 个独立功能 | 3 Worker | 2-3 倍 |
| 2 个独立功能 | 2 Worker | 1.5-2 倍 |
| 高度耦合功能 | 串行执行 | 无提升 |

**最佳场景**：
- Phase 数量：3-7 个
- 文件独立性：高
- 依赖关系：少
- 功能耦合：低
