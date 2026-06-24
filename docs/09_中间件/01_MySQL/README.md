# MySQL

> 全球用得最广的开源关系型数据库。互联网公司的"默认选项"，几乎每个后端工程师的入门数据库。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 1995 | Michael Widenius 在瑞典 MySQL AB 公司发布 MySQL 1.0 |
| 2008 | Sun 以 10 亿美元收购 MySQL AB |
| 2010 | Oracle 收购 Sun，MySQL 归 Oracle |
| 2010 | 原作者 Monty 出走，**Fork 成 MariaDB**（社区担心 Oracle 闭源） |
| 2013 | MySQL 5.6（GTID 复制） |
| 2016 | MySQL 5.7（JSON 列、原生复制增强） |
| 2018 | **MySQL 8.0**（窗口函数、CTE、Roles、Atomic DDL） |
| 2023 | MySQL 8.0 进入 Innovation Release 模式 |
| 2024 | MySQL **8.4 LTS** 发布（首个 LTS 版） |
| 2024 | 阿里 OceanBase、PingCAP TiDB 开始大规模替代 MySQL |

**当前主流版本**：MySQL 8.0 / 8.4 LTS、MariaDB 11.x。新项目优先 8.4 LTS。

## 二、核心功能

```
1. ACID 事务（InnoDB）
2. 行级锁 + MVCC（高并发）
3. 主从复制（异步/半同步/组复制）
4. 分区表（按范围/Hash/List）
5. 多存储引擎插拔（InnoDB 主流，MyISAM 已过时）
6. JSON 列原生支持（8.0+）
7. 窗口函数 / CTE / 公共表达式（8.0+）
8. 不可见索引、隐藏列、原子 DDL（8.0+）
9. SSL/TLS 加密传输
10. 资源组（CPU 隔离）
```

## 三、架构原理

```
┌─────────── Server 层 ────────────┐
│ 连接器 → 查询缓存 → 解析器        │
│       → 优化器  → 执行器          │
└──────────────┬──────────────────┘
               ↓
┌─────────── 存储引擎层（可插拔）──┐
│ InnoDB (主流)、MyISAM、Memory   │
│ NDB Cluster、Archive、CSV …     │
└──────────────┬──────────────────┘
               ↓
┌─────────── 物理存储 ─────────────┐
│ ibdata / *.ibd / redo / undo / bin-log │
└─────────────────────────────────┘
```

### InnoDB 关键机制

| 机制 | 作用 |
|:---|:---|
| **Buffer Pool** | 内存缓存表/索引数据，命中率 > 99% 是底线 |
| **Redo Log** | 物理日志，崩溃恢复（WAL）|
| **Undo Log** | 回滚 + MVCC 旧版本 |
| **Change Buffer** | 二级索引的写缓冲，提升写性能 |
| **Doublewrite Buffer** | 防止页面写半损坏 |
| **Adaptive Hash Index** | 自动为热点页建哈希索引 |
| **Binlog** | 主从复制 + 审计基础 |

## 四、使用场景

### ✅ 强烈推荐

- **OLTP 在线事务**：电商订单、支付、用户系统
- **中小规模 Web 应用**：单库 < 1TB / QPS < 5 万
- **多读少写**：通过从库扩展读
- **Java/PHP/Python 生态**：连接器和 ORM 极成熟
- **MHA / 半同步主从架构**

### ⚠️ 不推荐 / 需慎选

- **超大规模 OLTP**（单表 > 1 亿行频繁 OLAP）→ 用 TiDB / OceanBase / 分库分表
- **复杂分析查询**（GROUP BY + JOIN 大表）→ 用 ClickHouse / Doris
- **强一致分布式**（跨可用区强一致）→ 用 TiDB / OceanBase / Spanner
- **高写入吞吐**（百万 TPS+）→ 用 Kafka 缓冲 + 异步写入
- **图谱关系深度查询**（多跳）→ 用 Neo4j / Nebula

## 五、最佳实践

### 5.1 表设计

```sql
-- 1. 主键用 BIGINT UNSIGNED AUTO_INCREMENT，避免 UUID 主键
-- 2. 所有表带 created_at / updated_at
-- 3. NOT NULL + 显式 DEFAULT 是默认
-- 4. 字符集统一 utf8mb4，排序规则 utf8mb4_0900_ai_ci

CREATE TABLE orders (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  status TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  KEY idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5.2 索引

```
✅ 高选择性列建索引（用户ID、订单号、手机号）
✅ 联合索引遵循"最左前缀"原则
✅ 覆盖索引：SELECT 列全在索引中
✅ 区分度低（性别、状态）单独建索引 = 浪费
❌ 大字段(TEXT/BLOB) 不建索引
❌ 函数索引会让普通索引失效 → 改 generated column
```

### 5.3 SQL 规范

```sql
-- 1. 避免 SELECT *
-- 2. 拒绝隐式类型转换 WHERE id = '123'
-- 3. JOIN 控制在 3 张表内
-- 4. 大批量 UPDATE/DELETE 分批
DELETE FROM logs WHERE created_at < '2024-01-01' LIMIT 1000;
-- 5. LIKE 'xxx%' 可用索引，'%xxx' 不可
-- 6. 子查询尽量改 JOIN
-- 7. 大事务（行数 > 1万、时间 > 1s）分批
```

### 5.4 主从复制

```
推荐方案: 1 主 + 2 从 + MHA / Orchestrator 自动故障转移
复制模式: 半同步 (After_Sync) 防丢数据
GTID:    必开（8.0 默认开）
binlog_format: ROW
sync_binlog: 1
innodb_flush_log_at_trx_commit: 1
```

### 5.5 高可用方案

| 方案 | 适合规模 | 特点 |
|:---|:---|:---|
| MHA + 半同步 | 中小 | 经典、需脚本 |
| **Orchestrator** | 中大 | GitHub 出品，主流 |
| MGR（Group Replication） | 中 | 官方多主，国内用得少 |
| InnoDB Cluster | 中 | 官方一体化方案 |
| **TiDB / OceanBase** | 大 | 强一致分布式 |
| 阿里 PolarDB / 腾讯 TDSQL | 云上 | 计算存储分离 |

### 5.6 关键参数（生产 my.cnf 起步）

```ini
[mysqld]
# 内存（按机器 60-70% 配 Buffer Pool）
innodb_buffer_pool_size = 32G
innodb_buffer_pool_instances = 8

# 日志
innodb_log_file_size = 2G
innodb_log_buffer_size = 64M
innodb_flush_log_at_trx_commit = 1
sync_binlog = 1
binlog_format = ROW
binlog_expire_logs_seconds = 604800

# 连接
max_connections = 2000
max_connect_errors = 1000

# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_0900_ai_ci

# 慢查询
slow_query_log = 1
long_query_time = 0.5
log_queries_not_using_indexes = 0

# 安全
local_infile = 0
sql_mode = STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION
```

### 5.7 备份策略

```
全量:  xtrabackup / mysqlpump / mysqldump（小库）
增量:  xtrabackup 增量
PITR:  binlog + 全量备份回放
异地:  备份要异地副本（OSS/S3）
验证:  定期恢复演练（不演练 = 没备份）
```

## 六、运维命令速查

```sql
-- 状态
SHOW ENGINE INNODB STATUS\G
SHOW PROCESSLIST;
SHOW FULL PROCESSLIST;

-- 性能 Schema
SELECT * FROM performance_schema.events_statements_summary_by_digest
  ORDER BY sum_timer_wait DESC LIMIT 10;

-- 锁
SELECT * FROM performance_schema.data_locks;
SELECT * FROM performance_schema.data_lock_waits;

-- 复制
SHOW REPLICA STATUS\G       -- 8.0+ 改名
SHOW MASTER STATUS\G

-- 慢查询分析
pt-query-digest /var/lib/mysql/slow.log

-- Online DDL
gh-ost / pt-online-schema-change
```

## 七、常见坑

| 坑 | 建议 |
|:---|:---|
| 大事务 + 主从延迟 | 拆小事务、用并行复制 |
| utf8 不是真 utf8 | 永远用 utf8mb4 |
| 隐式锁升级 | 加索引避免表锁 |
| Online DDL 锁表 | 用 gh-ost / pt-osc |
| 慢查询拖垮主库 | 慢查询监控 + 定期 review |
| 复制延迟 | 升级硬件 / 并行复制 / 拆库 |
| 死锁频繁 | 改事务顺序、缩短事务 |
| 时间字段用 INT | 用 DATETIME(3) 或 TIMESTAMP |
| 误删除无法找回 | 启用 binlog + 备份 + 双人复核 |
| max_connections 过高 | 用连接池（ProxySQL / 应用侧） |

## 八、相关周边

| 工具 | 用途 |
|:---|:---|
| **Percona Toolkit** | pt-online-schema-change / pt-query-digest |
| **gh-ost** | GitHub 的 Online DDL，无锁 |
| **ProxySQL** | 读写分离、连接池 |
| **MaxScale** | MariaDB 的 SQL 路由 |
| **xtrabackup** | 物理热备 |
| **Orchestrator** | 高可用 failover |
| **MyDumper / MyLoader** | 并行逻辑备份 |
| **mysql-shell** | 8.0 新 CLI（JS/Python） |

## 九、信创替代

| 数据库 | 兼容协议 | 特点 |
|:---|:---|:---|
| **TiDB** | MySQL 5.7/8.0 | 分布式 NewSQL |
| **OceanBase** | MySQL/Oracle 双兼容 | 蚂蚁集团出品 |
| **PolarDB-X** | MySQL | 阿里云分布式 |
| **GoldenDB** | MySQL | 中兴 |
| **达梦 DM** | Oracle 兼容为主 | 党政常用 |
| **人大金仓 KingbaseES** | PostgreSQL 兼容 | 信创主力 |

> 📖 一句话：**先把 MySQL 8.0/8.4 用熟，再根据规模决定是否上分布式数据库**。永远不要"小马拉大车"，但也不要"杀鸡用牛刀"。
