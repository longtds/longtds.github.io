# 基础

> DevOps 基础 = **理念(CALMS/DORA) + Git 工作流 + Jenkins/GitLab CI/CD 基础 + 构建 + 镜像 + 部署 + 简单 IaC**。本章面向入职 1 年内的工程师。

## 一、DevOps 理念

```
CALMS:
  Culture       文化
  Automation    自动化
  Lean          精益
  Measurement   度量
  Sharing       共享

DORA 4 大指标 (DevOps 业界事实标准):
  1. 部署频率 (Deployment Frequency)
  2. 变更前置时间 (Lead Time for Changes)
  3. 变更失败率 (Change Failure Rate)
  4. 故障恢复时间 (MTTR)

精英团队基准:
  - 部署: 按需 (每天多次)
  - 前置: < 1 小时
  - 失败率: < 15%
  - MTTR: < 1 小时
```

## 二、Git 工作流

### 2.1 主流策略

```
GitFlow:           长分支 (master/develop/feature/release/hotfix)
                   适合版本发布型 (季度发版)

GitHub Flow:       master + feature PR
                   简单, 适合持续部署 ⭐

GitLab Flow:       master + production 分支 / env 分支
                   适合多环境

Trunk-Based:       all commits → trunk
                   feature flag 控制可见性
                   超高速团队 (Google/FB) ⭐⭐
```

### 2.2 Trunk-Based 推荐

```
1 个长期分支 main + 短期 feature/* (< 2 天)
PR 必走 + CI 必绿
Feature Flag 隔离未完成功能
小步快跑, 每天合并
配合 Tags / Release 发版
```

### 2.3 Commit 规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：

```
feat:     新功能
fix:      Bug 修复
docs:     文档
style:    格式
refactor: 重构
perf:     性能
test:     测试
chore:    构建/工具链
ci:       CI 配置
revert:   回滚
```

工具：commitizen / commitlint / conventional-changelog。

## 三、CI/CD 基础

### 3.1 流水线分层

```
CI (Continuous Integration):
  Lint → Unit Test → Build → Scan → Image Push → Notify

CD (Continuous Delivery):
  Deploy Dev → Test → Deploy Staging → 人工 → Deploy Prod

CD (Continuous Deployment):
  Deploy Dev → Test → Deploy Staging → 自动 Prod (无人工)
```

### 3.2 Jenkins 经典声明式

```groovy
pipeline {
  agent { label 'docker' }
  options { timeout(time: 30, unit: 'MINUTES'); ansiColor('xterm') }
  environment {
    REGISTRY = 'harbor.example.com'
    IMAGE    = "${REGISTRY}/web/api"
  }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Lint')     { steps { sh 'make lint' } }
    stage('Test')     { steps { sh 'make test' } }
    stage('Build')    {
      steps {
        sh "docker build -t ${IMAGE}:${GIT_COMMIT[0..7]} ."
        sh "docker tag ${IMAGE}:${GIT_COMMIT[0..7]} ${IMAGE}:latest"
      }
    }
    stage('Scan')     { steps { sh "trivy image --severity HIGH,CRITICAL --exit-code 1 ${IMAGE}:${GIT_COMMIT[0..7]}" } }
    stage('Push')     {
      steps {
        withCredentials([usernamePassword(credentialsId: 'harbor', usernameVariable: 'U', passwordVariable: 'P')]) {
          sh "docker login -u $U -p $P ${REGISTRY}"
          sh "docker push ${IMAGE}:${GIT_COMMIT[0..7]}"
        }
      }
    }
    stage('Deploy')   {
      when { branch 'main' }
      steps {
        sh "helm upgrade --install web ./charts/web -n web --set image.tag=${GIT_COMMIT[0..7]}"
      }
    }
  }
  post {
    success { dingTalk accessToken: 'xxx', text: "✅ ${env.JOB_NAME} #${env.BUILD_NUMBER}" }
    failure { dingTalk accessToken: 'xxx', text: "❌ ${env.JOB_NAME} #${env.BUILD_NUMBER}" }
  }
}
```

### 3.3 GitLab CI

```yaml
stages: [lint, test, build, scan, deploy]

variables:
  IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

lint:
  stage: lint
  script: [make lint]

test:
  stage: test
  script: [make test]
  artifacts: { reports: { junit: junit.xml, coverage_report: { coverage_format: cobertura, path: cov.xml } } }

build:
  stage: build
  script:
    - docker build -t $IMAGE .
    - docker push $IMAGE
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

scan:
  stage: scan
  script:
    - trivy image --severity HIGH,CRITICAL --exit-code 1 $IMAGE
  allow_failure: false

deploy_dev:
  stage: deploy
  script:
    - helm upgrade --install web ./charts/web -n dev --set image.tag=$CI_COMMIT_SHORT_SHA
  environment: { name: dev, url: https://dev.example.com }
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy_prod:
  stage: deploy
  script:
    - helm upgrade --install web ./charts/web -n prod --set image.tag=$CI_COMMIT_SHORT_SHA
  environment: { name: prod }
  when: manual
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
```

### 3.4 GitHub Actions

```yaml
name: CI
on:
  push: { branches: [main] }
  pull_request:

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with: { go-version: '1.22' }
      - run: make lint test
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }} }
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
          severity: HIGH,CRITICAL
          exit-code: '1'
```

### 3.5 国产 CI 选项

```
GitLab CE/EE        国内自建主流 ⭐
Jenkins             经典 (Pipeline + Blue Ocean)
TektonCD            K8s 原生
Drone CI            轻量
Gitea + Drone       全开源轻量
极狐 GitLab         合规版
Coding (腾讯)       SaaS
华为 CodeArts       全栈 DevOps
阿里云效            SaaS / 私有
```

## 四、构建 & 镜像

### 4.1 多阶段 Dockerfile（基础）

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/app ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /out/app /app
USER nonroot
EXPOSE 8080
ENTRYPOINT ["/app"]
```

### 4.2 Buildx 缓存（CI 内）

```bash
docker buildx create --use --name ci
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --cache-from type=registry,ref=$REGISTRY/cache/web:main \
  --cache-to   type=registry,ref=$REGISTRY/cache/web:main,mode=max \
  --tag $REGISTRY/web:$SHA \
  --push .
```

### 4.3 镜像规范

```
☐ 不可变 tag (sha / vX.Y.Z, 禁 :latest)
☐ distroless / wolfi / alpine 基础
☐ multi-stage 分离 builder 和 runtime
☐ 非 root USER
☐ HEALTHCHECK / ENTRYPOINT exec form
☐ .dockerignore (.git/node_modules)
```

## 五、部署 & 包管

### 5.1 Helm

```bash
helm create web
helm lint web/
helm template web/ --debug > out.yaml
helm upgrade --install web ./web -n web -f values-prod.yaml --atomic --wait --timeout 5m
helm history web -n web
helm rollback web 3 -n web
```

```yaml
# values-prod.yaml
replicaCount: 3
image: { repository: harbor.example.com/web, tag: v1.2.3 }
resources:
  requests: { cpu: 100m, memory: 128Mi }
  limits:   { cpu: 500m, memory: 512Mi }
ingress: { host: web.prod.example.com }
```

### 5.2 Kustomize

```
base/
  deployment.yaml
  service.yaml
  kustomization.yaml
overlays/
  dev/
    kustomization.yaml
    patch-replicas.yaml
  prod/
    kustomization.yaml
    patch-prod.yaml
```

```bash
kubectl apply -k overlays/prod
```

### 5.3 ArgoCD（GitOps 入门）

```bash
helm install argocd argo/argo-cd -n argocd --create-namespace
argocd app create web --repo https://gitlab/.../infra.git --path overlays/prod \
  --dest-server https://kubernetes.default.svc --dest-namespace web \
  --sync-policy automated --auto-prune --self-heal
```

GitOps 核心：

```
源:  Git
工:  ArgoCD / Flux
目:  K8s 集群
循:  reconcile
赢:  审计 / 回滚 / 多集群 / 一致性
```

## 六、IaC（基础）

### 6.1 Ansible

```yaml
- hosts: webservers
  become: yes
  tasks:
    - name: install nginx
      apt: { name: nginx, state: present, update_cache: yes }
    - name: deploy config
      template: { src: nginx.conf.j2, dest: /etc/nginx/nginx.conf }
      notify: restart nginx
    - name: enable + start
      systemd: { name: nginx, enabled: yes, state: started }
  handlers:
    - name: restart nginx
      systemd: { name: nginx, state: restarted }
```

### 6.2 Terraform（基础）

```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" { region = "cn-northwest-1" }

resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }
resource "aws_subnet" "a" { vpc_id = aws_vpc.main.id, cidr_block = "10.0.1.0/24" }

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"
  cluster_name = "prod"
  cluster_version = "1.30"
  vpc_id = aws_vpc.main.id
  subnet_ids = [aws_subnet.a.id]
  eks_managed_node_groups = {
    default = { instance_types = ["m5.large"], min_size = 2, max_size = 10, desired_size = 3 }
  }
}
```

## 七、入门 20 题

```
1.  DevOps vs SRE
2.  CI vs CD vs Continuous Deployment
3.  DORA 4 指标
4.  GitFlow vs GitHub Flow vs GitLab Flow vs Trunk-Based
5.  Conventional Commits / SemVer
6.  Jenkins Declarative vs Scripted
7.  GitLab CI vs GitHub Actions vs Jenkins
8.  Build Cache vs Layer Cache
9.  Helm vs Kustomize
10. 多阶段 Dockerfile 用途
11. distroless 是什么
12. ArgoCD vs Flux
13. GitOps 三件套
14. Canary vs Blue/Green vs RollingUpdate
15. Feature Flag 用途
16. Ansible vs Terraform 区别
17. Trivy / cosign / SBOM 用途
18. Pipeline as Code 优势
19. Secrets 怎么管 (Vault / Sealed / SOPS)
20. Pipeline 失败常见原因
```

## 八、典型坑（基础）

| 坑 | 建议 |
|:---|:---|
| **CI 跑全量测试 1 小时** | 单元/集成/E2E 分层 |
| **Build 没 cache** | Buildx + 远程缓存 |
| **镜像 1GB+** | 多阶段 + distroless |
| **密码硬编码** | Vault / SealedSecrets / SOPS |
| **手 kubectl apply** | GitOps ArgoCD |
| **没回滚机制** | helm rollback / Git revert |
| **CI 用 root** | rootless / DinD 用 BuildKit Pod |
| **环境只在 prod 测** | dev/staging/prod 三环境 |
| **配置在镜像里** | ConfigMap / 环境变量 |
| **JVM 没 UseContainerSupport** | -XX:MaxRAMPercentage=75 |

## 九、推荐栈（基础）

```
代码托管:    GitLab CE / Gitea / GitHub
CI:         GitLab CI ⭐ / Jenkins / GitHub Actions / Tekton
镜像:       Harbor + Buildx + Trivy + cosign
包管:       Helm ⭐ / Kustomize
部署:       ArgoCD ⭐ / Flux
IaC:        Terraform ⭐ + Ansible
秘密:       Vault ⭐ / SealedSecrets / SOPS
通知:       钉钉 / 飞书 / 企微 / 邮件 / Slack
```

## 十、学习路径

```
入门（1-3 月）:
  1. Git 工作流 (Trunk-Based)
  2. Jenkins / GitLab CI 写一条 Pipeline (lint+test+build+push+deploy)
  3. Helm 一遍 (lint/template/install/upgrade/rollback)
  4. ArgoCD 部署一个应用
  5. Trivy 扫描 + cosign 签名
  6. Vault / SealedSecrets 一种
  7. Terraform 创一个 VPC / K8s 集群
  8. Ansible 写一个 nginx 部署
  9. 20 题过一遍

进阶（3-12 月，见 02_进阶）:
  10. 镜像构建加速 (BuildKit / Kaniko / Buildah)
  11. 多环境 GitOps (ApplicationSet)
  12. 渐进式发布 (Argo Rollouts)
  13. Policy as Code (OPA / Kyverno)
```

> 📖 **核心判断**：DevOps 基础 = **理念(DORA) + Git 工作流 + Jenkins/GitLab CI/CD + 多阶段构建 + Helm + ArgoCD + Vault + Terraform/Ansible**。能在团队里搭出"Git → CI(lint+test+build+scan) → Harbor → ArgoCD → K8s → 钉钉通知"全链，就具备 DevOps 入门能力。
