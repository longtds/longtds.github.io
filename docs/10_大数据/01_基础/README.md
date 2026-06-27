# 基础

> 大数据基础 = **数据架构(Lambda/Kappa) + Hadoop 生态(HDFS/YARN/Hive) + Spark + Flink + 调度(Airflow/DolphinScheduler) + 采集(DataX/SeaTunnel/Flume) + 数据建模(维度建模/数据分层) + 国产引擎(Doris/StarRocks/Paimon)**。本章面向数据工程师入门。

## 一、大数据全景

```
计算引擎:
  Hadoop MapReduce       老 (淘汰中)
  Spark ⭐               批 + 流 + ML + Graph
  Flink ⭐               流 (有状态, 低延时)
  Trino / Presto         即席查询
  Doris / StarRocks ⭐   MPP 实时数仓 (国产)
  ClickHouse ⭐          列存 OLAP

存储:
  HDFS                   传统分布式
  对象存储 (S3/OSS/MinIO)  云原生 ⭐
  Iceberg / Hudi / Delta / Paimon  数据湖格式 ⭐
  Hive Metastore         元数据 (老)
  Nessie / Polaris       数据湖目录 (新)

调度:
  Airflow ⭐             Python DAG
  DolphinScheduler ⭐    国产, 易用, 可视化
  Argo Workflows         K8s 原生
  Dagster                Python 现代

采集 / 集成:
  Flume / Logstash       日志
  DataX ⭐               国产, 阿里
  SeaTunnel ⭐           国产, Apache, 流批一体
  Canal / Debezium       CDC 增量
  Kafka Connect          云原生

OLAP:
  ClickHouse / Doris / StarRocks / Druid / Kylin

数据湖 / 湖仓:
  Iceberg / Hudi / Delta / Paimon
  Databricks Lakehouse
  Snowflake / BigQuery

可视化 / BI:
  Superset ⭐ / Grafana / Tableau / FineBI / Quick BI
  Metabase / Redash
```

## 二、Lambda vs Kappa 架构

```
Lambda (老):
  批层 (Batch)     Spark / Hadoop   全量准
  速度层 (Speed)   Storm / Flink    实时
  服务层 (Serving) Druid / HBase    合并

  缺点: 双套维护 / 一致性难

Kappa (新):
  流为主 (Kafka + Flink)
  历史回放 (从 offset 0)
  
  优点: 一套代码 / 一致
  
湖仓一体 (Lakehouse, 现代主流):
  Iceberg + Spark / Flink + Trino
  Paimon + Flink (流批一体 ⭐)
  Snowflake / BigQuery (云上)
```

## 三、HDFS 基础

### 3.1 概念

```
NameNode:    元数据
DataNode:    实际块 (默认 128MB)
副本:        默认 3 副本
读写:        Client → NN 询问 → DN 直接读写

HA 拓扑:
  Active NN + Standby NN
  ZooKeeper Failover Controller
  JournalNode 共享 edits
```

### 3.2 必会命令

```bash
hdfs dfs -ls /
hdfs dfs -mkdir -p /user/alice/data
hdfs dfs -put local.txt /user/alice/
hdfs dfs -get /user/alice/local.txt .
hdfs dfs -cat /user/alice/local.txt
hdfs dfs -rm -r /user/alice/data
hdfs dfs -du -h /user
hdfs dfs -setrep 3 /user/alice/data
hdfs dfsadmin -report
hdfs fsck /user/alice/data -files -blocks -locations
```

### 3.3 替代

```
HDFS (淘汰中):
  老 / 重 / 难以容器化

替代:
  对象存储 ⭐ (S3 / OSS / MinIO)
  JuiceFS    POSIX + 对象后端
  CubeFS     国产, CNCF
  Alluxio    缓存层
```

## 四、Hive 基础

### 4.1 概念

```
组件:
  Metastore     元数据 (MySQL)
  HiveServer2   服务
  HCatalog      表抽象

特性:
  SQL → MR/Tez/Spark
  外表 (External Table)
  分区 / 分桶
  ACID (Hive 3.x, Hive on Tez)
```

### 4.2 必会 SQL

```sql
CREATE EXTERNAL TABLE orders (
  id BIGINT,
  user_id BIGINT,
  amount DOUBLE,
  ts TIMESTAMP
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION 'hdfs:///warehouse/orders';

ALTER TABLE orders ADD PARTITION (dt='2026-06-27')
  LOCATION 'hdfs:///warehouse/orders/dt=2026-06-27';

SELECT user_id, SUM(amount) AS total
FROM orders
WHERE dt = '2026-06-27'
GROUP BY user_id;

MSCK REPAIR TABLE orders;     -- 修复分区
```

### 4.3 替代

```
Hive Metastore + HiveQL:
  老 (依赖 MR / Tez 慢)

替代:
  Iceberg + Spark/Trino (湖仓)
  Paimon + Flink (流批)
  Apache Polaris / Nessie (元数据)
  Databricks Unity Catalog
```

## 五、Spark 基础

### 5.1 核心概念

```
RDD       不可变分布式数据集 (低级)
DataFrame Schema 优化 (主流) ⭐
Dataset   类型安全 (Scala/Java)
SparkSQL  SQL 接口
Structured Streaming  流 (流批一体)

执行:
  Driver → DAG → Stage → Task
  Lazy eval (action 触发)
  Cluster Manager: K8s / YARN / Standalone
```

### 5.2 必会 PySpark

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder \
    .appName("demo") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()

df = spark.read.parquet("s3://bucket/orders/")
result = (df
    .filter(F.col("dt") == "2026-06-27")
    .groupBy("user_id")
    .agg(F.sum("amount").alias("total"), F.count("*").alias("cnt"))
    .orderBy(F.desc("total"))
)
result.show(20)
result.write.mode("overwrite").parquet("s3://bucket/agg/")
```

### 5.3 提交

```bash
spark-submit \
  --master k8s://https://k8s.example.com:6443 \
  --deploy-mode cluster \
  --name demo \
  --conf spark.kubernetes.container.image=harbor.example.com/spark:3.5 \
  --conf spark.kubernetes.namespace=spark \
  --conf spark.executor.instances=4 \
  --conf spark.driver.cores=1 --conf spark.executor.cores=2 \
  --conf spark.driver.memory=2g --conf spark.executor.memory=4g \
  --conf spark.kubernetes.driver.podTemplateFile=driver.yaml \
  local:///opt/job.py
```

### 5.4 Spark on K8s

```
推荐:
  Spark Operator ⭐ (kubeflow / Apache)
  原生 spark-submit cluster mode
  Volcano / Yunikorn 调度
  
存储:
  S3 / OSS (取代 HDFS)
  Iceberg / Paimon (湖仓)
```

## 六、Flink 基础

### 6.1 核心概念

```
JobManager    协调
TaskManager   执行
Slot          并发槽
Checkpoint    一致性快照 (exactly-once)
Savepoint     手动 (升级 / 迁移)

API:
  DataStream  流
  Table API / Flink SQL ⭐ (流批一体)
  CEP         事件模式
  Stateful Functions
```

### 6.2 Flink SQL 实战

```sql
-- Kafka 源
CREATE TABLE orders_src (
  id BIGINT,
  user_id BIGINT,
  amount DECIMAL(10,2),
  ts TIMESTAMP(3),
  WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'orders',
  'properties.bootstrap.servers' = 'kafka:9092',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json'
);

-- 输出到 Paimon 湖
CREATE TABLE orders_agg (
  user_id BIGINT,
  win_start TIMESTAMP(3),
  win_end   TIMESTAMP(3),
  total     DECIMAL(20,2),
  cnt       BIGINT,
  PRIMARY KEY (user_id, win_start) NOT ENFORCED
) WITH (
  'connector' = 'paimon',
  'path' = 's3://bucket/paimon/orders_agg'
);

-- 流式聚合
INSERT INTO orders_agg
SELECT
  user_id,
  TUMBLE_START(ts, INTERVAL '1' MINUTE),
  TUMBLE_END  (ts, INTERVAL '1' MINUTE),
  SUM(amount),
  COUNT(*)
FROM orders_src
GROUP BY user_id, TUMBLE(ts, INTERVAL '1' MINUTE);
```

### 6.3 部署

```bash
# Standalone / Session
./bin/start-cluster.sh

# K8s Session
./bin/kubernetes-session.sh \
  -Dkubernetes.cluster-id=prod-flink \
  -Dkubernetes.namespace=flink \
  -Dkubernetes.container.image=harbor.example.com/flink:1.19

# Application Mode (推荐 K8s)
./bin/flink run-application \
  --target kubernetes-application \
  -Dkubernetes.cluster-id=demo-job \
  -Dkubernetes.namespace=flink \
  -Dkubernetes.container.image=harbor.example.com/flink-job:v1 \
  local:///opt/flink/usrlib/demo.jar
```

### 6.4 Flink Kubernetes Operator ⭐

```yaml
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata: { name: orders-agg, namespace: flink }
spec:
  image: harbor.example.com/flink:1.19
  flinkVersion: v1_19
  flinkConfiguration:
    taskmanager.numberOfTaskSlots: "2"
    state.backend: rocksdb
    state.checkpoints.dir: s3://flink/checkpoints
  serviceAccount: flink
  jobManager: { resource: { memory: "2048m", cpu: 1 } }
  taskManager: { resource: { memory: "4096m", cpu: 2 } }
  job:
    jarURI: local:///opt/flink/usrlib/demo.jar
    parallelism: 4
    upgradeMode: savepoint
    state: running
```

## 七、调度系统

### 7.1 Airflow（Python DAG）

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "etl_daily",
    start_date=datetime(2026, 6, 1),
    schedule="0 2 * * *",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["etl"],
) as dag:
    extract = BashOperator(task_id="extract", bash_command="python /opt/etl/extract.py")
    transform = BashOperator(task_id="transform", bash_command="spark-submit /opt/etl/tx.py")
    load = BashOperator(task_id="load", bash_command="python /opt/etl/load.py")
    extract >> transform >> load
```

### 7.2 DolphinScheduler（国产 ⭐）

```
特性:
  - 可视化 DAG (拖拽)
  - 多租户 + 项目
  - 国产 Apache 顶级
  - Web UI 友好
  - 支持 Shell / Spark / Flink / Python / SQL
  - K8s Worker

适合:
  - 国央企 / 政企 (中文 + 易上手)
  - 业务非 Python 团队
```

### 7.3 Argo Workflows（K8s 原生）

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata: { name: etl-daily }
spec:
  entrypoint: main
  templates:
    - name: main
      dag:
        tasks:
          - name: extract
            template: run
            arguments: { parameters: [{ name: cmd, value: "python extract.py" }] }
          - name: transform
            template: run
            depends: extract
            arguments: { parameters: [{ name: cmd, value: "spark-submit tx.py" }] }
    - name: run
      inputs: { parameters: [{ name: cmd }] }
      container: { image: etl:v1, command: [sh, -c, "{{inputs.parameters.cmd}}"] }
```

### 7.4 选型

```
Python 团队 + 灵活:     Airflow ⭐
国央企 + 可视化:        DolphinScheduler ⭐
K8s 原生 + 微服务:      Argo Workflows ⭐
现代 Python + Asset:    Dagster
轻量 ETL:               Prefect
```

## 八、数据采集

### 8.1 DataX（国产 ⭐）

```json
{
  "job": {
    "content": [{
      "reader": {
        "name": "mysqlreader",
        "parameter": {
          "username": "user", "password": "***",
          "connection": [{
            "jdbcUrl": ["jdbc:mysql://10.0.0.1:3306/app"],
            "table": ["orders"]
          }],
          "column": ["id","user_id","amount","ts"],
          "where": "dt='2026-06-27'"
        }
      },
      "writer": {
        "name": "hdfswriter",
        "parameter": {
          "defaultFS": "hdfs://nameservice1",
          "path": "/warehouse/orders/dt=2026-06-27",
          "fileType": "parquet",
          "fileName": "part",
          "column": [...]
        }
      }
    }],
    "setting": { "speed": { "channel": 4 } }
  }
}
```

### 8.2 SeaTunnel（国产 Apache ⭐）

```hocon
env {
  parallelism = 4
  job.mode = "STREAMING"
}
source {
  Kafka {
    topic = "orders"
    bootstrap.servers = "kafka:9092"
    format = json
    schema = { fields { id = bigint, user_id = bigint, amount = double, ts = timestamp } }
  }
}
transform {
  Sql { sql = "SELECT user_id, amount, ts FROM kafka WHERE amount > 0" }
}
sink {
  Paimon {
    warehouse = "s3://bucket/paimon"
    database = "ods"
    table = "orders"
  }
}
```

### 8.3 Canal / Debezium（CDC 增量）

```
Canal (阿里):     MySQL binlog 解析 → Kafka/MQ
Debezium:        多 DB CDC (MySQL/PG/Mongo/Oracle/SQL Server) → Kafka
Flink CDC ⭐:    Flink 原生 CDC (基于 Debezium, 支持全增量一体)
TiCDC:           TiDB 原生
```

## 九、数据建模

### 9.1 数据分层（Lambda 标准）

```
ODS (Operational Data Store)     原始数据 (1:1 同步)
DWD (Data Warehouse Detail)      明细 (清洗 + 维度退化)
DIM (Dimension)                  维度表 (公共)
DWS (Data Warehouse Summary)     轻汇总
ADS (Application Data Service)   应用 (面向业务)

命名:
  ods_<source>_<table>_d
  dwd_<domain>_<event>_d
  dim_<domain>_<entity>
  dws_<domain>_<metric>_d
  ads_<biz>_<metric>_d
```

### 9.2 维度建模（Kimball）

```
星型模型:
  事实表 (Fact)  + 维度表 (Dimension)
  
雪花模型:
  维度表再分层
  
SCD (Slowly Changing Dimension):
  Type 1  覆盖
  Type 2  历史保留 (start/end + 是否当前) ⭐
  Type 3  字段保留前值
```

### 9.3 实体关系 + 主题域

```
主题域:
  用户 / 商品 / 订单 / 支付 / 营销 / 物流 / 库存
  风控 / 推荐 / 监控

每个主题:
  ods → dwd → dws → ads
  数据字典 + 血缘 (DataHub / Apache Atlas)
```

## 十、入门 20 题

```
1.  Lambda vs Kappa vs Lakehouse
2.  HDFS 副本 / 容错 / 写流程
3.  MapReduce shuffle 原理
4.  Hive 内表 vs 外表 / 分区 vs 分桶
5.  Spark RDD vs DataFrame
6.  Spark shuffle 三种 (Sort / Bypass / Tungsten)
7.  Spark Stage 切分原理
8.  Flink 状态 / Checkpoint / Savepoint
9.  Flink 时间 (Event/Ingestion/Processing)
10. Flink Watermark 作用
11. Flink Exactly-Once 实现
12. Kafka + Flink 端到端一致性
13. Iceberg vs Hudi vs Delta vs Paimon
14. SCD 类型
15. 数据倾斜原因 + 解决
16. 维度建模 vs 范式
17. Star vs Snowflake
18. Doris vs StarRocks vs ClickHouse
19. DataX vs SeaTunnel
20. Airflow vs DolphinScheduler
```

## 十一、推荐栈（基础）

```
计算:      Spark ⭐ (批) + Flink ⭐ (流)
存储:      对象存储 ⭐ + Iceberg / Paimon ⭐
元数据:    Hive Metastore (老) / Polaris / Nessie (新)
调度:      Airflow ⭐ / DolphinScheduler ⭐ / Argo Workflows
采集:      SeaTunnel ⭐ + Flink CDC ⭐
OLAP:      Doris ⭐ / StarRocks ⭐ / ClickHouse ⭐
BI:        Superset ⭐ / 国产 FineBI / Quick BI
血缘:      DataHub / Apache Atlas
```

## 十二、学习路径

```
入门（1-3 月）:
  1. HDFS / Hive 概念 + 命令
  2. Spark PySpark + DataFrame
  3. Flink SQL + Table API
  4. Airflow / DolphinScheduler 一种
  5. SeaTunnel / DataX 一种
  6. 数据分层 + 维度建模
  7. 20 题

进阶（3-12 月, 见 02_进阶）:
  8. Iceberg / Paimon 湖仓
  9. Doris / StarRocks 实时数仓
  10. Spark on K8s / Flink Operator
  11. 调度 + CI/CD + 监控
```

> 📖 **核心判断**：大数据基础 = **Lambda/Kappa/湖仓三种架构 + HDFS/对象存储 + Hive/Iceberg/Paimon + Spark/Flink 双引擎 + Airflow/DolphinScheduler 调度 + DataX/SeaTunnel/CDC 采集 + 数据分层(ODS/DWD/DWS/ADS) + 维度建模**。能跑通 Kafka → Flink SQL → Paimon → Doris → Superset 流批一体链路，就具备数据工程师入门能力。
