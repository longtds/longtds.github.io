<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T01:32:29+08:00
source: AWS Containers Blog
domain: 云原生
url: https://aws.amazon.com/blogs/containers/announcing-amazon-eks-rollback-for-safe-and-reliable-management-of-cluster-upgrades/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 宣布推出 Amazon EKS Rollback，以安全可靠地管理集群升级 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 01:32 CST |
| 领域 | 云原生 |
| 来源 | AWS Containers Blog |
| 原文标题 | Announcing Amazon EKS Rollback for safe and reliable management of cluster upgrades \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/containers/announcing-amazon-eks-rollback-for-safe-and-reliable-management-of-cluster-upgrades/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

今天，我们宣布推出 Amazon EKS 版本回滚，这是一项新功能，允许集群管理员安全地回滚 Amazon Elastic Kubernetes Service (Amazon EKS) 集群上的 Kubernetes 版本升级。借助此功能，您现在可以放心地在 EKS 车队中推出新版本升级，并提供额外的安全网。

## 正文

### [容器](https://aws.amazon.com/blogs/containers/)

## 宣布推出 

Amazon EKS Rollback，以安全可靠地管理集群升级

今天，我们宣布推出 [Amazon EKS 版本回滚](https://docs.aws.amazon.com/eks/latest/userguide/rollback-cluster.html)，这是一项新功能，允许集群管理员安全地回滚 Amazon Elastic Kubernetes Service (Amazon EKS) 集群上的 Kubernetes 版本升级。借助此功能，您现在可以放心地在 EKS 车队中推出新版本升级，并提供额外的安全网。

每年三个小版本的发布周期要求您定期升级集群以维护安全性和功能。然而，执行 Kubernetes 版本升级可能具有挑战性。新版本通常会引入可能影响现有应用程序的更改，例如功能添加、API 弃用和内部组件修改。按照设计，开源 Kubernetes 不具备在升级完成后回滚 Kubernetes 控制平面的功能。由于没有本机回滚路径，许多组织采用了昂贵的缓解策略。其中包括使基础设施成本加倍的蓝/绿部署，或消耗大量工程时间的集群状态手动快照，所有这些都是为了创建一个本来不存在的安全网。

通过 Amazon EKS 版本回滚，如果您在升级后发现问题，您现在可以安全地将 Kubernetes 控制平面恢复到已知的良好状态。对于使用 EKS 自动模式的集群，回滚功能也扩展到数据平面，为整个集群提供全面的保护。此功能提供了两个关键优势。首先，它为您提供了可靠的生产升级安全网，以及满足灾难恢复计划监管要求的方法。其次，它支持更快的升级，从而增强您的安全状况，因为回滚消除了延迟的原因。因此，团队可以主动升级，减少运行具有已知 CVE 的版本的时间，并保持对需要受支持、主动修补软件的框架的合规性。通过提供恢复升级的路径，EKS 版本回滚可帮助您了解最新的 Kubernetes 版本，同时保持操作可靠性。

### EKS 版本回滚的工作原理通过版本回滚，平台工程师和集群管理员可以获得就地升级的安全网。

如果升级后出现问题，他们可以在 7 天内将集群恢复到之前的 Kubernetes 版本。 EKS 使用 Amazon EKS Rollback Readiness Insights 自动扫描您的集群与之前版本的兼容性，并显示可能影响回滚安全的任何问题。

![Amazon EKS 回滚就绪情况洞察显示在集群回滚之前评估的兼容性检查](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/29/CONTAINERS-195-1.png)

当您触发回滚时，EKS 会执行全面的安全检查，包括：

- API 兼容性：验证您的资源使用的 API 是否与以前的版本兼容。
- API 字段更改：检查版本之间是否存在不兼容的 API 字段使用情况。
- 集群运行状况：验证不存在会妨碍成功回滚的运行状况问题。
- Kubelet 版本偏差：验证工作节点是否符合 Kubernetes 版本偏差策略。
- Kube-proxy 兼容性：验证 kube-proxy 版本兼容性。
- 附加组件版本：检查已安装的 EKS 附加组件是否与目标版本兼容。

### EKS 自动模式回滚

前面几节中描述的回滚体验适用于标准 EKS 集群。使用 [Amazon EKS 自动模式](https://docs.aws.amazon.com/eks/latest/userguide/automode.html) 的集群的体验甚至更进一步，它通过使用内置的最佳实践自动管理计算、网络和存储等基础设施来简化集群操作。当您在[启用自动模式的集群](https://docs.aws.amazon.com/eks/latest/userguide/rollback-automode.html) 上启动控制平面回滚时，EKS 首先自动回滚您的自动模式工作节点，然后继续控制平面回滚。这将验证整个回滚过程中是否符合 Kubernetes 版本偏差策略。回滚将遵循您配置的中断预算，包括 NodePool 中断预算和 PodDisruptionBudget (PDB)，以尽量减少对运行工作负载的影响。即使检测到潜在的兼容性问题，“--force”标志也会绕过 EKS [回滚就绪见解](https://docs.aws.amazon.com/eks/latest/userguide/cluster-insights.html) 警告并继续回滚。然而，“--force”不会凌驾于中断预算或 Pod 级中断控制之上。在整个回滚过程中继续遵守这些规定，以保持工作负载可用。

对于 EKS 自动模式集群，版本回滚验证：

- NodePool 中断预算 – 验证 Karpenter 中断预算允许基于漂移的节点更换，并且不会设置为无限期阻止节点中断。
- Pod 中断注释 – 检查带有 karpenter.sh/do-not-disrupt 注释的 pod，这些注释可能会在回滚期间延迟节点终止。
- PodDisruptionBudgets (PDB) – 验证 PDB 是否允许足够的 pod 驱逐，并且没有错误配置（例如 maxUnavailable：0）以阻止节点中断。
- 节点中断注释 – 使用 karpenter.sh/do-not-disrupt 注释标识节点，以防止回滚期间节点替换。

这些验证可在启动回滚之前识别潜在的阻碍因素，从而帮助您确认数据平面回滚可以顺利进行，从而使您能够了解可能延迟或阻止自动节点更换过程的配置。

如果回滚花费的时间比预期长，或者您决定通过其他方法解决问题，则可以使用 [CancelUpdate API](https://docs.aws.amazon.com/eks/latest/userguide/rollback-automode.html#automode-cancel-rollback) 取消正在进行的回滚。当您想要向前应用修复而不是等待回滚完成时，或者当另一个关键更新被正在进行的回滚操作阻止时，这非常有用。此功能仅适用于自动模式回滚，因为节点回滚阶段可能是一个长时间运行的操作（在保守的中断预算下最长可达 7 天）。没有自动模式的标准集群可以快速完成回滚，并且没有可取消的阶段。

要取消回滚，请调用cancel-update API：```
aws eks 取消更新 \ --name my-cluster \ --update-id <更新 ID> \ --region <aws-region>
```取消后，集群将恢复到发起回滚时的ACTIVE状态，您可以继续下一步操作。

### 回滚期间的缩放

即使版本回滚正在进行中，Amazon EKS 也能让您的集群响应工作负载需求。尽管 EKS 不支持并发集群更新，但该服务在主动回滚操作期间会根据需要继续扩展集群的控制平面。这意味着，如果您的集群在回滚窗口期间遇到 API 服务器负载增加的情况，EKS 会自动扩展控制平面基础设施以满足需求。处理版本恢复时，您的工作负载不会受到影响。

### EKS 版本回滚入门

要启动回滚，您可以使用现有的 UpdateClusterVersion API、AWS 命令行界面 (AWS CLI)、Amazon EKS 控制台或其他首选工具。

#### 使用 

AWS CLI

回滚过程使用与升级相同的 API，但指定了以前的版本：```
# Rollback from version 1.33 to 1.32 aws eks update-cluster-version \ --name my-cluster \ --kubernetes-version 1.32
```在启动回滚之前，请查看 EKS Cluster Insights 中的回滚就绪情况见解：```
# 列出回滚洞察 aws eks list-insights \ --cluster-name my-cluster \ --filter Category=ROLLBACK_READINESS # 获取详细洞察信息 aws eks describe-insight \ --cluster-name my-cluster \ --id <insight-id>
```如果 Cluster Insights 报告任何错误（错误状态），您必须在继续回滚之前解决这些问题。状态为“通过”、“警告”或“未知”的见解不会阻止回滚。

#### 使用 

Amazon EKS 控制台

在 Amazon EKS 控制台中：

- 导航到您的集群并选择“操作”菜单。
- 选择回滚集群版本。
- 查看回滚见解以识别任何阻塞问题。
- 选择目标版本并选择“启动回滚”。
- 确认回滚操作。

![Amazon EKS 控制台显示回滚集群版本操作以及回滚见解和目标版本选择](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/29/CONTAINERS-195-2.png)

### Salesforce 采用 EKS 回滚的历程

Amazon EKS 为 EKS 集群引入了 Kubernetes 版本回滚。此功能允许集群管理员在就地升级完成后随时将控制平面升级恢复到之前的次要版本。此功能直接解决了升级过程中未缓解的关键风险。

#### 回滚资格的先决条件

回滚功能最关键的前提是控制平面和数据平面（kubelet）之间的版本关系。当节点的 kubelet 被回收到升级版本（N+1）后，恢复控制平面需要相应回滚数据平面。

这引入了对当前升级管道的直接依赖。该管道在一次连续运行中推进控制平面、附加组件和数据平面，阶段之间没有烘焙时间。

因此，在控制平面和数据平面升级之间引入结构化分离是有意义地使用回滚功能的先决条件。

#### 推荐流程：通过控制平面烘焙期进行分阶段升级

为了保留回滚窗口并减少升级后回归的范围，我们建议按如下方式重组升级顺序：- 插件升级 – 将托管插件升级到与 N-1、N 和 N+1 K8s 版本交叉兼容的版本。这验证了附加组件不会成为回滚或升级的阻碍因素。
- 控制平面升级和烘焙 – 将控制平面升级到目标版本，并观察每个环境大约一周的烘焙周期。此窗口可以在数据平面升级到新版本之前及早检测控制平面回归。
- 数据平面升级 – 烘焙期结束后，继续进行节点回收，将 kubelet 升级到目标版本。

>

注意：建议使用匹配的控制平面和数据平面版本进行初始验证，以便在周期的早期出现回归。

推荐的顺序是：控制平面升级，然后一周的烘焙期，然后数据平面升级（节点回收）。

如果在数据平面升级期间或之后发现回归：

- 仅数据平面回归：将工作节点回滚到 N-1 kubelet；控制平面保持在N。
- 控制平面和数据平面均回归：先回滚数据平面（将 kubelet 返回到 N-1），然后启动控制平面回滚。

好处：

- 这种方法可以在整个机队中快速部署控制平面（CP 升级速度很快），从而减少 EKS 延长支持费用的风险。
- 这使得回滚窗口在烘焙期间保持打开状态，从而使事件响应更快并降低风险。

权衡：

- 增加了完成机队完整升级周期（控制平面+数据平面）的时间。

#### 示例场景

场景 1：干净回滚，未检测到任何问题

集群从1.30升级到1.31。回滚洞察显示一切都已通过。管理员发起回滚：```
aws eks update-cluster-version --name my-cluster --kubernetes-version 1.30 # Returns InProgress VersionRollback update
```场景 2：因见解错误而阻止回滚

集群从1.30升级到1.31。数据平面节点已回收到 kubelet 1.31。回滚见解显示 kubelet/kube-proxy 版本偏差存在错误。

![集群见解显示 kubelet 和 kube-proxy 版本偏差的错误会阻止回滚](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/29/CONTAINERS-195-3.png)

解决方案：将受影响的节点回收到 1.30 kubelet，并将 kube-proxy 回滚到兼容版本，刷新见解，然后重试回滚。

场景 3：尝试回滚多个版本

集群从1.29升级到1.30再到1.31，然后回滚到1.30。管理员尝试回滚到1.29：```
aws eks update-cluster-version --name my-cluster --kubernetes-version 1.29 # 错误：集群无法回滚到指定的 Kubernetes 版本。 # 只能回滚1个版本。
```![集群只能回滚一个版本的错误信息](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/29/CONTAINERS-195-4.png)

#### 回滚见解的范围

Rollback Insights 检查 EKS 托管插件（coredns、VPC CNI、kube-proxy）。不会自动检查 cluster-autoscaler 等自我管理的附加组件。我们 Salesforce 必须维护我们自己的验证，以确保自我管理的附加组件与回滚目标版本的兼容性。

我们的 Kubernetes 升级流程已通过跨不同版本的多个升级周期构建为严格的多阶段计划，具有广泛的验证、烘焙期、自动签核和交错生产部署。所有这些都是为了弥补一个基本限制：EKS 不支持控制平面回滚。

EKS版本回滚的推出从根本上改变了Kubernetes升级的风险计算。

- 真正的生产升级安全网 - 如果任何交错组出现升级后问题，回滚不再是不可能的。
- 更快地在整个机队范围内推出控制平面 - 通过使用烘烤窗口分离 CP 和 DP 升级，团队可以在整个机队中快速推进控制平面版本，从而减少扩展支持成本风险。
- 降低监管风险 - 对于受监管的工作负载，记录并经过测试的回滚路径可满足灾难恢复规划的合规性要求。

为了充分利用该功能，我们需要进行有针对性的管道更改：分离控制平面和数据平面的部署，在 CP 和 DP 升级阶段之间引入烘焙窗口，以及通过回滚洞察集成和适当的护栏构建特定于回滚的管道。

我们现有的升级严格性和 EKS 版本回滚支持相结合，使团队能够更有信心地在我们的大型集群机群中进行升级，并减少影响范围。

### 注意事项

以下是有关此功能的主要考虑因素：

回滚范围——版本回滚支持回滚一个 Kubernetes 小版本（N 到 N-1）。目前不支持多版本回滚。仅当您的集群是通过就地升级升级到当前版本时才可以回滚；在版本 N 创建的集群无法回滚到 N-1。支持的版本 – 当前支持的 EKS 版本可进行版本回滚。这将验证启动时对所有当前支持的 EKS 版本的回滚支持。

回滚窗口和超时 – 只要 EKS 仍然支持以前的版本，您可以在升级后 7 天内完成升级后随时启动回滚。但是，如果您进行的更改使用了新版本中的新 API 或功能，则必须在回滚之前恢复这些更改。

默认情况下，EKS 允许回滚操作最多 7 天完成，然后将其标记为失败。此外，帮助您评估回滚准备情况的回滚见解仅在升级后 7 天内可用，因此在该窗口内进行评估和采取行动非常重要。但是，如果您使用基础设施即代码 (IaC) 工具（例如 AWS CloudFormation 或 Terraform）管理集群，这些工具会强制执行自己的操作超时（分别为 36 小时和 24 小时），则 7 天的回滚窗口可能会导致与您的自动化管道发生冲突。

要解决此问题，您可以在回滚请求中指定自定义 timeoutMinutes，以定义 EKS 在操作失败之前应尝试回滚的最长时间。这样，您可以将 EKS 回滚行为与 IaC 工具的超时预期保持一致：```
aws eks update-cluster-version \ --name my-cluster \ --kubernetes-version 1.32 \ --rollback-config timeoutMinutes=1440
```扩展支持 – 如果您回滚到扩展支持下的版本，您的集群将开始产生扩展支持费用。再次升级到标准支持下的版本将停止延长支持费用。

工作节点回滚 – 对于自动模式集群，EKS 自动管理工作节点回滚。对于受管节点组，请使用 [UpdateNodegroupVersion API](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html#mng-rollback) 回滚工作节点。自我管理和混合节点必须由客户手动回滚。

Fargate：AWS Fargate 工作线程节点不支持版本回滚。虽然您可以回滚基于 Fargate 的集群的控制平面，但任何运行与预回滚控制平面相同 Kubernetes 版本的 Fargate Pod 都会触发 kubelet 版本偏差洞察并显示错误状态。发生这种情况是因为底层基础设施不支持独立于 API 服务器的 kubelet 版本降级。要解决此问题，请在启动回滚之前删除受影响的 Fargate Pod，或者使用“--force”绕过洞察检查，一旦控制平面回滚完成，新的 Pod 将使用回滚版本启动。

附加组件兼容性 – 您可以通过 UpdateAddon API 或 EKS 控制台指定所需的附加组件版本，手动回滚 EKS 附加组件。 Cluster Insights 将识别可能影响回滚安全的附加兼容性问题。

安全检查 – EKS Rollback Readiness Insights 在允许回滚之前自动根据多个安全谓词验证您的集群，包括 API 兼容性、功能门兼容性和版本偏差策略。在继续回滚之前必须解决任何错误。值得注意的是，EKS Upgrade Insights 涵盖了标准 Kubernetes 和 EKS 组件的已知兼容性检查。客户有责任在升级之前验证任何自定义附加组件、自定义构建的 AMI 或定制配置。此外，版本回滚被设计为解决升级后问题的安全网，而不是作为常规升级工作流程。有关 Upgrade Insights 评估内容的更多详细信息，请参阅 [EKS Cluster Insights 文档](https://docs.aws.amazon.com/eks/latest/userguide/cluster-insights.html)。

### 现已推出

Amazon EKS 版本回滚现已在所有提供 Amazon EKS 的 AWS 区域推出。有关区域可用性的信息，请访问 AWS 区域服务页面。

使用版本回滚不会产生额外费用。

要了解更多信息，请访问 Amazon EKS 用户指南中的 [Amazon EKS 版本回滚文档](https://docs.aws.amazon.com/eks/latest/userguide/rollback-cluster.htmldocs.aws.amazon.comPrepare)。

在 Amazon EKS 控制台中尝试一下，并将反馈发送到 AWS re:Post for EKS 或通过您常用的 AWS Support 联系人发送反馈。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
