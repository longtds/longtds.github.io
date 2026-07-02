<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T19:00:00+08:00
source: CNCF Blog
domain: 云原生
url: https://www.cncf.io/blog/2026/07/01/understanding-dynamic-resource-allocation-in-kubernetes/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# 了解 Kubernetes 中的动态资源分配

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 19:00 CST |
| 领域 | 云原生 |
| 来源 | CNCF Blog |
| 原文标题 | Understanding dynamic resource allocation in Kubernetes |
| 原文 | [打开原文](https://www.cncf.io/blog/2026/07/01/understanding-dynamic-resource-allocation-in-kubernetes/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

动态资源分配（DRA）最近在 Kubernetes v1.35 中达到了 GA，相信我们很多人都渴望尝试一下。 NVIDIA 已将 dra-driver-nvidia-gpu 移至 Kubernetes SIG，这进一步推动了这一势头，...

## 正文

动态资源分配（DRA）最近在 Kubernetes v1.35 中达到了 GA，相信我们很多人都渴望尝试一下。 NVIDIA 已将 dra-driver-nvidia-gpu 移至 Kubernetes SIG，文档中删除了 Beta 标签，这标志着该技术及其标准正在逐渐成熟，这进一步推动了这一势头。

在这篇文章中，我借用了 [CNTUG Infra Labs](https://docs.cloudnative.tw/) 目前提供的所有 NVIDIA GPU，以了解如何使用 DRA 优雅地分配设备和资源。

#### CNTUG Infra Labs：实验室环境概述

CNTUG Infra Labs 的成立旨在培养台湾软件基础设施领域的下一代学生和工程师。该实验室托管在 Equinix 的东京数据中心，由多名 CNTUG 社区成员共同资助。构建环境利用了一系列开源项目，包括 OpenStack、Ceph 和 Ansible

。

由于基础设施软件具有陡峭的学习曲线，并且需要大量的计算、存储和网络资源，CNTUG Infra Labs 旨在提供一个云平台，学生和社区成员可以在其中试验和托管相关服务。还向开源社区提供备用容量，用于托管网站、Mattermost 和 Jitsi Meet 等服务，或用于研讨会活动。您可以查看[用例](https://docs.cloudnative.tw/usecase)以了解更多详细信息。

#### 实验室环境

我们将使用使用 Cluster API + OpenStack 构建的 Kubernetes 集群。为了简洁起见，这里省略了设置过程 - 请随意参考其他博客文章以了解详细信息，或者等待我写完以后的文章。

- 操作系统：Ubuntu 24.04
- Kubernetes v1.35.3
- 容器2.2.2
- 节点：

- 1 个控制平面 + etcd
- 3名工人

- 没有GPU
- T10*2
- A5000*1

- NVIDIA GPU Operator v26.3.1
- NVIDIA DRA 驱动程序 GPU v25.12.0

运行 kubectl get node 应返回类似以下内容的内容：```
姓名 状态 角色 年龄 版本
capi-dralabs-control-plane-xtcth 就绪控制平面 8m7s v1.35.3
capi-dralabs-md-0-p4xkh-rpfxc 就绪 <无> 6m55s v1.35.3
capi-dralabs-md-gpua5000-jw4mx-d64jz 就绪 <无> 2m37s v1.35.3
capi-dralabs-md-gput10-gzl84-f2m2d 就绪 <无> 6m49s v1.35.3

```#### 安装 NVIDIA GPU Operator

在安装 GPU Operator 之前，标记具有 GPU 的节点。对于我的环境，这看起来像：```
kubectl label node capi-dralabs-md-gpua5000-jw4mx-d64jz
nvidia.com/dra-kubelet-plugin=true
kubectl label node capi-dralabs-md-gput10-gzl84-f2m2d
nvidia.com/dra-kubelet-plugin=true
```添加 NVIDIA 图表存储库：```
helm 存储库添加 nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update
```创建一个我们将在安装过程中使用的values-gpu-operator.yaml 文件：

值-gpu-operator.yaml```
# version: v26.3.1
devicePlugin:
enabled: false

driver:
manager:
env:
- name: NODE_LABEL_FOR_GPU_POD_EVICTION
value: "nvidia.com/dra-kubelet-plugin"
```注意

如果您使用不同的 Kubernetes 发行版（例如 Rancher 或 K3s），默认的 Containerd 安装路径可能会有所不同 - 请记住将以下设置添加到values-gpu-operator.yaml：```
toolkit:
env:
- name: CONTAINERD_SOCKET
值：/run/k3s/containerd/containerd.sock
```安装 NVIDIA GPU Operator：```
helm upgrade --install gpu-operator nvidia/gpu-operator \
--version=v26.3.1 \
--create-namespace \
--namespace gpu-operator -f values-gpu-operator.yaml

```等待 GPU 操作员出现。它将安装 NVIDIA GPU 驱动程序并调整容器运行时配置。具体调优需求请参考【NVIDIA官方文档】(https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/overview.html)。

#### 安装 

NVIDIA DRA GPU 驱动程序

创建一个我们将在安装过程中使用的values-nvidia-dra-driver-gpu.yaml 文件：

值-nvidia-dra-driver-gpu.yaml````
# version: 25.12.0
nvidiaDriverRoot：/run/nvidia/driver
gpuResourcesEnabledOverride: true
image:
pullPolicy: IfNotPresent
kubeletPlugin:
nodeSelector:
nvidia.com/dra-kubelet-plugin：“真实”
resources:
gpus:
enabled: true
computeDomains:
enabled: false # 这里没有 NVLink
# featureGates:
#   TimeSlicingSettings: true

```如果您想稍后尝试[场景四的GPU时间切片](https://docs.google.com/document/d/19HfO3UlrPod6pMqNyXuZuBcm8NUOsktOZDoeysdo4HY/edit?pli=1#bookmark=id.qyv7kwp9nn3x)，您可以立即启用TimeSlicingSettings功能门；否则，请将其注释掉，并在需要时进行升级。

安装 NVIDIA DRA GPU 驱动程序：```
helm upgrade -i nvidia-dra-driver-gpu nvidia/nvidia-dra-driver-gpu \
--version="25.12.0" \
--namespace nvidia-dra-driver-gpu \
--create-namespace -f values-nvidia-dra-driver-gpu.yaml

```使用 kubectl get pod 确认 NVIDIA DRA 驱动程序 GPU 已启动：```
kubectl get pod -n nvidia-dra-driver-gpu
名称就绪状态重新开始年龄
nvidia-dra-driver-gpu-kubelet-plugin-6skhp 1/1 运行 0 10m
nvidia-dra-driver-gpu-kubelet-plugin-jswk6 1/1 运行 0 10m

```#### DRA 初探

##### 设备类

安装完成后，你会发现DeviceClass和ResourceSlice已经被NVIDIA DRA Driver GPU设置好了。顾名思义，DeviceClass 代表设备类别 - 打开它会显示常规 GPU、MIG 和 VFIO。 （如果没有禁用 ComputeDomains，您还将看到 ComputeDomains 信息。）```
kubectl get deviceclass
```DeviceClass 示例输出```
NAME                  AGE
gpu.nvidia.com        44m
mig.nvidia.com        44m
vfio.gpu.nvidia.com 44m
```#### 资源切片

ResourceSlice 由每个节点上的 DRA 驱动程序自动更新，记录该驱动程序在该节点上管理的所有设备。

同一节点上由同一驱动程序管理的设备属于同一Pool。当设备计数超过单个对象的容量时（最多 128 个条目，如果任何设备使用污点或计数器，则为 64 个条目），驱动程序会将池拆分为多个 ResourceSlice。

.spec.pool. Generation 和 .spec.pool.resourceSliceCount 让调度程序确定它是否具有给定节点的完整且最新的设备列表。```
kubectl get resourceslice
```资源切片示例输出```
名称节点驱动程序池年龄
capi-dralabs-md-gpua5000-jw4mx-d64jz-gpu.nvidia.com-w9fnv
capi-dralabs-md-gpua5000-jw4mx-d64jz gpu.nvidia.com
capi-dralabs-md-gpua5000-jw4mx-d64jz   5m13s
capi-dralabs-md-gput10-gzl84-f2m2d-gpu.nvidia.com-dtgtc
capi-dralabs-md-gput10-gzl84-f2m2d gpu.nvidia.com
卡皮-dralabs-md-gput10-gzl84-f2m2d 23m

```您可以使用 -o yaml 扩展完整内容：```
kubectl get resourceslices -o yaml
```单击下面的面板查看完整的输出。每个 ResourceSlice 在 .metadata.ownerReferences 中记录其节点，在 .spec.devices 中记录其设备。每个设备都带有属性，包括（但不限于）架构、产品名称和驱动程序版本。

由于本实验中的每个节点最多有 2 个 GPU（远低于单个 ResourceSlice 的 128 个条目限制），因此每个节点仅显示一个 ResourceSlice。

▼ 完整的资源切片输出```
apiVersion: v1
items:
- apiVersion: resource.k8s.io/v1
kind: ResourceSlice
metadata:
creationTimestamp: "2026-05-04T14:40:17Z"
生成名称：capi-dralabs-md-gpua5000-jw4mx-d64jz-gpu.nvidia.com-
generation: 1
名称：capi-dralabs-md-gpua5000-jw4mx-d64jz-gpu.nvidia.com-w9fnv
ownerReferences:
- apiVersion: v1
controller: true
kind: Node
名称：capi-dralabs-md-gpua5000-jw4mx-d64jz
uid: 83aafab6-7eb3-42d0-9faf-6118f78341ef
resourceVersion: "11490"
uid: d03fd27e-f6cb-4386-ae61-80aa84309e77
spec:
devices:
- attributes:
addressingMode:
string: HMM
architecture:
string: Ampere
brand:
string: NvidiaRTX
cudaComputeCapability:
version: 8.6.0
cudaDriverVersion:
version: 13.0.0
driverVersion:
version: 580.126.20
productName:
string: NVIDIA RTX A5000
resource.kubernetes.io/pciBusID:
string: "0000:00:06.0"
resource.kubernetes.io/pcieRoot:
string: pci0000:00
type:
string: gpu
uuid:
string: GPU-e13ce856-7474-797f-d143-16e99b65c0c3
capacity:
memory:
value: 23028Mi
name: gpu-0
驱动程序：gpu.nvidia.com
节点名称：capi-dralabs-md-gpua5000-jw4mx-d64jz
pool:
generation: 1
名称：capi-dralabs-md-gpua5000-jw4mx-d64jz
resourceSliceCount: 1
- apiVersion: resource.k8s.io/v1
kind: ResourceSlice
metadata:
creationTimestamp: "2026-05-04T14:21:53Z"
生成名称：capi-dralabs-md-gput10-gzl84-f2m2d-gpu.nvidia.com-
generation: 1
名称：capi-dralabs-md-gput10-gzl84-f2m2d-gpu.nvidia.com-dtgtc
ownerReferences:
- apiVersion: v1
controller: true
kind: Node
名称：capi-dralabs-md-gput10-gzl84-f2m2d
uid: d7ecdc93-1d6c-4868-8503-4251bcf8cf3b
resourceVersion: "7408"
uid: 66f32713-c547-4369-84de-97f86430d18d
spec:
devices:
- attributes:
addressingMode:
string: HMM
architecture:
string: Turing
brand:
string: Nvidia
cudaComputeCapability:
version: 7.5.0
cudaDriverVersion:
version: 13.0.0
driverVersion:
version: 580.126.20
productName:
string: Tesla T10
resource.kubernetes.io/pciBusID:
string: "0000:00:06.0"
resource.kubernetes.io/pcieRoot:
string: pci0000:00
type:
string: gpu
uuid:
字符串：GPU-dae084a2-974c-00e2-6dec-4ba1999b8652
capacity:
memory:
value: 16Gi
name: gpu-0
- attributes:
addressingMode:
string: HMM
architecture:
string: Turing
brand:
string: Nvidia
cudaComputeCapability:
version: 7.5.0
cudaDriverVersion:
version: 13.0.0
driverVersion:
version: 580.126.20
productName:
string: Tesla T10
resource.kubernetes.io/pciBusID:
string: "0000:00:07.0"
resource.kubernetes.io/pcieRoot:
string: pci0000:00
type:
string: gpu
uuid:
string: GPU-d1bf2033-42f6-096c-b0c6-470575bc08df
capacity:
memory:
value: 16Gi
name: gpu-1
驱动程序：gpu.nvidia.com
节点名称：capi-dralabs-md-gput10-gzl84-f2m2d
pool:
generation: 1
名称：capi-dralabs-md-gput10-gzl84-f2m2d
resourceSliceCount: 1
kind: List
metadata:
resourceVersion: ""

```有了这些信息，Pod 如何告诉 Kubernetes 它需要哪些设备？这就是 ResourceClaim 和 ResourceClaimTemplate 的用武之地！

#### 资源声明和资源声明模板

如果您希望多个 Pod 共享同一设备，可以手动创建 ResourceClaim。无论 Pod 创建或删除，它都保持完全独立。

![资源声明图/流程图](https://www.cncf.io/wp-content/uploads/2026/06/image-9.jpeg)

如果您希望每个 Pod 都有自己的专用设备怎么办？ ResourceClaimTemplate 允许您预定义 ResourceClaim。一旦 Deployment 按名称引用模板，每个新 Pod 都会自动获取相应的 ResourceClaim；相反，删除 Pod 会删除其声明。

![ResourceClaim模板图](https://www.cncf.io/wp-content/uploads/2026/06/image-10.jpeg)

这些概念是不是感觉很熟悉？ DRA 仿照 Kubernetes 中的 Storage — PersistentVolumeClaim 和 PersistentVolumeClaimTemplate（后者仅存在于 StatefulSet 中），DeviceClass 大致扮演 StorageClass 的角色。

### DRA 实践

#### 场景一：两个容器共享一个 

GPU

使用 ResourceClaim 声明我们需要一个 NVIDIA GPU，然后运行一个包含两个共享该 GPU 的容器的 Pod。

lab01-rc.yaml```
apiVersion: resource.k8s.io/v1
kind: ResourceClaim
metadata:
name: must-nvidia-gpu
spec:
devices:
requests:
- name: gpu
exactly:
deviceClassName: gpu.nvidia.com
count: 1

```应用资源：```
kubectl apply -f lab01-rc.yaml
```使用 get 检查 ResourceClaim：```
kubectl get resourceclaim
```状态为待处理，因为还没有 Pod 正在使用它。```
NAME              STATE     AGE
必须 nvidia-gpu 等待 10 秒
```现在定义一个包含两个容器的 Pod，两个容器都引用我们刚刚创建的 Must-nvidia-gpu ResourceClaim。

lab01-pod.yaml```
apiVersion: v1
kind: Pod
metadata:
name: must-nvidia-gpu-pod
spec:
restartPolicy: Never
containers:
- name: ctr0
image: ubuntu:24.04
command: ["bash", "-c"]
args: ["nvidia-smi -L; trap 'exit 0' TERM; sleep 9999 & wait"]
resources:
claims:
- name: gpu
- name: ctr1
image: ubuntu:24.04
command: ["bash", "-c"]
args: ["nvidia-smi -L; trap 'exit 0' TERM; sleep 9999 & wait"]
resources:
claims:
- name: gpu
resourceClaims:
- name: gpu
resourceClaimName: must-nvidia-gpu

```应用 Pod：```
kubectl apply -f lab01-pod.yaml
```再次检查 ResourceClaim：```
kubectl get resourceclaim
```状态更改为已分配和已保留，因为 Pod 现在正在使用该资源。```
NAME              STATE                AGE
必须分配 nvidia-gpu，保留 16s
```现在我们可以使用日志来打印输出：```
kubectl logs pod must-nvidia-gpu-pod --all-containers --prefix
[pod/must-nvidia-gpu-pod/ctr0] GPU 0: Tesla T10 (UUID:
GPU-dae084a2-974c-00e2-6dec-4ba1999b8652)
[pod/must-nvidia-gpu-pod/ctr1] GPU 0: Tesla T10 (UUID:
GPU-dae084a2-974c-00e2-6dec-4ba1999b8652)
```实际上，它可能不是 T10，也可能是 A5000。

现在删除 Pod：```
kubectl删除-f lab01-pod.yaml
```再次检查 ResourceClaim：```
kubectl get resourceclaim
```状态返回到待处理，因为没有 Pod 不再使用该资源。```
NAME              STATE     AGE
必须 nvidia-gpu 待处理 3 分 39 秒
```删除资源声明：```
kubectl delete -f lab01-rc.yaml
```上面的示例只需要一个 GPU，但没有告诉我们会得到哪一个。

这个场景与原始的设备插件没有什么不同，对吧？接下来的场景才是 DRA 真正大放异彩的地方！

#### 场景 II：ResourceClaimTemplate — 在部署中首选 A5000

今天，一位工程师向我询问一个更喜欢 A5000 的推理模型，但由于 A5000 很稀缺，因此在扩展时它们可以回落到 T10。

除此之外，ResourceClaim 还支持用于排名偏好的firstAvailable。 [回到完整的 ResourceSlice 输出](https://docs.google.com/document/d/19HfO3UlrPod6pMqNyXuZuBcm8NUOsktOZDoeysdo4HY/edit?pli=1#bookmark=id.exsay057icpn)，我们可以使用 .attributes.productName 按名称定位 GPU。

配置如下：

lab02.yaml```
apiVersion: resource.k8s.io/v1
kind: ResourceClaimTemplate
metadata:
name: first-a5000
spec:
spec:
devices:
requests:
- name: gpu
firstAvailable:
- name: a5000
设备类名称：gpu.nvidia.com
selectors:
- cel:
表达式：device.attributes["gpu.nvidia.com"].productName == "NVIDIA RTX A5000"
- name: fallback-t10
设备类名称：gpu.nvidia.com
selectors:
- cel:
表达式：device.attributes["gpu.nvidia.com"].productName == "Tesla T10"
---
apiVersion: apps/v1
kind: Deployment
metadata:
name: first-a5000-deploy
labels:
app: first-a5000-deploy
spec:
replicas: 1
selector:
matchLabels:
app: first-a5000-deploy
template:
metadata:
labels:
app: first-a5000-deploy
spec:
containers:
- name: ctr0
image: ubuntu:24.04
command: ["bash", "-c"]
args: ["nvidia-smi -L; 陷阱 'exit 0' TERM; sleep 9999 & wait"]
resources:
claims:
- name: gpu
resourceClaims:
- name: gpu
resourceClaimTemplateName: first-a5000

```将以上内容保存为 lab02.yaml 并应用：```
kubectl apply -f lab02.yaml
```确认 Pod 正在运行并使用 nvidia-smi -L 输出来验证它是否获得了 A5000：```
kubectl get pod
kubectl 日志部署/first-a5000-deploy --all-pods
名称就绪状态重新开始年龄
first-a5000-deploy-8c6cf4568-2lsv9 1/1 运行 0 9s

[pod/first-a5000-deploy-8c6cf4568-2lsv9/ctr0] GPU 0：NVIDIA RTX A5000（UUID：GPU-e13ce856-7474-797f-d143-16e99b65c0c3）

```现在扩展到 2 个副本以查看新 Pod 获得哪个 GPU：```
kubectl scale deployment first-a5000-deploy --replicas 2
kubectl logs deployments/first-a5000-deploy --all-pods
[pod/first-a5000-deploy-8c6cf4568-2lsv9/ctr0] GPU 0: NVIDIA RTX A5000 (UUID: GPU-e13ce856-7474-797f-d143-16e99b65c0c3)
[pod/first-a5000-deploy-8c6cf4568-865jj/ctr0] GPU 0: Tesla T10 (UUID: GPU-dae084a2-974c-00e2-6dec-4ba1999b8652)

```第一个 Pod 占用了唯一的 A5000，因此第二个 Pod 回退到 T10 — 这正是首选不可用时 firstAvailable 的预期行为。

我们还可以看到对应的ResourceClaims：```
kubectl get resourceclaim
NAME                                           STATE                AGE
First-a5000-deploy-8c6cf4568-2lsv9-gpu-bdz9j 已分配，保留 4m29s
first-a5000-deploy-8c6cf4568-865jj-gpu-mqfcx 已分配，保留 3 分 29 秒

```⚠️ 警告 — 如果我们删除 A5000 Pod，重建的 Pod 会恢复为 A5000 吗？

按照上面的配置，不行，不会回到A5000。 Deployment默认的strategy.type是RollingUpdate；当旧 Pod 正在终止时，其 ResourceClaim 尚未释放。

Deployment 控制器立即从 ResourceClaimTemplate 创建一个新的 Pod 和一个新的 ResourceClaim。由于 A5000 仍由旧 Pod 持有，因此新声明回落至 T10。

最后，清理：```
kubectl delete -f lab02.yaml
```#### 场景 III：具有至少 20 GiB 内存的 GPU

今天，一位工程师想要部署一个需要具有至少 20 GiB 内存的单个 GPU 的法学硕士。由于它仍处于测试阶段，计算要求很灵活——任何满足内存阈值的可用 GPU 都可以。

除了.attributes之外，我们还可以使用.capacity.memory。我们如何表达比较规则？看一下第15行：

lab03.yaml```
apiVersion: resource.k8s.io/v1
kind: ResourceClaimTemplate
metadata:
name: gt20g
spec:
spec:
devices:
requests:
- name: gpu
firstAvailable:
- name: gt20g
设备类名称：gpu.nvidia.com
selectors:
- cel:
表达式：device.capacity["gpu.nvidia.com"].memory.isGreaterThan(quantity("20Gi"))
---
apiVersion: apps/v1
kind: Deployment
metadata:
name: gt20g-deploy
labels:
app: gt20g-deploy
spec:
replicas: 1
selector:
matchLabels:
app: gt20g-deploy
template:
metadata:
labels:
app: gt20g-deploy
spec:
containers:
- name: ctr0
image: ubuntu:24.04
command: ["bash", "-c"]
args: ["nvidia-smi -L; 陷阱 'exit 0' TERM; sleep 9999 & wait"]
resources:
claims:
- name: gpu
resourceClaims:
- name: gpu
resourceClaimTemplateName: gt20g

```我们使用 CEL 的 isGreaterThan(quantity(“20Gi”)) 来要求超过 20 GiB。

应用 YAML：```
kubectl apply -f lab03.yaml
```确认 Pod 正在运行并且我们获得了 A5000：```
kubectl get pod
kubectl 日志部署/gt20g-deploy --all-pods
名称就绪状态重新开始年龄
gt20g-deploy-5ff576476-hdz8f   1/1     Running   0          5m16s

[pod/gt20g-deploy-5ff576476-hdz8f/ctr0] GPU 0：NVIDIA RTX A5000（UUID：GPU-e13ce856-7474-797f-d143-16e99b65c0c3）

```现在让我们看看扩大规模后会发生什么：```
kubectl scale deployment gt20g-deploy --replicas 2
```伸缩完成后，查看是否有新的Pod添加：```
kubectl get pod
名称就绪状态重新开始年龄
gt20g-deploy-5ff576476-hdz8f   1/1     Running   0          8m9s
gt20g-deploy-5ff576476-vjss8   0/1     Pending   0          26s

```在 gt20g-deploy-5ff576476-vjss8 Pod 上运行描述：```
kubectl describe pod gt20g-deploy-5ff576476-vjss8
Events:
Type     Reason            Age   From               Message
----     ------            ----  ----               -------
Warning  FailedScheduling  98s   default-scheduler  0/4 nodes are available: 1 node(s) had untolerated taint(s), 3 cannot allocate all claims. still not schedulable, preemption: 0/4 nodes are available: 4 Preemption is not helpful for scheduling.

```由于集群中没有其他 GPU 具有至少 20 GiB 的内存（T10 只有 16 GiB），因此新 Pod 陷入 Pending 状态。

清理资源：```
kubectl删除-f lab03.yaml
```有关更复杂的匹配逻辑，请参阅 [Kubernetes 中的 CEL](https://kubernetes.io/docs/reference/using-api/cel/)。

#### 场景 IV：DRA 中的 

GPU 时间切片

读者须知：

截至 2026 年 6 月，NVIDIA 官方文档和 NVIDIA DRA 驱动程序 GPU wiki 均不包含任何有关时间切片的教程。

以下配置改编自[demo/specs/quickstart/v1/gpu-test5.yaml](https://github.com/kubernetes-sigs/dra-driver-nvidia-gpu/blob/95e0744565cd23a7cbb2f91c4e401ba50024f927/demo/specs/quickstart/v1/gpu-test5.yaml)，并通过阅读部分源代码进行补充； Feature Gate 部分取自第三方文章。

该设置可能会在未来的版本中发生变化 - 请记住这一点！

今天，一位工程师回来问我：“我知道 DRA 对于资源分配非常有用，但是有没有办法回到时间切片模式？”

想回到旧模式吗？不……根本就是问题！

只需在 .spec.devices.config 下指定设备并将共享策略切换为 TimeSlicing 即可。这是一个例子：

lab04.yaml```
apiVersion: resource.k8s.io/v1
kind: ResourceClaim
metadata:
name: time-slicing-manual
spec:
devices:
requests:
- name: ts-gpu
exactly:
deviceClassName: gpu.nvidia.com
config:
- requests: ["ts-gpu"]
opaque:
driver: gpu.nvidia.com
parameters:
apiVersion: resource.nvidia.com/v1beta1
kind: GpuConfig
sharing:
strategy: TimeSlicing
timeSlicingConfig:
interval: Long
---
apiVersion: apps/v1
kind: Deployment
metadata:
name: ts-gpu-deployment
spec:
replicas: 4
selector:
matchLabels:
app: ts-gpu
template:
metadata:
labels:
app: ts-gpu
spec:
containers:
- name: ctr
image: nvcr.io/nvidia/k8s/cuda-sample:nbody-cuda11.6.0-ubuntu18.04
command: ["bash", "-c"]
args: ["trap 'exit 0' TERM; /tmp/sample --benchmark --numbodies=4226000 & wait"]
resources:
claims:
- name: gpu
resourceClaims:
- name: gpu
resourceClaimName: time-slicing-manual

```将以上内容保存为 lab04.yaml 并应用：```
kubectl apply -f lab04.yaml
```验证所有 Pod 是否正在运行：```
kubectl get pod
NAME                                 READY   STATUS    RESTARTS   AGE
ts-gpu-deployment-549c945798-6t2dx   1/1     Running   0          4s
ts-gpu-deployment-549c945798-tlgp4   1/1     Running   0          4s
ts-gpu-deployment-549c945798-x2gbv   1/1     Running   0          4s
ts-gpu-deployment-549c945798-xbv22   1/1     Running   0          4s

```由于所有 4 个 Pod 共享相同的 ResourceClaim，因此 kubectl get resourceclaim 仅返回一个条目 - 这本身就是它们正在共享的证据：```
kubectl get resourceclaim
NAME                  STATE                AGE
时间分片-手动分配，预留30s

```使用“describe”深入查看，您将看到“预留”下列出的所有 4 个 Pod：```
kubectl describe resourceclaim time-slicing-manual
Status:
Allocation:
Devices:
Config:
Opaque:
Driver:  gpu.nvidia.com
Parameters:
API Version:  resource.nvidia.com/v1beta1
Kind:         GpuConfig
Sharing:
Strategy:  TimeSlicing
Time Slicing Config:
Interval:  Long
Requests:
ts-gpu
Source:  FromClaim
Results:
Device:   gpu-0
Driver:   gpu.nvidia.com
Pool:     capi-dralabs-md-gpua5000-jw4mx-d64jz
Request:  ts-gpu
Node Selector:
Node Selector Terms:
Match Fields:
Key:       metadata.name
Operator:  In
Values:
capi-dralabs-md-gpua5000-jw4mx-d64jz
Reserved For:
Name:      ts-gpu-deployment-549c945798-x2gbv
Resource:  pods
UID:       be21eecf-2d58-4891-9cac-ac3674f4ff09
Name:      ts-gpu-deployment-549c945798-6t2dx
Resource:  pods
UID:       37d504a0-966e-4263-9fcd-b713d73c0e77
Name:      ts-gpu-deployment-549c945798-xbv22
Resource:  pods
UID:       2b5ec297-9889-4cb9-8079-b626a854b292
Name:      ts-gpu-deployment-549c945798-tlgp4
Resource:  pods
UID:       ee836856-8c6b-4161-9582-4bc4ff63a606

```这就是在 DRA 下启用时间切片的方式 - 效果类似于旧设备插件的时间切片模式，只是我们不需要指定要分成多少个切片。我们只需配置 timeSlicingConfig 及其间隔。

最后，清理资源：```
kubectl删除-f lab04.yaml
```总结

与设备插件相比，DRA 现在提供了更清晰的使用模型，使开发人员和集群管理员可以更精确地分配设备。不再需要在同一节点上并置相同类型的设备，也不再需要在nodeSelector或Affinity中编写复杂的规则。

从 K8s v1.36 开始，还提供了设备运行状况报告，因此 Pod 不再简单地显示错误 - 我们可以判断故障是源于设备还是源于应用程序。

以前，当 K8s 集群 CPU 或内存不足时，Cluster Autoscaler 可以启动新机器。未来，同样的情况也可能适用于 GPU 短缺的情况——Cluster Autoscaler 可以按需提供 GPU 节点，从而实现更高效的资源分配。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
