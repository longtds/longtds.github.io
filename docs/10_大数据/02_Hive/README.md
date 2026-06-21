# Hive

## 概述

Hive 提供 SQL 接口查询 HDFS 上的数据，将 HQL 转换为 MapReduce/Spark/Tez 任务执行。

## 表类型

```sql
-- 内部表（数据由 Hive 管理）
CREATE TABLE users (
  id INT,
  name STRING,
  created DATE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ',';

-- 外部表（数据在 HDFS 外部）
CREATE EXTERNAL TABLE logs (
  log_time TIMESTAMP,
  level STRING,
  message STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION '/data/logs';

-- 分区表
ALTER TABLE logs ADD PARTITION (dt='2026-06-15');
```

## 优化

```sql
-- 分区裁剪
SELECT * FROM logs WHERE dt = '2026-06-15';

-- 分桶表（提高 JOIN 效率）
CREATE TABLE users_bucketed (
  id INT, name STRING
)
CLUSTERED BY (id) INTO 16 BUCKETS;

-- 文件格式：ORC/Parquet 比 Text 快 10x
-- 开启向量化
SET hive.vectorized.execution.enabled = true;
```
