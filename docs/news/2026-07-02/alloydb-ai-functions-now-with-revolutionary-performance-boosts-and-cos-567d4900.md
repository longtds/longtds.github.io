<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T02:00:00+08:00
source: Google Cloud Blog
domain: AI 基础设施
url: https://cloud.google.com/blog/products/databases/boost-performance-and-lower-costs-with-alloydb-ai-functions/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 利用 AlloyDB AI 功能提升性能并降低成本 |谷歌云博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 02:00 CST |
| 领域 | AI 基础设施 |
| 来源 | Google Cloud Blog |
| 原文标题 | Boost Performance and Lower Costs with AlloyDB AI Functions \| Google Cloud Blog |
| 原文 | [打开原文](https://cloud.google.com/blog/products/databases/boost-performance-and-lower-costs-with-alloydb-ai-functions/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

AlloyDB 是一个人工智能原生数据库——它不仅仅是一个被动的数据存储，它可以智能地理解和处理您的数据。借助 AlloyDB，您可以获得业界领先的向量和混合搜索、近乎 100% 准确的自然语言到 SQL 功能来构建会话代理、使您能够使用所选代理 IDE 进行构建的工具，以及通过 AI 功能将 Gemini 等基础模型的智能直接引入您的数据的能力。在这篇博文中，我们讨论了人工智能功能处理方面的巨大突破以及一系列全新的人工智能功能。但首先：人工智能功能到底是什么？他们将 Gemini 的世界知识带入您的 AlloyDB 数据中。考虑一下管理原始用户反馈的挑战：它是非结构化的，并且难以解析。在利用这些数据进行搜索之前，可能需要进行预处理和实体提取。您无需维护复杂的自定义知识提取管道，而是可以直接在 AlloyDB 中使用 Gemini 的生成功能，将原始文本转换为结构化、可搜索的见解。例如，以下是如何使用 ai.generate 将原始反馈立即转换为干净、结构化的 JS

## 正文

数据库

##

AlloyDB 

AI 函数

- 现在具有革命性的性能提升和成本节省

2026 年 7 月 2 日

###### 达莎娜·西瓦库玛

集团产品经理

###### 普什卡·哈迪卡

软件工程师

###### 立即尝试 

Gemini Enterprise 商业版

[AlloyDB](https://cloud.google.com/products/alloydb) 是一个人工智能原生数据库——它不仅仅是一个被动的数据存储，它可以智能地理解和处理您的数据。借助 AlloyDB，您可以获得业界领先的矢量和混合搜索、近乎 100% 准确的[自然语言到 SQL 功能](https://cloud.google.com/blog/products/databases/introducing-querydata-for-near-100-percent-accurate-data-agents?e=48754805) 来构建会话代理、使您能够[使用您选择的代理 IDE 进行构建](https://cloud.google.com/blog/products/databases/managed-mcp-servers-for-google-cloud-databases?e=48754805) 的工具，以及通过 [AI 函数](https://docs.cloud.google.com/alloydb/docs/ai/evaluate-semantic-queries-ai-operators) 将 Gemini 等基础模型的智能直接引入您的数据的能力。

在这篇博文中，我们讨论了人工智能功能处理方面的巨大突破以及一系列全新的人工智能功能。

但首先：人工智能功能到底是什么？他们将 Gemini 的世界知识带入您的 AlloyDB 数据中。考虑一下管理原始用户反馈的挑战：它是非结构化的，并且难以解析。在利用这些数据进行搜索之前，可能需要进行预处理和实体提取。您无需维护复杂的自定义知识提取管道，而是可以直接在 AlloyDB 中使用 Gemini 的生成功能，将原始文本转换为结构化、可搜索的见解。例如，以下是如何使用“ai.generate”立即将原始反馈转换为干净、结构化的 JSON（请参阅[此处](https://medium.com/google-cloud/sql-in-the-gemini-era-bringing-gemini-3-0-to-your-data-with-alloydb-ai-3c5ab775ab31) 的更多示例）：

正在加载...SELECT log_id, raw_content, -- 使用 Gemini 3.0 对原始用户反馈进行推理并提取结构 ai.generate( model_id => 'gemini-3.1-pro-preview', Prompt => '分析此原始客户反馈条目。提取国家/地区、服务名称和反馈的 1 句话摘要。以 JSON 形式返回。' || raw_content) AS Structured_feedback FROM raw_feedback_logs WHERE user_type <> '内部';

这是一个示例结果：

|日志ID |原始内容 |结构化分析 |
|:---|:---|:---|
| 1001 | 1001 2025-12-16 08:00:01 [错误] 服务：OrderSvc \| DbConnectionTimeout：5000 毫秒后无法从池“primary-shard-04”获取连接。 | {"errorCode": "DbConnectionTimeout", "serviceName": "OrderSvc", "rootCause": "服务未能在 5000 毫秒超时限制内从主分片池获取数据库连接。"} |
| 1002 | 1002 2025-12-16 08:05:12 [警告] 服务：IdentityProvider \| 401 未经授权：user_id=9942 的承载令牌验证失败。签名不匹配。 | {“error_code”：“401”，“service_name”：“IdentityProvider”，“root_cause”：“由于签名不匹配，不记名令牌验证失败。” } |
| 1003 | 1003 2025-12-16 08:12:45 [关键] 服务：AnalyticsEngine \| OutOfMemoryError：Java 堆空间。 1.2GB 阵列分配失败。堆使用率 99%。 | { "error_code": "OutOfMemoryError", "service_name": "AnalyticsEngine", "root_cause": "服务在尝试分配 1.2GB 数组时耗尽了可用的 Java 堆内存。" } |
| 1004 | 1004 2025-12-16 08:25:33 [错误] 服务：WebFrontEnd \| 404 NotFound：未找到资源 /api/v3/users/profile/settings。上游返回 404。 { "error_code": "404", "service_name": "WebFrontEnd", "root_cause": "上游服务找不到为用户配置文件设置请求的 API 资源。" } |
| 1005 | 1005 2025-12-16 08:35:50 [警告] 服务：NotificationGateway \| GatewayTimeout：外部提供商“SendGrid”未能在 30 秒内响应。已安排重试。 | {"error_code": "GatewayTimeout", "service_name": "NotificationGateway", "root_cause": "外部提供商 SendGrid 未能在 30 秒超时限制内响应。"} |

#### 更多总结和分析情绪的功能我们的核心人工智能功能——“ai.generate”、“ai.rank”、“ai.if”和“ai.forecast”——现已全面可用。要了解有关前三个用例的更多信息，请参阅此[博客文章](https://medium.com/google-cloud/sql-in-the-gemini-era-bringing-gemini-3-0-to-your-data-with-alloydb-ai-3c5ab775ab31)。要探索实际的预测函数，请查看此[深入探讨](https://cloud.google.com/blog/products/data-analytics/timesfm-models-in-bigquery-and-alloydb)。

在此势头的基础上，我们推出了三个全新的函数：“ai.summarize”、“ai.agg_summarize”和“ai.analyze_sentiment”。

-

`ai.analyze_sentiment`：自动将文本的情绪基调分类为积极、消极或中性。

-

`ai.summarize`：将冗长的文本压缩为其最重要的信息，同时保留原始语气和细微差别。

-

`ai.agg_summarize`：一种聚合工具，用于处理列中的多行，为整个组生成单个统一的摘要（例如，通过 `GROUP BY` 子句）。

以下是如何使用“ai.agg_summarize”来整合零售网站上产品的产品评论的示例：

加载中...

选择产品名称，ai.agg_summarize(review) 作为reviews_summary GROUP BY 产品名称；

以下是两种游戏机产品的总结评论结果示例：

|产品名称 |评论摘要 |
|:---|:---|
| AlphaCore 控制台 |用户称赞令人惊叹的 4K 图形、流畅的 120Hz 帧速率以及高度符合人体工程学的控制器设计。然而，一些评论对长时间游戏过程中冷却风扇的巨大噪音表示沮丧。总体而言，尽管有轻微的散热和噪音投诉，但它被认为是顶级控制台。 |
| NeoCore 控制台 |客户喜欢其卓越的电池续航时间和充满活力的 OLED 显示屏，适合随时随地进行手持游戏。大量用户指出，用户界面可能会感觉迟缓，并且游戏库目前有限。它对于休闲游戏玩家来说具有巨大的价值，但高级用户可能会发现性能不足。 |

#### 法学硕士对数据的影响力：

现在速度更快、成本更低我们现在在AI功能处理方面实现了前所未有的性能和成本突破。以前，为大型数据库中的每一行运行基础模型调用会带来成本和延迟限制。我们通过引入两项突破性功能打破了这些障碍：

[AI 函数智能批处理](https://docs.cloud.google.com/alloydb/docs/ai/accelerate-ai-queries)：此 AI 函数加速功能提供 AI 函数调用的智能批处理，以实现最佳性能和质量。这种效率是通过消除重复的提示开销来实现的； LLM 的样板指令每批次传输一次，而不是在每一行中重复传输。您可能有一个问题 - “为什么不在我自己的应用程序层中执行此操作？”。这是因为，AlloyDB 会智能地确定正确的批量大小以获得最佳结果 - 如果您低估批量大小，您将不会获得成本和延迟方面的收益，如果您高估批量大小，LLM 的提示可能会变得臃肿并导致幻觉，或者您可能会超出模型的令牌限制。除了计算每个请求的完美批量大小之外，AlloyDB 还可以开箱即用地自动处理重试，确保您的管道保持弹性。我们在内部做了一些测试并看到了巨大的成果；例如，与传统的一次行 LLM 调用相比，性能提升高达 2,400 倍（每秒处理 10,000 行）。目前可用于 ai.if 和 ai.rank 函数，并支持未来的其他函数。

让我们看一个使用智能批处理/加速与 ai.if 来解决此用例的示例：想象一下，一位客户在小工具零售网站上搜索可以处理“60 米或更深”水下深度的相机。传统的混合搜索将拉出最接近的语义和全文匹配，但它忽略了数字数据的硬约束——这意味着它可能提供只能在 20 米深度工作的相机。通过使用 AlloyDB 基于 ai.if 的智能过滤，数据库实际上可以理解深度的细微差别，并使查询返回满足或超过 60 米深度标准的产品。请注意，在下面的示例中，您不需要指定批处理大小 - AlloyDB 在使用 ai.if 时会在幕后处理所有优化。

加载中...-- 智能批处理/AI 函数加速 SET google_ml_integration.enable_ai_function_acceleration = on; SELECT Productid, Productname, Category,description FROM products AS p WHERE ai.if( '评估产品描述是否表明该产品防水深度为 60m 或更深。描述：' || description);

这是假设的小工具网站上的示例结果。请注意产品的扩展描述如何真正符合 60 米深度工作的标准：

![https://storage.googleapis.com/gweb-cloudblog-publish/images/1_7d1Ppqp.max-1100x1100.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/1_7d1Ppqp.max-1100x1100.jpg)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/1_7d1Ppqp.max-1100x1100.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/1_7d1Ppqp.max-1100x1100.jpg)

[优化的 AI 功能](https://docs.cloud.google.com/alloydb/docs/ai/accelerate-queries-optimized-functions)：为了提高效率，我们引入了优化模式，从 ai.if 开始。通过部署一个小型代理模型，该模型利用您的嵌入并根据您的特定 LLM 输出进行训练，我们可以在数据库中本地处理决策。这大大减少了致电外部法学硕士的需要——并且根据我们的一些内部测试，我们看到了惊人的收益；例如，每秒处理多达 100,000 行（提高了 23,000 倍），成本削减了 6,000 倍（降至 1/10 美分）。有关此技术的技术见解，包括何时效果最佳、何时效果不佳，请参阅此[博客文章](https://cloud.google.com/blog/products/data-analytics/more-than-100x-faster-and-cheaper-llm-powered-sql-queries-with-proxy-models?e=48754805)。 AlloyDB 在使用优化的 ai.if 时执行以下操作：

-

训练代理模型：AlloyDB 在数据样本上训练轻量级代理模型。当您将 PREPARE 语句与 ai.if 函数结合使用来训练优化查询的模型时，这种情况会在后台发生。

-

执行查询：当您使用 EXECUTE 语句时，AlloyDB 使用经过训练的代理模型在本地处理查询。

-

回退到 LLM：如果模型的准确性较低，或者 AlloyDB 找不到模型，AlloyDB 会自动回退到使用 LLM。让我们看一下使用优化的 ai.if 搜索能够处理 60 米或更深水下深度的相机的相同示例。在这里，我们使用 PREPARE 语句训练代理模型，然后执行该语句。

加载中...

-- 准备优化函数/代理模型 PREPARE Waterproof_camera_60m AS SELECT ProductID, ProductName, Category, Description FROM products AS p WHERE ai.if( '评估产品描述是否表明产品防水深度为 60m 或更深。Description:' || description, description_embedding); -- 运行代理模型 EXECUTE Waterproof_camera_60m;

您会看到真正符合 60 米深度工作标准的相同产品 - 如上面的屏幕截图所示。这是前三种产品的表格版本，因此您可以更仔细地查看说明：

|产品名称 |描述 |
|:---|:---|
|脉冲运动相机 MZ314 |使用这款相机征服您的下一次冒险。不要让自然因素阻碍你；凭借其抗震、适合冒险的底盘，可潜入 60 米深或承受崎岖的路径。每一次跳跃、每一次转弯、每一次飞溅都通过先进的地平线锁定稳定性呈现完美平滑，确保您的镜头以无与伦比的流畅性讲述故事。 |
|超字节运动相机LG688 |即使在动作最激烈的时候，也能以令人惊叹的细节捕捉世界。这款相机将强大的 1 英寸传感器封装在极其坚固的口袋大小的框架中。拍摄令人惊叹的 5K 视频和清晰的 20MP 静态照片，可与专业设备相媲美。 60 米的坚固防水性能比以往任何时候都潜得更深。 |
| Alphasync 运动相机 WW897 |这款功能强大的紧凑型相机能够摆脱恶劣天气的影响，而巨大的 1 英寸传感器将每一个令人惊叹的时刻转化为令人惊叹的 5K 视频和水晶般清晰的 20MP 静态照片。凭借 60 米防水和革命性的 Horizo​​n Lock，征服任何环境 - 从最深的潜水到最高峰，确保您的镜头保持难以置信的稳定。 |

#### 看看它的实际效果！

在此[演示视频](https://www.youtube.com/watch?v=PxbLWePxt40&feature=youtu.be) 中观看这一切是如何结合在一起的。![https://storage.googleapis.com/gweb-cloudblog-publish/images/2_gLOlS0A.max-1900x1900.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/2_gLOlS0A.max-1900x1900.png)

#### 入门很简单

准备好为您的 AI 工作负载带来前所未有的速度和成本效益了吗？

-

AlloyDB 新手？通过 [30 天免费试用](https://docs.cloud.google.com/alloydb/docs/free-trial-cluster) 探索 AlloyDB。

-

AI 函数快速入门：启用[一些快速先决条件](https://docs.cloud.google.com/alloydb/docs/ai/evaluate-semantic-queries-ai-operators) 并开始直接在 SQL 查询中调用 ai.if、ai.generate 或 ai.analyze_sentiment 等函数。请先查看这些[实际示例](https://medium.com/google-cloud/sql-in-the-gemini-era-bringing-gemini-3-0-to-your-data-with-alloydb-ai-3c5ab775ab31)。

-

提升性能并优化成本：要实现最大的性能和成本收益，请遵循我们的[优化功能](https://docs.cloud.google.com/alloydb/docs/ai/accelerate-queries-optimized-functions) 指南。该功能已在 ai.if 预览版中提供，并将很快扩展到更多功能。有关此技术的技术见解，包括何时效果最佳、何时效果不佳，请参阅此[博客文章](https://cloud.google.com/blog/products/data-analytics/more-than-100x-faster-and-cheaper-llm-powered-sql-queries-with-proxy-models?e=48754805)。

-

扩展吞吐量：使用[智能批处理](https://docs.cloud.google.com/alloydb/docs/ai/accelerate-ai-queries) 加速 AI 函数（可在 ai.if 和 ai.rank 预览版中使用）或[基于数组的函数](https://docs.cloud.google.com/alloydb/docs/ai/evaluate-semantic-queries-ai-operators#filter-batch-arrays)（通常适用于所有基于 LLM 的 AI 函数）以顺利处理批量提示。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
