# 基础

> 硬件测试基础 = **硬件分层认知(组件→整机→集群) + 入场清单 + 基础工具 5 件套(dmidecode/lshw/smartctl/ipmitool/lspci) + CPU/内存/磁盘/NIC/BMC 单点检查 + SMART 读懂 + IPMI 入门 + 基础压测(stress/memtester/fio/iperf3)**。面向数据中心新人 / 服务器测试工程师入门。

## 一、核心理念

```
测试分层:
  组件级    (CPU/MEM/SSD/NIC 单点)
  整机级    (BIOS+OS+负载组合)
  集群级    (HPC/AI/分布式)

测试阶段:
  Incoming  来料检验 (供应商交付)
  Burn-in   老化烤机 (24-72h)
  Pre-deploy 上架前 (固件 + 配置基线)
  Production 生产中 (DCIM 监控)
  EOL       退役 (数据擦除)

KPI:
  DOA (Dead on Arrival)  < 0.5%
  AFR (Annual Failure)   < 2%
  MTBF / MTTR
  烤机通过率 > 99%
```

## 二、基础工具 5 件套

```bash
# 1. dmidecode - 主板/BIOS/内存/CPU 元信息 (SMBIOS)
sudo dmidecode -t system            # 整机 SN
sudo dmidecode -t baseboard          # 主板
sudo dmidecode -t bios               # BIOS 版本
sudo dmidecode -t processor          # CPU
sudo dmidecode -t memory             # 内存
sudo dmidecode -s system-serial-number  # 单字段

# 2. lshw - 全景硬件 (树形)
sudo lshw -short
sudo lshw -html > hw.html
sudo lshw -class disk
sudo lshw -class network

# 3. smartctl - 磁盘健康 (SMART)
sudo smartctl --scan
sudo smartctl -a /dev/sda
sudo smartctl -H /dev/sda            # 仅 Health 状态

# 4. ipmitool - BMC / 传感器
sudo ipmitool mc info
sudo ipmitool sensor list
sudo ipmitool sel list
sudo ipmitool fru list

# 5. lspci / lsusb / lsblk - 总线设备
lspci -vvnn
lspci -tv                            # 树形
lsusb -tv
lsblk -o NAME,SIZE,ROTA,MODEL,SERIAL,TRAN
```

辅助工具：`inxi -Fxz`（友好概览）/ `hwinfo --short` / `cpuid` / `nvme list` / `ethtool` / `sensors`。

## 三、CPU 基础检查

```bash
lscpu                                # 整体: 核心/线程/微架构
cat /proc/cpuinfo | grep "model name" | head -1
cat /proc/cpuinfo | grep flags | head -1   # 指令集 (avx/avx2/avx512/amx)

# 拓扑
lscpu -e                             # 每核 socket/node
numactl -H                            # NUMA 拓扑
lstopo-no-graphics                    # hwloc 树

# 微码
dmesg | grep microcode

# MCE (硬件错误)
sudo mcelog --client
journalctl -k | grep -i mce

# 检查项:
☐ CPU 数量 + 型号 = 标称
☐ 全核 online (lscpu -e)
☐ 微码最新
☐ NUMA 平衡 (双路服务器双 node)
☐ 0 MCE / Correctable Error
```

## 四、内存基础检查

```bash
# 拓扑 + 速率
sudo dmidecode -t memory | grep -E "Size|Speed|Locator|Manufacturer|Part Number"
sudo dmidecode -t 17 | less

# free
free -g
cat /proc/meminfo | head -20

# ECC 错误
sudo edac-util -v                    # EDAC 内核
sudo edac-util -s
journalctl -k | grep -i edac

# RAS daemon (推荐, 持续监控) ⭐
sudo rasdaemon -r
sudo rasdaemon --list

# 检查项:
☐ 总容量 = 标称
☐ 通道平衡 (每 socket 6/8/12 通道全插)
☐ Speed = 标称 (DDR4-3200 / DDR5-4800/5600)
☐ ECC enabled (服务器必)
☐ 0 ECC 错误
☐ 厂商 / Part Number 一致性 (混插慎)
```

## 五、磁盘基础检查 (SMART)

```bash
lsblk
sudo smartctl --scan

# SATA / SAS
sudo smartctl -a /dev/sda

# NVMe
sudo smartctl -a /dev/nvme0
sudo nvme list
sudo nvme smart-log /dev/nvme0n1
sudo nvme id-ctrl /dev/nvme0          # 控制器信息
```

### 关键 SMART 字段（务必能看懂）

```
通用 (SATA/SAS):
  Reallocated_Sector_Ct       重映射扇区数 ⚠️ > 0 警报
  Current_Pending_Sector      等待重映射 ⚠️
  Offline_Uncorrectable       不可恢复 ⚠️
  Power_On_Hours              累计运行 (二手警惕)
  Power_Cycle_Count           开机次数
  Temperature                  温度
  UDMA_CRC_Error_Count        SATA 线缆 CRC

SSD 专属:
  Wear_Leveling_Count          损耗均衡
  Media_Wearout_Indicator      磨损 (剩余 %)
  Total_LBA_Written           总写入 (估算寿命)
  
NVMe (字段不同):
  critical_warning            = 0 必须 ⭐
  temperature                  < 70℃
  available_spare              > 10%
  percentage_used              < 80% (寿命)
  media_errors                  = 0
  data_units_written           总写入
```

### Self-test (盘自检)

```bash
# SATA/SAS
sudo smartctl -t short /dev/sda      # 短测 (~2 min)
sudo smartctl -t long /dev/sda       # 长测 (数小时)
sudo smartctl -l selftest /dev/sda   # 查看结果

# NVMe
sudo nvme device-self-test /dev/nvme0n1 -s 1   # short
sudo nvme device-self-test /dev/nvme0n1 -s 2   # extended
sudo nvme self-test-log /dev/nvme0n1
```

### 检查项

```
☐ smartctl -H → PASSED
☐ Reallocated/Pending/Uncorrectable = 0
☐ NVMe critical_warning = 0
☐ 温度 < 60℃ (HDD) / < 70℃ (SSD/NVMe)
☐ Self-test PASS
☐ 容量 / 型号 / 序列号 = 标称
☐ 二手盘警惕: Power_On_Hours / Cycle
```

## 六、网卡基础检查

```bash
ip link
sudo ethtool eth0                    # Speed/Duplex/Auto
sudo ethtool -i eth0                 # driver/firmware
sudo ethtool -S eth0                 # 统计 (errors/drops/CRC)
sudo ethtool -m eth0                 # SFP/QSFP 模块 (光功率/温度)
sudo lspci | grep -i ether

# 检查项:
☐ Speed = 标称 (1G/10G/25G/100G)
☐ Duplex = Full
☐ Link = up
☐ 0 RX/TX errors / drops / CRC
☐ Driver / Firmware 已知好
☐ SFP 厂商兼容 + DDM 正常
```

## 七、BMC / IPMI 入门

```bash
# 本地 (in-band)
sudo ipmitool mc info                 # BMC 固件版本
sudo ipmitool lan print 1             # BMC IP
sudo ipmitool sensor list             # 传感器
sudo ipmitool sel list                # 事件日志 (重要!)
sudo ipmitool fru list                # 整机 SN/PN

# 远程 (out-of-band)
ipmitool -I lanplus -H <bmc-ip> -U admin -P xxx chassis status
ipmitool -I lanplus -H <bmc-ip> -U admin -P xxx chassis power status
ipmitool -I lanplus -H <bmc-ip> -U admin -P xxx sol activate     # 串口

# 健康
ipmitool sdr type Fan
ipmitool sdr type Temperature
ipmitool sdr type "Power Supply"

# 清空 SEL (验证后)
ipmitool sel clear
```

### Redfish（现代 ⭐）

```bash
# 替代 IPMI 的 HTTPS/JSON API
curl -k -u admin:xxx https://<bmc>/redfish/v1/Systems/1
curl -k -u admin:xxx https://<bmc>/redfish/v1/Chassis/1/Thermal
curl -k -u admin:xxx https://<bmc>/redfish/v1/Managers/1/LogServices/SEL/Entries
```

### 检查项

```
☐ BMC 固件最新
☐ BMC IP 在管理网段 + 可达
☐ 默认密码已改 (admin/admin 禁)
☐ SOL 启用 (串口重定向)
☐ Redfish 启用 + HTTPS
☐ NTP 同步
☐ SEL 0 Critical (清空后观察)
```

## 八、温度 + 风扇 + PSU

```bash
# lm-sensors
sudo sensors-detect
sensors

# IPMI 传感器
ipmitool sdr type Fan
ipmitool sdr type Temperature
ipmitool sdr type "Power Supply"

# 厂商工具
sudo OneCli inventory                 # Lenovo XCC
sudo racadm getsensorinfo             # Dell
sudo hponcfg                          # HPE iLO

# 检查项:
☐ 双 PSU 在位 + 同型号 + 同 FW
☐ AC Input OK / DC Output OK
☐ 风扇全部转 + RPM 在范围
☐ CPU/HDD/Ambient 温度正常
☐ SEL 0 Critical
```

## 九、基础压测入门

### 9.1 CPU

```bash
# stress-ng (现代) ⭐
stress-ng --cpu $(nproc) --timeout 10m --metrics-brief
stress-ng --matrix 0 --timeout 30m    # 矩阵运算 (AVX)

# 老 stress
stress -c $(nproc) -t 600

# 监控 (另开窗口)
mpstat -P ALL 5
sensors -A
watch -n1 'cat /proc/cpuinfo | grep MHz | head -4'

# 检查:
☐ 全核 100% 负载
☐ 温度 < TjMax (Intel 90-100℃)
☐ 无降频
```

### 9.2 内存

```bash
# 在线 (OS 运行时)
sudo memtester 16G 3                  # 16G × 3 pass

# stress-ng VM
stress-ng --vm 4 --vm-bytes 70% --vm-keep --timeout 1h

# 脱机 (最全, 大内存推荐) ⭐
# MemTest86 / MemTest86+ U 盘启动, 4+ pass
```

### 9.3 磁盘 (fio)

```bash
# 4K 随机读 (IOPS)
fio --name=randread --rw=randread --bs=4k --iodepth=64 --numjobs=4 \
    --runtime=300 --time_based --group_reporting \
    --direct=1 --ioengine=libaio --filename=/dev/nvme0n1

# 顺序读 (带宽)
fio --name=seqread --rw=read --bs=1M --iodepth=32 --numjobs=1 \
    --runtime=120 --time_based --direct=1 --filename=/dev/nvme0n1

# 监控
iostat -mx 5
```

⚠️ **`--filename=/dev/xxx` 是裸盘破坏性测试**，新盘 / 已格式化盘小心；安全做法用文件 `--filename=/tmp/fio.bin --size=10G`。

### 9.4 网络 (iperf3)

```bash
# Server
iperf3 -s

# Client
iperf3 -c <server> -t 60 -P 1         # 单流
iperf3 -c <server> -t 60 -P 16        # 多流 (25G/100G 必)
iperf3 -c <server> -R                 # 反向
iperf3 -c <server> --bidir            # 双向
iperf3 -c <server> -u -b 10G -t 60    # UDP 丢包/抖动
```

## 十、入场清单（来料 / 上架前）

```
外观:
☐ 资产标 / SN / 型号
☐ 包装无变形 / 防潮
☐ 螺丝 / 配件齐全 (轨道 / 线材)
☐ 风扇 / PSU 全在位

通电前:
☐ 上架位置确认 (机柜 + U 位)
☐ 电源接线 (双路独立)
☐ 网络接线 (Mgmt + Data)

POST + 体检:
☐ POST 通过 (无蜂鸣 / 无报错)
☐ dmidecode / lshw 全部一致
☐ CPU / 内存 / 磁盘 / NIC 全识别
☐ BMC 可达 + Redfish 通
☐ SEL log 0 Critical
☐ 温度 + 风扇 + PSU 正常
☐ SMART 全 PASS
☐ 默认密码已改

上 OS 后:
☐ 基础压测 (CPU/MEM/DISK/NET 各 10-30 min)
☐ 加入 CMDB / 监控 / 告警
☐ 准备进入 Burn-in (见 04_最佳实践)
```

## 十一、Checklist（基础）

```
工具:
☐ dmidecode / lshw / inxi
☐ smartctl / nvme-cli
☐ ipmitool / Redfish curl
☐ ethtool / lspci
☐ rasdaemon / mcelog

CPU:
☐ 数量 + 型号 + NUMA
☐ 微码最新
☐ 0 MCE

内存:
☐ 容量 + 通道 + Speed
☐ ECC + 0 错误

磁盘:
☐ SMART PASSED
☐ 0 Reallocated/Pending
☐ NVMe critical_warning = 0
☐ Self-test PASS

NIC:
☐ Speed/Duplex/Link
☐ 0 CRC/drop

BMC:
☐ 可达 + Redfish
☐ 密码改 + NTP + SOL
☐ SEL 0 Critical

PSU/风扇/温度:
☐ 双 PSU OK
☐ 风扇全转
☐ 温度正常

压测 (基础):
☐ stress-ng 10m
☐ memtester 1 pass
☐ fio 5 min
☐ iperf3 60s
```

## 十二、推荐栈（基础）

```
体检:        dmidecode + lshw + inxi ⭐ + hwinfo
磁盘:        smartctl + nvme-cli ⭐
网卡:        ethtool + lspci
BMC:        ipmitool ⭐ + Redfish curl
温度:        sensors + lm-sensors + ipmitool sdr
RAS:        rasdaemon ⭐ + edac-util + mcelog
压测入门:    stress-ng ⭐ + memtester + fio + iperf3
报告:        手工记录 → 后续自动化
```

> 📖 **核心判断**：硬件测试基础 = **5 件套(dmidecode/lshw/smartctl/ipmitool/lspci) + CPU/MEM/DISK/NIC/BMC 单点体检 + SMART 关键字段(Reallocated/critical_warning) + IPMI/Redfish 入门 + 基础压测(stress-ng/memtester/fio/iperf3)**。能给一台新到货服务器做"开箱体检 + 入场清单 + 基础压测"且能读懂 SMART / SEL / IPMI 输出, 就具备初级服务器测试工程师能力。**硬件测试的本质 = 早发现问题, 别等生产挂了再排查。**
