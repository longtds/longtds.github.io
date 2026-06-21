# Kafka

## 部署

```bash
# Strimzi Operator（K8s 原生）
kubectl create namespace kafka
kubectl apply -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka

# 创建 Kafka 集群
cat <<EOF | kubectl apply -n kafka -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: kafka-cluster
spec:
  kafka:
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
    storage:
      type: persistent-claim
      size: 100Gi
      deleteClaim: false
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 20Gi
EOF
```

## 核心概念

| 概念 | 说明 |
|:---|:---|
| Topic | 消息分类 |
| Partition | 分区，扩展并行度 |
| Broker | 服务器节点 |
| Producer | 生产者 |
| Consumer | 消费者 |
| Consumer Group | 消费组，负载均衡 |
| ISR | 同步副本集合 |
| Offset | 消息偏移量 |

## 调优

```bash
# 生产者
ack=all           # 最强可靠性
batch.size=65536  # 批量大小
linger.ms=10      # 等待时间
compression.type=snappy  # 压缩

# 消费者
fetch.min.bytes=1
fetch.max.wait.ms=500
max.poll.records=500
```

## 常见故障

- **Rebalance**：消费者加入/离开触发，可通过 `group.instance.id` 静态成员减少
- **ISR 收缩**：副本同步跟不上，检查网络和磁盘 IO
- **磁盘满**：配置 log retention 和 cleanup policy
