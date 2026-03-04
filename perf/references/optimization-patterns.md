# 性能优化模式参考

> 来源：perf SKILL.md 拆分
> 按需加载：主文件中通过 `读取 references/optimization-patterns.md` 引用

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
