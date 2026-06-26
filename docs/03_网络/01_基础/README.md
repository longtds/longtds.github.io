# 基础

> 网络基础 = **OSI/TCP-IP 模型 + 二层(ARP/VLAN) + 三层(IP/路由/ICMP) + 传输层(TCP/UDP) + 应用层(HTTP/DNS) + 子网计算 + Linux 网络命令**。掌握本章后能独立读懂抓包、配置静态 IP、解释三次握手、做基础排查。本章面向新手和入职 1 年内的工程师。

## 一、OSI 7 层与 TCP/IP 4 层

### 1.1 模型对比

```
OSI 7 层               TCP/IP 4 层      协议示例           设备
──────────────────────────────────────────────────────────────
7. 应用 Application    应用层           HTTP/DNS/SSH/FTP    应用进程
6. 表示 Presentation   ─┘               TLS/JSON/MIME       (并入应用)
5. 会话 Session        ─┘               RPC/Session
──────────────────────────────────────────────────────────────
4. 传输 Transport      传输层           TCP/UDP/QUIC        L4 LB
──────────────────────────────────────────────────────────────
3. 网络 Network        网络层           IP/ICMP/IGMP        路由器/L3 交换
──────────────────────────────────────────────────────────────
2. 数据链路 Data Link  网络接口层       Ethernet/ARP/VLAN   交换机/网桥
1. 物理 Physical       ─┘               电信号/光信号       网线/光纤/网卡
```

### 1.2 数据封装

```
应用数据
  └─ 加 HTTP 头 → HTTP 报文
      └─ 加 TCP 头 → TCP 段 (segment)
          └─ 加 IP 头 → IP 包 (packet)
              └─ 加 以太网头/尾 → 以太网帧 (frame)
                  └─ 物理信号 → 比特流
```

### 1.3 关键头字段速记

```
Ethernet 帧:    源 MAC | 目的 MAC | 类型(0x0800=IPv4) | Payload | FCS
IPv4 头:       版本/TTL/协议(TCP=6,UDP=17)/源 IP/目的 IP/校验和
TCP 头:        源端口/目的端口/序号 Seq/确认号 Ack/Flags(SYN/ACK/FIN/RST)/窗口/校验和
UDP 头:        源端口/目的端口/长度/校验和
```

## 二、二层：以太网与 ARP

### 2.1 MAC 地址

```
6 字节，前 3 字节 OUI（厂商），后 3 字节序列号
广播地址: FF:FF:FF:FF:FF:FF
组播:     01:xx:xx:xx:xx:xx
单播:     第一字节最低位 = 0

# 看
ip link show
cat /sys/class/net/eth0/address
ethtool -P eth0                    # Permanent address
```

### 2.2 ARP（IP → MAC）

```
工作流程:
  1. 主机 A 要发包给 IP X，查 ARP 缓存
  2. 没有 → 广播 ARP Request "谁是 IP X？告诉我 MAC"
  3. IP X 主机回 ARP Reply（单播）
  4. 缓存到 ARP 表

ARP 仅在同一二层广播域内有效
跨网段 → 找网关，目的 MAC 写网关 MAC（IP 不变）
```

```bash
ip neigh                            # 看 ARP 表（推荐）
arp -an                             # 老命令
ip neigh flush all                  # 清缓存

# 绑定静态
ip neigh add 192.168.1.1 lladdr 00:11:22:33:44:55 dev eth0

# 抓 ARP
tcpdump -i eth0 -nn arp
```

### 2.3 VLAN（虚拟局域网）

```
作用: 一根线 / 一台交换机隔离多个广播域
原理: 帧加 4 字节 802.1Q tag (含 VLAN ID 12 bit)
ID 范围: 1-4094 (4096 - 保留)

类型:
  Access  端口属一个 VLAN，接终端
  Trunk   端口允许多 VLAN，接交换机/路由器
  Native  Trunk 上不打 tag 的默认 VLAN
```

```bash
# Linux 创建 VLAN 子接口
ip link add link eth0 name eth0.100 type vlan id 100
ip addr add 10.100.1.10/24 dev eth0.100
ip link set eth0.100 up

# netplan
vlans:
  vlan100:
    id: 100
    link: eth0
    addresses: [10.100.1.10/24]

# 验证
ip -d link show eth0.100
```

### 2.4 STP（生成树）

```
作用: 防止二层环路造成广播风暴
协议: STP / RSTP / MSTP

概念:
  Root Bridge       根桥（优先级最小）
  Root Port         去根桥最短路径
  Designated Port   每段网络的唯一转发口
  Blocked Port      被阻塞的口（防环）

变种:
  PVST+   Cisco 每 VLAN 一棵树
  MSTP    标准多实例
```

## 三、三层：IP 与路由

### 3.1 IPv4 地址结构

```
32 bit，点分十进制: 192.168.1.10
网络位 + 主机位（用子网掩码切分）

CIDR 表示: 192.168.1.0/24  ← 前 24 bit 是网络位

私有地址（RFC 1918）:
  10.0.0.0/8           大型企业
  172.16.0.0/12        中型
  192.168.0.0/16       小型/家用

特殊:
  127.0.0.0/8          回环 (loopback)
  169.254.0.0/16       链路本地 (DHCP 失败)
  224.0.0.0/4          组播
  255.255.255.255      广播
```

### 3.2 子网计算（必会）

```
192.168.1.0/26 拆分:
  /26 = 26 网络位 + 6 主机位
  每子网 2^6 = 64 个地址
  可用主机 64 - 2 (网络号 + 广播) = 62

  192.168.1.0/26    网段 1: 0-63    可用 1-62    广播 .63
  192.168.1.64/26   网段 2: 64-127  可用 65-126  广播 .127
  192.168.1.128/26  网段 3: 128-191 可用 129-190 广播 .191
  192.168.1.192/26  网段 4: 192-255 可用 193-254 广播 .255

掩码速记:
  /24 → 255.255.255.0    256 个
  /25 → 255.255.255.128  128 个
  /26 → 255.255.255.192  64 个
  /27 → 255.255.255.224  32 个
  /28 → 255.255.255.240  16 个
  /29 → 255.255.255.248  8 个
  /30 → 255.255.255.252  4 个 (点对点常用)
  /32 → 单 IP
```

```bash
# 计算工具
ipcalc 192.168.1.0/26
sipcalc 10.0.0.0/8
```

### 3.3 路由

```
路由表三要素: 目的网段 / 下一跳 / 出接口

匹配规则: 最长前缀匹配
  路由表:
    0.0.0.0/0     → 192.168.1.1   (默认路由)
    10.0.0.0/8    → 192.168.1.254
    10.1.0.0/16   → 192.168.1.100
  
  发包到 10.1.5.20 → 匹配 10.1.0.0/16 (前缀最长)
```

```bash
# 看路由
ip route                            # 推荐
ip r
ip route get 8.8.8.8               # 看走哪条 ⭐

# 加路由
ip route add 10.0.0.0/8 via 192.168.1.254
ip route add default via 192.168.1.1
ip route add 10.1.0.0/16 dev eth1   # 直连

# 持久化（netplan/NetworkManager 见进阶）
```

### 3.4 ICMP（探活/报错）

```
常见类型:
  0  Echo Reply
  3  Destination Unreachable
  8  Echo Request   ← ping
  11 Time Exceeded  ← traceroute 用
  
工作原理:
  ping = ICMP Echo Request + Echo Reply
  traceroute = 发 TTL=1,2,3... 让路径每跳返回 Time Exceeded
```

```bash
ping -c 4 1.1.1.1
ping -i 0.2 -c 100 host                # 0.2s 间隔
ping -s 1472 -M do host                 # MTU 测试（don't fragment）

traceroute -n example.com               # 不解析 DNS
traceroute -T -p 443 example.com       # TCP 443 traceroute
mtr -n example.com                       # 持续探测 ⭐
```

## 四、传输层：TCP 与 UDP

### 4.1 端口

```
端口范围 0-65535

知名端口 (0-1023):
  22   SSH
  53   DNS
  80   HTTP
  443  HTTPS
  3306 MySQL
  6379 Redis

注册端口 (1024-49151)
动态端口 (49152-65535)

Linux 默认源端口范围:
  net.ipv4.ip_local_port_range = 32768 60999
```

### 4.2 TCP 三次握手 / 四次挥手

```
建立 (3-way handshake):
  Client                Server
    │  SYN seq=x           │
    │ ───────────────────► │
    │                      │
    │  SYN+ACK seq=y,ack=x+1│
    │ ◄─────────────────── │
    │                      │
    │  ACK ack=y+1         │
    │ ───────────────────► │
    │                      │
    [ ESTABLISHED ]

关闭 (4-way handshake):
  Client                Server
    │  FIN                 │
    │ ───────────────────► │  CLOSE_WAIT
    │                      │
    │  ACK                 │
    │ ◄─────────────────── │
    │                      │  (服务端处理剩余)
    │  FIN                 │
    │ ◄─────────────────── │  LAST_ACK
    │                      │
    │  ACK                 │
    │ ───────────────────► │  CLOSED
    TIME_WAIT (2MSL)
    └─ 等待残留包消失
```

### 4.3 TCP 状态机（必懂）

```
LISTEN          监听
SYN_SENT        发了 SYN，等回应
SYN_RECV        收到 SYN，回了 SYN+ACK，等 ACK
ESTABLISHED     已连接 ⭐

FIN_WAIT_1      主动方发 FIN
FIN_WAIT_2      主动方收 ACK，等对方 FIN
TIME_WAIT       主动方等 2MSL 才彻底关
CLOSE_WAIT      被动方收 FIN，应用还没 close ⭐
LAST_ACK        被动方发 FIN，等最后 ACK
CLOSING         双方同时发 FIN
CLOSED          已关
```

```bash
# 看状态
ss -tan
ss -tan state established
ss -tan state time-wait | wc -l

# 关键场景:
# TIME_WAIT 多   → 频繁主动关连接，调 tcp_tw_reuse=1
# CLOSE_WAIT 多  → 应用没 close socket（代码 bug）
# SYN_RECV 多    → 可能 SYN flood，开 tcp_syncookies
```

### 4.4 UDP

```
特点: 无连接 / 不可靠 / 简单 / 低开销
适合: DNS / DHCP / 视频流 / 游戏 / QUIC（基于 UDP）
报文: 头部仅 8 字节
```

### 4.5 TCP vs UDP

| 维度 | TCP | UDP |
|:---|:---|:---|
| 连接 | 面向连接 | 无连接 |
| 可靠 | 重传 + 确认 | 不保证 |
| 顺序 | 保证 | 不保证 |
| 开销 | 大（20+ 字节头） | 小（8 字节头） |
| 拥塞控制 | 有 | 无 |
| 应用 | HTTP/SSH/MySQL | DNS/DHCP/视频/QUIC |

## 五、应用层：HTTP/DNS/SSH

### 5.1 HTTP

```
请求方法:
  GET     获取
  POST    创建/提交
  PUT     替换
  DELETE  删除
  PATCH   局部更新
  HEAD    仅 header
  OPTIONS CORS 预检

状态码:
  1xx  信息
  2xx  成功
       200 OK
       201 Created
       204 No Content
  3xx  重定向
       301 永久  302 临时  304 缓存有效
  4xx  客户端错
       400 Bad Request  401 未认证  403 禁止  404 不存在  429 限流
  5xx  服务端错
       500 内部错  502 Bad Gateway  503 不可用  504 网关超时

Header 关键:
  Host          目标域名（HTTP 1.1 必带）
  User-Agent
  Accept / Accept-Encoding
  Content-Type / Content-Length
  Cookie / Set-Cookie
  Authorization
  Cache-Control / ETag / If-None-Match
  X-Forwarded-For / X-Real-IP
```

```bash
# curl 实战
curl -v https://api.example.com/         # 看握手 + Header
curl -I https://example.com              # 仅 header
curl -X POST -H "Content-Type: application/json" -d '{"k":"v"}' https://api/
curl -L https://example.com              # 跟随重定向
curl -o file.bin https://...             # 下载
curl -w "@curl-format.txt" -o /dev/null -s https://...  # 时延分析
```

### 5.2 DNS

```
工作流程:
  1. 应用问 example.com → 本机 /etc/hosts
  2. 本机 stub resolver → 系统配置的 DNS（resolv.conf）
  3. 本地 DNS（递归解析器）→ Root → TLD → 权威
  4. 缓存（按 TTL）

记录类型:
  A      IPv4 地址
  AAAA   IPv6
  CNAME  别名
  MX     邮件交换
  NS     域名服务器
  TXT    任意文本（SPF/DKIM/验证）
  SOA    起始权威
  PTR    反向 (IP → name)
  SRV    服务发现
```

```bash
dig example.com                          # 标准查询
dig example.com +short
dig @8.8.8.8 example.com
dig example.com MX
dig +trace example.com                   # 看完整解析链
dig -x 8.8.8.8                           # 反向查询

host example.com
nslookup example.com                     # 老命令

# 系统配置
cat /etc/resolv.conf
resolvectl status
resolvectl flush-caches                  # 清缓存
```

### 5.3 SSH

```
端口 22 / TCP
密钥认证（推荐） + 密码（不推荐）

密钥类型:
  RSA       老牌，推 4096 位以上
  ED25519   现代，推荐 ⭐（短小快安全）
  ECDSA     椭圆曲线
```

```bash
# 生成密钥
ssh-keygen -t ed25519 -C "alice@example.com"

# 部署公钥
ssh-copy-id user@host

# 配置 ~/.ssh/config
Host bastion
    HostName 1.2.3.4
    User alice
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ForwardAgent yes

# 跳板
ssh -J bastion target-host

# 端口转发
ssh -L 8080:internal:80 bastion         # 本地 8080 → 远程 internal:80
ssh -R 9000:localhost:22 bastion        # 反向转发
ssh -D 1080 bastion                     # SOCKS5 代理
```

## 六、Linux 网络命令工具箱

### 6.1 接口与地址（iproute2）

```bash
ip a                                    # 看所有接口
ip -br a                                # 简洁
ip a show eth0
ip link set eth0 up|down
ip link set eth0 mtu 9000

ip addr add 192.168.1.10/24 dev eth0
ip addr del 192.168.1.10/24 dev eth0
```

### 6.2 路由

```bash
ip route                                # 路由表
ip route add 10.0.0.0/8 via 192.168.1.254
ip route del 10.0.0.0/8
ip route get 8.8.8.8                    # 看走哪条

route -n                                # 老命令
netstat -rn                              # 老命令
```

### 6.3 监听与连接

```bash
ss -tln                                  # TCP 监听
ss -tunlp                                # TCP+UDP+进程
ss -tan state established
ss -s                                    # 全局统计

netstat -tnlp                            # 老命令（不推荐）
lsof -i :8080                            # 端口占用
lsof -i tcp:8080
```

### 6.4 连通性

```bash
ping -c 4 host
ping -i 0.5 -c 100 host
ping6 ::1

traceroute -n host
traceroute -T -p 443 host
mtr -n host                              # 持续 ⭐

# DNS
dig host; host host; nslookup host
```

### 6.5 抓包入门

```bash
tcpdump -i eth0 -nn                      # -nn 不解析 IP/端口
tcpdump -i any host 1.2.3.4              # 任意接口
tcpdump -i eth0 port 80
tcpdump -i eth0 -nn -c 100 'tcp port 80'

# 保存到文件后 Wireshark 看
tcpdump -i eth0 -w trace.pcap host 1.2.3.4
wireshark trace.pcap                     # 图形化
tshark -r trace.pcap                     # 命令行
```

## 七、入门必会场景

### 7.1 配静态 IP（Ubuntu netplan）

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
```

```bash
netplan generate
netplan try                              # 2 分钟无确认自动回滚
netplan apply
```

### 7.2 端口被谁占用

```bash
ss -tlnp | grep :8080
lsof -i :8080
fuser 8080/tcp

# 看进程详情
ps -ef | grep PID
```

### 7.3 测网络连通性

```bash
ping -c 4 host                            # 2 层 + 3 层
traceroute host                           # 看路径
curl -v https://host/                     # 7 层
nc -zv host 443                           # 测端口
nc -zv host 1-1000                        # 扫端口段
```

### 7.4 测带宽

```bash
# Server
iperf3 -s

# Client
iperf3 -c server -t 30                    # 30s
iperf3 -c server -P 8                     # 8 并发
iperf3 -c server -u -b 1G                 # UDP 1G
```

### 7.5 看 DNS 走哪个

```bash
resolvectl status
cat /etc/resolv.conf
dig example.com +trace
nslookup example.com
```

## 八、抓包速查（场景）

```bash
# 三次握手抓 SYN
tcpdump -i eth0 -nn 'tcp[tcpflags] & tcp-syn != 0 and not tcp[tcpflags] & tcp-ack != 0'

# 看 HTTP 请求行
tcpdump -i eth0 -nn -A 'tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'

# 看 DNS 查询
tcpdump -i any -nn port 53

# 看 RST
tcpdump -i eth0 -nn 'tcp[tcpflags] & tcp-rst != 0'

# 仅某主机
tcpdump -i eth0 -nn host 1.2.3.4
tcpdump -i eth0 -nn 'src host 1.2.3.4 and dst port 443'
```

## 九、入门必练 20 题

```
1.  说出 TCP 三次握手每个包的 Seq/Ack/Flags
2.  192.168.1.0/26 有多少可用主机？
3.  /etc/hosts 和 DNS 谁优先？
4.  TIME_WAIT 状态为什么存在？多久消失？
5.  CLOSE_WAIT 多是谁的问题？
6.  default route 改用 eth1: 命令
7.  抓 src 10.0.0.5 dst port 80 的包
8.  Linux 端口被谁占用：ss / lsof
9.  curl 访问 https://x 超时，怎么定位？
10. ping 通但 curl 不通，可能原因？
11. ARP 缓存清理命令
12. mtr 看到第 5 跳 100% 丢包是什么意思？
13. iperf3 测出 800 Mbps（千兆口），正常吗？
14. tcpdump 加 -nn 的作用
15. HTTP 状态码 502 vs 504 vs 503 区别
16. 配静态 IP 后丢了 SSH 怎么救？(留 console / IPMI)
17. resolv.conf 失效后如何手工查 DNS？(dig @8.8.8.8)
18. ip neigh 看到 INCOMPLETE 状态什么含义？
19. ip route get 1.2.3.4 输出怎么读？
20. nc -zv 用来干嘛？
```

## 十、典型坑

| 坑 | 建议 |
|:---|:---|
| **改完 IP 丢 SSH** | 留 console 接入路径 / netplan try |
| **netstat 慢/老** | 用 ss |
| **route 命令过时** | 用 ip route |
| **DNS 改了不生效** | resolvectl flush-caches / 重启 systemd-resolved |
| **MTU 不一致丢包** | ping -s SIZE -M do 测 |
| **ARP 表满** | gc_thresh 三件套调大 |
| **TIME_WAIT 暴涨** | tcp_tw_reuse=1（绝不开 tcp_tw_recycle） |
| **抓包看不到包** | -i any / 关 RSS 多队列绑核 / 看 BPF 表达式 |
| **CIDR 算错** | 用 ipcalc 验证 |
| **curl 跳板没装 ca** | curl -k 测，但生产必修 ca |

## 十一、学习资源

```
书籍:
  - 《TCP/IP 详解 卷一》Stevens ⭐ 经典
  - 《计算机网络：自顶向下方法》Kurose
  - 《图解 HTTP》上野宣

在线:
  - High Performance Browser Networking (Ilya Grigorik) 免费
  - Beej's Guide to Network Programming
  - explainshell.com
  - submitlinks.io / DNS for Developers

实操:
  - GNS3 / EVE-NG     虚拟网络实验
  - Wireshark 抓包教程
  - tcpdump 实战

国内:
  - 极客时间《透视 HTTP 协议》罗剑锋
  - 极客时间《Linux 性能优化实战》倪朋飞
  - 小林 coding 网络专栏（公众号）
```

> 📖 **核心判断**：网络基础 = **OSI/TCP-IP + 三次握手/状态机 + 子网计算 + 抓包阅读 + Linux 网络命令**。能解释 TIME_WAIT / CLOSE_WAIT 区别、能算 /26 子网、能用 tcpdump 抓 SYN、能配 netplan 静态 IP，就是合格的基础。**别再用 ifconfig / netstat / route**，用 iproute2 (ip/ss)。
