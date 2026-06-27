# 08. DevOps

> DevOps = 文化 + 自动化 + 度量。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦 DORA + Git 工作流 + Jenkins/GitLab CI + Helm + ArgoCD + Tekton Chains + Crossplane + 平台工程(Backstage) + DevSecOps + SLSA L3 + FinOps + 国产化十二条主线。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入职 1 年内 | CALMS+DORA / Git 工作流(Trunk-Based) / Jenkins+GitLab CI / 多阶段 Dockerfile / Helm+Kustomize / ArgoCD / Terraform+Ansible / Vault 基础 + 20 题 |
| [02_进阶](02_进阶/README.md) | 独立平台搭建 | GitOps 全链(ApplicationSet+Image Updater+Rollouts+Workflows) / Tekton 云原生流水线 / 镜像构建深度(Kaniko/BuildKit Pod) / Vault+ESO+SOPS 秘密 / Terraform Cloud+Crossplane / OPA+Kyverno 策略 / SBOM+cosign+SLSA / DORA 度量(DevLake) |
| [03_高级](03_高级/README.md) | 平台架构师 | Platform Engineering(Backstage+Software Templates) / Crossplane Composition / Tekton Chains 自动 SLSA L3 / Hermetic Build / ArgoCD 大规模 sharding / SRE(SLO+错误预算+Chaos Mesh) / AI 加持(Copilot+AIOps+Code Review) / 多集群+多云+信创联邦 / FinOps + DevSecOps 全链 |
| [04_最佳实践](04_最佳实践/README.md) | 团队负责人 | 团队拓扑(Team Topologies) / DORA 基线 / 流水线工程化标准 + 必须 Gates / 镜像+部署+秘密+策略 强制规范 / 多环境多集群拓扑 / SRE 运营(SLO+混沌+Postmortem) / DevSecOps 全链 / FinOps + IDP 落地 / 国产化路径 / Incident SOP + 4 种生产架构 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | Platform Engineering 取代 DevOps 团队 / GitOps 普及 / SLSA L3 强制 / AI 全面加持 / DevSecOps 一体化 / 多云+信创+边缘 / VSM 替代 DORA / SRE+FinOps 普及 / 国产开源 70% + 19 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
  └─ 01_基础: Git Trunk-Based + GitLab CI 一条 Pipeline (lint/test/build/scan/push/deploy) + Helm + ArgoCD + Vault + Terraform + Ansible + 20 题

进阶（3-12 月）
  └─ 02_进阶: ArgoCD ApplicationSet + Image Updater + Argo Rollouts + Tekton + Kaniko/BuildKit + Vault+ESO + OPA/Kyverno + cosign+SBOM + DevLake DORA

高级（1-2 年）
  └─ 03_高级: Backstage IDP + Crossplane Composition + Tekton Chains SLSA L3 + Hermetic Build + ArgoCD sharding + Pyrra SLO + Chaos Mesh + AI 加持 + 多云联邦

工程化（2-3 年）
  └─ 04_最佳实践: 团队拓扑 + DORA 基线 + 流水线 Gates + 镜像/部署/秘密/策略规范 + 多集群拓扑 + SRE 运营 + DevSecOps 全链 + FinOps + IDP + Incident SOP

展望（持续）
  └─ 99_发展与展望: Platform Engineering + GitOps + SLSA L3 + AI Native + DevSecOps + 多云联邦 + VSM + SRE/FinOps + 国产开源 十大主线
```

## 核心判断

```
心法:
  1. DevOps 是文化，不是工具堆
  2. CI/CD 三层卡控（Pre-commit / PR / Build / Deploy）必须有标准 Gates
  3. GitOps 是单一事实源 — 一切走 Git，禁手 kubectl apply
  4. 不可变镜像 + cosign 签名 + SBOM + SLSA Provenance 四件套必备
  5. Vault + ESO 是秘密治理唯一正解（禁硬编码、禁 base64）
  6. SLO + 错误预算 + 混沌演练 — SRE 三件套
  7. Platform Engineering = Platform as a Product（DevOps 团队转型方向）
  8. AI 工具（Copilot / 通义灵码 / AIOps）必须入栈
  9. 国产化栈 (KubeSphere DevOps / 极狐 / Harbor / DeepFlow / 通义灵码) 必修
  10. DORA → VSM（端到端价值流）是下一代度量

红线:
  ❌ 密码硬编码 / base64 当加密
  ❌ 手 kubectl apply 上生产
  ❌ :latest tag 上生产
  ❌ 没回滚机制
  ❌ CI 跑 root + DinD
  ❌ 没策略卡控 (resources/probe/sig)
  ❌ 没 SBOM / 签名
  ❌ 单 master ArgoCD + 单 Vault
  ❌ 没 SLO / 错误预算 / Postmortem
  ❌ 直推 prod 不灰度
  ❌ 没成本归属 label
  ❌ 没接 DORA / VSM 度量
```

## 相关章节

- 配合 [06_Docker](../06_Docker/index.md) 看镜像构建（Buildx/Kaniko）+ Harbor + cosign
- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 ArgoCD/Helm/Kustomize/Operator + 资源策略
- 配合 [09_中间件](../09_中间件/index.md) 看 DB/Redis/MQ Operator GitOps 化（KubeBlocks）
- 配合 [10_大数据](../10_大数据/index.md) 看 Spark/Flink 流水线 + 数据 Pipeline GitOps
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 Argo Workflows 训练 pipeline + 模型 GitOps
- 配合 [12_AIOps](../12_AIOps/index.md) 看 AI 加持 CI/CD + 故障 RCA + 智能告警
- 配合 [13_认证与SSO](../13_认证与SSO/index.md) 看 GitLab/Vault/ArgoCD OIDC + Keycloak SSO
- 配合 [14_安全](../14_安全/index.md) 看 DevSecOps 全链 + SLSA + Falco + Tetragon
- 配合 [15_渗透测试](../15_渗透测试/index.md) 看 CI 内 DAST + SCA + 红蓝攻防
- 配合 [16_故障排查](../16_故障排查/index.md) 看 Incident SOP + Postmortem 模板
