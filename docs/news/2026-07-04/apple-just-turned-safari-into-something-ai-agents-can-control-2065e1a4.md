<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-04T01:19:46+08:00
source: The New Stack
domain: AI 基础设施
url: https://thenewstack.io/safari-mcp-platform-infrastructure/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# 苹果刚刚将 Safari 变成了人工智能代理可以控制的东西

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-04 01:19 CST |
| 领域 | AI 基础设施 |
| 来源 | The New Stack |
| 原文标题 | Apple just turned Safari into something AI agents can control |
| 原文 | [打开原文](https://thenewstack.io/safari-mcp-platform-infrastructure/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

本周早些时候，Apple 的 WebKit 团队发布了带有内置模型上下文协议服务器的 Safari 技术预览版 247 — 16 Apple 刚刚将 Safari 变成 AI 代理可以控制的东西的帖子首先出现在 The New Stack 上。

## 正文

本周早些时候，Apple 的 WebKit 团队发布了带有内置模型上下文协议服务器的 [Safari 技术预览版 247](https://webkit.org/blog/18136/introducing-the-safari-mcp-server-for-web-developers/) — 16 个工具，可让任何兼容 MCP 的 AI 代理直接访问实时 Safari 浏览器窗口。 Within this workflow, an agent can capture screenshots, inspect the DOM, execute JavaScript, read console output, monitor network requests, resize the viewport, emulate CSS media modes, and run accessibility checks, all without the developer leaving the terminal.

任何使用 Safari 进行开发的人都知道这是生活质量的显着改善。 And since this is the second official MCP server Apple has shipped in under a month, platform vendors are starting to build MCP into their products rather than leaving it to community implementations.

### 两台服务器，三周

在 6 月初的 WWDC 上，Apple 在 Xcode 27 中引入了 MCPBridge，这是一个二进制文件，可将 XPC 上的 MCP 转换为 Xcode 的实时进程，公开 [20 个内置工具](https://developer.apple.com/documentation/xcode/giving-external-agents-access-to-xcode)，让 AI 代理构建项目、运行测试、渲染 SwiftUI 预览、搜索文档和读取诊断信息。来自 Anthropic、OpenAI 和 Google 的代理都可以通过相同的协议进行连接。

Safari MCP 服务器非常相似，因为它作为 Safari 技术预览版的一部分提供，连接到任何 MCP 客户端，并通过标准化接口公开浏览器功能。如果您愿意，可以将其称为实验，但如果您问我，大约三周内从单个平台供应商作为标准产品功能发货的两台官方 MCP 服务器就证明了 MCP 正在成为平台基础设施。

>

大约三周内，单个平台供应商将两台官方 MCP 服务器作为标准产品功能发货，这证明 MCP 正在成为平台基础设施。

### 架构隐私

服务器完全在本地计算机上运行，无法访问 Safari 中的个人信息。这意味着没有自动填充数据，没有浏览历史记录，也没有其他浏览器活动。当它捕获页面内容、屏幕截图或控制台日志时，数据会直接发送到开发人员正在运行的 AI 代理，而不是发送到 Apple；从那里发生的事情取决于代理及其背后的模型。这种隐私架构值得注意，因为它与其他浏览器供应商处理人工智能集成的方式不同。微软 Edge 中的 Copilot 通过微软的基础设施读取和分析打开的选项卡，而谷歌的 Gemini for Mac 通过谷歌的模型访问本地文件。在这两种情况下，浏览器公司和AI公司是同一实体，简化了技术架构，但集中了信任关系。苹果的方法将两者解耦：浏览器供应商提供界面，开发人员选择信任哪个人工智能来处理会话数据。

结果是 Safari 成为调试循环的积极参与者，代理可以直接查询。

>

苹果的方法将两者解耦：浏览器供应商提供界面，开发人员选择信任哪个人工智能来处理会话数据。

### 从社区到供应商

不久前，人工智能代理的浏览器集成几乎完全依赖于社区构建的工具。开发人员通过 Playwright、Chrome DevTools 协议包装器或志愿者维护的非官方 MCP 服务器拼凑连接。这些方法有效，但它们依赖于逆向工程，几乎没有提供供应商支持承诺，并且在浏览器版本之间出现不可预测的中断。

让我们记住，苹果并不是唯一采取这一举措的公司。自 2025.2 版本以来，JetBrains 在 IntelliJ IDEA 中提供了捆绑的 MCP 服务器，并且[在 2026.2 EAP 中扩展其 MCP 范围](https://blog.jetbrains.com/idea/2026/05/intellij-idea-2026-2-eap/)，以通过协议向代理公开调试功能（包括断点和日志点）。 Brave 为其搜索 API 维护一个[官方 MCP 服务器](https://github.com/brave/brave-search-mcp-server)。 Anthropic 将模型上下文协议本身[捐赠给 Linux 基金会的 Agentic AI 基金会](https://www.linuxfoundation.org/press/anthropic-donates-model-context-protocol-to-linux-foundation)，OpenAI、Google 和 Microsoft 都公开认可了它。

一致的策略表明，构建浏览器、IDE 和开发者平台的公司正在将 MCP 端点作为标准产品功能提供，而不是依靠社区集成来填补空白。

### 可靠性需要官方支持简而言之，官方实现与底层软件同步更新。 Apple 控制 Safari MCP 服务器和 Safari 渲染引擎之间的兼容性。社区维护的替代方案无法提供相同的保证，因为它们依赖于供应商可以随时更改的稳定的内部 API。

对于评估是否依赖代理驱动的调试、测试或部署的工程团队来说，底层集成的可靠性与模型的功能一样重要。如果每次浏览器发布一个版本时提供 DOM 树的工具都会中断，那么可以推理 DOM 树的模型就没有用处。

>

如果每次浏览器发布一个版本时提供 DOM 树的工具都会中断，那么可以推理 DOM 树的模型就没有用处。

我们不能忘记安全模型：Apple 的 Safari MCP 服务器明确规定了其访问范围——供应商更容易可靠地执行这一边界，而不是第三方集成所承诺的边界。

### What comes next

现在就说吧：MCP 正在进入平台基础设施领域。如果这个轨迹成立，开发人员最终可能会期望软件以与他们今天期望的 REST API、SDK 或命令行工具大致相同的方式公开 MCP 接口。

代理工具通信的竞争方法仍然存在，生态系统继续快速发展。但平台供应商将 MCP 视为一种运输产品功能而不是集成实验这一事实标志着一个明显的阶段性变化。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
