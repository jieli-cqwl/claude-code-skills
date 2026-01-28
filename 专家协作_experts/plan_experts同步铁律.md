# 计划：/experts 同步铁律规范

> **目标**：将最新的编码时铁律同步到 /experts 下的专家定义文件
> **创建日期**：2026-01-27

---

## 背景

最近对编码规范做了重大改进：
1. `implementer.md` 新增了 7 条「编码时铁律」
2. `/check` 的 Agent1 铁律检查项已同步
3. 但 `/experts` 下的专家定义文件滞后

---

## Tasks

- [x] Task 1: 更新 backend-architect.md
  - 在"禁止的模式"部分增加：HTTP 状态码检查、错误提示用户友好、函数设计约束

- [x] Task 2: 更新 frontend-architect.md
  - 在"禁止的模式"部分增加：fetch 响应检查、错误提示用户友好

- [x] Task 3: 更新 tech-lead.md
  - 增加对「编码时铁律」的引用
  - 确保专家输出符合铁律

- [x] Task 4: 更新 fullstack-feature.md
  - Phase 4 增加「实时代码检查」要求
  - Phase 5 增加「铁律检查」要求

---

## 验证标准

- [x] backend-architect.md 包含 HTTP 状态码检查规则
- [x] backend-architect.md 包含函数设计约束
- [x] frontend-architect.md 包含 fetch 响应检查规则
- [x] tech-lead.md 引用编码时铁律
- [x] fullstack-feature.md 包含实时检查和铁律检查
