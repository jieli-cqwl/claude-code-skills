---
name: mcp-builder
command: mcp-builder
user_invocable: true
description: |
  MCP 服务器开发指南。自动激活场景：
  1) 用户说"开发 MCP"、"MCP 服务"、"做个 MCP server"时
  2) 用户说"让 Claude 能调用外部服务"、"集成外部 API 给 AI 用"时
  3) 需要让 LLM 与外部服务交互时
  构建高质量的 Model Context Protocol 服务器。来源：anthropics/skills（官方）
---

# MCP Server Development Guide

> **来源**: [anthropics/skills](https://github.com/anthropics/skills) - Anthropic 官方 Skills

---

## 依赖规范

> **执行前按需读取**：以下规范文件在执行时按需加载。

| 规范文件 | 覆盖内容 |
|---------|---------|
| `~/.claude/reference/MCP工具规范.md` | 工具命名、Schema 设计、错误处理 |

**执行 /mcp-builder 时，自动读取上述规范文件。**

> **职责分离**：本 Skill 定义开发**流程**，规范文件定义开发**标准**。

---

## 什么是 MCP

Model Context Protocol (MCP) 是一种让 LLM 与外部服务交互的协议。通过 MCP Server，Claude 可以：
- 查询数据库
- 调用外部 API
- 读写文件系统
- 执行特定操作

---

## 四阶段开发流程

### Phase 1: 研究和规划

1. **学习 MCP 协议**
   - 官方文档：https://modelcontextprotocol.io
   - SDK 文档（推荐 TypeScript）

2. **分析目标服务 API**
   - 认证方式
   - 可用端点
   - 数据格式

3. **规划工具设计**（命名规范：`{domain}_{action}_{resource}`）
   ```markdown
   ## 工具列表

   | 工具名 | 用途 | 参数 |
   |--------|------|------|
   | user_list_records | 获取用户列表 | page, limit |
   | user_get_info | 获取用户详情 | user_id |
   | user_create_record | 创建用户 | name, email |
   ```

### Phase 2: 实现

1. **项目结构**（TypeScript）

```
my-mcp-server/
├── src/
│   ├── index.ts         # 入口
│   ├── tools/           # 工具实现
│   │   ├── users.ts
│   │   └── orders.ts
│   ├── api/             # API 客户端
│   │   └── client.ts
│   └── types/           # 类型定义
│       └── schemas.ts
├── package.json
└── tsconfig.json
```

2. **工具定义示例**

```typescript
import { z } from 'zod'

// 参数 Schema
const GetUserSchema = z.object({
  user_id: z.string().describe('用户 ID')
})

// 工具定义
const getUserTool = {
  name: 'get_user',
  description: '根据 ID 获取用户详情',
  inputSchema: GetUserSchema,
  annotations: {
    readOnly: true,      // 只读操作
    idempotent: true,    // 幂等
    openWorld: false     // 结果可预测
  }
}

// 工具实现
async function getUser(params: z.infer<typeof GetUserSchema>) {
  const { user_id } = params
  const user = await apiClient.users.get(user_id)
  return {
    content: [{
      type: 'text',
      text: JSON.stringify(user, null, 2)
    }]
  }
}
```

### Phase 3: 测试

1. **构建**
   ```bash
   npm run build
   ```

2. **使用 MCP Inspector 测试**
   ```bash
   npx @anthropic-ai/mcp-inspector ./dist/index.js
   ```

3. **检查清单**
   - [ ] 所有工具都能正常调用
   - [ ] 错误处理正确
   - [ ] 返回格式符合预期

### Phase 4: 评估

创建 10 个测试问题验证 LLM 使用效果：

```xml
<evaluations>
  <evaluation>
    <question>列出所有活跃用户</question>
    <expected_tools>list_users</expected_tools>
    <verification>返回用户列表，状态为 active</verification>
  </evaluation>
  ...
</evaluations>
```

---

## 设计原则

> **详细规范**：参见 `~/.claude/reference/MCP工具规范.md`

| 原则 | 说明 |
|------|------|
| **命名规范** | 使用 `{domain}_{action}_{resource}` 格式（详见规范） |
| **友好错误** | 错误信息要指导如何解决，不是单纯报错 |
| **分页支持** | 列表接口要支持分页 |
| **类型安全** | 使用 Zod/Pydantic 定义参数 Schema |
| **注解完整** | 标注 readOnly, destructive, idempotent |

---

## 工具注解

```typescript
annotations: {
  readOnly: true,       // 只读，不修改数据
  destructive: false,   // 是否有破坏性
  idempotent: true,     // 多次调用结果相同
  openWorld: false      // 结果是否不可预测
}
```

---

## 推荐技术栈

| 组件 | 推荐 |
|------|------|
| 语言 | TypeScript |
| 传输 | stdio（本地）或 HTTP（远程） |
| Schema | Zod |
| API 客户端 | axios 或 fetch |

---

## Few-shot 对比示例

### 好的 MCP Server

- 工具定义完整：名称、描述、参数 schema（含类型、必填、默认值）
- 错误处理规范：参数校验失败返回 `isError: true` + 用户友好消息
- 幂等性：同一请求重复调用返回一致结果
- 资源清理：连接池在 server shutdown 时正确关闭

### 坏的 MCP Server

- 工具描述为空或过于简短（LLM 无法理解何时调用此工具）
- 异常直接抛出裸 Error（调用方看到 "Internal Server Error"，无法定位问题）
- 无输入校验（传入非法参数时 server crash）
- 长连接未设超时（网络中断时连接泄漏，最终耗尽资源）

---

## 资源

- [MCP 协议文档](https://modelcontextprotocol.io)
- [TypeScript SDK](https://github.com/anthropics/mcp-typescript-sdk)
- [示例 MCP Servers](https://github.com/anthropics/mcp-servers)
