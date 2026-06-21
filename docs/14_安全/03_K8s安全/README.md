# K8s 安全

## OPA Gatekeeper 策略

```yaml
# 禁止所有容器以 root 运行
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-nonroot
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
  parameters:
    allowed: false
```

## Pod Security Standards

```yaml
# 命名空间级别应用
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Kubescape

```bash
kubescape scan --submit
kubescape scan framework nsa
kubescape scan framework mitre
```
