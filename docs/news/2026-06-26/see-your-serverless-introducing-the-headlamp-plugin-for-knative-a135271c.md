<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-26T02:00:00+08:00
source: Kubernetes Blog
domain: 云原生
url: https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 查看您的无服务器：引入 Knative 的 Headlamp 插件

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-26 02:00 CST |
| 领域 | 云原生 |
| 来源 | Kubernetes Blog |
| 原文标题 | See your serverless: introducing the Headlamp plugin for Knative |
| 原文 | [打开原文](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

Headlamp 是一个开源、可扩展的 Kubernetes SIG UI 项目，旨在让您探索、管理和调试集群资源。 Knative 为 Kubernetes 带来了无服务器工作负载，处理流量路由、自动扩展和修订管理，以便团队可以在不影响基础设施的情况下进行部署和迭代。但日常操作 Knative 工作负载可能很困难，kn CLI、kubectl 和 Kubernetes UI 之间仍然存在大量跳转，无法全面了解正在运行的内容。我们构建了 Headlamp Knative 插件来弥补这一差距，使操作员能够从一个地方检查、理解和处理他们的工作负载。该插件是作为 LFX 指导的一部分而构建的。这是我们运送的物品的概览。以下是 Headlamp Knative 插件的简短演练：将 Knative 资源与 Headlamp 的地图视图集成 Headlamp 的资源映射也适用于 Knative CRD。您可以在单个图形视图中查看 KServices、Revisions 和 DomainMappings 如何相互关联。 KService 管理：编辑流量分割、重启 pod 和查看日志 KService 是 Knative 中的顶级资源：它管理路由、配置、修订和更新的生命周期。

## 正文

## 查看您的无服务器：引入 Knative 的 Headlamp 插件

作者：[Mudit Maheshwari](https://github.com/mudit06mah)（独立）、[Kahiro Okina](https://github.com/kahirokunn)（Craftsman Software, Inc.）| 2026 年 6 月 25 日，星期四

[Headlamp](https://headlamp.dev/) 是一个开源、可扩展的 Kubernetes SIG UI 项目，旨在让您探索、管理和调试集群资源。

[Knative](https://knative.dev/) 将无服务器工作负载引入 Kubernetes，处理流量路由、自动扩展和修订管理，以便团队可以在不影响基础设施的情况下进行部署和迭代。但是日常操作 Knative 工作负载可能很困难，在“kn”CLI、“kubectl”和 Kubernetes UI 之间仍然存在大量跳转，以全面了解正在运行的内容。

我们构建了 [Headlamp Knative 插件](https://github.com/headlamp-k8s/plugins/tree/main/knative) 来弥补这一差距，使操作员能够从一个地方检查、理解和处理他们的工作负载。该插件是作为 LFX 指导的一部分而构建的。这是我们运送的物品的概览。

以下是 Headlamp Knative 插件的简短演练：

### 将 Knative 资源与 Headlamp 的地图视图集成[](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/#integrating-knative-resources-with-headlamp-s-map-view)

Headlamp 的资源映射也适用于 Knative CRD。您可以在单个图形视图中查看 KServices、Revisions 和 DomainMappings 如何相互关联。

![头灯地图视图中的原生资源](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/knative-map-view.png)

### KService管理：编辑流量分割、重启pod、查看日志[](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/#kservice-management-edit-traffic-splits-restart-pods-and-view-logs)

KService 是 Knative 中的顶级资源：它管理路由、配置、修订以及运行和公开应用程序所需的一切的生命周期。

该插件为 KServices 提供了完整的详细视图，并具有编辑模式切换功能，可对流量分割、自动缩放注释等进行实时更改。查看 YAML、打开日志、触发重新部署或重新启动支持 Pod 等常见操作会显示在标头中，并由您当前的 RBAC 权限控制。![Knative 服务详细信息视图](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/knative-kservice-view.png)

### 流量分割：跨版本路由以逐步推出和测试[](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/#traffic-splitting-route-across-revisions-for-gradual-rollouts-and-testing)

Knative 使得跨同一服务的多个修订版路由流量成为可能。这对于金丝雀发布、逐步推出、标记预览 URL 和 A/B 测试非常有用。

该插件显示分配给每个修订版的流量、最新准备的修订版、准备状态、期限和配置的标签。在编辑模式下，您可以内联调整百分比和标签。该插件在保存之前会验证流量总计是否为 100%，并且标签是唯一的。带有报告 URL 的标记路由呈现为可点击链接。

![修订版之间的流量分配](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/knative-traffic-view.png)

### 自动缩放配置：查看有效设置和集群默认值[](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/#autoscaling-configuration-view-effective-settings-and-cluster-defaults)

Knative 的自动缩放器支持一系列设置：并发目标、目标利用率、RPS 目标、最小/最大规模、初始规模、稳定窗口、缩减延迟等。任何工作负载的有效价值是 KService 级别注释和集群范围 ConfigMap 的组合。

该插件读取“config-autoscaler”和“config-defaults”，并在上下文中显示每个 KService 的有效配置，因此您可以一目了然地了解某个设置是显式配置的还是回退到集群默认值。

![自动缩放和并发视图](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/knative-autoscaling-view.png)

### Prometheus 指标：监控请求率、延迟和资源利用率[](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/#prometheus-metrics-monitor-request-rates-latency-and-resource-utilization)与 [Headlamp 的 Prometheus 插件](https://github.com/headlamp-k8s/plugins/tree/main/plugins/prometheus) 配合使用时，该插件会在 KService 和修订详细信息页面上呈现请求率、延迟和资源利用率图表。在验证正在进行的流量分割时，每个修订版请求率细分特别有用。

![按修订过滤的 Knative 指标](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/knative-revision-metrics-graph.png)

### 其他 CRD 的仪表板[](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/#dashboard-for-other-crds)

该插件还包括修订、DomainMappings、ClusterDomainClaims 的列表和详细视图以及集群级网络概述（阅读“config-network”和“config-gateway”以显示有效的入口类、网关设置和支持服务）。这些使操作员无需离开头灯即可全面了解 Knative 的状态。

![Knative 修订列表视图](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/knative-revisions-view.png)
![Knative 域映射列表视图](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/knative-domain-mapping-view.png)
![Knative 集群域声明列表视图](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/knative-cluster-domain-claim-view.png)

### 如何在 Headlamp[](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/#how-to-install-the-knative-plugin-in-headlamp) 中安装 Knative 插件

- 确保集群中安装了 [Knative](https://knative.dev/docs/install/)。
- 在 Headlamp Desktop 中，打开插件目录，搜索 Knative，然后单击安装。
- 重新加载头灯，侧边栏中将出现一个新的 Knative 条目。

有关开发或源代码级设置，请参阅 [Knative 插件自述文件](https://github.com/headlamp-k8s/plugins/tree/main/plugins/knative)。当前版本是 [0.3.0-beta](https://github.com/headlamp-k8s/plugins/releases/tag/knative-0.3.0-beta)。

### 分享您的反馈[](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/#share-your-feedback)我们希望获得 Knative 运营商和用户的反馈。如果您遇到错误或需要对我们未涵盖的工作流程的支持，[请提出问题](https://github.com/headlamp-k8s/plugins/issues)。您还可以在 [Kubernetes Slack #headlamp 频道](https://kubernetes.slack.com/archives/headlamp) 中找到我们。

- [←上一页](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/)
- [下一页→](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/)

最后修改时间为太平洋标准时间 2026 年 6 月 21 日晚上 9:36：[调整博客文章标题 (7bf3df0ce7)](https://github.com/kubernetes/website/commit/7bf3df0ce739b9ec7fac9b9feb9d1ed8cf45d23b)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
