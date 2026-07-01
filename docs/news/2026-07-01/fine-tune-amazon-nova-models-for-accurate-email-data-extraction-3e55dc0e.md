<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:26:48+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/fine-tune-amazon-nova-models-for-accurate-email-data-extraction/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 微调 Amazon Nova 模型以准确提取电子邮件数据 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:26 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | Fine-tune Amazon Nova models for accurate email data extraction \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/fine-tune-amazon-nova-models-for-accurate-email-data-extraction/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在本文中，您将了解如何使用 Amazon SageMaker AI 微调 Amazon Nova 模型来解决这些特定问题，方法是教模型识别您的确切数据模式、区分相似字段并更高效地处理信息，实现高达 94.77% 的提取准确率，同时降低 50% 的成本。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 微调 

Amazon Nova 模型以准确提取电子邮件数据

作者还要感谢 Karan Bhandarkar、Sue Cha、Yash Shah 和 Nieves Garcia 为使这一举措成为可能所做的贡献。

如果您每天处理数百万封电子邮件，微调 Amazon Nova 模型可以帮助您自动执行准确的数据提取，同时降低成本和减少幻觉。 Parcel Perform 是面向全球电子商务企业的领先 AI 交付体验平台，在从各种电子邮件格式（从简单的通知到具有大量 JavaScript 元素的复杂 HTML 文档）中提取结构化信息时，就面临着这一具体挑战。

常见的挑战包括模型幻觉、相似数据类型（例如订单号和跟踪号）之间的混淆，以及处理 HTML 格式的电子邮件时过高的令牌成本。

在本文中，您将了解如何使用 Amazon SageMaker AI 微调 Amazon Nova 模型来解决这些特定问题，方法是教模型识别您的确切数据模式、区分相似字段并更高效地处理信息，实现高达 94.77% 的提取准确率，同时降低 50% 的成本。

### 合作

Parcel Perform 与 AWS GenAIIC 合作，在整个客户旅程中提供业务和技术咨询。从 Parcel Perform 的问题陈述开始，团队确定了一个项目范围，通过各种定制技术和参数优化来优化 Nova 模型。

这种协作允许同时改进多个指标：准确性、延迟和成本。 Parcel Perform 人工智能团队负责人 Le Vy 报告称，经过微调的 Nova Micro 模型在测试数据集上的提取准确率高达 94.77%，比基线提高了 16.6 个百分点。与 Parcel Perform 之前的型号相比，经过微调的 Nova Micro 将推理延迟降低了 30% 以上，成本减半，同时以更低的成本达到或超过了经过微调的 Nova Lite 模型。凭借这些成果，Parcel Perform 将该解决方案投入生产，以改善其电子商务物流运营。

### 解决方案概述您可以使用 

Amazon SageMaker AI 自定义模型微调来调整 Amazon Nova Lite 和 Amazon Nova Micro 模型，以便从电子商务电子邮件中提取专门的实体。该解决方案通过低秩适应 (LoRA) 使用监督微调 (SFT) 和参数高效微调 (PEFT)。借助 PEFT，您可以使用有限的训练数据有效地定制模型，同时保持计算效率。

您还可以使用 PEFT 将模型部署到 Amazon Bedrock 中，并通过按代币定价的按需推理来调用它。 Amazon Bedrock 提供灵活的部署选项：借助 PEFT，您可以使用 [按需推理](https://docs.aws.amazon.com/bedrock/latest/userguide/deploy-custom-model-on-demand.html) 进行部署，而全等级 SFT 支持通过 [Amazon Bedrock 上的预配置吞吐量](https://docs.aws.amazon.com/bedrock/latest/userguide/prov-throughput.html) 或 [SageMaker AI 终端节点](https://docs.aws.amazon.com/sagemaker/latest/dg/deploy-model.html) 进行部署。

自定义模型微调使用 [Amazon Nova Recipe](https://docs.aws.amazon.com/nova/latest/nova2-userguide/nova-model-recipes.html)，它们是 YAML 配置文件，向 Amazon SageMaker AI 提供有关如何运行模型自定义作业的详细信息，包括基本模型名称、训练超参数、优化设置和其他选项。下图展示了该解决方案的架构。

![绘图](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/10/ML-20559-1.png)

工作流程的工作原理如下：

- 以 Amazon Bedrock 对话格式准备训练数据，其中电子邮件内容作为输入，提取的实体作为输出。
- 将训练数据上传到 Amazon Simple Storage Service (Amazon S3)。
- 使用低阶适应 (LoRA) 配置在 SageMaker AI 中创建微调作业。
- 使用 Amazon Bedrock 和按需推理来部署微调模型。
- 运行推理以从新电子邮件中提取实体。

### 先决条件

您将需要以下内容来微调和部署 Nova 模型：- 具有适当权限的 AWS 账户：访问 AWS 服务和创建资源所需的。
- 访问 Amazon Bedrock 和 Amazon Nova 模型：必须在您选择的 AWS 区域中可用。
- IAM 服务角色：具有 Amazon Bedrock 模型自定义权限的 AWS Identity and Access Management (IAM) 角色。
- S3 存储桶：用于存储训练数据和输出工件。
- JSONL 格式的训练数据：遵循数据格式和准备指南。
- 足够的服务配额：为您在 SageMaker AI Training 中选择的实例类型和大小建立足够的配额。

有关创建服务角色的说明，请参阅[创建模型定制的服务角色](https://docs.aws.amazon.com/bedrock/latest/userguide/model-customization-iam-role.html)。

### 准备训练数据

您的训练数据必须遵循 Amazon Bedrock 对话架构格式。每个示例都包含作为用户输入的电子邮件内容和作为助理响应的提取实体。

这是所需格式的简化示例：```
{ "schemaVersion": "bedrock-conversation-2024", "system": [{ "text": "您是从电商订单邮件中提取结构化数据的专家。准确提取所有相关字段，无需伪造任何信息。" } ], "messages": [{ "role": "user", "content": [{ "text": "<email_content>您的订单 #12345 已发货！跟踪您的包裹：TRK789456123</email_content>" } ] }, { "role": "assistant", "content": [{ "text": "{\"order_number\": \"12345\"、\"tracking_number\"：\"TRK789456123\"、\"status\"：\"已发货\"}" } ] } ] }
```在我们的实验中，我们准备了两个训练数据集：一个包含 1,300 个样本的较小集和一个包含 4,900 个样本的较大集。这使我们能够评估训练数据大小如何影响模型性能。

您可以使用 Amazon SageMaker Studio 作为开发环境来运行 Jupyter Notebook 来执行数据准备步骤。

### 将训练数据上传到S3存储桶

SageMaker AI Training 在与代码和数据开发环境不同的环境中运行作业。借助 SageMaker AI Training，您可以高效地使用一个或多个强大的 GPU 驱动的实例，这些实例会在训练完成时自动停止。由于实例与数据准备环境分开，因此您需要将数据上传到集中位置：Amazon S3。

以下代码说明了如何将数据从 SageMaker Studio 上传到 S3 存储桶：```
import boto3 s3 = boto3.client('s3') s3.upload_file('train.jsonl', 'your-training-bucket', 'train.jsonl')
```### 微调 Amazon Nova 模型

准备好训练数据后，您可以通过 SageMaker SDK 使用 Amazon SageMaker AI API 创建微调作业。请遵循 [Amazon Nova Customization Hub](https://github.com/aws-samples/amazon-nova-samples/tree/main/customization) 中的示例。这将使用 Amazon SageMaker AI Training 提供一项训练作业，该作业在一个或多个具有您选择的类型和大小的独立实例的容器上运行。

下表总结了我们实验中的关键微调参数：

|参数|描述 |
|:---|:---|
|模型类型 | “amazon.nova-lite-v1:0:300k”或“amazon.nova-micro-v1:0:128k”|
|模型名称或路径 | “nova-lite/prod”或“nova-micro/prod”|
|复制品| 1 用于 g5/g6 4 用于 p5 |
|最大长度| 8192 用于 g5/g6 32768 用于 p5 |
|全局批量大小 | 64 | 64
|最大纪元 | 2 |
|佩夫特方案 |劳拉 |
| loraplus_lr_比率 | 8.0 |
|阿尔法 | 32 | 32

我们选择 Nova Lite 和 Nova Micro 是因为与 Amazon Nova Pro 和其他型号相比，它们的成本较低且性能具有竞争力。

### 部署并运行推理

当您的微调作业成功完成后，您可以在 Amazon Bedrock 中创建自定义模型，以导入由 Amazon SageMaker AI 训练的 PEFT 调整的 Nova 模型。请按照[创建自定义模型](https://docs.aws.amazon.com/bedrock/latest/userguide/create-custom-model-sdks.html)了解详细步骤。然后，您可以使用自定义模型运行推理，如以下示例所示：```
import boto3 import json bedrock_runtime = boto3.client(service_name="bedrock-runtime") def extract_entities(email_content, Provisioned_model_arn): body = { "messages": [{ "role": "user", "content": f"从此电子邮件中提取所有相关数据字段:\n\n{email_content}" }], "max_tokens": 2048, "温度": 0.1 } response = bedrock_runtime.invoke_model( body=json.dumps(body), modelId=provisioned_model_arn,accept="application/json", contentType="application/json" ) response_body = json.loads(response.get('body').read()) return response_body['output']['message']['content'][0]['text'] # 示例use email = """ 亲爱的客户， 您的订单已发货！承运商：FedEx 预计送达：2025 年 1 月 15 日 """ result = extract_entities(email, "arn:aws:bedrock:us-east-1:${account-id}:provisioned-model/your-model-id")
```该函数返回提取的字段，类似于以下内容：```
{ Carrier: FedEx, Date: January 15, 2025 }
```您还可以选择使用不同的方法迭代训练模型。例如，您可以使用 SFT-PEFT 调整中的检查点作为下游直接偏好优化 (DPO) 训练的基础。请参阅[有关迭代训练的文档](https://docs.aws.amazon.com/sagemaker/latest/dg/nova-iterative-training.html)。

### 评估结果

微调模型的准确度比基线提高了 5.6-16.6 个百分点，尽管 Nova Micro 的模型较小，但整体准确度最高，达到 94.77%。与按使用付费的现有模型相比，通过对较轻模型进行 PEFT 调整，微调还可以将推理延迟减少约 32%，并将成本降低约 50%。这些准确性、速度和成本方面的综合收益使 Parcel Perform 能够将调整后的 Amazon Nova 模型部署到生产中。

#### 准确度比较

Parcel Perform 使用 Parcel Perform 的加权精度指标（结合了跨数据字段的提取精度）根据基线模型评估了微调模型。我们在两个代表性数据集上进行了测试，分别有 100 个样本和 200 个样本。

主要发现：

微调为所有模型带来了准确率提升，与基准模型相比提高了 5.6 到 16.6 个百分点。 Nova Micro 的增幅最大，微调后从 76.63% 攀升至 93.27%。将训练数据从 1,300 个样本扩展到 4,900 个样本，将性能进一步提升了 3.3%，这表明训练量的适度增加继续产生有意义的回报。尽管型号较小，Nova Micro 在 200 个样本的测试集上实现了 94.77% 的最高总体准确率。在特定领域的任务上，经过良好调整的紧凑模型可以胜过更大的替代模型。

#### 延迟改进

微调还显着降低了推理延迟：Nova Lite 降低了 31%，Nova Micro 降低了 32%，因为与 Parcel Perform 之前的模型相比，Nova Micro 的模型尺寸更小，参数也更少。这意味着每次推理大约需要 7.7 秒，从而可以更快地每天处理大量电子邮件。

＃＃＃＃ 影响与 Parcel Perform 之前的模型相比，处理时间显着缩短。成本降低了大约 50%，因为 PEFT 可以让更轻的模型在特定任务上表现更好，同时支持按使用付费定价的部署。准确性的提高，加上成本和延迟的降低，让 Parcel Perform 在生产中使用经过微调的 Amazon Nova 模型。

### 结论

在这篇文章中，我们演示了如何使用 Amazon SageMaker AI 微调 Amazon Nova 模型，以从电子商务电子邮件中准确提取实体。我们与 Parcel Perform 的合作表明，使用 LoRA 进行参数高效微调可以显着提高准确性，同时将推理延迟减少 30% 以上。

此次合作的主要收获：

事实证明，微调可以有效减少幻觉。该模型可以正确区分订单号和跟踪号，而无需伪造源材料中不存在的数据。您不需要大量数据集来查看真实结果：只需 25 个实体的 1,300 个训练样本即可实现有意义的准确性提升，即使对于标记数据有限的团队来说，微调也是一种实用的选择。一项违反直觉的发现是，经过微调后，较小的 Nova Micro 模型的性能优于较大的 Nova Lite，这表明特定于任务的优化可以弥补基本模型大小的差异。这会产生成本影响：将 Nova Micro 等更小、更快的模型与减少的推理延迟相结合，可以创建一种经济高效的解决方案，用于大规模处理大量电子邮件。能够通过按需、基于令牌的定价将 PEFT 调整的模型直接部署到 Amazon Bedrock 中，这意味着您可以按使用付费运行完全定制的模型，从而无需预置和维护专用的 LLM 托管基础设施。

#### 开始使用

要实施此解决方案，首先以上述格式准备训练数据。从本文中所示的至少包含 1,300 个样本的数据集开始，以获得有意义的结果。为了获得最佳结果，请确保您的训练数据代表您在生产中会遇到的各种电子邮件格式。如果您面临类似的实体提取挑战，您可以使用 SageMaker AI 模型自定义来构建准确的、可立即投入生产的解决方案。此方法展示了如何将 Nova Micro 和 Nova Lite 等快速且经济高效的模型应用于生产用例，从而提供准确性、速度和成本效益。

准备好亲自尝试一下吗？探索这些资源：

- [在 Amazon Bedrock 中自定义模型](https://docs.aws.amazon.com/bedrock/latest/userguide/custom-models.html)：了解有关 Amazon Bedrock 模型自定义的更多信息。
- [Amazon Nova Forge 产品详细信息页面](https://aws.amazon.com/nova/forge)：探索使用 Nova 进行自定义模型开发。
- [生成式 AI 创新中心](https://app.qbs-cell001.word.us-east-1.prod.plato.ai.aws.dev/link)：与 AWS GenAIIC 合作处理类似的用例。

AWS GenAIIC 是 AWS 于 2023 年推出的一项计划，旨在帮助组织将生成式 AI 潜力转化为业务价值。该中心汇集了 AWS 科学和战略专家，他们在整个生成式 AI 旅程中与客户合作，帮助确定用例的优先级、构建战略路线图，并将 AI 解决方案从概念转变为生产。自成立以来，该创新中心已与一级方程式、纳斯达克、瑞安航空、标准普尔全球等1000多家跨行业客户合作，近年来超过65%的项目达到了生产部署。此后，AWS 对该计划的投资增加了一倍，以扩大对构建生成式 AI 解决方案的客户的支持。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
