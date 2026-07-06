<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-25T02:00:00+08:00
source: Kubernetes Blog
domain: 云原生
url: https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 聚焦 WG 设备管理

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-25 02:00 CST |
| 领域 | 云原生 |
| 来源 | Kubernetes Blog |
| 原文标题 | Spotlight on WG Device Management |
| 原文 | [打开原文](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

Kubernetes 上的人工智能、边缘计算和电信工作负载的日益普及对硬件管理提出了新的要求。我们现在需要 CPU 时间和内存分配之外的硬件规范。这包括分配 GPU、TPU、网络接口和其他硬件，有时在 Pod 启动后分配，有时通过分时分配。有效管理这种专用硬件是设备管理工作组的使命。他们的基石项目动态资源分配 (DRA) 最近已进入 GA 阶段，标志着该项目大规模处理硬件密集型工作负载的方式发生了根本性转变。在这个聚光灯下，我们与工作组主席 Kevin Klues、Patrick Ohly 和 John Belamaric 坐下来讨论遗留设备模型的局限性、调度的 NP 难题，以及他们如何为 Kubernetes 构建一个更加可编程、硬件感知的未来。设备管理简介 Natalie Fisher：您能介绍一下您自己、您的角色以及您是如何参与设备管理工作组的吗？凯文·克鲁斯：我的名字是凯文·克鲁斯。我是 NVIDIA 的杰出工程师。我曾担任设备管理工作的联合主席

## 正文

## 聚焦 WG 设备管理

作者：娜塔莉·费希尔2026 年 6 月 24 日星期三

Kubernetes 上的人工智能、边缘计算和电信工作负载的日益普及对硬件管理提出了新的要求。我们现在需要 CPU 时间和内存分配之外的硬件规范。这包括分配 GPU、TPU、网络接口和其他硬件，有时在 Pod 启动后分配，有时通过分时分配。

有效管理这种专用硬件是[设备管理工作组](https://www.kubernetes.dev/community/community-groups/wg/device-management/) 的使命。他们的基石项目 [动态资源分配 (DRA)](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/) 最近进入 GA，标志着该项目大规模处理硬件密集型工作负载的方式发生了根本性转变。

在这个聚光灯下，我们与工作组主席 [Kevin Klues](https://github.com/klueska)、[Patrick Ohly](https://github.com/pohly) 和 [John Belamaric](https://github.com/johnbelamaric) 坐下来讨论遗留设备模型的局限性、调度的 NP 难题，以及他们如何为 Kubernetes 构建一个更加可编程、硬件感知的未来。

### 设备管理简介[](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/#introducing-device-management)

Natalie Fisher：您能介绍一下您自己、您的角色以及您是如何参与设备管理工作组的吗？

凯文·克鲁斯：我的名字是凯文·克鲁斯。我是 NVIDIA 的杰出工程师。自 Kubecon EU 2024 年设备管理工作组成立以来，我一直担任设备管理工作组的联合主席。自 2019 年/2020 年成立以来，我还参与了 DRA（工作组的主要交付成果）。自 2019 年以来，我也是 kubelet 维护者，重点关注其设备管理器、CPU 管理器和拓扑管理器子组件。我们在使用这些组件来处理依赖外部加速器（例如 GPU）的工作负载时遇到的挑战正是促使我们首先开始研究 DRA 的原因。Patrick Ohly：我是英特尔的首席工程师。在 Kubernetes 中，我是 [SIG 测试](https://www.kubernetes.dev/community/community-groups/sigs/testing/) 和 [SIG Instrumentation](https://www.kubernetes.dev/community/community-groups/sigs/instrumentation/) 的技术主管以及设备管理工作组的联合主席。我是结构化日志工作组的联合主席和指导委员会的成员。我对 Kubernetes 的一些早期贡献包括[临时 CSI 卷](https://kubernetes.io/docs/concepts/storage/ephemeral-volumes/) 和存储容量跟踪，因此我在 API 设计、实现和调度方面拥有一些经验。我们知道，为加速器引入一个重要的新 API 会很困难。有点愚蠢的是，我在 2020 年接受了这一挑战，编写了最初的 DRA KEP（现在称为“经典 DRA”）并实现了其中的大部分内容，然后为今天的“结构化参数 DRA”重新开始了第二个 KEP。最初，让维护者相信这项工作是必要的是一场艰苦的战斗。直到 2023 年左右，人们对 DRA 的兴趣才有所回升，从而导致了工作组的成立。

John Belamaric：我是 Google 的高级 SWE，也是设备管理工作组自成立以来的第三任联合主席。自 2019 年以来，我也是 [SIG Architecture](https://www.kubernetes.dev/community/community-groups/sigs/architecture/) 的联合主席。正如 Patrick 提到的，2023 年末，人们对 DRA 的兴趣真正回升。最初的实现使自动缩放变得非常具有挑战性，因此社区对将其推进到测试版存在一些担忧。我参与其中，试图帮助解决其中一些问题，我们三个人和蒂姆·霍金在接下来的几个月里努力工作，围绕新设计达成共识。为了促进这种合作，我们在 2024 年巴黎 KubeCon 上讨论后成立了工作组。

### 问题及解决方案[](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/#the-problem-and-the-solution)

该工作组从根本上重新思考 Kubernetes 如何与专用硬件交互。这一演变的核心是动态资源分配（DRA）。 DRA 没有将设备视为简单的整数，而是提供了一个结构化框架，将设备管理分为四个不同的阶段：- 建模：供应商使用 ResourceSlice API 来宣传其硬件的精细功能和容量。
- 请求：用户通过“ResourceClaim” API 定义其特定的硬件需求，例如 GPU 内存或互连要求。
- 调度：Kubernetes 调度程序使用这些 API 来智能地将工作负载需求与可用硬件相匹配。
- 启动：一旦匹配成功，系统就会处理“握手”，为 Pod 的使用做好准备并确保设备安全。

NF：对于读者来说，可能不熟悉什么是设备管理工作组，它试图解决什么问题？

KK：设备管理工作组的宗旨是在 Kubernetes 工作负载中实现加速器和其他专用硬件的简单高效配置、共享和分配。想想 GPU、TPU、FPGA 和类似的设备，它们并不完全适合 Kubernetes 的传统资源模型。

我们要解决的问题是旧的设备插件 API（它是 Kubernetes 中公开硬件加速器的主要机制）从根本上是有限的。它将设备视为不透明的整数：您可以请求“2 个 GPU”，但您无法说出任何有关您需要哪些 GPU、它们应如何相互连接、是否可以共享或应如何分区的有意义的信息。对于简单的情况来说这很好，但现代 AI/ML 工作负载绝非简单。它们跨越多个节点，需要特定的互连拓扑，并且越来越需要动态共享或分区硬件。

该工作组的主要交付成果是动态资源分配 (DRA)，这是一个新框架，用灵活的声明性 API 取代了严格的设备插件模型。借助 DRA，工作负载可以描述其硬件要求（例如 GPU 类型、内存容量、互连拓扑、所需分区），驱动程序可以发布调度程序可以执行的细粒度设备属性。 DRA [已毕业](https://kubernetes.io/blog/2025/09/01/kubernetes-v1-34-dra-updates/) 到 Kubernetes 1.34 中的 GA，其周围的生态系统（例如驱动程序、工具和新的 API 扩展）正在快速发展。PO：正如 Kevin 所说，工作组是围绕开发 DRA 的现有工作而组建的。最初的工作是在少数人积极参与的情况下完成的，也许也只有在这样的设置下才能成功完成。但由于它涉及 Kubernetes 的许多不同领域，我们还需要一个地方来讨论这个问题，并让更广泛的 Kubernetes 维护者、设备供应商社区以及（在较小程度上）最终用户参与其中。工作组提供了这样的场所，定期举行在线会议（美洲/欧洲、中东和非洲地区一个时段，欧洲、中东和非洲地区/亚洲一个时段）和 KubeCon。

JB：DRA 是工作组解决的第一个问题。它的重点是设备的选择、分配和配置。我们将问题分为四个部分：供应商如何对设备进行建模并公布容量、用户如何请求、我们如何在公布的容量之上安排该请求以及我们如何执行该结果（即，我们如何使设备准备就绪并可供 Pod 使用）。

我们采取的方法的基础之一是意识到硬件令人难以置信的多样性以及硬件行业的快速变化。我们知道，如果 Kubernetes API 必须针对每种类型的硬件进行更改，我们就无法跟上变化。相反，我们创建了一种通用方法，解决对 Kubernetes 重要的硬件方面的问题。到目前为止，我们所做的重点是设备的调度和配置方面。我们构建了一个设备建模 API（ResourceSlice API），供应商用它来建模其设备的调度特性，并允许用户将任意配置传递给这些设备。通过这样做，Kubernetes 可以通过“编程”来了解设备的这些方面，而无需进行修改。

但就目前情况而言，DRA 非常注重调度。设备管理的其他方面也属于工作组的范围。特别是，我们正在研究设备故障检测和缓解，以及是否可以在 Kubernetes 中构建一些更好的支持来提供帮助。此外，正如凯文提到的，设备通常是分组分配和使用的，而不是单独使用。选择在组中协同工作的正确设备取决于它们的互连方式；例如，NVIDIA GPU 可能处于 NVLINK 域中的任意对任意结构排列，而 TPU 可能具有 3D 环面互连。这会影响设备的“选择、分配和配置”，我们还有很多工作要做来解决这些用例。

### 跨 SIG 的努力[](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/#a-cross-sig-effort)

由于设备管理涉及调度、节点操作、自动扩展、网络和 API 设计，因此这项工作自然会跨越 Kubernetes 项目的多个 SIG。

NF：这些 SIG 之间的协作在实践中是如何运作的？为什么有必要？

KK：设备管理几乎涉及 Kubernetes 堆栈的每一层，这就是为什么该工作组从一开始就被指定为跨 SIG 的工作。我们有五个利益相关者 SIG：sig-node、sig-scheduling、sig-autoscaling、sig-network 和 sig-architecture。

在实践中，工作组充当协调层。我们不直接拥有代码；相反，我们的交付成果采用位于各自 SIG 中的 KEP 和实现的形式。我们提供的是一个统一的论坛，构建调度器、kubelet、自动缩放器和网络平面的人们可以一起设计，而不是孤立的。

为什么这是必要的？考虑一个简单的示例：用户请求一组需要通过 NVLink 进行通信的 GPU。该要求涉及调度程序（将 Pod 放置在正确的节点上）、kubelet（配置设备并将它们暴露给容器）以及潜在的自动缩放（如果不存在，则提供正确的节点类型）。

如果这三个小组独立设计，最终会出现不一致的抽象、重复的逻辑和仅在生产中出现的集成错误。该工作组确保单一一致的 API 和数据模型流经所有这些组件。

跨SIG模型还意味着设计决策需要从多个角度进行审查。来自 sig-scheduling 的人会发现 sig-node 贡献者可能会忽略的调度程序复杂性，反之亦然。它会稍微减慢个人决策的速度，但会产生更稳健的结果。### 当前关注领域[](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/#current-focus-areas)

随着 DRA 现已普遍可用，工作组的重点已扩展到支持更先进的调度模型、共享语义、操作可见性以及对日益复杂的硬件拓扑的支持。

NF：工作组目前关注的一些关键举措或可交付成果是什么？

KK：我们在 [Kubernetes 项目委员会](https://github.com/orgs/kubernetes/projects/95) 维护一个项目委员会，实时跟踪我们的计划及其进度。

PO：有意限制核心 DRA 的范围和功能集，以便能够在合理的时间内升级到 GA。其他 KEP 按照自己的时间表添加更多功能。这些大致分为三类：

- 扩展DRA的表现力以支持更复杂的设备和调度场景。
- 支持第二天的操作，例如健康监测。
- 主要通过与工作负载感知调度集成来改进多节点支持。

除了项目板之外，我们还维护一个表格，其中总结了当前正在运行的所有 [KEP](https://www.kubernetes.dev/resources/keps/)。这是1.36的状态； 1.37 可能会添加更多内容：|凯普|描述 |发布 |  |  |  |  |
|:---|:---|:---|:---|:---|:---|:---|
|  |  | 1.32 | 1.32 1.33 | 1.33 1.34 | 1.34 1.35 | 1.35 1.36 | 1.36
| [4381](https://www.kubernetes.dev/resources/keps/4381) | DRA：结构化参数 |测试版 |测试版 |稳定|  |  |
| [5004](https://www.kubernetes.dev/resources/keps/5004) | DRA：通过 DRA 扩展资源请求 |  |  |阿尔法 |阿尔法 |测试版 |
| [4817](https://www.kubernetes.dev/resources/keps/4817) | DRA：资源声明状态 |阿尔法 |测试版 |测试版 |测试版 |测试版 |
| [5018](https://www.kubernetes.dev/resources/keps/5018) | DRA：命名空间控制的管理访问 |  |阿尔法 |测试版 |测试版 |稳定|
| [5055](https://www.kubernetes.dev/resources/keps/5055) | DRA：设备污染和容忍度 |  |阿尔法 |阿尔法 |阿尔法 |测试版 |
| [4816](https://www.kubernetes.dev/resources/keps/4816) | DRA：设备请求中的优先替代方案 |  |阿尔法 |测试版 |测试版 |稳定|
| [5075](https://www.kubernetes.dev/resources/keps/5075) | DRA：耗材容量 |  |  |阿尔法 |阿尔法 |测试版 |
| [4815](https://www.kubernetes.dev/resources/keps/4815) | DRA：可分区设备 |  |阿尔法 |阿尔法 |阿尔法 |测试版 |
| [5304](https://www.kubernetes.dev/resources/keps/5304) | DRA：属性向下 API |  |  |  |  |阿尔法 |
| [5729](https://www.kubernetes.dev/resources/keps/5729) | DRA：工作负载的 ResourceClaim 支持 |  |  |  |  |阿尔法 |
| [4680](https://www.kubernetes.dev/resources/keps/4680) | Pod Status 中的资源健康状态 |阿尔法 |阿尔法 |阿尔法 |阿尔法 |测试版 |
| [5517](https://www.kubernetes.dev/resources/keps/5517) | DRA：本机资源请求 |  |  |  |  |阿尔法 |
| [5677](https://www.kubernetes.dev/resources/keps/5677) | DRA：资源可用性可见性 |  |  |  |  |阿尔法 |
| [5007](https://www.kubernetes.dev/resources/keps/5007) | DRA：设备绑定条件 |  |  |阿尔法 |阿尔法 |测试版 |
| [5491](https://www.kubernetes.dev/resources/keps/5491) | DRA：属性的列表类型 |  |  |  |  |阿尔法 |

NF：核心挑战之一是高效的设备利用和共享。该领域正在取得哪些进展？

JB：好问题。一种思考方式是我们在两个主要 API 中所做的事情：ResourceClaim 和 ResourceSlice。ResourceClaim API 是用户请求设备的方式。我们构建了一些功能，使用户可以更灵活地提出他们的请求。例如，他们可以要求具有至少一定内存量的 GPU，而不是要求特定型号的 GPU。或者他们可以要求提供替代品列表：“我想要一个 A100 (80GB) GPU，但如果你没有，我会选择 2 个 A100 (40 GB) GPU。”这为调度程序提供了一些满足请求的选项，从而可以更好地获取和利用原本不会被选择的硬件。

ResourceClaim API 允许用户显式共享设备。您可以将多个容器（在相同或不同的 Pod 中）指向一个 ResourceClaim；如果设备支持的话，这允许在所有这些容器中使用该声明分配的设备。

ResourceSlice API 是供应商建模和宣传其设备的方式。这是我们实现对其他共享模型的支持的地方。例如，我们有一种方法来表示“重叠分区”，使调度程序能够动态选择一个 MIG 分区，并自动使任何重叠的 MIG 分区不可用。这与“给我任何具有 20GB 或更多内存的 GPU”之类的请求结合起来效果很好 - 调度程序可以使用 MIG 或真正的 GPU 来满足这一要求。

有些功能需要两者都进行更改。我们还有另一种共享方法，我们称之为“消耗能力”。在上述显式共享的情况下，用户需要将容器指向同一个ResourceClaim；多个容器和 Pod 之间共享一个 ResourceClaim。有了可消耗的容量，设备共享的工作方式更像是 Pod 共享节点的方式。用户创建一个 ResourceClaim 来请求一定数量的资源，例如“我需要一个具有 2Gbps 带宽的 NIC”。调度程序知道有一个具有 40Gbps 可用带宽的 NIC，因此它从 40Gbps 中分配 2Gbps 并将其提供给该 ResourceClaim。在这种情况下，每个 Pod 都有自己的 ResourceClaim，但底层设备在这些声明之间共享。由节点上的 DRA 驱动程序来正确设置设备以进行此类共享（在 NIC 情况下，可能通过创建子接口）。我们将其称为“平台介导的共享”，以区别于明确的“用户介导的共享”。### 现实世界的影响[](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/#real-world-impact)

虽然大部分工作都是技术性很强的，但根本目标是实用的：使 Kubernetes 能够更好地大规模支持现实世界的 AI/ML 和硬件密集型工作负载。

NF：当今用户在 Kubernetes 上运行硬件密集型工作负载（例如 AI/ML）时面临的最大挑战是什么？

PO：此类工作负载在几个方面与传统容器工作负载不同：它们可能由多个通信 Pod 组成，这些 Pod 都需要同时运行（“组调度”）。它们通常需要长时间运行且初始化成本昂贵，并且它们的性能对其运行位置敏感（节点内的拓扑以及多个 Pod 的节点之间的互连）。传统上，Kubernetes 调度程序无法很好地支持这两者，因为它一次调度一个 pod，并且不知道节点内的拓扑。多个外部调度程序试图填补这一空白，但这通常并不理想，特别是当 Kubernetes 调度程序将其他 pod 调度到同一集群时。

NF：平台工程师在设计 Kubernetes 平台时应如何考虑设备管理？

JB：我们仍在学习，但 DRA 的一个想法是实现向更多“需求驱动”规范的转变。这可以减少编写工作负载规范的最终用户与设置集群的集群管理员之间的耦合。用户可以指定他们的工作负载需求，并且调度程序可以找出如何满足它，而不是就标签约定达成一致并要求用户了解集群拓扑。如果我们能够做到这一点，它甚至可以使复杂的工作负载在集群之间更加可移植。

### 挑战和权衡[](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/#challenges-and-trade-offs)

与 Kubernetes 的许多领域一样，灵活性和表现力的提高也带来了新的复杂性，特别是在调度和优化方面。

NF：工作组目前正在解决哪些最困难的技术挑战？PO：灵活性和调度复杂性之间存在固有的冲突。当前的实现重点是找到一些满足所请求资源的解决方案，但它不一定是最好的解决方案，无论“最佳”意味着什么，这也并不总是很清楚。另一个重大挑战是将节点可分配资源（RAM、CPU）暴露为具有附加元数据的设备；这对于微调工作负载的调度是必要的，这些工作负载需要在节点上完美对齐以获得最佳性能。

JB：帕特里克的清单很好。复杂的设备建模很困难，并且确保我们构建正确的语义以使其适用于许多不同的硬件总是很棘手。

最重要的是，调度通常非常复杂，并且是一个 NP 难题。 DRA 添加的所有元数据和灵活性为调度程序提供了更多选择，这有利有弊。如果您的选择受到限制，更多选择会很有帮助，因为这意味着您可以安排一些原本无法安排的事情。但这也意味着，当给定集群中有多种可能性时，找到最佳解决方案就更加困难。到目前为止，DRA 在我们的常见用例中运行良好，但我们还有很多工作要做，以提高所选调度解决方案的最优性并确保做出该选择的性能。

### 展望未来[](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/#looking-ahead)

尽管面临挑战，整个工作组的贡献者仍然对创新的步伐和围绕 Kubernetes 设备管理形成的不断增长的社区感到兴奋。

NF：展望未来，您对 Kubernetes 设备管理的未来最兴奋的是什么？

KK：NVIDIA 最近向 Kubernetes 项目捐赠了 GPU 的 DRA 驱动程序。我个人很高兴更多的社区成员开始为该项目做出贡献并定义其未来方向。

PO：对我来说，主要是新贡献者和挺身而出提供帮助的人们的数量。这给审查提案和帮助开发人员实施和合并提案带来了新的挑战。看到其他人取得成功是件好事，也是值得的，这对未来来说是个好兆头，因为越来越多的人熟悉这个话题。JB：我对很多事情感到兴奋。该社区确实已经发展壮大，并且正在开发许多有趣的功能，可以对更复杂的设备进行建模，并更好地对多节点设备进行建模。

我真的很高兴看到人们以创造性的方式使用这些 API。它们主要是为了解决“设备”问题而设计的，但就像 Unix/Linux 中的“一切都是文件”一样，API 本身对于它们的建模内容非常灵活。他们确实构建了一个更具可编程性的调度程序，它可以有有趣的应用程序。例如，我最近使用 DRA 进行了原型设计，将 Pod 调度到本地已缓存大型 AI 模型的节点。它确实非常灵活，而且我对我们社区的创造力非常有信心，所以我认为我们会在生态系统中看到一些意想不到的解决方案。

## 参与其中[](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/#getting-involved)

NF：贡献者如何参与设备管理工作组？

KK：最简单的第一步是加入我们的邮件列表 [wg-device-management@kubernetes.io](mailto:wg-device-management@kubernetes.io)。订阅将自动将我们每两周一次的会议的日历邀请添加到您的日历中。

我们有两个会议时段来适应不同的时区：

- 欧洲/美洲：太平洋时间周二上午 8:30（每两周一次）
- 亚洲/欧洲：每周三上午 9:00 CET（每两周一次）

会议记录、议程和录音均可公开访问（可从 [设备管理页面](https://www.kubernetes.dev/community/community-groups/wg/device-management/#meetings) 获取链接）。在参加第一次会议之前，您可以了解正在进行的工作。

在 Slack 上，可以在 Kubernetes Slack 工作区的“#wg-device-management”中找到我们。这是快速提问或自我介绍的最佳场所。

如需更多实践贡献，NVIDIA GPU 的 DRA 驱动程序现已成为一个社区项目，也是一个很好的起点。这是一个现实世界的生产级实施，更广泛的社区现在正在共同塑造。

我们欢迎各个级别的贡献者 – 无论您是对 API 设计、调度程序内部结构、驱动程序开发还是文档感兴趣。过来打个招呼。

### 摘要[](https://kubernetes.io/blog/2026/06/24/wg-device-management-spotlight-2026/#summary)随着 Kubernetes 不断发展以支持 AI/ML 革命和高性能计算，WG 设备管理中发生的工作正在成为如何大规模调度和操作现代工作负载的基础。

从动态资源分配（DRA）的毕业到健康监控和拓扑感知调度的下一个前沿，该小组正在有效地改写软件和硬件之间的“握手”。

如果您有兴趣塑造硬件感知编排的未来，那么现在是参与的最佳时机。无论您是想帮助完善 API、构建驱动程序还是改进文档，工作组都欢迎来自整个社区的各种级别的经验和观点。

这是[原始文章](https://www.kubernetes.dev/blog/2026/06/24/wg-device-management-spotlight-2026) 的镜像。

- [←上一页](https://kubernetes.io/blog/2026/06/15/sig-storage-spotlight-2026/)
- [下一页→](https://kubernetes.io/blog/2026/06/25/headlamp-knative-plugin/)

最后修改时间为太平洋标准时间 2026 年 6 月 30 日下午 1:29：[固定网址 (78155dfa03)](https://github.com/kubernetes/website/commit/78155dfa03109a503f62da632807c5714f2a500e)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
