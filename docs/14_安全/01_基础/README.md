# 基础

> 安全基础 = **CIA + 威胁模型 STRIDE + 主机加固 + 网络 ACL + OWASP Top 10 + 密码学 + 证书 + 镜像扫描 + 审计 + 备份 + 等保2.0 入门**。本章面向初次接触安全的运维/开发。

## 一、核心理念

```
CIA: Confidentiality 机密 / Integrity 完整 / Availability 可用
AAA: Authentication 认证 / Authorization 授权 / Accounting 审计

威胁建模 STRIDE:
  S Spoofing            假冒
  T Tampering           篡改
  R Repudiation         抵赖
  I Information Disclosure 泄露
  D Denial of Service   拒绝服务
  E Elevation of Privilege 提权

OWASP Top 10 (2021):
  A01 失效访问控制       (最频)
  A02 加密失败
  A03 注入 (SQL/XSS/Cmd)
  A04 不安全设计
  A05 安全错配 (默认密码 / 暴露端口)
  A06 过时组件
  A07 鉴别失败
  A08 完整性失败 (SSC/CICD)
  A09 日志监控不足
  A10 SSRF
```

## 二、主机加固

### 2.1 SSH 加固

```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no       # 强制 key
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers ops
Protocol 2
X11Forwarding no
```

### 2.2 用户/sudo

```bash
useradd -m ops
echo "ops ALL=(ALL) NOPASSWD: /usr/bin/systemctl" > /etc/sudoers.d/ops
chmod 440 /etc/sudoers.d/ops
passwd -l root                   # 锁 root
chage -M 90 ops                  # 90 天改密码
```

### 2.3 防火墙

```bash
# firewalld (RHEL)
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --permanent --remove-service=cockpit
firewall-cmd --reload

# nftables (Debian 现代)
nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input tcp dport {22,443} accept

# ufw (Ubuntu)
ufw default deny incoming
ufw allow 22/tcp
ufw allow 443/tcp
ufw enable
```

### 2.4 内核加固 (sysctl)

```ini
# /etc/sysctl.d/99-security.conf
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.log_martians = 1
kernel.randomize_va_space = 2        # ASLR
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.suid_dumpable = 0
```

### 2.5 SELinux / AppArmor

```bash
setenforce 1                          # SELinux 强制
ausearch -m AVC -ts recent            # 看 SELinux 拒绝

aa-status                             # AppArmor 状态
aa-enforce /etc/apparmor.d/profile    # 强制 profile
```

### 2.6 auditd 审计

```bash
yum install audit
systemctl enable --now auditd

# 规则
auditctl -w /etc/passwd -p wa -k passwd_changes
auditctl -w /etc/shadow -p wa -k shadow_changes
auditctl -w /etc/sudoers -p wa -k sudoers_changes
auditctl -w /var/log/secure -p wa -k secure_log
auditctl -a always,exit -F arch=b64 -S execve -k exec
```

## 三、网络安全

```
基础:
  最小开放 (默认 DROP)
  限来源 IP (内网 / VPN)
  禁高危端口 (Redis 6379 / MongoDB 27017 公网)
  
DDoS 基础:
  - syn_cookies
  - 限速 (iptables hashlimit / nginx limit_req)
  - 上游清洗 (云厂商)
  
IDS/IPS:
  Snort / Suricata ⭐
  Wazuh (开源 HIDS)
  Falco (容器运行时)
  
VPN:
  WireGuard ⭐ (现代轻量)
  OpenVPN (老牌)
  IPsec (站点对站点)
  Tailscale (零配置)
```

## 四、漏洞与 CVE

```
CVE = Common Vulnerabilities and Exposures
CVSS = Common Vulnerability Scoring System (0-10 评分)
  Critical 9.0-10
  High     7.0-8.9
  Medium   4.0-6.9
  Low      0.1-3.9

漏洞库:
  NVD (NIST)
  CVE Mitre
  CNNVD / CNVD (国内)
  GitHub Advisory
  
扫描工具 (主机):
  OpenVAS ⭐
  Nessus (商业)
  Nuclei ⭐ (现代)
  
扫描 (镜像):
  Trivy ⭐ + Grype + Clair
  Snyk / 阿里云镜像扫描
  
扫描 (代码):
  SonarQube ⭐
  Semgrep ⭐
  CodeQL (GitHub)
```

## 五、密码学基础

```
对称加密:
  AES-256-GCM ⭐ (推荐)
  ChaCha20-Poly1305 (移动端)
  ❌ DES / 3DES (淘汰)
  ❌ AES-CBC (无认证)
  国密: SM4

非对称:
  RSA-2048+ / RSA-3072
  ECDSA (P-256/P-384)
  Ed25519 ⭐ (现代)
  国密: SM2

哈希:
  SHA-256 / SHA-384 / SHA-512 ⭐
  SHA-3 / BLAKE2 / BLAKE3
  国密: SM3
  ❌ MD5 / SHA-1 (淘汰)

密码哈希:
  Argon2id ⭐ (推荐)
  bcrypt (经典)
  scrypt
  ❌ 纯 SHA-256 (无盐 / 快)

HMAC: 消息完整性 + 来源
PBKDF2: 弱密钥派生
```

## 六、证书与 PKI

```
X.509 证书:
  Issuer / Subject / Public Key / Signature / Validity
  扩展 (SAN / EKU / KU)

PKI 三角:
  CA (Certificate Authority)
  RA (Registration Authority)
  CRL / OCSP (撤销)

工具:
  openssl ⭐
  cfssl
  cert-manager (K8s)
  Let's Encrypt (公网 ACME)
  step-ca (内网 CA)
  CFCA (国密)

最佳:
  TLS 1.3 only
  HSTS + Preload
  证书 90d 短期 + 自动续签
  ECDSA P-256 (轻 + 快)
  禁 SSLv2/v3 + TLS 1.0/1.1
```

## 七、Web 安全 (OWASP)

```
SQL 注入:
  防: 参数化查询 + ORM + 输入校验
  
XSS:
  防: 输出转义 + CSP + HttpOnly Cookie

CSRF:
  防: SameSite Cookie + CSRF Token

SSRF:
  防: 白名单 + 禁内网 + 元数据 IP 拦截

文件上传:
  防: 白名单 + 重命名 + 隔离存储

弱密码:
  防: Argon2 + 密码策略 + MFA

未授权访问:
  防: 默认拒绝 + 鉴权中间件 + 测试覆盖

CSP (Content Security Policy):
  Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-xxx'

HTTP 安全头:
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=()
```

## 八、容器/镜像安全

```bash
# Trivy 扫描
trivy image nginx:1.27
trivy image --severity CRITICAL,HIGH --exit-code 1 myapp:latest

# Grype
grype docker.io/nginx:1.27

# Dockerfile 基线
FROM gcr.io/distroless/static:nonroot   # 最小基础
USER 65532:65532                          # 非 root
COPY --chown=65532:65532 app /app
ENTRYPOINT ["/app"]

# 禁:
  - latest 标签
  - root 运行
  - ADD URL (用 COPY)
  - 大基础镜像 (用 distroless / alpine)
```

## 九、日志审计

```
必采:
☐ Linux audit (auditd) → SIEM
☐ SSH login (/var/log/secure)
☐ sudo (/var/log/secure)
☐ 应用 access / error
☐ 数据库 慢查询 + 审计
☐ K8s audit (apiserver)
☐ Web Nginx + waf
☐ Firewall drops

SIEM:
  Wazuh ⭐ (开源)
  Elastic Security
  Splunk (商业)
  阿里云 SLS / 华为 LTS

保留:
  等保 2 级: 6 个月
  等保 3 级: 6 个月 + 不可篡改
  
告警:
  失败登录 5次/10min → 告警
  sudo to root → 告警
  /etc/passwd 修改 → 告警
  外联可疑 IP → 告警
```

## 十、备份与恢复

```
3-2-1 原则:
  3 份副本
  2 种介质
  1 份异地

工具:
  Restic ⭐ (现代 + 加密 + 去重)
  Borg ⭐
  rsync + cron (基础)
  Velero (K8s)
  
加密:
  备份必加密 (AES-256)
  密钥分离 (Vault / KMS)
  
验证:
  季度恢复演练
  RPO / RTO 度量
```

## 十一、等保 2.0 入门

```
等级保护 (中国强制, 2019 起):
  1 级: 用户自主保护
  2 级: 系统审计保护 (一般业务)
  3 级: 安全标记保护 (重要系统) ⭐
  4 级: 结构化保护 (核心系统)
  5 级: 访问验证 (军事)

10 大方面:
  1. 安全物理环境
  2. 安全通信网络
  3. 安全区域边界
  4. 安全计算环境
  5. 安全管理中心
  6. 安全管理制度
  7. 安全管理机构
  8. 安全管理人员
  9. 安全建设管理
  10. 安全运维管理

测评:
  每年一次
  公安部认证机构
  整改 + 备案
```

## 十二、必会工具清单

```
扫描:        Trivy / Grype / Nuclei / OpenVAS
WAF:        ModSecurity / OpenResty + waf 模块 / 阿里云 WAF
IDS:        Suricata / Snort / Wazuh
HIDS:        Wazuh ⭐ / OSSEC
EDR:        阿里云盾 / 360 / 奇安信
SIEM:        Wazuh + Elastic / 阿里 SLS
合规:        OpenSCAP + CIS Benchmarks
密码学:     OpenSSL / cfssl / Tongsuo
PKI:        cert-manager + Let's Encrypt / step-ca
VPN:        WireGuard + Tailscale
密码管理:   Vault / Bitwarden
```

## 十三、入门 20 题

```
1.  CIA 三性
2.  STRIDE 6 项
3.  OWASP Top 10 (2021)
4.  SSH 加固关键 5 项
5.  sysctl 加固关键 5 项
6.  SELinux / AppArmor 区别
7.  auditd 关键规则
8.  CVE / CVSS 评分
9.  对称 vs 非对称
10. SHA-256 vs MD5 (为何弃)
11. Argon2 vs bcrypt
12. TLS 1.3 与 1.2 区别
13. SQL 注入防御
14. XSS 防御 (输出转义 + CSP)
15. CSRF 防御 (SameSite)
16. Trivy 镜像扫描
17. K8s audit 三级 (None/Metadata/Request/RequestResponse)
18. 等保 2.0 等级
19. 3-2-1 备份
20. CIS Benchmark 用途
```

## 十四、推荐栈

```
主机:        SSH 加固 + sysctl + SELinux + auditd
WAF:        ModSecurity / 阿里 WAF
IDS/HIDS:   Wazuh ⭐ + Suricata
扫描:        Trivy ⭐ + OpenVAS + Nuclei
SIEM:        Wazuh + Elastic / 阿里 SLS
密码学:     OpenSSL + Tongsuo (国密)
PKI:        cert-manager + Let's Encrypt
VPN:        WireGuard + Tailscale
备份:        Restic + 异地 S3/OSS
合规:        等保 2 级 + OpenSCAP + CIS
```

> 📖 **核心判断**：安全基础 = **CIA + STRIDE + OWASP Top 10 + 主机加固(SSH/sysctl/SELinux/audit) + 网络 ACL + Trivy 镜像扫描 + TLS 1.3 + Argon2 + Wazuh SIEM + 等保 2 级 + 3-2-1 备份**。掌握这 10 条线，就具备运维安全入门能力。
