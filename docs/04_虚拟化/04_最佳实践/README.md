# 最佳实践

> 虚拟化最佳实践 = **平台选型决策 + 资源规划与超分基线 + HA 与容灾 + 备份策略 3-2-1 + 监控告警 + 变更纪律 + 安全合规 + 容量水位 + 排查 SOP + 国产化路线**。本章把"会装"升级到"会运营"，给可复制的工程化方案。

## 一、平台选型决策树

### 1.1 决策矩阵

```
规模 < 10 主机 / < 100 VM
  ├─ 学习/实验:      Proxmox VE + Ceph
  ├─ 中小企业:       Proxmox VE / ZStack ⭐
  └─ Windows 系:    Hyper-V Failover Cluster

规模 10-100 主机
  ├─ 通用:           Proxmox VE 集群 + PBS
  ├─ 强 Web UI:     oVirt / ZStack
  └─ 国产替代:       SmartX / 深信服 aCloud

规模 100+ 主机
  ├─ 私有云:         OpenStack (见 05_私有云)
  ├─ 大企业:         VMware vSphere (存量) / FusionCompute
  └─ 云原生:         KubeVirt + K8s

特殊:
  桌面虚拟化:        Citrix / 华为云桌面 / 深信服 VDI / vGPU
  AI 训练:           PCI 直通 / MIG / KubeVirt + GPU Operator
  机密计算:          SEV-SNP / TDX (公有云优先 / 海光 CSV 国产)
  超低延迟:          KVM-RT / DPDK
  多租户 SaaS:       Kata / Firecracker / KubeVirt
```

### 1.2 国产化优先矩阵

| 场景 | 第一替代 | 第二替代 | 备注 |
|:---|:---|:---|:---|
| VMware vSphere | **ZStack / 深信服 HCI** | 华为 FusionCompute | 中小用 ZStack，超融合用 SmartX/深信服 |
| Veeam | **Vinchin** | 爱数 / 鼎甲 | 兼容主流 hypervisor |
| Citrix VDI | 华为云桌面 / 深信服 aDesk | 锐捷 | 信创桌面 |
| Microsoft S2D | 浪潮 InCloud / 联想凌拓 | | |
| Nutanix | SmartX | 深信服 / 华为 | |

### 1.3 选型 5 问

```
1. 规模 - 当前 / 3 年后？
2. 预算 - 商业 vs 开源 ROI？
3. 团队 - 有多少人懂这个栈？
4. 国产化 - 是否必须（信创/等保）？
5. 工作负载 - VM / 容器 / GPU / 数据库 / 桌面比例？
```

## 二、资源规划与超分基线

### 2.1 超分指导

| 资源 | 默认超分 | 关键业务 | 红线 |
|:---|:---|:---|:---|
| **vCPU** | 1:2-1:4 | 1:1 (DB/RT) | < 75% Host CPU 利用 |
| **vMem** | 不超分 (推荐) 或 1:1.2 | 1:1 | 看 swap 是否被用 |
| **vDisk (Thin)** | 可 1:2 | 1:1 | 实际占用 < 80% |
| **Network** | 不超分 | | 接口 < 60% 峰值 |

### 2.2 容量水位红线

```
Host CPU avg     <  60%   预警
Host CPU peak    >  80%   工单
Host Mem         >  85%   工单（不算 cache）
Host swap used   >  0     立即查
存储池           >  75%   工单，> 85% 紧急扩
集群剩余资源     可承载 N-1 故障 → 触发扩容

接口 / 流量      >  60%   预警，> 80% 工单
快照数 / VM      <  3     超过定期 commit
单 VM RAID 重建  时间窗  晚上低峰
```

### 2.3 资源画像（必备）

```
每月输出:
  - Host 总核数 / 内存 / 存储
  - 实际分配 / 实际使用 / 超分比
  - Top 10 大 VM / 高负载 VM / 闲置 VM
  - 计划下月预留
  - 国产化进度 %
```

## 三、HA 与容灾

### 3.1 HA 三件套

```
1. 主机级 HA
   ☐ 节点 ≥ 3
   ☐ 心跳网独立 (corosync / VRRP)
   ☐ Fencing / Watchdog
   ☐ 自动迁移已开

2. 存储 HA
   ☐ 共享存储副本 ≥ 3 (Ceph) 或 SAN 双控
   ☐ 多路径 multipath
   ☐ 网络冗余 LACP

3. 网络 HA
   ☐ 物理双网卡 LACP/MLAG
   ☐ 上联双交换机
   ☐ 业务/管理/存储 三网分离
```

### 3.2 容灾级别

```
RTO   恢复时间目标
RPO   数据丢失目标

Tier 0  本地备份                 RTO 4h   RPO 24h
Tier 1  跨机房备份               RTO 2h   RPO 4h
Tier 2  跨机房热备 (异步)        RTO 30m  RPO 15m
Tier 3  双活 (同步存储)          RTO 5m   RPO 0
Tier 4  跨地域双活               RTO 1m   RPO 0
```

### 3.3 演练频率

```
☐ 月度: 单 VM 故障切换
☐ 季度: 单节点故障 + Live Migration
☐ 半年: 单存储节点故障
☐ 年度: 整 IDC 切换 / 备份恢复全链
```

### 3.4 双活方案

```
Proxmox VE + RBD Mirror   异步 (RPO 分钟)
oVirt + Gluster Geo-Rep   异步
VMware SRM + 同步存储     RPO 0（贵）
华为 OceanStor 同步       国产
SmartX Metro 双活         国产

注意:
  - 双活成本翻倍
  - 网络延迟 < 5 ms / RTT < 10 ms
  - 仲裁节点 (第三站点)
```

## 四、备份策略 3-2-1

### 4.1 3-2-1 准则

```
3 份: 在线 + 近线 + 离线
2 介质: 不同介质（SSD + HDD + 磁带 + 对象存储）
1 异地

加强版 3-2-1-1-0:
  + 1 不可变 (S3 Object Lock)
  + 0 验证错误
```

### 4.2 PBS（Proxmox Backup Server）部署

```
独立物理机:
  - 中端 X86 服务器
  - ZFS RAIDZ2 / RAID6
  - 大盘 HDD + SSD log/cache
  - 网络 10G+
  
特性:
  - 客户端去重 (一般 < 5% 增量)
  - 增量 forever
  - 加密 + 签名
  - 完整性校验

集群:
  PBS 1 主 + PBS 2 远程同步
  Object Store offload (S3) 可选
```

### 4.3 备份保留策略

```
3-7-4-12-3 模式:
  保留最近 3 天每日
  保留最近 7 周每周
  保留最近 4 月每月
  保留最近 12 月（季度）
  保留最近 3 年（年度）

PBS 范例:
keep-last      3
keep-daily     7
keep-weekly    4
keep-monthly   12
keep-yearly    3
```

### 4.4 验证（防"看似成功"）

```
每月:
  ☐ 随机抽 1-3 个 VM 完整恢复 → 启动 → 验证应用
  ☐ PBS Verify Job 完整性校验
  ☐ 异地副本同步差距 < 24h

每季:
  ☐ 一次完整 RTO 演练
  ☐ 一次跨机房恢复

每年:
  ☐ DR 红蓝对抗
```

### 4.5 防勒索

```
☐ PBS 加密 + 私钥离线保管
☐ S3 Object Lock (不可变)
☐ 备份网络隔离 / 单向 push
☐ 备份账号不能登业务
☐ 关键 VM 备份保留更久
```

## 五、监控告警

### 5.1 监控分层

```
Host:    Prometheus + node_exporter
Hypervisor:  libvirt_exporter / vcenter_exporter / pve_exporter
存储:    ceph_exporter / smart_exporter
网络:    snmp_exporter
VM:     guest agent (CPU/Mem 真实使用) + node_exporter
应用:    业务自定义 metric / blackbox
日志:    Loki / Filebeat → ES
```

### 5.2 告警分级标准

> 具体 PromQL 规则详见 [02_进阶](../02_进阶/README.md#92)。

| 级别 | 告警项 | 响应时效 | 通知方式 |
|:---|:---|:---|:---|
| **P0 Critical** | VM 关机 / 集群节点掉线 / Host swap 使用 | 立即（≤5min） | 电话 + 短信 + IM |
| **P1 Warning** | Host CPU > 85% / Host Mem > 90% / 存储池 > 80% | 15min 内 | 短信 + IM |
| **P2 Notice** | 备份失败 / 接口错包 / VM 高 CPU | 1h 内 | IM 工单 |
| **P3 Info** | 容量趋势预警 / 超分比偏高 | 日报 | 日报/周报 |

决策标准:
  ☐ P0 必须有 runbook + 自动化恢复（如 VM evacuate）
  ☐ P1 需人工介入 + 工单跟踪
  ☐ P2/P3 纳入容量治理月报
  ☐ 告警合并: 同一对象 5min 内同级别告警合并为一条
  ☐ 静默窗口: 计划维护期间静默 P1/P2，保留 P0

### 5.3 监控大盘必备

```
Cluster Overview:
  - 总 CPU/Mem/Storage 资源 + 已分配 + 已使用
  - VM 总数 / 运行中 / 故障
  - 节点列表 + 状态
  - 警告/严重告警分布

Per-Host:
  - CPU/Mem/Disk/Net 实时 + 历史
  - VM 数 / 各 VM CPU/Mem 占比
  - NUMA 节点利用

Per-VM:
  - CPU/Mem 真实使用 (guest)
  - 磁盘 IOPS / 吞吐
  - 网卡 PPS / 流量
  - 应用 health
```

## 六、变更管理

### 6.1 变更分级

```
小变更    单 VM 加内存/CPU、加盘                  on-call
中变更    VM 迁移、模板更新、补丁                  审批
大变更    集群升级、存储扩容、网络改造             评审会 + 灰度
特变更    Hypervisor 升级、HA 配置、固件          停机窗口
```

### 6.2 变更纪律

```
1. 工单先行（含影响 / 回滚 / 时间窗）
2. 配置备份 (XML / pvecm dump / vCenter cfg)
3. 灰度（单 VM → 单 Host → 集群）
4. 监控大盘 + 持续 ping
5. 双人复核（核心节点）
6. 失败立刻回滚（先恢复，后定位）
7. 完成后回填工单 + 复盘
```

### 6.3 标准变更模板（参考）

```bash
#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d-%H%M%S)
VM=${1:?vm name}

# 1. 快照（短期保险）
virsh snapshot-create-as "$VM" "pre-$TS" --atomic

# 2. 备份 XML
virsh dumpxml "$VM" > /backup/$VM.$TS.xml

# 3. 应用变更
virsh setvcpus "$VM" 8 --config --live
virsh setmem "$VM" 16G --config --live

# 4. 验证
virsh domstats "$VM" --vcpu
ssh "$VM" 'nproc && free -h'

# 5. 失败回滚
trap 'virsh snapshot-revert "$VM" "pre-$TS"' ERR

# 6. 24h 后清快照
echo "rm-snap: virsh snapshot-delete $VM pre-$TS"
```

## 七、安全合规

### 7.1 Host 加固

```
☐ 最小化安装 (无图形/GUI)
☐ SELinux/AppArmor enforce
☐ sVirt 启用 (libvirt 默认)
☐ 关闭无关服务
☐ SSH 密钥 + 禁 root + MFA
☐ 内核 + 微码 + 固件定期升级
☐ /var/lib/libvirt/images 权限 660
☐ libvirt TLS (跨主机 API)
```

### 7.2 网络隔离

```
管理网    SSH/API/监控    专用 VLAN + ACL
业务网    生产流量         分租户 VLAN/VXLAN
存储网    Ceph/SAN/NFS    专用 VLAN + 10G+
迁移网    Live Migration  独立网，加密
带外      IPMI/iDRAC       专用网，跳板机
```

### 7.3 多租户隔离

```
计算:   不同租户 VM 不混宿主（关键场景）
网络:   VLAN / VXLAN 隔离
存储:   不同 pool / namespace
权限:   RBAC + 项目 (project)
密钥:   各租户独立
合规:   SEV-SNP / TDX 机密计算
```

### 7.4 等保 2.0 三级要点（虚拟化）

```
☐ 身份鉴别: SSO + MFA + 强密码
☐ 访问控制: RBAC + 最小权限
☐ 安全审计: 操作日志 6 月+
☐ 入侵防范: HIDS + 漏扫
☐ 恶意代码: 防病毒 + 签名验证
☐ 数据完整性: 备份 + 校验
☐ 数据保密性: 传输 TLS + 存储加密
☐ 数据备份: 异地 + 异质
☐ 剩余信息保护: 删 VM 抹盘
☐ 个信保护: 涉敏感数据加密
☐ 国密: SM2/SM3/SM4 接入
```

### 7.5 国密 / 信创

```
合规要求:
  - 党政 / 关基 必上信创
  - CPU: 鲲鹏 / 飞腾 / 海光 / 龙芯 / 申威
  - OS: openEuler / 麒麟 / UOS / Anolis
  - 虚拟化: FusionCompute / 深信服 / ZStack
  - GPU: 摩尔 / 沐曦 / 寒武纪 / 昇腾
  - 加密: 国密卡 / Tongsuo / GmSSL
```

## 八、容量管理

### 8.1 上线前 Capacity Sizing

```
公式简版:
  每节点 vCPU 容量 = 物理核 × 超分系数 × (1 - HA 预留)
  每节点 vMem 容量 = 物理内存 × 0.95 × (1 - HA 预留)
  
HA 预留 N-1: 5 节点集群 → 80% 安全水位
HA 预留 N-2: 5 节点集群 → 60% 安全水位

存储:
  原始容量 × 0.85 × (1 / 副本数 或 EC 比例)
  - 25% 缓冲 (碎片 / OSD failure)
```

### 8.2 闲置 / 僵尸 VM 治理

```
每月扫:
  ☐ 关机 > 30 天 VM        → 通知所有人 → 删
  ☐ CPU avg < 5% 且 IO < 1/s 30 天 → 降配
  ☐ 长期无 login (last 30d) → 通知
  ☐ 占大磁盘但未实际用     → thin / 缩容

工具:
  - virsh domstats + 自研脚本
  - PVE community plugin
  - vROps (VMware)
```

## 九、排查 SOP

### 9.1 用户报"VM 卡" 6 步法

```
1. 范围: 单 VM / 多 VM / 全 Host？
2. 看 Host: top / vmstat / iostat / pidstat
3. 看 VM:  virsh domstats / guest agent / 内 top
4. 看存储: 后端 IOPS / 队列 / 副本健康
5. 看网络: ip -s / ethtool -S / ss
6. 看历史: Prometheus 大盘 (24h/7d 对比)
```

### 9.2 关键命令速查

```bash
# Host 总览
htop / iotop / nload / atop

# VM 实时
virsh domstats vm01
virsh top                                       # PVE 没有，自己脚本
nvidia-smi pmon

# 磁盘
iostat -xz 2
fio --name=test --filename=/path --rw=randread --bs=4k --iodepth=64 --runtime=30s --time_based

# 网络
iperf3 -c host
tcpdump -i vnet0 -nn

# 内核日志
dmesg -T | tail -100
journalctl -u libvirtd -n 200

# Hypervisor 日志
/var/log/libvirt/qemu/vm01.log
/var/log/messages
```

### 9.3 常见症状定位

| 症状 | 优先查 |
|:---|:---|
| VM 整体慢 | Host CPU 是否打满 / NUMA 是否跨 |
| VM 磁盘慢 | 存储队列 / virtio-blk vs scsi / cache 模式 |
| VM 网慢 | vhost-net / 多队列 / 上联交换机 |
| VM 内存抖 | balloon / KSM / swap |
| Host 频繁重启 | 看 BMC / mce / 硬件 |
| 迁移失败 | 共享存储 / CPU 兼容 / 网络 MTU |
| 快照后变慢 | qcow2 链太长 → blockcommit |
| 重启后丢盘 | XML 与实际 source 不一致 |

## 十、Toolbox

### 10.1 平台工具

```
管理面板:  virt-manager / Cockpit + cockpit-machines / PVE Web / Harvester UI
CLI:      virsh / virt-install / virt-sysprep / virt-customize / virt-v2v
镜像:     qemu-img / libguestfs (guestfish) / Packer
监控:     libvirt_exporter / pve_exporter / vcenter_exporter
备份:     PBS / Vinchin / 爱数
自动化:   Terraform + Ansible (community.libvirt) + Packer
迁移:     virt-v2v / virsh migrate / SCP+convert
GPU:     nvidia-smi / nvitop / dcgmi / nvtop
```

### 10.2 排查工具

```
Host:     htop / iotop / iftop / atop / dstat
内核:     perf / bpftrace / sysstat
网络:     tcpdump / Wireshark / ss / mtr
GPU:      nvidia-smi / nvitop / dcgm
压测:     fio / iperf3 / sysbench / phoronix
镜像取证: libguestfs / guestfish
```

## 十一、典型坑（最佳实践）

| 坑 | 建议 |
|:---|:---|
| **快照当备份** | 快照是短期回滚，不是备份 |
| **没演练恢复** | 备份 == 0 直到验证 |
| **超分 1:8 上 DB** | DB 1:1 |
| **HA 心跳网与业务混** | 必须独立心跳网 |
| **共享存储无 fence** | 集群脑裂数据腐蚀 |
| **变更不快照** | 直接改 XML 灾难 |
| **没装 qemu-guest-agent** | 备份/迁移/IP 都半残 |
| **僵尸 VM 长年累积** | 月度治理 |
| **没监控 swap** | OOM 才发现 |
| **没看 NUMA** | 大 VM 跨 NUMA 性能跳水 |
| **国产化没提前测** | 上线前 2-3 月联调 |
| **vCenter 不入备份** | vCSA 也要备份 |
| **存储 75% 报警没扩** | 突发 100% → 全集群 RO |

## 十二、最佳实践 Checklist

```
架构:
☐ 集群 ≥ 3 节点
☐ 心跳/业务/存储/迁移 网分离
☐ 共享存储副本 ≥ 3 或 SAN 双控
☐ N-1 HA 预留

资源:
☐ 超分基线明确
☐ 容量水位 75%/85%/90%
☐ 月度资源画像
☐ 闲置 VM 治理

HA / DR:
☐ Fencing 启用
☐ Live Migration 测试通过
☐ 备份 3-2-1 + 不可变
☐ 月度恢复演练
☐ 年度 DR 红蓝对抗

监控:
☐ libvirt_exporter / pve_exporter
☐ VM 关机 / Host CPU/Mem/swap / 备份失败 告警
☐ 接口错包 / 存储水位
☐ 大盘集群/节点/VM 三级

变更:
☐ 工单 + 回滚 + 灰度
☐ XML 入 Git
☐ 变更窗口

安全:
☐ sVirt / SELinux/AppArmor
☐ 网络三网分离
☐ TLS API + RBAC + MFA
☐ 等保 2.0 三级自查

国产化:
☐ 一类设备替代方案
☐ ZStack / FusionCompute / SmartX 试点
☐ Vinchin 备份
☐ 国密接入
```

## 十三、典型生产架构模板

### 13.1 中小企业 (推荐)

```
3 节点 Proxmox VE 集群
  - 每节点 2x AMD EPYC + 512GB + 2x NVMe + 8x HDD
  - 25G LACP 双网卡
  - Ceph 内置 (3 副本)
  - PBS 独立节点
  
管理:
  - Web UI / API
  - Prometheus + Grafana
  - 飞书机器人告警
  
DR:
  - 异地 PBS 同步
  - 关键 VM 每日备份保留 30 天
  
国产化路径:
  - 第一步: 操作系统 openEuler/麒麟
  - 第二步: 国产 X86 (海光) 或 ARM (鲲鹏/飞腾)
  - 第三步: 商业版 ZStack / 深信服 HCI
```

### 13.2 大型企业

```
OpenStack Yoga/Bobcat
  Nova (KVM) + Cinder (Ceph + 国产 SAN) + Neutron (OVN)
  Ironic 裸金属
  Magnum K8s
  Octavia LBaaS
  Designate DNS

CMP:
  自研 / Mesosphere / Cloudify
  
DR:
  双活 (同步)  Active-Active 关键业务
  异地热备 (异步) 一般业务
  对象存储归档
```

### 13.3 信创全栈

```
CPU:        鲲鹏 920 / 海光 7390
OS:         openEuler 22.03 LTS-SP3 / 麒麟 V10
虚拟化:     FusionCompute / ZStack / 深信服 HCI
存储:       华为 OceanStor / 浪潮 / Ceph
网络:       华为 CE / H3C / 锐捷
备份:       Vinchin / 爱数
监控:       夜莺 / 阿里云 ARMS
GPU:        昇腾 910B / 摩尔 / 沐曦
桌面:       华为云桌面 / 深信服 aDesk
```

## 十四、学习路径

```
工程化 (6 月):
  1. SLI/SLO + 资源画像
  2. PBS 部署 + 月度恢复演练
  3. Prometheus + libvirt_exporter + 关键告警
  4. Terraform + Packer + Ansible 整合
  5. 变更模板 + 灰度
  6. 闲置 VM 月度治理脚本
  
国产化 (3-6 月):
  7. ZStack / FusionCompute / SmartX 试点
  8. 国密 / 信创合规自查
  9. 关键设备国产替代方案

平台化 (12 月+):
  10. CMP / 自服务门户
  11. 一键变更 + GitOps
  12. AIOps 接入（接 12_AIOps）
  13. 多云 / 混合云 (接 05_私有云)
```

> 📖 **核心判断**：虚拟化最佳实践 = **平台选型 + HA/DR + 3-2-1 备份 + 监控告警 + 变更纪律 + 安全合规 + 国产化路线**。能在白板上画出 3 节点 PVE+Ceph+PBS 架构 + 备份恢复流程 + 等保 3 级自查清单 + 国产化路径，就具备做"虚拟化负责人"的能力。**备份恢复演练 + 变更纪律 + 容量水位** 是从工程师到 SRE 团队负责人的分水岭。
