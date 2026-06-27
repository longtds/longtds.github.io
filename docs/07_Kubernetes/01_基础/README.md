# 基础

> K8s 基础 = **核心对象(Pod/Deployment/Service/Ingress/ConfigMap/Secret) + 控制平面(apiserver/scheduler/controller-manager/etcd) + 节点组件(kubelet/kube-proxy/CRI/CNI/CSI) + kubectl 操作 + Helm 基础 + RBAC + 调度模型 + 常见排障**。本章面向入职 1 年内的工程师。

## 一、整体架构

```
┌─────────── Control Plane (master) ───────────┐
│  kube-apiserver  ← 唯一入口 (HTTPS+RBAC)        │
│  etcd            ← 唯一状态存储                  │
│  kube-scheduler  ← Pod 调度                     │
│  controller-mgr  ← Deployment/RS/Endpoint 控制器 │
│  cloud-cm        ← 云厂集成 (LB/Volume)         │
└────────────────┬─────────────────────────────┘
                 │ apiserver
┌────────────────▼─────────── Node ────────────┐
│  kubelet         ← 节点上 Pod 生命周期           │
│  kube-proxy      ← Service/iptables/IPVS         │
│  Container Runtime ← containerd / CRI-O          │
│  CNI / CSI plugins                              │
└─────────────────────────────────────────────────┘
```

要点：

- **声明式**：你写期望状态，控制器循环 reconcile
- **API + etcd 二元中心**：一切对象走 apiserver，落 etcd
- **Pod 是最小调度单元**（不是容器）
- **Service 是稳定虚 IP**，解决 Pod IP 漂移
- **Label/Selector** 是连接对象的元粘合剂

## 二、核心对象

| 对象 | 作用 | 典型 |
|:---|:---|:---|
| **Pod** | 1+ 容器共享网络/存储 | 业务最小单元 |
| **Deployment** | 无状态副本 + 滚动升级 | Web/API |
| **StatefulSet** | 有状态 + 稳定身份 | DB/MQ |
| **DaemonSet** | 每节点 1 实例 | 日志/监控/CNI |
| **Job/CronJob** | 一次性/周期任务 | 备份/批处理 |
| **Service** | 稳定 VIP + 负载均衡 | 服务发现 |
| **Ingress** | L7 入口路由 | HTTP 网关 |
| **ConfigMap** | 配置 KV | 应用配置 |
| **Secret** | 加密配置 | 密钥/证书 |
| **PersistentVolume(C)** | 存储卷 | 持久化 |
| **Namespace** | 资源租户 | 隔离 |
| **HPA** | 水平自动扩缩 | 弹性 |
| **NetworkPolicy** | L3/L4 策略 | 网络隔离 |
| **ResourceQuota** | 命名空间额度 | 多租户 |

## 三、Pod 速通

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
  labels: { app: web, tier: frontend }
spec:
  containers:
    - name: nginx
      image: nginx:1.27-alpine
      ports: [{ containerPort: 80 }]
      resources:
        requests: { cpu: 100m, memory: 64Mi }
        limits:   { cpu: 500m, memory: 256Mi }
      livenessProbe:
        httpGet: { path: /, port: 80 }
        initialDelaySeconds: 10
        periodSeconds: 10
      readinessProbe:
        httpGet: { path: /, port: 80 }
      env:
        - name: TZ
          value: Asia/Shanghai
  restartPolicy: Always
```

```bash
kubectl apply -f pod.yaml
kubectl get pod -o wide
kubectl describe pod web
kubectl logs -f web
kubectl exec -it web -- sh
kubectl delete pod web
```

### Pod 生命周期

```
Pending → Running → Succeeded / Failed
                  ↘ CrashLoopBackOff（异常）
                  
Init Container → Main Container → poststart hook
                                ↓
                          (run) ↓
                                ↓ preStop hook
                                ↓ SIGTERM
                                ↓ terminationGracePeriodSeconds (默认 30s)
                                ↓ SIGKILL
```

## 四、Deployment + Service + Ingress

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: web }
spec:
  replicas: 3
  selector: { matchLabels: { app: web } }
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  template:
    metadata: { labels: { app: web } }
    spec:
      containers:
        - name: nginx
          image: nginx:1.27-alpine
          readinessProbe:
            httpGet: { path: /, port: 80 }
---
apiVersion: v1
kind: Service
metadata: { name: web }
spec:
  selector: { app: web }
  ports: [{ port: 80, targetPort: 80 }]
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: 8m
spec:
  ingressClassName: nginx
  rules:
    - host: web.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service: { name: web, port: { number: 80 } }
```

```bash
kubectl rollout status deploy/web
kubectl rollout history deploy/web
kubectl rollout undo deploy/web
kubectl scale deploy/web --replicas=5
kubectl set image deploy/web nginx=nginx:1.27.1-alpine
```

### Service 4 种类型

| Type | 用途 |
|:---|:---|
| **ClusterIP** | 集群内 VIP（默认） |
| **NodePort** | 节点端口 30000-32767（测试） |
| **LoadBalancer** | 云 LB / MetalLB（生产入口） |
| **ExternalName** | DNS CNAME |
| **Headless** (clusterIP: None) | StatefulSet 用 |

## 五、ConfigMap / Secret

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: app-config }
data:
  app.yaml: |
    server: { port: 8080 }
    log: { level: info }
---
apiVersion: v1
kind: Secret
metadata: { name: app-secret }
type: Opaque
stringData:
  DB_PASSWORD: change...e_password
  TLS_CERT: |
    -----BEGIN CERTIFICATE-----
    ...
```

```yaml
# 挂载用法
spec:
  containers:
    - name: app
      envFrom:
        - secretRef: { name: app-secret }
      volumeMounts:
        - name: cfg
          mountPath: /etc/app
          readOnly: true
  volumes:
    - name: cfg
      configMap: { name: app-config }
```

Secret 默认 base64 编码 ≠ 加密。生产需配合 KMS / SealedSecrets / External Secrets / Vault（见 14_安全）。

## 六、存储 PV/PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: data }
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: ceph-rbd
  resources: { requests: { storage: 10Gi } }
---
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: mysql }
spec:
  serviceName: mysql
  replicas: 1
  selector: { matchLabels: { app: mysql } }
  template:
    metadata: { labels: { app: mysql } }
    spec:
      containers:
        - name: mysql
          image: mysql:8
          volumeMounts:
            - { name: data, mountPath: /var/lib/mysql }
  volumeClaimTemplates:
    - metadata: { name: data }
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: ceph-rbd
        resources: { requests: { storage: 20Gi } }
```

### AccessMode

```
RWO  ReadWriteOnce       单节点读写（块存储）
ROX  ReadOnlyMany        多节点只读
RWX  ReadWriteMany       多节点读写（NFS/CephFS）
RWOP ReadWriteOncePod    单 Pod 读写（1.22+）
```

## 七、RBAC

```yaml
# 给 dev 团队仅看 dev namespace
apiVersion: v1
kind: ServiceAccount
metadata: { name: dev-viewer, namespace: dev }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: viewer, namespace: dev }
rules:
  - apiGroups: ["", "apps", "batch"]
    resources: ["pods", "pods/log", "deployments", "services", "configmaps"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: viewer, namespace: dev }
subjects:
  - kind: ServiceAccount
    name: dev-viewer
    namespace: dev
roleRef:
  kind: Role
  name: viewer
  apiGroup: rbac.authorization.k8s.io
```

### 四件套

```
Role / ClusterRole              权限定义
RoleBinding / ClusterRoleBinding 绑定到 User / Group / ServiceAccount
```

## 八、kubectl 速查

```bash
# 上下文
kubectl config get-contexts
kubectl config use-context prod
kubectl config set-context --current --namespace=dev

# 资源
kubectl api-resources               # 看支持哪些
kubectl explain pod.spec.containers # 字段说明

# 查
kubectl get all -A
kubectl get pod -o wide -l app=web
kubectl get pod -o yaml
kubectl describe pod web
kubectl logs -f --tail=200 web -c sidecar
kubectl exec -it web -- sh
kubectl top pods / nodes

# 改
kubectl apply -f .
kubectl scale deploy/web --replicas=5
kubectl set image deploy/web nginx=nginx:1.27.1
kubectl edit deploy/web
kubectl patch deploy/web -p '{"spec":{"replicas":3}}'
kubectl rollout restart deploy/web

# 调
kubectl debug -it pod/web --image=busybox --target=nginx
kubectl port-forward svc/web 8080:80
kubectl cp ./file.txt web:/tmp/file.txt
kubectl exec -it web -- env

# 删
kubectl delete -f .
kubectl delete pod web --force --grace-period=0    # 强删

# 事件 / 节点
kubectl get events -A --sort-by=.lastTimestamp
kubectl get node -o wide
kubectl cordon node1    # 不再调度
kubectl drain node1 --ignore-daemonsets --delete-emptydir-data    # 驱逐
kubectl uncordon node1
```

## 九、Helm 基础

```bash
# 安装
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg
echo "deb [signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt update && sudo apt install helm

# Repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install / Upgrade
helm install web bitnami/nginx -n web --create-namespace -f values.yaml
helm upgrade --install web bitnami/nginx -n web -f values.yaml
helm uninstall web -n web
helm list -A
helm history web -n web
helm rollback web 1 -n web

# Lint / Template / Package
helm create mychart
helm lint ./mychart
helm template ./mychart > rendered.yaml
helm package ./mychart
```

## 十、调度模型

### 10.1 资源 requests/limits

```
requests  → 调度依据 (节点必须有这么多 free)
limits    → 运行硬上限 (超 CPU 节流，超 mem OOMKilled)

QoS:
  Guaranteed   requests = limits
  Burstable    requests < limits
  BestEffort   都没设 (生产禁用)
```

### 10.2 选择器 + 亲和

```yaml
spec:
  nodeSelector:
    disk: ssd
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - { key: gpu, operator: In, values: ["a100"] }
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector: { matchLabels: { app: web } }
            topologyKey: kubernetes.io/hostname
  tolerations:
    - { key: dedicated, operator: Equal, value: ai, effect: NoSchedule }
  topologySpreadConstraints:
    - maxSkew: 1
      topologyKey: topology.kubernetes.io/zone
      whenUnsatisfiable: ScheduleAnyway
      labelSelector: { matchLabels: { app: web } }
```

### 10.3 Taint / Toleration

```bash
kubectl taint nodes gpu-1 dedicated=ai:NoSchedule
```

Pod 没有匹配 toleration 不会调度到该节点。

## 十一、HPA / VPA / 健康检查

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: web }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 70 } }
    - type: Resource
      resource: { name: memory, target: { type: Utilization, averageUtilization: 80 } }
```

健康检查三件套（必备）：

```yaml
livenessProbe:    # 失败 → 重启容器
  httpGet: { path: /healthz, port: 8080 }
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:   # 失败 → 从 Service 摘除（不重启）
  httpGet: { path: /ready, port: 8080 }
  periodSeconds: 5

startupProbe:     # 启动慢应用专用，成功后才跑 liveness
  httpGet: { path: /startup, port: 8080 }
  failureThreshold: 30
  periodSeconds: 10
```

## 十二、CNI / CSI / CRI 速览

| 接口 | 实现 | 主要功能 |
|:---|:---|:---|
| **CRI** | containerd / CRI-O | 容器运行时 |
| **CNI** | Calico / Cilium / Flannel / Weave / Antrea | Pod 网络 |
| **CSI** | Ceph-CSI / Rook / Longhorn / NFS-CSI / 云厂 CSI | 存储 |
| **Device Plugin** | NVIDIA / 昇腾 / Intel SR-IOV | 异构硬件 |

新建集群默认推荐：

```
CRI: containerd ⭐
CNI: Cilium ⭐ (eBPF) 或 Calico (久经考验)
CSI: Rook-Ceph / Longhorn (HCI) / 云厂 CSI
Ingress: ingress-nginx / Higress / APISIX / Cilium Gateway
```

## 十三、必备命令排障

| 症状 | 命令 |
|:---|:---|
| Pod Pending | `kubectl describe pod` 看 Events / 资源不够 / 选择器不匹配 |
| CrashLoopBackOff | `kubectl logs --previous` |
| ImagePullBackOff | secret / mirror / 网络 |
| OOMKilled | `kubectl describe pod` Last State + 调 limit |
| Service 不通 | `kubectl get endpoints` 验证 selector |
| DNS 失败 | `kubectl exec pod -- nslookup kubernetes.default` |
| 节点 NotReady | `kubectl describe node` / kubelet log |
| etcd 慢 | `etcdctl endpoint status` 看 leader / IO |

## 十四、入门 20 题

```
1.  Pod / Deployment / Service / Ingress 关系
2.  Pod 内多容器怎么共享网络/存储
3.  Init Container vs Sidecar
4.  HostPath / EmptyDir / ConfigMap / Secret / PVC 区别
5.  ReadWriteOnce / Once / Many 各场景
6.  Service ClusterIP / NodePort / LoadBalancer 区别
7.  Ingress 与 Service 区别
8.  Headless Service 用途
9.  Liveness / Readiness / Startup 区别
10. requests / limits / QoS (Guaranteed/Burstable/BestEffort)
11. HPA 用什么指标
12. nodeSelector / nodeAffinity / podAntiAffinity 区别
13. Taint / Toleration 用途
14. RBAC 四对象
15. Rolling Update 参数 maxSurge / maxUnavailable
16. Helm 模板 + values + hooks
17. controller-manager 都管哪些控制器
18. etcd 备份命令
19. kubelet 跟 apiserver 是怎么通信的
20. CRI / CNI / CSI 接口分别由谁实现
```

## 十五、典型坑（基础）

| 坑 | 建议 |
|:---|:---|
| **没设 requests/limits** | BestEffort 上生产 = 灾难 |
| **JVM 没 -XX:+UseContainerSupport** | Java 看到 host CPU/Mem |
| **没 readinessProbe** | 服务一启动就被打流量 |
| **NodePort 暴露生产** | 用 Ingress + LoadBalancer |
| **Secret 直接 base64 当加密** | 接 KMS / Vault |
| **kubectl exec 改文件** | 全部 IaC，改要走 Git |
| **同 namespace 全资源混跑** | 至少 dev/test/prod 三隔离 |
| **etcd 没备份** | 必备 etcdctl snapshot 定时 |
| **集群版本不一致** | apiserver/kubelet/CRI 版本对齐 |
| **CNI/CSI 装错** | 节点 NotReady / Pod Pending 高频原因 |

## 十六、推荐栈

```
集群:     kubeadm / Rancher / KubeSphere / OpenShift / 云厂托管
CRI:      containerd ⭐
CNI:      Cilium (eBPF) ⭐ / Calico
Ingress:  ingress-nginx ⭐ / Higress / APISIX
存储:     Rook-Ceph / Longhorn / NFS-CSI / 云厂 CSI
监控:     Prometheus + Grafana + Loki (kube-prometheus-stack)
日志:     Fluent Bit / Vector → Loki / ELK
安全:     Falco + Kyverno/Gatekeeper + Trivy Operator
包管:     Helm + Helmfile / Kustomize
GitOps:   ArgoCD ⭐ / Flux
```

## 十七、学习路径

```
入门（1-3 月）:
  1. kubeadm 装 3 节点集群（containerd + Calico）
  2. kubectl 熟练（get/describe/logs/exec/port-forward）
  3. 部署 Deployment + Service + Ingress + ConfigMap + Secret
  4. StatefulSet + PVC + Headless Service 一套
  5. RBAC 给团队 viewer / editor 角色
  6. Helm 装 ingress-nginx + cert-manager + prometheus
  7. HPA + readinessProbe + livenessProbe 三件套
  8. 20 题过一遍

进阶（3-12 月，见 02_进阶）:
  9. CNI Cilium + NetworkPolicy
  10. Rook-Ceph 存储
  11. ArgoCD GitOps
  12. Prometheus + Loki 全链
```

> 📖 **核心判断**：K8s 基础 = **声明式 + Pod + 控制器 + Service/Ingress + RBAC + Probe + HPA**。能在 kubeadm 上装出 3 节点集群、能部署 Deployment + Service + Ingress + ConfigMap + Secret + StatefulSet + HPA + RBAC、能用 kubectl 排出 Pod Pending / CrashLoop / DNS 问题，就具备 K8s 入门。
