# Keycloak

## 部署

```bash
# K8s Helm 部署
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install keycloak bitnami/keycloak -n sso \
  --set auth.adminUser=admin \
  --set auth.adminPassword=<password> \
  --set production=true \
  --set proxy=edge \
  --set postgresql.architecture=replication
```

## 核心概念

| 概念 | 说明 |
|:---|:---|
| Realm | 安全域，逻辑隔离租户 |
| Client | 接入 SSO 的应用 |
| User | 用户 |
| Group | 用户组 |
| Role | 角色 |
| Client Scope | 客户端权限范围 |

## 各系统 OIDC 配置速查

```bash
# GitLab
gitlab_rails['omniauth_providers'] = [{
  name: "openid_connect",
  label: "SSO",
  args: {
    issuer: "https://sso.company.com/auth/realms/company",
    client_options: {
      identifier: "gitlab",
      secret: "<secret>",
      redirect_uri: "https://gitlab.company.com/users/auth/openid_connect/callback"
    }
  }
}]

# Grafana（generic_oauth）
[auth.generic_oauth]
enabled = true
name = SSO
client_id = grafana
client_secret = <secret>
auth_url = https://sso.company.com/auth/realms/company/protocol/openid-connect/auth
token_url = https://sso.company.com/auth/realms/company/protocol/openid-connect/token
api_url = https://sso.company.com/auth/realms/company/protocol/openid-connect/userinfo
```
