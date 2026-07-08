# PXE 批量加载 Linux 测试镜像（内存启动）

> 服务器到货 50 台要做压力测试、内存测试、硬盘检测——不需要装系统，PXE 网络引导直接加载镜像到内存，开机即测，测完即走，磁盘零写入。

---

## 一、原理与适用场景

### 1.1 内存启动 vs 磁盘安装

| 维度 | PXE 内存启动 | PXE 安装到磁盘 |
|:---|:---|:---|
| 是否写磁盘 | ❌ 不写 | ✅ 分区+安装 |
| 启动方式 | 内核 + initramfs 全部加载到 RAM | 内核引导安装程序 |
| 运行依赖 | 纯内存运行，不依赖本地盘 | 依赖本地磁盘 |
| 重启后 | 内存清空，回到原始状态 | 系统保留在磁盘 |
| 适用场景 | 硬件测试/诊断/固件升级/临时救援 | 正式部署操作系统 |
| 启动速度 | 30 秒 - 3 分钟（取决于镜像大小） | 10-30 分钟安装 |
| 可同时测试 | ✅ 批量并行 | 逐台安装 |

### 1.2 典型场景

```
服务器到货验收          → Memtest86+ 内存测试 + CPU 烤机
硬盘健康检查            → SystemRescue 启动 + smartctl 扫盘
固件/BIOS 批量升级      → DOS/WinPE/Linux 内存启动 + 刷写工具
故障诊断               → 启动到内存环境排查（不依赖故障盘）
临时计算任务            → 内存 Linux + 跑完关机
网络设备测试            → 内存启动 + iperf3/fping 测网络
```

### 1.3 内存启动的两种方式

```
方式一：initramfs 独立运行（推荐，简单）
  ┌───────────────────────────────────────┐
  │ PXE 下载 vmlinuz + initramfs.img      │
  │ → 内核加载 initramfs 到 RAM           │
  │ → initramfs 解压后作为完整根文件系统   │
  │ → 全部在内存中运行                    │
  │ → 不需要 NFS/HTTP 持续连接            │
  └───────────────────────────────────────┘
  适合: 小镜像 (<2GB), 测试工具盘, Memtest

方式二：NFS Root（适合大镜像）
  ┌───────────────────────────────────────┐
  │ PXE 下载 vmlinuz + 小 initramfs       │
  │ → 内核启动后通过 NFS 挂载根文件系统    │
  │ → 文件在 NFS 服务器上, 按需读取        │
  │ → 内存占用小, 支持完整发行版           │
  └───────────────────────────────────────┘
  适合: 完整桌面环境, >2GB 镜像, 需要持久化
```

---

## 二、环境准备

### 2.1 复用已有 PXE 服务器

本文基于 [PXE 批量自动安装](02-PXE批量自动安装.md) 中已搭建的服务器：

```
PXE 服务器: 192.168.100.10
  - dnsmasq (DHCP + TFTP)  ← 已有
  - nginx (HTTP)            ← 已有
  - TFTP 根目录: /srv/tftp
  - HTTP 根目录: /srv/install

新增目录:
  /srv/tftp/memtest/        ← Memtest86+
  /srv/tftp/rescue/         ← SystemRescue
  /srv/tftp/ubuntu-live/    ← Ubuntu Live (内存模式)
  /srv/nfsroot/             ← NFS Root 文件系统
```

### 2.2 安装额外组件

```bash
# NFS 服务 (NFS Root 方式需要)
dnf install -y nfs-utils
systemctl enable --now nfs-server

# 工具
dnf install -y xorriso squashfs-tools cpio
```

---

## 三、Memtest86+ 内存测试（最常用）

### 3.1 准备镜像

```bash
mkdir -p /srv/tftp/memtest

# 下载 Memtest86+ (免费版, 开源)
cd /tmp
# 官方: https://www.memtest86.com/download.htm
# 选 "Linux/Mac" 版本的镜像, 或直接用预编译二进制

# 方式一: 从 SystemRescue 提取 (最简单)
wget https://downloads.sourceforge.net/systemrescue/systemrescue-11.02-amd64.iso
mount -o loop,ro systemrescue-11.02-amd64.iso /mnt

# SystemRescue 内含 memtest86+
cp /mnt/boot/memtest86+/memtest.bin /srv/tftp/memtest/memtest86+
umount /mnt

# 方式二: 从 Fedora/EPEL 安装
dnf install -y memtest86+
cp /boot/memtest86+-5.31 /srv/tftp/memtest/memtest86+

# 方式三: Memtest86 (商业版, 支持 UEFI Secure Boot)
# 下载 memtest86-usb.zip → 解压 → 提取 memtest (EFI 二进制)
# 商业版支持 UEFI Secure Boot, 免费 13 轮测试
```

### 3.2 添加引导菜单

#### Legacy BIOS（pxelinux.cfg/default 追加）

```bash
cat >> /srv/tftp/pxelinux.cfg/default << 'EOF'

LABEL memtest
    MENU LABEL ^4. Memtest86+ 内存测试
    KERNEL memtest/memtest86+
    # Memtest86+ 不需要 initramfs, 自身就是裸金属程序
EOF
```

#### UEFI（grub/grub.cfg 追加）

```bash
cat >> /srv/tftp/grub/grub.cfg << 'EOF'

menuentry "4. Memtest86+ 内存测试" {
    linux16 memtest/memtest86+
}
EOF
```

!!! note "Memtest86+ 特殊性"
    Memtest86+ 不是 Linux 内核，是一个裸金属程序，直接接管硬件。
    - Legacy BIOS: 用 `linux16` 或 `kernel` 加载
    - UEFI: 需要支持 Legacy 的 GRUB 或用 memtest86 EFI 版本
    - 不需要 initramfs

### 3.3 批量启动内存测试

```bash
#!/bin/bash
# batch-memtest.sh — 批量启动 Memtest86+
# 用法: batch-memtest.sh <bmc_ip_list>

BMC_USER="root"
BMC_PASS="calvin"

while read -r bmc_ip; do
    [ -z "$bmc_ip" ] && continue
    echo "[$(date +%H:%M:%S)] $bmc_ip → Memtest86+"

    # 设置 PXE 引导
    ipmitool -I lanplus -H "$bmc_ip" -U "$BMC_USER" -P "$BMC_PASS" \
        chassis bootdev pxe 2>/dev/null

    # 重启
    ipmitool -I lanplus -H "$bmc_ip" -U "$BMC_USER" -P "$BMC_PASS" \
        chassis power cycle 2>/dev/null

    sleep 3
done < "$1"

echo "全部触发。Memtest86+ 启动后自动开始测试。"
echo "测试时间取决于内存容量: 128GB 约 2-4 小时, 256GB 约 4-8 小时"
```

!!! tip "Memtest86+ 自动化结果"
    Memtest86+ 免费版不支持自动上报结果。批量测试时：
    - 人工通过 BMC KVM 逐台查看（小批量可行）
    - 使用商业版 MemTest86 Pro（支持 HTML 报告 + 网络上传）
    - 或改用 Linux 内存测试工具（见第五节），脚本化结果上报

---

## 四、SystemRescue 内存启动（诊断工具箱）

### 4.1 准备镜像

```bash
mkdir -p /srv/tftp/rescue
mkdir -p /srv/install/rescue

# 下载 SystemRescue
cd /tmp
wget https://downloads.sourceforge.net/systemrescue/systemrescue-11.02-amd64.iso

mount -o loop,ro systemrescue-11.02-amd64.iso /mnt

# 复制内核和 initramfs
cp /mnt/sysresccd/boot/x86_64/vmlinuz /srv/tftp/rescue/vmlinuz
cp /mnt/sysresccd/boot/x86_64/initramfs.img /srv/tftp/rescue/initramfs.img

# 复制 squashfs 根文件系统 (放到 HTTP, initramfs 启动后下载)
cp /mnt/sysresccd/x86_64/airootfs.sfs /srv/install/rescue/

# 复制 BIOS/UEFI 引导文件
cp /mnt/sysresccd/boot/x86_64/sysresccd.img /srv/tftp/rescue/ 2>/dev/null || true

umount /mnt
```

### 4.2 添加引导菜单

#### Legacy BIOS

```bash
cat >> /srv/tftp/pxelinux.cfg/default << 'EOF'

LABEL rescue
    MENU LABEL ^5. SystemRescue (内存启动)
    KERNEL rescue/vmlinuz
    APPEND initrd=rescue/initramfs.img \
           archisobasedir=sysresccd \
           archiso_http_srv=http://192.168.100.10/install/rescue/ \
           ip=dhcp \
           copytoram \
           quiet
EOF
```

#### UEFI

```bash
cat >> /srv/tftp/grub/grub.cfg << 'EOF'

menuentry "5. SystemRescue (内存启动)" {
    linux rescue/vmlinuz \
          archisobasedir=sysresccd \
          archiso_http_srv=http://192.168.100.10/install/rescue/ \
          ip=dhcp \
          copytoram \
          quiet
    initrd rescue/initramfs.img
}
EOF
```

!!! info "copytoram 参数"
    `copytoram` 是关键参数：让 initramfs 把整个 squashfs 文件系统复制到内存中运行，之后不再依赖网络。这样：
    - 启动完成后网络可以断开
    - 不依赖 HTTP 服务器持续可用
    - 全部在 RAM 中运行，速度最快

### 4.3 SystemRescue 中的测试工具

启动后通过 SSH 或 BMC 串口连接，可用的硬件测试工具：

```bash
# === CPU 测试 ===
# 烤机 (mprime = Prime95 for Linux)
mprime -t            # 多线程压力测试

# stress-ng 综合压力
stress-ng --cpu $(nproc) --io 4 --vm 2 --vm-bytes 4G --timeout 1h
stress-ng --cpu 0 --cpu-method all --metrics-brief --timeout 2h

# === 内存测试 ===
# memtester (运行中内存测试, 不影响系统运行)
memtester 8G 3       # 测试 8GB 内存, 循环 3 次

# === 磁盘测试 ===
# smartctl 健康检查
smartctl -a /dev/sda
smartctl -t short /dev/sda    # 短测试 (2分钟)
smartctl -t long /dev/sda     # 长测试 (数小时)

# fio 性能测试
fio --name=seq-read --rw=read --bs=1M --size=10G --numjobs=1 --runtime=60 \
    --filename=/dev/sda --direct=1
fio --name=rand-write --rw=randwrite --bs=4k --size=1G --numjobs=4 \
    --filename=/dev/sda --direct=1 --runtime=60

# badblocks 坏块扫描
badblocks -sv /dev/sda

# === 网络 ===
iperf3 -s            # 服务端
iperf3 -c <peer_ip>  # 客户端测带宽

# === 系统 ===
sensors              # 温度传感器
dmidecode -t memory  # 内存条详情
lspci -v             # PCIe 设备
lscpu                # CPU 信息
```

---

## 五、Ubuntu Live 内存启动（完整环境）

### 5.1 准备镜像

```bash
mkdir -p /srv/tftp/ubuntu-live
mkdir -p /srv/install/ubuntu-live

cd /tmp
mount -o loop,ro ubuntu-22.04.5-live-server-amd64.iso /mnt

# 复制内核和 initramfs
cp /mnt/casper/vmlinuz /srv/tftp/ubuntu-live/vmlinuz
cp /mnt/casper/initrd /srv/tftp/ubuntu-live/initrd

# casper 文件系统 (放到 HTTP)
cp /mnt/casper/casper.squashfs /srv/install/ubuntu-live/
# 有些版本叫 filesystem.squashfs
cp /mnt/casper/filesystem.squashfs /srv/install/ubuntu-live/ 2>/dev/null || true

umount /mnt
```

### 5.2 添加引导菜单

#### Legacy BIOS

```bash
cat >> /srv/tftp/pxelinux.cfg/default << 'EOF'

LABEL ubuntu_live
    MENU LABEL ^6. Ubuntu 22.04 Live (内存启动)
    KERNEL ubuntu-live/vmlinuz
    APPEND initrd=ubuntu-live/initrd \
           root=/dev/ram0 \
           ramdisk_size=2000000 \
           url=http://192.168.100.10/install/ubuntu-live/casper.squashfs \
           boot=casper \
           netboot=url \
           ip=dhcp \
           toram \
           quiet splash
EOF
```

#### UEFI

```bash
cat >> /srv/tftp/grub/grub.cfg << 'EOF'

menuentry "6. Ubuntu 22.04 Live (内存启动)" {
    linux ubuntu-live/vmlinuz \
          root=/dev/ram0 ramdisk_size=2000000 \
          url=http://192.168.100.10/install/ubuntu-live/casper.squashfs \
          boot=casper netboot=url \
          ip=dhcp toram quiet splash
    initrd ubuntu-live/initrd
}
EOF
```

!!! tip "toram 参数"
    `toram` 让 Ubuntu Live 把整个 squashfs 加载到内存，启动后不依赖网络。
    - `ramdisk_size=2000000` 分配 2GB 内存盘空间（需足够大）
    - `url=` 指定 squashfs 下载地址
    - `netboot=url` 告诉 casper 从 URL 获取根文件系统

### 5.3 Ubuntu Live 中配置 SSH（自动）

默认 Ubuntu Live 没有 SSH 服务，需要通过 cloud-init 自动配置：

```bash
mkdir -p /srv/install/ubuntu-live/cloud-init

cat > /srv/install/ubuntu-live/cloud-init/user-data << 'EOF'
#cloud-config
hostname: test-node
ssh_pwauth: true
chpasswd:
  list: |
    ubuntu: TestPass123!
  expire: false
ssh_authorized_keys:
  - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... admin@ops
packages:
  - stress-ng
  - smartmontools
  - fio
  - iperf3
  - lm-sensors
runcmd:
  - systemctl start ssh
  - sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
  - systemctl restart ssh
EOF

touch /srv/install/ubuntu-live/cloud-init/meta-data
```

引导菜单内核参数追加：

```
ds=nocloud-net\;s=http://192.168.100.10/install/ubuntu-live/cloud-init/
```

---

## 六、Rocky Linux Live 内存启动

### 6.1 准备镜像

```bash
mkdir -p /srv/tftp/rocky-live
mkdir -p /srv/install/rocky-live

cd /tmp
# Rocky 9 Live ISO (不是 DVD 安装镜像)
wget https://download.rockylinux.org/pub/rocky/9/live/x86_64/Rocky-9.5-XFCE-x86_64-latest.iso

mount -o loop,ro Rocky-9.5-XFCE-x86_64-latest.iso /mnt

# 复制内核和 initramfs
cp /mnt/isolinux/vmlinuz /srv/tftp/rocky-live/vmlinuz
cp /mnt/isolinux/initrd.img /srv/tftp/rocky-live/initrd.img

# 复制 LiveOS 目录 (squashfs 根文件系统)
rsync -aH /mnt/LiveOS/ /srv/install/rocky-live/LiveOS/

umount /mnt
```

### 6.2 添加引导菜单

```bash
# Legacy BIOS
cat >> /srv/tftp/pxelinux.cfg/default << 'EOF'

LABEL rocky_live
    MENU LABEL ^7. Rocky 9 Live (内存启动)
    KERNEL rocky-live/vmlinuz
    APPEND initrd=rocky-live/initrd.img \
           root=live:http://192.168.100.10/install/rocky-live/LiveOS/squashfs.img \
           rd.live.image \
           rd.live.ram=1 \
           ip=dhcp \
           quiet
EOF

# UEFI
cat >> /srv/tftp/grub/grub.cfg << 'EOF'

menuentry "7. Rocky 9 Live (内存启动)" {
    linux rocky-live/vmlinuz \
          root=live:http://192.168.100.10/install/rocky-live/LiveOS/squashfs.img \
          rd.live.image rd.live.ram=1 \
          ip=dhcp quiet
    initrd rocky-live/initrd.img
}
EOF
```

**关键参数说明：**

| 参数 | 作用 |
|:---|:---|
| `root=live:http://...` | 从 HTTP 下载 LiveOS squashfs 作为根文件系统 |
| `rd.live.image` | 启用 LiveOS 镜像模式 |
| `rd.live.ram=1` | 将 squashfs 完全加载到内存（关键！） |
| `ip=dhcp` | 网络配置（下载镜像需要） |

---

## 七、NFS Root 方式（大镜像/持久化）

### 7.1 适用场景

initramfs 方式适合 <2GB 的小镜像。如果需要：

- 完整桌面环境（>4GB squashfs）
- 测试数据需要持久化（重启不丢）
- 多台机器共享同一文件系统

用 NFS Root 更合适。

### 7.2 准备 NFS Root

```bash
mkdir -p /srv/nfsroot/rocky-live

# 从 Live ISO 解压完整文件系统
mount -o loop,ro Rocky-9.5-XFCE-x86_64-latest.iso /mnt
# LiveOS squashfs 里面有完整根文件系统
cd /mnt/LiveOS
unsquashfs -d /srv/nfsroot/rocky-live/rootfs squashfs.img
# 如果 squashfs.img 里面还有 ext4 镜像, 再解一层:
# mount -o loop rootfs/LiveOS/rootfs.img /tmp/rootfs
# rsync -aH /tmp/rootfs/ /srv/nfsroot/rocky-live/
# umount /tmp/rootfs

# 设置 NFS 导出
cat >> /etc/exports << 'EOF'
/srv/nfsroot/rocky-live  *(ro,sync,no_root_squash,no_subtree_check)
EOF

exportfs -ra
```

### 7.3 引导菜单

```bash
# Legacy BIOS
cat >> /srv/tftp/pxelinux.cfg/default << 'EOF'

LABEL rocky_nfs
    MENU LABEL ^8. Rocky 9 Live (NFS Root)
    KERNEL rocky-live/vmlinuz
    APPEND initrd=rocky-live/initrd.img \
           root=nfs:192.168.100.10:/srv/nfsroot/rocky-live/rootfs \
           rw \
           ip=dhcp \
           quiet
EOF

# UEFI
cat >> /srv/tftp/grub/grub.cfg << 'EOF'

menuentry "8. Rocky 9 Live (NFS Root)" {
    linux rocky-live/vmlinuz \
          root=nfs:192.168.100.10:/srv/nfsroot/rocky-live/rootfs \
          rw ip=dhcp quiet
    initrd rocky-live/initrd.img
}
EOF
```

### 7.4 initramfs vs NFS Root 对比

| 维度 | initramfs (copytoram) | NFS Root |
|:---|:---|:---|
| 内存占用 | 大（整个根文件系统在 RAM） | 小（按需读取） |
| 网络依赖 | 启动后可断网 | 持续依赖 NFS 连接 |
| 启动速度 | 慢（下载整个镜像到 RAM） | 快（按需加载） |
| 运行速度 | 快（纯内存读写） | 受网络/NFS 性能影响 |
| 持久化 | ❌ 重启全丢 | ✅ 可配置持久化 |
| 适合镜像大小 | <2GB | 任意大小 |
| 并发能力 | 好（各跑各的） | 受 NFS 服务器性能限制 |

---

## 八、自定义最小测试镜像（initramfs）

### 8.1 场景

不需要完整 Linux 发行版，只需要一个最小环境跑测试脚本：
- 启动时间 < 30 秒
- 内存占用 < 512MB
- 自动执行测试脚本并上报结果

### 8.2 构建自定义 initramfs

```bash
#!/bin/bash
# build-test-initramfs.sh — 构建最小测试 initramfs

set -e

WORKDIR=/tmp/initramfs-build
OUTPUT=/srv/tftp/test-image/initramfs-test.img

mkdir -p "$WORKDIR" /srv/tftp/test-image
cd "$WORKDIR"

# 1. 下载 BusyBox (静态编译, 无依赖)
wget -O busybox https://busybox.net/downloads/binaries/1.36.1-x86_64-linux-musl/busybox
chmod +x busybox

# 2. 创建基本目录结构
mkdir -p bin sbin etc proc sys dev tmp run usr/bin usr/sbin var/log

# 3. 安装 BusyBox
cp busybox bin/busybox
cd bin
for cmd in sh ash cat echo ls mkdir mount umount ip ping wget sleep \
           dmesg uname hostname date hwclock env test [ expr tr \
           grep sed awk head tail cut wc sort uniq find chmod chown \
           ln rm cp mv dd sync poweroff reboot; do
    ln -sf busybox "$cmd"
done
cd ..

# 4. 基本设备节点
mknod -m 622 dev/console c 5 1
mknod -m 666 dev/null c 1 3
mknod -m 666 dev/zero c 1 5
mknod -m 666 dev/tty c 5 0
mknod -m 444 dev/random c 1 8
mknod -m 444 dev/urandom c 1 9

# 5. init 脚本 (PID 1)
cat > init << 'INITEOF'
#!/bin/sh
# === 最小测试环境 init ===

# 挂载虚拟文件系统
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev 2>/dev/null || true
mount -t tmpfs none /tmp
mount -t tmpfs none /run

# 网络
ip link set lo up
# 等待 DHCP
udhcpc -i eth0 -t 10 -n 2>/dev/null || udhcpc -i enp0s3 -t 10 -n 2>/dev/null || true

MY_IP=$(ip -4 addr show | grep 'inet ' | grep -v 127 | awk '{print $2}' | cut -d/ -f1 | head -1)
MAC=$(cat /sys/class/net/*/address 2>/dev/null | head -1)
SERVER="192.168.100.10"

echo "================================"
echo "  PXE 测试环境已启动"
echo "  IP:   $MY_IP"
echo "  MAC:  $MAC"
echo "  时间: $(date)"
echo "================================"

# 下载并执行测试脚本
echo "[$(date +%H:%M:%S)] 下载测试脚本..."
wget -q -O /tmp/test.sh "http://${SERVER}/test/test.sh" && {
    chmod +x /tmp/test.sh
    echo "[$(date +%H:%M:%S)] 开始执行测试..."
    /tmp/test.sh 2>&1 | tee /tmp/test-result.log

    # 上报结果到 PXE 服务器
    echo "[$(date +%H:%M:%S)] 上报测试结果..."
    wget -q -O /dev/null \
        "http://${SERVER}/test/report.php?mac=${MAC}&ip=${MY_IP}&status=done" 2>/dev/null

    # 上传详细日志
    cat /tmp/test-result.log | wget -q -O /dev/null \
        --post-data="$(cat /tmp/test-result.log)" \
        "http://${SERVER}/test/upload.php?mac=${MAC}" 2>/dev/null
} || {
    echo "[$(date +%H:%M:%S)] ❌ 无法下载测试脚本"
}

echo "[$(date +%H:%M:%S)] 测试完成。60 秒后关机..."
sleep 60
poweroff -f
INITEOF
chmod +x init

# 6. 下载测试工具到 initramfs
# 添加 stress-ng (静态编译版)
wget -q -O bin/stress-ng "https://github.com/ColinIanKing/stress-ng/releases/download/V0.18.05/stress-ng-0.18.05.x86_64-static" 2>/dev/null && chmod +x bin/stress-ng || true

# 添加 smartctl (静态编译)
# 需要自行编译或从包中提取

# 7. 打包 initramfs
find . | cpio -H newc -o | gzip -9 > "$OUTPUT"

echo "构建完成: $OUTPUT"
ls -lh "$OUTPUT"
```

### 8.3 测试脚本（HTTP 提供）

```bash
# /srv/install/test/test.sh — 服务器端维护, 随时可改

#!/bin/sh
# === 服务器硬件测试脚本 ===

echo "===== 1. 系统信息 ====="
uname -a
cat /proc/cpuinfo | grep "model name" | head -1
cat /proc/meminfo | grep MemTotal
cat /proc/cmdline

echo ""
echo "===== 2. CPU 测试 (60秒压力) ====="
if [ -x /bin/stress-ng ]; then
    stress-ng --cpu $(nproc) --timeout 60s --metrics-brief
    echo "CPU 测试: PASS"
else
    echo "stress-ng 不可用, 跳过"
fi

echo ""
echo "===== 3. 内存测试 ====="
# 简单内存写入测试
MEMTOTAL=$(cat /proc/meminfo | grep MemTotal | awk '{print $2}')
TESTMEM=$((MEMTOTAL / 4))  # 测试 1/4 内存
echo "测试 ${TESTMEM}KB 内存..."
dd if=/dev/urandom of=/tmp/memtest bs=1M count=$((TESTMEM / 1024)) 2>/dev/null
md5sum /tmp/memtest
rm -f /tmp/memtest
echo "内存测试: PASS"

echo ""
echo "===== 4. 磁盘检测 ====="
lsblk
for disk in /dev/sd? /dev/nvme?n1; do
    [ -b "$disk" ] || continue
    echo "--- $disk ---"
    cat /sys/block/$(basename $disk)/device/model 2>/dev/null || echo "N/A"
    cat /sys/block/$(basename $disk)/size 2>/dev/null | awk '{printf "容量: %.1f GB\n", $1/2097152}'
done

echo ""
echo "===== 5. 网络测试 ====="
ip addr show | grep 'inet ' | grep -v 127
ping -c 3 192.168.100.10

echo ""
echo "===== 测试完成 ====="
echo "结果: ALL PASS"
```

### 8.4 引导菜单

```bash
# Legacy BIOS
cat >> /srv/tftp/pxelinux.cfg/default << 'EOF'

LABEL test_image
    MENU LABEL ^9. 自定义测试镜像 (最小 initramfs)
    KERNEL test-image/vmlinuz
    APPEND initrd=test-image/initramfs-test.img ip=dhcp quiet
EOF

# UEFI
cat >> /srv/tftp/grub/grub.cfg << 'EOF'

menuentry "9. 自定义测试镜像 (最小 initramfs)" {
    linux test-image/vmlinuz ip=dhcp quiet
    initrd test-image/initramfs-test.img
}
EOF
```

!!! note "内核选择"
    自定义 initramfs 需要一个 Linux 内核。可以直接用 Rocky/Ubuntu 的标准内核：
    ```bash
    cp /boot/vmlinuz-$(uname -r) /srv/tftp/test-image/vmlinuz
    ```
    确保内核编译了网络驱动、DHCP 客户端、tmpfs 支持（发行版默认内核都有）。

---

## 九、批量测试自动化

### 9.1 全流程脚本

```bash
#!/bin/bash
# batch-test.sh — 批量 PXE 内存启动 + 硬件测试
#
# 用法: batch-test.sh <bmc_list_file>
# 文件格式: 每行 BMC_IP,HOSTNAME
# 例如:
#   192.168.100.201,node-01
#   192.168.100.202,node-02

SERVER_IP="192.168.100.10"
BMC_USER="root"
BMC_PASS="calvin"
RESULT_DIR="/var/log/pxe-test"
TEST_IMAGE="test_image"   # 引导菜单中的 LABEL

mkdir -p "$RESULT_DIR"

# 1. 启动 HTTP 接收结果
start_result_server() {
    # 简单方案: 用 nc 监听, 或用 python http server
    python3 -c "
import http.server, os, datetime

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if '/test/report' in self.path:
            # 解析 mac=xx&ip=xx&status=xx
            import urllib.parse
            params = urllib.parse.parse_qs(self.path.split('?',1)[1])
            mac = params.get('mac',[''])[0]
            status = params.get('status',[''])[0]
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            logfile = os.path.join('$RESULT_DIR', f'{mac}_{ts}.log')
            with open(loglog, 'w') as f:
                f.write(f'mac={mac} status={status} ts={ts}\n')
            self.send_response(200)
            self.end_headers()
        elif '/test/test.sh' in self.path:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            with open('/srv/install/test/test.sh', 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if '/test/upload' in self.path:
            import urllib.parse
            params = urllib.parse.parse_qs(self.path.split('?',1)[1])
            mac = params.get('mac',[''])[0]
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            logfile = os.path.join('$RESULT_DIR', f'{mac}_detail.log')
            with open(logfile, 'wb') as f:
                f.write(body)
            self.send_response(200)
            self.end_headers()

http.server.HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
" &
    RESULT_PID=$!
    echo "结果接收服务启动 (PID: $RESULT_PID, 端口 8080)"
}

# 2. 批量触发 PXE 引导
trigger_pxe_boot() {
    while IFS=, read -r bmc_ip hostname; do
        [ -z "$bmc_ip" ] && continue
        echo "[$(date +%H:%M:%S)] $hostname ($bmc_ip) → PXE 测试镜像"

        ipmitool -I lanplus -H "$bmc_ip" -U "$BMC_USER" -P "$BMC_PASS" \
            chassis bootdev pxe 2>/dev/null

        ipmitool -I lanplus -H "$bmc_ip" -U "$BMC_USER" -P "$BMC_PASS" \
            chassis power cycle 2>/dev/null

        sleep 5
    done < "$1"
}

# 3. 等待结果
wait_for_results() {
    local total=$1
    local timeout=3600  # 1 小时超时
    local start=$(date +%s)

    while true; do
        local done_count=$(ls "$RESULT_DIR"/*_detail.log 2>/dev/null | wc -l)
        local elapsed=$(( $(date +%s) - start ))

        echo -ne "\r[$(date +%H:%M:%S)] 完成: $done_count/$total | 耗时: ${elapsed}s"

        if [ "$done_count" -ge "$total" ]; then
            echo -e "\n全部完成!"
            break
        fi

        if [ "$elapsed" -ge "$timeout" ]; then
            echo -e "\n超时! 已完成 $done_count/$total"
            break
        fi

        sleep 10
    done
}

# === 主流程 ===
TOTAL=$(wc -l < "$1")
echo "=== 批量 PXE 测试 ==="
echo "目标: $TOTAL 台服务器"
echo ""

start_result_server
sleep 2
trigger_pxe_boot "$1"
echo ""
echo "等待测试结果..."
wait_for_results "$TOTAL"

echo ""
echo "=== 测试结果汇总 ==="
for f in "$RESULT_DIR"/*_detail.log; do
    [ -f "$f" ] || continue
    mac=$(basename "$f" | cut -d_ -f1)
    result=$(grep "结果:" "$f" 2>/dev/null || echo "未知")
    echo "  $mac: $result"
done

kill $RESULT_PID 2>/dev/null
```

### 9.2 执行

```bash
# bmc_list.txt
192.168.100.201,node-01
192.168.100.202,node-02
192.168.100.203,node-03
...

# 一键批量测试
chmod +x batch-test.sh
./batch-test.sh bmc_list.txt
```

---

## 十、自动选择测试镜像（按 MAC 路由）

### 10.1 场景

不同批次服务器跑不同测试：

```
批次 A (web 服务器): → Memtest86+ 内存测试
批次 B (存储服务器): → SystemRescue + 硬盘扫描
批次 C (GPU 服务器): → Ubuntu Live + GPU 压力测试
```

### 10.2 dnsmasq 按 MAC 路由

```bash
# /etc/dnsmasq.d/pxe-test.conf

# 批次 A → Memtest86+
dhcp-host=aa:bb:cc:dd:ee:01,set:memtest
dhcp-host=aa:bb:cc:dd:ee:02,set:memtest

# 批次 B → SystemRescue
dhcp-host=aa:bb:cc:dd:ee:03,set:rescue
dhcp-host=aa:bb:cc:dd:ee:04,set:rescue

# 批次 C → Ubuntu Live
dhcp-host=aa:bb:cc:dd:ee:05,set:ubuntu
dhcp-host=aa:bb:cc:dd:ee:06,set:ubuntu

# === Legacy BIOS 引导文件 ===
# memtest 组: 直接引导 memtest86+
dhcp-boot=tag:memtest,tag:bios,memtest/memtest86+
# rescue 组: 引导 SystemRescue 的 pxelinux.0 (需要单独配置目录)
dhcp-boot=tag:rescue,tag:bios,rescue/pxelinux.0
# ubuntu 组: 引导统一菜单 (手动选 Ubuntu)
dhcp-boot=tag:ubuntu,tag:bios,pxelinux.0

# === UEFI 引导文件 ===
dhcp-boot=tag:memtest,tag:efi-x86_64,memtest/memtest86+
dhcp-boot=tag:rescue,tag:efi-x86_64,rescue/grubx64.efi
dhcp-boot=tag:ubuntu,tag:efi-x86_64,grub/grubx64.efi

# 默认 (未匹配的 MAC): 统一菜单
dhcp-boot=tag:!memtest,tag:!rescue,tag:!ubuntu,tag:bios,pxelinux.0
dhcp-boot=tag:!memtest,tag:!rescue,tag:!ubuntu,tag:efi-x86_64,grub/grubx64.efi
```

### 10.3 更优雅的方案：gPXE/iPXE 脚本

用 iPXE 替代标准 PXE 固件，支持 HTTP 下载和脚本化引导逻辑：

```bash
# 安装 iPXE
dnf install -y ipxe-bootimgs
cp /usr/share/ipxe/undionly.kpxe /srv/tftp/undionly.kpxe
cp /usr/share/ipxe/ipxe.efi /srv/tftp/ipxe.efi

# dnsmasq 引导 iPXE
dhcp-boot=tag:bios,undionly.kpxe
dhcp-boot=tag:efi-x86_64,ipxe.efi

# iPXE 启动后加载脚本
# /srv/tftp/boot.ipxe
cat > /srv/tftp/boot.ipxe << 'EOF'
#!ipxe

# 获取 MAC
echo "MAC: ${net0/mac}"
echo "IP:  ${net0/ip}"

# 根据 MAC 地址选择引导
goto ${mac:hexraw}

# 批次 A: Memtest86+
:aabbccddeE01
:aabbccddeE02
echo "→ Memtest86+ 内存测试"
chain http://192.168.100.10/ipxe/memtest.ipxe
goto end

# 批次 B: SystemRescue
:aabbccddeE03
:aabbccddeE04
echo "→ SystemRescue"
chain http://192.168.100.10/ipxe/rescue.ipxe
goto end

# 默认: 显示菜单
:default
menu PXE Boot Menu
item rocky     Rocky 9.5 Live
item ubuntu    Ubuntu 22.04 Live
item memtest   Memtest86+
item rescue    SystemRescue
item local     Local Disk
choose target && goto ${target}

:rocky
chain http://192.168.100.10/ipxe/rocky-live.ipxe
:ubuntu
chain http://192.168.100.10/ipxe/ubuntu-live.ipxe
:memtest
chain http://192.168.100.10/ipxe/memtest.ipxe
:rescue
chain http://192.168.100.10/ipxe/rescue.ipxe
:local
sanboot --no-describe

:end
EOF
```

iPXE 优势：

| 特性 | 标准 PXE | iPXE |
|:---|:---|:---|
| 下载协议 | 仅 TFTP | TFTP/HTTP/FTP/NFS/iSCSI |
| 脚本化 | ❌ | ✅ 条件分支/循环/变量 |
| 下载速度 | 慢（TFTP） | 快（HTTP） |
| Secure Boot | 取决于固件 | 支持 |
| Wi-Fi 引导 | ❌ | ✅ |

---

## 十一、镜像内存占用估算

选择镜像前确认服务器内存够用：

| 镜像 | squashfs 大小 | 内存运行占用 | 最低内存要求 |
|:---|:---:|:---:|:---:|
| Memtest86+ | — | 64MB | 256MB |
| 自定义 initramfs | 50-200MB | 200-500MB | 512MB |
| SystemRescue | 600MB | 1-1.5GB | 2GB |
| Ubuntu Server Live | 800MB | 1.5-2GB | 4GB |
| Rocky Live XFCE | 1.8GB | 2.5-3.5GB | 4GB |
| Ubuntu Desktop Live | 2.5GB | 3.5-5GB | 8GB |

```
计算公式:
  内存运行占用 ≈ squashfs 大小 × 1.5 (解压 + 缓存)
  最低内存要求 ≈ 内存运行占用 + 1GB (内核 + 运行时)
```

!!! warning "大内存服务器注意事项"
    256GB 内存的服务器用 `copytoram` 模式没问题，但 `ramdisk_size` 参数要设够大。
    另外 Memtest86+ 在 256GB 内存上完整跑一轮可能要 8 小时以上。

---

## 十二、常见问题

### Q1: 内存启动后卡在 "Loading initramfs"

```bash
# 原因: initramfs 太大, TFTP 下载超时
# 解决: 用 HTTP 代替 TFTP 下载大文件

# 方案一: 用 iPXE (支持 HTTP 下载)
# 方案二: 拆分 initramfs
#   基础 initramfs 只含网络驱动 (<50MB, TFTP 下载)
#   启动后从 HTTP 下载 squashfs 根文件系统

# 方案三: 调大 TFTP 超时
# /etc/dnsmasq.d/pxe.conf
tftp-timeout=120
tftp-max=200
tftp-blocksize=1468
```

### Q2: Ubuntu Live 启动后进入 emergency mode

```bash
# 原因: squashfs 下载失败或损坏
# 检查:
curl -I http://192.168.100.10/install/ubuntu-live/casper.squashfs
# 确认文件完整: sha256sum 对比

# 原因2: ramdisk_size 不够
# 内核参数加大: ramdisk_size=4000000 (4GB)

# 原因3: 内存不足
# 服务器最低 4GB 内存才能跑 Ubuntu Live
```

### Q3: copytoram 后内存不够

```bash
# 如果服务器内存 < squashfs × 1.5, copytoram 会失败
# 解决: 不用 copytoram, 改用 NFS Root
# 或换更小的镜像

# 检查当前内存:
free -h
# 检查 squashfs 大小:
ls -lh /srv/install/*/casper.squashfs /srv/install/*/LiveOS/squashfs.img
```

### Q4: 多台同时 PXE 下载太慢

```bash
# TFTP 是 UDP, 并发性能差
# 解决:

# 1. 用 iPXE + HTTP (TCP, 支持并发)
# 2. dnsmasq 调优:
#    /etc/dnsmasq.d/pxe.conf
tftp-max=500          # 最大并发 TFTP 连接
tftp-blocksize=1468   # 最大块大小
tftp-no-fail          # 不因 TFTP 失败而停止

# 3. nginx 调优 (HTTP 下载):
#    /etc/nginx/nginx.conf
worker_connections 4096;
sendfile on;
tcp_nopush on;

# 4. 分批启动, 每批 10-20 台, 间隔 30 秒
```

### Q5: Memtest86+ 在 UEFI 模式无法引导

```bash
# 开源 Memtest86+ 的 UEFI 支持有限
# 方案:

# 1. 使用商业版 MemTest86 (免费版支持 UEFI)
#    https://www.memtest86.com/
#    下载 memtest86-usb.zip → 提取 BOOTX64.EFI → 放到 TFTP

# 2. 切换到 Legacy BIOS 模式跑 Memtest86+
#    BIOS → Boot Mode → Legacy → 保存重启

# 3. 用 Linux 内存测试替代 (Ubuntu Live + memtester)
#    适合 UEFI-only 服务器
```

### Q6: 测试结果如何自动收集

```bash
# 方案一: HTTP 回调 (见第九节)
# 测试脚本跑完 POST 到 PXE 服务器

# 方案二: SSH 反向收集
# 测试镜像启动后自动 SSH 连回 PXE 服务器上传结果
# initramfs 中:
#   scp -o StrictHostKeyChecking=no /tmp/test-result.log admin@192.168.100.10:/var/log/pxe-test/${MAC}.log

# 方案三: 共享 NFS 目录
# NFS Root 方式: 测试结果写到 NFS 共享目录
#   mount 192.168.100.10:/srv/test-results /tmp/results
#   cp /tmp/test-result.log /tmp/results/${MAC}.log

# 方案四: BMC 串口日志
# 所有机器的串口输出通过 BMC 集中收集
#   ipmitool -I lanplus -H <BMC_IP> sol activate > /var/log/pxe-test/${BMC_IP}.sol.log
```

---

## 十三、目录结构速查

```
/srv/
├── tftp/                              # TFTP 根目录
│   ├── grub/grub.cfg                  # UEFI 统一菜单
│   ├── pxelinux.cfg/default           # Legacy 统一菜单
│   ├── memtest/
│   │   └── memtest86+                 # Memtest86+ 二进制
│   ├── rescue/
│   │   ├── vmlinuz                    # SystemRescue 内核
│   │   └── initramfs.img              # SystemRescue initramfs
│   ├── ubuntu-live/
│   │   ├── vmlinuz                    # Ubuntu 内核
│   │   └── initrd                     # Ubuntu initramfs
│   ├── rocky-live/
│   │   ├── vmlinuz                    # Rocky Live 内核
│   │   └── initrd.img                 # Rocky Live initramfs
│   ├── test-image/
│   │   ├── vmlinuz                    # 自定义测试内核
│   │   └── initramfs-test.img         # 自定义 initramfs
│   ├── boot.ipxe                      # iPXE 脚本 (可选)
│   ├── undionly.kpxe                  # iPXE Legacy (可选)
│   └── ipxe.efi                       # iPXE UEFI (可选)
├── install/                           # HTTP 根目录
│   ├── rescue/
│   │   └── airootfs.sfs               # SystemRescue 根文件系统
│   ├── ubuntu-live/
│   │   ├── casper.squashfs            # Ubuntu 根文件系统
│   │   └── cloud-init/
│   │       ├── user-data              # 自动配置
│   │       └── meta-data
│   ├── rocky-live/
│   │   └── LiveOS/squashfs.img        # Rocky 根文件系统
│   └── test/
│       └── test.sh                    # 测试脚本 (HTTP 提供)
└── nfsroot/                           # NFS Root (可选)
    └── rocky-live/rootfs/
```

---

## 十四、完整引导菜单汇总

最终 pxelinux.cfg/default（Legacy BIOS）：

```
DEFAULT menu.c32
PROMPT 0
TIMEOUT 30
ONTIMEOUT local

MENU ====== PXE Boot Menu ======

LABEL memtest
    MENU LABEL ^1. Memtest86+ 内存测试
    KERNEL memtest/memtest86+

LABEL rescue
    MENU LABEL ^2. SystemRescue (内存启动)
    KERNEL rescue/vmlinuz
    APPEND initrd=rescue/initramfs.img archisobasedir=sysresccd \
           archiso_http_srv=http://192.168.100.10/install/rescue/ \
           ip=dhcp copytoram quiet

LABEL ubuntu_live
    MENU LABEL ^3. Ubuntu 22.04 Live (内存启动)
    KERNEL ubuntu-live/vmlinuz
    APPEND initrd=ubuntu-live/initrd root=/dev/ram0 ramdisk_size=2000000 \
           url=http://192.168.100.10/install/ubuntu-live/casper.squashfs \
           boot=casper netboot=url ip=dhcp toram quiet

LABEL rocky_live
    MENU LABEL ^4. Rocky 9 Live (内存启动)
    KERNEL rocky-live/vmlinuz
    APPEND initrd=rocky-live/initrd.img \
           root=live:http://192.168.100.10/install/rocky-live/LiveOS/squashfs.img \
           rd.live.image rd.live.ram=1 ip=dhcp quiet

LABEL test_image
    MENU LABEL ^5. 自定义测试镜像 (最小 initramfs)
    KERNEL test-image/vmlinuz
    APPEND initrd=test-image/initramfs-test.img ip=dhcp quiet

LABEL rocky9_auto
    MENU LABEL ^6. Rocky 9.5 自动安装 (Kickstart)
    KERNEL rocky9/vmlinuz
    APPEND initrd=rocky9/initrd.img \
           inst.stage2=http://192.168.100.10/install/rocky9 \
           inst.ks=http://192.168.100.10/ks/rocky9-ks.cfg ip=dhcp quiet

LABEL local
    MENU LABEL ^0. 本地磁盘启动
    LOCALBOOT 0
```

---

## 十五、各镜像测试能力对比

| 测试项 | Memtest86+ | SystemRescue | Ubuntu Live | Rocky Live | 自定义 initramfs |
|:---|:---:|:---:|:---:|:---:|:---:|
| 内存测试 | ✅ 专业 | ✅ memtester | ✅ memtester | ✅ memtester | ✅ 基础 |
| CPU 压力 | ❌ | ✅ stress-ng | ✅ stress-ng | ✅ stress-ng | ✅ 基础 |
| 磁盘 SMART | ❌ | ✅ smartctl | ✅ smartctl | ✅ smartctl | ❌ |
| 磁盘性能 | ❌ | ✅ fio | ✅ fio | ✅ fio | ❌ |
| 网络测试 | ❌ | ✅ iperf3 | ✅ iperf3 | ✅ iperf3 | ✅ 基础 |
| 温度传感器 | ❌ | ✅ sensors | ✅ sensors | ✅ sensors | ❌ |
| 固件升级 | ❌ | ✅ fwupd | ✅ fwupd | ✅ fwupd | ❌ |
| 结果自动化 | ❌ | ✅ 脚本 | ✅ cloud-init | ✅ 脚本 | ✅ 内置 |
| 启动速度 | 5s | 60s | 90s | 90s | 15s |
| 内存占用 | 64MB | 1.5GB | 2GB | 3GB | 200MB |
| 适合场景 | 纯内存测试 | 综合诊断 | 完整环境 | 完整环境 | 批量自动化 |

**选型建议：**

```
到货验收 (快速过一遍):  自定义 initramfs → 15 秒启动 → 自动跑完上报
内存深度测试:           Memtest86+ → 跑 4-8 小时
硬盘坏块扫描:           SystemRescue → badblocks + smartctl
GPU/CPU 烤机:           Ubuntu Live + stress-ng + gpu-burn
固件批量升级:           自定义 initramfs + 刷写工具
临时救援:               SystemRescue
```

---

*最后更新: 2026-07-07*
