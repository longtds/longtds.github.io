# VMware vSphere

> VMware vSphere 是企业级虚拟化的事实标准。Broadcom 收购后许可变化引发了大规模"去 VMware 化"浪潮，但**存量市场仍然庞大，技术体系依然是行业基准**。

## 一、vSphere 是什么

```
vSphere = ESXi (裸金属 Hypervisor) + vCenter Server (集中管理)
          + 配套套件 (vSAN, NSX, HA, DRS, vMotion, ...)
```

- **ESXi**：直接装在物理服务器上的 Type-1 Hypervisor
- **vCenter Server**：集中管理多台 ESXi 主机的"大脑"
- **VMware Cloud Foundation (VCF)**：现在的主推套件名

## 二、版本演进与关键节点

| 版本 | 时间 | 关键特性 |
|:---|:---:|:---|
| vSphere 4 | 2009 | DRS、FT 稳定 |
| vSphere 5 | 2011 | vCenter Server Appliance（VCSA）|
| vSphere 6.0 | 2015 | vMotion 跨 vCenter |
| vSphere 6.5/6.7 | 2016-18 | HTML5 客户端、TPM 2.0 |
| vSphere 7 | 2020 | **vSphere with Tanzu**（K8s 集成）|
| **vSphere 8** | 2022 | DPU/SmartNIC 支持、AI/ML 工作负载优化 |
| vSphere 8 U3 | 2024 | NVIDIA NIM 集成、生成式 AI 支持 |

> ⚠️ **2023.11 Broadcom 完成收购**。许可证从"按 CPU 收费"改为"按核心 + 订阅"，多数客户费用上涨 2-10 倍，引发逃离潮。

## 三、核心架构

```
┌─────────────────────────────────────────┐
│         vCenter Server (VCSA)           │
│  ── 集中管理、API 入口、Web UI            │
└─────────┬───────────────────────────────┘
          │
   ┌──────┼──────┬──────┐
   ↓      ↓      ↓      ↓
 ESXi-1 ESXi-2 ESXi-3 ESXi-N
   │      │      │      │
   └──────┴──────┴──────┘
              ↓
   ┌────────────────────────┐
   │  共享存储 (vSAN/SAN/NFS) │
   └────────────────────────┘
              ↓
   ┌────────────────────────┐
   │  分布式交换机 (vDS) + NSX │
   └────────────────────────┘
```

## 四、ESXi 关键技术

| 技术 | 作用 |
|:---|:---|
| **VMFS** | VMware 专有集群文件系统 |
| **VMkernel** | Hypervisor 内核（管理 + IO + vMotion 网络）|
| **vmware-tools** | Guest 内驱动套件 |
| **EVC（Enhanced vMotion Compatibility）** | 跨代 CPU 兼容性 |
| **TPM 2.0 + Secure Boot** | 主机完整性 |

## 五、核心企业特性（你最常用的）

### 5.1 vMotion（在线迁移）

```
原 ESXi 主机 ────── VM 内存 + 状态 ──→ 目标 ESXi 主机
              (毫秒级切换，业务无感)
```

- **Standard vMotion**：跨主机
- **Storage vMotion**：跨存储
- **Cross-vCenter vMotion**：跨 vCenter
- **Long-Distance vMotion**：跨数据中心

### 5.2 HA（高可用）

```
某 ESXi 主机宕机
      ↓
HA 检测（默认 30 秒心跳）
      ↓
该主机上的 VM 在其他主机自动重启
      ↓
RTO ~分钟级
```

### 5.3 DRS（分布式资源调度）

- 自动平衡集群内主机负载
- 三档：手动 / 半自动 / 全自动
- 与 vMotion 配合实现 VM 动态迁移

### 5.4 FT（容错）

- VM 双活：主备 VM 同步运行
- RTO = 0（真零中断）
- 限制：CPU/内存有上限，开销大

### 5.5 vSAN

```
SSD/HDD 直接装在 ESXi 主机上
      ↓
vSAN 软件聚合成分布式存储池
      ↓
所有 VM 共享，无需独立 SAN
```

- HCI（超融合）形态
- 支持 RAID 1/5/6 软件级
- 与 vSphere 深度集成

### 5.6 NSX（网络虚拟化）

- 分布式防火墙、微分段
- L2-L7 全栈虚拟化
- 与 VMware Cloud Foundation 绑定

## 六、vSphere with Tanzu（K8s 集成）

```
vSphere 7+ 支持原生跑 K8s:
   ESXi 主机 → Supervisor Cluster
      ↓
   开发者用 kubectl 直接部署 VM 或 Pod
      ↓
   vSphere Pod = ESXi 上的"轻量级 VM 容器"
```

**适用场景**：传统 VM + K8s 混合环境，无需独立搭 K8s 集群。

## 七、日常运维场景

| 场景 | 工具 / 命令 |
|:---|:---|
| 创建 VM | vSphere Client / `govc` CLI / Terraform |
| 批量管理 | **PowerCLI**（PowerShell 模块，超强）|
| 自动化 | **govc**（Go 写的 vSphere CLI） |
| 监控 | vCenter Performance Charts + Aria Operations |
| 备份 | Veeam / Commvault / Rubrik |
| 升级 | vSphere Lifecycle Manager (vLCM) |
| 故障排查 | `esxtop` / `vmkfstools` / `vm-support` |

### PowerCLI 示例

```powershell
# 连接 vCenter
Connect-VIServer vcenter.lab.local

# 批量克隆 VM
1..10 | ForEach-Object {
  New-VM -Name "web-$_" -Template "tpl-rhel9" `
         -VMHost (Get-VMHost | Get-Random) `
         -Datastore "vsan-datastore"
}

# 查找占用 CPU 高的 VM
Get-VM | Get-Stat -Stat cpu.usage.average -Realtime |
  Sort-Object Value -Desc | Select -First 10
```

### govc 示例

```bash
export GOVC_URL="https://user:pass@vcenter.lab.local/sdk"
export GOVC_INSECURE=1

govc ls /                              # 列对象
govc vm.info web-01                    # VM 详情
govc vm.power -on web-01               # 开机
govc vm.clone -vm tpl-rhel9 web-02     # 克隆
```

## 八、esxtop 排查（必备）

```bash
# 在 ESXi shell 中
esxtop
   c → CPU
   m → Memory
   n → Network
   d → Disk Adapter
   v → Disk VM
   x → vSAN

关键指标:
  %RDY    > 10 → CPU 等待严重
  %CSTP   > 3  → vSMP 协调延迟
  CACHEUS > 高 → 内存压力
  KAVG/d  > 2ms → 存储延迟
  GAVG    = KAVG + DAVG（端到端）
```

## 九、典型架构规模

### 9.1 中小企业（10-50 VM）

```
2× ESXi 主机（每台 32C/256GB）
1× vCenter VCSA
共享存储（NAS/iSCSI）
1× vSphere Standard 许可
```

### 9.2 中型企业（100-500 VM）

```
4-8× ESXi 主机
vCenter HA
vSAN 集群（HCI）
NSX 微分段
vSphere Enterprise Plus + vSAN + NSX
```

### 9.3 大型企业 / 私有云

```
多集群、多数据中心
VMware Cloud Foundation 全套
SRM 容灾、Aria 监控运营
HCX 跨云迁移
```

## 十、Broadcom 收购后的影响（必读）

### 10.1 商业变化

| 项 | 变化 |
|:---|:---|
| 永久许可 | 全部停售 |
| 订阅制 | 强制按年/三年订阅 |
| 套件捆绑 | VCF / VVF 两种套件，单品基本不卖 |
| 最低核心 | 每 CPU 最低 16 核计费 |
| 渠道 | 大幅裁减经销商，集中头部客户 |
| 价格 | 上涨 2-10 倍是常态 |

### 10.2 客户的选择

```
1. 接受涨价继续用 VMware（大企业、金融）
2. 迁移到 Proxmox VE / Nutanix / Hyper-V
3. 迁移到 OpenStack / KubeVirt
4. 迁移到公有云（AWS / 阿里云）
5. 混合方案: 关键负载留 VMware, 其他下移
```

### 10.3 替代方案对比

| 维度 | vSphere | Proxmox VE | XCP-ng | OpenStack | KubeVirt |
|:---|:---|:---|:---|:---|:---|
| 类型 | 闭源商业 | 开源 KVM | 开源 Xen | 开源云平台 | K8s+KVM |
| 上手难度 | 低 | 低 | 低 | 高 | 高 |
| 商业支持 | 强 | 中 | 中 | 弱-中 | 弱 |
| 企业特性 | 极全 | 中 | 中 | 多 | 起步 |
| 适合规模 | 任何 | 中小 | 中小 | 中大 | K8s 化场景 |
| 国内信创 | ❌ | ⚠️ | ⚠️ | ✅ | ✅ |

## 十一、迁移到其他平台

### 11.1 常见迁移路径

| 来源 → 目标 | 工具 |
|:---|:---|
| vSphere → Proxmox VE | **PVE 8.2+ 内置导入向导**、qm importovf、`virt-v2v` |
| vSphere → KVM/oVirt | `virt-v2v` |
| vSphere → OpenStack | `cinder-glance-import` + virt-v2v |
| vSphere → Hyper-V | MVMC（已停更）、StarWind |
| vSphere → Nutanix | Nutanix Move |
| vSphere → 公有云 | 阿里云 SMC、AWS MGN |

### 11.2 迁移挑战

```
- vmdk 转 qcow2 / raw 的格式转换
- virtio 驱动注入（让 Windows VM 在 KVM 启动）
- VMware Tools 卸载 → qemu-guest-agent 安装
- 网络配置重做（vDS 不通用）
- 存储重新规划（vSAN 不通用）
- 备份 / DR 体系全部重做
```

## 十二、信创场景下的 vSphere 替代

国内信创要求下，主流替代方案：

| 厂商 | 产品 | 基础 |
|:---|:---|:---|
| **华为** | FusionCompute / FusionSphere | 自研 |
| **新华三** | UIS / CAS | KVM |
| **深信服** | aCloud / HCI | KVM |
| **ZStack** | ZStack Cloud | KVM |
| **EasyStack** | ECS | OpenStack |
| **浪潮** | InCloud Sphere | KVM |
| **腾讯** | TStack | OpenStack |

## 十三、关键经验与坑

| 坑 | 建议 |
|:---|:---|
| 永久许可消失 | 提前 6-12 个月做迁移评估 |
| ESXi 免费版被取消（2024.2） | 实验环境改用 Proxmox / XCP-ng |
| vCenter 单点故障 | 配 vCenter HA 或 File-Based Backup |
| vSAN 满了 | 70% 容量警戒线 |
| 跨代 CPU 集群 | 必须开 EVC |
| 网络风暴 | vDS Portgroup 隔离 + NSX 微分段 |
| 升级翻车 | 用 vLCM 镜像基线，先非生产灰度 |
| HA 不工作 | 检查 Isolation Response + Admission Control |

## 十四、学习路径

```
1. 基础: 装一套 ESXi + VCSA Home Lab（白嫖 EVAL 60 天）
2. 核心: vMotion / HA / DRS / vSAN 实操
3. 网络: vDS → NSX
4. 自动化: PowerCLI / govc / Terraform
5. 排查: esxtop + 性能图 + 日志收集
6. 进阶: SRM 容灾 / Tanzu / Aria Suite
7. 迁移: 学一套 KVM/Proxmox 兜底
```

## 十五、未来展望

```
短期 (1-2 年):
  - Broadcom 砍 SKU、提价继续
  - 大量客户启动迁移项目
  - VMware Cloud Foundation 成主力 SKU

中期 (2-5 年):
  - 头部金融/电信仍是 VMware 大客户
  - 中小企业逐步转 Proxmox VE / Nutanix / OpenStack
  - 国内信创快速吃下 VMware 市场份额

长期 (5 年+):
  - VMware 走向超大规模专用化
  - 开源虚拟化（KubeVirt + Proxmox + OpenStack）三足鼎立
  - 容器逐步蚕食传统 VM 工作负载
```

> 💡 即使你的目标是"逃离 VMware"，**理解 vSphere 也是必修课**——因为你要迁移的源头通常就是它，而行业基准的"对照标准"也是它。
