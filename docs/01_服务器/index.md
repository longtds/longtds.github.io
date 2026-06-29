# 01. 服务器

> 服务器是数据中心的最小可寻址单元。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦 "认得清、调得动、选得对、买得值、跟得上未来"。硬件测试 / 烤机 / 故障定位 详见 [18. 硬件测试](../18_硬件测试/index.md)。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入门 | 服务器分类(机架/刀片/塔式/整机柜) + 5 大件(CPU/内存/磁盘/网卡/电源) + 物理拓扑(主板/PCIe/NUMA) + 散热(风冷/液冷) + 机柜上下架 + 数据中心 ABC(Tier/UPS/温湿度) + 厂商生态(国外四大 + 国产四大) |
| [02_进阶](02_进阶/README.md) | 资深运维 | CPU 深度(Granite Rapids/EPYC Turin/鲲鹏 + AMX/SVE + NUMA 绑核) + 内存(DDR5/MRDIMM/CXL/HBM) + 存储(NVMe 队列/RAID/分层) + 网络(SR-IOV/DPDK/RDMA/Offload) + BMC(Redfish/IPMI) + 固件层次 + GPU 入门(H100/SXM/NVLink/CUDA) |
| [03_高级](03_高级/README.md) | AI 基础设施架构师 | AI 整机(HGX 8 卡 + GB200 NVL72) + GPU 互联(NVLink 5/NVSwitch/IB Fat-Tree) + OCP 整机柜(48V DC) + 液冷工程(冷板/浸没/RDHx) + DPU(BlueField-3) + CXL Fabric + 信创全栈(Atlas/曙光/浪潮) + 多机调度(SLURM+K8s+Volcano) + DC 选址与电力 |
| [04_最佳实践](04_最佳实践/README.md) | IT 基础设施总监 | 10 金标 + 选型决策树(通用/DB/AI/存储/边缘) + BOM 与 TCO 5 年模型 + 厂商管理(RFP/SLA/多家) + 生命周期管理 + 多平台并存 + 国产渐进 + CapEx vs OpEx + 双碳 ESG + 团队组织 KPI |
| [99_发展与展望](99_发展与展望.md) | 所有人 | AI 算力爆炸(B200/GB300/Rubin) + 整机柜(NVL72/NVL576) + 液冷主流 + CXL Fabric + DPU 普及 + 800G/1.6T CPO + 国产化全栈 + Confidential + Sovereign + Green DC + AIOps + ARM/RISC-V + 25 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
  └─ 01_基础: 分类 + 5 大件 + NUMA 拓扑 + 机柜上架 + 厂商生态

进阶（3-12 月）
  └─ 02_进阶: CPU/内存/存储/网络深度调优 + BMC Redfish + GPU 入门

高级（1-2 年）
  └─ 03_高级: AI 整机 + GPU 互联 + 整机柜 + 液冷 + DPU + CXL + 信创

工程化（2-3 年）
  └─ 04_最佳实践: 选型决策 + TCO + RFP + 生命周期 + 多平台 + 国产替代 + 团队

展望（持续）
  └─ 99_发展与展望: B200/GB300/Rubin + 液冷 + CXL + DPU + 信创 + Sovereign + Green
```

## 核心判断

```
心法:
  1. 业务先于硬件 (SLA/性能/容量 → 选型)
  2. TCO 5 年思维 (不光看采购价)
  3. 多厂商策略 (2-3 家, 避免锁定)
  4. 平台标准化 (3-5 机型, 控 SKU)
  5. 满通道内存 + NVMe IRQ 亲和 + NUMA 绑核
  6. Redfish API 自动化 (替代 IPMI 2.0)
  7. AI 服务器 = HGX 8 卡 + NVLink + IB + 液冷 + DCGM
  8. 整机柜 NVL72 是 AI 分水岭
  9. 国产渐进 (试点 → 主力, 别一刀切)
  10. 不学 AI + 液冷 + 信创的硬件工程师 5 年边缘化

红线:
  ❌ 唯采购价低 (忽略 TCO + 服务)
  ❌ 单厂商绑定 (议价权 + 风险)
  ❌ 跳过 72h 烤机直接上架 (见 18)
  ❌ NUMA 不绑核 + 内存不平衡
  ❌ NVMe 用 SATA 兼容模式 (浪费)
  ❌ AI 服务器风冷强上 H200/B200 (温度爆)
  ❌ 整机柜不留液冷接口 (后期改造贵)
  ❌ 信创一刀切 (业务挂)
  ❌ 默认 BMC 密码不改 (admin/admin)
  ❌ 不做寿命管理 (SSD/GPU)
```

## 相关章节

- 配合 [02_Linux](../02_Linux/index.md) 看 OS 层工具调用
- 配合 [03_网络](../03_网络/index.md) 看高速 NIC / RDMA / IB Fabric
- 配合 [04_虚拟化](../04_虚拟化/index.md) 看 Hypervisor 与硬件直通
- 配合 [11_AI 基础设施](../11_AI基础设施/index.md) 看 GPU 调度与推理引擎
- 配合 [12_AIOps](../12_AIOps/index.md) 看硬件预测性维护
- 配合 [16_故障排查](../16_故障排查/index.md) 看硬件故障 RCA
- 配合 [17_软件测试](../17_测试/index.md) 看软件层质量
- 配合 [18_硬件测试](../18_硬件测试/index.md) 看 ⭐ **硬件测试 / 烤机 / 固件升级 / PXE 自动化全流程**
