# Proxmox VE (PVE)

> Proxmox Virtual Environment 是开源、免费、企业级的虚拟化平台。**Broadcom 收购 VMware 后，PVE 成为中小企业、Homelab、私有云的头号迁移目标**。

## 一、PVE 是什么

```
PVE = Debian Linux
    + KVM (虚拟机)
    + LXC (Linux 容器)
    + Web 管理界面
    + 集群管理 (corosync)
    + 软件定义存储 (Ceph/ZFS)
    + 企业级备份 (PBS)
```

**一句话**：用一套开源工具栈拼起来的"VMware vSphere 平替"，但**完全免费、源码可见、按需付费订阅技术支持**。

## 二、版本演进

| 版本 | 时间 | 关键特性 |
|:---|:---:|:---|
| PVE 5.x | 2017 | Debian 9 / Ceph Luminous |
| PVE 6.x | 2019 | Ceph Nautilus / Corosync 3 |
| PVE 7.x | 2021 | Debian 11 / 内核 5.13 |
| **PVE 8.x** | 2023 | Debian 12 / 内核 6.2-6.8 / SDN GA |
| **PVE 8.2** | 2024 | **VMware ESXi 导入向导（杀手锏）** |
| **PVE 8.3** | 2024 | SDN 增强、APT 仓库优化 |
| PVE 9.x (规划) | 2025 | Debian 13 / 全新 UI |

## 三、核心架构

```
┌─────────── 单节点 ──────────────┐
│  Debian + PVE 套件                │
│  KVM (qemu-kvm)  ─→ VM           │
│  LXC            ─→ 容器           │
│  Web UI :8006                     │
└──────────────┬───────────────────┘
               │ corosync (集群心跳)
   ┌───────────┼───────────┐
   ↓           ↓           ↓
 Node-1     Node-2      Node-N      ← 最大支持 32 节点
   │           │           │
   └─── 共享存储 ──────────┘
        Ceph / NFS / iSCSI / ZFS over iSCSI
```

## 四、安装与上手

### 4.1 安装

```bash
# 下载 ISO（约 1.2GB）
https://www.proxmox.com/en/downloads

# 最小配置:
#   CPU: 支持虚拟化的 x86-64（VT-x/AMD-V）
#   内存: 2GB+（生产 32GB+）
#   磁盘: 8GB（系统） + N TB（VM 存储）
#   网卡: 1+ 张（生产 4+）

# 安装方式:
#  - 官方 ISO 一键装（推荐）
#  - 已装 Debian 上加装 PVE 仓库
```

### 4.2 首次访问

```
https://<PVE_IP>:8006
用户: root@pam
密码: 安装时设置
```

### 4.3 关闭企业仓库 + 启用社区仓库（免费用户）

```bash
# 注释企业仓库
sed -i 's/^/#/' /etc/apt/sources.list.d/pve-enterprise.list
sed -i 's/^/#/' /etc/apt/sources.list.d/ceph.list 2>/dev/null

# 添加 no-subscription 仓库
echo "deb http://download.proxmox.com/debian/pve $(lsb_release -cs) pve-no-subscription" \
  > /etc/apt/sources.list.d/pve-no-subscription.list

apt update && apt -y dist-upgrade
```

### 4.4 去除"无订阅"弹窗（可选）

```bash
sed -i.bak "s/data.status !== 'Active'/false/g" \
  /usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js
systemctl restart pveproxy.service
```

## 五、核心概念

| 概念 | 说明 |
|:---|:---|
| **Node** | 一台物理 PVE 服务器 |
| **Cluster** | 多 Node 组成集群（最多 32 节点） |
| **VM** | KVM 虚拟机 |
| **CT (LXC)** | Linux 容器（共享内核） |
| **Storage** | 后端存储（本地/NFS/iSCSI/Ceph/ZFS） |
| **Pool** | 资源池（用于权限分组） |
| **Datacenter** | 集群级配置入口 |

## 六、存储后端选择

| 类型 | 用途 | 推荐 |
|:---|:---|:---:|
| **Directory** | 本地目录（qcow2） | 入门 |
| **LVM-Thin** | 本地块存储 | 单机 |
| **ZFS** | 单机/双机镜像 | ⭐⭐⭐⭐ |
| **NFS** | 共享文件 | ⭐⭐⭐ |
| **iSCSI / iSCSI+LVM** | SAN 块存储 | ⭐⭐⭐ |
| **Ceph (集群内置)** | HCI 分布式存储 | ⭐⭐⭐⭐⭐ |
| **Ceph RBD (外部)** | 接外部 Ceph 集群 | ⭐⭐⭐⭐ |

### 6.1 Ceph 集群内置（HCI）

```
PVE 8 已经原生集成 Ceph（Pacific/Quincy/Reef）:
  • Web UI 一键创建 OSD/MON/MGR/Pool
  • 至少 3 节点起步
  • 每节点至少 1× SSD（OSD）
  • 推荐 10G+ 公网 + 10G+ Cluster 网络分离
```

### 6.2 ZFS（单机最佳）

```bash
# 创建 RAIDZ1 池
zpool create -f data raidz1 sdb sdc sdd sde

# 加进 PVE
pvesm add zfspool zfs-data -pool data
```

## 七、网络模型

### 7.1 默认 Linux Bridge

```
vmbr0 ── eth0 (上行)
   ├── VM-1 vnet
   ├── VM-2 vnet
   └── ...
```

### 7.2 高级选项

| 类型 | 用途 |
|:---|:---|
| Linux Bridge | 默认、简单 |
| Open vSwitch | 高级流量管理 |
| **SDN（PVE 8 GA）** | 分布式虚拟网络、VXLAN/EVPN |
| Bond | 链路聚合 / HA |
| VLAN-aware Bridge | 多 VLAN 共享 |

### 7.3 PVE SDN（重磅）

```
PVE 8.x SDN 支持:
  • Zone: VLAN / VXLAN / EVPN
  • VNet: 类似 vDS Portgroup
  • Subnet: IPAM 集成
  • 跨节点 L2/L3 网络

可以理解为 PVE 内置的"轻量级 NSX"。
```

## 八、集群与 HA

### 8.1 创建集群

```bash
# 在第一台节点
pvecm create my-cluster

# 在其他节点加入
pvecm add <first-node-ip>

# 查看
pvecm status
pvecm nodes
```

### 8.2 HA 配置

```
Web UI: Datacenter → HA → Add

要求:
  • 至少 3 节点（用于 quorum）
  • 共享存储 (Ceph/NFS/iSCSI)
  • 网络稳定（建议独立 corosync 网络）

效果:
  Node 宕机 → VM 在其他节点自动重启（RTO ~分钟）
```

### 8.3 Quorum / Fencing

```
Quorum: corosync 多数派投票
   ↓
失去 quorum → 节点拒绝写存储（防脑裂）
   ↓
建议: 奇数节点 / 加 qdevice（小机器做仲裁）
```

## 九、与 vSphere 对比

| 能力 | vSphere | PVE |
|:---|:---|:---|
| Hypervisor | ESXi（自研） | KVM（开源） |
| 集中管理 | vCenter | Web UI（任一节点）|
| 在线迁移 | vMotion | qm migrate / Web 拖拽 |
| HA | vSphere HA | PVE HA Manager |
| 自动调度 | DRS | ❌（社区有脚本） |
| 容错 (FT) | vSphere FT | ❌ |
| 软件存储 | vSAN | **Ceph + ZFS（内置）** |
| 微分段 | NSX | SDN（基础） |
| 备份 | 第三方 | **PBS（官方，免费）** |
| 容器 | 需 Tanzu | **LXC 内置** |
| API | REST + PowerCLI | REST + pvesh + Ansible |
| 价格 | 贵 | 免费 / 订阅 |
| 商业支持 | 强 | 中（订阅含） |

## 十、PVE 杀手特性

### 10.1 LXC 容器（vSphere 没有）

```
轻量级 Linux 容器:
  • 共享宿主机内核
  • 启动 < 1 秒
  • 内存占用 < 50MB（最小）
  • 适合：开发环境、轻服务、DNS、监控代理
```

### 10.2 PBS（Proxmox Backup Server）

```
独立产品（也免费）:
  • 增量永久备份（一次全量后只传增量）
  • 客户端去重
  • 加密 + 校验
  • 还原可恢复单文件
  • 支持 VM、LXC、宿主机
```

### 10.3 ESXi 导入向导（PVE 8.2+ 杀手锏）

```
Datacenter → Storage → Add → ESXi
  填入 vCenter 或 ESXi 地址 + 凭证
  ↓
  直接看到 vSphere VM 列表
  ↓
  右键 "Import" → 自动转换 vmdk → qcow2
  ↓
  自动注入 virtio 驱动
  ↓
  一键启动
```

> 这是 Broadcom 收购后 PVE 最重要的特性，**专为接盘 VMware 客户准备**。

### 10.4 CLI 友好

```bash
# VM 管理
qm list                          # 列出 VM
qm start 100                     # 启动 VMID=100
qm stop 100
qm migrate 100 node2 --online    # 在线迁移

# 容器管理
pct list / pct start / pct enter 200

# 集群信息
pvecm status / pvesh get /nodes

# 备份
vzdump 100 --storage backup-store --mode snapshot
```

## 十一、生产部署最佳实践

```
1. 网络分离（生产必做）:
   - 管理网 / VM 业务网 / 存储网 / 集群心跳网 / 备份网
   - 建议至少 2× 10G + Bond
   
2. 存储:
   - 中小规模: ZFS 镜像（每节点）
   - 中大规模: Ceph 3+ 节点
   - 入门混用: NFS（NAS）
   
3. 集群:
   - 至少 3 节点（HA）
   - corosync 独立网络
   - 时间同步必做（chrony）

4. 备份:
   - 单独 PBS 服务器
   - 异地副本（GC、Verify、Prune 自动化）

5. 监控:
   - PVE 自带 + Prometheus pve_exporter + Grafana

6. 防火墙:
   - Datacenter / Node / VM 三级防火墙
   - 默认 Deny + 显式 Allow

7. 自动化:
   - Ansible community.general.proxmox.*
   - Terraform telmate/proxmox provider
```

## 十二、VMware → PVE 迁移工作流

```
Step 1: 评估
   - 列出全部 VM、依赖、特性使用情况
   - 标记: vDS Portgroup / vSAN 策略 / DRS 规则 / FT
   
Step 2: PVE 环境准备
   - 3+ 节点 PVE 8.2+ 集群
   - Ceph 或 NFS/iSCSI 存储就绪
   - 网络规划完成
   
Step 3: 试迁移
   - PVE Web UI → Storage → Add → ESXi
   - 选 1-2 台无关紧要 VM 验证
   - 验证 boot、驱动、网络、性能
   
Step 4: 批量迁移
   - 关 VM → 导入 → 启动验证 → 切换 DNS/LB
   - 或在线: virt-v2v + libvirt 流式迁移
   - 安装 qemu-guest-agent
   
Step 5: 切换
   - 旧 vSphere 留 30-90 天回滚窗
   - 监控告警、备份、性能基准

Step 6: 收尾
   - vSphere 退役（退订阅、回收资源）
   - 文档更新、Runbook 重写
```

## 十三、常见坑（必看）

| 坑 | 建议 |
|:---|:---|
| 单网卡集群心跳 | corosync 必须独立或冗余网络 |
| 偶数节点没仲裁 | 加 qdevice / 转奇数 |
| Windows VM 启动慢 | 安装 **virtio-win** ISO 驱动 |
| 备份耗满 IO | dump 设 bwlimit / 错峰 |
| ZFS 内存吃满 | 设 zfs_arc_max（默认 50% RAM） |
| Ceph 网络抖动 | OSD flapping → 独立 cluster network |
| 升级翻车 | 一定先在 1 节点小步走 + 看 release notes |
| NUMA 没启 | VM 选项里启用 NUMA + CPU 类型 host |
| GPU 直通失败 | 内核参数 `iommu=on`、查 vfio 绑定 |

## 十四、运维命令速查

```bash
# 节点
pveversion -v          # 版本详情
pveperf                # 性能基准

# VM
qm config 100          # VM 配置
qm status 100          # 状态
qm guest cmd 100 network-get-interfaces

# LXC
pct list
pct enter 200          # 进入容器

# 存储
pvesm status           # 全部存储
pvesm scan iscsi <ip>  # 扫 iSCSI 目标

# 集群
pvecm status
pvecm nodes
journalctl -u corosync -f

# Ceph
ceph -s
ceph osd df tree
ceph health detail

# 备份
vzdump 100 --storage backup
pvesm status -storage backup

# API
pvesh get /nodes/<node>/qemu
pvesh create /nodes/<node>/qemu/100/clone -newid 101
```

## 十五、自动化集成

### 15.1 Ansible

```yaml
- name: 创建 VM
  community.general.proxmox_kvm:
    api_host: pve1.lab.local
    api_user: root@pam
    api_password: "{{ pve_password }}"
    name: web-01
    node: pve1
    clone: tpl-debian12
    full: true
    state: present
```

### 15.2 Terraform

```hcl
provider "proxmox" {
  pm_api_url = "https://pve1.lab.local:8006/api2/json"
  pm_user    = "root@pam"
  pm_password = var.pve_pwd
}

resource "proxmox_vm_qemu" "web" {
  count       = 3
  name        = "web-${count.index}"
  target_node = "pve1"
  clone       = "tpl-debian12"
  cores       = 4
  memory      = 8192
}
```

### 15.3 K8s on PVE

```
方案 1: Cluster API Provider Proxmox（CAPMOX）
方案 2: kubeadm + 自建脚本
方案 3: K3s/RKE2 小规模快速验证

PVE 跑 K8s 的优势: 资源弹性、快照、备份一体化
```

## 十六、PVE 适合 / 不适合场景

### ✅ 推荐

```
- 中小企业虚拟化（< 100 节点）
- Homelab / 个人实验室
- 接盘 VMware 客户（PBS + 导入向导）
- 私有云轻量替代
- 边缘节点 / 分支机构
- 开发测试环境
```

### ⚠️ 谨慎

```
- 千节点超大规模（OpenStack 更合适）
- 重度 K8s 工作负载（直接 K8s + KubeVirt）
- 必须有 FT 容错（PVE 不支持）
- 强商业 SLA 要求（VMware 仍领先）
```

## 十七、与其他开源虚拟化对比

| 维度 | PVE | XCP-ng | OpenStack | KubeVirt |
|:---|:---|:---|:---|:---|
| Hypervisor | KVM/LXC | Xen | KVM | KVM |
| 难度 | 低 | 低 | 高 | 高 |
| 规模 | 中小 | 中小 | 中大 | 中大 |
| 存储 | Ceph 内置 | 接外部 | Cinder | CSI |
| K8s 集成 | 弱 | 弱 | 中 | 原生 |
| 商业支持 | Proxmox GmbH | Vates | 多家 | Red Hat |
| 中国生态 | 活跃 | 一般 | 强 | 兴起 |

## 十八、学习路径

```
入门:
  1. Homelab 单节点装 PVE 8.x
  2. 用 LXC 跑几个轻服务（DNS/HTTP）
  3. 用 KVM 跑 Win/Linux VM

进阶:
  4. 3 节点集群 + NFS 共享存储
  5. 启用 HA + 模拟节点故障
  6. PBS 备份还原全流程
  7. Ceph HCI 部署 3 节点

实战:
  8. vSphere → PVE 迁移演练
  9. Ansible/Terraform 自动化
  10. SDN 多 VLAN/VXLAN 部署
  11. GPU 直通（PCIe Passthrough）

进阶玩法:
  12. PVE + K8s 套娃
  13. PVE + 国产化 GPU 直通
  14. PVE + AI 推理小集群
```

## 十九、未来展望

```
1-2 年:
  - 大量 VMware 客户迁入
  - PVE 9.0 发布（Debian 13 内核）
  - SDN 持续增强（更接近 NSX）
  - PBS 更强的去重和压缩

3-5 年:
  - 中小企业默认开源虚拟化方案
  - 与 K8s/KubeVirt 互操作
  - 进入信创替代清单（部分场景）
  - 商业订阅服务进一步成熟
```

> 💡 PVE 的最大魅力：**装上就能用、白嫖完整功能、想要支持就买订阅**。这是开源企业级产品最干净的商业模式，没有之一。
