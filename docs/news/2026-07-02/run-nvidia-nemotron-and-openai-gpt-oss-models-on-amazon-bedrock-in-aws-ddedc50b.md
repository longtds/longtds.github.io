<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T02:14:34+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/run-nvidia-nemotron-and-openai-gpt-oss-models-on-amazon-bedrock-in-aws-govcloud-us/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 在 AWS GovCloud（美国）的 Amazon Bedrock 上运行 NVIDIA Nemotron 和 OpenAI GPT OSS 模型 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 02:14 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | Run NVIDIA Nemotron and OpenAI GPT OSS models on Amazon Bedrock in AWS GovCloud (US) \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/run-nvidia-nemotron-and-openai-gpt-oss-models-on-amazon-bedrock-in-aws-govcloud-us/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

我们很高兴在 AWS GovCloud（美国）中引入基于美国的前沿开放权重模型。通过此版本，Amazon Bedrock 现在支持 OpenAI 的开放权重 GPT OSS 模型（120B 和 20B）和 NVIDIA Nemotron（Nano 9B v2、Nano 12B v2、Nano 30B、Super 120B）模型。在这篇文章中，我们将介绍这些模型及其功能、数据驻留的推理选项、可用的服务层以及如何开始。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 在 

AWS GovCloud（美国）的 Amazon Bedrock 上运行 NVIDIA Nemotron 和 OpenAI GPT OSS 模型

在 AWS GovCloud（美国）中运行工作负载的政府机构需要与商业部门保持同步的 AI 功能。与此同时，他们不能损害其任务所需的安全和合规控制。随着开放重量基础模型 (FM) 从实验转向任务系统，每个模型决策都有两个要求。首先，模型必须提供任务所需的能力。其次，推理环境必须满足机构的安全性、合规性和数据驻留义务。对于美国政府机构、国防和情报界以及为其服务的承包商来说，这些要求是不容谈判的。访问先进的开放权重模型对于情报分析、任务规划、采购和合同文档审查、安全日志分析和合规自动化等工作至关重要。此访问不得要求将敏感数据移至管理它的边界之外。

我们很高兴在 AWS GovCloud（美国）中引入基于美国的前沿开放权重模型。通过此版本，Amazon Bedrock 现在支持 OpenAI 的开放权重 GPT OSS 模型（120B 和 20B）和 NVIDIA Nemotron（Nano 9B v2、Nano 12B v2、Nano 30B、Super 120B）模型。借助这些新模型，您可以使用多样化的高性能 FM 来构建和扩展生成式 AI 应用程序。这使得通过单一、统一的 API 可以灵活地使用 OpenAI 和 NVIDIA 的最新模型以及其他领先的 AI 模型。您可以使用这个统一的 API 为每个特定用例选择正确的模型，而无需更改应用程序代码。

AWS GovCloud（美国）提供一组隔离的 AWS 区域，旨在托管敏感数据和受监管的工作负载。区域实际上位于美国，并且仅由美国公民管理。它们帮助客户满足合规性框架，包括 FedRAMP High（临时操作授权）和 DoD 云计算安全要求指南 (SRG) 影响级别 2、4 和 5。其他框架包括国际武器贸易条例 (ITAR) 和刑事司法信息服务 (CJIS)。[Amazon Bedrock](https://aws.amazon.com/bedrock/) 是一项完全托管的服务，用于访问来自独立模型提供商的 FM，推理完全在 AWS 运营的基础设施上运行。

借助 Amazon Bedrock，推理可以在 AWS GovCloud（美国）隔离边界内、美国公民在美国领土上运营的基础设施上运行。有关 Amazon Bedrock 如何处理您的数据的详细信息，请参阅 [Amazon Bedrock 中的数据保护](https://docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html)。

OpenAI 的开放权重 GPT OSS 模型和 NVIDIA Nemotron 开放权重模型现已在 AWS GovCloud（美国）的 Amazon Bedrock 上提供。此次发布向 AWS GovCloud（美国）区域提供了两个开放权重模型系列：OpenAI gpt-oss-120b 和 gpt-oss-20b，以及 NVIDIA Nemotron 3 系列，包括 Nemotron 3 Super 120B 以及 Nemotron 3 Nano 模型。借助这些模型，您可以构建代理应用程序和任务工作流程，例如自动安全控制评估、多文档情报合成、合同和采购分析以及策略合规性检查。所有这些都在 AWS GovCloud（美国）合规范围内运行。

在这篇文章中，我们将介绍 AWS GovCloud（美国）当前可用的模型及其功能、数据驻留的推理选项、可用的服务层级以及如何开始。

### 关于模型

本部分介绍 AWS GovCloud（美国）目前提供的两个开放权重模型系列以及每个模型的独特功能。

#### NVIDIA Nemotron

NVIDIA Nemotron 系列提供小语言模型 (SLM) 和大语言模型 (LLM) 功能，专为专业代理 AI 系统的计算效率和准确性而构建。 NVIDIA对这两种模型的描述如下：- NVIDIA Nemotron 3 Super 是一种 120B 开放式混合专家混合 (MoE) 模型，适用于复杂的多代理工作负载，总参数为 1200 亿个，每个令牌仅激活 120 亿个参数。该 MoE 设计的吞吐量比上一代高出 5 倍，可实现经济高效的推理，其 100 万个令牌上下文窗口为代理提供了长期记忆，以在长期、多步骤的任务中保持专注。
- NVIDIA Nemotron 3 Nano 是一个包含 300 亿个参数的开放模型，每个令牌可激活约 30 亿个参数，吞吐量比上一代高 4 倍，推理令牌生成量减少高达 60%。其 100 万个令牌上下文窗口支持长时间运行的多步骤代理工作流程。

有关 AWS GovCloud（美国）中提供的 NVIDIA Nemotron 型号的完整列表，请参阅 [Amazon Bedrock 上的 NVIDIA 型号](https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-nvidia.html)。

#### Open

AI GPT OSS

OpenAI 的 GPT OSS 模型是开放权重的文本到文本模型，专为推理、代理和开发人员任务而设计，具有可调整的推理工作量并支持外部工具集成。这篇文章重点关注两种变体：

gpt-oss-120b 是 OpenAI 的 1200 亿参数开放权重模型，专为生产、通用和高推理用例而设计。

gpt-oss-20b 是 200 亿个参数模型，专为降低延迟和本地或特殊用例而设计。

两种模型都提供 128K 令牌上下文窗口和最多 16K 输出令牌，并且都接受文本输入并生成文本输出。由于权重是开放的，组织可以独立评估模型架构、查看已发布的模型卡，并对代表性工作负载运行自己的基准测试。对于政府团队来说，这种透明度支持组织风险评估，使客户安全团队能够在部署之前评估模型行为，并与许多美国政府机构采用的零信任原则保持一致。

有关 AWS GovCloud（美国）中可用的 OpenAI 模型的完整列表，请参阅 [Amazon Bedrock 上的 OpenAI 模型](https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-openai.html)。

### 合规性边界内的无服务器推理

Amazon Bedrock 上的 NVIDIA Nemotron 和 GPT OSS 模型由 Amazon Bedrock 中的下一代推理引擎提供服务。要理解该架构，有助于区分引擎和端点：引擎是底层服务基础设施，设计有模型部署帐户隔离和零操作员访问权限，而“基岩地幔”端点是与 OpenAI 兼容的 HTTPS API，应用程序调用它来向引擎发送请求。对于机构而言，无需配置基础设施，无需管理 GPU，也不需要模型部署专业知识。

下一代推理引擎建立在零操作员访问设计的基础上。任何操作员（无论是来自 AWS、客户还是模型提供商）都无法访问客户数据，例如推理提示或完成结果。与 AWS GovCloud（美国）隔离边界相结合，这为政府团队提供了强大的数据保护基础。技术细节请参考[探索Mantle的零操作员访问设计](https://aws.amazon.com/blogs/machine-learning/exploring-the-zero-operator-access-design-of-mantle/)。

Amazon Bedrock 提供了两个端点来调用这些模型。 “bedrock-mantle”端点是下一代推理引擎的 OpenAI 兼容 API，因此您可以使用 OpenAI Python 和 TypeScript SDK 调用它。它使用聊天完成和响应 API。 “bedrock-runtime”终端节点通过 AWS 开发工具包使用 Converse 和 InvokeModel API，可以访问原生 Amazon Bedrock 功能，例如 Guardrails。两者的代码示例位于入门部分。

### 区域可用性和数据驻留

Amazon Bedrock 提供多种处理推理请求的选项。区域内将每个请求保留在单个区域内，而地理跨区域推理则在一个地理区域内跨区域路由请求以获得更高的吞吐量，因此您的数据保持在该地理边界内。对于 AWS GovCloud（美国）中的 NVIDIA Nemotron 和 GPT OSS 模型，选项如下：

- 区域内推理可在“us-gov-west-1”（AWS GovCloud（美国西部））中使用。
- 地理跨区域推理可通过专用的 AWS GovCloud（美国）跨区域推理 ID 进行，该 ID 可跨“us-gov-west-1”和“us-gov-east-1”路由请求。流量保持在 AWS GovCloud（美国）边界内，同时您可以跨两个区域获得弹性。这些模型的所有推理均位于 AWS GovCloud（美国）边界内。 AWS GovCloud（美国）不提供全球跨区域推理（可跨全球商业 AWS 区域路由请求）。您可以根据需要选择单区域和跨区域。

### 服务等级

Amazon Bedrock 提供多个[服务层级](https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html) 来满足不同的工作负载要求。所有三种型号均支持标准层、优先层和弹性层。

|服务等级|描述 |支持 |
|:---|:---|:---|
|标准|按令牌付费访问，无需承诺 |是的 |
|优先|延迟敏感流量的更高吞吐量 |是的 |
|弹性|以更低的成本访问灵活、非时间敏感的工作负载 |是的 |
|保留 |具有期限承诺的专用吞吐量 |目前不可用 |

默认情况下，请求在标准层上使用按需推理，您可以按令牌付费，而无需提前预留容量。对于延迟敏感、面向客户的工作负载，您可以将单个请求路由到优先级。对于模型评估或批量汇总等非时间敏感型工作，Flex 层提供了成本较低的选项。有关扩展指南以及如何处理生产量限制，请参阅[扩展和吞吐量最佳实践](https://docs.aws.amazon.com/bedrock/latest/userguide/scaling-throughput-best-practices.html) 和入门部分。

### AWS GovCloud 入门（美国）

本节将逐步介绍如何调用模型，从推荐的“基岩-地幔”端点开始。这些示例使用“us-gov-west-1”区域，其中可以使用区域内推理。

#### 控制台游乐场

- 导航到您的 AWS GovCloud（美国）账户中的 [Amazon Bedrock 控制台](https://console.amazonaws-us-gov.com/bedrock/)。
- 从“测试”部分下的左侧菜单中选择“Playground”。
- 选择选择型号。
- 从类别列表中选择提供商（NVIDIA 或 OpenAI），然后选择型号（例如 NVIDIA Nemotron 3 Super 或 120B gpt-oss-120b）。
- 选择应用加载模型。
- 输入测试模型的提示。

#### 使用基岩-地幔端点（推荐）要使用

这些模型，您需要在 AWS GovCloud（美国）中拥有一个具有调用 Amazon Bedrock 模型权限的 AWS 账户。对于“bedrock-mantle”终端节点，您需要 [Amazon Bedrock API 密钥](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html) 或标准 AWS 凭证。以下是政策示例：```
{ "Version": "2012-10-17", "Statement": [{ "Sid": "BedrockMantleInference", "Effect": "允许", "Action": ["bedrock-mantle:CreateInference", "bedrock-mantle:Get*", "bedrock-mantle:List*" ], "Resource": "arn:aws-us-gov:bedrock-mantle:us-gov-west-1:111122223333:project/*" }, { "Sid": "BedrockMantleCallWithBearerToken", "效果": "允许", "操作": "bedrock-mantle:CallWithBearerToken", "资源": "*" } ] }
```将“111122223333”替换为您的 AWS 账户 ID，并将区域范围限定为您使用的 AWS GovCloud（美国）区域。本文中的代码示例使用 Bedrock API 密钥进行身份验证，这需要“bedrock-mantle:CallWithBearerToken”。此操作的范围必须为“Resource”：“*”，如第二个语句所示。要控制哪些身份可以生成或使用 Amazon Bedrock API 密钥，请参阅[控制生成和使用 Amazon Bedrock API 密钥的权限](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html)。要将您的组织限制为仅使用经批准的模型，请使用[服务控制策略 (SCP)](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)。

以下示例使用 [OpenAI Python SDK](https://github.com/openai/openai-python) 调用 `bedrock-mantle` 端点。对于生产工作负载，请使用短期 API 密钥，该密钥会自动过期（最长 12 小时）并继承生成它们的 IAM 角色的权限。```
import boto3 from openai import OpenAI # Retrieve the Bedrock API key from AWS Secrets Manager secrets_client = boto3.client("secretsmanager", region_name="us-gov-west-1") api_key = secrets_client.get_secret_value(SecretId="bedrock-api-key")["SecretString"] client = OpenAI( # Use the AWS GovCloud (US) Region in the base URL, e.g. us-gov-west-1 base_url="https://bedrock-mantle.us-gov-west-1.api.aws/v1", api_key=api_key, ) response = client.chat.completions.create( model="openai.gpt-oss-120b", messages=[{"role": "user", "content": "Explain the benefits of open-weight models for regulated workloads."} ], reasoning_effort="medium", # low | medium | high max_completion_tokens=512, ) print(response.choices[0].message.content)
```注意：这些示例从 [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/) 检索 Bedrock API 密钥。对于本地开发，您可以从环境变量中读取密钥，但在生产中避免这种模式。使用 AWS Secrets Manager 或其他密钥存储。

要改为调用 NVIDIA Nemotron 3 Super 120B，请将模型参数更改为“nvidia.nemotron-super-3-120b”并删除“reasoning_effort”参数（推理工作量控制特定于 GPT OSS）。无需更改其他代码。

##### 控制推理工作

GPT OSS 模型是公开可调整推理工作的推理模型。将聊天完成调用上的“reasoning_effort”参数设置为“low”、“medium”或“high”，以在响应延迟与推理深度之间进行权衡。对于大容量、延迟敏感的流量使用“低”，对于复杂的多步骤推理或代理规划使用“高”。对于推理模型，更喜欢用“max_completion_tokens”来限制响应长度（旧的“max_tokens”字段仍然被接受）。

##### 使用响应 API

除了聊天完成之外，GPT OSS 模型还支持 Responses API，这是 OpenAI 用于推理式交互的接口。它需要一个“输入”而不是一个“消息”数组。 NVIDIA Nemotron 3 Super 120B 不支持响应 API。针对该模型使用聊天完成、对话或调用。```
import boto3 from openai import OpenAI # 从 AWS Secrets Manager 检索 Bedrock API 密钥 Secrets_client = boto3.client("secretsmanager", Region_name="us-gov-west-1") api_key = Secrets_client.get_secret_value(SecretId="bedrock-api-key")["SecretString"] client = OpenAI( base_url="https://bedrock-mantle.us-gov-west-1.api.aws/v1", api_key=api_key, ) response = client.responses.create( model="openai.gpt-oss-120b", input="解释开放权重模型对于受监管工作负载的好处。", ) print(response)
```##### 流式响应

对于聊天和代理用例，您希望在生成令牌时向用户显示令牌，请设置“stream=True”。响应成为增量增量事件的迭代器：```
stream = client.chat.completions.create( model="openai.gpt-oss-120b", messages=[{"role": "user", "content": "Write a short summary of mixture-of-experts architectures."} ], stream=True, ) for chunk in stream: delta = chunk.choices[0].delta.content if delta: print(delta, end="", flush=True) print()
```在“bedrock-runtime”端点上，等效功能需要“bedrock:InvokeModelWithResponseStream”权限，稍后显示的最低策略已授予该权限。

##### 工具调用

NVIDIA Nemotron 和 GPT OSS 开放权重模型专为代理工作流程而设计，使其可用于工具调用场景。在工具调用工作流中，您定义模型可以调用的函数（工具），模型根据用户的请求决定何时调用它们，您的应用程序运行该函数并返回结果以供模型合并到其最终响应中。

以下示例端到端地演示了此模式。我们定义一个“get_weather”工具，发送用户消息，让模型请求该工具调用，使用模拟数据运行该函数，并将结果传回，以便模型可以生成自然语言答案。```
import json import boto3 from openai import OpenAI # 从 AWS Secrets Manager 检索 Bedrock API 密钥 Secrets_client = boto3.client("secretsmanager", Region_name="us-gov-west-1") api_key = Secrets_client.get_secret_value(SecretId="bedrock-api-key")["SecretString"] client = OpenAI( base_url="https://bedrock-mantle.us-gov-west-1.api.aws/v1", api_key=api_key, ) tools = [{ "type": "function", "function": { "name": "get_weather", "description": "获取给定位置的当前天气", "parameters": { "type": "object", "properties": { "location": { "type": "string", "description": "城市和国家（例如，美国西雅图）" }, "unit": { "type": "string", "enum": ["celsius", "fahrenheit"], "description": "温度单位" } }, "required": ["location"] } } } ] # 第 1 步：发送带有工具定义的用户请求 messages = [{"role": "user", "content": "西雅图的天气怎么样？"} ] response = client.chat.completions.create( model="openai.gpt-oss-120b", messages=messages, tools=tools, tool_choice="auto", ) Assistant_message = response.choices[0].message # 步骤 2: 检查模型是否要调用工具 if Assistant_message.tool_calls: messages.append(assistant_message) for tool_call in Assistant_message.tool_calls: function_name = tool_call.function.name Arguments = json.loads(tool_call.function.arguments) # 步骤 3：验证函数名称并运行 if function_name == "get_weather": location = argument.get("location", "Unknown") unit = argument.get("unit", "fahrenheit") result = { "location": location, "温度": 18 if unit == "celsius" else 64, "unit": unit, "condition": "Partly cloudy", "humidity": 72, } else: result = {"error": f"Unknown function: {function_name}"} # 步骤 4：将函数结果返回到模型 messages.append({ "role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result), }) # 步骤 5：获取包含工具结果的最终响应 Final_response = client.chat.completions.create( model="openai.gpt-oss-120b", messages=messages, tools=tools, ) print(final_response.choices[0].message.content) else: print(assistant_message.content)
```此处显示的示例演示了客户端工具调用：模型返回工具调用，您的应用程序运行该函数，然后将结果传回。在“基岩地幔”上，GPT OSS模型同时支持客户端和服务器端工具调用，而NVIDIA Nemotron 3 Super 120B仅支持客户端工具调用。两个模型系列还支持通过 Converse API 在“bedrock-runtime”端点上调用工具（使用“toolConfig”）。请参阅每个型号的[型号卡](https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards.html)，了解完整的功能矩阵。

#### 使用基岩运行时端点 (boto3)

对于“bedrock-runtime”终端节点，您需要配置具有调用模型权限的 AWS 凭证（AWS Identity and Access Management (IAM) 用户或角色）。以下是政策示例：```
{ "Version": "2012-10-17", "Statement": [{ "Effect": "Allow", "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream" ], "Resource": "arn:aws-us-gov:bedrock:us-gov-west-1::foundation-model/openai.gpt-oss-120b-1:0" } ] }
```对于生产部署，将“资源”范围限定为您使用的特定 AWS GovCloud（美国）区域和模型 ID。

以下示例使用 [AWS SDK for Python (boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) 和 Converse API 发送单轮请求。在“bedrock-runtime”端点上，GPT OSS 模型 ID 包含版本后缀（例如“openai.gpt-oss-120b-1:0”）。使用每个型号的型号卡中的准确型号 ID。响应包含一个推理块，后跟一个文本块，因此该示例在打印答案时选择文本块。```
import boto3 client = boto3.client("bedrock-runtime",region_name="us-gov-west-1") response = client.converse( modelId="openai.gpt-oss-120b-1:0", messages=[{ "role": "user", "content": [{"text": "什么是专家混合架构？"}] }], inferenceConfig={"maxTokens": 2048, "温度": 1.0, "topP": 0.95}, ) content_blocks = response["output"]["message"]["content"] response_text = next( (block["text"] for block in content_blocks if "text" in block), None ) if response_text: print(response_text) else: print("无文本响应。")
```要通过“bedrock-runtime”调用 NVIDIA Nemotron 3 Super 120B，请使用型号 ID“nvidia.nemotron-super-3-120b”（此型号 ID 不带有版本后缀）。

您还可以使用 [AWS 命令​​行界面 (AWS CLI)](https://docs.aws.amazon.com/cli/latest/reference/bedrock-runtime/) 从终端访问这些模型：```
aws bedrock-runtime converse \ --model-id openai.gpt-oss-120b-1:0 \ --messages '[{"role":"user","content":[{"text":"Type_Your_Prompt_Here"}]}]' \ --inference-config '{"maxTokens":512}' \ --region us-gov-west-1
```#### 扩展按需推理

标准层上的按需容量是按 AWS 区域共享和分配的，因此在区域需求较高期间，请求可能会短暂排队或受到限制。在“bedrock-mantle”端点上，没有每分钟请求配额。吞吐量受基于令牌的限制控制。这些开放权重模型目前没有在服务配额控制台中发布每个帐户的令牌配额，因此请使用具有指数退避的重试逻辑来处理瞬时限制。 Amazon Bedrock 会显示两个 HTTP 错误代码，指示何时无法处理请求：

|错误代码 |意义|建议行动 |
|:---|:---|:---|
| 429 | 429该请求被拒绝，因为它超出了 Amazon Bedrock 的账户配额。 |通过服务配额控制台请求增加配额，并应用客户端限制。 |
| 503 | 503该服务正面临高需求或临时容量限制。 |使用指数退避和抖动重试。如果持续限制，请降低请求速率并逐渐恢复。 |

对于瞬态 503 响应，请在 SDK 中配置自动重试：```
从 botocore.config 导入 Config config = Config(retries={"total_max_attempts": 6, "mode": "standard"}) client = boto3.client("bedrock-runtime", config=config)
```持续节流后回升时，在两次增加之间保持稳定状态约 15 分钟，而不是直接逐步达到目标音量。有关更详细的启动过程和其他最佳实践，请参阅 Amazon Bedrock 用户指南中的[扩展和吞吐量最佳实践](https://docs.aws.amazon.com/bedrock/latest/userguide/scaling-throughput-best-practices.html)。

#### 清理

这些模型使用按需推理，仅在调用模型时才会产生费用，因此无需拆除端点或基础设施。为避免测试后产生意外费用：

如果您生成短期 Bedrock API 密钥，它们会自动过期（最长 12 小时）。要尽快撤销，请在 Amazon Bedrock 控制台中将其删除。

如果您选择使用优先级进行测试，请通过从调用中删除“service_tier”参数返回到非延迟敏感流量的标准定价。

如果您在 AWS Secrets Manager 中存储了 Bedrock API 密钥以进行测试，请删除该密钥以避免存储费用。

有关按型号和等级划分的定价详细信息，请参阅 [Amazon Bedrock 定价](https://aws.amazon.com/bedrock/pricing/)。

### 定价和供货情况

OpenAI GPT OSS 和 NVIDIA Nemotron 模型现已在 AWS GovCloud（美国）的 Amazon Bedrock 上提供。区域内推理可在 AWS GovCloud（美国西部）(`us-gov-west-1`) 中使用，地理跨区域推理可跨 AWS GovCloud (美国西部) 和 AWS GovCloud (美国东部) (`us-gov-east-1`) 路由请求，同时将流量保持在 AWS GovCloud (美国) 边界内。

定价按代币计算，并因型号和服务级别而异。当您调用模型时，标准层上的按需推理会产生费用，没有预留容量，也没有需要拆除的基础设施。有关当前费率，请参阅 [Amazon Bedrock 定价](https://aws.amazon.com/bedrock/pricing/)。

＃＃＃ 结论OpenAI GPT OSS 和 NVIDIA Nemotron 模型现已在 AWS GovCloud（美国）的 Amazon Bedrock 上提供，让政府客户能够在其合规范围内访问高级开放权重模型。在这篇文章中，我们介绍了可用的模型及其功能、调用它们的两个端点、可用的服务层和扩展指南。政府团队可以为任务工作负载运行这些开放权重模型，同时在 AWS GovCloud（美国）边界内的 AWS 运营的基础设施上保持推理。

开始使用：

- 在您的 AWS GovCloud（美国）账户中打开 [Amazon Bedrock 控制台](https://console.amazonaws-us-gov.com/bedrock/) 并尝试 Playground 中的模型。
- 根据您自己的数据运行本文中的“bedrock-mantle”Python 示例。
- 在您的工作负载上评估 gpt-oss-120b、gpt-oss-20b 和 NVIDIA Nemotron 3 Super 120B，以选择适合您的成本和延迟情况的型号。
- 对于生产部署，请查看[扩展和吞吐量最佳实践](https://docs.aws.amazon.com/bedrock/latest/userguide/scaling-throughput-best-practices.html) 并考虑延迟敏感流量的优先级。

### 资源

有关更多信息，请参阅以下资源：

- [AWS GovCloud（美国）](https://aws.amazon.com/govcloud-us/)
- [亚马逊基岩用户指南](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
- [Amazon Bedrock 上的 OpenAI 模型](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-openai.html)
- [NVIDIA Nemotron 3 Super 120B 型号卡](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-nvidia-nemotron-super-3-120b.html)
- [探索Mantle的零操作员访问设计](https://aws.amazon.com/blogs/machine-learning/exploring-the-zero-operator-access-design-of-mantle/)
- [Amazon Bedrock 服务等级](https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html)
- [Amazon Bedrock API 密钥](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html)

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
