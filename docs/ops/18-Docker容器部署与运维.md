# Docker 容器部署与运维

> Docker 怎么装？镜像怎么构建？网络/存储怎么配？生产环境怎么运维？本文覆盖 Docker 全栈实践。

---

## 一、Docker 架构

### 1.1 容器 vs 虚拟机

```
虚拟机 vs 容器:

  虚拟机 (KVM/ESXi):
  ┌───────┐ ┌───────┐ ┌───────┐
  │  VM1   │ │  VM2   │ │  VM3   │
  │ Bins   │ │ Bins   │ │ Bins   │
  │ Libs   │ │ Libs   │ │ Libs   │
  │ Guest  │ │ Guest  │ │ Guest  │
  │  OS    │ │  OS    │ │  OS    │  ← 每个 VM 完整 OS (GB 级)
  └───┬───┘ └───┬───┘ └───┬───┘
      │         │         │
  ┌───▼─────────▼─────────▼───┐
  │       Hypervisor           │
  └───────────┬───────────────┘
              │
  ┌───────────▼───────────────┐
  │        物理硬件             │
  └───────────────────────────┘
  启动: 分钟级    隔离: 强    资源开销: 大

  容器 (Docker):
  ┌───────┐ ┌───────┐ ┌───────┐
  │ Ctn1  │ │ Ctn2  │ │ Ctn3  │
  │ Bins  │ │ Bins  │ │ Bins  │
  │ Libs  │ │ Libs  │ │ Libs  │  ← 只打包应用+依赖 (MB 级)
  └───┬───┘ └───┬───┘ └───┬───┘
      │         │         │
  ┌───▼─────────▼─────────▼───┐
  │      Docker Engine         │
  └───────────┬───────────────┘
              │
  ┌───────────▼───────────────┐
  │     宿主机 OS (Linux)      │  ← 共享宿主机内核
  └───────────┬───────────────┘
              │
  ┌───────────▼───────────────┐
  │        物理硬件             │
  └───────────────────────────┘
  启动: 秒级/毫秒级    隔离: 中    资源开销: 小

  核心差异:
    VM:   硬件级虚拟化 (Hypervisor 模拟硬件)
    容器: OS 级虚拟化 (Namespace 隔离 + Cgroup 限制)

  容器隔离原理:
    Namespace: 隔离视图 (进程/网络/挂载点/IPC/用户/UTS)
      PID:     进程隔离 (容器内 PID 1, 看不到宿主机进程)
      NET:     网络隔离 (独立网卡/IP/端口/路由表)
      MNT:     挂载隔离 (独立文件系统视图)
      IPC:     IPC 隔离 (信号量/消息队列/共享内存)
      UTS:     主机名隔离 (hostname/domainname)
      USER:    用户隔离 (容器 root → 宿主机非 root)
      Cgroup:  Cgroup 视图隔离

    Cgroup:  限制资源 (CPU/内存/IO/设备)
      cpu:     CPU 配额/权重
      memory:  内存限制/OOM 控制
      blkio:   磁盘 IO 限制
      pids:    进程数限制
      devices: 设备访问控制
```

### 1.2 Docker 架构

```
┌─────────────────────────────────────────────────────────┐
│                    Docker 架构                          │
│                                                         │
│  ┌──────────────────────────┐                          │
│  │      Docker Client        │  docker CLI              │
│  │  docker build/run/push..  │  docker compose          │
│  └────────────┬─────────────┘                          │
│               │ REST API (/var/run/docker.sock)         │
│  ┌────────────▼─────────────┐                          │
│  │     Docker Daemon         │  dockerd                 │
│  │  (server side)            │                          │
│  │                           │                          │
│  │  ┌─────────────────────┐ │                          │
│  │  │   Image Manager     │ │  镜像管理                 │
│  │  │   (build/pull/push) │ │                          │
│  │  └─────────────────────┘ │                          │
│  │  ┌─────────────────────┐ │                          │
│  │  │   Container Manager │ │  容器管理                 │
│  │  │   (create/run/stop) │ │                          │
│  │  └─────────────────────┘ │                          │
│  │  ┌─────────────────────┐ │                          │
│  │  │   Network Manager   │ │  网络管理                 │
│  │  │   (bridge/overlay)  │ │                          │
│  │  └─────────────────────┘ │                          │
│  │  ┌─────────────────────┐ │                          │
│  │  │   Volume Manager    │ │  存储管理                 │
│  │  └─────────────────────┘ │                          │
│  └────────────┬─────────────┘                          │
│               │                                         │
│  ┌────────────▼─────────────┐                          │
│  │      containerd          │  高级运行时               │
│  │  (容器生命周期管理)        │                          │
│  │                           │                          │
│  │  ┌───────────────────┐   │                          │
│  │  │    runc            │   │  低级运行时 (OCI 标准)    │
│  │  │  (创建/运行容器)    │   │                          │
│  │  └───────────────────┘   │                          │
│  └────────────┬─────────────┘                          │
│               │                                         │
│  ┌────────────▼─────────────┐                          │
│  │      Linux Kernel         │                          │
│  │  Namespace + Cgroup       │                          │
│  └───────────────────────────┘                          │
│                                                         │
│  镜像存储:                                               │
│  ┌───────────────────────────────────────────────┐     │
│  │  /var/lib/docker/                              │     │
│  │  ├── overlay2/    镜像层 (写时复制)             │     │
│  │  ├── containers/  容器数据                      │     │
│  │  ├── volumes/     数据卷                        │     │
│  │  └── network/     网络配置                      │     │
│  └───────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘

  Docker 镜像 (Image):
    分层结构 (Layer), 每层只读
    Union FS (overlay2) 将多层合并为统一视图
    容器启动时, 在镜像顶部加一个可写层 (Copy-on-Write)

    镜像层示例:
    ┌──────────────────────┐
    │  可写层 (容器层)       │  ← docker run 后的修改
    ├──────────────────────┤
    │  Layer 5: COPY app/  │  ← COPY 指令
    ├──────────────────────┤
    │  Layer 4: RUN mvn    │  ← RUN 指令
    ├──────────────────────┤
    │  Layer 3: ENV/JAVA   │  ← ENV 指令
    ├──────────────────────┤
    │  Layer 2: apt install│  ← RUN 指令
    ├──────────────────────┤
    │  Layer 1: Ubuntu base│  ← FROM 指令
    └──────────────────────┘
```

---

## 二、安装部署

### 2.1 安装 Docker

```bash
# === Rocky / RHEL 9 ===
# 卸载旧版本
dnf remove -y docker docker-client docker-client-latest docker-common \
    docker-latest docker-latest-logrotate docker-logrotate docker-engine

# 添加 Docker 官方仓库
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 国内镜像源 (二选一)
dnf config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

# 安装
dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# === Ubuntu 22.04 / 24.04 ===
apt remove -y docker docker-engine docker.io containerd runc
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# === 启动 ===
systemctl enable --now docker

# 验证
docker version
docker info
docker run hello-world

# === 非 root 用户 ===
usermod -aG docker $USER
# 重新登录生效

# === 离线安装 ===
# 下载二进制包
wget https://download.docker.com/linux/static/stable/x86_64/docker-27.1.1.tgz
tar xzf docker-27.1.1.tgz
cp docker/* /usr/local/bin/

# systemd
cat > /etc/systemd/system/docker.service << 'EOF'
[Unit]
Description=Docker Application Container Engine
After=network-online.target

[Service]
Type=notify
ExecStart=/usr/local/bin/dockerd
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now docker
```

### 2.2 配置

```bash
# === /etc/docker/daemon.json ===
cat > /etc/docker/daemon.json << 'EOF'
{
  "data-root": "/data/docker",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "5"
  },
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.m.daocloud.io"
  ],
  "insecure-registries": [
    "192.168.1.10:5000"
  ],
  "live-restore": true,
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5,
  "default-ulimits": {
    "nofile": { "Hard": 65536, "Soft": 65536 },
    "nproc": { "Hard": 65536, "Soft": 65536 }
  },
  "storage-driver": "overlay2",
  "iptables": true,
  "ip-forward": true,
  "ip-masq": true,
  "userland-proxy": false,
  "exec-opts": ["native.cgroupdriver=systemd"],
  "features": {
    "buildkit": true
  }
}
EOF

systemctl restart docker

# 配置说明:
# data-root:            Docker 数据目录 (镜像/容器/卷)
# log-driver:           日志驱动 (json-file/Fluentd/syslog)
# log-opts:             日志大小限制 (防磁盘满)
# registry-mirrors:     镜像加速源
# insecure-registries:  私有 Registry (HTTP)
# live-restore:         重启 Docker 时不影响运行中的容器
# storage-driver:       存储驱动 (overlay2 最佳)
# cgroupdriver:         Cgroup 驱动 (systemd, K8s 要求)
# buildkit:             BuildKit 构建器 (更快, 更安全)

# === 镜像加速 (国内必备) ===
# daemon.json 中已配置 registry-mirrors
# 或单独配置
cat >> /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://mirror.ccs.tencentyun.com",
    "https://docker.nju.edu.cn"
  ]
}
EOF

# === 日志清理 ===
# 定期清理容器日志
cat > /etc/cron.daily/docker-log-cleanup << 'CRON'
#!/bin/bash
# 清理超过 100MB 的容器日志
find /var/lib/docker/containers -name "*-json.log" -size +100M -exec truncate -s 0 {} \;
CRON
chmod +x /etc/cron.daily/docker-log-cleanup

# === Docker 代理 (拉取外网镜像) ===
mkdir -p /etc/systemd/system/docker.service.d
cat > /etc/systemd/system/docker.service.d/proxy.conf << 'EOF'
[Service]
Environment="HTTP_PROXY=http://proxy.example.com:8080"
Environment="HTTPS_PROXY=http://proxy.example.com:8080"
Environment="NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,.example.com"
EOF
systemctl daemon-reload
systemctl restart docker
```

---

## 三、镜像管理

### 3.1 Dockerfile 最佳实践

```dockerfile
# === 多阶段构建 Java 应用 ===
# 阶段 1: 构建
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline                        # 先下载依赖 (利用缓存)
COPY src/ ./src/
RUN mvn clean package -DskipTests

# 阶段 2: 运行
FROM eclipse-temurin:21-jre-alpine
RUN apk add --no-cache curl tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1
USER 1000:1000
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]

# === 多阶段构建 Go 应用 ===
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o server -ldflags="-s -w" .

FROM alpine:3.20
RUN apk add --no-cache ca-certificates tzdata
COPY --from=builder /build/server /usr/local/bin/
ENTRYPOINT ["server"]

# === 多阶段构建 Python 应用 ===
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /install /usr/local
WORKDIR /app
COPY . .
RUN useradd -r appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]

# === 多阶段构建前端 ===
FROM node:20-alpine AS builder
WORKDIR /build
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 3.2 Dockerfile 指令速查

```dockerfile
# 基础镜像
FROM ubuntu:22.04

# 元数据
LABEL maintainer="ops@example.com"
LABEL version="1.0.0"
LABEL description="My App"

# 环境变量
ENV APP_HOME=/opt/app \
    JAVA_OPTS="-Xmx512m"

# 工作目录
WORKDIR $APP_HOME

# 复制文件 (COPY 推荐, ADD 有自动解压等功能)
COPY app.jar .
COPY config/ ./config/

# ADD (支持远程 URL 和自动解压 tar)
ADD https://example.com/file.tar.gz /tmp/
ADD file.tar.gz /opt/

# 运行命令
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 用户
RUN groupadd -r app && useradd -r -g app app
USER app

# 暴露端口 (仅声明, 不实际映射)
EXPOSE 8080 8443

# 数据卷 (仅声明, 不实际挂载)
VOLUME ["/data", "/logs"]

# 入口点 (ENTRYPOINT + CMD 组合)
ENTRYPOINT ["java", "-jar"]
CMD ["app.jar"]
# 实际执行: java -jar app.jar
# 可被 docker run 参数覆盖: docker run image -jar other.jar

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# ARG (构建时变量)
ARG VERSION=1.0.0
RUN echo "Building version $VERSION"

# SHELL (切换 shell, Windows 用)
SHELL ["/bin/bash", "-c"]

# STOPSIGNAL (优雅停止信号)
STOPSIGNAL SIGTERM
```

### 3.3 镜像构建与操作

```bash
# === 构建 ===
docker build -t my-app:1.0.0 .
docker build -t my-app:1.0.0 -f Dockerfile.prod .
docker build -t my-app:1.0.0 --build-arg VERSION=2.0.0 .
docker build -t my-app:1.0.0 --no-cache .                # 不使用缓存
docker build -t my-app:1.0.0 --target builder .          # 构建到指定阶段
docker build -t my-app:1.0.0 --platform linux/arm64 .    # 交叉编译

# 查看
docker images
docker image ls --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
docker image inspect my-app:1.0.0
docker image history my-app:1.0.0                        # 查看构建层

# === 操作 ===
docker tag my-app:1.0.0 my-app:latest
docker pull nginx:alpine
docker push registry.example.com/my-app:1.0.0
docker save -o my-app.tar my-app:1.0.0                   # 导出
docker load -i my-app.tar                                # 导入
docker rmi my-app:1.0.0
docker image prune -a                                    # 清理未使用镜像
docker image prune -a --filter "until=168h"              # 清理 7 天前

# === 构建最佳实践 ===
# 1. 使用 .dockerignore
cat > .dockerignore << 'EOF'
.git
node_modules
target
*.log
*.md
.env
Dockerfile
docker-compose*.yml
EOF

# 2. 合并 RUN 指令 (减少层数)
# ❌ 不好 (3 个层)
# RUN apt-get update
# RUN apt-get install -y curl
# RUN rm -rf /var/lib/apt/lists/*
# ✅ 好 (1 个层)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

# 3. 利用缓存 (变化频率从低到高排列)
# 先 COPY 不常变的, 后 COPY 常变的
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src/ ./src/
RUN mvn package

# 4. 使用小基础镜像
# alpine:    ~5MB (但可能有 musl libc 兼容问题)
# slim:      ~20-80MB (Debian 精简版, 推荐)
# distroless: ~20MB (无 shell, 更安全)
# scratch:   0MB (空镜像, 适合静态编译的 Go)
```

---

## 四、容器管理

### 4.1 运行容器

```bash
# === docker run ===
docker run [OPTIONS] IMAGE [COMMAND] [ARG...]

# 基本运行
docker run --name web -p 8080:80 nginx:alpine

# 后台运行
docker run -d --name web -p 8080:80 nginx:alpine

# 交互式
docker run -it --name shell ubuntu:22.04 /bin/bash

# 自动删除 (退出后自动删)
docker run --rm -it alpine sh

# === 常用选项 ===
docker run -d \
    --name my-app \
    -p 8080:8080 \
    -p 8443:8443 \
    -v /data/app/logs:/app/logs \
    -v /data/app/config:/app/config:ro \
    -e PROFILE=prod \
    -e JAVA_OPTS="-Xmx2g" \
    -e DB_PASSWORD \
    --env-file /etc/app/env.list \
    --network my-net \
    --network-alias app \
    --restart=unless-stopped \
    --memory=2g \
    --memory-swap=2g \
    --cpus=2 \
    --cpu-shares=512 \
    --pids-limit=200 \
    --ulimit nofile=65536:65536 \
    --health-cmd="curl -f http://localhost:8080/health" \
    --health-interval=30s \
    --health-timeout=5s \
    --health-retries=3 \
    --health-start-period=60s \
    --stop-timeout=30 \
    --user 1000:1000 \
    --read-only \
    --tmpfs /tmp \
    --cap-drop ALL \
    --cap-add NET_BIND_SERVICE \
    --security-opt no-new-privileges \
    my-app:1.0.0

# === 重启策略 ===
# no:             不自动重启 (默认)
# always:         总是重启 (宕机/重启 Docker)
# unless-stopped: 总是重启, 但手动 stop 后不再重启 (推荐)
# on-failure:     非零退出码时重启
docker run -d --restart=unless-stopped my-app
docker run -d --restart=on-failure:5 my-app                    # 最多重启 5 次

# === 环境变量文件 ===
cat > /etc/app/env.list << 'EOF'
PROFILE=prod
DB_HOST=192.168.1.10
DB_PORT=3306
DB_USER=appuser
DB_PASSWORD=secret
REDIS_HOST=192.168.1.10
EOF
```

### 4.2 容器生命周期

```bash
# === 生命周期管理 ===
docker create --name my-app my-app:1.0.0        # 创建 (不启动)
docker start my-app                               # 启动
docker stop my-app                                # 优雅停止 (SIGTERM → 10s 后 SIGKILL)
docker stop -t 30 my-app                          # 30 秒超时
docker kill my-app                                # 强制停止 (SIGKILL)
docker restart my-app                             # 重启
docker pause my-app                               # 暂停 (冻结进程)
docker unpause my-app                             # 恢复
docker rm my-app                                  # 删除 (停止状态)
docker rm -f my-app                               # 强制删除 (运行中)
docker rename my-app my-app-v2                    # 重命名

# === 查看状态 ===
docker ps                                          # 运行中
docker ps -a                                       # 所有 (含停止)
docker ps -q                                       # 只显示 ID
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# === 进入容器 ===
docker exec -it my-app /bin/bash
docker exec -it my-app sh                          # Alpine 无 bash
docker exec -it -u root my-app sh                  # 以 root 进入
docker exec my-app ls /app                         # 执行命令

# === 日志 ===
docker logs my-app
docker logs -f my-app                              # 实时跟踪
docker logs --tail 100 my-app                      # 最后 100 行
docker logs --since 30m my-app                     # 最近 30 分钟
docker logs -t my-app                              # 显示时间戳
docker logs --details my-app                       # 显示额外信息

# === 资源使用 ===
docker stats                                       # 所有容器实时
docker stats my-app                                # 指定容器
docker stats --no-stream                           # 只输出一次
docker top my-app                                  # 容器内进程

# === 查看详情 ===
docker inspect my-app
docker inspect -f '{{.NetworkSettings.IPAddress}}' my-app
docker inspect -f '{{json .State.Health}}' my-app
docker inspect -f '{{.Config.Env}}' my-app
docker port my-app                                 # 端口映射

# === 文件传输 ===
docker cp my-app:/app/logs/app.log /tmp/           # 容器 → 宿主机
docker cp /tmp/config.yml my-app:/app/config/      # 宿主机 → 容器

# === 批量操作 ===
docker stop $(docker ps -q)                        # 停止所有运行中容器
docker rm $(docker ps -aq)                         # 删除所有容器
docker rmi $(docker images -q -f "dangling=true")  # 删除悬空镜像
docker system prune -a --volumes                   # 清理所有未使用资源
```

---

## 五、网络

### 5.1 网络模式

```
Docker 网络模式:

  1. Bridge (默认, docker0)
  ┌──────────┐    ┌──────────┐
  │ 容器 A    │    │ 容器 B    │
  │ 172.17.0.2│    │ 172.17.0.3│
  └────┬─────┘    └────┬─────┘
       │               │
  ┌────▼───────────────▼─────┐
  │       docker0 (网桥)       │
  │       172.17.0.1          │
  └───────────┬──────────────┘
              │ NAT
  ┌───────────▼──────────────┐
  │       宿主机 eth0         │
  │       192.168.1.10       │
  └──────────────────────────┘
  - 容器有独立 IP, 通过 NAT 访问外网
  - 端口映射: -p 8080:80 (宿主机:容器)
  - 适合: 单机

  2. Host (共享宿主机网络)
  ┌──────────────────────────┐
  │       宿主机网络栈         │
  │       eth0: 192.168.1.10 │
  │  ┌────────┐ ┌────────┐  │
  │  │ 容器 A  │ │ 容器 B  │  │
  │  │        │ │        │  │
  │  └────────┘ └────────┘  │
  └──────────────────────────┘
  - 容器直接使用宿主机网络 (无隔离)
  - 性能最好 (无 NAT)
  - 端口冲突: 同一端口只能一个容器用
  - 适合: 对网络性能要求高的场景

  3. None (无网络)
  - 容器没有网络接口 (只有 lo)
  - 适合: 不需要网络的计算任务

  4. Container (共享其他容器网络)
  docker run --network=container:web nginx
  - 新容器共享 web 容器的网络栈
  - 适合: Sidecar 模式

  5. Overlay (跨主机)
  - VXLAN 隧道连接多台主机的容器
  - 需要: Docker Swarm 或 etcd/consul
  - 适合: Docker Swarm 集群

  6. Macvlan (MAC 地址虚拟化)
  - 容器拥有独立 MAC 地址, 直接出现在物理网络
  - 无 NAT, 性能好
  - 需要: 网卡混杂模式
  - 适合: 容器需要真实 IP 的场景
```

### 5.2 网络配置

```bash
# === 自定义 Bridge 网络 (推荐) ===
# 默认 docker0 不支持 DNS, 自定义 Bridge 支持容器名解析

# 创建网络
docker network create --driver bridge \
    --subnet 172.20.0.0/16 \
    --gateway 172.20.0.1 \
    -o com.docker.network.bridge.name=br0 \
    my-net

# 使用网络
docker run -d --name app --network my-net --network-alias app my-app:1.0.0
docker run -d --name db --network my-net --network-alias db mysql:8

# 容器间通过名称通信
docker exec app ping db                           # ✅ 可解析
docker exec app curl http://app:8080              # ✅ 可解析

# === Macvlan ===
# 创建 Macvlan 网络
docker network create -d macvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 \
    -o macvlan_mode=bridge \
    macvlan-net

# 运行容器 (容器获得真实 IP)
docker run -d --name web --network macvlan-net \
    --ip=192.168.1.50 nginx:alpine

# 注意: Macvlan 模式下, 宿主机无法与容器通信 (内核限制)
# 解决: 创建 Macvlan bridge

# === Overlay (Swarm) ===
docker network create -d overlay --attachable my-overlay
docker run -d --name app --network my-overlay my-app

# === 端口映射 ===
docker run -p 8080:80 nginx                        # 单端口
docker run -p 8080:80 -p 8443:443 nginx            # 多端口
docker run -p 127.0.0.1:8080:80 nginx              # 绑定指定 IP
docker run -p 8080:80/tcp -p 53:53/udp nginx       # TCP + UDP
docker run -P nginx                                # 随机端口映射

# === 网络管理 ===
docker network ls
docker network inspect my-net
docker network connect my-net container-name       # 运行中容器加入网络
docker network disconnect my-net container-name    # 移出网络
docker network rm my-net
docker network prune                               # 清理未使用网络

# === DNS ===
# 自定义 Bridge 网络内置 DNS (127.0.0.11)
# 容器名即主机名
docker exec app cat /etc/resolv.conf
# nameserver 127.0.0.11
```

---

## 六、存储

### 6.1 存储类型

```
Docker 存储类型:

  1. Volume (数据卷, 推荐)
  ┌──────────────────────────────────────────┐
  │  Docker 管理, 存于 /var/lib/docker/volumes/ │
  │                                          │
  │  宿主机: /var/lib/docker/volumes/myvol/   │
  │  容器内: /data                            │
  │                                          │
  │  特点:                                    │
  │  - Docker 管理, 独立于容器生命周期          │
  │  - 可在容器间共享                          │
  │  - 支持 remote driver (NFS/AWS EFS)       │
  │  - 可备份/迁移                            │
  └──────────────────────────────────────────┘

  2. Bind Mount (绑定挂载)
  ┌──────────────────────────────────────────┐
  │  直接挂载宿主机路径                        │
  │                                          │
  │  宿主机: /data/app/config                 │
  │  容器内: /app/config                      │
  │                                          │
  │  特点:                                    │
  │  - 完全依赖宿主机路径                      │
  │  - 性能好 (无中间层)                      │
  │  - 适合: 配置文件/开发代码挂载             │
  │  - 风险: 容器可修改宿主机文件              │
  └──────────────────────────────────────────┘

  3. tmpfs (内存文件系统)
  ┌──────────────────────────────────────────┐
  │  存于宿主机内存, 不写磁盘                   │
  │                                          │
  │  特点:                                    │
  │  - 性能极高                               │
  │  - 容器停止后数据消失                      │
  │  - 适合: 敏感数据/临时文件/缓存             │
  └──────────────────────────────────────────┘
```

### 6.2 存储操作

```bash
# === Volume (推荐) ===
# 创建
docker volume create mydata
docker volume create --driver local \
    --opt type=nfs \
    --opt o=addr=192.168.1.20,nfsvers=4 \
    --opt device=:/data/nfs \
    nfs-data

# 使用
docker run -d -v mydata:/app/data my-app
docker run -d --mount source=mydata,target=/app/data my-app
docker run -d --mount source=mydata,target=/app/data,readonly my-app

# 查看
docker volume ls
docker volume inspect mydata
docker volume rm mydata
docker volume prune

# === Bind Mount ===
docker run -d -v /data/app/config:/app/config my-app
docker run -d -v /data/app/config:/app/config:ro my-app     # 只读
docker run -d --mount type=bind,source=/data/config,target=/app/config my-app

# === tmpfs ===
docker run -d --tmpfs /tmp:rw,size=100m my-app
docker run -d --mount type=tmpfs,target=/tmp,tmpfs-size=100m my-app

# === Volume 备份与恢复 ===
# 备份
docker run --rm -v mydata:/data -v /backup:/backup alpine \
    tar czf /backup/mydata-$(date +%Y%m%d).tar.gz /data

# 恢复
docker run --rm -v mydata:/data -v /backup:/backup alpine \
    tar xzf /backup/mydata-20260711.tar.gz -C /

# === Volume 共享 ===
# 容器间共享 Volume
docker run -d --name app1 -v shared-data:/data my-app
docker run -d --name app2 -v shared-data:/data my-app

# 使用 --volumes-from (共享其他容器的 Volume)
docker run -d --name app --volumes-from app1 my-app
```

---

## 七、Docker Compose

### 7.1 编排多容器应用

```yaml
# docker-compose.yml
version: "3.9"

services:
  # === 应用 ===
  app:
    image: my-app:1.0.0
    build:
      context: .
      dockerfile: Dockerfile
      args:
        VERSION: 1.0.0
      target: production
    container_name: my-app
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - PROFILE=prod
      - DB_HOST=db
      - DB_PORT=3306
      - DB_USER=appuser
      - DB_PASSWORD=AppPass2026!
      - REDIS_HOST=redis
      - KAFKA_SERVERS=kafka:9092
    env_file:
      - .env
    volumes:
      - app-logs:/app/logs
      - ./config:/app/config:ro
    networks:
      - app-net
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
      kafka:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G
        reservations:
          cpus: "0.5"
          memory: 512M
    logging:
      driver: json-file
      options:
        max-size: "100m"
        max-file: "5"
    stop_grace_period: 30s

  # === MySQL ===
  db:
    image: mysql:8.0
    container_name: mysql
    restart: unless-stopped
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: RootPass2026!
      MYSQL_DATABASE: myapp
      MYSQL_USER: appuser
      MYSQL_PASSWORD: AppPass2026!
    volumes:
      - mysql-data:/var/lib/mysql
      - ./init-db:/docker-entrypoint-initdb.d:ro
      - ./mysql-conf.d:/etc/mysql/conf.d:ro
    networks:
      - app-net
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-pRootPass2026!"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --max-connections=200
      - --innodb-buffer-pool-size=1G
      - --slow-query-log=ON
      - --long-query-time=2

  # === Redis ===
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - app-net
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru --appendonly yes

  # === Kafka ===
  kafka:
    image: confluentinc/cp-kafka:7.6.0
    container_name: kafka
    restart: unless-stopped
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      CLUSTER_ID: "MkU3ODA0NTMyNT
      KAFKA_LOG_DIRS: /var/lib/kafka/data
    volumes:
      - kafka-data:/var/lib/kafka/data
    networks:
      - app-net

  # === Nginx ===
  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/certs:/etc/nginx/certs:ro
      - nginx-logs:/var/log/nginx
    networks:
      - app-net
    depends_on:
      - app

volumes:
  app-logs:
  mysql-data:
  redis-data:
  kafka-data:
  nginx-logs:

networks:
  app-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
```

### 7.2 Compose 命令

```bash
# === 启动/停止 ===
docker compose up -d                               # 启动 (后台)
docker compose up -d --build                       # 重新构建并启动
docker compose up -d --scale app=3                 # 扩容 app 到 3 个
docker compose down                                # 停止并删除
docker compose down -v                             # 停止并删除 (含 Volume)
docker compose stop                                # 停止 (不删除)
docker compose start                               # 启动
docker compose restart                             # 重启
docker compose pause                               # 暂停
docker compose unpause                             # 恢复

# === 查看 ===
docker compose ps                                  # 容器状态
docker compose logs -f app                         # 查看日志
docker compose top                                 # 进程
docker compose config                              # 查看渲染后的配置

# === 操作 ===
docker compose exec app sh                         # 进入容器
docker compose run --rm app npm test               # 运行一次性命令
docker compose build                               # 构建镜像
docker compose pull                                # 拉取镜像
docker compose push                                # 推送镜像

# === 多环境 ===
# docker-compose.yml          (基础配置)
# docker-compose.override.yml (默认覆盖, 自动加载)
# docker-compose.prod.yml     (生产环境)

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# docker-compose.prod.yml
cat > docker-compose.prod.yml << 'EOF'
version: "3.9"
services:
  app:
    image: registry.example.com/my-app:1.0.0
    build: !reset null                            # 生产不构建, 用镜像
    environment:
      - PROFILE=prod
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "4"
          memory: 4G
EOF
```

---

## 八、私有 Registry

### 8.1 Docker Registry

```bash
# === 官方 Registry (简单, 适合内网) ===
docker run -d --name registry \
    --restart always \
    -p 5000:5000 \
    -v /data/registry:/var/lib/registry \
    -e REGISTRY_PROXY_REMOTEURL=https://registry-1.docker.io \
    registry:2

# 配置 HTTP (内网, 无 TLS)
# /etc/docker/daemon.json:
# "insecure-registries": ["192.168.1.10:5000"]

# 使用
docker tag my-app:1.0.0 192.168.1.10:5000/my-app:1.0.0
docker push 192.168.1.10:5000/my-app:1.0.0
docker pull 192.168.1.10:5000/my-app:1.0.0

# 查看仓库
curl http://192.168.1.10:5000/v2/_catalog
curl http://192.168.1.10:5000/v2/my-app/tags/list
```

### 8.2 Harbor（企业级 Registry）

```yaml
# Harbor — 带 UI/认证/扫描/复制的企业级 Registry

# 1. 下载
wget https://github.com/goharbor/harbor/releases/download/v2.11.0/harbor-offline-installer-v2.11.0.tgz
tar xzf harbor-offline-installer-v2.11.0.tgz -C /opt/

# 2. 配置
cp /opt/harbor/harbor.yml.tmpl /opt/harbor/harbor.yml

# /opt/harbor/harbor.yml
cat > /opt/harbor/harbor.yml << 'EOF'
hostname: registry.example.com
http:
  port: 80
https:
  port: 443
  certificate: /opt/harbor/certs/server.crt
  private_key: /opt/harbor/certs/server.key
harbor_admin_password: HarborAdmin2026!
database:
  password: HarborDb2026!
  max_idle_conns: 50
  max_open_conns: 1000
data_volume: /data/harbor
trivy:
  ignore_unfixed: false
  skip_update: false
  offline_scan: false
  security_check: vuln
jobservice:
  max_job_workers: 10
notification:
  webhook_job_max_retry: 3
log:
  level: info
  local:
    rotate_count: 50
    rotate_size: 200M
    location: /var/log/harbor
_version: 2.11.0
proxy:
  http_proxy:
  https_proxy:
  no_proxy:
  components:
    - core
    - jobservice
    - trivy
upload_purging:
  enabled: true
  age: 168h
  interval: 24h
  dryrun: false
EOF

# 3. 生成自签名证书 (或用 Let's Encrypt)
mkdir -p /opt/harbor/certs
openssl req -newkey rsa:4096 -nodes -sha256 -keyout /opt/harbor/certs/server.key \
    -x509 -days 3650 -out /opt/harbor/certs/server.crt \
    -subj "/CN=registry.example.com"

# 4. 安装
cd /opt/harbor
./install.sh --with-trivy                          # 带 Trivy 漏洞扫描

# 5. 管理
docker compose -f /opt/harbor/docker-compose.yml up -d
docker compose -f /opt/harbor/docker-compose.yml down
docker compose -f /opt/harbor/docker-compose.yml restart

# 访问: https://registry.example.com
# 用户: admin / HarborAdmin2026!

# === Harbor 功能 ===
# 1. 项目管理 (公开/私有)
# 2. 用户/角色管理 (管理员/开发者/访客)
# 3. 镜像扫描 (Trivy 集成)
# 4. 镜像复制 (跨数据中心同步)
# 5. 垃圾回收 (清理未引用的 Blob)
# 6. 审计日志
# 7. Webhook (推送通知)
# 8. 漏洞扫描策略 (阻断严重漏洞镜像)

# 客户端配置 (信任 Harbor 证书)
cp /opt/harbor/certs/server.crt /etc/docker/certs.d/registry.example.com/ca.crt
systemctl restart docker

# 登录
docker login registry.example.com

# 推送
docker tag my-app:1.0.0 registry.example.com/prod/my-app:1.0.0
docker push registry.example.com/prod/my-app:1.0.0
```

---

## 九、安全

### 9.1 安全加固

```bash
# === 1. 非 Root 运行 ===
# Dockerfile
# RUN groupadd -r app && useradd -r -g app app
# USER app
# 或运行时指定
docker run --user 1000:1000 my-app

# === 2. 只读文件系统 ===
docker run --read-only --tmpfs /tmp my-app

# === 3. 限制能力 (Capabilities) ===
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE my-app

# 常见 Capabilities:
# NET_BIND_SERVICE  绑定 <1024 端口
# CHOWN             修改文件所有者
# DAC_OVERRIDE      忽略文件权限检查
# KILL              发送信号
# SETUID/SETGID     切换用户/组
# SYS_ADMIN         系统管理 (危险!)

# === 4. 禁止特权提升 ===
docker run --security-opt no-new-privileges my-app

# === 5. 限制资源 ===
docker run \
    --memory=1g \
    --memory-swap=1g \
    --cpus=1 \
    --pids-limit=100 \
    --ulimit nofile=1024:1024 \
    --ulimit nproc=50:50 \
    my-app

# === 6. 网络隔离 ===
# 不用 host 模式, 使用自定义 bridge
docker run --network my-net my-app

# === 7. 不使用 --privileged ===
# --privileged 等于给容器所有权限 (危险!)
# ❌ docker run --privileged my-app
# ✅ 只添加必要的 capabilities

# === 8. 使用 Secret 管理 ===
# 不要在镜像/环境变量中硬编码密码
# 使用 Docker Secret (Swarm) 或外部 Secret Manager

# Docker Secret
echo "MyDbPassword" | docker secret create db_password -
docker service create --name app --secret db_password my-app
# 容器内: /run/secrets/db_password
```

### 9.2 镜像扫描

```bash
# === Trivy (推荐, 开源) ===
# 安装
dnf install -y trivy

# 扫描镜像
trivy image my-app:1.0.0
trivy image --severity HIGH,CRITICAL my-app:1.0.0
trivy image --ignore-unfixed my-app:1.0.0
trivy image --exit-code 1 --severity CRITICAL my-app:1.0.0  # CI/CD 集成

# 扫描文件系统
trivy fs .
trivy fs --severity HIGH,CRITICAL .

# 扫描配置文件
trivy config .

# === Docker Scout (官方) ===
docker scout cves my-app:1.0.0
docker scout recommendations my-app:1.0.0

# === Grype ===
grype my-app:1.0.0
grype my-app:1.0.0 --only-fixed

# === CI/CD 集成 ===
# GitLab CI
# scan:
#   script:
#     - trivy image --exit-code 1 --severity CRITICAL my-app:$CI_COMMIT_TAG
```

### 9.3 Rootless Docker

```bash
# Rootless 模式 (非 root 用户运行 Docker Daemon)
# 更安全: 容器逃逸不会获得 root 权限

# 1. 安装依赖
dnf install -y slirp4netns fuse-overlayfs uidmap

# 2. 安装 rootless
curl -fsSL https://get.docker.com/rootless | sh

# 3. 配置环境变量
cat >> ~/.bashrc << 'EOF'
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
EOF
source ~/.bashrc

# 4. 启动
systemctl --user enable --now docker

# 5. 使用 (与普通 Docker 相同)
docker run -d -p 8080:80 nginx:alpine

# 注意: Rootless 模式限制
# - 不能用 --privileged
# - 不能绑定 <1024 端口 (除非 sysctl 配置)
# - 网络性能略低 (slirp4netns)
# - 部分 storage driver 不支持
```

---

## 十、监控

### 10.1 cAdvisor + Prometheus

```yaml
# docker-compose.monitoring.yml
version: "3.9"

services:
  # cAdvisor (容器资源监控)
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.49.1
    container_name: cadvisor
    restart: unless-stopped
    ports:
      - "8081:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=GrafanaAdmin2026!
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  prometheus-data:
  grafana-data:
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'docker'
    static_configs:
      - targets: ['host.docker.internal:9323']  # Docker daemon metrics
```

```bash
# Docker daemon 指标
# daemon.json 添加:
# "metrics-addr": "0.0.0.0:9323"

# Grafana 仪表盘:
# Docker:   ID 193 (cAdvisor)
# Docker:   ID 179 (Docker)
```

### 10.2 关键指标

```
cAdvisor 指标:
  container_cpu_usage_seconds_total    CPU 使用率
  container_memory_usage_bytes         内存使用
  container_network_receive_bytes      网络接收
  container_network_transmit_bytes     网络发送
  container_fs_reads_bytes_total       磁盘读
  container_fs_writes_bytes_total      磁盘写
  container_last_seen                  容器存活

Docker daemon 懈标:
  engine_daemon_container_actions_total    容器操作计数
  engine_daemon_container_states_containers  各状态容器数
  engine_daemon_events_total               事件计数
```

### 10.3 日志管理

```bash
# === 日志驱动 ===
# daemon.json 全局配置:
# "log-driver": "json-file"  (默认)
# "log-opts": {"max-size": "100m", "max-file": "5"}

# 容器级配置:
docker run --log-driver json-file \
    --log-opt max-size=10m \
    --log-opt max-file=3 \
    --log-opt labels=service,env \
    my-app

# Fluentd 日志驱动
docker run --log-driver fluentd \
    --log-opt fluentd-address=localhost:24224 \
    --log-opt tag=docker.myapp \
    my-app

# === Docker 日志聚合到 Loki ===
docker plugin install grafana/loki-docker-driver:latest --alias loki
docker run --log-driver loki \
    --log-opt loki-url=http://192.168.1.10:3100/loki/api/v1/push \
    --log-opt loki-batch-size=400 \
    my-app

# 或全局配置 daemon.json:
# "log-driver": "loki"
# "log-opts": {
#   "loki-url": "http://192.168.1.10:3100/loki/api/v1/push",
#   "loki-pipeline-stages": "[{\"json\":{\"expressions\":{\"level\":\"level\",\"service\":\"service\"}}}]"
# }
```

---

## 十一、性能优化

### 11.1 镜像优化

```dockerfile
# 1. 使用小基础镜像
FROM alpine:3.20          # ~5MB (注意 musl libc 兼容性)
FROM debian:bookworm-slim # ~28MB (推荐, 兼容性好)
FROM distroless/java21    # ~200MB (无 shell, 更安全)
FROM scratch              # 0MB (静态编译 Go)

# 2. 多阶段构建 (只保留运行所需)
FROM golang:1.22 AS builder
COPY . .
RUN CGO_ENABLED=0 go build -o app -ldflags="-s -w" .
FROM scratch
COPY --from=builder /build/app /
ENTRYPOINT ["/app"]

# 3. 合并 RUN 指令 (减少层数)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=7.88.1* \
    && rm -rf /var/lib/apt/lists/*

# 4. 使用 .dockerignore (减少构建上下文)
# .dockerignore:
# .git, node_modules, target, *.log, *.md

# 5. 合理利用缓存
# 先 COPY 依赖文件 → 下载依赖 → COPY 源码
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# 6. 使用 BuildKit (更快, 并行构建)
# docker build --buildkit .
# 或 daemon.json: "features": {"buildkit": true}
```

### 11.2 运行时优化

```bash
# === 资源限制 ===
# CPU 限制
docker run --cpus=2 my-app                     # 限制 2 核
docker run --cpu-shares=512 my-app             # CPU 权重 (默认 1024)
docker run --cpuset-cpus=0,1 my-app            # 绑定到 CPU 0,1

# 内存限制
docker run --memory=2g my-app                  # 限制 2GB
docker run --memory=2g --memory-swap=2g my-app # swap = memory (不允许 swap)
docker run --memory-reservation=1g my-app      # 软限制
docker run --oom-kill-disable my-app           # 禁止 OOM Kill (危险!)

# IO 限制
docker run \
    --device-read-bps /dev/sda:10mb \
    --device-write-bps /dev/sda:10mb \
    --device-read-iops /dev/sda:1000 \
    --device-write-iops /dev/sda:1000 \
    my-app

# 进程数限制
docker run --pids-limit=200 my-app

# === 网络优化 ===
# 使用 host 模式 (最高性能, 无 NAT)
docker run --network host my-app

# 调整 DNS
docker run --dns 223.5.5.5 --dns-search example.com my-app

# === 存储优化 ===
# 使用 Volume (比 bind mount 性能好)
docker run -v data:/data my-app

# tmpfs (内存, 最高性能)
docker run --tmpfs /cache:size=100m my-app

# === 日志优化 ===
# 限制日志大小 (防磁盘满)
docker run --log-opt max-size=10m --log-opt max-file=3 my-app
```

### 11.3 系统优化

```bash
# === 内核参数 ===
cat >> /etc/sysctl.d/99-docker.conf << 'EOF'
# 网络转发
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1

# 文件描述符
fs.file-max = 2097152
fs.nr_open = 2097152

# 网络连接
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15

# 内存
vm.swappiness = 10
vm.overcommit_memory = 1
EOF
sysctl -p /etc/sysctl.d/99-docker.conf

# === 磁盘 IO ===
# 使用 overlay2 (最佳)
# daemon.json: "storage-driver": "overlay2"

# 定期清理
docker system prune -a --volumes --filter "until=168h"

# 清理构建缓存
docker builder prune -a

# === ulimit ===
# daemon.json
# "default-ulimits": {
#   "nofile": {"Hard": 65536, "Soft": 65536},
#   "nproc": {"Hard": 65536, "Soft": 65536}
# }
```

---

## 十二、故障排查

### 12.1 常见问题

| 问题 | 原因 | 解决 |
|:---|:---|:---|
| 容器启动立即退出 | CMD/ENTRYPOINT 错误 | 查看日志 `docker logs` |
| 容器 OOM Killed | 内存不足 | 增加 `--memory` / 排查内存泄漏 |
| 端口被占用 | 宿主机端口冲突 | 换端口 / 停止占用进程 |
| 无法拉取镜像 | 网络/DNS/源 | 配置镜像加速 / 代理 |
| 磁盘满 | 镜像/日志/Volume 过多 | `docker system prune` |
| 容器网络不通 | 网桥/iptables/防火墙 | 检查网络/iptables/防火墙 |
| 权限拒绝 | SELinux/AppArmor | `chcon` 或 `--security-opt` |
| 容器卡 D 状态 | IO 瓶颈/内核 Bug | 检查磁盘/升级内核 |

### 12.2 诊断命令

```bash
# === 查看日志 ===
docker logs my-app
docker logs -f --tail 100 my-app

# === 查看事件 ===
docker events --filter container=my-app

# === 查看资源 ===
docker stats my-app
docker top my-app

# === 查看详情 ===
docker inspect my-app

# === 查看文件系统 ===
docker diff my-app                                # 查看文件变更

# === 查看健康状态 ===
docker inspect -f '{{json .State.Health}}' my-app | python3 -m json.tool

# === 网络诊断 ===
# 进入容器排查
docker exec -it my-app sh
# 容器内:
ping google.com
curl -v http://db:3306
nslookup db
cat /etc/resolv.conf
ip addr
ss -tlnp

# 查看网桥
brctl show
iptables -t nat -L -n

# === Docker daemon 诊断 ===
docker info
docker info --format '{{json .}}' | python3 -m json.tool
docker system df                                  # 磁盘使用
docker system df -v                               # 详细

# === 查看 Docker 日志 ===
journalctl -u docker --since "1 hour ago"
journalctl -u docker -f

# === 查看容器退出码 ===
docker inspect -f '{{.State.ExitCode}}' my-app
# 0:   正常退出
# 1:   应用错误
# 125: Docker 错误
# 126: 命令不可执行
# 127: 命令未找到
# 137: SIGKILL (通常是 OOM)
# 139: SIGSEGV (段错误)
# 143: SIGTERM (正常停止)

# === 清理僵尸容器 ===
docker rm $(docker ps -aq --filter status=exited)
docker rm $(docker ps -aq --filter status=dead)

# === 查看 containerd ===
ctr containers list
ctr tasks list
crictl ps                                         # K8s 场景
```

### 12.3 磁盘空间清理

```bash
# === 查看磁盘占用 ===
docker system df
docker system df -v

# === 清理 ===
# 删除停止的容器
docker container prune

# 删除悬空镜像 (无标签)
docker image prune

# 删除所有未使用镜像
docker image prune -a

# 删除未使用 Volume
docker volume prune

# 删除未使用网络
docker network prune

# 一键清理
docker system prune                                # 不含 Volume
docker system prune -a                             # 含所有未使用镜像
docker system prune -a --volumes                   # 含 Volume

# 按时间过滤
docker image prune -a --filter "until=168h"        # 7 天前

# === 清理构建缓存 ===
docker builder prune
docker builder prune -a

# === 清理大容器日志 ===
# 查看日志大小
find /var/lib/docker/containers -name "*-json.log" -exec ls -lh {} \;
# 清理
truncate -s 0 /var/lib/docker/containers/*/*-json.log

# === 迁移 Docker 数据目录 ===
# 1. 停止 Docker
systemctl stop docker

# 2. 迁移数据
rsync -aP /var/lib/docker/ /data/docker/

# 3. 修改配置
# daemon.json: "data-root": "/data/docker"

# 4. 启动
systemctl start docker

# 5. 验证
docker info | grep "Docker Root Dir"
```

---

## 十三、Docker Swarm

```bash
# === Swarm 集群 (轻量级编排) ===
# 适合: 小规模集群, 不需要 K8s 的场景

# 1. 初始化 Manager
docker swarm init --advertise-addr 192.168.1.10

# 2. 获取 Worker 加入命令
docker swarm join-token worker
# docker swarm join --token SWMTKN-xxx 192.168.1.10:2377

# 3. 在 Worker 节点执行
docker swarm join --token SWMTKN-xxx 192.168.1.10:2377

# 4. 查看节点
docker node ls
docker node inspect <node-name>

# 5. 部署服务
docker service create --name web -p 80:80 --replicas 3 nginx:alpine

# 6. 管理
docker service ls
docker service ps web
docker service scale web=5
docker service update --image nginx:latest web
docker service rm web

# 7. Stack (类似 Compose)
docker stack deploy -c docker-compose.yml myapp
docker stack ls
docker stack ps myapp
docker stack rm myapp

# 8. Overlay 网络 (跨主机)
docker network create -d overlay my-overlay
docker service create --name app --network my-overlay my-app

# 9. 滚动更新
docker service update \
    --update-parallelism 2 \
    --update-delay 10s \
    --update-failure-action rollback \
    --image my-app:2.0.0 app

# 10. 节点维护
docker node update --availability drain <node>     # 不调度新任务
docker node update --availability active <node>    # 恢复
docker node rm <node>                              # 移除
```

---

## 十四、对比总结

### 14.1 容器运行时对比

| 维度 | Docker Engine | containerd | CRI-O | Podman |
|:---|:---|:---|:---|:---|
| 定位 | 完整容器平台 | 运行时 | K8s 运行时 | 无守护进程容器 |
| 守护进程 | dockerd | containerd | CRI-O | 无 (fork-exec) |
| Rootless | 支持有限 | 支持 | 支持 | ⭐ 默认 |
| Compose | ⭐ 原生 | 不支持 | 不支持 | podman-compose |
| Swarm | ⭐ 支持 | 不支持 | 不支持 | 不支持 |
| K8s 兼容 | 通过 containerd | ⭐ CRI 原生 | ⭐ CRI 原生 | 通过 CRI-O |
| 生态 | ⭐ 最丰富 | K8s 内置 | K8s 专用 | Docker 兼容 |
| 资源占用 | 中 | ⭐ 低 | ⭐ 低 | ⭐ 低 |
| 适用场景 | 开发/单机 | K8s 运行时 | K8s 运行时 | 开发/无 root |

### 14.2 Docker vs K8s

| 维度 | Docker + Compose | Docker Swarm | Kubernetes |
|:---|:---|:---|:---|
| 复杂度 | ⭐ 低 | ⭐ 低 | ⭐ 高 |
| 单机 | ⭐ 最佳 | 可用 | 过重 |
| 多机 | ❌ | 可用 | ⭐ 最佳 |
| 自动扩缩容 | ❌ | 手动 | ⭐ HPA/VPA |
| 服务发现 | DNS | DNS | ⭐ CoreDNS |
| 负载均衡 | ❌ | 内置 | ⭐ Ingress |
| 滚动更新 | 手动 | ⭐ 内置 | ⭐ 内置 |
| 配置管理 | env/volume | secret | ⭐ ConfigMap/Secret |
| 存储 | Volume | Volume | ⭐ PV/PVC/CSI |
| 网络 | bridge/overlay | overlay | ⭐ CNI |
| 适用 | 开发/单机 | 小集群 | 生产集群 |

### 14.3 最佳实践检查清单

```
镜像构建:
  □ 多阶段构建, 减小镜像体积
  □ 使用 .dockerignore
  □ 合并 RUN 指令, 清理缓存
  □ 使用固定版本 tag (不用 latest)
  □ 非 root 用户运行
  □ 添加 HEALTHCHECK
  □ 镜像扫描 (Trivy) 通过

容器运行:
  □ 资源限制 (--memory/--cpus)
  □ 日志限制 (max-size/max-file)
  □ 重启策略 (unless-stopped)
  □ 健康检查
  □ 非 root 用户
  □ 只读文件系统 (--read-only)
  □ 最小权限 (--cap-drop ALL)
  □ 禁止特权提升 (no-new-privileges)

生产环境:
  □ 私有 Registry (Harbor)
  □ 镜像扫描
  □ 监控 (cAdvisor + Prometheus)
  □ 日志收集 (Loki/ELK)
  □ 定期清理 (docker system prune)
  □ 数据备份 (Volume 备份)
  □ 网络隔离 (自定义 bridge)
  □ 配置/密钥不硬编码
```

---

## 十五、配置文件速查表

| 文件/目录 | 用途 |
|:---|:---|
| `/etc/docker/daemon.json` | Docker Daemon 配置 |
| `/etc/systemd/system/docker.service.d/` | systemd 覆盖配置 (代理等) |
| `/var/lib/docker/` | Docker 数据目录 (镜像/容器/卷) |
| `/var/lib/docker/containers/` | 容器数据 (日志/配置) |
| `/var/lib/docker/volumes/` | Volume 数据 |
| `/var/lib/docker/overlay2/` | 镜像层存储 |
| `/var/run/docker.sock` | Docker Socket (API) |
| `~/.docker/config.json` | 客户端配置 (认证) |
| `Dockerfile` | 镜像构建文件 |
| `.dockerignore` | 构建上下文排除 |
| `docker-compose.yml` | 多容器编排 |
| `/etc/docker/certs.d/` | Registry TLS 证书 |
| Harbor `harbor.yml` | Harbor 配置 |

---

*最后更新: 2026-07-11*
