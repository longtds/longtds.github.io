# 14. 安全

> 安全 = 体系工程，覆盖主机/网络/容器/数据/身份/应用/AI/合规。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦主机加固 + DevSecOps + K8s 安全基线 + Service Mesh mTLS + Vault 全栈 + 雷池/ModSec WAF + Falco/Tetragon 运行时 + SPIRE + SOC + 红蓝 + 国密 + 等保 3 + 关基 + AI 安全 + Confidential Computing + PQC 16 大主线。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入门 | CIA + STRIDE + OWASP Top 10 + 主机加固(SSH/sysctl/SELinux/auditd) + 网络ACL + 密码学 + 证书+PKI + Web 安全 + Trivy 镜像 + 日志审计 + 等保2级 + 20 题 |
| [02_进阶](02_进阶/README.md) | 维护安全平台 | DevSecOps 全链 + Falco/Tetragon + K8s PSS+NetPol+Kyverno + Mesh mTLS + Vault 全栈 + 雷池/ModSec WAF + 蜜罐 + API 安全 + 数据加密+脱敏+DLP + 等保3 + 国密 + SIEM |
| [03_高级](03_高级/README.md) | 安全架构师 | SOC+SOAR+TIP+CTEM+ASM + 威胁建模 + 红蓝紫 + Threat Hunting + 供应链 SLSA L3 + Confidential Computing + 零信任 + DSPM/DLP/隐私计算 + AI 安全(LLM Top10) + 多云 CNAPP + 关基 + PICERL IR + 团队 |
| [04_最佳实践](04_最佳实践/README.md) | 平台负责人/CISO | 12 金标 + CIS + DevSecOps 工具链 + K8s 基线 + 零信任落地 + 数据保护 + 等保3+国密+信创 + 24x7 SOC + 红蓝 + IR + 团队组织 + KPI + 法规合规 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | LLM 安全 + AI 反 AI + SLSA L3 强制 + Confidential 普及 + 零信任/SASE + 国密+关基 + Sovereign + PQC + DSPM/CNAPP + AI SOC + 20 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
 └─ 01_基础: 加固 + OWASP + Trivy + TLS + 等保2 + 20 题

进阶（3-12 月）
 └─ 02_进阶: DevSecOps + Falco + Kyverno + Mesh + Vault + WAF + SIEM + 等保3

高级（1-2 年）
 └─ 03_高级: SOC平台 + 红蓝 + SLSA + Confidential + AI 安全 + CNAPP + 关基

工程化（2-3 年）
 └─ 04_最佳实践: 12 金标 + 24x7 SOC + 红蓝演练 + 等保3+国密+信创 + IR + KPI

展望（持续）
 └─ 99_发展与展望: LLM + Agent + Confidential + PQC + Sovereign + AI SOC
```

## 核心判断

```
心法:
 1. 安全是体系, 不是产品堆砌
 2. CIS Benchmarks + 等保 是基线
 3. DevSecOps 左移: SAST/SCA/IaC/Container/SBOM/签名全链
 4. K8s 必走 PSS + NetPol + Kyverno + Falco
 5. Service Mesh Strict mTLS + SPIFFE (服务间默认加密)
 6. Vault 动态凭证 取代 静态密码
 7. 全员 MFA + Passkey + WebAuthn (身份是入口)
 8. 24x7 SOC + SIEM 6mo + 季度红蓝
 9. 国密 + 等保 3 + 关基 + 信创 (中国央企)
 10. AI 安全 (Prompt Injection + Guardrails + Agent) 是新风口
 11. Confidential Computing (TDX/SEV/CSV) 是 LLM 时代刚需
 12. PICERL IR + Velociraptor 取证 + Postmortem 闭环

红线:
 边界防火墙 + 静态密码 (古典)
 K8s 默认 Pod (root + privileged + 无 NetPol)
 镜像 latest + 无签名 + 无扫描
 Secret 入代码 (gitleaks 必跑)
 DB 静态密码 + 多人共享
 SSH 静态 key 长期不轮换
 无 SIEM / 无审计 / 无 6mo 留存
 无红蓝演练 (不知道防御缺口)
 等保 / 国密 / 信创 不学 (央企淘汰)
 AI 安全 不学 (LLM 时代盲区)
```

## 相关章节

- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 RBAC + PSS + NetPol + Kyverno + Falco
- 配合 [08_DevOps](../08_DevOps/index.md) 看 DevSecOps 工具链 + cosign + SLSA
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 LLM Guardrails + Confidential Inference
- 配合 [12_AIOps](../12_AIOps/index.md) 看 SIEM + UEBA + AI SOC Copilot
- 配合 [13_认证与SSO](../13_认证与SSO/index.md) 看 IdP + MFA + SPIRE + Vault
- 配合 [15_渗透测试](../15_渗透测试/index.md) 看 红蓝 + ATT&CK + Sliver
- 配合 [16_故障排查](../16_故障排查/index.md) 看 IR + 取证 + Postmortem
