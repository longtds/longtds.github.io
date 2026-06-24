# PostgreSQL（大数据场景）

> PG 不只是 OLTP——**在大数据栈中，PG 是元数据底座、轻量数仓、向量库、HTAP 起步首选**。一套数据库吃掉传统大数据栈的多个组件。

> 💡 PG 的通用介绍详见 [中间件 → PostgreSQL](../../09_中间件/02_PostgreSQL/README.md)。本章聚焦**大数据场景下的角色与扩展**。

## 一、PG 在大数据栈中的多重角色

```
1. 元数据存储
   - Hive Metastore 后端（替代 MySQL，更稳）
   - Airflow / DolphinScheduler 元数据库
   - Trino / Spark 调度元数据
   - DataHub / Atlas / OpenMetadata 后端

2. 轻量数仓 / 数据集市
   - 100GB-1TB 量级 OLAP（替代过早上 CH）
   - Citus 扩展 → 分布式 PG 数仓

3. 时序数据库
   - TimescaleDB 扩展（监控、IoT）

4. 向量数据库 / RAG
   - pgvector 扩展（AI 时代爆发点）

5. CDC 源头
   - WAL 逻辑解码 → Debezium / wal2json → Kafka

6. 数据科学辅助
   - PostGIS（GIS 分析全球最强）
   - PL/Python、PL/R（数据库内 ML）
```

## 二、大数据栈中 PG 的扩展生态

| 扩展 | 角色 |
|:---|:---|
| **Citus** | 分布式分片 → 数仓 |
| **TimescaleDB** | 时序数据库 |
| **pgvector** | 向量检索（RAG 必备） |
| **PostGIS** | 地理空间分析 |
| **pg_partman** | 自动分区管理（大表必备） |
| **pg_cron** | 定时任务（替代 Airflow 微任务） |
| **wal2json** | CDC 输出 |
| **AGE** | 图数据库 |
| **pgmq** | 队列扩展 |
| **pg_duckdb** | DuckDB 嵌入 PG（OLAP 加速）|
| **pg_analytics** | 列存扩展（Parquet 直查） |

## 三、PG 作为 Hive Metastore（HMS）后端

### 为什么是 PG 不是 MySQL

```
✅ MVCC 更适合频繁 DDL/元数据更新
✅ JSON 字段（properties 表）查询好
✅ 并发性能更稳
✅ 长期备份恢复成熟
✅ Patroni HA + pgBackRest 一体化运维

实际:
  - 大型 Hadoop / Cloudera CDP 部署常用 PG 做 HMS 后端
  - Spark + HMS + Iceberg 元数据可全在 PG
```

### 部署示例

```bash
# 1. PG 创建 HMS 库
createuser hive
createdb hive_metastore -O hive

# 2. HMS 配置（hive-site.xml）
javax.jdo.option.ConnectionURL=jdbc:postgresql://pg-host:5432/hive_metastore
javax.jdo.option.ConnectionDriverName=org.postgresql.Driver
javax.jdo.option.ConnectionUserName=hive
javax.jdo.option.ConnectionPassword=...

# 3. 初始化 Schema
schematool -dbType postgres -initSchema

# 4. 调优
shared_buffers = 8GB
work_mem = 64MB
max_connections = 500
```

## 四、PG 作为轻量数仓（替代过早上 Hadoop）

### 适用场景

```
✅ 数据量 < 1TB
✅ 单机内存 64-512GB
✅ 查询并发 < 100
✅ 团队规模小，运维简化
✅ HTAP 混合（既要事务也要分析）

不适用:
  ❌ 数据 > 10TB（用 Citus 或换 CH/Doris）
  ❌ 高并发 BI 千 QPS
  ❌ 极致 OLAP 性能
```

### 数仓建模

```sql
-- 维度建模（星型）
CREATE TABLE dim_user (
  user_id BIGINT PRIMARY KEY,
  user_name TEXT,
  country TEXT,
  signup_date DATE,
  is_vip BOOLEAN,
  attrs JSONB
);

-- 事实表 + 分区（按月）
CREATE TABLE fact_orders (
  order_id BIGINT,
  user_id BIGINT,
  product_id BIGINT,
  amount NUMERIC(12,2),
  status SMALLINT,
  order_time TIMESTAMPTZ NOT NULL
) PARTITION BY RANGE (order_time);

-- 自动分区（pg_partman）
SELECT partman.create_parent(
  p_parent_table => 'public.fact_orders',
  p_control => 'order_time',
  p_type => 'native',
  p_interval => '1 month',
  p_premake => 6
);

-- 物化视图（BI 报表预聚合）
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT date_trunc('day', order_time) AS dt,
       sum(amount) AS revenue,
       count(*) AS orders
FROM fact_orders
GROUP BY 1;

CREATE UNIQUE INDEX ON mv_daily_sales (dt);

REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales;
```

### 列存加速（pg_duckdb / hydra）

```sql
-- pg_duckdb（PG 内嵌 DuckDB）
CREATE EXTENSION pg_duckdb;

-- 直查 Parquet
SELECT * FROM read_parquet('s3://bucket/data/*.parquet')
WHERE event_date = '2026-06-22';

-- Hydra (column store)
CREATE TABLE events_cstore (...) USING columnar;
```

## 五、Citus（分布式 PG 数仓）

### 架构

```
            ┌──── Coordinator (单/HA) ────┐
                  ↓ 分布式查询
   ┌──────┬──────┴──────┬──────┐
   ↓      ↓             ↓      ↓
 Worker1 Worker2  ...  WorkerN

  每个 Worker:
    - 独立 PG 实例
    - 分片 (shard) 存于本地
```

### 分布式表设计

```sql
-- 启用扩展
CREATE EXTENSION citus;

-- 添加 Worker
SELECT * from master_add_node('worker1', 5432);

-- 分布式表（按用户 ID 分片）
CREATE TABLE events (
  event_id BIGSERIAL,
  user_id BIGINT NOT NULL,
  event_time TIMESTAMPTZ,
  data JSONB
);
SELECT create_distributed_table('events', 'user_id');

-- 引用表（小维度表，所有 Worker 都有副本）
CREATE TABLE dim_country (country_code TEXT PRIMARY KEY, country_name TEXT);
SELECT create_reference_table('dim_country');

-- 共置 JOIN（同分片字段的多表）
SELECT create_distributed_table('orders', 'user_id', colocate_with => 'events');
```

### 适用规模

```
Citus 上限:
  - 总数据 10TB - 100TB
  - 节点数 10-100
  - 单分片 5-50GB
  
超出: 用 Greenplum / 换 ClickHouse / Doris
```

## 六、TimescaleDB（时序数据库扩展）

```sql
CREATE EXTENSION timescaledb;

-- 普通 PG 表 → Hypertable
CREATE TABLE metrics (
  ts TIMESTAMPTZ NOT NULL,
  service TEXT NOT NULL,
  metric TEXT NOT NULL,
  value DOUBLE PRECISION,
  labels JSONB
);

SELECT create_hypertable('metrics', 'ts', chunk_time_interval => INTERVAL '1 day');

-- 数据保留策略
SELECT add_retention_policy('metrics', INTERVAL '90 days');

-- 连续聚合（自动维护汇总）
CREATE MATERIALIZED VIEW metrics_5m
WITH (timescaledb.continuous) AS
SELECT time_bucket('5 minutes', ts) AS bucket, service, metric,
       avg(value) AS avg_v, max(value) AS max_v
FROM metrics
GROUP BY 1, 2, 3;

SELECT add_continuous_aggregate_policy('metrics_5m',
  start_offset => INTERVAL '1 day',
  end_offset => INTERVAL '5 minutes',
  schedule_interval => INTERVAL '5 minutes');

-- 压缩（节省 90%+ 空间）
ALTER TABLE metrics SET (timescaledb.compress, timescaledb.compress_segmentby = 'service,metric');
SELECT add_compression_policy('metrics', INTERVAL '7 days');
```

### TimescaleDB vs 其他时序

| 维度 | TimescaleDB | InfluxDB | Prometheus | VictoriaMetrics | TDengine |
|:---|:---|:---|:---|:---|:---|
| SQL | ✅ 完整 | ❌ Flux | ❌ PromQL | ❌ PromQL+ | ✅ |
| 长期存储 | ✅ | ⚠️ | ❌ | ✅ | ✅ |
| 高基数 | 中 | 弱 | 弱 | 强 | 强 |
| PG 生态 | **✅** | ❌ | ❌ | ❌ | ❌ |
| 国产 | ❌ | ❌ | ❌ | ❌ | ✅ |

**经验**：监控指标 + 已有 PG → TimescaleDB；纯监控 → VictoriaMetrics；国产化 → TDengine。

## 七、pgvector（向量数据库 / RAG）

### 安装与建表

```sql
CREATE EXTENSION vector;

CREATE TABLE docs (
  id BIGSERIAL PRIMARY KEY,
  title TEXT,
  content TEXT,
  embedding VECTOR(1536)         -- OpenAI ada-002 维度
);

-- 索引（IVFFlat 适合中等规模、HNSW 适合大规模）
CREATE INDEX ON docs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- 或
CREATE INDEX ON docs USING hnsw (embedding vector_cosine_ops);
```

### 检索

```sql
-- 找最相似 5 条
SELECT id, title, 1 - (embedding <=> '[0.1, 0.2, ...]') AS similarity
FROM docs
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 5;

-- 混合检索（向量 + 全文）
SELECT * FROM docs
WHERE to_tsvector('english', content) @@ to_tsquery('AI')
ORDER BY embedding <=> $1
LIMIT 10;
```

### pgvector vs 专业向量库

| 维度 | pgvector | Milvus | Pinecone | Qdrant |
|:---|:---|:---|:---|:---|
| 部署 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 与关系数据混合 | **⭐⭐⭐⭐⭐** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 千万级以下 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 千万以上 | ⭐⭐⭐ | **⭐⭐⭐⭐⭐** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 国内主流 | **极高** | 高 | 不能用 | 中 |

**经验**：千万向量以下 + 已有 PG → pgvector 无脑选；亿级以上 → 专业向量库。

## 八、PG 作为 CDC 源头

```
WAL 逻辑解码:
  PG 主库 wal_level=logical
   ↓
  逻辑复制槽 (replication slot)
   ↓
  Debezium / wal2json / pglogical
   ↓
  Kafka → 下游消费

适用:
  - 同步到 ES / CH / 数据湖
  - 跨库实时同步
  - 业务事件流
```

### Debezium 配置

```json
{
  "name": "pg-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "pg-host",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "...",
    "database.dbname": "app",
    "plugin.name": "pgoutput",
    "slot.name": "debezium",
    "publication.name": "dbz_publication",
    "table.include.list": "public.orders,public.users",
    "topic.prefix": "app-cdc"
  }
}
```

**PG CDC 注意**：
- 必须 `wal_level=logical`
- 长期不消费的 slot 会撑爆磁盘（监控）
- 主备切换需要重建 slot
- 大事务延迟高

## 九、PG 作为元数据底座

### Airflow / DolphinScheduler

```ini
# Airflow
sql_alchemy_conn = postgresql+psycopg2://airflow:pwd@pg/airflow

# DolphinScheduler
spring.datasource.url=jdbc:postgresql://pg:5432/dolphinscheduler
```

### Atlas / DataHub / OpenMetadata

```
DataHub:
  PG (推荐) / MySQL 都行
  存:
    - 元数据（库/表/列）
    - 血缘关系
    - 标签/术语
    - 用户/团队

OpenMetadata:
  PG 默认后端，开箱即用
```

## 十、大数据栈中的 PG 部署最佳实践

### 10.1 高可用

```
方案: Patroni + etcd + HAProxy
  - 自动 failover
  - 同步/异步复制可选
  - 监控集成
  
K8s 部署: CloudNativePG (CNPG) CRD
  - 声明式部署
  - 自动备份/恢复
  - 滚动升级
  - Backup → S3
```

### 10.2 备份

```bash
# pgBackRest（推荐）
pgbackrest --stanza=main backup --type=full
pgbackrest --stanza=main backup --type=incr
pgbackrest --stanza=main backup --type=diff
pgbackrest --stanza=main restore

# 配置 S3
repo1-type=s3
repo1-s3-bucket=pg-backup
repo1-retention-full=7
```

### 10.3 监控

```
工具:
  - postgres_exporter + Prometheus + Grafana
  - pg_stat_statements + pgwatch2
  - PASH-Viewer (top SQL)
  
关键指标:
  - 连接数 / 慢查询 / TPS
  - WAL 写入量 / Replication Lag
  - Buffer / Cache Hit Ratio
  - Vacuum 状态 / Bloat
  - Replication Slot Lag
  - Disk Used
```

## 十一、PG 在 K8s

```
推荐: CloudNativePG (CNPG)
  apiVersion: postgresql.cnpg.io/v1
  kind: Cluster
  spec:
    instances: 3
    primaryUpdateStrategy: unsupervised
    storage:
      size: 1Ti
      storageClass: ssd
    backup:
      barmanObjectStore:
        destinationPath: s3://...
    monitoring:
      enablePodMonitor: true

  特性:
    ✅ 自动 failover + 故障转移
    ✅ 备份到 S3
    ✅ Pooler 内置（PgBouncer）
    ✅ Patroni 不需要单独装
```

## 十二、常见坑（大数据场景）

| 坑 | 建议 |
|:---|:---|
| **大量短连接** | 必装 PgBouncer |
| **VACUUM 不及时** | autovacuum 调优 + 监控死元组 |
| **大表 ALTER** | 拆步骤 / 在线工具 (pg_repack) |
| **slot 撑爆磁盘** | 监控 + 不用就 DROP |
| **Citus 跨分片 JOIN** | 共置字段对齐 |
| **TimescaleDB chunk 过多** | 调 chunk_time_interval |
| **pgvector 大向量插入慢** | 批量 + 关闭 autovacuum during load |
| **Replication Lag 高** | 同步副本 + 监控 |
| **shared_buffers 设错** | 物理内存 25% |
| **work_mem × connections OOM** | 总和 < 50% RAM |
| **WAL 满盘** | 监控 + archive_command |
| **统计信息过期** | ANALYZE 定期 |
| **CDC 不消费** | 业务侧 commit slot |

## 十三、PG vs 其他在大数据栈的定位

```
PG 在大数据栈中的定位:
  - 元数据底座（首选）
  - 轻量数仓（中小规模）
  - HTAP 起步
  - 向量库 + GIS + 时序（一站式）
  - CDC 源
  - Spark/Trino/Flink 跨源 JOIN 的"小表 / 维度表"来源

不是:
  ❌ PB 级大数据存储
  ❌ 高并发流处理
  ❌ 海量 OLAP 引擎
  ❌ 实时数仓主力
```

## 十四、国产化与同类

| 产品 | 厂商 | 兼容 PG | 说明 |
|:---|:---|:---|:---|
| **人大金仓 KingbaseES** | 人大金仓 | ✅ | 信创主力 |
| **openGauss / MogDB** | 华为 | 源自 PG 9.2 | 党政常用 |
| **海量 Vastbase** | 海量数据 | ✅ | 信创 |
| **瀚高 HighGo** | 瀚高 | ✅ | 信创 |
| **PolarDB-PG** | 阿里云 | ✅ | 云原生 |
| **AnalyticDB for PG** | 阿里云 | Citus 改造 | MPP 数仓 |
| **Hologres** | 阿里云 | PG 兼容 | 实时数仓 |
| **Greenplum** | VMware | ✅ | MPP 数仓鼻祖 |

## 十五、学习路径（大数据视角）

```
基础: PG 主流玩法 → 见中间件章节

大数据扩展:
  1. pgvector + RAG 实战
  2. TimescaleDB 时序入门
  3. PostGIS 地理空间
  4. PG 作 HMS 后端
  5. Citus 分布式扩展
  
HA 与运维:
  6. Patroni 高可用
  7. pgBackRest 备份
  8. CloudNativePG K8s 部署
  
CDC 与集成:
  9. WAL2JSON / Debezium → Kafka
  10. Spark/Trino JDBC 集成
  11. 与 Iceberg / Delta 元数据互通
```

## 十六、未来展望

```
1-2 年:
  - pgvector + RAG 继续爆发
  - CloudNativePG 在 K8s 成主流
  - 与数据湖元数据深度融合

3-5 年:
  - PG 取代 MySQL 成新建项目默认
  - 列存扩展（hydra/pg_duckdb）成熟
  - HTAP 一体化能力进一步增强

5 年+:
  - PG 成为"瑞士军刀型"数据库
  - 在大数据栈中成为元数据/小数仓/向量/时序的统一底座
```

> 📖 **核心判断**：PG 在大数据栈中**不与 ClickHouse/Spark/Hive 抢主线赛道**，而是吃下"元数据 + 小数仓 + 向量 + 时序 + GIS"的多面手生态位。**一套 PG 集群能替代过去的 MySQL HMS + InfluxDB + Milvus + PostGIS + 多个小数仓**，是中小团队的最佳选择。
