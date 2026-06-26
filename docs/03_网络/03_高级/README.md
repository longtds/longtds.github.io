# 高级

> 网络高级 = **SDN/OpenFlow + Overlay 网络(VXLAN/Geneve) + eBPF/XDP 数据面 + DPDK/SmartNIC/DPU + RDMA/RoCE/InfiniBand + 服务网格(Istio/Cilium) + 高速网络调优 + 国产化网络栈**。本章面向需要做底层网络平台、AI 集群网络、数据中心架构的高级工程师。

## 一、SDN 与 OpenFlow

### 1.1 SDN 三层模型

```
应用层 (App)            业务策略（QoS / 安全 / 路由策略）
     ↑ NorthBound API（REST）
控制层 (Controller)     全局视图，下发流表
     ↑ SouthBound API（OpenFlow / OVSDB / NETCONF）
数据层 (Switch)         按流表转发（OVS / 硬件交换机）
```

### 1.2 主流控制器

```
开源:
  OpenDaylight (ODL)     大而全 Java
  ONOS                   运营商级
  Ryu                    Python 轻量
  Faucet                 简化 OpenFlow

商业:
  VMware NSX             虚拟化主流
  Cisco ACI              数据中心
  Juniper Contrail
  
国产:
  云杉 DeepFlow + SDN
  华三 (H3C) AD-DC
  锐捷
```

### 1.3 OVS (Open vSwitch) 实战

```bash
# 安装
apt install openvswitch-switch

# 创建网桥
ovs-vsctl add-br br-int
ovs-vsctl add-port br-int eth1

# 看
ovs-vsctl show
ovs-ofctl show br-int
ovs-ofctl dump-flows br-int

# 加流表（OpenFlow）
ovs-ofctl add-flow br-int "in_port=1,actions=output:2"
ovs-ofctl add-flow br-int "priority=100,dl_type=0x0800,nw_dst=10.0.0.0/24,actions=output:3"

# VXLAN 隧道
ovs-vsctl add-port br-tun vxlan0 \
  -- set interface vxlan0 type=vxlan \
     options:remote_ip=192.168.1.20 options:key=100
```

## 二、Overlay 网络

### 2.1 VXLAN 原理

```
Virtual eXtensible LAN
  - 二层报文封装在 UDP 4789 端口里
  - VNI 24 bit (16M 个隔离域)
  - VTEP (VXLAN Tunnel End Point) 做封装/解封

帧格式:
  外层: Ethernet | IP | UDP(4789) | VXLAN(VNI) | 内层: Ethernet | IP | Payload

适合: 多租户数据中心 / K8s CNI / VMware NSX
```

### 2.2 Linux 原生 VXLAN

```bash
# Host A
ip link add vxlan100 type vxlan \
  id 100 \
  local 10.0.0.10 \
  remote 10.0.0.20 \
  dstport 4789 \
  dev eth0
ip addr add 192.168.100.1/24 dev vxlan100
ip link set vxlan100 up

# Host B 对应配置
ip link add vxlan100 type vxlan id 100 \
  local 10.0.0.20 remote 10.0.0.10 dstport 4789 dev eth0
ip addr add 192.168.100.2/24 dev vxlan100
ip link set vxlan100 up

# 测
ping 192.168.100.2

# 看
bridge fdb show dev vxlan100
```

### 2.3 Geneve（VXLAN 的进化）

```
GENEric NEtwork Virtualization
  - 24 bit VNI + 可扩展 TLV
  - OVN / OVS 默认隧道
  - Tungsten Fabric / NSX-T 用
```

### 2.4 GRE / IPIP

```
GRE   通用路由封装，可跑组播 / 多协议
IPIP  IP-in-IP，最简单

# Linux GRE
ip tunnel add gre0 mode gre local 10.0.0.10 remote 10.0.0.20 ttl 64
ip addr add 192.168.99.1/30 dev gre0
ip link set gre0 up
```

## 三、K8s 网络栈深度

### 3.1 CNI 主流对比

| CNI | 数据面 | Overlay | NetworkPolicy | 适用 |
|:---|:---|:---:|:---:|:---|
| **Calico** | eBPF / iptables | BGP / VXLAN | ✅ | 大规模 ⭐ |
| **Cilium** | eBPF / XDP | VXLAN / Geneve / BGP | ✅ L3/L7 | 现代首选 ⭐⭐ |
| **Flannel** | iptables | VXLAN / host-gw | ❌ | 简单测试 |
| **Antrea** | OVS | Geneve | ✅ | VMware 系 |
| **Kube-OVN** | OVS | Geneve | ✅ | 国产首选 ⭐ |
| **AWS VPC CNI** | 原生 ENI | 无 | ✅ | AWS |
| **华为 Yangtse** | DPU | 智能网卡卸载 | ✅ | 华为云 |

### 3.2 Cilium（eBPF 革命）

```bash
# 安装
helm install cilium cilium/cilium --namespace kube-system \
  --set kubeProxyReplacement=true \
  --set bpf.masquerade=true \
  --set ipam.mode=kubernetes \
  --set encryption.enabled=true --set encryption.type=wireguard

# 状态
cilium status
cilium connectivity test
cilium-cli config view

# L7 策略
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata: { name: api }
spec:
  endpointSelector: { matchLabels: { app: api } }
  ingress:
    - fromEndpoints: [{ matchLabels: { app: frontend } }]
      toPorts:
        - ports: [{ port: "8080", protocol: TCP }]
          rules:
            http:
              - method: GET
                path: "/api/v1/.*"
```

### 3.3 Service / kube-proxy 演进

```
模式演进:
  userspace  (远古，已废)
  iptables   规则太多 → O(n) 性能差
  ipvs       LVS in K8s，万级 Service 可用
  eBPF       Cilium kubeProxyReplacement ⭐ 最快

替换 kube-proxy 后:
  iptables 规则归零
  Service / NodePort / LoadBalancer 全走 eBPF
  性能 5-10x 提升
```

## 四、eBPF / XDP 数据面

### 4.1 XDP 三模式

```
XDP_GENERIC   通用，性能一般（任意网卡可用）
XDP_NATIVE    驱动支持（intel/mlx5/bnxt）⭐
XDP_OFFLOAD   网卡硬件卸载（Netronome 等）
```

### 4.2 XDP 程序范例（C）

```c
// xdp_drop.c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int xdp_drop_ipv4(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct ethhdr *eth = data;
    if ((void *)eth + sizeof(*eth) > data_end) return XDP_PASS;
    if (eth->h_proto == __constant_htons(0x0800))
        return XDP_DROP;
    return XDP_PASS;
}
char _license[] SEC("license") = "GPL";
```

```bash
# 编译加载
clang -O2 -target bpf -c xdp_drop.c -o xdp_drop.o
ip link set dev eth0 xdp obj xdp_drop.o sec xdp
ip link show eth0                          # 看 xdp 标记

# 卸载
ip link set dev eth0 xdp off
```

### 4.3 工业应用

```
Cilium       K8s CNI + ServiceMesh
Katran       Meta 的 L4 LB（百亿请求/秒）
Cloudflare   DDoS / 缓存 / WAF 加速
Calico eBPF  替代 iptables
中国应用:
  字节 KubeRay / 火山引擎 veLinux
  阿里云 LoongCollector
  腾讯 TKE eBPF
```

## 五、DPDK / 用户态网络

### 5.1 概念

```
DPDK (Data Plane Development Kit)
  - 网卡绕过内核协议栈，直接用户态收包
  - 大页 + 轮询 + 多队列 + NUMA 绑核
  - 性能: 单核 10-20 Mpps
  - 缺点: 占满 CPU / 开发门槛高

主要消费者:
  OVS-DPDK
  VPP (FD.io)
  网关 / NFV / 商用 5G UPF
  阿里 Tengine / 字节
```

### 5.2 DPDK 编译运行

```bash
# 大页
echo 4096 > /sys/devices/system/node/node0/hugepages/hugepages-2048kB/nr_hugepages
mount -t hugetlbfs nodev /mnt/huge

# 绑网卡
dpdk-devbind.py --status
dpdk-devbind.py -b vfio-pci 0000:01:00.0

# 跑 testpmd
testpmd -l 0-3 -n 4 --huge-dir=/mnt/huge -- -i --portmask=0x1
```

### 5.3 VPP（思科捐赠的高性能数据面）

```
特点:
  - 矢量化包处理（一次处理一组包）
  - 用户态 + DPDK
  - 比 OVS-DPDK 性能高 3-5x
  - 应用: 5G UPF / SD-WAN / 边缘网关
```

## 六、SmartNIC / DPU（卸载革命）

### 6.1 主流产品

| 产品 | 厂商 | 架构 | 应用 |
|:---|:---|:---|:---|
| **BlueField-3** | NVIDIA / Mellanox | ARM + ConnectX | AI 集群 / VMware vSphere 9 |
| **AWS Nitro** | AWS 自研 | 安全 / 网络 / 存储卸载 | EC2 |
| **Pensando** | AMD | P4 可编程 | Oracle / 微软 |
| **海光 / 飞腾 DPU** | 国产 | RISC-V / ARM | 信创集群 |
| **中科驭数 Yusur** | 国产 | 网络卸载 | 金融 / 云 |

### 6.2 DPU 卸载典型场景

```
1. vSwitch 卸载（OVS → DPU 硬件加速）
2. RDMA / RoCE 网络（AI 训练必备）
3. NVMe-oF 存储（远程盘像本地盘）
4. 安全（IPsec/TLS/防火墙卸载）
5. 监控（流采样 / 抓包零开销）
6. Hypervisor 卸载（VMware ESXi 9 / OpenStack）
```

## 七、RDMA / RoCE / InfiniBand

### 7.1 概念

```
RDMA (Remote Direct Memory Access)
  绕过 CPU 直接读写远端内存，延迟 μs 级

3 种实现:
  InfiniBand  专用网络（HPC/AI 主流）
  RoCE v1/v2  基于 Ethernet（数据中心常用）⭐
  iWARP       基于 TCP（已小众）

AI 训练关键:
  - 多机多卡 NCCL allreduce 全靠 RDMA
  - 单卡 H100 节点 8x 400G NDR
  - 大模型集群 = GPU + RDMA + DPU
```

### 7.2 RoCE v2 部署要点

```
硬件:
  Mellanox ConnectX-6 / 7 (NVIDIA)
  Broadcom Thor / Mt. Reagan
  Intel E810

无损以太网必备:
  PFC (Priority Flow Control)   每队列流控
  ECN (Explicit Congestion Notification) 主动告知拥塞
  DCQCN  数据中心 QCN 拥塞算法
```

```bash
# 看 RDMA 设备
ibstat
ibdev2netdev
rdma link show

# 链路状态
ibstatus

# 性能压测
ib_write_bw / ib_read_bw / ib_send_bw
ib_write_lat                              # 延迟
qperf node tcp_bw tcp_lat rc_rdma_write_bw
```

### 7.3 NCCL（AI 必备）

```bash
# 看版本
python -c "import torch; print(torch.cuda.nccl.version())"

# 关键环境
export NCCL_DEBUG=INFO
export NCCL_IB_HCA=mlx5_0,mlx5_1
export NCCL_IB_GID_INDEX=3
export NCCL_SOCKET_IFNAME=eth0
export NCCL_NET_GDR_LEVEL=2               # GPU Direct RDMA

# 测全互联带宽
nccl-tests/build/all_reduce_perf -b 8 -e 8G -f 2 -g 8
```

## 八、服务网格（Service Mesh）

### 8.1 主流方案

| 方案 | 数据面 | 控制面 | 特点 |
|:---|:---|:---|:---|
| **Istio** | Envoy | Istiod | 功能全 ⭐ |
| **Cilium ServiceMesh** | eBPF + Envoy | Cilium | 无 sidecar ⭐ |
| **Linkerd** | Rust micro-proxy | linkerd-control | 轻量 |
| **Consul Connect** | Envoy | Consul | 配置中心一体 |
| **Kuma** | Envoy | Kuma | 多集群 |
| 国产: **Slime / MOSN** | MOSN (蚂蚁) | | 蚂蚁 |

### 8.2 Istio 关键能力

```
流量管理: VirtualService / DestinationRule / Gateway
安全:    mTLS 自动注入 / AuthorizationPolicy
观测:    Envoy access log + tracing + metrics
弹性:    超时 / 重试 / 熔断 / 故障注入

灰度发布范例:
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata: { name: reviews }
spec:
  http:
    - match: [{ headers: { user: { exact: alice } } }]
      route: [{ destination: { host: reviews, subset: v2 } }]
    - route:
        - destination: { host: reviews, subset: v1 }
          weight: 90
        - destination: { host: reviews, subset: v2 }
          weight: 10
```

### 8.3 Sidecar vs Sidecarless 演进

```
Sidecar (经典 Istio): 
  每 Pod 注入 Envoy → 资源开销 ~50MB/Pod
  
Ambient Mesh (Istio 1.22+):
  ztunnel + waypoint proxy → 节点级共享

Cilium ServiceMesh:
  eBPF 内核态处理 → 零 sidecar，性能最佳
```

## 九、高速网络调优（25G/100G/400G）

### 9.1 网卡多队列

```bash
# 看
ethtool -l eth0

# 设置 16 队列
ethtool -L eth0 combined 16

# 中断绑核（NUMA-aware）
# 网卡在 NUMA 0 → 中断绑 NUMA 0 的 CPU
cat /sys/class/net/eth0/device/numa_node
cat /proc/interrupts | grep eth0
echo 7 > /proc/irq/IRQ/smp_affinity_list

# 自动: irqbalance / mlnx-tools
# 关闭 irqbalance 后手工
systemctl stop irqbalance
set_irq_affinity_cpulist.sh 0-15 eth0
```

### 9.2 大页 / 巨型帧

```bash
# Jumbo Frame (MTU 9000)
ip link set eth0 mtu 9000

# 注意: 全链路（交换机、路由器、服务器）都要支持
ping -s 8972 -M do -c 4 peer            # 验证

# RX/TX Ring
ethtool -g eth0
ethtool -G eth0 rx 4096 tx 4096
```

### 9.3 GRO / GSO / TSO offload

```bash
ethtool -k eth0
ethtool -K eth0 tso on gso on gro on lro on   # 开
ethtool -K eth0 tso off                        # 关（特定场景）

# AI 训练场景一般保持开启
# 网络抓包/IDS 场景可能要关 LRO/GRO
```

### 9.4 Coalescing

```bash
ethtool -c eth0
ethtool -C eth0 rx-usecs 100 tx-usecs 100     # 攒一会儿再中断
ethtool -C eth0 adaptive-rx on adaptive-tx on
```

### 9.5 GPU Direct RDMA

```
GPU 显存 ⟷ 网卡 直接 DMA（绕过 CPU 主存）
要求:
  - NVIDIA GPU + Mellanox ConnectX-5/6/7
  - 同一 PCIe Root Complex 或 NVLink
  - kernel module nvidia_peermem

环境:
NCCL_NET_GDR_LEVEL=2
NCCL_NET_GDR_READ=1
```

## 十、QUIC 与 HTTP/3

### 10.1 QUIC

```
基于 UDP，集成 TLS 1.3
特点:
  - 0-RTT 重连
  - 连接迁移（IP 变了不断）
  - 多路复用无队头阻塞
  - 端口 443/udp

主要部署:
  Google / YouTube
  Cloudflare quic-go
  字节 / 阿里 / 微信视频号
  
Linux 服务端:
  Nginx (1.25+ 实验) / HAProxy 2.6+
  Caddy / quiche / msquic / lsquic
```

### 10.2 Nginx HTTP/3 配置

```nginx
# 编译需带 --with-http_v3_module（1.25+）
server {
    listen 443 quic reuseport;
    listen 443 ssl http2;
    ssl_certificate /path/cert.pem;
    ssl_certificate_key /path/key.pem;
    ssl_protocols TLSv1.3;
    add_header Alt-Svc 'h3=":443"; ma=86400';
}
```

## 十一、网络可观测性（eBPF 时代）

### 11.1 工具栈

```
Pixie               K8s 应用零侵入可观测
Coroot              eBPF + Prom + APM
DeepFlow            国产 eBPF 网络可观测 ⭐
Inspektor Gadget    K8s 故障排查工具集
Beyla (Grafana)     自动 trace
hubble (Cilium)     L3-L7 流量可视化
```

### 11.2 Hubble 实战

```bash
hubble status
hubble observe                          # 实时流量
hubble observe --pod default/web --since 1m
hubble observe -t l7 -t drop
hubble observe --to-fqdn '*.google.com'
hubble ui                                # Web 可视化
```

### 11.3 DeepFlow（国产开源 SOTA）

```
能力:
  - eBPF + AF_PACKET 全栈采集
  - 自动应用拓扑
  - 调用链 + RED 指标 + 日志 + tracing 统一
  - 无侵入零代码改动
  
开源: github.com/deepflowio/deepflow
```

## 十二、国产化网络栈

### 12.1 国产 SDN / NFV

```
华为 CloudEngine + iMaster NCE
新华三 (H3C) AD-DC / Comware V9
锐捷 RG-S 系列
中兴 ZXR10
云杉 DeepFlow + NSP
品高 SDN
```

### 12.2 国产 SmartNIC / DPU

```
中科驭数 (Yusur) K2-Pro
星云智联 (Xcalibyte)
大禹智芯 Paratus
中兴 G5
华为擎天 (Tian Tian)
飞腾 ARM-based DPU
```

### 12.3 国产 LB / 网关

```
F5 替代:
  阿里 SLB / Tengine
  腾讯 CLB
  华为 ELB
  深信服 AD
  绿盟 LB
  新华三 SecPath
  
WAF:
  阿里云 WAF
  腾讯云 WAF
  长亭雷池 SafeLine ⭐ 开源
  奇安信 WAF
```

## 十三、典型场景案例

### 13.1 AI 训练集群网络（8x H100）

```
拓扑: 
  Spine-Leaf + InfiniBand NDR (400G) + 8x BlueField-3 DPU
  
关键:
  - 节点内: NVLink 4 (900GB/s)
  - 节点间: 8x 400G IB / RoCE
  - 存储: NVMe-oF (BlueField 卸载)
  - 拓扑感知: PXN / SHARP 协议
  - 拥塞控制: DCQCN / Adaptive Routing
  
工具:
  NCCL all_reduce_perf
  ib_*  延迟带宽
  nv-fabricmanager (NVLink fabric)
```

### 13.2 万节点 K8s 网络（Cilium + DPU）

```
- Cilium kubeProxyReplacement (eBPF 替代 iptables)
- Cilium BGP 给每节点宣告 Pod CIDR
- 部分流量卸载到 BlueField DPU
- L7 mTLS by Cilium ServiceMesh

收益:
  - 万级 Service 延迟稳定（iptables 模式会爆炸）
  - 主机 CPU 用于业务
  - 安全策略零开销下沉到 DPU
```

### 13.3 跨地域多活（BGP Anycast）

```
方案:
  - 同 IP 在多 IDC 宣告 BGP
  - 用户路由到最近 IDC
  - 单 IDC 挂自动撤回
  
开源:
  ExaBGP / GoBGP
  
应用:
  Cloudflare 全球 DNS
  阿里 Anycast EIP
  腾讯云加速服务
```

## 十四、典型坑（高级）

| 坑 | 建议 |
|:---|:---|
| **VXLAN MTU 没减 50** | 内层 MTU 1450 |
| **iptables 规则爆炸** | 上 ipvs 或 Cilium |
| **kube-proxy iptables 模式延迟** | 替换为 Cilium eBPF |
| **OVS 流表千条手抖** | OpenFlow 用 P4 / OVN 抽象 |
| **DPDK 占满 CPU** | 独立核心 isolcpus |
| **RoCE 没配 PFC** | 网络一拥塞重传爆炸 |
| **NCCL 没绑网卡** | NCCL_IB_HCA 显式指定 |
| **MTU 9000 全链路没对齐** | ping -s -M do 验证 |
| **Cilium 没装 hubble** | 看流量靠 tcpdump 累死 |
| **没看 numa_node** | 中断绑核绑错 NUMA |
| **国产 DPU 驱动版本** | 锁版本 / 与 OS 内核匹配 |

## 十五、高级 Checklist

```
SDN/Overlay:
☐ OVS + OpenFlow 上手
☐ VXLAN/Geneve 双机隧道
☐ FRR OSPF/BGP

K8s 网络:
☐ Calico / Cilium 装过
☐ kubeProxyReplacement
☐ NetworkPolicy L3/L7
☐ Hubble / DeepFlow 看流量

eBPF / XDP:
☐ 看过 Cilium 源码大致结构
☐ 写过 XDP_DROP 范例
☐ bpftool prog show

高速:
☐ 25/100/400G 上线过
☐ RoCE / IB 装过
☐ DPDK testpmd 跑过
☐ 中断绑核 NUMA

DPU:
☐ BlueField / 国产 DPU 接入
☐ OVS 卸载验证

ServiceMesh:
☐ Istio / Cilium ServiceMesh
☐ mTLS 自动启用
☐ 灰度发布配过

国产化:
☐ Kube-OVN / DeepFlow / 国产 LB
☐ 飞腾 / 鲲鹏 ARM 网卡兼容
```

## 十六、推荐栈

```
CNI:        Cilium ⭐ / Calico / Kube-OVN
ServiceMesh: Cilium ⭐ / Istio Ambient
LB (云原生): Cilium L4LB + MetalLB / Cloud LB
LB (经典):   LVS + Keepalived + Nginx/HAProxy
SDN:        OVS / OVN / DeepFlow
Overlay:    Cilium VXLAN/Geneve / Tungsten Fabric
高速:       Mellanox ConnectX-7 / BlueField-3
RDMA:       NCCL + RoCE v2 + DCQCN
QUIC:       Nginx 1.25+ / Caddy / Cloudflare quiche
观测:       Hubble / DeepFlow ⭐ / Coroot / Pixie
DPU 国产:   中科驭数 / 星云智联 / 大禹智芯
```

## 十七、学习路径

```
高级（6-12 月）:
  1. OVS + VXLAN + OpenFlow 实验
  2. FRR OSPF/BGP 双节点
  3. Cilium 装 + Hubble + L7 NetworkPolicy
  4. eBPF 入门 + XDP 范例
  5. DPDK testpmd
  6. RoCE / IB 双节点
  7. NCCL all_reduce 多机测试
  8. Istio 灰度发布 + mTLS
  9. HTTP/3 部署
  10. DeepFlow / Coroot 装一个

专家:
  11. K8s 万节点 Cilium 优化
  12. SmartNIC OVS 卸载
  13. 自研 eBPF 网络工具
  14. AI 集群 RoCE 调优
  15. 国产 DPU 适配
```

## 十八、参考资料

```
经典:
  - 《Computer Networks》 Tanenbaum
  - 《TCP/IP Illustrated》Stevens
  - 《BGP4》Sam Halabi

云原生:
  - Cilium docs ⭐
  - Calico docs
  - Istio docs / Envoy docs
  - K8s Network Policy

高速/AI:
  - NVIDIA InfiniBand / NCCL 文档
  - DPDK programmer's guide
  - VPP wiki (fd.io)
  - SIGCOMM / NSDI 论文

国产:
  - DeepFlow 文档 / 公众号
  - 华为云 / 阿里云 网络白皮书
  - InfoQ Cloud Native 专栏
  - Kube-OVN 文档
```

> 📖 **核心判断**：高级 = **eBPF/Cilium + VXLAN/Overlay + RoCE/IB + DPDK/DPU + Istio + 国产化**。能装 Cilium 全栈替换 kube-proxy、能搭 RoCE AI 训练集群、能用 DeepFlow/Hubble 看 L7 流量、能解释 DPU 卸载收益，就具备做底层网络平台的能力。**别只学协议，更要学新范式**——eBPF + 智能网卡 + 服务网格 + AI 网络是未来 10 年战场。
