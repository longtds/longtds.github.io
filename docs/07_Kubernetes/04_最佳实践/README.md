# 最佳实践

> K8s 最佳实践 = **集群选型+规模规划 + 高可用拓扑 + 资源画像与超分基线 + 多租户隔离 + 网络策略+安全基线 + 镜像/部署/发布纪律 + 监控/告警/SLO + 备份+灾备+恢复 + 升级 SOP + FinOps + 国产化路径 + 故障排查体系**。本章把"会用 K8s"升级到"能运营企业级容器平台"。

## 一、集群选型与规模规划

### 1.1 集群规模分级

| 规模 | 节点 | Pod | 推荐方案 |
|:---|---:|---:|:---|
| 试点 | 3-10 | < 500 | kubeadm + 单集群 |
| 小型 | 10-50 | < 5k | kubeadm + Cilium + Rook |
| 中型 | 50-300 | < 30k | kubeadm + Cilium + Karmada (2-5 集群) |
| 大型 | 300-2000 | < 200k | 多集群 Karmada + 强治理 |
| 超大 | 2000+ | 200k+ | 联邦 + region 多 hub + 专项调优 |

### 1.2 1 集群 vs 多集群

```
单集群优势:
  - 简单 / 成本低
  - 应用级故障域共享差
  
多集群优势:
  - 故障域隔离 (region/AZ/租户)
  - apiserver/etcd 不堆爆
  - 升级灰度 / 容灾切换
  - 多租户强隔离
  - 信创 + 公有 + 私有 多形态共存
  
建议:
  - dev/staging/prod 必分集群
  - prod 跨 region 最少 2 集群
  - 大业务独立集群
  - AI 训练独立集群
```

### 1.3 标准生产拓扑

```
Karmada Hub (1 + 2 副本 LB)
  ├─ Cluster-PROD-Region-A (3 master + N worker)
  ├─ Cluster-PROD-Region-B (3 master + N worker)
  ├─ Cluster-STAGING        (3 master + N worker)
  └─ Cluster-DEV            (1 master + N worker)

每集群:
  master: 3 副本 + etcd 独立 SSD + LB VIP
  worker: 通用池 + GPU 池 + DB 池 (taint 隔离)
  Ingress: 多副本 + 节点亲和 + LB
  存储: Rook-Ceph / Longhorn / 云厂 CSI
```

## 二、节点规划

### 2.1 节点角色与池

```
节点池:
  general:        通用业务 (8C32G - 32C128G)
  database:       数据库 (16C64G+ + 本地 NVMe)
  ai-train:       训练 (8x A100/H100 + NVLink + IB)
  ai-infer:       推理 (1-2x A30/L40 + 普通网)
  ingress:        Ingress 专用 (高带宽)
  edge:           边缘 (ARM64 + 小)

通过 taint + nodeSelector + nodeAffinity 隔离调度:
  kubectl taint nodes db-1 dedicated=db:NoSchedule
  pod 必须 toleration + nodeSelector 才能调度
```

### 2.2 节点基线

```
OS:           openEuler 22.03 LTS-SP3 / Ubuntu 22.04 / RHEL 9.x
Kernel:       5.15+ (推荐 6.x for eBPF/cgroup v2)
CRI:          containerd 1.7+
swap:         off
selinux/AppArmor: enforcing (但允许 K8s)
sysctl:       完整调优 (net.core / fs.inotify / vm.max_map_count)
ulimit:       nofile 1M+
分区:
  /              50-100GB
  /var/lib/kubelet 独立
  /var/lib/containerd 独立 100-500GB SSD
  /var/lib/etcd  独立 NVMe (仅 master)
  /var/log       独立
监控:           node-exporter + cAdvisor + 标签齐全
```

### 2.3 容量规划

```
CPU:
  超分 1.5-3x (requests)
  保留 system reserved + kube reserved (各 0.5-1C + 1Gi)
  
内存:
  超分 1.1-1.3x (谨慎)
  evictionHard memory.available<500Mi
  
Pod 数:
  默认 110 / 节点
  大节点 (32C+) 调 200-250
  
PV:
  按业务规划 (DB / 日志 / 训练数据)
  StorageClass 默认 + 多类型可选
```

## 三、资源画像与超分基线

### 3.1 必填 requests/limits

```yaml
resources:
  requests: { cpu: 100m, memory: 128Mi }
  limits:   { cpu: 500m, memory: 512Mi }
```

| 应用 | requests CPU | requests Mem | limits Mem |
|:---|:---|:---|:---|
| 微服务 (Go/Rust) | 100m | 128Mi | 256-512Mi |
| 微服务 (Python) | 200m | 256Mi | 512Mi-1Gi |
| Java (JVM) | 500m | 1Gi | 2-4Gi |
| DB (MySQL) | 2 | 4Gi | 8-16Gi |
| Redis | 200m | 512Mi | 1-2Gi |
| Kafka | 1-2 | 2-4Gi | 8Gi |
| ES data | 2-4 | 8Gi | 16-32Gi |
| AI 推理 (7B) | 4 | 8Gi + 24G GPU | - |
| AI 训练 | 8-32 | 32-128Gi | 多卡 |

JVM 必加：

```
-XX:+UseContainerSupport -XX:MaxRAMPercentage=75
```

### 3.2 VPA / 推荐

```bash
# VPA 用 Recommendation 模式收集数据
helm install vpa fairwinds-stable/vpa -n vpa --create-namespace
```

KRR (Robusta) 离线分析：

```bash
krr simple -k <kubeconfig>
# 输出每个 workload 的推荐 cpu/mem
```

### 3.3 QoS

```
Guaranteed   requests = limits         核心服务 (DB / Ingress)
Burstable    requests < limits         普通业务
BestEffort   都没设                     禁用
```

## 四、多租户

### 4.1 软多租户基线

```
每租户:
  - namespace(可多个) + RBAC + ResourceQuota + LimitRange
  - NetworkPolicy 默认 deny
  - PSS restricted
  - ImagePullSecret
  - 仓库 Project 隔离
  - 监控 + 日志按租户 label 切分

跨租户禁:
  - hostNetwork / hostPID / hostPath
  - privileged
  - 共享 PVC
```

### 4.2 RBAC 模板

```
租户 admin:    namespace 内全权 + 限制 PSP/PSS
租户 dev:      工作负载 + 配置 CRUD
租户 viewer:   只读
平台 admin:    集群级
平台 SRE:      读 + 节点维护
平台 audit:    只读 audit log
```

### 4.3 vcluster / Capsule（强隔离）

```bash
# 每租户独立 apiserver/etcd，共享宿主 K8s 节点
vcluster create tenant-x -n tenant-x \
  --connect=false \
  --values vcluster-values.yaml
```

## 五、网络与安全基线

### 5.1 NetworkPolicy 全 deny + 显式 allow

```yaml
# 每个 namespace 必备
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny }
spec: { podSelector: {}, policyTypes: [Ingress, Egress] }
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-dns }
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } }
          podSelector:       { matchLabels: { k8s-app: kube-dns } }
      ports: [{ port: 53, protocol: UDP }, { port: 53, protocol: TCP }]
```

### 5.2 Pod Security Standards

```
dev:        baseline (告警)
staging:    baseline (enforce) + restricted (warn)
prod:       restricted (enforce)
```

### 5.3 镜像策略

```
☐ 仅允许 Harbor + 白名单仓库
☐ Trivy Operator 持续扫描
☐ cosign 签名 + sigstore policy-controller 准入
☐ 禁 :latest
☐ 禁 root 用户 + 禁 privileged
☐ Pod 必须 USER 非 0 / 必须 readOnlyRootFilesystem
```

### 5.4 Kyverno 策略

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: require-resources }
spec:
  validationFailureAction: Enforce
  background: false
  rules:
    - name: require-requests-limits
      match: { any: [{ resources: { kinds: [Pod] } }] }
      validate:
        message: "Containers must have CPU/Memory requests and limits"
        pattern:
          spec:
            containers:
              - resources:
                  requests: { memory: "?*", cpu: "?*" }
                  limits:   { memory: "?*" }
```

常用策略：

```
☐ require-requests-limits
☐ disallow-latest-tag
☐ disallow-privileged
☐ require-nonroot
☐ require-trusted-registries
☐ require-pod-anti-affinity (prod 副本)
☐ require-readiness-probe / liveness-probe
☐ require-network-policy
```

## 六、镜像/部署/发布纪律

### 6.1 镜像规范（沿用 06_Docker/04_最佳实践）

```
命名:       harbor.example.com/<org>/<project>/<service>:<tag>
tag:        v1.2.3 / branch-shortsha
prod:       不可变 tag
基础:       distroless / wolfi / alpine
签名:       cosign 强签
扫描:       Trivy HIGH/CRITICAL 阻断
```

### 6.2 Deployment 模板（团队基线）

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  labels: { app.kubernetes.io/name: web, app.kubernetes.io/version: 1.5.2 }
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  selector: { matchLabels: { app: web } }
  template:
    metadata: { labels: { app: web } }
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector: { matchLabels: { app: web } }
                topologyKey: kubernetes.io/hostname
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector: { matchLabels: { app: web } }
      terminationGracePeriodSeconds: 60
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: web
          image: harbor.example.com/web/nginx:1.5.2
          imagePullPolicy: IfNotPresent
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: [ALL] }
          resources:
            requests: { cpu: 100m, memory: 128Mi }
            limits:   { cpu: 500m, memory: 256Mi }
          ports: [{ containerPort: 8080, name: http }]
          readinessProbe: { httpGet: { path: /ready, port: http }, periodSeconds: 5 }
          livenessProbe:  { httpGet: { path: /healthz, port: http }, periodSeconds: 10 }
          startupProbe:   { httpGet: { path: /healthz, port: http }, failureThreshold: 30, periodSeconds: 10 }
          lifecycle:
            preStop: { exec: { command: ["sh","-c","sleep 10"] } }
          volumeMounts:
            - { name: tmp, mountPath: /tmp }
            - { name: config, mountPath: /etc/app, readOnly: true }
      volumes:
        - { name: tmp, emptyDir: { medium: Memory, sizeLimit: 64Mi } }
        - { name: config, configMap: { name: web-config } }
```

### 6.3 发布策略

```
小流量 → 全量:
  RollingUpdate (maxSurge=1, maxUnavailable=0)
  
Canary:
  Argo Rollouts + Istio/Ingress
  10% → pause → 分析 → 50% → 全量
  
Blue/Green:
  双 Deployment + Service 切换
  
A/B Test:
  Header / Cookie 路由
```

### 6.4 PreStop + 优雅退出

```yaml
lifecycle:
  preStop:
    exec:
      command: ["sh","-c","sleep 10 && nginx -s quit"]
terminationGracePeriodSeconds: 60
```

Service 摘流要 endpoints 控制器更新 + kube-proxy/ipvs/cilium 同步，10s 是工程经验。

## 七、监控/告警/SLO

### 7.1 监控栈

```
指标:
  Prometheus + kube-prometheus-stack
  Thanos / VictoriaMetrics / Mimir (远端长存)
  
日志:
  Loki + Promtail / Fluent Bit / Vector
  
Trace:
  OpenTelemetry + Tempo / Jaeger / SkyWalking
  
APM:
  DeepFlow (国产 eBPF) ⭐
  
平台:
  Grafana + Alertmanager + 钉钉/飞书 webhook
```

### 7.2 必备告警

```yaml
- alert: NodeNotReady
  expr: kube_node_status_condition{condition="Ready",status="true"} == 0
  for: 5m

- alert: HighAPIServerLatency
  expr: histogram_quantile(0.99, rate(apiserver_request_duration_seconds_bucket{verb!~"WATCH|CONNECT"}[5m])) > 1
  for: 10m

- alert: EtcdHighLatency
  expr: histogram_quantile(0.99, rate(etcd_disk_backend_commit_duration_seconds_bucket[5m])) > 0.5
  for: 10m

- alert: EtcdHasNoLeader
  expr: etcd_server_has_leader == 0

- alert: PVCFull
  expr: kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.9
  for: 5m

- alert: PodOOMKilled
  expr: increase(kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}[15m]) > 0

- alert: HPAMaxed
  expr: kube_horizontalpodautoscaler_status_current_replicas == kube_horizontalpodautoscaler_spec_max_replicas
  for: 15m

- alert: HighCPUThrottle
  expr: rate(container_cpu_cfs_throttled_seconds_total[5m]) > 0.5
  for: 15m
```

### 7.3 SLO（Pyrra / Sloth）

```yaml
apiVersion: pyrra.dev/v1alpha1
kind: ServiceLevelObjective
metadata: { name: web-availability }
spec:
  target: "99.9"
  window: 28d
  indicator:
    ratio:
      errors:
        metric: http_requests_total{job="web", code=~"5.."}
      total:
        metric: http_requests_total{job="web"}
```

### 7.4 必备大盘

```
集群总览:  节点 / Pod / 资源利用率 / API QPS / etcd 健康
节点维度:  CPU/Mem/Disk/Net + Pod 密度
工作负载:  Deploy/StatefulSet 副本/重启/Probe 失败
应用 APM:  QPS/RT/Error/PRT P95
存储:     PVC 用量 + IOPS / 延迟
网络:     Hubble / DeepFlow / Service Mesh 流量
安全:     Falco / Tetragon / Audit
GitOps:   ArgoCD App health / Sync 失败
```

## 八、备份+灾备+恢复

### 8.1 三件套

```
1. etcd snapshot          每日 + 异地
2. Velero 资源备份        每日 (namespace + Restic PV)
3. 应用级备份             DB binlog / 业务侧
```

### 8.2 演练 SOP

```
季度演练:
  ☐ etcd 恢复 (单 master 故障 → 重建)
  ☐ Velero 全 namespace 恢复
  ☐ 跨集群应用切换 (DNS / GLB)
  ☐ 跨 region 灾备演练

RPO/RTO:
  关键业务:   RPO < 1h, RTO < 30min
  普通业务:   RPO < 24h, RTO < 4h
```

### 8.3 多集群灾备

```
Karmada/ApplicationSet → 多集群部署
DNS / GTM / Anycast LB → 流量切换
跨集群存储复制:
  - Ceph rbd-mirror
  - Velero + Restic / Kopia
  - DB 异步 / 半同步
  - 对象存储跨 Region
```

## 九、升级 SOP

### 9.1 月度小版本 / 季度 minor

```
准备:
☐ 阅读 changelog + deprecation
☐ 检查 CRD/Webhook 兼容
☐ 检查 CSI/CNI 兼容矩阵
☐ kubectl convert / kubeval 校验 YAML
☐ 备份 etcd

灰度:
☐ Dev 集群先升
☐ Staging 验证
☐ Prod canary 节点
☐ Prod 全量

回滚:
☐ etcd snapshot
☐ kubeadm rollback 路径
☐ 应用层兼容 (apiVersion 平滑)
```

### 9.2 Skew Policy 表

```
kubelet 与 apiserver:  ±2 minor
kubectl 与 apiserver:  ±1 minor
kube-proxy 与 apiserver: 同
controller-mgr/sched:  同
扩展 (CSI/CNI):       看各自矩阵
```

## 十、FinOps

### 10.1 成本可视化

```
工具:
  OpenCost / Kubecost ⭐
  阿里云 / 华为云 / 腾讯云 FinOps
  Robusta KRR (优化推荐)

维度:
  - 按 namespace / label / 团队 切分
  - CPU/Mem/Storage/Egress
  - 闲置 (idle) 资源
```

### 10.2 优化策略

```
☐ requests 精准化 (VPA recommendation)
☐ HPA + 节点 Auto Scaling
☐ Spot/抢占式实例 + PodDisruptionBudget
☐ 关停夜间 dev 集群
☐ 长期闲置 PVC 清理
☐ 大镜像懒加载 (Stargz/Nydus)
☐ 多租户配额 + 成本归属
☐ 弹性混部 (在线 + 离线 / AI 训练 + 业务)
```

## 十一、国产化路径

```
2026 落地清单:
☐ 一集群 KubeSphere + 鲲鹏 ARM64 worker
☐ kube-ovn / 华为 CCE-Turbo 一种
☐ 昇腾 GPU + HAMi 混调度
☐ kube-prometheus-stack / DeepFlow 监控
☐ Harbor 国密 TLS + Trivy
☐ 国产 OS (openEuler / 麒麟) + iSulad/containerd
☐ KubeBlocks 国产数据库 Operator
☐ 等保 三级 / 国测中心 评测

2027-2028:
☐ 党政关基 全栈信创
☐ Karmada 跨多云联邦 (公私 + 信创)
☐ 海光 CSV CoCo
```

## 十二、故障排查体系

### 12.1 标准排查路径

```
1. kubectl get all -A | grep -v Running
2. kubectl describe <对象>  → Events
3. kubectl logs --previous
4. kubectl get events -A --sort-by=.lastTimestamp
5. kubectl top nodes / top pods
6. journalctl -u kubelet -u containerd
7. dmesg | tail
8. 节点 ssh: ctr/crictl ps -a + nsenter
9. apiserver audit log
10. Hubble / DeepFlow 网络层
```

### 12.2 常见故障速查

| 症状 | 大概率原因 |
|:---|:---|
| Pod Pending | requests 不足 / Selector / Taint / PVC 未 bind |
| CrashLoopBackOff | 应用错 / 探针错 / 配置错 |
| ImagePullBackOff | 仓库 / Secret / 网络 / quota |
| Node NotReady | kubelet / containerd / CNI / 磁盘满 / 内存 |
| Svc 不通 | endpoints 空 / NP 阻塞 / DNS / kube-proxy |
| 部分节点 DNS 慢 | NodeLocal 没装 / ndots / CoreDNS 副本不够 |
| etcd 慢 | IO / 磁盘满 / defrag 没做 / 5+ 副本网络 |
| apiserver 雪崩 | APF / 大对象 watch / Audit 同步 |
| HPA 不缩 | metrics-server / cooldown / minReplicas |
| OOMKilled | limits 太小 / leak / JVM 没 UseContainerSupport |
| 节点 Disk Pressure | image / 日志 / volume |
| CNI 异常 | bird/BGP / VXLAN / firewall / MTU |
| GPU 调度失败 | device plugin / driver / MIG profile |

### 12.3 常用工具

```
kubectl debug / krew 插件: tree / neat / who-can / view-allocations / df-pv
stern (多 Pod 日志聚合)
kube-shell / k9s ⭐
kubectl-tree (依赖关系)
ksniff (Pod tcpdump)
kubescape / popeye (健康审计)
Hubble / Tetragon / DeepFlow (eBPF)
nsenter / crictl / ctr (节点级)
```

## 十三、最佳实践 Checklist

```
集群拓扑:
☐ 3+ master HA + LB VIP
☐ etcd 独立 NVMe
☐ 多 worker 池 (taint 隔离)
☐ Karmada 多集群联邦

节点基线:
☐ openEuler/Ubuntu + kernel 5.15+
☐ containerd + systemd cgroup
☐ swap off + sysctl 调优
☐ 分区: /var/lib/containerd + /var/lib/kubelet + /var/lib/etcd 独立

工作负载:
☐ requests/limits 全设
☐ readiness + liveness + startupProbe
☐ podAntiAffinity + topology spread
☐ PreStop + grace 60s
☐ rollout maxSurge=1 maxUnavailable=0
☐ HPA + PDB

网络:
☐ Cilium / Calico + NetworkPolicy 默认 deny
☐ NodeLocal DNSCache
☐ Ingress + cert-manager
☐ Service Mesh (Istio Ambient / Cilium SM) 可选

存储:
☐ Rook-Ceph / Longhorn
☐ StorageClass + Snapshot
☐ Velero 备份

安全:
☐ PSS restricted (prod)
☐ Kyverno / Gatekeeper 强制策略
☐ Trivy Operator + cosign
☐ Falco + Tetragon
☐ Audit log → SIEM
☐ RBAC 最小权限 + OIDC SSO

观测:
☐ kube-prometheus-stack + Loki + Tempo + DeepFlow
☐ 必备告警全配
☐ SLO + 错误预算
☐ Hubble / Tetragon 可视化

多租户:
☐ ns + RBAC + Quota + LimitRange + NP + PSS
☐ vcluster / Capsule (强隔离场景)

GitOps:
☐ ArgoCD + ApplicationSet
☐ Image Updater 自动跟踪
☐ Argo Rollouts (Canary + AnalysisTemplate)

备份:
☐ etcd snapshot 每日 + 异地
☐ Velero 每日
☐ DB 应用级备份
☐ 季度演练 + RTO/RPO 文档

升级:
☐ Skew Policy 表
☐ 月度小版本 + 季度 minor
☐ 灰度: dev → staging → prod canary → 全量

FinOps:
☐ OpenCost / Kubecost
☐ KRR 优化推荐
☐ HPA + Cluster AutoScaler + 抢占
☐ 闲置资源月度清理

国产化:
☐ KubeSphere / CCE / ACK / TKE
☐ 鲲鹏/飞腾 ARM64 节点池
☐ 昇腾 GPU + HAMi
☐ Higress / APISIX / kube-ovn
☐ Harbor 国密 + 国产监控

故障排查:
☐ 应急 SOP 文档
☐ 排障工具集 (k9s/stern/kube-shell/kubescape)
☐ 演练手册 + Postmortem 模板
```

## 十四、典型生产架构模板

### 14.1 互联网中型企业

```
集群:    K8s 1.30 + containerd + Cilium + Rook-Ceph
入口:    LB → ingress-nginx + cert-manager (Let's Encrypt)
观测:    kube-prometheus-stack + Loki + Tempo
GitOps: ArgoCD + Helmfile
安全:    Kyverno + Trivy Operator + Falco + cosign
多集群:  Karmada (dev/staging/prod 三集群)
团队:    5-15 SRE + DevOps
```

### 14.2 央企信创

```
集群:    KubeSphere + containerd/iSulad + kube-ovn + Rook-Ceph + Spiderpool
入口:    F5 / 华为 ELB → Higress + 国密 TLS
观测:    DeepFlow + 夜莺 + kube-prometheus-stack
GitOps: GitLab + Jenkins + ArgoCD
安全:    Kyverno + 长亭洞鉴 + 奇安信 + Falco
合规:    等保三级 / 国测中心
信创:    鲲鹏 + openEuler + GaussDB + 海光 CSV
GPU:    昇腾 910B + HAMi
```

### 14.3 AI 训练平台

```
集群:    K8s 1.30 + 节点池 (8x A100/H100 + IB + NVLink)
调度:    Volcano + Kueue + HAMi
镜像:    Harbor + vLLM/PyTorch 大镜像 (Stargz lazy load)
存储:    Ceph + NFS + S3 数据 lake
观测:    DCGM exporter + NVIDIA Container Toolkit
推理:    KServe / vLLM Production Stack / llm-d
任务:    JobSet / PyTorchJob / Argo Workflows
```

### 14.4 边缘/IoT

```
中心:    K8s + KubeEdge / OpenYurt / SuperEdge
边缘:    k3s + containerd + iSulad (国产)
镜像:    Harbor Proxy Cache + 离线同步
观测:    轻量 Prometheus + DeepFlow
管理:    云边协同 + GitOps
```

## 十五、推荐栈

```
集群安装:   kubeadm / KubeSphere / Rancher / 云厂托管
CRI:        containerd ⭐
CNI:        Cilium ⭐ / Calico / kube-ovn (国产)
CSI:        Rook-Ceph ⭐ / Longhorn / 云厂 CSI
Ingress:    ingress-nginx ⭐ / Higress / APISIX
DNS:        CoreDNS + NodeLocal DNSCache
观测:       kube-prometheus-stack + Loki + Tempo + DeepFlow + Hubble
GitOps:     ArgoCD ⭐ + Image Updater + Argo Rollouts
备份:       Velero + Restic + etcd snapshot
安全:       Kyverno + Trivy Operator + cosign + Falco + Tetragon
多集群:     Karmada ⭐ / Cluster API
平台:       KubeSphere ⭐ / Backstage / Rancher / Crossplane
GPU/AI:     NVIDIA GPU Operator + HAMi + Volcano/Kueue + vLLM/llm-d/KServe
国产开源:   KubeSphere / Sealos / KubeBlocks / Karmada / OpenKruise / Higress / HAMi / kube-ovn / Spiderpool / HwameiStor
```

> 📖 **核心判断**：K8s 最佳实践 = **拓扑(HA 多 master + Karmada 多集群) + 节点(NVMe etcd + 池化) + 资源(VPA/KRR 画像) + 多租户(RBAC+Quota+NP+PSS) + 镜像/部署纪律(Kyverno 强制) + 监控告警 SLO + 备份灾备演练 + 升级 SOP + FinOps + 国产化 + 故障排查体系**。能在白板上画出"3-region 多集群 + Karmada + ArgoCD ApplicationSet + kube-prometheus + Velero + Kyverno + Trivy + cosign + Falco + DeepFlow"全栈、能给团队定 Deployment 基线 + 策略基线 + 升级 SOP + 灾备演练表，就具备 K8s 平台负责人能力。
