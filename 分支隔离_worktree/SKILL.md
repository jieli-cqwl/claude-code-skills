---
name: worktree
command: worktree
user_invocable: true
description: Git Worktree 管理。为开发任务创建隔离的工作目录，避免影响主分支。支持并行开发多个功能。来源：obra/superpowers（经过实战验证）
---

# Using Git Worktrees

> **来源**: [obra/superpowers](https://github.com/obra/superpowers) - 经过实战验证的 Skills 集合

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**分支隔离**"或"**创建 worktree**"（主触发词）
- 使用命令：`/worktree`
- 说"隔离开发"、"新建工作目录"
- 说"不想影响主分支"
- 说"并行开发多个功能"

**适用场景**：
- 开发新功能不想影响主分支
- 需要同时开发多个功能
- 大型重构需要隔离环境

---

## 什么是 Worktree

Git worktree 允许你在同一个仓库创建多个工作目录，每个目录可以检出不同的分支。

**优势**：
- 开发新功能时不影响主分支
- 可以同时开发多个功能
- 切换功能不需要 stash/commit 半成品代码

---

## 工作流程

### 1. 选择目录

优先级顺序：
1. 已存在的 `.worktrees/` 目录
2. 已存在的 `worktrees/` 目录
3. CLAUDE.md 中指定的目录
4. 询问用户

### 2. 安全检查

确保目录被 `.gitignore` 忽略：

```bash
# 检查 .gitignore
grep -E "^\.?worktrees/?$" .gitignore

# 如果没有，添加
echo ".worktrees/" >> .gitignore
```

### 3. 创建 Worktree

```bash
# 创建新分支并检出到 worktree
git worktree add .worktrees/feature-xxx -b feature/xxx

# 基于特定分支创建
git worktree add .worktrees/feature-xxx -b feature/xxx origin/main
```

### 4. 设置环境

```bash
cd .worktrees/feature-xxx

# 根据项目类型安装依赖
npm install          # Node.js
pip install -r requirements.txt  # Python

# 运行测试确认环境正常
npm test
```

### 5. 验证

确认：
- [ ] Worktree 创建成功
- [ ] 依赖安装完成
- [ ] 测试可以运行
- [ ] 在正确的分支上

---

## 常用命令

```bash
# 列出所有 worktree
git worktree list

# 创建 worktree
git worktree add <path> -b <branch>

# 删除 worktree
git worktree remove <path>

# 清理不存在的 worktree 引用
git worktree prune
```

---

## 目录结构

```
project/
├── .git/
├── .gitignore          # 包含 .worktrees/
├── .worktrees/         # Worktree 目录（被忽略）
│   ├── feature-auth/
│   └── feature-payment/
├── src/
└── ...
```

---

## 完成开发后

开发完成后的处理流程：

### 合并到主分支

```bash
# 回到主工作目录
cd /path/to/project

# 合并功能分支
git merge feature/xxx

# 删除 worktree
git worktree remove .worktrees/feature-xxx

# 删除分支
git branch -d feature/xxx
```

### 创建 PR

```bash
# 在 worktree 中推送分支
cd .worktrees/feature-xxx
git push -u origin feature/xxx

# 使用 gh 创建 PR
gh pr create --title "feat: xxx" --body "..."
```

---

## 关键原则

> **"Fix broken things immediately"** - Jesse
>
> 如果发现 `.gitignore` 缺少 worktree 目录，立即添加，不要继续。

---

## 危险信号

| 信号 | 问题 |
|------|------|
| Worktree 目录不在 .gitignore | 可能会被提交到仓库 |
| 在主工作目录创建 worktree | 应该在子目录 |
| 多个 worktree 用同一个分支 | 会导致冲突 |

---

## ✅ 完成提示

当 Worktree 创建完成后，输出：

```
✅ 分支隔离环境已创建

下一步：在隔离分支中执行 /run-plan（执行计划）
```
