<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:40:47+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/implementing-resilience-patterns-with-amazon-bedrock-and-llm-gateway/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 使用 Amazon Bedrock 和 LLM 网关实施弹性模式 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:40 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | Implementing resilience patterns with Amazon Bedrock and LLM gateway \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/implementing-resilience-patterns-with-amazon-bedrock-and-llm-gateway/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在本文中，您将学习在 AWS 上构建弹性生成 AI 应用程序的五种实用模式，从原生 Amazon Bedrock 功能发展到使用 LLM 网关的多模型编排。这些模式解决了现实世界的挑战，例如意外流量激增期间的配额耗尽，通过推理的地理分布最大化可用性，并帮助防止多租户环境中的嘈杂邻居问题。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 使用 

Amazon Bedrock 和 LLM 网关实施弹性模式

随着生成式 AI 工作负载从实验大规模转向生产，实施 [大语言模型 (LLM)](https://aws.amazon.com/what-is/large-language-model/) 推理的弹性模式至关重要。随着 LLM 支持的应用程序现已投入生产，组织需要各种方法来保持 LLM 推理的高度可用性、响应能力和成本效益。现有的弹性最佳实践（例如静态稳定性以及实施退避和重试）仍然适用。然而，生成式人工智能引入了新的考虑因素，包括模型可用性、快速变化的配额、跨多个提供商的代币限制以及与新发布的模型保持一致性。 [Amazon Bedrock](https://aws.amazon.com/bedrock/) 提供完全托管的基础模型，具有跨区域推理等内置弹性功能。

在设计生产推理时，通常有四个维度指导架构决策：可用性、响应时间、成本和吞吐量。可用性是指在模型、区域或提供商中断期间维持推理。响应时间涵盖了用户接收输出的速度，通常以第一个令​​牌的时间 (TTFT) 和最后一个令牌的时间 (TTLT) 来衡量。成本捕获每个令牌和每个请求的支出以及路由决策如何影响它。吞吐量反映了系统在负载下每秒可以承受多少并发请求和令牌。

这些维度是相互关联的。例如，跨区域路由可提高可用性和吞吐量，但可能会增加响应时间。本文中的模式主要关注可用性：通过故障转移、地理分布和配额隔离保持推理可操作。未来的帖子将深入探讨响应时间优化和成本感知路由。在本文中，您将学习在 AWS 上构建弹性生成 AI 应用程序的五种实用模式，从原生 Amazon Bedrock 功能发展到使用 LLM 网关的多模型编排。这些模式解决了现实世界的挑战，例如意外流量激增期间的配额耗尽，通过推理的地理分布最大化可用性，并帮助防止多租户环境中的嘈杂邻居问题。它们还通过智能请求路由支持成本优化，并让您可以根据您的具体要求灵活地使用多个模型和提供商。

这种爬行、行走、运行方法使您可以根据应用程序的成熟度和要求逐步采用这些模式。随附的 [GitHub 存储库](https://github.com/aws-samples/sample-resilient-llm-inference) 提供了演示每种模式的代码示例。

### 推断弹性模式的增量方法

您可以使用此[GitHub 存储库部分](https://github.com/aws-samples/sample-resilient-llm-inference?tab=readme-ov-file#testing-all-resilience-patterns) 中的代码示例和说明在您自己的环境中测试以下每个模式。

#### 先决条件

在开始演示之前，请通过完成[先决条件](https://github.com/aws-samples/sample-resilient-llm-inference?tab=readme-ov-file#prerequisites) 来验证您是否安装了适当的软件并正确配置了您的 AWS 账户。

注意：遵循本文中的模式将创建和使用会产生费用的 AWS 资源，包括 Amazon Bedrock 推理请求和 Amazon CloudWatch 日志。请参阅清理部分以避免测试后持续产生费用。

#### 模式 1：使用 

Amazon Bedrock 跨区域推理Amazon Bedrock 跨区域推理 (CRIS) 是一项本机功能，默认为弹性推理提供基础。您可以使用[跨区域推理配置文件](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html) 来提高吞吐量、降低在 AWS 区域内受到限制的可能性以及分配模型流量。 CRIS 消除了管理流量分配的手动工作，并提高了应用程序的可用性。它根据可用性、延迟和当前需求等实时因素，自动将请求从源区域路由到最佳目标区域。这可以解决高峰使用期间流量意外激增的问题，并降低服务配额影响推理的可能性。

CRIS 配置文件通常与美国或欧盟等特定地理区域内的商业区域相关联，为推理请求提供性能和延迟之间的适当平衡。此方法将聚合吞吐量提高到超出单区域配额，同时保持地理边界内的数据驻留。

![显示 Amazon Bedrock 跨区域推理的架构图。请求从源区域通过 API 端点流向 CRIS 推理路由器，后者路由到目标区域 1（活动，具有 API 端点和模型）或目标区域 2（备用，具有 API 端点和模型）。](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-19331-1.png)

Amazon Bedrock 跨区域推理

对于某些可以处理推理请求中较高延迟的用例，可以选择使用[全局跨区域推理配置文件](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html#:~:text=Global%20Claude%20Sonnet%204)。通过全局配置文件，请求可以跨多个商业区域路由，其中​​模型可用于全局推理，从而提供比标准跨区域推理配置文件更大的吞吐量。

例如，在我们的演示中，当使用跨区域推理配置文件向 Amazon Bedrock 发送 10 个请求时，命令输出显示 CRIS 如何在 3 个 AWS 区域自动分发模型推理：

|地区 |祈求|百分比 |
|:---|:---|:---|
|美国东部 1 | 1 | 10% |
|美国东2 | 7 | 70% |
|美国西2 | 2 | 20% |Amazon Bedrock 跨区域推理在三个 AWS 区域分发 10 个请求

#### 模式 2：使用多个 

AWS 账户

虽然 CRIS 使 AWS 账户内的吞吐量成倍增加，但您可以从额外的规模和隔离策略中受益。 AWS 账户分片将请求分配到多个 AWS 账户，每个账户都有独立的配额和 CRIS 配置文件。

帐户分片创建了自然的[故障隔离边界](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html)，其中一个帐户中的问题不会影响其他帐户，这对于需要在工作负载之间严格隔离的多团队和多租户架构特别有价值。

![显示使用 Amazon Bedrock 跨区域推理的 AWS 账户分片的架构图。 LLM 消费者生态系统（用户、代理、应用程序）连接到三个独立的 AWS 账户（A、B 和 C），每个账户都包含具有 Amazon Bedrock CRIS 的区域 A。](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-19331-2.png)

使用 Amazon Bedrock 跨区域推理进行 AWS 账户分片

运行帐户分片演示时，我们使用跨区域推理配置文件向两个配置的 AWS 帐户中的每一个发送 10 个请求。输出显示每个账户如何独立地跨 AWS 区域分配推理：

|帐户 1 |  |  |
|:---|:---|:---|
|地区 |祈求|百分比 |
|美国东2 | 7 | 70% |
|美国西2 | 3 | 30% |

|帐户 2 |  |  |
|:---|:---|:---|
|地区 |祈求|百分比 |
|美国东部 1 | 2 | 20% |
|美国东2 | 3 | 30% |
|美国西2 | 5 | 50% |

两个 AWS 账户通过 CRIS 独立跨区域分配请求

#### 使用 

LLM 网关对于复杂的生产场景，LLM 网关提供的路由、故障转移和治理功能超出了直接 API 调用所能提供的功能。网关充当您的应用程序和 LLM 提供商之间的智能代理，提供统一的抽象层，因此您可以通过单个 API 接口访问不同供应商的多个模型。这种标准化简化了集成，同时嵌入了负责任的 AI 防护、审核日志记录、自动重试和回退逻辑以及配额管理等功能，以及许多其他功能，帮助您的应用程序保持弹性，即使在个别模型不可用时也是如此。

![显示 LLM 网关跨 AWS 账户和外部提供商编排请求的架构图。 LLM 消费者生态系统连接到账户 A 区域 A 中包含 Lite LLM 和 Amazon Bedrock 的 LLM 网关，该网关路由到多个 AWS 账户（B、C、D）和外部 LLM 提供商（Anthropic、OpenAI、Cohere、Vertex AI）。](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-19331-3.png)

LLM 网关跨 AWS 账户和外部提供商编排请求

该网关支持跨多个模型和帐户的智能请求路由和负载平衡，最大限度地提高吞吐量，同时通过每个消费者隔离实施速率限制和配额管理。这有助于防止多租户环境中的噪音邻居问题，同时通过使用情况分析提供全面的成本跟踪和优化。集中的可观测性和监控使您能够全面了解 LLM 使用模式，并获得针对每个应用程序的详细见解，帮助识别优化机会并快速解决问题。如今有许多开源和商业 LLM 网关可供使用。对于我们的演示，我们使用 [LiteLLM](https://www.litellm.ai/) 作为本地运行的轻量级开源选项来演示这些模式。大规模部署时，[适用于多提供商生成 AI 网关的 AWS 解决方案](https://aws.amazon.com/solutions/guidance/multi-provider-generative-ai-gateway-on-aws/) 提供了参考实施和架构，该参考实现和架构也使用 LiteLLM，但添加了企业功能，包括在 [Amazon Elastic Container Service](https://aws.amazon.com/pm/ecs/) (Amazon ECS) 或 [Amazon Elastic Kubernetes Service](https://aws.amazon.com/pm/eks/) (Amazon EKS) 上进行容器化部署、自动扩展、[AWS WAF](https://aws.amazon.com/waf/) 保护、秘密管理以及通过以下方式进行全面观察： [Amazon CloudWatch](https://aws.amazon.com/cloudwatch/)。

#### 模式 3：模型回退

即使主要模型达到速率限制或遇到服务中断，模型之间的自动故障转移也可支持更高的可用性。此模式旨在自动在客户定义的主模型和辅助模型之间路由请求。如果您的后备策略侧重于优化质量和成本而不是配额耗尽，[Amazon Bedrock 智能提示路由](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-routing.html) 提供了一个本机选项。它会为每个请求动态选择最合适的模型，而不需要外部网关。如果对主要模型的调用失败，网关会自动使用辅助模型重试请求，即使在流量意外高峰期间也支持高可用性。回退策略还结合了成本优化和性能考虑，例如，限制成本较高的模型，并在适当时回退到更具成本效益的替代方案。

![显示具有速率限制的主要模型和更高容量的回退模型的回退演示的架构图。客户端向 Lite LLM 发送 10 个请求，后者将 3 个请求路由到 Amazon Bedrock 中的主模型（具有 3 RPM 限制）和 7 个请求到后备模型（具有 25 RPM 容量）](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-19331-4.png)

使用速率受限的主模型和更高容量的后备模型进行后备演示在我们的演示中，LiteLLM 配置定义了一个主模型，其速率限制为每分钟 3 个请求 (RPM)，以及一个容量更高的备用模型，为 25 RPM。当客户端通过网关发送 10 个并发请求时，前三个请求将路由到 Amazon Bedrock 中的主要模型。当主模型达到其速率限制时，LiteLLM 会自动将剩余的 7 个请求转移到后备模型。这 10 个请求成功完成，无需手动干预或应用程序级重试逻辑。

演示输出证实了该模式的有效性，显示出高可靠性，尽管主模型存在速率限制，但 10 个请求仍成功完成。该分布表明，在达到其配额之前，主模型恰好处理了 3 个请求。其余 7 个请求故障转移到回退模型，展示了网关通过智能路由维持服务可用性的能力。

![回退演示结果的屏幕截图显示：请求总数：10，成功：10，失败：0，使用的主要模型：3，触发回退：7。模型使用情况分布显示 FALLBACK 模型处理了 7 个请求 (70.0%)，PRIMARY 模型处理了 3 个请求 (30.0%)](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-19331-5.png)

显示模型分布的后备演示输出

#### 模式 4：跨模型负载均衡

负载均衡模式将请求分布在多个模型实例之间，以优化资源利用率并帮助防止出现瓶颈。这种方法不仅最大限度地提高了利用率，还允许您根据需要添加或删除模型实例来快速扩展。例如，在完全部署之前评估新模型时，您可以实施加权路由或 A/B 测试策略，仅将一小部分请求定向到新模型，而大多数请求继续使用经过验证的模型。![架构图显示了具有回退溢出的跨主要模型的负载平衡。客户端向 Lite LLM 发送 10 个请求，后者向 Amazon Bedrock 中的主模型 1 和主模型 2（每个具有 3 RPM 限制）各分配 3 个请求，并向后备模型（具有 25 RPM 容量）分配 4 个溢出请求。](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-19331-6.png)

具有回退溢出功能的跨主要模型的负载平衡

在我们的负载平衡演示中，网关使用随机策略成功地将 10 个并发请求分配到两个模型。负载均衡器最初将 3 个请求路由到两个配置的主要模型中的每一个，当达到其速率限制时，其余 4 个请求将自动重定向到回退模型。结果是 100% 的成功率，展示了负载平衡如何与后备策略结合使用。

![负载均衡结果的屏幕截图显示：请求总数：10，成功：10，失败：0。模型分布显示三个模型，每个模型处理请求：claude-3-5-sonnet（4 个请求，40.0%）、claude-3-7-sonnet（3 个请求，30.0%）和 claude-sonnet-4（3 个请求，30.0%）。](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-19331-7.png)

负载平衡演示输出

#### 模式 5：多租户配额隔离

多租户配额隔离模式创建逻辑隔离的环境，配备自己的配额和速率限制，以管理多租户环境中的请求。通过为每个消费者实施独立的速率限制桶，这种模式有助于防止“吵闹的邻居”挑战，其中一个消费者的请求会对其他消费者的性能产生负面影响。无论其他租户的使用模式如何，每个租户都会收到专用配额，支持公平的资源分配并保持消费者之间一致的服务质量。

![显示多租户配额隔离的架构图，每个消费者具有独立的速率限制。三个使用者（A 为 3 RPM、B 为 10 RPM、C 为 10 RPM）各自向 Lite LLM 发送 5 个请求，Lite LLM 在路由到 Amazon Bedrock 模型之前强制实施单独的配额。消费者 A 显示 3 个成功的请求和 2 个被拒绝的请求。](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-19331-8.png)多租户配额隔离，每个消费者具有独立的速率限制

该模式非常适合多个应用程序共享模型资源，同时需要可预测的性能和隔离置信度的环境。

在我们的演示中，具有不同速率限制的三个消费者尝试同时访问同一模型。消费者 A 配置为每分钟仅允许 3 个请求 (RPM)，而消费者 B 和 C 各有 10 个 RPM。当三个消费者各发送 5 个并发请求时，网关会强制执行单独的配额。消费者 A 遇到速率限制，只有 3 个请求成功，2 个请求被拒绝。消费者 B 和消费者 C 处理了所有 5 个请求，成功率达到 100%。

|配额隔离分析|  |  |  |  |  |  |
|:---|:---|:---|:---|:---|:---|:---|
|消费者 |类型 |成功率|总计 |成功|失败 |价格有限 |
|一个 |吵闹 | 60% | 5 | 3 | 2 | 2 |
|乙|正常 | 100% | 5 | 5 | 0 | 0 |
| C |正常 | 100% | 5 | 5 | 0 | 0 |

多租户隔离演示输出

#### 清理

警告：以下清理步骤将永久删除 CloudWatch 日志。如果您需要保留日志用于审核或分析目的，请在继续清理之前将其导出。

为了避免您的帐户持续产生费用，请[完成这些步骤](https://github.com/aws-samples/sample-resilient-llm-inference?tab=readme-ov-file#cleanup) 以停止网关并删除 CloudWatch 日志。

#### 重要注意事项

上述指南对工作负载要求、数据安全和合规义务以及性能需求做出了某些假设。与大多数事情一样，“我什么时候应该使用这些模式？”的答案是“这取决于！”。以下是应用这些模式有意义的一些用例。

##### 适用场景和用例

高可用性要求：当您的应用程序无法容忍停机时，多个模型提供自动故障转移。如果您的主要模型达到速率限制或遇到中断，请求将路由到备份模型，从而保持 100% 的可用性。

超出单一模型配额的扩展：单个模型具有吞吐量限制。使用多个模型（甚至不同帐户/区域中的相同模型类型）会成倍增加您的总可用容量。这对于请求量可能超过单一模型配额的大容量应用程序至关重要。多租户隔离：在软件即服务 (SaaS) 应用程序中，不同的客户可以使用不同的模型或模型实例，有助于防止一个客户的使用影响其他客户。

开发与生产：用于测试（更便宜、更快的模型）和生产（更高质量的模型）的单独模型配置，无需更改代码。

### 结论

这篇文章介绍了弹性 LLM 推理的多种模式，从 Amazon Bedrock 本机跨区域推理开始，到需要实施 LLM 网关的更复杂模式结束。使用这些策略，您可以提高生成式 AI 支持的工作负载的弹性，并获得对模型可用性和故障转移策略的精细控制，包括对特定消费者和应用程序的专用控制。

我们邀请您使用[附带的 GitHub 存储库](https://github.com/aws-samples/sample-resilient-llm-inference) 详细试验这些模式，其中提供了用于测试每种模式的代码示例和分步说明。如需生产就绪的生成式 LLM 网关的全面参考实施，请探索 [适用于多提供商生成式 AI 网关的 AWS 解决方案](https://aws.amazon.com/solutions/guidance/multi-provider-generative-ai-gateway-on-aws/)。

有关更多生成式 AI 架构模式和最佳实践，请访问 [AWS 人工智能博客](https://aws.amazon.com/blogs/machine-learning/)。

如果您有任何意见或问题，请将其留在评论部分。

标签：生成式人工智能、Amazon Bedrock、弹性、架构

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
