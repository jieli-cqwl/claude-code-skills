---
name: parallel
command: parallel
user_invocable: true
description: 并行 Agent 调度。当有多个独立问题需要调查时，启动多个 agent 并行处理，大幅提升效率。适用于多测试失败、多子系统问题、批量调研。
---

# Dispatching Parallel Agents

> 全房通项目专用并行调度流程

---

## 核心理念

> "当有多个不相关的问题（不同测试文件、不同子系统、不同 bug），顺序调查是浪费时间。"

每个独立问题域分配一个 agent，并行工作。

---

## 何时使用

### ✅ 适用场景

| 场景 | 示例 |
|------|------|
| 多文件测试失败 | 3 个测试文件失败，原因各不相同 |
| 多子系统问题 | 前端、后端、Celery 各有问题 |
| 独立调查任务 | 调研多个模块的实现方式 |
| 批量代码审查 | 审查多个 PR 或多个模块 |

### ❌ 不适用场景

| 场景 | 原因 |
|------|------|
| 问题相互关联 | 需要完整上下文 |
| 需要完整系统视角 | 无法分割 |
| 探索性调试 | 方向不明确 |
| 会竞争同一资源 | 会产生冲突 |

---

## 执行流程

### Step 1: 按领域分组

将问题分类到独立的领域：

```markdown
## 问题分类

### 领域 A: 后端 API
- `backend/app/api/v1/documents.py` 报错
- 错误：xxx

### 领域 B: Celery 任务
- `backend/app/tasks/resource_tasks.py` 任务失败
- 错误：yyy

### 领域 C: 前端组件
- `frontend/src/pages/DocumentList.tsx` 类型错误
- 错误：zzz
```

### Step 2: 创建聚焦任务

每个 agent 的任务描述应该是：

```markdown
## Agent 任务模板

**范围**：[具体的问题域]

**目标**：调查并修复 [具体测试/问题]

**上下文**：
- 错误信息：[完整错误]
- 相关文件：[文件列表]
- 已知信息：[已有的调查结果]

**约束**：
- 只关注 [范围] 内的代码
- 不要修改 [其他模块]
- 遵循 /debug 流程
- 遵循项目铁律（禁止降级、禁止硬编码）

**输出格式**：
- 根因分析
- 修复方案
- 相关代码改动
```

### Step 3: 并行执行

```python
# 使用 Task tool 并行启动多个 agent
Task(
  subagent_type="general-purpose",
  prompt="调查后端 API 问题...",
  run_in_background=True
)

Task(
  subagent_type="general-purpose",
  prompt="调查 Celery 任务问题...",
  run_in_background=True
)

Task(
  subagent_type="general-purpose",
  prompt="调查前端组件问题...",
  run_in_background=True
)
```

### Step 4: 整合结果

```markdown
## 结果整合

### Agent A 结果
- 根因：xxx
- 修复：yyy

### Agent B 结果
- 根因：xxx
- 修复：yyy

### Agent C 结果
- 根因：xxx
- 修复：yyy

### 冲突检查
- [ ] 检查修复之间是否有冲突
- [ ] 运行完整测试套件
- [ ] 确认所有问题已解决
```

---

## 项目特定领域划分

### 按模块划分

| 领域 | 文件范围 | 常见问题 |
|------|---------|---------|
| **后端 API** | `backend/app/api/` | 路由、参数校验 |
| **后端服务** | `backend/app/services/` | 业务逻辑、数据库操作 |
| **Celery 任务** | `backend/app/tasks/` | 异步任务、超时 |
| **向量服务** | `backend/app/services/rag_*` | Qdrant、Embedding |
| **前端页面** | `frontend/src/pages/` | 组件、状态管理 |
| **前端 API** | `frontend/src/api/` | 请求、响应处理 |

### 按服务划分

| 领域 | 相关组件 | 检查命令 |
|------|---------|---------|
| **MySQL** | 数据库连接、ORM | `cd backend && python -c "from app.core.database import engine; print(engine.url)"` |
| **Qdrant** | 向量库连接、检索 | `curl http://localhost:6333/collections` |
| **Redis** | 缓存、Celery Broker | `redis-cli ping` |
| **OSS** | 文件存储 | 检查 `.env` 中的 OSS 配置 |

---

## 任务描述要点

好的任务描述是：

| 特征 | 说明 |
|------|------|
| **聚焦** | 一个明确的问题域 |
| **自包含** | 包含理解问题所需的所有上下文 |
| **有边界** | 明确说明不要碰什么 |
| **有格式** | 指定输出格式便于整合 |
| **有约束** | 强调项目铁律 |

---

## 优势

| 优势 | 说明 |
|------|------|
| **并行化** | 多个调查同时进行 |
| **专注度高** | 每个 agent 只关注一个问题 |
| **独立性** | agent 之间不会相互干扰 |
| **更快解决** | 3 倍以上的速度提升（取决于问题数量） |

---

## ✅ 完成提示

当所有并行任务完成后，输出：

```
✅ 并行任务完成

下一步：汇总结果后继续主流程（/check 或 /run-plan）
```
