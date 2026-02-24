---
name: status
command: status
user_invocable: true
description: Pipeline 进度查询。查看当前项目的 Pipeline 运行状态、阶段进度和最近检查结果。
---

# Pipeline 进度查询 (Status)

> **目标**：展示当前项目 Pipeline 的运行状态和详细进度
> **层级**：L2 主动查询（对应 L1 Status Line 被动显示）

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 使用命令：`/status`
- 说"Pipeline 进度"、"查看进度"
- 说"当前状态"、"运行到哪了"
- 说"Pipeline 跑得怎么样了"

---

## 执行流程

```
1. 搜索进度文件 → 解析 JSON → 格式化展示
2. 无进度文件 → 提示无活跃 Pipeline
```

---

## 实现逻辑

### 步骤 1: 搜索进度文件

在当前项目根目录下搜索所有 `.pipeline-progress-*.json` 文件：

```bash
ls -t .pipeline-progress-*.json 2>/dev/null
```

- 如果没有找到任何文件，跳到步骤 3（无活跃 Pipeline）
- 如果找到文件，对每个文件执行步骤 2

### 步骤 2: 解析并展示进度

读取每个 `.pipeline-progress-{feature}.json` 文件，文件结构预期如下：

```json
{
  "feature": "用户管理",
  "current_step": "implement",
  "step_index": 3,
  "total_steps": 6,
  "status": "running",
  "start_time": "2026-02-13T15:18:00",
  "elapsed_seconds": 720,
  "fix_count": 0,
  "cli_backend": "claude",
  "last_updated": "2026-02-13T15:30:00"
}
```

按以下格式展示（每个 Pipeline 一段）：

```
Pipeline 进度：{feature}
+-- 当前步骤：{current_step} ({step_index}/{total_steps})
+-- 状态：{status}
+-- 已用时间：{elapsed_seconds / 60} 分钟
+-- 修复次数：{fix_count}
+-- CLI Backend：{cli_backend}
+-- 上次更新：{last_updated}
```

**阶段参考表**（帮助用户理解进度）：

| 序号 | 阶段 | 说明 |
|------|------|------|
| 1 | design | 架构设计 |
| 2 | plan | 开发计划 |
| 3 | implement | 编码实现 |
| 4 | check | 代码检查 |
| 5 | qa | 测试验收 |
| 6 | ship | 代码交付 |

如果 `status` 为 `failed`，额外提示用户检查日志文件 `.pipeline-log-{feature}.txt`。

### 步骤 3: 无活跃 Pipeline

如果没有找到任何进度文件，展示：

```
当前没有活跃的 Pipeline。

启动方式：
  - 使用 /clarify 开始新需求，完成后启动 Pipeline
  - 或直接运行：~/.claude/pipeline.sh "{feature名}" {项目路径}
```

---

## Few-shot 对比示例

### 好的进度报告

```
[auto-dev] 进度: clarify(DONE) -> design(DONE) -> plan(IN PROGRESS) -> run-plan -> check -> qa
当前阶段: 编写实施计划（Task 拆分中，预计 5 个 Tasks）
耗时: 12 分钟 | Token: ~45K
```

### 坏的进度报告

```
正在处理中...
```
（无具体阶段、无进度指示、无时间信息，用户无法判断是否正常运行）

---

## 注意事项

- 此 Skill 是**只读**操作，不修改任何文件
- 进度文件由 `pipeline.sh` 写入，此 Skill 仅读取展示
- 多个 Pipeline 并行时，按 feature 分别列出所有进度
- 展示时间使用**分钟**为单位（`elapsed_seconds / 60`，取整）
- 如果 JSON 解析失败，提示文件格式异常并显示文件路径
