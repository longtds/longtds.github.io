# 数据湖与存储

## Delta Lake

Delta Lake 在数据湖上提供 ACID 事务、时间旅行和 Schema 演化。

```python
# Delta 表操作
df.write.format("delta").mode("overwrite").save("/data/delta-table")

# 时间旅行
spark.read.format("delta").option("versionAsOf", "10").load("/data/delta-table")

# UPSERT（合并）
from delta.tables import DeltaTable
deltaTable = DeltaTable.forPath(spark, "/data/delta-table")
deltaTable.alias("target").merge(
    updates.alias("source"),
    "target.id = source.id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

## S3 vs HDFS

| 维度 | HDFS | S3 / MinIO |
|:---|:---|:---|
| 协议 | 专用协议 | HTTP RESTful |
| 扩展性 | 有限 | 无限 |
| 存储成本 | 高（3副本） | 低（纠删码） |
| 计算存储耦合 | 物理耦合 | 分离 |
| 生态 | Hadoop 生态 | 通用 S3 生态 |
| K8s 集成 | 困难 | 原生集成 |
