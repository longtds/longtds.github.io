# 企业认证体系

## LDAP/AD 集成

Keycloak 可以通过 LDAP 对接企业 AD/OpenLDAP，将用户数据同步到 Keycloak。

```bash
# Keycloak 中配置 LDAP 同步
# 1. 添加 User Federation → LDAP
# 2. 配置连接参数
# 3. 配置同步策略（定时同步/实时同步）
```

## 员工生命周期管理

| 阶段 | 动作 |
|:---|:---|
| 入职 | Keycloak 创建账号 → 自动同步到 GitLab/Jenkins/Grafana 等 |
| 转岗 | 调整用户组和角色权限 |
| 离职 | Keycloak 禁用账号 → 所有系统同时失效 |

## MFA 配置

Keycloak 支持 TOTP（基于时间的一次性密码）和 WebAuthn（硬件密钥）作为多因素认证。
