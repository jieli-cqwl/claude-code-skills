# Agent 任务分派模板

> Tech Lead 向专家 Agent 分派任务时使用的标准格式
> 确保任务描述清晰、边界明确、依赖可追踪

---

## 任务分派格式

```markdown
# 专家任务分派

## 基本信息
- **任务 ID**: [ORCH-001]
- **目标专家**: [backend-architect | frontend-architect | security-auditor | code-reviewer]
- **优先级**: [P0 紧急 | P1 高 | P2 中 | P3 低]
- **预计时长**: [估计完成时间]

## 任务背景

### 整体目标
[描述整个编排任务的最终目标，让专家理解全局]

### 当前阶段
[描述当前处于编排流程的哪个阶段]

## 任务描述

### 目标
[清晰描述这个专家需要完成的具体目标]

### 预期输出
[列出专家应该产出的具体交付物]
- [ ] 交付物 1
- [ ] 交付物 2

### 约束条件
[列出必须遵守的约束]
- 约束 1
- 约束 2

## 依赖信息

### 前置任务
| 任务 ID | 专家 | 状态 | 输出 |
|---------|------|------|------|
| ORCH-000 | tech-lead | ✅ 完成 | 任务分解方案 |

### 依赖的输出
[粘贴前置任务的相关输出，专家需要基于这些信息工作]

```
[前置任务的输出内容]
```

### 后续任务
[说明当前任务的输出将被谁使用]
- ORCH-002 (frontend-architect) 将使用本任务定义的 API 接口

## 参考资料

### 项目规范
- `.claude/rules/[相关规范].md`

### 相关文件
- `backend/app/xxx/xxx.py` - [说明]

## 输出格式要求

请按以下格式输出结果：

```markdown
# [专家角色] 任务报告

## 任务信息
- **任务 ID**: ORCH-001
- **完成时间**: YYYY-MM-DD HH:mm

## 分析/设计结果
[具体内容]

## 交付物清单
- [x] 交付物 1
- [x] 交付物 2

## 后续建议
[如果发现了需要其他专家关注的问题]

## 风险和关注点
[需要 Tech Lead 关注的风险]
```
```

---

## 各专家任务分派示例

### 示例 1：分派给 backend-architect

```markdown
# 专家任务分派

## 基本信息
- **任务 ID**: ORCH-001
- **目标专家**: backend-architect
- **优先级**: P1 高
- **预计时长**: 30 分钟

## 任务背景

### 整体目标
实现用户认证系统，支持登录、注册、Token 刷新功能。

### 当前阶段
阶段 1：API 和数据模型设计

## 任务描述

### 目标
设计用户认证相关的 REST API 和数据库模型。

### 预期输出
- [ ] API 接口设计文档（端点、请求、响应格式）
- [ ] 数据库表结构设计（DDL）
- [ ] 错误码定义
- [ ] 缓存策略说明

### 约束条件
- 遵循 RESTful 规范
- 使用 JWT 进行认证
- Token 有效期 2 小时，刷新 Token 有效期 7 天
- 密码使用 BCrypt 加密

## 依赖信息

### 前置任务
| 任务 ID | 专家 | 状态 | 输出 |
|---------|------|------|------|
| ORCH-000 | tech-lead | ✅ 完成 | 任务分解方案 |

### 后续任务
- ORCH-002 (frontend-architect) 将使用本任务定义的 API 接口
- ORCH-003 (security-auditor) 将审查本任务的安全设计

## 参考资料

### 项目规范
- `.claude/rules/全栈开发.md` - API 设计规范、错误码规范
- `.claude/rules/性能效率.md` - 缓存策略

## 输出格式要求

请输出：
1. API 设计（Markdown 表格）
2. 数据库 DDL
3. 错误码列表
4. 缓存 Key 设计
```

---

### 示例 2：分派给 security-auditor

```markdown
# 专家任务分派

## 基本信息
- **任务 ID**: ORCH-003
- **目标专家**: security-auditor
- **优先级**: P1 高
- **预计时长**: 20 分钟

## 任务背景

### 整体目标
实现用户认证系统，支持登录、注册、Token 刷新功能。

### 当前阶段
阶段 2：安全审查

## 任务描述

### 目标
审查用户认证系统的安全设计，识别潜在风险。

### 预期输出
- [ ] OWASP Top 10 检查报告
- [ ] 认证流程安全评估
- [ ] 安全加固建议

### 约束条件
- 必须覆盖 OWASP Top 10
- 关注认证绕过、会话劫持、密码安全

## 依赖信息

### 前置任务
| 任务 ID | 专家 | 状态 | 输出 |
|---------|------|------|------|
| ORCH-001 | backend-architect | ✅ 完成 | API 设计 |

### 依赖的输出

```markdown
## API 设计（来自 backend-architect）

| 端点 | 方法 | 描述 |
|------|------|------|
| /api/v1/auth/login | POST | 用户登录 |
| /api/v1/auth/register | POST | 用户注册 |
| /api/v1/auth/refresh | POST | 刷新 Token |

## 认证流程
1. 用户提交用户名和密码
2. 后端验证密码（BCrypt）
3. 生成 JWT Token（有效期 2h）
4. 返回 Token
```

## 参考资料

### 项目规范
- `.claude/rules/代码质量.md` - 安全相关规范
```

---

## 协作模式

### 串行协作

```
Tech Lead 分派任务 A 给 backend-architect
       ↓
backend-architect 完成任务 A，输出 API 设计
       ↓
Tech Lead 将 API 设计传递给 frontend-architect（任务 B）
       ↓
frontend-architect 完成任务 B，输出组件设计
       ↓
Tech Lead 整合所有输出
```

### 并行协作

```
                    ┌─ backend-architect (任务 A)
Tech Lead 分派 ────┤
                    └─ frontend-architect (任务 B，不依赖 A)
       ↓
Tech Lead 等待所有任务完成
       ↓
Tech Lead 整合并检查一致性
```

### 迭代协作

```
Tech Lead 分派任务 A 给 backend-architect
       ↓
backend-architect 完成初稿
       ↓
Tech Lead 分派审查给 security-auditor
       ↓
security-auditor 发现问题
       ↓
Tech Lead 分派修复任务给 backend-architect
       ↓
循环直到通过审查
```

---

## 冲突处理

当多个专家的输出存在冲突时：

1. **识别冲突**
   - Tech Lead 对比各专家输出
   - 标记不一致的地方

2. **冲突分派格式**

```markdown
# 冲突解决请求

## 冲突描述
backend-architect 和 frontend-architect 对 API 响应格式有不同意见。

## 各方意见

### backend-architect 意见
```json
{ "code": 0, "data": {...} }
```
理由：与现有 API 保持一致

### frontend-architect 意见
```json
{ "success": true, "result": {...} }
```
理由：更符合前端处理习惯

## 请求
请 tech-lead 根据项目规范做出最终决定。
```

3. **Tech Lead 裁决**
   - 参考项目规范
   - 考虑长期维护性
   - 发布最终决定
