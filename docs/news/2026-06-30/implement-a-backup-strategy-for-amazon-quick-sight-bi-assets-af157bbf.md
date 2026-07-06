<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-30T02:15:14+08:00
source: AWS ML Blog
domain: 技术动态
url: https://aws.amazon.com/blogs/machine-learning/implement-a-backup-strategy-for-amazon-quick-sight-bi-assets/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 实施 Amazon Quick Sight BI 资产的备份策略 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-30 02:15 CST |
| 领域 | 技术动态 |
| 来源 | AWS ML Blog |
| 原文标题 | Implement a backup strategy for Amazon Quick Sight BI assets \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/implement-a-backup-strategy-for-amazon-quick-sight-bi-assets/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在这篇文章中，我们将介绍在 Quick Sight 中实施有效的 BI 资产备份策略的最佳实践。我们首先介绍用于选择要包含在备份中的资产的选项，然后解释可用于此目的的高级 API，最后提供示例代码以帮助您快速入门。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 实施 

Amazon Quick Sight BI 资产的备份策略

[Amazon Quick Sight](https://aws.amazon.com/quick/quicksight/) 是 [Amazon Quick](https://aws.amazon.com/quicksuite/) 中的一项核心功能，这是一个由 AI 驱动的代理数字工作空间，旨在最大限度地提高最终用户的工作效率，它通过自然语言查询、交互式仪表板和来自可信企业数据源的嵌入式分析来提供由 AI 驱动的 BI 功能。

Amazon Quick Sight 资产（例如仪表板、分析、数据集和数据源）可以使用本文中描述的“AssetsAsBundle” API 进行备份。备份策略有助于防止意外删除、意外修改和区域中断。对于依赖 Quick Sight 支持关键业务决策的团队，建议制定精心设计的备份计划。

本文是涵盖 Amazon Quick Sight BI 资产备份和恢复的两部分系列文章中的第一篇：

- 第 1 部分（本文）：介绍如何设计和实施备份策略，包括资产选择、可用于导出的 API 以及即用型示例自动化工具。
- 第 2 部分：介绍恢复过程。您可以使用第 1 部分中创建的备份来恢复意外删除、意外更改后的资产，或者作为更广泛的灾难恢复计划的一部分。

出于多种原因，有效的备份策略对于金融服务、医疗保健和能源等受到严格监管的行业的组织尤其重要：- 数据丢失防护可防止人为错误、意外删除和勒索软件等事件。
- 满足恢复目标可帮助组织实现恢复点目标 (RPO) 和恢复时间目标 (RTO)，从而最大程度地减少事件期间的数据丢失。
- 审计和报告支持在资产的整个生命周期（创建、更新和删除）中跟踪和报告资产。
- 提高工作负载弹性，使系统能够快速恢复到之前的状态，从而减少停机时间并提高可靠性。这与 [AWS 架构完善的框架](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html) 的可靠性支柱相一致。
- 灾难恢复 (DR) 准备为实施 [DR 流程](https://aws.amazon.com/what-is/disaster-recovery/) 奠定了基础，该流程可预测与技术相关的灾难并有助于组织的 [业务连续性计划 (BCP)](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/business-continuity-plan-bcp.html)。

有关 Quick 灾难恢复功能以及如何根据组织要求对其进行评估的更多信息，请参阅 [Amazon Quick 灾难恢复和弹性指南](https://builder.aws.com/content/3ARv3heLpgnufWleBwpxLYmHWeu/amazon-quick-disaster-recovery-and-resiliency-guide)。

在这篇文章中，我们将介绍在 Quick Sight 中实施有效的 BI 资产备份策略的最佳实践。我们首先介绍用于选择要包含在备份中的资产的选项，然后解释可用于此目的的高级 API，最后提供示例代码以帮助您快速入门。

### 商业智能的备份实践

BI 系统因其在支持决策流程和关键利益相关者方面的作用而带来了独特的业务连续性挑战。您必须通过实施有效的备份计划来保护它们免受服务中断的影响。在制定此计划之前，了解作为灾难恢复计划一部分要考虑的架构和维度非常重要。![该图显示了 Quick Sight 区域架构，其中包含托管用户和组的身份区域以及跨多个可用区托管数据源、数据集、分析和仪表板的独立分析区域](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/05/ML-20472-1.png)

上图显示 Quick Sight 依赖 AWS 跨多个 AWS 区域的全球基础设施来为 Quick Sight 资产（包括数据源、数据集、分析和仪表板）[提供高可用性](https://docs.aws.amazon.com/quicksuite/latest/userguide/disaster-recovery-resiliency.html)。

超快速并行内存计算引擎 (SPICE) 通过跨 Quick Sight 区域内多个可用区 (AZ) 的冗余副本以高可用性 (HA) 存储和[加密](https://docs.aws.amazon.com/quicksuite/latest/userguide/data-encryption.html) 导入的数据。

通过此区域设计，您可以维护多个区域中的资源，并在发生影响主要 BI 资源的区域中断（不太可能发生）的情况下使用辅助区域。

对于用户和身份管理，Quick Sight 使用您在[初始帐户订阅过程](https://docs.aws.amazon.com/quicksuite/latest/userguide/signing-up.html) 期间定义的单个区域。该图显示该区域托管用户和组身份信息，并且必须可供用户访问 Quick Sight。

例如，如果用户想要访问 eu-west-1 区域中的仪表板，但 Quick Sight 主区域是 us-east-1，则两个区域都必须可用才能完成用户访问流程。 Quick Sight 使用带有 AZ 的区域架构来实现冗余。但是，如果您的企业需要针对不太可能发生的区域中断事件提供保护，则必须相应地设计灾难恢复 (DR) 策略。

提示：如果您不确定您的 Quick Sight 主区域，您可以通过运行以下命令来检索此信息：```
aws Quicksight 描述账户设置 --aws-账户-id XXXXXXXXXXXX --region us-east-1
```注意：此“aws Quicksight describe-account-settings”命令将 us-east-1 指定为终端节点区域。如果您收到“200”状态，则您的身份区域为 us-east-1。否则，您会收到如下错误，指示您指向当前的身份区域（例如 eu-west-1）：```
An error occurred (AccessDeniedException) when calling the DescribeAccountSettings operation: Operation is being called from endpoint us-east-1, but your identity region is us-east-1. Please use the eu-west-1 endpoint.
```### 定义要包含在备份计划中的 Quick Sight 资产

更清楚地了解 Quick Sight 架构后，下一步是选择要包含在备份计划中的资产，为此您可以遵循两种策略：

#### 备份特定资产：

当您定义的[备份或灾难恢复策略](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-best-practices/strategy.html) 专注于保护业务运营的关键资产（您可以在灾难或意外删除后方便地恢复这些资产）时，此选项适用。这包括关键利益相关者用于制定业务决策或运营团队（财务、物流、采购等）用于支持持续业务运营的特定仪表板（及其相关资产）。

当您需要简单的备份计划并且对业务连续性至关重要的 BI 资产是 Quick Sight 实例中所有可用资产的子集时，建议使用此选项。

#### 备份所有资产：

当您想要定义涵盖版本控制和潜在灾难恢复的备份策略时，建议使用此策略。通过备份所有资产，如果人为错误导致意外修改或删除，您可以将任何资产就地回滚到之前的状态。此外，由于您拥有账户中所有资产的备份，因此您可以选择要恢复的特定资产作为灾难恢复计划的一部分。

这种方法可以为您提供最大的覆盖范围，但也需要更复杂的编排和自动化。这篇文章重点介绍这一策略，并提供示例代码，您可以调整这些代码以最大限度地缩短生产时间。

选择策略后，选择要导出的 BI 资产类型。 Quick Sight 提供以下资产类型：- [仪表板](https://docs.aws.amazon.com/quicksuite/latest/userguide/creating-a-dashboard.html)：针对读者用户的只读资产，根据分析发布。您还可以将仪表板保存到分析中以进行编辑。
- [分析和仪表板](https://docs.aws.amazon.com/quicksuite/latest/userguide/working-with-visuals.html)：分析是仪表板的可编辑版本。只有您选择的作者才能访问它。
- [数据源](https://docs.aws.amazon.com/quicksuite/latest/userguide/working-with-data-sources.html)：数据源实现与数据的连接，数据可以来自分析源（例如数据库或数据仓库）、AWS 服务（例如 Amazon Simple Storage Service (Amazon S3)）或第三方软件即服务 (SaaS) 数据提供商（例如 Jira 和 ServiceNow）。
- [数据集](https://docs.aws.amazon.com/quicksuite/latest/userguide/working-with-datasets.html)：一种资产类型，它使用数据源访问外部数据，您可以使用外部数据来准备和构建支持分析和仪表板的数据。
- [VPC 连接](https://docs.aws.amazon.com/quicksuite/latest/userguide/working-with-aws-vpc.html)：可用于与 VPC 资源集成的功能，例如位于该 VPC 中或可从该 VPC 访问的数据库和数据仓库（对等 VPC 或通过 VPN 或 AWS Direct Connect 连接的网络）。
- [主题](https://docs.aws.amazon.com/quicksuite/latest/userguide/themes-in-quicksight.html)：样式和外观设置的集合，您可以将其应用于多个分析和仪表板，以匹配满足您的产品或企业品牌需求的美学标准。

所有这些资产彼此之间都具有依赖关系，分析和仪表板位于该依赖关系链的顶部，如下图所示。

![Quick Sight 资产依赖关系图，顶部显示分析和仪表板，中间显示数据集，底部显示数据源、VPC 连接和主题](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/05/ML-20472-2.png)当您选择要备份的资产类型时，请注意这些依赖性，以便您可以从备份中完全恢复资产。例如，当您备份仪表板时，您还需要备份其依赖项，其中可能包括数据集、数据源、VPC 连接和主题。接下来的部分将解释 Quick Sight 导出 API 如何处理这些依赖关系。

### 备份过程概述

我们在本文中介绍的机制使用 Quick Sight 中提供的 [AssetsAsBundle API](https://docs.aws.amazon.com/quicksight/latest/developerguide/asset-bundle-ops.html)。 AssetsAsBundle API（也称为 AAB API）是一组高级 API，旨在支持以编程方式导出和导入 Quick Sight 资源。它们涵盖一系列用例，例如发布管理、备份和恢复、跨账户迁移以及[持续集成和持续交付 (CI/CD) 工作流程](https://aws.amazon.com/solutions/guidance/multi-account-environments-on-amazon-quicksight/)。

这组API包括以下操作：- [StartAssetBundleExportJob](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_StartAssetBundleExportJob.html)：创建一个包（捆绑包），其中包含作为操作一部分导出的资产。该包是一个包含文本文件的 zip 文件。格式可以是 JSON 或 [AWS CloudFormation](https://aws.amazon.com/cloudformation/)，具体取决于 [ExportFormat](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_StartAssetBundleExportJob.html#API_StartAssetBundleExportJob_RequestSyntax) 参数中指定的值。根据格式，您可以直接使用 AAB API 导入这些资产，或使用 CloudFormation 基础设施即代码 (IaC) 进行配置。异步操作完成后，系统将包上传到临时 S3 位置以供下载。
- [StartAssetBundleImportJob](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_StartAssetBundleImportJob.html)：获取之前导出的包并恢复其中打包的资源。您可以使用导入操作定义[覆盖广泛的](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_AssetBundleImportJobDataSourceOverrideParameters.html) 参数集，例如资产名称和数据源连接参数（主机、端口、工作组等）。
- [DescribeAssetBundleImportJob](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_DescribeAssetBundleImportJob.html) 和 [DescribeAssetBundleExportJob](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_DescribeAssetBundleExportJob.html)：两个 AssetBundle 操作都是异步的。您可以使用这些 API 来描述操作、轮询其状态并在操作完成后采取行动。执行导出作业时，您可以使用“DescribeAssetBundleExportJob”来检索捆绑包的“DownloadUrl”，该文件的有效期为 5 分钟。您可以通过进一步调用“DescribeAssetBundleExportJob”来更新 URL。

#### AssetsAsBundle API 支持的资产和当前限制

AssetsAsBundle API 支持 Quick Sight 资产列表，包括分析、仪表板、数据源、数据集、共享文件夹、受限文件夹、刷新计划、主题和 VPC 连接。然而，某些资产类型有局限性。不受支持的数据源：Adobe Analytics、File、GitHub、Jira、Salesforce、ServiceNow、Amazon S3（带有本地上传的 [清单文件](https://docs.aws.amazon.com/quicksight/latest/user/supported-manifest-file-format.html)）和 Twitter。

不受支持的数据集：包含通过[连接的 SageMaker ML 模型](https://docs.aws.amazon.com/quicksight/latest/user/sagemaker-integration.html) 进行推理而生成的机器学习 (ML) 列的数据集。

您必须从备份计划中排除这些资产，以避免在发出“StartAssetBundleExportJob”操作时出现“InvalidParameterValueException”错误。

要解决此问题，您可以按照以下过程替换不受支持的数据源和数据集。

对于具有本地清单文件的 Amazon S3 数据源：

- 创建新的 Amazon S3 数据源。
- 将清单文件上传到 Amazon S3。
- 从您的数据源引用清单文件。
- 使用 [UpdateDataSet](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_UpdateDataSet.html) API 替换依赖数据集中的数据源。

对于其他不支持的数据源和数据集：

请按照以下过程将不兼容的数据集转换为兼容的数据集：

- 创建连接到您想要在备份中支持的数据源的分析。
- 创建一个显示所有数据集列的[表格视觉](https://docs.aws.amazon.com/quicksuite/latest/userguide/tabular.html)。
- 将数据导出为 CSV 文件。
- 使用上传到 Amazon S3 的清单创建 Amazon S3 数据集。
- 使用[替换数据集功能](https://docs.aws.amazon.com/quicksuite/latest/userguide/replacing-data-sets.html) 使用新数据集更新您的分析和仪表板。

#### 需要考虑作为备份一部分的其他资产

尽管 Quick Sight 资源是要备份的关键资产，但您需要在备份计划中包含一些额外的资源和配置，以应对潜在的还原或灾难恢复情况。

您可以导出 Quick Sight 资产及其权限，包括有权访问它们的用户和组。您可以通过将 [IncludePermissions](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_StartAssetBundleExportJob.html#API_StartAssetBundleExportJob_RequestSyntax) 标志设置为“true”来控制这一点。由于每个 Quick Sight 资产均由用户拥有，因此您需要备份用户和组以获得完整且可恢复的备份。

AssetsAsBundle API 不涵盖用户和组，但您可以使用 [DescribeUser](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_DescribeUser.html)、[DescribeGroup](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_DescribeGroup.html) 和 [DescribeGroupMembership](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_DescribeGroupMembership.html) 将此信息包含在备份中。

除了用户和组之外，还可以考虑备份帐户设置，例如帐户自定义（[DescribeAccountCustomization](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_DescribeAccountCustomization.html) API）、自定义品牌（[DescribeBrand](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_DescribeBrand.html) API）和文件夹（[ListFolders](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_ListFolders.html)、[DescribeFolder](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_DescribeFolder.html) 和 [DescribeFolderPermissions](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_DescribeFolderPermissions.html) API）。

### 技术实现

在本节中，我们将介绍如何创建自动化来协调执行有效备份实施所需的 Quick Sight API 的调用。我们在本节末尾提供了示例代码，用于实现用户和组备份以及 Quick Sight 资产备份。

#### 备份编排流程

该自动化工具支持三种操作模式：仅用户备份、仅资产备份以及两者。这在您执行备份计划时提供了最大的灵活性。下图显示了该工具根据所选操作模式所遵循的流程。

![备份自动化工具的流程图，显示三种操作模式（仅用户备份、仅资产备份和两者）及其编排步骤](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/05/ML-20472-3.png)

#### 用户和组备份用户和组备份服务使用 Quick Sight [用户](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_User.html) 和 [组](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_Group.html) API 读取您账户的当前状态并将检索到的用户和组数据存储在 [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) 中。该服务对 DynamoDB 表名称使用基于日期的后缀，以保留历史备份数据并防止覆盖。这允许时间点恢复和备份历史记录跟踪。此设计还简化了恢复操作，因为您在查询特定备份中的数据时无需按日期后缀进行筛选。

![用户和组备份流程图，显示 Quick Sight 用户和组 API 如何为三个 DynamoDB 表提供数据：用户、组和用户组成员资格](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/05/ML-20472-4.png)

2025 年 10 月 19 日运行的备份示例：

- 用户：quicksight-users-backup-2025-10-19
- 组：quicksight-groups-backup-2025-10-19
- 用户组成员资格：quicksight-users-groups-backup-2025-10-19

用户表架构：```
{ "user_name": "string (分区键)", "arn": "string", "email": "string", "role": "string", "identity_type": "string", "active": "boolean", "principal_id": "string", "backup_timestamp": "string (ISO 8601)", "custom_permissions_name": "string" }
```组表架构：```
{ "group_name": "string (partition key)", "arn": "string", "description": "string", "principal_id": "string", "members": ["list of user names"], "backup_timestamp": "string (ISO 8601)" }
```用户组成员资格表架构：```
{ "membership_id": "string (分区键，格式：用户名#组名)", "user_name": "string", "group_name": "string", "user_arn": "string", "group_arn": "string", "backup_timestamp": "string (ISO 8601)" }
```注：用户和组备份服务实现双Region支持。用户和组操作使用“identity_region”配置参数，而备份资产操作使用标准“aws_region”。此设计解决了在与资产存储不同的区域中配置 Quick Sight 身份管理的企业场景。

#### 资产备份

资产包备份服务协调区域内资产的导出，并将生成的包上传到 Amazon S3 位置以供以后使用。自动化备份以下资产：数据源、数据集、分析、仪表板和主题。默认情况下，备份包含所有依赖项。如果需要，您可以禁用此设置。

在较高级别上，该服务执行以下任务：

- 使用 [ListDataSources](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_ListDataSources.html) API 列出所有数据源，过滤掉基于 Amazon S3 清单的数据源和具有无效 VPC 连接名称的数据源。名称只能包含由连字符分隔的字母数字字符。
- 使用 [ListDataSets](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_ListDataSets.html) API 列出所有数据集，通过检查“ImportMode”字段过滤掉“FILE”数据集。
- 使用 [ListAnalyses](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_ListAnalyses.html) API 列出所有分析。
- 使用 [ListDashboards](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_ListDashboards.html) API 列出所有仪表板。
- 按类型对资产进行分组以进行单独的导出作业。您可以配置每个捆绑包中包含的资产数量，最多 100 个（[API 限制](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_StartAssetBundleExportJob.html#QS-StartAssetBundleExportJob-request-ResourceArns)）。
- 使用 [DescribeAssetBundleExportJob](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_DescribeAssetBundleExportJob.html) API 检查导出作业状态并[实现指数退避](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) 以避免限制。
- 使用以下前缀结构将完整的资产包上传到 Amazon S3。```
my-QuickSight-backups/ └── QuickSight-backups/ # Custom S3 prefix ├── 2024/01/15/ │ ├── datasources/ │ │ ├── datasources-143022.zip # Single bundle (≤ max_assets_per_bundle) │ │ └── datasources_bundle_1-143045.zip # Multiple bundles when assets exceed limit │ ├── datasets/ │ │ ├── datasets_bundle_1-143045.zip # Multiple bundles when assets exceed limit │ │ └── datasets_bundle_2-143045.zip # Sequential numbering for multiple bundles │ ├── analyses/ │ │ └── analyses-143108.zip # Single bundle │ └── dashboards/ │ ├── dashboards_bundle_1-143131.zip # First of multiple dashboard bundles │ └── dashboards_bundle_2-143131.zip # Second dashboard bundle └── 2024/01/16/ ├── datasources/ │ └── datasources-090015.zip ├── datasets/ │ └── datasets-090030.zip └── ...
```注意：仅当要备份的资产数量超过“max_assets_per_bundle”中的配置值时，才会出现捆绑包编号字符串。

#### 用于备份创建的端到端工具

QuickSight 备份工具提供了一种简单的方法，可将所有 Quick Sight 资产及其依赖项导出到持久、廉价的存储（例如 Amazon S3）中。该工具为生成的捆绑包创建新的前缀，因此以前的备份不会被覆盖。该工具还使用相同的原理导出用户和组：DynamoDB 存储此数据，表名称包含生成备份的日期。通过这种方法，您可以使用备份作为恢复策略的来源，并跟踪 Quick Sight 资产和关联用户的更改历史记录。

该代码使用 [Boto3 Python SDK](https://aws.amazon.com/sdk-for-python/) 并通过 [setuptools](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/) 提供打包支持以进行设置和使用。

#### 工具使用和配置

在使用该工具之前，请确保您满足以下先决条件：

- Python 3.8 或更高版本。
- 企业版或更高版本的 Quick Sight 帐户。
- 使用适当的凭证配置的 AWS 命令​​行界面 (AWS CLI)。
- 所需的 AWS 权限。请参阅代码中的[权限部分](https://github.com/aws-samples/sample-quicksight-backup-tool/blob/main/README.md#permissions)。

从源克隆```
git clone https://github.com/aws-samples/sample-quicksight-backup-tool.git cd Quicksight-backup-tool
```创建Python venv（推荐）```
python3 -m venv ./.venv source .venv/bin/activate
```安装包```
pip install -e .
```创建配置文件

首先，请参阅存储库中的 [config-basic.yaml](https://github.com/aws-samples/sample-quicksight-backup-tool/blob/main/examples/config-basic.yaml) 文件或从头开始创建一个文件。该配置文件定义了该工具的关键参数，包括以下内容：

- AWS 账户。
- 地区。
- 备份位置（DynamoDB 表和 Amazon S3 存储桶前缀）。

使用工具

安装完成后，您可以运行该工具，如下所示：```
quicksight-backup --config config.yaml --mode full
```您只需要提供`--config`参数。您可以省略其余部分。 `--mode` 参数控制备份类型（`full`、`users-only` 或 `assets-only`），其中 `full` 是默认模式。以下列表描述了该工具支持的参数。

可选参数

- `--mode`、`-m`：备份模式（`完整`、`仅用户`、`仅资产`）；默认为“完整”。
- `--output-dir`、`-o`：报告和清单的输出目录。
- `--verbose`、`-v`：启用详细（`DEBUG`）日志记录。
- `--log-file`：日志文件的路径。
- `--dry-run`：验证配置而不运行备份。
- `--no-progress`：禁用进度指示器。
- `--generate-manifest`：生成备份清单文件。
- `--generate-report`：生成人类可读的备份报告。
- `--version`：显示版本信息。

有关详细信息，请参阅工具 [README 文件](https://github.com/aws-samples/sample-quicksight-backup-tool/blob/main/README.md)。

#### 工具代码

您可以在 [aws-samples 存储库](https://github.com/aws-samples/sample-quicksight-backup-tool) 中找到此工具的代码。该工具可帮助您快速入门。使用它作为基础参考来完善和适应您的特定备份要求。

在生产环境中实施备份解决方案之前，请确认您：

- 检查并调整代码，以符合您的特定基础设施要求、安全策略和合规性标准。
- 在非生产环境中进行全面测试以验证功能和性能。
- 实施适当的安全控制，包括组织所需的加密、访问管理和审核日志记录。
- 验证恢复过程以确认您的备份策略满足您定义的恢复时间目标 (RTO) 和恢复点目标 (RPO)。
- 考虑成本优化策略和监控，以使解决方案保持在您的运营预算范围内。
- 避免并发工具执行：该工具依赖于具有较低限制阈值的 AssetsAsBundle API。该示例工具不适用于在同一 AWS 账户中并行运行多个实例。如果多个团队需要使用该工具，请考虑实施并发控制机制（例如 DynamoDB 中的锁表或数据库级锁），以防止可能触发 API 限制的并发运行。

### 预定执行上一节中描述的示例工具专为按需执行而设计，非常适合入门或运行临时备份。对于生产级备份策略，您可能希望定期自动运行备份，以便您的 Quick Sight 资产得到一致的保护，而无需手动干预。

本节概述了预定的全自动备份解决方案的高级架构。该架构的详细实现和代码超出了本文的范围。

#### 架构概述

计划执行架构基于三个 AWS 托管服务构建，这些服务协同工作以提供可靠、无服务器且经济高效的自动化管道：

- [Amazon EventBridge](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html) 是调度程序。它以定义的节奏（例如每天午夜）触发备份工作流程。 EventBridge 规则允许您定义灵活的基于 cron 或基于速率的计划，而无需管理任何底层基础设施。
- [AWS Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html) 是编排层。它以正确的顺序协调各个备份步骤的运行。 Step Functions 提供内置错误处理、重试逻辑和执行历史记录，这使其非常适合跨越多个 API 调用和异步操作的长时间运行的工作流。
- [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) 将每个单独的备份步骤实现为独立的无状态函数。将备份逻辑拆分到多个 Lambda 函数可以解决备份过程中固有的时间限制。每个导出作业都是异步的，可能需要几分钟才能完成，具体取决于要导出的资产的数量和大小。

#### 工作流程步骤

由于端到端备份过程可能需要大量时间，因此自动化过程被分解为离散的步骤，每个步骤都由专用的 Lambda 函数实现。 AWS Step Functions 按顺序编排这些函数，在它们之间传递状态并处理瞬时故障的重试。工作流程包括以下步骤：- 用户和组备份：使用 Quick Sight 身份 API 检索所有 Quick Sight 用户、组和组成员身份，并使用基于日期的表后缀将数据保存到 DynamoDB，如技术实施部分中所述。此操作可以与资产备份操作并行运行，因为它没有任何依赖性。
- 资产备份发现：列出目标区域中的所有 Quick Sight 资产（数据源、数据集、分析和仪表板），应用必要的筛选器以排除不受支持的资产类型，并将资产分组到每个最多 100 个项目的列表中。该步骤的输出作为输入传递给后续步骤。
- 生成捆绑包：启动指定为输入参数的列表中包含的所有资产的导出作业，轮询作业完成情况，并将生成的 ZIP 捆绑包上传到指定的 Amazon S3 前缀。
- 检查状态：定期轮询活动捆绑包执行情况，并在导出完成时通知 AWS Step Functions 状态机。

下图说明了计划执行架构的高级流程。

![该图显示了使用 EventBridge 触发 Step Functions 状态机的计划执行架构，该状态机为用户和组备份、资产备份发现、生成捆绑包和检查状态编排 Lambda 函数，捆绑包上传到 Amazon S3，元数据存储在 DynamoDB 中](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/05/ML-20472-5.png)

#### 关键设计考虑因素

- 异步轮询：检查状态 Lambda 函数使用“DescribeAssetBundleExportJob” API 轮询由generate-bundle Lambda 函数启动的作业，直到作业达到最终状态（“SUCCESSFUL”或“FAILED”）。检查状态 Lambda 函数在循环中运行，调用之间有等待条件（例如 30 秒）。
- 并行度：配置足够的并行度以控制工作流程中的步骤执行的 API 调用量，尤其是在调用“DescribeAssetBundleExportJob”和“StartAssetBundleExportJob” API 的生成捆绑包步骤上，这些 API 的并发速率限制较低。您可以使用[内联映射状态 MaxConcurrency 字段](https://docs.aws.amazon.com/step-functions/latest/dg/state-map-inline.html) 来限制生成包步骤的并发运行数。
- 错误处理：Step Functions 允许您在每个阶段定义 catch 块和重试策略。某一步骤出现故障（例如，不受支持的资产类型）不会中止整个备份运行。
- 成本：启用计划后，成本随备份频率和保留期而变化。有关估算存储成本的指南，请参阅成本估算部分。

### 成本估算

以下部分估计了在 Amazon S3（针对资产包）和 DynamoDB（针对用户和组元数据）上运行备份工具的成本。

#### Amazon S3：资产捆绑存储

资产包是在每次导出作业后上传到 Amazon S3 的压缩 ZIP 文件。根据解决方案设计，每包最多 100 个资产在压缩后平均约为 500 KB。

要点：资产包的 Amazon S3 存储成本极低。即使对于拥有数千个资产的超大型 Quick Sight 部署，压缩包大小仍保持在低兆字节范围内，从而使每月存储成本远低于 0.01 美元。

#### Amazon DynamoDB：用户和组元数据存储

用户和组信息存储在具有基于日期的后缀的 DynamoDB 表中，以保留备份历史记录。 DynamoDB 存储的价格约为每月每 GB 0.25 美元（标准表类，按需模式）。DynamoDB 中存储的每个项目代表单个用户或组定义（包括所有关联的属性，例如 ARN、电子邮件、角色、组成员身份和备份时间戳）。根据本文中描述的架构，平均项目大小约为 256 KB。

您可以使用以下公式来估计 DynamoDB 表的大小：

表大小估计 = 项目数 × 平均项目大小 (256 KB)

要点：对于中小型组织，DynamoDB 存储成本仍然很低（每个备份快照每月低于 0.10 美元）。对于拥有数万用户的大型组织来说，成本仍然较低，每个快照的成本在个位数美元左右。

### 总结

对于单个非计划备份运行，AWS 总成本实际上接近于零，最多由几美分的 Amazon S3 和 DynamoDB 存储主导。如果您实施计划备份（在计划执行部分中介绍），成本将随着备份频率和保留期呈线性增长。即使每日备份保留 90 天，大多数部署的总存储成本仍保持在较低的个位数美元范围内。随着备份历史记录的增长，考虑使用 Amazon S3 生命周期策略和 DynamoDB Standard-IA 来优化成本。

### 结论

在这篇文章中，我们介绍了如何为 Amazon Quick Sight 资产设计和实施全面的备份策略，以便您可以保持业务连续性、满足监管要求并防止数据丢失。

我们介绍了如何使用 AssetsAsBundle API 以编程方式导出和保留关键 BI 资产，包括仪表板、分析、数据集和数据源及其依赖项和权限。为了帮助您入门，本文包含一个示例自动化工具，您可以测试并适应您组织的需求。该代码编排这些 API，将资产包存储在 Amazon S3 中，并在 DynamoDB 中保留用户和组信息以进行时间点恢复。准备好保护您的 Quick Sight BI 资产了吗？立即开始从 [AWS 示例存储库](https://github.com/aws-samples/sample-quicksight-backup-tool) 克隆示例备份工具并在非生产环境中对其进行测试。从简单的配置开始备份最关键的仪表板，然后在验证流程时扩展到生产就绪的备份策略。要了解有关 Amazon Quick Sight 的更多信息，请参阅 [Amazon Quick Sight 用户指南](https://docs.aws.amazon.com/quicksuite/latest/userguide/welcome.html)。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
