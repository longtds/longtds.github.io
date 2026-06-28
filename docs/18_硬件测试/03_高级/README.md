# 高级

> 硬件测试高级 = **固件升级全栈(BIOS/BMC/RAID/NIC/NVMe/GPU VBIOS) + 72h 整机烤机(CPU+MEM+DISK+NET+GPU 并发) + PXE+iPXE 自动化流水线(Foreman/MAAS/Cobbler/Ansible) + AI 服务器整机测试(H100/A100/HGX/8 卡 + NVLink + IB) + HPC 集群测试(Linpack + MPI) + 信创全栈(鲲鹏/海光/昇腾/飞腾) + 数据中心交付 SOP + 资产 CMDB(NetBox) + DCIM 监控**。面向数据中心交付经理 / 测试架构师。

## 一、固件升级全栈

### 1.1 固件清单（典型 2U 服务器）

```
☐ BIOS / UEFI                       (主板)
☐ BMC / iDRAC / iLO / XCC / iBMC    (管理芯片)
☐ ME / PSP                          (Intel ME / AMD PSP)
☐ CPLD                              (主板可编程逻辑)
☐ RAID 控制器                       (LSI / PERC / SmartArray)
☐ HBA                               (SAS3008/3408)
☐ NIC                               (Intel / Mellanox / Broadcom)
☐ SSD / NVMe 固件
☐ HDD 固件                          (老盘)
☐ GPU VBIOS                         (NVIDIA)
☐ PSU 固件                          (大型 PSU)
☐ Backplane Expander                (背板扩展)
☐ NVMe Switch                       (NVMe-oF)
☐ Optical Module                    (DDM 固件, 罕)
```

### 1.2 厂商一键升级总览

| 厂商 | CLI 工具 | 集中平台 | 离线包 |
|:---|:---|:---|:---|
| **Lenovo** | OneCli ⭐ / OneCli-vmware | XClarity Administrator | UpdateXpress (UXSP) |
| **Dell** | RACADM ⭐ / DSU | OpenManage Enterprise | DSU bundle / Lifecycle Controller |
| **HPE** | hponcfg / iLO REST / SUM ⭐ | OneView | Service Pack for ProLiant (SPP) |
| **Supermicro** | SMCIPMITool / SUM | SuperCloud Composer | SPP |
| **华为** | iBMA / Toolkit-SP ⭐ | FusionDirector / eSight | iBMC 包 |
| **浪潮** | ISBMC / iSM | ISCM ⭐ | iBMC 包 |
| **新华三 H3C** | HDM-CLI | HDM Manager | 离线包 |
| **中科曙光** | Tcsm | Sugon Manager | - |

### 1.3 实战流程

```bash
# 1. 现状采集
sudo dmidecode -s bios-version
sudo ipmitool mc info | grep "Firmware Revision"
sudo storcli /c0 show | grep -i firmware
sudo ethtool -i eth0 | grep firmware
sudo nvme id-ctrl /dev/nvme0 | grep -E "^fr "
sudo nvidia-smi --query-gpu=vbios_version --format=csv

# 2. 比对 HCL (厂商 Hardware Compatibility List)
# 推荐: Production Baseline / Latest Stable
# ❌ 禁: Beta / Tech Preview 上生产

# 3. 升级 (示例 Lenovo)
sudo OneCli update flash --uselocalimage --imm <ip> --user <u> --password <p>

# Dell + DSU
sudo dsu --inventory                    # 当前
sudo dsu --preview-upgrades              # 预览
sudo dsu --apply-upgrades                # 应用

# HPE + SPP
mount /dev/sr0 /mnt && cd /mnt && ./launch_sum.sh

# NVMe 固件 (通用)
sudo nvme fw-download /dev/nvme0n1 -f firmware.bin
sudo nvme fw-commit /dev/nvme0n1 -s 1 -a 1
sudo nvme reset /dev/nvme0

# Mellanox NIC
sudo mlxfwmanager --query
sudo mlxfwmanager -i fw.bin -u --force

# NVIDIA GPU VBIOS (慎!) ⭐
sudo nvflash --save backup.rom          # 备份原版!
sudo nvflash new_vbios.rom              # 慎重, 错版本 = 砖

# 4. 重启 + 复核
sudo reboot
# 再次采集 + 对比版本
```

### 1.4 红线 + 注意事项

```
☐ 备份 BMC/BIOS 配置 (RACADM export / OneCli config save)
☐ 升级窗口避开业务高峰
☐ 灰度: 1 → 10 → 100 台
☐ 升级后 ≥ 24h 观察期
☐ 单台升级顺序: BMC → BIOS → CPLD → RAID/NIC → 其他
☐ 双 PSU 不要同时拔
☐ 升级失败 → Recovery (CMOS 跳线 / DC Reset / Recovery USB)
☐ GPU VBIOS 必备份原版
☐ 升级期间禁止断电 (UPS 必)
☐ 升级日志归档 (审计 + 回溯)
☐ NVMe FW commit -a 1 (replace + activate) 风险高, 务必备份数据
```

## 二、72h 整机烤机 (Burn-in)

### 2.1 烤机 5 并发方案 ⭐

```bash
# 同时跑: CPU + 内存 + 磁盘 + 网卡 + GPU (5 项)
# 验收前必跑 72h

tmux new -d -s cpu  "stress-ng --cpu \$(nproc) --metrics-brief -t 72h"
tmux new -d -s mem  "stress-ng --vm 8 --vm-bytes 80% --vm-keep -t 72h"
tmux new -d -s fio  "fio --name=mix --rw=randrw --rwmixread=70 --bs=4k \
                        --iodepth=64 --numjobs=4 --runtime=259200 --time_based \
                        --direct=1 --ioengine=libaio --filename=/dev/nvme0n1 \
                        --output=/var/log/fio.json --output-format=json"
tmux new -d -s net  "iperf3 -c <peer> -t 259200 -P 8"
tmux new -d -s gpu  "./gpu_burn -d 259200"

# 监控 (集中, 必)
- node_exporter + Prometheus + Grafana ⭐
- IPMI 历史 (ipmitool sensor + cron)
- rasdaemon (RAS 错误)
- DCGM exporter (GPU)
- smartmontools (磁盘)
```

### 2.2 综合方案（替代）

```bash
# 一行综合
stress-ng --cpu $(nproc) --io 4 --vm 4 --vm-bytes 75% \
  --hdd 4 --hdd-bytes 10G --metrics --timeout 72h

# Phoronix Test Suite
phoronix-test-suite batch-benchmark pts/server-stress

# HPL Linpack (AI/HPC 必, 整机)
mpirun -np <核数> ./xhpl
# 配 HPL.dat: N = sqrt(MEM_bytes * 0.8 / 8), NB=192, P*Q=核数
```

### 2.3 烤机通过条件 ⭐

```
☐ 72h 0 系统挂起 / 0 panic / 0 OOPS
☐ 0 MCE (mcelog / rasdaemon)
☐ 0 ECC Uncorrectable
☐ 0 GPU Xid 错误
☐ 0 磁盘 SMART 新增 Reallocated
☐ 0 网卡 CRC / drop 增长 (差值检查)
☐ 温度持续在阈值内 (CPU < 90℃ / GPU < 85℃ / 环境 < 45℃)
☐ 性能不衰减 (前后 fio/iperf 一致 ±5%)
☐ IPMI SEL 0 Critical
☐ DCGM diag -r 3 PASS (烤后)
☐ 风扇全周期转 (无停转)
☐ PSU 双路全程供电
```

### 2.4 自动化报告

```python
# burnin_report.py - 烤机报告生成
import json, subprocess, time
from datetime import datetime

def snapshot():
    return {
        "ts": datetime.now().isoformat(),
        "mce": subprocess.check_output("mcelog --client 2>/dev/null | wc -l",
                                        shell=True, text=True).strip(),
        "xid": subprocess.check_output("dmesg | grep -ic 'nvrm.*xid' || true",
                                        shell=True, text=True).strip(),
        "nic_crc": subprocess.check_output(
            "ethtool -S eth0 | grep -i crc | awk '{print $2}'",
            shell=True, text=True).strip(),
        "smart_realloc": subprocess.check_output(
            "smartctl -A /dev/sda | awk '/Reallocated/ {print $10}'",
            shell=True, text=True).strip(),
        "gpu_temp": subprocess.check_output(
            "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits",
            shell=True, text=True).strip(),
    }

# 烤前 + 烤后对比
before = snapshot()
# ... 72h 等待 ...
after = snapshot()
json.dump({"before": before, "after": after}, open("/var/log/burnin.json", "w"),
          indent=2, ensure_ascii=False)
```

## 三、PXE + 自动化流水线 ⭐⭐⭐

> 你联想三年的老本行（PXE + Python + MySQL）的现代化版本

### 3.1 架构

```
[新机器入场]
    ↓ 网线 + 上电
[PXE Boot]
    ↓ DHCP + TFTP + HTTP (iPXE 链式)
[Live OS 内存运行] (Ubuntu Live / RHEL Live / 自定义 ISO)
    ↓
[自动采集硬件指纹] (lshw / dmidecode / smartctl / nvidia-smi → JSON)
    ↓ 上报 API
[CMDB 入库] (NetBox / Ralph / 自研 MySQL)
    ↓ 比对版本
[固件批量升级] (OneCli / RACADM / SUM / NVMe / Mellanox)
    ↓ 重启复核
[烤机 72h] (stress-ng + fio + iperf3 + gpu-burn)
    ↓ 上报状态
[Web Dashboard 看板] (Grafana / 自研 Flask/Django)
    ↓ 通过/失败
[通过 → 上架] (机柜分配 + IP 分配 + 接入监控)
[失败 → 故障池] (人工介入 / RMA / 退货)
```

### 3.2 工具栈

```
PXE / 网络启动:
  iPXE ⭐ (HTTP/HTTPS/IPv6/iSCSI 链式, 推荐)
  pxelinux (BIOS 传统)
  GRUB-PXE (UEFI 现代)

DHCP / TFTP / HTTP:
  dnsmasq ⭐ (一体, 推荐 small/mid)
  ISC dhcpd + tftpd-hpa + nginx (生产/大规模)

装机平台:
  Foreman ⭐ (RH 系, 强大)
  MAAS ⭐ (Canonical, 裸机管理)
  Cobbler (老牌)
  Razor (Puppet 系)
  Ironic (OpenStack 裸机)

OS 镜像:
  Ubuntu Server Live ⭐
  RHEL / Rocky / Alma Live
  openEuler (国产)
  自定义 ISO (mkisofs + cloud-init / kickstart)

自动化:
  Ansible ⭐ + Python + Click/Typer
  SaltStack
  Puppet / Chef (老)

CMDB / 资产:
  NetBox ⭐ (现代, Python+Django)
  Ralph
  GLPI
  自研 MySQL/PostgreSQL

Web UI:
  Grafana ⭐ (监控)
  Flask / FastAPI / Django (自研)

通知:
  Slack / 钉钉 / 飞书 / 企业微信
  PagerDuty (告警)
```

### 3.3 iPXE 配置示例

```ipxe
#!ipxe
# 自动选择 Live OS 烤机环境
:retry_dhcp
dhcp || goto retry_dhcp

# 链式加载烤机 ISO
set base http://192.168.0.10/burnin
kernel ${base}/vmlinuz initrd=initrd.img boot=live noeject \
       fetch=${base}/filesystem.squashfs \
       script=${base}/burnin.sh \
       log=${base}/upload \
       sn=$(dmidecode -s system-serial-number)
initrd ${base}/initrd.img
boot || goto retry_dhcp
```

### 3.4 烤机脚本示例

```bash
#!/bin/bash
# /var/lib/tftpboot/burnin/burnin.sh

set -e
LOG="/tmp/burnin_$(date +%s).log"
SN=$(dmidecode -s system-serial-number)
CMDB="http://192.168.0.10/api/inventory"

# 1. 硬件采集
echo "=== Inventory ===" | tee -a $LOG
{
  echo "{"
  echo "  \"sn\": \"$SN\","
  echo "  \"mfr\": \"$(dmidecode -s system-manufacturer)\","
  echo "  \"model\": \"$(dmidecode -s system-product-name)\","
  echo "  \"bios\": \"$(dmidecode -s bios-version)\","
  echo "  \"cpu\": \"$(dmidecode -s processor-version | head -1)\","
  echo "  \"mem_gb\": $(free -g | awk '/Mem/{print $2}'),"
  echo "  \"disks\": $(lsblk -J | tr -d '\n'),"
  echo "  \"nics\": $(ip -j link 2>/dev/null | tr -d '\n')"
  echo "}"
} > /tmp/inv.json

curl -X POST $CMDB -H "Content-Type: application/json" -d @/tmp/inv.json

# 2. 固件升级 (示例 NVMe)
for nvme in /dev/nvme[0-9]*; do
  nvme id-ctrl $nvme | grep -q "fr.*OLD_FW" && \
    nvme fw-download $nvme -f /tmp/fw.bin && \
    nvme fw-commit $nvme -s 1 -a 1
done

# 3. 烤机 (前台 72h)
timeout 259200 stress-ng --cpu $(nproc) --vm 8 --vm-bytes 80% \
                         --hdd 4 --metrics --timeout 72h | tee -a $LOG

# 4. 上报
curl -X POST $CMDB/result -F "sn=$SN" -F "log=@$LOG" -F "status=PASS"

# 5. 关机 / 通知机柜上架
shutdown -h now
```

### 3.5 现代化方案：MAAS

```bash
# Canonical MAAS (裸机即服务)
sudo snap install --channel=3.4/stable maas
sudo maas init region+rack --database-uri ...

# 节点入纳 (PXE Enlist)
# 机器上电 → MAAS 自动识别 → Commissioning (硬件采集) → Ready → Deploy

# 命令行
maas <user> machines read | jq
maas <user> machine commission <system-id>
maas <user> machine deploy <system-id> distro_series=jammy

# 测试脚本 (Commissioning Scripts)
# 上传烤机脚本到 MAAS, 自动跑
```

### 3.6 现代化方案：Foreman + Katello

```yaml
# Foreman 角色: 主机管理 + 装机 + 配置
- 集成 Puppet / Ansible / Salt
- 报告 + 仪表盘
- 与 RH Satellite 同源

# Provisioning Templates 自定义烤机脚本
```

## 四、AI 服务器整机测试 (H100/A100/HGX)

### 4.1 测试矩阵

```
8 卡 H100/HGX 配置:
  - 8x H100 SXM5 80GB
  - NVLink 4.0 (900GB/s)
  - NVSwitch (全互联)
  - PCIe Gen 5
  - 多张 IB CX-7 / RoCE (400G)

测试项:
☐ GPU 数量 + UUID 唯一
☐ NVLink 全互联 (nvidia-smi topo -m)
☐ NVSwitch 健康
☐ ECC enabled + 0 Uncorrectable
☐ PCIe Gen 5 x16 (全速)
☐ IB / RoCE 端口 UP
☐ GPUDirect RDMA 工作
☐ 温度 < 75℃ (风冷 H100)
☐ DCGM diag -r 4 PASS (数小时)
☐ NCCL allreduce > 800 GB/s (8 卡 NVLink)
☐ HPL-AI / MLPerf 跑分
```

### 4.2 NCCL 测试

```bash
# 单机 8 卡 all-reduce
mpirun --allow-run-as-root -np 8 \
  --mca pml ucx --mca btl ^vader,tcp,openib \
  -x NCCL_DEBUG=INFO \
  ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1

# 多机 (2 机 16 卡)
mpirun --allow-run-as-root -np 16 \
  -H host1:8,host2:8 \
  -x NCCL_DEBUG=INFO \
  -x NCCL_IB_DISABLE=0 \
  -x NCCL_IB_HCA=mlx5_0:1,mlx5_1:1 \
  ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1

# 期望:
- 单机 8 卡 NVLink: ~900 GB/s busBW
- 多机 IB 400G: 单端口 ~50 GB/s
```

### 4.3 GPUDirect RDMA

```bash
# 验证 GDR
nvidia-smi topo -m              # 看 NIC ↔ GPU 关系
ibv_devinfo | grep "state"

# 启用 GDR
modprobe nvidia_peermem
lsmod | grep peermem

# 测试 (perftest + GDR)
ib_send_bw -d mlx5_0 --use_cuda=0 <peer>
ib_write_bw -d mlx5_0 --use_cuda=0 <peer>
```

### 4.4 MLPerf / HPL-AI

```bash
# HPL-AI (NVIDIA 提供 Docker)
docker run --gpus all --rm nvcr.io/nvidia/hpc-benchmarks:24.03 \
  hpl-ai.sh --dat hpl-ai.dat

# MLPerf Training (大型)
# 跑标准模型 (ResNet / BERT / GPT) 看是否达官方基准
```

## 五、HPC 集群测试

```
集群测试项:
☐ MPI 互联 (OpenMPI / Intel MPI / MVAPICH)
☐ InfiniBand 全互联 (Subnet Manager)
☐ NFS / Lustre / GPFS / BeeGFS 并行存储
☐ 时间同步 (Chrony / PTP)
☐ Slurm / PBS 调度
☐ HPL (Top500 算 FLOPS)
☐ HPCG (现实负载)
☐ STREAM (内存)
☐ OSU MPI Benchmarks (互联)

工具:
- HPL ⭐ (Top500 标准)
- HPCG (内存密集真实负载)
- OSU MPI Benchmarks (osu_latency, osu_bw, osu_allreduce)
- IOR (并行 IO)
- mdtest (元数据)
- Linktest (NVIDIA ClusterMax)
- nccl-tests (AI 集群)
```

## 六、信创全栈

### 6.1 国产服务器矩阵

| CPU | 厂商 | 架构 | 服务器代表 |
|:---|:---|:---|:---|
| 鲲鹏 920/950 | 华为/超聚变 | ARMv8.2 | TaiShan / FusionServer |
| 海光 C86/Hygon | 海光 | x86 (Zen 衍生) | 中科曙光 / 浪潮 |
| 飞腾 FT-2500/D2000 | 飞腾 | ARM v8 | 长城 / 长虹 / 中兴 |
| 兆芯 KH/KX | 兆芯 | x86 | 联想开天 |
| 龙芯 3C5000/3D5000 | 龙芯 | LoongArch | 自主 + 长城 |
| 申威 SW26010 | 申威 | Alpha 衍生 | 神威·太湖之光 |

### 6.2 国产 GPU / NPU 矩阵

| 厂商 | 产品 | 用途 |
|:---|:---|:---|
| 华为昇腾 | Ascend 910B/C / 310 | AI 训练 / 推理 |
| 海光 | DCU Z100/K100 | 通用计算 / AI |
| 摩尔线程 | MTT S系列 | 通用 GPU |
| 寒武纪 | 思元 370/590 | AI 推理 |
| 天数智芯 | Iluvatar BI-V100 | AI 训练 |
| 壁仞 BR100 | 通用 GPU | AI |
| 燧原 i20 | AI 推理 | |
| 沐曦 C500 | 通用 GPU | AI |

### 6.3 国产 OS / 软件栈

```
OS:
  openEuler ⭐ (华为, 开源, 主流)
  麒麟 (银河麒麟 / 中标麒麟, 商业)
  统信 UOS
  Anolis OS (阿里)
  OpenCloudOS (腾讯)

DB:
  TiDB / OceanBase ⭐ / GaussDB / DM / Kingbase / TDSQL

中间件:
  TongWeb / 东方通 / 普元 / 中创

容器:
  iSulad (华为, 替代 Docker)
  K8s 国产发行: HCE / OEE / KubeSphere
```

### 6.4 测试工具适配

```
通用工具兼容性:
☐ stress-ng / fio / iperf3      → ✅ 全平台
☐ memtester / Phoronix          → ✅ 大部分
☐ DCGM                          → ❌ 仅 NVIDIA, 国产用 npu-smi
☐ Linpack (Intel MKL)           → ❌ 仅 Intel
☐ KML-Linpack (华为)            → ✅ 鲲鹏专版
☐ MegaRAID                      → ⚠️ 部分国产 RAID 用专版
☐ Mellanox MFT                  → ⚠️ 部分国产 NIC 用厂商工具

测试要点:
☐ 鲲鹏 NUMA (多 die 多 socket, 拓扑复杂)
☐ 海光 SME / SEV (机密计算)
☐ 飞腾 ARM 大小核 (部分型号)
☐ 信创全栈兼容 (DB + 中间件 + 应用)
☐ 国密 SM2/3/4 CPU 加速 (验证卸载)
☐ 等保 / 关基 / 自主可控合规
```

### 6.5 信创实战命令

```bash
# 华为昇腾
npu-smi info
npu-smi info -t board -i 0
npu-smi info -t temp -i 0
npu-smi info -t power -i 0
hccn_tool -i 0 -info                  # HCCN 网络
hccn_tool -i 0 -link -g               # 链路

# 海光 DCU
rocm-smi
rocminfo
rocm-bandwidth-test

# 鲲鹏 CPU 拓扑
numactl -H
lstopo
sudo apt install hisi-kunpeng-tools   # 华为工具集
```

## 七、数据中心交付 SOP

### 7.1 交付流程（机柜级）

```
1. 入库验收
   ☐ 外包装 / 数量 / SN 核对
   ☐ 配件清单 (轨道 / 线材 / 备件)

2. 拆箱体检
   ☐ 外观无损
   ☐ 通电 POST 通过
   ☐ 基础采集 (dmidecode / lshw)
   ☐ DOA 退货流程

3. 固件基线
   ☐ 比对推荐固件
   ☐ 批量升级 (PXE 自动化)
   ☐ 验证升级成功

4. 烤机 72h
   ☐ CPU + MEM + DISK + NET + GPU 并发
   ☐ 监控告警接入
   ☐ 通过 / 失败判定

5. 上架
   ☐ 机柜位置 (机房 + 列 + U 位)
   ☐ 电源接线 (双路独立)
   ☐ 网络接线 (Mgmt + Data + IPMI)
   ☐ 标签贴附

6. 网络配置
   ☐ BMC IP / Mgmt IP / Data IP
   ☐ VLAN / Bonding / Subnet
   ☐ 监控 + 告警接入

7. 业务交付
   ☐ CMDB 入库
   ☐ 监控 (Prometheus / Zabbix / DCIM)
   ☐ 备份 (BMC 配置 / 系统镜像)
   ☐ 业务方接收 (邮件 / 工单)

8. 文档
   ☐ 测试报告 (硬件 + 固件 + 烤机)
   ☐ 配置基线
   ☐ 告警接收人
   ☐ 退役/RMA 流程
```

### 7.2 故障件 RMA

```
☐ 现象记录 (dmesg / SEL / SMART / Xid)
☐ 厂商工单 + SN + Part Number
☐ 备件到货 + 替换 SOP
☐ 替换后烤机验证
☐ CMDB 更新 + 资产对接
☐ 旧件返厂 (数据擦除必)
```

## 八、资产 CMDB (NetBox)

```bash
# NetBox 安装 (Docker)
git clone https://github.com/netbox-community/netbox-docker
cd netbox-docker && docker compose up -d

# API 上报示例
curl -X POST http://netbox/api/dcim/devices/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "srv-01",
    "device_type": 1,
    "device_role": 1,
    "site": 1,
    "rack": 1,
    "position": 10,
    "face": "front",
    "serial": "ABC123",
    "asset_tag": "DC001"
  }'

# 字段:
- 站点 / 机柜 / U 位
- 厂商 / 型号 / SN / Asset Tag
- 电源接线
- 网络接口 (Mgmt / Data / IPMI / VLAN / IP)
- 配置文件 (BMC / BIOS 版本)
- 业务关联 (Tenant / Service)
```

## 九、DCIM 监控

```
工具:
  Prometheus ⭐ + node_exporter + ipmi_exporter + dcgm_exporter
  Grafana ⭐ 仪表盘
  Zabbix (传统, IPMI 支持好)
  Datacenter Infrastructure Management:
    Schneider EcoStruxure IT
    Vertiv Trellis
    Sunbird DCIM
    国产: 中科曙光 / 华为 DCIM

监控项:
  ☐ CPU 温度 + 频率 + 负载
  ☐ 内存 ECC 错误 + 使用率
  ☐ 磁盘 SMART + IOPS + 延迟
  ☐ 网络 带宽 + 丢包 + CRC
  ☐ GPU 温度 + 功率 + Xid
  ☐ BMC SEL + 风扇 + PSU
  ☐ 机柜电流 / PDU
  ☐ 机房温湿度

告警:
  Alertmanager ⭐ + 钉钉/飞书/Webhook
  PagerDuty (商业)
  SEL 转发到 NMS (SNMP Trap)
```

## 十、Checklist（高级）

```
固件:
☐ BIOS / BMC / CPLD / RAID / NIC / NVMe / GPU 全栈
☐ 厂商工具熟练 (OneCli/RACADM/SUM/iBMA)
☐ NVMe FW + Mellanox MFT
☐ GPU VBIOS 备份 + 升级
☐ 升级 SOP + Recovery

烤机:
☐ 72h 5 项并发 (CPU+MEM+DISK+NET+GPU)
☐ 监控集中 + 告警
☐ 通过条件全部满足
☐ 自动化报告

PXE 流水线:
☐ iPXE / Foreman / MAAS / Cobbler 任一精通
☐ 采集 → 升级 → 烤机 → 上架 自动化
☐ Ansible + Python 脚本
☐ CMDB (NetBox) 入库

AI 服务器:
☐ 8 卡 H100 / HGX 测试
☐ NVLink + NVSwitch + IB / RoCE
☐ NCCL + GPUDirect RDMA
☐ DCGM diag -r 4
☐ MLPerf / HPL-AI

HPC 集群:
☐ MPI 互联 + IB
☐ 并行存储 (Lustre / GPFS)
☐ HPL / HPCG / OSU benchmark

信创:
☐ 鲲鹏 / 海光 / 飞腾 适配
☐ 昇腾 / DCU / 摩尔线程 NPU
☐ openEuler / 麒麟 / UOS
☐ 国密 + 等保 + 关基

交付 SOP:
☐ 入库 → 体检 → 固件 → 烤机 → 上架 → 网络 → CMDB → 业务交付
☐ 故障件 RMA 流程
☐ DCIM 监控 + 告警

文档:
☐ 测试报告自动化
☐ 配置基线
☐ 资产 CMDB
☐ Postmortem
```

## 十一、推荐栈（高级）

```
固件:        Lenovo OneCli ⭐ + Dell RACADM/DSU + HPE SUM + 华为 iBMA + NVMe + Mellanox MFT
烤机:        stress-ng + fio + iperf3 + gpu-burn + HPL + Phoronix (72h 并发)
PXE 平台:    iPXE ⭐ + Foreman ⭐ / MAAS ⭐ + Ansible ⭐ + Python
CMDB:        NetBox ⭐ + 自研 MySQL
监控:        Prometheus ⭐ + node_exporter + ipmi_exporter + dcgm_exporter + Grafana
AI 服务器:   DCGM diag -r 4 + nccl-tests + perftest + GDR + MLPerf
HPC:        HPL + HPCG + OSU MPI Benchmarks + IOR + Slurm
信创:        华为 FusionDirector + 浪潮 ISCM + KML-Linpack + npu-smi + rocm-smi
故障 RMA:    厂商工单 + 备件 + 替换 SOP + 数据擦除
DCIM:       Prometheus + 国产 (中科曙光 / 华为 DCIM)
报告:        自研 HTML/Excel + Allure + Grafana 仪表盘
通知:        钉钉 / 飞书 / 企业微信 + PagerDuty (商业)
```

> 📖 **核心判断**：硬件测试高级 = **固件全栈(BIOS/BMC/RAID/NIC/NVMe/GPU + OneCli/RACADM/SUM) + 72h 整机烤机(5 项并发 + 监控集中) + PXE 自动化流水线(iPXE+Foreman/MAAS+Ansible+NetBox CMDB) + AI 服务器(H100/HGX 8 卡 + NVLink + NCCL + GDR + DCGM-r4) + HPC 集群(MPI + IB + HPL/HPCG/OSU) + 信创全栈(鲲鹏/海光/昇腾/飞腾 + openEuler/麒麟) + 数据中心交付 SOP + DCIM 监控**。能给整个数据中心(10-1000 台)做交付 + 烤机 + 上架 + 监控 + RMA 全流程, 就具备数据中心交付经理 / 硬件测试架构师能力。**高级的本质 = 从单机操作升级到机柜级 / 机房级批量自动化 + 全栈固件 + AI/HPC 集群整体验证 + 信创替代落地。**
