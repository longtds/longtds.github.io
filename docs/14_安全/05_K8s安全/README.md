# Kubernetes 安全

> K8s 安全 = **集群组件 + API Server + RBAC + Network Policy + 镜像准入 + 节点 + 多租户隔离 + 审计**。K8s 是新一代 OS，**默认安全配置 = 默认不安全**，必须层层加固。

## 一、K8s 攻击面全景

```
1. Control Plane
   ├── kube-apiserver         RBAC 漏 / 公网暴露 / 弱认证
   ├── etcd                   未加密 / 公网暴露 / 弱认证
   ├── kube-scheduler         调度污点利用
   ├── kube-controller-manager 控制器漏洞
   └── kubelet                未鉴权 / 10250 公网

2. Workload
   ├── Pod                    privileged / hostPath / capability
   ├── ServiceAccount         token 泄漏
   ├── Secret                 etcd 明文
   └── 网络流量               同 ns 互通无隔离

3. 节点
   ├── 内核                   逃逸 0day
   ├── containerd/runc        逃逸漏洞
   └── kubeconfig             被偷

4. 边界
   ├── Ingress                暴露面
   ├── Service Type LoadBalancer 公网暴露
   └── NodePort               未授权访问

5. 供应链
   ├── 镜像                   恶意/CVE
   ├── Helm Chart             第三方
   ├── Operator               CRD/Controller 权限大
   └── CRD Schema             注入

6. 多租户
   ├── ns 隔离不严
   ├── 共享 Node 风险
   └── 跨租户 Volume / Network
```

## 二、API Server 安全（最重要）

### 2.1 必备配置

```yaml
# kube-apiserver.yaml 关键参数
- --anonymous-auth=false                      # 禁匿名
- --insecure-port=0                           # 关闭 HTTP（已默认）
- --authorization-mode=Node,RBAC              # 必上 RBAC
- --admission-plugins=NodeRestriction,PodSecurity,ResourceQuota,LimitRanger,EventRateLimit,ServiceAccount,NamespaceLifecycle,DefaultStorageClass
- --enable-admission-plugins=PodSecurity      # 启用 PSA
- --audit-policy-file=/etc/kubernetes/audit-policy.yaml
- --audit-log-path=/var/log/kube-audit.log
- --audit-log-maxage=30
- --audit-log-maxbackup=10
- --audit-log-maxsize=100
- --tls-cipher-suites=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,...
- --tls-min-version=VersionTLS12
- --encryption-provider-config=/etc/kubernetes/encryption-config.yaml
- --service-account-lookup=true
- --request-timeout=60s
- --profiling=false
```

### 2.2 etcd 加密（Secret 必加密）

```yaml
# /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources: [secrets, configmaps]
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-32byte-key>
      - identity: {}                         # 兜底
```

```bash
# 重写已有 secret 触发加密
kubectl get secrets --all-namespaces -o json | kubectl replace -f -

# 配 KMS 更安全（AWS KMS / Vault Transit）
- kms:
    name: vault-kms
    endpoint: unix:///var/run/kmsplugin.sock
    cachesize: 1000
```

### 2.3 网络暴露收敛

```
✅ API Server 不要直接公网
   - 仅 VPC 内网
   - 跳板机 / Bastion + SSH 隧道
   - VPN / 零信任接入

✅ 限制 etcd 端口
   - 仅 Control Plane 节点间
   - mTLS 双向认证

✅ kubelet
   - --anonymous-auth=false
   - --authorization-mode=Webhook
   - 10250 仅 API Server 可达
   - 关 --read-only-port (10255)
```

## 三、RBAC 实战

### 3.1 RBAC 基础概念

```
Role            namespace 内权限
ClusterRole     cluster 级权限
RoleBinding     绑定 Role 到主体
ClusterRoleBinding  cluster 级绑定

主体（Subject）:
  - User
  - Group
  - ServiceAccount
```

### 3.2 最小权限示例

```yaml
# ❌ 反例: 全员 cluster-admin
# ✅ 正例: 按角色细分

# 只读 Pod 信息
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata: { name: pod-reader }
rules:
  - apiGroups: [""]
    resources: [pods, pods/log, pods/status]
    verbs: [get, list, watch]

# 应用部署员（限定 namespace）
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: deployer, namespace: prod }
rules:
  - apiGroups: [""]
    resources: [pods, services, configmaps]
    verbs: [get, list, watch, create, update, patch, delete]
  - apiGroups: [apps]
    resources: [deployments, statefulsets]
    verbs: [get, list, watch, create, update, patch, delete]
  - apiGroups: [networking.k8s.io]
    resources: [ingresses]
    verbs: [get, list, watch, create, update, patch, delete]
  - apiGroups: [""]
    resources: [secrets]
    verbs: []                              # 禁止访问 secret
```

### 3.3 危险 RBAC 配置（红线）

```yaml
# ❌ 永远不要
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]

# ❌ 等价 cluster-admin
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
  # secret 可读 ≈ 拿到 SA token ≈ 提权

# ❌ Pod exec/create + serviceaccount
- apiGroups: [""]
  resources: ["pods", "pods/exec"]
  verbs: ["create", "get"]
  # 攻击者: 创建 Pod 挂 SA → 拿 token

# ❌ 绑 system:masters 组
subjects:
  - kind: Group
    name: system:masters       # ≈ 超级管理员

# ❌ Role 同时给 escalate / bind / impersonate
- verbs: [escalate, bind, impersonate]
```

### 3.4 RBAC 审计

```bash
# 看谁是 cluster-admin
kubectl get clusterrolebindings -o json | jq '
  .items[] | select(.roleRef.name=="cluster-admin") | {
    binding: .metadata.name,
    subjects: .subjects
  }'

# 用户能做什么
kubectl auth can-i --list --as=user@company.com
kubectl auth can-i --list --as=system:serviceaccount:prod:my-sa

# 谁能 get secrets
kubectl get rolebindings,clusterrolebindings -A -o json | \
  jq '.items[] | select(.roleRef.kind=="ClusterRole" and .roleRef.name=="cluster-admin")'

# 工具:
✅ kubectl-who-can
✅ rakkess (Access Matrix)
✅ rbac-lookup
✅ kubectl-access-matrix
```

### 3.5 ServiceAccount 安全

```yaml
# 不需要 API 时禁挂载
apiVersion: v1
kind: ServiceAccount
metadata: { name: app, namespace: prod }
automountServiceAccountToken: false

---
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: app
  automountServiceAccountToken: false        # Pod 级覆盖
```

```bash
# 短期 token（K8s 1.22+）
kubectl create token my-sa --duration=1h
# Bound 到具体 Pod
kubectl create token my-sa --bound-object-kind=Pod --bound-object-name=my-pod
```

## 四、Pod Security Admission (PSA)

### 4.1 三个级别

| Level | 描述 | 适合 |
|:---|:---|:---|
| **privileged** | 无限制 | 系统组件 / 特权 ns |
| **baseline** | 防明显逃逸 | 常规生产 |
| **restricted** | 最严 | 推荐生产 ⭐ |

### 4.2 启用

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prod
  labels:
    # 三种模式
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
    
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
```

### 4.3 restricted 级别要求

```
✅ runAsNonRoot: true
✅ allowPrivilegeEscalation: false
✅ capabilities.drop: ["ALL"]
✅ seccompProfile.type: RuntimeDefault
✅ 禁止 hostNetwork/PID/IPC
✅ 禁止 hostPath
✅ 禁止 privileged
✅ 限制 volume 类型
✅ 限制 sysctl
```

### 4.4 集群级默认

```yaml
# kube-apiserver
- --admission-control-config-file=/etc/kubernetes/psa.yaml
```

```yaml
# psa.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
  - name: PodSecurity
    configuration:
      apiVersion: pod-security.admission.config.k8s.io/v1
      kind: PodSecurityConfiguration
      defaults:
        enforce: baseline
        enforce-version: latest
        audit: restricted
        warn: restricted
      exemptions:
        usernames: []
        runtimeClasses: []
        namespaces: [kube-system, gatekeeper-system]
```

## 五、Policy Engine：Kyverno / OPA Gatekeeper

### 5.1 选型

| 维度 | Kyverno | OPA Gatekeeper |
|:---|:---:|:---:|
| 语言 | YAML | Rego |
| 学习曲线 | 低 ⭐ | 高 |
| 性能 | 高 | 中 |
| Mutation | ✅ 原生 | 实验中 |
| Image 验证 | ✅ 原生 | 需扩展 |
| 社区 | CNCF Incubating | CNCF Graduated |
| 中文资料 | 多 | 少 |

**推荐**：新项目选 **Kyverno**，老项目继续 OPA。

### 5.2 Kyverno 必备策略

```yaml
# 禁止 latest tag
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: disallow-latest-tag }
spec:
  validationFailureAction: enforce
  rules:
    - name: require-image-tag
      match: { resources: { kinds: [Pod] } }
      validate:
        message: "Image tag 'latest' not allowed"
        pattern:
          spec:
            containers:
              - image: "!*:latest"

---
# 强制资源限制
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: require-resources }
spec:
  validationFailureAction: enforce
  rules:
    - name: validate-resources
      match: { resources: { kinds: [Pod] } }
      validate:
        message: "CPU/Memory limits required"
        pattern:
          spec:
            containers:
              - resources:
                  limits:
                    memory: "?*"
                    cpu: "?*"
                  requests:
                    memory: "?*"
                    cpu: "?*"

---
# 必须签名镜像
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: verify-image-signature }
spec:
  validationFailureAction: enforce
  webhookTimeoutSeconds: 30
  rules:
    - name: check-signature
      match: { resources: { kinds: [Pod] } }
      verifyImages:
        - imageReferences: ["harbor.company.com/*"]
          attestors:
            - entries:
                - keys:
                    publicKeys: |
                      -----BEGIN PUBLIC KEY-----
                      ...
                      -----END PUBLIC KEY-----

---
# 强制 NetworkPolicy
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: require-netpol }
spec:
  generateExisting: true
  rules:
    - name: generate-default-deny
      match: { resources: { kinds: [Namespace] } }
      exclude:
        any:
          - resources: { names: [kube-system, gatekeeper-system] }
      generate:
        kind: NetworkPolicy
        apiVersion: networking.k8s.io/v1
        name: default-deny
        namespace: "{{request.object.metadata.name}}"
        data:
          spec:
            podSelector: {}
            policyTypes: [Ingress, Egress]

---
# 禁止 hostPath
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: disallow-host-path }
spec:
  validationFailureAction: enforce
  rules:
    - name: deny-host-path
      match: { resources: { kinds: [Pod] } }
      validate:
        pattern:
          spec:
            =(volumes):
              - X(hostPath): "null"
```

## 六、网络安全

### 6.1 NetworkPolicy 默认拒绝

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-all, namespace: prod }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
# 仅允许 DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-dns, namespace: prod }
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector: {}
          podSelector: { matchLabels: { k8s-app: kube-dns } }
      ports:
        - { port: 53, protocol: UDP }
        - { port: 53, protocol: TCP }
```

### 6.2 CNI 选择（带安全特性）

| CNI | NetworkPolicy | 加密 | eBPF | 推荐 |
|:---|:---:|:---:|:---:|:---:|
| **Cilium** ⭐⭐⭐⭐⭐ | ✅ 高级 | WireGuard | ✅ | 首选 |
| **Calico** | ✅ | IPsec/WireGuard | ✅ | 主流 |
| **Antrea** | ✅ | IPsec | 部分 | 企业 |
| **Flannel** | ❌ | ❌ | ❌ | 弃用 |
| **Weave** | ✅ | ✅ | ❌ | 老牌 |

### 6.3 Cilium 高级策略（L7）

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata: { name: l7-policy }
spec:
  endpointSelector: { matchLabels: { app: api } }
  ingress:
    - fromEndpoints:
        - matchLabels: { app: frontend }
      toPorts:
        - ports: [{ port: "8080", protocol: TCP }]
          rules:
            http:
              # 只允许 GET / POST 特定路径
              - method: "GET"
                path: "/api/v1/users.*"
              - method: "POST"
                path: "/api/v1/orders"
                headers:
                  - "X-Tenant: trusted"
```

### 6.4 Service Mesh mTLS

```yaml
# Istio 强制 mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata: { name: default, namespace: istio-system }
spec:
  mtls:
    mode: STRICT                            # 全局强制
---
# Authorization Policy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata: { name: api-auth, namespace: prod }
spec:
  selector: { matchLabels: { app: api } }
  rules:
    - from:
        - source: { principals: ["cluster.local/ns/prod/sa/frontend"] }
      to:
        - operation: { methods: [GET, POST], paths: [/api/*] }
```

### 6.5 Ingress 安全

```yaml
# Nginx Ingress 强制 HTTPS + WAF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/ssl-ciphers: "ECDHE-RSA-AES256-GCM-SHA384:..."
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.2 TLSv1.3"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/rate-limit-rps: "100"
    nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8,192.168.0.0/16"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_clear_headers "Server";
      more_set_headers "X-Frame-Options: DENY";
      more_set_headers "X-Content-Type-Options: nosniff";
      more_set_headers "Strict-Transport-Security: max-age=31536000";
spec:
  tls:
    - hosts: [api.company.com]
      secretName: api-tls
  rules:
    - host: api.company.com
      http: ...
```

## 七、Secret 管理

### 7.1 K8s 原生 Secret 的问题

```
❌ etcd 中是 base64（不是加密）
❌ kubectl get secret 默认可看
❌ Pod ENV 写入容器内
❌ 容易随 manifest 入 Git
❌ 轮换困难
```

### 7.2 解决方案

```
方案 1: etcd 加密（基础）
  - 见第二节
  
方案 2: External Secrets Operator (ESO)
  - 从 Vault / AWS Secrets Manager 同步
  - K8s 内只是引用

方案 3: SealedSecrets (Bitnami)
  - 公钥加密 → 入 Git
  - 集群私钥解密

方案 4: SOPS + Kustomize
  - 文件级加密
  - 与 GitOps 配合

方案 5: Vault Agent Injector
  - Sidecar 直接挂载文件
  - 不进 etcd
```

### 7.3 External Secrets Operator 实战

```yaml
# 1. 安装 ESO
helm install external-secrets external-secrets/external-secrets -n external-secrets

# 2. 配 Vault SecretStore
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata: { name: vault-store, namespace: prod }
spec:
  provider:
    vault:
      server: "https://vault.company.com"
      path: kv
      version: v2
      auth:
        kubernetes:
          mountPath: kubernetes
          role: prod-app

# 3. 同步 Secret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata: { name: app-secrets, namespace: prod }
spec:
  refreshInterval: 1h
  secretStoreRef: { name: vault-store, kind: SecretStore }
  target: { name: app-secrets }
  data:
    - secretKey: db-password
      remoteRef: { key: secret/prod/db, property: password }
    - secretKey: api-key
      remoteRef: { key: secret/prod/api, property: key }
```

### 7.4 SealedSecrets

```bash
# 加密
echo -n "supersecret" | kubectl create secret generic mysecret \
  --dry-run=client --from-file=password=/dev/stdin -o yaml | \
  kubeseal --controller-namespace=sealed-secrets -o yaml > sealed.yaml

# sealed.yaml 可以入 Git，集群内自动解密
```

## 八、节点安全

### 8.1 节点加固

```bash
# OS 层（详见 01_Linux安全）
✅ CIS 基线
✅ 内核自动更新
✅ SELinux/AppArmor enforcing
✅ minimal install（无图形/无开发工具）

# K8s 节点专属
✅ kubelet TLS bootstrap + 自动轮换
✅ kubelet --read-only-port=0
✅ kubelet --anonymous-auth=false
✅ kubelet --authorization-mode=Webhook
✅ 禁止 root 登录节点
✅ 节点不暴露 SSH 公网
```

### 8.2 节点池隔离

```yaml
# 按风险分池
# 1. 系统节点池（Control Plane / Ingress）
# 2. 生产应用池
# 3. 测试 / Dev 池
# 4. 不可信 / 多租户池（用 Kata）
# 5. GPU 池

# Taint + Toleration 控制
kubectl taint nodes gpu-1 dedicated=gpu:NoSchedule

apiVersion: v1
kind: Pod
spec:
  tolerations:
    - key: dedicated
      operator: Equal
      value: gpu
      effect: NoSchedule
  nodeSelector: { workload: gpu }
```

### 8.3 RuntimeClass 强隔离

```yaml
# 启用 Kata
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata: { name: kata }
handler: kata

---
# 不可信工作负载用 Kata
apiVersion: v1
kind: Pod
metadata: { name: untrusted-app }
spec:
  runtimeClassName: kata
  containers: [...]
```

## 九、kubelet 安全

```bash
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

authentication:
  anonymous: { enabled: false }
  webhook: { enabled: true }
  x509: { clientCAFile: /etc/kubernetes/pki/ca.crt }

authorization:
  mode: Webhook

readOnlyPort: 0
protectKernelDefaults: true
makeIPTablesUtilChains: true
streamingConnectionIdleTimeout: 5m
eventRecordQPS: 10
tlsCipherSuites:
  - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
tlsMinVersion: VersionTLS12
rotateCertificates: true
serverTLSBootstrap: true
seccompDefault: true                       # K8s 1.27+ 默认 seccomp
```

## 十、审计日志

### 10.1 审计策略

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages: [RequestReceived]
rules:
  # 不记 system 类
  - level: None
    users: ["system:kube-proxy"]
  - level: None
    userGroups: ["system:nodes"]
    verbs: [get, list, watch]
  
  # Secret / ConfigMap / token 操作完整记录
  - level: RequestResponse
    resources:
      - group: ""
        resources: [secrets, configmaps, serviceaccounts/token]
  
  # RBAC 变更
  - level: RequestResponse
    resources:
      - group: rbac.authorization.k8s.io
  
  # 修改类操作
  - level: Request
    verbs: [create, update, patch, delete, deletecollection]
  
  # 其他读
  - level: Metadata
```

### 10.2 集中分析

```
日志 → Filebeat/Fluent-bit → Loki/ELK → 异常分析
  
关键检测:
  - 大量 4xx/5xx（错误猜测）
  - cluster-admin 操作
  - 异常时间登录
  - exec/portforward 异常
  - Secret 读取异常
  - 跨 namespace 异常
```

### 10.3 自动检测工具

```
✅ Falco K8s rules        实时
✅ Sysdig Secure          商业
✅ Magnify (KubeArmor)    LSM
✅ kubeaudit              静态扫描
✅ Polaris                K8s YAML 检查
✅ Kubescape              CIS + NSA + MITRE
✅ kube-bench             CIS 标准
```

## 十一、多租户隔离

### 11.1 软多租户（同集群多 ns）

```
✅ Namespace 边界
✅ ResourceQuota
✅ LimitRange
✅ NetworkPolicy 默认拒绝
✅ PSA restricted
✅ RBAC 严格分离
✅ Pod 亲和性
❌ 不能防内核 0day 逃逸
```

### 11.2 硬多租户

```
✅ vCluster（虚拟集群，多个 API Server）
✅ Capsule（多租户 Operator）
✅ HyperShift（OpenShift 多集群）
✅ 一租户一集群（最强）
✅ Kata Containers（节点 VM 隔离）
✅ gVisor / Firecracker
```

### 11.3 vCluster 示例

```bash
# 装 vCluster CLI
curl -L "https://github.com/loft-sh/vcluster/releases/latest/download/vcluster-linux-amd64" -o vcluster
chmod +x vcluster && mv vcluster /usr/local/bin

# 创建虚拟集群
vcluster create my-vcluster -n tenant-a

# 连接
vcluster connect my-vcluster
kubectl get pods                  # 看到的是 vcluster 内的视图
```

## 十二、CIS 合规扫描

### 12.1 kube-bench

```bash
# Helm 部署
helm install kube-bench aquasecurity/kube-bench

# 一次性 Job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# 解读结果
kubectl logs job/kube-bench

# 关注:
[FAIL] 1.2.7 Ensure that the --authorization-mode argument
[FAIL] 1.2.16 Ensure that admission control plugin is set
```

### 12.2 Kubescape

```bash
# 装
curl -s https://raw.githubusercontent.com/kubescape/kubescape/master/install.sh | /bin/bash

# 扫
kubescape scan --enable-host-scan
kubescape scan framework nsa
kubescape scan framework mitre
```

### 12.3 Polaris

```bash
helm install polaris fairwinds-stable/polaris
kubectl port-forward svc/polaris-dashboard 8080
# UI 看每个 workload 的健康/安全分
```

## 十三、应急响应（IR）

### 13.1 入侵迹象

```
✅ 异常 SA token 创建
✅ cluster-admin 操作激增
✅ exec / port-forward 飙升
✅ Egress 流量异常（C2）
✅ 挖矿 CPU 100%
✅ DaemonSet 突然出现
✅ 大量 Pod 重建
✅ 镜像不在白名单
```

### 13.2 应急命令

```bash
# 看异常 Pod
kubectl get pods -A | grep -v Running
kubectl get pods -A -o json | jq '.items[] | select(.spec.containers[].image | test("crypto|miner"))'

# 看异常 SA + RoleBinding
kubectl get clusterrolebindings -o json | jq '.items[] | select(.roleRef.name=="cluster-admin")'
kubectl get sa -A -o json | jq '.items[].metadata.name'

# 实时事件
kubectl get events --sort-by='.lastTimestamp' -A | tail -50

# 异常网络连接（在节点）
crictl ps
nsenter -t <pid> -n ss -tnp

# 隔离 Pod
kubectl label pod <bad-pod> isolated=true
kubectl annotate pod <bad-pod> kyverno.io/blocked=true
# NetworkPolicy 阻断 isolated=true 的流量

# 取证后销毁
kubectl debug node/<node> -it --image=ubuntu          # 节点 debug
kubectl cp <pod>:/var /tmp/forensics                 # 文件 copy
kubectl exec <pod> -- ps -ef > /tmp/ps.txt
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
```

## 十四、典型坑

| 坑 | 建议 |
|:---|:---|
| **API Server 公网** | 内网 / 跳板 / VPN |
| **匿名认证开** | --anonymous-auth=false |
| **kubelet readonly port** | --read-only-port=0 |
| **etcd Secret 明文** | encryption-config |
| **cluster-admin 滥发** | 按角色细分 |
| **secret 入 Git** | ESO / SealedSecrets |
| **PSA 没启** | namespace 标签 restricted |
| **NetworkPolicy 缺** | default deny |
| **CNI 选 Flannel** | 换 Cilium / Calico |
| **Service Mesh 不强制 mTLS** | STRICT 模式 |
| **节点 SSH 公网** | 内网 / Bastion |
| **kubeconfig 满天飞** | 短期 token / OIDC |
| **审计没开** | 必开 + 集中 |
| **镜像无签名验证** | Sigstore Policy |
| **Operator 权限过大** | 最小化 |
| **CRD 不做校验** | OpenAPI schema |
| **应急没演练** | 季度 Chaos |
| **多租户共享节点** | Kata / vCluster |

## 十五、最佳实践 Checklist

```
Control Plane:
☐ API Server 内网
☐ etcd 加密 + 备份
☐ 审计开启 + 集中
☐ TLS 1.2+ + 强密码套件
☐ Anonymous off
☐ admission controllers 完整
☐ profiling off

RBAC:
☐ 最小权限
☐ 无 cluster-admin 滥发
☐ ServiceAccount 不自动挂
☐ 短期 token (TokenRequest)
☐ 月度 RBAC 审计

Workload:
☐ PSA restricted
☐ Kyverno / Gatekeeper 策略
☐ Sigstore image 验证
☐ ResourceQuota / LimitRange
☐ securityContext 完整

网络:
☐ NetworkPolicy 默认拒绝
☐ Cilium / Calico
☐ Service Mesh mTLS STRICT
☐ Ingress 强 HTTPS + 限流
☐ Egress 限制

Secret:
☐ etcd encryption-config
☐ ESO / SealedSecrets / Vault
☐ 定期轮换
☐ 审计访问

节点:
☐ CIS 基线
☐ 内核更新
☐ SELinux/AppArmor
☐ kubelet 加固
☐ 节点池隔离
☐ Kata (敏感)

检测:
☐ Falco / Tetragon
☐ kube-bench 定期
☐ Kubescape 月度
☐ Polaris CI 集成
☐ 异常告警

应急:
☐ IR 剧本
☐ 备份 + 异地
☐ 隔离能力（NetworkPolicy / Taint）
☐ 季度演练
```

## 十六、技术栈推荐（2025）

### 16.1 小团队

```
准入:        PSA + Kyverno
镜像:        Trivy + Cosign + Sigstore Policy
密钥:        ESO + Vault
网络:        Cilium
检测:        Falco
合规:        kube-bench + Kubescape
```

### 16.2 中大企业

```
+ OPA Gatekeeper
+ Tetragon eBPF
+ Service Mesh (Istio/Cilium)
+ vCluster / Capsule（多租户）
+ Sysdig / Aqua / Wiz / Lacework
+ Vault HA / SPIRE
+ SIEM (Splunk / 长亭)
+ 红队蓝队演练
```

### 16.3 国产 / 信创

```
+ KubeArmor (LSM 国产生态)
+ 雷池 / 长亭洞鉴
+ 小佑科技 容器云安全
+ 等保 2.0 合规
+ 信创操作系统适配（麒麟 / 统信）
```

## 十七、学习路径

```
入门（2 周）:
  1. K8s 集群 + RBAC 实战
  2. PSA 启用
  3. NetworkPolicy 编写
  4. kube-bench 跑通

中级（1 个月）:
  5. Kyverno 策略
  6. Cosign 验证镜像
  7. ESO + Vault
  8. Falco 部署
  9. 审计 + Loki

高级（3 个月）:
  10. Tetragon eBPF
  11. Service Mesh mTLS
  12. vCluster / Kata
  13. 多租户架构
  14. CIS 全套合规

专家:
  15. 红蓝对抗
  16. 自定义准入控制
  17. 零信任 K8s
  18. 跨集群 / 多云安全治理
```

## 十八、参考资料

```
标准:
  - CIS Kubernetes Benchmark
  - NSA K8s Hardening Guidance
  - MITRE ATT&CK for Containers

书:
  - 《Kubernetes Security》(O'Reilly)
  - 《Hacking Kubernetes》(O'Reilly)
  - 《Kubernetes Security & Observability》

工具:
  - Kyverno: https://kyverno.io/
  - OPA Gatekeeper: https://open-policy-agent.github.io/gatekeeper/
  - Cilium: https://cilium.io/
  - Falco: https://falco.org/
  - Tetragon: https://tetragon.io/
  - Kubescape: https://kubescape.io/
  - kube-bench: https://github.com/aquasecurity/kube-bench
  - ESO: https://external-secrets.io/

社区:
  - CNCF Security TAG
  - K8s SIG-Security
  - r/kubernetes
```

> 📖 **核心判断**：K8s 安全是**纵深防御**的工程。**RBAC + PSA + Kyverno + Cosign + NetworkPolicy + ESO + Falco** 是 2025 国内可落地的黄金组合。最容易翻车的不是技术，而是：**cluster-admin 滥发、secret 入 Git、NetworkPolicy 缺失、kubelet 暴露公网、Pod 跑 root**——这五条做不到，K8s 就是新型的"裸奔操作系统"。
