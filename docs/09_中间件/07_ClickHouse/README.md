# ClickHouse

> 列存 OLAP 数据库的王者。**单机性能吊打绝大多数数据仓库**，PB 级数据秒级查询的能力让它成为日志分析、用户行为、AIOps 的首选。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2009 | Yandex（俄罗斯搜索引擎）内部启动 ClickHouse，为广告分析服务 |
| 2016.6 | 开源（Apache 2.0） |
| 2019 | 国内字节、快手、阿里大规模采用 |
| 2021 | **ClickHouse, Inc.** 公司成立（独立运营） |
| 2022 | 22.3 LTS、ClickHouse Cloud Beta |
| 2023 | 23.x 系列、与 dbt/Iceberg 深度集成 |
| 2024 | **24.x 引入 Lightweight UPDATE / Parallel Replicas** |
| 2025 | **25.x 列存存算分离**、与 S3 深度集成 |

**当前主流 LTS**：24.3 / 24.8。

## 二、ClickHouse 是什么

```
"列存分析数据库" (Column-Oriented OLAP DBMS)

核心特点:
  - 列式存储（同列连续存，压缩比 10:1+）
  - 向量化执行（SIMD）
  - 极致并行（多核、多分片）
  - SQL 完整支持（MySQL/PG 协议兼容）
  - 单表查询性能怪兽（单机 GB/s 级扫描）

注意:
  - 不是 OLTP（不擅长频繁 UPDATE/DELETE）
  - 不强一致（最终一致）
  - 不适合事务（弱事务）
```

## 三、核心功能

```
1. 列式存储 + LZ4/ZSTD 压缩
2. SIMD 向量化执行
3. 分布式表 + 分片 + 副本
4. 多种引擎（MergeTree 家族 + 特殊引擎）
5. 物化视图 / Projection（自动聚合）
6. 丰富 SQL（窗口函数、CTE、JOIN、UDF）
7. 多协议接入（HTTP/TCP/MySQL/PG）
8. 外部表（S3/HDFS/Kafka/JDBC）
9. Geo / IP / URL / 数组函数
10. 副本通过 Keeper/ZK（24.x 起 Keeper 默认）
```

## 四、表引擎家族（核心知识）

### 4.1 MergeTree 家族（核心）

| 引擎 | 用途 |
|:---|:---|
| **MergeTree** | 通用列存表（首选） |
| **ReplicatedMergeTree** | 自带副本 |
| **ReplacingMergeTree** | 主键去重（异步） |
| **SummingMergeTree** | 自动求和聚合 |
| **AggregatingMergeTree** | 任意聚合状态 |
| **CollapsingMergeTree** | 行级折叠（适合 CDC） |
| **VersionedCollapsing** | 带版本的折叠 |
| **GraphiteMergeTree** | 时序数据 |

### 4.2 特殊引擎

| 引擎 | 用途 |
|:---|:---|
| **Distributed** | 分布式表（路由到各分片） |
| **Kafka** | 直接消费 Kafka |
| **MaterializedView** | 物化视图 |
| **MaterializedPostgreSQL** | PG CDC 同步 |
| **S3 / HDFS** | 外部表 |
| **Memory / Buffer** | 临时/缓冲 |

## 五、为什么 ClickHouse 这么快

```
1. 列式存储:
   只读需要的列（10% 列 → 10% IO）

2. 数据压缩:
   同列相似度高 → 压缩比 10:1
   LZ4 / ZSTD / Delta / DoubleDelta

3. 向量化执行:
   一次处理一批（SIMD）

4. 主键稀疏索引:
   每 8192 行一个索引（少而快）

5. 分区裁剪:
   按时间分区 → 一次跳过整月

6. 并行执行:
   单机多核 + 多分片

7. 异步 Merge:
   写入快，后台合并
```

## 六、使用场景

### ✅ 完美匹配

| 场景 | 说明 |
|:---|:---|
| **日志分析** | 大日志 GROUP BY、TopN（替代 ES 重分析场景） |
| **用户行为分析** | 留存、漏斗、路径 |
| **实时大屏** | 千亿级实时聚合 |
| **AIOps 指标** | 监控指标存储与分析 |
| **广告投放分析** | Yandex 起家场景 |
| **风控反作弊** | 高速明细 + 聚合 |
| **物联网时序** | 替代 InfluxDB |
| **Trace 分析** | OpenTelemetry 后端 |
| **替代 Hadoop 离线** | Spark + Hive 太慢时 |

### ⚠️ 不推荐

- **OLTP 事务** → MySQL / PG
- **频繁 UPDATE/DELETE** → 关系数据库
- **强一致 + 多表 JOIN 复杂** → 数据仓库
- **小数据 + 高并发点查** → Redis / MySQL
- **行级别精确控制** → PG

## 七、ClickHouse vs 其他 OLAP

| 维度 | ClickHouse | Doris | StarRocks | Druid | Pinot | DuckDB |
|:---|:---|:---|:---|:---|:---|:---|
| 单表性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| JOIN 性能 | ⚠️ 中 | **强** | **强** | 弱 | 弱 | 中 |
| 并发查询 | 中 | **强** | **强** | 强 | 强 | 单机 |
| 易用性 | 中 | 高 | 高 | 中 | 中 | 极高 |
| 国内主流 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| MySQL 兼容 | 中 | **强** | **强** | 弱 | 弱 | 强 |
| 实时入库 | 强 | 强 | 强 | 强 | 强 | 中 |
| 学习成本 | 中 | 低 | 低 | 高 | 高 | 极低 |

> 💡 **国内现状**：ClickHouse 单表性能极致，**Doris/StarRocks JOIN 和并发更强**，越来越多团队选择 Doris/StarRocks。但 ClickHouse 在日志和单表大宽表场景仍是首选。

## 八、最佳实践

### 8.1 建表最佳实践

```sql
CREATE TABLE events
(
    event_time      DateTime CODEC(DoubleDelta, ZSTD(1)),
    event_date      Date DEFAULT toDate(event_time),
    user_id         UInt64,
    event_type      LowCardinality(String),
    country         LowCardinality(String),
    properties      JSON,
    revenue         Decimal(18, 4) CODEC(ZSTD)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_type, user_id, event_time)
TTL event_date + INTERVAL 365 DAY
SETTINGS index_granularity = 8192;
```

**关键点**：

```
✅ PARTITION BY 用 toYYYYMM 或 toDate（不要太细，每月 1 个分区起）
✅ ORDER BY 按"过滤条件 + 聚合维度"排序（决定数据顺序）
✅ LowCardinality 用于枚举类（性能 +50%）
✅ 数值类用最小够用类型（UInt32 比 UInt64 省空间）
✅ CODEC 压缩选择：DoubleDelta 时间、ZSTD 通用
✅ TTL 自动过期
✅ index_granularity 默认 8192，绝大多数场景不用改

❌ 不要用 Nullable（性能差），用默认值替代
❌ 不要太多列（建议 < 200）
❌ 不要频繁 ALTER TABLE
```

### 8.2 分区与排序

```
PARTITION 决定:
  - 数据物理分组
  - DROP/ALTER 单位（DROP PARTITION 秒级）
  - 分区裁剪范围

ORDER BY 决定:
  - 数据在 part 内顺序
  - 主键稀疏索引
  - 压缩效率

经验:
  PARTITION:  按月/按天（数据量大才按天）
  ORDER BY:   高基数 + 查询过滤字段在前
```

### 8.3 物化视图（杀手锏）

```sql
-- 自动维护预聚合
CREATE MATERIALIZED VIEW events_daily_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, event_type)
AS SELECT
    event_date,
    event_type,
    count() AS cnt,
    sum(revenue) AS total_revenue
FROM events
GROUP BY event_date, event_type;

-- 查询日级汇总秒级
SELECT event_date, sum(cnt) FROM events_daily_mv
WHERE event_date >= today() - 30 GROUP BY event_date;
```

### 8.4 副本与分片

```
单分片多副本:
  ReplicatedMergeTree + Keeper/ZK
  数据自动同步

分布式表 (Distributed):
  N 分片 × M 副本
  查询自动路由 + 合并

推荐:
  小集群 (< 100TB): 1 分片 + 2-3 副本
  中集群 (100TB-PB): 2-4 分片 + 2 副本
  大集群: 多分片 + 2 副本
```

```sql
-- 本地表
CREATE TABLE events_local ON CLUSTER prod
( ... )
ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/events', '{replica}')
...

-- 分布式表
CREATE TABLE events ON CLUSTER prod AS events_local
ENGINE = Distributed(prod, default, events_local, rand());
```

### 8.5 数据导入

```
✅ 批量写入（每批 1 万-100 万行）
✅ 并发 = CPU 核数
✅ 用 Native / RowBinary 格式（最快）
✅ 客户端: clickhouse-client / vector / Materialize / Kafka 引擎
✅ Buffer 引擎做前置缓冲

❌ 单行 INSERT（极慢，会让 ZK 爆炸）
❌ 频繁 UPDATE/DELETE
```

### 8.6 关键参数

```xml
<!-- config.xml -->
<max_concurrent_queries>200</max_concurrent_queries>
<max_server_memory_usage>0</max_server_memory_usage>

<!-- users.xml -->
<max_memory_usage>20000000000</max_memory_usage>  <!-- 20GB -->
<max_bytes_before_external_group_by>10000000000</max_bytes_before_external_group_by>
<max_threads>16</max_threads>
<max_execution_time>300</max_execution_time>

<!-- MergeTree -->
parts_to_throw_insert = 3000
max_parts_in_total = 100000
old_parts_lifetime = 480
merge_max_block_size = 8192
```

### 8.7 24.x 新特性应用

```sql
-- Lightweight DELETE（不立刻物理删，标记）
DELETE FROM events WHERE event_date < '2024-01-01';

-- Lightweight UPDATE
UPDATE events SET revenue = 0 WHERE user_id = 0;

-- Parallel Replicas（并行副本查询提速）
SET allow_experimental_parallel_reading_from_replicas = 1;

-- Projection（自动维护的二级索引/聚合）
ALTER TABLE events ADD PROJECTION proj_country
( SELECT * ORDER BY country, event_time );
```

## 九、运维命令速查

```sql
-- 集群
SELECT * FROM system.clusters;
SELECT * FROM system.replicas FORMAT Vertical;

-- 表/分区
SELECT database, table, sum(rows), sum(bytes_on_disk) FROM system.parts
WHERE active GROUP BY database, table ORDER BY 4 DESC;

SELECT partition, count(), sum(rows), sum(bytes_on_disk)
FROM system.parts WHERE table = 'events' AND active
GROUP BY partition ORDER BY partition;

-- 慢查询
SELECT query_duration_ms, query, read_rows, memory_usage
FROM system.query_log
WHERE event_time > now() - INTERVAL 1 HOUR
ORDER BY query_duration_ms DESC LIMIT 20;

-- 锁/Mutation
SELECT * FROM system.mutations WHERE NOT is_done;
SELECT * FROM system.replication_queue;

-- 性能事件
SELECT * FROM system.events ORDER BY value DESC LIMIT 30;
SELECT * FROM system.metrics WHERE value > 0;

-- 数据 part 合并状态
SELECT * FROM system.merges;
```

## 十、常见坑

| 坑 | 建议 |
|:---|:---|
| **单行 INSERT** | 批量写！每批 1 万+ 行 |
| **小 part 太多** | parts_to_throw_insert 限制 + 批量 |
| **频繁 UPDATE/DELETE** | 改用 ReplacingMergeTree 或 24.x Lightweight |
| **Nullable 列** | 改默认值或 -1 |
| **分区过细（每小时）** | 至少按天，建议按月 |
| **ORDER BY 字段顺序错** | 高过滤字段在前 |
| **没有 LowCardinality** | 枚举类必加 |
| **Memory limit 超** | 分批 + external GROUP BY |
| **ZK/Keeper 压力大** | 减少 part 数 + 升级 ClickHouse Keeper |
| **JOIN 慢** | 小表用 dictionary，大表先聚合 |
| **磁盘满** | TTL + 监控 + 异地备份 |
| **没有备份** | clickhouse-backup → S3 |
| **跨副本一致性问题** | SELECT FINAL 或异步合并完后查 |

## 十一、生态与工具

| 工具 | 用途 |
|:---|:---|
| **clickhouse-client** | 官方 CLI |
| **clickhouse-keeper** | 替代 ZooKeeper |
| **clickhouse-backup** | 备份还原 → S3 |
| **chproxy** | 代理 / 限流 / 缓存 |
| **clickhouse-bulk** | INSERT 缓冲代理 |
| **Vector / Fluent Bit** | 日志采集 → CH |
| **Materialize / RisingWave** | 流式物化视图 |
| **dbt + dbt-clickhouse** | 数仓建模 |
| **Tabix / DBeaver / Datagrip** | GUI |
| **clickhouse-operator (Altinity)** | K8s |
| **ClickHouse Cloud** | 商业托管 |

## 十二、监控指标（必看）

```
查询:
  Query count / failed
  query_duration_ms p99
  memory_usage p99
  ReadyForFetch / Async Insert queue

存储:
  parts count per table  ← 关键，< 300/分区
  delayed inserts
  disk used %
  background merges

副本:
  replication_queue length
  is_session_expired (Keeper)
  lag

系统:
  CPU / RAM / Disk IO / Network
```

**工具**：Prometheus + clickhouse-exporter + Grafana / Datadog / Altinity Observability。

## 十三、ClickHouse in K8s

```
推荐: Altinity clickhouse-operator (CRD)

apiVersion: clickhouse.altinity.com/v1
kind: ClickHouseInstallation
spec:
  configuration:
    clusters:
      - name: prod
        layout:
          shardsCount: 2
          replicasCount: 2

特性:
  ✅ 声明式 CRD
  ✅ 自动副本/分片
  ✅ Keeper 集成
  ✅ 配置热更新
  ✅ 监控集成
```

## 十四、备份与恢复

```bash
# clickhouse-backup 工具
# 配置 → ~/.clickhouse-backup/config.yml
clickhouse-backup create my-backup
clickhouse-backup upload my-backup
clickhouse-backup download my-backup
clickhouse-backup restore my-backup

# 集成 S3
remote_storage: s3
s3:
  bucket: ch-backup
  region: cn-north-1
```

## 十五、与 Kafka / 数据湖集成

```sql
-- Kafka 引擎直接消费
CREATE TABLE kafka_events (raw String) ENGINE = Kafka()
SETTINGS kafka_broker_list='kafka:9092',
         kafka_topic_list='events',
         kafka_group_name='clickhouse',
         kafka_format='JSONAsString';

-- 物化视图自动入库
CREATE MATERIALIZED VIEW mv_events TO events AS
SELECT JSONExtractString(raw, 'user_id') AS user_id, ...
FROM kafka_events;

-- S3 / Iceberg
CREATE TABLE s3_data ENGINE = S3('https://...', 'Parquet');
CREATE TABLE iceberg_t ENGINE = Iceberg('s3://...', '...');
```

## 十六、学习路径

```
入门:
  1. 单节点 Docker 起 ClickHouse
  2. 建第一张 MergeTree 表
  3. 导入 1 亿行体验秒级查询
  4. 理解 PARTITION + ORDER BY

进阶:
  5. ReplicatedMergeTree + Keeper 副本
  6. 分布式表 + 多分片
  7. 物化视图 / Projection
  8. 索引 / TTL / 压缩 CODEC

高阶:
  9. JVM ... 啊不是, 内存/线程参数调优
  10. Kafka 集成实时入库
  11. 备份恢复实战
  12. K8s + Operator 部署
  13. 监控告警全链路
  14. 国产 Doris/StarRocks 对比评估
```

## 十七、国产替代 / 同类竞品

| 产品 | 厂商 | 说明 |
|:---|:---|:---|
| **Apache Doris** | 百度开源 | MPP + MySQL 协议、JOIN 极强 |
| **StarRocks** | 镜舟科技 | Doris Fork、商业增强 |
| **ByteHouse** | 字节跳动 | CH 商业版 |
| **Tencent Cloud CDW-CH** | 腾讯云 | 托管 CH |
| **阿里云 ADB-PG / Hologres** | 阿里 | HTAP |
| **TDengine** | 涛思 | 时序专精 |

## 十八、ClickHouse vs Doris/StarRocks 怎么选

```
选 ClickHouse:
  - 海量单表大宽表分析
  - 日志/AIOps/广告分析
  - 性能极致 + 团队能 Hold 住
  - 国际生态对齐

选 Doris / StarRocks:
  - 多表 JOIN 复杂
  - 高并发 BI 报表
  - MySQL 协议无痛接入
  - 国产化 + 商业支持
  - 团队偏好"傻瓜化"
```

> 📖 **核心判断**：ClickHouse 在**单表性能、压缩比、日志/AIOps 场景**仍是王者。如果你的查询模式有大量 JOIN 或要做企业级 BI 报表，**Doris/StarRocks 是更现代的选择**。两者并存于国内大数据栈，掌握其一即可走天下。
