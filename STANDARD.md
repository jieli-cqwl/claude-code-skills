# Skills 标准索引

> 所有可用的 Skills 列表，按工作流程阶段组织
> **版本**：v4.0（Skills 与 SubAgents 优化改造，2026-02-23）

## 核心理念

| 理念 | 说明 |
|------|------|
| **简单、合适、演化** | 不过度设计，根据需求规模选择合适的流程 |
| **三种使用方式** | 主对话直接用 Skill、触发 SubAgent 隔离执行、全流程自动编排 |
| **三层架构** | 编排层（Skill/pipeline.sh）+ 执行层（SubAgent 角色卡）+ 知识层（知识型 Skill） |
| **严格 TDD** | 没有先失败的测试，就没有生产代码 |
| **完成前验证** | 只有亲眼看到验证命令成功，才能声称完成 |

## 规范文件说明

| 目录 | 加载方式 | 内容 |
|------|---------|------|
| `~/.claude/rules/` | **始终加载** | 核心铁律（RULES.md） |
| `~/.claude/reference/` | **按需加载** | 详细规范（由 Skills 触发读取） |

### 核心参考规范

| 规范 | 路径 | 用途 |
|------|------|------|
| TDD 规范 | `~/.claude/reference/TDD规范.md` | 严格的测试驱动开发 |
| 完成前验证 | `~/.claude/reference/完成前验证.md` | 声明完成前的验证清单 |
| 并行拆分策略 | `~/.claude/reference/并行拆分策略.md` | 多人协作模式的拆分原则 |

---

## 三种使用方式

### 方式 1：主对话直接使用 Skill

不需要上下文隔离时，直接在主对话中使用 Skill。

适用 Skill：`/clarify`, `/ship`, `/refactor`, `/overview`, `/status`, `/security`, `/perf`, `/scan`, `/worktree`, `/mcp-builder`, `/admin-ui`, `/h5`, `/product`

### 方式 2：触发 SubAgent 隔离执行

需要上下文隔离（避免噪音污染主对话）时，通过入口 Skill 触发 SubAgent。

适用 Skill：`/design`, `/plan`, `/run-plan`, `/check`, `/qa`, `/fix`

机制：入口 Skill 的 `context: fork` + `agent: pipeline-xxx` → Claude Code 原生创建隔离上下文 → 自动加载 SubAgent 及其 skills

### 方式 3：全流程自动编排

需要连续执行多个隔离阶段时，使用编排 Skill。

| 命令 | 场景 | 特点 |
|------|------|------|
| `/auto-dev` | 日常开发 | 在主对话中编排，有人工确认检查点 |
| `pipeline.sh` | 无人值守 | 独立终端，超时/费用/锁等加固 |

---

## 流程选择指南（核心）

> **原则**：根据需求规模智能选择流程，遵循"简单、合适、演化"

### 需求规模判断

| 规模 | 判断条件 | 示例 |
|------|---------|------|
| **小** | AC ≤ 3，模块 ≤ 2 | 修复 bug、添加字段、调整样式 |
| **中** | AC ≤ 8，模块 ≤ 5 | 新增 API、添加页面、功能增强 |
| **大** | AC > 8 或 模块 > 5 | 新增子系统、重构核心模块 |

### 推荐流程

| 规模 | 推荐流程 | 跳过环节 |
|------|---------|---------|
| **小** | clarify → plan → run-plan → check → ship | design |
| **中** | clarify → design → plan → run-plan → check → qa → ship | — |
| **大** | clarify → design → plan → run-plan → check → qa → ship | — |

### 快速入口

| 场景 | 命令 | 说明 |
|------|------|------|
| **全流程自动编排** | `/auto-dev` | 在主对话中依次编排 design->plan->impl->check->qa，含人工确认检查点 |
| **无人值守全自动** | `~/.claude/pipeline.sh "<feature>"` | 独立终端运行，含超时/费用/锁等加固机制（CI/CD 场景） |
| 小改动 | 直接开发 → `/check` → `/ship` | 不需要走流程 |
| 修复问题 | `/fix` | 修复 check/qa 发现的问题（调用 pipeline-fixer） |
| 查看进度 | `/status` | 查看当前 Pipeline 运行进度 |

---

## 快速选择

| 你想做什么？ | 命令 | 说明 |
|-------------|------|------|
| **项目概览** | `/overview` | 接手新项目时快速理解全貌（产品视角+架构图） |
| 需求澄清 | `/clarify` | 上下文感知的精准澄清，先研究项目再提问 |
| **架构设计** | `/design` | 隔离上下文，模块划分、接口契约、数据模型 |
| 产品设计 | `/product` | 心理学视角的 PRD/交互设计 |
| **代码重构** | `/refactor` | 通用入口，自动识别语言并应用对应规则 |
| 写实施计划 | `/plan` | 隔离上下文，拆分可执行任务 + Design 评审 |
| **执行计划** | `/run-plan` | 隔离上下文，严格 TDD 执行 + Plan 评审 |
| **开发检查** | `/check` | 隔离上下文，五维代码质量检查（对抗性审查） |
| **测试验收** | `/qa` | 隔离上下文，端到端功能验收（黑盒视角） |
| 修复/调试 | `/fix` | 修复 check/qa 问题（已合并 debug 功能） |
| 隔离开发 | `/worktree` | Git Worktree 管理 |
| MCP 开发 | `/mcp-builder` | MCP 服务器开发指南 |
| Admin UI | `/admin-ui` | Ant Design 后台管理 UI 规范 |
| H5 移动端 | `/h5` | 移动端交互体验优化 |
| **安全扫描** | `/security` | 专业工具扫描 OWASP Top 10 漏洞 |
| **性能分析** | `/perf` | 定位热点函数和 N+1 查询 |
| 代码扫描 | `/scan` | 代码质量扫描（技术债） |
| **修复问题** | `/fix` | 修复 check/qa 发现的 FAIL 项（调用 pipeline-fixer SubAgent） |
| **全流程编排** | `/auto-dev` | 主对话中编排完整开发流程（含人工确认检查点） |
| **Pipeline 进度** | `/status` | 查看当前 Pipeline 运行阶段和进度 |
| **代码交付** | `/ship` | 提交、推送、创建 PR 一键完成 |

---

## 主工作流（智能流程选择）

```
/overview（项目概览）← 接手新项目时首先使用
    ↓
/clarify（需求澄清）← 必须，定义 AC
    ↓
【智能判断需求规模】
    ↓
    ├─ 小需求（AC ≤ 3）
    │   → /plan → /run-plan → /check → /ship
    │
    ├─ 中需求（AC ≤ 8）
    │   → /design → /plan → /run-plan → /check → /qa → /ship
    │
    └─ 大需求（AC > 8）
        → /design → /plan → /run-plan → /check → /qa → /ship
```

**关键说明**：
- `/design`：根据需求规模**按需调用**，小需求可跳过
- 全流程编排：`/auto-dev` 在主对话中编排（含人工确认），`pipeline.sh` 在独立终端无人值守运行

**可选分支**：
- `/product`：涉及用户体验时，在 `/clarify` 之后使用
- `/refactor`：代码重构时，替代 `/design` → `/plan` 流程

---

## Skills 详情

### 0. overview（项目概览）

**触发**：`/overview`

**用途**：接手新项目时快速理解全貌，建立认知地图

**版本**：v1.0（2025-01-26）

**核心原则**：
- **用产品视角理解代码**：不是看懂每一行，而是理解解决什么问题
- **用架构视角建立地图**：核心模块如何协作
- **给出入门指南**：新手应该从哪里开始

**输出**：
- 用通俗语言解释项目用途
- 核心模块关系图（Mermaid）
- 推荐先看的 3 个文件
- 保存到 `docs/项目概览.md`

**支持的项目类型**：
- Java/Spring 后端
- Vue/React 前端
- UniApp H5/小程序
- Python/FastAPI 后端

---

### 1. clarify（需求澄清）

**触发**：`/clarify`

**用途**：基于项目上下文的精准需求澄清，充分利用项目规范和代码信息，减少无效提问

**版本**：v2.0（上下文感知版，2025-01-22 更新）

**核心原则**：
- **先研究，再提问**：充分利用项目规范、代码、文档
- **聚焦关键疑点**：只问真正不确定的问题
- **结合项目约束**：基于规范主动告知约束，不问已知
- 一次只问一个核心问题
- 优先使用选择题（基于实际情况）

**执行流程**：
0. **项目上下文研究**（核心改进）：读取规范、读取代码、识别约束
1. 总结当前状态（展示给用户）
2. 聚焦关键疑点（问题分类：规范相关/技术实现/业务逻辑）
3. 精准提问（基于项目的具体选项）
4. 确认边界和约束（引用项目规范）
5. 输出增强版需求文档（含上下文和技术方案要点）

**改进效果**：提问轮次从 5 轮降到 2-3 轮，用户感受到「被理解」

---

### 2. design（架构设计）

**触发**：`/design`

**用途**：在隔离上下文中启动 pipeline-designer SubAgent 执行架构设计

**机制**：`context: fork` + `agent: pipeline-designer` → 自动加载 `pipeline-architecture` 知识

**核心产出**：
- handoff_design.md（模块划分、接口设计、数据模型）
- Key_Decisions.md（关键架构决策记录）

**前置条件**：有 `/clarify` 的输出

---

### 3. product（产品设计）

**触发**：`/product`，或讨论用户行为、功能设计时自动激活

**用途**：基于心理学的产品设计分析

**核心框架**：
- 认知心理学（7±2 法则、希克定律）
- 行为心理学（Fogg 模型、Hooked 模型）
- 情绪设计（三层设计、峰终定律）
- 尼尔森十大可用性原则

---

### 4. plan（写计划）

**触发**：`/plan`

**用途**：在隔离上下文中启动 pipeline-planner SubAgent，将架构蓝图拆分为可执行任务

**机制**：`context: fork` + `agent: pipeline-planner` → 自动加载 `pipeline-architecture` + `pipeline-review-standard` 知识

**双职责**：
1. 评审 Design 文档 → 输出 DESIGN_OK / DESIGN_ISSUE
2. 制定开发计划 → 输出 handoff_plan.md

**前置条件**：有 `/design` 的输出

---

### 5. refactor（代码重构 - 通用入口）

**触发**：`/refactor`

**用途**：通用重构入口，自动识别语言并应用对应的重构规则

**语言路由**：
- Java 代码 → 自动应用 Java 重构规则
- Python 代码 → 自动应用 Python 重构规则

**三大原则**：
1. **简单**：不过度设计，避免"万一将来需要"的预设
2. **合适**：该复杂时复杂（业务本身复杂），该简单时简单
3. **演化**：根据实际需求演化，重复 3 次再抽象

**重构方向**：
- **减法**：过度设计 → 删除不必要的抽象（如只有一个实现的接口）
- **加法**：设计不足 → 补充必要的抽象（如有多个实现需要切换时保留接口）
- **调整**：设计不当 → 重新划分职责

---

### 6. run-plan（执行计划）

**触发**：`/run-plan`

**用途**：在隔离上下文中启动 pipeline-implementer SubAgent，严格 TDD 执行开发

**机制**：`context: fork` + `agent: pipeline-implementer` → 自动加载 `pipeline-tdd-methodology` + `pipeline-code-quality` 知识

**双职责**：
1. 评审 Plan 文档 → 输出 PLAN_OK / PLAN_ISSUE
2. 按 Task 拓扑顺序严格 TDD 执行 → 输出 handoff_run.md

**前置条件**：有 `/plan` 的输出

---

### 7. check（开发检查）

**触发**：`/check`

**用途**：在隔离上下文中启动 pipeline-checker SubAgent，五维代码质量检查

**机制**：`context: fork` + `agent: pipeline-checker` → 自动加载 `pipeline-code-quality` + `pipeline-review-standard` 知识

**五维检查**：
1. 测试：全量测试运行结果
2. Lint：代码规范检查
3. 类型检查：静态类型分析
4. 代码质量规则：函数长度/参数/嵌套/空 catch 等
5. AC 覆盖：逐条核对验收标准

---

### 8. qa（测试验收）

**触发**：`/qa`

**用途**：在隔离上下文中启动 pipeline-qa SubAgent，端到端功能验收

**机制**：`context: fork` + `agent: pipeline-qa` → 自动加载 `pipeline-qa-methodology` 知识

**核心原则**：
- 验收标准唯一来源：handoff_clarify.md
- 与 Check 差异化：Check 验代码质量，QA 验功能正确性
- 端到端验证（黑盒视角）

---

### 9. worktree（Git Worktree）

**触发**：`/worktree`

**用途**：为开发任务创建隔离的工作目录

**优势**：
- 不影响主分支
- 并行开发多个功能
- 无需 stash 半成品代码

---

### 10. mcp-builder（MCP 开发）

**触发**：`/mcp-builder`

**用途**：构建高质量的 Model Context Protocol 服务器

**来源**：anthropics/skills（Anthropic 官方）

---

### 11. admin-ui（Admin 后台 UI）

**触发**：`/admin-ui`，或开发后台管理页面、使用 Ant Design 组件时自动激活

**用途**：Admin 后台管理系统 UI 开发规范

**技术栈**：
- 框架：React 18+ + TypeScript
- UI 组件：Ant Design 5.x
- 请求：ahooks (useRequest)
- 路由：react-router-dom v6

**核心内容**：
- 页面布局规范
- 表格规范
- 表单规范
- 弹窗规范
- 状态与反馈
- 权限控制 UI 模式

---

### 12. h5（H5 移动端开发）

**触发**：`/h5`，或开发 H5 组件、讨论移动端交互时自动激活

**用途**：移动端开发规范（UniApp + Vue3）

**核心关注**：
- 60fps 流畅动画
- 即时触摸反馈（< 100ms）
- 容错友好的错误提示
- 响应式布局

---

### 13. security（安全扫描）

**触发**：`/security`

**用途**：使用专业工具检测安全漏洞，覆盖 OWASP Top 10

**版本**：v1.2（2026-01-28）

**核心工具**：
- **SAST**: Bandit (Python) + Semgrep (多语言)
- **密钥扫描**: Gitleaks
- **依赖漏洞**: pip-audit / npm audit
- **容器安全**: Trivy

**执行模式**：
| 模式 | 说明 |
|------|------|
| `/security` | 默认完整扫描 |
| `/security quick` | 快速扫描 (<30s) |
| `/security full` | 全面扫描 + AI 审查 |
| `/security deps` | 仅依赖漏洞 |
| `/security docker` | 容器镜像扫描 |
| `/security fix` | 扫描 + 自动修复 |

**输出**：
- 终端摘要（严重/高危/中危/低危）
- 完整报告 → `docs/安全扫描/[日期]_安全扫描报告.md`
- 每个漏洞附可执行修复代码

**铁律**：工具优先、修复完整、不隐瞒严重漏洞

---

### 14. perf（性能分析）

**触发**：`/perf`

**用途**：使用专业工具定位性能瓶颈，输出火焰图和优化建议

**版本**：v1.2（2026-01-28）

**核心工具**：
- **CPU 热点**: pyinstrument / py-spy / scalene
- **N+1 检测**: nplusone / fastapi-sqlalchemy-monitor
- **内存分析**: memory_profiler / tracemalloc

**执行模式**：
| 模式 | 说明 |
|------|------|
| `/perf` | 默认 pyinstrument 分析 |
| `/perf quick` | 热点 Top 10 (<30s) |
| `/perf deep` | scalene 全面分析 |
| `/perf n1` | N+1 查询检测 |
| `/perf memory` | 内存分析 |
| `/perf attach <pid>` | 附加运行中进程 |
| `/perf flame` | 生成火焰图 |

**输出**：
- 终端摘要（热点 Top 5 + N+1 问题）
- HTML 报告 → `docs/性能分析/[日期]_性能分析报告.html`
- 火焰图 → `docs/性能分析/[日期]_flame.svg`

**铁律**：数据驱动（禁止猜测）、可视化、可量化、可操作

---

### 15. scan（代码扫描）

**触发**：`/scan [项目路径]`

**用途**：扫描项目整体代码质量，发现存量技术债

**版本**：v1.0（2025-01-26）

**与 /check 的区别**：
| 维度 | /check | /scan |
|------|--------|-------|
| 范围 | 变更文件（git diff） | 全项目 |
| 时机 | 开发完成后 | 定期巡检、接手项目 |
| 输出 | 通过/不通过 | 健康度评分 + 详细报告 |

**检测内容**：
- 铁律检测（降级/硬编码/Mock）
- 安全漏洞（SQL 注入/XSS）
- 代码规范（函数长度/空 catch）
- 技术债（TODO/FIXME/废弃代码）

**输出**：
- 健康度评分 (0-100)
- 详细报告 → `docs/技术债扫描/[日期]_技术债扫描报告.md`

---

### 16. ship（代码交付）

**触发**：`/ship`

**用途**：一键完成代码提交、推送和 PR 创建

**核心流程**：
1. 检查 git 状态
2. 分析变更内容
3. 自动生成 commit message（用户确认）
4. 提交代码
5. 推送远程
6. 创建 PR（可选）

**安全特性**：
- 敏感文件检测（.env、credentials 等）
- 推送前确认
- 禁止 force push

**前置条件**：`/check` 或 `/qa` 通过后使用

---

### 17. auto-dev（全流程自动开发）

**触发**：`/auto-dev`

**用途**：在主对话中编排完整开发流程（design->plan->run-plan->check->qa）

**与 pipeline.sh 的区别**：

| 维度 | /auto-dev | pipeline.sh |
|------|-----------|-------------|
| 运行环境 | 主对话中 | 独立终端 |
| 人工介入 | 实时确认检查点 | touch 文件确认 |
| 加固机制 | 无（依赖 Claude Code 原生） | 超时/费用/锁/回滚锚点 |
| 适用场景 | 日常开发 | 无人值守/CI/CD |

**前置条件**：有 `/clarify` 的输出

---

## 典型工作流

### 小改动
```
直接开发 → /check → /ship
```

### 中等功能
```
/clarify → /design → /plan → /run-plan → /check → /qa → /ship
```

### 大型功能
```
/clarify → /design → /plan
→ /worktree → /run-plan → /check → /qa → /ship
```

### 修复问题
```
/fix → /check → /ship
```

### 代码重构
```
/refactor → 输出重构计划 → /run-plan → /check → /qa → /ship
```
