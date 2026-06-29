# 18. 硬件测试

> 服务器硬件测试 = 数据中心硬件交付的兜底。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，覆盖组件检查 + 固件升级 + 压力测试 + 烤机 + PXE 自动化 + AI 服务器 + HPC 集群 + 信创全栈 + DCIM + RMA 全生命周期。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入门 | 5 件套(dmidecode/lshw/smartctl/ipmitool/lspci) + CPU/内存/磁盘/NIC/BMC 单点 + SMART 关键字段 + IPMI/Redfish 入门 + 基础压测(stress-ng/memtester/fio/iperf3) + 入场清单 |
| [02_进阶](02_进阶/README.md) | 资深测试工程师 | RAID(storcli/perccli/ssacli) + 高速 NIC(Mellanox MFT) + NVMe 深度 + GPU(DCGM/Xid) + 厂商 BMC(OneCli/RACADM/iLO/iBMC) + Linpack/MLC/STREAM/gpu-burn + RAS daemon + Python/Ansible 自动化 |
| [03_高级](03_高级/README.md) | 测试架构师 | 固件全栈(BIOS/BMC/RAID/NIC/NVMe/GPU) + 72h 烤机(5 并发) + PXE 自动化(iPXE/Foreman/MAAS/Ansible/NetBox) + AI 服务器(H100/HGX 8 卡 + NCCL + GDR) + HPC + 信创(鲲鹏/海光/昇腾) + DCIM |
| [04_最佳实践](04_最佳实践/README.md) | 数据中心运营总监 | 12 金标 + 入场 SOP + 固件基线管理 + RAS 三件套 + RMA 流程 + 备件 5-10% + NetBox CMDB + Sanitize 数据擦除 + DC 现场作业 + 容量寿命 + 国产合规 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | AI 算力爆炸(B200/GB300/Rubin) + 整机柜(NVL72) + 液冷主流 + 国产化全栈 + CXL + DPU + 800G CPO + Confidential Computing + Sovereign + Green DC + AIOps + 24 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
 └─ 01_基础: 5 件套 + SMART + IPMI + 基础压测

进阶（3-12 月）
 └─ 02_进阶: RAID + Mellanox + NVMe + DCGM + 厂商 BMC + Linpack + RAS

高级（1-2 年）
 └─ 03_高级: 固件全栈 + 72h 烤机 + PXE 流水线 + AI 服务器 + 信创

工程化（2-3 年）
 └─ 04_最佳实践: SOP + 基线 + CMDB + RMA + 备件 + 合规

展望（持续）
 └─ 99_发展与展望: GB300/Rubin + 液冷 + 信创 + CXL + DPU + AIOps
```

## 核心判断

```
心法:
 1. 硬件测试 = 早发现问题, 别等生产挂
 2. 72h 烤机是验收红线
 3. 固件基线管理 + 灰度发布
 4. RAS 三件套持续监控 (rasdaemon + mcelog + edac)
 5. PXE 自动化是规模化前提
 6. CMDB 全量入库 (NetBox)
 7. 备件 5-10% 是 SLA 基础
 8. 数据擦除 + EOL 合规
 9. 国产化是央企必修
 10. AI 服务器测试是未来 5 年最大机遇
 11. 液冷是分水岭 (AI 100%)
 12. 不学 AI + 信创 + AIOps 的硬件工程师 5 年内边缘化

红线:
 跳过 72h 烤机直接上架
 升级期间双 PSU 同时拔
 默认密码不改 (admin/admin)
 GPU VBIOS 不备份就刷
 NVMe FW commit 不备份数据
 Sanitize 不验证就退役
 ECC UE 不立刻处置
 DCGM diag 不跑就上线 AI 服务器
 无 CMDB / 无监控 / 无告警的"裸跑"
 信创认证不验证就采购
```

## 相关章节

- 配合 [01_服务器](../01_服务器/index.md) 看硬件基础
- 配合 [02_Linux](../02_Linux/index.md) 看 OS 层工具
- 配合 [04_虚拟化](../04_虚拟化/index.md) 看 Hypervisor 层硬件
- 配合 [11_AI 基础设施](../11_AI基础设施/index.md) 看 H100/HGX/NCCL 调度
- 配合 [12_AIOps](../12_AIOps/index.md) 看硬件预测 + AIOps
- 配合 [16_故障排查](../16_故障排查/index.md) 看硬件故障 RCA
- 配合 [17_测试](../17_测试/index.md) 看软件测试体系
