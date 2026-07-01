<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-30T19:38:00+08:00
source: CNCF Blog
domain: 数据中心 / 硬件
url: https://www.cncf.io/blog/2026/06/30/kepler-re-architected-improved-power-accuracy-and-a-community-call-to-action/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# 重新设计的开普勒：提高功率精度并呼吁社区采取行动！

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-30 19:38 CST |
| 领域 | 数据中心 / 硬件 |
| 来源 | CNCF Blog |
| 原文标题 | Kepler, re-architected: Improved power accuracy and a community call to action! |
| 原文 | [打开原文](https://www.cncf.io/blog/2026/06/30/kepler-re-architected-improved-power-accuracy-and-a-community-call-to-action/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

感谢 Laura Llinares、Mary Baldwin Hughes、Vimal Kumar 和 Sunil Thaha 对本博客文章和开普勒项目的重大贡献。 2024年数据中心占全球电力需求的1.5%，...

## 正文

感谢 Laura Llinares、Mary Baldwin Hughes、Vimal Kumar 和 Sunil Thaha 对本博客文章和开普勒项目的重大贡献。

根据国际能源署 2025 年发布的[“能源与人工智能”](https://www.iea.org/reports/energy-and-ai) 报告，数据中心在 2024 年占全球电力需求的 1.5%，预计到 2030 年将翻一番，达到 945 TWh 左右，部分原因是人工智能工作负载的快速增长。在 Kubernetes 集群中，没有简单的内置方法来为每个工作负载分配电力。 Kepler 解决了这个问题：它从硬件功率计中读取数据，将功耗归因于 Linux 进程，将其与 Kubernetes 集群中运行的 Pod 关联起来，并导出 Prometheus 指标。

自 2023 年作为沙盒项目加入 CNCF 以来，Kepler 的采用率不断增长。然而，原始架构依赖于 eBPF，虽然增加了粒度，但也产生了问题。首先，它需要“CAP_BPF”和“CAP_SYSADMIN”权限，这对许多生产环境来说是一个障碍。其次，事实证明，在这种精度水平上跟踪细粒度的内核级进程时，eBPF 很容易出错。此级别的数据不准确为我们需要训练的功率估计模型造成了瓶颈，以便在虚拟机 (VM) 上部署开普勒。除了权限提升和准确性问题之外，eBPF 集成还使学习曲线变得更加陡峭。它添加了复杂的抽象，使得扩展和维护代码库变得困难。

该团队决定正面应对这些挑战。我们希望让 Kepler 更易于配置和部署，不易出错，并且社区更容易扩展代码库。

维护团队做出了一个重大但令人兴奋的决定：重写开普勒。在这篇文章中，我们将介绍发生的变化、原因以及如何参与。有关此决定的更多信息，Vimal Kumar 在[本播客节目](https://www.youtube.com/watch?v=IWxwRmS2RYo) 中详细介绍了重写内容。

### 重新架构开普勒

要运行 Kepler，需要两个要素：容器化 Linux 进程的利用率信号和电表访问。 [电源归因](https://sustainable-computing.io/kepler/usage/power-attribution/) 文档指南解释了 Kepler 如何测量功耗并将其归因于进程、Pod 和其他 Kubernetes 内部结构。此前，Kepler 依靠 eBPF 来捕获利用率信号，这占了用户报告问题的大部分。与此同时，它导致了短暂、终止的流程缺失，导致能源足迹不准确、报告不足。

为了优先考虑易于采用和提高准确性，我们正在放弃 eBPF 并回归基础。我们重新架构的解决方案利用对标准“/proc”和“/sys”的只读访问。由于这些在 Linux 系统上普遍可用，因此它们需要显着降低的权限和最少的设置。通过消除复杂的配置开销，我们使 Kepler 更容易通过单个配置的 Helm 进行开箱即用部署。

对于功率指标，之前，Kepler 假设了硬编码的功率结构（例如，RAPL 由核心、DRAM 等组成）。然而，我们发现实际的硬件拓扑差异很大，这意味着旧的设计将数据归因于不存在的基本事实。重新架构的开普勒在运行时动态发现主机的功率计结构。通过适应底层硬件的布局，Kepler 现在可以根据实际可用性报告不同环境中的精确能源指标。

### 验证准确性改进

我们进行了两个实验来验证开普勒重写的准确性改进。

#### 实验 1：比较重写前和重写后的版本

第一个测试由 Laura Llinares (CERN) 领导，比较了重写前后的开普勒版本。我们在同一个裸机节点上同时部署了两个 Kepler 版本：

- kepler-old：以前的版本，发布带有 old_ 前缀的指标。
- kepler-new：重新架构的版本，发布没有前缀的干净指标。
- 智能电源管理接口 (IPMI)：硬件 BMC 功率计读数。

然后我们比较了节点级CPU能耗和容器级CPU能耗。

两个 Kepler 版本都读取 RAPL 包域（整个 CPU 插槽）。较新的开普勒版本将功率公开为瓦特计（“kepler_node_cpu_watts”）和焦耳计数器（“kepler_node_cpu_joules_total”和“kepler_container_cpu_joules_total”）。在如下所示的 Grafana 仪表板面板中，PromQL 用于使用 PromQL 的“rate()”从旧焦耳计数器中导出瓦特，以便所有系列共享相同的单位。

- 节点级CPU能耗|公制|版本 |
|:---|:---|
| `kepler_node_package_joules_total` |旧|
| `kepler_node_cpu_watts` |新 |

两个计数器都随着 CPU 包 RAPL 域在节点级别消耗的能量而增加。

- 容器级CPU能耗

|公制|版本 |
|:---|:---|
| `kepler_container_package_joules_total` |旧|
| `kepler_container_cpu_joules_total` |新 |

IPMI 是 BMC 的全节点功耗。它包括 CPU 之外的 DRAM、风扇、NIC 和 PSU 损耗，因此 Kepler 值预计为 IPMI 的 40-70%。由于 IPMI 测量整个节点，而 Kepler 仅测量 CPU，因此我们使用 IPMI 作为负载形状参考。 IPMI 在覆盖面板中显示为背景参考。当压力工作负载增加时，IPMI 和两个 Kepler 版本应该都会一起上升。与 IPMI 同步上升和下降的开普勒估计器可以正确跟踪负载。

![图：仪表板（来源）显示新旧开普勒针对 IPMI 的跟踪](https://www.cncf.io/wp-content/uploads/2026/06/image-5-5.jpg)

仪表板（[来源](https://github.com/sustainable-computing-io/kepler/blob/f6e275fee21e785c6034d86043e1bbd27604ca09/compose/dev/grafana/dashboards/dev/old-vs-new-accuracy.json)）显示针对 IPMI 的新旧开普勒跟踪

新的 Kepler node_cpu_watts 指标密切跟踪 IPMI 模式，并消除了旧的 node_pkg_joules 和 full_node_joules 计数器中超过 IPMI 真实值的多千瓦峰值。

#### 实验 2：可忽略的归因差距

由 Vimal Kumar（红帽）领导的第二个测试显示，在将节点功率与通过流程归因模型得出的功率进行比较时，归因差距可以忽略不计，这验证了开普勒新设计的准确性。系统测试使用渐进式压力测试工作负载。由此产生的核心和封装能量的 Grafana 仪表板显示，过程功率归因差距基本上为 0 瓦。

![图示：显示过程能源变化和归因差距的仪表板（源）面板](https://www.cncf.io/wp-content/uploads/2026/06/image-6-1.jpg)

显示过程能量变化和归因差距的仪表板（[来源](https://github.com/sustainable-computing-io/kepler/blob/main/compose/dev/grafana/dashboards/dev/dashboard.json)）面板![图示：显示核心能量变化和归因差距的仪表板（源）面板](https://www.cncf.io/wp-content/uploads/2026/06/image-6-1.jpg)

显示核心能量变化和归因差距的仪表板（[来源](https://github.com/sustainable-computing-io/kepler/blob/main/compose/dev/grafana/dashboards/dev/dashboard.json)）面板

此外，详细的增量图表明，总节点活跃能量与分配给各个进程的能量之间的差异很小，波动仅为几毫瓦。这种可以忽略不计的差异表明该架构能够在流程级别准确跟踪和分配电源使用情况。

最后但并非最不重要的一点是，我们添加了广泛的集成和单元测试，以达到 90% 的测试覆盖率。这提高了长期可维护性和结果的可信度。这是验证 Kepler 导出的功率指标​​准确性的关键。该项目将继续改进测试和验证框架，以不断提高开普勒的准确性。

### 接下来是什么？号召性用语

重写奠定了基础。我们的当务之急是改善裸机上的 CPU 功率归属，然后扩展到虚拟机。正确处理这一点是关键。它为接下来的一切奠定了基础。

展望未来，我们有很多令人兴奋的事情，并且有足够的空间可以提供帮助！我们正在寻找三个特定领域的贡献：- 尝试 GPU 功率监控：我们有一个用于 GPU 功率监控的实验标志，这对于 AI 和加速器密集型工作负载现在至关重要。我们需要运行 AI/ML 工作负载的最终用户来测试和验证 Kepler 的 [GPU 功率监控](https://github.com/sustainable-computing-io/kepler/blob/304d236299b2ed13e047b0fcf254c309e8f93b8a/docs/developer/design/architecture/gpu-power-monitoring.md) 功能。
- 训练虚拟机功率建模：我们需要具有机器学习经验的社区成员来（重新）训练模型，该模型可在硬件计数器不可用的虚拟化环境中估计功率。这将弥合虚拟化环境和物理能源信号之间的差距。
- 验证数据准确性：我们需要最终用户根据物理功率测量来测试开普勒，包括裸机上的 CPU 属性和 GPU 功率监控。如果您拥有带有 IPMI 或外部功率计的硬件，您的结果将直接影响我们改进模型的方式。
- 改进空闲功率归因：重写后，Kepler 仅对每个工作负载的活动 CPU 使用情况进行归因。然而，这过于简化了功率估计。虽然添加它是为了避免空闲状态和动态状态之间的混淆，但应该将其添加回来并更好地表达。

要测试 Kepler，请使用 [Helm](https://github.com/sustainable-computing-io/kepler#-quick-start-kubernetes-with-helm) 或 [Kepler Operator](https://github.com/sustainable-computing-io/kepler-operator) 安装它。使用 [Grafana 仪表板](https://github.com/sustainable-computing-io/kepler/tree/main/compose/dev/grafana/dashboards/dev) 探索指标。

如果您希望贡献、浏览并处理 [good First issues](https://github.com/sustainable-computing-io/kepler/issues?q=label%3A%22good+first+issue%22)，请打开一个新问题，或 [查看开放的 PR](https://github.com/sustainable-computing-io/kepler/pulls)。对于功能和更大的工作流，我们转向[增强提案](https://github.com/sustainable-computing-io/kepler/blob/main/docs/developer/proposal/index.md#creating-a-new-enhancement-proposal-ep)。这为社区提供了一种更清晰的方式来讨论想法、审查设计以及在实施之前就更大的变更进行协作。重写为开普勒奠定了坚实的基础。接下来会发生什么取决于建立在它之上的社区。加入我们的[每月两次的社区会议](https://zoom-lfx.platform.linuxfoundation.org/meetings/kepler?view=month) 和 [CNCF Slack](https://slack.cncf.io) 上的 #kepler-project 频道，以保持势头！ 💚

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
