# Agent Assignments - 8 Agent 并行分工详情

> 本文件从 `SKILL.md` 拆出，包含 8 个并行 Agent 的详细分工表、启动指令和错误处理策略。

---

## Agent 分工表

| Agent | 任务 | 收集内容 | 返回格式 |
|-------|------|---------|---------|
| Agent 1 | 目录结构分析 | 项目目录树、核心目录识别 | `{directories: [], core_modules: []}` |
| Agent 2 | 技术栈识别 | 框架、语言、构建工具、版本 | `{framework: "", language: "", build_tool: "", versions: {}}` |
| Agent 3 | 依赖关系分析 | 外部依赖、内部模块依赖 | `{external_deps: [], internal_deps: []}` |
| Agent 4 | 核心模块识别 | 业务模块、职责、关键文件 | `{modules: [{name, responsibility, key_files}]}` |
| Agent 5 | API 端点收集 | 路由、接口、HTTP 方法 | `{endpoints: [{path, method, description}]}` |
| Agent 6 | 数据模型分析 | 实体、表结构、关系 | `{models: [{name, fields, relations}]}` |
| Agent 7 | 配置文件分析 | 环境配置、关键配置项 | `{configs: [{file, key_settings}]}` |
| Agent 8 | 文档收集 | README、现有文档、注释 | `{docs: [{file, summary}], readme_summary: ""}` |

---

## Agent 启动指令

```yaml
parallel_tasks:
  - name: "目录结构分析"
    subagent_type: Explore
    task: |
      分析项目目录结构，识别核心目录和模块边界。
      返回 JSON: {directories: [...], core_modules: [...]}

  - name: "技术栈识别"
    subagent_type: Explore
    task: |
      识别项目使用的技术栈（框架、语言、构建工具）及版本。
      检查: package.json, pom.xml, pyproject.toml, go.mod 等
      返回 JSON: {framework, language, build_tool, versions}

  - name: "依赖关系分析"
    subagent_type: Explore
    task: |
      分析项目的外部依赖和内部模块依赖关系。
      返回 JSON: {external_deps: [...], internal_deps: [...]}

  - name: "核心模块识别"
    subagent_type: Explore
    task: |
      识别项目的核心业务模块、职责和关键文件。
      返回 JSON: {modules: [{name, responsibility, key_files}]}

  - name: "API 端点收集"
    subagent_type: Explore
    task: |
      收集项目暴露的 API 端点信息。
      返回 JSON: {endpoints: [{path, method, description}]}

  - name: "数据模型分析"
    subagent_type: Explore
    task: |
      分析项目的数据模型、表结构和关系。
      返回 JSON: {models: [{name, fields, relations}]}

  - name: "配置文件分析"
    subagent_type: Explore
    task: |
      分析项目的配置文件和关键配置项。
      返回 JSON: {configs: [{file, key_settings}]}

  - name: "文档收集"
    subagent_type: Explore
    task: |
      收集项目现有文档、README 和关键注释。
      返回 JSON: {docs: [{file, summary}], readme_summary: ""}
```

**等待所有 Agent 完成后继续。**

---

## 错误处理

**单个 Agent 失败**：

```yaml
error_handling:
  strategy: partial_success
  rules:
    - if_failed: "Agent 1-4"  # 核心信息
      action: retry_once
      fallback: abort_with_message
    - if_failed: "Agent 5-8"  # 辅助信息
      action: continue_without
      note: "在输出中标注缺失部分"
```

| 失败场景 | 处理方式 |
|---------|---------|
| Agent 1-4 失败（核心信息） | 重试一次，仍失败则终止并报告 |
| Agent 5-8 失败（辅助信息） | 继续执行，在输出中标注缺失 |
| 超过 3 个 Agent 失败 | 终止并建议用户检查项目结构 |
| 超时（单个 Agent > 60s） | 终止该 Agent，使用已有结果 |

**错误报告格式**：

```markdown
⚠️ 部分信息收集失败：
- [失败的 Agent]: [失败原因]

已完成的分析：
- [成功收集的信息列表]

建议：
- [根据失败原因给出的建议]
```
