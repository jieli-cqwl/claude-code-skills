---
name: perf
command: perf
user_invocable: true
parallel_mode: true
description: 性能分析诊断。在发现慢接口、性能优化、上线前验收时使用。使用专业工具（pyinstrument/py-spy/nplusone）定位热点函数和 N+1 查询，输出火焰图和可视化报告。
---

# 性能分析 (Performance)

> **角色**：性能工程师
> **目标**：使用专业工具定位性能瓶颈，提供可量化的优化方案
> **原则**：数据驱动、工具先行、可视化输出
> **思考模式**：启用 ultrathink 深度思考，系统分析性能问题

---

## 核心原则

**"不要猜测，要测量"**

性能优化必须基于数据：profiler 采样 → 定位热点 → 针对性优化 → 验证效果。

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**性能分析**"或"**分析性能**"（主触发词）
- 使用命令：`/perf`
- 说"太慢了"、"卡"、"为什么这么慢"
- 说"优化性能"、"提升速度"
- 说"有 N+1 查询吗"

**何时使用**：

| 场景 | 使用 |
|------|------|
| 发现慢接口 (>500ms) | ✅ 必须 |
| 性能优化专项 | ✅ 必须 |
| 上线前性能验收 | ✅ 推荐 |
| 生产环境卡顿 | ✅ 用 `/perf attach` |
| 内存泄漏排查 | ✅ 用 `/perf memory` |
| 代码审查 | ❌ 用 `/check` 或 `/scan` |

---

## 执行模式

```bash
/perf                  # 默认：pyinstrument 采样分析
/perf quick            # 快速：热点 Top 10 (<30s)
/perf deep             # 深度：scalene 全面分析 (CPU+内存+GPU)
/perf n1               # N+1：检测 ORM 查询问题
/perf memory           # 内存：memory_profiler 分析
/perf attach <pid>     # 附加：py-spy 附加运行中进程
/perf flame            # 火焰图：生成交互式火焰图
/perf sql              # SQL：慢查询分析
/perf compare          # 对比：优化前后性能对比
/perf async            # 异步：asyncio 代码分析
/perf baseline <target> # 基准：设定性能目标
/perf run <command>    # 运行：分析指定命令
/perf test <test_file> # 测试：分析测试用例
```

---

## 工具选择矩阵

| 工具 | 类型 | 开销 | 生产可用 | 多线程 | 输出 |
|------|------|------|----------|--------|------|
| **pyinstrument** | 统计采样 | 低 | ⚠️ 开发 | ❌ | HTML/JSON |
| **py-spy** | 进程外采样 | 极低 | ✅ | ✅ | 火焰图 |
| **cProfile** | 确定性 | 高 (2-5x) | ❌ | ❌ | pstats |
| **scalene** | 综合 | 低 | ⚠️ | ✅ | HTML |
| **memory_profiler** | 内存 | 高 | ❌ | ❌ | 文本/图表 |
| **line_profiler** | 行级 | 高 | ❌ | ❌ | 文本 |

### 场景推荐

| 场景 | 推荐工具 |
|------|----------|
| 日常开发调试 | pyinstrument |
| 生产问题诊断 | py-spy |
| 全面性能分析 | scalene |
| 内存泄漏排查 | memory_profiler |
| 热点函数深入 | line_profiler |

---

## 执行流程

```
/perf [mode]
    ↓
Phase 1: 环境检测
    - 检测项目类型 (Python/Node/Java)
    - 检查工具可用性
    - 识别入口文件/测试用例
    ↓
Phase 2: 数据采集
    ┌──────────────────────────────────────────┐
    │  CPU: pyinstrument / py-spy / scalene    │
    │  内存: memory_profiler / tracemalloc     │
    │  SQL: nplusone / sqlalchemy-monitor      │
    └──────────────────────────────────────────┘
    ↓
Phase 3: 分析定位
    - 识别热点函数 (>10% 时间占比)
    - 检测 N+1 查询
    - 检测内存异常
    ↓
Phase 4: 生成报告
    - 终端摘要
    - HTML 可视化报告
    - 火焰图 (SVG)
    ↓
Phase 5: 优化建议
    - 每个热点提供优化方案
    - 预估优化收益
```

---

## 并行架构

### Phase 1: 并行分析（8 Agent，subagent_type=Bash）

同时启动以下 8 个分析任务：

| Agent | 分析任务 | 工具 | 输出 |
|-------|---------|------|------|
| Agent 1 | CPU 热点分析 | pyinstrument/py-spy | 热点函数列表 |
| Agent 2 | 内存使用分析 | memory_profiler/tracemalloc | 内存分配报告 |
| Agent 3 | I/O 瓶颈分析 | strace/iostat | I/O 等待时间 |
| Agent 4 | N+1 查询检测 | nplusone | N+1 问题列表 |
| Agent 5 | 查询优化分析 | EXPLAIN/慢查询日志 | 索引建议、慢查询列表（不涉及缓存） |
| Agent 6 | 并发性能分析 | py-spy/threading | 锁竞争、线程阻塞 |
| Agent 7 | 网络延迟分析 | requests/aiohttp 监控 | 外部调用耗时 |
| Agent 8 | 资源泄漏检测 | objgraph/gc | 对象引用、连接泄漏 |

**等待所有 Agent 完成后继续。**

### Phase 2: 并行优化建议（8 Agent，subagent_type=general-purpose）

各 Agent 为发现的问题生成优化方案：

| Agent | 优化范围 | 输出 |
|-------|---------|------|
| Agent 1 | CPU 热点优化 | 算法优化、并行化建议 |
| Agent 2 | 内存优化 | 对象池、生成器改造建议 |
| Agent 3 | I/O 优化 | 异步化、批量化建议 |
| Agent 4 | N+1 修复 | joinedload/prefetch 代码 |
| Agent 5 | 查询优化 | 索引创建语句、查询重写 |
| Agent 6 | 并发优化 | 锁优化、异步改造建议 |
| Agent 7 | 网络优化 | 连接池、重试策略建议 |
| Agent 8 | 泄漏修复 | 资源释放、上下文管理器建议 |

**约束（缓存需人工确认）**：
- 涉及缓存的建议必须标注"需人工确认"
- 不自动添加缓存代码
- 缓存建议格式：`⚠️ 缓存建议（需人工确认）：[具体建议]`
- 原因：早期系统缓存弊大于利，需人工评估缓存失效、一致性等问题

**等待所有 Agent 完成后继续。**

### Phase 3: 汇总报告（串行）

主 Agent 汇总所有分析结果：

1. **按影响程度排序**：将所有问题按性能影响（时间占比/耗时）降序排列
2. **生成火焰图**：合并 CPU 分析数据生成交互式火焰图
3. **输出优化建议**：每个问题附带具体修复方案和预估收益
4. **生成最终报告**：HTML 报告 + Markdown 摘要

### 错误处理

**单 Agent 失败处理**：
- 记录失败原因和堆栈
- 其他 Agent 继续执行
- 最终报告中标注"[分析名称] 分析失败：[原因]"

**超时处理**：
- 单个分析任务超时时间：5 分钟
- 超时后终止该 Agent，记录已收集的部分数据
- 报告中标注"[分析名称] 分析超时，数据可能不完整"

**全部失败处理**：
- 如果所有 Agent 都失败，输出环境诊断信息
- 提示用户检查：工具安装、权限、目标进程状态

---

## Phase 1: 环境检测

### 项目类型检测

| 标识文件 | 项目类型 | 推荐工具 | 支持程度 |
|---------|----------|----------|----------|
| `pyproject.toml` / `requirements.txt` | Python | pyinstrument + nplusone | ✅ 完整支持 |
| `package.json` | Node.js | clinic.js + 0x | ⚠️ 基础支持 |
| `pom.xml` / `build.gradle` | Java | async-profiler + JFR | ⚠️ 基础支持 |
| `go.mod` | Go | pprof | ⚠️ 基础支持 |

**说明**：当前版本主要针对 Python 项目优化，其他语言提供基础工具指引。

### 识别入口文件/测试用例

性能分析需要运行代码才能采样。按以下优先级识别入口：

```
1. 用户指定: /perf run src/main.py
    ↓ (如未指定)
2. pytest 测试: pytest tests/ --benchmark
    ↓ (如无测试)
3. 常见入口文件:
   - Python: main.py, app.py, manage.py, wsgi.py
   - FastAPI: uvicorn main:app
   - Django: python manage.py runserver
    ↓ (如都找不到)
4. 询问用户: "请指定要分析的入口文件或命令"
```

**推荐方式**：
```bash
# 分析特定脚本
/perf run python src/heavy_task.py

# 分析 API 端点（配合 curl/httpie 触发请求）
/perf run "uvicorn main:app" --trigger "curl http://localhost:8000/api/slow"

# 分析测试用例
/perf test tests/test_performance.py
```

### 工具安装检测

检测到工具缺失时的交互：
```
⚠️ 检测到以下工具未安装:
   - pyinstrument (CPU 采样)
   - nplusone (N+1 检测)

🔧 是否自动安装？ [Y/n]
```

```bash
# Python 性能工具
pip install pyinstrument py-spy scalene memory_profiler line_profiler

# N+1 检测
pip install nplusone fastapi-sqlalchemy-monitor

# 验证
pyinstrument --version && py-spy --version
```

---

## Phase 2: 数据采集

### 2.1 CPU 热点分析

**pyinstrument (开发环境)**:
```bash
# 命令行运行
pyinstrument -o profile.html script.py

# 代码中使用
from pyinstrument import Profiler
profiler = Profiler()
profiler.start()
# ... 被测代码 ...
profiler.stop()
profiler.print()
```

**py-spy (生产环境)**:
```bash
# 附加到运行中进程
py-spy top --pid <PID>

# 生成火焰图
py-spy record -o flame.svg --pid <PID>

# 运行并分析
py-spy record -o flame.svg -- python script.py
```

**scalene (全面分析)**:
```bash
scalene --html --outfile profile.html script.py
```

### 2.2 N+1 查询检测

**nplusone (SQLAlchemy/Django)**:
```python
# settings.py 或 conftest.py
NPLUSONE_RAISE = True  # 检测到 N+1 时抛异常

# pytest 插件
pytest --nplusone-fail
```

**fastapi-sqlalchemy-monitor**:
```python
from fastapi_sqlalchemy_monitor import SQLAlchemyMonitorMiddleware

app.add_middleware(
    SQLAlchemyMonitorMiddleware,
    engine=engine,
    warn_threshold=10,  # 单请求超过 10 次查询告警
)
```

### 2.3 内存分析

**memory_profiler**:
```bash
# 逐行内存分析
python -m memory_profiler script.py

# 装饰器方式
@profile
def my_function():
    ...
```

**tracemalloc (标准库)**:
```python
import tracemalloc
tracemalloc.start()
# ... 代码 ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

### 2.4 SQL 慢查询

**SQLAlchemy echo**:
```python
engine = create_engine(url, echo=True)  # 打印所有 SQL
```

**慢查询日志 (PostgreSQL)**:
```sql
-- 开启慢查询日志
ALTER SYSTEM SET log_min_duration_statement = 100;  -- 记录 >100ms 的查询
SELECT pg_reload_conf();
```

### 2.5 异步代码分析

**asyncio 内置调试**:
```python
import asyncio
asyncio.get_event_loop().set_debug(True)  # 开启调试模式，检测慢回调
```

**py-spy 对 asyncio 的支持**:
```bash
# py-spy 可以分析异步代码的调用栈
py-spy record -o async_flame.svg -- python async_app.py
```

**aiomonitor (异步任务监控)**:
```python
import aiomonitor
with aiomonitor.start_monitor(loop):
    loop.run_forever()
# 然后用 nc localhost 50101 连接监控
```

### 2.6 性能对比

运行 `/perf compare` 时，自动：
1. 读取上次报告 (`docs/性能分析/` 最新文件)
2. 运行当前分析
3. 生成对比表

**对比报告格式**:
```
┌─────────────────────────────────────────────────┐
│  指标          优化前      优化后      变化     │
├─────────────────────────────────────────────────┤
│  总耗时        2.34s       1.12s      -52.1%   │
│  热点函数      5 个        2 个       -60%     │
│  N+1 问题      3 个        0 个       -100%    │
└─────────────────────────────────────────────────┘
```

---

## Phase 3: 分析定位

### 性能基准设定

使用 `/perf baseline` 设定性能目标，让"慢"有明确定义：

```bash
# 设定 API 响应时间目标
/perf baseline api:200ms

# 设定批量任务目标
/perf baseline batch:5s

# 设定内存目标
/perf baseline memory:512MB
```

**默认基准**（如未设定）：

| 场景 | 默认目标 | 说明 |
|------|----------|------|
| API 响应 | <200ms | 用户可感知阈值 |
| 页面加载 | <1s | 首屏渲染 |
| 批量任务 | <30s | 单批次 |
| 内存占用 | <1GB | 单进程 |

**基准配置文件** (`.perf-baseline.yaml`)：
```yaml
# 项目性能基准
api:
  p50: 100ms
  p95: 200ms
  p99: 500ms
batch:
  max_time: 30s
memory:
  max_rss: 1GB
n1:
  max_queries_per_request: 10
```

### 热点识别标准

| 指标 | 阈值 | 说明 |
|------|------|------|
| 函数时间占比 | >10% | 需要关注 |
| 函数时间占比 | >30% | 必须优化 |
| 单次调用耗时 | >100ms | 需要关注（或超过基准） |
| 调用次数 | >1000/请求 | 可能是循环问题 |

### N+1 检测标准

| 指标 | 阈值 | 说明 |
|------|------|------|
| 单请求查询数 | >10 | 可能存在 N+1 |
| 相同查询重复 | >3 次 | 确认是 N+1 |
| 关联查询无预加载 | 存在 | 需要 joinedload |

### 内存异常标准

| 指标 | 阈值 | 说明 |
|------|------|------|
| 内存持续增长 | 线性增长 | 可能泄漏 |
| 单对象占用 | >100MB | 需要关注 |
| 对象数量 | 持续增长 | 需要排查引用 |

---

## Phase 4: 报告格式

### 终端输出

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 性能分析报告 - [项目名]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 总耗时: 2.34s | 采样: 1000 次

🔥 热点函数 TOP 5:
  1. 45.2% (1.06s) - db.query() @ src/repository.py:89
     → 建议: 添加索引或使用缓存
  2. 23.1% (0.54s) - json.loads() @ src/api/handler.py:45
     → 建议: 使用 orjson 替代
  3. 12.8% (0.30s) - encrypt() @ src/utils/crypto.py:23
     → 建议: 考虑异步或缓存
  ...

⚠️ N+1 查询检测:
  - User.posts 触发 N+1 (查询 52 次)
    → 修复: 使用 joinedload(User.posts)

📄 完整报告: docs/性能分析/[日期]_性能分析报告.html
🔥 火焰图: docs/性能分析/[日期]_flame.svg
```

### HTML 报告结构

报告包含：
- 交互式火焰图
- 热点函数调用栈
- 时间线视图
- 内存分配图（如使用 scalene）

### Markdown 摘要

```markdown
# 性能分析报告

## 概览
- 分析时间: YYYY-MM-DD HH:MM
- 总耗时: X.XXs
- 热点函数: X 个
- N+1 问题: X 个

## 热点函数

### 1. db.query() - 45.2%
- **位置**: `src/repository.py:89`
- **调用次数**: 156 次
- **平均耗时**: 6.8ms
- **优化建议**:
  - 添加数据库索引
  - 实现查询缓存
- **预估收益**: 优化后可减少 30-40% 耗时

## N+1 查询

### User.posts
- **触发位置**: `src/api/users.py:34`
- **查询次数**: 52 次
- **修复代码**:
```python
# Before
users = session.query(User).all()
for user in users:
    print(user.posts)  # N+1!

# After
users = session.query(User).options(joinedload(User.posts)).all()
```
```

---

## Phase 5: 优化建议库

### 常见热点优化

| 热点类型 | 优化方案 | 预估收益 |
|---------|---------|---------|
| 数据库查询 | 添加索引/缓存 | 50-90% |
| JSON 序列化 | 使用 orjson/ujson | 30-50% |
| 循环中 I/O | 批量操作/异步 | 60-80% |
| 正则匹配 | 预编译/简化模式 | 20-40% |
| 加密操作 | 缓存结果/异步 | 30-50% |
| 大对象复制 | 使用引用/生成器 | 40-60% |

### N+1 修复模板

**SQLAlchemy**:
```python
# 使用 joinedload
from sqlalchemy.orm import joinedload
query.options(joinedload(Model.relation))

# 使用 selectinload (一对多推荐)
from sqlalchemy.orm import selectinload
query.options(selectinload(Model.relations))

# 使用 subqueryload
from sqlalchemy.orm import subqueryload
query.options(subqueryload(Model.relations))
```

**Django**:
```python
# select_related (外键/一对一)
User.objects.select_related('profile')

# prefetch_related (多对多/反向外键)
User.objects.prefetch_related('posts')
```

---

## 危险信号（停止并报告）

- 单个函数占用 >80% 时间（可能是死循环）
- 内存在短时间内增长 >1GB（可能是泄漏）
- 数据库连接数持续增长（连接泄漏）
- profiler 本身报错（代码可能有问题）

---

## 常见借口（都是错的）

| 借口 | 现实 |
|------|------|
| "在我机器上很快" | 生产环境数据量不同 |
| "用户不会注意到" | 慢 100ms 用户就能感知 |
| "优化是过早的" | 明显的热点不是过早优化 |
| "硬件升级就行" | 代码问题升级硬件也没用 |
| "这是框架的问题" | 大多数是使用方式问题 |

---

## 工具安装指南

### 一键安装

```bash
# 核心工具
pip install pyinstrument py-spy scalene memory_profiler

# N+1 检测
pip install nplusone

# FastAPI 专用
pip install fastapi-sqlalchemy-monitor

# 验证
pyinstrument --version
py-spy --version
scalene --version
```

### py-spy 权限问题

macOS/Linux 可能需要 sudo 或调整权限：
```bash
# macOS
sudo py-spy record -o flame.svg --pid <PID>

# Linux (无需 sudo)
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

---

## 与其他 Skills 的关系

```
/clarify → /explore → /design → /plan
                                   ↓
                        /run-plan (开发)
                                   ↓
                   ┌───────────────┼───────────────┐
                   ↓               ↓               ↓
               /security       /perf ← 当前     /scan
                   │               │               │
                   └───────────────┼───────────────┘
                                   ↓
                                /check
                                   ↓
                                 /qa
                                   ↓
                                /ship
```

---

## 完成检查清单

- [ ] 工具环境已检测
- [ ] CPU 热点已分析 (pyinstrument/py-spy)
- [ ] N+1 查询已检测 (nplusone)
- [ ] 热点 Top 5 已识别
- [ ] 每个热点有优化建议
- [ ] HTML 报告已生成
- [ ] 火焰图已生成（如适用）
- [ ] 报告已保存到 `docs/性能分析/`

---

## ⛔ 铁律约束

| 约束 | 要求 |
|------|------|
| **数据驱动** | 必须先运行 profiler，禁止仅靠猜测 |
| **可视化** | 必须输出 HTML 报告或火焰图 |
| **可量化** | 每个热点必须有百分比和耗时数据 |
| **可操作** | 每个热点必须附优化建议 |
| **报告位置** | 必须保存到 `docs/性能分析/` 目录（自动创建） |
| **基准对比** | 有基准时，报告必须标注是否达标 |

### 报告目录处理

保存报告前自动创建目录：
```bash
mkdir -p docs/性能分析
```

如果项目根目录没有 `docs/` 文件夹，先创建完整路径。

---

## ✅ 完成提示

```
✅ 性能分析完成

⚡ 总耗时: X.XXs
   🔥 热点函数: X 个
   ⚠️ N+1 问题: X 个
   💾 内存问题: X 个

📄 报告: docs/性能分析/[日期]_性能分析报告.html
🔥 火焰图: docs/性能分析/[日期]_flame.svg

🎯 下一步:
1. 优先解决 Top 3 热点（预计提升 XX%）
2. 修复 N+1 查询问题
3. 优化后重新运行 /perf 验证效果
```

---

**版本**：v1.2
**创建日期**：2026-01-28
**更新日期**：2026-01-28
**参考**：[调研报告](docs/设计文档/调研_security_perf.md)

**更新日志**：
- v1.2: 增加入口识别流程、性能基准设定、明确语言支持范围、报告目录自动创建
- v1.1: 增加异步代码分析 (asyncio)、性能对比功能
