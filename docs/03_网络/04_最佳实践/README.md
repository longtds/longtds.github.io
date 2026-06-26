# 最佳实践

> 网络最佳实践 = **网络架构设计原则 + 容量与安全基线 + 监控与排查 SOP + 变更纪律 + DDoS/WAF 防御 + VPN/远程接入 + 国产化选型 + 排查工具箱**。本章把"会配"升级到"会运营"，给可复制的工程化方案。

## 一、网络架构设计原则

### 1.1 经典层级（数据中心）

```
Internet → 边界路由 (BGP/Anycast)
       → DDoS 清洗（高防）
       → WAF / 入侵防御
       → 四层 LB (LVS/Cloud LB)
       → 七层 LB (Nginx/HAProxy/Envoy)
       → 后端服务 (K8s / VM)

水平拆分:
  - DMZ 区          公网入口
  - 应用区          业务服务器
  - 数据区          MySQL/Redis/ES
  - 管理区          堡垒机 / 监控 / CMDB
  - 备份区          独立 VLAN，单向访问
```

### 1.2 现代数据中心：Spine-Leaf

```
传统三层 (Core-Agg-Access): 南北向瓶颈
现代 Spine-Leaf (CLOS):
  - 任意 Leaf 之间最多 2 跳
  - 等价多路径 ECMP
  - 水平扩展线性
  - BGP unnumbered + IPv6 LL 邻居
  
适合: K8s 大集群 / AI 训练集群 / 云数据中心
```

### 1.3 高可用三件套

```
1. 链路冗余
   ☐ 服务器双网卡 Bond LACP
   ☐ 上联双交换机（M-LAG / VPC）
   ☐ 双电源 / 双 IDC

2. 设备冗余
   ☐ 双核心 VRRP
   ☐ LVS 双机 Keepalived
   ☐ 防火墙 HA pair

3. 路由冗余
   ☐ OSPF/BGP 等价多路径
   ☐ Anycast 多地宣告
   ☐ DNS 多 NS + GSLB
```

### 1.4 容量规划

```
红线指标:
  接口利用率   持续 > 60% 预警
  带宽峰值     > 70% 工单
  会话数       > 70% max 预警
  CPU (设备)   > 70% 工单
  内存 (设备)  > 80% 工单
  连接数 (LB)  > 70% 预警

预测:
  历史 P95 + 业务增长曲线 + 突发 buffer 30-50%

每季度复盘:
  - 流量趋势同比
  - 异常事件
  - 设备老化
  - 资源结余
```

## 二、安全基线

### 2.1 网络安全分层

```
1. 边界:    DDoS + WAF + IDS/IPS + 国密 VPN
2. 网络:    VLAN/微分段 + ACL + 入侵检测
3. 主机:    iptables/nftables + fail2ban + SELinux
4. 应用:    HTTPS + 认证授权 + 限流
5. 数据:    传输 TLS + 静态加密 + 备份加密
6. 运维:    堡垒机 + MFA + 审计
```

### 2.2 接入控制原则

```
默认拒绝 (default deny)
最小权限 (least privilege)
显式放行 (explicit allow)
按角色分段 (zero trust)
日志全留存 (≥ 6 月)
变更工单化
```

### 2.3 网络 ACL 模板（关键服务）

```
SSH (22):
  仅堡垒机 / 运维网段
  
MySQL (3306):
  仅应用服务器网段
  
Redis (6379):
  仅 K8s Pod CIDR
  
Kubelet (10250):
  仅 K8s 节点
  
监控 (9090, 9100, 9093):
  仅监控网段
  
管理 (Prometheus, Grafana, ArgoCD UI):
  堡垒机 + VPN
```

### 2.4 DDoS 防御层级

```
1. 接入层:
   - 云高防 / 运营商清洗
   - Anycast 分散
   - BGP RTBH (黑洞)

2. 边界:
   - SYN cookies + rate limit
   - syn proxy (LVS / 防火墙)
   - GeoIP / IP 信誉

3. 应用层:
   - WAF (CC 防护)
   - JS / 滑块验证
   - 行为分析

工具:
  阿里云高防 / 腾讯大禹
  Cloudflare
  长亭雷池（开源 WAF）
  Cilium Envoy 限流
```

### 2.5 WAF 选型

| 类型 | 代表 | 适用 |
|:---|:---|:---|
| **云 WAF** | 阿里云 / 腾讯云 / Cloudflare | 互联网业务 ⭐ |
| **本地 WAF** | F5 ASM / Imperva / 绿盟 | 金融/政企 |
| **开源** | **长亭雷池 SafeLine** ⭐ / ModSecurity / Coraza | 自部署首选 |
| **K8s-native** | Cilium L7 / Istio Envoy WAF | 云原生 |

## 三、监控与告警

### 3.1 网络监控分层

```
连通性 (探活):
  smokeping / blackbox_exporter
  外部第三方监测点（多地）

设备 (SNMP):
  net-snmp / Prometheus snmp_exporter
  - 接口流量 / 错包 / 丢包
  - CPU / 内存

主机 (node_exporter):
  - 接口 RX/TX
  - 队列 drops
  - TCP retrans / overflow

流量 (NetFlow / sFlow / IPFIX):
  - elastiflow
  - ntopng
  - 国产: DeepFlow ⭐

应用 (服务):
  - HTTP latency / status
  - DNS 解析时间
  - TLS 握手时间
```

### 3.2 关键告警规则（Prometheus）

```yaml
# 接口流量异常
- alert: InterfaceTrafficHigh
  expr: rate(node_network_receive_bytes_total[5m]) * 8 > 0.8 * 10e9   # 假设 10Gbps
  for: 10m
  labels: { severity: warning }

# 接口错包
- alert: InterfaceErrors
  expr: rate(node_network_receive_errs_total[5m]) > 1
  for: 5m

# TCP 重传率
- alert: TCPRetransRate
  expr: rate(node_netstat_Tcp_RetransSegs[5m]) / rate(node_netstat_Tcp_OutSegs[5m]) > 0.05
  for: 10m

# Listen Overflow
- alert: TCPListenOverflows
  expr: rate(node_netstat_TcpExt_ListenOverflows[5m]) > 0
  for: 5m

# Conntrack 满
- alert: ConntrackFull
  expr: node_nf_conntrack_entries / node_nf_conntrack_entries_limit > 0.9
  for: 5m
  labels: { severity: critical }

# 外部探活
- alert: ExternalProbeDown
  expr: probe_success == 0
  for: 2m
```

### 3.3 全球外部监测

```
免费/便宜:
  UptimeRobot
  Pingdom (商业)
  阿里云探针 / 腾讯云拨测

自建:
  blackbox_exporter 多地部署
  smokeping
  
GSLB / DNS 决策:
  阿里云 GTM / 腾讯云 GTM
  Cloudflare GeoSteering
  PowerDNS GeoIP / 自研
```

## 四、排查 SOP

### 4.1 用户报"网慢" 6 步法

```
1. 范围确认
   单点 / 多点 / 全量？
   时间段：持续 / 偶发？
   方向：上行 / 下行？

2. 端到端拆分
   客户端 ↔ 公网 ↔ 入口 LB ↔ Nginx ↔ 后端 ↔ DB
   每段 ping/curl/tcping，看延迟分布

3. 应用层
   curl -w "@curl-format.txt"
   关注 namelookup/connect/starttransfer/total

4. 协议层
   tcpdump 抓包看重传 / RST
   ss -tin 看 cwnd / rtt / retransmits

5. 接口层
   ip -s link / ethtool -S eth0
   看 errors / dropped / softirq

6. 全局
   监控大盘 / mtr 持续探测
```

### 4.2 curl 时延分解（必备模板）

```
# /etc/curl-format.txt
    time_namelookup:  %{time_namelookup}s
       time_connect:  %{time_connect}s
    time_appconnect:  %{time_appconnect}s
   time_pretransfer:  %{time_pretransfer}s
 time_starttransfer:  %{time_starttransfer}s
        time_total:  %{time_total}s

# 用
curl -w "@curl-format.txt" -o /dev/null -s https://api.example.com/

# 解读:
# namelookup 高    → DNS 慢
# connect 高       → 网络 RTT 慢
# appconnect 高    → TLS 握手慢
# starttransfer 高 → 服务端处理慢
```

### 4.3 抓包决策树

```
丢包?       tcpdump 看 retrans
RST?        看是哪端发的（应用 vs 协议栈）
握手失败?   看 SYN/SYN+ACK 是否到达
HTTP 502?   Nginx 看 upstream / 抓上游
TLS 失败?   openssl s_client + Wireshark TLS 解密
DNS?        dig +trace / tcpdump port 53
```

### 4.4 ss 关键字段（必背）

```bash
ss -tin                                    # TCP 详细
ss -tan state established | wc -l         # 看连接数
ss -tan state time-wait | wc -l           # TIME_WAIT
ss -tan state close-wait | wc -l          # CLOSE_WAIT (应用问题)
ss -lntp                                   # 监听 + 进程
ss -s                                      # 全局摘要

# 关注字段:
# cwnd        拥塞窗口
# ssthresh    慢启动阈值
# rtt:N/M     RTT/RTT 方差
# retrans:X/Y 当前/总重传
# bytes_acked/bytes_sent
```

## 五、变更管理

### 5.1 网络变更分级

```
小变更   防火墙单条 / 路由微调 / VLAN 加成员      on-call
中变更   LB upstream 增减 / DNS 切换 / 证书续期    审批
大变更   网络拓扑改造 / 跨 IDC 互联 / 设备升级    评审会 + 灰度
```

### 5.2 变更纪律

```
1. 工单先行（含回滚预案 + 影响评估）
2. 配置备份（show running / iptables-save）
3. 灰度（先单设备 → 半集群 → 全量）
4. 监控大盘 + 持续 mtr/ping
5. 变更窗口（业务低峰，避开大促）
6. 双人复核（核心设备）
7. 失败立刻回滚（先恢复，再查因）
```

### 5.3 配置变更模板

```bash
#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d-%H%M%S)

# 1. 备份
iptables-save > /backup/iptables.$TS.rules
ip route save > /backup/route.$TS.bin
nft list ruleset > /backup/nft.$TS.txt

# 2. 应用变更
iptables -A INPUT -p tcp --dport 8443 -j ACCEPT

# 3. 验证
ss -tln | grep 8443
curl -k https://localhost:8443/health

# 4. 持久化
iptables-save > /etc/iptables/rules.v4

# 5. 异常回滚
trap 'iptables-restore < /backup/iptables.$TS.rules' ERR
```

## 六、远程接入与 VPN

### 6.1 选型矩阵

| 方案 | 协议 | 性能 | 配置 | 适用 |
|:---|:---|:---|:---|:---|
| **WireGuard** ⭐ | UDP / 内核 | 极快 | 极简 | 现代首选 |
| OpenVPN | TCP/UDP / 用户态 | 一般 | 复杂 | 兼容老客户端 |
| IPsec | ESP / 内核 | 快 | 复杂 | 企业互联 |
| **L2TP/IPsec** | 旧 | 慢 | 中 | 兼容 Windows |
| **SoftEther** | 多协议 | 快 | 中 | 穿透强 |
| **国密 VPN** | GM IPsec/SSL | 中 | 复杂 | 党政信创 |

### 6.2 WireGuard 实战

```bash
# 安装
apt install wireguard

# 生成密钥
wg genkey | tee privatekey | wg pubkey > publickey

# 服务端 /etc/wireguard/wg0.conf
[Interface]
PrivateKey = <服务端私钥>
Address = 10.10.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = <客户端公钥>
AllowedIPs = 10.10.0.2/32

# 启用
wg-quick up wg0
systemctl enable wg-quick@wg0
wg show
```

### 6.3 零信任接入（ZTNA）

```
开源:
  Headscale (Tailscale 后端开源版) ⭐
  Tailscale / ZeroTier
  Cloudflare Zero Trust
  
商用国产:
  深信服 EasyConnect
  奇安信 网神
  腾讯 iOA
  阿里云 ZeroNetwork
```

### 6.4 堡垒机 + 网络分段

```
JumpServer 部署:
  - 用户 → JumpServer → 目标主机
  - 多因素 MFA
  - 会话录屏 + 审计
  - 工单审批 + 临时授权
  
网络上:
  - 堡垒机独立 VLAN
  - SSH 端口仅对堡垒机开放
  - 数据库端口仅对应用层开放
```

## 七、DNS 治理

### 7.1 内外网 DNS 拆分

```
公网 DNS:    权威 (Bind / PowerDNS / 阿里云解析) 
            + 多 NS / Anycast
            + DNSSEC / DoH

内网 DNS:    CoreDNS (K8s) + 自建递归 (Unbound)
            - 域名命名规范: <svc>.<env>.internal
            - 不要泄露内网域名到公网

防 DNS 劫持:
  - DNS over HTTPS (DoH) / DNS over TLS (DoT)
  - 应用层固定 IP (DNS 失败后兜底)
  - 内网用自建 DNS
```

### 7.2 CoreDNS（K8s 标配）

```yaml
# 自定义解析（连内网 DB）
data:
  custom.server: |
    db.internal:53 {
        forward . 10.0.0.53
    }

# 缓存调优
cache 300

# 上游
forward . 8.8.8.8 1.1.1.1 {
    prefer_udp
    health_check 10s
}

# 监控
prometheus :9153
```

### 7.3 DNS 监控

```yaml
# blackbox dns probe
modules:
  dns_a:
    prober: dns
    dns:
      query_name: example.com
      query_type: A
      validate_answer_rrs:
        fail_if_not_matches_regexp:
          - "1\\.2\\.3\\.4"
```

## 八、HTTPS / 证书生命周期

### 8.1 证书全栈管理

```
申请:
  Let's Encrypt + certbot (互联网)
  阿里云 SSL / 腾讯云 SSL (国内 ICP 备案场景)
  企业 CA (内网)
  国密证书 (CFCA / 沃通)

部署:
  Nginx / Envoy / HAProxy
  K8s: cert-manager ⭐
  
监控:
  blackbox SSL 探针 (剩余天数)
  Prometheus alert < 30 天

续期:
  自动: certbot.timer / cert-manager renewer
  手动: 大促前 1 个月提前续

吊销 (CRL/OCSP):
  ocspstapling on (Nginx)
```

### 8.2 cert-manager（K8s 必装）

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: letsencrypt-prod }
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef: { name: letsencrypt-prod }
    solvers:
      - http01:
          ingress: { class: nginx }

---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata: { name: api-tls }
spec:
  secretName: api-tls
  issuerRef: { name: letsencrypt-prod, kind: ClusterIssuer }
  dnsNames: [api.example.com]
```

## 九、混沌工程（网络）

### 9.1 工具

```
ChaosMesh   K8s 原生 ⭐
ChaosBlade  阿里
toxiproxy   代理注入
tc / netem  Linux 内核
pumba       Docker
```

### 9.2 tc/netem 经典用例

```bash
# 加 100ms 延迟
tc qdisc add dev eth0 root netem delay 100ms

# 加抖动 (50±10ms 正态)
tc qdisc add dev eth0 root netem delay 50ms 10ms distribution normal

# 加丢包 1%
tc qdisc change dev eth0 root netem loss 1%

# 加乱序
tc qdisc add dev eth0 root netem delay 10ms reorder 25% 50%

# 限流
tc qdisc add dev eth0 root tbf rate 100mbit burst 32kbit latency 400ms

# 清除
tc qdisc del dev eth0 root
```

### 9.3 ChaosMesh 网络故障注入

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata: { name: delay-chaos }
spec:
  action: delay
  mode: all
  selector: { namespaces: [default], labelSelectors: { app: api } }
  delay: { latency: "200ms", jitter: "50ms" }
  duration: "5m"
```

## 十、备份与灾备（网络维度）

### 10.1 配置备份

```
设备:
  - 每日 SNMP + Python (netmiko / nornir / NAPALM)
  - 入 Git，PR 审计
  
Linux:
  - iptables-save / nft list ruleset
  - ip route save
  - 入 Ansible / IaC repo

LB / 防火墙:
  - 每日 backup
  - 跨 IDC 异地存
```

### 10.2 容灾架构

```
单 IDC 内:
  - 设备双机 / 链路冗余

跨 IDC:
  - 双活: BGP Anycast / GSLB
  - 主备: VPN/IPsec + DNS 切换
  - 数据: 主从同步 / 同步复制

跨 Region (云):
  - 多 Region 部署
  - 全球加速 (CDN / Anycast)
```

### 10.3 演练

```
☐ 月度: 单设备故障切换
☐ 季度: 链路切换
☐ 半年: IDC 整体切换
☐ 年度: 跨地域灾备演练
```

## 十一、国产化选型

### 11.1 设备替代

| 场景 | 进口 | 国产替代 |
|:---|:---|:---|
| 核心交换 | Cisco Nexus / Arista | 华为 CE / 新华三 S12500 |
| 接入交换 | Cisco Catalyst | 锐捷 / 中兴 / 烽火 |
| 路由器 | Cisco ASR / Juniper MX | 华为 NE / H3C MSR |
| 防火墙 | Fortinet / PaloAlto | 启明 / 绿盟 / 奇安信 / 深信服 |
| 负载均衡 | F5 BIG-IP | 深信服 AD / 绿盟 LB / 国双 |
| WAF | Imperva / F5 ASM | 长亭雷池 ⭐ / 安恒 / 默安 |
| VPN | Cisco AnyConnect | 深信服 EasyConnect / 奇安信 |
| DDoS | Arbor / Radware | 阿里高防 / 腾讯大禹 / 绿盟 |
| 控制器 | Cisco DNA | 华为 iMaster NCE / 锐捷 |

### 11.2 CNI / SDN 国产

```
Kube-OVN     ⭐ 灵雀云开源，OVN-based
DeepFlow     ⭐ 云杉开源，eBPF 网络可观测
Antrea       VMware/中兴
华为 Yangtse  HCE 平台
腾讯 GalaxyKube  TKE
```

### 11.3 加密 / 合规

```
国密:
  TLS:  Tongsuo (铜锁) / GmSSL
  IPsec: 商密 IPsec
  
合规:
  等保 2.0 三级 (网络层)
  关键信息基础设施安全保护条例
  网络安全审查办法
```

## 十二、Toolbox（精选）

### 12.1 排查工具速查

| 工具 | 用途 |
|:---|:---|
| **ip / ss** ⭐ | iproute2 必备 |
| **mtr / traceroute** | 路径排查 |
| **tcpdump / Wireshark** ⭐ | 抓包 |
| **dig / drill / dog** | DNS |
| **curl / httpie / xh** | HTTP |
| **iperf3 / nuttcp** | 带宽 |
| **netperf / qperf** | 延迟 / RDMA |
| **wrk / hey / vegeta** | HTTP 压测 |
| **nmap / masscan / rustscan** | 端口扫 |
| **fortio** | gRPC/HTTP 压测 |
| **ngrep** | 文本抓包 |
| **bmon / nload / iftop** | 实时流量 |
| **conntrack** | 连接跟踪 |
| **ethtool** | 网卡详情 |
| **bpftrace** | 内核级追踪 ⭐ |
| **hubble** | Cilium 流量观测 |
| **DeepFlow CLI** | 国产可观测 |

### 12.2 平台工具

```
监控:        Prometheus + Grafana + 夜莺 ⭐
告警:        Alertmanager + 飞书机器人 / PagerDuty
日志:        Loki / ELK
NetFlow:    elastiflow / DeepFlow ⭐
APM:        SkyWalking / Pixie / Coroot
WAF:        长亭雷池 SafeLine ⭐
VPN:        WireGuard / Headscale
堡垒:        JumpServer ⭐
CDN:        阿里云 / 腾讯云 / Cloudflare
SDN:        OVS / OVN / Cilium
配置:        Ansible / nornir / NAPALM
```

## 十三、典型坑（最佳实践）

| 坑 | 建议 |
|:---|:---|
| **变更没回滚预案** | 配置先备份 + trap ERR |
| **大促前升级** | 严格变更冻结 |
| **DNS 单点** | 多 NS + Anycast + 多家解析商 |
| **证书过期没告警** | blackbox 监 < 30 天 |
| **iptables 规则手工** | 一律入 Ansible / IaC |
| **缺乏 baseline** | 季度跑 iperf + wrk 留档 |
| **WAF 误拦** | 灰度 + 白名单 + 监控 4xx 暴涨 |
| **DDoS 来了才买高防** | 提前接入 / 设置黑洞预案 |
| **VPN 单点** | 双节点 + 自动切换 |
| **国产化没提前测** | 上线前 ≥ 2 月联调 |
| **配置不入 Git** | 设备配 + iptables 全 Git |
| **告警噪音** | 月度治理 + 必须可操作 |

## 十四、最佳实践 Checklist

```
架构:
☐ Spine-Leaf 拓扑
☐ Bond LACP + M-LAG / VPC
☐ 多 IDC / 多 Region
☐ Anycast / GSLB

安全:
☐ 默认拒绝 + 显式放行
☐ VLAN/微分段
☐ WAF + DDoS 接入
☐ 堡垒机 + MFA
☐ 国密合规

监控:
☐ 接口 / 错包 / TCP retrans / conntrack
☐ 外部探活 (多地)
☐ blackbox + smokeping
☐ DeepFlow / Hubble

排查:
☐ curl-format 模板
☐ ss 关键字段熟练
☐ tcpdump 5 个常用过滤
☐ mtr 持续探测

变更:
☐ 工单 + 回滚预案
☐ 配置入 Git / Ansible
☐ 灰度 + 监控大盘
☐ 变更窗口

DR:
☐ 配置每日备份
☐ 证书 30 天告警
☐ 季度切换演练

国产化:
☐ 一类设备国产化方案
☐ 国密 / 等保
```

## 十五、学习路径

```
工程化（6 月）:
  1. SLI/SLO + 网络黄金信号
  2. blackbox + smokeping + 多地探活
  3. WAF / DDoS / 堡垒机 部署
  4. WireGuard + Headscale 零信任
  5. cert-manager + 证书全自动
  6. ChaosMesh / tc-netem 演练
  7. Ansible 网络配置 + Git PR
  8. 配置备份脚本 + 灾备演练

国产化（3 月）:
  9. 一类设备替代验证
  10. DeepFlow + Cilium + 雷池 SafeLine
  11. 等保 2.0 三级 (网络层) 自查

平台化（12 月+）:
  12. 自研网络运维平台
  13. 智能告警 / 根因分析（接 12_AIOps）
  14. 一键变更 + GitOps
```

> 📖 **核心判断**：网络最佳实践 = **架构冗余 + 安全基线 + 监控可观测 + 排查 SOP + 变更纪律 + 国产化储备**。能搭出 LVS+Keepalived+WAF+DDoS+堡垒机 完整入口、能用 Prometheus+DeepFlow 看清"哪段网络在拖慢"、能用 WireGuard+Headscale 替代传统 VPN、能在大促前跑通切换演练，就具备做"网络负责人"的能力。**变更纪律 + 灰度 + 监控 + Git 化** 是从工程师到 SRE 团队的分水岭。
