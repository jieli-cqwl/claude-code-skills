---
name: design
description: |
  架构设计。在隔离上下文中启动 pipeline-designer SubAgent 输出设计文档和决策记录。
  Use when: 讨论系统架构或模块划分、接口设计、/clarify 完成后进入设计阶段。前置条件：需先完成 /clarify。
context: fork
agent: pipeline-designer
---

<!-- 权限说明：本 Skill 通过 SubAgent pipeline-designer 执行。SubAgent 可用工具：Read, Write, Glob, Grep, WebSearch。参见 agents/pipeline-designer.md 的 allowedTools 定义 -->

# /design -- 架构设计

> 在隔离上下文中执行架构设计，输出架构设计文档和关键决策记录。

## 前置条件

`docs/pipeline/{feature}/handoff_clarify.md` 必须存在。如不存在，请先执行 `/clarify`。

## 执行流程

1. 读取 `docs/pipeline/{feature}/handoff_clarify.md`
2. 选择模板：clarify 规则 ≤ 3 条且涉及单模块 → 精简版；否则 → 完整版
3. 用 Glob/Grep 扫描现有代码，了解项目结构和编码模式
4. 基于扫描结果和需求文档执行架构设计
5. 关键决策列出 2-3 个备选方案并对比（方法论由 arch-methodology Skill 提供）
6. 输出到 `docs/pipeline/{feature}/handoff_design.md` + `Key_Decisions.md`

## 输出格式

根据 clarify 文档的规则数量和模块范围选择模板：
- **精简版**：clarify 规则 ≤ 3 条且涉及单模块
- **完整版**：clarify 规则 > 3 条、跨模块或架构变更

### 精简版模板

```markdown
# handoff_design.md

## Goals / Non-Goals
### Goals
- [G1: ...]
### Non-Goals
- [NG1: 本可以成为目标但被排除的事项...]

## 输入分析
[扫描现有代码的发现 + clarify 规则逐条理解]

## 架构视图（可选）
> 涉及多模块交互时建议绘制，单模块内部改动可省略

## 决策
[关键技术选型及方案对比]

## 产出
### 模块划分
### 接口清单
### 数据模型

## Open Questions
[待确认假设，无则标"无待确认项"]

## 覆盖表
[clarify 规则 -> 设计产出 -> 覆盖状态]

## 交接项
```

### 完整版模板

```markdown
# handoff_design.md

## Goals / Non-Goals
### Goals
- [G1: ...]
### Non-Goals
- [NG1: 本可以成为目标但被排除的事项...]

## 输入分析
[扫描现有代码的发现 + clarify 规则逐条理解]

## 架构视图
[Mermaid C4 System Context 图 + Container 图，强制要求]

## 决策
[关键技术选型及方案对比]

## 产出
### 模块划分
### 接口清单
### 数据模型

## 横切关注点
[安全、隐私、可观测性、错误监控]

## Open Questions
[待确认假设]

## 成功指标
[可量化的验收标准]

## 覆盖表
[clarify 规则 -> 设计产出 -> 覆盖状态]

## 交接项
```
