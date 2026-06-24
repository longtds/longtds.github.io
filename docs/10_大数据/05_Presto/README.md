# Presto / Trino

> 交互式 SQL 查询引擎之王。**不存数据，但能查任何地方的数据**——Hive、Iceberg、Kafka、MySQL、ES、Redis、S3……一条 SQL 跨源 JOIN，秒级响应。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2012 | Facebook 内部启动 Presto，替代 Hive 慢查询 |
| 2013.11 | 开源 |
| 2018 | 创始团队从 FB 出走 |
| 2019 | 创始团队 Fork 出 **PrestoSQL**（社区版） |
| 2020.12 | PrestoSQL **改名 Trino**（与 Facebook 撇清） |
| 2021+ | **Trino 社区繁荣**，PrestoDB（FB）继续独立演进 |
| 2024 | Trino 460+ 版本、统一 Catalog 标准 |
| 2024+ | Iceberg + Trino 成 Lakehouse 黄金搭档 |
| 2025 | Trino on K8s + Polaris Catalog 主流化 |

> ⚠️ **重要分裂**：现在主流是 **Trino**（社区活跃），**PrestoDB**（Facebook + Meta + Ahana 维护）仅在 Uber、字节等大厂用。**新建项目无脑选 Trino**。

## 二、Presto / Trino 是什么

```
"分布式 SQL 查询引擎"

核心定位:
  - 不存数据（无 Catalog 时连不上）
  - MPP 架构（大规模并行）
  - 内存计算 + 流水线
  - 秒级响应（交互式分析）
  - 跨数据源 JOIN（最大特色）

不是:
  ❌ 数据仓库（不存数据）
  ❌ ETL 引擎（用 Spark/Flink）
  ❌ 流处理（用 Flink）
  ❌ OLTP（不写）
```

## 三、架构原理

```
┌──────────────── Coordinator ────────────┐
│  解析 SQL / 计划 / 优化                  │
│  调度 Task                              │
│  收集结果                                │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────── Worker × N ─────────────┐
│  Source Stage (Scan)                    │
│  Intermediate Stage (Join/Agg)          │
│  Output Stage                           │
│                                          │
│  → 通过流水线传递数据（无落盘）          │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────── Connectors ─────────────┐
│ Hive / Iceberg / Delta / Hudi           │
│ MySQL / PostgreSQL / Oracle              │
│ Kafka / Pulsar                          │
│ ES / Cassandra / MongoDB                │
│ Redis / ClickHouse / Druid              │
│ JDBC / S3 / Kudu / GCS                  │
│ ...（50+ 个连接器）                      │
└─────────────────────────────────────────┘
```

### Catalog / Schema / Table

```
catalog.schema.table

例:
  hive.dwd.events
  iceberg.warehouse.user_action
  mysql.app.users
  
跨 catalog 直接 JOIN:
  SELECT u.name, o.amount
  FROM mysql.app.users u
  JOIN hive.dwd.orders o ON u.id = o.user_id
```

## 四、核心功能

```
1. ANSI SQL（窗口/CTE/递归/JOIN）
2. 50+ Connector（异构数据源）
3. 跨数据源 JOIN
4. 联邦查询（Federation）
5. MPP 并行执行
6. 流水线 + 内存计算
7. 动态过滤（Dynamic Filtering）
8. 物化视图 + 缓存
9. 资源组 + 队列
10. 安全（Kerberos、Ranger、LDAP、TLS）
11. Python / JDBC / CLI / REST
12. Spark Connector / DBT 集成
```

## 五、使用场景

### ✅ 完美匹配

| 场景 | 说明 |
|:---|:---|
| **Adhoc 查询** | 数据分析师/科学家用 |
| **BI 报表** | Tableau/Superset/Metabase 后端 |
| **跨源 JOIN** | MySQL + Hive 一条 SQL |
| **数据湖查询** | Iceberg/Delta/Hudi 上 SQL |
| **数仓 + 数据湖混合** | 跨 HMS + Iceberg |
| **联邦查询** | 不集中数据，直接查 |
| **替代 Hive on MR** | 同 SQL，秒级返回 |

### ⚠️ 不推荐

- **ETL（落表写）** → Spark / Flink
- **流处理** → Flink
- **超低延迟点查** → Redis / KV
- **超复杂 ML 处理** → Spark MLlib / Ray
- **重 UDF 计算** → Spark

## 六、Trino vs 其他

| 维度 | Trino | Spark SQL | Hive | Doris/StarRocks | ClickHouse |
|:---|:---|:---|:---|:---|:---|
| 延迟 | **秒级** | 秒-分钟 | 分钟-小时 | 亚秒级 | 亚秒级 |
| 吞吐 | 中 | 极大 | 极大 | 中 | 极大 |
| 跨源 | **⭐⭐⭐⭐⭐** | ⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ |
| ETL | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| SQL 完整 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 并发 | 中 | 中 | 低 | **极强** | 中 |
| Iceberg | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 适合 | **Adhoc/BI** | ETL | 老 ETL | BI 实时 | 单表 OLAP |

## 七、Presto vs Trino

| 维度 | Trino | PrestoDB |
|:---|:---|:---|
| 社区活跃 | **极活跃** | 弱（Meta 内部为主） |
| Catalog 数 | 50+ | 30+ |
| 新特性 | 快 | 慢 |
| Iceberg | **领先** | 跟随 |
| 国内主流 | **上升中** | 字节、Uber 还在用 |
| 选型 | **新建首选** | 老系统 |

## 八、最佳实践

### 8.1 集群规划

```
最小生产:
  1× Coordinator (无状态，关键路径)
  3+ × Worker（CPU/内存型，无状态）
  独立网络区域
  HMS / Iceberg Catalog 必备

硬件:
  Coordinator: 32C / 128GB
  Worker:      64C / 256GB / SSD
  网络:        10G+ / 25G+
  内存比 CPU 多（典型 4:1 ~ 8:1）
```

### 8.2 关键配置

```properties
# config.properties (Coordinator)
coordinator=true
node-scheduler.include-coordinator=false
http-server.http.port=8080
query.max-memory=200GB
query.max-memory-per-node=10GB
query.max-total-memory=400GB
query.max-execution-time=30m
discovery.uri=http://coordinator:8080

# Worker
coordinator=false
http-server.http.port=8080
query.max-memory-per-node=10GB
discovery.uri=http://coordinator:8080

# jvm.config（每节点）
-server
-Xmx100G
-XX:+UseG1GC
-XX:+ExplicitGCInvokesConcurrent
-XX:+HeapDumpOnOutOfMemoryError
-XX:+UseGCOverheadLimit
-XX:+ExitOnOutOfMemoryError
-XX:ReservedCodeCacheSize=512M
```

### 8.3 Catalog 配置

```properties
# etc/catalog/hive.properties
connector.name=hive
hive.metastore.uri=thrift://hms:9083
hive.allow-drop-table=true
hive.allow-rename-table=true
hive.parquet.use-column-names=true

# etc/catalog/iceberg.properties
connector.name=iceberg
iceberg.catalog.type=hive_metastore
hive.metastore.uri=thrift://hms:9083

# etc/catalog/mysql.properties
connector.name=mysql
connection-url=jdbc:mysql://mysql:3306
connection-user=trino_ro
connection-password=...
```

### 8.4 查询调优

```sql
-- 1. 查看执行计划
EXPLAIN (TYPE DISTRIBUTED) SELECT ...;
EXPLAIN ANALYZE SELECT ...;

-- 2. 提示
SELECT /*+ broadcast(b) */ * FROM a JOIN b ON ...;

-- 3. 分区裁剪
SELECT * FROM events WHERE dt = '2026-06-22';   -- 必加分区条件

-- 4. 动态过滤（自动）
SET SESSION enable_dynamic_filtering = true;

-- 5. 列裁剪（不写 SELECT *）
SELECT user_id, event FROM events;

-- 6. 谓词下推（Hive/Iceberg 自动）
```

### 8.5 资源组（Resource Groups）

```json
// etc/resource-groups.json
{
  "rootGroups": [
    {
      "name": "global",
      "softMemoryLimit": "80%",
      "hardConcurrencyLimit": 100,
      "maxQueued": 1000,
      "subGroups": [
        {
          "name": "etl",
          "softMemoryLimit": "60%",
          "hardConcurrencyLimit": 20,
          "schedulingPolicy": "weighted"
        },
        {
          "name": "adhoc",
          "softMemoryLimit": "40%",
          "hardConcurrencyLimit": 50
        }
      ]
    }
  ],
  "selectors": [
    {"user": "etl_.*", "group": "global.etl"},
    {"user": ".*", "group": "global.adhoc"}
  ]
}
```

### 8.6 安全

```
认证:
  - Kerberos（Hadoop 生态）
  - LDAP / OAuth / OIDC
  - 密码文件
  
传输:
  - TLS（HTTP/HTTPS）
  - 证书校验

授权:
  - Ranger（推荐，集中策略）
  - File-based access control
  - System-access-control

审计:
  - access-control 日志
  - Ranger audit
```

### 8.7 物化视图 / 缓存

```sql
-- Iceberg 物化视图
CREATE MATERIALIZED VIEW daily_events AS
SELECT dt, event, count(*) AS cnt
FROM hive.dwd.events
GROUP BY dt, event;

REFRESH MATERIALIZED VIEW daily_events;

-- Trino 内置缓存:
  - Metadata Cache
  - File List Cache
  - Result Cache (社区版部分)
```

### 8.8 Iceberg 集成（Lakehouse 黄金搭档）

```sql
-- 创建 Iceberg 表
CREATE TABLE iceberg.warehouse.events (
  event_time TIMESTAMP(6),
  user_id BIGINT,
  event STRING,
  properties MAP(VARCHAR, VARCHAR)
)
WITH (
  partitioning = ARRAY['day(event_time)'],
  format = 'PARQUET',
  format_version = 2
);

-- DML
INSERT INTO ...;
UPDATE ...;
DELETE FROM ... WHERE ...;
MERGE INTO target USING source ON ... WHEN MATCHED ...;

-- 时间旅行
SELECT * FROM events FOR TIMESTAMP AS OF TIMESTAMP '2026-06-20 00:00:00';
SELECT * FROM events FOR VERSION AS OF 12345;

-- 维护
ALTER TABLE events EXECUTE optimize;
ALTER TABLE events EXECUTE expire_snapshots(retention_threshold => '7d');
ALTER TABLE events EXECUTE remove_orphan_files();
```

## 九、Trino 在 K8s 部署

```yaml
# 用 Trino Helm Chart
helm repo add trino https://trinodb.github.io/charts/
helm install trino trino/trino \
  --set server.workers=10 \
  --set server.coordinator.jvm.maxHeapSize=64G \
  --set server.worker.jvm.maxHeapSize=128G \
  --set additionalCatalogs.hive="connector.name=hive\nhive.metastore.uri=..."
```

**优势**：
- HPA 弹性扩缩 Worker
- 与 S3 + Iceberg 完美配合
- Coordinator 单 Pod 无状态
- 高可用 = 多 Coordinator + Gateway

## 十、运维命令速查

```bash
# CLI
trino --server coordinator:8080 --catalog hive --schema default

trino> SHOW CATALOGS;
trino> SHOW SCHEMAS FROM hive;
trino> SHOW TABLES FROM hive.dwd;
trino> DESCRIBE hive.dwd.events;

# 系统表
SELECT * FROM system.runtime.queries WHERE state='RUNNING';
SELECT * FROM system.runtime.nodes;
SELECT * FROM system.metadata.catalogs;

# 性能
EXPLAIN ANALYZE SELECT ...;
SHOW STATS FOR hive.dwd.events;

# Web UI
http://coordinator:8080/ui/
  → 查询 / Worker / Cluster / 历史
```

## 十一、常见坑

| 坑 | 建议 |
|:---|:---|
| **Coordinator 单点** | 多 Coordinator + Gateway |
| **内存 OOM** | query.max-memory-per-node |
| **大表 JOIN 慢** | 调 join distribution + broadcast 提示 |
| **小文件多** | Iceberg 定期 optimize |
| **HMS 慢** | HMS HA + MySQL 调优 |
| **JDBC Connector 慢** | 谓词下推 + 分页 |
| **网络慢** | exchange 压缩开启 |
| **跨源 JOIN 慢** | 数据落本地 catalog |
| **K8s POD 漂移** | nodeAffinity + 资源声明 |
| **Catalog 配置不热加载** | 部分需重启 |
| **统计信息没用** | ANALYZE 或 Iceberg 自动 |
| **版本升级不平滑** | Worker/Coord 同版本 |

## 十二、生态与工具

| 工具 | 用途 |
|:---|:---|
| **Trino CLI** | 官方 CLI |
| **Trino JDBC / ODBC** | BI 接入 |
| **Apache Ranger** | 权限 |
| **Apache Atlas** | 血缘 |
| **DBeaver / DataGrip** | GUI |
| **Apache Superset** | BI |
| **Metabase** | BI |
| **Tabular / Polaris** | Iceberg Catalog |
| **dbt-trino** | 数仓建模 |
| **Trino Gateway** | 多 Coordinator 路由 |
| **Starburst** | Trino 商业版 |

## 十三、监控指标

```
查询:
  Running / Queued / Failed / Completed
  Wall time / CPU time
  Memory peak per query

集群:
  Worker count / heap usage
  Network IO / Cluster CPU

Connector:
  Hive/Iceberg metadata 命中率
  Split count

工具:
  Prometheus + JMX exporter
  Trino UI（自带）
  Grafana dashboard
  Starburst Galaxy Mission Control
```

## 十四、数据湖仓黄金组合

```
2025 Lakehouse 标准栈:
  存储:       S3 / OSS / MinIO
  格式:       Iceberg / Delta / Hudi（Parquet 底层）
  Catalog:    HMS / Polaris / Unity / Nessie
  写入:       Spark / Flink（ETL/流）
  查询:       Trino（Adhoc/BI）+ Spark SQL（重计算）
  调度:       Airflow / DolphinScheduler
  治理:       Atlas / DataHub
  BI:         Superset / Tableau / FineBI
```

## 十五、国产替代 / 同类

| 产品 | 厂商 | 说明 |
|:---|:---|:---|
| **MaxCompute SQL** | 阿里云 | 自研 SQL |
| **DLI** | 华为云 | 多引擎 SQL |
| **Apache Doris / StarRocks** | 百度/镜舟 | MPP 数仓 |
| **Apache Kyuubi** | 网易 | Spark SQL Gateway |
| **Apache Drill** | Apache | 类 Presto |
| **Dremio** | 商业 | Lakehouse 引擎 |

## 十六、Trino 何时不够用

```
继续用 Trino:
  ✅ Adhoc 探索 + BI
  ✅ 跨源 JOIN
  ✅ Iceberg/Delta Lakehouse 查询
  ✅ 数据科学家 SQL 入口

换其他:
  - 高并发 BI 报表 (千 QPS) → Doris / StarRocks
  - 大 ETL 写 → Spark
  - 流处理 → Flink
  - 单表大宽表极致性能 → ClickHouse
```

## 十七、学习路径

```
入门:
  1. 单机 Trino + Hive Catalog
  2. CLI 跑 SELECT
  3. 跨源 JOIN（Hive + MySQL）

中级:
  4. 3 节点集群（Coordinator + 2 Worker）
  5. Iceberg 集成 + 时间旅行
  6. 资源组 + 队列
  7. Ranger 权限

高级:
  8. K8s 部署 + 弹性扩缩
  9. 性能调优 + 大查询
  10. 物化视图 + 缓存
  11. 多 Coordinator + Gateway HA
  12. 国产替代评估
```

## 十八、未来展望

```
1-2 年:
  - Trino + Iceberg 成 Lakehouse 默认
  - K8s 上 Trino 弹性化普及
  - dbt + Trino 数仓建模标配

3-5 年:
  - SQL 引擎与计算引擎边界模糊
  - 多 Catalog 联邦标准化（REST Iceberg Catalog）
  - 与 Doris/StarRocks 并存（Adhoc vs BI）

5 年+:
  - 数据湖仓一体（Lakehouse）成主流
  - Trino 仍是开源 Adhoc 王者
```

> 📖 **核心判断**：**Adhoc + 跨源 + Lakehouse = 选 Trino**。新建项目无脑选 Trino（而不是 PrestoDB）。配合 Iceberg + S3，是 2025 大数据栈的标准答案。如果场景以高并发 BI 报表为主，Doris/StarRocks 才是更好的选择。
