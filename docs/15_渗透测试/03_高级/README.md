# 高级

> 渗透测试高级 = **APT 模拟全链路 + 红队基础设施(C2 集群+Redirector+域前置/Cloudfront/Fastly) + EDR/XDR 对抗 + Living-off-the-Land(BYOVD/COM/WMI) + Active Directory 深度(ADCS/Trust 滥用/SCCM) + Cloud 渗透(AWS/Azure/GCP/阿里) + K8s 攻击(逃逸/RBAC 滥用/Sidecar 注入) + Service Mesh 攻击 + 容器/镜像/Helm 攻击 + DevOps 链攻击(GitLab/Jenkins/Argo) + 供应链攻击(SolarWinds/XZ 模式) + 物联网+OT/ICS + 0day 研究 + 漏洞挖掘(模糊测试/AFL/libFuzzer) + AI/LLM 红队 + 移动 + 硬件 + 物理 + 社工(钓鱼基础设施+Evilginx)**。本章面向红队 / APT 模拟 / 0day 研究员 / 漏挖工程师。

## 一、APT 模拟全链路

```
Recon (情报):
  OSINT (员工/技术栈/邮件/泄露)
  Shodan / Censys + 自动 Recon
  暴露面 (子域 / 端口 / 服务)
  社工 (LinkedIn / 脉脉 / 简历)

Initial Access:
  钓鱼邮件 (Office macro / HTA / LNK / OneNote / ISO)
  Web 0/1day (Log4j / Spring / Confluence)
  暴露 RDP / SSH
  VPN 漏洞 (Pulse / Citrix / Fortinet / Ivanti)
  供应链 (3CX / SolarWinds 模式)
  USB drop / Wi-Fi

Execution:
  PowerShell / cmd / wmic
  LOL Bins (rundll32 / regsvr32 / mshta)
  COM / WMI
  Scheduled Task
  
Persistence:
  Run key + Scheduled + Service
  WMI Event Subscription
  COM Hijacking
  AD Golden / Silver Ticket
  Skeleton Key

Privilege Escalation:
  本地内核
  Service / DLL Hijack
  Token Impersonation
  AD Kerberoasting / ADCS

Defense Evasion:
  syscall (绕 EDR userland hook)
  AMSI Bypass
  ETW Bypass
  BYOVD (自带漏洞驱动 → 关 EDR)
  签名伪造 (winsign / Sigthief)
  父进程伪造

Credential Access:
  Mimikatz / LaZagne
  DPAPI
  LSASS dump (procdump / nanodump)
  AD DCSync
  Vault / Cloud metadata

Discovery:
  AD BloodHound
  Cloud (ScoutSuite / Pacu)
  K8s (kubectl / Peirates)

Lateral Movement:
  PsExec / WMI / WinRM / SMB / DCOM
  Kerberos PtT
  SSH key 复用
  K8s ServiceAccount Token

Collection:
  数据库导出
  文件 (邮件 / 代码 / 文档)
  屏幕 / 键盘

Exfiltration:
  HTTPS / DNS / Cloud (S3 / OneDrive)
  Encrypt + Stage
  低速 + 多通道

Impact:
  数据销毁 (勒索)
  破坏可用性
  操纵
```

## 二、红队基础设施

```
C2 Server:
  Cobalt Strike Teamserver
  Sliver Server
  Mythic
  
Redirector (CDN / 反代):
  Nginx / Apache + 流量过滤
  Cloudflare / Fastly (CDN 域前置)
  AWS CloudFront
  Azure FrontDoor
  
DNS:
  域前置 (Domain Fronting, 渐减)
  自建 NS + DNS over HTTPS
  
Phishing:
  Gophish / King Phisher
  Evilginx2 ⭐ (会话窃取)
  Modlishka
  Muraena
  
分层:
  Stage 0: Dropper (Email / Web)
  Stage 1: Beacon (公开域 / CDN)
  Stage 2: Pivot Beacon (内网)
  Stage 3: 长期 (低速 + 备份)

OPSEC:
  - 隔离 (每客户独立)
  - 域 + IP 历史检查 (无威胁情报标记)
  - SSL 证书 (Let's Encrypt / 真实)
  - 流量伪装 (Malleable Profile / cloudflare 模仿)
  - 时区 + 工作时间 (匹配目标)
```

## 三、EDR / XDR 对抗

```
EDR 检测:
  - 进程链 (parent-child)
  - syscall hooks (userland)
  - ETW (内核事件)
  - AMSI (PowerShell / .NET)
  - 行为 (LSASS access / WMI / 注入)
  - YARA / Sigma 规则

绕过:
  - syscall 直接 (Hells Gate / Halo Gate / NTAPI)
  - PPID Spoof (PROC_THREAD_ATTRIBUTE_PARENT_PROCESS)
  - ETW Bypass (Patch ntdll EtwEventWrite)
  - AMSI Bypass (DllImport / 内存 patch)
  - Unhooking (重载 ntdll)
  - BYOVD (RTCore64 / EDRSandblast)
  - 进程注入新法 (EarlyBird / ImageLoad)
  - Sleep masking (Ekko / Phantom)
  
工具:
  RastaMouse OffSec course
  SharpHound
  EDRSandblast ⭐
  Donut / Freeze
  
EDR 列表 (国际):
  CrowdStrike Falcon
  Microsoft Defender for Endpoint
  SentinelOne
  Carbon Black
  Cortex XDR (Palo Alto)
  
EDR (国产):
  阿里云盾 ⭐
  奇安信 天擎
  360 天眼
  深信服 EDR
  亚信 / 安天 / 安博通
```

## 四、Living-off-the-Land (LOL)

```
Windows LOLBins (lolbas-project.github.io):
  certutil   下载文件
  bitsadmin  下载 + 调度
  mshta      执行 HTA
  rundll32   DLL 执行
  regsvr32   DLL 注册
  wmic       WMI
  powershell -enc
  msbuild    构建 = 任意代码
  installutil
  csc        编译
  
Linux LOLBins (GTFOBins.github.io):
  curl / wget
  python / perl
  awk / sed
  find -exec
  vim / less
  systemctl edit

技巧:
  - 不下载二进制
  - 用系统自带
  - 流量混入合法
  - Defender 默认信任
```

## 五、Active Directory 深度

### 5.1 ADCS (Active Directory Certificate Services)

```
Esc 漏洞 (Certipy):
  ESC1: 模板可指定 SAN
  ESC2: 模板 + Any Purpose
  ESC3: Enrollment Agent
  ESC4: 模板可写
  ESC6: EDITF_ATTRIBUTESUBJECTALTNAME2
  ESC7: CA ACL 弱
  ESC8: NTLM Relay 到 CA HTTP ⭐
  ESC9/10/11: Schannel / 限制

工具:
  Certipy ⭐
  certify (C#)
  
攻击链:
  PetitPotam → Coerce → NTLM Relay → ESC8 → 拿 DC 证书 → DC Sync
```

### 5.2 Trust 滥用

```
跨域:
  Forest Trust
  External Trust
  
攻击:
  Golden Ticket cross-forest
  Trust Key 滥用
  SID History 注入
  
工具:
  Rubeus + Mimikatz
  AD Module
```

### 5.3 SCCM

```
SCCM 暴露 → 部署任意 MSI 到全网
凭证: NAA (Network Access Account)
攻击: SharpSCCM / Misconfig Manager
```

### 5.4 LAPS / gMSA

```
LAPS Bypass:
  Read LAPS ACL 滥用
  gMSA Read 后用 gMSA Dumper

工具:
  pyldap / GetADUsers
  LAPSToolkit
  gMSADumper
```

## 六、Cloud 渗透

```
AWS:
  Pacu ⭐ (AWS 攻击框架)
  ScoutSuite (审计)
  CloudFox (Recon)
  
  常见:
  - SSRF → metadata → STS token
  - IAM 错配 (PassRole / iam:* / sts:AssumeRole)
  - S3 公开
  - Lambda 后门 + 持久化
  - Cognito 误配
  
Azure:
  ROADtools ⭐
  AADInternals
  MicroBurst
  
  常见:
  - Token 窃取
  - Conditional Access 绕过
  - Logic App 滥用
  - Storage 公开
  
GCP:
  GCPBucketBrute
  gcp_enum
  Hayat
  
  常见:
  - Service Account 滥用
  - GCS 公开
  - Cloud Function 后门
  
阿里云 / 腾讯云 / 华为云:
  - SLS / OSS 公开
  - RAM AssumeRole 滥用
  - ECS metadata SSRF
  - 元数据 IMDSv1 (类 AWS)
  - 工具: 阿里云盾 / 安全管家 检测
  
多云:
  Steampipe (查询多云)
  ScoutSuite + Prowler
  Wiz / Cyera (商业)
```

## 七、K8s 攻击

```
攻击面:
  - kubelet 10250 (未鉴权)
  - kubeconfig 泄露
  - SA Token (Pod 内 /var/run/secrets/kubernetes.io/serviceaccount/token)
  - etcd 未加密
  - Dashboard 暴露
  - Helm Tiller (老版)
  - Kubernetes Secret 明文
  - Pod 逃逸

Pod 逃逸:
  privileged: true → docker run 
  hostPID / hostNetwork / hostIPC
  hostPath mount → 宿主机
  capability SYS_ADMIN
  ServiceAccount admin → 提权
  CVE (Symlink / runc / containerd / CRI-O)
  
RBAC 滥用:
  可创建 Pod → 任意 SA → cluster-admin
  可 exec / port-forward → 直接进 Pod
  可改 Secret → 持久化
  可读 Secret → 拿凭证

工具:
  kube-hunter ⭐
  Peirates ⭐
  kdigger
  Kubectl-who-can / kubescape
  
Service Mesh 攻击:
  Sidecar 注入
  mTLS 配置错
  AuthorizationPolicy 绕过
  Envoy admin (15000)
```

## 八、容器 / 镜像 / Helm 攻击

```
镜像:
  - 后门镜像 (混入 base)
  - Latest tag 篡改
  - Registry 未鉴权 (push)
  - 镜像签名缺失
  - SBOM 缺失

Helm Chart:
  - 模板注入 (RCE)
  - hooks 滥用
  - 默认 Service Account admin

CRI / runtime:
  - containerd / runc CVE
  - dockerd.sock 暴露 → 宿主机
  
ImagePullSecret:
  - 凭证泄露 → registry takeover
  
工具:
  Trivy / Grype (扫)
  Dive (镜像层)
  Cosign (签名验证)
  Docker.sock 攻击脚本
```

## 九、DevOps 链攻击

```
GitLab:
  - Public repo 找 secret (gitleaks)
  - Runner 配置错 → 任意代码
  - CI variable 泄露
  - Webhook SSRF
  - CVE (历年多个)

Jenkins:
  - 公开实例 + 弱鉴权
  - Script Console (Groovy)
  - Pipeline 注入
  - Credential 解密

ArgoCD:
  - 公开 UI
  - 默认 admin 密码
  - Git repo 凭证
  - Sync 注入

Tekton / GitHub Actions:
  - secrets 泄露
  - injection (PR 来源)
  - self-hosted runner 滥用

Harbor / Nexus:
  - 公开 + 默认密码
  - Robot account 泄露
  
工具:
  gitleaks ⭐ + trufflehog (secret)
  GitDorker (公开 dorking)
  Stratus Red Team (Cloud DevOps)
```

## 十、供应链攻击

```
真实案例:
  SolarWinds (2020): Build server 后门 Orion
  Codecov (2021): Bash uploader 篡改
  ua-parser-js (2021): npm 包植入
  Log4Shell (2021): 上游漏洞 → 万企业
  3CX (2023): 多级供应链 (X_TRADER → 3CX)
  XZ Utils (2024): 上游 maintainer 植入后门 ⭐
  GitHub Actions tj-actions (2025): action 篡改

红队模拟:
  - 编辑器插件 (VSCode malicious)
  - npm / pip / Go 包注入
  - 镜像层注入
  - CI/CD 中间人
  - 假 maintainer (社工后接管)

防御:
  Sigstore + cosign
  SBOM + SLSA L3
  内网镜像源 + 锁定
  Renovate / Dependabot
  Reproducible builds
```

## 十一、AI / LLM 红队

```
攻击:
  Prompt Injection (直接 + 间接 RAG)
  Jailbreak (DAN / Crescendo / Multi-turn)
  Data Poisoning (训练 / RAG)
  Model Extraction (Stealing)
  Membership Inference
  Adversarial Examples
  Excessive Agency (Agent 越权)
  Tool Confused
  Multi-Agent 协作
  System Prompt Leak

工具:
  Garak ⭐ (LLM 漏扫, Nvidia)
  PyRIT ⭐ (Microsoft AI Red Team)
  llm-guard
  Promptfoo
  HouYi (LLM-Integrated 攻击)
  GPTFuzz
  AgentDojo (Agent benchmark)

红队流程:
  1. 模型识别 (探针)
  2. System Prompt 提取
  3. 越狱 + Prompt Injection
  4. RAG 投毒
  5. Tool / Agent 越权
  6. 数据泄露
  7. 报告

防御 (你的视角):
  Guardrails (LlamaGuard / NeMo)
  Output filter
  RLHF + 红蓝
  RAG 内容审核
  Agent 鉴权 (MCP)
  Token Exchange
```

## 十二、0day 研究 + 漏洞挖掘

```
模糊测试 (Fuzzing):
  AFL++ ⭐ (C/C++)
  libFuzzer (LLVM)
  Honggfuzz
  Boofuzz (协议)
  FuzzGen / Syzkaller (内核)
  WinAFL (Windows)
  
静态分析:
  CodeQL ⭐ (GitHub)
  Semgrep
  IDA Pro / Ghidra / Binary Ninja
  angr (符号执行)

动态:
  GDB + Pwndbg / GEF
  WinDbg
  Frida (Hook)
  
漏洞类型:
  Memory: Heap / Stack overflow / UAF / Type confusion
  Logic: Race / TOCTOU
  Web: Logic / Reflected / 反序列化
  
利用:
  ROP / JOP / SROP
  Heap exploit
  Kernel exploit
  Browser exploit (Chrome / Firefox)
  
练手:
  pwn.college
  pwnable.kr
  Phrack 杂志
  ROP Emporium
```

## 十三、IoT / OT / ICS

```
IoT:
  固件提取 (binwalk / firmware-mod-kit)
  二进制分析 (Ghidra / IDA)
  UART / JTAG (硬件接口)
  Bluetooth / Zigbee / LoRa
  
工具:
  attify-os
  firmwalker
  routersploit

OT / ICS:
  Modbus / DNP3 / IEC-104 / OPC-UA / S7 (西门子) / EtherNet/IP
  PLC / SCADA / HMI
  
工具:
  Wireshark + 协议插件
  ICSSPLOIT
  Metasploit SCADA module
  Conpot (蜜罐)

警示:
  OT 渗透极敏感, 误操作影响生产/人身
  必书面授权 + 演练环境
```

## 十四、社工 + 钓鱼基础设施

```
钓鱼框架:
  Gophish ⭐ (开源邮件)
  King Phisher
  Evilginx2 ⭐ (会话/2FA 窃取)
  Modlishka / Muraena
  zphisher
  SET (Social Engineering Toolkit)

钓鱼链:
  域名 (typo + IDN)
  邮件服务 (SPF/DKIM/DMARC 配真)
  Web (品牌克隆)
  载荷 (HTA / ISO / LNK / OneNote)
  Stealer (浏览器凭证 / cookies)
  
真实流程:
  1. OSINT 选目标
  2. 模板个性化
  3. 域名 + DNS + Mail 配齐
  4. EvilProxy → 拿 cookie → 绕 MFA
  5. Web 上线 → 横向

防御:
  反钓鱼演练 (季度)
  FIDO2 / Passkey (抗 EvilProxy)
  Email DMARC + 网关
  员工培训
```

## 十五、Checklist（高级）

```
APT 模拟:
☐ 全链 Recon → Impact
☐ 红队基础设施 (CS + Sliver + Redirector + CDN)
☐ OPSEC (隔离 + 伪装)

EDR 对抗:
☐ syscall + Unhook + AMSI Bypass
☐ ETW Bypass + Sleep masking
☐ BYOVD
☐ EDR 测评 (Falcon / 360 / 阿里)

LOL:
☐ Windows LOLBins
☐ Linux GTFOBins
☐ 不下载二进制

AD 深度:
☐ ADCS Esc1-8
☐ Trust 滥用
☐ SCCM
☐ LAPS / gMSA
☐ Certipy + Rubeus + Impacket

Cloud:
☐ Pacu / ROADtools / GCP 工具
☐ SSRF → metadata
☐ IAM 错配 + S3/OSS 公开
☐ Steampipe

K8s:
☐ kube-hunter + Peirates
☐ Pod 逃逸 (priv/hostPath/SYS_ADMIN)
☐ RBAC 滥用
☐ Service Mesh
☐ Helm + Image

DevOps:
☐ GitLab / Jenkins / Argo / Harbor
☐ CI/CD 注入
☐ Secret 泄露

供应链:
☐ npm/pip/Go 包 + 镜像层
☐ Maintainer 社工
☐ SBOM 缺失

AI 红队:
☐ Garak + PyRIT
☐ Prompt Injection (直/间接)
☐ Agent 越权
☐ OWASP LLM Top 10

0day:
☐ AFL++ / libFuzzer
☐ CodeQL / Semgrep
☐ ROP / Heap / Kernel

IoT/OT:
☐ binwalk / Ghidra
☐ Modbus/S7/DNP3
☐ 严格授权

社工:
☐ Evilginx2 / Gophish
☐ 域名 + DNS + Mail 真实
☐ FIDO2 反制
```

## 十六、推荐栈（高级）

```
APT 模拟:    CS + Sliver + Mythic + Redirector
红队基建:    Cloudflare/Fastly CDN + Let's Encrypt + Malleable C2
EDR 对抗:   Hells Gate + Donut + EDRSandblast + Ekko
AD 深度:     Certipy ⭐ + Rubeus + Impacket ⭐ + BloodHound + SharpHound
Cloud:       Pacu (AWS) + ROADtools (Azure) + GCP enum + Steampipe + Wiz
K8s:        kube-hunter ⭐ + Peirates + kubescape + Service Mesh exploit
DevOps:     gitleaks + trufflehog + Stratus Red Team + GitDorker
供应链:     模拟 + SBOM 反制
AI 红队:    Garak ⭐ + PyRIT + Promptfoo + llm-guard + HouYi
0day:       AFL++ ⭐ + libFuzzer + CodeQL + Ghidra + GDB
IoT:        binwalk + Ghidra + attify-os + UART/JTAG
OT:         Wireshark + ICSSPLOIT + Conpot
社工:        Evilginx2 ⭐ + Gophish + EvilProxy
报告:        PlexTrac + Markdown + Jinja2 + 内部规范
```

> 📖 **核心判断**：渗透测试高级 = **APT 模拟全链(MITRE ATT&CK) + 红队基建(C2+Redirector+CDN+Malleable+OPSEC) + EDR 对抗(syscall/BYOVD/Sleep/ETW) + LOL + AD 深度(ADCS/Trust/SCCM/LAPS) + Cloud 渗透(AWS/Azure/GCP/阿里) + K8s 攻击(逃逸/RBAC/Mesh/Helm) + DevOps 链 + 供应链(XZ/SolarWinds 模式) + AI/LLM 红队(Garak/PyRIT/Prompt Injection) + 0day 漏挖(AFL/libFuzzer/CodeQL) + IoT/OT/ICS + 社工(Evilginx2/EvilProxy)**。能独立完成"央企/大型互联网红队 APT 模拟 + Cloud + K8s + AI 红队 + 0day"完整链路，就具备红队工程师/APT 模拟专家能力。**永远授权先行。**
