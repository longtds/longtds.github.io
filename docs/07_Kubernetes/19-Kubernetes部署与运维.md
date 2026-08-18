# Kubernetes 部署与运维

> K8s 怎么搭？Pod/Service/Ingress 怎么配？生产集群怎么运维？本文覆盖 K8s 全栈实践。

---

## 一、Kubernetes 架构

### 1.1 概述

```
Kubernetes (K8s) — 容器编排平台

  定位: 容器编排/调度/管理 (Container Orchestration)
  目标: 自动化部署/弹性伸缩/滚动更新/故障恢复
  模式: 声明式 API + 控制循环 (Reconcile Loop)
  生态: CNCF 毕业, 云原生事实标准

  K8s vs Docker Compose:
    Compose: 单机编排, YAML 定义多容器, docker compose up
    K8s:      多机编排, 声明式 API, 自动调度/自愈/伸缩

  K8s vs Docker Swarm:
    Swarm: 轻量, Docker 内置, 功能有限
    K8s:   重量级, 功能全面, 生态丰富

  版本发布: 每年 3 个版本 (约 15 周一个)
    2025.06: v1.32
    2025.10: v1.33
    2026.02: v1.34
    支持周期: 最近 3 个版本 (约 14 个月)
```

### 1.2 集群架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes 集群架构                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Control Plane (Master)                  │  │
│  │                                                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │  │
│  │  │  kube-      │  │  kube-      │  │   etcd      │     │  │
│  │  │  apiserver  │  │  scheduler  │  │  (KV 存储)  │     │  │
│  │  │             │  │             │  │             │     │  │
│  │  │ API 入口    │  │ Pod 调度    │  │ 集群状态    │     │  │
│  │  │ :6443       │  │             │  │ :2379/2380  │     │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │  │
│  │                                                          │  │
│  │  ┌─────────────┐  ┌─────────────┐                       │  │
│  │  │  kube-      │  │  cloud-     │                       │  │
│  │  │  controller │  │  controller │                       │  │
│  │  │  -manager   │  │  -manager   │                       │  │
│  │  │             │  │             │                       │  │
│  │  │ 节点/路由   │  │ 云厂商集成  │                       │  │
│  │  │ 副本控制    │  │ (LB/Volume) │                       │  │
│  │  └─────────────┘  └─────────────┘                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │ API (6443)                            │
│  ┌──────────────────────┼──────────────────────────────────┐  │
│  │              Worker Nodes (计算节点)                       │  │
│  │                      │                                    │  │
│  │  ┌───────────────────▼──────────────────────────────┐   │  │
│  │  │              kubelet                              │   │  │
│  │  │  节点代理: Pod 生命周期/健康检查/资源上报           │   │  │
│  │  └───────────────────┬──────────────────────────────┘   │  │
│  │                      │                                    │  │
│  │  ┌───────────────────▼──────────────────────────────┐   │  │
│  │  │           kube-proxy                              │   │  │
│  │  │  网络代理: Service 负载均衡/iptables/IPVS          │   │  │
│  │  └───────────────────┬──────────────────────────────┘   │  │
│  │                      │                                    │  │
│  │  ┌───────────────────▼──────────────────────────────┐   │  │
│  │  │           Container Runtime                       │   │  │
│  │  │  containerd / CRI-O / Docker                     │   │  │
│  │  └───────────────────┬──────────────────────────────┘   │  │
│  │                      │                                    │  │
│  │  ┌─────────┐  ┌──────┴───┐  ┌──────────┐  ┌─────────┐ │  │
│  │  │  Pod 1  │  │  Pod 2   │  │  Pod 3   │  │ Pod N   │ │  │
│  │  │┌───────┐│  │┌───────┐ │  │┌───────┐ │  │┌───────┐│ │  │
│  │  ││Ctn app││  ││Ctn app│ │  ││Ctn app│ │  ││Ctn app││ │  │
│  │  │└───────┘│  │└───────┘ │  │└───────┘ │  │└───────┘│ │  │
│  │  │┌───────┐│  │          │  │┌───────┐ │  │         │ │  │
│  │  ││Ctn log││  │          │  ││Ctn init│ │  │         │ │  │
│  │  │└───────┘│  │          │  │└───────┘ │  │         │ │  │
│  │  └─────────┘  └──────────┘  └──────────┘  └─────────┘ │  │
│  │           (pause 容器, 每个 Pod 一个)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                   插件 (Add-ons)                          │ │
│  │  CNI (网络): Calico / Flannel / Cilium / Weave           │ │
│  │  CSI (存储): CSI 驱动 (NFS/Ceph/云盘)                     │ │
│  │  DNS:       CoreDNS                                        │ │
│  │  Ingress:   Ingress-NGINX / Traefik / Envoy               │ │
│  │  监控:      Prometheus / metrics-server                   │ │
│  │  Dashboard: Kubernetes Dashboard                           │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 核心概念

```
┌─────────────────────────────────────────────────────────────────┐
│                     K8s 资源模型                                 │
│                                                                 │
│  Cluster ─┬─ Namespace ─┬─ Pod ─┬─ Container                   │
│           │              │       │                              │
│           │              │       └─ Volume (存储)               │
│           │              │                                      │
│           │              ├─ Deployment (无状态应用)              │
│           │              │    └─ ReplicaSet (副本控制)          │
│           │              │         └─ Pod × N                   │
│           │              │                                      │
│           │              ├─ StatefulSet (有状态应用)             │
│           │              │    └─ Pod × N (有序/持久标识)         │
│           │              │                                      │
│           │              ├─ DaemonSet (每节点一个)              │
│           │              │                                      │
│           │              ├─ Job / CronJob (批处理)              │
│           │              │                                      │
│           │              ├─ Service (网络抽象)                  │
│           │              │    ├─ ClusterIP (集群内)             │
│           │              │    ├─ NodePort (节点端口)            │
│           │              │    ├─ LoadBalancer (云 LB)           │
│           │              │    └─ Headless (直连 Pod)           │
│           │              │                                      │
│           │              ├─ Ingress (HTTP 路由)                │
│           │              │                                      │
│           │              ├─ ConfigMap (配置)                   │
│           │              ├─ Secret (密钥)                      │
│           │              ├─ PersistentVolume (PV)              │
│           │              ├─ PersistentVolumeClaim (PVC)        │
│           │              ├─ StorageClass (存储类)              │
│           │              ├─ HorizontalPodAutoscaler (HPA)      │
│           │              ├─ PodDisruptionBudget (PDB)          │
│           │              ├─ NetworkPolicy (网络策略)           │
│           │              └─ ServiceAccount (服务账号)          │
│           │                                                      │
│           └─ Node ─┬─ Master Node                               │
│                     └─ Worker Node                              │
└─────────────────────────────────────────────────────────────────┘

  声明式模型:
    用户提交 YAML (期望状态) → API Server → etcd
    Controller 持续对比 期望状态 vs 实际状态 → 调整 (Reconcile)
    例: Deployment replicas=3 → 某节点故障 → Controller 发现只剩 2 个 Pod → 在其他节点创建第 3 个
```

### 1.4 Pod 生命周期

```
Pod 状态:

  Pending      → 已提交, 等待调度/拉取镜像/创建
  Running      → 已启动, 至少一个容器运行中
  Succeeded    → 所有容器正常退出 (Job)
  Failed       → 至少一个容器异常退出
  Unknown      → 状态未知 (通常是与节点失联)

  Pod 启动流程:
    1. kubectl create → API Server → etcd
    2. Scheduler 选择 Node → 绑定 (binding)
    3. kubelet 接收 → 调用 CRI 创建容器
    4. Init Container 顺序执行 (可选)
    5. 主容器启动 → postStart Hook
    6. Startup Probe (启动探针, 可选)
    7. Liveness Probe (存活探针) + Readiness Probe (就绪探针)
    8. 运行中...
    9. 收到终止信号 → preStop Hook
    10. 容器停止 (SIGTERM → 超时 SIGKILL)

  Pod 重启策略 (restartPolicy):
    Always:      容器退出后总是重启 (默认, Deployment/StatefulSet/DaemonSet)
    OnFailure:   非零退出码时重启 (Job)
    Never:       不重启 (Job/CronJob)

  Pod 退出码:
    0:   正常退出
    1:   应用错误
    137: SIGKILL (OOM 或超时强杀)
    139: SIGSEGV (段错误)
    143: SIGTERM (正常终止)

  ImagePullPolicy:
    Always:      总是拉取 (latest tag 推荐)
    IfNotPresent: 本地有就不拉 (固定 tag 推荐)
    Never:       从不拉取 (只用本地镜像)
```

---

## 二、集群部署

### 2.1 部署方式对比

| 方式 | 复杂度 | 生产可用 | 适用场景 |
|:---|:---|:---|:---|
| **kubeadm** | ⭐ 中 | ⭐ 是 | **生产首选**, 官方工具 |
| Kubespray | 中 | 是 | Ansible 批量部署 |
| RKE2 | 中 | 是 | Rancher 发行版 |
| K3s | ⭐ 低 | 是 | 轻量/边缘/IoT |
| kind | ⭐ 低 | ❌ 否 | 本地开发测试 |
| minikube | ⭐ 低 | ❌ 否 | 本地学习 |
| 云托管 (EKS/GKE/ACK) | ⭐ 低 | 是 | 云上生产 |

### 2.2 kubeadm 部署

```bash
# === 环境准备 (所有节点) ===

# 1. 主机名
hostnamectl set-hostname k8s-master01
hostnamectl set-hostname k8s-worker01
hostnamectl set-hostname k8s-worker02

# /etc/hosts
cat >> /etc/hosts << 'EOF'
192.168.1.10  k8s-master01 k8s-master01.example.com
192.168.1.20  k8s-worker01 k8s-worker01.example.com
192.168.1.21  k8s-worker02 k8s-worker02.example.com
192.168.1.100 k8s-api.example.com  # HA VIP (keepalived)
EOF

# 2. 关闭 swap (K8s 要求)
swapoff -a
sed -i '/swap/s/^/#/' /etc/fstab

# 3. 内核模块
cat > /etc/modules-load.d/k8s.conf << 'EOF'
overlay
br_netfilter
EOF
modprobe overlay
modprobe br_netfilter

# 4. 内核参数
cat > /etc/sysctl.d/99-k8s.conf << 'EOF'
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sysctl -p /etc/sysctl.d/99-k8s.conf

# 5. 关闭防火墙和 SELinux
systemctl disable --now firewalld
setenforce 0
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config

# 6. 时间同步
dnf install -y chrony
systemctl enable --now chronyd

# 7. 安装 containerd
dnf install -y containerd.io

# 配置 containerd
containerd config default > /etc/containerd/config.toml
# 修改 SystemdCgroup = true
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
# 配置镜像加速
sed -i 's|config_path = ""|config_path = "/etc/containerd/certs.d"|' /etc/containerd/config.toml

mkdir -p /etc/containerd/certs.d/docker.io
cat > /etc/containerd/certs.d/docker.io/hosts.toml << 'EOF'
server = "https://registry-1.docker.io"
[host."https://docker.m.daocloud.io"]
  capabilities = ["pull", "resolve"]
EOF

systemctl enable --now containerd

# 8. 安装 kubeadm/kubelet/kubectl
cat > /etc/yum.repos.d/kubernetes.repo << 'EOF'
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.32/rpm/
enabled=1
gpgcheck=0
EOF

dnf install -y kubelet-1.32.* kubeadm-1.32.* kubectl-1.32.*
systemctl enable kubelet

# === 初始化 Master ===

# 1. 生成初始化配置
kubeadm config print init-defaults > kubeadm-config.yaml

cat > kubeadm-config.yaml << 'EOF'
apiVersion: kubeadm.k8s.io/v1beta4
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: "192.168.1.10"
  bindPort: 6443
nodeRegistration:
  criSocket: "unix:///var/run/containerd/containerd.sock"
  name: "k8s-master01"
  taints: []
---
apiVersion: kubeadm.k8s.io/v1beta4
kind: ClusterConfiguration
kubernetesVersion: "v1.32.0"
controlPlaneEndpoint: "192.168.1.10:6443"
imageRepository: "registry.k8s.io"
networking:
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
  dnsDomain: "cluster.local"
apiServer:
  certSANs:
    - "192.168.1.10"
    - "192.168.1.100"
    - "k8s-api.example.com"
  extraArgs:
    feature-gates: "AnonymousAuth=false"
    max-requests-inflight: "400"
    max-mutating-requests-inflight: "200"
controllerManager:
  extraArgs:
    horizontal-pod-autoscaler-sync-period: "15s"
    node-monitor-period: "5s"
    node-monitor-grace-period: "40s"
scheduler:
  extraArgs:
    bind-timeout: "15s"
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cgroupDriver: systemd
failSwapOn: false
maxPods: 250
kubeAPIQPS: 50
kubeAPIBurst: 100
serializeImagePulls: false
registryPullQPS: 10
registryBurst: 20
evictionHard:
  imagefs.available: "15%"
  memory.available: "100Mi"
  nodefs.available: "10%"
  nodefs.inodesFree: "5%"
---
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: "ipvs"
ipvs:
  scheduler: "lc"
  strictARP: true
EOF

# 2. 预拉取镜像
kubeadm config images pull --config kubeadm-config.yaml

# 3. 初始化!
kubeadm init --config kubeadm-config.yaml --upload-certs

# 4. 配置 kubectl
mkdir -p $HOME/.kube
cp /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

# 5. 验证
kubectl get nodes
kubectl get pods -A

# === Worker 节点加入 ===
# kubeadm init 输出的 join 命令:
kubeadm join 192.168.1.10:6443 --token <token> \
    --discovery-token-ca-cert-hash sha256:<hash>

# 如果 token 过期, 重新生成:
kubeadm token create --print-join-command

# === 安装 CNI (Calico) ===
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/tigera-operator.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/custom-resources.yaml

# 或 Flannel (更简单)
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml

# 或 Cilium (eBPF, 高性能)
curl -fsSL https://get.cilium.io | helm template cilium cilium/cilium --version 1.16.0 > cilium.yaml
kubectl apply -f cilium.yaml

# === 安装 metrics-server (kubectl top) ===
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# 注意: 生产环境需配置 TLS 证书或 --kubelet-insecure-tls (仅测试)

# === 验证集群 ===
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl get cs                    # 组件状态
kubectl cluster-info
```

### 2.3 高可用集群

```bash
# === 3 Master HA 架构 ===
#
#  ┌──────────────────────────────────────────────────────┐
#  │           HAProxy + Keepalived (VIP)                  │
#  │           VIP: 192.168.1.100:6443                     │
#  └───┬──────────┬──────────┬───────────────────────────┘
#      │          │          │
#  ┌───▼──┐  ┌───▼──┐  ┌───▼──┐
#  │M01   │  │M02   │  │M03   │
#  │.10   │  │.11   │  │.12   │
#  │API   │  │API   │  │API   │
#  │etcd  │  │etcd  │  │etcd  │
#  └──────┘  └──────┘  └──────┘
#
#  etcd 分布式一致 (Raft 协议), 3 节点容忍 1 故障

# 1. 在所有 Master 安装 HAProxy + Keepalived
dnf install -y haproxy keepalived

# 2. HAProxy 配置 (所有 Master)
cat > /etc/haproxy/haproxy.cfg << 'EOF'
global
    log /dev/log local0
    maxconn 2000

defaults
    log global
    mode tcp
    timeout connect 5s
    timeout client 50s
    timeout server 50s

frontend kube-api
    bind *:6443
    default_backend kube-api-backend

backend kube-api-backend
    balance roundrobin
    option tcp-check
    server k8s-master01 192.168.1.10:6443 check fall 3 rise 2
    server k8s-master02 192.168.1.11:6443 check fall 3 rise 2
    server k8s-master03 192.168.1.12:6443 check fall 3 rise 2
EOF

# 3. Keepalived 配置
# Master01 (MASTER)
cat > /etc/keepalived/keepalived.conf << 'EOF'
global_defs {
    router_id K8S_HA
}
vrrp_script check_haproxy {
    script "killall -0 haproxy"
    interval 3
    weight -2
}
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass K8sHaPass2026
    }
    virtual_ipaddress {
        192.168.1.100/24
    }
    track_script {
        check_haproxy
    }
}
EOF

# Master02/03 (BACKUP, priority 90/80)
# state BACKUP, priority 90/80

# 4. 启动
systemctl enable --now haproxy keepalived

# 5. 初始化第一个 Master (使用 VIP)
# kubeadm-config.yaml:
# controlPlaneEndpoint: "192.168.1.100:6443"

kubeadm init --config kubeadm-config.yaml --upload-certs

# 6. 其他 Master 加入 (control-plane)
kubeadm join 192.168.1.100:6443 \
    --token <token> \
    --discovery-token-ca-cert-hash sha256:<hash> \
    --control-plane --certificate-key <key>

# 7. Worker 加入
kubeadm join 192.168.1.100:6443 \
    --token <token> \
    --discovery-token-ca-cert-hash sha256:<hash>
```

### 2.4 K3s 轻量部署

```bash
# === K3s (轻量级 K8s, 适合边缘/开发/小集群) ===

# 1. 安装 Server
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.32.0+k3s1" sh -s - server \
    --token=K3sToken2026 \
    --data-dir=/data/k3s \
    --disable=traefik \
    --node-ip=192.168.1.10 \
    --flannel-backend=vxlan

# 2. 获取 kubeconfig
cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sed -i 's/127.0.0.1/192.168.1.10/' ~/.kube/config

# 3. Worker 加入
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.32.0+k3s1" K3S_URL=https://192.168.1.10:6443 \
    K3S_TOKEN=K3sToken2026 sh -

# 4. 验证
k3s kubectl get nodes

# K3s 特点:
# - 单二进制 (~70MB), 内含 containerd + Flannel + CoreDNS
# - 内置 SQLite (单机) 或 etcd/MySQL (HA)
# - 默认启用 Traefik Ingress
# - 完全兼容 K8s API
```

---

## 三、工作负载

### 3.1 Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: production
  labels:
    app: web
    tier: frontend
spec:
  replicas: 3
  revisionHistoryLimit: 10           # 保留 10 个旧版本
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1                    # 滚动更新时, 最多多创建 1 个 Pod
      maxUnavailable: 0              # 滚动更新时, 不允许减少 Pod
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
        tier: frontend
    spec:
      affinity:
        podAntiAffinity:             # Pod 反亲和 (分散到不同节点)
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: web
                topologyKey: kubernetes.io/hostname
      containers:
        - name: web
          image: registry.example.com/web:1.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
              name: http
              protocol: TCP
          env:
            - name: PROFILE
              value: "prod"
            - name: DB_HOST
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: db_host
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: password
          envFrom:
            - configMapRef:
                name: app-config
          resources:
            requests:                # 调度依据 (保证最小资源)
              cpu: "500m"
              memory: "512Mi"
            limits:                  # 硬限制 (不能超过)
              cpu: "1000m"
              memory: "1Gi"
          livenessProbe:             # 存活探针 (失败重启)
            httpGet:
              path: /actuator/health/liveness
              port: 8080
            initialDelaySeconds: 60
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:            # 就绪探针 (失败摘除流量)
            httpGet:
              path: /actuator/health/readiness
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 3
          startupProbe:              # 启动探针 (慢启动应用)
            httpGet:
              path: /actuator/health
              port: 8080
            failureThreshold: 30
            periodSeconds: 10
          lifecycle:
            preStop:                 # 优雅停止
              exec:
                command: ["sh", "-c", "sleep 15 && curl -X POST http://localhost:8080/shutdown"]
          volumeMounts:
            - name: config
              mountPath: /app/config
              readOnly: true
            - name: logs
              mountPath: /app/logs
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: config
          configMap:
            name: app-config
        - name: logs
          persistentVolumeClaim:
            claimName: app-logs-pvc
        - name: tmp
          emptyDir:
            medium: Memory
            sizeLimit: 100Mi
      terminationGracePeriodSeconds: 60
      imagePullSecrets:
        - name: registry-secret
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
```

### 3.2 StatefulSet

```yaml
# statefulset.yaml — 有状态应用 (数据库/MQ)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
  namespace: production
spec:
  serviceName: mysql-headless       # 必须指定 Headless Service
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:8.0
          ports:
            - containerPort: 3306
              name: mysql
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: root-password
          resources:
            requests:
              cpu: "1000m"
              memory: "2Gi"
            limits:
              cpu: "2000m"
              memory: "4Gi"
          volumeMounts:
            - name: data
              mountPath: /var/lib/mysql
  volumeClaimTemplates:             # 每个 Pod 独立 PVC
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ceph-rbd
        resources:
          requests:
            storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
spec:
  clusterIP: None                   # Headless (无 ClusterIP)
  selector:
    app: mysql
  ports:
    - port: 3306
      name: mysql

# StatefulSet 特点:
# - Pod 有序: mysql-0, mysql-1, mysql-2 (顺序创建/删除)
# - 持久标识: Pod 重建后名称不变, DNS 不变
# - 独立存储: 每个 Pod 有独立 PVC (不会混淆)
# - DNS: mysql-0.mysql-headless, mysql-1.mysql-headless
# - 适用: MySQL/PostgreSQL/Redis Cluster/Kafka/ES/ZooKeeper
```

### 3.3 DaemonSet / Job / CronJob

```yaml
# daemonset.yaml — 每个节点运行一个 Pod
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: filebeat
  template:
    metadata:
      labels:
        app: filebeat
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          effect: NoSchedule        # 允许在 Master 运行
      containers:
        - name: filebeat
          image: docker.elastic.co/beats/filebeat:8.14.0
          volumeMounts:
            - name: varlog
              mountPath: /var/log
              readOnly: true
            - name: varlibdockercontainers
              mountPath: /var/lib/docker/containers
              readOnly: true
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: varlibdockercontainers
          hostPath:
            path: /var/lib/docker/containers
```

```yaml
# cronjob.yaml — 定时任务
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
  namespace: production
spec:
  schedule: "0 2 * * *"             # 每天 2:00 AM
  timeZone: "Asia/Shanghai"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
  concurrencyPolicy: Forbid          # 禁止并发执行
  startingDeadlineSeconds: 200
  jobTemplate:
    spec:
      backoffLimit: 3               # 失败重试 3 次
      activeDeadlineSeconds: 3600   # 最长运行 1 小时
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: backup
              image: registry.example.com/backup:1.0.0
              command:
                - /bin/sh
                - -c
                - |
                  mysqldump -h mysql -u root -p$DB_PASSWORD \
                    --all-databases --single-transaction | \
                    gzip > /backup/db-$(date +%Y%m%d).sql.gz
              env:
                - name: DB_PASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: mysql-secret
                      key: root-password
              volumeMounts:
                - name: backup
                  mountPath: /backup
          volumes:
            - name: backup
              persistentVolumeClaim:
                claimName: backup-pvc
```

---

## 四、网络

### 4.1 Service

```yaml
# === ClusterIP (集群内访问, 默认) ===
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
    - port: 80                       # Service 端口
      targetPort: 8080               # Pod 端口
      protocol: TCP
      name: http
---
# === NodePort (节点端口, 外部可访问) ===
apiVersion: v1
kind: Service
metadata:
  name: web-app-np
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080                # 30000-32767
---
# === LoadBalancer (云 LB, 云环境) ===
apiVersion: v1
kind: Service
metadata:
  name: web-app-lb
spec:
  type: LoadBalancer
  loadBalancerClass: service.k8s.aws/nlb  # 云厂商 LB
  selector:
    app: web
  ports:
    - port: 443
      targetPort: 8080
---
# === Headless (直连 Pod, 用于 StatefulSet) ===
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
spec:
  clusterIP: None
  selector:
    app: mysql
  ports:
    - port: 3306

# Service 流量路径:
#   Client → ClusterIP:Port → kube-proxy(iptables/IPVS) → Pod:targetPort
#
# ClusterIP:    虚拟 IP, 集群内可达, 外部不可达
# NodePort:     在所有节点开端口 (30000-32767), 外部可达
# LoadBalancer: 云厂商提供外部 LB → NodePort → Pod
# Headless:     无 ClusterIP, DNS 直接返回 Pod IP
```

### 4.2 Ingress

```yaml
# === Ingress (HTTP/HTTPS 路由) ===
# 需要安装 Ingress Controller (如 Ingress-NGINX)

# 安装 Ingress-NGINX
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml

# Ingress 规则
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "X-Frame-Options: DENY";
      more_set_headers "X-Content-Type-Options: nosniff";
    nginx.ingress.kubernetes.io/rate-limit-connections: "10"
    nginx.ingress.kubernetes.io/rate-limit-requests: "100"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.example.com
        - app.example.com
      secretName: example-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80
    - host: app.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-service
                port:
                  number: 80

# Ingress 流量路径:
#   外部 DNS → Ingress Controller(NodePort/LoadBalancer) → Ingress 规则匹配 → Service → Pod
#
# Ingress vs Service:
#   Service:    L4 (TCP/UDP), 端口转发
#   Ingress:    L7 (HTTP/HTTPS), 域名/路径路由, TLS 终止
```

### 4.3 NetworkPolicy

```yaml
# === NetworkPolicy (网络隔离) ===
# 需 CNI 支持 (Calico/Cilium 支持, Flannel 不支持)

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # 允许 Ingress Controller 命名空间访问
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
    # 允许 monitoring 命名空间抓取指标
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
      ports:
        - protocol: TCP
          port: 9090
  egress:
    # 允许 DNS
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    # 允许访问数据库
    - to:
        - podSelector:
            matchLabels:
              app: mysql
      ports:
        - protocol: TCP
          port: 3306
    # 允许访问外部 API
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
      ports:
        - protocol: TCP
          port: 443
```

### 4.4 CNI 对比

| CNI | 模式 | 性能 | NetworkPolicy | 特点 |
|:---|:---|:---|:---|:---|
| **Calico** | BGP/VXLAN | ⭐ 高 | ⭐ 完整 | 生产首选, BGP 路由 |
| **Cilium** | eBPF | ⭐⭐ 最高 | ⭐ 完整 | eBPF, 无 iptables, 可观测 |
| Flannel | VXLAN/host-gw | 中 | ❌ 不支持 | 简单, 轻量 |
| Weave | VXLAN | 中 | 部分 | 加密支持 |
| Antrea | OVS | 高 | 完整 | VMware, OVS 数据面 |

---

## 五、存储

### 5.1 存储体系

```
K8s 存储体系:

  ┌──────────────────────────────────────────────────────────┐
  │                    应用层                                 │
  │  Pod → Volume → (PVC 引用)                               │
  └──────────────────────┬───────────────────────────────────┘
                         │
  ┌──────────────────────▼───────────────────────────────────┐
  │              PersistentVolumeClaim (PVC)                  │
  │  用户对存储的请求: 大小/读写模式/存储类                    │
  └──────────────────────┬───────────────────────────────────┘
                         │
  ┌──────────────────────▼───────────────────────────────────┐
  │              PersistentVolume (PV)                        │
  │  集群中的存储资源: NFS/Ceph/云盘/本地盘                    │
  │  静态: 管理员手动创建                                      │
  │  动态: StorageClass 自动创建                               │
  └──────────────────────┬───────────────────────────────────┘
                         │
  ┌──────────────────────▼───────────────────────────────────┐
  │              StorageClass (SC)                            │
  │  存储类: 定义后端/参数/回收策略                             │
  │  → CSI 驱动 → 真实存储 (Ceph/NFS/云盘)                    │
  └──────────────────────────────────────────────────────────┘

  访问模式 (accessModes):
    ReadWriteOnce (RWO):   单节点读写 (默认, 块存储)
    ReadOnlyMany (ROX):    多节点只读
    ReadWriteMany (RWX):   多节点读写 (NFS/CephFS)
    ReadWriteOncePod:      单 Pod 读写 (K8s 1.22+)

  回收策略 (reclaimPolicy):
    Retain:    PVC 删除后, PV 保留 (需手动清理)
    Delete:    PVC 删除后, PV 自动删除 (动态供应)

  绑定策略 (volumeBindingMode):
    Immediate:  立即绑定 (创建 PVC 就绑定)
    WaitForFirstConsumer: 等待 Pod 调度后再绑定 (推荐, 拓扑感知)
```

### 5.2 存储配置

```yaml
# === StorageClass (动态供应) ===

# Ceph RBD (块存储)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ceph-rbd
provisioner: ceph.csi.ceph.com
parameters:
  clusterID: <ceph-cluster-id>
  pool: kubernetes
  imageFormat: "2"
  imageFeatures: "layering"
  csi.storage.k8s.io/provisioner-secret-name: ceph-secret
  csi.storage.k8s.io/provisioner-secret-namespace: kube-system
  csi.storage.k8s.io/node-stage-secret-name: ceph-secret
  csi.storage.k8s.io/node-stage-secret-namespace: kube-system
  csi.storage.k8s.io/controller-expand-secret-name: ceph-secret
  csi.storage.k8s.io/controller-expand-secret-namespace: kube-system
reclaimPolicy: Retain
allowVolumeExpansion: true          # 允许扩容
volumeBindingMode: WaitForFirstConsumer
mountOptions:
  - discard
---
# NFS
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs
provisioner: nfs.csi.k8s.io
parameters:
  server: 192.168.1.20
  share: /data/nfs
reclaimPolicy: Retain
volumeBindingMode: Immediate
---
# 本地存储 (Local Persistent Volume)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
---
# === PVC ===
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ceph-rbd
  resources:
    requests:
      storage: 50Gi
---
# RWX (多 Pod 共享, NFS/CephFS)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: nfs
  resources:
    requests:
      storage: 100Gi
---
# === Pod 使用 PVC ===
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: my-app:1.0.0
      volumeMounts:
        - name: data
          mountPath: /app/data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: app-data
```

### 5.3 其他存储类型

```yaml
# === ConfigMap (配置文件) ===
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  application.yml: |
    server:
      port: 8080
    spring:
      datasource:
        url: jdbc:mysql://mysql:3306/myapp
  nginx.conf: |
    server {
      listen 80;
      location / {
        proxy_pass http://web:80;
      }
    }
---
# Pod 挂载 ConfigMap
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: my-app:1.0.0
      envFrom:
        - configMapRef:
            name: app-config
      volumeMounts:
        - name: config
          mountPath: /app/config/application.yml
          subPath: application.yml
  volumes:
    - name: config
      configMap:
        name: app-config

---
# === Secret (密钥) ===
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  password: "MyDbPassword2026!"
  username: "appuser"
# 或使用 data (base64 编码)
# data:
#   password: TXlEYlBhc3N3b3JkMjAyNiE=
---
# docker registry Secret
apiVersion: v1
kind: Secret
metadata:
  name: registry-secret
type: kubernetes.io/dockerconfigjson
stringData:
  .dockerconfigjson: |
    {"auths":{"registry.example.com":{"username":"admin","password":"***"
---
# === emptyDir (临时存储, Pod 删除后消失) ===
volumes:
  - name: cache
    emptyDir:
      medium: Memory                # 用内存 (tmpfs)
      sizeLimit: 100Mi
---
# === hostPath (挂载宿主机路径, 谨慎使用) ===
volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
      type: Socket
```

---

## 六、调度与伸缩

### 6.1 调度

```yaml
# === 节点选择器 (简单) ===
spec:
  nodeSelector:
    disktype: ssd
    zone: east

---
# === Node Affinity (高级节点选择) ===
spec:
  affinity:
    nodeAffinity:
      # 硬约束 (必须满足)
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/arch
                operator: In
                values: ["amd64"]
              - key: node.kubernetes.io/instance-type
                operator: In
                values: ["large", "xlarge"]
      # 软约束 (尽量满足)
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          preference:
            matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values: ["east-1a"]

---
# === Pod Affinity/Anti-Affinity (Pod 间关系) ===
spec:
  affinity:
    # Pod 亲和 (调度到有指定 Pod 的节点)
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: cache
          topologyKey: kubernetes.io/hostname
    # Pod 反亲和 (调度到没有指定 Pod 的节点)
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchLabels:
                app: web
            topologyKey: kubernetes.io/hostname

---
# === Taint & Toleration (污点/容忍) ===
# 节点加 Taint (排斥 Pod)
kubectl taint nodes worker01 gpu=true:NoSchedule
# Taint 效果:
#   NoSchedule:       不调度新 Pod
#   PreferNoSchedule: 尽量不调度
#   NoExecute:        驱逐已有 Pod

# Pod 加 Toleration (容忍 Taint)
spec:
  tolerations:
    - key: "gpu"
      operator: "Equal"
      value: "true"
      effect: "NoSchedule"
    - key: "node-role.kubernetes.io/control-plane"
      operator: "Exists"
      effect: "NoSchedule"

---
# === Topology Spread (拓扑分布) ===
spec:
  topologySpreadConstraints:
    - maxSkew: 1                    # 各域最多差 1 个 Pod
      topologyKey: topology.kubernetes.io/zone
      whenUnsatisfiable: DoNotSchedule  # 或 ScheduleAnyway
      labelSelector:
        matchLabels:
          app: web
    - maxSkew: 1
      topologyKey: kubernetes.io/hostname
      whenUnsatisfiable: ScheduleAnyway
      labelSelector:
        matchLabels:
          app: web

---
# === Resource Quota (命名空间配额) ===
apiVersion: v1
kind: ResourceQuota
metadata:
  name: prod-quota
  namespace: production
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "20"
    services: "10"
    pods: "50"
    configmaps: "20"
    secrets: "20"
---
# === LimitRange (默认资源限制) ===
apiVersion: v1
kind: LimitRange
metadata:
  name: prod-limits
  namespace: production
spec:
  limits:
    - type: Pod
      max:
        cpu: "4"
        memory: 8Gi
      min:
        cpu: "100m"
        memory: 128Mi
    - type: Container
      default:                      # 默认 limits
        cpu: "500m"
        memory: 512Mi
      defaultRequest:               # 默认 requests
        cpu: "100m"
        memory: 128Mi
      max:
        cpu: "4"
        memory: 8Gi
      min:
        cpu: "50m"
        memory: 64Mi
```

### 6.2 HPA / VPA

```yaml
# === HPA (水平自动伸缩) ===
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 3
  maxReplicas: 20
  metrics:
    # CPU 使用率
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70    # CPU > 70% 扩容
    # 内存使用率
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    # 自定义指标 (需 Prometheus Adapter)
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"      # 每秒 1000 请求扩容
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0   # 立即扩容
      policies:
        - type: Percent
          value: 100                 # 每次最多翻倍
          periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 300  # 5 分钟稳定后才缩容
      policies:
        - type: Percent
          value: 10                  # 每次最多缩 10%
          periodSeconds: 60

---
# === VPA (垂直自动伸缩, 需安装 VPA 组件) ===
# 自动调整 Pod 的 CPU/内存 requests/limits
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  updatePolicy:
    updateMode: Auto                # Off/Initial/Auto
  resourcePolicy:
    containerPolicies:
      - containerName: '*'
        minAllowed:
          cpu: 100m
          memory: 128Mi
        maxAllowed:
          cpu: "4"
          memory: 8Gi
```

### 6.3 Cluster Autoscaler / Karpenter

```bash
# === Cluster Autoscaler (节点自动伸缩) ===
# 云环境: ASG (AWS) / VMSS (Azure) / VNG (阿里云)

# 安装 (AWS 示例)
helm install cluster-autoscaler autoscaler/cluster-autoscaler \
  --namespace kube-system \
  --set autoDiscovery.clusterName=my-cluster \
  --set awsRegion=us-east-1 \
  --set image.tag=v1.32.0

# 原理:
#   Pod Pending (资源不足) → CA 触发扩容节点 → Pod 调度成功
#   节点利用率低 → CA 缩容节点 (迁移 Pod 后删除)

# === Karpenter (更快的节点伸缩, AWS) ===
helm install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --namespace karpenter \
  --create-namespace

# NodePool (替代 ASG)
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m"]
        - key: karpenter.k8s.aws/instance-cpu
          operator: In
          values: ["4", "8", "16"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  limits:
    cpu: 100
    memory: 200Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s
```

---

## 七、安全

### 7.1 RBAC

```yaml
# === ServiceAccount ===
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: production
---
# === Role (命名空间级) ===
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create"]
---
# === RoleBinding ===
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-pod-reader
  namespace: production
subjects:
  - kind: ServiceAccount
    name: app-sa
    namespace: production
  - kind: User
    name: dev-user
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
---
# === ClusterRole (集群级) ===
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "watch"]
---
# === ClusterRoleBinding ===
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-node-reader
subjects:
  - kind: User
    name: admin
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

### 7.2 Pod Security

```yaml
# === Pod Security Standards (PSS) ===
# 命名空间级安全策略 (替代旧 PodSecurityPolicy)

# 三个级别:
#   privileged:  不限制 (特权)
#   baseline:    基线 (禁止最危险操作)
#   restricted:  严格 (推荐生产)

# 命名空间标签启用 PSS
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest

---
# === Pod SecurityContext ===
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
spec:
  securityContext:
    runAsNonRoot: true              # 必须 非 root
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    fsGroupChangePolicy: OnRootMismatch
    seccompProfile:                 # 系统调用过滤
      type: RuntimeDefault
    supplementalGroups: [1000]
  containers:
    - name: app
      image: my-app:1.0.0
      securityContext:
        allowPrivilegeEscalation: false  # 禁止提权
        readOnlyRootFilesystem: true     # 只读根文件系统
        runAsNonRoot: true
        runAsUser: 1000
        capabilities:                  # 丢弃所有能力
          drop:
            - ALL
          add:
            - NET_BIND_SERVICE
        seccompProfile:
          type: RuntimeDefault
      volumeMounts:
        - name: tmp
          mountPath: /tmp             # 只读根 FS 需要 tmpfs 写临时文件
  volumes:
    - name: tmp
      emptyDir:
        medium: Memory
```

### 7.3 证书与认证

```bash
# === kubeconfig 管理 ===
# 查看当前 context
kubectl config current-context

# 查看 cluster
kubectl config get-clusters

# 切换 context
kubectl config use-context prod-context

# 创建新用户证书
openssl genrsa -out dev-user.key 2048
openssl req -new -key dev-user.key -out dev-user.csr \
    -subj "/CN=dev-user/O=development"

# 用 K8s CA 签名
openssl x509 -req -in dev-user.csr \
    -CA /etc/kubernetes/pki/ca.crt \
    -CAkey /etc/kubernetes/pki/ca.key \
    -CAcreateserial -out dev-user.crt -days 365

# 创建 kubeconfig
kubectl config set-cluster k8s-cluster \
    --server=https://192.168.1.10:6443 \
    --certificate-authority=/etc/kubernetes/pki/ca.crt \
    --embed-certs=true \
    --kubeconfig=/tmp/dev-user.kubeconfig

kubectl config set-credentials dev-user \
    --client-certificate=dev-user.crt \
    --client-key=dev-user.key \
    --embed-certs=true \
    --kubeconfig=/tmp/dev-user.kubeconfig

kubectl config set-context dev-context \
    --cluster=k8s-cluster \
    --user=dev-user \
    --namespace=development \
    --kubeconfig=/tmp/dev-user.kubeconfig

kubectl config use-context dev-context --kubeconfig=/tmp/dev-user.kubeconfig

# === ServiceAccount Token ===
# K8s 1.24+ 不再自动为 SA 创建 Secret
# 需要手动创建 Token Secret
apiVersion: v1
kind: Secret
metadata:
  name: app-sa-token
  annotations:
    kubernetes.io/service-account.name: app-sa
type: kubernetes.io/service-account-token

# === 证书过期检查 ===
kubeadm certs check-expiration

# 续期 (所有 Master)
kubeadm certs renew all
systemctl restart kube-apiserver kube-controller-manager kube-scheduler etcd

# === 审计日志 ===
# /etc/kubernetes/manifests/kube-apiserver.yaml 添加:
# - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
# - --audit-log-path=/var/log/kubernetes/audit/audit.log
# - --audit-log-maxage=30
# - --audit-log-maxbackup=10
# - --audit-log-maxsize=100
```

---

## 八、Helm 包管理

### 8.1 Helm 基础

```bash
# === 安装 ===
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 添加仓库
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add jetstack https://charts.jetstack.io
helm repo update

# 搜索
helm search repo nginx
helm search hub redis

# === 安装 Chart ===
helm install my-nginx bitnami/nginx \
    --namespace web \
    --create-namespace \
    --version 15.0.0 \
    --set service.type=ClusterIP \
    --set resources.requests.cpu=100m \
    --set resources.requests.memory=128Mi

# 自定义 values
helm install my-app ./my-chart -f values.yaml -f values-prod.yaml

# === 管理 ===
helm list -A
helm status my-nginx -n web
helm get values my-nginx -n web
helm get manifest my-nginx -n web
helm history my-nginx -n web
helm rollback my-nginx 1 -n web          # 回滚到版本 1
helm upgrade my-nginx bitnami/nginx -f values.yaml -n web
helm uninstall my-nginx -n web

# === 模板渲染 (调试) ===
helm template my-app ./my-chart -f values.yaml
helm lint ./my-chart                     # 语法检查
```

### 8.2 自定义 Chart

```bash
# 创建 Chart
helm create my-app
```

```yaml
# my-app/Chart.yaml
apiVersion: v2
name: my-app
description: My Application Helm Chart
type: application
version: 1.0.0
appVersion: "1.0.0"
dependencies:
  - name: mysql
    version: 9.x.x
    repository: https://charts.bitnami.com/bitnami
    condition: mysql.enabled
```

```yaml
# my-app/values.yaml
replicaCount: 3

image:
  repository: registry.example.com/my-app
  pullPolicy: IfNotPresent
  tag: "1.0.0"

resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: app.example.com
      paths:
        - path: /
          pathType: Prefix

mysql:
  enabled: true
  auth:
    rootPassword: "RootPass2026!"
    database: myapp
```

```yaml
# my-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "my-app.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "my-app.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          {{- with .Values.env }}
          env:
            {{- toYaml . | nindent 12 }}
          {{- end }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

---

## 九、监控

### 9.1 Prometheus + Grafana

```yaml
# === kube-prometheus-stack (一站式监控) ===
# helm install monitoring prometheus-community/kube-prometheus-stack

# prometheus-values.yaml
prometheus:
  prometheusSpec:
    retention: 30d
    retentionSize: 50GB
    scrapeInterval: 30s
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: ceph-rbd
          resources:
            requests:
              storage: 100Gi
    additionalScrapeConfigs:
      - job_name: 'my-app'
        metrics_path: /actuator/prometheus
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            regex: my-app
            action: keep
          - source_labels: [__meta_kubernetes_pod_ip]
            target_label: __address__
            replacement: "$1:8080"

alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: ceph-rbd
          resources:
            requests:
              storage: 10Gi

grafana:
  adminPassword: "GrafanaAdmin2026!"
  persistence:
    enabled: true
    storageClassName: ceph-rbd
    size: 10Gi
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
        - name: 'default'
          folder: 'Default'
          type: file
          options:
            path: /var/lib/grafana/dashboards
  dashboards:
    default:
      k8s-cluster:
        gnetId: 7249
        revision: 1
      pods:
        gnetId: 6336
        revision: 1
```

```yaml
# === 告警规则 ===
# PrometheusRule
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: k8s-alerts
  namespace: monitoring
spec:
  groups:
    - name: k8s
      rules:
        - alert: NodeDown
          expr: up{job="node-exporter"} == 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Node {{ $labels.instance }} is down"
            description: "{{ $labels.instance }} has been down for more than 5 minutes."

        - alert: PodCrashLooping
          expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Pod {{ $labels.pod }} is crash looping"

        - alert: HighCPU
          expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
          for: 10m
          labels:
            severity: warning

        - alert: HighMemory
          expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
          for: 5m
          labels:
            severity: warning

        - alert: DiskFull
          expr: (1 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"})) * 100 > 85
          for: 5m
          labels:
            severity: critical

        - alert: PVCAlmostFull
          expr: kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes * 100 > 85
          for: 5m
          labels:
            severity: warning
```

### 9.2 日志 (Loki)

```yaml
# === Loki + Promtail (日志收集) ===
# helm install loki grafana/loki-stack

# promtail-values.yaml
promtail:
  config:
    clients:
      - url: http://loki:3100/loki/api/v1/push
    snippets:
      extraScrapeConfigs: |
        - job_name: k8s-containers
          kubernetes_sd_configs:
            - role: pod
          pipeline_stages:
            - cri: {}
            - labels:
                app:
                namespace:
                container:
            - output:
                source: message
          relabel_configs:
            - source_labels: [__meta_kubernetes_pod_label_app]
              target_label: app
            - source_labels: [__meta_kubernetes_namespace]
              target_label: namespace

# 查询 (Grafana):
# {namespace="production", app="web-app"} |= "error"
# {namespace="production"} | json | line_format "{{.level}} {{.msg}}"
# rate({app="web-app"}[5m])
```

### 9.3 日常巡检

```bash
# === 集群状态 ===
kubectl get nodes -o wide
kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,VERSION:.status.nodeInfo.kubeletVersion
kubectl top nodes
kubectl top pods -A --sort-by=cpu

# === 组件健康 ===
kubectl get cs
kubectl get pods -n kube-system
kubectl get pods -A --field-selector=status.phase!=Running
kubectl get events -A --sort-by=.lastTimestamp | tail -20

# === 证书 ===
kubeadm certs check-expiration

# === etcd ===
# 查看 etcd 状态
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
    --cacert=/etc/kubernetes/pki/etcd/ca.crt \
    --cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt \
    --key=/etc/kubernetes/pki/etcd/healthcheck-client.key \
    endpoint status --write-out=table

# etcd 备份
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%Y%m%d).db \
    --endpoints=https://127.0.0.1:2379 \
    --cacert=/etc/kubernetes/pki/etcd/ca.crt \
    --cert=/etc/kubernetes/pki/etcd/server.crt \
    --key=/etc/kubernetes/pki/etcd/server.key

# etcd 恢复
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-20260711.db \
    --data-dir=/var/lib/etcd-restored
```

---

## 十、故障排查

### 10.1 常见问题

| 问题 | 排查 | 解决 |
|:---|:---|:---|
| Pod Pending | 调度失败/资源不足 | `kubectl describe pod` 看 Events |
| Pod CrashLoopBackOff | 容器崩溃/配置错误 | 查日志 `kubectl logs` |
| Pod ImagePullBackOff | 镜像拉取失败 | 检查镜像名/registry/secret |
| Pod OOMKilled | 内存不足 | 增加 limits.memory/查内存泄漏 |
| Service 不通 | 标签不匹配/端口错误 | `kubectl get endpoints` 检查 |
| Node NotReady | kubelet 故障/资源耗尽 | `kubectl describe node` |
| PVC Pending | 无可用 PV/StorageClass | 检查 SC/后端存储 |
| API Server 慢 | etcd 性能/大量请求 | 检查 etcd 磁盘/限流 |
| DNS 解析失败 | CoreDNS 故障 | `kubectl logs -n kube-system` |
| 证书过期 | 集群不可用 | `kubeadm certs renew` |

### 10.2 诊断命令

```bash
# === Pod 诊断 ===
kubectl describe pod <pod-name>                    # 事件/状态
kubectl logs <pod-name>                            # 当前日志
kubectl logs <pod-name> --previous                 # 上次崩溃日志
kubectl logs -f <pod-name> -c <container-name>     # 跟踪日志
kubectl get pod <pod-name> -o yaml                 # 完整 YAML
kubectl exec -it <pod-name> -- sh                  # 进入容器

# === 调试 ===
# 临时调试容器 (Ephemeral Container)
kubectl alpha debug <pod-name> --image=busybox --target=<container-name>

# 临时 Pod (网络调试)
kubectl run debug --rm -it --image=nicolaka/netshoot -- bash
# 在 debug Pod 中:
dig kubernetes.default.svc.cluster.local
curl http://web-app:80
nslookup mysql-headless
tcpdump -i eth0

# === Node 诊断 ===
kubectl describe node <node-name>
kubectl describe node <node-name> | grep -A5 "Allocated"
kubectl get events --field-selector involvedObject.kind=Node

# 节点上的诊断
journalctl -u kubelet --since "1 hour ago"
journalctl -u containerd --since "1 hour ago"
crictl ps
crictl logs <container-id>
crictl inspect <container-id>

# === 集群诊断 ===
kubectl get componentstatuses
kubectl cluster-info dump
kubectl get apiservices | grep False
kubectl get validatingwebhookconfigurations
kubectl get mutatingwebhookconfigurations

# === 网络诊断 ===
kubectl get svc --all-namespaces
kubectl get endpoints --all-namespaces
kubectl get networkpolicy --all-namespaces

# iptables (kube-proxy)
iptables-save | grep <service-name>
iptables -t nat -L -n -v

# CoreDNS
kubectl logs -n kube-system -l k8s-app=kube-dns
kubectl get configmap coredns -n kube-system -o yaml
# 测试 DNS
kubectl run dns-test --rm -it --image=busybox -- nslookup kubernetes.default

# === 存储诊断 ===
kubectl get pv
kubectl get pvc --all-namespaces
kubectl get sc
kubectl describe pvc <pvc-name>

# === 清理 ===
# 删除已完成 Pod
kubectl delete pods --field-selector status.phase=Succeeded -A
kubectl delete pods --field-selector status.phase=Failed -A

# 清理 Evicted Pod
kubectl delete pods --field-selector status.phase=Failed -A
kubectl get pods -A | grep Evicted | awk '{print $2 " --namespace=" $1}' | xargs -n2 kubectl delete pod
```

---

## 十一、运维操作

### 11.1 节点维护

```bash
# === 节点维护 (驱逐 + 停止调度) ===

# 1. 标记为不可调度
kubectl cordon <node-name>

# 2. 驱逐 Pod
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data --force

# 3. 维护 (升级内核/重启等)
ssh <node-name>
dnf update -y
reboot

# 4. 恢复
kubectl uncordon <node-name>

# === 节点升级 ===
# 1. 驱逐节点
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# 2. 升级 kubelet/kubeadm
dnf upgrade kubelet-1.32.* kubeadm-1.32.* -y

# 3. 升级节点配置
kubeadm upgrade node

# 4. 重启 kubelet
systemctl daemon-reload
systemctl restart kubelet

# 5. 恢复调度
kubectl uncordon <node-name>
```

### 11.2 集群升级

```bash
# === 集群升级 (逐节点滚动升级) ===

# 1. 升级 kubeadm
dnf upgrade kubeadm-1.33.* -y

# 2. 升级第一个 Master
kubeadm upgrade plan
kubeadm upgrade apply v1.33.0

# 3. 升级其他 Master
kubeadm upgrade node

# 4. 升级所有节点 kubelet/kubectl
dnf upgrade kubelet-1.33.* kubectl-1.33.* -y
systemctl daemon-reload
systemctl restart kubelet

# 5. 验证
kubectl get nodes
# 所有节点 Ready + 版本一致

# 升级原则:
# - 一次只升级一个小版本 (1.32 → 1.33, 不跳版本)
# - 先升级 Master, 后升级 Worker
# - 逐个节点升级 (drain → upgrade → uncordon)
# - 升级前备份 etcd
```

### 11.3 备份与恢复

```bash
# === etcd 备份 (最重要!) ===
# etcd 是集群唯一有状态组件, 备份 etcd = 备份整个集群

# 定时备份脚本
cat > /opt/k8s-backup/etcd-backup.sh << 'BASH'
#!/bin/bash
BACKUP_DIR=/data/backup/etcd
DATE=$(date +%Y%m%d-%H%M)
mkdir -p $BACKUP_DIR

ETCDCTL_API=3 etcdctl snapshot save $BACKUP_DIR/etcd-$DATE.db \
    --endpoints=https://127.0.0.1:2379 \
    --cacert=/etc/kubernetes/pki/etcd/ca.crt \
    --cert=/etc/kubernetes/pki/etcd/server.crt \
    --key=/etc/kubernetes/pki/etcd/server.key

# 保留 30 天
find $BACKUP_DIR -name "etcd-*.db" -mtime +30 -delete
BASH
chmod +x /opt/k8s-backup/etcd-backup.sh

# Cron 定时
echo "0 */6 * * * root /opt/k8s-backup/etcd-backup.sh" > /etc/cron.d/etcd-backup

# === etcd 恢复 ===
# 1. 停止 etcd (所有 Master)
systemctl stop etcd

# 2. 备份当前数据 (以防万一)
mv /var/lib/etcd /var/lib/etcd.bak

# 3. 恢复
ETCDCTL_API=3 etcdctl snapshot restore /data/backup/etcd/etcd-20260711.db \
    --data-dir=/var/lib/etcd

# 4. 修复权限
chown -R etcd:etcd /var/lib/etcd

# 5. 启动
systemctl start etcd

# === 资源导出 ===
# 导出所有资源
kubectl get all -A -o yaml > all-resources.yaml
kubectl get configmaps,secrets -A -o yaml > configs-secrets.yaml
kubectl get pv,sc -o yaml > storage.yaml

# 导出指定命名空间
kubectl get all -n production -o yaml > prod-resources.yaml
```

---

## 十二、生产最佳实践

### 12.1 资源规划

```
生产集群资源规划:

  Master 节点:
    < 5 节点:    2 C / 4 G / 50G SSD
    5-10 节点:   4 C / 8 G / 100G SSD
    10-50 节点:  8 C / 16 G / 200G SSD
    50+ 节点:    16 C / 32 G / 500G NVMe SSD
    Master 数量: 3 或 5 (奇数, Raft 多数派)
    etcd 磁盘:   独立 NVMe SSD (低延迟)

  Worker 节点:
    小型: 4 C / 8 G / 100G (开发/测试)
    中型: 8 C / 16 G / 200G (一般应用)
    大型: 16 C / 32 G / 500G (数据库/计算密集)
    计算密集: 32 C / 64 G / 1T (大数据/ML)
    GPU: 8 C / 32 G + 1 GPU (AI 推理)

  网络规划:
    Pod CIDR:     10.244.0.0/16 (可容纳 256 × 256 Pod)
    Service CIDR: 10.96.0.0/12
    Node CIDR:    192.168.1.0/24
    不要重叠!

  etcd 建议:
    - 3 节点 (容忍 1 故障) 或 5 节点 (容忍 2 故障)
    - 独立磁盘 (NVMe SSD, IOPS > 5000)
    - 网络延迟 < 10ms
    - fsync 延迟 < 10ms
    - 定期备份 (至少每 6 小时)
```

### 12.2 检查清单

```
集群安全:
  □ API Server 匿名访问已禁用
  □ RBAC 已启用 (不是 ABAC/AlwaysAllow)
  □ Pod Security Standards enforced (restricted)
  □ NetworkPolicy 已配置
  □ Secret 加密 (encryption at rest)
  □ 证书自动续期
  □ 审计日志已开启
  □ kubelet 端口 10250/10255 不对外
  □ etcd 端口 2379/2380 不对外

高可用:
  □ 3+ Master 节点
  □ etcd 3+ 节点
  □ API Server LB (HAProxy/云 LB)
  □ CoreDNS 副本 >= 2
  □ Ingress Controller 副本 >= 2
  □ 关键应用 PDB 配置

资源管理:
  □ 所有 Pod 设置 requests/limits
  □ 命名空间 ResourceQuota
  □ LimitRange 默认值
  □ HPA 配置
  □ PVC 大小合理

监控告警:
  □ Prometheus + Grafana
  □ Node/Pod/Container 指标
  □ etcd 延迟监控
  □ API Server 延迟监控
  □ 证书过期告警
  □ PVC 使用率告警
  □ 日志收集 (Loki/ELK)

备份恢复:
  □ etcd 定时备份
  □ PV 数据备份
  □ 集群配置导出
  □ 恢复演练
  □ 备份验证 (定期恢复测试)

CI/CD:
  □ 镜像扫描
  □ Helm Chart 版本管理
  □ 滚动更新策略
  □ 回滚机制
  □ GitOps (ArgoCD/Flux)
```

---

## 十三、对比总结

### 13.1 K8s 部署方案对比

| 方案 | 复杂度 | 维护成本 | 适用场景 |
|:---|:---|:---|:---|
| **云托管 (EKS/GKE/ACK)** | ⭐ 低 | ⭐ 低 | 云上生产, 不想管 Master |
| **kubeadm** | ⭐ 中 | 中 | 物理机/私有云生产 |
| Kubespray | 中 | 中 | Ansible 批量部署 |
| RKE2 | 中 | 中 | Rancher 生态 |
| K3s | ⭐ 低 | ⭐ 低 | 边缘/IoT/开发/小集群 |
| kind | ⭐ 低 | - | CI/本地测试 |
| minikube | ⭐ 低 | - | 学习 |
| Talos | 中 | ⭐ 低 | 不可变系统, 声明式管理 |

### 13.2 K8s 生态工具

| 类别 | 工具 | 说明 |
|:---|:---|:---|
| 包管理 | Helm | K8s 应用包管理器 |
| CI/CD | ArgoCD / Flux | GitOps 持续交付 |
| 服务网格 | Istio / Linkerd | 流量管理/可观测/安全 |
| 存储 | Rook / Longhorn | Ceph/NFS CSI 管理 |
| 监控 | Prometheus / Grafana | 指标采集/可视化 |
| 日志 | Loki / ELK / Fluentd | 日志收集/存储/查询 |
| 镜像仓库 | Harbor | 私有 Registry + 扫描 |
| 安全 | Falco / Trivy / OPA | 运行时安全/镜像扫描/策略 |
| 网络 | Calico / Cilium | CNI 网络插件 |
| Ingress | NGINX / Traefik / Envoy | Ingress Controller |
| 多集群 | Cluster API / Karmada | 多集群管理 |

---

## 十四、配置文件速查表

| 文件/路径 | 用途 |
|:---|:---|
| `/etc/kubernetes/admin.conf` | 集群管理员 kubeconfig |
| `/etc/kubernetes/kubelet.conf` | kubelet kubeconfig |
| `/etc/kubernetes/pki/` | 集群证书目录 |
| `/etc/kubernetes/manifests/` | 静态 Pod 清单 (API/Controller/Scheduler/etcd) |
| `/var/lib/kubelet/` | kubelet 数据目录 |
| `/var/lib/etcd/` | etcd 数据目录 |
| `/etc/systemd/system/kubelet.service.d/` | kubelet systemd 配置 |
| `/etc/cni/net.d/` | CNI 配置 |
| `/etc/containerd/config.toml` | containerd 配置 |
| `~/.kube/config` | 用户 kubeconfig |
| `kubeadm-config.yaml` | kubeadm 初始化配置 |
| `kube-flannel.yml` / `calico.yaml` | CNI 安装清单 |
| `dashboard.yaml` | Kubernetes Dashboard |
| `/var/log/kubernetes/` | K8s 日志目录 |
| `/var/log/pods/` | Pod 日志 (容器运行时) |
| `/var/log/containers/` | 容器日志 (符号链接) |

---

*最后更新: 2026-07-12*
