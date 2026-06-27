# 最佳实践

> 渗透测试最佳实践 = **法律合同 + 范围规则(ROE) + 方法论(PTES/OSSTMM/OWASP/PCI) + 工具链 + Recon → Exploit → Post → 报告 + Bug Bounty + 红蓝紫 + Purple Team 落地 + KPI + 团队组织 + 国产渗透合规 + HW 行动 + Postmortem**。本章把"会用 Burp + nmap"升级到"运营企业级红队 / 渗透服务 / SRC"。

## 一、12 项金标准

```
1. ✅ 书面授权 + 范围 + 时间 + 联系人 + 升级路径 (法律先行)
2. ✅ ROE (Rules of Engagement) 明确范围 / 禁区 / 通报
3. ✅ 方法论 (PTES / OSSTMM / OWASP Testing Guide / PCI)
4. ✅ 工具链标准化 (Kali / Burp Pro / nuclei / Sliver / 自研)
5. ✅ Recon 资产管理 (持续 + 自动)
6. ✅ 漏洞分级 (CVSS + 业务) + 修复优先级
7. ✅ 报告标准 (摘要 + 详情 + 修复 + 证据 + CWE/CVE)
8. ✅ 数据保护 (隔离环境 + 加密 + 30d 销毁)
9. ✅ 红蓝紫协同 (红 + 蓝 + 复盘 + 改进)
10. ✅ HW 行动 + 国家级演练 (中国)
11. ✅ Bug Bounty + SRC 内部
12. ✅ KPI (覆盖率 / 漏洞数 / 闭环率 / 重测通过)
```

## 二、法律 + 授权流程

```
SOW (Statement of Work):
  ☐ 范围 (IP / 域名 / 应用 / 资产)
  ☐ 不可触及 (生产数据 / 高敏)
  ☐ 时间窗 (工作时间 / 24x7)
  ☐ 联系人 (技术 + 管理)
  ☐ 升级路径 (0day / 关键发现)
  ☐ 数据保护 (加密 + 销毁)
  ☐ 报告交付 (格式 + 时间)
  ☐ 费用 + 付款
  ☐ 保密 (NDA)
  ☐ 责任界定 (生产中断)

法律依据 (中国):
  ☐ 网安法 27 条
  ☐ 数据安全法
  ☐ 个保法
  ☐ 关基条例
  ☐ 网络安全审查办法

合规:
  ☐ 服务商资质 (CISP-PTE / CISP)
  ☐ 实施人员背景调查
  ☐ 项目档案保存 (3-5 年)
```

## 三、ROE (Rules of Engagement)

```
明确:
☐ 目标列表
☐ 不可碰 (生产 DB / 关基资产 / 客户数据)
☐ 时间窗
☐ 攻击强度 (Low / Medium / High)
☐ 漏洞利用是否允许 (PoC 还是 Exploit)
☐ 社工是否允许 (员工钓鱼)
☐ 物理是否允许 (现场)
☐ 持久化 / 后门 是否允许
☐ DDoS / 暴力破解 强度
☐ 客户数据接触 (脱敏后销毁)
☐ 通报机制 (高危 1h 内)
☐ 紧急停止口令

签字:
  甲方安全负责人 + 乙方项目经理
```

## 四、方法论选择

```
PTES (Penetration Testing Execution Standard):
  通用 + 红队风格
  7 阶段 (Pre-engagement → Reporting)
  
OSSTMM (Open Source Security Testing Methodology Manual):
  科学量化 + RAVs 评分
  人员 / 物理 / 无线 / 数据 / 通信
  
OWASP Testing Guide:
  Web / API 专用
  
PCI-DSS:
  支付行业 + 年度强制
  
NIST 800-115:
  美国政府
  
中国:
  GB/T 等保 + 关基测评
  CISP-PTE 体系
```

## 五、工具链标准化

```
基础 OS:
  Kali Linux / Parrot Security
  自定义 ISO (持久化 + 工具集)

信息收集:
  amass + subfinder + assetfinder + dnsx + httpx
  nmap + masscan + naabu
  Shodan + Censys
  BBOT (自动)

Web:
  Burp Pro ⭐
  ZAP (二选一)
  nuclei + nuclei-templates
  sqlmap + XSStrike
  ffuf + dirsearch
  jwt_tool + Autorize

漏洞利用:
  Metasploit Pro / Free
  Sliver / Cobalt Strike
  msfvenom
  searchsploit + ExploitDB

密码:
  hashcat + john
  hydra + CrackMapExec
  Responder + Mimikatz
  Impacket + Rubeus

AD:
  BloodHound + SharpHound
  Certipy + Impacket + Rubeus
  PowerView + ADRecon

Cloud:
  Pacu + ScoutSuite (AWS)
  ROADtools + AADInternals (Azure)
  GCP enum (GCP)
  Steampipe + Wiz

K8s:
  kube-hunter + Peirates + kubescape

报告:
  Markdown + Pandoc → PDF
  PlexTrac / Dradis (商业)
  自研 Jinja2 模板

协作:
  Notion / Obsidian
  ZeroTier / Tailscale (远程)
  专网 (高敏项目)
```

## 六、Recon 资产管理

```
持续 Recon:
  ☐ Cron 每周扫子域 + 端口
  ☐ 新资产入库 → 自动漏扫 nuclei
  ☐ 历史对比 (新增 / 变化)
  ☐ 风险评分

工具:
  reNgine / Faraday / DefectDojo
  自建 PostgreSQL + Grafana
  Watchtowr (商业 CTEM)
  
SRC 内部:
  暴露面平台 ⭐ (内部 ASM)
  风险评分 + 闭环
  漏洞修复看板
```

## 七、漏洞分级 + 修复

```
CVSS 评分:
  Critical 9.0-10
  High     7.0-8.9
  Medium   4.0-6.9
  Low      0.1-3.9
  Info     0

业务调整:
  生产 + 暴露 + 数据敏感 = 提级
  内网 + 边缘 = 降级
  
修复 SLA:
  Critical: 24h
  High:     7d
  Medium:   30d
  Low:      90d

闭环:
  发现 → 录入 → 分配 → 修复 → 重测 → 关闭
  
工具:
  DefectDojo ⭐
  Faraday
  自建 Jira workflow
```

## 八、报告标准

```
结构:
  封面 + 概要 (1 页)
  目录
  执行摘要 (1-2 页, 给管理)
  范围 + 方法 + 工具
  关键发现 (TOP 5-10 漏洞 + 图)
  漏洞详情 (每个 1-3 页)
    - 标题 + 风险等级
    - CVSS + CWE + OWASP / ATT&CK
    - 受影响范围
    - 重现步骤 (截图)
    - 影响
    - 修复建议 (具体到代码 / 配置)
    - 参考
  整体评估 + 风险矩阵
  改进建议
  附录: 工具输出 + 完整资产

质量:
  ☐ 每漏洞有截图 + payload + curl 命令
  ☐ 风险描述清晰 (不是 "可能危险")
  ☐ 修复建议可操作 (不是 "应升级")
  ☐ 中英文版 (出海)
  ☐ PDF 加密 + 水印
  ☐ 30d 后销毁
```

## 九、Bug Bounty + SRC

```
内部 SRC:
  ☐ 平台 (开源: kbcms / nbms; 商业: 补天 / 漏洞盒子)
  ☐ 范围 + 规则 + 奖励
  ☐ 三方测试人员管理
  ☐ 重复漏洞机制
  ☐ 季度回顾 + 改进

外部:
  HackerOne ⭐ / Bugcrowd / Synack / Intigriti
  中国: 补天 / 漏洞盒子 / Security Response Center
  
工具:
  HackerOne CLI
  自动 Triage (AI + 规则)
  
关键 KPI:
  收到漏洞数
  Triage SLA < 24h
  修复 SLA
  误报率
  奖励发放 < 30d
  重复率 < 30%
```

## 十、红蓝紫协同

```
红队 (Offense):
  季度 + 年度
  内部 + 外部第三方
  全链 APT 模拟

蓝队 (Defense):
  SOC + EDR + SIEM
  Threat Hunting
  Velociraptor 取证

紫队 (Purple) ⭐:
  红蓝同会 ATT&CK 演练
  红队 TTP → 蓝队检测规则 → Sigma → SIEM
  
工具:
  Caldera ⭐ (ATT&CK 自动)
  Atomic Red Team ⭐ (小测试)
  Vectr (跟踪)
  ATT&CK Navigator
  
KPI:
  ATT&CK Technique 覆盖 > 70%
  检测率 > 70%
  MTTD < 1h
  改进项 季度闭环
```

## 十一、HW 行动（中国实战）

```
背景:
  HW = 实战化攻防演练
  公安部 / 网信办主导
  关基单位强制
  年度 2-4 周
  
角色:
  攻击方: 国家队 / 外部红队
  防守方: 单位安全团队
  指挥部: 公安 + 监管 + 客户
  
准备:
  T-3 月: 资产梳理 + 暴露面收敛
  T-1 月: 重保模式 + 7x24 监控
  T-1 周: 应急演练 + 全员到位
  T-1 日: 战时机房 + 通讯 + 物资
  
进行:
  实时监控 + IP 封禁
  威胁情报共享
  应急响应 + 取证
  通报 + 复盘
  
得分项:
  关键事件 (拿权 / 数据)
  暴露面发现
  防御 (检测 / 阻断)
  
教训:
  - 资产梳理早做
  - 0day 防御 (Patch + WAF + 蜜罐)
  - SOC 7x24 + 国家威胁情报
  - 演练 ≥ 季度
  - 应急 SOP 熟练
```

## 十二、KPI + 度量

```
红队:
☐ ATT&CK Technique 覆盖 > 70%
☐ 季度演练 100%
☐ 检测率 > 70%
☐ 红队达 OBJ (拿权 / 数据) 时间
☐ 检出 / 误报比

渗透服务:
☐ Critical/High 漏洞数 / 项目
☐ 修复 SLA 达标率
☐ 重测通过率 > 95%
☐ 客户满意度 NPS > 60
☐ 报告质量评分

SRC / Bug Bounty:
☐ 收到漏洞数 / 月
☐ Triage SLA < 24h
☐ Critical 修复 < 7d
☐ 误报率 < 20%
☐ 奖励发放 < 30d

HW 行动:
☐ 暴露面收敛率 100%
☐ 0 重大失分
☐ 检测率
☐ 演练 ≥ 季度
☐ 应急 SOP 演练 100%

人员:
☐ 红队人员 OSCP / CRTO 比例
☐ 案例库丰富度
☐ 技能矩阵覆盖
```

## 十三、团队组织

```
红队 (3-8 人):
  负责人 (高级红队 / 案例 100+)
  红队工程师 (Web + AD + 内网)
  Cloud 红队
  AI 红队 (新)
  C2 运维 (基建)
  报告 (兼职)

蓝队 / SOC (10-20 人):
  L1 + L2 + L3 + Threat Hunter
  
渗透服务 (商业, 5-15 人):
  Web + AD + 内网
  Cloud + K8s
  移动 / IoT
  AI / LLM
  报告 + 项目经理

SRC (2-5 人):
  平台运营
  Triage + 复测
  奖励发放
  关系维护

CTF / 培训 (1-2 人):
  内部培训
  CTF 参赛
  实战题库
```

## 十四、典型生产架构

### 14.1 中型互联网公司红队

```
红队:        4 人 (Web + AD + Cloud + AI)
基建:        Sliver + Cobalt Strike + Cloudflare CDN
工具:        Burp Pro + nuclei + BBOT + 自研
SRC:        HackerOne + 内部 (补天 接入)
演练:        季度 + 年度第三方
紫队:        Caldera + ATT&CK Navigator
报告:        PlexTrac
合规:        网安法 + 等保 2
```

### 14.2 央企信创关基

```
红队:        外包 + 自有 (8 人)
基建:        自研 C2 + 国产 CDN
工具:        Cobalt Strike + Sliver + 国产 (Goby / Viper)
HW:         年度 + 上级演练
重保:        T-3 月准备 + 7x24 SOC
SRC:        补天 / 漏洞盒子 + 内部
演练:        季度 + ATT&CK Navigator
报告:        国密加密 + 内部专网
合规:        网安法 + 等保 3 + 关基 + 国密
信创:        鲲鹏 + openEuler + 国产工具
```

## 十五、推荐栈（最佳实践）

```
红队基建:    Cobalt Strike (商) + Sliver (开源) ⭐ + Mythic
信息收集:    BBOT ⭐ + Project Discovery 全家桶
Web:        Burp Pro ⭐ + nuclei + sqlmap + ffuf + Autorize
AD:         BloodHound ⭐ + Impacket ⭐ + Certipy + Rubeus + Mimikatz
内网:        ligolo-ng + chisel + LinPEAS/WinPEAS
Cloud:       Pacu + ROADtools + Steampipe + Wiz
K8s:        kube-hunter + Peirates + kubescape
AI 红队:    Garak + PyRIT + Promptfoo + llm-guard
0day:        AFL++ + libFuzzer + CodeQL + Ghidra
社工:        Evilginx2 + Gophish + 自建钓鱼基建
报告:        PlexTrac (商) + 自研 Jinja2 Markdown
管理:        DefectDojo + Faraday + Jira
SRC:        HackerOne + 补天 + 漏洞盒子 + 内部
紫队:        Caldera + Atomic Red Team + Vectr + ATT&CK Navigator
演练:        季度 + HW 行动 + 国家级
合规:        网安法 + 等保 + 关基 + CISP-PTE
团队:        红队 4-8 + SOC 10-20 + 服务 5-15 + SRC 2-5
KPI:         ATT&CK 覆盖 + 检测率 + SLA + 闭环
```

> 📖 **核心判断**：渗透测试最佳实践 = **12 项金标 + 法律授权 + ROE + PTES/OSSTMM + 工具链标准 + 持续 Recon + CVSS+业务分级 + 报告标准 + SRC/Bug Bounty + 红蓝紫(ATT&CK/Caldera) + HW 行动重保 + KPI(覆盖率/检测率/SLA) + 团队组织 + 国产合规(等保/关基/信创)**。能给央企/大型互联网搭"红队 4-8 人 + Sliver/CS + BBOT + Burp + Pacu + AI 红队 + PlexTrac + DefectDojo + 季度演练 + HW 重保"完整体系，落地从授权 → Recon → Exploit → 报告 → 闭环 全流程，就具备红队负责人/渗透服务经理能力。**法律先行 + 道德 + 技术。**
