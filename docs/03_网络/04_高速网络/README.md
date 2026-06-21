# 高速网络

## RDMA

RDMA 允许一台计算机直接访问另一台计算机的内存，无需 CPU 参与数据传输，极大降低延迟。

## InfiniBand

| 特性 | 说明 |
|:---|:---|
| 带宽 | HDR 200Gbps / NDR 400Gbps |
| 延迟 | < 1μs |
| 拓扑 | Fat-Tree / DragonFly |
| 子网管理器 | OpenSM / Fabric Manager |

## RoCEv2

RoCE（RDMA over Converged Ethernet）是在标准以太网上实现 RDMA 的方案。

| 方案 | 网络 | 延迟 | 成本 |
|:---|:---|:---:|:---:|
| InfiniBand | IB 专网 | < 1μs | 高 |
| RoCEv2 | 标准以太网 | ~2μs | 中 |

## GPU 集群网络规划

- 计算网络：100Gbps+ RoCE 或 IB，承载 NCCL 通信
- 存储网络：25-100Gbps，访问 S3 和数据集
- 管理网络：1-10Gbps，带外管理
