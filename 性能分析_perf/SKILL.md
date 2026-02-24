---
name: perf
command: perf
user_invocable: true
parallel_mode: true
description: |
  性能分析诊断。自动激活场景：
  1) 用户说"太慢了"、"性能怎么样"、"卡"、"响应慢"、"为什么这么慢"时
  2) 用户说"优化性能"、"提升速度"、"有 N+1 查询吗"、"哪里是瓶颈"时
  3) 上线前需要性能验收时
  使用专业工具（pyinstrument/py-spy/nplusone）定位热点函数和 N+1 查询，输出火焰图和可视化报告。
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

> 需要工具详细配置时，读取 `references/tool-usage.md`

> 需要优化模式参考时，读取 `references/optimization-patterns.md`

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
