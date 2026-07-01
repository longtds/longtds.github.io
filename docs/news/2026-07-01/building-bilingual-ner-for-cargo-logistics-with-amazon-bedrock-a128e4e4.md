<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:33:46+08:00
source: AWS ML Blog
domain: 云原生
url: https://aws.amazon.com/blogs/machine-learning/building-bilingual-ner-for-cargo-logistics-with-amazon-bedrock/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 使用 Amazon Bedrock 构建用于货运物流的双语 NER |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:33 CST |
| 领域 | 云原生 |
| 来源 | AWS ML Blog |
| 原文标题 | Building bilingual NER for cargo logistics with Amazon Bedrock \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/building-bilingual-ner-for-cargo-logistics-with-amazon-bedrock/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在这篇文章中，我们分享使用基于代币的蒸馏的技术方法、经验教训和部署架构。如果您面临类似的双语 NER 挑战，您可以从 IBS Software 的 Amazon Bedrock 知识提炼功能经验中受益。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 使用 

Amazon Bedrock 构建用于货运物流的双语 NER

[IBS Software](https://www.ibsplc.com/) 的货运系统每天处理数千封双语货运物流电子邮件。该系统提取关键信息，例如英语和日语的航空运单 (AWB) 号码、航班详细信息、重量和交付说明。这增加了构建强大的命名实体识别 (NER) 解决方案的复杂性。挑战包括减慢操作速度的手动干预以及准确性和成本之间的权衡。 IBS Software 需要一种 AI 解决方案，能够跨两种语言准确识别 23 种不同的实体类型，同时保持大规模的成本效益。

在探索多种方法后，IBS Software 使用 Amazon Bedrock 的托管蒸馏功能来创建可立即投入生产的解决方案。通过将 Amazon Nova Pro 中的知识提炼为更高效的 [Amazon Nova Lite](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-lite.html) 模型，IBS Software 实现了 95.085% 的 F1-Score 准确率，同时将运营成本降低了 14 倍。本案例研究详细介绍了他们从面对复杂的开源实施到在 AWS 上成功部署（现在可以实时处理货物电子邮件）的历程。

在这篇文章中，我们分享使用基于代币的蒸馏的技术方法、经验教训和部署架构。如果您面临类似的双语 NER 挑战，您可以从 IBS Software 的 [Amazon Bedrock](https://aws.amazon.com/bedrock/model-distillation/) 知识提炼功能经验中受益。

### 解决方案概述

目标是建立一个双语 NER 系统，能够从用英语和日语编写的货运物流电子邮件中提取 23 种实体类型。关键实体包括：

- AWB（航空运单）号码。
- 航班号和航线。
- 重量（毛重、计费重量、尺寸）。
- 尺寸和体积。
- 商品描述。
- 托运人和收货人信息。
- 特殊处理代码。
- 交货说明。主要风险包括保持两种语言的高精度、大规模管理推理成本以及实现实时处理的低延迟。借助 Amazon Bedrock 的模型蒸馏功能，您可以使用更小、更快且更具成本效益的模型。这些模型为您的用例提供的准确性可与 Amazon Bedrock 中最先进的模型相媲美。

下图显示了 Amazon Bedrock 上的端到端双语 NER 工作流程。

![Amazon Bedrock 上的端到端双语 NER 工作流程](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/25/ML-20433-1.png)

图 1：Amazon Bedrock 上的端到端双语 NER 工作流程

### 解决方案

IBS 的 9 名研究人员和工程师团队花费了大约 4 个月的时间来开发和部署该解决方案。项目时间表包括：

- 第 1 个月：500 封双语电子邮件的数据集准备和注释。
- 第 2 个月：开源框架（PyTorch、TextBrewer）面临的挑战。
- 第 3 个月：使用 Amazon Bedrock 成功蒸馏（Nova Pro → Nova Lite）。
- 第 4 个月：生产部署和优化。

完成的主要任务：

- 注释了 500 条货物电子邮件消息（350 条英语，150 条日语），包含 23 种实体类型。
- 使用自定义超参数配置 Amazon Bedrock 蒸馏。
- 经过 4 个 epoch 训练的学生模型超过 70 个步骤。
- 损失从 0.05 减少到 0.008。
- 使用 .eml 文件处理管道部署推理端点。
- 在测试集上验证了 95.085% 的 F1 分数。

IBS Software 使用 Amazon Bedrock 托管服务部署了所有基础设施，从而绕过了对自定义模型托管基础设施的需求。

#### 开源方法面临的挑战

最初，该团队尝试使用开源框架（包括基于 PyTorch 的实现和 TextBrewer 库）进行知识蒸馏。这些方法失败的原因是：

- 为双语数据配置蒸馏管道的复杂性。
- 缺乏用于培训和部署的托管基础​​设施。
- 难以调整代币级蒸馏的超参数。
- 与我们的生产电子邮件处理工作流程不兼容。

有关知识蒸馏基础知识的更多详细信息，请参阅 [AWS 机器学习最佳实践](https://docs.aws.amazon.com/machine-learning/)。

#### 亚马逊基岩蒸馏方法我们转向 

Amazon Bedrock 模型蒸馏，使用 Amazon Nova Pro 作为教师模型，使用 Nova Lite 作为学生模型。主要优点包括：

- 通过自动超参数优化管理训练基础设施。
- 对令牌级蒸馏的本机支持。
- 易于与我们的电子邮件处理管道集成。
- 内置监控和评估指标。

训练配置：```
蒸馏_config = {“teacher_model”：“amazon.nova-pro-v1：0”，“student_model”：“amazon.nova-lite-v1：0”，“max_sequence_length”：2048，“epochs”：4，“training_steps”：70，“loss_function”：“token_level_kl_divergence”}
```训练过程通过 70 个步骤将损失从 0.05 减少到 0.008，这表明教师到学生的知识转移很强。

有关 Amazon Bedrock 蒸馏文档，请参阅 [在 Amazon Bedrock 中使用蒸馏自定义模型](https://docs.aws.amazon.com/bedrock/latest/userguide/model-distillation.html)。

#### 数据集准备

我们的数据集包含 500 封真实的货运物流电子邮件：

- 350 封英文电子邮件：标准货物文件，包含 AWB 编号、航班详细信息、重量和装卸说明。
- 150 封日语电子邮件：具有日语特定格式和术语的类似内容。

每封电子邮件均由熟悉货运物流术语的领域专家手动注释 23 种实体类型。注释过程大约耗时 3 周，并为两种语言提供了高质量的训练数据。

#### 模型评估

我们使用 F1-Score（精确率和召回率的调和平均值）评估了教师和学生模型：

结果：

尽管基本 Nova Lite 模型的整体 F1 分数约为 84%，但教师模型和定制的 Nova Lite 模型的准确率提高了约 10%。下表显示了 F1 分数结果。

|型号|总体 F1 分数 |英语 F1-Score |日本F1-分数|
|:---|:---|:---|:---|
| Nova Pro（教师）| 97.0% | 97.8% | 96.2% |
| Nova Lite（学生）| 95.085% | 96.535% | 93.635% |

经过提炼的 Nova Lite 模型保留了 98% 的教师性能，同时将生产推理成本降低了 14 倍。

#### 错误分析和挑战

我们观察到，学生模型在日语文本上的 F1 分数比在英语文本上低 2.565%。这种差距主要来自于商品描述中复杂的汉字字符组合、日语文本中不明确的实体边界（没有空格）以及日语训练数据量较小（150 封电子邮件与 350 封电子邮件）。带有嵌入实体的多行传递指令有时也会导致边界检测错误。

为了克服这些挑战，我们通过综合示例增强了日语训练数据。我们还对已知实体模式（AWB 格式、航班号正则表达式）应用后处理规则，并实施置信度阈值来标记低置信度预测以供人工审核。

#### 部署工作流程注意：以下部署创建会产生费用的 

AWS 资源。 Amazon Simple Storage Service (Amazon S3) 存储、AWS Lambda 调用、Amazon Bedrock 模型推理和 Amazon DynamoDB 存储都有相关成本。当您不再需要这些资源时，请将其删除，以避免持续产生费用。

我们的生产部署通过以下工作流程处理 .eml 文件：

- 电子邮件摄取：货物电子邮件消息以 .eml 文件形式到达 Amazon S3 中。
- 预处理：AWS Lambda 提取电子邮件正文和元数据。
- 推理：Amazon Bedrock 终端节点使用经过精炼的 Nova Lite 模型处理文本。
- 实体提取：模型返回 23 种带有置信度分数的实体类型。
- 后处理：应用验证规则和置信过滤。
- 输出：结构化 JSON，提取的实体存储在 Amazon DynamoDB 中。```
import boto3 import json bedrock_runtime = boto3.client('bedrock-runtime') def extract_entities(email_text): response = bedrock_runtime.invoke_model( modelId='<custom model arn>', body=json.dumps({ "inputText": email_text, "taskType": "NER", "entityTypes": ["AWB_NUMBER", "FLIGHT_NUMBER", "WEIGHT_GROSS", "WEIGHT_CHARGEABLE", "DIMENSIONS", "COMMODITY", "SHIPPER", "CONSIGNEE", "HANDLING_CODE", # ... 14 more entity types ] }) ) result = json.loads(response['body'].read()) return result['entities']
```有关 Lambda 集成模式，请参阅[AWS Lambda 与 Amazon Bedrock](https://docs.aws.amazon.com/lambda/latest/dg/services-bedrock.html)。

整个管道在 2 秒内处理电子邮件消息，准确率高达 95.085%，满足我们的实时处理要求。

### 结论

在这篇文章中，我们展示了 IBS Software 如何使用 Amazon Bedrock 托管蒸馏功能为货运物流构建经济高效的双语 NER 系统。该系统实现了 95.085% 的 F1 分数，同时将运营成本降低了 14 倍。经过提炼的 Nova Lite 模型保留了教师模型 98% 的性能，使其成为大批量生产工作负载的理想选择。

我们的主要收获是 Amazon Bedrock 管理的蒸馏功能减轻了开源框架的复杂性。令牌级知识蒸馏保留了英语和日语的准确性，并且 2048 个令牌序列长度适应了典型的货物电子邮件长度。使用 AWS Lambda 和 Amazon S3 集成进行生产部署需要最少的自定义基础设施。

后续步骤：

如果您面临类似的双语 NER 挑战，请考虑：

- 从 Amazon Bedrock 按需基础模型开始进行快速原型设计。
- 投资高质量的双语训练数据注释。
- 使用训练数据集探索模型蒸馏。模型蒸馏的一个限制是教师模型和学生模型必须位于同一模型系列中。

有关本文讨论的主题的更多信息，请参阅以下资源：

- [Amazon Bedrock 模型蒸馏指南](https://aws.amazon.com/blogs/machine-learning/a-guide-to-amazon-bedrock-model-distillation-preview/)
- [在 Amazon Bedrock 中使用 Claude 工具加速自定义实体识别](https://aws.amazon.com/blogs/machine-learning/accelerating-custom-entity-recognition-with-claude-tool-use-in-amazon-bedrock/)
- [在 Amazon SageMaker AI 上使用开源 NER 模型和 LLM 构建人工智能驱动的文档处理平台](https://aws.amazon.com/blogs/machine-learning/build-an-ai-powered-document-processing-platform-with-open-source-ner-model-and-llm-on-amazon-sagemaker/)

如果您正在为自己的用例进行双语 NER 或知识提炼，我们很想听听您的经验。在评论中分享您的问题或反馈。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
