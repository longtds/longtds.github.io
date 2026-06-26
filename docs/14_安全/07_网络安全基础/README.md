# 网络安全基础

> 本章是**底层网络安全原理**（OSI、TCP/IP、防火墙原理、攻防基础）。企业实战详见 `04_网络安全`。

## 一、OSI 七层模型与安全

```
7. Application       HTTP/FTP/SSH         | XSS, SQL注入, CSRF, 业务漏洞
6. Presentation      TLS/SSL              | 弱加密, 协议降级
5. Session           Session/Cookies      | 会话劫持, Session Fixation
4. Transport         TCP/UDP              | SYN Flood, Port Scan
3. Network           IP/ICMP/路由         | IP 欺骗, ICMP 滥用, 路由劫持
2. Data Link         MAC/Switch/ARP       | ARP 欺骗, MAC Flooding, VLAN 跳跃
1. Physical          电缆/光纤/无线        | 物理接入, 窃听, 干扰

每层都有独立攻击面，需要分层防御
```

## 二、TCP/IP 协议安全

### 2.1 IP 层威胁

```
IP Spoofing（IP 欺骗）:
  - 伪造源 IP 发包
  - 绕过基于 IP 的认证
  - DDoS 反射放大
  防御: uRPF / 入口过滤 (BCP 38)

ICMP 滥用:
  - Ping Flood
  - Smurf Attack（ICMP 广播放大）
  - ICMP Tunnel（数据外泄）
  防御: rate-limit, 不响应 broadcast

碎片攻击:
  - Teardrop（旧）
  - 巨型 ping
  防御: 防火墙重组检测
```

### 2.2 TCP 层威胁

```
SYN Flood:
  半开连接耗尽资源
  防御: SYN Cookies (sysctl)
        SYN Proxy（防火墙代理）
        BGP Anycast

TCP Reset 攻击:
  伪造 RST 包断开连接
  防御: TCP MD5 (BGP)
        TCP-AO (RFC 5925)

TCP 会话劫持:
  猜测 seq 号注入
  防御: 随机化 ISN（初始序列号）

端口扫描:
  - SYN scan (-sS)
  - Connect scan (-sT)
  - Stealth scan (-sN/-sF/-sX)
  - UDP scan (-sU)
  防御: IDS / Firewall / Honeypot
```

### 2.3 UDP 层威胁

```
UDP Flood:
  无连接，资源消耗
  
反射放大 (DDoS 放大器):
  - DNS Amplification    （28-54x）
  - NTP Monlist            （556x）
  - SSDP                  （30x）
  - Memcached            （5万x！）
  - LDAP                  （46x）
  
防御:
  ✅ 关闭递归 (DNS)
  ✅ 限制 monlist (NTP)
  ✅ 不暴露 memcached 公网
  ✅ ingress filtering (BCP 38)
```

## 三、链路层威胁

### 3.1 ARP 欺骗

```
原理:
  攻击者发 ARP 响应"网关 MAC 是我"
  → 流量经过攻击者（MITM）
  
检测:
  arp -a | sort -k2          # 多个 IP → 同 MAC = 可疑
  arpwatch / arpalert

防御:
  ✅ 静态 ARP（重要主机）
  ✅ DHCP Snooping + DAI (Dynamic ARP Inspection)
  ✅ 802.1X 端口认证
```

### 3.2 MAC Flooding

```
原理:
  发大量假 MAC → 交换机 CAM 表满 → 退化为 Hub（广播）→ 嗅探

防御:
  ✅ Port Security（限制端口 MAC 数）
  ✅ 802.1X
```

### 3.3 VLAN 跳跃

```
攻击:
  Double Tagging      双 VLAN tag 绕过
  Switch Spoofing     伪装 trunk

防御:
  ✅ 禁用 trunk 自动协商
  ✅ Native VLAN 设独立 ID
  ✅ 不用的端口设 access + shutdown
```

### 3.4 STP 攻击

```
攻击者发 BPDU 声称自己是根桥 → 流量重新路由
防御: BPDU Guard / Root Guard
```

## 四、加密协议层（TLS）

### 4.1 TLS 演进

| 版本 | 年份 | 状态 |
|:---|:---|:---|
| SSL 2.0 | 1995 | ❌ 严重漏洞 |
| SSL 3.0 | 1996 | ❌ POODLE |
| TLS 1.0 | 1999 | ❌ BEAST，弃用 |
| TLS 1.1 | 2006 | ❌ 弃用 |
| TLS 1.2 | 2008 | ⚠️ 仍可用 |
| **TLS 1.3** | 2018 | ✅ **推荐** |

### 4.2 TLS 握手

```
TLS 1.2 (5 步, 2 RTT):
  Client Hello (cipher, random)
  Server Hello + Cert + KeyExchange
  Client Key Exchange + Change Cipher
  Finished
  
TLS 1.3 (3 步, 1 RTT):
  Client Hello + KeyShare
  Server Hello + Cert + Finished
  Client Finished
  
+ 0-RTT (Resumption)
+ 强制 PFS (Perfect Forward Secrecy)
+ 移除弱算法
```

### 4.3 已知 TLS 漏洞

```
2014 Heartbleed       OpenSSL CVE-2014-0160  内存泄漏
2014 POODLE           SSL 3.0
2015 FREAK            导出级 RSA
2015 Logjam            512-bit DH
2016 DROWN            SSLv2
2016 SWEET32          3DES/Blowfish
2018 ROBOT            RSA padding oracle
2020 Raccoon          DH 时序

→ 全部源于"弱算法 + 旧协议"
```

### 4.4 现代 TLS 配置

```nginx
# Nginx 现代配置（Mozilla SSL Configurator）
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 1.1.1.1 8.8.8.8 valid=60s;

# HSTS
add_header Strict-Transport-Security "max-age=63072000" always;

# DH
ssl_dhparam /etc/nginx/dhparam.pem;     # 2048+ bit
```

### 4.5 TLS 健康检查

```bash
# 测试工具
testssl.sh https://example.com
sslscan example.com
nmap --script ssl-enum-ciphers -p 443 example.com

# 在线
https://www.ssllabs.com/ssltest/

# 目标: A+ 评级
```

## 五、防火墙原理

### 5.1 包过滤防火墙

```
五元组规则:
  源 IP / 源端口 / 目标 IP / 目标端口 / 协议
  
特点:
  ✅ 简单 / 快
  ❌ 无状态（每个包独立判断）
  ❌ 不识别应用
  
代表: 早期 iptables / ACL
```

### 5.2 状态检测防火墙（Stateful）

```
跟踪连接状态:
  NEW           新连接
  ESTABLISHED   已建立
  RELATED       相关（FTP 数据通道）
  INVALID       无效

优势:
  - 出方向自动允许返回包
  - 防 spoof（基于状态）
  
代表: iptables -m state, conntrack
```

### 5.3 应用层防火墙（NGFW）

```
深度包检测 (DPI):
  - 识别 HTTP/FTP/SSH 等应用
  - 看 URL / 内容
  - 解 SSL（中间人证书）
  - 与 IPS 一体

代表: Palo Alto, Fortinet, 华为 USG
```

### 5.4 Web 应用防火墙（WAF）

```
专门防 Web 攻击:
  - SQL 注入
  - XSS
  - CSRF
  - 命令注入
  
模式:
  - 反向代理（最常见）
  - Bridge（透明）
  - Plugin（Nginx 模块）

代表: ModSecurity, 雷池, 阿里云 WAF
```

## 六、IDS / IPS 原理

```
IDS (Intrusion Detection System):
  被动监听，只告警

IPS (Intrusion Prevention System):
  串接路径，实时阻断

检测模型:
  签名检测     已知攻击 pattern
  异常检测     行为偏离基线
  状态分析     协议状态机
  
开源: Suricata / Snort / Zeek
商业: Cisco Firepower / Palo Alto / 山石

部署:
  - SPAN/TAP 镜像（IDS）
  - Inline 串接（IPS）
```

## 七、网络扫描与侦察

### 7.1 Nmap（攻击者第一工具）

```bash
# 主机发现
nmap -sn 192.168.1.0/24                 # Ping scan
nmap -PR 192.168.1.0/24                 # ARP scan（局域网）

# 端口扫描
nmap -sS target                         # SYN scan（隐蔽）
nmap -sT target                         # TCP Connect
nmap -sU target                         # UDP
nmap -sV target                         # 版本探测
nmap -A target                          # 全套（OS + version + script）
nmap -O target                          # OS fingerprint

# 脚本扫描
nmap --script vuln target
nmap --script smb-vuln-* target
nmap --script "default,safe" target

# 速率控制
nmap -T0 target     # Paranoid（极慢，避检测）
nmap -T4 target     # Aggressive
nmap -T5 target     # Insane

# 隐蔽技巧
nmap -f target                          # 分片
nmap -D RND:10 target                  # 假源 IP
nmap -S spoof_ip target                # 伪造源
nmap -e eth0 target                    # 指定接口
nmap --proxies socks4://proxy target   # 代理
```

### 7.2 防扫描

```
✅ IDS 检测 + 告警
✅ 防火墙限速（每秒新建连接数）
✅ Honeypot（蜜罐误导）
✅ 关闭无用端口
✅ Banner Grabbing 屏蔽
✅ TCP/IP fingerprint 混淆（pfSense）
```

## 八、协议安全（DNS / HTTP）

### 8.1 DNS 安全

```
威胁:
  - DNS 欺骗 / 投毒
  - DNS 隧道（C2）
  - DGA 域名（动态生成，难封）
  - DNS 放大
  - Subdomain Takeover

防御:
  ✅ DNSSEC          签名验证（防伪造）
  ✅ DoT / DoH / DoQ  加密传输（防嗅探/篡改）
  ✅ DNS Firewall (RPZ)
  ✅ Split DNS（内外分离）
  ✅ 监控异常 DNS 流量
```

### 8.2 HTTP 安全头

```
# 基础安全头（生产必加）
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Resource-Policy: same-origin
```

### 8.3 Cookie 安全

```
Set-Cookie: sessionid=...; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=3600

HttpOnly      JS 不可读（防 XSS 偷 Cookie）
Secure         仅 HTTPS 传输
SameSite      防 CSRF
  - Strict   同站才发
  - Lax      默认，部分跨站允许
  - None     完全跨站（必配 Secure）
```

## 九、Wireshark / tcpdump 抓包

### 9.1 tcpdump

```bash
# 基础
tcpdump -i eth0
tcpdump -i any -nn

# 过滤
tcpdump -i eth0 'host 192.168.1.1'
tcpdump -i eth0 'port 80'
tcpdump -i eth0 'tcp port 443 and host 1.2.3.4'
tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn|tcp-fin) != 0'
tcpdump -i eth0 'icmp[icmptype] = icmp-echo'

# 保存
tcpdump -i eth0 -w trace.pcap -G 60 -W 10    # 每 60s 一文件，循环 10 个

# 读取
tcpdump -r trace.pcap
tcpdump -r trace.pcap -A 'port 80'           # 看 HTTP 内容

# 抓 sni（看用户访问的 HTTPS 域名）
tcpdump -i eth0 -nn -A 'tcp port 443 and tcp[((tcp[12:1] & 0xf0) >> 2):4] = 0x16030100'
```

### 9.2 Wireshark 过滤器

```
# 显示过滤（capture 后过滤）
ip.addr == 192.168.1.1
tcp.port == 443
http.request.method == "POST"
tls.handshake.type == 1                  # Client Hello
dns.flags.response == 0                  # DNS 请求
tcp.flags.syn == 1 and tcp.flags.ack == 0  # SYN

# 关键技巧
- Follow TCP Stream / Follow HTTP Stream
- Statistics > Conversations
- IO Graph
- Expert Information
- 导出 HTTP 对象 (File > Export Objects > HTTP)
```

## 十、加密基础

### 10.1 对称加密

```
AES-256-GCM        ⭐ 推荐
ChaCha20-Poly1305   ⭐ 移动端
AES-256-CBC         需配 HMAC
3DES                ❌ 弃用
RC4                 ❌ 弃用
DES                 ❌ 弃用

模式:
  GCM  AEAD（加密 + 认证），首选
  CBC  需配 HMAC，PKCS7 padding
  CTR  并行
  ECB  ❌ 永远不要用
```

### 10.2 非对称加密

```
RSA            ≥ 2048-bit, 推荐 4096
ECDSA          P-256 / P-384, 椭圆曲线
Ed25519         ⭐ 推荐（小、快、安全）
DH / ECDH       密钥交换（PFS）
X25519          ⭐ 推荐密钥交换

后量子（PQC）:
  - Kyber       NIST 标准化
  - Dilithium   签名
  → 2025-2030 渐进迁移
```

### 10.3 哈希函数

```
✅ SHA-256 / SHA-384 / SHA-512
✅ SHA-3 系列
✅ BLAKE3 (快)

❌ MD5  (碰撞)
❌ SHA-1 (碰撞)
⚠️ HMAC-MD5 / HMAC-SHA1 (可用但不建议)

密码哈希专用:
  ✅ Argon2id       ⭐ 当前最佳
  ✅ bcrypt          老牌
  ✅ scrypt          内存硬
  ❌ PBKDF2          仅在合规要求时
  ❌ MD5/SHA 直接哈希密码（永远不要）
```

### 10.4 国密算法

```
SM2     椭圆曲线（替代 ECDSA）
SM3     哈希（替代 SHA-256）
SM4     分组对称（替代 AES）
SM9     标识密码（替代 IBE）

应用:
  - 等保 2.0 + 密评
  - 金融 / 政务 / 关键基础设施
  - 国密 TLS（GMSSL）

工具:
  - openssl + gmssl patch
  - 国密 HSM（江南天安 / 三未信安）
```

## 十一、PKI 基础

### 11.1 X.509 证书

```
内容:
  - Subject (CN, O, C)
  - Issuer
  - Public Key
  - Validity (notBefore, notAfter)
  - Extensions (SAN, KeyUsage, EKU)
  - Signature (CA 签)

链:
  Root CA → Intermediate CA → Server Cert

信任:
  - 系统 / 浏览器内置 Root CA
  - 内网自签：分发 Root CA 到所有客户端
```

### 11.2 证书工具

```bash
# 看证书
openssl x509 -in cert.pem -text -noout
openssl s_client -connect example.com:443 -showcerts < /dev/null

# 验证证书链
openssl verify -CAfile chain.pem cert.pem

# 自签 CA
openssl genrsa -out ca.key 4096
openssl req -x509 -new -key ca.key -out ca.crt -days 3650 -subj "/CN=My CA"

# 签发服务器证书
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=server.local"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 365 -sha256 \
  -extfile <(printf "subjectAltName=DNS:server.local,IP:10.0.0.1")
```

### 11.3 Let's Encrypt + ACME

```bash
# certbot 自动签发
certbot certonly --nginx -d example.com -d www.example.com
certbot renew --dry-run

# acme.sh（轻量）
acme.sh --issue -d example.com --webroot /var/www
acme.sh --install-cert -d example.com \
  --key-file /etc/nginx/ssl/key.pem \
  --fullchain-file /etc/nginx/ssl/fullchain.pem \
  --reloadcmd "systemctl reload nginx"

# 通配符（DNS-01）
acme.sh --issue --dns dns_ali -d '*.example.com' -d example.com
```

## 十二、常见攻击手法分类

### 12.1 OWASP Top 10 (2021)

```
A01 Broken Access Control
A02 Cryptographic Failures
A03 Injection (SQL/Command/LDAP)
A04 Insecure Design
A05 Security Misconfiguration
A06 Vulnerable Components
A07 Identification & Auth Failures
A08 Software & Data Integrity Failures
A09 Security Logging & Monitoring Failures
A10 SSRF
```

### 12.2 MITRE ATT&CK 战术阶段

```
1. Reconnaissance      侦察
2. Resource Development 资源准备
3. Initial Access      初始访问
4. Execution            执行
5. Persistence         持久化
6. Privilege Escalation 提权
7. Defense Evasion     防御规避
8. Credential Access   凭证窃取
9. Discovery            发现
10. Lateral Movement   横向移动
11. Collection         数据收集
12. Command & Control  C2 控制
13. Exfiltration       数据外泄
14. Impact              破坏

→ 攻击者全流程地图，蓝队按 phase 检测
```

### 12.3 Kill Chain（Lockheed Martin）

```
Recon → Weaponize → Deliver → Exploit → Install → C2 → Action

早阶段断链 = 阻止后续 = 低成本防御
```

## 十三、网络取证基础

### 13.1 取证证据类型

```
1. 易失性最高 → 最易丢失
   CPU 寄存器 / Cache
   内存 (RAM)
   路由表 / ARP 表 / 进程
   临时文件
   磁盘
   远程日志
   备份
```

### 13.2 取证步骤

```
1. 识别（什么遭攻击）
2. 保留（不修改证据）
3. 收集（按易失性顺序）
4. 分析
5. 报告
6. 司法移交

工具:
  - dd / dc3dd / FTK Imager (磁盘镜像)
  - LiME / AVML (内存)
  - Wireshark / Arkime (网络)
  - Volatility (内存分析)
  - Sleuthkit / Autopsy (磁盘分析)
  - plaso / log2timeline (时间线)
```

## 十四、学习路径

```
入门（1 月）:
  1. OSI / TCP/IP 完整理解
  2. Wireshark 抓包熟练
  3. nmap 基础扫描
  4. iptables/nftables 配置
  5. TLS 配置 + ssllabs A+

中级（3 月）:
  6. Suricata IDS + Zeek
  7. Wireshark 高级（流追踪 / Lua 插件）
  8. OWASP Top 10 实战（DVWA / WebGoat）
  9. 加密算法 + PKI
  10. 攻击重现（VulnHub）

高级（6 月+）:
  11. MITRE ATT&CK 全战术
  12. 红蓝对抗（HTB / TryHackMe）
  13. 流量取证 + 内存取证
  14. CTF（XCTF / DEFCON）
  15. CISSP / OSCP 认证

专家:
  16. 红队全流程
  17. APT 分析
  18. 0day 研究 / 漏洞挖掘
```

## 十五、推荐学习资源

```
书:
  - 《图解 TCP/IP》
  - 《TCP/IP Illustrated》(Stevens)
  - 《Network Security Essentials》(Stallings)
  - 《Applied Cryptography》(Schneier)
  - 《Black Hat Python》
  - 《The Web Application Hacker's Handbook》

证书:
  - CISSP   宏观体系
  - CISP    国内等保 / 行业
  - CompTIA Security+    入门
  - OSCP   渗透实操
  - GCIH/GREM/GCFE    SANS 体系

实战:
  - HackTheBox          渗透靶场
  - TryHackMe           入门靶场
  - VulnHub             VM 靶机
  - PortSwigger Web Academy  Web 安全
  - DVWA / WebGoat / Juice Shop  Web 漏洞
  - root-me.org         挑战
  - 国内: XCTF / 攻防世界 / 看雪
  
社区:
  - r/netsec / r/AskNetsec
  - SANS Internet Storm Center
  - Krebs on Security
  - 国内: FreeBuf / 安全客 / 看雪 / 先知
  - 长亭 / 奇安信 / 360 安全应急中心
```

## 十六、参考

```
- RFC 4949 Internet Security Glossary
- NIST SP 800-53 Security Controls
- NIST SP 800-115 Penetration Testing
- ISO 27001 信息安全管理
- MITRE ATT&CK: https://attack.mitre.org/
- OWASP: https://owasp.org/
- 等保 2.0 / GB/T 22239
```

> 📖 **核心判断**：网络安全基础 = **协议原理（TCP/IP/TLS）+ 攻击手法分类（OWASP/ATT&CK）+ 工具熟练（nmap/wireshark/tcpdump）+ 加密 PKI**。一切上层安全工具都建立在这些底层之上——不懂 TCP 状态机，看不懂 SYN Flood；不懂 TLS 握手，配不好 Nginx；不懂 PKI，搞不定零信任。**先打牢底层，再追工具**。
