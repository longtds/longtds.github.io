# 基础

> 身份认证基础 = **身份/账号/凭证 概念 + 协议(LDAP/Kerberos/SAML/OAuth2/OIDC/JWT) + Keycloak/Authentik 单机 + LDAP 目录服务 + 基础 RBAC + 密码学基础(哈希/盐/HMAC) + MFA + Linux/Web/数据库 接入 SSO 入门**。本章面向初次接触 SSO 与企业身份的工程师。

## 一、身份认证全景

```
身份 (Identity):   员工/服务/设备  唯一 ID
账号 (Account):    身份在系统的实例
凭证 (Credential): 密码/证书/Token
认证 (AuthN):      你是谁
授权 (AuthZ):      你能做啥
审计 (Audit):      你做了啥
```

## 二、协议地图

| 协议 | 场景 | 现状 |
|:---|:---|:---|
| LDAP / LDAPS | 目录服务 (用户/组) | 企业必备 ⭐ |
| Kerberos | Windows AD / Hadoop | 大型企业 |
| SAML 2.0 | Web SSO (老牌, 政企多) | 仍主流 |
| OAuth 2.0 | 授权委托 (第三方登录) | 必备 ⭐ |
| OIDC | OAuth 上的认证 (JWT 携带身份) | 现代主流 ⭐⭐ |
| JWT | 无状态 Token | 必备 ⭐ |
| SCIM 2.0 | 跨系统账号同步 | 大企必修 |
| WebAuthn / Passkey | 无密码 (FIDO2) | 2026 主流 |
| WS-Fed | 老 Microsoft | 渐退 |

## 三、Keycloak 单机

```bash
# Docker
docker run -d --name keycloak -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:25.0 start-dev

# Realm: example  Client: gitlab  Role: developer
# 接入: 客户端配 OIDC issuer = http://kc/realms/example
```

```
核心概念:
  Realm        租户 (隔离)
  Client       受保护应用
  User / Group 用户 / 组
  Role         角色 (Realm / Client 两级)
  Identity Provider  外部接入 (GitHub/Google/LDAP/SAML)
  Federation   联邦 (LDAP/Kerberos 用户来源)
```

## 四、Authentik（轻量替代 Keycloak）

```yaml
# docker-compose
services:
  authentik-server: { image: ghcr.io/goauthentik/server:2025.x, command: server }
  authentik-worker: { image: ghcr.io/goauthentik/server:2025.x, command: worker }
  postgresql: { image: postgres:16 }
  redis: { image: redis:7 }
```

```
对比:
  Keycloak    重 / 全 (Java)   政企首选
  Authentik   轻 / Python 现代  互联网 / 中小
  Zitadel     云原生 + 多租户   新兴
  Casbin      代码级 RBAC      嵌入
```

## 五、LDAP 目录服务

```bash
# OpenLDAP 部署
docker run -d --name openldap -p 389:389 \
  -e LDAP_ORGANISATION="Example" \
  -e LDAP_DOMAIN="example.com" \
  -e LDAP_ADMIN_PASSWORD=admin \
  osixia/openldap:1.5.0

# 查询
ldapsearch -x -H ldap://localhost -D "cn=admin,dc=example,dc=com" -w admin \
  -b "dc=example,dc=com" "(objectClass=person)"
```

```
DIT (Directory Information Tree):
  dc=example,dc=com
    ou=users
      uid=alice
      uid=bob
    ou=groups
      cn=admins
      cn=developers

国产替代:
  阿里 DingDing 企业目录
  企业微信 / 飞书 企业身份
  自研 + OpenLDAP
```

## 六、OAuth 2.0 + OIDC

### 6.1 OAuth 2.0 流程

```
Authorization Code (推荐 Web):
  1. App → /authorize → IDP
  2. 用户登录 + 同意
  3. IDP 回调 code → App
  4. App → /token (code) → IDP
  5. IDP 返 access_token + refresh_token

Client Credentials:
  服务间, 无用户

Device Code:
  CLI / 智能设备
```

### 6.2 OIDC = OAuth + ID Token

```
ID Token (JWT):
  iss     发行方
  sub     用户 ID
  aud     客户端
  exp     过期
  email / name / groups (claim)

JWKS:
  公钥集 /.well-known/jwks.json
```

### 6.3 JWT 必修

```bash
# 解码 (header.payload.sig base64)
echo $JWT | cut -d. -f2 | base64 -d | jq

# 验签 (HS256 或 RS256)
jwt verify --secret $SECRET $JWT
jwt verify --pubkey @pub.pem $JWT
```

```
风险:
  ❌ 无验签 (alg=none 攻击)
  ❌ HS256 + 弱 secret
  ❌ exp 太长 (24h+ 危险)
  ❌ refresh_token 不轮换
```

## 七、MFA 基础

```
TOTP (Time-based OTP):
  Google Authenticator / 阿里 / 飞书
  6 位 / 30s
  
Push (推荐):
  Authy / Duo / 自研 App
  
WebAuthn / Passkey ⭐ (2026 主流):
  无密码 + 硬件密钥 / 手机
  抗钓鱼

短信:
  弱 (SIM swap 攻击)
  不推荐

Keycloak MFA:
  Realm → Authentication → OTP/WebAuthn
```

## 八、基础 RBAC

```
RBAC = Role-Based Access Control
  Subject (User / Group)
  ↓
  Role (admin / dev / viewer)
  ↓
  Permission (read/write/delete)
  ↓
  Resource (project A / DB / file)

K8s RBAC:
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: dev-binding, namespace: dev }
roleRef: { kind: ClusterRole, name: edit, apiGroup: rbac.authorization.k8s.io }
subjects:
  - kind: Group
    name: developers
    apiGroup: rbac.authorization.k8s.io
```

## 九、Linux SSO 接入

```bash
# SSSD + LDAP / Kerberos
yum install sssd sssd-ldap oddjob-mkhomedir
authconfig --enableldap --enableldapauth \
  --ldapserver=ldaps://ldap.example.com \
  --ldapbasedn="dc=example,dc=com" \
  --enablesssd --enablesssdauth --update

# Realmd (AD 加入)
realm join example.com -U Administrator
```

## 十、Web 接入 SSO（Nginx + OIDC）

```nginx
# oauth2-proxy 反代
location /oauth2/ {
  proxy_pass http://oauth2-proxy:4180;
  proxy_set_header X-Real-IP $remote_addr;
}

location / {
  auth_request /oauth2/auth;
  error_page 401 = /oauth2/sign_in;
  auth_request_set $email $upstream_http_x_auth_request_email;
  proxy_set_header X-Email $email;
  proxy_pass http://app;
}
```

```bash
# oauth2-proxy
oauth2-proxy \
  --provider=oidc \
  --oidc-issuer-url=https://kc/realms/example \
  --client-id=app \
  --client-secret=$SECRET \
  --cookie-secret=$COOKIE \
  --email-domain=* \
  --upstream=http://app:8080 \
  --http-address=:4180
```

## 十一、数据库 SSO

```
MySQL:        external auth plugin (LDAP / PAM)
PostgreSQL:   LDAP / Kerberos / cert auth
MongoDB:      LDAP / Kerberos
Vault Dynamic Credentials: 动态短期账号 ⭐

最佳实践:
  尽量不直连 → 走代理 (BastionHost / Vault DB)
  审计 SQL (全量) → SIEM
```

## 十二、密码学基础

```
密码哈希:
  bcrypt / scrypt / Argon2 ⭐
  ❌ MD5 / SHA1 / SHA256 (无盐)

盐 (Salt):
  每用户随机, 防彩虹表

HMAC:
  消息完整 + 来源验证

数字签名:
  非对称 (RSA / ECDSA / Ed25519)
  
密码学库:
  OpenSSL / BoringSSL
  Bouncy Castle (Java)
  Tongsuo (国密) ⭐
```

## 十三、必会工具清单

```
IDP:        Keycloak ⭐ / Authentik / Zitadel
LDAP:        OpenLDAP / 389-ds / FreeIPA
Web 代理:    oauth2-proxy ⭐ / Pomerium / Authelia
K8s OIDC:   kube-apiserver --oidc-* / Dex
Vault:        HashiCorp Vault (动态凭证) ⭐
MFA:        WebAuthn / TOTP / Duo
审计:        SIEM (Wazuh / Elastic / Splunk)
国产:        飞书 / 钉钉 / 企业微信 / 阿里 IDaaS
```

## 十四、入门 20 题

```
1.  AuthN vs AuthZ
2.  LDAP DIT 结构
3.  Kerberos KDC + Ticket
4.  SAML vs OIDC 区别
5.  OAuth 2.0 4 种 grant
6.  JWT header / payload / signature
7.  ID Token vs Access Token
8.  JWKS 用途
9.  Refresh Token 轮换
10. MFA 4 种类型
11. WebAuthn / Passkey 原理
12. RBAC 4 元素
13. K8s RoleBinding vs ClusterRoleBinding
14. oauth2-proxy 工作流
15. PAM 模块 (Linux)
16. SCIM 协议
17. bcrypt vs Argon2
18. Salt + Pepper
19. JWT 安全风险 5 个
20. Keycloak Realm / Client / Role
```

## 十五、推荐栈

```
IDP:        Keycloak ⭐ (政企) / Authentik (互联网)
LDAP:        OpenLDAP + sssd
Web 代理:    oauth2-proxy + Nginx
K8s OIDC:   kube-apiserver --oidc + Dex
MFA:        WebAuthn + TOTP
Vault:        HashiCorp Vault (动态 DB)
审计:        Wazuh + Elastic (SIEM)
密码学:     Argon2 + Ed25519 + Tongsuo (国密)
国产:        飞书 / 钉钉 / IDaaS 一种
```

> 📖 **核心判断**：身份认证基础 = **协议(LDAP/OIDC/OAuth/JWT/SAML) + Keycloak/Authentik + LDAP 目录 + RBAC + MFA(WebAuthn/TOTP) + Linux SSSD + Web oauth2-proxy + 数据库代理 + 密码学(Argon2/Ed25519)**。能跑通"Keycloak Realm + LDAP 用户 + OIDC App + WebAuthn MFA + RBAC + 审计"全链路, 就具备身份认证入门能力。
