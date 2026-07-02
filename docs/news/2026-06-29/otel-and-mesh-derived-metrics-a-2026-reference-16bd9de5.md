<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-29T19:00:00+08:00
source: CNCF Blog
domain: AIOps / 可观测性
url: https://www.cncf.io/blog/2026/06/29/otel-and-mesh-derived-metrics-a-2026-reference/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# OTel 和网格衍生指标：2026 年参考

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-29 19:00 CST |
| 领域 | AIOps / 可观测性 |
| 来源 | CNCF Blog |
| 原文标题 | OTel and mesh-derived metrics: A 2026 reference |
| 原文 | [打开原文](https://www.cncf.io/blog/2026/06/29/otel-and-mesh-derived-metrics-a-2026-reference/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

如果您已经运行 OpenTelemetry 管道，那么您可以很好地了解应用程序正在执行的操作。这篇博文是关于您尚未看到的内容：您的服务之间的东西向流量，在...测量

## 正文

如果您已经运行 OpenTelemetry 管道，那么您可以很好地了解应用程序正在执行的操作。这篇博文是关于您尚未看到的内容：服务之间的东西向流量，在网络层测量，对应用程序代码进行零更改。

Linkerd 的代理提供了这些指标。一旦工作负载网格化，代理就会立即为每个入站和出站请求发出黄金指标。无需检测、SDK 调用或图像重建。这篇博文展示了这些指标的外观、它们在哪些方面与 OTel 重叠、哪些不重叠，以及如何将它们连接到现有的 OTel Collector 管道中，以便两个层都位于同一后端。如果您来自网状网络领域并且想知道 OTel 添加了哪些内容，您也会了解到这一点。

设置

参考环境是 K3s v1.34.6（单节点）、Linkerd 2.19+（在 2026 年 6 月的 Edge-26.5.5 上测试）、[OpenTelemetry Demo (Astronomy Shop)](https://github.com/open-telemetry/opentelemetry-demo) 作为网格工作负载、OTel Collector contrib 0.118.0 作为 DaemonSet，以及 [VictoriaMetrics](https://victoriametrics.com/)格拉法纳。工作 Collector 配置和 Grafana 仪表板可在本文末尾下载。

#### OTel 涵盖哪些内容

[OpenTelemetry 规范](https://opentelemetry.io/docs/specs/otel/) 定义了三种信号类型：跟踪、指标和日志。跟踪跟踪跨服务边界的请求，并为您提供完整的调用图。指标捕获随时间变化的数字测量值：计数器、仪表和直方图。日志是您的应用程序发出的结构化事件。

自动检测提供的功能取决于语言和框架：HTTP 请求计数、数据库调用持续时间和消息队列深度。您自己编写的是业务层信号：所下订单的数量、添加到购物车的商品以及付款失败。 OpenTelemetry 演示就是一个很好的例子：它发出 app_cart_add_item_latency_seconds、app_ payment_transactions_total、app_recommendations_counter_total 以及一些其他基础设施层无法推断的特定于服务的指标。

所有这些都存在于应用程序层。 OTel 检测您的代码，但它无法查看网络级别的服务之间流动的流量，除非您明确检测两端。

#### 网格衍生指标涵盖哪些内容当 Linkerd 将 sidecar 代理注入 pod 时，

该代理会拦截工作负载的所有入站和出站流量。它在每个网格 Pod 的端口 4191 上公开 Prometheus 指标端点。您不需要更改一行应用程序代码。您注释命名空间并滚动部署。范围是网状工作负载之间东西向的 L7 流量；南北入口流量是一个单独的问题。

命令之前的版本说明：截至撰写本文时，Linkerd 开源项目不再发布稳定版本工件；边缘版本是生产就绪型产品线（请参阅 [linkerd.io/releases](https://linkerd.io/releases/)），[Buoyant Enterprise for Linkerd (BEL)](https://www.buoyant.io/linkerd-enterprise) 是受支持的企业发行版。本实验运行edge-26.5.5。

注入之前，代理端口不存在。在“otel-demo”命名空间中的未网格化 Pod 上：```
kubectl exec -n otel-demo ad-74784f8f59-4nmwp -- wget -qO- http://localhost:4191/metrics 2>&1

```4191 上没有任何内容正在侦听。使用“linkerd.io/inject=enabled”注释命名空间并滚动部署后，每个 Pod 从“1/1”变为“2/2”就绪。第二个容器是“linkerd-proxy”。对新 Pod 运行相同的命令，添加“-c ad”以登陆应用程序容器（代理映像不附带“wget”），代理会以其完整的指标说明进行回答。这是该输出中的 1 个计数器，及其帮助文本（为便于阅读而修剪了标签）：```
# HELP request_total Total count of HTTP requests.
request_total{direction="inbound", target_addr="10.42.0.217:8080", tls="true",

client_id="otel-demo.otel-demo.serviceaccount.identity.linkerd.cluster.local", ...} 20

````client_id` 标签是调用者的 mTLS 身份。这是应用程序级指标无法为您提供的东西：在每个请求计数器上谁在与谁交谈的加密证明。

本博文所基于的指标系列均可在 Linkerd 2.19+ 中使用：

- `response_total`：总响应计数，标有`direction`、`classification`（成功或失败）、`status_code`、`grpc_status` 和目标工作负载
- `response_latency_ms`：响应延迟直方图。根据指标自己的帮助文本，它测量接收请求标头和完成响应流之间的经过时间
- `tcp_open_connections`、`tcp_read_bytes_total`、`tcp_write_bytes_total`：TCP 级计量器和计数器

前 2 个是 Linkerd 黄金指标的来源：成功率、请求率和延迟都是根据它们计算出来的。 TCP 计数器同时增加了连接级别的可见性。

前面的一个范围注释：代理还公开每个路由系列`（outbound_http_route_*，带有_秒直方图，而不是_ms`）。这篇文章的管道故意不发送它们：过滤器保留上面的 5 个系列，每个路由指标带来不同的单位和另一层基数。我将它们视为未来的工作而不是头条新闻；上述家庭是端到端工作的，是值得首先建立的家庭。

完整的代理指标参考位于 [linkerd.io/docs/reference/proxy-metrics/](https://linkerd.io/docs/reference/proxy-metrics/)。

### 重叠

请求率、延迟和错误都出现在两个层中。它们是相同的信号，但测量方式不同。

获取请求率。网格端有 `response_total{layer="mesh"}`，由代理对其返回的每个响应进行计数。您之前在代理输出中看到了一个原始的“request_total”计数器；这篇文章的管道故意保留了response_total，因此请求率是根据完成的响应来衡量的，这些响应也带有分类和“grpc_status”标签。应用程序端有“app_frontend_requests_total”，由前端自己的 OTel 仪器进行计数。相同的信号，但不同的度量名称和标签集：网格系列带有“client_id，classification”和“grpc_status”；该应用程序系列具有开发人员选择记录的任何尺寸。延迟讲述了同样的故事。在网格方面，“response_latency_ms_bucket{layer="mesh"}”测量请求标头被接收到响应流完成之间所经过的时间。在应用程序方面，“app_cart_add_item_latency_seconds_bucket”测量购物车服务自己的仪器为同一操作记录的时间。

两者都在一张图表上：

![Grafana timeseries 面板标题为“p99 延迟：网格层与应用层。”多条彩色线代表 otel-demo 命名空间中每个 Pod 的网格 p99 延迟。底部的一条明显的线代表 cart.add_item 操作的应用程序 p99 延迟，以毫秒为单位。](https://www.cncf.io/wp-content/uploads/2026/06/image-5-3.jpg)

Grafana 时间序列面板标题为“p99 延迟：网格层与应用层”。多条彩色线代表 otel-demo 命名空间中每个 Pod 的网格 p99 延迟。底部的一条明显的线代表 cart.add_item 操作的应用程序 p99 延迟（以毫秒为单位）。

网格和应用程序的测量不会相同。代理测量网络级时序；应用程序测量其自身的内部处理。它们之间的差距可能会导致网络开销、排队或缓慢的中间件。

信任哪一个来做什么：

- 对于 mTLS 身份和东西向成功率，请信任网格指标。代理是权威来源，因为它观察实际连接，而不是应用程序报告的有关自身的内容。
- 对于业务语义和自定义维度，请信任 OTel 应用指标。只有您的代码知道该请求是“白金”客户的“结帐”。
- 对于根本原因，请信任分布式跟踪。网格可以看到故障率；跟踪显示调用图并告诉您哪个跨度失败。

#### 不重叠

现在让我们看看它们在哪里互补。

OTel 涵盖了应用程序所知道的内容：自定义业务指标、每个请求跟踪、应用程序层事件以及您显式连接的基础设施指标。网格指标涵盖代理观察到的 L7 东西向服务到服务流量。

- 观察差异的最简单方法是通过失败。在 OpenTelemetry 演示中，前端服务定期调用广告服务。网格看到这些（为了可读性而修剪的标签）：接收请求标头和完成响应流之间经过的时间```
response_total{direction=“出站”，status_code=“200”，dst_service=“广告”，
分类=“失败”，grpc_status =“14”，...} 6
```查看标签对：`status_code="200"` 和 `grpc_status="14"`。 HTTP层报告成功； gRPC 状态为“不可用”。在 gRPC 中，状态代码在响应尾部中传输，与 HTTP 状态行分开，因此如果您仅针对 HTTP 状态代码发出警报，则此故障是不可见的。代理读取该状态并将响应归类为失败。网格知道调用失败以及失败了多少次，但不知道原因。

Jaeger 对同一操作的跟踪讲述了故事的其余部分：

![user_get_ads 请求的 Jaeger 跟踪时间线。生成树显示负载生成器调用前端代理，前端代理又调用前端。最深的跨度，前端服务上的 oteldemo.AdService/GetAds，以红色突出显示，标签显示 error=true 和 grpc.error_message “14 UNAVAILABLE: client 10.42.0.216:52176: server: 10.42.0.217:4143.”](https://www.cncf.io/wp-content/uploads/2026/06/image-5-4.jpg)

user_get_ads 请求的 Jaeger 跟踪时间线。生成树显示负载生成器调用前端代理，前端代理又调用前端。最深的跨度（前端服务上的 oteldemo.AdService/GetAds）以红色突出显示，标签显示 error=true 和 grpc.error_message“14 UNAVAILABLE: client 10.42.0.216:52176: server: 10.42.0.217:4143”。

跟踪显示失败的确切跨度、确切的错误消息以及涉及的客户端和服务器地址。网格标记了问题，而跟踪则显示了根本原因。

同样的分离也适用于业务指标。`app_ payment_transactions_total`和`app_recommendations_counter_total`显示在应用程序端，因为 OTel Demo 自己的仪器会发出它们。没有代理可以推断请求是付款或推荐。该领域知识存在于代码中。

#### 集成模式

目标是将网格指标放入与您的 OTel 指标相同的后端，并进行标记，以便您可以区分它们。该机制是 OTel Collector 中的专用管道。

以下是收集器配置的相关部分（完整文件可与本文一起下载）：```
receivers:
prometheus/mesh:
config:
scrape_configs:
- job_name: linkerd-mesh
scrape_interval: 30s
kubernetes_sd_configs:
- role: pod
relabel_configs:
- source_labels: [__meta_kubernetes_pod_container_name]
action: keep
regex: linkerd-proxy
- source_labels: [__meta_kubernetes_pod_ip]
action: replace
target_label: __address__
regex: (.+)
replacement: $1:4191

processors:
filter/mesh:
error_mode: ignore
metrics:
metric:
- 'not(name == "response_total" or IsMatch(name, "response_latency_ms.*") or name == "tcp_open_connections" or name == "tcp_read_bytes_total" or name == "tcp_write_bytes_total")'

resource/mesh:
attributes:
- key: layer
value: mesh
action: insert

service:
pipelines:
metrics/mesh:
receivers: [prometheus/mesh]
processors: [memory_limiter, filter/mesh, resource/mesh, resourcedetection, k8sattributes, batch]
exporters: [prometheusremotewrite]
```“prometheus/mesh”接收器使用 Kubernetes pod discovery 来查找名为 l“inkerd-proxy”的每个容器，并抓取端口 4191。“filter/mesh 处理器”以 OpenTelemetry Transformation Language (OTTL) 编写，仅保留前面列出的 5 个指标系列。 “resource/mesh”“处理器在每个系列上插入”“layer=mesh”，“k8sattributes”通过 pod、命名空间、部署和节点元数据丰富每个系列。该管道与您现有的指标管道是分开的，因此不会产生干扰。

此设置中的一个问题花费了我真正的调试时间：“替换：”$1:4191 重新标记规则在某些版本上超出了 Collector 基于 $ 的环境变量扩展，并且该配置在启动时被拒绝。我在之前的运行中在 contrib 0.104.0 上遇到了这个问题，其中“confmap.unifyEnvVarExpansion”功能门是原因“（当时的解决方法：--feature-gates=-confmap.unifyEnvVarExpansion）”。同样的故障[在 0.112.0 上向上游报告](https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/36160)，甚至拒绝转义的 $$1:$$2 替换。 Contrib 0.118.0（本实验室固定的版本）接受配置。固定您的图像标签。

以下是管道如何组合在一起的。网格指标通过收集器流入 VictoriaMetrics； OTel Demo 的应用程序指标保留在其捆绑的 Prometheus 中。 Grafana 将两者作为单独的数据源读取，这正是可下载仪表板的混合面板的连接方式：

![网格指标和应用程序指标作为单独数据源流入 Grafana 的流程图图像](https://www.cncf.io/wp-content/uploads/2026/06/image-5.png)

Grafana 仪表板 JSON 可与本文一起下载。它使用混合数据源面板：查询 A 从 VictoriaMetrics 中提取 `response_latency_ms_bucket{layer="mesh"`}；查询 B 从 Prometheus 数据源中提取“app_cart_add_item_latency_seconds_bucket”。当工作负载进行网格化和 OTel 检测时，这两条线都会填充。导入测试时，两个数据源输入都是普罗米修斯类型，很容易意外指向同一源。将网格输入映射到 VictoriaMetrics，并将应用程序输入映射到 Prometheus。

该参考堆栈使用 VictoriaMetrics 和 OTel Demo 的内置 Grafana。该模式适用于任何与 Prometheus 兼容的后端。该堆栈还包括用于应用程序日志的 VictoriaLogs；该管道超出了本文的范围。收集器配置也维护在 [myOTel](https://github.com/mesutoezdil/myOTel) 参考堆栈中，本实验室的设置改编自该参考堆栈。命名空间和存储类不同，但管道是相同的。

#### 关于基数的简短说明

代理指标带有很多标签。在此管道丰富后存储在 VictoriaMetrics 中的单个 response_latency_ms_bucket 系列带有 35 个标签：“direction、tls、client_id、authz_kind、route_name、srv_name、le”等。有些是代理发出的，有些是由 k8sattributes 和资源处理器添加的。这些标签值的每个组合都是其自己的系列，每个直方图桶在每个网格 Pod 上一次。该实验室的抓取覆盖了 30 个网状 Pod：25 个 OTel 演示 Pod、管道自己的 Collector 和 VictoriaMetrics，以及 Linkerd 的 3 个控制平面 Pod，因为抓取将每个 Linkerd 代理容器保留在集群中。仅“response_latency_ms_bucket”就产生了 5,642 个系列，整个“job="linkerd-mesh””抓取经过过滤后总共有 9,280 个系列。这两个数字都是过滤后的，这就是要点：按度量标准系列过滤会缩短名称列表，但它对您保留的系列内的标签基数没有任何作用。您保留的直方图就是您付费的直方图。

如果不进行过滤，代理会公开 163 个不同的指标系列。在过滤器/网格处理器仅保留这 5 个系列之后，11 个指标名称到达 VictoriaMetrics：这 5 个系列导出为 7 个名称（每个直方图分为“_bucket”、“_count”和“_sum”），还有 3 个来自“control_response_latency_ms_*”的泄漏，最后一个是导出器生成的 target_info。这些额外的东西从哪里来是下一个主题。

您有 2 个地方可以进行此过滤，我在本实验室中的 contrib 0.118.0 上测试了这两个地方。第一个是普罗米修斯接收器中的“metric_relabel_configs”保留规则：```
metric_relabel_configs:
- source_labels: [__name__]
action: keep
正则表达式：“response_total|response_latency_ms.*|tcp_.*”
```在此规则处于活动状态且没有 OTTL 过滤器的情况下，15 个指标名称流入 VictoriaMetrics：9 个与正则表达式匹配的代理名称，加上 keep 规则从未见过的 6 个名称。这 6 个是 scrape 自己的合成系列 `(up, scrape_duration_seconds, scrape_samples_scraped, scrape_samples_post_metric_relabeling`, scrape_series_added)，指标重新标记不适用于该系列，以及 `target_info`，是 `prometheusremotewrite` 导出器在处理器运行后生成的。

第二个是来自集成部分的 OTTL 过滤器/网格处理器，它有 11 个名称：163 个族输入，11 个输出。当你选择时，11 和 15 之间的差距很重要。重新标记正则表达式是完全锚定的，因此 `response_latency_ms.* ` 不承认 `control_response_latency_ms_*;` OTTL 的 IsMatch 是未锚定的，因此这 3 个控制平面名称会通过它泄漏。另一方面，keep 规则中的 tcp_.* 承认代理公开的每个 TCP 系列，包括“tcp_open_total”和“tcp_close_total”，而 OTTL 列表明确命名其 3 个 TCP 指标。并且只有OTTL过滤器会掉落合成刮擦系列。

此参考配置附带 OTTL 过滤器：保留列表位于标记和丰富数据的处理器旁边的管道中，而合成系列则位于后端之外。重新标记路线也是一个不错的选择，它会在样本进入管道之前的刮擦时间进行过滤；只需在考虑锚定的情况下编写正则表达式，并期望向上和“scrape_*”系列流动即可。

#### 每个人都赢得自己的位置

OTel 为您提供应用程序对其自身的了解：业务事件、自定义维度以及跨每个服务边界跟踪请求的分布式跟踪。 Linkerd 为您提供网络所知道的信息：网格服务之间的每个东西向请求，具有 mTLS 身份、成功率和延迟，并且对代码进行零更改。

两者是互补的。没有网格指标的 OTel 管道缺少服务拓扑层。没有 OTel 检测的网格可以告诉您请求失败，但不能告诉您原因。

如果您已经在运行 OTel，则添加网格管道是一项收集器配置更改和命名空间注释。本博文中的 Grafana 仪表板会立即在一张图表上显示两个图层。

关于作者：Mesut 是 Adfinis GmbH 的开发运营工程师和云原生开源贡献者（[Project HAMi,](https://project-hami.io/) [kagent](https://kagent.dev/) 等），总部位于德国斯图加特。您可以在 GitHub 上找到他的作品：[https://github.com/mesutoezdil](https://github.com/mesutoezdil) 并在 LinkedIn 上与他联系：[https://www.linkedin.com/in/mesut-oezdil/](https://www.linkedin.com/in/mesut-oezdil/)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
