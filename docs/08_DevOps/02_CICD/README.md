# CI/CD

> 从代码提交到生产可用的全链路自动化。**没有 CI/CD = 没有 DevOps**。2025 CI/CD 已从"跑跑测试"演进为"代码安全 + 构建 + 镜像 + 测试 + 部署 + 验证 + 回滚"一站式平台。

## 一、CI/CD 全景

```
CI (Continuous Integration)
  代码合入 → 自动构建 + 测试
  目标: 每次 commit 都可发布
  
CD (Continuous Delivery)
  自动构建产物，等审批后部署
  
CD (Continuous Deployment)
  自动构建 + 自动部署（全自动）
  
DevSecOps
  CI/CD + 安全扫描 + 合规检查
  
GitOps
  Git 即真理源，集群状态由 Git 驱动
```

## 二、CI/CD 工具全景

### 2.1 主流工具对比

| 工具 | 类型 | 部署 | K8s | 国内主流 | 推荐 |
|:---|:---|:---|:---:|:---:|:---:|
| **Jenkins** | 经典 | 自建 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **GitLab CI** | 一体化 | 自建/SaaS | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **GitHub Actions** | SaaS | 托管 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Tekton** | K8s 原生 | K8s | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Argo Workflows** | K8s 原生 | K8s | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Drone CI** | 容器原生 | 自建 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Buildkite** | 商业 | Hybrid | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **CircleCI / Travis** | SaaS | 托管 | ⭐⭐⭐ | ⭐ | ⭐⭐ |
| **Woodpecker** | 开源 | 自建 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **AWS CodePipeline** | 云原生 | AWS | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| **阿里云效 Flow** | 国产 | SaaS | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **腾讯 CODING** | 国产 | SaaS | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### 2.2 2025 选型建议（按场景）

```
传统企业 / 强自建:        Jenkins + Harbor + Nexus
中小团队 / 一体化:        GitLab CE/EE 全家桶
开源 / GitHub 生态:       GitHub Actions
K8s First / 云原生:       Tekton + Argo CD
混合栈 / 国产化:          Jenkins + 国产替代品
跨国 / 多云:              GitHub Actions + Argo CD
极简 / 个人项目:          Drone CI / Woodpecker
```

## 三、Jenkins（国内仍是主流）

### 3.1 为什么国内还是 Jenkins

```
✅ 私有化部署
✅ 插件生态最丰富（1800+）
✅ 中文文档 + 培训成熟
✅ 与传统中间件兼容好
✅ 信创可适配
❌ 维护重 + 配置散乱
❌ 安全洞百出
❌ K8s 集成不如新工具
```

### 3.2 Jenkins 推荐架构（2025）

```
✅ Jenkins Controller + Cloud Agent
  - Controller 单点（HA 用 OpenShift / 自研双 master）
  - Agent on K8s（按需创建 Pod）
  - Agent on 物理机（构建机器学习镜像等重负载）

✅ Pipeline as Code
  - Jenkinsfile 入 Git
  - Multibranch Pipeline 自动扫描
  - 共享库（Shared Library）

✅ 配置即代码
  - JCasC (Configuration as Code)
  - 用 YAML 管 Jenkins 自身

✅ 安全
  - Role-Based Access Control
  - Credentials + Vault 集成
  - Audit Trail
```

### 3.3 Jenkinsfile 完整示例

```groovy
@Library('shared-pipeline-lib@v2.0') _

pipeline {
  agent {
    kubernetes {
      yaml """
        apiVersion: v1
        kind: Pod
        spec:
          containers:
          - name: maven
            image: maven:3.9-eclipse-temurin-21
            command: ['sleep']
            args: ['9999999']
          - name: docker
            image: gcr.io/kaniko-project/executor:debug
            command: ['sleep']
            args: ['9999999']
          - name: kubectl
            image: bitnami/kubectl:1.30
            command: ['sleep']
            args: ['9999999']
      """
    }
  }
  
  options {
    timeout(time: 30, unit: 'MINUTES')
    timestamps()
    ansiColor('xterm')
    buildDiscarder(logRotator(numToKeepStr: '20'))
    disableConcurrentBuilds()
  }
  
  environment {
    APP_NAME = 'order-api'
    REGISTRY = 'harbor.company.com/apps'
    VAULT_ADDR = 'https://vault.company.com'
  }
  
  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          env.COMMIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
          env.IMAGE_TAG = "${env.BRANCH_NAME}-${env.COMMIT_SHA}-${env.BUILD_NUMBER}"
        }
      }
    }
    
    stage('Lint & Security') {
      parallel {
        stage('SonarQube') {
          steps { sh 'mvn sonar:sonar' }
        }
        stage('Trivy FS') {
          steps { sh 'trivy fs --severity HIGH,CRITICAL --exit-code 1 .' }
        }
        stage('Secret Scan') {
          steps { sh 'gitleaks detect --no-git' }
        }
      }
    }
    
    stage('Build & Test') {
      steps {
        container('maven') {
          sh 'mvn -B clean verify -P prod'
        }
      }
      post {
        always {
          junit '**/target/surefire-reports/*.xml'
          publishCoverage adapters: [jacocoAdapter('**/target/site/jacoco/jacoco.xml')]
        }
      }
    }
    
    stage('Build Image') {
      steps {
        container('docker') {
          sh """
            /kaniko/executor \
              --context=. \
              --destination=${REGISTRY}/${APP_NAME}:${IMAGE_TAG} \
              --cache=true \
              --cache-repo=${REGISTRY}/cache \
              --reproducible
          """
        }
      }
    }
    
    stage('Image Scan') {
      steps {
        sh "trivy image --severity HIGH,CRITICAL --exit-code 1 ${REGISTRY}/${APP_NAME}:${IMAGE_TAG}"
      }
    }
    
    stage('Sign & SBOM') {
      steps {
        sh "cosign sign --key vault://kv/cosign ${REGISTRY}/${APP_NAME}:${IMAGE_TAG}"
        sh "syft ${REGISTRY}/${APP_NAME}:${IMAGE_TAG} -o spdx-json > sbom.json"
        archiveArtifacts 'sbom.json'
      }
    }
    
    stage('Deploy Staging') {
      when { branch 'main' }
      steps {
        container('kubectl') {
          sh """
            kubectl --context=stg \
              set image deploy/${APP_NAME} ${APP_NAME}=${REGISTRY}/${APP_NAME}:${IMAGE_TAG} \
              -n staging
            kubectl --context=stg rollout status deploy/${APP_NAME} -n staging --timeout=5m
          """
        }
      }
    }
    
    stage('Smoke Test') {
      when { branch 'main' }
      steps {
        sh 'curl -fsS https://stg.api.company.com/order/healthz'
        sh 'pytest tests/smoke/ --base-url=https://stg.api.company.com'
      }
    }
    
    stage('Deploy Prod') {
      when { branch 'main' }
      input {
        message '上线生产？'
        ok 'Deploy'
        submitter 'sre-lead,platform-team'
      }
      steps {
        // Push Git tag → Argo CD 自动同步
        sh "git tag prod-${IMAGE_TAG} && git push origin prod-${IMAGE_TAG}"
      }
    }
  }
  
  post {
    success {
      wechatNotify('🎉 ${APP_NAME} ${IMAGE_TAG} 部署成功')
    }
    failure {
      wechatNotify('❌ ${APP_NAME} ${IMAGE_TAG} 失败 → ${BUILD_URL}')
    }
  }
}
```

### 3.4 Jenkins 共享库

```groovy
// shared-pipeline-lib/vars/wechatNotify.groovy
def call(String msg) {
  httpRequest(
    httpMode: 'POST',
    url: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx',
    requestBody: "{\"msgtype\":\"markdown\",\"markdown\":{\"content\":\"${msg}\"}}",
    contentType: 'APPLICATION_JSON'
  )
}

// shared-pipeline-lib/vars/buildAndPush.groovy
def call(Map config) {
  // 通用构建逻辑
}
```

### 3.5 JCasC（配置即代码）

```yaml
# jenkins.yaml
jenkins:
  systemMessage: "Jenkins managed by JCasC"
  numExecutors: 0       # Controller 不跑任务
  scmCheckoutRetryCount: 3
  authorizationStrategy:
    roleBased:
      roles:
        global:
          - name: admin
            permissions: [Overall/Administer]
            assignments: [sre-team]
  securityRealm:
    ldap:
      configurations:
        - server: ldap://ldap.company.com
          rootDN: dc=company,dc=com

unclassified:
  location:
    url: https://jenkins.company.com/
  globalLibraries:
    libraries:
      - name: shared-pipeline-lib
        defaultVersion: main
        retriever:
          modernSCM:
            scm:
              git:
                remote: git@github.com:company/jenkins-shared-lib.git
```

## 四、GitLab CI（一体化首选）

### 4.1 为什么选 GitLab CI

```
✅ 代码 + CI + Registry + Pages + Wiki 一站式
✅ 私有化部署成熟
✅ 国内大厂大量在用
✅ Runner 灵活（Docker / K8s / Shell）
✅ 多项目继承（include/extends）
✅ Auto DevOps（开箱即用）
```

### 4.2 完整 .gitlab-ci.yml 示例

```yaml
include:
  - project: 'platform/ci-templates'
    file: '/security/sast.yml'
  - project: 'platform/ci-templates'
    file: '/security/trivy.yml'

variables:
  APP_NAME: order-api
  REGISTRY: harbor.company.com/apps
  IMAGE: $REGISTRY/$APP_NAME:$CI_COMMIT_SHORT_SHA

stages:
  - lint
  - build
  - test
  - scan
  - package
  - deploy
  - verify

# Lint
lint:
  stage: lint
  image: golangci/golangci-lint:latest
  script:
    - golangci-lint run ./...

# Build
build:
  stage: build
  image: golang:1.22
  script:
    - go build -o bin/server ./cmd/server
  artifacts:
    paths: [bin/]
    expire_in: 1 day
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths: [.cache/go-build, .cache/go-mod]

# Test
unit-test:
  stage: test
  image: golang:1.22
  script:
    - go test -race -coverprofile=coverage.out ./...
    - go tool cover -func=coverage.out
  coverage: '/total:\s+\(statements\)\s+(\d+\.\d+)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

# Security Scan
sast:
  stage: scan
  extends: .sast

container-scan:
  stage: scan
  extends: .trivy-image
  needs: [package-image]

dependency-scan:
  stage: scan
  image: aquasec/trivy:latest
  script:
    - trivy fs --severity HIGH,CRITICAL --exit-code 1 .

secret-scan:
  stage: scan
  image: zricethezav/gitleaks:latest
  script:
    - gitleaks detect --no-git --verbose

# Build image
package-image:
  stage: package
  image:
    name: gcr.io/kaniko-project/executor:debug
    entrypoint: [""]
  script:
    - mkdir -p /kaniko/.docker
    - echo "{\"auths\":{\"$REGISTRY\":{\"auth\":\"$HARBOR_AUTH\"}}}" > /kaniko/.docker/config.json
    - /kaniko/executor
        --context $CI_PROJECT_DIR
        --dockerfile $CI_PROJECT_DIR/Dockerfile
        --destination $IMAGE
        --cache=true
        --cache-repo=$REGISTRY/cache

# Deploy Staging
deploy-stg:
  stage: deploy
  image: bitnami/kubectl:1.30
  environment:
    name: staging
    url: https://stg.company.com
  script:
    - kubectl set image deploy/$APP_NAME $APP_NAME=$IMAGE -n staging
    - kubectl rollout status deploy/$APP_NAME -n staging --timeout=5m
  only: [main]

# Deploy Production (manual)
deploy-prod:
  stage: deploy
  image: bitnami/kubectl:1.30
  environment:
    name: production
    url: https://api.company.com
  script:
    - git tag prod-$(date +%Y%m%d-%H%M%S)
    - git push origin --tags
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual
      allow_failure: false

# Smoke test
smoke-test:
  stage: verify
  image: alpine:3.20
  script:
    - apk add curl
    - curl -fsS https://api.company.com/healthz
  needs: [deploy-prod]
```

### 4.3 GitLab Runner 选型

| 类型 | 适合 |
|:---|:---|
| **Shell Runner** | 简单脚本，安全风险高 |
| **Docker Runner** | 主流 |
| **Kubernetes Runner** | **生产首选**，弹性 |
| **Docker Machine** | AWS Spot 弹性 |
| **Custom Executor** | 特殊需求 |

```yaml
# K8s Runner Helm Chart
runners:
  config: |
    [[runners]]
      [runners.kubernetes]
        namespace = "gitlab-runner"
        cpu_limit = "2"
        memory_limit = "4Gi"
        service_account = "gitlab-runner"
        helper_image = "registry.company.com/gitlab-runner-helper:latest"
        privileged = false
      [runners.cache]
        Type = "s3"
        Path = "gitlab-cache"
        Shared = true
        [runners.cache.s3]
          ServerAddress = "minio.company.com"
          BucketName = "gitlab-cache"
```

## 五、GitHub Actions

### 5.1 优势

```
✅ 与 GitHub 深度整合
✅ Marketplace 海量 Action
✅ 免费额度大方
✅ 跨平台（Linux/Mac/Windows）
✅ Reusable Workflows
✅ OIDC 免密码认证云
```

### 5.2 完整工作流

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

permissions:
  contents: read
  packages: write
  id-token: write     # OIDC

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
          cache: true
      
      - run: go mod download
      - run: golangci-lint run
      - run: go test -race -coverprofile=cover.out ./...
      
      - uses: codecov/codecov-action@v4

  build-push:
    needs: lint-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - uses: docker/setup-buildx-action@v3
      
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=sha-
            type=ref,event=branch
            type=semver,pattern={{version}}
      
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: true        # SLSA
          sbom: true
      
      - uses: sigstore/cosign-installer@v3
      - run: cosign sign --yes ${{ steps.meta.outputs.tags }}

  deploy:
    needs: build-push
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://api.company.com
    steps:
      - uses: actions/checkout@v4
      
      # OIDC 临时凭证（无需 AK/SK）
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::xxx:role/github-deploy
          aws-region: cn-north-1
      
      - run: aws eks update-kubeconfig --name prod-eks
      
      - run: |
          kubectl set image deploy/api api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          kubectl rollout status deploy/api --timeout=5m
```

### 5.3 Reusable Workflow

```yaml
# .github/workflows/reusable-build.yml
on:
  workflow_call:
    inputs:
      app_name: { required: true, type: string }
    secrets:
      REGISTRY_PASSWORD: { required: true }

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      ...

# 调用
jobs:
  call-build:
    uses: ./.github/workflows/reusable-build.yml
    with:
      app_name: order-api
    secrets:
      REGISTRY_PASSWORD: ${{ secrets.REG_PWD }}
```

## 六、Tekton（K8s 原生 CI）

### 6.1 是什么

```
"CI on K8s, by K8s, for K8s"
  ✅ 所有任务都是 K8s CR
  ✅ Pod-based 执行
  ✅ 与 Argo CD/Flux 配合好
  ✅ 跨集群可复用 Task
  ❌ 学习曲线陡
  ❌ UI 弱（用 Tekton Dashboard）
```

### 6.2 核心概念

```
Step          一个容器步骤
Task          一组 Step
TaskRun       一次 Task 执行
Pipeline      一组 Task 编排
PipelineRun   一次 Pipeline 执行
Workspaces    共享存储
Triggers      事件触发（Webhook）
```

### 6.3 示例 Pipeline

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: ci-pipeline
spec:
  workspaces:
    - name: source
  params:
    - name: repo-url
    - name: image-name
  tasks:
    - name: clone
      taskRef: { name: git-clone }
      params:
        - name: url
          value: $(params.repo-url)
      workspaces:
        - name: output
          workspace: source
    
    - name: test
      runAfter: [clone]
      taskRef: { name: go-test }
      workspaces:
        - name: source
          workspace: source
    
    - name: build
      runAfter: [test]
      taskRef: { name: kaniko }
      params:
        - name: IMAGE
          value: $(params.image-name)
      workspaces:
        - name: source
          workspace: source
    
    - name: deploy
      runAfter: [build]
      taskRef: { name: kubectl-deploy }
```

## 七、Argo Workflows（DAG 编排）

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: ml-pipeline-
spec:
  entrypoint: main
  templates:
    - name: main
      dag:
        tasks:
          - name: prep-data
            template: data-prep
          - name: train-a
            template: train
            dependencies: [prep-data]
            arguments: { parameters: [{name: model, value: a}] }
          - name: train-b
            template: train
            dependencies: [prep-data]
            arguments: { parameters: [{name: model, value: b}] }
          - name: evaluate
            template: eval
            dependencies: [train-a, train-b]
```

**典型场景**：ML Pipeline、批处理、定时任务。

## 八、容器构建技术

### 8.1 工具对比

| 工具 | 安全 | 速度 | 复杂度 | 推荐 |
|:---|:---:|:---:|:---:|:---:|
| **Docker** | 需 daemon | ⭐⭐⭐⭐ | 低 | 老 |
| **Kaniko** | 无 daemon ✅ | ⭐⭐⭐ | 中 | ⭐⭐⭐⭐ |
| **BuildKit** | rootless ✅ | ⭐⭐⭐⭐⭐ | 中 | **⭐⭐⭐⭐⭐** |
| **Buildah** | rootless ✅ | ⭐⭐⭐⭐ | 中 | ⭐⭐⭐⭐ |
| **img** | rootless | ⭐⭐⭐ | 中 | ⭐⭐⭐ |
| **Podman** | rootless ✅ | ⭐⭐⭐⭐ | 低 | ⭐⭐⭐⭐ |
| **Nerdctl** | containerd | ⭐⭐⭐⭐ | 低 | ⭐⭐⭐⭐ |

### 8.2 BuildKit 实战

```dockerfile
# syntax=docker/dockerfile:1.6
FROM golang:1.22 AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download
COPY . .
RUN --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -ldflags="-s -w" -o /bin/app

FROM gcr.io/distroless/static:nonroot
COPY --from=builder /bin/app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```

```bash
docker buildx build \
  --cache-to type=registry,ref=harbor/cache,mode=max \
  --cache-from type=registry,ref=harbor/cache \
  --platform linux/amd64,linux/arm64 \
  -t myapp:1.0 --push .
```

### 8.3 多阶段 + 多平台

```
✅ 多阶段（Build + Runtime 分离）
✅ distroless / scratch / alpine 基础镜像
✅ 非 root 用户
✅ 多平台（amd64 + arm64）
✅ 缓存挂载（--mount=type=cache）
✅ 不要 latest tag
✅ COPY 顺序优化（变动多的放后面）
```

## 九、镜像仓库（Registry）

| 工具 | 类型 | 特点 |
|:---|:---|:---|
| **Harbor** | 开源 | 国内主流，全功能 |
| **Nexus 3** | 通用 | 多类型 |
| **JFrog Artifactory** | 商业 | 重型 |
| **Docker Hub** | SaaS | 公网 |
| **GHCR / GCR / ECR / ACR** | 云厂 | 云原生 |
| **Quay** | RedHat | OpenShift |
| **Zot** | 轻量 | OCI 原生 |

### 9.1 Harbor 部署最佳实践

```
✅ 启用 HTTPS（必备）
✅ Trivy / Clair 漏洞扫描
✅ Cosign 签名验证
✅ Tag retention 策略
✅ 复制策略（多 Region）
✅ Webhook 集成 CI
✅ 配额管理（按项目）
✅ 准入策略
✅ 与 LDAP / OIDC 集成
```

### 9.2 镜像签名（Cosign）

```bash
# 生成密钥
cosign generate-key-pair

# 签名
cosign sign --key cosign.key harbor/myapp:1.0

# 验证（K8s 准入）
cosign verify --key cosign.pub harbor/myapp:1.0

# Keyless（OIDC）
cosign sign harbor/myapp:1.0
cosign verify --certificate-identity=https://github.com/... harbor/myapp:1.0
```

### 9.3 SBOM（软件物料清单）

```bash
# 生成 SBOM
syft harbor/myapp:1.0 -o spdx-json > sbom.json

# 漏洞扫描
grype sbom:./sbom.json

# 上传到仓库
cosign attach sbom --sbom sbom.json harbor/myapp:1.0
```

## 十、测试金字塔（CI 的灵魂）

```
              ┌──────────┐
              │  E2E      │  少（10%）  慢、贵
              ├──────────┤
              │ 集成测试   │  中（30%） 中速
              ├──────────┤
              │ 单元测试   │  多（60%） 快、便宜
              └──────────┘

每一层在 CI 中:
  - 单元: 每次 commit 必跑
  - 集成: 合 main 必跑
  - E2E:  上线前必跑
```

### 10.1 单元测试

```
关键指标:
  覆盖率 > 70%
  执行时间 < 5 分钟
  并行化（pytest -n / go test -p）
  失败必阻塞
```

### 10.2 集成测试

```
Testcontainers:
  - 容器化的 MySQL/Redis/Kafka 启动测试
  - 真实依赖测试
  - 跨语言（Go/Java/Python）

Docker Compose:
  - 多服务联调
  
K3d / Kind:
  - K8s 集群级测试
```

### 10.3 E2E

```
工具:
  - Playwright / Cypress（Web UI）
  - K6 / Locust（性能）
  - Postman / Bruno（API）
  - Robot Framework（混合）

策略:
  - 关键业务路径覆盖
  - 失败截屏 + 录屏
  - 并行 + 分片
```

## 十一、流水线设计原则

```
1. Fail Fast
   越早失败的步骤放越前面
   Lint → 单元测试 → 安全扫描 → 构建 → 集成测试 → 部署

2. 并行化
   独立步骤并行跑
   parallel 块

3. 缓存
   依赖缓存（pip / maven / go mod）
   Docker layer 缓存
   测试结果缓存

4. 工件复用
   build 一次，多环境部署
   不要每个环境都重新 build

5. 幂等性
   重跑安全
   带版本号

6. 通知合理
   失败通知到位
   成功通知不打扰

7. 可追溯
   每次构建记录: who/when/what/where
   PR 关联 build/deploy 记录

8. 可回滚
   1 分钟回滚是底线
```

## 十二、构建产物管理

```
不可变工件（Immutable Artifacts）:
  ✅ 一次构建，多环境运行
  ✅ 工件带版本号 + commit SHA
  ✅ 永远不重新 build "同一版本"
  
存储:
  - 镜像 → Harbor
  - JAR/WAR → Nexus
  - npm/pypi → 私有仓库
  - 二进制 → MinIO/S3

保留策略:
  - 主干分支镜像: 90 天
  - 生产镜像: 永久
  - 临时分支: 7 天
```

## 十三、安全集成（DevSecOps）

### 13.1 全链路扫描

```
代码层:
  ✅ Secret 扫描 (gitleaks, trufflehog)
  ✅ SAST (SonarQube, Semgrep, CodeQL)
  ✅ License 扫描 (FOSSA, Snyk)
  ✅ 依赖扫描 (Dependabot, Renovate, Snyk)

镜像层:
  ✅ 漏洞扫描 (Trivy, Grype, Clair)
  ✅ 配置扫描 (Docker Bench)
  ✅ 签名验证 (Cosign)
  ✅ SBOM (Syft)

部署层:
  ✅ K8s YAML 扫描 (Polaris, Kubesec)
  ✅ Admission Webhook (Kyverno, OPA Gatekeeper)
  ✅ Pod Security Standards
  ✅ Network Policy

运行时:
  ✅ Runtime Security (Falco)
  ✅ eBPF 监控
```

### 13.2 Secrets 管理

```
✅ HashiCorp Vault
✅ External Secrets Operator
✅ SealedSecrets
✅ SOPS + age
✅ K8s Secret + KMS 加密

❌ 永远不要:
   - Secret 入 Git
   - Secret 写 Dockerfile
   - Secret 写 ENV
```

## 十四、Deployment 与 CI/CD 衔接

详见 [05_部署策略](../05_部署策略/README.md)。

```
CI 完成后:
  方式 1: Push 式（CI 直接 kubectl apply）
    简单但权限过大
  
  方式 2: Pull 式 GitOps（Argo CD）
    ⭐ 推荐
    CI 只更新镜像 tag 到 git
    Argo CD 监听 git → 同步集群
```

## 十五、流水线监控与度量

### 15.1 DORA 四大关键指标

```
1. Deployment Frequency       部署频次
   精英: 每天多次
   高: 每周-每月
   中: 每月-每半年
   低: < 每半年

2. Lead Time for Changes      变更前置时间
   commit → 生产
   精英: < 1 小时
   高: 1 天-1 周
   中: 1 周-1 月
   低: > 6 月

3. Change Failure Rate         变更失败率
   精英: 0-15%
   高: 16-30%
   中: 16-30%
   低: 16-30%

4. Mean Time to Recovery (MTTR)
   精英: < 1 小时
   高: < 1 天
   中: 1 天-1 周
   低: > 1 周
```

### 15.2 流水线指标

```
✅ 流水线成功率
✅ 平均执行时长
✅ 排队时间
✅ 失败原因分布
✅ Top 10 慢任务
✅ Runner 利用率
✅ 缓存命中率
```

### 15.3 度量工具

| 工具 | 用途 |
|:---|:---|
| **Sleuth** | DORA 度量 |
| **LinearB** | DevOps 度量 |
| **GitHub Insights** | 内置 |
| **GitLab Value Stream** | 内置 |
| **Sleuthkit / 4-Keys** | 开源 DORA |
| **Pluralsight Flow** | 商业 |

## 十六、典型坑（生产血泪）

| 坑 | 建议 |
|:---|:---|
| **每次都重新 build** | 不可变工件 |
| **Secrets 入 Git** | gitleaks + Vault |
| **缺少缓存** | mod/layer 缓存 |
| **测试不并行** | matrix / xdist / -p |
| **流水线串行** | parallel 块 |
| **没有 fail fast** | Lint 放前面 |
| **构建机权限大** | rootless + minimal RBAC |
| **没有重试机制** | 网络/Flaky 测试需要重试 |
| **CI 太长** | 拆分 + 缓存 + 并行 |
| **生产直接 kubectl** | GitOps |
| **回滚靠重 build** | 镜像 tag 回滚 |
| **缺少 SBOM** | syft 必接 |
| **依赖锁文件不入 Git** | 必入 |
| **多分支策略乱** | trunk-based 或明确 GitFlow |
| **PR Review 形式化** | 强制 + 工具辅助 |
| **没有蓝绿/金丝雀** | 详见 05 部署策略 |

## 十七、最佳实践 Checklist

```
代码:
☐ 主干清晰（trunk-based / GitFlow）
☐ 分支保护 + PR Review
☐ Lint / 格式化强制
☐ Pre-commit hooks
☐ Conventional Commits

CI:
☐ Pipeline as Code (Jenkinsfile / .gitlab-ci.yml)
☐ 缓存依赖 + Docker layer
☐ 并行 + Fail Fast
☐ 多阶段（lint/test/scan/build）
☐ 单元覆盖率 > 70%
☐ Flaky 测试治理

镜像:
☐ Multi-stage Dockerfile
☐ 非 root 用户
☐ 多平台（amd64+arm64）
☐ BuildKit / Kaniko
☐ Trivy 扫描
☐ Cosign 签名
☐ Syft SBOM
☐ Harbor 仓库

安全:
☐ Secret 扫描
☐ SAST
☐ 依赖扫描
☐ 镜像扫描
☐ K8s YAML 扫描
☐ Vault / ESO

CD:
☐ 不可变工件
☐ GitOps（Argo CD）
☐ 蓝绿 / 金丝雀
☐ 一键回滚
☐ 多环境（dev/stg/prod）
☐ 人工审批生产

度量:
☐ DORA 4 指标
☐ 流水线监控
☐ MTTR 跟踪
☐ 周报 / 月报
```

## 十八、技术栈推荐（2025）

### 18.1 中小团队（< 50 人）

```
代码:     GitLab CE（一体化）
CI:       GitLab CI + K8s Runner
Registry: Harbor
扫描:     Trivy + gitleaks
签名:     Cosign
GitOps:   Argo CD
监控:     Prometheus + Grafana
```

### 18.2 中大团队（50-500 人）

```
代码:     GitLab EE / GitHub Enterprise
CI:       GitLab CI / GitHub Actions / Jenkins
Registry: Harbor 集群 + 多 Region
SAST:     SonarQube + Semgrep
DAST:     OWASP ZAP
扫描:     Trivy + Snyk
签名:     Cosign + Sigstore
GitOps:   Argo CD ApplicationSet
密钥:     Vault + ESO
策略:     Kyverno / OPA Gatekeeper
度量:     LinearB / Sleuth
```

### 18.3 大型 / 跨国（> 500 人）

```
代码:     GitHub Enterprise + GitLab 混合
CI:       自研平台 + Jenkins/Tekton 引擎
Registry: Harbor 多 AZ + 联邦
全套安全: Snyk + Wiz + Lacework
GitOps:   Argo CD 多集群 + Flagger
平台:     Backstage 内部开发者平台
AI 辅助:  Copilot + 自训练代码助手
```

## 十九、学习路径

```
入门（2 周）:
  1. 装 GitLab CE / 用 GitHub Actions
  2. 跑第一个 hello-world 流水线
  3. 写第一个 Dockerfile + push

中级（1 个月）:
  4. Pipeline as Code（Jenkinsfile / .gitlab-ci.yml）
  5. 缓存 + 并行
  6. 多环境部署
  7. Argo CD GitOps

高级（3 个月）:
  8. K8s Runner + Kaniko
  9. Cosign + Trivy + Syft 全套安全
  10. Reusable Workflow / Shared Library
  11. DORA 度量 + 改进

专家:
  12. 自研 IDP（Backstage / Coding 平台）
  13. 多集群 GitOps
  14. AI 辅助流水线
  15. 跨团队 CI/CD 治理
```

## 二十、参考资料

```
书:
  - 《Continuous Delivery》(Jez Humble)
  - 《Accelerate》(Nicole Forsgren)
  - 《DevOps Handbook》(Gene Kim)
  - 《Effective DevOps》

社区:
  - DORA: https://dora.dev/
  - CD Foundation: https://cd.foundation/
  - GitOps Working Group
  - CNCF App Delivery TAG

工具:
  - Jenkins: https://www.jenkins.io/
  - GitLab CI: https://docs.gitlab.com/ee/ci/
  - GitHub Actions: https://docs.github.com/actions
  - Tekton: https://tekton.dev/
  - Argo: https://argoproj.github.io/
  - Drone: https://www.drone.io/

报告:
  - Annual State of DevOps Report (Google DORA)
  - State of GitOps (Argo)
  - State of Kubernetes (VMware)
```

> 📖 **核心判断**：CI/CD 是 DevOps 的"心脏"。**中小团队首选 GitLab CI 一体化**，**国内大型场景 Jenkins + Argo CD 混部**，**GitHub 生态项目用 Actions**。2025 不可妥协的四件事：**不可变工件、Cosign 签名、Trivy 扫描、GitOps 部署**。最终目标是把 **DORA 四大指标**做到精英级——每天多次部署、< 1 小时变更前置、< 15% 失败率、< 1 小时恢复。
