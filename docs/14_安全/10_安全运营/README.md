# 安全运营（SecOps / SOC）

> 安全运营 = **预防 + 检测 + 响应 + 恢复 + 改进**。**SOC 不是工具堆砌，是人 + 流程 + 工具 + 情报的综合体**。**SIEM + SOAR + EDR + NDR + TI + IR + 度量** = 现代化 SecOps 标配。

## 一、SecOps 核心能力

```
NIST CSF 框架:
  Identify    资产清单 / 风险评估 / 治理
  Protect      访问控制 / 数据安全 / 培训
  Detect       异常检测 / 持续监控 / 告警
  Respond      响应计划 / 通讯 / 分析 / 缓解 / 改进
  Recover      恢复计划 / 改进 / 通讯

SOC 工作:
  1. 7x24 监控
  2. 告警分类响应
  3. 事件调查
  4. 威胁狩猎（主动）
  5. 漏洞管理
  6. 安全度量
  7. 应急演练
  8. 安全意识
```

## 二、SOC 组织架构

### 2.1 人员分层

```
CISO / 安全总监         战略 + 风险 + 合规

L3 高级分析师 / 红队     威胁狩猎 + 高级事件 + 复盘
L2 SOC 分析师           事件深挖 + 调查
L1 SOC 监控             7x24 告警响应 + 一线处置

横向:
  IR (Incident Response)   重大事件
  TI (Threat Intelligence) 情报分析
  Pentester                 主动测试
  GRC                       合规 / 审计
  SecDevOps                工具 + 自动化
```

### 2.2 SOC 规模参考

```
小型（10-50 人公司）:
  1 个安全工程师 + 外包 MSSP

中型（50-500 人）:
  2-5 人安全团队
  - 1 SecDevOps
  - 1-2 SOC
  - 1 GRC

大型（500-5000 人）:
  10-30 人
  - 7x24 SOC (L1/L2/L3)
  - 红蓝队
  - GRC
  - IR

超大型（> 5000 人）:
  50-200+
  - 多 SOC 中心
  - 专门 IR / TI / 红队 / 蓝队 / 紫队
  - 全球 7x24
```

## 三、SIEM（Security Information & Event Management）

### 3.1 SIEM 核心能力

```
1. 日志采集（Log Aggregation）
2. 标准化（Normalization）
3. 关联分析（Correlation）
4. 告警（Alerting）
5. 搜索 / 调查（Investigation）
6. 报表 / 合规（Reporting）
7. 威胁情报集成
8. SOAR 集成
```

### 3.2 主流 SIEM

| SIEM | 类型 | 国内 | 适合 |
|:---|:---|:---:|:---|
| **Splunk** | 商业 | ⭐⭐⭐ | 大型 |
| **IBM QRadar** | 商业 | ⭐⭐⭐ | 金融 |
| **Microsoft Sentinel** | 云 SaaS | ⭐⭐ | Azure 生态 |
| **Elastic Security** | 开源/商业 | ⭐⭐⭐⭐ | 中小 |
| **Wazuh** ⭐ | 开源 | ⭐⭐⭐⭐ | 中小开源 |
| **Graylog** | 开源/商业 | ⭐⭐⭐ | 日志为主 |
| **Chronicle** | Google | ⭐ | 多云 |
| **国内: 奇安信 NGSOC** | 商业 | ⭐⭐⭐⭐⭐ | 合规 |
| **长亭 雷池/牧云** | 商业 | ⭐⭐⭐⭐ | 国产 |
| **绿盟 SAS-H** | 商业 | ⭐⭐⭐⭐ | 国产 |

### 3.3 Wazuh 开源 SIEM 实战

```bash
# All-in-One 部署
curl -sO https://packages.wazuh.com/4.7/wazuh-install.sh
sudo bash wazuh-install.sh -a

# 组件:
#   - Wazuh Manager (规则引擎 + HIDS 后端)
#   - Wazuh Indexer (OpenSearch)
#   - Wazuh Dashboard (Kibana)
#   - Filebeat
#   - Wazuh Agent (主机端)

# Agent 部署
curl -so wazuh-agent.deb https://.../wazuh-agent_x.x.x.deb
WAZUH_MANAGER='manager.company.com' dpkg -i wazuh-agent.deb

# 内置能力:
#   ✅ HIDS (文件完整性 / 异常进程 / rootkit)
#   ✅ 日志采集
#   ✅ 合规检查 (CIS / PCI / GDPR / NIST)
#   ✅ 漏洞检测
#   ✅ 容器监控
#   ✅ 云监控 (AWS / Azure / GCP)
#   ✅ MITRE ATT&CK 映射
#   ✅ Active Response (自动处置)
```

### 3.4 数据源接入

```
必接入:
  ✅ 操作系统日志 (Linux auth/syslog/audit / Windows Event)
  ✅ 网络设备 (防火墙 / IDS / IPS / VPN / 交换机)
  ✅ 应用日志 (Web / App / DB / 中间件)
  ✅ K8s / 容器 (Audit / Pod / Falco)
  ✅ 云平台 (AWS CloudTrail / Azure Activity / GCP Audit / 阿里 ActionTrail)
  ✅ IdP (LDAP / AD / Keycloak / Okta)
  ✅ EDR / 杀软告警
  ✅ DLP
  ✅ 邮件网关
  ✅ WAF
  ✅ DNS

可选:
  - 数据库审计
  - 业务关键日志（订单 / 支付）
  - 物理门禁
```

### 3.5 检测规则示例

```yaml
# Wazuh rule: 暴力破解
<rule id="100100" level="10">
  <if_matched_sid>5710</if_matched_sid>
  <same_source_ip />
  <description>SSH brute force attack</description>
  <mitre>
    <id>T1110</id>
  </mitre>
  <group>authentication_failures,</group>
</rule>

# Sigma rule（跨 SIEM 通用格式）
title: Suspicious PowerShell Encoded Command
status: stable
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|endswith: '\powershell.exe'
    CommandLine|contains:
      - '-enc'
      - '-EncodedCommand'
  condition: selection
level: high
tags:
  - attack.execution
  - attack.t1059.001
```

## 四、SOAR（Security Orchestration, Automation & Response）

### 4.1 SOAR 价值

```
没有 SOAR:
  - 一个告警 → L1 手动看 → L2 调查 → 写邮件 → 通知开发
  - 每天 10000 告警 → 90% 噪声 → 关键漏过
  - MTTR 几小时-几天

有 SOAR:
  - 告警进来 → 自动富化（whois / VT / TI）→ 自动判断
  - 简单的: 自动处置（封 IP / 隔离主机 / 重置密码）
  - 复杂的: Playbook 引导 L1 一步步操作
  - MTTR 缩到分钟
```

### 4.2 主流 SOAR

```
商业:
  - Palo Alto XSOAR ⭐⭐⭐⭐⭐
  - Splunk SOAR (前 Phantom)
  - IBM Resilient
  - Microsoft Sentinel Playbooks
  - Swimlane
  - Tines

开源:
  - Shuffle (开源 SOAR) ⭐
  - TheHive + Cortex
  - n8n / Zapier (轻量自动化)
  - 自研 Python 脚本 + Webhook

国内:
  - 长亭 雷池
  - 奇安信 SOAR
  - 安恒 SOAR
```

### 4.3 典型 Playbook

```
Playbook: 钓鱼邮件处置
  1. 接收告警（邮件网关 / 用户上报）
  2. 提取 IOC（URL / 附件 hash / 发件人）
  3. 富化:
     - VirusTotal 查 hash
     - URLhaus 查链接
     - 内部 TI 平台
  4. 判断:
     - 已知恶意 → 自动隔离邮件 + 封发件人
     - 未知 → 沙箱跑附件
  5. 影响评估:
     - 谁收到了
     - 谁点击了
     - 是否有人输入凭证
  6. 处置:
     - 隔离邮件
     - 封 URL / IP
     - 重置受影响用户密码
     - 强制下机器扫描
  7. 通知:
     - 告知受影响员工
     - 上报 IR 团队
  8. 闭环:
     - 工单记录
     - 加入 TI 库
     - 培训素材
```

```
Playbook: 横向移动检测
  1. EDR 触发"异常 RDP 登录"
  2. 富化:
     - 源主机情况
     - 目标主机情况
     - 用户身份
  3. 判断:
     - 工作时间 / 计划任务 → 可能正常
     - 凌晨 / 异常账号 → 高风险
  4. 自动隔离主机（如确认）
  5. 取证（内存 / 进程 / 日志）
  6. 通知 IR
```

## 五、EDR / XDR

### 5.1 EDR vs XDR

```
EDR (Endpoint Detection & Response):
  端点行为分析 + 检测 + 响应
  
XDR (Extended Detection & Response):
  端点 + 网络 + 云 + 邮件 + 身份 跨域关联
  
2025 趋势: EDR → XDR
```

### 5.2 主流产品

```
国际:
  - CrowdStrike Falcon
  - SentinelOne
  - Microsoft Defender for Endpoint
  - Palo Alto Cortex XDR
  - Sophos Intercept X
  - Cybereason

国内:
  - 奇安信 天擎 ⭐
  - 360 终端安全
  - 深信服 EDR
  - 安恒 EDR
  - 山石 EDR

开源:
  - Wazuh (HIDS + EDR 基础)
  - Velociraptor (DFIR + 终端响应)
  - osquery + Kolide / Fleet
  - Tetragon / Falco (Linux/K8s)
```

### 5.3 osquery 实战

```sql
-- 列出所有进程
SELECT pid, name, path, cmdline FROM processes;

-- 监听端口
SELECT pid, port, address FROM listening_ports;

-- 找 SUID 文件
SELECT path, uid, gid FROM file 
  WHERE path LIKE '/usr/bin/%' AND mode LIKE '%4%%' LIMIT 50;

-- 用户登录
SELECT * FROM logged_in_users;

-- 异常计划任务
SELECT * FROM crontab WHERE event NOT IN ('@reboot') AND path LIKE '%/tmp/%';

-- USB 设备
SELECT * FROM usb_devices;
```

```yaml
# Kolide / Fleet 部署 + 中央调度
# 周期查询所有节点 → 统一分析
schedules:
  - name: high_severity_processes
    query: SELECT * FROM processes WHERE on_disk = 0
    interval: 300                  # 5 min
    snapshot: true
```

## 六、NDR（Network Detection & Response）

```
能力:
  - 全流量分析
  - 行为基线 + 异常检测
  - C2 / Beacon 检测
  - 数据外泄检测
  - 加密流量识别（不解密）

工具:
  开源:    Suricata + Zeek + Arkime
  商业:    Vectra / ExtraHop / Darktrace
  国内:    长亭洞鉴 / 启明天眼 / 奇安信天眼

部署:
  SPAN/TAP 镜像 → NDR
  云上: VPC Mirroring / 阿里云镜像
  K8s: Cilium / Pixie eBPF
```

## 七、威胁情报（TI）

### 7.1 TI 类型

```
战略级（Strategic）:
  - 行业趋势 / 攻击组织 / 地缘
  - 给 CISO 决策

战术级（Tactical）:
  - 战术 / 技术 / 流程 (TTPs)
  - MITRE ATT&CK 映射
  - 给红蓝队

操作级（Operational）:
  - 具体活动情报
  - "近期 APT41 在攻击金融业"

技术级（Technical / IOC）:
  - IP / Domain / Hash / URL
  - 直接进 SIEM / Firewall
```

### 7.2 IOC 来源

```
免费:
  - AbuseIPDB
  - URLhaus
  - MalwareBazaar
  - AlienVault OTX
  - VirusTotal (有限免费)
  - GreyNoise
  - Shodan
  - Censys

商业:
  - Recorded Future
  - Mandiant
  - CrowdStrike
  - Anomali
  - ThreatConnect

国内:
  - 微步在线 (TI 平台)
  - 奇安信 威胁情报中心
  - 安天 / 360 / 安恒
  - QAX-A-TIP
  - 长亭

格式:
  - STIX / TAXII（标准）
  - MISP（开源 TI 平台）
  - OpenIOC
  - JSON / CSV / IOC feed
```

### 7.3 MISP（开源 TI 平台）

```bash
# Docker 部署
git clone https://github.com/MISP/misp-docker
cd misp-docker
docker-compose up -d

# 用途:
✅ 组织内部 IOC 共享
✅ 与外部 TI 同步
✅ 自动分发到 SIEM / Firewall
✅ STIX/TAXII feed
```

## 八、事件响应（IR）

### 8.1 NIST IR 生命周期

```
1. Preparation        准备
2. Detection & Analysis 检测分析
3. Containment         隔离
4. Eradication        根除
5. Recovery            恢复
6. Post-Incident      复盘
```

### 8.2 IR 团队

```
Incident Commander    总指挥（一个）
Tech Lead            技术决策
Forensics            取证
Investigator         调查
Communications       通讯（内部 / 客户 / 媒体）
Legal / GRC           合规 / 法律
Business             业务对接

文化:
  - Blameless（不追责，找根因）
  - 透明（不掩盖）
  - 学习（持续改进）
```

### 8.3 IR 剧本模板

```
1. 检测（T0）
   - 告警源
   - 初步分类（True/False Positive）
   - 严重度

2. 集结（T+15min）
   - Incident Commander 指定
   - Slack/飞书 战情室
   - 工单创建

3. 隔离（T+1h）
   - 主机网络隔离
   - 账号禁用
   - WAF 阻断

4. 取证（T+2h）
   - 内存 / 磁盘镜像
   - 日志归档
   - 时间线建立

5. 分析（T+4h）
   - 入侵路径
   - 横向移动范围
   - 数据外泄评估
   - IOC 提取

6. 根除（T+24h）
   - 删 webshell / 后门
   - 重置凭证
   - 修补漏洞
   - 重做受影响主机

7. 恢复（T+48h）
   - 业务恢复
   - 监控加强
   - 灰度上线

8. 复盘（T+1w）
   - 时间线总结
   - 教训
   - 改进项
   - 流程更新
```

### 8.4 IR 沟通模板

```
主题: 【高/中/低】安全事件通报 #编号
时间: 2026-06-26 14:30 起
状态: 已隔离 / 调查中 / 已恢复
影响范围: 
  - 系统: xxx
  - 数据: xxx
  - 客户: xxx
当前进展:
  - 已完成: ...
  - 进行中: ...
  - 下一步: ...
联系人: IR-Commander xxx
下次更新: 30 分钟后
```

### 8.5 取证工具

```
磁盘:        dd / dc3dd / FTK Imager
内存:        LiME / AVML / Volatility
网络:        Wireshark / Arkime / tcpdump
进程:        ps / pstree / lsof
全栈:        SIFT Workstation / CAINE / REMnux / Velociraptor
LiME:        Linux Memory Extractor
GRR / Velociraptor: 大规模远程取证
```

## 九、威胁狩猎（Threat Hunting）

### 9.1 主动 vs 被动

```
被动: 等告警 → 响应
主动: 假设被入侵 → 找证据 → 证实/证伪

假设驱动:
  "如果攻击者已经在内网，他会做什么？"
  → 用 SIEM 查
  → MITRE ATT&CK 映射
  → TTPs 检测
```

### 9.2 狩猎方法

```
1. 假设（Hypothesis）
   "攻击者可能用 PowerShell 编码命令"

2. 数据收集
   process_creation logs

3. 查询
   SIEM 搜索 PowerShell -enc

4. 分析
   过滤合法 → 异常分析

5. 输出
   - 新的检测规则
   - IOC
   - 工单 / 事件
   - 流程改进
```

### 9.3 工具

```
- Velociraptor       大规模 DFIR + 狩猎
- Cortex XSOAR
- Sigma 规则库
- Splunk Enterprise Security
- Elastic Security 内置
- Splunk SIEM rules from Atomic Red Team
- HELK (Hunting ELK)
```

## 十、安全度量与汇报

### 10.1 关键 KPI

```
覆盖率:
  - 资产 / 应用 / 端点接入率
  - SBOM 覆盖率
  - 日志接入完整性

检测:
  - 告警量 / 误报率
  - MTTD (Mean Time to Detect)
  - MTTI (Mean Time to Investigate)
  - 检测覆盖率（MITRE ATT&CK 覆盖）

响应:
  - MTTR (Mean Time to Respond)
  - MTTC (Mean Time to Contain)
  - 重大事件数 / 重大事件 MTTR
  - SLA 达成

漏洞:
  - 修复 SLA 达成
  - 累计漏洞 / 修复 / 新增
  - 漏洞密度

合规:
  - 等保 / PCI / SOC 评估
  - 内审 / 外审通过

意识:
  - 培训覆盖率
  - 钓鱼演练点击率
  - SRC 内部上报数

成本:
  - 安全投入 / 业务损失避免
  - ROI
```

### 10.2 报告模板

```
月度 SOC 报告:
  1. 关键指标 (KPI Dashboard)
  2. 重大事件回顾
  3. 漏洞修复进展
  4. 威胁情报亮点
  5. 改进计划
  6. 资源 / 预算需求

季度战略报告:
  1. 整体安全态势
  2. 风险评估
  3. 合规状态
  4. 行业对标
  5. 战略调整
```

## 十一、安全意识 & 培训

### 11.1 培训内容

```
全员（年度必修）:
  - 密码安全
  - 钓鱼邮件识别
  - 数据保护
  - 移动设备安全
  - 社会工程学

研发（专项）:
  - 安全编码 (OWASP Top 10)
  - SAST 工具使用
  - Secret 管理
  - 代码审查

SRE / 运维:
  - 配置基线
  - 应急响应
  - 日志分析

管理层:
  - 风险评估
  - 投资 ROI
  - 合规要求
```

### 11.2 钓鱼演练

```
工具:
  - GoPhish (开源)
  - KnowBe4 (商业)
  - 安全意识培训商业版

执行:
  季度演练 → 点击率 → 培训 → 再演练
  目标: 点击率 < 5%
```

## 十二、Purple Team（紫队）

```
Red Team:    模拟攻击
Blue Team:   防御检测
Purple Team: 协同（红蓝联合，最有效）

价值:
  - 红队找弱点 + 蓝队当场补
  - 检测规则现场验证
  - MITRE ATT&CK 覆盖度评估
  - 文化建设（不是对抗，是协作）

工具:
  - Atomic Red Team (开源 TTP 测试)
  - Caldera (MITRE 出品)
  - PurpleSharp
  - Vectr (紫队协作平台)
```

## 十三、典型坑

| 坑 | 建议 |
|:---|:---|
| **SIEM 当日志收集器** | 配关联 + 告警 |
| **告警淹没** | 调优 + SOAR 自动化 |
| **没人 7x24** | MSSP / 排班 |
| **没情报** | 至少订阅免费 TI |
| **EDR 装了不看** | 接入 SIEM + SOAR |
| **没 IR 剧本** | 季度演练 |
| **重大事件靠救火** | 提前准备 |
| **修了不复盘** | Blameless 复盘 |
| **报表没数据** | 度量先行 |
| **不培训** | 钓鱼演练 |
| **红蓝对立** | Purple Team 文化 |
| **依赖单一工具** | 工具栈 + 人 + 流程 |
| **应急联系人不更新** | 季度刷新 |
| **告警优先级乱** | 风险加权 |
| **跨团队不协作** | 战情室 + RACI |

## 十四、最佳实践 Checklist

```
组织:
☐ CISO / 安全负责人
☐ 7x24 SOC（自建 / MSSP）
☐ IR 团队 + 剧本
☐ 红蓝紫定期演练

工具:
☐ SIEM（Wazuh / Splunk）
☐ SOAR
☐ EDR / XDR
☐ NDR
☐ TI 平台
☐ 漏洞管理（DefectDojo）
☐ 取证工具就位

流程:
☐ NIST CSF 对齐
☐ IR 流程文档化
☐ 沟通模板
☐ 升级矩阵
☐ Blameless 复盘
☐ 合规对接

度量:
☐ MTTD / MTTR 跟踪
☐ MITRE ATT&CK 覆盖
☐ 月度 / 季度报告
☐ 看板可视化

文化:
☐ 全员培训
☐ 钓鱼演练（< 5%）
☐ 安全意识周
☐ Bug Bounty
☐ Blameless 复盘
☐ Purple Team
```

## 十五、推荐栈（2025）

### 15.1 小团队 / 起步

```
SIEM:      Wazuh
EDR:       Wazuh Agent + osquery
NDR:       Suricata + Zeek
TI:        MISP + 免费 feed
SOAR:      Shuffle + n8n
IR:        SIFT + Velociraptor
培训:      GoPhish
```

### 15.2 中型企业

```
SIEM:      Wazuh / Elastic Security / Splunk
EDR:       CrowdStrike / SentinelOne / 奇安信天擎
NDR:       Suricata + Zeek + Arkime + 商业（Vectra/天眼）
SOAR:      Shuffle / XSOAR
TI:        微步 / Recorded Future / MISP
漏洞:      DefectDojo + 长亭 / 启明
应急:      内部 IR + 外部 顾问
```

### 15.3 大型 / 跨国

```
+ 多 SOC 中心（follow-the-sun）
+ 自研 SOAR Playbook 库
+ AI 辅助 (LLM 告警分析、见 12_AIOps)
+ Threat Hunting 团队
+ Bug Bounty 平台
+ Purple Team 季度
+ 红蓝紫一体化
+ 应急法律 + PR
```

## 十六、学习路径

```
入门（2 周）:
  1. SOC 角色 + 工作流程
  2. NIST CSF 框架
  3. MITRE ATT&CK 基础
  4. SIEM 基础 (Wazuh)

中级（3 月）:
  5. SIEM 规则编写 (Sigma)
  6. EDR / NDR 部署
  7. IR 剧本演练
  8. SOAR Playbook
  9. TI 集成

高级（6 月+）:
  10. Threat Hunting
  11. 取证 + 内存分析
  12. Purple Team
  13. APT 跟踪
  14. Detection Engineering

专家:
  15. 大规模 SOC 设计
  16. AI 辅助 SOC（详见 12_AIOps）
  17. 红队全流程
  18. 国家级威胁应对
```

## 十七、参考资料

```
框架:
  - NIST CSF
  - MITRE ATT&CK
  - SANS Incident Handler's Handbook
  - 等保 2.0
  - ISO 27001

书:
  - 《Blue Team Handbook》
  - 《Practical Threat Intelligence》
  - 《Incident Response & Computer Forensics》
  - 《The Art of Memory Forensics》

社区:
  - SANS Internet Storm Center
  - r/blueteamsec / r/SecOps
  - MITRE Engenuity
  - DFIR Report
  - 国内: FreeBuf / 安全客 / 看雪 / 微步

证书:
  - GIAC: GCIH / GCFA / GNFA / GREM
  - SANS SEC504 / SEC503
  - CISSP / CISM
  - 国内: CISP / CISP-PTE
```

> 📖 **核心判断**：SecOps 是**人 + 流程 + 工具 + 情报 + 度量**的综合体。**SIEM + SOAR + EDR/XDR + NDR + TI** 是 2025 标准工具栈，但**没有人和流程，工具就是摆设**。**MTTD/MTTR 是真北指标**——所有努力服务于"快速发现 + 快速响应"。**Blameless 复盘 + Purple Team 协作 + 持续培训** 是文化建设。最容易翻车的不是攻击太强，而是：**SOC 没人 7x24、IR 没剧本、复盘走形式、培训只为合规**——把这四个文化做对，技术工具的效果至少翻倍。
