# 进阶

> K8s 进阶 = **kubeadm/Rancher/KubeSphere 多节点生产部署 + Cilium/Calico CNI 深度 + NetworkPolicy + Rook-Ceph/Longhorn 存储 + Ingress(Nginx/APISIX/Higress) + cert-manager + ExternalDNS + Pod Security Standards + Network Policy + RBAC 实战 + Helm + Kustomize + 备份恢复(Velero/etcd snapshot) + 多租户 + 集群升级 + 监控(kube-prometheus-stack/Loki/Tempo)**。本章面向独立运维 5-50 节点集群的工程师。

## 一、生产集群部署

### 1.1 kubeadm（最主流）

```bash
# 全节点公共操作
swapoff -a; sed -i '/swap/s/^/#/' /etc/fstab
modprobe br_netfilter overlay
cat > /etc/sysctl.d/k8s.conf <<EOF
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF
sysctl --system

# containerd
apt install -y containerd.io
containerd config default > /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sed -i 's|registry.k8s.io/pause:3.6|registry.aliyuncs.com/k8sxio/pause:3.9|' /etc/containerd/config.toml
systemctl restart containerd

# kube* 三件套
apt install -y kubeadm=1.30.* kubelet=1.30.* kubectl=1.30.*
apt-mark hold kubeadm kubelet kubectl

# 镜像加速
sed -i 's|registry.k8s.io|registry.aliyuncs.com/k8sxio|g' kubeadm.yaml

# Master 初始化（HA: 用 stacked etcd + 3 master + LB VIP）
kubeadm init --config kubeadm.yaml --upload-certs

# Worker join
kubeadm join <vip>:6443 --token ... --discovery-token-ca-cert-hash sha256:...
```

`kubeadm.yaml`（生产模板）：

```yaml
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
kubernetesVersion: 1.30.5
controlPlaneEndpoint: "k8s-vip.example.com:6443"
imageRepository: registry.aliyuncs.com/k8sxio
networking:
  serviceSubnet: 10.96.0.0/16
  podSubnet: 10.244.0.0/16
etcd:
  local:
    extraArgs:
      election-timeout: "5000"
apiServer:
  certSANs:
    - "k8s-vip.example.com"
    - "10.0.0.100"
  extraArgs:
    audit-log-path: /var/log/k8s/audit.log
    audit-log-maxsize: "200"
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cgroupDriver: systemd
maxPods: 110
serializeImagePulls: false
```

### 1.2 HA 拓扑

```
LB (haproxy + keepalived VIP 6443)
   │
   ├─ master-1 (apiserver + scheduler + cm + etcd)
   ├─ master-2 (apiserver + scheduler + cm + etcd)
   └─ master-3 (apiserver + scheduler + cm + etcd)

worker-1 ... worker-N
```

### 1.3 国内常用发行版

```
Rancher / Rancher Manager  ⭐ 多集群管理 (SUSE)
KubeSphere ⭐               (青云开源, 国产首选)
OpenShift / OKD            Red Hat
Kubernetes Operations (kops) AWS
KubeKey                    KubeSphere 安装器
RKE2 / k3s                 SUSE 轻量
华为 CCE / 阿里 ACK / 腾讯 TKE / 火山 VKE  云厂托管
```

## 二、CNI 深度

### 2.1 选型矩阵

| CNI | 模型 | NetworkPolicy | 性能 | 国产化 |
|:---|:---|:---:|:---:|:---:|
| **Cilium** ⭐ | eBPF | L3-L7 + eBPF | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Calico** | BGP/VXLAN | L3-L4 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Flannel** | VXLAN | 无 | ⭐⭐⭐ | ⭐⭐ |
| **Antrea** | OVS | L7 | ⭐⭐⭐⭐ | ⭐⭐ |
| **kube-ovn** ⭐ | OVN | L3-L4 + VPC + SR-IOV | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **华为 CCE-Turbo** | ENI | L3 + VPC | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 2.2 Cilium 部署

```bash
helm repo add cilium https://helm.cilium.io
helm install cilium cilium/cilium --version 1.16 -n kube-system \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost=k8s-vip.example.com \
  --set k8sServicePort=6443 \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true \
  --set bpf.masquerade=true \
  --set ipam.mode=kubernetes \
  --set tunnel=vxlan
```

Cilium 替代 kube-proxy（高性能 eBPF）+ Hubble 全链路可观测。

### 2.3 NetworkPolicy

```yaml
# 默认全 deny + 显式 allow
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny, namespace: prod }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-frontend-to-backend, namespace: prod }
spec:
  podSelector: { matchLabels: { app: backend } }
  ingress:
    - from:
        - podSelector: { matchLabels: { app: frontend } }
      ports: [{ port: 8080, protocol: TCP }]
```

Cilium 还支持 L7（HTTP method/path）：

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata: { name: api-l7 }
spec:
  endpointSelector: { matchLabels: { app: api } }
  ingress:
    - fromEndpoints:
        - matchLabels: { app: frontend }
      toPorts:
        - ports: [{ port: "8080", protocol: TCP }]
          rules:
            http:
              - { method: "GET", path: "/v1/.*" }
              - { method: "POST", path: "/v1/orders" }
```

### 2.4 IPVS / kube-proxy

```bash
# 大集群必启 IPVS（不是 iptables）
# kubeadm.yaml 内:
mode: ipvs
ipvs: { strictARP: true }

# 或 cilium kubeProxyReplacement=true（彻底干掉 kube-proxy）
```

## 三、存储 CSI

### 3.1 选型

| 方案 | 场景 | 模式 |
|:---|:---|:---|
| **Rook-Ceph** ⭐ | 通用、块+文件+对象 | 大规模 |
| **Longhorn** ⭐ | HCI / 中小、易上手 | RWO 块 |
| **OpenEBS** | 块/卷复制 | 中等 |
| **NFS-CSI** | 共享 | RWX |
| **MinIO + S3 CSI** | 对象存储 | OSS |
| **云厂 CSI** | EBS/CBS/OSS | 公有云 |
| **华为 SFS+EVS** | 信创 | 国产 |

### 3.2 Rook-Ceph 部署

```bash
git clone --single-branch --branch v1.14 https://github.com/rook/rook
cd rook/deploy/examples
kubectl apply -f crds.yaml -f common.yaml -f operator.yaml
kubectl apply -f cluster.yaml      # 单 Region 3 节点
kubectl apply -f toolbox.yaml      # ceph CLI

# StorageClass
kubectl apply -f csi/rbd/storageclass.yaml
kubectl apply -f filesystem.yaml
kubectl apply -f csi/cephfs/storageclass.yaml
```

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: ceph-rbd }
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  clusterID: rook-ceph
  pool: replicapool
  imageFormat: "2"
  imageFeatures: layering
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### 3.3 VolumeSnapshot

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata: { name: ceph-rbd-snap }
driver: rook-ceph.rbd.csi.ceph.com
deletionPolicy: Delete
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata: { name: mysql-snap, namespace: prod }
spec:
  volumeSnapshotClassName: ceph-rbd-snap
  source: { persistentVolumeClaimName: mysql-data }
```

## 四、Ingress / Gateway

### 4.1 ingress-nginx + cert-manager

```bash
helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.metrics.enabled=true \
  --set controller.podAnnotations."prometheus\.io/scrape"=true \
  --set controller.config.proxy-body-size=8m \
  --set controller.config.use-forwarded-headers=true

helm install cert-manager jetstack/cert-manager -n cert-manager --create-namespace \
  --set installCRDs=true
```

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: letsencrypt-prod }
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: sre@example.com
    privateKeySecretRef: { name: letsencrypt-prod }
    solvers:
      - http01:
          ingress: { class: nginx }
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls: [{ hosts: [web.example.com], secretName: web-tls }]
  rules:
    - host: web.example.com
      http: { paths: [{ path: /, pathType: Prefix, backend: { service: { name: web, port: { number: 80 } } } }] }
```

### 4.2 Gateway API（新标准）

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata: { name: my-gw }
spec:
  gatewayClassName: cilium
  listeners:
    - name: https
      port: 443
      protocol: HTTPS
      tls: { certificateRefs: [{ name: web-tls }] }
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata: { name: web }
spec:
  parentRefs: [{ name: my-gw }]
  hostnames: [web.example.com]
  rules:
    - matches: [{ path: { type: PathPrefix, value: / } }]
      backendRefs: [{ name: web, port: 80 }]
```

支持：Cilium / Istio / Envoy Gateway / Higress / Kong / APISIX。

### 4.3 国产选项

```
APISIX ⭐ (Apache, 国产开源)
Higress ⭐ (阿里, Istio + Envoy + Nginx 三合一)
Kong / Tyk
华为 ELB / 阿里 ALB Ingress
```

## 五、可观测：kube-prometheus-stack + Loki + Tempo

```bash
helm install kps prometheus-community/kube-prometheus-stack -n monitoring --create-namespace \
  --set grafana.adminPassword=change...  --set prometheus.prometheusSpec.retention=15d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=200Gi

helm install loki grafana/loki-stack -n monitoring \
  --set promtail.enabled=true --set loki.persistence.enabled=true

helm install tempo grafana/tempo -n monitoring
```

### 5.1 ServiceMonitor 抓应用指标

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata: { name: web, namespace: monitoring, labels: { release: kps } }
spec:
  selector: { matchLabels: { app: web } }
  namespaceSelector: { matchNames: [prod] }
  endpoints: [{ port: metrics, interval: 30s }]
```

### 5.2 必备告警（PrometheusRule）

```yaml
- alert: NodeNotReady
  expr: kube_node_status_condition{condition="Ready",status="true"} == 0
  for: 5m
- alert: PodCrashLoop
  expr: rate(kube_pod_container_status_restarts_total[5m]) > 0
  for: 10m
- alert: PVCNearFull
  expr: kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.85
  for: 10m
- alert: APIServerLatencyHigh
  expr: histogram_quantile(0.99, rate(apiserver_request_duration_seconds_bucket[5m])) > 1
  for: 10m
- alert: EtcdHasNoLeader
  expr: etcd_server_has_leader == 0
- alert: EtcdHighCommitDuration
  expr: histogram_quantile(0.99, rate(etcd_disk_backend_commit_duration_seconds_bucket[5m])) > 0.25
```

## 六、Helm + Kustomize + GitOps

### 6.1 多环境 Kustomize

```
base/
  deployment.yaml
  service.yaml
  kustomization.yaml
overlays/
  dev/
    kustomization.yaml  # patches: { replicas: 1, env: { LOG_LEVEL: debug } }
  staging/
    kustomization.yaml
  prod/
    kustomization.yaml  # replicas: 3, HPA enabled
```

```bash
kubectl apply -k overlays/prod
```

### 6.2 ArgoCD GitOps

```bash
helm install argocd argo/argo-cd -n argocd --create-namespace
argocd login argocd.example.com
argocd app create web --repo https://gitlab/.../infra.git --path overlays/prod --dest-server https://kubernetes.default.svc --dest-namespace web --sync-policy automated
```

ApplicationSet 实现多集群多环境：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata: { name: web }
spec:
  generators:
    - list:
        elements:
          - { env: dev,  cluster: in-cluster }
          - { env: prod, cluster: prod-cluster }
  template:
    metadata: { name: 'web-{{env}}' }
    spec:
      source: { repoURL: 'https://...', path: 'overlays/{{env}}', targetRevision: HEAD }
      destination: { server: '{{cluster}}', namespace: web }
      syncPolicy: { automated: { prune: true, selfHeal: true } }
```

## 七、备份与恢复

### 7.1 etcd snapshot

```bash
# 每日定时
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%F).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 恢复
etcdctl snapshot restore /backup/etcd-2026-06-27.db \
  --data-dir=/var/lib/etcd-restore
# 改 etcd 数据目录 + 重启
```

### 7.2 Velero（对象级备份）

```bash
velero install \
  --provider aws --plugins velero/velero-plugin-for-aws:v1.10.0 \
  --bucket k8s-backup --secret-file ./credentials \
  --backup-location-config region=cn-north-1,s3Url=https://s3.example.com,s3ForcePathStyle=true \
  --use-volume-snapshots=true

velero backup create daily-backup --include-namespaces=prod --ttl 720h
velero schedule create daily --schedule="0 2 * * *" --include-namespaces=prod --ttl 720h
velero restore create --from-backup daily-20260627
```

支持 Restic / Kopia 文件级备份 PVC 数据。

## 八、Pod Security + 多租户

### 8.1 Pod Security Standards (PSS)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prod
  labels:
    pod-security.kubernetes.io/enforce: restricted     # 严格
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

`restricted` 强制：

- 非 root + readOnlyRootFilesystem + drop ALL caps
- 禁 hostNetwork/hostPID/hostIPC/hostPath
- seccomp Default
- 仅特定 volumes

### 8.2 ResourceQuota + LimitRange

```yaml
apiVersion: v1
kind: ResourceQuota
metadata: { name: prod-quota, namespace: prod }
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    limits.cpu: "200"
    limits.memory: 400Gi
    persistentvolumeclaims: "50"
    requests.storage: 10Ti
    count/pods: "500"
---
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: prod }
spec:
  limits:
    - type: Container
      default:        { cpu: 500m, memory: 512Mi }
      defaultRequest: { cpu: 100m, memory: 128Mi }
      max:            { cpu: 4,    memory: 8Gi }
```

### 8.3 多租户模式

```
软多租户:
  - namespace 隔离 + RBAC + Quota + NetworkPolicy + PSS
  - 单集群成本低，隔离弱
强多租户:
  - vcluster / Kamaji / Capsule
  - 每租户独立 apiserver
  - 共享底层节点
硬多租户:
  - 每租户独立集群
  - 最强隔离，最高成本
```

vcluster（虚拟集群）：

```bash
vcluster create my-tenant -n tenant-x
```

## 九、集群升级

```bash
# minor 升级（必从次低版本递进，不能跨 minor）
# 1. master 一个一个升
apt-mark unhold kubeadm
apt install -y kubeadm=1.31.*
kubeadm upgrade plan
kubeadm upgrade apply v1.31.0

# 2. kubelet + kubectl
apt install -y kubelet=1.31.* kubectl=1.31.*
systemctl restart kubelet

# 3. worker 节点逐个
kubectl drain node1 --ignore-daemonsets
ssh node1
  kubeadm upgrade node
  apt install -y kubelet=1.31.* kubectl=1.31.*
  systemctl restart kubelet
kubectl uncordon node1
```

### Skew Policy（版本偏差）

```
apiserver vs kubelet:  kubelet 可低 2 minor
kubectl:               与 apiserver 同或差 1
kube-proxy:            与 apiserver 同
node CSI/CNI plugin:   按各自兼容矩阵
```

## 十、CRD + Operator 基础

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata: { name: mysqlclusters.db.example.com }
spec:
  group: db.example.com
  scope: Namespaced
  names:
    kind: MySQLCluster
    plural: mysqlclusters
    shortNames: [mysqlcl]
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                replicas: { type: integer, minimum: 1, maximum: 9 }
                version:  { type: string }
```

Operator 框架：

- **Operator SDK** (Go/Ansible/Helm)
- **kubebuilder** ⭐ Go 主流
- **KOPF** (Python)
- **Crossplane** (基础设施)

## 十一、典型坑（进阶）

| 坑 | 建议 |
|:---|:---|
| **etcd 没单独 SSD** | etcd 写延迟 > 100ms 集群崩 |
| **kube-proxy iptables 模式大集群** | 启 IPVS / Cilium kpr |
| **CoreDNS 没扩容** | replicas=2 默认，大集群至少 4+ |
| **没 NodeLocal DNSCache** | DNS 抖动放大 |
| **Calico VXLAN 性能不够** | 切 BGP / Cilium |
| **NetworkPolicy 不写默认 deny** | 等于没用 |
| **PSS 给 baseline 不够** | 生产用 restricted |
| **Helm release 滚动失败回滚** | --atomic + --wait |
| **kubectl exec 改文件** | 全 IaC + ArgoCD |
| **etcd 备份没演练** | 必演练 restore |
| **集群跨大版本升级** | 1.28→1.29→1.30 必递进 |
| **没 ResourceQuota** | 单 ns 资源全占 |

## 十二、进阶 Checklist

```
部署:
☐ kubeadm 多 master HA + LB VIP
☐ containerd + systemd cgroup
☐ etcd 独立 SSD + 备份 cron
☐ kube-proxy 切 IPVS 或 Cilium kpr

网络:
☐ Cilium / Calico + NetworkPolicy 默认 deny
☐ NodeLocal DNSCache
☐ MetalLB / LB / CCM
☐ Ingress + cert-manager + Let's Encrypt

存储:
☐ Rook-Ceph / Longhorn 一种
☐ StorageClass + VolumeSnapshot
☐ 备份策略 (Velero + Restic)

安全:
☐ Pod Security Standards restricted (prod)
☐ NetworkPolicy 默认 deny + 显式 allow
☐ RBAC 最小权限
☐ Audit log + SIEM
☐ Image PullSecret + Trivy Operator + Kyverno

观测:
☐ kube-prometheus-stack
☐ Loki + Promtail
☐ Tempo / Jaeger
☐ Hubble (Cilium)
☐ 告警全覆盖 + 钉钉/飞书

多租户:
☐ namespace + RBAC + Quota + LimitRange + NP
☐ vcluster 试点

GitOps:
☐ ArgoCD + Kustomize/Helm
☐ ApplicationSet 多环境多集群
☐ image-updater 自动升级

备份:
☐ etcd snapshot 每日 + 异地
☐ Velero 周备 + 月备 + 灾备
☐ 季度恢复演练

升级:
☐ minor 跨集群灰度
☐ skew policy 严格

国产化:
☐ KubeSphere / Rancher 控制台
☐ kube-ovn + 鲲鹏/飞腾
☐ 华为 CCE / 阿里 ACK 适配
```

## 十三、推荐栈

```
集群安装:   kubeadm + KubeSphere / Rancher / RKE2
CNI:        Cilium ⭐ / Calico / kube-ovn (国产)
CSI:        Rook-Ceph ⭐ / Longhorn / NFS-CSI
Ingress:    ingress-nginx / Higress / APISIX / Cilium Gateway
DNS:        CoreDNS + NodeLocal DNSCache
证书:       cert-manager + Let's Encrypt / 内 CA
观测:       kube-prometheus-stack + Loki + Tempo + Hubble
日志:       Promtail / Vector / Fluent Bit → Loki / ELK
GitOps:     ArgoCD ⭐ / Flux
包管:       Helm + Kustomize (Helmfile / ArgoCD)
备份:       Velero + Restic + etcd snapshot
安全:       Kyverno / Gatekeeper + Trivy Operator + Falco
多租户:     vcluster / Capsule / Kamaji
国产:       KubeSphere / 华为 CCE / 阿里 ACK / 腾讯 TKE / 火山 VKE
```

> 📖 **核心判断**：K8s 进阶 = **kubeadm HA + Cilium/Calico CNI + Rook-Ceph/Longhorn + ingress-nginx+cert-manager + kube-prometheus-stack+Loki+Tempo + ArgoCD GitOps + Velero+etcd snapshot + PSS restricted + ResourceQuota + 多租户(vcluster) + 集群升级**。能搭出 3 master HA + Cilium + Rook-Ceph + ArgoCD + 监控全栈 + Velero 备份，就具备 K8s 平台运维能力。
