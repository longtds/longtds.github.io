# 03_网络 · 概述

> 网络是分布式系统的连接组织。从七层协议到 SDN/SmartNIC，再到 RDMA/CXL，网络的形态在不断进化。

## 一、网络发展简史

| 阶段 | 时期 | 标志 |
|:---|:---:|:---|
| 局域网 | 1980s | Ethernet/Token Ring |
| TCP/IP | 1990s | 互联网成型 |
| 千兆/万兆 | 2000s | 数据中心普及 |
| 虚拟化网络 | 2010s | VXLAN/Open vSwitch |
| SDN | 2014-2020 | 控制面与数据面分离 |
| 云原生网络 | 2018-至今 | CNI、Service Mesh、eBPF |
| 高速智能网络 | 2020-至今 | 400G/800G、DPU、RDMA |

## 二、网络协议栈

```
应用层    HTTP/HTTPS/gRPC/MQTT/DNS/SSH
─────────────────────────────────────
传输层    TCP/UDP/QUIC/SCTP
─────────────────────────────────────
网络层    IPv4/IPv6/ICMP/路由协议 (BGP/OSPF)
─────────────────────────────────────
数据链路  Ethernet/VLAN/VXLAN/MPLS
─────────────────────────────────────
物理层    光纤/双绞线/无线
```

## 三、数据中心网络架构

```
传统三层架构 (Core-Aggr-Access)
        ↓
现代 Spine-Leaf 架构（CLOS 拓扑）
        ↓
            Spine (核心交换)
           /  |  |  |  \
          Leaf Leaf Leaf...（接入交换）
           |     |
        Server Server
```

| 维度 | 传统三层 | Spine-Leaf |
|:---|:---|:---|
| 延迟 | 不可预测 | 任意两点 2 跳 |
| 扩容 | 受 Core 限制 | 横向加 Leaf |
| 东西向流量 | 弱 | 强（云原生友好） |

## 四、本章组织

| 子章节 | 内容 |
|:---|:---|
| **基础网络协议** | OSI/TCPIP、二/三/四/应用层 |
| **网络设备与运维** | 交换机/路由器配置、流量分析 |
| **SDN** | OpenFlow/控制器/OVS/OVN |
| **高速网络** | 25/100/400G、RDMA、RoCE |
| **网络排查工具** | tcpdump/Wireshark/iperf/eBPF |
| **网络项目与实验** | 实战演练 |

## 五、学习路径

1. **协议基础** → OSI 七层 + TCP/IP 四层
2. **设备配置** → VLAN、路由、ACL
3. **进阶虚拟化** → VXLAN、Open vSwitch
4. **云原生** → CNI、Service Mesh、Cilium
5. **高性能** → RDMA、DPU、SR-IOV

> 📖 网络的核心思维：分层封装、地址唯一、路由可达、可观测。
