---
name: mcp-builder
command: mcp-builder
user_invocable: true
description: MCP 服务器开发指南。构建高质量的 Model Context Protocol 服务器，让 LLM 能够与外部服务交互。适用于 AI 项目集成外部 API。来源：anthropics/skills（官方）
---

# MCP Server Development Guide

> **来源**: [anthropics/skills](https://github.com/anthropics/skills) - Anthropic 官方 Skills

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**开发 MCP**"或"**MCP 服务**"（主触发词）
- 使用命令：`/mcp-builder`
- 说"做个 MCP server"
- 说"让 Claude 能调用外部服务"
- 说"集成外部 API 给 AI 用"

**适用场景**：
- 需要让 LLM 与外部服务交互
- 开发 Claude 插件/工具
- 集成外部 API 到 AI 项目

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

## 资源

- [MCP 协议文档](https://modelcontextprotocol.io)
- [TypeScript SDK](https://github.com/anthropics/mcp-typescript-sdk)
- [示例 MCP Servers](https://github.com/anthropics/mcp-servers)
