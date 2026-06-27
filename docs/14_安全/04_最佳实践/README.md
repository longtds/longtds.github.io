# 最佳实践

> 安全最佳实践 = **CIS 基线 + DevSecOps 工具链 + K8s 安全基线 + 零信任落地 + 数据保护 + 等保3级 + 国密改造 + 24x7 SOC + 红蓝演练 + IR SOP + 团队 + KPI**。本章把"会装 Trivy"升级到"运营企业级安全平台"。

## 一、12 项金标准

```
1. ✅ CIS Benchmarks 基线 (Linux/K8s/Docker/Cloud)
2. ✅ DevSecOps 全链 (SAST+SCA+IaC+Secret+Container+SBOM+签名+admission)
3. ✅ Pod Security Standards: Restricted + NetworkPolicy 默认拒
4. ✅ Service Mesh Strict mTLS + AuthorizationPolicy 零信任
5. ✅ Vault 全栈动态凭证 + 国密 HSM
6. ✅ 全员 MFA (WebAuthn 优先) + IdP SSO
7. ✅ 24x7 SOC + SIEM 6mo + SOAR 自动化
8. ✅ 季度红蓝对抗 + ATT&CK 覆盖率 + 紫队
9. ✅ 供应链 SLSA L2/L3 + Sigstore + SBOM
10. ✅ 等保 3 级 + 国密 + 信创 + 备案
11. ✅ IR PICERL + Velociraptor 取证 + 演练
12. ✅ KPI 度量 (MTTD/MTTR/覆盖率) + 季度回顾
```

## 二、CIS Benchmarks

```
Linux (RHEL / Ubuntu):
  ☐ 系统加固 (sysctl + SELinux + auditd)
  ☐ 用户/sudo
  ☐ SSH 加固
  ☐ 防火墙
  ☐ 文件权限
  ☐ 日志

工具:
  OpenSCAP (自动化扫描) ⭐
  Lynis (审计)
  
Docker:
  ☐ root 运行禁
  ☐ 用户命名空间
  ☐ 只读 rootfs
  ☐ 资源限制
  ☐ 安全 capability
  ☐ AppArmor / Seccomp
  
工具: docker bench security

Kubernetes:
  ☐ apiserver 加固
  ☐ etcd 加密
  ☐ kubelet 认证
  ☐ RBAC 最小
  ☐ NetworkPolicy
  ☐ Pod Security
  ☐ audit
  
工具: kube-bench ⭐

Cloud (AWS/Azure/GCP):
  ☐ IAM 最小
  ☐ S3 公开禁
  ☐ 加密默认
  ☐ 日志启用
  
工具: Steampipe + Scout Suite + Prowler
```

## 三、DevSecOps 工具链（标准化）

```
.gitlab-ci.yml 示例:

stages: [lint, security, build, scan, sign, deploy]

# 1. Secret 扫描
secret-scan:
  stage: security
  script: gitleaks detect --source . --verbose

# 2. SAST
sast:
  stage: security
  script:
    - semgrep --config auto --error
    - sonar-scanner

# 3. SCA
sca:
  stage: security
  script:
    - trivy fs --severity HIGH,CRITICAL --exit-code 1 .
    - dependency-check --project app --scan .

# 4. IaC
iac:
  stage: security
  script:
    - checkov -d terraform/
    - kube-linter lint k8s/

# 5. License
license:
  stage: security
  script: licensee detect

# 6. Build
build:
  stage: build
  script: docker buildx build -t app:$CI_COMMIT_SHA .

# 7. Container Scan
container-scan:
  stage: scan
  script:
    - trivy image --severity HIGH,CRITICAL --exit-code 1 app:$CI_COMMIT_SHA

# 8. SBOM
sbom:
  stage: scan
  script: syft app:$CI_COMMIT_SHA -o cyclonedx-json > sbom.json

# 9. Sign
sign:
  stage: sign
  script:
    - cosign sign --key $COSIGN_KEY app:$CI_COMMIT_SHA
    - cosign attest --predicate sbom.json --type cyclonedx --key $COSIGN_KEY app:$CI_COMMIT_SHA

# 10. Deploy
deploy:
  stage: deploy
  script:
    - cosign verify --key $COSIGN_PUB app:$CI_COMMIT_SHA
    - kubectl apply -f deploy.yaml
```

```
门禁:
  ☐ Critical CVE = 0
  ☐ High CVE < 5 (允许漂白 + 复审)
  ☐ Secret 检测 = 0
  ☐ License 黑名单 = 0
  ☐ IaC 严重违规 = 0
  ☐ 镜像必签 (cosign verify)
```

## 四、K8s 安全基线

```
☐ Pod Security: Restricted
☐ NetworkPolicy 默认拒
☐ Cilium / Calico + 加密
☐ Service Mesh Strict mTLS
☐ Kyverno admission policy
  - 禁 :latest
  - 必签名验证 (cosign)
  - 必 resources
  - 必非 root
  - 必 readOnlyRootFilesystem
☐ kube-bench 季度
☐ Audit policy: RequestResponse (关键资源)
☐ etcd 加密 (KMS plugin)
☐ Secret: external-secrets + Vault
☐ Falco / Tetragon 运行时
☐ ImagePullPolicy: Always
☐ Image 内网源 (Harbor mirror)
```

## 五、零信任落地

```
Phase 1 (基础, 1-3 月):
  ✅ 统一 IdP + 全员 MFA
  ✅ oauth2-proxy 内部应用
  ✅ Teleport SSH

Phase 2 (中级, 3-6 月):
  ✅ 设备认证 (MDM)
  ✅ Conditional Access
  ✅ Vault Dynamic
  ✅ Step-up 高敏

Phase 3 (高级, 6-12 月):
  ✅ SPIRE + Istio mTLS
  ✅ UEBA + Risk-based
  ✅ OPA / OpenFGA

Phase 4 (深化, 12+ 月):
  ✅ JIT 自服务
  ✅ Confidential Computing
  ✅ Sovereign Identity
```

## 六、数据保护

```
分类:
  公开 / 内部 / 机密 / 绝密
  PII / PHI / 财务 / 行业

加密:
  ☐ 传输: TLS 1.3 强制
  ☐ 存储: KMS envelope (S3 / DB / Backup)
  ☐ 字段: SM4 / AES-256-GCM
  ☐ 备份: 加密 + 异地

脱敏:
  ☐ 日志 (手机号 + 身份证 + 卡号)
  ☐ 测试环境 (生产脱敏副本)
  ☐ 查询脱敏 (视图 + 中间件)

DLP:
  ☐ 网络出口监控
  ☐ 终端 USB / 邮件
  ☐ 云存储 API
  ☐ DSPM 持续发现

隐私计算 (内部数据共享):
  联邦学习 (FATE / 隐语 / TFF)
  MPC / TEE
```

## 七、等保 3 级

```
身份鉴别:
  ☐ MFA + 国密 USB Key
  ☐ 失败锁定 + 超时
  
访问控制:
  ☐ 最小授权 + 双批
  ☐ 强制访问控制 (SELinux)
  
安全审计:
  ☐ 全审计 → SIEM 6mo (不可篡改)
  ☐ 审计员独立
  
入侵防范:
  ☐ HIDS (Wazuh) + IPS (Suricata)
  ☐ 漏扫月度 + 补丁季度
  ☐ 蜜罐
  
恶意代码防范:
  ☐ EDR (阿里 / 360 / 奇安信)
  ☐ 邮件网关 (国产)
  
可信验证:
  ☐ 国密 TPM/TCM
  ☐ 启动 + 运行 完整性
  
集中管控:
  ☐ SOC 24x7
  ☐ 应急演练 季度
  ☐ 公安备案 + 年度测评
```

## 八、国密 + 信创

```
密码学:
  Tongsuo (BabaSSL) ⭐
  GmSSL
  SM2 / SM3 / SM4 / SM9 / ZUC

PKI:
  CFCA 国密证书
  自建国密 CA

HSM:
  江南天安 / 三未信安 / 渔翁 (国产)
  SafeNet / Thales (国际兜底)

TLS:
  TLCP (双证书)
  TLS 1.3 + GM 套件

应用:
  Nginx + Tongsuo
  Java + GmSSL
  Go + GmSSL-Go

K8s:
  apiserver 国密 TLS
  etcd 加密

数据库:
  MySQL / PG 字段加密 SM4
  TDE (透明加密)

信创栈:
  鲲鹏 + openEuler + 麒麟
  飞腾 + UOS
  海光 + CentOS 兼容
```

## 九、24x7 SOC

```
组织:
  L1 (监控员, 4-6 人 24x7): 接报 + 分级
  L2 (分析师, 3-5 人): 调查 + 响应
  L3 (高级 / 取证, 2 人): 复杂事件 + Forensics
  Threat Hunter (1-2 人): 主动狩猎
  SOC Manager (1 人)

班次:
  3 班轮值 / 12h
  on-call backup
  节假日 增员

工具:
  SIEM: Wazuh + Elastic (开源) / Splunk (商业)
  SOAR: TheHive + Cortex / Phantom
  TIP: MISP + OpenCTI
  EDR: Falcon / 阿里云盾 / 奇安信
  Ticket: Jira / TheHive 内置

KPI:
  MTTD < 5 min
  MTTA < 5 min
  MTTR P0 < 30 min
  P1 < 4h
  误报率 < 10%
  Playbook 覆盖率 > 80%
```

## 十、红蓝演练

```
频次:
  ☐ 季度 (内部红蓝)
  ☐ 年度 (第三方红队 + 实战化)
  ☐ 关基: 国家红队 (HW 行动)

范围:
  ☐ 互联网暴露面
  ☐ 内网横向
  ☐ 钓鱼员工
  ☐ 物理 (考察)
  ☐ 社工

ATT&CK 覆盖:
  ☐ Initial Access
  ☐ Execution
  ☐ Persistence
  ☐ Privilege Escalation
  ☐ Defense Evasion
  ☐ Credential Access
  ☐ Discovery
  ☐ Lateral Movement
  ☐ Collection
  ☐ Exfiltration
  ☐ Impact

工具:
  Red: Sliver / Cobalt Strike / Mythic / Caldera
  Blue: Velociraptor + Wazuh + Falco + Suricata
  Purple: ATT&CK Navigator + 自动化

KPI:
  覆盖 ATT&CK Technique > 70%
  红队成功率 < 30% (检测率 > 70%)
  MTTD 红队 < 1h
  改进项 季度跟踪
```

## 十一、IR (Incident Response) SOP

```
PICERL:
  Preparation:    工具 / SOP / 演练 / 培训
  Identification: 告警 → 5min ack
  Containment:    隔离 (网络 / 主机) → 15min
  Eradication:    清理 (恶意代码 / 后门) → 2h
  Recovery:       恢复 (重装 / 验证) → 24h
  Lessons:        Postmortem → 7d

P0 (大面积或关键数据泄露):
  RTO < 1h (止血)
  全员 + 法务 + 公关
  对外通报 (合规)

P1 (单业务被入侵):
  RTO < 4h
  SOC + 业务

P2 (单机入侵):
  RTO < 24h
  SOC L2

P3 (低级别异常):
  工作时间

法律:
  ☐ 个保法: 数据泄露 72h 内报告
  ☐ 网安法: 关基 立即报告
  ☐ 数据安全法: 重要数据
  ☐ GDPR (跨境): 72h
```

## 十二、团队组织

```
CISO:        1 人
SOC:         L1 (4-6) + L2 (3-5) + L3 (2) + Hunter (2) = 12-15 人
BSE:         3-5 人
Red Team:    3-5 人
DevSecOps:   3-5 人
IAM:         2-3 人
GRC + 合规:  2-3 人
IR + 取证:   2-3 人

中型 (1000 人公司): 25-35 人
大型 (10K 人): 100+ 人
央企关基: 50+ 人 + 外包 SOC
```

## 十三、KPI

```
平台:
☐ DevSecOps 工具链覆盖 100%
☐ K8s PSS Restricted 100% (生产)
☐ NetworkPolicy 覆盖 100%
☐ Service Mesh mTLS 覆盖 > 90%
☐ Vault Dynamic 覆盖 > 80%
☐ 镜像签名验证 100%

SOC:
☐ MTTD < 5 min
☐ MTTA < 5 min
☐ MTTR P0 < 30 min
☐ 告警噪音率 < 10%
☐ Playbook 覆盖率 > 80%
☐ SIEM 完整率 > 99%

红蓝:
☐ 季度演练 100%
☐ ATT&CK Technique 覆盖 > 70%
☐ 检测率 > 70%
☐ 改进项闭环率 > 80%

合规:
☐ 等保 3 测评通过
☐ 国密改造 100%
☐ 季度权限审查 100%
☐ 备案 + 报告 准时

IR:
☐ P0 RTO < 1h
☐ Postmortem 完成率 100%
☐ Action Item 闭环 > 80%
☐ 演练通过率 > 90%

合规:
☐ 数据泄露 72h 上报
☐ 个保法 / 数据安全法 / 网安法 全合规
```

## 十四、典型生产架构

### 14.1 互联网中大型

```
DevSecOps:   SonarQube + Semgrep + Trivy + Checkov + cosign
WAF:        阿里云 WAF / 雷池
K8s:        PSS + NetPol + Kyverno + Falco
Mesh:       Istio Strict mTLS
Vault:      HA + Dynamic
SIEM:       Wazuh + Elastic + TheHive + MISP
SOC:        24x7 12 人
红蓝:        季度 + 年度第三方
EDR:        阿里云盾 + 360
合规:        等保 2 级
```

### 14.2 央企信创关基

```
DevSecOps:   SonarQube + 国产 SCA + Trivy + 雷池
WAF:        雷池 ⭐ + 启明
K8s:        PSS + Kyverno + Falco + 国密
Mesh:       Istio + Tongsuo
Vault:      HA + 国密 HSM (江南天安)
SIEM:       国产 SOC + Wazuh
SOC:        24x7 + 外包 + 国家通报
红蓝:        季度 + HW 行动 ⭐
EDR:        奇安信 / 360 / 启明
PKI:        CFCA 国密
密码学:     Tongsuo + SM2/SM3/SM4
合规:        等保 3 级 ⭐ + 国密 + 关基条例 + 信创
信创:        鲲鹏 + openEuler + 麒麟
```

## 十五、推荐栈（最佳实践）

```
DevSecOps:   SonarQube + Semgrep + Trivy + Checkov + Syft + cosign + Kyverno
K8s:        PSS Restricted + NetPol + Falco + Tetragon
Mesh:       Istio Strict + SPIRE
Vault:      HA + Dynamic + 国密 HSM
WAF:        雷池 ⭐ + ModSec + 阿里
SIEM:       Wazuh ⭐ + Elastic + TheHive + MISP
SOAR:       TheHive Cortex + Playbook
EDR:        阿里云盾 / 奇安信 / Falcon
ASM:        Censys + 长亭 + 自研
密码学:     Tongsuo (SM2/SM3/SM4) ⭐
PKI:        CFCA + cert-manager
HSM:        江南天安 / 三未信安 (国产)
红蓝:        Sliver + Caldera + ATT&CK Navigator
取证:        Velociraptor ⭐ + Volatility
DSPM:       Wiz / 阿里云 DSPM
DLP:        阿里 DLP + 自研
隐私计算:   隐语 / FATE
AI 安全:    LlamaGuard + Garak + 自研 Guardrails
合规:        等保 3 级 ⭐ + 国密 + 个保 + 网安 + 关基 + 信创
SOC:        24x7 + 季度演练 + Postmortem
团队:        CISO + 7 组 (25-35 人 / 中型)
```

> 📖 **核心判断**：安全最佳实践 = **12 项金标准 + CIS 基线 + DevSecOps 工具链 + K8s 安全基线 + 零信任 4 阶段 + 数据保护(KMS+DLP+DSPM) + 等保 3 级 + 国密+信创 + 24x7 SOC + 季度红蓝(ATT&CK) + PICERL IR + 取证 + 团队 25-35 人 + KPI(MTTD/MTTR/覆盖率) + 合规法规(个保/网安/数据/关基)**。能给央企/大型互联网画"Wazuh + Trivy + Kyverno + Falco + Istio + Vault + 雷池 + Velociraptor + 隐语 + Tongsuo + 等保3 + 关基 + 信创"完整安全平台，落地 SOC 24x7 + 红蓝 + 国密 + 取证 + 合规，就具备安全平台负责人 / CISO 副手能力。
