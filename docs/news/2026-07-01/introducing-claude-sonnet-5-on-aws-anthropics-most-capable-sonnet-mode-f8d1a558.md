<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T02:40:09+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/introducing-claude-sonnet-5-on-aws-anthropics-most-capable-sonnet-model/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 在 AWS 上推出 Claude Sonnet 5：Anthropic 最强大的 Sonnet 模型 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 02:40 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | Introducing Claude Sonnet 5 on AWS: Anthropic’s most capable Sonnet model \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/introducing-claude-sonnet-5-on-aws-anthropics-most-capable-sonnet-model/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

今天，我们很高兴地宣布 Anthropic 最先进的 Sonnet 模型 Claude Sonnet 5 在 Amazon Bedrock 和 AWS 上的 Claude Platform 上可用。 Claude Sonnet 5 是 Anthropic 最新一代的第一个 Sonnet 模型，代表着向前迈出的有意义的一步。它以 Sonnet 定价为编码、代理和日常专业人士提供顶级情报 [...]

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 在 

AWS 上推出 Claude Sonnet 5：Anthropic 最强大的 Sonnet 模型

今天，我们很高兴地宣布 Anthropic 最先进的 Sonnet 模型 Claude Sonnet 5 在 Amazon Bedrock 和 [AWS 上的 Claude Platform](https://aws.amazon.com/blogs/machine-learning/introducing-claude-platform-on-aws-anthropics-native-platform-through-your-aws-account/) 上可用。 Claude Sonnet 5 是 Anthropic 最新一代的第一个 Sonnet 模型，代表着向前迈出的有意义的一步。它以 Sonnet 定价为大规模编码、代理和日常专业工作提供顶级情报。借助 Amazon Bedrock 上的 Claude Sonnet 5，您可以在现有的 AWS 环境中进行构建、维护企业安全性和区域数据驻留以及规模推理。 Claude Sonnet 5 还可通过 AWS 上的 Claude Platform 获取，让您可以通过 AWS 管理控制台访问 Anthropic 的本机平台体验和功能。使用与直接使用 Anthropic 相同的 API、功能和控制台体验进行构建、测试和部署，并与 AWS 计费和身份验证相统一。

这篇文章介绍了 Sonnet 5 的改进以及 AI 工程师将该模型集成到 Amazon Bedrock 上的代理系统和生产推理工作负载中的实用指南。请参阅 AWS 上的 Claude Platform 的[文档](https://docs.aws.amazon.com/claude-platform/)。

### 是什么让

Claude十四行诗 5 与众不同

Claude Sonnet 5 在编码、代理任务和专业工作方面表现出更强的表现。 Claude Sonnet 5 带来了接近 Opus 的智能，同时保持了相同的功能、成本和速度平衡，因此团队可以依靠 Sonnet 来完成大规模的日常任务。当您需要大规模的强大推理、编码和代理可靠性且无需 Opus 级别定价时，请使用 Claude Sonnet 5。当您的任务需要最高的推理来证明成本溢价合理时，请使用 Claude Opus。 Sonnet 5 可以跨阶段制定计划，跟踪已完成的工作和剩余的工作，并通过更少的修正轮次来解决问题。这会导致大规模行为更加可预测。在编码方面，Sonnet 5 旨在导航真实的代码库、进行多文件更改以及进行更长时间的调试和重构任务直至完成。它可以编写更干净、更易于维护的代码，并减少监督。对于自主代理来说，Claude Sonnet 5 可以作为自动化操作的更可靠的支柱，处理复杂的依赖链和多步骤工具的使用，使其非常适合面向客户和内部代理。在专业工作中，Sonnet 5 将冗长、复杂、非结构化的资源合成为结构化的可交付成果，例如简报、分析和报告。 Claude Sonnet 5 被设计为 Sonnet 4.6 的明显升级。

### 行业用例

Claude Sonnet 5 非常适合可靠性和结构化推理最重要的行业。对于金融服务团队来说，Sonnet 5 为电子表格建模、财务分析和报告代理提供了支持，可以随时审核自己的数据。这支持从数据摄取到验证输出的端到端工作流程。对于生产力工作，它可以高度一致性地处理报告构建和审计、文档起草和结构化分析。借助其计算机使用功能，您可以自动化以前需要人工交互的浏览器和桌面工作流程。对于代理和工作流程自动化，Claude Sonnet 5 充当生产代理的支柱，可调用工具并在无人值守的情况下运行多步骤作业。

### 在 

Amazon Bedrock 上开始使用 Claude Sonnet 5

您可以在 [Amazon Bedrock 控制台](https://console.aws.amazon.com/bedrock/?trk=d8ec3b19-0f37-4f8c-8c12-189f913e205c&sc_channel=el) 中开始使用 Claude Sonnet 5。

- 在 Amazon Bedrock 控制台的测试下，选择 Playground。
- 对于模型，选择 Claude Sonnet 5。现在，您可以使用该模型测试复杂的编码提示。

![Amazon Bedrock 控制台选择模型对话框，选择了 Anthropic 并选择了 Claude Sonnet 5](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/25/ML-21192-1.jpg)

![聊天模式下的 Amazon Bedrock Playground 显示分布式架构提示和 Claude Sonnet 5 响应](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/25/ML-21192-2.jpg)

Amazon Bedrock 控制台 Playground 选择了 Claude Sonnet 5您还可以使用 [Anthropic Messages API](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html?trk=d8ec3b19-0f37-4f8c-8c12-189f913e205c&sc_channel=el) 以编程方式访问模型，通过 Anthropic SDK 或 `bedrock-mantle` 端点调用 `bedrock-runtime`，或者通过 [AWS 命令行界面 (AWS CLI)](https://aws.amazon.com/cli/?trk=769a1a2b-8c19-4976-9c45-b6b1226c7d20&sc_channel=el) 和 [AWS 继续在 `bedrock-runtime` 上使用 [Invoke](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-api.html) 和 [Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html?trk=d8ec3b19-0f37-4f8c-8c12-189f913e205c&sc_channel=el) SDK](https://aws.amazon.com/developer/tools/?trk=769a1a2b-8c19-4976-9c45-b6b1226c7d20&sc_channel=el)。

#### 先决条件

- 具有 Amazon Bedrock 访问权限的活跃 AWS 账户
- AWS CLI 安装并配置
-Python 3.8+
- Boto3 安装：`pip install boto3`
- 安装 Anthropic SDK：`pip install anthropic[bedrock]`
- IAM权限：`bedrock:InvokeModel`、`bedrock:InvokeModelWithResponseStream` 和 `bedrock:CreateInference`

以下是使用适用于 Python 的 AWS 开发工具包 (Boto3) 的简单示例：```
import boto3 import json # 创建一个 Bedrock Runtime 客户端 bedrock_runtime = boto3.client( service_name="bedrock-runtime", Region_name="us-east-1" ) # 调用 Claude Sonnet 5 response = bedrock_runtime.invoke_model( modelId="us.anthropic.claude-sonnet-5", contentType="application/json", Accept="application/json", body=json.dumps({ "anthropic_version": "bedrock-2023-05-31", "max_tokens": 4096, "messages": [{ "role": "user", "content": "在 AWS 上使用 Python 设计分布式架构，该架构应支持跨多个地理区域每秒 100k 请求。" } ] }) ) result = json.loads(response["body"].read())打印（结果[“内容”][0][“文本”]）
```您还可以将 Claude Sonnet 5 与 Amazon Bedrock Converse API 结合使用，以获得统一的多模型体验：```
import boto3 bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1") response = bedrock_runtime.converse( modelId="us.anthropic.claude-sonnet-5", messages=[{ "role": "user", "content": [{ "text": "Design a distributed architecture on AWS in Python that should support 100k requests per second across multiple geographic regions." } ] } ], inferenceConfig={ "maxTokens": 4096 } ) print(response["output"]["message"]["content"][0]["text"])
```您还可以将 Claude Sonnet 5 与 Anthropic Messages API 结合使用，使用 `anthropic[bedrock]` SDK 包来获得简化的体验：```
from anthropic import AnthropicBedrockMantle # 初始化基岩地幔客户端（自动使用 SigV4 身份验证） mantle_client = AnthropicBedrockMantle(aws_region="us-east-1") # 使用 Messages API 创建消息 message = mantle_client.messages.create( model="anthropic.claude-sonnet-5", max_tokens=4096, messages=[{"role": "user", "content": "在 AWS 上使用 Python 设计一个分布式架构，该架构应支持跨多个地理区域每秒 100k 请求"} ] ) print(message.content[0].text)
```### 可用性

Claude Sonnet 5 现已在 Amazon Bedrock 上推出，受支持的 AWS 区域的完整列表可在 [Amazon Bedrock 文档](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-sonnet-5.html) 中找到。 Claude Sonnet 5 还可在北美、南美、欧洲和亚太地区的 AWS 上的 Claude 平台上使用。

在 [Amazon Bedrock 控制台](https://console.aws.amazon.com/bedrock?trk=d8ec3b19-0f37-4f8c-8c12-189f913e205c&sc_channel=el)、[AWS 上的 Claude Platform](https://console.aws.amazon.com/claude-platform/) 中尝试 Claude Sonnet 5，或浏览 GitHub 上的[入门笔记本](https://github.com/aws-samples/anthropic-on-aws/tree/main/notebooks)。 Sonnet 5 在 2026 年 8 月 31 日之前以促销价提供。有关详细信息，请参阅 [Amazon Bedrock 定价](https://aws.amazon.com/bedrock/pricing/)。您还可以使用 Amazon Bedrock 上的 [高级提示优化](https://docs.aws.amazon.com/bedrock/latest/userguide/advanced-prompt-optimization-how.html) 来释放 Sonnet 5 的全部潜力。它会根据您当前的提示，根据您的评估标准对它们进行基准测试，并输出可用于生产的重写。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
