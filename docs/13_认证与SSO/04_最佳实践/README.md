# 最佳实践

> 身份认证最佳实践 = **统一 IdP + LDAP/AD 接入 + 应用矩阵 OIDC + 工作负载 mTLS + 零信任 + Vault 动态凭证 + PAM + MFA(WebAuthn) + IGA + SCIM + 合规(等保/国密/备案) + 国产化路径 + 监控告警 + Incident SOP + 团队 + KPI**。本章把"会装 Keycloak"升级到"运营企业级身份平台"。

## 一、12 项金标准

```
1. ✅ 单一 IdP, 不多套 (Keycloak / Okta / Azure AD 选一)
2. ✅ HR 是 SoT (Source of Truth), SCIM 自动开/撤
3. ✅ 所有应用走 OIDC/SAML, 禁本地账号 (admin 除外)
4. ✅ MFA 全员 (WebAuthn 优先, TOTP 兜底)
5. ✅ K8s --oidc, 不再人手 kubeconfig
6. ✅ 工作负载用 SPIFFE / IRSA / WI, 不再静态 access key
7. ✅ DB 用 Vault 动态凭证, 不再静态密码
8. ✅ SSH CA + Teleport, 不再静态 SSH key
9. ✅ Service Mesh Strict mTLS (服务间默认加密)
10. ✅ 审计 SIEM 6mo + 季度权限审查
11. ✅ 国产/国密/等保 三件套
12. ✅ Incident SOP + 月度演练
```

## 二、单一 IdP 选型

```
互联网 / 中型 (< 1000 人):
  Keycloak ⭐ (开源, 全功能)
  Authentik (现代 Python)
  Zitadel (云原生)
  
互联网 / 大型 (1000+):
  Okta / Auth0 (商业)
  Keycloak + 自研增强

央企 / 信创:
  阿里 IDaaS ⭐
  华为 OneAccess
  永泰 / 安畅
  Keycloak + 国密改造

混合云:
  Azure AD + Keycloak Federation
  Okta + 自建 LDAP

选型决策:
  - 用户规模
  - 合规要求 (等保 / 国密)
  - 预算
  - 现有生态 (微软 / 阿里 / 自研)
```

## 三、HR 是 SoT

```
HR 系统 (Workday / 北森 / SAP / 自建):
  → SCIM out (或 webhook)
  → IdP (Keycloak / IDaaS)
  → 业务应用

入职:
  HR 录入 → SCIM 推送 → IdP 创建 → 应用自动接收

调岗:
  HR 变更 → SCIM 更新 → IdP groups 变 → 应用权限自动调

离职:
  HR 离职 → SCIM 禁用 → 1h 内全应用撤权

关键 SLO:
  ☐ 入职 D-day 全应用可用
  ☐ 离职 1h 撤权 (高敏 5min)
  ☐ 调岗 4h 生效
  ☐ 全链路审计 (HR + SCIM + IdP + 应用)
```

## 四、应用矩阵纪律

```
强制接入 OIDC / SAML:
☐ 代码: GitLab / GitHub / Bitbucket
☐ CI: Jenkins / Argo Workflows / GitHub Actions
☐ CD: ArgoCD / Spinnaker
☐ 监控: Grafana / 夜莺 / Kibana
☐ 日志: Loki / ClickHouse / SLS
☐ 镜像: Harbor / Nexus
☐ 工件: Nexus / JFrog
☐ K8s: --oidc + kubelogin
☐ 数据: Superset / Metabase
☐ AI: MLflow / W&B / KServe
☐ 工单: Jira / ServiceDesk / TAPD
☐ 知识: Confluence / 飞书 / Notion
☐ 网关: Higress / Kong / APISIX
☐ Vault / Bitwarden
☐ SSH: Teleport
☐ 跳板: Teleport / 齐治

禁止:
❌ admin/admin
❌ 共享账号
❌ 本地密码 (生产)
❌ 无 MFA 高敏

例外:
  break-glass account (3 个, 离线 + 双人保管)
```

## 五、MFA 全员

```
分级:
  普通用户:    TOTP (Google Authenticator / 飞书) + Push
  特殊员工:   WebAuthn / Passkey ⭐ + TOTP
  管理员:     WebAuthn 强制 + 硬件 Key (Yubikey)
  高敏操作:   每次 Step-up MFA
  
WebAuthn 优势:
  ✅ 抗钓鱼
  ✅ 无密码
  ✅ 用户体验好 (Touch ID / Face ID)
  
推广路径:
  Phase 1 (3 月): IT/SRE/Admin 强制 WebAuthn
  Phase 2 (6 月): 工程师 + DBA + 安全 强制
  Phase 3 (12 月): 全员 (TOTP 兜底)
```

## 六、K8s OIDC + Workload Identity

```
人工:
☐ kubectl 全部走 --oidc + kubelogin
☐ ~/.kube/config 不存 token
☐ RBAC 接 groups (oidc:developers)
☐ 短期 token (1-8h)
☐ 禁 ServiceAccount Token 长期复用

服务 (Workload):
☐ AWS: IRSA + IAM Role
☐ GCP: Workload Identity
☐ Azure: AD Workload Identity
☐ 通用: Projected Token + Vault K8s Auth
☐ Service Mesh: SPIFFE + Istio mTLS
☐ 禁: 静态 access key 入镜像
```

## 七、Vault 全栈动态化

```
应用:
☐ DB 凭证: dynamic (1h TTL)
☐ Cloud 凭证: dynamic (AWS/Azure/GCP)
☐ SSH 证书: CA signed (1h)
☐ TLS 证书: cert-manager + Vault PKI (90d)
☐ AppRole: 应用专用

人:
☐ Vault OIDC 登录 (Keycloak)
☐ 短期 token (8h)
☐ 审批高敏 secret
☐ Audit 全开 → SIEM

合规:
☐ 加密落盘 (KMS / 国密)
☐ HA 3 副本 + Raft
☐ Snapshot 每天 + 异地
☐ 解封 (Auto-unseal) + KMS
```

## 八、PAM 落地

```
跳板:
☐ Teleport / 齐治 / 行云 一种
☐ 强制 OIDC + MFA + WebAuthn
☐ 会话全录制
☐ JIT 临时权限 (1-8h)
☐ 高敏命令二次审批
☐ Keystroke + Video → SIEM

凭证:
☐ Vault Dynamic
☐ 1h TTL
☐ 禁静态 root / DBA 密码

审计:
☐ 全 SSH / DB / K8s 操作录制
☐ 6mo 保留
☐ 异常告警 (rm -rf / drop / chmod 777)
☐ 季度审计回看 (抽样)
```

## 九、零信任落地路径

```
Phase 1 (基础, 1-3 月):
  ☐ 统一 IdP
  ☐ 全员 MFA
  ☐ oauth2-proxy 内部应用代理
  ☐ Teleport SSH / K8s

Phase 2 (中级, 3-6 月):
  ☐ 设备认证 (MDM 证书)
  ☐ Conditional Access (IP/Geo/时间)
  ☐ Step-up 高敏
  ☐ Vault Dynamic

Phase 3 (高级, 6-12 月):
  ☐ SPIFFE Workload + Istio mTLS
  ☐ Risk-based UEBA
  ☐ ABAC (OPA)
  ☐ B2B 联邦
  ☐ JIT 自服务

Phase 4 (深化, 12+ 月):
  ☐ ReBAC (OpenFGA, 业务复杂)
  ☐ Confidential Computing
  ☐ 国密 + 等保三级 全项
  ☐ 自动化 + 自服务 IDP (Backstage)
```

## 十、IGA 体系

```
权限审查:
☐ 季度: 经理批 + 自动撤销
☐ 月度: 高敏权限
☐ 90d 无活动: 自动撤
☐ 离职: 1h 撤

SoD (Separation of Duties):
☐ 申请 + 审批 ≠ 同人
☐ DBA + Audit ≠ 同人
☐ 财务 + 出纳 ≠ 同人
☐ 开发 + 运维生产 ≠ 同人 (大型)

合规:
☐ 等保三级 + 国密 (中)
☐ SOX (上市)
☐ HIPAA (医疗)
☐ PCI-DSS (金融)
☐ 个保法 / 网安法 (全)

工具:
☐ SailPoint / Saviynt (商业)
☐ Apache Syncope (开源)
☐ 自研 + Keycloak + Workflow
```

## 十一、监控告警

```
指标:
☐ 登录成功率
☐ MFA 启用率
☐ 失败登录 (异常 IP / 多次)
☐ 异地登录
☐ 高敏操作 (root / drop / chmod)
☐ SCIM 同步延迟
☐ Token 续签率
☐ Vault 健康
☐ Service Mesh mTLS 覆盖率

告警:
☐ 单用户 5 次失败 / 10min → 锁定 + 通知
☐ 异地登录 + 无 MFA → 阻断 + 通知
☐ Admin 操作 → 审计实时 + 经理通知
☐ Vault 异常 → on-call
☐ Keycloak 副本 down → page
```

## 十二、Incident SOP

```
P0 (身份系统 down / 大面积):
  RTO < 15 min
  备 IdP / break-glass
  公司公告

P1 (单应用 SSO down):
  RTO < 1h
  本地账号兜底 (临时)
  快速修复

P2 (单用户登录异常):
  RTO < 4h
  on-call 处理

P3 (权限申请慢):
  工作时间

常见 SOP:
  Keycloak 卡死:
    1. 重启副本 (滚动)
    2. PG 健康检查
    3. Infinispan 缓存清理
    
  SCIM 同步失败:
    1. HR webhook 重试
    2. 手动同步
    3. 异常用户单独建
    
  MFA 丢失:
    1. 用户提工单 + 经理批
    2. 经理人脸视频核实
    3. 重置 + 重新注册
    4. 审计记录

  break-glass:
    1. 离线保管 3 个紧急账号
    2. 使用必双人 + 录像
    3. 事后 1d Postmortem
```

## 十三、团队组织

```
身份平台团队 (3-5 人):
  - 平台负责人
  - SSO + IdP 工程师
  - 零信任 + PAM 工程师
  - IGA + 合规
  - 安全审计

接入团队 (每业务 1 人):
  - SSO Champion (各业务部)
  - 推动应用接入
  - 培训
  
合规 (1-2 人):
  - 等保 / 国密 / 备案
  - 季度审计
  - 红蓝对抗参与
```

## 十四、KPI

```
覆盖:
☐ 应用 SSO 接入率 > 95%
☐ MFA 启用率 > 95% (普通) / 100% (Admin)
☐ K8s OIDC 接入率 100%
☐ DB 动态凭证覆盖率 > 80%
☐ SSH CA 覆盖率 100%
☐ Service Mesh mTLS 覆盖率 > 90%

效率:
☐ 入职 D-day 全应用可用率 > 99%
☐ 离职 1h 撤权率 100%
☐ 权限申请 SLA < 4h
☐ MFA 重置 SLA < 1h

合规:
☐ 季度权限审查完成率 100%
☐ 90d 无活动撤权率 100%
☐ 审计 SIEM 完整率 100%
☐ 等保 / 国密 全项达标

安全:
☐ 失败登录告警响应 < 5min
☐ 异常登录处置 < 30min
☐ Break-glass 误用 = 0
☐ 钓鱼演练通过率 > 95%
```

## 十五、国产化路径

```
IdP:        阿里 IDaaS ⭐ / 华为 OneAccess / 永泰 / Keycloak + 国密
目录:        OpenLDAP + AD / 国产 (统一身份)
MFA:        WebAuthn + 国密 USB Key (国密 GM/T)
SSO:        OIDC + 国密 SM2/SM3
SCIM:       北森 HR + 国产 IDaaS
SSH:        齐治 / 行云 / 安畅
PAM:        齐治 / 北信源 / 安畅
零信任:     奇安信 / 360 / 启明 / 阿里云
TLS:        Tongsuo (SM2/SM3/SM4) ⭐
PKI:        CFCA / 自建国密 CA
合规:        等保三级 + 国密 + 个保法 + 备案
信创:        鲲鹏 + openEuler + 麒麟
```

## 十六、典型生产架构

### 16.1 互联网 1000 人工程组织

```
IdP:        Keycloak 3 副本 + PG HA
HR:         北森 → SCIM → Keycloak
联邦:        飞书 + GitHub
应用:        GitLab / Argo / Grafana / Harbor / Vault / Jenkins / Nexus 全 OIDC (35+ 应用)
K8s:        --oidc + kubelogin (生产 / 测试 / DR 3 集群)
工作负载:    SPIRE + Istio Strict mTLS
SSH:        Teleport (Keystroke + Video)
DB:         Vault Dynamic (200+ DB)
MFA:        WebAuthn 90% + TOTP 10%
零信任:     oauth2-proxy + Cloudflare Access
PAM:        Teleport + JIT
ABAC:       OPA (K8s + API Gateway)
审计:        Wazuh + Elastic 6mo
Incident:   RTO < 15min (P0)
```

### 16.2 央企信创

```
IdP:        阿里 IDaaS ⭐ + Keycloak (备)
HR:         自建 + SCIM
联邦:        企业微信 / 钉钉
应用:        Argo / 自研 OA / Grafana 全 OIDC
K8s:        --oidc
SSH:        齐治堡垒机 + 国密
DB:         自研代理 + 国密 SM2/SM4
MFA:        WebAuthn + 国密 USB Key + TOTP
零信任:     奇安信 ZTNA
PAM:        齐治 + 行云
密码学:     Tongsuo (SM2/SM3/SM4)
PKI:        CFCA 国密证书
审计:        SIEM (国产) 6mo
合规:        等保三级 ⭐ + 国密 + 备案
信创:        鲲鹏 + openEuler + 飞腾备选
```

## 十七、推荐栈（最佳实践）

```
IDP:        Keycloak HA ⭐ + 阿里 IDaaS (信创)
联邦:        飞书 / 钉钉 / 企微 + GitHub/Google
SCIM:       北森 / Workday → IdP
K8s:        --oidc + kubelogin + Dex
工作负载:    SPIRE ⭐ + Istio Strict mTLS + IRSA/Projected Token
应用矩阵:    GitLab/Argo/Grafana/Harbor/Vault/Jenkins/Nexus 全 OIDC
SSH:        Teleport ⭐ + 齐治 (信创)
DB:         Vault Dynamic Credentials ⭐
MFA:        WebAuthn ⭐ + TOTP + 国密 USB
ABAC:       OPA on K8s + API Gateway
PAM:        Teleport ⭐ + 齐治 / 北信源 (信创)
IGA:        自研 + Keycloak + Workflow / SailPoint (大型)
零信任:     oauth2-proxy + Cloudflare Access + Teleport
密码学:     Argon2 + Ed25519 + Tongsuo (SM2/SM3/SM4) ⭐
SIEM:       Wazuh + Elastic / 阿里 SLS / 国产
合规:        等保三级 + 国密 + 个保法 + 备案 ⭐
信创:        鲲鹏 + openEuler + Tongsuo + 阿里 IDaaS
```

> 📖 **核心判断**：身份认证最佳实践 = **12 项金标准 + 单一 IdP + HR SoT + 应用矩阵 OIDC 纪律 + MFA 全员 + K8s OIDC + Vault 全栈动态 + PAM 落地 + 零信任 4 阶段 + IGA + 监控 + Incident SOP + 团队 + KPI + 国产化(IDaaS/齐治/Tongsuo) + 等保三级**。能给中型/央企画"Keycloak + 北森 + 飞书 + Teleport + SPIRE + Istio + Vault + WebAuthn + OPA + 国密 + 等保"完整身份平台, 落地 SCIM 自动开撤 + MFA + 零信任 + PAM + IGA + 合规, 就具备身份平台负责人能力。
