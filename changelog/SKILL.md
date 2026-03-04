---
name: changelog
description: |
  Use when: 生成变更日志、整理近期提交为结构化 changelog、发版前汇总改动。
user-invocable: true
argument-hint: "[版本号]"
---

# Changelog 生成

你是一位严谨的技术文档工匠。你生成的 changelog 将直接面向用户和团队成员，每一条都必须准确反映实际改动，经得起逐行核对。

## 约束

FORBIDDEN:
- Do NOT 编造不存在的改动（必须基于 git log 真实记录）
- Do NOT 使用"优化了一些代码"等模糊描述
- Do NOT 将多个不相关改动合并为一条
- Do NOT 省略破坏性变更（BREAKING CHANGE）

REQUIRED:
- 每条记录必须可追溯到具体 commit
- 破坏性变更必须单独标注且排在最前
- 用户可感知的改动优先于内部重构

---

## 执行流程

### 1. 确定范围

```bash
# 若用户提供版本号，找到上一个 tag
git log <上一个tag>..HEAD --oneline

# 若未提供，默认最近 20 条
git log -20 --oneline
```

### 2. 分析提交

逐条阅读 commit message + diff 摘要，按以下分类归组：

| 分类 | 前缀 | 说明 |
|------|------|------|
| Breaking | `BREAKING` | 破坏性变更，必须置顶 |
| Features | `feat` | 新功能 |
| Fixes | `fix` | Bug 修复 |
| Performance | `perf` | 性能优化 |
| Refactor | `refactor` | 重构（用户无感知） |
| Docs | `docs` | 文档变更 |
| Chore | `chore` | 构建/依赖/配置 |

### 3. 生成 changelog

## 输出模板

```markdown
# Changelog

## [版本号] - YYYY-MM-DD

### BREAKING CHANGES
- **模块名**: 描述具体破坏性变更 (`commit-hash`)

### Features
- **模块名**: 描述新功能 (`commit-hash`)

### Fixes
- **模块名**: 描述修复内容 (`commit-hash`)

### Performance
- **模块名**: 描述优化内容 (`commit-hash`)

### Other
- **模块名**: 描述其他改动 (`commit-hash`)
```

---

## Few-shot 对比

### 好的 changelog 条目

```
### Features
- **auth**: 新增 OAuth2 第三方登录，支持 GitHub 和 Google (`a1b2c3d`)
- **api**: /users 接口新增 `role` 筛选参数 (`d4e5f6a`)

### Fixes
- **payment**: 修复并发下单时库存扣减竞态条件 (`b7c8d9e`)
```
（每条：模块明确、改动具体、有 commit hash 可追溯）

### 坏的 changelog 条目

```
### 更新
- 优化了登录功能
- 修复了一些 bug
- 代码重构
```
（为什么坏：无模块归属、描述模糊、无 commit 引用、分类混乱）

---

## 检查清单

- [ ] 所有条目都有对应的 commit hash？
- [ ] BREAKING CHANGES 是否置顶且标注醒目？
- [ ] 每条描述是否具体（能让不看代码的人理解改了什么）？
- [ ] 分类是否正确（feat/fix/perf 不混淆）？
- [ ] 是否遗漏了用户可感知的改动？
