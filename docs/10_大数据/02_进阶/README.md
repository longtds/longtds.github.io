# 进阶

> 大数据进阶 = **Spark on K8s 生产化(Spark Operator/Volcano/Stargz) + Flink Kubernetes Operator + 数据湖深度(Iceberg/Paimon/Hudi 三选一) + 实时数仓(Doris/StarRocks/ClickHouse 选型 + 实时维表 + 物化视图) + Kafka Connect / Flink CDC 增量 + DolphinScheduler 多租户 + Spark/Flink 调优 + Trino/Presto 即席查询 + 数据血缘(DataHub/Atlas) + 数据质量(Great Expectations/Soda) + 监控告警 + 平台化(Backstage 数据 IDP) + 国产化路径**。本章面向独立维护中型数据平台的工程师。

## 一、Spark on K8s 生产化

### 1.1 Spark Operator（kubeflow / Apache）

```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata: { name: etl-orders-daily, namespace: spark }
spec:
  type: Python
  mode: cluster
  image: harbor.example.com/spark/spark:3.5-py
  imagePullPolicy: Always
  mainApplicationFile: local:///opt/spark/work-dir/etl.py
  sparkVersion: 3.5.0
  restartPolicy: { type: OnFailure, onFailureRetries: 3 }
  driver:
    cores: 1
    memory: 2g
    serviceAccount: spark-driver
    labels: { app: etl, team: data }
  executor:
    cores: 2
    instances: 6
    memory: 4g
    labels: { app: etl, team: data }
  deps:
    jars:
      - https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.5.0/iceberg-spark-runtime-3.5_2.12-1.5.0.jar
  sparkConf:
    spark.kubernetes.allocation.batch.size: "10"
    spark.sql.adaptive.enabled: "true"
    spark.sql.adaptive.coalescePartitions.enabled: "true"
    spark.sql.adaptive.skewJoin.enabled: "true"
    spark.dynamicAllocation.enabled: "true"
    spark.dynamicAllocation.shuffleTracking.enabled: "true"
    spark.sql.shuffle.partitions: "200"
    spark.kubernetes.driver.podTemplateFile: /opt/spark/templates/driver.yaml
    spark.kubernetes.executor.podTemplateFile: /opt/spark/templates/executor.yaml
    spark.eventLog.enabled: "true"
    spark.eventLog.dir: s3a://logs/spark-events/
```

### 1.2 Volcano / Yunikorn 批调度

```
Volcano ⭐:
  - 队列 / 抢占 / 公平
  - 适配 Spark / Flink / TensorFlow / Argo
  - CNCF 国产 (华为)
  
Yunikorn:
  - 类似 YARN 队列
  - Apache 项目
  
对 K8s 默认调度优势:
  - Gang scheduling (整体调度)
  - 多租户 + Quota
  - 抢占
```

### 1.3 Shuffle 优化

```
RSS (Remote Shuffle Service):
  Apache Celeborn ⭐ (国产)
  Magnet (LinkedIn)
  Uniffle
  
优势:
  - 解耦计算与 shuffle 数据
  - 推到对象存储 / Celeborn worker
  - 抗 K8s pod 抢占
  - 大 shuffle 性能 5-10x
```

### 1.4 镜像 + 启动加速

```
镜像:
  - 自建 Spark Image (官方 + 业务 deps)
  - Stargz 懒加载 (减启动延迟)
  - Harbor + p2p (Dragonfly/Spegel)
  
启动:
  - executorEnv: SPARK_LOCAL_DIRS 用 emptyDir
  - 减少 deps 拉取 (镜像内打入 jars)
```

## 二、Flink Kubernetes Operator 进阶

### 2.1 Session vs Application

```
Session 模式:
  多 Job 共享 JM + TM
  适合: 小 Job 多 / 测试

Application 模式:
  每 Job 独立 JM + TM
  适合: 大 Job / 生产 ⭐
```

### 2.2 高级特性

```yaml
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata: { name: orders-stream, namespace: flink }
spec:
  image: harbor.example.com/flink:1.19
  flinkVersion: v1_19
  flinkConfiguration:
    taskmanager.numberOfTaskSlots: "4"
    state.backend: rocksdb
    state.backend.rocksdb.localdir: /tmp/rocksdb
    state.checkpoints.dir: s3://flink/checkpoints
    state.savepoints.dir: s3://flink/savepoints
    execution.checkpointing.interval: "60000"
    execution.checkpointing.timeout: "10min"
    execution.checkpointing.min-pause: "30000"
    execution.checkpointing.mode: EXACTLY_ONCE
    high-availability: org.apache.flink.kubernetes.highavailability.KubernetesHaServicesFactory
    high-availability.storageDir: s3://flink/ha
    restart-strategy: failure-rate
    restart-strategy.failure-rate.max-failures-per-interval: "10"
    restart-strategy.failure-rate.failure-rate-interval: "10 min"
    restart-strategy.failure-rate.delay: "30 s"
  serviceAccount: flink
  jobManager:
    replicas: 2
    resource: { memory: "4096m", cpu: 2 }
  taskManager:
    replicas: 4
    resource: { memory: "8192m", cpu: 4 }
  podTemplate: { spec: { tolerations: [{ key: dedicated, operator: Equal, value: flink, effect: NoSchedule }] } }
  job:
    jarURI: local:///opt/flink/usrlib/orders.jar
    parallelism: 16
    upgradeMode: savepoint
    state: running
    savepointTriggerNonce: 0
```

### 2.3 自动升级 + Savepoint

```
upgradeMode:
  stateless        无状态 (不保 state)
  last-state       最后状态 (内存 checkpoint)
  savepoint ⭐     生产推荐 (强保证)
  
流程:
  1. 触发 savepoint (trigger nonce++)
  2. 优雅停 (drain + flush)
  3. 升级 jarURI / image
  4. 从 savepoint 启动
```

### 2.4 Flink SQL Gateway

```
SQL Gateway (REST/HTTP):
  统一入口
  Beam / Notebook 接入
  Web UI
```

## 三、数据湖深度

### 3.1 Iceberg

```
特性:
  - ACID 事务 (snapshot isolation)
  - Schema evolution (加列 / 删列 / 类型变)
  - Partition evolution (改分区不重写)
  - Time travel (查询历史 snapshot)
  - Hidden Partitioning (列计算分区)
  - 多引擎兼容 (Spark / Flink / Trino / StarRocks / Doris)

引擎集成:
  Spark 3.x ⭐
  Flink 1.16+ ⭐
  Trino / Presto ⭐
  Snowflake / BigQuery / AWS Athena
```

### 3.2 Iceberg 实战

```sql
-- Spark SQL
CREATE TABLE iceberg.ods.orders (
  id BIGINT, user_id BIGINT, amount DECIMAL(10,2), ts TIMESTAMP
)
USING iceberg
PARTITIONED BY (days(ts))
TBLPROPERTIES (
  'format-version' = '2',
  'write.format.default' = 'parquet',
  'write.target-file-size-bytes' = '536870912'   -- 512MB
);

-- 写入
INSERT INTO iceberg.ods.orders VALUES (1, 100, 99.5, current_timestamp());

-- 查询历史
SELECT * FROM iceberg.ods.orders TIMESTAMP AS OF '2026-06-25 00:00:00';
SELECT * FROM iceberg.ods.orders VERSION AS OF 12345;

-- 维护
CALL iceberg.system.expire_snapshots('ods.orders', TIMESTAMP '2026-06-20 00:00:00');
CALL iceberg.system.remove_orphan_files('ods.orders');
CALL iceberg.system.rewrite_data_files('ods.orders');
CALL iceberg.system.rewrite_manifests('ods.orders');
```

### 3.3 Paimon（国产 Apache ⭐）

```
特性:
  - Flink 社区主导 (国产)
  - 流批一体 (主键表 + Append-only 表)
  - LSM-Tree 引擎 (CDC 高效)
  - 兼容 Iceberg / Hudi 部分语义
  - Spark / Trino / StarRocks / Doris 集成

适合:
  - 流式数据湖 (CDC 入湖)
  - 实时数仓底座
  - 与 Flink 一体
```

```sql
-- Flink SQL
CREATE CATALOG paimon WITH ('type'='paimon', 'warehouse'='s3://bucket/paimon');

CREATE TABLE paimon.ods.orders (
  id BIGINT PRIMARY KEY NOT ENFORCED,
  user_id BIGINT, amount DECIMAL(10,2), ts TIMESTAMP(3)
)
WITH (
  'bucket' = '4',
  'changelog-producer' = 'input',
  'merge-engine' = 'deduplicate'
);

INSERT INTO paimon.ods.orders
SELECT id, user_id, amount, ts FROM kafka_orders;
```

### 3.4 Hudi

```
特性:
  - 实时 upsert (COW / MOR 两种表)
  - Uber 开源
  - 与 Spark 强耦合

适合:
  - 实时 upsert + 历史
  - 与 Spark 生态 (Databricks 替代)
```

### 3.5 选型

| 场景 | 推荐 |
|:---|:---|
| **大厂主流 / 多引擎** | Iceberg ⭐ |
| **流批一体 / Flink** | Paimon ⭐ (国产) |
| **实时 upsert / Spark** | Hudi |
| **Databricks 平台** | Delta Lake |

## 四、实时数仓

### 4.1 Doris / StarRocks（国产 MPP ⭐）

```
特性:
  - MPP 列存
  - 实时写 (Stream Load / Routine Load)
  - 物化视图 (异步 + 同步)
  - 联邦查询 (External Catalog: Iceberg / Hive / Hudi)
  - 兼容 MySQL 协议
  - 国产 (Apache 顶级)

Doris vs StarRocks:
  Doris       Apache, 社区
  StarRocks   商业 + 开源 (CelerData)
  ~80% 兼容, 各有优势
```

### 4.2 Doris 实战

```sql
-- 主键模型 (Unique Key, 实时 upsert)
CREATE TABLE orders (
  id BIGINT, user_id BIGINT, amount DECIMAL(10,2), ts DATETIME,
  status VARCHAR(20)
)
UNIQUE KEY(id)
DISTRIBUTED BY HASH(id) BUCKETS 32
PROPERTIES (
  "replication_num" = "3",
  "enable_unique_key_merge_on_write" = "true",
  "function_column.sequence_col" = "ts"
);

-- Routine Load (Kafka 实时摄入)
CREATE ROUTINE LOAD app.load_orders ON orders
COLUMNS(id, user_id, amount, ts, status)
PROPERTIES ("desired_concurrent_number"="3", "max_batch_interval"="20")
FROM KAFKA (
  "kafka_broker_list" = "kafka:9092",
  "kafka_topic" = "orders",
  "property.kafka_default_offsets" = "OFFSET_BEGINNING"
);

-- 物化视图 (实时聚合)
CREATE MATERIALIZED VIEW mv_orders_hourly AS
SELECT
  date_trunc('hour', ts) AS hour,
  user_id,
  SUM(amount) AS total
FROM orders
GROUP BY hour, user_id;

-- 联邦查询 Iceberg
CREATE CATALOG iceberg_cat PROPERTIES (
  "type" = "iceberg",
  "iceberg.catalog.type" = "hms",
  "hive.metastore.uris" = "thrift://hms:9083"
);

SELECT * FROM iceberg_cat.ods.orders WHERE dt = '2026-06-27';
```

### 4.3 ClickHouse 实时数仓

```sql
-- AggregatingMergeTree + Materialized View
CREATE TABLE events_agg_local
ON CLUSTER prod
(
  hour DateTime,
  user String,
  total AggregateFunction(sum, Float64),
  cnt   AggregateFunction(count)
)
ENGINE = ReplicatedAggregatingMergeTree('/clickhouse/tables/{shard}/events_agg', '{replica}')
ORDER BY (hour, user)
PARTITION BY toYYYYMM(hour);

CREATE MATERIALIZED VIEW events_agg_mv TO events_agg_local AS
SELECT
  toStartOfHour(ts) AS hour,
  user,
  sumState(amount) AS total,
  countState() AS cnt
FROM events
GROUP BY hour, user;

-- 查询时 merge
SELECT hour, user, sumMerge(total), countMerge(cnt)
FROM events_agg_local
WHERE hour >= now() - INTERVAL 1 DAY
GROUP BY hour, user;
```

### 4.4 选型

| 场景 | 推荐 |
|:---|:---|
| **大单表 / 日志/事件 / 高并发简单查询** | ClickHouse ⭐ |
| **多表 JOIN / 实时数仓 / 主键 upsert** | Doris ⭐ / StarRocks ⭐ |
| **联邦查询 + 数据湖** | StarRocks ⭐ / Doris / Trino |
| **AI / 信创** | Doris (Apache 顶级国产) |

## 五、CDC 增量与流式入湖

### 5.1 Flink CDC（基于 Debezium）

```sql
-- MySQL CDC 源
CREATE TABLE mysql_orders (
  id BIGINT, user_id BIGINT, amount DECIMAL(10,2), ts TIMESTAMP(3),
  PRIMARY KEY (id) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = '10.0.0.1', 'port' = '3306',
  'username' = 'cdc', 'password' = '***',
  'database-name' = 'app', 'table-name' = 'orders',
  'scan.incremental.snapshot.enabled' = 'true',
  'scan.startup.mode' = 'initial'
);

-- 直接落 Paimon
INSERT INTO paimon.ods.orders SELECT * FROM mysql_orders;
```

### 5.2 Kafka Connect / Debezium

```
Debezium → Kafka → Spark/Flink → Iceberg/Paimon → Doris

工具栈:
  Strimzi Kafka Connect Operator
  Schema Registry (Avro/Protobuf)
  Debezium MySQL/PG/Mongo/Oracle Connector
```

## 六、Trino / Presto（即席查询）

```
特性:
  - MPP 跨源查询 (Iceberg + Hive + MySQL + PG + ES + ...)
  - 标准 SQL
  - 联邦
  - 适合 Ad-hoc / BI

部署:
  Coordinator + Worker (K8s Operator)
  Galaxy / Starburst (商业版)

替代 / 互补:
  StarRocks (有 External Catalog)
  Doris (External Catalog)
  Spark SQL (批 + Iceberg)
```

```sql
-- Trino 跨源 JOIN
SELECT
  o.id, o.amount, u.name, u.region
FROM iceberg.ods.orders o
JOIN mysql.app.users u ON o.user_id = u.id
WHERE o.dt = DATE '2026-06-27';
```

## 七、DolphinScheduler 多租户

### 7.1 部署

```yaml
# Helm
helm install dolphinscheduler dolphinscheduler/dolphinscheduler \
  --set api.replicaCount=2 \
  --set master.replicaCount=2 \
  --set worker.replicaCount=4 \
  --set postgresql.enabled=false \
  --set externalDatabase.host=pg.example.com \
  --set externalDatabase.database=dolphinscheduler \
  --set externalRegistry.registryServers="zk:2181" \
  -n ds
```

### 7.2 多租户隔离

```
租户 (Tenant) = Linux 用户
项目 (Project) = 业务隔离
资源中心 = 共享 jar / sql / 脚本

权限:
  租户 → 项目 → 工作流 → 任务
  K8s 集群独立 namespace
  Worker pool per team
```

### 7.3 K8s 任务执行

```yaml
# Worker 配置 K8s 任务
KUBERNETES_TASK_HOST=k8s-api
KUBERNETES_TASK_NAMESPACE=ds-job
KUBERNETES_TASK_IMAGE=harbor.example.com/ds-runtime:v1
```

## 八、Spark/Flink 调优

### 8.1 Spark 调优 Top 10

```
1.  spark.sql.adaptive.enabled=true (AQE) ⭐
2.  spark.sql.adaptive.coalescePartitions.enabled=true
3.  spark.sql.adaptive.skewJoin.enabled=true
4.  spark.dynamicAllocation.enabled=true + shuffleTracking
5.  spark.sql.shuffle.partitions = 总核数 × 2-3
6.  广播 JOIN (autoBroadcastJoinThreshold=100MB)
7.  Cache 大表多次使用
8.  Repartition 优化倾斜 (salt 加盐)
9.  Bloom Filter Index (Iceberg)
10. Celeborn / RSS 远程 shuffle
```

### 8.2 Flink 调优 Top 10

```
1.  taskmanager.numberOfTaskSlots = vcore × 1
2.  state.backend = rocksdb (大状态)
3.  checkpoint interval 1-5 min, timeout 10 min
4.  execution.checkpointing.mode=EXACTLY_ONCE
5.  内存: managed=0.4, network=0.1, jvm-overhead=0.1
6.  Watermark 对齐 + 空闲分区超时
7.  Source 并发 = Kafka 分区数
8.  反压: tm-network-buffer-size 调优 + 异步 IO
9.  Object Reuse + Operator Chaining
10. Kubernetes HA (replicas: 2)
```

## 九、数据血缘 + 数据质量

### 9.1 DataHub（LinkedIn）

```
特性:
  - 数据资产目录
  - 血缘 (Lineage) 表/列级
  - 业务术语 (Glossary)
  - 数据所有权
  - 集成 Spark/Flink/Airflow/dbt/Iceberg/Snowflake/...

部署:
  DataHub GMS + frontend + Kafka + MySQL/PG + ES
```

### 9.2 Apache Atlas

```
特性:
  - Hadoop 原生
  - 老 (维护一般)
  - 替代: DataHub / OpenMetadata
```

### 9.3 数据质量

```
Great Expectations ⭐:
  Python, 强大 expectation suite
  
Soda ⭐:
  SodaCL YAML, 易用
  
Apache Griffin:
  Hadoop 时代 (老)
  
dbt tests:
  与 dbt 集成

工具栈:
  Soda + Great Expectations 双栈
  与 Airflow / DolphinScheduler 集成
  告警接 Slack / 钉钉
```

## 十、监控告警

```
Spark:
  - Spark UI + History Server
  - Prometheus pushgateway / spark-prometheus-exporter
  - Driver / Executor 资源
  - shuffle 失败 / GC / OOM

Flink:
  - Flink Metric Reporter (Prometheus)
  - checkpoint 时间 / 大小 / 失败率
  - 反压 (BackPressure)
  - watermark 滞后

Kafka:
  - kafka-exporter, kafka-lag-exporter
  - Lag, ISR, controller, under-replicated

Doris / StarRocks:
  - BE 内存 + 磁盘
  - tablet 副本 / Compaction Score
  - Routine Load 状态

数据湖:
  - 文件数量 / 小文件比例
  - Compaction 状态
  - Snapshot 数量
  - Manifest 大小

调度:
  - Airflow DAG run 时长 / 失败率
  - DolphinScheduler 任务延迟
```

## 十一、典型坑（进阶）

| 坑 | 建议 |
|:---|:---|
| **Spark 小文件** | Iceberg rewrite_data_files / Spark coalesce |
| **Spark 数据倾斜** | AQE skewJoin + 加盐 + 广播 |
| **Spark OOM** | executor memory 调大 + spill 调优 + GC |
| **Flink 反压** | source / sink 并行 + buffer 调 + 异步 IO |
| **Flink Checkpoint 超时** | RocksDB + incremental + S3 multi-part |
| **Flink Savepoint 损坏** | 多版本保留 + 验证后切换 |
| **Iceberg 元数据膨胀** | rewrite_manifests + expire_snapshots |
| **Paimon 主键表 compaction 慢** | bucket 数调 + dedicated compaction Job |
| **Doris BE 高 Compaction Score** | tablet 数 + bucket 调 + 限流 |
| **CDC binlog GTID 缺失** | initial snapshot + GTID 持久 |
| **Hive Metastore 单点** | MySQL MGR + HA Metastore |
| **DolphinScheduler 任务堆积** | Worker pool 扩 + 队列优化 |
| **Trino OOM** | 调 max-memory-per-node / spill-enabled |
| **数据质量没接入** | Soda + Great Expectations + 告警 |
| **血缘没建** | DataHub 自动采集 (Spark/Flink/dbt) |

## 十二、Checklist（进阶）

```
计算:
☐ Spark Operator + Volcano + 动态分配
☐ Flink Kubernetes Operator + 自动 savepoint 升级
☐ Celeborn / Remote Shuffle (大 shuffle)
☐ Stargz 镜像懒加载

存储:
☐ 对象存储 (S3/OSS/MinIO) 取代 HDFS
☐ Iceberg 或 Paimon 一种湖格式
☐ 维护任务: rewrite_data + expire_snapshots + remove_orphan
☐ Hive Metastore HA / 替换 Polaris/Nessie

实时数仓:
☐ Doris 或 StarRocks 一种
☐ 主键模型 + Routine Load
☐ 物化视图 (实时聚合)
☐ External Catalog 联邦

CDC:
☐ Flink CDC 全增量一体
☐ Debezium + Kafka Connect 备选
☐ Schema Registry 接入

调度:
☐ Airflow (Python) / DolphinScheduler (国产) 一种
☐ 多租户 + 资源隔离
☐ K8s Worker
☐ 监控 + Alert

血缘 + 质量:
☐ DataHub 自动采集
☐ Great Expectations / Soda 数据质量
☐ 与调度集成 告警

监控:
☐ Prometheus + 各 exporter
☐ Grafana 大盘
☐ 关键告警 (反压/lag/失败)

平台化:
☐ Backstage 数据 IDP (数据集 + 业务术语)
☐ Self-service 申请
☐ FinOps (Doris/Flink/Spark 成本归属)
```

## 十三、推荐栈（进阶）

```
计算:        Spark 3.5 ⭐ + Flink 1.19 ⭐
调度器:      Volcano / Yunikorn
存储:        S3 / OSS / MinIO + Iceberg / Paimon ⭐
元数据:      Polaris / Nessie / DataHub
实时数仓:    Doris ⭐ / StarRocks ⭐
即席查询:    Trino / Presto
列存 OLAP:   ClickHouse ⭐
CDC:        Flink CDC ⭐ / Debezium
消息:        Kafka KRaft + Strimzi
采集:        SeaTunnel ⭐ + Flink CDC ⭐
调度:        Airflow ⭐ / DolphinScheduler ⭐
血缘:        DataHub ⭐
质量:        Great Expectations + Soda
BI:          Superset / FineBI / Quick BI
监控:        kube-prometheus + 各 exporter
平台:        Backstage + 自研数据门户
```

> 📖 **核心判断**：大数据进阶 = **Spark Operator + Volcano + Celeborn + AQE + 动态分配 + Flink Operator + Application + Savepoint 升级 + Paimon/Iceberg 湖仓 + Doris/StarRocks 实时数仓 + Flink CDC + DolphinScheduler 多租户 + DataHub 血缘 + Soda/GE 质量 + Prometheus 监控**。能搭出"Kafka → Flink CDC → Paimon → Doris/StarRocks → Superset"完整流批一体链路 + 监控告警 + 数据治理，就具备数据平台运维工程师能力。
