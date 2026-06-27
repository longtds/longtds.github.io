# 进阶

> 中间件进阶 = **高可用集群拓扑(MGR/InnoDB Cluster/PG Patroni+repmgr/Redis Sentinel+Cluster/Kafka 多 Broker+KRaft/Nacos 集群/ES 多节点/ClickHouse Replicated+ZooKeeper/Nginx 双主+Keepalived) + 主从复制+故障切换 + 分库分表(ShardingSphere/Vitess/Citus) + 性能调优 + 监控告警 + 备份恢复 + 容器化(StatefulSet/Operator/KubeBlocks)**。本章面向独立运维生产中间件集群的工程师。

## 一、MySQL 高可用集群

### 1.1 主从复制（异步）

```bash
# 主库
SET GLOBAL server_id = 1;
SHOW MASTER STATUS;            # 记 File 和 Position
CREATE USER 'repl'@'%' IDENTIFIED BY 'ReplPass';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';

# 从库
SET GLOBAL server_id = 2;
CHANGE MASTER TO MASTER_HOST='10.0.0.1', MASTER_USER='repl',
  MASTER_PASSWORD='ReplPass', MASTER_LOG_FILE='binlog.000001', MASTER_LOG_POS=154;
START SLAVE;
SHOW SLAVE STATUS\G
```

监控：Slave_IO_Running / Slave_SQL_Running / Seconds_Behind_Master

### 1.2 半同步复制

```sql
INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';
INSTALL PLUGIN rpl_semi_sync_slave  SONAME 'semisync_slave.so';
SET GLOBAL rpl_semi_sync_master_enabled = 1;
SET GLOBAL rpl_semi_sync_master_timeout = 1000;   -- ms
```

### 1.3 MGR (MySQL Group Replication)

```ini
[mysqld]
server_id = 1
gtid_mode = ON
enforce_gtid_consistency = ON
plugin_load_add = 'group_replication.so'
loose-group_replication_group_name = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
loose-group_replication_start_on_boot = OFF
loose-group_replication_local_address = "10.0.0.1:33061"
loose-group_replication_group_seeds = "10.0.0.1:33061,10.0.0.2:33061,10.0.0.3:33061"
loose-group_replication_bootstrap_group = OFF
```

```sql
-- 节点 1 引导
SET GLOBAL group_replication_bootstrap_group=ON;
START GROUP_REPLICATION;
SET GLOBAL group_replication_bootstrap_group=OFF;

-- 节点 2/3 加入
START GROUP_REPLICATION;
SELECT * FROM performance_schema.replication_group_members;
```

### 1.4 InnoDB Cluster

```bash
mysqlsh
> dba.configureInstance('root@10.0.0.1:3306')
> var cluster = dba.createCluster('prodCluster')
> cluster.addInstance('root@10.0.0.2:3306')
> cluster.addInstance('root@10.0.0.3:3306')
> cluster.status()

# MySQL Router 接入层
mysqlrouter --bootstrap root@10.0.0.1:3306 --user=mysqlrouter
```

### 1.5 国产高可用方案

```
PXC (Percona XtraDB Cluster)    多主同步, 不推荐 (锁冲突)
Galera Cluster                  同 PXC
MGR ⭐                          官方主流
InnoDB Cluster ⭐               官方 + Router
OceanBase                       分布式 (蚂蚁)
TiDB                            HTAP 分布式 ⭐
GaussDB                         华为
TencentDB CynosDB              腾讯
PolarDB                         阿里
```

### 1.6 调优要点

```ini
innodb_buffer_pool_size = 物理内存 50-70%
innodb_buffer_pool_instances = 8
innodb_log_file_size = 1-2G
innodb_log_buffer_size = 16M
innodb_flush_log_at_trx_commit = 1   # 强一致
sync_binlog = 1
innodb_io_capacity = 2000-20000      # 看磁盘
innodb_io_capacity_max = 4000-40000
innodb_flush_method = O_DIRECT
innodb_thread_concurrency = 0
innodb_read_io_threads = 8
innodb_write_io_threads = 8
max_connections = 1000-5000
thread_cache_size = 100
table_open_cache = 4096
```

## 二、PostgreSQL 高可用

### 2.1 流复制 + Patroni

```yaml
# /etc/patroni/patroni.yml
scope: prod-pg
namespace: /service/
name: pg-node-1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.0.1:8008

etcd3:
  hosts: 10.0.0.10:2379,10.0.0.11:2379,10.0.0.12:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    synchronous_mode: true
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 1000
        shared_buffers: 4GB
        effective_cache_size: 12GB
        max_wal_senders: 10
        max_replication_slots: 10
        wal_level: replica
        hot_standby: "on"

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.0.1:5432
  data_dir: /var/lib/postgresql/data
  pgpass: /var/lib/postgresql/.pgpass
  authentication:
    replication: { username: replicator, password: ReplPass }
    superuser:   { username: postgres,   password: PostgresPass }
```

```bash
systemctl enable --now patroni
patronictl -c /etc/patroni/patroni.yml list
patronictl failover
patronictl switchover
```

### 2.2 接入层

```
HAProxy → patroni REST /master 端口  (写)
HAProxy → patroni REST /replica 端口 (读)

或 pgbouncer 连接池 + Patroni 检测
```

### 2.3 Citus 分布式 PG（OLAP/水平扩展）

```sql
CREATE EXTENSION citus;
SELECT citus_add_node('worker1', 5432);
SELECT citus_add_node('worker2', 5432);
SELECT create_distributed_table('orders', 'user_id');
```

## 三、Redis 高可用与集群

### 3.1 Sentinel（哨兵）

```ini
# sentinel.conf
port 26379
sentinel monitor mymaster 10.0.0.1 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 60000
sentinel parallel-syncs mymaster 1
sentinel auth-pass mymaster redis123
```

3 Sentinel + 1 主 + 2 从 = 标准最小拓扑。

### 3.2 Redis Cluster（分片 + HA）

```bash
# 6 节点 (3 主 3 从)
redis-cli --cluster create \
  10.0.0.1:6379 10.0.0.2:6379 10.0.0.3:6379 \
  10.0.0.4:6379 10.0.0.5:6379 10.0.0.6:6379 \
  --cluster-replicas 1

redis-cli -c -h 10.0.0.1 -p 6379
> CLUSTER NODES
> CLUSTER INFO
> CLUSTER SLOTS
```

### 3.3 Codis / 阿里 Tair / DragonflyDB

```
Codis                豌豆荚 / 阿里 (老)
Tair ⭐              阿里 (持久化 KV / 性能强)
KeyDB                多线程 Redis fork
DragonflyDB ⭐       新一代 (单进程多线程, 25x 性能)
KvRocks              Kvrocks (RocksDB 持久化)
```

### 3.4 调优

```ini
maxmemory 8gb
maxmemory-policy allkeys-lru

# 持久化
appendonly yes
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# 网络
tcp-backlog 1024
tcp-keepalive 60
timeout 300

# 安全
requirepass YourStrong@Pass
rename-command FLUSHALL ""
rename-command CONFIG ""

# Cluster
cluster-enabled yes
cluster-node-timeout 15000
cluster-require-full-coverage no
```

## 四、Kafka 集群

### 4.1 KRaft 模式集群

```properties
# server.properties (node 1)
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@10.0.0.1:9093,2@10.0.0.2:9093,3@10.0.0.3:9093
listeners=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
advertised.listeners=PLAINTEXT://10.0.0.1:9092
log.dirs=/data/kafka-logs
num.partitions=6
default.replication.factor=3
min.insync.replicas=2
log.retention.hours=168
```

### 4.2 关键参数

```
副本因子:           3 (生产必要)
min.insync.replicas: 2
acks:               all (生产者)
unclean.leader.election: false
分区数:             业务 QPS / 单分区吞吐 (1w/s/分区)
压缩:               lz4 / zstd
日志保留:           7 天
日志大小:           按盘容量
```

### 4.3 监控关键指标

```
Broker:
  - UnderReplicatedPartitions (应为 0)
  - ActiveControllerCount (集群只能 1)
  - OfflinePartitionsCount (应为 0)
  - RequestHandlerAvgIdlePercent (越高越好)
  - NetworkProcessorAvgIdlePercent
  - BytesInPerSec / BytesOutPerSec
  - MessagesInPerSec

Consumer:
  - Lag (消费滞后, 关键)
  - ConsumerRebalance
```

### 4.4 Kafka Connect / MirrorMaker / Schema Registry

```
Kafka Connect:    源/汇 (MySQL → Kafka → ES)
MirrorMaker 2:    跨集群复制
Schema Registry:  Avro/Protobuf Schema 管理
ksqlDB:           流处理 SQL
Kafka Streams:    Java 流处理 lib
```

## 五、RocketMQ 集群

```
NameServer: 3 节点 (无状态)
Broker:     M-S 主从 (Sync/Async) + Raft (DLedger 5.0+)
Topic:      多 BrokerName 分散
Tag:        消息标签
Group:      消费组

部署模式:
  双主双从 异步      性能高 / 数据可能丢
  双主双从 同步 ⭐    强一致 / 性能略低
  多副本 Raft (DLedger 5.0+) ⭐  Raft 选主 + 强一致
```

```bash
mqadmin clusterList -n nameserver:9876
mqadmin topicList -n nameserver:9876
mqadmin consumerProgress -n nameserver:9876 -g consumer_group
```

## 六、Nacos 集群

### 6.1 部署

```properties
# application.properties
spring.datasource.platform=mysql
db.num=1
db.url.0=jdbc:mysql://10.0.0.10:3306/nacos?characterEncoding=utf8
db.user.0=nacos
db.password.0=NacosPass
nacos.naming.distro.replication.timeout=30000
nacos.core.auth.enabled=true
nacos.core.auth.plugin.nacos.token.secret.key=BASE64_SECRET
```

```bash
# cluster.conf (3 节点)
10.0.0.1:8848
10.0.0.2:8848
10.0.0.3:8848

bash startup.sh -m cluster
```

### 6.2 接入

```
负载: Nginx / HAProxy / VIP
DB:   MySQL 主从 (推荐 MGR)
模式: AP (默认) / CP (Raft)
监控: Spring Boot Actuator + Prometheus
```

## 七、Elasticsearch 集群

### 7.1 节点角色

```
master         决策
data           存储+查询
ingest         写入预处理
coordinating   协调查询
ml             ML 任务
transform      Transform 任务
```

### 7.2 集群拓扑

```yaml
# elasticsearch.yml
cluster.name: prod-es
node.name: es-data-1
node.roles: [data, ingest]
network.host: 0.0.0.0
discovery.seed_hosts: ["es-master-1:9300","es-master-2:9300","es-master-3:9300"]
cluster.initial_master_nodes: ["es-master-1","es-master-2","es-master-3"]

xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
```

### 7.3 关键参数

```
indices.memory.index_buffer_size: 20%
indices.queries.cache.size: 10%
thread_pool.write.queue_size: 1000
indices.fielddata.cache.size: 30%

JVM:
  -Xms16g -Xmx16g    (不超过 32g, 物理内存 50%)
  
分片:
  单分片 30-50GB 最佳
  主分片 = 节点数 × 1-3
  副本 1 (HA) 或 2 (读多)
```

### 7.4 ILM (Index Lifecycle Management)

```json
PUT _ilm/policy/logs-policy
{
  "policy": {
    "phases": {
      "hot":  { "min_age": "0ms", "actions": { "rollover": { "max_size": "50gb", "max_age": "1d" } } },
      "warm": { "min_age": "7d",  "actions": { "shrink": { "number_of_shards": 1 }, "forcemerge": { "max_num_segments": 1 } } },
      "cold": { "min_age": "30d", "actions": { "allocate": { "include": { "data": "cold" } } } },
      "delete": { "min_age": "90d", "actions": { "delete": {} } }
    }
  }
}
```

### 7.5 OpenSearch（AWS fork）

```
OpenSearch ⭐ (Apache 2.0)
原生支持: 多租户 / SQL / Anomaly Detection / k-NN
国内政企友好 (无 ES license 风险)
```

## 八、ClickHouse 集群

### 8.1 Replicated + ZooKeeper

```xml
<!-- config.xml -->
<zookeeper>
    <node><host>zk-1</host><port>2181</port></node>
    <node><host>zk-2</host><port>2181</port></node>
    <node><host>zk-3</host><port>2181</port></node>
</zookeeper>

<remote_servers>
    <prod>
        <shard>
            <internal_replication>true</internal_replication>
            <replica><host>ck-1</host><port>9000</port></replica>
            <replica><host>ck-2</host><port>9000</port></replica>
        </shard>
        <shard>
            <internal_replication>true</internal_replication>
            <replica><host>ck-3</host><port>9000</port></replica>
            <replica><host>ck-4</host><port>9000</port></replica>
        </shard>
    </prod>
</remote_servers>

<macros>
    <shard>01</shard>
    <replica>ck-1</replica>
</macros>
```

### 8.2 表引擎

```sql
-- 单节点
CREATE TABLE local.events (...) ENGINE = MergeTree ORDER BY (ts);

-- Replicated (强同步)
CREATE TABLE local.events_replicated (...) ENGINE = ReplicatedMergeTree(
  '/clickhouse/tables/{shard}/events', '{replica}'
) ORDER BY (ts);

-- Distributed (分布式表)
CREATE TABLE prod.events ON CLUSTER prod (...)
ENGINE = Distributed(prod, local, events_replicated, cityHash64(user));
```

### 8.3 ClickHouse Keeper（替代 ZK）

```
22.7+ 起 ClickHouse Keeper (基于 Raft + 兼容 ZK 协议)
推荐替代 ZK (一致性 / 维护更好)
```

### 8.4 替代方案

```
ClickHouse ⭐     单表大宽 / SQL / 高并发
StarRocks ⭐      MPP + 实时 / 国产 (DorisDB fork)
Apache Doris ⭐   国产 / MPP / 实时 / 多模 (类 OLAP+OLTP)
TiDB / TiFlash    HTAP
Druid             实时 OLAP (老, 维护)
```

## 九、Nginx 高可用

### 9.1 Keepalived + VIP

```conf
# /etc/keepalived/keepalived.conf (主)
vrrp_script chk_nginx { script "killall -0 nginx"; interval 2; weight -20 }

vrrp_instance VI_1 {
  state MASTER
  interface eth0
  virtual_router_id 51
  priority 100
  advert_int 1
  authentication { auth_type PASS auth_pass YourPass }
  virtual_ipaddress { 10.0.0.100/24 }
  track_script { chk_nginx }
}
```

备节点：priority 90 + state BACKUP。

### 9.2 LVS + Keepalived

```
LVS DR / TUN 模式:
  L4 负载, 性能 1000w pps
  适合超高并发
  
Nginx Plus / Tengine / OpenResty ⭐
  L7 增强
```

### 9.3 OpenResty / APISIX / Higress

```
OpenResty ⭐:    Nginx + LuaJIT，灵活但要自写
APISIX ⭐:       OpenResty 内核 + etcd + 控制面，国产 ⭐
Higress ⭐:      Envoy 内核 + Istio 控制面，国产阿里 ⭐
Kong:            老牌
Envoy:           CNCF L7
HAProxy:         L4/L7 经典
```

## 十、分库分表 / 分布式 SQL

### 10.1 ShardingSphere

```yaml
# ShardingSphere-JDBC (Java)
dataSources:
  ds_0: { url: jdbc:mysql://10.0.0.1:3306/db_0, username: app, password: *** }
  ds_1: { url: jdbc:mysql://10.0.0.2:3306/db_1, username: app, password: *** }
rules:
  - !SHARDING
    tables:
      orders:
        actualDataNodes: ds_${0..1}.orders_${0..3}
        databaseStrategy: { standard: { shardingColumn: user_id, shardingAlgorithmName: db_mod } }
        tableStrategy:    { standard: { shardingColumn: id,      shardingAlgorithmName: t_mod } }
    shardingAlgorithms:
      db_mod: { type: MOD, props: { sharding-count: 2 } }
      t_mod:  { type: MOD, props: { sharding-count: 4 } }
```

ShardingSphere-Proxy（中间件模式）：MySQL 协议代理，对应用透明。

### 10.2 Vitess（YouTube）

```
MySQL 兼容 + 分片 + 拓扑感知 + Operator (CNCF)
PlanetScale 商业版 (基于 Vitess)
```

### 10.3 TiDB / OceanBase / GaussDB / PolarDB

```
TiDB ⭐         国产, HTAP, 兼容 MySQL, K8s 原生 (TiDB Operator)
OceanBase ⭐    国产 (蚂蚁), 分布式金融级, 兼容 MySQL/Oracle
GaussDB         国产 (华为), 分布式
PolarDB         阿里, 存算分离
TDSQL           腾讯
```

## 十一、容器化中间件（KubeBlocks / Operator）

### 11.1 主流 Operator

```
MySQL:     Vitess Operator / Bitnami / KubeBlocks ⭐
PG:        CloudNativePG ⭐ / Crunchy / Zalando / KubeBlocks
Redis:     Redis Operator (OT) / KubeBlocks
Kafka:     Strimzi ⭐ / Confluent / KubeBlocks
ES:        ECK ⭐ / KubeBlocks
ClickHouse: Altinity ⭐ / KubeBlocks
Nginx:     ingress-nginx
RabbitMQ:  RabbitMQ Cluster Operator
Pulsar:    Pulsar Operator (StreamNative)
MinIO:     MinIO Operator ⭐

国产神器 KubeBlocks ⭐:
  统一 API CRD (Cluster / Component)
  支持 30+ 数据库 (MySQL, PG, Redis, Mongo, Kafka, ES, MQ, Pulsar, OceanBase, TiDB...)
  Cloud Native 数据库平台
  替代每种 DB 单独 Operator
```

### 11.2 KubeBlocks 示例

```yaml
apiVersion: apps.kubeblocks.io/v1alpha1
kind: Cluster
metadata: { name: prod-mysql, namespace: db }
spec:
  clusterDefinitionRef: apecloud-mysql
  clusterVersionRef: ac-mysql-8.0.30
  terminationPolicy: DoNotTerminate
  componentSpecs:
    - name: mysql
      componentDefRef: mysql
      replicas: 3
      resources:
        requests: { cpu: 2, memory: 4Gi }
        limits:   { cpu: 4, memory: 8Gi }
      volumeClaimTemplates:
        - name: data
          spec:
            accessModes: [ReadWriteOnce]
            resources: { requests: { storage: 100Gi } }
            storageClassName: rook-ceph-block
```

## 十二、监控告警基线

```
Prometheus Exporter:
  mysqld_exporter ⭐
  postgres_exporter ⭐
  redis_exporter ⭐
  kafka_exporter / kafka-lag-exporter ⭐
  elasticsearch_exporter ⭐
  clickhouse exporter ⭐
  nginx-prometheus-exporter

必备告警:
☐ MySQL 主从延迟 > 10s
☐ MySQL 连接数 > 80%
☐ MySQL 慢查询激增
☐ MySQL InnoDB Buffer Hit < 95%
☐ MySQL Repl_Stop
☐ PG WAL lag
☐ PG Connection limit
☐ Redis maxmemory > 80%
☐ Redis keyspace_miss 激增
☐ Kafka Consumer Lag > 阈值
☐ Kafka UnderReplicatedPartitions > 0
☐ Kafka OfflinePartitions > 0
☐ ES Cluster Status Yellow/Red
☐ ES JVM Old Gen > 75%
☐ ES Index 数 > 阈值
☐ CK Replica Queue > 1k
☐ Nginx 5xx 比例

仪表盘:
  Grafana Dashboard ID:
    7362 (MySQL Overview)
    9628 (PostgreSQL)
    763  (Redis)
    7589 (Kafka)
    266  (ES)
    14192 (ClickHouse)
    12708 (Nginx)
```

## 十三、备份与恢复

### 13.1 MySQL

```bash
# 逻辑备份
mysqldump -uroot -p --single-transaction --routines --triggers --master-data=2 --all-databases > all.sql

# 物理备份 (Percona XtraBackup)
xtrabackup --backup --target-dir=/backup/full --user=root --password=***
xtrabackup --prepare --target-dir=/backup/full
xtrabackup --copy-back --target-dir=/backup/full

# Binlog 增量
mysqlbinlog --start-datetime="2026-06-27 00:00:00" /var/lib/mysql/binlog.000001 > incr.sql
```

### 13.2 PostgreSQL

```bash
# 逻辑
pg_dumpall -U postgres > all.sql
pg_dump -U postgres -Fc app > app.dump
pg_restore -U postgres -d app app.dump

# 物理 + WAL (PITR)
pg_basebackup -h 10.0.0.1 -U replicator -D /backup/base -Fp -Xs -P -R
```

工具：**pgBackRest** / **Barman** / **WAL-G** (S3 备份)。

### 13.3 Redis

```
RDB:    BGSAVE / 自动 save 规则
AOF:    持续 + BGREWRITEAOF
跨地:   redis-shake / 阿里 RedisShake
```

### 13.4 Kafka

```
存量:   Kafka Mirror Maker 2 / Cluster Linking
事件:   定期 dump 关键 Topic 到 S3 (Confluent Tiered Storage / Strimzi Tiered)
配置:   ACL / Topic 配置 Git 化
```

### 13.5 ES

```bash
PUT _snapshot/s3-backup
{ "type": "s3", "settings": { "bucket": "es-backup", "region": "cn-northwest-1" } }

PUT _snapshot/s3-backup/snapshot_1?wait_for_completion=true
{ "indices": "*", "include_global_state": true }

POST _snapshot/s3-backup/snapshot_1/_restore
```

## 十四、典型坑（进阶）

| 坑 | 建议 |
|:---|:---|
| **MySQL 主从延迟突增** | 大事务 / 长查 / 网络 / 单线程复制 (并行复制) |
| **Redis 大 key (50MB+)** | 拆分 / 删除时用 UNLINK 异步 |
| **Redis Cluster 不均衡** | reshard / 一致性 hash |
| **Kafka Consumer Lag 突增** | 增分区 / 增 consumer / 升 CPU |
| **Kafka unclean leader** | min.insync.replicas + unclean=false |
| **ES 分片过多 1w+** | ILM rollover / shrink / merge |
| **ES Yellow/Red** | 副本 / 节点 / 磁盘 / fielddata |
| **CK Mutation 卡住** | KILL MUTATION / 优化 ALTER 频率 |
| **Nginx upstream 雪崩** | 主动健康检查 + 熔断 + retry |
| **PG VACUUM 滞后** | autovacuum + 大表手动 + bloat 监控 |
| **Nacos DB 单点** | 必须 MGR / Galera MySQL |
| **etcd 慢 (Patroni)** | 独立 SSD + 三副本 + 不共享 |
| **K8s Operator 升级** | 灰度 + 备份 + 看 changelog |
| **跨 region 同步** | DTS / canal / Debezium / MirrorMaker |
| **慢查询日志没接 SIEM** | 自动归集 + ML 检测 |

## 十五、Checklist（进阶）

```
MySQL:
☐ MGR / InnoDB Cluster + Router
☐ 半同步 + GTID + 并行复制
☐ XtraBackup 全 + binlog 增量 + 异地
☐ exporter + Slow Log
☐ ProxySQL / Atlas / MaxScale 读写分离

PG:
☐ Patroni + etcd + HAProxy
☐ pgBackRest / WAL-G S3 备份
☐ pg_stat_statements + auto_explain
☐ Citus 分片 (可选)

Redis:
☐ Sentinel (中小) 或 Cluster (大)
☐ AOF + RDB
☐ exporter + 大 key 监控
☐ KeyDB / Dragonfly 替代评估

Kafka:
☐ KRaft 3+ broker / 副本 3 / min.isr 2
☐ Schema Registry + Connect
☐ MirrorMaker 2 / Cluster Linking
☐ kafka-lag-exporter

Nacos:
☐ MySQL MGR + 3 节点 Nacos
☐ 鉴权 + 命名空间隔离
☐ Spring Boot Actuator

ES:
☐ master(3) + data + ingest 分角色
☐ ILM hot/warm/cold/delete
☐ S3 Snapshot
☐ ECK Operator

CK:
☐ Replicated + Keeper 替代 ZK
☐ Distributed 表 + 多 shard
☐ Altinity Operator / KubeBlocks
☐ TTL + 分区

Nginx:
☐ Keepalived + VIP
☐ APISIX / Higress 升级路径
☐ 上游主动健康检查
☐ 日志接 ELK / Loki

容器化:
☐ KubeBlocks 一站式 ⭐
☐ Strimzi Kafka / CloudNativePG / ECK
☐ Velero 备份 PVC
☐ StorageClass 选型 (Rook-Ceph + Longhorn)

监控:
☐ kube-prometheus-stack
☐ exporter 全覆盖
☐ 大盘 + 必备告警
☐ 慢日志接 Loki / ELK

备份:
☐ 物理 + 逻辑 + Binlog/WAL
☐ 异地 (S3 / 对象存储)
☐ 季度演练
```

## 十六、推荐栈（进阶）

```
MySQL:    MySQL 8.0 + MGR / InnoDB Cluster + Router + XtraBackup + Vitess (分片)
PG:       PG 16 + Patroni + etcd + pgBackRest + Citus
Redis:    Redis 7 Cluster + KeyDB/Dragonfly 评估
Kafka:    Kafka 3.7 KRaft + Strimzi + Schema Registry + Connect
Nacos:    Nacos 2.3 + MGR
ES:       ES 8.13 / OpenSearch 2.x + ECK + Snapshot to S3
CK:       ClickHouse 24.x + Keeper + Altinity Operator
Nginx:    Nginx 1.27 + Keepalived + 升级 APISIX/Higress
分布式 DB: TiDB ⭐ / OceanBase ⭐ / PolarDB / GaussDB
容器化:   KubeBlocks ⭐ (一站式)
监控:     Prometheus + Grafana + 各 exporter + Loki/ELK
```

> 📖 **核心判断**：中间件进阶 = **主从+集群高可用(MGR/Patroni/Cluster/Strimzi/Replicated/Keepalived) + 性能调优 + 备份+异地+演练 + 监控告警 + 容器化(KubeBlocks/各 Operator) + 分库分表(ShardingSphere/Vitess) + 国产分布式 DB(TiDB/OceanBase) 替代评估**。能搭出"MGR MySQL + Patroni PG + Redis Cluster + Kafka KRaft + ES + ClickHouse Replicated + Nacos 集群 + Nginx Keepalived"全栈 + 接 KubeBlocks 容器化 + Prometheus 监控 + 跨地备份，就具备中间件运维工程师能力。
