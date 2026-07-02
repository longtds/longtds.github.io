<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T02:07:06+08:00
source: AWS ML Blog
domain: 云原生
url: https://aws.amazon.com/blogs/machine-learning/building-a-serverless-a2a-gateway-for-agent-discovery-routing-and-access-control/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 构建用于代理发现、路由和访问控制的无服务器 A2A 网关 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 02:07 CST |
| 领域 | 云原生 |
| 来源 | AWS ML Blog |
| 原文标题 | Building a serverless A2A gateway for agent discovery, routing, and access control \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/building-a-serverless-a2a-gateway-for-agent-discovery-routing-and-access-control/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在本文中，您将了解如何在 AWS 上构建无服务器 A2A 网关，该网关使用基于路径的路由 (/agents/{agentId}) 在单个域后面托管多个代理。标准 A2A 客户端无需修改即可工作。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 构建用于代理发现、路由和访问控制的无服务器 A2A 网关

随着企业跨团队、供应商和基础设施部署人工智能代理，管理代理之间的通信成为越来越大的运营负担。如果没有集中层，每个新的代理集成都会添加点对点连接、单独的凭据和自定义路由逻辑。团队花费工程周期来连接连接，而不是构建代理功能。访问控制变得支离破碎，没有一个地方可以强制哪些客户端可以访问哪些代理。结果是新代理工作流程的上市时间变慢，身份验证策略不一致导致的安全风险增加，以及随着每个新代理添加到网络而呈二次方扩展的运营开销。

网关模式通过在代理前面放置单个入口点来解决此问题，无论它们是在 [Amazon Elastic Container Service (Amazon ECS)](https://aws.amazon.com/ecs/)、[AWS Lambda](https://aws.amazon.com/lambda/)、[Amazon Bedrock AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html)、非 AWS 云还是混合环境上运行。它集中处理路由并强制执行细粒度的权限，无需将团队绑定到特定的运行时、框架或编排层。此模式建立在代理到代理 (A2A) 协议的基础上，该协议标准化了代理之间的通信方式。如果没有中央协调器，部署 20 个代理需要多达 190 个点对点连接。

在本文中，您将了解如何在 AWS 上构建无服务器 A2A 网关，该网关使用基于路径的路由 (/agents/{agentId}) 在单个域后面托管多个代理。标准 A2A 客户端无需修改即可工作。该解决方案分为三层：

- 管理层：具有发现和语义搜索功能的集中式代理注册。
- 控制层：使用 JSON Web Token (JWT) 范围和 Lambda 授权者进行细粒度访问控制。
- 执行层：具有 OAuth 后端身份验证和服务器发送事件 (SSE) 流支持的单域路由。

按照下面的操作，您将部署一个 Terraform 配置的网关，A2A 一致的代理可以连接到该网关。

＃＃＃ 建筑学下图显示了网关的组件以及请求如何流经系统。

![无服务器 A2A 网关的架构图，显示从客户端到后端代理的请求流](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/22/ML-20635-1.png)

[Amazon API Gateway](https://aws.amazon.com/api-gateway/) (REST API) 充当单入口点。该架构使用 REST API，因为 REST API 支持响应流。基于 SSE 的实时代理响应需要流式传输。 Lambda 授权方检查 JWT 范围并生成 AWS Identity and Access Management (IAM) 策略，允许访问特定代理路径 (/agents/agent-a/*)，同时拒绝其他代理路径。

Lambda 函数实现网关逻辑：

- 授权者：验证 JWT 并根据范围到代理的映射生成 IAM 策略。
- 注册表：列出呼叫者可以访问的代理，并重写 URL 以指向网关。
- 搜索：使用 [Amazon Bedrock](https://aws.amazon.com/bedrock/) 中的 Amazon Titan 文本嵌入进行语义代理发现。
- 代理：通过 OAuth 身份验证将请求路由到后端代理，通过 Lambda Web Adaptor 支持 SSE 流。
- 管理员：代理注册和生命周期管理。

[Amazon DynamoDB](https://aws.amazon.com/dynamodb/) 存储三个表。代理注册表将代理 ID 映射到后端 URL、身份验证配置和缓存的代理卡。权限表将 JWT 范围映射到允许的代理。 RateLimitCounters 表对每分钟的请求进行计数。

[Amazon Cognito](https://aws.amazon.com/cognito/) 使用 OAuth 2.0 客户端凭证流处理身份验证。令牌中的范围决定调用者可以访问哪些代理。当客户端进行身份验证时，他们会收到包含“billing:read”或“support:write”等范围的 JWT。授权者在权限表中查找这些范围以确定客户端可以联系哪些代理。

[AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) 存储后端凭证。当 Proxy Lambda 需要通过后端代理进行身份验证时，它会通过 Amazon 资源名称 (ARN) 检索 OAuth 客户端密钥。机密不存储在 DynamoDB 中。对于语义搜索，代理描述使用 Amazon Titan Text Embeddings 嵌入并存储在 [Amazon S3 Vectors](https://aws.amazon.com/s3/features/vectors/) 中。这允许客户端使用自然语言查询而不是精确的名称匹配来发现代理。

### 网关设计

A2A 本机端点遵循 A2A 协议规范并路由到后端代理。网关支持规范中定义的两种协议绑定。 JSON-RPC 每个代理使用一个端点，并在请求正文中使用方法：

- GET /agents/{agentId}/.well-known/agent-card.json – 获取代理功能。
- POST /agents/{agentId} 并带有 `{"method": "SendMessage", ...}` （用于缓冲响应）。
- POST /agents/{agentId} 并带有 `{"method": "SendStreamingMessage", ...}`（用于 SSE 流）。

对于喜欢 RESTful URL 的客户端，还支持 HTTP+JSON/REST 绑定。

这些端点完全符合 A2A 协议。客户端指向网关 URL，而不是单独的后端 URL。然而，A2A 本机端点本身并不能解决管理问题。客户仍然需要一种方法来发现存在哪些代理、按功能搜索代理以及管理代理生命周期。

网关端点提供这一层：

- GET /agents – 列出呼叫者可以访问的代理。
- POST /search – 代理的语义搜索。
- POST /admin/agents/register – 注册新的后端代理。
- POST /admin/agents/{agentId}/sync – 刷新缓存的代理卡。
- POST /admin/agents/{agentId}/status – 激活或停用代理。

每个请求都遵循相同的路径。客户端发送授权标头中包含 JWT 的请求。 API Gateway 调用 Lambda 授权方，该授权方验证 JWT 并在权限表中查找调用方的范围。授权者返回允许或拒绝特定代理访问的 IAM 策略。如果允许，请求将路由到适当的 Lambda：用于 A2A 流量的代理、用于代理发现的注册表、用于语义查询的搜索或用于管理操作的管理员。对于 A2A 请求，Proxy Lambda 使用 OAuth 向后端进行身份验证并转发请求。未经授权的请求会被 API Gateway 拒绝，并且不会到达后端 Lambda。

#### 三层模型随着代理部署的增长，团队需要了解可用的内容。管理层提供了一个集中式注册表，其中对代理的功能、后端 URL 和状态进行了编目。部署新代理后，它会在网关中注册一次，并立即被授权客户端发现。注册表还缓存代理卡，因此客户端不需要单独从每个后端获取功能。缓存卡的 URL 被重写为通过网关指向，因此客户端与单个网关域交互，而不是发现后端 URL。对于较大的部署，语义搜索允许客户通过描述他们需要的内容而不是知道确切的名称来找到代理。

在企业中，并非每个客户都应该访问每个代理。控制层根据 JWT 范围强制执行细粒度的权限。当客户端进行身份验证时，其令牌包含“billing:read”或“support:admin”等范围。 Lambda 授权方将这些范围映射到权限表中的特定代理，并生成允许或拒绝 API 网关级别访问的 IAM 策略。未经授权的请求不会到达后端 Lambda。此外，速率限制是在代理级别针对每个用户、每个代理强制执行的。代理使用具有自动生存时间 (TTL) 到期功能的原子 DynamoDB 计数器跟踪请求计数，当客户端超出其配额时，返回带有 Retry-After 标头的 429。权限和速率限制是集中管理的：要授予或撤销访问权限或调整配额，您可以更新权限表，而不是修改每个代理。

执行层处理将请求实际路由到后端代理的过程。客户端连接到单个域，网关根据路径路由到适当的后端。这简化了网络配置：客户端只需到达网关，而不是打开与每个代理的连接。 Proxy Lambda 通过后端处理 OAuth 身份验证，因此客户端无需管理后端凭据。它从 Secrets Manager 检索机密、获取访问令牌并透明地转发请求。对于实时用例，代理支持 SSE 流，允许代理在生成增量响应时将其发送回客户端。

### 部署解决方案

网关完全使用 Terraform 进行部署。首先，验证您是否具备以下条件。

#### 先决条件

- [Terraform](https://developer.hashicorp.com/terraform) >= 1.5.0。
- [Python](https://www.python.org/) 3.12。
- [AWS 命令​​行界面 (AWS CLI)](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) 配置了有效凭证。
- [Docker](https://www.docker.com/)（用于构建代理 Lambda 容器）。
- 用于 Terraform 状态的 [Amazon Simple Storage Service (Amazon S3) 存储桶](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html)（可选，用于远程状态）。

[网关代码](https://github.com/aws-samples/sample-a2a-gateway/) 可在 aws-samples GitHub 存储库中获取。

克隆存储库并配置变量：```
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```使用您的区域和命名首选项编辑 terraform/terraform.tfvars：```
aws_region = "us-east-1" project_name = "a2a-gateway" environment = "poc"
```构建 Lambda 包并部署：```
./scripts/build_lambda_package.sh cd terraform terraform init terraform plan terraform apply
```Terraform 一次性创建资源：DynamoDB 表、Cognito 用户池、Amazon Elastic Container Registry (Amazon ECR) 存储库、Lambda 函数、API 网关和 IAM 角色。 Terraform 在部署过程中构建并推送代理 Lambda 容器。

### 测试解决方案

从 Terraform 输出获取网关凭据：```
GATEWAY_URL=$(terraform output -raw api_gateway_url) TOKEN_ENDPOINT=$(terraform output -raw cognito_token_endpoint) CLIENT_ID=$(terraform output -raw cognito_client_id) CLIENT_SECRET=$(terraform output -raw cognito_client_secret) PERMISSIONS_TABLE=$(terraform output -raw permissions_table_name)
```获取 JWT：```
TOKEN_RESPONSE=$(curl -s -X POST "$TOKEN_ENDPOINT" \ -H "Content-Type: application/x-www-form-urlencoded" \ -d "grant_type=client_credentials&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET") 导出 JWT=$(echo $TOKEN_RESPONSE | jq -r .access_token)
```该存储库在示例/目录中包含可部署的 A2A 示例代理：天气代理和计算器代理。它们可以使用自己的 Terraform 配置进行部署。 （可选）使用“cd Examples/terraform && terraform apply”部署它们，然后捕获它们的输出：```
# From examples/terraform after deploying the example agents WEATHER_BACKEND=$(terraform output -raw weather_agent_backend_url) WEATHER_CARD=$(terraform output -raw weather_agent_card_url) AGENT_TOKEN_ENDPOINT=$(terraform output -raw cognito_token_endpoint) AGENT_CLIENT_ID=$(terraform output -raw cognito_client_id) AGENT_CLIENT_SECRET=$(terraform output -raw cognito_client_secret)
```然后向网关注册代理（使用之前捕获的“$GATEWAY_URL”和“$JWT”）：```
curl -X POST "$GATEWAY_URL/admin/agents/register" \ -H "授权：承载 $JWT" \ -H "内容类型：application/json" \ -d '{ "agentId": "weather-agent", "name": "Weather Agent", "backendUrl": "'"$WEATHER_BACKEND"'", "agentCardUrl": "'"$WEATHER_CARD"'", "authConfig": { "type": "oauth2_client_credentials", "tokenUrl": "'"$AGENT_TOKEN_ENDPOINT"'", "clientId": "'"$AGENT_CLIENT_ID"'", "clientSecret": "'"$AGENT_CLIENT_SECRET"'", "范围": [“a2a-网关/天气：读取”] } }'
```网关实施细粒度的访问控制。必须明确向每个 OAuth 范围授予对 DynamoDB 权限表中特定代理的访问权限。

更新权限以允许您的范围访问注册代理：```
aws dynamodb put-item \ --table-name "$PERMISSIONS_TABLE" \ --item '{ "scope": {"S": "gateway:admin"}, "allowedAgents": {"L": [{"S": "weather-agent"}]}, "description": {"S": "Admin scope with access to weather agent"} }'
```发现注册代理并通过网关发送消息：```
卷曲“$GATEWAY_URL/agents”-H“授权：承载$JWT”卷曲-X POST“$GATEWAY_URL/agents/weather-agent/message：发送”\ -H“授权：承载$JWT”\-H“内容类型：application/json”\-d'{“message”：{“messageId”：“msg-001”，“角色”： "user", "parts": [{"text": "纽约的天气怎么样"}] } }'
```#### 清理

要清理解决方案，请从 /terraform 文件夹运行 terraform destroy 。 Terraform 将请求您允许删除资源。```
terraform destroy
```### 安全考虑

该网关是一个参考实现。在投入生产之前，请根据组织的安全状况检查以下需要强化的领域。

#### 后端信任模型

网关在身份验证后信任模型上运行。注册后端代理并验证 OAuth 凭据后，网关将响应直接代理给客户端，而无需进行内容检查。 A2A 消息无需修改即可代理，因此后端代理负责实现自己的提示注入防御和输入验证。在生产中，实施代理注册的批准工作流程，管理员在后端代理可供访问之前对其进行审查。将其与持续集成和持续交付 (CI/CD) 管道集成，以便在部署过程中而不是之后对代理进行审查。

#### 速率限制和配额

网关在代理层强制执行每个用户、每个代理的速率限制。每个请求都会增加 DynamoDB 中由用户、代理和分钟窗口键入的原子计数器。当客户端超出其配额时，代理会返回带有重试标头的 429，并且请求不会到达后端。计数器通过 DynamoDB TTL 自动过期，因此没有清理开销。限制与权限表中的访问控制一起配置，作为每分钟的默认请求或每个代理的覆盖，使管理员能够对使用进行精细控制。

#### 私有部署

对于需要私有基础设施的环境，网关支持可选的 [Amazon Virtual Private Cloud](https://aws.amazon.com/vpc/) (Amazon VPC) 部署模式。当您启用此模式时，Lambda 函数将在私有子网内运行。 API 网关切换到只能在 VPC 内访问的私有终端节点。 VPC 终端节点无需遍历 Internet 即可处理 AWS 服务的流量。

该网关支持创建新的 VPC 和自带 VPC。要部署到现有 VPC，请在 terraform.tfvars 中提供您的 VPC ID、子网 ID、路由表 ID 和安全组 ID：```
enable_private_deployment = true 现有_vpc_id =“vpc-0123456789abcdef0”现有_子网_ids = [“子网-aaa”，“子网-bbb”，“子网-ccc”]现有_路由表_ids = [“rtb-aaa”]现有_lambda_security_group_id =“sg-aaa”现有_vpc_endpoint_security_group_id =“sg-bbb”
```请注意，此模式使网关的基础设施私有，但您的 VPC 仍然需要出站互联网连接，以便与 Cognito 或其他外部身份提供商进行 OAuth 令牌交换。这通常通过网络地址转换 (NAT) 网关或 [AWS Transit Gateway 路由到共享出口 VPC](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/centralized-egress-to-internet.html) 来处理。 AWS 服务流量（DynamoDB、Amazon S3、Secrets Manager、S3 Vectors）通过 VPC 终端节点保持私有。只有 OAuth 令牌交换需要出站连接。如果您需要使用 Amazon Bedrock 进行语义搜索，请设置 `enable_bedrock_endpoint = true` 以添加 Amazon Bedrock Runtime VPC 终端节点。

对于在本地或其他云上运行的代理，可以通过 [AWS Direct Connect](https://aws.amazon.com/directconnect/) 或 [AWS Interconnect](https://aws.amazon.com/interconnect/multicloud/)（预览版）访问私有网关。这使得网关可以跨环境管理代理，而无需将流量暴露到公共互联网。

#### A2A服务器认证

网关使用 OAuth 2.0 客户端凭据流向后端代理进行身份验证。每个注册代理都包含其令牌 URL 和凭证，Proxy Lambda 透明地处理令牌获取。这意味着后端代理必须在启用 OAuth 身份验证的情况下部署，无论它们在何处运行。

当专门使用 Amazon Bedrock AgentCore Runtime 时，一个关键细节是：配置“customJWTAuthorizer”，并将“allowedClients”设置为您的 Cognito 客户端 ID，而不是“allowedAudience”。 Cognito 客户端凭证令牌包含“client_id”声明，但不包含标准 JWT“aud”声明。 “allowedAudience”参数验证“aud”声明，并将针对 Cognito 机器对机器 (M2M) 令牌返回 401 Unauthorized。使用“allowedClients”根据 Cognito 令牌提供的“client_id”进行验证。有关完整的身份验证选项集，请参阅 AgentCore A2A 协议合同。

＃＃＃ 结论随着组织从少数代理发展到数十或数百个代理，运营挑战从构建单个代理转变为管理它们之间的连接。点对点集成无法扩展。团队不需要知道每个代理住在哪里，管理每个代理的单独凭据，或者从头开始构建自己的发现和访问控制。

该网关为您提供了一个注册代理、控制谁可以访问代理以及路由流量的位置。由于它在协议级别运行，因此它可以跨环境管理代理：AWS 服务、第三方云、本地基础设施或其组合。 A2A 工作的后端。使用其 URL 和 OAuth 凭据注册代理，然后网关处理其余的事情。底层运行时并不重要。新代理在注册后即可被发现，并且访问控制和速率限制是集中管理的，而不是分散在后端。

A2A 协议标准化了代理之间的对话方式。网关标准化了您的组织管理通信的方式。 [完整源代码](https://github.com/aws-samples/sample-a2a-gateway) 可在 aws-samples 存储库中获取。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
