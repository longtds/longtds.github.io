# KVM

## 架构

KVM（Kernel-based Virtual Machine）是 Linux 内核的虚拟化模块，将 Linux 变成 Type1 Hypervisor。

## 常用命令

```bash
# 检查 CPU 是否支持虚拟化
grep -E "(vmx|svm)" /proc/cpuinfo

# 安装 KVM
apt install -y qemu-kvm libvirt-daemon-system libvirt-clients virt-manager

# 查看虚拟机
virsh list --all
virsh list --state-running

# 创建虚拟机
virt-install \
  --name vm01 \
  --ram 4096 \
  --vcpus 4 \
  --disk path=/var/lib/libvirt/images/vm01.qcow2,size=50 \
  --network bridge=br0 \
  --cdrom /path/to/iso

# 管理虚拟机
virsh start vm01
virsh shutdown vm01
virsh destroy vm01
virsh reboot vm01

# 迁移（热迁移）
virsh migrate --live vm01 qemu+ssh://target-host/system
```
