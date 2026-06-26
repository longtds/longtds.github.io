# 系统管理

> Linux 系统管理 = **systemd（一切服务的入口）+ 用户权限（最小特权）+ 包管理（DNF/APT/RPM）+ 日志（journald）+ 网络（NetworkManager/netplan）+ 安全模块（SELinux/AppArmor）**。这六块是运维日常 80% 时间打交道的核心。

## 一、systemd（必精通）

### 1.1 核心概念

```
systemd 是 PID 1，统一管理:
  - service     服务
  - socket      套接字（按需启动）
  - target      运行级别（=runlevel）
  - timer       定时任务（替代 cron）
  - mount       挂载点
  - automount   自动挂载
  - swap        交换
  - path        路径监控
  - slice       cgroup 资源组
  - scope       外部进程纳管

单元文件位置:
  /usr/lib/systemd/system/   软件包提供的（不要改）
  /etc/systemd/system/        管理员覆盖（优先级高）
  ~/.config/systemd/user/     用户级
```

### 1.2 常用命令矩阵

```bash
# 服务管理
systemctl start|stop|restart|reload|status nginx
systemctl enable|disable nginx              # 开机自启
systemctl enable --now nginx                 # 启用+启动
systemctl mask|unmask nginx                  # 禁用到任何方式都启不了
systemctl is-active|is-enabled|is-failed nginx
systemctl reset-failed nginx                 # 重置失败状态

# 列出
systemctl list-units --type=service           # 当前运行
systemctl list-units --type=service --all     # 全部
systemctl list-unit-files --state=enabled    # 开机自启的
systemctl list-dependencies nginx             # 依赖树
systemctl list-sockets                        # 所有 socket
systemctl list-timers                         # 所有 timer

# 配置
systemctl cat nginx                          # 看 unit 文件
systemctl edit nginx                         # 编辑 override (drop-in)
systemctl edit --full nginx                  # 编辑完整
systemctl daemon-reload                      # 改了 unit 必须 reload

# 启动级别 (替代 runlevel)
systemctl get-default                        # 默认 target
systemctl set-default multi-user.target      # 服务器无 GUI
systemctl isolate rescue.target              # 临时切换

# 关机/重启
systemctl reboot
systemctl poweroff
systemctl suspend
systemctl rescue                              # 救援模式
systemctl emergency                           # 紧急模式

# 分析启动
systemd-analyze                              # 总耗时
systemd-analyze blame                        # 各服务耗时排序 ⭐
systemd-analyze critical-chain                # 关键路径
systemd-analyze plot > boot.svg               # 启动甘特图
systemd-analyze verify nginx.service         # 验证 unit 语法
```

### 1.3 编写自定义 service

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application
Documentation=https://docs.example.com
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service                   # 强依赖（postgresql 挂它也停）

[Service]
Type=simple                                   # simple/forking/oneshot/notify/dbus
ExecStartPre=/bin/mkdir -p /var/log/myapp
ExecStart=/usr/local/bin/myapp --config /etc/myapp.conf
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill -TERM $MAINPID
Restart=on-failure                             # always/on-failure/on-abnormal/no
RestartSec=5s
TimeoutStartSec=60
TimeoutStopSec=30

# 运行环境
User=myapp
Group=myapp
WorkingDirectory=/var/lib/myapp
Environment="LOG_LEVEL=info" "APP_ENV=prod"
EnvironmentFile=-/etc/myapp/env              # - 表示文件不存在不报错

# 资源限制
LimitNOFILE=65536                             # ulimit -n
LimitNPROC=4096                               # ulimit -u
MemoryMax=2G
CPUQuota=200%                                 # 2 个 CPU
TasksMax=512

# 安全加固（生产推荐）
NoNewPrivileges=true                          # 不能 sudo 提权
PrivateTmp=true                               # 独立 /tmp
ProtectSystem=strict                          # /usr /etc 只读
ProtectHome=true                              # /home 不可见
ReadWritePaths=/var/lib/myapp /var/log/myapp
PrivateDevices=true                           # 屏蔽 /dev
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
SystemCallFilter=@system-service              # systemd 自带白名单
CapabilityBoundingSet=CAP_NET_BIND_SERVICE   # 仅允许绑定低端口
AmbientCapabilities=CAP_NET_BIND_SERVICE

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myapp

[Install]
WantedBy=multi-user.target
```

```bash
# Drop-in 覆盖（不改原 unit）
mkdir -p /etc/systemd/system/myapp.service.d/
cat > /etc/systemd/system/myapp.service.d/override.conf <<EOF
[Service]
Environment="LOG_LEVEL=debug"
MemoryMax=4G
EOF
systemctl daemon-reload && systemctl restart myapp
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
OnCalendar=daily                              # 每天 00:00
# 或 OnCalendar=*-*-* 02:30:00               # 每天 2:30
# 或 OnCalendar=Mon..Fri 09:00               # 工作日 9 点
# OnBootSec=15min                             # 启动后 15min
# OnUnitActiveSec=1h                          # 上次完成 1h 后
RandomizedDelaySec=10min                      # 随机延迟，避免雪崩
Persistent=true                                # 错过的也补跑
Unit=backup.service

[Install]
WantedBy=timers.target
```

```bash
systemctl enable --now backup.timer
systemctl list-timers                         # 看下次执行

# 调试
systemd-analyze calendar "Mon..Fri 09:00"
# 输出：next elapse 时间

# vs cron 优势:
# - 日志统一进 journald
# - 失败自动重启
# - 依赖系统状态（如等网络）
# - 随机化避免雪崩
```

### 1.5 systemd-resolved / networkd

```bash
# 现代 distro 默认用 systemd-resolved 解析 DNS
systemd-resolve --status                      # 查看 DNS 配置
resolvectl dns                                # 各接口 DNS
resolvectl statistics                         # 查询统计
resolvectl flush-caches                       # 清 DNS 缓存

# 配置 /etc/systemd/resolved.conf
[Resolve]
DNS=8.8.8.8 1.1.1.1
FallbackDNS=114.114.114.114
DNSStubListener=yes
Cache=yes
```

## 二、用户与权限

### 2.1 用户管理

```bash
# 创建/修改/删除
useradd -m -s /bin/bash -G docker,wheel alice  # -m 建 home, -G 附加组
usermod -aG docker bob                          # 加入组（必须 -a 追加）
usermod -L|-U user                              # 锁定/解锁
userdel -r user                                  # -r 同时删 home

# 密码
passwd alice
passwd -l user                                   # 锁密码
passwd -e user                                   # 强制下次登录改
chage -l user                                    # 看密码策略
chage -M 90 -W 7 user                            # 90 天过期，7 天前警告

# 系统账户
useradd -r -s /sbin/nologin -d /var/lib/myapp myapp   # 服务账户

# 切换/sudo
su - user                                        # 完整环境
sudo -u user command
sudo -i                                          # root shell
sudo -l                                          # 看自己有哪些 sudo 权限

# 谁在登录
who; w; last; lastlog
loginctl                                          # systemd 会话
```

### 2.2 文件权限

```bash
# 基础
chmod 755 file                                   # rwxr-xr-x
chmod u+x,g-w,o= file                            # 符号
chmod -R 644 dir                                  # 递归

# 特殊位
chmod 4755 file     # setuid (+s on owner)        # 以文件所有者运行
chmod 2755 file     # setgid (+s on group)
chmod 1777 dir      # sticky bit (t)              # /tmp 用，只能删自己的

# 所有权
chown user:group file
chown -R alice:devs /data
chgrp devs file

# umask (新建文件默认权限)
umask                                            # 默认 022 → 文件 644 目录 755
umask 027                                         # 同组可读 / 他人无权限

# 看权限
ls -l
stat file
namei -l /path/to/file                            # 整条路径权限
```

### 2.3 ACL（细粒度权限）

```bash
# 启用 ACL (xfs/ext4 默认支持)
mount -o remount,acl /

# 设置 ACL
setfacl -m u:alice:rwx /data
setfacl -m g:devs:rx /data
setfacl -Rm u:alice:rwx /data                    # 递归
setfacl -d -m u:alice:rwx /data                  # 默认 ACL（继承到子项）

# 查看
getfacl /data

# 删除
setfacl -x u:alice /data
setfacl -b /data                                  # 删除所有 ACL

# 注意：ls -l 出现 "+" 表示有 ACL
ls -l /data
# drwxrwx---+  ← + 表示有 ACL
```

### 2.4 Capabilities（细粒度 root）

```bash
# 替代 setuid 的安全方案
# 让程序拥有特定 root 权限而不是全 root

# 看
getcap /usr/bin/ping
# /usr/bin/ping cap_net_raw=ep

# 设置
setcap cap_net_bind_service=+ep /usr/local/bin/myapp    # 允许绑 <1024 端口
setcap cap_net_admin,cap_net_raw=+ep /usr/local/bin/tool

# 删除
setcap -r /usr/bin/ping

# 列表
capsh --print

# 常用 capability:
# CAP_NET_BIND_SERVICE   绑定 < 1024 端口
# CAP_NET_ADMIN          网络管理
# CAP_NET_RAW            raw socket
# CAP_SYS_ADMIN          系统管理（万能 root）
# CAP_DAC_OVERRIDE       绕过 DAC 检查
# CAP_SYS_PTRACE         追踪
# CAP_KILL               kill 任意进程
```

### 2.5 sudo 配置

```bash
# /etc/sudoers (用 visudo 编辑)
# 用户        主机=(切换为) NOPASSWD: 命令
alice         ALL=(ALL) ALL                        # 完全 root
%wheel        ALL=(ALL) ALL                        # wheel 组所有人
bob           ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
deploy        ALL=(www-data) NOPASSWD: ALL         # 只能切到 www-data

# Defaults
Defaults env_reset
Defaults timestamp_timeout=15                       # 15min 免密
Defaults logfile=/var/log/sudo.log
Defaults !visiblepw
Defaults requiretty                                  # 必须有 tty

# 别名
User_Alias DEVOPS = alice, bob, charlie
Cmnd_Alias RESTART_WEB = /usr/bin/systemctl restart nginx, /usr/bin/systemctl reload nginx
DEVOPS ALL=(ALL) NOPASSWD: RESTART_WEB

# 测试配置
sudo visudo -c
```

## 三、进程管理

### 3.1 查看进程

```bash
# ps
ps aux                                            # BSD 风格
ps -ef                                            # System V 风格
ps -eo pid,ppid,user,%cpu,%mem,rss,stat,start,time,cmd --sort=-%cpu | head -20
ps --forest -ef                                   # 树形

# pgrep / pkill
pgrep -fl nginx
pgrep -u alice
pkill -SIGTERM -u alice                            # 杀某用户所有进程

# top
top
top -p $(pgrep -d',' nginx)                       # 监控特定进程
top -H -p PID                                      # 看线程
top -1                                              # 各 CPU 分开看
# 交互: P=CPU排序  M=内存  c=完整命令  Shift+W 保存配置

# htop / btop (推荐)
htop                                                # 彩色 + 交互
btop                                                # 更炫的新一代

# 查看打开的文件
lsof -p PID
lsof -i :8080                                      # 占用 8080 的进程
lsof -u alice
lsof +D /var/log                                   # 用了某目录的进程
lsof -nP +c 15                                     # 不解析 dns / port / 命令长

# /proc/PID
cat /proc/PID/status
cat /proc/PID/cmdline | tr '\0' ' '
cat /proc/PID/environ | tr '\0' '\n'              # 环境变量
ls -l /proc/PID/cwd                                # 当前目录
ls -l /proc/PID/exe                                 # 可执行文件
ls -l /proc/PID/fd/                                 # 打开的 fd
cat /proc/PID/limits                                # 进程的 limit
cat /proc/PID/maps                                  # 内存映射
cat /proc/PID/stack                                 # 内核栈
```

### 3.2 信号

```bash
# 常用信号
1   SIGHUP   挂断（很多守护进程用来 reload 配置）
2   SIGINT   Ctrl+C
3   SIGQUIT  Ctrl+\ (退出+core dump)
9   SIGKILL  强杀（不可捕获）
15  SIGTERM  优雅终止（默认）
17  SIGCHLD  子进程退出
18  SIGCONT  继续
19  SIGSTOP  停止（不可捕获）
20  SIGTSTP  Ctrl+Z

# 发送
kill PID
kill -9 PID                                        # 强杀
kill -HUP $(pidof nginx)                           # reload
kill -l                                             # 列出所有信号

killall nginx                                       # 按名字
pkill -f "java.*MyApp"                              # 模式
```

### 3.3 后台 / 守护化

```bash
# 后台
command &                                          # 后台运行
nohup command &                                    # 不挂断（不随终端退出）
jobs                                                # 当前 shell 后台任务
fg %1                                               # 前台
bg %1                                               # 继续后台

# 现代：用 systemd / tmux / screen

# tmux
tmux new -s mywork                                # 新会话
tmux ls                                            # 列出会话
tmux a -t mywork                                  # 接入
# Ctrl+B d   分离
# Ctrl+B c   新窗口
# Ctrl+B "   水平分屏
# Ctrl+B %   垂直分屏

# screen
screen -S work
screen -r work
# Ctrl+A d   分离
```

## 四、包管理

### 4.1 RHEL/CentOS/Rocky/Alma（DNF/YUM）

```bash
# 基础
dnf install nginx
dnf remove nginx
dnf upgrade                                        # 全量升级
dnf update --security                              # 仅安全更新
dnf check-update
dnf list installed | grep nginx
dnf info nginx
dnf provides /usr/bin/python3                      # 这个文件属于哪个包
dnf history                                         # 操作历史
dnf history undo 5                                  # 回滚事务 5

# 仓库管理
dnf repolist
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf config-manager --set-enabled crb               # Rocky/Alma 启用 CRB
dnf config-manager --set-disabled epel
dnf install epel-release                           # EPEL
dnf install elrepo-release                         # ELRepo (新内核)

# 模块化（dnf module）
dnf module list
dnf module enable nodejs:18
dnf module install nodejs

# 下载不安装
dnf download nginx
dnf download --resolve --alldeps nginx -d ./rpms   # 含依赖

# 离线安装
rpm -ivh package.rpm
rpm -Uvh package.rpm                               # 升级
rpm -qa | grep nginx
rpm -ql nginx                                      # 看包内文件
rpm -qf /etc/nginx/nginx.conf                      # 文件属于哪个包
rpm -qi nginx                                      # 详细信息
rpm -V nginx                                        # 校验文件完整性
rpm -qp --scripts xxx.rpm                          # 看安装脚本
```

### 4.2 Debian/Ubuntu（APT）

```bash
# 基础
apt update                                          # 刷新元数据
apt upgrade                                         # 升级
apt full-upgrade                                    # 含删除依赖
apt install nginx
apt remove nginx                                   # 保留配置
apt purge nginx                                    # 连配置一起删
apt autoremove                                     # 清理无用依赖
apt search keyword
apt show nginx
apt list --installed

# 仓库
add-apt-repository ppa:ondrej/php
add-apt-repository "deb https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# 配置 sources.list
cat /etc/apt/sources.list.d/*.list

# 国内镜像（Ubuntu 24.04）
sed -i 's|http://archive.ubuntu.com|https://mirrors.aliyun.com|g' /etc/apt/sources.list

# 锁版本
apt-mark hold nginx
apt-mark unhold nginx

# DEB 包
dpkg -i package.deb
dpkg -l | grep nginx
dpkg -L nginx                                      # 文件列表
dpkg -S /etc/nginx/nginx.conf                      # 文件属于哪个包
dpkg --configure -a                                # 修复未完成的安装
apt --fix-broken install                           # 修复依赖
```

### 4.3 通用 / 跨发行版

```bash
# Snap (Canonical 主推，Ubuntu 默认)
snap install code --classic
snap list
snap refresh

# Flatpak (桌面应用)
flatpak install flathub org.mozilla.firefox

# AppImage (无需安装的 portable)
chmod +x myapp.AppImage && ./myapp.AppImage

# Homebrew (Linux 也支持)
curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash

# pip / pipx / uv
uv tool install black                              # 推荐 (2024+)
pipx install black                                 # 隔离环境
pip install --user black                           # 用户级

# 容器化使用（替代裸装）
docker run --rm -it python:3.12 bash
```

### 4.4 国产发行版

```
统信 UOS / 麒麟 Kylin / 中科方德:
  - apt 系（基于 Debian）

openEuler / OpenAnolis (龙蜥) / OpenCloudOS:
  - dnf 系（RHEL 兼容）
  - 包名兼容 CentOS
  - 国密 + 等保补丁

# openEuler 安装示例
sudo dnf install nginx
# 仓库 https://repo.openeuler.org/
```

## 五、日志（journald + rsyslog）

### 5.1 journalctl 速查

```bash
# 实时跟踪
journalctl -f                                      # 全部新日志
journalctl -fu nginx                               # 跟踪某服务
journalctl -fk                                     # 内核日志

# 按服务
journalctl -u nginx
journalctl -u nginx --since today
journalctl -u nginx --since "2026-06-26 10:00" --until "2026-06-26 11:00"
journalctl -u nginx -n 100                         # 最近 100 行
journalctl -u nginx -r                             # 反向
journalctl -u nginx -p err                         # 仅 error 以上

# 按优先级
# 0 emerg / 1 alert / 2 crit / 3 err / 4 warning / 5 notice / 6 info / 7 debug
journalctl -p 3 -xb                                # 本次启动后所有错误

# 按 PID/UID
journalctl _PID=1234
journalctl _UID=1000

# 按 boot
journalctl --list-boots
journalctl -b 0                                     # 本次启动
journalctl -b -1                                    # 上次启动

# 内核
journalctl -k                                       # = dmesg
journalctl -k --since "1 hour ago" | grep -i error

# 输出格式
journalctl -o json-pretty
journalctl -o cat                                  # 仅消息
journalctl -o short-precise                        # 含毫秒

# 占用空间
journalctl --disk-usage
journalctl --vacuum-time=7d                         # 只保留 7 天
journalctl --vacuum-size=2G                         # 限制大小
```

### 5.2 journald 配置

```ini
# /etc/systemd/journald.conf
[Journal]
Storage=persistent                                  # 持久化（auto/volatile/persistent）
SystemMaxUse=2G                                     # 最大占用
SystemKeepFree=1G                                   # 保留磁盘空闲
SystemMaxFileSize=200M
SystemMaxFiles=20
RuntimeMaxUse=200M
ForwardToSyslog=yes                                 # 转发到 rsyslog
Compress=yes
RateLimitInterval=30s
RateLimitBurst=1000
```

```bash
systemctl restart systemd-journald
# 持久化目录: /var/log/journal/
# 临时目录: /run/log/journal/
```

### 5.3 rsyslog 转发

```bash
# /etc/rsyslog.d/forward.conf
*.* @@logserver.example.com:514                    # @@ TCP / @ UDP

# 或转 ELK / Loki
*.* @@@logstash.example.com:5514;RSYSLOG_SyslogProtocol23Format

# /etc/rsyslog.d/myapp.conf  按 facility 路由
if $programname == 'myapp' then /var/log/myapp.log
& stop

systemctl restart rsyslog
```

### 5.4 logrotate

```bash
# /etc/logrotate.d/myapp
/var/log/myapp/*.log {
    daily
    rotate 30                                        # 保留 30 个
    compress
    delaycompress
    missingok
    notifempty
    create 0640 myapp myapp
    sharedscripts
    postrotate
        kill -HUP $(cat /var/run/myapp.pid) 2>/dev/null || true
    endscript
}

# 测试
logrotate -d /etc/logrotate.d/myapp                 # debug 不执行
logrotate -f /etc/logrotate.d/myapp                 # 强制执行
```

## 六、网络管理

### 6.1 NetworkManager（RHEL/Ubuntu 桌面）

```bash
nmcli                                              # 全局状态
nmcli device status
nmcli connection show
nmcli connection up "Wired connection 1"

# 创建静态 IP 连接
nmcli connection add type ethernet con-name eth0-static ifname eth0 \
  ipv4.method manual \
  ipv4.addresses 192.168.1.10/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "8.8.8.8 1.1.1.1"

nmcli connection up eth0-static

# 修改
nmcli connection modify eth0-static ipv4.dns "114.114.114.114"
nmcli connection reload && nmcli connection up eth0-static

# 删除
nmcli connection delete eth0-static
```

### 6.2 netplan（Ubuntu 服务器）

```yaml
# /etc/netplan/01-static.yaml
network:
  version: 2
  renderer: networkd                                # 或 NetworkManager
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
        mode: 802.3ad                               # LACP
        mii-monitor-interval: 100
      addresses: [10.0.0.10/24]
  vlans:
    vlan100:
      id: 100
      link: bond0
      addresses: [10.100.0.10/24]
```

```bash
netplan generate                                   # 生成 backend 配置
netplan try                                        # 测试 2 分钟自动回滚
netplan apply                                      # 应用
```

### 6.3 systemd-networkd（轻量服务器）

```ini
# /etc/systemd/network/10-static.network
[Match]
Name=eth0

[Network]
Address=192.168.1.10/24
Gateway=192.168.1.1
DNS=8.8.8.8

[Route]
Destination=10.0.0.0/8
Gateway=192.168.1.254
```

```bash
systemctl enable --now systemd-networkd
networkctl status                                 # 状态
```

### 6.4 传统 ip / iproute2

```bash
# 接口
ip a                                              # 所有接口
ip a show eth0
ip link set eth0 up|down
ip link set eth0 mtu 9000                          # Jumbo Frame

# 地址
ip addr add 192.168.1.10/24 dev eth0
ip addr del 192.168.1.10/24 dev eth0

# 路由
ip route                                          # = ip r
ip route add default via 192.168.1.1
ip route add 10.0.0.0/8 via 192.168.1.254
ip route del 10.0.0.0/8
ip route get 8.8.8.8                              # 看走哪条路由

# 邻居 (ARP)
ip neigh
ip neigh flush all

# 命名空间
ip netns add ns1
ip netns exec ns1 ip a
ip netns del ns1

# 看监听
ss -tlnp                                           # TCP listening
ss -tunlp                                          # TCP+UDP listening
ss -anp | grep :8080
ss -i                                              # 内部 TCP 信息

# 防火墙
firewall-cmd --list-all                            # firewalld (RHEL)
firewall-cmd --add-port=8080/tcp --permanent
firewall-cmd --reload

ufw status                                          # Ubuntu
ufw allow 80/tcp
ufw enable

iptables -L -n -v --line-numbers                   # 传统 iptables
nft list ruleset                                    # nftables (新)
```

## 七、SELinux / AppArmor

### 7.1 SELinux（RHEL 系）

```bash
# 状态
getenforce                                          # Enforcing / Permissive / Disabled
sestatus

# 临时切换
setenforce 0                                        # Permissive (不阻断，只警告)
setenforce 1                                        # Enforcing

# 永久（/etc/selinux/config）
SELINUX=enforcing                                   # 不要轻易 disabled

# 查看上下文
ls -Z /var/www/html
ps -eZ | grep nginx
id -Z

# 修改 context
chcon -t httpd_sys_content_t /var/www/html/index.html
restorecon -Rv /var/www/html                        # 按默认恢复

# 持久化 context 规则
semanage fcontext -a -t httpd_sys_content_t "/data(/.*)?"
restorecon -Rv /data

# 端口
semanage port -l | grep http
semanage port -a -t http_port_t -p tcp 8888

# 布尔值
getsebool -a | grep httpd
setsebool -P httpd_can_network_connect on          # -P 永久

# 故障排查
ausearch -m AVC -ts recent                         # 看 SELinux 拒绝
sealert -a /var/log/audit/audit.log                # 友好分析
journalctl -t setroubleshoot
```

### 7.2 AppArmor（Ubuntu/SUSE）

```bash
# 状态
aa-status

# Profile 位置
ls /etc/apparmor.d/

# 管理
aa-enforce /etc/apparmor.d/usr.sbin.nginx          # 启用强制
aa-complain /etc/apparmor.d/usr.sbin.nginx         # 仅警告
aa-disable /etc/apparmor.d/usr.sbin.nginx

# 自动生成 profile
aa-genprof /path/to/myapp                           # 引导式生成
aa-logprof                                          # 学习模式

# 看拒绝
journalctl -k | grep DENIED
dmesg | grep apparmor
```

## 八、时间同步

### 8.1 chrony（推荐）

```bash
# /etc/chrony.conf 或 /etc/chrony/chrony.conf
server ntp.aliyun.com iburst
server cn.pool.ntp.org iburst
pool 2.cn.pool.ntp.org iburst

driftfile /var/lib/chrony/drift
makestep 1.0 3                                      # 启动后强制对齐
rtcsync                                              # 同步到 RTC
local stratum 10
allow 192.168.0.0/16                                # 允许子网作为客户端

systemctl enable --now chronyd

# 命令
chronyc sources -v                                   # 各源状态
chronyc tracking                                     # 当前状态
chronyc makestep                                     # 立即强制对齐
chronyc -a 'burst 4/4'                              # 突发同步
```

### 8.2 systemd-timesyncd（轻量）

```bash
timedatectl                                          # 整体状态
timedatectl set-timezone Asia/Shanghai
timedatectl set-ntp true

# /etc/systemd/timesyncd.conf
[Time]
NTP=ntp.aliyun.com
FallbackNTP=cn.pool.ntp.org

systemctl restart systemd-timesyncd
timedatectl timesync-status
```

## 九、引导与内核

### 9.1 GRUB2

```bash
# 配置 /etc/default/grub
GRUB_TIMEOUT=5
GRUB_DEFAULT=saved                                  # 上次启动的
GRUB_CMDLINE_LINUX="quiet rhgb"                    # 内核参数

# 应用配置
grub2-mkconfig -o /boot/grub2/grub.cfg              # RHEL
update-grub                                          # Ubuntu

# 临时改内核参数（启动时 e 编辑）
# 紧急模式：在 linux 行末加 single  或 init=/bin/bash

# 设置默认启动条目
grub2-set-default 0
grub2-editenv list

# 查看可启动内核
awk -F\' '/^menuentry/ {print i++, $2}' /boot/grub2/grub.cfg
```

### 9.2 内核管理

```bash
uname -r                                            # 当前内核
ls /boot/vmlinuz-*                                  # 已装内核
dnf list installed kernel                           # RHEL
apt list --installed | grep linux-image             # Ubuntu

# 清理旧内核
dnf remove --oldinstallonly --setopt installonly_limit=2 kernel  # RHEL
apt autoremove --purge                              # Ubuntu

# 升级到新内核（RHEL ELRepo）
dnf install elrepo-release
dnf --enablerepo=elrepo-kernel install kernel-ml
# 改默认 → grub2-set-default 0 && reboot

# 内核模块
lsmod
modinfo nvidia
modprobe nvidia
modprobe -r nvidia                                  # 卸载
echo "blacklist nouveau" > /etc/modprobe.d/blacklist-nouveau.conf
dracut --force                                      # RHEL 重建 initramfs
update-initramfs -u                                  # Ubuntu
```

## 十、典型操作场景

### 10.1 新机器开荒（标准化）

```bash
#!/bin/bash
# init-server.sh

# 1. 时区 + NTP
timedatectl set-timezone Asia/Shanghai
systemctl enable --now chronyd

# 2. 主机名
hostnamectl set-hostname web-prod-01

# 3. 关闭 swap (K8s)
swapoff -a
sed -i '/swap/d' /etc/fstab

# 4. 防火墙基本规则
firewall-cmd --add-service=ssh --permanent
firewall-cmd --add-port=80/tcp --add-port=443/tcp --permanent
firewall-cmd --reload

# 5. SELinux (按需)
# setenforce 0   # K8s 老姿势, 新 K8s 已支持 enforcing

# 6. limits
cat >> /etc/security/limits.conf <<EOF
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOF

# 7. sysctl 基本
cat > /etc/sysctl.d/99-tuning.conf <<EOF
vm.max_map_count=262144
net.ipv4.ip_forward=1
net.bridge.bridge-nf-call-iptables=1
fs.file-max=2097152
EOF
sysctl --system

# 8. 创建运维用户 + SSH key
useradd -m -s /bin/bash -G wheel ops
mkdir -p /home/ops/.ssh
cat > /home/ops/.ssh/authorized_keys <<EOF
ssh-ed25519 AAAA... ops@bastion
EOF
chmod 700 /home/ops/.ssh
chmod 600 /home/ops/.ssh/authorized_keys
chown -R ops:ops /home/ops/.ssh

# 9. 禁用 root SSH 登录
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl reload sshd

# 10. 包管理基础
dnf install -y vim git wget curl htop net-tools tcpdump lsof tmux jq

echo "✅ Server bootstrap done"
```

### 10.2 服务异常排查 5 步

```bash
# 1. 状态
systemctl status myapp -l --no-pager

# 2. 日志
journalctl -u myapp -n 200 --no-pager
journalctl -u myapp --since "5 min ago"

# 3. 进程 / 端口
ps aux | grep myapp
ss -tlnp | grep PID
lsof -p PID | head

# 4. 资源
top -p PID
cat /proc/PID/status
cat /proc/PID/limits

# 5. 配置 + 重启
systemctl cat myapp
systemctl daemon-reload
systemctl restart myapp
```

## 十一、典型坑

| 坑 | 建议 |
|:---|:---|
| **改了 unit 没 daemon-reload** | systemctl daemon-reload 是肌肉记忆 |
| **service Type 选错（forking）** | nginx/php-fpm 用 forking, 大多 simple |
| **journald 占满磁盘** | SystemMaxUse 限制 + 持久化目录监控 |
| **直接 vim /etc/sudoers** | 必须 visudo |
| **usermod -G 没加 -a** | 不加 -a 会覆盖原组 |
| **改 sshd_config 没 reload** | 重启 sshd 别在远程 / 留个 root session |
| **rm -rf 误删** | 别用 root 日常 / alias rm='rm -i' |
| **iptables 改了没保存** | iptables-save / nftables 持久化 |
| **SELinux 一律 disabled** | RHEL 系尽量 enforcing |
| **改内核参数没持久化** | /etc/sysctl.d/ |
| **/etc/fstab 写错** | reboot 起不来 → 救援模式 |
| **swap 开着跑 K8s** | swapoff + 删 fstab |
| **NetworkManager 与 ifcfg 混用** | 选一种 |
| **GRUB 改了没 mkconfig** | 必须 grub2-mkconfig |
| **rpm -e 强删依赖** | --nodeps 慎用 |
| **logrotate 没 sharedscripts** | 多文件时 postrotate 执行多次 |

## 十二、推荐栈（2025）

```
init:             systemd
日志:             journald + rsyslog 转发 + Loki
网络:             netplan (Ubuntu) / NetworkManager (RHEL)
时间:             chrony
DNS:              systemd-resolved 或 dnsmasq
包管理:           dnf (RHEL) / apt (Debian) / uv (Python tooling)
安全模块:         SELinux (RHEL) / AppArmor (Ubuntu)
监控:             node-exporter + Prometheus
配置管理:         Ansible + GitOps
```

## 十三、国产化清单

```
发行版:
  - 麒麟 Kylin V10 (信创认证)
  - 统信 UOS V20
  - 龙蜥 Anolis OS (RHEL 兼容)
  - 欧拉 openEuler (华为，RHEL 兼容)
  - 红旗 Red Flag Linux
  - OpenCloudOS (腾讯)

特点:
  - RHEL/Debian 兼容
  - 国密算法支持
  - 等保 2.0 / 信创合规
  - 内核打了厂商补丁
  - 包管理类同（dnf/apt）

差异:
  - 默认开 SELinux + 国密
  - 部分商业组件需授权
  - 兼容性测试范围有限
```

## 十四、学习路径

```
入门（1 月）:
  1. systemd 基础 (start/stop/enable/status)
  2. 用户权限 + chmod/chown
  3. yum/apt 包管理
  4. journalctl 日志查看
  5. ip / ss / firewall 基础

中级（3 月）:
  6. 编写自定义 systemd service + timer
  7. ACL + Capability
  8. SELinux / AppArmor 上手
  9. netplan / NetworkManager
  10. systemd-analyze 启动分析
  11. logrotate

高级（6 月+）:
  12. systemd security hardening (沙箱)
  13. 内核模块管理
  14. GRUB 双内核切换
  15. 自动化开荒脚本
  16. 国产 OS 兼容

专家:
  17. systemd 源码 / 深度调试
  18. 自定义 PAM 模块
  19. 等保合规加固
```

## 十五、参考资料

```
- systemd 文档: https://www.freedesktop.org/wiki/Software/systemd/
- The Linux Documentation Project: https://tldp.org/
- ArchWiki: https://wiki.archlinux.org/
- Red Hat Documentation
- Ubuntu Server Guide
- 《Linux 系统管理技术手册》(UNIX/Linux System Administration Handbook)
- 《鸟哥的 Linux 私房菜》
- 阿铭 Linux 教程
```

> 📖 **核心判断**：Linux 系统管理 = **systemd（一切的入口）+ 权限模型（DAC + ACL + Capability + LSM）+ 包管理 + 日志 + 网络**。**自定义 systemd service 是运维分水岭**——能写出生产级 hardened unit（NoNewPrivileges/ProtectSystem/MemoryMax）的工程师才算合格。**SELinux 不要无脑 disabled**，RHEL 系尽量 enforcing；ulimit/sysctl/swap 是 K8s/数据库部署的三大检查项。

