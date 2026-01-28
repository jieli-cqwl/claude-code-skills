# 任务交接模板

> 用于向 implementer 子代理传递任务时使用

---

## 任务交接文档

### 基本信息

| 项目 | 内容 |
|------|------|
| **任务编号** | Task N |
| **任务名称** | [名称] |
| **计划文档** | `docs/开发文档/plan_xxx.md` |
| **交接时间** | YYYY-MM-DD HH:mm |

---

## 任务描述

### Task: [任务名称]

**目标**:
[一句话描述任务目标]

**文件操作**:
```
Create: backend/app/api/v1/new_file.py
Modify: backend/app/services/existing_service.py:123-145
Delete: backend/app/utils/obsolete_util.py
Test:   backend/tests/test_new_file.py
```

**详细步骤**:

1. **步骤 1**: [步骤描述]
   ```python
   # 代码示例
   ```

2. **步骤 2**: [步骤描述]
   ```python
   # 代码示例
   ```

3. **步骤 3**: [步骤描述]
   ```python
   # 代码示例
   ```

**验证标准**:
- [ ] [验证条件 1]
- [ ] [验证条件 2]
- [ ] [验证条件 3]

---

## 项目背景

### 技术栈
- **后端**: Python 3.10+ + FastAPI + SQLAlchemy 2.0+
- **前端**: React 18 + TypeScript + Ant Design 5
- **数据库**: MySQL 8.0 + Qdrant（向量库）
- **构建**: pip / poetry / Vite

### 项目规范
必须遵循 `.claude/rules/` 目录下的规范：
- `代码质量.md` - Fail Fast 原则、零容忍行为
- `全栈开发.md` - API 设计、错误码规范
- `性能效率.md` - 缓存、批量、并发

### 代码风格
```python
# 必须使用
from typing import Optional, List  # 类型提示
from pydantic import BaseModel     # 数据模型
import logging                     # 日志

logger = logging.getLogger(__name__)

# 必须避免
print()                  # 使用 logger.xxx
except:                  # 必须指定异常类型
except Exception as e:
    pass                 # 禁止吞掉异常
```

### 测试要求
- TDD 原则：先写测试，后写实现
- 覆盖率：>= 80%
- 命名：should_xxx_when_yyy
- 模式：Given-When-Then

---

## 相关文件

### 需要参考的文件

| 文件路径 | 说明 |
|---------|------|
| `backend/app/services/yyy_service.py` | 相关服务类 |
| `backend/app/crud/zzz.py` | 相关 CRUD |
| `backend/tests/test_yyy_service.py` | 参考测试写法 |

### 依赖的接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `user_service` | `get_by_id(id: int)` | 获取用户信息 |
| `order_crud` | `get_by_user_id(user_id: int)` | 查询用户订单 |

---

## 注意事项

1. **不要读取计划文件**：本文档已包含所有必要信息
2. **有问题立即提问**：不要假设，不要猜测
3. **遵循 TDD**：先写测试，看它失败，再实现
4. **完成自审**：实现后执行自审检查表
5. **提交完成报告**：使用标准格式报告完成情况

---

## 完成标准

当以下条件都满足时，任务视为完成：

- [ ] 所有验证条件都通过
- [ ] 测试全部通过
- [ ] 覆盖率达标
- [ ] 自审检查表全部通过
- [ ] 完成报告已提交

---

**请开始执行任务。如有问题，请先提问。**
