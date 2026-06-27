# 基础

> Docker 基础 = **容器原理(namespace+cgroup+rootfs) + Docker 架构(daemon/containerd/runc) + 镜像/容器/仓库 三件套 + Dockerfile 编写 + docker CLI + 网络/存储基础 + Compose 单机编排 + 安全基线 + 国产化镜像**。本章面向入职 1 年内的工程师，先把容器"是什么、能干什么、怎么用"打通。

## 一、容器是什么

### 1.1 一句话

```
容器 = 进程 + namespace(隔离视图) + cgroup(限制资源) + rootfs(独立文件系统)
     = 共享内核的"轻量虚拟机"
     ≠ 虚拟机（VM 有独立内核 + Hypervisor）
```

### 1.2 与 VM 对比

| 维度 | 容器 | VM |
|:---|:---|:---|
| 隔离 | namespace/cgroup（共享内核） | 完整 OS（独立内核） |
| 启动 | 秒级 ⭐ | 分钟级 |
| 大小 | MB | GB |
| 性能 | 接近裸机 ⭐ | ~5-10% 损耗 |
| 密度 | 高（单机 1000+） | 中（单机 10-100） |
| 隔离强度 | 弱（共享内核漏洞） | 强 ⭐ |
| 适用 | 微服务 / CI / Web / 计算 | 老系统 / Windows / 多内核 |

### 1.3 历史时间线（关键节点）

```
2008  Linux Container (LXC)
2013  Docker 0.x  (Solomon Hykes, dotCloud)
2014  Docker 1.0
2015  OCI (Open Container Initiative) 成立
2016  Docker Swarm
2017  containerd 独立 / Kubernetes 胜出
2018  CRI-O / runc 标准
2020  Docker 桌面收费 → Podman 兴起
2021  Kubernetes 弃用 dockershim
2022  Docker Desktop / Compose v2 / BuildKit
2023  Wasm 容器 / Confidential Containers
2024  rootless / OCI 镜像 v1.1 / 国产容器引擎
2025  Sysbox / Kata / Confidential 主流化
2026  WASM + microVM + 国产 OCI 引擎多线并进
```

## 二、底层原理（必懂）

### 2.1 namespace（隔离）

```
mnt     文件系统挂载
pid     进程号
net     网络栈（接口/路由/端口）
ipc     System V IPC / POSIX MQ
uts     hostname / domain
user    UID/GID 映射（rootless 核心）
cgroup  cgroup 视图（v2）
time    系统时间（5.6+）

# 看进程的 namespace
ls -l /proc/<pid>/ns/
lsns -p <pid>

# 进入容器 namespace
nsenter -t <host-pid> -a
```

### 2.2 cgroup（资源限制）

```
cgroup v1   (CentOS 7 默认，已废)
cgroup v2 ⭐ (主流，统一层级)

可限制:
  cpu / cpuset / memory / io / pids / hugetlb / freezer / devices

# 查看 cgroup v2 当前层级
mount | grep cgroup2
cat /sys/fs/cgroup/cgroup.controllers

# Docker 容器对应 cgroup 路径
/sys/fs/cgroup/system.slice/docker-<container-id>.scope/
```

### 2.3 rootfs（联合文件系统）

```
传统: chroot + 完整 OS 拷贝（大、重）
Docker: 联合挂载 (Union FS)，分层叠加

存储驱动:
  overlay2 ⭐ (推荐，主流)
  fuse-overlayfs (rootless)
  btrfs / zfs (特殊场景)
  devicemapper (历史)

镜像 = 多层只读层
容器 = 镜像层 + 上层 RW 层

查看:
  docker info | grep -i storage
  docker inspect <ctr> | jq '.[0].GraphDriver'
```

### 2.4 网络（CNI 出现前）

```
默认 bridge:
  docker0 网桥 + veth pair + iptables NAT
  
模式:
  bridge       默认，独立 IP，NAT 出口
  host         共享宿主网络栈
  none         无网络
  container    与其他容器共享
  macvlan      直接挂物理网（生产用）
  ipvlan       新方案
  overlay      Swarm/K8s 跨主机
```

## 三、Docker 架构

### 3.1 组件分层

```
┌───────────────────────────────┐
│   docker CLI (用户)            │
└──────────────┬────────────────┘
               │ REST API
┌──────────────▼────────────────┐
│   dockerd (Docker Daemon)      │
└──────────────┬────────────────┘
               │ gRPC
┌──────────────▼────────────────┐
│   containerd                   │  (CNCF)
└──────────────┬────────────────┘
               │ shim
┌──────────────▼────────────────┐
│   runc (OCI Runtime)           │  (CNCF)
└──────────────┬────────────────┘
               ▼
        Linux namespace + cgroup
```

### 3.2 为什么拆这么细

```
1. Kubernetes 不需要 dockerd → 直接 containerd
2. runc 可替换为 crun / kata / gvisor / youki
3. containerd 可被 K8s/Nerdctl/Buildkit 共享
4. 解耦 + OCI 标准
```

### 3.3 OCI 标准

```
OCI Image Spec       镜像格式 (manifest + config + layers)
OCI Runtime Spec     运行时规范 (config.json + bundle)
OCI Distribution Spec  仓库 API (v2)

意义:
  - 镜像互通（Docker/Podman/buildah 都能用）
  - 运行时可换（runc/crun/youki/kata/gvisor）
  - 仓库可换（registry/Harbor/JFrog/ACR/TCR）
```

## 四、安装与第一个容器

### 4.1 安装

```bash
# Ubuntu 22.04/24.04
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
docker version
docker info

# CentOS / RHEL / openEuler / 麒麟
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-buildx-plugin

# 国产镜像加速（必做）
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ],
  "log-driver": "json-file",
  "log-opts": { "max-size": "100m", "max-file": "3" },
  "storage-driver": "overlay2",
  "default-ulimits": { "nofile": { "Name": "nofile", "Hard": 65536, "Soft": 65536 } }
}
EOF
systemctl restart docker

# 非 root 用户用 docker
usermod -aG docker $USER
newgrp docker
```

### 4.2 第一个容器

```bash
docker run --rm -it alpine sh
docker run -d --name web -p 8080:80 nginx:1.27-alpine
curl http://localhost:8080
docker logs -f web
docker exec -it web sh
docker stop web
docker rm web
```

## 五、镜像 / 容器 / 仓库

### 5.1 镜像操作

```bash
# 拉取 / 推送
docker pull nginx:1.27
docker push myregistry/myapp:1.0

# 列表 / 详情
docker images
docker image inspect nginx:1.27
docker history nginx:1.27

# 命名 / 标签
docker tag nginx:1.27 myregistry/nginx:latest

# 导入 / 导出
docker save -o nginx.tar nginx:1.27
docker load -i nginx.tar

# 清理
docker image prune -a -f                        # 删未引用
docker system prune -a --volumes -f             # 大清理（慎用）
```

### 5.2 容器操作

```bash
# 运行
docker run -d --name web --restart unless-stopped \
  -p 80:80 -v /data:/usr/share/nginx/html:ro \
  -e TZ=Asia/Shanghai \
  --memory=512m --cpus=1 \
  nginx:1.27-alpine

# 生命周期
docker ps                       # 在跑
docker ps -a                    # 全部
docker start / stop / restart / pause / unpause / kill
docker rm -f <ctr>

# 进入
docker exec -it <ctr> sh
docker exec -u 0 <ctr> sh       # 以 root 进入

# 日志
docker logs -f --tail 100 <ctr>

# 拷贝
docker cp <ctr>:/etc/nginx/nginx.conf .
docker cp ./nginx.conf <ctr>:/etc/nginx/nginx.conf

# 看资源
docker stats
docker top <ctr>

# 改运行参数（少用，重启级）
docker update --memory=1g --cpus=2 <ctr>
```

### 5.3 仓库

```bash
# Docker Hub (国外，受限)
docker login

# 私有仓库
docker login registry.example.com
docker tag myapp:1.0 registry.example.com/myproj/myapp:1.0
docker push registry.example.com/myproj/myapp:1.0

# 主流私有仓库:
#   Harbor ⭐ (国产开源，最主流)
#   Docker Registry (官方简版)
#   JFrog Artifactory (商业)
#   Nexus Repository
#   阿里云 ACR / 腾讯 TCR / 华为 SWR (国产云厂)
```

## 六、Dockerfile（必会）

### 6.1 经典模板

```dockerfile
# syntax=docker/dockerfile:1.6

# ---- 构建阶段 ----
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
ARG VERSION=dev
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags "-X main.Version=$VERSION -s -w" -o /app

# ---- 运行阶段 ----
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app /app
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```

### 6.2 指令速查

| 指令 | 说明 |
|:---|:---|
| `FROM` | 基础镜像 |
| `ARG` / `ENV` | 构建/运行环境变量 |
| `WORKDIR` | 工作目录 |
| `COPY` / `ADD` | 复制文件（优先 COPY） |
| `RUN` | 执行命令（合并 && 减层） |
| `EXPOSE` | 端口元数据（不映射） |
| `VOLUME` | 数据卷挂载点 |
| `USER` | 运行用户（不要 root） |
| `ENTRYPOINT` + `CMD` | 入口 + 默认参数 |
| `HEALTHCHECK` | 健康检查 |
| `STOPSIGNAL` | 停止信号（默认 SIGTERM） |
| `LABEL` | 元数据标签 |

### 6.3 构建最佳实践

```
1. 多阶段构建      Build / Runtime 分离，运行镜像最小
2. 选最小基础镜像  distroless / alpine / scratch / wolfi
3. 固定版本        FROM nginx:1.27-alpine（不要 :latest）
4. 合并 RUN        减少层数 + apt clean
5. .dockerignore   过滤 node_modules / .git
6. ARG 注入版本    --build-arg VERSION=$(git rev-parse HEAD)
7. USER nonroot    不跑 root（安全）
8. HEALTHCHECK     生产必加
9. 缓存 mount      RUN --mount=type=cache,target=/root/.cache
10. SBOM + 签名    docker buildx + cosign（见安全）
```

### 6.4 构建命令

```bash
# 单架构
docker build -t myapp:1.0 .

# BuildKit + 多架构（推荐）
docker buildx create --use --name multi
docker buildx build --platform linux/amd64,linux/arm64 \
  -t myregistry/myapp:1.0 --push .

# 国产 ARM 必备
docker buildx build --platform linux/arm64 -t myapp:arm64 --load .
```

## 七、网络

### 7.1 默认网络

```bash
docker network ls               # bridge / host / none
docker network inspect bridge

# 自定义 bridge（推荐，支持 DNS）
docker network create app-net
docker run -d --name db --network app-net mysql:8
docker run -d --name web --network app-net -e DB_HOST=db nginx
# web 容器内可以 ping db (DNS 解析)
```

### 7.2 端口映射

```bash
-p 80:80          tcp 80 映射
-p 443:443/tcp    显式 tcp
-p 53:53/udp      udp
-p 127.0.0.1:8080:80   只绑本地
-P                自动随机映射 EXPOSE
```

### 7.3 网络模式速查

| 模式 | 命令 | 场景 |
|:---|:---|:---|
| bridge | 默认 | 一般业务 |
| host | `--network host` | 性能极致 / 需要直访宿主网 |
| none | `--network none` | 安全沙箱 |
| container | `--network container:xxx` | 共享网络栈（K8s Pod 模型） |
| macvlan | 自定义 driver | VM 风格直接拿物理 IP |
| overlay | Swarm/K8s | 跨主机 |

## 八、存储

### 8.1 三种挂载

```bash
# 1. Volume（推荐，托管）
docker volume create mydata
docker run -d -v mydata:/var/lib/mysql mysql:8

# 2. Bind Mount（开发常用）
docker run -d -v $PWD/data:/var/lib/mysql mysql:8
# 或新语法
docker run -d --mount type=bind,source=$PWD/data,target=/var/lib/mysql mysql:8

# 3. tmpfs（内存盘）
docker run -d --tmpfs /tmp:size=100m alpine

# 查看
docker volume ls
docker volume inspect mydata
docker volume prune -f          # 清未引用
```

### 8.2 生产建议

```
☐ 状态数据用 Volume / 外部存储（NFS/Ceph）
☐ 配置文件用 Bind Mount 或 Config
☐ 日志走 stdout/stderr（不要落容器内）
☐ 大数据 / DB 必须挂外部 PV
☐ 备份策略: 定期 docker run --rm 镜像备份卷
```

## 九、Docker Compose（单机编排）

### 9.1 入门

```yaml
# compose.yaml (v2 / Compose Spec)
services:
  db:
    image: mysql:8.0
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: app
    volumes:
      - db-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      retries: 5
    networks: [internal]

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks: [internal]

  web:
    build: .
    image: myapp:1.0
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }
    ports: ["8080:8080"]
    environment:
      DB_HOST: db
      REDIS_HOST: redis
    networks: [internal, public]
    deploy:
      resources:
        limits: { cpus: '1', memory: 512M }

volumes:
  db-data:

networks:
  internal:
  public:
```

```bash
# 操作
docker compose up -d
docker compose ps
docker compose logs -f web
docker compose exec db mysql -u root -p
docker compose down -v          # -v 删 volume（小心）
docker compose pull
docker compose restart web
docker compose config           # 校验 + 展开
```

### 9.2 进阶用法

```yaml
# .env 文件
DB_PASSWORD=changeme
TAG=1.0

# Profiles（按需启动）
services:
  metrics:
    image: prom/prometheus
    profiles: ["monitoring"]

# 启动监控套件
# docker compose --profile monitoring up -d

# Override
# docker-compose.override.yaml 自动叠加（开发用）
```

### 9.3 Compose vs Swarm vs K8s

| 工具 | 场景 | 集群 |
|:---|:---|:---|
| Compose | 单机 / 开发 / CI | 否 |
| Swarm | 简单集群（已淘汰） | 是（弱） |
| Kubernetes | 生产集群 ⭐ | 是 |

**结论**：单机/开发用 Compose，生产一律 K8s（见 07_K8s）。

## 十、安全基线

### 10.1 镜像安全

```
☐ 基础镜像选 distroless / alpine / scratch
☐ 不要 :latest，固定版本
☐ 多阶段构建剥离构建工具
☐ 扫描 (Trivy / Grype / Clair)
☐ 签名 (cosign)
☐ SBOM 生成
☐ 私有仓库 + 镜像保留策略
```

### 10.2 运行时安全

```bash
# 资源限制
--memory=512m --cpus=1 --pids-limit=200

# 只读 rootfs
--read-only --tmpfs /tmp

# 删能力
--cap-drop=ALL --cap-add=NET_BIND_SERVICE

# 非 root
--user 1000:1000

# 禁特权
# ❌ 不要 --privileged
# ❌ 不要 -v /:/host
# ❌ 不要 -v /var/run/docker.sock:/var/run/docker.sock (除非必要)

# AppArmor / Seccomp
--security-opt seccomp=default.json
--security-opt apparmor=docker-default

# rootless Docker
dockerd-rootless-setuptool.sh install
```

### 10.3 必扫工具

```bash
# Trivy（最主流）
trivy image nginx:1.27-alpine
trivy fs --severity HIGH,CRITICAL .

# 国产
# 阿里云镜像扫描 / 华为 SWR / 腾讯 TCR 都内置
```

## 十一、日志与监控

### 11.1 日志驱动

```
json-file ⭐ 默认（注意 rotate）
journald
syslog
fluentd        → ELK / Loki
local         BuildKit 内部
none
```

```json
// daemon.json 全局
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "100m", "max-file": "3" }
}
```

### 11.2 监控

```bash
# 实时
docker stats

# Prometheus
# 1. 开启 Docker metrics
{
  "metrics-addr": "0.0.0.0:9323",
  "experimental": true
}

# 2. cAdvisor (推荐)
docker run -d --name cadvisor \
  -v /:/rootfs:ro -v /var/run:/var/run:ro \
  -v /sys:/sys:ro -v /var/lib/docker/:/var/lib/docker:ro \
  -p 8080:8080 gcr.io/cadvisor/cadvisor

# 3. node_exporter + Prometheus + Grafana
```

## 十二、国产化镜像与替代

### 12.1 国产镜像加速

```
docker.m.daocloud.io       DaoCloud ⭐
docker.1panel.live         1Panel
hub.rat.dev                匿名（不稳）
mirror.ccs.tencentyun.com  腾讯（仅自家 ECS）
镜像加速器 (阿里云 cr 个人)  registry.cn-hangzhou.aliyuncs.com

注: docker hub 无加速会很慢/失败，必配
```

### 12.2 国产私有仓库

```
Harbor ⭐⭐⭐    VMware/中国团队开源（最主流）
阿里云 ACR     企业版含扫描
腾讯 TCR
华为 SWR
JFrog（信创版本）

特性: 多租户 / 复制 / 扫描 / 签名 / 国密 TLS
```

### 12.3 国产容器引擎

```
iSulad (华为)            轻量 / 嵌入式 / openEuler 默认
isuladd                 服务化
PouchContainer (阿里)    历史项目
鲲鹏 OCI 优化            ARM 适配
龙蜥 OS + containerd     主流国产容器栈

实际生产: 多数仍用 docker / containerd + 国产 OS
```

## 十三、入门 20 题

```
1.  容器 vs VM 区别？
2.  namespace 8 种各管什么？
3.  cgroup v1 vs v2 区别
4.  overlay2 工作原理（lower/upper/work/merged）
5.  dockerd / containerd / runc 关系
6.  OCI Image Spec / Runtime Spec / Distribution Spec
7.  Dockerfile 10 个最佳实践
8.  多阶段构建好处
9.  COPY vs ADD 区别
10. ENTRYPOINT vs CMD
11. RUN 合并的理由
12. 镜像层为什么不要装 build 工具
13. Compose v1 / v2 区别
14. depends_on healthy 怎么写
15. 镜像加速器配在哪个文件
16. docker volume 与 bind mount 区别
17. host 网络 vs bridge 网络
18. 怎么让容器不能 root
19. 一条命令查容器占多少内存
20. K8s 为什么弃用 dockershim
```

## 十四、典型坑（基础）

| 坑 | 建议 |
|:---|:---|
| **用 :latest tag** | 必固定版本 |
| **镜像几个 G** | 多阶段 + distroless |
| **跑 root** | USER 1000 + cap-drop |
| **/var/lib/docker 撑爆** | 单独分区 + log rotate + prune |
| **没设 ulimit nofile** | daemon.json 配 |
| **没用国产加速器** | pull 慢/失败 |
| **bind mount 权限错** | UID 对齐 (1000:1000) |
| **HEALTHCHECK 没写** | restart unless-stopped 没意义 |
| **日志写容器内** | 一律 stdout/stderr |
| **大文件用 ADD 解压** | COPY 后 RUN tar |
| **Compose v1 命令** | 用 `docker compose` 不是 `docker-compose` |
| **K8s 还用 dockershim** | 老 K8s 必须升级，新装 containerd/CRI-O |

## 十五、推荐栈

```
引擎:        Docker CE ⭐ / containerd / Podman
构建:        Buildx + BuildKit + 多阶段
仓库:        Harbor ⭐ / Aliyun ACR / Tencent TCR
扫描:        Trivy ⭐ / Grype
签名:        cosign + Notary
基础镜像:    distroless / alpine / wolfi / scratch
编排:        Compose (单机) / K8s (集群)
日志:        json-file + log-rotate / Loki / ELK
监控:        cAdvisor + Prometheus + Grafana
安全:        rootless / seccomp / AppArmor / cap-drop
国产化:      iSulad / 国产 OS / Harbor + 国密 TLS
```

## 十六、学习路径

```
入门（1-2 月）:
  1. 装 docker + 镜像加速器
  2. docker run / ps / logs / exec 熟练
  3. Dockerfile 多阶段 + distroless
  4. docker compose 单机栈
  5. 自建 Harbor + push/pull
  6. Trivy 扫一遍镜像
  7. 20 题过一遍

进阶（3-6 月）:
  8. BuildKit 多架构（amd64 + arm64）
  9. cgroup v2 + namespace 排障
  10. rootless docker
  11. 接 Prometheus + cAdvisor 监控
  12. K8s 集群中 containerd (见 07_K8s)
```

## 十七、参考资料

```
官方:
  docs.docker.com ⭐
  github.com/opencontainers
  containerd.io
  
经典:
  - 《Docker 实践》Ian Miell
  - 《Docker 容器与容器云》浙大 SEL
  - 《Kubernetes 权威指南》龚正
  
中文:
  - 阿里云 / 华为云 / 腾讯云 容器白皮书
  - InfoQ 容器专题
  - 极客时间《深入剖析 Kubernetes》(张磊)
  - 容器魔方公众号
  - openEuler iSulad SIG
```

> 📖 **核心判断**：Docker 基础 = **namespace+cgroup+overlay2 三件套 + dockerd/containerd/runc 三层架构 + OCI 三规范 + Dockerfile 多阶段 + Compose 单机 + 国产化镜像/仓库**。能在白板上画出"容器与 VM 区别"、能写出多阶段 distroless Dockerfile、能用 Compose 起 5 服务栈、能用 Harbor 自建仓库、能用 Trivy 扫漏洞，就具备容器入门。**生产容器 ≠ docker run**：生产一律 K8s + Harbor + Trivy + 多阶段镜像，从一开始就按这个标准练。
