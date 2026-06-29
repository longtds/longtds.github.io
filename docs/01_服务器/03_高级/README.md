# 高级

> 服务器高级 = **AI 服务器整机架构(HGX H100/B200 + GB200 NVL72) + GPU 互联(NVLink/NVSwitch/InfiniBand) + 整机柜与 OCP + 液冷工程(冷板/浸没) + DPU/IPU 卸载 + CXL Fabric + 信创全栈(鲲鹏/海光/昇腾/飞腾整机) + 多机互联(IB Fabric + Scheduler) + 数据中心选址与电力 + 边缘服务器**。面向 AI 基础设施 / DC 架构师。

## 一、AI 服务器整机架构

### 1.1 NVIDIA HGX 平台

```
HGX H100 / H200 / B200 SXM
  → 8× GPU SXM 基板 (单一 PCB 上)
  → 4× NVSwitch (NVLink 4/5 全互联)
  → 主板独立 (CPU + 内存 + 8× PCIe Gen5 x16 → GPU)
  → 8× IB CX-7/CX-8 (东西向网络)
  → 2× IB Mgmt + 2× 25G/100G (南北向)
  → 6-12 NVMe (本地高速)
  → 12-32 风扇 / 4-6 PSU 3kW

典型规格 (8×H100 SXM5):
  CPU         2× Intel Xeon Platinum 8480+ (56 核) 或 AMD EPYC 9554 (64 核)
  内存        2 TB DDR5-4800 (32× 64GB)
  GPU         8× H100 80GB HBM3 (700W × 8 = 5.6kW)
  NIC         8× IB CX-7 400G (东西) + 2× 25/100G (Mgmt)
  存储        8× NVMe Gen5 7.68TB
  PCIe        Gen5 全速
  电源        6× 3000W (4+2 冗余)
  功耗        10-12 kW
  尺寸        8U
  散热        风冷顶配 + 液冷主推
```

### 1.2 GB200 NVL72 (整机柜) ⭐

```
NVIDIA Grace Blackwell GB200 NVL72:
  72 GPU + 36 Grace CPU (1 整机柜)
  = 18 个 Compute Tray (每 Tray 2 GPU + 1 Grace)
  + 9 NVSwitch Tray (全互联)
  + 液冷 (强制冷板)
  + 整柜 OS / Manager

互联:
  NVLink 5.0: 1.8 TB/s 每 GPU
  NVLink Switch: 跨 Tray 全互联
  ConnectX-8 800G: 跨机柜 (InfiniBand)
  
功耗:
  ~120 kW / 机柜 (传统机柜的 5-10 倍)
  
应用:
  - 万亿参数大模型训练
  - 单一"超级 GPU"(72 卡当一个)
  - 配 GB200 NVL576 (8 柜 = 576 GPU 全互联)

国产对标:
  华为 Atlas 900 SuperCluster
  寒武纪 玄思 / 思元集群
  海光 DCU 集群
```

### 1.3 国产 AI 整机

```
华为 Atlas 800:
  - 8× Ascend 910B (256TFlops FP16/卡, 64GB HBM)
  - 鲲鹏 920 (双路)
  - HCCN (华为自研, 类 NVLink)
  - openEuler + MindSpore

浪潮 NF5688G7:
  - 8× H100 / H200 SXM
  - Intel/AMD 双路
  - 国内 H100 主供给商

中科曙光 X785-G30:
  - 海光 C86 + DCU Z100
  - 国产 ROCm 衍生栈

超聚变 FusionServer G5500 V7:
  - 8× H100 / H200 / B100/B200
  - 鲲鹏 / Intel / AMD 多平台

新华三 R5350 G6 / R5500 G6:
  - 8× H100 / H200
  - 多平台
```

## 二、GPU 互联

### 2.1 NVLink / NVSwitch

```
NVLink 演进:
  NVLink 1.0 (Pascal P100):  20 GB/s × 4 link
  NVLink 2.0 (Volta V100):    25 GB/s × 6 link = 150 GB/s
  NVLink 3.0 (Ampere A100):   25 GB/s × 12 link = 300 GB/s
  NVLink 4.0 (Hopper H100):   25 GB/s × 18 link = 450 GB/s (单向)
  NVLink 5.0 (Blackwell B200): 50 GB/s × 18 link = 900 GB/s (单向)

NVSwitch:
  - 全互联交换芯片
  - HGX 8 卡: 4 NVSwitch (节点内全互联)
  - NVL72: 9 NVSwitch Tray (机柜级全互联)

测试:
  nvidia-smi nvlink --status                       # 链路状态
  nvidia-smi topo -m                                # 拓扑矩阵
  ./nccl-tests/build/all_reduce_perf -b 8 -e 8G -f 2 -g 8

期望带宽:
  H100 8 卡 NVLink AllReduce: ~480 GB/s (busBW)
  B200 8 卡: ~900 GB/s
```

### 2.2 InfiniBand Fabric

```
拓扑:
  Rail-Optimized (Fat-Tree):
    每 GPU 一张 IB (8 GPU → 8 IB)
    Leaf → Spine → Super-Spine
    无阻塞 1:1
    
    8 GPU × 400G = 3.2 Tbps 出口
    
工具:
  ibstat / ibstatus                                # 端口状态
  ibnetdiscover                                    # 拓扑发现
  ibdiagnet                                        # 健康检查 ⭐
  perftest:
    ib_send_bw -d mlx5_0 <peer>                    # 单端口带宽
    ib_write_lat                                    # 延迟

Subnet Manager:
  OpenSM (开源)
  UFM (NVIDIA Unified Fabric Manager) ⭐

GPUDirect RDMA:
  GPU 直接读写远端内存 (绕过 CPU)
  modprobe nvidia_peermem
  详见 03 网络 / 11 AI 基础设施
```

### 2.3 PCIe Switch

```
PCIe Gen5 Switch (Broadcom PEX 89000 系列):
  扩展 PCIe lane (1 上行 → 多下行)
  GPU-to-GPU P2P (节点内, 不经 CPU)
  
用途:
  - 多 GPU 互联 (RTX/L40S 等无 NVLink 卡)
  - NVMe 扩展 (24+ U.2)
  - 灵活拓扑

测试:
  lspci -tvvv                                      # 完整树
  lspci -vvv | grep -E "LnkCap|LnkSta"             # 链路速率
```

## 三、整机柜 + OCP

### 3.1 Open Compute Project

```
OCP = Open Compute Project (Facebook 2011 发起)
目标: 数据中心硬件开源标准

Open Rack v3:
  宽 21 英寸 (vs 19 英寸传统)
  深 1067mm
  48V DC 直流供电 ⭐ (vs 12V/AC)
  高密度 48 OU (Open U)
  统一前进风, 后出风 + 后门冷却

整机柜组件:
  Power Shelf: 共享电源 (12-30kW)
  Bus Bar: 12V/48V 直流母线
  Compute Sled: 服务器节点 (1-2 OU)
  Storage Sled: 存储节点
  Network Switch: 顶置

国内变种:
  阿里 天蝎 3.0 (类 OCP, 12V)
  字节 / 腾讯 自研整机柜
  华为 FusionPoD (整机柜 + 液冷 + 模块化)
```

### 3.2 整机柜优势

```
能效:
  AC→DC 一次转换 (传统每节点一次 → 整柜共享)
  PSU 利用率 80%+ (传统 50%)
  PUE 改善 0.1-0.2

成本:
  共享电源 + 共享散热
  10-20% TCO 降低

运维:
  统一管理 (BMC 聚合)
  快速上下架
  线缆减少 (共享背板)

热设计:
  整柜液冷友好 (统一 manifold)
  冷热通道隔离 (整柜级)
```

## 四、液冷工程

### 4.1 冷板液冷 (Cold Plate)

```
原理:
  CPU/GPU 上加冷板 (液体接触)
  循环泵 → 冷板 → 热交换器 → 室外
  
覆盖:
  CPU + GPU + VRM (50-70% 热)
  风扇辅助内存 + 磁盘 + 主板

液体:
  PG25 (乙二醇 25%)
  纯水 + 抑制剂
  非导电液 (Galden 等, 贵)

部件:
  ☐ 冷板 (CPU/GPU 定制)
  ☐ Manifold (整机柜分水)
  ☐ Quick Connector (热插)
  ☐ CDU (Coolant Distribution Unit)
  ☐ 泵 + 过滤 + 监控
  ☐ 二次环路 → 一次环路 → 室外冷却塔

测试 (见 18 高级):
  ☐ 流量 + 压力 + 温度
  ☐ 漏液检测 (DCIM)
  ☐ 长期腐蚀 + 微生物
  ☐ 维护流程 (Quick Disconnect)
```

### 4.2 浸没液冷 (Immersion)

```
单相 (Single-Phase):
  矿物油 / 合成油
  整机泡液
  泵循环
  PUE 1.05-1.1

两相 (Two-Phase):
  氟化液 (3M Novec) → 已 EOL (环保)
  低沸点液体沸腾相变
  PUE 1.02-1.05
  3M 退出后产业链调整中

特殊处理:
  ☐ 磁盘机械件 (HDD 不行, SSD/NVMe OK)
  ☐ 光纤密封改造
  ☐ 主板涂层 (部分元件)
  ☐ 维护需排液 (麻烦)

案例:
  阿里 仁和数据中心 (单相浸没)
  字节 海南数据中心
  Microsoft 海底数据中心 (Project Natick)
```

### 4.3 后门冷却

```
Rear Door Heat Exchanger (RDHx):
  机柜后门加水冷盘管
  改造友好 (旧机房升级)
  PUE 1.2-1.3
  支持 30-50 kW/机柜
  
适用:
  - 旧机房改造
  - 不能装液冷服务器
  - 边缘 / 临时
```

## 五、DPU / IPU 卸载

```
DPU = Data Processing Unit
作用: 卸载 CPU 上的网络/存储/安全/虚拟化

主流:
  NVIDIA BlueField-3 ⭐
    - 400G ConnectX-7 + ARM 16 core + DDR5
    - DOCA SDK
    - K8s + Cloud Native
  Intel IPU (Mount Evans / Oak Springs Canyon)
    - 200G + Xeon-D
  AMD Pensando (DSC2/DSC3)
    - 100/200G + ARM
    - VMware / Oracle 主推
  阿里 神龙 CIPU
  AWS Nitro
  字节 Bali / 腾讯 自研

应用:
  ☐ vSwitch 卸载 (OVS-DPDK → BlueField)
  ☐ NVMe-oF Target (存储分离)
  ☐ TLS / IPsec 卸载
  ☐ K8s CNI 加速
  ☐ 防火墙 / 微分段
  ☐ HCI (超融合)

测试:
  perftest (DPU 流量)
  DOCA 工具集 (BlueField)
  ovs-dpctl + ofctl
```

## 六、CXL Fabric

```
CXL 3.0+:
  Fabric Manager
  跨节点内存池化
  Type 2 (GPU/FPGA) + Type 3 (Mem)
  P2P 跨设备
  
应用 (2025-2028):
  - 内存解耦 (Disaggregated Memory)
  - 大模型 KV-Cache 卸载
  - 数据库共享内存
  - HCI 资源池

厂商:
  Intel Granite Rapids (CXL 2.0)
  AMD Turin (CXL 2.0)
  Samsung / SK Hynix / Micron (CXL 内存模组)
  Astera Labs / Marvell (CXL Switch)

测试:
  cxl-cli (Linux 6.x)
  Intel MLC (CXL 模式)
  fabric manager API
```

## 七、信创全栈整机

### 7.1 华为 TaiShan + Atlas

```
TaiShan 200 / 220 (鲲鹏 920):
  双路 64×2 = 128 核
  DDR4-3200 满通道
  iBMC + openEuler + 麒麟

Atlas 800 (训练 / 推理):
  Atlas 800 9000   8× Ascend 910B 训练
  Atlas 800 3000   16× Ascend 310 推理
  MindSpore 框架 (类 PyTorch)

FusionServer (超聚变):
  Intel/AMD/鲲鹏 多平台
  G5500 V7  AI 8 卡
  X86 + ARM 通吃
```

### 7.2 海光 + 中科曙光

```
海光 C86 系列 (Zen 衍生):
  C86 1 (Zen1)
  C86 2 (Zen2)
  C86 3 (Zen2+)
  C86 4 (Zen4 衍生, 2024+)

中科曙光:
  I620-G30: 双路 C86, 通用
  I8000:   AI 训练 8× DCU
  天阔系列: HPC

ROCm 国产分支:
  DCU 工具链 (类 NVIDIA CUDA)
  PaddlePaddle / TensorFlow / PyTorch 适配
```

### 7.3 浪潮 + 飞腾 + 长城

```
浪潮:
  - NF系列 (X86 双路)
  - K1 Power (Power 架构, 已淡)
  - 鲲鹏 / 海光 服务器 (多平台)
  - NE5260 (AI 推理)
  - NF5468 (8 卡 GPU)

飞腾整机:
  长城 / 中科可控 / 中兴 (飞腾 FT-2500/FT-D2000)
  UOS + 麒麟
  军工 / 政府

龙芯整机:
  长城 / 国资委 (龙芯 3C5000/3D5000)
  自主指令集 (LoongArch)
```

### 7.4 国产 NPU 矩阵

| 厂商 | 产品 | 算力 (FP16) | 互联 |
|:---|:---|:---|:---|
| 华为昇腾 | 910B / 910C | 256 / 320 TFlops | HCCN |
| 海光 | DCU Z100 / K100 | 200+ TFlops | xGMI |
| 寒武纪 | 思元 590 | 192 TFlops | MLU-Link |
| 摩尔线程 | MTT S4000 | - | MTLink |
| 燧原 | 邃思 2.0 / i20 | - | - |
| 天数智芯 | BI-V100 | - | - |
| 壁仞 | BR104 | 256 TFlops | BLink |
| 沐曦 | C500 | - | - |

## 八、多机互联 + 调度

### 8.1 IB Fabric 设计

```
Rail-Optimized Fat-Tree (AI 主流):
  Leaf  (每机柜 1 个)
  Spine (跨机柜全互联)
  Super-Spine (跨集群)

带宽:
  每 GPU 1 张 IB (400G)
  8 GPU 节点 = 3.2 Tbps 上行
  无阻塞 1:1 (Spine 满速)

工具:
  ibnetdiscover
  ibdiagnet ⭐
  UFM (Unified Fabric Manager)
  Subnet Manager (OpenSM / UFM)
```

### 8.2 调度

```
SLURM:        HPC 标杆
PBS / Torque:  老 HPC
Kubernetes:    云原生 ⭐
  + Volcano / Kueue / Run:ai (AI 调度)
  + GPU Operator + Network Operator + GPUDirect

NVIDIA Base Command:
  企业级 AI Platform
  
Topology-aware:
  K8s + NRI / Topology Manager
  绑 GPU + NIC + NVMe 同 NUMA
```

## 九、数据中心选址 + 电力

```
选址要素:
  ☐ 电力充足 (10-100MW)
  ☐ 网络互联 (骨干 + 海缆 + 多运营商)
  ☐ 自然冷 (高纬度 / 高海拔)
  ☐ 水源 (冷却塔 / 浸没)
  ☐ 政策 (税收 / 备案 / 等保)
  ☐ 抗灾 (地震 / 洪水 / 雷击)
  ☐ 用地 (面积 + 地价)

中国典型:
  北方:  乌兰察布 (内蒙古) / 张家口 (河北) - 风电 + 冷
  西部:  贵安 / 庆阳 / 宁夏中卫 - 水电 + 冷
  长三角: 江苏 / 浙江 / 上海 - 业务近, 但电力紧
  粤港澳: 韶关 / 清远 / 中山 - 业务近
  海南:  海底 (字节)

电力等级:
  小型     1-5 MW
  中型     5-20 MW
  大型     20-100 MW
  超大     100MW+ (Hyperscale)
```

## 十、边缘服务器

```
特征:
  ☐ 小型化 (1U / 短深度)
  ☐ 加固 (宽温 / 防尘 / 抗震)
  ☐ 高可靠 (双 PSU + 远程管理)
  ☐ 多接口 (5G / WiFi6 / RS232 / GPIO)
  ☐ 加速器 (Jetson / 推理 NPU)

典型场景:
  5G MEC (运营商边缘)
  CDN
  工业现场 (机器视觉 / IoT 网关)
  零售 / 安防
  车联网 (V2X)

代表机型:
  NVIDIA Jetson AGX Orin / Thor
  Intel NUC / Aaeon
  浪潮 NE5260 (边缘 AI)
  研华 / 凌华 加固机
  ZTE / 华为 边缘节点

国家政策:
  东数西算 (西部 DC + 东部边缘)
  5G + 工业互联网
```

## 十一、Checklist (高级)

```
AI 整机:
☐ HGX H100/H200/B100/B200 SXM 架构
☐ GB200 NVL72 整机柜 (72 GPU + 36 Grace)
☐ 国产 (Atlas 800 / 浪潮 NF5688 / 曙光 X785)
☐ 8 GPU + 8 IB + NVLink 拓扑

GPU 互联:
☐ NVLink 5.0 (900 GB/s)
☐ NVSwitch 全互联
☐ IB Fat-Tree Rail-Optimized
☐ GPUDirect RDMA
☐ ibdiagnet + UFM

整机柜:
☐ OCP Open Rack v3 (21" + 48V DC)
☐ 阿里天蝎 + 字节 / 腾讯自研
☐ 共享 PSU + 母线 + 后门冷

液冷:
☐ 冷板 (CPU+GPU+VRM, 主流)
☐ 浸没 (单相主流, 两相 EOL)
☐ 后门冷却 (改造)
☐ CDU + Manifold + Quick Connect

DPU/IPU:
☐ BlueField-3 400G + ARM 16 核
☐ Intel IPU / AMD Pensando
☐ 阿里 CIPU / 字节 / 腾讯

CXL:
☐ Type 3 内存扩展
☐ Type 2 GPU/FPGA
☐ Fabric 跨节点 (3.0+)

信创:
☐ 鲲鹏 + 昇腾 (Atlas 800)
☐ 海光 + DCU (中科曙光)
☐ 飞腾 + 龙芯整机
☐ 国产 NPU 8 家矩阵

互联:
☐ IB Fabric Fat-Tree 设计
☐ SLURM / K8s + Volcano / Run:ai
☐ Topology-aware 调度

DC:
☐ 选址 (电力 + 网络 + 冷 + 政策)
☐ 100MW+ Hyperscale
☐ 东数西算

边缘:
☐ Jetson Orin / Thor
☐ 5G MEC / 工业 / 车联网
```

## 十二、推荐栈 (高级)

```
AI 整机:     NVIDIA HGX H100/H200/B200/GB200 NVL72 ⭐ + 浪潮/超聚变 / 华为 Atlas 800
互联:        NVLink 5.0 + NVSwitch + IB CX-7/CX-8 + UFM + ibdiagnet
整机柜:      OCP Open Rack v3 (48V) + 阿里天蝎 + 华为 FusionPoD
液冷:        冷板 (主流) + 浸没单相 (试点) + RDHx (改造)
DPU:        BlueField-3 ⭐ + Intel IPU + AMD Pensando + 阿里 CIPU + AWS Nitro
CXL:        Granite Rapids + EPYC Turin + Samsung/Micron CXL 内存 + cxl-cli
信创:        华为 Atlas 800 / 浪潮 NF5688 / 曙光 X785 / 超聚变 G5500 ⭐
调度:        SLURM + Kubernetes + Volcano + Run:ai + Topology Manager
管理:        Redfish API + 厂商 BMC (iDRAC/iLO/XCC/iBMC/ISBMC)
监控:        Prometheus + DCGM exporter + IPMI exporter + Grafana + DCIM
DC 设计:    Tier 3+ + 100MW + 自然冷 + 双路市电 + 柴发 + UPS
边缘:        Jetson Orin/Thor + 5G MEC + 加固机
```

> 📖 **核心判断**：服务器高级 = **AI 整机(HGX 8 卡 H100/B200 + GB200 NVL72) + GPU 互联(NVLink 5 + NVSwitch + IB Fat-Tree) + 整机柜与 OCP(48V DC + 共享 PSU) + 液冷工程(冷板 + 浸没 + RDHx) + DPU 卸载(BlueField-3) + CXL Fabric + 信创全栈(Atlas/曙光/浪潮/超聚变 + 8 家 NPU) + 多机调度(SLURM + K8s + Volcano) + DC 设计(选址 + 电力) + 边缘**。能给数据中心做 AI 集群整体架构选型、液冷部署、整机柜设计、信创替代落地, 就具备 AI 基础设施架构师 / 数据中心架构师能力。**口诀: 整机选 8 卡 NVLink, 互联选 IB Fat-Tree, 散热选液冷, 网络选 BlueField, 内存看 CXL, 国产替代分平台。运维/测试细节参考 [18 硬件测试 03 高级](../../18_硬件测试/03_高级/README.md)。**
