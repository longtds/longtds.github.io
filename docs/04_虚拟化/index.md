# 04. 虚拟化

> 虚拟化是云原生 / AI / 信创的核心算力底座。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，覆盖从 KVM/qcow2 到 KubeVirt/MIG、从 libvirt 到 OpenStack、从开源到国产化的完整知识链。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入职 1 年内 | Type1/2 / VT-x+EPT / virtio / qcow2 / KVM+libvirt / virt-install / virsh / cloud-init |
| [02_进阶](02_进阶/README.md) | 独立运维 5-50 台 | libvirt XML / 存储池(NFS/LVM/Ceph) / OVS+VLAN+SR-IOV / Proxmox VE 集群 / NUMA+HugePage 调优 / PBS 备份 / Windows VM |
| [03_高级](03_高级/README.md) | 平台架构师 | GPU 虚拟化(MIG/vGPU/SR-IOV) / PCI 直通 / RT/DPDK / 机密计算(SEV-SNP/TDX) / HCI / KubeVirt+Kata+Firecracker / 国产化 |
| [04_最佳实践](04_最佳实践/README.md) | 团队负责人 | 平台选型决策 / 容量水位 / HA+DR / 3-2-1 备份 / 监控告警 / 变更纪律 / 等保合规 / 国产化路线 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | KubeVirt+microVM / GPU 切片标配 / 机密 VM 主流 / DPU 卸载 / OpenStack 回归 / 信创替代 / 5 年趋势 |

## 学习路径

```
入门 (1-3 月)
 └─ 01_基础: 装 KVM + virt-install + bridge + qcow2 + cloud-init + 20 题

进阶 (3-12 月)
 └─ 02_进阶: Proxmox+Ceph 3 节点 + NUMA/HugePage + PBS 备份 + Windows + OVS+VLAN

高级 (1-2 年)
 └─ 03_高级: PCI 直通 GPU / MIG 切片 / RT+DPDK / KubeVirt+Kata / 国产 Hypervisor

工程化 (2-3 年)
 └─ 04_最佳实践: 容量画像 + DR 演练 + 变更纪律 + 等保 3 级 + 国产化路径

展望 (持续)
 └─ 99_发展与展望: KubeVirt + GPU 切片 + 机密计算 + DPU + 信创六条线
```

## 核心判断

```
学习心法:
 1. 生产永远 KVM + libvirt + virtio + qcow2 + bridge
 2. iproute2 (ip/ss) 完全替代 ifconfig/netstat/route
 3. 集群从 3 节点起步：Proxmox VE 是中小首选
 4. NUMA + HugePage + CPU pinning 是大 VM 性能基本盘
 5. 备份不演练 = 没备份
 6. 快照是回滚，不是备份
 7. 容量水位 75%/85%/90% 三色线
 8. K8s 大集群必上 KubeVirt 看 VM
 9. AI 集群必上 MIG / 国产 vGPU
 10. 国产化提前 2-3 月联调

红线:
 CPU 不开 VT / BIOS 没改
 cache=writeback 上生产
 DB VM 超分 1:8
 大 VM 跨 NUMA
 没装 qemu-guest-agent
 嵌套虚拟化跑生产
 快照当备份用
 HA 集群 < 3 节点 / 心跳网混业务
 共享存储无 fence
 备份不验证 / 不异地
 VMware vCSA 不备份
```

## 相关章节

- 配合 [01_服务器](../01_服务器/index.md) 看 CPU/PCIe/IOMMU 硬件
- 配合 [02_Linux](../02_Linux/index.md) 看内核虚拟化栈
- 配合 [03_网络](../03_网络/index.md) 看 OVS / VXLAN / SR-IOV / DPU
- 配合 [05_私有云](../05_私有云/index.md) 看 OpenStack / Ironic / Magnum
- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 KubeVirt / Kata / Harvester
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 GPU 切片 / MIG / GPU Operator
- 配合 [14_安全](../14_安全/index.md) 看机密计算 / 等保合规
- 配合 [16_故障排查](../16_故障排查/index.md) 看 VM 卡顿 / 迁移失败实战
