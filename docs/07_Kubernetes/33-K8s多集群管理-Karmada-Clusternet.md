# Kubernetes 多集群管理（Karmada / Clusternet）

> 集群越建越多，怎么管？多集群的本质是「跨集群的资源分发、服务发现、流量治理和故障转移」。本文覆盖 Karmada、Clusternet 两大主流多集群框架，从架构原理、安装部署、联邦调度、服务治理、灾备到选型对比，一站讲透。

---

## 一、多集群为什么难？选型总览

### 1.1 典型痛点

| 痛点 | 具体表现 | 后果 |
|:---|:---|:---|
| 集群分散 | 生产/测试/灾备/边缘各自独立，kubectl 来回切 | 配置漂移、人肉重复部署 |
| 应用分发 | 一个应用要在 10 个集群各跑一份 | 手工部署慢、易出错、版本不一致 |
| 流量调度 | 用户就近接入 / 跨集群灰度 | 业务侧自己做 DNS 轮询，不可控 |
| 灾备切换 | 主集群挂了怎么切到备集群 | RTO 长、数据/流量切换全人工 |
| 资源池化 | 多个集群算一份算力，按负载自动调度 | 资源孤岛、利用率不均 |
| 治理分散 | 策略（安全、配额、网络）各集群各配一套 | 合规难审计、策略不同步 |
| 观测割裂 | 每个集群独立 Prometheus/Grafana | 排查问题要切好几个面板 |

### 1.2 多集群架构模式

```text
多集群架构演进路径:

  模式 1: 完全孤岛 (现状, 90% 团队起点)
  ┌──────┐  ┌──────┐  ┌──────┐
  │集群A │  │集群B │  │集群C │
  │ 各管各│  │ 各管各│  │ 各管各│ ← 独立 kubectl / Helm / CI
  └───┬──┘  └───┬──┘  └───┬──┘
      └──────────┼──────────┘
                 ▼
             手工 / 脚本

  模式 2: Hub-Spoke 联邦 (主流)
  ┌─────────── 控制平面 (Host Cluster) ───────────┐
  │  karmada-apiserver / clusternet-hub            │
  │  统一 API, 统一调度, 统一策略                    │
  └────┬──────────┬──────────┬──────────┬──────────┘
       ▼          ▼          ▼          ▼
     ┌────┐     ┌────┐     ┌────┐     ┌────┐
     │成员1│     │成员2│     │成员3│     │成员N│  ← 业务集群
     └────┘     └────┘     └────┘     └────┘

  模式 3: 扁平对等 (Flat)
  ┌────┐ ← 联邦 → ┌────┐ ← 联邦 → ┌────┐
  │集群1│          │集群2│          │集群3│  ← 无中心, 两两联邦
  └────┘          └────┘          └────┘
  (典型: 旧联邦 v1, service mesh 联邦)

  模式 4: 层级联邦 (Hierarchical)
  ┌────────── 大区 Hub ──────────┐
  │      华东 Hub / 华南 Hub     │
  └───────┬───────────┬──────────┘
          ▼           ▼
        ┌─┬─┐       ┌─┬─┐
        集群...       集群...  ← 两级或多级 Hub
```

**主流选型一览**：

| 方案 | 所属 | 架构模式 | 核心定位 | 成熟度 |
|:---|:---|:---|:---|:---|
| Karmada | CNCF Sandbox → Incubating | Hub-Spoke | K8s 原生 API 联邦编排 | 高 (字节/华为背书) |
| Clusternet | CNCF Sandbox | Hub-Spoke | 应用编排 + 应用市场 | 中 (腾讯开源) |
| Kubernetes Federation v2 | 社区已停止 | Hub-Spoke | 早期联邦 | 低 (已归档) |
| OCM (Open Cluster Management) | CNCf Sandbox | Hub-Spoke | 集群生命周期 + 策略 | 中 (IBM/Red Hat) |
| Argo CD ApplicationSet + Generator | Argo 生态 | 扁平 (GitOps) | GitOps 式多集群分发 | 高 |
| Rancher Fleet | SUSE/Rancher | Hub-Spoke | 边缘 + Fleet GitOps | 中 |
| Anthos Multi-cluster | Google | Hub-Spoke | 商用混合云 | 高 (付费) |

### 1.3 场景推荐

| 场景 | 首选 | 备选 | 原因 |
|:---|:---|:---|:---|
| 多集群统一应用分发 (K8s 原生 API) | **Karmada** | OCM | PropagationPolicy 原生, 社区最活跃 |
| 多集群 + 应用市场 + Helm 治理 | **Clusternet** | Karmada + Chart Museum | AppStore 内置, Helm 原生 |
| GitOps 纯声明式多集群 | Argo CD + ApplicationSet | Karmada + Flux | Git 是唯一真相源 |
| 边缘海量小集群 (1000+) | KubeEdge / K3s + Fleet | Clusternet | 边缘资源受限 |
| 企业级混合云 + 策略治理 | OCM | Anthos | Red Hat 背书, 策略完善 |
| 服务网格多集群 | Istio multi-cluster | Linkerd + Gateway API | 服务层治理, 非资源分发 |

---

## 二、Karmada

### 2.1 架构原理

Karmada 是 Kubernetes 多集群编排引擎,**API 完全兼容 K8s 原生**,核心概念是「在管控面声明资源 → 按调度策略分发到成员集群 → 收集运行状态」。

```text
Karmada 架构 (Hub-Spoke):

┌─────── 管控面 Karmada Control Plane ───────────────────────────┐
│                                                                  │
│  ┌──────────────────────────┐      ┌─────────────────────┐     │
│  │    karmada-apiserver     │      │  karmada-scheduler   │     │
│  │   (基于 K8s apiserver)   │◄────►│   联邦调度器         │     │
│  │   原生 K8s API + CRD     │      │  - 集群亲和          │     │
│  │   PropagationPolicy /    │      │  - 集群污点/容忍     │     │
│  │   OverridePolicy /       │      │  - 资源划分           │     │
│  │   ResourceBinding / ...  │      │  - 副本弹性          │     │
│  └───────────┬──────────────┘      └─────────────────────┘     │
│              │                                                   │
│  ┌───────────▼──────────────┐      ┌─────────────────────┐     │
│  │   karmada-controller     │      │ karmada-webhook      │     │
│  │   - 管理器               │      │ - 准入校验 / 突变      │     │
│  │   - 资源绑定控制器        │      │                       │     │
│  │   - 状态聚合控制器        │      │                       │     │
│  └───────────┬──────────────┘      └─────────────────────┘     │
└──────────────┼──────────────────────────────────────────────────┘
               │ kubeconfig / 服务账户
        ┌──────┼──────┬──────────┐
        ▼      ▼      ▼          ▼
      ┌────┐ ┌────┐ ┌────┐     ┌────┐
      │member│ │member│ │member│ ... │member│   ← 成员集群 (业务跑在这里)
      │ 1  │ │  2  │ │  3  │     │ N  │
      └────┘ └────┘ └────┘     └────┘
```

**核心 CRD**：

| CRD | 作用 | 类比单集群的 |
|:---|:---|:---|
| `PropagationPolicy (PP)` | 资源怎么分发: 发到哪、发多少、冲突策略 | 调度策略 + 资源对象 |
| `ClusterPropagationPolicy (CPP)` | 集群级 PP (跨命名空间全局生效) | ClusterRole 级别 |
| `ResourceBinding (RB)` | PP 计算后生成的实际绑定关系 (调度结果) | Binding |
| `ClusterResourceBinding (CRB)` | 集群级 RB | - |
| `OverridePolicy (OP)` | 跨集群差异化覆盖 (镜像/tag/副本数等) | 补丁 |
| `ClusterOverridePolicy (COP)` | 集群级 OP | - |
| `Cluster` | 注册的成员集群对象 | Node (集群粒度) |
| `Work` | 下发到成员集群的实际资源清单 | Pod (最终要跑的) |

### 2.2 安装部署

**前置条件**:
- 一个 K8s 集群作为管控面(host cluster),版本 ≥ 1.22
- Helm 3 / kubectl
- 成员集群若干 (至少 1 个,可与管控面复用同一集群做测试)

**方式一: Helm 安装(推荐)**

```bash
# 添加 Helm 仓库
helm repo add karmada https://raw.githubusercontent.com/karmada-io/karmada/master/charts
helm repo update

# 安装 karmada 管控面
kubectl create namespace karmada-system
helm install karmada karmada/karmada \
  --namespace karmada-system \
  --set hostCluster=host-cluster \
  --set karmada-apiserver.service.type=NodePort

# 验证
kubectl get pods -n karmada-system
# NAME                                       READY   STATUS
# karmada-apiserver-0                        1/1     Running
# karmada-controller-manager-xxxxxx-yyyyy    1/1     Running
# karmada-scheduler-xxxxxx-yyyyy             1/1     Running
# karmada-webhook-xxxxxx-yyyyy               1/1     Running
```

**方式二: karmadactl (命令行工具)**

```bash
# 下载 karmadactl
curl -sL https://github.com/karmada-io/karmada/releases/download/v1.8.0/karmadactl-linux-amd64.tgz | tar -xz
install karmadactl /usr/local/bin/

# 在已存在的集群上初始化管控面
karmadactl init --kubeconfig=$HOME/.kube/config

# 验证
karmadactl version
```

**注册成员集群**：

```bash
# 方式 1: push 模式 (管控面主动连成员集群, 最常用)
# 在管控面执行, 指向成员集群的 kubeconfig
karmadactl add \
  --cluster-context member1 \
  --cluster-kubeconfig ~/.kube/member1.kubeconfig \
  --name member1

# 方式 2: pull 模式 (成员集群主动连管控面, 适合边缘/防火墙后)
# 在管控面生成 join 命令
karmadactl token create --print-register-command

# 在成员集群上执行上面输出的 join 命令
# karmadactl register <管控面地址> --token <token> --name edge1

# 查看已注册集群
kubectl get clusters
# NAME      VERSION   MODE    READY   AGE
# member1   v1.29.2   Push    True    5m
# member2   v1.28.7   Push    True    2m
```

### 2.3 资源分发入门

**场景**：把一个 Nginx Deployment + Service 同时分发到 member1 和 member2 两个集群。

```yaml
# deployment.yaml  —— 原生 K8s 资源, 不需要改任何字段
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  namespace: demo
  labels:
    app: nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-svc
  namespace: demo
spec:
  selector:
    app: nginx
  ports:
    - port: 80
      targetPort: 80
```

```yaml
# policy.yaml  —— Karmada 分发策略
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: nginx-pp
  namespace: demo
spec:
  # 选择要分发的资源 (和 Deployment/Service 同命名空间)
  resourceSelectors:
    - apiVersion: apps/v1
      kind: Deployment
      name: nginx
    - apiVersion: v1
      kind: Service
      name: nginx-svc

  # 分发策略
  placement:
    # 静态集群列表
    clusterAffinity:
      clusterNames:
        - member1
        - member2

    # 副本策略: 按集群平分 / 指定每个集群的副本数
    replicaScheduling:
      # replicaDivisionPreference: Divided   # Divided = 各集群分摊 (默认)
      # replicaDivisionPreference: Duplicated  # Duplicated = 每个集群都全量副本
      replicaDivisionPreference: Divided
      schedulingMode: Divided            # Divided (调度器决定比例) / 下面可显式指定
      # weightPreference:                 # 按权重分摊
      #   staticWeightList:
      #     - targetCluster:
      #         clusterNames: [member1]
      #       weight: 2
      #     - targetCluster:
      #         clusterNames: [member2]
      #       weight: 1
```

```bash
# 应用到 Karmada 管控面
kubectl apply -f deployment.yaml
kubectl apply -f policy.yaml

# 查看 ResourceBinding (调度结果)
kubectl get resourcebinding -n demo
# NAME           SCHEDULED   REPLICAS   AGE
# nginx-deploy   True        2/2        10s

# 查看各成员集群上的实际状态
karmadactl get deployment nginx -n demo -C member1
karmadactl get deployment nginx -n demo -C member2
# 或: kubectl --context member1 get deploy -n demo
```

> **关键心智**：资源定义(Deployment/Service)是**标准 K8s 资源**,分发策略(PropagationPolicy)是**额外的策略对象**。两者通过同命名空间 + resourceSelectors 关联。Karmada 不要求改业务 YAML,这是它最大的优势。

### 2.4 集群亲和与动态调度

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: ClusterPropagationPolicy
metadata:
  name: by-region
spec:
  resourceSelectors:
    - apiVersion: apps/v1
      kind: Deployment
  placement:
    clusterAffinity:
      # 按标签选择集群, 而不是写死名称
      labelSelector:
        matchLabels:
          region: east-china
          env: prod
        # matchExpressions 也支持

      # 污点与容忍 (和 node taint/toleration 同构)
      # tolerations:
      #   - key: dedicated
      #     operator: Equal
      #     value: finance
      #     effect: NoSchedule

      # 集群字段选择器
      # fieldSelector:
      #   - matchExpressions:
      #       - key: status.ready
      #         operator: Equals
      #         value: "True"

    # 集群拓扑约束: 跨可用区分布
    spreadConstraints:
      - spreadByField: cluster
        maxGroups: 3
        minGroups: 2
```

**副本调度模式**：

| 模式 | 含义 | 适用场景 |
|:---|:---|:---|
| `Duplicated` | 每个集群部署完整副本数 | 高可用/多活, 每个集群都独立承载全量 |
| `Divided` | 各集群分摊副本数 | 资源池化 / 跨集群扩容 |
| `Divided + weight` | 按权重比例分摊 | 容量不均的集群池 |
| `Divided + aggregation` | 总数聚合回管控面 | 统一对外显示总副本数 |

### 2.5 差异化覆盖：OverridePolicy

同一个 Deployment 在不同集群经常有差异(镜像仓库地址、副本数、资源限制、环境变量)。OverridePolicy 负责打补丁。

```yaml
# member1 集群: 镜像走 Harbor 内网 + 副本数 3 + 增加 CPU 限制
apiVersion: policy.karmada.io/v1alpha1
kind: OverridePolicy
metadata:
  name: member1-override
  namespace: demo
spec:
  # 覆盖哪些资源
  resourceSelectors:
    - apiVersion: apps/v1
      kind: Deployment
      name: nginx
  # 目标集群
  overrideRules:
    - targetCluster:
        clusterNames:
          - member1
      # 过了就应用下面的 overriders
      overriders:
        # 镜像替换
        imageOverrider:
          - component: Repository
            operator: Replace
            value: harbor.internal.example.com/library/nginx
          - component: Tag
            operator: Replace
            value: 1.25-internal

        # 纯文本 patch (最灵活, 支持任意字段)
        plaintext:
          - path: /spec/replicas
            operator: replace
            value: 3

        # JSON 补丁 (RFC 6902)
        jsonpatch:
          - op: add
            path: /spec/template/spec/containers/0/resources
            value:
              limits:
                cpu: "500m"
                memory: "256Mi"
              requests:
                cpu: "100m"
                memory: "128Mi"

          - op: add
            path: /spec/template/spec/containers/0/env/-
            value:
              name: CLUSTER_NAME
              value: member1

        # 命令与参数补丁
        commandArgsOverrider:
          - containerName: nginx
            operator: add
            value:
              - "-g"
              - "daemon off;"
```

```bash
# 验证: 查看 member1 上的实际 Deployment 字段
karmadactl get deployment nginx -n demo -C member1 -o yaml | grep -E 'replicas:|image:'
```

> **应用顺序**: 默认 OverridePolicy 先于 Work 下发时应用,可以叠加多个 OP,按优先级排序(`spec.priority` 字段,数字越大越晚生效)。

### 2.6 多集群服务治理

**多集群 Service (ServiceExport / ServiceImport)**:

```text
多集群服务调用:
  集群 member1 的 client 想访问 member2 的 backend-svc
  传统: 走公网 LB / 内部 DNS
  Karmada: ServiceExport + ServiceImport + MCS (Multi-cluster Service)

  member1:                        member2:
  ┌──────────────┐               ┌──────────────┐
  │ client-pod   │  mcs-dns      │ backend-svc  │
  │              │ ────────────► │  (ServiceExport) │
  │              │  backend.default.svc.clusterset.local
  └──────────────┘               └──────────────┘
```

```yaml
# 在 backend 所在集群导出服务 (在 Karmada 管控面声明)
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: backend-export-pp
  namespace: demo
spec:
  resourceSelectors:
    - apiVersion: v1
      kind: Service
      name: backend
  placement:
    clusterAffinity:
      clusterNames: [member2]
---
# 导出服务到联邦
apiVersion: multicluster.x-k8s.io/v1alpha1
kind: ServiceExport
metadata:
  name: backend
  namespace: demo
spec: {}
---
# 在 member1 导入服务
apiVersion: multicluster.x-k8s.io/v1alpha1
kind: ServiceImport
metadata:
  name: backend
  namespace: demo
spec:
  type: ClusterSetIP
  ips: []
  ports:
    - name: http
      port: 80
      protocol: TCP
```

**跨集群 DNS 域名**: `服务名.命名空间.svc.clusterset.local`

```bash
# 在 member1 上的 pod 里可以直接解析:
nslookup backend.demo.svc.clusterset.local
# 返回 member2 上 backend 服务的 ClusterIP (通过 mcs-controller 同步)
```

**流量治理进阶**：Karmada 本身**不做 L7 流量治理**,灰度/熔断/限流建议配合服务网格(Istio/Kuma)的多集群模式。Karmada 负责资源分发,Istio 负责服务层流量治理,职责分离。

### 2.7 弹性伸缩：多集群 HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nginx-hpa
  namespace: demo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
---
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: nginx-hpa-pp
  namespace: demo
spec:
  resourceSelectors:
    - apiVersion: autoscaling/v2
      kind: HorizontalPodAutoscaler
      name: nginx-hpa
  placement:
    clusterAffinity:
      clusterNames: [member1, member2]
  # HPA 的副本在各集群独立伸缩
```

> 多集群弹性的两种思路:
> - **分散伸缩**: 每个集群独立 HPA,本地扩本地缩 (默认,最稳定)
> - **全局弹性**: 管控面聚合全局指标,统一下发副本数 (需要全局指标 + 自定义调度器)

### 2.8 状态收集与聚合

```bash
# karmadactl 聚合多集群输出
karmadactl get pods -n demo -C member1,member2
karmadactl top nodes -C member1,member2

# 查看资源分发状态
kubectl get resourcebinding nginx-deploy -n demo -o yaml | \
  yq '.status.aggregatedStatus'

# 查看 Work 对象 (实际下发到集群的内容)
kubectl get works -n karmada-es-member1
# (每个成员集群有一个 karmada-es-<name> 的执行空间)
```

### 2.9 Karmada 常用命令速览

```bash
# 集群管理
karmadactl add --cluster-context ctx1 --name member1        # 注册集群 (push)
karmadactl token create --print-register-command            # pull 模式 token
karmadactl deatch member1                                    # 脱离集群
kubectl get clusters                                        # 查看集群列表
kubectl describe cluster member1                            # 集群详情/状态

# 资源查看
karmadactl get deploy -n demo                               # 所有集群聚合
karmadactl get deploy -n demo -C member1                    # 指定集群
karmadactl describe pod xxx -n demo -C member1              # 描述

# 策略调试
kubectl get resourcebindings -A                             # 调度结果
kubectl get works -A                                        # 实际下发
kubectl get propagationpolicies -A                          # 分发策略
karmadactl interpret --resource deploy/nginx -n demo        # 解释资源

# 故障排查
karmadactl taint clusters member1 dedicated=test:NoSchedule
kubectl logs -n karmada-system deploy/karmada-scheduler     # 调度器日志
kubectl logs -n karmada-system deploy/karmada-controller-manager
```

---

## 三、Clusternet

### 3.1 架构原理

Clusternet 是腾讯开源的多集群应用治理平台,定位是「K8s 多集群的 App Store」,强调**应用市场 + Helm 原生 + 轻量化 agent**。

```text
Clusternet 架构 (Hub-Spoke, pull 为主):

┌──────────── 父集群 (Hub / Parent Cluster) ────────────────┐
│                                                             │
│  ┌──────────────────┐   ┌──────────────────────────────┐   │
│  │clusternet-hub    │   │ 应用市场 / App Store          │   │
│  │  - 集群管理      │   │  - Helm Chart 仓库            │   │
│  │  - 调度/分发     │   │  - 应用模板 / 版本管理         │   │
│  │  - 状态同步      │   │  - 一键安装/升级/回滚          │   │
│  └─────────┬────────┘   └───────────────┬──────────────┘   │
│            │                            │                  │
│  ┌─────────▼────────┐   ┌───────────────▼──────────────┐   │
│  │  CRD 资源         │   │  Subscription (订阅)          │   │
│  │  ManagedCluster   │   │    + Base (基资源)            │   │
│  │  Description      │   │    + Override (差异化)        │   │
│  │  Helmet / ...     │   │    + HelmChart / Description  │   │
│  └──────────────────┘   └──────────────────────────────┘   │
└─────────────┬──────────────────────────────────────────────┘
              │  HTTPS (Websocket / TLS, 子集群主动连父集群)
   ┌──────────┼──────────┬──────────────┐
   ▼          ▼          ▼              ▼
 ┌─────┐   ┌─────┐   ┌─────┐        ┌─────┐
 │子集群│   │子集群│   │子集群│  ...   │边缘集群│   ← 子集群 (业务集群)
 │  1  │   │  2  │   │  3  │        │  N  │
 └─────┘   └─────┘   └─────┘        └─────┘
   ▲
   │ clusternet-agent (以 DaemonSet / Deployment 跑在子集群)
```

**核心 CRD**：

| CRD | 作用 | 类比 Karmada 的 |
|:---|:---|:---|
| `ManagedCluster` | 已注册的子集群对象 | Cluster |
| `Base` | 要分发的基础资源清单 (一组 YAML) | 原生资源 + PropagationPolicy |
| `Subscription` | 订阅 (把 Base 推到哪些集群) | PropagationPolicy |
| `Localization` | 本地差异化覆盖 (子集群侧) | OverridePolicy |
| `Globalization` | 全局差异化覆盖 (父集群侧) | ClusterOverridePolicy |
| `HelmChart` | Helm Chart 类型的基资源 | - (Karmada 用 Flux HelmRelease) |
| `Description` | 描述资源 (可观测、应用视图) | - |
| `HelmRelease` | Chart 部署状态 | - |

**关键设计差异 (vs Karmada)**:

| 维度 | Karmada | Clusternet |
|:---|:---|:---|
| 连接方向 | 默认 push (管控面连成员) | 默认 pull (agent 主动连 hub) |
| 模型 | 原生 K8s API + 策略对象分离 | Base + Subscription + Localization 三层 |
| Helm 支持 | 需配合 Flux / 手动 | 内置 HelmChart / HelmRelease |
| 应用市场 | 无 (需自建) | 内置 App Store |
| 边缘场景 | 支持 pull 模式 | 原生 pull, 天然适合边缘 |
| 调度 | 成熟的联邦调度器 | 标签选择器为主 |
| 多集群服务 | MCS (K8s 标准) | 内置多集群 DNS / 服务发现 |

### 3.2 安装部署

**安装 Hub (父集群)**：

```bash
# Helm 安装
helm repo add clusternet https://clusternet.github.io/charts
helm repo update

kubectl create namespace clusternet-system
helm install clusternet-hub clusternet/clusternet-hub \
  --namespace clusternet-system \
  --set replicaCount=1

# 验证
kubectl get pods -n clusternet-system
# NAME                                    READY   STATUS
# clusternet-hub-xxxxxxxxxx-yyyyy        1/1     Running
# clusternet-scheduler-xxxxxxxxx-yyyyy   1/1     Running
```

**安装子集群 Agent**：

```bash
# 在父集群生成子集群注册 token
kubectl create serviceaccount child1 -n clusternet-system
kubectl create clusterrolebinding child1 --clusterrole=clusternet-cluster-admin --serviceaccount=clusternet-system:child1

# 获取 token (子集群用这个 token 连 hub)
kubectl -n clusternet-system create token child1 > /tmp/child1-token
# 获取 hub 的 API server 地址
HUB_URL=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')

# 在子集群上安装 agent
helm install clusternet-agent clusternet/clusternet-agent \
  --namespace clusternet-system --create-namespace \
  --set parentURL=$HUB_URL \
  --set parentToken=$(cat /tmp/child1-token) \
  --set clusterName=child1 \
  --set clusterNamespace=clusternet-xxx   # 子集群在父集群的命名空间

# 验证 (在父集群查看)
kubectl get managedclusters
# NAME      STATUS    AGE
# child1    Active    2m
```

**一键安装(开发测试用)**:
```bash
# 用官方 install.sh 一步装 hub + agent (同一集群)
curl -sSL https://raw.githubusercontent.com/clusternet/clusternet/main/hack/install.sh | bash -s -- --mode hub+agent
```

### 3.3 应用分发入门

**场景**: 把一个应用 (用 Helm Chart) 分发到 child1 和 child2 两个子集群。

```text
Clusternet 分发模型:

  Base (基资源: HelmChart 或原始 YAML)
       │
       ▼
  Subscription (订阅: 把 Base 推到哪些集群)
       │
       ├─ Globalization (全局差异化, hub 侧)
       └─ Localization (本地差异化, 子集群侧)
       │
       ▼
  HelmRelease / Description (子集群上的实际部署)
```

**步骤 1: 定义 Base (Helm Chart)**

```yaml
# base-nginx.yaml
apiVersion: apps.clusternet.io/v1alpha1
kind: HelmChart
metadata:
  name: nginx
  namespace: default
spec:
  repo: https://charts.bitnami.com/bitnami
  chart: nginx
  version: "15.10.3"
```

**步骤 2: 定义 Subscription (订阅, 分发策略)**

```yaml
# sub-nginx.yaml
apiVersion: apps.clusternet.io/v1alpha1
kind: Subscription
metadata:
  name: nginx-sub
  namespace: default
spec:
  # 订阅者: 选哪些集群
  subscribers:
    - clusterAffinity:
        matchLabels:
          region: east-china      # 按标签匹配, 也可以用 clusterName

  # 待分发的 Base 列表
  feeds:
    - kind: HelmChart
      apiVersion: apps.clusternet.io/v1alpha1
      name: nginx
      namespace: default

  # 全局差异化 (hub 侧应用)
  # globalizations:
  #   - name: global-nginx-override
```

```bash
# 应用到父集群
kubectl apply -f base-nginx.yaml
kubectl apply -f sub-nginx.yaml

# 查看订阅状态
kubectl get subscriptions -n default
kubectl describe subscription nginx-sub -n default

# 查看子集群上的部署 (通过 clusternet 查看)
kubectl get helmreleases -n clusternet-xxx  # 在子集群的命名空间里
```

### 3.4 差异化覆盖

**Globalization (全局覆盖)**:

```yaml
apiVersion: apps.clusternet.io/v1alpha1
kind: Globalization
metadata:
  name: nginx-global-override
spec:
  # 作用于哪些 feed (Chart / Description)
  feed:
    kind: HelmChart
    name: nginx
    namespace: default
  # 覆盖值 (Helm values 格式)
  overrideValues:
    image:
      registry: harbor.internal.example.com
    service:
      type: ClusterIP
  # 优先级 (数字大的后应用)
  priority: 100
```

**Localization (本地覆盖)**:

```yaml
# 在子集群上, 针对某 feed 做本地差异化
apiVersion: apps.clusternet.io/v1alpha1
kind: Localization
metadata:
  name: nginx-local
  namespace: default
spec:
  feed:
    kind: HelmChart
    name: nginx
  overrideValues:
    replicaCount: 5
    service:
      type: NodePort
      nodePorts:
        http: "30080"
  priority: 200
```

> **优先级**: Localization > Globalization > Base 默认值。集群本地的覆盖优先级最高,符合「全局默认 + 本地特殊」的企业治理模式。

### 3.5 应用市场 (App Store)

Clusternet 内置应用市场,支持接入 Helm/OCI 仓库:

```yaml
# 注册 Helm 仓库
apiVersion: apps.clusternet.io/v1alpha1
kind: HelmRepo
metadata:
  name: bitnami
  namespace: default
spec:
  url: https://charts.bitnami.com/bitnami
  # 认证
  # username: user
  # password: pass

# 同步仓库索引
kubectl annotate helmrepo bitnami apps.clusternet.io/sync-charts=true -n default

# 查看可用 Chart
kubectl get helmcharts -n default | head -10
```

```bash
# 一键安装 (通过 Subscription 订阅 Chart 到 N 个集群)
kubectl apply -f - <<EOF
apiVersion: apps.clusternet.io/v1alpha1
kind: Subscription
metadata:
  name: install-redis
  namespace: default
spec:
  subscribers:
    - clusterAffinity:
        matchLabels:
          env: prod
  feeds:
    - kind: HelmChart
      name: redis
      namespace: default
EOF
```

### 3.6 多集群服务发现

Clusternet 提供 `clusternet-dns` 组件,支持跨集群服务 DNS 解析:

```bash
# 启用多集群 DNS
helm install clusternet-dns clusternet/clusternet-dns \
  --namespace clusternet-system

# 在子集群的 CoreDNS 中添加 stub zone
# .svc.clusternet.local 走 clusternet-dns
kubectl edit configmap coredns -n kube-system
# 添加:
#   clusternet.local:53 {
#     errors
#     cache 30
#     forward . 10.96.0.10:1053  # clusternet-dns 地址
#   }
```

```bash
# 在任意子集群 pod 内解析其他集群的服务
nslookup nginx.default.svc.cluster.child1.clusternet.local
# 直接访问
curl http://nginx.default.svc.cluster.child1.clusternet.local
```

### 3.7 Clusternet 常用命令速览

```bash
# 集群管理
kubectl get managedclusters                          # 子集群列表
kubectl describe managedcluster child1               # 集群详情
kubectl get clusternet-nodes -n clusternet-xxx       # 子集群节点(聚合)

# 应用分发
kubectl get subscriptions -A                         # 订阅
kubectl get helmcharts -A                            # Chart
kubectl get descriptions -A                          # 描述资源
kubectl get helmreleases -A                          # 发布状态
kubectl get localizations -A                         # 本地覆盖
kubectl get globalizations -A                        # 全局覆盖

# 调试
kubectl logs -n clusternet-system deploy/clusternet-hub
kubectl logs -n clusternet-system deploy/clusternet-agent   # 子集群上
kubectl get events -n clusternet-system --sort-by='.lastTimestamp'
```

---

## 四、对比与选型

### 4.1 Karmada vs Clusternet 维度对比

| 维度 | Karmada | Clusternet |
|:---|:---|:---|
| 发起方 | 华为 + 字节 | 腾讯 |
| 开源时间 | 2021 | 2021 |
| CNCF 阶段 | Incubating (2023) | Sandbox (2022) |
| 架构模式 | Hub-Spoke, push 为主,支持 pull | Hub-Spoke, pull 为主,支持 push |
| 资源模型 | 原生 K8s API + PropagationPolicy + OverridePolicy | Base + Subscription + Globalization + Localization |
| Helm 支持 | 需配合 Flux/Argo | 内置 HelmChart + HelmRelease |
| 应用市场 | 无 | 内置 App Store |
| 调度能力 | 强(集群亲和/污点/权重/拓扑 spread/副本划分) | 中(标签选择为主,权重支持) |
| 多集群服务 | MCS (K8s 标准 API) | clusternet-dns (自定义) |
| 边缘场景 | 支持 (pull 模式) | 原生优化,更轻量 |
| 状态聚合 | karmadactl 聚合输出 | 子集群 CRD 回传,可查看 |
| 与 GitOps 配合 | 好 (YAML 都是原生的,Argo/Flux 直接管) | 好 (Subscription 是 CRD) |
| 学习曲线 | 中 (掌握 PP/OP/RB/Work 四个核心 CRD) | 中高 (App Store + 多一层抽象) |
| 社区活跃度 | 高 (star 多 + 生产案例多) | 中 (腾讯生态为主) |
| 生产案例 | 字节/华为/滴滴/小红书/Shopee | 腾讯内部 + 外部若干 |

### 4.2 选型决策树

```text
选型决策:

  你要解决什么核心问题?
  │
  ├─ 「多集群统一调度 + 原生 K8s API 不侵入」
  │     → Karmada  (PropagationPolicy 附加上去, 业务 YAML 不用改)
  │
  ├─ 「多集群 + 应用商店 + Helm 治理 + 批量下发」
  │     → Clusternet  (App Store + Subscription 体验更好)
  │
  ├─ 「纯 GitOps, 所有变更走 Git」
  │     → Argo CD ApplicationSet (最简单) / Karmada + Flux
  │
  ├─ 「海量边缘集群 (1000+)」
  │     → Clusternet (pull 模式轻量) / KubeEdge
  │
  ├─ 「企业混合云 + 策略治理 + 集群生命周期」
  │     → OCM (Red Hat 路线) / Anthos (预算充足)
  │
  └─ 「服务层多集群(灰度/熔断/东西向流量)」
        → Istio multi-cluster (不是资源分发, 是服务治理)
```

### 4.3 两者可以共存吗

可以。Karmada 负责**资源层的联邦调度**,Clusternet 负责**应用层的市场与订阅**。生产上的常见组合:

```text
共存模式:

  底层 100 个集群
    │
    ├─ 用 Clusternet 管应用市场 (1000+ 个 Chart 的版本/分发)
    │   业务团队自助申请 → 一键部署到 N 个集群
    │
    └─ 用 Karmada 管核心业务 Deployment 的跨集群调度
        例如电商下单服务: 按权重 3:2 分布在 5 个集群
```

或者更简单的方式:**选一个主框架,另一个的能力通过插件补全**。比如用 Karmada 做分发,配合 Chart Museum + Argo CD 做应用市场。

---

## 五、多集群运维实践

### 5.1 集群生命周期管理

**新集群接入 SOP**：

```text
新集群接入 5 步:
  1. 集群合规检查 (版本/网络/CNI/CSI/认证)
  2. 部署 agent (karmada-agent / clusternet-agent)
  3. 注册到管控面 (add / register)
  4. 打标签 (region/az/env/department/business-line)
  5. 冒烟测试 (下发一个测试 Deployment, 验证分发+回传)
```

```bash
# Karmada: 注册 + 打标 + 验证
karmadactl add --cluster-context prod-cd-01 --name prod-cd-01
kubectl label cluster prod-cd-01 region=east-cd env=prod department=payment

# 冒烟测试
kubectl apply -f test-smoke.yaml   # 一个 Deployment + PP
karmadactl get deploy smoke-test -n test -C prod-cd-01
```

**集群下线 SOP**：

```text
下线 4 步:
  1. 排空: 把该集群的应用全部迁移走 (从 PP/Subscription 移除)
  2. 校验: 确认集群上已无业务流量 (Service Mesh 摘流)
  3. 脱离: karmadactl deatch / 删 ManagedCluster
  4. 回收: agent 卸载 + 资源回收
```

### 5.2 命名与标签规范

**集群命名**: `<环境>-<地域>-<编号>`,如 `prod-cd-01`、`test-bj-03`

**标签体系(必备)**:

| 标签 key | 含义 | 示例值 |
|:---|:---|:---|
| `region` | 地域/大区 | east-china / south-china / us-west |
| `az` | 可用区 | az1 / az2 / az3 |
| `env` | 环境 | prod / staging / test / dev |
| `department` | 所属部门 | payment / order / infra |
| `business-line` | 业务线 | retail / finance / internal |
| `cluster-type` | 集群类型 | standard / edge / gpu |
| `k8s-version` | K8s 版本 (自动打) | v1.29.2 |
| `provider` | 云厂商 | aliyun / tencent / on-prem |

> 标签体系直接决定分发策略的灵活性。建议在集群接入时就强制规范,不打标不允许注册。

### 5.3 跨集群监控与日志

**监控聚合方案**：

```text
方案一: 每个集群独立 Prometheus + 全局 Thanos (推荐)

  集群1 Prometheus ──┐
  集群2 Prometheus ──┼→ Thanos Sidecar → 对象存储 ← Thanos Query (全局查询)
  集群3 Prometheus ──┘

方案二: 中心化 Prometheus + federate
  (大规模不推荐, 单点压力大)

方案三: VictoriaMetrics 集群版 + vmagent 远程写
  (VictoriaMetrics 原生多租户, 适合多集群)
```

**日志聚合**: 各集群 Filebeat/Vector → 中心 Kafka → 中心 ES/ClickHouse。和单集群一样,只是多了一层采集。

**告警路由**: 按集群标签路由到对应团队的值班组(Alertmanager 的 `cluster=` 标签 + route)。

### 5.4 多集群灾备

**双活模式**:

```text
华东集群 (主)   ← 50% 流量 ← DNS / GSLB → 50% 流量 → 华南集群 (备)

应用: 双集群 Duplicated 模式, 各跑全量副本
数据: 数据库主从 / 对象存储跨域复制
流量: GSLB / 云厂商全局负载均衡
RTO: 分钟级 (DNS 切换)
RPO: 取决于数据同步延迟
```

**灾备切换 SOP**:

```text
故障判定 → 流量摘除 → 数据确认 → 全量切换 → 验证 → 通知
   1 分       2 分      3 分      2 分    2 分    1 分
                              ≈ 11 分钟
```

Karmada 操作:

```bash
# 故障集群脱离调度
kubectl taint cluster member1 failure=true:NoSchedule
# 把副本全部迁移到其他集群 (改 PP 的 clusterAffinity)
kubectl patch propagationpolicy nginx-pp -n demo --type=merge \
  -p '{"spec":{"placement":{"clusterAffinity":{"clusterNames":["member2"]}}}}'
```

### 5.5 安全与权限

| 风险点 | 对策 |
|:---|:---|
| 管控面权限过大 | RBAC 分层: 平台管理员管集群, 业务团队只管自己命名空间的 PP/Sub |
| 成员集群被入侵 | agent 最小权限 (只允许管自己命名空间的资源) |
| 跨集群横向移动 | 网络隔离 (VPC 对等 / 防火墙), 服务走 mTLS |
| 凭据泄露 | 短生命周期 token + 轮换, 不用长期 kubeconfig |
| 镜像分发安全 | 统一走 Harbor + cosign 验签, 子集群只能拉内网仓库 |
| 策略合规 | OPA/Gatekeeper 策略下发到所有集群, 统一审计 |

---

## 六、故障排查

### 6.1 通用排查思路

```text
多集群问题排查的四层模型:

  第 1 层: 资源定义层    ←  业务 YAML / Base / Chart 有问题
  第 2 层: 策略分发层    ←  PP/OP/Subscription/Localization 配错
  第 3 层: 调度绑定层    ←  scheduler 没调度 / 找不到匹配集群
  第 4 层: 执行通信层    ←  集群连不上 / agent 挂了 / 网络不通

定位口诀:
  "资源不发 → 看策略; 发了不到 → 看调度; 到了不跑 → 看集群"
```

### 6.2 Karmada 常见问题排查

| 现象 | 排查步骤 | 常见原因 |
|:---|:---|:---|
| ResourceBinding 一直 NOT SCHEDULED | `kubectl describe rb` + 看 scheduler 日志 | 集群名写错、标签不匹配、集群不健康 |
| Work 已创建但集群上没有 | `kubectl get work` + 看 execution controller 日志 | 集群不可达 / 权限不足 / 命名空间不存在 |
| 资源下发了但副本不对 | `kubectl describe rb` 看 aggregatedStatus | OverridePolicy 覆盖了 replicas / HPA 冲突 |
| 缓存状态不一致 | `karmadactl get deploy -C all` 对比 | 网络抖动 / agent 重启导致状态回传延迟 |
| 集群 NotReady | `kubectl describe cluster <name>` 看 conditions | apiserver 连不上 / token 过期 / 证书过期 |

**关键日志**:

```bash
# 调度器日志 (为什么没调度到某集群)
kubectl logs -n karmada-system deploy/karmada-scheduler --tail=100 | grep -i 'fail\|skip\|unschedulable'

# 执行控制器日志 (为什么没下发成功)
kubectl logs -n karmada-system deploy/karmada-controller-manager --tail=100 | grep -i 'work\|execut'

# Webhook 日志 (准入拒绝)
kubectl logs -n karmada-system deploy/karmada-webhook
```

### 6.3 Clusternet 常见问题排查

| 现象 | 排查步骤 | 常见原因 |
|:---|:---|:---|
| 子集群 NotActive | `kubectl describe managedcluster` + 看 agent 日志 | token 过期 / hub 地址不对 / 网络不通 |
| Subscription 不调度 | `kubectl describe subscription` | 集群标签不匹配 / feed 名称写错 |
| HelmRelease 失败 | `kubectl describe helmrelease` + `helm ls -n` | 仓库不可达 / values 语法错 / 镜像拉不到 |
| 应用市场 Chart 列表空 | `kubectl get helmrepo` 看同步状态 | 仓库 URL 错 / 认证失败 / 网络不通 |
| Localization 不生效 | `kubectl describe localization` 看事件 | feed 匹配错 / priority 不够被覆盖 |

### 6.4 网络连通性排错

```bash
# 验证管控面 → 成员集群连通性 (Karmada push 模式)
kubectl get cluster member1 -o jsonpath='{.status.conditions[?(@.type=="Ready")]}'

# 从管控面手动连成员集群 apiserver
kubectl --context member1 cluster-info

# Clusternet: 验证 agent → hub 连通性 (在子集群上)
kubectl logs -n clusternet-system deploy/clusternet-agent | grep -i 'connect\|heartbeat\|register'
kubectl exec -n clusternet-system deploy/clusternet-agent -- wget -O- $PARENT_URL/healthz
```

---

## 七、配置速查表

### 7.1 Karmada 核心 CRD 速查

| CRD | 作用 | 级别 | 关键字段 |
|:---|:---|:---|:---|
| `PropagationPolicy` | 分发策略 | 命名空间 | resourceSelectors / placement / replicaScheduling |
| `ClusterPropagationPolicy` | 集群级分发策略 | 集群 | 同上, 全集群范围生效 |
| `ResourceBinding` | 调度结果 | 命名空间 | clusters / scheduleDecision / aggregatedStatus |
| `ClusterResourceBinding` | 集群级调度结果 | 集群 | 同上 |
| `OverridePolicy` | 差异化覆盖 | 命名空间 | resourceSelectors / overrideRules / overriders |
| `ClusterOverridePolicy` | 集群级覆盖 | 集群 | 同上 |
| `Work` | 实际下发内容 | 执行空间 (karmada-es-*) | workload / status |
| `Cluster` | 集群对象 | 集群 | spec.syncMode (Push/Pull) / status.conditions |

### 7.2 Clusternet 核心 CRD 速查

| CRD | 作用 | 级别 | 关键字段 |
|:---|:---|:---|:---|
| `ManagedCluster` | 子集群对象 | 集群 (clusternet-*) | status.heartbeatFrequency / conditions |
| `Subscription` | 订阅 (分发策略) | 命名空间 | subscribers / feeds / globalizations |
| `Base` | 基资源 (原始 YAML) | 命名空间 | data (资源列表) |
| `HelmChart` | Helm 类型基资源 | 命名空间 | repo / chart / version / values |
| `HelmRelease` | Helm 发布状态 | 子集群命名空间 | chart / values / releaseName / status |
| `Localization` | 本地差异化 | 子集群命名空间 | feed / overrideValues / priority |
| `Globalization` | 全局差异化 | 集群 | feed / overrideValues / priority |
| `HelmRepo` | Helm 仓库 | 命名空间 | url / username / sync |

### 7.3 安装命令速查

```bash
# ===== Karmada =====
# Helm 装管控面
helm repo add karmada https://raw.githubusercontent.com/karmada-io/karmada/master/charts
helm install karmada karmada/karmada -n karmada-system --create-namespace
# 注册集群 (push)
karmadactl add --cluster-context ctx1 --name member1
# pull 模式
karmadactl token create --print-register-command

# ===== Clusternet =====
helm repo add clusternet https://clusternet.github.io/charts
# Hub
helm install clusternet-hub clusternet/clusternet-hub -n clusternet-system --create-namespace
# Agent
helm install clusternet-agent clusternet/clusternet-agent -n clusternet-system --create-namespace \
  --set parentURL=$HUB_URL --set parentToken=$TOKEN --set clusterName=child1
```

### 7.4 检查清单

```text
集群接入前:
  □ K8s 版本 ≥ 1.22 (和管控面差 ≤ 2 个小版本)
  □ 网络可达 (管控面 ↔ 成员集群 apiserver, push 模式)
  □ CNI / CSI / StorageClass 就绪
  □ 镜像仓库可访问 (Harbor / 公网)
  □ 集群标签体系完整 (region/az/env/department)
  □ 接入账号最小权限 (只给必要的 CRUD)

上线前:
  □ 冒烟测试通过 (Deployment + Service + HPA)
  □ 监控接入 (Prometheus / Grafana 大盘)
  □ 告警配置 (集群离线 / 资源下发失败 / 副本不足)
  □ 灾备演练过 (故障切换 RTO 达标)
  □ RBAC 分层 (平台 / 业务 / 只读)

日常运维:
  □ 每周健康巡检 (集群状态 / agent 在线 / 分发成功率)
  □ 每月版本评估 (升级 Karmada/Clusternet)
  □ 每季度灾备演练
  □ 策略变更走 Git + CR
```

### 7.5 一句话选型

```text
选 Karmada: 你想要"多集群 K8s 调度器", 业务 YAML 一个字都不想改。
选 Clusternet: 你想要"多集群应用商店", 批量下发 Helm Chart 是核心诉求。
都不选: 只有 2-3 个集群 + GitOps, 直接 Argo CD ApplicationSet 够用了。
```

*最后更新: 2026-08-25*
