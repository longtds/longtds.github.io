# PXE 批量自动安装操作系统

> 10 台以上服务器装机不要逐台插 U 盘。用 PXE 网络引导 + Kickstart/Autoinstall 实现全自动批量安装，插网线开机即装。

---

## 一、原理与架构

### 1.1 PXE 引导流程

```
服务器上电
  │
  ▼
网卡 PXE 固件发起 DHCP 请求
  │
  ▼
DHCP Server 响应:
  分配 IP + 告知 TFTP Server 地址 + 引导文件名 (pxelinux.0 / grubx64.efi)
  │
  ▼
服务器从 TFTP 下载引导文件 + 内核 (vmlinuz) + initramfs
  │
  ▼
内核启动, 加载 initramfs
  │
  ▼
安装程序读取 Kickstart/Autoinstall 配置文件 (HTTP)
  │
  ▼
全自动分区 + 选包 + 配置网络 + 设密码 + 安装
  │
  ▼
安装完成, 重启进入新系统
```

### 1.2 组件说明

| 组件 | 作用 | 端口 | 软件 |
|:---|:---|:---:|:---|
| DHCP Server | 分配 IP + 指定引导文件 | UDP 67 | dnsmasq / isc-dhcp-server |
| TFTP Server | 传输引导文件和内核 | UDP 69 | tftp-server / dnsmasq |
| HTTP Server | 提供 ISO 镜像和 Kickstart 文件 | TCP 80 | nginx / httpd |
| Kickstart | Rocky/CentOS 自动应答文件 | — | anaconda |
| Autoinstall | Ubuntu 自动应答文件 | — | cloud-init/subiquity |

### 1.3 网络拓扑

```
┌──────────────────────────────────────────────┐
│              PXE 装机服务器                    │
│                                              │
│  ┌─────┐  ┌─────┐  ┌──────┐  ┌───────────┐  │
│  │DHCP │  │TFTP │  │HTTP  │  │Kickstart  │  │
│  │:67  │  │:69  │  │:80   │  │ autoinstall│  │
│  └──┬──┘  └──┬──┘  └──┬───┘  └─────┬─────┘  │
│     └────────┴────────┴─────────────┘        │
│                    ens33                      │
│              192.168.100.10                   │
└──────────────────┬───────────────────────────┘
                   │ 交换机 (VLAN 100)
     ┌─────────────┼─────────────┐
     │             │             │
 ┌───┴───┐   ┌────┴───┐   ┌────┴───┐
 │Server1│   │Server2 │   │ServerN │
 │PXE引导│   │PXE引导 │   │PXE引导 │
 └───────┘   └────────┘   └────────┘
```

!!! warning "DHCP 冲突"
    PXE 网段**不能有其他 DHCP Server**（包括路由器/交换机的 DHCP），否则 PXE 客户端可能拿到错误 IP 无法引导。建议用独立 VLAN 或先关闭其他 DHCP。

---

## 二、装机服务器搭建

### 2.1 环境准备

```bash
# 装机服务器: Rocky Linux 9 (或任何 Linux)
# IP: 192.168.100.10/24
# 网卡: ens33
# 隔离 VLAN, 无其他 DHCP

# 关闭防火墙和 SELinux (装机阶段简化)
systemctl stop firewalld && systemctl disable firewalld
setenforce 0
sed -i 's/^SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config
```

### 2.2 安装服务组件

```bash
# 安装 dnsmasq (DHCP + TFTP 二合一) + nginx (HTTP)
dnf install -y dnsmasq nginx

# 安装 syslinux (Legacy PXE 引导文件)
dnf install -y syslinux

# 安装工具
dnf install -y wget rsync
```

### 2.3 准备镜像

```bash
mkdir -p /srv/install/{rocky9,ubuntu22}
mkdir -p /srv/tftp/{rocky9,ubuntu22}
mkdir -p /srv/ks

# 下载镜像
cd /tmp
wget https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.5-x86_64-dvd.iso
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.5-live-server-amd64.iso

# 挂载 Rocky 镜像并复制内容
mount -o loop,ro Rocky-9.5-x86_64-dvd.iso /mnt
rsync -aH /mnt/ /srv/install/rocky9/
umount /mnt

# 挂载 Ubuntu 镜像并复制内容
mount -o loop,ro ubuntu-22.04.5-live-server-amd64.iso /mnt
rsync -aH /mnt/ /srv/install/ubuntu22/
umount /mnt

# 复制引导文件到 TFTP 目录
# Rocky (UEFI)
cp /srv/install/rocky9/EFI/BOOT/BOOTX64.EFI /srv/tftp/rocky9/
cp /srv/install/rocky9/EFI/BOOT/grubx64.efi /srv/tftp/rocky9/
cp /srv/install/rocky9/images/pxeboot/vmlinuz /srv/tftp/rocky9/
cp /srv/install/rocky9/images/pxeboot/initrd.img /srv/tftp/rocky9/

# Rocky (Legacy BIOS)
cp /srv/install/rocky9/isolinux/pxelinux.0 /srv/tftp/rocky9/ 2>/dev/null || \
  cp /usr/share/syslinux/pxelinux.0 /srv/tftp/rocky9/
cp /srv/install/rocky9/isolinux/ldlinux.c32 /srv/tftp/rocky9/ 2>/dev/null || \
  cp /usr/share/syslinux/ldlinux.c32 /srv/tftp/rocky9/
cp /srv/install/rocky9/isolinux/menu.c32 /srv/tftp/rocky9/ 2>/dev/null || \
  cp /usr/share/syslinux/menu.c32 /srv/tftp/rocky9/
cp /srv/install/rocky9/isolinux/libutil.c32 /srv/tftp/rocky9/ 2>/dev/null || \
  cp /usr/share/syslinux/libutil.c32 /srv/tftp/rocky9/
cp /srv/install/rocky9/isolinux/libcom32.c32 /srv/tftp/rocky9/ 2>/dev/null || \
  cp /usr/share/syslinux/libcom32.c32 /srv/tftp/rocky9/

# Ubuntu (UEFI)
cp /srv/install/ubuntu22/casper/vmlinuz /srv/tftp/ubuntu22/
cp /srv/install/ubuntu22/casper/initrd /srv/tftp/ubuntu22/

# Ubuntu (Legacy BIOS)
cp /usr/share/syslinux/pxelinux.0 /srv/tftp/ubuntu22/ 2>/dev/null || true
```

---

## 三、配置 DHCP + TFTP (dnsmasq)

### 3.1 dnsmasq 配置

```bash
cat > /etc/dnsmasq.d/pxe.conf << 'EOF'
# === DHCP 配置 ===
# 监听接口
interface=ens33
bind-interfaces

# DHCP 地址池
dhcp-range=192.168.100.100,192.168.100.200,12h

# 网关
dhcp-option=option:router,192.168.100.1

# DNS
dhcp-option=option:dns-server,192.168.100.10,114.114.114.114

# === PXE 引导配置 ===
# 启用 TFTP
enable-tftp
tftp-root=/srv/tftp

# --- UEFI 引导 (现代服务器, 默认走这里) ---
dhcp-match=set:efi-x86_64,option:client-arch,7
dhcp-match=set:efi-x86_64,option:client-arch,9
# --- Legacy BIOS 引导 ---
dhcp-match=set:bios,option:client-arch,0

# 根据引导模式分配不同引导文件
# UEFI -> Rocky grubx64.efi
dhcp-boot=tag:efi-x86_64,rocky9/grubx64.efi
# Legacy BIOS -> Rocky pxelinux.0
dhcp-boot=tag:bios,rocky9/pxelinux.0

# 日志
log-facility=/var/log/dnsmasq-pxe.log
log-dhcp
EOF
```

### 3.2 启动 dnsmasq

```bash
systemctl enable --now dnsmasq

# 验证
systemctl status dnsmasq
ss -ulnp | grep -E '67|69'
# 应看到 dnsmasq 监听 :67 (DHCP) 和 :69 (TFTP)

# 查看日志
tail -f /var/log/dnsmasq-pxe.log
```

---

## 四、配置 HTTP (nginx)

### 4.1 nginx 配置

```bash
cat > /etc/nginx/conf.d/pxe.conf << 'EOF'
server {
    listen 80;
    server_name _;

    # 镜像文件
    location /install/ {
        alias /srv/install/;
        autoindex on;
    }

    # Kickstart / Autoinstall 配置文件
    location /ks/ {
        alias /srv/ks/;
        autoindex on;
        default_type text/plain;
    }
}
EOF

systemctl enable --now nginx
nginx -t && systemctl reload nginx
```

### 4.2 验证 HTTP 可达

```bash
curl -I http://192.168.100.10/install/rocky9/.discinfo
curl -I http://192.168.100.10/ks/rocky9-ks.cfg
```

---

## 五、Kickstart 配置（Rocky/CentOS/RHEL）

### 5.1 主 Kickstart 文件

```bash
cat > /srv/ks/rocky9-ks.cfg << 'EOF'
# ============================================
# Rocky Linux 9 Kickstart - 全自动安装
# ============================================

# --- 基本设置 ---
# 图形安装改为文本
text

# 安装类型 (全新安装, 不升级)
install

# 安装源 (HTTP)
url --url=http://192.168.100.10/install/rocky9/BaseOS
# 如果有 AppStream (Rocky 9 默认有)
repo --name="AppStream" --baseurl=http://192.168.100.10/install/rocky9/AppStream

# 语言和键盘
lang zh_CN.UTF-8
keyboard --xlayouts='us'

# 时区
timezone Asia/Shanghai --isUtc

# --- 网络配置 ---
# DHCP 自动获取 (装完后改为静态)
network --bootproto=dhcp --device=link --activate --hostname=server-template

# --- Root 密码 ---
# 生成加密密码: python3 -c "import crypt; print(crypt.crypt('YourPass123!'))"
# 或: openssl passwd -6 'YourPass123!'
rootpw --iscrypted $6$xxxxx...

# --- 普通用户 ---
user --name=admin --groups=wheel --password=$6$xxxxx... --iscrypted

# --- 磁盘分区 ---
# 清除所有分区, 初始化所有磁盘
clearpart --all --initlabel

# UEFI 引导 (GPT 分区表)
part /boot/efi --fstype=efi --size=1024 --ondisk=nvme0n1
part /boot --fstype=xfs --size=1024 --ondisk=nvme0n1
part swap --fstype=swap --size=8192 --ondisk=nvme0n1
part / --fstype=xfs --grow --size=20480 --ondisk=nvme0n1

# Legacy BIOS 引导 (MSDOS 分区表, 替换上面的 /boot/efi)
# part /boot --fstype=xfs --size=1024 --ondisk=sda
# part swap --fstype=swap --size=8192 --ondisk=sda
# part / --fstype=xfs --grow --size=20480 --ondisk=sda

# --- 软件包 ---
%packages
@minimal
@core
vim
git
wget
curl
tmux
htop
net-tools
bind-utils
telnet
tcpdump
sysstat
nc
socat
rsync
python3
bash-completion
epel-release
# 排除不需要的
-aic94xx-firmware
-alsa-tools-firmware
-ivtv-firmware
-iwl*firmware
%end

# --- 安装后脚本 ---
%post --log=/var/log/ks-post.log

# 时区
timedatectl set-timezone Asia/Shanghai

# SSH 安全配置
sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# 部署公钥
mkdir -p /home/admin/.ssh
cat > /home/admin/.ssh/authorized_keys << 'KEY'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... admin@ops
KEY
chmod 700 /home/admin/.ssh
chmod 600 /home/admin/.ssh/authorized_keys
chown -R admin:admin /home/admin/.ssh

# 禁用 SELinux (按需)
sed -i 's/^SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config

# 更新系统
dnf update -y

# 安装基础工具
dnf install -y storcli64 ipmitool

# 配置 NTP
systemctl enable --now chronyd

# 清理
dnf clean all

%end

# --- 重启 ---
reboot
EOF
```

### 5.2 多机不同配置（SNIPPET）

如果 10 台机器需要不同主机名和 IP，用 `%include` + 脚本动态生成：

```bash
# /srv/ks/rocky9-ks.cfg 中替换静态主机名:
# 删除 network --hostname= 行, 改为:
network --bootproto=dhcp --device=link --activate

# 添加 %pre 脚本, 根据 IP 或 MAC 设置主机名:
%pre --log=/var/log/ks-pre.log

# 根据 DHCP 分配的 IP 设置主机名
IP=$(ip -4 addr show | grep 'inet ' | grep -v 127 | awk '{print $2}' | cut -d/ -f1)
LAST_OCTET=$(echo $IP | cut -d. -f4)
HOSTNAME="node-$(printf '%02d' $LAST_OCTET)"

echo "network --hostname=${HOSTNAME}" > /tmp/network.cfg

%end

# 然后在主配置中引入
%include /tmp/network.cfg
```

或者按 MAC 地址分配静态 IP + 主机名（更精确）：

```bash
# 在 dnsmasq 中按 MAC 绑定 IP + 主机名:
# /etc/dnsmasq.d/hosts.conf
dhcp-host=aa:bb:cc:dd:ee:01,192.168.100.101,web-01,12h
dhcp-host=aa:bb:cc:dd:ee:02,192.168.100.102,web-02,12h
dhcp-host=aa:bb:cc:dd:ee:03,192.168.100.103,db-01,12h
```

---

## 六、UEFI 引导菜单配置（Rocky）

### 6.1 GRUB 配置

```bash
mkdir -p /srv/tftp/rocky9/grub

cat > /srv/tftp/rocky9/grub/grub.cfg << 'EOF'
set timeout=10
set default=0

menuentry "Rocky Linux 9.5 自动安装 (PXE)" {
    linux rocky9/vmlinuz inst.stage2=http://192.168.100.10/install/rocky9 \
          inst.ks=http://192.168.100.10/ks/rocky9-ks.cfg \
          ip=dhcp \
          quiet
    initrd rocky9/initrd.img
}

menuentry "Rocky Linux 9.5 手动安装 (PXE)" {
    linux rocky9/vmlinuz inst.stage2=http://192.168.100.10/install/rocky9 \
          ip=dhcp
    initrd rocky9/initrd.img
}

menuentry "Rocky Linux 9.5 救援模式 (PXE)" {
    linux rocky9/vmlinuz inst.stage2=http://192.168.100.10/install/rocky9 \
          rescue \
          ip=dhcp
    initrd rocky9/initrd.img
}
EOF
```

### 6.2 Legacy BIOS 引导菜单

```bash
mkdir -p /srv/tftp/rocky9/pxelinux.cfg

cat > /srv/tftp/rocky9/pxelinux.cfg/default << 'EOF'
DEFAULT menu.c32
PROMPT 0
TIMEOUT 10
ONTIMEOUT Rocky9_Auto

MENU TITLE PXE Boot Menu

LABEL Rocky9_Auto
    MENU LABEL Rocky Linux 9.5 ^自动安装 (Kickstart)
    KERNEL rocky9/vmlinuz
    APPEND initrd=rocky9/initrd.img \
           inst.stage2=http://192.168.100.10/install/rocky9 \
           inst.ks=http://192.168.100.10/ks/rocky9-ks.cfg \
           ip=dhcp quiet

LABEL Rocky9_Manual
    MENU LABEL Rocky Linux 9.5 ^手动安装
    KERNEL rocky9/vmlinuz
    APPEND initrd=rocky9/initrd.img \
           inst.stage2=http://192.168.100.10/install/rocky9 \
           ip=dhcp

LABEL Rocky9_Rescue
    MENU LABEL Rocky Linux 9.5 ^救援模式
    KERNEL rocky9/vmlinuz
    APPEND initrd=rocky9/initrd.img \
           inst.stage2=http://192.168.100.10/install/rocky9 \
           rescue ip=dhcp

LABEL local
    MENU LABEL ^本地磁盘启动
    LOCALBOOT 0
EOF
```

---

## 七、Ubuntu Autoinstall 配置

### 7.1 Ubuntu 引导菜单

Ubuntu 22.04 Server 使用 cloud-init 风格的自动安装（autoinstall）：

```bash
# Legacy BIOS pxelinux.cfg/default (Ubuntu)
cat > /srv/tftp/ubuntu22/pxelinux.cfg/default << 'EOF'
DEFAULT menu.c32
PROMPT 0
TIMEOUT 10
ONTIMEOUT Ubuntu22_Auto

MENU TITLE Ubuntu PXE Boot Menu

LABEL Ubuntu22_Auto
    MENU LABEL Ubuntu 22.04 ^自动安装 (Autoinstall)
    KERNEL ubuntu22/vmlinuz
    APPEND initrd=ubuntu22/initrd \
           root=/dev/ram0 \
           ramdisk_size=1500000 \
           url=http://192.168.100.10/install/ubuntu22/ubuntu-22.04.5-live-server-amd64.iso \
           autoinstall ds=nocloud-net;s=http://192.168.100.10/ks/ubuntu22/ \
           ip=dhcp quiet

LABEL local
    MENU LABEL ^本地磁盘启动
    LOCALBOOT 0
EOF

# UEFI grub.cfg (Ubuntu)
cat > /srv/tftp/ubuntu22/grub.cfg << 'EOF'
set timeout=10
set default=0

menuentry "Ubuntu 22.04 自动安装 (Autoinstall)" {
    linux ubuntu22/vmlinuz \
          root=/dev/ram0 ramdisk_size=1500000 \
          url=http://192.168.100.10/install/ubuntu22/ubuntu-22.04.5-live-server-amd64.iso \
          autoinstall ds=nocloud-net\;s=http://192.168.100.10/ks/ubuntu22/ \
          ip=dhcp quiet
    initrd ubuntu22/initrd
}
EOF
```

### 7.2 Autoinstall 配置文件

```bash
mkdir -p /srv/ks/ubuntu22

cat > /srv/ks/ubuntu22/user-data << 'EOF'
#cloud-config
# ============================================
# Ubuntu 22.04 Autoinstall
# ============================================
autoinstall:
  version: 1

  # 语言/键盘
  locale: zh_CN.UTF-8
  keyboard:
    layout: us

  # 网络 (DHCP)
  network:
    network:
      version: 2
      ethernets:
        ens33:
          dhcp4: true

  # 磁盘分区 (全自动, 单盘)
  storage:
    layout:
      name: direct

  # 用户
  identity:
    hostname: ubuntu-template
    realname: Admin
    username: admin
    # 生成: openssl passwd -6 'YourPass123!'
    password: "$6$xxxxx..."

  # SSH
  ssh:
    install-server: true
    allow-pw: false

  # 时区
  timezone: Asia/Shanghai

  # 安装后执行
  late-commands:
    # 部署 SSH 公钥
    - curtin in-target --target=/target -- mkdir -p /home/admin/.ssh
    - |
      curtin in-target --target=/target -- bash -c \
      'echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... admin@ops" > /home/admin/.ssh/authorized_keys'
    - curtin in-target --target=/target -- chmod 700 /home/admin/.ssh
    - curtin in-target --target=/target -- chmod 600 /home/admin/.ssh/authorized_keys
    - curtin in-target --target=/target -- chown -R admin:admin /home/admin/.ssh

    # SSH 安全配置
    - curtin in-target --target=/target -- sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    - curtin in-target --target=/target -- sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config

    # 更新系统
    - curtin in-target --target=/target -- apt update
    - curtin in-target --target=/target -- apt upgrade -y

    # 安装工具
    - curtin in-target --target=/target -- apt install -y vim git wget curl tmux htop net-tools dnsutils telnet tcpdump sysstat

    # 清理 snap
    - curtin in-target --target=/target -- apt autoremove --purge -y snapd

  # 安装完成动作
  user-data:
    disable_root: true
EOF

# autoinstall 需要一个 meta-data 文件 (可为空)
touch /srv/ks/ubuntu22/meta-data
```

---

## 八、多系统引导菜单（同时支持 Rocky + Ubuntu）

如果 dnsmasq 需要根据不同服务器引导不同 OS，可以按 MAC 地址区分：

### 8.1 按 MAC 指定引导文件

```bash
# /etc/dnsmasq.d/pxe.conf 追加:
# 特定 MAC 引导 Ubuntu, 其余引导 Rocky
dhcp-host=aa:bb:cc:dd:ee:10,set:ubuntu
dhcp-host=aa:bb:cc:dd:ee:11,set:ubuntu
dhcp-host=aa:bb:cc:dd:ee:12,set:ubuntu

# Ubuntu 机器引导 Ubuntu
dhcp-boot=tag:ubuntu,tag:efi-x86_64,ubuntu22/grubx64.efi
dhcp-boot=tag:ubuntu,tag:bios,ubuntu22/pxelinux.0

# 其他机器引导 Rocky (默认)
dhcp-boot=tag:!ubuntu,tag:efi-x86_64,rocky9/grubx64.efi
dhcp-boot=tag:!ubuntu,tag:bios,rocky9/pxelinux.0
```

### 8.2 统一引导菜单（手动选择）

更简单的方案：所有机器引导到同一个菜单，人工选择装哪个：

```bash
# Legacy BIOS 统一菜单
cat > /srv/tftp/pxelinux.cfg/default << 'EOF'
DEFAULT menu.c32
PROMPT 0
TIMEOUT 30
ONTIMEOUT local

MENU ====== PXE Boot Menu ======

LABEL rocky9_auto
    MENU LABEL ^1. Rocky 9.5 自动安装
    KERNEL rocky9/vmlinuz
    APPEND initrd=rocky9/initrd.img \
           inst.stage2=http://192.168.100.10/install/rocky9 \
           inst.ks=http://192.168.100.10/ks/rocky9-ks.cfg \
           ip=dhcp quiet

LABEL ubuntu22_auto
    MENU LABEL ^2. Ubuntu 22.04 自动安装
    KERNEL ubuntu22/vmlinuz
    APPEND initrd=ubuntu22/initrd \
           url=http://192.168.100.10/install/ubuntu22/ubuntu-22.04.5-live-server-amd64.iso \
           autoinstall ds=nocloud-net\;s=http://192.168.100.10/ks/ubuntu22/ \
           ip=dhcp quiet

LABEL rocky9_manual
    MENU LABEL ^3. Rocky 9.5 手动安装
    KERNEL rocky9/vmlinuz
    APPEND initrd=rocky9/initrd.img \
           inst.stage2=http://192.168.100.10/install/rocky9 ip=dhcp

LABEL local
    MENU LABEL ^0. 本地磁盘启动
    LOCALBOOT 0
EOF

# UEFI 统一菜单 (用 GRUB)
cat > /srv/tftp/grub/grub.cfg << 'EOF'
set timeout=30
set default=0

menuentry "1. Rocky 9.5 自动安装" {
    linux rocky9/vmlinuz \
         inst.stage2=http://192.168.100.10/install/rocky9 \
         inst.ks=http://192.168.100.10/ks/rocky9-ks.cfg \
         ip=dhcp quiet
    initrd rocky9/initrd.img
}

menuentry "2. Ubuntu 22.04 自动安装" {
    linux ubuntu22/vmlinuz \
         url=http://192.168.100.10/install/ubuntu22/ubuntu-22.04.5-live-server-amd64.iso \
         autoinstall ds=nocloud-net\;s=http://192.168.100.10/ks/ubuntu22/ \
         ip=dhcp quiet
    initrd ubuntu22/initrd
}

menuentry "0. 本地磁盘启动" {
    exit
}
EOF
```

此时 dnsmasq 引导文件统一指向：
```bash
dhcp-boot=tag:efi-x86_64,grub/grubx64.efi
dhcp-boot=tag:bios,pxelinux.0
```

---

## 九、目标服务器配置

### 9.1 设置 PXE 引导

在目标服务器上操作（通过 BMC KVM 或物理接触）：

```
1. 开机 → 进 BIOS (F1/F2/Del)
2. Boot Order:
   ① Network Boot (PXE) → 第一位
   ② Hard Disk → 第二位
3. Boot Mode: UEFI (或 Legacy, 与 PXE 服务器配置一致)
4. 网卡 PXE:
   - BIOS → Network Boot → Enable
   - 或 BIOS → PCIe → 网卡 → PXE → Enable
5. 保存重启
```

### 9.2 通过 BMC 批量设置

```bash
# 使用 ipmitool 远程设置引导（以 Dell iDRAC 为例）
# 设置下次从 PXE 引导
ipmitool -I lanplus -H <BMC_IP> -U root -P calvin \
  chassis bootdev pxe

# 设置永久从 PXE 引导
ipmitool -I lanplus -H <BMC_IP> -U root -P calvin \
  chassis bootdev pxe persistent

# 远程开机
ipmitool -I lanplus -H <BMC_IP> -U root -P calvin \
  chassis power on

# 远程重启
ipmitool -I lanplus -H <BMC_IP> -U root -P calvin \
  chassis power cycle
```

**批量装机脚本：**

```bash
#!/bin/bash
# batch-install.sh — 批量 PXE 装机
# 用法: batch-install.sh <bmc_ip_list_file>

BMC_USER="root"
BMC_PASS="calvin"
IP_LIST="$1"

if [ -z "$IP_LIST" ]; then
    echo "用法: $0 <bmc_ip_list_file>"
    echo "文件格式: 每行一个 BMC IP"
    exit 1
fi

while read -r bmc_ip; do
    [ -z "$bmc_ip" ] && continue
    echo "[$(date +%H:%M:%S)] 处理 $bmc_ip ..."

    # 1. 设置 PXE 引导
    ipmitool -I lanplus -H "$bmc_ip" -U "$BMC_USER" -P "$BMC_PASS" \
        chassis bootdev pxe 2>/dev/null

    # 2. 重启进入 PXE
    ipmitool -I lanplus -H "$bmc_ip" -U "$BMC_USER" -P "$BMC_PASS" \
        chassis power cycle 2>/dev/null

    echo "[$(date +%H:%M:%S)] $bmc_ip 已触发 PXE 安装"

    # 间隔 5 秒, 避免 DHCP 冲突
    sleep 5

done < "$IP_LIST"

echo "[$(date +%H:%M:%S)] 全部触发完成"
echo "监控: tail -f /var/log/dnsmasq-pxe.log"
```

```bash
# bmc_list.txt
192.168.100.201
192.168.100.202
192.168.100.203
192.168.100.204
192.168.100.205

# 执行批量装机
chmod +x batch-install.sh
./batch-install.sh bmc_list.txt
```

---

## 十、安装过程监控

### 10.1 监控 DHCP/TFTP

```bash
# 实时查看 PXE 引导日志
tail -f /var/log/dnsmasq-pxe.log

# 典型成功日志:
# dnsmasq-dhcp[1234]: DHCPDISCOVER(ens33) aa:bb:cc:dd:ee:01
# dnsmasq-dhcp[1234]: DHCPOFFER(ens33) 192.168.100.101 aa:bb:cc:dd:ee:01
# dnsmasq-dhcp[1234]: DHCPREQUEST(ens33) 192.168.100.101 aa:bb:cc:dd:ee:01
# dnsmasq-dhcp[1234]: DHCPACK(ens33) 192.168.100.101 aa:bb:cc:dd:ee:01 web-01
# dnsmasq-tftp[1234]: sent /srv/tftp/rocky9/grubx64.efi
# dnsmasq-tftp[1234]: sent /srv/tftp/rocky9/vmlinuz
# dnsmasq-tftp[1234]: sent /srv/tftp/rocky9/initrd.img
```

### 10.2 监控 HTTP 下载

```bash
# nginx 访问日志
tail -f /var/log/nginx/access.log

# 典型日志:
# 192.168.100.101 - - "GET /ks/rocky9-ks.cfg HTTP/1.1" 200 1234
# 192.168.100.101 - - "GET /install/rocky9/BaseOS/... HTTP/1.1" 200 5678
```

### 10.3 监控安装进度（VNC/Sol）

通过 BMC 串口重定向或 VNC 控制台实时查看：

```bash
# ipmitool 串口重定向 (Sol)
ipmitool -I lanplus -H <BMC_IP> -U root -P calvin sol activate

# 退出 Sol
# ~.  (先按回车, 再按 ~.)
```

---

## 十一、安装后验证

装完重启后，逐台验证：

```bash
#!/bin/bash
# verify-install.sh — 批量验证安装结果
# 用法: verify-install.sh <host_list_file>
# 文件格式: 每行 IP

while read -r ip; do
    [ -z "$ip" ] && continue
    echo "===== $ip ====="

    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 admin@$ip \
        'echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d\" -f2)";
         echo "Kernel: $(uname -r)";
         echo "Hostname: $(hostname)";
         echo "IP: $(hostname -I)";
         echo "Disk: $(lsblk -d -o NAME,SIZE | grep -v NAME | head -1)";
         echo "Uptime: $(uptime -p)";
         echo "SSH: OK"' 2>/dev/null

    if [ $? -ne 0 ]; then
        echo "  ❌ SSH 连接失败"
    else
        echo "  ✅ 安装成功"
    fi
done < "$1"
```

---

## 十二、常见问题

### Q1: PXE 客户端拿不到 IP

```bash
# 检查 dnsmasq 是否运行
systemctl status dnsmasq

# 检查 DHCP 端口
ss -ulnp | grep :67

# 检查网络隔离
# ⚠️ 确认没有其他 DHCP Server (路由器/交换机)
# ⚠️ 确认 PXE VLAN 和装机服务器在同一二层网络

# 抓包确认
tcpdump -i ens33 port 67 or port 68 -n
```

### Q2: 拿到 IP 但下载引导文件失败

```bash
# 检查 TFTP
ss -ulnp | grep :69
# 手动测试 TFTP
tftp 192.168.100.10 -c get rocky9/grubx64.efi /tmp/test.efi
ls -la /tmp/test.efi

# 检查文件路径
ls -la /srv/tftp/rocky9/grubx64.efi
ls -la /srv/tftp/rocky9/pxelinux.0

# 检查权限
chmod -R 755 /srv/tftp
```

### Q3: 引导菜单不显示 / 直接过

```bash
# Legacy: 检查 pxelinux.0 和 menu.c32 是否在 TFTP 根目录
# UEFI: 检查 grubx64.efi 和 grub/grub.cfg 路径

# dnsmasq 指定的引导文件路径是相对于 tftp-root 的
# 例如 dhcp-boot=rocky9/grubx64.efi
# 实际文件应在 /srv/tftp/rocky9/grubx64.efi

# GRUB 配置文件路径: UEFI 会自动找 /grub/grub.cfg
# 确认 /srv/tftp/grub/grub.cfg 存在
ls /srv/tftp/grub/grub.cfg
```

### Q4: Kickstart 下载失败 (HTTP 404)

```bash
# 验证 HTTP 可达
curl http://192.168.100.10/ks/rocky9-ks.cfg

# 检查 nginx alias 路径
ls /srv/ks/rocky9-ks.cfg

# 检查 nginx 配置
nginx -t
```

### Q5: UEFI 和 Legacy 混合环境

```bash
# dnsmasq 用 tag 区分:
dhcp-match=set:efi-x86_64,option:client-arch,7   # UEFI x86_64
dhcp-match=set:efi-x86_64,option:client-arch,9   # UEFI x86_64 (2.0+)
dhcp-match=set:bios,option:client-arch,0          # Legacy BIOS

dhcp-boot=tag:efi-x86_64,grub/grubx64.efi
dhcp-boot=tag:bios,pxelinux.0

# 注意: pxelinux.0 只能用于 Legacy BIOS
#       grubx64.efi 只能用于 UEFI
#       两者不能混用
```

### Q6: Ubuntu autoinstall 不生效

```bash
# Ubuntu 22.04+ 需要明确指定 autoinstall 关键字
# 否则会停在交互式安装界面

# 检查 user-data 文件:
# 1. 第一行必须是 #cloud-config
# 2. autoinstall: version: 1 必须存在
# 3. meta-data 文件必须存在 (可为空)

# 验证:
curl http://192.168.100.10/ks/ubuntu22/user-data
curl http://192.168.100.10/ks/ubuntu22/meta-data

# 如果还是交互式, 在内核参数加 autoinstall ds=nocloud
# (不加分号和 URL, 让它从默认路径找)
```

### Q7: 多网卡服务器 PXE 从错误网卡引导

```bash
# 在 BIOS 中指定 PXE 引导网卡:
# BIOS → Network Boot → 选择正确的网卡 (通常是有 PXE 标志的那个)

# 或在 dnsmasq 中只响应特定 MAC:
dhcp-host=aa:bb:cc:dd:ee:01,192.168.100.101

# 或禁用其他网卡的 PXE:
# BIOS → Network Boot → 只 Enable 业务网卡, Disable 其他
```

---

## 十三、进阶：Cobbler 自动化

手动搭 PXE 适合 10-50 台。100 台以上用 Cobbler：

```bash
# 安装 Cobbler
dnf install -y epel-release
dnf install -y cobbler cobbler-web

# 初始化
systemctl enable --now cobblerd
systemctl enable --now httpd

# 修改配置
vi /etc/cobbler/settings
  server: 192.168.100.10
  next_server: 192.168.100.10
  manage_dhcp: true

# 导入镜像 (自动生成引导文件和菜单)
mount -o loop,ro Rocky-9.5-x86_64-dvd.iso /mnt
cobbler import --name=rocky9 --arch=x86_64 --path=/mnt

# 创建自动安装配置
cobbler profile add \
    --name=rocky9-web \
    --distro=rocky9-x86_64 \
    --kickstart=/srv/ks/rocky9-web.cfg

# 按主机名/MAC 绑定配置
cobbler system add \
    --name=web-01 \
    --mac=aa:bb:cc:dd:ee:01 \
    --ip-address=192.168.100.101 \
    --hostname=web-01 \
    --profile=rocky9-web \
    --static=true \
    --subnet=255.255.255.0 \
    --gateway=192.168.100.1

# 同步配置
cobbler sync

# Cobbler 自动管理 DHCP/TFTP/HTTP, 每次改配置只需 cobbler sync
```

### Cobbler vs 手动 PXE

| 维度 | 手动 PXE | Cobbler |
|:---|:---|:---|
| 搭建复杂度 | 中等 | 较高 |
| 管理多发行版 | 手动配置 | 一条命令导入 |
| 按主机分配配置 | 手动写 dnsmasq | `cobbler system add` |
| Web 界面 | ❌ | ✅ |
| 适合规模 | 10-50 台 | 50-1000 台 |
| 维护成本 | 改配置需手动同步 | `cobbler sync` |

---

## 十四、目录结构速查

```
/srv/
├── tftp/                          # TFTP 根目录
│   ├── grub/
│   │   └── grub.cfg               # UEFI 统一引导菜单
│   ├── pxelinux.0                 # Legacy 引导程序
│   ├── menu.c32                   # 菜单模块
│   ├── pxelinux.cfg/
│   │   └── default                # Legacy 引导菜单
│   ├── rocky9/
│   │   ├── grubx64.efi            # UEFI 引导程序
│   │   ├── vmlinuz                # 内核
│   │   ├── initrd.img             # 初始内存盘
│   │   ├── pxelinux.0
│   │   └── *.c32                  # syslinux 模块
│   └── ubuntu22/
│       ├── grubx64.efi
│       ├── vmlinuz
│       └── initrd
├── install/                       # HTTP 镜像目录
│   ├── rocky9/                    # Rocky DVD 内容
│   │   ├── BaseOS/
│   │   ├── AppStream/
│   │   └── images/
│   └── ubuntu22/                  # Ubuntu ISO 内容
│       ├── casper/
│       └── ubuntu-22.04.5-live-server-amd64.iso
└── ks/                            # Kickstart/Autoinstall 配置
    ├── rocky9-ks.cfg              # Rocky 自动应答
    └── ubuntu22/
        ├── user-data              # Ubuntu 自动应答
        └── meta-data              # (空文件, 必须存在)
```

---

## 十五、完整流程总结

```
                  ┌─────────────────────┐
                  │ 1. 搭建 PXE 服务器    │
                  │ (dnsmasq + nginx)   │
                  └─────────┬───────────┘
                            │
                  ┌─────────▼───────────┐
                  │ 2. 准备镜像 + 引导    │
                  │ (ISO -> HTTP/TFTP)  │
                  └─────────┬───────────┘
                            │
                  ┌─────────▼───────────┐
                  │ 3. 编写 Kickstart    │
                  │ /Autoinstall 配置    │
                  └─────────┬───────────┘
                            │
                  ┌─────────▼───────────┐
                  │ 4. 目标服务器设 PXE  │
                  │ (BMC/BIOS)          │
                  └─────────┬───────────┘
                            │
                  ┌─────────▼───────────┐
                  │ 5. 开机 → 自动安装    │
                  │ (全程无需人工)       │
                  └─────────┬───────────┘
                            │
                  ┌─────────▼───────────┐
                  │ 6. 验证 + 收尾       │
                  │ (SSH 验证 + 改引导)  │
                  └─────────────────────┘
```

**装机后记得：**

```bash
# 1. BIOS 改回硬盘引导 (或保留 PXE 但设为最后优先级)
# 通过 BMC:
ipmitool -I lanplus -H <BMC_IP> -U root -P calvin chassis bootdev disk permanent

# 2. 验证系统
ssh admin@<server_ip> 'cat /etc/os-release && uname -r && hostname'

# 3. 安装基础软件
ssh admin@<server_ip> 'sudo dnf install -y storcli64 ipmitool'

# 4. 配置监控接入 (Zabbix/Prometheus node_exporter)

# 5. 录入 CMDB
```

---

*最后更新: 2026-07-07*
