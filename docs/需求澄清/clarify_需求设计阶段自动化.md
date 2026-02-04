## 需求澄清结果

**需求名称**：需求设计阶段自动化（req-loop + design-loop）
**澄清日期**：2026-02-04
**状态**：已确认
**复杂度**：中等
**涉及范围**：Skills 开发

---

### 1. 背景

继 `/dev-loop` 完成开发阶段自动化后，继续完善前置阶段的自动化：
- **需求阶段**：clarify → gemini-critique → 提示用户补充
- **设计阶段**：explore → design → critique → gemini-critique → 自动修复循环

---

### 2. 目标

| Skill | 流程 | 输入 | 输出 |
|-------|------|------|------|
| `/req-loop` | clarify → gemini-critique | 用户需求 | AC 文档（经评审） |
| `/design-loop` | explore → design → critique → gemini-critique | AC 文档 | 设计文档（经评审） |

---

### 3. 验收标准

**AC 指纹**：`AC-HASH-9D4E3F2B`

#### 3.1 /req-loop

| AC-ID | Given | When | Then | 优先级 |
|-------|-------|------|------|--------|
| RL-1 | 用户提供需求 | 执行 `/req-loop` | 启动 clarify 与用户交互 | P0 |
| RL-2 | clarify 完成 | AC 文档生成 | 自动调用 gemini-critique 评审 | P0 |
| RL-3 | 评审通过 | 无严重问题 | 输出"需求阶段完成" | P0 |
| RL-4 | 评审发现问题 | 有改进建议 | 显示评审意见，提示用户补充 | P0 |
| RL-5 | gemini 不可用 | 降级 | 跳过评审，输出警告 | P2 |

#### 3.2 /design-loop

| AC-ID | Given | When | Then | 优先级 |
|-------|-------|------|------|--------|
| DL-1 | AC 文档存在 | 执行 `/design-loop` | 依次执行 explore → design | P0 |
| DL-2 | design 完成 | 自动触发 | 调用 critique 自评审 | P0 |
| DL-3 | critique 通过 | 自动触发 | 调用 gemini-critique 外部评审 | P0 |
| DL-4 | 双重评审通过 | 无严重问题 | 输出"设计阶段完成" | P0 |
| DL-5 | critique 发现问题 | 评审失败 | 自动修复，重新 critique | P0 |
| DL-6 | gemini-critique 发现问题 | 评审失败 | 自动修复，重新 critique → gemini-critique | P0 |
| DL-7 | 修复后通过 | 评审通过 | 输出成功报告（含重试次数） | P0 |
| DL-8 | 达到最大重试（2 次） | 仍失败 | 停止，输出失败报告，提示人工介入 | P0 |
| DL-9 | AC 文档不存在 | 门控失败 | 提示先执行 /clarify 或 /req-loop | P1 |
| DL-10 | gemini 不可用 | 降级 | 跳过外部评审，仅 critique | P2 |
| DL-11 | 用户中断 | 中断 | 保存检查点，可恢复 | P2 |

---

### 4. 技术约束

- 复用：clarify、explore、design、critique、gemini-critique
- 最大重试：design-loop 2 次
- 检查点：design-loop 支持中断恢复
- 降级：gemini 不可用时跳过外部评审

---

### 5. 下一步

1. 创建 `/req-loop` SKILL.md
2. 创建 `/design-loop` SKILL.md
3. 更新 STANDARD.md
