# 最佳实践

> 私有云最佳实践 = **平台选型决策树 + 容量规划与超分基线 + 资源画像 + 多租户配额 + HA/DR/双活 + 监控告警 SOP + 变更纪律 + 升级 SLURP 路线 + 安全合规(等保/国密) + 自服务门户 + FinOps + 国产化路径**。本章把"会装"升级到"会运营"，给可复制的工程化方案。

## 一、平台选型决策树

### 1.1 矩阵

```
规模 / 信创 / K8s 比例:
  < 100 节点 / 弱信创 / K8s-only → Harvester / OpenShift / Rancher
  < 100 节点 / 信创 / 混合       → ZStack / SmartX / 深信服 EDS
  100-1000 节点 / 通用           → Kolla-Ansible OpenStack
  100-1000 节点 / 信创           → 华为 FusionSphere / EasyStack / 易捷行云
  1000+ 节点                     → OpenStack 内核 + 大厂订制 (自研 CMP) 
  AI 训练专用                    → OpenStack + KubeVirt + Cluster API + GPU 切片
  边缘                           → StarlingX / KubeEdge / OpenYurt
  桌面虚拟化                     → 华为云桌面 / 深信服 aDesk / Citrix
```

### 1.2 三大判断（必问）

```
1. 必须信创吗？
   - 是 → FusionSphere / EasyStack / ZStack / 深信服
   - 否 → Kolla-Ansible / Harvester / Proxmox VE
   
2. VM:容器:GPU 比例？
   - VM > 50% → OpenStack 内核
   - 容器 > 70% → OpenShift / Rancher
   - GPU > 30% → OpenStack + Cluster API + KubeVirt
   
3. 团队规模 / 经验？
   - < 5 人，新手 → 商业产品 ⭐
   - 5-15 人，有经验 → Kolla-Ansible
   - 20+ 人，专家 → 自研 + OpenStack 内核
```

## 二、容量规划

### 2.1 节点配置基线

```
控制节点 (3+ 个):
  CPU:     32-64 核
  RAM:     128-256 GB
  Disk:    2x 480GB SSD (RAID1) + 2x 1.92TB NVMe (DB)
  Net:     2x 25G LACP (mgmt+api)
  
计算节点 (N 个):
  CPU:     48-96 核 (信创 96-128 核)
  RAM:     384-1024 GB
  Disk:    本地 1-4 TB NVMe (cache 池) + Ceph 后端
  Net:     2x 25G LACP + 1x 100G (tunnel) + 1x 100G (storage)

存储节点 (Ceph, 3+ 个):
  CPU:     32-48 核
  RAM:     256-512 GB
  Disk:    12-24x 16TB HDD + 2-4x 3.84TB NVMe (DB/WAL)
  Net:     2x 100G (public + cluster)

网络:
  TOR:     25G/100G Spine-Leaf
  上联:    100G/400G
```

### 2.2 超分基线

| 资源 | 默认超分 | 关键业务 | 红线 |
|:---|:---|:---|:---|
| vCPU | 1:3-1:4 | 1:1 (DB/AI) | Host < 75% |
| vMem | 不超分 | 1:1 | swap=0 |
| Disk (thin) | 1:2 | 1:1 | 实际 < 80% |
| Ceph 集群 | - | - | < 80% RAW |

### 2.3 容量画像（月报必备）

```
集群总览:
  - vCPU 总数 / 已分配 / 已使用 / 超分比
  - vRAM 总数 / 已分配 / 已使用
  - 存储 总容量 / 已用 / 增长趋势
  - VM 总数 / 运行 / 故障
  - 各项目资源占比 Top 10

资源结余:
  - HA N-1 预留够否
  - 下季度可承载新增 N 个 VM / N TB 卷
  - 容量扩容触发：> 70%

闲置 / 僵尸:
  - 关机 > 30 天 VM
  - CPU avg < 5% 且 IO < 1/s 的 VM
  - 长期未挂载的卷
```

### 2.4 红线水位

```
Host CPU avg < 60%      预警
Host CPU peak > 80%     工单
Host Mem > 85%           工单
Host swap used > 0       立即查
Ceph RAW > 70%           扩
Ceph PG 不平衡          rebalance
RabbitMQ 队列 > 5000     查消费
Galera replication 延迟 > 5s
API p99 > 500ms          排查
```

## 三、多租户与配额

### 3.1 域 / 项目 / 角色规划

```
Domain (部门级):    财务部 / 研发部 / 安全部 / 运维部
Project (业务级):   财务 ERP / 研发 测试 / 研发 生产 / 安全合规
Role:
  member            日常用户
  admin             项目管理员
  operator          运维（只读 + 配额调整）
  auditor           审计（只读）
  cloud_admin       全局管理员
```

### 3.2 配额模板（按等级）

| 等级 | vCPU | RAM | 存储 | 浮动 IP | LB | 描述 |
|:---|---:|---:|---:|---:|---:|:---|
| 小 | 16 | 32 GB | 200 GB | 5 | 1 | 测试 / 学习 |
| 中 | 64 | 128 GB | 1 TB | 10 | 3 | 一般业务 |
| 大 | 256 | 512 GB | 10 TB | 30 | 10 | 核心业务 |
| 超大 | 1024 | 2048 GB | 50 TB | 100 | 30 | 重点项目 |

### 3.3 自服务门户

```
开源:    Skyline + 自研工单 / Adjutant
商业:    EasyStack ECS / 阿里飞天云管 / 华为 ManageOne
功能:
  - 资源申请 / 工单审批
  - 自服务扩缩容
  - 配额可视化
  - 计费明细
  - 备份/快照自助
  - DNS/SSL 自助
```

### 3.4 RBAC 收紧

```
关键收紧:
☐ admin 角色仅给 cloud_admin
☐ 普通用户不能跨项目看
☐ 审计角色独立
☐ 关键操作（删 VM/卷/快照）二次确认
☐ 项目模板化创建（避免漂移）
☐ 所有操作日志保留 ≥ 6 月
```

## 四、HA / DR / 双活

### 4.1 HA 三件套（私有云级）

```
1. 控制面 HA
   ☐ 控制节点 ≥ 3
   ☐ MariaDB Galera 3 节点
   ☐ RabbitMQ Quorum 3 节点
   ☐ HAProxy + Keepalived VIP
   ☐ 心跳网独立

2. 计算面 HA
   ☐ Nova evacuate 自动 (masakari)
   ☐ AZ 分布 / 反亲和
   ☐ Live Migration 验证

3. 存储 HA
   ☐ Ceph 副本 3 / EC 4+2
   ☐ Mon ≥ 3
   ☐ CRUSH 故障域 rack
   ☐ 多路径 SAN
```

### 4.2 容灾级别

```
Tier 0  本地备份                RTO 4h   RPO 24h
Tier 1  跨机房备份              RTO 2h   RPO 4h
Tier 2  跨机房热备 (异步)       RTO 30m  RPO 15m
Tier 3  双活 (同步存储)         RTO 5m   RPO 0
Tier 4  跨地域双活              RTO 1m   RPO 0
```

### 4.3 双活方案

```
存储:
  Stretched Ceph (3 站点仲裁)
  华为 OceanStor HyperMetro (同步)
  浪潮 / 同有 同步双活
  
计算:
  跨 AZ 部署
  VM 反亲和 + 浮动 IP DNS 切换
  Octavia 双活 LB

控制面:
  Region 内 HA + 跨 Region 灾备复制
  Keystone Federation 跨 Region

应用:
  双活 DB (Galera / GaussDB / OceanBase)
  K8s 跨集群 (Karmada / KubeFed) (见 07_K8s)
```

### 4.4 演练频率

```
☐ 月度: 单 VM 故障切换 + 单卷恢复
☐ 季度: 单节点故障 (compute/storage/network/control)
☐ 半年: 单机房断网 / 控制平面失效
☐ 年度: IDC 整体切换 / DR 红蓝对抗
```

## 五、备份策略 SOP

> 各组件备份方案（DB/配置/卷/镜像/控制平面）详见 [02_进阶](../02_进阶/README.md#_4)。本节聚焦备份 SOP、验证频次与 Checklist。

### 5.1 备份分级 SOP

| 级别 | 对象 | 方式 | 频次 | 保留 | RTO |
|:---|:---|:---|:---|:---|:---|
| **T0** | MariaDB | mariabackup + binlog | 每日全量 + 15min 增量 | 30 天 | 2h |
| **T1** | Cinder 卷 | Cinder backup → Ceph backups pool | 按策略（每日/每周） | 90 天 | 4h |
| **T2** | 异地备份 | backup pool → S3 / 磁带 | 每周同步 | 1 年 | 24h |
| **T3** | 配置/IaC | /etc/kolla + Terraform → Git | 每次变更 | 永久 | 30min |

### 5.2 备份工具选型决策

| 场景 | 推荐工具 | 备注 |
|:---|:---|:---|
| OpenStack 原生 | Cinder backup + Freezer | 集成度高 |
| K8s 工作负载 | Velero / Kasten K10 | CNCF 生态 |
| 跨 hypervisor | Veeam | 商业，功能全 |
| 国产信创 | Vinchin ⭐ / 爱数 AnyBackup | 等保合规 |
| 容灾级 | 英方 i2 | RPO 接近 0 |

### 5.3 恢复验证 Checklist

```
☐ 每月: 1-3 个 VM 完整恢复验证
☐ 每月: 1 个卷恢复验证
☐ 每季: DB 恢复演练（mariabackup → 新实例 → 数据校验）
☐ 每年: 整集群恢复演练（控制面 + 存储 + 网络）
☐ 每次备份策略变更后: 抽样恢复测试
☐ 恢复报告归档（时间/对象/结果/问题）
```

## 六、监控告警

### 6.1 监控矩阵

```
基础设施:
  node_exporter, ipmi_exporter, smart_exporter

虚拟化:
  libvirt_exporter, openstack_exporter

存储:
  ceph_exporter, cinder_exporter

网络:
  ovn_exporter, ovs_exporter, snmp_exporter
  blackbox_exporter (业务探活)

中间件:
  mariadb_exporter, rabbitmq_exporter, memcached_exporter

平台服务:
  haproxy_exporter, keystone_exporter, neutron_exporter

应用:
  统一通过 Prometheus 抓取
```

### 6.2 必备告警（精选）

```yaml
# 控制面
- alert: ControlPlaneAPIDown
  expr: up{job=~'keystone|nova-api|neutron-api|cinder-api'} == 0
  for: 2m
  severity: critical

- alert: GaleraNodeOut
  expr: mysql_global_status_wsrep_cluster_size < 3
  for: 1m
  severity: critical

- alert: RabbitMQQueueLong
  expr: rabbitmq_queue_messages > 5000
  for: 10m

# 计算
- alert: NovaComputeDown
  expr: openstack_nova_agent_state{service='nova-compute'} == 0
  for: 5m

- alert: VMPlacementFailed
  expr: increase(openstack_nova_scheduler_failed[5m]) > 5

# 存储
- alert: CephHealthError
  expr: ceph_health_status == 2
  for: 5m
  severity: critical

- alert: CephOSDDown
  expr: count by(cluster) (ceph_osd_up == 0) > 1
  for: 5m

- alert: CephClusterNearFull
  expr: ceph_cluster_total_used_bytes / ceph_cluster_total_bytes > 0.75
  for: 30m

# 网络
- alert: OVNControllerDown
  expr: ovn_chassis_status == 0
  for: 5m

- alert: FloatingIPExhaustion
  expr: openstack_neutron_floating_ip_used / openstack_neutron_floating_ip_total > 0.85

# 备份
- alert: CinderBackupFailed
  expr: openstack_cinder_backup_status{status='error'} > 0
```

### 6.3 大盘必备

```
集群总览:    资源池 / 健康 / 各服务状态
节点级:      Host CPU/Mem/Disk/Net / VM 数 / NUMA
存储:        Ceph 容量 / OSD / PG / Pool / 性能
网络:        OVN 状态 / FIP / 流量 / API 延迟
中间件:      Galera / RabbitMQ
租户级:      项目资源占用 / 配额 / 计费
应用级:      业务 SLI/SLO
```

### 6.4 SLI/SLO 建议

```
API:          可用性 99.95% / p99 < 500ms
VM Create:    成功率 99.5% / p99 < 60s
Live Migrate: 成功率 99% / p99 < 5min
Cinder Vol:   创建成功率 99.5% / IOPS 达标
LB:          可用性 99.99%
```

## 七、变更管理

### 7.1 变更分级

```
小变更   单 VM 操作 / 配额调整 / FIP 增减            on-call
中变更   服务配置改 + reconfigure / 镜像加 / Type 加  审批
大变更   节点新增 / Ceph 扩容 / OS 升级              评审会 + 灰度
特变更   OpenStack 大版本升级 / 控制面替换            停机窗口
```

### 7.2 升级 SLURP 路线

```
2024.1 Caracal (SLURP LTS)
   ↓ 可跳级
2025.1 Epoxy (SLURP LTS)
   ↓ 可跳级
2026.1 Grand Tour (SLURP LTS, 规划)

非 SLURP:
  Dalmatian 2024.2 → Flamingo 2025.2 一定要逐个

升级前必做:
☐ Stage 集群跑通
☐ DB 备份
☐ 控制面 reconfigure 测
☐ 灰度（先 1 控制节点）
☐ 回滚方案明确
☐ 告知用户窗口
```

### 7.3 变更纪律

```
1. 工单先行（影响 / 回滚 / 窗口）
2. 配置入 Git（Kolla / Terraform）
3. Stage 灰度
4. 监控大盘 + 持续探活
5. 双人复核（控制面 + 存储）
6. 失败立刻回滚（先恢复后查因）
7. 完成回填 + 复盘
```

## 八、安全合规

### 8.1 等保 2.0 三级（默认）

```
身份鉴别:    SSO + MFA + 强密码策略
访问控制:    RBAC + 最小权限 + 项目隔离
安全审计:    操作日志 ≥ 6 月 + 异常分析
入侵防范:    边界 WAF/IDS/IPS + HIDS
恶意代码:    防病毒 + 签名
数据完整性:  传输 TLS + 存储校验
数据保密性:  传输 TLS + 卷加密 (Barbican+LUKS)
数据备份:    异地 + 异质 + 加密
剩余信息:    删 VM 必抹盘
个信保护:    敏感数据加密 + 脱敏
```

### 8.2 关基 / 等保四级

```
☐ 国密 TLS (SM2/SM3/SM4)
☐ 机密计算 (SEV-SNP / TDX / 海光 CSV)
☐ 双活 + 异地灾备 RPO≤0
☐ 国测 / 公安测评
☐ 漏洞 SLA: 高危 24h / 中 7d / 低 30d
☐ 红蓝对抗年度
☐ 日志 ≥ 12 月
```

### 8.3 安全加固清单

```
Hypervisor:
☐ SELinux/AppArmor enforce
☐ sVirt 启用
☐ 镜像权限 660
☐ libvirt TLS 跨节点 API
☐ KVM CVE 跟进 + 补丁

控制平面:
☐ 全 API TLS (内 + 外)
☐ Fernet token + 轮换
☐ keystone 后端 LDAP/OIDC + MFA
☐ HAProxy 限速 + IP allowlist 管控

网络:
☐ Tenant 间 SG 默认 deny
☐ OVN ACL + L7 防火墙
☐ FIP 池白名单
☐ 管理/业务/存储 三网分离
☐ Tenant 内 microsegmentation

存储:
☐ Cinder 加密卷
☐ Ceph 加密 (at-rest)
☐ 备份独立网 + 加密
☐ Barbican KMS / 国密 HSM

主机:
☐ SSH 密钥 + 禁 root + MFA
☐ 自动补丁 + 内核升级
☐ HIDS (osquery / wazuh)
☐ 配置基线 (CIS-Benchmark)
☐ 漏扫月度

合规:
☐ 等保 2.0 / 关基 / 数据安全法
☐ 国密接入 (Tongsuo)
☐ 测评 + 整改
☐ 隐私脱敏
```

## 九、FinOps（资源经济学）

### 9.1 计量 + 计费

```
组件:
  Ceilometer + Gnocchi (时序)
  Cloudkitty (计费)
  自研账单系统
  
项目:
  - 按资源量 (vCPU h, RAM GB·h, Disk GB·h, FIP/h, LB/h)
  - 按租户出账
  - 月度部门分摊 / 内部交易
```

### 9.2 成本优化

```
关闭闲置:
  - 关机 > 30 天 VM 通知 + 删
  - 闲置卷 / 浮动 IP / LB 月度治理
  - 镜像生命周期管理

降配建议:
  - CPU avg < 5%, mem avg < 30% → 降一档
  - SSD 卷低 IOPS → 转 HDD

资源池化:
  - Reserved / Bursting 不同价格
  - Spot 实例 (利用计算碎片)
```

### 9.3 报表必备

```
- 资源使用 Top 10 项目
- 月度增长趋势
- 浪费率（已分配未使用 %）
- TCO (总拥有成本) 分摊
- 单位算力成本 (元/vCPU·h)
```

## 十、自服务门户

### 10.1 核心功能

```
基础:
  - 资源申请（VM/卷/LB/FIP）→ 工单审批
  - 自服务扩缩容
  - 快照 / 备份 / 恢复
  - DNS / SSL 自助
  - 配额查看
  - 计费明细

进阶:
  - 应用市场（一键起 Nginx/MySQL/K8s）
  - 蓝图（Heat / Terraform 模板）
  - K8s 自服务 (Cluster API)
  - GPU 切片申请
  - 数据库即服务

平台:
  - Skyline + 自研
  - Adjutant (申请审批)
  - 阿里飞天云管 / 华为 ManageOne (商业)
```

### 10.2 工单流

```
申请 → 部门审批 → 平台审批 → 自动创建 → 资源就绪
   ↓
变更 → 工单 → 审批 → 灰度 → 验证 → 回填
   ↓
回收 → 工单 → 备份 → 删除 → 确认
```

## 十一、排查 SOP

### 11.1 用户报"VM 起不来" 6 步法

```
1. 看状态: openstack server show <vm>; fault 字段
2. 看调度: nova-scheduler 日志 (NoValidHost?)
3. 看 compute: nova-compute 日志 + libvirt
4. 看网络: neutron port-show + OVN trace
5. 看卷: cinder show + Ceph health
6. 看资源: 配额 / Placement
```

### 11.2 常用速查

```bash
# 全局状态
openstack catalog list
openstack endpoint list
openstack service list
nova service-list                                # 老命令
openstack compute service list

# 看 host
openstack hypervisor list
openstack hypervisor show <id>

# 看资源
openstack resource provider list
openstack allocation candidate list --resource VCPU=2

# 调度失败
grep -i 'NoValidHost\|insufficient' /var/log/kolla/nova/nova-scheduler.log

# 网络
openstack port list --server <vm>
openstack security group rule list <sg>
ovn-nbctl show
ovn-trace --detailed ...

# 卷
openstack volume show <vol>
ceph -s
rbd info volumes/volume-<id>

# 配额
openstack quota show <project>
```

### 11.3 故障决策树

| 症状 | 优先查 |
|:---|:---|
| VM ERROR | nova fault 字段 / scheduler 日志 |
| VM 无 IP | neutron port / DHCP agent / OVN |
| VM 慢 | NUMA / 超分 / Ceph health |
| 卷 attach 失败 | cinder-volume 日志 / iscsi/rbd auth |
| API 慢 | HAProxy / Galera / RabbitMQ |
| 控制面挂 | Galera 集群 / RabbitMQ / Keepalived |
| Ceph slow | OSD slow ops / PG / 网络 / 慢盘 |
| 升级失败 | 回滚 + 看 kolla-ansible 日志 |

## 十二、典型坑（最佳实践）

| 坑 | 建议 |
|:---|:---|
| **没规划 IP 段** | 提前 5 网划分 + 文档 |
| **超分 1:8 上 DB** | DB 项目 1:1 |
| **配额没分级** | 模板化 + 部门审批 |
| **快照当备份** | Cinder backup ≠ snapshot |
| **HA 没演练** | 月度 chaos |
| **升级跳版** | 走 SLURP LTS |
| **私钥裸放** | Barbican / Vault |
| **不监控 OVN/Ceph** | 必要告警 |
| **大变更没回滚** | 灰度 + 工单 + 双人 |
| **闲置资源不治理** | 月度报告 + 通知 |
| **vCenter 当业务 VM 跑** | 控制面独立 |
| **审计日志不到 6 月** | 等保不达标 |
| **信创不提前压测** | 上线前 3-6 月联调 |

## 十三、最佳实践 Checklist

```
架构:
☐ 3 控制 + N 计算 + 3 存储
☐ 5 网络分离 (mgmt/tunnel/ext/storage/bmc)
☐ Spine-Leaf TOR
☐ HA / Galera / RabbitMQ Quorum
☐ Skyline + Horizon

容量:
☐ 节点基线明确
☐ 超分基线模板
☐ 月度容量画像
☐ 闲置 / 僵尸治理

多租户:
☐ 域 / 项目 / 角色 3 层
☐ 配额模板化
☐ SSO + MFA
☐ 自服务门户

HA / DR:
☐ Masakari (compute HA)
☐ Live Migration 演练
☐ 备份 3-2-1
☐ 月度恢复演练
☐ 年度 DR 红蓝

监控:
☐ openstack/ceph/ovn exporter
☐ 必要告警全覆盖
☐ 大盘 集群/节点/租户/应用

变更:
☐ 工单 + 灰度 + 回滚
☐ 配置入 Git
☐ SLURP LTS 升级演练

安全:
☐ 等保 2.0 三级
☐ Barbican 加密卷
☐ 国密接入
☐ 国测 / 公安测评
☐ 漏扫 + 补丁 SLA

FinOps:
☐ 计量 + 计费
☐ 闲置降配
☐ 月度报表

国产化:
☐ 一类替代方案 (鲲鹏/海光)
☐ openEuler/麒麟试点
☐ GaussDB/OceanBase
☐ Vinchin/爱数备份
☐ 国密 HSM
```

## 十四、典型生产架构模板

### 14.1 中等规模信创私有云

```
3 控制 + 3 网络 + 3 存储 + 50 计算 + 10 GPU
  + Kolla-Ansible (Caracal/Epoxy)
  + OVN + Ceph (3 副本 + EC 备份)
  + Cluster API + KubeSphere 自服务 K8s
  + 信创: 鲲鹏 + openEuler + GaussDB
  + Vinchin 备份 + 异地
  + Keycloak SSO + MFA
  + Skyline + Prometheus + 夜莺
  + 飞书机器人告警
  + 等保 2.0 三级
```

### 14.2 大型央企主权云

```
3 Region (主备灾) × 3 AZ × 200 节点
  + Cells V2 多 cell
  + Stretched Ceph + 国产 SAN 异步
  + OpenStack + KubeVirt + OpenShift
  + 海光 CSV 机密 VM
  + 国密 Tongsuo TLS + HSM
  + 等保四级 + 关基
  + 自研云管 / Cloudpods
  + 年度 DR + 红蓝对抗
```

### 14.3 运营商 NFV（选型决策）

> 架构详情（StarlingX/DPDK/SR-IOV/Tacker）详见 [03_高级](../03_高级/README.md#112-nfv)。

| 决策项 | 选项 | 判断标准 |
|:---|:---|:---|
| 边缘平台 | StarlingX / OpenStack 轻量 | 资源 < 50 节点选 StarlingX |
| 数据面 | OVS-DPDK / SR-IOV / 双栈 | 吞吐 > 100Gbps 必须 SR-IOV |
| 编排 | Tacker / ONAP / 手动 | VNF 数 > 20 用 Tacker |
| 多地市 | Cells V2 / 多 Region | 地市 > 5 用 Cells V2 |
| 国产化 | 华为/中兴网络硬件 | 运营商招标要求 |

### 14.4 AI 训练云（选型决策）

> 架构详情（GPU 直通/MIG/Cyborg/训练数据 lake）详见 [03_高级](../03_高级/README.md#113-ai)。

| 决策项 | 选项 | 判断标准 |
|:---|:---|:---|
| GPU 切分 | PCI 直通 / MIG / vGPU | 多租户 → MIG；独占 → 直通 |
| 网络 | RoCE / IB / 400G以太 | 延迟 < 2μs 选 IB；成本优先选 RoCE |
| 编排 | Cluster API + KubeVirt / 纯 OpenStack | K8s 生态深 → CAPI；纯 VM → Nova |
| 存储 | Ceph / 并行文件系统 (Lustre/GPFS) | 大文件训练数据 → 并行 FS |
| 国产 GPU | 昇腾 910B / 摩尔 S4000 / 沐曦 | 信创要求 + 驱动成熟度 |
| 机密计算 | SEV-SNP / TDX / 海光 CSV | 跨机构联合训练必须 |

## 十五、学习路径

```
工程化（6 月）:
  1. SLI/SLO + 容量画像
  2. 配额模板 + 自服务门户
  3. Skyline + Prometheus + 关键告警
  4. SLURP LTS 升级演练
  5. 备份恢复月度演练
  6. 变更工单 + 灰度模板
  7. 国密 / 等保自查

国产化（3-6 月）:
  8. 鲲鹏 / 海光 试点
  9. 国产数据库适配 (GaussDB/OceanBase)
  10. Vinchin / 爱数 备份切换

平台化（12 月+）:
  11. 自研云管门户
  12. LLM-OPS 接入
  13. AIOps (见 12_AIOps)
  14. 主权云 / 跨境合规
```

> 📖 **核心判断**：私有云最佳实践 = **平台选型 + 容量画像 + 多租户配额 + HA/DR/双活 + 监控告警 + 变更纪律 + 升级 SLURP + 等保/国密 + FinOps + 国产化路径**。能在白板上画出 3 控制+50 计算+3 存储 全栈架构 + 配额模板 + 等保 3 级自查清单 + SLURP 升级演练流程 + 国产化路径，就具备做"私有云负责人"的能力。**备份恢复演练 + SLURP 升级 + 等保合规 + 国产化储备** 是从工程师到 SRE 团队负责人的四个分水岭。
