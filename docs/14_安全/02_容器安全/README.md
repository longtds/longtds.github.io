# 容器安全

> 容器不是安全边界。**一行 privileged: true 就能从容器跳到宿主机**。容器安全 = 镜像安全 + 构建安全 + 运行时安全 + 主机隔离 + 准入控制，必须层层防护。

## 一、容器攻击面全景

```
1. 镜像层
   - 已知 CVE
   - 恶意基础镜像
   - 后门 / 挖矿
   - secrets 入镜像

2. 构建层
   - 不可信源
   - 中间人篡改
   - 没签名
   - 缺 SBOM

3. 运行时
   - privileged 滥用
   - capability 过多
   - hostPath / hostNetwork
   - root 用户
   - 逃逸漏洞

4. 编排层
   - K8s RBAC 弱
   - API server 暴露
   - kubelet 未鉴权
   - Secret 明文

5. 主机隔离
   - 共享内核（Namespace 不完全隔离）
   - cgroup 限制不严
   - 内核 0day → 全节点沦陷
```

## 二、容器逃逸经典手段（攻击者视角）

```
1. privileged 容器     直接 chroot 宿主机 /host
2. CAP_SYS_ADMIN      mount + nsenter 跳出
3. hostPID            ps -ef 看主机进程，kill / debug
4. hostNetwork         嗅探内网
5. hostPath /         挂载宿主机根目录
6. Docker socket      /var/run/docker.sock → 拉新容器逃
7. K8s Service Account  默认 token 读 secrets
8. CVE-2019-5736       runc copy-on-write 覆盖 runc
9. CVE-2022-0185       FUSE 提权
10. CVE-2024-0132       NVIDIA Container Toolkit
11. Dirty Pipe (2022)   pipe → 写任意文件
12. nsenter --target 1  cap_sys_admin 容器逃

→ 不熟攻击 就做不好防御
```

## 三、镜像安全

### 3.1 基础镜像选择

```
威胁面对比:
  ubuntu:22.04         ~28MB  ~80 CVE 包
  debian:12-slim       ~50MB  ~50 CVE
  alpine:3.20          ~7MB   ~10 CVE
  distroless/static    ~2MB   ~0
  scratch              0      0
  chainguard 系列      ~5-30MB ~0 (持续维护)
  
推荐:
  ✅ Go/Rust 静态二进制: scratch / distroless/static
  ✅ Java/Python: distroless/java / distroless/python / chainguard
  ✅ 兼容性场景: alpine
  ❌ ubuntu/debian 完整版（除非必要）
```

### 3.2 镜像漏洞扫描

```bash
# Trivy（开源首选）
trivy image --severity HIGH,CRITICAL --ignore-unfixed nginx:1.25
trivy image --format sarif --output report.sarif myimage

# Grype（Anchore）
grype myimage --fail-on high

# Clair (Quay)
# Snyk Container
# Aqua / Sysdig / Wiz / Lacework (商业)

# 国内
# 长亭 / 奇安信 / 阿里云镜像安全
```

### 3.3 镜像签名（Cosign）

```bash
# 生成密钥
cosign generate-key-pair --kms vault://kv/cosign

# 签名
cosign sign --key vault://kv/cosign harbor/app:1.0

# Keyless 签名（OIDC，推荐）
cosign sign --yes ghcr.io/company/app:1.0

# 验证
cosign verify --key cosign.pub harbor/app:1.0

# 集群强制验证（Sigstore Policy Controller）
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata: { name: only-signed }
spec:
  images:
    - glob: "harbor.company.com/**"
  authorities:
    - keyless:
        identities:
          - issuer: https://token.actions.githubusercontent.com
            subject: https://github.com/company/.*
        ctlog: { url: https://rekor.sigstore.dev }
```

### 3.4 SBOM 强制

```bash
# 生成 SBOM
syft harbor/app:1.0 -o spdx-json > sbom.json

# 附到镜像
cosign attest --predicate sbom.json --type spdx --key key harbor/app:1.0

# 准入检查
# Kyverno: 拒绝无 SBOM 的镜像
- name: require-sbom
  match: { resources: { kinds: [Pod] } }
  verifyImages:
    - imageReferences: ["harbor.company.com/*"]
      attestations:
        - predicateType: https://spdx.dev/Document
```

### 3.5 Dockerfile 安全最佳实践

```dockerfile
# syntax=docker/dockerfile:1.6

# ✅ 多阶段构建
FROM golang:1.22 AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags='-s -w' -o /app

# ✅ 最小运行时
FROM gcr.io/distroless/static:nonroot

# ✅ 非 root 用户
USER nonroot:nonroot

# ✅ 只复制必要
COPY --from=builder /app /app

# ✅ 明确暴露
EXPOSE 8080

# ✅ Healthcheck
HEALTHCHECK CMD ["/app", "health"]

# ✅ 不要 ENV 存 secrets
# ✅ 不要 ADD 远程 URL（用 RUN curl + 校验 hash）

# ✅ 使用 BuildKit secrets
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm install

# ✅ 校验下载文件 hash
RUN curl -fsSL https://example.com/file.tar.gz -o /tmp/f.tar.gz && \
    echo "abc123... /tmp/f.tar.gz" | sha256sum -c && \
    tar xzf /tmp/f.tar.gz -C /opt

ENTRYPOINT ["/app"]
```

### 3.6 镜像扫描红线

```
✅ HIGH/CRITICAL CVE = 0（除非有豁免单）
✅ 不允许 latest tag
✅ 不允许 root 运行
✅ 必须有 SBOM
✅ 必须签名
✅ 仅信任公司 Registry
```

## 四、运行时安全（runtime）

### 4.1 容器运行时选择

| 运行时 | 安全模型 | 性能 | 适合 |
|:---|:---|:---:|:---|
| **runc** | namespace + cgroup | ⭐⭐⭐⭐⭐ | 默认 |
| **crun** | 同 runc，C 写 | ⭐⭐⭐⭐⭐ | RHEL 默认 |
| **gVisor** | 用户态内核 (Sentry) | ⭐⭐⭐ | 多租户隔离 |
| **Kata Containers** | 轻量 VM | ⭐⭐⭐⭐ | 强隔离 |
| **Firecracker** | 微 VM | ⭐⭐⭐⭐ | Serverless / FaaS |
| **Nabla** | 单一进程 | ⭐⭐⭐ | 安全极致 |

```
何时选 Kata/gVisor:
  ✅ 多租户公有云
  ✅ 不可信代码（CI 构建 / 客户代码）
  ✅ 强合规（金融 / 政府）
  
何时坚持 runc:
  ✅ 内部应用
  ✅ 已有充分隔离（network policy / RBAC / 准入）
  ✅ 极致性能
```

### 4.2 必备 Pod Security Context

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    # Pod 级
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault          # 启用 seccomp
    supplementalGroups: []
    sysctls: []
  
  containers:
    - name: app
      image: harbor/app:1.0
      securityContext:
        # 容器级
        allowPrivilegeEscalation: false      # 必关
        privileged: false                     # 必 false
        readOnlyRootFilesystem: true          # 文件系统只读
        runAsNonRoot: true
        runAsUser: 1000
        capabilities:
          drop: ["ALL"]                       # 全砍
          add: ["NET_BIND_SERVICE"]           # 按需加
      resources:
        limits:
          cpu: 1
          memory: 512Mi
          ephemeral-storage: 1Gi
        requests: { cpu: 100m, memory: 128Mi }
      volumeMounts:
        - { name: tmp, mountPath: /tmp }
        - { name: cache, mountPath: /var/cache/app }
  
  volumes:
    - { name: tmp, emptyDir: {} }
    - { name: cache, emptyDir: {} }
  
  # 不要 host*
  hostNetwork: false
  hostPID: false
  hostIPC: false
  
  # 服务账号最小权限
  automountServiceAccountToken: false       # 不需要 API 时关闭
  serviceAccountName: app-sa
```

### 4.3 Capability 详解

```
危险 capability（绝大多数应用不需要）:
  CAP_SYS_ADMIN     ≈ root
  CAP_SYS_PTRACE    调试任意进程
  CAP_SYS_MODULE    加载内核模块
  CAP_NET_ADMIN     改网络配置
  CAP_NET_RAW       原始套接字（嗅探）
  CAP_DAC_OVERRIDE  绕过 DAC
  CAP_DAC_READ_SEARCH 读任意文件
  CAP_SETUID/GID    setuid 跳用户

常用合法 capability:
  CAP_NET_BIND_SERVICE   绑定 80/443
  CAP_CHOWN              chown
  CAP_KILL               kill 别人进程
  CAP_SETPCAP            设置 capability

→ 默认全 drop，逐项 add
```

### 4.4 seccomp 配置

```json
// /etc/docker/seccomp-custom.json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat",
                "lstat", "poll", "lseek", "mmap", "mprotect", "munmap",
                "brk", "rt_sigaction", "rt_sigprocmask", "ioctl",
                "access", "pipe", "select", "sched_yield", "mremap",
                "msync", "mincore", "madvise", "shmget", "shmat",
                "shmctl", "dup", "dup2", "pause", "nanosleep",
                "getitimer", "alarm", "setitimer", "getpid",
                "sendfile", "socket", "connect", "accept", "sendto",
                "recvfrom", "sendmsg", "recvmsg", "shutdown", "bind",
                "listen", "getsockname", "getpeername", "socketpair",
                "setsockopt", "getsockopt", "clone", "fork", "vfork",
                "execve", "exit", "wait4", "kill", "uname",
                "futex", "fcntl", "getcwd", "chdir", "mkdir", "rmdir"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

```yaml
# K8s 中使用
securityContext:
  seccompProfile:
    type: Localhost
    localhostProfile: profiles/custom.json   # /var/lib/kubelet/seccomp/profiles/custom.json
```

### 4.5 AppArmor / SELinux

```yaml
# AppArmor
metadata:
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: localhost/k8s-deny-write

# SELinux
securityContext:
  seLinuxOptions:
    level: "s0:c123,c456"
```

### 4.6 运行时威胁检测

```
工具:
  ✅ Falco             CNCF 标准
  ✅ Tetragon (Cilium) eBPF 现代
  ✅ Tracee (Aqua)     eBPF
  ✅ KubeArmor         LSM-based
  ✅ Sysdig Secure     商业
  ✅ Aqua / Wiz / Lacework / SentinelOne 商业
```

```yaml
# Falco 规则示例
- rule: Container Run as Root
  desc: Container running as root user
  condition: container and proc.uid == 0 and not user_known_root_containers
  output: "Root in container (image=%container.image.repository)"
  priority: WARNING

- rule: Mount Sensitive FS
  desc: Mount of sensitive host paths
  condition: spawned_process and proc.name=mount and not user_known_mount
  output: "Sensitive mount (cmd=%proc.cmdline)"
  priority: CRITICAL

- rule: Shell in Container
  desc: Shell spawned in production container
  condition: spawned_process and container.id != host and shell_procs
  output: "Shell in container (user=%user.name shell=%proc.name image=%container.image)"
  priority: WARNING

- rule: Outbound Connection to C2
  condition: outbound and fd.sip in (c2_ips)
  output: "C2 connection (image=%container.image dest=%fd.sip)"
  priority: CRITICAL
```

### 4.7 网络隔离

```yaml
# 默认拒绝所有
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny, namespace: prod }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]

---
# 仅允许指定流量
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-api, namespace: prod }
spec:
  podSelector: { matchLabels: { app: api } }
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - podSelector: { matchLabels: { app: frontend } }
      ports: [{ port: 8080 }]
  egress:
    - to:
        - podSelector: { matchLabels: { app: db } }
      ports: [{ port: 5432 }]
    - to:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } }
        - podSelector: { matchLabels: { k8s-app: kube-dns } }
      ports: [{ port: 53, protocol: UDP }]
```

## 五、容器逃逸防护

### 5.1 主机隔离

```
✅ K8s 节点专用（不要混跑业务和管理面）
✅ 节点池按风险分（生产/测试/可信/不可信）
✅ 节点 Taint + Pod Toleration 控制调度
✅ 节点 SELinux/AppArmor 强制
✅ 节点 kernel 自动更新
```

### 5.2 禁止高危挂载

```yaml
# Kyverno 拒绝危险挂载
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: disallow-host-path }
spec:
  validationFailureAction: enforce
  rules:
    - name: deny-host-path
      match: { resources: { kinds: [Pod] } }
      validate:
        message: "hostPath volumes are forbidden"
        deny:
          conditions:
            - key: "{{ request.object.spec.volumes[].hostPath || `[]` }}"
              operator: NotEquals
              value: []

# 拒绝 host network/pid/ipc
- name: deny-host-namespaces
  validate:
    message: "hostNetwork/hostPID/hostIPC forbidden"
    pattern:
      spec:
        =(hostNetwork): false
        =(hostPID): false
        =(hostIPC): false

# 拒绝 privileged
- name: deny-privileged
  validate:
    pattern:
      spec:
        =(containers):
          - =(securityContext):
              =(privileged): false
              =(allowPrivilegeEscalation): false
```

### 5.3 Pod Security Admission（PSA）

```yaml
# Namespace 级别启用
apiVersion: v1
kind: Namespace
metadata:
  name: prod
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/enforce-version: latest
```

三个级别：
```
privileged   无限制（仅 kube-system 等）
baseline     基础（不允许明显逃逸）
restricted   严格（推荐生产）
```

## 六、Docker Daemon 安全（如还在用）

```bash
# /etc/docker/daemon.json
{
  "icc": false,                          # 容器间默认不互通
  "userns-remap": "default",             # 用户命名空间隔离
  "no-new-privileges": true,
  "live-restore": true,
  "log-driver": "json-file",
  "log-opts": { "max-size": "100m", "max-file": "5" },
  "default-ulimits": {
    "nofile": { "Name": "nofile", "Hard": 64000, "Soft": 64000 }
  },
  "seccomp-profile": "/etc/docker/seccomp.json",
  "selinux-enabled": true,
  "default-runtime": "runc",
  "runtimes": {
    "kata": { "path": "/usr/bin/kata-runtime" }
  },
  "registry-mirrors": ["https://harbor.company.com"],
  "insecure-registries": [],
  "tls": true,
  "tlsverify": true,
  "tlscacert": "/etc/docker/ca.pem",
  "tlscert": "/etc/docker/server-cert.pem",
  "tlskey": "/etc/docker/server-key.pem"
}
```

```bash
# 永远不要把 docker.sock 暴露出去
# /var/run/docker.sock 权限严格 660 docker:docker
```

## 七、Containerd / CRI-O 安全

```toml
# /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  SystemdCgroup = true
  NoNewPrivileges = true                 # 安全
  NoPivotRoot = false

[plugins."io.containerd.grpc.v1.cri".containerd]
  default_runtime_name = "runc"
  disable_snapshot_annotations = false

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
  runtime_type = "io.containerd.kata.v2"

[plugins."io.containerd.grpc.v1.cri".registry.configs."harbor.company.com".tls]
  ca_file = "/etc/ssl/harbor-ca.crt"

# Restart
systemctl restart containerd
```

## 八、CIS Docker / Kubernetes Benchmark

```bash
# Docker Bench
docker run --net host --pid host --userns host --cap-add audit_control \
  -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
  -v /var/lib:/var/lib:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /etc:/etc:ro \
  --label docker_bench_security \
  docker/docker-bench-security

# Kube-bench (K8s CIS)
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs -l app=kube-bench

# 解读: 通常 70%+ 通过即合格，关注 critical 项
```

## 九、运行时漏洞响应

### 9.1 紧急响应剧本

```
🚨 发现镜像 0day:
  1. 全 Registry 标记隔离
  2. Kyverno 加 deny rule（按 image）
  3. 拉新基础镜像
  4. CI 重 build → 滚动更新
  5. 漏洞披露后 24h 内必须完成
  
🚨 容器被入侵:
  1. 不要 kubectl delete pod（销毁取证）
  2. 隔离 node（cordon + drain other pods）
  3. 进入容器/节点取证（ps, netstat, /proc）
  4. dump 进程内存
  5. 备份 container fs（docker commit）
  6. 之后 kill 容器
  7. 排查横向移动（其他节点）
```

### 9.2 取证命令

```bash
# 容器内取证
kubectl exec -it pod -- /bin/sh
# 进入受限容器:
nsenter -t $(crictl inspect $CID | jq .info.pid) -m -u -i -n -p
crictl inspect $CID
crictl exec -it $CID /bin/sh
crictl logs $CID
crictl stats

# 主机侧
ps -ef --forest                              # 找到容器对应的 host pid
ls /proc/<pid>/root                          # 容器根文件系统
cat /proc/<pid>/status                       # capabilities
cat /proc/<pid>/cgroup                       # 所属容器
ss -tnp | grep <pid>
```

## 十、镜像供应链全流程

```
代码 → CI → 构建 → 扫描 → 签名 → 推送 → 准入 → 部署 → 运行时

每个环节有不同攻击面，对应安全控制:
  Source:    SAST / 依赖扫描
  Build:     可信构建器 / 隔离 builder
  Image:     Trivy / Grype 扫描
  Sign:      Cosign / Notary
  Push:      私有 Registry / Webhook
  Verify:    Sigstore Policy / Kyverno
  Deploy:    OPA / Kyverno / PSA
  Run:       Falco / Tetragon

→ 详见 06_供应链安全
```

## 十一、典型坑（生产血泪）

| 坑 | 建议 |
|:---|:---|
| **privileged: true** | 永远不要 |
| **hostPath /** | 严禁 / 用 PVC |
| **hostNetwork/PID/IPC** | 仅特殊场景 |
| **root 用户运行** | 必非 root |
| **CAP 全开** | 必 drop ALL |
| **latest tag** | 用 SHA / SemVer |
| **base 镜像太大** | distroless |
| **没有 readOnlyRootFilesystem** | 必开 |
| **没有 NetworkPolicy** | default deny |
| **SA token 自动挂载** | 不用时关 |
| **secrets 写镜像** | Vault / Secret |
| **没扫描** | Trivy + 阻断 |
| **没签名** | Cosign + Policy Controller |
| **没 PSA** | 必启 restricted |
| **没运行时检测** | Falco / Tetragon |
| **docker.sock 暴露** | 永禁 |
| **kubelet 公网** | 永禁 |
| **API server 公网** | 必 IP 白名单 + RBAC |

## 十二、最佳实践 Checklist

```
镜像:
☐ distroless / chainguard 基础
☐ 多阶段构建
☐ 非 root + readOnlyRoot
☐ SHA / SemVer tag
☐ Trivy 扫描红线
☐ Cosign 签名
☐ Syft SBOM
☐ Dockerfile lint (hadolint)

运行时:
☐ securityContext 完整
☐ Capability drop ALL
☐ seccomp RuntimeDefault
☐ allowPrivilegeEscalation false
☐ runAsNonRoot
☐ readOnlyRootFilesystem
☐ resources limits
☐ automount SA token 按需

准入:
☐ Pod Security Admission (restricted)
☐ Kyverno / OPA Gatekeeper
☐ Sigstore Policy Controller
☐ Image 来源白名单

网络:
☐ NetworkPolicy 默认拒绝
☐ Service Mesh mTLS
☐ Ingress TLS
☐ Egress 控制

主机:
☐ 节点池按风险分
☐ 内核自动更新
☐ SELinux/AppArmor
☐ Kata/gVisor（不可信场景）

检测:
☐ Falco / Tetragon
☐ kube-bench CIS
☐ 漏洞扫描周期
☐ 异常告警接入

应急:
☐ IR 剧本
☐ 取证工具就位
☐ 演练
```

## 十三、推荐工具栈（2025）

### 13.1 小团队

```
镜像扫描:    Trivy
签名:        Cosign keyless
SBOM:        Syft
准入:        Kyverno + PSA
运行时:      Falco
NetworkPolicy: Cilium / Calico
基线:        kube-bench
```

### 13.2 中大企业

```
镜像扫描:    Trivy + Snyk
签名:        Cosign + Sigstore Policy Controller
SBOM:        Syft + 自动审计
准入:        Kyverno + OPA Gatekeeper + PSA
运行时:      Tetragon + Falco
强隔离:      Kata Containers（敏感工作负载）
平台:        Aqua / Wiz / Sysdig / Lacework
SIEM:        Splunk / 长亭 / 奇安信
零信任:      Cilium + SPIRE
```

### 13.3 国产 / 信创

```
镜像扫描:    长亭牧云 / 启明 / 奇安信
准入:        OpenKruise / KubeArmor
运行时:      KubeArmor / 雷池
平台:        小佑科技 / 安全狗
合规:        等保 2.0 + 信创操作系统适配
```

## 十四、学习路径

```
入门（2 周）:
  1. 跑通 Trivy 扫描
  2. 写一个 distroless Dockerfile
  3. securityContext 完整配置
  4. Pod Security Admission 启用

中级（1 个月）:
  5. Cosign 签名 + 验证
  6. Syft SBOM
  7. NetworkPolicy 编写
  8. Kyverno / OPA 策略
  9. Falco 部署

高级（3 个月）:
  10. Kata Containers / gVisor
  11. Tetragon eBPF 检测
  12. kube-bench / CIS 合规
  13. 容器逃逸演练
  14. IR + 取证

专家:
  15. Sigstore 全栈
  16. 自研准入 / 检测规则
  17. 零信任架构
  18. AI 辅助容器安全
```

## 十五、参考资料

```
标准:
  - CIS Docker Benchmark
  - CIS Kubernetes Benchmark
  - NIST 800-190 (容器安全)
  - PCI-DSS Container Guidance

书:
  - 《Container Security》(Liz Rice, O'Reilly)
  - 《Hacking Kubernetes》(O'Reilly)
  - 《Kubernetes Security and Observability》

工具:
  - Trivy: https://aquasecurity.github.io/trivy/
  - Cosign: https://docs.sigstore.dev/cosign/
  - Falco: https://falco.org/
  - Tetragon: https://tetragon.io/
  - Kyverno: https://kyverno.io/
  - kube-bench: https://github.com/aquasecurity/kube-bench

社区:
  - CNCF Security TAG
  - OWASP Container Security Top 10
  - r/kubernetes
  - 国内: K8s 安全社区 / 看雪
```

> 📖 **核心判断**：容器不是安全边界，是性能边界。**安全 = 镜像（distroless+扫描+签名）+ 运行时（securityContext+seccomp）+ 准入（PSA+Kyverno）+ 检测（Falco/Tetragon）+ 网络（NetworkPolicy+mTLS）+ 强隔离（Kata/gVisor，敏感场景）**。最容易翻车的不是技术，而是**默认 privileged、默认 root、默认全 capability、默认无 NetworkPolicy**——把这四个默认翻过来，容器安全就过及格线。
