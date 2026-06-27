# 高级

> 大数据高级 = **湖仓一体架构(Lakehouse) + 数据网格(Data Mesh) + 流批一体深度(Paimon+Flink) + 多源 ETL/ELT 平台 + 实时数据中台 + 数据治理(DataHub+OpenMetadata+Marquez) + 数据契约(Data Contracts) + 数据产品化 + 大规模 Spark/Flink 内核调优 + Trino/StarRocks 联邦查询 + MLOps 上的特征工程(Feast) + 实时特征 + 多云数据移动 + 数据安全(脱敏+加密+审计) + 国密+等保 + 国产数据湖栈(Paimon/Doris) + AI Native 数据栈(LLM+Embedding+RAG)**。本章面向数据架构师 / 数据平台负责人。

## 一、湖仓一体（Lakehouse）

```
核心理念:
  - 一份数据 (对象存储 + Iceberg/Paimon)
  - 多引擎 (Spark/Flink/Trino/Doris/StarRocks)
  - ACID + Schema Evolution + Time Travel
  - 替代 Hadoop + 数据仓库 双层

参考:
  Databricks Lakehouse
  Snowflake (近似)
  阿里 EMR + DLF
  字节 LAS (Lakehouse Analytics)
  华为 LakeFormation

国产 OSS 栈:
  Paimon ⭐ (流批一体)
  Doris External Catalog
  StarRocks External Catalog
  Trino + Iceberg
```

## 二、数据网格（Data Mesh）

```
4 个核心原则 (Zhamak Dehghani):
  1. Domain Ownership      业务域所有权
  2. Data as a Product     数据即产品 ⭐
  3. Self-Serve Platform   平台自服务
  4. Federated Governance  联邦治理

实施:
  - 每个 Domain 团队负责自己数据资产
  - 提供 SLA / 文档 / 监控
  - 平台团队提供 Lakehouse + DataHub + 调度
  - 全局元数据/血缘/质量统一

工具:
  Backstage 数据插件 ⭐
  DataHub Domain Authorization
  dbt + DataHub + Soda
  Iceberg Catalog 命名空间

适合:
  - 大企业 (500+ 工程师)
  - 多业务域 (电商 + 金融 + 物流)
  - 中央 IT 团队改革
```

## 三、流批一体深度（Paimon + Flink）

### 3.1 Paimon 表类型

```
主键表 (Primary Key Table):
  - LSM-Tree
  - 实时 upsert
  - merge-engine: deduplicate / partial-update / aggregation / first-row
  - changelog-producer: input / lookup / full-compaction
  
追加表 (Append-Only Table):
  - 不可变
  - 类 Iceberg 日志事件
  
分区表:
  - PARTITIONED BY (dt)
  - 流式 + 批读
```

### 3.2 部分列更新 (partial-update)

```sql
CREATE TABLE user_features (
  user_id BIGINT PRIMARY KEY NOT ENFORCED,
  -- 来自订单流
  total_orders BIGINT,
  total_amount DECIMAL(20,2),
  -- 来自行为流
  last_login TIMESTAMP(3),
  click_count BIGINT
)
WITH (
  'merge-engine' = 'partial-update',
  'fields.total_orders.sequence-group' = 'order_ts',
  'fields.click_count.sequence-group' = 'click_ts'
);

-- 流 1 只更新订单字段
INSERT INTO user_features (user_id, total_orders, total_amount, order_ts)
SELECT user_id, COUNT(*), SUM(amount), MAX(ts) FROM orders_stream GROUP BY user_id;

-- 流 2 只更新行为字段
INSERT INTO user_features (user_id, last_login, click_count, click_ts)
SELECT user_id, MAX(ts), COUNT(*), MAX(ts) FROM clicks_stream GROUP BY user_id;
```

### 3.3 Paimon CDC 入湖

```sql
-- 整库 CDC 入湖
EXECUTE STATEMENT SET
BEGIN
INSERT INTO paimon.ods.users SELECT * FROM mysql.app.users;
INSERT INTO paimon.ods.orders SELECT * FROM mysql.app.orders;
INSERT INTO paimon.ods.items SELECT * FROM mysql.app.items;
END;
```

### 3.4 流批一体 ETL 链路

```
Kafka (CDC) → Flink → Paimon ODS
                      ↓ stream read
                    Flink Aggregate
                      ↓
                    Paimon DWS
                      ↓
              Doris / StarRocks 加速查询
                      ↓
                    Superset / BI

历史回刷 (Backfill):
  Paimon Snapshot / Tag → Spark 批读 → 重算 → 写回
```

## 四、Spark 内核与调优

### 4.1 内核要点

```
Catalyst Optimizer:
  Analyzer → Optimizer → Planner → CodeGen
  RBO + CBO + AQE

Tungsten:
  Off-heap memory
  Cache-friendly binary 格式
  Code Generation

Shuffle:
  Sort-based (默认)
  Bypass (无 Map 端聚合)
  Tungsten-Sort (列优化)
  RSS (Celeborn / Magnet)
  
AQE (Spark 3.x ⭐):
  动态合并小分区
  动态调整 Join 策略
  动态处理倾斜
```

### 4.2 调优进阶

```
读优化:
  - 列剪裁 + 谓词下推
  - Iceberg Bloom Filter Index
  - 分区过滤 + Z-Order (Iceberg)
  - Parquet Page Index
  
JOIN 优化:
  - Broadcast 小表 (autoBroadcastJoinThreshold)
  - Sort-Merge Join 大表
  - Bucket Join (预分桶)
  - DynamicPartitionPruning (AQE)
  
Shuffle 优化:
  - Celeborn / Magnet (RSS)
  - shuffle.partitions = vcore × 2-3
  - 压缩 lz4 / zstd
  - Skew Join (AQE)
  
内存:
  - executor 内存 = on-heap + off-heap
  - storage / execution 动态共享 (Unified)
  - off-heap 大 (减 GC)
  
GC:
  - G1GC (默认)
  - 大堆 ZGC (Java 17+)
```

## 五、Flink 内核与调优

### 5.1 内核要点

```
Stream API → JobGraph → ExecutionGraph

State:
  Operator State (并行实例 state)
  Keyed State (按 key state)
  
State Backend:
  Hashmap (内存, 默认)
  RocksDB ⭐ (持久化, 大状态)
  
Checkpoint:
  Barrier alignment / unaligned
  Incremental (RocksDB)
  
Time:
  EventTime / ProcessingTime / IngestionTime
  Watermark + 空闲处理
  
EXACTLY_ONCE:
  Checkpoint + 幂等 sink
  Two-Phase Commit Sink
```

### 5.2 调优进阶

```
Checkpoint:
  - Incremental RocksDB (减 size)
  - Unaligned Checkpoint (反压时不阻塞)
  - 异步快照
  - S3 多线程 + multi-part
  
反压:
  - Sink 慢 → 异步 IO / 增并行
  - Shuffle 慢 → 网络 buffer 调
  - Source 不均 → 加 rebalance
  - Watermark 滞后 → 重设
  
状态:
  - TTL 自动过期
  - RocksDB Block Cache 调
  - 分层存储 (RocksDB + S3)
  - 状态分桶 (Keyed)
  
SQL:
  - mini-batch 聚合
  - local-global 聚合 (减热点)
  - 异步维表 JOIN
  - Lookup Join + Cache
```

## 六、Trino / StarRocks 联邦查询

### 6.1 Trino 架构

```
组件:
  Coordinator     SQL 解析 + 计划 + 调度
  Worker          执行
  Catalog         数据源 (Hive/Iceberg/PG/MySQL/ES/Cassandra/...)
  
特性:
  - MPP 分布式
  - 内存执行 (大数据 spill 到盘)
  - 标准 SQL
  - 联邦 (跨源 JOIN)
```

### 6.2 StarRocks External Catalog

```sql
-- 注册多源
CREATE EXTERNAL CATALOG hive_cat PROPERTIES (
  "type" = "hive",
  "hive.metastore.uris" = "thrift://hms:9083"
);
CREATE EXTERNAL CATALOG iceberg_cat PROPERTIES (
  "type" = "iceberg",
  "iceberg.catalog.type" = "hms",
  "hive.metastore.uris" = "thrift://hms:9083"
);
CREATE EXTERNAL CATALOG paimon_cat PROPERTIES (
  "type" = "paimon",
  "paimon.catalog.type" = "filesystem",
  "paimon.warehouse" = "s3://bucket/paimon"
);

-- 跨源 JOIN
SELECT o.id, o.amount, u.name
FROM paimon_cat.ods.orders o
JOIN iceberg_cat.dim.users u ON o.user_id = u.id
WHERE o.dt = '2026-06-27';
```

### 6.3 Trino vs StarRocks 选型

| 场景 | 推荐 |
|:---|:---|
| **跨源 BI / Ad-hoc** | Trino ⭐ |
| **实时数仓 + 联邦** | StarRocks ⭐ |
| **国产 + 数据湖 + 高并发** | Doris / StarRocks |
| **超大集群 (1000+ 节点)** | Trino |

## 七、特征工程（Feast / 国产）

```
Feast ⭐:
  - Apache 2.0
  - Online (Redis/DynamoDB) + Offline (Snowflake/BigQuery/Iceberg)
  - Python API
  
其他:
  Feathr (LinkedIn)
  Tecton (商业)
  阿里 PAI Featurestore
  字节 LasV / Featurestore (内部)

适合:
  - ML 团队
  - 在线推理 + 离线训练 一致性
  - 与 Spark/Flink/Snowflake 集成
```

```python
# Feast 实战
from feast import FeatureStore, Entity, FeatureView, Field
from feast.types import Float32, Int64

store = FeatureStore(repo_path=".")

# 注册实体
user = Entity(name="user_id", value_type=ValueType.INT64)

# 离线 (Iceberg)
user_features = FeatureView(
    name="user_features",
    entities=[user],
    schema=[Field(name="total_orders", dtype=Int64), Field(name="avg_amount", dtype=Float32)],
    source=IcebergSource(table="ml.user_features"),
    online=True,   # 推送到 Redis
)

# 训练
training_df = store.get_historical_features(
    entity_df=labels_df,
    features=["user_features:total_orders", "user_features:avg_amount"],
).to_df()

# 推理
features = store.get_online_features(
    features=["user_features:total_orders", "user_features:avg_amount"],
    entity_rows=[{"user_id": 100}],
).to_dict()
```

## 八、数据治理（高级）

### 8.1 DataHub 高级

```
Domain & Glossary:
  - 业务域 (订单 / 用户 / 商品)
  - 业务术语 (GMV / DAU / 客单价)
  
Lineage:
  - 表级 + 列级 + DAG
  - 自动: Spark, Flink, dbt, Airflow, Iceberg
  
SLA / Tags / Ownership:
  - SLO 监控 (新鲜度)
  - 弃用标记
  - Steward / Owner 团队归属

DataHub Actions:
  - 事件驱动 (新增字段 → 通知)
  - 与 Kyverno / Slack / 钉钉 集成
```

### 8.2 OpenMetadata / Marquez

```
OpenMetadata ⭐:
  - 现代 (高 UI)
  - 内置数据质量
  - Atlas / DataHub 替代
  
Marquez:
  - OpenLineage 标准的实现
  - 简单 / 调度血缘
```

### 8.3 数据契约（Data Contracts）

```
理念:
  数据生产者承诺 Schema / SLA / Quality
  消费者依赖契约 (类似 API 合同)
  
工具:
  Conduktor / Lighthouse / DataContract.com
  自研 YAML 契约 + CI 验证
  
契约内容:
  ☐ Schema (字段 + 类型 + nullable)
  ☐ 主键 / 唯一键
  ☐ 业务规则 (amount > 0)
  ☐ SLA (新鲜度 / 完整性)
  ☐ Owner / Steward
  ☐ 变更通知 (Slack / 邮件)

实施:
  CI 内 schema check
  Iceberg + dbt + DataHub 自动
```

### 8.4 数据质量进阶

```
Great Expectations:
  ExpectationSuite (一组规则)
  Checkpoint (定期跑)
  Data Docs (HTML 报告)
  
Soda:
  SodaCL (YAML DSL) ⭐
  Soda Core / Soda Cloud
  与 Slack / 钉钉 告警
  
dbt tests:
  built-in (unique/not_null/relationship/accepted_values)
  dbt-expectations 扩展

度量:
  数据新鲜度 (Freshness)
  完整性 (Completeness)
  唯一性 (Uniqueness)
  一致性 (Consistency)
  有效性 (Validity)
  准确性 (Accuracy)
```

## 九、AI Native 数据栈

```
LLM + 数据栈融合:
  
1. Text-to-SQL:
   - Vanna AI / WrenAI ⭐
   - SQLCoder / DeepSeek-Coder
   - 国产: 通义千问 SQL / 文心 / 智谱
   
2. RAG + 数据:
   - LlamaIndex + Iceberg/Paimon 
   - 业务问答 → 自动查数据
   
3. AI 自动建模:
   - LLM 推荐 Schema / 索引 / 分区
   - dbt + Cursor / Copilot
   
4. Embedding 大数据:
   - Spark UDF + 文本 embedding
   - 千万级文本入 Milvus / pgvector
   
5. 智能数据治理:
   - 自动血缘解读
   - 自动业务术语建议
   - 自动数据质量规则

工具:
  Databricks DBRX / Genie ⭐
  Snowflake Cortex
  PostgresML / Pgvector
  LangChain SQL Agent
  DataHub AI Tags
```

## 十、多云数据移动

### 10.1 数据复制

```
对象存储:
  S3 → S3 (Replication)
  AWS DataSync / GCP Transfer / Azure Sync
  阿里 OSS 跨 region 复制
  
数据湖:
  Iceberg Replication (Polaris)
  Paimon DataStream
  Snowflake Replication
  
DB:
  Debezium / Flink CDC → Kafka → 多目的地
  阿里 DTS / 腾讯 DTS

ETL:
  Airbyte ⭐ (云原生)
  Fivetran (商业)
  SeaTunnel ⭐ (国产)
```

### 10.2 跨云架构

```
活动 - 备份 (DR):
  主集群 (阿里) + 备集群 (腾讯)
  双向 / 单向 CDC
  RTO < 4h, RPO < 1h

双活:
  按 user_id 路由
  CDC 反向同步
  最终一致

混合云:
  本地核心 + 云上弹性 (Spark on 公有云)
  对象存储跨云 (MinIO + 公有云 S3 网关)
```

## 十一、数据安全

```
脱敏:
  动态: Trino / StarRocks Policy + LDAP 角色
  静态: ETL 时 mask (regex / hash / fpe)
  Apache Ranger / Privacera
  
加密:
  传输 TLS (国密 SM2)
  存储 (S3 SSE / Iceberg KMS-encrypted / 国密)
  字段级 (列加密 + KMS)
  
审计:
  操作日志 → Loki / SIEM 180 天
  慢查询 / 大查询 告警
  双人审 (DROP / DELETE / 全表)
  
权限:
  RBAC / ABAC
  Trino Access Control
  Iceberg + Polaris/Nessie 权限
  Spark Row/Column Level (Ranger)
  Hive / Doris 行列权限

合规:
  ☐ 等保三级
  ☐ 国测中心
  ☐ 国密 SM2/3/4
  ☐ 数据安全法 + 个保法
  ☐ GDPR (出境)
  ☐ 数据出境评估
```

## 十二、国产化路径

```
计算:        Spark + Flink (开源)
湖仓:        Paimon ⭐ (国产 Apache)
实时数仓:    Doris ⭐ / StarRocks ⭐ (国产)
即席:        Trino + Doris External Catalog
调度:        DolphinScheduler ⭐ (国产 Apache)
采集:        SeaTunnel ⭐ (国产 Apache) + Flink CDC
血缘/治理:   DataHub / OpenMetadata
质量:        Soda + Great Expectations
对象存储:    MinIO ⭐ / Ceph RGW / 阿里 OSS / 华为 OBS
元数据:      Hive Metastore (老) + Polaris / Nessie (新)
BI:          Superset + FineBI ⭐ + Quick BI ⭐
平台:        自研 + Backstage 数据插件
信创 K8s:    KubeSphere / 华为 CCE
信创 OS:     openEuler / 麒麟
信创 CPU:    鲲鹏 / 飞腾 / 海光
国密:        Tongsuo + SM2/3/4
合规:        等保三级 + 国测中心 + 国密 + 数据安全法
```

## 十三、典型坑（高级）

| 坑 | 建议 |
|:---|:---|
| **Paimon 主键表 amplification** | bucket 数 + compaction 调 |
| **Iceberg 元数据膨胀 (snapshot 太多)** | expire_snapshots 周 + manifest rewrite |
| **Spark + AQE 调度倾斜** | shuffle.partitions + skew threshold |
| **Flink 反压链路定位** | Web UI + REST API + 异步 IO |
| **跨源 JOIN 性能** | Pre-aggregate + broadcast 小表 |
| **Doris BE 高负载** | replica_num + Compaction Score 监控 |
| **数据血缘 不全** | 接入 Spark/Flink listener + dbt + Airflow |
| **数据契约缺失** | YAML 契约 + CI 强制 |
| **跨地复制延迟** | 异步 + 多线程 + 多 Kafka partition |
| **AI Text-to-SQL 不准** | RAG + Schema 注入 + 少样本 |
| **DolphinScheduler 资源争抢** | Worker Pool per Team + Quota |
| **数据脱敏不严** | 多层 (静态 + 动态) + Ranger |

## 十四、Checklist（高级）

```
湖仓:
☐ Paimon / Iceberg 一种湖格式落地
☐ 维护任务 (rewrite/expire/orphan) 周调度
☐ Doris/StarRocks External Catalog 联邦
☐ 流批一体 (Flink + Paimon)

数据网格:
☐ Domain 团队所有权
☐ 数据产品化 (Backstage Catalog)
☐ 联邦治理 (DataHub Domain)

调优:
☐ Spark AQE + Celeborn + 动态分配
☐ Flink Application + Savepoint + Incremental
☐ Trino / StarRocks 联邦

治理:
☐ DataHub / OpenMetadata 血缘
☐ 数据契约 (YAML + CI)
☐ 数据质量 (Soda + Great Expectations)
☐ Ranger / Polaris 权限

特征工程:
☐ Feast / 自研 Feature Store
☐ 在线 (Redis) + 离线 (Iceberg/Paimon) 一致

AI Native:
☐ Text-to-SQL (Vanna/WrenAI)
☐ RAG + 业务问答
☐ LLM 辅助建模
☐ Embedding 大数据 → Milvus

多云:
☐ 对象存储复制 + Iceberg replication
☐ DTS / CDC 双活
☐ 灾备 RTO/RPO 量化

安全:
☐ Ranger / Polaris 行列权限
☐ 国密 + 字段加密
☐ 审计 → SIEM 180d
☐ 数据脱敏 (动态 + 静态)
☐ 等保三级 + 国测 + 国密

国产化:
☐ Paimon + Doris + DolphinScheduler + SeaTunnel
☐ 信创 K8s + OS + CPU
☐ FineBI / Quick BI 替代
```

## 十五、推荐栈（高级）

```
湖仓:        Paimon ⭐ + Iceberg + 对象存储 (MinIO/OSS)
实时数仓:    Doris ⭐ + StarRocks ⭐
即席:        Trino + StarRocks 联邦
计算:        Spark 3.5 + AQE + Celeborn + Flink 1.19 + Application Mode
CDC:        Flink CDC (Debezium) + Schema Registry
调度:        DolphinScheduler / Airflow + K8s Worker
采集:        SeaTunnel + Flink CDC
特征:        Feast + Redis + Paimon/Iceberg
血缘:        DataHub ⭐
质量:        Soda + Great Expectations
权限:        Apache Ranger + Polaris (现代)
AI Native:  Vanna / WrenAI + LangChain + Milvus
BI:          Superset + FineBI / Quick BI
平台:        Backstage 数据 IDP + 自研门户
监控:        kube-prometheus + Flink/Spark exporter
国密合规:   Tongsuo + 等保三级 + 国测
```

> 📖 **核心判断**：大数据高级 = **湖仓一体(Paimon/Iceberg) + 数据网格(Domain Ownership) + 流批一体(Flink+Paimon) + 实时数仓(Doris/StarRocks) + 内核调优(AQE/RSS/Incremental) + 联邦查询(Trino/StarRocks Catalog) + 特征(Feast) + 治理(DataHub+契约+质量) + AI Native(Text-to-SQL/RAG) + 多云+安全+国产化**。能给企业画"Kafka → Flink CDC → Paimon → Doris External Catalog → Trino → Superset/FineBI + DataHub 血缘 + Soda 质量 + Feast 特征 + AI Text-to-SQL + 国密合规"完整数据中台架构，就具备数据平台架构师能力。
