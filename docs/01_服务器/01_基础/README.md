# 基础

> 服务器基础 = **服务器分类(机架/刀片/塔式/整机柜) + 5 大件(CPU/内存/磁盘/网卡/电源) + 物理拓扑(主板/PCIe/NUMA) + 散热(风冷/液冷) + 上下架认知 + 数据中心 ABC(机柜/PDU/UPS/温湿度) + 厂商生态(国外四大 + 国产四大)**。面向从笔记本/桌面 PC 转入数据中心的工程师入门。

## 一、服务器分类

```
按形态:
  机架式 (1U/2U/4U/8U)        ⭐ 数据中心主流, 占 80%+
  刀片式 (Blade Server)        高密度, 共享背板 (浪潮 / HPE C7000 / 华为 E9000)
  塔式 (Tower)                 SOHO / 分支机构
  整机柜 (Rack-Scale)          AI / 云原生 (OCP / GB200 NVL72) ⭐
  边缘 / 微型 (Edge)           5G / IoT / 工业现场

按用途:
  通用计算                     Web / 应用 / 微服务 (2U 双路 + 中等内存)
  数据库 / 存储                 (大内存 + NVMe + RAID)
  AI 训练 / 推理                (8 卡 GPU + NVLink + IB)
  HPC                          (多核 + IB + 并行存储)
  大数据 (Hadoop/Spark)         (中等 CPU + 大量 HDD + 多网卡)
  分布式存储 (Ceph)             (CPU 适中 + 多盘位 + 双 SSD 缓存)

按市场:
  通用品牌                     Lenovo / Dell / HPE / Supermicro
  国产                         华为/超聚变 / 浪潮 / 中科曙光 / 新华三 / 长城
  自研 (OCP-like)              阿里天蝎 / 字节 / 腾讯 / 百度
```

## 二、5 大件认知

### 2.1 CPU

```
核心参数:
  ☐ 厂商架构  Intel x86 / AMD x86 / ARM (鲲鹏/AmpereOne) / LoongArch (龙芯)
  ☐ 代号      Intel Sapphire Rapids / Emerald / Granite Rapids
              AMD Genoa / Bergamo / Turin
              鲲鹏 920 / 950
  ☐ 核数      8 / 16 / 32 / 64 / 96 / 128+ (AMD EPYC Turin 192 核 + HT)
  ☐ 主频      2.0-3.5 GHz (基础) + Turbo 3.8-5.0 GHz
  ☐ 指令集    SSE / AVX2 / AVX-512 / VNNI / AMX (AI 加速)
  ☐ TDP       150-400W (单 CPU)
  ☐ 缓存      L1/L2/L3, 大缓存 (EPYC 384MB+)
  ☐ 内存通道  6 / 8 / 12 / 16 通道
  ☐ PCIe      Gen 4 / 5 / 6, 64-128 lane

双路 (2-Socket) ⭐ 数据中心主流
  - 2 颗 CPU 通过 UPI / Infinity Fabric 互联
  - 跨 NUMA 访问有延迟
  - 高可用 (单颗故障可降级)

NUMA 拓扑:
  Socket0: CPU0 + 内存通道 0-7 + PCIe 0-63 (Node 0)
  Socket1: CPU1 + 内存通道 8-15 + PCIe 64-127 (Node 1)
  → 应用要 NUMA-aware (绑核)
```

### 2.2 内存

```
类型:
  DDR4-2133/2400/2666/2933/3200      上一代主流 (老服务器)
  DDR5-4800/5600/6400 ⭐              当前主流 (Sapphire Rapids+, EPYC Genoa+)
  HBM (片上, GPU 用)                 H100 80GB HBM3, B200 192GB HBM3e

服务器内存特征:
  ☐ ECC ⭐                  Error-Correcting Code (服务器必)
  ☐ RDIMM / LRDIMM        寄存器 / 负载缓冲 (容量大)
  ☐ NVDIMM (持久内存)      Optane (已停产) / CXL-Mem
  ☐ 单条容量              16/32/64/128/256/512GB
  ☐ 通道数 ⭐              8/12/16 通道 (满插 = 满带宽)
  ☐ 速率                  与 CPU 配 (DDR5 4800 / 5600 / 6400)

性能影响:
  - 通道不平衡 → 性能 -30%
  - 单条多 Rank → 兼容性慎
  - DDR5 ECC = On-die + System (双保险)
```

### 2.3 磁盘 / 存储

```
分类:
  HDD                     7200 rpm, 4-30TB, 顺序好 / 随机差
  SATA SSD                500MB/s, 入门级
  SAS SSD                 1.2GB/s, 双端口高可用
  NVMe SSD (U.2/U.3)      3-7GB/s, 数据中心主流 ⭐ (PCIe Gen4/5)
  NVMe (E1.S/E3.S)        EDSFF, 新规范, 散热好
  M.2 NVMe                小型化 (开机/缓存盘, 不推荐企业生产)

接口/规范:
  ☐ SAS 12G/24G          老但稳, 双端口
  ☐ SATA 6G              入门, 单端口
  ☐ NVMe PCIe Gen4/5 ⭐  当前主流
  ☐ EDSFF (E1.S/E3.S)    新规范, 散热好

特性:
  ☐ Endurance (DWPD)     企业级 1-3 / 读密集 0.3 / 混合 3+ DWPD
  ☐ 容量                  1/2/4/8/16/32 TB
  ☐ 电容掉电保护          PLP (企业必)
  ☐ 加密                  SED / OPAL / 国密
  ☐ 双端口                高可用 (SAS / NVMe dual port)

RAID 控制器:
  HBA (直通) ⭐           ZFS / Ceph / 软 RAID 用
  Hardware RAID         LSI MegaRAID / PERC / Smart Array (BBU 必)
  Tri-mode (SAS+SATA+NVMe)  新一代
```

### 2.4 网卡 (NIC)

```
速率演进:
  1G  → 10G → 25G ⭐ → 100G ⭐ → 200G → 400G → 800G (新)

形态:
  板载 (Onboard)         1/10G, Mgmt
  PCIe 标卡             10/25/100G+
  OCP 3.0 卡            数据中心标准, 热插
  Mezzanine (刀片)      共享背板

主流厂商:
  Intel (E810 / X710 / X550)
  Mellanox / NVIDIA (ConnectX-6/7/8, BlueField DPU) ⭐ AI 主流
  Broadcom (BCM57500/58800)
  国产: 中科驭数 / 大禹 / 云豹

协议:
  TCP / UDP
  RDMA (RoCEv2 / InfiniBand)  ⭐ AI / HPC / 高频金融
  TCP/IP Offload (TOE)
  SR-IOV (虚拟化 VF, NUMA 亲和)
  DPDK (内核旁路)

布线:
  铜缆 DAC (Direct Attach Copper)   < 5m, 便宜
  AOC (Active Optical Cable)         5-30m, 光信号
  光模块 SFP+/QSFP+/QSFP28/QSFP-DD/OSFP
```

### 2.5 电源 (PSU)

```
特征:
  ☐ 双路冗余 (1+1 / N+1)       ⭐ 服务器必
  ☐ 热插拔 (Hot-swap)           不停机替换
  ☐ 80 Plus 认证                Platinum / Titanium (节能)
  ☐ 功率                        550W / 750W / 1100W / 1600W / 2000W / 3000W (AI 服务器)
  ☐ AC 输入                     100-240V 自适应
  ☐ DC 输入                     -48V (运营商) / 12V (OCP)

配电:
  PDU (机柜级 Power Distribution Unit)
  双路 PDU (A/B, 不同 UPS)
  整机柜级 (OCP Power Shelf, 共享转换)

数据中心实战:
  ☐ 双路独立接 A/B PDU (任一断电不影响)
  ☐ 双 PSU 不同时拔
  ☐ UPS / 柴发 兜底
```

## 三、物理拓扑

### 3.1 主板组成

```
[CPU Socket × 1-2]
    ↓ UPI / Infinity Fabric (CPU 间互联)
[内存插槽 × 16-32] (双路服务器 8×2 = 16 条 DDR5 起步)
[PCIe 槽 × 5-12] (Gen 4/5, x8/x16)
[BMC] (远程管理, IPMI/Redfish)
[VGA / USB / 串口 / Mgmt NIC]
[M.2 / U.2 NVMe 直连]
[CPLD] (上电时序 / 风扇控制)
```

### 3.2 PCIe 拓扑

```
CPU0 ──── 64 lanes Gen5 ──── PCIe Switch ── [GPU0] [GPU1] [NVMe×4]
CPU1 ──── 64 lanes Gen5 ──── PCIe Switch ── [GPU2] [GPU3] [NIC]

关键概念:
  - lane × x16 = 16 lane (256GB/s Gen5)
  - PCIe Switch 扩展 (多 GPU / NVMe 共享 lane)
  - NUMA 亲和: GPU/NIC/NVMe 应连本 CPU socket
  - Bifurcation: x16 → 2×x8 / 4×x4 (拆分)
```

### 3.3 NUMA

```bash
# 查看
lscpu | grep -i numa
numactl -H
lstopo                            # hwloc 图形化

# 关键:
- 每个 NUMA Node 有本地 CPU + 本地内存
- 跨 Node 访问 → 延迟 +50-100%
- 应用要绑核 (taskset / numactl --cpunodebind=0 --membind=0)
```

## 四、散热

```
风冷 (Air Cooling) ⭐ 当前主流 (95% 数据中心)
  - 风扇 (6-12 个, 热插拔)
  - 散热片 (CPU/GPU/VRM)
  - 风道 (前进后出 / 侧进侧出)
  - 最大支持: CPU 350W / GPU 700W (H100 风冷)

冷板液冷 (Cold Plate) ⭐ AI 趋势
  - CPU/GPU 直接接触液体 (50-70%)
  - 风扇辅助 (内存/磁盘)
  - 单板 1-2 kW
  - PUE 1.1-1.2
  - H100/H200/B200 主推

浸没液冷 (Immersion)
  - 整机泡氟化液
  - 单相 / 两相
  - PUE 1.05-1.1
  - 头部互联网试点 (阿里仁和 / 字节)

后门冷却 (Rear Door Heat Exchanger)
  - 机柜后门加水冷
  - 改造友好 (旧机房升级)
```

## 五、上下架认知

### 5.1 机柜

```
标准:
  19 英寸 (宽度 482.6mm)
  深度 800/1000/1200mm
  高度 42U / 47U / 48U / 52U (1U = 44.45mm)

容量:
  传统 5-10 kW (风冷)
  高密 15-30 kW (风冷极限)
  AI 液冷 40-120 kW+ (NVL72)

配套:
  PDU (双路独立, 监控电流)
  Cable Manager (理线架)
  Blanking Panel (闲置 U 位填充, 风道)
  Sliding Rail (滑轨)
  KVM (集中管理)
  接地 (地线连接)
```

### 5.2 上架顺序

```
底部 (重 + 散热好):
  → 大型存储设备 (24/36/72 盘位)
  → 双路服务器 (2U)

中部:
  → 1U 服务器 (高密度)
  → 网络交换机 (ToR, 顶置或中置)

顶部 (轻 + 操作方便):
  → 1U 设备 (跳线盒 / 终端)
  → KVM
  → 光纤跳线 (Patch Panel)

布线:
  电源 (后部) / 网络 (后部 + Mgmt)
  机柜外: 列头柜 / 列尾柜
```

## 六、数据中心 ABC

```
分级 (TIA-942):
  Tier 1   基本 (99.671% / 28.8h 年宕机)
  Tier 2   冗余 (99.741% / 22h)
  Tier 3 ⭐ 可维护并行 (99.982% / 1.6h)
  Tier 4   容错 (99.995% / 26 min)

国标:
  GB 50174 (A/B/C 级)

关键设施:
  ☐ 双路市电 + 柴油发电机 (柴发)
  ☐ UPS (不间断电源, 在线式)
  ☐ 精密空调 (列间 / 行级 / 房间级)
  ☐ 冷却塔 / 冷水机组
  ☐ 消防 (七氟丙烷气体 / 烟感)
  ☐ 安防 (门禁 / 监控 / 防尾随)
  ☐ 监控 (DCIM: 电流 / 温湿度 / 漏水)

机房环境:
  温度  18-27℃ (推荐 22℃)
  湿度  40-60% RH
  PUE   1.1-1.5 (新建) / 1.5-2.0 (老旧)
```

## 七、厂商生态

### 7.1 国外四大

| 厂商 | 代表机型 | BMC | 特点 |
|:---|:---|:---|:---|
| **Dell** | PowerEdge R650/R750/R760 | iDRAC | OpenManage 生态强 |
| **HPE** | ProLiant DL360/DL380/DL580 | iLO | iLO 远程管理标杆 |
| **Lenovo** | ThinkSystem SR650/SR670 | XCC (IMM2 升级) | 联想数据中心业务 (原 IBM) |
| **Supermicro** | A+ / X12 / X13 系列 | IPMI/Redfish | 定制化强, AI 服务器多 |

### 7.2 国产四大

| 厂商 | 代表机型 | BMC | 特点 |
|:---|:---|:---|:---|
| **华为 / 超聚变** | TaiShan / FusionServer 2288H / 5288 / Atlas 800 | iBMC | 鲲鹏 + 昇腾全栈 |
| **浪潮 (Inspur)** | NF5280M6 / NF5468 / NE5260 | ISBMC | 中国市场份额第一 |
| **中科曙光** | I620-G30 / X785-G30 / I8000 | Tcsm | 海光 + 国资委 |
| **新华三 (H3C)** | UniServer R4900 / R5300 | HDM | 多平台兼容 |

### 7.3 互联网自研

```
阿里:     天蝎整机柜 / 倚天 710 (ARM)
字节:      自研 OCP-like / GPU 整机柜
腾讯:      星星海 / 自研 GPU 柜
百度:      昆仑芯 + 自研服务器
美团:      自研 + 浪潮定制
```

## 八、典型配置（速查）

```
通用应用 (2U):
  CPU         双路 Intel/AMD 32 核
  内存        128-256 GB DDR4/DDR5
  磁盘        2× NVMe 480GB (系统) + 4-8× 1.92TB NVMe (数据)
  网卡        2× 10G (业务) + 1× 1G (Mgmt) + IPMI
  电源        2× 800W

数据库 (2U):
  CPU         双路 32-64 核 + 大缓存
  内存        512GB-2TB
  磁盘        2× M.2 + 8-12× NVMe 3.84TB
  网卡        2× 25G

AI 训练 (4-8U):
  CPU         双路 Intel SR / AMD EPYC
  内存        1-2 TB DDR5
  GPU         8× H100 / H200 / B200 SXM (HGX 基板)
  存储        8× NVMe (大容量)
  网卡        8× 400G IB/RoCE (CX-7/8)
  Mgmt        2× 25G
  电源        4× 3000W (12 kW+)
  散热        液冷 (冷板)

存储 (4U):
  CPU         双路 16-24 核
  内存        128GB
  磁盘        36-72× HDD 22TB + 2× NVMe (缓存)
  网卡        2× 25G + 2× 100G
```

## 九、Checklist

```
认知:
☐ 机架 vs 刀片 vs 整机柜 vs 塔式
☐ 1U/2U/4U 高度区别
☐ 双路 NUMA 概念

5 大件:
☐ CPU 核数/频率/TDP/PCIe Lane
☐ 内存 DDR4/DDR5 + ECC + 通道
☐ HDD/SSD/NVMe 区别 + DWPD
☐ NIC 1G/10G/25G/100G + DAC/AOC
☐ PSU 双路 + 80 Plus

物理:
☐ 主板布局
☐ PCIe Gen / x16 / Bifurcation
☐ NUMA 亲和

机柜:
☐ 42U 标准
☐ 上下架顺序
☐ 双路 PDU

数据中心:
☐ Tier 等级
☐ UPS / 柴发 / 精密空调
☐ 温湿度

厂商:
☐ Dell/HPE/Lenovo/Supermicro
☐ 华为/超聚变/浪潮/曙光/新华三
☐ 互联网自研

实战:
☐ 看懂 dmidecode 输出
☐ 看懂 lspci 输出
☐ NUMA 拓扑 (numactl -H / lstopo)
```

## 十、推荐栈

```
体检:         dmidecode + lshw + lscpu + lsblk + ipmitool
拓扑:         lstopo + numactl -H
品牌生态:     Dell PowerEdge / HPE ProLiant / Lenovo ThinkSystem / 浪潮 / 华为 TaiShan
入门书:       《大教堂与集市》(理念) / Brendan Gregg 系列 / 厂商白皮书
社区:         STH (ServeTheHome) ⭐ / AnandTech / Phoronix
国内信息:     极客邦 / 36kr / 芯东西 / EETOP
```

> 📖 **核心判断**：服务器基础 = **分类(机架/刀片/塔式/整机柜) + 5 大件(CPU/内存/磁盘/网卡/电源) + 物理拓扑(主板/PCIe/NUMA) + 散热(风冷/液冷) + 机柜与上下架 + DC ABC(Tier/UPS/温湿度) + 厂商生态(国外四大 + 国产四大)**。能看懂双路服务器的 BOM 单, 理解 NUMA 拓扑, 区分 SATA/SAS/NVMe, 认识 25G/100G NIC, 知道 1U/2U/4U 用途差异, 就具备数据中心硬件准入认知。**测试/操作详见 [18 硬件测试](../../18_硬件测试/01_基础/README.md), 这里聚焦"认得清, 选得对"。**
