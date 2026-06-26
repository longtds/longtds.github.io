# 容器化 CI

> 把构建、测试、镜像打包"装进容器"，CI 跑在 K8s 里。**云原生时代的 CI = 容器 + K8s + 不可变工件**，告别 Jenkins 物理机时代。

## 一、为什么要容器化 CI

```
传统物理机/VM Jenkins:
  ❌ 环境污染（上次跑的依赖留下）
  ❌ 多项目互相干扰
  ❌ 扩缩容慢（VM 启动分钟级）
  ❌ 难维护（手动装工具链）
  ❌ 单点故障

容器化 CI:
  ✅ 干净环境（每次 Pod 全新）
  ✅ 并行无干扰
  ✅ 秒级弹性（Pod 启动 5-30s）
  ✅ 工具链可声明（容器镜像 + YAML）
  ✅ 与 K8s 生态融合（GitOps 自然延伸）
```

## 二、容器化 CI 核心组件

```
1. 构建执行环境 (Runner / Agent)
   - K8s Pod 短生命周期
   - 多容器（lint / test / build 各一个）

2. 容器镜像构建工具
   - Kaniko / BuildKit / Buildah
   - 在容器内安全 build 容器

3. 镜像仓库
   - Harbor / GHCR / 私有 Registry
   - Cache repo

4. 制品管理
   - Helm Chart / OCI Artifact
   - Nexus / Artifactory

5. 部署引擎
   - Argo CD / Flux / Helm
   - GitOps 模式

6. 调度 + 编排
   - K8s 原生 (Tekton/Argo)
   - 或外部 (GitLab/Jenkins K8s plugin)
```

## 三、CI Runner on K8s（核心）

### 3.1 三种 Runner 模式

| 模式 | 工具 | 适合 |
|:---|:---|:---|
| **K8s Plugin 模式** | Jenkins K8s Plugin / GitLab K8s Runner | 改造老 Jenkins/GitLab |
| **K8s 原生 CI** | Tekton / Argo Workflows | 云原生新建 |
| **轻量原生** | Drone K8s / Woodpecker | 简单需求 |

### 3.2 Jenkins K8s Agent

```yaml
# Jenkinsfile 内嵌 Pod 模板
pipeline {
  agent {
    kubernetes {
      yaml '''
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins-build
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: workload
                operator: In
                values: [ci]
  containers:
    - name: jnlp
      image: jenkins/inbound-agent:latest-jdk21
      resources:
        requests: { cpu: 200m, memory: 512Mi }
    - name: maven
      image: maven:3.9-eclipse-temurin-21
      command: ['sleep', '999999']
      resources:
        requests: { cpu: 1, memory: 2Gi }
        limits: { cpu: 4, memory: 8Gi }
      volumeMounts:
        - { name: m2, mountPath: /root/.m2 }
    - name: kaniko
      image: gcr.io/kaniko-project/executor:debug
      command: ['sleep', '999999']
      volumeMounts:
        - { name: docker-config, mountPath: /kaniko/.docker }
    - name: kubectl
      image: bitnami/kubectl:1.30
      command: ['sleep', '999999']
  volumes:
    - name: m2
      persistentVolumeClaim: { claimName: maven-cache }
    - name: docker-config
      secret: { secretName: harbor-auth }
'''
    }
  }
  
  stages {
    stage('Build') {
      steps {
        container('maven') {
          sh 'mvn -B clean package'
        }
      }
    }
    stage('Image') {
      steps {
        container('kaniko') {
          sh '/kaniko/executor --context=. --destination=harbor/app:$BUILD_NUMBER'
        }
      }
    }
  }
}
```

### 3.3 GitLab K8s Runner

```yaml
# values.yaml (gitlab-runner Helm)
gitlabUrl: https://gitlab.company.com/
runnerRegistrationToken: ...

runners:
  config: |
    concurrent = 50
    check_interval = 5
    log_level = "info"
    
    [[runners]]
      name = "k8s-runner"
      url = "https://gitlab.company.com/"
      executor = "kubernetes"
      environment = ["FF_USE_FASTZIP=true", "ARTIFACT_COMPRESSION_LEVEL=fastest"]
      [runners.kubernetes]
        namespace = "gitlab-runner"
        image = "ubuntu:24.04"
        privileged = false
        cpu_limit = "4"
        memory_limit = "8Gi"
        cpu_request = "200m"
        memory_request = "512Mi"
        service_account = "gitlab-runner-build"
        helper_image = "registry.company.com/gitlab-runner-helper:latest"
        poll_interval = 5
        poll_timeout = 600
      [runners.kubernetes.affinity]
        [runners.kubernetes.affinity.node_affinity]
          [runners.kubernetes.affinity.node_affinity.required_during_scheduling_ignored_during_execution]
            [[runners.kubernetes.affinity.node_affinity.required_during_scheduling_ignored_during_execution.node_selector_terms]]
              [[runners.kubernetes.affinity.node_affinity.required_during_scheduling_ignored_during_execution.node_selector_terms.match_expressions]]
                key = "workload"
                operator = "In"
                values = ["ci"]
      [runners.cache]
        Type = "s3"
        Shared = true
        Path = "gitlab-cache"
        [runners.cache.s3]
          ServerAddress = "minio.company.com"
          BucketName = "gitlab-cache"
          BucketLocation = "us-east-1"
          AccessKey = "xxx"
          SecretKey = "xxx"

rbac:
  create: true
  rules:
    - apiGroups: [""]
      resources: ["pods", "pods/exec", "pods/log", "secrets", "configmaps", "services", "events"]
      verbs: ["*"]
    - apiGroups: ["apps"]
      resources: ["deployments"]
      verbs: ["*"]
```

### 3.4 .gitlab-ci.yml + K8s Runner

```yaml
default:
  image: golang:1.22
  tags: [k8s]

variables:
  GIT_STRATEGY: fetch
  GIT_DEPTH: 1
  GOPATH: $CI_PROJECT_DIR/.cache/go
  GOMODCACHE: $CI_PROJECT_DIR/.cache/gomod
  KUBERNETES_CPU_REQUEST: "1"
  KUBERNETES_MEMORY_REQUEST: "2Gi"

cache:
  key: $CI_COMMIT_REF_SLUG
  paths: [.cache/]

stages: [lint, test, build, deploy]

lint:
  stage: lint
  image: golangci/golangci-lint:v1.58
  script: [golangci-lint run]

test:
  stage: test
  script:
    - go test -race -cover ./...

build:
  stage: build
  image:
    name: gcr.io/kaniko-project/executor:debug
    entrypoint: [""]
  script:
    - /kaniko/executor
        --context $CI_PROJECT_DIR
        --destination harbor.company.com/apps/$CI_PROJECT_NAME:$CI_COMMIT_SHORT_SHA
        --cache=true
        --cache-repo=harbor.company.com/cache
```

## 四、容器内安全构建容器

### 4.1 为什么不能用 Docker-in-Docker (DinD)

```
DinD 问题:
  ❌ 需要 privileged: true（容器逃逸风险）
  ❌ 跨 Pod 不共享缓存
  ❌ 性能差
  ❌ 与 containerd K8s 兼容性差

替代方案:
  ✅ Kaniko       Google 出品，无 daemon
  ✅ BuildKit     rootless 模式
  ✅ Buildah      Red Hat 出品，rootless
  ✅ img          podman 系
```

### 4.2 Kaniko 实战

```yaml
# K8s Job 跑 Kaniko 构建
apiVersion: batch/v1
kind: Job
metadata:
  name: kaniko-build
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: kaniko
          image: gcr.io/kaniko-project/executor:v1.22.0-debug
          args:
            - --context=git://github.com/company/app.git#refs/heads/main
            - --dockerfile=Dockerfile
            - --destination=harbor.company.com/apps/myapp:1.0
            - --cache=true
            - --cache-repo=harbor.company.com/cache
            - --cache-ttl=168h
            - --reproducible
            - --use-new-run
            - --snapshot-mode=redo
          volumeMounts:
            - name: docker-config
              mountPath: /kaniko/.docker
      volumes:
        - name: docker-config
          secret:
            secretName: harbor-auth
            items:
              - key: .dockerconfigjson
                path: config.json
```

### 4.3 BuildKit 实战（推荐）

```yaml
# BuildKit Daemon as a Pod
apiVersion: apps/v1
kind: Deployment
metadata:
  name: buildkitd
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: buildkitd
          image: moby/buildkit:latest-rootless
          args:
            - --addr=tcp://0.0.0.0:1234
            - --addr=unix:///run/buildkit/buildkitd.sock
            - --oci-worker-no-process-sandbox
          securityContext:
            seccompProfile: { type: Unconfined }
            runAsUser: 1000
            runAsGroup: 1000
          ports:
            - { containerPort: 1234 }
          volumeMounts:
            - { name: buildkitd, mountPath: /home/user/.local/share/buildkit }
      volumes:
        - name: buildkitd
          persistentVolumeClaim:
            claimName: buildkitd-cache
---
apiVersion: v1
kind: Service
metadata: { name: buildkit }
spec:
  ports: [{port: 1234, targetPort: 1234}]
  selector: { app: buildkit }
```

```bash
# 客户端连接构建
export BUILDKIT_HOST=tcp://buildkit:1234
buildctl build \
  --frontend dockerfile.v0 \
  --local context=. \
  --local dockerfile=. \
  --output type=image,name=harbor/myapp:1.0,push=true \
  --export-cache type=registry,ref=harbor/cache,mode=max \
  --import-cache type=registry,ref=harbor/cache
```

### 4.4 Buildah（Pod 内构建）

```bash
# 完全 rootless，K8s 友好
buildah from --pull alpine:3.20
buildah run alpine apk add curl
buildah commit alpine harbor/myapp:1.0
buildah push harbor/myapp:1.0
```

## 五、Dockerfile 最佳实践

### 5.1 多阶段构建

```dockerfile
# syntax=docker/dockerfile:1.6

# 阶段 1: 构建
FROM golang:1.22 AS builder
WORKDIR /src

# 依赖单独 COPY，利用缓存
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

COPY . .
RUN --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/go/pkg/mod \
    CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w -extldflags '-static'" -o /bin/server ./cmd/server

# 阶段 2: 运行
FROM gcr.io/distroless/static:nonroot
COPY --from=builder /bin/server /server
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/server"]
```

### 5.2 最小化镜像基础

| 基础镜像 | 大小 | 适合 |
|:---|:---:|:---|
| **scratch** | 0 | 静态二进制 |
| **distroless/static** | ~2MB | Go 静态 |
| **distroless/cc** | ~20MB | 需 glibc |
| **alpine:3.20** | ~7MB | 小通用 |
| **ubuntu:24.04-slim** | ~28MB | 兼容性 |
| **chainguard 系列** | ~5-30MB | 安全强化 ⭐ |

### 5.3 关键技巧

```dockerfile
# ✅ 用 .dockerignore
# node_modules
# .git
# .env
# dist

# ✅ COPY 顺序：变动少的在前
COPY package.json package-lock.json ./
RUN npm ci
COPY src/ ./src/

# ✅ 不要存 secrets
# ❌ ENV API_KEY=xxx
# ✅ docker build --secret id=mysecret,src=./secret.txt

# ✅ 使用 buildkit secrets
RUN --mount=type=secret,id=mysecret \
    cat /run/secrets/mysecret

# ✅ 多平台
FROM --platform=$BUILDPLATFORM golang:1.22 AS builder
ARG TARGETOS TARGETARCH
RUN GOOS=$TARGETOS GOARCH=$TARGETARCH go build ...

# ✅ Healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/healthz || exit 1

# ✅ 元数据 Label
LABEL org.opencontainers.image.source="https://github.com/company/app"
LABEL org.opencontainers.image.revision="$COMMIT_SHA"
LABEL org.opencontainers.image.created="$BUILD_DATE"
LABEL org.opencontainers.image.title="my-app"
```

## 六、镜像缓存策略

### 6.1 三层缓存

```
1. 本地 Layer Cache（Builder 内存）
2. Registry Cache（Harbor /cache repo）
3. Remote Cache（BuildKit Registry / GHA）

效果:
  无缓存:    5 分钟
  Layer:     1 分钟
  Registry: 30 秒
  全命中:    5 秒
```

### 6.2 BuildKit Cache 类型

```bash
# Inline cache（嵌入主镜像）
buildctl build ... \
  --export-cache type=inline \
  --import-cache type=registry,ref=harbor/myapp:latest

# Registry cache（推荐）
--export-cache type=registry,ref=harbor/cache,mode=max,compression=zstd
--import-cache type=registry,ref=harbor/cache

# GitHub Actions cache
--export-cache type=gha,mode=max
--import-cache type=gha

# Local
--export-cache type=local,dest=/tmp/cache
--import-cache type=local,src=/tmp/cache
```

### 6.3 缓存命中关键

```
✅ COPY 拆分依赖与代码
✅ 不要 RUN apt-get update && install 混合
✅ 固定基础镜像版本（不要 latest）
✅ 单独的 COPY 行而不是合并
✅ 用 --mount=type=cache 持久缓存
```

## 七、镜像安全（必装）

### 7.1 全链路扫描

```
源码 → SCA (依赖) → SAST (静态) → 镜像 → 漏洞扫描 → 签名 → SBOM → 部署 → 运行时

工具栈:
  SCA:     Snyk / Dependabot / Renovate
  SAST:    SonarQube / Semgrep / CodeQL
  镜像漏洞: Trivy / Grype / Clair
  签名:    Cosign / Notary v2
  SBOM:    Syft / Tern
  运行时:  Falco / Tetragon
```

### 7.2 Trivy 扫描

```yaml
# 流水线步骤
- name: Scan
  run: |
    trivy image --severity HIGH,CRITICAL \
      --ignore-unfixed \
      --exit-code 1 \
      --format sarif --output trivy.sarif \
      harbor/myapp:$TAG

- name: Upload
  uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: trivy.sarif }
```

### 7.3 Cosign 签名

```bash
# 生成密钥（Vault 存储）
cosign generate-key-pair --kms vault://kv/cosign

# 签名
cosign sign --key vault://kv/cosign harbor/myapp:1.0

# Keyless（GitHub Actions OIDC）
cosign sign --yes ghcr.io/company/myapp:1.0

# 验证（K8s 准入）
cosign verify --key cosign.pub harbor/myapp:1.0

# K8s policy（Sigstore Policy Controller）
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata:
  name: signed-by-company
spec:
  images:
    - glob: "harbor.company.com/**"
  authorities:
    - keyless:
        identities:
          - issuer: https://token.actions.githubusercontent.com
            subject: https://github.com/company/.*
```

### 7.4 SBOM（软件物料清单）

```bash
# Syft 生成
syft harbor/myapp:1.0 -o spdx-json > sbom.json
syft harbor/myapp:1.0 -o cyclonedx-json > sbom.cdx.json

# 附到镜像
cosign attach sbom --sbom sbom.json harbor/myapp:1.0
cosign attest --predicate sbom.json --type spdx --key key harbor/myapp:1.0

# 后续审计
grype sbom:./sbom.json
```

### 7.5 准入控制（K8s 拦截不合规镜像）

```yaml
# Kyverno 策略：只允许签名 + 扫描通过的镜像
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-image-signatures
spec:
  validationFailureAction: enforce
  rules:
    - name: verify-image
      match: { resources: { kinds: [Pod] } }
      verifyImages:
        - imageReferences: ["harbor.company.com/*"]
          attestors:
            - entries:
                - keys:
                    publicKeys: |-
                      -----BEGIN PUBLIC KEY-----
                      ...
                      -----END PUBLIC KEY-----
```

## 八、流水线产物管理

### 8.1 工件类型

```
1. 容器镜像          Harbor + Cosign + SBOM
2. Helm Chart       Harbor (OCI) / ChartMuseum
3. 二进制可执行文件   Nexus / Artifactory / MinIO
4. npm / pip / maven 包  私有 npm/PyPI/Maven
5. Terraform Module  私有 Terraform Registry
6. AI 模型           HuggingFace Hub / 自建 MinIO
```

### 8.2 Harbor 作为统一仓库

```
Harbor 支持的 OCI Artifact:
  ✅ Docker / OCI 镜像
  ✅ Helm Chart (helm push)
  ✅ CNAB Bundle
  ✅ Cosign 签名
  ✅ SBOM Attestation
  ✅ ORAS 通用 OCI 推送

→ Harbor 不仅是镜像库，还是"OCI 制品库"
```

```bash
# Helm Chart OCI 推送
helm push my-app-1.0.tgz oci://harbor.company.com/charts

# 通用 OCI 推送（ORAS）
oras push harbor.company.com/artifacts/myfile:v1 \
  --artifact-type application/vnd.company.config.v1+json \
  config.yaml:application/json

# Cosign 验证
cosign verify --key cosign.pub harbor.company.com/apps/myapp:1.0
```

### 8.3 Tag 策略

```
不要用:
  ❌ latest          不可复现
  ❌ master/main     不固定
  
要用:
  ✅ Git SHA         harbor/app:sha-abc123
  ✅ SemVer          harbor/app:v1.2.3
  ✅ 时间戳          harbor/app:20260622-1430
  ✅ Branch+Build    harbor/app:main-42
  ✅ 组合            harbor/app:v1.2.3-sha-abc123

Tag Retention 策略:
  - 主分支镜像: 保留最近 50 + 90 天
  - 临时分支:   7 天
  - 生产 tag:   永久
  - 测试:       30 天
```

## 九、流水线性能优化

### 9.1 优化清单

```
✅ 缓存依赖（mod/pip/npm/maven）
✅ 缓存 Docker Layer
✅ 多阶段构建
✅ 并行 stages
✅ Fail Fast（lint 放前）
✅ 精简 Runner 镜像
✅ 资源 request 合理
✅ Node 亲和（CI 专用节点池）
✅ Spot 实例（成本省）
✅ Build Once, Deploy Many
```

### 9.2 缓存实战

```yaml
# GitLab CI
cache:
  key:
    files: [go.sum, go.mod]
  paths:
    - .cache/go-build
    - .cache/gomod
  policy: pull-push

# GitHub Actions
- uses: actions/setup-go@v5
  with: { go-version: '1.22', cache: true }

- uses: actions/cache@v4
  with:
    path: ~/.cache/go-build
    key: go-build-${{ hashFiles('**/go.sum') }}

# Jenkins (K8s PVC)
volumes:
  - persistentVolumeClaim:
      claimName: cache-maven
```

### 9.3 并行执行

```yaml
# GitLab：parallel matrix
test:
  parallel:
    matrix:
      - GO_VERSION: ["1.21", "1.22"]
        OS: ["linux/amd64", "linux/arm64"]
  script: ...

# GitHub Actions
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
    node: [20, 22]

# Jenkins
parallel(
  unit: { sh 'go test ./...' },
  lint: { sh 'golangci-lint run' },
  scan: { sh 'trivy fs .' }
)
```

### 9.4 增量构建（Monorepo）

```yaml
# 只对改动的目录跑流水线
job:
  rules:
    - changes:
        - services/order/**
  script:
    - cd services/order
    - make ci

# 工具:
#   - GitHub Action: paths-filter
#   - GitLab: rules:changes
#   - Bazel/Nx: 增量构建图
```

## 十、Tekton（K8s 原生 CI）实战

### 10.1 完整 Pipeline

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata: { name: build-deploy }
spec:
  workspaces: [{ name: source }, { name: cache }]
  params:
    - { name: repo-url, type: string }
    - { name: branch, type: string, default: main }
    - { name: image, type: string }
  tasks:
    - name: clone
      taskRef: { name: git-clone, kind: ClusterTask }
      workspaces: [{ name: output, workspace: source }]
      params:
        - { name: url, value: $(params.repo-url) }
        - { name: revision, value: $(params.branch) }
    
    - name: lint
      runAfter: [clone]
      taskRef: { name: golangci-lint }
      workspaces: [{ name: source, workspace: source }]
    
    - name: test
      runAfter: [clone]
      taskRef: { name: go-test }
      workspaces:
        - { name: source, workspace: source }
        - { name: cache, workspace: cache }
    
    - name: build-image
      runAfter: [lint, test]
      taskRef: { name: kaniko }
      params:
        - { name: IMAGE, value: $(params.image) }
        - { name: EXTRA_ARGS, value: ["--cache=true", "--reproducible"] }
      workspaces: [{ name: source, workspace: source }]
    
    - name: scan
      runAfter: [build-image]
      taskRef: { name: trivy-scan }
      params: [{ name: IMAGE, value: $(params.image) }]
    
    - name: sign
      runAfter: [scan]
      taskRef: { name: cosign-sign }
      params: [{ name: IMAGE, value: $(params.image) }]
    
    - name: update-gitops
      runAfter: [sign]
      taskRef: { name: git-update-deployment }
      params:
        - { name: IMAGE, value: $(params.image) }
        - { name: GITOPS_REPO, value: github.com/company/gitops }
```

### 10.2 触发器（Webhook → PipelineRun）

```yaml
apiVersion: triggers.tekton.dev/v1beta1
kind: EventListener
metadata: { name: github-listener }
spec:
  triggers:
    - name: github-push
      interceptors:
        - ref: { name: github }
          params:
            - name: secretRef
              value: { secretName: github-webhook }
            - name: eventTypes
              value: ["push"]
      bindings:
        - ref: github-push-binding
      template:
        ref: build-deploy-template
```

## 十一、Argo Workflows（DAG 编排）

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata: { name: full-ci }
spec:
  entrypoint: main
  templates:
    - name: main
      dag:
        tasks:
          - { name: clone, template: git-clone }
          - { name: lint, template: lint, dependencies: [clone] }
          - { name: test, template: test, dependencies: [clone] }
          - { name: build, template: build, dependencies: [lint, test] }
          - { name: scan, template: scan, dependencies: [build] }
          - { name: sign, template: sign, dependencies: [scan] }
          - { name: notify, template: notify, dependencies: [sign] }
```

## 十二、自托管 GitHub Actions Runner

```yaml
# Actions Runner Controller (ARC)
apiVersion: actions.github.com/v1alpha1
kind: AutoscalingRunnerSet
metadata: { name: company-runners }
spec:
  githubConfigUrl: https://github.com/company
  githubConfigSecret: github-token
  template:
    spec:
      containers:
        - name: runner
          image: ghcr.io/actions/actions-runner:latest
          resources:
            requests: { cpu: "1", memory: "4Gi" }
            limits: { cpu: "4", memory: "16Gi" }
  minRunners: 2
  maxRunners: 50
```

## 十三、镜像分发优化

```
方案 1: 多 Region Harbor + 自动复制
  - 国内 + 海外 镜像中心
  - 自动同步（policy）
  - 就近拉取

方案 2: P2P 镜像分发
  - Dragonfly / Kraken / harbor-p2p
  - 大集群启动时节省带宽
  - 字节、阿里大量在用

方案 3: 镜像预热（Preheat）
  - 上线前主动推送到所有节点
  - 避免上线时拉镜像超时

方案 4: 镜像加速（按需加载）
  - Stargz / Nydus / SOCI
  - 大镜像不必完全下载就可启动
```

## 十四、典型坑（生产血泪）

| 坑 | 建议 |
|:---|:---|
| **DinD privileged** | 改 Kaniko / BuildKit |
| **没有缓存** | 三层缓存全开 |
| **基础镜像 latest** | 固定版本 + 自动续期 |
| **每环境重新 build** | 不可变工件 |
| **CI Pod 抢资源** | 专用节点池 |
| **大镜像启动慢** | distroless / Nydus |
| **Layer 顺序差** | 拆分 COPY |
| **secret 入镜像** | --mount secret |
| **没签名** | Cosign 必上 |
| **没扫描** | Trivy + 阻断高危 |
| **CI 失败不通知** | 必通知 owner |
| **Runner 数量爆** | HPA + Spot |
| **跨集群镜像慢** | 多 Region + P2P |
| **Helm Chart 推送方式乱** | 统一 OCI |
| **缺少 SBOM** | Syft 标配 |

## 十五、最佳实践 Checklist

```
Runner:
☐ K8s 弹性 Runner
☐ 专用节点池（Taint+Toleration）
☐ Spot 实例（成本）
☐ HPA 自动扩缩
☐ 资源 request/limit 合理

构建:
☐ Kaniko / BuildKit（非 DinD）
☐ 多阶段 Dockerfile
☐ distroless 基础镜像
☐ 非 root 用户
☐ 三层缓存
☐ Multi-platform (amd64+arm64)

镜像:
☐ Harbor 集群 + 多 Region
☐ Tag 策略明确（SHA/SemVer）
☐ Tag Retention
☐ Trivy 扫描
☐ Cosign 签名
☐ Syft SBOM
☐ Helm Chart 用 OCI 推送

安全:
☐ 镜像准入控制（Kyverno）
☐ 仅允许签名镜像
☐ 仅允许扫描通过镜像
☐ Pre-commit + gitleaks
☐ 依赖扫描（Renovate）

性能:
☐ 缓存命中率监控
☐ CI 平均时长跟踪
☐ Top 慢任务治理
☐ 增量 build/test（Monorepo）
☐ 镜像分发优化（P2P/Nydus）

工程:
☐ Pipeline as Code
☐ 共享库 / 模板
☐ 单元/集成/E2E 分层
☐ Build Once, Deploy Many
☐ 通知 + 度量
```

## 十六、推荐栈（2025）

### 16.1 小团队

```
CI:        GitLab CI + K8s Runner
构建:      Kaniko
镜像:      Harbor 单集群
签名:      Cosign keyless
扫描:      Trivy
SBOM:      Syft
部署:      Argo CD
```

### 16.2 中大团队

```
CI:        GitLab CI / GitHub Actions / Jenkins K8s Agent
构建:      BuildKit cluster
镜像:      Harbor 多 Region + Dragonfly P2P
签名:      Cosign + Sigstore Policy Controller
扫描:      Trivy + Snyk + Wiz
SBOM:      Syft + 自动审计
部署:      Argo CD ApplicationSet
策略:      Kyverno + OPA Gatekeeper
平台:      Backstage
```

## 十七、学习路径

```
入门（2 周）:
  1. 装 K8s + GitLab Runner
  2. 写第一个 .gitlab-ci.yml on K8s
  3. Kaniko 构建第一个镜像

中级（1 个月）:
  4. 多阶段 Dockerfile
  5. BuildKit 缓存
  6. Harbor 部署 + 配置
  7. Trivy + Cosign 集成

高级（3 个月）:
  8. Tekton / Argo Workflows
  9. 多平台镜像 + 多 Region 复制
  10. Dragonfly P2P 分发
  11. SBOM 治理
  12. 准入策略

专家:
  13. Backstage 内部门户
  14. AI 辅助流水线
  15. 跨集群 CI/CD
  16. 自研 Build Cache
```

## 十八、参考资料

```
官方:
  - Kaniko: https://github.com/GoogleContainerTools/kaniko
  - BuildKit: https://github.com/moby/buildkit
  - Buildah: https://buildah.io/
  - Tekton: https://tekton.dev/
  - Harbor: https://goharbor.io/
  - Cosign: https://docs.sigstore.dev/cosign/
  - Syft: https://github.com/anchore/syft
  - Argo Workflows: https://argoproj.github.io/workflows/

社区:
  - CNCF App Delivery TAG
  - OpenSSF SLSA / Sigstore
  - SLSA Framework: https://slsa.dev/

工具:
  - Dragonfly: https://d7y.io/
  - Nydus: https://nydus.dev/
  - Stargz Snapshotter
  - ORAS: https://oras.land/

报告:
  - State of Cloud-Native CI/CD
  - Sysdig Cloud-Native Security Report
```

> 📖 **核心判断**：容器化 CI 是云原生时代的"基础设施"。**Kaniko/BuildKit + Harbor + Trivy + Cosign + Syft + Argo CD** 是 2025 标准栈。最容易翻车的不是工具，而是：**还在用 DinD、没有缓存、没有签名、没有 SBOM**——这四条做不到，"容器化"只是表面功夫。最后的灵魂是 **Build Once, Deploy Many + Immutable Artifacts**：一份制品走完 dev/stg/prod，永不重 build。
