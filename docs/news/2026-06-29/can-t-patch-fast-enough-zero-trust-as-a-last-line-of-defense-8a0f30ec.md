<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-29T08:00:00+08:00
source: Red Hat Blog
domain: 技术动态
url: https://www.redhat.com/en/blog/cant-patch-fast-enough-zero-trust-last-line-defense
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 补丁速度不够快？零信任作为最后一道防线

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-29 08:00 CST |
| 领域 | 技术动态 |
| 来源 | Red Hat Blog |
| 原文标题 | Can't patch fast enough? Zero trust as a last line of defense |
| 原文 | [打开原文](https://www.redhat.com/en/blog/cant-patch-fast-enough-zero-trust-last-line-defense) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

添加新功能和应用程序发展的速度直接提高了架构的复杂性。这种不懈的步伐不仅是出于对新功能的渴望，也是出于对新功能的渴望。由于不断发现新的漏洞，它的压力越来越大。修补单个关键依赖项可能会触发一系列所需的更新和意外的架构更改，因为每个产品和解决方案都带有无数的实现选项以及要启用或禁用的各种功能。根据您的特定环境定制这种复杂性使得保证每个组件都具有挑战性

## 正文

## 修补速度不够快？零信任作为最后一道防线

20268 年 6 月 29 日阅读[容器](https://www.redhat.com/en/blog?f[0]=taxonomy_topic_tid:9001#rhdc-search-listing)、[安全](https://www.redhat.com/en/blog?f[0]=taxonomy_topic_tid:4491#rhdc-search-listing)、[零信任](https://www.redhat.com/en/blog?f[0]=taxonomy_topic_tid:114051#rhdc-search-listing)

![Przemyslaw Roguski](https://www.redhat.com/rhdc/managed-files/styles/media_thumbnail/private/photo%20-%20Przemyslaw%20Roguski.jpg?itok=ZKtFaWyh)

[普热梅斯瓦夫·罗古斯基](https://www.redhat.com/en/authors/przemysław-roguski)

安全解决方案首席架构师

添加新功能和应用程序发展的速度直接提高了架构的复杂性。这种不懈的步伐不仅是出于对新功能的渴望，也是出于对新功能的渴望。由于不断发现新的漏洞，它的压力越来越大。修补单个关键依赖项可能会触发一系列所需的更新和意外的架构更改，因为每个产品和解决方案都带有无数的实现选项以及要启用或禁用的各种功能。根据您的特定环境定制这种复杂性使得保证每个组件都根据行业最佳实践进行部署变得具有挑战性。 [验证模式](https://validatedpatterns.io/) 通过为各种用例提供​​即用型、经过严格测试的部署模式来弥补这一差距，从而减少从头开始构建复杂的、以安全为重点的架构的需要。

### 关于漏洞管理的令人不安的事实

2025 年，发布了超过 40,000 个新 CVE。每天都有超过 100 个。如今，人工智能驱动的漏洞利用生成大大缩短了从漏洞披露到主动利用的时间。 “[追逐圣杯](https://www.redhat.com/en/blog/chasing-holy-grail-why-red-hats-hummingbird-project-aims-near-zero-cves)”展示了如果追求零 CVE 的满分，如果分散了对更深层次纵深防御策略的注意力，有时会适得其反。上午 9 点“干净”的组件到下午 5 点可能会出现新披露的漏洞。即使已知 CVE 为零，未知漏洞也始终存在。对于运行数百个容器化工作负载的企业环境来说，修补数学（一种误解，认为安全性只是一个数字游戏，CVE 越少意味着风险越小）。与在单个操作系统上运行的传统整体架构不同，分布式容器环境引入了显着更高的架构复杂性。无数的微服务和网络接触点提供了更多的配置选项，其中可能会出现问题并无意中造成安全漏洞。试图立即修复所有问题是一项西西弗斯任务，与现代基于风险的安全策略相冲突。它还忽略了一个基本事实：无论您多么积极地尝试应用更新，总会有滞后。

那么，在漏洞披露和补丁部署之间的间隙，您会做什么呢？答案在于一个已经存在多年但在今天比以往任何时候都更加重要的安全原则：零信任架构。

### 零信任对于您的 Red Hat OpenShift 集群意味着什么

[零信任不是您安装的产品](https://www.redhat.com/en/topics/security/what-is-zero-trust)。这是一种假设已经发生违规的架构哲学，要求每次交互都必须经过显式验证和授权。根据 [NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final)，零信任意味着删除仅基于资源（资产、应用程序或用户帐户）的物理或网络位置授予的隐式信任。身份验证和授权是在建立与企业资源的任何会话之前执行的离散功能。在 Kubernetes 和 Red Hat OpenShift 中实现零信任需要采用涵盖工作负载身份、秘密管理和运行时访问控制的多层方法。特别是在网络领域，这一理念最重要的影响之一是超越默认的扁平网络状态，即每个 Pod 都可以自由通信。默认情况下，Kubernetes 不应用内部网络限制，相当于仅仅因为建筑物有前门（例如集群入口控制器、API 网关或外围防火墙），就将建筑物中的每个内门解锁。然而，仅仅依靠这种外围防御对于现代云原生环境来说从根本上是不够的。

根据零信任模型，我们假设已经发生了违规行为，并且不良行为者已经存在于您的环境中，无论他们是绕过外围的外部攻击者、受损的供应链组件还是直接从内部操作的恶意内部威胁。通过实施 Kubernetes 网络资源限制，我们创建一个默认拒绝网络连接，并通过显式身份验证和授权来使用网络并访问附加到其上的其他资源（图 1）。

[![说明如何使用零信任创建默认拒绝网络连接，并需要显式身份验证和授权才能访问附加到其上的其他资源。](https://www.redhat.com/rhdc/managed-files/10000201000003BB000002C90D53D171AAAA75D3.webp)](https://www.redhat.com/rhdc/managed-files/10000201000003BB000002C90D53D171AAAA75D3.webp)

### 从理论到实践：分层零信任验证模式 (ZTVP)

为了将这些最佳实践转化为现实，我们利用[分层零信任验证模式 (ZTVP)](http://red.ht/ztvp)。经过验证的模式体现了基础设施即代码 (IaC) 最佳实践和 GitOps 自动化，大大缩短了专为安全性和可扩展性而设计的复杂 OpenShift 部署的设置时间。在过去三个月中，ZTVP 项目取得了重大进展，获得了[测试级别](https://validatedpatterns.io/learn/about-pattern-tiers-types/#tested-tier) 认证。

该模式将多个组件汇集到一个有凝聚力的、GitOps 部署的零信任架构中：- [零信任工作负载身份管理器](https://www.redhat.com/en/technologies/cloud-computing/openshift/zero-trust-workload-identity-manager)：为工作负载提供基于 SPIFFE/SPIRE 项目的短期加密身份。
- [HashiCorp Vault](https://www.hashicorp.com/en/products/vault)：以安全第一的方式存储敏感资产和集群机密，与 ZTWIM 集成以进行 JWT 身份验证。
- [Red Hat 版本的 Keycloak](https://access.redhat.com/products/red-hat-build-keycloak/)：管理用户身份验证和联合身份。
- [Red Hat Advanced Cluster Security for Kubernetes](https://www.redhat.com/en/technologies/cloud-computing/openshift/advanced-cluster-security-kubernetes)：充当智能安全大脑，提供统一的多集群监控、主动准入控制、实时行为异常检测以及在我们的示例中至关重要的网络策略分析器。

### 网络政策：最后一道防线

虽然网络策略经常被视为零信任的基础，但它们本身并不是一项原则。相反，它们是一种主动的架构机制，用于强制实现零信任模型的预期结果。红帽概述了[零信任的四个核心原则](https://www.redhat.com/en/topics/security/what-is-zero-trust#principles-and-concepts)，并且精心设计的网络策略积极支持其中的每一项原则：

- 微分段：通过在单个 Pod 级别管理流量，网络策略本质上将集群划分为精细的、安全性增强的分段。
- 最低权限访问：默认拒绝状态规定，工作负载仅被授予其运行绝对需要的确切网络权限，仅此而已。
- 外围化：安全控制不再只是集群的“前门”，而是直接应用于工作负载本身。
- 假设违规：通过主动消除横向攻击路径，严格的入口和出口规则已经到位，可以在发生泄露时控制爆炸半径。此外，Kubernetes 网络策略的一个极其重要的方面是它们存在于与其保护的应用程序 Pod 不同的控制平面上。这意味着即使攻击者成功破坏容器并在该应用程序中获得提升的权限，他们也不能简单地重新定义或绕过限制他们的网络边界。为了增强内部环境的整体安全态势并真正将这些原则付诸实践，我们必须定义细粒度的网络策略来管理 Pod 级别的入口和出口流量：

- 入口策略：这些策略控制 Pod 的传入流量，强制执行服务仅接受来自明确授权源的连接的规则。如果集群中的相邻 Pod 受到威胁，强大的入口策略会阻止攻击者横向访问您的敏感工作负载。
- 出口策略：这些策略控制 Pod 的传出流量。他们的目标是严格限制 Pod 可以访问的外部或内部资源。如果 Pod 受到威胁，出口策略会阻止攻击者窃取数据、执行广泛的网络侦察或从外部命令和控制服务器下载恶意负载的能力。

#### 默认拒绝基础

虽然定义特定的入口和出口规则至关重要，但仅依赖它们会留下危险的漏洞，导致人为错误和欺骗性攻击。默认情况下，Kubernetes 在允许所有模型上运行，这意味着允许任何未明确限制的流量。如果开发人员只是忘记应用策略，那么该 Pod 就会处于开放状态。但风险不仅仅限于无心错误。在供应链攻击中，开发人员可能会在不知不觉中被诱骗部署受损的第三方组件，完全不知道隐藏的恶意负载或其后果。默认拒绝策略将此范例从阻止列表翻转为允许列表。零信任的核心原则要求每次交互都必须经过明确授权，因此从逻辑上讲，绝对不能隐式访问。通过严格阻止所有流量出入口，默认拒绝姿势会创建一个环境，在该环境中，意外遗漏（或巧妙伪装的流氓容器试图打电话回家）会导致安全阻止连接。它迫使您通过设计显式授予访问权限，将可能是无声的、灾难性的违规行为转变为明显的、易于修复的部署错误。

该方法从一个简单但强大的规则开始：默认拒绝所有流量。每个命名空间都会收到一个默认拒绝的 NetworkPolicy，该策略会阻止每个 Pod 的所有入口和出口，除非存在显式允许策略。```
apiVersion：networking.k8s.io/v1 种类：NetworkPolicy 元数据：名称：default-deny-in-namespace 规范：podSelector：{} 策略类型：- 入口 - 出口
```一旦 NetworkPolicy 以命名空间中的 pod 为目标，它就不再保留不受限制的访问。通过定义默认阻止访问的策略，它与默认状态的零信任拒绝保持一致。

### 当你无法修补时为什么

这很重要

考虑一个企业场景，让人想起臭名昭著的 Log4j 危机或最近的框架冲击，例如 React2Shell 漏洞 (CVE-2025-55182)：

- 您的应用程序使用的普遍存在的库中突然披露了一个严重的远程代码执行 (RCE) 漏洞。
- 如果攻击者只需向受影响的服务发送特制请求，则该漏洞允许完全接管服务器。
- 由于该库深深嵌入到您的依赖项中，因此经过验证的补丁在几天内无法成功测试并部署到生产中。

对采用零信任网络策略的组织的影响很小：

- 危害任何 Pod 的攻击者可以轻松地跨任何命名空间访问易受攻击的服务（无横向隔离）。

- 使用 ZTVP 网络策略：攻击者无法从另一个命名空间访问服务（命名空间隔离）。
- 攻击者可以连接到服务上的任何公开端口，包括关键或管理端口（无端口级过滤）。

- 使用 ZTVP 网络策略：攻击者无法连接到未明确允许的端口（端口级过滤）。
- 攻击者可以自由地建立出站连接以窃取数据或建立命令和控制 (C2) 通道（无出口限制）。

- 使用 ZTVP 网络策略：攻击者无法将数据泄露到外部端点（出口限制）。

#### 演示：消除攻击路径

我们制作了一个演示视频，在其中我们准确观察了正确实施的网络策略如何主动消除攻击路径。最初，我们看到一个没有默认拒绝状态的环境，利用供应链漏洞的攻击者可以轻松地执行广泛的侦察，自由地探测网络以查找其他未修补的组件以供利用。然后我们看到，一旦应用严格的网络策略，情况就会完全改变。即使攻击者成功地破坏了 Pod，他们研究网络、扫描漏洞或横向转动的能力也会被完全抵消。这些策略将它们限制在受感染的容器中，有效地遏制了威胁，并为您赢得了实施纠正措施所需的关键时间。虽然它们可能不是全面安全策略中唯一的故障安全措施，但建立严格的网络边界可以说是构建最后一道防线的最佳起点。

该演示展示了网络策略如何限制对受感染容器的攻击，有效遏制威胁并为您赢得实施纠正措施所需的关键时间。

### 更广阔的前景：纵深防御

网络政策只是综合战略的一层。分层零信任验证模式将这些策略与 SPIFFE/SPIRE 工作负载身份（使用零信任工作负载身份管理器）、Vault 管理的机密、使用身份提供商 (IdP)（例如我们默认的 Red Hat 版本的 Keycloak）的集中式身份验证以及用于 Kubernetes 运行时监控的 Red Hat Advanced Cluster Security 相结合。网络策略通过确保即使身份、秘密和应用程序安全失败，网络层也能提供遏制来完善这一图景。

但是，您如何知道您的网络策略是否真正有效，或者受感染的容器是否正在反复探测您的内部边界？当零日漏洞触发拒绝连接时会发生什么？

我们在本博客系列中帮助回答这些关键问题，探索[分层零信任验证模式](http://red.ht/ztvp) 如何实现零信任安全实践。当我们继续进行时，我们会看到以下内容：

- 使用适用于 Kubernetes 的红帽高级集群安全进行主动防御：实施深度运行时监控、自动网络策略扫描和实时警报，充当您的中央安全大脑。
- 身份和秘密：通过零信任工作负载身份管理器和 Vault 集成更安全地管理工作负载身份。
- 供应链：通过强制内容签名和验证管道任务，从头到尾锁定您的软件供应链，以保证只有可信代码到达您的集群。准备好看看它的实际效果了吗？您不必等待下一篇文章即可开始。查看[分层零信任验证模式](http://red.ht/ztvp) 来探索该架构，并亲自尝试网络策略演示。

### 参考文献

- [NIST SP 800-207：零信任架构](https://csrc.nist.gov/pubs/sp/800/207/final)
- [NIST SP 800-207A：云原生应用程序零信任](https://csrc.nist.gov/pubs/sp/800/207/a/final)
- [CISA：零信任微分段指南](https://www.cisa.gov/sites/default/files/2025-07/ZT-Microsegmentation-Guidance-Part-One_508c.pdf)
- [分层零信任验证模式](https://validatedpatterns.io/patterns/layered-zero-trust)
- [已验证的模式](https://validatedpatterns.io/learn/)
- [追逐圣杯：为什么红帽蜂鸟项目的目标是接近零 CVE](https://www.redhat.com/en/blog/chasing-holy-grail-why-red-hats-hummingbird-project-aims-near-zero-cves)
- [CVE 指标](https://www.cve.org/about/Metrics)

[尝试一下](https://www.redhat.com/en/technologies/cloud-computing/openshift/ocp-self-managed-trial?intcmp=7013a000003Sq0iAAC)

#### 关于作者

[![普热米斯瓦夫·罗古斯基](https://www.redhat.com/rhdc/managed-files/styles/media_thumbnail/private/photo%20-%20Przemyslaw%20Roguski.jpg?itok=ZKtFaWyh)](https://www.redhat.com/en/authors/przemysław-roguski)

[#### 普热梅斯瓦夫·罗古斯基

安全解决方案首席架构师](https://www.redhat.com/en/authors/przemysław-roguski)

Przemysław “Rogue” Roguski 是红帽的一名安全架构师，专门从事左移安全计划，专注于将安全最佳实践和证明嵌入到 SDLC 的最早阶段。他致力于红帽 OpenShift 和其他 OpenShift 相关产品的安全分析工作。他还设计了红帽的安全解决方案和流程。

作为 CISA SBOM/VEX 工作组成员、OASIS OpenEoX 技术委员会成员以及 CWE 计划的主要贡献者，他为安全生态系统做出了贡献。

[该作者的更多内容](https://www.redhat.com/en/authors/przemysław-roguski)

### 更多

这样的

博客文章

#### [BackendTLSPolicy 扩展网关 API 传输安全](https://www.redhat.com/en/blog/backendtlspolicy-expands-gateway-api-transport-security)

博客文章#### [使用红帽 OpenShift、Ansible 自动化平台和身份管理管理特权工作负载边界](https://www.redhat.com/en/blog/govern-privileged-workload-boundaries-red-hat-openshift-ansible-automation-platform-and-identity-management)

原创播客

#### [产品安全方面的合作 |编译器](https://www.redhat.com/en/compiler-podcast/collaboration-in-product-security)

原创播客

#### [使用 CVE 跟踪漏洞 |编译器](https://www.redhat.com/en/compiler-podcast/keeping-track-of-CVEs)

### 继续探索

- [免费试用：红帽学习订阅试用](https://www.redhat.com/en/services/training/learning-subscription?intcmp=7013a000003Sq0iAAC)
- [开始免费产品试用试用](https://www.redhat.com/en/products/trials?intcmp=7013a000003Sq0iAAC)
#### [自动化](https://www.redhat.com/en/blog/channel/management-and-automation)

有关技术、团队和环境的 IT 自动化的最新信息

![AI 图标](https://www.redhat.com/cms/managed-files/AI.svg)

#### [人工智能](https://www.redhat.com/en/blog/channel/artificial-intelligence)

平台更新使客户可以在任何地方运行人工智能工作负载

![打开混合云图标](https://www.redhat.com/cms/managed-files/open-hybrid-cloud.svg)

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

我们针对最严峻的应用挑战的解决方案![虚拟化图标](https://www.redhat.com/rhdc/managed-files/Icon-Red_Hat-Virtual_server-A-Black-RGB.svg)

#### [虚拟化](https://www.redhat.com/en/blog/channel/red-hat-virtualization)

适用于本地或跨云工作负载的企业虚拟化的未来

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
