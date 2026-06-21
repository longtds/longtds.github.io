# Hadoop

## HDFS

HDFS 是分布式文件系统，适合大文件的顺序读写。

```bash
# HDFS 常用命令
hdfs dfs -ls /data
hdfs dfs -mkdir -p /data/logs
hdfs dfs -put localfile /data/
hdfs dfs -get /data/remotefile ./
hdfs dfs -rm -r /data/old

# 查看集群状态
hdfs dfsadmin -report
hdfs fsck / -files -blocks
```

## YARN

YARN 是 Hadoop 的资源调度系统。

```bash
# 查看任务
yarn application -list
yarn application -status <app_id>
yarn logs -applicationId <app_id>

# 查看节点
yarn node -list -all
```
