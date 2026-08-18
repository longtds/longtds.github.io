# 定制 Linux 测试镜像（内置测试工具 + 物理驱动）

> 到货 50 台服务器要跑全套硬件测试，但官方 Live 镜像缺 RAID 卡驱动、没有测试工具、GPU 驱动也不对。自己定制一个镜像：内置 stress-ng/fio/memtester/smartmontools，注入 MegaRAID storcli、Mellanox OFED、NVIDIA CUDA 驱动，PXE 引导直接开测。

---

## 一、方案选型

### 1.1 为什么需要定制镜像

| 问题 | 官方 Live 镜像 | 定制镜像 |
|:---|:---|:---|
| RAID 卡驱动 | 可能缺失，看不到磁盘 | ✅ 预装 storcli + megaraid_sas |
| GPU 驱动 | 无 NVIDIA 驱动 | ✅ 预装 nvidia.ko + CUDA |
| 网卡驱动 | 通用驱动，性能差 | ✅ 注入 Mellanox OFED |
| 测试工具 | 需要联网安装 | ✅ 离线内置全套 |
| BMC/IPMI | 基础 ipmitool | ✅ 完整 ipmitool + 厂商工具 |
| NVMe | 基础 nvme-cli | ✅ nvme-cli + 厂商工具 |
| 启动速度 | 1-3 分钟 | ✅ 可精简到 30 秒 |
| 离线运行 | 需联网装包 | ✅ 全部离线可用 |

### 1.2 三种定制方式对比

| 方式 | 工具 | 难度 | 灵活度 | 适合场景 |
|:---|:---|:---:|:---:|:---|
| LiveOS 定制 | livemedia-creator (Rocky) / live-build (Ubuntu) | 中 | 高 | 完整环境 + 包管理 |
| initramfs 手搓 | BusyBox + 手动打包 | 高 | 极高 | 极简/嵌入式/特殊驱动 |
| Kickstart 生成 ISO | livemedia-creator + ks | 低 | 中 | 标准发行版 + 额外包 |

**本文采用方式一（LiveOS 定制）+ 方式二（initramfs 手搓）结合：**

```
方案: 基于 Rocky 9 LiveOS + 注入驱动 + 内置测试工具 + 打包 ISO/PXE

构建流程:
  ┌──────────────┐
  │ Rocky 9 基础  │ ← dnf --installroot 安装最小系统
  └──────┬───────┘
         │
  ┌──────▼───────┐
  │ 注入测试工具  │ ← stress-ng fio memtester smartmontools iperf3 ...
  └──────┬───────┘
         │
  ┌──────▼───────┐
  │ 注入物理驱动  │ ← storcli OFED nvidia ipmitool nvme-cli ...
  └──────┬───────┘
         │
  ┌──────▼───────┐
  │ 配置自启动    │ ← systemd 服务: 自动跑测试脚本
  └──────┬───────┘
         │
  ┌──────▼───────┐
  │ 打包 squashfs │ ← mksquashfs 压缩根文件系统
  └──────┬───────┘
         │
  ┌──────▼───────┐
  │ 生成 ISO/PXE │ ← xorriso / 复制到 TFTP
  └──────────────┘
```

### 1.3 构建环境要求

```
构建服务器:
  - OS: Rocky Linux 9 / CentOS Stream 9 / RHEL 9
  - 内存: ≥ 8GB
  - 磁盘: ≥ 20GB 空闲
  - 网络: 可访问 dnf 源 (官方 + EPEL)
  - 工具: dnf, mksquashfs, xorriso, dracut
  - 权限: root
```

---

## 二、构建根文件系统

### 2.1 创建构建工作区

```bash
#!/bin/bash
set -euo pipefail

# === 变量 ===
BUILD_DIR="/srv/image-build"
ROOTFS="$BUILD_DIR/rootfs"
ROCKY_VER="9"
MIRROR="https://mirrors.aliyun.com/rockylinux/$ROCKY_VER/BaseOS/x86_64/os/"
EPEL_MIRROR="https://mirrors.aliyun.com/epel/$ROCKY_VER/Everything/x86_64/"
APPSTREAM_MIRROR="https://mirrors.aliyun.com/rockylinux/$ROCKY_VER/AppStream/x86_64/os/"
IMG_NAME="hwtest-live"
IMG_VERSION="1.0"
IMG_DATE=$(date +%Y%m%d)

# === 清理 + 创建目录 ===
rm -rf "$BUILD_DIR"
mkdir -p "$ROOTFS" "$BUILD_DIR/output"
```

### 2.2 用 dnf 安装基础系统

```bash
# 安装基础包到 rootfs (不依赖构建机的包管理器状态)
dnf install -y --installroot="$ROOTFS" \
    --releasever="$ROCKY_VER" \
    --repofrompath="baseos,$MIRROR" \
    --repofrompath="appstream,$APPSTREAM_MIRROR" \
    --repofrompath="epel,$EPEL_MIRROR" \
    --nodocs --nogpgcheck \
    @core \
    bash-completion \
    vim \
    less \
    which \
    file \
    tree \
    pciutils \
    usbutils \
    net-tools \
    bind-utils \
    iproute \
    ethtool \
    tcpdump \
    wget \
    curl \
    rsync \
    tmux \
    openssh-server \
    openssh-clients \
    NetworkManager \
    chrony \
    epel-release \
    kernel \
    kernel-modules \
    kernel-modules-extra

# 挂载虚拟文件系统 (chroot 需要)
mount --bind /dev "$ROOTFS/dev"
mount --bind /proc "$ROOTFS/proc"
mount --bind /sys "$ROOTFS/sys"
mount --bind /run "$ROOTFS/run"

# 复制 DNS 配置
cp /etc/resolv.conf "$ROOTFS/etc/resolv.conf"
```

### 2.3 chroot 内配置基础环境

```bash
chroot "$ROOTFS" << 'CHROOT_EOF'
set -euo pipefail

# 设置时区
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# 语言
echo "LANG=zh_CN.UTF-8" > /etc/locale.conf
localedef -i zh_CN -f UTF-8 zh_CN.UTF-8 2>/dev/null || true

# 主机名
echo "hwtest-node" > /etc/hostname

# 网络 (DHCP)
cat > /etc/NetworkManager/system-connections/eth0.nmconnection << 'EOF'
[connection]
id=eth0
type=ethernet
autoconnect=true

[ipv4]
method=auto

[ipv6]
method=ignore
EOF
chmod 600 /etc/NetworkManager/system-connections/eth0.nmconnection

# SSH 配置 (允许密码登录, 测试阶段方便)
sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# 设置 root 密码
echo 'root:hwtest123' | chpasswd

# 启用服务
systemctl enable sshd
systemctl enable NetworkManager
systemctl enable chronyd

# dnf 配置 (镜像源)
cat > /etc/yum.repos.d/rocky.repo << 'EOF'
[baseos]
name=Rocky Linux 9 - BaseOS
baseurl=https://mirrors.aliyun.com/rockylinux/9/BaseOS/x86_64/os/
gpgcheck=0
enabled=1

[appstream]
name=Rocky Linux 9 - AppStream
baseurl=https://mirrors.aliyun.com/rockylinux/9/AppStream/x86_64/os/
gpgcheck=0
enabled=1

[epel]
name=EPEL 9
baseurl=https://mirrors.aliyun.com/epel/9/Everything/x86_64/
gpgcheck=0
enabled=1
EOF

CHROOT_EOF
```

---

## 三、注入测试工具

### 3.1 系统级测试工具

```bash
chroot "$ROOTFS" << 'CHROOT_EOF'
set -euo pipefail

# === CPU/内存/系统压力测试 ===
dnf install -y \
    stress-ng \
    memtester \
    mprime \
    sysbench \
    lm-sensors \
    dmidecode \
    lshw \
    hwloc \
    hwloc-gui \
    numactl \
    numactl-devel

# === 磁盘测试 ===
dnf install -y \
    fio \
    smartmontools \
    hdparm \
    nvme-cli \
    sg3-utils \
    lsscsi \
    blktrace

# === 网络测试 ===
dnf install -y \
    iperf3 \
    mtr \
    fping \
    nmap-ncat \
    socat \
    net-snmp-utils \
    tcpdump \
    wireshark-cli

# === GPU 测试 (NVIDIA) ===
dnf install -y \
    mesa-dri-drivers \
    glx-utils \
    opencl-headers

# === 基础开发工具 (编译驱动需要) ===
dnf install -y \
    gcc \
    make \
    kernel-devel \
    kernel-headers \
    dkms \
    elfutils-libelf-devel

# === Python (测试脚本运行环境) ===
dnf install -y \
    python3 \
    python3-pip \
    python3-devel

# === 文件系统工具 ===
dnf install -y \
    xfsprogs \
    e2fsprogs \
    btrfs-progs \
    nfs-utils \
    cifs-utils

# === 监控/日志 ===
dnf install -y \
    sysstat \
    dstat \
    iotop \
    iftop \
    nmon \
    atop \
    collectl

# === 其他实用工具 ===
dnf install -y \
    jq \
    parallel \
    expect \
    screen \
    socat \
    rsyslog

# 清理缓存
dnf clean all
rm -rf /var/cache/dnf

CHROOT_EOF
```

### 3.2 安装 Python 测试框架

```bash
chroot "$ROOTFS" << 'CHROOT_EOF'
set -euo pipefail

# 安装 Python 测试相关包
pip3 install --no-cache-dir \
    pytest \
    requests \
    paramiko \
    pyyaml \
    jinja2 \
    rich \
    tabulate

CHROOT_EOF
```

### 3.3 自建测试脚本框架

```bash
mkdir -p "$ROOTFS/opt/hwtest"/{bin,conf,results,logs}

# 测试主控脚本
cat > "$ROOTFS/opt/hwtest/bin/hwtest" << 'EOF'
#!/bin/bash
# ============================================
# hwtest — 服务器硬件测试主控脚本
# 用法:
#   hwtest run all          # 跑全部测试
#   hwtest run cpu          # 只跑 CPU
#   hwtest run memory       # 只跑内存
#   hwtest run disk         # 只跑磁盘
#   hwtest run network      # 只跑网络
#   hwtest report           # 生成报告
# ============================================

set -euo pipefail

HWTEST_HOME="/opt/hwtest"
HWTEST_CONF="$HWTEST_HOME/conf/hwtest.conf"
HWTEST_RESULTS="$HWTEST_HOME/results"
HWTEST_LOGS="$HWTEST_HOME/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_DIR="$HWTEST_RESULTS/$TIMESTAMP"

mkdir -p "$RESULT_DIR" "$HWTEST_LOGS"

# 加载配置
source "$HWTEST_CONF" 2>/dev/null || true

log() { echo "[$(date '+%H:%M:%S')] $*"; }
pass() { echo "  ✅ PASS: $1"; echo "PASS: $1" >> "$RESULT_DIR/summary.txt"; }
fail() { echo "  ❌ FAIL: $1: $2"; echo "FAIL: $1 ($2)" >> "$RESULT_DIR/summary.txt"; }

# === 系统信息收集 ===
collect_info() {
    log "收集系统信息..."
    {
        echo "===== 硬件测试报告 ====="
        echo "时间: $(date)"
        echo "主机名: $(hostname)"
        echo ""
        echo "--- 系统 ---"
        cat /etc/os-release | grep PRETTY_NAME
        uname -r
        echo ""
        echo "--- CPU ---"
        lscpu
        echo ""
        echo "--- 内存 ---"
        free -h
        dmidecode -t memory 2>/dev/null | grep -E "Size|Speed|Type|Manufacturer|Serial" | grep -v "No Module\|Unknown"
        echo ""
        echo "--- 主板 ---"
        dmidecode -t baseboard 2>/dev/null | grep -E "Manufacturer|Product|Serial"
        echo ""
        echo "--- 磁盘 ---"
        lsblk -o NAME,SIZE,TYPE,MODEL,SERIAL
        echo ""
        echo "--- 网卡 ---"
        ip -o link show | awk '{print $2, $3}'
        lspci | grep -i ethernet
        echo ""
        echo "--- GPU ---"
        lspci | grep -i -E "vga|3d|display"
        echo ""
        echo "--- RAID 卡 ---"
        lspci | grep -i raid
        which storcli64 >/dev/null 2>&1 && storcli64 /c0 show 2>/dev/null || echo "storcli 未安装"
        echo ""
        echo "--- BMC ---"
        ip addr show | grep -A2 -i bmc || true
        which ipmitool >/dev/null 2>&1 && ipmitool mc info 2>/dev/null || echo "ipmitool 不可用"
    } > "$RESULT_DIR/system-info.txt"
    log "系统信息已保存"
}

# === CPU 测试 ===
test_cpu() {
    log "=== CPU 测试 ==="
    local cores=$(nproc)
    local duration="${CPU_TEST_DURATION:-300}"

    # 1. stress-ng 多维度压力
    log "  stress-ng CPU 压力 (${duration}s, ${cores} 核)..."
    if stress-ng --cpu "$cores" --timeout "${duration}s" --metrics-brief \
            > "$RESULT_DIR/cpu-stress.log" 2>&1; then
        pass "CPU stress-ng (${cores}核 ${duration}s)"
    else
        fail "CPU stress-ng" "退出码 $?"
    fi

    # 2. CPU 浮点测试
    log "  stress-ng 浮点测试..."
    if stress-ng --cpu "$cores" --cpu-method float80 --timeout 60s --metrics-brief \
            >> "$RESULT_DIR/cpu-stress.log" 2>&1; then
        pass "CPU 浮点测试"
    else
        fail "CPU 浮点测试" "退出码 $?"
    fi

    # 3. sysbench CPU
    if which sysbench >/dev/null 2>&1; then
        log "  sysbench CPU 测试..."
        if sysbench cpu --threads="$cores" --time=60 run \
                > "$RESULT_DIR/cpu-sysbench.log" 2>&1; then
            pass "CPU sysbench"
        else
            fail "CPU sysbench" "退出码 $?"
        fi
    fi
}

# === 内存测试 ===
test_memory() {
    log "=== 内存测试 ==="
    local total_mem_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    # 测试可用内存的 75% (留余量给系统)
    local test_mem_kb=$((total_mem_kb * 3 / 4))
    local test_mem_mb=$((test_mem_kb / 1024))

    # 1. memtester
    log "  memtester (${test_mem_mb}MB, 3 循环)..."
    if memtester "${test_mem_mb}M" 3 > "$RESULT_DIR/memtester.log" 2>&1; then
        pass "内存 memtester (${test_mem_mb}MB)"
    else
        fail "内存 memtester" "见 memtester.log"
    fi

    # 2. stress-ng 内存
    log "  stress-ng vm 压力..."
    if stress-ng --vm 2 --vm-bytes "${test_mem_mb}M" --timeout 120s --metrics-brief \
            > "$RESULT_DIR/mem-stress.log" 2>&1; then
        pass "内存 stress-ng vm"
    else
        fail "内存 stress-ng vm" "退出码 $?"
    fi
}

# === 磁盘测试 ===
test_disk() {
    log "=== 磁盘测试 ==="

    # 收集所有块设备
    local disks=$(lsblk -d -n -o NAME | grep -E '^sd|^nvme' | sort)

    for disk in $disks; do
        local dev="/dev/$disk"
        log "  --- $dev ---"

        # 1. SMART 健康检查
        if smartctl -a "$dev" > "$RESULT_DIR/disk-${disk}-smart.txt" 2>&1; then
            local health=$(smartctl -H "$dev" | awk '/result/{print $NF}')
            [ "$health" = "PASSED" ] && pass "磁盘 $disk SMART" || fail "磁盘 $disk SMART" "$health"
        else
            log "    $disk 不支持 SMART (可能是 NVMe 或 RAID 虚拟盘)"
        fi

        # 2. 顺序读写 (不破坏数据, 只读测试)
        log "    fio 顺序读测试..."
        if fio --name=seq-read --rw=read --bs=1M --size=1G --numjobs=1 \
                --runtime=30 --time_based --direct=1 \
                --filename="$dev" --group_reporting \
                > "$RESULT_DIR/disk-${disk}-fio-seq-read.json" 2>&1; then
            local iops=$(jq -r '.jobs[0].read.iops' "$RESULT_DIR/disk-${disk}-fio-seq-read.json" 2>/dev/null || echo "N/A")
            local bw=$(jq -r '.jobs[0].read.bw' "$RESULT_DIR/disk-${disk}-fio-seq-read.json" 2>/dev/null || echo "N/A")
            pass "磁盘 $disk 顺序读 (${bw}KB/s, ${iops} IOPS)"
        else
            fail "磁盘 $disk fio 顺序读" "退出码 $?"
        fi

        # 3. 随机读写 (在临时文件上, 不破坏原数据)
        log "    fio 随机读写测试..."
        if fio --name=rand-rw --rw=randrw --bs=4k --size=512M --numjobs=4 \
                --runtime=30 --time_based --direct=1 \
                --filename="/tmp/fio-test-${disk}" --group_reporting \
                --output-format=json \
                > "$RESULT_DIR/disk-${disk}-fio-rand-rw.json" 2>&1; then
            local iops=$(jq -r '.jobs[0].read.iops' "$RESULT_DIR/disk-${disk}-fio-rand-rw.json" 2>/dev/null || echo "N/A")
            pass "磁盘 $disk 随机读写 (${iops} IOPS)"
        else
            fail "磁盘 $disk fio 随机读写" "退出码 $?"
        fi
        rm -f "/tmp/fio-test-${disk}"
    done
}

# === 网络测试 ===
test_network() {
    log "=== 网络测试 ==="

    # 1. 网卡链路状态
    for iface in $(ip -o link show | awk -F': ' '{print $2}' | grep -E '^eth|^ens|^enp' | grep -v lo); do
        log "  --- $iface ---"
        local speed=$(ethtool "$iface" 2>/dev/null | grep Speed | awk '{print $2}')
        local link=$(ethtool "$iface" 2>/dev/null | grep "Link detected" | awk '{print $3}')
        echo "$iface: speed=$speed link=$link" >> "$RESULT_DIR/network-info.txt"

        if [ "$link" = "yes" ]; then
            pass "网卡 $iface 链路 (${speed})"
        else
            fail "网卡 $iface 链路" "未连接"
        fi
    done

    # 2. 网络连通性
    local gateway=$(ip route | grep default | awk '{print $3}' | head -1)
    if [ -n "$gateway" ]; then
        if ping -c 10 "$gateway" > "$RESULT_DIR/ping-gateway.log" 2>&1; then
            local loss=$(grep "packet loss" "$RESULT_DIR/ping-gateway.log" | grep -oP '\d+(?=%)')
            [ "$loss" = "0" ] && pass "网关连通 (${gateway}, 0% 丢包)" || fail "网关连通" "${loss}% 丢包"
        else
            fail "网关连通" "ping 失败"
        fi
    fi
}

# === GPU 测试 ===
test_gpu() {
    log "=== GPU 测试 ==="

    if ! which nvidia-smi >/dev/null 2>&1; then
        log "  NVIDIA 驱动未安装, 跳过 GPU 测试"
        return 0
    fi

    local gpu_count=$(nvidia-smi --list-gpus | wc -l)
    log "  检测到 ${gpu_count} 个 GPU"

    nvidia-smi > "$RESULT_DIR/gpu-info.txt" 2>&1

    # 1. GPU 基本检测
    if nvidia-smi -L > "$RESULT_DIR/gpu-list.txt" 2>&1; then
        pass "GPU 检测 ($gpu_count 个)"
    else
        fail "GPU 检测" "nvidia-smi 失败"
        return 1
    fi

    # 2. GPU 压力测试 (如果有 gpu-burn)
    if [ -x /opt/gpu-burn/gpu-burn ]; then
        log "  GPU 烤机 (60s)..."
        if /opt/gpu-burn/gpu-burn 60 > "$RESULT_DIR/gpu-burn.log" 2>&1; then
            pass "GPU 烤机"
        else
            fail "GPU 烤机" "见 gpu-burn.log"
        fi
    fi
}

# === 生成报告 ===
generate_report() {
    log "=== 生成报告 ==="
    {
        echo "================================"
        echo "  硬件测试报告"
        echo "  时间: $(date)"
        echo "  主机: $(hostname)"
        echo "================================"
        echo ""

        if [ -f "$RESULT_DIR/summary.txt" ]; then
            echo "--- 测试结果汇总 ---"
            cat "$RESULT_DIR/summary.txt"
            echo ""

            local total=$(wc -l < "$RESULT_DIR/summary.txt")
            local passed=$(grep -c "^PASS" "$RESULT_DIR/summary.txt" 2>/dev/null || echo 0)
            local failed=$(grep -c "^FAIL" "$RESULT_DIR/summary.txt" 2>/dev/null || echo 0)
            echo "总计: $total | 通过: $passed | 失败: $failed"
            echo ""
            if [ "$failed" = "0" ]; then
                echo "🎉 全部通过!"
            else
                echo "⚠️  有 $failed 项失败, 请检查详情"
            fi
        fi
    } > "$RESULT_DIR/report.txt"

    cat "$RESULT_DIR/report.txt"
    log "报告已保存: $RESULT_DIR/report.txt"
}

# === 主入口 ===
case "${1:-}" in
    run)
        collect_info
        case "${2:-all}" in
            cpu)     test_cpu ;;
            memory|mem) test_memory ;;
            disk)    test_disk ;;
            network|net) test_network ;;
            gpu)     test_gpu ;;
            all)
                test_cpu
                test_memory
                test_disk
                test_network
                test_gpu
                ;;
            *) echo "未知测试: $2"; exit 1 ;;
        esac
        generate_report
        ;;
    report)
        generate_report
        ;;
    info)
        collect_info
        cat "$RESULT_DIR/system-info.txt"
        ;;
    *)
        echo "用法: hwtest run [all|cpu|memory|disk|network|gpu]"
        echo "      hwtest report"
        echo "      hwtest info"
        exit 1
        ;;
esac
EOF
chmod +x "$ROOTFS/opt/hwtest/bin/hwtest"

# 配置文件
cat > "$ROOTFS/opt/hwtest/conf/hwtest.conf" << 'EOF'
# 硬件测试配置
CPU_TEST_DURATION=300     # CPU 压力测试时长 (秒)
MEM_TEST_LOOPS=3          # 内存测试循环次数
DISK_FIO_RUNTIME=30       # 磁盘 fio 测试时长 (秒)
PING_COUNT=10             # 网络连通性 ping 次数

# 结果上报 (可选)
# REPORT_SERVER="http://192.168.100.10:8080"
# REPORT_MAC=$(cat /sys/class/net/*/address 2>/dev/null | head -1)
EOF

# 加入 PATH
echo 'export PATH=$PATH:/opt/hwtest/bin' >> "$ROOTFS/etc/profile.d/hwtest.sh"
```

---

## 四、注入物理驱动

### 4.1 RAID 卡驱动（MegaRAID / storcli）

```bash
chroot "$ROOTFS" << 'CHROOT_EOF'
set -euo pipefail

# === MegaRAID 驱动 (内核模块, 通常已含在 kernel-modules 中) ===
# 确认驱动已加载
modinfo megaraid_sas 2>/dev/null && echo "megaraid_sas 已内置" || {
    echo "megaraid_sas 不在标准内核中, 需手动编译"
}

# 其他常见 RAID 卡驱动
modinfo mpt3sas 2>/dev/null && echo "mpt3sas 已内置" || true   # LSI HBA
modinfo hpsa 2>/dev/null && echo "hpsa 已内置" || true          # HPE Smart Array
modinfo aacraid 2>/dev/null && echo "aacraid 已内置" || true    # Adaptec
modinfo arcmsr 2>/dev/null && echo "arcmsr 已内置" || true      # Areca

# === storcli64 (Broadcom/LSI RAID 管理工具) ===
# 需要手动下载: https://www.broadcom.com/products/storage/raid-controllers/megaraid-9560-8i#downloads
# 文件: 007.2708.0000.0000_Unified_StorCLI.zip → storcli_All_OS.zip → storcli64

# 假设已下载到 /tmp/storcli64
if [ -f /tmp/storcli64 ]; then
    install -m 755 /tmp/storcli64 /usr/sbin/storcli64
    ln -sf /usr/sbin/storcli64 /usr/sbin/storcli
    echo "storcli64 已安装"
else
    echo "⚠️ storcli64 未找到, 请手动放入 /tmp/"
    # 可以创建一个占位脚本
    cat > /usr/sbin/storcli64 << 'EOF'
#!/bin/bash
echo "storcli64 未安装。请从 Broadcom 下载并放入镜像中。"
echo "下载: https://www.broadcom.com/products/storage/raid-controllers"
exit 1
EOF
    chmod +x /usr/sbin/storcli64
fi

# === Perccli (Dell PERC RAID 管理工具) ===
# 下载: https://www.dell.com/support/home/ (搜 PERC CLI)
# 文件: perccli_7.5-xxx_Nova_A09_Linux.tar.gz
if [ -f /tmp/perccli64 ]; then
    install -m 755 /tmp/perccli64 /usr/sbin/perccli64
    echo "perccli64 已安装"
fi

# === ssacliu (HPE Smart Array CLI) ===
# 下载: https://support.hpe.com/ (搜 Smart Array Command Line Interface)
if [ -f /tmp/ssacli ]; then
    install -m 755 /tmp/ssacli /usr/sbin/ssacli
    echo "ssacli 已安装"
fi

CHROOT_EOF
```

### 4.2 网卡驱动（Mellanox OFED / Intel / Broadcom）

```bash
chroot "$ROOTFS" << 'CHROOT_EOF'
set -euo pipefail

# === 确认内核已含网卡驱动 ===
# Intel
modinfo ixgbe 2>/dev/null && echo "ixgbe (Intel 10G) 已内置" || true
modinfo i40e 2>/dev/null && echo "i40e (Intel 25G/40G) 已内置" || true
modinfo ice 2>/dev/null && echo "ice (Intel 800G) 已内置" || true
modinfo igb 2>/dev/null && echo "igb (Intel 1G) 已内置" || true

# Broadcom
modinfo tg3 2>/dev/null && echo "tg3 (Broadcom) 已内置" || true
modinfo bnxt_en 2>/dev/null && echo "bnxt_en (Broadcom NetXtreme) 已内置" || true

# Mellanox (基础驱动在内核中, 但 OFED 提供完整用户态工具)
modinfo mlx5_core 2>/dev/null && echo "mlx5_core (Mellanox ConnectX) 已内置" || true
modinfo mlx4_core 2>/dev/null && echo "mlx4_core (Mellanox ConnectX-3) 已内置" || true

# === Mellanox OFED (可选, 完整 RDMA/InfiniBand 支持) ===
# 官方: https://network.nvidia.com/products/infiniband-drivers/linux/mlnx_ofed/
# 下载 MLNX_OFED_LINUX-xx.x.x-rhel9.x-x86_64.iso

# 如果有 OFED ISO:
if [ -f /tmp/MLNX_OFED_LINUX.iso ]; then
    mkdir -p /mnt/ofed
    mount -o loop /tmp/MLNX_OFED_LINUX.iso /mnt/ofed
    /mnt/ofed/mlnxofedinstall --without-dkms --add-kernel-support --force 2>/dev/null || \
        echo "⚠️ OFED 安装失败, 可能需要对应内核版本"
    umount /mnt/ofed
    rmdir /mnt/ofed
    echo "Mellanox OFED 已安装"
else
    echo "ℹ️ 未找到 OFED ISO, 使用内核自带 mlx5_core 驱动"
    # 安装基础 RDMA 工具
    dnf install -y rdma-core libibverbs-utils perftest
fi

# === Mellanox 管理工具 (MFT) ===
# 下载: https://network.nvidia.com/products/adapter-software/firmware-tools/
# 文件: mft-xx.x.x-x86_64-rpm.tgz
if [ -f /tmp/mft-install.sh ]; then
    /tmp/mft-install.sh --force 2>/dev/null || echo "⚠️ MFT 安装失败"
fi

# 网卡固件管理工具
dnf install -y ethtool pciutils lshw

CHROOT_EOF
```

### 4.3 GPU 驱动（NVIDIA）

```bash
# NVIDIA 驱动需要对应内核版本编译, 在 chroot 中安装
chroot "$ROOTFS" << 'CHROOT_EOF'
set -euo pipefail

# === 方法一: RPM Fusion 驱动 (推荐, 自动 DKMS 编译) ===
dnf install -y https://mirrors.aliyun.com/rpmfusion/free/el/rpmfusion-free-release-9.noarch.rpm 2>/dev/null || true
dnf install -y https://mirrors.aliyun.com/rpmfusion/nonfree/el/rpmfusion-nonfree-release-9.noarch.rpm 2>/dev/null || true

# 安装 NVIDIA 驱动 (DKMS, 自动适配内核)
dnf install -y kmod-nvidia xorg-x11-drv-nvidia-cuda 2>/dev/null && {
    echo "NVIDIA 驱动已安装 (RPM Fusion)"
} || {
    echo "⚠️ RPM Fusion 驱动安装失败, 尝试手动安装"

    # === 方法二: 手动安装 .run 驱动 ===
    # 下载: https://www.nvidia.com/Download/index.aspx
    # 文件: NVIDIA-Linux-x86_64-550.xx.run

    if [ -f /tmp/NVIDIA-Linux-x86_64-*.run ]; then
        # 安装依赖
        dnf install -y gcc make kernel-devel kernel-headers dkms \
            elfutils-libelf-devel libglvnd-devel

        # 安装驱动 (静默模式)
        sh /tmp/NVIDIA-Linux-x86_64-*.run --silent --accept-license --no-questions \
            --dkms --install-libglvnd 2>/dev/null && {
            echo "NVIDIA 驱动已安装 (.run)"
        } || {
            echo "⚠️ NVIDIA .run 安装失败"
            echo "可能需要在有对应内核的机器上编译后注入"
        }
    else
        echo "ℹ️ 未找到 NVIDIA 驱动, 跳过 GPU 驱动安装"
    fi
}

# === NVIDIA CUDA Toolkit (可选) ===
# 下载: https://developer.nvidia.com/cuda-downloads
if [ -f /tmp/cuda-repo-rhel9-*.rpm ]; then
    rpm -ivh /tmp/cuda-repo-rhel9-*.rpm
    dnf install -y cuda-toolkit 2>/dev/null || echo "⚠️ CUDA 安装失败"
fi

# === GPU 测试工具: gpu-burn ===
if which nvidia-smi >/dev/null 2>&1 || [ -d /usr/src/nvidia-* ]; then
    mkdir -p /opt/gpu-burn
    cd /opt/gpu-burn
    # 下载 gpu-burn 源码
    curl -sL https://github.com/wilicc/gpu-burn/archive/refs/heads/master.tar.gz | \
        tar xz --strip-components=1 2>/dev/null && {
        # 编译 (需要 NVIDIA 驱动头文件)
        make CUDA_INSTALL_PATH=/usr/local/cuda 2>/dev/null || \
            echo "⚠️ gpu-burn 编译失败 (需要 CUDA)"
    } || echo "ℹ️ gpu-burn 下载失败"
fi

CHROOT_EOF
```

### 4.4 BMC / IPMI 工具

```bash
chroot "$ROOTFS" << 'CHROOT_EOF'
set -euo pipefail

# === ipmitool (通用) ===
dnf install -y ipmitool OpenIPMI OpenIPMI-tools

# 加载 IPMI 内核模块
echo "ipmi_devintf" >> /etc/modules-load.d/ipmi.conf
echo "ipmi_si" >> /etc/modules-load.d/ipmi.conf
echo "ipmi_msghandler" >> /etc/modules-load.d/ipmi.conf

# === 厂商 BMC 工具 (可选) ===

# Lenovo XCC 工具 (OneCli)
# 下载: https://support.lenovo.com/ (搜 OneCLI)
if [ -f /tmp/lnvgy_utl_lxcrs_xxx.tgz ]; then
    mkdir -p /opt/lenovo
    tar xzf /tmp/lnvgy_utl_lxcrs_xxx.tgz -C /opt/lenovo
    ln -sf /opt/lenovo/lnvgy_utl_lxcrs_*/lnvgy_utl_lxcrs /usr/sbin/onecli
    echo "Lenovo OneCLI 已安装"
fi

# Dell 工具
# 下载: https://www.dell.com/support/ (搜 Dell Command | PowerShell)
# dsu (Dell System Update): 用于固件更新
if [ -f /tmp/dell-dsu-installer ]; then
    sh /tmp/dell-dsu-installer 2>/dev/null || echo "⚠️ DSU 安装失败"
fi

# HPE 工具 (SPP - Smart Update Manager)
# 下载: https://support.hpe.com/ (搜 Service Pack for ProLiant)
# SPP 通常以 ISO 形式提供, 可挂载后运行

# 浪潮 BMC 工具
# 通常通过 BMC Web 界面操作, 无独立命令行工具

CHROOT_EOF
```

### 4.5 NVMe 驱动 + 管理工具

```bash
chroot "$ROOTFS" << 'CHROOT_EOF'
set -euo pipefail

# NVMe 驱动 (通常已内置在内核中)
modinfo nvme 2>/dev/null && echo "nvme 已内置" || true
modinfo nvme-core 2>/dev/null && echo "nvme-core 已内置" || true

# NVMe 管理工具
dnf install -y nvme-cli

# 厂商 NVMe 工具 (可选)
# Samsung: samsung-nvme-cli
# Intel/Solidigm: solidigm-nvme-cli
# Western Digital: wd-nvme-cli

# 验证
nvme --version
nvme list 2>/dev/null || echo "(chroot 中无法访问 NVMe 设备, 正常)"

CHROOT_EOF
```

### 4.6 传感器驱动（温度/电压/风扇）

```bash
chroot "$ROOTFS" << 'CHROOT_EOF'
set -euo pipefail

# 硬件监控驱动
modinfo coretemp 2>/dev/null && echo "coretemp (Intel CPU 温度) 已内置" || true
modinfo k10temp 2>/dev/null && echo "k10temp (AMD CPU 温度) 已内置" || true
modinfo drivetemp 2>/dev/null && echo "drivetemp (硬盘温度) 已内置" || true
modinfo nct6775 2>/dev/null && echo "nct6775 (主板传感器) 已内置" || true
modinfo ipmi_si 2>/dev/null && echo "ipmi_si (IPMI 传感器) 已内置" || true

# sensors 工具
dnf install -y lm_sensors
sensors-detect --auto 2>/dev/null || true

# IPMI 传感器
dnf install -y ipmitool freeipmi

CHROOT_EOF
```

---

## 五、配置自启动测试

### 5.1 systemd 服务：开机自动执行测试

```bash
# 自启动测试服务
cat > "$ROOTFS/etc/systemd/system/hwtest-autorun.service" << 'EOF'
[Unit]
Description=Hardware Test Auto-Run
After=network-online.target
Wants=network-online.target
ConditionKernelCommandLine=!hwtest.skip

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 5
ExecStart=/opt/hwtest/bin/hwtest-autorun.sh
StandardOutput=journal+console
StandardError=journal+console
TimeoutStartSec=7200
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# 自启动脚本
cat > "$ROOTFS/opt/hwtest/bin/hwtest-autorun.sh" << 'EOF'
#!/bin/bash
# 开机自动执行硬件测试

set -euo pipefail

LOG=/var/log/hwtest-autorun.log
RESULT_DIR=/opt/hwtest/results
REPORT_SERVER=""  # 留空则不上报, 设为 http://192.168.100.10:8080 则自动上报

exec > >(tee -a "$LOG") 2>&1

echo "========================================"
echo "  硬件测试自动启动"
echo "  时间: $(date)"
echo "  主机: $(hostname)"
echo "========================================"

# 等待网络就绪
echo "[$(date '+%H:%M:%S')] 等待网络..."
for i in $(seq 1 30); do
    if ip route | grep -q default; then
        echo "[$(date '+%H:%M:%S')] 网络就绪"
        break
    fi
    sleep 2
done

# 执行测试
echo "[$(date '+%H:%M:%S')] 开始硬件测试..."
/opt/hwtest/bin/hwtest run all

# 上报结果
if [ -n "$REPORT_SERVER" ]; then
    MAC=$(cat /sys/class/net/*/address 2>/dev/null | head -1)
    LATEST=$(ls -t "$RESULT_DIR" | head -1)

    echo "[$(date '+%H:%M:%S')] 上报结果到 $REPORT_SERVER ..."

    # 上报摘要
    curl -s -X POST \
        "${REPORT_SERVER}/report?mac=${MAC}&hostname=$(hostname)" \
        -F "summary=@${RESULT_DIR}/${LATEST}/summary.txt" \
        -F "system_info=@${RESULT_DIR}/${LATEST}/system-info.txt" \
        -F "report=@${RESULT_DIR}/${LATEST}/report.txt" \
        -F "log=@${LOG}" \
        2>/dev/null && echo "[$(date '+%H:%M:%S')] 上报成功" || \
        echo "[$(date '+%H:%M:%S')] ⚠️ 上报失败"
fi

echo "[$(date '+%H:%M:%S')] 测试完成。"
echo "结果目录: ${RESULT_DIR}/${LATEST:-unknown}"

# 不自动关机 (留给用户检查)
# 如需自动关机, 取消下一行注释:
# poweroff

EOF
chmod +x "$ROOTFS/opt/hwtest/bin/hwtest-autorun.sh"

# 启用自启动
chroot "$ROOTFS" systemctl enable hwtest-autorun.service
```

### 5.2 可选：内核命令行跳过测试

```bash
# 在 PXE 引导菜单中可添加 hwtest.skip 跳过自动测试:
# APPEND ... hwtest.skip
# 这样进入测试环境但不自动跑测试, 方便手动操作
```

### 5.3 登录后提示

```bash
cat > "$ROOTFS/etc/profile.d/hwtest-motd.sh" << 'EOF'
#!/bin/bash
echo ""
echo "╔══════════════════════════════════════╗"
echo "║     硬件测试环境 (hwtest-live)       ║"
echo "╠══════════════════════════════════════╣"
echo "║                                      ║"
echo "║  快速开始:                            ║"
echo "║    hwtest run all     跑全部测试      ║"
echo "║    hwtest run cpu     只跑 CPU        ║"
echo "║    hwtest run memory  只跑内存        ║"
echo "║    hwtest run disk    只跑磁盘        ║"
echo "║    hwtest run network 只跑网络        ║"
echo "║    hwtest run gpu     只跑 GPU        ║"
echo "║    hwtest info        查看硬件信息    ║"
echo "║    hwtest report      生成报告        ║"
echo "║                                      ║"
echo "║  测试结果: /opt/hwtest/results/       ║"
echo "║  日志: /var/log/hwtest-autorun.log    ║"
echo "║                                      ║"
echo "╚══════════════════════════════════════╝"
echo ""
EOF
```

---

## 六、打包 LiveOS 镜像

### 6.1 清理 rootfs

```bash
# 卸载虚拟文件系统
umount "$ROOTFS/dev" "$ROOTFS/proc" "$ROOTFS/sys" "$ROOTFS/run" 2>/dev/null || true

# 清理
chroot "$ROOTFS" dnf clean all 2>/dev/null || true
rm -rf "$ROOTFS/var/cache/dnf" \
       "$ROOTFS/var/log/*" \
       "$ROOTFS/tmp/*" \
       "$ROOTFS/root/.bash_history"

# 查看大小
echo "rootfs 大小:"
du -sh "$ROOTFS"
```

### 6.2 制作 squashfs

```bash
# 创建 LiveOS 目录结构
mkdir -p "$BUILD_DIR/LiveOS"

# 打包 squashfs (xz 压缩, 压缩率最高)
mksquashfs "$ROOTFS" "$BUILD_DIR/LiveOS/squashfs.img" \
    -comp xz \
    -Xcompression-level 9 \
    -no-exports \
    -no-xattrs \
    -noappend

echo "squashfs 大小:"
ls -lh "$BUILD_DIR/LiveOS/squashfs.img"
```

### 6.3 生成 initramfs

```bash
# 使用 dracut 生成 LiveOS 用的 initramfs
# 需要包含 liveos 模块

# 在 rootfs 中生成 (确保内核版本匹配)
mount --bind /dev "$ROOTFS/dev"
mount --bind /proc "$ROOTFS/proc"
mount --bind /sys "$ROOTFS/sys"

chroot "$ROOTFS" << 'CHROOT_EOF'
# 安装 dracut live 模块
dnf install -y dracut-live

# 获取内核版本
KVER=$(ls /lib/modules | sort -V | tail -1)
echo "内核版本: $KVER"

# 生成 initramfs (包含 liveos 模块)
dracut --force \
    --add "dmsquash-live" \
    --add-drivers "megaraid_sas mpt3sas nvme nvme-core mlx5_core mlx4_core \
                    ixgbe i40e ice igb tg3 bnxt_en ipmi_devintf ipmi_si \
                    coretemp k10temp drivetemp nct6775" \
    --no-hostonly \
    --filesystems "squashfs ext4 xfs" \
    /boot/initramfs-live.img "$KVER"

# 同时复制内核
cp "/boot/vmlinuz-${KVER}" /boot/vmlinuz-live

echo "initramfs 生成完成"
ls -lh /boot/vmlinuz-live /boot/initramfs-live.img

CHROOT_EOF

umount "$ROOTFS/dev" "$ROOTFS/proc" "$ROOTFS/sys"

# 复制到输出目录
cp "$ROOTFS/boot/vmlinuz-live" "$BUILD_DIR/output/vmlinuz"
cp "$ROOTFS/boot/initramfs-live.img" "$BUILD_DIR/output/initrd.img"
cp "$BUILD_DIR/LiveOS/squashfs.img" "$BUILD_DIR/output/"

```

### 6.4 生成 ISO

```bash
# 创建 ISO 目录结构
ISODIR="$BUILD_DIR/iso"
mkdir -p "$ISODIR/isolinux" "$ISODIR/LiveOS" "$ISODIR/EFI/BOOT"

# 复制文件
cp "$BUILD_DIR/output/vmlinuz" "$ISODIR/isolinux/vmlinuz"
cp "$BUILD_DIR/output/initrd.img" "$ISODIR/isolinux/initrd.img"
cp "$BUILD_DIR/LiveOS/squashfs.img" "$ISODIR/LiveOS/"

# isolinux 配置 (Legacy BIOS)
cat > "$ISODIR/isolinux/isolinux.cfg" << 'EOF'
DEFAULT linux
PROMPT 1
TIMEOUT 30

LABEL linux
    MENU LABEL ^1. HWTest Live (自动测试)
    KERNEL /isolinux/vmlinuz
    APPEND initrd=/isolinux/initrd.img \
           root=live:CDLABEL=HWTEST-LIVE \
           rd.live.image rd.live.ram=1 \
           rd.live.overlay.overlayfs=1 \
           ip=dhcp quiet

LABEL linux_manual
    MENU LABEL ^2. HWTest Live (手动, 跳过自动测试)
    KERNEL /isolinux/vmlinuz
    APPEND initrd=/isolinux/initrd.img \
           root=live:CDLABEL=HWTEST-LIVE \
           rd.live.image rd.live.ram=1 \
           rd.live.overlay.overlayfs=1 \
           ip=dhcp hwtest.skip quiet

LABEL memtest
    MENU LABEL ^3. Memtest86+
    KERNEL /isolinux/memtest86+

EOF

# 复制 isolinux 引导文件
cp /usr/share/syslinux/isolinux.bin "$ISODIR/isolinux/" 2>/dev/null || \
    dnf install -y syslinux-nonlinux && \
    cp /usr/share/syslinux/isolinux.bin "$ISODIR/isolinux/"
cp /usr/share/syslinux/ldlinux.c32 "$ISODIR/isolinux/" 2>/dev/null || true
cp /usr/share/syslinux/menu.c32 "$ISODIR/isolinux/" 2>/dev/null || true
cp /usr/share/syslinux/libcom32.c32 "$ISODIR/isolinux/" 2>/dev/null || true
cp /usr/share/syslinux/libutil.c32 "$ISODIR/isolinux/" 2>/dev/null || true

# 复制 Memtest86+ (如果有)
cp "$ROOTFS/boot/memtest86+-"* "$ISODIR/isolinux/memtest86+" 2>/dev/null || \
    echo "(Memtest86+ 未包含)"

# UEFI 引导 (GRUB)
cat > "$ISODIR/EFI/BOOT/grub.cfg" << 'EOF'
set timeout=30
set default=0

menuentry "1. HWTest Live (自动测试)" {
    linux /isolinux/vmlinuz \
          root=live:CDLABEL=HWTEST-LIVE \
          rd.live.image rd.live.ram=1 \
          rd.live.overlay.overlayfs=1 \
          ip=dhcp quiet
    initrd /isolinux/initrd.img
}

menuentry "2. HWTest Live (手动, 跳过自动测试)" {
    linux /isolinux/vmlinuz \
          root=live:CDLABEL=HWTEST-LIVE \
          rd.live.image rd.live.ram=1 \
          rd.live.overlay.overlayfs=1 \
          ip=dhcp hwtest.skip quiet
    initrd /isolinux/initrd.img
}
EOF

# 复制 UEFI 引导文件
cp "$ROOTFS/boot/efi/EFI/rocky/grubx64.efi" "$ISODIR/EFI/BOOT/BOOTX64.EFI" 2>/dev/null || \
    cp /boot/efi/EFI/rocky/grubx64.efi "$ISODIR/EFI/BOOT/BOOTX64.EFI" 2>/dev/null || \
    dnf install -y shim-x64 grub2-efi-x64 && \
    cp /boot/efi/EFI/rocky/grubx64.efi "$ISODIR/EFI/BOOT/BOOTX64.EFI"

# 生成 ISO
xorriso -as mkisofs \
    -o "$BUILD_DIR/output/hwtest-live-${IMG_VERSION}-${IMG_DATE}.iso" \
    -V "HWTEST-LIVE" \
    -isohybrid-mbr /usr/share/syslinux/isohdpfx.bin \
    -b isolinux/isolinux.bin \
    -c isolinux/boot.cat \
    -boot-load-size 4 \
    -boot-info-table \
    -no-emul-boot \
    -eltorito-alt-boot \
    -e EFI/BOOT/BOOTX64.EFI \
    -no-emul-boot \
    -isohybrid-gpt-basdat \
    "$ISODIR"

echo ""
echo "=== 构建完成 ==="
ls -lh "$BUILD_DIR/output/"
echo ""
echo "ISO: $BUILD_DIR/output/hwtest-live-${IMG_VERSION}-${IMG_DATE}.iso"
echo "PXE 文件:"
echo "  vmlinuz → /srv/tftp/hwtest/vmlinuz"
echo "  initrd  → /srv/tftp/hwtest/initrd.img"
echo "  squashfs → /srv/install/hwtest/squashfs.img"
```

---

## 七、部署到 PXE

### 7.1 复制文件

```bash
mkdir -p /srv/tftp/hwtest /srv/install/hwtest

cp "$BUILD_DIR/output/vmlinuz" /srv/tftp/hwtest/vmlinuz
cp "$BUILD_DIR/output/initrd.img" /srv/tftp/hwtest/initrd.img
cp "$BUILD_DIR/output/squashfs.img" /srv/install/hwtest/
```

### 7.2 添加引导菜单

```bash
# Legacy BIOS
cat >> /srv/tftp/pxelinux.cfg/default << 'EOF'

LABEL hwtest_auto
    MENU LABEL ^A. HWTest Live (自动测试)
    KERNEL hwtest/vmlinuz
    APPEND initrd=hwtest/initrd.img \
           root=live:http://192.168.100.10/install/hwtest/squashfs.img \
           rd.live.image rd.live.ram=1 \
           rd.live.overlay.overlayfs=1 \
           ip=dhcp quiet

LABEL hwtest_manual
    MENU LABEL ^B. HWTest Live (手动, 跳过自动测试)
    KERNEL hwtest/vmlinuz
    APPEND initrd=hwtest/initrd.img \
           root=live:http://192.168.100.10/install/hwtest/squashfs.img \
           rd.live.image rd.live.ram=1 \
           rd.live.overlay.overlayfs=1 \
           ip=dhcp hwtest.skip quiet
EOF

# UEFI
cat >> /srv/tftp/grub/grub.cfg << 'EOF'

menuentry "A. HWTest Live (自动测试)" {
    linux hwtest/vmlinuz \
          root=live:http://192.168.100.10/install/hwtest/squashfs.img \
          rd.live.image rd.live.ram=1 \
          rd.live.overlay.overlayfs=1 \
          ip=dhcp quiet
    initrd hwtest/initrd.img
}

menuentry "B. HWTest Live (手动, 跳过自动测试)" {
    linux hwtest/vmlinuz \
          root=live:http://192.168.100.10/install/hwtest/squashfs.img \
          rd.live.image rd.live.ram=1 \
          rd.live.overlay.overlayfs=1 \
          ip=dhcp hwtest.skip quiet
    initrd hwtest/initrd.img
}
EOF
```

---

## 八、一键构建脚本

将以上步骤整合为一个可重复执行的构建脚本：

```bash
#!/bin/bash
# ====================================================================
# build-hwtest-image.sh — 一键构建硬件测试 Live 镜像
#
# 用法: ./build-hwtest-image.sh [选项]
#
# 选项:
#   --with-nvidia      包含 NVIDIA 驱动 (需提前放 .run 文件到 /tmp/)
#   --with-ofed        包含 Mellanox OFED (需提前放 ISO 到 /tmp/)
#   --with-storcli     包含 storcli64 (需提前放到 /tmp/storcli64)
#   --version VER      镜像版本号 (默认 1.0)
#   --output DIR       输出目录 (默认 /srv/image-build/output)
#
# 前置: 将驱动文件放到 /tmp/ 目录
#   /tmp/NVIDIA-Linux-x86_64-550.xx.run   (NVIDIA 驱动)
#   /tmp/MLNX_OFED_LINUX.iso              (Mellanox OFED)
#   /tmp/storcli64                        (LSI RAID 工具)
#   /tmp/perccli64                        (Dell PERC 工具)
#   /tmp/ssacli                           (HPE RAID 工具)
#
# 输出:
#   output/hwtest-live-<ver>-<date>.iso   (可刻录/虚拟媒体)
#   output/vmlinuz                        (PXE 内核)
#   output/initrd.img                     (PXE initramfs)
#   output/squashfs.img                   (PXE 根文件系统)
# ====================================================================

set -euo pipefail

# === 默认变量 ===
IMG_NAME="hwtest-live"
IMG_VERSION="1.0"
IMG_DATE=$(date +%Y%m%d)
BUILD_DIR="/srv/image-build"
ROOTFS="$BUILD_DIR/rootfs"
OUTPUT_DIR="$BUILD_DIR/output"
ROCKY_VER="9"

WITH_NVIDIA=false
WITH_OFED=false
WITH_STORCLI=false

# === 解析参数 ===
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-nvidia)  WITH_NVIDIA=true; shift ;;
        --with-ofed)    WITH_OFED=true; shift ;;
        --with-storcli) WITH_STORCLI=true; shift ;;
        --version)      IMG_VERSION="$2"; shift 2 ;;
        --output)       OUTPUT_DIR="$2"; shift 2 ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

echo "╔══════════════════════════════════════════╗"
echo "║  硬件测试镜像构建工具                      ║"
echo "║  版本: ${IMG_VERSION}                      ║"
echo "║  日期: ${IMG_DATE}                         ║"
echo "╠══════════════════════════════════════════╣"
echo "║  NVIDIA:  $WITH_NVIDIA                    ║"
echo "║  OFED:    $WITH_OFED                      ║"
echo "║  StorCLI: $WITH_STORCLI                   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# === 检查驱动文件 ===
echo "[1/8] 检查驱动文件..."
$WITH_NVIDIA && {
    [ -f /tmp/NVIDIA-Linux-x86_64-*.run ] || { echo "❌ 未找到 NVIDIA 驱动"; exit 1; }
}
$WITH_OFED && {
    [ -f /tmp/MLNX_OFED_LINUX.iso ] || { echo "❌ 未找到 OFED ISO"; exit 1; }
}
$WITH_STORCLI && {
    [ -f /tmp/storcli64 ] || { echo "❌ 未找到 storcli64"; exit 1; }
}
echo "  ✅ 驱动文件检查通过"

# === 后续步骤 2-8 调用前面的函数 ===
# [2/8] 构建根文件系统
# [3/8] 注入测试工具
# [4/8] 注入物理驱动
# [5/8] 配置自启动
# [6/8] 打包 squashfs
# [7/8] 生成 initramfs
# [8/8] 生成 ISO + PXE 文件

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  构建完成!                                 ║"
echo "╠══════════════════════════════════════════╣"
echo "║  ISO:  $OUTPUT_DIR/${IMG_NAME}-${IMG_VERSION}-${IMG_DATE}.iso"
echo "║  PXE:  vmlinuz + initrd.img + squashfs.img"
echo "╚══════════════════════════════════════════╝"
```

---

## 九、镜像维护与更新

### 9.1 更新测试工具

```bash
# 挂载已有 squashfs, 更新工具, 重新打包
mkdir -p /tmp/rootfs-update
mount -t squashfs -o loop /srv/install/hwtest/squashfs.img /tmp/rootfs-update

# 复制到可写目录
cp -a /tmp/rootfs-update/* "$ROOTFS/"
umount /tmp/rootfs-update

# chroot 更新
mount --bind /dev "$ROOTFS/dev"
mount --bind /proc "$ROOTFS/proc"
mount --bind /sys "$ROOTFS/sys"

chroot "$ROOTFS" dnf update -y
chroot "$ROOTFS" dnf install -y <新工具包>
chroot "$ROOTFS" dnf clean all

umount "$ROOTFS/dev" "$ROOTFS/proc" "$ROOTFS/sys"

# 重新打包
mksquashfs "$ROOTFS" /srv/install/hwtest/squashfs.img.new \
    -comp xz -Xcompression-level 9 -noappend

# 替换
mv /srv/install/hwtest/squashfs.img /srv/install/hwtest/squashfs.img.bak
mv /srv/install/hwtest/squashfs.img.new /srv/install/hwtest/squashfs.img
```

### 9.2 内核更新后重建 initramfs

```bash
# 当 rootfs 中更新了 kernel 包后, 需要重新生成 initramfs
# (initramfs 必须与内核版本严格匹配)

chroot "$ROOTFS" << 'EOF'
KVER=$(ls /lib/modules | sort -V | tail -1)
dracut --force \
    --add "dmsquash-live" \
    --add-drivers "megaraid_sas mpt3sas nvme mlx5_core ixgbe i40e ipmi_si" \
    --no-hostonly \
    --filesystems "squashfs ext4 xfs" \
    /boot/initramfs-live.img "$KVER"
cp "/boot/vmlinuz-${KVER}" /boot/vmlinuz-live
EOF

cp "$ROOTFS/boot/vmlinuz-live" /srv/tftp/hwtest/vmlinuz
cp "$ROOTFS/boot/initramfs-live.img" /srv/tftp/hwtest/initrd.img
```

### 9.3 版本管理

```bash
# 镜像版本信息
cat > "$ROOTFS/etc/hwtest-release" << EOF
NAME=hwtest-live
VERSION=$IMG_VERSION
DATE=$IMG_DATE
BUILDER=$(whoami)@$(hostname)
KERNEL=$(chroot "$ROOTFS" uname -r 2>/dev/null || echo "unknown")
TOOLS=stress-ng,fio,memtester,smartmontools,iperf3,nvme-cli,ipmitool
DRIVERS=megaraid_sas,mpt3sas,nvme,mlx5_core,ixgbe,i40e
EOF

# 构建后在镜像中可以查看:
# cat /etc/hwtest-release
```

---

## 十、验证清单

镜像构建完成后，启动一台测试机验证：

| # | 检查项 | 命令 | 预期 |
|:---:|:---|:---|:---|
| 1 | 系统启动 | PXE 引导 → 自动进入 | 2 分钟内进入系统 |
| 2 | 内核版本 | `uname -r` | 与构建时一致 |
| 3 | 测试工具 | `which stress-ng fio memtester iperf3` | 全部存在 |
| 4 | RAID 工具 | `storcli64 /c0 show` | 能看到 RAID 卡 |
| 5 | RAID 驱动 | `lsmod \| grep megaraid` | megaraid_sas 已加载 |
| 6 | 磁盘可见 | `lsblk` | RAID 虚拟盘可见 |
| 7 | NVMe | `nvme list` | NVMe 盘可见 |
| 8 | 网卡驱动 | `ethtool -i eth0` | 正确驱动 + 固件版本 |
| 9 | IPMI | `ipmitool mc info` | BMC 信息可读 |
| 10 | 传感器 | `sensors` | CPU/主板温度可读 |
| 11 | GPU (如有) | `nvidia-smi` | GPU 列表可见 |
| 12 | 自动测试 | 等待自启动 | hwtest-autorun.service 执行 |
| 13 | 测试结果 | `cat /opt/hwtest/results/*/report.txt` | 报告生成 |
| 14 | SSH | `ssh root@<IP>` | 可登录 |
| 15 | 内存占用 | `free -h` | squashfs 加载后占用合理 |

---

## 十一、常见问题

### Q1: 构建时 dnf --installroot 失败

```bash
# 原因: 构建服务器无法访问镜像源
# 解决: 配置本地源或使用 --repofrompath 指定可用的源

# 或者先在本机安装包再复制:
dnf install -y --downloadonly --downloaddir=/tmp/rpms @core
dnf install -y --installroot="$ROOTFS" /tmp/rpms/*.rpm
```

### Q2: squashfs 太大（>4GB）

```bash
# 原因: 装了太多包
# 解决:

# 1. 用 --nodocs 减少文档
dnf install -y --installroot="$ROOTFS" --nodocs ...

# 2. 清理缓存
chroot "$ROOTFS" dnf clean all
rm -rf "$ROOTFS"/var/cache/* "$ROOTFS"/usr/share/{doc,man,info}/*

# 3. 用 zstd 压缩 (比 xz 快, 压缩率略低)
mksquashfs "$ROOTFS" squashfs.img -comp zstd -Xcompression-level 19

# 4. 拆分: 基础 squashfs + 额外模块 overlay
```

### Q3: NVIDIA 驱动在目标服务器上不加载

```bash
# 原因: 构建机内核和目标机内核不一致, DKMS 没编译成功
# 解决:

# 1. 确保 rootfs 中的 kernel-devel 版本与 kernel 完全一致
chroot "$ROOTFS" bash -c 'rpm -q kernel kernel-devel'

# 2. 在 chroot 中手动触发 DKMS 编译
chroot "$ROOTFS" dkms autoinstall -k $(chroot "$ROOTFS" ls /lib/modules)

# 3. 或者不用 DKMS, 直接预编译对应版本:
chroot "$ROOTFS" bash -c '
    KVER=$(ls /lib/modules | tail -1)
    sh /tmp/NVIDIA-Linux-x86_64-*.run --silent --kernel-name=$KVER --no-dkms
'
```

### Q4: 引导时 "unable to mount root fs"

```bash
# 原因: initramfs 缺少网络驱动, 无法从 HTTP 下载 squashfs
# 解决: dracut 强制包含网络驱动

dracut --force \
    --add "dmsquash-live network" \
    --add-drivers "mlx5_core ixgbe i40e igb tg3 bnxt_en" \
    --install "/usr/sbin/dhclient" \
    --no-hostonly \
    /boot/initramfs-live.img "$KVER"
```

### Q5: rd.live.ram 导致内存不足

```bash
# 如果服务器内存 < 8GB, squashfs 全部加载到 RAM 可能不够
# 解决: 去掉 rd.live.ram=1, 改为 NFS Root 方式

# 引导参数改为:
# root=live:nfs:192.168.100.10:/srv/nfsroot/hwtest squashfs.img ro
# (不加 rd.live.ram, 文件系统在 NFS 上按需读取)
```

### Q6: 测试工具版本过旧

```bash
# stress-ng / fio 等工具更新很快, EPEL 源可能不是最新
# 解决: 从源码编译最新版

chroot "$ROOTFS" << 'EOF'
# 编译最新 stress-ng
dnf install -y git
git clone https://github.com/ColinIanKing/stress-ng.git /tmp/stress-ng
cd /tmp/stress-ng
make -j$(nproc)
install -m 755 stress-ng /usr/bin/stress-ng
rm -rf /tmp/stress-ng

# 编译最新 fio
git clone https://github.com/axboe/fio.git /tmp/fio
cd /tmp/fio
./configure --disable-native
make -j$(nproc)
install -m 755 fio /usr/bin/fio
rm -rf /tmp/fio
EOF
```

---

## 十二、驱动注入清单速查

### 12.1 内核模块（通常已内置，需确认）

| 驱动模块 | 硬件 | 确认命令 |
|:---|:---|:---|
| `megaraid_sas` | Broadcom/LSI MegaRAID | `modinfo megaraid_sas` |
| `mpt3sas` | LSI HBA / SAS | `modinfo mpt3sas` |
| `hpsa` | HPE Smart Array | `modinfo hpsa` |
| `aacraid` | Adaptec RAID | `modinfo aacraid` |
| `arcmsr` | Areca RAID | `modinfo arcmsr` |
| `nvme` | NVMe SSD | `modinfo nvme` |
| `nvme-fc` | NVMe over Fabrics | `modinfo nvme-fc` |
| `mlx5_core` | Mellanox ConnectX-4+ | `modinfo mlx5_core` |
| `mlx4_core` | Mellanox ConnectX-3 | `modinfo mlx4_core` |
| `ixgbe` | Intel 10GbE | `modinfo ixgbe` |
| `i40e` | Intel 25/40GbE | `modinfo i40e` |
| `ice` | Intel 800GbE | `modinfo ice` |
| `igb` | Intel 1GbE | `modinfo igb` |
| `tg3` | Broadcom 1GbE | `modinfo tg3` |
| `bnxt_en` | Broadcom NetXtreme | `modinfo bnxt_en` |
| `ipmi_si` | IPMI 系统接口 | `modinfo ipmi_si` |
| `ipmi_devintf` | IPMI 设备接口 | `modinfo ipmi_devintf` |
| `coretemp` | Intel CPU 温度 | `modinfo coretemp` |
| `k10temp` | AMD CPU 温度 | `modinfo k10temp` |
| `drivetemp` | 硬盘温度 | `modinfo drivetemp` |
| `nct6775` | 主板传感器 (Nuvoton) | `modinfo nct6775` |
| `nvidia` | NVIDIA GPU | `modinfo nvidia` |

### 12.2 用户态工具（需手动安装/注入）

| 工具 | 用途 | 获取方式 |
|:---|:---|:---|
| `storcli64` | LSI/Broadcom RAID 管理 | Broadcom 官网下载 |
| `perccli64` | Dell PERC RAID 管理 | Dell 支持站下载 |
| `ssacli` | HPE Smart Array 管理 | HPE 支持站下载 |
| `OneCLI` | Lenovo 服务器管理 | Lenovo 支持站下载 |
| `MFT` | Mellanox 固件工具 | NVIDIA 网络官网下载 |
| `MLNX_OFED` | Mellanox 完整驱动栈 | NVIDIA 网络官网下载 |
| `NVIDIA .run` | NVIDIA GPU 驱动 | NVIDIA 官网下载 |
| `gpu-burn` | GPU 压力测试 | GitHub: wilicc/gpu-burn |
| `DSU` | Dell 系统更新 | Dell 支持站下载 |
| `mprime` | Prime95 for Linux | mersenne.org 下载 |

---

## 十三、镜像大小参考

| 组件 | 大小 | 说明 |
|:---|:---:|:---|
| Rocky 9 最小系统 | 400MB | @core + 基础工具 |
| 内核 + 模块 | 150MB | kernel + kernel-modules + extra |
| 测试工具 | 200MB | stress-ng/fio/memtester/smartmontools 等 |
| 网络工具 | 50MB | iperf3/nmap/tcpdump 等 |
| RAID 工具 | 20MB | storcli64/perccli/ssacli |
| IPMI 工具 | 10MB | ipmitool/OpenIPMI |
| NVIDIA 驱动 | 350MB | 驱动 + CUDA 库 (可选) |
| Mellanox OFED | 200MB | 完整 OFED 栈 (可选) |
| Python + pip 包 | 100MB | Python3 + 测试框架 |
| **合计 (无 GPU/OFED)** | **~930MB** | squashfs 压缩后约 400MB |
| **合计 (含 GPU+OFED)** | **~1.5GB** | squashfs 压缩后约 650MB |
| **initramfs** | **~80MB** | 仅引导用 |
| **ISO 总大小** | **~500-700MB** | 含 squashfs + 引导文件 |

---

*最后更新: 2026-07-07*
