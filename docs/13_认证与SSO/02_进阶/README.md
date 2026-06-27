# 进阶

> 身份认证进阶 = **Keycloak/Authentik 生产化(HA+PostgreSQL+Cluster) + 多 Realm 多租户 + IdP 联邦(LDAP/AD/SAML/GitHub) + SCIM 自动开账 + K8s OIDC 接入 + GitLab/Argo/Grafana/Harbor 应用对接 + ssh-CA 证书登录 + Vault 动态凭证 + WebAuthn/Passkey 生产 + 审计日志 + 国产对接(钉钉/飞书/企微/IDaaS)**。本章面向独立运维 SSO 平台 + 接入企业应用矩阵的工程师。

## 一、Keycloak 生产化

### 1.1 HA 拓扑

```yaml
# Keycloak Operator + PostgreSQL HA
apiVersion: k8s.keycloak.org/v2alpha1
kind: Keycloak
metadata: { name: kc, namespace: iam }
spec:
  instances: 3
  hostname: { hostname: sso.example.com }
  http: { tlsSecret: sso-tls }
  db:
    vendor: postgres
    host: pg-cluster
    database: keycloak
    usernameSecret: { name: pg-secret, key: user }
    passwordSecret: { name: pg-secret, key: password }
    poolMinSize: 10
    poolMaxSize: 50
  features:
    enabled: [token-exchange, admin-fine-grained-authz, declarative-user-profile]
  proxy: { headers: xforwarded }
  ingress: { enabled: true, className: nginx }
```

```
关键:
☐ 3 副本 + Sticky Session / Distributed Session
☐ PostgreSQL HA (Patroni)
☐ Realm 缓存 (Infinispan)
☐ JGroups 跨副本同步
☐ Theme 定制 (品牌)
☐ TLS + HSTS
```

### 1.2 多 Realm 多租户

```
策略 1: 单 Realm 共享 + Client 分租
  - 简单, 但用户冲突
  
策略 2: 每租户 1 Realm ⭐
  - 隔离强
  - Master Realm 管理
  - 适合 SaaS / 多业务

策略 3: 联邦 IdP
  - Master Realm + 外部 Realm
  - 适合集团 / 子公司
```

## 二、IdP 联邦

### 2.1 LDAP / AD Federation

```
Keycloak Realm → User Federation → LDAP/AD
  Connection URL: ldaps://ad.example.com:636
  Users DN: ou=users,dc=example,dc=com
  Bind Type: simple
  Bind DN: cn=svc,ou=svc,dc=example,dc=com
  Edit Mode: READ_ONLY (推荐)
  Sync: periodic full sync (每周)

特性:
  - LDAP 为 SoT (Source of Truth)
  - Keycloak 缓存 + Provider
  - 密码本地或转 LDAP
```

### 2.2 SAML / OIDC 外部 IdP

```
Realm → Identity Providers
  - GitHub / GitLab (OAuth)
  - Google / Microsoft (OIDC)
  - 飞书 / 钉钉 / 企微 (OIDC ⭐)
  - Azure AD / Okta (SAML)
  - 自建 IdP

国产对接:
  飞书 OIDC: 
    issuer = https://open.feishu.cn
    client_id / client_secret 飞书后台获取
  钉钉 OAuth: 自定义协议
  企业微信 OAuth: 自定义协议
```

## 三、SCIM 自动开账

```
SCIM 2.0 (System for Cross-domain Identity Management):
  - 标准化 用户 / 组 CRUD API
  - 主流 IdP 支持 (Okta / Azure AD / Keycloak)
  - 自动开账 + 撤账

场景:
  HR 系统 → SCIM → Keycloak → 业务应用
  入职自动开 / 离职自动撤

实现:
  Keycloak: User Storage SPI
  Authentik: 内置 SCIM 出站 ⭐
  Casdoor: 内置 SCIM
  自研: scim2 库
```

## 四、K8s OIDC 接入

```yaml
# kube-apiserver flags
--oidc-issuer-url=https://sso.example.com/realms/example
--oidc-client-id=k8s
--oidc-username-claim=preferred_username
--oidc-username-prefix="oidc:"
--oidc-groups-claim=groups
--oidc-groups-prefix="oidc:"

# RBAC
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata: { name: developers }
roleRef: { kind: ClusterRole, name: edit, apiGroup: rbac.authorization.k8s.io }
subjects:
  - kind: Group
    name: "oidc:developers"
    apiGroup: rbac.authorization.k8s.io
```

```bash
# kubectl OIDC login (kubelogin)
kubectl oidc-login setup \
  --oidc-issuer-url=https://sso/realms/example \
  --oidc-client-id=k8s

kubectl config set-credentials oidc \
  --exec-api-version=client.authentication.k8s.io/v1beta1 \
  --exec-command=kubectl --exec-arg=oidc-login --exec-arg=get-token \
  --exec-arg=--oidc-issuer-url=https://sso/realms/example \
  --exec-arg=--oidc-client-id=k8s
```

## 五、应用矩阵 SSO 对接

### 5.1 GitLab

```yaml
# /etc/gitlab/gitlab.rb
gitlab_rails['omniauth_enabled'] = true
gitlab_rails['omniauth_providers'] = [{
  name: 'openid_connect',
  label: 'Keycloak',
  args: {
    name: 'openid_connect',
    scope: ['openid','profile','email'],
    response_type: 'code',
    issuer: 'https://sso/realms/example',
    discovery: true,
    client_auth_method: 'query',
    uid_field: 'preferred_username',
    client_options: {
      identifier: 'gitlab',
      secret: '*****',
      redirect_uri: 'https://gitlab.example.com/users/auth/openid_connect/callback'
    }
  }
}]
```

### 5.2 ArgoCD

```yaml
# argocd-cm
oidc.config: |
  name: Keycloak
  issuer: https://sso/realms/example
  clientID: argocd
  clientSecret: $oidc.keycloak.clientSecret
  requestedScopes: ["openid","profile","email","groups"]
  requestedIDTokenClaims: { groups: { essential: true } }

# argocd-rbac-cm
policy.default: role:readonly
policy.csv: |
  g, argocd-admins, role:admin
  g, developers, role:dev
```

### 5.3 Grafana

```ini
[auth.generic_oauth]
enabled = true
name = Keycloak
client_id = grafana
client_secret = ***
scopes = openid profile email groups
auth_url = https://sso/realms/example/protocol/openid-connect/auth
token_url = https://sso/realms/example/protocol/openid-connect/token
api_url = https://sso/realms/example/protocol/openid-connect/userinfo
role_attribute_path = contains(groups[*], 'admins') && 'Admin' || 'Viewer'
```

### 5.4 Harbor

```
Harbor Admin → Configuration → Authentication Mode: OIDC
  Provider Name: Keycloak
  OIDC Endpoint: https://sso/realms/example
  Client ID: harbor
  Client Secret: ***
  Scope: openid,profile,email
  Group Claim: groups
```

### 5.5 Jenkins / GitLab Runner / Vault / MinIO / Nexus

```
全部支持 OIDC, 配置类似
关键: client_id / client_secret / groups claim → 角色映射
```

## 六、SSH CA 证书登录

```bash
# 1. 生成 CA
ssh-keygen -t ed25519 -f /etc/ssh/ca

# 2. 服务器信任 CA
echo "TrustedUserCAKeys /etc/ssh/ca.pub" >> /etc/ssh/sshd_config
systemctl restart sshd

# 3. 用户拿 SSO 登录 → 颁发 SSH 证书 (短期)
ssh-keygen -s /etc/ssh/ca -I alice -n alice -V +1h -z 1 user.pub

# 4. 用户登录
ssh -i user -i user-cert.pub server
```

```
工具:
  HashiCorp Vault SSH Secret Engine ⭐
  Teleport ⭐ (SSH + DB + K8s + Web 跳板)
  smallstep ⭐
  自研 (CA + Webhook)

价值:
  - 无静态 SSH key
  - 短期凭证 (1-24h)
  - 审计 (cert ID + 用户)
  - 撤销集中 (CRL)
```

## 七、Vault 动态凭证

```bash
# DB 动态凭证
vault secrets enable database
vault write database/config/mysql \
  plugin_name=mysql-database-plugin \
  connection_url="{{username}}:{{password}}@tcp(mysql:3306)/" \
  allowed_roles=app

vault write database/roles/app \
  db_name=mysql \
  creation_statements="CREATE USER '{{name}}'@'%' IDENTIFIED BY '{{password}}'; GRANT SELECT ON app.* TO '{{name}}'@'%';" \
  default_ttl=1h max_ttl=24h

# App 拿凭证
vault read database/creds/app
# → 临时用户 + 密码 (1h 过期)
```

```
价值:
  - 无静态 DB 密码
  - 每次请求拿短期凭证
  - 审计 (谁拿了什么)
  - 自动回收
```

## 八、WebAuthn / Passkey 生产

```
Keycloak Realm → Authentication → WebAuthn:
  - Required Actions: webauthn-register
  - Browser Flow: 加 WebAuthn Authenticator
  
用户:
  1. 第一次登录 → 注册 Passkey (Touch ID / Yubikey)
  2. 后续 → 仅 Passkey 即可
  
适合:
  - 高安全 (内部员工 / 管理员)
  - 抗钓鱼 (Passkey 绑定 origin)
  - 无密码体验
```

## 九、审计日志

```
Keycloak Events:
  - Login Events (登录 / 失败)
  - Admin Events (Realm / Client 变更)
  → Event Listener SPI → Kafka → SIEM

ELK / Wazuh / Splunk:
  集中存 6 个月 (合规)
  实时告警 (异常 IP / 多次失败 / 异地登录)
  
关联:
  K8s audit + GitLab audit + Vault audit + Keycloak events
  → SIEM 统一关联
```

## 十、国产 IdP 对接

```
飞书 (Lark):
  - OAuth 2.0 + 自定义协议
  - 企业管理后台创建应用
  - issuer / client_id / secret 配 Keycloak IdP

钉钉:
  - DingTalk OAuth 2.0
  - 扫码登录 Web
  - SCIM 离线同步

企业微信:
  - WeWork OAuth
  - 通讯录同步 → Keycloak Group

阿里 IDaaS / 华为 OneAccess / 腾讯 IDaaS / 永泰 (国产 SaaS):
  - 商业 IdP, 适合大企业
  - 一站式 SSO + MFA + Audit + SCIM
```

## 十一、零信任接入（中级）

```
理念:
  - 永不信任, 持续验证
  - 设备 + 身份 + 上下文
  - 最小权限
  - 微隔离

工具:
  Cloudflare Access / Tailscale ⭐
  Pomerium / Teleport
  Authelia + ForwardAuth
  Zscaler / Netskope (商业)
  
基本接入:
  oauth2-proxy + Keycloak + 设备策略
```

## 十二、Checklist（进阶）

```
IDP:
☐ Keycloak 3 副本 + PG HA
☐ Theme + TLS
☐ 多 Realm 隔离

联邦:
☐ LDAP / AD
☐ 飞书/钉钉/企微 OIDC
☐ GitHub/Google (互联网员工)

K8s:
☐ apiserver --oidc + Dex / 直接
☐ kubelogin 客户端
☐ RBAC 接 groups

应用矩阵:
☐ GitLab / ArgoCD / Grafana / Harbor / Vault / Jenkins / Nexus / MinIO
☐ 全 OIDC + groups claim → role mapping

SSH:
☐ SSH CA + Vault SSH / Teleport
☐ 1h 短期证书
☐ 审计 SSH

DB:
☐ Vault Dynamic Credentials
☐ 1h TTL
☐ 无静态 DB 密码

MFA:
☐ WebAuthn / Passkey (高敏)
☐ TOTP (基础)
☐ Push (备选)

SCIM:
☐ HR → IdP
☐ 自动开 / 撤
☐ 离职 1h 内撤权

审计:
☐ Events → Kafka → SIEM
☐ 6 个月保留
☐ 异常登录告警

国产:
☐ 飞书 / 钉钉 / 企微 OIDC
☐ 阿里 IDaaS / 华为 OneAccess (大企)

零信任 (起步):
☐ oauth2-proxy + Keycloak + 设备检查
```

## 十三、推荐栈（进阶）

```
IDP:        Keycloak ⭐ (3 副本 + PG HA)
LDAP:        OpenLDAP / 389-ds / Windows AD
Web 代理:    oauth2-proxy ⭐ + Pomerium
K8s:        --oidc + Dex + kubelogin
SSH:        Vault SSH ⭐ / Teleport
DB:         Vault Dynamic Credentials
MFA:        WebAuthn + TOTP + Push
SCIM:       Authentik 出站 / 自研
审计:        Wazuh + Elastic 6mo
国产:        飞书 / 钉钉 / 企微 OIDC + 阿里 IDaaS
零信任:     oauth2-proxy + Keycloak 起步
密码学:     Argon2 + Ed25519 + Tongsuo (国密)
```

> 📖 **核心判断**：身份认证进阶 = **Keycloak HA + 多 Realm + LDAP/AD/飞书/钉钉/企微 联邦 + SCIM 自动开账 + K8s OIDC + 应用矩阵(GitLab/Argo/Grafana/Harbor/Vault) + SSH CA + DB 动态凭证 + WebAuthn + 审计 SIEM + 国产 IdP**。能独立给 100+ 人工程组织搭"Keycloak + LDAP + 飞书 + 10+ 应用 SSO + WebAuthn MFA + Vault 动态凭证 + SCIM + SIEM 审计"完整体系, 就具备身份平台工程师能力。
