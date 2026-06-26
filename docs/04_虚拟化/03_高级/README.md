# 高级

> 虚拟化高级 = **GPU 虚拟化(vGPU/MIG/SR-IOV) + PCIe 直通 + NUMA/CPU 拓扑深度 + 嵌套虚拟化 + 实时虚拟化(KVM-RT) + 机密计算(SEV/TDX/CCA) + 超融合(HCI) + 虚拟机即容器(KubeVirt/Firecracker/Kata) + 国产化深度**。本章面向需要做底层虚拟化平台、AI 训练 GPU 隔离、机密计算的高级工程师。

## 一、GPU 虚拟化（AI 时代核心）

### 1.1 五种主流方案

| 方案 | 厂商 | 隔离 | 性能 | 适用 |
|:---|:---|:---|:---|:---|
| **PCI Passthrough** | 通用 | 强 | 100% 裸机 | 整卡给 1 VM |
| **NVIDIA vGPU** | NVIDIA | 时间片 | 共享，单 VM 部分性能 | 桌面虚拟化 VDI |
| **NVIDIA MIG** ⭐ | NVIDIA A100/H100 | **硬件隔离** | 最高 7 切片 | AI 推理 / 多租户 |
| **MPS** | NVIDIA | 进程级 | 时间共享 | 同 OS 多进程 |
| **SR-IOV (AMD/Intel)** | AMD MI / Intel ATS | 中等 | VF 切分 | 部分 GPU |
| **国产 vGPU** | 摩尔 / 沐曦 / 寒武纪 / 华为昇腾 | 时间片或硬件 | 各异 | 国产化 ⭐ |

### 1.2 PCI Passthrough（整卡直通）

```bash
# 1. 开 IOMMU
# GRUB: intel_iommu=on iommu=pt   或   amd_iommu=on iommu=pt

# 2. 找 GPU 设备
lspci -nn | grep -i nvidia
# 03:00.0 ... [10de:2330]   GPU
# 03:00.1 ... [10de:1aef]   Audio

# 3. 加载 vfio-pci 绑定（开机就绑，避免 nvidia 抢）
# /etc/modprobe.d/vfio.conf
options vfio-pci ids=10de:2330,10de:1aef

# 黑名单 nvidia
echo "blacklist nouveau" > /etc/modprobe.d/blacklist-nv.conf
echo "blacklist nvidia" >> /etc/modprobe.d/blacklist-nv.conf

update-initramfs -u
reboot

# 4. VM XML
<hostdev mode='subsystem' type='pci' managed='yes'>
  <source>
    <address domain='0' bus='0x03' slot='0x00' function='0x0'/>
  </source>
</hostdev>
<hostdev mode='subsystem' type='pci' managed='yes'>
  <source>
    <address domain='0' bus='0x03' slot='0x00' function='0x1'/>
  </source>
</hostdev>
```

### 1.3 NVIDIA MIG（A100/H100 必备）

```
MIG = Multi-Instance GPU
原理: 硬件级 GPU 切片（计算/显存/L2/Copy Engine 都隔离）

A100 80G 切片选项:
  1g.10gb  (×7)  最小
  2g.20gb  (×3)
  3g.40gb  (×2)
  4g.40gb  (×1)
  7g.80gb  (×1)  整卡

H100 80G 切片选项:
  1g.10gb  / 1g.20gb
  2g.20gb  / 2g.40gb
  3g.40gb
  4g.40gb
  7g.80gb

收益:
  - 多租户隔离（不同 VM/Pod 真正不互相干扰）
  - 推理服务密度提升 5-7x
  - VM/容器都能用
```

```bash
# 1. 启用 MIG
nvidia-smi -mig 1

# 2. 看可用切片
nvidia-smi mig -lgip                            # GPU Instance Profile
nvidia-smi mig -lcip -gi 0                      # Compute Instance Profile

# 3. 创建 3 个 2g.20gb 切片
nvidia-smi mig -cgi 9,9,9 -C

# 4. 看 UUID
nvidia-smi -L
# MIG 2g.20gb     Device  0:  UUID  MIG-xxx

# 5. K8s 用
# 用 NVIDIA GPU Operator + mig-manager
# 容器:  --gpus '"device=MIG-xxx"'

# 6. VM 用 (vfio-mig)
# VM XML 用 mdev 绑定
```

### 1.4 NVIDIA vGPU（VDI / 共享推理）

```
许可证: 商业 (NVIDIA vGPU Software License)
工作模式:
  - 时间片调度
  - 显存固定切分 (1Q/2Q/4Q/8Q...)
  
适合:
  - VDI 桌面云
  - 多用户共享推理
  - 不能 MIG 的卡 (V100/T4 等)

Host 装:
  - nvidia-vgpu-mgr.service
  - kvm + libvirt + mdevctl
  - 创建 mdev 类型实例
  
配置范例:
mdevctl define -u <uuid> -p 0000:03:00.0 -t nvidia-37    # vGPU 类型
mdevctl start -u <uuid>
mdevctl modify -u <uuid> --auto                          # 开机自动

VM XML:
<hostdev mode='subsystem' type='mdev' managed='no' model='vfio-pci'>
  <source><address uuid='<uuid>'/></source>
</hostdev>
```

### 1.5 国产 GPU 虚拟化

```
摩尔线程 MTT S4000          硬件切片 + 软件 vGPU
沐曦 MXC500/C500            cuda 兼容 + 切片
寒武纪 MLU370 / 590          MLU-Link 互联 + 切片
华为昇腾 910B / 910C         HCCL + 整卡为主，渐进切片
天数智芯 / 燧原              成熟度较弱

K8s 适配:
  - 各厂自家 device plugin
  - 国家智算中心多在适配
```

### 1.6 GPU Direct / RDMA

```
GPU Direct P2P:        同主机 GPU 间 PCIe 直接 DMA
GPU Direct RDMA:       GPU 显存 ⟷ 网卡（绕过主存）
GPU Direct Storage:    NVMe ⟷ GPU 显存

虚拟化注意:
  - PCI 直通时可用
  - 跨 vfio 设备同 IOMMU 组
  - NCCL_NET_GDR_LEVEL=2
```

## 二、PCIe 直通深度

### 2.1 IOMMU Group

```
IOMMU 把 PCIe 设备分组（同组共享地址空间）
同组设备必须一起直通

# 看 group
for d in /sys/kernel/iommu_groups/*/devices/*; do
  n=${d#*/iommu_groups/*}; n=${n%%/*}
  printf 'IOMMU Group %s: %s\n' "$n" "${d##*/}"
done | sort -k 3 -V

# 拆分 group (有风险)
# kernel: pci=resource_alignment=...   或  ACS override patch
```

### 2.2 NVMe / 网卡 / FPGA 直通

```bash
# NVMe 直通
lspci | grep -i nvme
echo "vfio-pci" > /sys/bus/pci/devices/0000:01:00.0/driver_override

# 适合:
#   - DB VM 极致 IOPS
#   - AI 训练 NVMe-oF
#   - FPGA 加速卡
```

### 2.3 USB 直通

```xml
<!-- USB host controller passthrough (整 controller) -->
<hostdev mode='subsystem' type='pci' managed='yes'>
  <source><address domain='0' bus='0' slot='0x14' function='0'/></source>
</hostdev>

<!-- 或单个 USB 设备 -->
<hostdev mode='subsystem' type='usb' managed='yes'>
  <source><vendor id='0x046d'/><product id='0xc31c'/></source>
</hostdev>
```

## 三、NUMA / CPU 拓扑深度

### 3.1 拓扑感知 XML

```xml
<cpu mode='host-passthrough'>
  <topology sockets='2' dies='1' cores='8' threads='2'/>
  <numa>
    <cell id='0' cpus='0-7,16-23' memory='32' unit='GiB'>
      <distances>
        <sibling id='0' value='10'/>
        <sibling id='1' value='21'/>
      </distances>
    </cell>
    <cell id='1' cpus='8-15,24-31' memory='32' unit='GiB'>
      <distances>
        <sibling id='0' value='21'/>
        <sibling id='1' value='10'/>
      </distances>
    </cell>
  </numa>
</cpu>

<cputune>
  <vcpupin vcpu='0' cpuset='0'/>
  <vcpupin vcpu='1' cpuset='16'/>
  ...
</cputune>

<numatune>
  <memory mode='strict' nodeset='0,1'/>
  <memnode cellid='0' mode='strict' nodeset='0'/>
  <memnode cellid='1' mode='strict' nodeset='1'/>
</numatune>
```

### 3.2 CPU 隔离（低延迟 VM 必备）

```bash
# Host kernel cmdline
isolcpus=4-15 nohz_full=4-15 rcu_nocbs=4-15

# 然后 VM 绑这些核
# 中断不进
echo 0,1,2,3 > /proc/irq/default_smp_affinity
```

## 四、嵌套虚拟化

### 4.1 KVM nested

```bash
# Intel
modprobe -r kvm_intel
echo "options kvm_intel nested=1" > /etc/modprobe.d/kvm.conf
modprobe kvm_intel
cat /sys/module/kvm_intel/parameters/nested      # Y

# AMD
echo "options kvm_amd nested=1" > /etc/modprobe.d/kvm.conf

# VM XML
<cpu mode='host-passthrough'/>

# 在 VM 内
egrep -c '(vmx|svm)' /proc/cpuinfo               # >0
```

```
适用:
  - 开发测试 (PVE/openstack 在 VM 里)
  - CI/CD 隔离
  - DevBox

注意:
  - 性能降 20-40%
  - 不推荐生产
```

## 五、实时虚拟化（RT）

### 5.1 场景

```
工业控制 / 5G UPF / 自动驾驶 / 高频交易
要求: 微秒级延迟、确定性、零丢包
```

### 5.2 KVM-RT

```bash
# Host 内核: PREEMPT_RT patch
uname -a | grep -i rt

# CPU 隔离
isolcpus=4-15 nohz_full=4-15 rcu_nocbs=4-15

# VM cputune
<cputune>
  <vcpupin vcpu='0' cpuset='4'/>
  <vcpupin vcpu='1' cpuset='5'/>
  ...
  <emulatorpin cpuset='0-3'/>
  <vcpusched vcpus='0-3' scheduler='fifo' priority='1'/>
</cputune>

# 关 KSM, balloon, transparent_hugepage, irqbalance
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo 0 > /sys/kernel/mm/ksm/run
systemctl stop irqbalance

# 锁定内存
<memoryBacking><locked/><nosharepages/></memoryBacking>

# 测延迟
cyclictest -p 95 -t 1 -i 200 -l 100000 -m
```

### 5.3 DPDK + KVM

```
场景: NFV / 5G UPF / vRouter

构件:
  Host:  Open vSwitch + DPDK (OVS-DPDK)
  VM:    DPDK 用户态 (vhost-user)

XML:
<interface type='vhostuser'>
  <source type='unix' path='/var/run/openvswitch/vhost-user-1' mode='client'/>
  <model type='virtio'/>
  <driver queues='4'/>
</interface>
```

## 六、机密计算（Confidential VM）

### 6.1 三大方案

| 方案 | 厂商 | 隔离粒度 | 现状 |
|:---|:---|:---|:---|
| **AMD SEV-SNP** | AMD EPYC | 整 VM | 主流，公有云大量使用 |
| **Intel TDX** | Intel SPR+ | 整 VM | 推广中 |
| **ARM CCA** | ARM v9 | Realm VM | 早期 |
| **国产 海光 CSV** | 海光 EPYC fork | 整 VM | 国产化基础 |

### 6.2 SEV-SNP（AMD）

```
SEV       Secure Encrypted Virtualization (Memory encryption)
SEV-ES    + 寄存器加密
SEV-SNP   + Secure Nested Paging (反映射攻击防护) ⭐

部署:
  AMD EPYC 7003/9004+
  内核: 5.19+ (推荐 6.x)
  qemu: 8.x+
  ovmf-sev

VM XML:
<launchSecurity type='sev'>
  <cbitpos>51</cbitpos>
  <reducedPhysBits>1</reducedPhysBits>
  <policy>0x07</policy>          <!-- SNP enable -->
</launchSecurity>
```

### 6.3 用途

```
- 公有云隔离 (云厂运维看不到内存)
- 跨境数据合规
- 机密 AI 训练 (模型/数据加密)
- 金融 / 医疗 / 法务
```

## 七、超融合（HCI）

### 7.1 概念

```
HCI = Hyper-Converged Infrastructure
特点: 计算 + 存储 + 网络 + 虚拟化 在一台标准 X86

开源方案:
  Proxmox VE + Ceph ⭐
  oVirt + Gluster
  OpenStack + Ceph
  Harvester (SUSE / Rancher) ⭐ K8s-native HCI

商业:
  VMware vSAN
  Nutanix
  Microsoft S2D
  
国产:
  深信服 aCloud
  华为 FusionCube
  浪潮 InCloud
  SmartX 超融合
  联想凌拓
```

### 7.2 设计要点

```
节点: 3 起步，推荐 4-8
存储: 副本 3 / EC (大集群)
网络: 25G/100G 双网 (业务 + 存储分离)
SSD: NVMe + 缓存盘 (Bluestore)
```

## 八、轻量虚拟化（容器 + VM 边界）

### 8.1 Firecracker (AWS)

```
特点:
  - microVM (启动 < 125ms)
  - 单进程 (无 QEMU 庞大代码)
  - 极简设备模型
  - Rust 编写
  
应用:
  AWS Lambda / Fargate
  Fly.io
  
开源: github.com/firecracker-microvm
```

```bash
# 一行启动
firectl --kernel vmlinux --root-drive rootfs.ext4

# 集成
firecracker-containerd / Kata Containers
```

### 8.2 Kata Containers

```
特点:
  - 容器 API + 强 VM 隔离
  - 每 Pod 一个 microVM
  - 适合多租户 SaaS
  
runtime:
  containerd + kata-runtime
  K8s RuntimeClass: kata
  
对比 runc:
  启动慢一点（~1s）
  内存隔离强
  内核隔离强（每 Pod 独立内核）
```

### 8.3 KubeVirt（在 K8s 跑 VM）

```
特点:
  - VM 即 K8s CRD (VirtualMachine)
  - 与容器同一调度器
  - 共享 K8s CNI/CSI
  - 在线迁移 LiveMigration CR
  
应用:
  - 老系统迁 K8s 不重写
  - 混部 VM/容器
  - 多租户隔离

主推方:
  Red Hat OpenShift Virt
  华为云 / 阿里云 / 腾讯云 边缘 VM 服务
```

### 8.4 Cloud Hypervisor (Intel/Microsoft)

```
特点:
  - Rust + 现代设计
  - 比 QEMU 轻量但比 Firecracker 功能多
  - 直通 / live migration / NUMA 等都支持
  
应用:
  - Cluster API Provider
  - 与 Kata 集成
```

## 九、自动化与 IaC

### 9.1 Terraform Provider

```hcl
# libvirt
terraform {
  required_providers {
    libvirt = { source = "dmacvicar/libvirt", version = "~> 0.7" }
  }
}

resource "libvirt_volume" "vm01" {
  name   = "vm01.qcow2"
  pool   = "default"
  source = "/iso/ubuntu-22.04.img"
  format = "qcow2"
}

resource "libvirt_cloudinit_disk" "ci" {
  name      = "ci-vm01.iso"
  user_data = file("user-data.yaml")
  pool      = "default"
}

resource "libvirt_domain" "vm01" {
  name   = "vm01"
  vcpu   = 4
  memory = 8192
  cloudinit = libvirt_cloudinit_disk.ci.id
  disk { volume_id = libvirt_volume.vm01.id }
  network_interface { network_name = "default" }
}
```

### 9.2 Packer（造镜像）

```hcl
# golden.pkr.hcl
source "qemu" "ubuntu" {
  iso_url      = "https://.../ubuntu-22.04-live-server-amd64.iso"
  iso_checksum = "sha256:..."
  ssh_username = "ubuntu"
  ssh_password = "ubuntu"
  disk_size    = "20G"
  format       = "qcow2"
  accelerator  = "kvm"
  cpus         = 2
  memory       = 4096
}
build {
  sources = ["source.qemu.ubuntu"]
  provisioner "ansible" { playbook_file = "./baseline.yml" }
}
```

### 9.3 Ansible KVM 模块

```yaml
- hosts: kvmhosts
  tasks:
    - name: 定义 VM
      community.libvirt.virt:
        name: vm01
        command: define
        xml: "{{ lookup('template', 'vm01.xml.j2') }}"
    
    - name: 启动 VM
      community.libvirt.virt:
        name: vm01
        state: running
```

## 十、国产化虚拟化全景

### 10.1 私有云 / 虚拟化整机

```
华为 FusionCompute / FusionSphere
深信服 aCloud / HCI ⭐
浪潮 InCloud Sphere
中科曙光 SugonCloud
H3C UIS / CAS
中标麒麟 NeoKylin Virt
青云 QingCloud Private
EasyStack
ZStack ⭐ 国产开源
SmartX 超融合
```

### 10.2 国产 Hypervisor 内核

```
龙蜥 / openEuler KVM Stack
华为 OpenStack + 自研 KVM 调优
ZStack (基于 KVM 重写管理面)
青云 QingCloud Hypervisor (KVM fork)
统信 UOS Virt
```

### 10.3 国产 GPU 虚拟化

```
摩尔线程 MTT S4000     vGPU + cuda 兼容 (zluda)
沐曦 MXC500           cuda 兼容 + 切片
寒武纪 MLU370         自有 sm-vGPU + Volcano 调度
华为昇腾 910B/910C    HCCL + 切片演进
天数智芯 BI / 燧原    早期 vGPU
```

### 10.4 国产备份

```
Vinchin (云祺) ⭐
爱数 AnyBackup
鼎甲科技 DBackup
英方 i2 (容灾)
飞康 (Falconstor)
中科同向 / 多备份
```

## 十一、典型生产架构（参考）

### 11.1 中小企业 (50 主机 / 500 VM)

```
3 节点 Proxmox VE 集群 + Ceph (内置)
    │
    ├─ Web UI / 备份: PBS 独立节点
    ├─ 监控:   Prometheus + Grafana + 夜莺
    ├─ 备份:   PBS + 异地 S3
    ├─ 网络:   OVS + VLAN + 25G LACP
    └─ 国产化方向: ZStack / SmartX
```

### 11.2 大型企业 (1000+ 主机)

```
OpenStack Yoga/Bobcat (见 05_私有云)
  Nova: KVM + libvirt
  Cinder: Ceph + 国产 SAN
  Neutron: OVN + DPDK
  Ironic: 裸金属
  Magnum: K8s 集成
  Designate / Heat / Octavia

虚拟化层调优:
  - 大 VM CPU pinning + NUMA + HugePage
  - SR-IOV / OVS-DPDK 高吞吐
  - 数据库专用 RT 内核
```

### 11.3 AI 训练集群

```
8 卡 H100 / 910B / MXC500 节点
  - GPU 整卡直通 (PCI Passthrough)
  - 或 MIG 切片 (推理)
  - RoCE/IB 网卡直通 (SR-IOV)
  - NVMe 直通 (训练数据)
  - 1 GB HugePage + NUMA strict
  
管理:
  - KubeVirt + GPU Operator
  - 或 OpenStack + nova-gpu-vfio
```

### 11.4 多租户 SaaS

```
Kata Containers / KubeVirt
  - 每 Pod microVM 隔离
  - K8s 调度 + 网络
  - mTLS + 机密计算可选
  - SEV-SNP / TDX 加密
```

## 十二、典型坑（高级）

| 坑 | 建议 |
|:---|:---|
| **IOMMU group 多设备** | ACS override / 选合适主板 |
| **MIG 没启用就跑容器** | nvidia-smi mig 先建实例 |
| **vGPU 许可证缺** | DLS 服务器接入 |
| **SR-IOV 不能 live migrate** | 设计阶段分流量 |
| **嵌套虚拟化生产用** | 仅 dev / CI 用 |
| **RT VM 没隔核** | cyclictest 跳水 |
| **DPDK VM cache 写穿** | hugepage + cache=none |
| **SEV-SNP 启动慢** | 内存度量 + ovmf-sev 必须匹配 |
| **HCI 节点 < 3** | 副本至少 3 节点 |
| **Firecracker 没 vsock** | 默认无设备过简 |
| **KubeVirt PV 慢** | 配置 RWX + Ceph RBD direct |
| **国产 GPU device plugin 不匹配** | 锁版本，提前测 |

## 十三、高级 Checklist

```
GPU:
☐ PCI Passthrough 直通过整卡
☐ MIG 切片 (A100/H100)
☐ vGPU 部署 (VDI)
☐ NCCL + RoCE 测试通过
☐ 国产 GPU device plugin 一项

PCIe 直通:
☐ NVMe / 网卡 / FPGA 直通
☐ IOMMU group 读懂
☐ SR-IOV VF 8+

NUMA / RT:
☐ <numa> XML 配过
☐ vcpupin + emulatorpin 标配
☐ cyclictest 验证
☐ DPDK vhost-user 跑通

嵌套:
☐ nested KVM 在 PVE/openstack VM 里跑

机密计算:
☐ SEV-SNP / TDX 尝鲜过
☐ launchSecurity XML 配过

HCI / K8s:
☐ Proxmox + Ceph HCI
☐ KubeVirt 装 VM CRD
☐ Kata / Firecracker microVM
☐ Harvester / OpenShift Virt

国产化:
☐ ZStack / FusionCompute 一台
☐ 国产 GPU 切片
☐ 国密 / 机密 VM
```

## 十四、推荐栈

```
单机:     KVM + libvirt + virt-manager
小集群:   Proxmox VE + Ceph + PBS ⭐
大集群:   OpenStack / oVirt / KubeVirt
HCI:     Proxmox / Harvester / SmartX / 深信服
GPU:     NVIDIA MIG / vGPU + GPU Operator
RT/NFV:  KVM-RT + DPDK + OVS-DPDK / VPP
microVM: Firecracker / Kata / Cloud Hypervisor
机密:    SEV-SNP / TDX / 海光 CSV
IaC:     Terraform libvirt provider + Packer + Ansible
监控:    libvirt_exporter + Prom + Grafana
备份:    PBS / Vinchin / 爱数
国产:    ZStack / SmartX / 华为 / 深信服
```

## 十五、学习路径

```
高级（6-12 月）:
  1. PCI Passthrough GPU 整卡
  2. MIG / vGPU 至少一种
  3. NUMA + HugePage + CPU pinning 上生产
  4. KVM-RT / DPDK NFV 实验
  5. Proxmox + Ceph HCI 3 节点
  6. KubeVirt + 数据卷 + 在线迁移
  7. Firecracker / Kata 上手
  8. SEV-SNP 或 TDX 一次
  9. Terraform + Packer + Ansible 整合
  10. 国产平台一台 (ZStack / FusionCompute)

专家:
  11. 万节点虚拟化平台架构 (OpenStack)
  12. AI 集群 GPU 调度 (MIG + K8s)
  13. 给 KubeVirt / Firecracker 提 PR
  14. 国产化大规模适配
  15. 机密计算大规模落地
```

## 十六、参考资料

```
经典:
  - 《系统虚拟化：原理与实现》英特尔团队
  - QEMU/KVM Internals
  - libvirt 文档全集
  - DPDK programmer's guide

云原生:
  - KubeVirt docs ⭐
  - Kata Containers docs
  - Firecracker docs
  - Harvester docs

GPU:
  - NVIDIA MIG User Guide ⭐
  - NVIDIA GPU Operator docs
  - DGX 集群最佳实践

机密计算:
  - AMD SEV-SNP 白皮书
  - Intel TDX docs
  - CCC (Confidential Computing Consortium)

国产:
  - 龙蜥 / openEuler 虚拟化 SIG
  - ZStack 文档
  - 华为 FusionCompute / 深信服 aCloud 白皮书
  - 摩尔/沐曦/寒武纪 SDK 文档
```

> 📖 **核心判断**：高级 = **GPU 虚拟化(MIG/vGPU/SR-IOV) + PCI 直通 + NUMA/RT + 机密计算 + microVM(KubeVirt/Kata/Firecracker) + 国产化**。能搭出"H100 MIG 切片 + KubeVirt + Ceph"AI 多租户平台、能写出 RT VM 的完整 XML、能上线一台 SEV-SNP VM、能在国产 GPU 上切片，就具备做底层虚拟化平台的能力。**虚拟化的未来 = GPU 切片 + microVM + 机密计算 + 国产化**，这四条线钉死。
