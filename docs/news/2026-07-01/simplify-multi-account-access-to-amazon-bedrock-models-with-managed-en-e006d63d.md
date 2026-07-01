<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:42:49+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/simplify-multi-account-access-to-amazon-bedrock-models-with-managed-entitlements/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 使用托管权利简化多账户对 Amazon Bedrock 模型的访问 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:42 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | Simplify multi-account access to Amazon Bedrock models with managed entitlements \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/simplify-multi-account-access-to-amazon-bedrock-models-with-managed-entitlements/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在这篇文章中，我们将向您展示如何使用 Amazon Bedrock 的托管权利从中央账户订阅一次并在整个组织中分配模型访问权限。此方法无需工作负载账户中的 AWS Marketplace 权限。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 通过托管权利简化多账户对 

Amazon Bedrock 模型的访问

管理数十个或数百个 AWS 账户的 AI 模型访问会造成一个困境。您要么广泛授予 [AWS Marketplace](https://docs.aws.amazon.com/marketplace/) 权限（冒治理问题的风险），要么在每个账户中手动启用订阅。对于使用 Anthropic Claude 或 Cohere 等第三方模型的组织来说，这种运营开销会减缓人工智能的采用。

在这篇文章中，我们将解释托管权利何时适合您的组织，逐步完成四步工作流程，演示真实场景，并涵盖专属优惠和区域行为的重要注意事项。

了解不同模型的分布方式是了解何时需要托管权利的关键。下表显示了三个类别：

|型号类别 |示例 |访问方式 |
|:---|:---|:---|
|亚马逊型号|亚马逊新星 |获得 Amazon Bedrock 权限后立即可用 |
|亚马逊出售的型号| Meta、米斯特拉尔、DeepSeek |获得 Amazon Bedrock 权限后立即可用 |
| AWS Marketplace 模型 | Anthropic Claude、Cohere、稳定性 AI |需要 AWS Marketplace 订阅 |

对于亚马逊型号和亚马逊销售的型号，最近推出的[简化访问](https://aws.amazon.com/blogs/security/simplified-amazon-bedrock-model-access/) 意味着您可以立即开始调用它们，无需额外设置。通过 AWS Marketplace 分发的第三方模型的工作方式有所不同。每个账户在调用这些模型之前都需要订阅，这意味着每个账户都需要 AWS Marketplace 权限。对于管理多个账户的组织来说，这会产生运营开销。您可以广泛授予 AWS Marketplace 权限，也可以让某人在每个账户中手动启用模型。托管权利专为以下组织而设计：跨多个 AWS 账户运行工作负载、希望避免向工作负载账户授予 AWS Marketplace 权限、已协商专属优惠定价并希望跨账户获得一致的费率，或者需要集中了解整个组织的模型访问情况。它仅在使用第三方 AWS Marketplace 模型（例如 Anthropic Claude、AI21 Labs、Cohere 和 Stability AI）时适用。

如果您仅使用 Amazon 和合作伙伴模型（例如 Amazon Titan、Llama、Mistral 或 DeepSeek）、在单个 AWS 账户中运营，或者每个账户团队已独立管理自己的 AWS Marketplace 订阅，则您可能不需要托管权利。

### 先决条件

在实施托管权利之前，请验证您已具备以下条件：

- 启用所有功能的 AWS Organizations：托管权利需要配置为启用所有功能的 [AWS Organizations](https://docs.aws.amazon.com/organizations/)。
- 管理账户访问权限：您需要访问具有 AWS Marketplace 和 AWS License Manager 权限的管理账户。
- 会员帐户：您想要分配模型访问权限的帐户。
- 服务相关角色 (SLR)：直接链接到 AWS 服务的预定义 AWS Identity and Access Management (IAM) 角色。对于托管权利，您必须为 AWS License Manager 和 AWS Marketplace 创建 SLR。这些角色包括服务代表您调用其他 AWS 服务所需的所有权限。

### 它是如何工作的

将许可证视为您的组织使用模型的权利，并将授权视为与特定帐户共享该权利的机制。一个许可证可以有多个授权，因此您可以通过单个订阅将访问权限分配给多个帐户。

托管权利工作流程由四个主要步骤组成，如下图所示：- 验证许可证创建：AWS License Manager 自动为您的订阅创建许可证。该许可证代表您使用该模型的权利，并作为分发给其他帐户的基础。
- 创建授权：使用 AWS License Manager，您可以创建授权以与 [AWS Organizations](https://docs.aws.amazon.com/organizations/) 中的特定成员账户共享许可证。您可以准确控制哪些帐户可以访问每个模型。
- 激活和使用：会员帐户收到赠款通知。激活授权后，他们可以立即开始调用模型。无需 AWS Marketplace 权限或额外订阅。

会员帐户仍然可以在不订阅私人优惠或激活赠款的情况下调用模型，但将按公开定价计费。

### 真实场景

#### 场景 1：在整个组织中启用模型

结果：集中订阅、分布式访问、工作负载账户中没有 AWS Marketplace 权限。

#### 场景 2：分阶段模型推出

情况：您希望在组织范围内使用新模型之前与选定的团队进行试点。您需要了解谁在使用什么以及逐步扩展访问权限的能力。

结果：通过清晰的审计跟踪来控制部署，了解哪些帐户有权访问以及何时激活它。

#### 场景 3：私募发行

情况：您已通过 AWS Marketplace 与模型提供商协商自定义定价。您需要每个帐户都使用此定价，而不是创建自己的订阅。

解决方案：要求提供商将专属优惠扩展到管理帐户。接受您管理帐户的专属优惠。创建的许可证反映了您协商的条款。通过授权分配访问权限，以验证成员帐户之间的使用是否符合您的协议。

结果：整个组织的定价保持一致，成本分配得到简化。

#### 场景 4：组织范围内的快速部署

情况：您的组织已经对 AI 工作负载模型进行了标准化。您希望 AWS Organizations 中的每个账户都能立即访问。就是这样。会员帐户自动收到补助金。对于启用了所有功能的组织，组织会自动接受授权，但它们会显示为“已禁用”状态，直到帐户管理员明确激活它们为止。这在模型使用开始之前提供了最终控制点。

结果：组织中的每个帐户只需一次授权即可获得模型访问权限。添加到组织的新帐户会自动继承访问权限，无需创建额外的授权。

### 注意事项

在实施托管权利之前，请记住以下几点，以确保您的部署顺利进行。

#### 成本分配

模型使用费用将记入持有订阅的管理帐户。使用 AWS 成本分配标签跟踪成员账户或团队的使用情况。

#### 私人优惠

使用通过 AWS Marketplace 协商的专属优惠时，托管权利工作流程保持不变。接受您管理帐户的专属优惠，许可证将自动创建。然后，您可以通过赠款分配对成员帐户的访问权限。

私人优惠通常包括定制定价、付款条件或附加支持协议。这些条款适用于您的组织对模型的使用，无论哪个成员帐户调用它。在接受和分发访问权限之前，请仔细查看要约条款。

#### 现有订阅

当会员账户拥有活跃的 Amazon Bedrock 模型并且其付款人账户向他们分配同一模型的订阅时，第一个订阅的权利将被禁用，并且他们现在拥有新分配补助金的权利。

#### 区域行为

虽然您可以在受支持的 AWS 区域中调用模型，但 AWS License Manager 在 us-east-1 中创建许可证。即使您的工作负载在其他区域运行，授权创建和激活也可以通过 AWS License Manager 的 us-east-1 终端节点进行。

### 清理资源

如果您不再需要模型订阅：

- 从 AWS License Manager 中的成员账户删除授权。
- 从您的管理账户取消 AWS Marketplace 订阅。
- 验证会员帐户不再按私人费率计费。

注意：取消订阅不会自动删除赠款。您必须单独删除赠款才能撤销私人定价。

＃＃＃ 结论在本文中，我们向您展示了如何使用 Amazon Bedrock 的托管权利来集中第三方模型订阅并在整个组织中分配访问权限，而无需向工作负载账户授予 AWS Marketplace 权限。

Amazon Bedrock 的托管权利代表了组织大规模管理第三方模型访问方式的重大改进。您的现有订阅将继续运行而不会中断，并且您可以立即开始使用新订阅的集中分发工作流程，同时维护组织的治理控制。

通过集中订阅管理并避免对每个账户 AWS Marketplace 权限的需求，您可以专注于构建 AI 应用程序，而不是管理访问基础设施。

#### 后续步骤

准备好实施托管权利了吗？开始于：

- 确定您的组织使用哪些第三方模型。
- 审查您当前的跨帐户订阅方式。
- 作为试点实施一种模型的托管权利。
- 根据您的结果扩展到其他模型和帐户。

您还可以探索将托管权利与 AWS Service Catalog 相结合，为您的团队创建自助服务模型访问工作流程。

如果您有疑问或想要分享您如何管理跨 AWS 账户的模型访问，请发表评论。

### 资源

- [Amazon Bedrock 中的托管权利](https://docs.aws.amazon.com/bedrock/latest/userguide/managed-entitlements.html)。
- [Amazon Bedrock 模型访问](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)。
- [简化的 Amazon Bedrock 模型访问](https://aws.amazon.com/blogs/security/simplified-amazon-bedrock-model-access/)（AWS 安全博客）。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
