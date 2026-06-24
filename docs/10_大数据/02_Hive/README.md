# Hive

> "用 SQL 操作 HDFS"——Hive 让 PB 级数据分析门槛从写 MR 代码降到写 SELECT。**几乎所有离线数据仓库都跑着 Hive**。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2007 | Facebook 内部启动 Hive，解决日均 TB 级日志分析 |
| 2008 | 开源捐 Apache |
| 2010 | 0.5 GA，国内开始大规模使用 |
| 2013 | 0.13 引入 **Tez** 执行引擎（替代 MR） |
| 2016 | 2.0 LLAP（低延迟） |
| 2018 | 3.0 **ACID + Hive Streaming**、不再支持非 ACID |
| 2022 | 4.0 大版本，Iceberg 集成、外部表增强 |
| 2024 | **4.0.1 GA** 稳定版 |
| 2025 | Hive 与 Iceberg / Trino 深度融合 |

> ⚠️ **现状**：Hive 已是"老枪"，但**Hive Metastore (HMS) 仍是大数据栈元数据事实标准**——Spark/Trino/Flink/Presto/Doris 都用它。

## 二、Hive 是什么

```
"基于 Hadoop 的数据仓库工具"

定位:
  - SQL → MapReduce / Tez / Spark 翻译器
  - 元数据存储 (Metastore)
  - 表/分区/列管理
  - 用户/权限/审计

不是:
  ❌ 实时查询（最快 LLAP 也是秒级）
  ❌ OLTP 事务（ACID 是批 ACID）
  ❌ 单点查询（不擅长 KV）
```

## 三、核心组件

```
┌──────────── 客户端 ──────────────┐
│ Beeline / JDBC / Hue / ODBC      │
└──────────────┬───────────────────┘
               ↓
┌──────────── HiveServer2 ─────────┐
│  SQL 解析 / 编译 / 执行计划       │
│  权限校验                         │
└──────────────┬───────────────────┘
               ↓
┌──────────── Metastore (HMS) ─────┐
│  库/表/分区/列/统计/权限元数据    │
│  存 MySQL/PostgreSQL              │
└──────────────┬───────────────────┘
               ↓
┌──────────── 执行引擎 ─────────────┐
│  MapReduce (老) / Tez / Spark    │
└──────────────┬───────────────────┘
               ↓
┌──────────── 数据 ──────────────────┐
│  HDFS / S3 / OSS                  │
│  ORC / Parquet / TEXT / Iceberg   │
└────────────────────────────────────┘
```

### Hive Metastore（HMS）的特殊地位

```
HMS 已经成为"大数据元数据事实标准":
  - Spark SQL 用 HMS
  - Trino / Presto 用 HMS
  - Flink SQL 用 HMS
  - Doris / StarRocks 用 HMS
  - Iceberg / Hudi 兼容 HMS

→ 即使你不再用 Hive 跑 SQL，HMS 仍然必装
```

## 四、核心功能

```
1. HQL（类 SQL 方言）
2. 库/表/分区/桶（partitioning + bucketing）
3. 自定义函数 UDF / UDAF / UDTF
4. ACID 事务表（3.0+）
5. 物化视图 + 自动改写
6. LLAP（低延迟内存执行）
7. Iceberg / Delta / Hudi 集成（4.0+）
8. Ranger / Sentry 列级权限
9. Hive on Spark（推荐）
10. JDBC/ODBC 通用接入
```

## 五、表类型与存储格式

### 5.1 表类型

| 类型 | 说明 |
|:---|:---|
| **Managed Table（内部表）** | DROP 删数据 |
| **External Table（外部表）** | DROP 不删数据，推荐 |
| **Partitioned Table** | 按列分区，存为子目录 |
| **Bucketed Table** | 按 hash 分桶，存为文件 |
| **ACID Table** | 3.0+，事务表（INSERT/UPDATE/DELETE） |
| **Iceberg Table** | 4.0+，数据湖格式 |

### 5.2 存储格式

| 格式 | 特点 | 推荐 |
|:---|:---|:---:|
| TEXT | 原始文本 | 仅原始日志 |
| SequenceFile | 二进制 | ❌ 过时 |
| RCFile | 列存老 | ❌ 过时 |
| **ORC** | Hive 原生列存 + 内置索引 + ACID | ⭐⭐⭐⭐⭐ |
| **Parquet** | 跨引擎友好 + 高效 | ⭐⭐⭐⭐⭐ |
| Avro | Schema 演进 | ⭐⭐⭐ |

**经验**：
- Hive 原生 → **ORC**
- Spark / Trino / 跨引擎 → **Parquet**
- 数据湖 → **Iceberg/Delta/Hudi**（Parquet 底层）

## 六、使用场景

### ✅ 推荐

| 场景 | 说明 |
|:---|:---|
| **离线数仓 T+1 报表** | 经典战场 |
| **大批量 ETL** | Hive on Spark/Tez |
| **冷数据归档查询** | SQL 直查 HDFS |
| **元数据统一** | HMS 跨引擎共享 |
| **多租户 SQL 入口** | HiveServer2 + Ranger |
| **数据治理** | 与 Atlas + Ranger 集成 |

### ⚠️ 不推荐

- **实时查询** → Presto/Trino + Iceberg / StarRocks
- **OLTP** → MySQL / PG
- **复杂数据科学** → Spark / PySpark
- **流式入仓** → Flink + Iceberg / Hudi
- **新建云上项目** → 直接 Iceberg + Spark on K8s

## 七、Hive vs 其他 SQL 引擎

| 维度 | Hive | Spark SQL | Trino/Presto | Impala | Doris/StarRocks |
|:---|:---|:---|:---|:---|:---|
| 延迟 | 分钟-小时 | 秒-分钟 | **秒级** | **秒级** | **亚秒级** |
| 吞吐 | 大 | 极大 | 中 | 中 | 中 |
| ACID | ✅ 3.0+ | ✅ Delta/Iceberg | ❌ | ❌ | ✅ |
| 元数据 | HMS | HMS | HMS/Iceberg | HMS | HMS |
| 跨源查询 | 弱 | 强 | **极强** | 弱 | 弱 |
| 适合 | ETL 批 | ETL + 计算 | Adhoc | BI | BI / 实时 |

## 八、最佳实践

### 8.1 库表设计

```sql
-- 库
CREATE DATABASE dwd
COMMENT '明细层'
LOCATION 'hdfs://cluster/warehouse/dwd';

-- 分区表（强烈推荐）
CREATE EXTERNAL TABLE dwd.events (
    event_time TIMESTAMP,
    user_id BIGINT,
    event_type STRING,
    properties STRING
)
PARTITIONED BY (dt STRING, hour STRING)
STORED AS ORC
LOCATION 'hdfs://cluster/warehouse/dwd/events'
TBLPROPERTIES (
    'orc.compress' = 'ZSTD',
    'orc.bloom.filter.columns' = 'user_id,event_type',
    'orc.create.index' = 'true'
);

-- 分桶（小数据 + JOIN 优化）
CREATE TABLE dwd.users (...)
CLUSTERED BY (user_id) INTO 64 BUCKETS;
```

### 8.2 分区策略

```
✅ 时间分区: dt='2026-06-22' / hour='14'
✅ 业务+时间二级分区
✅ 每分区文件 128MB-1GB 最佳
✅ 单表分区数 < 10 万
❌ 不要按高基数列分区（如 user_id）
❌ 不要 N 层深度分区（≤ 3 层）
```

### 8.3 命名规范

```
库名:
  ods_<业务>           Operational Data Store
  dwd_<业务>           Detail（明细）
  dws_<业务>           Summary（汇总）
  ads_<业务>           Application Service（应用）
  dim_<域>             Dimension
  tmp                  临时

表名: <层><业务>_<对象>_<粒度>
  例: dwd_pay_order_di（每日增量）
       dws_user_active_md（每月度）

字段:
  id / user_id / event_time / dt / hour
  is_xxx (布尔)、cnt_xxx (计数)、amt_xxx (金额)
```

### 8.4 性能优化

```sql
-- 1. 开启向量化
SET hive.vectorized.execution.enabled=true;
SET hive.vectorized.execution.reduce.enabled=true;

-- 2. CBO（基于成本优化）
SET hive.cbo.enable=true;
SET hive.compute.query.using.stats=true;
SET hive.stats.fetch.column.stats=true;
SET hive.stats.fetch.partition.stats=true;

ANALYZE TABLE events PARTITION (dt='2026-06-22') COMPUTE STATISTICS;
ANALYZE TABLE events PARTITION (dt='2026-06-22') COMPUTE STATISTICS FOR COLUMNS;

-- 3. 动态分区
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.max.dynamic.partitions=10000;
SET hive.exec.max.dynamic.partitions.pernode=1000;

-- 4. Map Join（小表加载内存）
SET hive.auto.convert.join=true;
SET hive.auto.convert.join.noconditionalbinning.threshold=50000000;  -- 50M

-- 5. 数据倾斜
SET hive.optimize.skewjoin=true;
SET hive.skewjoin.key=100000;

-- 6. 压缩
SET hive.exec.compress.output=true;
SET mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.ZStandardCodec;
```

### 8.5 引擎选择

```
hive.execution.engine =
  mr        ❌ 老 MapReduce，慢，仅兼容
  tez       ⭐⭐⭐ Hortonworks 主推，已少
  spark     ⭐⭐⭐⭐⭐ 主流（Hive on Spark）
  spark-sql ⭐⭐⭐⭐⭐ 用 Spark SQL 直接跑 HQL（更快）
```

### 8.6 Hive on Spark vs Spark SQL

```
Hive on Spark:
  - Hive 解析 SQL，Spark 执行
  - 老 SQL 不改

Spark SQL:
  - 直接用 Spark 解析 + 执行
  - 性能更好（CBO/AQE 更强）
  - 推荐新作业用

→ 趋势: 越来越多团队用 Spark SQL 替代 Hive
→ HMS 仍保留作为元数据
```

### 8.7 ACID + Iceberg 现代化

```sql
-- 老 ACID（Hive 3.0 ORC + 事务）
CREATE TABLE events (...)
STORED AS ORC
TBLPROPERTIES('transactional'='true');

-- Iceberg（推荐新建）
CREATE TABLE events (...)
USING iceberg
PARTITIONED BY (days(event_time));

INSERT INTO events VALUES (...);
UPDATE events SET ... WHERE ...;
DELETE FROM events WHERE ...;
MERGE INTO target USING source ON ... WHEN MATCHED ...;
```

### 8.8 安全集成

```
认证: Kerberos
权限:
  - SQL 标准 GRANT/REVOKE
  - Ranger 集中策略（表/列/行级）
  - Sentry（老 Hortonworks/CDH）

审计:
  - Ranger Audit → Solr/ES/Kafka
  - HiveServer2 操作日志

数据屏蔽: Ranger Column Masking
```

### 8.9 多租户 HiveServer2 部署

```
拓扑:
  HiveServer2 (HS2) 多实例 + Nginx/HAProxy LB
  ZooKeeper Service Discovery
  Beeline / JDBC 客户端
  独立 HMS 集群（3 节点 + MySQL HA）

配置:
  hive.server2.support.dynamic.service.discovery=true
  hive.server2.zookeeper.namespace=hiveserver2
  hive.server2.thrift.max.worker.threads=500
```

## 九、运维命令速查

```bash
# Beeline
beeline -u "jdbc:hive2://hs2-host:10000/default;principal=hive/_HOST@REALM"

# HMS
schematool -dbType mysql -info
schematool -dbType mysql -upgradeSchema

# 元数据
SHOW DATABASES;
SHOW TABLES IN dwd;
DESCRIBE FORMATTED dwd.events;
SHOW PARTITIONS dwd.events;
MSCK REPAIR TABLE dwd.events;   -- 修复分区元数据

# 数据
SHOW CREATE TABLE dwd.events;
ANALYZE TABLE dwd.events COMPUTE STATISTICS;
INSERT OVERWRITE TABLE ... SELECT ...;

# 性能
EXPLAIN SELECT ...;
EXPLAIN EXTENDED SELECT ...;
EXPLAIN VECTORIZATION DETAIL SELECT ...;
```

## 十、常见坑

| 坑 | 建议 |
|:---|:---|
| **小文件爆炸** | 分区合理 + INSERT 后 ALTER TABLE CONCATENATE |
| **数据倾斜** | distribute by / 加盐 / map join |
| **MR 引擎慢** | 切 Spark / Tez |
| **统计信息过期** | 定期 ANALYZE |
| **分区过多** | 减少粒度或换 Iceberg |
| **MSCK REPAIR 慢** | 改用 Iceberg / 动态分区 |
| **Metastore 单点** | HMS 多实例 + MySQL HA |
| **MySQL HMS 慢** | 索引 + 升级 PG 或调优 |
| **TEXT 格式** | 改 ORC/Parquet |
| **未开 CBO** | 必开 + ANALYZE |
| **大文件 GROUP BY OOM** | 调 mapreduce.reduce.memory.mb |
| **跨集群 Hive** | Replication / Atlas |

## 十一、生态与工具

| 工具 | 用途 |
|:---|:---|
| **Beeline** | 官方 JDBC CLI |
| **Hue** | Web SQL IDE |
| **DBeaver / DataGrip** | 通用 GUI |
| **DolphinScheduler / Airflow** | 工作流调度 |
| **Atlas** | 数据血缘 / 元数据治理 |
| **Ranger** | 权限管控 |
| **Iceberg / Delta / Hudi** | 数据湖格式（与 Hive 集成） |
| **Hive Metastore as Service** | 独立 HMS 服务化 |
| **Waggle Dance** | HMS Proxy |

## 十二、监控指标

```
HiveServer2:
  ActiveSessions / OpenOperations
  AvgRPCTime
  GC / Heap
  Failed queries rate

Metastore:
  RPC time
  GetTable / GetPartitions QPS
  DB connection pool

底层 MySQL:
  慢查询、连接数、锁

工具:
  Prometheus + jmx_exporter
  Cloudera Manager / Ambari
```

## 十三、迁移到现代栈

```
现代化路径:
  Hive → Spark SQL on K8s + Iceberg + S3

迁移要点:
  1. 表迁移:
     - 内部表先转外部表
     - 数据格式 ORC → Parquet（如果跨引擎）
     - 注册到 Iceberg / Hudi 表
  
  2. SQL 兼容:
     - 多数 HQL 在 Spark SQL 直接跑
     - UDF 需要重写为 Spark UDF
     - 部分语法差异（如 LATERAL VIEW）
  
  3. 元数据:
     - HMS 继续用（兼容 Spark/Trino/Flink）
     - 或换 Polaris / Unity Catalog
  
  4. 调度:
     - Oozie → Airflow / DolphinScheduler

工具:
  - hive-iceberg 迁移
  - SQL 改写工具（Trino-Hive 兼容层）
```

## 十四、Hive 4 新特性

```
✅ Iceberg 表原生支持
✅ Materialized View 与 Iceberg 自动改写
✅ Branch / Tag（Iceberg）
✅ 兼容 ANSI SQL 子集增强
✅ HBase Snapshot 表
✅ Tez UI 简化
✅ HMS HA 增强
✅ Calcite CBO 升级
```

## 十五、国产替代 / 同类

| 产品 | 厂商 |
|:---|:---|
| **MaxCompute (ODPS)** | 阿里云 |
| **DLI** | 华为云 |
| **TencentDB-DWS** | 腾讯云 |
| **EMR Hive** | 各家云 |
| **TDH Inceptor** | 星环科技 |
| **DataWorks** | 阿里云数据开发 |
| **OceanBase 数据仓库** | 蚂蚁 |

## 十六、学习路径

```
入门:
  1. 单机 Hive + MySQL HMS
  2. Beeline 跑 SELECT
  3. 分区表 + ORC 体验

进阶:
  4. ETL 全流程（ods → dwd → dws → ads）
  5. 性能优化（CBO / Map Join / 倾斜）
  6. HiveServer2 多实例 + LB
  7. Ranger 权限 + Atlas 血缘
  8. Hive on Spark / Spark SQL 替代

高阶:
  9. ACID 事务表实战
  10. Iceberg 集成 + 迁移
  11. HMS HA + Service Discovery
  12. 跨集群复制
  13. 元数据治理（DataWorks 自研化）
```

## 十七、未来展望

```
短期 (1-2 年):
  - HMS 仍是元数据事实标准
  - Hive 4 在私有化场景普及
  - Iceberg/Delta 与 Hive 表共存

中期 (2-5 年):
  - Hive 计算引擎被 Spark SQL 完全取代
  - HMS 可能被 Polaris / Unity / Nessus 挑战
  - Lakehouse 一统天下

长期 (5 年+):
  - Hive 项目可能停止演进
  - HMS 仍可能以独立项目存在
  - 数据仓库 → 数据湖仓
```

> 📖 **核心判断**：作为运维要分清——**Hive ≈ HQL + HMS**。HQL 这层已经被 Spark SQL 取代；HMS 这层仍是大数据元数据底座短期不会换。所以"Hive 没死，只是退到幕后了"。私有化数仓继续用，新建场景直接 Iceberg + Spark SQL。
