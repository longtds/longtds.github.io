# 最佳实践

> 硬件测试最佳实践 = **12 项金标 + 入场 SOP + 烤机标准化 + 固件基线管理 + RAS 持续监控 + 故障 RMA 流程 + 备件管理 + 资产 CMDB + 数据擦除/EOL + 容量规划 + DC 现场作业 + 国产化采购验收**。本章把"会跑 fio"升级到"运营数据中心硬件全生命周期"。

## 一、12 项金标准

```
1.  ✅ 入场 SOP 文档化 (来料 → 体检 → 固件 → 烤机 → 上架)
2.  ✅ 固件基线管理 (生产基线 + 灰度发布 + Recovery 流程)
3.  ✅ 72h 烤机强制 (Burn-in 通过才上架)
4.  ✅ RAS daemon 持续 (ECC CE 趋势 + UE 立刻告警)
5.  ✅ DOA/AFR KPI 跟踪 (DOA < 0.5% / AFR < 2%)
6.  ✅ 备件管理 (CPU/MEM/SSD/NIC/PSU/风扇关键备件 5-10%)
7.  ✅ RMA 流程 (现象 → 工单 → 备件 → 替换 → 数据擦除)
8.  ✅ CMDB 资产化 (NetBox 全量入库 + 厂商工单系统对接)
9.  ✅ DCIM 监控 + 告警 (Prometheus + 钉钉/飞书)
10. ✅ 数据擦除 SOP (Sanitize / NIST 800-88 / 物理销毁)
11. ✅ DC 现场作业规范 (双人 / 工单 / 防 ESD / 操作日志)
12. ✅ 容量规划 + 寿命管理 (SSD 寿命 / GPU 老化 / 退役计划)
```

## 二、入场 SOP（标准化）

### 2.1 流程模板

```
[新机入场]
    ↓
[来料验收] (外包装 / 数量 / SN / 配件 / 拍照存档)
    ↓
[拆箱体检] (外观 / 通电 / POST / 基础采集)
    ↓ DOA 退货
[初步采集] (dmidecode/lshw/smartctl/ipmitool/nvidia-smi)
    ↓
[固件基线对齐] (比对 HCL + 批量升级)
    ↓
[BMC 配置] (BMC IP / 默认密码 / Redfish / NTP / SOL)
    ↓
[72h 烤机] (CPU+MEM+DISK+NET+GPU 并发)
    ↓ 失败 → 故障池
[终检] (烤后再采集 + 对比烤前 + DCGM diag)
    ↓
[上架] (机柜位置 + 电源 + 网络 + 标签)
    ↓
[网络配置] (Mgmt/Data/IPMI IP + VLAN + Bonding)
    ↓
[CMDB 入库] (NetBox + 业务关联)
    ↓
[监控接入] (Prometheus / Zabbix / DCIM)
    ↓
[业务交付] (邮件 / 工单 + 文档归档)
```

### 2.2 必备文档

```
☐ 入场 SOP 手册 (流程图 + 命令)
☐ 固件基线表 (机型 / 版本 / 升级窗口)
☐ 烤机标准 (脚本 + 通过条件 + 报告模板)
☐ 网络规划 (VLAN / Subnet / IP 段)
☐ CMDB 字段约定 (命名规范 / 标签)
☐ 故障 RMA 流程 (厂商 / 备件 / SOP)
☐ 数据擦除 SOP (Sanitize / NIST 800-88)
☐ 应急预案 (主备机房 / DC 失火 / 断电)
```

## 三、固件基线管理

### 3.1 基线策略

```
基线层级:
  Production    生产基线 (Stable, 3 个月以上验证)
  Staging       预生产基线 (1-3 个月观察)
  Testing       测试基线 (内部环境)
  ❌ Beta/Tech Preview  → 生产禁

基线表 (示例):
  机型              BIOS  BMC   RAID  NIC      NVMe
  Lenovo SR650 V3   2.10  2.20  52.x  Mlnx 4.5 1.4.x
  Dell R760         2.5.x 6.x   ...
  HPE DL380 Gen11   2.x   ...

来源:
  - 厂商 HCL (Hardware Compatibility List)
  - Production Baseline / Latest Stable
  - 内部验证通过 3 个月+

更新策略:
  季度审视 + 安全 CVE 紧急 + 业务驱动
```

### 3.2 升级灰度

```
灰度阶段:
  1 台 (Pilot, 7 天观察)
    ↓
  10 台 (Canary, 7 天观察)
    ↓
  100 台 (Rolling)
    ↓
  全量 (避开业务高峰 + 双 PSU 不同时拔)

Rollback 准备:
  ☐ 备份 BMC 配置 (RACADM/OneCli export)
  ☐ 备份 BIOS 配置 (Setup defaults 记录)
  ☐ NVMe FW 备份 (fw-log)
  ☐ GPU VBIOS 备份 (nvflash --save backup.rom)
  ☐ Recovery 工具 (CMOS 跳线 / Recovery USB / 厂商工程师)
```

### 3.3 升级 SOP

```
顺序:
  1. BMC (先, 升级后 BMC 重启 ≠ 服务器重启)
  2. BIOS / UEFI (重启)
  3. CPLD (慎)
  4. RAID / HBA / NIC / NVMe / GPU VBIOS
  5. 验证 (采集对比)
  6. 烤机 24h 观察

红线:
☐ 不双 PSU 同时拔
☐ 不升级期间断电 (UPS 必)
☐ 不跳过备份步骤
☐ 不在业务高峰升级
☐ 不混合多版本批次升级
```

## 四、烤机标准化

### 4.1 烤机分类

| 场景 | 时长 | 强度 | 通过条件 |
|:---|:---|:---|:---|
| **来料检验** | 24h | 中 | DOA 排除 + 基础健康 |
| **上架前 Burn-in** ⭐ | 72h | 高 | 全项目并发 + 温度/性能/RAS |
| **维护后验证** | 6-24h | 中 | 替换件功能验证 |
| **大促前演练** | 24h | 高 | 性能基线 + 容量验证 |
| **退役前测试** | - | - | 数据擦除 + 报废 |

### 4.2 标准烤机命令

```bash
# 5 并发 72h (tmux 标准方案, 文档化)
tmux new -d -s cpu  "stress-ng --cpu \$(nproc) --metrics-brief -t 72h"
tmux new -d -s mem  "stress-ng --vm 8 --vm-bytes 80% --vm-keep -t 72h"
tmux new -d -s fio  "fio --name=mix --rw=randrw --rwmixread=70 --bs=4k \
                        --iodepth=64 --numjobs=4 --runtime=259200 --time_based \
                        --direct=1 --ioengine=libaio --filename=/data/fio.bin \
                        --size=500G --output=/var/log/fio.json --output-format=json"
tmux new -d -s net  "iperf3 -c <peer> -t 259200 -P 8"
tmux new -d -s gpu  "/opt/gpu-burn/gpu_burn -d 259200"

# 监控 (必)
- Prometheus + node_exporter + ipmi_exporter + dcgm_exporter
- Grafana 烤机看板 (一台一面板)
- rasdaemon 持续记录
- 告警到群 (CRITICAL 立即响应)
```

### 4.3 通过条件清单 ⭐

```
☐ 72h 0 系统挂起 / 0 panic / 0 OOPS
☐ 0 MCE (mcelog --client | wc -l = 0)
☐ 0 ECC Uncorrectable (rasdaemon)
☐ ECC Correctable < 阈值 (低于厂商规格)
☐ 0 GPU Xid 错误 (dmesg | grep -i xid)
☐ 0 磁盘 SMART Reallocated/Pending 新增
☐ 0 网卡 CRC/drop 新增
☐ NVMe critical_warning = 0
☐ 温度全程 < 阈值 (CPU < 90℃ / GPU < 85℃ / 环境 < 45℃)
☐ 性能不衰减 (前后 fio/iperf/gpu_burn ±5%)
☐ IPMI SEL 0 Critical/Fatal
☐ DCGM diag -r 3 PASS (烤后)
☐ 风扇全程转 (无停转事件)
☐ PSU 双路全程供电 (无切换)
☐ 内存通道无降级 (lscpu / dmidecode 一致)
```

### 4.4 烤机失败处置

```
失败分类:
  A. 立即 DOA (硬件死) → RMA / 退货
  B. 性能衰减 → 重测 + 厂商技术介入
  C. 间歇性错误 (ECC/CRC 增长) → 隔离 + 备件替换
  D. 软件/驱动相关 → 重装驱动重测
  
处置 SOP:
  1. 现象记录 (dmesg / SEL / 监控截图 / 日志)
  2. 工单录入 (内部 + 厂商)
  3. 隔离 (停烤 + 隔离机柜位置)
  4. 厂商现场支持 + 备件
  5. 替换后重新烤机
  6. 报告归档 (Postmortem)
```

## 五、RAS 持续监控

### 5.1 RAS 三件套 (生产标配)

```bash
# 1. rasdaemon (现代, 推荐) ⭐
sudo apt install rasdaemon
sudo systemctl enable rasdaemon --now

# 2. mcelog (老但稳)
sudo apt install mcelog
sudo systemctl enable mcelog --now

# 3. edac-utils (内核接口)
sudo apt install edac-utils
```

### 5.2 关键指标 + 阈值

```
内存:
  ECC Correctable Errors (CE)
    日 < 10 (持续高 → 提前换 DIMM)
    单 DIMM 周 > 100 → RMA
  ECC Uncorrectable (DBE/UE)
    任一 → 立即 RMA (硬故障)

CPU:
  MCE Correctable
    日 < 5 (高 → 注意)
  MCE Uncorrectable
    任一 → 立即处置 (重启 → 排查 → RMA)

磁盘:
  Reallocated Sectors 增长 > 0 → 关注
  Reallocated > 100 → 准备替换
  Current Pending > 0 → 立即替换

NVMe:
  critical_warning bit 0 (available_spare 低) → 替换
  critical_warning bit 2 (设备可靠性降级) → 立即 RMA
  percentage_used > 80% → 计划替换
  unsafe_shutdowns 突增 → 排查电源

GPU:
  Xid 48 (DBE) 任一 → 立即 RMA
  Xid 79 (掉链 PCIe) 任一 → 排查 + 可能 RMA
  Xid 63/64 (Page Retired) → 监控趋势 (累计 64 个 → RMA)
  ECC Uncorrectable 任一 → 立即 RMA
```

### 5.3 监控告警

```yaml
# Prometheus + Alertmanager 示例
groups:
- name: hardware
  rules:
  - alert: ECCUncorrectable
    expr: rate(node_edac_uncorrectable_errors_total[5m]) > 0
    for: 0m
    annotations:
      summary: "{{ $labels.instance }} ECC UE detected"
      severity: critical
      
  - alert: ECCCorrectableHigh
    expr: rate(node_edac_correctable_errors_total[1h]) > 100
    for: 10m
    annotations:
      summary: "{{ $labels.instance }} ECC CE rate high"
      
  - alert: GPUXid
    expr: dcgm_xid_errors > 0
    for: 0m
    annotations:
      severity: critical
      
  - alert: NVMeCriticalWarning
    expr: node_nvme_info{critical_warning!="0"} > 0
    for: 1m
```

## 六、故障 RMA 流程

### 6.1 RMA SOP

```
1. 现象确认
   ☐ 日志收集 (dmesg / journalctl / SEL / SMART / Xid)
   ☐ 现场拍照 (LED 状态 / 物理损伤)
   ☐ 复现路径 (是否可重现)
   ☐ 业务影响评估

2. 厂商工单
   ☐ SN + Part Number 准确
   ☐ 故障现象 + 日志附件
   ☐ 工单优先级 (P1-P4)
   ☐ 联系人 + 现场窗口

3. 备件到货
   ☐ 备件 SN 录入 CMDB
   ☐ 版本 / 固件比对
   ☐ 防 ESD 包装确认

4. 替换 SOP
   ☐ 业务下线 / 漂移
   ☐ 双人作业 + 工单
   ☐ 防 ESD 手腕带
   ☐ 旧件拍照 + 标签
   ☐ 新件安装 + 拧紧
   ☐ 上电 + POST + 体检

5. 验证烤机
   ☐ 替换件功能验证 (smartctl / nvidia-smi / lspci)
   ☐ 6-24h 短期烤机
   ☐ 性能基线对齐

6. 数据擦除 + 返厂
   ☐ Sanitize / NIST 800-88
   ☐ 厂商签收
   ☐ 工单关闭

7. Postmortem
   ☐ 根因分析 (RCA)
   ☐ 是否批次问题 (排查同批次)
   ☐ 监控规则补充
   ☐ 备件库存调整
```

### 6.2 RMA KPI

```
☐ 平均 RMA 时长 < 7 天 (P1) / < 14 天 (P3)
☐ 备件到货时长 < 4h (Critical 4h SLA)
☐ 厂商响应 SLA 达成 > 95%
☐ 同批次故障率 (识别批次问题)
☐ DOA 率 < 0.5%
☐ AFR < 2% (年化)
```

## 七、备件管理

```
备件清单 (5-10% 比例):
☐ CPU                (高价值, 1-2 颗备用)
☐ 内存条             (5-10% 备份, 各厂商各速率)
☐ SSD/NVMe          (5-10% 备份)
☐ HDD                (5-10% 备份)
☐ NIC                (2-5 张, 多型号)
☐ RAID 控制器         (1-2 块 + 电池/CV)
☐ PSU                (5-10% 备份)
☐ 风扇                (5-10% 备份, 多 SKU)
☐ GPU                (高价值, 5% 备份)
☐ 主板               (极少, 厂商交付)
☐ 线缆               (网线 + 光纤 + DAC + 电源线)
☐ SFP/QSFP 模块      (5-10% 备份)

备件仓库:
☐ 防潮 + 防静电 (ESD 袋)
☐ 标签 (SN + PN + 入库日期)
☐ CMDB 入库 (位置 + 状态)
☐ 老化测试 (季度抽检, 长期库存)
☐ 出库流程 (工单 + 双签)

KPI:
☐ 关键备件库存 > 5%
☐ 备件 4h 内可达
☐ 备件年化损耗 < 10%
```

## 八、资产 CMDB

```
CMDB 必填字段:
☐ 设备 (SN / PN / 厂商 / 型号 / 入库日期)
☐ 位置 (机房 / 列 / 机柜 / U 位)
☐ 电源 (双路 PDU / 功率)
☐ 网络 (Mgmt / Data / IPMI IP + VLAN + 端口)
☐ 配置 (CPU/MEM/磁盘/NIC/GPU 配置)
☐ 固件 (BIOS / BMC / RAID / NIC 版本)
☐ 业务 (Tenant / Service / 业务线)
☐ 状态 (Active / Maintenance / RMA / Retired)
☐ 寿命 (入库日期 + 保修期 + 预计退役)
☐ 责任人 (Owner + 二线)

工具:
NetBox ⭐ (推荐, 现代, Python)
Ralph
GLPI
自研 MySQL/PostgreSQL

集成:
☐ 装机自动入库 (PXE + API)
☐ 监控自动发现 (Prometheus + relabel)
☐ 工单系统对接 (Jira / 禅道)
☐ 厂商工单 (SN 查询保修 + 工单)
☐ 仓库系统 (备件管理)
```

## 九、数据擦除 + EOL

### 9.1 数据擦除标准

```
分级 (NIST SP 800-88):
  Clear      软件擦除 (低敏感)
  Purge      固件 Sanitize (中敏感) ⭐
  Destroy    物理销毁 (高敏感)

SSD/NVMe Sanitize ⭐:
  sudo nvme sanitize /dev/nvme0 -a 1     # Block Erase
  sudo nvme sanitize /dev/nvme0 -a 2     # Overwrite
  sudo nvme sanitize /dev/nvme0 -a 4     # Crypto Erase (快, 推荐)
  sudo nvme sanitize-log /dev/nvme0

ATA/SAS:
  hdparm --security-erase <pwd> /dev/sda
  sg_sanitize --crypto-erase /dev/sda

物理销毁:
  HDD: 消磁 + 物理破碎
  SSD: 物理破碎 (粉碎机)
  存档: 销毁证书 (有资质厂商)
```

### 9.2 EOL 流程

```
1. 退役通知 (业务方 → 运维 / 提前 1 个月)
2. 数据迁移 (业务下线 / 备份)
3. CMDB 标记 Retiring
4. 数据擦除 (NIST 800-88 + 证书)
5. 物理拆机
6. 资产报废 (财务 + 厂商回收)
7. CMDB 更新 Retired
8. 文档归档
```

### 9.3 GPU / NVRAM 擦除

```bash
# GPU 显存 (可重启清除, 一般不需特殊处理)
nvidia-smi --gpu-reset

# BMC 配置擦除 (Factory Default, 退役前必)
ipmitool raw 0x32 0x66                  # Lenovo 示例
sudo racadm racresetcfg                  # Dell
sudo hponcfg -r                          # HPE

# BIOS 配置擦除
# Setup 进入 → Load Setup Defaults → 保存
# 或 CMOS 跳线 / 取电池
```

## 十、DC 现场作业规范

```
☐ 双人作业 (1 操作 + 1 监督)
☐ 工单授权 (变更管理 / CMDB)
☐ 防 ESD (手腕带 + 接地)
☐ 操作日志 (时间 / 人员 / 操作)
☐ 物品出入登记 (备件 / 工具)
☐ 拍照存档 (前后对比)
☐ 业务窗口 (避开高峰)
☐ 双 PSU 不同时拔
☐ 不带电热插拔 (除 hot-swap 件)
☐ 完成后通电验证
☐ 工单关闭 + 报告归档

机房红线:
☐ 不擅自挪动他人设备
☐ 不动他人线缆
☐ 不带饮料/食物
☐ 烟雾报警绝对禁
☐ 紧急按钮 (EPO) 严禁误碰

应急:
☐ 主备机房演练 (季度)
☐ 断电应急流程
☐ 失火预案
☐ DC 经理 24/7 值班联系
```

## 十一、容量规划

```
SSD/NVMe 寿命:
  TBW (Total Bytes Written) 估算
  percentage_used 月增 < 1% (寿命 > 5 年)
  
  示例: 3.84TB 企业 NVMe = 7000 TBW
  日均写 5TB → 7000/5/365 = 3.8 年

CPU/MEM 寿命:
  正常使用 5-7 年
  保修期 3 年 (大部分)

GPU 寿命:
  生产负载 24/7 → 4-5 年
  ECC CE 趋势 + Xid 监控

机柜电力:
  每机柜 < 80% 额定 (留余量)
  双路 PDU 不超 50% (单路故障切换)

网络带宽:
  接入层 < 70% (突发)
  汇聚层 < 50%
  核心层 < 30%

监控:
  Prometheus 长期趋势 (年)
  容量预警 (Burn Rate)
```

## 十二、国产化采购验收

```
采购前:
☐ HCL 兼容性矩阵 (CPU/GPU/OS/DB/中间件)
☐ 信创清单 (国家 / 行业目录)
☐ 国密支持 (SM2/3/4)
☐ 等保 / 关基 / 自主可控

验收:
☐ 来料 SN + 资质证明
☐ 信创认证 (国家)
☐ 兼容性测试 (整栈业务跑通)
☐ 性能测试 (基线对比国外平台)
☐ 国密验证 (CPU 加速)
☐ 文档完整 (中文)

测试矩阵:
☐ 鲲鹏 + 麒麟 + GaussDB
☐ 海光 + 麒麟 + OceanBase
☐ 飞腾 + UOS + DM
☐ 昇腾 + MindSpore / PyTorch
☐ DCU + PaddlePaddle / TensorFlow

合规:
☐ 等保 3 / 关基测评
☐ 密评 (商用密码)
☐ 信创占比 KPI (央企 100%)
```

## 十三、典型生产架构

### 13.1 中型互联网 (1000 台)

```
团队:        2-3 人 (硬件交付) + 5-8 人 (运维)
工具:        OneCli/RACADM + PXE + Foreman + NetBox + Prometheus
SLA:        DOA < 0.5% + AFR < 2% + RMA < 7 天
备件:        关键件 5-10%
监控:        Prometheus + Grafana + 钉钉/飞书告警
固件:        季度评审 + 灰度发布
合规:        信创 0-30% + 等保 2
```

### 13.2 央企数据中心 (5000+ 台)

```
团队:        15-30 人 (硬件 + DC + 备件) + 集中外包
工具:        FusionDirector/ISCM + PXE + 自研 CMDB + Prometheus + DCIM
SLA:        DOA < 0.3% + AFR < 1.5% + RMA < 4h (Critical)
备件:        关键件 8-10% + 异地容灾
监控:        DCIM (Schneider/Vertiv/华为) + 自研整合
合规:        信创 100% + 等保 3 + 关基 + 密评
HW 行动:    季度演练
```

## 十四、Checklist（最佳实践）

```
SOP:
☐ 入场流程文档化 + 培训
☐ 固件基线表 + 灰度规则
☐ 烤机标准 + 通过条件
☐ RMA 流程 + 厂商 SLA

监控:
☐ RAS 三件套 (rasdaemon + mcelog + edac)
☐ Prometheus + ipmi/dcgm exporter
☐ Grafana 看板 (硬件 / 烤机 / 容量)
☐ 告警 (钉钉/飞书 + PagerDuty)

资产:
☐ NetBox CMDB 全量入库
☐ 字段规范 + 命名约定
☐ 厂商工单系统对接
☐ 备件库存 5-10%

数据安全:
☐ Sanitize / NIST 800-88
☐ 物理销毁证书
☐ BMC/BIOS 配置擦除

现场:
☐ 双人作业 + 工单
☐ 防 ESD + 操作日志
☐ 拍照存档
☐ 应急预案

容量:
☐ SSD/GPU 寿命跟踪
☐ 机柜电力 / 网络带宽
☐ Burn Rate 预警

国产化:
☐ HCL 矩阵
☐ 信创清单
☐ 等保 / 关基 / 密评

KPI:
☐ DOA < 0.5%
☐ AFR < 2%
☐ RMA < 7 天 (P3) / < 4h 备件 (Critical)
☐ 烤机通过 > 99%
☐ 信创占比 (按业务要求)
```

## 十五、推荐栈（最佳实践）

```
SOP 文档:    Markdown + Confluence / Wiki / Notion + Git 版本
基线管理:    YAML + 厂商 HCL + 自研 + 季度评审
PXE 流水线:  iPXE ⭐ + Foreman / MAAS + Ansible + Python + NetBox API
固件升级:    OneCli ⭐ / RACADM ⭐ / SUM ⭐ / 华为 Toolkit-SP / nvme + Mellanox MFT
烤机:        stress-ng + fio + iperf3 + gpu-burn + Phoronix (72h 并发)
监控:        Prometheus ⭐ + node_exporter + ipmi_exporter ⭐ + dcgm_exporter ⭐ + Grafana
RAS:        rasdaemon ⭐ + mcelog + edac-util (生产标配)
CMDB:       NetBox ⭐ + 自研 MySQL + 厂商对接
DCIM:       Prometheus + 国产 (中科曙光 / 华为 DCIM) + 商业 (Schneider / Vertiv)
告警:        Alertmanager + 钉钉/飞书/企业微信 + PagerDuty (商业)
数据擦除:    nvme sanitize ⭐ + hdparm + sg_sanitize + 物理销毁
现场:        工单系统 + 双人 + 防 ESD + 拍照
容量:        Prometheus 长期 + Grafana + 自研报表
国产合规:    信创清单 + 等保 + 关基 + 密评 + HW 行动
```

> 📖 **核心判断**：硬件测试最佳实践 = **12 项金标 + 入场 SOP(来料→体检→固件→烤机 72h→上架→CMDB) + 固件基线管理(Production Baseline + 灰度) + RAS 三件套持续监控(rasdaemon+mcelog+edac, ECC/Xid/SMART 阈值告警) + RMA 流程(< 7 天 / Critical 4h) + 备件管理(关键件 5-10%) + NetBox CMDB 全量 + 数据擦除(NIST 800-88) + DC 现场作业规范 + 容量寿命管理 + 国产合规(信创/等保/关基)**。能给央企/大型互联网搭"硬件全生命周期 + DCIM + RMA + 备件 + CMDB + 合规"完整体系, 落地从来料 → 烤机 → 上架 → 监控 → 寿命 → 退役全闭环, 就具备数据中心硬件运营总监 / 硬件架构师能力。
