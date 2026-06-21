# Redis

## 部署模式

| 模式 | 说明 | 适用 |
|:---|:---|:---|
| 单机 | 单实例 | 开发测试 |
| Sentinel | 主从+自动切换 | 高可用要求 |
| Cluster | 分片+高可用 | 大规模场景 |

## 常用命令

```bash
# 基础
redis-cli SET key value
redis-cli GET key
redis-cli DEL key
redis-cli KEYS pattern

# 监控
redis-cli INFO
redis-cli INFO memory
redis-cli INFO stats
redis-cli MONITOR
redis-cli SLOWLOG GET 10

# 集群管理
redis-cli --cluster create 10.0.0.1:6379 10.0.0.2:6379 10.0.0.3:6379
redis-cli --cluster check 10.0.0.1:6379
```

## 缓存策略

| 策略 | 说明 | 场景 |
|:---|:---|:---|
| 过期时间 (TTL) | 自动删除 | 通用缓存 |
| LRU | 最近最少使用淘汰 | 内存受限 |
| LFU | 最不经常使用淘汰 | 访问频率不均 |
| 穿透 | 查不到也缓存空值 | 防止穿透 |
| 击穿 | 热点 key 互斥更新 | 高并发 |
| 雪崩 | 过期时间加随机值 | 批量过期 |

## 性能排查

```bash
# 大 key 扫描
redis-cli --bigkeys

# 内存分析
redis-cli MEMORY USAGE key
redis-cli MEMORY STATS

# 延迟
redis-cli --latency -h <host> -p 6379
```
