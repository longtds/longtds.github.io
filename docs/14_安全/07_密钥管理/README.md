# 密钥管理（Secrets Management）

> 密钥是企业最敏感的资产，**90% 的数据泄漏由密钥失控引起**。密钥管理 = 集中存储 + 最小权限 + 自动轮换 + 全程审计 + 应急回收。**HashiCorp Vault 是事实标准，国产替代品也已成熟**。

## 一、密钥管理的挑战

```
密钥泛滥的痛:
  ❌ 配置文件含明文密码
  ❌ Secrets 入 Git 仓库
  ❌ 环境变量公开可见
  ❌ 多人共享一把密钥
  ❌ 离职员工密钥未回收
  ❌ 密钥从不轮换
  ❌ 日志含密码
  ❌ 镜像内嵌 token
  ❌ K8s Secret 实为 base64（不是加密）
  ❌ 备份未加密

数据:
  - GitHub 每年发现 1000 万+ 公开仓库泄漏密钥
  - 80% 数据泄漏与凭证失控相关
  - 平均 280 天才能发现密钥泄漏
```

## 二、密钥类型

```
1. 用户凭证       密码 / Token / SSH 密钥 / MFA
2. 数据库凭证     DB Password / 连接串
3. API 密钥       AK/SK / Bearer Token
4. TLS 证书       Server / Client / mTLS
5. 加密密钥       AES / RSA / 应用层加密
6. 服务账号       K8s SA / OAuth Client Secret
7. 云凭证         AWS IAM / 阿里云 RAM / GCP SA
8. 签名密钥       Cosign / GPG / Code Signing
9. SSH Host 密钥  服务器主机标识
10. CA 私钥        最高级别保护

不同类型 → 不同生命周期 + 不同保护策略
```

## 三、密钥管理金字塔

```
                  ┌──────────────────┐
                  │  HSM             │  硬件安全模块（CA 根 / 高合规）
                  ├──────────────────┤
                  │  Vault / KMS     │  集中存储 + 动态生成 + 自动轮换
                  ├──────────────────┤
                  │  Secrets Mgr     │  AWS SM / Azure Key Vault / 阿里 KMS
                  ├──────────────────┤
                  │  K8s Secret      │  仅运行时（etcd 加密）
                  ├──────────────────┤
                  │  Local           │  ❌ 永远不要明文文件
                  └──────────────────┘
```

## 四、HashiCorp Vault（事实标准）

### 4.1 Vault 核心能力

```
1. Static Secrets        KV 存储（密码 / API Key）
2. Dynamic Secrets       按需生成（DB / Cloud / SSH）⭐ 最强
3. Transit Encryption    应用层加密即服务
4. PKI                   颁发证书（替代 Let's Encrypt 内网）
5. SSH 签名              CA 签名 SSH key（替代分发 authorized_keys）
6. Tokens                短期访问 token
7. Wrapping              一次性 secret
8. Identity              身份 + 实体
9. Replication           多 DC / 多集群
10. Audit                完整审计
```

### 4.2 部署架构

```
单机（POC）:
  vault server -dev

生产 HA:
  3-5 节点 Raft / Consul backend
  TLS + 负载均衡
  Auto-unseal（AWS KMS / Azure Key Vault / HSM）

K8s 部署:
  helm install vault hashicorp/vault \
    --set='server.ha.enabled=true' \
    --set='server.ha.raft.enabled=true' \
    --set='server.ha.replicas=3'
```

### 4.3 必备配置（生产）

```hcl
# config.hcl
ui = true

storage "raft" {
  path = "/vault/data"
  node_id = "node-1"
  retry_join {
    leader_api_addr = "https://vault-1.svc:8200"
  }
}

listener "tcp" {
  address = "0.0.0.0:8200"
  cluster_address = "0.0.0.0:8201"
  tls_cert_file = "/vault/tls/tls.crt"
  tls_key_file  = "/vault/tls/tls.key"
  tls_min_version = "tls13"
}

seal "awskms" {                       # Auto-unseal
  region = "us-east-1"
  kms_key_id = "alias/vault-unseal"
}

api_addr = "https://vault.company.com"
cluster_addr = "https://vault-1.internal:8201"

# 关键审计
audit {
  type = "file"
  path = "/vault/logs/audit.log"
}
```

### 4.4 初始化与解封

```bash
# 初始化（生成 5 把解封 key + root token）
vault operator init -key-shares=5 -key-threshold=3
# 妥善保管 5 把解封 key + Root Token

# 解封（至少 3 把）
vault operator unseal <key1>
vault operator unseal <key2>
vault operator unseal <key3>

# 登录
vault login <root-token>

# 启用 Auto-unseal 后不需要手动解封

# 撤销 Root Token（推荐生产）
vault token revoke <root-token>
# 后续用 OIDC / LDAP / K8s 认证
```

### 4.5 KV Secrets

```bash
# v2 KV 引擎
vault secrets enable -path=secret kv-v2

# 写入
vault kv put secret/prod/db username=admin password=supersecret
vault kv put secret/prod/api key=abc123

# 读取
vault kv get secret/prod/db
vault kv get -field=password secret/prod/db

# 版本管理（v2 支持历史）
vault kv get -version=2 secret/prod/db
vault kv rollback -version=1 secret/prod/db
```

### 4.6 Dynamic Secrets（杀手锏）

#### Database

```bash
# 启用 DB engine
vault secrets enable database

# 配置数据库连接
vault write database/config/mysql-prod \
    plugin_name=mysql-database-plugin \
    connection_url="{{username}}:{{password}}@tcp(mysql.svc:3306)/" \
    allowed_roles="readonly,readwrite" \
    username="vault-admin" \
    password="..."

# 定义角色（Vault 会用模板创建用户）
vault write database/roles/readonly \
    db_name=mysql-prod \
    creation_statements="CREATE USER '{{name}}'@'%' IDENTIFIED BY '{{password}}'; \
                         GRANT SELECT ON app.* TO '{{name}}'@'%';" \
    default_ttl="1h" \
    max_ttl="24h"

# 应用请求短期账号
vault read database/creds/readonly
# Output:
#   username: v-app-readonly-Xy7z2a-1672934
#   password: ZsK0fPx9Aq...
#   lease_duration: 1h

# 自动过期 + 自动 DROP USER
```

#### Cloud (AWS)

```bash
vault secrets enable aws
vault write aws/config/root \
    access_key=AKIA... \
    secret_key=...

vault write aws/roles/s3-ro \
    credential_type=iam_user \
    policy_document=- <<EOF
{ "Version": "2012-10-17",
  "Statement": [{"Effect": "Allow", "Action": "s3:Get*", "Resource": "*"}] }
EOF

# 临时获取
vault read aws/creds/s3-ro
# → 临时 AK/SK，自动过期
```

#### SSH

```bash
vault secrets enable ssh
vault write ssh/roles/admin \
    key_type=ca \
    allowed_users=ops,sre \
    default_user=ops \
    allow_user_certificates=true \
    ttl=30m

# 应用申请短期 SSH 证书
vault write ssh/sign/admin public_key=@id_rsa.pub \
  valid_principals=ops ttl=30m \
  | jq -r .data.signed_key > id_rsa-cert.pub

# 用证书登录（服务器配置 TrustedUserCAKeys）
ssh -i id_rsa -i id_rsa-cert.pub server
```

### 4.7 Transit（应用层加密即服务）

```bash
vault secrets enable transit
vault write -f transit/keys/orders-pii

# 加密（应用调用）
vault write transit/encrypt/orders-pii plaintext=$(echo -n "1234-5678-9012" | base64)
# → ciphertext=vault:v1:abcdef...

# 解密
vault write transit/decrypt/orders-pii ciphertext=vault:v1:abcdef...

# 应用代码:
#   - 不持有密钥
#   - 每次加解密调 Vault
#   - 密钥轮换不需要应用改代码
```

### 4.8 PKI（内网 CA）

```bash
# Root CA
vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=87600h pki
vault write pki/root/generate/internal common_name="company.com" ttl=87600h

# Intermediate CA
vault secrets enable -path=pki_int pki
vault write -format=json pki_int/intermediate/generate/internal \
    common_name="company Intermediate" | jq -r .data.csr > pki_int.csr

# 签 Intermediate
vault write -format=json pki/root/sign-intermediate csr=@pki_int.csr \
    format=pem_bundle ttl=43800h | jq -r .data.certificate > pki_int.pem
vault write pki_int/intermediate/set-signed certificate=@pki_int.pem

# 配置角色
vault write pki_int/roles/svc \
    allowed_domains=company.com,svc.cluster.local \
    allow_subdomains=true \
    max_ttl=720h

# 应用申请证书
vault write pki_int/issue/svc common_name=order-api.svc.cluster.local ttl=24h
```

### 4.9 认证方式（Auth Methods）

| 方法 | 适合 |
|:---|:---|
| **Token** | 默认，bootstrap |
| **Kubernetes** | Pod 用 SA token 认证 ⭐ |
| **OIDC / OAuth** | 用户走 SSO |
| **LDAP / AD** | 企业目录 |
| **AppRole** | 应用对应用 |
| **Cert (mTLS)** | 强证书 |
| **AWS / GCP / Azure** | 云原生 |
| **JWT** | CI/CD 集成 |

```bash
# K8s 认证
vault auth enable kubernetes
vault write auth/kubernetes/config \
    kubernetes_host=https://kubernetes.default \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
    token_reviewer_jwt=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)

vault write auth/kubernetes/role/order-api \
    bound_service_account_names=order-api \
    bound_service_account_namespaces=prod \
    policies=order-api-policy \
    ttl=1h
```

### 4.10 Policy（HCL）

```hcl
# order-api-policy.hcl
# 只能读特定 KV
path "secret/data/prod/db" {
  capabilities = ["read"]
}
# 可申请 DB 动态凭证
path "database/creds/readonly" {
  capabilities = ["read"]
}
# Transit 加解密
path "transit/encrypt/orders-pii" {
  capabilities = ["update"]
}
path "transit/decrypt/orders-pii" {
  capabilities = ["update"]
}
```

```bash
vault policy write order-api-policy order-api-policy.hcl
```

## 五、K8s 集成 Vault

### 5.1 三种集成方式

| 方式 | 特点 |
|:---|:---|
| **Vault Agent Injector** | Sidecar 注入，模板渲染到文件 |
| **CSI Driver** | 挂载 Volume，更接近原生 Secret |
| **External Secrets Operator (ESO)** | 同步到 K8s Secret |

### 5.2 Agent Injector 实战

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: order-api }
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "order-api"
        vault.hashicorp.com/agent-inject-secret-db: "database/creds/readonly"
        vault.hashicorp.com/agent-inject-template-db: |
          {{- with secret "database/creds/readonly" -}}
          DB_USER={{ .Data.username }}
          DB_PASS={{ .Data.password }}
          {{- end }}
    spec:
      serviceAccountName: order-api
      containers:
        - name: app
          image: harbor/order-api:1.0
          env:
            - name: DB_CONFIG
              value: /vault/secrets/db
```

注入 Sidecar 后：
- 应用启动前 Vault Agent 申请 secret
- 渲染到 `/vault/secrets/db`
- 应用直接读文件
- 自动续期 + 重新渲染

### 5.3 ESO（External Secrets Operator）

```yaml
# SecretStore
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata: { name: vault-store, namespace: prod }
spec:
  provider:
    vault:
      server: https://vault.company.com
      path: secret
      version: v2
      auth:
        kubernetes:
          mountPath: kubernetes
          role: order-api

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata: { name: order-api-secrets, namespace: prod }
spec:
  refreshInterval: 1h
  secretStoreRef: { name: vault-store, kind: SecretStore }
  target: { name: order-api-secrets }
  data:
    - secretKey: DB_PASS
      remoteRef: { key: prod/db, property: password }
    - secretKey: API_KEY
      remoteRef: { key: prod/api, property: key }
```

ESO 优势：**应用代码零改造**，原本读 ENV 还是读 ENV。

### 5.4 CSI Driver

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: vault-db }
spec:
  provider: vault
  parameters:
    roleName: order-api
    objects: |
      - objectName: "db-password"
        secretPath: "secret/data/prod/db"
        secretKey: "password"

---
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: app
      volumeMounts:
        - name: secrets
          mountPath: /etc/secrets
          readOnly: true
  volumes:
    - name: secrets
      csi:
        driver: secrets-store.csi.k8s.io
        readOnly: true
        volumeAttributes:
          secretProviderClass: vault-db
```

## 六、云原生 Secrets Manager

### 6.1 AWS Secrets Manager

```bash
# 创建
aws secretsmanager create-secret \
  --name prod/db \
  --secret-string '{"username":"admin","password":"..."}'

# 读取
aws secretsmanager get-secret-value --secret-id prod/db

# 自动轮换（配 Lambda）
aws secretsmanager rotate-secret --secret-id prod/db
```

### 6.2 阿里云 KMS Secret Manager

```bash
aliyun kms CreateSecret --SecretName prod-db \
  --VersionId v1 --SecretData '{"password":"..."}'

aliyun kms GetSecretValue --SecretName prod-db
```

### 6.3 Azure Key Vault / GCP Secret Manager

类似能力，与各自 IAM 深度集成。

### 6.4 选型对比

| 工具 | 多云 | 动态密钥 | PKI | 价格 |
|:---|:---:|:---:|:---:|:---:|
| **Vault** | ✅ | ⭐⭐⭐⭐⭐ | ✅ | 开源 / Enterprise |
| **AWS SM** | AWS | ⭐⭐ | 部分 | 按 secret 收费 |
| **Azure KV** | Azure | ⭐⭐ | ✅ | 按操作收费 |
| **GCP SM** | GCP | ⭐⭐ | 部分 | 按 secret 收费 |
| **阿里 KMS** | 阿里 | ⭐⭐ | ✅ | 按版本/操作 |
| **国产 SealedSecrets** | 任意 | ❌ | ❌ | 开源 |

**结论**：
- 多云 / 强需求 → **Vault**
- 单云 → 云厂商原生 SM
- 简单场景 → SealedSecrets / SOPS

## 七、SOPS（文件级加密）

```bash
# 用 age / GPG / KMS 加密 YAML
brew install sops age

# 生成 age key
age-keygen -o ~/.age/key.txt
# Public: age1...

# .sops.yaml
creation_rules:
  - path_regex: secrets/.*\.yaml$
    age: age1xyz...

# 加密
sops --encrypt --in-place secrets/db.yaml

# 解密
sops --decrypt secrets/db.yaml

# 与 GitOps 配合（Flux/Argo CD 内置支持）
```

## 八、SealedSecrets

```bash
# 集群部署
helm install sealed-secrets sealed-secrets/sealed-secrets

# 客户端加密（用集群公钥）
echo -n mypassword | kubectl create secret generic mysecret \
  --dry-run=client --from-file=password=/dev/stdin -o yaml | \
  kubeseal --controller-namespace=sealed-secrets -o yaml > sealed.yaml

# sealed.yaml 入 Git，集群自动解密为 Secret
```

## 九、密钥轮换（Rotation）

### 9.1 轮换原则

```
✅ 短期 token > 长期密钥
✅ 动态生成 > 静态存储
✅ 自动化 > 人工
✅ 应用无感（dual key 过渡）
✅ 审计完整

轮换周期建议:
  长期 API key      30-90 天
  数据库密码        14-30 天
  动态密钥          按 lease（1-24h）
  TLS 证书          90 天（Let's Encrypt 强制）
  根密钥            1-3 年（HSM 严格管控）
```

### 9.2 自动化轮换

```python
# 例: 30 天自动轮换 DB 密码
import hvac
import secrets

client = hvac.Client(url='https://vault.company.com', token='...')

def rotate_db_password():
    new_pwd = secrets.token_urlsafe(32)
    
    # 1. 数据库内改密码
    db.execute(f"ALTER USER admin IDENTIFIED BY '{new_pwd}'")
    
    # 2. Vault 更新
    client.secrets.kv.v2.create_or_update_secret(
        path='prod/db',
        secret={'username': 'admin', 'password': new_pwd}
    )
    
    # 3. 触发应用重载（K8s rolling restart）
    k8s.rolling_restart(namespace='prod', deployment='order-api')
    
    # 4. 验证
    if not verify_connections():
        rollback(old_pwd)

# Cron: 每月 1 号 3 点
```

### 9.3 双 key 过渡（避免抖动）

```
T0:  生成新 key
T0~T+24h:  应用同时接受新旧 key（dual-validating）
T+24h:  下线旧 key
T+24h+:  仅新 key

工具:
  - Vault 自带 versioning
  - 自研业务接口"双向兼容期"
```

## 十、审计与合规

### 10.1 Vault Audit

```bash
# 启用文件 audit
vault audit enable file file_path=/vault/logs/audit.log

# 启用 syslog
vault audit enable syslog tag=vault facility=AUTH

# 多个 audit device（高可用）
vault audit enable -path=file1 file file_path=/vault/logs/audit1.log
vault audit enable -path=file2 file file_path=/vault/logs/audit2.log
```

### 10.2 关键事件监控

```
告警条件:
  ⚠️ Root token 被使用
  ⚠️ 异常时段访问
  ⚠️ 异常 IP 访问
  ⚠️ 大量 401 / 403
  ⚠️ Policy 变更
  ⚠️ 密钥导出（list keys）
  ⚠️ Sealing / Unsealing
```

### 10.3 合规要求

```
等保 2.0:
  - 加密密钥安全管理
  - 关键操作审计
  - 数据加密存储

PCI-DSS:
  - 密钥分层（DEK + KEK）
  - 双人控制
  - 年度轮换
  - HSM 保护

GDPR / 个保法:
  - 数据加密（静态 + 传输）
  - 密钥与数据分离
  - 审计访问
```

## 十一、HSM（硬件安全模块）

```
何时需要 HSM:
  ✅ CA 根证书私钥
  ✅ 加密货币私钥
  ✅ 强合规（金融 / 政府 / 军用）
  ✅ FIPS 140-2/3 Level 3+

主流产品:
  - Thales Luna
  - Utimaco
  - 国密 SM2/3/4 HSM（江南天安 / 三未信安）
  - AWS CloudHSM
  - 阿里云加密机
  - 腾讯云加密机

Vault 集成:
  seal "pkcs11" {
    lib = "/usr/lib/libCryptoki2_64.so"
    slot = "0"
    pin = "..."
    key_label = "vault-key"
    hmac_key_label = "vault-hmac"
  }
```

## 十二、应急响应

### 12.1 密钥泄漏处置

```
🚨 1. 立即撤销
   vault token revoke <token>
   或 vault lease revoke <lease-id>
   或修改云厂商 IAM key

🚨 2. 排查影响
   - 该 key 关联的资源
   - 该 key 的访问历史
   - 是否已被滥用（CloudTrail / Audit）

🚨 3. 生成新 key + 全量替换
   - 应用 rolling restart
   - 双 key 过渡

🚨 4. 复盘
   - 泄漏路径（Git? 日志? 截图? 内部?）
   - 加强防护
   - 培训 / 改进流程
```

### 12.2 Vault 灾难恢复

```
日常:
  ✅ 解封 key 5 把分散（多人保管）
  ✅ Raft snapshot 定期备份
  ✅ 异地备份（加密）
  ✅ DR 集群（Performance / DR Replication）

故障:
  vault operator raft snapshot save snap.bin
  # 异机恢复
  vault operator raft snapshot restore snap.bin
```

## 十三、最佳实践 Checklist

```
基础:
☐ 集中密钥管理（Vault / Cloud SM）
☐ 应用代码不存密钥
☐ Git 不存密钥（gitleaks 扫描）
☐ 镜像不含密钥
☐ 配置文件不含明文

Vault:
☐ Auto-unseal
☐ HA 集群 (Raft 3-5 节点)
☐ TLS 必启
☐ 审计开启
☐ 解封 key 分散保管
☐ Root token 撤销
☐ Policy 最小化
☐ 命名空间隔离

动态密钥:
☐ DB 密码动态生成
☐ Cloud AK 动态生成
☐ SSH CA 签名
☐ PKI 内网证书

K8s:
☐ ESO / Vault Injector / CSI 任选其一
☐ K8s Secret 不入 Git
☐ etcd 加密
☐ ServiceAccount 短期 token

轮换:
☐ 自动轮换流水线
☐ 双 key 过渡
☐ TLS 自动续期（Let's Encrypt / Vault PKI）
☐ 月度密钥审计

应急:
☐ 撤销 API 演练
☐ 备份 + 异地
☐ DR 集群
☐ IR 剧本
```

## 十四、常见坑

| 坑 | 建议 |
|:---|:---|
| **密钥入 Git** | gitleaks + Pre-commit |
| **Vault 单节点** | Raft HA |
| **手动解封** | Auto-unseal |
| **Root token 长期用** | OIDC / K8s 认证 |
| **K8s Secret 当库存** | ESO / Injector |
| **etcd 未加密** | 必启 encryption-config |
| **凭证不轮换** | 自动化流水线 |
| **K8s Secret 直接 base64** | 不是加密 |
| **API key 共享** | 每应用独立 |
| **离职不清理** | OIDC + 退出流程 |
| **Vault 备份缺失** | 每日 raft snapshot |
| **Policy 全开** | 最小权限 |
| **Audit 不接 SIEM** | 必接 |
| **K8s SA 自动挂载** | 不用时关 |
| **HSM 选错** | 强合规才用 |

## 十五、推荐栈（2025）

### 15.1 小团队

```
中心: Vault Open Source 单实例 / 云厂 SM
K8s:  External Secrets Operator + Vault
轮换: 手动 + 文档
扫描: gitleaks + trufflehog
```

### 15.2 中大企业

```
中心:  Vault Enterprise HA (3-5 节点) + Auto-unseal
认证:  OIDC + K8s + AppRole
动态:  DB + AWS/Aliyun + SSH CA
PKI:   内网 CA（替代多个证书工具）
K8s:   Vault Injector + ESO 混用
轮换:  自动化流水线（Jenkins / GitLab）
审计:  Audit → Splunk / Wazuh
HSM:   关键场景（CA 根）
DR:    跨 region replication
```

### 15.3 国产 / 信创

```
中心:  Vault / 阿里云 KMS / 腾讯云 KMS / 华为云 KMS
HSM:   江南天安 / 三未信安 / 国密 SM 系列
密码:  国密算法（SM2/3/4）
合规:  等保 2.0 + 密评
```

## 十六、学习路径

```
入门（1 周）:
  1. Vault 单机 dev 模式
  2. KV 读写
  3. K8s auth
  4. gitleaks 接 pre-commit

中级（1 个月）:
  5. Vault HA 集群
  6. Dynamic Secrets (DB)
  7. ESO 部署 + 同步
  8. 审计 + 监控
  9. 应用集成 Vault

高级（3 个月）:
  10. PKI 内网 CA
  11. Transit 应用层加密
  12. SSH CA 签名
  13. 自动轮换流水线
  14. DR + 多 DC
  15. HSM 集成
  16. 合规审计
```

## 十七、参考资料

```
官方:
  - HashiCorp Vault: https://developer.hashicorp.com/vault
  - External Secrets: https://external-secrets.io/
  - SOPS: https://github.com/getsops/sops
  - SealedSecrets: https://github.com/bitnami-labs/sealed-secrets

书:
  - 《Running Hashicorp Vault in Production》
  - 《Secrets Management with HashiCorp Vault》
  - 《Modern Cryptography for Cybersecurity Professionals》

标准:
  - NIST SP 800-57 Key Management
  - FIPS 140-2/3
  - PCI-DSS Key Management
  - GM/T 0028 国密标准

社区:
  - r/hashicorp
  - HashiCorp User Groups
  - 国内: HashiCorp 中文社区
```

> 📖 **核心判断**：密钥管理是企业安全的"皇冠明珠"。**Vault + 动态密钥 + Auto-unseal + ESO + 自动轮换 + 审计** 是 2025 黄金组合。最容易翻车的不是技术，而是**密钥入 Git、应用代码硬编码、不轮换、共享一把 key**——把这四件事消灭，密钥泄漏风险降 90%。**动态密钥（Vault DB / Cloud / SSH）是杀手锏**：临时凭证 + 自动过期 + 全程审计，从根本上解决了"密钥从不轮换"的世纪难题。
