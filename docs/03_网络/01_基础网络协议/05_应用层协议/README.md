# 应用层协议

## DNS

DNS 将域名解析为 IP 地址。

```bash
# 查询 DNS 记录
dig example.com
dig A example.com
dig MX example.com
nslookup example.com

# 查看 DNS 解析流程
dig +trace example.com
```

## HTTP/HTTPS

| 版本 | 特点 | 状态 |
|:---|:---|:---:|
| HTTP/1.1 | 文本协议，队头阻塞 | 逐步淘汰 |
| HTTP/2 | 二进制帧，多路复用 | 当前主流 |
| HTTP/3 | QUIC (UDP)，0-RTT | 逐步普及 |

## DHCP

DHCP 自动分配 IP 地址。

```
Client                  Server
   │                       │
   ├── DHCP Discover ────► │
   │ ◄── DHCP Offer ───── │
   ├── DHCP Request ─────► │
   │ ◄── DHCP ACK ─────── │
   │                       │
```

## NTP

NTP 同步服务器时间，对分布式系统至关重要。

```bash
# 查看 NTP 状态
timedatectl status
ntpq -p
chronyc sources -v

# 配置 NTP 服务器
# /etc/chrony/chrony.conf
server 0.cn.pool.ntp.org iburst
server 1.cn.pool.ntp.org iburst
```
