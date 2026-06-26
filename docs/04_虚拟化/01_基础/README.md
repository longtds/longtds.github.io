# 基础

> 虚拟化基础 = **概念分类(Type1/Type2) + CPU 虚拟化(VT-x/AMD-V) + 内存虚拟化(EPT/NPT) + IO 虚拟化(virtio) + 镜像格式(qcow2/raw/vmdk) + 主流平台 + KVM/QEMU 入门**。掌握本章后能装 KVM、跑 VM、做 P2V、读懂 qemu-kvm 启动参数。本章面向新手和入职 1 年内的工程师。

## 一、虚拟化分类

### 1.1 三种类型

```
Type 1 (裸机 / 原生)         Type 2 (宿主型)          OS-Level (容器)
─────────────────────       ─────────────────       ─────────────────
   VM    VM    VM              VM    VM             Container Container
    │     │     │               │     │                  │       │
  ──┴─────┴─────┴──           ──┴─────┴──             ──┴───────┴──
   Hypervisor                  Host OS                 Host OS
   ─────────────              ─────────────           ─────────────
       硬件                       硬件                     硬件

代表:                          代表:                    代表:
ESXi / KVM / Xen              VirtualBox             Docker / LXC
Hyper-V / Proxmox             VMware Workstation     containerd
华为 FusionCompute            QEMU (纯软件)           runC
```

### 1.2 关键术语

```
Hypervisor / VMM    虚拟机监控器，调度 VM
Host                宿主机
Guest               虚拟机
vCPU                虚拟 CPU
vMEM / vRAM         虚拟内存
vNIC / vDisk        虚拟网卡 / 虚拟磁盘
Live Migration      在线迁移（不停机）
P2V / V2V           物理→虚拟 / 虚拟→虚拟
Snapshot            快照
Template / Clone    模板 / 克隆
Overcommit          超分（vCPU/Mem 总和 > 物理）
NUMA Affinity       NUMA 亲和
```

### 1.3 全虚拟化 / 半虚拟化 / 硬件辅助

```
全虚拟化 (Full)
  Guest 内核不修改
  指令翻译 (Binary Translation) → 慢
  代表: 早期 VMware Workstation

半虚拟化 (Paravirt / PV)
  Guest 内核打 hyper-call → 直接调 Hypervisor
  快但要改内核
  代表: Xen PV / virtio (准虚拟设备)

硬件辅助 (HVM, Hardware-assisted)
  CPU 提供 Root/Non-root 两种模式
  Intel VT-x / AMD-V → 直接跑 Guest 指令
  现代主流 ⭐
```

## 二、CPU 虚拟化

### 2.1 Intel VT-x / AMD-V

```
Root Mode      Hypervisor 模式
Non-root Mode  Guest 模式
  VMX (Intel)
  SVM (AMD)

VMX Transitions:
  VM Entry   Root → Non-root（进入 Guest）
  VM Exit    Non-root → Root（陷入，如 IO/中断/敏感指令）

# 看 CPU 是否支持
egrep -c '(vmx|svm)' /proc/cpuinfo            # >0 表示支持
lscpu | grep Virtualization
```

### 2.2 BIOS 开虚拟化

```
启动 BIOS:
  Intel: Virtualization Technology (VT-x) = Enabled
         VT-d (IOMMU) = Enabled
  AMD:   SVM Mode = Enabled
         IOMMU = Enabled

未开会报错:
  KVM: disabled by bios
  或 /dev/kvm 不存在
```

### 2.3 vCPU 与超分

```
1 vCPU = Host 上 1 个线程时间片
不一定独占核心

超分原则:
  ☐ CPU 1:2-1:4 (中等负载)
  ☐ 1:1 (核心生产, DB)
  ☐ 关键业务用 cpu pinning 绑核

NUMA 亲和:
  - 大 VM 绑定单 NUMA → 性能好
  - 跨 NUMA 性能下降 20-40%
```

## 三、内存虚拟化

### 3.1 EPT / NPT（二级地址翻译）

```
Guest 虚拟地址 (GVA)
   ↓ Guest 页表
Guest 物理地址 (GPA)
   ↓ EPT/NPT (硬件)
Host 物理地址 (HPA)

Intel EPT  Extended Page Tables
AMD NPT    Nested Page Tables

收益:
  - 硬件加速二级翻译
  - 替代旧软件 shadow page table
  - 现代必备
```

### 3.2 KSM（同页合并）

```
Kernel Samepage Merging
  内核扫描相同内存页 → 合并 → COW
  
# Linux
cat /sys/kernel/mm/ksm/run                   # 1 开
cat /sys/kernel/mm/ksm/pages_sharing          # 节省页数

# 适用: 相同 OS 的多 VM 节省内存 20-30%
# 不适用: 内存敏感型，PCI passthrough VM
```

### 3.3 Balloon（气球驱动）

```
Guest 装 balloon driver (virtio_balloon)
Hypervisor 让 Guest "膨胀" 释放内存还宿主机
Host 内存紧张时动态平衡

# 看
virsh dommemstat <vm>
```

### 3.4 大页（HugePage）

```bash
# 配置 2 MB 大页
echo 4096 > /proc/sys/vm/nr_hugepages
mount -t hugetlbfs nodev /mnt/huge

# 看
cat /proc/meminfo | grep -i huge

# VM 使用
qemu-kvm -m 8G -mem-path /mnt/huge ...

# 收益:
#   - 减少 TLB miss
#   - DB / 大内存 VM 必开
```

## 四、IO 虚拟化

### 4.1 三种实现

```
完全模拟 (Emulation)
  QEMU 模拟出 e1000/RTL8139/IDE
  慢但兼容性强
  适合: 老 OS 安装阶段
  
准虚拟 virtio
  半虚拟驱动 (Guest 装 virtio-net/virtio-blk)
  快 ⭐ 现代主流
  
直通 (PCI Passthrough)
  整个 PCI 设备分配给 Guest（IOMMU 隔离）
  接近裸机性能
  适合: GPU / 网卡 / NVMe
```

### 4.2 virtio 设备

```
virtio-net    网卡
virtio-blk    块设备 (老)
virtio-scsi   SCSI 控制器 (推荐替代 blk)
virtio-balloon 气球
virtio-rng    随机数
virtio-9p     共享文件系统
virtio-gpu    GPU
vhost-user    用户态加速 (DPDK)
```

### 4.3 VFIO + IOMMU 直通

```bash
# 1. 开 IOMMU
# GRUB: intel_iommu=on  或  amd_iommu=on
update-grub && reboot

# 2. 看 IOMMU 组
find /sys/kernel/iommu_groups/ -type l | sort -V

# 3. 绑 vfio-pci
echo "vfio-pci" > /sys/bus/pci/devices/0000:01:00.0/driver_override
echo "0000:01:00.0" > /sys/bus/pci/drivers/vfio-pci/bind

# 4. KVM 启动加 -device vfio-pci,host=01:00.0
```

### 4.4 SR-IOV

```
Single-Root I/O Virtualization
  一块物理网卡虚拟出多个 VF (Virtual Function)
  每个 VF 可直通给 VM
  
ethtool 看 VF:
  lspci | grep -i ethernet
  echo 8 > /sys/class/net/eth0/device/sriov_numvfs

虚拟化场景:
  - 网卡 VF 给 VM
  - 高性能网络
  - NFV / 5G UPF
```

## 五、镜像格式

### 5.1 主流格式

| 格式 | 厂商 | 特点 |
|:---|:---|:---|
| **raw** | 通用 | 原始块，无开销，无快照 |
| **qcow2** ⭐ | QEMU | 支持快照/COW/压缩/加密，KVM 主流 |
| **vmdk** | VMware | vSphere/Workstation |
| **vhd / vhdx** | Microsoft | Hyper-V |
| **vdi** | Oracle | VirtualBox |
| **ova / ovf** | OASIS | 跨平台打包 |

### 5.2 qcow2 实战

```bash
# 创建
qemu-img create -f qcow2 disk.qcow2 50G

# 看信息
qemu-img info disk.qcow2

# 转换
qemu-img convert -f raw -O qcow2 src.raw dst.qcow2
qemu-img convert -f vmdk -O qcow2 src.vmdk dst.qcow2

# 调整大小
qemu-img resize disk.qcow2 +10G

# 快照
qemu-img snapshot -c snap1 disk.qcow2
qemu-img snapshot -l disk.qcow2
qemu-img snapshot -a snap1 disk.qcow2          # 回滚
qemu-img snapshot -d snap1 disk.qcow2

# 检查
qemu-img check disk.qcow2

# 压缩
qemu-img convert -O qcow2 -c src.qcow2 dst.qcow2
```

### 5.3 cloud-init 镜像（云时代）

```
官方镜像:
  Ubuntu Cloud Image (.img qcow2)
  RHEL/Rocky Cloud
  openEuler Cloud
  Anolis Cloud

特点:
  - 内置 cloud-init
  - 首次启动注入 SSH key / hostname / 网络
  - 适合云 / Terraform / 大批量
```

## 六、主流虚拟化平台

### 6.1 选型矩阵

| 平台 | 类型 | 商业/开源 | 适用 |
|:---|:---|:---|:---|
| **KVM + libvirt** | Type 1 | 开源 ⭐ | Linux 标配 |
| **QEMU** | Type 2/1 | 开源 | 仿真器 + KVM 底层 |
| **VMware vSphere/ESXi** | Type 1 | 商业 | 企业老牌 |
| **Hyper-V** | Type 1 | MS 自带 | Windows 系 |
| **Proxmox VE** | Type 1 | 开源 ⭐ | 中小企业首选 |
| **Xen** | Type 1 | 开源 | 历史悠久，AWS 旧版 |
| **VirtualBox** | Type 2 | 开源 | 桌面/学习 |
| **华为 FusionCompute** | Type 1 | 商业 | 国产信创 ⭐ |
| **深信服 aSV / 中科曙光 / 浪潮 InCloud** | Type 1 | 商业 | 国产替代 |

### 6.2 KVM 全栈

```
内核态:  kvm.ko + kvm_intel.ko / kvm_amd.ko
用户态:  qemu-kvm (硬件模拟 + 设备)
管理:    libvirt (libvirtd + virsh + virt-manager)
高阶:    OpenStack Nova / oVirt / Proxmox / kubevirt
```

## 七、KVM 实战入门

### 7.1 装包

```bash
# Ubuntu/Debian
apt install qemu-kvm libvirt-daemon-system virt-manager virtinst bridge-utils

# RHEL/Anolis/openEuler
dnf install qemu-kvm libvirt virt-manager virt-install bridge-utils

# 启服务
systemctl enable --now libvirtd

# 检查
virt-host-validate
kvm-ok                                          # Ubuntu
```

### 7.2 创建第一个 VM

```bash
# 下载 cloud-image (Ubuntu)
wget https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img

# 创建磁盘
qemu-img create -f qcow2 -F qcow2 \
  -b /var/lib/libvirt/images/jammy-server-cloudimg-amd64.img \
  /var/lib/libvirt/images/vm01.qcow2 50G

# 用 virt-install
virt-install \
  --name vm01 \
  --vcpus 4 \
  --memory 8192 \
  --disk path=/var/lib/libvirt/images/vm01.qcow2,format=qcow2 \
  --os-variant ubuntu22.04 \
  --network bridge=virbr0 \
  --graphics none \
  --cloud-init user-data=user-data.yaml
```

### 7.3 cloud-init user-data

```yaml
#cloud-config
hostname: vm01
users:
  - name: alice
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... alice@laptop
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    shell: /bin/bash

package_update: true
packages:
  - nginx
  - curl
```

### 7.4 virsh 基础命令

```bash
# 列表
virsh list                                       # 运行中
virsh list --all                                 # 全部

# 生命周期
virsh start vm01
virsh shutdown vm01                              # 优雅关
virsh destroy vm01                               # 强制断电
virsh reboot vm01
virsh suspend / resume vm01
virsh undefine vm01                              # 删定义
virsh undefine --remove-all-storage vm01         # 连磁盘删

# 信息
virsh dominfo vm01
virsh domstats vm01
virsh domifaddr vm01                              # 看 IP
virsh dumpxml vm01 > vm01.xml

# 控制台 (回 ^]退出)
virsh console vm01

# 编辑配置
virsh edit vm01

# 快照
virsh snapshot-create-as --domain vm01 snap1
virsh snapshot-list vm01
virsh snapshot-revert vm01 snap1
virsh snapshot-delete vm01 snap1

# 自启动
virsh autostart vm01
virsh autostart --disable vm01
```

### 7.5 网络模式

```
NAT (default)              虚拟机走宿主机 NAT 上网，外部不可访问
                           virbr0 + dnsmasq + iptables
                           
Bridge                     虚拟机直连物理网络，独立 IP ⭐
                           需要 br0（绑物理网卡）
                           
Routed                     宿主机做路由
                           
Isolated                   仅 VM 间互通

OVS                        Open vSwitch + VLAN/VXLAN，云常用
```

```bash
# 看默认网络
virsh net-list
virsh net-dumpxml default

# 创建桥接（Linux Bridge）
cat > /etc/netplan/50-bridge.yaml <<EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
  bridges:
    br0:
      interfaces: [eth0]
      addresses: [192.168.1.10/24]
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8]
EOF
netplan apply

# virsh 创建 bridge 网络
cat > br0.xml <<EOF
<network>
  <name>br0-net</name>
  <forward mode='bridge'/>
  <bridge name='br0'/>
</network>
EOF
virsh net-define br0.xml
virsh net-start br0-net
virsh net-autostart br0-net
```

### 7.6 qemu 命令行（理解底层）

```bash
qemu-system-x86_64 \
  -name vm01 \
  -machine q35,accel=kvm \
  -cpu host \
  -smp 4 \
  -m 8192 \
  -drive file=disk.qcow2,if=virtio,format=qcow2 \
  -netdev tap,id=net0,ifname=tap0,script=no \
  -device virtio-net-pci,netdev=net0,mac=52:54:00:11:22:33 \
  -vga virtio \
  -display vnc=:0 \
  -monitor stdio \
  -enable-kvm
```

## 八、生命周期 + 模板

### 8.1 P2V / V2V

```bash
# V2V (KVM ← VMware)
virt-v2v -i vmx /path/to/vmx -o libvirt -of qcow2 -on vm01

# 物理机 P2V
# 先 dd 磁盘:
dd if=/dev/sda of=/mnt/nfs/server.raw bs=4M status=progress
# 转 qcow2:
qemu-img convert -f raw -O qcow2 server.raw server.qcow2
# virt-v2v 整理:
virt-v2v -i disk server.qcow2 -o libvirt -of qcow2 -on server01
```

### 8.2 模板与克隆

```bash
# 清理 + 模板化
virt-sysprep -d vm01                             # 清 cloud-init/hostname/key
virsh snapshot-create-as --domain vm01 base

# 克隆
virt-clone --original vm01 --name vm02 --auto-clone
```

### 8.3 在线迁移（同后端存储）

```bash
# 主备 host 都装 libvirt + 共享存储
virsh migrate --live --persistent vm01 qemu+ssh://host2/system

# 关键: 
#   - 共享存储 (NFS / GlusterFS / Ceph / iSCSI)
#   - CPU 兼容（migrate 时机器系列一致或 cpu mode 用 host-model）
#   - 网络互通
```

## 九、入门必练 20 题

```
1.  Type 1 vs Type 2 区别？
2.  VT-x / VT-d 各管什么？
3.  CPU vmx/svm 没在 cpuinfo 里，从哪开？
4.  EPT 解决什么问题？
5.  virtio 三个最常用设备
6.  qcow2 比 raw 多了什么能力？
7.  qemu-img 转 vmdk → qcow2 命令
8.  cloud-init user-data 中 ssh_authorized_keys 字段
9.  virt-install 一行装 VM
10. virsh console 回不来怎么办？(Ctrl+])
11. NAT 网络 vs Bridge 网络的差异
12. virbr0 是什么？
13. KSM 适合什么场景？不适合什么？
14. HugePage 怎么挂？哪些 VM 受益？
15. SR-IOV 是什么？VF 怎么生成？
16. virsh dumpxml 看 vm01 的 CPU/内存配置
17. virt-clone 一行命令
18. P2V 通常分几步？
19. 在线迁移的前提条件
20. KVM 比 VMware 差在哪？强在哪？
```

## 十、典型坑（基础）

| 坑 | 建议 |
|:---|:---|
| **CPU 不支持 VT-x / 没开 BIOS** | grep vmx/svm /proc/cpuinfo + BIOS 检查 |
| **/dev/kvm 不存在** | modprobe kvm_intel / kvm_amd |
| **virt-host-validate FAIL** | 按提示装包 + 调内核 |
| **网络只能 NAT** | 切 bridge + br0 |
| **virsh console 黑屏** | grub 加 console=ttyS0 + serial-getty.service |
| **qcow2 大小膨胀** | qemu-img convert 重写 |
| **快照后无法迁移** | 先合并快照再走 |
| **virtio 驱动缺** | Windows 装 virtio-win.iso |
| **NUMA 没绑** | 大 VM 跨 NUMA 性能差 |
| **存储 IOPS 差** | virtio-scsi > virtio-blk |

## 十一、学习资源

```
书籍:
  - 《系统虚拟化：原理与实现》英特尔团队 ⭐
  - 《KVM 实战》任永杰 单海涛
  - 《Mastering KVM Virtualization》Packt

在线:
  - libvirt.org 官方文档
  - QEMU Wiki
  - linux-kvm.org
  - Red Hat Virtualization Documentation

视频:
  - Red Hat Summit / KVM Forum 演讲
  - 极客时间《深入剖析 Linux 虚拟化》

国内:
  - 红帽中国官方博客
  - 阿里云 / 华为云 / 腾讯云 虚拟化白皮书
  - openEuler 虚拟化 SIG
  - InfoQ 虚拟化专栏
```

> 📖 **核心判断**：虚拟化基础 = **Type1/2 分类 + VT-x/EPT + virtio + qcow2 + KVM/libvirt 全栈**。能装 KVM、用 virt-install 起 VM、配 bridge 网络、做模板克隆、用 virsh 管 10 台 VM，就是合格的基础。**生产场景永远 KVM + libvirt + bridge + virtio + qcow2**，别恋战 VirtualBox 和纯 QEMU。
