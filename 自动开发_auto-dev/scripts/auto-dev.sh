#!/bin/bash
# Auto Dev - 自动循环开发脚本
# 基于 Ralph Loop 原理 + Skills 链路融合
# 用法: ./auto-dev.sh --prd <需求文档> [--max-iterations N] [--log <日志文件>]

set -e

# ===== 配置 =====
PRD_FILE=""
MAX_ITERATIONS=100
LOG_FILE=".claude/auto-dev.log"
DETAIL_FILE=".claude/auto-dev-detail.md"
COMPLETION_MARKER="COMPLETE"

# ===== 颜色 =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===== 参数解析 =====
while [[ $# -gt 0 ]]; do
    case $1 in
        --prd)
            PRD_FILE="$2"
            shift 2
            ;;
        --max-iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        --log)
            LOG_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Auto Dev - 自动循环开发"
            echo ""
            echo "用法: $0 --prd <需求文档> [选项]"
            echo ""
            echo "选项:"
            echo "  --prd <文件>           需求文档路径（必需）"
            echo "  --max-iterations <N>   最大迭代次数（默认: 100，适合大需求过夜运行）"
            echo "  --log <文件>           日志文件路径（默认: .claude/auto-dev.log）"
            echo "  --help                 显示帮助"
            exit 0
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

# ===== 验证 =====
if [[ -z "$PRD_FILE" ]]; then
    echo -e "${RED}错误: 必须指定需求文档 (--prd)${NC}"
    exit 1
fi

if [[ ! -f "$PRD_FILE" ]]; then
    echo -e "${RED}错误: 需求文档不存在: $PRD_FILE${NC}"
    exit 1
fi

# ===== 初始化 =====
mkdir -p .claude
mkdir -p "$(dirname "$LOG_FILE")"

# 读取需求文档
PRD_CONTENT=$(cat "$PRD_FILE")

# ===== 构建提示词 =====
PROMPT="# 自动开发任务

## 需求文档

$PRD_CONTENT

---

## 执行指南

你是一个自主开发 Agent，需要完成以上需求文档中描述的功能。

### 执行流程

1. **设计阶段**（如果还没有设计文档）：
   - 执行方案探索（/explore）：调研最佳实践
   - 执行架构设计（/design）：输出模块划分、接口设计
   - **执行方案评审（/critique）**：以批评者视角审查架构设计
   - 执行写计划（/plan）：输出详细实施步骤（引用 /clarify 的 AC）
   - **执行计划评审（/critique）**：以批评者视角审查计划
   - 保存到 docs/ 目录

2. **测试先行阶段**：
   - **执行测试生成（/test-gen from-clarify）**：从 AC 生成 FAILING 测试
   - 验证测试文件存在
   - 运行测试确认全部失败（符合 TDD 预期）

3. **实现阶段**（基于已有测试）：
   - 读取计划文档，找到下一个未完成的 Task
   - 按 TDD 实现：运行测试 → 看到失败 → 写最小实现 → 看到通过
   - 每完成一个文件，运行 lint 检查
   - 完成后 git commit

4. **检查阶段**（所有 Task 完成后）：
   - 执行开发检查（/check）：铁律、规范、质量审查、TDD 验证
   - 运行全量测试：pytest -v 或 npm test
   - 检查代码质量：ruff/eslint + mypy/tsc

5. **测试验收阶段**：
   - **执行测试验收（/qa）**：金字塔门控（单元→集成→E2E）
   - 基于 /clarify 的 AC 表格核对验收标准

6. **修复阶段**（如有问题）：
   - 分析失败原因
   - 修复问题
   - 重新验证（回到检查阶段）

### 项目规范

- 遵循 CLAUDE.md 中的技术栈和规范
- 遵循 ~/.claude/rules/RULES.md 中的铁律
- **AC 单一来源**：验收标准来自 /clarify 的 AC 文档，禁止重新定义
- **测试先行**：/plan 之后必须执行 /test-gen 生成 FAILING 测试
- TDD：基于已有测试，让测试从 FAILING 变为 PASSING
- 每个功能点都要有测试覆盖

### 完成条件

以下条件**全部满足**时才算完成：
- [ ] 需求文档中的所有功能点已实现
- [ ] 所有测试通过
- [ ] 无 lint 错误
- [ ] 无类型错误
- [ ] 验收标准全部满足

### 完成信号

当以上条件**全部满足**时，在回复末尾输出：

<promise>$COMPLETION_MARKER</promise>

### 注意事项

- 这是第 \$ITERATION 次迭代
- 检查 git log 和现有文件，了解之前的工作进度
- 不要重复已完成的工作
- 如果卡住，记录问题并尝试不同方案
- 每完成一步就 git commit，保存进度"

# ===== 启动信息 =====
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🚀 Auto Dev 启动${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "   需求文档: ${YELLOW}$PRD_FILE${NC}"
echo -e "   最大迭代: ${YELLOW}$MAX_ITERATIONS${NC}"
echo -e "   日志文件: ${YELLOW}$LOG_FILE${NC}"
echo -e "   详细记录: ${YELLOW}$DETAIL_FILE${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 记录启动信息
{
    echo "# Auto Dev 执行记录"
    echo ""
    echo "- 启动时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "- 需求文档: $PRD_FILE"
    echo "- 最大迭代: $MAX_ITERATIONS"
    echo ""
    echo "---"
    echo ""
} > "$DETAIL_FILE"

# ===== 主循环 =====
iteration=0
start_time=$(date +%s)

while [ $iteration -lt $MAX_ITERATIONS ]; do
    iteration=$((iteration + 1))

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📍 迭代 $iteration / $MAX_ITERATIONS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 记录迭代开始
    {
        echo "## 迭代 $iteration"
        echo ""
        echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
    } >> "$DETAIL_FILE"

    # 替换迭代次数
    CURRENT_PROMPT="${PROMPT//\$ITERATION/$iteration}"

    # 运行 Claude Code
    echo -e "${YELLOW}正在执行...${NC}"
    output=$(claude -p --permission-mode bypassPermissions "$CURRENT_PROMPT" 2>&1) || true

    # 记录输出
    {
        echo "### 输出"
        echo ""
        echo '```'
        echo "$output" | tail -100
        echo '```'
        echo ""
    } >> "$DETAIL_FILE"

    # 记录到日志
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 迭代 $iteration 完成" >> "$LOG_FILE"

    # 检查完成标记
    if echo "$output" | grep -q "<promise>$COMPLETION_MARKER</promise>"; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        minutes=$((duration / 60))

        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}✅ 自动开发完成！${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "   总迭代次数: ${YELLOW}$iteration${NC}"
        echo -e "   总耗时: ${YELLOW}$minutes 分钟${NC}"
        echo ""
        echo -e "   详细记录: ${BLUE}$DETAIL_FILE${NC}"
        echo ""
        echo -e "${YELLOW}🎯 下一步建议:${NC}"
        echo "   1. 执行 /qa 进行人工测试验收"
        echo "   2. 执行 /ship 提交代码"
        echo ""

        # 记录完成
        {
            echo "---"
            echo ""
            echo "## 完成统计"
            echo ""
            echo "- 完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "- 总迭代次数: $iteration"
            echo "- 总耗时: $minutes 分钟"
            echo "- 状态: ✅ 成功"
        } >> "$DETAIL_FILE"

        exit 0
    fi

    echo -e "   ${YELLOW}未检测到完成标记，继续下一次迭代...${NC}"
    echo ""

    # 短暂暂停，避免 API 限流
    sleep 3
done

# 达到最大迭代
end_time=$(date +%s)
duration=$((end_time - start_time))
minutes=$((duration / 60))

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}⚠️  达到最大迭代次数 ($MAX_ITERATIONS)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "   总耗时: ${YELLOW}$minutes 分钟${NC}"
echo ""
echo "   任务可能未完成，请检查:"
echo -e "   - 详细记录: ${BLUE}$DETAIL_FILE${NC}"
echo -e "   - 日志文件: ${BLUE}$LOG_FILE${NC}"
echo ""
echo "   可以增加迭代继续:"
echo "   $0 --prd $PRD_FILE --max-iterations 20 --resume"
echo ""

# 记录未完成
{
    echo "---"
    echo ""
    echo "## 未完成"
    echo ""
    echo "- 结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "- 总迭代次数: $iteration"
    echo "- 总耗时: $minutes 分钟"
    echo "- 状态: ⚠️ 达到最大迭代次数"
} >> "$DETAIL_FILE"

exit 1
