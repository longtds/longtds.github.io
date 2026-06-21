# 网络安全

## TLS/SSL 证书

```bash
# cert-manager 自动证书
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: wildcard
spec:
  secretName: wildcard-tls
  dnsNames:
    - "*.company.com"
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
```

## WAF

ModSecurity 是开源的 WAF。

## VPN/堡垒机

- WireGuard：轻量级 VPN
- Apache Guacamole：Web SSH 堡垒机
