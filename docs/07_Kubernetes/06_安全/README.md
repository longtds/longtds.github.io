# 安全

## RBAC

```yaml
# 只读角色
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
```

## Pod Security Standards

| 策略 | 说明 | 典型场景 |
|:---|:---|:---|
| Privileged | 无限制 | 系统组件 |
| Baseline | 基本限制 | 通用 |
| Restricted | 严格限制 | 生产环境 |

## OPA Gatekeeper

```yaml
# 禁止特权容器
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPrivilegedContainer
metadata:
  name: no-privileged
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces:
      - "production"
  parameters: {}
```

## Kubescape 安全扫描

```bash
# 安装
curl -s https://raw.githubusercontent.com/kubescape/kubescape/master/install.sh | /bin/bash

# 扫描集群
kubescape scan --submit

# 扫描特定框架
kubescape scan framework nsa
kubescape scan framework mitre
```
