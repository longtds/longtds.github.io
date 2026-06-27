# 进阶

> Docker 进阶 = **BuildKit 深度 + 多阶段+多架构 + Buildx 缓存 + Harbor 私有仓库 + 镜像签名(cosign)+SBOM + 网络深度(bridge/macvlan/iptables) + 存储驱动 + 镜像优化 + Compose 生产用法 + 日志/监控/调优 + rootless + 安全加固**。本章面向独立运维容器化平台 50-500 容器规模的工程师。

## 一、BuildKit 深度

### 1.1 启用

```bash
# Docker 23+ 默认启用 BuildKit
docker version | grep -i build

# 或显式
export DOCKER_BUILDKIT=1
docker build .

# Compose
export COMPOSE_DOCKER_CLI_BUILD=1
```

### 1.2 Buildx 多 builder

```bash
# 创建独立 builder（推荐）
docker buildx create --use --name builder-multi \
  --driver docker-container \
  --driver-opt image=moby/buildkit:v0.13.0,network=host

docker buildx inspect --bootstrap
docker buildx ls

# 切换
docker buildx use builder-multi
```

### 1.3 多架构构建

```bash
# 安装 QEMU（跨架构必需）
docker run --privileged --rm tonistiigi/binfmt --install all

# 一次推多架构
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/ppc64le \
  -t myregistry/myapp:1.0 \
  --push .

# Manifest List 自动生成
docker buildx imagetools inspect myregistry/myapp:1.0
```

### 1.4 BuildKit 缓存

```dockerfile
# syntax=docker/dockerfile:1.6
FROM golang:1.22-alpine AS builder
WORKDIR /src

# 用 cache mount（go mod 缓存不重下）
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download

COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -o /app

# Apt 缓存
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y curl

# Npm 缓存
RUN --mount=type=cache,target=/root/.npm \
    npm ci
```

### 1.5 远程缓存

```bash
# Registry cache
docker buildx build \
  --cache-from type=registry,ref=myregistry/myapp:buildcache \
  --cache-to type=registry,ref=myregistry/myapp:buildcache,mode=max \
  -t myapp:1.0 --push .

# 本地 cache
docker buildx build \
  --cache-from type=local,src=/tmp/cache \
  --cache-to type=local,dest=/tmp/cache \
  -t myapp:1.0 .

# S3 / GHA cache
--cache-to type=gha,mode=max
```

### 1.6 Secret / SSH 安全注入

```dockerfile
# 不留痕迹注入构建期密钥
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci

RUN --mount=type=ssh \
    git clone git@github.com:org/private-repo.git
```

```bash
docker buildx build \
  --secret id=npmrc,src=$HOME/.npmrc \
  --ssh default \
  -t myapp:1.0 .
```

## 二、镜像优化

### 2.1 体积优化清单

```
☐ 多阶段构建
☐ 基础镜像 distroless / scratch / alpine
☐ 一次性 RUN 合并 (&&)
☐ 清理 apt / yum cache
☐ .dockerignore 过滤
☐ 不带源码 / build 工具
☐ Go/Rust: CGO=0 + static + strip
☐ Python: --no-cache-dir + 多阶段 wheel
☐ Node: npm ci --omit=dev + 多阶段
☐ Java: jlink + custom JRE
☐ 用 dive 分析每层
```

### 2.2 dive 分析层

```bash
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive:latest myapp:1.0

# 关注:
# - 浪费 (Wasted) 是否过大
# - 哪一层增量异常
# - 是否有 sensitive 文件残留
```

### 2.3 各语言模板

```dockerfile
# --- Go ---
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /app
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app /app
ENTRYPOINT ["/app"]

# --- Python ---
FROM python:3.12-slim AS builder
WORKDIR /src
RUN pip install --no-cache-dir --user -r requirements.txt
FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
WORKDIR /app
COPY . .
USER 1000:1000
CMD ["python", "-m", "myapp"]

# --- Node ---
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
FROM node:20-alpine
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
USER node
CMD ["node", "server.js"]

# --- Java (jlink) ---
FROM eclipse-temurin:21-jdk AS jre-build
RUN jlink --add-modules java.base,java.logging,java.naming,java.sql \
    --strip-debug --no-man-pages --no-header-files --compress=2 \
    --output /jre
FROM debian:12-slim
COPY --from=jre-build /jre /opt/jre
COPY app.jar /app/app.jar
ENV PATH=/opt/jre/bin:$PATH
CMD ["java","-jar","/app/app.jar"]
```

### 2.4 极端瘦身: scratch + static

```dockerfile
# Go 静态二进制 → 仅 ~10 MB 镜像
FROM golang:1.22 AS b
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w -extldflags '-static'" -o /app
FROM scratch
COPY --from=b /app /app
ENTRYPOINT ["/app"]
```

## 三、Harbor 私有仓库

### 3.1 部署

```bash
# Harbor 2.10+
wget https://github.com/goharbor/harbor/releases/download/v2.10.0/harbor-offline-installer-v2.10.0.tgz
tar xf harbor-offline-installer-*.tgz
cd harbor
cp harbor.yml.tmpl harbor.yml

# 编辑 harbor.yml
hostname: harbor.example.com
https:
  certificate: /etc/harbor/certs/harbor.crt
  private_key: /etc/harbor/certs/harbor.key
harbor_admin_password: ChangeMe...le_trivy: true

./prepare
./install.sh --with-trivy --with-notary
```

### 3.2 多租户与权限

```
Project (项目):
  - 公开 / 私有
  - 成员角色: Maintainer / Developer / Guest / Limited Guest
  - 配额: 镜像数量 / 存储

Robot Account (机器人):
  - 用于 CI/CD（不要用 admin 密码）
  - 细粒度权限（push/pull/scan）

Tag immutability (标签不可变):
  - 防止 prod tag 被覆盖
```

### 3.3 关键能力

```
✅ 镜像复制 (Replication)        多机房同步
✅ 漏洞扫描 (Trivy / Clair)       PR 阻断
✅ 镜像签名 (Notary / Cosign)
✅ 镜像保留策略                  按 tag/时间清理
✅ 仓库代理 (Proxy Cache)         缓存 Docker Hub / quay.io
✅ 国密 TLS                       Tongsuo 集成
✅ Webhook                       推送/扫描事件
✅ OIDC / LDAP 接入
```

### 3.4 镜像保留策略

```yaml
# Project → Policy → Retention
保留规则:
  - 标签匹配 v* 的最近 10 个
  - latest 永久
  - 其他 14 天
  
自动 GC:
  - 每周日凌晨执行
  - 删未引用层
```

### 3.5 Proxy Cache（推荐）

```
新建 Project: docker-proxy
类型: 代理项目
源仓库: https://docker.m.daocloud.io (国产加速)
访问方式:
  docker pull harbor.example.com/docker-proxy/nginx:1.27
  
内网集群一律走 Harbor，避免对外
```

## 四、镜像签名与 SBOM

### 4.1 cosign 签名

```bash
# 生成密钥
cosign generate-key-pair
# 或 keyless（OIDC）
cosign sign --yes harbor.example.com/myproj/myapp:1.0

# 验证
cosign verify --key cosign.pub harbor.example.com/myproj/myapp:1.0

# K8s 准入控制
# 安装 sigstore-policy-controller，给 namespace 加 label 强制验签
```

### 4.2 SBOM（软件物料清单）

```bash
# Syft
syft myapp:1.0 -o spdx-json > sbom.json
syft myapp:1.0 -o cyclonedx-json > sbom.cdx.json

# Trivy 直接生成
trivy image --format cyclonedx --output sbom.json myapp:1.0

# 推到 OCI Artifact（cosign）
cosign attach sbom --sbom sbom.json myapp:1.0
cosign attest --predicate sbom.json --type cyclonedx myapp:1.0
```

### 4.3 SLSA / Provenance

```bash
# Buildx 自动生成 SLSA Provenance
docker buildx build \
  --attest type=provenance,mode=max \
  --attest type=sbom \
  -t myapp:1.0 --push .

# Harbor / cosign 验证 Provenance
cosign verify-attestation --type slsaprovenance \
  --key cosign.pub harbor.example.com/myproj/myapp:1.0
```

## 五、网络深度

### 5.1 bridge 内部机制

```
docker0 (172.17.0.1/16)
  ├─ veth-xxx ─── eth0@容器 1
  ├─ veth-yyy ─── eth0@容器 2

iptables -t nat -L DOCKER -n
iptables -t filter -L DOCKER -n

# DNS
容器内 /etc/resolv.conf 自动写 nameserver 127.0.0.11
（Docker 内嵌 DNS 服务器，解析容器名）
```

### 5.2 自定义 bridge

```bash
docker network create app-net \
  --subnet 10.10.0.0/24 \
  --gateway 10.10.0.1 \
  --opt com.docker.network.bridge.name=br-app \
  --opt com.docker.network.driver.mtu=1500

docker run -d --name db --network app-net --ip 10.10.0.10 mysql:8
```

### 5.3 macvlan / ipvlan

```bash
# macvlan: 容器拿物理 IP（生产推荐）
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=eth0 macnet

docker run -d --name app --network macnet --ip 192.168.1.100 nginx
# 注意：宿主机无法访问该 IP（macvlan 隔离），需 macvlan-bridge 模式或加 sub-interface

# ipvlan: 共享 MAC，可用于 SR-IOV
docker network create -d ipvlan \
  --subnet=192.168.1.0/24 \
  -o parent=eth0 -o ipvlan_mode=l2 ipvnet
```

### 5.4 host / container 模式

```bash
# host：极致性能，但端口冲突
docker run --network host nginx

# container：与 K8s Pod 模型一致
docker run -d --name net-shared alpine sleep infinity
docker run --network container:net-shared nginx
```

### 5.5 端口暴露与防火墙

```bash
# Docker 改 iptables，可能绕过 ufw/firewalld
# 解决:
{
  "iptables": true,
  "userland-proxy": false
}

# 仅绑本机
-p 127.0.0.1:8080:80

# DOCKER-USER 链（自定义规则放这里）
iptables -I DOCKER-USER -i ext-eth0 -p tcp --dport 3306 -j DROP
```

### 5.6 IPv6

```json
{
  "ipv6": true,
  "fixed-cidr-v6": "2001:db8::/64",
  "experimental": true,
  "ip6tables": true
}
```

## 六、存储驱动深度

### 6.1 overlay2 内部

```
/var/lib/docker/overlay2/
  <id>/
    lower    ← 父镜像层
    upper    ← 容器写层
    work     ← overlay 工作目录
    merged   ← 合并视图（容器内看到的）
    diff     ← 实际写入文件

# 看驱动
docker info | grep -i 'storage driver'

# 单独分区（生产强烈推荐）
/var/lib/docker  → 独立 XFS / ext4 / LVM
```

### 6.2 daemon.json 调优

```json
{
  "data-root": "/data/docker",
  "storage-driver": "overlay2",
  "storage-opts": ["overlay2.override_kernel_check=true"],
  "default-shm-size": "256m",
  "default-ulimits": {
    "nofile": { "Name": "nofile", "Hard": 1048576, "Soft": 1048576 },
    "nproc":  { "Name": "nproc",  "Hard": 65536,  "Soft": 65536 }
  },
  "live-restore": true,
  "log-driver": "json-file",
  "log-opts": { "max-size": "100m", "max-file": "5", "compress": "true" },
  "registry-mirrors": ["https://docker.m.daocloud.io"],
  "insecure-registries": ["harbor.example.com"],
  "exec-opts": ["native.cgroupdriver=systemd"],
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 10
}
```

关键：

- `live-restore: true` → daemon 重启容器不挂
- `native.cgroupdriver=systemd` → 与 K8s 一致
- `data-root` 独立大盘（防 /var 撑爆）

## 七、Compose 生产用法

### 7.1 多文件 + Profiles + Override

```
compose.yaml              基础
compose.override.yaml     开发覆盖（自动加载）
compose.prod.yaml         生产覆盖
compose.monitoring.yaml   监控套件 (profile)

# 启动
docker compose -f compose.yaml -f compose.prod.yaml --profile monitoring up -d
```

### 7.2 健康检查 + 依赖编排

```yaml
services:
  db:
    image: mysql:8.0
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-p$$MYSQL_ROOT_PASSWORD"]
      interval: 5s
      timeout: 3s
      retries: 20
      start_period: 30s
  web:
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
```

### 7.3 资源 / 安全 / 日志

```yaml
services:
  web:
    image: myapp:1.0
    read_only: true
    tmpfs: [/tmp, /run]
    user: "1000:1000"
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    security_opt:
      - no-new-privileges:true
      - seccomp:./seccomp.json
    deploy:
      resources:
        limits: { cpus: '1', memory: 512M }
        reservations: { cpus: '0.5', memory: 256M }
    logging:
      driver: json-file
      options: { max-size: "100m", max-file: "5" }
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost/health"]
```

### 7.4 Secret 管理

```yaml
secrets:
  db_password:
    file: ./secrets/db_password.txt
services:
  web:
    secrets: [db_password]
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
```

应用从 `/run/secrets/<name>` 读，不入环境变量（更安全）。

## 八、日志方案

### 8.1 集中日志

```
方案 A: stdout/stderr + 日志驱动
  - json-file（默认，本机）
  - fluentd → Loki / ELK
  - gelf → Graylog
  - syslog
  
方案 B: 应用自写 + Filebeat/Vector/Promtail sidecar
方案 C: K8s 节点级 (DaemonSet)
```

### 8.2 fluentd 驱动

```yaml
services:
  web:
    logging:
      driver: fluentd
      options:
        fluentd-address: "localhost:24224"
        tag: "docker.{{.Name}}"
        fluentd-async: "true"
```

### 8.3 Loki 主流栈

```yaml
# Promtail 抓所有容器 stdout
services:
  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/log:/var/log:ro
      - ./promtail.yaml:/etc/promtail/config.yaml
```

## 九、监控与可观测

### 9.1 cAdvisor + Prometheus + Grafana

```yaml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.49.0
    privileged: true
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    ports: ["8080:8080"]
  prometheus:
    image: prom/prometheus
    volumes: [./prometheus.yml:/etc/prometheus/prometheus.yml]
    ports: ["9090:9090"]
  grafana:
    image: grafana/grafana
    ports: ["3000:3000"]
```

### 9.2 Docker daemon metrics

```json
// daemon.json
{
  "metrics-addr": "0.0.0.0:9323",
  "experimental": true
}
```

### 9.3 关键指标

```
容器:
  container_cpu_usage_seconds_total
  container_memory_usage_bytes
  container_memory_rss
  container_fs_usage_bytes
  container_network_receive_bytes_total
  container_network_transmit_bytes_total

引擎:
  engine_daemon_container_states
  engine_daemon_events_total
```

## 十、Rootless Docker

### 10.1 启用

```bash
# 先关 systemd docker
systemctl stop docker
systemctl disable docker

# 装 rootless（用户级）
dockerd-rootless-setuptool.sh install

systemctl --user start docker
systemctl --user enable docker

# 环境
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
docker info
```

### 10.2 收益与代价

```
收益:
  - daemon 不需要 root
  - 容器逃逸不能直接拿宿主 root
  - 多租户安全
  
代价:
  - 网络性能下降（slirp4netns）
  - 不能 --privileged
  - 端口 < 1024 需 capability 或代理
  - cgroup v2 + user namespace 必备
  - 部分网卡 / 设备 直通不可用
```

## 十一、安全加固

### 11.1 daemon 层

```json
{
  "userns-remap": "default",       // 启用 user ns 映射
  "no-new-privileges": true,
  "live-restore": true,
  "log-driver": "json-file",
  "icc": false,                    // 容器间默认禁通信
  "userland-proxy": false,
  "seccomp-profile": "/etc/docker/seccomp.json"
}
```

### 11.2 容器层

```bash
docker run -d \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop=ALL --cap-add=NET_BIND_SERVICE \
  --security-opt no-new-privileges:true \
  --security-opt seccomp=/etc/docker/seccomp.json \
  --pids-limit=200 \
  --memory=512m --cpus=1 \
  --user 1000:1000 \
  myapp:1.0
```

### 11.3 镜像扫描接入 CI

```yaml
# GitLab CI / GitHub Actions / Jenkins 通用
trivy-scan:
  image: aquasec/trivy:latest
  script:
    - trivy image --severity HIGH,CRITICAL --exit-code 1 --no-progress myapp:$CI_COMMIT_SHA
    - trivy fs --severity HIGH,CRITICAL --exit-code 1 .
```

### 11.4 OPA / Kyverno（容器准入）

K8s 层强制：禁特权 / 必须签名 / 必扫描通过 → 见 [07_Kubernetes](../../07_Kubernetes/index.md)。

## 十二、调优

### 12.1 性能

```
☐ /var/lib/docker 单独 XFS/ext4，关 atime
☐ overlay2（不要 devicemapper）
☐ cgroup v2 (systemd cgroup driver)
☐ ulimit nofile 1M
☐ shm-size 按需调（默认 64M 不够 Java）
☐ network MTU 与上联一致
☐ DPDK / SR-IOV 走 K8s + Multus
```

### 12.2 GC / 清理

```bash
# 手工
docker system df
docker system prune -af --volumes
docker image prune -af
docker builder prune -af --filter "until=168h"

# 自动（cron）
0 3 * * 0 docker system prune -af --filter "until=168h" >/var/log/docker-gc.log 2>&1
```

### 12.3 BuildKit GC 配置

```toml
# /etc/buildkit/buildkitd.toml
[worker.oci]
  gc = true
  gckeepstorage = 30000  # MB
[[worker.oci.gcpolicy]]
  keepBytes = 10737418240
  keepDuration = 604800
  filters = ["type==source.local","type==exec.cachemount","type==source.git.checkout"]
```

## 十三、典型坑（进阶）

| 坑 | 建议 |
|:---|:---|
| **BuildKit 缓存爆盘** | gc 策略 + 定时清 |
| **多架构 manifest 不刷** | 用 imagetools，不用旧 push |
| **macvlan 宿主访问不到** | macvlan-bridge 或专 IP |
| **iptables 被 firewalld 改坏** | DOCKER-USER 链 |
| **systemd cgroup vs cgroupfs 不一致** | daemon.json 显式 systemd |
| **Harbor 复制慢** | 调线程 + Proxy Cache |
| **Trivy 数据库下载失败** | mirror.gcr.io / 内部缓存 |
| **cosign 验签 K8s 没生效** | 装 policy-controller + label |
| **rootless 性能差** | 网络用 vpnkit / slirp4netns + portforward |
| **/var/lib/docker 撑爆** | 独立分区 + 日志 rotate + prune cron |
| **Compose v1 命令仍在用** | 一律 `docker compose` |
| **HEALTHCHECK 不接 K8s** | 配合 livenessProbe |

## 十四、进阶 Checklist

```
构建:
☐ BuildKit + Buildx 多 builder
☐ 多架构 amd64/arm64 一次推
☐ 远程 cache (registry / S3 / GHA)
☐ Secret/SSH 注入安全
☐ SLSA Provenance + SBOM

镜像:
☐ distroless / scratch 多阶段
☐ dive 看每层
☐ Trivy 扫无 HIGH+
☐ cosign 签名

仓库:
☐ Harbor 部署
☐ Replication / Proxy Cache
☐ 标签不可变 + 保留策略
☐ Robot Account CI/CD 用

网络:
☐ 自定义 bridge / macvlan / ipvlan
☐ iptables DOCKER-USER 自定义
☐ live-restore + userns-remap

存储:
☐ /var/lib/docker 独立分区
☐ daemon.json 调优
☐ Volume 备份策略

Compose:
☐ Profiles + override 多文件
☐ healthcheck + depends_on
☐ secret/config 文件挂载
☐ 资源/安全/日志限额

安全:
☐ Trivy CI 阻断
☐ cosign 签名 + K8s 准入
☐ rootless / userns-remap
☐ seccomp/AppArmor
☐ 网络分段 + icc=false

监控:
☐ cAdvisor + Prometheus + Grafana
☐ 集中日志 Loki/ELK
☐ daemon metrics 抓
```

## 十五、推荐栈

```
构建:        Buildx + BuildKit + 多阶段 + 多架构
缓存:        Registry cache / S3 cache / GHA cache
仓库:        Harbor ⭐ + Proxy Cache + Trivy + Notary/Cosign
扫描:        Trivy ⭐ + Grype + Dockle (CIS)
签名:        cosign + sigstore policy-controller
SBOM:        Syft + CycloneDX / SPDX
基础镜像:    distroless / chainguard / wolfi / alpine
日志:        Loki + Promtail / Fluentd + ELK
监控:        cAdvisor + Prometheus + Grafana / 夜莺
运行时:      docker / containerd / podman + crun (轻量)
单机编排:    Docker Compose v2 + Profiles
安全:        rootless + userns + seccomp + AppArmor
国产:        Harbor + 国密 + DaoCloud 加速 + iSulad + 麒麟 OS
```

## 十六、学习路径

```
进阶（3-12 月）:
  1. BuildKit + Buildx 多架构 + 缓存
  2. distroless + dive + Trivy 优化镜像 < 50MB
  3. Harbor 部署 + Replication + Proxy Cache
  4. cosign 签名 + SBOM + Provenance
  5. macvlan / ipvlan / iptables 排障
  6. /var/lib/docker 调优 + daemon.json
  7. Compose 生产用法（健康+secret+profiles）
  8. cAdvisor + Prometheus + Loki 监控全链
  9. rootless docker 试点
  10. K8s + containerd 接管 (见 07_K8s)
```

> 📖 **核心判断**：进阶 = **BuildKit 多架构 + 镜像优化(distroless/dive) + Harbor 仓库 + cosign 签名+SBOM + macvlan/iptables 网络 + daemon.json 调优 + Compose 生产 + cAdvisor+Prometheus 监控 + rootless+seccomp 安全**。能搭出"Harbor + Trivy + cosign + Proxy Cache + 多架构 CI"完整流水线、能把镜像从 1GB 砍到 50MB、能用 macvlan 让容器拿物理 IP、能跑通 rootless docker，就具备容器化平台运维能力。**容器是 K8s 的底座，但单机/边缘/CI 仍大量直用 Docker**，进阶不可跳过。
