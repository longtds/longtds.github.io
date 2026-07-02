<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T02:03:10+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/structured-memory-filtering-with-metadata-in-agentcore-memory/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# AgentCore 内存中使用元数据进行结构化内存过滤 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 02:03 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | Structured memory filtering with metadata in AgentCore Memory \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/structured-memory-filtering-with-metadata-in-agentcore-memory/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在这篇文章中，您将了解元数据如何跨配置、摄取和检索工作，探索包括多代理和多租户架构在内的企业用例，并发现实施的最佳实践。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 使用 

AgentCore 内存中的元数据进行结构化内存过滤

假设您的客户支持代理询问“账单问题”，并得到技术支持票证、带有收据问题的销售对话以及账单纠纷。一旦代理积累了数周的交互历史记录，团队就会遇到检索精度墙：相似性搜索会找到语义上与该客户接近的所有内容，但不会将其范围限定到您实际需要的相关维度：问题类型、状态或时间。

[Amazon Bedrock AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html) 是一项完全托管的内存服务，使 AI 代理能够记住和回忆对话中的信息。它将代理内存记录组织到定义隔离范围（如“clients/client-123”）的命名空间中，因此每个实体的数据保持独立。您可以阅读[大规模组织代理内存：AgentCore 内存中的命名空间设计模式](https://aws.amazon.com/blogs/machine-learning/organizing-agents-memory-at-scale-namespace-design-patterns-in-agentcore-memory/) 博客，了解有关命名空间组织的更多信息。随着记忆的增长，相关信号淹没在语义相似但上下文无关的结果中，仅靠命名空间范围无法将它们分开。

元数据过滤弥补了这一差距。现在，您可以在命名空间隔离之上分层细粒度、基于属性的过滤器，这有助于在相似性搜索运行之前按优先级、部门或时间范围等业务维度确定检索范围。在我们对基于长期记忆基准（LoCoMo 式多会话对话）的 151 个问题测试集进行的评估中，它显示出改进。在所有问题类型上启用元数据过滤后，整体问答 (QA) 准确率从 40% 提高到 64%。收益集中在依赖于上下文边界的问题子集中，例如有时间限制的查找、基于优先级的过滤或部门范围的搜索。对于这些问题，准确率从 16% 跃升至 69%。在这篇文章中，您将了解元数据如何跨配置、摄取和检索工作，探索包括多代理和多租户架构在内的企业用例，并发现实施的最佳实践。

### 构建命名空间和元数据

AgentCore Memory 使用命名空间沿着主要实体边界组织和隔离内存。您将检索范围限制为特定命名空间，例如“clients/client-123/sessionABC”或“患者/患者-456”，这样您的代理就不会意外检索其他客户或患者的数据。命名空间提供了基础的隔离层。在[有关命名空间设计模式的博客](https://aws.amazon.com/blogs/machine-learning/organizing-agents-memory-at-scale-namespace-design-patterns-in-agentcore-memory/) 中了解更多相关信息。

![显示检索范围从 10,000 多条内存记录缩小到约 500 条记录的命名空间范围，然后元数据过滤器缩小到约 100 条记录，然后语义搜索返回前 10 条匹配项的漏斗图](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/19/ML-20840-1.png)

随着部署规模的扩大，命名空间内的语义搜索会遇到一些限制。考虑一个金融服务代理，每个客户都有一个命名空间，并且已经积累了六个月的交互历史。当关系经理要求客服人员回忆特定客户的“投资组合重新平衡讨论”时，命名空间会正确地确定该客户记忆的搜索范围。但结果涵盖了该客户历史记录中不同的投资策略、时间段和优先级。代理无法区分上周的高优先级重新平衡对话和三个月前的例行询问。这些信息在语义上相似，但上下文完全不同。

多租户环境清楚地说明了分层。命名空间已经为您提供了租户之间的完全数据分离。在每个租户的命名空间中，您的 IT 帮助台代理仍然需要在搜索解决模式之前过滤票证类型。命名空间是对 who 的逻辑分离。元数据过滤处理这些边界内的子分组：类别、解决状态、日期、优先级和标签。

### AgentCore 内存中的元数据

AgentCore Memory 中的元数据跨短期和长期内存运行，遵循三个阶段的生命周期：配置、摄取和检索。以下部分将介绍元数据在每个记忆层的工作原理，从短期记忆开始，然后深入到长期记忆的完整三个阶段生命周期。

#### 短期记忆中的元数据

在短期记忆层，您将基于字符串的键值对附加到事件，标记与上下文信息的交互，这些信息不是对话本身的一部分，但对于以后的检索至关重要。

短期记忆元数据支持事件上基于字符串的键值对，可用于过滤。这些标签在提取和整合过程中会进入长期记忆，成为可过滤的维度。

#### 长期记忆中的元数据

长期记忆是元数据发挥其全部影响力的地方。下面描述的三个阶段使您可以精确控制结构化上下文的声明、传播和查询方式。简而言之，您可以在配置时声明哪些键重要。在摄取过程中附加或让模型推断它们的值，并在检索时对其进行过滤。当会话中的多个事件携带相同的键时，AgentCore Memory 会使用您在“llmExtractionInstruction”中定义的解析行为将它们合并为一个值。

![三阶段元数据生命周期：第一阶段配置定义可索引键和元数据模式，第二阶段摄取通过事件驱动和批处理 API 路径附加元数据，第三阶段检索在语义搜索之前应用命名空间和元数据过滤器](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/25/ml-20840-3phase.png)

##### 第 1 阶段：配置

创建内存资源时，您可以声明要索引哪些元数据键，以便跨内存记录进行快速过滤和检索。在每个内存策略上定义元数据模式，指示 AgentCore Memory 如何提取和解析元数据值。索引键以针对查询过滤优化的格式存储，而非索引键则与内存记录一起存储以供参考。

以下内容创建具有元数据配置的客户支持内存资源：```
响应 = agentcore_client.create_memory( name="CustomerSupportMemory", eventExpiryDuration=30, indexedKeys=[{"key": "priority", "type": "STRING"}, {"key": "agent_type", "type": "STRING"}, {"key": "channel", "type": "STRING"}, {"key": "ticket_id", "type": "STRING"} ], memoryStrategies=[{ "semanticMemoryStrategy": { "name": "SupportSemanticStrategy", "description": "捕获支持交互详细信息", "namespaces": ["support/{actorId}"], "memoryRecordSchema": { "metadataSchema": [{ "key": "priority", "type": "STRING", "extractionType": "STRICTLY_CONSISTENT", "extractionType": "STRICTLY_CONSISTENT""extractionConfig": { "llmExtractionConfig": { "definition": "根据客户影响确定问题优先级。", "llmExtractionInstruction": "LATEST_VALUE", "validation": { "stringValidation": { "allowedValues": ["ritic", "high", "medium", "low"] } } } } }, { "key": "agent_type", "type": "STRING", "extractionType": "STRICTLY_CONSISTENT", "extractionConfig": { "llmExtractionConfig": { "definition": "支持代理分类。", "llmExtractionInstruction": "首选最专业的代理类型。层次结构：专家 > tier3 > tier2 > tier1 > 机器人。" } } }, { "key": "sentiment", "type": "STRING", "extractionType": "STRICTLY_CONSISTENT", "extractionConfig": { "llmExtractionConfig": { "definition": " 交互过程中的客户情绪 ", "llmExtractionInstruction": "对整体客户进行分类。基于所使用的语气和语言的情绪。", "validation": { "stringValidation": { "allowedValues": ["positive", "neutral", "negative", "frustated"] } } } } } ] } } }] )
```每个模式条目的“extractionConfig”在元数据提取期间指导大语言模型（LLM）。 “definition”字段描述了该字段代表的内容，而“llmExtractionInstruction”提供了额外的提取指导和冲突解决行为。内置的“LATEST_VALUE”操作提供基于新近度的解析，而自定义自然语言指令则处理特定于域的逻辑。可选的“validation”字段限制提取的值，例如用于 STRING 和 STRINGLIST 的“allowedValues”、用于 STRINGLIST 的“maxItems”或用于 NUMBER 的 min-max。这可以保持下游过滤的一致值。请注意（在前面的代码示例中）“sentiment”是在架构中定义的，但未声明为索引键。因此，LLM 将纯粹从对话内容中获取其值并将其填充到提取的记录中，但它不能在元数据过滤器表达式中使用。

请注意，“ticket_id”在内存级别被声明为索引键，但不包含在策略的“memoryRecordSchema”中。该键不会填充到提取的内存记录中。提取后，只有策略的“memoryRecordSchema”中定义的键才会出现在记录上。即使原始事件上存在匹配值，模式中不存在的索引键也会被忽略。如果您需要一个键出现在提取的记录上，它必须有一个架构条目。

![使用元数据代码块创建内存资源的可视化表示](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/30/image5_v2.png)

您可以在 [AgentCore 内存文档](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-memory-metadata.html) 中阅读有关配置约束的更多信息。除了配置的元数据键之外，还可以通过系统生成的“dateTimeValue”字段“x-amz-agentcore-memory-createdAt”和“x-amz-agentcore-memory-updatedAt”进行时间过滤（以考虑内存衰减，如果相关），它们支持“BEFORE”和“AFTER”运算符，而无需声明日期时间索引键。

##### 已知值的严格一致的元数据一些元数据键是组织分类符，例如“department”、“compliance_level”或“interaction_type”。这些携带的值是调用应用程序在事件创建时已经知道的，并且它们必须完全按照提供的那样落在结果内存记录上。 LLM 提取引入了这些键的可变性：同一对话可以在一条记录上生成“eng”，在另一条记录上生成“Engineering”，并且在提取过程中可能会重新推断事件提供的值。 AgentCore Memory 通过“STRICTLY_CONSISTENT”提取类型（“LLM_INFERRED”提取类型的一个选项）解决了这个问题。当以这种方式配置密钥时，事件中提供的值通过提取和合并不变地传播，并且不会向 LLM 咨询该密钥。```
"metadataSchema": [{ "key": "department", "type": "STRING", "extractionType": "STRICTLY_CONSISTENT" }, { "key": "priority", "type": "STRING", "extractionType": "STRICTLY_CONSISTENT" } { "key": "topic", "type": "STRING", "extractionType": "LLM_INFERRED" "extractionConfig": { "llmExtractionConfig": { "definition": "Primary topic of the conversation", "llmExtractionInstruction": "Identify the main topic discussed" } } } ]
````STRICTLY_CONSISTENT` 键的作用不仅仅是跳过推理。他们分区提取。共享相同值的事件总是一起提取，并与具有不同值的事件隔离，因此对于哪个值属于记录不会有任何歧义。

这种隔离也支配着整合。由一组确定性值生成的记录仅与共享这些相同值的记录合并。带有“department:“billing””的记录不会与带有“department:“engineering””的记录合并，无论它们的内容在语义上有多相似。

考虑一次支持会议，其中客户的问题涉及多个部门：```
# 事件 1：初始账单查询 agentcore_client.create_event( memoryId="mem-support-abc123", actorId="customer-123", sessionId="session-escalation-001", Payload=[{"conversational": {"role": "USER", "content": {"text": "我在企业计划的最后一张发票上看到重复的费用。"}}}], metadata={"department": {"stringValue": "billing"}, "priority": {"stringValue": "high"}} ) # 事件 2：仍在计费上下文 agentcore_client.create_event( memoryId="mem-support-abc123", actorId="customer-123", sessionId="session-escalation-001", Payload=[{"conversational": {"role": "USER", "content": {"text": "上周我们从标准层升级到企业层后出现了费用。"}}}],metadata={"department": {"stringValue": "billing"}, "priority": {"stringValue": "high"}} ) # 事件 3：升级为工程（技术根本原因）agentcore_client.create_event( memoryId="mem-support-abc123", actorId =“customer-123”，sessionId =“session-escalation-001”，payload = [{“conversational”：{“role”：“USER”，“content”：{“text”：“您的团队发现了一个配置错误，在层迁移期间触发了重复收费。”}}}]，元数据= {“department”：{“stringValue”：“engineering”}，“priority”：{“stringValue”： “高”}}）
```如果没有确定性隔离，所有三个事件将被一起提取。 LLM 可能会将“部门：“计费””、“部门：“工程””甚至“部门：“帐户管理””非确定性地分配给结果事实。在“department”上配置“STRICTLY_CONSISTENT”：

- 事件 1 和 2 共享相同的确定性值（“department=billing”、“priority=high”）并一起提取。生成的内存记录携带这些精确值。
- 事件 3 具有不同的确定性值（“department=engineering”、“priority=high”）并且是独立提取的。其记录准确地包含“部门：“工程””。

使用“department=billing”进行查询的计费代理仅检索有关重复费用和层升级的事实，而不是来自工程上下文的配置错误详细信息。合并遵循相同的分离：计费记录和工程记录不会合并，即使它们的内容在语义上相关。

这使得确定性密钥非常适合合规性隔离（HIPAA 与标准记录不会混合）、组织路由（无交叉污染的部门范围检索）以及调用应用程序在事件时知道值并需要将其准确保留在结果内存中的任何场景。

配置为“STRICTLY_CONSISTENT”的键还必须声明为内存资源上的索引键。通过元数据过滤器对索引键进行合并范围，并且该范围可以防止具有不同确定性值的记录合并。缺少确定性元数据键值的事件仍会被处理，并且该键在结果记录中根本不存在。

AgentCore 内存每个策略最多支持三个“STRICTLY_CONSISTENT”键。这些键中的每一个都会消耗内存资源上的十个索引键槽之一，并且索引键一旦添加就无法删除。如果您打算使用此功能，请提前预留时段。

##### 第 2 阶段：摄入

配置元数据架构后，下一步就是提取附加元数据的数据。元数据通过两种途径进入系统。事件驱动路径将元数据附加到事件，AgentCore Memory 通过提取和合并（基于提取指令）自动将其传播到长期内存记录中：```
# Initial contact event agentcore_client.create_event( memoryId="mem-support-abc123", actorId="customer-123", sessionId="session-001", eventTimestamp="2024-01-23T10:00:00Z", payload=[{ "conversational": { "role": "USER", "content": {"text": "I have a question about my bill"} } }], metadata={ "priority": {"stringValue": "medium"}, "channel": {"stringValue": "email"}, "ticket_id": {"stringValue": "TKT-5001"} } )
```当会话中的多个事件对同一键携带不同的值时，LLM 会使用该架构条目上的“llmExtractionInstruction”来解决冲突。例如，如果稍后的工单事件将优先级从“中”升级到“高”，则“LATEST_VALUE”指令将保留“高”优先级值（图 3）。自定义层次结构（如“agent_type”字段中的层次结构）保留处理链中最专业的代理（图 3）。请注意，只有策略的“memoryRecordSchema”中定义的元数据键才会填充到结果内存记录中。不在模式中的事件元数据键在提取过程中将被忽略。

确定性密钥遵循不同的摄取路径。您为事件提供的值就是结果记录上的值。没有 LLM 推理，也没有冲突解决，因为 AgentCore Memory 在提取之前按事件的确定性键值对事件进行分组。标记为“部门：“工程””的事件和标记为“部门：“财务””的事件按独立批次进行处理，并在这些组内进行合并。因此，带有 `compliance_level: "hipaa"` 的记录不会与标记为 `compliance_level: "standard"` 的记录合并。这就是确定性提取非常适合合规性隔离和路由密钥的原因。

如果事件到达时没有确定性键集，则该键将从该事件的分组中省略，并且在结果记录中不存在。直接写入路径（“BatchCreateMemoryRecords”和“BatchUpdateMemoryRecords”）完全绕过提取，因此“STRICTLY_CONSISTENT”提取类型对它们没有影响。直接提供元数据，就像您为这些 API 所做的那样。

![解决元数据冲突的合并规则：LATEST_VALUE 保留较新的优先级值，自定义层次结构保留最专业的 agent_type](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/19/ML-20840-3.png)

模式键生成值并不严格需要事件元数据。当架构键在原始事件上没有匹配的元数据时，LLM 使用键的定义和 llmExtractionInstruction 完全从对话内容中导出值。考虑一个具有三个键的模式；事件中没有提供这些：```
# 策略上定义的架构键 "metadataSchema": [{"key": "domain", "type": "STRING", "definition": "讨论的主要技术领域\..."}, {"key": "tags", "type": "STRINGLIST", "definition": "AWS services referenced\..."}, {"key": "priority", "type": "NUMBER", "definition": "Importance from 1 to 10\..."} ] # 使用无元数据创建的事件 agentcore_client.create_event( memoryId="mem-abc123", actorId="user-1", sessionId="session-001", Payload=[{"conversational": {"role": "USER", "content": {"text": "如何在两个账户之间设置 VPC 对等互连？"}}}] # 无元数据参数）
```提取的内存记录填充有从内容推断的所有三个字段：```
{ "content": {"text": "The user asked how to set up VPC peering across two AWS accounts."}, "metadata": { "domain": {"stringValue": "Networking"}, "tags": {"stringListValue": ["VPC"]}, "priority": {"numberValue": 7.0} } }
```验证规则仍然适用：LLM 的输出仅限于您声明的“allowedValues”，无论该值来自事件元数据还是内容推断。这种隐式提取对于仅存在于对话本身中的维度非常有用，例如主题分类、情绪或重要性，而不需要调用者在事件创建时提供它们。

对于直接内存记录创建，例如导入知识库或从外部系统摄取预处理记录，您可以显式提供元数据：```
agentcore_client.batch_create_memory_records( memoryId="mem-support-abc123", reports=[{ "requestIdentifier": "import-001", "namespaces": ["support/customer-456"], "content": {"text": "客户更喜欢电话支持来解决紧急计费问题"}, "timestamp": "2024-01-15T10:00:00Z", "metadata": { "priority": {"stringValue": "high"}, "agent_type": {"stringValue": "billing_agent"}, "channel": {"stringValue": "phone"}, "ticket_id": {"stringValue": "TKT-7890"} } }] )
```批量创建的记录上的元数据行为取决于您是否为每个记录提供可选的“memoryStrategyId”。

当提供“memoryStrategyId”时，服务会根据该策略的“memoryRecordSchema”过滤输入元数据。只有模式中定义的键才会存储在记录中。其他键会被悄悄删除，包括不在架构中的索引键和未在任何地方声明的键。这为您提供了架构强制的一致性，确保批量创建的记录与事件驱动提取生成的记录具有相同的元数据形状。

当省略“memoryStrategyId”时，服务将元数据键按原样存储在记录上的有效负载中。这包括已索引的键、策略模式中的键以及两者都不是的键。但是，只有索引键是可过滤的。尝试过滤非索引键会返回“ValidationException”。非索引键在“getMemoryRecord”和“listMemoryRecords”响应中仍然可见，但不能在过滤器表达式中使用。

##### 第三阶段：检索

通过在内存记录上建立索引和填充元数据，您现在可以将语义搜索与元数据过滤器结合起来来确定结果范围。 AgentCore Memory 使用预过滤架构：在向量相似性搜索运行之前应用元数据过滤器。这首先减少了候选集，因此 K 最近邻 (KNN) 搜索在更小、更相关的子集上运行。请注意下面的示例，其中在语义搜索与“账单问题”匹配之前，结果范围仅限于当年的高优先级记录。```
results = agentcore_client.retrieve_memory_records( memoryId="mem-support-abc123", namespace="support/customer-123", searchCriteria={ "searchQuery": "billing issues", "topK": 10, "metadataFilters": [{ "left": {"metadataKey": "priority"}, "operator": "EQUALS_TO", "right": {"metadataValue": {"stringValue": "high"}} }, { "left": {"metadataKey": "x-amz-agentcore-memory-createdAt"}, "operator": "AFTER", "right": {"metadataValue": {"dateTimeValue": "2026-01-01T00:00:00Z"}} }] } )
```请注意，在运行相似性搜索之前，如何将自定义元数据过滤器与系统生成的时间戳相结合，沿两个维度（业务优先级和新近度）压缩候选集。 AgentCore Memory 提供[多个运算符](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-memory-metadata.html#long-term-memory-metadata-query) 来涵盖常见的查询模式。

AgentCore Memory 还使用“x-amz-agentcore-memory-*”前缀添加服务生成的元数据字段，您可以使用相同的过滤器运算符进行查询，以支持无需自定义日期时间键的时间范围查询。

##### 为什么时间过滤可以带来最大的准确度增益

在我们的实验中，具有时间限制的查询显示元数据过滤的最大改进。使用“BEFORE”和“AFTER”运算符的结构化 DATETIME 过滤可将其转换为确定性索引查找，从而避免歧义。

对于非基于搜索的检索，“ListMemoryRecords”提供元数据过滤，无需语义搜索。当您需要枚举匹配特定元数据条件的记录而不是查找语义相似的内容时，这非常有用。例如，您可以列出客户的高优先级记录，或提取带有特定部门标记的记录。

以下示例列出了在特定日期之后创建的高优先级记录：```
记录= agentcore_client.list_memory_records（内存Id =“mem-support-abc123”，namespace =“support/customer-123”，metadataFilters = [{“left”：{“metadataKey”：“优先级”}，“operator”：“EQUALS_TO”，“right”：{“metadataValue”：{“stringValue”：“high”}}}，{“left”： {"metadataKey": "x-amz-agentcore-memory-createdAt"}, "operator": "之后", "right": {"metadataValue": {"dateTimeValue": "2024-01-20T00:00:00Z"}} } ] )
```### 企业用例

以下示例展示了元数据过滤如何解决跨行业的常见企业检索挑战。

#### 多租户 SaaS 应用程序

如果您运营一家为多个企业客户提供 AI 助手的 SaaS 公司，命名空间已经提供了主租户隔离，其中每个租户的内存都位于专用命名空间中，例如“/tenants/{actorId}/”。元数据在这些边界内添加细粒度过滤以添加业务维度。通过对“customer_segment”、“department”或“subscription_tier”等元数据键建立索引，您可以将检索直接映射到业务层次结构，而无需为每个组织维度维护单独的内存存储。

分层组织过滤：在租户的命名空间内，元数据支持针对特定部门、团队或项目进行深入检索。例如，当平台工程师询问认证服务问题时，只能通过“部门：“工程””和“团队：“平台””来检索记忆。这直接映射到企业组织结构图，而不需要每个组织单位单独的命名空间。

订阅层感知检索：SaaS 模型可以使用元数据来区分客户层的内存行为。企业级租户可能会获得完整的历史记录检索，而入门级租户只能获得最近内存范围内的检索（在“x-amz-agentcore-memory-createdAt”上使用“AFTER”日期时间过滤器）。这支持内存层的功能门控，而无需每层单独的基础设施。

#### 医疗保健和合规敏感领域

如果您的医疗保健 AI 代理管理跨多个部门的患者交互，则“患者/患者-123”等命名空间已经隔离了每个患者的记忆。但在单个患者的命名空间内，对“用药史”的广泛搜索会返回每个科室的结果：心脏病学、内分泌学和初级保健。通过索引“department”、“record_type”、“severity”和“symptoms”等元数据键，您的代理可以在患者命名空间内沿着多个临床维度缩小检索范围。```
results = agentcore_client.retrieve_memory_records( memoryId="mem-healthcare-001", namespace="patients/patient-123", searchCriteria={ "searchQuery": "medication history", "topK": 10, "metadataFilters": [{ "left": {"metadataKey": "department"}, "operator": "EQUALS_TO", "right": {"metadataValue": {"stringValue": "Cardiology"}} }, { "left": {"metadataKey": "symptoms"}, "operator": "CONTAINS", "right": {"metadataValue": {"stringValue": "chest pain"}} } ] } )
```“症状”字符串列表上的“包含”运算符检查列表是否包含指定的值，该值将检索范围限制为特定的临床指标。

为了合规性，元数据过滤有助于符合监管要求。

- HIPAA：部门级过滤可确保心脏病专家的查询仅检索心脏病相关记录，从而降低显示不相关临床数据的风险。
- GDPR：“x-amz-agentcore-memory-createdAt”上的元数据过滤器有助于识别保留窗口之外的记录。您可以通过“DeleteMemoryRecord”或命名空间范围的删除来处理删除。
- SOC 2：系统生成的时间戳提供可验证的线索，表明检索范围正确。您还可以为“data_classification”键（使用“PII”、“confidential”或“general”等值）建立索引，以进行敏感度感知检索。

#### 基于优先级的路由的客户支持

如果您的支持组织处理数千张票证，您需要代理根据紧急情况和升级状态对上下文进行优先级排序。元数据通过将自定义元数据过滤器与系统时间戳过滤器相结合，支持“查找过去 30 天的高优先级计费内存”等检索模式。在实时会话期间，您的代理会提取最相关的高优先级上下文，而无需费力解决已解决的低优先级问题。随着故障单从低级升级到关键级，合并规则使合并内存上的元数据与最新的升级状态而不是初始分类保持一致。

#### 金融服务和时间精度

财务数据本质上具有时间敏感性。关于“第三季度投资组合讨论”的查询必须返回第三季度特定的记录，而不是其他季度的记录。财富管理代理可以将 DATETIME 过滤与自定义元数据相结合，以精确范围检索，这有助于您避免来自其他资产类别和时间段的干扰：```
results = agentcore_client.retrieve_memory_records( memoryId="mem-wealth-001", namespace="clients/client-789", searchCriteria={ "searchQuery": "投资组合重新平衡策略", "topK": 10, "metadataFilters": [{ "left": {"metadataKey": "asset_class"}, "operator": "EQUALS_TO", "right": {"metadataValue": {"stringValue": "equities"}} }, { "left": {"metadataKey": "x-amz-agentcore-memory-createdAt"}, "operator": "之后", "right": {"metadataValue": {"dateTimeValue": "2024-07-01T00:00:00Z"}} }, { "left": {"metadataKey": "x-amz-agentcore-memory-createdAt"}, "operator": "BEFORE", "right": {"metadataValue": {"dateTimeValue": "2024-09-30T23:59:59Z"}} } ] } )
```#### 多代理系统和内存协调

随着代理系统的成熟并变得更加突出，元数据对于多个代理如何通过公共内存层共享和协调变得至关重要。

- 代理来源：在多代理工作流程中，了解哪个代理创建了内存对于信任、调试和路由至关重要。通过索引“source_agent”、“agent_role”和“workflow_step”等键，主管代理可以过滤特定代理存储的内存。例如，您可以在客户的命名空间内过滤 `source_agent: "billing_agent"` 以回答“计费代理在上次会话中得出了什么结论？”
- 代理范围内的内存可见性：在多代理管道中（分类机器人到一级代理再到专家），您可以使用元数据来控制每个代理检索哪些内存。分类机器人使用“workflow_step:“triage””写入内存。处理升级的专家通过“workflow_step：“triage””进行过滤以了解初始分类，或通过“agent_role：“tier1””来审查已经尝试过的内容，从而避免重复工作。 “agent_role”的自定义“llmExtractionInstruction”将整合记忆以反映最高专业知识的处理，而不仅仅是最近的接触。
- 检索增强生成 (RAG) 管道中的元数据门控检索：检索代理按“source_type:“knowledge_base””过滤以获取事实基础，个性化代理按“interaction_type:“preference””过滤以获取特定于用户的上下文，安全代理按“content_flag:“reviewed””过滤以获取经过审查的内容。这三个查询都查询相同的命名空间，但收到完全不同的结果集，而无需管理多个内存存储。

### 元数据模式演变

您的生产内存系统不是静态的，元数据模式需要与它们所服务的应用程序一起发展。 AgentCore Memory 通过仅添加更新模型支持模式演化。您可以根据需要向现有内存资源添加新的索引元数据键：```
agentcore_client.update_memory( memoryId="mem-support-abc123", addIndexedKeys=[{"metadataKey": "customer_segment", "metadataValueType": "STRING"} ] )
```新密钥可立即用于传入事件和内存记录。现有记录不会追溯接收新字段，但随着旧记忆与新记忆的整合，它们自然会获取新的元数据。您无法删除以前索引的键，这有助于防止意外丢失现有数据的过滤功能。随着提取需求的发展，您可以自由添加、删除或修改策略级元数据模式中的非索引键。

### 最佳实践

从代理所需的过滤维度开始。避免预先对每个可以想到的元数据字段建立索引。每个索引字段都会消耗一个索引键槽，并增加两条路径的成本：在摄取期间每次写入需要更多工作，在读取时进行查询压缩。从直接影响检索质量的三到五个键开始，并根据具体需要添加更多键。

写出清晰、具体的定义。 “definition”字段和“llmExtractionInstruction”一起是LLM接收的用于元数据提取的主要指令。不要写“工单的优先级”，而是写“根据客户影响确定问题优先级。对于影响生产的服务中断使用‘严重’，对于性能下降使用‘高’，对于功能请求使用‘中’，对于文档或外观问题使用‘低’。”

选择与域语义匹配的合并规则。对于大多数字段来说，“LATEST_VALUE”是安全的默认值，但并不总是正确的。对于支持升级工作流程中的“agent_type”，应保留最高级的代理类型，而不是最新的代理类型。自定义合并指令将表达此域逻辑。

使用验证规则约束 LLM 输出。在“validation”字段中定义“allowedValues”以强制执行受控词汇表。如果没有验证，LLM 可能会对同一概念产生“高”、“高”、“高”或“关键”，从而破坏下游过滤器匹配。

为键设计事件驱动路径，这些键的值在事件发生时已知，并且在会话中的事件中保持不变，例如“department”或“tenant_tier”。将元数据附加到事件，并让 AgentCore Memory 通过提取来传播元数据，以实现自动冲突解决和整合处理。在您已经知道正确的元数据值的情况下，为批量导入和预处理内容保留直接批处理 API 路径。在策略级别规划元数据模式。每个内存策略都可以有自己的元数据模式，允许不同的策略以不同的方式提取和处理相同的键。语义策略可能使用自定义提取指令对对话上下文的优先级进行分类，而摘要策略可能使用针对特定于摘要的元数据调整的不同定义。这种灵活性支持根据策略优化元数据处理，而不会影响共享索引密钥基础设施。

在批量创建的记录上谨慎使用“memoryStrategyId”。当您在批量创建请求中包含“memoryStrategyId”时，服务会将输入元数据过滤为仅包含该策略架构中的键，而其他键将被静默删除。这对于强制与提取生成的记录保持一致非常有用。当您省略它时，负载中的元数据将按原样存储。根据您的使用案例进行选择：模式强制的记录应类似于提取的记录，或者完全控制在外部管理元数据的批量导入。

使用非索引架构键来丰富上下文。并非每个元数据键都需要可过滤。未声明为索引键的架构键仍会填充在提取的记录中，并且在 get 和 list 响应中可见，但它们不能在过滤器表达式中使用。这对于丰富下游消费记录（例如“sentiment”、“summary_notes”或“source_url”）的元数据非常有用，而无需消耗索引的关键预算。为您主动过滤的维度保留索引键。

对您已知的值使用确定性提取。如果某个键表示代理在事件创建时具有的固定组织属性，例如“部门”、租户层或合规范围，请将其配置为“STRICTLY_CONSISTENT”并在每个事件上提供它。这保证了结果记录的精确值，并消除了 LLM 提取可能引入的归一化漂移（“eng”与“Engineering”相比）。为必须从对话内容推断的维度（例如情绪或主题）保留“llmExtractionConfig”。

避免这些反模式：- 不要对高基数自由文本字段（如描述或全名）建立索引，这些字段会使索引膨胀，而没有有用的过滤器边界。
- 不要将元数据用于每次交互时都会改变的值；元数据对于稳定或缓慢变化的属性最有效。
- 不要仅通过元数据复制命名空间隔离。没有命名空间隔离的“tenant_id”元数据字段是一种通过约定的安全模型，可以破坏任何错过的过滤器。

### 结论

AgentCore Memory 中的元数据过滤解决了基本的检索挑战。命名空间已经通过用户、租户或项目等主要实体隔离了内存。通过在命名空间范围之上分层的结构化元数据过滤，您可以在相似性匹配运行之前将代理的检索范围缩小到精确的上下文边界，从而为合规性、基于优先级的上下文管理和细粒度的组织过滤提供明显更高的准确性和实用基础。 LLM 驱动的提取避免了手动标记负担，而可配置的提取指令可大规模处理元数据传播和冲突解决。

首先，确定最直接影响用例的检索质量的三到五个过滤维度。首先使用虚拟内存资源进行概念验证 (PoC) 来测试相关策略，然后根据出现的具体需求扩展架构。以下资源提供实践指导：

- [Amazon Bedrock AgentCore 文档](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)。
- [AgentCore 内存代码示例](https://github.com/awslabs/agentcore-samples/tree/main/01-features/04-manage-context-of-your-agent/memory)。
- 关于 [Amazon Bedrock AgentCore Memory：构建上下文感知代理](https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-agentcore-memory-building-context-aware-agents/) 的博客。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
