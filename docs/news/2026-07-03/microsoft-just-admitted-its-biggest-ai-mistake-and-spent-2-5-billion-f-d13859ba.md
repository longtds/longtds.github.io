<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-03T05:03:36+08:00
source: The New Stack
domain: AI 基础设施
url: https://thenewstack.io/enterprise-ai-model-routing/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# 微软刚刚承认其最大的人工智能错误，并花费 25 亿美元修复它

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-03 05:03 CST |
| 领域 | AI 基础设施 |
| 来源 | The New Stack |
| 原文标题 | Microsoft just admitted its biggest AI mistake — and spent $2.5 billion fixing it |
| 原文 | [打开原文](https://thenewstack.io/enterprise-ai-model-routing/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

微软最新的人工智能服务公告表明，单一模型标准化的时代可能正在结束。本周，微软刚刚承认了其最大的人工智能错误，并花费 25 亿美元修复该错误，该帖子首先出现在 The New Stack 上。

## 正文

微软最新的人工智能服务公告表明，单一模型标准化的时代可能正在结束。本周，该公司[推出了价值 25 亿美元的人工智能采用业务](https://www.reuters.com/business/retail-consumer/microsoft-launches-firm-help-companies-adopt-ai-with-25-billion-2026-07-02/)，旨在帮助企业定制人工智能部署并使用多个模型，而不是将自己锁定在单一提供商——这是向将每个请求路由到最适合任务的模型的系统进行更大转变的一部分。

简而言之，这家可以说是业内拥有最深厚单一模型合作伙伴关系的公司现在正在将模型可互换性作为产品进行销售。

### 将 25 亿美元押注于灵活性

据[路透社报道](https://www.reuters.com/business/retail-consumer/microsoft-launches-firm-help-companies-adopt-ai-with-25-billion-2026-07-02/)，微软周四表示，它正在创建一个新的运营实体 Microsoft Frontier Company，以帮助企业客户选择真正适合其业务并产生投资回报的人工智能技术。该部门由微软提供 25 亿美元资金启动，并将与包括联合利华和诺和诺德在内的客户合作。

新公司将帮助客户选择来自微软和外部提供商的人工智能工具并将其与每个客户的内部数据集成。客户将拥有该工作的成果，而不是将其返还给微软。此举使微软与 Palantir 和 Amazon Web Services 并肩作战，Palantir 正在使用 Nvidia 的开源模型与大客户开展类似的工作，而 Amazon Web Services 最近推出了自己的 [10 亿美元嵌入式工程部门](https://www.cnbc.com/2026/07/02/microsoft-commits-2point5-billion-6000-employees-ai-implementation-unit.html)。最能说明问题的是推理。微软商业业务首席执行官 Judson Althoff [告诉路透社](https://www.reuters.com/business/retail-consumer/microsoft-launches-firm-help-companies-adopt-ai-with-25-billion-2026-07-02/) 这家新公司的成长部分源于微软自己观察 DeepSeek 和谷歌 Gemini 等模型赶上 OpenAI 的经验。在谈到最初的 Copilot 时，他说：“我们犯了一个错误，只将它与 OpenAI 模型绑定。” Althoff 表示，客户更关心他们的数据和模型的组合，而不是任何特定的模型，而且他们需要能够随着最先进技术的变化而快速交换模型。

>

“我们犯了一个错误，只将它绑定到 OpenAI 模型。”

### 一种型号不再适合

考虑一个典型的客户服务应用程序，它可能需要总结支持票证、分析 300 页的合同、生成电子邮件、转录会议并审查源代码。这些不一定是同一个问题。像谷歌的 Gemini 这样的模型，具有一百万个或更多代币的上下文窗口，可能是合约的正确选择。像 OpenAI 的 GPT-5.4 mini 或 Anthropic 的 Claude Haiku 这样的小型快速模型可以以一小部分成本处理票证摘要。转录可能会进入专门构建的模型，如 Whisper。如果监管机构要求客户数据保留在本地，像 Meta 的 Llama 或 Mistral 这样的开放权重模型通常是首选。

开发人员不再选择单一的基础模型，而是越来越多地选择多个模型，然后由应用程序决定由哪个模型来处理每个请求。

### AI网关成为核心基础设施

该模型只是堆栈的一个组件，因此路由请求的决策必须位于某个地方。这就是为什么开发人员放弃将应用程序硬编码为单一模型并构建可以在多个模型中进行选择的系统。路由逻辑可能会优先考虑一个请求的成本、另一个请求的速度，或者将敏感工作负载保留在本地模型上。这样，如果一个提供商遇到中断，流量可以路由到其他地方，而无需更改应用程序本身。

>

这家可以说是业内拥有最深厚的单一模型合作伙伴关系的公司现在正在将模型可互换性作为产品进行销售。

### 这改变了开发人员构建的内容一旦公司停止依赖单一模型，挑战就转移到构建系统来决定针对每个请求使用哪个模型。

这意味着开发人员需要工具来路由请求、比较模型性能、监控可靠性、控制成本、执行安全策略以及在模型出现故障时切换到另一个模型，这是一个非常不同的工程问题，特别是因为每次有人使用您的应用程序时都会决定哪个模型应该响应请求。在企业规模上，这些决策每天会发生数百万次，因此它们必须快速、可靠且易于管理。

### 生态系统已经做出反应

[LiteLLM](https://github.com/BerriAI/litellm) 等开源代理和 [Portkey](https://portkey.ai/) 等网关规范了跨提供商的 API。 [LangChain](https://www.langchain.com/) 和 [LangGraph](https://www.langchain.com/langgraph) 等编排框架从一开始就假设存在多个模型。 [模型上下文协议](https://modelcontextprotocol.io/) (MCP) 使工具集成可以跨模型移植，而不是绑定到一个供应商。云提供商本身 - [Amazon Bedrock](https://aws.amazon.com/bedrock/)、[Azure AI Foundry](https://azure.microsoft.com/en-us/products/ai-foundry)、[Google Vertex AI](https://cloud.google.com/vertex-ai) - 现在在单个 API 背后公开了许多模型。

### 编排是新的护城河

核心模型将不断完善。但随着许多业务任务的性能趋同，编排成为挑战。微软的声明表明，最大的供应商相信企业正在朝这个方向发展，并愿意花费数十亿美元来掌握路由层。

>

企业始终不将模型视为平台，而是始终将其视为编排层背后的可替换组件。

云时代教会开发人员不要将应用程序与一台服务器捆绑得太紧；容器化使基础设施变得可移植。现在，同样的理念也被应用于人工智能。企业始终不将模型视为平台，而是始终将其视为编排层背后的可替换组件。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
