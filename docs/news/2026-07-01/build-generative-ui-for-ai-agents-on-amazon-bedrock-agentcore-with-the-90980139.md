<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:46:17+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/build-generative-ui-for-ai-agents-on-amazon-bedrock-agentcore-with-the-ag-ui-protocol/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 使用 AG-UI 协议在 Amazon Bedrock AgentCore 上为 AI 代理构建生成 UI |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:46 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | Build generative UI for AI agents on Amazon Bedrock AgentCore with the AG-UI protocol \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/build-generative-ui-for-ai-agents-on-amazon-bedrock-agentcore-with-the-ag-ui-protocol/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

本文将介绍 AG-UI 如何集成到 Fullstack AgentCore 解决方案模板 (FAST) 中，以在 Amazon Bedrock AgentCore 上构建交互式代理前端。然后，我们展示 CopilotKit 如何通过生成 UI、共享状态和人机交互交互来扩展此功能，所有这些都部署在 Amazon Bedrock AgentCore 上。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 使用 AG-UI 协议在 

Amazon Bedrock AgentCore 上为 AI 代理构建生成 UI

人工智能代理可以做的不仅仅是聊天。通过正确的协议，代理可以在您的对话中渲染内联的交互式图表，实时更新共享画布，或暂停执行以在继续之前请求您的批准。这些交互（生成 UI、共享状态和人机交互）需要一种标准方法，让代理后端将动态事件传递给前端。

[AG-UI](https://docs.ag-ui.com/introduction)（代理-用户交互协议）是定义此标准的开放协议。它可与多个代理框架（Strands Agents、LangGraph、CrewAI）和前端库（React、Angular、Vue）配合使用。使用 AG-UI，您的代理代码和前端代码保持解耦。您为后端选择最佳框架，为前端选择最佳库，AG-UI 将它们连接起来。

[Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) 是 [Amazon Bedrock](https://aws.amazon.com/bedrock/) 生成型 AI 服务系列的一部分。 AgentCore 是一个代理平台，用于使用任何框架和任何模型安全地大规模构建、部署和操作 AI 代理。

本文将介绍 AG-UI 如何集成到 [Fullstack AgentCore 解决方案模板 (FAST)](https://github.com/awslabs/fullstack-solution-template-for-agentcore) 以在 Amazon Bedrock AgentCore 上构建交互式代理前端。然后，我们展示 [CopilotKit](https://copilotkit.ai/) 如何通过生成 UI、共享状态和人机交互交互来扩展此功能，所有这些都部署在 Amazon Bedrock AgentCore 上。

### 解决方案概述

Amazon Bedrock AgentCore Runtime 提供安全、无服务器且专门构建的托管环境，用于部署和运行 AI 代理或工具。 AgentCore Runtime 支持多种代理协议。模型上下文协议 (MCP) 将代理连接到工具，Agent2Agent (A2A) 将代理连接到其他代理，AG-UI 将代理连接到用户。当您部署具有 AG-UI 协议标志的代理容器时，AgentCore 充当透明代理。它处理身份验证（签名版本 4 [SigV4] 或通过 Amazon Cognito 的 OAuth 2.0）、会话隔离、扩展和可观测性。您的容器在端口 8080 上公开用于 AG-UI 请求的“POST /incalls”和用于健康检查的“GET /ping”。AgentCore 不加修改地传递请求。有关更多详细信息，请参阅[在 AgentCore Runtime 中部署 AGUI 服务器](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-agui.html)。

FAST 是一个可立即部署的入门项目。它将 AgentCore 运行时、网关、身份、内存和代码解释器与 React 前端和 Amazon Cognito 身份验证连接起来，所有这些均由 AWS 云开发套件 (AWS CDK) 定义。它附带了 Strands Agents、LangGraph 和 Claude Agent SDK 的代理模式。 FAST v0.4.1 添加了两个共享单个前端解析器的 AG-UI 模式（“agui-strands-agent”和“agui-langgraph-agent”）。有关 FAST 架构和部署的完整演练，请参阅[使用 Amazon Bedrock AgentCore 的全堆栈入门模板加速代理应用程序开发](https://aws.amazon.com/blogs/machine-learning/accelerate-agentic-application-development-with-a-full-stack-starter-template-for-amazon-bedrock-agentcore/)。

该解决方案有两层。 FAST 中的 AG-UI 提供了两种新的代理模式和一个处理这两种模式的前端解析器，因此前端不需要知道正在运行哪个代理框架。 CopilotKit + FAST 是一个独立示例，用 CopilotKit 替换了 FAST 的内置聊天 UI。它添加了生成式 UI（内联图表和组件）、双向共享状态（待办事项画布）和人机交互（暂停代理并等待您输入的会议安排程序）。这两层都部署在具有 Cognito 身份验证的 AgentCore Runtime、用于 MCP 工具连接的 AgentCore Gateway 和用于持久对话的 AgentCore Memory 上。![架构概述。前端通过 AG-UI 事件与 AgentCore Runtime 进行通信。 AgentCore 处理身份验证、扩展和会话隔离。代理运行时将特定于框架的事件转换为 AG-UI 协议。](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/25/ml-20863-img1.png)

架构概述。前端通过 AG-UI 事件与 AgentCore Runtime 进行通信。 AgentCore 处理身份验证、扩展和会话隔离。代理运行时将特定于框架的事件转换为 AG-UI 协议。

### 演练

本演练分为两个部分。首先，我们展示 AG-UI 模式如何在 FAST 中工作，以及单个前端解析器如何处理 Strands 和 LangGraph 后端。其次，我们部署 CopilotKit 示例来演示 AgentCore 上的生成 UI、共享状态和人机交互。

源代码：

- [FAST 存储库（具有 AG-UI 模式）](https://github.com/awslabs/fullstack-solution-template-for-agentcore)。
- [CopilotKit + FAST 示例](https://github.com/aws-samples/sample-FAST-applications/tree/main/samples/copilotkit-generative-ui)。

#### 先决条件

对于本演练，您应该满足以下先决条件：

- 具有 AWS CloudFormation、Amazon Elastic Container Registry (Amazon ECR)、Amazon Bedrock AgentCore、Amazon Cognito 和 AWS Amplify 权限的 [AWS 账户](https://signin.aws.amazon.com/signin?redirect_uri=https%3A%2F%2Fportal.aws.amazon.com%2Fbilling%2Fsignup%2Fresume&client_id=signup)。
- 安装并配置了 [AWS 命令​​行界面 (AWS CLI) v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)。
- 已安装 [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html)。
- [Node.js 18 或更高版本](https://nodejs.org/) 和 Python 3.11 或更高版本。
- Docker 正在运行，用于容器构建。
- 在 Amazon Bedrock 控制台中为代理使用的模型启用模型访问。

#### FAST 中的 AG-UI：一个解析器，两个框架

“agui-strands-agent”模式将 Strands Agent 包装在“ag-ui-strands”库中的“StrandsAgent”中。包装器自动将 Strands 流事件转换为 AG-UI 服务器发送的事件。每个请求都会使用 Gateway MCP 工具创建一个新代理。 AgentCore 内存通过会话管理器提供程序附加到每个线程，因此对话历史记录在 AgentCore 运行时扩展过程中保持不变。内存是选择加入的：当未设置“MEMORY_ID”时，提供程序返回“None”：```
# models/agui-strands-agent/agent.py from ag_ui_strands import StrandsAgent, StrandsAgentConfig from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext fromstrands import Agent app = BedrockAgentCoreApp() # 在模块加载时构建模型和代码解释器 MODEL = BedrockModel(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0") CODE_INTERPRETER = StrandsCodeInterpreterTools(REGION).execute_python_securely @app.entrypoint async def 调用(payload: dict, context: RequestContext): input_data = RunAgentInput.model_validate(payload) actor_id = extract_user_id_from_context(context) # 每个请求的新鲜代理 --- 获取调用者的身份和工具 agent = Agent( model=MODEL, system_prompt=SYSTEM_PROMPT, tools=[create_gateway_mcp_client(actor_id), CODE_INTERPRETER], session_manager=get_memory_session_manager(actor_id, session_id), ) agui_agent = StrandsAgent( agent=agent, name="agui_strands_agent", config=StrandsAgentConfig( session_manager_provider=make_memory_provider(actor_id), replay_history_into_strands=False, ), ) agui_agent.run(input_data) 中的事件异步：yield event.model_dump(mode="json", by_alias=True, except_none=True)
```“BedrockAgentCoreApp”读取 AgentCore 运行时标头（“WorkloadAccessToken”、“Authorization”、“Session-Id”）并填充上下文变量，因此网关身份验证和内存的工作方式与 HTTP 模式相同。

“agui-langgraph-agent”模式使用“copilotkit”库中的“LangGraphAGUIAgent”。它会针对每个请求构建全新的编译图，因此每次调用都会获得适用于调用者的 MCP 工具。 AgentCore 内存在这里也是选择加入的：当未设置“MEMORY_ID”时，帮助器返回“None”，因此您可以在不配置内存的情况下运行该模式：```
# patterns/agui-langgraph-agent/agent.py from copilotkit import CopilotKitMiddleware, LangGraphAGUIAgent async def build_graph(actor_id: str): """Build a fresh LangGraph compiled graph with Gateway tools.""" mcp_client = await create_gateway_mcp_client(actor_id) tools = await mcp_client.get_tools() tools.append(CODE_INTERPRETER) return create_agent( model=MODEL, tools=tools, checkpointer=get_memory_saver(), # None when MEMORY_ID is unset middleware=[CopilotKitMiddleware()], system_prompt=SYSTEM_PROMPT, ) @app.entrypoint async def invocations(payload: dict, context: RequestContext): input_data = RunAgentInput.model_validate(payload) actor_id = extract_user_id_from_context(context) graph = await build_graph(actor_id) agui_agent = LangGraphAGUIAgent( name="agui_langgraph_agent", graph=graph, config={"configurable": {"actor_id": actor_id}}, ) async for event in agui_agent.run(input_data): yield event.model_dump(mode="json", by_alias=True, exclude_none=True)
```两种模式都会产生相同的 AG-UI 事件。该协议定义了服务器发送事件的类型化事件流。例如，单个工具调用会产生以下序列：```
数据：{“type”：“RUN_STARTED”，“threadId”：“t1”，“runId”：“r1”}数据：{“type”：“TEXT_MESSAGE_START”，“messageId”：“m1”，“role”：“助理”}数据：{“type”：“TEXT_MESSAGE_CONTENT”，“messageId”：“m1”，“delta”：“让我检查一下"} 数据：{"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "给你的。"} 数据: {"type": "TEXT_MESSAGE_END", "messageId": "m1"} 数据: {"type": "TOOL_CALL_START", "toolCallId": "tc1", "toolCallName": "get_weather"}数据: {"type": "TOOL_CALL_ARGS", "toolCallId": "tc1", "delta": "{\"location\": \"西雅图\"}"} 数据: {"type": "TOOL_CALL_END", "toolCallId": "tc1"} 数据: {"type": "TOOL_CALL_RESULT", "toolCallId": "tc1", "content": “{\”temp\”：55}”}数据：{“type”：“RUN_FINISHED”，“threadId”：“t1”，“runId”：“r1”}
```前端解析器将每个事件映射到前端操作：```
// frontend/src/lib/agentcore-client/parsers/agui.ts export const parseAguiChunk: ChunkParser = (line, callback) => { if (!line.startsWith("data: ")) return; const json = JSON.parse(line.substring(6).trim()); switch (json.type) { case "TEXT_MESSAGE_CONTENT": callback({ type: "text", content: json.delta ?? "" }); break; case "TOOL_CALL_START": callback({ type: "tool_use_start", toolUseId: json.toolCallId, name: json.toolCallName }); break; case "TOOL_CALL_RESULT": callback({ type: "tool_result", toolUseId: json.toolCallId, result: json.content ?? "" }); break; case "RUN_FINISHED": callback({ type: "result", stopReason: "end_turn" }); } };
```与 HTTP 模式相比，Strands、LangGraph 和 Claude-agent-sdk 都需要一个单独的解析器来处理不同的流格式。使用AG-UI，后端框架被抽象出来。您可以在配置中将“agui-strands-agent”替换为“agui-langgraph-agent”，并且前端不会改变。

要部署，请在“infra-cdk/config.yaml”中设置模式并运行 CDK：```
后端：模式：agui-strands-agent＃或agui-langgraph-agent部署类型：docker
``````
cd infra-cdk cdk deploy --require-approval never python3 ../scripts/deploy-frontend.py
```#### CopilotKit + FAST：生成式 UI、共享状态和人机交互

基本的 FAST 前端提供了功能性聊天界面，但 AG-UI 支持更丰富的交互：代理呈现自定义 UI 组件、与前端同步状态以及在执行过程中暂停以等待用户输入。 CopilotKit 是专门为这些模式构建的 React 库。 CopilotKit 团队在 FAST 之上构建了一个[示例应用程序](https://github.com/aws-samples/sample-FAST-applications/tree/main/samples/copilotkit-generative-ui)，在 AgentCore 上演示了这些功能。它包括 LangGraph 和 Strands 代理模式，您可以在部署时选择一种模式。

生成式 UI 涵盖从高前端控制到高代理自由度的范围。该示例位于受控端：前端拥有预构建的 React 组件，代理选择要渲染的组件并通过 AG-UI 事件提供数据。进一步沿着这个范围，代理返回前端呈现的声明性 UI 描述，或前端嵌入的完整 UI 表面。 AG-UI 承载了这三者，因为它标准化了事件和状态流而不是 UI 本身。您给予代理的自由度越大，您承担的责任就越多：开放式表面需要沙箱和输入验证。

![CopilotKit 示例架构。 CopilotKit 运行时 Lambda 充当浏览器和 AgentCore 运行时之间的服务器端桥梁，处理 AG-UI 事件解析、生成 UI 路由和身份验证转发。](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/25/ml-20863-img2-2.png)

CopilotKit 示例架构。 CopilotKit 运行时 Lambda 充当浏览器和 AgentCore 运行时之间的服务器端桥梁，处理 AG-UI 事件解析、生成 UI 路由和身份验证转发。

##### 生成式 UI：代理渲染 React 组件

借助 CopilotKit，代理可以在聊天中内联呈现自定义 React 组件，而不仅仅是文本。前端注册代理可以通过 AG-UI 工具调用事件调用的组件：```
// 注册代理可以渲染的饼图 useComponent({ name: "pieChart", description: "将数据显示为饼图。",parameters: PieChartPropsSchema, render: PieChart, });
```当代理调用“pieChart”工具时，CopilotKit 会拦截“TOOL_CALL_START”和“TOOL_CALL_ARGS”事件，并直接在对话中呈现“PieChart”组件。代理首先调用“query_data”工具从示例逗号分隔值 (CSV) 文件中获取数据，然后将结果传递到图表组件。

##### 共享状态：与代理同步的待办事项画布

该示例包括一个待办事项画布，该画布在代理和 UI 之间保持双向同步。当您告诉代理“添加三个任务：设计 API、编写测试并部署到暂存”时，代理会调用“manage_todos”，并通过 AG-UI“STATE_SNAPSHOT”事件实时更新画布。您还可以直接在 UI 中编辑待办事项。代理会在下一回合看到更新的状态，因为 Strands 模式将当前待办事项注入系统提示符中：```
def state_context_builder(state: dict) -> str: todos = state.get("todos", []) if todos: return f"\nCurrent todos:\n{json.dumps(todos, indent=2)}" return ""
```##### 人机交互：代理暂停并等待

该示例演示了一个会议安排程序，其中代理在执行过程中暂停并呈现时间选择器。用户选择时间，代理继续该选择：```
useHumanInTheLoop({ name: "scheduleTime", description: "安排与用户的会议。",parameters: z.object({ ReasonForScheduling: z.string(), meetDuration: z.number(), }), render: ({ respond, status, args }) => ( <MeetingTimePicker status={status} respond={respond} {...args} /> ), });
```这是通过 AG-UI 的工具调用流程实现的：代理为“scheduleTime”发出“TOOL_CALL_START”，CopilotKit 渲染选择器而不是执行后端工具，用户的响应作为“TOOL_CALL_RESULT”返回。

##### 部署 CopilotKit 示例

克隆 FAST Samples 存储库并部署：```
git clone https://github.com/aws-samples/sample-FAST-applications.git cd sample-FAST-applications/samples/copilotkit-generative-ui cp config.yaml.example config.yaml # Edit config.yaml --- set stack_name_base and admin_user_email ./deploy-langgraph.sh # or ./deploy-strands.sh
```部署脚本配置完整堆栈：Amazon Cognito 用户池、Amazon ECR 存储库、AgentCore 运行时、AgentCore Gateway、AgentCore 内存、带有 Amazon API Gateway 的 CopilotKit 运行时 Lambda 以及 AWS Amplify 托管。完成后，打开最后打印的 Amplify URL 并登录。您将进入 CopilotKit 聊天界面，其中进行了一些快速检查以确认部署是否有效：

- 向代理索要样本数据中的饼图。它在对话中呈现内联。
- 要求将三个任务添加到待办事项画布中。画布实时更新。
- 要求安排会议。代理暂停并显示时间选择器。

#### 清理

本演练部署了两个独立的堆栈。拆除您部署的任何一个，这样它们就不再产生费用。

要删除 FAST 部署：```
cd infra-cdk npx cdk destroy --all
```要删除 CopilotKit 示例：```
cd sample-FAST-applications/samples/copilotkit-generative-ui npx cdk destroy --all
```如果 Amazon ECR 存储库仍然保存容器映像，请手动将其删除，因为某些 CDK 配置会将存储库保留在适当的位置。

### 结论

本文展示了如何使用 AG-UI 协议在 Amazon Bedrock AgentCore 上构建交互式代理前端。 FAST 中的 AG-UI 集成使您可以在 Strands 和 LangGraph 代理后端之间进行交换，而无需更改前端代码。 CopilotKit 示例通过生成 UI、共享状态和人机交互交互来扩展此功能，所有这些都在具有托管身份验证、扩展和内存的 AgentCore 上运行。

要了解更多信息，请探索以下资源：

- [FAST 存储库](https://github.com/awslabs/fullstack-solution-template-for-agentcore)：使用“pattern: agui-strands-agent”或“pattern: agui-langgraph-agent”克隆并部署 AG-UI 模式。
- [CopilotKit 生成式 UI 示例](https://github.com/aws-samples/sample-FAST-applications/tree/main/samples/copilotkit-generative-ui)：在 AgentCore 上尝试生成式 UI、共享状态和人机交互。
- [AgentCore AG-UI 文档](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-agui.html)：完整的协议合同和部署详细信息。
- [AG-UI协议规范](https://docs.ag-ui.com/concepts/overview)：核心事件类型和协议设计。
- [CopilotKit 文档](https://docs.copilotkit.ai/)：生成式 UI 的前端集成指南。

如果您有疑问或反馈，请在 [FAST 存储库](https://github.com/awslabs/fullstack-solution-template-for-agentcore/issues) 或 [FAST 示例存储库](https://github.com/aws-samples/sample-FAST-applications/issues) 中提出问题。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
