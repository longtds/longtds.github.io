# 最佳实践

> Docker 最佳实践 = **运行时选型决策树 + 镜像规范 + 仓库治理 + CI/CD 流水线 + K8s 接管节奏 + 监控/日志/告警 SOP + 安全合规 + 资源容量 + 多架构发布 + 国产化路径 + 故障排查 SOP**。本章把"会用 Docker"升级到"运营企业级容器平台"。

## 一、运行时选型决策

### 1.1 决策矩阵

```
单机开发 / CI runner:
  → Docker CE + Compose ⭐
  
单机生产（边缘 / 小服务）:
  → Docker CE + Compose / Podman
  → 资源受限场景: iSulad / k3s
  
K8s 集群（生产）:
  → containerd ⭐ (主流，新装首选)
  → CRI-O (Red Hat / OpenShift)
  → 旧集群 dockershim 必须升级
  
机密计算 / 多租户 SaaS:
  → containerd + Kata Containers
  → + SEV-SNP/TDX/海光 CSV (CoCo)
  
不可信代码 / 沙箱:
  → gVisor (runsc)
  → Firecracker (microVM)
  
嵌入式 / 物联网:
  → iSulad (openEuler) ⭐
  → balenaEngine
  → k3s + containerd

Wasm / Serverless 边缘:
  → containerd + runwasi + WasmEdge
```

### 1.2 K8s 集群 dockershim 替换

```bash
# 1. 节点上停 dockershim (老 K8s)
systemctl stop kubelet
systemctl stop docker

# 2. 装 containerd
apt install -y containerd.io
containerd config default > /etc/containerd/config.toml
# 关键改:
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sed -i 's|registry.k8s.io/pause:3.6|registry.aliyuncs.com/k8sxio/pause:3.9|' /etc/containerd/config.toml

systemctl enable --now containerd

# 3. kubelet 切换
# /var/lib/kubelet/kubeadm-flags.env
KUBELET_KUBEADM_ARGS="--container-runtime=remote --container-runtime-endpoint=unix:///run/containerd/containerd.sock"

systemctl daemon-reload
systemctl restart kubelet
crictl ps                        # 验证
```

## 二、镜像规范（团队级）

### 2.1 命名规约

```
harbor.example.com/<org>/<project>/<service>:<tag>

tag 规则:
  - 语义版本: 1.2.3 / 1.2 / 1
  - Git: <branch>-<short-sha> 或 <git-tag>
  - 时间戳: 20260627-1430-<sha>
  - 环境: <ver>-dev / <ver>-staging / <ver>-prod
  
❌ 永远不要:
  - latest 上生产
  - 不带 tag
  - tag 复用（除 latest 自动指向最新）
```

### 2.2 镜像分级

| 层级 | 来源 | 示例 | 用途 |
|:---|:---|:---|:---|
| L0 基础 | 公司根 | `org/base:debian12-1.0` | OS + 公共依赖 |
| L1 语言 | L0 派生 | `org/base-go:1.22-1.0` | Go/Python/Node 工具链 |
| L2 框架 | L1 派生 | `org/base-spring:3.2-1.0` | 业务框架 |
| L3 业务 | L2 派生 | `org/payment-api:1.5.2` | 应用 |
| L4 临时 | 任意 | `tmp/...` | CI / 测试 |

```
治理:
  L0/L1 由平台组维护，月度升级（CVE 跟进）
  L2 框架组负责
  L3 业务团队
  L4 7 天自动清理
```

### 2.3 Dockerfile 规约（团队）

```dockerfile
# syntax=docker/dockerfile:1.6
ARG BASE=harbor.example.com/org/base-go:1.22-1.0
FROM ${BASE} AS builder
...

# 必填 LABEL（团队基线）
LABEL org.opencontainers.image.title="payment-api" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.source="https://gitlab.example.com/org/payment-api" \
      org.opencontainers.image.vendor="ExampleCorp" \
      org.opencontainers.image.licenses="Apache-2.0" \
      maintainer="sre@example.com"

# 必填健康检查
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost:8080/health || exit 1

USER 1000:1000
EXPOSE 8080
```

### 2.4 镜像质量门禁

```
☐ 必须多阶段
☐ 不允许 :latest
☐ 不允许 root 运行
☐ 必须 HEALTHCHECK
☐ 必须 LABEL 元数据齐全
☐ 镜像 < 500 MB (业务) / < 2 GB (AI)
☐ Trivy 扫无 HIGH/CRITICAL
☐ Dockle / Hadolint 通过
☐ cosign 签名
☐ SBOM 生成
☐ Provenance 生成
```

## 三、Harbor 仓库治理

### 3.1 Project 划分

```
分类:
  - public/        公共镜像 (CentOS / Nginx 镜像)
  - base/          公司基础镜像
  - infra/         平台组件
  - <team>/        团队空间（按部门）
  - dev/           开发测试
  - prod/          生产

权限:
  - Maintainer:    Tech Lead
  - Developer:     开发者
  - Guest:         其他团队
  - 机器人账号:    CI/CD push, K8s pull
```

### 3.2 必备策略

```
1. Tag 不可变（prod project）
2. 镜像签名必须（cosign）
3. 漏洞扫描必须（Trivy 内置）
4. 保留策略:
   - 最新 N 个 + latest + tag 是 v* 的保留
   - 其他 14-30 天
   - 已签名永久
5. Replication:
   - prod 镜像复制到 2 个 Region 仓库
6. Proxy Cache:
   - 代理 docker.io / gcr.io / quay.io
   - 集群内一律通过 Proxy
7. Webhook:
   - 扫描完成 → 通知 ChatOps
   - 推送 prod → 触发 K8s ArgoCD
```

### 3.3 Robot Account 规范

```yaml
# CI 用 (push)
robot$ci-push:
  permissions:
    - resource: repository, action: push
    - resource: repository, action: pull
  expiry: 90 days

# K8s 节点 (pull only)
robot$k8s-pull:
  permissions:
    - resource: repository, action: pull
  expiry: 永久

# 千万不要用 admin 账号给 CI
```

## 四、CI/CD 流水线

### 4.1 标准流水线（GitLab CI 示例）

```yaml
stages: [test, lint, build, scan, sign, push, deploy]

variables:
  IMAGE: harbor.example.com/${CI_PROJECT_PATH}
  TAG: ${CI_COMMIT_BRANCH}-${CI_COMMIT_SHORT_SHA}

test:
  image: harbor.example.com/base/golang:1.22
  script:
    - go test -v -race -coverprofile=coverage.out ./...
  artifacts: { paths: [coverage.out] }

lint-dockerfile:
  image: hadolint/hadolint:latest
  script:
    - hadolint Dockerfile

build:
  image: harbor.example.com/base/buildx:1.0
  script:
    - docker buildx build
        --platform linux/amd64,linux/arm64
        --cache-from type=registry,ref=${IMAGE}:buildcache
        --cache-to type=registry,ref=${IMAGE}:buildcache,mode=max
        --attest type=provenance,mode=max
        --attest type=sbom
        --label "org.opencontainers.image.revision=${CI_COMMIT_SHA}"
        -t ${IMAGE}:${TAG}
        --push .

scan:
  image: aquasec/trivy:latest
  script:
    - trivy image --severity HIGH,CRITICAL --exit-code 1 --no-progress ${IMAGE}:${TAG}
    - trivy image --format cyclonedx --output sbom.json ${IMAGE}:${TAG}
  artifacts: { paths: [sbom.json] }

sign:
  image: gcr.io/projectsigstore/cosign:latest
  script:
    - cosign sign --yes --key $COSIGN_KEY ${IMAGE}:${TAG}
    - cosign attest --predicate sbom.json --type cyclonedx --key $COSIGN_KEY ${IMAGE}:${TAG}

deploy-dev:
  stage: deploy
  script:
    - kubectl set image deploy/myapp myapp=${IMAGE}:${TAG} -n dev
  only: [develop]

deploy-prod:
  stage: deploy
  script:
    - argocd app set myapp --helm-set image.tag=${TAG}
    - argocd app sync myapp
  when: manual
  only: [main]
```

### 4.2 多架构发布

```yaml
build-multiarch:
  parallel:
    matrix:
      - PLATFORM: ["linux/amd64", "linux/arm64"]
  script:
    - docker buildx build --platform $PLATFORM -t ${IMAGE}:${TAG}-${PLATFORM##*/} --push .

manifest:
  needs: [build-multiarch]
  script:
    - docker buildx imagetools create -t ${IMAGE}:${TAG} \
        ${IMAGE}:${TAG}-amd64 \
        ${IMAGE}:${TAG}-arm64
```

### 4.3 缓存层级

```
L0 buildkit local cache (单机/runner)
L1 registry cache       (Harbor 缓存层)
L2 GHA / S3 cache       (跨 runner)
L3 Proxy cache (dep)    (Maven/npm/pip 走 Nexus)
```

## 五、监控与日志 SOP

### 5.1 集中监控栈

```
Prometheus + Grafana
  + cAdvisor (容器级)
  + node_exporter (主机)
  + dockerd metrics (engine)
  + Harbor exporter
  + DeepFlow (eBPF APM)

日志:
  应用 stdout
    → DaemonSet (Promtail/Fluent Bit/Vector)
    → Loki / ELK / 阿里 SLS
  
Trace:
  OpenTelemetry SDK
    → Jaeger / Tempo / SkyWalking
```

### 5.2 必备告警

```yaml
# 单容器
- alert: ContainerOOMKilled
  expr: increase(container_oom_events_total[5m]) > 0

- alert: ContainerHighMemory
  expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
  for: 5m

- alert: ContainerHighCPU
  expr: rate(container_cpu_usage_seconds_total[5m]) > 0.9 * container_spec_cpu_quota / container_spec_cpu_period
  for: 10m

- alert: ContainerRestarting
  expr: increase(kube_pod_container_status_restarts_total[15m]) > 3

# 引擎
- alert: DockerEngineDown
  expr: up{job='docker-engine'} == 0
  for: 2m

# 镜像
- alert: ImagePullBackOff
  expr: kube_pod_container_status_waiting_reason{reason='ImagePullBackOff'} > 0
  for: 5m

# 仓库
- alert: HarborDiskFull
  expr: harbor_filesystem_used_ratio > 0.85

- alert: HarborReplicationFailed
  expr: increase(harbor_replication_failed_total[1h]) > 0
```

### 5.3 关键大盘

```
集群总览:
  - 节点数 / Pod 数 / 容器数
  - 镜像总量 / 仓库容量
  - 资源利用率 (CPU/Mem/Net/Disk)

应用维度:
  - QPS / RT / 错误率
  - 容器实例数 + 重启次数
  - 资源利用率分布
  - HPA 状态

仓库维度:
  - Pull/Push QPS
  - Top 镜像 / Top 用户
  - 漏洞分布
  - 复制状态

构建维度:
  - 构建时长 / 成功率
  - 缓存命中率
  - 镜像大小趋势
```

## 六、安全合规

### 6.1 平台级 Checklist

```
身份:
☐ Harbor + LDAP/OIDC SSO
☐ Robot 账号最小权限
☐ MFA 给 Maintainer+

构建:
☐ Dockerfile lint (hadolint)
☐ Trivy 扫 HIGH/CRITICAL 阻断
☐ Dockle CIS 检测
☐ SBOM 生成
☐ Provenance SLSA L2+

签名:
☐ cosign 强制签名
☐ K8s sigstore policy-controller 准入
☐ 国密 HSM 集成

运行时:
☐ rootless / userns-remap
☐ seccomp default + custom
☐ AppArmor / SELinux enforce
☐ Pod Security Standards (Restricted)
☐ OPA Gatekeeper / Kyverno 策略

监控:
☐ Falco / Tetragon 运行时威胁
☐ K8s Audit Log → SIEM
☐ 镜像 pull/push 审计
☐ 容器逃逸检测

合规:
☐ 等保 2.0 三级 / 四级
☐ CIS Docker Benchmark
☐ NIST 800-190 容器安全
☐ 数据安全法 / 个保法
☐ 镜像 / Secret 加密存储

供应链:
☐ 仓库 Proxy Cache 隔离公网
☐ 三方镜像审计 + 白名单
☐ 第三方依赖 SBOM 追踪
☐ Notary / Sigstore 验证
```

### 6.2 CIS Docker Benchmark 自查

```bash
# 用 docker-bench-security
docker run --rm --net host --pid host --userns host --cap-add audit_control \
  -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
  -v /etc:/etc:ro -v /usr/bin/containerd:/usr/bin/containerd:ro \
  -v /usr/bin/runc:/usr/bin/runc:ro -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /var/lib:/var/lib:ro -v /var/run/docker.sock:/var/run/docker.sock:ro \
  --label docker_bench_security \
  docker/docker-bench-security
```

关键项：

1. Host 配置（kernel, 升级）
2. Docker daemon 配置（TLS, userns, no-new-privileges）
3. daemon.json 安全
4. 容器镜像 (USER nonroot, HEALTHCHECK)
5. 容器运行（cap-drop, read-only, no-privileged）
6. 集群安全

## 七、资源容量

### 7.1 容器规格基线

```
微服务:
  CPU:    100m-1000m
  Memory: 128Mi-512Mi
  
Java 应用:
  CPU:    500m-2000m
  Memory: 1Gi-4Gi
  JVM 必设 -Xmx + UseContainerSupport

数据库容器:
  CPU:    2-8 核
  Memory: 4-32 Gi
  外挂存储

AI 推理 / 训练:
  CPU:    4-32 核
  Memory: 16-256 Gi
  GPU:    MIG 切片 / 整卡 / 多卡
  Shm:    4 Gi+
```

### 7.2 节点容量

```
单节点容器密度:
  Web/API:       50-200 容器
  数据库:        2-5 容器
  AI 训练:       1-4 容器
  
Docker 配置:
  --max-concurrent-downloads=10
  --max-concurrent-uploads=10
  --default-ulimits nofile=65536

K8s 节点:
  max-pods: 110 (默认) / 250 (大节点)
```

### 7.3 镜像存储容量

```
节点本地镜像:
  /var/lib/docker 或 /var/lib/containerd
  独立分区 50-200 GB
  自动 GC

Harbor 仓库:
  每业务约 50-200 GB
  保留策略 + GC 月度
  Proxy Cache 减少外网拉取
```

## 八、变更管理

### 8.1 镜像发布流程

```
Dev push code
  ↓
CI: lint → test → build → scan → sign → push (Dev tag)
  ↓
Dev 环境自动部署
  ↓
QA 验证
  ↓
Promote: 给镜像加 Staging tag
  ↓
Staging 部署 + 回归
  ↓
Promote: 加 Prod tag (cosign 重新签)
  ↓
Prod 部署 (ArgoCD/Flux Canary/Blue-Green)
  ↓
监控 + 回滚预案
```

### 8.2 镜像 Promote 规范

```bash
# 同一镜像 SHA 多 tag（不重新 build）
docker buildx imagetools create -t ${IMAGE}:v1.5.2-prod ${IMAGE}:v1.5.2-staging

# 重新签名 prod tag
cosign sign --key $PROD_KEY ${IMAGE}:v1.5.2-prod
```

### 8.3 回滚

```bash
# K8s 回滚
kubectl rollout undo deploy/myapp -n prod

# ArgoCD 回滚
argocd app history myapp
argocd app rollback myapp <revision>

# 镜像紧急下线
# Harbor: Project Settings → Vulnerability → 强制阻断该 tag
```

## 九、K8s 接管节奏

### 9.1 路径

```
阶段 1: 单机 Docker + Compose (5-20 服务)
  ↓ 增长到 30+
阶段 2: K3s / k0s (小集群，1-5 节点)
  ↓
阶段 3: K8s (kubeadm/Rancher) 3 master + N worker
  ↓
阶段 4: K8s 多集群 + GitOps + 多租户
```

### 9.2 单机 → K8s 迁移点

```
触发:
☐ 服务 > 30 个
☐ 多机部署需要
☐ 需要 HA / 滚动升级
☐ CI/CD 接 GitOps
☐ 多团队多租户
☐ HPA / VPA 弹性需求

工具:
  Kompose: compose.yaml → K8s manifest
  Helm:    模板化
  Kustomize: 多环境覆盖
```

### 9.3 共存方案

```
方案 A: 单 OS 装 K8s + 偶尔 docker
  - K8s 用 containerd
  - docker CE 也可装（指向独立 containerd 或自己）
  - 双 socket 风险（避免）
  
方案 B: 分机
  - CI runner 用 Docker / Buildah
  - 业务全 K8s
  
方案 C: K8s 集群内跑 BuildKit / Kaniko
  - 完全统一 K8s
```

## 十、故障排查 SOP

### 10.1 速查表

| 症状 | 关键命令 |
|:---|:---|
| 容器启动失败 | `docker logs / events --since` |
| OOMKilled | `dmesg \| grep -i oom` / `docker inspect` |
| 网络不通 | `docker network inspect` / `iptables-save` |
| 端口冲突 | `ss -lntp` / `docker port` |
| 性能慢 | `docker stats` / `top -p $(pgrep)` |
| 磁盘满 | `docker system df` / `du -sh /var/lib/docker/*` |
| Pull 失败 | `docker info \| grep mirrors` / 防火墙 / DNS |
| BuildKit 慢 | 看 Builder log + cache hit |
| HEALTHCHECK 失败 | `docker inspect --format='{{json .State.Health}}'` |
| ImagePullBackOff | secret / mirror / quota / 网络 |

### 10.2 经典案例

#### case 1: 容器频繁 OOM
```
1. docker inspect 看 memory limit
2. dmesg | tail -50 找 OOM-killer
3. 看应用 metrics 内存曲线
4. JVM: -Xmx 必小于 limit * 0.8 + -XX:+UseContainerSupport
5. 调整 limit 或优化代码
```

#### case 2: pull 失败
```
1. docker info | grep -A 3 Mirrors
2. curl -v <mirror>
3. 看 /etc/resolv.conf DNS
4. Harbor 端: 看 robot account / project 权限
5. 拉私有镜像: docker login + secret
```

#### case 3: 容器内 DNS 慢
```
1. docker run 加 --dns=119.29.29.29
2. 改 daemon.json:
   { "dns": ["119.29.29.29","223.5.5.5"] }
3. K8s 用 NodeLocal DNSCache
4. 应用层不要每次 lookup（DNS cache）
```

#### case 4: /var/lib/docker 撑爆
```
1. docker system df -v
2. docker system prune -af --filter "until=168h"
3. 日志 rotate (daemon.json)
4. 长期: 单独分区 + 定时 GC
```

#### case 5: 性能差
```
1. docker stats 看资源
2. perf / bpftrace 看 syscall 热点
3. 看 storage driver (overlay2 ✓)
4. cgroup v1 vs v2，systemd cgroup driver 一致
5. 网络 host vs bridge 试
```

### 10.3 升级 / 兼容性

```
Docker → containerd 切换:
☐ K8s 节点排空 (cordon + drain)
☐ kubelet 配置改
☐ 验证 crictl ps
☐ 灰度

镜像格式兼容:
  OCI Image v1.0 / v1.1 通用
  Docker Image v2 schema 2
  
旧集群升级容器运行时:
  必看 K8s deprecation
  Docker Hub 拉限速 → Proxy Cache
```

## 十一、国产化路径

### 11.1 渐进替代矩阵

```
组件         国际方案           国产方案
─────────────────────────────────────────
OS          Ubuntu/RHEL       openEuler/麒麟/UOS/Anolis
引擎        Docker CE         iSulad / containerd
仓库        Docker Hub        Harbor + DaoCloud 加速
扫描        Trivy             长亭洞鉴 / 奇安信
签名        cosign            cosign + 国密 HSM
监控        Prometheus        夜莺 / 阿里 ARMS / DeepFlow
GPU         NVIDIA CUDA       昇腾 CANN / 摩尔 MUSA
机密计算    SEV-SNP/TDX       海光 CSV
K8s         上游 K8s          KubeSphere / 华为 CCE / 腾讯 TKE
```

### 11.2 试点 → 落地节奏

```
2026:
  ☐ 一节点 openEuler + iSulad 跑通
  ☐ Harbor + 国密 TLS
  ☐ 鲲鹏/飞腾 ARM64 镜像 build & deploy
  ☐ 海光 CSV CoCo PoC
  
2027:
  ☐ 党政关基业务全栈信创
  ☐ 国产 GPU (昇腾 910B) 训练镜像
  ☐ 夜莺 / DeepFlow 监控
  ☐ 国测中心容器测评
  
2028+:
  ☐ 通用业务渐进信创
  ☐ Wasm + 国产边缘 (iSulad 边缘版)
```

## 十二、典型坑（最佳实践）

| 坑 | 建议 |
|:---|:---|
| **CI 用 admin 账号 push** | 必须 Robot Account |
| **Trivy 扫不阻断** | exit 1 必接 CI 退出 |
| **HEALTHCHECK 没接 K8s** | livenessProbe + readinessProbe 一致 |
| **Java -Xmx > 容器 limit** | -Xmx ≤ limit * 0.75 |
| **不用 init 容器** | tini / dumb-init 处理僵尸进程 |
| **Multi-stage 没 stage 名** | --target 难精确 build |
| **基础镜像不更新** | 月度 CVE 升级 |
| **Harbor 不做 Replication** | 单点风险 |
| **K8s 节点直拉公网** | 必接 Proxy Cache |
| **prod tag 可变** | Tag immutability 开启 |
| **没有 SBOM** | 供应链审计无据 |
| **不签名** | K8s 准入装不上 |
| **多团队无 Project 隔离** | Harbor RBAC + 配额 |
| **Build 用 docker-in-docker** | 改 Kaniko / Buildkit-in-K8s |
| **没监控 Harbor 容量** | 撑爆 GC 不及时 |
| **dockershim 还在生产** | K8s 1.24+ 必换 containerd |

## 十三、最佳实践 Checklist

```
镜像规范:
☐ 命名 + tag 规约
☐ 镜像分级 (L0-L3)
☐ Dockerfile 团队基线 + LABEL 元数据
☐ 质量门禁: 多阶段+nonroot+HEALTHCHECK+Trivy 通过

仓库治理:
☐ Harbor 多 Project + RBAC + Robot
☐ Tag 不可变（prod）
☐ Replication 跨 Region
☐ Proxy Cache 代理上游
☐ 保留策略 + 月度 GC

CI/CD:
☐ test → lint → build → scan → sign → push → deploy
☐ 多架构 amd64 + arm64
☐ 缓存分层（registry + L1）
☐ SBOM + Provenance 自动生成
☐ Promote 用 imagetools 不重 build

监控:
☐ cAdvisor + Prometheus + Grafana
☐ Loki / ELK 集中日志
☐ DeepFlow / Tetragon eBPF 可观测
☐ 关键告警全覆盖

安全:
☐ rootless / userns / cap-drop
☐ seccomp + AppArmor
☐ K8s PSS + Gatekeeper
☐ Falco / Tetragon
☐ cosign 签名 + policy-controller
☐ 等保 / CIS / NIST 800-190 自查

容量:
☐ /var/lib/* 独立分区
☐ 日志 rotate + GC cron
☐ Harbor 容量监控
☐ 镜像分级保留

K8s 接管:
☐ dockershim 替换为 containerd
☐ K8s 节点最佳实践（cgroup v2 + systemd cgroup）
☐ GitOps + ArgoCD/Flux

国产化:
☐ openEuler/麒麟 + iSulad 试点
☐ ARM64 镜像 build & deploy
☐ 海光 CSV CoCo PoC
☐ 夜莺 / DeepFlow 监控
☐ 国密 TLS / HSM 签名
```

## 十四、典型生产架构模板

### 14.1 互联网中型企业

```
开发:     Docker Desktop / Rancher Desktop + Compose
CI:       GitLab CI + Buildx + Trivy + cosign
仓库:     Harbor (2 Region 复制 + Proxy Cache)
集群:     K8s (containerd) + ArgoCD + Cilium + Istio
监控:     Prometheus + Loki + Tempo + DeepFlow
安全:     Falco + Gatekeeper + Trivy Operator
镜像策略: 多阶段 + distroless + cosign 签名
团队:     5-20 人 SRE + DevOps
```

### 14.2 大型央企信创

```
开发:     Docker / Podman + openEuler
CI:       Jenkins + Buildah + 长亭扫描 + cosign+国密 HSM
仓库:     Harbor (国密 TLS) + Replication 跨灾备
集群:     KubeSphere / 华为 CCE + containerd + iSulad 混合
监控:     夜莺 + DeepFlow + 阿里 ARMS
安全:     奇安信 / 启明星辰 + Falco + Tetragon
合规:     等保三级 / 数据安全法 / 国测中心
信创:     鲲鹏 + openEuler + GaussDB + 海光 CSV
```

### 14.3 AI 训练平台

```
基础镜像: pytorch:2.4-cuda12.4 + 团队加 ai-base
仓库:     Harbor 含训练镜像 5-10 GB / 个
GPU:      NVIDIA Container Toolkit + GPU Operator + MIG
国产 GPU: 昇腾 / 摩尔 平行栈
集群:     K8s + Volcano / Kueue 批调度
存储:     Ceph + NFS + S3 训练数据 lake
监控:     DCGM exporter + Prometheus + Grafana
机密:     Kata + 海光 CSV (重要客户)
```

### 14.4 边缘 / IoT

```
节点:     ARM64 / RISC-V + openEuler Embedded
引擎:     iSulad / k3s + containerd
镜像:     多架构 + 极小化 (< 30 MB)
分发:     Harbor + Proxy Cache + KubeEdge 离线
监控:     DeepFlow + 轻量 Prometheus
管理:     KubeEdge / OpenYurt 云边协同
```

## 十五、学习路径

```
工程化（6 月）:
  1. CI/CD 全链 (lint+scan+sign+SBOM+Provenance)
  2. Harbor 多 Project + Replication + Proxy Cache
  3. 镜像规范 + Dockerfile 团队基线
  4. cAdvisor + Prometheus + Loki + Falco
  5. CIS + 等保 自查
  6. K8s 节点 containerd 切换演练
  7. 镜像 Promote + 回滚 SOP

平台化（12 月+）:
  8. ArgoCD GitOps + 多环境
  9. Cosign + sigstore policy-controller
  10. DeepFlow / Tetragon eBPF 接入
  11. 多架构 ARM64 build 池
  12. 国产化栈一遍 (openEuler + iSulad + 国密)
  13. AI / GPU 容器平台
  14. 机密计算 (Kata-cc / 海光 CSV)
```

> 📖 **核心判断**：Docker 最佳实践 = **运行时选型 + 镜像规范 + Harbor 治理 + CI/CD 流水线 + 监控告警 + 安全合规 + 容量 + 多架构 + K8s 接管节奏 + 国产化**。能在白板上画出 "GitLab CI → Trivy → cosign → Harbor → ArgoCD → K8s + Falco" 全链、能给团队定 Dockerfile 基线 + 镜像分级 + 仓库 RBAC、能跑通 CIS + 等保三级 自查 + 国产化栈试点，就具备容器平台负责人能力。**镜像规范 + 仓库治理 + 签名供应链 + 监控告警** 是从工程师到平台负责人的四个分水岭。
