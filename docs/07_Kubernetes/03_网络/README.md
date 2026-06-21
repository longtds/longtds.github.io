# 网络

## CNI 原理

CNI（Container Network Interface）是 K8s 的网络接口标准，负责为 Pod 分配 IP 和配置网络。

## Cilium

Cilium 基于 eBPF 实现，是目前 K8s 网络的最佳选择。

```bash
# 安装 Cilium
helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium --namespace kube-system \
  --set ipam.mode=cluster-pool \
  --set ipam.operator.clusterPoolIPv4PodCIDR=10.244.0.0/16

# 验证
cilium status
cilium connectivity test
```

## Ingress-Nginx

```bash
# 部署 Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx

# Ingress 示例
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app
  annotations:
    ingress.class: nginx
spec:
  rules:
  - host: app.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

## 常见网络问题排查

```bash
# 检查 Pod 网络
kubectl exec -it <pod> -- ip a
kubectl exec -it <pod> -- ping <other-pod-ip>

# DNS 排查
kubectl run test --image=busybox --rm -it -- nslookup kubernetes

# Cilium 排查
cilium endpoint list
cilium connectivity diagnose
```
