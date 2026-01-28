---
name: refactor-py
command: refactor-py
user_invocable: true
description: Python 代码重构。处理 Python/FastAPI 项目的过度设计：ABC 滥用、装饰器嵌套、过度类型化、模块拆分过细。输出重构计划交给 /run-plan 执行。
---

# Python 代码重构 (Refactor Python)

> **角色**：Python 代码质量守护者
> **目标**：让 Python 代码保持"恰到好处"的状态
> **原则**：简单、合适、演化
> **思考模式**：启用 ultrathink 深度思考，全面评估 Python 重构影响

---

## 依赖规范

本 Skill 依赖以下规范文件：

| 规范文件 | 覆盖内容 |
|---------|---------|
| `.claude/rules/代码质量.md` | 项目铁律（禁止 Mock 测试） |
| `.claude/rules/代码清洁.md` | 未使用代码检测（ruff、vulture） |
| `.claude/rules/文档规范.md` | 重构计划文档存放位置 |

> **职责分离**：本 Skill 定义重构**流程**，`rules/` 定义**代码标准**。

---

## Python 重构哲学

**"Python 的问题不是不够 Java，而是太想成为 Java"**

Python 开发者容易从 Java 带来坏习惯：
- ABC 抽象类（模仿 Java 接口）
- 过度类型注解（模仿 Java 静态类型）
- 过度 OOP（一切皆类）
- 过度分层（照搬 Spring 架构）

但也要注意：**必要的抽象是好的**，关键是判断"是否必要"。

---

## 重构方向判断

| 问题类型 | 特征 | 方向 |
|---------|------|------|
| **过度设计** | ABC 只有一个实现、装饰器嵌套过深 | 减法 |
| **设计不足** | 职责混乱、重复代码、难扩展 | 加法 |
| **设计不当** | 继承链混乱、模块边界不清 | 调整 |

---

## 减法：过度设计模式识别

### 🔴 P0 - 必须处理

| 模式 | 特征 | 重构方法 |
|------|------|---------|
| **空 ABC** | 抽象类只有一个实现 | 删除 ABC，保留实现 |
| **God Module** | 单文件 >500 行 | 按职责拆分 |
| **过度继承** | 继承链 >3 层 | 用组合替代继承 |
| **死代码** | 从未调用的函数/类 | 直接删除 |

### 🟡 P1 - 强烈建议处理

| 模式 | 特征 | 重构方法 |
|------|------|---------|
| **假协议类** | Protocol 只有一个实现 | 删除 Protocol |
| **过度 dataclass** | 简单 dict 就够用 | 用 TypedDict 或 dict |
| **装饰器嵌套** | 3 层以上装饰器 | 合并装饰器 |
| **元类滥用** | metaclass 只做简单事 | 用装饰器或 `__init_subclass__` |
| **过度依赖注入** | 模仿 Spring IoC | 直接导入 |

### 🟢 P2 - 建议处理

| 模式 | 特征 | 重构方法 |
|------|------|---------|
| **过度类型体操** | 泛型嵌套 3 层以上 | 简化类型或用 Any |
| **过度配置** | 配置类比业务代码还多 | 用 pydantic-settings |
| **过度抽象** | 一个函数只被调用一次 | 内联 |
| **过度模块化** | 每个类一个文件 | 合并相关类到一个模块 |

---

## 加法：设计不足模式识别

### 何时需要加抽象

| 场景 | 建议 |
|------|------|
| 有 **多个实现** 需要切换 | 保留/添加 Protocol 或 ABC |
| 有 **真实的扩展需求** | 保留/添加扩展点 |
| **重复代码** 出现 3 次以上 | 抽取公共函数/类 |
| **职责混乱**，一个模块做太多事 | 拆分职责 |
| 需要 **依赖注入** 做测试 | 保留适度的 DI |

### 示例：何时保留 Protocol

```python
# ✅ 保留 Protocol：有多个实现
from typing import Protocol

class StorageBackend(Protocol):
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...

class LocalStorage:
    def save(self, key: str, data: bytes) -> None:
        Path(key).write_bytes(data)

    def load(self, key: str) -> bytes:
        return Path(key).read_bytes()

class S3Storage:
    def save(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)

    def load(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

# 运行时根据配置切换
def get_storage() -> StorageBackend:
    if settings.STORAGE_TYPE == "s3":
        return S3Storage()
    return LocalStorage()
```

---

## 调整：设计不当模式识别

### 常见问题

| 问题 | 特征 | 重构方法 |
|------|------|---------|
| **循环导入** | A → B → A | 提取公共模块或延迟导入 |
| **继承链混乱** | 多重继承顺序问题 | 用组合替代，或明确 MRO |
| **模块边界不清** | 包之间互相导入 | 重新划分包边界 |
| **职责不清** | 不知道该放哪个模块 | 明确职责，重新分配 |

---

## 具体案例：删除空 ABC

### 识别空 ABC

```python
# 🔴 只有一个实现的 ABC
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    def get_user(self, user_id: int) -> User: ...

    @abstractmethod
    def save_user(self, user: User) -> None: ...

class UserRepository(IUserRepository):  # 唯一实现
    def get_user(self, user_id: int) -> User:
        return db.query(User).get(user_id)

    def save_user(self, user: User) -> None:
        db.add(user)
        db.commit()
```

### 删除 ABC

```python
# ✅ 直接用类
class UserRepository:
    def get_user(self, user_id: int) -> User:
        return db.query(User).get(user_id)

    def save_user(self, user: User) -> None:
        db.add(user)
        db.commit()
```

**删除条件**：
- ABC 只有一个实现
- 不需要 Mock 测试（用真实数据库测试）
- 不是插件系统的扩展点

---

## 具体案例：简化过度继承

### 识别过度继承

```python
# 🔴 继承链太长
class BaseEntity:
    id: int
    created_at: datetime

class AuditableEntity(BaseEntity):
    updated_at: datetime
    updated_by: str

class SoftDeletableEntity(AuditableEntity):
    deleted_at: datetime | None

class User(SoftDeletableEntity):  # 4 层继承！
    name: str
    email: str
```

### 用组合替代

```python
# ✅ 扁平结构
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
```

---

## 具体案例：合并装饰器

### 识别装饰器嵌套

```python
# 🔴 装饰器嵌套过深
@router.post("/users")
@authenticate
@authorize("admin")
@validate_request
@rate_limit(100)
@cache(ttl=60)
@log_request
@trace
async def create_user(request: UserCreate) -> User:
    ...
```

### 合并装饰器

```python
# ✅ 合并为一个装饰器
def api_endpoint(
    method: str,
    path: str,
    auth: bool = True,
    role: str | None = None,
    rate_limit: int = 100,
    cache_ttl: int = 0,
):
    def decorator(func):
        # 组合所有逻辑
        ...
    return decorator

@api_endpoint("POST", "/users", role="admin", cache_ttl=60)
async def create_user(request: UserCreate) -> User:
    ...
```

---

## 具体案例：简化过度依赖注入

### 识别过度 DI

```python
# 🔴 模仿 Spring IoC
class Container:
    _instances = {}

    @classmethod
    def register(cls, interface, implementation):
        cls._instances[interface] = implementation

    @classmethod
    def resolve(cls, interface):
        return cls._instances[interface]

# 注册
Container.register(IUserRepository, UserRepository())
Container.register(IUserService, UserService(Container.resolve(IUserRepository)))

# 使用
user_service = Container.resolve(IUserService)
```

### 简化为直接导入

```python
# ✅ Python 方式：直接导入
from app.repositories.user import UserRepository
from app.services.user import UserService

user_repo = UserRepository()
user_service = UserService(user_repo)

# 或更简单：模块级单例
# app/services/user.py
_repo = UserRepository()

def get_user(user_id: int) -> User:
    return _repo.get_user(user_id)
```

---

## FastAPI 特定规则

### 依赖注入控制

```python
# 🔴 过度使用 Depends
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    auth: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    ...

# ✅ 只 Depends 必要的
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # user_service 直接导入使用
    return user_service.get_user(db, user_id)
```

### Depends 数量控制

| 依赖数 | 状态 | 行动 |
|-------|------|------|
| 1-3 | ✅ 正常 | 无需处理 |
| 4-5 | ⚠️ 警告 | 考虑合并 |
| >5 | 🔴 严重 | 必须重构 |

### 路由组织

| 模式 | 文件数 | 重构后 |
|------|-------|--------|
| 每个端点一个文件 | 20+ | 按资源分组，5-10 文件 |
| 每个模型一个文件 | 15+ | 相关模型合并，5 文件 |

---

## 执行流程

### Phase 1: 代码诊断

```bash
# 统计代码行数
find . -name "*.py" -exec wc -l {} \; | sort -rn | head -20

# 统计类的方法数
grep -c "def " xxx_service.py

# 检查 ABC 使用
grep -r "ABC\|abstractmethod" --include="*.py"

# 检查装饰器嵌套
grep -B5 "^async def\|^def " xxx.py | grep "@"
```

### Phase 2: 识别问题类型

- [ ] 过度设计？（减法）
- [ ] 设计不足？（加法）
- [ ] 设计不当？（调整）

### Phase 3: 制定重构计划

输出到 `docs/开发文档/plan_重构_[模块名].md`

---

## 危险信号

| 信号 | 行动 |
|------|------|
| 重构后更难理解 | 停，方向可能错了 |
| 想引入 ABC 来"解耦" | 停，Python 用鸭子类型 |
| 想用 metaclass 来"优雅" | 停，通常有更简单的方法 |
| 想模仿 Java 分层 | 停，Python 不需要那么多层 |
| 想引入 IoC 容器 | 停，直接导入就行 |

---

## 常见误区

> **规范来源**：`.claude/rules/代码质量.md`（项目铁律三：禁止 Mock）

| 误区 | 正确理解 |
|------|---------|
| "ABC 方便 Mock 测试" | **铁律禁止 Mock**，用真实数据库测试 |
| "类型注解要完整" | `Any` 和简化类型也是合法选择 |
| "分层是最佳实践" | Python 的最佳实践是简单 |
| "dataclass 更规范" | dict 也很规范，看场景 |
| "代码越少越好" | 合适的代码量才是好的 |

---

## Python 之禅（重构版）

```
简单胜于复杂
扁平胜于嵌套
如果实现很难解释，那就是个坏主意
如果实现很容易解释，那可能是个好主意
```

---

## 完成检查清单

- [ ] 问题类型明确（过度设计/设计不足/设计不当）
- [ ] 重构方向明确（减法/加法/调整）
- [ ] 符合三原则（简单、合适、演化）
- [ ] 没有 >500 行的模块
- [ ] 没有只有一个实现的 ABC/Protocol
- [ ] 没有 3 层以上的装饰器嵌套
- [ ] 没有 3 层以上的继承链
- [ ] 重构计划已输出
