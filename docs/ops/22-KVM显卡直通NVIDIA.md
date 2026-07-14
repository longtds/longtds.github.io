# KVM 直通 NVIDIA 显卡

> 把物理显卡直通给虚拟机打游戏/AI 训练/视频渲染？本文覆盖 KVM VFIO 显卡直通全流程：硬件要求、IOMMU 配置、GPU 隔离、libvirt 配置、性能优化、常见故障处理。

---

## 一、GPU 直通概述

### 1.1 什么是 GPU 直通

```
GPU 直通 (GPU Passthrough):

  将物理 GPU 直接分配给虚拟机独占使用。
  通过 VFIO (Virtual Function I/O) 技术,
  将物理 PCI 设备穿透给 Guest OS,
  虚拟机直接控制硬件, 无需 Hypervisor 模拟。

  架构:

  ┌──────────────────────────────────────────────────────────────┐
  │                        Host (Linux)                          │
  │                                                              │
  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
  │  │ Host Apps   │  │ VM (Win/Linux)│  │ VM (AI Training)   │  │
  │  │ (日常使用)    │  │ GPU: 直通     │  │ GPU: 直通          │  │
  │  │ 无 GPU 或   │  │ Nvidia A4000 │  │ Nvidia A100        │  │
  │  │ iGPU 集成    │  │             │  │                    │  │
  │  └──────┬──────┘  └──────┬──────┘  └─────────┬───────────┘  │
  │         │               │                    │              │
  │         │               │   VFIO             │  VFIO        │
  │         │               │   ┌──────┐         │  ┌──────┐    │
  │         │               │   │NVIDIA│         │  │NVIDIA│    │
  │         │               │   │A4000 │         │  │ A100 │    │
  │         │               │   └──────┘         │  └──────┘    │
  │         │               │                    │              │
  │  ┌──────▼──────┐       ▼                    ▼              │
  │  │ Intel iGPU  │    PCIe Slot 1           PCIe Slot 2      │
  │  │ (SR-IOV?)   │                                           │
  │  └─────────────┘                                           │
  │                                                              │
  │  /dev/iommu — IOMMU 硬件虚拟化                               │
  │  vfio-pci 驱动接管 GPU, 屏蔽 Nvidia/nouveau 驱动              │
  └──────────────────────────────────────────────────────────────┘
```

### 1.2 GPU 直通的三种方案

| 方案 | 描述 | 适用场景 | 性能损耗 |
|:---|:---|:---|:---|
| **VFIO Passthrough** | 整张 GPU 直通给一个 VM | 游戏/渲染/AI 训练 | ~1-3% |
| **NVIDIA vGPU** | 一张 GPU 切分成多个 vGPU | 多用户共享 GPU (GRID) | ~5-10% |
| **SR-IOV** | 硬件支持的虚拟化功能分割 | 数据中心 GPU 虚拟化 | ~3-5% |
| **GPU API Remoting** | API 转发 (CUDA over TCP) | 远程 GPU 计算 | 网络延迟 |

### 1.3 硬件要求

```
必备条件:

  CPU:
    Intel: VT-d 支持 (多数 Core i5/i7/i9, Xeon)
    AMD:   AMD-Vi / IOMMU 支持 (Ryzen, EPYC)

 主板 / 芯片组:
    Intel Z 系列 / X 系列 (Z690/790, W680, X299)
    AMD B 系列 / X 系列 (B650, X670), TRX40
    企业板: 基本都支持

  BIOS 设置:
    ✅ IOMMU / VT-d 开启
    ✅ Above 4G Decoding 开启
    ✅ Resizable BAR / Re-Size BAR Support 开启
    ✅ SR-IOV Support (如需)
    ❌ Secure Boot (建议关闭, 或配置 MOK)

  GPU:
    所有 NVIDIA/AMD 显卡都支持直通
    常见问题:
      - NVIDIA GTX/RTX 直通 Windows 可能 Error 43
        → 需隐藏 KVM 虚拟机标识 (见故障排查)
      - 部分旧显卡没有 UEFI GOP BIOS
        → 需刷 UEFI GOP ROM 或使用 CSM 模式

 显示器:
    HDMI 欺骗器 (Headless 虚拟机)
    或 双显卡: 主机用 iGPU / 另一张卡, 直通卡输出到显示器

  内存:
    ≥ 16 GB (建议 32 GB+)
    CPU 需支持: 大页内存 (HugePages) 提升性能
```

### 1.4 拆解要点

```
常见拆解场景:

  1. 双显卡 (推荐):
     主机: 集成显卡 (Intel iGPU) 或 一块亮机卡
     直通: 主力 NVIDIA 卡给 VM
     显示: 主机显示器插 iGPU, VM 显示器插 NVIDIA 卡

  2. 单张显卡 (复杂):
     主机启动用显卡, VM 启动时卸载驱动重新绑定
     需要 SSH/串口远程管理主机
     → 不推荐, 上手难度高

  3. 多 GPU 虚拟化:
     多张 GPU 分别直通给不同 VM
     或 单张 GPU 用 vGPU 切分

  前提: 确认 IOMMU 分组
    同组设备必须一起直通 (GPU + HDMI Audio 一般同组)
    IOMMU 分组决定直通粒度
```

---

## 二、IOMMU 与 VFIO 原理

### 2.1 IOMMU (I/O Memory Management Unit)

```
IOMMU — 和外设打交道的 MMU

  作用:
    将 PCIe 设备的 DMA 请求翻译到物理内存
    限制设备只能访问指定的内存区域 (设备隔离)
    为虚拟机提供直接设备访问 (无需软件模拟)

  vs MMU:
    MMU: CPU 的虚拟地址 → 物理地址
    IOMMU: 设备的 DMA 地址 → 物理地址

  Intel: VT-d (Virtualization Technology for Directed I/O)
  AMD:   AMD-Vi / IOMMU

  IOMMU 分组 (Group):
    PCIe 设备按拓扑结构分成组
    同组设备共享同一个 IOMMU 转换表
    组内设备必须一起直通 (不能单独)
    分组越细越好 (ACS 功能)

  查看 IOMMU 分组命令:
    find /sys/kernel/iommu_groups/ -type l
    # 或
    for g in $(find /sys/kernel/iommu_groups -type d -name '[0-9]*'); do
      echo "IOMMU Group $(basename $g):"
      for d in $g/devices/*; do
        lspci -nns $(basename $d)
      done
    done

  IOMMU 分组示例:
    IOMMU Group 20:
      03:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3070]
      03:00.1 Audio device [0403]: NVIDIA Corporation GA104 High Definition Audio Controller
      ↑ GPU 和 HDMI Audio 在同一组, 必须一起直通

    IOMMU Group 4:
      01:00.0 Non-Volatile memory controller [0108]: Samsung NVMe SSD
      ↑ NVMe SSD 可单独直通
```

### 2.2 VFIO (Virtual Function I/O)

```
VFIO — 用户态直接访问硬件的框架

  用户态驱动框架:
    传统驱动: 设备 → 内核驱动 → 系统调用 → 用户态
    VFIO:    设备 → VFIO 驱动 → MMAP → 用户态 (虚拟机)

  VFIO 工作流程:
    1. 卸载设备的原生驱动 (nvidia/nouveau)
    2. 设备绑定到 vfio-pci 驱动
    3. vfio-pci 创建 /dev/vfio/N 设备节点
    4. QEMU 通过 /dev/vfio/N 直接访问硬件
    5. 设备中断通过 vfio-pci 转发给 QEMU
    6. DMA 通过 IOMMU 直接映射到 VM 内存

  关键内核模块:
    vfio:           核心框架
    vfio_iommu_type1: IOMMU 后端
    vfio_pci:       PCIe 设备绑定驱动
    vfio_virqfd:    中断事件通知

  绑定方式:
    方法 1: 内核参数 (推荐)
      options vfio-pci ids=10de:2482,10de:228b
      ↓
      10de:2482 = GPU Device ID
      10de:228b = HDMI Audio Device ID

    方法 2: driverctl
      driverctl set-override 0000:03:00.0 vfio-pci
      driverctl set-override 0000:03:00.1 vfio-pci

    方法 3: sysfs 手动
      echo 0000:03:00.0 > /sys/bus/pci/devices/0000:03:00.0/driver/unbind
      echo vfio-pci > /sys/bus/pci/devices/0000:03:00.0/driver_override
      echo 0000:03:00.0 > /sys/bus/pci/drivers/vfio-pci/bind
```

### 2.3 PCIe ACS (Access Control Services)

```
ACS — PCIe 点对点隔离

  问题:
    没有 ACS 的 PCIe 交换芯片,
    不同设备可以不经 Root Complex 直接 DMA 通信
    → 导致 IOMMU 分组粗放 (大组)

  检查 ACS 支持:
    lspci -vvv -s 00:1c.0 | grep -i acs
    # 输出包含 ACSCap 表示支持

  对策:
    1. 使用带 ACS 的 PCIe Switch
    2. ACS 覆盖补丁 (内核参数)
       pcie_acs_override=downstream
       pcie_acs_override=multifunction
       pcie_acs_override=id:8086:277c,1002:4384
    3. 自定义 ACS 内核补丁

  注意:
    ACS 覆盖补丁是软件模拟, 不完全等价硬件 ACS
    测试环境可用, 生产环境慎重
```

---

## 三、环境准备

### 3.1 BIOS 设置

```
BIOS 检查项 (重启前确认):

  1. Intel VT-d / AMD IOMMU:
     Intel 主板: Advanced → VT-d (Intel Virtualization Technology for Directed I/O)
     AMD 主板:  Advanced → IOMMU

  2. Above 4G Decoding:
     BIOS → PCI Subsystem Settings / Above 4G MMIO BIOS Assignment → Enabled
     (必须, 否则 64-bit PCIe BAR 无法分配)

  3. Re-Size BAR Support (可选, 提升性能):
     BIOS → PCI Subsystem Settings → Re-Size BAR Support → Auto

  4. Secure Boot:
     BIOS → Secure Boot → Disabled
     (如果开启了, 需签名 vfio-pci 驱动模块)

  5. CSM / Legacy Boot:
     如果 GPU 是 UEFI GOP 卡, 可以关闭 CSM (推荐)
     如果 GPU 不支持 UEFI, 开启 CSM 启用 Legacy Option ROM

  6. SR-IOV Support (如需 vGPU):
     BIOS → SR-IOV Support → Enabled
```

### 3.2 内核参数

```bash
# === 确认当前 IOMMU 是否启用 ===
dmesg | grep -i iommu
# 应该有: DMAR: IOMMU enabled

# Intel 平台
dmesg | grep -e DMAR -e IOMMU
# DMAR: IOMMU enabled
# DMAR-IR: Enabled IRQ remapping in x2apic mode

# AMD 平台
dmesg | grep AMD-Vi
# AMD-Vi: IOMMU enabled

# === 查看 IOMMU 分组 (重要!) ===
#!/bin/bash
# list-iommu-groups.sh
for iommu_group in $(find /sys/kernel/iommu_groups -maxdepth 1 -mindepth 1 -type d | sort -V); do
    echo "IOMMU Group $(basename $iommu_group):"
    for device in $iommu_group/devices/*; do
        echo "  $(lspci -nns $(basename $device))"
    done
done

# 输出示例:
# IOMMU Group 20:
#   03:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA104 [GeForce RTX 3070] [10de:2482] (rev a1)
#   03:00.1 Audio device [0403]: NVIDIA Corporation GA104 High Definition Audio Controller [10de:228b] (rev a1)
# ↵ GPU (10de:2482) 和 HDMI Audio (10de:228b) 在同一组, 必须一起直通

# === 确认是否开启 Above 4G Decoding ===
dmesg | grep -i 'above 4g'
# pci 0000:00:00.0:    bridge window [mem 0x00100000-0x0fffffff]  ← 不满足
# pci 0000:00:00.0:    bridge window [mem 0x800000000-0xffffffffff] ← Above 4G OK
# 或查看:
lspci -vvv | grep -i 'Above 64'

# === 查看显卡当前驱动 ===
lspci -k -s 03:00.0
# Kernel driver in use: nvidia     ← 现在被 nvidia 驱动占用
# 我们要改成: vfio-pci

lspci -k -s 03:00.1
# Kernel driver in use: snd_hda_intel
# 也要改成: vfio-pci

# 确认显卡的 PCI Vendor:Device ID
lspci -n -s 03:00.0
# 03:00.0 0300: 10de:2482 (rev a1)   # 10de=NVIDIA, 2482=RTX 3070
lspci -n -s 03:00.1
# 03:00.1 0403: 10de:228b (rev a1)   # HDMI Audio
```

### 3.3 配置内核参数

```bash
# === 编辑 GRUB 配置 ===

# 1. 编辑 /etc/default/grub
sudo vim /etc/default/grub

# Intel 平台 VT-d + vfio-pci 绑定
GRUB_CMDLINE_LINUX_DEFAULT="quiet \
    intel_iommu=on \
    iommu=pt \
    pcie_acs_override=downstream \
    vfio-pci.ids=10de:2482,10de:228b \
    kvm.ignore_msrs=1 \
    video=vesafb:off \
    video=efifb:off \
    rdblacklist=nouveau \
    modprobe.blacklist=nouveau"

# AMD 平台
GRUB_CMDLINE_LINUX_DEFAULT="quiet \
    amd_iommu=on \
    iommu=pt \
    pcie_acs_override=downstream \
    vfio-pci.ids=10de:2482,10de:228b \
    kvm.ignore_msrs=1 \
    video=vesafb:off \
    video=efifb:off \
    rdblacklist=nouveau \
    modprobe.blacklist=nouveau"

# 参数说明:
#   intel_iommu=on / amd_iommu=on: 启用 IOMMU
#   iommu=pt:       只解直通设备, 其他走原生驱动 (性能更好)
#   pcie_acs_override=downstream: ACS 覆盖 (如分组太粗)
#   vfio-pci.ids:   指定设备绑定到 vfio-pci (取代 nvidia/nouveau 驱动)
#   kvm.ignore_msrs=1: 忽略未处理的 MSR (Windows VM 必备)
#   video=vesafb:off, video=efifb:off: 释放帧缓冲 (避免黑屏)
#   rdblacklist=nouveau, modprobe.blacklist=nouveau: 屏蔽开源驱动

# 2. 更新 GRUB
# BIOS + MBR:
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
# UEFI:
sudo grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg   # Rocky
# 或
sudo update-grub                                            # Ubuntu

# 3. 重启
sudo reboot

# 4. 验证 IOMMU 启用
dmesg | grep -i 'iommu enabled'
# DMAR: IOMMU enabled

# 5. 验证 vfio-pci 接管显卡
lspci -k -s 03:00.0
# 03:00.0 VGA compatible controller: NVIDIA Corporation GA104 [GeForce RTX 3070]
# Subsystem: Device 10de:2482
# Kernel driver in use: vfio-pci          ← 成功! 被 vfio-pci 接管

lspci -k -s 03:00.1
# Kernel driver in use: vfio-pci          ← HDMI Audio 也被接管
```

### 3.4 模块加载配置

```bash
# === 配置文件: /etc/modprobe.d/vfio.conf ===
cat > /etc/modprobe.d/vfio.conf << 'EOF'
# 绑定 GPU 到 vfio-pci
options vfio-pci ids=10de:2482,10de:228b disable_vga=1

# 屏蔽 nvidia 和 nouveau 驱动 (防止抢夺设备)
blacklist nvidia
blacklist nouveau
blacklist nvidiafb
blacklist radeon
blacklist amdgpu

# vfio 模块预加载
softdep nvidia pre: vfio-pci
EOF

# === 配置文件: /etc/modprobe.d/kvm.conf ===
cat > /etc/modprobe.d/kvm.conf << 'EOF'
# 忽略 MSR (Windows VM 需要)
options kvm ignore_msrs=1
EOF

# === 更新 initramfs ===
sudo dracut --force
# 或 Ubuntu:
# sudo update-initramfs -u

# 重启
sudo reboot

# 验证模块加载
lsmod | grep vfio
# vfio_pci               45056  0
# vfio_pci_core          81920  1 vfio_pci
# vfio_iommu_type1       49152  0
# vfio                   53248  6 vfio_iommu_type1,vfio_pci_core
# vfio_virqfd            16384  1 vfio_pci_core
```

### 3.5 主机环境准备

```bash
# === 安装 KVM + Libvirt ===
# Rocky / RHEL 9
dnf install -y qemu-kvm libvirt virt-manager virt-install \
    bridge-utils dmidecode edk2-ovmf seabios

# Ubuntu / Debian
apt install -y qemu-kvm libvirt-daemon-system libvirt-clients \
    bridge-utils virt-manager virtinst ovmf seabios

# 启动服务
systemctl enable --now libvirtd

# 验证 KVM
ls -l /dev/kvm
# crw-rw-rw- 1 root kvm 10, 232 Jul 12 10:00 /dev/kvm

# 添加用户到 kvm 组
usermod -aG kvm,libvirt $(whoami)

# === 分配大页内存 (HugePages, 提升性能) ===
# 配置: 分配 16 GB HugePages (2M 页 = 8192 页)
cat >> /etc/sysctl.d/99-hugepages.conf << 'EOF'
vm.nr_hugepages = 8192
EOF

sysctl -p /etc/sysctl.d/99-hugepages.conf

# 验证
grep HugePages /proc/meminfo
# HugePages_Total:    8192
# HugePages_Free:     8192

# 挂载 hugetlbfs
mount -t hugetlbfs hugetlbfs /dev/hugepages
echo "hugetlbfs /dev/hugepages hugetlbfs defaults 0 0" >> /etc/fstab

# === 安装 OVMF (UEFI 启动, 推荐) ===
# 已经安装, 查看路径
rpm -ql edk2-ovmf | grep CODE
# /usr/share/edk2/ovmf/OVMF_CODE.fd
# /usr/share/edk2/ovmf/OVMF_VARS.fd

# === 安装 Windows VirtIO 驱动 (Windows VM 必备) ===
# 下载 virtio-win ISO
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso
# 路径: /var/lib/libvirt/images/virtio-win.iso
```

---

## 四、GPU 隔离与绑定

### 4.1 vfio-pci 绑定方式

```bash
# === 方式 1: 内核参数 (推荐, 前面已做) ===
# GRUB_CMDLINE_LINUX_DEFAULT 中加:
#   vfio-pci.ids=10de:2482,10de:228b
#   启动后自动绑定

# === 方式 2: driverctl (适合热切换) ===
# 安装
dnf install -y driverctl

# 绑定到 vfio-pci
driverctl set-override 0000:03:00.0 vfio-pci
driverctl set-override 0000:03:00.1 vfio-pci

# 解除绑定 (还给 nvidia)
driverctl unset-override 0000:03:00.0
driverctl unset-override 0000:03:00.1
# 然后 modprobe nvidia

# 查看当前驱动
driverctl list-overrides

# === 方式 3: 手动 sysfs (调试用) ===
# 需要先卸载 nvidia 驱动
modprobe -r nvidia_drm nvidia_modeset nvidia

# 解绑
echo 0000:03:00.0 > /sys/bus/pci/devices/0000:03:00.0/driver/unbind
echo 0000:03:00.1 > /sys/bus/pci/devices/0000:03:00.1/driver/unbind

# 绑定 vfio-pci
echo vfio-pci > /sys/bus/pci/devices/0000:03:00.0/driver_override
echo vfio-pci > /sys/bus/pci/devices/0000:03:00.1/driver_override
echo 0000:03:00.0 > /sys/bus/pci/drivers/vfio-pci/bind
echo 0000:03:00.1 > /sys/bus/pci/drivers/vfio-pci/bind
```

### 4.2 验证 VFIO 设备

```bash
# === 验证 vfio 设备节点 ===
ls -l /dev/vfio/
# total 0
# crw------- 1 root root 10, 196 Jul 12 10:00 20     ← IOMMU 组 20
# crw------- 1 root root 10, 197 Jul 12 10:00 vfio   ← 控制设备

# 验证组内设备数
ls -l /dev/vfio/20
# crw------- 1 root root 10, 196 Jul 12 10:00 /dev/vfio/20

# 查看 IOMMU 组详情
cat /sys/kernel/iommu_groups/20/device_list
# 0000:03:00.0
# 0000:03:00.1

# === 验证可用的大页内存 ===
grep HugePages /proc/meminfo
# HugePages_Total:    8192
# HugePages_Free:     8192

# === 验证 NUMA 拓扑 (多路 CPU 环境) ===
numactl --hardware
# available: 2 nodes (0-1)
# node 0 cpus: 0-7,16-23
# node 0 size: 32768 MB
# node 1 cpus: 8-15,24-31
# node 1 size: 32768 MB

# GPU 在哪个 NUMA Node 上?
cat /sys/bus/pci/devices/0000:03:00.0/numa_node
# 1   ← GPU 在 Node 1, VM vCPU 和内存应该分配在 Node 1
```

---

## 五、创建虚拟机

### 5.1 virt-install 命令行创建

```bash
# === 创建 Windows 虚拟机 (GPU 直通 + UEFI) ===

# 先查看 GPU NUMA 节点
GPU_NUMA=$(cat /sys/bus/pci/devices/0000:03:00.0/numa_node)
GPU_GROUP=$(basename $(readlink /sys/bus/pci/devices/0000:03:00.0/iommu_group))

# 创建虚拟机
virt-install \
  --name win11-gpu \
  --ram 16384 \
  --vcpus sockets=1,cores=8,threads=2 \
  --cpu host-passthrough \
  --machine q35 \
  --boot uefi \
  --disk path=/var/lib/libvirt/images/win11-gpu.qcow2,size=200,bus=virtio \
  --cdrom /var/lib/libvirt/images/Win11_22H2.iso \
  --disk path=/var/lib/libvirt/images/virtio-win.iso,device=cdrom \
  --network bridge=br0,model=virtio \
  --graphics spice \
  --video qxl \
  --host-device 0000:03:00.0 \
  --host-device 0000:03:00.1 \
  --iothreads 2 \
  --cpu host-passthrough,kvm=off \
  --features kvm_hidden=on \
  --clock hypervclock \
  --tpm type=emulator,version=2.0 \
  --boot loader=/usr/share/edk2/ovmf/OVMF_CODE.fd,loader_ro=yes,nvram_template=/usr/share/edk2/ovmf/OVMF_VARS.fd

# 参数说明:
#   --host-device:        直通 PCI 设备 (GPU + HDMI Audio)
#   --machine q35:        现代 q35 芯片组, 比 i440fx 更兼容 Windows
#   --cpu host-passthrough: 透传 CPU 特性 (必须)
#   kvm=off / --features kvm_hidden=on: 隐藏 KVM 标识 (防 Error 43)
#   --boot uefi:          UEFI 启动, 支持 GOP 显卡
#   --iothreads 2:        独立 IO 线程
#   --clock hypervclock:  Hyper-V 时钟同步
#   --tpm:                TPM 2.0 (Windows 11 必须)
```

### 5.2 安装后配置

```bash
# === 安装 VirtIO 驱动 (Windows VM) ===
# 启动 VM 后, 在 Windows 中:
# 1. 挂载 virtio-win.iso
# 2. 设备管理器 → 更新网卡驱动 → 选择 ISO 上的 NetKVM
# 3. 存储控制器 → 更新驱动 → viostor/w10/amd64
# 4. 可选: balloon/qemu-ga

# === 安装 NVIDIA 驱动 ===
# 从 NVIDIA 官网下载对应显卡驱动
# 正常安装即可

# === 拔掉 Spice/QXL 虚拟显卡 (直通后虚拟机用真显卡) ===
virsh edit win11-gpu
# 删除 <video> 段 (qxl)
# 或改成 <model type='none'/>

# === 优化 VM 配置 ===
virsh edit win11-gpu
```

### 5.3 libvirt XML 完整配置

```xml
<!-- /etc/libvirt/qemu/win11-gpu.xml -->
<domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>
  <name>win11-gpu</name>
  <uuid>a1b2c3d4-e5f6-7890-abcd-ef1234567890</uuid>
  <title>Windows 11 with GPU Passthrough</title>

  <!-- 内存配置: 16GB + HugePages -->
  <memory unit='GiB'>16</memory>
  <currentMemory unit='GiB'>16</currentMemory>
  <memoryBacking>
    <hugepages/>
    <source type='memfd'/>
    <access mode='shared'/>
  </memoryBacking>

  <!-- VCPU -->
  <vcpu placement='static'>8</vcpu>
  <iothreads>2</iothreads>

  <!-- NUMA 绑定 (CPU 和 GPU 同 Node) -->
  <numatune>
    <memory mode='strict' nodeset='1'/>
  </numatune>

  <!-- CPU 配置 -->
  <cpu mode='host-passthrough' check='none'>
    <topology sockets='1' dies='1' cores='4' threads='2'/>
    <numa>
      <cell id='0' cpus='0-7' memory='16' unit='GiB' memAccess='shared'/>
    </numa>
    <feature policy='disable' name='hypervisor'/>
  </cpu>

  <!-- KVM 隐藏 (防 Error 43) -->
  <features>
    <acpi/>
    <apic/>
    <hyperv>
      <relaxed state='on'/>
      <vapic state='on'/>
      <spinlocks state='on' retries='8191'/>
      <vpindex state='on'/>
      <synic state='on'/>
      <stimer state='on'/>
      <reset state='on'/>
      <frequencies state='on'/>
    </hyperv>
    <kvm>
      <hidden state='on'/>
    </kvm>
    <vmport state='off'/>
    <smm state='on'/>
  </features>

  <!-- 时钟 -->
  <clock offset='localtime'>
    <timer name='hypervclock' present='yes'/>
    <timer name='hpet' present='no'/>
    <timer name='tsc' present='yes' mode='native'/>
  </clock>

  <!-- PMU Passthrough (性能监控) -->
  <pmu state='on'/>

  <!-- OVMF UEFI 启动 -->
  <os>
    <type arch='x86_64' machine='q35'>hvm</type>
    <loader readonly='yes' type='pflash'>/usr/share/edk2/ovmf/OVMF_CODE.fd</loader>
    <nvram template='/usr/share/edk2/ovmf/OVMF_VARS.fd'>/var/lib/libvirt/qemu/nvram/win11-gpu_VARS.fd</nvram>
    <boot dev='hd'/>
  </os>

  <!-- 主机设备: GPU + HDMI Audio -->
  <devices>
    <!-- 网络: virtio -->
    <interface type='bridge'>
      <mac address='52:54:00:ab:cd:ef'/>
      <source bridge='br0'/>
      <model type='virtio'/>
      <driver name='vhost' queues='4'/>
    </interface>

    <!-- 磁盘: virtio -->
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='writeback' io='threads' iothread='1'/>
      <source file='/var/lib/libvirt/images/win11-gpu.qcow2'/>
      <target dev='vda' bus='virtio'/>
    </disk>

    <!-- VirtIO 驱动 ISO -->
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>
      <source file='/var/lib/libvirt/images/virtio-win.iso'/>
      <target dev='sdb' bus='sata'/>
      <readonly/>
    </disk>

    <!-- GPU (VFIO Passthrough) -->
    <hostdev mode='subsystem' type='pci' managed='yes'>
      <driver name='vfio'/>
      <source>
        <address domain='0x0000' bus='0x03' slot='0x00' function='0x0'/>
      </source>
      <address type='pci' domain='0x0000' bus='0x06' slot='0x00' function='0x0'/>
  </hostdev>

    <!-- HDMI Audio (同组) -->
    <hostdev mode='subsystem' type='pci' managed='yes'>
      <driver name='vfio'/>
      <source>
        <address domain='0x0000' bus='0x03' slot='0x00' function='0x1'/>
      </source>
      <address type='pci' domain='0x0000' bus='0x07' slot='0x00' function='0x0'/>
  </hostdev>

    <!-- USB 控制器 (直通键盘鼠标) -->
    <hostdev mode='subsystem' type='usb' managed='yes'>
      <source>
        <vendor id='0x046d'/>
        <product id='0xc077'/>
      </source>
    </hostdev>

    <!-- SPICE (关闭, 虚拟机使用直通 GPU 输出) -->
    <graphics type='none'/>

    <!-- 虚拟串口 (排错用) -->
    <serial type='pty'>
      <target port='0'/>
    </serial>

    <console type='pty'>
      <target type='serial' port='0'/>
    </console>

    <!-- 声卡 -->
    <sound model='ich9'>
      <audio id='1'/>
    </sound>
    <audio id='1' type='none'/>

    <!-- 输入设备 -->
    <input type='keyboard' bus='usb'/>
    <input type='mouse' bus='usb'/>
    <input type='tablet' bus='usb'/>
  </devices>

  <!-- QEMU 额外参数 -->
  <qemu:commandline>
    <!-- 绕过 MSI 问题 (防直通不可用) -->
    <qemu:env name='QEMU_AUDIO_DRV' value='none'/>
    <qemu:arg value='-fw_cfg'/>
    <qemu:arg value='name=opt/ovmf/X-PciMmio64Mb,string=65536'/>

    <!-- 绕过 vBIOS 限制 -->
    <qemu:arg value='-rom'/>
    <qemu:arg value='file=/usr/share/vgabios/nvidia.rom'/>

    <!-- 绕过 MSI (某些主板需要) -->
    <qemu:arg value='-global'/>
    <qemu:arg value='kvm-pit.lost_tick_policy=delay'/>
  </qemu:commandline>
</domain>
```

---

## 六、Linux 虚拟机 GPU 直通

```bash
# === GPU 直通给 Linux VM (AI 训练/计算) ===

# 1. 创建 VM (AI 训练服务器, 无图形界面)
virt-install \
  --name ubuntu-gpu \
  --ram 32768 \
  --vcpus 16 \
  --cpu host-passthrough \
  --machine q35 \
  --boot uefi \
  --disk path=/var/lib/libvirt/images/ubuntu-gpu.qcow2,size=500,bus=virtio \
  --cdrom /var/lib/libvirt/images/ubuntu-22.04-server.iso \
  --network bridge=br0,model=virtio \
  --graphics none \
  --serial pty \
  --console pty,target_type=serial \
  --host-device 0000:03:00.0 \
  --host-device 0000:03:00.1 \
  --iothreads 4

# 2. VM 中安装 NVIDIA 驱动
# 进入 VM (virsh console ubuntu-gpu)
# 在 Ubuntu VM 内:
apt update
apt install -y build-essential linux-headers-$(uname -r)

# 下载驱动
wget https://us.download.nvidia.com/XFree86/Linux-x86_64/550.120/NVIDIA-Linux-x86_64-550.120.run
chmod +x NVIDIA-Linux-x86_64-550.120.run
./NVIDIA-Linux-x86_64-550.120.run

# 或使用 Ubuntu 源 (推荐)
apt install -y nvidia-driver-550-server
# 重启

# 验证
nvidia-smi
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 550.120    Driver Version: 550.120    CUDA Version: 12.4         |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# |===============================+======================+======================|
# |   0  NVIDIA A4000        Off  | 00000000:04:00.0 Off |                  Off |
# +-------------------------------+----------------------+----------------------+

# 3. 安装 CUDA
wget https://developer.download.nvidia.com/compute/cuda/12.4.1/local_installers/cuda_12.4.1_550.54.15_linux.run
sh cuda_12.4.1_550.54.15_linux.run

# 验证 CUDA
nvidia-smi
nvcc --version

# 4. 安装 Docker + NVIDIA Container Toolkit (可选)
# VM 内:
curl -fsSL https://get.docker.com | sh
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list > /etc/apt/sources.list.d/nvidia-docker.list
apt update && apt install -y nvidia-container-toolkit
systemctl restart docker

# 测试 GPU Docker
docker run --rm --gpus all nvidia/cuda:12.4.1-base nvidia-smi

# 5. 性能对比 (直通 vs 裸机)
# 同样的硬件, 直通性能损耗:
#   GPU 计算 (AI 训练):   ~1-3%
#   GPU 渲染 (Blender):  ~2-5%
#   显存带宽:             ~0-1%
#   PCIe 延迟:            ~1-3us 增加
```

---

## 七、性能优化

### 7.1 CPU / 内存

```bash
# === 大页内存 (HugePages) ===
# 前面已配置, 验证:
grep HugePages /proc/meminfo
# HugePages_Total:    8192   ← 16GB 大页
# HugePages_Free:     8192

# libvirt 使用大页 (XML 中 memoryBacking 已配置)

# === CPU Pin (vCPU 固定到物理 CPU) ===
# 避免 CPU 上下文切换开销
cat /sys/bus/pci/devices/0000:03:00.0/numa_node
# 1 → GPU 在 NUMA Node 1, 用 Node 1 的 CPU

virsh edit win11-gpu
# 在 <vcpu> 后添加:
# <cputune>
#   <vcpupin vcpu='0' cpuset='8'/>
#   <vcpupin vcpu='1' cpuset='9'/>
#   <vcpupin vcpu='2' cpuset='10'/>
#   <vcpupin vcpu='3' cpuset='11'/>
#   <vcpupin vcpu='4' cpuset='12'/>
#   <vcpupin vcpu='5' cpuset='13'/>
#   <vcpupin vcpu='6' cpuset='14'/>
#   <vcpupin vcpu='7' cpuset='15'/>
#   <emulatorpin cpuset='8-15'/>
#   <iothreadpin iothread='1' cpuset='8'/>
#   <iothreadpin iothread='2' cpuset='9'/>
# </cputune>

# === TSC 频率固定 (防 Windows VM 时钟不稳) ===
# 确认主机 TSC 稳定
cat /sys/devices/system/clocksource/clocksource0/current_clocksource
# tsc  ← 必须输出 tsc

# 如果输出是 hpet 或 acpi_pm, 需要:
# 在 GRUB 加: clocksource=tsc tsc=reliable

# XML 加 <timer name='tsc' present='yes' mode='native'/>
```

### 7.2 PCIe / 显存

```bash
# === Resizable BAR (显存重设大小) ===
# 将 GPU 的 PCIe BAR 直接映射到其全显存大小
# 提升 PCIe 通信效率 (对 GPU 密集型应用提升明显)

# 检查当前 BAR 大小
lspci -vv -s 03:00.0 | grep -i 'region\|prefetch'
# Region 0: Memory at ... (64-bit, prefetchable) [size=16M]    ← 太小

# 确认 ReBAR 支持
lspci -vv -s 03:00.0 | grep -i 'resizable'
# Capabilities: [400 v1] Physical Resizable BAR
# BAR 0: current size: 16MB, supported: 256MB 512MB 1GB 2GB 4GB 8GB 16GB
# ↕ 支持到 8GB (对应 RTX 3070 的 8GB 显存)

# Resizable BAR 需要在 BIOS 开启 (前面已做)
# 且 QEMU 版本 ≥ 7.0

# 验证 VM 中是否启用:
# Windows VM: GPU-Z → Resizable BAR: Enabled
# Linux VM: nvidia-smi -q | grep 'BAR'
# BAR1 Memory Usage:
# Total: 8192 MiB              ← 映射了 8GB

# === MSI/MSI-X 中断直通 ===
# 避免中断重映射性能损失
# XML 中加:
# <qemu:arg value='-global'/>
# <qemu:arg value='vfio-pci.msi=on'/>

# 验证 MSI 启用:
cat /proc/interrupts | grep vfio
# 68:      vfio-msi     edge      0000:03:00.0
# 69:      vfio-msi     edge      0000:03:00.0
```

### 7.3 IO 线程

```bash
# === iothreads (分离 IO 处理) ===
# 隔离磁盘和网络的 IO 中断, 避免阻塞 vCPU
# XML:
# <iothreads>4</iothreads>
# ... 磁盘上: <driver iothread='1'/>  # 第 1-2 个 iothread
# ... 网络: <driver queues='4'/>      # 4 个队列, 分配 iothread 3-4

# === virtio 多队列 ===
# 网络多队列 (主机和 VM 端都要配)
# XML:
# <driver name='vhost' queues='4'/>

# Windows VM 内:
# 设备管理器 → NetKVM → 高级 → 设置 RSS 队列数 = 4
```

### 7.4 NVIDIA vGPU (GRID)

```
如果需要一张 GPU 分给多台 VM:

  适用场景:
    多用户共享一张高端 GPU (如 A100, H100, L40s)
    VDI 虚拟桌面 (GRID vPC)

  方案限制:
    需要 NVIDIA vGPU License Server (商业授权)
    不支持消费级显卡 (GTX/RTX)
    仅支持数据中心卡: A/H/L 系列

  开通步骤:
    1. BIOS 开启 SR-IOV
    2. 安装 NVIDIA vGPU Manager (Host)
    3. 安装 NVIDIA vGPU Guest Driver (VM)
    4. 配置 License Server
    5. libvirt 中指定 vGPU profile

  vGPU Profile 示例:
    NVIDIA A16-1Q:   将 A16 (4x GPU) 分成 4 个 vGPU, 每 VM 分配 1Q
    NVIDIA A100-10C: 将 A100 切分为 10 个计算实例
    NVIDIA L40S-2Q:  将 L40S 切分为 2 个 vGPU

  费用:
    vGPU 需要 NVIDIA GRID 许可 (按用户/年)
    vCS 计算虚拟化: 较低成本
    vPC 虚拟桌面: 标准许可
    vApps 应用虚拟化: 标准许可
```

---

## 八、故障排查

### 8.1 NVIDIA Error 43 (Windwos VM)

```
现象: Windows VM 安装驱动后设备管理器显示
  "Windows has stopped this device because it has reported problems. (Code 43)"

原因: NVIDIA 驱动检测到运行在 KVM 虚拟机中, 主动阻止

解决:

  1. 隐藏 KVM 标识 (最重要!)
     XML 中:
       <features>
         <kvm>
           <hidden state='on'/>         ← 隐藏 KVM 标志
         </kvm>
         <hyperv>
           ...
         </hyperv>
       </features>
     CPU 中:
       <cpu mode='host-passthrough'>
         <feature policy='disable' name='hypervisor'/>  ← 去掉 hypervisor 标志
       </cpu>

  2. 使用 Hyper-V 时钟
     <clock offset='localtime'>
       <timer name='hypervclock' present='yes'/>
     </clock>

  3. 机型选择 q35
     <type arch='x86_64' machine='q35'>hvm</type>

  4. MSR 忽略
     主机内核参数: kvm.ignore_msrs=1

  5. Vendor ID 修改 (高级)
     <qemu:arg value='-cpu'/>
     <qemu:arg value='host,hv_vendor_id=1234567890ab'/>

  6. 驱动版本
     尝试不同版本驱动, 有些新版 NV 驱动检查更严格
     推荐: 537.xx 或 551.xx

  7. 部分卡不行
     GTX 10xx / RTX 20xx 系列 Error 43 较少
     RTX 30xx / 40xx 系列需要上述全设置
     RTX 50xx 可能需要更新 KVM/QEMU 版本
```

### 8.2 IOMMU 分组错误

```
现象: 启动 VM 时提示设备无法分配

  Error: vfio: Unable to get group fd for device 0000:03:00.0

原因: IOMMU 分组把必要的设备分开了, 或同组设备没都直通

解决:

  1. 检查 IOMMU 分组
     ./list-iommu-groups.sh | grep -A 2 03:00

  2. ACS 覆盖补丁 (粗分组时)
     GRUB 加: pcie_acs_override=downstream
     或:      pcie_acs_override=multifunction
     或:      pcie_acs_override=id:8086:277c,1002:4384

  3. 同组设备必须一起直通
     如果 GPU 和 NVMe 在同一个组, NVMe 也要直通给 VM
     或 修改内核设备树 (麻烦)

  4. 内核升级
     新内核有更好的 ACS 支持
```

### 8.3 黑屏问题

```
现象: VM 启动后显示器黑屏, 无输出

原因 1: UEFI GOP BIOS 问题

解决:
  1. 确认显卡支持 UEFI GOP
     nvidia-smi -q | grep 'UEFI'
     # UEFI Compatible: Yes

  2. 如果不支持:
     - 使用 CSM/Legacy 模式 (BIOS 关闭 UEFI)
     - 刷 UEFI GOP ROM (部分卡支持)

  3. OVMF 问题
     确认 OVMF_CODE.fd 路径正确
     尝试使用 edk2-ovmf 内置的纯 CODE 文件 (不含 VARS)

  4. 尝试使用 Seabios 而不是 OVMF (如果显卡不支持 UEFI)
     <os>
       <type arch='x86_64' machine='q35'>hvm</type>
       <boot dev='hd'/>
     </os>
     <loader type='rom'>/usr/share/seabios/bios.bin</loader>

原因 2: 帧缓冲冲突

  主机帧缓冲可能占用了显卡
  GRUB 加:
    video=vesafb:off video=efifb:off vga=normal
    rdblacklist=nouveau

原因 3: HDMI 欺骗器

  如果 VM headless (不连接显示器), 显卡不输出
  方案:
    - 插一个 HDMI 欺骗器 (假负载)
    - VM 中设置虚拟显示 (如 Looking Glass)
    - 使用 Sunix 显卡输出模拟器
```

### 8.4 中断 / DMA 问题

```
现象: VM 卡死, dmesg 大量 IOMMU 错误

  DMAR: DRHD: handling fault status reg 3
  DMAR: [DMA Read] Request device [03:00.0] fault addr 0x12345678

原因: IOMMU 中断重映射问题

解决:

  1. IRQ Remapping
     确认 BIOS 中 Interrupt Remapping 开启
     dmesg | grep 'IRQ remapping'
     # DMAR-IR: Enabled IRQ remapping in x2apic mode

  2. MSI 绕过
     XML 加:
     <qemu:arg value='-global'/>
     <qemu:arg value='vfio-pci.msi_enable=off'/>

  3. 旁路 IOMMU 失败 (硬件 bug)
     GRUB 加: iommu=pt

  4. 尝试 pci=realloc
     GRUB 加: pci=realloc

  5. 尝试禁用 ACS (不是补丁, 是禁用)
     GRUB 加: acpi=off   (不推荐, 严重影响性能)

  6. GPU 的 FLR 问题
     某些 GPU 重置有问题
     XML 加:
     <qemu:arg value='-global'/>
     <qemu:arg value='vfio-pci.disable_vga=1'/>
     <qemu:arg value='-global'/>
     <qemu:arg value='vfio-pci.no-kvm-ioeventfd=1'/>
```

### 8.5 其他常见问题

| 现象 | 原因 | 解决 |
|:---|:---|:---|
| VM 启动慢 (5min+) | 显卡 vBIOS 初始化慢 | 尝试 romfile 加载 vBIOS |
| nvidia-smi 报 No devices | VM 内没装对驱动 | 检查 lspci -k 确认设备可见 |
| GPU 温度高但没使用 | 驱动电源管理问题 | 设置 persistence mode `nvidia-persistenced` |
| 显存显示 0MB | Resizable BAR 未启用 | BIOS 开 ReBAR, QEMU ≥ 7.0 |
| USB 鼠标键盘不工作 | USB 控制器未直通 | 直通 USB 控制器或使用 evdev |
| 音频无输出 | HDMI Audio 未直通 | 确认 03:00.1 已直通 |
| 重启 VM 后 GPU 不可用 | FLR 重置问题 | VM 完全关机再启动 |
| QEMU 崩溃 segfault | 内核/QEMU 版本太旧 | 升级 QEMU ≥ 7.2, 内核 ≥ 5.15 |
| Windows 蓝屏 (VIDEO_TDR_FAILURE) | GPU 驱动超时 | 增 TDR 延迟或换驱动版本 |

### 8.6 诊断工具

```bash
# === 主机端排查 ===

# 1. 查看 dmesg IOMMU 相关错误
dmesg -T | grep -i -E 'iommu|vfio|dmir|dmar'

# 2. 查看 QEMU 日志
tail -f /var/log/libvirt/qemu/win11-gpu.log

# 3. 验证 vfio 设备
lspci -k -s 03:00.0
cat /sys/kernel/iommu_groups/20/device_list
ls -l /dev/vfio/

# 4. 查看中断
cat /proc/interrupts | grep vfio

# 5. CPU / 内存排查
cat /sys/bus/pci/devices/0000:03:00.0/numa_node
numactl --hardware
grep HugePages /proc/meminfo

# 6. VM 状态
virsh list --all
virsh dominfo win11-gpu
virsh dumpxml win11-gpu > /tmp/win11-gpu.xml

# === VM 内排查 (Linux) ===
lspci -k
nvidia-smi
nvidia-smi -q | grep 'BAR'
dmesg | grep -i nvidia

# VM 内排查 (Windows)
# GPU-Z
# Device Manager → 查看错误代码
# Event Viewer → System → nvlddmkm 错误日志
```

---

## 九、配置速查表

| 配置项 | 文件/命令 | 内容 |
|:---|:---|:---|
| GRUB 内核参数 (Intel) | `/etc/default/grub` | `intel_iommu=on iommu=pt vfio-pci.ids=10de:XXXX,10de:YYYY kvm.ignore_msrs=1 video=vesafb:off video=efifb:off rdblacklist=nouveau` |
| GRUB 内核参数 (AMD) | `/etc/default/grub` | `amd_iommu=on iommu=pt vfio-pci.ids=10de:XXXX,10de:YYYY kvm.ignore_msrs=1 video=vesafb:off video=efifb:off rdblacklist=nouveau` |
| VFIO 模块配置 | `/etc/modprobe.d/vfio.conf` | `options vfio-pci ids=... disable_vga=1` + `blacklist nvidia nouveau` |
| KVM 模块配置 | `/etc/modprobe.d/kvm.conf` | `options kvm ignore_msrs=1` |
| HugePages | `/etc/sysctl.d/99-hugepages.conf` | `vm.nr_hugepages=8192` |
| NUMA 绑定 | libvirt XML `<numatune>` | `memory mode='strict' nodeset='1'` |
| CPU 隐藏 | libvirt XML `<features><kvm>` | `<hidden state='on'/>` |
| Hypervisor 隐藏 | libvirt XML `<cpu>` | `<feature policy='disable' name='hypervisor'/>` |
| OVMF UEFI 路径 | `/usr/share/edk2/ovmf/OVMF_CODE.fd` | QEMU UEFI 固件 |
| VirtIO 驱动 ISO | `/var/lib/libvirt/images/virtio-win.iso` | Windows 驱动 |
| GPU ROM 备份 | `/usr/share/vgabios/nvidia.rom` | 可选, 绕过 vBIOS 问题 |
| GPU PCI ID 查询 | `lspci -n -s 03:00.0` | 获取 `10de:XXXX` |
| IOMMU 分组查询 | `find /sys/kernel/iommu_groups/ -type l` | 确认直通可行性 |
| GRUB 更新 (BIOS) | `grub2-mkconfig -o /boot/grub2/grub.cfg` | BIOS 启动系统 |
| GRUB 更新 (UEFI) | `grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg` | UEFI 启动系统 |
| Initramfs 更新 | `dracut --force` | 重建 initramfs |
| VM 日志 | `/var/log/libvirt/qemu/<vm>.log` | QEMU 运行日志 |

---

*最后更新: 2026-07-14*
