# Kafka

> 全球部署最广的分布式流处理平台。**大数据/日志/CDC/AIOps 的事实总线**——把数据从一处搬到任何地方，吞吐百万消息/秒不在话下。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2010 | LinkedIn 内部启动 Kafka（Jay Kreps、Jun Rao、Neha Narkhede 三人组）|
| 2011 | 开源捐献 Apache 基金会 |
| 2014 | 创始团队成立 **Confluent**（商业公司）|
| 2017 | **Kafka Streams** 流处理 GA |
| 2019 | 1.0+ 引入 Exactly-Once 语义 |
| 2021 | 2.8 开始去 ZooKeeper（**KRaft 模式**预览） |
| 2022 | 3.3 KRaft 生产就绪 |
| 2024 | **3.7+ ZooKeeper 完全可移除** |
| 2025 | 4.0 移除 ZooKeeper，KRaft 唯一模式 |

> ⚠️ **重要变化**：2024+ 新建 Kafka 集群直接用 **KRaft 模式**，**不再需要 ZooKeeper**。

## 二、Kafka 是什么

```
不是简单的消息队列，而是一套"分布式提交日志 (Distributed Commit Log)"
   ↓
特点:
  - 消息持久化（按时间或大小保留，不删）
  - 顺序写磁盘（极致吞吐）
  - 副本机制（高可用）
  - Consumer 自己维护 offset（消费灵活）
  - 主题分区（水平扩展）
  - 流处理一等公民
```

### 三大典型角色

```
Producer → Kafka → Consumer
            ↑
        Broker 集群（多节点）
            ↓
        Topic / Partition / Replica
```

## 三、核心概念

| 概念 | 说明 |
|:---|:---|
| **Broker** | 一个 Kafka 节点（推荐 3+） |
| **Topic** | 消息分类（Topic 内有多个 Partition） |
| **Partition** | 主题分区，并行单位 |
| **Replica** | 副本（Leader + Follower） |
| **ISR** | In-Sync Replicas（同步副本集合）|
| **Offset** | 消息在分区内的位移 |
| **Consumer Group** | 消费组，组内分区独占 |
| **Controller** | 集群控制器（KRaft 内置 quorum） |
| **Segment** | 物理日志文件分段（log/index）|

## 四、核心功能

```
1. 高吞吐: 百万 msg/s（单集群）
2. 持久化: 默认 7 天可配
3. 副本: 多副本 + ISR + min.insync.replicas
4. 顺序保证: 分区内有序
5. 水平扩展: 增加 Broker + Partition
6. Exactly-Once: 幂等 Producer + 事务
7. 流处理: Kafka Streams、KSQL
8. Connect: 与外部系统对接 (CDC/ES/JDBC)
9. Schema Registry: Avro/Protobuf 类型管理
10. Tiered Storage: 冷数据上 S3（3.6+）
```

## 五、架构原理

```
┌─────────────── 集群 ────────────────────┐
│ Broker 1 (Leader for P0, Follower P1)   │
│ Broker 2 (Leader for P1, Follower P2)   │
│ Broker 3 (Leader for P2, Follower P0)   │
│ Controller (KRaft Quorum)               │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────── Topic ───────────────────┐
│ Partition 0  [ msg0 msg1 msg2 ... ]    │
│ Partition 1  [ msg0 msg1 msg2 ... ]    │
│ Partition 2  [ msg0 msg1 msg2 ... ]    │
│ ── 顺序写磁盘 + Page Cache 缓存          │
└──────────────┬──────────────────────────┘
               ↓
┌────────── 消费 ─────────────────────────┐
│ Consumer Group A:                       │
│   C1 → P0    C2 → P1, P2                │
│ Consumer Group B（独立 offset）:         │
│   C1 → P0, P1    C2 → P2                │
└─────────────────────────────────────────┘
```

### 为什么这么快

```
1. 顺序写磁盘（接近内存速度）
2. 零拷贝 (sendfile)
3. Page Cache（OS 文件缓存）
4. 批量发送 + 压缩 (zstd/lz4)
5. 分区天然并行
6. Producer 异步 + 批量 Acks
```

## 六、使用场景

### ✅ 经典场景

| 场景 | 说明 |
|:---|:---|
| **日志聚合** | 替代 Flume，对接 ES/Loki |
| **业务消息总线** | 微服务解耦 |
| **CDC 数据同步** | Debezium → Kafka → ES/HBase |
| **流处理** | Flink/Spark Streaming 上游 |
| **事件溯源** | 业务事件持久化 |
| **指标埋点** | 客户端/服务端事件采集 |
| **大数据 ETL** | 数据仓库前置缓冲 |
| **AIOps** | 监控数据流 + 异常检测 |
| **LLM 数据管道** | 训练数据采集 |

### ⚠️ 不推荐场景

- **延时极敏感（< 1ms）** → 用 Redis Stream / NATS
- **超小规模（< 10 万消息/天）** → 用 RabbitMQ / SQS
- **复杂路由 / 优先级队列** → 用 RabbitMQ
- **强事务多 Topic 协调** → 用数据库 + outbox 模式

## 七、Kafka vs 其他消息系统

| 维度 | Kafka | RabbitMQ | RocketMQ | Pulsar | NATS JetStream |
|:---|:---|:---|:---|:---|:---|
| 类型 | 日志型 | 队列型 | 日志型 | 日志型 | 流型 |
| 吞吐 | 极高 | 中 | 高 | 极高 | 高 |
| 延迟 | 毫秒级 | 微秒级 | 毫秒 | 毫秒 | 微秒 |
| 顺序 | 分区内 | 队列内 | 分区内 | 分区内 | Stream 内 |
| 路由 | 简单 | 复杂 | 简单 | 简单 | 简单 |
| 存储/计算分离 | 否 | 否 | 否 | **是** | 否 |
| 多租户 | 一般 | 一般 | 一般 | **强** | 中 |
| 主流度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐（国内） | ⭐⭐⭐ | ⭐⭐⭐ |
| 国产替代 | RocketMQ | — | 阿里出品 | StreamNative | — |

## 八、最佳实践

### 8.1 集群规划

```
最小生产配置:
  3× Broker（KRaft 模式）
  ≥ 16 核 / 64GB / 4× NVMe SSD（独立日志盘）
  10G 网络
  
副本因子: 默认 3
min.insync.replicas: 2
acks: all（强一致）
```

### 8.2 Topic 设计

```
✅ 分区数 = 消费者数 × 1-2 倍（预留扩展）
✅ 单分区吞吐通常 10-50 MB/s
✅ 单 Broker 分区总数 < 4000
✅ Key 决定分区，相同 Key 必到同分区
✅ 命名: <domain>.<entity>.<event>  如 order.payment.created
❌ 分区数不要超过 100 万消息/秒所需
❌ 不要随意增减分区（消费顺序会乱）
```

### 8.3 Producer 最佳实践

```java
acks = all                       // 强一致
enable.idempotence = true        // 幂等（必开）
retries = Integer.MAX_VALUE
max.in.flight.requests = 5
batch.size = 32KB - 512KB
linger.ms = 10-100               // 攒批
compression.type = zstd          // 压缩首选
buffer.memory = 64MB
delivery.timeout.ms = 120000
```

### 8.4 Consumer 最佳实践

```java
enable.auto.commit = false         // 手动 commit
auto.offset.reset = earliest       // 或 latest
max.poll.records = 500
max.poll.interval.ms = 300000      // 业务慢要调大
session.timeout.ms = 45000
fetch.min.bytes = 1MB
fetch.max.wait.ms = 500
isolation.level = read_committed   // 配合事务
```

**消费正确姿势**：

```
1. 拉一批 → 处理 → 同步 commit
2. 慢消费要拆批或单独线程池
3. 处理失败 → 死信队列 (DLQ)
4. 幂等消费（业务侧去重）
5. 限制 max.poll.interval.ms 避免 Rebalance 风暴
```

### 8.5 关键参数

```ini
# server.properties
num.network.threads = 8
num.io.threads = 16
socket.send.buffer.bytes = 1048576
socket.receive.buffer.bytes = 1048576

# 日志保留
log.retention.hours = 168          # 7 天
log.retention.bytes = -1
log.segment.bytes = 1073741824     # 1G

# 副本
default.replication.factor = 3
min.insync.replicas = 2
unclean.leader.election.enable = false

# KRaft
process.roles = broker,controller
controller.quorum.voters = 1@n1:9093,2@n2:9093,3@n3:9093
```

### 8.6 高可用要点

```
✅ replication.factor = 3
✅ min.insync.replicas = 2
✅ acks = all
✅ unclean.leader.election = false
✅ 多机架分布（rack.id 配置）
✅ KRaft Controller 至少 3 个
✅ 监控 ISR 收缩、Under-Replicated Partitions
```

### 8.7 容量规划

```
单分区吞吐:    10-50 MB/s（取决于消息大小、磁盘）
单 Broker:    最多 50 万消息/秒、~1GB/s
单分区文件:    < 1TB（建议）
保留期 vs 磁盘: 算清！7 天 × 100MB/s = 60TB（含 3 副本）
```

## 九、运维命令速查

```bash
# Topic
kafka-topics.sh --bootstrap-server localhost:9092 --list
kafka-topics.sh --create --topic orders --partitions 6 --replication-factor 3
kafka-topics.sh --describe --topic orders
kafka-topics.sh --alter --topic orders --partitions 12

# Consumer Group
kafka-consumer-groups.sh --bootstrap-server ... --list
kafka-consumer-groups.sh --describe --group billing
kafka-consumer-groups.sh --reset-offsets --to-earliest --group billing --topic orders --execute

# 性能压测
kafka-producer-perf-test.sh --topic test --num-records 1000000 --record-size 1024 \
  --throughput -1 --producer-props bootstrap.servers=localhost:9092
kafka-consumer-perf-test.sh --bootstrap-server localhost:9092 --topic test --messages 1000000

# 副本检查
kafka-reassign-partitions.sh ...
kafka-leader-election.sh ...

# KRaft 元数据
kafka-metadata-shell.sh --snapshot /var/lib/kafka/__cluster_metadata-0/00000000000000000000.log
```

## 十、常见坑

| 坑 | 建议 |
|:---|:---|
| **不开幂等** | 必开 enable.idempotence |
| **acks=1 丢数据** | 用 acks=all + min.isr=2 |
| **Rebalance 风暴** | 增大 max.poll.interval.ms |
| **分区数过多** | 单 Broker < 4000，超大集群拆 |
| **磁盘满** | 监控 + 自动告警 + 定期清理 |
| **跨机房延迟高** | 用 MirrorMaker / Cluster Linking |
| **大消息（>1MB）** | 调 max.message.bytes + 拆分 |
| **Consumer Lag 滞涨** | 加 Consumer / 加分区 |
| **ZooKeeper 老坑** | 迁 KRaft |
| **没 DLQ** | 必加死信队列 |
| **没有 Schema 治理** | 上 Schema Registry |
| **OS 调优缺失** | 关 swap、numa、THP、调 vm.dirty |

## 十一、生态与工具

| 工具 | 用途 |
|:---|:---|
| **Kafka Connect** | 数据集成（JDBC/ES/S3） |
| **Kafka Streams** | JVM 流处理 |
| **ksqlDB** | SQL 风格流处理 |
| **Schema Registry** | Avro/Protobuf 类型管理 |
| **Debezium** | MySQL/PG CDC → Kafka |
| **MirrorMaker 2** | 跨集群复制 |
| **Cruise Control** | 自动均衡 |
| **Kafka UI / AKHQ / Conduktor** | Web 管理 |
| **Kowl / Kafka Manager** | 监控管理 |
| **Strimzi** | K8s Operator |
| **Confluent Cloud** | 商业托管 |

## 十二、监控指标（必看）

```
Broker:
  UnderReplicatedPartitions   ← 必须 = 0
  OfflinePartitionsCount      ← 必须 = 0
  RequestQueueSize / IdleRatio
  BytesIn/Out PerSec

Topic/Partition:
  MessagesInPerSec
  ProduceTotalTimeMs
  ConsumerLag                 ← 关键

Consumer:
  records-lag-max             ← 业务侧关注
  commit-rate / rebalance-rate

KRaft:
  CurrentControllerID
  MetadataLag
```

**工具**：JMX Exporter + Prometheus + Grafana / Confluent Control Center / Kafka UI

## 十三、Kafka in K8s

```
推荐方案: Strimzi Operator
  ✅ CRD 声明式
  ✅ 自动滚动升级
  ✅ TLS / 认证内置
  ✅ Cruise Control 集成

云方案:
  AWS MSK / Confluent Cloud / 阿里云 Kafka
  ✅ 免运维、按量付费
```

## 十四、国产替代

| 产品 | 厂商 | 说明 |
|:---|:---|:---|
| **RocketMQ** | 阿里捐 Apache | 国内主流，金融级 |
| **Pulsar** | StreamNative | 存算分离架构 |
| **TDMQ** | 腾讯云 | 多协议托管 |
| **AutoMQ** | 国产新势力 | Kafka 协议 + 存算分离 + 云原生 |

## 十五、学习路径

```
入门:
  1. 概念：Topic / Partition / Offset / Consumer Group
  2. KRaft 单机起一个 broker
  3. console producer/consumer 跑通

进阶:
  4. 3 节点集群（KRaft）+ 副本
  5. Java/Go Producer/Consumer 编程
  6. Exactly-Once 实战
  7. Connect + Debezium 跑一遍 CDC

高阶:
  8. Kafka Streams / Flink 集成
  9. Schema Registry + Avro
  10. 监控 + Cruise Control
  11. K8s + Strimzi 部署
  12. 跨集群 MirrorMaker / Cluster Linking
  13. Tiered Storage 冷数据
```

> 📖 **核心判断**：Kafka 是大数据/微服务/AI 数据管道的"主干道"。**ZooKeeper 时代终结**，新建集群一律 KRaft。规模超大或多租户严苛可选 Pulsar；国内金融场景仍多用 RocketMQ；云上要省心直接选托管。
