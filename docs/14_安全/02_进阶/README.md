# 进阶

> 安全进阶 = **DevSecOps 全链(SAST/DAST/SCA/IaC/Secret/Container/SBOM) + 容器运行时安全(Falco/Tetragon) + K8s 安全基线(PSS/NetworkPolicy/OPA Gatekeeper) + 服务网格 mTLS + Vault 全栈 + WAF 进阶(ModSec/雷池/阿里云) + 蜜罐 + 威胁情报 + 等保3级 + 国密改造 + SIEM 工程化**。本章面向独立维护安全平台的工程师。

## 一、DevSecOps 全链

```
左移 (Shift Left):
  IDE → Git → CI → 镜像 → 部署 → 运行时
  每阶段都查
  
工具矩阵:

阶段         工具                            扫描内容
─────────────────────────────────────────────────────
IDE         Snyk Plugin / CodeQL / Semgrep   编码即扫
Pre-commit  gitleaks ⭐ / trufflehog          Secret
Git         GitLeaks / Snyk / Dependabot     SCA + Secret
CI: SAST    SonarQube ⭐ / Semgrep / CodeQL   代码缺陷
CI: SCA     Snyk / OWASP DC ⭐ / Trivy        依赖漏洞
CI: IaC     Checkov ⭐ / tfsec / kube-bench   Terraform/K8s
CI: Container Trivy ⭐ / Grype / Snyk          镜像漏洞
CI: SBOM    Syft ⭐ / CycloneDX               物料清单
CI: License FOSSA / Black Duck                许可证
CD: 签名    cosign ⭐ + Rekor + Fulcio        镜像签名
CD: 策略   Kyverno ⭐ / Gatekeeper / Cosign   admission
Runtime    Falco ⭐ / Tetragon / Wazuh        异常检测
Runtime    Cilium NetworkPolicy ⭐            网络
Audit      K8s audit + Pixie + Coroot       日志
```

## 二、容器运行时安全

### 2.1 Falco

```yaml
# Helm
helm install falco falcosecurity/falco \
  --set driver.kind=ebpf \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true

# 规则 (Rego)
- rule: Shell in Container
  desc: A shell was spawned in container
  condition: container.id != host and proc.name in (shell_binaries)
  output: "Shell in container (user=%user.name container=%container.id)"
  priority: WARNING
```

### 2.2 Tetragon (eBPF)

```
基于 eBPF + CO-RE
更现代 + 性能好
Cilium 出品

能力:
  - syscall 级监控
  - 进程树
  - 网络
  - 文件
  - capability
  - 自动 enforcement (kill 进程)
```

### 2.3 对比

```
工具        机制       侵入     性能
Falco       eBPF/kmod  低       中
Tetragon    eBPF       极低     高 ⭐
Wazuh       agent      中       中
NeuVector   agent      高       中 (商业)
Sysdig      eBPF       低       中 (商业)
```

## 三、K8s 安全基线

```yaml
# Pod Security Standards (Restricted) ⭐
apiVersion: v1
kind: Namespace
metadata:
  name: prod
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
```

```yaml
# NetworkPolicy 默认拒绝
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny, namespace: prod }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
# 允许 monitoring 抓 metrics
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-monitoring, namespace: prod }
spec:
  podSelector: { matchLabels: { app: api } }
  ingress:
    - from: [{ namespaceSelector: { matchLabels: { name: monitoring } } }]
      ports: [{ port: 9090 }]
```

### 3.1 OPA Gatekeeper / Kyverno

```yaml
# Kyverno: 禁止 latest
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: disallow-latest-tag }
spec:
  validationFailureAction: enforce
  rules:
    - name: validate-image-tag
      match: { any: [{ resources: { kinds: [Pod] } }] }
      validate:
        message: "Tag :latest is forbidden"
        pattern:
          spec:
            containers:
              - image: "!*:latest"
```

### 3.2 镜像签名验证

```yaml
# Kyverno verifyImages (cosign)
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: verify-signatures }
spec:
  validationFailureAction: enforce
  rules:
    - name: verify
      match: { any: [{ resources: { kinds: [Pod] } }] }
      verifyImages:
        - imageReferences: ["registry.example.com/*"]
          attestors:
            - entries:
                - keys:
                    publicKeys: |-
                      -----BEGIN PUBLIC KEY-----
                      MFkw...
                      -----END PUBLIC KEY-----
```

### 3.3 kube-bench / CIS

```bash
docker run --rm --pid=host \
  -v /etc:/etc:ro -v /var:/var:ro \
  aquasec/kube-bench:latest run --targets master,node
```

## 四、服务网格 mTLS

```yaml
# Istio Strict
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata: { name: default, namespace: istio-system }
spec:
  mtls: { mode: STRICT }

# AuthorizationPolicy 零信任
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata: { name: deny-all, namespace: prod }
spec:
  {}                # 空 → 拒绝所有

---
# 显式允许
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata: { name: api-allow, namespace: prod }
spec:
  selector: { matchLabels: { app: api } }
  rules:
    - from:
        - source: { principals: ["cluster.local/ns/prod/sa/gateway"] }
      to: [{ operation: { methods: [GET, POST], paths: [/v1/*] } }]
```

## 五、Vault 全栈

```
DB 凭证:        dynamic, 1h TTL
Cloud:          dynamic IRSA/STS
SSH:             CA signed, 1h
TLS:             PKI engine + cert-manager
KV:             静态密钥 (尽量少)
Transit:        加解密即服务 (不存密文)

HA:
  3 副本 + Raft / Consul
  Auto-unseal (KMS / HSM)
  Audit Device 全开
  Performance Replication (多 region)
  
合规:
  国密 改造 (Tongsuo)
  HSM (SafeNet / 国产 HSM)
  审计 → SIEM
```

## 六、WAF 进阶

```
开源:
  ModSecurity ⭐ + OWASP CRS
  雷池 (Long Pillar) ⭐ 国产现代
  OpenResty + 自定义 Lua
  Coraza (Go, ModSec 兼容)

商业:
  阿里云 WAF
  腾讯 T-Sec
  Cloudflare WAF
  F5 / Imperva (硬件)

部署:
  反代层 (Nginx + ModSec)
  云上 (CDN + WAF)
  Service Mesh (Envoy + WAF filter)
  
策略:
  OWASP Top 10
  CC 防护 (限速 + 验证码)
  自定义规则 (业务)
  威胁情报 (黑 IP)
  Bot 防护
```

## 七、蜜罐 + 威胁情报

```
蜜罐:
  T-Pot ⭐ (集成多个)
  Cowrie (SSH)
  Honeyd
  HFish (国产)

部署:
  公网 DMZ + 内网穿插
  日志 → SIEM
  攻击者画像 + 自动黑名单

威胁情报:
  AlienVault OTX
  MISP ⭐ (开源平台)
  阿里云 / 奇安信 威胁情报
  IBM X-Force
  自动订阅 → SIEM IoC 匹配
```

## 八、API 安全

```
认证: OAuth 2.0 + JWT (验签 + exp)
限速: API Gateway (Kong / APISIX)
WAF: 接入 API
Schema: OpenAPI 校验
Rate Limiting: Token bucket
异常检测: 行为基线 + UEBA

OWASP API Top 10:
  Broken Object Level Authorization
  Broken Authentication
  Excessive Data Exposure
  Lack of Resources & Rate Limiting
  Broken Function Level Authorization
  Mass Assignment
  Security Misconfiguration
  Injection
  Improper Assets Management
  Insufficient Logging & Monitoring

工具:
  42Crunch (商业)
  Salt Security (商业)
  Kong + 自定义
  自研 + OPA + APISIX
```

## 九、数据安全

```
数据分类:
  公开 / 内部 / 机密 / 绝密
  PII / PHI / 金融 / 个保法 单独

加密:
  传输: TLS 1.3 ⭐
  存储: KMS (envelope) ⭐
  字段: AES-256-GCM / SM4
  密钥: Vault / KMS / HSM

脱敏:
  日志 (手机号 / 身份证 / 卡号)
  数据库 (查询脱敏 + 视图)
  备份 (脱敏副本给测试)

工具:
  阿里云数据脱敏
  Apache ShardingSphere Encrypt
  自研 + 中间件层
  
DLP (Data Loss Prevention):
  网络 (出口监控)
  终端 (USB / 邮件 / 上传)
  云 (Azure Purview / DSPM)
```

## 十、等保 3 级要点

```
身份鉴别:
  ☐ 唯一 + 复杂 + MFA
  ☐ 失败锁定 + 超时
  ☐ 双因素 国密

访问控制:
  ☐ 最小授权 + 分离
  ☐ 重要操作 双批
  ☐ MAC (强制访问)

数据完整 + 保密:
  ☐ 传输 SM4 / TLCP
  ☐ 存储 SM4 字段
  ☐ 密钥 国密 HSM

入侵防范:
  ☐ HIDS + IPS
  ☐ 漏洞扫描月度
  ☐ 补丁 季度
  ☐ 蜜罐

恶意代码:
  ☐ 主机 EDR
  ☐ 邮件网关
  ☐ 上网行为

可信验证:
  ☐ 国密 TPM/TCM
  ☐ 启动 + 运行 完整性

集中管控:
  ☐ SIEM 6mo
  ☐ 24x7 SOC
  ☐ 应急演练
  ☐ 安全策略 + 制度

合规:
  ☐ 每年测评
  ☐ 公安备案
  ☐ 整改报告
```

## 十一、国密改造

```
TLS:
  Tongsuo (BabaSSL) ⭐
  TLCP (双证书) / TLS 1.3 + GM
  国密浏览器 (火狐国密 / 360)

PKI:
  CFCA 国密证书
  自建国密 CA (Tongsuo)
  SM2 keypair

加密:
  SM4 (块对称, 替 AES)
  SM3 (Hash, 替 SHA-256)
  SM2 (非对称, 替 RSA/ECDSA)
  SM9 (标识密码)

实现:
  应用: GmSSL / Tongsuo + JNI/Go
  Web: Nginx + Tongsuo
  K8s: kube-apiserver Tongsuo
  存储: 数据库字段 SM4
  
HSM:
  SafeNet / Thales (国际)
  江南天安 / 三未信安 (国产)
```

## 十二、SIEM 工程化

```
架构:
  采集: Filebeat / Vector / Fluent Bit
  消息: Kafka (削峰)
  存储: ClickHouse / Elasticsearch / OpenSearch
  分析: Wazuh / Elastic Security / 阿里 SLS
  可视化: Kibana / Grafana
  告警: Webhook / 钉钉 / on-call

来源:
☐ Linux audit
☐ SSH / sudo
☐ K8s audit (RequestResponse)
☐ Application logs
☐ Nginx / Envoy
☐ Database (slow + audit)
☐ Cloud audit (CloudTrail / OSS / 阿里 ActionTrail)
☐ Firewall / WAF
☐ HIDS (Wazuh / Falco)
☐ IDS (Suricata)
☐ Vault audit
☐ Keycloak events

关联规则:
  - 失败登录 + 异地 → 高
  - root 提权 + 异常文件 → 关键
  - 数据库大量导出 → 关键
  - K8s admission 拒绝 → 中
  - 蜜罐触发 → 关键
```

## 十三、Checklist（进阶）

```
DevSecOps:
☐ SAST + DAST + SCA + IaC + Secret + Container + SBOM 全链
☐ cosign 镜像签名 + Rekor + Fulcio
☐ Kyverno admission 强制

运行时:
☐ Falco / Tetragon eBPF
☐ Wazuh HIDS
☐ K8s audit RequestResponse
☐ Pixie / Coroot 拓扑

K8s:
☐ Pod Security Standards: Restricted
☐ NetworkPolicy 默认拒
☐ Cilium / Calico 加密 + 国密
☐ kube-bench 季度

Mesh:
☐ Istio Strict mTLS
☐ Default Deny AuthorizationPolicy
☐ SPIFFE 工作负载

Vault:
☐ HA + Auto-unseal
☐ Dynamic 全栈
☐ 国密 HSM
☐ 审计 → SIEM

WAF:
☐ ModSec + OWASP CRS / 雷池 / 阿里
☐ CC 防护 + 限速
☐ Bot 防护

蜜罐:
☐ T-Pot + 内网穿插
☐ MISP 威胁情报
☐ 自动黑名单

API:
☐ 网关 (Kong/APISIX) 限速 + WAF
☐ Schema 校验
☐ OAuth + JWT
☐ OWASP API Top 10

数据:
☐ 分类 + 加密 + 脱敏
☐ KMS + Vault Transit
☐ DLP (出口监控)

等保 3:
☐ 全 10 项达标
☐ 国密改造
☐ HSM
☐ 24x7 SOC

国密:
☐ Tongsuo
☐ CFCA / 自建 CA
☐ SM2/SM3/SM4 全栈
☐ 国密 USB Key

SIEM:
☐ 全源接入 (Linux/K8s/App/DB/Cloud/Firewall/HIDS)
☐ Kafka 削峰
☐ ClickHouse 长期
☐ 关联规则 + 告警
```

## 十四、推荐栈（进阶）

```
DevSecOps:   SonarQube + Semgrep + Trivy + Checkov + cosign + Syft + Kyverno
运行时:     Falco / Tetragon ⭐ + Wazuh
K8s:        PSS + NetworkPolicy + Kyverno + kube-bench
Mesh:       Istio Strict + SPIRE
Vault:      HA + Dynamic + 国密 HSM
WAF:        雷池 ⭐ (国产) + ModSec + 阿里云
蜜罐:        T-Pot + MISP
API:        APISIX / Kong + OPA + OWASP API
数据:        KMS + ShardingSphere Encrypt + DSPM
等保:        等保 3 级 + 国密 + HSM
国密:        Tongsuo + CFCA + 江南天安 HSM
SIEM:       Wazuh + Elastic + Kafka + ClickHouse
```

> 📖 **核心判断**：安全进阶 = **DevSecOps 全链(SAST/SCA/IaC/Container/cosign/SBOM) + 运行时(Falco/Tetragon/eBPF) + K8s 基线(PSS+NetPol+Kyverno+kube-bench) + Mesh mTLS + Vault 全栈 + 雷池/ModSec WAF + 蜜罐+威胁情报 + API 安全 + 数据加密+脱敏+DLP + 等保3级+国密(Tongsuo/HSM) + SIEM 工程化**。能独立给企业搭"Trivy + Kyverno + Falco + Istio + Vault + 雷池 + Wazuh + Tongsuo + 等保3"完整安全平台，就具备安全运维进阶能力。
