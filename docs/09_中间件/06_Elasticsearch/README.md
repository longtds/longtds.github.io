# Elasticsearch

## 部署

```bash
# ECK Operator（K8s 原生）
kubectl create -f https://download.elastic.co/downloads/eck/2.12.0/crds.yaml
kubectl apply -f https://download.elastic.co/downloads/eck/2.12.0/operator.yaml

# 创建 ES 集群
cat <<EOF | kubectl apply -f -
apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
  name: elastic
spec:
  version: 8.14.0
  nodeSets:
  - name: master
    count: 3
    config:
      node.roles: ["master"]
  - name: data
    count: 3
    config:
      node.roles: ["data", "ingest"]
    volumeClaimTemplates:
    - metadata:
        name: elasticsearch-data
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 500Gi
EOF
```

## 索引生命周期管理

```bash
PUT _ilm/policy/30d-retention
{
  "policy": {
    "phases": {
      "hot": { "actions": { "rollover": { "max_size": "50GB", "max_age": "1d" }}},
      "warm": { "min_age": "7d", "actions": { "forcemerge": { "max_num_segments": 1 }}},
      "delete": { "min_age": "30d", "actions": { "delete": {} }}
    }
  }
}
```

## 常见故障

| 问题 | 排查 |
|:---|:---|
| 集群 Red | `GET _cluster/health` 查看未分配分片 |
| JVM GC 抖动 | `GET _nodes/stats/jvm` 检查 GC 次数和时间 |
| 慢查询 | `GET _nodes/hot_threads` 查看热点线程 |
| 磁盘满 | 检查 ILM 策略，强制 rollover 或删除索引 |
