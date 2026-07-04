<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-03T19:00:00+08:00
source: CNCF Blog
domain: 云原生
url: https://www.cncf.io/blog/2026/07/03/how-data-sovereignty-is-changing-cloud-native-infrastructure-design/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# 数据主权如何改变云原生基础设施设计

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-03 19:00 CST |
| 领域 | 云原生 |
| 来源 | CNCF Blog |
| 原文标题 | How data sovereignty is changing cloud native infrastructure design |
| 原文 | [打开原文](https://www.cncf.io/blog/2026/07/03/how-data-sovereignty-is-changing-cloud-native-infrastructure-design/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

The core issue isn’t where your server sits.谁可以被迫交出上面的东西。 For years, cloud providers treated sovereignty as a geography problem.选择一个区域。选择一个国家。保持...

## 正文

The core issue isn’t where your server sits.谁可以被迫交出上面的东西。

多年来，云提供商将主权视为地理问题。选择一个区域。选择一个国家。将您的数据保存在本地。

但美国《云法案》等法律改变了这一现状。数据访问遵循公司控制，而不是物理位置。法兰克福的一家超大规模运营基础设施仍受管辖其母公司的法律的约束。 Region selection is a geographic control. Sovereignty is a jurisdictional one.

这种区别正在日益影响基础设施决策。

2026 年 6 月提出的[欧盟云和人工智能发展法案 (CADA)](https://digital-strategy.ec.europa.eu/en/library/proposal-cloud-and-ai-development-act-cada?utm_source=chatgpt.com) 为公共部门云采购引入了四层主权框架。加拿大联邦政府现在对云供应商在加拿大数据驻留和管辖控制方面进行评分。许多国家现在都维持数据本地化、主权或驻留要求。监管框架越来越多地超出数据驻留范围，扩展到运营控制、供应链透明度、可移植性和弹性等问题。

欧盟数据法案促进互操作性并减少更换提供商的障碍。 《人工智能法案》引入了有关人工智能系统的可追溯性、治理和问责制的要求。 NIS2 和 DORA 更加重视供应链依赖性、运营弹性和集中风险。类似的对话正在全球各个司法管辖区出现。

总而言之，这些发展预示着未来基础设施控制将不再仅仅是一种技术偏好。它日益成为监管期望。

这种转变通常被视为隐私讨论。事实上，这越来越成为一个关于弹性的讨论。防止外国法律干预的相同架构还可以减少制裁、贸易争端、服务暂停、许可变更、供应商退出和其他形式的外部依赖的风险。

对于平台工程师来说，挑战很简单：如何在不牺牲自动化、可移植性和运营效率的情况下满足主权要求，而正是这些因素使云基础设施具有吸引力？

#### The pattern emerging in production在整个欧洲，受监管的

企业越来越多地利用开源组件组装主权平台，而不是从超大规模企业购买主权作为高级功能。

这种模式越来越熟悉。 Kubernetes 提供编排和策略层。 GitOps provides operational consistency across jurisdictions. OpenStack 提供底层基础设施。它们共同允许组织通过架构而不是合同来执行主权要求。

这些不是概念验证部署。国家铁路运营商、主要银行和欧洲电信公司已经在使用 Kubernetes、GitOps 和政策驱动的自动化来跨主权环境大规模运行受监管的工作负载。

模式是一致的：Kubernetes 用于治理和编排，OpenStack 用于主权基础设施，策略即代码用于执行，声明性操作用于可重复性。

#### Kubernetes 作为主权控制平面

建设主权基础设施是一项挑战。持续操作是另一回事。

大多数合规计划仍然严重依赖文档、审查和手动流程。 Those approaches work, but they don’t scale particularly well across hundreds or thousands of workloads. Kubernetes changes that by allowing sovereignty requirements to be enforced directly by the platform.

Admission controllers can enforce workload placement before a pod is ever scheduled. Node affinity rules ensure workloads only land on approved infrastructure within the correct jurisdiction.命名空间隔离在租户、环境或区域之间创建清晰的边界。 Policy engines evaluate every API request against sovereignty requirements and reject non-compliant resources before they reach production.

Policy as code extends the same approach operationally.主权策略存在于 Git 中，经过同行评审，通过 CI 管道进行测试，并在部署时自动实施。 Tools such as OPA/Gatekeeper and Kyverno allow organizations to encode jurisdictional requirements directly into the cluster. The result is continuous enforcement rather than periodic verification.每一项政策变化都是可追溯的。每个部署决策都是可审计的。

到那时，主权就不再是一个过程，而是成为一种平台能力。但 Kubernetes 仍然依赖于其下面的基础设施层。计算、网络、存储和身份都必须来自某个地方。如果该基础与您管辖范围之外的组织运营的平台相关联，那么在 Kubernetes 层执行的一些保证将变得更难以维护。

这就是 OpenStack 的用武之地。

OpenStack 提供 Kubernetes 所依赖的基础设施服务，同时允许组织在自己的管辖范围内运营这些服务。通过 Ironic 的裸机配置消除了工作负载和硬件之间对专有虚拟机管理程序的需求。 Keystone 保持身份管理自托管。 Neutron provides network isolation under the operator’s control. Ceph 在您拥有和运营的基础设施上提供分布式存储。

OpenStack can be deployed entirely within a controlled environment.没有许可证服务器。没有强制性遥测服务。 No external dependencies required for day-to-day operations.

组合才是使架构发挥作用的原因。 Kubernetes provides the policy and enforcement layer. OpenStack provides the infrastructure foundation beneath it.它们一起允许主权要求在代码中实现，自动执行，并在整个堆栈中进行审核。

#### 困难的部分：操作它

主权通常意味着每个管辖区有不同的环境。现在，每次升级、证书轮换、RBAC 更改、安全补丁和容量规划练习都发生在多个集群上，而不是一个集群上。

GitOps 使这在操作上易于管理。

Git 存储库包含共享配置和特定于管辖区的覆盖。每个集群内运行的 GitOps 控制器不断根据所需状态进行协调。不需要集中控制平面。每个集群在本地提取并应用自己的配置。

运营效益显而易见，但合规效益也同样重要。每项更改都会经过审核、版本控制和审核。当有人询问在特定时间点集群中正在运行什么时，答案已经在提交历史记录中。

同样的原则也适用于软件供应链。 SBOM、映像签名和准入策略有助于确保只有经过验证的工作负载才能进入生产环境。对于追求更高级别主权的组织来说，可见性不能仅限于操作系统。固件、管理控制器和硬件组件位于软件堆栈下方，通常可以广泛访问主机本身。这就是为什么硬件物料清单和固件验证也成为主权对话的一部分。

#### 接下来会发生什么

基础设施建设已经在进行中。 CADA 的目标是在未来几年大幅扩大欧洲数据中心的容量，但仅靠硬件并不能创造主权。平台层与其下面的基础设施一样重要。

AI is making that reality even more visible.随着监管机构更加重视模型的训练、管理和审计方式，培训基础设施越来越多地通过与数据本身相同的主权视角进行评估。

联邦学习是如何改变架构的一个例子。训练不是将数据移动到中央位置，而是在数据已经驻留的地方进行。 Sovereign Kubernetes clusters perform local training while only aggregated model updates move between jurisdictions. The same policies, namespace boundaries, and governance controls used for compliance become the foundation for distributed AI systems.

对于平台团队来说，问题不再是主权要求是否到来。他们已经在影响采购决策、基础设施设计和运营模式。

好消息是构建模块已经存在。 Kubernetes 提供编排和策略框架。 OpenStack 提供基础设施基础。 GitOps、策略引擎、软件供应链安全和身份完成了这一切。

多年来，云基础设施针对集中化进行了优化。主权正在朝相反的方向发展：更多的区域控制、更大的透明度和更强的运营所有权。

问题不再是主权是否会影响基础设施设计。

问题是主权是否仍然是组织记录的东西，或者是他们的平台可以强制执行的东西。

Many of the technologies discussed in this article are developed and operated in the open.在 GitHub 上探索 VEXXHOST 的开源工作和贡献：[https://github.com/vexxhost](https://github.com/vexxhost)。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
