<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-27T03:00:45+08:00
source: NVIDIA Technical Blog
domain: AI 基础设施
url: https://developer.nvidia.com/blog/deploy-a-production-ready-nvidia-ai-q-blueprint-on-oracle-cloud-infrastructure/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 在 Oracle 云基础设施上部署生产就绪的 NVIDIA AI-Q 蓝图 | NVIDIA 技术博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-27 03:00 CST |
| 领域 | AI 基础设施 |
| 来源 | NVIDIA Technical Blog |
| 原文标题 | Deploy a Production-Ready NVIDIA AI-Q Blueprint on Oracle Cloud Infrastructure \| NVIDIA Technical Blog |
| 原文 | [打开原文](https://developer.nvidia.com/blog/deploy-a-production-ready-nvidia-ai-q-blueprint-on-oracle-cloud-infrastructure/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

过去两年，人工智能代理发生了很大变化。第一个一次只能回答一个问题。然后是多轮聊天，模型可以在其中保留......

## 正文

[数据中心/云](https://developer.nvidia.com/blog/category/data-center-cloud/)

English中文

## 在 Oracle 云基础设施上部署生产就绪的 

NVIDIA AI-Q 蓝图

![装饰图片。](https://developer-blogs.nvidia.com/wp-content/uploads/2025/08/genai-press-project-aiq-3503101-1920x1080-1-1024x576-jpg.webp)

2026 年 6 月 26 日

作者：[Anurag Kuppala](https://developer.nvidia.com/blog/author/akuppala/)、[Sanjay Basu](https://developer.nvidia.com/blog/author/sanjaybasu/) 和 [Felipe Garcia](https://developer.nvidia.com/blog/author/fdecarvalhop/)

喜欢

过去两年，人工智能代理发生了很大变化。第一个一次只能回答一个问题。然后是多轮聊天，模型可以在整个会话中保留一些上下文。今天，我们拥有长期代理。计划许多步骤、在子代理之间分配工作、在长期任务中保留上下文以及在安全沙箱中运行工具的系统。

[NVIDIA AI-Q 蓝图](https://build.nvidia.com/nvidia/aiq) 是此类代理的开源参考。它基于 [LangChain Deep Agents](https://docs.langchain.com/oss/python/integrations/providers/nvidia) 和 [NVIDIA NeMo Agent Toolkit](https://github.com/NVIDIA/NeMo-Agent-Toolkit) 构建。您可以将其用于快速引用的答案，或用于较长的带有来源的研究报告。

本文向您展示如何使用 Terraform 创建 OCI 资源并使用 Helm 在 Oracle Cloud Infrastructure (OCI) 上部署 AI-Q 2.0 以在 OKE 上安装工作负载。最后，您将在自己的 OCI 租赁中拥有一个可用的 AI-Q 端点，并在完成后通过一个命令将其全部关闭。

适用人群：熟悉 Kubernetes、Terraform 和 shell，并且希望在 OCI 而不是笔记本电脑上运行 AI-Q 的开发人员和平台工程师。

您将学到什么：AI-Q 的多代理架构如何映射到 OCI 服务，以及从头到尾配置、部署和打开蓝图的确切命令。

有关多代理架构（例如意图路由器、浅层研究代理、深层代理、规划子代理、研究员子代理）的更多背景信息，请参阅 [AI-Q 产品页面](https://build.nvidia.com/nvidia/aiq) 和 [NeMo Agent Toolkit 文档](https://github.com/NVIDIA/NeMo-Agent-Toolkit)。

先决条件

确保您有：

- OCI 租赁访问，包含可部署到的隔间，以及足够的服务限制：- OKE：1个增强集群和1个节点池
- 块卷：至少 10 GB（由 OKE CSI 驱动程序为集群内 PostgreSQL 动态配置）
- 负载均衡器：一个灵活的
- 保险库：一个保险库加秘密
- API 密钥：

- 来自 [build.nvidia.com](https://build.nvidia.com/) 的 NGC API 密钥，格式为“nvapi-”...既用作 NVIDIA 推理密钥，又用于向 NGC 容器注册表 (`nvcr.io`) 进行身份验证。
- 来自 [tavily.com](https://tavily.com/) 的 Tavilly API 密钥，格式为 `tvly-`...
- 本地工具：terraform 1.5 或更高版本、`kubectl` 1.28 或更高版本、`helm` 3.x 或更高版本、使用 API 签名密钥设置的 oci CLI
- Kubernetes、Helm 图表、Terraform 和 shell 的一些基本知识。有 LangChain 或 NeMo Agent Toolkit 经验固然很好，但不是必需的。

### 架构概述[](https://developer.nvidia.com/blog/deploy-a-production-ready-nvidia-ai-q-blueprint-on-oracle-cloud-infrastructure/#architecture_overview)

AI-Q 采用多智能体设计。意图路由器读取每个用户查询并将其发送到正确的工作流程。

![AI-Q 多智能体架构图。用户查询进入意图路由器，该路由器将其发送到浅层研究代理或深层代理。深度代理有一个规划子代理和一个研究员子代理。他们共享文件系统层（待办事项列表、内存、文件存储）并在隔离的沙箱中运行数据分析和图像处理等技能。入口点的数据源包括 MCP、AI 数据平台、Web 搜索和用户上传的文档。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201114%20646%22%3E%3C/svg%3E) 图 1. AI-Q 多代理架构。意图路由器将查询发送到浅层研究代理（快速、有界工具增强搜索）或深层代理（共享文件系统层并在沙箱中运行技能的规划子代理和研究子代理）

该蓝图被构建为可扩展的。每一层（模型、工具、RAG 后端、子代理、评估器）都可以通过 YAML 配置或 NeMo Agent Toolkit 插件系统进行交换。我们将在本系列的第 2 部分和第 3 部分中使用这种可扩展性。

### OCI 部署架构[](https://developer.nvidia.com/blog/deploy-a-production-ready-nvidia-ai-q-blueprint-on-oracle-cloud-infrastructure/#oci_deployment_architecture)该部署使用 Terraform 作为 OCI 资源，使用 Helm 作为 Kubernetes 工作负载。这在基础设施和应用程序之间提供了清晰的划分，并且一个“terraform destroy”足以在以后删除所有内容。

![AI-Q在OCI上部署的架构图。 VCN 内 OKE 集群前面的公共 OCI 负载均衡器，具有公共子网和 OKE 子网。 OKE 集群运行从 NVIDIA NGC 注册表中提取的三个工作负载：AI-Q 后端 (FastAPI)、AI-Q 前端 (Next.js) 和 PostgreSQL Pod。 OCI Vault 在配置时存储 NGC 和 Tavily API 密钥。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201600%201020%22%3E%3C/svg%3E) 图 2. OCI 上的 AI-Q 部署。 Terraform 创建 VCN、OKE 集群、负载均衡器和 Vault。 Helm 在 OKE 上安装 AI-Q 后端、前端和 PostgreSQL 工作负载。

|资源 | Terraform 模块 |目的|
|:---|:---|:---|
| VCN、子网、网关、NSG | `网络` |与公共子网和 OKE 子网的网络隔离 |
| OKE集群+节点池 | `好吧` | Kubernetes 运行时（增强型集群、VCN-原生 CNI）|
| OCI 负载均衡器 | `负载均衡器` |端口 80 上的公共 HTTP 入口，转发到 NodePort 30080 |
| OCI Vault + 秘密 | `金库` | API 密钥和凭证的 AES-256 加密存储 |

表 1. `deploy/terraform` 中 Terraform 模块创建的 OCI 资源。

Helm 图表在 OKE 上安装了三个工作负载：

- 后端（`aiq-backend`）：运行 AI-Q 工作流程的基于 FastAPI 的代理服务器。
- 前端（`aiq-frontend`）：通过 NodePort 30080 公开的“next.js” Web UI。
- PostgreSQL (`aiq-postgres`)：用于作业存储、检查点和摘要的集群内数据库。

### 部署步骤[](https://developer.nvidia.com/blog/deploy-a-production-ready-nvidia-ai-q-blueprint-on-oracle-cloud-infrastructure/#deployment_steps)```
git clone https://github.com/oracle-samples/ai-q.git cd ai-q/oke-samples/aiq-2.0
```总时间：约20至25分钟。完整参考位于 [aiq-2.0/README.md](https://github.com/oracle-samples/ai-q/blob/main/oke-samples/aiq-2.0/README.md) 中。

步骤 1. 配置 Terraform 变量

复制示例文件并使用您的租赁详细信息进行编辑：```
cd deploy/terraform cp terraform.tfvars.example terraform.tfvars
```至少，在 `terraform.tfvars` 中设置这些变量：

- `tenancy_ocid`、`compartment_id`、`region`（例如`us-chicago-1`）
- `user_ocid`、`fingerprint`、`private_key_path` （与您的 `~/.oci/config` 值相同）
- `db_admin_password`，用于引导集群内 PostgreSQL，存储在 OCI Vault 中。
- `nvidia_api_key`，来自 [build.nvidia.com](https://build.nvidia.com/) 的 NVIDIA NGC 密钥。用于推理并从“nvcr.io”中提取容器映像。
- `tavily_api_key`，来自 [tavily.com](https://tavily.com/) 的 Tavily 密钥，用于网络搜索。

步骤 2. 创建基础设施

初始化提供者，检查计划并应用：```
terraform 初始化 terraform 计划 terraform 应用
```这大约需要 10 到 15 分钟。 Terraform 使用静态加密的 NGC 和 Tavily API 密钥创建 VCN、OKE 集群、负载均衡器和 Vault。

检查：“terraform output”应显示“oke_cluster_id”和“lb_public_ip”的值。如果其中一个为空，请再次运行“terraform apply”——可以安全地重复该应用。

捕获下一步需要的两个值：```
export OKE_CLUSTER_ID="$(terraform output -raw oke_cluster_id)" export LB_PUBLIC_IP="$(terraform output -raw lb_public_ip)"
```步骤 3. 从 NGC Helm 图表安装 AI-Q

图表和容器镜像发布在 NGC 上，因此无需在本地构建任何内容。我们将“kubectl”指向新的 OKE 集群，创建图表使用的密钥，然后“helm pull”和“helm install”。

3a.为 OKE 集群配置 kubectl```
# 为 OKE 集群 oci ce 集群配置 kubectl create-kubeconfig \ --cluster-id "$OKE_CLUSTER_ID" \ --file ~/.kube/config \ --region us-ashburn-1 \ --token-version 2.0.0 \ --kube-endpoint PUBLIC_ENDPOINT # 健全性检查。节点应该准备好 kubectl 获取节点
```3b.导出 API 密钥

重复使用您在“terraform.tfvars”中放入的相同 NGC 和 Tavily 密钥。 NGC 密钥具有双重作用。它既是推理密钥，又是“nvcr.io”拉取凭证。```
export NGC_API_KEY="nvapi-..." # from build.nvidia.com export TAVILY_API_KEY="tvly-..." # from tavily.com export DB_USER_PASSWORD="<same value as db_admin_password in Step 1>"
```3c.创建命名空间和秘密```
kubectl 创建命名空间 ns-aiq --dry-run=client -o yaml | kubectl apply -f - # 应用程序凭证（NVIDIA + Tavily 推理，Postgres 用户） kubectl create Secret generic aiq-credentials -n ns-aiq \ --from-literal=NVIDIA_API_KEY="$NGC_API_KEY" \ --from-literal=TAVILY_API_KEY="$TAVILY_API_KEY" \ --from-literal=DB_USER_NAME="aiq" \ --from-literal=DB_USER_PASSWORD="$DB_USER_PASSWORD" # nvcr.io（NGC 容器注册表）的镜像拉取密钥 kubectl create Secret docker-registry ngc-secret -n ns-aiq \ --docker-server=nvcr.io \ --docker-username='$oauthtoken' \ --docker-password="$NGC_API_KEY"
```3d.从 NGC 拉取并安装图表```
cd ../helm # from deploy/terraform to deploy/helm helm pull https://helm.ngc.nvidia.com/nvidia/blueprint/charts/aiq2-web-2.0.0.tgz \ --username='$oauthtoken' \ --password="$NGC_API_KEY" helm upgrade --install aiq aiq2-web-2.0.0.tgz \ -n ns-aiq \ --wait --timeout 10m \ -f values-oci-ngc.yaml
```OCI 覆盖层（“values-oci-ngc.yaml”）故意很小——它仅将前端服务固定到 NodePort 30080（OCI 负载均衡器运行状况检查的端口），并命名为“ngc-secret”图像拉取密钥。图像存储库、Postgres init SQL 和动态配置的 10 Gi 块卷 PVC 均来自图表自身的默认值。

检查：“kubectl get pods -n ns-aiq”应在 3 到 5 分钟后显示处于“正在运行”状态的“aiq-backend”、“aiq-frontend”和“aiq-postgres” Pod。

步骤 4. 打开 AI-Q

LB IP 已在第 2 步中的 shell 中：```
echo "http://$LB_PUBLIC_IP"
```如果您从那时起打开了新的 shell，请从 Terraform 重新导出它：```
cd ../terraform export LB_PUBLIC_IP="$(terraform output -raw lb_public_ip)" echo "http://$LB_PUBLIC_IP"
```在浏览器中打开“http://<lb_public_ip>`”。您应该看到“AI-Q”前端。

首先尝试回答一个简单的问题，例如“NeMo Agent Toolkit 是什么？”，以确认路由是否有效。然后尝试更深层次的方法，例如“通过基准分数和成本比较排名前三的开源深度研究代理”，以了解深度代理的实际情况。

#### 故障排除[](https://developer.nvidia.com/blog/deploy-a-production-ready-nvidia-ai-q-blueprint-on-oracle-cloud-infrastructure/#troubleshooting)

- “terraform apply” 在创建“OKE”时失败，并出现配额错误。检查您所在分区的“集群计数”和“节点计数”的服务限制，并在需要时请求更多配额。
- Pod 陷入“ImagePullBackOff”状态。检查在步骤 3c 中运行“kubectl create Secret docker-registry ngc-secret”命令时是否已创建镜像拉取密钥（“kubectl get Secret -n ns-aiq”）以及“NGC_API_KEY”是否正确。要轮换，请删除密钥并重新创建它，然后“kubectl rollout restart deployment -n ns-aiq aiq-backend aiq-frontend”。
- “postgres” Pod 处于“Pending”状态超过 2 分钟。块卷 PVC 没有得到动态配置。运行“kubectl 描述 pvc -n ns-aiq”。典型原因是 OKE CSI 驱动程序未运行、默认 StorageClass 丢失或块卷配额不足。使用“kubectl get sc”检查存储类别以及您的分区的块卷服务限制。
- 负载均衡器 IP 返回为“null”。 OCI 在“Terraform”之后可能需要一两分钟才能完成“LB”。再次运行“terraformfresh”，然后运行“terraformoutputlb_public_ip”。
- 前端加载但查询返回“500”。查看“kubectl日志-n ns-aiq部署/aiq-backend”。最常见的原因是您在步骤 3c 中创建的“aiq-credentials”密钥中的“NVIDIA_API_KEY”或“TAVILY_API_KEY”错误或丢失。

#### 了解更多[](https://developer.nvidia.com/blog/deploy-a-production-ready-nvidia-ai-q-blueprint-on-oracle-cloud-infrastructure/#learn_more)

现在，您已经在 OCI 上进行了有效的“AI-Q 2.0”部署，并在完成后使用一个命令（“terraform destroy”）将其彻底删除。当您进一步前进时，需要记住以下几点：- 成本：OKE 节点池和负载均衡器在运行时不断产生成本。销毁实验之间的堆栈，或将节点池缩小到零。
- 秘密：Terraform 在配置时将 NGC 和 Tavily 密钥存储在 OCI Vault 中（用于审计和灾难恢复），但正在运行的 Pod 从您在步骤 3c 中创建的“aiq-credentials”Kubernetes 秘密中读取它们。要轮换、删除并使用新值重新创建该密钥，请执行“kubectl rollout restart deployment -n ns-aiq aiq-backend”。单独编辑 `terraform.tfvars` 无法到达 Pod。
- 可扩展性：您刚刚部署的所有内容均由 YAML 和 NeMo Agent Toolkit 插件系统驱动。交换“LLM”、添加子代理或插入新的 RAG 后端是配置更改，而不是重写。

克隆 [OCI 存储库中的 AI-Q](https://github.com/oracle-samples/ai-q.git) 并在 [NVIDIA 开发者论坛](https://forums.developer.nvidia.com/) 上分享您构建的解决方案以及您解决的问题。

喜欢

### 标签

[代理人工智能/生成人工智能](https://developer.nvidia.com/blog/category/generative-ai/) | [数据中心/云](https://developer.nvidia.com/blog/category/data-center-cloud/) | [一般](https://developer.nvidia.com/blog/recent-posts/?industry=General) | [蓝图](https://developer.nvidia.com/blog/recent-posts/?products=Blueprint) | [初级技术](https://developer.nvidia.com/blog/recent-posts/?learning_levels=Beginner+Technical) | [教程](https://developer.nvidia.com/blog/recent-posts/?content_types=Tutorial) | [人工智能代理](https://developer.nvidia.com/blog/tag/ai-agent/) | [浪链](https://developer.nvidia.com/blog/tag/langchain/)

### 关于作者

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于阿努拉格·库帕拉
Anurag Kuppala 是 NVIDIA CSP GTM 团队的解决方案架构师。他与云提供商合作，大规模设计和部署 GPU 加速的人工智能基础设施。他的工作重点是实现大规模训练和推理、优化分布式系统的性能以及为高性能人工智能工作负载构建云原生架构。 Anurag 的兴趣包括大规模人工智能系统、分布式计算以及不断发展的加速计算领域。[查看 Anurag Kuppala 的所有帖子](https://developer.nvidia.com/blog/author/akuppala/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于桑杰·巴苏
Sanjay Basu 是解决方案架构高级总监，领导 Oracle Cloud 的生成式 AI 和 GPU 云工程团队。 Sanjay 拥有 30 多年的技术经验，拥有管理和计算机工程高级学位，目前正在攻读第二个博士学位。在人工智能中。他是 ACM、AAAI、IEEE 会员以及电子和电信工程师学会会员。

[查看 Sanjay Basu 的所有帖子](https://developer.nvidia.com/blog/author/sanjaybasu/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于费利佩·加西亚
Felipe Garcia 是 NVIDIA CSP GTM 团队的解决方案架构师，他帮助云服务提供商扩展 GPU 加速的 AI 基础设施、代理和模型。在加入 NVIDIA 之前，他曾在 Oracle、Google、Microsoft 和 AWS 工作，构建和交付云和 AI 原生解决方案。

[查看 Felipe Garcia 的所有帖子](https://developer.nvidia.com/blog/author/fdecarvalhop/)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
