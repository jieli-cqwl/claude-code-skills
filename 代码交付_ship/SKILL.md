---
name: ship
command: ship
user_invocable: true
description: |
  代码交付。专注 commit / pull --rebase / push，冲突即停，不自动改冲突。
  Use when: 提交代码、推送远程、开发完成准备交付。
---

# 代码交付 (Ship)

> 目标：安全完成一次 Git 交付。
> 原则：最小流程、显式确认、冲突即停。

---

## 职责边界

`/ship` 只负责交付动作，不重复承担研发流程编排职责：

- 做：检查仓库状态、生成提交建议、提交、同步远程、推送
- 不做：替代 `/check` 或 `/qa` 执行质量验收
- 做：若检测到冲突，立即停止并交给人工处理
- 不做：自动修改冲突内容

---

## 执行流程

```
1. 交付前检查（仓库、分支、变更）
2. 质量状态提示（/check、/qa 仅做提示，不作为硬阻断）
3. 生成并确认提交信息 + 提交范围
4. 提交（commit）
5. 同步远程（pull --rebase）并推送（push）
```

---

## 步骤 1：交付前检查

```bash
git rev-parse --is-inside-work-tree || { echo "❌ 当前目录不是 Git 仓库"; exit 1; }
git status --short | grep -q . || { echo "ℹ️ 无变更需要提交"; exit 0; }
branch="$(git branch --show-current)"
```

分支规则：

- `main/master` 默认禁止直接交付，提示先切分支后重试
- 如用户明确要求在主分支交付，需二次确认后再执行

---

## 步骤 2：质量状态提示（非阻断）

检查以下文件是否存在、是否 PASS：

- `docs/pipeline/{feature}/handoff_check.md`
- `docs/pipeline/{feature}/handoff_qa.md`

处理策略：

- 两者均 PASS：继续
- 任一缺失或非 PASS：明确提示风险，要求用户确认是否继续交付

注意：`/ship` 不自动触发 `/check`、`/qa`，只做风险提示与确认。

---

## 步骤 3：提交信息与提交范围确认

先展示变更信息：

```bash
git fetch origin
git diff --stat
git status --short
git log --oneline -3
```

提交信息模板：

```text
<type>: <简短描述>

<详细说明>
```

`type` 约定：

- `feat`：新功能
- `fix`：缺陷修复
- `docs`：文档更新
- `refactor`：重构
- `chore`：杂项维护

交互要求：

- 展示建议提交信息，等待用户确认或改写
- 展示待提交文件，等待用户确认提交范围
- 未确认提交范围时，停止流程

---

## 步骤 4：提交 + 同步 + 推送

```bash
# 1) 暂存确认范围并提交
git add -- <pathspec...>
git diff --cached --name-only
git commit -m "<最终确认的提交信息>"

# 2) 同步远程（冲突即停）
branch="$(git branch --show-current)"
if git pull --rebase origin "$branch"; then
  echo "✅ 已完成远程同步"
else
  conflict_files="$(git diff --name-only --diff-filter=U)"
  if [ -n "$conflict_files" ]; then
    echo "⚠️ 检测到 rebase 冲突，流程已暂停"
    echo "$conflict_files"
    echo "请人工处理后执行：git add <resolved-files> && git rebase --continue"
    echo "放弃本次同步：git rebase --abort"
    exit 1
  fi
  echo "❌ 同步失败（非冲突原因），请检查网络或权限后重试"
  exit 1
fi

# 3) 推送
if git rev-parse --abbrev-ref @{upstream} >/dev/null 2>&1; then
  git push
else
  git push -u origin "$branch"
fi
```

---

## 边界处理

| 场景 | 处理 |
|---|---|
| 无变更 | 直接提示并结束 |
| 非 Git 仓库 | 直接失败并结束 |
| main/master 分支 | 默认阻断，需显式二次确认 |
| pull --rebase 冲突 | 列出冲突文件并暂停 |
| 非冲突类同步失败 | 明确失败原因，停止 |
| 无 upstream | 自动 `git push -u origin <branch>` |

---

## 完成输出模板

```text
✅ 代码交付完成

提交信息：<message>
分支：<branch>
远程：origin/<branch>
质量状态：/check=<PASS|FAIL|SKIP> /qa=<PASS|FAIL|SKIP>
```
