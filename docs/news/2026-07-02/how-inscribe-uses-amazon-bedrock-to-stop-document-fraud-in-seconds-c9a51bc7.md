<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T01:53:16+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/how-inscribe-uses-amazon-bedrock-to-stop-document-fraud-in-seconds/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# Inscribe 如何使用 Amazon Bedrock 在几秒钟内阻止文档欺诈 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 01:53 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | How Inscribe uses Amazon Bedrock to stop document fraud in seconds \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/how-inscribe-uses-amazon-bedrock-to-stop-document-fraud-in-seconds/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在本文中，您将了解 Inscribe 如何使用 Amazon Bedrock 开发代理 AI 系统，以专业欺诈分析师的方式对文档进行推理。借助这一新的代理 AI 系统，Inscribe 现在可以在 90 秒内检测到被篡改、伪造和 AI 生成的财务文档。这比传统的人工审核提高了 20 倍，同时保持了金融服务法规所要求的准确性和可解释性。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## Inscribe 如何使用 

Amazon Bedrock 在几秒钟内阻止文档欺诈

这篇文章是与 Inscribe 首席技术官兼联合创始人 Conor Burke 共同撰写的

目前，每 16 份文件中就有 1 份存在欺诈行为，从 2025 年 4 月到 2025 年 12 月，人工智能生成的伪造文件增长了 5 倍（[Inscribe 的 2026 年文件欺诈状况报告](https://www.inscribe.ai/reports/2026-document-fraud-report)）。对于每天处理数千份申请的金融机构来说，这种规模的欺骗造成了不可能的挑战。传统的人工审核每个申请需要 30 分钟，无法跟上不断增长的数量。更重要的是，手动流程很难检测现代欺诈工具所带来的不断变化的策略。仅靠速度是不够的。该解决方案还必须捕获复杂的伪造品、深度伪造品和协调的欺诈团伙，而人类审查员和基于规则的遗留系统从未设计过识别这些欺诈团伙。

[Inscribe](https://www.inscribe.ai/) 自 2017 年以来一直致力于为领先的[银行](https://www.inscribe.ai/industries/banks)、[贷方](https://www.inscribe.ai/industries/lenders) 和金融科技公司构建人工智能驱动的文档欺诈检测。在本文中，您将了解 Inscribe 如何使用 Amazon Bedrock 开发 [代理 AI](https://www.inscribe.ai/why-inscribe) 系统，该系统以专家欺诈分析师的方式跨文档进行推理。借助这一新的代理 AI 系统，Inscribe 现在可以在 90 秒内检测到被篡改、伪造和 AI 生成的财务文档。这比传统的人工审核提高了 20 倍，同时保持了金融服务法规所要求的准确性和可解释性。

[Amazon Bedrock](https://aws.amazon.com/bedrock/) 是一项完全托管的服务，通过单个 API 提供来自领先 AI 公司（例如 AI21 Labs、Anthropic、Cohere、Meta、Stability AI 和 Amazon）的高性能基础模型 (FM) 选择。它还提供了构建具有安全性、隐私性和负责任的 AI 的生成式 AI 应用程序所需的广泛功能。

### 挑战考虑一家中型银行的典型贷款申请。客户提交银行对账单、工资单、税务文件和身份证明。欺诈分析师必须验证每份文件的真实性、跨文件的交叉引用信息、检查是否存在操纵迹象，包括日益复杂的深度伪造和人工智能生成的伪造品，并研究申请人的雇主和地址。他们必须在完成所有这一切的同时保持快速周转，以避免将客户输给竞争对手。

此手动过程带来了三个复杂的挑战：

- 规模：随着申请量的增长，机构必须按比例雇用更多的分析师，从而在不提高检测准确性的情况下增加成本。
- 适应性：静态欺诈检测规则会错过复杂的方案，例如深度伪造、人工智能生成的虚假文档和协调的身份盗窃团伙。
- 一致性：不同的分析师对类似案例得出不同的结论，造成合规风险和公平性担忧。

财务风险是巨大的。一个漏掉的案件可能意味着数百万美元的直接损失、金融犯罪失败的监管风险以及更难以挽回的声誉后果。耗时的手动审核会使客户批准延迟数天，从而导致很高的放弃率。与此同时，欺诈者不断改变策略，从人工智能深度伪造和伪造文件转向合成身份欺诈，因为他们知道，过度劳累的分析师在每天处理数百个应用程序时可能会错过微妙的操纵信号。

### 解决方案：为什么代理人工智能能够捕捉到人工审核遗漏的内容

Inscribe 构建了一个与风险和承保团队合作的 [AI 解决方案](https://www.inscribe.ai/why-inscribe)。它可以自动执行常规文档分析，同时标记复杂案例以供人工审核，将深厚的领域专业知识与[分层检测技术](https://www.inscribe.ai/ai-risk-agents) 相结合，以发现手动审核团队和其他提供商遗漏的内容。将代理人工智能系统视为从头到尾工作的专家分析师。它需要一个目标，将其分解为多个步骤，使用多种工具，然后一直完成。基本的人工智能工具可以回答单个问题，而代理系统则协调专门的模型，在需要时调用外部 API，并将所有内容综合成最终决策。对于文档欺诈检测，这意味着 Inscribe 的系统不仅会标记可疑字段。它提交一份文档，通过正确的模型进行路由，运行并行取证检查，搜索网络以验证雇主详细信息，跨整个文档集交叉引用数据，并生成可审计的欺诈报告，无需人工干预，只需几秒钟即可完成该过程。

[基础模型](https://aws.amazon.com/what-is/foundation-models/) 擅长理解上下文、跨文档推理以及生成自然语言解释，这些功能对于欺诈分析至关重要。塑造 Inscribe 架构的关键洞察：没有一个模型能够同样适合每项任务。为每个步骤协调正确的模型，而不是将一个模型应用于所有事情，可以以更低的成本提供更好的结果。

### Amazon 

Bedrock 如何支持多模型欺诈检测

Amazon Bedrock 提供的广泛模型选择意味着 Inscribe 可以为每项任务选择正确的 FM，而无需管理单独的基础设施，从而将模型选择转变为配置选择而不是集成项目。

无服务器扩展可应对文档处理量的大幅波动，从安静的夜间时间到工作时间的高峰，而无需 Inscribe 提供专用的服务基础设施。

企业安全性和合规性满足金融服务所需的严格数据保护标准：加密涵盖传输中和静态的数据，AWS Identity and Access Management (IAM) 提供细粒度的访问控制。

模型版本控制和治理允许 Inscribe 在升级到生产环境之前在暂存环境中测试新模型版本，这对于保持一致的欺诈检测准确性至关重要。

### 将模型与任务相匹配以提高速度和成本效率

Inscribe 在 Amazon Bedrock 上评估了多个模型，测量性能、延迟和成本，以确定每个欺诈检测任务的正确模型。#### Anthropic Claude Haiku 4.5：在不减慢审核速度的情况下将成本降低 40%

与使用 Claude Sonnet 执行日常任务相比，您可以将推理成本降低约 40%，而无需牺牲速度。 Inscribe 使用 Claude Haiku 4.5 进行可在几秒钟内完成的大批量操作：文档解析、字段提取、初始分类和预筛选检查。 Haiku 4.5 的升级提高了准确性，同时降低了日常任务的成本。

#### Meta Llama 3.1 70B 和 Meta Llama 4：保持事务分析快速且经济高效

为了丰富交易和实体提取，Inscribe 使用 Meta Llama 模型。 Inscribe 工程经理 Ivo 解释了这一决定：

>

“我们在性能方面没有看到太大的差异。Llama 执行这些任务的质量与我们想要的不相上下，因此选择 Llama 使我们能够在不牺牲质量的情况下降低成本。价格在最终决定中肯定会发挥作用。”

这种务实的方法在性能与更昂贵的替代方案相匹配时使用 Llama，可以在大批量推理任务中显着节省成本。

#### Anthropic 

Claude Sonnet 4 和 4.5：捕获跨文档欺诈模式

Claude Sonnet 充当协调层，处理最复杂的任务：跨文档欺诈分析、多步骤推理工作流程、用于雇主验证的 Web 搜索集成以及自然语言生成可审计的欺诈报告。 Sonnet 的扩展上下文窗口使其能够保持对整个文档集的感知，识别单独分析文档时不可见的模式。

### Inscribe 如何扩展 

AWS 上的欺诈检测

Inscribe 的欺诈检测系统构建在 AWS 基础设施之上，旨在大规模提供速度、可靠性和合规性。其代理架构意味着系统协调专门的模型，决定下一步要分析的内容，在需要时调用外部 API，并将所有内容综合为最终决策，无需人工干预。![Inscribe AWS 上的欺诈检测架构，显示文档提取、基于队列的异步处理、文本提取、Amazon Bedrock 多模型管道、Amazon SageMaker AI 模型以及存储和可观察层](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-19301-1.png)

AWS 上的 Inscribe 欺诈检测架构

#### 文档摄取和存储

当贷款申请文件通过 Inscribe 的 Web 界面或 API 上传时，文件会存储在 [Amazon Simple Storage Service](https://aws.amazon.com/pm/serv-s3/) (Amazon S3) 中，这是一种行业领先的可扩展对象存储服务。 Web 应用程序通过 [Amazon CloudFront](https://aws.amazon.com/cloudfront/) 和 [Application Load Balancer](https://aws.amazon.com/elasticloadbalancing/application-load-balancer/) 提供服务，创建一个处理作业并将其在 [Amazon Simple Queue Service](https://aws.amazon.com/sqs/) (Amazon SQS) 中排队。文件立即排队等待处理，无需手动移交。

#### 异步处理

在 Amazon Elastic Compute Cloud (Amazon EC2) 上运行的 Celery 工作进程（分布式任务队列）从队列中提取作业。这种基于队列的架构可以无延迟地处理流量高峰。在工作时间内，更多的工人会自动扩大规模，而一夜之间，产能就会缩小以最大限度地降低成本。无论您处理十个还是一万个应用程序，系统都能提供一致的性能。

#### 文本提取

[Amazon Textract](https://aws.amazon.com/textract/) 提供基线光学字符识别 (OCR) 以及从 PDF 和图像中提取文本。 Inscribe 越来越多地将解析工作负载直接转移到 Amazon Bedrock 上的 FM，从而从复杂的财务文档中更准确地提取内容。

#### 多模型欺诈检测管道

Inscribe 提取文本后，文档按协调顺序流经 Amazon Bedrock 上的多个 FM。 Claude Haiku 执行快速初始解析和分类。 Meta Llama 模型处理交易数据并提取实体。 Claude Sonnet 进行跨文档分析，协调雇主验证和地址验证的网络搜索，并生成最终的欺诈评估。每个模型都处理它最擅长的事情，将您的审核时间控制在几秒钟内。#### Amazon SageMaker AI 上的专有欺诈检测模型

在进行基础模型分析的同时，Inscribe 还运行 [Amazon SageMaker AI](https://aws.amazon.com/sagemaker/ai/) 上托管的专有机器学习 (ML) 模型。这些模型完全在内部构建，并每年在数百万个应用程序 Inscribe 流程上进行训练，可检测通用LLM（基础模型的子集）遗漏的信号：用于识别经过数字更改的图像的像素级取证分析、将文档与已知欺诈模板库进行匹配的网络模式检测，以及针对受操纵的签名或布局的视觉异常检测。

SageMaker AI 提供用于大规模部署这些专用模型的托管基础​​架构，并具有用于模型部署、自动扩展和性能监控的内置功能。 Inscribe 的工程团队可以专注于完善欺诈检测算法，而不是管理基础设施，这一点尤其重要，因为金融犯罪策略的发展速度快于静态规则系统的适应速度。

#### 结果存储、缓存和可观测性

Inscribe 将中间推理跟踪和最终欺诈报告存储在 Amazon Relational Database Service (Amazon RDS) 中，为合规团队提供可靠的审计跟踪，同时支持持续的模型改进。 [Amazon ElastiCache for Valkey](https://aws.amazon.com/elasticache/what-is-valkey/) 缓存短期数据（例如 Webhook 令牌）、实施速率限制并管理 Celery 任务元数据。 [Amazon MemoryDB](https://aws.amazon.com/memorydb/) 支持矢量数据库层，其中使用 K 最近邻 (KNN) 搜索来存储和查询事务嵌入，这是一种在数据集中查找最相似记录的技术，为支持模型提供支持。

[Amazon CloudWatch](https://aws.amazon.com/cloudwatch/) 跟踪模型性能指标，包括推理延迟、错误率、令牌使用情况和每个请求的成本。这种可观测性对于检测模型漂移、预测准确性的变化至关重要，这些变化表明需要重新训练或模型更新。

### 结果：使用 Inscribe 可以实现什么由 

Amazon Bedrock 提供支持的代理欺诈检测的转变为 Inscribe 的客户群带来了可衡量的结果。以下客户示例展示了组织使用 Inscribe 欺诈检测解决方案所取得的成果。

|客户|防止欺诈损失|缩短审核时间 |主要成果 |
|:---|:---|:---|:---|
| BHG金融|数百万人被阻止|减少 90% 以上 |伴随您成长的系统化工作流程 |
| Logix 联邦信用合作社 | 8 个月内 300 万美元以上 |减少高达 99% | AI伪造检测|
| BCU |阻止了 560 万美元 |处理 10 至 10,000 个应用程序的数量 |欺诈团伙检测 |

#### BHG Financial：从手动到系统

[BHG Financial](https://www.inscribe.ai/customers/bhg-financial) 是一家领先的金融服务公司，其手动文档审核流程不一致且无法跟上不断增长的申请量。部署 Inscribe 后，BHG Financial 的手动审核时间减少了 90% 以上，并避免了数百万美元的潜在欺诈损失。欺诈检测从主观的、依赖于分析师的流程转变为透明的工作流程，团队可以依赖该工作流程做出每项决策，该工作流程随着应用程序数量的增长而增加，而无需按比例增加人员数量。

>

“Inscribe 是我们的转折点。它将欺诈检测从手动、主观的过程转变为我们每次都可以信任的可扩展、透明的系统。” — Michael Coomer，BHG Financial 欺诈管理总监

#### Logix 联邦信用合作社：八个月内节省了 300 万美元的欺诈费用

[Logix 联邦信用合作社](https://www.inscribe.ai/customers/logix-federal-credit-union) 每年处理数百起贷款欺诈案件。他们的调查人员需要能够发现手动文件检查无法发现的东西的工具，特别是人工智能生成的伪造文件和合成文件。在部署 Inscribe 后的八个月内，Logix 避免了超过 300 万美元的潜在贷款欺诈损失。该团队还避免了耗时的手动交叉引用雇主记录和样本文件，这种方式以前会减慢每个案件的速度。

>“我们于去年 4 月下旬开始使用 Inscribe。在短短八个月内，我们发现潜在的贷款欺诈节省超过 300 万美元，并且节省了无数的身份盗窃费用。” — Matt Overin，Logix 联邦信用合作社欺诈风险管理

#### BCU：在损失增加之前阻止欺诈行为

[BCU](https://www.inscribe.ai/customers/bcu) 是一家领先的信用合作社，面临着更复杂的挑战：协调一致的欺诈团伙提交了多个人工审核无法发现的申请。 Inscribe 为 BCU 的帐户保护团队提供了尽早发现这些方案所需的跨应用程序模式检测。结果是避免了 560 万美元的欺诈损失，团队能够在不按比例增加人员的情况下处理不断增长的审核量。

>

“过去几年，我们采取的一些最大规模的预防措施都直接来自 Inscribe 检测。我们正在谈论的是避免了数百万美元的损失，这对我们阻止欺诈的速度和信心产生了显着的影响。” — Nickie Christianson，BCU 帐户保护团队高级经理

### 结论和后续步骤

Inscribe 的结果表明，当代理人工智能应用于文档欺诈检测工作流程时，一切将变得可能。不仅审查速度更快，而且系统能够推理、适应和捕获首次训练时不存在的欺诈策略。随着 Amazon Bedrock 上的基础模型不断发展，代理方法意味着 Inscribe 可以采用新功能，而无需重建核心基础设施，从而使您的机构领先于欺诈者。

Amazon Bedrock 上的多模型架构也为面临类似挑战的其他企业提供了模板。在 Amazon Bedrock 的统一 API 和无服务器扩展的支持下，战略模型选择可帮助您在复杂的 AI 工作流程中平衡质量、速度和成本。

首先，请探索以下资源：- 要构建您自己的多模型欺诈检测解决方案，请[探索 Amazon Bedrock 和可用的基础模型](https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards.html)。
- 要大规模部署自定义 ML 模型，[Amazon SageMaker AI 入门](https://docs.aws.amazon.com/sagemaker/latest/dg/canvas-custom-models.html)。
- 要了解 Inscribe 如何帮助您的机构防止文件欺诈，请访问 [Inscribe AI](https://www.inscribe.ai/)。
- 要了解 Anthropic Claude 和 Meta Llama 模型在 Amazon Bedrock 上的执行情况，请阅读[模型文档](https://aws.amazon.com/bedrock/anthropic/)。
- 要了解有关代理 AI 系统的更多信息，请访问 [AWS Agentic AI](https://aws.amazon.com/ai/agentic-ai/) 页面并发现可帮助您开发企业级代理 AI 解决方案的服务和功能。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
