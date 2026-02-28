# Codex Skills Quick Start

## 推荐主流程（串行，最稳）

1. `$prd`
2. `$design`
3. `$plan`
4. `$run-plan`
5. `$check`
6. `$qa`
7. `$ship`

## 一键流程

- `$auto-dev`

## 并行与子 agent 规则

- 默认主线程执行，不自动启用子 agent。
- 需要并行时请明确说：`请并行执行，使用子 agent`，然后调用 `$run-plan-parallel` 或 `$auto-dev`。
- 不需要并行时请明确说：`请串行执行，不使用子 agent`。

## 依赖路径

- 参考规范：`~/.codex/reference/`
- 规则文件：`~/.codex/rules/RULES.md`
- 外部流水线脚本：`~/.codex/pipeline.sh`
