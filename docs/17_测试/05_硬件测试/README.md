# 服务器硬件测试

> 服务器硬件测试 = **组件检查 (CPU/内存/磁盘/RAID/NIC/GPU/PSU/风扇/BMC) + 固件升级 (BIOS/BMC/RAID/HBA/NIC/SSD/GPU) + 压力测试 (CPU/MEM/DISK/NET/GPU/整机) + 兼容性 (HCL) + 可靠性 (老化/温度/震动) + PXE 自动化流水线 + 厂商工具 (XClarity/iDRAC/iLO/iBMC) + 国产化 (鲲鹏/海光/飞腾)**。面向数据中心交付/服务器测试工程师，覆盖从板卡 POST 到整机 72h 烤机的完整链路。

## 一、核心理念

```
测试分层:
  组件级    (CPU/MEM/SSD/NIC 单点)
  整机级    (BIOS+OS+负载组合)
  集群级    (网络互联/HPC/AI 训练)

测试阶段:
  Incoming  来料检验 (供应商)
  Burn-in   老化 (24-72h 烤机)
  Pre-deploy 上架前 (固件 + 配置基线)
  Production 生产中 (DCIM 监控)
  EOL       退役 (数据擦除 + 资产回收)

KPI:
  DOA (Dead on Arrival) < 0.5%
  AFR (Annual Failure Rate) < 2%
  MTBF / MTTR 数据中心级
  烤机通过率 > 99%
```

## 二、组件检查（清单 + 工具）

### 2.1 整机清单 (Inspection)

```bash
# 一键体检
sudo dmidecode -t system          # 整机 SN / 型号
sudo dmidecode -t baseboard        # 主板
sudo dmidecode -t bios             # BIOS 版本
sudo dmidecode -t processor        # CPU
sudo dmidecode -t memory           # 内存
sudo dmidecode -t chassis          # 机箱

# lshw 全景
sudo lshw -short
sudo lshw -html > hw.html

# inxi 友好
sudo inxi -Fxz

# hwinfo (SUSE)
sudo hwinfo --short
```

### 2.2 CPU 检查

```bash
lscpu                              # 整体 (核心/线程/微架构/MHz)
cat /proc/cpuinfo | grep "model name" | head -1
cat /proc/cpuinfo | grep "flags" | head -1   # 指令集 (avx512/vnni/amx)

# 微码版本
dmesg | grep microcode
cat /proc/cpuinfo | grep microcode | head -1

# CPU 拓扑
lscpu -e                           # 每核 socket/node/online
numactl -H                         # NUMA 拓扑
lstopo-no-graphics                 # hwloc 树形图

# 温度 + 频率
sensors                            # lm-sensors
turbostat                          # Intel
cpupower frequency-info            # 调频
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# MCE (Machine Check Exception) - 硬件错误
sudo mcelog --client
journalctl -k | grep -i mce

# 检查项:
☐ CPU 数量 + 型号一致
☐ 全核心 online
☐ 微码最新
☐ NUMA 平衡
☐ 无 MCE / Correctable Error
☐ 频率达标 (Turbo)
☐ 温度 < 80℃ (空载)
```

### 2.3 内存检查

```bash
# 拓扑
sudo dmidecode -t memory | grep -E "Size|Speed|Locator|Manufacturer|Part Number"
sudo dmidecode -t 17 | less        # DIMM 详细

# 容量 + Speed 必查:
☐ 通道平衡 (Per Socket 6/8/12 通道全插)
☐ 速率达标 (DDR4-3200 / DDR5-4800/5600)
☐ ECC 启用 (服务器必)
☐ 厂商 (Samsung/Hynix/Micron 一致性)

# ECC 错误监控
sudo edac-util -v                  # EDAC (内核 ECC)
sudo edac-util -s
sudo journalctl -k | grep -i "edac\|mce"
sudo rasdaemon -r                  # RAS daemon (推荐) ⭐

# MemTest86 / MemTest86+ (脱机)
# - 启动 USB / PXE
# - 4-8 pass 完整 (约 24h, 大内存)
# - 必抓: Address Test / Pattern / Random

# 内存带宽
stream                             # STREAM benchmark
mlc                                # Intel Memory Latency Checker

# 检查项:
☐ 总容量 = 标称
☐ 通道平衡 (NUMA balanced)
☐ Speed = 标称 (BIOS XMP/DOCP 关)
☐ ECC enabled + 0 错误
☐ MemTest86 0 Fail
☐ STREAM Triad 接近理论值 (DDR5 4800 单通 ~38GB/s)
```

### 2.4 磁盘 / SSD / NVMe

```bash
# 拓扑
lsblk -o NAME,SIZE,ROTA,MODEL,SERIAL,TRAN,VENDOR
ls -la /dev/disk/by-id/
nvme list                          # NVMe 专用
sudo smartctl --scan

# SMART 全量
sudo smartctl -a /dev/sda          # SATA/SAS
sudo smartctl -a /dev/nvme0        # NVMe (注意是字符设备)
sudo nvme smart-log /dev/nvme0
sudo nvme id-ctrl /dev/nvme0       # 控制器信息

# 关键 SMART 指标:
☐ Reallocated_Sector_Ct = 0
☐ Current_Pending_Sector = 0
☐ Offline_Uncorrectable = 0
☐ Power_On_Hours / Power_Cycle_Count (二手警惕)
☐ Wear_Leveling_Count / Percentage_Used < 80% (SSD)
☐ Media_Wearout_Indicator
☐ Temperature < 60℃
☐ NVMe: Percentage_Used / Available_Spare / Critical_Warning = 0

# Self Test
sudo smartctl -t short /dev/sda    # 2 min
sudo smartctl -t long /dev/sda     # 数小时
sudo nvme device-self-test /dev/nvme0n1 -s 1   # short
sudo nvme self-test-log /dev/nvme0n1

# 坏块扫描
sudo badblocks -wsv /dev/sdX       # 破坏性 (新盘可用)
sudo badblocks -nsv /dev/sdX       # 非破坏性

# fio 性能验证 (见压测章)

# 检查项:
☐ 所有盘识别 (容量/型号一致)
☐ SMART Health = PASSED
☐ Reallocated/Pending = 0
☐ 温度 < 60℃
☐ Self-test 通过
☐ NVMe Critical_Warning = 0
```

### 2.5 RAID / HBA

```bash
# LSI / Broadcom MegaRAID
sudo storcli /c0 show all          # 控制器
sudo storcli /c0/eall/sall show all # 所有物理盘
sudo storcli /c0/vall show all      # 所有 VD
sudo storcli /c0 show events        # 事件日志

# 老的 megacli
sudo megacli -AdpAllInfo -aALL
sudo megacli -PDList -aALL
sudo megacli -LDInfo -Lall -aALL

# Dell PERC
sudo perccli /c0 show all

# HPE Smart Array
sudo ssacli ctrl all show config detail

# SAS3 HBA
sudo sas3ircu LIST
sudo sas3ircu 0 DISPLAY

# 检查项:
☐ 固件版本一致
☐ Battery / BBU 健康 (写缓存策略)
☐ RAID 级别 (RAID1/10/5/6) + Stripe Size 合规
☐ 0 故障盘 + 0 重建中
☐ 写缓存策略 (Write Back + BBU) 一致
☐ 没有 Foreign Config 残留
```

### 2.6 网卡 (NIC)

```bash
# 列表
ip link
sudo ethtool -i eth0               # driver / firmware / bus-info
sudo lspci | grep -i ether
sudo lshw -class network

# 速率 + 协商
sudo ethtool eth0                  # Speed/Duplex/Auto/MDI
sudo ethtool -S eth0               # 统计 (drops/errors/crc)
sudo ethtool -k eth0               # offload (LRO/GRO/TSO)
sudo ethtool -g eth0               # ring buffer
sudo ethtool -l eth0               # queue
sudo ethtool -m eth0               # SFP/QSFP 模块信息

# 链路诊断
sudo mii-tool eth0
sudo ip -s link show eth0          # tx/rx 统计 + 错误

# 多队列 / NUMA
ls /sys/class/net/eth0/queues/
cat /proc/interrupts | grep eth0

# 25/100G 高速
mlnx_qos -i eth0                   # Mellanox
sudo mst start && mst status        # ConnectX 工具
sudo mlxfwmanager                   # Mellanox 固件
sudo mstflint -d <pci> q            # 固件查询

# 检查项:
☐ Speed = 标称 (1G/10G/25G/100G)
☐ Duplex = Full
☐ Link = up
☐ Driver / Firmware 最新
☐ 0 RX/TX errors / drops / CRC
☐ SFP 厂商 + DDM (温度/电压/光功率)
☐ 多队列 = CPU 核心数
☐ 中断 IRQ 绑核 (NUMA 亲和)
```

### 2.7 GPU

```bash
# NVIDIA
nvidia-smi                         # 概览
nvidia-smi -q                      # 详细
nvidia-smi nvlink --status         # NVLink
nvidia-smi topo -m                 # 拓扑 (NVLink/PCIe/SYS)
nvidia-smi -q -d ECC               # ECC 错误
nvidia-smi -q -d TEMPERATURE
nvidia-smi -q -d POWER
nvidia-smi -q -d CLOCK             # 时钟降频检查

# DCGM (Datacenter GPU Manager) ⭐
sudo systemctl start nvidia-dcgm
dcgmi discovery -l                 # 列 GPU
dcgmi diag -r 4                    # 全诊断 (Level 4 最全, 数十分钟)
dcgmi diag -r 3                    # 中等 (生产前)
dcgmi health --check-all           # 健康
dcgm-exporter                       # Prometheus

# Xid 错误 (硬件级)
dmesg | grep -i nvrm.*xid
journalctl | grep -i xid
# Xid 列表参考: NVIDIA Xid Error Reference

# 国产 GPU
hccn_tool -i 0 -info               # 华为昇腾 (Ascend)
npu-smi info                       # 昇腾
mxsmi                              # 摩尔线程
hl-smi                             # Habana Gaudi (Intel)

# 检查项:
☐ GPU 数量 + 型号一致
☐ ECC enabled + 0 Uncorrectable
☐ 温度 < 85℃ (空载 < 50℃)
☐ Persistence mode ON
☐ 时钟达标 (无 SW Power Cap / HW Throttle)
☐ PCIe Gen 4/5 + x16
☐ NVLink up (DGX/H100)
☐ DCGM diag -r 4 PASS
☐ 0 Xid 错误
```

### 2.8 PSU / 风扇 / 温度

```bash
# IPMI
sudo ipmitool sensor list           # 所有传感器
sudo ipmitool sdr type Fan
sudo ipmitool sdr type Temperature
sudo ipmitool sdr type "Power Supply"
sudo ipmitool sel list              # 系统事件日志
sudo ipmitool sel elist             # 详细

# 厂商工具
sudo OneCli inventory               # Lenovo XCC
sudo racadm getsensorinfo           # Dell
sudo hponcfg                        # HPE iLO
sudo ipmi-fru                       # FRU 信息 (PN/SN)

# lm-sensors
sudo sensors-detect
sensors

# 检查项:
☐ 双 PSU 在位 + 同型号 + 同 FW
☐ AC Input OK / DC Output OK
☐ 风扇全部转 + RPM 在范围
☐ CPU/GPU/HDD/Ambient 温度正常
☐ SEL 0 Critical (检查后清空: ipmitool sel clear)
```

### 2.9 BMC / IPMI

```bash
# BMC 信息
sudo ipmitool mc info
sudo ipmitool lan print 1           # BMC IP
sudo ipmitool fru list              # FRU (机器序列号)

# 远程
ipmitool -I lanplus -H <bmc-ip> -U admin -P xxx chassis status
ipmitool -I lanplus -H <bmc-ip> -U admin -P xxx sol activate   # 串口重定向

# Redfish (现代 ⭐)
curl -k -u admin:xxx https://<bmc>/redfish/v1/Systems/1
curl -k -u admin:xxx https://<bmc>/redfish/v1/Chassis/1/Thermal
curl -k -u admin:xxx https://<bmc>/redfish/v1/Managers/1/LogServices/SEL/Entries

# 检查项:
☐ BMC 固件最新
☐ BMC IP 在管理网段 + 可达
☐ Admin 密码已改 (默认弱口令禁)
☐ SOL (Serial over LAN) 启用
☐ Redfish 启用 + HTTPS
☐ NTP 同步 (日志时间)
☐ SNMP/告警转发到 NMS
```

## 三、固件升级 (Firmware)

### 3.1 固件清单 (一台 2U 服务器典型)

```
☐ BIOS / UEFI
☐ BMC / iDRAC / iLO / XCC / iBMC
☐ ME / PSP (Intel ME / AMD PSP)
☐ CPLD
☐ RAID 控制器 (LSI/PERC/SmartArray)
☐ HBA
☐ NIC (Intel/Mellanox/Broadcom)
☐ SSD/NVMe 固件
☐ HDD 固件 (老盘)
☐ GPU VBIOS (NVIDIA)
☐ PSU 固件 (大型 PSU 有)
☐ Backplane Expander
☐ NVMe Switch (NVMe-oF 系统)
☐ Optical 模块 (DDM 固件)
```

### 3.2 厂商一键升级工具 ⭐

```
Lenovo:
  OneCLI ⭐ / XClarity Essentials
  XClarity Administrator (集中)
  UpdateXpress System Pack (UXSP)
  
Dell:
  iDRAC RACADM ⭐
  Dell EMC OpenManage Enterprise
  Dell System Update (DSU)
  Lifecycle Controller
  
HPE:
  iLO REST / hponcfg
  HPE OneView (集中)
  Smart Update Manager (SUM) ⭐
  Service Pack for ProLiant (SPP)

Supermicro:
  SUM (Supermicro Update Manager)
  IPMICfg / SMCIPMITool
  SuperDoctor

华为:
  iBMA / iBMC + UEFI 包
  eSight (集中)
  FusionDirector / Toolkit-SP ⭐
  
浪潮:
  ISBMC / NF8260 工具集
  浪潮服务器管理平台 (ISCM)
  
中科曙光:
  Tcsm / Sugon Manager
  
新华三 (H3C):
  HDM / OneStor
```

### 3.3 实战流程

```bash
# 1. 现状采集
sudo dmidecode -s bios-version
sudo ipmitool mc info | grep "Firmware Revision"
sudo storcli /c0 show | grep -i firmware
sudo ethtool -i eth0 | grep firmware
sudo nvme id-ctrl /dev/nvme0 | grep fr
sudo nvidia-smi --query-gpu=vbios_version --format=csv

# 2. 比对推荐版本 (厂商 HCL)
# 通常推荐: Production Baseline / Latest Stable
# 严禁 Beta / Tech Preview 上生产

# 3. 升级 (Lenovo XCC 示例)
sudo OneCli update flash --uselocalimage --imm <ip> --user <u> --password <p>

# 3.1 Dell iDRAC + DSU
sudo dsu --apply-upgrades
sudo dsu --inventory                  # 当前
sudo dsu --preview-upgrades            # 预览

# 3.2 HPE SPP
mount /dev/sr0 /mnt
cd /mnt && ./launch_sum.sh

# 3.3 NVMe (通用)
sudo nvme fw-download /dev/nvme0n1 -f firmware.bin
sudo nvme fw-activate /dev/nvme0n1 -a 3 -s 1
sudo nvme reset /dev/nvme0n1
sudo nvme id-ctrl /dev/nvme0 | grep fr

# 3.4 Mellanox NIC
sudo mlxfwmanager --query
sudo mlxfwmanager -i firmware.bin -u
# 或: sudo mstflint -d <pci> -i fw.bin b

# 3.5 NVIDIA GPU VBIOS (慎)
sudo nvflash --save backup.rom        # 备份
sudo nvflash new_vbios.rom            # 慎重! 操作错 → 砖

# 4. 重启 + 验证
sudo reboot
# 验证版本 + 健康
```

### 3.4 PXE + 自动化升级流水线 ⭐

```
适用: 批量 (10-1000 台) 上架前
背景: 你在联想就这么干的 (PXE + Python + MySQL)

流水线:
  1. DHCP + TFTP + HTTP (PXE Server)
  2. WinPE / RHEL Live / Ubuntu Live boot
  3. 自动执行: 
     - 采集硬件指纹 (SN/MAC/CPU/MEM/Disk)
     - 入库 MySQL/PostgreSQL
     - 比对 BIOS/BMC/NIC FW 版本
     - 自动 OneCli/RACADM/SUM 升级
     - 重启 + 复核
     - 上报状态 → Web Dashboard
  4. 失败告警 + 人工介入
  
工具栈:
  PXE:        pxelinux / iPXE ⭐ / GRUB-PXE
  DHCP:       dnsmasq / ISC dhcpd
  TFTP:       tftpd-hpa / atftpd
  HTTP:       nginx
  装机 OS:    Ubuntu Live / Cobbler / FAI / Razor
  装机平台:   Foreman ⭐ / Cobbler / Razor / MAAS (Canonical) ⭐
  自动化:     Ansible / Salt / Python 脚本
  CMDB:       NetBox / Ralph / 自研
  Web UI:     Flask / Django / FastAPI

iPXE 示例:
#!ipxe
dhcp
kernel http://server/vmlinuz initrd=initrd.img boot=live noeject \
  fetch=http://server/filesystem.squashfs script=http://server/burn.sh
initrd http://server/initrd.img
boot

burn.sh:
#!/bin/bash
SN=$(dmidecode -s system-serial-number)
curl -X POST http://cmdb/api/inventory -d @<(lshw -json)
# 升级 + 烤机...
```

### 3.5 红线 + 注意事项

```
☐ 备份 BIOS/BMC 配置 (RACADM export / ipmitool raw 导出)
☐ 升级窗口避开业务高峰
☐ 灰度: 1 台 → 10 台 → 100 台
☐ 升级后 ≥ 24h 观察期
☐ 单台升级: BMC → BIOS → 其他 (BMC 先)
☐ 双 PSU 不要同时拔
☐ 升级失败 → 厂商 Recovery (CMOS 跳线 / DC Power Reset / Recovery USB)
☐ GPU VBIOS 慎重 (容易砖, 提前备份)
☐ 升级期间禁止断电
☐ 升级日志归档 (审计)
```

## 四、压力测试 (Stress Test)

### 4.1 CPU 压测

```bash
# stress-ng (现代, 推荐) ⭐
stress-ng --cpu $(nproc) --timeout 30m --metrics-brief
stress-ng --cpu $(nproc) --cpu-method matrixprod --timeout 1h
stress-ng --matrix 0 --timeout 1h        # 矩阵运算 (AVX)

# 老 stress
stress -c $(nproc) -t 3600

# Linpack / HPL ⭐ (HPC 黄金标准, 算 FLOPS)
# Intel MKL Linpack
/opt/intel/mkl/benchmarks/linpack/runme_intel64_static

# HPL (OpenMPI)
mpirun -np <核数> ./xhpl

# Geekbench (CLI)
geekbench6 --upload

# Phoronix Test Suite ⭐
phoronix-test-suite benchmark pts/cpu
phoronix-test-suite benchmark pts/compress-7zip
phoronix-test-suite benchmark pts/sysbench

# y-cruncher (Pi 计算, CPU + RAM 综合)
./y-cruncher bench 1b

# sysbench
sysbench cpu --cpu-max-prime=100000 --threads=$(nproc) run

# 监控 (另开窗口)
turbostat -i 5                       # Intel 频率/温度
sensors -A                            # 温度
mpstat -P ALL 5                       # 每核负载
watch -n1 'cat /proc/cpuinfo | grep MHz'

# 检查项:
☐ 全核 100% 负载 1h+
☐ 温度 < TjMax (Intel 90-100℃)
☐ 无降频 (检查 turbostat)
☐ 0 MCE
☐ Linpack 接近理论值 (90%+)
```

### 4.2 内存压测

```bash
# stress-ng VM
stress-ng --vm 8 --vm-bytes 80% --vm-keep --timeout 24h
stress-ng --vm $(nproc) --vm-bytes 4G --vm-method all -t 1h

# memtester (在线, OS 运行时)
sudo memtester 16G 5                  # 16G x 5 pass

# MemTest86 / MemTest86+ (脱机, 全内存) ⭐
# - U 盘启动 / PXE
# - 4-8 pass 大内存可能 24-72h
# - 必抓: Address Test / Walking 1's / Random / Block Move

# Intel MLC (Memory Latency Checker)
sudo mlc                              # 全套
sudo mlc --bandwidth_matrix            # NUMA 带宽
sudo mlc --latency_matrix              # NUMA 延迟

# STREAM (经典)
gcc -fopenmp -O3 stream.c -o stream
OMP_NUM_THREADS=$(nproc) ./stream

# 检查项:
☐ MemTest86 0 Error (4+ pass)
☐ stress-ng VM 24h 0 OOM / 0 segfault
☐ ECC 错误 = 0 (rasdaemon -r)
☐ STREAM Triad 接近理论 (DDR5 4800 单通 ~38GB/s, 8 通道 ~250GB/s+)
☐ MLC 延迟 < 100ns (本地) / < 150ns (远端 NUMA)
```

### 4.3 磁盘 / IO 压测

```bash
# fio ⭐ (黄金标准)
# 4K 随机读 (IOPS)
fio --name=randread --rw=randread --bs=4k --iodepth=64 --numjobs=4 \
    --runtime=300 --time_based --group_reporting \
    --direct=1 --ioengine=libaio --filename=/dev/nvme0n1

# 4K 随机写
fio --name=randwrite --rw=randwrite --bs=4k --iodepth=64 --numjobs=4 \
    --runtime=300 --time_based --group_reporting \
    --direct=1 --ioengine=libaio --filename=/dev/nvme0n1

# 顺序读写 (带宽)
fio --name=seqread --rw=read --bs=1M --iodepth=32 --numjobs=1 \
    --runtime=300 --time_based --direct=1 --filename=/dev/nvme0n1

# 70R/30W 混合 (生产常用)
fio --name=mix --rw=randrw --rwmixread=70 --bs=4k --iodepth=64 \
    --numjobs=4 --runtime=24h --time_based --group_reporting \
    --direct=1 --ioengine=libaio --filename=/dev/nvme0n1

# dd (粗略, 不推荐做压测)
dd if=/dev/zero of=/tmp/test bs=1M count=10240 oflag=direct status=progress

# iozone (老)
iozone -a -g 4G

# 监控
iostat -mx 5
nvme smart-log /dev/nvme0n1 | grep -E "temperature|critical|used"
sar -d 5

# 检查项 (SSD/NVMe):
☐ 顺序读 接近标称 (PCIe Gen4 NVMe ~7000 MB/s)
☐ 顺序写 接近标称
☐ 4K 随机读 > 500K IOPS (企业 NVMe)
☐ 4K 随机写 > 100K IOPS (企业 NVMe)
☐ 24h 持续无 critical_warning
☐ 温度 < 70℃
☐ SMART Reallocated = 0
```

### 4.4 网络压测

```bash
# iperf3 (基线) ⭐
# Server:
iperf3 -s

# Client (单流)
iperf3 -c <server> -t 60 -P 1
# 多流 (满速 25G/100G 必)
iperf3 -c <server> -t 60 -P 16

# 反向
iperf3 -c <server> -R                # Server → Client
iperf3 -c <server> --bidir            # 双向

# UDP (丢包/抖动)
iperf3 -c <server> -u -b 10G -t 60

# ethr (微软, 现代多协议) ⭐
ethr -s
ethr -c <server> -t b -d 60s -p tcp

# netperf
netperf -H <server> -t TCP_RR        # 短连接
netperf -H <server> -t TCP_STREAM

# Mellanox 专用 (RDMA)
ib_send_bw -d mlx5_0 <server>        # IB/RoCE 带宽
ib_send_lat                          # 延迟

# NCCL 测试 (AI / GPU 互联) ⭐
mpirun -np 8 ./all_reduce_perf -b 8 -e 256M -f 2 -g 1

# 长跑 (24-72h, 抓丢包/CRC)
iperf3 -c <server> -t 86400 -P 8

# 监控
sar -n DEV 5
ethtool -S eth0 | grep -i error
ip -s link show eth0

# 检查项:
☐ 单流 = 链路 80%+ (10G ~9.4Gbps / 25G ~23Gbps / 100G ~94Gbps)
☐ 多流 (16+) 满速
☐ 双向同时满速
☐ UDP 丢包 < 0.01%
☐ 24h 长跑 0 CRC / 0 drop
☐ NCCL allreduce 接近理论 (NVLink/IB)
```

### 4.5 GPU 压测

```bash
# NVIDIA DCGM Diag (推荐) ⭐
sudo dcgmi diag -r 4                  # Level 4 全面 (含 stress)
                                       # 检测: GPU/PCIe/NVLink/Memory/Thermal/Software

# gpu-burn (CUDA 暴力压测) ⭐
git clone https://github.com/wilicc/gpu-burn
cd gpu-burn && make
./gpu_burn -d 3600                    # 1h
./gpu_burn -tc 7200                    # Tensor Core, 2h

# CUDA Samples 自带 bandwidthTest
/usr/local/cuda/extras/demo_suite/bandwidthTest
/usr/local/cuda/extras/demo_suite/deviceQuery

# nccl-tests ⭐ (多卡互联)
./build/all_reduce_perf -b 8 -e 8G -f 2 -g 8

# HPL (GPU 版)
xhpl_cuda

# 长跑 (24-72h 烤机)
nohup ./gpu_burn -d 259200 &           # 72h

# 监控
nvidia-smi dmon -s pucvmet -d 1        # 每秒打印
dcgm-exporter + Prometheus + Grafana
watch -n1 'nvidia-smi --query-gpu=temperature.gpu,power.draw,utilization.gpu --format=csv'

# 检查项:
☐ GPU 利用 100% 持续
☐ 温度 < 85℃ (H100 < 75℃ 风冷)
☐ 0 ECC Uncorrectable
☐ 0 Xid 错误 (dmesg)
☐ 无降频 (clocks.gr 持续高频)
☐ 0 OOM / 0 driver hang
☐ DCGM diag -r 4 PASS
☐ NCCL allreduce 接近理论
```

### 4.6 整机烤机 (Burn-in 24-72h) ⭐

```bash
# 同时跑: CPU + 内存 + 磁盘 + 网卡 + GPU
# 验收前必跑 72h

# 综合方案 1: stress-ng all-in-one
stress-ng --cpu $(nproc) --io 4 --vm 4 --vm-bytes 75% \
  --hdd 4 --hdd-bytes 10G --metrics --timeout 72h

# 方案 2: 分进程
tmux new -d -s cpu "stress-ng --cpu \$(nproc) -t 72h"
tmux new -d -s mem "stress-ng --vm 8 --vm-bytes 80% -t 72h"
tmux new -d -s fio "fio --name=mix --rw=randrw --bs=4k --iodepth=64 \
  --numjobs=4 --runtime=72h --time_based --filename=/dev/nvme0n1"
tmux new -d -s net "iperf3 -c <peer> -t 259200 -P 8"
tmux new -d -s gpu "./gpu_burn -d 259200"

# 方案 3: Phoronix Test Suite (集成 + 报告)
phoronix-test-suite batch-benchmark pts/server

# 方案 4: HPL Linpack (HPC/AI 整机)
mpirun -np <核数> ./xhpl
# HPL.dat 配置: N=内存 80% / NB=192 / P*Q=核数

# 监控 (集中)
- node_exporter + Prometheus + Grafana ⭐
- IPMI sensor 历史 (ipmitool sensor + cron)
- rasdaemon -r (RAS 错误)
- DCGM exporter (GPU)
- smartmontools (磁盘)

# 烤机通过条件:
☐ 72h 0 系统挂起 / 0 panic
☐ 0 MCE / 0 ECC Uncorrectable
☐ 0 XID GPU 错误
☐ 0 磁盘 SMART 新增 reallocated
☐ 0 网卡 CRC / drop 增长
☐ 温度持续在阈值内
☐ 性能不衰减 (前后 fio/iperf 一致)
☐ SEL log 0 Critical
```

### 4.7 Phoronix Test Suite（一站式）

```bash
sudo apt install phoronix-test-suite
phoronix-test-suite install pts/server-stress
phoronix-test-suite benchmark pts/server-stress

# 自动跑 + 上传 OpenBenchmarking
# CPU / 内存 / 磁盘 / 网络 / GPU / 编译 / 数据库等
# 500+ 测试项

推荐套件:
  pts/cpu              CPU 综合
  pts/memory           内存
  pts/disk             磁盘
  pts/gpu              GPU
  pts/server           服务器整合
  pts/database         DB (MySQL/PG/Redis)
  pts/audio-encoding / pts/compression-7zip (实际工作负载)
```

## 五、可靠性测试 (环境)

```
温度循环:
  恒温箱: -5℃ → 45℃ 循环 ☐
  每点 4h + 切换 1h
  
湿度:
  RH 20% / 80% / 95% ☐
  无凝露
  
震动 / 跌落:
  运输振动 (随机 / 正弦)
  跌落 (拐角 / 边 / 面)
  
EMC:
  电磁兼容 (CCC / FCC / CE)
  
高/低压 / 电源:
  输入 100-240V AC 全范围
  突降 / 突升 (Sag/Surge)
  PSU 单挂测试 (拔一路)
  
高海拔:
  3000m / 5000m (青藏/数据中心)
  风扇加速 + 降频策略

加速老化:
  HALT (Highly Accelerated Life Test)
  HASS (生产筛选)

工具:
  恒温恒湿箱 (Espec / Weiss / 国产)
  振动台
  EMC 实验室
  AC Source (Chroma / Ametek)
  IT Power (电网模拟)

注: 一般原厂 (Lenovo/Dell/HPE/华为) 实验室做, 集成商抽测
```

## 六、PXE + 自动化测试流水线 ⭐

> 你在联想就是这套（PXE + Python + MySQL），这里给现代版

```
架构:
[新机器] → PXE 启动 → Live OS (内存运行)
        → 采集 (lshw/dmidecode/smartctl/nvidia-smi)
        → 入 CMDB (MySQL/PG/NetBox)
        → 固件比对 + 升级
        → 烤机 72h
        → 报告
        → 通过 → 上架
        → 失败 → 退货 / 维修

工具栈:
  iPXE ⭐ / pxelinux       网络启动
  Foreman ⭐ / MAAS ⭐      集中装机平台
  Cobbler                  老牌
  Ironic (OpenStack)        裸机
  
  Ansible / SaltStack       配置 + 命令
  Python + Click / Typer    采集 / 报告脚本
  
  MySQL / PostgreSQL        CMDB
  NetBox ⭐ / Ralph         IPAM/CMDB
  
  Grafana + Prometheus      监控
  Allure / 自研             报告
  Slack / 钉钉 / 飞书       通知

国产替代:
  鲲鹏服务器自动化 (华为 FusionDirector)
  浪潮服务器管理 (ISCM)
  天工 / 天眼 (大厂自研)
```

### 6.1 现代化脚本示例（Python + Ansible）

```python
# collect.py - 上架前采集
import subprocess, json, requests

def shell(cmd):
    return subprocess.check_output(cmd, shell=True, text=True)

def collect():
    return {
        "sn": shell("dmidecode -s system-serial-number").strip(),
        "mfr": shell("dmidecode -s system-manufacturer").strip(),
        "model": shell("dmidecode -s system-product-name").strip(),
        "bios": shell("dmidecode -s bios-version").strip(),
        "cpu": shell("dmidecode -s processor-version").strip(),
        "mem_gb": int(shell("free -g | awk '/Mem/{print $2}'").strip()),
        "disks": json.loads(shell("lsblk -J")),
        "nics": shell("ip -j link").strip(),
        "gpus": shell("nvidia-smi -L 2>/dev/null || echo none").strip(),
    }

inv = collect()
requests.post("http://cmdb/api/servers", json=inv)
print(json.dumps(inv, indent=2, ensure_ascii=False))
```

```yaml
# burnin.yml - Ansible 烤机编排
- hosts: new_servers
  tasks:
    - name: 升级 BIOS
      command: OneCli update flash ...
      
    - name: 安装压测工具
      apt:
        name: [stress-ng, fio, iperf3]
        
    - name: 启动 72h 烤机
      shell: |
        nohup stress-ng --cpu 0 --vm 8 --vm-bytes 80% \
          --hdd 4 --timeout 72h > /var/log/stress.log 2>&1 &
          
    - name: 启动 fio
      shell: |
        nohup fio --name=mix --rw=randrw --bs=4k \
          --iodepth=64 --numjobs=4 --runtime=72h \
          --time_based --filename=/dev/nvme0n1 \
          > /var/log/fio.log 2>&1 &
          
    - name: 注册 Prometheus
      uri:
        url: http://prom/api/v1/admin/tsdb/...
```

## 七、国产化服务器

```
CPU:
  鲲鹏 920 / 950 (ARMv8.2, 华为)
  海光 (Hygon, x86)
  飞腾 (FT-2500 ARM / Phytium)
  兆芯 (Zhaoxin x86)
  龙芯 (LoongArch, MIPS 兼容)
  申威 (SW, Alpha 衍生)

服务器:
  华为 TaiShan / Atlas (鲲鹏 + 昇腾)
  浪潮 NF / SA / NE
  中科曙光 (海光 + Hygon DCU)
  新华三 H3C (兼容多平台)
  长城 / 联想 (鲲鹏版)
  超聚变 (华为分离后)

GPU:
  华为昇腾 Ascend 910B/C
  海光 DCU
  摩尔线程 MTT S系列
  天数智芯 Iluvatar
  寒武纪 思元
  壁仞 / 燧原 / 沐曦

OS:
  openEuler ⭐ / 麒麟 / UOS / Anolis (阿里)
  Ubuntu / RHEL 兼容 (大部分场景)

工具适配:
  ☐ stress-ng / fio / iperf3 → 通用 (兼容 ARM)
  ☐ Phoronix → 部分 (LoongArch 较少)
  ☐ DCGM → 不适用昇腾 (用 npu-smi / hccn_tool)
  ☐ Linpack → 鲲鹏专版 (KML-Linpack 华为)
  ☐ Mellanox → 部分国产 NIC 用厂商工具
  ☐ MegaRAID → 部分国产 RAID 用专版

测试要点:
  ☐ 鲲鹏 NUMA (多 die 多 socket, 拓扑复杂)
  ☐ 海光 SME / SEV (机密计算)
  ☐ 飞腾 ARM 大小核 (部分型号)
  ☐ 信创全栈兼容 (DB / 中间件 / 应用)
  ☐ 国密 SM2/3/4 加速 (CPU 卸载)
  ☐ 等保 / 关基 / 自主可控合规
```

## 八、Checklist（完整）

```
入场:
☐ 外观 / 资产标 / SN
☐ PSU x2 (型号 + 输入)
☐ 风扇 (数量 + 转向)
☐ 上架位置 (机柜 + U 位)
☐ 电源接线 + 网络接线

组件:
☐ CPU (型号/数量/微码)
☐ 内存 (容量/速率/通道/ECC)
☐ 磁盘 (SMART/型号/固件)
☐ RAID (固件/BBU)
☐ NIC (Speed/FW/SFP)
☐ GPU (DCGM/Xid/拓扑)
☐ BMC (FW/IP/Redfish)
☐ PSU (双路 OK)
☐ 风扇 (全转)
☐ 温度 (各点)

固件:
☐ BIOS / BMC / CPLD / ME 比对 + 升级
☐ RAID / HBA / NIC / NVMe / GPU VBIOS
☐ 备份配置 (RACADM export / OneCli config save)
☐ 升级日志归档

压测:
☐ CPU 1h Linpack
☐ MemTest86 4+ pass
☐ stress-ng VM 24h
☐ fio 24h 混合 IO
☐ iperf3 24h 长跑
☐ gpu_burn / DCGM diag -r 4
☐ 整机烤机 72h

环境:
☐ 温度 (各点 < 阈值)
☐ 湿度 (DC 标准)
☐ 海拔 (高海拔降频策略)

报告:
☐ 采集报告 (lshw / dmidecode 全)
☐ SMART / RAID / ECC 历史
☐ 压测结果 + 基线对比
☐ 异常清单 + 处置
☐ 签收 + 上架确认

上架后:
☐ 加入 CMDB
☐ 加入监控 (Prom / Zabbix / DCIM)
☐ 加入备份计划
☐ 加入告警接收人
```

## 九、推荐栈

```
组件检查:    dmidecode + lshw + smartctl + nvme-cli + ipmitool + nvidia-smi + DCGM ⭐
RAID 工具:   storcli + perccli + ssacli + sas3ircu
NIC 工具:    ethtool + mlnx (Mellanox) + mst
固件管理:    Lenovo OneCli ⭐ / Dell RACADM + DSU / HPE SUM / 华为 iBMA / 浪潮 ISBMC
BMC:        ipmitool + Redfish curl / Python ⭐
集中管理:    XClarity Admin / OpenManage Enterprise / OneView / FusionDirector / ISCM
CPU 压测:    stress-ng ⭐ + Linpack + Phoronix + sysbench + y-cruncher
内存压测:    MemTest86 ⭐ (脱机) + memtester + stress-ng + Intel MLC + STREAM
磁盘压测:    fio ⭐ + smartctl + iostat
网络压测:    iperf3 ⭐ + ethr + netperf + Mellanox ib_send_bw
GPU 压测:    DCGM diag -r 4 ⭐ + gpu-burn + nccl-tests + Linpack-CUDA
RAS 监控:    rasdaemon ⭐ + edac-util + mcelog
整机烤机:    stress-ng + fio + iperf3 + gpu-burn + Phoronix (72h)
PXE 平台:    iPXE ⭐ + Foreman ⭐ / MAAS ⭐ / Cobbler
自动化:      Ansible ⭐ + Python + Click
CMDB:       NetBox ⭐ / Ralph / 自研 MySQL
监控:        Prometheus + Grafana + node_exporter + DCGM exporter ⭐
报告:        Allure + 自研 HTML
国产:        华为 FusionDirector + 浪潮 ISCM + KML-Linpack + npu-smi (昇腾)
```

## 十、常见故障速查

```
现象                         可能原因               排查
─────────────────────────────────────────────────────────
开机不亮                     PSU / 主板 / 电源       双路 / CMOS / 跳线 / 厂商支持
开机后无显示                 BIOS POST 失败          BMC 视频 / 蜂鸣码 / 单条内存
POST 通过, 无 OS             启动顺序 / 引导损坏    BIOS Boot Order / Recovery / 重装
频繁蓝屏 / Panic             内存 / CPU / PSU       MemTest / mcelog / dmesg
GPU 不识别                   驱动 / PCIe / 槽       lspci / 重插 / 驱动重装
GPU Xid 79                   GPU 掉链 (PCIe)        重启 / 换槽 / GPU 故障
NIC 不通                     线缆 / SFP / 配置       ethtool / 换线 / 换模块
NIC CRC 增长                 线缆 / 模块 / 距离      换光纤 / 换 SFP / 缩短距离
磁盘 Reallocated 增长        盘老化 / 物理损伤       替换 + 数据迁移
温度报警                     风扇 / 散热 / 灰        清灰 / 换风扇 / 检查空调
ECC 频繁                     单条内存 / 主板         定位 DIMM (rasdaemon) / 替换
RAID Foreign Config         插入旧盘                 storcli clear foreign
BMC 失联                     BMC 死锁                ipmitool mc reset cold / 物理 reset
PSU 告警                     单路掉 / 输入异常       换路 / 换 PSU / 检查 UPS
风扇转速 100%                温度异常 / 风扇坏       sensors / 找原因 / 换风扇
```

> 📖 **核心判断**：服务器硬件测试 = **dmidecode/lshw 全清单 + smartctl/nvme 盘健康 + ipmitool/Redfish BMC + DCGM GPU + Lenovo OneCli/Dell RACADM/HPE SUM 一键固件升级 + stress-ng+MemTest86+fio+iperf3+gpu-burn 五大压测 + 72h 整机烤机 + iPXE+Foreman/MAAS+Ansible+CMDB 自动化流水线 + 鲲鹏/海光/昇腾国产化适配**。能从单台采集到机柜级批量上架, 覆盖来料 → 老化 → 上架 → 监控 → 退役全生命周期, 就具备数据中心硬件交付/测试工程师能力。**这是你联想三年的老本行, 现在加 AI/GPU + 国产化 + PXE 现代化 = 完整答卷。**
