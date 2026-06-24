# ClickHouse（大数据场景）

> 大数据栈中的 **OLAP 终极武器**。列存 + 向量化 + 极致压缩，PB 级数据秒级响应。**日志分析、用户行为、广告分析、AIOps 监控指标的首选**。

> 💡 ClickHouse 的通用介绍详见 [中间件 → ClickHouse](../../09_中间件/07_ClickHouse/README.md)。本章聚焦**大数据栈中的角色与最佳实践**。

## 一、来历回顾

| 年份 | 事件 |
|:---:|:---|
| 2009 | Yandex（俄罗斯搜索引擎）启动 ClickHouse，为广告分析服务 |
| 2016 | 开源（Apache 2.0） |
| 2019-2022 | 国内大规模采用（字节、快手、阿里、滴滴） |
| 2024 | 24.x 引入 Lightweight UPDATE / Parallel Replicas |
| 2025 | **存算分离架构 + 与 S3/Iceberg 深度集成** |

## 二、为什么选 ClickHouse 进大数据栈

```
1. 单表 GROUP BY 性能怪兽
   - 列存 + 向量化（SIMD）
   - 1000 亿行 GROUP BY 秒级

2. 压缩比惊人
   - LZ4 / ZSTD / Delta / DoubleDelta
   - 通常 10:1，极端 50:1

3. 写吞吐高
   - 单分片 50-200MB/s（百亿行/天）

4. 部署轻
   - 一个二进制启动
   - 不依赖 Hadoop

5. 与现代大数据栈集成好
   - Kafka 直接消费
   - S3/HDFS 外部表
   - 24.x+ Iceberg 集成
```

## 三、在大数据栈中的角色

```
典型大数据架构:
  数据源        Kafka / CDC
   ↓
  采集层        Flink / Spark Streaming / Vector
   ↓
  存储层        ── HDFS / S3 / Iceberg / Delta
   ↓             └── ClickHouse（实时 OLAP）
  服务层        Trino / Spark SQL  +  ClickHouse SQL
   ↓
  应用层        Superset / Metabase / 自研 BI

ClickHouse 定位:
  ✅ 实时大屏 / BI 报表（亚秒级）
  ✅ 日志分析（替代部分 ES OLAP 场景）
  ✅ AIOps 监控数据（指标存储）
  ✅ 用户行为分析 / 漏斗 / 留存
```

## 四、典型应用场景

### 4.1 日志分析

```sql
-- 收集层: Filebeat/Vector → Kafka → CH (Kafka 引擎)
CREATE TABLE kafka_logs (raw String)
ENGINE = Kafka()
SETTINGS kafka_broker_list='kafka:9092',
         kafka_topic_list='app-logs',
         kafka_group_name='clickhouse-logs',
         kafka_format='JSONAsString',
         kafka_num_consumers=4;

-- 落表
CREATE TABLE logs (
  ts        DateTime CODEC(DoubleDelta, ZSTD),
  service   LowCardinality(String),
  level     LowCardinality(String),
  trace_id  String CODEC(ZSTD),
  message   String CODEC(ZSTD),
  attrs     JSON
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(ts)
ORDER BY (service, level, ts)
TTL ts + INTERVAL 30 DAY;

-- 物化视图自动入库
CREATE MATERIALIZED VIEW mv_logs TO logs AS
SELECT
  parseDateTimeBestEffort(JSONExtractString(raw, 'timestamp')) AS ts,
  JSONExtractString(raw, 'service') AS service,
  JSONExtractString(raw, 'level') AS level,
  JSONExtractString(raw, 'trace_id') AS trace_id,
  JSONExtractString(raw, 'message') AS message,
  raw AS attrs
FROM kafka_logs;

-- 查询: 某服务最近 1 小时的 ERROR 日志按分钟统计
SELECT toStartOfMinute(ts) AS m, count() FROM logs
WHERE service='order-api' AND level='ERROR' AND ts > now() - INTERVAL 1 HOUR
GROUP BY m ORDER BY m;
```

### 4.2 用户行为分析

```sql
CREATE TABLE user_events (
  event_date Date,
  event_time DateTime,
  user_id UInt64,
  device_id String,
  event_name LowCardinality(String),
  page_path LowCardinality(String),
  utm_source LowCardinality(String),
  duration UInt32,
  props JSON
) ENGINE = MergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_name, user_id, event_time);

-- 漏斗分析（窗口函数 + arrayJoin）
WITH funnel AS (
  SELECT user_id,
    windowFunnel(3600)(
      event_time,
      event_name='visit',
      event_name='add_cart',
      event_name='checkout',
      event_name='paid'
    ) AS step
  FROM user_events
  WHERE event_date BETWEEN '2026-06-01' AND '2026-06-30'
  GROUP BY user_id
)
SELECT step, count() FROM funnel GROUP BY step ORDER BY step;

-- 留存分析（retention 函数）
SELECT
  retention(
    event_date = '2026-06-01',
    event_date = '2026-06-08',
    event_date = '2026-06-15'
  ) AS r
FROM user_events
GROUP BY user_id;

-- 用户路径
SELECT sequenceCount('(?1)(?2)')(event_time, event_name='visit', event_name='paid')
FROM user_events;
```

### 4.3 AIOps 监控指标

```sql
CREATE TABLE metrics (
  metric_time DateTime CODEC(DoubleDelta, LZ4),
  metric_name LowCardinality(String),
  service     LowCardinality(String),
  host        LowCardinality(String),
  value       Float64 CODEC(Gorilla, LZ4),
  labels      Map(LowCardinality(String), String)
) ENGINE = MergeTree
PARTITION BY toDate(metric_time)
ORDER BY (metric_name, service, metric_time)
TTL metric_time + INTERVAL 90 DAY;

-- 查询: 服务 CPU 趋势
SELECT toStartOfMinute(metric_time) AS m, avg(value)
FROM metrics
WHERE metric_name='cpu.usage' AND service='order-api'
  AND metric_time > now() - INTERVAL 1 HOUR
GROUP BY m ORDER BY m;

-- 异常检测: 当前值偏离最近 7 天同时段均值的程度
WITH base AS (
  SELECT toStartOfMinute(metric_time) AS m, avg(value) AS avg_v
  FROM metrics
  WHERE metric_name='qps' AND service='order-api'
    AND metric_time > now() - INTERVAL 7 DAY
  GROUP BY m
)
SELECT m, value, (value - avg_v) / avg_v AS deviation
FROM (SELECT toStartOfMinute(metric_time) AS m, avg(value) AS value FROM metrics
      WHERE metric_name='qps' AND service='order-api'
        AND metric_time > now() - INTERVAL 30 MINUTE
      GROUP BY m)
JOIN base USING m
WHERE abs(deviation) > 0.5;
```

### 4.4 广告 / 流量分析

```sql
-- 大宽表 + 物化视图预聚合
CREATE TABLE ad_clicks ( ... ) ENGINE = MergeTree...;

CREATE MATERIALIZED VIEW mv_ad_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(dt) ORDER BY (dt, advertiser_id, ad_id)
AS SELECT toDate(click_time) AS dt, advertiser_id, ad_id,
   count() AS clicks, sum(cost) AS cost, sum(conversion) AS conv
FROM ad_clicks GROUP BY dt, advertiser_id, ad_id;
```

### 4.5 Trace / OpenTelemetry

```sql
CREATE TABLE traces (
  trace_id        FixedString(32),
  span_id         FixedString(16),
  parent_span_id  FixedString(16),
  service         LowCardinality(String),
  operation       LowCardinality(String),
  start_time      DateTime64(9) CODEC(DoubleDelta, ZSTD),
  duration_ns     UInt64,
  status_code     UInt8,
  tags            Map(LowCardinality(String), String)
) ENGINE = MergeTree
PARTITION BY toYYYYMMDD(start_time)
ORDER BY (service, operation, start_time);

-- p99 延迟
SELECT service, operation,
  quantile(0.99)(duration_ns/1e6) AS p99_ms,
  quantile(0.5)(duration_ns/1e6)  AS p50_ms,
  count() AS qps
FROM traces
WHERE start_time > now() - INTERVAL 5 MINUTE
GROUP BY service, operation
ORDER BY p99_ms DESC LIMIT 50;
```

## 五、大数据栈集成最佳实践

### 5.1 Kafka 直接消费（写入主路径）

```sql
-- 1. Kafka 引擎表（消费）
CREATE TABLE kafka_events ( raw String )
ENGINE = Kafka()
SETTINGS
  kafka_broker_list='kafka1:9092,kafka2:9092',
  kafka_topic_list='events',
  kafka_group_name='clickhouse-events',
  kafka_format='JSONAsString',
  kafka_num_consumers=8,
  kafka_max_block_size=65536;

-- 2. 落地表（实际存储）
CREATE TABLE events (...) ENGINE = ReplicatedMergeTree(...);

-- 3. 物化视图（自动 ETL）
CREATE MATERIALIZED VIEW mv_events TO events AS
SELECT ... FROM kafka_events;
```

### 5.2 S3 / HDFS 外部表

```sql
-- 直接查 S3 上的 Parquet（不导入）
SELECT count() FROM s3(
  'https://bucket.s3.amazonaws.com/logs/*.parquet',
  'AKIA...', 'secret...',
  'Parquet'
);

-- Iceberg 表（24.x+）
CREATE TABLE iceberg_events
ENGINE = Iceberg('s3://bucket/warehouse/events/', '...');

-- 增量同步到本地表（性能更好）
INSERT INTO local_events
SELECT * FROM iceberg_events
WHERE event_date >= today() - 1;
```

### 5.3 Spark / Flink 写入

```python
# Spark JDBC
df.write.format("jdbc") \
  .option("url", "jdbc:clickhouse://ch:8123/default") \
  .option("dbtable", "events") \
  .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
  .option("batchsize", "100000") \
  .mode("append").save()

# 推荐 native client（更快）
spark-clickhouse-connector

# Flink
flink-connector-clickhouse
```

### 5.4 Trino 联邦查询

```properties
# trino/etc/catalog/clickhouse.properties
connector.name=clickhouse
connection-url=jdbc:clickhouse://ch:8123
connection-user=trino
connection-password=...
```

```sql
-- Trino 跨源 JOIN：Iceberg 维度表 + ClickHouse 事实表
SELECT ch.user_id, dim.country, count(*)
FROM clickhouse.default.events ch
JOIN iceberg.dim.users dim ON ch.user_id = dim.user_id
WHERE ch.event_date = '2026-06-22'
GROUP BY ch.user_id, dim.country;
```

## 六、大数据规模下的建表最佳实践

```sql
-- 大宽表 + 高基数 + 日均 100 亿行级别
CREATE TABLE events_local (
  event_time     DateTime CODEC(DoubleDelta, ZSTD(1)),
  event_date     Date DEFAULT toDate(event_time),
  
  -- 高基数标识（用 LowCardinality 还是 String 看基数）
  user_id        UInt64,
  device_id      String CODEC(ZSTD),
  
  -- 枚举 + 低基数 → LowCardinality
  event_name     LowCardinality(String),
  country        LowCardinality(String),
  app_version    LowCardinality(String),
  
  -- 数值列
  duration_ms    UInt32 CODEC(T64, ZSTD),
  revenue        Decimal(18, 4) CODEC(ZSTD),
  
  -- JSON 列（24.x 推荐）
  attrs          JSON,
  
  -- 时序压缩（重复值多）
  region         LowCardinality(String)
)
ENGINE = ReplicatedMergeTree('/ch/tables/{shard}/events', '{replica}')
PARTITION BY toYYYYMMDD(event_date)        -- 按天分区
ORDER BY (event_name, user_id, event_time) -- 查询模式决定
TTL event_date + INTERVAL 90 DAY
SETTINGS
  index_granularity = 8192,
  storage_policy = 's3_tiered';            -- 热温冷
```

## 七、热温冷分层（存算分离）

```xml
<!-- config.xml -->
<storage_configuration>
  <disks>
    <ssd><path>/var/lib/clickhouse/ssd/</path></ssd>
    <hdd><path>/var/lib/clickhouse/hdd/</path></hdd>
    <s3><type>s3</type><endpoint>...</endpoint></s3>
  </disks>
  <policies>
    <s3_tiered>
      <volumes>
        <hot><disk>ssd</disk></hot>
        <warm><disk>hdd</disk></warm>
        <cold><disk>s3</disk></cold>
      </volumes>
      <move_factor>0.2</move_factor>
    </s3_tiered>
  </policies>
</storage_configuration>
```

```sql
-- TTL 自动迁移
ALTER TABLE events MODIFY TTL
  event_date + INTERVAL 7 DAY  TO VOLUME 'warm',
  event_date + INTERVAL 30 DAY TO VOLUME 'cold',
  event_date + INTERVAL 365 DAY DELETE;
```

## 八、分布式部署架构

```
                ┌────── chproxy / LB ──────┐
                       ↓
   ┌──── 分布式表 Distributed ──────┐
   ↓                                ↓
 shard1                          shard2
  ├── ReplicatedMergeTree (rep1)   ├── ReplicatedMergeTree (rep1)
  ├── ReplicatedMergeTree (rep2)   ├── ReplicatedMergeTree (rep2)
  └── ClickHouse Keeper × 3        └── ...
```

```sql
-- 本地表
CREATE TABLE events_local ON CLUSTER prod ( ... )
ENGINE = ReplicatedMergeTree('/ch/{shard}/events', '{replica}')
...;

-- 分布式表
CREATE TABLE events ON CLUSTER prod AS events_local
ENGINE = Distributed(prod, default, events_local, rand());
```

**经验**：
```
小集群: 1 分片 + 2-3 副本
中集群: 2-4 分片 + 2 副本（总 4-8 节点）
大集群: 8-32 分片 + 2 副本（数百节点）

分片数原则:
  - 写入吞吐 / 单分片 50-100MB/s
  - 数据总量 / 单分片建议 < 100TB
```

## 九、常见坑（大数据场景特别版）

| 坑 | 建议 |
|:---|:---|
| **单行 INSERT 拖垮 Keeper** | 必须批量（每批 10K+ 行） |
| **小 part 太多** | 用 Kafka 引擎或 Async Insert |
| **小文件 part 风暴** | 限制 parts_to_throw_insert |
| **Compaction 拖死** | 错峰 + 限速 |
| **JSON 列爆字段** | 改 Map(LowCardinality, String) |
| **没有 LowCardinality** | 枚举类必加 |
| **大表 JOIN 慢** | dictionary / 预聚合 / 小表广播 |
| **跨分片 JOIN** | 设计上避免，用 GLOBAL JOIN 慎用 |
| **Memory limit 超** | external GROUP BY 落盘 |
| **副本不一致** | 检查 system.replicas + replication_queue |
| **Keeper 压力** | 监控 + 调大 |
| **冷数据查询慢** | S3 缓存 + 二级索引 |
| **物化视图链路问题** | MV 失败不影响源表写入需开 fault tolerance |

## 十、监控（大数据场景）

```sql
-- 写入慢
SELECT event_time, query, written_rows, written_bytes, query_duration_ms
FROM system.query_log
WHERE event_time > now() - INTERVAL 1 HOUR
  AND type = 'QueryFinish'
  AND query_kind = 'Insert'
ORDER BY query_duration_ms DESC LIMIT 20;

-- Part 数量
SELECT table, count() FROM system.parts
WHERE active GROUP BY table ORDER BY 2 DESC LIMIT 20;

-- 副本滞后
SELECT table, replica_name, absolute_delay
FROM system.replicas ORDER BY absolute_delay DESC;

-- 物化视图状态
SELECT * FROM system.tables WHERE engine LIKE '%MaterializedView%';
```

## 十一、ClickHouse vs Doris/StarRocks（大数据场景）

| 维度 | ClickHouse | Doris/StarRocks |
|:---|:---|:---|
| 单表性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| JOIN 性能 | ⚠️ | **⭐⭐⭐⭐⭐** |
| 高并发 BI | ⭐⭐ | **⭐⭐⭐⭐⭐** |
| 实时写入 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 资源利用 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 学习曲线 | 陡 | 平 |
| 国内主流 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 数据湖集成 | 24.x+ Iceberg | Iceberg/Hudi/Delta |
| 国产替代 | ByteHouse | 镜舟 StarRocks |

**经验**：
- **日志 / 单表大宽表 / 极致性能** → ClickHouse
- **数仓 / 多表 JOIN / 高并发 BI** → Doris/StarRocks
- 两者并存很常见

## 十二、大数据栈中的角色总结

```
2025 大数据栈中的 ClickHouse:
  - 实时 OLAP 层主力（与 Doris/StarRocks 并存）
  - 日志 / Trace / Metrics 后端
  - AIOps 指标存储（替代部分 InfluxDB）
  - 用户行为分析底层（替代部分 Druid）
  - Lakehouse 中的"快路径"（Trino 是 Adhoc 慢路径）
```

> 📖 **核心判断**：大数据栈中，**ClickHouse = 实时 OLAP 快路径**，与 Spark（ETL）/ Trino（Adhoc）/ Flink（流）形成互补。**单表性能极致 + 压缩比惊人**仍是其无可替代的优势。配合 Kafka + Iceberg + S3 分层存储，能搭出 PB 级实时分析平台。
