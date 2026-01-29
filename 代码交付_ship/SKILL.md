---
name: ship
command: ship
user_invocable: true
description: 代码交付。开发完成并通过检查后使用，自动完成 git add、commit（自动生成消息供确认）、push 和可选的 PR 创建。在 /check 或 /qa 之后使用。
---

# 代码交付 (Ship)

> **角色**：交付助手
> **目标**：一键完成代码提交、推送和 PR 创建
> **原则**：自动化但不失控制，关键步骤需用户确认

---

## 核心原则

**"交付是开发的最后一公里，自动化但保留控制权"**

所有变更在推送前必须经过用户确认，避免意外提交敏感信息或错误代码。

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**提交代码**"或"**代码交付**"（主触发词）
- 使用命令：`/ship`
- 说"发布"、"推上去"
- 说"搞定了提交吧"
- 说"commit 一下"、"push 一下"

**何时使用**：

| 场景 | 使用 |
|------|------|
| `/check` 或 `/qa` 通过后 | ✅ 必须 |
| 功能开发完成，准备提交 | ✅ 推荐 |
| 修复 bug 后提交 | ✅ 推荐 |
| 代码还在开发中 | ❌ 不适用 |
| 测试未通过 | ❌ 不适用 |

---

## 执行流程

```
步骤 1: 状态检查
    ↓
步骤 2: 分析变更
    ↓
步骤 3: 生成 Commit Message（用户确认）
    ↓
步骤 4: 提交代码
    ↓
步骤 5: 推送远程
    ↓
步骤 6: 创建 PR（可选）
```

### 步骤 1: 状态检查

检查当前 git 状态，确保可以提交：

```bash
# 检查是否在 git 仓库中
git rev-parse --is-inside-work-tree

# 查看当前分支
git branch --show-current

# 查看工作区状态
git status

# 查看是否有远程仓库
git remote -v
```

**检查项**：
- [ ] 当前在 git 仓库中
- [ ] 有未提交的变更
- [ ] 远程仓库已配置

如果没有变更，提示用户并结束。

### 步骤 2: 分析变更

收集变更信息用于生成 commit message：

```bash
# 查看未暂存的变更
git diff

# 查看已暂存的变更
git diff --cached

# 查看变更的文件列表
git status --short

# 查看最近的 commit 风格（用于参考）
git log --oneline -5
```

### 步骤 3: 生成 Commit Message

基于变更内容自动生成 commit message，**必须让用户确认或修改**。

**Commit Message 格式**：

```
<type>: <简短描述>

<详细说明（可选）>

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type 类型**：
| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖 |

**示例输出**：

```markdown
根据变更内容，建议的 commit message：

---
feat: 添加用户登录功能

- 实现登录 API 接口
- 添加 JWT token 生成
- 前端登录表单组件

Co-Authored-By: Claude <noreply@anthropic.com>
---

请确认或修改后回复：
1. 确认提交
2. 取消
（或直接输入新内容修改后提交）
```

**必须等待用户确认后才能继续！**

### 步骤 4: 提交代码

用户确认后执行提交：

```bash
# 暂存所有变更
git add -A

# 提交（使用 HEREDOC 确保格式正确）
git commit -m "$(cat <<'EOF'
<用户确认的 commit message>
EOF
)"
```

### 步骤 5: 推送远程

```bash
# 获取当前分支名
branch=$(git branch --show-current)

# 检查是否有上游分支
git rev-parse --abbrev-ref @{upstream} 2>/dev/null

# 如果没有上游分支，设置并推送
git push -u origin "$branch"

# 如果有上游分支，直接推送
git push
```

**推送前确认**：
- 当前分支：`<branch_name>`
- 远程仓库：`origin`
- 是否继续推送？

### 步骤 6: 创建 PR（可选）

推送成功后，询问用户是否创建 PR：

```markdown
代码已推送到远程仓库。

是否创建 Pull Request？
1. 是，创建 PR
2. 否，稍后手动创建
```

如果用户选择创建 PR：

```bash
# 使用 gh 创建 PR
gh pr create --title "<commit 的简短描述>" --body "$(cat <<'EOF'
## Summary
<基于 commit message 生成的摘要>

## Test plan
- [ ] 单元测试通过
- [ ] 功能测试通过

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## 危险信号

| 信号 | 处理 |
|------|------|
| 有 `.env` 或敏感文件在变更中 | 立即警告，建议添加到 `.gitignore` |
| 变更文件超过 50 个 | 提醒用户确认是否正确 |
| 在 `main`/`master` 分支直接提交 | 警告，建议使用功能分支 |
| 未配置远程仓库 | 提示配置后再执行 |
| `git push --force` | 禁止，除非用户明确要求 |

---

## 敏感文件检测

提交前自动检测以下文件类型：

```
.env*
*.pem
*.key
*credentials*
*secret*
config/local.*
```

如果检测到，输出警告：

```markdown
⚠️ 检测到可能的敏感文件：

- .env.local
- config/credentials.json

这些文件包含敏感信息，不应提交到仓库。

建议操作：
1. 添加到 .gitignore
2. 从暂存区移除：git reset <file>

是否继续？
1. 继续（强制提交）
2. 取消
```

---

## 常见借口（都是错的）

| 借口 | 现实 |
|------|------|
| "我确定没有敏感信息" | 自动检测比人工可靠 |
| "这是私有仓库不要紧" | 私有仓库也可能泄露 |
| "先提交再说" | 提交后再删除，历史中仍然存在 |

---

## 与其他 Skills 的关系

```
/run-plan（执行计划）
    ↓
/check（开发检查）
    ↓
/qa（测试验收）
    ↓
/ship（代码交付）← 本技能
    ↓
完成
```

---

## 完整示例

```
用户：/ship

Claude：让我检查当前的 git 状态...

📊 当前状态：
- 分支：feature/user-auth
- 变更文件：8 个
- 新增：3 个
- 修改：5 个

📝 变更内容分析：
- backend/app/api/auth.py（新增）
- backend/app/services/auth_service.py（新增）
- frontend/src/pages/Login.tsx（新增）
- backend/app/models/user.py（修改）
- ...

---
建议的 commit message：

feat: 实现用户认证功能

- 添加登录/注册 API
- 实现 JWT token 认证
- 前端登录页面

Co-Authored-By: Claude <noreply@anthropic.com>
---

请确认或修改：
1. 确认提交
2. 取消
（或直接输入新内容修改后提交）

用户：1

Claude：✅ 代码已提交

正在推送到远程仓库...
- 分支：feature/user-auth
- 远程：origin

✅ 推送成功

是否创建 Pull Request？
1. 是
2. 否

用户：是

Claude：正在创建 PR...

✅ PR 已创建：https://github.com/xxx/xxx/pull/123

🎉 代码交付完成！
```

---

## 完成检查清单

- [ ] 当前在 git 仓库中
- [ ] 有变更需要提交
- [ ] 无敏感文件（或已确认）
- [ ] Commit message 已用户确认
- [ ] 代码已提交
- [ ] 已推送到远程
- [ ] PR 已创建（如需要）

---

## ✅ 完成提示

当代码交付完成后，输出：

```
✅ 代码交付完成

📋 提交信息：<commit message 简短描述>
🔗 远程分支：origin/<branch>
🔗 PR 地址：<pr_url>（如已创建）

🎉 本次开发任务完成！
```
