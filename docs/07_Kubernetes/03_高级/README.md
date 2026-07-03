# 高级

> K8s 高级 = **Operator/CRD/kubebuilder + 自定义调度器+扩展(Volcano/Kueue/Yunikorn) + 多集群联邦(Karmada/Clusterset/Submariner) + Service Mesh(Istio/Linkerd/Cilium) + KubeVirt VM 共存 + Cluster API + GPU Operator+MIG+昇腾 + Confidential Containers + GitOps 高级(ArgoCD ApplicationSet/Image Updater/Argo Workflows) + eBPF 可观测(Pixie/Tetragon/DeepFlow) + 大规模调优(etcd/apiserver/CoreDNS) + 国产化平台深度**。本章面向 K8s 平台架构师 / 大规模集群 (500-10000 节点) 工程师。

## 一、CRD + Operator 深度

### 1.1 kubebuilder 工程化

```bash
kubebuilder init --domain example.com --repo github.com/example/mysql-operator
kubebuilder create api --group db --version v1 --kind MySQLCluster
# controller-gen 生成 deepcopy + manifests + CRD
make manifests generate
```

控制器 reconcile 三段式：

```go
func (r *Reconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
  // 1. Get desired state
  cr := &dbv1.MySQLCluster{}
  if err := r.Get(ctx, req.NamespacedName, cr); err != nil { return ctrl.Result{}, client.IgnoreNotFound(err) }
  // 2. Reconcile actual state
  if err := r.ensureStatefulSet(ctx, cr); err != nil { return ctrl.Result{}, err }
  if err := r.ensureService(ctx, cr); err != nil { return ctrl.Result{}, err }
  // 3. Update status
  cr.Status.Ready = true
  return ctrl.Result{RequeueAfter: 30 * time.Second}, r.Status().Update(ctx, cr)
}
```

### 1.2 Operator 主流

```
数据库:      Percona Operator / Bitnami / Crunchy / Zalando PG / KubeBlocks ⭐ (国产)
消息:        Strimzi (Kafka) / RabbitMQ Operator / Pulsar Operator
缓存:        Redis Operator / Memcached Operator
监控:        Prometheus Operator / Grafana Operator
存储:        Rook-Ceph / Longhorn / OpenEBS Operator
机器学习:    Kubeflow / Volcano / Ray / vLLM Production Stack ⭐
平台:        Crossplane (基础设施)
GitOps:      ArgoCD / Flux Operator
```

### 1.3 OperatorHub.io + OLM

```
OLM (Operator Lifecycle Manager): 装 Operator 的 Operator
OperatorHub: 社区库 (类似 Helm Hub)
ClusterServiceVersion (CSV) 是 Operator 的"Helm Chart"等价物
```

## 二、调度扩展

### 2.1 内置调度器扩展点

```
Filter   节点过滤 (能不能放)
Score    节点打分 (放哪个最优)
Bind     绑定 Pod 到节点
Reserve / PreBind / PostBind / PreFilter / PostFilter
```

### 2.2 Volcano（批处理调度）

```bash
helm install volcano volcano-sh/volcano -n volcano-system --create-namespace
```

```yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata: { name: pytorch-train }
spec:
  minAvailable: 4                  # gang scheduling
  schedulerName: volcano
  tasks:
    - name: master
      replicas: 1
      template:
        spec:
          containers:
            - { name: master, image: pytorch:2.4-cuda12.4, resources: { limits: { nvidia.com/gpu: 1 } } }
    - name: worker
      replicas: 3
      template:
        spec:
          containers:
            - { name: worker, image: pytorch:2.4-cuda12.4, resources: { limits: { nvidia.com/gpu: 1 } } }
```

特性：

- **Gang Scheduling**（要么全起，要么不起 → AI 训练必备）
- **Queue + Fair Share**
- **PodGroup**
- **优先级 / 抢占**

### 2.3 Kueue（K8s 官方批处理）

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: ai-team }
spec:
  resourceGroups:
    - coveredResources: [cpu, memory, "nvidia.com/gpu"]
      flavors:
        - name: default
          resources:
            - { name: cpu, nominalQuota: 200 }
            - { name: memory, nominalQuota: 800Gi }
            - { name: "nvidia.com/gpu", nominalQuota: 16 }
```

K8s 1.27+ 官方批处理调度，配 JobSet / PyTorchJob / RayJob。

### 2.4 Apache Yunikorn（CNCF）

大数据 + AI 混合场景，Yarn-like 队列模型。

## 三、多集群联邦

### 3.1 Karmada（国产 CNCF）

```bash
kubectl karmada init
kubectl karmada join member1 --cluster-kubeconfig=member1.kubeconfig
kubectl karmada join member2 --cluster-kubeconfig=member2.kubeconfig
```

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata: { name: web-propagation }
spec:
  resourceSelectors:
    - { apiVersion: apps/v1, kind: Deployment, name: web }
  placement:
    clusterAffinity: { clusterNames: [member1, member2] }
    replicaScheduling:
      replicaSchedulingType: Divided
      replicaDivisionPreference: Weighted
      weightPreference:
        staticWeightList:
          - { targetCluster: { clusterNames: [member1] }, weight: 2 }
          - { targetCluster: { clusterNames: [member2] }, weight: 1 }
```

特点：

- 单控制平面 + 多集群
- 调度 + 故障切换
- Propagation/Override 策略
- 国产 CNCF 毕业项目（华为主导）

### 3.2 其他方案

```
Karmada ⭐                 国产 CNCF, 多集群调度
Open Cluster Management     IBM/Red Hat
Cluster API (CAPI)          K8s 集群即资源
KubeFed (已停滞)
Rancher Fleet               GitOps 多集群
Argo CD ApplicationSet      GitOps 多集群
Submariner                  跨集群 Service 互通
Skupper                     L7 多集群
Istio multicluster          Service Mesh 多集群
```

### 3.3 Cluster API（CAPI）

```bash
clusterctl init --infrastructure openstack
clusterctl generate cluster prod-cluster --kubernetes-version v1.30.0 --control-plane-machine-count 3 --worker-machine-count 5 | kubectl apply -f -
```

把 K8s 集群当 CRD 管，替代 Magnum + Rancher 一部分。

## 四、Service Mesh

### 4.1 大规模选型决策

> 基础 Ingress / Gateway API 概念详见 [02_进阶](../02_进阶/README.md#ingress-gateway)。

大规模（> 500 Pod / 多集群）Service Mesh 选型决策矩阵:

| 决策维度 | Istio Ambient ⭐ | Cilium SM | Linkerd | Higress |
|:---|:---|:---|:---|:---|
| **数据面** | ztunnel + waypoint (无 sidecar) | eBPF + Envoy (无 sidecar) | linkerd-proxy (Rust sidecar) | Envoy sidecar |
| **规模上限** | 10w+ Pod | 10w+ Pod (eBPF) | 2w Pod | 5w Pod |
| **CPU/内存开销** | 省 60-90% vs sidecar | 最低 (eBPF 内核态) | 低 (Rust) | 中 |
| **多集群** | 原生支持 (Multi-primary) | 需 Cluster Mesh | 有限 | 有限 |
| **L7 能力** | 强 (waypoint Envoy) | 中 (Envoy on-demand) | 中 | 强 |
| **mTLS** | ztunnel 自动 | 自动 | 自动 | 自动 |
| **国产化** | 社区 | 社区 | 社区 | 阿里主导 ⭐ |
| **迁移成本** | 高 (Istio 生态) | 中 (替换 CNI) | 低 | 中 |

选型判断:
  - **大规模 + 已有 Istio** → Istio Ambient（去 sidecar，省资源）
  - **极致性能 + Cilium CNI** → Cilium Service Mesh（eBPF 无代理）
  - **中小规模 + 易运维** → Linkerd（Rust 轻量，配置简单）
  - **国产化 / API 网关一体** → Higress（阿里，Istio + Envoy + Nginx）

### 4.2 Istio Ambient（无 sidecar，新主流）

```bash
istioctl install --set profile=ambient

# 给 namespace 启用
kubectl label namespace prod istio.io/dataplane-mode=ambient
```

特点：

- ztunnel (L4) + waypoint proxy (L7)
- 内存 / CPU 比 sidecar 省 60-90%
- 渐进式升级

### 4.3 流量管理

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata: { name: web }
spec:
  hosts: [web.prod.svc.cluster.local]
  http:
    - match: [{ headers: { x-canary: { exact: "true" } } }]
      route: [{ destination: { host: web, subset: v2 } }]
    - route:
        - { destination: { host: web, subset: v1 }, weight: 90 }
        - { destination: { host: web, subset: v2 }, weight: 10 }
---
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata: { name: web }
spec:
  host: web.prod.svc.cluster.local
  subsets:
    - { name: v1, labels: { version: v1 } }
    - { name: v2, labels: { version: v2 } }
  trafficPolicy:
    connectionPool: { tcp: { maxConnections: 100 } }
    outlierDetection: { consecutive5xxErrors: 5, interval: 30s, baseEjectionTime: 30s }
```

### 4.4 mTLS + Auth

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata: { name: default, namespace: prod }
spec: { mtls: { mode: STRICT } }
---
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata: { name: web-only-frontend, namespace: prod }
spec:
  selector: { matchLabels: { app: web } }
  rules:
    - from: [{ source: { namespaces: [frontend] } }]
      to: [{ operation: { methods: [GET] } }]
```

## 五、KubeVirt（K8s 跑 VM）

```bash
export VERSION=v1.4.0
kubectl create -f https://github.com/kubevirt/kubevirt/releases/download/$VERSION/kubevirt-operator.yaml
kubectl create -f https://github.com/kubevirt/kubevirt/releases/download/$VERSION/kubevirt-cr.yaml
```

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata: { name: legacy-vm }
spec:
  running: true
  template:
    spec:
      domain:
        cpu: { cores: 4 }
        memory: { guest: 8Gi }
        devices:
          disks:
            - { name: rootdisk, disk: { bus: virtio } }
          interfaces:
            - { name: default, masquerade: {} }
      networks: [{ name: default, pod: {} }]
      volumes:
        - { name: rootdisk, persistentVolumeClaim: { claimName: vm-disk } }
```

场景：

- VMware 替代 (Harvester / OpenShift Virt)
- 老应用容器化前过渡
- 多租户强隔离 (kata 不够)
- AI 训练 + GPU 直通 (PCI Passthrough)
- 国产化迁移过渡

## 六、GPU 与 AI 调度

### 6.1 NVIDIA GPU Operator

```bash
helm install gpu-operator nvidia/gpu-operator -n gpu-operator --create-namespace \
  --set driver.enabled=true --set toolkit.enabled=true \
  --set mig.strategy=mixed
```

自动装：driver + container toolkit + device plugin + DCGM exporter + MIG manager。

```yaml
# A100 用 MIG 切片
nodeSelector: { nvidia.com/mig-1g.10gb.product: NVIDIA-A100-SXM4-40GB-MIG-1g.10gb }
resources:
  limits: { nvidia.com/mig-1g.10gb: 1 }
```

### 6.2 国产 GPU

```
昇腾 910B / Ascend Operator
摩尔 S4000 / MUSA Operator
沐曦 / 寒武纪 / 燧原 / 天数

部署模式同 NVIDIA：driver + device plugin + exporter
混合调度：HAMi (Heliyon AI Middleware, 国产开源) ⭐
HAMi: 单 K8s 集群混调度 NVIDIA + 昇腾 + 摩尔
```

### 6.3 vLLM Production Stack

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: qwen2-7b }
spec:
  predictor:
    model:
      modelFormat: { name: vllm }
      runtime: kserve-vllmserver
      storageUri: pvc://models/Qwen2-7B-Instruct
    minReplicas: 1
    maxReplicas: 10
```

或直接 vLLM Operator / llm-d (CNCF Sandbox) / Ray Serve。

详见 [11_AI基础设施](../../11_AI基础设施/index.md)。

## 七、Confidential Containers (CoCo)

```bash
kubectl apply -k https://github.com/confidential-containers/operator/config/release?ref=v0.10.0
kubectl apply -k https://github.com/confidential-containers/operator/config/samples/ccruntime/default?ref=v0.10.0
```

RuntimeClass: `kata-cc` (SEV-SNP / TDX / 海光 CSV)。

```yaml
apiVersion: v1
kind: Pod
spec:
  runtimeClassName: kata-cc
  containers: [...]
```

KBS (Key Broker Service) 远程证明 + 加密镜像/Secret 解密 → 见 [06_Docker/03_高级](../../06_Docker/03_高级/README.md)。

## 八、GitOps 高级

### 8.1 ArgoCD ApplicationSet + Image Updater

```yaml
# 自动跟踪镜像 tag (基于 SemVer / Latest / digest)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web
  annotations:
    argocd-image-updater.argoproj.io/image-list: nginx=harbor.example.com/web/nginx
    argocd-image-updater.argoproj.io/nginx.update-strategy: semver
    argocd-image-updater.argoproj.io/nginx.allow-tags: regexp:^v1\.[0-9]+\.[0-9]+$
spec: ...
```

### 8.2 Progressive Delivery (Argo Rollouts / Flagger)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: web }
spec:
  replicas: 5
  strategy:
    canary:
      canaryService: web-canary
      stableService: web
      trafficRouting: { istio: { virtualService: { name: web, routes: [primary] } } }
      steps:
        - setWeight: 10
        - pause: { duration: 5m }
        - analysis:
            templates: [{ templateName: success-rate }]
        - setWeight: 50
        - pause: { duration: 10m }
```

`AnalysisTemplate` 接 Prometheus 自动判断成功率，失败自动回滚。

### 8.3 Argo Workflows / Argo Events

DAG + 事件驱动批处理 + AI 训练 pipeline。

## 九、eBPF 可观测

### 9.1 Cilium Hubble（默认）

```bash
helm upgrade cilium cilium/cilium --set hubble.relay.enabled=true --set hubble.ui.enabled=true
hubble observe --namespace prod
hubble observe --from-pod prod/web --to-pod prod/db --type drop
```

### 9.2 Tetragon（容器安全）

```bash
helm install tetragon cilium/tetragon -n kube-system

# 检测容器内 shell
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata: { name: monitor-exec }
spec:
  kprobes:
    - call: "__x64_sys_execve"
      syscall: true
      ...
```

### 9.3 DeepFlow（国产 eBPF APM）

```bash
helm install deepflow deepflow/deepflow -n deepflow --create-namespace
```

零代码全栈 APM：网络 + 应用 + DB + 中间件 + K8s + 业务全自动采集。

### 9.4 Pixie / Inspektor Gadget

```bash
# Pixie (CNCF, eBPF + Pixie Cloud)
px deploy

# Inspektor Gadget (eBPF 工具集)
kubectl gadget run trace_exec -A
```

## 十、大规模调优

### 10.1 etcd

```
☐ 单独物理机 / NVMe SSD
☐ 写延迟 < 50ms / 99 分位
☐ 大集群 5 副本 (不是 3)
☐ etcd defrag 月度
☐ alarm DISARM 监控
☐ snapshot 每日 + 异地
☐ --quota-backend-bytes 设 8GB
☐ etcd 跟 apiserver 分离
☐ 大集群拆 events 到独立 etcd
```

```bash
# 大集群关键
--quota-backend-bytes=8589934592
--max-request-bytes=33554432
--snapshot-count=10000
```

### 10.2 apiserver

```
☐ 多副本 + LB
☐ --max-requests-inflight=3000
☐ --max-mutating-requests-inflight=1000
☐ --watch-cache-sizes=services#1000,endpoints#1000
☐ --enable-priority-and-fairness (APF) 防雪崩
☐ Audit log 异步 + 滚动
☐ 大资源 (Endpoints/EndpointSlices) 必开启 EndpointSlices
☐ CRD scope/select 设计：避免大对象
```

### 10.3 CoreDNS

```
☐ NodeLocal DNSCache (每节点缓存)
☐ ndots:2 (减少补全)
☐ 复制扩容 + 节点亲和
☐ 大集群拆多 CoreDNS 实例 / 多 zone
☐ Cache TTL ↑
☐ autopath plugin
```

### 10.4 调度器 / kubelet

```
kubelet:
  --node-status-update-frequency=10s
  --kube-api-qps=50 --kube-api-burst=100
  --serialize-image-pulls=false (并行拉镜像)
  --max-pods=250
  --image-gc-high-threshold=85
  
scheduler:
  --kube-api-qps=100 --kube-api-burst=200
  分批调度 / Volcano / Kueue
```

### 10.5 节点

```
☐ /var/lib/* 独立 SSD
☐ /var/log 独立分区
☐ 内核 5.15+ (cgroup v2 / eBPF)
☐ sysctl 调优 (net.core / fs.inotify)
☐ ulimit nofile 1M+
☐ CPU Manager static policy (NUMA / 实时业务)
☐ Topology Manager
```

### 10.6 1000+ 节点经验

```
- 拆 region/zone 多集群比单集群上 5000 节点更稳
- Karmada 联邦比超大单集群好运维
- 单 namespace pod 数 < 30k
- Service / Endpoints 用 EndpointSlices
- 大量 watch 用 Informer + reflector
```

## 十一、平台工程（Backstage 等）

```
Backstage (Spotify) ⭐    开发者门户
Port                     SaaS IDP
KubeSphere ⭐            国产平台 (DevOps + 多集群 + 多租户)
Rancher                  多集群管理 + 商店
Crossplane               基础设施 IaC + Composition
```

## 十二、国产化平台深度

### 12.1 KubeSphere

```
功能矩阵:
☐ 多集群管理
☐ 多租户 (workspace/project/role)
☐ DevOps (Jenkins/Tekton/ArgoCD)
☐ 应用商店
☐ 监控 / 日志 / 告警全栈
☐ Service Mesh (Istio)
☐ 边缘计算 (KubeEdge)
☐ 信创 (鲲鹏/飞腾/海光)
☐ 国密 TLS

部署:
kk create cluster --with-kubernetes v1.30.0 --with-kubesphere v3.4.1
```

### 12.2 华为云 CCE / CCE-Turbo / Stack

```
- VPC 集成 (ENI / Trunkport)
- 鲲鹏 ARM64 节点池
- ASCEND GPU 调度
- 信创全栈
- CCE-Turbo 容器网络性能 SR-IOV
```

### 12.3 阿里云 ACK / Lingjun

```
- ACK Pro / Edge / Serverless
- Lingjun (灵骏) AI 训练集群
- Sealos / Higress 国产开源
- ARM64 倚天 710
```

### 12.4 国产开源

```
KubeSphere ⭐
Sealos                    集群 / Cloud OS
KubeBlocks                数据库 Operator
OpenKruise                增强工作负载
Karmada                   多集群联邦
Volcano                   批处理
Higress                   Gateway
Spiderpool                IPAM
kube-ovn                  CNI (基于 OVN)
HwameiStor                本地存储
HAMi                      多 GPU 混调度
Kruise Rollout            渐进发布
KubeEdge / OpenYurt       云边协同
```

## 十三、典型坑（高级）

| 坑 | 建议 |
|:---|:---|
| **etcd 跑虚拟机 / 共享盘** | 必物理 + NVMe |
| **CRD 用大 spec 当 DB** | 限制 < 1MB / 必拆 Status |
| **Controller 全量 List** | 用 Informer Indexer |
| **Operator reconcile 死循环** | requeueAfter + 限速 |
| **Istio sidecar 内存 100MB×N** | 切 Ambient |
| **Karmada 集群多到 50+** | 拆 hub 多副本 / 分层 |
| **GPU MIG 没规划 profile** | 启动 mig.strategy=mixed |
| **HAMi 用错虚拟模式** | 看驱动兼容 |
| **多集群联邦 RBAC 复杂** | OPA + 统一 SSO |
| **Service Mesh 没限流** | EnvoyFilter + ratelimit |
| **CoCo 加密镜像启动慢** | KBS 接 HA + 预热 |
| **Volcano Job 全卡死** | minAvailable 写错 |
| **平台 Backstage 没接 Catalog** | Catalog Discovery 必装 |

## 十四、高级 Checklist

```
Operator:
☐ kubebuilder 工程化
☐ KubeBlocks / Strimzi / Prometheus Op 主流
☐ OperatorHub / OLM
☐ 自研 Operator 团队规范

调度:
☐ Volcano / Kueue / Yunikorn 一种
☐ 自定义调度器 (gang / fair / topo)
☐ HAMi 多卡混调度

多集群:
☐ Karmada / OCM / CAPI 一种
☐ Submariner / Istio Multicluster 互通

Service Mesh:
☐ Istio (sidecar 或 Ambient) / Linkerd / Cilium SM
☐ mTLS + AuthZ + 限流 + 熔断
☐ Higress 一种国产

VM:
☐ KubeVirt 部署 + GPU 直通
☐ Harvester / OpenShift Virt 试点

GPU/AI:
☐ NVIDIA GPU Operator + MIG
☐ 国产 GPU (昇腾 / 摩尔) 一种
☐ HAMi 混调度
☐ vLLM Production Stack / llm-d / KServe

CoCo:
☐ SEV-SNP / TDX / 海光 CSV
☐ KBS 集成

GitOps:
☐ ApplicationSet + Image Updater
☐ Argo Rollouts (Canary + AnalysisTemplate)
☐ Argo Workflows (训练 pipeline)

eBPF:
☐ Hubble (Cilium)
☐ Tetragon / Falco
☐ DeepFlow / Pixie

调优:
☐ etcd NVMe + defrag
☐ APF + Audit + EndpointSlices
☐ CoreDNS NodeLocal + ndots
☐ kubelet 并发 + maxPods
☐ 拆多集群 Karmada 联邦

平台:
☐ KubeSphere / Backstage / Rancher 一种
☐ Crossplane / Cluster API

国产化:
☐ KubeSphere / 华为 CCE / 阿里 ACK / 腾讯 TKE
☐ 鲲鹏/飞腾/海光节点池
☐ 昇腾 GPU 调度
☐ kube-ovn / Spiderpool / HwameiStor / HAMi
☐ Higress / APISIX 国产 Gateway
```

## 十五、推荐栈

```
Operator 框架: kubebuilder ⭐ / OperatorSDK / KOPF
平台:        KubeSphere ⭐ / Backstage / Rancher
调度:        Volcano ⭐ / Kueue / Yunikorn + HAMi (多 GPU)
多集群:      Karmada ⭐ / Cluster API / Submariner
Mesh:        Istio Ambient ⭐ / Cilium SM / Linkerd / Higress
VM:          KubeVirt + Harvester
GPU:        NVIDIA GPU Operator + MIG + HAMi (混卡) + 昇腾
CoCo:        Confidential Containers + SEV-SNP/TDX/海光 CSV
GitOps:      ArgoCD ApplicationSet + Image Updater + Argo Rollouts/Workflows
eBPF:        Cilium Hubble + Tetragon + DeepFlow ⭐
基础设施:    Crossplane + Cluster API
国产开源:    KubeSphere + Sealos + KubeBlocks + Karmada + OpenKruise + Higress + HAMi + kube-ovn
```

> 📖 **核心判断**：K8s 高级 = **Operator/CRD + 调度扩展(Volcano/Kueue) + 多集群(Karmada/CAPI) + Service Mesh(Istio Ambient) + KubeVirt VM + GPU/MIG + HAMi 混卡 + CoCo + GitOps 高级 + eBPF 可观测 + 大规模调优 + 国产化平台**。能写 Operator + 用 Karmada 联邦 5+ 集群 + Istio Ambient 全栈 mTLS + Volcano/HAMi 调度 1000 GPU + KubeSphere 多租户 + DeepFlow eBPF 全栈观测，就具备 K8s 平台架构师能力。
