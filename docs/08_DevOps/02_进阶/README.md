# 进阶

> DevOps 进阶 = **GitOps 全链(ArgoCD ApplicationSet+Image Updater+Rollouts) + Tekton/Argo Workflows 云原生流水线 + 镜像深度(Kaniko/Buildah/远程缓存) + 多环境多集群 + 渐进式发布(Canary/Blue-Green) + Vault+SOPS+SealedSecrets 秘密治理 + Terraform Cloud/Atlantis + Crossplane + Policy as Code(OPA/Kyverno) + DORA 度量 + SBOM+签名+SLSA + 国产化栈(GitLab 极狐/华为 CodeArts/阿里云效)**。本章面向独立负责中型团队 DevOps 平台的工程师。

## 一、GitOps 深度

### 1.1 ApplicationSet (多环境/多集群)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata: { name: microservices }
spec:
  generators:
    - matrix:
        generators:
          - git:
              repoURL: https://gitlab.example.com/infra.git
              revision: HEAD
              directories: [{ path: "apps/*" }]
          - list:
              elements:
                - { env: dev,     cluster: in-cluster, namespace: dev }
                - { env: staging, cluster: in-cluster, namespace: staging }
                - { env: prod,    cluster: prod, namespace: prod }
  template:
    metadata: { name: '{{path.basename}}-{{env}}' }
    spec:
      project: default
      source:
        repoURL: https://gitlab.example.com/infra.git
        path: '{{path}}/overlays/{{env}}'
        targetRevision: HEAD
      destination: { server: '{{cluster}}', namespace: '{{namespace}}' }
      syncPolicy:
        automated: { prune: true, selfHeal: true }
        retry:     { limit: 3, backoff: { duration: 30s, factor: 2 } }
```

### 1.2 Image Updater

```yaml
metadata:
  annotations:
    argocd-image-updater.argoproj.io/image-list: web=harbor.example.com/web/api
    argocd-image-updater.argoproj.io/web.update-strategy: semver
    argocd-image-updater.argoproj.io/web.allow-tags: regexp:^v\d+\.\d+\.\d+$
    argocd-image-updater.argoproj.io/write-back-method: git
    argocd-image-updater.argoproj.io/git-branch: main
```

策略：

```
semver:     v1.2.3 → v1.2.4 (语义化升级)
latest:     mutable tag (开发)
digest:     SHA digest
newest-build: 时间最新
alphabetical: 字母序
```

### 1.3 Argo Rollouts（渐进式发布）

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: web }
spec:
  replicas: 10
  selector: { matchLabels: { app: web } }
  template: { ... }   # 与 Deployment 一样
  strategy:
    canary:
      canaryService: web-canary
      stableService: web
      trafficRouting:
        istio:
          virtualService: { name: web, routes: [primary] }
      steps:
        - setWeight: 5
        - pause: { duration: 5m }
        - analysis:
            templates: [{ templateName: success-rate }]
        - setWeight: 25
        - pause: { duration: 10m }
        - analysis:
            templates: [{ templateName: success-rate }]
        - setWeight: 50
        - pause: { duration: 20m }
        - setWeight: 100
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata: { name: success-rate }
spec:
  args: [{ name: service-name }]
  metrics:
    - name: success-rate
      interval: 1m
      successCondition: result[0] >= 0.99
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(http_requests_total{job="{{args.service-name}}",code=~"2.."}[5m])) /
            sum(rate(http_requests_total{job="{{args.service-name}}"}[5m]))
```

### 1.4 Argo Workflows（任务编排 + 训练流水线）

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata: { generateName: ml-train- }
spec:
  entrypoint: pipeline
  templates:
    - name: pipeline
      dag:
        tasks:
          - { name: prepare,    template: prepare-data }
          - { name: train,      template: train, dependencies: [prepare] }
          - { name: evaluate,   template: eval,  dependencies: [train] }
          - { name: deploy,     template: deploy, dependencies: [evaluate], when: "{{tasks.evaluate.outputs.parameters.score}} > 0.9" }
    - name: prepare-data
      container: { image: harbor.example.com/ml/prepare:1, command: [python, prepare.py] }
    - name: train
      container:
        image: harbor.example.com/ml/train:1
        command: [python, train.py]
        resources: { limits: { nvidia.com/gpu: 1 } }
    - name: eval
      container: { image: harbor.example.com/ml/eval:1, command: [python, eval.py] }
      outputs:
        parameters:
          - name: score
            valueFrom: { path: /tmp/score.txt }
    - name: deploy
      container: { image: bitnami/kubectl, command: [helm, upgrade, --install, ...] }
```

## 二、Tekton（云原生流水线）

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata: { name: web-ci }
spec:
  params:
    - { name: image, type: string }
    - { name: sha,   type: string }
  workspaces: [{ name: ws }]
  tasks:
    - name: fetch
      taskRef: { name: git-clone }
      workspaces: [{ name: output, workspace: ws }]
      params:
        - { name: url, value: 'https://gitlab/.../web.git' }
        - { name: revision, value: '$(params.sha)' }
    - name: build
      runAfter: [fetch]
      taskRef: { name: buildah }
      workspaces: [{ name: source, workspace: ws }]
      params:
        - { name: IMAGE, value: '$(params.image):$(params.sha)' }
    - name: scan
      runAfter: [build]
      taskRef: { name: trivy }
      params: [{ name: IMAGE, value: '$(params.image):$(params.sha)' }]
    - name: deploy
      runAfter: [scan]
      taskRef: { name: helm-upgrade }
      params: [{ name: chart, value: ./charts/web }, { name: image-tag, value: '$(params.sha)' }]
```

Tekton 优势：

- K8s 原生 CRD (Pipeline / Task / TaskRun / PipelineRun)
- 容器内任务并行
- 完整资源审计
- 配 ArgoCD + Argo Events 完美闭环

## 三、镜像构建深度（CI 内）

### 3.1 三大方案对比

| 方案 | 守护进程 | 安全 | 速度 | 适用 |
|:---|:---:|:---:|:---:|:---|
| **docker-in-docker** | ✓ | ⚠️ | 中 | 老 Jenkins |
| **Kaniko** ⭐ | ✗ | ⭐⭐⭐⭐ | 中 | K8s 内通用 |
| **Buildah** ⭐ | ✗ | ⭐⭐⭐⭐⭐ | 快 | 红帽栈 |
| **BuildKit Pod** ⭐ | ✗ | ⭐⭐⭐⭐ | 极快 | rootless |
| **img** | ✗ | ⭐⭐⭐ | 中 | 小众 |
| **nerdctl + containerd** | ✓ | ⭐⭐⭐⭐ | 极快 | 新栈 |

### 3.2 Kaniko（K8s 内推荐）

```yaml
apiVersion: v1
kind: Pod
metadata: { name: build-web }
spec:
  containers:
    - name: kaniko
      image: gcr.io/kaniko-project/executor:latest
      args:
        - --dockerfile=Dockerfile
        - --context=git://gitlab.example.com/web.git#refs/heads/main
        - --destination=harbor.example.com/web/api:$(SHA)
        - --cache=true
        - --cache-repo=harbor.example.com/cache/web
      volumeMounts: [{ name: docker-config, mountPath: /kaniko/.docker }]
  volumes:
    - name: docker-config
      secret: { secretName: harbor-cred }
```

### 3.3 BuildKit Pod（rootless + 多架构）

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: buildkitd, namespace: ci }
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: buildkitd
          image: moby/buildkit:latest-rootless
          args: ["--addr", "unix:///run/user/1000/buildkit/buildkitd.sock", "--oci-worker-no-process-sandbox"]
          securityContext: { runAsUser: 1000, runAsGroup: 1000 }
```

```bash
buildctl --addr kube-pod://buildkitd build \
  --frontend dockerfile.v0 \
  --opt platform=linux/amd64,linux/arm64 \
  --local context=. --local dockerfile=. \
  --output type=image,name=harbor.example.com/web/api:$SHA,push=true
```

### 3.4 远程缓存策略

```
方案:
  type=registry,ref=harbor.example.com/cache/web:main  ⭐
  type=gha (GitHub Actions)
  type=s3 (AWS)
  type=inline (镜像层内嵌)

实测加速:
  无缓存: 5 min
  Layer cache: 2 min
  Buildx registry cache: 30s ⭐
```

## 四、秘密治理

### 4.1 方案对比

| 方案 | 加密 | K8s 集成 | 旋转 | 国产 |
|:---|:---:|:---:|:---:|:---:|
| **HashiCorp Vault** ⭐ | 强 | external-secrets | 强 | 商业 (开源 BSL) |
| **External Secrets Operator** ⭐ | - | ⭐⭐⭐⭐⭐ | - | - |
| **SealedSecrets** | 弱 | ⭐⭐⭐⭐ | 弱 | - |
| **SOPS + KMS** | 强 | helm-secrets | 中 | - |
| **Sealed Secrets + age** | 中 | ⭐⭐⭐ | 弱 | - |
| **AWS Secrets Manager** | 强 | ⭐⭐⭐⭐ | 强 | - |
| **CyberArk Conjur** | 强 | ⭐⭐⭐ | 强 | - |
| **百度 BSM / 华为 KPS / 阿里 KMS** | 强 | ⭐⭐⭐ | 强 | ⭐⭐⭐⭐⭐ |
| **国密 Tongsuo / 阿里加密机 / 海光 CSV** | 强 | - | - | ⭐⭐⭐⭐⭐ |

### 4.2 Vault + External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata: { name: vault, namespace: prod }
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "prod-app"
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata: { name: db-creds, namespace: prod }
spec:
  refreshInterval: "1h"
  secretStoreRef: { name: vault, kind: SecretStore }
  target: { name: db-creds }
  data:
    - secretKey: username
      remoteRef: { key: prod/db, property: username }
    - secretKey: password
      remoteRef: { key: prod/db, property: password }
```

### 4.3 SOPS

```bash
# 用 KMS / age / GPG 加密 YAML
sops --encrypt --age age1xxxxxxxx values.secret.yaml > values.secret.enc.yaml

# CI 内解密
sops --decrypt values.secret.enc.yaml | helm upgrade --install web ./web -f -
```

配 helm-secrets / sops-edit 插件。

## 五、IaC 进阶

### 5.1 Terraform Cloud / Atlantis

```yaml
# Atlantis (PR-driven Terraform)
# atlantis.yaml
version: 3
projects:
  - name: vpc
    dir: terraform/vpc
    workflow: prod
    autoplan: { when_modified: ["*.tf"], enabled: true }
workflows:
  prod:
    plan:
      steps: [init, plan]
    apply:
      steps: [apply]
```

PR comment：

```
atlantis plan      → CI 自动 terraform plan
atlantis apply     → 评审后 apply
```

### 5.2 Terragrunt（多环境复用）

```
terragrunt/
  prod/
    vpc/terragrunt.hcl
    eks/terragrunt.hcl
  staging/
    vpc/terragrunt.hcl
    eks/terragrunt.hcl
  modules/  ← 真正的 .tf
```

### 5.3 Crossplane（基础设施即 K8s CRD）

```yaml
apiVersion: ec2.aws.crossplane.io/v1alpha1
kind: VPC
metadata: { name: prod-vpc }
spec:
  forProvider:
    region: cn-northwest-1
    cidrBlock: "10.0.0.0/16"
  providerConfigRef: { name: aws-prod }
```

```yaml
# Composition (多资源打包)
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata: { name: postgres-aws }
spec:
  compositeTypeRef: { apiVersion: db.example.com/v1, kind: XPostgres }
  resources:
    - { name: rds, base: { apiVersion: rds.aws.crossplane.io/v1alpha1, kind: DBInstance, ... } }
    - { name: sg,  base: { apiVersion: ec2.aws.crossplane.io/v1alpha1, kind: SecurityGroup, ... } }
```

### 5.4 Pulumi（用编程语言）

```typescript
import * as aws from "@pulumi/aws";
const vpc = new aws.ec2.Vpc("main", { cidrBlock: "10.0.0.0/16" });
const subnet = new aws.ec2.Subnet("a", { vpcId: vpc.id, cidrBlock: "10.0.1.0/24" });
```

## 六、Policy as Code

### 6.1 OPA / Conftest（CI 内策略）

```rego
# policy/k8s-no-latest.rego
package main

deny[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  endswith(container.image, ":latest")
  msg := sprintf("Deployment '%s' uses :latest tag", [input.metadata.name])
}

deny[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.resources.limits
  msg := sprintf("Container '%s' missing resource limits", [container.name])
}
```

```bash
conftest test deploy.yaml
```

CI 内强卡：

```yaml
policy:
  stage: validate
  script:
    - conftest test --policy ./policy charts/web/templates/
```

### 6.2 Kyverno / Gatekeeper（集群准入）

```yaml
# Kyverno (易用) ⭐
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: enforce-resources }
spec:
  validationFailureAction: Enforce
  rules:
    - name: require-resources
      match: { any: [{ resources: { kinds: [Pod] } }] }
      validate:
        message: "Resources required"
        pattern:
          spec:
            containers:
              - resources:
                  requests: { cpu: "?*", memory: "?*" }
                  limits:   { memory: "?*" }
```

```yaml
# Gatekeeper (OPA) (功能强、学习曲线陡)
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata: { name: k8srequiredlabels }
spec:
  crd: { spec: { names: { kind: K8sRequiredLabels } } }
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        violation[{"msg": msg}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("missing labels: %v", [missing])
        }
```

## 七、SBOM + 签名 + SLSA

### 7.1 syft 生成 SBOM

```bash
syft harbor.example.com/web/api:v1.2.3 -o spdx-json > sbom.json
syft harbor.example.com/web/api:v1.2.3 -o cyclonedx-xml > sbom.xml
```

### 7.2 cosign 签名 + 附 SBOM

```bash
cosign generate-key-pair k8s://prod/cosign
cosign sign --key cosign.key harbor.example.com/web/api:v1.2.3
cosign attach sbom --sbom sbom.json harbor.example.com/web/api:v1.2.3
cosign verify --key cosign.pub harbor.example.com/web/api:v1.2.3
```

### 7.3 SLSA Provenance

```bash
# 用 slsa-github-generator 或 Tekton Chains 自动生成
# 输出 in-toto attestation
cosign attest --predicate provenance.json --key cosign.key harbor.example.com/web/api:v1.2.3
cosign verify-attestation --key cosign.pub --type slsaprovenance harbor.example.com/web/api:v1.2.3
```

### 7.4 准入卡控

```yaml
# Kyverno verifyImages
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: verify-signature }
spec:
  validationFailureAction: Enforce
  rules:
    - name: verify-images
      match: { any: [{ resources: { kinds: [Pod] } }] }
      verifyImages:
        - imageReferences: ["harbor.example.com/*"]
          attestors:
            - entries: [{ keys: { publicKeys: |
                -----BEGIN PUBLIC KEY-----
                MFkwEwYHKoZIzj0CA...
                -----END PUBLIC KEY-----
              } }]
```

或 sigstore policy-controller（Cosign 官方控制器）。

## 八、DORA 度量

### 8.1 工具

```
开源:    DevLake (Apache) ⭐ 一站采集 GitLab/Jenkins/Jira
        Pelorus (Red Hat)
        Sleuth / LinearB / Jellyfish (SaaS)
        
自研:    GitLab API + Prometheus + Grafana
```

### 8.2 必看大盘

```
1. 部署频率           Deploys/Day
2. Lead Time          PR Open → Prod
3. Change Fail Rate   prod incidents / deploys
4. MTTR               故障 → 恢复
5. Cycle Time         Issue → Done
6. PR Size            Avg lines per PR
7. Code Review Time   PR Open → Review
8. CI Duration P95    每 job
9. CI Pass Rate
10. Flaky Tests
```

## 九、Pipeline 模板（团队基线）

### 9.1 标准流水线分阶段

```
1. Lint            (语法/格式 → 1-2min)
2. Unit Test       (并行 → 3-5min)
3. Static Scan     (SonarQube + 安全扫描 + License)
4. Build           (Buildx + Cache → 30s-2min)
5. Image Scan      (Trivy + Grype 双扫)
6. Sign + SBOM     (cosign + syft)
7. Integration     (TestContainers + 服务集成)
8. Push            (Harbor)
9. Deploy Dev      (ArgoCD 自动)
10. Smoke Test     (E2E 关键路径)
11. Deploy Staging (ArgoCD 自动)
12. E2E Test       (Cypress / Playwright)
13. Deploy Prod    (Canary via Argo Rollouts)
14. Monitor        (Prometheus + Loki)
15. Notify         (钉钉/飞书 + 审计入仓)
```

### 9.2 标准 Gates（卡控点）

```
Lint:        失败立止
Unit:        Coverage > 70%
Static:      SonarQube Pass + 0 CRITICAL
Image Scan:  Trivy HIGH+CRITICAL = 0
SBOM:        必生成
Signature:   必签名 (cosign)
Integration: Pass
Deploy Prod: 人工 + change ticket
```

## 十、国产化 DevOps 栈

### 10.1 主流方案

```
GitLab CE/EE + Jenkins  ⭐ 自建主流
极狐 GitLab              GitLab 中国版 (合规)
华为 CodeArts            全栈 SaaS / 私有 (代码+流水线+发布+测试)
阿里云效                  全栈 SaaS (Codeup + Flow)
腾讯 Coding              SaaS
京东行云                  SaaS
KubeSphere DevOps ⭐     K8s 内置 (Jenkins + Tekton + ArgoCD)
```

### 10.2 国产开源

```
代码:       Gitea / Forgejo (Go 系)
CI:         JenkinsX / Tekton (国产社区)
镜像:       Harbor ⭐ (国产开源王者)
ArgoCD/Flux GitOps
夜莺监控 + DeepFlow eBPF
KubeSphere DevOps 一站式
```

## 十一、典型坑（进阶）

| 坑 | 建议 |
|:---|:---|
| **CI 跑全量 E2E** | 分层 (单元/集成/E2E) + 并行 |
| **ArgoCD app-of-apps 没拆** | ApplicationSet + 分项目 |
| **Image Updater 跟 :latest** | semver / digest 策略 |
| **Rollouts 没 AnalysisTemplate** | 必接 Prometheus / Datadog |
| **Tekton 任务无 retry** | retries: 2 + timeout 必加 |
| **Kaniko OOM** | resources + 大缓存 PVC |
| **Vault 单节点** | Raft 3 副本 + auto-unseal |
| **SOPS 多人协作冲突** | 拆文件 / 按服务 |
| **Terraform state 锁竞争** | S3 + DynamoDB 锁 / GCS + Tofu |
| **Crossplane CRD 爆炸** | Composition 抽象 + 限 API surface |
| **OPA/Kyverno 误杀** | Audit mode 先开 30 天 |
| **cosign key 在 git** | KMS / k8s://prod/cosign |
| **没 SLSA provenance** | 强制 Tekton Chains 自动 |
| **DORA 无数据** | DevLake / 自采 必装 |

## 十二、Checklist（进阶）

```
GitOps:
☐ ArgoCD + ApplicationSet 多环境多集群
☐ Image Updater (semver / digest)
☐ Argo Rollouts (Canary + AnalysisTemplate)
☐ Argo Workflows (任务 / 训练 pipeline)

流水线:
☐ Tekton 或 GitLab CI 云原生
☐ 多 stage gates 卡控
☐ Buildx + 远程缓存
☐ Kaniko / BuildKit Pod (K8s 内构建)

秘密:
☐ Vault Raft HA + auto-unseal
☐ External Secrets Operator
☐ SOPS + KMS (Git 内加密)
☐ SealedSecrets 备选

IaC:
☐ Terraform 模块化 + 远端 state + 锁
☐ Atlantis / TF Cloud PR-driven
☐ Terragrunt 多环境
☐ Crossplane K8s 内 IaC (可选)
☐ Pulumi 编程语言 IaC (团队选)

策略:
☐ Conftest CI 内 OPA
☐ Kyverno / Gatekeeper K8s 准入
☐ 必须策略全覆盖 (resources/probe/registry/sig)

供应链:
☐ Trivy + Grype 双扫
☐ syft 生成 SBOM
☐ cosign 签名 + KMS 密钥
☐ SLSA Provenance (Tekton Chains / GitHub OIDC)
☐ verify-images 准入

度量:
☐ DevLake / Pelorus
☐ DORA 4 指标 + cycle time
☐ Grafana 全大盘
☐ CI duration P95 / pass rate / flaky

国产:
☐ Harbor 国密 TLS
☐ KubeSphere DevOps / 华为 CodeArts / 阿里云效 一种
☐ GitLab 极狐 (合规版)
☐ DeepFlow / 夜莺监控
```

## 十三、推荐栈（进阶）

```
代码:       GitLab EE ⭐ / 极狐 / Gitea / Forgejo
CI:         GitLab CI ⭐ / Tekton ⭐ / Jenkins / GitHub Actions
镜像构建:   Buildx + Kaniko / Buildah / BuildKit Pod
镜像仓库:   Harbor ⭐ (+ 国密 TLS)
GitOps:     ArgoCD ⭐ + ApplicationSet + Image Updater + Rollouts + Workflows
IaC:        Terraform + Atlantis + Terragrunt / Crossplane / Pulumi
秘密:       Vault + External Secrets Operator (+ SOPS)
策略:       Conftest (CI) + Kyverno (K8s) ⭐
供应链:     Trivy + Grype + syft + cosign + sigstore policy-controller
度量:       DevLake ⭐ / Prometheus + Grafana
平台:       KubeSphere DevOps / Backstage / Port
通知:       钉钉 / 飞书 / 企微 / 邮件 / Webhook
```

> 📖 **核心判断**：DevOps 进阶 = **GitOps 全链(ArgoCD ApplicationSet + Image Updater + Rollouts + Workflows) + Tekton 云原生流水线 + Kaniko/BuildKit Pod 安全构建 + Vault+ESO+SOPS 秘密治理 + Terraform+Atlantis+Crossplane IaC + OPA+Kyverno 策略 + 供应链(Trivy+SBOM+cosign+SLSA) + DORA 度量 + 国产化栈**。能搭出 Git→Tekton/GitLab→Harbor+签名+SBOM→ArgoCD→Argo Rollouts→Vault+ESO→DevLake DORA→Kyverno 全链闭环，就具备 DevOps 平台工程师能力。
