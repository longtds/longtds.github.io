# Linux 网络安全与防火墙

> Linux 网络安全怎么搞？iptables/firewalld 怎么配？如何屏蔽恶意应用和 IP？本文覆盖网络安全基础、防火墙实战、应用防护全流程。

---

## 一、Linux 网络安全基础

### 1.1 网络安全分层

```
┌─────────────────────────────────────────────────────────────┐
│                    Linux 网络安全分层                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  L7 应用层安全                                        │   │
│  │  - WAF (ModSecurity/Nginx)                          │   │
│  │  - 应用认证/授权                                     │   │
│  │  - SQL 注入/XSS/CSRF 防护                            │   │
│  │  - DDoS 防护 (rate limit)                           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  L4 传输层安全                                        │   │
│  │  - 防火墙 (iptables/firewalld/nftables)             │   │
│  │  - 端口管控 (只开放必要端口)                          │   │
│  │  - TCP Wrapper (hosts.allow/hosts.deny)             │   │
│  │  - 连接数限制 (connlimit/hashlimit)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  L3 网络层安全                                        │   │
│  │  - IP 黑白名单                                       │   │
│  │  - 路由控制 (rp_filter)                              │   │
│  │  - ICMP 控制 (防 Ping)                               │   │
│  │  - 反向路径过滤                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  L2 数据链路层安全                                    │   │
│  │  - ARP 防护 (arptables)                              │   │
│  │  - MAC 地址过滤                                       │   │
│  │  - 交换机端口安全                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  内核安全                                             │   │
│  │  - sysctl 网络参数调优                                │   │
│  │  - SELinux / AppArmor                               │   │
│  │  - 内核模块裁剪                                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心概念

```
防火墙:
  包过滤 (Packet Filter):
    检查每个数据包的 IP/端口/协议/标志位, 决定放行或丢弃
    工作在网络层 (L3) 和传输层 (L4)
    速度块, 但不检查应用内容

  状态检测 (Stateful Inspection):
    追踪连接状态 (NEW/ESTABLISHED/RELATED/INVALID)
    只放行属于已建立连接的数据包
    比纯包过滤更安全

  NAT (Network Address Translation):
    SNAT: 修改源 IP (内网 → 外网)
    DNAT: 修改目标 IP (端口转发)
    MASQUERADE: 动态 SNAT (动态 IP 场景)

  连接追踪 (Connection Tracking):
    内核维护连接表 (/proc/net/nf_conntrack)
    记录每个连接的状态/源/目的/端口
    conntrack 表满 = 新连接被丢弃

iptables 五链四表:

  ┌─────────────────────────────────────────────────────────┐
  │                    iptables 架构                         │
  │                                                         │
  │  五链 (Chain) - 数据包经过的 5 个 Hook 点:                │
  │                                                         │
  │  PREROUTING → [路由判断] → FORWARD → POSTROUTING        │
  │       ↓                    ↑               ↓            │
  │  [路由判断]              [路由判断]                    │
  │       ↓                    ↑                            │
  │    INPUT → [本地进程] → OUTPUT → POSTROUTING           │
  │                                                         │
  │  四表 (Table) - 规则优先级 (从高到低):                    │
  │    raw       → 连接追踪豁免 (NOTRACK)                   │
  │    mangle    → 修改包内容 (TTL/TOS/MARK)                │
  │    nat       → 地址转换 (SNAT/DNAT/MASQUERADE)          │
  │    filter    → 过滤 (ACCEPT/DROP/REJECT)                │
  │                                                         │
  │  数据包流向:                                             │
  │    入站: PREROUTING → INPUT → 本地进程                  │
  │    出站: 本地进程 → OUTPUT → POSTROUTING                │
  │    转发: PREROUTING → FORWARD → POSTROUTING             │
  └─────────────────────────────────────────────────────────┘

  规则匹配顺序: 从上到下, 匹配即停止 (除非有 RETURN)
  默认策略 (Policy): 所有规则都不匹配时的动作 (ACCEPT/DROP)

  动作 (Target):
    ACCEPT:  放行
    DROP:    丢弃 (不回应, 对方超时)
    REJECT:  拒绝 (回应 ICMP unreachable, 对方立即知道)
    LOG:     记录日志 (不中断匹配)
    SNAT:    源地址转换
    DNAT:    目标地址转换
    MASQUERADE: 动态伪装
    REDIRECT: 重定向到本机端口
    RETURN:  返回上一级链
```

---

## 二、iptables

### 2.1 基础语法

```bash
# === iptables 命令格式 ===
# iptables [-t 表] [-I/A/D/F/L] 链 [规则] -j 动作

# -t table:      raw/mangle/nat/filter (默认 filter)
# -I chain:      Insert (插入到链首, 或指定位置)
# -A chain:      Append (追加到链尾)
# -D chain:      Delete (删除规则)
# -R chain:      Replace (替换规则)
# -F chain:      Flush (清空链所有规则)
# -L chain:      List (列出规则)
# -P chain:      Policy (设置默认策略)
# -N chain:      New (创建自定义链)
# -X chain:      Delete (删除自定义链)

# 匹配条件:
# -s IP/掩码:    源地址
# -d IP/掩码:    目标地址
# -p 协议:       tcp/udp/icmp/all
# --sport 端口:  源端口
# --dport 端口:  目标端口
# -i 接口:       入站网卡
# -o 接口:       出站网卡
# -m module:     扩展模块 (state/connlimit/hashlimit/mac/owner)

# === 查看规则 ===
iptables -L -n -v --line-numbers
# -n: 不解析 IP/端口 (更快)
# -v: 详细信息 (包计数/字节数)
# --line-numbers: 显示行号

# 查看指定表
iptables -t nat -L -n -v --line-numbers
iptables -t mangle -L -n -v
iptables -t raw -L -n -v

# 查看指定链
iptables -L INPUT -n -v --line-numbers
```

### 2.2 基础规则配置

```bash
# === 基础规则 ===

# 1. 清空所有规则 (配置前先清空)
iptables -F                          # 清空 filter 表
iptables -t nat -F                   # 清空 nat 表
iptables -t mangle -F                # 清空 mangle 表
iptables -X                          # 删除自定义链

# 2. 设置默认策略
iptables -P INPUT DROP               # 默认拒绝入站
iptables -P FORWARD DROP             # 默认拒绝转发
iptables -P OUTPUT ACCEPT            # 默认允许出站

# 3. 允许回环接口
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# 4. 允许已建立连接 (状态检测, 最重要!)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# 5. 允许 SSH (限制源 IP)
iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 22 -j ACCEPT

# 6. 允许 Web
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 7. 允许 ICMP (Ping)
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

# 8. 允许 DNS (如果是 DNS 服务器)
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT

# 9. 记录被拒绝的包 (可选, 排查用)
iptables -A INPUT -m limit --limit 5/min --limit-burst 10 -j LOG \
    --log-prefix "iptables-dropped: " --log-level 4

# 10. 最终丢弃 (默认策略已 DROP, 这条可选)
iptables -A INPUT -j DROP
```

### 2.3 IP 黑白名单

```bash
# === IP 白名单 (只允许指定 IP) ===

# 方式 1: 白名单链
iptables -N WHITELIST                                # 创建自定义链
iptables -A WHITELIST -s 192.168.1.0/24 -j ACCEPT    # 内网
iptables -A WHITELIST -s 10.0.0.0/8 -j ACCEPT        # VPN
iptables -A WHITELIST -s 172.16.0.0/12 -j ACCEPT     # Docker
iptables -A WHITELIST -j DROP                        # 其他丢弃

# 应用到指定端口
iptables -A INPUT -p tcp --dport 22 -j WHITELIST     # SSH
iptables -A INPUT -p tcp --dport 3306 -j WHITELIST   # MySQL
iptables -A INPUT -p tcp --dport 6379 -j WHITELIST   # Redis

# 方式 2: ipset (更高效, 适合大量 IP)
dnf install -y ipset

# 创建白名单集合
ipset create whitelist hash:net family inet hashsize 4096 maxelem 100000
ipset add whitelist 192.168.1.0/24
ipset add whitelist 10.0.0.0/8
ipset add whitelist 172.16.0.0/12

# 在 iptables 中引用
iptables -A INPUT -p tcp --dport 22 -m set --match-set whitelist src -j ACCEPT
iptables -A INPUT -p tcp --dport 3306 -m set --match-set whitelist src -j ACCEPT

# 查看
ipset list whitelist
ipset test whitelist 192.168.1.100

# 添加/删除
ipset add whitelist 8.8.8.8
ipset del whitelist 10.0.0.0/8

# === IP 黑名单 ===
# 方式 1: 单条规则
iptables -I INPUT 1 -s 1.2.3.4 -j DROP              # 插入到第 1 条
iptables -I INPUT 1 -s 5.6.7.0/24 -j DROP            # 封整个段

# 方式 2: ipset 黑名单
ipset create blacklist hash:ip family inet hashsize 4096 maxelem 100000 timeout 3600
# timeout 3600: 自动过期 (1 小时后自动删除, 适合临时封禁)

ipset add blacklist 1.2.3.4 timeout 86400            # 封禁 1 天
ipset add blacklist 5.6.7.8 timeout 3600             # 封禁 1 小时

iptables -I INPUT 1 -m set --match-set blacklist src -j DROP

# 动态封禁 (脚本)
# ban-ip.sh
#!/bin/bash
IP=$1
TIMEOUT=${2:-3600}
ipset add blacklist $IP timeout $TIMEOUT 2>/dev/null && echo "Banned $IP for ${TIMEOUT}s" || echo "Already banned or error"

# unban-ip.sh
#!/bin/bash
IP=$1
ipset del blacklist $IP 2>/dev/null && echo "Unbanned $IP" || echo "Not in blacklist"

# === 封禁国家/地区 (GeoIP) ===
# 安装 xtables-addons
dnf install -y xtables-addons
# 下载 GeoIP 数据库
/usr/libexec/xtables-addons/xt_geoip_dl
/usr/libexec/xtables-addons/xt_geoip_build -D /usr/share/xt_geoip/

# 封禁指定国家
iptables -A INPUT -m geoip --src-cc CN,RU -j DROP    # 封禁中国和俄罗斯
# 只允许指定国家
iptables -A INPUT -m geoip ! --src-cc CN -j DROP     # 只允许中国
```

### 2.4 应用防护

```bash
# === SSH 防护 ===

# 1. 限制 SSH 源 IP
iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 22 -j ACCEPT

# 2. 限制并发连接数
# 每个源 IP 最多 3 个 SSH 连接
iptables -A INPUT -p tcp --dport 22 -m connlimit --connlimit-above 3 -j DROP

# 3. 限制连接频率 (防暴力破解)
# 每分钟最多 5 个新连接, 突发 10 个
iptables -A INPUT -p tcp --dport 22 -m state --state NEW \
    -m recent --set --name SSH
iptables -A INPUT -p tcp --dport 22 -m state --state NEW \
    -m recent --update --seconds 60 --hitcount 5 --name SSH -j DROP
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -j ACCEPT

# 或使用 hashlimit
iptables -A INPUT -p tcp --dport 22 -m state --state NEW \
    -m hashlimit --hashlimit-name ssh \
    --hashlimit 5/min --hashlimit-burst 10 \
    --hashlimit-mode srcip --hashlimit-srcmask 32 \
    -j ACCEPT

# 4. 端口敲门 (Port Knocking)
# 顺序敲击端口后才开放 SSH
# 敲 7000 → 8000 → 9000 后开放 22
iptables -N SSH_KNOCK
iptables -A SSH_KNOCK -m recent --name knock1 --remove
iptables -A SSH_KNOCK -p tcp --dport 8000 -m recent --name knock2 --set -j DROP
iptables -A SSH_KNOCK -p tcp --dport 9000 -m recent --name knock3 --set -j DROP
iptables -A SSH_KNOCK -j DROP

iptables -N SSH_OPEN
iptables -A SSH_OPEN -m recent --name knock3 --remove
iptables -A SSH_OPEN -p tcp --dport 22 -j ACCEPT
iptables -A SSH_OPEN -j SSH_KNOCK

iptables -A INPUT -p tcp --dport 7000 -m recent --name knock1 --set -j DROP
iptables -A INPUT -p tcp --dport 8000 -m recent --name knock1 --update --seconds 10 -j SSH_KNOCK
iptables -A INPUT -p tcp --dport 9000 -m recent --name knock2 --update --seconds 10 -j SSH_OPEN
iptables -A INPUT -p tcp --dport 22 -m recent --name knock3 --update --seconds 30 -j SSH_OPEN

# === Web 防护 ===

# 1. 限制 HTTP 并发连接
iptables -A INPUT -p tcp --dport 80 -m connlimit \
    --connlimit-above 100 --connlimit-mask 32 -j DROP
# 每个 IP 最多 100 个 HTTP 连接

# 2. 限制请求频率 (防 CC 攻击)
iptables -A INPUT -p tcp --dport 80 -m state --state NEW \
    -m hashlimit --hashlimit-name http \
    --hashlimit 50/sec --hashlimit-burst 100 \
    --hashlimit-mode srcip -j ACCEPT

# 3. 限制 SYN 包 (防 SYN Flood)
iptables -A INPUT -p tcp --syn -m limit --limit 20/s --limit-burst 40 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# 4. 防端口扫描
iptables -N SCAN
iptables -A SCAN -m recent --name scan --set -j DROP
iptables -A SCAN -m recent --name scan --update --seconds 600 --hitcount 5 -j LOG \
    --log-prefix "Port scan: " --log-level 4
iptables -A INPUT -p tcp --tcp-flags SYN,ACK,FIN,RST RST -m recent --name scan --update --seconds 60 --hitcount 3 -j DROP

# === 数据库防护 ===

# MySQL 只允许应用服务器
iptables -A INPUT -s 192.168.1.20 -p tcp --dport 3306 -j ACCEPT   # app01
iptables -A INPUT -s 192.168.1.21 -p tcp --dport 3306 -j ACCEPT   # app02
iptables -A INPUT -p tcp --dport 3306 -j DROP                      # 其他拒绝

# Redis 只允许内网
iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 6379 -j ACCEPT
iptables -A INPUT -p tcp --dport 6379 -j DROP

# === NAT 与端口转发 ===

# SNAT (内网共享上网)
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 \
    -j SNAT --to-source 202.1.2.3
# 或动态 IP 用 MASQUERADE
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE

# DNAT (端口转发)
# 外部访问 202.1.2.3:8080 → 内网 192.168.1.20:80
iptables -t nat -A PREROUTING -p tcp --dport 8080 \
    -j DNAT --to-destination 192.168.1.20:80
iptables -A FORWARD -p tcp -d 192.168.1.20 --dport 80 -j ACCEPT

# 本地端口重定向 (80 → 8080)
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080
# 本地产生的流量也重定向
iptables -t nat -A OUTPUT -p tcp --dport 80 -j REDIRECT --to-ports 8080

# === 透明代理 ===
# 将内网 HTTP 流量重定向到代理 (如 Squid 3128)
iptables -t nat -A PREROUTING -s 192.168.1.0/24 -p tcp --dport 80 \
    -j REDIRECT --to-ports 3128
```

### 2.5 规则持久化

```bash
# === 规则保存与恢复 ===

# 保存当前规则
iptables-save > /etc/sysconfig/iptables

# 恢复规则
iptables-restore < /etc/sysconfig/iptables

# RHEL/Rocky: iptables-services
dnf install -y iptables-services
systemctl enable iptables
iptables-save > /etc/sysconfig/iptables
systemctl restart iptables

# Ubuntu: iptables-persistent
apt install -y iptables-persistent
iptables-save > /etc/iptables/rules.v4
ip6tables-save > /etc/iptables/rules.v6
netfilter-persistent save
netfilter-persistent reload

# === ipset 持久化 ===
ipset save > /etc/sysconfig/ipset
ipset restore < /etc/sysconfig/ipset

# systemd 服务 (先加载 ipset, 再加载 iptables)
cat > /etc/systemd/system/ipset-save.service << 'EOF'
[Unit]
Description=ipset persistent rules
Before=iptables.service
Before=firewalld.service
DefaultDependencies=no

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/ipset restore -f /etc/sysconfig/ipset
ExecStop=/sbin/ipset save /etc/sysconfig/ipset

[Install]
WantedBy=multi-user.target
EOF
systemctl enable ipset-save
```

### 2.6 完整生产配置

```bash
#!/bin/bash
# /opt/firewall/iptables-init.sh
# 生产环境 iptables 完整配置

# === 清空 ===
iptables -F
iptables -t nat -F
iptables -t mangle -F
iptables -X
iptables -t nat -X
iptables -t mangle -X

# === 默认策略 ===
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# === 基础规则 ===
# 回环
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# 已建立连接
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# 丢弃无效包
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# === SYN Flood 防护 ===
iptables -A INPUT -p tcp ! --syn -m state --state NEW -j DROP
iptables -A INPUT -p tcp --syn -m limit --limit 20/s --limit-burst 40 -j ACCEPT

# === ICMP 控制 ===
# 限制 Ping 频率
iptables -A INPUT -p icmp --icmp-type echo-request \
    -m limit --limit 1/s --limit-burst 5 -j ACCEPT
# 允许其他 ICMP (traceroute 等)
iptables -A INPUT -p icmp --icmp-type time-exceeded -j ACCEPT
iptables -A INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT

# === IP 黑白名单 ===
# 创建 ipset
ipset create whitelist hash:net -exist
ipset create blacklist hash:ip -exist timeout 3600

# 白名单 (信任 IP)
ipset add whitelist 192.168.1.0/24 -exist
ipset add whitelist 10.0.0.0/8 -exist

# 黑名单优先
iptables -A INPUT -m set --match-set blacklist src -j DROP
# 白名单放行
iptables -A INPUT -m set --match-set whitelist src -j ACCEPT

# === 管理服务 ===
# SSH (限源 + 限频)
iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 22 \
    -m connlimit --connlimit-above 3 -j DROP
iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 22 \
    -m state --state NEW -m hashlimit \
    --hashlimit-name ssh --hashlimit 5/min --hashlimit-burst 10 \
    --hashlimit-mode srcip -j ACCEPT

# === 业务服务 ===
# HTTP/HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 \
    -m connlimit --connlimit-above 100 --connlimit-mask 32 -j DROP
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

# === 内部服务 (限源) ===
# MySQL
iptables -A INPUT -s 192.168.1.20 -p tcp --dport 3306 -j ACCEPT
iptables -A INPUT -s 192.168.1.21 -p tcp --dport 3306 -j ACCEPT
# Redis
iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 6379 -j ACCEPT
# Kafka
iptables -A INPUT -s 192.168.1.0/24 -p tcp -m multiport --dports 9092,9093 -j ACCEPT
# Elasticsearch
iptables -A INPUT -s 192.168.1.0/24 -p tcp -m multiport --dports 9200,9300 -j ACCEPT

# === 监控 ===
# Prometheus (限源)
iptables -A INPUT -s 192.168.1.30 -p tcp --dport 9100 -j ACCEPT  # node_exporter
iptables -A INPUT -s 192.168.1.30 -p tcp --dport 9090 -j ACCEPT  # Prometheus

# === 日志 ===
iptables -A INPUT -m limit --limit 5/min --limit-burst 10 -j LOG \
    --log-prefix "iptables-dropped: " --log-level 4

# === 最终丢弃 ===
iptables -A INPUT -j DROP

# === 保存 ===
iptables-save > /etc/sysconfig/iptables
ipset save > /etc/sysconfig/ipset

echo "Firewall configured and saved."
```

---

## 三、firewalld

### 3.1 核心概念

```
firewalld — RHEL/CentOS 7+ 默认防火墙

  vs iptables:
    iptables:  命令行逐条规则, 难管理, 重载时断连
    firewalld: 动态管理, 区域(zone)概念, 运行时修改不断连

  核心概念:
    Zone (区域): 网络连接的信任级别
      public:    默认, 只允许 SSH/DHCP
      trusted:   信任, 允许所有
      internal:  内网, 信任度高
      work:      工作
      home:      家庭
      dmz:       非军事区, 只允许 SSH
      block:     拒绝所有 (ICMP 禁止)
      drop:      丢弃所有 (无响应)

    Service (服务): 预定义的端口/协议组合
      ssh:       tcp/22
      http:      tcp/80
      https:     tcp/443
      mysql:     tcp/3306
      dns:       tcp/53, udp/53

    Runtime vs Permanent:
      Runtime:   立即生效, 重启丢失
      Permanent: 写入配置, reload 后生效
      firewall-cmd --permanent → reload

    Rich Rule (富规则): 复杂规则
      源 IP + 服务 + 动作 + 日志
```

### 3.2 基础操作

```bash
# === 查看状态 ===
systemctl status firewalld
systemctl enable --now firewalld

firewall-cmd --state
firewall-cmd --reload                           # 重载配置 (不断连)
firewall-cmd --complete-reload                  # 完整重载 (断连)

# === Zone 管理 ===
# 查看默认 zone
firewall-cmd --get-default-zone
# public

# 查看所有 zone
firewall-cmd --get-zones

# 查看当前活跃 zone
firewall-cmd --get-active-zones

# 查看指定 zone 配置
firewall-cmd --zone=public --list-all

# 修改网卡所属 zone
firewall-cmd --zone=public --change-interface=eth0 --permanent

# 设置默认 zone
firewall-cmd --set-default-zone=public

# === Service 管理 ===
# 查看所有预定义服务
firewall-cmd --get-services

# 查看当前 zone 允许的服务
firewall-cmd --zone=public --list-services

# 添加服务
firewall-cmd --zone=public --add-service=http --permanent
firewall-cmd --zone=public --add-service=https --permanent
firewall-cmd --zone=public --add-service=ssh --permanent

# 移除服务
firewall-cmd --zone=public --remove-service=dhcpv6-client --permanent

# 重载生效
firewall-cmd --reload

# === Port 管理 ===
# 查看开放的端口
firewall-cmd --zone=public --list-ports

# 开放端口
firewall-cmd --zone=public --add-port=8080/tcp --permanent
firewall-cmd --zone=public --add-port=8443/tcp --permanent
firewall-cmd --zone=public --add-port=53/udp --permanent
firewall-cmd --zone=public --add-port=1000-2000/tcp --permanent  # 端口范围

# 移除端口
firewall-cmd --zone=public --remove-port=8080/tcp --permanent

# 重载
firewall-cmd --reload

# === IP 黑白名单 ===
# 白名单: 信任源 IP
firewall-cmd --zone=trusted --add-source=192.168.1.0/24 --permanent
firewall-cmd --zone=trusted --add-source=10.0.0.0/8 --permanent

# 黑名单: 拒绝源 IP (用 drop zone)
firewall-cmd --zone=drop --add-source=1.2.3.4 --permanent
firewall-cmd --zone=drop --add-source=5.6.7.0/24 --permanent

# 或使用 block zone (返回 ICMP 禁止)
firewall-cmd --zone=block --add-source=1.2.3.4 --permanent

# 查看各 zone 的 source
firewall-cmd --zone=trusted --list-sources
firewall-cmd --zone=drop --list-sources

# 移除
firewall-cmd --zone=trusted --remove-source=10.0.0.0/8 --permanent
firewall-cmd --zone=drop --remove-source=1.2.3.4 --permanent

# 重载
firewall-cmd --reload

# === ICMP 控制 ===
# 查看 ICMP 类型
firewall-cmd --get-icmptypes

# 查看允许的 ICMP
firewall-cmd --zone=public --list-icmp-blocks

# 禁止 Ping
firewall-cmd --zone=public --add-icmp-block=echo-request --permanent

# 禁止所有 ICMP
firewall-cmd --zone=public --add-icmp-block-inversion --permanent

# 允许 Ping (移除禁止)
firewall-cmd --zone=public --remove-icmp-block=echo-request --permanent

# 重载
firewall-cmd --reload
```

### 3.3 富规则（Rich Rules）

```bash
# === Rich Rule 语法 ===
# rule [family="ipv4|ipv6"]
# [source address="IP|CIDR" invert="yes"]
# [destination address="IP|CIDR"]
# service name="service"
# port port="N" protocol="tcp|udp"
# [forward-port port="N" protocol="tcp" to-port="M" to-addr="IP"]
# [icmp-type name="type"]
# [protocol value="protocol"]
# [log prefix="text" level="level" limit value="rate"]
# [audit limit value="rate"]
# accept | reject | drop | mark

# === SSH 限制 (只允许指定 IP) ===
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" \
    source address="192.168.1.0/24" \
    service name="ssh" \
    accept' --permanent

# 拒绝其他 SSH
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" \
    service name="ssh" \
    drop' --permanent

# === 端口限制 (限源 IP) ===
# MySQL 只允许 app01
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" \
    source address="192.168.1.20" \
    port port="3306" protocol="tcp" \
    accept' --permanent

# Redis 只允许内网
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" \
    source address="192.168.1.0/24" \
    port port="6379" protocol="tcp" \
    accept' --permanent

# === 限频规则 (防暴力破解) ===
# SSH 每分钟最多 5 个新连接
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" \
    service name="ssh" \
    limit value="5/m" \
    accept' --permanent

# 超过频率的记录日志并丢弃
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" \
    service name="ssh" \
    limit value="1/m" \
    log prefix="ssh-brute: " level="warning" \
    drop' --permanent

# === IP 封禁 ===
# 封禁单个 IP
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" \
    source address="1.2.3.4" \
    drop' --permanent

# 封禁网段
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" \
    source address="5.6.7.0/24" \
    reject type="icmp-admin-prohibited"' --permanent

# === 端口转发 ===
# 80 → 8080 (本机)
firewall-cmd --zone=public --add-forward-port=port=80:proto=tcp:toport=8080 --permanent
# 或用 rich rule
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" \
    forward-port port="80" protocol="tcp" \
    to-port="8080"' --permanent

# 端口转发到其他机器
firewall-cmd --zone=public --add-forward-port=port=80:proto=tcp:toport=80:toaddr=192.168.1.20 --permanent
# 开启 masquerade
firewall-cmd --zone=public --add-masquerade --permanent

# === 限并发 ===
# Rich rule 不直接支持 connlimit, 需用直接规则 (见 3.4)

# === 查看所有富规则 ===
firewall-cmd --zone=public --list-rich-rules

# 删除富规则
firewall-cmd --zone=public --remove-rich-rule='\
    rule family="ipv4" \
    source address="1.2.3.4" \
    drop' --permanent

# 重载
firewall-cmd --reload
```

### 3.4 直接规则（Direct Rules）

```bash
# === firewalld 直接使用 iptables 语法 ===
# 当 rich rule 不够用时, 可直接写 iptables 规则

# 查看直接规则
firewall-cmd --direct --get-all-chains
firewall-cmd --direct --get-all-rules

# 添加直接规则
# 限制每 IP HTTP 并发 50 连接
firewall-cmd --permanent --direct -A INPUT 0 \
    -p tcp --dport 80 -m connlimit \
    --connlimit-above 50 --connlimit-mask 32 -j DROP

# 限制 SYN 包频率
firewall-cmd --permanent --direct -A INPUT 0 \
    -p tcp --syn -m limit --limit 20/s --limit-burst 40 -j ACCEPT

# 丢弃无效包
firewall-cmd --permanent --direct -A INPUT 0 \
    -m conntrack --ctstate INVALID -j DROP

# 查看直接规则
firewall-cmd --direct --get-rules ipv4 filter INPUT

# 删除直接规则
firewall-cmd --permanent --direct -D INPUT 0 \
    -p tcp --dport 80 -m connlimit \
    --connlimit-above 50 --connlimit-mask 32 -j DROP

# 重载
firewall-cmd --reload
```

### 3.5 自定义服务

```bash
# === 创建自定义服务 ===
# /etc/firewalld/services/app-service.xml
cat > /etc/firewalld/services/app-service.xml << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<service>
  <short>App Service</short>
  <description>My Application Service (8080/TCP)</description>
  <port protocol="tcp" port="8080"/>
  <port protocol="tcp" port="8443"/>
</service>
EOF

# 重载 firewalld
firewall-cmd --reload

# 使用自定义服务
firewall-cmd --zone=public --add-service=app-service --permanent
firewall-cmd --reload

# === 完整生产配置 ===
#!/bin/bash
# /opt/firewall/firewalld-init.sh

# 重置
firewall-cmd --reload

# 基础
firewall-cmd --set-default-zone=public --permanent

# 信任 IP → trusted zone
firewall-cmd --zone=trusted --add-source=192.168.1.0/24 --permanent
firewall-cmd --zone=trusted --add-source=10.0.0.0/8 --permanent

# 封禁 IP → drop zone
firewall-cmd --zone=drop --add-source=1.2.3.4 --permanent

# 公开服务
firewall-cmd --zone=public --add-service=ssh --permanent
firewall-cmd --zone=public --add-service=http --permanent
firewall-cmd --zone=public --add-service=https --permanent

# SSH 限频
firewall-cmd --zone=public --add-rich-rule='\
    rule service name="ssh" limit value="5/m" accept' --permanent

# 内部服务限源
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" source address="192.168.1.20" \
    port port="3306" protocol="tcp" accept' --permanent
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" source address="192.168.1.0/24" \
    port port="6379" protocol="tcp" accept' --permanent

# 监控
firewall-cmd --zone=public --add-rich-rule='\
    rule family="ipv4" source address="192.168.1.30" \
    port port="9100" protocol="tcp" accept' --permanent

# SYN Flood 防护
firewall-cmd --permanent --direct -A INPUT 0 \
    -p tcp --syn -m limit --limit 20/s --limit-burst 40 -j ACCEPT
firewall-cmd --permanent --direct -A INPUT 0 \
    -m conntrack --ctstate INVALID -j DROP

# 禁止 Ping (可选)
# firewall-cmd --zone=public --add-icmp-block=echo-request --permanent

# 重载
firewall-cmd --reload

echo "Firewalld configured."

# 查看结果
firewall-cmd --zone=public --list-all
firewall-cmd --zone=trusted --list-all
firewall-cmd --zone=drop --list-all
```

---

## 四、nftables

### 4.1 概述

```
nftables — iptables 的继任者 (Linux 3.13+, RHEL 8+ 默认)

  vs iptables:
    iptables:  分离的工具 (iptables/ip6tables/ebtables/arptables)
               每条规则单独插入, 效率低
    nftables:  统一框架 (IPv4/IPv6/ARP/bridge)
               原子性操作, 一次性加载所有规则
               更简洁的语法, 更高效

  兼容性:
    RHEL 8+: firewalld 后端默认使用 nftables
    iptables 命令仍可用 (通过 iptables-nft 兼容层)
    但建议新部署直接使用 nftables 语法
```

### 4.2 基础语法

```bash
# === 查看规则 ===
nft list ruleset

# === 清空所有规则 ===
nft flush ruleset

# === 创建表 ===
nft add table inet filter
# inet: 同时处理 IPv4 和 IPv6

# === 创建链 ===
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add chain inet filter forward '{ type filter hook forward priority 0; policy drop; }'
nft add chain inet filter output '{ type filter hook output priority 0; policy accept; }'

# === 基础规则 ===
# 回环
nft add rule inet filter input iif "lo" accept
# 已建立连接
nft add rule inet filter input ct state established,related accept
# 无效包丢弃
nft add rule inet filter input ct state invalid drop
# SSH
nft add rule inet filter input tcp dport 22 accept
# HTTP/HTTPS
nft add rule inet filter input tcp dport '{ 80, 443 }' accept
# ICMP (IPv4 + IPv6)
nft add rule inet filter input ip protocol icmp accept
nft add rule inet filter input ip6 nexthdr icmpv6 accept

# === IP 黑白名单 ===
# 白名单
nft add rule inet filter input ip saddr 192.168.1.0/24 accept
# 黑名单
nft add rule inet filter input ip saddr 1.2.3.4 drop
nft add rule inet filter input ip saddr 5.6.7.0/24 drop

# === 限频 (防暴力) ===
nft add rule inet filter input tcp dport 22 \
    ct state new limit rate 5/minute burst 10 packets accept

# === 限制并发 ===
nft add rule inet filter input tcp dport 80 \
    ct state new meter http-conns '{ ip saddr limit rate over 100/second }' drop

# === 配置文件 ===
# /etc/nftables.nft
cat > /etc/nftables.nft << 'EOF'
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        # 回环
        iif "lo" accept

        # 已建立连接
        ct state established,related accept
        ct state invalid drop

        # SYN Flood 防护
        tcp flags & (fin|syn|rst|ack) == syn limit rate 20/second burst 40 packets accept

        # ICMP
        ip protocol icmp accept
        ip6 nexthdr icmpv6 accept

        # 白名单
        ip saddr { 192.168.1.0/24, 10.0.0.0/8 } accept

        # SSH (限频)
        tcp dport 22 ct state new limit rate 5/minute burst 10 packets accept

        # HTTP/HTTPS
        tcp dport { 80, 443 } accept

        # MySQL (限源)
        ip saddr { 192.168.1.20, 192.168.1.21 } tcp dport 3306 accept

        # Redis (限内网)
        ip saddr 192.168.1.0/24 tcp dport 6379 accept

        # 监控
        ip saddr 192.168.1.30 tcp dport 9100 accept

        # 日志
        limit rate 5/minute log prefix "nft-dropped: "
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
EOF

# 应用
nft -f /etc/nftables.nft

# 持久化
systemctl enable nftables
systemctl start nftables
```

---

## 五、内核网络安全参数

```bash
# === /etc/sysctl.d/99-network-security.conf ===
cat > /etc/sysctl.d/99-network-security.conf << 'EOF'

# === 反向路径过滤 (防 IP 欺骗) ===
# 严格模式: 数据包的源 IP 必须可通过同一接口路由回去
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# === 禁用 ICMP 重定向 (防中间人攻击) ===
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# === 禁用源路由 (防路由欺骗) ===
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# === 禁用 ICMP 广播响应 (防 Smurf 攻击) ===
net.ipv4.icmp_echo_ignore_broadcasts = 1

# === 启用 SYN Cookies (防 SYN Flood) ===
net.ipv4.tcp_syncookies = 1

# === 增加 SYN 队列 ===
net.ipv4.tcp_max_syn_backlog = 65535

# === SYN+ACK 重试次数 (减少) ===
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 3

# === 连接追踪表大小 ===
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 7200
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 30
net.netfilter.nf_conntrack_tcp_timeout_close_wait = 30
net.netfilter.nf_conntrack_tcp_timeout_fin_wait = 30

# === 禁用 IP 转发 (如果不是路由器) ===
net.ipv4.ip_forward = 0
# 如果是 Docker/K8s 节点, 必须设为 1
# net.ipv4.ip_forward = 1

# === 禁用 bc...

# === TCP keepalive ===
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3

# === TIME_WAIT 优化 ===
net.ipv4.tcp_max_tw_buckets = 1048576
net.ipv4.tcp_tw_reuse = 1

# === TCP 快速回收 (生产慎用, 可能导致 NAT 环境问题) ===
# net.ipv4.tcp_fin_timeout = 15

# === 内存调优 ===
net.ipv4.tcp_mem = 786432 1048576 1572864
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# === 日志可疑包 ===
net.ipv4.conf.all.log_martians = 0
# 设为 1 可记录源地址异常的包 (排查用, 生产可能日志过多)
EOF

sysctl -p /etc/sysctl.d/99-network-security.conf

# 注意:
# 1. Docker/K8s 节点必须开启 ip_forward=1
# 2. conntrack_max 需根据内存调整 (每条约 300 字节)
# 3. tcp_tw_reuse=1 在 NAT 环境可能导致问题, 建议仅在服务端开启
```

---

## 六、应用屏蔽实战

### 6.1 屏蔽指定应用的网络访问

```bash
# === 方法 1: 通过 PID/UID 屏蔽 ===

# 找到应用 PID
PID=$(pgrep -f "my-app")

# 通过 cgroup 限制 (systemd 方式)
# 创建 systemd unit, 限制网络
cat > /etc/systemd/system/restricted-app.service << 'EOF'
[Unit]
Description=Restricted App
After=network.target

[Service]
Type=simple
ExecStart=/opt/app/my-app
# 限制网络命名空间 (私有不联网)
PrivateNetwork=yes
# 或限制访问特定地址
IPAddressDeny=any
IPAddressAllow=192.168.1.0/24
# 限制设备访问
DevicePolicy=closed

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now restricted-app

# === 方法 2: iptables owner 模块 ===
# 按 UID 屏蔽
# 创建专用用户运行应用
useradd -r appuser
# iptables 规则: 禁止 appuser 访问外网
iptables -A OUTPUT -m owner --uid-owner appuser -j DROP
# 允许 appuser 访问内网
iptables -A OUTPUT -m owner --uid-owner appuser -d 192.168.1.0/24 -j ACCEPT
iptables -A OUTPUT -m owner --uid-owner appuser -d 127.0.0.1 -j ACCEPT
# 其他丢弃
iptables -A OUTPUT -m owner --uid-owner appuser -j DROP

# 运行应用
sudo -u appuser /opt/app/my-app

# === 方法 3: 网络命名空间隔离 ===
# 创建独立的网络命名空间 (完全隔离)
ip netns add isolated
# 只配置回环
ip netns exec isolated ip link set lo up
# 应用在此命名空间中运行, 无任何网络
ip netns exec isolated /opt/app/my-app

# veth pair 连接命名空间 (有限网络)
ip link add veth-host type veth peer name veth-ns
ip link set veth-ns netns isolated
ip addr add 10.200.1.1/24 dev veth-host
ip link set veth-host up
ip netns exec isolated ip addr add 10.200.1.2/24 dev veth-ns
ip netns exec isolated ip link set veth-ns up
ip netns exec isolated ip route add default via 10.200.1.1

# 在宿主机用 iptables 限制 veth-ns 的流量
iptables -A FORWARD -i veth-host -s 10.200.1.2 -d 192.168.1.0/24 -j ACCEPT
iptables -A FORWARD -i veth-host -s 10.200.1.2 -j DROP

# 清理
ip netns del isolated
```

### 6.2 屏蔽特定端口/协议

```bash
# === 屏蔽应用出站端口 ===

# 禁止访问外部 SSH
iptables -A OUTPUT -p tcp --dport 22 -d ! 192.168.1.0/24 -j DROP

# 禁止访问外部 DNS (强制使用内部 DNS)
iptables -A OUTPUT -p udp --dport 53 -d ! 192.168.1.1 -j DROP
iptables -A OUTPUT -p tcp --dport 53 -d ! 192.168.1.1 -j DROP

# 禁止应用访问外部 Redis
iptables -A OUTPUT -p tcp --dport 6379 -d ! 192.168.1.0/24 -j DROP

# 禁止应用访问外部 MySQL
iptables -A OUTPUT -p tcp --dport 3306 -d ! 192.168.1.0/24 -j DROP

# 禁止出站 Telnet
iptables -A OUTPUT -p tcp --dport 23 -j DROP

# 禁止出站 IRC
iptables -A OUTPUT -p tcp --dport 6667 -j DROP

# 禁止所有出站, 只允许必要的 (白名单模式)
iptables -P OUTPUT DROP
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT        # HTTP (更新)
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT       # HTTPS (更新)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT        # DNS
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT        # DNS
iptables -A OUTPUT -d 192.168.1.0/24 -j ACCEPT        # 内网
```

### 6.3 封禁恶意 IP（自动化）

```bash
# === 自动封禁恶意 IP ===

# 1. 从日志分析恶意 IP 并自动封禁
#!/bin/bash
# /opt/security/auto-ban.sh
# 分析 Nginx 日志, 自动封禁恶意 IP

LOG=/var/log/nginx/access.log
THRESHOLD=100                  # 每分钟超过 100 次请求
BANTIME=3600                   # 封禁 1 小时

# 分析最近 1 分钟的日志
tail -10000 $LOG | \
    awk -v date="$(date -d '1 min ago' '+%d/%b/%Y:%H:%M')" \
    '$0 ~ date {print $1}' | \
    sort | uniq -c | sort -rn | \
    while read count ip; do
        if [ $count -gt $THRESHOLD ]; then
            # 检查是否已封禁
            if ! ipset test blacklist $ip 2>/dev/null; then
                ipset add blacklist $ip timeout $BANTIME 2>/dev/null
                logger "Auto-ban: $ip (requests: $count in 1 min)"
            fi
        fi
    done

# Cron 每分钟执行
echo "* * * * * root /opt/security/auto-ban.sh" > /etc/cron.d/auto-ban

# 2. 封禁 SSH 暴力破解
#!/bin/bash
# /opt/security/ssh-ban.sh
# 分析 SSH 日志, 自动封禁暴力破解

LOG=/var/log/secure
THRESHOLD=5                    # 5 次失败
BANTIME=86400                  # 封禁 24 小时

# 分析最近 5 分钟的 SSH 失败日志
journalctl -u sshd --since "5 min ago" | \
    grep "Failed password" | \
    awk '{for(i=1;i<=NF;i++) if($i=="from") print $(i+1)}' | \
    sort | uniq -c | sort -rn | \
    while read count ip; do
        if [ $count -gt $THRESHOLD ]; then
            if ! ipset test blacklist $ip 2>/dev/null; then
                ipset add blacklist $ip timeout $BANTIME
                logger "SSH-ban: $ip (failed: $count)"
            fi
        fi
    done

echo "*/5 * * * * root /opt/security/ssh-ban.sh" > /etc/cron.d/ssh-ban

# 3. 使用 Fail2Ban (推荐, 自动化封禁)
dnf install -y fail2ban

# /etc/fail2ban/jail.local
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
banaction = firewallcmd-ipset        # 或 iptables-ipset-proto6
backend = systemd

[sshd]
enabled = true
port = ssh
maxretry = 3
bantime = 86400

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = firewallcmd-ipset[name=ReqIP, port=80, protocol=tcp]
logpath = /var/log/nginx/error.log
findtime = 600
maxretry = 10
bantime = 3600

[nginx-botsearch]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

systemctl enable --now fail2ban
fail2ban-client status
fail2ban-client status sshd
fail2ban-client set sshd unbanip 1.2.3.4
```

### 6.4 应用层防护

```bash
# === Nginx 应用层防护 ===

# /etc/nginx/nginx.conf
http {
    # === 限频 ===
    limit_req_zone $binary_remote_addr zone=req_limit:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    # === 限速 ===
    limit_rate 1m;                   # 限速 1MB/s

    server {
        listen 80;

        # 请求频率限制
        limit_req zone=req_limit burst=20 nodelay;
        # 并发连接限制
        limit_conn conn_limit 10;

        # 屏蔽恶意 User-Agent
        if ($http_user_agent ~* (bot|spider|crawler|scan)) {
            return 403;
        }

        # 屏蔽特定路径
        location ~* /\.(git|env|sql|bak) {
            deny all;
            return 404;
        }

        # IP 白名单
        location /admin {
            allow 192.168.1.0/24;
            deny all;
            proxy_pass http://backend;
        }

        # IP 黑名单
        # geo 模块定义 IP 列表
        geo $blocked_ip {
            default 0;
            1.2.3.4 1;
            5.6.7.0/24 1;
        }

        if ($blocked_ip) {
            return 403;
        }
    }
}

# === Nginx 加载 IP 黑名单文件 ===
# /etc/nginx/blacklist.conf
cat > /etc/nginx/blacklist.conf << 'EOF'
deny 1.2.3.4;
deny 5.6.7.0/24;
deny 10.0.0.1;
EOF

# nginx.conf 中 include
# http {
#     include /etc/nginx/blacklist.conf;
# }

# 动态更新黑名单 (不重启 Nginx)
echo "deny 9.8.7.6;" >> /etc/nginx/blacklist.conf
nginx -t && nginx -s reload
```

---

## 七、云环境安全组

```
云环境安全组 (Security Group) vs 本地防火墙:

  安全组 (云端):
    - 云平台提供 (AWS/Aliyun/Tencent)
    - 实例级防火墙, 在虚拟化层过滤
    - 状态检测: 入站规则控制, 出站默认全通
    - 多安全组可叠加
    - 无法过滤 ICMP 类型和应用层

  本地防火墙 (iptables/firewalld):
    - 操作系统提供
    - 主机级防火墙, 在内核网络栈过滤
    - 更精细的控制 (connlimit/hashlimit/rich rule)
    - 可配合 ipset 处理大量 IP

  最佳实践: 双层防护
    云安全组: 控制端口/源 IP (粗粒度)
    本地防火墙: 细粒度控制 (限频/封禁/日志)
```

```bash
# AWS CLI 操作安全组 (示例)
# 查看安全组
aws ec2 describe-security-groups --group-ids sg-xxx

# 添加入站规则
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxx \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# 限制源 IP
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxx \
    --protocol tcp \
    --port 22 \
    --cidr 192.168.1.0/24

# 删除规则
aws ec2 revoke-security-group-ingress \
    --group-id sg-xxx \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

# 阿里云 CLI
aliyun ecs AuthorizeSecurityGroup \
    --SecurityGroupId sg-xxx \
    --IpProtocol tcp \
    --PortRange 443/443 \
    --SourceCidrIp 0.0.0.0/0
```

---

## 八、入侵检测

### 8.1 文件完整性监控

```bash
# === AIDE (文件完整性检查) ===
dnf install -y aide

# 初始化数据库
aide --init
cp /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# 检查
aide --check

# 更新数据库 (修改后)
aide --update
cp /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# 定时检查
echo "0 3 * * * root /usr/sbin/aide --check | mail -s 'AIDE Report' security@example.com" > /etc/cron.d/aide
```

### 8.2 Rootkit 检测

```bash
# === rkhunter ===
dnf install -y rkhunter

# 更新数据库
rkhunter --update

# 扫描
rkhunter --check --sk

# 定时扫描
echo "0 4 * * * root /usr/bin/rkhunter --check --sk --report-warnings-only | mail -s 'rkhunter Report' security@example.com" > /etc/cron.d/rkhunter

# === clamav (病毒扫描) ===
dnf install -y clamav clamav-update
freshclam
clamscan -r /home
clamscan -r --max-filesize=100M --max-scansize=400M /data
```

### 8.3 审计日志

```bash
# === auditd (系统审计) ===
dnf install -y audit
systemctl enable --now auditd

# 监控文件访问
auditctl -w /etc/passwd -p wa -k identity_changes
auditctl -w /etc/sudoers -p wa -k sudo_changes
auditctl -w /etc/ssh/sshd_config -p wa -k ssh_config

# 监控命令执行
auditctl -a always,exit -F arch=b64 -S execve -k commands

# 查看审计日志
ausearch -k identity_changes
ausearch -k ssh_config
aureport --summary
aureport --file

# 持久化 (/etc/audit/audit.rules)
cat > /etc/audit/rules.d/hardening.rules << 'EOF'
# 监控用户/组文件
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

# 监控 SUDO
-w /etc/sudoers -p wa -k sudo
-w /etc/sudoers.d -p wa -k sudo

# 监控 SSH 配置
-w /etc/ssh/sshd_config -p wa -k sshd

# 监控 cron
-w /etc/crontab -p wa -k cron
-w /etc/cron.d -p wa -k cron
-w /etc/cron.daily -p wa -k cron
-w /etc/cron.hourly -p wa -k cron

# 监控系统启动
-w /etc/systemd/system -p wa -k systemd
-w /lib/systemd/system -p wa -k systemd

# 监控网络环境
-w /etc/hosts -p wa -k network
-w /etc/sysconfig/network -p wa -k network
-w /etc/resolv.conf -p wa -k network

# 监控登录相关
-w /var/log/lastlog -p wa -k logins
-w /var/log/faillog -p wa -k logins

# 锁定审计规则 (最后一条)
-e 2
EOF

augenrules --load
```

---

## 九、对比总结

### 9.1 防火墙方案对比

| 维度 | iptables | firewalld | nftables |
|:---|:---|:---|:---|
| 定位 | 传统防火墙 | RHEL 默认防火墙 | 新一代防火墙 |
| 语法 | 命令行逐条 | XML + CLI | 统一脚本语法 |
| 区域概念 | ❌ | ⭐ Zone | ❌ |
| 动态更新 | ❌ 重载断连 | ⭐ 不断连 | ⭐ 原子替换 |
| IPv6 | ip6tables (分离) | ⭐ 统一 | ⭐ inet 统一 |
| ipset 支持 | ⭐ 原生 | 通过 direct | ⭐ 集合 |
| 性能 | 中 | 中 (底层 iptables/nftables) | ⭐ 高 |
| 生态 | ⭐ 最成熟 | RHEL 生态 | 逐渐替代 |
| 适用 | 通用 | RHEL/CentOS | 新部署 |

### 9.2 iptables vs firewalld vs nftables 选择

```
选择建议:

  已有 RHEL/Rocky/CentOS:
    → firewalld (默认, Zone 概念清晰, 富规则够用)
    → 复杂场景用 direct rules 或 nftables

  Ubuntu/Debian:
    → UFW (简单) 或 iptables (灵活) 或 nftables (新)

  新部署 (内核 5.10+):
    → nftables (语法统一, 性能好)
    → 或 firewalld (RHEL 系, 后端已是 nftables)

  Docker/K8s 环境:
    → Docker 默认操作 iptables (不要手动改 iptables filter 表!)
    → K8s kube-proxy 默认操作 iptables/ipvs
    → 宿主机防火墙用 firewalld 或 nftables (与容器不冲突)
    → 容器网络隔离用 NetworkPolicy

  关键原则:
    1. 一个节点只用一个防火墙管理工具
    2. 不要混用 iptables 和 firewalld (规则冲突)
    3. Docker/K8s 节点的 iptables 由容器管理, 不要手动改
    4. 先配置, 再测试, 最后持久化
```

### 9.3 安全加固检查清单

```
内核层:
  □ rp_filter = 1 (反向路径过滤)
  □ accept_redirects = 0 (禁用 ICMP 重定向)
  □ accept_source_route = 0 (禁用源路由)
  □ icmp_echo_ignore_broadcasts = 1 (防 Smurf)
  □ tcp_syncookies = 1 (防 SYN Flood)
  □ nf_conntrack_max 合理设置
  □ 禁用不需要的内核模块 (dccp/sctp/rds)

防火墙:
  □ 默认策略 INPUT DROP (白名单模式)
  □ 只开放必要端口
  □ 管理端口 (SSH/DB) 限源 IP
  □ SSH 限频 (防暴力破解)
  □ Web 限并发/限频 (防 CC)
  □ SYN Flood 防护
  □ 规则持久化 (重启不丢失)
  □ ipset 管理大量 IP

应用层:
  □ Nginx rate limit / conn limit
  □ IP 黑白名单
  □ WAF (ModSecurity)
  □ 隐藏服务器版本信息
  □ 屏蔽敏感路径 (.git/.env)
  □ HTTPS + HSTS

入侵检测:
  □ Fail2Ban (自动封禁)
  □ AIDE (文件完整性)
  □ auditd (系统审计)
  □ rkhunter (Rootkit 检测)
  □ 日志集中收集

审计:
  □ 定期审查防火墙规则
  □ 定期检查开放端口 (ss/nmap)
  □ 定期检查用户/权限
  □ 定期更新系统
  □ 安全扫描 (Lynis)
```

---

## 十、配置文件速查表

| 文件/路径 | 用途 |
|:---|:---|
| `/etc/sysconfig/iptables` | iptables 规则文件 (RHEL) |
| `/etc/iptables/rules.v4` | iptables 规则文件 (Ubuntu) |
| `/etc/sysconfig/ipset` | ipset 规则文件 |
| `/etc/firewalld/firewalld.conf` | firewalld 主配置 |
| `/etc/firewalld/zones/` | firewalld zone 配置 |
| `/etc/firewalld/services/` | firewalld 自定义服务 |
| `/etc/firewalld/direct.xml` | firewalld 直接规则 |
| `/etc/nftables.nft` | nftables 配置文件 |
| `/etc/sysctl.d/99-network-security.conf` | 内核网络安全参数 |
| `/etc/hosts.allow` | TCP Wrapper 允许 |
| `/etc/hosts.deny` | TCP Wrapper 拒绝 |
| `/etc/fail2ban/jail.local` | Fail2Ban 配置 |
| `/etc/audit/rules.d/` | auditd 审计规则 |
| `/etc/aide.conf` | AIDE 配置 |
| `/etc/nginx/blacklist.conf` | Nginx IP 黑名单 |

---

*最后更新: 2026-07-12*
