<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-30T08:00:00+08:00
source: Red Hat Blog
domain: 技术动态
url: https://www.redhat.com/en/blog/how-should-your-infrastructure-connect-red-hat-lightspeed
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 您的基础设施应如何连接到红帽 Lightspeed？

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-30 08:00 CST |
| 领域 | 技术动态 |
| 来源 | Red Hat Blog |
| 原文标题 | How should your infrastructure connect to Red Hat Lightspeed? |
| 原文 | [打开原文](https://www.redhat.com/en/blog/how-should-your-infrastructure-connect-red-hat-lightspeed) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

保持运营稳定性，同时保护基础设施免受不断增加的漏洞的影响，这是一种日常平衡行为。红帽 Lightspeed 提供大规模管理基础设施所需的核心服务。但是，要充分利用这些服务，需要做出战略决策：您的基础设施应如何连接到红帽 Lightspeed？选择部署架构的过程超出了工程的范围；它还必须考虑业务战略，因为它会影响您的数据隐私、基础设施成本和运营敏捷性。红帽 Lightspe

## 正文

## 您的基础设施应如何连接到红帽 Lightspeed？

20263 年 6 月 30 日阅读[Linux](https://www.redhat.com/en/blog?f[0]=taxonomy_topic_tid:27061#rhdc-search-listing)

![马修·叶](https://www.redhat.com/rhdc/managed-files/styles/media_thumbnail/private/IMG_4087%20-%20Matthew%20Yee_0.jpg?itok=jJmjxOPq)

[马修·叶](https://www.redhat.com/en/authors/matthew-yee)

技术营销经理

保持运营稳定性，同时保护基础设施免受不断增加的漏洞的影响，这是一种日常平衡行为。红帽 Lightspeed 提供大规模管理基础设施所需的核心服务。

然而，要充分利用这些服务，需要做出战略决策：您的基础设施应如何连接到红帽 Lightspeed？

选择部署架构的过程超出了工程的范围；它还必须考虑业务战略，因为它会影响您的数据隐私、基础设施成本和运营敏捷性。红帽 Lightspeed 提供 3 种不同的架构模型，如图 1 所示。

[![光速架构模型](https://www.redhat.com/rhdc/managed-files/image1_353.png)](https://www.redhat.com/rhdc/managed-files/image1_353.png)

图 1. Lightspeed 架构模型

您选择的模型将取决于您组织的监管要求和风险偏好。以下是如何考虑每种模型与您的业务目标相一致的方式。

### 托管（直接）：最大敏捷性和最低 TCO

在托管模型中（包含在您的 Red Hat Enterprise Linux (RHEL) 订阅中），您环境中的每个 RHEL 节点都通过互联网直接连接到 Red Hat Lightspeed。

- 商业价值：这是最终的低摩擦方法。它以最快的速度实现价值，同时将设置复杂性降至最低。您的团队可以立即、实时地访问全套服务，包括顾问、漏洞和合规性服务，而无需任何额外的基础设施开销。此功能包含在您的 RHEL 订阅中。
- 权衡：每个节点都需要出站互联网访问，并且遥测数据驻留在红帽托管的云中。
- 结论：非常适合优先考虑速度、最大限度降低基础设施成本并在可接受公共云数据驻留的标准商业环境中运营的组织。### 通过卫星代理：安全的中间地带

对于需要集中控制网络流量的组织来说，通过卫星架构代理提供了一种优雅的折衷方案。内部节点与公共互联网保持安全隔离，通过集中式红帽卫星出口网关路由所有红帽 Lightspeed 流量。

- 商业价值：您可以保持托管模型的实时云同步优势和完整功能可用性，同时显着增强安全状况。您的内部网络对外界保持黑暗，满足大多数内部安全和合规团队的要求。
- 权衡：设置复杂性适中，需要管理红帽卫星基础设施。
- 结论：标准企业和金融环境的黄金标准。它平衡了强大的内部网络安全性与实时云分析的功能。

此功能需要订阅 Red Hat Satellite。

### 本地部署（气隙）：绝对数据主权

国防或关键基础设施等行业或受到严格监管的公共部门的组织不允许任何数据离开其物理网络。对于这些环境，红帽 Lightspeed 在本地架构中提供了一部分服务，该架构使用断开连接的红帽卫星同步和容器化红帽 Lightspeed 服务。

- 商业价值：毫不妥协的数据驻留。遥测数据完全在您的范围内进行分析。通过此模型，您仍然可以利用强大的分析（顾问）和漏洞跟踪，而不会违反严格的气隙要求。
- 权衡：虽然设置复杂性是可控的（中等），但此模型需要维护本地同步数据，而不是依赖实时云更新。
- 结论：零信任、高度机密或严格监管环境的强制选择，其中绝对数据主权是不可协商的优先事项。

此功能需要订阅 Red Hat Satellite。

### 做出正确的决定

选择符合您运营能力和风险承受能力的架构；没有普遍正确的选择。通过了解托管、代理和本地部署之间的差异，决策者可以为他们的团队提供主动保护和管理 RHEL 队列所需的工具，而不会影响组织的合规性和安全标准。

### 补充阅读

- “[Red Hat Satellite 与 Red Hat Lightspeed 同步：](https://www.redhat.com/en/blog/red-hat-satellite-synchronization-insights)”有关 Satellite 如何与 Red Hat Lightspeed 交互的深入博文（以前称为 Insights）。
- “[红帽卫星中的红帽 Lightspeed 顾问](https://www.redhat.com/en/blog/red-hat-insights-advisor-red-hat-satellite)：”有关使用卫星进行本地气隙部署的红帽 Lightspeed 配置的深入博文。
- [红帽 Lightspeed 信息门户](https://www.redhat.com/en/lightspeed)

[尝试一下](https://www.redhat.com/en/technologies/linux-platforms/enterprise-linux/ai/trial?intcmp=7013a000003Sq0iAAC)

#### 关于作者

[![马修·叶](https://www.redhat.com/rhdc/managed-files/styles/media_thumbnail/private/IMG_4087%20-%20Matthew%20Yee_0.jpg?itok=jJmjxOPq)](https://www.redhat.com/en/authors/matthew-yee)

[####马修·叶

技术营销经理](https://www.redhat.com/en/authors/matthew-yee)

作为红帽企业 Linux 业务部门的高级首席技术营销经理，Matthew Yee 致力于帮助每个人了解我们的产品的用途。他于 2021 年加入红帽，居住在加拿大温哥华。

[该作者的更多内容](https://www.redhat.com/en/authors/matthew-yee)

### 更多

这样的

博客文章

#### [Red Hat Enterprise Linux 10.2 和 9.8 映像生成器的新增功能](https://www.redhat.com/en/blog/whats-new-image-builder-red-hat-enterprise-linux-102-and-98)

博客文章

#### [红帽已更新 RISC-V 开发者预览版](https://www.redhat.com/en/blog/red-hat-has-updated-risc-v-developer-preview)

原创播客

#### [边缘基础设施 |编译器](https://www.redhat.com/en/compiler-podcast/infrastructure-at-the-edge)

原创播客

#### [操作系统管理 |编译器](https://www.redhat.com/en/compiler-podcast/operating-system-management)

### 继续探索

- [管理云规模基础设施电子书](https://www.redhat.com/en/engage/managing-infrastructure-cloud-20221226?intcmp=7013a000003Sq0iAAC)
- 为现代企业的成功构建高效的 IT 基础电子书
- [开始试用：红帽企业 Linux 试用](https://www.redhat.com/en/technologies/linux-platforms/enterprise-linux/server/trial?intcmp=7013a000003Sq0iAAC)

### 按频道浏览

[探索所有频道](https://www.redhat.com/en/blog/channels)

![自动化图标](https://www.redhat.com/cms/managed-files/automation.svg)

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

我们针对最严峻的应用挑战的解决方案

![虚拟化图标](https://www.redhat.com/rhdc/managed-files/Icon-Red_Hat-Virtual_server-A-Black-RGB.svg)

#### [虚拟化](https://www.redhat.com/en/blog/channel/red-hat-virtualization)

适用于本地或跨云工作负载的企业虚拟化的未来

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
