# 漏洞管理

> 漏洞管理 = **发现 + 评估 + 优先级排序 + 修复 + 验证 + 度量**。**漏洞永远修不完，关键是修对的**。**漏洞密度（vulnerability density）和修复时间（MTTR）** 比漏洞总数更重要。

## 一、漏洞管理生命周期

```
1. Discover          扫描 / 渗透 / 情报订阅 / Bug Bounty
2. Triage            评级 / 验证（去误报）
3. Prioritize        风险评估（CVSS + EPSS + 资产价值 + 威胁情报）
4. Remediate         修复 / 缓解 / 接受
5. Verify            验证修复
6. Track             度量 / 报表 / 改进

→ 闭环 + 度量 = 真正的漏洞管理
→ 不是"找漏洞"，是"快速降低风险"
```

## 二、漏洞评级体系

### 2.1 CVSS（通用漏洞评分）

```
CVSS v3.1 / v4.0 (2024)

四个维度:
  Base       本质属性（不变）
    - Attack Vector (网络/邻接/本地/物理)
    - Attack Complexity
    - Privileges Required
    - User Interaction
    - Scope (变化/不变)
    - C/I/A 影响
  
  Temporal   时间属性
    - Exploit Code Maturity
    - Remediation Level
    - Report Confidence
  
  Environmental 环境属性
    - 资产价值
    - 安全需求
  
评分:
  0.0       None
  0.1-3.9   Low
  4.0-6.9   Medium
  7.0-8.9   High
  9.0-10.0  Critical
```

### 2.2 EPSS（漏洞利用预测）⭐ 2025 新主流

```
Exploit Prediction Scoring System (FIRST)
  - 基于机器学习
  - 预测"未来 30 天被实际利用"的概率（0-1）
  - 数据源: 漏洞披露、利用代码、攻击观测、社交媒体

为什么需要 EPSS:
  CVSS 9.8 ≠ 一定被利用
  CVSS 5.0 但 EPSS 0.95 → 比 9.8 但 EPSS 0.001 更危险
  
组合优先级:
  EPSS 高 + CVSS 高 + 资产关键 = 立即修
  EPSS 高 + CVSS 中             = 优先修
  EPSS 低 + CVSS 高             = 排队
  EPSS 低 + CVSS 低             = 延后

查询: https://epss.cyentia.com/
```

### 2.3 KEV（已知被利用漏洞）

```
CISA Known Exploited Vulnerabilities Catalog
  - 已确认在野利用的漏洞
  - 政府强制修复时限（通常 14 天）
  - 比 CVSS 更"硬"的指标

→ 出现在 KEV = 立即修
→ 这是漏洞管理的"红线"

订阅: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
```

### 2.4 综合优先级模型（推荐）

```
P0 (立即修, < 24h):
  - 在 KEV 中
  - EPSS ≥ 0.5 + CVSS ≥ 7
  - 已被武器化（Metasploit / PoC 公开）
  - 关键资产 + 0day

P1 (7 天内):
  - CVSS ≥ 9
  - EPSS ≥ 0.1
  - 互联网暴露 + CVSS ≥ 7

P2 (30 天):
  - CVSS 7-8.9
  - 内网仅暴露

P3 (季度):
  - CVSS < 7
  - 非关键资产

P4 (按需):
  - 信息泄漏
  - 配置建议
```

## 三、漏洞发现来源

### 3.1 自动扫描

```
主机层:
  - Nessus / Qualys / OpenVAS (端口、服务、CVE)
  - Lynis (Linux 加固)
  - Vuls (Go, 轻量 CVE)
  
容器/K8s:
  - Trivy / Grype / Clair
  - kube-bench / Kubescape / Polaris
  
Web:
  - Burp Suite / OWASP ZAP
  - Acunetix / AppScan
  - 国内: 长亭 X-Ray / Goby / AWVS / 360 / 启明
  
SAST:
  - SonarQube / Semgrep / CodeQL
  - Snyk Code / Checkmarx / Fortify
  
DAST:
  - OWASP ZAP / Burp / Acunetix
  
IaC:
  - Checkov / tfsec / KICS
  
依赖:
  - Snyk / OSV-Scanner / Dependabot / Renovate
  - Trivy fs
  
云配置:
  - Prowler / ScoutSuite / CloudSploit
  - Wiz / Lacework / Aqua / Sysdig (商业)
  
国产:
  - 长亭洞鉴 / 牧云
  - 奇安信 NGSOC
  - 绿盟 RSAS
  - 启明 天镜
```

### 3.2 渗透测试

```
内部渗透 (Red Team):
  - 季度 / 年度
  - 全公司视角
  - 真实攻击模拟
  
外部渗透:
  - 第三方 / 合规要求
  - 等保 / PCI / SOC2
  
漏洞挖掘:
  - 业务上线前
  - 重大变更后

工具:
  - Cobalt Strike / Sliver / Mythic
  - Metasploit
  - BloodHound (AD)
  - Empire / Covenant
```

### 3.3 Bug Bounty / SRC

```
内部 SRC（应急响应中心）:
  - 阿里 ASRC / 腾讯 TSRC / 字节 BSRC / 美团 MTSRC
  - 自建 / 平台代运营

外部平台:
  - HackerOne (全球)
  - Bugcrowd
  - Synack
  - 国内: 补天 / 漏洞盒子 / 360 SRC平台 / 火线

奖金区间:
  P0: 1万-50万+
  P1: 5千-5万
  P2: 1千-1万
  P3: 几百-几千

收益:
  ✅ 持续众测
  ✅ 多元化视角
  ✅ 性价比高
```

### 3.4 情报订阅

```
公共:
  - NVD (https://nvd.nist.gov/)
  - MITRE CVE
  - GitHub Security Advisory
  - OSV (Open Source Vulnerabilities)
  - Vendor PSIRTs (RedHat / Ubuntu / Microsoft)
  
中文:
  - CNNVD (国家漏洞库)
  - CNVD (国家信息安全漏洞共享平台)
  - CN-CERT
  - 阿里云漏洞库 / 腾讯安全 / 奇安信

威胁情报商业:
  - Recorded Future
  - Mandiant
  - Crowdstrike Falcon Intelligence
  - 国内: 微步 / 奇安信 / 安天 / 360 / 安恒

订阅工具:
  - email + RSS
  - 自研 LLM 摘要器（详见 12_AIOps 02_LLM告警）
```

## 四、漏洞工单平台

### 4.1 DefectDojo（开源 ⭐）

```bash
# 部署
git clone https://github.com/DefectDojo/django-DefectDojo
cd django-DefectDojo
./dc-up.sh

# 特点:
✅ 集成 50+ 工具（Trivy/Snyk/Nessus/ZAP/...）
✅ 自动去重
✅ Jira 集成
✅ SLA 跟踪
✅ 报表
✅ Bug Bounty 流程
```

### 4.2 商业平台

```
- Snyk (开发者友好)
- Wiz (CNAPP)
- Qualys VMDR (老牌)
- Tenable.io (Nessus 云版)
- 国内: 长亭/奇安信/绿盟自研平台
```

### 4.3 Jira / 飞书工单流程

```
漏洞流程:
  Reported → Triaged → Assigned → In Progress → Fixed → Verified → Closed
  
工单字段:
  - CVE / CVSS / EPSS / KEV
  - 影响资产清单
  - 修复 owner
  - SLA 截止时间
  - 优先级 (P0-P4)
  - 状态
  - 关联 commit / PR
  - 验证报告
```

## 五、修复策略

### 5.1 三种处置

```
1. Remediate（修复）
   - 升级补丁
   - 重构代码
   - 关闭服务
   
2. Mitigate（缓解）
   - WAF 规则
   - 防火墙限制
   - 配置改造
   - 临时下线
   
3. Accept（接受）
   - 业务无法影响
   - 风险已接受签字
   - 补偿性控制到位
```

### 5.2 修复 SLA

| 严重度 | 互联网暴露 | 内网 | 离线 |
|:---|:---|:---|:---|
| KEV / 0day | 24h | 48h | 7 天 |
| Critical (CVSS 9+) | 24h | 7 天 | 30 天 |
| High (7-8.9) | 7 天 | 30 天 | 90 天 |
| Medium (4-6.9) | 30 天 | 90 天 | 季度 |
| Low (< 4) | 季度 | 半年 | 按需 |

### 5.3 紧急修复（Log4Shell 级）

```
T+0:    情报订阅触发
T+1h:   确认范围
T+2h:   止血（WAF 规则 / 防火墙）
T+6h:   评估修复方案
T+24h:  灰度部署修复
T+72h:  全量恢复
T+1w:   复盘 + 加固
```

### 5.4 虚拟补丁

```
官方补丁未发布前的临时防护:
  - WAF 规则（拦截特定 payload）
  - IPS 规则（Suricata/Snort）
  - 防火墙规则（封 IP）
  - 应用层配置（关接口）
  - Falco rule（运行时阻断）

工具:
  - ModSecurity OWASP CRS
  - Cloudflare WAF custom
  - 雷池 SafeLine
  - 长亭洞鉴自动规则
```

## 六、零日（0day）应对

### 6.1 检测

```
✅ 异常行为基线
✅ EDR 文件/进程异常
✅ NDR 流量异常
✅ Honeypot 触发
✅ Bug Bounty / SRC 上报
✅ 威胁情报订阅
```

### 6.2 处置

```
1. 立即隔离
2. 取证（不要重启）
3. 限流 / 关接口
4. 临时缓解（WAF/IPS 虚拟补丁）
5. 等官方补丁 / 自研修复
6. 验证 + 全网部署
7. 公开 IOC 给社区
8. 复盘 + 加固
```

## 七、典型漏洞类型与防御

### 7.1 Web 漏洞 (OWASP Top 10)

| 类型 | 示例 | 防御 |
|:---|:---|:---|
| **SQL 注入** | `1' OR '1'='1` | 参数化查询 / ORM |
| **XSS** | `<script>alert(1)</script>` | 输出编码 + CSP |
| **CSRF** | 跨站请求 | Token + SameSite |
| **SSRF** | 内网探测 | URL 白名单 / 出口 ACL |
| **XXE** | XML 实体注入 | 禁外部实体 |
| **RCE** | 命令注入 | 不拼命令 / 白名单 |
| **反序列化** | Java/PHP/Python | 不反序列化不可信 |
| **路径穿越** | `../../etc/passwd` | 白名单路径 |
| **文件上传** | webshell | 类型/内容/沙箱 |
| **认证缺陷** | 弱密码 / 越权 | MFA + RBAC |

### 7.2 中间件常见 CVE

```
Apache       2.4.x         多个 mod_proxy 高危
Nginx        ngx_http_*    路径穿越 / 内存读取
Tomcat       AJP / Ghostcat (CVE-2020-1938)
WebLogic     XMLDecoder / T3 协议
JBoss         JMX / EAP
Redis        未授权 RCE / 主从同步
MongoDB     未授权
Elasticsearch  未授权 / Groovy 沙箱逃逸
Kafka         JMX 暴露
Memcached    无认证
RabbitMQ     默认凭证
```

### 7.3 主机 CVE 关键应对

```
Linux 内核    Dirty Pipe / Pwnkit / nf_tables UAF
SSH         CVE-2024-6387 (regreSSHion)
OpenSSL      Heartbleed / 3.0 高危
glibc         多个 buffer overflow
sudo          Baron Samedit (CVE-2021-3156)
polkit        Pwnkit (CVE-2021-4034)
```

## 八、度量与改进

### 8.1 关键指标 (KPI)

```
覆盖率:
  - 资产 / 应用覆盖率
  - 扫描频次达成率
  - SBOM 覆盖率

漏洞趋势:
  - 新增 vs 修复
  - 累计漏洞数
  - 漏洞密度（漏洞数 / KLOC 或 资产数）

时效性:
  - MTTD (Mean Time to Detect)
  - MTTR (Mean Time to Remediate)
  - 各级别 SLA 达成率
  - 超期未修数

质量:
  - 重复漏洞率
  - 误报率
  - 验证不通过率
  - Bug Bounty 漏报率
```

### 8.2 定期报告

```
月报:
  - 新增 / 修复 / 累计
  - 各业务线对比
  - Top 10 漏洞类型
  - SLA 达成
  - 重大事件

季度复盘:
  - 趋势 + 改进
  - 流程 / 工具升级
  - 培训需求

年度审计:
  - 合规对接
  - 第三方评估
  - 战略调整
```

## 九、合规与漏洞管理

```
等保 2.0:
  - 三级要求: 漏扫月度 + 修复闭环
  - 重保期间高频
  
PCI-DSS:
  - 季度漏扫（ASV 认证扫描）
  - 重大变更后再扫
  
SOC 2:
  - 漏洞管理流程文档
  - 修复 SLA 证据
  
GDPR / 个保法:
  - 影响个人数据的漏洞 72h 内披露

ISO 27001:
  - 漏洞管理流程
  - 风险评估
```

## 十、典型坑

| 坑 | 建议 |
|:---|:---|
| **只扫不修** | 闭环 + SLA |
| **CVSS 唯一** | + EPSS + KEV |
| **修复无优先级** | 综合模型 |
| **误报淹没** | 去重 + 三方验证 |
| **资产清单不全** | CMDB 必备 |
| **不订阅情报** | NVD/CNNVD/PSIRT |
| **季度才扫一次** | 持续监控 |
| **修复无验证** | 二次扫描 |
| **跨团队甩锅** | Owner 明确 + Jira |
| **0day 来了懵** | 应急剧本 + 演练 |
| **修复影响业务** | 灰度 + 回滚 |
| **不分析根因** | 类似漏洞重现 |
| **不培训开发** | SDL + SAST 教育 |
| **Bug Bounty 无人接** | 7x24 + SLA |
| **报表给老板**“漏洞少了” | 衡量 MTTR / 风险下降 |

## 十一、最佳实践 Checklist

```
基础:
☐ 资产 CMDB 完整
☐ SBOM 全企业
☐ 漏洞工单平台（DefectDojo）
☐ 情报订阅自动化

扫描:
☐ 主机周期扫
☐ Web 应用扫
☐ 容器/镜像扫
☐ K8s/IaC 扫
☐ SAST CI 集成
☐ DAST 测试环境
☐ 依赖持续监控

优先级:
☐ CVSS + EPSS + KEV 综合
☐ 资产价值加权
☐ 业务影响评估
☐ 暴露面分级

修复:
☐ SLA 明确 + 看板
☐ Owner 制
☐ Jira / 飞书工单
☐ 修复后验证
☐ 紧急虚拟补丁（WAF/IPS）

应急:
☐ 0day 剧本
☐ 季度演练
☐ Bug Bounty / SRC
☐ 媒体公关预案

度量:
☐ MTTD / MTTR
☐ 漏洞密度
☐ SLA 达成
☐ 月报 / 季报
☐ 复盘 + 改进
```

## 十二、推荐技术栈（2025）

### 12.1 小团队

```
扫描:    Trivy + OpenVAS + OWASP ZAP + OSV-Scanner
工单:    DefectDojo
情报:    NVD RSS + GitHub Advisory
应急:    WAF (雷池) + 人工
报表:    DefectDojo dashboard
```

### 12.2 中大企业

```
扫描:    Nessus + Trivy + Snyk + 自研 Web 扫
SAST/DAST/IAST: SonarQube + Burp + Checkmarx
工单:    DefectDojo / 自研 + Jira
情报:    商业 TI (Recorded Future / 微步) + 自动 LLM 摘要
渗透:    内部红队 + 第三方
Bug Bounty: HackerOne / 补天
SOC:    7x24 + SOAR
CNAPP:   Wiz / Aqua / 长亭 (容器/云原生)
```

### 12.3 国产/信创

```
+ 长亭洞鉴 / 牧云
+ 奇安信 NGSOC / 启明天镜
+ 绿盟 RSAS / 安全狗
+ 等保扫描器（合规专用）
+ CNNVD/CNVD 订阅
```

## 十三、学习路径

```
入门（2 周）:
  1. CVSS / CVE 体系
  2. Trivy / Nessus 实战
  3. OWASP Top 10
  4. DefectDojo 部署

中级（1 个月）:
  5. EPSS / KEV 整合
  6. SAST / DAST 集成 CI
  7. Bug Bounty 接入
  8. 漏洞应急流程

高级（3 个月）:
  9. 红队 / 渗透实战
  10. 0day 响应剧本
  11. 自动化漏洞修复
  12. 大规模漏洞治理

专家:
  13. 自研漏洞挖掘
  14. SRC 运营
  15. 漏洞情报体系
  16. SDL 全流程
```

## 十四、参考资料

```
标准:
  - CVE / NVD / CVSS / EPSS
  - MITRE ATT&CK
  - OWASP Top 10
  - 等保 2.0 / PCI-DSS

书:
  - 《The Web Application Hacker's Handbook》
  - 《The Hacker Playbook》
  - 《Practical Threat Intelligence》
  - 《白帽子讲 Web 安全》(吴翰清)

工具:
  - DefectDojo: https://defectdojo.com/
  - OSV: https://osv.dev/
  - KEV: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
  - EPSS: https://www.first.org/epss/

社区:
  - r/netsec / r/AskNetsec
  - SANS / OWASP
  - 国内: 看雪 / FreeBuf / 安全客 / 先知 / 长亭社区
```

> 📖 **核心判断**：漏洞管理的精髓不是"找到所有漏洞"，而是**"用 20% 精力修掉 80% 风险"**。**CVSS + EPSS + KEV 三位一体优先级** 是 2025 的核心方法论。**SBOM 是基础设施**（看不见 = 管不了），**DefectDojo 是闭环平台**（不闭环 = 白扫），**虚拟补丁是急救方案**（0day 必备）。**修复 MTTR 是真北指标**——所有努力都要服务于"快速降风险"。
