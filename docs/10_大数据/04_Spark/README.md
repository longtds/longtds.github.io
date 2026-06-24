# Spark

> 内存计算时代的"统一引擎"。**批处理、流处理、SQL、机器学习、图计算——一套 API 全搞定**。Hadoop 第二代主流，云原生时代仍是大数据计算的事实标准。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2009 | Matei Zaharia 在 UC Berkeley AMPLab 启动 Spark |
| 2010 | 开源（BSD），主打"比 Hadoop MR 快 100 倍" |
| 2013 | Apache 顶级项目 |
| 2013 | 成立 **Databricks** 公司 |
| 2014 | 1.0 GA、Spark SQL |
| 2016 | 2.0 引入 **Structured Streaming** |
| 2018 | 2.4 ML / GraphX 成熟 |
| 2020 | **3.0** AQE + Dynamic Partition Pruning，性能跃进 |
| 2022 | 3.3 Pandas API on Spark、ANSI SQL |
| 2023 | **3.5** Spark Connect（远程执行） |
| 2024 | **4.0 准备发布**，强化 Spark Connect、Variant 类型 |
| 2024+ | **Spark on K8s + S3 + Iceberg/Delta** 成主流姿态 |

**主流版本**：3.4.x / 3.5.x，即将 4.0。

## 二、Spark 是什么

```
"统一的大规模数据分析引擎"

核心理念:
  - 内存计算（中间结果不落盘）
  - DAG 执行（替代 MR 的两阶段）
  - 一套 API 多种负载

五大模块:
  1. Spark Core          RDD 基础
  2. Spark SQL           DataFrame + SQL
  3. Structured Streaming 流处理
  4. MLlib               机器学习
  5. GraphX              图计算
```

## 三、核心抽象

| 抽象 | 说明 |
|:---|:---|
| **RDD** | 不可变分布式数据集（底层，少用） |
| **DataFrame** | 带 Schema 的分布式表（首选） |
| **Dataset** | Type-safe DataFrame（Java/Scala） |
| **Stage** | 由 Shuffle 切分的执行单元 |
| **Task** | Stage 内每个分区一个 Task |
| **Executor** | 工作进程，跑 Task |
| **Driver** | 主进程，调度 + 收集结果 |

## 四、架构原理

```
┌──────────────── Driver ────────────────┐
│  SparkContext / SparkSession          │
│  DAG Scheduler                        │
│  Task Scheduler                       │
└──────────────┬─────────────────────────┘
               ↓
┌──────────────── Cluster Manager ───────┐
│  YARN / K8s / Standalone / Mesos      │
└──────────────┬─────────────────────────┘
               ↓
┌──────────────── Executors × N ─────────┐
│  Task × M (multi-thread)              │
│  Block Manager (cache)                │
│  Shuffle Service                      │
└──────────────┬─────────────────────────┘
               ↓
┌──────────────── 数据 ──────────────────┐
│  HDFS / S3 / Iceberg / Delta / Kafka  │
└────────────────────────────────────────┘
```

### 执行流程

```
Application
  ↓
Job (由 Action 触发)
  ↓
Stage (Shuffle 边界切分)
  ↓
Task (每分区一个)
```

## 五、为什么 Spark 这么快

```
1. 内存计算（中间不落盘）
2. DAG 执行（MR 的两阶段 → 任意阶段）
3. Lazy 评估 + Catalyst 优化器
4. AQE（Adaptive Query Execution）3.0+
5. CBO（Cost-Based Optimizer）
6. Vectorized Execution（列向量化）
7. Tungsten（堆外 + Code Gen）
8. Whole-Stage Code Generation
```

## 六、核心功能

```
计算模式:
  - 批: Spark SQL + DataFrame
  - 流: Structured Streaming
  - 交互: spark-shell / pyspark / Notebook
  - ML: MLlib (Pipeline)
  - 图: GraphX (少用)
  - Pandas: pandas API on Spark (兼容)

API 语言:
  - Scala（原生最快）
  - Python (PySpark, 主流)
  - Java
  - R
  - SQL

集成:
  - Hive Metastore
  - Iceberg / Delta / Hudi
  - Kafka / Pulsar
  - JDBC / 各种 NoSQL
  - K8s 原生
```

## 七、使用场景

### ✅ 强烈推荐

| 场景 | 说明 |
|:---|:---|
| **离线 ETL** | 替代 Hive on MR，10-100x 提速 |
| **数据湖处理** | Iceberg/Delta/Hudi + Spark |
| **复杂 SQL 分析** | Spark SQL on HMS |
| **机器学习 ETL** | 训练数据准备 |
| **流批一体** | Structured Streaming |
| **数据科学** | PySpark + Jupyter |
| **跨数据源 ETL** | JDBC + S3 + HDFS + Kafka |
| **数仓宽表建设** | DWD/DWS 层加工 |

### ⚠️ 不推荐

- **超低延迟流处理（< 100ms）** → Flink
- **OLAP 实时查询** → Doris / ClickHouse / Trino
- **小数据（< 1GB）** → 单机 pandas / DuckDB
- **强事务** → 关系数据库
- **图查询深度** → Neo4j / Nebula

## 八、Spark vs 其他

| 维度 | Spark | Flink | Hive | Presto/Trino | Ray |
|:---|:---|:---|:---|:---|:---|
| 批处理 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 流处理 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ❌ | ⭐⭐⭐ |
| SQL | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| ML | ⭐⭐⭐⭐ | ⭐⭐ | ❌ | ❌ | ⭐⭐⭐⭐⭐ |
| 易用 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 流批一体 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ❌ | ⭐⭐⭐ |
| K8s 原生 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 主流度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

## 九、最佳实践

### 9.1 部署模式

| 模式 | 适合 |
|:---|:---|
| **Local** | 开发调试 |
| **Standalone** | 简单生产 |
| **YARN** | Hadoop 生态主流 |
| **K8s** ⭐ | **云原生首选** |
| **Mesos** | 已 deprecated |

### 9.2 资源配置（Driver/Executor）

```bash
spark-submit \
  --master k8s://https://k8s-api \
  --deploy-mode cluster \
  --conf spark.kubernetes.container.image=spark:3.5 \
  --conf spark.driver.memory=4g \
  --conf spark.driver.cores=2 \
  --conf spark.executor.instances=20 \
  --conf spark.executor.memory=16g \
  --conf spark.executor.cores=4 \
  --conf spark.executor.memoryOverhead=4g \
  --conf spark.sql.shuffle.partitions=400 \
  --conf spark.sql.adaptive.enabled=true \
  --conf spark.sql.adaptive.coalescePartitions.enabled=true \
  ...
```

**经验**：
```
Executor 内存 = 8-32GB 之间最甜
Executor cores = 4-5 个最佳
内存:核数 ≈ 4:1
Driver = 业务复杂度决定（默认 4GB 起）
```

### 9.3 Spark SQL / DataFrame 调优

```python
spark.conf.set("spark.sql.adaptive.enabled", "true")              # AQE 必开
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")     # 倾斜自动处理
spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", "true")
spark.conf.set("spark.sql.cbo.enabled", "true")
spark.conf.set("spark.sql.cbo.joinReorder.enabled", "true")
spark.conf.set("spark.sql.shuffle.partitions", "400")             # 默认 200
spark.conf.set("spark.sql.files.maxPartitionBytes", "256m")
spark.conf.set("spark.sql.broadcastTimeout", "600")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "100m")    # 小表广播
spark.conf.set("spark.sql.parquet.compression.codec", "zstd")
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
```

### 9.4 Shuffle 调优（性能关键）

```
✅ AQE 打开（自动合并/拆分分区）
✅ 分区数 ≈ 集群总 core × 2-4
✅ 减少不必要的 Shuffle (broadcast join, repartition 慎用)
✅ 倾斜数据处理:
   - 加盐 (salt)
   - 单独处理大 key
   - AQE skewJoin
✅ 关闭 sort-merge join 触发广播
✅ Shuffle Service 开启 (External Shuffle Service)
✅ 用 Tungsten 列式 shuffle
```

### 9.5 Structured Streaming（流处理）

```python
df = (spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "...")
        .option("subscribe", "events")
        .load())

result = (df
    .selectExpr("CAST(value AS STRING) as json")
    .selectExpr("from_json(json, 'user_id BIGINT, event STRING, ts TIMESTAMP') as data")
    .select("data.*")
    .withWatermark("ts", "10 minutes")
    .groupBy(window("ts", "1 minute"), "event")
    .count())

query = (result.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "s3://bucket/checkpoints/events")
    .trigger(processingTime="30 seconds")
    .start("s3://bucket/silver/events"))
```

**关键**：
```
✅ Watermark 处理迟到数据
✅ Checkpoint 必设（HDFS/S3）
✅ Trigger 控制频率（continuous 模式实验性）
✅ Output: append / update / complete
✅ Exactly-once（Source/Sink 都支持）
```

### 9.6 数据湖集成

```python
# Delta
spark.sql("CREATE TABLE events USING DELTA LOCATION 's3://...' AS SELECT ...")

# Iceberg
spark.sql("""
  CREATE TABLE catalog.db.events (
    user_id BIGINT, event STRING, ts TIMESTAMP
  ) USING iceberg
  PARTITIONED BY (days(ts))
""")

# Hudi
df.write.format("hudi") \
  .option("hoodie.table.name", "events") \
  .option("hoodie.datasource.write.recordkey.field", "user_id") \
  .mode("append").save("s3://...")
```

### 9.7 Spark on K8s 最佳实践

```yaml
# spark-operator (Kubeflow)
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: etl-daily
spec:
  type: Python
  pythonVersion: "3"
  mode: cluster
  image: registry/spark:3.5
  mainApplicationFile: s3a://bucket/jobs/etl.py
  sparkVersion: "3.5.0"
  driver:
    cores: 2
    memory: "4g"
    serviceAccount: spark
  executor:
    cores: 4
    instances: 10
    memory: "16g"
  dynamicAllocation:
    enabled: true
    minExecutors: 2
    maxExecutors: 50
  sparkConf:
    "spark.sql.adaptive.enabled": "true"
    "spark.kubernetes.allocation.batch.size": "10"
```

### 9.8 Python 开发最佳实践

```
✅ PySpark + Pandas API on Spark（替代 pandas）
✅ pip install pyspark[sql,ml] 本地开发
✅ Notebook: Jupyter / Databricks
✅ 类型 hint + pyspark.sql.types
✅ UDF 慎用（慢，优先 SQL 内置或 Pandas UDF）
✅ Pandas UDF (vectorized) 比普通 UDF 快 10-100x
```

### 9.9 数据倾斜处理

```sql
-- 1. AQE skewJoin (3.0+) 自动
-- 2. 加盐 (manual)
SELECT /*+ SKEW('orders', 'user_id', (1001, 1002)) */ ...

-- 3. 拆分大 Key + Union
SELECT * FROM (
  SELECT * FROM big WHERE user_id IN (hot_keys)
  /*+ BROADCAST(small) */ JOIN small
  UNION ALL
  SELECT * FROM big WHERE user_id NOT IN (hot_keys)
  JOIN small
)

-- 4. 广播小表
SELECT /*+ BROADCAST(dim) */ ... FROM fact JOIN dim
```

### 9.10 资源动态分配

```bash
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.minExecutors=2
spark.dynamicAllocation.maxExecutors=100
spark.dynamicAllocation.initialExecutors=10
spark.dynamicAllocation.executorIdleTimeout=60s
spark.shuffle.service.enabled=true       # YARN
# K8s 用 spark.dynamicAllocation.shuffleTracking.enabled=true
```

## 十、运维命令速查

```bash
# 提交
spark-submit --class App app.jar
spark-submit --master yarn --deploy-mode cluster ...
spark-sql -e "SELECT ..."
pyspark / spark-shell

# 监控
# Spark UI: 默认 4040 / Driver 上
# History Server: 18080
$SPARK_HOME/sbin/start-history-server.sh

# K8s
kubectl get sparkapplications
kubectl describe sparkapplication etl-daily
kubectl logs sparkapp-driver

# 查看执行计划
spark.sql("EXPLAIN EXTENDED SELECT ...").show()
df.explain(True)
df.explain("formatted")
```

## 十一、常见坑

| 坑 | 建议 |
|:---|:---|
| **OOM Executor** | 加内存或拆分区 |
| **Shuffle 慢** | AQE + 调 partitions + Tungsten |
| **GC 卡顿** | 堆 < 32G + G1GC |
| **数据倾斜** | AQE skewJoin / 加盐 / 广播 |
| **Driver OOM** | collect/toPandas 数据量太大 |
| **task 太多/太少** | partitions 调整 |
| **小文件输出多** | coalesce / repartition + AQE |
| **Broadcast 超时** | broadcastTimeout 调大 |
| **Hive 兼容性** | spark.sql.hive.convertMetastoreOrc/Parquet |
| **PySpark 慢 UDF** | 用 Pandas UDF / SQL 内置 |
| **K8s Driver Pod 飘** | 设 nodeSelector + tolerations |
| **S3 写慢** | 用 S3A + DirectoryCommitter / Iceberg/Delta |
| **dynamic allocation 不工作** | shuffle service / shuffle tracking |
| **大表 JOIN OOM** | sort-merge + 分区裁剪 + AQE |

## 十二、生态与工具

| 工具 | 用途 |
|:---|:---|
| **Spark Connect** | 远程 client，Pythonic |
| **Spark Operator** | K8s |
| **Delta Lake** | Databricks 数据湖 |
| **Apache Iceberg** | 数据湖 |
| **Apache Hudi** | 数据湖 + CDC |
| **MLflow** | ML 实验管理 |
| **Koalas / Pandas API on Spark** | pandas 兼容 |
| **Sedona** | 地理空间 |
| **GraphFrames** | 图 |
| **DataHub / Atlas** | 元数据 |

## 十三、Spark Connect（3.4+）

```python
# 客户端连接远程 Spark
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .remote("sc://spark-server:15002") \
    .getOrCreate()

df = spark.read.parquet("s3://...")
df.show()
```

**优势**：
- 解耦 Client / Driver
- 客户端不再依赖整个 Spark 环境
- 支持多语言（Go/Rust/Java/Python）
- 适合 Notebook、BI 工具集成

## 十四、Databricks vs Open Source Spark

| 维度 | Databricks | OSS Spark |
|:---|:---|:---|
| 性能 | 商业 Photon 引擎快 2-5x | 基线 |
| 易用 | Notebook + Unity Catalog | spark-submit |
| 价格 | $$$ | 免费 |
| 国内 | 不直接卖 | 主流 |
| 数据湖 | Delta（亲生） | 通用 |
| ML/AI | MLflow + AutoML | 自建 |

## 十五、监控指标

```
Driver:
  Active Jobs / Failed Jobs
  Total Tasks / Skipped
  GC time / heap

Executor:
  Tasks Active / Failed
  Input/Output bytes
  Shuffle Read/Write
  Memory Used

Shuffle:
  Shuffle Read Bytes
  Shuffle Write Bytes
  Spill (disk/memory)

工具:
  Spark UI / History Server
  Prometheus + spark-metrics
  Datadog APM
  Databricks GhostDriver UI
```

## 十六、K8s + S3 + Iceberg 标准栈

```
推荐 2025 大数据栈:
  存储:     S3 / OSS / MinIO / Ozone
  计算:     Spark on K8s（Operator）
  目录:     Iceberg / Delta + HMS / Polaris / Unity
  调度:     Airflow / Argo / DolphinScheduler
  元数据:   HMS / Atlas / DataHub
  查询:     Trino + Spark SQL + Doris/StarRocks
  ML:       MLflow / Kubeflow
  CDC:      Debezium → Kafka → Spark/Flink
```

## 十七、国产替代 / 兼容

| 产品 | 厂商 |
|:---|:---|
| **MaxCompute** | 阿里云（自研，SQL 兼容）|
| **EMR Spark** | 各家云 |
| **DataWorks** | 阿里云数据开发 |
| **SparkCompute / TBDS** | 腾讯云 |
| **DLI** | 华为云 |
| **OushuDB** | 偶数科技 |
| **Inceptor** | 星环科技 |

## 十八、学习路径

```
入门:
  1. 装单机 Spark + 跑 examples
  2. pyspark 操作 DataFrame
  3. 理解 RDD / DataFrame / Catalyst

中级:
  4. Spark SQL + Hive Metastore
  5. ETL 全流程（读 → 转 → 写）
  6. AQE / 倾斜 / 调优
  7. Structured Streaming + Kafka
  8. K8s + Spark Operator 部署

高级:
  9. Iceberg/Delta/Hudi 集成
  10. 性能压测 + GC 调优
  11. 流批一体架构
  12. MLlib / Pandas UDF
  13. Spark Connect 远程开发
  14. 国产化大数据栈对接
```

## 十九、未来展望

```
1-2 年:
  - Spark 4.0 发布，Variant、Spark Connect 标配
  - Photon 类向量化引擎社区化（Comet / Gluten）
  - Spark on K8s 取代 Spark on YARN
  - Iceberg/Delta/Hudi 三国杀持续

3-5 年:
  - 流批一体逐步统一到 Flink + Spark 并存
  - 数据湖仓（Lakehouse）成为新默认
  - SQL 引擎多元化（Trino/Spark/Doris 共存）

5 年+:
  - Spark 进入"稳定持续维护"阶段
  - AI 数据管道与传统大数据栈融合
  - Ray / Dask 在 ML 数据预处理蚕食部分场景
```

> 📖 **核心判断**：Spark 是大数据**第二代主流计算引擎**，目前仍是事实标准。**新建项目首选 Spark on K8s + S3 + Iceberg/Delta**。流处理可与 Flink 配合（重写流场景选 Flink，老 Spark 流场景 Structured Streaming 也够用）。
