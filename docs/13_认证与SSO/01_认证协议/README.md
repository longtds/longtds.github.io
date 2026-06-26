# 认证协议

## OAuth 2.0

OAuth 2.0 是授权框架，定义了四种授权模式。

| 模式 | 场景 | 安全性 |
|:---|:---|:---:|
| 授权码（Authorization Code） | Web 应用 | 高 |
| 隐式（Implicit） | SPA（已不推荐） | 中 |
| 密码（Password） | 信任应用 | 低 |
| 客户端凭证（Client Credentials） | 服务间通信 | 高 |

## OpenID Connect（OIDC）

OIDC 在 OAuth 2.0 上增加身份认证层，是目前 SSO 的主流方案。

## SAML

基于 XML 的旧式 SSO 协议，仍在企业中广泛使用。

## LDAP

轻量级目录访问协议，用户信息的标准存储方式。
