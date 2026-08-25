# Docker 镜像构建优化（多阶段构建）

> 镜像怎么越建越大？构建为什么越来越慢？多阶段构建如何让镜像从 GB 级瘦身到几十 MB？本文从构建原理出发，覆盖多阶段构建、BuildKit 缓存、构建上下文、基础镜像选型、CI/CD 集成与故障排查的全栈实践。

---

## 一、镜像构建的痛点与优化总览

### 1.1 典型痛点

生产环境中"能跑"和"好维护"之间隔着一条巨大的沟。镜像构建的常见问题：

| 痛点 | 典型表现 | 后果 |
|:---|:---|:---|
| 镜像体积大 | Java 应用 1.5GB、Python 应用 800MB | 拉取慢、存储贵、启动慢、攻击面大 |
| 构建慢 | 每次 CI 全量重装依赖 5-10 分钟 | CI 排队、发布节奏被拖垮 |
| 依赖泄漏 | 构建工具链混入运行镜像 | 生产镜像里有 gcc、npm、Maven 仓库 |
| 缓存失效 | 改一行代码所有层全部重建 | 构建时间与代码改动成正比 |
| 层数爆炸 | 一条命令一层，50+ 层 | 镜像元数据膨胀、Docker Hub 250MB 限制 |
| 安全隐患 | 以 root 运行、含完整 SDK | CVE 面大、被入侵后提权容易 |
| 上下文臃肿 | 整个 git 仓库打进上下文 | 构建机网络打满、无缓存命中 |

### 1.2 优化手段全景

```text
镜像构建优化手段分层:

┌─────────────────────────────────────────────────────┐
│  一、结构层   多阶段构建 (Multi-stage Build)         │
│               构建阶段与运行阶段分离                 │
│               COPY --from 只拷贝产物                │
├─────────────────────────────────────────────────────┤
│  二、缓存层   BuildKit 缓存                          │
│               依赖层前置 + --mount=type=cache        │
│               远程缓存 (registry/gha)               │
├─────────────────────────────────────────────────────┤
│  三、输入层   .dockerignore + 构建上下文瘦身          │
│               只传构建所需文件                       │
├─────────────────────────────────────────────────────┤
│  四、基座层   基础镜像选型                          │
│               scratch / distroless / alpine          │
├─────────────────────────────────────────────────────┤
│  五、安全层   非 root + 精简层 + 扫描签名            │
└─────────────────────────────────────────────────────┘
```

### 1.3 优化效果参考

| 指标 | 优化前 | 优化后 | 手段 |
|:---|:---|:---|:---|
| Go 应用镜像 | 800MB (golang:1.22) | 7-15MB (scratch) | 多阶段 + 静态编译 |
| Java 应用镜像 | 1.5GB (maven:3.9 + jdk) | 150-250MB (eclipse-temurin JRE) | 多阶段 + JRE 精简 |
| Node 应用镜像 | 1.2GB (node:20 全量) | 100-150MB (node:20-alpine) | 多阶段 + 生产依赖 |
| Python 应用镜像 | 900MB (python:3.12) | 150-200MB (python:3.12-slim) | 多阶段 + venv |
| 构建时间 | 5-10 分钟 (全量) | 30-60 秒 (缓存命中) | BuildKit 缓存 |
| 层数 | 30-60 层 | 10-20 层 | 合并 RUN + 多阶段 |

> **核心心法**：构建工具链只需要在构建阶段存在，运行阶段只需要产物和运行时。多阶段构建就是把这句大白话变成 Dockerfile 语法。

---

## 二、多阶段构建原理

### 2.1 单阶段构建的问题

先看一个典型的单阶段 Java 镜像（这是绝大多数团队的现状）：

```dockerfile
# 单阶段: 构建工具 + 运行时 混在一起
FROM maven:3.9-eclipse-temurin-17

WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline          # 预拉依赖
COPY src ./src
RUN mvn package -DskipTests            # 编译打包

EXPOSE 8080
CMD ["java", "-jar", "target/app.jar"]
```

问题一目了然：

| 问题 | 说明 |
|:---|:---|
| 镜像巨大 | maven:3.9-eclipse-temurin-17 基础镜像就 ~800MB，还包含完整 JDK + Maven |
| 攻击面大 | gcc、Maven 插件、文档、测试框架全在运行镜像里 |
| 无意义层 | 编译产物、中间文件、.m2 仓库全部保留 |
| 不专业 | 生产镜像里躺着完整的构建工具链 |

### 2.2 多阶段构建原理

多阶段构建（Multi-stage Build，Docker 17.05+ 引入）允许一个 Dockerfile 里有多个 `FROM`。**只有最后一个阶段的产物会进入最终镜像**，前面所有阶段只作为"构建车间"存在。

```text
多阶段构建原理:

┌─ 阶段 1: builder (构建车间) ──────────────────────┐
│  FROM golang:1.22                                │
│  COPY . .                                        │
│  RUN CGO_ENABLED=0 go build -o /out/app          │
│  产物: /out/app  (二进制)                        │
└──────────────────────┬───────────────────────────┘
                       │  COPY --from=builder
                       ▼
┌─ 阶段 2: 运行阶段 (成品车间) ─────────────────────┐
│  FROM scratch                                    │
│  COPY --from=builder /out/app /app               │
│  ENTRYPOINT ["/app"]                             │
│  产物: 最终镜像 (仅 15MB)                        │
└──────────────────────────────────────────────────┘

关键点:
  1. 阶段 1 的中间层在构建完成后被丢弃
  2. 只有阶段 2 的层会被 push 到仓库
  3. 阶段间通过 COPY --from=<阶段名> 传递产物
  4. 未使用的阶段构建时自动跳过 (BuildKit)
```

### 2.3 核心语法

**阶段命名**：`FROM <镜像> AS <阶段名>`，阶段名用于 `COPY --from` 引用。

```dockerfile
FROM golang:1.22 AS builder        # 命名阶段
FROM scratch                       # 匿名阶段 (默认叫 0, 1, 2...)
```

**跨阶段拷贝**：从指定阶段拷贝文件或目录。

```dockerfile
COPY --from=builder /out/app /app
COPY --from=golang:1.22 /usr/local/go /usr/local/go   # 甚至可以从外部镜像拷
```

**指定目标阶段**：构建时用 `--target` 只构建到某个阶段（常用于 dev/prod 分离）。

```bash
docker build --target builder -t myapp:build .   # 只构建构建阶段 (调试用)
docker build --target prod -t myapp:1.0.0 .      # 构建最终阶段
```

### 2.4 多阶段最小示例（Go）

```dockerfile
# ============ 阶段 1: 构建 ============
FROM golang:1.22-alpine AS builder

WORKDIR /src
# 先拷 go.mod/go.sum 预拉依赖 (缓存友好)
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/app .

# ============ 阶段 2: 运行 ============
FROM scratch

COPY --from=builder /out/app /app
# 时区文件 (scratch 里什么都没有)
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

EXPOSE 8080
USER 65532:65532
ENTRYPOINT ["/app"]
```

```bash
docker build -t myapp:multi .
docker images | grep myapp        # 看到体积从 800MB → 15MB
```

| 镜像 | 体积 | 层数 |
|:---|:---|:---|
| 单阶段 (golang:1.22) | ~800MB | 12 |
| 多阶段 (scratch) | ~15MB | 4 |
| 节省 | **98%** | 8 层 |

### 2.5 为什么多阶段能"白拿"优化

```text
层是镜像的增量单元:
  单阶段:  [OS 层][工具链层][依赖层][源码层][编译层]  ← 全部保留
  多阶段:  [OS 层][工具链层][依赖层][源码层][编译层]  ← 构建后丢弃
           [运行层: 仅产物 + 运行时]                  ← 只保留这个
```

BuildKit 构建器还会**并行执行互不依赖的阶段**，并且**跳过没有被最终阶段引用的阶段**，构建速度进一步提升。

---

## 三、四语言实战案例

### 3.1 Go：静态编译 + scratch/distroless

Go 是最适合多阶段构建的语言——静态编译后零依赖，理论上可以跑在 `scratch`（空镜像）上。

**优化前**（典型错误做法）：

```dockerfile
FROM golang:1.22
WORKDIR /app
COPY . .
RUN go build -o app .
CMD ["./app"]
```

**优化后**：

```dockerfile
# ===== 构建阶段 =====
FROM golang:1.22-alpine AS builder

RUN apk add --no-cache ca-certificates tzdata
WORKDIR /src

# 依赖缓存友好: 先拷模块文件
COPY go.mod go.sum ./
RUN go mod download

COPY . .

# -trimpath 去掉构建路径信息
# -ldflags="-s -w" 去掉符号表和调试信息 (体积再减 30%)
# CGO_ENABLED=0 纯静态编译, 不依赖 glibc
RUN CGO_ENABLED=0 GOOS=linux go build \
    -trimpath \
    -ldflags="-s -w" \
    -o /out/app .

# ===== 运行阶段: scratch (无 shell 无包管理器, 最安全) =====
FROM scratch

# 时区 + CA 证书 (scratch 是空的, 必须自带)
COPY --from=builder /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /out/app /app

# 非 root: scratch 里 UID 直接用数字
USER 65532:65532

EXPOSE 8080
ENTRYPOINT ["/app"]
```

**选择 scratch 还是 distroless**：

| 需求 | 选型 | 说明 |
|:---|:---|:---|
| 纯静态二进制、零依赖 | `scratch` | 最小 (~0MB + 产物) |
| 需要 CA 证书/时区但不要 shell | `gcr.io/distroless/static` | 自带证书, 无 shell 无包管理器 |
| 需要调试 (exec 进容器) | `gcr.io/distroless/static-debian12:nonroot` | 带 debug 变体 |
| 需要 glibc 动态链接 | `gcr.io/distroless/base` | CGO 程序可用 |

> **注意**：如果 Go 程序用了 `net` 包做 DNS 解析（生产几乎必用），`scratch` 必须自带 CA 证书，否则 HTTPS 请求会报 `x509: certificate signed by unknown authority`。

**体积对比**：

```bash
$ docker images | grep goapp
goapp:single-stage    808MB
goapp:multi-scratch   15.2MB
goapp:multi-distroless 18.6MB
```

### 3.2 Java：Maven 多阶段 + JRE 精简 + 分层

Java 镜像大的根源：完整 JDK（含编译器、调试工具、JVM 源码）不需要出现在运行镜像里。多阶段把 Maven 构建放在 JDK 阶段，运行阶段只用 JRE。

**优化后**：

```dockerfile
# ===== 构建阶段: JDK + Maven =====
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build
# 先拷 pom.xml 预拉依赖 (依赖不变则缓存命中)
COPY pom.xml .
RUN mvn dependency:go-offline

COPY src ./src
RUN mvn package -DskipTests -Dmaven.test.skip=true

# ===== 运行阶段: 只带 JRE =====
FROM eclipse-temurin:17-jre-alpine

# 非 root 用户 (alpine 自带, 无需额外创建)
RUN addgroup -S app && adduser -S app -G app

WORKDIR /app
# 只拷贝构建产物, 不带源码不带 .m2
COPY --from=builder /build/target/app.jar app.jar

USER app
EXPOSE 8080
# Java 17: 显式指定时区 + 限制 JVM 内存
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-Duser.timezone=Asia/Shanghai", "-jar", "app.jar"]
```

**JDK vs JRE 体积**：

| 基础镜像 | 体积 | 适用 |
|:---|:---|:---|
| eclipse-temurin:17-jdk | ~350MB | 构建阶段 |
| eclipse-temurin:17-jre | ~190MB | 运行阶段 (官方瘦身 45%) |
| eclipse-temurin:17-jre-alpine | ~120MB | 运行阶段 (musl, 再瘦 35%) |

**Spring Boot 分层镜像（进阶）**：Spring Boot 2.3+ 的 jar 是分层结构，可以只拷贝需要的层，让依赖层缓存命中：

```dockerfile
FROM eclipse-temurin:17-jre-alpine AS builder
WORKDIR /builder
COPY target/app.jar app.jar
# 解包 Spring Boot fat jar 为分层目录
RUN java -Djarmode=layertools -jar app.jar extract

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
# 依赖层在最前 → 依赖不变时后续构建全部命中缓存
COPY --from=builder /builder/dependencies/ ./
COPY --from=builder /builder/spring-boot-loader/ ./
COPY --from=builder /builder/snapshot-dependencies/ ./
COPY --from=builder /builder/application/ ./
ENTRYPOINT ["java", "-jar", "app.jar"]
```

> **分层收益**：改一行业务代码，只有 `application/` 层重建，依赖层全部命中缓存，构建从 3 分钟降到 20 秒。

### 3.3 Node.js：npm ci + 生产依赖 + Alpine

Node 镜像常见的两个坑：把 `node_modules` 整个拷进镜像、devDependencies 混入生产。

**优化后**：

```dockerfile
# ===== 构建阶段 =====
FROM node:20-alpine AS builder

WORKDIR /app
# 利用 BuildKit 缓存挂载: npm 缓存不落层
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production

COPY . .
# 生产构建 (Next.js/Vue/React 等需要)
RUN npm run build

# ===== 运行阶段 =====
FROM node:20-alpine

WORKDIR /app
ENV NODE_ENV=production

# 只拷贝生产依赖 + 构建产物
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next        # 以 Next.js 为例
COPY --from=builder /app/package.json ./package.json

# 非 root (node 官方镜像内置 node 用户)
USER node

EXPOSE 3000
CMD ["npm", "start"]
```

**npm 依赖缓存的两条路线**：

| 方式 | 原理 | 适用 |
|:---|:---|:---|
| `COPY package*.json` + `npm ci` 前置 | 依赖层在源码层之前, 依赖不变则缓存命中 | Docker 默认构建器 |
| `RUN --mount=type=cache,target=/root/.npm` | npm 全局缓存挂载, 不写入镜像层 | BuildKit |

**npm ci vs npm install**：

| 对比项 | npm ci | npm install |
|:---|:---|:---|
| 依赖锁定 | 严格按 package-lock.json | 可能更新 |
| 速度 | 快 (跳过解析) | 慢 |
| node_modules 已有 | 强制删除重装 | 复用 |
| 生产推荐 | ✅ | ❌ |

### 3.4 Python：多阶段 venv + slim

Python 镜像优化的核心：**不要把全局 site-packages 和构建依赖带进运行镜像**。用 venv 隔离 + 多阶段只拷 venv。

**优化后**：

```dockerfile
# ===== 构建阶段 =====
FROM python:3.12-slim AS builder

# 构建依赖 (编译 wheel 用, 不进运行镜像)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# 创建独立 venv 并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# ===== 运行阶段 =====
FROM python:3.12-slim

# 运行依赖 (如果需要) — 尽量少
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 只拷 venv (包含解释器链接 + 依赖)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . .

# 非 root
RUN useradd -m appuser
USER appuser

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

**体积对比**：

| 方式 | 镜像体积 | 说明 |
|:---|:---|:---|
| python:3.12 全量 + pip install 全装 | ~900MB | 含 gcc、文档、缓存 |
| python:3.12-slim 单阶段 | ~500MB | 依赖层多, 含构建工具 |
| 多阶段 venv (slim) | ~180MB | 只带 venv 产物 |

> **注意**：`COPY --from=builder /opt/venv /opt/venv` 拷贝后 venv 里的 `python` 是软链接，指向 `python3.12`，所以 venv 目录必须整体拷（含 bin/、lib/、pyvenv.cfg），不能只拷 site-packages。

### 3.5 四语言优化对照

| 语言 | 构建阶段基础镜像 | 运行阶段基础镜像 | 优化前 | 优化后 | 关键技巧 |
|:---|:---|:---|:---|:---|:---|
| Go | golang:1.22-alpine | scratch / distroless | ~800MB | 10-20MB | CGO_ENABLED=0 + -ldflags |
| Java | maven:3.9-eclipse-temurin | eclipse-temurin:17-jre-alpine | ~1.5GB | 120-200MB | 只拷 jar + layertools |
| Node | node:20-alpine | node:20-alpine | ~1.2GB | 100-150MB | npm ci + 生产依赖 |
| Python | python:3.12-slim | python:3.12-slim | ~900MB | 150-200MB | venv 整体拷贝 |

---

## 四、构建缓存优化（BuildKit）

### 4.1 缓存机制：层是缓存的最小单位

```text
Docker 缓存判定 (经典构建器):

  指令是否命中缓存?
  ├─ 基础镜像相同?
  ├─ 指令文本相同?
  ├─ 上下文文件内容未变 (COPY/ADD)?
  └─ 父层缓存命中?
      全部 YES → 复用缓存层 (不重新执行)
      任一 NO  → 该层及之后所有层全部重建

关键推论:
  1. 层顺序决定缓存效率 — 变动频繁的放后面
  2. 一条 RUN 内指令文本变化 → 整层失效
  3. COPY 的文件内容变化 → 该 COPY 及之后全失效
```

**缓存友好的依赖安装顺序**（最重要的一条规则）：

```dockerfile
# ❌ 错误: 先拷全部代码再装依赖
COPY . .
RUN npm ci          # 改一行代码 → 依赖全重装

# ✅ 正确: 依赖定义文件先行
COPY package.json package-lock.json ./
RUN npm ci          # 依赖没变 → 永远命中缓存
COPY . .
```

### 4.2 启用 BuildKit

BuildKit 是 Docker 的新一代构建引擎（Docker 23.0+ 默认启用），提供并行构建、缓存挂载、密钥传递等能力。

```bash
# Docker < 23.0 手动启用
export DOCKER_BUILDKIT=1
docker build -t myapp:1.0 .

# 或 daemon.json 全局启用
# /etc/docker/daemon.json
{
  "features": {
    "buildkit": true
  }
}
```

### 4.3 缓存挂载：`--mount=type=cache`

包管理器缓存（apt/pip/npm/go）写在镜像层里是浪费——既增大镜像又随层失效。BuildKit 的 cache mount 把缓存挂到构建机的持久目录，**不进镜像层**。

```dockerfile
# apt: 软件包缓存不进镜像
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && apt-get clean

# pip: wheel 缓存
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# npm: 全局缓存
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production

# Go: 模块缓存
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

# Maven: .m2 仓库
RUN --mount=type=cache,target=/root/.m2 \
    mvn package -DskipTests

# yarn / pnpm
RUN --mount=type=cache,target=/usr/local/share/.cache/yarn yarn install
RUN --mount=type=cache,target=/root/.local/share/pnpm/store pnpm install --frozen-lockfile
```

**cache mount 参数**：

| 参数 | 说明 | 示例 |
|:---|:---|:---|
| `target` | 缓存挂载点 (容器内路径) | `target=/root/.npm` |
| `id` | 多阶段间共享缓存的标识 | `id=npm-cache` |
| `sharing` | 并发策略: `shared`/`private`/`locked` | `sharing=locked` (apt 必须 locked) |
| `ro` | 只读挂载 | `ro=true` |

**多阶段共享缓存**：不同阶段用相同 `id` 的 cache mount 共享同一份缓存：

```dockerfile
FROM node:20-alpine AS deps
RUN --mount=type=cache,id=npm,target=/root/.npm npm ci

FROM node:20-alpine AS build
RUN --mount=type=cache,id=npm,target=/root/.npm npm ci && npm run build
```

### 4.4 源码挂载：`--mount=type=bind`

避免把源码 COPY 进镜像层（层大且泄源码），直接用 bind mount 只读挂载上下文：

```dockerfile
# 对比:
# COPY . .                 → 源码进层, 层体积 = 源码大小
# --mount=type=bind,target=. → 源码只读挂载, 不进层

FROM golang:1.22-alpine AS builder
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=bind,source=.,target=/src \
    cd /src && go build -o /out/app .
```

### 4.5 其他 BuildKit 特性

**并行构建**：BuildKit 自动并行执行无依赖关系的阶段。

```text
构建 DAG 示例:
  builder-go ──┐
               ├──→ 最终镜像 (等最慢的阶段)
  builder-web ─┘
  (两个阶段并行跑, 总耗时 = max(两者) 而非 两者之和)
```

**跳过未用阶段**：最终阶段没引用的阶段不构建。例如 `--target=prod` 构建时，`test` 阶段（若有）自动跳过。

**输出类型控制**：

```bash
# 只导出镜像
docker build --output type=image,name=myapp:1.0 .

# 直接把产物拷到本地目录 (无需运行容器)
docker build --output type=local,dest=./dist --target builder .
# 等价于: 构建 builder 阶段后把 /out 拷出来

# 导出为 tar 包
docker build --output type=tar,dest=app.tar .
```

**内联构建缓存**：

```bash
# 把缓存元数据写进镜像 → 推仓库后其他机器拉取即得缓存
docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t myapp:1.0 .
```

### 4.6 远程缓存（CI 关键）

CI 里每次都是全新机器，本地缓存不生效。远程缓存是 CI 提速的关键：

| 缓存后端 | 用法 | 适用 |
|:---|:---|:---|
| registry (镜像仓库) | `--cache-from type=registry,ref=myapp:cache --cache-to type=registry,ref=myapp:cache,mode=max` | 有 Harbor/Docker Hub |
| gha (GitHub Actions) | `--cache-from type=gha --cache-to type=gha,mode=max` | GitHub Actions |
| local | `--cache-from type=local,src=... --cache-to type=local,dest=...` | 自建 CI 挂载持久盘 |
| s3 | `--cache-from type=s3,region=...,bucket=...` | AWS 环境 |

**Harbor/Registry 远程缓存示例**：

```bash
docker build \
  --cache-from type=registry,ref=harbor.example.com/myapp/cache \
  --cache-to type=registry,ref=harbor.example.com/myapp/cache,mode=max \
  -t harbor.example.com/myapp/app:1.0.0 .
```

> `mode=max` 导出所有层缓存（默认只导出已命中的层），首次全量导出会稍慢，但之后每次构建都能命中。`mode=min` 只导出最终层，适合镜像本身很小的情况。

---

## 五、构建上下文与 .dockerignore

### 5.1 构建上下文原理

```text
docker build . 的执行过程:

  1. 客户端把 "." (构建上下文) 打包成 tar
  2. 发送给 dockerd / buildkitd
  3. 构建器在上下文中执行 Dockerfile

  问题:
  ├─ 上下文 = 整个目录递归打包
  ├─ 包含 .git/ node_modules/ dist/ 等垃圾 → 传输慢
  ├─ 文件多 → 每次 COPY 都要重新比较校验
  └─ 上下文内容变化 → 该层缓存失效

  注意: Dockerfile 里的 COPY 只能访问上下文内的文件
        (../ 越界文件无法 COPY, 会报错)
```

### 5.2 .dockerignore 完整示例

```dockerignore
# 版本控制
.git
.gitignore
.svn

# CI/CD
.gitlab-ci.yml
Jenkinsfile
.github

# 依赖目录 (绝不进镜像)
node_modules
vendor
.venv
__pycache__
*.pyc
.m2

# 构建产物
dist
build
target
*.log
coverage

# 本地环境
.env
.env.*
docker-compose*.yml
Dockerfile*
.dockerignore
.idea
.vscode
*.swp
.DS_Store

# 大数据/测试文件
data
*.csv
*.parquet
test
tests
```

**效果量化**：

```bash
# 加 .dockerignore 前后对比
$ du -sh .                      # 项目目录 850MB
$ tar -czf /dev/null . 2>/dev/null   # 未忽略: 上下文 ~800MB
$ docker build -t app .         # 第一次构建上下文传输耗时 ~2min

# 加 .dockerignore 后
# 上下文降到 ~5MB, 传输 < 1s, COPY 层校验也快一个数量级
```

### 5.3 上下文瘦身技巧

| 技巧 | 做法 | 收益 |
|:---|:---|:---|
| 最小上下文 | 只把 Dockerfile + 源码放一个目录 | 传输最小 |
| 单独构建目录 | `docker build -f docker/Dockerfile docker/` | 上下文限定在 docker/ |
| 用 .dockerignore 白名单 | 先忽略全部再放行 | 不会漏 |
| git 子目录检出 | CI 里只 checkout 需要的子目录 | 大仓友好 |

**白名单式 .dockerignore**（先全忽略，再放行）：

```dockerignore
*
!src/
!package.json
!package-lock.json
!Dockerfile
!docker-entrypoint.sh
```

> **陷阱**：`.dockerignore` 不支持 `!` 重新包含目录内文件再排除子目录的复杂嵌套规则（如 `!src/` + `src/*.log`），规则匹配顺序是从上到下，最后一个匹配的规则生效。白名单模式必须放行到文件级。

---

## 六、基础镜像选型

### 6.1 主流基础镜像对比

| 镜像 | 体积 (无应用) | 包管理器 | Shell | 用户态 | 适用场景 |
|:---|:---|:---|:---|:---|:---|
| `scratch` | 0MB | 无 | 无 | 无 | 纯静态 Go/Rust 二进制 |
| `alpine:3.20` | ~7MB | apk (musl) | busybox sh | 无 | 通用精简, musl 兼容注意 |
| `debian:bookworm-slim` | ~80MB | apt (glibc) | bash | 有 | 通用, glibc 兼容性最好 |
| `ubuntu:24.04` | ~78MB | apt (glibc) | bash | 有 | 企业习惯, 和物理机一致 |
| `distroless/static` | ~2MB | 无 | 无 | nonroot | 静态二进制 + 证书 |
| `distroless/base` | ~20MB | 无 | 无 | nonroot | glibc 动态程序 |
| `distroless/java17` | ~130MB | 无 | 无 | nonroot | Java 运行 |
| `distroless/nodejs20` | ~85MB | 无 | 无 | nonroot | Node 运行 |
| `distroless/python3` | ~50MB | 无 | 无 | nonroot | Python 运行 (非官方维护) |

**musl vs glibc 的坑**：

```text
alpine 用 musl libc:
  ├─ 体积小 (静态链接 musl, 无 glibc 兼容层)
  ├─ 二进制兼容性: 用 glibc 编译的动态程序可能报
  │   "not found" / 段错误 (如 Oracle JDK, 部分 C 扩展)
  ├─ DNS 解析差异: musl 对 /etc/resolv.conf 处理与 glibc 不同
  │   (老版本不读 search 域, 需 /etc/hosts 兜底)
  └─ 结论: 自己编译的语言 (Go/Rust/纯解释型) 用 alpine 没问题;
           依赖预编译二进制 (Java 原生库/Python wheel) 优先 debian-slim
```

### 6.2 各语言运行时镜像推荐

| 语言 | 首选 | 备选 | 说明 |
|:---|:---|:---|:---|
| Go (静态) | scratch | distroless/static | CGO_ENABLED=0 后零依赖 |
| Go (CGO) | distroless/base | debian-slim | 需要 glibc |
| Java | eclipse-temurin:17-jre | distroless/java17 | 不要用 jdk 镜像跑生产 |
| Node | node:20-alpine | distroless/nodejs20 | alpine 注意原生模块编译 |
| Python | python:3.12-slim | python:3.12-alpine | wheel 兼容性 slim 更稳 |
| Rust | scratch | distroless/static | 同 Go |
| PHP | php:8.3-fpm-alpine | php:8.3-fpm | 官方已出 alpine 变体 |
| 通用运维工具 | debian:bookworm-slim | alpine | 需要 shell + 包管理时 |

### 6.3 基础镜像固定版本（可复现性）

```dockerfile
# ❌ 漂移: 每次构建拉最新 tag
FROM node:20

# ✅ 固定 digest (完全不可变)
FROM node:20.14.0-alpine@sha256:5d8a7a0b8c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f

# 或至少固定大版本小版本
FROM node:20.14.0-alpine
```

```bash
# 获取 digest
docker buildx imagetools inspect node:20.14.0-alpine | grep Digest
docker pull node:20.14.0-alpine && docker inspect --format='{{index .RepoDigests 0}}' node:20.14.0-alpine
```

> **原则**：`latest` 只用于本地开发。CI/生产构建必须固定 tag + digest，否则一次上游更新可能导致不可复现的构建差异（甚至供应链投毒）。

### 6.4 多架构构建 (Buildx)

```bash
# 创建多架构构建器
docker buildx create --name multiarch --driver docker-container --use
docker buildx ls

# 构建并推送 amd64 + arm64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t harbor.example.com/myapp/app:1.0.0 \
  --push .

# 只构建到本地 (当前架构)
docker buildx build --platform linux/arm64 -t myapp:arm64 --load .
```

```dockerfile
# Dockerfile 里按架构选择基础镜像
FROM --platform=$BUILDPLATFORM golang:1.22-alpine AS builder
ARG TARGETOS TARGETARCH
RUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -o /out/app .

FROM --platform=$TARGETPLATFORM scratch
COPY --from=builder /out/app /app
```

> **关键点**：`--platform=$BUILDPLATFORM` 让构建阶段在构建机架构上跑（快），`$TARGETPLATFORM` 让运行阶段匹配目标架构。`ARG TARGETOS/TARGETARCH` 是 buildx 自动注入的预定义变量，直接用即可。

---

## 七、高级技巧

### 7.1 ARG / ENV 跨阶段传递

```dockerfile
# ARG: 构建期变量 (可跨阶段传递, 需在各阶段重复声明)
ARG VERSION=1.0.0

FROM golang:1.22-alpine AS builder
ARG VERSION                      # 阶段内重新声明才能用
RUN go build -ldflags "-X main.Version=$VERSION" -o /out/app .

FROM scratch
ARG VERSION                      # 运行阶段也可声明
LABEL version=$VERSION
COPY --from=builder /out/app /app

# ENV: 运行期环境变量 (镜像层, 进最终镜像)
FROM node:20-alpine
ENV NODE_ENV=production \
    PORT=3000
```

| 变量类型 | 生命周期 | 进最终镜像 | 用途 |
|:---|:---|:---|:---|
| `ARG` | 仅构建期 | 否 (但 `ENV ARG=$ARG` 可固化) | 版本号、镜像源、开关 |
| `ENV` | 运行期 | 是 (环境变量在层里) | 运行时配置默认值 |

**构建参数注入**：

```bash
docker build --build-arg VERSION=2.0.0 -t myapp:2.0.0 .
# Dockerfile 里 ARG VERSION 会收到 2.0.0
```

> **安全注意**：`--build-arg` 传密钥（如 token）会留在镜像历史里（`docker history` 可见），密钥必须走 7.4 的 secret 机制。

### 7.2 `--target` 多环境构建（dev/prod 分离）

```dockerfile
# ===== 开发阶段: 带热重载工具 =====
FROM node:20-alpine AS dev
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["npm", "run", "dev"]

# ===== 测试阶段: 跑测试 =====
FROM dev AS test
RUN npm run test

# ===== 生产阶段: 精简 =====
FROM node:20-alpine AS prod
WORKDIR /app
ENV NODE_ENV=production
COPY --from=dev /app/node_modules ./node_modules
COPY . .
RUN npm run build
USER node
CMD ["npm", "start"]
```

```bash
docker build --target dev -t myapp:dev .      # 本地开发
docker build --target test -t myapp:test .    # CI 测试 (跑完即弃)
docker build --target prod -t myapp:1.0.0 .   # 发布
```

> 一个 Dockerfile 服务三种环境，杜绝 dev/prod Dockerfile 漂移。BuildKit 下 `--target=prod` 时 `dev`/`test` 阶段**自动跳过**，不会浪费时间。

### 7.3 层数控制与合并

```text
每一条指令一层。层不是免费的:
  ├─ 每层都是 tar 增量 (有元数据开销)
  ├─ 层多 → push/pull 请求多 (Docker Registry API 按层传输)
  └─ 层多 → 历史膨胀 (删除的文件在上一层仍占空间)

控制手段:
  1. 同类操作合并成一条 RUN (&& 连接)
  2. 包管理缓存清理放在同一 RUN 内 (删了才不占层)
  3. 多阶段 (构建产物天然单层)
  4. 不要盲目 squash (会丢失缓存粒度)
```

```dockerfile
# ✅ 一条 RUN 内: 安装 → 清理 (缓存不落层)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ❌ 分开写: 三层, 且 apt lists 缓存留在层里
RUN apt-get update
RUN apt-get install -y libpq5
RUN apt-get clean
```

### 7.4 构建密钥：secrets 与 ssh

**不要用 ARG/ENV 传密钥**（会留在镜像历史和层里）。BuildKit 提供专用机制：

```dockerfile
# ===== 构建密钥 (文件或环境变量) =====
FROM python:3.12-slim AS builder
# 使用挂载的密钥, 不写入任何层
RUN --mount=type=secret,id=pypi_token \
    pip install -r requirements.txt \
    --extra-index-url https://user:$(cat /run/secrets/pypi_token)@private-pypi.example.com/simple/
```

```bash
# 从文件传密钥
docker build --secret id=pypi_token,src=./secrets/token.txt -t myapp .

# 从环境变量传密钥
docker build --secret id=pypi_token,env=PIP_TOKEN -t myapp .
```

**SSH 转发**（私有 git 依赖）：

```dockerfile
FROM golang:1.22-alpine AS builder
# 构建时走本机 SSH agent, 拉私有仓库
RUN --mount=type=ssh \
    go mod download && go build -o /out/app .
```

```bash
# 需要先配置 SSH agent
eval $(ssh-agent)
ssh-add ~/.ssh/id_ed25519
docker build --ssh default -t myapp .
```

### 7.5 HEALTHCHECK 与元数据

```dockerfile
FROM distroless/static:nonroot
COPY --from=builder /out/app /app

# 健康检查: 无 shell 也能用 (distroless 自带 curl? 没有, 用 wget/二进制自检)
# 有 shell 的镜像:
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -q -O - http://127.0.0.1:8080/healthz || exit 1

# 或依赖应用自身 healthz + 编排层探针 (K8s liveness/readiness)
LABEL org.opencontainers.image.title="myapp" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.source="https://git.example.com/myapp" \
      org.opencontainers.image.revision="$(git rev-parse --short HEAD)"
```

---

## 八、镜像分析工具与优化验证

### 8.1 工具矩阵

| 工具 | 定位 | 安装 | 核心能力 |
|:---|:---|:---|:---|
| `docker history` | 内置, 查层 | 自带 | 每层体积、指令、创建者 |
| `dive` | 交互式层分析 | `go install` / brew / 二进制 | 每层文件变化、浪费空间检测、可交互按层浏览 |
| `skopeo` | 仓库/镜像操作 | `dnf install skopeo` / apt | 不拉全镜像查看 manifest、复制镜像、检查远端体积 |
| `ctr` | containerd 原生 | 随 containerd | 镜像管理、内容存储查看 |
| `buildah` | 无 daemon 构建 | dnf/apt | 脚本化构建、从容器导出 |
| `docker-slim` | 自动瘦身 | 二进制 | 动态分析后裁剪未使用文件 |

### 8.2 dive 实战

```bash
# 安装 (Go)
go install github.com/wagoodman/dive@latest

# 分析镜像
dive myapp:1.0.0

# 交互界面:
#   ← → 切换层
#   ↑ ↓ 浏览文件
#   Tab 切换 层视图/文件视图
#   Ctrl+U 只显示本层修改 (找浪费)
#   Space 折叠目录
```

```bash
# CI 非交互模式: 按效率阈值失败
dive --ci myapp:1.0.0 --ci-threshold 0.9
# 镜像效率 = 实际使用字节 / 镜像总字节
# 效率 0.9 = 90% 的镜像内容被实际引用 (未删除文件)
```

**dive 效率低的原因排查**：

| 低效原因 | dive 表现 | 对策 |
|:---|:---|:---|
| 删掉的文件仍在层里 | 下层文件在上层显示删除, 但体积仍占 | 合并 RUN (同层删除) |
| 缓存目录未清理 | 明显的大目录 (npm/.m2/apt lists) | 同层清理 + cache mount |
| 源码拷贝 | src/ 目录完整可见 | 多阶段只拷产物 |
| 测试/文档混入 | test/, *.md, node_modules 全量 | .dockerignore + 多阶段 |

### 8.3 skopeo 实战

```bash
# 查看远端镜像 (不拉取)
skopeo inspect docker://harbor.example.com/myapp/app:1.0.0 | head -20
# 输出: 架构、层列表、各层大小、digest

# 只输出体积统计
skopeo inspect --raw docker://harbor.example.com/myapp/app:1.0.0 | \
  python3 -m json.tool | grep -E 'size|mediaType'

# 跨仓库复制 (Harbor → AWS ECR)
skopeo copy docker://harbor.example.com/myapp/app:1.0.0 \
            docker://123456789.dkr.ecr.cn-north-1.amazonaws.com.cn/myapp:1.0.0 \
            --dest-creds AWS:$(aws ecr get-login-password --region cn-north-1)

# 同步整个仓库
skopeo sync --src docker --dest docker \
  --src-creds user:pass --dest-creds user:pass \
  harbor.example.com/myapp harbor.example.com/myapp-mirror
```

### 8.4 优化验证三板斧

```bash
# 1. 层视角: 看每层大小, 找异常大层
docker history myapp:1.0.0 --no-trunc --format "table {{.Size}}\t{{.CreatedBy}}"

# 2. 内容视角: dive 找浪费
dive --ci myapp:1.0.0

# 3. 运行视角: 真实启动并验证功能
docker run --rm -d -p 8080:8080 --name verify myapp:1.0.0
curl -fsS http://127.0.0.1:8080/healthz && echo OK
docker exec verify sh -c 'ls /usr/bin | wc -l'   # 对比精简效果
```

**优化前后量化表（模板）**：

| 指标 | 优化前 | 优化后 | 变化 |
|:---|:---|:---|:---|
| 镜像体积 | 1.2GB | 158MB | -87% |
| 层数 | 24 | 12 | -50% |
| 构建时间 (无缓存) | 6m20s | 2m10s | -66% |
| 构建时间 (缓存) | 6m20s | 35s | -91% |
| 拉取时间 (100Mbps) | ~96s | ~13s | -86% |
| CVE 数 (Trivy HIGH) | 34 | 2 | -94% |

---

## 九、安全加固

### 9.1 非 root 运行

```text
容器内 root 的危害:
  ├─ 容器逃逸后直接是宿主机 root (无 userns 隔离时)
  ├─ 内核漏洞利用链更短
  └─ 与宿主机共享的挂载点 (如 PVC) 权限灾难

非 root 三层保障:
  1. Dockerfile: USER 非 root 用户
  2. 运行期: docker run --user / K8s securityContext
  3. 内核级: userns-remap / Pod Security (seccomp+AppArmor)
```

```dockerfile
# Alpine/Debian 系: 创建专用用户
FROM debian:bookworm-slim
RUN groupadd -r app && useradd -r -g app -d /app app
USER app

# distroless: 自带 nonroot 用户
FROM gcr.io/distroless/static:nonroot
# 无需额外配置

# 数字 UID (不可变, 兼容任意基础镜像)
USER 65532:65532
```

### 9.2 精简攻击面

| 措施 | 说明 |
|:---|:---|
| 不用 latest | 不可复现 + 可能引入新 CVE |
| 最小基础镜像 | 少一个包少一个 CVE |
| 无 shell 无包管理器 | 被攻破后无法安装工具横向移动 |
| 只装运行依赖 | `--no-install-recommends` / `--only=production` |
| 定期重建 | 基础镜像上游修 CVE 后重新 build + 推送 |
| 固定 digest | 防止上游被投毒 |
| 清理 setuid 位 | `find / -perm -4000` 审计 |

### 9.3 扫描与签名

```bash
# Trivy 扫描 (安装: dnf install trivy / curl 脚本)
trivy image --severity HIGH,CRITICAL myapp:1.0.0
trivy image --ignore-unfixed myapp:1.0.0            # 只看可修复的
trivy image --exit-code 1 --severity CRITICAL myapp:1.0.0   # CI 门禁

# cosign 签名 (Sigstore)
cosign sign --key cosign.key harbor.example.com/myapp/app:1.0.0
cosign verify --key cosign.pub harbor.example.com/myapp/app:1.0.0

# SBOM 生成 (Syft)
syft myapp:1.0.0 -o spdx-json > sbom.spdx.json
```

**CI 门禁策略**：

```text
构建 → Trivy 扫描 (CRITICAL 阻断) → cosign 签名 → 推 Harbor
                                        ↓
                              Harbor 策略: 未签名镜像不允许拉取
```

### 9.4 供应链安全四件套

| 环节 | 工具 | 作用 |
|:---|:---|:---|
| 镜像扫描 | Trivy / Grype / Clair | 已知 CVE 检测 |
| 签名验证 | cosign / Notation | 防篡改 + 来源可信 |
| SBOM | Syft / Trivy | 成分清单, 应急响应 |
| 策略门禁 | Harbor Robot + Webhook / OPA | 不满足策略不放行 |

---

## 十、CI/CD 集成

### 10.1 GitLab CI 完整示例

```yaml
# .gitlab-ci.yml
stages:
  - build
  - scan
  - push

variables:
  IMAGE: harbor.example.com/myapp/app
  # 远程缓存 tag: 每次构建复用上次的缓存层
  CACHE_IMAGE: harbor.example.com/myapp/cache

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker login harbor.example.com -u $HARBOR_USER -p $HARBOR_PASS
    # 远程缓存: 拉上次缓存 + 本次导出新缓存
    - docker buildx build \
        --cache-from type=registry,ref=$CACHE_IMAGE \
        --cache-to type=registry,ref=$CACHE_IMAGE,mode=max \
        --build-arg VERSION=$CI_COMMIT_SHORT_SHA \
        -t $IMAGE:$CI_COMMIT_SHORT_SHA \
        .
    - docker tag $IMAGE:$CI_COMMIT_SHORT_SHA $IMAGE:$CI_COMMIT_REF_NAME

scan:
  stage: scan
  image: aquasec/trivy:latest
  script:
    - trivy image --severity CRITICAL --exit-code 1 $IMAGE:$CI_COMMIT_SHORT_SHA

push:
  stage: push
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker login harbor.example.com -u $HARBOR_USER -p $HARBOR_PASS
    - docker push $IMAGE:$CI_COMMIT_SHORT_SHA
    - docker push $IMAGE:$CI_COMMIT_REF_NAME
  only:
    - main
    - tags
```

> **dind 注意**：GitLab Runner 用 docker executor + docker:dind 时，buildx 的 docker-container driver 可能不可用（嵌套 docker），此时用 `docker build --cache-from` 经典缓存模式或配置外置 buildkitd。

### 10.2 Jenkins 流水线示例

```groovy
// Jenkinsfile (Declarative)
pipeline {
    agent any
    environment {
        IMAGE = "harbor.example.com/myapp/app"
        CACHE = "harbor.example.com/myapp/cache"
        BUILDKIT_PROGRESS = "plain"
    }
    stages {
        stage('Build') {
            steps {
                sh '''
                    docker login harbor.example.com -u ${HARBOR_USER} -p ${HARBOR_PASS}
                    docker buildx create --use --name ci-builder || true
                    docker buildx build \
                        --cache-from type=registry,ref=${CACHE} \
                        --cache-to type=registry,ref=${CACHE},mode=max \
                        --build-arg VERSION=${GIT_COMMIT.take(8)} \
                        -t ${IMAGE}:${GIT_COMMIT.take(8)} \
                        --load .
                '''
            }
        }
        stage('Scan') {
            steps {
                sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --severity CRITICAL --exit-code 1 ${IMAGE}:${GIT_COMMIT.take(8)}'
            }
        }
        stage('Push') {
            when { branch 'main' }
            steps {
                sh '''
                    docker push ${IMAGE}:${GIT_COMMIT.take(8)}
                    docker tag ${IMAGE}:${GIT_COMMIT.take(8)} ${IMAGE}:latest
                    docker push ${IMAGE}:latest
                '''
            }
        }
    }
}
```

### 10.3 CI 缓存策略决策表

| 场景 | 缓存方案 | 说明 |
|:---|:---|:---|
| 自建 GitLab + Harbor | registry 远程缓存 | 免额外存储 |
| GitHub Actions | `type=gha` | 自动按仓库分桶 |
| 裸机 Jenkins 常驻 agent | local cache (agent 磁盘) | 最快, 但多 agent 不共享 |
| 多 agent 轮询 | registry 缓存 + 构建机挂 NFS cache | 共享 |
| K8s 内构建 (buildkitd) | local (PVC) 或 registry | 看规模 |

```bash
# GitHub Actions 专用缓存示例 (build-push-action 自动处理)
# 只需在 workflow 里设置:
#   cache-from: type=gha
#   cache-to: type=gha,mode=max
```

---

## 十一、故障排查

### 11.1 常见错误速查

| 错误信息 | 原因 | 解法 |
|:---|:---|:---|
| `COPY --from=xxx: not found` | 阶段名拼错 / 阶段未定义 | 检查 `AS` 名称, `docker build --target` 时该阶段可能被跳过 |
| `failed to solve: failed to fetch` | 基础镜像拉取失败 | 检查网络/镜像加速器/Harbor 代理 |
| `no space left on device` | 构建缓存膨胀 | `docker builder prune -af`, 查看 `/var/lib/docker` |
| `x509: certificate signed by unknown authority` | scratch 无 CA 证书 | 从 builder 阶段 COPY 证书 |
| `exec: "/app": permission denied` | 二进制不可执行 / 架构不符 | `chmod +x` / 检查 GOARCH |
| `standard_init_linux.go: exec format error` | **架构不匹配** (amd64 镜像跑 arm64) | `--platform` 指定 / buildx 多架构 |
| `not found` (动态链接) | 缺 .so (alpine musl 跑 glibc 程序) | 换 debian-slim / distroless/base |
| 缓存一直不命中 | COPY 的文件顺序/内容变动 / 上下文大 | 依赖文件前置 + .dockerignore |
| `failed to compute cache key` | COPY 源路径不在上下文 | 检查 .dockerignore 是否误杀 |
| 时区不对 | 容器 UTC | 拷贝 zoneinfo 或设 `TZ=Asia/Shanghai` |
| npm 装不上原生模块 | alpine 缺编译链 / musl 兼容 | 换 debian-slim 或用 `--build-from-source` |

### 11.2 缓存失效排查

```bash
# 查看构建时哪层缓存命中
docker build --progress=plain -t myapp . 2>&1 | grep -E "CACHED|COPY|RUN"
# 输出示例:
#  CACHED [builder 2/5] COPY go.mod go.sum ./
#  CACHED [builder 3/5] RUN go mod download
#  [builder 4/5] COPY . .          ← 从这里开始重建 (源码变了)
#  [builder 5/5] RUN go build ...

# 确认上下文大小
docker build --no-cache -t myapp . 2>&1 | grep -i context
```

**排查清单**：

```text
□ 依赖定义文件是否在 COPY . 之前?
□ COPY 的目录里是否混入频繁变动文件 (如 version 文件)?
□ .dockerignore 是否排除了 node_modules/.git/dist?
□ 构建是否每次在不同机器 (无共享缓存)?
□ 时间戳类文件是否导致层指纹变化 (如 build time 注入)?
```

### 11.3 构建慢排查

| 症状 | 可能原因 | 对策 |
|:---|:---|:---|
| 上下文传输慢 | 目录巨大 | .dockerignore / 最小上下文 |
| 依赖下载慢 | 海外源 | 换国内源 (aliyun/tencent) |
| 单条 RUN 慢 | 未缓存 | 依赖前置 + cache mount |
| 阶段串行 | 阶段间无并行 | BuildKit 自动并行 |
| 每次全量重建 | 无远程缓存 | registry/gha 缓存 |
| 编译慢 | 构建资源小 | 构建机加 CPU/内存 (并行编译) |

**国内镜像源加速**：

```dockerfile
# pip
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# npm
RUN npm config set registry https://registry.npmmirror.com

# apt
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.debian12

# go
RUN go env -w GOPROXY=https://goproxy.cn,direct
```

### 11.4 体积排查

```bash
# 每层大小
docker history myapp:1.0.0 --format "table {{.Size}}\t{{.CreatedBy}}" | head -30

# 实际使用空间 (dive)
dive myapp:1.0.0

# 无用镜像/构建缓存清理 (注意: 生产谨慎, 先确认无引用)
docker builder prune -af          # 构建缓存
docker image prune -a             # 悬空镜像
```

---

## 十二、对比总结

### 12.1 优化手段效果总览

| 手段 | 主要收益 | 成本 | 优先级 |
|:---|:---|:---|:---|
| 多阶段构建 | 体积 -80~98%, 攻击面大减 | 低 (语法学习) | ★★★★★ |
| .dockerignore | 构建提速, 缓存命中率↑ | 极低 | ★★★★★ |
| 依赖层前置 | 缓存命中, 构建提速 | 极低 (调顺序) | ★★★★★ |
| BuildKit 缓存挂载 | 构建提速, 镜像不膨胀 | 低 | ★★★★ |
| 基础镜像选型 | 体积 -50~90% | 低 (换 FROM) | ★★★★ |
| 远程缓存 (CI) | CI 构建从分钟级到秒级 | 中 (配置) | ★★★★ |
| 非 root + 精简 | 安全 | 低 | ★★★★ |
| 固定 digest | 可复现 + 供应链安全 | 低 | ★★★ |
| 扫描 + 签名 | 供应链安全 | 中 (工具链) | ★★★ |
| 多架构 buildx | 兼容 ARM 环境 | 中 (构建器) | ★★★ |

### 12.2 单阶段 vs 多阶段 vs 多阶段+BuildKit

| 对比项 | 单阶段 | 多阶段 | 多阶段 + BuildKit |
|:---|:---|:---|:---|
| 镜像体积 | 大 (全工具链) | 小 (仅产物) | 同左 |
| 层数 | 多 | 少 | 同左 |
| 构建并行 | 无 | 有限 | ✅ 自动并行 |
| 缓存挂载 | 无 | 无 | ✅ cache/secret/ssh |
| 未用阶段跳过 | 无 | 部分 | ✅ |
| 多架构 | 手动 | 手动 | ✅ buildx 一条命令 |
| 远程缓存 | 仅 classic | 仅 classic | ✅ 多后端 |
| 适用 | 本地实验 | 生产基线 | 生产 + CI |

### 12.3 推荐的黄金组合

```text
生产镜像基线 (可复制):

  Dockerfile 结构:
  1. FROM <构建镜像> AS builder       # 依赖前置 + cache mount
  2. RUN --mount=type=cache ...       # 包管理器缓存
  3. FROM <精简运行镜像>              # scratch/distroless/slim
  4. COPY --from=builder <产物>       # 只拷产物
  5. USER 非root
  6. HEALTHCHECK + 固定版本

  配套:
  - .dockerignore (白名单式)
  - docker buildx build (多架构 + registry 远程缓存)
  - Trivy 扫描 + cosign 签名 + Syft SBOM
  - CI 门禁: CRITICAL CVE 阻断
```

---

## 十三、配置速查表

### 13.1 Dockerfile 指令速查

| 指令 | 作用 | 多阶段相关要点 |
|:---|:---|:---|
| `FROM <img> [AS <name>]` | 定义阶段 | 阶段名供 `COPY --from` 引用 |
| `COPY --from=<name>` | 跨阶段拷贝 | 多阶段的核心 |
| `ARG <name>[=<default>]` | 构建参数 | 跨阶段需重复声明 |
| `ENV <k>=<v>` | 环境变量 | 进最终镜像 |
| `RUN --mount=type=cache` | 缓存挂载 | BuildKit 专用 |
| `RUN --mount=type=secret` | 密钥挂载 | 不落层 |
| `RUN --mount=type=ssh` | SSH 转发 | 拉私有依赖 |
| `USER <uid>` | 非 root | 数字 UID 最稳 |
| `HEALTHCHECK` | 健康检查 | 无 shell 镜像用二进制自检 |
| `LABEL` | 元数据 | 版本/来源/修订号 |

### 13.2 常用构建命令速查

```bash
# 基础构建
docker build -t myapp:1.0.0 .
docker build --no-cache -t myapp:1.0.0 .          # 禁用缓存 (排查用)

# 指定 Dockerfile 与上下文
docker build -f docker/Dockerfile -t myapp .

# 目标阶段
docker build --target prod -t myapp:1.0.0 .

# 构建参数
docker build --build-arg VERSION=1.0.0 -t myapp .

# BuildKit 远程缓存
docker build \
  --cache-from type=registry,ref=harbor.example.com/myapp/cache \
  --cache-to type=registry,ref=harbor.example.com/myapp/cache,mode=max \
  -t harbor.example.com/myapp/app:1.0.0 .

# 多架构
docker buildx build --platform linux/amd64,linux/arm64 -t app:1.0 --push .

# 产物导出 (不经仓库)
docker build --output type=local,dest=./dist --target builder .

# 缓存清理
docker builder prune -af

# 镜像层/体积分析
docker history myapp:1.0.0
dive myapp:1.0.0
skopeo inspect docker://harbor.example.com/myapp/app:1.0.0
```

### 13.3 镜像体积目标参考

| 应用类型 | 目标体积 | 参考基线 |
|:---|:---|:---|
| Go/Rust 静态二进制 | < 50MB | scratch + 产物 ~15MB |
| Java 服务 | < 300MB | JRE-alpine + jar |
| Node 服务 | < 200MB | alpine + 生产依赖 |
| Python 服务 | < 250MB | slim + venv |
| 运维工具类 | < 100MB | alpine |

### 13.4 检查清单

```text
构建前:
  □ 基础镜像固定 tag + digest
  □ .dockerignore 已配置 (排除 node_modules/.git/dist)
  □ 依赖定义文件前置, COPY . 在后
  □ 包管理器缓存用 cache mount (BuildKit)
  □ 密钥用 secret/ssh, 不用 ARG/ENV 传

构建后:
  □ 非 root 用户 (USER)
  □ 多阶段只拷产物
  □ 时区/CA 证书已处理
  □ HEALTHCHECK 已加
  □ Trivy 扫描无 CRITICAL
  □ 签名 + SBOM (生产)

CI:
  □ 远程缓存已配置 (registry/gha)
  □ 扫描门禁阻断 CRITICAL
  □ 多架构构建 (如需要)
  □ 只推 main/tags 分支
```

### 13.5 一分钟优化的最快路径

```text
如果只做三件事:
  1. 多阶段构建: 构建阶段和运行阶段分离 (体积立减 80%+)
  2. 依赖前置: COPY package*.json 先于 COPY . (缓存立竿见影)
  3. .dockerignore: 排除 node_modules/.git/dist (上下文瘦身)

如果再多做三件事:
  4. BuildKit cache mount: --mount=type=cache (构建提速)
  5. 远程缓存: --cache-from/to type=registry (CI 提速)
  6. 非 root + Trivy 扫描 (安全底线)
```

*最后更新: 2026-08-25*

