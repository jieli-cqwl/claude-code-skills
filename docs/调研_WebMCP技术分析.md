# 调研：WebMCP (Web Model Context Protocol) 技术分析

> 调研日期：2026-02-22
> 状态：早期预览阶段，持续关注

---

## 一、WebMCP 是什么

WebMCP (Web Model Context Protocol) 是 Google 和 Microsoft 联合开发、通过 W3C Web Machine Learning 社区组孵化的**浏览器端标准**。2026 年 2 月在 Chrome 146 Canary 中发布早期预览。

**核心思路**：让网站主动声明自己能做什么（暴露结构化工具），AI Agent 直接调用函数，而不是通过截图/DOM 解析去猜测页面结构。

**注意**：WebMCP 与 Anthropic 的 MCP 是**不同的东西**，尽管名字相似。

---

## 二、解决的核心问题

当前 AI Agent 操作网页的三种方式及痛点：

| 方式 | 问题 |
|------|------|
| 截图识别 | 每张截图消耗 2000+ token，慢、贵、不准 |
| DOM 解析 | 大量无关 HTML 噪声，网站改版就失效 |
| 模拟点击（CSS 选择器） | 依赖页面布局，改版即崩 |

WebMCP 通过浏览器 API `navigator.modelContext` 让网站暴露结构化工具定义，AI Agent 直接调用函数。

---

## 三、关键性能数据

来源：1,890 次真实 API 调用基准测试（GPT-3.5-turbo、GPT-4o、Claude 等模型）

| 指标 | 效果 |
|------|------|
| Token 消耗 | 减少 **89%**（结构化调用 20-100 token vs 截图 2000+ token） |
| 任务成功率 | **97.9%**（传统方式 98.8%，基本持平） |
| 处理开销 | 减少 **67.6%** |
| API 成本 | 降低 **34-63%** |

---

## 四、技术实现

### 4.1 声明式 API（HTML 属性，零 JS）

在已有 `<form>` 上加属性即可：

```html
<form toolname="searchFlight"
      tooldescription="搜索航班"
      toolautosubmit="true">
  <input name="destination" type="text" />
  <input name="date" type="date" />
  <button type="submit">搜索</button>
</form>
```

AI Agent 看到的是结构化工具：`searchFlight(destination, date)`，而非 DOM。

### 4.2 命令式 API（JavaScript，复杂场景）

```javascript
navigator.modelContext.registerTool({
  name: 'addToCart',
  description: '将商品加入购物车',
  inputSchema: {
    type: 'object',
    properties: {
      productId: { type: 'string' },
      quantity: { type: 'number' }
    },
    required: ['productId']
  },
  async execute(args) {
    const result = await cart.add(args.productId, args.quantity);
    return { content: [{ type: 'text', text: JSON.stringify(result) }] };
  }
});
```

### 4.3 两种 API 对比

| 维度 | 声明式 API | 命令式 API |
|------|-----------|-----------|
| 机制 | HTML 属性 `toolname`/`tooldescription` | JS `navigator.modelContext.registerTool()` |
| 复杂度 | 简单表单操作 | 复杂多步骤工作流 |
| 需要 JS | 否 | 是 |
| 适用场景 | 登录、搜索、提交 | 加购、多步流程、自定义逻辑 |

两者可在同一页面共存。

### 4.4 React 集成

已有 `@mcp-b/react-webmcp` 包，提供 `useWebMCP`、`useMcpTool` hooks。

### 4.5 Polyfill

`@mcp-b/global` 包为不支持的浏览器提供 `navigator.modelContext` polyfill。

---

## 五、安全设计

- **Human-in-the-Loop**：AI Agent 不能直接执行操作，浏览器作为中介
- 关键操作弹出用户确认（如"允许 AI 预订这个航班？"）
- 表单提交时触发 `SubmitEvent.agentInvoked`，后端可区分人类/机器请求
- 比模拟点击攻击面更小，但多标签页上下文注入风险仍存在

---

## 六、WebMCP vs Anthropic MCP

| 维度 | Anthropic MCP | WebMCP |
|------|--------------|--------|
| 发起方 | Anthropic（已捐赠 Linux Foundation） | Google + Microsoft (W3C) |
| 运行位置 | **后端服务器** | **浏览器客户端** |
| 协议 | JSON-RPC | 浏览器原生 JS API |
| 用途 | AI 连接后端工具/数据源 | 网站向浏览器内 Agent 暴露操作 |
| 关系 | 服务端标准 | 客户端标准 |

**互补不竞争**：旅游公司可同时维护后端 MCP Server（供 API 直接调用）和前端 WebMCP 工具（供浏览器 Agent 交互）。

---

## 七、与 Claude in Chrome 的关系

Claude Code 的 Chrome 扩展（`mcp__claude-in-chrome__*`）采用"由外向内"方式：截图 → 读取 DOM → 模拟点击。

WebMCP 采用"由内向外"方式：网站主动声明 → AI 直接调用函数。

| 维度 | Claude in Chrome（当前） | WebMCP（未来） |
|------|------------------------|---------------|
| 交互方式 | 模拟人类操作 | 直接调用结构化函数 |
| 谁主导 | AI 猜测页面结构 | 网站主动声明能力 |
| Token 消耗 | 高 | 低（减少 89%） |
| 可靠性 | 页面改版可能失效 | API 契约不变就稳定 |
| 依赖 | 任何网站都能用 | 网站必须实现 WebMCP |
| 覆盖率 | 100% | 极低（几乎没有网站支持） |

**长期会共存**：WebMCP 优先调用，截图/DOM 方式兜底。

### 理论上的桥接方式

若使用 Chrome Canary 并启用 WebMCP flag，可通过 `mcp__claude-in-chrome__javascript_tool` 桥接：

```javascript
// 发现页面工具
const tools = await navigator.modelContext.listTools();
// 直接调用
const result = await navigator.modelContext.invokeTool("searchFlight", {...});
```

---

## 八、当前状态与生态

| 状态项 | 详情 |
|--------|------|
| 可用浏览器 | Chrome 146 Canary（feature flag） |
| 需要条件 | 加入 Google 早期预览计划 |
| Edge 支持 | 预计跟进（微软是联合作者） |
| Firefox/Safari | 尚未表态 |
| 正式发布 | 预计 2026 年中后期 |
| 网站覆盖率 | 约 0（标准刚发布） |
| W3C 状态 | Web Machine Learning 社区组孵化中 |

---

## 九、行动建议

### 短期（现在）：观望

- 标准处于早期预览，API 可能变化
- 几乎没有网站实现 WebMCP
- 当前 Claude in Chrome 截图/DOM 方式覆盖所有网站

### 中期（2026 下半年）：关注两个信号

1. Chrome 稳定版是否默认启用 WebMCP
2. 主流网站是否开始实现

### 长期：如果有自己的 Web 产品

声明式 API 改造成本极低（几行 HTML 属性），值得提前准备：

```html
<!-- 改造前 -->
<form action="/api/search">
  <input name="keyword" type="text" />
  <button type="submit">搜索</button>
</form>

<!-- 改造后：加两个属性 -->
<form action="/api/search"
      toolname="searchProduct"
      tooldescription="按关键词搜索商品">
  <input name="keyword" type="text" />
  <button type="submit">搜索</button>
</form>
```

---

## 十、参考资源

- [Chrome 官方博客: WebMCP Early Preview](https://developer.chrome.com/blog/webmcp-epp)
- [VentureBeat: Chrome ships WebMCP](https://venturebeat.com/infrastructure/google-chrome-ships-webmcp-in-early-preview-turning-every-website-into-a)
- [MarkTechPost: Google AI Introduces WebMCP](https://www.marktechpost.com/2026/02/14/google-ai-introduces-the-webmcp-to-enable-direct-and-structured-website-interactions-for-new-ai-agents/)
- [Search Engine Land: Google previews WebMCP](https://searchengineland.com/google-releases-preview-of-webmcp-how-ai-agents-interact-with-websites-469024)
- [WebMCP 官方站点](https://webmcp.link/)
- [W3C GitHub 仓库](https://github.com/webmachinelearning/webmcp)
- [WebMCP 示例代码](https://github.com/WebMCP-org/examples)
- [Codely: What is WebMCP](https://codely.com/en/blog/what-is-webmcp-and-how-to-use-it)
- [学术论文 (ResearchGate)](https://www.researchgate.net/publication/394472408_webMCP_Efficient_AI-Native_Client-Side_Interaction_for_Agent-Ready_Web_Design)
- [Google Cloud MCP 官方文档](https://docs.cloud.google.com/mcp/overview)（后端 MCP，非 WebMCP）
