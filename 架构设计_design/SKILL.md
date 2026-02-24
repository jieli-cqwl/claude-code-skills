---
name: design
description: |
  架构设计。自动激活场景：
  1) 用户讨论系统架构、模块划分、接口设计时
  2) 用户说"帮我设计一下"、"怎么设计这个功能"、"架构方案"时
  3) /clarify 完成后用户准备进入设计阶段时
  在隔离上下文中启动 pipeline-designer SubAgent。前置条件：需先完成 /clarify。
context: fork
agent: pipeline-designer
---

# /design -- 架构设计

> 在隔离上下文中执行架构设计，输出架构设计文档和关键决策记录。

## 前置条件

`docs/pipeline/{feature}/handoff_clarify.md` 必须存在。如不存在，请先执行 `/clarify`。

## 执行流程

1. 读取 `docs/pipeline/{feature}/handoff_clarify.md`
2. 用 Glob/Grep 扫描现有代码，了解项目结构和编码模式
3. 基于扫描结果和需求文档执行架构设计
4. 关键决策列出 2-3 个备选方案并对比（方法论由 skills 引入的知识 Skill 提供）
5. 输出到 `docs/pipeline/{feature}/handoff_design.md` + `Key_Decisions.md`

## 输出格式

Handoff 文档必须包含以下结构：

```markdown
# handoff_design.md

## 输入分析
[扫描现有代码的发现 + clarify 规则逐条理解]

## 决策
[关键技术选型及方案对比]

## 产出

### 模块划分
[模块列表，每个模块的"负责/不负责"]

### 接口清单
[每个接口的入参/出参/错误码]

### 数据模型
[模型定义和字段说明]

## 覆盖表
[clarify 规则 -> 设计产出 -> 覆盖状态]

## 交接项
- 接口清单（供 Planner 拆分任务）
- 模块依赖图
- 技术风险点
- 设计约束
```
