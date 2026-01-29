---
name: check
command: check
user_invocable: true
description: 开发检查。开发完成后的一站式自检，使用多 Agent 并行执行，大幅提升检查效率。包含苏格拉底反问、项目铁律检查、TDD 流程验证、规范匹配、代码审查、自动化验证、服务启动验证、需求覆盖检查、Hooks 配置检测。在执行计划（/run-plan）之后、测试验收（/qa）之前使用。
---

# 开发检查 (Check) - 并行版

> **角色**：开发者完成代码后的一站式自检
> **架构**：多 Agent 并行执行，提效 50-70%
> **核心理念**：如果你没有看到它有效，它就还没有有效
> **下一步**：检查通过后进入测试验收 (`/qa`)

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**检查一下**"或"**开发检查**"（主触发词）
- 使用命令：`/check`
- 说"自检"、"代码有问题吗"
- 说"看看有没有遗漏"
- 说"检查完成了吗"

**适用场景**：
- 开发完成后，提交前检查
- 不确定代码是否符合规范
- 需要全面审查变更

---

## 文档契约（铁律）

> **原则**：没有输入文档 → 不能执行；没有输出文档 → 不算完成

### 输入文档（门控检查）

| 文档 | 路径 | 必须 | 检查命令 |
|------|------|------|---------|
| **计划文档** | `docs/开发文档/plan_[功能名].md` | ✅ 必须 | `ls docs/开发文档/plan_*.md` |

**门控规则**：
```bash
# 门控检查：计划文档必须存在（Agent7 需求覆盖检查依赖）
PLAN_DOC=$(ls docs/开发文档/plan_*.md 2>/dev/null | head -1)
if [ -z "$PLAN_DOC" ]; then
  echo "❌ 门控失败: 计划文档不存在"
  echo "   修复: 先执行 /plan 生成计划文档"
  exit 1
fi
echo "✅ 计划文档: $PLAN_DOC"
```

**门控失败处理**：
- 计划文档不存在 → **停止执行**，先执行 `/plan`

### 输出文档

| 文档 | 路径 | 用途 |
|------|------|------|
| 检查报告 | 终端输出 | /qa 执行前的质量关卡 |

**下游依赖**：
- `/qa` 依赖检查通过

---

## 参考规范

| 规范 | 路径 | 用途 |
|------|------|------|
| **完成前验证** | `~/.claude/reference/完成前验证.md` | Agent6 服务启动验证的详细标准 |
| **测试 Hooks 配置** | `~/.claude/reference/测试Hooks配置.md` | Hooks 配置检测标准 |
| **TDD 规范** | `~/.claude/reference/TDD规范.md` | TDD 流程验证标准 |

---

## 并行架构

```
Phase 0: 自我审问（必须先完成）
    ↓
Phase 1: 变更范围检查（快速，作为后续输入）
    ↓
Phase 2: 并行检查（9 个 Agent 同时执行）
    ┌─────────────────────────────────────────────────┐
    │  Agent1: 铁律检查      Agent2: 后端自动化       │
    │  (grep 降级/硬编码)    (ruff + mypy + pytest)   │
    │                                                 │
    │  Agent3: 前端自动化    Agent4: 代码质量审查     │
    │  (lint + type-check)   (逐文件审查)             │
    │                                                 │
    │  Agent5: 文档同步检查  Agent6: 服务启动验证     │
    │  (代码变更→文档同步)   (启动服务→健康检查)      │
    │                                                 │
    │  Agent7: 需求覆盖检查  Agent8: TDD 流程验证     │
    │  (计划文档→代码对照)   (测试先于实现)           │
    │                                                 │
    │  Agent9: Hooks 配置检测 ← 新增                  │
    │  (检测测试自动化配置)                           │
    └─────────────────────────────────────────────────┘
    ↓
Phase 3: 汇总报告
```

**预估耗时**：原 5 分钟 → 现 2-3 分钟

---

## 紧急模式

> 修复紧急 bug 时，可跳过 TDD 检查，但必须事后补测试

**触发方式**：用户明确说明"紧急修复"或"hotfix"

**行为**：
- Agent8 TDD 验证改为警告而非阻塞
- 在报告中标记"需补测试"
- 下次 `/check` 时验证测试是否已补充

---

## 依赖规范

> **执行前按需读取**：以下规范文件在执行检查时按需加载。

| 规范文件 | 覆盖检查项 |
|---------|-----------|
| `~/.claude/reference/代码质量.md` | 项目铁律、安全性、代码质量 |
| `~/.claude/reference/代码清洁.md` | 未使用代码检测 |
| `~/.claude/reference/代码复用.md` | 新增代码复用检查 |
| `~/.claude/reference/硬编码治理规范.md` | 硬编码检测 |
| `~/.claude/reference/性能效率.md` | 性能检查 |
| `~/.claude/reference/全栈开发.md` | 前后端同步 |
| `~/.claude/reference/文档规范.md` | PR 描述、决策记录 |
| `~/.claude/reference/测试Hooks配置.md` | Hooks 配置检测 |

**执行 /check 时，自动读取上述规范文件。**

---

## 执行流程

### Phase 0: 自我审问（串行，必须先完成）

**快速回答以下问题**：

```markdown
## 自我审问

1. 所有相关代码都读过了吗？→ [是/否]
2. 前后端都完成了吗（如适用）？→ [是/否/不适用]
3. 有假设但未验证的部分吗？→ [是/否]
4. 实现符合计划文档吗？→ [是/否/无计划文档]
5. 新增代码是否搜索过复用？→ [是/否/无新增代码]
```

**任何"否"必须先解决再继续。**

---

### Phase 1: 变更范围检查（串行，快速）

```bash
# 快速获取变更范围
git status --short
git diff --stat HEAD~1
```

**输出**：变更文件列表，分类为前端/后端/配置/文档。

---

### Phase 2: 并行检查（核心优化）

**使用 Task 工具同时启动 7 个 Agent**：

```markdown
同时启动以下 7 个检查任务（使用 Task 工具，subagent_type="Explore"）：

1. **Agent1: 铁律检查**（与 implementer.md 的 7 条铁律对应）
   - **HTTP 状态码检查**：
     - Python: 检查 `requests.get/post` 后是否有 `raise_for_status()`
     - TS/JS: 检查 `fetch` 后是否有 `if (!res.ok)` 或类似检查
   - **降级逻辑检查**：
     - Java: `orElse(null)`, `orElseGet(() -> null)`, `catch.*return null`
     - Python: `except:.*pass`, `or None`, `if.*else None`
     - TS/JS: `catch.*return null`, `|| null`, `?? null`
   - **硬编码检查**：
     - URL: `http://localhost`, `127.0.0.1`, `://.*:\d{4,5}`
     - 密钥: `api_key.*=`, `secret.*=`, `password.*=`, `token.*=`
     - 配置: `timeout.*=.*\d+`, `retry.*=.*\d+`
   - **常量分层检查**（详见 `~/.claude/reference/硬编码治理规范.md`）：
     - 跨模块导入模块级常量（禁止 `from src.{module_a}.constants import` 在其他模块使用）
     - 模块常量缺少前缀（模块常量必须带模块前缀如 `QFT_`）
     - 常量膨胀预警（constants.py 超过 200 行需拆分）
   - **类型注解检查**：
     - Python: 函数参数和返回值是否有类型注解
     - TS: 是否使用 `any` 类型（应避免）
   - **Mock 检查**：
     - Python: `@patch`, `MagicMock`, `Mock(`, `mock_`
     - TS/JS: `vi.fn`, `vi.mock`, `jest.fn`, `jest.mock`
   - **错误提示检查**：
     - 检查 HTTPException/throw 的 detail/message 是否暴露技术细节
   - **函数设计检查**：
     - 函数长度 > 40 行
     - 参数数量 > 5 个
     - 嵌套深度 > 3 层
   - 检查未完成代码：`TODO`, `FIXME`, `XXX`, `HACK`
   - 检查新增文件复用说明：新文件是否有「搜索关键词」和「为什么不复用」注释

2. **Agent2: 后端自动化**（如有后端变更）
   - ruff check backend/
   - mypy backend/app/ --ignore-missing-imports
   - pytest backend/tests/ -q --tb=line

3. **Agent3: 前端自动化**（如有前端变更）
   - npm run lint
   - npm run type-check
   - npm run build

4. **Agent4: 代码质量审查**
   - 对每个变更文件进行代码审查
   - 检查安全性、性能、代码规范

5. **Agent5: 文档同步检查**
   - 分析变更文件，识别代码改动类型（API/功能/配置/架构）
   - 搜索 docs/ 目录下相关文档
   - 验证文档内容与代码是否一致
   - 返回需要更新但未更新的文档列表

6. **Agent6: 服务启动验证**
   - 见下方 Agent6 Task 定义

7. **Agent7: 需求覆盖检查**（防止欺骗/遗漏）
   - **目的**：验证代码实现与计划/需求完全一致
   - **步骤**：
     1. 找到计划文档：`docs/开发文档/plan_*.md`（兼容扫描 `docs/plan_*.md`）
     2. 提取 Tasks 执行清单中的每个任务
     3. 对每个任务：
        - 提取验收标准/功能点
        - 检查对应代码是否存在
        - 验证功能是否完整实现（不只是文件存在）
     4. 输出覆盖报告
   - **检查内容**：
     - 功能完整性：计划要求的功能是否都实现了
     - 接口一致性：API 签名是否与设计一致
     - 行为正确性：代码逻辑是否符合需求描述
   - **输出格式**：逐条对照表
```

**执行方式**（在一条消息中发送多个 Task 调用）：

```
<Task>
  subagent_type: Explore
  description: "铁律检查"
  prompt: "检查以下目录中的铁律违反情况：
    1. 降级逻辑：
       - Java: grep -rE 'orElse\(null\)|orElseGet\(\(\) -> null\)|catch.*return null' --include='*.java'
       - Python: grep -rE 'except:.*pass|or None|if.*else None' --include='*.py'
       - TS/JS: grep -rE 'catch.*return null|\|\| null|\?\? null' --include='*.ts' --include='*.tsx'
    2. 硬编码：
       - URL: grep -rE 'http://localhost|127\.0\.0\.1|://.*:[0-9]{4,5}' --include='*.java' --include='*.py' --include='*.ts'
       - 密钥: grep -rE 'api_key.*=|secret.*=|password.*=|token.*=' --include='*.java' --include='*.py' --include='*.ts'
    3. 常量分层（详见硬编码治理规范.md）：
       - 跨模块导入: grep -rn 'from src\.\(adapters\|services\|modules\)\.[^.]\+\.constants import' src/ | 检查是否在其他模块中使用
       - 模块常量前缀: 检查 src/**/constants.py 中的常量是否带模块前缀
       - 常量膨胀: wc -l src/constants.py src/**/constants.py 2>/dev/null | 超过200行需拆分
    4. Mock：
       - Python: grep -rE '@patch|MagicMock|Mock\(|mock_' --include='*.py' tests/
       - TS/JS: grep -rE 'vi\.fn|vi\.mock|jest\.fn|jest\.mock' --include='*.ts' --include='*.tsx'
    5. 未完成代码：grep -rE 'TODO|FIXME|XXX|HACK' --include='*.java' --include='*.py' --include='*.ts'
    6. 代码复用：检查新增文件是否有「搜索关键词」和「为什么不复用」注释（如有新增文件）
    返回：发现的违反项列表（文件:行号:违规类型:内容），或'无违反'"
</Task>

<Task>
  subagent_type: Bash
  description: "后端自动化验证"
  prompt: "cd backend && source venv/bin/activate 2>/dev/null; ruff check . 2>&1; mypy app/ --ignore-missing-imports 2>&1; pytest tests/ -q --tb=line 2>&1"
</Task>

<Task>
  subagent_type: Bash
  description: "前端自动化验证"
  prompt: "cd frontend && npm run lint 2>&1; npm run type-check 2>&1; npm run build 2>&1"
</Task>

<Task>
  subagent_type: Explore
  description: "代码质量审查"
  prompt: "审查以下变更文件的代码质量：[文件列表]
    检查项：
    1. 安全性：SQL注入、XSS、敏感信息泄露
    2. 性能：N+1查询、无效循环
    3. 代码规范：命名、类型注解、异常处理
    返回：问题列表（文件:行号:问题:严重程度）"
</Task>

<Task>
  subagent_type: Explore
  description: "文档同步检查"
  prompt: "检查代码变更是否需要同步更新文档：
    1. 分析变更文件列表（从 Phase 1 输出获取）
    2. 识别改动类型：
       - API 变更（新增/修改接口）→ **必须**更新 `docs/API文档/`
       - 功能变更 → **必须**更新 `docs/需求文档/`
       - 架构变更 → **必须**更新 `docs/设计文档/`
       - 配置变更 → **必须**更新 `docs/交付文档/`
    3. 搜索 docs/ 目录下相关文档
    4. 验证文档内容与代码是否一致

    **重要**：文档不同步是阻塞项，不是建议项。
    禁止使用'建议'、'可选'等表述。

    返回：
    - ❌ 需要更新的文档列表（阻塞项，必须修复）
    - 文档与代码不一致的具体位置
    - 或 ✅ '文档已同步，无需更新'"
</Task>

<Task>
  subagent_type: Bash
  description: "服务启动验证"
  prompt: "验证服务能正常启动并响应请求（见 ~/.claude/reference/完成前验证.md）：

    # 1. 检测项目类型并启动服务
    if [ -f 'backend/pyproject.toml' ] || [ -f 'backend/requirements.txt' ]; then
        echo '检测到 Python 后端项目'
        cd backend
        source venv/bin/activate 2>/dev/null
        python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
        PID=$!
        sleep 3

        # 2. 健康检查
        echo '执行健康检查...'
        if curl -sf http://127.0.0.1:8000/health; then
            echo '✅ 健康检查通过'
        elif curl -sf http://127.0.0.1:8000/; then
            echo '✅ 根路径响应正常'
        else
            echo '❌ 健康检查失败'
        fi

        # 3. 清理
        kill $PID 2>/dev/null

    elif [ -f 'package.json' ]; then
        echo '检测到 Node.js 项目'
        npm run dev &
        PID=$!
        sleep 5

        if curl -sf http://127.0.0.1:3000/; then
            echo '✅ 服务启动验证通过'
        else
            echo '❌ 服务启动验证失败'
        fi

        kill $PID 2>/dev/null

    elif [ -f 'pom.xml' ]; then
        echo '检测到 Java Maven 项目'
        mvn spring-boot:run &
        PID=$!
        sleep 10

        if curl -sf http://127.0.0.1:8080/actuator/health; then
            echo '✅ 健康检查通过'
        else
            echo '❌ 健康检查失败'
        fi

        kill $PID 2>/dev/null
    else
        echo '⚠️ 未检测到已知项目类型，跳过服务启动验证'
    fi

    **铁律**：如果健康检查失败，这是阻塞项，必须修复。
    返回：✅ 服务启动验证通过 或 ❌ 服务启动验证失败（附错误信息）"
</Task>

<Task>
  subagent_type: Explore
  description: "需求覆盖检查"
  prompt: "验证代码实现与计划/需求完全一致（防止欺骗/遗漏）：

    ## 第一步：找到计划文档

    搜索计划文档：
    - docs/开发文档/plan_*.md（标准位置）
    - docs/plan_*.md（兼容旧文件）
    - 或当前会话中提到的需求文档

    如果找不到计划文档，返回 '⚠️ 未找到计划文档，跳过需求覆盖检查'

    ## 第二步：提取验收标准

    从计划文档中提取：
    1. Tasks 执行清单中的每个任务
    2. 每个任务的验收标准 / 功能点
    3. 接口设计（如有）

    ## 第三步：逐条对照检查

    对每个功能点：
    1. **代码存在性**：对应的代码文件/函数是否存在
    2. **功能完整性**：是否只是空壳/占位符（检查函数体是否有实际逻辑）
    3. **接口一致性**：API 签名是否与设计一致（参数、返回值）
    4. **行为正确性**：代码逻辑是否符合需求描述

    ## 第四步：输出覆盖报告

    **检查重点（防止欺骗）**：
    - 函数体是否只有 pass/return None/raise NotImplementedError
    - 是否只创建了文件但没有实现内容
    - 是否只实现了部分功能
    - 前端是否只有 UI 但没有调用后端
    - 后端是否只有路由但没有业务逻辑

    **输出格式**：

    | 需求/功能点 | 代码位置 | 状态 | 说明 |
    |------------|---------|------|------|
    | [功能1] | file.py:行号 | ✅ 已实现 / ❌ 未实现 / ⚠️ 部分实现 | [具体说明] |
    | [功能2] | ... | ... | ... |

    **覆盖率统计**：
    - 已完整实现：X/Y (Z%)
    - 部分实现：X 个
    - 未实现：X 个

    **结论**：
    - ✅ 需求覆盖完整，可以继续
    - ❌ 存在未实现/部分实现的功能，列表如下：[...]

    **铁律**：
    - 任何未实现或部分实现都是阻塞项
    - 禁止 '基本完成'、'大部分完成' 等表述
    - 要么 100% 实现，要么列出缺失项"
</Task>
```

**等待所有 Agent 完成后继续。**

---

#### Agent8: TDD 流程验证

**目的**：确保测试先于实现，不是后补的

```
<Task>
  subagent_type: Explore
  description: "TDD 流程验证"
  prompt: "验证本次变更是否遵循 TDD 流程（测试先于实现）：

    ## 验证方式（优先级从高到低）

    ### 1. 会话内验证（首选）
    检查当前会话中是否有'写测试 → 失败 → 实现'的记录。
    如果是由 /run-plan 执行的任务，应该有 TDD 执行记录。

    ### 2. Git 历史验证（备选）
    对于已有代码的修改，检查 git 提交顺序：
    ```bash
    # 检查测试文件和实现文件的提交时间
    git log --oneline --follow -- tests/test_*.py
    git log --oneline --follow -- app/**/*.py
    ```

    ### 3. 文件时间戳验证（兜底）
    检查测试文件的修改时间是否 ≤ 实现文件：
    ```bash
    ls -la tests/test_*.py
    ls -la app/**/*.py
    ```

    ## 相关测试识别（与 /qa 统一标准）

    对每个新增/修改的实现文件，按以下规则识别相关测试：
    1. **文件名对应**：`login.py` → `test_login.py`
    2. **import 关系**：测试文件 import 了变更模块
    3. **函数/类调用**：测试中调用了变更的函数/类

    ## 检查内容

    对每个识别出的相关测试：
    1. 测试文件是否存在
    2. 测试文件是否有实际的测试用例（不是空文件）
    3. 测试是否覆盖了主要功能

    ## 输出格式

    | 实现文件 | 测试文件 | TDD 状态 | 说明 |
    |---------|---------|---------|------|
    | login.py | test_login.py | ✅ TDD 符合 | 测试先于实现 |
    | register.py | test_register.py | ⚠️ 无法验证 | 首次开发 |
    | utils.py | (无) | ❌ 缺少测试 | 需补充测试 |

    **结论**：
    - ✅ TDD 流程符合
    - ⚠️ 部分无法验证（首次开发），已启用 TDD 监控
    - ❌ TDD 流程违反：以下文件的测试是后补的或缺失的 [列表]

    **铁律**：
    - 缺少测试是阻塞项（除非紧急模式）
    - 测试后补需要在报告中标记"
</Task>
```

---

#### Agent9: Hooks 配置检测

**目的**：确保测试自动化配置就绪

```
<Task>
  subagent_type: Bash
  description: "Hooks 配置检测"
  prompt: "检测项目是否配置了测试 Hooks：

    # 1. 检查配置文件是否存在
    if [ -f '.claude/settings.json' ]; then
        echo '✅ .claude/settings.json 存在'

        # 2. 检查是否有 PostToolUse hooks
        if grep -q 'PostToolUse' .claude/settings.json; then
            echo '✅ PostToolUse hooks 已配置'

            # 3. 检查是否有测试相关命令
            if grep -q 'pytest\|npm test\|jest' .claude/settings.json; then
                echo '✅ 测试命令已配置'
            else
                echo '⚠️ 未检测到测试命令（pytest/npm test）'
            fi
        else
            echo '⚠️ PostToolUse hooks 未配置'
        fi
    else
        echo 'ℹ️ 未配置测试 Hooks（可选）'
    fi"
</Task>
```

**注意**：Hooks 是可选功能，不配置也不影响 `/check` 和 `/qa` 的正常使用。

---

### Phase 3: 汇总报告

```markdown
# /check 开发检查报告（并行版）

**检查时间**：YYYY-MM-DD HH:mm
**变更范围**：X 个文件
**执行模式**：9 Agent 并行

---

## 自我审问
- [x] 代码完整阅读
- [x] 前后端同步（如适用）
- [x] 无假设性结论
- [x] 新增代码已搜索复用

## Agent1: 铁律检查（7 项）
- [ ] HTTP 调用都检查了状态码
- [ ] 无降级逻辑（静默失败）
- [ ] 无硬编码配置
- [ ] 类型注解完整
- [ ] 无 Mock 数据
- [ ] 错误提示用户友好
- [ ] 函数设计符合约束（长度/参数/嵌套）
- [ ] 无未完成代码（TODO/FIXME）
- [ ] 新增文件有复用说明（如适用）

## Agent2: 后端自动化
- [ ] ruff: 通过/X 个问题
- [ ] mypy: 通过/X 个问题
- [ ] pytest: X/X 通过

## Agent3: 前端自动化
- [ ] lint: 通过/X 个问题
- [ ] type-check: 通过/X 个问题
- [ ] build: 通过/失败

## Agent4: 代码质量
| 文件 | 行号 | 问题 | 严重程度 |
|------|------|------|---------|
| （无问题 或 列出问题）|

## Agent5: 文档同步（阻塞项）
- [ ] 相关文档已识别
- [ ] 文档内容与代码一致
- 需要更新的文档：（无/列表）

**注意**：文档不同步是阻塞项，必须修复后才能继续。禁止"建议更新（可选）"表述。

## Agent6: 服务启动验证（铁律）
- [ ] 服务启动无报错
- [ ] 健康检查端点响应 200
- [ ] 无未捕获的异常

**铁律**：如果没有亲眼看到服务正常启动并响应请求，就不能声称完成。

## Agent7: 需求覆盖检查（阻塞项）

**计划文档**：[plan_xxx.md]

| 需求/功能点 | 代码位置 | 状态 | 说明 |
|------------|---------|------|------|
| [功能1] | file.py:行号 | ✅/❌/⚠️ | [说明] |
| [功能2] | ... | ... | ... |

**覆盖率统计**：
- 已完整实现：X/Y (Z%)
- 部分实现：X 个
- 未实现：X 个

**结论**：✅ 需求覆盖完整 / ❌ 存在缺失

**铁律**：
- 任何未实现或部分实现都是阻塞项，必须修复
- 禁止"基本完成"、"大部分完成"等表述

## Agent8: TDD 流程验证（阻塞项/紧急模式警告）

| 实现文件 | 测试文件 | TDD 状态 | 说明 |
|---------|---------|---------|------|
| login.py | test_login.py | ✅/❌/⚠️ | [说明] |

**结论**：
- ✅ TDD 流程符合
- ⚠️ 部分无法验证（首次开发）
- ❌ TDD 流程违反：需补充测试

**紧急模式**：[ ] 已启用（跳过 TDD 检查，需事后补测试）

## Agent9: Hooks 配置检测（可选）

- Hooks 状态：[已配置 / 未配置]

（Hooks 是可选功能，不影响 /check 和 /qa 使用）

---

## 结论

✅ **检查通过** - 可以执行 `/qa`

或

❌ **需要修复以下问题才能继续**：

| # | 问题 | 文件 | 修复方式 |
|---|------|------|---------|
| 1 | xxx | file.py:123 | [具体修复方法] |

**全部修复后重新执行 `/check`**

---

### 问题分类规则

| 类型 | 处理方式 | 示例 |
|------|---------|------|
| **本次引入** | 必须立即修复 | 新代码的 lint 错误 |
| **存量问题** | 修复当前文件涉及的部分 | 改动文件的类型注解 |
| **基础设施** | 第一次遇到就装好 | ruff/mypy 未安装 |

**禁止表述**：
- ❌ "不阻塞交付"
- ❌ "可以后续改进"
- ❌ "建议优化，非必须"

**正确表述**：
- ✅ "需要修复以下问题才能继续"
- ✅ "全部修复后重新执行 /check"
```

---

## 简化执行模板

**实际执行时，直接复制此模板**：

### Step 1: 快速审问

```
自我审问：代码读完 ✓ | 前后端同步 ✓ | 无假设 ✓ | 符合计划 ✓ | 复用已搜索 ✓
```

### Step 2: 获取变更

```bash
git status --short && git diff --stat HEAD~1
```

### Step 3: 并行检查（一条消息发 9 个 Task）

根据变更范围，选择需要的 Agent：
- 有后端变更 → Agent1 + Agent2 + Agent4 + Agent5 + Agent6 + Agent7 + Agent8 + Agent9
- 有前端变更 → Agent1 + Agent3 + Agent4 + Agent5 + Agent6 + Agent7 + Agent8 + Agent9
- 全栈变更 → 全部 9 个 Agent
- Agent5（文档同步）始终执行
- Agent6（服务启动验证）在有代码变更时始终执行
- Agent7（需求覆盖检查）在有计划文档时始终执行
- Agent8（TDD 流程验证）在有代码变更时始终执行
- Agent9（Hooks 配置检测）始终执行（建议项）

### Step 4: 汇总并输出报告

---

## 场景适配

| 变更类型 | 启动的 Agent | 预估耗时 |
|---------|-------------|---------|
| 仅后端 | 1 + 2 + 4 + 5 + 6 + 7 + 8 + 9 | 2-3 分钟 |
| 仅前端 | 1 + 3 + 4 + 5 + 6 + 7 + 8 + 9 | 2-3 分钟 |
| 全栈 | 全部 9 个 Agent | 3-4 分钟 |
| 仅文档 | 4 + 5 + 9（简化审查） | 30 秒 |

**注意**：
- Agent6（服务启动验证）在有代码变更时始终执行
- Agent7（需求覆盖检查）在有计划文档时始终执行（防止欺骗/遗漏）
- Agent8（TDD 流程验证）在有代码变更时始终执行（确保测试先于实现）
- Agent9（Hooks 配置检测）始终执行（建议项，不阻塞）

---

## ⛔ 边界约束（铁律）

> **`/check` 的职责边界：只做开发检查，不能跳过后续环节**

| 禁止行为 | 说明 |
|---------|------|
| ❌ 跳过 `/qa` 直接进入 `/ship` | 必须按顺序：check → qa → ship |
| ❌ 检查失败时继续后续流程 | 必须修复问题后重新检查 |

**正确的完成动作**：
1. 输出检查报告
2. 展示完成提示
3. 进入下一环节 `/qa`（正常流转）或等待用户指令

**跳过环节的处理**：
- `/qa` 不能跳过，这是质量门控

---

## 禁止行为

| 禁止行为 | 说明 |
|---------|------|
| 跳过自我审问 | Phase 0 必须先完成 |
| 串行执行检查 | 必须使用 Task 并行 |
| 忽略 Agent 返回的错误 | 所有错误必须汇总 |
| 假设性结论 | 必须有实际输出证据 |

---

## 与其他 Skills 的关系

```
/run-plan（执行计划）
    ↓ 开发完成后
/check（开发检查）← 当前（并行版）
    ↓ 检查通过后
/qa（测试验收）
    ↓ 测试通过后
/ship（代码交付）
```

---

## ✅ 完成提示

```
✅ 开发检查通过（并行执行）

⏱️ 执行统计：
- Agent1 铁律检查：X 秒
- Agent2 后端自动化：X 秒
- Agent3 前端自动化：X 秒
- Agent4 代码审查：X 秒
- Agent5 文档同步：X 秒
- Agent6 服务启动验证：X 秒 ← 亲眼看到服务正常运行
- Agent7 需求覆盖检查：X 秒 ← 确认代码实现与计划一致
- Agent8 TDD 流程验证：X 秒 ← 确认测试先于实现
- Agent9 Hooks 配置检测：X 秒
- 总耗时：X 秒（并行）

📊 需求覆盖率：X/Y (100%)
🧪 TDD 符合率：X/Y (100%)

下一步：/qa（测试验收）
```

---

**版本**：v4.2（多 Agent 并行版 + TDD 验证 + Hooks 检测）
**更新日期**：2026-01-28
**核心改进**：
- **v4.0 新增**：Agent8 TDD 流程验证（确保测试先于实现）
- **v4.0 新增**：Agent9 Hooks 配置检测（建议配置测试自动化）
- **v4.0 新增**：紧急模式支持（跳过 TDD 检查，需事后补测试）
- 9 Agent 并行执行，全面质量检查
**v4.2 修复**：
- Hooks 配置模板：matcher 排除 tests 目录，避免无限循环
- 新增 TDD规范.md 文件，完善 Agent8 引用链
**v4.1 修复**：
- 统一"相关测试识别"定义（与 /qa 一致：文件名对应、import 关系、函数调用）
**改进要点**：
- **v3.1 新增**：Agent7 需求覆盖检查（防止欺骗/遗漏，确保代码与计划一致）
- **v3.0 新增**：Agent6 服务启动验证（必须亲眼看到服务正常运行）
- 引用 `~/.claude/reference/完成前验证.md` 规范
- 7 Agent 并行执行，文档同步检查
