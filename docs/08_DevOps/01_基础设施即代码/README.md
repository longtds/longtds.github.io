# 基础设施即代码（IaC）

> 把基础设施"画在 YAML 里"——服务器、网络、K8s 集群、DNS、证书……都用代码声明式管理。**IaC = 可版本化 + 可审查 + 可回滚 + 可复制 + 可审计**，是 DevOps/GitOps 的底层基石。

## 一、为什么需要 IaC

```
没有 IaC 的痛:
  - "线上集群是手动 click 出来的，没人敢动"
  - "测试和生产环境不一样，定位故障基本靠猜"
  - "运维离职 → 一堆人肉知识失传"
  - "改个安全组要去控制台点 30 次"
  - "灾备恢复要 2 周"

有 IaC 的好:
  ✅ Git diff 看变更
  ✅ PR Review 把关
  ✅ 测试环境 = 生产环境（同一份代码）
  ✅ 灾备 = git clone + apply
  ✅ 跨账号/跨云一键复制
  ✅ 全部审计可追溯
```

## 二、IaC 工具全景

| 维度 | Terraform | OpenTofu | Pulumi | CloudFormation | Crossplane | Ansible | Salt |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 语言 | HCL | HCL | Py/Go/TS | YAML/JSON | YAML/K8s | YAML | Python |
| 多云 | ✅ | ✅ | ✅ | ❌(AWS) | ✅ | ✅ | ✅ |
| 状态文件 | ✅ | ✅ | ✅ | 托管 | K8s etcd | ❌ | ❌ |
| K8s 原生 | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| 学习曲线 | 中 | 中 | 高 | 低 | 中 | 低 | 中 |
| Drift 检测 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 国内主流度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**2025 选型建议**：
- **基础设施声明**：**Terraform / OpenTofu**（事实标准）
- **K8s 内 GitOps**：**Argo CD + Helm/Kustomize**
- **K8s 控制平面 IaC**：**Crossplane**
- **配置管理 / 编排**：**Ansible**
- **多语言/复杂逻辑**：Pulumi

## 三、Terraform / OpenTofu（核心）

### 3.1 OpenTofu 是什么

```
2023.8 HashiCorp Terraform 改 BSL 协议（非开源）
       ↓
2023.9 Linux Foundation 接手 Fork → OpenTofu
       ↓
2024+ OpenTofu 与 Terraform 双轨
       - 配置完全兼容（drop-in replacement）
       - 新功能 OpenTofu 先有（如 module exclude）
       - 国内大厂大量迁移到 OpenTofu

→ 新建项目首选 OpenTofu，老项目可保留 Terraform
```

### 3.2 核心概念

```
Provider   云厂商驱动（AWS / 阿里云 / GCP / K8s / 自建）
Resource   一个具体资源（EC2、VPC、RDS、K8s Deployment）
Data Source 只读查询（不创建）
Module     可复用的资源组
State      记录当前实际状态（.tfstate）
Plan       预演变更
Apply      实际执行
Backend    state 存储位置（S3/OSS/HTTP/远程）
Workspace  环境隔离（dev/stg/prod）
```

### 3.3 标准目录结构（生产推荐）

```
infra/
├── modules/                    # 可复用模块
│   ├── vpc/
│   ├── eks-cluster/
│   ├── rds/
│   └── alb/
├── envs/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── stg/
│   └── prod/
├── shared/                     # 跨环境共享（IAM/DNS）
└── .github/workflows/
    └── terraform-plan.yml
```

### 3.4 最小可用示例（AWS）

```hcl
# envs/prod/main.tf
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket         = "company-tfstate"
    key            = "prod/aws.tfstate"
    region         = "cn-north-1"
    dynamodb_table = "tfstate-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      env       = "prod"
      team      = "infra"
      owner     = "sre"
      managedBy = "terraform"
    }
  }
}

module "vpc" {
  source = "../../modules/vpc"
  cidr   = "10.0.0.0/16"
  azs    = ["cn-north-1a", "cn-north-1b", "cn-north-1c"]
}

module "eks" {
  source     = "../../modules/eks-cluster"
  name       = "prod-eks"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  node_groups = {
    general = { instance_types = ["m6i.xlarge"], min = 3, max = 20 }
    gpu     = { instance_types = ["g5.2xlarge"], min = 0, max = 10, taints = [{key="nvidia.com/gpu", value="true", effect="NO_SCHEDULE"}] }
  }
}

module "rds" {
  source             = "../../modules/rds"
  engine             = "postgres"
  engine_version     = "16.3"
  instance_class     = "db.r6g.large"
  allocated_storage  = 200
  multi_az           = true
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
}
```

### 3.5 阿里云 / 腾讯云 / 华为云 Provider

```hcl
# 国内常用 provider
terraform {
  required_providers {
    alicloud = { source = "aliyun/alicloud", version = "~> 1.230" }
    tencentcloud = { source = "tencentcloudstack/tencentcloud", version = "~> 1.81" }
    huaweicloud = { source = "huaweicloud/huaweicloud", version = "~> 1.65" }
  }
}

provider "alicloud" {
  region = "cn-hangzhou"
  # 推荐用 STS 临时凭证或 RAM Role，禁止 AK/SK 写文件
}

# ACK (阿里云 K8s)
resource "alicloud_cs_managed_kubernetes" "prod" {
  name           = "prod-ack"
  cluster_spec   = "ack.pro.small"
  worker_vswitch_ids = alicloud_vswitch.k8s[*].id
  ...
}
```

### 3.6 Backend / 状态管理（关键）

```hcl
# ❌ 不要把 state 提交到 git
# ✅ 用远程 backend + 锁

# AWS S3 + DynamoDB
backend "s3" {
  bucket         = "company-tfstate"
  key            = "prod/aws.tfstate"
  region         = "cn-north-1"
  dynamodb_table = "tfstate-lock"     # 锁表
  encrypt        = true
}

# 阿里云 OSS
backend "oss" {
  bucket = "company-tfstate"
  prefix = "prod"
  key    = "aws.tfstate"
  region = "cn-hangzhou"
  tablestore_endpoint = "..."
  tablestore_table = "tfstate-lock"
}

# Terraform Cloud / Spacelift / env0 / Scalr / 国产: Erda Cloud
# K8s ConfigMap (kubernetes backend) - 仅测试
```

### 3.7 Module 设计原则

```
✅ 输入 / 输出 明确
✅ 单一职责（一个 module 干一件事）
✅ 不要硬编码（用 variable）
✅ 提供合理默认值
✅ 版本化（Git tag 或 Terraform Registry）
✅ 文档 + 示例

❌ Module 内部不要再读外部 state
❌ 不要 module 嵌套 4 层以上
❌ 不要 module 跨账号 / 跨区域操作
```

### 3.8 Workspace vs Directory（环境隔离）

```
方案 A: Directory（推荐）
  envs/dev/   envs/stg/   envs/prod/
  
  ✅ 完全独立，安全
  ✅ 可不同版本 / 不同 backend
  ❌ 代码有少量重复

方案 B: Workspace（不推荐生产）
  terraform workspace new dev / stg / prod
  
  ⚠️ 同一份代码 + 同一份 backend
  ⚠️ 容易误操作生产
  ✅ 资源少时简单
```

### 3.9 变量与密钥

```hcl
# variables.tf
variable "region" {
  type    = string
  default = "cn-north-1"
}

variable "db_password" {
  type      = string
  sensitive = true              # 标记敏感，避免日志泄漏
}

# 密钥来源（优先级）:
# 1. Vault / KMS / AWS Secrets Manager
data "aws_secretsmanager_secret_version" "db" {
  secret_id = "prod/db/password"
}

# 2. 环境变量: TF_VAR_db_password
# 3. .tfvars 文件（必须 .gitignore，加密保存）

# ❌ 永远不要硬编码密钥
```

### 3.10 工作流（CI/CD）

```yaml
# .github/workflows/terraform.yml
name: Terraform
on:
  pull_request:
    paths: ['infra/**']
  push:
    branches: [main]
    paths: ['infra/**']

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with: { terraform_version: 1.7.5 }
      - run: terraform fmt -check -recursive
      - run: terraform init
      - run: terraform validate
      - run: terraform plan -out=tfplan
      - name: Comment PR
        uses: actions/github-script@v7
        with:
          script: |
            const plan = fs.readFileSync('plan.txt', 'utf8');
            github.rest.issues.createComment({...});
  
  apply:
    needs: plan
    if: github.ref == 'refs/heads/main'
    environment: production       # 需人工审批
    runs-on: ubuntu-latest
    steps:
      - run: terraform apply tfplan
```

### 3.11 安全扫描

```bash
# tfsec / checkov / kics 静态扫描
tfsec .
checkov -d .
trivy config .

# Terraform 原生
terraform validate
terraform fmt -check
```

### 3.12 Drift 检测（必装）

```bash
# 定期 plan，发现实际状态被手动改了
terraform plan -detailed-exitcode
# exit 0: no change
# exit 2: drift detected!

# 自动化:
#   - 每天定时 plan
#   - 发现 drift 告警
#   - 工具: driftctl, Terraform Cloud Drift Detection
```

## 四、Crossplane（K8s 控制平面 IaC）

### 4.1 是什么

```
"用 K8s 管理云资源"
  - 把"创建 RDS / S3 / VPC"变成 K8s CR
  - GitOps 友好（同 Argo CD/Flux 配合）
  - 跨云抽象（Composite Resource）
  - 适合"K8s 是世界中心"的团队
```

### 4.2 简单示例

```yaml
# 用 K8s CR 创建 AWS RDS
apiVersion: rds.aws.crossplane.io/v1alpha1
kind: DBInstance
metadata:
  name: prod-db
spec:
  forProvider:
    region: cn-north-1
    dbInstanceClass: db.r6g.large
    engine: postgres
    allocatedStorage: 200
  writeConnectionSecretToRef:
    name: prod-db-conn
    namespace: app
```

### 4.3 Crossplane vs Terraform

| 维度 | Crossplane | Terraform |
|:---|:---|:---|
| 范式 | Reconcile（持续校准） | One-shot apply |
| K8s 原生 | ⭐⭐⭐⭐⭐ | ❌ |
| 多云 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 学习曲线 | 高 | 中 |
| 生态成熟度 | 中 | 高 |
| 国内主流度 | 小 | 大 |

**结论**：传统 IaC 用 Terraform，K8s 优先架构可选 Crossplane。

## 五、Ansible（配置管理 + 编排）

### 5.1 角色定位

```
Ansible 干什么:
  ✅ 装软件包 / 写配置文件
  ✅ 滚动重启服务
  ✅ 批量执行命令
  ✅ 准备 K8s 节点
  ✅ 物理机 / VM 操作

Ansible 不擅长:
  ❌ 创建云资源（用 Terraform）
  ❌ 状态管理（无 state file）
  ❌ Drift 自动校准

经典分工:
  Terraform 起资源 → Ansible 装软件 → K8s 跑应用
```

### 5.2 最佳实践

```
✅ Inventory 用动态（aws_ec2 / openstack 插件）
✅ Role 化（roles/nginx/{tasks,handlers,templates,defaults}）
✅ Tag 化（--tags / --skip-tags）
✅ 幂等性（每个 task 都要可重跑）
✅ Vault 加密敏感
✅ check mode + diff（演练）
✅ 限流（serial 滚动）
✅ Galaxy / 私有镜像分发 Role
```

### 5.3 经典模式

```yaml
# playbook.yml
- name: 部署 Nginx 集群
  hosts: web
  become: true
  serial: 25%                  # 一次 25% 滚动
  max_fail_percentage: 10
  
  pre_tasks:
    - name: 健康检查（从 LB 摘除）
      uri: { url: "http://lb/api/drain/{{ inventory_hostname }}" }
  
  roles:
    - role: nginx
      tags: nginx
    - role: monitoring
      tags: monitoring
  
  post_tasks:
    - name: 健康检查（加回 LB）
      uri: { url: "http://lb/api/restore/{{ inventory_hostname }}" }
```

### 5.4 与 Terraform 集成

```hcl
# Terraform 起完资源后调 Ansible
resource "null_resource" "ansible" {
  triggers = { ips = join(",", aws_instance.web[*].private_ip) }
  
  provisioner "local-exec" {
    command = "ansible-playbook -i ${join(",", aws_instance.web[*].private_ip)}, playbook.yml"
  }
}

# 或用动态 inventory: 直接 ansible-inventory --list 拉 AWS
```

## 六、Helm（K8s 应用打包）

### 6.1 核心概念

```
Chart       打包的 K8s 应用（模板 + 默认值）
Values      用户自定义参数
Release     一次 helm install 的实例
Repo        Chart 仓库（Harbor/ChartMuseum）

Helm 3 vs 2:
  ✅ 去掉 Tiller（更安全）
  ✅ Three-way merge（更稳）
  ✅ Library Chart
```

### 6.2 Chart 结构

```
my-app/
├── Chart.yaml              # metadata
├── values.yaml             # 默认参数
├── values-prod.yaml        # 生产参数
├── values-dev.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── tests/
│       └── connection.yaml
├── charts/                 # 依赖 charts
└── README.md
```

### 6.3 关键命令

```bash
helm create my-app
helm lint .
helm template . -f values-prod.yaml         # 渲染不部署
helm install my-app . -f values-prod.yaml
helm upgrade --install my-app . -f values-prod.yaml --atomic --timeout 5m
helm rollback my-app 1
helm history my-app
helm uninstall my-app
helm test my-app
helm diff upgrade my-app . -f values.yaml   # 必装 plugin
```

### 6.4 高级特性

```yaml
# Helm Hook（生命周期）
metadata:
  annotations:
    "helm.sh/hook": post-install,post-upgrade
    "helm.sh/hook-weight": "0"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded

# Library Chart（共享逻辑）
type: library

# 子 Chart 复用
dependencies:
  - name: postgresql
    version: 14.x.x
    repository: https://charts.bitnami.com/bitnami
```

### 6.5 私有 Chart 仓库

| 工具 | 类型 |
|:---|:---|
| **Harbor** | 含 Chart 支持，国内主流 |
| **ChartMuseum** | 老牌专用 |
| **JFrog Artifactory** | 商业 |
| **OCI Registry** | Helm 3.8+ 用 OCI 协议（推荐）|

```bash
# OCI 推送（推荐）
helm push my-app-1.0.tgz oci://harbor.company.com/charts
helm pull oci://harbor.company.com/charts/my-app --version 1.0
```

## 七、Kustomize（K8s 配置叠加）

### 7.1 vs Helm

```
Helm:        模板 + 参数（动态）
Kustomize:   叠加 + 补丁（声明式）

何时选 Kustomize:
  ✅ 简单参数化（环境差异）
  ✅ 不想学模板语言
  ✅ 多环境同结构

何时选 Helm:
  ✅ 复杂条件逻辑
  ✅ 三方应用分发
  ✅ 包管理需求
```

### 7.2 标准结构

```
my-app/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   ├── replicas-patch.yaml
    │   └── env-configmap.yaml
    ├── stg/
    └── prod/
        ├── kustomization.yaml
        ├── replicas-patch.yaml
        └── resources-patch.yaml
```

### 7.3 实战示例

```yaml
# base/kustomization.yaml
resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
commonLabels:
  app: my-app

---
# overlays/prod/kustomization.yaml
resources:
  - ../../base
patches:
  - path: replicas-patch.yaml
    target: { kind: Deployment }
configMapGenerator:
  - name: app-config
    behavior: merge
    literals:
      - LOG_LEVEL=info
      - REGION=cn-north-1
images:
  - name: my-app
    newTag: v1.2.3
namePrefix: prod-
namespace: production
```

```bash
kubectl apply -k overlays/prod
kubectl kustomize overlays/prod          # 渲染查看
```

## 八、Pulumi（多语言 IaC）

```python
# 用 Python 写基础设施（不用学 HCL）
import pulumi
import pulumi_aws as aws

vpc = aws.ec2.Vpc("main", cidr_block="10.0.0.0/16")

for i, az in enumerate(["a", "b", "c"]):
    aws.ec2.Subnet(f"public-{az}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i}.0/24",
        availability_zone=f"cn-north-1{az}")

cluster = aws.eks.Cluster("main",
    role_arn=role.arn,
    vpc_config={"subnet_ids": subnet_ids})

pulumi.export("cluster_endpoint", cluster.endpoint)
```

**优势**：可用真正的编程语言（Python/TypeScript/Go/Java/.NET），有 IDE 自动完成、单元测试、复杂逻辑。
**劣势**：生态不如 Terraform，国内主流度低。

## 九、Packer（不可变镜像）

```hcl
# 把"装好软件的镜像"build 出来，IaC 直接用
packer {
  required_plugins {
    amazon = { version = "~> 1.2.8", source = "github.com/hashicorp/amazon" }
  }
}

source "amazon-ebs" "ubuntu" {
  ami_name      = "company-base-{{timestamp}}"
  instance_type = "t3.medium"
  region        = "cn-north-1"
  source_ami_filter {
    filters = { name = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" }
    owners  = ["099720109477"]
  }
  ssh_username = "ubuntu"
}

build {
  sources = ["source.amazon-ebs.ubuntu"]
  provisioner "ansible" {
    playbook_file = "./playbook.yml"
  }
}
```

```bash
packer init .
packer validate .
packer build .
```

**用途**：把 Ansible 装好的 AMI 烧出来 → Terraform 启动 → 秒级开机。

## 十、GitOps（IaC 的终极形态）

```
传统 CD:
  Dev → CI → 推送命令 → 集群
  
GitOps:
  Dev → CI → Git 仓库（声明状态）→ Agent 拉取 → 集群
  
  → Git = Single Source of Truth
  → 集群状态永远等于 Git 状态
  → drift 自动校准
```

### 10.1 Argo CD vs Flux

| 维度 | Argo CD | Flux v2 |
|:---|:---:|:---:|
| UI | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 多租户 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 多集群 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| ApplicationSet | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 国内主流度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**结论**：国内项目无脑选 **Argo CD**。

### 10.2 Argo CD 典型应用

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: git@github.com:company/k8s-config.git
    targetRevision: main
    path: my-app/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - PruneLast=true
    retry:
      limit: 5
      backoff: { duration: 5s, factor: 2, maxDuration: 3m }
```

### 10.3 多环境 ApplicationSet

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: my-app
spec:
  generators:
    - list:
        elements:
          - cluster: dev-cluster
            namespace: dev
            values: values-dev.yaml
          - cluster: prod-cluster
            namespace: prod
            values: values-prod.yaml
  template:
    metadata:
      name: 'my-app-{{cluster}}'
    spec:
      destination:
        server: 'https://{{cluster}}.kubeapi'
      source:
        helm:
          valueFiles: ['{{values}}']
        repoURL: ...
        path: my-app
```

## 十一、IaC 安全（必做）

### 11.1 静态扫描工具

| 工具 | 用途 |
|:---|:---|
| **tfsec** | Terraform 专用 |
| **Checkov** | Terraform / K8s / CloudFormation |
| **Trivy** | 含 IaC 扫描 |
| **KICS** | 多工具 IaC |
| **Polaris** | K8s YAML 检查 |
| **Kubesec** | K8s 安全打分 |
| **OPA / Conftest** | 自定义策略 |

### 11.2 必须检测的问题

```
✅ S3 / OSS 公开读写
✅ 安全组 0.0.0.0/0 开放
✅ RDS 公网访问
✅ 未加密的卷 / 备份
✅ IAM 通配符 *
✅ 缺少 Tag
✅ EKS / ACK 公网 endpoint
✅ K8s Pod root 用户
✅ K8s 缺少 resource limits
✅ 镜像 latest 标签
✅ Secrets 写在 ConfigMap
```

### 11.3 OPA 策略示例

```rego
# policy/no-public-s3.rego
package terraform

deny[msg] {
  resource := input.resource.aws_s3_bucket_acl[name]
  resource.acl == "public-read"
  msg := sprintf("S3 bucket %s is publicly readable", [name])
}
```

```bash
conftest test plan.json -p policy/
```

### 11.4 密钥管理

```
✅ AWS Secrets Manager / SSM Parameter Store
✅ HashiCorp Vault
✅ K8s External Secrets Operator
✅ SealedSecrets（加密后入 Git）
✅ SOPS + age + git-crypt

❌ .env 入 Git
❌ tfvars 含密钥入 Git
❌ K8s Secret 明文 base64 入 Git
```

## 十二、IaC + AI（2025 新趋势）

```
"AI 写 IaC":
  - GitHub Copilot / Codeium
  - Terraform AI (HashiCorp Terraform Stacks)
  - Pulumi AI (生成 Pulumi 程序)
  - 阿里云 IaC Copilot
  - 腾讯云 IaC AI

"AI 审查 IaC":
  - Snyk / Wiz AI 审查
  - K8sGPT 自动找问题
  - 自建 LLM + tfsec/checkov 结果

"AI 解释 IaC":
  - "把这个 Terraform 配置解释给开发听"
  - "找出与生产环境的差异"
  - "估算这个变更的成本"
```

## 十三、IaC 团队协作流程

```
1. 需求 → Jira / 飞书工单
2. 分支开发: feature/add-redis-cluster
3. 本地: terraform fmt + validate + plan
4. PR + Review（至少 1 个 SRE +1）
5. CI 自动跑: fmt / validate / tfsec / plan
6. PR 评论展示 plan diff
7. 审批 → Merge to main
8. CI 自动 Apply（生产需人工 Approve）
9. 通知 Slack/企业微信
10. 监控 + 验证
```

## 十四、典型坑（生产血泪）

| 坑 | 建议 |
|:---|:---|
| **state 入 Git** | 永远用远程 backend |
| **state 没加锁** | 必加 lock 表 |
| **多人同时 apply** | CI 串行 + Mutex |
| **手动改资源** | 改完必导回 IaC |
| **没有 drift 检测** | 每日 plan 监控 |
| **密钥写文件** | Vault / Secrets Manager |
| **module 版本不锁** | 必加 version = "~> X.Y" |
| **乱用 count + for_each** | 数据驱动选 for_each |
| **destroy 误触** | -target / 严格 PR |
| **跨账号通用 module** | 严格隔离 |
| **太多 Provider** | 收敛 |
| **不写测试** | terratest / kitchen-terraform |
| **不规范 tagging** | 必上 tag 治理 |
| **plan 没人看** | PR 必贴 plan diff |
| **依赖循环** | 拆 module |
| **terraform_remote_state 滥用** | 用 SSM/Vault 替代 |
| **未做成本估算** | infracost CI 集成 |

## 十五、最佳实践 Checklist

```
代码:
☐ 目录结构清晰（modules + envs）
☐ Module 版本化
☐ 变量命名规范
☐ 输出有意义
☐ 文档 + README

State:
☐ 远程 backend
☐ State 锁
☐ State 加密
☐ 多环境隔离

CI/CD:
☐ fmt / validate / lint
☐ tfsec / checkov 扫描
☐ plan diff 贴 PR
☐ 生产必人工审批
☐ Apply 后通知

安全:
☐ Secrets 不入 Git
☐ Provider 用最小权限
☐ Tag 强制
☐ 网络隔离合规
☐ 加密存储 / 传输

可观测:
☐ Drift 检测
☐ 成本估算（infracost）
☐ 变更审计
☐ 监控 Provider 健康
```

## 十六、推荐技术栈（2025）

### 16.1 极简栈（小团队）

```
基础设施声明: OpenTofu
配置管理:    Ansible
K8s 应用:    Helm + Argo CD
密钥:        AWS Secrets Manager / Vault
扫描:        tfsec + Checkov
代码托管:    GitLab + GitLab CI / GitHub Actions
状态:        S3 / OSS + DynamoDB lock
```

### 16.2 中型团队

```
基础设施: OpenTofu + Atlantis (PR 自动 plan/apply)
镜像:     Packer + Ansible
配置管理: Ansible
K8s:      Crossplane + Argo CD + Kustomize + Helm
密钥:     Vault + External Secrets Operator
策略:     OPA Gatekeeper + Conftest
扫描:     Snyk / Wiz / 自建 tfsec
成本:     Infracost
```

### 16.3 大型 / 多云

```
基础设施: OpenTofu + Terragrunt + Spacelift
镜像:     Packer + 内部 base image 流水线
K8s:      Crossplane + Argo CD ApplicationSet 多集群
密钥:     Vault + KMS + Doppler
策略:     OPA + Kyverno + Sentinel
扫描:     Snyk + Wiz + Lacework
成本:     Cloudability / CAST AI
```

## 十七、学习路径

```
入门（2 周）:
  1. 装 Terraform/OpenTofu，跑第一个 hello-world
  2. 创建 VPC + EC2 + 安全组
  3. terraform init / plan / apply / destroy
  4. 理解 state 和 backend

中级（1 个月）:
  5. Module 化重构
  6. 多环境（dev/stg/prod）
  7. 远程 backend + 锁
  8. CI 集成（plan + apply）
  9. Helm Chart 写第一个

高级（3 个月）:
  10. Crossplane / Argo CD GitOps
  11. tfsec/Checkov/OPA 安全
  12. Atlantis / Spacelift 自动化
  13. 多云 Provider
  14. 团队协作流程

专家:
  15. 自研 module 库 + 内部分发
  16. 跨账号 IAM / 网络
  17. 灾备演练
  18. IaC + AI 实战
```

## 十八、参考资料

```
官方:
  - Terraform: https://developer.hashicorp.com/terraform
  - OpenTofu: https://opentofu.org/
  - Crossplane: https://www.crossplane.io/
  - Argo CD: https://argo-cd.readthedocs.io/
  - Helm: https://helm.sh/
  - Pulumi: https://www.pulumi.com/

书:
  - 《Terraform: Up & Running》(Yevgeniy Brikman)
  - 《Infrastructure as Code》(Kief Morris)
  - 《Pro Terraform with Pulumi》

社区:
  - HashiCorp Discuss
  - r/Terraform
  - Awesome Terraform / Awesome Pulumi
  - 国内: 阿里云 IaC / 腾讯云 TIC 社区

工具集:
  - Atlantis: https://www.runatlantis.io/
  - Terragrunt: https://terragrunt.gruntwork.io/
  - Infracost: https://www.infracost.io/
  - tfsec: https://aquasecurity.github.io/tfsec/
  - Checkov: https://www.checkov.io/
```

> 📖 **核心判断**：2025 IaC 已成 DevOps 必备地基。**OpenTofu/Terraform + Ansible + Helm + Argo CD** 是最普适的四件套；K8s 优先架构可加 **Crossplane**。最容易翻车的不是工具，而是：**state 管理、密钥管理、drift 治理、人工干预生产**。**先把基础四件套用透 6 个月**，再考虑高级技巧（Stacks/AI/多云抽象）。
