# 容器原理

## Namespace

Namespace 实现资源隔离：

| Namespace | 隔离内容 | 作用 |
|:---|:---|:---|
| PID | 进程 ID | 进程隔离 |
| Network | 网络栈 | 网络隔离 |
| Mount | 挂载点 | 文件系统隔离 |
| UTS | 主机名/域名 | 主机名隔离 |
| User | 用户 ID | 用户隔离 |
| IPC | 进程间通信 | IPC 隔离 |

## Cgroup

Cgroup 实现资源限制：

| 子系统 | 限制内容 |
|:---|:---|
| cpu | CPU 使用时间/份额 |
| memory | 内存使用上限 |
| blkio | 块设备 IO |
| cpuset | CPU 核心绑定 |
| pid | 进程数限制 |

## UnionFS（联合文件系统）

Docker 镜像使用分层存储：

```
Container Layer (R/W)
    ┌─────────────┐
    │ 镜像层 N    │ (R/O)
    ├─────────────┤
    │ ...         │
    ├─────────────┤
    │ 镜像层 1    │ (R/O)
    └─────────────┘
    ┌─────────────┐
    │ Base Layer  │ (R/O)
    └─────────────┘
```
