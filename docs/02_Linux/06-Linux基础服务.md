# Linux 基础服务配置

> 服务器装完系统后的第一件事：配好 SSH 远程登录、系统日志、网络管理、NFS/Samba 文件共享。这些是所有后续运维的基础。

---

## 一、远程登录（SSH）

### 1.1 SSH 服务端配置

```bash
# 安装 (Rocky/RHEL)
dnf install -y openssh-server openssh-clients

# 安装 (Ubuntu)
apt install -y openssh-server openssh-client

# 启动
systemctl enable --now sshd

# 验证
ss -tlnp | grep :22
```

### 1.2 sshd_config 生产配置

```bash
cat > /etc/ssh/sshd_config.d/99-hardening.conf << 'EOF'
# === 基本设置 ===
Port 22                          # 端口 (可改非标准端口减少扫描)
AddressFamily inet               # 仅 IPv4
ListenAddress 0.0.0.0            # 监听地址 (0.0.0.0=全部)

# === 认证设置 ===
PermitRootLogin prohibit-password  # 禁止 root 密码登录, 允许密钥
# PermitRootLogin no               # 完全禁止 root 登录 (更严格)
PasswordAuthentication no          # 禁止密码登录 (仅密钥)
PubkeyAuthentication yes           # 启用密钥认证
MaxAuthTries 3                     # 最大认证尝试次数
MaxSessions 10                     # 最大并发会话

# === 登录控制 ===
LoginGraceTime 30                  # 登录宽限期 30 秒
PermitEmptyPasswords no            # 禁止空密码
X11Forwarding no                   # 禁止 X11 转发 (服务器不需要)
AllowTcpForwarding no              # 禁止 TCP 转发 (防跳板)
AllowAgentForwarding no            # 禁止 Agent 转发

# === 超时设置 ===
ClientAliveInterval 300            # 300 秒无操作发心跳
ClientAliveCountMax 2              # 2 次心跳无响应断开 (总计 10 分钟)

# === 日志 ===
LogLevel VERBOSE                   # 详细日志
SyslogFacility AUTHPRIV            # 记录到 /var/log/secure

# === 允许/禁止用户 (可选) ===
# AllowUsers admin deploy @ops     # 只允许这些用户/组
# DenyUsers guest test             # 禁止这些用户

# === SFTP ===
Subsystem sftp internal-sftp

# === 限制 SFTP 用户到主目录 (可选) ===
# Match Group sftpusers
#     ChrootDirectory /home/%u
#     ForceCommand internal-sftp
#     AllowTcpForwarding no
#     X11Forwarding no
EOF

# 重启生效
systemctl restart sshd

# 验证配置语法
sshd -t
```

### 1.3 密钥管理

```bash
# === 生成密钥对 ===
# ed25519 (推荐, 更短更快更安全)
ssh-keygen -t ed25519 -C "admin@ops-server-01" -f ~/.ssh/id_ed25519

# RSA (兼容性, 旧系统)
ssh-keygen -t rsa -b 4096 -C "admin@ops-server-01" -f ~/.ssh/id_rsa

# 带密码保护的密钥 (更安全)
ssh-keygen -t ed25519 -C "admin@ops" -f ~/.ssh/id_ed25519_secure -N "密钥密码"

# === 部署公钥 ===
# 方式一: ssh-copy-id (最简单)
ssh-copy-id -i ~/.ssh/id_ed25519.pub admin@192.168.1.100

# 方式二: 手动
cat ~/.ssh/id_ed25519.pub | ssh admin@192.168.1.100 \
    "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# === 密钥权限 (必须正确) ===
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

# === SSH Agent (免重复输入密钥密码) ===
eval $(ssh-agent)
ssh-add ~/.ssh/id_ed25519
ssh-add -l                    # 查看已加载的密钥

# === 配置 ~/.ssh/config (简化连接) ===
cat > ~/.ssh/config << 'EOF'
# 默认设置
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    StrictHostKeyChecking accept-new
    UserKnownHostsFile ~/.ssh/known_hosts

# 服务器快捷连接
Host web-01
    HostName 192.168.1.101
    User admin
    Port 22
    IdentityFile ~/.ssh/id_ed25519

Host db-01
    HostName 192.168.1.201
    User admin
    Port 2222
    IdentityFile ~/.ssh/id_ed25519

# 跳板机
Host bastion
    HostName 1.2.3.4
    User ops
    IdentityFile ~/.ssh/id_ed25519

# 通过跳板机连接内网
Host internal-*
    ProxyJump bastion
    User admin
    IdentityFile ~/.ssh/id_ed25519
EOF
chmod 600 ~/.ssh/config

# 使用: ssh web-01 (等同 ssh -i ~/.ssh/id_ed25519 admin@192.168.1.101)
```

### 1.4 SSH 安全加固清单

```bash
# 1. 禁止密码登录 (仅密钥)
# → sshd_config 中 PasswordAuthentication no

# 2. 修改默认端口 (减少暴力扫描)
# → sshd_config 中 Port 2222
# → SELinux: semanage port -a -t ssh_port_t -p tcp 2222
# → 防火墙: firewall-cmd --add-port=2222/tcp --permanent

# 3. fail2ban (自动封禁暴力破解 IP)
dnf install -y fail2ban
cat > /etc/fail2ban/jail.d/sshd.local << 'EOF'
[sshd]
enabled = true
port = 22
maxretry = 3
findtime = 300
bantime = 3600
EOF
systemctl enable --now fail2ban

# 4. 限制来源 IP (防火墙层面)
firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 port port=22 protocol=tcp accept'
firewall-cmd --permanent --remove-service=ssh
firewall-cmd --reload

# 5. 双因素认证 (可选, Google Authenticator)
dnf install -y google-authenticator
google-authenticator              # 为用户生成 TOTP 密钥
# sshd_config 中:
#   KbdInteractiveAuthentication yes
#   ChallengeResponseAuthentication yes
#   /etc/pam.d/sshd 添加:
#   auth required pam_google_authenticator.so
```

### 1.5 SSH 常用操作

```bash
# === 端口转发 ===
# 本地转发 (访问本地 8080 = 访问远程的 80)
ssh -L 8080:localhost:80 admin@192.168.1.100

# 远程转发 (远程访问其 8080 = 访问本地的 80)
ssh -R 8080:localhost:80 admin@192.168.1.100

# 动态转发 (SOCKS 代理)
ssh -D 1080 admin@192.168.1.100

# === 文件传输 ===
# SCP
scp file.tar.gz admin@192.168.1.100:/tmp/
scp -r admin@192.168.1.100:/var/log /tmp/remote-logs/
scp -P 2222 file.txt admin@192.168.1.100:/tmp/    # 非标准端口

# rsync (增量同步, 大文件推荐)
rsync -avzP /local/dir/ admin@192.168.1.100:/remote/dir/
rsync -avzP --delete admin@192.168.1.100:/remote/ /local/   # --delete 删除目标多余文件
rsync -avzP -e "ssh -p 2222" /local/ admin@192.168.1.100:/remote/

# sftp
sftp admin@192.168.1.100
sftp> put localfile /tmp/
sftp> get /tmp/remotefile ./
sftp> ls / cd / pwd

# === 批量执行 ===
# 单条命令
ssh admin@192.168.1.100 "uname -r && df -h"

# 多条命令
ssh admin@192.168.1.100 << 'EOF'
hostname
uptime
df -h
EOF

# 批量到多台
for host in web-{01..05}; do
    echo "=== $host ==="
    ssh $host "uptime"
done
```

---

## 二、日志管理

### 2.1 日志体系

```
┌─────────────────────────────────────────────┐
│              应用程序                         │
│    Nginx  MySQL  Docker  自研服务             │
└──────┬──────────────────────────────────────┘
       │ 写日志
       ▼
┌──────────────┐     ┌──────────────────┐
│  rsyslog     │     │  journal (二进制) │
│  (文本日志)   │     │  systemd-journal  │
└──────┬───────┘     └────────┬─────────┘
       │                      │
       ▼                      ▼
┌──────────────┐     ┌──────────────────┐
│ /var/log/    │     │ /var/log/journal/│
│  messages    │     │  (持久化二进制)    │
│  secure      │     │                   │
│  maillog     │     │  journalctl 查询  │
│  cron        │     │                   │
└──────────────┘     └──────────────────┘
```

### 2.2 journalctl（systemd 日志）

```bash
# === 基本查询 ===
journalctl                        # 全部日志 (最新)
journalctl -b                     # 本次启动的日志
journalctl -b -1                  # 上次启动的日志
journalctl --since "2026-07-07 09:00:00" --until "2026-07-07 12:00:00"
journalctl --since "1 hour ago"
journalctl --since today

# === 按优先级 ===
# 0=emerg 1=alert 2=crit 3=err 4=warning 5=notice 6=info 7=debug
journalctl -p err                 # 只看错误
journalctl -p warning             # 警告及以上
journalctl -p 3..6                # err 到 info

# === 按服务 ===
journalctl -u sshd                # SSH 服务日志
journalctl -u nginx -u php-fpm    # 多个服务
journalctl -u docker --since "10 min ago"

# === 按进程/用户 ===
journalctl _PID=12345
journalctl _UID=1000
journalctl _GID=1000

# === 实时跟踪 ===
journalctl -f                     # 类似 tail -f
journalctl -f -u sshd             # 跟踪特定服务

# === 格式化输出 ===
journalctl -o json                # JSON 格式
journalctl -o json-pretty         # 美化 JSON
journalctl -o cat                 # 只显示消息内容 (无时间戳)
journalctl -o short-iso           # ISO 时间戳

# === 磁盘占用 ===
journalctl --disk-usage           # 查看日志占用
journalctl --vacuum-size=500M     # 限制到 500MB
journalctl --vacuum-time=7d       # 只保留 7 天
journalctl --vacuum-files=10      # 只保留 10 个日志文件

# === 持久化配置 ===
# /etc/systemd/journald.conf
# Storage=auto      # 默认, 有 /var/log/journal 就持久化
# Storage=persistent # 强制持久化
# Storage=none      # 不存
# SystemMaxUse=500M  # 最大磁盘用量
# MaxRetentionSec=1month  # 保留时间
```

### 2.3 rsyslog 配置

```bash
# rsyslog 管理传统文本日志 (/var/log/messages, secure, maillog 等)

# 配置文件: /etc/rsyslog.conf + /etc/rsyslog.d/*.conf

# 规则格式: facility.priority  action
# facility: auth, authpriv, cron, daemon, kern, mail, user, local0-7
# priority: debug, info, notice, warning, err, crit, alert, emerg

cat > /etc/rsyslog.d/99-custom.conf << 'EOF'
# === 默认规则 (Rocky 9 默认已配) ===
#*.info;mail.none;authpriv.none;cron.none  /var/log/messages
#authpriv.*                                /var/log/secure
#mail.*                                    /var/log/maillog
#cron.*                                    /var/log/cron
#*.emerg                                   :omusrmsg:*

# === 自定义: 应用日志 ===
local0.*                                    /var/log/myapp/app.log
local1.notice                               /var/log/myapp/notice.log

# === 远程日志服务器 (集中日志) ===
# *.*  @@192.168.1.10:514     # TCP (双@)
# *.*  @192.168.1.10:514      # UDP (单@)

# === 按 IP 分目录 ===
# $template RemoteLogs,"/var/log/remote/%fromhost-ip%/%$YEAR%%$MONTH%%$DAY%.log"
# *.*  ?RemoteLogs
EOF

systemctl restart rsyslog
```

### 2.4 日志轮转（logrotate）

```bash
# 安装
dnf install -y logrotate

# 主配置: /etc/logrotate.conf
# 子配置: /etc/logrotate.d/*

# 示例: Nginx 日志轮转
cat > /etc/logrotate.d/nginx << 'EOF'
/var/log/nginx/*.log {
    daily                  # 每天轮转
    rotate 30              # 保留 30 天
    missingok              # 日志不存在不报错
    compress               # 压缩旧日志
    delaycompress          # 延迟压缩 (保留最近一个未压缩)
    notifempty             # 空文件不轮转
    create 0640 nginx adm  # 创建新日志文件权限
    sharedscripts          # 多个日志共享脚本
    postrotate
        if [ -f /run/nginx.pid ]; then
            kill -USR1 $(cat /run/nginx.pid)
        fi
    endscript
}
EOF

# 示例: 自定义应用日志
cat > /etc/logrotate.d/myapp << 'EOF'
/var/log/myapp/*.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    create 0644 app app
    size 100M              # 超过 100MB 也轮转
    postrotate
        systemctl reload myapp 2>/dev/null || true
    endscript
}
EOF

# 手动执行 (测试)
logrotate -d /etc/logrotate.d/nginx   # 模拟 (dry-run)
logrotate -f /etc/logrotate.d/nginx   # 强制轮转

# logrotate 由 cron 定时触发:
# /etc/cron.daily/logrotate
```

### 2.5 常见日志文件速查

| 日志文件 | 内容 | 查看命令 |
|:---|:---|:---|
| `/var/log/messages` | 系统主日志 | `tail -f /var/log/messages` |
| `/var/log/secure` | SSH/sudo/认证日志 | `grep Failed /var/log/secure` |
| `/var/log/maillog` | 邮件日志 | `tail -f /var/log/maillog` |
| `/var/log/cron` | 定时任务日志 | `grep CRON /var/log/cron` |
| `/var/log/dmesg` | 内核启动日志 | `dmesg` |
| `/var/log/audit/audit.log` | SELinux 审计日志 | `ausearch -m avc` |
| `/var/log/wtmp` | 登录记录 (二进制) | `last` |
| `/var/log/btmp` | 失败登录 (二进制) | `lastb` |
| `/var/log/lastlog` | 最后登录 (二进制) | `lastlog` |
| `journalctl` | systemd 日志 | `journalctl -b -p err` |

```bash
# 查看登录历史
last                              # 谁登录过
last -n 20                        # 最近 20 条
last -f /var/log/wtmp.1           # 上个月的记录
last root                         # root 用户的登录
last reboot                       # 重启历史

# 查看失败登录
lastb                             # 失败的登录尝试
lastb -n 20                       # 最近 20 条

# 查看当前登录
w                                 # 谁在线 + 在干什么
who                               # 谁在线
```

---

## 三、网络管理

### 3.1 NetworkManager（推荐）

```bash
# nmcli 是 NetworkManager 的命令行工具

# === 查看网络状态 ===
nmcli device status               # 设备状态
nmcli connection show             # 连接配置列表
nmcli device show ens33           # 网卡详情

# === 配置静态 IP ===
# 修改现有连接
nmcli connection modify ens33 \
    ipv4.method manual \
    ipv4.addresses 192.168.1.100/24 \
    ipv4.gateway 192.168.1.1 \
    ipv4.dns "192.168.1.10,8.8.8.8" \
    ipv4.dns-search example.com \
    connection.autoconnect yes

# 应用配置
nmcli connection up ens33

# 验证
ip addr show ens33
ip route show
nslookup github.com

# === 创建新连接 ===
# 静态 IP
nmcli connection add \
    con-name eth0-static \
    type ethernet \
    ifname eth0 \
    ipv4.method manual \
    ipv4.addresses 192.168.1.100/24 \
    ipv4.gateway 192.168.1.1 \
    ipv4.dns 192.168.1.10 \
    autoconnect yes

# DHCP
nmcli connection add \
    con-name eth0-dhcp \
    type ethernet \
    ifname eth0 \
    ipv4.method auto \
    autoconnect yes

# === 多 IP (一个网卡多地址) ===
nmcli connection modify ens33 +ipv4.addresses 10.0.0.100/24
nmcli connection up ens33

# === Bonding (网卡绑定) ===
# 创建 bond 接口
nmcli connection add \
    type bond \
    con-name bond0 \
    ifname bond0 \
    bond.options "mode=802.3ad,miimon=100,lacp_rate=fast"
    # mode=802.3ad: LACP 动态聚合 (需要交换机配 LACP)
    # mode=active-backup: 主备 (不需要交换机配)
    # mode=balance-rr: 轮询

# 添加从接口
nmcli connection add type ethernet slave-type bond con-name bond0-port1 ifname ens33 master bond0
nmcli connection add type ethernet slave-type bond con-name bond0-port2 ifname ens34 master bond0

# 配置 bond IP
nmcli connection modify bond0 \
    ipv4.method manual \
    ipv4.addresses 192.168.1.100/24 \
    ipv4.gateway 192.168.1.1

nmcli connection up bond0

# === VLAN ===
nmcli connection add \
    type vlan \
    con-name vlan100 \
    ifname vlan100 \
    dev ens33 \
    id 100 \
    ipv4.method manual \
    ipv4.addresses 10.100.0.100/24

nmcli connection up vlan100
```

### 3.2 Bonding 模式对比

| 模式 | 名称 | 交换机要求 | 带宽 | 容错 | 适用场景 |
|:---:|:---|:---|:---|:---|:---|
| 0 | balance-rr | 无需配置 | N 倍 | ✅ | 测试环境 |
| 1 | active-backup | 无需配置 | 1 倍 | ✅ | 服务器标准 |
| 2 | balance-xor | 无需配置 | N 倍 | ✅ | 少用 |
| 3 | broadcast | 无需配置 | 1 倍 | ✅ | 少用 |
| 4 | 802.3ad (LACP) | 需配 LACP | N 倍 | ✅ | **生产推荐** |
| 5 | balance-tlb | 无需配置 | N 倍 | ✅ | 发送负载 |
| 6 | balance-alb | 无需配置 | N 倍 | ✅ | 收发负载 |

**生产环境建议：** mode=802.3ad (LACP) + 交换机配 LACP，带宽和容错最佳。如果不方便配交换机，用 mode=active-backup。

### 3.3 网络配置文件方式

```bash
# Rocky 9 / RHEL 9 — ifcfg 已弃用, 使用 keyfile
# /etc/NetworkManager/system-connections/ens33.nmconnection

[connection]
id=ens33
type=ethernet
interface-name=ens33
autoconnect=true

[ipv4]
method=manual
address1=192.168.1.100/24
gateway=192.168.1.1
dns=192.168.1.10;8.8.8.8;
dns-search=example.com;

# Ubuntu — netplan
# /etc/netplan/01-netcfg.yaml
network:
  version: 2
  ethernets:
    ens33:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [192.168.1.10, 8.8.8.8]
        search: [example.com]

# 应用
netplan apply
```

### 3.4 网络诊断工具

```bash
# === 连通性 ===
ping -c 4 192.168.1.1            # ICMP 连通
ping -c 4 -i 0.1 192.168.1.1     # 快速 ping (间隔 0.1s)
ping -c 4 -W 2 192.168.1.1       # 超时 2s
ping6 -c 4 fe80::1               # IPv6 ping

# === 路由 ===
ip route show                     # 查看路由表
ip route get 8.8.8.8              # 查看到某 IP 的路由路径
traceroute 8.8.8.8                # 路由追踪
mtr 8.8.8.8                       # 交互式路由追踪 (推荐)
mtr -r -c 10 8.8.8.8              # 报告模式

# === DNS ===
nslookup example.com              # DNS 查询
dig example.com                   # 详细 DNS 查询
dig @8.8.8.8 example.com          # 指定 DNS 服务器
dig example.com MX                # 查 MX 记录
dig example.com TXT               # 查 TXT 记录
dig -x 192.168.1.1                # 反向解析

# === 端口/连接 ===
ss -tlnp                          # 监听的 TCP 端口
ss -tunp                          # 所有 TCP/UDP 连接
ss -t state established           # 已建立的 TCP 连接
ss -s                             # 连接统计摘要
netstat -tlnp                     # 旧命令 (ss 替代)

# === 抓包 ===
tcpdump -i ens33 -n               # 抓取所有流量
tcpdump -i ens33 port 80          # 只抓 80 端口
tcpdump -i ens33 host 192.168.1.1 # 只抓与某 IP 的流量
tcpdump -i ens33 -nn -w /tmp/capture.pcap  # 保存到文件
tcpdump -r /tmp/capture.pcap      # 读取抓包文件

# === 带宽/性能 ===
iperf3 -s                         # 服务端 (一端运行)
iperf3 -c 192.168.1.100           # 客户端测带宽
iperf3 -c 192.168.1.100 -u -b 10G # UDP 测试 10G 带宽
iperf3 -c 192.168.1.100 -P 4     # 4 路并行

# === 网卡信息 ===
ethtool ens33                     # 网卡速率/双工/链路
ethtool -i ens33                  # 驱动/固件版本
ethtool -S ens33                  |  # 网卡统计 (丢包/错误)
ethtool -g ens33                  # 环形缓冲区大小

# 诊断丢包
ethtool -S ens33 | grep -iE "drop|error|discard"
```

### 3.5 防火墙（firewalld）

```bash
# === 基本操作 ===
systemctl enable --now firewalld

firewall-cmd --state              # 状态
firewall-cmd --list-all           # 查看所有规则
firewall-cmd --get-zones          # 所有 zone
firewall-cmd --get-active-zones   # 活跃 zone

# === 添加服务/端口 ===
# 服务方式 (推荐)
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https

# 端口方式
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --add-port=10000-20000/udp

# 重新加载 (永久规则需要 reload 才生效)
firewall-cmd --reload

# === 限制来源 IP ===
# 只允许 192.168.1.0/24 访问 SSH
firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 service name=ssh accept'

# 禁止某 IP
firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=10.0.0.5 reject'

# === 端口转发 ===
firewall-cmd --permanent --add-forward-port=port=80:proto=tcp:toport=8080:toaddr=192.168.1.200

# === NAT / 伪装 ===
firewall-cmd --permanent --add-masquerade
firewall-cmd --reload

# === 删除规则 ===
firewall-cmd --permanent --remove-service=http
firewall-cmd --permanent --remove-port=8080/tcp
firewall-cmd --reload
```

### 3.6 nftables（替代 iptables）

```bash
# nftables 是新一代 Linux 防火墙, firewalld 底层已使用 nftables
# Rocky 9 / Ubuntu 22.04 默认使用 nftables

# 查看规则
nft list ruleset

# 直接写 nftables 规则 (不通过 firewalld)
# /etc/nftables.conf
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        # 允许已建立的连接
        ct state established,related accept

        # 允许本地回环
        iif "lo" accept

        # 允许 ICMP
        ip protocol icmp accept
        ip6 nexthdr ipv6-icmp accept

        # 允许 SSH
        tcp dport 22 accept

        # 允许 HTTP/HTTPS
        tcp dport { 80, 443 } accept

        # 限制 SSH 暴力破解 (每分钟最多 5 个新连接)
        tcp dport 22 meter ssh-meter { ip saddr limit rate 5/minute } accept

        # 记录被丢弃的包
        limit rate 10/second log prefix "nft-dropped: " drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}

# 启用
systemctl enable --now nftables
nft -f /etc/nftables.conf
```

---

## 四、网络文件共享

### 4.1 NFS（Linux 之间共享）

#### 服务端配置

```bash
# 安装
dnf install -y nfs-utils

# 创建共享目录
mkdir -p /srv/nfs/share
chmod 755 /srv/nfs/share

# 配置导出
cat > /etc/exports << 'EOF'
# 格式: 共享目录  客户端(选项)
#
# 选项:
#   ro / rw           只读 / 读写
#   sync / async      同步 / 异步 (sync 更安全)
#   root_squash       root 映射为 nfsnobody (安全)
#   no_root_squash    不映射 root (不安全, 但某些场景需要)
#   all_squash        所有用户映射为 nfsnobody
#   anonuid/anongid   指定映射的 UID/GID

# 允许整个子网读写
/srv/nfs/share    192.168.1.0/24(rw,sync,root_squash)

# 允许特定主机读写, 不 squash root
/ssrv/nfs/admin   192.168.1.100(rw,sync,no_root_squash)

# 只读共享
/srv/nfs/iso      *(ro,sync,all_squash)
EOF

# 启动
systemctl enable --now nfs-server

# 导出生效
exportfs -ra                      # 重新导出所有
exportfs -v                       # 查看当前导出

# 防火墙放行
firewall-cmd --permanent --add-service=nfs
firewall-cmd --permanent --add-service=rpc-bind
firewall-cmd --permanent --add-service=mountd
firewall-cmd --reload
```

#### 客户端挂载

```bash
# 安装客户端
dnf install -y nfs-utils

# 查看服务端导出列表
showmount -e 192.168.1.10

# 临时挂载
mount -t nfs -o vers=4.2 192.168.1.10:/srv/nfs/share /mnt/nfs

# 挂载选项:
#   vers=4.2        NFS 版本 (4.2 最新, 3 兼容性好)
#   hard            硬挂载 (IO 错误时等待恢复, 生产推荐)
#   soft            软挂载 (超时后报错, 可能丢数据)
#   rsize/wsize     读写块大小 (默认 1MB, 可调大)
#   timeo=600       超时时间 (60 秒)
#   retrans=2       重试次数
#   noatime         不更新访问时间 (性能优化)

# 永久挂载 (/etc/fstab)
192.168.1.10:/srv/nfs/share  /mnt/nfs  nfs  vers=4.2,hard,rsize=1048576,wsize=1048576,timeo=600,retrans=2,noatime  0  0

# 挂载
mount /mnt/nfs

# 验证
df -hT /mnt/nfs
mount | grep nfs

# 卸载
umount /mnt/nfs
# 如果 busy:
umount -l /mnt/nfs               # lazy unmount
fuser -km /mnt/nfs               # 杀掉占用进程后卸载
```

#### NFS 性能调优

```bash
# 服务端优化
# /etc/nfs.conf
[nfsd]
threads=16                       # NFS 线程数 (默认 8, 大并发调大)
# /etc/sysctl.conf
sunrpc.tcp_slot_table_entries=128
sunrpc.tcp_max_slot_table_entries=128

# 客户端优化
mount -t nfs -o vers=4.2,hard,rsize=1048576,wsize=1048576,nconnect=4 192.168.1.10:/share /mnt/nfs
# nconnect=4: 建立 4 个 TCP 连接 (提高吞吐, 内核 5.3+)

# 测试性能
dd if=/dev/zero of=/mnt/nfs/testfile bs=1M count=1000 oflag=direct
fio --name=nfs-test --filename=/mnt/nfs/test --bs=1M --size=1G --rw=write --direct=1 --numjobs=4
```

### 4.2 Samba（Linux ↔ Windows 共享）

#### 服务端配置

```bash
# 安装
dnf install -y samba samba-client

# 创建共享目录
mkdir -p /srv/samba/share
chmod 777 /srv/samba/share

# 创建 Samba 用户 (必须是系统用户)
useradd -s /sbin/nologin smbuser
smbpasswd -a smbuser               # 设置 Samba 密码

# 配置
cat > /etc/samba/smb.conf << 'EOF'
[global]
    workgroup = WORKGROUP
    server string = Samba Server
    security = user                # 用户认证
    map to guest = never           # 禁止 guest

    # 性能
    socket options = TCP_NODELAY SO_RCVBUF=65536 SO_SNDBUF=65536
    max xmit = 65535
    deadtime = 15                  # 15 分钟空闲断开

    # 日志
    log file = /var/log/samba/log.%m
    max log size = 50
    log level = 1

# 共享目录
[share]
    path = /srv/samba/share
    browseable = yes
    writable = yes
    valid users = smbuser, @smbgroup
    create mask = 0660
    directory mask = 0770

# 只读共享
[public]
    path = /srv/samba/public
    browseable = yes
    writable = no
    guest ok = no
EOF

# 测试配置
testparm

# 启动
systemctl enable --now smb nmb

# 防火墙
firewall-cmd --permanent --add-service=samba
firewall-cmd --reload
```

#### 客户端访问

```bash
# Linux 客户端
# 安装
dnf install -y samba-client cifs-utils

# 查看共享
smbclient -L //192.168.1.10 -U smbuser

# 交互式访问
smbclient //192.168.1.10/share -U smbuser
smb: \> ls
smb: \> get file.txt
smb: \> put local.txt
smb: \> quit

# 挂载到目录
mount -t cifs -o username=smbuser,password=xxx,uid=1000,gid=1000 \
    //192.168.1.10/share /mnt/samba

# 永久挂载 (/etc/fstab)
# 安全方式: 凭据文件
cat > /etc/samba/smbcredentials << 'EOF'
username=smbuser
password=xxx
domain=WORKGROUP
EOF
chmod 600 /etc/samba/smbcredentials

# /etc/fstab
//192.168.1.10/share  /mnt/samba  cifs  credentials=/etc/samba/smbcredentials,uid=1000,gid=1000,iocharset=utf8  0  0

mount /mnt/samba
```

```powershell
# Windows 客户端
# 资源管理器地址栏输入:
\\192.168.1.10\share

# 映射网络驱动器:
net use Z: \\192.168.1.10\share /user:smbuser 密码
```

### 4.3 共享方式对比

| 维度 | NFS | Samba (SMB) | iSCSI |
|:---|:---|:---|:---|
| 适用平台 | Linux ↔ Linux | Linux ↔ Windows | 任意 OS |
| 传输层 | UDP/TCP | TCP | TCP |
| 性能 | 高（原生） | 中 | 高（块设备） |
| 共享级别 | 文件级 | 文件级 | 块级 |
| 认证 | IP + UID | 用户/密码 | CHAP |
| Windows 兼容 | 需第三方 | ✅ 原生 | ✅ |
| 权限控制 | UID/GID | 用户/组 | 块设备权限 |
| 典型场景 | Linux 集群共享 | 混合环境 | SAN 存储 |

### 4.4 iSCSI（块级共享，可选了解）

```bash
# 服务端 (target)
dnf install -y targetcli

# 创建块设备
targetcli
# /> backstores/block create name=disk0 dev=/dev/sdb
# /> iscsi/create iqn.2026-07.com.example:target
# /> iscsi/iqn.../tpg1/luns create /backstores/block/disk0
# /> iscsi/iqn.../tpg1/acls create iqn.2026-07.com.example:client
# /> saveconfig
# /> exit

systemctl enable --now target

# 客户端 (initiator)
dnf install -y iscsi-initiator-utils
systemctl enable --now iscsid

# 发现目标
iscsiadm -m discovery -t st -p 192.168.1.10
# 登录
iscsiadm -m node -T iqn.2026-07.com.example:target -p 192.168.1.10 -l
# 验证
lsblk                           # 应该看到新的块设备
```

---

## 五、时间同步

### 5.1 chronyd（推荐）

```bash
# 安装
dnf install -y chrony
systemctl enable --now chronyd

# 配置 /etc/chrony.conf
cat > /etc/chrony.conf << 'EOF'
# NTP 服务器 (国内推荐)
server ntp.aliyun.com iburst
server ntp.tencent.com iburst
server cn.pool.ntp.org iburst

# 如果是 NTP 服务器, 允许客户端同步
# allow 192.168.1.0/24

# 本地硬件时钟
rtcsync

# 如果硬件时钟可靠, 可以作为本地 NTP 源
# local stratum 10

# 日志
logdir /var/log/chrony
makestep 1.0 3                   # 时差大于 1 秒时立即调整 (前 3 次)
EOF

systemctl restart chronyd

# 验证
chronyc tracking                 # 同步状态
chronyc sources -v               # NTP 源状态
chronyc clients                  # 客户端列表 (如果作为 NTP 服务器)

# 手动同步
chronyc makestep                 # 立即同步一次

# 查看时区
timedatectl
timedatectl set-timezone Asia/Shanghai
```

---

## 六、SELinux

### 6.1 基本操作

```bash
# 查看状态
getenforce                       # Enforcing / Permissive / Disabled
sestatus                         # 详细状态

# 临时切换
setenforce 0                     # 临时设为 Permissive
setenforce 1                     # 临时设为 Enforcing

# 永久配置
# /etc/selinux/config
# SELINUX=enforcing              # 强制 (生产推荐)
# SELINUX=permissive             # 宽松 (只记录不阻止)
# SELINUX=disabled               # 关闭 (不推荐)

# 查看上下文
ls -Z /var/www/html/index.html   # 文件上下文
ps -ZC nginx                     # 进程上下文
semanage fcontext -l | grep httpd # 上下文规则

# 修改上下文
semanage fcontext -a -t httpd_sys_content_t "/srv/web(/.*)?"
restorecon -Rv /srv/web

# 排查 SELinux 拒绝
ausearch -m avc -ts recent       # 最近的 AVC 拒绝
sealert -a /var/log/audit/audit.log  # 分析审计日志
journalctl -t setroubleshoot     # SELinux 告警

# 布尔值 (开关)
getsebool -a | grep httpd        # 查看 httpd 相关布尔值
setsebool -P httpd_can_network_connect on  # 允许 httpd 网络连接 (-P 永久)
```

### 6.2 常见 SELinux 问题

```bash
# 问题: 网页无法访问
# 原因: 文件上下文不对
semanage fcontext -a -t httpd_sys_content_t "/srv/www(/.*)?"
restorecon -Rv /srv/www

# 问题: Nginx 反代被拒
# 原因: httpd 不允许连网络
setsebool -P httpd_can_network_connect on

# 问题: 自定义端口被拒
# 原因: 端口上下文未定义
semanage port -a -t http_port_t -p tcp 8080

# 问题: 服务无法读取某目录
# 排查:
ausearch -m avc -ts recent | audit2allow -m mypolicy
# 生成允许策略模块
semodule -i mypolicy.pp
```

---

## 七、运维常用组合

### 7.1 新服务器初始化脚本

```bash
#!/bin/bash
# new-server-init.sh — 新服务器基础配置
set -euo pipefail

echo "=== 1. 更新系统 ==="
dnf update -y

echo "=== 2. 安装基础工具 ==="
dnf install -y vim git wget curl tmux htop \
    net-tools bind-utils telnet tcpdump \
    sysstat dnf-automatic epel-release \
    fail2ban chrony rsync nfs-utils samba-client

echo "=== 3. 时区 + NTP ==="
timedatectl set-timezone Asia/Shanghai
systemctl enable --now chronyd

echo "=== 4. SSH 加固 ==="
cat > /etc/ssh/sshd_config.d/99-hardening.conf << 'EOF'
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
ClientAliveInterval 300
ClientAliveCountMax 2
EOF
systemctl restart sshd

echo "=== 5. 防火墙 ==="
systemctl enable --now firewalld
firewall-cmd --permanent --add-service=ssh
firewall-cmd --reload

echo "=== 6. fail2ban ==="
cat > /etc/fail2ban/jail.d/sshd.local << 'EOF'
[sshd]
enabled = true
maxretry = 3
bantime = 3600
EOF
systemctl enable --now fail2ban

echo "=== 7. 自动更新安全补丁 ==="
systemctl enable --now dnf-automatic.timer

echo "=== 8. 日志保留 ==="
sed -i 's/^#SystemMaxUse=.*/SystemMaxUse=500M/' /etc/systemd/journald.conf
sed -i 's/^#MaxRetentionSec=.*/MaxRetentionSec=1month/' /etc/systemd/journald.conf
systemctl restart systemd-journald

echo "=== 完成 ==="
echo "下一步:"
echo "  1. 部署 SSH 公钥: ssh-copy-id admin@<ip>"
echo "  2. 配置网络: nmcli connection modify ..."
echo "  3. 配置 NFS/Samba (如需)"
echo "  4. 安装监控 (node_exporter/zabbix-agent)"
```

### 7.2 日常运维速查

```bash
# === 系统状态 ===
uptime                            # 负载
free -h                           # 内存
df -hT                            # 磁盘
ss -s                             # 网络连接摘要
top -b -n 1 | head -20           # CPU/内存 Top

# === 服务管理 ===
systemctl status sshd             # 服务状态
systemctl restart nginx           # 重启
journalctl -u nginx -f            # 实时日志

# === 网络排查 ===
ip addr                           # IP 地址
ip route                          # 路由
ss -tlnp                          # 监听端口
ping -c 3 8.8.8.8                 # 连通性
dig example.com                   # DNS

# === 日志排查 ===
journalctl -b -p err              # 本次启动的错误
tail -f /var/log/messages         # 系统日志
grep Failed /var/log/secure       # SSH 失败
last -n 10                        # 登录历史

# === 磁盘 ===
lsblk                             # 块设备
du -sh /var/log/*                 # 日志大小
find / -xdev -type f -size +1G   # 大文件
```

---

## 八、配置文件速查表

| 服务 | 配置文件 | 说明 |
|:---|:---|:---|
| SSH | `/etc/ssh/sshd_config` | 主配置 |
| SSH | `/etc/ssh/sshd_config.d/*.conf` | 片段配置 (优先级更高) |
| 日志 | `/etc/systemd/journald.conf` | journald 配置 |
| 日志 | `/etc/rsyslog.conf` + `/etc/rsyslog.d/*.conf` | rsyslog 配置 |
| 日志 | `/etc/logrotate.d/*` | 日志轮转 |
| 网络 | `/etc/NetworkManager/system-connections/*.nmconnection` | NM 配置 |
| 网络 | `/etc/netplan/*.yaml` | Ubuntu netplan |
| 网络 | `/etc/hosts` | 本地域名解析 |
| 网络 | `/etc/resolv.conf` | DNS 配置 (NM 管理) |
| 防火墙 | `/etc/firewalld/zones/*.xml` | firewalld 规则 |
| 防火墙 | `/etc/nftables.conf` | nftables 规则 |
| NFS | `/etc/exports` | NFS 导出 |
| Samba | `/etc/samba/smb.conf` | Samba 配置 |
| Samba | `/etc/samba/smbcredentials` | 挂载凭据 |
| 时间 | `/etc/chrony.conf` | NTP 配置 |
| SELinux | `/etc/selinux/config` | SELinux 模式 |
| 挂载 | `/etc/fstab` | 文件系统挂载表 |
| 系统 | `/etc/sysctl.conf` + `/etc/sysctl.d/*.conf` | 内核参数 |

---

*最后更新: 2026-07-07*
