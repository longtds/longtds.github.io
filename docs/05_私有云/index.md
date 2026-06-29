# 05. 私有云

> 私有云是企业 IT 基础设施 + 信创 + 主权云的核心载体。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦 OpenStack 全家桶、Kolla-Ansible 部署、HA 架构、OVN + Ceph、Cluster API + KubeVirt 共生、国产化全栈、机密计算与 LLM-OPS 八条主线。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入职 1 年内 | 公私混合云 / IaaS-PaaS-SaaS / 主流平台选型 / OpenStack 5 大组件(Keystone/Glance/Nova/Neutron/Cinder) / DevStack & PackStack 上手 / 国产化全景 + 20 题 |
| [02_进阶](02_进阶/README.md) | 独立部署 50-500 节点 | Kolla-Ansible 多节点 / MariaDB Galera + RabbitMQ Quorum + HAProxy HA / OVN 深度 / Cinder+Ceph 多 backend / Octavia LBaaS / Magnum / Ironic / Heat+Terraform / Skyline+Prometheus |
| [03_高级](03_高级/README.md) | 平台架构师 | Cells V2 / Region/AZ / OVS-DPDK+SR-IOV NFV / GPU+Cyborg / Ceph 调优 / Cluster API / OpenStack+K8s 共生 / SEV-SNP/TDX/海光 CSV 机密计算 / GitOps / LLM-OPS / 国产化深度 |
| [04_最佳实践](04_最佳实践/README.md) | 团队负责人 | 平台选型决策 / 容量画像 / 多租户配额 / HA+DR+双活 / 3-2-1 备份 / Prometheus 告警 / SLURP 升级 / 等保+国密 / FinOps / 自服务门户 / 国产化路径 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | OpenStack 价值回归 / 信创主权云 / K8s 共生 / AI 算力 / 边缘云 / 机密计算 / LLM-OPS / 15 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
 └─ 01_基础: 装 DevStack/Kolla 单节点 + CLI 一气呵成创建 VM+卷+网络 + 20 题

进阶（3-12 月）
 └─ 02_进阶: 3 控制+5 计算+3 存储 Kolla 多节点 + Galera/RabbitMQ HA + OVN + Cinder+Ceph + Octavia + Magnum + Heat/Terraform

高级（1-2 年）
 └─ 03_高级: Cells V2 + DPDK/SR-IOV + GPU 直通+MIG + Cluster API + 机密 VM + GitOps + 国产化

工程化（2-3 年）
 └─ 04_最佳实践: 容量画像 + 配额模板 + DR 演练 + SLURP 升级 + 等保 3 级 + 国产化路径 + 自服务门户

展望（持续）
 └─ 99_发展与展望: OpenStack 回归 + 信创 + K8s 共生 + AI 算力 + 边缘 + 机密计算 + LLM-OPS 八条主线
```

## 核心判断

```
心法:
 1. 私有云 ≠ 一堆 VM，而是计算+网络+存储+身份+编排+计费+合规一体
 2. 生产 OpenStack 永远 Kolla-Ansible + OVN + Ceph + Galera + RabbitMQ + HAProxy
 3. SLURP LTS（Antelope/Caracal/Epoxy）跳跃升级才稳
 4. Cluster API 取代 Magnum，是 K8s on OpenStack 新主流
 5. OpenStack 与 K8s 不是对抗，是共生
 6. 中大型私有云必须信创预案
 7. 机密计算（SEV-SNP/TDX/海光 CSV）2026 已不是 PoC
 8. Cells V2 让单 Region 撑 10w VM
 9. LLM-OPS 私有云 2027 成标配
 10. 边缘云成主流第三形态

红线:
 单 inventory 跑 controller+compute
 没规划 5 网（mgmt/tunnel/ext/storage/bmc）
 Galera 心跳网与业务网混
 控制节点 < 3
 一律 file 后端 Glance
 Ceph 副本 < 3 / 故障域 < rack
 Cinder 单 backend 包打天下
 大版本跳跃升级（不走 SLURP）
 Magnum 老 K8s 跑生产
 备份不验证 / 不异地
 没接 SSO + MFA
 信创不提前压测
```

## 相关章节

- 配合 [01_服务器](../01_服务器/index.md) 看 CPU/PCIe/IOMMU/Redfish 硬件
- 配合 [02_Linux](../02_Linux/index.md) 看内核虚拟化栈
- 配合 [03_网络](../03_网络/index.md) 看 OVS / OVN / VXLAN / SR-IOV / DPU
- 配合 [04_虚拟化](../04_虚拟化/index.md) 看 KVM/libvirt/HCI/KubeVirt
- 配合 [06_Docker](../06_Docker/index.md) 看容器运行时
- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 Cluster API / KubeVirt / Karmada
- 配合 [08_DevOps](../08_DevOps/index.md) 看 GitOps / Terraform / ArgoCD
- 配合 [09_中间件](../09_中间件/index.md) 看 Ceph / RabbitMQ / MariaDB
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 GPU 切片 / vLLM / RoCE
- 配合 [12_AIOps](../12_AIOps/index.md) 看 LLM-OPS / 智能运维
- 配合 [13_认证与SSO](../13_认证与SSO/index.md) 看 Keystone+Keycloak SSO
- 配合 [14_安全](../14_安全/index.md) 看机密计算 / 等保 / 国密 / 数据安全法
- 配合 [16_故障排查](../16_故障排查/index.md) 看 OpenStack VM/卷/网络 排障实战
