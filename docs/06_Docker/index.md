# 06_Docker · 概述

> Docker 把容器技术从工程师玩具变成了 IT 主流。即使现在 K8s 用 containerd/CRI-O，Docker 依然是开发者的容器入门。

## 一、容器发展简史

| 阶段 | 时期 | 关键技术 |
|:---|:---:|:---|
| chroot | 1979 | 文件系统隔离雏形 |
| FreeBSD jails | 2000 | 进程隔离 |
| Solaris Zones | 2004 | 资源限制 |
| LXC | 2008 | Linux 容器内核能力（namespace + cgroup） |
| Docker | 2013 | 镜像 + 工具链革命 |
| OCI 标准化 | 2015 | runc + image spec |
| containerd | 2016 | 解耦运行时 |
| K8s dockershim 移除 | 2022 | K8s 改用 containerd |

## 二、容器核心原理

容器 = **进程 + namespace（隔离）+ cgroup（资源限制）+ 镜像（文件系统）**

```
┌─────────────────────────────────────────┐
│            容器进程                      │
├─────────────────────────────────────────┤
│  Linux Namespace (隔离视图)              │
│  ├── pid   ── 进程号                    │
│  ├── net   ── 网卡/路由                 │
│  ├── mount ── 文件系统                  │
│  ├── uts   ── 主机名                    │
│  ├── ipc   ── 进程间通信                │
│  └── user  ── 用户/UID                  │
├─────────────────────────────────────────┤
│  cgroup v2 (资源限制)                   │
│  ├── cpu/cpuset                         │
│  ├── memory                             │
│  ├── blkio                              │
│  └── pid                                │
├─────────────────────────────────────────┤
│  OverlayFS (分层文件系统)                │
└─────────────────────────────────────────┘
              ↓ 共享
       Linux Kernel
```

## 三、Docker 架构

```
docker (CLI)
   ↓ REST
dockerd (守护进程)
   ↓ gRPC
containerd
   ↓ shim
runc (OCI runtime)
   ↓
containerd-shim → 容器进程
```

## 四、镜像分层

```
镜像 = 多层只读 + 一层可写

┌──────────────────────────┐
│  容器层 (可写)            │  ← 容器运行时改动
├──────────────────────────┤
│  应用层 (RUN/COPY/ADD)    │  ← Dockerfile 指令
├──────────────────────────┤
│  运行时层 (apt/pip)       │
├──────────────────────────┤
│  基础镜像 (ubuntu/alpine) │
└──────────────────────────┘
```

每层只读、可缓存、可复用，这是 Docker 镜像比 VM 镜像高效的核心。

## 五、本章组织

| 子章节 | 内容 |
|:---|:---|
| **01_容器原理** | namespace、cgroup、OverlayFS、镜像 |
| **02_Docker实践** | Dockerfile 最佳实践、多阶段构建 |
| **03_运行时** | Docker/containerd/CRI-O/Podman 对比 |
| **04_容器化迁移** | 应用容器化的步骤和坑 |

## 六、学习路径

1. **核心原理** → 手写一个 mini-docker（namespace + chroot）
2. **Dockerfile 精通** → 多阶段、缓存优化、安全基线
3. **运行时切换** → 至少熟悉 Docker + containerd
4. **生产经验** → 镜像安全、构建提速、私有仓库

> 📖 Docker 已经"成熟"，K8s 时代它的角色变成开发者工具，而非生产环境运行时。
