# 存储

## CSI 原理

CSI（Container Storage Interface）是 K8s 的存储接口标准，允许不同存储后端以插件形式接入。

## Rook + Ceph

Rook 在 K8s 上运行 Ceph 分布式存储。

```bash
# 部署 Rook Ceph
helm repo add rook-release https://charts.rook.io/release
helm install --create-namespace --namespace rook-ceph rook-ceph rook-release/rook-ceph

# 创建 CephCluster
cat <<EOF | kubectl apply -f -
apiVersion: ceph.rook.io/v1
kind: CephCluster
metadata:
  name: rook-ceph
  namespace: rook-ceph
spec:
  dataDirHostPath: /var/lib/rook
  mon:
    count: 3
  storage:
    useAllNodes: false
    useAllDevices: false
    config:
      databaseSizeMB: "1024"
      journalSizeMB: "1024"
    nodes:
    - name: node1
      devices:
      - name: sdb
EOF
```

## MinIO S3 对象存储

```bash
# MinIO Operator 部署
kubectl apply -k github.com/minio/operator
kubectl create tenant minio-tenant --servers 4 --capacity 4Ti
```

## 有状态应用存储方案

| 场景 | 推荐方案 | 说明 |
|:---|:---|:---|
| 数据库（MySQL/PG） | Rook Ceph/RWO | 块存储 |
| 文件存储 | NFS / CephFS | RWX |
| 日志/备份 | MinIO S3 | 对象存储 |
| AI 训练数据 | MinIO + PV | 高吞吐 |
