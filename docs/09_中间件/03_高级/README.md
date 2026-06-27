# 高级

> 中间件高级 = **分布式 NewSQL(TiDB/OceanBase/CockroachDB) + 数据库内核(MVCC/2PC/Raft/HTAP) + 海量数据治理(分库分表+冷热分层+TiFlash 列存) + Kafka 千万级 TPS 调优(零拷贝/Page Cache/Sendfile/批量) + Pulsar 存算分离架构 + Redis 万核(Pika/Tair/Dragonfly/KvRocks) + 多模 DB(MongoDB/Cassandra/Nebula/Milvus) + 向量数据库(pgvector/Milvus/Qdrant/Weaviate) + 时序数据库(TDengine/IoTDB/InfluxDB) + 国产数据湖(Paimon/Iceberg/Hudi) + DBaaS + 数据库容器化深度(KubeBlocks Operator 内核) + 跨地多活 + 国密合规**。本章面向 DBA / 中间件平台架构师。

## 一、分布式数据库（NewSQL）

### 1.1 TiDB（国产 HTAP 王者）

```
组件:
  PD (Placement Driver)    元数据 + 调度
  TiKV                     分布式 KV (基于 RocksDB + Raft)
  TiDB                     SQL 层 (无状态)
  TiFlash                  列存副本 (HTAP)
  TiCDC                    增量同步
  TiSpark                  Spark 接 TiKV

特性:
  - MySQL 8.0 协议兼容
  - HTAP (OLTP TiKV + OLAP TiFlash)
  - 水平扩展 (PB 级)
  - 强一致 (Raft Multi-Region)
  - 在线 DDL
  - Operator 原生 K8s
```

```bash
tiup cluster deploy prod-tidb v8.0.0 topology.yaml --user tidb
tiup cluster start prod-tidb
tiup cluster display prod-tidb

# K8s
helm install tidb-operator pingcap/tidb-operator -n tidb
kubectl apply -f tidb-cluster.yaml
```

### 1.2 OceanBase（蚂蚁金服）

```
特性:
  - 分布式 (类 Spanner)
  - MySQL/Oracle 双模兼容
  - 金融级强一致 (Paxos)
  - 分布式事务 + 2PC
  - HTAP
  - 行存 + 列存
  - 主用于金融 / 国央企

场景:
  - 双 11 大促 (蚂蚁)
  - 各大银行核心
  - 政府关基
```

### 1.3 GaussDB / PolarDB / TDSQL

```
GaussDB           华为, 分布式, 多形态 (centralized + distributed)
GaussDB(for openGauss)  开源
PolarDB           阿里, 存算分离, MySQL/PG/Oracle 兼容
PolarDB-X         分布式 (DRDS 演进)
TDSQL             腾讯, MySQL/PG 兼容分布式
CynosDB           腾讯, 存算分离
```

### 1.4 CockroachDB / YugabyteDB（国际）

```
CockroachDB       PostgreSQL 兼容, 全球级
Yugabyte          PG + Cassandra 兼容
PingCAP TiDB ⭐    国产 HTAP 王者
```

## 二、数据库内核基础

### 2.1 MVCC

```
原理:
  - 读不阻塞写 / 写不阻塞读
  - 通过版本号 / 事务 ID 维护多版本
  - 老版本由 VACUUM (PG) / Purge (InnoDB) 清理

MySQL InnoDB:
  - read view + undo log
  - 隔离级别: RR (默认), RC

PG:
  - tuple visibility + xmin/xmax
  - vacuum 必修
```

### 2.2 2PC / Saga / TCC

```
2PC (两阶段提交):
  Coordinator → Prepare → Commit/Rollback
  XA 标准 (MySQL XA / PG)
  
3PC: 加 CanCommit 阶段, 减阻塞

Saga:
  长事务拆 + 补偿
  RocketMQ Saga / Seata Saga ⭐
  
TCC (Try-Confirm-Cancel):
  业务侵入
  Seata TCC ⭐
```

### 2.3 Raft / Paxos

```
Raft (TiKV/etcd/Consul) ⭐
  Leader-based, 易理解
  日志复制 + 选主

Paxos (OceanBase/Chubby)
  Multi-Paxos, 性能更高, 工程难

ZAB (ZooKeeper)
  类 Paxos
```

### 2.4 共识与一致性模型

```
线性一致 (Linearizable)     最强, 直觉一致 (etcd/CockroachDB/TiKV)
顺序一致 (Sequential)       全局顺序但允许时延
因果一致 (Causal)           因果关系保序
最终一致 (Eventual)         最弱, Cassandra/Dynamo
读写一致 / 单调读 / 单调写
```

## 三、海量数据治理

### 3.1 分库分表设计

```
水平分库:    user_id % 4 → db_0..3
水平分表:    id % 16 → t_0..15
垂直分库:    业务边界 (订单库/用户库/支付库)
垂直分表:    冷热字段分离

挑战:
  - 跨库 JOIN → 禁止 / 应用层聚合
  - 分布式事务 → Saga / TCC
  - 全局唯一 ID → Snowflake / Leaf (美团) / UidGenerator
  - 全局二级索引 → ES 同步
  - 大跨页查询 → 游标 / search_after
  - 数据迁移 → 双写 + DTS
```

### 3.2 ShardingSphere 进阶

```yaml
# 强制路由 / 影子库 / 读写分离 / 加密 / 治理
rules:
  - !READWRITE_SPLITTING
    dataSources:
      ds_rw:
        writeDataSourceName: ds_master
        readDataSourceNames: [ds_slave_0, ds_slave_1]
        loadBalancerName: round_robin
  - !ENCRYPT
    tables:
      users:
        columns:
          phone:
            cipherColumn: phone_cipher
            encryptorName: aes_encryptor
    encryptors:
      aes_encryptor: { type: AES, props: { aes-key-value: "Your32CharKey..." } }
```

### 3.3 冷热数据分层

```
方案:
  - 业务表按时间分区 (PARTITION BY RANGE)
  - 老数据归档到 ClickHouse / S3 + Iceberg
  - TiDB Placement Rules (热盘 / 冷盘)
  - PG 表空间 (hot SSD / cold HDD)
  - MySQL Archive / TokuDB / RocksDB

工具:
  pt-archiver (Percona)
  阿里 DTS / 腾讯 DTS / Debezium ⭐
  TiCDC / MaxScale Replication
```

## 四、Kafka 千万级调优

### 4.1 零拷贝原理

```
普通 IO: 4 次数据拷贝 + 2 次上下文切换
零拷贝 (sendfile): 2 次数据拷贝 + 1 次切换
DMA Gather + sendfile: 1 次拷贝
Page Cache + DMA: 0 次 CPU 拷贝

Kafka 利用:
  - Producer: 直接写 Page Cache
  - Consumer: sendfile 直发网卡
  - 顺序写盘 (HDD 数百 MB/s)
```

### 4.2 极限调优参数

```properties
# Broker
num.network.threads=8
num.io.threads=16
socket.send.buffer.bytes=1048576
socket.receive.buffer.bytes=1048576
socket.request.max.bytes=104857600
queued.max.requests=500
log.flush.interval.messages=Long.MaxValue   # 不强 flush
log.flush.interval.ms=Long.MaxValue
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000

# 副本
replica.fetch.max.bytes=10485760
replica.lag.time.max.ms=10000
num.replica.fetchers=8

# 压缩
compression.type=lz4    # 或 zstd

# Producer
batch.size=131072       # 128KB
linger.ms=10
acks=all
enable.idempotence=true
compression.type=lz4
max.in.flight.requests.per.connection=5
buffer.memory=67108864

# Consumer
fetch.min.bytes=65536
fetch.max.wait.ms=500
max.poll.records=1000
max.partition.fetch.bytes=10485760
```

### 4.3 Kafka 监控深入

```
关键指标:
  - RequestQueueTimeMs (请求排队)
  - LocalTimeMs (本地处理)
  - RemoteTimeMs (副本同步)
  - ResponseQueueTimeMs (响应排队)
  - ResponseSendTimeMs (网络发送)

不同 5 段定位:
  RequestQueue 高 → IO 线程不够
  LocalTime   高 → 磁盘 / 锁
  RemoteTime  高 → 副本网络 / 副本 broker
  ResponseQueue 高 → Network 线程
```

### 4.4 Confluent / Strimzi 企业版

```
Tiered Storage:   冷数据 → S3 (Confluent 商业 / Strimzi 0.40+)
Cluster Linking:  跨集群同步 (Confluent)
Self-Balancing:   自动均衡 (Confluent)
Schema Registry:  Avro / Protobuf / JSON Schema
ksqlDB:           流处理 SQL
Kafka Connect:    源/汇

国产替代:
  RocketMQ 5.0 ⭐: 存算分离 + 副本组 + Controller
  Pulsar ⭐: 存算分离 (BookKeeper) + 多租户
```

## 五、Pulsar 架构

```
组件:
  Broker          无状态, 计算
  BookKeeper      存储 (Bookie)
  ZooKeeper       元数据 (3.0+ 替换为 etcd/Oxia)

特性:
  - 存算分离 ⭐
  - 多租户 (tenant/namespace/topic 三层)
  - 强一致 (Bookie Quorum)
  - 长期存储 (Tiered Storage)
  - Geo-Replication (内建跨地)
  - Functions (轻量流处理)
  - Schema Registry 内置

场景:
  - 大企业多租户消息平台
  - 长留存 (天数级 → 月级)
  - 跨地多活
  - 替代 Kafka + Connect + Schema
```

```yaml
# StreamNative Operator
apiVersion: pulsar.streamnative.io/v1alpha1
kind: PulsarCluster
metadata: { name: prod-pulsar }
spec:
  brokers: { replicas: 3, resources: { ... } }
  bookies: { replicas: 5, resources: { ... } }
  zookeeper: { replicas: 3 }
```

## 六、Redis 万核 + 替代

### 6.1 Pika（360 国产）

```
特性:
  - RocksDB 持久化 (单实例 TB 级)
  - Redis 协议兼容
  - 主从 + Sentinel
  
适合:
  - 数据量大 (内存装不下)
  - 单价低 (机械盘)
  - 性能要求中等
```

### 6.2 Tair（阿里）

```
版本:
  Tair MDB     内存版 (兼容 Redis)
  Tair LDB     持久化 (基于 LevelDB)
  Tair RDB     RDS Redis (云上)
  Tair Cluster 集群

特性:
  - 增强数据结构 (TairString / TairHash / TairZSet)
  - 多线程
  - 半同步副本
  - 阿里云 SaaS
```

### 6.3 DragonflyDB

```
特性:
  - 单进程多线程 (无锁)
  - Redis + Memcached 协议
  - 25x 性能于 Redis (官方)
  - 内存高效
  
适合:
  - 单机超高 QPS
  - 替代单机 Redis
  - 不需要 Cluster (单机已强)
```

### 6.4 KvRocks（CNCF）

```
- RocksDB 引擎
- Redis 协议
- 适合超大数据
- 阿里美团贡献
```

## 七、多模数据库

### 7.1 MongoDB（文档）

```yaml
# K8s Operator
apiVersion: mongodbcommunity.mongodb.com/v1
kind: MongoDBCommunity
metadata: { name: prod-mongo }
spec:
  members: 3
  type: ReplicaSet
  version: "7.0"
```

```javascript
db.users.aggregate([
  { $match: { active: true } },
  { $group: { _id: "$dept", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])

db.users.createIndex({ name: 1, email: 1 }, { unique: true })
```

### 7.2 Cassandra（宽列）

```
适合: 写多读少 / 时序 / 海量
拓扑: 多 DC + 多副本 + Gossip
一致性: 可调 (ONE / QUORUM / ALL)
```

### 7.3 Nebula Graph（国产图）

```
特性:
  - 万亿点关系
  - 类 SQL (nGQL)
  - Storage + Graph + Meta 三层分离
  - K8s Operator ⭐
  
场景:
  - 社交网络
  - 风控反欺诈 ⭐
  - 知识图谱
  - 推荐系统
```

### 7.4 Neo4j / JanusGraph

```
Neo4j:      老牌, Cypher 标准
JanusGraph: 分布式 (HBase/Cassandra 后端)
```

## 八、向量数据库（AI 时代必备）

### 8.1 主流方案

```
pgvector ⭐         PG 扩展 (易用, 中小规模)
Milvus ⭐           CNCF, 大规模 (10亿+)
Qdrant              Rust, 性能强
Weaviate            云原生 + 内置 ML
Chroma              轻量 LangChain 友好
Pinecone            SaaS
LanceDB             嵌入式
Redis VSS           Redis 8 内置
Elasticsearch 8.0+  kNN 内置
OpenSearch          k-NN
ClickHouse          向量索引 (24.x)
TiDB Serverless     TiDB 向量
PostgreSQL + pgvector ⭐ ⭐ 推荐 (与业务库共存)
```

### 8.2 Milvus 部署

```yaml
helm install milvus milvus/milvus -n milvus \
  --set cluster.enabled=true \
  --set service.type=ClusterIP \
  --set externalEtcd.enabled=true \
  --set externalEtcd.endpoints[0]=etcd:2379
```

### 8.3 pgvector 用法

```sql
CREATE EXTENSION vector;
CREATE TABLE items (
  id BIGSERIAL PRIMARY KEY,
  content TEXT,
  embedding VECTOR(1536)
);
CREATE INDEX ON items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 检索
SELECT * FROM items
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

### 8.4 选型矩阵

| 场景 | 推荐 |
|:---|:---|
| **小型 / 业务库共存** | pgvector ⭐ |
| **大型 (10亿+) / 独立** | Milvus ⭐ |
| **AI Native / 内置 ML** | Weaviate |
| **极致性能** | Qdrant |
| **LangChain 原型** | Chroma |
| **企业 SaaS** | Pinecone |
| **嵌入式** | LanceDB |
| **已有 Redis** | Redis VSS |

## 九、时序数据库

### 9.1 TDengine（涛思, 国产 ⭐）

```
特性:
  - 单机 1000w 写/s
  - 列存 + 压缩 (10:1)
  - SQL 兼容
  - 物联网首选

场景:
  - IoT (千万设备)
  - 智能制造
  - 智慧城市
  - 车联网
```

### 9.2 IoTDB（清华, 国产 ⭐）

```
- Apache 顶级
- 物联网时序
- 自研 TsFile 格式
- 与 Flink / Spark 集成
```

### 9.3 InfluxDB / TimescaleDB

```
InfluxDB ⭐:    全球老牌, Flux/InfluxQL
TimescaleDB ⭐: PG 扩展, SQL 兼容, AIOps 友好
VictoriaMetrics ⭐: Prometheus 长存 / 高性能
QuestDB:        高性能 ILP
```

## 十、数据湖（中间件 + 大数据）

```
Iceberg ⭐         Netflix 开源, ACID, 大厂主流
Delta Lake ⭐      Databricks, ACID
Hudi ⭐            Uber, 实时 upsert
Paimon ⭐          Flink 社区 (国产主导), 流批一体 ⭐
```

详见 [10_大数据](../../10_大数据/index.md)。

## 十一、DBaaS / 数据库平台

### 11.1 KubeBlocks 深度

```
核心 CRD:
  ClusterDefinition       数据库定义 (元 schema)
  ComponentDefinition     组件定义
  Cluster                 用户用 ⭐
  Component               单个组件实例
  Backup / Restore        备份恢复
  OpsRequest              运维操作 (扩容/升级)

支持数据库 (30+):
  MySQL (ApeCloud, Percona)
  PostgreSQL (KubeBlocks PG)
  Redis
  Kafka
  MongoDB
  ElasticSearch
  ClickHouse
  Pulsar
  RabbitMQ
  Greenplum
  OceanBase
  TiDB
  Vitess
  Milvus
  Qdrant
  Weaviate
  ...
```

### 11.2 自研 DBaaS 平台架构

```
门户层:    React + Backstage 插件
API:       Go/Java + Operator SDK
调度层:    K8s + KubeBlocks
存储:      Rook-Ceph / Longhorn / 云盘 CSI
备份:      Velero + Restic + S3
监控:      Prometheus + exporter
日志:      Loki / ELK
配置:      Nacos / Consul
SSO:       Keycloak / 企业 OAuth
工单:      Jira / 自研
计费:      OpenCost + 自研
```

## 十二、跨地多活

### 12.1 异地多活方案

```
方案:
  1. 主备 (灾备, RTO 分钟级)
  2. 双活 (读多写少, 业务分摊)
  3. 多活 (单元化, 蚂蚁/淘宝)

数据层:
  - MySQL → 阿里 DTS / Canal / Debezium / MaxScale
  - PG → Bucardo / pglogical / Citus
  - Redis → CRDT / 阿里 RedisShake
  - Kafka → MirrorMaker 2 / Confluent Cluster Linking
  - ES → CCR (Cross-Cluster Replication)
  - CK → Replicated Tables + Distributed
  - MongoDB → Replica Set + 区域感知

接入层:
  - DNS / GSLB / Anycast
  - 业务路由 (用户 ID 范围)

冲突解决:
  - 时间戳 (last-write-wins)
  - CRDT (无冲突)
  - 业务层 reconcile
```

### 12.2 单元化（蚂蚁 LDC）

```
单元 (Unit):
  - 数据按 user_id 分片 → 每分片归一个单元
  - 单元内闭环 (LDC: Logic Data Center)
  - 跨单元访问走异步

特点:
  - 99.99% 流量本单元
  - 1% 异常跨单元 (走专线)
  - 故障切单元 (RTO 秒级)
```

## 十三、国密 + 合规

### 13.1 数据库国密

```
MySQL:
  - 通过 Tongsuo / 国密 OpenSSL fork 替换 OpenSSL
  - SM2 证书 + SM3 哈希 + SM4 数据加密

PG:
  - pgcrypto + 国密扩展
  - 中科软 / 优炫 国密 PG

国产 DB:
  GaussDB / OceanBase / TiDB
  内置 SM2/3/4 (要确认版本)
  
等保三级要求:
  ☐ 透明加密 (列级 / 表级)
  ☐ 国密算法
  ☐ 备份加密
  ☐ Audit log 留存 180 天
  ☐ 操作分权 + 双人审计
```

### 13.2 加密机 / KMS

```
华为 KPS / 阿里 KMS / 腾讯 KMS
海光 CSV (机密计算)
长虹 / 江南 加密机
```

## 十四、典型坑（高级）

| 坑 | 建议 |
|:---|:---|
| **TiDB 热点导致 PD 调度疯狂** | 提前预切 / region merge 调参 |
| **OceanBase 升级失败** | OBProxy 灰度 + 备份 |
| **ShardingSphere 跨库 JOIN** | 禁止 / 应用层 / 数据迁移到 OLAP |
| **Kafka 千万 TPS 但磁盘满** | Tiered Storage / 减保留期 |
| **Pulsar BookKeeper 慢** | 独立 SSD + 多 Bookie |
| **Redis 大 key 阻塞** | 拆 + UNLINK + Big Key 监控 |
| **MongoDB 副本集分裂脑** | 奇数副本 + arbiter 限制 |
| **Cassandra wide row** | 控制 partition key 基数 |
| **Nebula 图查询慢** | indexscan + 算法预热 |
| **pgvector 大数据慢** | hnsw 索引 + 减 lists |
| **Milvus OOM** | 分 collection + 索引参数 |
| **TDengine 单机超大** | 多 vnode + 集群 |
| **跨地同步分裂脑** | quorum + fencing + 业务幂等 |
| **国密性能下降** | 硬件加密机 / 海光 CSV |

## 十五、Checklist（高级）

```
分布式 DB:
☐ TiDB / OceanBase / GaussDB / PolarDB-X 一种入栈
☐ Operator + Backup + 监控
☐ HTAP 场景: TiDB + TiFlash 或 Doris

内核:
☐ MVCC / 2PC / Saga / TCC 理论清晰
☐ Raft / Paxos 实战 1+ 集群
☐ 一致性模型 + CAP

海量数据:
☐ ShardingSphere / Vitess
☐ 冷热分层 + 归档
☐ Snowflake ID / Leaf / UidGenerator
☐ DTS / Canal / Debezium 增量同步

Kafka 调优:
☐ 千万 TPS 调参全栈
☐ Tiered Storage / Cluster Linking
☐ Strimzi Operator + Schema Registry

Pulsar:
☐ 存算分离架构理解
☐ 多租户 + Geo-Replication
☐ Functions / Tiered Storage

Redis:
☐ Pika / Tair / Dragonfly 选型
☐ 万核场景 + 大 key 治理

多模:
☐ MongoDB / Cassandra / Nebula / Neo4j 一种
☐ 场景驱动 (社交/风控/推荐)

向量:
☐ pgvector (业务库) + Milvus (大规模) 双栈
☐ 索引选型 (IVF / HNSW / DiskANN)

时序:
☐ TDengine / IoTDB (国产 IoT)
☐ VictoriaMetrics / TimescaleDB

数据湖:
☐ Iceberg / Paimon / Hudi 一种
☐ 配合 Flink / Spark

DBaaS:
☐ KubeBlocks 一站式 ⭐
☐ 自研门户 + 工单 + 计费
☐ 多租户 + 备份 + 监控

跨地多活:
☐ 主备 / 双活 / 多活 / 单元化 一种
☐ DTS / 双写 / CRDT
☐ 季度切换演练

合规:
☐ 国密 (Tongsuo / SM2/3/4)
☐ 透明加密 + Audit
☐ 等保三级 + 国测中心
☐ 加密机 / KMS / 海光 CSV
```

## 十六、推荐栈（高级）

```
分布式 DB:    TiDB ⭐ / OceanBase ⭐ / GaussDB / PolarDB-X / CockroachDB
分库分表:    ShardingSphere ⭐ / Vitess
DTS:         Canal / Debezium / TiCDC / 阿里 DTS
Kafka 进阶:  Strimzi + Schema Registry + Connect + Tiered Storage
Pulsar:     StreamNative Operator + Functions
Redis 替代:  KeyDB / Dragonfly / Pika / Tair / KvRocks
多模:        MongoDB / Cassandra / Nebula ⭐ (国产图)
向量:        pgvector ⭐ + Milvus ⭐
时序:        TDengine ⭐ / IoTDB ⭐ / VictoriaMetrics / TimescaleDB
数据湖:      Iceberg / Paimon ⭐ (国产) / Hudi
平台:        KubeBlocks ⭐ + 自研 DBaaS + Backstage 插件
跨地:        阿里 DTS / Canal / MirrorMaker 2 / CRDT
国密:        Tongsuo + 国密 PG / GaussDB / OceanBase 内置
```

> 📖 **核心判断**：中间件高级 = **分布式 NewSQL(TiDB/OceanBase) + 内核(MVCC/Raft/2PC) + 海量治理(分库分表/冷热/数据湖) + Kafka 千万 TPS 调优 + Pulsar 存算分离 + Redis 替代生态(Pika/Tair/Dragonfly) + 多模(图/向量/时序) + DBaaS 平台(KubeBlocks 深度) + 跨地多活(单元化/DTS) + 国密合规**。能给 PB 级数据画"TiDB OLTP + TiFlash/StarRocks OLAP + Kafka/Pulsar 实时 + Milvus 向量 + TDengine 时序 + KubeBlocks DBaaS + 双活跨地"全栈、能调通 Kafka 千万 TPS / TiDB 上百亿表 / Redis 万核、能落地国密 + 等保 + 加密机，就具备中间件平台架构师能力。
