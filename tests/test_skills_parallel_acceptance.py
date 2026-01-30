# tests/test_skills_parallel_acceptance.py
# 从 docs/需求文档/clarify_skills并行优化.md AC 表格自动生成
# 状态：FAILING（TDD 起点）

"""
Skills 并行优化验收测试

测试策略：
- 由于 Skills 是 Markdown 文件，无法直接单元测试
- 使用集成测试验证 SKILL.md 中的并行配置是否正确
- 使用 E2E 测试验证实际执行时是否启动预期数量的 Agent

测试方法：
1. 静态检查：验证 SKILL.md 文件中的 parallel_mode 配置和 Task 调用格式
2. 集成测试：验证 Phase 结构和 Agent 数量
3. E2E 测试：手动触发 Skill 验证实际行为

AC 来源：docs/需求文档/clarify_skills并行优化.md
"""

import pytest
import re
from pathlib import Path

# 项目根目录
SKILLS_ROOT = Path(__file__).parent.parent


# ============================================================================
# 辅助函数
# ============================================================================


def read_skill_file(skill_dir: str) -> str:
    """读取 Skill 的 SKILL.md 文件"""
    skill_path = SKILLS_ROOT / skill_dir / "SKILL.md"
    if not skill_path.exists():
        pytest.skip(f"Skill 文件不存在: {skill_path}")
    return skill_path.read_text(encoding="utf-8")


def count_task_calls(content: str, phase_pattern: str = None) -> int:
    """统计 Task 工具调用次数"""
    # 匹配 <Task 或 Task tool 调用模式
    task_pattern = r"<Task\s+subagent_type="
    if phase_pattern:
        # 在特定 Phase 中统计
        phase_match = re.search(
            rf"{phase_pattern}.*?(?=Phase \d|$)", content, re.DOTALL | re.IGNORECASE
        )
        if phase_match:
            return len(re.findall(task_pattern, phase_match.group()))
    return len(re.findall(task_pattern, content))


def has_parallel_mode(content: str) -> bool:
    """检查是否有 parallel_mode 配置"""
    return bool(re.search(r"parallel_mode:\s*true", content, re.IGNORECASE))


def count_agents_in_phase(content: str, phase_name: str) -> int:
    """统计某个 Phase 中的 Agent 数量"""
    # 查找形如 "Phase 1: xxx（N Agent" 的模式
    pattern = rf"{phase_name}[^(]*\((\d+)\s*Agent"
    match = re.search(pattern, content, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def check_mock_usage(content: str) -> list[str]:
    """检查是否使用了禁止的 Mock 关键词"""
    forbidden_patterns = [
        r"@patch",
        r"MagicMock",
        r"Mock\(",
        r"mock_",
        r"vi\.fn",
        r"vi\.mock",
        r"jest\.fn",
        r"jest\.mock",
    ]
    violations = []
    for pattern in forbidden_patterns:
        if re.search(pattern, content):
            violations.append(pattern)
    return violations


# ============================================================================
# P0 优先级测试
# ============================================================================


class TestExploreParallel:
    """AC-1.x: /explore 并行化测试"""

    def test_ac1_1_phase1_8_agents(self):
        """AC-1.1: /explore Phase 1 应启动 8 个 Agent 并行信息收集"""
        content = read_skill_file("方案探索_explore")

        # 检查 parallel_mode 配置
        assert has_parallel_mode(content), (
            "AC-1.1 FAILED: 缺少 parallel_mode: true 配置"
        )

        # 检查 Phase 1 Agent 数量
        agent_count = count_agents_in_phase(content, "Phase 1")
        assert agent_count == 8, (
            f"AC-1.1 FAILED: Phase 1 应有 8 个 Agent，实际 {agent_count} 个"
        )

    def test_ac1_2_phase2_8_agents(self):
        """AC-1.2: /explore Phase 2 应启动 8 个 Agent 并行方案分析"""
        content = read_skill_file("方案探索_explore")

        # 检查 Phase 2 Agent 数量
        agent_count = count_agents_in_phase(content, "Phase 2")
        assert agent_count == 8, (
            f"AC-1.2 FAILED: Phase 2 应有 8 个 Agent，实际 {agent_count} 个"
        )

    def test_ac1_3_phase3_aggregation(self):
        """AC-1.3: /explore Phase 3 应由主 Agent 汇总输出结构化对比报告"""
        content = read_skill_file("方案探索_explore")

        # 检查 Phase 3 存在且是串行汇总
        assert re.search(r"Phase 3.*汇总", content, re.DOTALL | re.IGNORECASE), (
            "AC-1.3 FAILED: 缺少 Phase 3 汇总阶段"
        )


class TestTestGenParallel:
    """AC-2.x: /test-gen 并行化测试"""

    def test_ac2_1_phase1_10_agents(self):
        """AC-2.1: /test-gen Phase 1 应启动 10 个 Agent 并行代码分析"""
        content = read_skill_file("测试生成_test-gen")

        # 检查 parallel_mode 配置
        assert has_parallel_mode(content), (
            "AC-2.1 FAILED: 缺少 parallel_mode: true 配置"
        )

        # 检查 Phase 1 Agent 数量
        agent_count = count_agents_in_phase(content, "Phase 1")
        assert agent_count == 10, (
            f"AC-2.1 FAILED: Phase 1 应有 10 个 Agent，实际 {agent_count} 个"
        )

    def test_ac2_2_phase2_10_agents(self):
        """AC-2.2: /test-gen Phase 2 应启动 10 个 Agent 并行测试生成"""
        content = read_skill_file("测试生成_test-gen")

        # 检查 Phase 2 Agent 数量
        agent_count = count_agents_in_phase(content, "Phase 2")
        assert agent_count == 10, (
            f"AC-2.2 FAILED: Phase 2 应有 10 个 Agent，实际 {agent_count} 个"
        )

    def test_ac2_3_phase3_aggregation(self):
        """AC-2.3: /test-gen Phase 3 应由主 Agent 合并去重输出"""
        content = read_skill_file("测试生成_test-gen")

        # 检查 Phase 3 存在且是串行汇总
        assert re.search(
            r"Phase 3.*汇总|合并|去重", content, re.DOTALL | re.IGNORECASE
        ), "AC-2.3 FAILED: 缺少 Phase 3 汇总阶段"

    def test_ac_edge_1_no_mock(self):
        """AC-EDGE-1: /test-gen 生成的测试不应包含 Mock 相关代码"""
        content = read_skill_file("测试生成_test-gen")

        # 检查是否有禁止 Mock 的说明
        assert re.search(r"禁止.*Mock|Mock.*禁止|不.*Mock", content, re.IGNORECASE), (
            "AC-EDGE-1 FAILED: 缺少禁止 Mock 的说明"
        )


class TestQaParallel:
    """AC-3.x: /qa 并行化测试"""

    def test_ac3_1_layer1_4_agents(self):
        """AC-3.1: /qa Layer 1 应启动 4 个 Agent 并行执行单元测试"""
        content = read_skill_file("测试验收_qa")

        # 检查 parallel_mode 配置
        assert has_parallel_mode(content), (
            "AC-3.1 FAILED: 缺少 parallel_mode: true 配置"
        )

        # 检查 Layer 1 Agent 数量
        layer1_match = re.search(r"Layer 1[^(]*\((\d+)\s*Agent", content, re.IGNORECASE)
        assert layer1_match, "AC-3.1 FAILED: 缺少 Layer 1 定义"
        assert int(layer1_match.group(1)) == 4, (
            f"AC-3.1 FAILED: Layer 1 应有 4 个 Agent，实际 {layer1_match.group(1)} 个"
        )

    def test_ac3_2_layer2_3_agents(self):
        """AC-3.2: /qa Layer 2 应启动 3 个 Agent 并行执行集成测试"""
        content = read_skill_file("测试验收_qa")

        # 检查 Layer 2 Agent 数量
        layer2_match = re.search(r"Layer 2[^(]*\((\d+)\s*Agent", content, re.IGNORECASE)
        assert layer2_match, "AC-3.2 FAILED: 缺少 Layer 2 定义"
        assert int(layer2_match.group(1)) == 3, (
            f"AC-3.2 FAILED: Layer 2 应有 3 个 Agent，实际 {layer2_match.group(1)} 个"
        )

    def test_ac3_3_layer3_serial(self):
        """AC-3.3: /qa Layer 3 应串行执行 E2E 测试"""
        content = read_skill_file("测试验收_qa")

        # 检查 Layer 3 是串行的
        assert re.search(
            r"Layer 3.*串行|Layer 3.*1\s*Agent", content, re.DOTALL | re.IGNORECASE
        ), "AC-3.3 FAILED: Layer 3 应为串行执行"

    def test_ac_err_4_layer_gate(self):
        """AC-ERR-4: /qa 任一 Layer 失败应停止后续 Layer"""
        content = read_skill_file("测试验收_qa")

        # 检查门控机制
        assert re.search(r"门控|全部通过.*Layer", content, re.IGNORECASE), (
            "AC-ERR-4 FAILED: 缺少 Layer 门控机制"
        )


# ============================================================================
# P1 优先级测试
# ============================================================================


class TestCritiqueParallel:
    """AC-4.x: /critique 并行化测试"""

    def test_ac4_1_10_agents(self):
        """AC-4.1: /critique 应启动 10 个 Agent 并行评审"""
        content = read_skill_file("方案评审_critique")

        # 检查 parallel_mode 配置
        assert has_parallel_mode(content), (
            "AC-4.1 FAILED: 缺少 parallel_mode: true 配置"
        )

        # 检查 Agent 数量
        agent_count = count_agents_in_phase(content, "Phase 1")
        assert agent_count == 10, (
            f"AC-4.1 FAILED: 应有 10 个评审 Agent，实际 {agent_count} 个"
        )


class TestDesignParallel:
    """AC-5.x: /design 并行化测试"""

    def test_ac5_1_9_agents_by_layer(self):
        """AC-5.1: /design 应启动 9 个 Agent 按数据层/业务层/接口层并行设计"""
        content = read_skill_file("架构设计_design")

        # 检查 parallel_mode 配置
        assert has_parallel_mode(content), (
            "AC-5.1 FAILED: 缺少 parallel_mode: true 配置"
        )

        # 检查 Agent 数量
        agent_count = count_agents_in_phase(content, "Phase 1")
        assert agent_count == 9, (
            f"AC-5.1 FAILED: 应有 9 个设计 Agent，实际 {agent_count} 个"
        )

        # 检查是否按层次划分
        assert re.search(r"数据层|业务层|接口层", content, re.IGNORECASE), (
            "AC-5.1 FAILED: 缺少按层次划分的设计"
        )

    def test_ac_edge_3_consistency_check(self):
        """AC-EDGE-3: /design Phase 2 应有一致性校验"""
        content = read_skill_file("架构设计_design")

        # 检查一致性校验
        assert re.search(r"一致性.*校验|校验.*一致性", content, re.IGNORECASE), (
            "AC-EDGE-3 FAILED: 缺少一致性校验机制"
        )


class TestExpertsParallel:
    """AC-6.x: /experts 并行化测试"""

    def test_ac6_1_8_required_agents(self):
        """AC-6.1: /experts 应启动 8 个必选专家 Agent"""
        content = read_skill_file("专家协作_experts")

        # 检查 parallel_mode 配置
        assert has_parallel_mode(content), (
            "AC-6.1 FAILED: 缺少 parallel_mode: true 配置"
        )

        # 检查必选专家数量
        assert re.search(r"8\s*.*必选|必选.*8", content, re.IGNORECASE), (
            "AC-6.1 FAILED: 缺少 8 个必选专家的定义"
        )

    def test_ac6_2_optional_business_analyst(self):
        """AC-6.2: /experts 业务流程时应启动业务分析师"""
        content = read_skill_file("专家协作_experts")

        # 检查可选业务分析师
        assert re.search(r"业务分析师|业务流程.*启动", content, re.IGNORECASE), (
            "AC-6.2 FAILED: 缺少业务分析师可选启动机制"
        )

    def test_ac6_3_optional_domain_expert(self):
        """AC-6.3: /experts 特定领域时应启动领域专家"""
        content = read_skill_file("专家协作_experts")

        # 检查可选领域专家
        assert re.search(r"领域专家|特定领域.*启动", content, re.IGNORECASE), (
            "AC-6.3 FAILED: 缺少领域专家可选启动机制"
        )

    def test_ac_edge_4_divergence_handling(self):
        """AC-EDGE-4: /experts 应处理专家分歧"""
        content = read_skill_file("专家协作_experts")

        # 检查分歧处理
        assert re.search(r"分歧|冲突|权衡", content, re.IGNORECASE), (
            "AC-EDGE-4 FAILED: 缺少专家分歧处理机制"
        )


# ============================================================================
# P2 优先级测试
# ============================================================================


class TestSecurityParallel:
    """AC-7.x: /security 并行化测试"""

    def test_ac7_1_8_agents(self):
        """AC-7.1: /security 应启动 8 个 Agent 并行扫描"""
        content = read_skill_file("安全扫描_security")

        # 检查 parallel_mode 配置
        assert has_parallel_mode(content), (
            "AC-7.1 FAILED: 缺少 parallel_mode: true 配置"
        )

        # 检查 Agent 数量
        agent_count = count_agents_in_phase(content, "Phase 1")
        assert agent_count == 8, (
            f"AC-7.1 FAILED: 应有 8 个扫描 Agent，实际 {agent_count} 个"
        )


class TestPerfParallel:
    """AC-8.x: /perf 并行化测试"""

    def test_ac8_1_8_agents(self):
        """AC-8.1: /perf 应启动 8 个 Agent 并行分析"""
        content = read_skill_file("性能分析_perf")

        # 检查 parallel_mode 配置
        assert has_parallel_mode(content), (
            "AC-8.1 FAILED: 缺少 parallel_mode: true 配置"
        )

        # 检查 Agent 数量
        agent_count = count_agents_in_phase(content, "Phase 1")
        assert agent_count == 8, (
            f"AC-8.1 FAILED: 应有 8 个分析 Agent，实际 {agent_count} 个"
        )

    def test_ac_edge_2_cache_manual_confirm(self):
        """AC-EDGE-2: /perf 缓存建议应标注"需人工确认" """
        content = read_skill_file("性能分析_perf")

        # 检查缓存需人工确认
        assert re.search(r"缓存.*人工确认|人工确认.*缓存", content, re.IGNORECASE), (
            "AC-EDGE-2 FAILED: 缺少缓存需人工确认的说明"
        )


class TestOverviewParallel:
    """AC-9.x: /overview 并行化测试"""

    def test_ac9_1_8_agents(self):
        """AC-9.1: /overview 应启动 8 个 Agent 并行收集"""
        content = read_skill_file("项目概览_overview")

        # 检查 parallel_mode 配置
        assert has_parallel_mode(content), (
            "AC-9.1 FAILED: 缺少 parallel_mode: true 配置"
        )

        # 检查 Agent 数量
        agent_count = count_agents_in_phase(content, "Phase 1")
        assert agent_count == 8, (
            f"AC-9.1 FAILED: 应有 8 个收集 Agent，实际 {agent_count} 个"
        )


class TestRefactorParallel:
    """AC-10.x: /refactor 并行化测试"""

    def test_ac10_1_10_agents(self):
        """AC-10.1: /refactor 应启动 10 个 Agent 并行检测"""
        content = read_skill_file("重构_refactor")

        # 检查 parallel_mode 配置
        assert has_parallel_mode(content), (
            "AC-10.1 FAILED: 缺少 parallel_mode: true 配置"
        )

        # 检查 Agent 数量
        agent_count = count_agents_in_phase(content, "Phase 1")
        assert agent_count == 10, (
            f"AC-10.1 FAILED: 应有 10 个检测 Agent，实际 {agent_count} 个"
        )


# ============================================================================
# 异常流程测试
# ============================================================================


class TestErrorHandling:
    """AC-ERR-x: 异常流程测试"""

    @pytest.mark.parametrize(
        "skill_dir",
        [
            "方案探索_explore",
            "测试生成_test-gen",
            "测试验收_qa",
            "方案评审_critique",
            "架构设计_design",
            "专家协作_experts",
            "安全扫描_security",
            "性能分析_perf",
            "项目概览_overview",
            "重构_refactor",
        ],
    )
    def test_ac_err_1_timeout_handling(self, skill_dir):
        """AC-ERR-1: 所有并行 Skill 应处理 Agent 超时"""
        content = read_skill_file(skill_dir)

        # 检查超时处理（只要有 parallel_mode 就需要）
        if has_parallel_mode(content):
            assert re.search(r"超时|timeout", content, re.IGNORECASE), (
                f"AC-ERR-1 FAILED: {skill_dir} 缺少超时处理机制"
            )

    @pytest.mark.parametrize(
        "skill_dir",
        [
            "方案探索_explore",
            "测试生成_test-gen",
            "测试验收_qa",
            "方案评审_critique",
            "架构设计_design",
            "专家协作_experts",
            "安全扫描_security",
            "性能分析_perf",
            "项目概览_overview",
            "重构_refactor",
        ],
    )
    def test_ac_err_2_crash_handling(self, skill_dir):
        """AC-ERR-2: 所有并行 Skill 应处理 Agent 崩溃"""
        content = read_skill_file(skill_dir)

        # 检查崩溃处理（只要有 parallel_mode 就需要）
        if has_parallel_mode(content):
            assert re.search(r"崩溃|失败.*继续|标记.*失败", content, re.IGNORECASE), (
                f"AC-ERR-2 FAILED: {skill_dir} 缺少崩溃处理机制"
            )

    @pytest.mark.parametrize(
        "skill_dir",
        [
            "方案探索_explore",
            "测试生成_test-gen",
            "测试验收_qa",
            "方案评审_critique",
            "架构设计_design",
            "专家协作_experts",
            "安全扫描_security",
            "性能分析_perf",
            "项目概览_overview",
            "重构_refactor",
        ],
    )
    def test_ac_err_3_majority_failure(self, skill_dir):
        """AC-ERR-3: 失败 Agent > 50% 时整体任务应失败"""
        content = read_skill_file(skill_dir)

        # 检查多数失败处理（只要有 parallel_mode 就需要）
        if has_parallel_mode(content):
            assert re.search(
                r"50%|过半|多数.*失败|失败.*整体", content, re.IGNORECASE
            ), f"AC-ERR-3 FAILED: {skill_dir} 缺少多数失败处理机制"


# ============================================================================
# 质量验收测试
# ============================================================================


class TestQualityMetrics:
    """质量验收：可量化指标"""

    @pytest.mark.parametrize(
        "skill_dir,expected_agents",
        [
            ("方案探索_explore", 8),
            ("测试生成_test-gen", 10),
            ("方案评审_critique", 10),
            ("架构设计_design", 9),
            ("专家协作_experts", 8),
            ("安全扫描_security", 8),
            ("性能分析_perf", 8),
            ("项目概览_overview", 8),
            ("重构_refactor", 10),
        ],
    )
    def test_parallel_call_count(self, skill_dir, expected_agents):
        """质量验收：每个并行点应有 8-10 个 Task 调用"""
        content = read_skill_file(skill_dir)

        # 检查 Agent 数量在 8-10 范围内
        agent_count = count_agents_in_phase(content, "Phase 1")
        assert 8 <= agent_count <= 10, (
            f"质量验收 FAILED: {skill_dir} Agent 数量 {agent_count} 不在 8-10 范围内"
        )


# ============================================================================
# 运行入口
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
