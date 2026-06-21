# 密钥管理

## External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretstore
    kind: SecretStore
  target:
    name: database-credentials
  data:
    - secretKey: username
      remoteRef:
        key: prod/database
        property: username
    - secretKey: password
      remoteRef:
        key: prod/database
        property: password
```

## HashiCorp Vault

```bash
# 写入密钥
vault kv put secret/database username=admin password=***

# 读取密钥
vault kv get secret/database

# 动态密钥（数据库临时账号）
vault read database/creds/app-role
```
