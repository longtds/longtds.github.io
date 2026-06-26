# 进阶

> 网络进阶 = **VLAN/Trunk 实战 + 路由协议(OSPF/BGP)入门 + NAT/PAT + 防火墙(iptables/nftables) + 负载均衡四层/七层 + HTTPS/TLS + 高可用 VRRP + Linux Bond/Team**。本章面向运维 5-50 台、需要规划机房网络、配置 LB/防火墙、做基础性能调优的工程师。

## 一、二层进阶：VLAN/Trunk/Bond

### 1.1 Trunk 实战（与交换机互联）

```
场景: Linux 服务器一根线接交换机 Trunk 口，承载多 VLAN
交换机侧:
  interface GigabitEthernet0/1
    switchport mode trunk
    switchport trunk allowed vlan 10,20,100
    switchport trunk native vlan 1
```

```bash
# Linux 侧
# 加载 8021q 模块
modprobe 8021q
echo 8021q >> /etc/modules-load.d/vlan.conf

# 创建 VLAN 子接口
ip link add link eth0 name eth0.10 type vlan id 10
ip link add link eth0 name eth0.20 type vlan id 20
ip addr add 10.10.1.5/24 dev eth0.10
ip addr add 10.20.1.5/24 dev eth0.20
ip link set eth0.10 up && ip link set eth0.20 up
```

### 1.2 Bond（链路聚合 / 主备）

```
模式:
  0  balance-rr      轮询（需交换机 LACP/静态聚合）
  1  active-backup   主备 ⭐ 最常用，对交换机无要求
  2  balance-xor     按 hash
  4  802.3ad / LACP  ⭐ 生产首选（需交换机配 LACP）
  5  balance-tlb     发送负载均衡
  6  balance-alb     收发负载均衡
```

```bash
# 加载模块
modprobe bonding

# 创建 bond0（active-backup）
ip link add bond0 type bond mode active-backup miimon 100
ip link set eth0 master bond0
ip link set eth1 master bond0
ip addr add 192.168.1.10/24 dev bond0
ip link set bond0 up

# 看状态
cat /proc/net/bonding/bond0
```

```yaml
# netplan LACP 范例
network:
  version: 2
  bonds:
    bond0:
      interfaces: [eth0, eth1]
      parameters:
        mode: 802.3ad
        lacp-rate: fast
        mii-monitor-interval: 100
        transmit-hash-policy: layer3+4
      addresses: [192.168.1.10/24]
```

### 1.3 Bridge（Linux 网桥）

```bash
# 虚拟二层交换机，常用于 KVM/Docker
ip link add br0 type bridge
ip link set eth0 master br0
ip link set br0 up
ip addr add 192.168.1.10/24 dev br0

# 看 fdb (MAC 表)
bridge fdb show
bridge link show

# brctl 老命令（已不推荐）
brctl show
```

## 二、三层进阶：路由协议入门

### 2.1 静态 vs 动态

```
静态: 手工配，简单稳定，规模小
动态:
  IGP (内部网关):
    RIP    距离矢量 v1/v2，已少用
    OSPF   链路状态，企业主流 ⭐
    IS-IS  运营商主流
  EGP (外部网关):
    BGP    互联网路由唯一选择 ⭐
```

### 2.2 OSPF 基础

```
特点:
  - 链路状态算法（每路由器有完整拓扑）
  - 区域划分（Area 0 骨干 + Area X 边缘）
  - 收敛快（秒级）
  - SPF (Dijkstra) 算法

配置思路（Cisco IOS）:
  router ospf 1
    network 10.0.0.0 0.0.0.255 area 0
    network 10.1.0.0 0.0.0.255 area 1
```

```bash
# Linux 用 FRR (FRRouting) 跑 OSPF
apt install frr
vi /etc/frr/frr.conf
# router ospf
#   network 10.0.0.0/24 area 0
systemctl restart frr

# 看邻居 / 路由
vtysh -c "show ip ospf neighbor"
vtysh -c "show ip route ospf"
```

### 2.3 BGP 基础（云原生重要）

```
角色:
  iBGP   AS 内部
  eBGP   AS 之间（互联网骨干）
  
属性（决策顺序）:
  Weight (Cisco) → Local Preference → AS-Path 长度
  → Origin → MED → eBGP > iBGP → IGP cost → Router ID

云原生应用:
  - Calico CNI BGP 模式（K8s Pod 路由）
  - Cilium BGP Control Plane
  - MetalLB BGP 模式
  - 公有云 BGP Anycast
```

```bash
# FRR BGP 范例
vtysh
  conf t
  router bgp 65000
    bgp router-id 10.0.0.1
    neighbor 10.0.0.2 remote-as 65001
    network 192.168.10.0/24

# 看
vtysh -c "show bgp summary"
vtysh -c "show ip bgp"
```

## 三、NAT 与 PAT

### 3.1 NAT 类型

```
SNAT (Source NAT)        改源 IP，私网出公网常见
DNAT (Destination NAT)   改目的 IP，公网映射到内网
PAT (Port Address Translation)  多对一 + 端口复用，家用路由器原理
MASQUERADE              动态 SNAT（用接口当前 IP）
Full Cone / Restricted / Symmetric   NAT 类型，P2P 穿越要关注
```

### 3.2 iptables NAT 实战

```bash
# 内网出公网（典型 SNAT）
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE
# 或固定 IP
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j SNAT --to 1.2.3.4

# 端口映射（DNAT）
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
  -j DNAT --to-destination 192.168.1.10:8080

# 开 forward
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.d/99-forward.conf

# 保存
iptables-save > /etc/iptables/rules.v4
```

### 3.3 nftables NAT 实战

```bash
nft add table ip nat
nft add chain ip nat postrouting { type nat hook postrouting priority 100\; }
nft add rule ip nat postrouting oifname "eth0" ip saddr 192.168.1.0/24 masquerade

nft add chain ip nat prerouting { type nat hook prerouting priority -100\; }
nft add rule ip nat prerouting iifname "eth0" tcp dport 80 dnat to 192.168.1.10:8080
```

## 四、iptables / nftables 防火墙

### 4.1 iptables 四表五链

```
表 (table):
  filter   过滤 ⭐ 默认
  nat      NAT
  mangle   报文修改
  raw      连接跟踪豁免

链 (chain):
  PREROUTING   入站之前
  INPUT        入本机
  FORWARD      转发
  OUTPUT       本机发出
  POSTROUTING  出站之前
```

### 4.2 iptables 基础模板

```bash
# 清空
iptables -F
iptables -X
iptables -t nat -F

# 默认策略
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 放行回环
iptables -A INPUT -i lo -j ACCEPT

# 放行已建立连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 放行 SSH (限速防爆破)
iptables -A INPUT -p tcp --dport 22 -m state --state NEW \
  -m recent --set --name SSH
iptables -A INPUT -p tcp --dport 22 -m state --state NEW \
  -m recent --update --seconds 60 --hitcount 4 --name SSH -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# 放行 HTTP/HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

# 放行 ICMP（限速）
iptables -A INPUT -p icmp -m limit --limit 1/sec -j ACCEPT

# 持久化
apt install iptables-persistent
netfilter-persistent save
```

### 4.3 nftables 现代写法

```bash
# /etc/nftables.conf
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
        iif lo accept
        icmp type echo-request limit rate 10/second accept
        tcp dport 22 ct state new limit rate 3/minute accept
        tcp dport { 80, 443 } accept
        ip saddr 192.168.0.0/16 tcp dport 3306 accept
        log prefix "[nft drop] " level info
    }
}

nft -f /etc/nftables.conf
systemctl enable --now nftables
```

### 4.4 firewalld（RHEL 系上层封装）

```bash
firewall-cmd --get-active-zones
firewall-cmd --list-all
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=1.2.3.4 reject'
firewall-cmd --reload

# 端口转发
firewall-cmd --permanent --add-forward-port=port=80:proto=tcp:toport=8080
```

## 五、负载均衡

### 5.1 L4 vs L7

| 维度 | L4 (TCP/UDP) | L7 (HTTP) |
|:---|:---|:---|
| 工作层 | 传输层 | 应用层 |
| 看到内容 | 仅 IP/Port | URL/Header/Body |
| 性能 | 高（百万 QPS） | 低（万 QPS） |
| 灵活性 | 低 | 高（路由/限流/重写）|
| 代表 | LVS / HAProxy TCP / Nginx stream | Nginx / HAProxy / Envoy / Traefik |
| 场景 | 入口 / 数据库前 | API 网关 / 微服务 |

### 5.2 LVS（L4 / 内核态最快）

```
模式:
  NAT   通过路由器 SNAT/DNAT，简单但带宽瓶颈
  DR    直接路由（Direct Routing），最常用 ⭐
  TUN   IP-in-IP，跨网段
  Fullnat 阿里改良版（Server 看到 LVS IP）

调度算法:
  rr / wrr            轮询
  lc / wlc            最少连接
  sh / dh             源/目的 hash（会话保持）
```

```bash
# 安装
apt install ipvsadm

# 创建虚拟服务
ipvsadm -A -t 1.2.3.4:80 -s wlc

# 加 real server (DR 模式)
ipvsadm -a -t 1.2.3.4:80 -r 10.0.0.10:80 -g -w 1
ipvsadm -a -t 1.2.3.4:80 -r 10.0.0.11:80 -g -w 1

# 看
ipvsadm -L -n
ipvsadm -L -n --stats

# 保存
ipvsadm-save > /etc/ipvsadm.rules
```

### 5.3 Nginx（L7）

```nginx
# /etc/nginx/conf.d/api.conf
upstream api_backend {
    least_conn;
    server 10.0.0.10:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.11:8080 max_fails=3 fail_timeout=30s weight=2;
    server 10.0.0.12:8080 backup;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+AESGCM:EDH+AESGCM;

    location / {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
        proxy_next_upstream error timeout http_502 http_503;
    }

    location /health {
        access_log off;
        return 200 "ok\n";
    }
}
```

### 5.4 HAProxy（L4/L7）

```haproxy
global
    maxconn 100000
    log 127.0.0.1 local0
    nbproc 1
    nbthread 8
    cpu-map auto:1/1-8 0-7

defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s
    option httplog
    option dontlognull

frontend api_in
    bind *:443 ssl crt /etc/haproxy/cert.pem
    http-request set-header X-Real-IP %[src]
    default_backend api_backend

backend api_backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server s1 10.0.0.10:8080 check inter 2s fall 3 rise 2
    server s2 10.0.0.11:8080 check inter 2s fall 3 rise 2
```

## 六、HTTPS / TLS 实战

### 6.1 TLS 握手

```
TLS 1.2 (4 个 RTT 含 TCP):
  ClientHello (支持 cipher) → 
  ServerHello + 证书 + ServerKeyExchange ←
  ClientKeyExchange + ChangeCipherSpec → 
  ChangeCipherSpec ←

TLS 1.3 (1 RTT):
  ClientHello (含 key share) → 
  ServerHello + 证书 + Finished ←
  Finished → 

0-RTT: 重连时
```

### 6.2 证书

```
类型:
  DV   域名验证（最低，Let's Encrypt 默认）
  OV   组织验证
  EV   扩展验证（浏览器绿条，已淡化）

通配符:
  *.example.com   仅匹配一级子域
  SAN 多域名扩展

链:
  Root CA → Intermediate CA → Leaf
  服务端要发 Leaf + Intermediate
```

### 6.3 Let's Encrypt + certbot

```bash
# 安装
apt install certbot python3-certbot-nginx

# 申请（HTTP-01 验证 + Nginx 自动配）
certbot --nginx -d api.example.com -d www.example.com

# 仅申请（手工配置）
certbot certonly --webroot -w /var/www -d example.com

# DNS-01（通配符必用）
certbot certonly --manual --preferred-challenges dns -d "*.example.com"

# 续期（自动）
systemctl status certbot.timer

# 测试续期
certbot renew --dry-run
```

### 6.4 自签证书（内网测试）

```bash
# 一行流（自签 + 私钥）
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem \
  -sha256 -days 365 -nodes -subj "/CN=internal.example.com" \
  -addext "subjectAltName=DNS:internal.example.com,DNS:*.internal.example.com,IP:10.0.0.10"

# 看证书
openssl x509 -in cert.pem -noout -text
openssl x509 -in cert.pem -noout -dates -subject -issuer

# 测远端
openssl s_client -connect example.com:443 -servername example.com -showcerts
```

### 6.5 国密（SM2/SM3/SM4）

```
背景:
  国密版 OpenSSL（TASSL / GmSSL）
  应用: 金融 / 党政 / 信创
  TLS 1.3 with SM2/SM4

主流软件:
  Tongsuo (铜锁 / 阿里)
  GmSSL (北大)
  openEuler 默认带
```

## 七、高可用：VRRP / Keepalived

### 7.1 VRRP 协议

```
作用: 多台路由器共享虚拟 IP（VIP），主挂从接管
原理:
  - Master 周期发 VRRP advert
  - Backup 收不到 → 接管 VIP
  - 心跳间隔 ~1s
```

### 7.2 Keepalived（Linux 实现）

```bash
# /etc/keepalived/keepalived.conf
vrrp_script chk_nginx {
    script "killall -0 nginx"
    interval 2
    weight -20
}

vrrp_instance VI_1 {
    state MASTER                        # 备机写 BACKUP
    interface eth0
    virtual_router_id 51
    priority 100                         # 备机 90
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass mysecret
    }
    virtual_ipaddress {
        192.168.1.100/24
    }
    track_script {
        chk_nginx
    }
}

systemctl enable --now keepalived
```

### 7.3 LVS + Keepalived 经典架构

```
[Internet]
   │
   ▼
[Keepalived + LVS Master (VIP)] ←→ [Keepalived + LVS Backup]
        │              │
        ▼              ▼
   [RS1] [RS2]  [RS3] [RS4]
```

## 八、Linux 调优：网络方向

### 8.1 必调 sysctl

```ini
# /etc/sysctl.d/99-network.conf

# 队列
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 32768

# 缓冲区
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# TIME_WAIT
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_max_tw_buckets = 1048576

# Keep-alive
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3

# 抗 SYN flood
net.ipv4.tcp_syncookies = 1

# 端口范围
net.ipv4.ip_local_port_range = 1024 65535

# 拥塞算法（推 BBR）
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq

# ARP（大规模）
net.ipv4.neigh.default.gc_thresh1 = 4096
net.ipv4.neigh.default.gc_thresh2 = 8192
net.ipv4.neigh.default.gc_thresh3 = 16384

# 转发（路由器/NAT）
net.ipv4.ip_forward = 1
```

### 8.2 BBR 拥塞算法

```bash
# 检查
sysctl net.ipv4.tcp_congestion_control
cat /proc/sys/net/ipv4/tcp_available_congestion_control

# 开 BBR
echo "net.core.default_qdisc=fq" >> /etc/sysctl.d/99-bbr.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.d/99-bbr.conf
sysctl --system

# 看连接是否用 BBR
ss -tin | grep bbr
```

## 九、IPv6 入门

```
地址:
  128 bit，冒分十六进制
  示例: 2001:db8::1
  缩写: 连续 0 用 ::，仅一次

类型:
  ::1                  回环
  fe80::/10            链路本地
  fc00::/7             ULA（私网）
  2000::/3             全球单播

工具:
  ip -6 a
  ping6 -c 4 ::1
  traceroute6
  ss -6 -tln
```

### 9.1 双栈配置

```yaml
# netplan 双栈
ethernets:
  eth0:
    addresses:
      - 192.168.1.10/24
      - "2001:db8::10/64"
    routes:
      - to: default
        via: 192.168.1.1
      - to: "::/0"
        via: "2001:db8::1"
```

## 十、连通性进阶测试

```bash
# 端口扫描
nmap -sS -p 1-1000 host                  # SYN 扫描
nmap -sU -p 53,123 host                  # UDP
nmap -O host                              # OS 指纹
nc -zv host 80                            # 单端口

# 带宽压测
iperf3 -c server -t 60 -P 8 -O 5         # 多并发 + 跳过前 5s
iperf3 -c server -u -b 1G -t 30          # UDP 1G

# DNS 压测
dnsperf -d query.txt -s 8.8.8.8

# HTTP 压测
wrk -t 8 -c 1000 -d 30s --latency http://x/
hey -n 100000 -c 1000 http://x/
vegeta attack -rate=1000/s -duration=60s -targets=t.txt | vegeta report
```

## 十一、典型坑（进阶）

| 坑 | 建议 |
|:---|:---|
| **iptables 默认 ACCEPT** | 默认 DROP + 显式放行 |
| **iptables 没保存重启丢** | iptables-persistent / netfilter-persistent save |
| **改 sysctl 没生效** | sysctl --system |
| **Bond 模式 0 无交换机配合** | 选 active-backup 或 802.3ad |
| **VRRP 双主（脑裂）** | priority 差距大 + nopreempt + 心跳网独立 |
| **certbot 续期挂** | systemctl status certbot.timer / cron |
| **Nginx 默认 proxy_buffer 小** | 调 proxy_buffer_size/buffers |
| **未带 Connection ""** | proxy 长连接复用失效 |
| **HAProxy 单线程** | nbthread 多线程 + cpu-map |
| **BGP 邻居不起** | 检查 AS / Router-ID / TCP 179 |
| **MASQUERADE 性能差** | 高并发用 SNAT 固定 IP |

## 十二、进阶 Checklist

```
二层:
☐ VLAN/Trunk 配过
☐ Bond LACP 上线
☐ Bridge 用于 KVM

三层:
☐ OSPF / BGP 实验过
☐ 静态路由 + 多网关
☐ NAT / DNAT / SNAT

防火墙:
☐ iptables 完整 ruleset
☐ nftables 改造一次
☐ firewalld / ufw

LB:
☐ Nginx 反向代理
☐ HAProxy L4/L7
☐ LVS DR 模式
☐ Keepalived VRRP

HTTPS:
☐ Let's Encrypt + certbot
☐ 自签 + 内网
☐ TLS 1.3
☐ 国密了解

调优:
☐ /etc/sysctl.d/ 持久化
☐ BBR + fq
☐ ARP 阈值
```

## 十三、推荐栈

```
配置:    netplan / NetworkManager / Ansible role
DNS:    systemd-resolved / dnsmasq / Bind
LB:     LVS / HAProxy / Nginx / Envoy
HA:     Keepalived (VRRP)
NAT:    nftables / iptables (兼容)
VPN:    WireGuard ⭐ / OpenVPN
路由:    FRR (OSPF/BGP)
监控:    blackbox_exporter / smokeping / mtr
抓包:    tcpdump / Wireshark / tshark
压测:    iperf3 / wrk / hey / vegeta / dnsperf
```

## 十四、学习路径

```
进阶（3-6 月）:
  1. VLAN/Trunk + Bond LACP 上线
  2. iptables 完整 ruleset → nftables 改造
  3. Nginx + HAProxy 反向代理 + 健康检查
  4. LVS DR + Keepalived VRRP
  5. Let's Encrypt + 自签证书
  6. TLS 1.3 / 证书链排查
  7. /etc/sysctl.d/ 标准 + BBR
  8. OSPF / BGP FRR 实验
  9. NAT / 端口映射 / 多网关
  10. 国密 SM2/SM3/SM4 了解
```

> 📖 **核心判断**：进阶 = **Bond + VLAN + iptables/nftables 完整 ruleset + LVS/Nginx/HAProxy + Keepalived + TLS + sysctl 调优**。能搭出"LVS+Keepalived+Nginx 三层负载"经典架构、能解释 TLS 1.3 握手、能写 200 行 nftables ruleset、能调网络 sysctl 把 QPS 拉到 10w+，就具备高级章资格。
