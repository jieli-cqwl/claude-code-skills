# 性能分析工具详细配置

> 来源：perf SKILL.md 拆分
> 按需加载：主文件中通过 `读取 references/tool-usage.md` 引用

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
