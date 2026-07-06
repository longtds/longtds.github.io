<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T15:00:00+08:00
source: Google Cloud Blog
domain: 云原生
url: https://cloud.google.com/blog/topics/developers-practitioners/scaling-llm-inference-multi-node-kv-cache-offloading-with-gke-managed-lustre/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 扩展 LLM 推理：使用 GKE 和托管 Lustre 进行多节点 KV 缓存卸载 |谷歌云博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 15:00 CST |
| 领域 | 云原生 |
| 来源 | Google Cloud Blog |
| 原文标题 | Scaling LLM Inference: Multi-Node KV Cache Offloading with GKE & Managed Lustre \| Google Cloud Blog |
| 原文 | [打开原文](https://cloud.google.com/blog/topics/developers-practitioners/scaling-llm-inference-multi-node-kv-cache-offloading-with-gke-managed-lustre/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

本文的重要贡献者包括 Google Kubernetes Engine 软件工程师 Sneha Aradhey 和 Google Cloud Managed Lustre 高级软件工程师 Michael MacDonald。企业生产环境正在转向分布式多节点架构，以服务于长上下文窗口长度和代理人工智能。随着这些工作负载的扩展，KVCache 通常会超出本地 CPU RAM 和主机 SSD 缓存层的容量。为了解决这个问题，一些设置尝试将节点本地存储池化到分布式层（例如多节点池化 NVMe 阵列）。池化 SSD 聚合原始容量并经常利用备用本地驱动器，呈现出明显的优势。然而，也存在一些限制：该方法要求计算集群管理其自身复杂的数据分布和跨节点复制。另一种方法是将注意力状态转移到专用的高性能外部并行文件系统。我们利用 Google Cloud Managed Lustre 和 llm-d 卸载堆栈作为集群范围的分散注意力缓存层，绕过主机级容量限制并消除管理本地池驱动器的网络开销。通过这种方法，我们可以大规模提高效率：

## 正文

开发者与从业者

##

扩展 

LLM 推理：使用 GKE 和托管 Lustre 进行多节点 KV 缓存卸载

2026 年 7 月 1 日

###### 米罗·尼科洛夫

资深软件工程经理，Google Cloud Managed Lustre

###### 巴拉克·爱泼斯坦

高级产品经理，Google Cloud Managed Lustre

本文的重要贡献者包括 Google Kubernetes Engine 软件工程师 Sneha Aradhey 和 Google Cloud Managed Lustre 高级软件工程师 Michael MacDonald。

企业生产环境正在转向分布式多节点架构，以服务于长上下文窗口长度和代理人工智能。随着这些工作负载的扩展，KVCache 通常会超出本地 CPU RAM 和主机 SSD 缓存层的容量。

为了解决这个问题，一些设置尝试将节点本地存储池化到分布式层（例如多节点池化 NVMe 阵列）。池化 SSD 聚合原始容量并经常利用备用本地驱动器，呈现出明显的优势。然而，也存在一些限制：该方法要求计算集群管理其自身复杂的数据分布和跨节点复制。

另一种方法是将注意力状态转移到专用的高性能外部并行文件系统。我们利用 Google Cloud Managed Lustre 和 llm-d 卸载堆栈作为集群范围的分散注意力缓存层，绕过主机级容量限制并消除管理本地池驱动器的网络开销。

通过这种方法，我们可以大规模提高效率：

Google Cloud Managed Lustre 可节省超过 50% 的 TCO，并将六节点 A3 Mega 集群上的 Llama-3.3-70B 推理的 GPU 小时要求降低近 60%。这些收益是通过将共享的、预填充的 KV 缓存卸载到 Lustre 的高性能层实现的，缓存命中率为 95%。

##### 基准配置

- 型号：Llama-3.3-70B
- 上下文动态：提示长度为 50,000 个标记，输入问题长度为 256 个标记，输出长度为 512 个标记。

##### 通过 CPU RAM 卸载扩展 Lustre KV 缓存解决方案托管 Lustre KV 缓存卸载架构可以通过将卸载集成到 CPU RAM 来扩展。对于 Llama-3.3-70B 推理，这种混合方法[与仅 CPU 卸载相比显着提高了性能](https://github.com/llm-d/llm-d/tree/main/guides/tiered-prefix-cache#llm-d-fs-connector--lustre)，首次令牌时间 (TTFT) 提高了约 40%，端到端延迟降低了 30%。

#### 用户指南

##### 架构组件

- GKE GPU 节点：专为高吞吐量模型执行和张量并行操作而配置的专用加速器资源。
- Managed Lustre：一个共享的高带宽并行文件系统，充当集中式外部层，缓存预填充注意力状态以消除冗余预填充计算。
- [PVC Evictor](https://github.com/llm-d/llm-d-kv-cache/tree/main/kv_connectors/pvc_evictor)：一种可扩展的分布式垃圾收集服务，可跟踪文件访问模式并自动删除最近最少使用 (LRU) 缓存块以保持健康的存储空间。

##### 目标模型

本指南根据您的模型偏好提供了两种不同的、经过验证的部署轨道：

- Qwen系列：`Qwen/Qwen3.5-35B-A3B`
- Gemma 4 架构：`google/gemma-4-31B-it`

##### 架构图

![https://storage.googleapis.com/gweb-cloudblog-publish/images/Scaling_LLM_Inference__Multi-Node_KV_Cache.max-2200x2200.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/Scaling_LLM_Inference__Multi-Node_KV_Cache.max-2200x2200.png)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/Scaling_LLM_Inference__Multi-Node_KV_Cache.max-2200x2200.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/Scaling_LLM_Inference__Multi-Node_KV_Cache.max-2200x2200.png)

##### 开始之前

在开始此部署之前，请确保您的 Google Cloud 项目已正确配置：- 配额：验证您对所选区域中的所选加速器有足够的配额，以及足够的常规 CPU、内存和 Managed Lustre 配额。
- [验证托管 Lustre 所需的 IAM 权限](https://docs.cloud.google.com/managed-lustre/docs/access-control)
- 准备环境以连接到 Managed Lustre：完成“[开始之前](https://docs.cloud.google.com/managed-lustre/docs/lustre-csi-driver-new-volume#before_you_begin)”步骤以启用 API、设置环境变量并设置 VPC。

- GKE 版本：GKE 版本 1.33 或更高版本支持 [托管 Lustre CSI 驱动程序](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/managed-lustre)。为了获得最佳体验和默认端口 (988) 使用情况，建议使用 GKE 版本 1.33.2-gke.4780000 或更高版本。

##### 所需步骤概述

- 创建 GKE 集群
- 创建GPU计算节点池
- 提供 Lustre 存储
- 使用 Lustre 部署 vLLM 服务引擎
- 部署 PVC 驱逐器
- 清理

##### 1. 创建 GKE 集群

创建一个快速通道 GKE 集群，并启用 Workload Identity 和所有必要的 CSI 存储插件（Lustre、GCSFuse 和持久磁盘）。

正在加载...

export CLUSTER_NAME="<INSERT CLUSTER NAME>" export ZONE="<INSERT ZONE>" export PROJECT_ID="<INSERT PROJECT>" export NETWORK_NAME="<INSERT NETWORK>" gcloud 容器配置 "$CLUSTER_NAME" \ --zone "$ZONE" \ --num-nodes "1" \ --network "${NETWORK_NAME}" \ --addons “HorizontalPodAutoscaling、HttpLoadBalancing、GcePersistentDiskCsiDriver、GcsFuseCsiDriver、LustreCsiDriver” \ --workload-pool “${PROJECT_ID}.svc.id.goog” \ --enable-management-prometheus \ --enable-ip-alias \ --enable-shielded-nodes \ --shielded-integrity-monitoring \ --no-shielded-secure-boot \ --node-locations "$ZONE" \ --network="${NETWORK_NAME}" \ --gateway-api=standard

##### 2.创建

GPU计算节点池

配置 GPU VM 节点池（例如“a3-megagpu-4g”、“a4-highgpu-4g”等）。

加载中...gcloud beta 容器节点池创建 gpu-vm 节点池 \ --location="$ZONE" \ --cluster="$CLUSTER_NAME" \ --project="$PROJECT_ID" \ --accelerator="type=<INSERT GPU_ACCELERATOR_NAME>,count=<INSERT GPU_COUNT>,gpu-driver-version=LATEST" \ --machine-type="<INSERT GPU_COMPUTE_VM_MACHINE TYPE>" \ --num-nodes="<INSERT NODE_COUNT>" \ --enable-gvnic \ --no-enable-autoupgrade # 获取集群凭据 gcloud 容器集群 get-credentials "$CLUSTER_NAME" --zone "$ZONE"

##### 3.配置Lustre存储（自动配置）

在部署 vLLM 之前，您需要配置 Lustre 存储。我们通过“StorageClass”和“PersistentVolumeClaim”（PVC）使用自动配置的 Lustre 实例。

创建一个名为“lustre-pvc.yaml”的文件，其中包含以下内容：

正在加载...

apiVersion: storage.k8s.io/v1 kind: StorageClass 元数据: name: lustre-class 配置程序: lustre.csi.storage.gke.io volumeBindingMode: Immediate reclaimPolicy: Delete mountOptions: - localflock 参数: perUnitStorageThroughput: "<CHOOSE_PERFORMANCE_TIER>" # 请参阅下面的选项。 network: "<INSERT NETWORK_NAME>" --- apiVersion: v1 kind: PersistentVolumeClaimmetadata: name: lustre-pvc spec: accessModes: - ReadWriteMany resources: requests: storage: <INSERT CAPACITY_GiB> # 范围从 9000Gi 到 84016000Gi，增量和范围取决于 Lustre 层。 storageClassName：光泽级

注：性能等级选项为“125”、“250”、“500”和“1000”。每层容量范围和增量可以在[此处](https://docs.cloud.google.com/managed-lustre/docs/performance-tiers) 找到。

应用此清单来配置 Lustre 实例并观察配置情况：

正在加载...

# 1. 将文件提交到集群（立即完成） kubectl apply -f lustre-pvc.yaml # 2. 观看实时配置流，直到显示“Bound” kubectl get pvc lustre-pvc -w

##### 4. 使用 Lustre 部署 v

LLM 服务引擎

步骤 4a：创建拥抱面部访问密钥

在提交部署清单之前，您必须将 Hugging Face API [令牌](https://huggingface.co/docs/hub/en/security-tokens) 配置为集群内的安全机密。

运行以下命令，将 `<INSERT_HF_TOKEN>` 替换为您的令牌：

正在加载...

kubectl 创建秘密通用 hf-token-secret \ --from-literal=token="<INSERT_HF_TOKEN>" \ --namespace=default

步骤 4b：创建 vLLM 部署清单此完整的 Kubernetes 清单部署 vLLM 引擎，配置“llmd-fs-connector”以实现高性能 KV 缓存，并安装并行 Lustre 存储 (“lustre-pvc”)。

通用清单（在 Qwen3.5 或 gemma-4 之间选择）

将 <> 之间的示例值替换为适合您环境的值。

加载中...apiVersion: apps/v1 kind: 部署元数据: 名称: vllm-storage 命名空间: 默认标签: app: vllm-storage 规格: 副本: 1 选择器: matchLabels: app: vllm-storage 模板: 元数据: 标签: app: vllm-storage 规格: nodeSelector: cloud.google.com/gke-accelerator: nvidia-h100-80gb 容忍度: - key: “nvidia.com/gpu”运算符：“存在”效果：“NoSchedule”securityContext：fsGroup：<YOUR_NON_ROOT_GID> runAsUser：<YOUR_NON_ROOT_UID>卷：-名称：lustre-storage permanentVolumeClaim：claimName：lustre-pvc-名称：shm emptyDir：medium：内存大小限制：“200Gi”容器：-名称： vllm-storage 镜像：vllm/vllm-openai:v0.23.0-cu129 volumeMounts: - mountPath: /mnt/files-storage 名称：lustre-storage 命令：- "/bin/bash" args: - "-c" - |设置 -x 导出 USER=vllm 导出日志名称=vllm pip install --user msgpack pip install 'llmd-fs-connector==0.23' --extra-index-url https://llm-d.github.io/llm-d-kv-cache/simple/ vllm 服务 <MODEL_NAME> \ # google/gemma-4-31B-it 或 Qwen/Qwen3.5-35B-A3B --download-dir /model/models \ --load-format auto \ --kv-transfer-config '{ "kv_connector": "MultiConnector", "kv_role": "kv_both", "kv_connector_extra_config": { "connectors": [{ "kv_connector": "OffloadingConnector", "kv_role": "kv_both", "kv_connector_extra_config": { “cpu_bytes_to_use”：64424509440，“lazy_offload”：true } }，{“kv_connector”：“OffloadingConnector”，“kv_role”：“kv_both”，“kv_connector_extra_config”：{“spec_name”：“SharedStorageOffloadingSpec”，“spec_module_path”： "llmd_fs_backend.spec", "shared_storage_path": "/mnt/files-storage/llmd-kv-cache/", "threads_per_gpu": 32, "block_size": <BLOCK_SIZE> # gemma 为 256 或 Qwen3.5 为 528 } } ] } }' \ --distributed_executor_backend “mp” \ --port 8000 \ --max_num_batched_tokens 16384 \ --enable-chunked-prefill \ --max-model-len 32000 \ --gpu-内存利用率 0.92 \ --tensor-parallel-size "4" \ --prefix-caching-hash-algo sha256_cbor \ --enable_prefix_caching \ --enforce-eager \ --no-disable-hybrid-kv-cache-manager env: - name: HUGGING_FACE_HUB_TOKEN valueFrom: SecretKeyRef: name: hf-token-secret key: token # ... 探针 ... 资源: 请求: nvidia.com/gpu: "4" 限制: nvidia.com/gpu: "4"

注意：Qwen-3.5 特别要求块大小为“528”以避免碎片，而 Gemma 4 使用默认的“256”可以完美运行。

步骤 4c：应用并验证部署

要将此清单应用到您的集群，请运行：正在加载...

kubectl apply -n default -f vllm-lustre-deployment.yaml

步骤 4d：跟踪模型下载状态

由于大型模型在首次启动时可能需要一些时间来下载，因此可以通过流式传输容器日志来直接跟踪初始化日志：

重击

正在加载...

kubectl 部署状态部署/vllm-storage

##### 5. 部署 PVC 驱逐器

###### PVC 驱逐器概述

架构与角色

“llmd_fs_backend”连接器将 KV 缓存块卸载到 Lustre，但本身不会删除旧的缓存文件。随着时间的推移，缓存将填满共享文件系统。 PVC Evictor 充当外部垃圾收集器，持续监控磁盘使用情况并逐出最近最少使用 (LRU) 文件以保持健康的存储空间。

扩展和分片

PVC Evictor 支持分片，并且可以扩展到多个副本，以匹配 Lustre 实例的容量和性能。根据经验，您应该为每 72 TB Lustre 容量部署 1 个逐出器副本，以有效地分配逐出负载，而不会使元数据服务器不堪重负。

对于大规模部署，驱逐器可以配置为与多个分片一起运行。在多副本模式下运行时，工作负载跨 Pod 分区，每个 Pod 管理缓存命名空间的特定分片。这可以防止冗余元数据扫描和竞争条件。

高性能资源需求

大规模运行驱逐器（例如，使用 16 个并行爬虫进程）需要大量 CPU 和内存资源来处理数百万个文件的快速扫描和队列管理。确保为 Pod 提供足够的资源（例如 12 个 CPU 请求和 8Gi 内存请求）并在适当的节点类型（例如“c4-standard-16”）上进行调度。

PVC 驱逐器部署步骤

PVC Evictor 使用位于“kv_connectors/pvc_evictor/helm”中的图表通过 Helm 进行部署。

步骤 5a：为 Evictor 创建专用节点池

大规模运行驱逐器需要大量的 CPU 和内存。首先，使用高性能机器类型（例如 c4-standard-16）创建专用节点池，以适应每个 Pod 所需的 12 个 CPU 和 8Gi 内存请求。

加载中...# 为 PVC Evictor gcloud 容器创建专用节点池 node-pools create evictor-pool \ --location="$ZONE" \ --cluster="$CLUSTER_NAME" \ --project="$PROJECT_ID" \ --machine-type="c4-standard-16" \ --num-nodes="1"

步骤 5b：通过 Helm 安装（高性能配置）

部署一个具有 2 个副本的扩展的高性能驱逐器池来监控 lustre-pvc。此配置每个 Pod 使用 16 个爬虫进程来处理大量文件命名空间。

关于安全上下文的注意事项：要允许 evictor pod 删除 vLLM 创建的文件，它必须使用匹配的安全上下文 ID 运行。确保占位符“<YOUR_NON_ROOT_GID>”和“<YOUR_NON_ROOT_UID>”与 vLLM 部署的“securityContext”中使用的非根值完全匹配，以确保共享 POSIX 文件权限。

正在加载...

git克隆--深度1 https://github.com/llm-d/llm-d-kv-cache.git cd llm-d-kv-cache/kv_connectors/pvc_evictor helm安装pvc-evictor ./helm \ --namespace default \ --set replicaCount=1 \ --set config.numCrawlerProcesses=16 \ --set config.deletionBatchSize=5000 \ --set config.fileQueueMinSize=1000000 \ --set config.fileQueueMaxsize=2000000 \ --set config.fileAccessTimeThresholdMinutes=10 \ --set securityContext.container.runAsNonRoot=false \ --set pvc.name="lustre-pvc" \ --set config.cleanupThreshold=85.0 \ --set config.targetThreshold=70.0 \ --set config.cacheDirectory="llmd-kv-cache" \ --set securityContext.pod.fsGroup=<YOUR_NON_ROOT_GID> \ --set securityContext.container.runAsUser=<YOUR_NON_ROOT_UID> \ --set resources.requests.cpu=12 \ --set resources.requests.memory=8Gi \ --set resources.limits.cpu=15 \ --set resources.limits.memory=16Gi \ --set nodeSelector."cloud\.google\.com/gke-nodepool"=evictor-pool \ --set securityContext.pod.seLinuxOptions.level="s0:c0\,c1"

##### 关键参数解释：

- `replicaCount=2`：部署 2 个 evictor pod。当使用多个副本时，Helm 图表会自动配置分片（“totalShards=2”）。
- `config.numCrawlerProcesses=16`：每个 Pod 运行 16 个并行爬虫线程以快速扫描文件系统。
- `config.deletionBatchSize=5000`：批量删除 5000 个文件以减少元数据开销。
- `config.fileQueueMinSize` 和 `config.fileQueueMaxsize`：配置大内存队列（最小 1M，最大 2M）来缓冲要删除的文件，以匹配高爬虫吞吐量。
- `config.fileAccessTimeThresholdMinutes=10`：触发清理阈值时，积极逐出过去 10 分钟内未访问过的文件。
- `securityContext.container.runAsNonRoot=false`：如果逐出者需要类似 root 的权限来管理/删除共享存储上不同用户所有权的文件，则需要此选项。
- `resources.requests` 和 `limits`：为每个 Pod 分配 12-15 个 CPU 和 8-16Gi 内存，以确保大量爬虫进程不会受到 CPU 限制或运行内存不足 (OOM)。

步骤 5c：验证和监控

正在加载...

# 验证 pod 状态 kubectl get pods -l app.kubernetes.io/name=pvc-evictor -n default

##### 第 6 步：清理

由于此部署提供了大量且成本高昂的硬件，因此完成后请务必清理您的环境，以避免产生不必要的费用。

重击

正在加载...

helm uninstall pvc-evictor && kubectl delete -f vllm-lustre-deployment.yaml kubectl delete pvc lustre-pvc # 删除集群（这也会删除关联的节点池） gcloud 容器集群 delete "$CLUSTER_NAME" \ --zone "$ZONE" \ --project "$PROJECT_ID" \ --quiet # 注意：Lustre StorageClass reclaimPolicy 设置为删除， # 因此会销毁PVC 或 Cluster 将自动清理底层 Lustre 存储。

#### 附录：Llama-3.3-70B 基准测试的参考配置

以下配置是用于生成本文中引用的 Llama-3.3-70B 基准测试结果的部署清单的表示。提供它是为了完整性和透明度。

注意：此配置利用软件堆栈的早期迭代 (vLLM v0.15.0) 和收集数据时在基准测试环境中处于活动状态的特定基础设施标志。

加载中...apiVersion: apps/v1 kind: 部署元数据: 名称: vllm-storage 命名空间: 默认标签: app: vllm-storage 规范: 副本: 1 选择器: matchLabels: app: vllm-storage 模板: 元数据: 标签: app: vllm-storage 规范: 卷: - 名称: lustre-storage permanentVolumeClaim: ClaimName: lustre-pvc - 名称: shm emptyDir: 中:内存大小限制：“200Gi”-名称：kv-store-disk permanentVolumeClaim：claimName：lustre-pvc容器：-名称：vllm-storage图像：vllm/vllm-openai：v0.15.0命令：-“/bin/bash”参数：-“-c”-| pip install https://raw.githubusercontent.com/kfirtoledo/llm-d-kv-cache-manager/connector/kv_connectors/llmd_fs_backend/wheels/llmd_fs_connector-0.1.0-cp312-cp312-linux_x86_64.whl; \ mkdir -p /tmp/prometheus_metrics;导出 PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_metrics; \ vllm服务meta-llama/Llama-3.3-70B-Instruct \ --download-dir /model/models \ --load-format runai_streamer \ --kv-transfer-config '{ "kv_connector": "OffloadingConnector", "kv_role": "kv_both", "kv_connector_extra_config": { "spec_name": “SharedStorageOffloadingSpec”，“spec_module_path”：“llmd_fs_backend.spec”，“shared_storage_path”：“/mnt/files-storage/llmd-kv-cache/”，“block_size”：1024，“threads_per_gpu”：“64”}}'\--distributed_executor_backend“mp”\--port 8000 \ --max_num_batched_tokens 16384 \ --enable-chunked-prefill \ --tensor-parallel-size 8 \ --enable_prefix_caching \ --gpu-memory-utilization 0.9 env： - 名称：HUGGING_FACE_HUB_TOKEN valueFrom：secretKeyRef：名称：hf-token-秘密密钥：令牌 - 名称： VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS 值：“3000”-名称：PYTHONHASHSEED 值：“123”端口：-containerPort：8000 资源：限制：nvidia.com/gpu：“8”请求：cpu：“200”内存：1024G 临时存储：5120Gi nvidia.com/gpu：“8” volumeMounts: - name: lustre-storage mountPath: /model - mountPath: /root/.cache/huggingface name: lustre-storage subPath: Huggingface-cache - name: shm mountPath: /dev/shm - mountPath: /mnt/files-storage name: kv-store-disk # ...为简洁起见，省略了探针 ...

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
