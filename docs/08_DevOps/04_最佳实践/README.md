# 最佳实践

> DevOps 最佳实践 = **DORA 团队基线 + 流水线工程化标准 + 镜像/部署/秘密/策略 强制规范 + 多环境多集群 GitOps 拓扑 + SLO+错误预算+混沌运营 + DevSecOps 全链 + FinOps + 平台工程 IDP 落地 + 国产化路径 + 团队组织模型(Spotify/Topologies) + Incident SOP**。本章把"会跑流水线"升级到"运营企业级 DevOps 平台"。

## 一、组织与团队

### 1.1 角色

```
平台 SRE/DevOps:  IDP + CI/CD 平台 + 监控 + 安全基线
业务 SRE:         应用 SLO + on-call + Postmortem
业务工程师:       用平台 + 写应用 + 接 Golden Path
QA / Sec:         策略 + 流水线 gates
DevSecOps:        SAST/DAST/SBOM/Compliance
FinOps Lead:      成本归属 + 优化
SRE Lead / 平台 PO 文化驱动
```

### 1.2 团队拓扑（Team Topologies）

```
4 种团队:
  Stream-Aligned   业务流 (主体)
  Platform         平台
  Enabling         教练 / 转型
  Complicated-Subsystem 复杂子系统 (AI / DB)

3 种交互:
  X-as-a-Service   平台对业务 ⭐
  Collaboration    短期协作
  Facilitating     教练辅导

健康比例:
  Stream  : Platform : Enabling : CS = 6 : 1 : 0.5 : 0.5
```

### 1.3 DORA 队伍画像基线

| 等级 | 部署频率 | Lead Time | MTTR | 失败率 |
|:---|:---|:---|:---|:---|
| **精英** | 按需(日多次) | < 1h | < 1h | < 15% |
| **高效** | 日-周 | 1d-1w | < 1d | < 15% |
| **中等** | 周-月 | 1w-1m | < 1d | 16-30% |
| **低效** | 月-季 | 1m-6m | < 1w | > 30% |

国内中大型企业大多在 **中等 → 高效** 区间，目标至少高效。

## 二、流水线工程化标准

### 2.1 流水线分层

```
Pre-commit (本地):
  - lint (Prettier / Black / gofmt)
  - 单测 (changed only)
  - gitleaks / detect-secrets
  - 不超 30s

Pull Request (CI):
  - lint full
  - 单元 (并行)
  - 静态扫描 (SonarQube + SAST)
  - SCA 依赖扫描
  - IaC 扫描 (Checkov / tfsec)
  - Build (with cache)
  - Image Scan (Trivy + Grype)
  - PR diff + test report
  - 5-10 min 内出结果

Merge → main (CI):
  - 上面全跑
  - 集成测试 (TestContainers)
  - Build push + cosign + SBOM + SLSA
  - Deploy Dev (auto)
  - Smoke Test

Tag → Release (CD):
  - Deploy Staging (auto + E2E)
  - Deploy Prod (Canary via Argo Rollouts)
  - 监控 + 错误预算
  - 自动回滚 (AnalysisTemplate 失败)
```

### 2.2 标准 Gates 表

| Gate | 阈值 | 强卡 |
|:---|:---|:---:|
| Lint | 0 errors | ✅ |
| Unit Coverage | ≥ 70% | ✅ |
| Sonar | 0 CRITICAL | ✅ |
| SAST (Semgrep/CodeQL) | 0 HIGH | ✅ |
| SCA | 0 CRITICAL CVE | ✅ |
| IaC Scan | 0 HIGH | ✅ |
| Image Trivy | 0 HIGH+CRITICAL | ✅ |
| Image Grype | 0 HIGH+CRITICAL | ✅ |
| Cosign Sign | 必须 | ✅ |
| SBOM | 必生成 | ✅ |
| SLSA Provenance | 必生成 | ✅ |
| Integration Test | Pass | ✅ |
| E2E Test (key path) | Pass | ✅ |
| Smoke after Dev | Pass | ✅ |
| Canary AnalysisTemplate | 99%+ SR | ✅ |
| Error Budget | 未冻结 | ✅ |
| Change Ticket (prod) | 审批 | ✅ |

### 2.3 流水线性能基线

```
Pre-commit:    < 30s
PR CI:         < 10 min (95th)
Build:         < 3 min (with cache)
Unit Test:     < 5 min (并行)
Image:         < 2 min
Deploy Dev:    < 2 min
E2E:           < 15 min

慢的原因排查:
  - Buildx 缓存命中率 < 80%
  - Test 串行
  - Maven/Gradle 没缓存
  - Docker pull 没 mirror
  - Runner pool 不够
```

## 三、镜像/部署/秘密/策略规范

### 3.1 镜像规范（直接沿用 06_Docker/04_最佳实践）

```
☐ 命名: harbor.example.com/<team>/<service>:<sha|vX.Y.Z>
☐ 禁 :latest
☐ 基础: distroless / wolfi / alpine
☐ 非 root USER + readOnlyRootFilesystem
☐ HEALTHCHECK
☐ cosign 签名 + SBOM
☐ Trivy HIGH+CRITICAL = 0
☐ 多架构 amd64+arm64
☐ 镜像 < 200MB（除大模型/AI）
```

### 3.2 Deployment 团队基线（直接沿用 07_K8s/04_最佳实践）

```
☐ replicas: 至少 2 (prod 3+)
☐ requests/limits 全设
☐ readiness + liveness + startupProbe
☐ podAntiAffinity + topology spread
☐ PreStop sleep 10 + grace 60s
☐ RollingUpdate maxSurge=1 maxUnavailable=0
☐ PDB minAvailable: 1
☐ HPA + 错误预算监控
☐ 标签齐全 (app/version/team/cost-center)
☐ ServiceAccount + 最小 RBAC
☐ readOnlyRootFilesystem + drop ALL caps
☐ NetworkPolicy
```

### 3.3 秘密规范

```
等级:
  L0 公开            可入 Git
  L1 配置 (非密)     ConfigMap
  L2 内部敏感        SealedSecrets / SOPS
  L3 高敏 (密钥)     Vault + ESO ⭐
  L4 国密 / 国家级    海光 CSV / 国密加密机 + Vault

规则:
  ❌ 写代码 / Dockerfile / Helm values
  ❌ 直接 base64 Secret
  ✅ ESO + Vault
  ✅ 90 天自动旋转
  ✅ 审计入 SIEM
```

### 3.4 策略规范（Kyverno 强制）

```yaml
集群必启策略:
☐ require-resources         必须 requests/limits
☐ require-probes            必须 readiness + liveness
☐ disallow-latest-tag
☐ disallow-privileged
☐ disallow-host-network
☐ require-nonroot
☐ require-trusted-registries
☐ require-image-signature   (cosign)
☐ require-runasnonroot      + readOnlyRootFilesystem
☐ require-pdb               prod
☐ require-network-policy
☐ require-labels            app/team/env/cost-center
```

## 四、多环境多集群拓扑

### 4.1 推荐架构

```
代码 (GitLab)
   │
   ▼
应用 repo            基础设施 repo
   │ (CI: build+scan+sign+SBOM+SLSA+push)   │
   ▼                                          ▼
Harbor (signed)                          ArgoCD ApplicationSet (Hub)
   │                                          │
   │ Image Updater (semver/digest)            │ Sync
   ▼                                          ▼
ArgoCD ApplicationSet
   ├─ Dev cluster        (auto, no gate)
   ├─ Staging cluster    (auto, E2E)
   ├─ Pre-prod cluster   (manual gate + change ticket)
   ├─ Prod-Region-A      (Canary 5%→25%→50%→100% via Argo Rollouts)
   ├─ Prod-Region-B      (按 Karmada PropagationPolicy)
   └─ DR-Region          (受控 sync, 灾备)
```

### 4.2 环境隔离原则

```
分集群:
  ☐ Dev / Staging / Pre-prod / Prod 必分集群
  ☐ Prod 跨 region 至少 2 集群
  ☐ AI 训练 独立集群
  ☐ 大业务/合规独立集群

资源:
  ☐ Dev 资源 = Prod / 4
  ☐ Staging = Prod / 2 (验证)
  ☐ Pre-prod = Prod 同构小规模

数据:
  ☐ Dev / Staging: 脱敏数据
  ☐ Pre-prod: 影子流量 / 镜像流量
  ☐ Prod: 真实
```

### 4.3 灰度发布矩阵

| 类型 | 速度 | 风险 | 场景 |
|:---|:---|:---|:---|
| **RollingUpdate** | 中 | 中 | 默认 |
| **Canary (Argo Rollouts)** | 慢 | 低 | 业务核心 |
| **Blue/Green** | 快 | 低 | 大改动 / DB 迁移 |
| **A/B Test** | 中 | 低 | 算法 / 功能 |
| **Shadow / Mirror** | - | 极低 | 新版本验证 |
| **Feature Flag** | 即时 | 极低 | 业务开关 |

## 五、SRE 运营基线

### 5.1 SLO 目标层级

```
P0 业务: 99.95% (月预算 21m)    支付 / 订单核心
P1 业务: 99.9%  (月预算 43m)    主业务
P2 业务: 99.5%  (月预算 3.6h)   后台
P3 业务: 99%    (月预算 7.2h)   内部
```

### 5.2 错误预算 SOP

```
燃烧策略:
  50%  Slow burn, 提醒
  100% Fast burn (1h 5%), 告警 + 关注
  150% 冻结发布 + 拉响应

发布冻结:
  ArgoCD Hook: 检查 Pyrra → 冻结期间 Sync skip
  必须接 RFC + 紧急通道
```

### 5.3 必备告警 + 升级路径

```
P0 业务:    钉钉/飞书 webhook + 电话 (Pagy / 阿里电话告警)
P1 业务:    钉钉/飞书 + 邮件
P2/P3:      钉钉/飞书

升级:
  on-call → on-call lead → SRE lead → CTO

值班:
  6h/天 + 周末轮换
  RA 必有 runbook
  Postmortem 模板
```

### 5.4 Chaos / Game Day

```
季度演练:
  Q1: 节点失联 (NetworkChaos partition)
  Q2: 单 Pod kill (PodChaos pod-kill)
  Q3: DNS 抖动 (DNSChaos)
  Q4: 磁盘满 (StressChaos)
  额外: 跨 region 切换 + 全链
```

## 六、DevSecOps 全链

```
Pre-commit:    gitleaks + detect-secrets + license check + format
PR:            SonarQube + Semgrep + Bandit (Py) + Snyk SCA + Checkov (IaC)
Build:         Trivy + Grype + syft + cosign + Tekton Chains (SLSA)
Deploy:        Kyverno verify-images + policy-controller
Runtime:       Falco + Tetragon + Tracee + 长亭雷池
SIEM:          Wazuh / 360 / 天眼 (告警 SOC)
合规:          等保三级 / 国测中心 / GDPR / SOC2
Audit:         K8s audit log + GitLab audit + Vault audit → SIEM
```

详见 [14_安全/03_高级](../../14_安全/03_高级/README.md) 供应链 SLSA L3 章节。

## 七、FinOps 落地

### 7.1 数据采集

```
工具:
  OpenCost ⭐ (开源)
  Kubecost (商业)
  阿里云 / 华为云 / 腾讯云 / 火山引擎 费用中心

维度:
  - namespace / label / 团队 / 业务线
  - CPU / 内存 / 存储 / GPU / 流量
  - 实际用 vs requests (idle 浪费)
  - 镜像/cache 存储
  - CI/CD Runner 时长
```

### 7.2 月度优化清单

```
☐ requests 精准化 (KRR / VPA recommendation)
☐ HPA + Cluster AutoScaler
☐ Spot / 抢占 (test/dev) + PDB
☐ 闲置 PVC 自动清理 (> 30 天)
☐ 闲置 Image 清理 (Harbor 策略)
☐ 镜像 Stargz 懒加载省 pull 带宽
☐ 大节点合并 (NUMA + 高密)
☐ 多租户 Quota 强制
☐ CI/CD cache 命中率监控
☐ 业务限流 / 退化 (削峰)
```

### 7.3 成本归属

```
强制 label:
  cost-center: <CC-001>
  team:        order
  env:         prod
  business:    ecommerce

Backstage 自动汇总:
  团队 / 业务线 / 服务 → 月度账单
  PR comment: "预估 +$X/月"
```

## 八、平台工程 IDP 落地

```
3 个月规划:
  M1: Backstage Service Catalog (从 GitLab 自动发现)
  M2: Software Template (Go / Java / Python 微服务三件套)
  M3: TechDocs + Cost + Argo App 集成

6 个月:
  M4: Crossplane Composition (DB / Redis / MQ)
  M5: 自助 namespace / RBAC / Quota 申请
  M6: AI 加持 (AIOps + Code Review)

KPI:
  - 新服务接入时间: < 1 天 (Template)
  - 平台 NPS: ≥ 8/10
  - 黄金路径覆盖率: > 80%
  - DORA 全指标提升
```

## 九、国产化路径

```
2026:
☐ GitLab CE/EE 或 极狐 GitLab 自建
☐ Harbor + 国密 TLS
☐ KubeSphere DevOps / 华为 CodeArts 一种
☐ Trivy + 长亭洞鉴
☐ DeepFlow / 夜莺监控
☐ 通义灵码 / CodeGeeX 私有部署
☐ KubeSphere DevOps 一站式
☐ 国产 OS (openEuler) + 鲲鹏 ARM Runner

2027-2028:
☐ Karmada 多云联邦
☐ Crossplane 国产 Provider (阿里/华为/腾讯/火山)
☐ 国产 AI 代码评审平台 (通义 / GLM / 智谱)
☐ 等保三级 + 国测 + 国密 全栈
☐ FinOps 国产平台 (阿里费用中心 / 华为 GA)
```

## 十、Incident SOP

### 10.1 应急 5 分钟黄金窗

```
0-5min:
  - 告警接收 (P0 → 自动拉群 / 电话)
  - on-call 确认 (ack)
  - 拉应急群 (钉钉/飞书 webhook)
  - 看大盘 (Grafana / DeepFlow)

5-30min:
  - 影响评估 (用户数 / 损失 / SLO)
  - 限流 / 降级 / 回滚 (ArgoCD rollback)
  - on-call lead 介入
  - 通知业务 + 安抚客户

30min-2h:
  - 根因定位
  - 修复 / 临时方案
  - 验证恢复
  - 监控观察

2h+:
  - Postmortem 启动
  - Action Item
  - 知识库归档
```

### 10.2 Postmortem 模板

```
Title:
Date / Duration / Severity:
Impact: (用户 / 损失 / SLO 燃烧)
Timeline: (T0 告警 / T1 定位 / T2 修复 / T3 恢复)
Root Cause:
Detection: (从发生到告警时差)
Resolution:
Lessons Learned:
Action Items: (Owner + Due Date + Priority)
Blameless: ⭐ 不针对个人
```

## 十一、Checklist（最佳实践）

```
组织:
☐ Stream / Platform / Enabling / CS 团队拓扑
☐ DORA 度量 (DevLake)
☐ Incident SOP + Postmortem 模板
☐ Game Day 季度

流水线:
☐ Pre-commit + PR + Merge + Release 四层
☐ 标准 Gates 表 + 强卡
☐ 性能基线 (PR < 10min)
☐ 标准 Pipeline Template (Catalog)

镜像/部署/秘密/策略:
☐ 镜像规范 + Trivy + cosign + SBOM
☐ Deployment 基线 + Kyverno 强制
☐ 秘密分级 + Vault + ESO
☐ 必须策略全覆盖

GitOps:
☐ Dev/Staging/Pre-prod/Prod 分集群
☐ ArgoCD ApplicationSet + 多团队 Project
☐ Image Updater + Argo Rollouts
☐ Karmada 多云

SRE:
☐ SLO + Pyrra
☐ 错误预算 + 发布冻结
☐ 必备告警 + 升级路径
☐ Chaos Mesh 季度
☐ Runbook 全覆盖

DevSecOps:
☐ Pre-commit (secrets/license)
☐ PR (SAST+SCA+IaC)
☐ Build (Trivy+SBOM+Cosign+SLSA)
☐ Deploy (verify-images)
☐ Runtime (Falco+Tetragon)
☐ SIEM + 等保

FinOps:
☐ OpenCost + Kubecost
☐ 强制 label cost-center
☐ KRR 月度
☐ Spot + 闲置清理
☐ PR cost preview bot

平台 IDP:
☐ Backstage / Port / KubeSphere DevOps
☐ Service Catalog 自动发现
☐ 黄金路径 5+ Template
☐ Crossplane Composition
☐ AI 加持

国产化:
☐ GitLab/极狐 + Harbor + KubeSphere
☐ 通义灵码 / CodeGeeX 私有
☐ DeepFlow + 夜莺
☐ 等保 + 国测 + 国密
```

## 十二、典型生产架构模板

### 12.1 互联网中型企业

```
Git:         GitLab CE + Trunk-Based
CI:          GitLab CI + Buildx + Harbor + Trivy + cosign
GitOps:      ArgoCD ApplicationSet + Image Updater + Rollouts
集群:        K8s 3 集群 (Dev/Staging/Prod) + Karmada Hub
监控:        kube-prometheus + Loki + Tempo + DeepFlow
混沌:        Chaos Mesh 季度
平台:        Backstage IDP (Service Catalog + 3 Templates)
团队:        5-15 SRE + DevOps
```

### 12.2 央企信创

```
Git:         极狐 GitLab Premium / 华为 CodeArts
CI:          GitLab CI / CodeArts + Buildah (rootless) + Harbor 国密
GitOps:      KubeSphere DevOps + ArgoCD
集群:        多集群 + Karmada + 鲲鹏 ARM64 + openEuler
监控:        DeepFlow + 夜莺 + 360 SIEM
混沌:        Chaos Mesh
AI:          通义灵码 / CodeGeeX 私有 + AIOps
合规:        等保三级 + 国测中心 + 国密
团队:        10-30 SRE/DevOps + DevSecOps + FinOps
```

### 12.3 AI 公司

```
Git:         GitLab / GitHub
CI:          GitLab CI + Buildx (大镜像 Stargz)
GitOps:      ArgoCD + Argo Workflows (训练 pipeline)
集群:        K8s (业务) + Slurm/K8s (训练) + Karmada
监控:        Prometheus + DCGM + Tempo + DeepFlow
AI 调度:    Volcano + HAMi + vLLM + Argo Workflows
模型:        Hugging Face Hub mirror + Harbor + 大文件 LFS
混沌:        Chaos Mesh (推理) + 模型 fallback
```

### 12.4 党政关基

```
Git:         GitLab 内网 (Self-hosted, 高安)
CI:          Jenkins / GitLab CI + Kaniko + 国密 TLS
GitOps:      ArgoCD (内网) + 隔离区流转
集群:        KubeSphere + 鲲鹏 ARM + openEuler + iSulad
存储:        Rook-Ceph + 国密
监控:        DeepFlow + 夜莺 + 国产 SOC
AI:          CodeGeeX 私有 + 等保三级 + 国测
合规:        等保 / 商密 / 关基 / 国测
```

## 十三、推荐栈（最佳实践）

```
代码:        GitLab CE/EE / 极狐 / Gitea
CI:          GitLab CI ⭐ / Tekton / Jenkins / GitHub Actions / 华为 CodeArts
镜像:        Harbor ⭐ + Buildx + Kaniko + cosign + syft + Trivy + Grype
GitOps:      ArgoCD ⭐ + ApplicationSet + Image Updater + Rollouts + Workflows
IaC:         Terraform + Atlantis / Crossplane Composition / Cluster API
秘密:        Vault + ESO ⭐ + SOPS
策略:        Conftest (CI) + Kyverno (K8s) + sigstore policy-controller
观测:        kube-prometheus + Loki + Tempo + DeepFlow + Pyrra/Sloth
混沌:        Chaos Mesh ⭐ / Litmus
平台:        Backstage ⭐ / Port / KubeSphere DevOps
AI:          通义灵码 / CodeGeeX / Copilot + AIOps
FinOps:      OpenCost / Kubecost + KRR
DevSecOps:   gitleaks + Semgrep + SonarQube + Trivy + Grype + cosign + Falco + Tetragon
国产:        Harbor + KubeSphere DevOps + 华为 CodeArts / 阿里云效 + DeepFlow + 通义灵码 + 长亭洞鉴
```

> 📖 **核心判断**：DevOps 最佳实践 = **DORA 团队基线 + 标准 Gates 流水线 + 镜像/部署/秘密/策略规范 + 多环境多集群 GitOps + SRE(SLO+错误预算+混沌) + DevSecOps 全链 + FinOps + 平台工程 IDP + 国产化 + Incident SOP**。能给团队画"GitLab CI + Tekton Chains + Harbor + cosign + ArgoCD ApplicationSet + Argo Rollouts + Vault + ESO + Pyrra + Chaos Mesh + Backstage + AI 加持 + DeepFlow + 国产化"全栈、能 Q1 Q2 月度 Game Day + 强制 Kyverno 策略 + 自动 SLSA Provenance + AI Code Review + 多云联邦交付，就具备 DevOps 团队负责人能力。
