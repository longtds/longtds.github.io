# 大数据篇故障排查

## Spark OOM

```bash
# 调整 Executor 内存
spark.executor.memory=8g
spark.executor.memoryOverhead=4g
spark.driver.memory=4g

# 调整分区数
spark.sql.shuffle.partitions=400
```

## HDFS 磁盘满

```bash
# 查看集群容量
hdfs dfsadmin -report

# 查看大目录
hdfs dfs -du -h / | sort -rh | head -10

# 回收站清理
hdfs dfs -expunge
```
