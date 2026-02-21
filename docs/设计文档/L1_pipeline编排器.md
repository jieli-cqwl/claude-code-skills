<!-- L1 模块规格 - 按需加载 -->
<!-- 来源：设计_人机协作模式重建.md 行 280-1146 -->
<!-- 生成日期：2026-02-21 -->

# L1: pipeline.sh 编排器设计

**本模块依赖**：无（编排器是顶层模块）
**本模块被依赖**：所有 SubAgent 由编排器调用、Handoff 文档由编排器验证、进度文件由编排器写入

---

## 1. 角色与职责

`pipeline.sh` 是 bash 脚本，作为整个流程的编排器。

**职责**：
- 确定性流程控制：步骤顺序、文件检查、循环计数、PASS/FAIL 判断，全部在 bash 中执行
- 调用 LLM 执行实际工作：每步通过 `claude -p` 调用对应 SubAgent，传入 Handoff 文件路径
- 异常检测与通知：每步检查退出码和输出文件，异常时发送系统通知
- 并行隔离：通过 feature name 参数和锁文件机制，支持多个 Pipeline 并行

**不做的事**：不解析 Handoff 文件内容、不做质量判断、不理解业务逻辑（全部交给 SubAgent）。

---

## 2. 触发方式

**方式 1（推荐）**：/clarify 完成后自动触发
```
用户完成 /clarify -> Claude 提示"要启动自动开发流程吗？"
用户："开始" -> Claude 通过 Bash 工具后台执行：
nohup ~/.claude/pipeline.sh "用户管理" "$(pwd)" &
```
pipeline.sh 作为独立进程运行，不依赖当前 Claude Code 会话。

**方式 2（备用）**：用户手动命令行
```bash
~/.claude/pipeline.sh "用户管理" /path/to/project
CLI_CMD=claude-codex ~/.claude/pipeline.sh "用户管理" /path/to/project
```

---

## 3. 配置参数

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `FEATURE` | 第一个参数（必填） | 需求名称，限中文/英文/数字/下划线/连字符 |
| `PROJECT_DIR` | `.`（第二个参数） | 项目根目录 |
| `CLI_CMD` | `claude`（环境变量） | CLI 命令，支持 claude / claude-codex / claude-gemini |
| `MAX_FIX` | 10 | QA-Fix 最大修复循环次数 |
| `MAX_REVIEW` | 3（环境变量） | Design-Plan / Plan-Implement 评审最大轮数 |
| `MAX_CHECK_LOOP` | 3（环境变量） | Implement-Check 修复循环最大轮数 |
| `STEP_BUDGET` | 10.00（临时占位） | 单步费用上限（USD），须通过 3 次实测校准 |
| `STEP_TIMEOUT` | 1800 | 单步超时（秒） |
| `TOTAL_STEPS` | 6 | 主步骤数（design/plan/implement/check/qa/fix） |
| `TOTAL_BUDGET` | 200.00（临时占位，环境变量） | 总费用安全网（USD），须通过 3 次实测校准 |
| `START_STEP` | `design`（环境变量） | 断点续传入口：design / implement / qa |
| `HUMAN_CHECKPOINT` | `true`（环境变量） | Design/Plan 人工确认开关（前 10 个需求建议保持开启，积累信心后可关闭） |
| `SKILLS_DIR` | `$HOME/.claude/skills` | Skills 知识层目录 |

---

## 4. 核心函数

### 4.1 notify() / notify_error()

系统通知函数，支持 macOS osascript + Linux notify-send，始终输出到日志。

```bash
notify()       # Glass 音效，正常通知
notify_error() # Basso 音效，错误通知
```

### 4.2 wait_for_confirmation()

人工确认函数，Design/Plan 方向性决策暂停等待用户确认。

- 写入进度状态 `waiting-confirmation`
- 轮询等待确认文件（每 30 秒，最长 24 小时）
- 支持三种响应：`touch` 确认 / `REJECT: 原因` 拒绝 / `pipeline.sh review` 交互式评审
- 超时或拒绝均 exit 1

> 详见 L2 原文 行 367-406

### 4.3 validate_handoff()

Handoff 结构化验证（最低限度格式检查，非质量保证）。

按步骤类型 grep 检查关键词：
- design: 接口/API、多方案对比
- plan: Task 编号、AC、依赖
- implement: commit、测试记录
- check: 测试、Lint、AC 覆盖
- fix: 根因分析

**定位**：最低限度格式兜底，不是质量门控核心。LLM 可轻易满足关键词匹配。质量判断交给 SubAgent 自检 + 评审循环 + 人工确认。

> 详见 L2 原文 行 408-447

### 4.4 check_budget()

费用累计检查。当前为步数 x STEP_BUDGET 估算（待 `claude -p` 支持 cost 输出后升级为实际费用）。超过 TOTAL_BUDGET 时暂停等待人工确认。

### 4.5 update_progress()

进度文件原子写入。先写临时文件（`.tmp.$$`）再 `mv`，防止读取方读到半写入数据。

**进度文件格式**（`.pipeline-progress-{feature}.json`）：
```json
{
  "schema_version": 1,
  "feature": "用户管理",
  "current_step": "implement",
  "step_index": 3,
  "total_steps": 6,
  "status": "running",
  "fix_count": 0,
  "total_cost_usd": 30,
  "elapsed_seconds": 720,
  "started_at": "2026-02-13T15:00:00",
  "updated_at": "2026-02-13T15:12:00",
  "cli_backend": "claude"
}
```

### 4.6 preflight_check()

环境依赖检查：jq（Status Line 解析 JSON）、gtimeout/timeout（进程超时强杀）、setsid（进程组隔离）。缺失任一依赖则阻断启动。

### 4.7 run_with_timeout()

超时执行函数。使用 `setsid` 创建新进程组 + `timeout --signal=KILL` 硬超时，彻底解决子进程孤儿问题。macOS 用 `gtimeout`。

### 4.8 get_permission_mode()

根据 SubAgent 角色确定权限模式：
- Designer/Planner: `plan`（只读，不需要 Bash）
- Implementer/Fixer/Checker/QA: `bypassPermissions`（需要 Bash）

### 4.9 verify_no_code_changes()

事后 diff 校验。只读角色（非 Implementer/Fixer）如果修改了 `docs/pipeline/` 以外的文件，exit 1 强阻断。

### 4.10 run_step()

执行单步的核心函数。流程：
1. update_progress -> running
2. run_with_timeout 调用 `$CLI_CMD -p`，注入 SubAgent prompt + 用户 prompt
3. 检查退出码（非 0 -> failed + notify + exit 1）
4. 检查输出文件存在且非空
5. 检查 Handoff 核心章节标题（输入分析/决策/产出）
6. validate_handoff 结构化验证
7. verify_no_code_changes 事后 diff 校验
8. update_progress -> completed
9. check_budget 费用检查

### 4.11 parse_review()

解析评审 REVIEW 行。从评审文件中提取 `DESIGN_OK/DESIGN_ISSUE` 或 `PLAN_OK/PLAN_ISSUE`，去除 Markdown 格式后 grep 匹配。

### 4.12 run_tests() / parse_result()

pipeline.sh 独立运行测试判定 PASS/FAIL。自动检测项目测试框架（pytest / npm test），退出码 0 = PASS，非 0 = FAIL。

**核心原则**：判定权在编排器，不在 SubAgent。杜绝"自证清白"的虚假完成。

### 4.13 build_prompt()

从 SubAgent 文件中解析 `skills` 字段，自动拼接 Skills 知识层内容。确保自动模式（`claude -p`）与手动模式（`context: fork`）下 SubAgent 获得相同的方法论。

```bash
build_prompt() {
  local agent_file="$1"
  local prompt="$(cat "${AGENTS_DIR}/${agent_file}")"
  local skills=$(sed -n '/^skills:/,/^[^ -]/p' "${AGENTS_DIR}/${agent_file}" | grep '^ *- ' | sed 's/^ *- //')
  for skill in $skills; do
    local skill_file="${SKILLS_DIR}/${skill}/SKILL.md"
    if [ -f "$skill_file" ]; then
      prompt="${prompt}\n\n$(cat "$skill_file")"
    fi
  done
  echo "$prompt"
}
```

---

## 5. 主流程状态机

### 5.1 前置检查

1. feature name 合法性校验（perl 正则，兼容 macOS bash 3.2 Unicode）
2. preflight_check()（jq/gtimeout/setsid）
3. handoff_clarify.md 存在性检查
4. 残留 Handoff 文件检查（handoff_design/plan/run/check/qa/fix_*.md）
5. 锁目录创建（`mkdir` 原子操作，防止同一 feature 并行）
6. `trap 'rm -rf "$LOCK_DIR"' EXIT`

### 5.2 断点续传（START_STEP）

| 入口 | 前置产物要求 | 跳过阶段 |
|------|------------|---------|
| `design` | handoff_clarify.md | 无（从头开始） |
| `implement` | clarify + design + plan 存在，run 不存在 | Design-Plan |
| `qa` | clarify + design + plan + run + check 存在，.check_passed=PASS，qa 不存在 | Design-Plan-Implement-Check |

### 5.3 阶段 1：方向决策

**Design-Plan 评审循环**（最多 MAX_REVIEW 轮）：
1. run_step "design" -> handoff_design.md
2. Planner 评审 -> review_design_N.md
3. parse_review 解析结果
   - DESIGN_OK -> 继续
   - DESIGN_ISSUE -> Designer 修正 -> 重新评审
   - MISSING（无有效 REVIEW 行）-> exit 1（不重试）
4. 超过 MAX_REVIEW 轮 -> exit 1
5. [可选] wait_for_confirmation "design"

**Plan-Implement 评审循环**（最多 MAX_REVIEW 轮）：
1. run_step "plan" -> handoff_plan.md
2. Implementer 评审 -> review_plan_N.md
3. parse_review 解析结果（逻辑同上）
4. [可选] wait_for_confirmation "plan"

### 5.4 阶段 2：执行交付

**Implement-Check 循环**（最多 MAX_CHECK_LOOP 轮）：
1. 记录 Implement 回滚锚点（`git rev-parse HEAD`）
2. run_step "implement" -> handoff_run.md
3. run_step "check" -> handoff_check.md
4. parse_result()（pipeline.sh 独立运行测试）
   - PASS -> 写入 .check_passed 标记，进入 QA
   - FAIL -> run_step "fix-pre-N" -> 重新 Check
5. 超过 MAX_CHECK_LOOP 轮 -> exit 1

### 5.5 阶段 3：验收修复

**QA-Fix 循环**（最多 MAX_FIX 轮）：
1. 调用 QA SubAgent -> handoff_qa.md
2. 非空检查 + 章节标题检查 + verify_no_code_changes
3. check_budget
4. parse_result()（pipeline.sh 独立运行测试）
5. 检查 INFRA_ERROR（服务启动失败/端口占用）-> exit 1（不进入 Fix）
6. PASS -> 通知"QA 验收通过" -> exit 0
7. FAIL -> fix_count++
   - >= 10 -> exit 1
   - >= 5 -> 暂停通知人工介入
   - >= 3 -> 注入历史修复上下文（避免重复方案）
8. run_step "fix-N" -> handoff_fix_N.md
9. run_step "re-check-N" -> handoff_check.md
10. 回到步骤 1

---

## 6. 关键设计决策

| 决策 | 理由 |
|------|------|
| 判定权分离 | PASS/FAIL 在 pipeline.sh 独立运行测试，SubAgent 只描述问题，杜绝"自证清白" |
| 交互式 Design/Plan 确认 | 方向性决策跑偏代价远超代码层面，支持 `pipeline.sh review` 进入上下文对话 |
| 阻断性降级约束 | Handoff 核心缺失一律 `exit 1`，不发 Warning 带病运行 |
| 全进程树防瘫痪 | `timeout --signal=KILL` + `setsid` 替代有僵尸隐患的 perl alarm |
| 费用总控（数据驱动） | STEP_BUDGET/TOTAL_BUDGET 为临时值，须 3 次实测校准（P90 x 1.5/2） |
| 评审循环先执行再审查 | 先输出完整产出物，再审查，保证每轮都有完整可审的文档 |
| 评审输出独立文件 | review_design_N.md 独立文件，修正时可同时读取原需求和评审意见 |
| 断点续传 | START_STEP 环境变量，3 个跨阶段入口，解决长流程中间失败需重跑的痛点 |
| Fix 历史注入 + 升级策略 | >= 3 次注入前几次失败记录；>= 5 次暂停人工介入 |
| 进度文件按 feature 隔离 | 多个 Pipeline 并行时互不覆盖 |
| 自动模式权限按角色分级 | Designer/Planner 用 plan，其余用 bypassPermissions，事后 git diff 校验 |
| Check/QA PASS/FAIL 判定 | pipeline.sh 独立运行测试，退出码 0 = PASS，非 0 = FAIL。SubAgent 无权判定，只负责描述问题 |
| Implement-Check 循环上限 3 轮 | Check 阶段问题是代码层面的，修复收敛快；3 轮已足够 |
| 每步独立 `claude -p` | 独立上下文窗口，步骤间通过 Handoff 文件传递信息 |
| `$CLI_CMD` 环境变量 | 一行配置切换 claude/claude-codex/claude-gemini，无缝支持多 backend |
| `PROJECT_DIR` 参数 | 确保 Handoff 文件落在正确的项目目录下，而非 pipeline.sh 所在目录 |
| `set -euo pipefail` | 任何命令失败立即退出，不静默继续 |
| `trap` 清理锁目录 | 无论正常退出还是异常退出，都清理锁目录 |
| `\|\| exit_code=$?` 捕获退出码 | 绕过 `set -e` 的立即退出行为，确保失败时能更新进度文件和发送通知 |
| 锁目录防并行 | `mkdir` 原子操作创建锁目录，同一 feature 不允许两个 Pipeline 同时运行 |
| 启动前检查残留 Handoff | 防止上次 Pipeline 未清理的文件被误读，确保每次从干净状态开始 |
| feature name 合法性校验 | 只允许中文、英文、数字、下划线、连字符，防止路径拼接异常或注入 |
| 进度文件原子写入 | 先写临时文件（`.tmp.$$`）再 `mv`，防止读取方读到半写入的 JSON |
| Handoff 最小结构校验 | 检查输出文件非空且包含关键标题，拦截空文件或格式严重偏离的输出 |
| jq 依赖检查 | Status Line 依赖 jq 解析 JSON，启动前检查，未安装则阻断启动 |
| 进度文件按 feature 隔离 | `.pipeline-progress-{feature}.json`，多个 Pipeline 并行时互不覆盖 |

---

## 7. 异常处理全表

| 异常类型 | 检测方式 | 处理 |
|---------|---------|------|
| handoff_clarify.md 不存在 | `[ ! -f ]` | 通知 + exit 1 |
| `claude -p` 执行失败 | `|| exit_code=$?` | 更新 failed + 通知 + exit 1 |
| Handoff 文件未生成 | `[ ! -f ]` | 通知 + exit 1 |
| Handoff 文件为空 | `[ ! -s ]` | 通知 + exit 1 |
| Handoff 章节标题缺失 | grep 检查 | exit 1 强阻断 |
| Handoff 结构验证失败 | validate_handoff | exit 1 强阻断 |
| 只读角色修改项目代码 | verify_no_code_changes（git diff） | exit 1 强阻断 |
| QA 反复失败 >= 10 | fix_count 检查 | 通知 + exit 1 |
| Fix 升级人工 >= 5 | fix_count 检查 | 暂停等待人工确认 |
| 同一 feature 重复启动 | mkdir 锁文件 | 拒绝启动 + 通知 |
| 脚本被 kill | `trap EXIT` | 清理锁文件 |
| 单步超时 | run_with_timeout（exit code 137） | 更新 failed + 通知 + exit 1 |
| 残留 Handoff 文件 | 启动时逐文件检查 | 拒绝启动 + 通知 |
| feature name 非法字符 | perl 正则校验 | 拒绝启动 |
| Design 评审循环耗尽 | design_review_count >= MAX_REVIEW | 通知 + exit 1 |
| Plan 评审循环耗尽 | plan_review_count >= MAX_REVIEW | 通知 + exit 1 |
| Check 循环耗尽 | check_loop_count >= MAX_CHECK_LOOP | 通知 + exit 1 |
| 评审输出无有效 REVIEW 行 | parse_review 返回 MISSING | 通知 + exit 1（不重试） |
| Check/QA 结果解析异常 | parse_result 防御性分支 | 通知 + exit 1 |
| 人工确认超时（24h） | confirm 文件未出现 | 通知 + exit 1 |
| 人工确认被拒绝 | confirm 文件内容 REJECT | 通知 + exit 1 |
| 累计费用超预算 | TOTAL_COST > TOTAL_BUDGET | 暂停等待人工确认 |
| Implement 中途失败 | 退出码非 0 或 handoff_run.md 未生成 | 通知用户 commit hash 列表，不自动回滚 |
| 用户重跑同一 Feature | `pipeline.sh reset {feature}` | 删除除 clarify 外的所有产物 |
| INFRA_ERROR（QA 阶段） | grep 服务启动失败/端口占用 | 不进入 Fix，直接 exit 1 |
| 无效 START_STEP | 参数校验 | 报错 + 列出可选值 |
| 断点续传缺少前置产物 | 检查 handoff_*.md | 报错 + 提示缺少文件 |

**所有异常都通过系统通知告知用户**，确保后台运行时不遗漏。通知失败不影响 Pipeline 执行。

> 详见 L2 原文 行 316-1146（完整脚本逻辑）
