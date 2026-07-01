<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:00:00+08:00
source: Google Cloud Blog
domain: AI 基础设施
url: https://cloud.google.com/blog/products/ai-machine-learning/gemini-enterprise-agent-platform-remote-mcp-server/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# Gemini企业代理平台远程MCP服务器|谷歌云博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:00 CST |
| 领域 | AI 基础设施 |
| 来源 | Google Cloud Blog |
| 原文标题 | Gemini Enterprise Agent Platform remote MCP server \| Google Cloud Blog |
| 原文 | [打开原文](https://cloud.google.com/blog/products/ai-machine-learning/gemini-enterprise-agent-platform-remote-mcp-server/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

几个月前，我们宣布有 50 多个 Google 管理的 MCP 服务器可供使用。今天，我们将深入探讨如何使用 Gemini Enterprise Agent Platform 远程 MCP 服务器将外部 AI 代理安全地连接到 Google Cloud 环境内的资源。将您的 IDE 连接到 Google Cloud 将 Agent Platform MCP 服务器视为您最喜欢的外部开发工具和 Google Cloud 架构之间的桥梁。例如，如果您在 Antigravity CLI 或 Claude Code 中构建代理，则代理平台 MCP 服务器允许该代理与您的代理平台资源安全地交互。这样，您的代理现在可以轻松地从 Model Garden 调用模型，p

## 正文

人工智能与机器学习

##

使用 

Gemini Enterprise Agent Platform 的完全托管远程 MCP 服务器更快地构建代理

2026 年 7 月 1 日

###### 科尔比·霍克

Gemini Enterprise 高级产品经理

###### 路易斯·林

软件工程师

###### 立即尝试 

Gemini Enterprise 商业版

几个月前，我们宣布[超过 50 个 Google 管理的 MCP 服务器](https://cloud.google.com/blog/products/ai-machine-learning/google-managed-mcp-servers-are-available-for-everyone?e=48754805) 可用。

今天，我们将深入探讨如何使用 [Gemini Enterprise Agent Platform 远程 MCP 服务器](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/use-agent-platform-mcp) 将外部 AI 代理安全地连接到 Google Cloud 环境内的资源。

#### 将您的 IDE 连接到 

Google Cloud

将 Agent Platform MCP 服务器视为您最喜欢的外部开发工具和 Google Cloud 架构之间的桥梁。

例如，如果您在 Antigravity CLI 或 Claude Code 中构建代理，则代理平台 MCP 服务器允许该代理与您的代理平台资源安全地交互。这样，您的代理现在可以轻松调用[模型花园中的模型](https://console.cloud.google.com/agent-platform/model-garden)、下拉共享的[提示模板](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/prompts/prompt-templates)，甚至直接在您的项目中管理[笔记本](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/overview) - 所有这些都无需离开 IDE。

#### 更快实现价值

交付价值的速度是您最大的优势之一。但有时，将外部开发环境连接到云基础设施会迫使人们进行权衡。开发人员希望以最少的设置快速行动，而 IT 团队需要对数据访问进行严格的管理。

代理平台 MCP 服务器为您的外部代理提供单一标准化接口，因此您可以花更少的时间编写集成代码，而将更多的时间用于构建有用的功能。通过完全在 Google Cloud 的安全基础架构内运行，它为您提供了即用型端点，可以保护您的数据，同时加速您的开发。

两全其美：- 按照开放标准进行构建：您在 Google Cloud 之外构建的代理完全符合开放 [MCP 规范](https://modelcontextprotocol.io)。您的外部 IDE 和框架可以与您的云环境无缝交互，而无需将您锁定在专有的生态系统中。
- 集中发现：使用代理平台中的 [代理注册表](https://docs.cloud.google.com/agent-registry) 对您的资产进行编目。它充当您组织的集中库，因此您的团队可以安全地存储、搜索和管理其技能、工具和其他 AI 功能的整个库存。
- 轻松访问并具有安全性和治理：默认情况下，您的连接受到保护。 IT 团队可以利用本机 [Cloud IAM 拒绝策略](https://docs.cloud.google.com/mcp/control-mcp-use-iam#deny-all-mcp-tool-use) 确保外部开发人员框架仅与授权的 Google Cloud 资源交互。

#### 工作原理：连接的三个简单步骤

- 启用 API：当您在 Google Cloud 项目中启用 Gemini Enterprise Agent Platform API 时，Gemini Enterprise Agent Platform 远程 MCP 服务器会自动启用。

![https://storage.googleapis.com/gweb-cloudblog-publish/images/1_AP_Home.max-1100x1100.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/1_AP_Home.max-1100x1100.png)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/1_AP_Home.max-1100x1100.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/1_AP_Home.max-1100x1100.png)

2. 配置您的客户端：按照我们的[配置说明](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/use-agent-platform-mcp#configure-client)连接您的AI应用程序以指向远程服务器。

![https://storage.googleapis.com/gweb-cloudblog-publish/images/1_Vo4cvfF.max-900x900.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/1_Vo4cvfF.max-900x900.jpg)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/1_Vo4cvfF.max-900x900.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/1_Vo4cvfF.max-900x900.jpg)

3. 使用工具集：访问强大、可复制的[工具集端点](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/mcp#expandable-1) 列表，立即开始与代理平台资源进行交互。![https://storage.googleapis.com/gweb-cloudblog-publish/images/2_INFnkQs.max-900x900.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/2_INFnkQs.max-900x900.jpg)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/2_INFnkQs.max-900x900.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/2_INFnkQs.max-900x900.jpg)

#### 可用工具集：

| MCP 工具集 |  |  |
|:---|:---|:---|
|端点 |描述 |工具|
| /mcp/生成 |生成式人工智能工具 |核心一代特点|
| /mcp/预测 |预测工具|推理和原始预测 |
| /mcp/笔记本 | Colab 企业笔记本工具 |笔记本运行时和执行管理 |
| /mcp/端点 |端点管理工具|模型端点的生命周期管理 |
| /mcp/模型 |模型注册工具|模型上传、注册和部署 |
| /mcp/调整 |模型微调工具|微调作业管理和跟踪 |
| /mcp/评估 |质量评估工具|自动化模型质量和实例评估 |
| /mcp/提示 |快捷管理工具|快速的工程和版本控制工作流程 |

#### 今天开始

访问 [Agent Platform 页面](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/use-agent-platform-mcp) 将您最喜欢的代理框架连接到 Agent Platform MCP 服务器并立即开始构建。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
