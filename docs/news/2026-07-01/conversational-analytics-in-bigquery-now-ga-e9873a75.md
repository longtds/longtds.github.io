<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T02:00:00+08:00
source: Google Cloud Blog
domain: AI 基础设施
url: https://cloud.google.com/blog/products/data-analytics/conversational-analytics-in-bigquery-now-ga/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# BigQuery 中的对话式分析现已正式发布 |谷歌云博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 02:00 CST |
| 领域 | AI 基础设施 |
| 来源 | Google Cloud Blog |
| 原文标题 | Conversational Analytics in BigQuery now GA \| Google Cloud Blog |
| 原文 | [打开原文](https://cloud.google.com/blog/products/data-analytics/conversational-analytics-in-bigquery-now-ga/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

企业需要快速做出决策，但掌握答案的团队往往被积压的日常请求所淹没，导致用户排队等待他们现在需要的见解。今天，我们将 BigQuery 中的对话式分析全面推出，以便业务和技术团队可以在数据所在的位置查询数据、运行多步骤分析并使用自然语言生成可视化报告。在此版本中，BigQuery 中的对话式分析现在提供了一个代理，该代理的行为就像分析师一样，了解您的业务、在回答之前进行思考并支持其工作。它建立在 Google 最新的 Gemini 模型和 BigQuery 的安全、受监管的基础之上，带来

## 正文

数据分析

##

BigQuery 中的对话式分析为每个人带来了可信的代理推理

2026 年 7 月 1 日

###### 瓦西娅·克里希南

产品负责人

###### 吴家勋

高级工程经理

###### 立即尝试 

Gemini Enterprise 商业版

企业需要快速做出决策，但掌握答案的团队往往被积压的日常请求所淹没，导致用户排队等待他们现在需要的见解。今天，我们将 BigQuery 中的对话式分析全面推出，以便业务和技术团队可以在数据所在的位置查询数据、运行多步骤分析并使用自然语言生成可视化报告。在此版本中，BigQuery 中的对话式分析现在提供了一个代理，该代理的行为就像分析师一样，了解您的业务、在回答之前进行思考并支持其工作。它建立在 Google 最新的 Gemini 模型和 BigQuery 安全、受监管的基础之上，为组织中的每个人带来值得信赖的分析师。

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/GAGif.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/GAGif.gif)

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/GAGif.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/GAGif.gif)

图 1. BigQuery 中的对话式分析

#### 企业数据的对话式分析

BigQuery 的对话功能是内置的，无需设置即可立即使用。

为了获得更深入、更一致的见解，数据专业人员可以根据重要的确切来源（从项目、数据集和表格到视图、图表和用户定义的函数）编写专门的代理。由于您的数据很少驻留在一个地方，会话分析的范围不仅限于本机 BigQuery 表，还包括 Lakehouse 管理的 Apache Iceberg 表以及 Databricks Unity、AWS Glue、SAP 和 Salesforce 等跨云 Lakehouse 源，因此您可以通过单个对话打破数据孤岛并跨云分析数据。作为数据从业者，您可以在 BigQuery Studio 和 Data Canvas 中使用对话式分析，并通过对话式分析 API 将您构建的代理发布到 Gemini Enterprise、Data Studio 或您自己的应用程序，将它们交给业务用户（无论他们在哪里工作）。

“在 MoneySuperMarket，BigQuery 对话式分析改变了我们团队获取洞察的方式。过去需要数周时间的分析现在只需几分钟即可完成，这为我们的财务分析师每周节省了大约半天的时间。通过使分析更加自助，我们正在帮助团队更快地获得洞察，以支持更好的产品和商业决策。” - Suzie Millar，Mony Group 数据主管

#### 精心设计的信任和可解释性

会话分析的准确性是设计使然，而不是愿望：每个代理都基于您的业务环境，而不是模型的假设。该上下文来自 [知识目录](https://cloud.google.com/blog/products/data-analytics/introducing-the-google-cloud-knowledge-catalog)（词汇表、配置文件扫描和上下文包）、用于多跳查询的 BigQuery Graph 以及您自己验证的查询和自定义代理说明。借助新的[开放知识格式](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)，您的团队已维护的 wiki 可以直接输入到知识目录中。在查询时，会话分析会利用 AI.GENERATE_EMBEDDINGS 生成的列值的现有嵌入来将您的问题与正确的数据相匹配，因此询问“Texas”会发现存储为“TX”的行。

只有用户能够看到，接地才能赢得信任。因此，每个答案都是可检查的，提供：

-

可见的思考步骤：在返回答案之前检查代理的逐步推理及其生成的确切 SQL。

-

上下文引用：查看每个响应背后的精确来源，包括表格、架构定义、经过验证的查询以及用于计算响应的术语表。

-

主动消歧：当提示模糊时，客服人员会提出有针对性的澄清问题，而不是猜测。

-

长期记忆：代理会记住您的术语和问题的含义，因此您不必两次消除同一件事的歧义。![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/Context_Citation_Gif.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/Context_Citation_Gif.gif)

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/Context_Citation_Gif.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/Context_Citation_Gif.gif)

图 2. 生成您可以信任的答案

#### 安全和治理设计

扩展人工智能的一个常见障碍是治理。覆盖数以万计的用户需要严格的安全性、治理和透明的[成本控制](https://docs.cloud.google.com/gemini/data-agents/conversational-analytics-api/manage-costs)。对话式分析继承了 BigQuery 的治理模型，因此用户仅查询他们有权查看的数据，并且每个查询都会被记录下来以便在 BigQuery 合规性框架内进行审核。除此之外，它还支持[访问透明度 (AxT)](https://cloud.google.com/security/products/access-transparency?hl=en)、[客户管理的加密密钥 (CMEK)](https://docs.cloud.google.com/kms/docs/cmek)、[私有 IP](https://cloud.google.com/vpc/docs/private-google-access) 和 [VPC 服务控制](https://docs.cloud.google.com/vpc/docs)，现在保证静态数据以及欧盟和美国多区域端点内的 ML 处理的[数据驻留](https://docs.cloud.google.com/assured-workloads/docs/data-residency)。

对于最活跃的用户，我们还提供可扩展需求的运营控制：配置 Google Cloud 原生成本控制，确保用户或项目不会超出其分配量、限制代理的最大查询大小（以字节为单位），并通过作业上的 BigQuery 标签跟踪使用情况。

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/4_IR0rdmb.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/4_IR0rdmb.gif)

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/4_IR0rdmb.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/4_IR0rdmb.gif)

图 3. 代理可观测性和监控

#### BigQuery 

AI 的强大功能（通俗易懂）

该代理不仅检索行，还为您调用 BigQuery 的 AI 函数，将高级分析转变为您可以用简单语言提出的问题。

-找到“原因”，而不仅仅是“什么”：询问是什么推动了变革，代理会使用 AI.KEY_DRIVERS 运行根本原因分析，显示出变革背后的确切细分。

-

看看接下来会发生什么：通过在聊天中触发 AI.FORECAST 和 AI.DETECT_ANOMALIES 来预测趋势并标记异常值，从而超越历史报告，无需构建或管理模型。

-

查询您的整个数据资产：借助对象表，代理可以对关系数据和非结构化文件、PDF、图像、日志和视频进行推理，因此一次对话即可涵盖您的整个数据资产。

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/5_UJkt6D1.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/5_UJkt6D1.gif)

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/5_UJkt6D1.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/5_UJkt6D1.gif)

图 4. 会话分析利用 BigQuery AI 功能

#### 从回答问题到开展调查

会话分析代理正在从人类规模的反应性分析转向代理规模的主动行动。您不再局限于提出问题并等待答案。

深入模式：如果您问“为什么指标发生变化？”，代理将构建自己的分析计划，映射关键问题，无需手动 SQL 即可完成完整的多步骤调查，并最大限度地减少分析盲点。结果是您可以下载和共享的综合报告。

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/DeepDiveFinalTrim.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/DeepDiveFinalTrim.gif)

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/DeepDiveFinalTrim.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/DeepDiveFinalTrim.gif)

图 5. 对话分析中的 Deep Dive 模式

代理工作流程：部署自主代理来监控您的数据、对事件进行推理、按计划运行多步骤工作流程，并直接向您的聊天提供见解。您可以设置周一早上的业务报告或跨关键指标的每日异常检测，每个指标都有一个自定义指令，以便他们只调查您关心的内容。![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/9_S5opsaC.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/9_S5opsaC.gif)

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/9_S5opsaC.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/9_S5opsaC.gif)

图 6. 安排会话分析代理工作流程

#### 今天开始与您的数据对话

BigQuery 中对话式分析的全面推出标志着静态仪表板时代的正式退出。通过将 Gemini 的深度认知推理直接嵌入到数据仓库中，我们正在实现一个自我管理环境，将原始数据转化为主动的企业知识。这种交付是代理数据云的关键组成部分，提供了一个真正的行动系统，超越了回顾性报告，通过设计整合了安全性和治理，并为企业信任而设计。

如果您已准备好开始，请从我们的[文档](https://docs.cloud.google.com/bigquery/docs/conversational-analytics)了解更多信息，联系您的 Google Cloud 客户代表，或者立即开始在 [BigQuery Studio](https://console.cloud.google.com/bigquery) 中构建和部署您的第一个代理。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
