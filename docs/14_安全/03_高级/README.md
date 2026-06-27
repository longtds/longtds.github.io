# 高级

> 安全高级 = **安全平台架构(SOC+SOAR+TIP+CTEM) + 威胁建模 + 红蓝对抗(Purple Team) + Threat Hunting + 供应链安全(SLSA L3+) + Confidential Computing + 零信任全栈 + 数据安全治理(DSPM/DLP) + 关键基础设施 + 国密+等保3+网安等级测评 + AI 安全(模型/Agent/Prompt 攻击) + 多云安全 + 主权云安全 + 应急响应+取证 + 团队组织(BSE/CISO)**。本章面向安全架构师 / CISO / 红蓝队负责人。

## 一、安全平台架构

```
SOC (Security Operations Center):
  24x7 监控 + 响应

SIEM 层:
  日志采集 / 关联 / 告警
  Wazuh / Elastic / Splunk / 阿里 SLS

SOAR (Security Orchestration & Automated Response):
  剧本化响应 (Playbook)
  自动隔离 + 自动取证 + 自动通知
  Splunk Phantom / Demisto / TheHive ⭐

TIP (Threat Intelligence Platform):
  MISP ⭐ / OpenCTI ⭐
  IoC 共享
  自动订阅

CTEM (Continuous Threat Exposure Management, Gartner 2024):
  - 持续暴露面发现
  - 优先级 (业务价值 × 威胁度)
  - 自动验证
  - 闭环修复

工具:
  Watchtowr / Tenable / Qualys (商业)
  自研 + Nuclei + Trivy + ASM

资产管理 (ASM):
  Attack Surface Management
  外部暴露面持续扫描
  - Censys / Shodan
  - 长亭 / 安恒 (国产)
```

## 二、威胁建模 (Threat Modeling)

```
方法:
  STRIDE ⭐ (Microsoft)
  PASTA (7 阶段)
  Trike
  Attack Trees
  
工具:
  Microsoft Threat Modeling Tool
  OWASP Threat Dragon ⭐
  PyTM (代码即建模)

实操:
  设计阶段 必做
  绘制 DFD (Data Flow Diagram)
  对每个数据流应用 STRIDE
  评估风险 (CVSS / DREAD)
  列对策 (Control)
  Review (季度)

ATT&CK 框架:
  Tactics (战术, 14 类)
  Techniques (技术, 200+)
  Procedures (具体)
  
  Initial Access → Execution → Persistence → ... → Impact

落地:
  覆盖率 (我能检测哪些 Technique)
  缺口 (哪些没覆盖)
  红蓝对抗 (基于 ATT&CK)
```

## 三、红蓝对抗 (Purple Team)

```
红队 (Red Team):
  - 模拟真实攻击 (APT)
  - 不告知蓝队
  - 多向量 (网络 / 钓鱼 / 物理 / 社工)
  - 持久化 + 横向 + 数据外泄
  
蓝队 (Blue Team):
  - 监控 + 响应
  - SOC + SIEM
  - 取证 + 复盘

紫队 (Purple Team) ⭐:
  - 红蓝协同
  - 共享 TTPs (ATT&CK)
  - 快速验证 + 改进
  
工具 (Red):
  Cobalt Strike (商业, 业界标准)
  Sliver ⭐ (开源, BishopFox)
  Metasploit
  Mythic (现代 C2)
  
工具 (Blue):
  Wazuh + Falco + Suricata
  Velociraptor ⭐ (取证 + 响应)
  CrowdStrike Falcon (商业)
  阿里云盾 / 奇安信 EDR

演练:
  季度 / 半年
  范围 + 规则 + 时长
  Postmortem + 改进 + KPI
```

## 四、Threat Hunting (主动狩猎)

```
理念:
  不等告警, 主动找隐蔽威胁
  假设入侵已发生

流程:
  1. 假设 (Hypothesis): "APT 在 PowerShell 编码命令"
  2. 数据 (Data): SIEM EDR
  3. 查询 (Query): KQL / SPL / Lucene
  4. 结果 (Findings)
  5. 转规则 (Detection Rule)

工具:
  Elastic Security ⭐ + KQL
  Splunk + SPL
  阿里云 SLS + 自定义
  Microsoft Defender + KQL

知识库:
  ATT&CK Navigator
  MITRE D3FEND (防御映射)
  Sigma (跨 SIEM 规则)
  Detection Engineering as Code

技能:
  - 攻击者思维
  - SIEM 查询
  - 取证基础
  - 行为分析
  - PowerShell / Linux 命令深度
```

## 五、供应链安全 (SLSA L3+)

```
SLSA Levels:
  L1: Build process 文档化
  L2: 第三方托管构建 (GitHub Actions / GitLab CI)
  L3: 隔离构建 + 不可篡改 provenance ⭐
  L4: 双人审核 + 可重现

L3 要求:
  ☐ Hermetic build (无网络 / 锁定依赖)
  ☐ Provenance (谁 / 何时 / 从哪 / 命令)
  ☐ in-toto attestation
  ☐ Tekton Chains / GitHub Attestations
  ☐ Sigstore (cosign + Rekor + Fulcio)
  ☐ Reproducible builds

工具:
  GitHub Artifact Attestations
  Tekton Chains
  GoReleaser + SBOM + cosign
  sigstore-python / sigstore-go

供应链威胁:
  Solar Winds (2020) - CI 后门
  Log4Shell (2021) - 依赖漏洞
  3CX (2023) - 多级供应链
  XZ Utils (2024) - 上游后门

防御:
  ☐ 内网镜像源 (Nexus / Harbor proxy)
  ☐ 依赖锁定 (lock file)
  ☐ SBOM + 签名验证
  ☐ Dependabot / Renovate
  ☐ 自建 base image (定期 patch)
  ☐ Trivy + Snyk 持续
```

## 六、Confidential Computing

```
威胁模型:
  - Hypervisor 不可信
  - OS 不可信
  - 运维不可信
  - 只信任 CPU TEE

技术:
  Intel TDX (VM 级)
  Intel SGX (Enclave)
  AMD SEV-SNP
  ARM CCA
  海光 CSV ⭐ (国产)
  
场景:
  - 多方计算 (隐私计算)
  - SaaS 客户机密
  - 国家级数据
  - LLM 模型加密

实现:
  Confidential Containers (Kata-cc) ⭐
  Inclavare Containers (国产)
  OpenAnolis Confidential Cloud

Attestation:
  - Verifier 验证 TEE 证明
  - 凭证 (Vault) 只下发到可信
  - 国密 + CSV 集成
```

## 七、零信任全栈

```
Phase 1: 身份 + MFA (基础)
Phase 2: 设备认证 + Conditional Access
Phase 3: 应用代理 + JIT + Step-up
Phase 4: Workload (SPIFFE + mTLS)
Phase 5: 数据 + ABAC
Phase 6: 持续验证 + UEBA + Risk

工具栈:
  身份:        Keycloak / IDaaS
  设备:        Jamf / Intune / Workspace ONE
  代理:        Cloudflare Access / Pomerium / Teleport
  Workload:   SPIRE + Istio mTLS
  策略:        OPA / Cedar / OpenFGA
  Risk:        UEBA + ML
  
国产:
  奇安信 / 360 / 启明 / 阿里云
  绿盟 / 山石 / 深信服

落地难点:
  - 遗留系统 (老协议)
  - 用户体验
  - 性能 (代理转发)
  - 组织变革
```

## 八、数据安全治理 (DSPM / DLP)

```
DSPM (Data Security Posture Management):
  - 自动发现敏感数据
  - 风险评估
  - 持续监控
  
工具:
  Wiz (商业领导)
  Cyera / BigID
  Microsoft Purview
  阿里云 / 华为云 (国产)

DLP (Data Loss Prevention):
  网络:        出口监控 (敏感 → 阻断)
  终端:        USB / 邮件 / 上传
  云:          API + 文件
  
工具:
  Symantec / Forcepoint (商业)
  Wazuh + 规则
  阿里云 DLP
  
联邦学习 / 隐私计算:
  - 数据不出域
  - 模型出域
  
工具:
  FATE (微众)
  TensorFlow Federated
  PySyft
  阿里隐语 / 蚂蚁链
  腾讯天御
```

## 九、AI 安全（新兴）

```
AI 模型威胁:
  ☐ Prompt Injection (越狱)
  ☐ Jailbreak (绕过 RLHF)
  ☐ Data Poisoning (训练数据投毒)
  ☐ Model Extraction (窃取)
  ☐ Adversarial Examples (对抗样本)
  ☐ Membership Inference (隐私推断)
  ☐ Backdoor (后门)

防御:
  - Guardrails (NeMo / LlamaGuard ⭐ / Aegis)
  - RLHF + Red Teaming
  - Watermarking
  - Output filter
  - LLM Judge

Agent 威胁:
  ☐ Tool Confused (工具混淆)
  ☐ Indirect Prompt Injection (RAG / Web 注入)
  ☐ Excessive Agency (越权操作)
  ☐ Multi-Agent Collusion

MCP 安全:
  - Tool 鉴权
  - Resource 隔离
  - Audit 全量
  - Token Exchange 委托

LLM 应用安全 Top 10 (OWASP 2025):
  1.  Prompt Injection
  2.  Sensitive Info Disclosure
  3.  Supply Chain
  4.  Data + Model Poisoning
  5.  Improper Output Handling
  6.  Excessive Agency
  7.  System Prompt Leakage
  8.  Vector + Embedding Weakness
  9.  Misinformation
  10. Unbounded Consumption

工具:
  Garak ⭐ (LLM 漏扫)
  PyRIT (Microsoft AI Red Team)
  llm-guard
  Lakera (商业)
```

## 十、多云 + 主权云

```
多云挑战:
  - 身份不统一
  - 策略不一致
  - 日志分散
  - 合规多套
  
工具:
  CSPM (Cloud Security Posture Management):
    Wiz / Prisma Cloud / Lacework
    阿里云 CSPM
    Steampipe ⭐ (开源)

CWPP (Cloud Workload Protection):
  Falcon / SentinelOne
  Cilium Tetragon
  阿里云盾

CNAPP (Cloud-Native App Protection):
  整合 CSPM + CWPP + IaC + Secret + SBOM
  
主权云:
  阿里 / 华为 / 腾讯 政务专属
  国密 / 等保 / 备案 全栈
  数据出境合规
  关键技术自主可控
```

## 十一、关键基础设施 (CII)

```
中国 关基条例 (2021):
  - 公共通信 / 能源 / 交通 / 水利 / 金融 / 公共服务 / 电子政务 / 国防
  - 网络安全等保 3 级以上
  - 年度评估
  - 重要数据出境审查

要求:
  ☐ 等保 3+
  ☐ 关基条例
  ☐ 数据安全法
  ☐ 个人信息保护法
  ☐ 网络安全审查
  ☐ 国密
  ☐ 信创

技术:
  ☐ 国产 OS + DB + 中间件
  ☐ 国密 TLS / PKI / KMS / HSM
  ☐ 物理隔离 + 单向
  ☐ 24x7 SOC + 国家威胁情报
  ☐ 年度红蓝对抗
```

## 十二、应急响应 + 取证

```
PICERL 流程:
  Preparation     准备 (工具 / SOP / 演练)
  Identification  识别 (告警 / 异常)
  Containment     遏制 (隔离 / 阻断)
  Eradication     清除 (清理 / 修复)
  Recovery        恢复 (上线 / 验证)
  Lessons Learned 复盘 (Postmortem)

取证工具:
  Velociraptor ⭐ (现代)
  GRR (Google)
  Volatility (内存)
  Autopsy / Sleuth Kit (磁盘)
  Plaso (timeline)
  CAINE Linux

容器取证:
  Sysdig Inspect
  Falco runtime
  CRI-O / containerd 镜像导出
  
内存取证:
  Volatility (Linux/Win/Mac)
  AVML (采集)

证据链:
  - 不可篡改 (Hash + WORM)
  - 时间戳 (NTP / 法证时间)
  - 责任链 (Chain of Custody)
  - 合规留存 (3-7 年)
```

## 十三、团队组织

```
CISO (Chief Information Security Officer):
  战略 + 风险 + 合规 + 预算

BSE (Business Security Engineering):
  与业务线对接
  威胁建模
  Architecture Review

SecOps / SOC:
  24x7 监控 + 响应
  3 班轮值

Red Team (红队):
  季度对抗
  3-5 人

Blue Team (蓝队):
  防御 + 改进
  与 SOC 重叠

DevSecOps:
  左移工具链
  与 DevOps 平台合作

Identity & IAM:
  身份平台
  零信任

GRC (Governance, Risk, Compliance):
  等保 / 国密 / 备案 / 审计

应急响应 (IR):
  CSIRT
  取证 + Forensics

人员 (中型 1000 人公司):
  - CISO + 1 副
  - SOC: 8-12 人 (24x7)
  - BSE: 3-5 人
  - Red Team: 3 人
  - DevSecOps: 3 人
  - IAM: 2-3 人
  - GRC: 2 人
  - IR: 2 人
  共 ~25-35 人
```

## 十四、Checklist（高级）

```
平台:
☐ SOC + SIEM + SOAR + TIP + CTEM
☐ ASM (外部暴露面)
☐ Wazuh + TheHive + MISP
☐ Steampipe / Wiz CSPM

威胁建模:
☐ STRIDE + PyTM
☐ ATT&CK 覆盖率 + 缺口
☐ Threat Dragon

红蓝:
☐ 红队 季度 + 紫队
☐ Sliver / Cobalt Strike
☐ Velociraptor 取证
☐ ATT&CK 演练

供应链:
☐ SLSA L3+
☐ Sigstore + cosign + Rekor
☐ Hermetic build
☐ in-toto

Confidential:
☐ Kata-cc + TDX/SEV/CSV
☐ Attestation + Vault

零信任:
☐ 6 阶段完整
☐ SPIRE + Istio
☐ UEBA + Risk

数据:
☐ DSPM (Wiz/Cyera/阿里)
☐ DLP (网络+终端+云)
☐ 隐私计算 (FATE/隐语)

AI 安全:
☐ Guardrails (NeMo/LlamaGuard)
☐ Prompt Injection 防御
☐ Garak / PyRIT 测试
☐ OWASP LLM Top 10

多云:
☐ CSPM (Wiz / Steampipe)
☐ CWPP (Falcon / Tetragon)
☐ CNAPP (整合)

关基:
☐ 等保 3+
☐ 国密 + 信创
☐ 24x7 SOC
☐ 年度红蓝
☐ 数据出境审查

IR + 取证:
☐ PICERL SOP
☐ Velociraptor / Volatility
☐ 证据链 + 合规留存

团队:
☐ CISO + 7 组 (SOC/BSE/Red/DevSec/IAM/GRC/IR)
☐ 1000 人公司 ~30 人
```

## 十五、推荐栈（高级）

```
SOC:        Wazuh + Elastic + TheHive + MISP + Velociraptor
SOAR:       TheHive Cortex / Splunk Phantom / 自研
TIP:        MISP + OpenCTI
CTEM:       Watchtowr / Steampipe / 自研
ASM:        Censys + Shodan + 长亭 ARL
威胁建模:   PyTM + Threat Dragon + ATT&CK Navigator
红队:        Sliver ⭐ + Cobalt Strike + Mythic
紫队:        ATT&CK + Caldera + 自动化
取证:        Velociraptor ⭐ + Volatility + Autopsy + Plaso
供应链:     Sigstore (cosign+Rekor+Fulcio) + SLSA L3 + in-toto + Syft
Confidential: Kata-cc + Intel TDX / AMD SEV / 海光 CSV
零信任:     SPIRE + Istio + UEBA + OPA/OpenFGA + Conditional Access
DSPM:       Wiz / Cyera / 阿里云
DLP:        Symantec + 阿里云 DLP
隐私计算:   FATE / 隐语 / 蚂蚁链
AI 安全:    LlamaGuard ⭐ + Garak + PyRIT + llm-guard
多云:        Steampipe + Tetragon + Falco
关基:        等保 3+ + 国密 + 信创全栈
合规:        阿里 / 奇安信 测评机构
```

> 📖 **核心判断**：安全高级 = **SOC 平台(SIEM+SOAR+TIP+CTEM+ASM) + 威胁建模(STRIDE+ATT&CK) + 红蓝紫(Sliver+Velociraptor) + Threat Hunting + 供应链 SLSA L3(Sigstore+in-toto) + Confidential Computing + 零信任 6 阶段 + DSPM/DLP/隐私计算 + AI 安全(Prompt Injection/Guardrails) + 多云 CNAPP + 关基(等保3+国密+信创) + PICERL IR + 团队组织(CISO+7 组)**。能给央企/大型互联网画"Wazuh + SPIRE + Istio + Kata-cc + 隐语 + LlamaGuard + Tongsuo + 等保3 + 国密 + 信创"完整安全平台，落地红蓝对抗 + Threat Hunting + 供应链 L3 + AI 安全 + 数据治理 + IR + 取证，就具备安全架构师/CISO 能力。
