# 03. 网络

> 网络是云原生 / AI / AIOps 的连接器。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，覆盖从二层抓包到 RoCE/RDMA、从 iptables 到 eBPF/Cilium、从 IPv4 到 HTTP/3、从开源到国产化的完整知识链。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入职 1 年内 | OSI/TCP-IP / 二层 ARP/VLAN / 三层 IP+路由+ICMP / TCP UDP / HTTP DNS SSH / 子网计算 / 抓包入门 |
| [02_进阶](02_进阶/README.md) | 独立运维 5-50 台 | VLAN+Bond / OSPF+BGP / NAT/PAT / iptables+nftables / LVS+Nginx+HAProxy / HTTPS+TLS+国密 / Keepalived VRRP / sysctl 调优 |
| [03_高级](03_高级/README.md) | 平台架构师 | SDN/OVS / VXLAN+Geneve / Cilium+eBPF+XDP / DPDK+SmartNIC+DPU / RoCE+IB+NCCL / Istio ServiceMesh / 高速网络 / 国产化 |
| [04_最佳实践](04_最佳实践/README.md) | 团队负责人 | Spine-Leaf 架构 / 安全基线 / 监控告警 / 排查 SOP / 变更纪律 / WireGuard ZTNA / cert-manager / 混沌工程 / 国产化选型 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | eBPF+DPU+Cilium 三剑客 / AI 网络 RoCE+IB / HTTP/3+PQC / SD-WAN+SASE / 国产化 / 5 年趋势 |

## 学习路径

```
入门 (1-3 月)
 └─ 01_基础: 抓包 + 子网算 + 静态 IP + iptables 基础 + 入门必练 20 题

进阶 (3-12 月)
 └─ 02_进阶: 搭出 LVS+Keepalived+Nginx + nftables ruleset + TLS 1.3 + BBR

高级 (1-2 年)
 └─ 03_高级: Cilium 装满 + Hubble + eBPF + RoCE 调优 + Istio 灰度

工程化 (2-3 年)
 └─ 04_最佳实践: 监控大盘 + 变更纪律 + DR 演练 + 国产化储备

展望 (持续)
 └─ 99_发展与展望: 紧跟 eBPF + DPU + AI 网络 + 国产化
```

## 核心判断

```
学习心法:
 1. 80% 问题用基础工具解决（ip/ss/tcpdump/curl/dig）
 2. ss + tcpdump 比 netstat + 千张图片有用
 3. iproute2 (ip/ss) 完全替代 ifconfig/netstat/route
 4. iptables 写完就该考虑 nftables 改造
 5. K8s 大集群必上 Cilium，不要恋战 kube-proxy
 6. AI 集群网络重在 RoCE/IB + NCCL 调优
 7. 一切配置入 Git → 一切变更 IaC 化
 8. 国产化设备提前 2 个月联调

红线:
 改完 IP 没留 console 直接踢自己 SSH
 iptables 默认 ACCEPT
 Bond 模式 0 没和交换机对齐
 TLS 证书过期没告警
 DNS 单点 / 业务高峰切 DNS
 WAF 未灰度全量拦截
 VPN 单点 / 单机 LB
 大促前升级 / 无回滚预案
```

## 相关章节

- 配合 [01_服务器](../01_服务器/index.md) 看网卡硬件
- 配合 [02_Linux](../02_Linux/index.md) 看内核网络栈
- 配合 [05_私有云](../05_私有云/index.md) / [04_虚拟化](../04_虚拟化/index.md) 看 OVS/VXLAN
- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 CNI / ServiceMesh
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 RoCE / NCCL
- 配合 [14_安全](../14_安全/index.md) 看防火墙 / WAF / DDoS / 国密
- 配合 [16_故障排查](../16_故障排查/index.md) 看网络排查实战
