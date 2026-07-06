<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-26T04:00:00+08:00
source: Kubernetes Blog
domain: 云原生
url: https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 使用 Headlamp 更快地检查 Volcano 工作负载

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-26 04:00 CST |
| 领域 | 云原生 |
| 来源 | Kubernetes Blog |
| 原文标题 | Inspect Volcano workloads faster with Headlamp |
| 原文 | [打开原文](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

Volcano 是 Kubernetes 的云原生批处理调度程序，专为高性能计算、AI/ML 和其他批处理工作负载而构建。 Headlamp 是一个可扩展的 Kubernetes Web UI。借助其插件系统，Headlamp 可以提供内置 Kubernetes 资源之外的 API 和工作流程。 Volcano 插件将核心 Volcano 资源引入 Headlamp，以便您可以在一处检查工作负载状态、队列行为和组调度详细信息。 Kubernetes 最初是围绕长期运行的服务而设计的，其中应用程序预计会随着时间的推移启动并保持可用。批处理、AI/ML 和 HPC 工作负载的行为通常有所不同：作业动态到达，争夺有限的资源，并且可能需要多个工作人员一起启动才能开始有用的工作。 Volcano 通过队列、优先级、配额和组调度等概念扩展了 Kubernetes。 Volcano 不是独立对待每个 Pod，而是在安排工作负载时考虑到整个作业以及取得进展所需的资源。为了使这些工作负载更易于操作和故障排除，Volcano 插件将该调度上下文直接引入 Headlamp。观看这个简短的演练以了解火山

## 正文

## 使用 Headlamp 更快地检查 Volcano 工作负载

作者：[Mahmoud Magdy](https://github.com/mahmoudmagdy1-1)（独立）| 2026 年 6 月 25 日，星期四

[Volcano](https://volcano.sh/) 是 Kubernetes 的云原生批量调度程序，专为高性能计算、AI/ML 和其他批量工作负载而构建。

[Headlamp](https://headlamp.dev/) 是一个可扩展的 Kubernetes Web UI。借助其插件系统，Headlamp 可以提供内置 Kubernetes 资源之外的 API 和工作流程。 Volcano 插件将核心 Volcano 资源引入 Headlamp，以便您可以在一处检查工作负载状态、队列行为和组调度详细信息。

Kubernetes 最初是围绕长期运行的服务而设计的，其中应用程序预计会随着时间的推移启动并保持可用。批处理、AI/ML 和 HPC 工作负载的行为通常有所不同：作业动态到达，争夺有限的资源，并且可能需要多个工作人员一起启动才能开始有用的工作。

Volcano 通过队列、优先级、配额和组调度等概念扩展了 Kubernetes。 Volcano 不是独立对待每个 Pod，而是在安排工作负载时考虑到整个作业以及取得进展所需的资源。

为了使这些工作负载更易于操作和故障排除，Volcano 插件将该调度上下文直接引入 Headlamp。

观看这个简短的演练，了解 Headlamp 中的 Volcano 插件：

### 视觉上下文帮助团队更快地理解 Volcano 作业、队列和 PodGroups[](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/#visual-context-helps-teams-understand-volcano-jobs-queues-and-podgroups-faster)

使用 Volcano 通常意味着在尝试了解批处理工作负载时跨多个相关资源。您可能会从一个 Job 开始，然后查看相关的 PodGroup，检查其后面的 Pod，检查 Queue，最后再次返回到 Job。所有这些都可以通过“kubectl”和 Volcano CLI 等 CLI 工具实现，但它很快就会变得支离破碎。

Headlamp 的 Volcano 插件将关键资源整合到一个 UI 中，使工作流程变得更加轻松。您可以从同一界面直接在作业、队列、PodGroup、Pod 和事件之间移动，而不用手动重建关系。

Volcano 在核心 Kubernetes 对象之上引入了自己的资源：Job 将批量工作负载描述为一组任务及其创建的 Pod。Queue 使用配额和优先级在团队或工作负载之间划分集群容量。PodGroup 将一组 Pod 捆绑在一起，以便调度程序可以将它们视为单个单元进行组调度。

该插件直接在 Headlamp 中显示所有三种资源类型，在侧边栏的 Volcano 部分下为每种资源类型提供专用列表和详细视图。

### 作业：工作负载状态、操作和日志[](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/#jobs-workload-status-actions-and-logs)

作业视图是插件体验的中心。在列表视图中，您可以快速了解工作负载的基础知识，包括其状态、队列、正在运行与最小可用值、任务计数和期限。

![头灯中的火山工作列表](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/volcano-jobs-list.png)

详细信息视图进一步显示调试作业时通常需要的信息：任务详细信息、Pod 状态、相关队列和 PodGroup 链接、条件、事件等。该插件不会强迫您在多个 CLI 命令之间跳转，而是将该上下文保留在一个页面中。

作业页面还为适当的状态添加了支持的生命周期操作，包括暂停和恢复，因此您可以直接从 UI 操作作业。

另一个有用的附加功能是直接访问作业日志。您无需离开作业详细信息页面即可打开 Volcano 作业创建的 Pod 的日志。日志查看器支持单 Pod 和所有 Pod 视图，以及容器选择和常见日志控制，例如行计数、先前日志、时间戳和关注。

![Headlamp 中的火山作业日志](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/volcano-job-logs.png)

### 队列：调度容量和资源上下文[](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/#queues-scheduling-capacity-and-resource-context)

队列视图提供的不仅仅是一小组顶级字段。它可以帮助您了解资源是如何分配的，以及如何受到表面容量、分配的资源、应得和保证的资源、预留详细信息、子队列等的限制。当尝试了解如何跨队列共享和限制资源时，这使得“队列”页面更加有用。

![头灯中的火山队列详细信息](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/volcano-queue-detail.png)

### PodGroups：帮派调度状态和拦截器[](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/#podgroups-gang-scheduling-state-and-blockers)

PodGroup 是理解 Volcano 中的群组调度的核心，该插件使该状态更易于检查。 PodGroup 视图突出显示进度、条件、最低资源要求等。

这还可以让您更清楚地了解工作负载是否因为尚未满足作为组运行所需的调度条件而被阻止。

![头灯中的火山 PodGroup 详细信息](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/volcano-podgroup-detail.png)

### 地图视图：作业、队列、PodGroup 和 Pod 位于一处[](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/#map-view-jobs-queues-podgroups-and-pods-in-one-place)

地图视图显示火山资源如何连接。您无需单独检查每个资源，而是可以查看作业、PodGroup、队列和 Pod 之间的相互关系。

当工作负载待处理或未按预期进行时，这尤其有用。该地图可以显示作业、其相关的 PodGroup、为工作负载创建的 Pod 以及其周围的队列上下文。警告和错误状态还可以更轻松地发现需要注意的资源。

![头灯地图视图中的火山资源](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/volcano-map-view.png)

### 为什么将其与 CLI 工具一起使用[](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/#why-use-this-alongside-cli-tools)

该插件并不试图取代“kubectl”或 Volcano CLI。这些对于自动化、脚本编写和原始对象检查仍然很重要。该插件改进的是交互式故障排除体验：更快地发现相关资源，理解结构化的详细页面，以及从调度状态转移到运行时输出，而无需不断切换工具。### 接下来是什么[](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/#what-s-next)

这项工作将主要的 Volcano 工作流程引入 Headlamp，包括作业、队列、PodGroup 和地图视图。未来可能的工作包括 Prometheus 集成、更丰富的调度见解以及跨 Volcano 工作负载的更多面向工作流的可见性。

### 尝试一下并分享反馈[](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/#try-it-and-share-feedback)

要尝试该插件：

- 安装头灯。
- 从 Headlamp UI 打开插件目录。
- 寻找火山。
- 安装火山插件。
- 将 Headlamp 连接到已安装 Volcano 的 Kubernetes 集群。
![Headlamp 插件目录中的 Volcano 插件](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/volcano-plugin-catalog.png)

如果您有想法、功能请求或错误报告，请在 [Headlamp 插件存储库](https://github.com/headlamp-k8s/plugins) 中提出问题。来自真实 Volcano 用户的反馈将有助于塑造接下来的发展。

- [←上一页](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/)
- [下一页→](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/)

最后修改时间为太平洋标准时间 2026 年 6 月 21 日晚上 9:39：[修复前面的问题 (4d8587009e)](https://github.com/kubernetes/website/commit/4d8587009ee08cb2ad8ac3e8b78fb0c2082650a8)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
