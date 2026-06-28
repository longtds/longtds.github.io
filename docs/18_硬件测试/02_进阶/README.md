# 进阶

> 硬件测试进阶 = **RAID 全栈(storcli/perccli/ssacli) + 高速 NIC(25/100G + Mellanox/Broadcom) + SFP 模块诊断 + NVMe 深度 + GPU 基础(nvidia-smi + DCGM) + 厂商 BMC 工具集(OneCli/RACADM/iLO/iBMC) + 压测进阶(Linpack/MLC/STREAM/gpu-burn) + RAS daemon 持续监控 + IPMI 自动化脚本 + 故障件定位**。面向独立负责 1-50 台服务器交付的工程师。

## 一、RAID / HBA 深度

### 1.1 LSI / Broadcom MegaRAID (storcli)

```bash
# 控制器列表
sudo storcli show
sudo storcli /c0 show all              # c0 = 第一块控制器

# 物理盘
sudo storcli /c0/eall/sall show all
sudo storcli /c0/eall/sall show       # 简洁

# 虚拟盘
sudo storcli /c0/vall show all
sudo storcli /c0/v0 show all

# 事件日志 ⭐
sudo storcli /c0 show events filter=warning,critical,fatal
sudo storcli /c0 show events file=/tmp/events.log

# BBU / CacheVault
sudo storcli /c0/bbu show all
sudo storcli /c0/cv show all

# 创建 RAID (示例 RAID10)
sudo storcli /c0 add vd r10 size=all drives=8:0-7 pdperarray=2 \
    wb ra direct strip=256

# 修改 RAID 属性
sudo storcli /c0/v0 set wrcache=wb
sudo storcli /c0/v0 set rdcache=ra
sudo storcli /c0/v0 set iopolicy=direct

# Foreign Config 清理 (插入旧盘必)
sudo storcli /c0/fall show
sudo storcli /c0/fall del

# 巡检 / Patrol Read
sudo storcli /c0 show patrolread
sudo storcli /c0 start patrolread
```

### 1.2 老的 MegaCli

```bash
sudo megacli -AdpAllInfo -aALL
sudo megacli -PDList -aALL
sudo megacli -LDInfo -Lall -aALL
sudo megacli -AdpEventLog -GetEvents -f /tmp/event.log -aALL
```

### 1.3 Dell PERC

```bash
sudo perccli /c0 show all              # storcli 兼容语法
sudo perccli /c0/vall show all
sudo perccli /c0 show events

# RACADM (远程, Dell iDRAC)
racadm storage get pdisks
racadm storage get vdisks
racadm storage get controllers
```

### 1.4 HPE Smart Array (ssacli)

```bash
sudo ssacli ctrl all show config
sudo ssacli ctrl all show config detail
sudo ssacli ctrl slot=0 pd all show status
sudo ssacli ctrl slot=0 ld all show status

# 创建 RAID
sudo ssacli ctrl slot=0 create type=ld drives=1I:1:1,1I:1:2 raid=1
```

### 1.5 SAS HBA (sas3ircu)

```bash
sudo sas3ircu LIST                     # 列控制器
sudo sas3ircu 0 DISPLAY                # 详细
sudo sas3ircu 0 STATUS                 # 简洁
```

### 1.6 RAID 检查项

```
☐ 固件版本 + 多控制器一致
☐ Battery / BBU 健康 (写缓存策略关键)
☐ RAID 级别 + Stripe Size 合规
☐ 0 故障盘 + 0 重建中
☐ 写缓存策略 (Write Back + BBU)
☐ 无 Foreign Config 残留
☐ Patrol Read 启用 (周期性巡检)
☐ Consistency Check 启用 (RAID5/6 必)
☐ 事件日志归档 (审计)
```

## 二、高速 NIC + SFP 模块

### 2.1 ethtool 进阶

```bash
# 速率 / 协商
sudo ethtool eth0

# 统计 (errors / drops / CRC)
sudo ethtool -S eth0 | grep -iE "error|drop|crc|miss"
sudo ethtool -S eth0 | grep -iE "rx_|tx_"

# Offload (LRO/GRO/TSO/GSO)
sudo ethtool -k eth0
sudo ethtool -K eth0 lro off          # 调试用

# Ring buffer
sudo ethtool -g eth0
sudo ethtool -G eth0 rx 4096 tx 4096   # 增大

# 多队列
sudo ethtool -l eth0
sudo ethtool -L eth0 combined $(nproc)

# 中断合并
sudo ethtool -c eth0
sudo ethtool -C eth0 adaptive-rx on

# SFP/QSFP 模块 (DDM) ⭐
sudo ethtool -m eth0
# 关键字段: Vendor / SN / Wavelength / 温度 / 电压 / 光功率 (RX/TX)

# 强制速率 / 关闭自协商
sudo ethtool -s eth0 speed 10000 duplex full autoneg off
```

### 2.2 Mellanox / NVIDIA NIC (ConnectX)

```bash
# MFT 工具集
sudo mst start
sudo mst status                        # 列设备
sudo mlxfwmanager --query               # 查询固件
sudo mlxfwmanager -u                    # 在线升级
sudo mlxfwmanager -i fw.bin -u --force

# mstflint (老工具)
sudo mstflint -d <pci> q                # 查询
sudo mstflint -d <pci> -i fw.bin b      # 烧录

# RDMA / RoCE 配置
mlnx_qos -i eth0                        # QoS
ibstat                                  # IB 状态
ibv_devices / ibv_devinfo                # 设备
show_gids                                # GID 表

# OFED 工具
ib_send_bw -d mlx5_0 <peer>             # 带宽
ib_send_lat                              # 延迟
ib_write_bw / ib_read_bw / ib_atomic_bw

# Mellanox 自检
sudo mlxlink -d <pci> -p 1
sudo mlxconfig -d <pci> q               # 查配置
```

### 2.3 Broadcom NIC

```bash
sudo bnxtnvm device_info
sudo niccli -dev=0 nvm queryversion
```

### 2.4 Intel NIC (ixgbe / i40e / ice)

```bash
sudo ethtool -i eth0                    # 看 driver/firmware
# 工具: nvmupdate64e (Intel 官方)
```

### 2.5 NIC 检查项

```
☐ Speed = 标称 (10/25/100/200/400G)
☐ 0 RX/TX errors / drops / CRC
☐ 多队列 = CPU 核心数
☐ 中断 IRQ 绑核 (NUMA 亲和)
☐ Ring buffer 调到合理大小
☐ SFP 厂商 + DDM 正常 (光功率 -3 ~ 0 dBm)
☐ Mellanox: ibstat 端口 Active
☐ MTU = 标称 (Jumbo 9000)
☐ Firmware 已知好
```

## 三、NVMe 深度

### 3.1 nvme-cli 工具集

```bash
sudo nvme list                          # 设备列表
sudo nvme list-subsys                   # 子系统

# 控制器 / Namespace
sudo nvme id-ctrl /dev/nvme0
sudo nvme id-ns /dev/nvme0n1

# SMART
sudo nvme smart-log /dev/nvme0n1
sudo nvme error-log /dev/nvme0

# 寿命 / Endurance
sudo nvme smart-log /dev/nvme0n1 | grep -E "percentage_used|available_spare"

# 温度告警阈值
sudo nvme get-feature /dev/nvme0 -f 0x04 -H

# Self-test
sudo nvme device-self-test /dev/nvme0n1 -s 1       # short
sudo nvme device-self-test /dev/nvme0n1 -s 2       # extended
sudo nvme self-test-log /dev/nvme0n1

# 固件
sudo nvme fw-log /dev/nvme0
sudo nvme fw-download /dev/nvme0 -f fw.bin
sudo nvme fw-commit /dev/nvme0 -s 1 -a 1
sudo nvme reset /dev/nvme0

# Format (谨慎, 破坏性)
sudo nvme format /dev/nvme0n1 -l 0 -s 1            # Secure Erase

# Sanitize (彻底清除)
sudo nvme sanitize /dev/nvme0 -a 1                 # Block Erase
sudo nvme sanitize-log /dev/nvme0
```

### 3.2 关键 NVMe 字段

```
critical_warning          0 = 正常 (bit 编码错误类型)
temperature              < 70℃
available_spare           > 10% (备用块剩余)
available_spare_threshold 阈值
percentage_used           < 80% (寿命磨损)
data_units_read/written  GB 累计
power_cycles              开机次数
power_on_hours            运行时长
unsafe_shutdowns          非正常断电次数 ⚠️
media_errors              介质错误 ⚠️
num_err_log_entries       错误日志条目数
```

### 3.3 NVMe-oF (NVMe over Fabrics)

```bash
# 在 Target 侧创建
sudo nvme connect-all -t rdma -a <ip> -s 4420
sudo nvme list-subsys

# Target 配置: SPDK / Linux Kernel Target
# 详见 SPDK / nvmet 文档
```

## 四、GPU 进阶

### 4.1 NVIDIA nvidia-smi 进阶

```bash
nvidia-smi                              # 概览
nvidia-smi -q                           # 详细全字段
nvidia-smi -q -d MEMORY,UTILIZATION,POWER,CLOCK,TEMPERATURE,ECC,XID
nvidia-smi nvlink --status               # NVLink 状态
nvidia-smi nvlink -c                     # NVLink 计数器
nvidia-smi topo -m                       # 拓扑矩阵
nvidia-smi topo -p2p w                   # P2P 可达性
nvidia-smi -L                            # 简洁列表
nvidia-smi --query-gpu=index,name,serial,uuid,vbios_version --format=csv

# 持久模式 (推荐, 减少延迟)
sudo nvidia-smi -pm 1

# 计算模式
sudo nvidia-smi -c 3                     # Exclusive Process

# ECC
nvidia-smi -q -d ECC
nvidia-smi -e 1                          # 启用 ECC (需重启)

# 实时监控 ⭐
nvidia-smi dmon -s pucvmet -d 1
nvidia-smi dmon -s pucvmet -d 1 -c 60    # 60 次

# 进程
nvidia-smi pmon -c 5
```

### 4.2 DCGM (Datacenter GPU Manager) ⭐

```bash
sudo systemctl start nvidia-dcgm
sudo systemctl enable nvidia-dcgm

dcgmi discovery -l                       # 列 GPU
dcgmi health --check-all                  # 健康

# 诊断 (Level 1-4, Level 越高越久)
dcgmi diag -r 1                          # 1-2 min (PCIe / 内存基础)
dcgmi diag -r 2                          # 5 min (中等压测)
dcgmi diag -r 3                          # 30 min (生产前推荐)
dcgmi diag -r 4                          # 数小时 (全面)

# 实时
dcgmi dmon -e 1004,1005,1010

# 字段定义参考
dcgmi fieldinfo --field-id 1004
```

### 4.3 Xid 错误（必懂 ⭐）

```bash
dmesg | grep -i "nvrm:.*xid"
journalctl -k | grep -i xid

# 常见 Xid:
# Xid 13: Graphics Engine Exception (一般可重启)
# Xid 31: GPU memory page fault (软件/驱动)
# Xid 43: GPU stopped processing (Reset 可)
# Xid 44: Graphics Engine fault (硬件嫌疑)
# Xid 48: Double Bit ECC ⚠️ (DBE, 硬件 RMA)
# Xid 63/64: Page Retired (内存有坏块 → 自动 Retire)
# Xid 74: NVLink Error
# Xid 79: GPU has fallen off the bus ⚠️ (掉链 PCIe, 重大)
# Xid 119/120: GPU Driver Error
# 参考: NVIDIA Xid Error Reference Manual
```

### 4.4 国产 GPU / NPU

```bash
# 华为昇腾 Ascend
npu-smi info                            # 概览
npu-smi info -t board -i 0              # 单板详细
npu-smi info -t temp -i 0
npu-smi info -t power -i 0
hccn_tool -i 0 -info                     # 网络/拓扑
hccn_tool -i 0 -link -g                  # 链路状态

# 海光 DCU
rocm-smi                                 # ROCm 兼容
rocminfo

# 摩尔线程
mxsmi
mthreads-smi

# Habana Gaudi (Intel)
hl-smi

# 寒武纪
cnmon
```

### 4.5 GPU 检查项

```
☐ 全卡识别 (nvidia-smi -L)
☐ ECC enabled + 0 Uncorrectable
☐ 温度 < 85℃ (空闲 < 50℃)
☐ Persistence ON
☐ PCIe Gen 4/5 + x16 (满速)
☐ NVLink up (DGX/HGX 必)
☐ DCGM diag -r 3 PASS
☐ 0 Xid 错误
☐ VBIOS 版本一致 (多卡)
☐ 拓扑符合预期 (NVLink/PCIe Switch)
```

## 五、厂商 BMC 工具集

### 5.1 Lenovo XCC (OneCli)

```bash
# 库存
sudo OneCli inventory --output /tmp/inventory.xml
sudo OneCli inventory getinfor --bmc <ip> --user <u> --password <p>

# 配置导出 / 导入
sudo OneCli config save --file /tmp/cfg.xml
sudo OneCli config restore --file /tmp/cfg.xml --bmc <ip> ...

# 固件升级 ⭐
sudo OneCli update flash --uselocalimage --imm <ip> --user <u> --password <p>
sudo OneCli update flash --uselocalimage --dir /tmp/firmware/

# 命令路径: /opt/lenovo/onecli/
```

### 5.2 Dell iDRAC RACADM

```bash
# 本地
sudo racadm getsysinfo
sudo racadm hwinventory
sudo racadm storage get controllers
sudo racadm storage get pdisks
sudo racadm storage get vdisks

# 远程
racadm -r <idrac-ip> -u root -p xxx getsysinfo
racadm -r <ip> -u root -p xxx serveraction powerstatus
racadm -r <ip> -u root -p xxx jobqueue view

# 配置导出
racadm get -t xml -f /tmp/config.xml
racadm set -t xml -f /tmp/config.xml

# 日志
racadm getseltrace
racadm getsel
racadm getraclog

# Lifecycle Controller
racadm lclog view
```

### 5.3 HPE iLO

```bash
# hponcfg (本地)
sudo hponcfg -a -f input.xml
sudo hponcfg -w /tmp/ilo_config.xml      # 导出
sudo hponcfg -r                          # Reset iLO

# iLO REST CLI
ilorest login <ilo-ip> -u admin -p xxx
ilorest list
ilorest get
ilorest serverinfo
ilorest serverstate
ilorest serverlogs

# HPE Smart Update Manager (SUM)
mount /dev/sr0 /mnt && /mnt/launch_sum.sh
```

### 5.4 华为 iBMC

```bash
# iBMA 客户端
sudo /opt/huawei/iBMA/bin/iBMA_config
sudo ipmitool -I lanplus -H <ibmc-ip> -U Administrator -P xxx mc info

# 命令行升级
upgrade --bmc <ip> --user <u> --password <p> --file fw.zip

# Toolkit-SP (集成升级包)
```

### 5.5 Supermicro

```bash
# SMCIPMITool
SMCIPMITool <ip> ADMIN xxx ipmi mc info
SMCIPMITool <ip> ADMIN xxx ipmi sdr

# SUM (Supermicro Update Manager)
sum -i <ip> -u ADMIN -p xxx -c GetBmcInfo
sum -i <ip> -u ADMIN -p xxx -c UpdateBmc --file fw.bin
```

### 5.6 国产服务器

```
浪潮:  ISBMC / ISCM + ipmitool 通用 + iSM 工具
中科曙光: Sugon Manager / Tcsm
新华三 H3C: HDM + HDM CLI
长城 / 联想 (鲲鹏版): 同 Lenovo OneCli
华为超聚变: FusionDirector + Toolkit-SP
```

## 六、压测进阶

### 6.1 CPU - Linpack ⭐

```bash
# Intel MKL Linpack (Intel CPU)
/opt/intel/mkl/benchmarks/linpack/runme_intel64_static
# 输出: GFLOPS (越接近理论越好)

# HPL (OpenMPI, 通用 + HPC) ⭐
mpirun -np <核数> ./xhpl
# HPL.dat 配置: N = sqrt(MEM*0.8/8), NB = 192, P*Q = 核数

# 鲲鹏: KML-Linpack (华为)
# 海光: HygonCloud Linpack
```

### 6.2 内存 - Intel MLC + STREAM

```bash
# Intel Memory Latency Checker ⭐
sudo mlc                                # 全套
sudo mlc --bandwidth_matrix              # NUMA 带宽矩阵
sudo mlc --latency_matrix                # NUMA 延迟矩阵
sudo mlc --idle_latency                  # 空闲延迟

# STREAM
gcc -fopenmp -O3 stream.c -o stream
OMP_NUM_THREADS=$(nproc) ./stream
# 关注 Triad 指标
# 参考: DDR5 4800 单通 ~38GB/s, 8 通道 ~250GB/s+

# 检查项:
☐ 本地 NUMA 延迟 < 100ns
☐ 远端 NUMA 延迟 < 150ns
☐ STREAM Triad 达理论 80%+
```

### 6.3 磁盘 - fio 进阶

```bash
# 4 种黄金负载 (企业 SSD/NVMe 标准)

# 1) 4K 随机读 (OLTP)
fio --name=4k_randread --rw=randread --bs=4k --iodepth=64 \
    --numjobs=4 --runtime=300 --time_based --group_reporting \
    --direct=1 --ioengine=libaio --filename=/dev/nvme0n1

# 2) 4K 随机写
fio --name=4k_randwrite --rw=randwrite --bs=4k --iodepth=64 \
    --numjobs=4 --runtime=300 --time_based --group_reporting \
    --direct=1 --ioengine=libaio --filename=/dev/nvme0n1

# 3) 1M 顺序读 (备份/大文件)
fio --name=1m_seqread --rw=read --bs=1M --iodepth=32 \
    --numjobs=1 --runtime=300 --time_based \
    --direct=1 --filename=/dev/nvme0n1

# 4) 70R/30W 混合 (生产 ⭐)
fio --name=mix7030 --rw=randrw --rwmixread=70 --bs=4k --iodepth=64 \
    --numjobs=4 --runtime=24h --time_based --group_reporting \
    --direct=1 --ioengine=libaio --filename=/dev/nvme0n1

# 看 IOPS / BW / Latency P99
# 参考 PCIe Gen4 NVMe: 
#   顺序读 7000 MB/s / 写 6000 MB/s
#   4K 随机读 1M IOPS / 写 200K IOPS

# 输出 JSON 便于对比 / 回归
fio ... --output-format=json --output=result.json
```

### 6.4 网络 - 长跑 + RDMA

```bash
# iperf3 24-72h 长跑
iperf3 -c <peer> -t 86400 -P 8

# ethr (微软, 现代)
ethr -s
ethr -c <peer> -t b -d 60s -p tcp -n 16

# Mellanox RDMA
ib_send_bw -d mlx5_0 <peer>
ib_send_lat
ib_write_bw

# NCCL (AI 互联)
mpirun -np 8 ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1
```

### 6.5 GPU - gpu-burn + DCGM

```bash
# gpu-burn (暴力)
git clone https://github.com/wilicc/gpu-burn
cd gpu-burn && make
./gpu_burn -d 3600                       # 1h
./gpu_burn -tc 7200                       # 2h Tensor Core

# DCGM diag (推荐, 厂商认可)
dcgmi diag -r 3                          # 30 min
dcgmi diag -r 4                          # 数小时 全面

# nccl-tests (多卡)
mpirun -np 8 ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1
```

## 七、RAS daemon 持续监控 ⭐

```bash
# 安装
sudo apt install rasdaemon
sudo systemctl enable rasdaemon --now

# 实时
sudo rasdaemon -r

# 查询
sudo ras-mc-ctl --summary
sudo ras-mc-ctl --errors
sudo ras-mc-ctl --status
sudo ras-mc-ctl --print-labels

# 输出 → SQLite
ls /var/lib/rasdaemon/ras-mc_event.db

# 集成 Prometheus
ras_exporter (社区) / 自研脚本

# 价值:
- 持续记录 CE (Correctable Error) → SCE 趋势 → 提前换 DIMM
- DBE (UE) 立刻告警 → RMA
- 替代 EDAC 老接口
```

## 八、IPMI 自动化脚本

```python
# ipmi_bulk_check.py - 批量健康检查
#!/usr/bin/env python3
import subprocess, json, csv, sys
from concurrent.futures import ThreadPoolExecutor

def ipmi(ip, user, pwd, args):
    cmd = ["ipmitool", "-I", "lanplus", "-H", ip,
           "-U", user, "-P", pwd] + args
    try:
        return subprocess.check_output(cmd, text=True, timeout=15)
    except Exception as e:
        return f"ERROR: {e}"

def check(host):
    ip, user, pwd = host["ip"], host["user"], host["pwd"]
    return {
        "ip": ip,
        "mc": ipmi(ip, user, pwd, ["mc", "info"]).split("\n")[1:4],
        "power": ipmi(ip, user, pwd, ["chassis", "power", "status"]).strip(),
        "sel_critical": sum(1 for l in ipmi(ip, user, pwd, ["sel", "list"]).split("\n") if "Critical" in l),
        "fan_min_rpm": min((int(l.split("|")[1].strip().split()[0])
                            for l in ipmi(ip, user, pwd, ["sdr", "type", "Fan"]).split("\n")
                            if "RPM" in l), default=0),
    }

hosts = json.load(open("hosts.json"))
with ThreadPoolExecutor(8) as pool:
    results = list(pool.map(check, hosts))

w = csv.DictWriter(sys.stdout, fieldnames=results[0].keys())
w.writeheader(); w.writerows(results)
```

```bash
# Ansible 批量
ansible all -i hosts.ini -m shell -a "ipmitool sel list | grep Critical"
ansible all -i hosts.ini -m shell -a "dcgmi diag -r 1"
```

## 九、故障件定位（DIMM / 风扇 / 盘）

```bash
# DIMM 定位 (ECC 错增长)
sudo rasdaemon -r                       # 持续
sudo ras-mc-ctl --errors | grep -i correctable

# 结合 dmidecode 找具体槽位
sudo dmidecode -t memory | grep -B 1 "Bank Locator"
# 例: Bank Locator: NODE 1 CHANNEL 0 DIMM 0

# 风扇定位
ipmitool sdr type Fan
# 不转 / 转速过低 → 物理找位置

# 盘定位 (LED 闪烁) ⭐
sudo storcli /c0/eX/sY start locate     # 开始闪
sudo storcli /c0/eX/sY stop locate       # 停止

# SAS HBA
sudo sg_ses --enclosure /dev/sg0 --get="ident"=1 -I X

# Dell PERC
racadm storage set pdisks blinkstart:Disk.Bay.0:Enclosure.Internal.0-1:RAID.Slot.X

# HPE
ssacli ctrl slot=0 pd 1I:1:1 modify led=on
```

## 十、Checklist（进阶）

```
RAID:
☐ storcli / perccli / ssacli 任一精通
☐ 固件 + BBU + 缓存策略
☐ 0 Foreign Config + Patrol Read 启用
☐ 事件日志归档

NIC:
☐ 25/100G + Mellanox / Broadcom / Intel
☐ ethtool 全字段 + SFP DDM
☐ Mellanox MFT + RDMA / RoCE
☐ 多队列 + IRQ 绑核 + Jumbo

NVMe:
☐ nvme-cli 全栈
☐ percentage_used / critical_warning / 自检
☐ Sanitize / Format 谨慎
☐ NVMe-oF 基础

GPU:
☐ nvidia-smi 全字段
☐ DCGM diag -r 3 (生产前)
☐ Xid 错误识别 (48 DBE / 79 掉链)
☐ 国产: npu-smi / rocm-smi

BMC:
☐ OneCli / RACADM / iLO / iBMC 任一精通
☐ Redfish API 调用
☐ 配置导出 + 自动化

压测进阶:
☐ Linpack ⭐ (HPL / MKL)
☐ MLC + STREAM
☐ fio 4 种黄金负载
☐ iperf3 + RDMA
☐ DCGM diag + gpu-burn

RAS:
☐ rasdaemon 部署
☐ ECC CE/UE 监控 + 趋势

自动化:
☐ Python / Ansible IPMI 批量
☐ Redfish 批量调用

故障定位:
☐ DIMM 槽位定位
☐ 盘 LED 闪烁
☐ 风扇 / PSU 定位
```

## 十一、推荐栈（进阶）

```
RAID:        storcli ⭐ / perccli / ssacli / sas3ircu / megacli
NIC:         ethtool + lspci + Mellanox MFT ⭐ + mstflint
RDMA:        OFED + ibstat + ib_send_bw + perftest
NVMe:        nvme-cli ⭐ + smartmontools
GPU:         nvidia-smi + DCGM ⭐ + nvtop + nvitop
国产 NPU:    npu-smi (昇腾) + rocm-smi (海光) + mxsmi (摩尔线程)
BMC:         ipmitool + Redfish (curl/python-redfish) ⭐
厂商:        OneCli (Lenovo) / RACADM (Dell) / hponcfg (HPE) / iBMA (华为)
压测:        stress-ng + Linpack ⭐ + Intel MLC + STREAM + fio + iperf3 + gpu-burn
RAS:         rasdaemon ⭐ + edac-util + mcelog
自动化:      Python (pyghmi/python-redfish) + Ansible + Shell
监控:        Prometheus + node_exporter + DCGM exporter + ipmi_exporter
故障定位:    storcli locate + ras-mc-ctl + dmidecode
报告:        Allure / 自研 + JSON 输出 + Excel
```

> 📖 **核心判断**：硬件测试进阶 = **RAID(storcli/perccli/ssacli) + 高速 NIC(Mellanox MFT/ethtool 进阶/SFP DDM) + NVMe(nvme-cli 全栈/Sanitize/Format) + GPU(DCGM diag-r3 + Xid 识别) + 厂商 BMC(OneCli/RACADM/iLO/iBMC) + 压测进阶(Linpack/MLC/STREAM/fio 4 种负载/gpu-burn) + RAS daemon 持续监控 + Python/Ansible IPMI 批量 + 故障件定位(DIMM/盘 LED)**。能独立给 1-50 台服务器做"组件深度体检 + 固件比对 + 进阶压测 + 故障定位 + 报告输出", 就具备资深服务器测试工程师能力。**进阶的本质 = 从单机操作升级到批量自动化 + 厂商工具熟练 + 看懂 RAS/Xid/SMART/SEL 真实硬件信号。**
