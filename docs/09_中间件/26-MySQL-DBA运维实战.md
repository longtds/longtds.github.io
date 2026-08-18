# MySQL DBA 运维实战

> MySQL 生产环境怎么部署?主从/MGR/InnoDB Cluster 怎么选?SQL 慢了怎么优化?怎么备份恢复?怎么排查故障?本文覆盖 MySQL DBA 全栈实战:安装部署、参数调优、高可用、备份恢复、SQL优化、监控告警、灾难恢复。

---

## 一、MySQL 基础架构

### 1.1 MySQL 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                    MySQL Server 架构                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  连接层 (Connection Layer)                              │  │
│  │  - 连接管理 (thread pool)                                │  │
│  │  - 认证 (mysql_native / caching_sha2)                   │  │
│  │  - 授权 (Grant)                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                          │                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  服务层 (Service Layer)                                 │  │
│  │  - SQL 解析器 (Parser)                                   │  │
│  │  - 查询优化器 (Optimizer)                                │  │
│  │  - 查询缓存 (8.0 已移除)                                 │  │
│  │  - 内置函数 / 视图 / 存储过程                             │  │
│  └────────────────────────────────────────────────────────┘  │
│                          │                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  存储引擎层 (Storage Engine Layer)                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │  │ InnoDB   │  │ MyISAM   │  │ Memory   │  ...        │  │
│  │  │ (默认)   │  │ (只读)   │  │ (临时)   │             │  │
│  │  └──────────┘  └──────────┘  └──────────┘             │  │
│  └────────────────────────────────────────────────────────┘  │
│                          │                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  文件系统                                                 │  │
│  │  数据文件 (.ibd) / redo log / undo log / binlog / 慢日志 │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 InnoDB 存储引擎

```
InnoDB 核心特性:
  - 事务 (ACID)
  - 行级锁 (row-level locking)
  - MVCC (多版本并发控制)
  - 外键
  - 崩溃恢复 (crash-safe)
  - 支持热备份

InnoDB 内存结构:

  ┌───────────────────────────────────────────────────┐
  │  Buffer Pool (最重要, 缓存数据页/索引页)             │
  │  ┌──────────────────────────────────────────┐    │
  │  │  Free List | LRU List | Flush List        │   │
  │  │  Change Buffer (二级索引缓冲)             │    │
  │  │  Adaptive Hash Index (自适应哈希)         │    │
  │  └──────────────────────────────────────────┘    │
  ├───────────────────────────────────────────────────┤
  │  Log Buffer (redo log 缓冲)                       │
  │  Dictionary Cache (数据字典缓存)                   │
  └───────────────────────────────────────────────────┘

InnoDB 磁盘结构:
  - System Tablespace (ibdata1): 系统信息
  - File-per-table Tablespaces (.ibd): 每表一个文件 (推荐)
  - General Tablespaces: 通用表空间
  - Undo Tablespaces (undo_001, undo_002): 回滚日志
  - Temporary Tablespaces: 临时表
  - Redo Log (ib_logfile0/1 或 #innodb_redo/): 重做日志

Redo Log vs Undo Log vs Binlog:

  Redo Log (InnoDB 层):
    - 崩溃恢复
    - 记录物理页修改
    - 循环写, 大小固定
    - 提交时 fsync (WAL)

  Undo Log (InnoDB 层):
    - 事务回滚 + MVCC
    - 记录数据修改前的值
    - 位于 undo tablespace

  Binlog (Server 层):
    - 主从复制 + 时间点恢复
    - 记录逻辑 SQL 或行变更
    - 追加写, 按大小切分
    - Row / Statement / Mixed 格式
```

---

## 二、生产环境部署

### 2.1 硬件规划

```
生产 MySQL 硬件配置:

  ┌──────────┬──────────────────┬──────────────────┐
  │ 规模     │ 配置              │ 场景             │
  ├──────────┼──────────────────┼──────────────────┤
  │ 小型     │ 8C/16G/500G SSD  │ 内部系统         │
  │ 中型     │ 16C/64G/1T NVMe  │ 电商/CRM         │
  │ 大型     │ 32C/256G/4T NVMe │ 核心业务         │
  │ 超大型   │ 64C/512G/多盘    │ 金融/电信        │
  └──────────┴──────────────────┴──────────────────┘

  关键点:
    - 内存: Buffer Pool 建议 = 内存的 60-75%
    - 磁盘: 必须 SSD/NVMe (机械盘性能差 10-100 倍)
    - 网络: 主从复制 >= 千兆, 建议万兆
    - CPU: 多核 > 高频 (MySQL 并发)
    - RAID: RAID 10 (性能+可靠性)
    - 独立分区: /data (数据) + /binlog (日志) 分开磁盘
```

### 2.2 系统优化

```bash
# === Linux 系统优化 ===

# 1. 关闭 Swap (或降低 swappiness)
echo 'vm.swappiness = 1' >> /etc/sysctl.d/99-mysql.conf

# 2. 文件系统: xfs 或 ext4 (推荐 xfs)
# 挂载参数: noatime, nodiratime, nobarrier (电池 BBU)
# /etc/fstab
/dev/nvme0n1p1  /data  xfs  defaults,noatime,nodiratime  0  0

# 3. 内核参数
cat >> /etc/sysctl.d/99-mysql.conf << 'EOF'
# 网络
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# 文件句柄
fs.file-max = 2097152
fs.aio-max-nr = 1048576

# 内存
vm.swappiness = 1
vm.dirty_ratio = 20
vm.dirty_background_ratio = 5
vm.overcommit_memory = 0

# NUMA (禁用交叉访问)
# numactl --interleave=all mysqld
EOF
sysctl -p /etc/sysctl.d/99-mysql.conf

# 4. 文件句柄限制
cat >> /etc/security/limits.d/mysql.conf << 'EOF'
mysql  soft  nofile  65535
mysql  hard  nofile  65535
mysql  soft  nproc   65535
mysql  hard  nproc   65535
EOF

# 5. THP (透明大页) 关闭
echo 'never' > /sys/kernel/mm/transparent_hugepage/enabled
echo 'never' > /sys/kernel/mm/transparent_hugepage/defrag

# 持久化
cat >> /etc/rc.local << 'EOF'
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
EOF

# 6. IO 调度器 (SSD 用 noop / mq-deadline)
echo mq-deadline > /sys/block/nvme0n1/queue/scheduler

# 7. CPU 性能模式
cpupower frequency-set -g performance
```

### 2.3 MySQL 8.0 安装

```bash
# === 方式 1: 官方 YUM 源 (推荐) ===
# Rocky/RHEL 9
dnf install -y https://dev.mysql.com/get/mysql80-community-release-el9-4.noarch.rpm
dnf module disable -y mysql
dnf install -y mysql-community-server mysql-community-client

# Ubuntu 22.04
wget https://dev.mysql.com/get/mysql-apt-config_0.8.29-1_all.deb
dpkg -i mysql-apt-config_0.8.29-1_all.deb
apt update
apt install -y mysql-server

# === 方式 2: 二进制包 (灵活) ===
cd /opt
wget https://cdn.mysql.com/Downloads/MySQL-8.0/mysql-8.0.39-linux-glibc2.28-x86_64.tar.xz
tar xf mysql-8.0.39-linux-glibc2.28-x86_64.tar.xz
mv mysql-8.0.39-linux-glibc2.28-x86_64 mysql-8.0
ln -s /opt/mysql-8.0 /usr/local/mysql

# 创建用户
groupadd mysql
useradd -r -g mysql -s /sbin/nologin mysql

# 数据目录
mkdir -p /data/mysql/{data,binlog,logs,tmp}
chown -R mysql:mysql /data/mysql
chown -R mysql:mysql /usr/local/mysql

# 环境变量
echo 'export PATH=/usr/local/mysql/bin:$PATH' >> /etc/profile
source /etc/profile
```

### 2.4 my.cnf 生产配置

```ini
# /etc/my.cnf (或 /etc/mysql/my.cnf)
# 生产环境优化配置 (16C/64G/1T NVMe 参考)

[mysqld]
# ========== 基础配置 ==========
user                            = mysql
port                            = 3306
bind-address                    = 0.0.0.0
server-id                       = 1                    # 每台唯一
datadir                         = /data/mysql/data
socket                          = /data/mysql/mysql.sock
pid-file                        = /data/mysql/mysql.pid
tmpdir                          = /data/mysql/tmp

# 字符集
character-set-server            = utf8mb4
collation-server                = utf8mb4_0900_ai_ci
default-time-zone               = '+08:00'

# 认证插件 (兼容性)
default-authentication-plugin   = mysql_native_password

# 禁用符号链接 (安全)
symbolic-links                  = 0

# ========== 连接与线程 ==========
max_connections                 = 2000
max_connect_errors              = 100000
max_user_connections            = 1800
wait_timeout                    = 3600
interactive_timeout             = 3600
connect_timeout                 = 10
net_read_timeout                = 60
net_write_timeout               = 60

# 线程池 (企业版功能, 社区版用 thread_cache)
thread_cache_size               = 128
back_log                        = 2048

# ========== InnoDB 核心 ==========
default-storage-engine          = InnoDB
innodb_file_per_table           = 1

# Buffer Pool (占内存 60-75%)
innodb_buffer_pool_size         = 48G                 # 64G 内存的 75%
innodb_buffer_pool_instances    = 16                  # 内存 > 1G 每 GB 一个
innodb_buffer_pool_chunk_size   = 128M
innodb_buffer_pool_dump_at_shutdown = 1              # 关闭时 dump
innodb_buffer_pool_load_at_startup  = 1              # 启动时 warm

# Redo Log (重要, 影响性能)
innodb_redo_log_capacity        = 8G                  # 8.0.30+ 新参数
# 旧版: innodb_log_file_size = 2G, innodb_log_files_in_group = 4
innodb_log_buffer_size          = 128M

# 刷盘策略
innodb_flush_log_at_trx_commit  = 1                   # 1=每事务 (最安全)
innodb_flush_method             = O_DIRECT            # 绕过 OS 缓存
innodb_flush_neighbors          = 0                   # SSD 关闭
innodb_io_capacity              = 4000                # SSD 4000-8000, HDD 200
innodb_io_capacity_max          = 8000
innodb_read_io_threads          = 8
innodb_write_io_threads         = 8
innodb_purge_threads            = 4

# 死锁 / 并发
innodb_lock_wait_timeout        = 50
innodb_rollback_on_timeout      = 1
innodb_deadlock_detect          = 1
innodb_print_all_deadlocks      = 1
innodb_thread_concurrency       = 0                   # 0=不限制
innodb_autoinc_lock_mode        = 2                   # 2=交错 (性能好)

# Undo
innodb_undo_log_truncate        = 1
innodb_max_undo_log_size        = 4G

# 双写缓冲 (数据保护)
innodb_doublewrite              = 1

# 页大小 (默认 16K, 建库前定)
# innodb_page_size              = 16K

# 临时表
innodb_temp_data_file_path      = ibtmp1:12M:autoextend:max:2G

# ========== 二进制日志 ==========
log-bin                         = /data/mysql/binlog/mysql-bin
log-bin-index                   = /data/mysql/binlog/mysql-bin.index
binlog_format                   = ROW                 # ROW 最安全
binlog_row_image                = FULL                # 完整行 (或 MINIMAL 省空间)
binlog_expire_logs_seconds      = 604800              # 7 天
max_binlog_size                 = 1G
sync_binlog                     = 1                   # 1=每事务 (最安全)
binlog_cache_size               = 4M
binlog_stmt_cache_size          = 4M
binlog_transaction_dependency_tracking = WRITESET     # 并行复制
binlog_row_metadata             = FULL

# GTID (必开, 强烈推荐)
gtid_mode                       = ON
enforce_gtid_consistency        = ON
log_slave_updates               = ON

# ========== Relay Log (从库) ==========
relay-log                       = /data/mysql/logs/relay-bin
relay-log-index                 = /data/mysql/logs/relay-bin.index
relay_log_purge                 = 1
relay_log_recovery              = 1                   # 崩溃后自动恢复
sync_relay_log                  = 1
sync_relay_log_info             = 1
master_info_repository          = TABLE               # 8.0 默认
relay_log_info_repository       = TABLE

# 复制并行
slave_parallel_type             = LOGICAL_CLOCK
slave_parallel_workers          = 16                  # 与 CPU 核数相近
slave_preserve_commit_order     = 1
skip_slave_start                = 0

# 半同步复制 (需加载插件)
# rpl_semi_sync_master_enabled  = 1
# rpl_semi_sync_master_timeout  = 1000

# ========== 查询与优化 ==========
tmp_table_size                  = 64M
max_heap_table_size             = 64M
sort_buffer_size                = 4M                  # 每连接, 谨慎调大
read_buffer_size                = 2M
read_rnd_buffer_size            = 2M
join_buffer_size                = 4M
thread_stack                    = 256K

# 表定义缓存
table_open_cache                = 8192
table_definition_cache          = 4096
open_files_limit                = 65535

# ========== 日志 ==========
# 错误日志
log_error                       = /data/mysql/logs/mysql-error.log
log_error_verbosity             = 3
log_timestamps                  = SYSTEM

# 慢查询日志
slow_query_log                  = 1
slow_query_log_file             = /data/mysql/logs/mysql-slow.log
long_query_time                 = 1                   # 1 秒
log_queries_not_using_indexes   = 1
log_throttle_queries_not_using_indexes = 60
min_examined_row_limit          = 100
log_slow_admin_statements       = 1
log_slow_slave_statements       = 1

# 通用日志 (调试用, 生产关闭)
general_log                     = 0

# ========== 安全 ==========
# skip-grant-tables             = OFF (紧急恢复用)
local_infile                    = OFF
secure_file_priv                = /data/mysql/tmp

# SSL (推荐)
# ssl-ca                        = /etc/mysql/ca.pem
# ssl-cert                      = /etc/mysql/server-cert.pem
# ssl-key                       = /etc/mysql/server-key.pem
# require_secure_transport      = ON

# ========== 其他 ==========
skip-name-resolve               = 1                   # 禁 DNS 反查
explicit_defaults_for_timestamp = 1
lower_case_table_names          = 1                   # 表名不区分大小写 (建库前定!)
event_scheduler                 = ON
performance_schema              = ON

[client]
port                            = 3306
socket                          = /data/mysql/mysql.sock
default-character-set           = utf8mb4

[mysql]
prompt                          = "\\u@\\h [\\d]> "
no-auto-rehash
default-character-set           = utf8mb4

[mysqldump]
quick
max_allowed_packet              = 512M
```

### 2.5 初始化与启动

```bash
# === 1. 初始化数据目录 ===
mysqld --initialize --user=mysql --datadir=/data/mysql/data
# 或空密码初始化 (测试用)
# mysqld --initialize-insecure --user=mysql --datadir=/data/mysql/data

# 查看临时密码
grep 'temporary password' /data/mysql/logs/mysql-error.log
# [Note] A temporary password is generated for root@localhost: xxxxxxxxxx

# === 2. 创建 systemd 服务 (二进制安装) ===
cat > /etc/systemd/system/mysqld.service << 'EOF'
[Unit]
Description=MySQL Server
After=network.target

[Service]
User=mysql
Group=mysql
Type=notify
ExecStart=/usr/local/mysql/bin/mysqld --defaults-file=/etc/my.cnf
LimitNOFILE=65535
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now mysqld

# === 3. 安全初始化 ===
mysql_secure_installation
# - 设置 root 密码 (强密码, 12+ 位)
# - 移除匿名用户
# - 禁用 root 远程登录
# - 删除 test 数据库
# - 刷新权限

# === 4. 验证 ===
mysql -uroot -p -e "SELECT VERSION(); SHOW ENGINES;"

# === 5. 创建管理用户 ===
mysql -uroot -p << 'SQL'
-- 应用用户 (读写)
CREATE USER 'app'@'10.%.%.%' IDENTIFIED BY 'App@2026!';
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE ON myapp.* TO 'app'@'10.%.%.%';

-- 只读用户 (BI/报表)
CREATE USER 'readonly'@'10.%.%.%' IDENTIFIED BY 'Read@2026!';
GRANT SELECT, SHOW VIEW ON *.* TO 'readonly'@'10.%.%.%';

-- 复制用户
CREATE USER 'repl'@'10.%.%.%' IDENTIFIED BY 'Repl@2026!';
GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'repl'@'10.%.%.%';

-- 备份用户
CREATE USER 'backup'@'localhost' IDENTIFIED BY 'Backup@2026!';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER, PROCESS, 
      REPLICATION SLAVE, REPLICATION CLIENT, RELOAD, 
      BACKUP_ADMIN ON *.* TO 'backup'@'localhost';

-- 监控用户 (Prometheus exporter)
CREATE USER 'monitor'@'127.0.0.1' IDENTIFIED BY 'Mon@2026!';
GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'monitor'@'127.0.0.1';

FLUSH PRIVILEGES;
SQL
```

---

## 三、主从复制

### 3.1 复制原理

```
MySQL 主从复制流程:

  Master                          Slave
  ┌──────────────┐              ┌──────────────┐
  │              │              │              │
  │  Client      │              │              │
  │  ↓ SQL       │              │              │
  │  ┌────────┐ │              │              │
  │  │事务提交 │ │              │              │
  │  └───┬────┘ │              │              │
  │      │      │              │              │
  │  ┌───▼────┐ │              │  ┌────────┐ │
  │  │ Binlog │◄┼──────────────┼──│IO线程   │ │
  │  │        │ │  (Dump线程)  │  │        │ │
  │  └────────┘ │              │  └───┬────┘ │
  │              │              │      │      │
  │              │              │  ┌───▼────┐ │
  │              │              │  │Relay   │ │
  │              │              │  │Log     │ │
  │              │              │  └───┬────┘ │
  │              │              │      │      │
  │              │              │  ┌───▼────┐ │
  │              │              │  │SQL线程 │ │
  │              │              │  │(重放)  │ │
  │              │              │  └───┬────┘ │
  │              │              │      │      │
  │              │              │  ┌───▼────┐ │
  │              │              │  │数据文件│ │
  │              │              │  └────────┘ │
  └──────────────┘              └──────────────┘

复制模式:
  异步复制 (Asynchronous):
    - 主库不等从库确认, 提交即返回
    - 性能最好, 但主库宕机可能丢数据
    - 默认模式

  半同步复制 (Semi-Synchronous):
    - 主库等至少一个从库收到 binlog 才返回
    - 数据安全性提升, 性能略降
    - 需要插件: rpl_semi_sync_master, rpl_semi_sync_slave

  组复制 (Group Replication, MGR):
    - 多主/单主模式, Paxos 协议
    - 自动故障切换
    - 一致性强

复制格式 (binlog_format):
  STATEMENT: 记录 SQL (可能不一致, 如 NOW())
  ROW:       记录行变更 (推荐, 最安全)
  MIXED:     混合模式

GTID (Global Transaction ID):
  格式: uuid:序号 (如 3e11fa47-71ca-11e1-9e33-c80aa9429562:1-5)
  优势:
    - 简化主从切换 (无需 pos)
    - 自动定位复制点
    - 事务级追踪
```

### 3.2 一主一从搭建

```bash
# === 主库配置 (Master, 10.0.1.10) ===
# /etc/my.cnf 关键项:
# server-id                     = 1
# log-bin                       = /data/mysql/binlog/mysql-bin
# gtid_mode                     = ON
# enforce_gtid_consistency      = ON
# binlog_format                 = ROW

# 重启主库
systemctl restart mysqld

# 主库创建复制用户
mysql -uroot -p << 'SQL'
CREATE USER 'repl'@'10.0.1.%' IDENTIFIED WITH mysql_native_password BY 'Repl@2026!';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'10.0.1.%';
FLUSH PRIVILEGES;
SQL

# 查看主库状态
mysql -uroot -p -e "SHOW MASTER STATUS\G"
# *************************** 1. row ***************************
#              File: mysql-bin.000001
#          Position: 157
#     Executed_Gtid_Set:

# === 从库配置 (Slave, 10.0.1.11) ===
# /etc/my.cnf 关键项:
# server-id                     = 2              # 必须唯一
# log-bin                       = /data/mysql/binlog/mysql-bin
# relay-log                     = /data/mysql/logs/relay-bin
# gtid_mode                     = ON
# enforce_gtid_consistency      = ON
# log_slave_updates             = ON
# read_only                     = 1               # 从库只读
# super_read_only               = 1
# slave_parallel_type           = LOGICAL_CLOCK
# slave_parallel_workers        = 16

# 重启从库
systemctl restart mysqld

# 如果主库已有数据, 先备份恢复到从库
# 主库执行:
mysqldump -uroot -p --single-transaction --master-data=2 \
  --triggers --routines --events --all-databases > /tmp/full-dump.sql

# 从库导入
mysql -uroot -p < /tmp/full-dump.sql

# 从库配置复制 (GTID 模式, 简单)
mysql -uroot -p << 'SQL'
CHANGE REPLICATION SOURCE TO
  SOURCE_HOST         = '10.0.1.10',
  SOURCE_PORT         = 3306,
  SOURCE_USER         = 'repl',
  SOURCE_PASSWORD     = 'Repl@2026!',
  SOURCE_AUTO_POSITION = 1,                     -- GTID 自动定位
  SOURCE_SSL          = 1,
  GET_SOURCE_PUBLIC_KEY = 1;

START REPLICA;
SQL

# 验证复制状态
mysql -uroot -p -e "SHOW REPLICA STATUS\G" | grep -E 'Running|Behind|Error'
# Replica_IO_Running: Yes
# Replica_SQL_Running: Yes
# Seconds_Behind_Source: 0
# Last_Error:

# === 测试复制 ===
# 主库
mysql -uroot -p -e "
CREATE DATABASE test_repl;
USE test_repl;
CREATE TABLE t1 (id INT PRIMARY KEY, name VARCHAR(50));
INSERT INTO t1 VALUES (1, 'test');
"

# 从库验证
mysql -uroot -p -e "SELECT * FROM test_repl.t1;"
```

### 3.3 半同步复制

```sql
-- === 主库启用半同步 ===
INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';
INSTALL PLUGIN rpl_semi_sync_slave  SONAME 'semisync_slave.so';   -- 双向都装

SET GLOBAL rpl_semi_sync_master_enabled = 1;
SET GLOBAL rpl_semi_sync_master_timeout = 1000;   -- 1 秒超时降级为异步
SET GLOBAL rpl_semi_sync_master_wait_for_slave_count = 1;
SET GLOBAL rpl_semi_sync_master_wait_no_slave = 1;
SET GLOBAL rpl_semi_sync_master_wait_point = AFTER_SYNC;  -- 无损模式

-- 持久化到 my.cnf
-- plugin_load_add          = "rpl_semi_sync_master=semisync_master.so"
-- plugin_load_add          = "rpl_semi_sync_slave=semisync_slave.so"
-- rpl_semi_sync_master_enabled = 1
-- rpl_semi_sync_master_timeout = 1000

-- === 从库启用半同步 ===
INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so';
SET GLOBAL rpl_semi_sync_slave_enabled = 1;

-- 重启复制线程使生效
STOP REPLICA IO_THREAD;
START REPLICA IO_THREAD;

-- === 验证 ===
-- 主库
SHOW STATUS LIKE 'Rpl_semi_sync%';
-- Rpl_semi_sync_master_status: ON
-- Rpl_semi_sync_master_clients: 1
-- Rpl_semi_sync_master_yes_tx: 100    <- 成功数
-- Rpl_semi_sync_master_no_tx: 0       <- 降级数
```

### 3.4 主从故障切换

```bash
# === 场景: 主库宕机, 从库提升为主库 ===

# 1. 确认原主库不可访问 (避免脑裂)
# 拔网线 / 停 MySQL / 防火墙隔离

# 2. 从库停止复制
mysql -uroot -p << 'SQL'
STOP REPLICA;
RESET REPLICA ALL;                              -- 清除复制配置
SET GLOBAL read_only = 0;                       -- 关闭只读
SET GLOBAL super_read_only = 0;
SQL

# 3. 应用连接切到新主库 (VIP 漂移 / DNS 切换 / ProxySQL)

# 4. 原主库恢复后, 作为从库连接新主库
# 原主库执行:
mysql -uroot -p << 'SQL'
CHANGE REPLICATION SOURCE TO
  SOURCE_HOST         = '10.0.1.11',            -- 新主库
  SOURCE_PORT         = 3306,
  SOURCE_USER         = 'repl',
  SOURCE_PASSWORD     = 'Repl@2026!',
  SOURCE_AUTO_POSITION = 1;

START REPLICA;
SET GLOBAL read_only = 1;
SET GLOBAL super_read_only = 1;
SQL

# === 自动切换工具 ===
# - MHA (Master High Availability, 老牌)
# - Orchestrator (GitHub 出品, 图形化)
# - MySQL Router + MGR (官方推荐)
# - ProxySQL + Sentinel
```

---

## 四、MGR (组复制)

### 4.1 MGR 架构

```
MGR (Group Replication) 特性:
  - 多主/单主模式
  - Paxos 协议, 最多 9 节点
  - 自动故障检测与切换
  - 自动冲突检测 (多主模式)
  - 网络分区保护

单主模式 (推荐):
  ┌──────────┐
  │ Primary  │ ← 读写
  └────┬─────┘
       │
   ┌───┴───┬───────┐
   ▼       ▼       ▼
 Secondary Sec  Sec  ← 只读
  (只读)

多主模式:
  ┌──────────┐  ┌──────────┐
  │ Primary  │◄►│ Primary  │  ← 都可读写
  └────┬─────┘  └────┬─────┘  ← 冲突检测
       │             │
       └──────┬──────┘
              ▼
         Primary       ← 都可读写

InnoDB Cluster = MGR + MySQL Router + MySQL Shell
  - MGR: 存储层高可用
  - MySQL Router: 应用层透明路由
  - MySQL Shell: 管理工具 (dba.*)
```

### 4.2 部署 InnoDB Cluster

```bash
# === 前置条件 (3 节点, mgr1/mgr2/mgr3) ===
# - MySQL 8.0.19+
# - InnoDB 表
# - 所有表有主键
# - binlog_format = ROW
# - gtid_mode = ON

# === 每个节点 my.cnf ===
cat >> /etc/my.cnf << 'EOF'
# MGR 配置
server-id                       = 1         # 每台唯一 (1/2/3)
gtid_mode                       = ON
enforce_gtid_consistency        = ON
master_info_repository          = TABLE
relay_log_info_repository       = TABLE
binlog_checksum                 = NONE
log_slave_updates               = ON
log_bin                         = binlog
binlog_format                   = ROW

# MGR 插件
plugin_load_add                 = 'group_replication.so'

# 组配置
group_replication_group_name    = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
group_replication_start_on_boot = off
group_replication_local_address = "10.0.1.10:33061"      # 每台改
group_replication_group_seeds   = "10.0.1.10:33061,10.0.1.11:33061,10.0.1.12:33061"
group_replication_bootstrap_group = off
group_replication_single_primary_mode = ON              # 单主模式
group_replication_enforce_update_everywhere_checks = OFF

# 提高稳定性
group_replication_communication_max_message_size = 10485760
group_replication_transaction_size_limit = 15000000
group_replication_member_expel_timeout = 5
group_replication_autorejoin_tries = 3
EOF

# 重启 MySQL
systemctl restart mysqld

# === 使用 MySQL Shell 一键部署 (最简单) ===
# 安装 MySQL Shell
dnf install -y mysql-shell

# 每台节点先配置
mysqlsh --uri root@10.0.1.10:3306 -e "dba.configureInstance()"
mysqlsh --uri root@10.0.1.11:3306 -e "dba.configureInstance()"
mysqlsh --uri root@10.0.1.12:3306 -e "dba.configureInstance()"

# 在 mgr1 创建集群
mysqlsh --uri root@10.0.1.10:3306 << 'JS'
var cluster = dba.createCluster('myCluster', {
    memberSslMode: 'REQUIRED',
    ipAllowlist: '10.0.1.0/24',
    consistency: 'BEFORE_ON_PRIMARY_FAILOVER'
});

// 添加节点
cluster.addInstance('root@10.0.1.11:3306', {recoveryMethod: 'clone'});
cluster.addInstance('root@10.0.1.12:3306', {recoveryMethod: 'clone'});

// 查看状态
cluster.status();
JS

# === 部署 MySQL Router ===
dnf install -y mysql-router

# 引导 Router
mysqlrouter --bootstrap root@10.0.1.10:3306 \
  --directory /opt/mysqlrouter \
  --user mysqlrouter \
  --account router_admin

# 启动 Router
/opt/mysqlrouter/start.sh

# 应用连接 Router (自动路由)
# 读写: mysql -uapp -h router-vip -P 6446    (RW 端口)
# 只读: mysql -uapp -h router-vip -P 6447    (RO 端口, 负载均衡)
```

### 4.3 MGR 运维

```sql
-- 查看 MGR 成员
SELECT * FROM performance_schema.replication_group_members;
-- +---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+
-- | CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE |
-- +---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+
-- | group_replication_applier | xxx                                  | mgr1        |        3306 | ONLINE       | PRIMARY     |
-- | group_replication_applier | yyy                                  | mgr2        |        3306 | ONLINE       | SECONDARY   |
-- | group_replication_applier | zzz                                  | mgr3        |        3306 | ONLINE       | SECONDARY   |
-- +---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+

-- 手动切换主节点
SELECT group_replication_set_as_primary('xxx-uuid');

-- 切换到多主模式
SELECT group_replication_switch_to_multi_primary_mode();

-- 切换到单主模式
SELECT group_replication_switch_to_single_primary_mode();

-- 节点重新加入
STOP GROUP_REPLICATION;
START GROUP_REPLICATION;

-- 强制解散集群 (紧急)
STOP GROUP_REPLICATION;
SET GLOBAL group_replication_bootstrap_group = ON;
START GROUP_REPLICATION;
SET GLOBAL group_replication_bootstrap_group = OFF;
```

---

## 五、备份与恢复

### 5.1 备份策略

```
备份方案矩阵:

  ┌─────────────┬────────────┬──────────┬──────────┬─────────┐
  │ 工具         │ 类型        │ 增量     │ 一致性    │ 推荐    │
  ├─────────────┼────────────┼──────────┼──────────┼─────────┤
  │ mysqldump   │ 逻辑        │ ❌       │ 事务/锁    │ ⭐ 小库  │
  │ mysqlpump   │ 逻辑 (并行)  │ ❌       │ 事务       │ ⭐ 中库  │
  │ mydumper    │ 逻辑 (并行)  │ ❌       │ 事务       │ ⭐⭐ 中库│
  │ XtraBackup  │ 物理        │ ✅       │ 热备      │ ⭐⭐⭐   │
  │ Clone Plugin│ 物理        │ ❌       │ 热备      │ ⭐⭐ 8.0+│
  │ Binlog      │ 增量        │ ✅       │ 时间点    │ 必备    │
  │ 快照 (LVM/Ceph) │ 文件系统  │ ✅       │ 需要锁    │ ⭐⭐     │
  └─────────────┴────────────┴──────────┴──────────┴─────────┘

推荐组合:
  小库 (<50GB):  mysqldump 全备 + binlog 增量
  中库 (50-500GB): XtraBackup 每周全备 + 每日增量 + binlog
  大库 (>500GB):  XtraBackup 或 快照 + binlog + 延迟从库

备份原则:
  1. 3-2-1 原则: 3 份数据, 2 种介质, 1 份异地
  2. 定期恢复演练 (至少每季度)
  3. 加密存储 (敏感数据)
  4. 保留策略: 每日 7 天, 每周 4 周, 每月 12 月
```

### 5.2 mysqldump 备份

```bash
# === 全库备份 (推荐参数) ===
mysqldump -h127.0.0.1 -uroot -p'***' \
  --single-transaction \                        # 事务快照 (InnoDB 不锁表)
  --master-data=2 \                             # 记录 binlog 位置 (注释)
  --triggers --routines --events \              # 包含触发器/存储过程/事件
  --hex-blob \                                  # blob 类型 hex 编码
  --set-gtid-purged=OFF \                       # 不包含 GTID (跨集群)
  --default-character-set=utf8mb4 \
  --result-file=/backup/full_$(date +%Y%m%d).sql \
  --all-databases

# 压缩备份
mysqldump ... --all-databases | gzip > /backup/full_$(date +%Y%m%d).sql.gz

# === 备份单个库 ===
mysqldump -uroot -p'***' --single-transaction \
  --databases mydb > /backup/mydb.sql

# === 备份单表 ===
mysqldump -uroot -p'***' --single-transaction \
  mydb table1 table2 > /backup/tables.sql

# === 只备份表结构 ===
mysqldump -uroot -p'***' --no-data --databases mydb > schema.sql

# === 只备份数据 ===
mysqldump -uroot -p'***' --no-create-info --single-transaction mydb > data.sql

# === 恢复 ===
mysql -uroot -p'***' < /backup/full.sql
# 或
gunzip < /backup/full.sql.gz | mysql -uroot -p'***'

# === 定期备份脚本 ===
cat > /opt/scripts/mysql-backup.sh << 'EOF'
#!/bin/bash
set -euo pipefail

BACKUP_DIR=/backup/mysql
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=7
LOG=/var/log/mysql-backup.log

mkdir -p ${BACKUP_DIR}

# 备份
mysqldump --defaults-extra-file=/etc/mysql/backup.cnf \
  --single-transaction \
  --master-data=2 \
  --triggers --routines --events \
  --hex-blob \
  --all-databases \
  | gzip > ${BACKUP_DIR}/full_${DATE}.sql.gz

# 验证
if [ -s ${BACKUP_DIR}/full_${DATE}.sql.gz ]; then
  echo "[$(date)] Backup OK: full_${DATE}.sql.gz ($(du -h ${BACKUP_DIR}/full_${DATE}.sql.gz | cut -f1))" >> ${LOG}
else
  echo "[$(date)] Backup FAILED" >> ${LOG}
  exit 1
fi

# 上传到对象存储 (可选)
# aws s3 cp ${BACKUP_DIR}/full_${DATE}.sql.gz s3://mybucket/mysql/

# 清理旧备份
find ${BACKUP_DIR} -name 'full_*.sql.gz' -mtime +${KEEP_DAYS} -delete

echo "[$(date)] Backup completed" >> ${LOG}
EOF

chmod +x /opt/scripts/mysql-backup.sh

# /etc/mysql/backup.cnf (安全, 只有 mysql 用户可读)
cat > /etc/mysql/backup.cnf << 'EOF'
[client]
user=backup
password=Backup@2026!
socket=/data/mysql/mysql.sock
EOF
chmod 600 /etc/mysql/backup.cnf

# crontab
# 0 2 * * * /opt/scripts/mysql-backup.sh
```

### 5.3 XtraBackup 物理备份

```bash
# === 安装 Percona XtraBackup ===
# MySQL 8.0 需要 XtraBackup 8.0
dnf install -y https://repo.percona.com/yum/percona-release-latest.noarch.rpm
dnf install -y percona-xtrabackup-80

# === 全备 ===
xtrabackup --backup \
  --target-dir=/backup/xtrabackup/full_$(date +%Y%m%d) \
  --user=backup --password='***' \
  --parallel=8 \
  --compress \
  --compress-threads=4

# === 增量备份 (基于上次备份) ===
xtrabackup --backup \
  --target-dir=/backup/xtrabackup/inc_$(date +%Y%m%d) \
  --incremental-basedir=/backup/xtrabackup/full_20260710 \
  --user=backup --password='***'

# === 准备备份 (恢复前必须做) ===
# 全备准备
xtrabackup --prepare --target-dir=/backup/xtrabackup/full_20260710

# 增量准备 (依次 apply)
xtrabackup --prepare --apply-log-only \
  --target-dir=/backup/xtrabackup/full_20260710

xtrabackup --prepare --apply-log-only \
  --target-dir=/backup/xtrabackup/full_20260710 \
  --incremental-dir=/backup/xtrabackup/inc_20260711

xtrabackup --prepare \
  --target-dir=/backup/xtrabackup/full_20260710 \
  --incremental-dir=/backup/xtrabackup/inc_20260712

# === 恢复 ===
# 1. 停止 MySQL
systemctl stop mysqld

# 2. 清空数据目录
rm -rf /data/mysql/data/*

# 3. 拷贝备份到数据目录
xtrabackup --copy-back \
  --target-dir=/backup/xtrabackup/full_20260710 \
  --datadir=/data/mysql/data

# 4. 修改权限
chown -R mysql:mysql /data/mysql/data

# 5. 启动 MySQL
systemctl start mysqld

# === 流式备份 (直接到远端/S3) ===
xtrabackup --backup --stream=xbstream --parallel=8 \
  --user=backup --password='***' \
  | ssh backup@backup-server "xbstream -x -C /backup/xtrabackup/"

# 或直接到 S3
xtrabackup --backup --stream=xbstream --parallel=8 --compress \
  --user=backup --password='***' \
  | aws s3 cp - s3://mybucket/mysql/full_$(date +%Y%m%d).xbstream
```

### 5.4 基于时间点恢复 (PITR)

```bash
# === 场景: 误删数据, 恢复到删除前 5 分钟 ===

# 1. 找到误操作时间
# 查看应用日志, 或从慢查询/general log 找

# 2. 恢复最近的全备
xtrabackup --prepare --target-dir=/backup/full_20260714_0200
xtrabackup --copy-back --target-dir=/backup/full_20260714_0200 --datadir=/data/mysql/data
chown -R mysql:mysql /data/mysql/data
systemctl start mysqld

# 3. 查看全备结束的 binlog 位置
cat /backup/full_20260714_0200/xtrabackup_binlog_info
# mysql-bin.000123  456  aaaa-bbbb-cccc:1-10000

# 4. 从 binlog 恢复到误操作前
# 假设误操作时间: 2026-07-14 10:30:00
# 全备时间:      2026-07-14 02:00:00

# 找到相关 binlog 文件
mysqlbinlog --start-datetime="2026-07-14 02:00:00" \
            --stop-datetime="2026-07-14 10:29:00" \
            /data/mysql/binlog/mysql-bin.00012* \
  > /tmp/incremental.sql

# 5. 恢复增量
mysql -uroot -p < /tmp/incremental.sql

# === GTID 方式 (推荐) ===
# 找到误操作 GTID
mysqlbinlog --base64-output=DECODE-ROWS -v /data/mysql/binlog/mysql-bin.000125 | less
# 找到 DROP TABLE 的 GTID, 如 aaaa-bbbb:15234

# 跳过该 GTID 恢复
mysqlbinlog --start-position=4 \
            --exclude-gtids='aaaa-bbbb-cccc:15234' \
            /data/mysql/binlog/mysql-bin.00012* \
  | mysql -uroot -p

# === 单表恢复 (只恢复某张表) ===
# 从备份中导出单表
mysqldump -uroot -p --single-transaction mydb bad_table > bad_table.sql

# 或从 binlog 提取单表操作
mysqlbinlog --database=mydb \
            --start-datetime="2026-07-14 02:00:00" \
            --stop-datetime="2026-07-14 10:29:00" \
            /data/mysql/binlog/mysql-bin.00012* \
  | grep -A 1 "bad_table" > single_table.sql
```

---

## 六、SQL 优化

### 6.1 慢查询分析

```bash
# === 开启慢查询日志 ===
# my.cnf
# slow_query_log                     = 1
# slow_query_log_file                = /data/mysql/logs/mysql-slow.log
# long_query_time                    = 1
# log_queries_not_using_indexes      = 1

# 运行时修改
mysql -uroot -p << 'SQL'
SET GLOBAL slow_query_log = 1;
SET GLOBAL long_query_time = 1;
SET GLOBAL log_queries_not_using_indexes = 1;
SQL

# === 分析慢日志 ===

# 方法 1: mysqldumpslow (官方)
mysqldumpslow -s t -t 20 /data/mysql/logs/mysql-slow.log
# -s: 排序 (t=时间, c=次数, l=锁, r=返回行, at=平均时间)
# -t: 显示 Top N

# 方法 2: pt-query-digest (Percona Toolkit, 推荐)
pt-query-digest /data/mysql/logs/mysql-slow.log > slow_report.txt

# 或分析特定时间段
pt-query-digest --since '2026-07-14 00:00:00' \
                --until '2026-07-14 12:00:00' \
                /data/mysql/logs/mysql-slow.log

# 报告示例:
# # Profile
# # Rank Query ID           Response time    Calls  R/Call V/M   Item
# # ==== ================== ================ ====== ====== ====== =========
# #    1 0x5DE0EAC7E5F      3600.0 (60.0%)  10000   0.36   0.01  SELECT users
# #    2 0x3DB0F1234E6      1200.0 (20.0%)   5000   0.24   0.02  SELECT orders

# === 实时监控 ===
# 当前运行 SQL
mysql -uroot -p -e "SHOW PROCESSLIST;"
# 或详细信息
mysql -uroot -p -e "SELECT * FROM information_schema.PROCESSLIST WHERE COMMAND != 'Sleep' ORDER BY TIME DESC;"

# 阻塞查询 (等待锁)
mysql -uroot -p -e "
SELECT * FROM performance_schema.data_lock_waits\G
SELECT * FROM sys.innodb_lock_waits\G
"

# 长事务 (>10 秒未提交)
mysql -uroot -p -e "
SELECT trx_id, trx_state, trx_started, trx_query, trx_operation_state,
       TIMESTAMPDIFF(SECOND, trx_started, NOW()) AS duration_sec
FROM information_schema.INNODB_TRX
WHERE TIMESTAMPDIFF(SECOND, trx_started, NOW()) > 10
ORDER BY duration_sec DESC;
"
```

### 6.2 EXPLAIN 分析

```sql
-- === EXPLAIN 执行计划 ===
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- 输出解读:
-- id:            查询序号
-- select_type:   查询类型 (SIMPLE/PRIMARY/SUBQUERY)
-- table:         表名
-- partitions:    分区
-- type:          访问类型 (重要!)
--   system > const > eq_ref > ref > range > index > ALL
--   ALL:    全表扫描 (差)
--   index:  全索引扫描
--   range:  范围扫描 (BETWEEN/IN/>)
--   ref:    非唯一索引等值
--   eq_ref: 唯一索引等值
--   const:  主键/唯一键等值
-- possible_keys: 可能用的索引
-- key:           实际用的索引
-- key_len:       索引长度 (bytes)
-- ref:           索引匹配的列
-- rows:          预估扫描行数
-- filtered:      预估过滤比例
-- Extra:         附加信息 (重要!)
--   Using index:           覆盖索引 (好)
--   Using where:           WHERE 过滤
--   Using temporary:       临时表 (差)
--   Using filesort:        文件排序 (差)
--   Using join buffer:     JOIN 缓冲

-- === EXPLAIN ANALYZE (8.0.18+, 实际执行) ===
EXPLAIN ANALYZE SELECT * FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active';

-- 输出:
-- -> Nested loop inner join  (actual time=0.056..12.345 rows=1000 loops=1)
--     -> Index scan on u using idx_status  (actual time=0.045..2.345 rows=500)
--     -> Index lookup on o using idx_user_id  (actual time=0.012..0.021 rows=2)

-- === 优化器提示 (Hints) ===
-- 强制使用索引
SELECT /*+ INDEX(users idx_email) */ * FROM users WHERE email = ?;

-- 强制 JOIN 顺序
SELECT /*+ JOIN_ORDER(u, o, p) */ * FROM users u, orders o, products p
WHERE u.id = o.user_id AND o.product_id = p.id;

-- 禁用某个索引
SELECT /*+ NO_INDEX(users idx_status) */ * FROM users WHERE status = ?;

-- 设置最大执行时间 (毫秒)
SELECT /*+ MAX_EXECUTION_TIME(1000) */ * FROM big_table;
```

### 6.3 索引优化

```sql
-- === 索引类型 ===
-- B+Tree 索引 (默认, 支持范围/排序)
CREATE INDEX idx_email ON users(email);

-- 唯一索引
CREATE UNIQUE INDEX idx_email_uniq ON users(email);

-- 联合索引 (最左前缀原则)
CREATE INDEX idx_status_created ON users(status, created_at);
-- ✅ 命中: WHERE status = ?
-- ✅ 命中: WHERE status = ? AND created_at > ?
-- ❌ 不命中: WHERE created_at > ?

-- 前缀索引 (长字段, 节省空间)
CREATE INDEX idx_name_prefix ON users(name(10));

-- 全文索引
CREATE FULLTEXT INDEX idx_content ON articles(title, content);

-- 函数索引 (8.0+)
CREATE INDEX idx_lower_email ON users((LOWER(email)));

-- 隐藏索引 (8.0+, 灰度测试)
CREATE INDEX idx_test ON users(name) INVISIBLE;

-- === 索引分析 ===

-- 查看表所有索引
SHOW INDEX FROM users;
-- 或
SELECT * FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'mydb' AND TABLE_NAME = 'users';

-- 查找未使用的索引
SELECT * FROM sys.schema_unused_indexes;

-- 冗余/重复索引
SELECT * FROM sys.schema_redundant_indexes;

-- 索引统计
ANALYZE TABLE users;

-- 查看索引选择性 (值域 / 总行数, 越接近 1 越好)
SELECT 
  COUNT(DISTINCT email) / COUNT(*) AS selectivity 
FROM users;

-- === 索引失效场景 ===
-- ❌ 隐式类型转换
SELECT * FROM users WHERE phone = 13800138000;  -- phone 是 varchar

-- ❌ 函数作用于列
SELECT * FROM users WHERE DATE(created_at) = '2026-07-14';  -- 应改为范围
SELECT * FROM users WHERE created_at >= '2026-07-14' AND created_at < '2026-07-15';

-- ❌ 前导模糊
SELECT * FROM users WHERE name LIKE '%wang';

-- ❌ OR (改用 UNION)
SELECT * FROM users WHERE name = 'wang' OR email = 'wang@x.com';

-- ❌ 联合索引跳过前列
CREATE INDEX idx_a_b_c ON t(a, b, c);
SELECT * FROM t WHERE b = 1;   -- 未用 a, 索引失效

-- === 索引最佳实践 ===
-- 1. 高频 WHERE/JOIN/ORDER BY 列
-- 2. 高选择性 (distinct 值多)
-- 3. 联合索引 = 高选择性列在前
-- 4. 覆盖索引 (查询列都在索引中, 避免回表)
-- 5. 索引不超过 5-6 个 (维护开销)
-- 6. 短索引 (前缀 / 小类型)
-- 7. 避免冗余 (idx(a,b) 已覆盖 idx(a))
```

### 6.4 SQL 改写优化

```sql
-- === 常见优化技巧 ===

-- 1. LIMIT 深分页 (offset 大, 慢)
-- ❌ 慢
SELECT * FROM orders ORDER BY id LIMIT 1000000, 20;
-- ✅ 快 (基于 id 定位)
SELECT * FROM orders WHERE id > 1000000 ORDER BY id LIMIT 20;
-- ✅ 或延迟关联
SELECT o.* FROM orders o
JOIN (SELECT id FROM orders ORDER BY id LIMIT 1000000, 20) tmp
  ON o.id = tmp.id;

-- 2. COUNT(*) 慢 (大表)
-- ❌ 慢
SELECT COUNT(*) FROM big_table;
-- ✅ 用统计信息 (近似值)
SELECT TABLE_ROWS FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'mydb' AND TABLE_NAME = 'big_table';

-- 3. IN 大列表 (>1000 慢)
-- ❌ 慢
SELECT * FROM users WHERE id IN (1, 2, ..., 10000);
-- ✅ 临时表
CREATE TEMPORARY TABLE tmp_ids (id INT PRIMARY KEY);
INSERT INTO tmp_ids VALUES (1), (2), ...;
SELECT u.* FROM users u JOIN tmp_ids t ON u.id = t.id;

-- 4. GROUP BY 慢
-- 确保 GROUP BY 列有索引
CREATE INDEX idx_status ON users(status);
SELECT status, COUNT(*) FROM users GROUP BY status;

-- 5. 子查询 → JOIN
-- ❌ 慢
SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE status = 'vip');
-- ✅ 快
SELECT o.* FROM orders o
JOIN users u ON o.user_id = u.id
WHERE u.status = 'vip';

-- 6. NULL 与索引
-- 可以命中索引, 但选择性低时无用
SELECT * FROM users WHERE deleted_at IS NULL;
-- 更好: 用状态列
SELECT * FROM users WHERE status = 'active';

-- 7. 批量插入
-- ❌ 慢
INSERT INTO t VALUES (1); INSERT INTO t VALUES (2); ...
-- ✅ 快 (批量)
INSERT INTO t VALUES (1), (2), (3), ...;
-- ✅ 更快 (LOAD DATA)
LOAD DATA LOCAL INFILE '/tmp/data.csv' INTO TABLE t 
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';

-- 8. UPDATE 大表分批
-- ❌ 慢 (锁大量行)
UPDATE big_table SET status = 'archived' WHERE created_at < '2020-01-01';
-- ✅ 分批
DELIMITER //
CREATE PROCEDURE batch_update()
BEGIN
  DECLARE done INT DEFAULT 0;
  WHILE done = 0 DO
    UPDATE big_table SET status = 'archived' 
    WHERE created_at < '2020-01-01' AND status != 'archived'
    LIMIT 10000;
    IF ROW_COUNT() = 0 THEN SET done = 1; END IF;
    SELECT SLEEP(1);
  END WHILE;
END//
DELIMITER ;
CALL batch_update();
```

---

## 七、监控与告警

### 7.1 关键指标

```
MySQL 监控黄金指标:

  连接:
    - Threads_connected:     当前连接数 (接近 max_connections 危险)
    - Threads_running:       活跃连接数 (> CPU 核数考虑扩容)
    - Aborted_connects:      认证失败次数
    - Max_used_connections:  历史最大

  查询性能:
    - QPS (Queries Per Second): Queries / Uptime
    - TPS (Transactions):        Com_commit + Com_rollback
    - Slow queries:              慢查询数
    - Select_scan:               全表扫描次数
    - Sort_merge_passes:         排序合并次数

  InnoDB:
    - Innodb_buffer_pool_read_requests:  逻辑读
    - Innodb_buffer_pool_reads:          物理读
    - Buffer Pool 命中率 = 1 - reads/read_requests (>99% 良好)
    - Innodb_row_lock_current_waits:     行锁等待
    - Innodb_deadlocks:                  死锁

  复制:
    - Seconds_Behind_Master:     从库延迟 (>10s 告警)
    - Slave_IO_Running / SQL_Running: 复制线程状态
    - Relay_Log_Space:           relay log 磁盘占用

  系统:
    - CPU / 内存 / 磁盘 IO / 网络
    - 数据目录磁盘空间
    - Binlog 磁盘空间
```

### 7.2 Prometheus 监控

```yaml
# === 部署 mysqld_exporter ===
# docker-compose.yml
services:
  mysqld-exporter:
    image: prom/mysqld-exporter:v0.15.1
    container_name: mysqld-exporter
    ports:
      - "9104:9104"
    environment:
      - DATA_SOURCE_NAME=monitor:Mon@2026!@(mysql:3306)/
    command:
      - --collect.info_schema.processlist
      - --collect.info_schema.innodb_metrics
      - --collect.info_schema.innodb_tablespaces
      - --collect.info_schema.innodb_cmp
      - --collect.info_schema.innodb_cmpmem
      - --collect.perf_schema.tablelocks
      - --collect.perf_schema.eventsstatements
      - --collect.perf_schema.eventswaits
      - --collect.perf_schema.file_events
      - --collect.perf_schema.file_instances
      - --collect.slave_status
      - --collect.slave_hosts
      - --collect.heartbeat
      - --collect.global_status
      - --collect.global_variables

# === Prometheus 配置 ===
# prometheus.yml
scrape_configs:
  - job_name: 'mysql'
    static_configs:
      - targets:
          - '10.0.1.10:9104'    # master
          - '10.0.1.11:9104'    # slave1
          - '10.0.1.12:9104'    # slave2
        labels:
          env: prod

# === 关键 PromQL ===
# QPS
rate(mysql_global_status_queries[1m])

# TPS
rate(mysql_global_status_commands_total{command=~"commit|rollback"}[1m])

# Buffer Pool 命中率
1 - (rate(mysql_global_status_innodb_buffer_pool_reads[5m]) 
     / rate(mysql_global_status_innodb_buffer_pool_read_requests[5m]))

# 连接使用率
mysql_global_status_threads_connected 
/ mysql_global_variables_max_connections * 100

# 从库延迟
mysql_slave_status_seconds_behind_master

# 慢查询率
rate(mysql_global_status_slow_queries[5m])

# 死锁
increase(mysql_global_status_innodb_deadlocks[1h])
```

### 7.3 告警规则

```yaml
# prometheus-alerts.yml
groups:
  - name: mysql
    rules:
      # 实例宕机
      - alert: MySQLDown
        expr: mysql_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MySQL {{ $labels.instance }} is down"

      # 连接数过高
      - alert: MySQLHighConnections
        expr: mysql_global_status_threads_connected / mysql_global_variables_max_connections > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "MySQL 连接使用率 > 85% ({{ $value }})"

      # 从库延迟
      - alert: MySQLReplicationLag
        expr: mysql_slave_status_seconds_behind_master > 60
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "从库延迟 > 60 秒 ({{ $value }}s)"

      # 复制中断
      - alert: MySQLReplicationBroken
        expr: mysql_slave_status_slave_io_running == 0 
              or mysql_slave_status_slave_sql_running == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "MySQL 复制中断 ({{ $labels.instance }})"

      # Buffer Pool 命中率低
      - alert: MySQLBufferPoolLowHitRate
        expr: |
          1 - (rate(mysql_global_status_innodb_buffer_pool_reads[5m])
              / rate(mysql_global_status_innodb_buffer_pool_read_requests[5m])) < 0.95
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Buffer Pool 命中率 < 95%"

      # 慢查询增多
      - alert: MySQLManySlowQueries
        expr: rate(mysql_global_status_slow_queries[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "慢查询率 > 10/s"

      # 死锁
      - alert: MySQLDeadlocks
        expr: increase(mysql_global_status_innodb_deadlocks[10m]) > 5
        labels:
          severity: warning
        annotations:
          summary: "10 分钟内发生 {{ $value }} 次死锁"

      # 磁盘空间
      - alert: MySQLDiskFull
        expr: node_filesystem_avail_bytes{mountpoint="/data"} 
              / node_filesystem_size_bytes{mountpoint="/data"} < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "MySQL 数据目录磁盘 < 10%"
```

---

## 八、常见故障处理

### 8.1 故障速查表

| 故障 | 排查 | 解决 |
|:---|:---|:---|
| **连接数满** | `SHOW PROCESSLIST` 查看长连接/慢查询 | 增大 `max_connections` / kill 慢查询 / 应用连接池优化 |
| **CPU 100%** | `top` 找到 mysqld / `SHOW PROCESSLIST` 找慢查询 | 优化 SQL / 加索引 / 限流 |
| **磁盘 IO 高** | `iostat -xm 1` / `SHOW ENGINE INNODB STATUS` | 优化 buffer_pool_size / 检查 checkpoint |
| **内存溢出** | `dmesg / oom` / `SHOW VARIABLES LIKE 'innodb%'` | 调小 buffer_pool_size / 检查 tmp_table |
| **主从延迟高** | `SHOW REPLICA STATUS` / 从库负载 | 并行复制 / 优化大事务 / 升级硬件 |
| **主从复制中断** | `SHOW REPLICA STATUS \G Last_Error` | 跳过错误 / 重新同步 |
| **表损坏** | `CHECK TABLE` | `REPAIR TABLE` (MyISAM) / 从备份恢复 (InnoDB) |
| **死锁** | `SHOW ENGINE INNODB STATUS` / `innodb_print_all_deadlocks` | 优化事务顺序 / 减小事务 / 加索引 |
| **binlog 满** | `df -h` 查磁盘 | `PURGE BINARY LOGS TO 'xxx'` |
| **误 DROP/DELETE** | 停业务 / 保护 binlog | XtraBackup 全备 + binlog PITR |

### 8.2 主从中断修复

```sql
-- === 场景 1: 从库执行冲突 (Error 1062: Duplicate entry) ===
-- 查看错误
SHOW REPLICA STATUS\G
-- Last_Error: Duplicate entry '123' for key 'PRIMARY'

-- 方法 1: 跳过单个事务 (仅冲突可跳)
STOP REPLICA;
SET GLOBAL sql_slave_skip_counter = 1;
START REPLICA;

-- 方法 2: GTID 跳过
STOP REPLICA;
SET GTID_NEXT = 'aaa-bbb-ccc:12345';    -- 从错误信息中获取
BEGIN; COMMIT;
SET GTID_NEXT = 'AUTOMATIC';
START REPLICA;

-- 方法 3: 从主库重新拉取 (推荐, 数据一致)
-- 前提: 主库仍保留相关 binlog

-- === 场景 2: 从库表不存在/结构不一致 ===
-- 需要重新初始化

-- 从库停止复制
STOP REPLICA;
RESET REPLICA ALL;

-- 主库全备
mysqldump --single-transaction --master-data=2 \
  --all-databases -uroot -p'***' > full.sql

-- 从库导入
mysql -uroot -p'***' < full.sql

-- 重新配置复制
CHANGE REPLICATION SOURCE TO
  SOURCE_HOST='10.0.1.10',
  SOURCE_USER='repl',
  SOURCE_PASSWORD='***',
  SOURCE_AUTO_POSITION=1;
START REPLICA;

-- === 场景 3: 从库落后严重 ===
-- 查看差距
SHOW REPLICA STATUS\G
-- Seconds_Behind_Source: 36000  (10 小时)

-- 排查原因
-- 1. 大事务 (>10 万行)
SELECT * FROM performance_schema.replication_applier_status_by_worker;

-- 2. 单线程 SQL 瓶颈 (未开并行复制)
SET GLOBAL slave_parallel_type = 'LOGICAL_CLOCK';
SET GLOBAL slave_parallel_workers = 16;

-- 3. 从库硬件差
-- 升级 CPU/内存/磁盘

-- 4. 从库 IO 瓶颈
-- 增大 innodb_flush_log_at_trx_commit=2 + sync_binlog=0 (从库降低耐久性换性能)
```

### 8.3 误删数据恢复

```bash
# === 场景: 误 DROP TABLE 关键表 ===

# 1. 立即停业务 (防止 binlog 覆盖)
# 应用侧: 拉黑 / 停服务

# 2. 保护 binlog (禁止自动清理)
mysql -uroot -p -e "SET GLOBAL expire_logs_days = 30;"
mysql -uroot -p -e "SET GLOBAL binlog_expire_logs_seconds = 2592000;"

# 3. 用最近的全备恢复到临时实例
# (不要覆盖生产!)
mkdir -p /tmp/restore
xtrabackup --prepare --target-dir=/backup/full_20260714_0200
# 复制到临时实例数据目录
# ... 启动临时 MySQL ...

# 4. 从临时实例导出误删表
mysqldump -uroot -p'***' -h 127.0.0.1 -P 3307 mydb dropped_table > dropped_table.sql

# 5. 应用 binlog 到临时实例 (直到误操作前)
mysqlbinlog --database=mydb \
  --start-position=456 \                      # 全备结束位置
  --stop-datetime='2026-07-14 10:29:59' \     # 误操作前
  /data/mysql/binlog/mysql-bin.000123 \
  /data/mysql/binlog/mysql-bin.000124 \
  | mysql -uroot -p'***' -h 127.0.0.1 -P 3307

# 6. 导出恢复后的表
mysqldump -uroot -p'***' -h 127.0.0.1 -P 3307 mydb dropped_table > recovered.sql

# 7. 导入生产
mysql -uroot -p'***' mydb < recovered.sql

# === 场景: 误 UPDATE/DELETE 不带 WHERE ===

# 1. binlog 反向解析 (需 binlog_format=ROW)
# 工具: MyFlash / binlog2sql

pip install binlog2sql

# 生成回滚 SQL
python binlog2sql.py -h127.0.0.1 -uroot -p'***' \
  --start-file='mysql-bin.000123' \
  --start-position=1000 \
  --stop-position=5000 \
  -d mydb -t important_table \
  -B > rollback.sql              # -B: 生成 rollback SQL

# 2. 检查 rollback.sql
cat rollback.sql
# UPDATE important_table SET name='old_value' WHERE id=1;
# UPDATE important_table SET name='old_value2' WHERE id=2;

# 3. 应用回滚
mysql -uroot -p'***' mydb < rollback.sql
```

---

## 九、日常运维

### 9.1 常用命令速查

```sql
-- === 状态查看 ===
SHOW STATUS;                          -- 全局状态
SHOW STATUS LIKE 'Threads_%';         -- 线程状态
SHOW STATUS LIKE 'Innodb_%';          -- InnoDB 状态
SHOW GLOBAL STATUS LIKE 'Bytes%';     -- 网络流量

SHOW VARIABLES;                       -- 系统变量
SHOW VARIABLES LIKE 'innodb%';

SHOW ENGINE INNODB STATUS\G           -- InnoDB 详细状态 (锁/事务/IO)
SHOW ENGINE PERFORMANCE_SCHEMA STATUS;

-- 进程管理
SHOW PROCESSLIST;                     -- 当前进程
SHOW FULL PROCESSLIST;                -- 完整 SQL
KILL 12345;                           -- 杀进程 (线程 ID)

-- 存储空间
SELECT 
  TABLE_SCHEMA AS 'DB',
  ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024 / 1024, 2) AS 'Size (GB)'
FROM information_schema.TABLES
GROUP BY TABLE_SCHEMA
ORDER BY SUM(DATA_LENGTH + INDEX_LENGTH) DESC;

-- 表大小 TOP 20
SELECT 
  TABLE_SCHEMA, TABLE_NAME,
  ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS 'Size (MB)',
  TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC
LIMIT 20;

-- === 用户与权限 ===
SHOW GRANTS FOR 'app'@'10.%.%.%';
SELECT user, host FROM mysql.user;

-- 修改密码 (8.0)
ALTER USER 'app'@'10.%.%.%' IDENTIFIED BY 'NewPass@2026!';
FLUSH PRIVILEGES;

-- 密码过期策略
ALTER USER 'app'@'10.%.%.%' PASSWORD EXPIRE INTERVAL 90 DAY;

-- === 表维护 ===
-- 分析表 (更新统计信息)
ANALYZE TABLE users;

-- 优化表 (重建, 回收空间)
OPTIMIZE TABLE users;

-- 检查表
CHECK TABLE users;

-- 在线 DDL (8.0 大部分支持)
ALTER TABLE users ADD COLUMN age INT, ALGORITHM=INPLACE, LOCK=NONE;

-- 大表变更 pt-online-schema-change (Percona Toolkit)
pt-online-schema-change --alter="ADD COLUMN age INT" \
  D=mydb,t=users,h=localhost \
  --user=root --ask-pass \
  --execute
```

### 9.2 巡检脚本

```bash
#!/bin/bash
# mysql-check.sh — 每日巡检

LOG=/var/log/mysql-check-$(date +%Y%m%d).log
CNF=/etc/mysql/monitor.cnf

exec > ${LOG} 2>&1
echo "=== MySQL Daily Check $(date) ==="

echo
echo "=== 1. 服务状态 ==="
systemctl status mysqld --no-pager | head -5

echo
echo "=== 2. 版本 ==="
mysql --defaults-extra-file=${CNF} -e "SELECT VERSION();"

echo
echo "=== 3. 存储引擎 ==="
mysql --defaults-extra-file=${CNF} -e "
SELECT ENGINE, SUPPORT FROM information_schema.ENGINES 
WHERE SUPPORT IN ('YES', 'DEFAULT');"

echo
echo "=== 4. 连接情况 ==="
mysql --defaults-extra-file=${CNF} -e "
SELECT VARIABLE_NAME, VARIABLE_VALUE FROM performance_schema.global_status
WHERE VARIABLE_NAME IN ('Threads_connected', 'Threads_running', 'Max_used_connections', 'Aborted_connects');
SELECT @@max_connections;"

echo
echo "=== 5. Buffer Pool 命中率 ==="
mysql --defaults-extra-file=${CNF} -e "
SELECT 
  ROUND((1 - reads / requests) * 100, 2) AS 'Buffer_Pool_Hit_Rate(%)'
FROM (
  SELECT 
    VARIABLE_VALUE AS reads FROM performance_schema.global_status 
    WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads'
) r, (
  SELECT 
    VARIABLE_VALUE AS requests FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests'
) rq;"

echo
echo "=== 6. 慢查询 ==="
mysql --defaults-extra-file=${CNF} -e "
SHOW GLOBAL STATUS LIKE 'Slow_queries';
SHOW GLOBAL STATUS LIKE 'Queries';"

echo
echo "=== 7. 复制状态 ==="
mysql --defaults-extra-file=${CNF} -e "SHOW REPLICA STATUS\G" | grep -E '(Running|Behind|Error)'

echo
echo "=== 8. 长事务 ==="
mysql --defaults-extra-file=${CNF} -e "
SELECT trx_id, trx_state, trx_started, 
       TIMESTAMPDIFF(SECOND, trx_started, NOW()) AS duration_sec,
       trx_query
FROM information_schema.INNODB_TRX
WHERE TIMESTAMPDIFF(SECOND, trx_started, NOW()) > 60
ORDER BY duration_sec DESC LIMIT 10;"

echo
echo "=== 9. 磁盘空间 ==="
df -h /data
du -sh /data/mysql/data /data/mysql/binlog /data/mysql/logs

echo
echo "=== 10. 前 20 大表 ==="
mysql --defaults-extra-file=${CNF} -e "
SELECT TABLE_SCHEMA, TABLE_NAME, 
  ROUND(DATA_LENGTH/1024/1024, 2) AS Data_MB,
  ROUND(INDEX_LENGTH/1024/1024, 2) AS Index_MB,
  TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA NOT IN ('mysql','information_schema','performance_schema','sys')
ORDER BY DATA_LENGTH DESC LIMIT 20;"

echo
echo "=== 巡检完成 $(date) ==="

# 发送邮件
mail -s "MySQL Daily Check $(hostname)" dba@example.com < ${LOG}
```

---

## 十、生产最佳实践

### 10.1 高可用架构

```
┌──────────────────────────────────────────────────────────┐
│              生产 MySQL 高可用架构 (推荐)                    │
│                                                          │
│                    应用集群                                │
│                        │                                 │
│              ┌─────────▼─────────┐                       │
│              │   ProxySQL / MyCat│                       │
│              │   (读写分离)       │                       │
│              │   连接池 / 熔断    │                       │
│              └─────────┬─────────┘                       │
│                        │                                 │
│         ┌──────────────┼──────────────┐                  │
│         │ 写            │ 读           │ 读               │
│         ▼              ▼              ▼                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │  Master     │ │  Slave 1    │ │  Slave 2    │        │
│  │ (Primary)   │ │ (Read)      │ │ (Read/BI)   │        │
│  │             │◄┤ 半同步       │◄┤ 异步         │        │
│  └──────┬──────┘ └─────────────┘ └─────────────┘        │
│         │                                                │
│         ▼                                                │
│  ┌─────────────┐                                         │
│  │ Delay Slave │  延迟从库 (24h), 防误删                   │
│  │ (Backup)    │                                         │
│  └─────────────┘                                         │
│                                                          │
│  高可用工具:                                              │
│    - Orchestrator: 拓扑管理 + 自动故障切换                 │
│    - MHA:         主从切换 (老牌, 需 SSH)                 │
│    - MGR:         官方组复制 (推荐 8.0+)                  │
│    - Keepalived: VIP 漂移 (简单)                         │
│                                                          │
│  备份策略:                                                │
│    - XtraBackup 每日全备 (2 AM)                          │
│    - Binlog 实时同步到 S3                                │
│    - 每季度恢复演练                                        │
└──────────────────────────────────────────────────────────┘
```

### 10.2 ProxySQL 读写分离

```bash
# === ProxySQL 部署 ===
dnf install -y https://github.com/sysown/proxysql/releases/download/v2.6.4/proxysql-2.6.4-1-centos9.x86_64.rpm
systemctl enable --now proxysql

# 连接 ProxySQL Admin (默认 6032 端口)
mysql -uadmin -padmin -h127.0.0.1 -P6032 --prompt='ProxySQL> '
```

```sql
-- === 配置后端 MySQL ===
-- HG10 = 写组 (master), HG20 = 读组 (slave)
INSERT INTO mysql_servers(hostgroup_id, hostname, port, weight, max_connections) VALUES
  (10, '10.0.1.10', 3306, 1000, 500),          -- master 写组
  (20, '10.0.1.11', 3306, 1000, 500),          -- slave1 读组
  (20, '10.0.1.12', 3306, 1000, 500);          -- slave2 读组

-- === 复制感知 ===
INSERT INTO mysql_replication_hostgroups(writer_hostgroup, reader_hostgroup, check_type)
VALUES (10, 20, 'read_only');

-- === 应用账号 ===
INSERT INTO mysql_users(username, password, default_hostgroup) VALUES
  ('app', 'App@2026!', 10);   -- 默认写组

-- === 监控账号 ===
UPDATE global_variables SET variable_value='monitor' 
  WHERE variable_name='mysql-monitor_username';
UPDATE global_variables SET variable_value='Mon@2026!' 
  WHERE variable_name='mysql-monitor_password';

-- === 读写分离规则 ===
INSERT INTO mysql_query_rules(rule_id, active, match_pattern, destination_hostgroup, apply)
VALUES
  (1, 1, '^SELECT.*FOR UPDATE$', 10, 1),          -- SELECT FOR UPDATE → 写组
  (2, 1, '^SELECT', 20, 1),                        -- SELECT → 读组
  (3, 1, '^INSERT|^UPDATE|^DELETE|^REPLACE', 10, 1); -- 写 → 写组

-- === 生效 ===
LOAD MYSQL SERVERS TO RUNTIME;
LOAD MYSQL USERS TO RUNTIME;
LOAD MYSQL QUERY RULES TO RUNTIME;
LOAD MYSQL VARIABLES TO RUNTIME;
LOAD ADMIN VARIABLES TO RUNTIME;

-- 持久化
SAVE MYSQL SERVERS TO DISK;
SAVE MYSQL USERS TO DISK;
SAVE MYSQL QUERY RULES TO DISK;
SAVE MYSQL VARIABLES TO DISK;

-- === 验证 ===
SELECT * FROM stats.stats_mysql_connection_pool;
SELECT * FROM stats.stats_mysql_query_digest ORDER BY count_star DESC LIMIT 10;
```

### 10.3 参数配置速查

| 参数 | 推荐值 | 说明 |
|:---|:---|:---|
| `innodb_buffer_pool_size` | 内存 60-75% | 最重要, 数据/索引缓存 |
| `innodb_buffer_pool_instances` | 8-16 | 并发访问 |
| `innodb_flush_log_at_trx_commit` | 1 | 1=最安全, 2/0=更快但可能丢数据 |
| `sync_binlog` | 1 | 1=最安全 |
| `innodb_flush_method` | O_DIRECT | 绕过 OS 缓存 |
| `innodb_io_capacity` | SSD=4000-8000 | 影响刷脏页 |
| `innodb_redo_log_capacity` | 8G-16G | 8.0.30+ 新参数 |
| `max_connections` | 1000-2000 | 应用连接池 * 3 |
| `binlog_format` | ROW | 最安全 |
| `binlog_expire_logs_seconds` | 604800 (7d) | binlog 保留 |
| `slow_query_log` | ON | 必开 |
| `long_query_time` | 1 | 慢查询阈值 |
| `slave_parallel_type` | LOGICAL_CLOCK | 并行复制 |
| `slave_parallel_workers` | 16 | 从库并行度 |
| `gtid_mode` | ON | 必开 |
| `enforce_gtid_consistency` | ON | 必开 |
| `character_set_server` | utf8mb4 | 必用 |
| `default_authentication_plugin` | mysql_native_password | 8.0 兼容旧客户端 |

### 10.4 变更管理

```
生产变更规范:

  1. 变更前:
     ✅ 提工单, 审核通过
     ✅ 备份 (至少 1 份可用)
     ✅ 测试环境验证
     ✅ 回滚方案
     ✅ 通知业务方 (预估影响)

  2. 变更中:
     ✅ 低峰期执行
     ✅ 用 pt-online-schema-change / gh-ost 做大表 DDL
     ✅ 监控主从延迟
     ✅ 监控业务错误率

  3. 变更后:
     ✅ 验证数据一致性
     ✅ 观察 30 分钟以上
     ✅ 更新文档

DDL 工具选型:
  ┌───────────────┬────────────────┬────────────────┐
  │ 工具          │ 优势           │ 劣势           │
  ├───────────────┼────────────────┼────────────────┤
  │ 原生 ONLINE   │ 简单, 官方支持 │ 部分操作锁表    │
  │ pt-osc        │ 稳定, 老牌     │ 依赖触发器      │
  │ gh-ost        │ 无触发器, 现代  │ 需要副本        │
  │ TiDB DDL      │ 完全在线       │ 需换 TiDB       │
  └───────────────┴────────────────┴────────────────┘

gh-ost 示例 (在从库执行, 主库无触发器):
  gh-ost \
    --user=root --password='***' \
    --host=10.0.1.10 \
    --database=mydb \
    --table=users \
    --alter="ADD COLUMN age INT" \
    --allow-on-master \
    --initially-drop-ghost-table \
    --initially-drop-old-table \
    --cut-over=default \
    --exact-rowcount \
    --concurrent-rowcount \
    --default-retries=120 \
    --chunk-size=1000 \
    --max-load='Threads_running=25' \
    --critical-load='Threads_running=100' \
    --verbose \
    --execute
```

---

## 十一、速查表

### 11.1 常用命令

| 场景 | 命令 |
|:---|:---|
| 连接 | `mysql -uroot -p -h host -P 3306` |
| 备份全库 | `mysqldump --single-transaction --master-data=2 --all-databases` |
| 物理备份 | `xtrabackup --backup --target-dir=/backup` |
| 慢日志分析 | `pt-query-digest /path/to/slow.log` |
| 复制状态 | `SHOW REPLICA STATUS\G` |
| 主库位置 | `SHOW MASTER STATUS\G` |
| 进程列表 | `SHOW PROCESSLIST` |
| 锁分析 | `SHOW ENGINE INNODB STATUS\G` |
| 长事务 | `SELECT * FROM information_schema.INNODB_TRX` |
| 表大小 | 见巡检脚本 SQL |
| 在线 DDL | `pt-online-schema-change` / `gh-ost` |
| 密码修改 | `ALTER USER 'x'@'y' IDENTIFIED BY 'zzz'` |
| 会话 kill | `KILL <thread_id>` |

### 11.2 关键文件路径

| 文件 | 路径 | 用途 |
|:---|:---|:---|
| 配置文件 | `/etc/my.cnf` | 主配置 |
| 数据目录 | `/data/mysql/data/` | 数据文件 |
| Binlog | `/data/mysql/binlog/` | 二进制日志 |
| 错误日志 | `/data/mysql/logs/mysql-error.log` | 错误 |
| 慢日志 | `/data/mysql/logs/mysql-slow.log` | 慢查询 |
| Socket | `/data/mysql/mysql.sock` | 本地连接 |
| Pid 文件 | `/data/mysql/mysql.pid` | 进程 ID |

### 11.3 推荐工具清单

| 类别 | 工具 | 用途 |
|:---|:---|:---|
| 客户端 | mysql / MySQL Workbench / DBeaver | 交互式查询 |
| 备份 | mysqldump / XtraBackup / mydumper | 备份恢复 |
| 分析 | pt-query-digest / mysqldumpslow | 慢日志 |
| 结构变更 | pt-online-schema-change / gh-ost | 在线 DDL |
| 主从管理 | Orchestrator / MHA | 拓扑管理 + 切换 |
| 中间件 | ProxySQL / MyCat / ShardingSphere | 读写分离 / 分库分表 |
| 监控 | Prometheus + mysqld_exporter + Grafana | 监控 |
| 审计 | MariaDB Audit Plugin / Percona Audit | 审计日志 |
| 快照 | LVM / Ceph RBD 快照 | 秒级快照 |
| 数据同步 | Otter / DataX / Canal | 异构同步 |
| 压测 | sysbench / mysqlslap | 性能测试 |
| 逻辑复制 | Canal / Debezium | binlog 订阅 |

---

*最后更新: 2026-07-14*
