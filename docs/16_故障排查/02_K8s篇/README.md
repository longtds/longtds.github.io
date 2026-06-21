# K8s 篇故障排查

## Pod CrashLoopBackOff

```bash
# 1. 查看 Pod 状态
kubectl get pod <pod-name> -o wide

# 2. 查看日志
kubectl logs <pod-name> --tail=50
kubectl logs <pod-name> --previous  # 查看上一次启动的日志

# 3. 查看事件
kubectl describe pod <pod-name>

# 4. 检查资源限制
kubectl get pod <pod-name> -o yaml | grep -A5 resources
```

## Pod Pending

```bash
# 1. 查看事件
kubectl describe pod <pod-name>

# 2. 检查节点资源
kubectl describe node <node-name>

# 3. 检查 PVC
kubectl get pvc
kubectl describe pvc <pvc-name>
```

## Node NotReady

```bash
# 1. 查看节点状态
kubectl describe node <node-name>

# 2. SSH 到节点检查
kubectl get nodes
# 登录节点
journalctl -u kubelet -n 100 --no-pager
systemctl status kubelet
```

## ETCD 性能问题

```bash
# 检查 ETCD 延迟
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  check perf

# 查看 ETCD 告警
etcdctl alarm list

# 磁盘 IO 延迟（ETCD 对 IO 敏感）
iostat -x 1
```
