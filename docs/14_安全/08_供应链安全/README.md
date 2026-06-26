# 供应链安全

> SolarWinds、Log4j、xz-utils、CodeCov、3CX —— 2020 年以来软件供应链攻击呈爆炸式增长。**供应链安全 = 源码 + 依赖 + 构建 + 镜像 + 分发 + 部署 + 运行时**，每个环节都是攻击面。**SLSA + SBOM + 签名 + 准入** 是 2025 标准答案。

## 一、供应链攻击全景

### 1.1 典型事件

```
2020 SolarWinds       Sunburst 后门，影响 18,000+ 客户
2021 CodeCov          Bash uploader 被篡改，泄漏密钥
2021 Log4Shell        Log4j 0day，全球数百万系统
2022 OpenSSL 3.0      高危漏洞 CVE-2022-3786
2023 3CX              桌面客户端遭供应链攻击
2024 xz-utils         后门植入（CVE-2024-3094），险些进入主流发行版
2024 PyPI / npm       数千恶意包，typosquatting
```

### 1.2 攻击面

```
1. 源码层
   - Git 仓库被入侵
   - 维护者账号被黑
   - 恶意 PR 合入
   - 内部威胁

2. 依赖层
   - 三方库后门 / 0day
   - typosquatting（react → reakt）
   - dependency confusion（私有名 → 公开恶意）
   - 依赖被劫持（npm event-stream）

3. 构建层
   - CI 系统被入侵
   - Build agent 被替换
   - 中间人篡改

4. 制品层
   - 镜像 / Jar / Wheel 被替换
   - Registry 被入侵

5. 分发层
   - 下载劫持
   - 镜像源中间人
   - HTTPS 证书伪造

6. 运行时
   - Updater 被替换
   - 配置被改
   - 0day 利用
```

## 二、SLSA 框架（Supply-chain Levels for Software Artifacts）

### 2.1 4 个等级

```
SLSA L1: 文档化构建过程
SLSA L2: 自动化 + 可追溯（version control + build service）
SLSA L3: 可信 build platform + 防篡改证据
SLSA L4: 双人审查 + 隔离 build + 可重现

目标:
  → 任何制品都可证明:
     1. 谁构建的 (Who)
     2. 何时构建 (When)
     3. 用什么源码 (What)
     4. 如何构建 (How)
     5. 在哪构建 (Where)
```

### 2.2 各级要求

| 要求 | L1 | L2 | L3 | L4 |
|:---|:---:|:---:|:---:|:---:|
| 版本控制 | ✅ | ✅ | ✅ | ✅ |
| 构建服务 | | ✅ | ✅ | ✅ |
| Provenance 生成 | | ✅ | ✅ | ✅ |
| Provenance 签名 | | | ✅ | ✅ |
| 隔离构建 | | | ✅ | ✅ |
| 可重现构建 | | | | ✅ |
| 双人评审 | | | | ✅ |

### 2.3 国内可落地的 SLSA L3 实践

```
✅ 源码:           GitLab/GitHub + Branch Protection + CODEOWNERS
✅ CI:             GitLab CI / Jenkins K8s + 隔离 Runner
✅ Build:          Kaniko/BuildKit（rootless）
✅ Provenance:    Sigstore / in-toto attestation
✅ Sign:           Cosign keyless
✅ SBOM:           Syft
✅ Verify:         Sigstore Policy Controller
```

## 三、SBOM（软件物料清单）

### 3.1 是什么

```
"软件的成分表"
  - 所有依赖（直接 + 间接）
  - 版本号
  - 许可证
  - 哈希值
  - 漏洞引用

国家政策:
  - 美国: 行政令 14028 强制 SBOM
  - 中国: 《关键信息基础设施安全保护条例》
  - 欧盟: Cyber Resilience Act
```

### 3.2 SBOM 格式

| 格式 | 主导 | 特点 |
|:---|:---|:---|
| **SPDX** ⭐⭐⭐⭐⭐ | Linux Foundation | ISO 标准 |
| **CycloneDX** ⭐⭐⭐⭐⭐ | OWASP | 安全侧重 |
| SWID Tags | ISO | 软件标识 |

### 3.3 生成 SBOM

```bash
# Syft（Anchore，最主流）
syft myapp:1.0 -o spdx-json > sbom.spdx.json
syft myapp:1.0 -o cyclonedx-json > sbom.cdx.json
syft dir:/path/to/source -o spdx-json
syft sbom:./old-sbom.json -o cyclonedx-json    # 格式转换

# Trivy 也能生成
trivy image --format spdx-json -o sbom.json myapp:1.0
trivy fs --format cyclonedx -o sbom.json /src

# 语言原生
npm sbom --sbom-format=cyclonedx
mvn org.cyclonedx:cyclonedx-maven-plugin:makeAggregateBom
poetry export --format requirements.txt | cyclonedx-py -i -
go-syft
cargo sbom
```

### 3.4 SBOM 附到镜像

```bash
# Cosign 附加
cosign attest --predicate sbom.json --type spdx \
  --key cosign.key harbor/app:1.0

# Verify
cosign verify-attestation --type spdx --key cosign.pub harbor/app:1.0 | \
  jq -r '.payload' | base64 -d | jq '.predicate'

# OCI Reference Types（推荐）
cosign attach sbom --sbom sbom.json harbor/app:1.0
```

### 3.5 SBOM 用途

```
1. 漏洞应急响应
   "Log4j 出 0day 了，谁用了？" 
   → grep sbom for log4j

2. 许可证合规
   "GPL 组件用在哪？"

3. 升级评估
   "升级 React 18 会影响哪些产品？"

4. 客户合规
   "我们卖软件给政府，需要 SBOM"

5. 审计追溯
   "这个安全事件涉及哪些版本？"
```

### 3.6 漏洞匹配

```bash
# Grype 配合 SBOM 扫漏洞
grype sbom:./sbom.json --fail-on critical

# Trivy
trivy sbom sbom.json

# Snyk
snyk test --file=sbom.json

# Dependency-Track（中央化 SBOM 管理）⭐
# OWASP 项目，跟踪整个组织的 SBOM
```

## 四、签名与证明（Sigstore 生态）

### 4.1 Sigstore 全栈

```
Fulcio       签名时颁发短期 X.509（OIDC 验证身份）
Rekor         透明日志（公开可审计）
Cosign        签名工具
Gitsign       Git commit 签名
SLSA          完整 framework

→ Keyless 签名：不需要长期管理私钥
```

### 4.2 Keyless 签名实战

```bash
# 自动 OIDC 认证 → 颁发临时证书 → 签名 → 上链
cosign sign --yes ghcr.io/company/app:1.0

# 验证
cosign verify ghcr.io/company/app:1.0 \
  --certificate-identity-regexp "^https://github.com/company/.*" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

# 输出包含:
#   - 签名身份（GitHub Actions / GitLab CI / 用户邮箱）
#   - 签名时间
#   - Rekor 索引（透明日志）
```

### 4.3 in-toto Attestation

```bash
# 不只是签镜像，签"事件"
cosign attest \
  --predicate scan-report.json \
  --type vuln \
  --key cosign.key \
  harbor/app:1.0

# 类型:
#   - SBOM (spdx, cyclonedx)
#   - Vuln (vulnerability report)
#   - Provenance (SLSA L3)
#   - Custom (任意 JSON)

# 验证
cosign verify-attestation --type vuln harbor/app:1.0
```

### 4.4 GitHub Actions OIDC 签名

```yaml
permissions:
  id-token: write           # 关键，启用 OIDC
  contents: read
  packages: write

steps:
  - uses: sigstore/cosign-installer@v3
  
  - name: Build & Push
    run: docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
  
  - name: Sign
    run: |
      cosign sign --yes \
        ghcr.io/${{ github.repository }}@${DIGEST}
  
  - name: Attest SBOM
    run: |
      syft ghcr.io/${{ github.repository }}@${DIGEST} -o spdx-json > sbom.json
      cosign attest --yes --predicate sbom.json --type spdx \
        ghcr.io/${{ github.repository }}@${DIGEST}
  
  - name: Attest SLSA Provenance
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@v1.10.0
```

## 五、依赖安全

### 5.1 依赖扫描工具

| 工具 | 语言 | 类型 |
|:---|:---|:---|
| **Snyk** | 全栈 | 商业 |
| **Dependabot** | 全栈 | GitHub 原生 |
| **Renovate** | 全栈 | 开源 ⭐ |
| **OWASP Dependency-Check** | 全栈 | 开源 |
| **OSV-Scanner** ⭐ | 全栈 | Google 开源 |
| **npm audit** | npm | 原生 |
| **pip-audit** | Python | 官方 |
| **safety** | Python | 开源 |
| **bundler-audit** | Ruby | 开源 |
| **govulncheck** | Go | 官方 |
| **cargo audit** | Rust | 官方 |

### 5.2 OSV-Scanner（推荐）

```bash
# Google 出品，覆盖 npm/PyPI/Go/Rust/Maven/Packagist/...
brew install osv-scanner

# 扫描项目
osv-scanner -r .                          # 递归
osv-scanner --lockfile=package-lock.json
osv-scanner --sbom=sbom.json

# CI 集成
osv-scanner --format=sarif --output=osv.sarif -r .
```

### 5.3 Renovate（自动 PR 升级）

```json
// renovate.json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:base", "security:openssf-scorecard"],
  "schedule": ["before 5am on monday"],
  "labels": ["dependencies"],
  "packageRules": [
    {
      "matchUpdateTypes": ["patch", "pin"],
      "automerge": true
    },
    {
      "matchUpdateTypes": ["major"],
      "labels": ["major-update", "manual-review"]
    },
    {
      "groupName": "security",
      "matchCategories": ["security"],
      "automerge": true,
      "schedule": ["at any time"]
    }
  ],
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security", "critical"]
  }
}
```

### 5.4 Lockfile 治理

```
✅ 锁文件入 Git (package-lock.json, poetry.lock, go.sum, Cargo.lock)
✅ CI 校验 lockfile 与 source 一致
✅ Lockfile 签名（npm verify-signatures）

❌ 不要忽略 lockfile
❌ 不要随意更新 lockfile
```

### 5.5 私有镜像源（防 Dependency Confusion）

```
攻击场景:
  内部包: @company/internal-utils（私服）
  攻击者: 注册同名公开包 → 版本号超高 → 拉取
  
防御:
  ✅ 私有 Registry（Nexus / Verdaccio / 阿里 Codeup）
  ✅ Scope 限制（@company 仅查私服）
  ✅ npm Scope: registry=https://nexus.company.com
  ✅ pip: --index-url=https://pypi.company.com
  ✅ 拒绝公网 fallback
  
工具:
  - Nexus Repository
  - JFrog Artifactory
  - Verdaccio (轻量 npm)
  - 阿里 Codeup Package
  - 腾讯 CODING Artifacts
```

### 5.6 OpenSSF Scorecard

```bash
# 评估开源项目的安全实践
scorecard --repo=github.com/your-dep/repo

# 评分项:
#   ✅ Maintained        近期活跃
#   ✅ Code-Review       PR 评审
#   ✅ Signed-Releases   发布签名
#   ✅ Branch-Protection 分支保护
#   ✅ Dependency-Update 依赖更新
#   ✅ Token-Permissions GitHub Token 最小化
#   ✅ Vulnerabilities   已知漏洞
#   ...
#   总分 0-10

# 低分项目 = 高风险依赖 → 谨慎引入
```

## 六、构建系统安全

### 6.1 隔离构建环境

```
✅ 一次性 Runner（K8s Pod / VM）
✅ 不共享 cache（多租户互相隔离）
✅ 网络白名单（只能访问必要域）
✅ 不可访问生产
✅ Audit 完整
✅ Build 时间限制（防挖矿）
```

### 6.2 GitHub Actions 安全

```yaml
permissions:
  contents: read         # 最小权限（不要全读写）
  id-token: write        # 仅需要 OIDC 时

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      # 第三方 action 必须 pin SHA（不要用 @v1）
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11   # v4.1.1
      
      # 不要在 PR 中无脑用 pull_request_target（高危）
      # 不要 echo ${{ secrets.* }} 到日志
      - run: echo "ok"
        env:
          TOKEN: ${{ secrets.TOKEN }}
      
      # restrict harden-runner
      - uses: step-security/harden-runner@v2
        with:
          egress-policy: audit
```

### 6.3 GitLab CI 安全

```yaml
# .gitlab-ci.yml
variables:
  GIT_STRATEGY: fetch
  GIT_SUBMODULE_STRATEGY: none
  FF_USE_FASTZIP: "true"

# 分级 Runner
build-trusted:
  tags: [trusted]                        # 仅 main 分支 + 内部
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

build-untrusted:
  tags: [untrusted]                      # PR / Fork
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'

# Secrets 不暴露给 fork PR
# Settings > CI/CD > Variables > Protected
```

### 6.4 Jenkins 安全

```
✅ 升级 Jenkins + 插件
✅ Configuration as Code (JCasC)
✅ RBAC（Matrix-based / Role-based）
✅ Credentials 不暴露日志
✅ Pipeline Sandbox 启用
✅ Build agents 隔离（K8s Pod，一次性）
✅ Master 不跑任务（numExecutors=0）
✅ 反向代理 + TLS
```

## 七、镜像准入（Policy Enforcement）

### 7.1 Sigstore Policy Controller

```yaml
# 强制集群只接受签名镜像
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata: { name: must-be-signed }
spec:
  images:
    - glob: "harbor.company.com/**"
    - glob: "ghcr.io/company/**"
  authorities:
    # GitHub Actions keyless
    - keyless:
        url: https://fulcio.sigstore.dev
        identities:
          - issuer: https://token.actions.githubusercontent.com
            subject: https://github.com/company/.*
        ctlog:
          url: https://rekor.sigstore.dev
    # 内部 Cosign key
    - key:
        data: |-
          -----BEGIN PUBLIC KEY-----
          MFkw...
          -----END PUBLIC KEY-----

---
# 强制要求 SBOM
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata: { name: require-sbom }
spec:
  images:
    - glob: "harbor.company.com/**"
  authorities:
    - keyless: ...
      attestations:
        - name: must-have-sbom
          predicateType: https://spdx.dev/Document
```

### 7.2 Kyverno 镜像验证

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: verify-image-signatures }
spec:
  validationFailureAction: enforce
  webhookTimeoutSeconds: 30
  rules:
    - name: check-signature
      match: { resources: { kinds: [Pod] } }
      verifyImages:
        - imageReferences: ["harbor.company.com/*"]
          mutateDigest: true                     # 锁 SHA
          required: true
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/company/*"
                    issuer: "https://token.actions.githubusercontent.com"
          attestations:
            - type: https://slsa.dev/provenance/v0.2
              conditions:
                - all:
                    - key: "{{ predicate.builder.id }}"
                      operator: Equals
                      value: "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/builder_container_slsa3.yml@refs/tags/v1.10.0"
```

## 八、镜像来源白名单

```yaml
# Kyverno: 只允许来自公司 Harbor
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: allowed-image-registries }
spec:
  validationFailureAction: enforce
  rules:
    - name: validate-registries
      match: { resources: { kinds: [Pod] } }
      validate:
        message: "Only company registry allowed"
        pattern:
          spec:
            containers:
              - image: "harbor.company.com/* | gcr.io/company/* | ghcr.io/company/*"
```

## 九、内部 Registry 安全

### 9.1 Harbor 最佳实践

```
✅ HTTPS 强制
✅ Replication 多 region
✅ Tag retention
✅ Trivy 扫描 + 自动阻断
✅ Cosign 签名验证
✅ 项目级配额
✅ RBAC + LDAP/OIDC
✅ Webhook 集成 CI
✅ 不可变 tag（防覆盖）
✅ Audit 日志
✅ 备份 + 异地
```

### 9.2 镜像清理与不变性

```yaml
# Harbor 不可变 tag 策略
# Project Setting > Tag Immutability
# 匹配规则: prod-*, v*, release-*
# 这些 tag 推送后不可删/不可覆盖

# Tag Retention 策略
# 保留最新 50 个 + 最近 90 天 + 关键 tag (production, latest)
# 其他自动清理
```

### 9.3 私有 Helm Chart

```bash
# OCI 推送（Helm 3.8+）
helm push my-chart-1.0.tgz oci://harbor.company.com/charts

# 签名 Chart
cosign sign --key cosign.key oci://harbor.company.com/charts/my-chart:1.0

# 部署验证
cosign verify --key cosign.pub oci://harbor.company.com/charts/my-chart:1.0
```

## 十、运行时供应链监控

### 10.1 实时检测

```
✅ Falco / Tetragon
   - 检测新进程
   - 检测异常下载
   - 检测异常 exec

✅ Sysdig / Aqua / Wiz
   - 持续 SBOM 漂移检测
   - 运行时 CVE 评估
   - 异常二进制告警
```

### 10.2 漂移检测

```
"运行的镜像与 SBOM 不一致"
  - 容器内被植入新二进制
  - 容器内被替换文件
  
工具:
  - Falco rule: 监控关键路径写入
  - Tetragon eBPF: 进程执行追踪
  - K8s 镜像 sha256 校验
  - imagePullPolicy: Always + digest
```

## 十一、内部 OSS 治理

### 11.1 三方组件评估

```
引入新依赖时必查:
  ✅ OpenSSF Scorecard 评分 ≥ 7
  ✅ 维护状态（近期 commit / 活跃度）
  ✅ 许可证（GPL? MIT? Apache?）
  ✅ 已知 CVE
  ✅ 维护者背景
  ✅ Star / Fork 健康度
  ✅ 替代品对比

工具:
  - deps.dev (Google 出品)
  - Snyk Advisor
  - Libraries.io
  - GitHub Advisory Database
```

### 11.2 内部 OSS Office

```
大企业 OSPO（开源项目办公室）:
  - 维护"已批准依赖清单"（whitelist）
  - 引入新依赖走审批流程
  - 季度审计现有依赖
  - 安全应急（Log4j 来了，扫整个组织）
  - 内部开源治理
```

## 十二、应急响应（依赖漏洞）

### 12.1 Log4Shell 级别响应剧本

```
T+0:   情报订阅触发 / 安全团队发现
       ↓
T+1h:  确认范围
       - 全公司 SBOM grep <CVE 涉及组件>
       - 影响产品清单
       - 影响版本评估
       ↓
T+2h:  公开 Advisory
       - 内部通告
       - 客户通告（如已影响）
       ↓
T+6h:  紧急止血
       - WAF / IDS 加规则
       - 限流 / 关闭非必要功能
       ↓
T+24h: 修复发布
       - 主线代码升级 / 临时 mitigation
       - CI 重 build 全镜像
       - 灰度发布
       ↓
T+72h: 全量恢复
       - 验证修复
       - 客户通告
       - 复盘

→ 没有 SBOM 的企业：T+1 周才能知道自己有没有受影响
→ 有 SBOM 的企业: T+5 分钟出影响清单
```

### 12.2 内部应急工具

```
✅ Dependency-Track（OWASP）
   - 集中所有 SBOM
   - CVE 实时匹配
   - 通知 Owner

✅ 自研漏洞平台
   - Inventory + SBOM + CVE 关联
   - 自动 PR / Jira

✅ DefectDojo
   - 漏洞工单平台
```

## 十三、典型坑

| 坑 | 建议 |
|:---|:---|
| **依赖不锁** | lockfile 入 Git |
| **包来源 fallback 公网** | 私服 + 严格 scope |
| **GitHub Actions @latest** | pin SHA |
| **CI 暴露 secrets** | 不 echo / mask |
| **Build agent 共享** | 一次性 + 隔离 |
| **没 SBOM** | Syft 标配 |
| **没签名** | Cosign keyless |
| **签了不验** | Sigstore Policy Controller |
| **依赖永不更新** | Renovate + auto PR |
| **CVE 来了找不到位置** | Dependency-Track |
| **第三方组件审核形式化** | OpenSSF Scorecard + OSPO |
| **挖矿镜像** | 漂移检测 + Falco |
| **Helm Chart 不签名** | 同镜像处理 |
| **内部 npm 名易撞** | Scope + 私服 |
| **Build 不可重现** | 固定版本 + lockfile + base image SHA |

## 十四、最佳实践 Checklist

```
源码:
☐ Branch Protection
☐ Signed Commits
☐ Pre-commit hooks (gitleaks)
☐ CODEOWNERS
☐ SAST / 依赖扫描 / Secret 扫描

依赖:
☐ Lockfile 入 Git
☐ 私有 Registry + Scope
☐ Renovate / Dependabot
☐ OSV-Scanner CI 阻断
☐ OpenSSF Scorecard 评估
☐ OSPO 审核新依赖

构建:
☐ 隔离 Runner（K8s Pod / 一次性）
☐ pin SHA 第三方 Action
☐ 最小权限 Token
☐ SLSA L2/L3
☐ Provenance 生成

镜像:
☐ Trivy 扫描 + 阻断
☐ Cosign 签名
☐ Syft SBOM
☐ in-toto attestation
☐ 来源白名单（Harbor only）
☐ 不可变 tag
☐ Harbor / Registry 加固

准入:
☐ Sigstore Policy Controller
☐ Kyverno verifyImages
☐ 镜像 SHA digest
☐ Helm Chart 签名验证

运行时:
☐ Falco / Tetragon
☐ 漂移检测
☐ 镜像 hash 校验
☐ Egress 监控

应急:
☐ SBOM 集中（Dependency-Track）
☐ CVE 订阅 + 自动化
☐ Log4Shell 级演练
☐ 客户通告流程
```

## 十五、推荐栈（2025）

### 15.1 中小团队

```
源码:        GitHub / GitLab + Branch Protection + Dependabot
依赖:        Renovate + OSV-Scanner
构建:        GitHub Actions + harden-runner
镜像:        Trivy + Cosign keyless + Syft
准入:        Sigstore Policy Controller
SBOM:        OWASP Dependency-Track
私服:        Verdaccio + Nexus
```

### 15.2 中大企业

```
+ Snyk / Wiz / Lacework
+ Sigstore Enterprise / 自托管 Fulcio+Rekor
+ JFrog Artifactory
+ OSPO 团队
+ DefectDojo 漏洞平台
+ SLSA L3 builder
+ HSM-backed signing keys
```

### 15.3 国产/信创

```
+ 长亭牧云 / 启明
+ 阿里云 镜像安全 / 容器安全
+ 国产 Cosign / 国密签名
+ 内部 SBOM 平台
+ 信创依赖审核
```

## 十六、学习路径

```
入门（2 周）:
  1. Trivy 扫描镜像
  2. Syft 生成 SBOM
  3. Cosign keyless 签名
  4. Renovate / Dependabot

中级（1 个月）:
  5. Sigstore Policy Controller K8s 准入
  6. Kyverno verifyImages
  7. Dependency-Track 部署
  8. SLSA L2 builder

高级（3 个月）:
  9. SLSA L3 完整 provenance
  10. in-toto attestation
  11. 私有 Sigstore 部署
  12. OSPO 治理流程
  13. 大规模 SBOM 自动化

专家:
  14. 自研漏洞平台
  15. AI 辅助代码审查
  16. 零信任 CI/CD
```

## 十七、参考资料

```
框架:
  - SLSA: https://slsa.dev/
  - SPDX: https://spdx.dev/
  - CycloneDX: https://cyclonedx.org/
  - in-toto: https://in-toto.io/
  - OpenSSF: https://openssf.org/

工具:
  - Sigstore: https://www.sigstore.dev/
  - Cosign: https://docs.sigstore.dev/cosign/
  - Syft: https://github.com/anchore/syft
  - Grype: https://github.com/anchore/grype
  - Dependency-Track: https://dependencytrack.org/
  - Renovate: https://docs.renovatebot.com/
  - OSV-Scanner: https://osv.dev/

报告:
  - State of Software Supply Chain (Sonatype)
  - Sysdig Cloud-Native Security Report
  - Google SLSA Maturity

社区:
  - OpenSSF Slack
  - Sigstore Slack
  - CNCF Security TAG

国内:
  - 中国信通院 软件供应链安全白皮书
  - SBOM 国家标准
```

> 📖 **核心判断**：2025 供应链安全是企业安全的"新常态"。**SLSA L2/L3 + SBOM（Syft）+ 签名（Cosign keyless）+ 准入（Sigstore Policy / Kyverno）+ 中央 SBOM（Dependency-Track）+ Renovate 自动升级** 是国内可落地的完整方案。最大教训来自 Log4Shell：**没有 SBOM 的企业 = 看不见自己用了什么 = 应急失败**。先把 SBOM 全企业铺开（哪怕不签名），就战胜了 80% 的公司。
