# 基础

> 服务器基础 = **服务器分类(机架/刀片/塔式/整机柜) + 5 大件(CPU/内存/磁盘/网卡/电源) + 物理拓扑(主板/PCIe/NUMA) + 散热(风冷/液冷) + 上下架认知 + 数据中心 ABC(机柜/PDU/UPS/温湿度) + 厂商生态(国外四大 + 国产四大)**。面向从笔记本/桌面 PC 转入数据中心的工程师入门，**每个术语都给出解释 + 类比 + 速查口诀**。

---

## 一、服务器分类

### 1.1 按形态分类

| 形态 | 全称 | 解释 | 典型应用 |
|:---|:---|:---|:---|
| **机架式** (Rack) | Rack-mount Server | 标准 19 英寸宽，高度按 U 计算 (1U=4.45cm)，水平躺在机柜里 | 数据中心主流 (80%+) |
| **刀片** (Blade) | Blade Server | 共享背板 (Backplane) + 共享电源 + 共享网络，单台机箱插多张刀片 | 高密度计算 (浪潮 / HPE C7000 / 华为 E9000) |
| **塔式** (Tower) | Tower Server | 立式机箱，像台式机但更大、双 CPU、ECC 内存 | SOHO / 小型办公室 / 分支机构 |
| **整机柜** (Rack-Scale) | Rack-Scale System | 出厂即整机柜交付，统一供电+散热+布线 | AI 训练 (NVIDIA GB200 NVL72) / 云原生 (OCP) |
| **边缘/微型** (Edge) | Edge Server | 小型、加固 (宽温/防尘)、低功耗 | 5G 基站 / IoT / 工业现场 |

**术语速查**:
- **U (Unit)**：机架高度单位，1U = 44.45 mm。常见 1U / 2U / 4U / 8U。
- **SOHO**：Small Office / Home Office，小型办公或家庭办公环境。
- **背板 (Backplane)**：刀片机箱中央的大 PCB 板，所有刀片通过它共享电源/网络/管理总线。
- **OCP**：Open Compute Project，Facebook 2011 年发起的开源数据中心硬件标准。

### 1.2 按用途分类

```
通用计算       Web / 应用 / 微服务 (2U 双路 + 中等内存)
数据库 / 存储   OLTP / OLAP (大内存 + NVMe + RAID)
AI 训练 / 推理 大模型训练 / 推理 (8 卡 GPU + NVLink + IB)
HPC           High Performance Computing (多核 + IB + 并行存储)
大数据         Hadoop / Spark (中等 CPU + 大量 HDD + 多网卡)
分布式存储     Ceph (CPU 适中 + 多盘位 + 双 SSD 缓存)
```

**术语速查**:
- **OLTP** (Online Transaction Processing)：在线事务处理，高频小事务 (银行转账、电商下单)。
- **OLAP** (Online Analytical Processing)：在线分析处理，大批量分析 (报表、BI)。
- **HPC**：High Performance Computing 高性能计算，气象/物理仿真/分子动力学。
- **IB**：InfiniBand，专用低延迟高带宽网络，AI 集群和超算主流。

### 1.3 按市场

| 类型 | 代表厂商 |
|:---|:---|
| 国外通用品牌 | Lenovo (联想) / Dell / HPE (慧与，原 HP 企业) / Supermicro (超微) |
| 国产 | 华为 / 超聚变 / 浪潮 (Inspur) / 中科曙光 / 新华三 (H3C) / 长城 |
| 互联网自研 (类 OCP) | 阿里天蝎 / 字节 / 腾讯星星海 / 百度 |

---

## 二、5 大件认知

服务器 5 大件 = **CPU + 内存 + 磁盘 + 网卡 + 电源**。配上主板/机箱/风扇/BMC 就是一台完整服务器。

### 2.1 CPU (中央处理器)

**CPU** = Central Processing Unit，计算的核心，所有指令都在这里执行。服务器 CPU 与桌面 CPU 区别在于：核数多、支持多路、支持 ECC 内存、PCIe 通道多、TDP 高。

#### 核心参数表

| 参数 | 解释 | 服务器典型值 |
|:---|:---|:---|
| **架构** | CPU 内部设计 (流水线/缓存层次)，决定性能与生态 | Intel x86 / AMD x86 / ARM (鲲鹏/AmpereOne) / LoongArch (龙芯) |
| **代号** | 同一架构的具体一代产品 | Intel Sapphire Rapids / Granite Rapids；AMD Genoa / Turin；鲲鹏 920 |
| **核数** | 物理核心数，每核独立计算 | 8 / 16 / 32 / 64 / 96 / 128 / 192 (EPYC Turin) |
| **主频** | 时钟频率 (GHz)，每秒可执行多少周期 | 基础 2.0-3.5 GHz + Turbo 3.8-5.0 GHz |
| **指令集** | CPU 内置的"操作集"，类似 API | SSE / AVX2 / AVX-512 / VNNI / AMX |
| **TDP** | Thermal Design Power 热设计功耗，决定散热需求 | 150-400W 单 CPU |
| **缓存** | CPU 内部高速存储，L1/L2/L3 三级 | L3 大缓存 (EPYC 384MB+) |
| **内存通道** | CPU 一次能并行访问几条内存 | 6 / 8 / 12 / 16 通道 |
| **PCIe** | 外设扩展总线，连 GPU/NIC/NVMe | Gen 4/5/6, 64-128 条 lane |

**术语解释**:

- **架构 (Architecture)**：CPU 的"种族"。x86 是 PC/服务器主流；ARM 省电，移动端起家、现在进数据中心；LoongArch 是中国自主指令集 (龙芯)。**类比**：架构 = 语言体系 (汉语/英语)，指令集 = 词汇表。
- **指令集 (Instruction Set)**：CPU 能直接执行的"动作集合"。
  - **SSE / AVX2 / AVX-512**：SIMD 指令 (Single Instruction Multiple Data)，"一条指令处理多个数据"，加速向量计算。AVX-512 一次处理 16 个 32 位浮点。
  - **VNNI** (Vector Neural Network Instructions)：Intel 推出，INT8 神经网络专用，AI 推理加速。
  - **AMX** (Advanced Matrix Extensions)：Intel SR+，矩阵乘法加速，AI 训练/推理利器。
- **TDP** (Thermal Design Power)：散热设计功耗。**注意**这是散热器要带走多少热量的指标，不严格等于"耗电"，但工程上近似。一颗 350W TDP 的 CPU，机房空调必须能带走这 350W。
- **Turbo / Boost**：在散热和功耗允许时，CPU 临时超频。基础 2.5 GHz 的 CPU 可能短时间冲到 4.5 GHz。
- **缓存 (Cache)**：CPU 内部高速 SRAM，比内存快 10-100 倍。**L1** 每核独享、最快、最小 (32-64KB)；**L2** 每核独享、中等 (1-2MB)；**L3** 全 CPU 共享、最大 (32-384MB)。命中缓存就快，没命中只能去内存找 (慢 100 倍)。
- **PCIe** (Peripheral Component Interconnect Express)：连接 CPU 与外设 (GPU/NIC/NVMe/RAID 卡) 的高速串行总线。
  - **Gen**：代数，每代带宽翻倍。Gen3 ≈ 1 GB/s/lane，Gen4 ≈ 2 GB/s，Gen5 ≈ 4 GB/s，Gen6 ≈ 8 GB/s。
  - **lane**：单条 PCIe 通道。x1 / x4 / x8 / x16 表示几条 lane 捆绑。x16 Gen5 ≈ 64 GB/s。
  - **服务器 CPU 一颗 64-128 lane**，桌面 CPU 只有 20-28 lane (这是服务器能插多 GPU 多 NVMe 的根本原因)。

#### 双路服务器与 NUMA

**双路** (2-Socket / Dual-Socket) = 一块主板装两颗 CPU。是数据中心绝对主流 (>80%)。

```
Socket0: CPU0 ─ UPI (Intel) / Infinity Fabric (AMD) ─ Socket1: CPU1
   ↓                                                       ↓
 内存通道 0-7                                            内存通道 8-15
 PCIe 0-63                                                PCIe 64-127
 (NUMA Node 0)                                            (NUMA Node 1)
```

**术语解释**:

- **Socket (插座)**：主板上固定 CPU 的物理插槽。双路 = 2 个 Socket。
- **UPI** (Ultra Path Interconnect)：Intel CPU 间互联，类似"高速公路连两个城市"。
- **Infinity Fabric**：AMD 对应的 CPU 间互联技术。
- **NUMA** (Non-Uniform Memory Access)：非一致内存访问。
  - **现象**：CPU0 访问"自己"的内存通道快 (本地)，访问 CPU1 的内存通道慢 (跨 socket，要走 UPI)，延迟差 50-100%。
  - **影响**：应用如果在 CPU0 上跑，但内存被分配到了 Node1，性能直接掉 30-50%。
  - **解决**：应用绑核 (numactl)，让 CPU + 内存 + 设备都在同一个 Node。
  - **口诀**：**"看 lstopo，绑同一 Node"**。

---

### 2.2 内存 (Memory / RAM)

**内存** = Random Access Memory (RAM)，CPU 的"工作台"。掉电数据丢失 (易失性)，但比磁盘快上千倍。

#### 类型对比

| 类型 | 速率 (MT/s) | 容量/条 | 服务器使用场景 |
|:---|:---|:---|:---|
| **DDR4** | 2133 / 2400 / 2666 / 2933 / 3200 | 16-64 GB | 老服务器主流 (上一代) |
| **DDR5** ⭐ | 4800 / 5600 / 6400 | 16-256 GB | 当前主流 (Sapphire Rapids+ / EPYC Genoa+) |
| **HBM** | 片上堆叠，2-5 TB/s | 8-192 GB | GPU 专用 (H100 80GB / B200 192GB) |

**术语解释**:

- **DDR** (Double Data Rate)：双倍数据速率内存。**DDR4 / DDR5** 是世代号。每代频率翻倍、电压降低。
- **MT/s** (Mega Transfers per second)：每秒百万次传输。DDR5-4800 = 每秒 48 亿次传输，单通道带宽 ≈ 38.4 GB/s。
- **HBM** (High Bandwidth Memory)：高带宽内存。多层 DRAM 堆叠 + 硅中介层，带宽 5 TB/s 级别，**只用在 GPU/AI 加速器**，CPU 上极少 (Intel Xeon Max 试过)。

#### 服务器内存的"必备特征"

| 特性 | 解释 | 重要性 |
|:---|:---|:---|
| **ECC** ⭐ | Error-Correcting Code，纠错码，硬件层能纠正单比特错、检测双比特错 | 服务器**必须**，桌面可选 |
| **RDIMM** | Registered DIMM，带寄存器缓冲芯片，时序更稳，容量更大 | 主流服务器内存 |
| **LRDIMM** | Load-Reduced DIMM，负载缓冲，容量更大 (256GB+/条) | 大内存服务器 |
| **PMIC** (DDR5) | DIMM 上自带电源管理芯片 | DDR5 标配 |
| **On-die ECC** (DDR5) | DDR5 芯片**内部**自带 ECC，加 System ECC = 双保险 | DDR5 标配 |

**术语解释**:

- **ECC** (Error-Correcting Code)：内存数据有偶发翻转 (宇宙射线/电压抖动)，ECC 能纠正 1 比特错、检测 2 比特错。**没有 ECC 的服务器跑半年必出莫名其妙的崩溃**。
- **DIMM** (Dual In-line Memory Module)：内存条物理形态，双排引脚。
- **Chipkill** (IBM/AMD)：高级 ECC，单颗 DRAM 芯片全坏也能纠正。
- **Rank**：内存条上一组并行工作的 DRAM 芯片。单条可能 1 Rank、2 Rank、4 Rank。Rank 越多容量越大，但兼容性要看主板。

#### 通道与性能

**内存通道 (Memory Channel)**：CPU 一次能并行访问几条内存。**满通道 = 满带宽**。

```
EPYC Genoa 单 CPU 12 通道，双路 = 24 通道
最佳:  24 条同规格 DIMM 满插         (满速)
次优:  16 条 (跳通道，损失约 30%)
最差:  混插不同速率 → 全部降速到最低
```

**口诀**: **"同规格、同型号、对称满插"**。

---

### 2.3 磁盘 / 存储

服务器存储 = HDD (机械盘) + SSD (固态盘) 组合。

#### 类型对比

| 类型 | 全称 | 顺序读 | 随机 IOPS | 容量 | 单位价格 | 使用场景 |
|:---|:---|:---|:---|:---|:---|:---|
| **HDD** | Hard Disk Drive，机械硬盘 | 200-280 MB/s | 100-200 | 4-30 TB | 最低 | 冷数据 / 备份 / 大容量 |
| **SATA SSD** | Serial ATA SSD | 500 MB/s | 50-100K | 0.5-4 TB | 低 | 入门级 |
| **SAS SSD** | Serial Attached SCSI SSD | 1.2 GB/s | 100-300K | 1-15 TB | 中 | 企业级，双端口高可用 |
| **NVMe SSD** ⭐ | Non-Volatile Memory Express | 3-15 GB/s | 1-3M | 1-32 TB | 中高 | **数据中心主流** |

**术语解释**:

- **HDD**：机械硬盘，盘片 + 磁头，靠物理旋转 (7200 转/分钟) 读写。便宜、容量大、速度慢、怕震。
- **SSD** (Solid State Drive)：固态硬盘，闪存芯片，无机械结构。快、抗震、贵。
- **SATA** (Serial ATA)：老接口，6 Gbps，约 600 MB/s 理论极限。
- **SAS** (Serial Attached SCSI)：企业级接口，12/24 Gbps，**双端口** (两条独立通路，单链路坏不影响)。
- **NVMe** (Non-Volatile Memory Express)：基于 PCIe 总线的协议。**不是接口，是协议**。绕开了 SATA/SAS 控制器，直接走 PCIe Gen4/5，速度爆发 10-30 倍。

#### 接口与外形

| 形态 | 说明 |
|:---|:---|
| **U.2 / U.3** | 2.5 寸 NVMe 盘位，可热插拔，数据中心主流 |
| **M.2** | 长条状，小型化，开机/缓存盘 (不推荐企业生产) |
| **EDSFF E1.S / E3.S** | 新规范，散热好，专为高密度服务器设计 |
| **PCIe 标卡** | 直接插 PCIe 槽，AIC (Add-In Card) |

#### 关键参数

- **DWPD** (Drive Writes Per Day)：每天可写满几次。**企业级 SSD 看 DWPD**。读密集 0.3 / 混合 1 / 写密集 3+。
- **PLP** (Power Loss Protection)：掉电保护，SSD 上的电容确保未刷盘数据安全。**企业级必备**。
- **SED** (Self-Encrypting Drive)：硬盘自加密 (硬件 AES)。
- **OPAL**：TCG (Trusted Computing Group) 制定的 SED 标准。

#### RAID 控制器

**RAID** (Redundant Array of Independent Disks)：独立磁盘冗余阵列。多个盘组合在一起，提供冗余 (坏盘不丢数据) 或性能。

| 类型 | 说明 |
|:---|:---|
| **HBA** (Host Bus Adapter) ⭐ | 直通模式 (JBOD)，控制器只做"接线"，软件层管理 (ZFS/Ceph 用) |
| **Hardware RAID** | 控制器自己做条带/校验，带 BBU 电池防掉电缓存丢失 |
| **BBU** (Battery Backup Unit) | RAID 卡上的电池，保护写缓存 |
| **Tri-mode** | 支持 SAS + SATA + NVMe 三模式 (新一代 RAID 卡) |

**RAID 级别速查** (后续章节展开)：
- **RAID 0**：条带，无冗余，性能高
- **RAID 1**：镜像，容量减半，可坏 1 盘
- **RAID 5**：分布奇偶校验，可坏 1 盘
- **RAID 6**：双奇偶，可坏 2 盘
- **RAID 10**：镜像+条带，容量减半，性能+冗余

---

### 2.4 网卡 (NIC)

**NIC** (Network Interface Card / Controller)：网络接口卡，把服务器接入网络。

#### 速率演进

```
1 Gbps  →  10 Gbps  →  25 Gbps ⭐  →  100 Gbps ⭐  →  200/400 Gbps  →  800 Gbps (新)
```

**Gbps** = Gigabits per second，每秒十亿比特。注意：网络是 bit (b)，存储是 byte (B)，1 Byte = 8 bit。100 Gbps ≈ 12.5 GB/s。

#### 形态

| 形态 | 说明 |
|:---|:---|
| **板载** (Onboard / LOM) | LAN On Motherboard，主板自带，1/10G，多做管理口 |
| **PCIe 标卡** | 插 PCIe 槽，10/25/100G+ 主流 |
| **OCP 3.0** | 数据中心专用规范卡，热插拔，统一外形 |
| **Mezzanine** | 刀片机箱专用，插刀片上 |

#### 主流厂商

| 厂商 | 代表产品 | 强项 |
|:---|:---|:---|
| **Intel** | E810 / X710 / X550 | 通用，OS 兼容好 |
| **Mellanox / NVIDIA** | ConnectX-6/7/8, BlueField DPU | **AI 集群主流** (IB/RoCE) |
| **Broadcom** | BCM57500/58800 | 云厂商定制 |
| **国产** | 中科驭数 / 大禹 / 云豹 | 信创替代 |

#### 协议与卸载

| 术语 | 解释 |
|:---|:---|
| **TCP / UDP** | 通用传输层协议 |
| **RDMA** | Remote Direct Memory Access，远程直接内存访问，跳过 CPU 拷贝，**低延迟高吞吐** |
| **RoCE** | RDMA over Converged Ethernet，以太网上跑 RDMA |
| **InfiniBand (IB)** | 专用 RDMA 网络，超低延迟 (~0.6 μs) |
| **SR-IOV** | Single Root I/O Virtualization，一张物理网卡虚拟出多个 VF (Virtual Function)，**直通虚拟机** |
| **DPDK** | Data Plane Development Kit，用户态网卡驱动，绕过内核，超高性能 |
| **TOE** | TCP Offload Engine，TCP 卸载到网卡 |

**RDMA 速查**：CPU 不参与数据搬运，网卡直接把数据从 A 主机的内存写到 B 主机的内存。**适合 AI 训练、HPC、高频金融、分布式存储**。

#### 布线

| 类型 | 全称 | 距离 | 说明 |
|:---|:---|:---|:---|
| **DAC** | Direct Attach Copper | < 5 m | 铜缆，便宜，机柜内/邻柜 |
| **AOC** | Active Optical Cable | 5-30 m | 光纤一体化，跨柜跨排 |
| **光模块 + 跳线** | SFP+/QSFP+/QSFP28/QSFP-DD/OSFP | 任意 | 模块化，长距 |

**SFP+** (Small Form-factor Pluggable +)：10G 单口；**QSFP+** 4 通道 40G；**QSFP28** 100G；**QSFP-DD** 200/400G；**OSFP** 400/800G。

---

### 2.5 电源 (PSU)

**PSU** (Power Supply Unit)：电源单元。服务器电源 ≠ 桌面电源，必有冗余、热插拔。

#### 必备特性

| 特性 | 解释 |
|:---|:---|
| **双路冗余 (1+1 / N+1)** | 两个电源，一坏不停机 (服务器**必须**) |
| **热插拔** (Hot-swap) | 不停机替换坏电源 |
| **80 Plus 认证** | 能效等级 White → Bronze → Silver → Gold → Platinum → Titanium |
| **功率档位** | 550W / 750W / 1100W / 1600W / 2000W / 3000W (AI 服务器) |
| **AC 输入** | 100-240V 自适应 (兼容全球) |
| **DC 输入** | -48V (运营商) / 12V (OCP) / 48V (OCP v3) |

**术语解释**:

- **AC** (Alternating Current)：交流电，市电 220V/110V。
- **DC** (Direct Current)：直流电，服务器内部最终都要转成 12V 直流。OCP 标准用 48V DC 直接送进机柜，少一次转换提升效率。
- **80 Plus**：能效认证。Platinum (白金) ≥ 94% 效率，Titanium (钛金) ≥ 96%。1000W 负载下，钛金每年能省几十度电。
- **N+1 冗余**：N 个工作电源 + 1 个备份，一坏即顶。常见 2+0 (两个都用) / 1+1 (一备一)。

#### 配电链路

```
[市电 220V] → [UPS] → [PDU] → [服务器 PSU × 2 (双路独立)]
                ↑                    ↑
              掉电 30 分钟兜底        分别接 A/B 路 PDU
              
[市电断] → [UPS 顶上 30 分钟] → [柴发启动接力] → [恢复市电]
```

- **PDU** (Power Distribution Unit)：机柜配电单元。
- **UPS** (Uninterruptible Power Supply)：不间断电源，电池组+逆变器，市电断电后立即顶上 (毫秒级切换)。
- **柴发**：柴油发电机。UPS 撑 30 分钟，柴发 1-2 分钟内启动接力，能撑几小时到几天。

**实战口诀**：**双 PSU 一定接到不同 PDU (A 路 / B 路)，任一断电不影响**。

---

## 三、物理拓扑

### 3.1 主板组成

```
┌──────────────────────────────────────────────────────────────┐
│ CPU Socket × 1-2                                              │
│   ↓ UPI / Infinity Fabric (CPU 间互联)                         │
│ 内存插槽 × 16-32 (双路 = 8×2 = 16 条 DDR5 起步)                 │
│ PCIe 槽 × 5-12 (Gen 4/5, x8/x16)                              │
│ BMC (远程管理芯片，独立 IP)                                    │
│ VGA / USB / 串口 / Mgmt NIC                                   │
│ M.2 / U.2 NVMe 直连接口                                       │
│ CPLD (上电时序 / 风扇控制)                                     │
└──────────────────────────────────────────────────────────────┘
```

**术语解释**:

- **BMC** (Baseboard Management Controller)：基板管理控制器，**独立于主 CPU 的小芯片**，主机断电它还活着。负责远程开关机、温度监控、KVM Over IP。每家叫法不同：Dell 叫 **iDRAC**、HPE 叫 **iLO**、联想叫 **XCC**、华为叫 **iBMC**、超微叫 **IPMI**。
- **VGA**：老视频接口，服务器用于直接接显示器排障 (15 针蓝色)。
- **CPLD** (Complex Programmable Logic Device)：可编程逻辑芯片，管控上电顺序、风扇调速等"主板大脑外的小脑"。
- **Mgmt NIC**：Management 网卡，专用于 BMC 出口，不走业务流量。

### 3.2 PCIe 拓扑

```
CPU0 ───── 64 lanes Gen5 ───── PCIe Switch ── [GPU0] [GPU1] [NVMe×4]
                                              │
CPU1 ───── 64 lanes Gen5 ───── PCIe Switch ── [GPU2] [GPU3] [NIC]
```

- **PCIe Switch**：PCIe 交换芯片 (Broadcom PEX / Microchip)，**扩展** PCIe 端口数。1 个上行 (连 CPU) → 多个下行 (连 GPU/NVMe)。
- **Bifurcation** (PCIe 分叉)：把一条 x16 拆成 2×x8 或 4×x4，连多个设备。
- **NUMA 亲和**：**GPU/NIC/NVMe 应该连在同一个 CPU socket 的 PCIe 上**，跨 socket 走 UPI 会损失带宽。

### 3.3 NUMA 实战速查

```bash
# 查看 NUMA 拓扑
lscpu | grep -i numa             # 节点数
numactl -H                       # 详细节点信息 + 内存大小
lstopo                           # 图形化 (hwloc 工具)

# 应用绑核
numactl --cpunodebind=0 --membind=0 ./app   # 绑到 Node 0

# 验证
ps -o pid,psr,comm <pid>          # psr = 当前在哪个 CPU
```

**口诀**: **"NUMA 不绑核，性能掉一半"**。

---

## 四、散热

数据中心**最大的成本之一是散热电费**。服务器越来越热 (单卡 H100 700W、B200 1200W)，散热从风冷走向液冷。

### 4.1 风冷 (Air Cooling) — 当前主流 95%

```
[空调送冷风] → [服务器前面板进风] → [CPU/GPU/内存散热器]
              → [风扇抽热风] → [机柜后部热通道] → [空调回风]
```

- **风扇**：6-12 个，热插拔，故障可单独换。
- **散热片**：金属鳍片 (铜底 + 铝鳍)，被动散热靠风扇吹。
- **风道**：前进后出 (主流) / 侧进侧出 (网络设备多)。
- **极限**：CPU 350W / GPU 700W (H100 风冷接近极限)。
- **冷热通道隔离** (Hot/Cold Aisle Containment)：机柜前面进冷风、后面出热风，物理隔开，提升空调效率。

### 4.2 冷板液冷 (Cold Plate) — AI 趋势 ⭐

```
[CPU/GPU 上加金属冷板] → [水/液体循环带走热] 
                       → [Manifold 分水] → [CDU 热交换] → [室外冷却塔]
```

- **冷板**：金属板贴 CPU/GPU，内通液体。**只覆盖发热大件 (50-70% 热量)**，剩下用风扇辅助。
- **Manifold**：歧管，整机柜级分水器。
- **CDU** (Coolant Distribution Unit)：冷却液分配单元，二次环路换热。
- **PUE**：1.1-1.2 (比风冷的 1.5 省 20-30% 电)。
- **典型应用**：H100/H200/B200 主推。

### 4.3 浸没液冷 (Immersion) — 头部试点

```
整机泡在不导电的氟化液 / 矿物油里，靠液体直接带走热。
```

- **单相**：液体不沸腾，泵循环。矿物油/合成油。
- **两相**：液体沸点低 (3M Novec)，受热气化，气体上升到冷凝器，凝结回液。**3M 已退出，产业链调整中**。
- **PUE 1.05-1.1**，业界顶配。
- **应用**：阿里仁和数据中心 / 字节海南。

### 4.4 后门冷却 (RDHx)

**RDHx** (Rear Door Heat Exchanger)：机柜**后门**装水冷盘管，热风出来被立刻冷却。**改造友好**，老机房升级首选。

---

## 五、上下架认知

### 5.1 机柜规格

| 参数 | 标准值 |
|:---|:---|
| 宽度 | **19 英寸** (482.6 mm)，全球通用 |
| 深度 | 800 / 1000 / 1200 mm |
| 高度 | 42U / 47U / 48U / 52U (1U = 44.45 mm) |
| 承重 | 1000-1500 kg |
| 标准颜色 | 黑 / 灰 |

**整机柜功率密度**：
- 传统 5-10 kW (风冷)
- 高密 15-30 kW (风冷极限)
- AI 液冷 40-120 kW+ (NVL72)

### 5.2 机柜配套

| 配件 | 说明 |
|:---|:---|
| **PDU** | 双路独立 (A 路 + B 路)，监控每口电流 |
| **Cable Manager** | 理线架，垂直/水平，防"线乱如毛" |
| **Blanking Panel** | 盲板，填闲置 U 位，避免冷热风短路 |
| **Sliding Rail** | 滑轨，服务器可拉出维护 |
| **KVM Console** | 1U 抽屉，含小屏幕+键盘鼠标，应急排障 |
| **接地线** | 机柜与机房接地汇流排连接，防静电+雷击 |

### 5.3 上架顺序

```
[顶部] ─────────── 跳线盒 (Patch Panel) / KVM 抽屉 / 1U 终端设备
[中部] ─────────── 网络交换机 (ToR, Top of Rack) / 1U 服务器
[下部] ─────────── 2U/4U 服务器
[底部] ─────────── 重型存储 (24/36/72 盘位 JBOD)
```

**口诀**：**"重下轻上、热下冷上、网络居中"**。

---

## 六、数据中心 ABC

### 6.1 Tier 分级 (TIA-942)

| Tier | 中文 | 可用性 | 年宕机 | 特点 |
|:---|:---|:---|:---|:---|
| Tier 1 | 基本 | 99.671% | 28.8 h | 单路市电 + UPS，无冗余 |
| Tier 2 | 冗余 | 99.741% | 22 h | UPS/柴发冗余 |
| Tier 3 ⭐ | 可维护并行 | 99.982% | 1.6 h | 双路市电 + 全冗余 + N+1 |
| Tier 4 | 容错 | 99.995% | 26 min | 全 2N 冗余，金融级 |

**国标**：GB 50174，分 A / B / C 三级，A 级近似 Tier 3-4。

### 6.2 关键设施

| 系统 | 作用 |
|:---|:---|
| **双路市电** | 两个变电站独立供电 |
| **柴发** | 柴油发电机，市电全断兜底 (1-2 分钟启动，撑数天) |
| **UPS** | 不间断电源，市电断到柴发起的"缝隙"由它顶 (毫秒级切换) |
| **精密空调** | 比家用空调精度高，温度 ±1℃、湿度 ±5% |
| **冷却塔 / 冷水机组** | 大型冷源，向精密空调供冷冻水 |
| **消防** | 七氟丙烷气体 (不损坏设备) + 烟感 + 极早期 (VESDA) |
| **安防** | 门禁 + 监控 + 防尾随 + 等保 |
| **DCIM** | Data Center Infrastructure Management，电流/温湿度/漏水监控 |

### 6.3 机房环境

| 参数 | 标准值 |
|:---|:---|
| **温度** | 18-27℃ (推荐 22℃，ASHRAE A1) |
| **湿度** | 40-60% RH (相对湿度，太干静电、太湿凝露) |
| **PUE** | 1.1-1.5 (新建) / 1.5-2.0 (老旧)  |
| **WUE** | Water Usage Effectiveness，水耗 |
| **CUE** | Carbon Usage Effectiveness，碳耗 |

**PUE** (Power Usage Effectiveness) = 数据中心总能耗 / IT 设备能耗。**理想值 1.0**，实际 1.1-1.5。PUE 1.5 意味着 IT 用 1 度电、辅助 (空调/UPS/照明) 用 0.5 度。

---

## 七、厂商生态

### 7.1 国外四大

| 厂商 | 代表机型 | BMC 叫法 | 特点 |
|:---|:---|:---|:---|
| **Dell** | PowerEdge R650 / R750 / R760 | **iDRAC** (integrated Dell Remote Access Controller) | OpenManage 生态强 |
| **HPE** | ProLiant DL360 / DL380 / DL580 | **iLO** (Integrated Lights-Out) | iLO 远程管理标杆 |
| **Lenovo** | ThinkSystem SR650 / SR670 | **XCC** (XClarity Controller) | 联想数据中心业务，原 IBM x86 |
| **Supermicro** | A+ / X12 / X13 系列 | **IPMI / Redfish** | 定制化强，AI 服务器多 |

### 7.2 国产四大

| 厂商 | 代表机型 | BMC | 特点 |
|:---|:---|:---|:---|
| **华为 / 超聚变** | TaiShan / FusionServer 2288H / 5288 / Atlas 800 | **iBMC** | 鲲鹏 + 昇腾全栈 |
| **浪潮 (Inspur)** | NF5280M6 / NF5468 / NE5260 | **ISBMC** | 中国市场份额第一 |
| **中科曙光** | I620-G30 / X785-G30 / I8000 | **Tcsm** | 海光 + 国资背景 |
| **新华三 (H3C)** | UniServer R4900 / R5300 | **HDM** | 多平台兼容 |

### 7.3 互联网自研

```
阿里:   天蝎整机柜 / 倚天 710 (ARM 自研 CPU)
字节:   自研 OCP-like / GPU 整机柜
腾讯:   星星海 / 自研 GPU 柜
百度:   昆仑芯 + 自研服务器
美团:   自研 + 浪潮定制
```

---

## 八、典型配置（速查）

### 8.1 通用应用 (2U)

```
CPU      双路 Intel/AMD 32 核
内存     128-256 GB DDR5
磁盘     2× NVMe 480GB (系统) + 4-8× 1.92TB NVMe (数据)
网卡     2× 10G (业务) + 1× 1G (Mgmt) + IPMI
电源     2× 800W
```

### 8.2 数据库 (2U)

```
CPU      双路 32-64 核 + 大缓存
内存     512GB-2TB
磁盘     2× M.2 (系统) + 8-12× NVMe 3.84TB
网卡     2× 25G
```

### 8.3 AI 训练 (8U)

```
CPU      双路 Intel SR / AMD EPYC
内存     1-2 TB DDR5
GPU      8× H100 / H200 / B200 SXM (HGX 基板)
存储     8× NVMe (大容量)
网卡     8× 400G IB/RoCE (CX-7/8) + 2× 25G (Mgmt)
电源     4× 3000W (12 kW+)
散热     液冷 (冷板)
```

### 8.4 存储 (4U)

```
CPU      双路 16-24 核
内存     128GB
磁盘     36-72× HDD 22TB + 2× NVMe (缓存)
网卡     2× 25G + 2× 100G
```

---

## 九、Checklist

```
认知:
☐ 机架 vs 刀片 vs 整机柜 vs 塔式
☐ 1U/2U/4U/8U 高度区别
☐ 双路 + NUMA 概念

5 大件:
☐ CPU 核数/频率/TDP/PCIe lane
☐ 内存 DDR4/DDR5 + ECC + 通道
☐ HDD/SSD/NVMe 区别 + DWPD
☐ NIC 1G/10G/25G/100G + DAC/AOC
☐ PSU 双路 + 80 Plus

物理:
☐ 主板布局
☐ PCIe Gen / x16 / Bifurcation
☐ NUMA 亲和

机柜:
☐ 19 英寸 / 42U 标准
☐ 上下架顺序
☐ 双路 PDU

数据中心:
☐ Tier 等级
☐ UPS / 柴发 / 精密空调
☐ 温湿度 / PUE

厂商:
☐ Dell / HPE / Lenovo / Supermicro (BMC: iDRAC / iLO / XCC / IPMI)
☐ 华为 / 超聚变 / 浪潮 / 曙光 / 新华三 (BMC: iBMC / ISBMC / Tcsm / HDM)
☐ 互联网自研

实战:
☐ 看懂 dmidecode 输出
☐ 看懂 lspci 输出
☐ NUMA 拓扑 (numactl -H / lstopo)
```

---

## 十、推荐栈

```
体检:       dmidecode + lshw + lscpu + lsblk + ipmitool
拓扑:       lstopo + numactl -H
品牌生态:   Dell PowerEdge / HPE ProLiant / Lenovo ThinkSystem / 浪潮 NF / 华为 TaiShan
入门书:     《大教堂与集市》(理念) / Brendan Gregg 系列 / 厂商白皮书
社区:       STH (ServeTheHome) ⭐ / AnandTech / Phoronix
国内信息:   极客邦 / 36kr / 芯东西 / EETOP
```

---

## 十一、术语总表 (一图速查)

| 缩写 | 全称 | 中文 |
|:---|:---|:---|
| **U** | Unit | 机架高度单位 (44.45 mm) |
| **TDP** | Thermal Design Power | 热设计功耗 |
| **NUMA** | Non-Uniform Memory Access | 非一致内存访问 |
| **UPI** | Ultra Path Interconnect | Intel CPU 间互联 |
| **ECC** | Error-Correcting Code | 纠错码内存 |
| **DIMM** | Dual In-line Memory Module | 双列直插内存模块 |
| **RDIMM** | Registered DIMM | 带寄存器内存 |
| **HBM** | High Bandwidth Memory | 高带宽内存 (GPU 用) |
| **PMIC** | Power Management Integrated Circuit | 电源管理芯片 |
| **HDD** | Hard Disk Drive | 机械硬盘 |
| **SSD** | Solid State Drive | 固态硬盘 |
| **NVMe** | Non-Volatile Memory Express | 基于 PCIe 的存储协议 |
| **SATA** | Serial ATA | 串行 ATA 接口 |
| **SAS** | Serial Attached SCSI | 串行 SCSI 接口 |
| **DWPD** | Drive Writes Per Day | 每日整盘写入次数 |
| **PLP** | Power Loss Protection | 掉电保护 |
| **RAID** | Redundant Array of Independent Disks | 独立磁盘冗余阵列 |
| **HBA** | Host Bus Adapter | 主机总线适配器 (直通卡) |
| **BBU** | Battery Backup Unit | RAID 卡电池 |
| **NIC** | Network Interface Card | 网络接口卡 |
| **RDMA** | Remote Direct Memory Access | 远程直接内存访问 |
| **RoCE** | RDMA over Converged Ethernet | 以太网 RDMA |
| **IB** | InfiniBand | 专用低延迟网络 |
| **SR-IOV** | Single Root I/O Virtualization | 单根 I/O 虚拟化 |
| **DPDK** | Data Plane Development Kit | 数据平面开发套件 |
| **DAC** | Direct Attach Copper | 直连铜缆 |
| **AOC** | Active Optical Cable | 有源光缆 |
| **PCIe** | Peripheral Component Interconnect Express | 高速外设总线 |
| **PSU** | Power Supply Unit | 电源单元 |
| **PDU** | Power Distribution Unit | 机柜配电单元 |
| **UPS** | Uninterruptible Power Supply | 不间断电源 |
| **BMC** | Baseboard Management Controller | 基板管理控制器 |
| **IPMI** | Intelligent Platform Management Interface | 智能平台管理接口 (协议) |
| **iDRAC** | integrated Dell Remote Access Controller | Dell BMC |
| **iLO** | Integrated Lights-Out | HPE BMC |
| **XCC** | XClarity Controller | Lenovo BMC |
| **iBMC** | integrated BMC | 华为 BMC |
| **CPLD** | Complex Programmable Logic Device | 复杂可编程逻辑器件 |
| **PUE** | Power Usage Effectiveness | 电源使用效率 |
| **WUE** | Water Usage Effectiveness | 水使用效率 |
| **CDU** | Coolant Distribution Unit | 冷却液分配单元 |
| **RDHx** | Rear Door Heat Exchanger | 后门换热器 |
| **OCP** | Open Compute Project | 开放计算项目 |
| **DCIM** | Data Center Infrastructure Management | 数据中心基础设施管理 |
| **OLTP** | Online Transaction Processing | 在线事务处理 |
| **OLAP** | Online Analytical Processing | 在线分析处理 |
| **HPC** | High Performance Computing | 高性能计算 |
| **ToR** | Top of Rack | 顶置交换机 |

---

> 📖 **核心判断**：服务器基础 = **分类(机架/刀片/塔式/整机柜) + 5 大件(CPU/内存/磁盘/网卡/电源) + 物理拓扑(主板/PCIe/NUMA) + 散热(风冷/液冷) + 机柜与上下架 + DC ABC(Tier/UPS/温湿度/PUE) + 厂商生态(国外四大 + 国产四大)**。
> 
> 能看懂双路服务器的 BOM 单、理解 NUMA 拓扑、区分 SATA/SAS/NVMe、认识 25G/100G NIC、知道 1U/2U/4U 用途差异、记住"双 PSU 接不同 PDU"，就具备数据中心硬件准入认知。
> 
> **测试 / 操作详见 [18 硬件测试](../../18_硬件测试/01_基础/README.md)，本章聚焦"认得清，选得对"。**
