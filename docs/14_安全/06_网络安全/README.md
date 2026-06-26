# 网络安全（企业实战）

> 本章聚焦**企业网络安全实战**——防火墙、IDS/IPS、WAF、零信任、DDoS、流量分析。基础协议原理详见 `07_网络安全基础`。

## 一、企业网络安全分层

```
┌────────────────────────────────────────┐
│  互联网                                  │
└─────────────────┬──────────────────────┘
                  ↓
         DDoS 防护 + Anti-Bot
                  ↓
              CDN + WAF
                  ↓
            边界防火墙
                  ↓
              IDS / IPS
                  ↓
              负载均衡
                  ↓
         反向代理 / API 网关
                  ↓
         应用层（Web/API）
                  ↓
       内部 Service Mesh + mTLS
                  ↓
              数据库 / 中间件

每一层都要"独立可生效"，单点失守不能击穿整个体系
```

## 二、防火墙演进

### 2.1 防火墙世代

| 世代 | 类型 | 能力 |
|:---|:---|:---|
| 1 代 | 包过滤 | 五元组 |
| 2 代 | 状态检测 | 连接跟踪 |
| 3 代 | 应用层 | 协议识别 |
| 4 代 | **下一代防火墙 (NGFW)** | DPI + IPS + 应用控制 + Sandbox |
| 5 代 | **威胁智能 (TI-Firewall)** | 云查 + ATP + AI |

### 2.2 Linux 自带（iptables / nftables）

```bash
# iptables (老) → nftables (新, 推荐)
apt install nftables
systemctl enable --now nftables

# /etc/nftables.conf
flush ruleset

table inet filter {
  chain input {
    type filter hook input priority filter; policy drop;
    ct state established,related accept
    ct state invalid drop
    iif "lo" accept
    
    # ICMP 限速
    ip protocol icmp limit rate 5/second accept
    ip6 nexthdr icmpv6 limit rate 5/second accept
    
    # SSH 防爆破
    tcp dport 22 ct state new limit rate 3/minute accept
    
    # 业务
    tcp dport { 80, 443 } accept
    
    # 仅内网
    ip saddr 10.0.0.0/8 tcp dport { 3306, 5432, 6379 } accept
    
    # 日志 + 拒绝
    log prefix "drop-input: " level info limit rate 10/minute
    counter
  }
  chain forward {
    type filter hook forward priority filter; policy drop;
  }
  chain output {
    type filter hook output priority filter; policy accept;
  }
}

# NAT
table ip nat {
  chain prerouting  { type nat hook prerouting priority dstnat; }
  chain postrouting { type nat hook postrouting priority srcnat;
                      oifname "eth0" masquerade; }
}
```

### 2.3 商业 NGFW

| 厂商 | 国家 | 特点 |
|:---|:---|:---|
| **Palo Alto** | 美 | NGFW 行业标杆 |
| **Fortinet FortiGate** | 加 | 性价比高 |
| **Cisco ASA / Firepower** | 美 | 老牌 |
| **Check Point** | 以 | 高端 |
| **华为 USG** | 中 | 国产主流 |
| **深信服 NGAF** | 中 | 国产 |
| **山石** | 中 | 国产 |
| **奇安信 网神** | 中 | 国产 |

## 三、IDS / IPS

### 3.1 IDS vs IPS

```
IDS (Detection)    检测，不阻断
IPS (Prevention)   检测 + 实时阻断

部署位置:
  IDS: SPAN/TAP 镜像流量
  IPS: 串联在路径上（影响性能）
```

### 3.2 开源 IDS/IPS

| 工具 | 类型 | 特点 |
|:---|:---|:---|
| **Suricata** ⭐⭐⭐⭐⭐ | IDS+IPS | 现代多核，规则兼容 Snort |
| **Snort 3** | IDS+IPS | 老牌经典 |
| **Zeek (Bro)** | NSM | 行为分析 |
| **OSSEC** | HIDS | 主机层 |
| **Wazuh** | SIEM+HIDS | 全栈 |

### 3.3 Suricata 部署

```yaml
# /etc/suricata/suricata.yaml 关键
af-packet:
  - interface: eth0
    cluster-id: 99
    cluster-type: cluster_flow
    threads: auto

outputs:
  - eve-log:
      enabled: yes
      filename: eve.json
      types:
        - alert
        - http
        - dns
        - tls
        - files

rule-files:
  - /etc/suricata/rules/emerging-all.rules
  - /etc/suricata/rules/local.rules

# 跑 IPS 模式
af-packet:
  - interface: eth0
    copy-mode: ips
    copy-iface: eth1
```

```bash
# 装规则（Emerging Threats / ET Open）
suricata-update
systemctl restart suricata

# 日志
tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'

# 接 ELK / Loki / Splunk
```

### 3.4 自定义规则

```
# /etc/suricata/rules/local.rules
alert tcp any any -> $HOME_NET 22 (msg:"SSH brute force"; \
  flow:to_server; flags:S; \
  threshold: type both, track by_src, count 10, seconds 60; \
  sid:1000001; rev:1;)

alert http any any -> $HOME_NET any (msg:"SQL Injection"; \
  flow:to_server; \
  content:"union"; nocase; http_uri; \
  content:"select"; nocase; http_uri; \
  sid:1000002;)

alert tls any any -> $EXTERNAL_NET any (msg:"Outbound to TOR"; \
  tls.cert_subject; content:"CN=*.onion"; \
  sid:1000003;)
```

## 四、WAF（Web 应用防火墙）

### 4.1 WAF 防护能力

```
OWASP Top 10:
  ✅ SQL 注入
  ✅ XSS
  ✅ CSRF
  ✅ 路径穿越
  ✅ 命令注入
  ✅ XXE
  ✅ SSRF
  ✅ 反序列化
  ✅ 0day 虚拟补丁

+
  ✅ CC 攻击 / 慢速攻击
  ✅ 爬虫 / 撞库
  ✅ Bot 防护
  ✅ API 滥用
  ✅ 业务风控（薅羊毛）
```

### 4.2 开源 WAF

| 工具 | 类型 | 特点 |
|:---|:---|:---|
| **ModSecurity + OWASP CRS** ⭐⭐⭐⭐ | 老牌 | Nginx/Apache 集成 |
| **Coraza** | Go 重写 ModSec | 新生代 |
| **OpenResty + Lua** | 自定义 | 灵活 |
| **APISIX / Kong + 插件** | API Gateway | 一体化 |
| **雷池 SafeLine** ⭐⭐⭐⭐⭐ | 长亭开源 | 国产首选 |
| **NAXSI** | Nginx | 简单 |

### 4.3 雷池 SafeLine（国产推荐）

```bash
# 一键安装
bash -c "$(curl -fsSLk https://waf-ce.chaitin.cn/release/latest/setup.sh)"

# 特点:
#   ✅ 无规则，基于语义分析（不易绕过）
#   ✅ 中文 UI
#   ✅ 反向代理模式
#   ✅ 资源占用低
#   ✅ 攻击溯源 + IP 画像

# 访问 https://localhost:9443 配置
```

### 4.4 ModSecurity + CRS

```nginx
# Nginx ModSec
load_module modules/ngx_http_modsecurity_module.so;

http {
  modsecurity on;
  modsecurity_rules_file /etc/nginx/modsec/main.conf;
  
  server {
    listen 443 ssl;
    location / {
      modsecurity_rules '
        SecRuleEngine On
        SecRequestBodyAccess On
        Include /etc/nginx/modsec/crs/crs-setup.conf
        Include /etc/nginx/modsec/crs/rules/*.conf
      ';
      proxy_pass http://backend;
    }
  }
}
```

### 4.5 商业 WAF / CDN-WAF

```
CDN+WAF (国内):
  - 阿里云 WAF / CDN
  - 腾讯云 WAF / CDN
  - 华为云 WAF
  - 网宿 WAF

CDN+WAF (国际):
  - Cloudflare ⭐
  - AWS WAF + Shield
  - Akamai
  - Fastly
```

## 五、DDoS 防护

### 5.1 DDoS 攻击类型

```
L3/L4（流量型）:
  - SYN Flood
  - UDP Flood / DNS Amplification
  - ICMP Flood
  - NTP / Memcached 反射
  
L7（应用型）:
  - HTTP Flood (CC)
  - 慢速攻击（Slowloris）
  - 业务接口刷
  - 验证码刷
  - 大查询攻击

混合型: 多向量同时
```

### 5.2 防护层次

```
1. 基础设施层
   - 高防 IP / 高防 IDC
   - 阿里云盾 / 腾讯大禹 / Cloudflare Magic Transit
   
2. 网络层
   - SYN Cookies (sysctl net.ipv4.tcp_syncookies=1)
   - 黑洞路由
   - BGP Anycast
   - RTBH / Flowspec
   
3. 应用层
   - WAF + 限流
   - 验证码
   - 行为分析
   - 多级缓存（命中率高 → 真实请求少）
   - API 限流
```

### 5.3 内核 / 系统调优

```bash
# /etc/sysctl.d/99-ddos.conf
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 8192
net.core.somaxconn = 65535
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 2
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_max_tw_buckets = 262144
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535
net.netfilter.nf_conntrack_max = 2097152
net.netfilter.nf_conntrack_tcp_timeout_established = 600
sysctl --system
```

### 5.4 Nginx 限流

```nginx
http {
  # 按 IP 限速
  limit_req_zone $binary_remote_addr zone=perip:10m rate=100r/s;
  limit_conn_zone $binary_remote_addr zone=connperip:10m;
  
  # 按 host 限速
  limit_req_zone $host zone=perserver:10m rate=10000r/s;
  
  server {
    location /api/ {
      limit_req zone=perip burst=200 nodelay;
      limit_conn connperip 50;
      proxy_pass http://backend;
    }
    
    location /login {
      limit_req zone=perip burst=5 nodelay;
      # 强制验证码
    }
  }
}
```

### 5.5 fail2ban 防爆破

```ini
# /etc/fail2ban/jail.local
[nginx-cc]
enabled = true
filter = nginx-cc
action = iptables[name=NGINX, port=http, protocol=tcp]
logpath = /var/log/nginx/access.log
maxretry = 100
findtime = 60
bantime = 3600

# /etc/fail2ban/filter.d/nginx-cc.conf
[Definition]
failregex = ^<HOST> -.*"(GET|POST).*HTTP.*" (200|404).*$
```

## 六、零信任（Zero Trust）

### 6.1 核心理念

```
传统: 内网可信 / 外网不可信
零信任: 永远不信任，永远验证（Never trust, always verify）

三大原则:
  1. 显式验证（每次请求都验证身份）
  2. 最小权限（每次访问只给必要权限）
  3. 假设被攻破（默认敌对环境）

核心组件:
  - Identity（身份）
  - Device（设备）
  - Network（网络）
  - Application（应用）
  - Data（数据）

每个组件都要"持续验证 + 动态信任评估"
```

### 6.2 ZTNA 方案

| 工具 | 类型 |
|:---|:---|
| **Cloudflare Access** | SaaS, 接入网关 |
| **Tailscale** ⭐⭐⭐⭐⭐ | WireGuard + 控制面 |
| **NetBird** | 开源 Tailscale 替代 |
| **Headscale** | 自托管 Tailscale 控制面 |
| **Twingate** | SaaS |
| **Zscaler ZPA** | 商业 |
| **Google BeyondCorp** | Google 内部+商业 |
| **微软 Entra ID + ZTNA** | 商业 |
| **国内:** 飞连 / 阿里云 IDaaS | 商业 |

### 6.3 Tailscale / Headscale 实战

```bash
# Headscale（开源服务端）部署
docker run -d --name headscale \
  -v ./config:/etc/headscale \
  -p 8080:8080 \
  headscale/headscale:latest

# 创建 user + key
headscale users create alice
headscale --user alice preauthkeys create --expiration 24h

# 客户端接入
tailscale up --login-server https://your-headscale.com --authkey <KEY>

# ACL 规则
{
  "acls": [
    { "action": "accept",
      "src": ["group:dev"],
      "dst": ["tag:db:5432", "tag:redis:6379"] }
  ],
  "groups": {
    "group:dev": ["alice@", "bob@"],
    "group:sre": ["charlie@"]
  },
  "tagOwners": {
    "tag:db": ["group:sre"]
  }
}
```

### 6.4 应用层零信任（mTLS + SPIFFE）

```yaml
# SPIRE 工作负载身份
apiVersion: spire.spiffe.io/v1alpha1
kind: ClusterSPIFFEID
metadata: { name: app-id }
spec:
  spiffeIDTemplate: spiffe://example.com/ns/{{ .PodMeta.Namespace }}/sa/{{ .PodSpec.ServiceAccountName }}
  podSelector:
    matchLabels: { app: order-api }

# Istio mTLS + SPIFFE 集成
# 每个 Pod 自动获得 X.509 证书，验证身份
```

### 6.5 实施路线图

```
阶段 1 (3 月):
  - SSO + MFA 全员
  - 设备清单（CMDB）
  - 关键资产标识

阶段 2 (6 月):
  - VPN 替换为 ZTNA（Tailscale/Cloudflare Access）
  - 应用层 SSO 改造
  - 设备合规检查

阶段 3 (12 月):
  - mTLS（Service Mesh）
  - 微分段（Microsegmentation）
  - 持续验证

阶段 4 (持续):
  - 数据分类 + DLP
  - 行为分析
  - AI 风险评分
```

## 七、流量分析（NDR / NSM）

### 7.1 NSM (Network Security Monitoring)

```
全流量采集 → 行为分析 → 威胁狩猎

工具栈:
  ✅ Zeek (前 Bro)        协议解析 + 事件
  ✅ Suricata             IDS + 元数据
  ✅ Arkime (Moloch)      全包索引 + UI
  ✅ Stenographer         全包存储
  ✅ Snort 3              IDS
  ✅ ntopng               流量画像
  ✅ Wireshark            离线分析
```

### 7.2 典型部署

```
SPAN/TAP → 流量分析机 (Suricata + Zeek + Arkime) → ELK/Splunk

物理:  交换机 SPAN 镜像端口
虚拟:  vSwitch port mirror
云上:  AWS VPC Traffic Mirroring / 阿里云镜像
K8s:   eBPF (Cilium / Tetragon / Pixie)
```

### 7.3 Zeek 实战

```bash
# 安装
apt install zeek

# 启动
zeekctl deploy
zeekctl status

# 日志路径
/var/log/zeek/conn.log     # 连接
/var/log/zeek/dns.log      # DNS
/var/log/zeek/http.log     # HTTP
/var/log/zeek/ssl.log      # TLS

# 自定义脚本
event connection_established(c: connection) {
  if (c$id$resp_p == 4444/tcp)
    print fmt("Suspicious port: %s", c$id$orig_h);
}
```

### 7.4 Arkime（全包 PCAP 索引）

```bash
# 安装（内含 ES + Capture + Viewer）
wget https://arkime.com/downloads/arkime_*.deb
dpkg -i arkime_*.deb
/opt/arkime/bin/Configure
systemctl start arkimecapture arkimeviewer
# Web: https://server:8005

# 应用场景:
#   - 历史回溯（"3 天前 14:30 那个 IP 干了什么"）
#   - 取证证据
#   - 长期威胁狩猎
```

## 八、邮件安全

```
邮件攻击:
  - 钓鱼（Phishing）
  - 鱼叉（Spear Phishing）
  - BEC（商业邮件欺诈）
  - 恶意附件 / 链接

防护:
  ✅ SPF / DKIM / DMARC 配置
  ✅ Anti-Spam (SpamAssassin / Rspamd)
  ✅ 邮件网关（Proofpoint / Mimecast / 国内 安天 / 联软）
  ✅ Sandbox（附件检测）
  ✅ URL 重写（链接保护）
  ✅ 钓鱼演练（培训员工）

DNS 配置示例:
  SPF:   v=spf1 include:_spf.google.com ~all
  DKIM:  selector._domainkey.example.com  TXT  "v=DKIM1; k=rsa; p=..."
  DMARC: _dmarc.example.com  TXT  "v=DMARC1; p=reject; rua=mailto:dmarc@example.com"
```

## 九、DNS 安全

### 9.1 DNS 攻击

```
- DNS 劫持（中间人）
- DNS 投毒（缓存污染）
- DNS 隧道（C2）
- DGA（域名生成算法 → 难封禁）
- DDoS 反射
- DNS 泄漏（VPN 没生效）
```

### 9.2 DNS 防护

```
✅ DNSSEC                    签名防伪造
✅ DoT / DoH / DoQ           加密传输
✅ 递归 DNS 强化              dnsdist / Unbound
✅ 内部 DNS 隔离              不解析外部
✅ DNS Firewall              RPZ 阻断恶意域
✅ DNS 流量分析               异常 DGA / Tunnel 检测

工具:
  - Pi-hole（家用/小型）
  - Unbound + RPZ
  - dnsdist
  - 阿里云 公共 DNS / 安全
  - Cloudflare 1.1.1.1 + Family
```

```bash
# Unbound + RPZ 示例
# /etc/unbound/unbound.conf
server:
  interface: 0.0.0.0
  access-control: 10.0.0.0/8 allow
  hide-identity: yes
  hide-version: yes
  qname-minimisation: yes
  use-syslog: yes
  log-queries: yes
  
  # 黑名单
  local-zone: "evil.com" refuse

# DoT 上游
forward-zone:
  name: "."
  forward-tls-upstream: yes
  forward-addr: 1.1.1.1@853#cloudflare-dns.com
  forward-addr: 8.8.8.8@853#dns.google
```

## 十、VPN

### 10.1 VPN 选型

| 协议 | 性能 | 安全 | 跨平台 | 推荐 |
|:---|:---:|:---:|:---:|:---:|
| **WireGuard** ⭐⭐⭐⭐⭐ | 极快 | 强 | 全 | 首选 |
| **OpenVPN** | 中 | 强 | 全 | 老牌 |
| **IPsec / IKEv2** | 快 | 强 | 全 | 企业 |
| **L2TP** | 慢 | 弱 | 全 | 弃用 |
| **PPTP** | 快 | 极弱 | 全 | ❌ 弃用 |
| **OpenConnect (Cisco Anyconnect)** | 中 | 强 | 全 | 商业 |

### 10.2 WireGuard 实战

```bash
# 服务端
apt install wireguard
wg genkey | tee privatekey | wg pubkey > publickey

# /etc/wireguard/wg0.conf
[Interface]
PrivateKey = <server-private>
Address = 10.10.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = <client-public>
AllowedIPs = 10.10.0.2/32

# 启动
systemctl enable --now wg-quick@wg0
```

### 10.3 ZTNA 替代 VPN

```
2025 趋势: VPN → ZTNA
  
  传统 VPN:        全网穿透 → 横向移动风险
  ZTNA:           应用级隧道 → 仅授权应用
  
  推荐迁移路径:
    WireGuard / OpenVPN → Tailscale / Cloudflare Access / NetBird
```

## 十一、SIEM / SOC

### 11.1 工具栈

| 类型 | 商业 | 开源 |
|:---|:---|:---|
| **SIEM** | Splunk / QRadar / Sentinel / Elastic Security | Wazuh / OpenSearch + ElasticSearch / Graylog |
| **SOAR** | XSOAR (Palo Alto) / Splunk SOAR | Shuffle / TheHive |
| **EDR** | CrowdStrike / SentinelOne / Microsoft Defender | Velociraptor / OSQuery |
| **NDR** | Vectra / ExtraHop | Zeek + Suricata |
| **国产** | 长亭 / 奇安信 / 360 / 绿盟 | 雷池 / 自研 |

### 11.2 Wazuh 部署

```bash
# All-in-One
curl -sO https://packages.wazuh.com/4.7/wazuh-install.sh
sudo bash wazuh-install.sh -a

# 包含:
#   ✅ Wazuh Manager (HIDS + SIEM)
#   ✅ Wazuh Dashboard (Kibana)
#   ✅ Wazuh Indexer (OpenSearch)
#   ✅ Filebeat
#   ✅ Wazuh Agent (HIDS)

# Agent 部署到节点
wazuh-agent... connect to manager
```

### 11.3 SOC 建设

```
人:
  L1 监控          7x24 告警响应
  L2 分析师        事件深挖
  L3 高级分析      威胁狩猎 / 复盘
  
流程:
  - 接入 → 分类 → 处置 → 复盘
  - 与 IT 运维 / 业务对接
  - 司法对接（重大事件）

工具:
  SIEM + SOAR + EDR + NDR + TI + Sandbox
  
情报:
  - 商业 TI（VirusTotal / 微步 / 奇安信 / 安天）
  - 开源 TI（MISP / AbuseIPDB / AlienVault OTX）
  - 行业共享（CN-CERT / 金融业 ISAC）
```

## 十二、堡垒机 / 跳板机

```
作用:
  - 单点 SSH/RDP 入口
  - 集中身份认证
  - 操作录屏 + 命令审计
  - 高危命令拦截

主流:
  ✅ Jumpserver ⭐⭐⭐⭐⭐  国产开源首选
  ✅ Teleport            开源 + 商业
  ✅ Ansible Tower / AWX
  ✅ 极盾 / 行云管家      国产商业
  ✅ CyberArk            高端商业

部署 Jumpserver:
  curl -sSL https://github.com/jumpserver/jumpserver/releases/latest/download/quick_start.sh | bash
  
  特性:
    - SSH/RDP/SFTP/Telnet/数据库 全协议
    - 4A（认证/账号/授权/审计）
    - 命令过滤
    - 工单审批
    - 录屏回放
    - MFA
```

## 十三、典型坑（生产血泪）

| 坑 | 建议 |
|:---|:---|
| **边界 = 安全** | 零信任 |
| **VPN 全网穿透** | ZTNA 应用级 |
| **裸暴露 22 端口** | 跳板机 + 改端口 + fail2ban |
| **WAF 误判全关** | 调白名单不要全关 |
| **DDoS 来了再买高防** | 平时演练 + 预案 |
| **NDR 看不懂日志** | 接 SIEM + AI |
| **Suricata 规则不更新** | 自动 |
| **DNS 用 8.8.8.8** | 内部 DNS + DoT |
| **邮件无 DMARC** | 必配 |
| **HIDS 全员裸奔** | Wazuh / EDR 必装 |
| **应急没演练** | 季度 |
| **管理网混业务网** | 独立 VLAN |
| **远程办公无 ZTNA** | 必上 |
| **零信任只买产品** | 文化 + 流程 + 工具 |

## 十四、最佳实践 Checklist

```
边界:
☐ NGFW + IDS/IPS
☐ DDoS 高防（云上）
☐ WAF（雷池/CRS）
☐ DNS 防护（DoT/RPZ）
☐ 邮件网关 + SPF/DKIM/DMARC

内网:
☐ 微分段（VLAN/NetworkPolicy）
☐ 零信任接入（ZTNA）
☐ Service Mesh mTLS
☐ 堡垒机 + MFA

主机:
☐ HIDS（Wazuh）
☐ EDR
☐ 漏扫周期
☐ 补丁管理

监测:
☐ Suricata + Zeek
☐ Arkime 全包索引
☐ SIEM 集中
☐ 异常告警
☐ 威胁情报订阅

应急:
☐ SOC 7x24
☐ IR 剧本
☐ 演练（季度）
☐ 司法对接
☐ 异地灾备
```

## 十五、推荐栈（2025）

### 15.1 小团队

```
边界:        Cloudflare（DDoS+WAF+CDN+Access）
内网:        Tailscale / Headscale
主机:        Wazuh
检测:        Suricata + Zeek
堡垒机:      Jumpserver
邮件:        Gmail/腾讯邮箱 + DMARC
```

### 15.2 中大企业

```
边界:        NGFW（Palo Alto/Fortinet/华为）
DDoS:        阿里云盾 / Cloudflare Magic
WAF:         雷池 / 阿里云 WAF / Imperva
内网:        ZTNA (Cloudflare/Tailscale) + 微分段
SIEM:        Splunk / Wazuh / 长亭
EDR:         CrowdStrike / SentinelOne / 奇安信天擎
NDR:         Suricata + Zeek + Arkime + Vectra
DNS:         内部 Unbound + RPZ + Cloudflare Gateway
邮件:        Proofpoint / Mimecast / 联软
SOC:        7x24 + SOAR + TI
堡垒机:      Jumpserver / CyberArk
```

## 十六、学习路径

```
入门（2 周）:
  1. nftables / iptables 基础
  2. Nginx + ModSecurity / 雷池
  3. fail2ban
  4. SSH 加固

中级（1 个月）:
  5. Suricata + Zeek 部署
  6. Wazuh SIEM
  7. WireGuard / Tailscale
  8. DNS 安全 (Unbound + RPZ)

高级（3 个月）:
  9. 零信任落地
  10. NDR + Arkime
  11. SIEM 规则编写
  12. SOC 运营
  13. 红蓝对抗

专家:
  14. 自研检测规则
  15. AI 威胁分析
  16. 跨国安全治理
```

## 十七、参考资料

```
书:
  - 《Network Security Through Data Analysis》
  - 《Practical Packet Analysis》(Chris Sanders)
  - 《Zero Trust Networks》(O'Reilly)
  - 《Applied Network Security Monitoring》

标准:
  - NIST SP 800-207 (Zero Trust)
  - MITRE ATT&CK
  - PCI-DSS Network Section
  - 等保 2.0

工具:
  - Suricata: https://suricata.io/
  - Zeek: https://zeek.org/
  - Wazuh: https://wazuh.com/
  - Tailscale: https://tailscale.com/
  - SafeLine 雷池: https://waf-ce.chaitin.cn/
  - Jumpserver: https://www.jumpserver.com/

社区:
  - SANS Internet Storm Center
  - r/netsec
  - 国内: FreeBuf / 安全客 / 看雪
```

> 📖 **核心判断**：2025 网络安全 = **边界（CDN+WAF+DDoS）+ 内网（ZTNA+微分段+mTLS）+ 主机（EDR+HIDS）+ 监测（SIEM+NDR+TI）+ 应急（SOC+IR+演练）**。最大变革是**从边界防御走向零信任**——VPN 替换 ZTNA、内网 mTLS、设备合规检查、持续验证。中文私有化首选 **雷池 + Wazuh + Jumpserver + Tailscale/Headscale + Suricata + 阿里云盾**。
