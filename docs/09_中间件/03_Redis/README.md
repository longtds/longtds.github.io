# Redis

> 单线程、内存型、极致快速的 Key-Value 数据库。**互联网公司最常用的"万能瑞士军刀"**——缓存、会话、计数器、消息、限流、分布式锁、地理、向量……几乎无所不能。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2009 | Salvatore Sanfilippo（antirez，意大利）发布 Redis |
| 2013 | VMware/Pivotal 赞助开发 |
| 2015 | Redis 3.0 发布 Cluster 模式 |
| 2018 | 5.0 引入 **Stream** 数据结构 |
| 2020 | 6.0 **多线程 IO**、ACL |
| 2022 | 7.0 函数（Functions）、ACL v2 |
| 2024.3 | **Redis 7.4 改 license（SSPL/RSAL）→ Linux 基金会 Fork 出 Valkey** |
| 2024 | AWS/Google/Oracle 全部转向 Valkey |
| 2025 | Valkey 8.0 发布，成为新事实标准 |

> ⚠️ **2024 重大变化**：Redis 改了 license，不再 BSD。**云厂商集体倒戈 Valkey（完全兼容协议）**。新建项目可考虑 Valkey 或仍用 Redis 商业版/AOSP 兼容版。

## 二、核心功能

```
内置 9 种数据结构:
  1. String              ← 缓存、计数器
  2. List                ← 队列、栈
  3. Hash                ← 对象存储
  4. Set                 ← 去重、标签
  5. Sorted Set (ZSet)   ← 排行榜、延时队列
  6. Bitmap              ← 签到、布隆过滤底层
  7. HyperLogLog         ← 基数统计 (UV)
  8. Geo                 ← 地理位置
  9. Stream              ← 消息队列（5.0+）

附加能力:
  - 发布订阅 Pub/Sub
  - 事务 MULTI/EXEC
  - Lua 脚本
  - 函数 Functions (7.0+)
  - 模块: RedisJSON / RediSearch / RedisBloom / RedisTimeSeries
  - 持久化: RDB / AOF / 混合
  - 复制: 主从 / Sentinel / Cluster
  - 多线程 IO (6.0+)
```

## 三、架构原理

```
┌────────────── 核心 ──────────────┐
│ 单线程事件循环（Reactor 模型）    │
│ → 命令处理永远单线程               │
│ → IO 读写多线程（6.0+ 可选）       │
└──────────────┬───────────────────┘
               ↓
┌────────────── 内存结构 ──────────┐
│ 字典 (dict) + SDS / quicklist /  │
│ ziplist / listpack / skiplist /  │
│ intset / hashtable               │
└──────────────┬───────────────────┘
               ↓
┌────────────── 持久化 ────────────┐
│ RDB  快照（定期 dump）           │
│ AOF  Append-Only File           │
│ 混合 RDB + AOF                  │
└──────────────────────────────────┘
```

### 为什么单线程还这么快

```
1. 纯内存操作（无磁盘 IO 等待）
2. IO 多路复用（epoll）
3. 没有锁竞争 + 没有线程切换开销
4. 高效数据结构（如 ziplist 紧凑存储）
5. 6.0+ IO 读写多线程（继续榨干 CPU）
```

## 四、使用场景

### ✅ 经典场景

| 场景 | 方案 |
|:---|:---|
| **缓存** | String + TTL，最经典 |
| **分布式 Session** | Hash 存用户态 |
| **排行榜** | ZSet（ZADD/ZRANGE）|
| **计数器** | INCR / HINCRBY |
| **限流** | INCR + EXPIRE 或 Lua |
| **分布式锁** | SET NX EX / Redlock |
| **延时队列** | ZSet + 定时扫描 / Streams |
| **消息队列** | Stream（轻量，比 Kafka 简单） |
| **去重** | Set / Bitmap / HyperLogLog |
| **签到** | Bitmap（一年 365 bit = 46B）|
| **地理位置** | Geo（GEOADD/GEORADIUS） |
| **向量检索** | RediSearch + vector 字段 |

### ⚠️ 不推荐场景

- **大对象存储**（图片、视频、大 JSON）→ 用 S3 / 对象存储
- **持久化为主**（强一致 + 不能丢数据）→ 用数据库
- **关系查询** → 用 SQL 数据库
- **海量冷数据**（内存贵）→ 用 PostgreSQL/MySQL/ES

## 五、最佳实践

### 5.1 Key 设计规范

```
✅ 用冒号分层：业务:类型:ID:字段
   user:profile:1001
   order:cart:user_1001
   counter:api:GET:/v1/users

✅ Key 不超过 64 字符（短小、有意义）

❌ 不带 TTL 的 key 越积越多
   永远显式：SET key value EX 3600
```

### 5.2 数据结构选型

```
存对象（已知字段）:        Hash（HSET user:1 name "Tom" age 20）
存对象（JSON 整体）:       String + 序列化
高频读 + 不常变 + 小对象: String 序列化更省
排行榜:                    ZSet
布尔状态/签到:             Bitmap
大量去重计数:              HyperLogLog（误差 < 1%）
精确去重:                  Set / Bloom Filter
消息队列轻量:              Stream
```

### 5.3 内存管理

```ini
# redis.conf
maxmemory 16gb
maxmemory-policy allkeys-lru     # LRU 淘汰所有 key
# 可选：
#  allkeys-lru        所有 key LRU
#  volatile-lru       仅设了 TTL 的 LRU
#  allkeys-lfu        所有 LFU（推荐 4.0+）
#  volatile-ttl       淘汰即将过期
#  noeviction         不淘汰，写入报错

# 重要：永远预留 30% 内存给 fork / AOF rewrite
```

### 5.4 持久化策略

| 模式 | RDB | AOF |
|:---|:---|:---|
| 数据丢失 | 最多丢 N 分钟 | 最多丢 1 秒（everysec） |
| 文件大小 | 小 | 大（可重写） |
| 恢复速度 | 快 | 慢 |
| 推荐组合 | **RDB + AOF 混合（7.0 默认）** | |

```ini
# 7.0+ 默认混合持久化
save 900 1
save 300 10
save 60 10000

appendonly yes
appendfsync everysec
aof-use-rdb-preamble yes
```

### 5.5 高可用方案

| 方案 | 规模 | 说明 |
|:---|:---|:---|
| **单机 + 持久化** | 测试 | 不推荐生产 |
| **主从复制** | 简单容灾 | 手动切换 |
| **Sentinel（哨兵）** | 中小 | 自动 failover，主流 |
| **Cluster（集群）** | 大 | 自带分片 + HA，主流 |
| **Codis / Twemproxy** | 老系统 | Proxy 分片 |
| **云托管** | 任意 | 阿里云 / Tair / Memorystore |

### 5.6 Cluster 关键概念

```
- 16384 个槽位 (slot)，按 CRC16(key) 分配
- 至少 3 主，建议 3 主 3 从
- 客户端必须支持 MOVED / ASK 重定向
- 跨槽事务/Lua 失败 → 用 Hash Tag {user:1001} 强制同槽
```

### 5.7 客户端最佳实践

```
1. 用连接池 (Jedis / lettuce / go-redis / redis-py 都支持)
2. Pipeline 批量执行（10x 性能）
3. 避免 KEYS *，用 SCAN
4. 慎用 MGET 跨 slot
5. 大 key 拆分（单个 value > 10KB 警惕）
6. 慎用 Lua 脚本超 100ms
7. 客户端开启自动重试 + 熔断
8. SUBSCRIBE 用独立连接（会阻塞）
```

### 5.8 分布式锁正确姿势

```python
# ✅ 正确：SET NX EX 原子
ok = r.set("lock:order:1001", token, nx=True, ex=10)
if ok:
    try:
        # 业务
    finally:
        # 释放必须验证 token
        r.eval("if redis.call('get', KEYS[1]) == ARGV[1] then "
               "return redis.call('del', KEYS[1]) else return 0 end",
               1, "lock:order:1001", token)

# ❌ 错误：先 GET 再 DEL 非原子
# ❌ 错误：SETNX + EXPIRE 分两步
```

> 对极致正确性场景用 **Redisson Redlock**，但生产中绝大多数业务单实例 NX EX 已足够。

### 5.9 关键参数（生产 redis.conf 起步）

```ini
# 网络
bind 0.0.0.0
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300

# 内存
maxmemory 16gb
maxmemory-policy allkeys-lfu

# 持久化
save 900 1
appendonly yes
appendfsync everysec

# 复制
repl-backlog-size 256mb
repl-timeout 60

# 多线程 IO（6.0+）
io-threads 4
io-threads-do-reads yes

# 慢日志
slowlog-log-slower-than 10000   # 10ms
slowlog-max-len 1024

# 客户端
maxclients 10000

# 安全
requirepass <strong-password>
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG ""
```

## 六、运维命令速查

```bash
# 信息
INFO                      # 全量
INFO memory               # 内存
INFO replication          # 复制
CLIENT LIST               # 连接数
CLUSTER NODES             # 集群拓扑
CLUSTER INFO

# 性能
SLOWLOG GET 10            # 慢查询
LATENCY DOCTOR            # 延迟诊断
LATENCY HISTORY event

# 内存
MEMORY USAGE key          # 单 key 内存
MEMORY STATS              # 全局
redis-cli --bigkeys       # 大 key 扫描
redis-cli --hotkeys       # 热点 key 扫描

# 调试
DEBUG OBJECT key
OBJECT ENCODING key       # 底层编码

# 备份
BGSAVE                    # 后台 RDB
BGREWRITEAOF              # AOF 重写
LASTSAVE

# 集群
redis-cli --cluster create ...
redis-cli --cluster check
redis-cli --cluster reshard
```

## 七、常见坑

| 坑 | 建议 |
|:---|:---|
| **大 key** | --bigkeys 扫，拆分 |
| **热 key** | 多副本分散、本地缓存 |
| **缓存穿透** | 空值缓存 + 布隆过滤器 |
| **缓存击穿** | 互斥锁 + 永不过期 |
| **缓存雪崩** | TTL 加随机 + 多级缓存 |
| **持久化 fork 卡顿** | 预留内存 + 关 THP |
| **AOF 越来越大** | 自动重写、Mixed 持久化 |
| **跨 slot 操作** | Hash Tag |
| **KEYS 阻塞** | 用 SCAN |
| **客户端不重试** | 启用自动重试 |
| **Sentinel 脑裂** | quorum + min-replicas-to-write |
| **Cluster 单主无从** | 必须配从，否则不可用 |
| **THP 透明大页** | 关闭：`echo never > .../transparent_hugepage/enabled` |

## 八、Redis vs Valkey vs 其他

| 维度 | Redis 7.4+ | Valkey | KeyDB | Dragonfly |
|:---|:---|:---|:---|:---|
| License | SSPL/RSAL | **BSD** | BSD | BSL |
| 协议兼容 | — | 100% | 100% | 100% |
| 多线程 | 部分（IO） | 同 | **全多线程** | **全异步多线程** |
| 性能 | 基线 | 同 | ~3x | **5-25x** |
| 国内主流 | 极高 | 上升中 | 一般 | 上升中 |
| 推荐 | 老系统 | **新建首选** | — | 性能极致 |

## 九、生态与模块

| 模块 | 用途 |
|:---|:---|
| **RedisJSON** | 原生 JSON 文档 |
| **RediSearch** | 全文 + 向量检索 |
| **RedisBloom** | 布隆 / Cuckoo Filter |
| **RedisTimeSeries** | 时序 |
| **RedisGraph**（已停） | 图数据库 |
| **RedisGears** | 流处理 |

## 十、监控指标（必看）

```
吞吐:        instantaneous_ops_per_sec
延迟:        slowlog + LATENCY
内存:        used_memory / used_memory_peak / mem_fragmentation_ratio
连接:        connected_clients / blocked_clients
持久化:      rdb_last_save_time / aof_pending_rewrite
复制:        master_link_status / repl_offset 差距
集群:        cluster_state / failed_nodes / failover

工具:
  Prometheus + redis_exporter
  RedisInsight（官方 GUI + 诊断）
```

## 十一、学习路径

```
1. 基础 9 种数据结构 + 命令
2. 持久化 RDB + AOF 实操
3. 主从 + Sentinel 部署
4. Cluster 6 节点搭建 + 数据分片
5. 缓存设计模式（穿透/雪崩/击穿）
6. 分布式锁 / 限流 / 延时队列
7. Stream 消息队列
8. 性能调优 + 大 key/热 key 处理
9. 模块 (RediSearch/RedisJSON)
10. 进阶：Valkey 迁移、KeyDB/Dragonfly 评估
```

## 十二、信创替代

| 产品 | 厂商 | 说明 |
|:---|:---|:---|
| **Tair** | 阿里云 | Redis 兼容，企业级 |
| **腾讯云 CRedis** | 腾讯 | 同上 |
| **OceanBase KVCache** | 蚂蚁 | 大规模 KV |
| **Pika** | 360 开源 | RocksDB 后端，省内存 |
| **Kvrocks** | 苹果开源（来自 Bilibili） | RocksDB 后端 |

> 📖 **核心判断**：Redis 仍是缓存/会话/计数器的事实标准。**新建项目可优先考虑 Valkey**（完全兼容、license 干净）。**性能极致诉求看 Dragonfly**。**内存贵的大数据冷热分层用 Pika/Kvrocks**。
