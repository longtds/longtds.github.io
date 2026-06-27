# 高级

> 身份认证高级 = **统一身份平台架构 + 零信任(BeyondCorp/SDP/SASE) + 设备身份+证书自动签发(SPIFFE/SPIRE/Cert-manager) + Service Mesh mTLS(Istio/Linkerd) + Workload Identity(AWS IRSA/GCP WI/K8s Projected Token) + Token Exchange + Step-up Authentication + Risk-based Auth(UEBA) + ABAC(OPA/Cedar) + 联邦租户(B2B/B2C) + IGA(身份治理+合规审查) + PAM(特权管理 Teleport/CyberArk) + Confidential Computing + 国密一体化 + 等保三级 IAM**。本章面向身份平台架构师 / 零信任 / 安全负责人。

## 一、统一身份平台架构

```
身份源 (SoT):
  HR (Workday / 北森 / SAP)
    ↓ SCIM
  IdP 主体 (Keycloak / Okta / Azure AD)
    ↓ SCIM / OIDC / SAML
  目录 (LDAP / AD / 自研)

认证层:
  Web Apps (OIDC / SAML)
  CLI / API (OAuth Device / Client Credentials)
  K8s (OIDC + Projected Token)
  服务 (mTLS / SPIFFE)
  SSH (CA 证书)
  DB / Vault (动态凭证)

授权层:
  RBAC (角色)
  ABAC (属性 + OPA / Cedar)
  ReBAC (关系, Zanzibar / OpenFGA) ⭐

设备 + 上下文:
  Device Trust (UEM / MDM)
  IP / Geo / Time / 风险评分

PAM (特权):
  Teleport / CyberArk
  会话录制 + 审批

审计 + 治理 (IGA):
  审计日志 (SIEM 6mo)
  权限矩阵 (季度审查)
  分离职责 (SoD)
  合规 (SOX / 等保 / 个保法)
```

## 二、零信任 (BeyondCorp / SDP / SASE)

```
BeyondCorp (Google 提出):
  - 永不信任, 持续验证
  - 无 VPN, 设备 + 身份 + 上下文
  - 应用细粒度策略
  - 网络只是介质

SDP (Software-Defined Perimeter):
  - 默认拒绝
  - 应用先认证后可见
  - Cloud Security Alliance 标准

SASE (Gartner):
  - SD-WAN + 零信任 + SWG + CASB + ZTNA
  - 边缘 + 云一体

落地:
  Cloudflare Access ⭐ (商业最快)
  Tailscale (WireGuard + IdP) ⭐
  Pomerium / Authelia (开源)
  Teleport (统一接入)
  Zscaler / Netskope / Palo Alto Prisma (商业大厂)
  国产: 奇安信 / 360 / 启明 / 阿里云零信任

工程化:
  设备认证 (MDM 证书)
  身份认证 (Keycloak OIDC)
  上下文 (IP/Geo/时间/UEBA)
  策略引擎 (OPA / Cedar / 自研)
  Just-in-Time 临时权限
```

## 三、SPIFFE / SPIRE 工作负载身份

```
SPIFFE:
  Secure Production Identity Framework For Everyone
  规范 + 标准化 workload 身份
  
SPIRE:
  Reference implementation
  Server + Agent + Workload API
  
SVID:
  X.509 SVID (mTLS)
  JWT SVID (HTTP)
  Trust Domain: spiffe://example.com

例:
  spiffe://example.com/ns/prod/sa/api
  spiffe://example.com/ns/prod/sa/db

K8s 集成:
  - SPIRE Server (Central)
  - SPIRE Agent (DaemonSet)
  - Workload (Annotation)
  - Istio / Linkerd 自动 mTLS

工具:
  SPIRE ⭐
  Istio + SPIRE Federation
  Tetrate Service Bridge
  cert-manager (X.509)
```

## 四、Service Mesh mTLS

```yaml
# Istio Strict mTLS (推荐)
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata: { name: default, namespace: istio-system }
spec:
  mtls: { mode: STRICT }

# AuthorizationPolicy (服务间)
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata: { name: api-allow, namespace: prod }
spec:
  selector: { matchLabels: { app: api } }
  rules:
    - from:
        - source: { principals: ["cluster.local/ns/prod/sa/gateway"] }
      to: [{ operation: { methods: [GET, POST] } }]
```

```
对比:
  Istio       全功能, 重
  Linkerd     轻, mTLS 默认
  Cilium      eBPF + 网格 + L7
  Consul      多云

价值:
  - 服务间默认加密
  - 工作负载身份验证 (SPIFFE)
  - 细粒度策略 (L7)
  - 审计
```

## 五、Workload Identity（云）

```
AWS IRSA (IAM Roles for Service Accounts):
  - OIDC IdP (EKS 集群) → IAM Role
  - Pod ServiceAccount → AWS API
  - 无 access key

GCP Workload Identity:
  - K8s SA ↔ GCP SA 映射
  
Azure AD Workload Identity:
  - AKS Pod → Azure AD Token

K8s Projected Token (通用):
  - apiserver 签 JWT
  - Audience + Expiration
  - Pod 内挂载

Vault Kubernetes Auth:
  - SA Token → Vault Role → 动态凭证
```

## 六、Token Exchange + 委托

```
OAuth 2.0 Token Exchange (RFC 8693):
  场景: Service A 调 Service B 代用户操作
  
流程:
  Service A 持用户 access_token (audience=A)
  → IdP /token (grant=token-exchange)
  → IdP 返新 token (audience=B, sub=用户, act=Service A)
  → 调 B

价值:
  - 跨服务委托
  - 保留用户身份
  - 减少凭证传递

Keycloak 支持 Token Exchange (feature flag)
```

## 七、Step-up Authentication

```
场景:
  - 用户登录后用 SSO 进入
  - 访问敏感操作 (转账 / 管理员 / 删除)
  - 要求二次 MFA

实现:
  acr_values=high
  → 拒绝 + 重定向 → MFA → 提升 token claim
  
Keycloak:
  Authentication Flow → 条件分支
  Browser Flow → 检查 amr / acr
  
合规:
  PCI-DSS / 等保 / 银保监 要求
```

## 八、Risk-based Auth (UEBA)

```
信号:
  - IP 异常 (异地)
  - 设备 新增
  - 时间 异常 (凌晨)
  - 行为 (操作频次)
  - Tor / VPN
  - 失败次数

策略:
  低风险: 透明
  中风险: 加 MFA
  高风险: 拒绝 + 通知
  
工具:
  Microsoft Conditional Access ⭐
  Okta Adaptive MFA
  Azure AD Identity Protection
  自研 + UEBA (规则 + ML)
  阿里云 / 国产 IDaaS 自带
```

## 九、ABAC 与 OPA / Cedar

```
RBAC vs ABAC:
  RBAC: 角色 → 权限
  ABAC: 属性 + 规则 → 决策
  
OPA (Open Policy Agent) ⭐:
  Rego 语言
  K8s admission / API gateway / Microservices
  
package authz
default allow = false
allow {
  input.user.role == "admin"
}
allow {
  input.user.team == input.resource.team
  input.action == "read"
}
allow {
  input.user.role == "developer"
  input.resource.env == "dev"
}

# Cedar (AWS 开源) ⭐:
  类似 OPA, AWS Verified Permissions 用
  
# OpenFGA / Zanzibar (Google) ⭐:
  ReBAC (关系-based)
  适合复杂权限 (文档 / 资源关系)
```

## 十、联邦租户 (B2B / B2C)

```
B2B (企业 → 客户):
  - 客户带自家 IdP (SAML / OIDC)
  - 你的 Realm 接受外部 IdP
  - 多租户隔离
  - SCIM 同步

B2C (大量个人用户):
  - 注册 + 邮件验证
  - 社交登录 (GitHub / 微信 / 飞书)
  - 自助密码重置
  - 设备绑定

Keycloak Realm 一个 / 客户:
  Authentik / Zitadel 同
  Auth0 / Okta 商业 B2C 强
```

## 十一、IGA（Identity Governance & Administration）

```
权限审查 (Access Review):
  - 季度审查 (经理批)
  - 自动撤销 (90d 无活动)
  - 高敏权限月度

分离职责 (SoD):
  - 同一人不能 "申请 + 审批"
  - 财务 + 出纳 隔离
  - DBA + Audit Log 隔离

合规:
  - SOX
  - 等保三级 + 国密
  - 个保法 + 网安法
  - HIPAA (医疗)
  - PCI-DSS (金融)

工具:
  SailPoint / Saviynt (商业)
  Apache Syncope (开源)
  自研 + Keycloak + Workflow
  国产: 永泰 / 安畅 / 阿里 IDaaS
```

## 十二、PAM（特权访问管理）

```
PAM = Privileged Access Management

要素:
  - 跳板机 + 会话录制
  - JIT (Just-In-Time) 临时权限
  - 审批流
  - 凭证轮换 (DB / SSH 密码)
  - 审计 (Keystroke / Video)

工具:
  Teleport ⭐ (开源 + 商业, SSH / DB / K8s / Web 一体)
  CyberArk (商业领导者)
  HashiCorp Vault (动态凭证)
  BeyondTrust
  国产: 阿里堡垒机 / 齐治 / 行云 / 安畅

工程化:
  入口: 跳板机 (Teleport)
  身份: OIDC + MFA
  授权: JIT + 审批
  会话: 全录制 + 审计
  凭证: Vault 动态
```

## 十三、Confidential Computing + 身份

```
场景:
  - SaaS 客户不信任你的运维
  - 国家级机密
  - 多方计算

技术:
  - Intel SGX / TDX
  - AMD SEV / SEV-SNP
  - ARM CCA
  - 海光 CSV
  - Confidential Containers (Kata-cc)
  
身份场景:
  - Attestation (远程证明)
  - 凭证只下发到可信硬件
  - Root of Trust + 国密 SM 系列
  - 模型加密 (LLM 在 TEE)
```

## 十四、国密一体化

```
TLS:
  TLCP / TLS 1.3 + SM2/SM3/SM4
  Tongsuo (BabaSSL) ⭐
  
Token:
  JWT signed with SM2 / SM9
  自研 / 国产 IdP 支持

PKI:
  CFCA 国密证书
  自建 CA + SM2

合规:
  等保三级 必要
  金融行业强制
  国央企强制
```

## 十五、等保三级 IAM 要点

```
身份鉴别 (a):
  ☐ 唯一标识 + 鉴别信息复杂
  ☐ MFA (远程 + 高敏)
  ☐ 失败锁定 + 超时
  ☐ 双因素 国密

访问控制 (b):
  ☐ 主体客体 标识 + 安全标记
  ☐ 强制访问控制 (MAC)
  ☐ 最小授权 + 分离
  ☐ 重要操作 双重批

安全审计 (c):
  ☐ 全用户行为审计
  ☐ 6 个月保留
  ☐ 集中 SIEM
  ☐ 审计员独立
  ☐ 防篡改

可信验证 (d):
  ☐ 启动 + 运行 完整性
  ☐ 国密 TPM / TCM
```

## 十六、典型生产架构

### 16.1 互联网中型

```
IdP:        Keycloak 3 副本 + PG HA
联邦:        飞书 / GitHub / Google
SCIM:       北森 HR → Keycloak
K8s:        --oidc + kubelogin
应用:        GitLab/Argo/Grafana/Harbor/Vault SSO
SSH:        Teleport
DB:         Vault Dynamic
MFA:        WebAuthn + TOTP
零信任:     oauth2-proxy + 设备策略
ABAC:       OPA on K8s
PAM:        Teleport
审计:        SIEM (Wazuh + Elastic)
```

### 16.2 央企信创

```
IdP:        阿里 IDaaS / 自研 + Keycloak ⭐
目录:        AD + LDAP
SCIM:       HR → IDaaS (定制)
联邦:        企业微信 / 钉钉 / 飞书
K8s:        --oidc + kubelogin
应用:        GitLab/Argo/Grafana 全 OIDC
SSH:        齐治堡垒机 + 国密
DB:         自研代理 + Vault 国密化
MFA:        WebAuthn + TOTP + 国密 USB Key
PAM:        齐治 / 安畅
零信任:     奇安信 / 360
密码学:     Tongsuo (SM2/SM3/SM4)
合规:        等保三级 + 备案
信创:        鲲鹏 + openEuler + Keycloak
```

## 十七、Checklist（高级）

```
平台:
☐ 统一 IdP (Keycloak HA)
☐ 多 Realm 多租户
☐ SCIM 自动开账 (HR)
☐ 审计 SIEM 6mo

零信任:
☐ 设备 + 身份 + 上下文
☐ oauth2-proxy / Pomerium / Teleport
☐ Just-In-Time 权限
☐ Step-up 高敏操作

工作负载身份:
☐ SPIFFE / SPIRE
☐ Service Mesh mTLS (Istio / Linkerd)
☐ Workload Identity (IRSA / WI / Projected Token)
☐ Vault Kubernetes Auth

授权:
☐ RBAC (基础)
☐ ABAC (OPA / Cedar)
☐ ReBAC (OpenFGA, 复杂)
☐ Token Exchange (委托)

设备 + 风险:
☐ MDM / UEM (Jamf / Intune)
☐ Risk-based MFA (UEBA)
☐ Conditional Access

PAM:
☐ Teleport / CyberArk / 齐治
☐ JIT + 审批 + 录制
☐ Vault 动态凭证

IGA:
☐ 季度权限审查
☐ SoD (分离职责)
☐ 90d 无活动撤权
☐ SOX / 等保 合规

联邦:
☐ B2B 客户 IdP (SAML/OIDC)
☐ B2C 社交 + 自服务

国密 + 信创:
☐ Tongsuo (SM2/SM3/SM4)
☐ 国密 USB Key MFA
☐ CFCA 证书
☐ 等保三级 IAM 全项

Confidential:
☐ Kata-cc + TEE
☐ Attestation 凭证下发

国产平台:
☐ 阿里 IDaaS / 华为 OneAccess / 永泰
☐ 齐治 / 行云 PAM
☐ 奇安信 / 360 零信任
```

## 十八、推荐栈（高级）

```
IDP:        Keycloak HA ⭐ + Authentik (轻)
联邦:        飞书 / 钉钉 / 企微 OIDC + GitHub/Google
SCIM:       北森 / Workday → IdP
K8s:        --oidc + Dex + kubelogin
工作负载:    SPIRE ⭐ + Istio Strict mTLS + IRSA/Projected Token
应用:        GitLab/Argo/Grafana/Harbor/Vault/Jenkins/MinIO/Nexus 全 OIDC
SSH:        Teleport ⭐ / 齐治
DB:         Vault Dynamic Credentials
MFA:        WebAuthn + TOTP + 国密 USB
ABAC:       OPA on K8s + API Gateway
PAM:        Teleport / 齐治 / CyberArk
IGA:        自研 + Keycloak + Workflow
零信任:     oauth2-proxy + Cloudflare Access + Teleport
密码学:     Argon2 + Ed25519 + Tongsuo (SM2/SM3/SM4)
SIEM:       Wazuh + Elastic / 阿里 SLS / 国产
信创:        鲲鹏 + openEuler + Tongsuo + 阿里 IDaaS
合规:        等保三级 + 国密 + 个保法 + 备案
```

> 📖 **核心判断**：身份认证高级 = **统一身份平台(IdP + LDAP + SCIM + 审计) + 零信任(设备+身份+上下文+JIT) + SPIFFE/SPIRE Workload + Service Mesh mTLS + Vault Dynamic + Token Exchange + Step-up + Risk-based + ABAC(OPA/Cedar) + ReBAC + IGA(权限审查+SoD) + PAM(Teleport/齐治) + Confidential Computing + 国密+等保**。能给央企画"Keycloak HA + 阿里 IDaaS + AD + 飞书 + SPIRE + Istio mTLS + Teleport + Vault + 国密 + 等保三级"完整身份平台, 落地零信任 / IGA / PAM, 就具备身份平台架构师能力。
