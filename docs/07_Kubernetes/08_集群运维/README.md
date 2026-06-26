# 集群运维

## ETCD 维护

```bash
# 备份
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /backup/etcd-snapshot-$(date +%Y%m%d).db

# 恢复
etcdctl snapshot restore /backup/etcd-snapshot.db \
  --data-dir=/var/lib/etcd-restored

# 性能检查
etcdctl check perf
```

## Velero 备份

```bash
# 安装
velero install \
  --provider aws \
  --bucket backups \
  --backup-location-config region=us-east,s3ForcePathStyle=true,s3Url=http://minio.company.com

# 备份
velero backup create daily-backup --ttl 720h

# 恢复
velero restore create --from-backup daily-backup
```

## 证书管理

```bash
# 查看证书到期时间
kubeadm certs check-expiration

# 续期
kubeadm certs renew all
systemctl restart kubelet

# 更新 kubeconfig
kubeadm init phase kubeconfig admin --config kubeadm-config.yaml
```

## 节点维护

```bash
# 节点排空（迁移 Pod）
kubectl drain node1 --ignore-daemonsets --delete-emptydir-data

# 节点恢复调度
kubectl uncordon node1

# 节点下线
kubectl delete node node1
```
