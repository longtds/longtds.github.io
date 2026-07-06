<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-26T06:00:00+08:00
source: Kubernetes Blog
domain: 云原生
url: https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 引入 Headlamp 的 Cluster API 插件

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-26 06:00 CST |
| 领域 | 云原生 |
| 来源 | Kubernetes Blog |
| 原文标题 | Introducing the Cluster API plugin for Headlamp |
| 原文 | [打开原文](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

Headlamp 是一个开源、可扩展的 Kubernetes SIG UI 项目，旨在让您直接从浏览器探索、管理和调试集群资源。 Cluster API (CAPI) 是一个 Kubernetes 子项目，它将声明性、Kubernetes 风格的 API 引入集群生命周期管理。它允许平台团队使用管理集群中存储和协调的标准 Kubernetes 对象来配置、升级和管理 Kubernetes 集群的生命周期。管理集群 API 资源历来需要原始 kubectl 命令和对所有权层次结构的深入熟悉。 Headlamp Cluster API 插件直接在 Headlamp 内部为平台团队带来视觉清晰度、更快的调试速度和简化的操作。该插件提供什么 Cluster API 插件向 Headlamp 添加了专用的 Cluster API 部分，并通过一致的列表和详细视图提供对核心 CAPI 资源的全面可见性。功能 描述 集群概述 查看具有实时控制平面和工作副本状态的集群。机器可见性 检查 MachineDeployments、MachineSet、机器和 MachinePools 的状态和条件。 Cluster API 仪表板 获取 Cluster API 资源的集中视图

## 正文

## 介绍 Headlamp 的 Cluster API 插件

作者：[Chayan Das](https://github.com/ChayanDass)（独立）| 2026 年 6 月 25 日，星期四

[Headlamp](https://headlamp.dev/) 是一个开源、可扩展的 Kubernetes SIG UI 项目，旨在让您直接从浏览器探索、管理和调试集群资源。

[集群 API (CAPI)](https://cluster-api.sigs.k8s.io) 是一个 Kubernetes 子项目，它将声明性、Kubernetes 风格的 API 引入集群生命周期管理。它允许平台团队使用管理集群中存储和协调的标准 Kubernetes 对象来配置、升级和管理 Kubernetes 集群的生命周期。

管理集群 API 资源历来需要原始的“kubectl”命令和对所有权层次结构的深入熟悉。 Headlamp Cluster API 插件直接在 Headlamp 内部为平台团队带来视觉清晰度、更快的调试速度和简化的操作。

### 该插件提供什么[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#what-this-plugin-provides)

Cluster API 插件向 Headlamp 添加了专用的 Cluster API 部分，并通过一致的列表和详细视图提供对核心 CAPI 资源的全面可见性。|特色 |描述 |
|:---|:---|
|集群概览 |查看具有实时控制平面和工作副本状态的集群。 |
|机器可视性|检查 MachineDeployments、MachineSet、Machine 和 MachinePools 的状态和条件。 |
|集群 API 仪表板 |集中查看集群 API 资源运行状况、活动状况问题、提供商信息和补救指南。 |
|控制平面监控 |跟踪 KubeadmControlPlane 副本、版本和关联机器。 |
|从 UI 进行缩放 |直接从 Headlamp 扩展 MachineDeployments 和 MachineSet。 |
|拥有的资源层次结构|跟踪集群、部署、集和机器之间的关系。 |
| KubeadmConfig 检查 |查看引导程序配置、文件、kubelet 参数和 join/init 设置。 |
|拓扑意识|自动检测并标记 ClusterClass 管理的资源。 |
|地图查看 |可视化集群、控制平面和工作线程关系。 |
|动态 API 版本控制 |支持 v1beta1 和 v1beta2 Cluster API 版本。 |
|普罗米修斯指标 |查看集群 API 资源详细信息页面上内联的 [Headlamp Prometheus 插件](https://github.com/headlamp-k8s/plugins/tree/main/prometheus) 的实时指标。 |

### 插件概览[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#a-tour-of-the-plugin)

Headlamp Cluster API 插件将核心 Cluster API 资源引入 Headlamp 内一致的可视化界面中。以下是第一个版本中包含的一些关键视图。

#### 集群 API 仪表板[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#cluster-api-dashboard)

仪表板提供了管理集群中集群 API 资源及其运行状况的集中视图。

![显示整体资源运行状况的集群 API 仪表板](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/cluster-api-dashboard.png)

概述总结了集群、机器、MachineDeployments、MachinePools、MachineSet 和控制平面的状态。它还突出显示活动条件问题、提供商信息和配置模板计数，以帮助操作员快速识别降级或不健康的资源。

![集群详细信息和修复指南](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/cluster-health-cards.png)选择集群会打开详细的运行状况视图，显示控制平面和工作线程状态、机器信息、基础设施详细信息和资源状况。检测到问题时，仪表板会提供修复指南和诊断命令以帮助进行故障排除。

#### 将完整的 Cluster API 可见性引入 Headlamp[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#bring-full-cluster-api-visibility-into-headlamp)

集群列表视图显示管理集群中的所有集群资源，包括控制平面和工作副本状态。这使您可以一目了然地了解集群的整体运行状况。

![显示控制平面和工作副本状态的集群列表视图](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/cluster-list-view.png)

集群详细信息视图在单个页面上提供资源状态、条件、基础设施参考、控制平面参考和相关机器。

![显示资源状态和条件的集群详细视图](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/cluster-detail-overview.png)

![显示相关机器的集群详细视图](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/cluster-detail-machines.png)

#### 在可视化界面中探索 Cluster API 资源[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#explore-cluster-api-resources-in-a-visual-interface)

专用视图可用于 MachineDeployments、MachineSet、Machines 和 MachinePools。这些页面显示副本计数、所有权关系、提供程序 ID、版本和条件，以支持日常操作和调试。

![显示副本计数、所有权和条件的 MachineDeployment 列表视图](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/machine-resources-view.png)

#### 直接从 Headlamp[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#scale-workloads-directly-from-headlamp) 扩展工作负载

MachineDeployments 和 MachineSet 包含内置的 Scale 操作，允许您直接从 Headlamp 调整副本计数，而无需使用终端命令。

对于拓扑管理的集群，该插件还指示何时应在集群级别执行扩展。![MachineDeployment 的缩放对话框](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/scale-machine-deployments.png)

![拓扑管理的集群显示集群级别的扩展指导](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/scale-machine-sets.png)

#### 在没有原始 YAML[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#inspect-bootstrap-configuration-without-raw-yaml) 的情况下检查引导程序配置

可以以结构化格式查看引导配置，包括内联文件、kubelet 参数、额外卷以及连接或初始化设置。这样就无需手动检查原始 YAML 或机密。

![以结构化格式显示引导配置的 KubeadmConfig 详细视图](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/bootstrap-config-view.png)

#### 使用地图视图可视化集群关系[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#visualize-cluster-relationships-with-map-view)

可视化地图视图显示集群、控制平面和工作资源之间的关系。它提供了一种更快的方式来了解所有权层次结构和整体集群结构。

![显示集群、控制平面和工作线程资源关系的地图视图](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/topology-map-view.png)

#### Prometheus 指标集成[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#prometheus-metrics-integration)

Cluster API 插件与 [Headlamp Prometheus 插件](https://github.com/headlamp-k8s/plugins/tree/main/prometheus) 集成，可直接在 Cluster API 资源详细信息页面内显示指标。

安装并配置 Prometheus 插件后，指标会内嵌在集群、MachineDeployments、MachineSets 和 Machines 的详细信息页面上。您可以查看资源运行状况和性能数据以及状态条件和所有权关系，而无需切换到单独的仪表板。

这使得在调试或日常集群操作期间更容易将基础设施状态与实时指标关联起来，所有这些都在 Headlamp 内进行。

![集群详细信息页面上内嵌的 Prometheus 指标](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/prometheus-metrics-view.png)### 如何使用[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#how-to-use)

请参阅 [`plugins/cluster-api/README.md`](https://github.com/headlamp-k8s/plugins/blob/main/cluster-api/README.md) 了解安装和使用说明。

### 在 LFX 指导期间开发[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#developed-during-lfx-mentorship)

该插件是作为 Headlamp 项目下 CNCF LFX 指导计划的一部分而开发的。此次指导提供了与 Headlamp 社区密切合作的机会，同时构建功能以改善集群 API 管理体验。

重点不仅在于实现功能，还在于了解围绕集群 API 操作的实际可用性挑战。与导师和社区成员的讨论有助于确定插件的方向，改善用户体验，并优先考虑对平台团队最有用的功能。

指导还为大型开源项目提供了宝贵的经验：与维护者合作、参与设计讨论、处理发布反馈以及根据社区输入迭代功能。

该插件的开发工作正在进行中，除了最初的 Alpha 版本之外，还计划进行其他改进和功能。

### 反馈和问题[](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/#feedback-and-questions)

这是一个 Alpha 版本，社区反馈直接决定了接下来的内容。

- 错误报告：[打开问题](https://github.com/kubernetes-sigs/headlamp/issues)
- 功能请求：[开始讨论](https://github.com/kubernetes-sigs/headlamp/discussions)
- 贡献：[欢迎 PR](https://github.com/kubernetes-sigs/headlamp/pulls)
- Kubernetes Slack：[加入#headlamp 频道](https://slack.k8s.io/) 进行提问和讨论

- [←上一页](https://kubernetes.io/blog/2026/06/25/visual-context-volcano-headlamp-plugin/)
- [下一页→](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/)

最后修改时间为太平洋标准时间 2026 年 6 月 21 日晚上 9:36：[调整博客文章标题 (7bf3df0ce7)](https://github.com/kubernetes/website/commit/7bf3df0ce739b9ec7fac9b9feb9d1ed8cf45d23b)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
