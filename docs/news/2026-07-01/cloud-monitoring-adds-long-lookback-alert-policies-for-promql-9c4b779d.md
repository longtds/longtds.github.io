<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:00:00+08:00
source: Google Cloud Blog
domain: AI 基础设施
url: https://cloud.google.com/blog/products/management-tools/cloud-monitoring-adds-long-lookback-alert-policies-for-promql/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# Cloud Monitoring 为 PromQL 添加长回溯警报策略 |谷歌云博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:00 CST |
| 领域 | AI 基础设施 |
| 来源 | Google Cloud Blog |
| 原文标题 | Cloud Monitoring adds long-lookback alert policies for PromQL \| Google Cloud Blog |
| 原文 | [打开原文](https://cloud.google.com/blog/products/management-tools/cloud-monitoring-adds-long-lookback-alert-policies-for-promql/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

选择警报策略的阈值可能是一件令人头疼的事情。您必须分析历史数据，将其聚合成语义上有意义的时间序列，并选择重要的阈值。如果工作负载增加，您之前设置的静态阈值可能会变得太低，并且您的警报可能会过于频繁地触发。新的工作负载可能需要设置新的阈值，并且为单独的工作负载设置单独的阈值需要创建单独的策略，从而导致管理一组大多相似的策略的麻烦。更不用说，某些指标甚至无法在使用静态阈值时发出警报。如果您的指标随着一天中的不同时间而变化，就像许多电子商务指标一样，那么没有一个

## 正文

管理工具

##

在 Cloud Monitoring 中使用动态阈值和长达两年的警报进行异常检测

2026 年 7 月 1 日

###### 李彦科

高级产品经理

###### 丹尼尔·科斯

资深软件工程师

###### 立即尝试 

Gemini Enterprise 商业版

选择警报策略的阈值可能是一件令人头疼的事情。您必须分析历史数据，将其聚合成语义上有意义的时间序列，并选择重要的阈值。如果工作负载增加，您之前设置的静态阈值可能会变得太低，并且您的警报可能会过于频繁地触发。新的工作负载可能需要设置新的阈值，并且为单独的工作负载设置单独的阈值需要创建单独的策略，从而导致管理一组大多相似的策略的麻烦。

更不用说，某些指标甚至无法在使用静态阈值时发出警报。如果您的指标随着一天中的不同时间而变化，就像许多电子商务指标一样，那么没有一个单一的阈值会起作用。例如，如果您的指标如下所示，您会怎么做：

![https://storage.googleapis.com/gweb-cloudblog-publish/images/qtfse9nqWC88b92.max-2200x2200.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/qtfse9nqWC88b92.max-2200x2200.png)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/qtfse9nqWC88b92.max-2200x2200.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/qtfse9nqWC88b92.max-2200x2200.png)

显然该图表中间出了问题……但由于异常值在每日数据的正常范围内，因此任何静态值阈值都无法捕捉到它。

#### 引入长回溯和动态阈值

我们很高兴地宣布，随着 [PromQL 的长回溯警报策略](https://docs.cloud.google.com/monitoring/alerts/using-promql#promql-2years) 的推出（目前处于预览阶段），[云监控警报](https://docs.cloud.google.com/monitoring/alerts) 的用户现在可以解决这个问题。这一备受期待的功能更新现在允许您配置 PromQL 警报策略，以运行 Cloud Monitoring 中存储的两年多的指标数据，支持逐年和逐季度分析。PromQL 中的两年回溯期解锁的一个主要用例是动态阈值，即阈值引用指标历史记录的策略。一个简单的例子是警报策略，其中规定“如果过去 5 分钟的平均值比上周的平均值高出 2 倍，则提醒我”。您无需将静态数字设置为阈值，而是在生成警报之前根据其历史数据设置每个时间序列的异常程度。这允许策略的灵活性，支持因工作负载增长而自然改变的基线，并提供适用于所有工作负载的单一阈值。您不必分析每个时间序列来正确设置警报 - 只需设置一个向您发出“异常”信号的因素即可。

以上面的示例为例：要捕获该异常，您可以创建一个策略，其中规定“如果过去 5 分钟的值低于一周前同一 5 分钟范围内的值的 70%，则提醒我”。这样的策略将创建一个随一天中的时间而变化的阈值，并且您将捕获异常下降：

![https://storage.googleapis.com/gweb-cloudblog-publish/images/8JX8WREHZPq68Fc.max-2100x2100.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/8JX8WREHZPq68Fc.max-2100x2100.png)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/8JX8WREHZPq68Fc.max-2100x2100.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/8JX8WREHZPq68Fc.max-2100x2100.png)

#### 动态阈值算法

在 PromQL 中选择正确的动态阈值算法取决于源数据的形状。随时间变化的指标需要与变化不大的指标不同的算法。

您可以重写以下示例，以将历史数据查询作为阈值（在 < 或 > 之后放置指标），但如果这样做，您将无法轻松可视化阈值。

由于这些使用历史数据，因此在启动新工作负载时，针对单个工作负载而不是聚合触发的精细警报策略可能会不稳定。当您积累历史数据时，这个问题将自行解决。您还可以通过仅对聚合运行动态阈值警报来避免这种情况。移动平均线
在最简单的算法中，当数据的近期趋势偏离长期数据的移动平均值时，就会触发警报。这有利于捕获相对稳定数据中的异常。

以下是 PromQL 的一些示例，它将最后 5 分钟与一周基线进行比较，并在比平均值高或低 30% 时发出警报：

正在加载...

sum(rate(http_requests_total[5m])) / sum(rate(http_requests_total[1w])) > 1.3 或 sum(rate(http_requests_total[5m])) / sum(rate(http_requests_total[1w])) < .7

![https://storage.googleapis.com/gweb-cloudblog-publish/images/4v9HQ8snDJbP2oR.max-1400x1400.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/4v9HQ8snDJbP2oR.max-1400x1400.png)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/4v9HQ8snDJbP2oR.max-1400x1400.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/4v9HQ8snDJbP2oR.max-1400x1400.png)

也可以直接写成比较，这样可能更容易理解。以下内容表示“如果最近 5 分钟的数据平均值 > 每周平均值的 1.3 倍，请提醒我。”：

正在加载...

总和（速率（http_requests_total[5m]））> 1.3 * 总和（速率（http_requests_total[1w]））

Z 分数（标准差）
使用此算法根据数据的平均值和标准差来识别异常。 [z-score](https://en.wikipedia.org/wiki/Standard_score) 衡量您最近的数据和历史数据之间的统计距离，一个常见的阈值是 z 得分高于 3 或低于负 3 被视为异常。这可以衡量数据的波动性与其通常的噪声相比，并且它最适合具有稳定的平均值和适当波动性的数据：

PromQL 示例，将最后 5 分钟与一周平均值和标准差进行比较：

正在加载...

绝对（总和（率（http_requests_total [5m]））-总和（率（http_requests_total [1w]）））/ stddev_over_time（总和（率（http_requests_total [5m]））[1w：5m]）> 3

z 分数信号示例和由此产生的异常检测阈值：

![https://storage.googleapis.com/gweb-cloudblog-publish/images/image1_VFrHPBv.max-1700x1700.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/image1_VFrHPBv.max-1700x1700.png)

季节分解（时间偏移比较）
这是一种简单的时间偏移算法，可将一段时间内的时间序列数据与前一天或前一周的同一时间段进行比较。这对于具有与之相关的及时模式的指标来说是理想的选择，例如网站的访问者随一天中的时间和一周中的日期而变化。假期和其他可能导致某一天低于预期的因素可以通过对多个历史时期进行平均来消除（例如，一周前、两周前和三周前的平均值，然后将该平均值与今天进行比较）。

PromQL 示例，将最近 5 分钟与昨天同一时间段进行比较，如果近期数据比一日偏移数据低 50% 以上，则发出警报：

正在加载...

sum(rate(http_requests_total[5m])) / sum(rate(http_requests_total[5m] 偏移 1d)) < .5

可以用代数方式重写为：

正在加载...

sum(rate(http_requests_total[5m])) < .5 * sum(rate(http_requests_total[5m] 偏移 1d))

![https://storage.googleapis.com/gweb-cloudblog-publish/images/Bkby4f9LySHuz75.max-1500x1500.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/Bkby4f9LySHuz75.max-1500x1500.png)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/Bkby4f9LySHuz75.max-1500x1500.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/Bkby4f9LySHuz75.max-1500x1500.png)

在生产中，您可能需要与一周前的同一时间段进行比较，或者与 1 天和 7 天前的同一时间段的平均值进行比较，以避免在周末和节假日等自然较低的日子触发：

正在加载...

sum(rate(http_requests_total[5m])) / (( sum(rate(http_requests_total[5m] 偏移量 1d)) + sum(rate(http_requests_total[5m] 偏移量 7d)) ) / 2) < .5

使用时间偏移时，您只能在下降或尖峰时可靠地触发，因为在单个策略中同时触发突然下降和突然尖峰可能会导致警报触发两次。可以这样想：如果今天的流量急剧下降，您的警报将立即触发。然而，恰好 24 小时后，今天的异常下跌成为明天的历史基线。如果您的政策触发任何异常差异（更高或更低），那么明天突然“恢复正常”将看起来像是相对于昨天的下跌而言的巨大峰值，并且您将收到幻影异常的虚假警报。您可以在上图中看到这一点 — 信号的下降（蓝线）在 24 小时后以其倒数重新出现。

为了防止这种情况，您应该在监控任何给定指标时仅跟踪下降或峰值。

#### 使用动态阈值控制失控成本

一旦您可以根据与历史基线的偏差触发警报，就会出现许多有趣的用例。例如，您可以使用动态阈值来防止任何提供粗略跟踪支出指标的 Google Cloud 服务超支。

假设您担心人工智能代币成本失控。您可以执行以下操作：

-

-

配置动态阈值警报，如果最近 10 分钟累计输入/输出令牌使用量超过一周历史平均值的 25 倍，则触发该警报，该警报应该只捕获绝对会导致超支的极端异常情况（例如泄漏的 API 密钥）：

-

`sum(rate({"__name__"="aiplatform.googleapis.com/publisher/online_serving/
token_count"}[10m])) >
``25 * sum(rate({"__name__"="aiplatform.googleapis.com/publisher/online_serving/
token_count"}[1w]))`

-

触发警报以触发 [Pub/Sub 通知通道](https://docs.cloud.google.com/monitoring/support/notification-options#pubsub)，该通道将通知推送到 [Cloud Run 函数](https://docs.cloud.google.com/run/docs/functions/overview)。

-

然后，该 Cloud Run 函数运行一个工作流程，该工作流程使用 [Cloud Quotas API](https://docs.cloud.google.com/docs/quotas/api-overview) 将您的令牌使用配额降低到 0，从而立即停止超支。请注意，在您解决问题之前，代币的合法使用将被暂停……但至少您可以止血。

我们正在致力于使用动态阈值来产品化异常检测，以便更容易编写。我们还在 Cloud Monitoring 警报中开发更复杂的异常检测算法，该算法使用专门针对时间序列数据进行训练的 AI 模型。[![https://storage.googleapis.com/gweb-cloudblog-publish/images/21_-_Management_Tools_EI9iqlb.max-700x700.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/21_-_Management_Tools_EI9iqlb.max-700x700.jpg)

管理工具

#### 从查询到操作：在 Cloud Monitoring Observability Analytics 中引入 SQL 警报

作者：Joy Wang • 4 分钟阅读](https://cloud.google.com/blog/products/management-tools/alert-with-sql-in-cloud-monitoring-observability-analytics)

[![https://storage.googleapis.com/gweb-cloudblog-publish/images/21_-_Management_Tools_EI9iqlb.max-700x700.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/21_-_Management_Tools_EI9iqlb.max-700x700.jpg)

管理工具

#### Log Analytics 

现在更名为 Observability Analytics：使用 SQL 查询日志和跟踪

作者：Joy Wang • 5 分钟阅读](https://cloud.google.com/blog/products/management-tools/query-logs-and-traces-with-sql-in-observability-analytics)

[![https://storage.googleapis.com/gweb-cloudblog-publish/images/10_-_Databases.max-700x700.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/10_-_Databases.max-700x700.jpg)

数据库

#### 认识最新的数据库中心，

现在具有 Gemini 支持的车队智能

作者：Kiran Shenoy • 5 分钟阅读](https://cloud.google.com/blog/products/databases/database-center-improvements-from-next26)

[![https://storage.googleapis.com/gweb-cloudblog-publish/images/GCN26_102_BlogHeader_2436x1200_Opt_11_Dark.max-700x700.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/GCN26_102_BlogHeader_2436x1200_Opt_11_Dark.max-700x700.jpg)

应用开发

#### Gemini Cloud Assist：主动云操作为您服务，甚至在您提出要求之前

作者：Michael Bachman • 5 分钟阅读](https://cloud.google.com/blog/products/application-development/gemini-cloud-assist-at-next26)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
