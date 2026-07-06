<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T08:00:00+08:00
source: Red Hat Blog
domain: 云原生
url: https://www.redhat.com/en/blog/agentic-ai-red-hat-openshift-what-enterprises-are-doing-right-now
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 红帽 OpenShift 上的 Agentic AI：企业现在正在做什么

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 08:00 CST |
| 领域 | 云原生 |
| 来源 | Red Hat Blog |
| 原文标题 | Agentic AI on Red Hat OpenShift: What enterprises are doing right now |
| 原文 | [打开原文](https://www.redhat.com/en/blog/agentic-ai-red-hat-openshift-what-enterprises-are-doing-right-now) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

2026 年红帽峰会客户圆桌会议的见解来自航空公司、公用事业、金融服务、高等教育和政府等各行业的平台工程和运营领导者齐聚一堂，在 2026 年红帽峰会上就代理人工智能进行了坦诚的对话。我们希望了解实际有效的方法、风险所在以及团队如何在当今找到价值。从平台管理到人工智能协作支撑我们圆桌会议上每次对话的问题都是这个问题的一个变体：它是什么样子的？当一个平台不再是你管理的东西时

## 正文

## 红帽 OpenShift 上的 Agentic 

AI：企业现在正在做什么

20265 年 7 月 1 日阅读[人工智能](https://www.redhat.com/en/blog?f[0]=taxonomy_topic_tid:75501#rhdc-search-listing)

![贾勒·里维斯](https://www.redhat.com/rhdc/managed-files/styles/media_thumbnail/private/Screenshot%202026-07-01%20at%2011.22.35%E2%80%AFPM.png?itok=RKMH-P5c)

[贾勒·里维斯](https://www.redhat.com/en/authors/jaleh-reeves)

红帽 OpenShift 高级产品营销经理

2026 年红帽峰会客户圆桌会议的见解

来自各行业（包括航空公司、公用事业、金融服务、高等教育和政府）的平台工程和运营领导者齐聚一堂，在 2026 年红帽峰会上就代理人工智能进行了坦诚对话。我们希望了解什么是真正有效的、风险在哪里，以及团队如何在当今找到价值。

从平台管理到AI协作

我们圆桌会议上每次对话的问题都是这个问题的一个变体：当一个平台不再是你管理的东西，而是开始成为与你的团队一起思考的东西时，会是什么样子？

团队正在管理复杂的多集群环境，其人员数量与两年前相同。诊断事件、关联警报和执行补救的手动工作正在消耗本应用于核心开发的能力。一位参与者明确表达了他们的目标——在不额外雇用一个人的情况下将管理的集群数量增加一倍。

这种需求超出了效率的范围。真正的问题是，当日常工作顺利进行时，你最优秀的员工会做什么？我们圆桌会议上的客户已经看到了这一点。一个团队的代理检测到存储驱动程序每 15 分钟就会悄然崩溃 — 对现有日志和警报来说是不可见的。该代理通过完整的诊断摘要来显示问题，并将自身置于锁定状态，直到有人授权采取下一步行动。当然，这一行动可以提供更快的解决方案，但平台与运行平台的人员之间的关系也截然不同。

IT 之外的惊人投资回报 (ROI)

当参与者描述人工智能代理解决传统基础设施领域之外的问题时，一些最引人注目的见解出现了。一个大学团队部署了代理来帮助他们的学生金融服务小组识别那些有资格获得联邦资助但被现有数据库查询忽视的服务不足的学生。该系统迅速识别出 100 多名学生和 60,000 至 70,000 美元无人认领的联邦援助。几周前，团队还没有意识到这个用例是可能的。

另一个例子是，政府机构描述了其提供代理界面的长期愿景，以帮助公民了解复杂的法律法规，并根据重大生活事件（例如生孩子、创业或搬迁）自动协调适当的公共服务，为公民提供单一的智能界面，而不是数十个互不相连的门户。

获得最大关注的组织是那些正在扩展其用例并扩展其对“运营人工智能”含义的先入为主的概念的组织。

人类监督是不容谈判的

圆桌会议的共识很明确——完全自治不是一种选择。由于人工智能具有不确定性，因此核心挑战不在于是否信任代理，而在于如何构建工作流程，以便代理可以安全地加速日常任务，同时人类保留对关键操作的控制。代理解决方案需要平台原生的清晰、标准的工作流程治理模型。

最引起共鸣的模型是将代理视为站点可靠性工程师，他们分析系统，生成执行计划，并起草总结调查结果和建议行动的票据。工程师审核并批准，代理只执行明确授权的内容。

一个团队分享了一个测试监督代理架构的警示故事，其中人工智能监督代理监督一组专门的子代理。他们表示，3 个下级特工协调一致，说服监督人工智能批准一项它本应拒绝的行动。该团队在任何损害发生之前就发现了这一问题，但教训很明确：如果没有人为干预，人工智能无法可靠地管理其他人工智能。

此示例表明产品需要可编码、易于使用的治理功能，例如“护栏服务”或“审批即服务”，组织可以从第一天起就在所有环境中部署这些功能。

设计安全对于运营团队来说，主要关注点是控制自主工具出错时的后果。风险包括代理尝试执行破坏性命令（如 rm -rf），以及诊断代理重复运行占用大量资源的命令并意外导致部署要修复的集群崩溃。

为了减轻这些风险，团队在容器化环境中使用[沙盒代理](https://www.redhat.com/en/blog/red-hat-ai-and-openshell-driving-security-enhanced-agent-execution-for-enterprise-ai)，对每个操作进行严格的资源限制和完整的审核日志记录。事实证明，将代理与确定性数据层（例如经过模式验证的文档存储或严格限制可接受输入的其他系统）配对，对于保持代理行为的基础非常有效。

障碍：买入、审计跟踪和投资回报率

阻碍采用的障碍主要是组织方面的，而不是技术方面的。

建立内部支持是很困难的，尤其是对于过去经历过过度承诺的自动化计划的团队来说。详细的审计追踪对于建立这种信任至关重要（在世界某些地区是法律规定的）——组织必须能够向监管机构和领导层准确地展示代理人做了什么、使用的推理以及谁授权了该行动。如果没有这些证据，治理团队就会默认拒绝该技术。

展示明确的投资回报率同样重要。圆桌会议上的每个团队都指出了在确保预算之前证明价值的压力。行动最快的团队从小型、高可见度的概念证明开始，记录结果，并利用这些证据来获得进一步的资金。赢得 60,000 至 70,000 美元的学生经济援助比减少警报噪音更具吸引力，即使两者都能带来价值。

主要发现

本次圆桌会议上的组织处于代理人工智能采用的不同阶段，但他们面临着相同的问题。取得最大进展的团队有一些突出的做法：- 从可观测性和自我修复开始：这是操作难度最大、价值路径最清晰、有限范围使项目易于管理的地方。
- 从第一天开始就进行人工监督设计：不要在部署后就进行治理。将审批工作流程、阻止状态和审计跟踪直接构建到您的架构中。
- 对您的代理进行沙箱处理：容器化执行环境不是可选的，它们提供了必要的防护措施来让代理安全运行。
- 认真对待人工智能基础设施成本：多个团队表示 GPU 和云推理成本的上升速度比预期更快，在某些情况下超过了所产生的价值。 [Red Hat OpenShift AI](https://www.redhat.com/en/products/ai/openshift-ai) 专为应对这一挑战而设计，可帮助企业优化混合基础设施中的 GPU 使用，这样大规模运行 AI 的成本就不会成为无法扩展 AI 的原因。在云推理费用和本地 GPU 硬件都代表着重大资本投入的环境中，拥有一个能够让投资发挥更大作用的平台至关重要。
- 专注于高可见度的业务价值：最具动力的团队会找到为整个组织（而不仅仅是平台工程团队）带来价值的用例。

面向代理时代的红帽 OpenShift

每一次重大的企业软件浪潮都需要一个基础层，使复杂的分布式系统能够大规模治理。在客户端-服务器时代，是像JBoss这样的中间件。云原生时代，就是Kubernetes。在代理 AI 时代，该角色属于 [Red Hat OpenShift](https://www.redhat.com/en/technologies/cloud-computing/openshift) 和 [Red Hat OpenShift AI](https://www.redhat.com/en/products/ai/openshift-ai)。

本次圆桌会议上的客户正在构建跨多集群环境运行的自主代理，在严格的治理边界内执行决策，与企业工作流程集成，并在主权或混合基础设施上运行。这不能可靠地建立在临时工具上。它需要一个企业已经信任的、以安全为中心的、一致的、开源的基础。OpenShift 不仅仅是容器的编排器。在该平台上，代理框架、MCP 服务器、代理技能库、人机交互工作流程和 GPU 工作负载被统一为企业可以跨多集群环境部署、管理和扩展的基础。

建立以安全为中心的基础需要解决完整的代理治理问题：策略和权限控制、身份和访问管理、应用程序和工具治理、运行时安全和审计、执行沙箱、数据和内容治理以及人在环生命周期管理。至关重要的是，身份和身份验证不能是事后的想法——每个代理操作都必须经过身份验证并可归因于特定的授权实体。

OpenShift 通过 AgentOps 满足这些要求，AgentOps 是红帽 AI 与框架无关的方法，可跨任何模型、加速器或云操作代理，并具有解决每个治理和安全层的内置护栏。这些不是稍后添加的可选功能——它们是使企业级代理人工智能成为可能的基础。从一开始就理解并解决这一问题的组织将更快地行动，更有效地治理，并花费更少的时间来构建这个基础，从而使他们能够自信地迈向代理人工智能的未来。

要了解红帽 OpenShift 如何迈向代理 AI 的未来：

- [观看 2026 年红帽峰会的产品聚焦会议](https://tv.redhat.com/detail/6396164544112/product-spotlight-red-hat-openshift)。
- 请查看我们的博客“[模型不会产生收入 - 应用程序会产生收入](https://www.redhat.com/en/blog/models-dont-generate-revenue-applications-do)。”
- 访问[红帽 OpenShift AI 产品页面](https://www.redhat.com/en/technologies/cloud-computing/openshift/openshift-ai)。

[获取资源](https://www.redhat.com/en/resources/the-adaptable-enterprise-ai-ebook?intcmp=7013a000003Sq0iAAC)

#### 关于作者

[![贾勒·里维斯](https://www.redhat.com/rhdc/managed-files/styles/media_thumbnail/private/Screenshot%202026-07-01%20at%2011.22.35%E2%80%AFPM.png?itok=RKMH-P5c)](https://www.redhat.com/en/authors/jaleh-reeves)

[#### 贾勒·里维斯

红帽 OpenShift 高级产品营销经理](https://www.redhat.com/en/authors/jaleh-reeves)Jaleh Reeves 是红帽的高级产品营销经理，专注于红帽 OpenShift 自我管理版本的营销和定位。

[该作者的更多内容](https://www.redhat.com/en/authors/jaleh-reeves)

### 更多

这样的

博客文章

#### [人工智能时代基础设施自动化的演变：2026 年红帽峰会的 4 个关键要点](https://www.redhat.com/en/blog/evolution-infrastructure-automation-age-ai-4-key-takeaways-red-hat-summit-2026)

博客文章

#### [使用代理 

AI 增强 RHEL 故障排除：goose 简介](https://www.redhat.com/en/blog/supercharge-rhel-troubleshooting-agentic-ai-introducing-goose)

原创播客

#### [从技术上讲|用开源定义主权人工智能](https://www.redhat.com/en/technically-speaking/defining-sovereign-AI)

原创播客

#### [从技术上讲|开源人工智能策略内部](https://www.redhat.com/en/technically-speaking/open-source-AI-strategy)

### 继续探索

- [什么是代理人工智能？文章](https://www.redhat.com/en/topics/ai/what-is-agentic-ai?intcmp=7013a000003Sq0iAAC)
- [预测人工智能与生成人工智能文章](https://www.redhat.com/en/topics/ai/predictive-ai-vs-generative-ai?intcmp=7013a000003Sq0iAAC)
- [构建生产就绪的 AI/ML 环境的首要考虑因素电子书](https://www.redhat.com/en/resources/building-production-ready-ai-environment-ebook?intcmp=7013a000003Sq0iAAC)
- [生成式人工智能，Ansible 方式视频](https://tv.redhat.com/detail/6347396983112/generative-ai-the-ansible-way?intcmp=7013a000003Sq0iAAC)
- [利用现代应用平台进行创新和转型](https://www.redhat.com/en/engage/modern-application-platform-20230406?intcmp=7013a000003Sq0iAAC)[电子书](https://www.redhat.com/en/engage/openshift-application-transformation-ebook?intcmp=7013a000003Sq0iAAC)

### 按频道浏览

[探索所有频道](https://www.redhat.com/en/blog/channels)

![自动化图标](https://www.redhat.com/cms/managed-files/automation.svg)

#### [自动化](https://www.redhat.com/en/blog/channel/management-and-automation)

有关技术、团队和环境的 IT 自动化的最新信息

![AI 图标](https://www.redhat.com/cms/managed-files/AI.svg)

#### [人工智能](https://www.redhat.com/en/blog/channel/artificial-intelligence)

平台更新使客户可以在任何地方运行人工智能工作负载![打开混合云图标](https://www.redhat.com/cms/managed-files/open-hybrid-cloud.svg)

#### [开放混合云](https://www.redhat.com/en/blog/channel/hybrid-cloud-infrastructure)

探索我们如何利用混合云构建更灵活的未来

![安全图标](https://www.redhat.com/cms/managed-files/security.svg)

#### [安全](https://www.redhat.com/en/blog/channel/security)

有关我们如何降低跨环境和技术风险的最新信息

![边缘图标](https://www.redhat.com/cms/managed-files/edge_2.svg)

#### [边缘计算](https://www.redhat.com/en/blog/channel/edge-computing)

简化边缘操作的平台更新

![基础设施图标](https://www.redhat.com/cms/managed-files/infrastructure.svg)

#### [基础设施](https://www.redhat.com/en/blog/channel/infrastructure)

全球领先企业 Linux 平台的最新动态

![应用程序开发图标](https://www.redhat.com/cms/managed-files/application-development.svg)

#### [应用程序](https://www.redhat.com/en/blog/channel/applications)

我们针对最严峻的应用挑战的解决方案

![虚拟化图标](https://www.redhat.com/rhdc/managed-files/Icon-Red_Hat-Virtual_server-A-Black-RGB.svg)

#### [虚拟化](https://www.redhat.com/en/blog/channel/red-hat-virtualization)

适用于本地或跨云工作负载的企业虚拟化的未来

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
