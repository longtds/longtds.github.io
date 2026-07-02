<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T01:46:54+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/simplify-model-selection-in-amazon-bedrock-with-the-open-source-model-profiler/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 使用开源 Model Profiler 简化 Amazon Bedrock 中的模型选择 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 01:46 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | Simplify model selection in Amazon Bedrock with the open source Model Profiler \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/simplify-model-selection-in-amazon-bedrock-with-the-open-source-model-profiler/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

Amazon Bedrock Model Profiler 是一款开源工具，可将来自多个 AWS API 和外部源的模型元数据聚合到单个可搜索界面中。在这篇文章中，您将在五分钟内了解 Model Profiler 提供的功能、它支持的实际场景以及如何将其部署到您自己的环境中。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 使用开源 Model Profiler 简化 

Amazon Bedrock 中的模型选择

生成式 AI 在各行业的采用正在加速，[Amazon Bedrock](https://aws.amazon.com/bedrock/) 提供了用于构建生产就绪的 AI 应用程序的托管服务。通过访问 Anthropic、OpenAI、Meta、Mistral AI、Cohere 和 Amazon 等提供商的 100 多个基础模型，团队可以灵活地为每个用例选择正确的模型。

但选择伴随着复杂性。在功能、定价、区域可用性、上下文窗口限制和吞吐量方面比较模型并不简单。这些信息分散在控制台页面、文档和区域 API 调用中。对于评估新工作负载模型、优化成本和性能或从其他人工智能系统迁移的组织来说，这种分散的发现过程会减慢实验速度并延迟生产决策。

[Amazon Bedrock Model Profiler](https://github.com/aws-samples/sample-bedrock-migration-and-modernization-tools/tree/main/bedrock-model-profiler) 弥补了这一差距。该开源工具将来自多个 AWS API 和外部源的模型元数据聚合到一个可搜索的界面中。借助高级过滤、并排比较和详细模型卡，团队可以探索完整的 Amazon Bedrock 目录，并通过简化跨各种文档和模型卡的手动搜索工作来做出明智的、数据驱动的决策。

在这篇文章中，您将在五分钟内了解 Model Profiler 提供的功能、它支持的实际场景以及如何将其部署到您自己的环境中。

### 解决方案概述

Model Profiler 是一款 Web 应用程序，可让您在一个位置浏览、筛选和比较 Amazon Bedrock 上可用的每个基础模型。您无需浏览多个控制台页面和文档站点，而是获得一个包含模型卡、并排比较、区域可用性地图和每日更新的定价细目的界面。

![模型分析器显示模型资源管理器界面](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-20648-1.png)

显示模型浏览器界面的模型分析器在界面后面，一个完全自动化的无服务器管道收集和处理来自七个不同来源的数据：五个 AWS API 和两个公共 URL。这可以保持目录准确，无需人工干预。

|来源 |类型 |授权 |收集的数据|
|:---|:---|:---|:---|
|亚马逊基岩ListFoundationModels API |亚马逊AWS官方博客IAM (Sigv4) | 33 个地区的型号规格、功能、模式和区域可用性
| AWS 价目表 API |亚马逊AWS官方博客IAM (Sigv4) |跨三个服务代码的按需定价、批量定价和预留定价 |
| AWS 服务配额 API |亚马逊AWS官方博客IAM (Sigv4) |每分钟令牌数 (TPM) 限制、每分钟请求数 (RPM) 配额和吞吐量限制 |
| Amazon Bedrock ListInferenceProfiles API | 亚马逊亚马逊AWS官方博客IAM (Sigv4) |跨区域推理配置和地理范围 |
|亚马逊基岩地幔 API |亚马逊AWS官方博客IAM (Sigv4) |跨地区地幔推断可用性 |
| LiteLLM 模型数据库 |公共网址 |无 |令牌规范，包括上下文窗口大小和最大输出令牌 |
| AWS 文档 |公共网址 |无 |模型生命周期状态（活跃、遗留、生命周期结束）|

在评估模型时，了解关键配额指标至关重要。每分钟令牌数 (TPM) 衡量每分钟可以处理的令牌数。将其视为吞吐量上限，其中 1,000 个令牌大约等于 750 个文本单词。每分钟请求数 (RPM) 限制您可以进行的 API 调用数量，无论大小如何。这两个配额因型号和区域而异。

![Model Profiler 数据管道的架构图](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-20648-2.png)

Model Profiler 数据管道的架构图

Model Profiler 运行由 AWS Step Functions 编排的全自动数据管道。 17 个 AWS Lambda 函数跨四个阶段处理数据，使用 Lambda S3 间缓存将每次执行的 API 调用从大约 480 次减少到 29 次。这表示缓存命中率为 97%。由 Amazon Bedrock 提供支持的自我修复代理系统可检测数据差距并自动应用安全配置修复。整个管道在 8 至 12 分钟内完成，每天早上 6 点（世界标准时间）运行。该计划可通过 AWS CloudFormation 模板中的 Amazon EventBridge 规则进行配置。您可以根据需要调整 cron 表达式以在不同的时间或频率运行。

#### 阶段 0：初始化

该管道首先动态发现哪些 AWS 区域当前支持 Amazon Bedrock。没有硬编码的区域列表，因此会自动选取新启动的区域。然后，它初始化执行上下文（S3 路径、缓存键）并同步后端和 React 前端之间的配置，确保双方在无需手动干预的情况下保持一致。

#### 第一阶段：并行收集

三个独立的收集分支同时运行。定价分支跨三个服务代码查询 AWS Price List API，并按提供商和模型聚合结果。模型分支分散到支持 Amazon Bedrock 的区域，在每个区域中调用 ListFoundationModels 并将结果重复数据删除到单个规范模型列表中。配额分支并行收集每分钟令牌数和每分钟请求服务限制。

#### 第 2 阶段：并行丰富

收集原始数据后，六个丰富步骤会同时运行，从缓存数据中读取而不是重新调用 API，将定价记录链接到模型，计算区域可用性，确定跨区域推理支持，获取上下文窗口大小，探测 Mantle API 并确定每个模型的生命周期状态。

#### 第三阶段：聚合和智能

最终的聚合器将丰富数据合并到两个生产就绪的 JSON 文件中：bedrock_models.json（包含规范、配额、可用性和生命周期状态的完整模型目录）和 bedrock_pricing.json（按提供商和模型组织的定价）。这两个文件都会复制到 Amazon Simple Storage Service (Amazon S3) 并通过 Amazon CloudFront 提供服务。

在发布之前，差距检测系统会扫描输出是否存在七种类型的数据质量问题。当差距超过配置的阈值时，自我修复代理会分析差距报告并自动应用安全修复。更改会进行版本控制和备份，不符合安全标准的建议会被记录下来以供手动审核，而不是自动应用。

#### 部署选项

该解决方案提供两种部署选项。本地模式完全使用您现有的 AWS 凭证在您的计算机上运行。运行数据收集器，启动前端，然后开始通过对 Amazon Bedrock 和定价 API 的读取访问权限进行探索。不需要云基础设施。

AWS 部署提供了完全无服务器架构，并具有自动每日数据刷新功能。 AWS Step Functions 工作流程编排 AWS Lambda 函数，这些函数每天早上 6 点（世界标准时间）收集新数据，将结果存储在 Amazon S3 中并通过 Amazon CloudFront 提供服务。本地收集器导入与 Lambda 代码相同的转换函数，无论您在本地还是在生产中运行，都保持相同的输出。

### 主要特点

模型分析器提供了四个核心功能，可简化模型选择：从发现和比较到区域规划和跟踪候选名单。

#### 模型浏览器

模型资源管理器是您发现 Amazon Bedrock 模型的起点。在可搜索、可过滤的界面中浏览 120 多个基础模型。您可以按提供商（Anthropic、Meta、Amazon、Mistral AI、Cohere 和其他 14 个）、视觉、代码生成、函数调用或嵌入等功能以及输入和输出模式来缩小结果范围。模态描述了模型可以处理的数据类型：纯文本模型处理书面内容，而多模态模型可能接受文本和图像作为输入，并生成文本、图像或两者作为输出。区域过滤器仅显示目标区域中可用的模型，而状态过滤器可让您专注于活动模型或包含旧选项。

![模型资源管理器界面显示过滤器选项和模型卡](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-20648-3.png)

模型资源管理器界面显示过滤器选项和模型卡

消耗选项过滤器可让您根据模型的使用方式来优化结果。 In Region（区域内）以按令牌定价的方式在特定 AWS 区域中提供按需推理。跨区域推理服务 (CRIS) 跨区域路由请求以获得更高的吞吐量。以较低的成本异步批量处理大量数据，并将结果传送到 Amazon S3。 Mantle 为托管推理端点提供专用容量和自定义配置。资源管理器支持两种查看模式。卡片视图提供视觉浏览，关键规格一目了然。表格视图可以对多种模型进行密集比较。全文搜索适用于型号名称、描述和提供商信息。

每个模型都有一个综合的详细视图，整合了可用信息：技术规范（模式、上下文窗口、推理类型）、按区域和消费类型划分的定价细目、具有跨区域推理详细信息的区域可用性、每个区域的服务配额（TPM 和 RPM 限制）以及官方文档和提供商信息的链接。

![显示技术规格信息的型号卡](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-20648-4.png)

显示技术规格信息的型号卡

#### 型号比较

一旦确定了候选模型，比较视图就可以让您在每个重要的维度上分析它们。

![模型比较视图并排显示四个模型，并带有概述和可用性选项卡](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-20648-5.png)

模型比较视图并排显示四个模型，并带有概述和可用性选项卡

在四个维度上同时比较多达 25 个模型。定价涵盖跨区域的输入和输出代币成本，具有按需、批量和预配置级别。区域可用性显示每个模型可用的位置的地图，包括跨区域推理支持。规范包括上下文窗口大小、最大输出令牌和支持的功能。功能矩阵显示了每个模型并排支持的内容。

Amazon Bedrock 提供多种定价选项来匹配不同的工作负载模式。按需层包括标准、灵活和优先选项，按代币定价且无需承诺。对于 24 小时内处理的非时间敏感型作业，批量定价可提供 30-50% 的折扣，具体取决于型号和方式。预留层以固定的小时费率提供专用容量，以应对持续的大容量工作负载。有关按型号划分的详细定价，请参阅 [Amazon Bedrock 定价](https://aws.amazon.com/bedrock/pricing/) 页面。

#### 区域可用性矩阵对于规划多区域部署的团队，区域可用性视图提供了跨所有 33 个支持 

Amazon Bedrock 的区域的全面的按区域模型矩阵。区域按地理区域（NAMER、EMEA、APAC、LATAM）分组，每个单元格显示模型在该区域的可用方式：按需（区域内）、跨区域推理 (CRIS) 或 Mantle。

您可以按可用性类型过滤矩阵，以快速回答“欧洲哪些型号支持 CRIS？”等问题。或“ap-southeast-2 中有哪些内容可供点播？”展开模型行可显示推理配置文件 ID、CRIS 源区域和地理范围。该矩阵还显示模型生命周期状态（活动、遗留或生命周期结束），因此您可以识别即将弃用的模型并提前计划迁移。对于跨多个地区运营的组织来说，此视图取代了原本需要数十个单独的 API 调用和手动交叉引用生命周期文档的视图。

![区域可用性矩阵显示每个区域的模型可用性，并用颜色编码的单元格指示模型状态](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-20648-6.png)

区域可用性矩阵显示每个区域的模型可用性，并用颜色编码的单元格指示模型状态

#### 收藏夹

当您探索模型时，您可以为模型加注星标，将其添加到您的收藏夹列表中，这是一个在浏览器会话中持续存在的个人候选列表。 “收藏夹”选项卡提供与主浏览器相同的过滤、排序和详细信息视图，范围仅限于您保存的模型。这对于在评估期间跟踪一组工作候选模型非常有用，或者对于快速访问团队最常使用的模型非常有用。

### 用例

让我们探讨不同的团队如何根据其独特的需求进行模型选择。以下场景以虚构组织为特色。他们使用真实的 AWS 定价和配额数据以及实际的工作负载假设来展示解决方案的功能。

#### 在欧洲地区选择符合合规性的模型Octank Financial Services 需要构建一个人工智能驱动的文档分析系统以实现监管合规性。该团队需要具有视觉功能的模型来处理扫描的文档，但操作必须仅在欧盟地区进行，以满足数据驻留要求。由于 Amazon Bedrock 上有数十种多模式模型，且定价因地区而异，该团队估计需要 6 到 8 小时的手动研究才能选出候选者。

使用模型分析器，团队按“愿景”能力和欧盟地区进行筛选，以立即查看符合条件的模型。他们使用区域可用性矩阵来确认 eu-west-1 和 eu-central-1 中的按需可用性，然后并排比较定价以找到最具成本效益的选项。服务配额确认吞吐量将满足他们预计的每日 50,000 份文档审查。

结果：模型评估从预计的 8 小时缩短到 25 分钟。该团队还发现，他们的首选模型在 eu-west-1 中比 eu-central-1 便宜 18%，并且发现了一种具有更大上下文窗口的新模型，可以减轻在多个调用之间分割长监管文档的需要。

#### 从第三方 

AI 提供商迁移

Octank Health 运营着一个基于第三方 AI 提供商构建的临床文档助理，需要迁移到 Amazon Bedrock 以实现更严格的 AWS 集成和成本控制。他们的要求很具体：128K 代币或更多的上下文窗口、低延迟以及至少三个美国区域的可用性以实现冗余。将当前提供商的功能手动映射到不同区域的 Amazon Bedrock 目录需要跨多个文档源进行广泛的研究。

该团队使用功能过滤器来查找符合其要求的模型，然后打开比较视图来评估候选者的上下文窗口、输出限制和定价。区域可用性视图确认了哪些模型支持美国范围内的跨区域推理，从而使它们无需更改应用程序即可自动进行故障转移。生命周期状态标志帮助他们避免模型接近遗留状态。评估在 45 分钟内完成。该团队选择了一个具有 200K 上下文窗口的模型（比之前的 128K 限制显着升级），每个代币的成本降低了 15%。跨区域推理可用性检查有助于防止他们选择没有跨区域支持的模型，否则需要重新构建其故障转移策略。

#### 多区域部署：规划全球扩张

Octank Media 正在将其人工智能驱动的内容推荐引擎从美国扩展到欧洲和亚太地区。在采用架构之前，他们需要确认当前模型在目标区域的可用性，了解每个模型支持哪些消费选项，并验证服务配额是否可以处理预计的流量。

区域可用性矩阵为团队提供了跨所有 33 个区域的模型的单一视图，按区域内、CRIS 和 Mantle 进行细分。按亚太地区和欧洲、中东和非洲地区进行筛选，准确揭示了其模型的可用地点和方式。生命周期状态列确认该模型在目标区域中处于活动状态，并且不会即将弃用。跨区域的配额比较发现 ap-northeast-1 是一个潜在的瓶颈，需要在启动之前请求增加配额。

20分钟内完成多区域可行性分析。以前，相同的工作需要通过 AWS 命令​​行界面 (AWS CLI) 和交叉引用文档来查询各个区域。在生产前确定东京的配额限制有助于防止中断，并确认欧洲的 CRIS 可用性为流量高峰​​制定了可靠的后备策略。

### 先决条件

在部署 Model Profiler 之前，请确认您已做好以下准备。

对于本地部署：

- Python 3.11 或更高版本。
- Node.js 18 或更高版本。
- 配置了对以下服务的读取访问权限的 AWS 凭证：```
基岩：ListFoundationModels、基岩：ListInferenceProfiles 基岩地幔：* 定价：GetProducts、定价：DescribeServices 服务配额：ListServiceQuotas、服务配额：GetServiceQuota ec2：DescribeRegions
```对于 AWS 部署（附加要求）：

- 安装了 AWS 无服务器应用程序模型 (AWS SAM) CLI。
- 有权部署 CloudFormation 堆栈、Lambda 函数、S3 存储桶、Step Functions 和 CloudFront 发行版的 AWS 凭证。 AWS SAM 模板会自动创建必要的 IAM 策略，因此您只需要部署堆栈本身的权限。

### 部署演练

Model Profiler 提供两种部署路径。选择本地部署以在您自己的计算机上快速探索，或选择 AWS 无服务器部署以获得自动刷新的托管界面。

#### 选项 1：本地部署

在五分钟内即可在本地部署 Model Profiler，无需云基础设施。

##### 步骤 1：克隆存储库```
git clone https://github.com/aws-samples/bedrock-model-profiler.git cd bedrock-model-profiler
```#####第二步：设置Python环境```
python -m venv .venv source .venv/bin/activate # 在 Windows 上：.venv\Scripts\activate pip install -r local/requirements.txt
```##### 步骤 3：收集模型数据

使用您的 AWS 配置文件运行数据收集器。此查询跨 25 个区域的 API，通常在 1-2 分钟内完成。```
python -m local collect --profile your-aws-profile
```每个阶段完成后，您将看到进度输出：```
[1/8] 正在收集定价数据... 找到 9562 个定价产品 [2/8] 正在聚合定价数据... 聚合到 18 个提供商中 ... [8/8] 构建最终输出... 写入 data/bedrock_models.json 写入 data/bedrock_pricing.json 收集完成！时长：81.3 秒收集的模型：117
```##### 第四步：启动前端```
cd frontend npm install cp template.env .env npm run dev
```在浏览器中导航至 [http://localhost:5173](http://localhost:5173/)。应用程序直接从本地 data/ 目录加载数据。

#### 选项 2：

AWS 部署

部署具有自动每日刷新功能的完整无服务器解决方案。

##### 第 1 步：验证您的 

AWS 账户```
aws sts 获取调用者身份
```如果您有多个配置文件，请设置要使用的一个：```
export AWS_PROFILE=your-profile-name
```##### 步骤 2：部署后端堆栈

必须首先使用 AWS SAM 部署后端。这将创建 Lambda 函数、Step Functions 工作流程、S3 数据存储桶和 EventBridge 计划。```
cd infra sam build -t backend-template.yaml sam deploy --guided
```引导式部署会提示您输入堆栈名称、区域和参数。使用标准部署的默认值或根据需要进行自定义。

##### 步骤 3：部署前端和链接基础设施

一旦后端堆栈运行，安装脚本就会部署剩余的基础设施并将所有内容连接在一起。```
./setup-infrastructure.sh
```该脚本执行五个步骤：

- 验证后端堆栈是否存在并检索数据桶名称。
- 部署前端基础设施（S3 托管存储桶和 CloudFront 分发）。
- 使用 CloudFront ARN 更新后端堆栈，以便数据存储桶授予对 CDN 的读取访问权限。
- 如果在 frontend/.env 中配置了 Amazon Cognito 凭证，则可以选择部署分析堆栈。
- 构建 React 前端并将其上传到 S3。

完成后，您将收到一个可访问应用程序的 CloudFront URL。数据会在世界标准时间 (UTC) 每天早上 6 点自动刷新。如需其他帮助，请参阅存储库中的部署指南 (https://github.com/aws-samples/bedrock-model-profiler)(https://github.com/aws-samples/bedrock-model-profiler#troubleshooting) 或在 [https://github.com/aws-samples/bedrock-model-profiler/issues](https://github.com/aws-samples/bedrock-model-profiler/issues) 中提出问题

### 清理

如果您部署 AWS 基础设施用于评估目的，请在完成模型选择后删除资源，以避免持续产生费用。

随着时间的推移，保留未使用的基础设施可能会累积意外成本，特别是当您在多个区域或帐户中运行探查器进行测试时。此外，删除评估堆栈有助于维护干净的 AWS 环境，并有助于防止管理生产资源时出现混乱。

对于本地部署：删除克隆的存储库目录。未创建云资源。对于 AWS 部署：删除 CloudFormation 堆栈以删除所有资源：```
aws cloudformation delete-stack --stack-name bedrock-profiler
```这将删除 S3 存储桶、Lambda 函数、Step Functions 工作流程和 CloudFront 分配。

### 结论

在构建生成式人工智能应用程序时，选择正确的基础模型是一个重要的决定，并且不需要花费数天的手动研究。 Amazon Bedrock Model Profiler 将 120 多个模型的功能、定价和区域可用性整合到一个界面中，以便您的团队可以在几分钟内从问题转变为决策。

您可以在五分钟内在本地部署 Model Profiler，无需云基础设施。如果您更喜欢自动每日刷新和托管界面，无服务器 AWS 部署选项只需执行几个额外步骤。无论哪种方式，您都可以获得 Amazon Bedrock 目录的相同完整视图。

准备好开始了吗？在 [github.com/aws-samples/bedrock-model-profiler](https://github.com/aws-samples/bedrock-model-profiler) 克隆存储库，并在五分钟内部署到本地。探索 [Amazon Bedrock](https://aws.amazon.com/bedrock/) 并查看 [Amazon Bedrock 定价](https://aws.amazon.com/bedrock/pricing/) 以规划您的模型策略。该项目是在 MIT 无署名 (MIT-0) 许可证下开源的。欢迎错误报告、功能请求和拉取请求。

相关资源

- [亚马逊基岩用户指南](https://docs.aws.amazon.com/bedrock/latest/userguide/)。
- [亚马逊基岩定价](https://aws.amazon.com/bedrock/pricing/)。
- [Amazon Bedrock 基础模型](https://aws.amazon.com/bedrock/models/)。

重要提示：此存储库包含用于教育或开发目的的示例代码。在生产使用之前进行彻底的审查和测试。 AWS 服务和模型可用性因区域而异，并随着时间的推移而变化。有关当前定价信息，请参阅 [Amazon Bedrock 定价页面](https://aws.amazon.com/bedrock/pricing/)。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
