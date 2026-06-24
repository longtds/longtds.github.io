# HBase

> Hadoop 生态里的"分布式 KV 数据库"。**海量数据下高并发随机读写的代表**——风控、画像、消息、IM、监控指标、车联网……至今难以被替代。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2006 | Google 发表 **BigTable 论文** |
| 2007 | Powerset 公司启动 HBase（参考 BigTable）|
| 2008 | Apache 顶级项目 |
| 2010 | 0.20 稳定，国内开始大规模使用 |
| 2015 | 1.0 GA |
| 2018 | 2.0 引入 In-Memory Compaction、Async API |
| 2020 | 2.4 / 2.5 性能优化 |
| 2023 | **3.0 准备发布**，去 ZooKeeper |
| 2024 | 与 K8s / 对象存储集成增强 |
| 2025 | Phoenix 5 + Kudu + Doris 蚕食部分场景 |

**主流版本**：2.4.x / 2.5.x。

## 二、HBase 是什么

```
"分布式、面向列族的 NoSQL 数据库"

核心特点:
  - 基于 HDFS（数据安全靠 HDFS 副本）
  - LSM-Tree 存储（写优于读）
  - 行键有序 + 自动分区 (Region)
  - 强一致（CP 系统）
  - 万亿行 + PB 级数据
  - 毫秒级随机读写

不是:
  ❌ SQL 数据库（没事务、没多表 JOIN）
  ❌ OLAP 引擎（不擅长聚合扫描）
  ❌ 关系数据库（无外键、无索引）
```

## 三、数据模型

```
Table → Region → Store → MemStore + HFile
                  ↑
            ColumnFamily

行键 (Row Key) | Column Family | Column Qualifier | Timestamp | Value
   user:001    |     info      |       name       |     t1    |  Alice
   user:001    |     info      |       age        |     t1    |   28
   user:001    |     stat      |       login      |     t2    | 2026-01-01

特点:
  - 行键决定一切（决定排序 + 分布）
  - 列族物理隔离（HFile 一个 CF 一组）
  - 同一行键不同时间戳 = 版本
  - Schemaless 列（同 CF 不同行可不同列）
  - 稀疏（不存的列不占空间）
```

## 四、架构原理

```
┌──────────── 客户端 ──────────────┐
│ HBase Java/Thrift/REST API       │
│ Phoenix (SQL Layer)              │
└──────────────┬───────────────────┘
               ↓
┌──────────── ZooKeeper ───────────┐
│ Master 选举 + Meta 表位置        │
│ (3.0 用 hbase:meta 自管)         │
└──────────────┬───────────────────┘
               ↓
┌──────────── HMaster ─────────────┐
│ Region 分配 / DDL / 负载均衡      │
└──────────────┬───────────────────┘
               ↓
┌────── RegionServer × N ──────────┐
│ MemStore (内存写)                 │
│ BlockCache (内存读)              │
│ HFile (HDFS 上)                  │
│ WAL (HDFS 上)                    │
└──────────────┬───────────────────┘
               ↓
┌──────────── HDFS ────────────────┐
│ HFile + WAL                      │
│ 3 副本 / EC                      │
└──────────────────────────────────┘
```

### 关键机制

| 机制 | 作用 |
|:---|:---|
| **LSM-Tree** | 写内存（MemStore），定期 flush 成 HFile |
| **MemStore** | 内存写缓冲（per CF per Region） |
| **HFile** | 不可变文件，Compaction 合并 |
| **WAL（HLog）** | 写前日志，崩溃恢复 |
| **BlockCache** | 读缓存 |
| **Compaction** | Minor + Major（合并小文件、清理 tombstone） |
| **Region Split** | 大 Region 自动拆分 |
| **Bloom Filter** | 加速点查 |

## 五、核心功能

```
1. 海量行（万亿+）
2. 高并发随机读写（毫秒级）
3. 强一致（单行强一致）
4. 数据多版本
5. 自动分片（Region Split）
6. Scan 范围查询（按行键有序）
7. Bloom Filter 加速
8. 协处理器 Coprocessor（类似存储过程）
9. Phoenix SQL 层
10. 与 Hive / Spark / Flink 集成
11. 备份恢复（Snapshot / Replication）
12. 列级 TTL
```

## 六、使用场景

### ✅ 完美匹配

| 场景 | 说明 |
|:---|:---|
| **风控画像** | 用户 KV 实时查询 |
| **消息/IM 存储** | 微信、钉钉、QQ 历史消息 |
| **监控指标** | OpenTSDB 底层 |
| **车联网/物联网** | 设备时序数据 |
| **订单/日志归档** | 海量历史回查 |
| **稀疏宽表** | 每行 100-10000 列 |
| **实时计算结果存储** | Flink → HBase |
| **会话存储** | 高并发读写 |

### ⚠️ 不推荐

- **强事务 + 多表 JOIN** → 关系数据库
- **复杂 SQL 分析** → ClickHouse / Doris
- **小数据量** → MySQL / PG
- **聚合多** → OLAP 数据库
- **需要二级索引精确查** → Phoenix 或别用 HBase

## 七、HBase vs 其他 NoSQL

| 维度 | HBase | Cassandra | MongoDB | TiKV | Redis | Kudu |
|:---|:---|:---|:---|:---|:---|:---|
| 模型 | 列族 KV | 列族 KV | 文档 | KV | KV | 列存 |
| 一致性 | **CP 强** | AP 最终 | 可配 | **CP 强** | 单点强 | CP |
| 海量数据 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| 写吞吐 | 极高 | 极高 | 高 | 高 | 极高 | 高 |
| 读延迟 | 毫秒 | 毫秒 | 毫秒 | 毫秒 | 微秒 | 毫秒 |
| OLAP 能力 | 弱 | 弱 | 弱 | 弱 | 弱 | **中** |
| 国内主流 | 高 | 中 | 高 | 上升 | 极高 | 中 |
| 适合 | 海量稀疏宽表 | 跨数据中心 | JSON 文档 | NewSQL 底层 | 缓存 | HTAP |

## 八、最佳实践

### 8.1 行键设计（最重要）

```
✅ 散列 + 业务有序
  
原则:
  1. 散列前缀: 避免热点（散列函数或反转时间戳）
  2. 业务前缀: 利于范围扫描
  3. 长度: 推荐 8-32 字节
  4. 二进制紧凑: bytes 优于字符串

模式:
  hash(user_id)[0:2] + user_id + timestamp_reversed
  region_id + user_id + event_type

❌ 不要:
  纯时间戳前缀 → 单 Region 热点
  自增 ID 前缀 → 顺序热点
  超长 string (> 100B) → HFile 膨胀
```

### 8.2 列族设计

```
✅ 列族越少越好（1-3 个）
✅ 同一列族的列访问频率相似
✅ 命名短（CF 名每行都存）

示例:
  CF 'i' = info（高频，必读）
  CF 'd' = detail（低频，按需读）
  CF 's' = stat（统计，定期写）

❌ 列族 > 3
❌ 列族命名长（"user_info" 比 'i' 浪费 700%）
```

### 8.3 预分区（必做）

```
✅ 建表时按行键散列预分区
   避免新表插入挤爆单 Region

create 'events', 'cf',
  {SPLITS => ['1', '2', '3', '4', '5', '6', '7', '8', '9']}

或:
  {NUMREGIONS => 100, SPLITALGO => 'HexStringSplit'}
```

### 8.4 关键参数

```xml
<!-- hbase-site.xml -->
<!-- 内存 -->
<property>
  <name>hbase.regionserver.global.memstore.size</name>
  <value>0.4</value>             <!-- 40% RS 堆 -->
</property>
<property>
  <name>hfile.block.cache.size</name>
  <value>0.4</value>             <!-- 40% RS 堆 -->
</property>

<!-- Region -->
<property>
  <name>hbase.hregion.memstore.flush.size</name>
  <value>134217728</value>       <!-- 128MB -->
</property>
<property>
  <name>hbase.hregion.max.filesize</name>
  <value>10737418240</value>     <!-- 10GB Region 大小 -->
</property>

<!-- Compaction -->
<property>
  <name>hbase.hstore.compaction.min</name>
  <value>3</value>
</property>
<property>
  <name>hbase.hstore.compaction.max</name>
  <value>10</value>
</property>

<!-- WAL -->
<property>
  <name>hbase.regionserver.logroll.period</name>
  <value>3600000</value>         <!-- 1h -->
</property>

<!-- 客户端 -->
<property>
  <name>hbase.client.write.buffer</name>
  <value>2097152</value>         <!-- 2MB -->
</property>
```

### 8.5 JVM 调优

```
RegionServer 堆:
  20-30GB（不要超 32GB 指针压缩）

GC:
  -XX:+UseG1GC
  -XX:MaxGCPauseMillis=100
  -XX:G1HeapRegionSize=32m
  -XX:InitiatingHeapOccupancyPercent=65

堆外 BucketCache:
  -XX:MaxDirectMemorySize=20g
  hbase.bucketcache.size=20480
  hbase.bucketcache.ioengine=offheap
```

### 8.6 读写优化

```
写优化:
  ✅ 客户端批量 put (1000-10000 rows)
  ✅ 关闭 WAL（仅日志类可忽略丢失）
  ✅ 预分区
  ✅ MemStore 大点（flush 少）
  ✅ Bulk Load（HFile 直接装载，最快）

读优化:
  ✅ BlockCache 大 + 堆外
  ✅ Bloom Filter（ROW or ROWCOL）
  ✅ DATA_BLOCK_ENCODING (FAST_DIFF/PREFIX)
  ✅ COMPRESSION (SNAPPY/LZ4/ZSTD)
  ✅ 短列名 / 短行键
  ✅ Scan 加 filter + caching
```

### 8.7 表配置示例

```bash
create 'events',
  {NAME => 'i',
   VERSIONS => 1,
   COMPRESSION => 'ZSTD',
   DATA_BLOCK_ENCODING => 'FAST_DIFF',
   BLOOMFILTER => 'ROW',
   IN_MEMORY => false,
   TTL => 7776000,                        # 90 天
   BLOCKSIZE => 65536},                   # 64K
  {SPLITS => ['1','2','3','4','5','6','7','8','9']}
```

### 8.8 高可用

```
HMaster HA: 2 个 Master（无状态）
RegionServer: 多个，挂了 Region 自动迁移（30s）
HDFS: 3 副本保数据
WAL: 写两份 (双 cluster)
ZooKeeper: 3 或 5 节点
Replication: 跨集群异步复制
```

### 8.9 备份

```bash
# 1. 快照（推荐）
hbase> snapshot 'events', 'events-snap-20260622'
hbase> list_snapshots
hbase> clone_snapshot 'events-snap-...', 'events_new'
hbase> restore_snapshot 'events-snap-...'

# 2. Export / Import
hbase org.apache.hadoop.hbase.mapreduce.Export events /backup/events
hbase org.apache.hadoop.hbase.mapreduce.Import events /backup/events

# 3. Replication（跨集群异步）
add_peer '1', CLUSTER_KEY => "zk1,zk2,zk3:2181:/hbase"
enable_table_replication 'events'
```

### 8.10 Phoenix（SQL 层）

```sql
-- Phoenix 给 HBase 装 SQL/二级索引
CREATE TABLE events (
  user_id BIGINT NOT NULL,
  ts TIMESTAMP NOT NULL,
  event STRING,
  CONSTRAINT pk PRIMARY KEY (user_id, ts)
);

CREATE INDEX idx_event ON events(event);

UPSERT INTO events VALUES (...);
SELECT * FROM events WHERE user_id = 1001 AND ts > NOW() - 1;
```

## 九、运维命令速查

```bash
# 进入 shell
hbase shell

# 表管理
> list
> describe 'events'
> create 'events', 'cf'
> alter 'events', NAME => 'cf', VERSIONS => 5
> disable 'events' / enable / drop
> count 'events', INTERVAL => 1000

# 数据
> put 'events', 'rk1', 'cf:col', 'value'
> get 'events', 'rk1'
> scan 'events', {LIMIT => 10, STARTROW => 'rk1', STOPROW => 'rk9'}
> delete 'events', 'rk1', 'cf:col'

# Region
> regions 'events'
> split 'events', 'splitkey'
> major_compact 'events'
> move 'region_id', 'target_rs'
> balancer
> balance_switch true

# 状态
> status
> status 'detailed'
> rsgroup_list

# 排查
hbase hbck                              # 老
hbase hbck2                             # 新（推荐）
hbase org.apache.hadoop.hbase.tool.LoadIncrementalHFiles ...
```

## 十、常见坑

| 坑 | 建议 |
|:---|:---|
| **行键热点** | 散列前缀 / 反转时间 |
| **新表未预分区** | 必预分区 |
| **列族过多** | ≤ 3 |
| **小文件多** | Major Compact 定期 |
| **GC 卡顿** | G1GC + 堆 < 32GB + 堆外 Cache |
| **RegionServer OOM** | MemStore + BlockCache 比例 |
| **Compaction 风暴** | 错峰 + 限速 |
| **Region 太大或太多** | 单表 10-500 Region/RS |
| **WAL 拖慢** | 多 WAL + SSD 专盘 |
| **Major Compact 卡业务** | 关闭自动 + 凌晨定时 |
| **跨集群 Replication 滞后** | 监控 + 加 RPC |
| **Phoenix 索引膨胀** | 慎建 + 监控 |
| **Scan 全表** | 永远加 STARTROW/STOPROW + LIMIT |
| **没有备份** | Snapshot 定期 + 异地 |

## 十一、生态与工具

| 工具 | 用途 |
|:---|:---|
| **HBase Shell** | 官方 CLI |
| **Phoenix** | SQL 层 + 二级索引 |
| **OpenTSDB** | 时序，HBase 底层 |
| **Atlas** | 元数据管理 |
| **HBase REST / Thrift** | 多语言接入 |
| **Spark on HBase** | 批处理读写 |
| **Flink HBase Connector** | 流处理写 |
| **HBase BulkLoad** | 离线高速导入 |
| **Cloudera Manager / Ambari** | 集群管理 |

## 十二、监控指标

```
RegionServer:
  Read/Write Request Count
  Read/Write Latency p99
  MemStore Size / FlushQueueSize
  BlockCacheHitRatio
  CompactionQueueSize
  GC time / heap

Master:
  RegionsInTransition
  Active Master / Backup
  RSDeadCount

集群:
  Region 数量 / 平衡度
  HDFS 使用率
  WAL 大小

工具:
  Prometheus + jmx_exporter
  Ganglia / Cloudera Manager
  Grafana HBase Dashboard
```

## 十三、HBase 在 K8s

```
方案 1: StatefulSet + 持久卷
  - 数据存 PVC
  - 与 HDFS-on-K8s 共存
  - 维护复杂

方案 2: Operator
  - apache-hbase-operator（社区）
  - 商业: Cloudera CDP Operator

方案 3: 云托管
  - 阿里云 HBase / Lindorm
  - 腾讯云 HBase
  - AWS Emr HBase / DynamoDB
```

## 十四、HBase vs 替代方案

```
HBase 仍最适合:
  - 海量行 + 稀疏宽表
  - 强一致 + 高并发 KV
  - 数据生命周期长（年级）

何时改其他:
  - 需要 SQL + 二级索引广泛 → TiDB / OceanBase
  - 实时分析 + 写入 → Doris / StarRocks / Kudu
  - 多模/多数据类型 → MongoDB / Lindorm
  - 强事务 → TiKV / Spanner
  - 时序专用 → InfluxDB / TDengine / VictoriaMetrics
```

## 十五、国产替代

| 产品 | 厂商 | 说明 |
|:---|:---|:---|
| **Lindorm** | 阿里云 | HBase 兼容增强 |
| **TBase / TencentDB HBase** | 腾讯 | 托管 |
| **GoldenDB-HBase** | 中兴 | 信创 |
| **Kudu** | Cloudera | HTAP 列存 |
| **TiKV** | PingCAP | 分布式 KV NewSQL |
| **OceanBase KVCache** | 蚂蚁 | 大规模 KV |

## 十六、学习路径

```
入门:
  1. 单机 HBase + 跑 shell 命令
  2. 理解行键 / 列族 / Region
  3. 装 ZooKeeper + 伪分布式

进阶:
  4. 3 节点集群 + HDFS
  5. 行键设计 + 预分区
  6. JVM + 内存调优
  7. Compaction 实战
  8. Phoenix SQL

高阶:
  9. Spark / Flink 集成
  10. Replication 跨集群
  11. 备份恢复演练
  12. 性能压测 (YCSB)
  13. K8s 部署
```

## 十七、未来展望

```
1-2 年:
  - HBase 3.0 发布（去 ZK 内置 quorum）
  - 与 K8s / 对象存储深度集成
  - Phoenix 继续演进

3-5 年:
  - 部分场景被 Lindorm/Kudu/TiKV 替代
  - 海量稀疏宽表仍是 HBase 主战场
  - 国产化版本接管私有化市场

5 年+:
  - 与数据湖融合（HBase + Iceberg）
  - 多模化（KV + Time-Series + Wide-Column）
```

> 📖 **核心判断**：**海量稀疏宽表 + 高并发强一致 KV**——HBase 至今仍是工业级最稳的选择。短期内难以被替代，但 Lindorm / Kudu / TiKV 在细分场景已构成挑战。行键设计是 HBase 的"灵魂"，几乎所有坑都源于行键设计错误。
