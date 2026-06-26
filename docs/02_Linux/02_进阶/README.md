# 进阶

> Linux 进阶 = **systemd 深度 + 存储栈（LVM/RAID/XFS）+ 网络配置 + 权限模型（ACL/Capability/SELinux）+ 调优入门 + Shell 中级**。本章面向已掌握基础、需要独立运维 5-50 台服务器的工程师。

## 一、systemd 深度

### 1.1 自定义 service（生产级 unit）

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application
Documentation=https://docs.example.com
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service             # 强依赖

[Service]
Type=simple                             # simple/forking/oneshot/notify
ExecStartPre=/bin/mkdir -p /var/log/myapp
ExecStart=/usr/local/bin/myapp --config /etc/myapp.conf
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill -TERM $MAINPID
Restart=on-failure                       # always/on-failure/on-abnormal
RestartSec=5s
TimeoutStartSec=60
TimeoutStopSec=30

# 运行身份
User=myapp
Group=myapp
WorkingDirectory=/var/lib/myapp
Environment="LOG_LEVEL=info"
EnvironmentFile=-/etc/myapp/env         # - 表示文件不存在不报错

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096
MemoryMax=2G
CPUQuota=200%                            # 2 个 CPU
TasksMax=512

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myapp

[Install]
WantedBy=multi-user.target
```

### 1.2 Type 类型对比

| Type | 何时认为启动完成 | 适合 |
|:---|:---|:---|
| **simple** ⭐ | ExecStart 调用完即认为 ready | 大部分前台进程 |
| **forking** | 主进程 fork 子进程退出 | nginx/php-fpm 老式 |
| **oneshot** | 命令执行完即停 | 一次性脚本 |
| **notify** | 进程发 sd_notify(READY=1) | 主动通知就绪 |
| **dbus** | 占了 BusName 即 ready | DBus 服务 |
| **exec** | exec 调用完成 | 类似 simple |

### 1.3 Drop-in（覆盖默认配置）

```bash
# 不动原 unit，叠加覆盖
mkdir -p /etc/systemd/system/myapp.service.d/
cat > /etc/systemd/system/myapp.service.d/override.conf <<EOF
[Service]
Environment="LOG_LEVEL=debug"
MemoryMax=4G
EOF
systemctl daemon-reload && systemctl restart myapp

# 编辑器方式
systemctl edit myapp                    # 创建 override
systemctl edit --full myapp             # 编辑完整

# 看最终生效配置
systemctl show myapp | grep -E "LOG_LEVEL|MemoryMax"
systemctl cat myapp                     # 看所有片段
```

### 1.4 systemd Timer（替代 cron）

```ini
# /etc/systemd/system/backup.service
[Unit]
Description=Daily backup

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
User=backup
```

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Run backup daily

[Timer]
OnCalendar=daily                         # 每天 00:00
# OnCalendar=*-*-* 02:30:00
# OnCalendar=Mon..Fri 09:00
# OnBootSec=15min                        # 启动后 15min
# OnUnitActiveSec=1h                     # 上次完成 1h 后
RandomizedDelaySec=10min                 # 随机延迟，避免雪崩
Persistent=true                           # 错过补跑
Unit=backup.service

[Install]
WantedBy=timers.target
```

```bash
systemctl enable --now backup.timer
systemctl list-timers --all
systemd-analyze calendar "Mon..Fri 09:00"

# vs cron 优势:
# - 日志统一进 journald
# - 失败自动重启
# - 随机化避免雪崩
# - 依赖系统状态（如等网络）
```

### 1.5 安全沙箱（必上）

```ini
[Service]
# 沙箱
NoNewPrivileges=true                     # 不能 sudo 提权
PrivateTmp=true                          # 独立 /tmp
ProtectSystem=strict                     # /usr /etc 只读
ProtectHome=true                         # /home 不可见
ReadWritePaths=/var/lib/myapp /var/log/myapp
PrivateDevices=true                      # 屏蔽 /dev
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# 网络
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

# 系统调用过滤
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# Capability
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
```

```bash
# 验证沙箱
systemd-analyze security myapp
# 给一个 0-10 分（Exposure level），越低越安全
```

### 1.6 启动分析

```bash
systemd-analyze                          # 启动总耗时
systemd-analyze blame                    # 各服务耗时
systemd-analyze critical-chain           # 关键路径
systemd-analyze plot > boot.svg          # 启动甘特图
systemd-analyze verify myapp.service     # 验证 unit 语法
```

## 二、ACL 与 Capability

### 2.1 ACL（细粒度权限）

```bash
# 标准 rwx 不够时（多用户共享场景）

# 启用（xfs/ext4 默认支持）
mount -o remount,acl /

# 设置
setfacl -m u:alice:rwx /data
setfacl -m g:devs:rx /data
setfacl -Rm u:alice:rwx /data            # 递归
setfacl -d -m u:alice:rwx /data          # 默认 ACL（继承到子项）

# 查看
getfacl /data
ls -l /data                              # rwxr-x---+ 末尾 + 表示有 ACL

# 删除
setfacl -x u:alice /data
setfacl -b /data                         # 删全部 ACL
```

### 2.2 Capability（细粒度 root）

```bash
# 替代 setuid 的安全方案
# 让程序拥有特定 root 权限而不是全 root

# 看
getcap /usr/bin/ping
# /usr/bin/ping cap_net_raw=ep

# 设置
setcap cap_net_bind_service=+ep /usr/local/bin/myapp    # 允许绑 <1024
setcap cap_net_admin,cap_net_raw=+ep /usr/local/bin/tool

# 删除
setcap -r /usr/bin/ping

# 常用 capability:
# CAP_NET_BIND_SERVICE   绑定 < 1024 端口
# CAP_NET_ADMIN          网络管理
# CAP_NET_RAW            raw socket
# CAP_SYS_ADMIN          系统管理（万能 root）
# CAP_DAC_OVERRIDE       绕过 DAC 检查
# CAP_SYS_PTRACE         追踪
# CAP_KILL               kill 任意进程

# 当前进程
capsh --print
cat /proc/self/status | grep Cap
```

### 2.3 sudo 进阶

```bash
# /etc/sudoers
# Defaults
Defaults env_reset
Defaults timestamp_timeout=15            # 15min 免密
Defaults logfile=/var/log/sudo.log
Defaults !visiblepw
Defaults requiretty                      # 必须有 tty

# 别名（推荐）
User_Alias DEVOPS = alice, bob, charlie
Cmnd_Alias RESTART_WEB = /usr/bin/systemctl restart nginx, /usr/bin/systemctl reload nginx
Cmnd_Alias READ_LOGS = /usr/bin/journalctl, /usr/bin/tail
Host_Alias WEBSERVERS = web1, web2, web3

DEVOPS WEBSERVERS=(ALL) NOPASSWD: RESTART_WEB, READ_LOGS

# 配置文件分割（推荐）
# /etc/sudoers.d/devops
%devops ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx

# 测试
sudo visudo -c
sudo -l                                  # 看自己有什么权限
sudo -lU alice                           # 看 alice 有什么权限
```

## 三、SELinux / AppArmor

### 3.1 SELinux（RHEL 系）

```bash
# 状态
getenforce                                # Enforcing / Permissive / Disabled
sestatus

# 临时切换
setenforce 0                              # Permissive
setenforce 1                              # Enforcing

# 永久（/etc/selinux/config）
SELINUX=enforcing                         # 不要 disabled

# 看上下文
ls -Z /var/www/html
ps -eZ | grep nginx
id -Z

# 改 context
chcon -t httpd_sys_content_t /var/www/html/index.html
restorecon -Rv /var/www/html             # 按默认恢复

# 持久化 context 规则
semanage fcontext -a -t httpd_sys_content_t "/data(/.*)?"
restorecon -Rv /data

# 端口
semanage port -l | grep http
semanage port -a -t http_port_t -p tcp 8888

# 布尔值（常用快开关）
getsebool -a | grep httpd
setsebool -P httpd_can_network_connect on

# 故障排查
ausearch -m AVC -ts recent               # SELinux 拒绝
sealert -a /var/log/audit/audit.log      # 友好分析
journalctl -t setroubleshoot

# 常见调整脚本
yum install setroubleshoot-server
```

### 3.2 AppArmor（Ubuntu/SUSE）

```bash
aa-status                                 # 状态
ls /etc/apparmor.d/                       # profile 位置

# 管理
aa-enforce /etc/apparmor.d/usr.sbin.nginx
aa-complain /etc/apparmor.d/usr.sbin.nginx   # 仅警告
aa-disable /etc/apparmor.d/usr.sbin.nginx

# 自动生成
aa-genprof /path/to/myapp
aa-logprof                                # 学习模式

# 看拒绝
journalctl -k | grep DENIED
dmesg | grep apparmor
```

## 四、存储栈（LVM + RAID + XFS）

### 4.1 LVM 概念与流程

```
PV (Physical Volume)   物理卷 = 一块磁盘/分区
VG (Volume Group)      卷组 = 多个 PV 池化
LV (Logical Volume)    逻辑卷 = 从 VG 切出的"虚拟分区"

优势:
  - 动态扩缩容
  - 快照
  - 跨磁盘聚合
  - thin provisioning
```

### 4.2 LVM 标准流程

```bash
# 1. 准备 PV
pvcreate /dev/sdb /dev/sdc
pvs                                       # 简洁
pvdisplay                                  # 详细

# 2. 创建 VG
vgcreate vg_data /dev/sdb /dev/sdc
vgs
vgextend vg_data /dev/sdd                 # 加盘
vgreduce vg_data /dev/sdd                 # 移除（需先 pvmove）

# 3. 创建 LV
lvcreate -L 100G -n lv_logs vg_data
lvcreate -l 100%FREE -n lv_data vg_data   # 用全部空间
lvcreate -L 50G -n lv_mirror -m1 vg_data  # 镜像 (RAID-1)
lvcreate -L 100G -n lv_stripe -i 2 vg_data # 条带 (RAID-0, 2 盘)

# 4. 格式化 + 挂载
mkfs.xfs /dev/vg_data/lv_logs
mkdir /var/log/app
mount /dev/vg_data/lv_logs /var/log/app

# 5. 写入 /etc/fstab
echo "/dev/vg_data/lv_logs /var/log/app xfs defaults,noatime 0 0" >> /etc/fstab
```

### 4.3 LVM 扩缩容

```bash
# 扩容（在线，ext4/xfs/btrfs）
lvextend -L +50G /dev/vg_data/lv_logs
lvextend -l +100%FREE /dev/vg_data/lv_logs   # 用剩余

# 同时扩文件系统
lvextend -r -L +50G /dev/vg_data/lv_logs  # -r 自动 resize fs
# 或分两步
lvextend -L +50G /dev/vg_data/lv_logs
xfs_growfs /var/log/app                    # XFS
resize2fs /dev/vg_data/lv_logs              # ext4

# 缩容（XFS 不支持！只能 ext4）
umount /var/log/app
e2fsck -f /dev/vg_data/lv_logs
resize2fs /dev/vg_data/lv_logs 80G          # 先缩 fs
lvreduce -L 80G /dev/vg_data/lv_logs        # 再缩 LV
mount /var/log/app
```

### 4.4 LVM 快照

```bash
# 创建（CoW）
lvcreate -L 10G -s -n snap1 /dev/vg_data/lv_data
# -L 10G = 预留 10G 给 CoW 数据

# 挂载并备份
mkdir /mnt/snap
mount /dev/vg_data/snap1 /mnt/snap
rsync -av /mnt/snap/ /backup/
umount /mnt/snap

# 删除
lvremove /dev/vg_data/snap1

# 回滚
lvconvert --merge /dev/vg_data/snap1     # 下次重启自动 merge
```

### 4.5 软 RAID（mdadm）

```bash
# 创建 RAID-10
mdadm --create /dev/md0 --level=10 --raid-devices=4 /dev/sd[b-e]

# 状态
cat /proc/mdstat
mdadm --detail /dev/md0
mdadm --examine /dev/sdb

# 保存配置（不然重启认不出）
mdadm --detail --scan >> /etc/mdadm.conf        # RHEL
mdadm --detail --scan >> /etc/mdadm/mdadm.conf  # Ubuntu
update-initramfs -u                              # Ubuntu

# 故障盘处理
mdadm /dev/md0 --fail /dev/sdb
mdadm /dev/md0 --remove /dev/sdb
mdadm /dev/md0 --add /dev/sdb            # 加入（自动 rebuild）

# 重建监控
watch cat /proc/mdstat

# 增加盘数（RAID-5/6 reshape）
mdadm --add /dev/md0 /dev/sdf
mdadm --grow /dev/md0 --raid-devices=5
```

### 4.6 XFS 实战

```bash
# 创建
mkfs.xfs -f /dev/sdb1
mkfs.xfs -L data -d agcount=8 -l size=64m /dev/sdb1

# 信息
xfs_info /mountpoint
xfs_db -r -c "sb 0" -c "p" /dev/sdb1

# 扩容（仅扩，不能缩）
xfs_growfs /mountpoint

# 修复（卸载后）
xfs_repair /dev/sdb1
xfs_repair -L /dev/sdb1                  # 强制清 log（数据丢失风险）

# 配额（XFS 项目配额）
mount -o uquota,gquota,pquota /dev/sdb1 /data
xfs_quota -x -c 'limit bsoft=10g bhard=11g alice' /data

# 项目配额（按目录配额）
echo "10:/data/project_a" >> /etc/projects
echo "project_a:10" >> /etc/projid
xfs_quota -x -c 'project -s project_a' /data
xfs_quota -x -c 'limit -p bsoft=10g bhard=12g project_a' /data
```

### 4.7 网络存储

```bash
# NFS 服务端
dnf install nfs-utils
systemctl enable --now nfs-server

# /etc/exports
/data 192.168.1.0/24(rw,sync,no_root_squash,no_subtree_check)

exportfs -ra                              # 重载

# NFS 客户端
showmount -e nfs-srv
mount -t nfs -o vers=4.1 nfs-srv:/data /mnt/data

# fstab
nfs-srv:/data /mnt/data nfs defaults,_netdev,vers=4.1,hard,intr 0 0

# CIFS / SMB
mount -t cifs //smb-srv/share /mnt/smb \
  -o credentials=/etc/samba/creds,vers=3.0,uid=alice
```

## 五、网络配置

### 5.1 NetworkManager（RHEL/Ubuntu 桌面）

```bash
nmcli                                     # 全局
nmcli device status
nmcli connection show

# 创建静态 IP
nmcli connection add type ethernet con-name eth0-static ifname eth0 \
  ipv4.method manual \
  ipv4.addresses 192.168.1.10/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "8.8.8.8 1.1.1.1"

nmcli connection up eth0-static

# 修改
nmcli connection modify eth0-static ipv4.dns "114.114.114.114"
nmcli connection reload
nmcli connection up eth0-static
```

### 5.2 netplan（Ubuntu 服务器）

```yaml
# /etc/netplan/01-static.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses: [192.168.1.10/24]
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
      mtu: 1500
  bonds:
    bond0:
      interfaces: [eth1, eth2]
      parameters:
        mode: 802.3ad                     # LACP
        mii-monitor-interval: 100
      addresses: [10.0.0.10/24]
  vlans:
    vlan100:
      id: 100
      link: bond0
      addresses: [10.100.0.10/24]
```

```bash
netplan generate                          # 生成 backend 配置
netplan try                                # 测试 2 分钟自动回滚
netplan apply                              # 应用
```

### 5.3 IP / iproute2 完整命令

```bash
# 接口
ip a; ip -br a
ip link set eth0 up|down
ip link set eth0 mtu 9000                  # Jumbo Frame

# 地址
ip addr add 192.168.1.10/24 dev eth0
ip addr del 192.168.1.10/24 dev eth0

# 路由
ip route
ip route add default via 192.168.1.1
ip route add 10.0.0.0/8 via 192.168.1.254
ip route del 10.0.0.0/8
ip route get 8.8.8.8                       # 看走哪条

# ARP / 邻居
ip neigh
ip neigh flush all

# 命名空间
ip netns add ns1
ip netns exec ns1 ip a
ip netns del ns1
```

### 5.4 防火墙

```bash
# firewalld (RHEL/openEuler)
firewall-cmd --list-all
firewall-cmd --add-service=http --permanent
firewall-cmd --add-port=8080/tcp --permanent
firewall-cmd --add-rich-rule='rule family=ipv4 source address=1.2.3.4 reject' --permanent
firewall-cmd --reload

# ufw (Ubuntu)
ufw status
ufw allow 80/tcp
ufw allow from 1.2.3.0/24 to any port 22
ufw enable

# iptables / nftables 详见高级章
```

### 5.5 DNS

```bash
# 解析
dig example.com
dig +trace example.com                     # 完整解析链
dig @8.8.8.8 example.com +short
host example.com

# 系统配置
cat /etc/resolv.conf                       # 当前 DNS

# systemd-resolved
systemd-resolve --status
resolvectl dns                              # 各接口 DNS
resolvectl statistics
resolvectl flush-caches

# 配置 /etc/systemd/resolved.conf
[Resolve]
DNS=8.8.8.8 1.1.1.1
FallbackDNS=114.114.114.114

# 修改 /etc/hosts （静态映射）
1.2.3.4    api.internal
```

## 六、调优入门（核心 sysctl）

### 6.1 配置方式

```bash
# 临时
sysctl -w net.ipv4.ip_forward=1

# 持久化（推荐）
cat > /etc/sysctl.d/99-tuning.conf <<EOF
vm.swappiness = 10
net.core.somaxconn = 65535
EOF

sysctl --system

# 当前值
sysctl -a | grep somaxconn
cat /proc/sys/net/core/somaxconn
```

### 6.2 通用基础

```ini
# /etc/sysctl.d/99-base.conf
# 文件句柄
fs.file-max = 2097152
fs.nr_open = 1048576
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 8192

# 进程
kernel.pid_max = 4194304

# Panic
kernel.panic = 10                          # 10s 自动重启

# 网络
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 600
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq

# 内存
vm.swappiness = 10
vm.overcommit_memory = 1
vm.max_map_count = 262144                  # ES/Redis 必加
```

### 6.3 ulimit（进程级）

```bash
# /etc/security/limits.conf
*        soft   nofile   65535
*        hard   nofile   65535
*        soft   nproc    65535
*        hard   nproc    65535
mysql    soft   memlock  unlimited
mysql    hard   memlock  unlimited

# systemd 服务
# /etc/systemd/system/myapp.service.d/limits.conf
[Service]
LimitNOFILE=1048576
LimitNPROC=65535
LimitMEMLOCK=infinity

# systemd 默认
# /etc/systemd/system.conf
[Manager]
DefaultLimitNOFILE=1048576

# 验证
ulimit -a                                  # 当前 shell
cat /proc/PID/limits                       # 进程
```

### 6.4 tuned profile（RHEL/openEuler 推荐）

```bash
tuned-adm list
tuned-adm active
tuned-adm profile throughput-performance    # 服务器
tuned-adm profile latency-performance       # 低延迟
tuned-adm profile virtual-host              # KVM 宿主
tuned-adm profile virtual-guest             # 虚拟机内

# 自定义
mkdir /etc/tuned/myprofile
cat > /etc/tuned/myprofile/tuned.conf <<EOF
[main]
include=throughput-performance

[sysctl]
net.ipv4.tcp_congestion_control=bbr
vm.swappiness=1

[vm]
transparent_hugepages=never
EOF
tuned-adm profile myprofile
```

## 七、Shell 中级

### 7.1 严格模式（必加）

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# -e  任一命令失败立即退出
# -u  使用未定义变量报错
# -o pipefail  管道中任一失败整体失败
# IFS  防止文件名空格被分词
```

### 7.2 函数 + local + main 模式

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly LOG=/var/log/myscript.log

log() {
    echo "[$(date '+%F %T')] $*" | tee -a "$LOG"
}

backup_db() {
    local db_name="${1:?需要 db_name}"
    log "Backing up $db_name"
    mysqldump --single-transaction "$db_name" > "/backup/$db_name-$(date +%F).sql"
}

main() {
    backup_db "production"
    backup_db "analytics"
    log "✅ Done"
}

main "$@"
```

### 7.3 参数解析（getopts）

```bash
#!/bin/bash
usage() {
    cat <<EOF
Usage: $0 [-h] [-v] [-o OUTPUT] INPUT
EOF
    exit 0
}

verbose=0
output=""

while getopts "hvo:" opt; do
    case $opt in
        h) usage ;;
        v) verbose=1 ;;
        o) output="$OPTARG" ;;
        \?) echo "Invalid: -$OPTARG"; exit 1 ;;
        :) echo "Option -$OPTARG requires value"; exit 1 ;;
    esac
done
shift $((OPTIND-1))

input=$1
[[ -z "$input" ]] && usage
```

### 7.4 trap + 清理

```bash
TMPDIR=$(mktemp -d)
LOCK=/var/lock/myapp.lock

cleanup() {
    local exit_code=$?
    rm -rf "$TMPDIR"
    rm -f "$LOCK"
    echo "Cleanup done, exit=$exit_code"
}
trap cleanup EXIT INT TERM

# 错误捕获
on_error() {
    local code=$1 line=$2 cmd="$3"
    echo "[ERROR] code=$code line=$line cmd=$cmd" >&2
}
set -E
trap 'on_error $? $LINENO "$BASH_COMMAND"' ERR
```

### 7.5 重试与超时

```bash
retry() {
    local attempts=${1:-3} delay=${2:-2}
    shift 2
    local i=0
    while (( i < attempts )); do
        if "$@"; then return 0; fi
        i=$((i + 1))
        echo "Attempt $i/$attempts failed, retry in ${delay}s..." >&2
        sleep $delay
        delay=$((delay * 2))                # 指数退避
    done
    return 1
}

retry 5 2 curl -sf http://api/health
timeout 10s slow_command
```

### 7.6 文件锁（防重入）

```bash
LOCKFILE=/var/run/myscript.lock

(
    flock -n 9 || { echo "已有实例在运行"; exit 1; }
    
    # 临界区
    do_work
) 9>"$LOCKFILE"
```

### 7.7 文本处理 oneliner

```bash
# top-N IP
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head

# 状态码统计
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# 各状态码占比
awk '{print $9}' access.log | sort | uniq -c | awk '{print $2, $1/'"$(wc -l < access.log)"'*100"%"}'

# 慢请求 top
awk '$NF > 1.0 {print $7, $NF}' access.log | sort -k2 -rn | head

# 看某文件每行长度分布
awk '{print length}' file | sort -n | uniq -c

# 提取 JSON 字段
curl -s api/users | jq -r '.[] | "\(.id) \(.name)"'

# YAML 处理
yq '.spec.containers[0].image' pod.yaml
```

## 八、定时任务进阶

### 8.1 cron 进阶

```bash
# 多种语法
@reboot                     /script.sh    # 启动时
@daily                      /script.sh    # = 0 0 * * *
@hourly
@weekly
@monthly

# 用户级 vs 系统级
crontab -e                                  # 用户级
/etc/crontab                                # 系统（含用户字段）
/etc/cron.d/myapp                          # 应用专用
/etc/cron.daily/myapp                       # 直接放脚本

# 日志输出
0 2 * * * /script.sh > /var/log/script.log 2>&1
0 2 * * * /script.sh 2>&1 | logger -t myscript
```

### 8.2 systemd timer vs cron 优势

```
systemd timer:
  ✅ 日志统一进 journald
  ✅ 失败自动重启
  ✅ 依赖系统状态
  ✅ 随机化避免雪崩
  ✅ Persistent=true 错过补跑
  ✅ 显式 service unit 复用

cron:
  ✅ POSIX 通用
  ✅ 简洁直接
  ❌ 日志分散
  ❌ 无依赖管理
```

## 九、备份基础

### 9.1 rsync 实战

```bash
# 本地
rsync -avh --delete src/ dst/

# 远程
rsync -avhP -e "ssh -p 22" src/ user@host:/dst/

# 增量 + 排除
rsync -avh --delete \
  --exclude=*.tmp --exclude=cache/ \
  src/ dst/

# 关键 flag
-a    archive (=-rlptgoD)
-v    verbose
-h    human-readable
-P    --progress + --partial
--delete    删除 dst 多余
--link-dest=/old/backup   硬链接到旧备份
--bwlimit=10M             限速
-z    压缩传输
```

### 9.2 restic（推荐）

```bash
# 初始化
export RESTIC_REPOSITORY=s3:s3.amazonaws.com/bucket/backup
export RESTIC_PASSWORD=*** init

# 备份
restic backup /data /etc --exclude=/data/cache --tag prod

# 列快照
restic snapshots
restic stats

# 恢复
restic restore latest --target /restore --include /data

# 保留策略
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune
```

### 9.3 数据库备份

```bash
# MySQL
mysqldump --single-transaction --routines --triggers --events \
  --all-databases > /backup/mysql-$(date +%F).sql
gzip /backup/mysql-*.sql

# PostgreSQL
pg_dumpall > /backup/pg-$(date +%F).sql
pg_dump dbname | gzip > /backup/dbname-$(date +%F).sql.gz

# Redis
redis-cli BGSAVE
redis-cli --rdb /backup/dump-$(date +%F).rdb
```

## 十、时间同步与时区

### 10.1 chrony（推荐）

```bash
# /etc/chrony.conf
server ntp.aliyun.com iburst
server cn.pool.ntp.org iburst
pool 2.cn.pool.ntp.org iburst

driftfile /var/lib/chrony/drift
makestep 1.0 3                              # 启动后强制对齐
rtcsync                                      # 同步到 RTC
allow 192.168.0.0/16                         # 允许子网作为客户端

systemctl enable --now chronyd

# 命令
chronyc sources -v                           # 各源状态
chronyc tracking                             # 当前状态
chronyc makestep                              # 立即强制对齐
chronyc -a 'burst 4/4'                       # 突发同步
```

## 十一、引导与内核入门

### 11.1 GRUB2

```bash
# 配置 /etc/default/grub
GRUB_TIMEOUT=5
GRUB_CMDLINE_LINUX="quiet rhgb"             # 内核参数

# 应用
grub2-mkconfig -o /boot/grub2/grub.cfg     # RHEL
update-grub                                  # Ubuntu

# 设置默认启动条目
grub2-set-default 0
grub2-editenv list
```

### 11.2 内核管理

```bash
uname -r                                     # 当前内核
ls /boot/vmlinuz-*                           # 已装内核
dnf list installed kernel
apt list --installed | grep linux-image

# 清理旧内核
dnf remove --oldinstallonly --setopt installonly_limit=2 kernel
apt autoremove --purge

# 模块
lsmod
modinfo nvidia
modprobe br_netfilter
modprobe -r nvidia                           # 卸载
echo br_netfilter > /etc/modules-load.d/k8s.conf    # 持久化

# 黑名单
cat > /etc/modprobe.d/blacklist-nouveau.conf <<EOF
blacklist nouveau
EOF
dracut --force                                # RHEL 重建 initramfs
update-initramfs -u                           # Ubuntu
```

## 十二、典型坑（进阶）

| 坑 | 建议 |
|:---|:---|
| **改 unit 没 daemon-reload** | 肌肉记忆 |
| **service Type 选错** | nginx/php-fpm 用 forking, 大多 simple |
| **LVM 扩容忘扩 fs** | `-r` 标志或分两步 |
| **XFS 不能缩** | 设计时多留 20% |
| **mdadm 没保存 config** | mdadm.conf + initramfs |
| **NetworkManager + ifcfg 混用** | 选一个 |
| **改 sysctl 没持久化** | /etc/sysctl.d/*.conf |
| **PAM 不加载 limits** | session required pam_limits.so |
| **SELinux 一律 disabled** | RHEL 系尽量 enforcing |
| **`sudo vi /etc/sudoers`** | 必须 visudo |
| **GRUB 改了没 mkconfig** | 必走 grub2-mkconfig |
| **fstab 写错重启起不来** | mount -a 测试 |

## 十三、进阶 Checklist

```
systemd:
☐ 写过自定义 service
☐ 用过 Drop-in 覆盖
☐ 用过 timer 替代 cron
☐ 配过沙箱（NoNewPrivileges 等）
☐ systemd-analyze 分析过启动

存储:
☐ LVM 创建 + 扩容 + 快照
☐ mdadm 软 RAID-1 / 10
☐ XFS / ext4 区别清楚
☐ /etc/fstab 配置过
☐ NFS / CIFS 挂载

权限:
☐ ACL 用过
☐ Capability 替代 setuid
☐ sudoers 别名
☐ SELinux 看过 ausearch

网络:
☐ 静态 IP 配置（NM / netplan）
☐ bond / VLAN
☐ firewalld / ufw 加规则
☐ resolved 配 DNS

调优:
☐ /etc/sysctl.d/*.conf
☐ /etc/security/limits.conf
☐ tuned profile
☐ noatime 挂载

Shell:
☐ 严格模式 set -euo pipefail
☐ 函数 + local + main
☐ getopts 参数
☐ trap 清理
☐ retry + flock
☐ shellcheck 通过

备份:
☐ rsync 增量
☐ restic / 数据库 dump
☐ systemd timer 自动化
```

## 十四、推荐栈

```
init:             systemd
日志:             journald + rsyslog → Loki
网络:             netplan (Ubuntu) / NetworkManager (RHEL)
存储:             LVM + XFS / ext4
RAID:             mdadm 或 硬 RAID
备份:             restic + S3
时间:             chrony
DNS:              systemd-resolved
安全模块:         SELinux (RHEL) / AppArmor (Ubuntu)
调优:             tuned profile + sysctl.d
Shell:            bash + shellcheck
```

## 十五、学习路径

```
进阶（3 月）:
  1. 写出生产级 systemd unit + timer
  2. LVM 全套（PV/VG/LV + 快照 + 扩容）
  3. mdadm 软 RAID
  4. ACL + Capability 替代 setuid
  5. SELinux/AppArmor 基础
  6. netplan / NetworkManager 静态 IP
  7. firewalld / ufw
  8. /etc/sysctl.d/ 持久化
  9. tuned profile
  10. Shell 中级（trap/getopts/flock/retry）
  11. restic 备份 + systemd timer
  12. shellcheck 干净通过
```

## 十六、参考资料

```
官方:
  - systemd 文档: freedesktop.org/wiki/Software/systemd/
  - Red Hat Storage Administration Guide
  - Ubuntu Server Guide
  - LVM HOWTO

书籍:
  - 《鸟哥的 Linux 私房菜 服务器篇》
  - 《Linux 系统管理技术手册》
  - 《Linux 命令行与 Shell 脚本编程大全》

教程:
  - DigitalOcean Tutorials
  - linuxconfig.org
  - Red Hat 官方培训
```

> 📖 **核心判断**：进阶 = **systemd 写出生产 unit + LVM 全套 + ACL/Capability + SELinux 不 disabled + sysctl.d 调优 + Shell 严格模式**。能独立处理 50 台服务器、能写 200 行带锁带 retry 的 Shell 脚本、能解释 LVM 扩容流程，就具备高级章资格。

