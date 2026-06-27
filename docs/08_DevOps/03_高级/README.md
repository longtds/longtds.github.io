# 高级

> DevOps 高级 = **Platform Engineering(IDP/Backstage/Port) + Internal Developer Platform 黄金路径 + 多集群+多云+信创联邦交付 + Service Catalog+Crossplane Composition + Pipeline as Code 高级(Tekton Chains+Hermetic Build) + 全链供应链 SLSA L3 + GitOps 高阶(渐进式发布+Flagger 自动化+AnalysisTemplate AI 化) + 大规模 ArgoCD(2000+ Apps) + AI 加持(CodeWhisperer/Copilot/AIOps/AI 评审) + FinOps + Reliability(SRE+错误预算+混沌) + 多集群灾备 SOP**。本章面向 DevOps 平台架构师 / 大企业 DevOps 团队 leader。

## 一、Platform Engineering

### 1.1 IDP（Internal Developer Platform）核心理念

```
平台不是工具堆，是产品。
SRE/DevOps 团队 = 平台开发团队
业务团队 = 平台用户

核心交付:
  - Golden Path (黄金路径)
  - Self-Service Portal
  - 标准化 Service Templates
  - 一站式可观测 + 安全 + 成本
  - DevEx (开发者体验) 指标化
```

### 1.2 Backstage（Spotify 开源）

```bash
npx @backstage/create-app
yarn install && yarn dev
```

核心：

```
Service Catalog        服务目录 (从 GitLab/GitHub 自动发现)
Software Templates     scaffold (Cookiecutter-like)
TechDocs               markdown → 文档站点
Plugins                300+ (ArgoCD/Kubernetes/Jenkins/Grafana/PagerDuty/Cost...)
Kubernetes             查看 Pod / 日志
ArgoCD                 看 App health
GitLab/GitHub          Issue/PR/CI
```

`catalog-info.yaml`（每服务一份）：

```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: order-service
  description: 订单服务
  annotations:
    backstage.io/source-location: url:https://gitlab/.../order
    backstage.io/kubernetes-id: order-service
    argocd/app-name: order-service
    pagerduty.com/integration-key: xxx
    prometheus.io/rule: order_service_slo
spec:
  type: service
  lifecycle: production
  owner: team-order
  system: ecommerce
  providesApis: [order-api]
  consumesApis: [user-api, payment-api]
```

### 1.3 Software Templates（一键脚手架）

```yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata: { name: go-microservice }
spec:
  type: service
  parameters:
    - title: Project
      properties:
        name:  { type: string, title: Name }
        owner: { type: string, ui:field: OwnerPicker }
  steps:
    - id: fetch
      action: fetch:template
      input:
        url: ./skeleton
        values: { name: '${{ parameters.name }}' }
    - id: publish
      action: publish:gitlab
      input:
        repoUrl: gitlab.example.com?repo=${{ parameters.name }}&owner=team-x
    - id: argocd
      action: argocd:create-resources
      input:
        appName: '${{ parameters.name }}'
        repoUrl: ${{ steps.publish.output.remoteUrl }}
    - id: register
      action: catalog:register
      input:
        repoContentsUrl: '${{ steps.publish.output.remoteUrl }}'
        catalogInfoPath: '/catalog-info.yaml'
  output:
    links:
      - { title: Repo,     url: '${{ steps.publish.output.remoteUrl }}' }
      - { title: Catalog,  icon: catalog, entityRef: '${{ steps.register.output.entityRef }}' }
```

一次点击 → repo + CI + ArgoCD + 监控 + 告警 + 文档 全自动接入。

### 1.4 国产平台

```
KubeSphere DevOps ⭐    K8s 内 Jenkins+ArgoCD+一站式
Port                    SaaS IDP
华为 CodeArts           全栈
阿里云效                全栈
腾讯 Coding             全栈
京东行云
百度 CCI / IIM
极狐 GitLab Premium     国内合规
```

## 二、Crossplane Composition（基础设施 IDP）

### 2.1 Composite Resource (XR)

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata: { name: xpostgresqlinstances.db.example.com }
spec:
  group: db.example.com
  names: { kind: XPostgresqlInstance, plural: xpostgresqlinstances }
  claimNames: { kind: PostgresqlInstance, plural: postgresqlinstances }
  versions:
    - name: v1alpha1
      served: true
      referenceable: true
      schema:
        openAPIV3Schema:
          properties:
            spec:
              properties:
                parameters:
                  properties:
                    storageGB: { type: integer }
                    version:   { type: string }
                    tier:      { type: string, enum: [dev, prod] }
```

### 2.2 Composition（多资源打包）

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: postgresqlinstances.aws
  labels: { provider: aws, tier: prod }
spec:
  compositeTypeRef: { apiVersion: db.example.com/v1alpha1, kind: XPostgresqlInstance }
  resources:
    - name: rdsinstance
      base:
        apiVersion: rds.aws.crossplane.io/v1alpha1
        kind: DBInstance
        spec:
          forProvider:
            engine: postgres
            engineVersion: "16"
            dbInstanceClass: db.t3.medium
            allocatedStorage: 20
            multiAZ: true
            backupRetentionPeriod: 7
      patches:
        - { fromFieldPath: spec.parameters.storageGB, toFieldPath: spec.forProvider.allocatedStorage }
        - { fromFieldPath: spec.parameters.version,   toFieldPath: spec.forProvider.engineVersion }
    - name: securitygroup
      base: { ... }
    - name: secret
      base: { ... }
```

业务方 Claim：

```yaml
apiVersion: db.example.com/v1alpha1
kind: PostgresqlInstance
metadata: { name: orders-db, namespace: order }
spec:
  parameters: { storageGB: 100, version: "16", tier: prod }
  compositionSelector: { matchLabels: { provider: aws, tier: prod } }
  writeConnectionSecretToRef: { name: orders-db-conn }
```

业务方只暴露 `storageGB` + `version` + `tier`，平台层屏蔽 RDS/SG/Subnet/IAM 等复杂度。

## 三、Pipeline as Code 高级

### 3.1 Tekton Chains（自动 SLSA Provenance）

```bash
kubectl apply --filename https://storage.googleapis.com/tekton-releases/chains/latest/release.yaml

# 配 KMS 签名 + Rekor 透明日志
kubectl patch configmap chains-config -n tekton-chains --patch '{
  "data": {
    "artifacts.taskrun.format": "in-toto",
    "artifacts.taskrun.storage": "oci,gcs",
    "artifacts.taskrun.signer": "kms",
    "signers.kms.kmsref": "gcpkms://projects/x/locations/y/keyRings/z/cryptoKeys/a/cryptoKeyVersions/1",
    "transparency.enabled": "true",
    "transparency.url": "https://rekor.sigstore.dev"
  }
}'
```

任务跑完自动产 in-toto attestation + 签名 + 推 Rekor 透明日志，无需流水线代码改动。

### 3.2 Hermetic Build（封闭构建）

```
要求:
  - 输入: 只来自 immutable repo + checksum
  - 网络: build 时禁外网 (或仅访问 cache mirror)
  - 工具: pinned digest
  - 输出: deterministic (相同 input → 相同 output)

实现:
  - Bazel ⭐ (大厂首选)
  - Nix / Flox (函数式构建)
  - Buildah --isolation oci
  - BuildKit + frontend.rootless --no-network
```

SLSA L3 准入门槛之一。

### 3.3 复用与共享 Tasks (Tekton Hub)

```bash
tkn hub install task git-clone
tkn hub install task buildah
tkn hub install task trivy-scanner
```

企业内 Catalog：

```
internal-catalog/
  tasks/
    java-build.yaml
    helm-upgrade.yaml
    ...
  pipelines/
    standard-ci.yaml
    fast-track.yaml
```

## 四、大规模 ArgoCD

### 4.1 多 Shard

```yaml
# argocd-application-controller-{0,1,2,3}
# 每个 shard 管 1/N 集群
spec:
  controller:
    sharding:
      replicas: 4
      algorithm: round-robin    # 或 consistent-hashing
```

### 4.2 性能调优

```
单 ArgoCD 实例承载 (实测):
  - < 500 Apps:     默认配置
  - 500-2000 Apps:  controller 多 shard + Redis 集群
  - 2000-5000 Apps: 多 ArgoCD 实例分项目
  - 5000+ Apps:     ApplicationSet + 拆 Hub

关键参数:
  --status-processors 20
  --operation-processors 10
  --kubectl-parallelism-limit 20
  --app-resync 180

Redis:
  - 必须集群 / 哨兵
  - HA + 持久化

Repo Server:
  - 多副本 (5-10)
  - 资源池: 各 4Gi
  - LFS / 大仓必用 cmp side
```

### 4.3 多团队多项目

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata: { name: team-order, namespace: argocd }
spec:
  description: Order team
  sourceRepos:
    - 'https://gitlab.example.com/order/*'
  destinations:
    - { namespace: 'order-*', server: 'https://kubernetes.default.svc' }
  clusterResourceWhitelist:
    - { group: '', kind: Namespace }
  namespaceResourceBlacklist:
    - { group: '', kind: ResourceQuota }    # 平台层管
  roles:
    - name: dev
      policies:
        - 'p, proj:team-order:dev, applications, get, team-order/*, allow'
        - 'p, proj:team-order:dev, applications, sync, team-order/*, allow'
      groups: [order-team]
```

## 五、Reliability：SRE + 错误预算 + 混沌

### 5.1 SLO + 错误预算

```yaml
apiVersion: pyrra.dev/v1alpha1
kind: ServiceLevelObjective
metadata: { name: order-availability }
spec:
  target: "99.9"
  window: 28d
  indicator:
    ratio:
      errors: { metric: 'http_requests_total{job="order",code=~"5.."}' }
      total:  { metric: 'http_requests_total{job="order"}' }
```

```
99.9% 月度 SLO:
  允许故障预算 = 43m12s / 月
  当烧到 50% → 告警
  当烧到 100% → 冻结发布 (release lock)
```

### 5.2 Chaos Mesh（CNCF, 国产 PingCAP 主导）

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata: { name: order-network-loss, namespace: chaos }
spec:
  action: loss
  mode: one
  selector:
    namespaces: [order]
    labelSelectors: { app: order }
  loss: { loss: "30", correlation: "100" }
  duration: "5m"
---
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata: { name: order-pod-kill }
spec:
  action: pod-kill
  mode: random-max-percent
  value: "33"
  selector: { namespaces: [order], labelSelectors: { app: order } }
  duration: "5m"
```

### 5.3 LitmusChaos / Chaos Mesh / Gremlin

```
Chaos Mesh ⭐         CNCF, PingCAP, 国产
LitmusChaos ⭐        CNCF, Hub-style
Gremlin             商业
chaoskube           老牌轻量
AWS FIS / Azure CLI Chaos / 火山引擎 故障注入
```

混沌实验剧本：

```
Game Day SOP:
  1. 选择 SLO 业务
  2. 假设 (Hypothesis): 30% 节点丢失下 P99 < 500ms
  3. 注入 (NetworkChaos / PodChaos / IOChaos / StressChaos)
  4. 观测 (Prometheus / Grafana / Slack)
  5. 自动回滚 (chaos-mesh 时长到期)
  6. 复盘 (Postmortem)
```

## 六、AI 加持 DevOps

### 6.1 代码辅助

```
开源/付费:
  GitHub Copilot ⭐
  Codeium / Cursor / Cody
  通义灵码 (阿里) ⭐
  豆包 MarsCode (字节)
  腾讯云 AI Code Assistant
  CodeGeeX (智谱) ⭐
  
本地化:
  Tabby (开源)
  Continue.dev + Ollama / vLLM 私有部署 ⭐
  CodeShell + 私有部署
```

### 6.2 AI Code Review

```
工具:
  CodeRabbit (PR 智能评审)
  Sourcery
  通义代码评审
  自研: GitLab Webhook + vLLM
  
能力:
  - 风格 / 安全 / Bug 提示
  - PR 摘要
  - 用例生成
  - SBOM 解读
```

### 6.3 AIOps + 流水线智能化

```
失败诊断:
  Prometheus 告警 → LLM 关联日志/trace → 自动 RCA
  CI fail → LLM 看日志 → 提示根因
  
预测:
  CI duration / 缓存命中预测
  代码热点预测 (谁要 review)
  风险评估 (改 SLO 关键服务)

平台:
  自研 LangChain + ELK / Loki
  极狐 GitLab Duo
  GitHub Copilot Workspace
  阿里云效智能助手
```

详见 [12_AIOps](../../12_AIOps/index.md)。

## 七、多集群+多云+信创交付

```
拓扑:
  Karmada Hub
    ├─ AWS / 阿里云 ACK
    ├─ 华为云 CCE
    ├─ 私有云 OpenStack + KubeSphere
    └─ 信创 (鲲鹏 + openEuler + 海光 + KubeSphere)

GitOps:
  ArgoCD ApplicationSet + matrix generator
  跨集群 Image Updater
  全局 Image 仓库 (Harbor Replication)

发布顺序:
  dev → staging → 预生产 → 蓝绿 (一个 region) → 灰度全量

灾备:
  跨 region 同步
  Velero 多 region
  DB 异步复制
```

## 八、FinOps（DevOps 侧）

```
工具:
  OpenCost / Kubecost ⭐
  阿里云费用中心
  华为云成本中心
  
集成 GitOps:
  PR 显示 "本次改动预估 $X / 月"
  Helm chart values 含资源 → 成本预估
  Pull Request comment bot

策略:
  - HPA + Cluster AutoScaler
  - Spot Instance + PDB
  - 闲置 / idle 资源告警
  - 夜间关停 dev/staging
  - 镜像 Stargz 懒加载省带宽
  - CI 缓存命中率监控
  - 多租户配额 + 成本归属
```

## 九、安全 DevOps（DevSecOps）

```
SAST:        SonarQube ⭐ / Semgrep / CodeQL / Coverity
DAST:        OWASP ZAP / Burp / Acunetix / 长亭 X-RAY
SCA:         OWASP Dependency-Check / Snyk / Mend / 长亭洞鉴 ⭐
Container:   Trivy + Grype + Anchore + Clair
IaC Scan:    Checkov / tfsec / KICS / Terrascan
Secrets:     gitleaks / trufflehog / detect-secrets ⭐
License:     FOSSA / Trivy license / OSS Review Toolkit
SBOM:        syft + grype + dependency-track
Signing:     cosign + sigstore policy-controller
Runtime:     Falco + Tetragon + Tracee + 长亭雷池
SIEM:        Wazuh / 国产 (天眼 / 360)
```

集成到 CI 标准 gates：

```
Pre-commit:    secrets / license / format
PR:            SAST + IaC scan + SCA + diff
Build:         Trivy + Grype + SBOM + cosign sign
Deploy:        verify-signature + policy-controller
Runtime:       Falco + Tetragon
```

## 十、典型坑（高级）

| 坑 | 建议 |
|:---|:---|
| **Backstage 没接 Catalog Discovery** | GitLab/GitHub Provider 必装 |
| **Crossplane Composition 太复杂** | 抽象不超 5 层 / Function-based |
| **Tekton Chains 没配 KMS** | 用 KMS / Vault 不要本地 key |
| **SLSA L2 但没 Hermetic** | L3 要封闭构建 |
| **ArgoCD App 5000+ 单 controller** | 必 sharding + Redis 集群 |
| **错误预算冻结发布无 SOP** | 配 ReleaseFreeze webhook + 审批 |
| **混沌没演练 Game Day** | 季度演练 + Postmortem 必发 |
| **AI 评审 false positive 多** | 加 rules + 人审兜底 |
| **Spot 中断没 PDB** | PDB + 优雅停 + 重试 |
| **多集群同步漂移** | ArgoCD self-heal + 周对账 |
| **FinOps 没业务标签** | 强制 label: owner/cost-center/env |
| **DevSecOps 没 baseline** | 必须 gates + 0 CRITICAL 强卡 |

## 十一、Checklist（高级）

```
平台:
☐ Backstage / Port / KubeSphere DevOps 一种
☐ Service Catalog (CatalogInfo 自动发现)
☐ Software Templates (5+ 黄金路径)
☐ TechDocs 自动化

IaC IDP:
☐ Crossplane Composition (DB/Redis/MQ/Object Storage 抽象)
☐ Terraform Atlantis PR-driven
☐ Cluster API 集群生命周期

流水线:
☐ Tekton Chains (in-toto + KMS + Rekor)
☐ Hermetic Build (Bazel / BuildKit no-network)
☐ Internal Task/Pipeline Catalog
☐ 标准 gates + 必须策略

GitOps 大规模:
☐ ArgoCD sharding + Redis HA
☐ AppProject 多团队隔离
☐ ApplicationSet matrix 多环境多集群
☐ Image Updater + Argo Rollouts + AnalysisTemplate

供应链 (SLSA L3):
☐ Tekton Chains 自动 provenance
☐ KMS 签名 + Rekor 透明
☐ Hermetic Build
☐ verify-images 准入
☐ Dependency-Track + Trivy + Grype

SRE:
☐ SLO + 错误预算 + ReleaseFreeze
☐ Pyrra / Sloth
☐ Chaos Mesh / Litmus 季度 Game Day
☐ Postmortem 模板 + 复盘库

AI:
☐ Copilot / 通义灵码 / CodeGeeX 私有
☐ AI 评审 (CodeRabbit / 自研 vLLM)
☐ AIOps 接 CI 失败 RCA
☐ 智能告警合并 (LLM 关联)

多集群:
☐ Karmada Hub + 多云 + 信创
☐ Harbor Replication
☐ Velero 跨 region
☐ 灾备季度演练 RTO/RPO 表

FinOps:
☐ OpenCost / Kubecost
☐ Backstage 成本插件
☐ PR cost preview bot
☐ Idle 资源月度

DevSecOps:
☐ Pre-commit (secrets/license/format)
☐ PR (SAST+SCA+IaC)
☐ Build (Trivy+Grype+SBOM+cosign)
☐ Deploy (verify-signature)
☐ Runtime (Falco+Tetragon)
☐ 等保三级 + 国测中心
```

## 十二、推荐栈（高级）

```
IDP:         Backstage ⭐ / Port / KubeSphere DevOps
基础设施:    Crossplane ⭐ + Composition / Cluster API / Terraform + Atlantis
流水线:      Tekton ⭐ + Chains + Hub / GitLab CI
镜像构建:    Buildah / BuildKit Pod / Bazel (Hermetic)
GitOps:      ArgoCD sharded ⭐ + Image Updater + Rollouts + Workflows + Events
秘密:        Vault Raft HA + ESO + SOPS
策略:        Conftest + Kyverno ⭐ + sigstore policy-controller
供应链 L3:   Tekton Chains + KMS + Rekor + Dependency-Track + Trivy/Grype
观测:        kube-prometheus-stack + Loki + Tempo + DeepFlow + Pyrra/Sloth
混沌:        Chaos Mesh ⭐ / Litmus
AI:          通义灵码 + Copilot + CodeGeeX + AIOps
FinOps:      OpenCost / Kubecost + KRR
安全:        Falco + Tetragon + 长亭洞鉴 + SonarQube
国产平台:    KubeSphere DevOps + 华为 CodeArts / 阿里云效 / 极狐 GitLab
```

> 📖 **核心判断**：DevOps 高级 = **Platform Engineering(Backstage/Port + Golden Path + Crossplane Composition) + Tekton Chains 自动 SLSA + Hermetic Build + ArgoCD 大规模(sharding+多 Project) + SRE(SLO+错误预算+Chaos Mesh) + AI(代码/评审/AIOps) + 多集群多云信创交付 + FinOps + DevSecOps 全栈**。能给团队画"Backstage IDP + Tekton Chains SLSA L3 + Crossplane Composition + ArgoCD 多 Shard + Pyrra SLO + Chaos Mesh + AI 加持 + 多云联邦"全栈架构、能落地 5+ Golden Path + Service Catalog + 季度 Game Day + DORA 度量 + FinOps + DevSecOps gates，就具备 DevOps 平台架构师能力。
