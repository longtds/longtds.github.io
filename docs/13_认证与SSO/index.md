# 13. 认证与 SSO

> 身份认证 = 企业入口。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦 Keycloak/Authentik + LDAP/AD + OIDC/SAML/OAuth/JWT + Vault Dynamic + Teleport PAM + SPIFFE Workload + WebAuthn/Passkey + OPA/OpenFGA + 国密 + 等保 12 大主线。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入门 SSO | 协议(LDAP/SAML/OAuth/OIDC/JWT) + Keycloak/Authentik 单机 + LDAP + RBAC + MFA + Linux SSSD + Web oauth2-proxy + 密码学 + 20 题 |
| [02_进阶](02_进阶/README.md) | 维护 SSO 平台 | Keycloak HA + 多 Realm + IdP 联邦(LDAP/AD/飞书/钉钉) + SCIM + K8s OIDC + 应用矩阵(GitLab/Argo/Grafana/Harbor) + SSH CA + Vault Dynamic + WebAuthn + 审计 SIEM |
| [03_高级](03_高级/README.md) | 身份平台架构师 | 统一身份平台 + 零信任(BeyondCorp/SDP/SASE) + SPIFFE/SPIRE + Service Mesh mTLS + Workload Identity + Token Exchange + Step-up + UEBA + ABAC(OPA/Cedar) + ReBAC + IGA + PAM + Confidential + 国密 + 等保 |
| [04_最佳实践](04_最佳实践/README.md) | 平台负责人 | 12 项金标准 + 单一 IdP + HR SoT + 应用矩阵纪律 + MFA 全员 + K8s OIDC + Vault 全栈 + PAM 落地 + 零信任 4 阶段 + IGA + KPI + Incident SOP + 国产化 + 等保三级 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | Passkey 取代密码 + 零信任主流 + SPIFFE K8s 默认 + DID/VC + Agent 身份 + Token Exchange + UEBA + ReBAC + 国密 + Sovereign Identity + AI 反钓鱼 + 20 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
  └─ 01_基础: 协议 + Keycloak + LDAP + WebAuthn + 20 题

进阶（3-12 月）
  └─ 02_进阶: HA + 多 Realm + 联邦 + SCIM + K8s OIDC + 应用矩阵 + Vault + Teleport

高级（1-2 年）
  └─ 03_高级: 零信任 + SPIFFE + mTLS + Token Exchange + UEBA + ABAC + ReBAC + IGA + PAM + 国密

工程化（2-3 年）
  └─ 04_最佳实践: 12 金标 + 单一 IdP + 应用纪律 + 4 阶段零信任 + IGA + KPI + 等保

展望（持续）
  └─ 99_发展与展望: Passkey + Agent 身份 + DID + 国密 + Sovereign
```

## 核心判断

```
心法:
  1. 单一 IdP, 别多套
  2. HR 是 SoT, SCIM 自动开撤
  3. 应用全 OIDC, 禁本地账号
  4. MFA 全员 (WebAuthn 优先)
  5. K8s 必走 OIDC + Workload Identity
  6. Vault 动态凭证 取代 静态 DB 密码
  7. SSH CA + Teleport 取代 静态 SSH key
  8. SPIFFE + Service Mesh mTLS 服务间默认加密
  9. 国产: 阿里 IDaaS + 齐治 + Tongsuo (信创必)
  10. 等保三级 + 国密 + 备案 (合规硬)
  11. Token Exchange + Agent 身份 (AI 时代)
  12. 季度权限审查 + Postmortem

红线:
  ❌ 多套 IdP / 用户重复
  ❌ 应用有本地账号 (admin/admin)
  ❌ 静态 access key / DB 密码
  ❌ K8s ServiceAccount Token 共享
  ❌ 无 MFA 高敏
  ❌ 静态 SSH key 长期不轮换
  ❌ 服务间明文 (无 mTLS)
  ❌ 离职 > 24h 仍有权限
  ❌ 无审计 / 无 SIEM (合规风险)
  ❌ 国产 IDaaS 不学 (央企淘汰)
```

## 相关章节

- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 RBAC + OIDC + SPIRE + Vault K8s Auth
- 配合 [08_DevOps](../08_DevOps/index.md) 看 GitLab/Argo/Jenkins SSO + Backstage
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 MLflow/KServe/Higress AI SSO
- 配合 [12_AIOps](../12_AIOps/index.md) 看 Grafana/夜莺 OIDC + ChatOps Agent 身份
- 配合 [14_安全](../14_安全/index.md) 看 SIEM + Audit + 等保 + 国密
- 配合 [15_渗透测试](../15_渗透测试/index.md) 看 钓鱼 + Token 窃取 + 横向移动
- 配合 [16_故障排查](../16_故障排查/index.md) 看 SSO 故障 + 异常登录
