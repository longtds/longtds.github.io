<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-03T01:03:59+08:00
source: AWS Containers Blog
domain: 云原生
url: https://aws.amazon.com/blogs/containers/diagnose-kubernetes-control-plane-performance-issues-with-aws-devops-agent/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 使用 AWS DevOps Agent 诊断 Kubernetes 控制平面性能问题 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-03 01:03 CST |
| 领域 | 云原生 |
| 来源 | AWS Containers Blog |
| 原文标题 | Diagnose Kubernetes Control Plane Performance Issues with AWS DevOps Agent \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/containers/diagnose-kubernetes-control-plane-performance-issues-with-aws-devops-agent/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

本文演示了 AWS DevOps Agent 如何诊断 Amazon Elastic Kubernetes Service (Amazon EKS) API 服务器性能下降，特别是 429 限制和 API 优先级和公平性 (APF) 席位耗尽。

## 正文

### [容器](https://aws.amazon.com/blogs/containers/)

## 使用 

AWS DevOps Agent 诊断 Kubernetes 控制平面性能问题

本文演示了 AWS DevOps Agent 如何诊断 Amazon Elastic Kubernetes Service (Amazon EKS) API 服务器性能下降，特别是 429 限制和 [API 优先级和公平性 (APF)](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/) 席位耗尽。真实的模拟会引入行为不当的控制器，该控制器会向 API 服务器发送过多的请求。然后，[AWS DevOps Agent](https://aws.amazon.com/devops-agent/) 会自动识别有问题的工作负载，将 Amazon CloudWatch 审核日志与限制模式关联起来，并建议有针对性的修复措施以恢复集群稳定性。

管理 Amazon EKS 环境中的生产事件给开发运营和站点可靠性工程 (SRE) 团队带来了独特的挑战。当事件发生时，值班工程师必须同时调查分布式系统的根本原因，同时向利益相关者提供及时的更新。此过程通常涉及关联来自多个可观测性来源的数据、检查最近的部署更改以及协调跨职能响应团队，这些过程经常在正常工作时间之外进行。

### 什么是 

AWS DevOps 代理？

AWS DevOps Agent 是一款由 AI 驱动的运营助手，可自主调查事件、关联基础设施中的信号，并提供可操作的根本原因分析和建议的补救措施。有关完整概述，请参阅[发布公告](https://aws.amazon.com/blogs/mt/announcing-general-availability-of-aws-devops-agent/)。对于 Amazon EKS 环境，代理扩展了以下功能：

EKS 环境的关键功能：- 自主事件调查：触发警报时自动开始调查事件，从而缩短平均解决时间 (MTTR)。
- EKS 特定见解：与 Amazon EKS 集群直接集成，以自省集群状态、Pod 日志和集群事件。
- Amazon CloudWatch 日志分析：查询 Amazon CloudWatch Logs Insights 以分析 EKS 审核日志，识别受限制的请求和负​​责的工作负载。
- 多工具集成：连接可观测性工具、持续集成和持续交付 (CI/CD) 管道以及通信平台，以实现全面的数据关联。
- 主动建议：分析历史事件和流量模式，为基础设施优化和应用程序弹性提供可行的建议。

### 基础设施设置

#### 先决条件

安装最新版本的 AWS 命令行界面 (AWS CLI)、eksctl 和 kubectl。请参考[安装步骤](https://docs.aws.amazon.com/eks/latest/userguide/setting-up.html)。

#### 克隆存储库

克隆 git 存储库 [https://github.com/aws-samples/sample-troubleshooting-eks-with-devops-agent](https://github.com/aws-samples/sample-troubleshooting-eks-with-devops-agent) 以创建 EKS 集群并重新创建控制平面性能场景。

#### 配置 EKS 自动模式集群

通过应用 eks-auto-mode-cluster.yaml 清单创建 EKS 自动模式集群。在执行之前，请确保您位于下载的存储库目录中，如以下命令所示。```
eksctl 创建集群 -f ./blog-troubleshooting-eks-with-devops-agent/manifests/eks-auto-mode-cluster.yaml
```此清单允许 EKS 控制平面与集群一起记录和部署 CloudWatch Observability 插件。为此性能测试创建专用集群，以隔离您的工作负载并避免对现有 EKS 环境产生意外影响。

#### Configure 

AWS DevOps Agent

- 按照[AWS DevOps Agent 帮助您加速事件响应并提高系统可靠性（预览）| 中提到的步骤配置 AWS DevOps Agent 空间。 Amazon Web Services](https://aws.amazon.com/blogs/aws/aws-devops-agent-helps-you-accelerate-incident-response-and-improve-system-reliability-preview/)
- 要使代理能够分类和分析 EKS 集群中的问题，请使用代理空间中配置的相同 AWS DevOps 代理角色创建 EKS 访问条目。创建访问条目时，选择“Standard”作为类型，选择“AmazonAIOpsAssistantPolicy”作为访问策略。 [创建访问条目 – Amazon EKS](https://docs.aws.amazon.com/eks/latest/userguide/creating-access-entries.html)

您还可以使用以下命令创建 EKS 访问条目并将其与 AWS DevOps 代理角色关联。

注意：使用您的 AWS DevOps Agent 主要 IAM 角色 ARN 替换主体 arn，当您选择在功能下的代理空间中编辑“主要源 – 必需”时，您可以找到该角色。```
aws eks create-access-entry --cluster-name devops --region us-east-1 --type STANDARD --principal-arn <devops-agent-role-arn> aws eks associate-access-policy --cluster-name devops --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonAIOpsAssistantPolicy --access-scope type=cluster --region us-east-1 --principal-arn <devops-agent-role-arn>
```### 场景：诊断 API 服务器过载和 429 限制

#### 挑战

API 服务器性能下降是 Kubernetes 最难诊断的问题之一。与产生明确错误信号的 Pod 故障或节点问题不同，API 服务器过载表现为集群操作中微妙的延迟增加。 “kubectl”命令速度变慢，部署时间更长，控制器协调循环落后，但可能没有任何明显的 Pod 崩溃或节点故障可以指出。

根本原因通常涉及行为不当的控制器或工作负载，这些控制器或工作负载会用过多的请求淹没 API 服务器。 Kubernetes 通过 APF 管理此负载，该系统限制可以同时处理的请求数量，同时每个活动请求占用所谓的并发席位。当 APF 席位耗尽时，API 服务器返回 429（请求过多）响应。这些 429 特别阴险，因为：

- 它们经常通过 client-go 透明地重试，因此有问题的工作负载甚至可能不会记录它们。
- 它们出现在 EKS 审核日志中，但不出现在标准应用程序日志中。
- 它们会导致合法系统控制器（例如 Karpenter 和其他 EKS 控制器）受到限制。
- 延迟影响是集群范围内的，因此很难隔离源。

在确定根本原因之前，工程师通常会花费数小时手动查询 CloudWatch Logs Insights、检查 API 服务器指标并关联多个工作负载的请求模式。这正是 AWS DevOps Agent 擅长的多信号调查类型。

#### 模拟如何进行

我们将部署一个“控制器”，一个 Python 异步应用程序，它模拟行为不当的 Kubernetes 控制器，通过可配置的 API 调用组合淹没 API 服务器。

呼叫类型的组合很重要。 LIST 和 GET 调用速度快，但容量大。 WATCH 调用在消耗 APF 席位方面特别有效，因为它们保持连接打开。 MUTATE 调用来执行单独的变异 APF 流模式。它们一起使读取和写入并发路径饱和。

在 50 个副本，每个副本每秒约 80-100 个实际请求时，约 1600-2000 个请求/秒的总负载产生：- 可见的 API 服务器延迟（基本 kubectl 命令约为 1.5 秒以上，基线约为 100 毫秒）。
- CloudWatch 审核日志中可见 429 个限制响应。
- 系统控制器（Karpenter、EKS 控制器）上的 429。

#### 场景准备

- 使用以下 kubectl 命令部署控制器```
# 设置 EKS 集群的区域导出 AWS_REGION=us-east-1 kubectl apply -f ./blog-troubleshooting-eks-with-devops-agent/manifests/controller-deployment.yaml
```这将创建“agent-demo”命名空间、基于角色的访问控制（RBAC）资源、控制器部署（已禁用）。

- 从 EKS 可观测性仪表板捕获基线。在 EKS 控制台中，导航到可观测性 → 监控集群 → 控制平面监控，并截取屏幕截图或记下 API 服务器延迟和请求率指标的当前值。这是你的基线。
- 验证基准 API 服务器响应能力：```
kubectl apply -f ./blog-troubleshooting-eks-with-devops-agent/manifests/measure-job.yaml # Wait for containers to start kubectl logs job/api-measure -n agent-demo
```- 注入故障：```
kubectl apply -f ./blog-troubleshooting-eks-with-devops-agent/manifests/inject-fault.yaml
```此清单将控制器扩展到 50 个副本并允许混合调用负载。

您可能会看到什么，以及为什么它没问题。控制器 Pod 本身可能会在启动期间短暂进入 CrashLoopBackOff 或 OOM 终止，因为它们各自打开连接池并开始攻击 API 服务器。您还可能会在 EKS 控制台中看到短暂的节点不健康指示器，并且单个 Pod 会重新启动。这是工作负载在其自身负载下自身不稳定，而不是集群范围内的故障。集群作为一个整体保持运行。当控制器稳定我们模拟的负载水平后，这两个指示灯都会自动清除，并且不会影响场景的诊断价值。

- 等待约 60 秒以构建负载，然后重新检查 EKS 可观测性仪表板。
刷新可观测性→监控集群→控制平面监控。您应该看到以下内容：

- API 服务器请求延迟远高于基线，通常达到数秒范围。
- API 服务器每秒请求数攀升至约 1,600–2,000。
- APF 拒绝了基线上没有的请求（429）。

即使 kubectl 速度很慢，这种测量仍然可靠，因为我们直接从控制平面的度量管道中提取这些数字，而不是从集群内的工作负载中提取。

可选：确认用户可见的影响。

从工作站运行一些 kubectl 命令，从客户端角度体验延迟。```
time kubectl get pods -n agent-demo time kubectl get nodes
```等待 60 秒以构建负载，然后观察影响：

预期：kubectl 命令现在需要大约 1.5 秒以上，这是一个明显的退化。

- 验证集群运行状况节点和 Pod 大部分不受影响：```
kubectl 获取节点 kubectl 获取 pod -A |头-20
```在这种情况下，问题主要表现为 API 服务器延迟峰值和 HTTP 429 限制。您还可以在 EKS 控制台中观察到 pod 重新启动和短暂的节点不健康指示器。这些是由于控制平面不堪重负而导致的次要症状，与计算或工作负载故障无关。这种区别很重要，因为传统的 Kubernetes 故障排除本能促使工程师首先调查节点运行状况和 Pod 崩溃。当根本问题是 API 服务器降级时，这种关注可能会延迟根本原因识别。

您可以在 Amazon EKS 控制台中导航到可观测性 → 监控集群 → 控制平面监控来观察此延迟和 429 限制指标，如下图所示。控制台显示存在问题并诊断 API 服务器不堪重负的原因。识别导致性能问题的特定客户端、请求模式或资源类型仍然是一项耗时的手动工作。

![EKS 控制台可观测性仪表板显示基线 API 服务器延迟和请求率指标](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/25/CONTAINERS-162-1.png)

API 服务器请求受到 429 的限制。

![EKS 控制台显示负载测试期间 API 服务器延迟峰值达到数秒范围](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/25/CONTAINERS-162-2.png)

加载期间 API 服务器请求延迟。

### 使用 

AWS DevOps Agent 进行故障排除

导航到 AWS DevOps Agent Operator 门户，在导航窗格中选择事件，然后在事件响应仪表板 → 开始调查部分提交以下诊断提示。

注意：使用聊天界面进行后续查询或在初步分析后将调查引向不同的方向。

>

从几分钟前开始，我在“us-east-1”中的 EKS 集群 devops 上遇到 API 服务器响应缓慢的情况。 kubectl 命令花费的时间比通常的亚秒级响应要长。请调查。

在调查起点中，提供额外的背景信息，例如“此问题是在几分钟前开始的”。

选择开始调查。![AWS DevOps Agent 调查启动界面显示诊断提示提交](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/25/CONTAINERS-162-3.png)

在 DevOps Agent 中开始调查。

注意：本节中提供的调查结果反映了 AWS DevOps Agent 在我们调查期间生成的输出。与任何人工智能驱动的工具一样，由于集群状态和可用遥测数据的差异，调查结果可能会有所不同。您的经验可能会产生略有不同的诊断路径，但得出相似的结论。

一旦我们启动调查，代理就会开始建立调查时间表并收集 EKS 集群上下文。它识别出 EKS 集群“devops”并开始调查。

该代理从各种来源同时启动多信号调查任务，包括 EKS API 指标、控制平面日志、AWS CloudTrail 事件以及任何更改的集群状态。

- EKS API 指标：查询 EKS API 服务器性能详细信息的 CloudWatch 指标。
- Kubernetes 集群状态分析：检查集群的当前状态，包括节点、事件和 Pod。
- 控制平面日志分析：搜索 429 节流、错误模式和显示缓慢请求的审核日志条目。
- 基础设施更改：扫描 CloudTrail 以查找可能影响 EKS 集群的最新更改，例如 EKS API 调用和 EC2 实例更改。

DevOps 代理对 EKS 控制平面问题进行故障排除。

代理查询 CloudWatch Logs Insights 并发现了控制器，该控制器在事件发生的短时间内生成了大量针对控制器服务帐户的 API 调用。这导致 API 服务器延迟在事件窗口期间明显激增。

![CloudWatch Logs Insights 查询结果显示用户代理限制了 429 个请求](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/25/CONTAINERS-162-5.png)

DevOps 代理识别根本案例。

DevOps 代理识别根本原因。

该代理还确定了 API 优先级和公平性 (APF) 高座位需求的关键发现，并比较了基线和事件期间之间的指标。

DevOps 代理正在调查 EKS 问题。

DevOps 代理正在调查该问题。代理比较了基线与事件 API 模式，并发现了关键的行为变化：在基线期间，API 服务器主要具有 LIST 操作。但在事件窗口期间，它还添加了 CREATE/DELETE configmap 突变、WATCH 操作和 GET 操作，这些操作在基线中不存在。

调查显示调查结果摘要。

代理确定 EKS 集群配置、安全组规则、AWS Identity and Access Management (IAM) 角色或策略以及网络配置没有更改。它还最终确定了调查摘要，该事件是由控制器部署引起的，导致 API 优先级和公平性“工作负载低”优先级并发饱和和 EKS 控制平面实例轮换。

调查显示调查结果摘要。

最后，为了确定根本原因，代理将多个来源的信号合成为明确的根本原因，并显示“根本原因”按钮。选择该按钮将导航到“根本原因”选项卡，该选项卡将调查结果合并为一个可操作的摘要。

![AWS DevOps Agent 根本原因确定界面及综合结果](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/25/CONTAINERS-162-11.png)

DevOps Agent 总结了主要发现。

![AWS DevOps Agent 总结主要调查结果](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/25/CONTAINERS-162-12.png)

DevOps 代理显示调查结果摘要。

代理人总结道：

Root Cause: ‘controller’ deployment generated approximately 66,000 API requests per minute to the EKS API server for cluster ‘devops’. This sustained load consumes 99%+ of API server traffic, impacting the API server’s performance.

在这种情况下，代理在大约 7 分钟内为我们完成了从最初提示到根本原因识别和 CloudTrail 归因的调查。该代理将来自 CloudWatch 指标、EKS 审核日志、CloudTrail 事件、Pod 日志和集群状态的数据关联起来，以找出根本原因。

### 恢复

Disable the controller and restore normal API server performance:```
kubectl apply -f ./manifests/recover.yaml sleep 60
```API 服务器响应能力在几秒钟内恢复到基线。使用用于基线测量的相同 EKS Observability 仪表板确认恢复情况，因此之前/之后的数字可以直接比较：

- 打开 Amazon EKS 控制台 → DevOps 集群 → 可观测性 → 监控集群 → 控制平面监控。
- 确认：

- API 服务器请求延迟已回落至基线范围。
- API 服务器每秒请求已从峰值 (~1,600–2,000) 降至基线水平。
- APF 拒绝的请求（429）已返回零或接近零。

我们故意在这里使用与故障注入期间使用的相同的测量源，因为当 API 服务器受到限制时，集群内测量作业方法可能无法部署或报告。控制平面仪表板在两种状态下均有效。

如果您愿意，您还可以在客户级别进行确认：```
kubectl 获取 pods -n agent-demo 的时间 kubectl 获取节点的时间
```现在，两者都应大致以您在故障注入之前观察到的基线延迟时间返回。

禁用控制器并恢复正常的 API 服务器性能：```
kubectl apply -f ./blog-troubleshooting-eks-with-devops-agent/manifests/recover.yaml sleep 10
```API 服务器响应能力在几秒钟内恢复到基线。```
kubectl 替换 --force -f ./blog-troubleshooting-eks-with-devops-agent/manifests/measure-job.yaml kubectl 日志 job/api-measure -n agent-demo
```### 清理

删除为此场景创建的所有资源：

删除 EKS 集群```
eksctl delete cluster -f ./blog-troubleshooting-eks-with-devops-agent/manifests/eks-auto-mode-cluster.yaml
```删除 AWS DevOps Agent 空间

以下命令将列出您的代理空间```
aws devops-agent 列表代理空间
```从前面的命令输出中获取为此创建的 AgentSpaceId，并替换以下命令中的 ID 以删除 AWS DevOps Agent 空间。```
aws devops-agent delete-agent-space --agent-space-id *<your-agent-space-id*>
```另外，删除为 AWS DevOps Agent 空间创建的 IAM 角色

### 为什么

这很重要：APF 透明度问题

此场景的一个重要见解是，API 优先级和公平性使应用程序代码部分不可见限制。当 API 服务器出现性能问题时，会发生以下情况：

- APF 层向客户端返回 429 响应。
- Kubernetes client-go 库（以及许多 HTTP 客户端）会自动重试。
- 在队列中短暂等待后，请求最终成功。
- 应用程序看到成功的响应，只是速度较慢。

这意味着有问题的工作负载在其日志中可能不会显示 429 错误，即使审核日志记录了数百个此类错误。仅查看应用程序日志的工程师将完全错过根本原因。该代理关联多个来源，包括 EKS 审核日志，这有助于有效地找到问题的根本原因。

这种模式在生产环境中很常见。协调循环中存在错误的控制器、进行过多 API 调用的 CI/CD 管道或过于积极的监控工具轮询都可能触发此行为。该代理能够自动查询审核日志并与指标和事件关联，这使其在诊断这些问题方面具有独特的有效性。

### 改进

AWS DevOps Agent 不仅可以通过自主调查当前问题来加速事件解决，还可以分析历史事件数据以提供防止问题重复发生的建议。通过将操作遥测与过去的事件相关联，代理可以识别新出现的风险模式并建议预防措施。团队可以主动解决漏洞，降低事件频率并提高系统可用性。

要查找改进详细信息，请导航到 AWS DevOps Agent Operator 门户并在导航窗格中选择改进。

### 结论

Kubernetes 控制平面性能问题是 DevOps 和 SRE 团队最具挑战性的诊断场景之一。微妙的延迟下降、429 次重试和多信号调查要求的结合使得手动诊断非常耗时且容易出错。AWS DevOps Agent 通过自动关联 CloudWatch 指标、审核日志、集群状态、CloudTrail 事件和工作负载模式来转变此流程，从而在几分钟而不是几小时内确定根本原因。通过查明导致性能问题的特定工作负载、服务帐户和 API 调用模式，代理允许团队采取有针对性的补救措施并实施预防措施。

组织正在大规模采用 Kubernetes 和容器化架构，AWS DevOps Agent 等工具可帮助团队保持卓越运营。我们鼓励您探索该服务如何转变您的 EKS 事件响应工作流程并帮助您构建更具弹性的应用程序。

您可以在多个 AWS 区域使用 AWS DevOps Agent（有关详细信息，请参阅[发布公告](https://aws.amazon.com/about-aws/whats-new/2026/03/aws-devops-agent-generally-available/)）。无论代理本身在何处运行，它都支持跨区域调查功能，使您可以监控、诊断跨多个 AWS 区域部署的资源并对其进行故障排除。

开始使用：

- [创建您的第一个 AWS DevOps Agent 空间](https://docs.aws.amazon.com/devopsagent/latest/userguide/getting-started-with-aws-devops-agent-creating-an-agent-space.html)
- [阅读 AWS DevOps Agent 文档](https://docs.aws.amazon.com/devopsagent/latest/userguide/getting-started-with-aws-devops-agent.html)
- [从这篇文章中克隆示例代码](https://github.com/aws-samples/sample-troubleshooting-eks-with-devops-agent)
- [了解有关 Amazon EKS 可观测性的更多信息](https://docs.aws.amazon.com/eks/latest/userguide/observability-dashboard.html)

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
