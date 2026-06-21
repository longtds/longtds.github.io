# MySQL

## 部署与高可用

```bash
# 主从复制部署
docker run -d --name mysql-master \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_REPLICATION_MODE=master \
  -e MYSQL_REPLICATION_USER=repl \
  -e MYSQL_REPLICATION_PASSWORD=repl \
  mysql:8.0

docker run -d --name mysql-slave \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_REPLICATION_MODE=slave \
  -e MYSQL_MASTER_HOST=mysql-master \
  -e MYSQL_MASTER_USER=repl \
  -e MYSQL_MASTER_PASSWORD=repl \
  mysql:8.0
```

## 性能优化

```sql
-- 查看慢查询
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;

-- InnoDB 调优
SET GLOBAL innodb_buffer_pool_size = 4G;
SET GLOBAL innodb_log_file_size = 512M;

-- 连接数
SET GLOBAL max_connections = 500;
```

## 常见问题

| 问题 | 排查方法 |
|:---|:---|
| 主从延迟 | `SHOW SLAVE STATUS\G` 看 Seconds_Behind_Master |
| 死锁 | `SHOW ENGINE INNODB STATUS\G` |
| 慢查询 | 启用 slow_log，用 pt-query-digest 分析 |
| 连接耗尽 | 检查 max_connections 和应用连接池 |
