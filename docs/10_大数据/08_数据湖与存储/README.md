# 数据湖与存储

> 数据湖 = **对象存储 + 开放表格式 + Catalog**。Iceberg / Delta / Hudi 三国杀重新定义了大数据存储，**Lakehouse（湖仓一体）成为 2025 新主流**。

## 一、来历与演进

| 年份 | 事件 |
|:---:|:---|
| 2010 | 数据湖概念由 Pentaho 创始人 James Dixon 提出 |
| 2015 | AWS S3 + Spark 普及，"原始数据湖"流行 |
| 2017 | Databricks 发布 **Delta Lake** |
| 2018 | Netflix 开源 **Apache Iceberg** |
| 2019 | Uber 开源 **Apache Hudi** |
| 2020 | "Lakehouse"概念由 Databricks 提出 |
| 2022 | Snowflake 拥抱 Iceberg、Tabular 创立 |
| 2024 | **Databricks 14 亿美元收购 Tabular**，Iceberg 与 Delta 走向统一 |
| 2024 | **Apache Polaris** Catalog 标准化运动开启 |
| 2025 | Iceberg 成为事实标准，Delta UniForm 双格式兼容 |

> ⚠️ **2024 行业大事件**：Databricks 收购 Tabular（Iceberg 创始团队），意味着 **Delta 和 Iceberg 走向兼容融合**，**Iceberg 协议层胜出**。

## 二、什么是数据湖 / Lakehouse

```
数据湖（Data Lake）:
  存任意原始数据（结构化/半结构化/非结构化）
  以对象存储为底（S3/HDFS/OSS）
  以开放格式存储（Parquet/ORC/Avro/CSV/JSON）
  Schema-on-Read（查时定义结构）

传统数据仓库（Data Warehouse）:
  结构化数据
  Schema-on-Write
  事务/ACID
  高性能 BI

Lakehouse（湖仓一体） = 数据湖 + 数据仓库:
  开放格式（Parquet）+ ACID 事务 + Schema
  廉价对象存储 + 数仓级查询性能
  → Iceberg / Delta / Hudi 三大开放表格式
```

## 三、四层架构

```
┌─────────────────────────────────────────────┐
│  应用层    BI / 数据科学 / ML / Dashboard    │
└────────────────────┬────────────────────────┘
                     ↓
┌─────────── 计算层（多引擎共存）────────────────┐
│ Spark / Flink / Trino / Doris / ClickHouse  │
└────────────────────┬────────────────────────┘
                     ↓
┌─────────── 表格式层 ─────────────────────────┐
│ Iceberg / Delta / Hudi                      │
│ → 元数据 + 事务 + 时间旅行 + Schema 演进     │
└────────────────────┬────────────────────────┘
                     ↓
┌─────────── 文件格式层 ───────────────────────┐
│ Parquet（列存）/ ORC / Avro                  │
└────────────────────┬────────────────────────┘
                     ↓
┌─────────── 存储层 ───────────────────────────┐
│ S3 / OSS / OBS / MinIO / HDFS / Ozone / GCS │
└─────────────────────────────────────────────┘
```

## 四、底层存储

### 4.1 对象存储（云原生主流）

| 类型 | 厂商 | 特点 |
|:---|:---|:---|
| **S3** | AWS | 行业标准，几乎所有引擎支持 S3A |
| **OSS** | 阿里云 | S3 兼容 |
| **OBS** | 华为云 | S3 兼容 |
| **COS** | 腾讯云 | S3 兼容 |
| **GCS** | Google | S3 兼容 |
| **Blob** | Azure | ABFS 协议 |
| **MinIO** | 开源 | S3 兼容，私有化首选 |
| **Ceph RGW** | 开源 | S3 兼容 |
| **JuiceFS** | 开源 | POSIX 兼容文件系统 over 对象 |

### 4.2 HDFS vs 对象存储

| 维度 | HDFS | 对象存储 |
|:---|:---|:---|
| 一致性 | 强 | 最终（部分强）|
| 延迟 | 低 | 中（首字节延迟） |
| 吞吐 | 高 | **极高** |
| 成本 | 高 | **低** |
| 弹性 | 差 | **极好** |
| 运维 | 重 | **轻** |
| 元数据 | 单点 NN | 分布式 |
| RENAME | 原子 | 慢/不原子 |
| Append | 弱 | 多版本 |
| 适合 | 私有化 | 云上 |

### 4.3 Apache Ozone（新一代）

```
Hadoop 社区为替代 HDFS 设计:
  ✅ 对象存储 + 文件系统 双模式
  ✅ 解决 HDFS 小文件
  ✅ S3 兼容 API
  ✅ 横向扩展百亿对象

定位: 私有化场景的"S3 替代品"
```

### 4.4 文件格式

| 格式 | 类型 | 推荐 |
|:---|:---|:---:|
| **Parquet** | 列存 | ⭐⭐⭐⭐⭐ **首选** |
| ORC | 列存 | ⭐⭐⭐⭐ Hive 偏好 |
| Avro | 行存 + Schema | ⭐⭐⭐ 流式 |
| JSON / CSV | 文本 | ⭐⭐ 原始数据 |
| **Lance** | 列存 + 向量 | ⭐⭐⭐ AI/ML 新势力 |

**结论**：**Parquet 是 2025 事实标准**（Iceberg/Delta/Hudi 都以 Parquet 为底）。

## 五、开放表格式三国杀（核心）

### 5.1 Iceberg

```
出身: Netflix 2018 开源
特点:
  - 隐式分区（Hidden Partitioning）
  - Schema/分区演进无锁
  - Snapshot 时间旅行
  - 元数据分层（Snapshot → Manifest → DataFile）
  - 多引擎良好支持
  - V2 行级 DELETE/UPDATE
  - Branch / Tag（Git 风格）

优势:
  ✅ 设计最新最干净
  ✅ 多引擎中立（Spark/Trino/Flink/Doris/CH 都好）
  ✅ Catalog 标准化（REST Catalog / Polaris）
  ✅ 2024 后行业事实标准

劣势:
  ⚠️ Streaming 写入相对弱
```

### 5.2 Delta Lake

```
出身: Databricks 2017 开源
特点:
  - 事务日志 (_delta_log)
  - 强 ACID + 乐观并发
  - Time Travel
  - Schema Evolution
  - Liquid Clustering（自动重组）
  - DML 性能极强
  - **UniForm**（与 Iceberg 双格式兼容，2.4+）

优势:
  ✅ Spark/Databricks 一等公民
  ✅ 性能优化最深
  ✅ 与 Photon 引擎深度整合

劣势:
  ⚠️ 非 Spark 引擎支持稍弱（虽然 UniForm 缓解）
  ⚠️ Databricks 主导带来"商业绑架"担忧
```

### 5.3 Hudi

```
出身: Uber 2017 开源
特点:
  - 两种存储模式: CoW / MoR
  - 内置 CDC（Change Capture）
  - 增量查询（incremental queries）
  - Clustering / Compaction 内置
  - Record-level Index
  - 强流处理基因

优势:
  ✅ 流式入湖 + CDC 最强
  ✅ Upsert / Delete 性能好
  ✅ 与 Kafka/Flink 配合
  ✅ 中国 Uber 系生态深

劣势:
  ⚠️ 设计偏复杂
  ⚠️ 多引擎支持不如 Iceberg
```

### 5.4 三者对比

| 维度 | Iceberg | Delta | Hudi |
|:---|:---|:---|:---|
| 出身 | Netflix | Databricks | Uber |
| 多引擎 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 流式入湖 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| ACID | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Schema 演进 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| CDC / 增量 | ⭐⭐⭐ | ⭐⭐⭐⭐ | **⭐⭐⭐⭐⭐** |
| 时间旅行 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 性能（Spark） | ⭐⭐⭐⭐ | **⭐⭐⭐⭐⭐** | ⭐⭐⭐⭐ |
| Catalog | REST / HMS / Polaris | Unity | HMS |
| 国内主流 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 商业支持 | Tabular(被 DB 收) | Databricks | Onehouse |

### 5.5 选型建议

```
新建项目 + 多引擎共存:    ✅ Iceberg
Databricks 客户:        ✅ Delta + UniForm
重流式入湖 + CDC:        ✅ Hudi
中国大厂常见组合:         Iceberg 为主，Hudi 为辅
最稳妥:                 Iceberg（行业事实标准）
```

## 六、Catalog（元数据管理）

```
Catalog 决定:
  - 表/库元数据存哪里
  - 如何被多引擎共享
  - 权限/认证如何接

主流 Catalog:
  1. Hive Metastore (HMS)    最经典，所有引擎兼容
  2. AWS Glue Catalog        AWS 默认
  3. Iceberg REST Catalog    新标准（多引擎）
  4. Apache Polaris          Snowflake 开源、Iceberg REST 实现
  5. Tabular (商业)           被 Databricks 收购
  6. Unity Catalog (Databricks) Delta 配套，开源化中
  7. Nessie                  Git 风格 Catalog（Dremio）
```

### Polaris（2024 新势力）

```
特点:
  ✅ Apache 2.0 开源
  ✅ Iceberg REST 协议
  ✅ 多租户 + RBAC
  ✅ Snowflake 主推
  ✅ 与 Trino/Spark/Flink 集成

定位: HMS 的"现代化继任者"
```

## 七、计算引擎与数据湖

| 引擎 | Iceberg | Delta | Hudi | 适合 |
|:---|:---:|:---:|:---:|:---|
| **Spark** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ETL |
| **Flink** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 流入湖 |
| **Trino/Presto** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Adhoc |
| **Doris** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | BI |
| **StarRocks** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | BI |
| **ClickHouse** | ⭐⭐⭐ (24.x+) | ⭐⭐ | ⭐⭐ | OLAP |
| **Databricks** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 商业 |
| **Snowflake** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 商业云 |

## 八、典型 Lakehouse 架构

```
┌─────────────────────────────────────────────────┐
│  CDC: Debezium → Kafka                          │
│  日志: Filebeat / Vector → Kafka                 │
│  业务: API → Kafka                              │
└────────────────────┬────────────────────────────┘
                     ↓
┌──────── 实时入湖 ────────────────────────────────┐
│  Flink + Iceberg/Hudi → S3                      │
│  Spark Streaming + Delta → S3                   │
└────────────────────┬────────────────────────────┘
                     ↓
┌──────── 数据湖 (S3 + Iceberg/Delta) ────────────┐
│  Bronze (原始)                                  │
│   ↓ Spark / Flink ETL                          │
│  Silver (清洗)                                  │
│   ↓ 维度建模                                   │
│  Gold (面向应用)                                │
└────────────────────┬────────────────────────────┘
                     ↓
┌──────── 查询服务 ────────────────────────────────┐
│  Trino    → Adhoc SQL                          │
│  Doris    → BI 报表                            │
│  ClickHouse → 实时 OLAP                        │
│  Spark SQL → ETL / 数据科学                    │
│  Flink SQL → 流式查询                          │
└─────────────────────────────────────────────────┘
```

## 九、最佳实践

### 9.1 表设计

```sql
-- Iceberg 标准建表
CREATE TABLE iceberg.warehouse.events (
  event_time TIMESTAMP,
  user_id BIGINT,
  event STRING,
  country STRING,
  amount DECIMAL(12,2),
  attrs MAP<STRING, STRING>
)
USING iceberg
PARTITIONED BY (days(event_time))  -- 隐式分区
TBLPROPERTIES (
  'format-version' = '2',
  'write.parquet.compression-codec' = 'zstd',
  'write.target-file-size-bytes' = '536870912',  -- 512MB
  'write.metadata.delete-after-commit.enabled' = 'true',
  'write.metadata.previous-versions-max' = '10'
);
```

### 9.2 文件大小调优

```
✅ 目标文件大小: 128MB - 1GB（推荐 256-512MB）
✅ 避免小文件（< 64MB）
✅ 定期 compaction:
   - Iceberg: rewrite_data_files
   - Delta: OPTIMIZE
   - Hudi: Clustering / Compaction

✅ 流式写后定期合并（每小时/每天）
```

### 9.3 分区策略

```
✅ 高基数列不要做分区列
✅ 时间分区: day/month
✅ Iceberg 隐式分区:
   PARTITIONED BY (days(event_time), bucket(16, user_id))

✅ 二级分区谨慎（深度 ≤ 2）
❌ 不要按 user_id 直接分区（基数太高）
```

### 9.4 元数据维护

```sql
-- Iceberg
ALTER TABLE events EXECUTE optimize;
ALTER TABLE events EXECUTE expire_snapshots(retention_threshold => '7d');
ALTER TABLE events EXECUTE remove_orphan_files();
ALTER TABLE events EXECUTE rewrite_manifests();

-- Delta
OPTIMIZE events;
VACUUM events RETAIN 168 HOURS;
DESCRIBE HISTORY events;
RESTORE TABLE events TO VERSION AS OF 123;

-- Hudi
CALL run_compaction(...);
CALL run_clustering(...);
CALL clean_archived_logs(...);
```

### 9.5 流式入湖

```python
# Spark Structured Streaming → Iceberg
(spark.readStream
   .format("kafka").option("kafka.bootstrap.servers", "...")
   .option("subscribe", "events").load()
   .selectExpr("CAST(value AS STRING) as json")
   .select(from_json(col("json"), schema).alias("data"))
   .select("data.*")
   .writeStream
   .format("iceberg")
   .outputMode("append")
   .option("path", "s3a://bucket/warehouse/events")
   .option("checkpointLocation", "s3a://bucket/ckpt/events")
   .trigger(processingTime='1 minute')
   .start())
```

### 9.6 时间旅行

```sql
-- Iceberg
SELECT * FROM events FOR TIMESTAMP AS OF '2026-06-22 00:00:00';
SELECT * FROM events FOR VERSION AS OF 1234567;

-- Delta
SELECT * FROM events TIMESTAMP AS OF '2026-06-22';
SELECT * FROM events VERSION AS OF 12;

-- Hudi
SET hoodie.datasource.read.read.commit.time=...;
```

### 9.7 数据治理

```
分层模型 (Medallion):
  Bronze: 原始数据，不删
  Silver: 清洗、去重、Schema 标准化
  Gold: 面向业务的宽表/聚合

权限:
  - Polaris / Ranger
  - 列级 / 行级 ACL
  - 数据脱敏

血缘:
  - DataHub / Atlas / OpenLineage
  - Spark/Flink 自动采集

质量:
  - Great Expectations
  - dbt-test
  - Deequ
```

## 十、私有化 / 国产化数据湖栈

### 10.1 私有化首选

```
存储:       MinIO / Ceph RGW / Ozone / 国产对象存储
表格式:     Iceberg
计算:       Spark on K8s / Flink on K8s
Catalog:    HMS + PostgreSQL 后端
查询:       Trino / Doris / StarRocks
调度:       Airflow / DolphinScheduler
治理:       OpenMetadata / Atlas
```

### 10.2 国产对象存储

| 产品 | 厂商 | 兼容 |
|:---|:---|:---|
| **OSS** | 阿里云 | S3 兼容 |
| **OBS** | 华为云 | S3 兼容 |
| **COS** | 腾讯云 | S3 兼容 |
| **EOS** | 京东云 | S3 兼容 |
| **MinIO** | 开源 | S3 兼容（私有化首选） |
| **Ceph RGW** | 开源 | S3 兼容 |
| **JuiceFS** | 国产开源 | POSIX over 对象 |
| **OceanFS** | 华为 | 文件 |

### 10.3 国产数据湖商业产品

| 产品 | 厂商 |
|:---|:---|
| **DLF (Data Lake Formation)** | 阿里云 |
| **DLI** | 华为云 |
| **EMR + Iceberg** | 各家云 |
| **Hashdata** | 中科院系 |
| **Tabular（国际，已被 DB 收）** | — |

## 十一、常见坑

| 坑 | 建议 |
|:---|:---|
| **小文件爆炸** | 定期 optimize/compaction |
| **S3 一致性问题** | 用支持强一致的 S3 / 用 Iceberg 解决 |
| **HMS 单点** | HMS HA + PG 后端 |
| **元数据过期** | snapshot/cleanup 定期 |
| **跨引擎不兼容** | Iceberg / Delta UniForm |
| **Hudi MoR 查询慢** | 切 CoW 或定期 compaction |
| **流入湖 Exactly-once** | Checkpoint + 幂等 |
| **Catalog 锁竞争** | REST Catalog 或分片 |
| **没有数据治理** | 加 DataHub/OpenMetadata |
| **没有血缘** | OpenLineage 集成 |
| **统计信息没用** | ANALYZE 或自动统计 |
| **跨可用区延迟** | 同区域部署 + 缓存 |
| **垃圾文件留存** | remove_orphan_files |

## 十二、监控

```
存储层:
  - S3 请求量 / 错误率
  - 数据增长曲线
  - 跨可用区流量

表格式:
  - 文件数 / 平均文件大小
  - Snapshot 数量
  - Compaction 状态

引擎:
  - Spark/Flink/Trino 各自监控

治理:
  - 表使用率
  - 冷热数据分布
```

## 十三、Lakehouse vs 传统数仓 vs 数据湖

```
传统数仓 (Snowflake/Teradata):
  ✅ 强 ACID / 性能极致
  ❌ 贵、封闭、扩展难
  
传统数据湖 (HDFS + Parquet):
  ✅ 廉价、灵活
  ❌ 无事务、Schema 漂移
  
Lakehouse (Iceberg/Delta + S3 + 多引擎):
  ✅ 开放、廉价、事务、Schema、多引擎
  ✅ 流批一体
  ✅ AI/ML 友好
```

## 十四、未来展望

```
1-2 年:
  - Iceberg 成事实标准
  - Delta UniForm 与 Iceberg 双格式互通
  - Polaris / REST Catalog 普及
  - 中国大厂 Lakehouse 落地完成

3-5 年:
  - Hudi 在流入湖场景守住地盘
  - 数据湖与 AI 平台融合（Lakehouse for AI）
  - 多模数据湖（结构化 + 向量 + 时序 + 图）
  - Lance 等新格式兴起

5 年+:
  - 数据湖统一存储成为云原生数据架构基石
  - 数据仓库不再是独立形态
  - 多引擎 + 一份数据成标配
```

## 十五、学习路径

```
入门:
  1. 理解对象存储 (S3/MinIO)
  2. Parquet 文件格式
  3. Iceberg 单机 + Spark 实战
  4. 时间旅行 + Schema 演进

中级:
  5. Trino + Iceberg + S3 Adhoc
  6. Spark + Iceberg ETL 全流程
  7. Flink + Hudi 流入湖
  8. HMS / Polaris 部署

高级:
  9. 三种表格式对比评估
  10. Catalog 选型 + 多引擎接入
  11. 数据治理（DataHub / OpenMetadata）
  12. Lakehouse 架构设计
  13. 国产化落地（MinIO + Iceberg + Trino + Doris）
```

> 📖 **核心判断**：**2025 大数据存储标准答案 = 对象存储 + Iceberg + 多引擎 + REST Catalog**。私有化首选 MinIO + Iceberg + Spark/Trino + HMS；云上首选 S3/OSS + Iceberg + Polaris + Trino/Spark。三大表格式中 **Iceberg 已成事实标准**，但 Delta 在 Databricks 客户中仍主流，Hudi 在流入湖场景守住地盘。
