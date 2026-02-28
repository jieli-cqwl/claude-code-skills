---
name: ship
command: ship
user_invocable: true
description: |
  代码交付。一键提交并推送代码，默认安全同步策略（冲突即停并请求人工处理）。
  Use when: 提交代码、push、创建 PR、发起合并请求、开发完成准备交付。
---

# 代码交付 (Ship)

> **角色**：严谨的 Release Engineer，每次交付都像正式发版。
> **驱动**：用户信赖你的每次交付，失误会中断整个团队的协作节奏，你不允许这种事发生。
> **标准**：你的每次提交都会被资深 Tech Lead 逐行 Review，零事故交付率是你的底线。

> **目标**：一键提交并推送代码
> **特点**：默认安全同步（冲突即停），必要时需用户确认

---

## 执行流程

```
1. 前置检查：/check 与 /qa 是否 PASS（未执行或未通过需显式确认）
2. 分析代码变更 → 生成提交信息
3. 用户确认
4. 提交 → 同步远程（冲突即停）→ 推送
```

---

## 实现细节（AI 参考）

### 步骤 0: /check 与 /qa 前置验证

- 若 `docs/pipeline/{feature}/handoff_check.md` 与 `handoff_qa.md` 均存在且结果为 PASS：继续
- 若未执行或存在 FAIL：要求用户显式确认继续，并记录原因到交付输出摘要

### 步骤 1: 分析变更 + 生成提交信息

```bash
# 检查 git 状态
git rev-parse --is-inside-work-tree || { echo "❌ 当前目录不是代码仓库"; exit 1; }
git status --short | grep -q . || { echo "ℹ️ 没有需要提交的代码"; exit 0; }

# 获取当前分支
branch=$(git branch --show-current)

# 检查远程更新
git fetch origin 2>&1

# 分析变更
git diff --stat
git status --short
git log --oneline -3
```

**生成提交信息**：

基于变更内容生成，格式：
```
<type>: <简短描述>

<详细说明>

Co-Authored-By: <从 git config 读取>
```

**Type 类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `refactor`: 重构
- `chore`: 其他

**动态获取作者**：
```bash
git_user_name=$(git config user.name 2>/dev/null || echo "Claude Sonnet 4.5")
git_user_email=$(git config user.email 2>/dev/null || echo "noreply@anthropic.com")
```

**展示给用户**：
```markdown
我分析了你的代码变更，建议提交信息：

---
<生成的提交信息>
---

确认提交？(y/n)
```

### 步骤 2: 用户确认

- 输入 `y` 或 `确认`：继续
- 输入 `n` 或 `取消`：停止
- 输入其他内容：作为新的提交信息

### 步骤 3: 提交 + 安全同步 + 推送

```bash
# 1. 暂存并提交
git add -A
git commit -m "<用户确认的提交信息>"

# 2. 同步远程（安全策略：冲突即停）
branch=$(git branch --show-current)

# 尝试 pull --rebase
if git pull --rebase origin "$branch" 2>&1; then
    echo "✅ 已同步远程代码"
else
    # 检测是否为冲突
    conflict_files=$(git diff --name-only --diff-filter=U || true)
    if [ -n "$conflict_files" ]; then
        echo "❌ 检测到 rebase 冲突，已停止自动流程"
        echo ""
        echo "冲突文件："
        echo "$conflict_files"
        echo ""
        echo "请先手工解决冲突后再继续交付"
        echo "回退命令：git rebase --abort && git reset --soft HEAD~1"
    else
        echo "❌ 同步失败（非冲突原因），已停止自动流程"
        echo "请检查网络/权限后重试"
        git rebase --abort 2>/dev/null || true
    fi
    exit 1
fi

# 3. 推送到远程
if git rev-parse --abbrev-ref @{upstream} >/dev/null 2>&1; then
    git push
else
    git push -u origin "$branch"
fi
```

**冲突处理策略**（安全优先）：

遇到 rebase 冲突时，必须执行以下步骤：

1. 检测冲突并列出冲突文件（`git diff --name-only --diff-filter=U`）
2. 立即停止自动交付流程，不做自动合并
3. 明确告知用户需要人工处理冲突
4. 提供回退命令：`git rebase --abort && git reset --soft HEAD~1`
5. 人工处理完成后，再重新执行 `/ship`

**错误处理（白话文）**：

| 技术错误 | 白话文翻译 |
|---------|-----------|
| `fatal: unable to access` | ❌ 推送失败：网络连接问题<br>建议：检查网络后重试 |
| `Permission denied` | ❌ 推送失败：没有权限<br>建议：检查仓库访问权限 |
| `rejected` | ❌ 推送失败：远程有新代码<br>建议：重新运行 /ship |
| `not a git repository` | ❌ 当前目录不是代码仓库 |

---

## 边界情况

| 情况 | 处理 |
|------|------|
| 无代码变更 | 提示"没有需要提交的代码" |
| 不是 git 仓库 | 提示"当前目录不是代码仓库" |
| 在 main/master 分支 | 警告"你在主分支上提交，确认吗？" |
| 无远程跟踪分支 | 自动推送到 origin/当前分支名 |
| 同步出现冲突 | 立即停止，列出冲突文件并请求人工处理 |
| git config 未配置 | 使用默认值 "Claude Sonnet 4.5" |

---

## 完整示例

**正常流程**：
```
用户：/ship

Claude：我分析了你的代码变更，建议提交信息：

---
feat: 添加用户登录功能

- 实现登录 API
- 添加登录页面

Co-Authored-By: 李杰 <lijie@example.com>
---

确认提交？(y/n)

用户：y

Claude：
✅ 代码已提交
✅ 已同步远程代码
✅ 推送成功

📋 提交信息：feat: 添加用户登录功能
🔗 远程分支：origin/feature/user-auth

🎉 代码交付完成！
```

**冲突即停（安全模式）**：
```
用户：/ship

Claude：[... 确认提交信息 ...]

用户：y

Claude：
✅ 代码已提交
❌ 检测到 rebase 冲突，已停止自动流程

冲突文件：
- src/app.py
- src/utils.py

请先手工解决冲突后再继续交付
回退命令：git rebase --abort && git reset --soft HEAD~1

⛔ 本次交付已暂停，等待人工处理
```

---

## ✅ 完成提示

```
✅ 代码交付完成

📋 提交信息：<简短描述>
🔗 远程分支：origin/<branch>
🧾 前置检查：/check=<PASS|FAIL|SKIP> /qa=<PASS|FAIL|SKIP>
📝 显式确认原因：<如有>

🎉 完成！
```
