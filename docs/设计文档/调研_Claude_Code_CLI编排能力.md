# 调研：Claude Code CLI 编排能力

> **调研日期**：2026-02-13
> **Claude Code 版本**：2.1.39
> **调研目标**：评估通过 Claude Code CLI 实现自动化研发流程编排的可行性
> **预期流程**：需求澄清 → design → plan → run-plan → check → qa → fix（循环）→ ship

---

## R1: Claude Code CLI 多会话脚本编排

### 1.1 非交互式运行

**结论：完全支持**

`-p` / `--print` 参数支持非交互式运行，执行完毕直接退出，适合脚本编排。

```bash
# 基本用法
claude -p "你的提示词"

# 管道输入
cat requirements.md | claude -p "分析这个需求文档"

# 命令替换嵌入文件内容
claude -p "$(cat docs/plan.md) 请执行这个计划"
```

**本地验证结果**：

```
$ claude -p "echo test"
→ 输出: test（正常退出，exit code 0）

$ echo "What is 2+2?" | claude -p --output-format json
→ 输出: {"type":"result","subtype":"success","is_error":false,"result":"4","session_id":"cb646d3a-..."}
```

**证据来源**：
- 官方文档: https://code.claude.com/docs/en/headless
- 本地实测验证

### 1.2 Headless Mode

**结论：完全支持**

`-p` 模式即为 headless mode（官方已将 "headless mode" 统一命名为 "Agent SDK CLI"）。特性：

- 跳过工作区信任对话框
- 不显示交互式 UI
- 直接输出结果并退出
- 支持所有 CLI 参数

### 1.3 Shell 脚本串联多次独立会话

**结论：完全支持**

每次 `claude -p` 调用默认为全新、独立的会话。串联调用示例：

```bash
# 方式 A：通过文档传递（推荐）
claude -p "设计数据库模型，写入 docs/design.md" --allowedTools "Read,Write,Edit"
claude -p "读取 docs/design.md，编写开发计划，写入 docs/plan.md" --allowedTools "Read,Write,Edit"
claude -p "读取 docs/plan.md，执行开发" --allowedTools "Read,Write,Edit,Bash"

# 方式 B：通过管道/变量传递
design=$(claude -p "设计数据库模型")
claude -p "基于以下设计写计划: $design"
```

**推荐方式 A**：通过文件传递，避免 prompt 过大导致 token 浪费。

### 1.4 读取文件作为输入

**结论：部分支持（无直接参数，但有等效方式）**

没有 `--input-file` 这样的直接参数，但有多种等效方式：

| 方式 | 命令 | 适用场景 |
|------|------|---------|
| 管道输入 | `cat file.md \| claude -p "分析"` | 单文件输入 |
| 命令替换 | `claude -p "$(cat file.md) 请分析"` | 需嵌入 prompt |
| system prompt 文件 | `--system-prompt-file ./prompt.txt` | 替换整个 system prompt |
| 追加 system prompt 文件 | `--append-system-prompt-file ./rules.txt` | 追加指令到默认 prompt |
| prompt 中指定路径 | `claude -p "读取 docs/x.md 并分析"` | 让 Claude 主动读取（推荐） |

`--system-prompt-file` 和 `--append-system-prompt-file` 仅在 `-p` 模式下有效。

### 1.5 SDK / API 程序化调用

**结论：完全支持**

Anthropic 提供官方 **Claude Agent SDK**，支持 Python 和 TypeScript 两种语言。

**Python 安装与使用**：

```bash
pip install claude-agent-sdk
```

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find and fix the bug in auth.py",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Bash"],
            permission_mode="acceptEdits",
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

**TypeScript 安装与使用**：

```bash
npm install @anthropic-ai/claude-agent-sdk
```

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Find and fix the bug in auth.py",
  options: { allowedTools: ["Read", "Edit", "Bash"] }
})) {
  if ("result" in message) console.log(message.result);
}
```

**SDK 额外能力**：

- 会话管理（resume / fork session）
- 子代理（subagents）定义与调度
- Hook 回调（PreToolUse / PostToolUse / Stop）
- MCP 服务器集成
- 自定义工具（`@tool` 装饰器）
- 结构化输出（JSON Schema）

**证据来源**：
- 官方文档: https://platform.claude.com/docs/en/agent-sdk/overview
- Python SDK: https://github.com/anthropics/claude-agent-sdk-python
- TypeScript SDK: https://github.com/anthropics/claude-agent-sdk-typescript

### 1.6 `--continue` 和 `--resume`

**结论：完全支持**

| 参数 | 功能 | 示例 |
|------|------|------|
| `-c` / `--continue` | 继续当前目录最近的会话 | `claude -c -p "继续"` |
| `-r` / `--resume <id>` | 恢复指定 session ID 的会话 | `claude -r "abc123" -p "继续"` |
| `--fork-session` | 恢复时创建新分支（不修改原会话） | `claude --resume abc --fork-session` |
| `--session-id <uuid>` | 指定特定 UUID 作为会话 ID | `claude --session-id "550e..."` |
| `--no-session-persistence` | 不保存会话到磁盘 | `claude -p "任务" --no-session-persistence` |

**跨会话编排的关键模式**（需要时可选用，但编排方案中推荐独立会话）：

```bash
session_id=$(claude -p "开始审查" --output-format json | jq -r '.session_id')
claude -p "继续审查数据库部分" --resume "$session_id"
```

---

## R2: 上下文管理

### 2.1 每次 `-p` 调用是否全新上下文

**结论：是，默认全新上下文**

每次 `claude -p` 调用创建全新会话，拥有独立上下文。会话之间不共享任何对话历史。这是编排方案的理想特性——天然隔离。

### 2.2 完全隔离上下文

**结论：默认即隔离，可进一步强化**

不使用 `--continue` 或 `--resume` 时，每次调用完全隔离。额外强化措施：

| 措施 | 参数 | 说明 |
|------|------|------|
| 禁止会话持久化 | `--no-session-persistence` | 不保存会话到磁盘 |
| 指定独立 session ID | `--session-id <uuid>` | 显式标识每个步骤的会话 |
| 不使用 --continue/--resume | 默认行为 | 不传这两个参数即可 |

### 2.3 确保每次调用加载特定文件

**结论：支持多种方式**

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| prompt 中指定路径 | 让 Claude 用 Read 工具读取 | 编排方案推荐方式 |
| 管道输入 | `cat file \| claude -p` | 单文件、内容不大时 |
| 命令替换 | `claude -p "$(cat file)"` | 嵌入 prompt 中 |
| `--append-system-prompt-file` | 从文件加载追加指令 | 固定规则/约束 |
| `--system-prompt-file` | 从文件替换整个 system prompt | 完全自定义行为 |
| `CLAUDE.md` | Claude Code 自动加载项目根目录的 CLAUDE.md | 项目级约束 |
| `--add-dir` | 添加额外目录供 Claude 访问 | 跨目录访问 |

**编排方案推荐模式**：每步将上一步的输出文档路径通过 prompt 传递，让 Claude 主动读取。这样做的好处是避免 prompt 过大（节省 token），同时 Claude 可按需读取文件的特定部分。

```bash
claude -p "请读取 docs/design.md，然后基于设计文档编写开发计划，输出到 docs/plan.md" \
  --allowedTools "Read,Write,Edit,Bash,Glob,Grep"
```

---

## R3: 异常检测

### 3.1 退出码机制

**结论：部分可靠，需配合 JSON 输出做双重检测**

| 场景 | 退出码 | 验证方式 |
|------|--------|---------|
| 正常完成 | `0` | 本地实测确认 |
| API 错误 / CLI 崩溃 | `1` | 官方文档 + 社区报告 |
| `--max-turns` 超限 | `0`（文档描述为 exits with error，但实测退出码仍为 0） | 本地实测确认 |
| `timeout` 命令超时 | `124` | shell timeout 标准行为 |
| CLI 挂死（已知 Bug） | 无退出码（进程卡死不退出） | 社区报告 |

**JSON 输出中的错误字段**（更可靠的检测方式）：

```json
// 成功
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": 2847,
  "num_turns": 4,
  "total_cost_usd": 0.034,
  "result": "响应文本...",
  "session_id": "abc-123"
}

// 失败
{
  "type": "result",
  "subtype": "error_during_execution",
  "is_error": true,
  "errors": ["API returned no messages"]
}
```

**推荐做法**：同时检查退出码 + JSON 字段：

```bash
output=$(timeout 600 claude -p "task" --output-format json 2>&1)
exit_code=$?

# 超时检测
if [[ $exit_code -eq 124 ]]; then
    echo "超时"
fi

# CLI 错误检测
if [[ $exit_code -ne 0 ]]; then
    echo "CLI 异常退出: $exit_code"
fi

# JSON 错误检测（退出码为 0 时也要检查）
is_error=$(echo "$output" | jq -r '.is_error // "true"')
subtype=$(echo "$output" | jq -r '.subtype // "unknown"')
if [[ "$is_error" == "true" ]]; then
    echo "执行失败: $subtype"
fi
```

### 3.2 异常检测手段

**结论：需要多层防护**

| 异常类型 | 检测方式 | 说明 |
|---------|---------|------|
| API 错误 | `exit_code != 0` 或 `is_error == true` | 双重检测 |
| 进程超时 | shell `timeout` 命令包裹 | 必须使用，CLI 有已知挂死 Bug |
| 上下文溢出 | JSON 中的 `stop_reason` 字段 | 检查是否为非正常停止 |
| 费用超限 | `--max-budget-usd` 参数 | 内置防护 |
| 轮次超限 | `--max-turns` 参数 | 内置防护，但退出码仍为 0 |
| 进程挂死 | `timeout` 命令强制终止后检测退出码 124 | 已知 Bug 的防护措施 |

**已知风险**：Claude CLI 存在间歇性挂死 Bug，在长时间运行的脚本中可能出现进程无法退出。必须用 `timeout` 命令防护每次调用。

相关 Issues：
- https://github.com/anthropics/claude-code/issues/19060 （CLI freezes with "No messages returned"）
- https://github.com/anthropics/claude-code/issues/24478 （CLI freeze requiring SIGKILL）
- https://github.com/anthropics/claude-code/issues/19498 （"No messages returned" crash in --print mode）

### 3.3 执行日志和状态

**结论：支持多种日志/监控方式**

| 方式 | 参数 | 说明 |
|------|------|------|
| 详细日志 | `--verbose` | turn-by-turn 日志输出 |
| 调试日志 | `--debug [filter]` | 按类别过滤（如 `"api,hooks"`） |
| 调试日志写文件 | `--debug-file <path>` | 写入指定路径 |
| JSON 结构化输出 | `--output-format json` | 含 `duration_ms`, `num_turns`, `total_cost_usd` |
| 流式 JSON | `--output-format stream-json` | 实时输出每个事件 |

---

## R4: 实际可行的编排方案

### 方案对比

| 方案 | 可行性 | 优势 | 劣势 |
|------|--------|------|------|
| **Shell 脚本 + `claude -p`** | 高 | 简单直接，无额外依赖，可立即使用 | 错误处理相对粗糙，CLI 挂死风险需 timeout 防护 |
| **Python Agent SDK** | 最高 | 原生 async/await，精细错误处理，session 管理 | 需安装 SDK，代码量更多 |
| **现有 auto-dev.sh 改造** | 中 | 已有基础可复用 | 单会话大 prompt 模式，非多会话编排 |

### 推荐方案：Shell 脚本编排

核心思路：每个环节独立 `claude -p` 调用 + JSON 输出检测 + `timeout` 防护 + 文档留痕。

#### 关键设计决策

| 决策 | 原因 |
|------|------|
| `timeout` 包裹每次调用 | 防止已知 CLI 挂死 Bug |
| `--output-format json` | 可靠解析 `is_error`、`subtype`、`cost`、`duration` |
| `--no-session-persistence` | 确保每步完全独立 |
| `--max-budget-usd` | 防止单步费用失控 |
| 文档路径写入 prompt（非管道） | 让 Claude 主动读取文件，避免 prompt 过大 |
| QA 结果使用 `--json-schema` | 结构化判定 PASS/FAIL，比文本匹配更可靠 |
| ship 步骤需用户确认 | 不可逆操作必须人工确认 |
| skills（`/design` 等）不可用 | `-p` 模式下 slash commands 不可用，需在 prompt 中描述等效任务 |

#### 完整脚本草案

```bash
#!/bin/bash
# dev-pipeline.sh - 研发流程自动化编排
# 流程: design -> plan -> run-plan -> check -> qa -> fix(循环) -> ship
# 每个环节独立上下文，通过文档传递信息
#
# 用法:
#   ./dev-pipeline.sh --prd <需求文档> --name <功能名> [选项]
#
# 选项:
#   --timeout <秒>     每步超时（默认: 600）
#   --budget <美元>    每步预算（默认: 5.00）
#   --max-fix <次数>   最大修复循环（默认: 10）
#   --model <model>    指定模型（默认: opus）

set -euo pipefail

# ===== 配置 =====
PROJECT_ROOT="$(pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"
PRD_FILE=""
FEATURE_NAME=""
MAX_FIX_ITERATIONS=10
STEP_TIMEOUT=600
STEP_BUDGET=5.00
MODEL="opus"
LOG_FILE="$PROJECT_ROOT/.claude/pipeline.log"
PERMISSION_MODE="bypassPermissions"
ALLOWED_TOOLS="Read,Write,Edit,Bash,Glob,Grep"

# ===== 颜色 =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ===== 参数解析 =====
while [[ $# -gt 0 ]]; do
    case $1 in
        --prd)       PRD_FILE="$2"; shift 2 ;;
        --name)      FEATURE_NAME="$2"; shift 2 ;;
        --timeout)   STEP_TIMEOUT="$2"; shift 2 ;;
        --budget)    STEP_BUDGET="$2"; shift 2 ;;
        --max-fix)   MAX_FIX_ITERATIONS="$2"; shift 2 ;;
        --model)     MODEL="$2"; shift 2 ;;
        --help|-h)
            echo "用法: $0 --prd <需求文档> --name <功能名> [选项]"
            echo ""
            echo "选项:"
            echo "  --prd <文件>           需求文档路径（必需）"
            echo "  --name <功能名>        功能名称，用于文档命名（必需）"
            echo "  --timeout <秒>         每步超时，默认 600"
            echo "  --budget <美元>        每步预算，默认 5.00"
            echo "  --max-fix <次数>       最大修复循环，默认 10"
            echo "  --model <model>        模型名称，默认 opus"
            exit 0 ;;
        *) echo -e "${RED}未知参数: $1${NC}"; exit 1 ;;
    esac
done

# ===== 参数验证 =====
if [[ -z "$PRD_FILE" ]]; then
    echo -e "${RED}错误: 必须指定 --prd <需求文档>${NC}"
    exit 1
fi
if [[ -z "$FEATURE_NAME" ]]; then
    echo -e "${RED}错误: 必须指定 --name <功能名>${NC}"
    exit 1
fi
if [[ ! -f "$PRD_FILE" ]]; then
    echo -e "${RED}错误: 需求文档不存在: $PRD_FILE${NC}"
    exit 1
fi

# ===== 文档路径定义 =====
DESIGN_DOC="$DOCS_DIR/设计文档/design_${FEATURE_NAME}.md"
PLAN_DOC="$DOCS_DIR/开发文档/plan_${FEATURE_NAME}.md"
CHECK_REPORT="$DOCS_DIR/检查报告/check_${FEATURE_NAME}.md"
QA_REPORT="$DOCS_DIR/验收报告/qa_${FEATURE_NAME}.md"

# ===== 初始化目录 =====
mkdir -p "$DOCS_DIR/设计文档" \
         "$DOCS_DIR/开发文档" \
         "$DOCS_DIR/检查报告" \
         "$DOCS_DIR/验收报告" \
         "$PROJECT_ROOT/.claude"

# ===== 日志函数 =====
log() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" >> "$LOG_FILE"
    echo -e "$1"
}

# ===== 核心：执行单步 =====
# 参数: $1=步骤名 $2=prompt $3=超时秒数（可选）
# 返回: 0=成功 1=错误 2=超时
run_step() {
    local step_name="$1"
    local prompt="$2"
    local timeout_sec="${3:-$STEP_TIMEOUT}"
    local output_file="$PROJECT_ROOT/.claude/step_${step_name}_output.json"

    log "${BLUE}[STEP] ${step_name} 开始${NC}"
    local step_start
    step_start=$(date +%s)

    # 执行 claude -p，独立会话 + JSON 输出 + timeout 防护
    local exit_code=0
    timeout "${timeout_sec}" \
        claude -p "$prompt" \
        --output-format json \
        --model "$MODEL" \
        --permission-mode "$PERMISSION_MODE" \
        --allowedTools "$ALLOWED_TOOLS" \
        --max-budget-usd "$STEP_BUDGET" \
        --no-session-persistence \
        > "$output_file" 2>&1 || exit_code=$?

    # 检测超时（timeout 命令退出码 124）
    if [[ $exit_code -eq 124 ]]; then
        log "${RED}[TIMEOUT] ${step_name} 超时 (${timeout_sec}s)${NC}"
        return 2
    fi

    # 检测 CLI 异常退出
    if [[ $exit_code -ne 0 ]]; then
        log "${RED}[ERROR] ${step_name} 异常退出 (exit code: ${exit_code})${NC}"
        return 1
    fi

    # 检测 JSON 中的 is_error 字段
    local is_error subtype
    is_error=$(jq -r '.is_error // "true"' "$output_file" 2>/dev/null || echo "true")
    subtype=$(jq -r '.subtype // "unknown"' "$output_file" 2>/dev/null || echo "unknown")

    if [[ "$is_error" == "true" ]]; then
        local error_msg
        error_msg=$(jq -r '.result // "未知错误"' "$output_file" 2>/dev/null || echo "JSON 解析失败")
        log "${RED}[ERROR] ${step_name} 执行失败 (subtype: ${subtype}): ${error_msg:0:200}${NC}"
        return 1
    fi

    # 记录成本和耗时
    local cost duration_ms
    cost=$(jq -r '.total_cost_usd // 0' "$output_file" 2>/dev/null || echo "0")
    duration_ms=$(jq -r '.duration_ms // 0' "$output_file" 2>/dev/null || echo "0")
    local wall_sec=$(( $(date +%s) - step_start ))

    log "${GREEN}[OK] ${step_name} 完成 (API: $((duration_ms/1000))s, 实际: ${wall_sec}s, 费用: \$${cost})${NC}"
    return 0
}

# ===== 暂停等待用户 =====
pause_for_user() {
    local message="$1"
    log "${YELLOW}[PAUSE] ${message}${NC}"
    echo ""
    echo -e "${YELLOW}====== 需要人工介入 ======${NC}"
    echo -e "$message"
    echo ""
    read -rp "解决后按 Enter 继续，输入 q 退出: " response
    if [[ "$response" == "q" ]]; then
        log "${RED}[ABORT] 用户选择退出${NC}"
        exit 1
    fi
}

# ===== 检查文档是否生成 =====
assert_file_exists() {
    local filepath="$1"
    local step_name="$2"
    if [[ ! -f "$filepath" ]]; then
        pause_for_user "${step_name} 的输出文档未生成: $filepath"
    fi
}

# ===== 流程开始 =====
pipeline_start=$(date +%s)

log "${GREEN}================================================${NC}"
log "${GREEN}  研发流程启动: ${FEATURE_NAME}${NC}"
log "${GREEN}================================================${NC}"
log "需求文档:     $PRD_FILE"
log "设计文档路径: $DESIGN_DOC"
log "计划文档路径: $PLAN_DOC"
log "检查报告路径: $CHECK_REPORT"
log "验收报告路径: $QA_REPORT"
log "最大修复循环: $MAX_FIX_ITERATIONS"
log "每步超时:     ${STEP_TIMEOUT}s"
log "每步预算:     \$${STEP_BUDGET}"

# ----- Step 1: Design -----
run_step "design" "
你是架构师。请完成以下架构设计工作。

## 输入
- 需求文档: ${PRD_FILE}（请用 Read 工具读取）

## 任务
1. 读取需求文档，理解功能需求
2. 进行架构设计：模块划分、接口定义、数据模型、技术选型
3. 遵循项目 CLAUDE.md 中的技术栈约定

## 输出
- 将设计文档写入: ${DESIGN_DOC}
- 文档包含：模块划分、接口设计、数据模型、技术选型理由
" || pause_for_user "Design 阶段失败，请检查日志后重试"

assert_file_exists "$DESIGN_DOC" "Design"

# ----- Step 2: Plan -----
run_step "plan" "
你是 Tech Lead。请编写详细开发计划。

## 输入
- 需求文档: ${PRD_FILE}（请用 Read 工具读取）
- 设计文档: ${DESIGN_DOC}（请用 Read 工具读取）

## 任务
1. 读取需求文档和设计文档
2. 编写开发计划：任务拆分、依赖关系、文件边界、执行顺序
3. 每个任务标明验收标准（AC）

## 输出
- 将计划文档写入: ${PLAN_DOC}
- 每个任务包含：描述、关联文件、依赖、AC
" || pause_for_user "Plan 阶段失败，请检查日志后重试"

assert_file_exists "$PLAN_DOC" "Plan"

# ----- Step 3: Run Plan -----
run_step "run-plan" "
你是开发者。请执行开发计划中的所有任务。

## 输入
- 计划文档: ${PLAN_DOC}（请用 Read 工具读取）
- 设计文档: ${DESIGN_DOC}（请用 Read 工具读取）

## 任务
1. 读取计划文档，按顺序执行所有开发任务
2. 遵循 TDD：先写测试再写实现
3. 每完成一个任务执行 git commit
4. 遵循项目 CLAUDE.md 中的编码规范

## 注意
- 每个功能点必须有测试覆盖
- 禁止 Mock 测试
- 禁止硬编码
" 900 || pause_for_user "Run-Plan 阶段失败，请检查日志后重试"

# ----- Step 4: Check -----
run_step "check" "
你是代码审查员。请对代码进行全面检查。

## 输入
- 计划文档: ${PLAN_DOC}（请用 Read 工具读取，核对任务完成度）

## 任务
1. 运行全量测试（pytest -v 或 npm test）
2. 运行 lint 检查（ruff / eslint）
3. 运行类型检查（mypy / tsc）
4. 检查代码质量：函数长度 <=40 行、参数 <=5 个、嵌套 <=3 层
5. 检查是否有空 catch、裸 except、硬编码

## 输出
- 将检查报告写入: ${CHECK_REPORT}
- 报告结论必须标注 PASS 或 FAIL
- 如果 FAIL，列出所有失败项
" || pause_for_user "Check 阶段失败，请检查日志后重试"

assert_file_exists "$CHECK_REPORT" "Check"

# ----- Step 5+6: QA + Fix 循环 -----
fix_iteration=0

while [[ $fix_iteration -lt $MAX_FIX_ITERATIONS ]]; do
    # --- QA ---
    run_step "qa_${fix_iteration}" "
你是 QA 工程师。请执行验收测试。

## 输入
- 需求文档: ${PRD_FILE}（请用 Read 工具读取）
- 检查报告: ${CHECK_REPORT}（请用 Read 工具读取）

## 任务
1. 逐条验证需求文档中的功能点和 AC 是否满足
2. 运行端到端测试
3. 检查 Check 报告中是否还有 FAIL 项

## 输出
- 将验收报告写入: ${QA_REPORT}
- 报告结论必须明确标注 PASS 或 FAIL
- 如果 FAIL，列出所有未通过的项目及原因
" || { pause_for_user "QA 阶段异常"; continue; }

    assert_file_exists "$QA_REPORT" "QA"

    # 判定 QA 结果
    if grep -qi "PASS" "$QA_REPORT" && ! grep -qi "FAIL" "$QA_REPORT"; then
        log "${GREEN}[QA] 验收通过${NC}"
        break
    fi

    fix_iteration=$((fix_iteration + 1))

    if [[ $fix_iteration -ge $MAX_FIX_ITERATIONS ]]; then
        log "${RED}[FAIL] 达到最大修复次数 ($MAX_FIX_ITERATIONS)${NC}"
        pause_for_user "QA 反复不通过（${fix_iteration}次），请人工排查后决定是否继续"
        break
    fi

    log "${YELLOW}[FIX] QA 未通过，第 ${fix_iteration}/${MAX_FIX_ITERATIONS} 次修复${NC}"

    # --- Fix ---
    run_step "fix_${fix_iteration}" "
你是修复工程师。请修复 QA 发现的所有问题。

## 输入
- QA 报告: ${QA_REPORT}（请用 Read 工具读取）
- 检查报告: ${CHECK_REPORT}（请用 Read 工具读取）

## 任务
1. 逐个分析 QA 报告中的 FAIL 项
2. 修复每个问题
3. 修复后运行相关测试验证
4. 每次修复执行 git commit

## 注意
- 这是第 ${fix_iteration} 次修复尝试
- 如果之前的修复方式无效，尝试不同的方案
- 禁止降级：不能通过删除测试或降低标准来"修复"
" || { pause_for_user "Fix 阶段异常"; continue; }

    # --- Re-check ---
    run_step "recheck_${fix_iteration}" "
你是代码审查员。请重新执行全面检查。

## 任务
1. 运行全量测试
2. 运行 lint 和类型检查
3. 检查代码质量

## 输出
- 更新检查报告: ${CHECK_REPORT}
- 结论标注 PASS 或 FAIL
" || { pause_for_user "Re-check 阶段异常"; continue; }

    # 短暂暂停避免 API 限流
    sleep 3
done

# ----- Step 7: Ship（用户确认后执行） -----
log "${GREEN}================================================${NC}"
log "${GREEN}  QA 流程结束，准备交付${NC}"
log "${GREEN}================================================${NC}"
echo ""
echo "文档清单:"
echo "  需求文档: $PRD_FILE"
echo "  设计文档: $DESIGN_DOC"
echo "  计划文档: $PLAN_DOC"
echo "  检查报告: $CHECK_REPORT"
echo "  验收报告: $QA_REPORT"
echo ""

pipeline_end=$(date +%s)
pipeline_minutes=$(( (pipeline_end - pipeline_start) / 60 ))
log "总耗时: ${pipeline_minutes} 分钟"

read -rp "确认执行 ship（创建 PR）？(y/n): " confirm

if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    run_step "ship" "
你是交付工程师。请执行代码交付。

## 任务
1. 确保所有改动已 commit
2. 创建 PR，包含：
   - 标题: feat(${FEATURE_NAME}): 功能描述
   - 描述: 需求概述 + 设计摘要 + 验收结论
3. PR description 使用 markdown 格式

## 输入
- 需求文档: ${PRD_FILE}
- 验收报告: ${QA_REPORT}
" || { pause_for_user "Ship 阶段异常"; }

    log "${GREEN}[DONE] 交付完成${NC}"
else
    log "${YELLOW}[SKIP] 用户取消 ship${NC}"
fi
```

#### 进阶优化：使用 `--json-schema` 提升 QA 判定准确度

QA 步骤可使用 JSON Schema 强制结构化输出，替代文本匹配 PASS/FAIL：

```bash
QA_SCHEMA='{"type":"object","properties":{"passed":{"type":"boolean"},"failures":{"type":"array","items":{"type":"string"}},"summary":{"type":"string"}},"required":["passed","failures","summary"]}'

qa_output=$(timeout "$STEP_TIMEOUT" \
    claude -p "执行 QA 验收..." \
    --output-format json \
    --json-schema "$QA_SCHEMA" \
    --permission-mode "$PERMISSION_MODE" \
    --allowedTools "$ALLOWED_TOOLS")

# 精确判定
passed=$(echo "$qa_output" | jq -r '.structured_output.passed')
if [[ "$passed" == "true" ]]; then
    echo "QA 通过"
else
    failures=$(echo "$qa_output" | jq -r '.structured_output.failures[]')
    echo "QA 失败: $failures"
fi
```

#### 进阶方案：Python Agent SDK 编排

对需要更精细控制的场景，推荐使用 Python Agent SDK：

```python
#!/usr/bin/env python3
"""dev_pipeline.py - 基于 Agent SDK 的研发流程编排"""

import asyncio
import json
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions


async def run_step(step_name: str, prompt: str, tools: list[str] | None = None) -> dict:
    """运行单个流程步骤，返回结果字典"""
    result_text = ""
    session_id = None
    is_error = False

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                allowed_tools=tools or ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
                permission_mode="acceptEdits",
            ),
        ):
            if hasattr(message, "subtype") and message.subtype == "init":
                session_id = message.session_id
            if hasattr(message, "result"):
                result_text = message.result
            if hasattr(message, "is_error") and message.is_error:
                is_error = True
    except Exception as e:
        return {"step": step_name, "error": str(e), "is_error": True}

    return {
        "step": step_name,
        "result": result_text,
        "session_id": session_id,
        "is_error": is_error,
    }


async def main(prd_path: str, feature_name: str, max_fix: int = 10):
    docs = Path("docs")
    design_doc = docs / "设计文档" / f"design_{feature_name}.md"
    plan_doc = docs / "开发文档" / f"plan_{feature_name}.md"
    check_report = docs / "检查报告" / f"check_{feature_name}.md"
    qa_report = docs / "验收报告" / f"qa_{feature_name}.md"

    for d in [design_doc.parent, plan_doc.parent, check_report.parent, qa_report.parent]:
        d.mkdir(parents=True, exist_ok=True)

    # Step 1: Design
    r = await run_step("design", f"读取 {prd_path}，完成架构设计，输出到 {design_doc}")
    if r["is_error"]:
        print(f"Design 失败: {r.get('error', r['result'])}")
        return

    # Step 2: Plan
    r = await run_step("plan", f"读取 {design_doc} 和 {prd_path}，写开发计划到 {plan_doc}")
    if r["is_error"]:
        print(f"Plan 失败: {r.get('error', r['result'])}")
        return

    # Step 3: Run Plan
    r = await run_step("run-plan", f"读取 {plan_doc} 和 {design_doc}，执行所有开发任务")
    if r["is_error"]:
        print(f"Run-Plan 失败: {r.get('error', r['result'])}")
        return

    # Step 4: Check
    r = await run_step("check", f"运行全量测试和代码检查，报告写入 {check_report}")
    if r["is_error"]:
        print(f"Check 失败: {r.get('error', r['result'])}")
        return

    # Step 5+6: QA + Fix 循环
    for i in range(max_fix):
        r = await run_step("qa", f"读取 {prd_path} 和 {check_report}，验收报告写入 {qa_report}")
        if r["is_error"]:
            print(f"QA 异常: {r.get('error', r['result'])}")
            break

        qa_content = qa_report.read_text() if qa_report.exists() else ""
        if "PASS" in qa_content.upper() and "FAIL" not in qa_content.upper():
            print("QA 通过")
            break

        print(f"QA 未通过，第 {i+1} 次修复...")
        await run_step("fix", f"读取 {qa_report}，修复所有 FAIL 项")
        await run_step("recheck", f"重新检查，更新 {check_report}")
    else:
        print(f"达到最大修复次数 ({max_fix})")
        return

    # Step 7: Ship
    confirm = input("确认创建 PR？(y/n): ")
    if confirm.lower() == "y":
        await run_step("ship", f"提交代码并创建 PR，功能名: {feature_name}")


if __name__ == "__main__":
    import sys
    asyncio.run(main(sys.argv[1], sys.argv[2]))
```

**Agent SDK 相比 Shell 脚本的优势**：

| 维度 | Shell 脚本 | Agent SDK |
|------|-----------|-----------|
| 错误处理 | 依赖 exit code + JSON 解析 | 原生 try/except |
| 进程挂死 | 需 timeout 防护 | SDK 内部处理 |
| 消息监控 | 只能看最终结果 | 可监控每个 tool call |
| Hook 集成 | 需配置文件 | 代码内回调函数 |
| 子代理 | 不支持 | 原生支持 AgentDefinition |
| 会话管理 | 手动解析 session_id | 原生 resume / fork |
| 可维护性 | 中 | 高 |

---

## 可行性总结

| 维度 | 结论 |
|------|------|
| **核心可行性** | **完全可行**。`claude -p` + `--output-format json` 提供了脚本编排所需的所有基础能力 |
| **上下文隔离** | **天然支持**。每次 `-p` 调用默认独立会话 |
| **文档传递** | **可行**。通过 prompt 指定文件路径让 Claude 主动读取 |
| **异常检测** | **部分可靠**。JSON 的 `is_error` + `subtype` 检测大部分错误，但需 `timeout` 防护已知挂死 Bug |
| **循环控制** | **可行**。shell while 循环 + QA 结果判定（推荐用 `--json-schema`） |
| **费用控制** | **支持**。`--max-budget-usd` 限制单步费用 |

### 注意事项和已知风险

1. **CLI 挂死风险**：已知 Bug，必须用 `timeout` 命令防护每次调用
2. **Skills 不可用**：`-p` 模式下 `/design`、`/plan` 等 slash commands 不可用，需在 prompt 中描述等效任务
3. **退出码不完全可靠**：`--max-turns` 超限时退出码仍为 0，需依赖 JSON 输出判断
4. **成本累积**：每步独立调用有上下文加载开销，全流程费用 = 各步之和
5. **prompt 质量关键**：每步 prompt 的质量直接决定执行效果，需要反复调试优化

### 推荐路径

- **短期**（快速验证）：Shell 脚本 + `claude -p`，直接可用
- **中期**（生产稳定）：Python Agent SDK，更强的错误处理和可维护性
- **长期**（规模化）：基于 Agent SDK 封装自有编排框架，集成 CI/CD

### 参考资料

- 官方 Headless 文档: https://code.claude.com/docs/en/headless
- CLI 参数参考: https://code.claude.com/docs/en/cli-reference
- Agent SDK 总览: https://platform.claude.com/docs/en/agent-sdk/overview
- Agent SDK Python: https://github.com/anthropics/claude-agent-sdk-python
- Agent SDK TypeScript: https://github.com/anthropics/claude-agent-sdk-typescript
- Hooks 指南: https://code.claude.com/docs/en/hooks-guide
- CLI 挂死 Bug: https://github.com/anthropics/claude-code/issues/19060
- Print 模式崩溃 Bug: https://github.com/anthropics/claude-code/issues/19498
- CLI 冻结 Bug: https://github.com/anthropics/claude-code/issues/24478
