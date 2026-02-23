---
name: design
description: 架构设计。在隔离上下文中启动 pipeline-designer SubAgent。
context: fork
agent: pipeline-designer
---

# /design -- 架构设计

> 在隔离上下文中执行架构设计，输出架构设计文档和关键决策记录。

## 前置条件

`docs/pipeline/{feature}/handoff_clarify.md` 必须存在。如不存在，请先执行 `/clarify`。

## 执行流程

1. 读取 `docs/pipeline/{feature}/handoff_clarify.md`
2. 用 Glob/Grep 扫描现有代码，了解项目结构和编码模式
3. 基于扫描结果和需求文档执行架构设计
4. 关键决策列出 2-3 个备选方案并对比（方法论由 skills 引入的 pipeline-architecture 提供）
5. 输出到 `docs/pipeline/{feature}/handoff_design.md` + `Key_Decisions.md`

## Few-shot 示例

### 好的输出

```
输入分析：
- 扫描项目发现现有模型在 src/models/（SQLAlchemy，5 个模型文件）
- API 风格 RESTful，路由在 src/api/v1/（文件路由，12 个文件）
- 认证方式 JWT（src/auth/jwt.py）

决策：
- 路由方案选择文件路由（方案 A），因为与现有 12 个路由文件风格一致
- 校验方案选择 Pydantic BaseModel（方案 B），因为项目已有 3 个 Schema 使用此模式

产出：
- POST /api/v1/users
  入参：username(str, 3-20字符), email(str, RFC5322), password(str, >=8字符)
  成功：201 {"id": int, "username": str, "created_at": datetime}
  失败：422 {"error_code": "VALIDATION_ERROR", "details": [...]}
  失败：409 {"error_code": "USER_EXISTS"}

覆盖表：
| clarify 规则 | 对应接口 | 状态 |
|---|---|---|
| R1 用户名3-20字符 | POST /users username 校验 | 已覆盖 |
| R2 密码>=8字符 | POST /users password 校验 | 已覆盖 |
```

### 坏的输出

```
建议使用微服务架构。接口使用 RESTful 风格。用户表包含必要字段。
（没有扫描现有代码、没有方案对比、没有具体接口定义、没有错误场景、没有覆盖表）
```

## 自检清单

输出前必须逐条确认：

1. clarify 每条规则都有对应接口或数据模型？（列出覆盖表）
2. 每个接口都定义了错误场景和错误码？
3. 扫描了现有代码并保持风格一致？（Handoff 体现扫描结果）
4. 关键决策给出了 2+ 备选方案对比？
5. 是否引入了 clarify 未提及的功能？（如是则删除）
6. 假设已标注为"待确认"？
7. 是否为每个关键架构决策生成了 Key_Decisions.md 条目？
8. 模块边界是否明确了"负责什么"和"不负责什么"？

## 输出格式

Handoff 文档必须包含以下结构：

```markdown
# handoff_design.md

## 输入分析
[扫描现有代码的发现 + clarify 规则逐条理解]

## 决策
[关键技术选型及方案对比]

## 产出

### 模块划分
[模块列表，每个模块的"负责/不负责"]

### 接口清单
[每个接口的入参/出参/错误码]

### 数据模型
[模型定义和字段说明]

## 覆盖表
[clarify 规则 -> 设计产出 -> 覆盖状态]

## 交接项
- 接口清单（供 Planner 拆分任务）
- 模块依赖图
- 技术风险点
- 设计约束
```
