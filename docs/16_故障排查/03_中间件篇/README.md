# 中间件篇故障排查

## MySQL 主从延迟

```sql
-- 查看从库状态
SHOW SLAVE STATUS\G
-- 关键字段：
-- Seconds_Behind_Master: 延迟秒数
-- Slave_IO_Running: IO 线程是否正常
-- Slave_SQL_Running: SQL 线程是否正常
```

## PostgreSQL 连接耗尽

```sql
-- 查看当前连接
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity;

-- 终止空闲连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle' AND pid <> pg_backend_pid();

-- 调整最大连接
ALTER SYSTEM SET max_connections = 300;
SELECT pg_reload_conf();
```

## Redis OOM

```bash
# 查看内存
redis-cli INFO memory

# 查看大 key
redis-cli --bigkeys

# 设置内存限制和淘汰策略
redis-cli CONFIG SET maxmemory 8GB
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Kafka 消费者延迟

```bash
# 查看消费组偏移
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group consumer-group \
  --describe

# 查看 Topic 偏移
kafka-run-class.sh kafka.tools.GetOffsetShell \
  --bootstrap-server localhost:9092 \
  --topic my-topic --time -1
```
