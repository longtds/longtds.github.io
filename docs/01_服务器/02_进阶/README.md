# 进阶

> 服务器进阶 = **CPU 深度(架构/指令集/性能模式) + 内存深度(DDR5/HBM/CXL/NUMA 平衡) + 存储深度(NVMe 队列/RAID/分层) + 网络深度(SR-IOV/DPDK/RDMA/Offload) + BMC 深度(Redfish/SOL/KVM/Sensor) + 固件层次(BIOS/UEFI/BMC/CPLD) + GPU 入门(架构/拓扑/驱动) + 多路 / 大内存 / 满 PCIe 配置**。面向 1-3 年硬件工程师。

## 一、CPU 深度

### 1.1 主流架构对比 (2024-2026)

| 系列 | 厂商 | 核数上限 | 主频 | DDR | PCIe | 备注 |
|:---|:---|:---|:---|:---|:---|:---|
| Sapphire Rapids (4th Xeon SP) | Intel | 60 | 2.0-3.7 | DDR5-4800 | Gen 5 | AMX + CXL 1.1 |
| Emerald Rapids (5th Xeon SP) | Intel | 64 | 2.3-4.0 | DDR5-5600 | Gen 5 | EMR, 性能优化 |
| Granite Rapids (6th Xeon 6) | Intel | 128 | 2.0-3.9 | DDR5-6400 / MRDIMM | Gen 5 | 2025 主推 ⭐ |
| Sierra Forest (E-core) | Intel | 288 | - | DDR5-6400 | Gen 5 | 高密度 E-core |
| EPYC Genoa (Zen4) | AMD | 96 | 2.4-3.7 | DDR5-4800 | Gen 5 | 单插槽王者 ⭐ |
| EPYC Bergamo (Zen4c) | AMD | 128 | 2.25-3.1 | DDR5-4800 | Gen 5 | 云原生密度 |
| EPYC Turin (Zen5) | AMD | 192 | 2.4-5.0 | DDR5-6000 | Gen 5 | 2024-2025 ⭐ |
| 鲲鹏 920 | 华为 | 64 | 2.6-3.0 | DDR4-3200 | Gen 4 | ARMv8.2 国产标杆 |
| 鲲鹏 950 (2025+) | 华为 | 96+ | - | DDR5 | Gen 5 | 7nm/5nm |
| 海光 C86-4 (Zen4 衍生) | 海光 | 64 | 2.5-3.3 | DDR5 | Gen 5 | 海光信创 |
| 飞腾 FT-2500 | 飞腾 | 64 | 2.0-2.2 | DDR4 | Gen 3 | 国密强 |
| Ampere AmpereOne | Ampere | 192 | 3.2 | DDR5-5200 | Gen 5 | 云原生 ARM |
| Graviton 4 | AWS | 96 | 3.0 | DDR5-5600 | Gen 5 | AWS 自研 ARM |

### 1.2 关键指令集

```
SSE/AVX2          通用 SIMD
AVX-512           Intel ⭐ AI/HPC/数据库
AMX (Advanced Matrix) ⭐  Intel SR+, AI 推理矩阵加速 (BF16/INT8)
VNNI              Intel, INT8 神经网络加速
SVE / SVE2        ARM 可变向量 (鲲鹏 950 / Graviton)
NEON              ARM SIMD 基础
Confidential:
  Intel TDX       ⭐ Trust Domain (机密 VM)
  AMD SEV-SNP     ⭐ 加密 VM + 完整性
  ARM CCA         Confidential Compute Architecture
国密加速:
  ZUC / SM2/3/4 (鲲鹏 / 海光 / 飞腾 CPU 卸载)
```

### 1.3 CPU 性能模式

```bash
# 性能 governor (Linux)
sudo cpupower frequency-set -g performance      # 性能模式
sudo cpupower frequency-set -g powersave         # 节能
sudo cpupower frequency-set -g schedutil         # 默认 (5.0+)

# 查看
cpupower frequency-info
turbostat                                       # Intel turbo 状态

# C-states (深度休眠, 唤醒延迟)
sudo cpupower idle-set --disable-by-latency 1   # 关闭 > 1μs 的 C-state (低延迟应用)

# P-states + EPB (Intel)
sudo x86_energy_perf_policy performance

# 关闭超线程 (HT) - 仅在确认有收益时 (HPC/低延迟)
echo off | sudo tee /sys/devices/system/cpu/smt/control

# NUMA balancing (内核自动迁移内存)
echo 0 | sudo tee /proc/sys/kernel/numa_balancing   # 关 (绑核应用)
echo 1 | sudo tee /proc/sys/kernel/numa_balancing   # 开 (通用)
```

### 1.4 NUMA 实战

```bash
# 拓扑
numactl -H
lstopo --of svg > topo.svg                       # 图形化

# 应用绑核
numactl --cpunodebind=0 --membind=0 ./app        # CPU0 socket + 本地内存
numactl --physcpubind=0-15 ./app                 # 具体 CPU

# 验证绑核
ps -o pid,psr,comm <pid>
taskset -pc <pid>

# 关键场景:
- 数据库: 绑 1 socket + 本地内存
- AI 训练: GPU 应连本 socket 的 NIC + NVMe
- 微服务: 绑核 + cpuset cgroup
```

## 二、内存深度

### 2.1 DDR5 + MRDIMM

```
DDR5 vs DDR4:
  - 通道 2 sub-channel (40 bit, 32 数据 + ECC)
  - 速率 4800-6400 (DDR5) vs 2400-3200 (DDR4)
  - On-die ECC (单条芯片级)
  - PMIC 上板 (DIMM 自带电源)
  - 单条容量 16-256 GB

MRDIMM (Multiplexed Rank DIMM) ⭐ 2025+
  - 双 Rank 并发, 速率 8800+
  - Granite Rapids / EPYC Turin 支持
  - AI / HPC 内存带宽提升 30-40%

通道布局示例 (双路 EPYC Genoa, 12 通道 × 2):
  最佳: 24 条同规格 DIMM 满插 ⭐
  次优: 16 条 (8 通道每路, 跳通道损失)
  ❌:   非对称 / 不同速率混插 → 降速到最低

ECC 类型:
  SECDED (传统)         单错纠 + 双错检
  Chipkill (IBM/AMD)     单芯片全坏可纠
  DDR5 On-die + System  双保险
  Optane DCPMM           已 EOL
```

### 2.2 CXL Memory

```
CXL 类型:
  Type 1: 加速器 (Cache 一致)
  Type 2: GPU/FPGA (Cache+Memory)
  Type 3: 内存扩展 ⭐ 主流

CXL Memory 扩展:
  - 通过 PCIe Gen5 接口
  - 单卡 128GB-1TB+
  - 延迟 100-200ns (vs DDR 80-120ns)
  - 适合冷热分层

NUMA 感知:
  CXL Mem 作为新的 NUMA Node
  内核自动冷热迁移 (Linux 6.x+, kdamond + DAMON)

工具:
  cxl-cli (Linux)         查看 CXL 设备
  ndctl                   命名空间管理
  Intel MLC (CXL 支持)    延迟测试
```

### 2.3 HBM (片上内存)

```
HBM = High Bandwidth Memory (Die 堆叠 + 硅中介)

主要用途:
  GPU                  H100 80GB HBM3 / B200 192GB HBM3e
  AI 加速器            TPU / 昇腾 / DCU
  HBM CPU              Intel Xeon Max (HBM2e 64GB, 已停)

带宽:
  HBM3      ~3 TB/s (H100)
  HBM3e     ~5 TB/s (H200/B200)
  HBM4      2025+ 量产

ECC: HBM3+ 强制 ECC
```

### 2.4 内存性能测试

```bash
# Intel MLC ⭐ (内存延迟+带宽)
mlc                                              # 完整测试
mlc --latency_matrix                              # NUMA 延迟矩阵
mlc --bandwidth_matrix                            # NUMA 带宽矩阵

# STREAM (经典)
gcc -O3 -fopenmp -mcmodel=medium stream.c -o stream
OMP_NUM_THREADS=$(nproc) ./stream

# 期望 (DDR5-5600 双路 EPYC Genoa 满通道):
- Copy:  ~600 GB/s
- Scale: ~580 GB/s
- Add:   ~620 GB/s
- Triad: ~620 GB/s
```

## 三、存储深度

### 3.1 NVMe 队列深度

```
NVMe 优势:
  - 64K 队列 (vs SAS 256)
  - 每队列 64K 命令
  - 无锁多核并发
  - 低延迟 (~10μs)

队列分配:
  CPU 核数 × N 队列 (Linux 默认每核 1 队列)
  echo nvme | cat /sys/block/nvme0n1/queue/nr_requests

中断:
  MSI-X 多向量 (每队列独立中断)
  irqbalance 自动平衡

性能调优:
  # IRQ 绑 CPU 本 NUMA
  cat /proc/interrupts | grep nvme0q
  sudo set_irq_affinity_cpulist.sh 0-15 nvme0
  
  # I/O Scheduler
  echo none > /sys/block/nvme0n1/queue/scheduler   # NVMe 关闭软件调度
  
  # io_uring (现代 async)
  fio --ioengine=io_uring --iodepth=128 --numjobs=4 ...
```

### 3.2 RAID 硬件 vs 软件

```
硬件 RAID (Hardware RAID):
  优势: BBU 缓存 + 卸载 CPU + 独立电池
  劣势: 控制器单点 + 厂商绑定 + NVMe 兼容差
  典型: LSI MegaRAID / Dell PERC / HPE Smart Array
  
  级别:
    RAID 0   条带 (无冗余, 性能高)
    RAID 1   镜像 (容量减半)
    RAID 5   分布奇偶 (1 盘冗余, 写惩罚)
    RAID 6   双奇偶 (2 盘冗余)
    RAID 10  镜像+条带 (容量减半, 性能+冗余)
    
软件 RAID:
  Linux mdadm        ⭐ 灵活, 兼容好
  ZFS / Btrfs         自带校验+快照
  LVM mirror          逻辑卷镜像
  Ceph / GlusterFS    分布式
  
NVMe 时代趋势:
  → HBA 直通 (JBOD) + 软件层 (ZFS / Ceph)
  → SPDK 用户态驱动 (低延迟)
  
工具:
  storcli64 / perccli64 / ssacli (厂商)
  mdadm (软 RAID)
  zpool (ZFS)
  详见 18 硬件测试 02 进阶
```

### 3.3 存储分层

```
Tier 0  HBM / CXL 内存       超热 (推理 KV-Cache)
Tier 1  NVMe Gen5 SSD        热数据 (DB / 热文件)
Tier 2  NVMe Gen4 SSD        温数据 (索引 / 缓存)
Tier 3  SATA SSD             冷热边界 (备份缓存)
Tier 4  HDD 22TB             冷数据 (归档)
Tier 5  Tape / Glacier       极冷 (合规归档)

工具:
  Bcache / dm-cache  SSD 加速 HDD
  ZFS L2ARC           读缓存
  ZFS SLOG            写日志 (SSD)
  Linux DAMON         冷热感知 (CXL 时代)
```

## 四、网络深度

### 4.1 高速 NIC

```
NIC 厂商对比:
  Intel E810 (100/200G)       通用, OSS 友好
  Mellanox CX-6 (200G)        IB/RoCE 主流
  Mellanox CX-7 (400G) ⭐      AI 集群标配
  Mellanox CX-8 (800G)        2025 新, 配 Blackwell
  BlueField-3 DPU             400G + ARM 加速
  Broadcom Thor 2 (400G)      云厂商定制多

接口:
  PCIe Gen4 x16   → 32 GB/s ≈ 256 Gbps
  PCIe Gen5 x16   → 64 GB/s ≈ 512 Gbps (400G 单口需要 Gen5 x16)
  PCIe Gen5 x32   → 双口 400G

形态:
  PCIe 标卡 / OCP 3.0 / Mezzanine
```

### 4.2 SR-IOV (单根虚拟化)

```bash
# 启用 (NIC + IOMMU)
# BIOS 启用: VT-d / IOMMU + SR-IOV
echo 8 | sudo tee /sys/class/net/ens1f0/device/sriov_numvfs    # 创建 8 个 VF

# 查看
lspci | grep -i ethernet                          # PF + VF
ip link show

# 关键:
- 直通虚拟机 (低延迟 / 接近线速)
- K8s SR-IOV CNI (云原生)
- NUMA 亲和必 (VF 要绑本 socket)
```

### 4.3 DPDK / 内核旁路

```
DPDK = Data Plane Development Kit
- 用户态驱动 (绕过内核)
- Poll Mode Driver (PMD)
- 大页 + CPU 隔离 + IRQ 绑核

适用场景:
  vSwitch (OVS-DPDK)
  NFV (vCMTS / 5G UPF)
  低延迟金融
  防火墙 / DPI

替代 / 互补:
  XDP (eBPF 在内核)             ⭐ 灵活, 内核维护友好
  AF_XDP (kernel ↔ user 0-copy)  
  io_uring (异步 IO)
  
要求:
  - 大页 (HugePages)
  - 绑核 (isolcpus 内核参数)
  - IOMMU 直通
```

### 4.4 RDMA (RoCE / InfiniBand)

```
RoCEv2  以太网上跑 RDMA (UDP 封装)
InfiniBand  专用网络 (低延迟, AI/HPC 主流)
iWARP    TCP 上 RDMA (已边缘)

部署:
  # Mellanox OFED 驱动
  sudo apt install mlnx-ofed-all
  
  # 启用 RoCE
  sudo mlxconfig -d /dev/mst/mt4123_pciconf0 set LINK_TYPE_P1=2   # 2=Ethernet
  
  # 测试
  ib_send_bw / ib_send_lat / ib_write_bw
  
延迟:
  IB:    ~0.6 μs (RDMA write)
  RoCE:  ~1.5 μs
  TCP:   ~10-50 μs

详见 03 网络 03 高级
```

### 4.5 网络 Offload

```
TSO / GSO / GRO         TCP 分段卸载 (传统)
LRO                     大接收
RSS                     多队列 (核分散)
VXLAN/NVGRE Offload     封装卸载 (云)
TLS Offload             加密卸载 (HTTPS)
crypto offload          IPsec
hardware GRO (TC)        高级
P4 / programmable        DPU (BlueField / IPU)

查看:
ethtool -k eth0                                  # 当前
ethtool -K eth0 tso on lro on gso on             # 启用
```

## 五、BMC 深度

### 5.1 BMC 功能矩阵

```
基础:
  ☐ 远程开关机 / 重启 / 强制断电
  ☐ KVM Over IP (虚拟显示器 + 键鼠)
  ☐ Virtual Media (虚拟挂载 ISO/USB)
  ☐ SOL (Serial Over LAN, 串口重定向)
  ☐ Sensor 监控 (温度 / 风扇 / 电压)
  ☐ SEL (System Event Log)
  ☐ 用户/权限管理
  ☐ 时间同步 (NTP)

进阶:
  ☐ 固件升级 (in-band / out-of-band)
  ☐ 自动恢复 (Watchdog)
  ☐ 电源策略 (掉电后行为)
  ☐ 安全启动 / TPM
  ☐ Redfish API ⭐
  ☐ IPMI 2.0 (老但通用)
  ☐ SNMP Trap
```

### 5.2 厂商 BMC

| 厂商 | BMC 名称 | 默认 IP | CLI |
|:---|:---|:---|:---|
| Dell | iDRAC 9/10 | 192.168.0.120 | racadm |
| HPE | iLO 5/6 | DHCP | hponcfg + ilorest |
| Lenovo | XCC | 192.168.70.125 | OneCli |
| Supermicro | IPMI/Redfish | DHCP | SUM / SMCIPMITool |
| 华为 | iBMC | 192.168.2.100 | iBMA / Toolkit-SP |
| 浪潮 | ISBMC | 100.2.2.81 | ISCM / iSM |
| 中科曙光 | Tcsm | 静态 | Tcsm |
| 新华三 | HDM | DHCP | HDM-CLI |

### 5.3 Redfish 实战

```bash
# 标准 RESTful API (替代 IPMI 2.0)
curl -k -u admin:password https://<bmc>/redfish/v1/Systems/1
curl -k -u admin:password https://<bmc>/redfish/v1/Chassis/1/Thermal
curl -k -u admin:password https://<bmc>/redfish/v1/Chassis/1/Power

# 重启
curl -k -u admin:password -X POST \
  -H "Content-Type: application/json" \
  -d '{"ResetType":"ForceRestart"}' \
  https://<bmc>/redfish/v1/Systems/1/Actions/ComputerSystem.Reset

# 优势:
- 厂商无关 (DMTF 标准)
- HTTPS + JSON
- 与 Kubernetes 兼容好 (Metal3, Ironic)
```

### 5.4 IPMI (老但通用)

```bash
ipmitool -I lanplus -H <bmc> -U admin -P pwd power status
ipmitool ... power on/off/cycle
ipmitool ... sel list                             # 系统事件
ipmitool ... sensor list                          # 传感器
ipmitool ... sol activate                         # 串口重定向
ipmitool ... mc info                              # BMC 信息
```

## 六、固件层次

```
[CPLD]   主板可编程逻辑 (上电时序, 风扇控制)
   ↓
[BMC]    管理芯片 (独立, 主机断电仍工作)
   ↓
[BIOS/UEFI] 主机固件 (POST + 引导)
   ↓
[Option ROM]  RAID/NIC/NVMe/GPU 卡上 ROM
   ↓
[OS Driver]   内核驱动

升级顺序:
  1. BMC (先, 之后 BIOS 升级稳)
  2. BIOS / UEFI
  3. CPLD (慎)
  4. RAID / NIC / NVMe / GPU VBIOS

详见 18 硬件测试 03 高级
```

## 七、GPU 入门

### 7.1 NVIDIA GPU 数据中心系列

```
Tesla 时代 → Volta → Turing → Ampere → Hopper → Blackwell → Rubin

主流型号:
  V100 (Volta, 32GB HBM2)               已退役
  T4 (Turing, 16GB GDDR6, 70W)          推理 (老但稳)
  A100 (Ampere, 40/80GB HBM2e, 400W)    上一代训练旗舰
  H100 (Hopper, 80GB HBM3, 700W)        当前训练旗舰 ⭐
  H200 (Hopper Refresh, 141GB HBM3e)    2024+
  L40S (Ada, 48GB GDDR6, 350W)          通用 + AI 推理
  B100/B200 (Blackwell, 192GB HBM3e)    2024-2025 ⭐
  GB200 (Grace + Blackwell, NVL72)      整机柜
  GB300 NVL72 (Ultra)                    2025
  Rubin / Rubin Ultra                    2026-2027

形态:
  PCIe (标卡)         350-400W, 通用机
  SXM (HGX 基板)      700-1000W ⭐ AI 训练首选 (NVLink 互联)
```

### 7.2 拓扑

```bash
# 看 GPU
nvidia-smi
nvidia-smi -q                                    # 详细
nvidia-smi topo -m                                # 拓扑矩阵 ⭐

# 典型 8 卡 H100 HGX 拓扑:
- 8× H100 SXM5 通过 4× NVSwitch 全互联
- NVLink 4.0: 单链 50 GB/s, 总 900 GB/s/GPU
- CPU ↔ GPU: PCIe Gen5 x16
- NIC: 4-8 张 IB/RoCE 400G

工具:
  nvidia-smi
  nvtop                                          # 类 htop
  DCGM (Data Center GPU Manager)                  详见 18 高级
```

### 7.3 驱动 + CUDA

```bash
# 驱动版本
nvidia-smi | head -3                              # 顶部显示

# 安装 (Ubuntu 22.04 示例)
sudo apt install nvidia-driver-535-server
# 或 .run 包

# CUDA Toolkit
sudo apt install cuda-toolkit-12-4

# 验证
nvidia-smi
nvcc --version

# 持久模式 (减少首次启动延迟)
sudo nvidia-smi -pm 1

# MIG (Multi-Instance GPU, A100/H100)
sudo nvidia-smi mig -lgip                         # 列出实例配置
sudo nvidia-smi mig -cgi 19 -C                    # 创建实例
```

## 八、多路 / 大内存配置

```
4 路 / 8 路:
  Intel Xeon SP 4S/8S (大型 ERP / SAP HANA / 内存 DB)
  优势: 单机 TB+ 内存 + 多 socket NUMA
  劣势: 价格 + 跨 socket 延迟

大内存:
  单机 12TB+ DDR5 (4 路 EPYC Turin + 满 DIMM)
  CXL Memory 扩展 (PCIe Gen5)
  SAP HANA / Oracle RAC 单机

满 PCIe:
  Gen5 x16 × 5-8 槽 + GPU/NIC/NVMe 混合
  PCIe Switch (Broadcom PEX / Microchip)
  Bifurcation 拆分 (x16 → 2× x8)
```

## 九、Checklist

```
CPU:
☐ Sapphire/Granite/Emerald + Genoa/Bergamo/Turin
☐ AVX-512/AMX/SVE 指令集
☐ NUMA + 绑核 + governor
☐ TDX/SEV/CCA 机密计算
☐ 国密加速 (鲲鹏/海光)

内存:
☐ DDR5 通道 + MRDIMM
☐ ECC 类型 (SECDED/Chipkill/On-die)
☐ CXL Memory + NUMA
☐ HBM (GPU)
☐ MLC + STREAM 测试

存储:
☐ NVMe 队列 + IRQ 绑核
☐ io_uring / SPDK
☐ RAID 硬件 vs 软件 (mdadm/ZFS/Ceph)
☐ 存储分层 (HBM→NVMe→SSD→HDD→Tape)

网络:
☐ 100/400G CX-7 / E810
☐ SR-IOV + IOMMU
☐ DPDK + XDP + io_uring
☐ RoCE / IB / RDMA
☐ Offload (TSO/GSO/LRO/RSS/TLS)

BMC:
☐ Redfish API ⭐
☐ IPMI 2.0
☐ 厂商 CLI (racadm/hponcfg/OneCli/iBMA/ISBMC)
☐ KVM/SOL/Virtual Media

固件:
☐ BMC → BIOS → CPLD → Option ROM
☐ 升级顺序 + 备份

GPU 入门:
☐ H100/H200/B200/L40S
☐ PCIe vs SXM
☐ NVLink + NVSwitch
☐ 驱动 + CUDA + MIG
☐ DCGM (见 18)
```

## 十、推荐栈

```
CPU 调优:    cpupower + turbostat + numactl + lstopo + perf
内存:        Intel MLC + STREAM + cxl-cli + ndctl
存储:        fio + nvme-cli + io_uring + storcli/perccli/ssacli + zpool
网络:        ethtool + Mellanox MFT (mlxconfig/mlxlink) + DPDK + perftest
BMC:        Redfish API ⭐ + ipmitool + racadm/hponcfg/OneCli/iBMA
GPU:        nvidia-smi + nvtop + DCGM + CUDA + nvidia-bug-report.sh
固件:        Lenovo OneCli ⭐ + Dell DSU + HPE SUM + nvme + mlxfwmanager
压测/烤机:   stress-ng + memtester + fio + iperf3 + gpu-burn (见 18 章)
```

> 📖 **核心判断**：服务器进阶 = **CPU 深度(架构/AMX/NUMA/governor) + 内存深度(DDR5/CXL/HBM/MLC) + 存储深度(NVMe 队列/RAID/分层) + 网络深度(SR-IOV/DPDK/RDMA/Offload) + BMC 深度(Redfish/IPMI/厂商 CLI) + 固件层次(CPLD→BMC→BIOS→Option ROM) + GPU 入门(H100/SXM/NVLink/CUDA) + 多路与大内存配置**。从"会看 BOM"升级到"会调性能 + 会用 Redfish + 会装 GPU + 会理解 NUMA/SR-IOV"。**调优口诀: 绑核(numactl) + 满通道内存 + NVMe IRQ 亲和 + NIC SR-IOV + 关 NUMA balancing(高负载) + 持久模式 GPU。详细测试 / 烤机详见 [18 硬件测试](../../18_硬件测试/02_进阶/README.md)。**
