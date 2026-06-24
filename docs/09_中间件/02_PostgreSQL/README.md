# PostgreSQL

> "世界上最先进的开源关系型数据库"（官方 slogan）。功能比 MySQL 强大，扩展性堪称恐怖，**正在成为 MySQL 之后的新一代默认选项**。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 1986 | UC Berkeley 教授 Michael Stonebraker 启动 POSTGRES 项目 |
| 1995 | 改用 SQL 接口，更名 Postgres95 |
| 1996 | 正式更名 **PostgreSQL**，开源社区接管 |
| 2010 | 9.0 引入流复制（streaming replication） |
| 2017 | 10.0 逻辑复制 GA |
| 2019 | 12 性能大跃进 |
| 2021 | 14 引入 JIT 默认开启 |
| 2022 | 15 引入 MERGE 语句 |
| 2023 | **16 大幅强化并行查询和逻辑复制** |
| 2024 | **17 LTS** 增量备份、逻辑复制故障转移 |
| 2025 | 18 进一步优化 OLTP |

**版本规律**：每年 9-10 月发新主版本，**每个版本支持 5 年**。

## 二、核心功能

```
1. 完整 ACID + MVCC（行级锁极少）
2. 丰富数据类型：JSON/JSONB、Array、Range、UUID、HSTORE、PostGIS 地理
3. 强大索引：B-Tree、Hash、GiST、SP-GiST、GIN、BRIN、Bloom
4. 窗口函数 / CTE / 递归查询 / MERGE / LATERAL
5. 表分区（声明式）+ 表继承
6. 全文检索（内置 tsvector/tsquery）
7. 流复制 + 逻辑复制（解耦订阅）
8. 外部数据 Foreign Data Wrapper (FDW)
9. 存储过程 PL/pgSQL、PL/Python、PL/V8
10. 扩展插件机制（CREATE EXTENSION）
```

## 三、PostgreSQL 杀手特性

### 3.1 JSONB（杀手锏）

```sql
-- JSONB 是二进制 JSON，可索引、可查询、可更新
CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  data JSONB NOT NULL
);

CREATE INDEX idx_events_gin ON events USING GIN (data);

-- 查询
SELECT * FROM events WHERE data @> '{"type":"login"}';
SELECT data->>'user_id' FROM events;

-- 性能接近原生列，比 MongoDB 稳定
```

### 3.2 扩展生态（无敌）

| 扩展 | 用途 |
|:---|:---|
| **PostGIS** | 地理空间，全球最强 GIS 后端 |
| **TimescaleDB** | 时序数据库 |
| **pgvector** | **AI 向量检索**（RAG 必备）|
| **Citus** | 分布式 PG（水平扩展）|
| **pg_stat_statements** | SQL 统计 |
| **pg_partman** | 自动分区管理 |
| **pg_cron** | 定时任务 |
| **pg_bigm / pg_trgm** | 中文/模糊检索 |
| **AGE** | 图数据库 |
| **wal2json** | CDC 输出 |

### 3.3 索引类型（远超 MySQL）

| 索引 | 适合 |
|:---|:---|
| B-Tree | 通用（默认） |
| Hash | 等值 |
| **GiST** | 几何、全文、范围 |
| **GIN** | JSONB、数组、全文 |
| **BRIN** | 超大时序表（小但快） |
| SP-GiST | 非平衡空间 |
| Bloom | 多列等值 |

### 3.4 pgvector + RAG

```sql
CREATE EXTENSION vector;
CREATE TABLE docs (id BIGSERIAL, embedding vector(1536));
CREATE INDEX ON docs USING ivfflat (embedding vector_cosine_ops);

-- 检索最相似的 5 条
SELECT id FROM docs ORDER BY embedding <=> '[0.1, 0.2, ...]' LIMIT 5;
```

> 💡 这是 PG 在 LLM/RAG 时代爆火的核心原因——**一套数据库同时搞定关系数据 + 向量检索**。

## 四、架构原理

```
┌─────────── postmaster (主进程) ───┐
│  监听端口、Fork 子进程              │
└──────────────┬────────────────────┘
   ┌────────┬──┴───┬─────────┐
   ↓        ↓      ↓         ↓
Backend  WAL    Checkpoint  AutoVacuum
(每连接一个进程)
   ↓
┌─────────── 共享内存 ─────────────┐
│ Shared Buffers / WAL Buffers     │
└──────────────┬───────────────────┘
   ↓
┌─────────── 物理存储 ─────────────┐
│ base/*  (表/索引)                │
│ pg_wal/* (WAL 日志)              │
│ pg_xact/* (事务状态)             │
└──────────────────────────────────┘
```

### 关键机制

| 机制 | 作用 |
|:---|:---|
| **MVCC** | 旧版本不删除，事务提交后由 VACUUM 清理 |
| **WAL** | 写前日志，崩溃恢复 + 复制基础 |
| **AutoVacuum** | 自动回收死元组（必须健康运行）|
| **HOT Update** | 同页更新无需更新索引 |
| **TOAST** | 大字段独立存储 |
| **进程模型** | 每连接一个进程（重，需要 PgBouncer） |

## 五、PostgreSQL vs MySQL

| 维度 | MySQL | PostgreSQL |
|:---|:---|:---|
| **设计哲学** | 简单实用 | 学院派、严谨 |
| **事务隔离** | 默认 RR | 默认 RC（更标准） |
| **MVCC** | Undo Log | 多版本元组 |
| **JSON 支持** | JSON 列 | **JSONB 完整生态** |
| **索引类型** | 5 种 | 10+ 种 |
| **复制** | binlog 主从 | WAL 流复制 + 逻辑复制 |
| **存储过程** | 弱 | 强（PL/* 多语言） |
| **GIS** | 弱 | **PostGIS 全球最强** |
| **向量检索** | ❌ | **pgvector** |
| **分布式** | 需分库分表 | Citus 一行扩展 |
| **进程模型** | 线程（轻） | 进程（重，需池） |
| **生态** | 极广 | 快速增长 |
| **学习曲线** | 平缓 | 陡峭（功能多） |
| **国内主流度** | 极高 | 快速上升 |

> 💡 **2025 年新建项目，PG 已经是大厂技术圈的默认选项**，MySQL 仍是兼容性最广的选择。

## 六、使用场景

### ✅ 强烈推荐

- **复杂业务系统**：财务、ERP、CRM、政务
- **GIS 地理空间**：地图、物流、轨迹
- **JSONB 半结构化**：替代 MongoDB
- **AI / 向量检索（RAG）**：pgvector
- **时序数据**：TimescaleDB 扩展
- **分析型查询混合 OLTP**（HTAP 轻量）
- **数据安全要求高**：行级安全 RLS
- **多租户 SaaS**：Schema 隔离 + RLS

### ⚠️ 不推荐 / 需慎选

- **简单 Web 应用 / MySQL 生态深度依赖** → MySQL 兼容性更广
- **超大单表 OLTP（亿级以上）** → TiDB / 分库分表
- **重 OLAP 分析** → ClickHouse / Doris
- **海量短连接** → 必须配 PgBouncer

## 七、最佳实践

### 7.1 表设计

```sql
-- 自增主键用 BIGSERIAL 或 IDENTITY（PG 10+）
CREATE TABLE orders (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL,
  amount NUMERIC(12,2) NOT NULL,
  status SMALLINT NOT NULL DEFAULT 0,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_user_created ON orders (user_id, created_at DESC);
CREATE INDEX idx_orders_metadata ON orders USING GIN (metadata);

-- 时间用 TIMESTAMPTZ，不用 TIMESTAMP
-- 金额用 NUMERIC，不用 FLOAT
-- 半结构化用 JSONB，不要用 JSON
```

### 7.2 索引选型

```
等值查询：     B-Tree
范围查询：     B-Tree + BRIN（大表时序）
JSONB 包含：    GIN
全文检索：     GIN tsvector
模糊匹配：     pg_trgm GIN
地理：         GiST / SP-GiST
向量：         ivfflat / hnsw (pgvector)
```

### 7.3 关键参数（生产 postgresql.conf 起步）

```ini
# 内存
shared_buffers = 8GB             # 物理内存的 25%
effective_cache_size = 24GB      # 物理内存的 60-75%
work_mem = 32MB                  # 每个排序/Hash
maintenance_work_mem = 1GB

# WAL
wal_level = replica              # 主从用 replica，逻辑复制 logical
max_wal_size = 16GB
checkpoint_timeout = 15min
synchronous_commit = on

# 复制
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on

# 并行
max_worker_processes = 16
max_parallel_workers = 8
max_parallel_workers_per_gather = 4

# 自动 VACUUM
autovacuum = on
autovacuum_naptime = 30s
autovacuum_vacuum_scale_factor = 0.1

# 日志
log_min_duration_statement = 500   # 慢查询 ms
log_checkpoints = on
log_lock_waits = on
```

### 7.4 高可用方案

| 方案 | 适合 | 说明 |
|:---|:---|:---|
| **流复制 + Patroni** | 中大 | **首选**，自动 failover |
| **repmgr** | 中小 | 经典开源 |
| **pg_auto_failover** | 中 | Citus 团队出品 |
| **Citus** | 大 | 水平分片 |
| **Stolon** | 中 | etcd 协调 |
| **CloudNativePG (CNPG)** | K8s | CNCF 项目，K8s 原生 |
| **PolarDB-PG** | 云上 | 阿里云 |

### 7.5 连接池（必装）

```
PG 一连接一进程 → 高并发会爆 → 必须连接池

PgBouncer:   最主流、轻量
  Pool Mode: transaction（推荐）
  
Pgpool-II:   功能多但坑多
Pgcat:       Rust 写的新势力，多租户友好
```

### 7.6 备份策略

```
逻辑备份：  pg_dump / pg_dumpall（小库）
物理备份：  pg_basebackup（全量）
增量：     pgBackRest / Barman / WAL-G（推荐 pgBackRest）
PITR：     WAL 持续归档 + 全量基线
异地：     备份上 S3/OSS，多版本保留
```

## 八、运维命令速查

```sql
-- 连接信息
SELECT * FROM pg_stat_activity WHERE state != 'idle';

-- 锁
SELECT * FROM pg_locks WHERE NOT granted;
SELECT pg_blocking_pids(pid) FROM pg_stat_activity WHERE wait_event_type = 'Lock';

-- 复制
SELECT * FROM pg_stat_replication;       -- 主库看
SELECT * FROM pg_stat_wal_receiver;      -- 从库看

-- 表大小
SELECT relname,
       pg_size_pretty(pg_total_relation_size(oid)) AS size
FROM pg_class
WHERE relkind='r'
ORDER BY pg_total_relation_size(oid) DESC LIMIT 20;

-- 慢查询（pg_stat_statements）
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 20;

-- VACUUM
VACUUM ANALYZE orders;
SELECT relname, last_vacuum, last_autovacuum FROM pg_stat_user_tables;

-- 索引利用率
SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;  -- 没用过的索引
```

## 九、常见坑

| 坑 | 建议 |
|:---|:---|
| **死元组堆积** | AutoVacuum 必须开 + 监控 |
| **未连接池直连** | 必须装 PgBouncer |
| **VACUUM Full 锁表** | 用 pg_repack / pg_squeeze |
| **大表 ALTER** | 拆步骤、避免重写 |
| **时区混乱** | TIMESTAMPTZ + 服务端 UTC |
| **Replication Slot 撑爆磁盘** | 监控 slot 滞后 + 不用就 DROP |
| **统计信息过期** | ANALYZE 定期手工或自动 |
| **WAL 满盘** | 监控 + archive_command 健康 |
| **OOM Killer** | work_mem × max_connections 估算合理 |
| **JSON 当 JSONB 用** | 永远用 JSONB |
| **大事务长锁** | 拆事务 / 设 statement_timeout |
| **缺主键的表** | 必须有主键，否则逻辑复制崩 |

## 十、生态工具

| 工具 | 用途 |
|:---|:---|
| **psql** | 官方 CLI |
| **pgAdmin** | 官方 GUI |
| **DBeaver / DataGrip** | 通用 GUI |
| **PgBouncer** | 连接池 |
| **pgBackRest** | 备份恢复 |
| **Patroni** | 高可用 |
| **CloudNativePG** | K8s 原生 |
| **pg_stat_statements** | SQL 统计 |
| **pg_repack** | 在线整理表 |
| **pgloader** | 数据迁移（MySQL → PG）|
| **Citus** | 水平分片 |
| **Debezium / wal2json** | CDC 同步 |

## 十一、信创替代

| 数据库 | 兼容协议 |
|:---|:---|
| **人大金仓 KingbaseES** | PG 兼容（信创主力） |
| **海量 Vastbase** | PG 兼容 |
| **瀚高 HighGo** | PG 兼容 |
| **openGauss / MogDB** | 华为系，源自 PG 9.2 |
| **PolarDB-PG** | 阿里云 |
| **TiDB** | MySQL 兼容（不是 PG）|

## 十二、学习路径

```
1. 基础：SQL + psql + 数据类型
2. 索引：理解 B-Tree / GIN / BRIN
3. JSONB：替代 NoSQL
4. 复制：流复制 + 逻辑复制
5. 扩展：PostGIS / pgvector / TimescaleDB
6. 高可用：Patroni 部署
7. 性能：EXPLAIN / pg_stat_statements
8. 备份：pgBackRest 全流程
9. 进阶：FDW / PL/Python / Citus 分片
10. K8s：CloudNativePG
```

> 📖 **核心判断**：从 2024 年开始，**新项目优先选 PostgreSQL**。除非你的整个生态都绑死 MySQL，或者需要极致的 OLTP 兼容（如老 PHP 项目）。PG 的 JSONB + pgvector + PostGIS 三件套，能让你**一套数据库吃掉 MySQL + MongoDB + Redis 部分场景 + 向量库 + GIS**。
