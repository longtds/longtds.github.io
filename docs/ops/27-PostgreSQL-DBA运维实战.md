# PostgreSQL DBA 运维实战

> PostgreSQL 生产环境怎么部署?流复制/逻辑复制怎么选?VACUUM 怎么调?SQL 慢了怎么优化?怎么备份恢复?怎么排查故障?本文覆盖 PostgreSQL DBA 全栈实战:安装部署、参数调优、高可用、备份恢复、SQL优化、监控告警、灾难恢复。

---

## 一、PostgreSQL 基础架构

### 1.1 进程与内存架构

```
┌──────────────────────────────────────────────────────────────┐
│                 PostgreSQL 进程架构                            │
│                                                              │
│  Postmaster (主进程, 端口 5432)                                │
│      │ fork()                                                 │
│      ├─→ Backend Process (每连接一个, 处理 SQL)                │
│      ├─→ Backend Process                                     │
│      │                                                       │
│      ├─→ Background Writer  (刷脏页)                          │
│      ├─→ WAL Writer         (WAL 落盘)                        │
│      ├─→ Checkpointer       (检查点, 数据文件持久化)            │
│      ├─→ Autovacuum Launcher / Worker (自动清理死元组)         │
│      ├─→ Stats Collector    (统计信息)                        │
│      ├─→ Logger             (日志收集)                        │
│      ├─→ Archiver           (WAL 归档)                        │
│      └─→ WAL Sender/Receiver(流复制)                          │
│                                                              │
│  内存结构:                                                    │
│  ┌────────────────────────────────────────────────────┐     │
│  │  共享内存 (Shared Memory)                          │     │
│  │  ├─ Shared Buffers (缓存数据页, 类 InnoDB BP)     │     │
│  │  ├─ WAL Buffers    (WAL 缓冲)                    │     │
│  │  ├─ CLOG            (事务提交状态)                │     │
│  │  └─ Lock Table      (锁表)                       │     │
│  ├────────────────────────────────────────────────────┤     │
│  │  进程私有内存 (Per-Backend)                        │     │
│  │  ├─ work_mem       (排序/哈希)                   │     │
│  │  ├─ maintenance_work_mem (VACUUM/CREATE INDEX)    │     │
│  │  └─ temp_buffers   (临时表缓存)                   │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘

关键概念:
  MVCC:      多版本并发控制, 读写不阻塞 (类 InnoDB, 但实现不同)
  Tuple:     元组 = 行, 更新产生新版本, 老版本变 "死元组"
  Vacuum:    清理死元组, 回收空间 (关键运维)
  WAL:       Write-Ahead Log, 崩溃恢复 + 复制
  Checkpoint: 脏页刷盘, 缩短恢复时间

对比 MySQL:
  ┌─────────────────┬──────────────────┬──────────────────┐
  │                 │ PostgreSQL       │ MySQL InnoDB    │
  ├─────────────────┼──────────────────┼──────────────────┤
  │ 进程模型         │ 多进程 (fork)    │ 多线程           │
  │ MVCC 实现       │ 多版本元组        │ Undo Log         │
  │ 死行清理        │ Vacuum (显式)     │ Purge (后台)     │
  │ 主键堆组织       │ 堆表 + 索引指向  │ 索引组织表 (聚簇) │
  │ 双引擎          │ 单一 (堆)         │ 多引擎 (InnoDB/MyISAM) │
  │ 复制            │ WAL 流/逻辑      │ Binlog           │
  │ 事务隔离        │ RC/RR/Serializable│ RC/RR/Serial     │
  │ JSON            │ 原生 JSONB (索引)│ JSON (弱索引)     │
  │ 扩展性          │ 强 (extension)   │ 弱                │
  │ 存储过程语言    │ PL/pgSQL/Python等│ 有限              │
  └─────────────────┴──────────────────┴──────────────────┘
```

### 1.2 存储结构

```
数据目录 (PGDATA) 结构:
  $PGDATA/
    ├── base/               # 每个数据库一个子目录 (以 OID 命名)
    │   ├── 1/              # template1
    │   ├── 13757/          # postgres
    │   └── 16384/          # mydb
    │       ├── 12345       # 表文件 (以 relfilenode 命名)
    │       ├── 12345_fsm   # Free Space Map
    │       ├── 12345_vm    # Visibility Map
    │       └── 12345.1     # 超过 1GB 自动分段
    ├── global/             # 全局对象 (pg_authid, pg_database)
    ├── pg_wal/             # WAL 日志 (前身 pg_xlog)
    ├── pg_xact/            # 事务提交状态 (CLOG)
    ├── pg_multixact/       # 多事务状态
    ├── pg_stat/            # 运行统计
    ├── pg_stat_tmp/        # 临时统计
    ├── pg_tblspc/          # 表空间符号链接
    ├── pg_replslot/        # 复制槽
    ├── pg_snapshots/       # 快照
    ├── pg_logical/         # 逻辑复制状态
    ├── postgresql.conf     # 主配置
    ├── pg_hba.conf         # 客户端认证
    ├── pg_ident.conf       # 用户映射
    └── postmaster.pid      # 进程 PID

页 (Page) 结构:
  默认 8KB, 包含多个 Tuple
  ┌──────────────┐
  │ Page Header  │  24 bytes
  ├──────────────┤
  │ Line Pointers │ 指向 Tuple
  ├──────────────┤
  │ Free Space   │  剩余空间
  ├──────────────┤
  │ Tuples       │  实际数据 (从底部向上写)
  └──────────────┘
```

---

## 二、生产环境部署

### 2.1 硬件规划

```
生产 PostgreSQL 硬件建议 (类 MySQL):

  ┌──────────┬──────────────────┬──────────────────┐
  │ 规模     │ 配置              │ 场景             │
  ├──────────┼──────────────────┼──────────────────┤
  │ 小型     │ 8C/32G/500G SSD  │ 内部系统         │
  │ 中型     │ 16C/64G/2T NVMe  │ SaaS/CRM         │
  │ 大型     │ 32C/256G/8T NVMe │ 核心业务         │
  │ 超大型   │ 64C/512G/多盘    │ 金融/OLAP        │
  └──────────┴──────────────────┴──────────────────┘

  关键点:
    - 内存: Shared Buffers 建议 25% 内存, OS Cache 用剩余
    - 磁盘: 必须 SSD/NVMe, WAL 单独 RAID10
    - 网络: 万兆 (流复制)
    - CPU: PG 并行查询, 多核收益大
    - 文件系统: xfs / ext4 (xfs 大文件更优)

分区规划:
    /pgdata      数据目录 (RAID10 SSD)
    /pgwal       WAL 目录 (独立 RAID10 SSD, 避免 IO 争抢)
    /pgarchive   WAL 归档目录 (大容量 SATA/NFS)
    /pgbackup    备份目录 (对象存储/NAS)
```

### 2.2 系统优化

```bash
# === Linux 系统优化 (PG 特有) ===

# 1. 内核参数
cat >> /etc/sysctl.d/99-postgres.conf << 'EOF'
# 共享内存 (PG 使用大量 SysV 共享内存)
kernel.shmmax = 68719476736         # 64GB
kernel.shmall = 16777216            # 页数
kernel.shmmni = 4096

# 信号量 (每连接需要)
kernel.sem = 500 32000 32 512

# 网络
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_keepalive_time = 60

# 文件句柄
fs.file-max = 2097152

# 内存管理
vm.swappiness = 1
vm.overcommit_memory = 2
vm.overcommit_ratio = 90            # PG 官方推荐: 关闭 OOM 影响
vm.dirty_ratio = 15
vm.dirty_background_ratio = 3
vm.zone_reclaim_mode = 0

# NUMA
vm.nr_hugepages = 4096              # 大页 (视 shared_buffers 大小)
EOF

sysctl -p /etc/sysctl.d/99-postgres.conf

# 2. 文件句柄限制
cat >> /etc/security/limits.d/postgres.conf << 'EOF'
postgres  soft  nofile  65535
postgres  hard  nofile  65535
postgres  soft  nproc   65535
postgres  hard  nproc   65535
postgres  soft  memlock unlimited
postgres  hard  memlock unlimited
EOF

# 3. 关闭 THP (大页由 huge_pages 管理)
echo 'never' > /sys/kernel/mm/transparent_hugepage/enabled
echo 'never' > /sys/kernel/mm/transparent_hugepage/defrag

# 4. IO 调度器
echo mq-deadline > /sys/block/nvme0n1/queue/scheduler

# 5. 文件系统挂载参数
# /etc/fstab
/dev/nvme0n1   /pgdata    xfs   defaults,noatime,nodiratime      0 0
/dev/nvme1n1   /pgwal     xfs   defaults,noatime,nodiratime      0 0

# 6. Huge Pages (可选, 高性能场景)
# PG 会自动尝试使用 huge_pages=try
# 计算需要的页数: shared_buffers / 2MB
```

### 2.3 PostgreSQL 16 安装

```bash
# === 方式 1: 官方 YUM 源 (推荐) ===
# Rocky/RHEL 9
dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm
dnf -qy module disable postgresql
dnf install -y postgresql16-server postgresql16-contrib

# Ubuntu 22.04
sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt update
apt install -y postgresql-16 postgresql-contrib-16

# === 方式 2: 源码编译 (灵活, 支持定制扩展) ===
cd /opt
wget https://ftp.postgresql.org/pub/source/v16.4/postgresql-16.4.tar.bz2
tar xf postgresql-16.4.tar.bz2
cd postgresql-16.4

./configure \
  --prefix=/usr/local/pgsql \
  --with-openssl \
  --with-libxml \
  --with-libxslt \
  --with-perl \
  --with-python \
  --with-uuid=ossp \
  --enable-nls

make -j$(nproc)
make install

# 编译 contrib 扩展
cd contrib
make -j$(nproc)
make install

# === 创建用户和目录 ===
groupadd postgres
useradd -r -g postgres -s /bin/bash -m -d /var/lib/pgsql postgres

mkdir -p /pgdata/16/data /pgwal/16 /pgarchive/16 /pgbackup
chown -R postgres:postgres /pgdata /pgwal /pgarchive /pgbackup
chmod 700 /pgdata/16/data

# 环境变量
cat >> /var/lib/pgsql/.bash_profile << 'EOF'
export PATH=/usr/local/pgsql/bin:$PATH   # 或 /usr/pgsql-16/bin
export PGDATA=/pgdata/16/data
export PGHOST=/tmp
export PGPORT=5432
export LD_LIBRARY_PATH=/usr/local/pgsql/lib:$LD_LIBRARY_PATH
export MANPATH=/usr/local/pgsql/share/man:$MANPATH
EOF
```

### 2.4 postgresql.conf 生产配置

```ini
# postgresql.conf - 生产配置 (16C/64G/2T NVMe 参考)

# ========== 连接与认证 ==========
listen_addresses            = '*'
port                        = 5432
max_connections             = 500                # 结合 pgBouncer, 不宜过大
superuser_reserved_connections = 5
unix_socket_directories     = '/tmp,/var/run/postgresql'
unix_socket_permissions     = 0777

# 认证 (在 pg_hba.conf)
password_encryption         = scram-sha-256
ssl                         = on
ssl_cert_file               = '/etc/postgres/server.crt'
ssl_key_file                = '/etc/postgres/server.key'
ssl_ca_file                 = ''
ssl_min_protocol_version    = 'TLSv1.2'

# ========== 内存配置 ==========
shared_buffers              = 16GB                # 内存的 25%
huge_pages                  = try
temp_buffers                = 32MB
work_mem                    = 32MB                # 每连接每操作, 谨慎调
maintenance_work_mem        = 2GB                 # VACUUM/CREATE INDEX
autovacuum_work_mem         = 1GB
max_stack_depth             = 7MB
dynamic_shared_memory_type  = posix

# 有效缓存大小 (给优化器提示, OS Cache + shared_buffers)
effective_cache_size        = 48GB                # 内存的 75%

# ========== WAL ==========
wal_level                   = replica             # replica (支持流复制) / logical
fsync                       = on                  # 必须 on
synchronous_commit          = on                  # on/off/local/remote_write/remote_apply
wal_sync_method             = fdatasync           # fdatasync/open_datasync/open_sync
full_page_writes            = on
wal_compression             = on                  # WAL 压缩
wal_buffers                 = 64MB                # -1 表示 shared_buffers/32
wal_writer_delay            = 200ms
wal_writer_flush_after      = 1MB

# WAL 大小与保留
max_wal_size                = 16GB
min_wal_size                = 2GB
wal_keep_size               = 4GB                 # 保留 WAL 供从库
max_slot_wal_keep_size      = 20GB                # 复制槽最大保留

# Checkpoint
checkpoint_timeout          = 15min
checkpoint_completion_target = 0.9
checkpoint_flush_after      = 256kB
checkpoint_warning          = 30s

# 归档
archive_mode                = on
archive_command             = 'test ! -f /pgarchive/16/%f && cp %p /pgarchive/16/%f'
archive_timeout             = 300s               # 5 分钟强制切换 WAL

# ========== 复制 ==========
max_wal_senders             = 20                 # WAL Sender 上限
max_replication_slots       = 20                 # 复制槽上限
wal_sender_timeout          = 60s
track_commit_timestamp      = on                  # 逻辑复制冲突解决用
hot_standby                 = on                  # 从库可读
hot_standby_feedback        = on                  # 减少查询冲突
max_standby_streaming_delay = 30s

# ========== 查询优化器 ==========
random_page_cost            = 1.1                 # SSD 用 1.1, HDD 用 4
seq_page_cost               = 1.0
cpu_tuple_cost              = 0.01
cpu_index_tuple_cost        = 0.005
cpu_operator_cost           = 0.0025
default_statistics_target   = 100                 # 直方图桶数, 大表可调 500-1000
effective_io_concurrency    = 200                 # SSD 高, HDD 低

# JIT (即时编译, 复杂查询提速)
jit                         = on
jit_above_cost              = 100000
jit_inline_above_cost       = 500000
jit_optimize_above_cost     = 500000

# 并行查询
max_worker_processes        = 32                  # >= CPU 核数
max_parallel_workers        = 16
max_parallel_workers_per_gather = 4
max_parallel_maintenance_workers = 4
parallel_leader_participation = on

# ========== Autovacuum ==========
autovacuum                  = on
autovacuum_max_workers      = 6                   # CPU 多可调大
autovacuum_naptime          = 30s
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
autovacuum_vacuum_scale_factor = 0.1              # 表 10% 死元组触发 (可小到 0.02)
autovacuum_analyze_scale_factor = 0.05
autovacuum_vacuum_cost_delay = 2ms                # 越小越快
autovacuum_vacuum_cost_limit = 3000
autovacuum_freeze_max_age   = 200000000
autovacuum_multixact_freeze_max_age = 400000000

# ========== 日志 ==========
log_destination             = 'csvlog'            # stderr/csvlog/jsonlog/syslog
logging_collector           = on
log_directory               = '/var/log/postgres'
log_filename                = 'postgresql-%Y-%m-%d.log'
log_rotation_age            = 1d
log_rotation_size           = 100MB
log_truncate_on_rotation    = off
log_file_mode               = 0600

log_min_duration_statement  = 1000                # >1s 记录 (慢查询)
log_min_messages            = warning
log_min_error_statement     = error
log_line_prefix             = '%m [%p] %q%u@%d/%a '   # 时间/pid/用户@库
log_checkpoints             = on
log_connections             = on
log_disconnections          = on
log_duration                = off
log_lock_waits              = on
log_temp_files              = 10MB                # 大临时文件记录
log_autovacuum_min_duration = 0                   # 记录所有 autovacuum
log_error_verbosity         = default
log_timezone                = 'Asia/Shanghai'

# ========== 客户端 ==========
statement_timeout           = 0                   # 会话级设, 生产建议 300000 (5分钟)
idle_in_transaction_session_timeout = 300000      # 5 分钟, 防止长事务
idle_session_timeout        = 3600000             # 1 小时 idle 断开
lock_timeout                = 0                   # 建议 10000 (10s)
tcp_keepalives_idle         = 60
tcp_keepalives_interval     = 10
tcp_keepalives_count        = 6

# 时区
timezone                    = 'Asia/Shanghai'
DateStyle                   = 'iso, ymd'
default_text_search_config  = 'pg_catalog.simple'

# ========== 扩展 ==========
shared_preload_libraries    = 'pg_stat_statements,auto_explain'

# pg_stat_statements
pg_stat_statements.max      = 10000
pg_stat_statements.track    = all

# auto_explain (自动解释慢查询)
auto_explain.log_min_duration = 3000              # 3 秒以上
auto_explain.log_analyze    = on
auto_explain.log_buffers    = on
auto_explain.log_timing     = on
auto_explain.log_verbose    = off
auto_explain.log_nested_statements = on

# ========== 其他 ==========
data_directory              = '/pgdata/16/data'
hba_file                    = '/pgdata/16/data/pg_hba.conf'
ident_file                  = '/pgdata/16/data/pg_ident.conf'
external_pid_file           = '/var/run/postgres/postgres.pid'
```

### 2.5 pg_hba.conf 认证

```conf
# pg_hba.conf - 客户端认证
# TYPE  DATABASE  USER  ADDRESS       METHOD

# 本地 socket
local   all       postgres            peer                          # 系统用户免密
local   all       all                 scram-sha-256

# 本机
host    all       all   127.0.0.1/32  scram-sha-256
host    all       all   ::1/128       scram-sha-256

# 复制连接 (仅允许 repl 用户)
host    replication  repl  10.0.1.0/24   scram-sha-256

# 应用网段
host    myapp      app     10.0.1.0/24   scram-sha-256

# 内网只读用户
host    all        readonly 10.0.0.0/16  scram-sha-256

# 拒绝其他
host    all        all      0.0.0.0/0    reject

# 认证方式说明:
#   trust:          无密码 (仅测试)
#   peer:           系统用户 (仅 local)
#   md5:            旧密码 (不推荐)
#   scram-sha-256:  新密码 (推荐, PG 10+)
#   cert:           证书 (最安全)
#   ldap/gss/pam:   企业认证
```

### 2.6 初始化与启动

```bash
# === 1. 初始化数据目录 ===
su - postgres -c "/usr/pgsql-16/bin/initdb -D /pgdata/16/data \
  --encoding=UTF8 \
  --locale=en_US.UTF-8 \
  --data-checksums \
  --auth-local=peer \
  --auth-host=scram-sha-256"

# --data-checksums: 页校验 (推荐, 检测硬件错误)
# 无法运行时改变, 需要 pg_checksums 工具在停机时启用

# === 2. 配置文件 ===
# 复制上面的 postgresql.conf / pg_hba.conf 到 /pgdata/16/data/

# === 3. systemd 服务 ===
cat > /etc/systemd/system/postgresql-16.service << 'EOF'
[Unit]
Description=PostgreSQL 16 database server
After=network.target

[Service]
Type=notify
User=postgres
Group=postgres
Environment=PGDATA=/pgdata/16/data
OOMScoreAdjust=-1000
Environment=PG_OOM_ADJUST_FILE=/proc/self/oom_score_adj
Environment=PG_OOM_ADJUST_VALUE=0

ExecStart=/usr/pgsql-16/bin/postgres -D /pgdata/16/data
ExecReload=/bin/kill -HUP $MAINPID

TimeoutSec=0
KillMode=mixed
KillSignal=SIGINT

LimitNOFILE=65535
LimitNPROC=65535

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now postgresql-16

# === 4. 初始化管理用户 ===
sudo -u postgres psql << 'SQL'
-- 修改 postgres 用户密码
ALTER USER postgres WITH PASSWORD 'Postgres@2026!';

-- 应用数据库和用户
CREATE DATABASE myapp OWNER postgres ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8' TEMPLATE=template0;
CREATE USER app WITH PASSWORD 'App@2026!';
GRANT CONNECT ON DATABASE myapp TO app;
\c myapp
GRANT USAGE ON SCHEMA public TO app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO app;

-- 只读用户
CREATE USER readonly WITH PASSWORD 'Read@2026!';
GRANT CONNECT ON DATABASE myapp TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;

-- 复制用户
CREATE USER repl WITH REPLICATION LOGIN PASSWORD 'Repl@2026!';

-- 备份用户 (需要 REPLICATION 权限)
CREATE USER backup WITH REPLICATION LOGIN PASSWORD 'Backup@2026!';
GRANT pg_read_all_data TO backup;

-- 监控用户
CREATE USER monitor WITH LOGIN PASSWORD 'Mon@2026!';
GRANT pg_monitor TO monitor;

-- 常用扩展
\c myapp
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS pg_trgm;           -- 模糊搜索
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS postgres_fdw;      -- 外部数据源
SQL

# === 5. 验证 ===
sudo -u postgres psql -c "SELECT version();"
sudo -u postgres psql -c "\l+"                    # 列出所有库
```

---

## 三、流复制 (Streaming Replication)

### 3.1 流复制原理

```
PostgreSQL 复制模式:

  1. 物理复制 (Physical / Streaming Replication):
     - 基于 WAL, 字节级复制
     - 主从版本必须一致
     - 从库只读 (hot standby)
     - 复制粒度: 整个集群

  2. 逻辑复制 (Logical Replication):
     - 基于 WAL, 解码为 SQL
     - 主从版本可不同
     - 支持跨版本升级
     - 复制粒度: 表级

同步模式:
  异步 (async):      默认, 主库不等从库
  同步 (sync):       等至少一个同步从库
    远程写 (remote_write): WAL 写入从库 OS 缓存
    远程刷新 (remote_flush): WAL 刷到从库磁盘 (default)
    远程应用 (remote_apply): WAL 已在从库应用

流复制拓扑:

  级联复制:
    Master → Standby1 → Standby2
                     → Standby3

  多从复制:
        Master
       /  |  \
    S1   S2   S3

  同步 + 异步组合:
    Master ─── (同步) ──→ S1 (备用)
           └── (异步) ──→ S2, S3 (读)
```

### 3.2 搭建流复制

```bash
# === 环境: master (10.0.1.10) + standby (10.0.1.11) ===

# === 主库准备 ===
# 1. postgresql.conf 关键项
# wal_level = replica
# max_wal_senders = 20
# max_replication_slots = 20
# wal_keep_size = 4GB
# archive_mode = on
# archive_command = '...'

# 2. pg_hba.conf 允许复制连接
echo "host replication repl 10.0.1.0/24 scram-sha-256" >> /pgdata/16/data/pg_hba.conf

# 3. 创建复制用户
sudo -u postgres psql -c "CREATE USER repl WITH REPLICATION LOGIN PASSWORD 'Repl@2026!';"

# 4. 创建复制槽 (可选, 但推荐, 防止主库删除未同步的 WAL)
sudo -u postgres psql -c "SELECT pg_create_physical_replication_slot('standby_slot_1');"

# 5. 重载配置
sudo -u postgres psql -c "SELECT pg_reload_conf();"

# === 从库配置 ===
# 1. 停止 postgres (如果已启动)
systemctl stop postgresql-16

# 2. 清空数据目录
rm -rf /pgdata/16/data/*

# 3. 从主库基础备份
export PGPASSWORD='Repl@2026!'
sudo -u postgres /usr/pgsql-16/bin/pg_basebackup \
  -h 10.0.1.10 -p 5432 -U repl \
  -D /pgdata/16/data \
  -Fp -Xs -P -R \
  -S standby_slot_1                              # 使用复制槽
# 参数说明:
#   -Fp: plain 格式
#   -Xs: 流式取 WAL
#   -P:  显示进度
#   -R:  自动生成 standby.signal 和 primary_conninfo
#   -S:  绑定复制槽

# 4. 检查 postgresql.auto.conf (pg_basebackup -R 自动生成)
cat /pgdata/16/data/postgresql.auto.conf
# primary_conninfo = 'user=repl password=*** host=10.0.1.10 port=5432 ...'
# primary_slot_name = 'standby_slot_1'

# 检查 standby.signal 存在 (PG 12+ 无 recovery.conf)
ls /pgdata/16/data/standby.signal

# 5. 权限
chown -R postgres:postgres /pgdata/16/data
chmod 700 /pgdata/16/data

# 6. 启动从库
systemctl start postgresql-16

# === 验证 ===
# 主库: 查看复制状态
sudo -u postgres psql -c "SELECT * FROM pg_stat_replication;"
# +--------+----------+--------+------------------+--------+-----------+-----------+--------+
# | pid    | usename  | app... | client_addr      | state  | sync_stat | write_lag | ...    |
# +--------+----------+--------+------------------+--------+-----------+-----------+--------+
# | 12345  | repl     | walrec | 10.0.1.11        | stream | async     | 00:00:00  | ...    |
# +--------+----------+--------+------------------+--------+-----------+-----------+--------+

# 主库: 查看复制槽
sudo -u postgres psql -c "SELECT * FROM pg_replication_slots;"

# 从库: 查看接收状态
sudo -u postgres psql -c "SELECT * FROM pg_stat_wal_receiver;"

# 从库: 是否只读
sudo -u postgres psql -c "SELECT pg_is_in_recovery();"    # t = 是从库

# === 测试 ===
# 主库
sudo -u postgres psql -c "CREATE DATABASE test_repl;"

# 从库 (等 1 秒)
sudo -u postgres psql -c "\l" | grep test_repl
```

### 3.3 同步复制配置

```ini
# 主库 postgresql.conf
synchronous_standby_names = 'FIRST 1 (standby1, standby2)'
# 'FIRST 1':      前 1 个从库同步 (排序按名字)
# 'ANY 2':        任意 2 个从库同步
# '*':            所有从库同步 (慎用)
# '':             异步 (默认)

# 应用行为控制
synchronous_commit = on
# on:            等 WAL 刷从库磁盘 (安全 + 慢)
# remote_write:  等从库 OS 缓存 (较安全 + 较快)
# remote_apply:  等从库应用 WAL (最安全, 最慢, 但支持读从库无延迟)
# local:         本地 WAL 刷盘就返回 (=异步)
# off:           不等 WAL 刷盘 (最快, 崩溃可能丢 200ms 数据)
```

```sql
-- 从库需注册 application_name (在 primary_conninfo 里)
-- primary_conninfo = 'application_name=standby1 ...'

-- 查看同步状态
SELECT application_name, state, sync_state 
FROM pg_stat_replication;
-- sync_state: sync / async / potential / quorum
```

### 3.4 主从切换 (Failover)

```bash
# === 计划内切换 (Switchover, 无数据丢失) ===

# 1. 主库停止写入 (应用侧)
# 2. 主库确认所有 WAL 已发送到从库
sudo -u postgres psql -c "SELECT pg_switch_wal();"    # 强制切换 WAL
sudo -u postgres psql -c "SELECT * FROM pg_stat_replication;"
# 确认 replay_lsn = sent_lsn

# 3. 停主库
systemctl stop postgresql-16

# 4. 从库提升为主库
sudo -u postgres /usr/pgsql-16/bin/pg_ctl promote -D /pgdata/16/data
# 或
sudo -u postgres psql -c "SELECT pg_promote();"

# 5. 应用切换连接 (VIP/HAProxy/pgpool)

# 6. 原主库作为从库重连
# 由于 timeline 不同, 需要 pg_rewind 或重做 pg_basebackup

# 方法 1: pg_rewind (推荐, 快)
systemctl stop postgresql-16 || true

sudo -u postgres /usr/pgsql-16/bin/pg_rewind \
  --target-pgdata=/pgdata/16/data \
  --source-server="host=10.0.1.11 port=5432 user=repl password=***" \
  --progress

# 创建 standby.signal + primary_conninfo (指向新主)
sudo -u postgres touch /pgdata/16/data/standby.signal

cat > /pgdata/16/data/postgresql.auto.conf << 'EOF'
primary_conninfo = 'user=repl password=Repl@2026! host=10.0.1.11 port=5432 application_name=standby_old'
primary_slot_name = 'standby_old_slot'
EOF

# 新主库创建复制槽
sudo -u postgres psql -h 10.0.1.11 -c "SELECT pg_create_physical_replication_slot('standby_old_slot');"

systemctl start postgresql-16

# === 计划外切换 (Failover, 主库宕机) ===
# 1. 确认主库不可访问 (避免脑裂 - STONITH)
# 2. 从库 promote
# 3. VIP 漂移到新主库
# 4. 原主库恢复后 pg_rewind 或重新 basebackup

# 自动化工具 (推荐):
#   - Patroni:     基于 etcd/Consul, 官方推荐
#   - repmgr:      2ndQuadrant 出品, 老牌
#   - pg_auto_failover: Microsoft/Citus, 简单
#   - Stolon:      SorintLab, 云原生
```

---

## 四、Patroni 高可用

### 4.1 Patroni 架构

```
Patroni HA 架构:

  ┌─────────────────────────────────────────────────────┐
  │              DCS (Distributed Config Store)          │
  │              etcd / Consul / ZooKeeper               │
  │              (至少 3 节点, 用于选主)                   │
  └────────────────────┬────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
  ┌─────────┐    ┌─────────┐    ┌─────────┐
  │ Patroni │    │ Patroni │    │ Patroni │
  │  node1  │    │  node2  │    │  node3  │
  ├─────────┤    ├─────────┤    ├─────────┤
  │ Postgres│    │ Postgres│    │ Postgres│
  │(Leader) │    │(Replica)│    │(Replica)│
  └─────────┘    └─────────┘    └─────────┘

       ┌───────────────┴───────────────┐
       │                               │
   ┌───────┐                    ┌───────┐
   │HAProxy│  ←─ 应用连接        │HAProxy│
   └───────┘                    └───────┘
       │                               │
    5432 (RW → Leader)          5433 (RO → Replicas)

工作原理:
  1. 每个 PG 节点跑一个 Patroni 进程
  2. Patroni 定期到 DCS 更新自己的健康状态 (leader lock)
  3. Leader 心跳超时, 其他节点选举新 leader
  4. 新 leader promote, 其他节点重新连接
  5. HAProxy 通过 Patroni REST API 检测角色, 路由请求
```

### 4.2 Patroni 部署

```bash
# === 前置: etcd 集群 (3 节点) ===
# 简化: 单机 etcd (测试)
dnf install -y etcd

cat > /etc/etcd/etcd.conf.yml << 'EOF'
name: 'default'
data-dir: /var/lib/etcd
listen-client-urls: http://0.0.0.0:2379
advertise-client-urls: http://10.0.1.10:2379
listen-peer-urls: http://0.0.0.0:2380
initial-advertise-peer-urls: http://10.0.1.10:2380
initial-cluster: 'default=http://10.0.1.10:2380'
initial-cluster-state: new
EOF

systemctl enable --now etcd

# === 安装 Patroni (每个 PG 节点) ===
dnf install -y python3-pip
pip3 install "patroni[etcd,psycopg2]"

# === Patroni 配置 (node1) ===
mkdir -p /etc/patroni
cat > /etc/patroni/patroni.yml << 'EOF'
scope: pg-cluster
namespace: /service/
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.1.10:8008

etcd3:
  hosts: 10.0.1.10:2379,10.0.1.11:2379,10.0.1.12:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    master_start_timeout: 300
    synchronous_mode: false
    postgresql:
      use_pg_rewind: true
      use_slots: true
      parameters:
        wal_level: replica
        hot_standby: "on"
        max_connections: 500
        max_worker_processes: 32
        wal_keep_size: 4GB
        max_wal_senders: 20
        max_replication_slots: 20
        wal_log_hints: "on"
        shared_buffers: 16GB
        effective_cache_size: 48GB
        work_mem: 32MB
        maintenance_work_mem: 2GB
        random_page_cost: 1.1
        effective_io_concurrency: 200
        checkpoint_timeout: 15min
        max_wal_size: 16GB
        min_wal_size: 2GB
        archive_mode: "on"
        archive_command: "test ! -f /pgarchive/16/%f && cp %p /pgarchive/16/%f"

  initdb:
    - encoding: UTF8
    - locale: en_US.UTF-8
    - data-checksums

  pg_hba:
    - host replication repl 10.0.1.0/24 scram-sha-256
    - host all all 10.0.1.0/24 scram-sha-256

  users:
    admin:
      password: Admin@2026!
      options:
        - createrole
        - createdb

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.1.10:5432
  data_dir: /pgdata/16/data
  bin_dir: /usr/pgsql-16/bin
  pgpass: /var/lib/pgsql/.pgpass
  authentication:
    replication:
      username: repl
      password: Repl@2026!
    superuser:
      username: postgres
      password: Postgres@2026!
    rewind:
      username: rewind
      password: Rewind@2026!
  parameters:
    unix_socket_directories: '/var/run/postgresql'

tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false
  nosync: false
EOF

# systemd
cat > /etc/systemd/system/patroni.service << 'EOF'
[Unit]
Description=Patroni PostgreSQL HA
After=syslog.target network.target etcd.service

[Service]
Type=simple
User=postgres
Group=postgres
ExecStart=/usr/local/bin/patroni /etc/patroni/patroni.yml
KillMode=process
TimeoutSec=30
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now patroni

# === 验证 ===
# 查看集群状态
patronictl -c /etc/patroni/patroni.yml list

# +-------------+-------------+-------------+---------+---------+
# | Member      | Host        | Role        | State   | Lag(MB) |
# +-------------+-------------+-------------+---------+---------+
# | node1       | 10.0.1.10   | Leader      | running |         |
# | node2       | 10.0.1.11   | Replica     | running | 0       |
# | node3       | 10.0.1.12   | Replica     | running | 0       |
# +-------------+-------------+-------------+---------+---------+

# 手动切换
patronictl -c /etc/patroni/patroni.yml switchover
patronictl -c /etc/patroni/patroni.yml failover

# 暂停自动切换 (维护窗口)
patronictl -c /etc/patroni/patroni.yml pause
patronictl -c /etc/patroni/patroni.yml resume

# 重新初始化节点
patronictl -c /etc/patroni/patroni.yml reinit pg-cluster node2
```

### 4.3 HAProxy 前置

```conf
# /etc/haproxy/haproxy.cfg
global
    maxconn 10000
    log 127.0.0.1 local0

defaults
    mode tcp
    log global
    retries 3
    timeout client 30m
    timeout connect 4s
    timeout server 30m
    timeout check 5s

# 状态页
listen stats
    mode http
    bind *:7000
    stats enable
    stats uri /

# 读写流量 (仅 Leader)
listen postgres-rw
    bind *:5432
    option httpchk GET /master
    http-check expect status 200
    default-server inter 3s fastinter 1s downinter 5s rise 2 fall 3 on-marked-down shutdown-sessions
    server node1 10.0.1.10:5432 maxconn 500 check port 8008
    server node2 10.0.1.11:5432 maxconn 500 check port 8008
    server node3 10.0.1.12:5432 maxconn 500 check port 8008

# 只读流量 (仅 Replica, 负载均衡)
listen postgres-ro
    bind *:5433
    balance roundrobin
    option httpchk GET /replica
    http-check expect status 200
    default-server inter 3s fastinter 1s downinter 5s rise 2 fall 3
    server node1 10.0.1.10:5432 maxconn 500 check port 8008
    server node2 10.0.1.11:5432 maxconn 500 check port 8008
    server node3 10.0.1.12:5432 maxconn 500 check port 8008
```

---

## 五、逻辑复制

### 5.1 逻辑复制场景

```
逻辑复制适用场景:
  ✅ 跨版本升级 (13 → 16)
  ✅ 跨平台迁移 (x86 → ARM)
  ✅ 部分表复制 (只订阅重要表)
  ✅ 多主复制 (谨慎, 需冲突处理)
  ✅ 数据整合 (多库汇总到 OLAP)
  ✅ 数据脱敏 (发布视图给下游)

限制:
  ❌ 不复制 DDL (表结构需先创建)
  ❌ 不复制序列 (需手动同步)
  ❌ 不复制大对象 (LOB)
  ❌ 表必须有主键或 REPLICA IDENTITY FULL
```

### 5.2 逻辑复制搭建

```bash
# === 主库 (发布端) ===
# postgresql.conf
# wal_level = logical       # 关键! 必须是 logical
# max_replication_slots = 20
# max_wal_senders = 20
# max_worker_processes = 32

# 重启使 wal_level 生效
systemctl restart postgresql-16

# 创建发布 (Publication)
sudo -u postgres psql -d myapp << 'SQL'
-- 发布所有表
CREATE PUBLICATION pub_all FOR ALL TABLES;

-- 发布特定表
CREATE PUBLICATION pub_users FOR TABLE users, orders;

-- 只发布 INSERT/UPDATE
CREATE PUBLICATION pub_ins_upd FOR TABLE logs WITH (publish = 'insert, update');

-- 8.4+ 支持行过滤
CREATE PUBLICATION pub_active_users 
  FOR TABLE users WHERE (status = 'active');

-- 8.4+ 支持列列表
CREATE PUBLICATION pub_users_public 
  FOR TABLE users (id, name, email);

-- 查看发布
SELECT * FROM pg_publication;
SELECT * FROM pg_publication_tables;
SQL

# === 订阅端 ===
# 1. 先在订阅端创建相同的表结构 (逻辑复制不复制 DDL)
# 主库导出 schema
pg_dump -h 10.0.1.10 -U postgres --schema-only -d myapp > myapp_schema.sql
# 订阅端导入
psql -U postgres -d myapp_sub -f myapp_schema.sql

# 2. 创建订阅
sudo -u postgres psql -d myapp_sub << 'SQL'
CREATE SUBSCRIPTION sub_from_master
  CONNECTION 'host=10.0.1.10 port=5432 user=repl password=*** dbname=myapp'
  PUBLICATION pub_all
  WITH (
    copy_data = true,        -- 初始全量拷贝
    create_slot = true,      -- 自动创建复制槽
    enabled = true,
    slot_name = 'sub_from_master_slot',
    synchronous_commit = 'off'  -- 订阅端提交策略
  );

-- 查看订阅
SELECT * FROM pg_subscription;
SELECT * FROM pg_stat_subscription;

-- 主库查看订阅
SELECT * FROM pg_replication_slots;
SELECT * FROM pg_stat_replication;
SQL

# === 运维操作 ===
# 暂停订阅
ALTER SUBSCRIPTION sub_from_master DISABLE;

# 恢复
ALTER SUBSCRIPTION sub_from_master ENABLE;

# 刷新发布 (主库添加了新表)
ALTER SUBSCRIPTION sub_from_master REFRESH PUBLICATION;

# 删除订阅
DROP SUBSCRIPTION sub_from_master;

# 冲突处理 (主键冲突时订阅会停止)
-- 查看冲突
SELECT * FROM pg_stat_subscription WHERE last_msg_receipt_time IS NULL;

-- 跳过冲突事务
ALTER SUBSCRIPTION sub_from_master SKIP (lsn = '0/1234567');
```

### 5.3 跨版本升级

```bash
# === 场景: PG 13 升级到 PG 16 (零停机) ===

# 1. 部署新集群 (PG 16)
# 完整安装 PG 16, 空实例

# 2. 导出旧集群 schema
pg_dump -h old_host -U postgres --schema-only -d myapp > schema.sql

# 3. 在新集群创建 schema (可能需要调整不兼容语法)
psql -h new_host -U postgres -d myapp -f schema.sql

# 4. 旧集群: 创建发布
psql -h old_host -c "ALTER SYSTEM SET wal_level = logical;"
# 重启旧集群 (仅此一次停机, 秒级)
systemctl restart postgresql-13
psql -h old_host -d myapp -c "CREATE PUBLICATION migration FOR ALL TABLES;"

# 5. 新集群: 创建订阅 (copy_data = true 触发全量拷贝)
psql -h new_host -d myapp -c "
CREATE SUBSCRIPTION migration_sub
  CONNECTION 'host=old_host port=5432 user=repl password=*** dbname=myapp'
  PUBLICATION migration
  WITH (copy_data = true);
"

# 6. 等待全量拷贝完成 + 追平延迟
# 查看主库 lag
psql -h old_host -c "SELECT * FROM pg_stat_replication;"
# write_lag/flush_lag/replay_lag 都接近 0

# 7. 切换 (业务低峰期, 秒级)
# 应用停写 → 确认追平 → 应用切到新集群 → 启动写入

# 8. 序列同步 (逻辑复制不复制序列!)
# 在旧集群导出各序列当前值
psql -h old_host -c "
SELECT 'SELECT setval(''' || quote_ident(schemaname) || '.' || quote_ident(sequencename) || 
       ''', ' || last_value || ');' 
FROM pg_sequences;
" -tA > seq.sql

# 在新集群导入
psql -h new_host -d myapp -f seq.sql

# 9. 清理
psql -h new_host -c "DROP SUBSCRIPTION migration_sub;"
psql -h old_host -c "DROP PUBLICATION migration;"
```

---

## 六、备份与恢复

### 6.1 备份方案对比

| 工具 | 类型 | 增量 | 热备 | 特点 | 推荐 |
|:---|:---|:---|:---|:---|:---|
| **pg_dump** | 逻辑 | ❌ | ✅ | 单库/表, 跨版本 | ⭐⭐ 小库 |
| **pg_dumpall** | 逻辑 | ❌ | ✅ | 全局对象+所有库 | ⭐⭐ 小集群 |
| **pg_basebackup** | 物理 | ❌ | ✅ | 官方, 简单 | ⭐⭐ 中库 |
| **pgBackRest** | 物理 | ✅ | ✅ | 并行/加密/压缩/云 | ⭐⭐⭐ 强推 |
| **Barman** | 物理 | ✅ | ✅ | Ruby, 中心化 | ⭐⭐ |
| **WAL-G** | 物理 | ✅ | ✅ | 云原生, Go 语言 | ⭐⭐ 云环境 |
| **文件系统快照** | 快照 | ✅ | 需要 | 秒级 (LVM/Ceph) | ⭐⭐ |
| **WAL 归档** | 增量 | ✅ | ✅ | PITR 必备 | 必备 |

### 6.2 pg_dump / pg_restore

```bash
# === pg_dump 逻辑备份 ===

# 单库备份 (SQL 格式)
pg_dump -h localhost -U postgres -d myapp \
  --format=plain \
  --file=/backup/myapp_$(date +%Y%m%d).sql

# 单库备份 (自定义格式, 推荐)
pg_dump -h localhost -U postgres -d myapp \
  --format=custom \                       # -Fc
  --compress=9 \                          # 压缩
  --jobs=8 \                              # 并行 (仅 directory 格式)
  --file=/backup/myapp_$(date +%Y%m%d).dump

# 单库备份 (目录格式, 支持并行)
pg_dump -h localhost -U postgres -d myapp \
  --format=directory \
  --jobs=8 \
  --file=/backup/myapp_$(date +%Y%m%d)

# 仅备份 schema
pg_dump -h localhost -U postgres -d myapp --schema-only > schema.sql

# 仅备份数据
pg_dump -h localhost -U postgres -d myapp --data-only > data.sql

# 备份指定 schema
pg_dump -h localhost -U postgres -d myapp -n public -n analytics > partial.sql

# 备份指定表
pg_dump -h localhost -U postgres -d myapp -t users -t orders > tables.sql

# 排除表
pg_dump -h localhost -U postgres -d myapp -T "log_*" > no_logs.sql

# === 全局备份 (角色/表空间) ===
pg_dumpall -h localhost -U postgres --globals-only > globals.sql

# 完整集群备份
pg_dumpall -h localhost -U postgres > /backup/full.sql

# === 恢复 ===
# SQL 格式
psql -h localhost -U postgres -d myapp_new < myapp.sql

# 自定义格式 (推荐)
pg_restore -h localhost -U postgres -d myapp_new \
  --jobs=8 \                              # 并行恢复
  --clean --if-exists \                   # 先清空
  --no-owner --no-privileges \            # 忽略权限
  /backup/myapp.dump

# 只恢复表结构
pg_restore -h localhost -U postgres -d myapp_new --schema-only /backup/myapp.dump

# 只恢复指定表
pg_restore -h localhost -U postgres -d myapp_new --table=users /backup/myapp.dump

# === 生产备份脚本 ===
cat > /opt/scripts/pg-backup.sh << 'EOF'
#!/bin/bash
set -euo pipefail

BACKUP_DIR=/backup/pg
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=7
LOG=/var/log/pg-backup.log
DBS=$(sudo -u postgres psql -tAc "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres');")

mkdir -p ${BACKUP_DIR}

# 全局对象
sudo -u postgres pg_dumpall --globals-only \
  > ${BACKUP_DIR}/globals_${DATE}.sql

# 每个库单独备份
for db in ${DBS}; do
  sudo -u postgres pg_dump -Fc -Z 9 -j 4 -f ${BACKUP_DIR}/${db}_${DATE}.dump ${db} 2>>${LOG}
  echo "[$(date)] Backup OK: ${db}_${DATE}.dump" >> ${LOG}
done

# 清理旧备份
find ${BACKUP_DIR} -mtime +${KEEP_DAYS} -delete

# 上传 S3
# aws s3 sync ${BACKUP_DIR}/ s3://mybucket/pg/ --exclude "*" --include "*_${DATE}*"
EOF

chmod +x /opt/scripts/pg-backup.sh
# crontab: 0 2 * * * /opt/scripts/pg-backup.sh
```

### 6.3 pgBackRest 物理备份 (强推)

```bash
# === 安装 pgBackRest ===
dnf install -y pgbackrest

# === 配置 (在 PG 服务器) ===
mkdir -p /etc/pgbackrest /pgbackup/pgbackrest /var/log/pgbackrest
chown postgres:postgres /pgbackup/pgbackrest /var/log/pgbackrest

cat > /etc/pgbackrest/pgbackrest.conf << 'EOF'
[global]
repo1-path=/pgbackup/pgbackrest
repo1-retention-full=4
repo1-retention-diff=6
repo1-retention-archive=7
repo1-cipher-type=aes-256-cbc
repo1-cipher-pass=YourSecret!Passphrase

process-max=8
log-level-console=info
log-level-file=detail
log-path=/var/log/pgbackrest

compress-type=lz4
compress-level=1
delta=y
resume=y

archive-async=y
spool-path=/var/spool/pgbackrest

# 压测建议
# 集群标识
[mycluster]
pg1-path=/pgdata/16/data
pg1-port=5432
pg1-user=postgres
EOF

# === 修改 postgresql.conf (归档命令) ===
sudo -u postgres psql << 'SQL'
ALTER SYSTEM SET archive_mode = 'on';
ALTER SYSTEM SET archive_command = 'pgbackrest --stanza=mycluster archive-push %p';
ALTER SYSTEM SET archive_timeout = '60s';
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET wal_level = 'replica';
SQL

systemctl restart postgresql-16

# === 初始化 Stanza ===
sudo -u postgres pgbackrest --stanza=mycluster stanza-create

# 验证配置
sudo -u postgres pgbackrest --stanza=mycluster check
# 应输出: check command end: completed successfully

# === 备份 ===
# 全备
sudo -u postgres pgbackrest --stanza=mycluster --type=full backup

# 差异备份 (基于最近全备)
sudo -u postgres pgbackrest --stanza=mycluster --type=diff backup

# 增量备份
sudo -u postgres pgbackrest --stanza=mycluster --type=incr backup

# 查看备份历史
sudo -u postgres pgbackrest --stanza=mycluster info

# stanza: mycluster
#   status: ok
#   cipher: aes-256-cbc
#   db (current)
#     wal archive min/max: 000000010000000000000005/00000001000000010000001A
#     full backup: 20260714-020000F
#       timestamp start/stop: 2026-07-14 02:00:00 / 2026-07-14 02:15:00
#       wal start/stop: 000000010000000000000005 / 000000010000000000000006
#       database size: 15GB, backup size: 15GB
#       repository size: 5GB, repository backup size: 5GB
#     diff backup: 20260714-020000F_20260715-020000D
#       ...

# === 恢复 ===
# 停止 PG
systemctl stop postgresql-16

# 清空数据目录
rm -rf /pgdata/16/data/*

# 恢复最新备份
sudo -u postgres pgbackrest --stanza=mycluster restore

# 时间点恢复 (PITR)
sudo -u postgres pgbackrest --stanza=mycluster \
  --type=time \
  --target='2026-07-14 10:00:00' \
  --target-action=promote \
  restore

# 恢复到指定 LSN
sudo -u postgres pgbackrest --stanza=mycluster \
  --type=lsn \
  --target=0/1A0000A0 \
  restore

# 恢复到指定备份
sudo -u postgres pgbackrest --stanza=mycluster \
  --type=immediate \
  --set=20260714-020000F \
  restore

# 启动
systemctl start postgresql-16

# === 定时备份 (crontab) ===
# 每周一 2:00 全备
# 0 2 * * 1 postgres pgbackrest --stanza=mycluster --type=full backup
# 每天 2:00 差异
# 0 2 * * 2-7 postgres pgbackrest --stanza=mycluster --type=diff backup
# 每小时增量
# 0 * * * * postgres pgbackrest --stanza=mycluster --type=incr backup
```

### 6.4 时间点恢复 (PITR)

```bash
# === 前置: 已开启归档 (archive_command) 并有基础备份 ===

# === 场景: 误 DROP TABLE, 恢复到删除前 5 分钟 ===

# 1. 找到误操作时间 (查日志)
grep 'DROP TABLE' /var/log/postgres/*.log

# 2. 停止 PG
systemctl stop postgresql-16

# 3. 保护现有数据 (备份)
mv /pgdata/16/data /pgdata/16/data.bak

# 4. 恢复基础备份
mkdir /pgdata/16/data
chmod 700 /pgdata/16/data
sudo -u postgres pgbackrest --stanza=mycluster \
  --type=time \
  --target='2026-07-14 10:29:59' \
  --target-action=pause \
  restore

# --target-action:
#   pause:    暂停在目标点, 手动确认后 promote (推荐)
#   promote:  自动 promote
#   shutdown: 停机

# 5. 启动 PG
systemctl start postgresql-16

# 6. 验证数据
sudo -u postgres psql -c "SELECT * FROM dropped_table LIMIT 5;"

# 7. 确认无误后 promote
sudo -u postgres psql -c "SELECT pg_wal_replay_resume();"
```

---

## 七、VACUUM 与死元组管理

### 7.1 VACUUM 原理

```
VACUUM (Post gres 独有的关键运维):

  为什么需要?
    - MVCC 更新/删除产生 "死元组"
    - 死元组占用空间但对查询不可见
    - 事务 ID (XID) 32 位, 会耗尽 (环绕)
    - 统计信息需要更新供优化器使用

  VACUUM 做什么:
    - 标记死元组空间可复用 (但不返还 OS)
    - 冻结老事务 (防 XID 环绕)
    - 更新统计信息 (ANALYZE)
    - 清理索引死条目

  VACUUM vs VACUUM FULL:
    ┌────────────────┬─────────────┬──────────────┐
    │                │ VACUUM      │ VACUUM FULL  │
    ├────────────────┼─────────────┼──────────────┤
    │ 锁            │ 共享锁       │ 排他锁 (阻塞) │
    │ 空间返还 OS   │ ❌          │ ✅           │
    │ 重建索引       │ ❌          │ ✅           │
    │ 速度          │ 快          │ 慢           │
    │ 生产用        │ ✅ 常用     │ ❌ 尽量避免  │
    └────────────────┴─────────────┴──────────────┘

  Autovacuum (自动执行):
    - PG 内置后台进程
    - 表死元组比例超阈值时触发
    - 默认参数偏保守, 大表需调优

  参数与触发条件:
    触发 VACUUM: n_dead_tup > autovacuum_vacuum_threshold + autovacuum_vacuum_scale_factor * n_live_tup
    默认: threshold=50, scale_factor=0.1 (10%)
    → 100 万行表, 10 万死元组才触发, 太晚!
    → 生产建议 scale_factor=0.02 (2%) 或更小

    触发 ANALYZE: n_ins_upd_del_since_analyze > threshold + scale_factor * n_live_tup
    默认: threshold=50, scale_factor=0.05 (5%)
```

### 7.2 VACUUM 调优

```sql
-- === 查看死元组情况 ===
SELECT 
  schemaname, relname,
  n_live_tup, n_dead_tup,
  ROUND(n_dead_tup::numeric / NULLIF(n_live_tup, 0) * 100, 2) AS dead_pct,
  last_autovacuum, last_autoanalyze,
  autovacuum_count, autoanalyze_count
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC
LIMIT 20;

-- === 表膨胀检查 (需要 pgstattuple 扩展) ===
CREATE EXTENSION IF NOT EXISTS pgstattuple;

SELECT 
  schemaname || '.' || relname AS table,
  pg_size_pretty(pg_relation_size(oid)) AS size,
  (pgstattuple(oid)).dead_tuple_percent AS dead_pct,
  (pgstattuple(oid)).free_percent AS free_pct
FROM pg_class c
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE relkind = 'r' AND schemaname NOT IN ('pg_catalog', 'information_schema')
  AND pg_relation_size(oid) > 1024*1024*100    -- >100MB
ORDER BY pg_relation_size(oid) DESC
LIMIT 20;

-- === 手动 VACUUM ===
-- 常规
VACUUM (VERBOSE, ANALYZE) users;

-- 并行 (13+)
VACUUM (PARALLEL 4, VERBOSE, ANALYZE) big_table;

-- 只 ANALYZE 更新统计信息
ANALYZE users;

-- VACUUM FULL (需要停机, 慎用)
VACUUM FULL users;   -- 加 ACCESS EXCLUSIVE 锁

-- 替代 VACUUM FULL: pg_repack (在线重组, 需要扩展)
-- pg_repack -h localhost -U postgres -d myapp -t users --no-order

-- === 单表调整 autovacuum 参数 ===
-- 高频更新表, 更激进
ALTER TABLE hot_table SET (
  autovacuum_vacuum_scale_factor = 0.02,      -- 2% 死元组即触发
  autovacuum_analyze_scale_factor = 0.01,
  autovacuum_vacuum_cost_delay = 0,           -- 不限速
  autovacuum_vacuum_cost_limit = 10000
);

-- 只插入的日志表, 关闭 vacuum (仅 analyze)
ALTER TABLE logs SET (
  autovacuum_enabled = false,   -- 或 autovacuum_vacuum_scale_factor = 1
  autovacuum_analyze_scale_factor = 0.01
);

-- 恢复默认
ALTER TABLE users RESET (autovacuum_vacuum_scale_factor);
```

### 7.3 XID 环绕预防

```sql
-- === XID 环绕是 PG 独有的严重问题 ===
-- XID 是 32 位, 约 20 亿事务后环绕, 环绕前必须 VACUUM FREEZE
-- 达到 age(datfrozenxid) = 2^31 - 1000000 = 2146483647 时数据库将强制停止!

-- 查看各库 XID age
SELECT datname, age(datfrozenxid) AS xid_age
FROM pg_database
ORDER BY xid_age DESC;

-- 查看各表 XID age
SELECT 
  schemaname, relname,
  age(relfrozenxid) AS xid_age,
  pg_size_pretty(pg_relation_size(oid)) AS size
FROM pg_class c 
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE relkind IN ('r', 'm')
ORDER BY age(relfrozenxid) DESC
LIMIT 20;

-- 手动 FREEZE (推荐定期在低峰期执行)
VACUUM (FREEZE, VERBOSE) users;

-- 全库 FREEZE (低峰期)
VACUUM FREEZE;

-- 关键参数 (postgresql.conf)
-- autovacuum_freeze_max_age = 200000000    (2 亿, 强制 vacuum freeze)
-- vacuum_freeze_min_age = 50000000         (5000 万, 冻结阈值)
-- vacuum_freeze_table_age = 150000000
```

---

## 八、SQL 优化

### 8.1 慢查询分析

```sql
-- === pg_stat_statements 扩展 (必装) ===
-- postgresql.conf: shared_preload_libraries = 'pg_stat_statements'
CREATE EXTENSION pg_stat_statements;

-- 查看最慢的 20 个查询
SELECT 
  queryid,
  substring(query, 1, 100) AS query,
  calls,
  ROUND(total_exec_time::numeric, 2) AS total_ms,
  ROUND(mean_exec_time::numeric, 2) AS mean_ms,
  ROUND(max_exec_time::numeric, 2) AS max_ms,
  rows,
  ROUND(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 2) AS cache_hit_pct
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- 按总时间排序 (系统整体压力来源)
SELECT 
  substring(query, 1, 100) AS query,
  calls,
  ROUND(total_exec_time::numeric / 1000, 2) AS total_sec,
  ROUND(mean_exec_time::numeric, 2) AS mean_ms
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- 重置统计
SELECT pg_stat_statements_reset();

-- === 实时监控 ===
-- 当前会话
SELECT 
  pid, usename, datname, application_name,
  state, wait_event_type, wait_event,
  now() - query_start AS duration,
  substring(query, 1, 100) AS query
FROM pg_stat_activity
WHERE state != 'idle' AND pid != pg_backend_pid()
ORDER BY duration DESC;

-- 阻塞查询
SELECT 
  blocked.pid AS blocked_pid,
  blocked.usename AS blocked_user,
  blocking.pid AS blocking_pid,
  blocking.usename AS blocking_user,
  blocked.query AS blocked_query,
  blocking.query AS blocking_query
FROM pg_stat_activity AS blocked
JOIN pg_stat_activity AS blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));

-- 锁分析
SELECT 
  l.locktype, l.mode, l.granted,
  a.pid, a.usename, a.state, a.query
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE NOT granted;

-- 长事务 (>10 秒)
SELECT 
  pid, usename, datname, 
  xact_start, now() - xact_start AS duration,
  state, query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL 
  AND now() - xact_start > interval '10 seconds'
ORDER BY duration DESC;

-- 长事务清理
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'idle in transaction' AND now() - xact_start > interval '5 minutes';
```

### 8.2 EXPLAIN 详解

```sql
-- === EXPLAIN 基本 ===
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';
--                                QUERY PLAN
-- ─────────────────────────────────────────────────────────────
--  Index Scan using idx_email on users  (cost=0.29..8.31 rows=1 width=64)
--    Index Cond: (email = 'test@example.com'::text)

-- === EXPLAIN ANALYZE (实际执行, 谨慎在生产用) ===
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT u.name, COUNT(o.id) AS orders
FROM users u LEFT JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
GROUP BY u.name
ORDER BY orders DESC LIMIT 10;

-- 关键指标:
--   cost:           起始成本..总成本
--   rows:           预估行数
--   actual time:    实际时间 (启动..总时间)
--   loops:          循环次数
--   Buffers:        shared hit=缓存命中, read=磁盘读
--   Rows Removed by Filter: 过滤掉的行数 (大 → 缺索引)

-- === 常见执行节点 ===
-- Seq Scan:         顺序扫描 (小表可以, 大表警告)
-- Index Scan:       索引扫描 + 回表
-- Index Only Scan:  覆盖索引 (最快, 无回表)
-- Bitmap Heap Scan: 位图扫描 (多索引组合)
-- Nested Loop:      嵌套循环 (小外表 + 内表索引)
-- Hash Join:        哈希连接 (大表)
-- Merge Join:       归并连接 (已排序)
-- Sort:             排序 (external merge → 磁盘, 需调 work_mem)
-- Hash Aggregate:   哈希分组
-- Materialize:      物化 (临时表)

-- === auto_explain (自动记录执行计划) ===
-- postgresql.conf:
-- shared_preload_libraries = 'auto_explain'
-- auto_explain.log_min_duration = 3000   # >3s 自动记录
-- auto_explain.log_analyze = on

-- 效果: 慢查询自动带执行计划出现在日志里
```

### 8.3 索引优化

```sql
-- === 索引类型 (PG 丰富) ===

-- B-Tree (默认, 支持 = < > BETWEEN)
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_created ON orders(created_at);

-- 联合索引 (最左前缀 + 全部命中效果好)
CREATE INDEX idx_status_created ON orders(status, created_at);

-- 唯一索引
CREATE UNIQUE INDEX idx_email_uniq ON users(email);

-- 部分索引 (只索引子集, 节省空间)
CREATE INDEX idx_active_users ON users(email) WHERE status = 'active';
CREATE INDEX idx_pending_orders ON orders(created_at) WHERE status = 'pending';

-- 表达式索引
CREATE INDEX idx_lower_email ON users((lower(email)));
CREATE INDEX idx_year ON orders((date_part('year', created_at)));

-- 包含列索引 (11+, 覆盖索引)
CREATE INDEX idx_email_include ON users(email) INCLUDE (name, phone);

-- Hash (仅 =, 用得少)
CREATE INDEX idx_hash ON users USING hash(email);

-- GIN (数组/JSONB/全文搜索)
CREATE INDEX idx_tags ON articles USING gin(tags);              -- 数组
CREATE INDEX idx_data ON events USING gin(data);                -- JSONB
CREATE INDEX idx_data_path ON events USING gin(data jsonb_path_ops);   -- JSONB 更小
CREATE INDEX idx_content ON articles USING gin(to_tsvector('english', content));  -- 全文

-- GIST (几何/范围/近似)
CREATE INDEX idx_range ON schedules USING gist(during);
CREATE INDEX idx_location ON stores USING gist(coordinates);

-- BRIN (超大表, 数据有序时高效, 索引小)
CREATE INDEX idx_ts ON logs USING brin(created_at);

-- SP-GIST (空间分区)
CREATE INDEX idx_ip ON access_log USING spgist(ip inet_ops);

-- === 并发建索引 (不锁表) ===
CREATE INDEX CONCURRENTLY idx_new ON big_table(col);
-- 注意: CONCURRENTLY 不能在事务中, 失败留下 INVALID 索引需删除

-- === 索引分析 ===
-- 未使用索引 (可考虑删除)
SELECT 
  schemaname, relname, indexrelname,
  idx_scan, idx_tup_read, idx_tup_fetch,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%pkey'
ORDER BY pg_relation_size(indexrelid) DESC;

-- 重复索引
SELECT 
  indrelid::regclass, 
  array_agg(indexrelid::regclass) AS duplicates
FROM pg_index
GROUP BY indrelid, indkey
HAVING count(*) > 1;

-- 索引膨胀
SELECT 
  schemaname || '.' || indexrelname AS index,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size,
  idx_scan
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;

-- 重建索引 (不锁)
REINDEX INDEX CONCURRENTLY idx_email;
REINDEX TABLE CONCURRENTLY users;
```

### 8.4 SQL 改写技巧

```sql
-- === 1. LIMIT + OFFSET 深分页慢 ===
-- ❌ 慢
SELECT * FROM orders ORDER BY id LIMIT 20 OFFSET 1000000;
-- ✅ 快 (keyset pagination)
SELECT * FROM orders WHERE id > 1000000 ORDER BY id LIMIT 20;

-- === 2. COUNT(*) 大表慢 ===
-- ❌ 慢 (需扫全表)
SELECT COUNT(*) FROM big_table;
-- ✅ 近似值 (从统计信息取)
SELECT reltuples::bigint FROM pg_class WHERE relname = 'big_table';
-- ✅ 精确值 + 索引扫描 (需 index-only scan)
-- (需要该表有 vacuum 更新 VM)

-- === 3. IN 大列表用 = ANY ===
-- 慢
SELECT * FROM users WHERE id IN (1, 2, 3, ..., 10000);
-- 快 (数组)
SELECT * FROM users WHERE id = ANY(ARRAY[1,2,3,...]);
-- 更快 (临时表 JOIN)
WITH tmp(id) AS (VALUES (1),(2),(3),...)
SELECT u.* FROM users u JOIN tmp t ON u.id = t.id;

-- === 4. NOT IN 用 NOT EXISTS ===
-- ❌ NOT IN 遇到 NULL 会错
SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM blacklist);
-- ✅ 更好
SELECT * FROM users u WHERE NOT EXISTS (
  SELECT 1 FROM blacklist b WHERE b.user_id = u.id
);

-- === 5. UPSERT (ON CONFLICT) ===
INSERT INTO users (id, email, name) 
VALUES (1, 'a@x.com', 'Alice')
ON CONFLICT (email) DO UPDATE 
SET name = EXCLUDED.name,
    updated_at = now()
WHERE users.name != EXCLUDED.name;    -- 只在实际变化时更新

-- === 6. 批量插入 ===
-- ❌ 慢
INSERT INTO logs VALUES (1); INSERT INTO logs VALUES (2); ...
-- ✅ 快
INSERT INTO logs VALUES (1), (2), (3), ...;
-- ✅ 最快 (COPY)
\COPY logs FROM '/tmp/logs.csv' WITH (FORMAT csv);

-- === 7. 更新大表分批 ===
-- ❌ 慢 + 锁大量行
UPDATE big_table SET status = 'archived' WHERE created_at < '2020-01-01';
-- ✅ 分批
DO $$
DECLARE
  rows_affected INT;
BEGIN
  LOOP
    WITH cte AS (
      SELECT id FROM big_table 
      WHERE created_at < '2020-01-01' AND status != 'archived'
      LIMIT 10000
    )
    UPDATE big_table b SET status = 'archived'
    FROM cte WHERE b.id = cte.id;
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    EXIT WHEN rows_affected = 0;
    COMMIT;
    PERFORM pg_sleep(0.5);
  END LOOP;
END$$;

-- === 8. 使用 CTE 时注意 (12+ 默认内联优化) ===
-- 加 MATERIALIZED 强制物化 (旧行为)
WITH tmp AS MATERIALIZED (SELECT * FROM big_table WHERE ...)
SELECT * FROM tmp WHERE ...;

-- === 9. JSON 索引 ===
-- JSONB 键查询用 -> 或 ->>
SELECT * FROM events WHERE data->>'type' = 'click';
-- 建 GIN 索引
CREATE INDEX idx_events_data ON events USING gin(data);
-- 特定路径索引
CREATE INDEX idx_events_type ON events((data->>'type'));

-- === 10. 窗口函数替代 GROUP BY 子查询 ===
-- 每用户最近订单
-- ❌ 
SELECT o.* FROM orders o
WHERE o.created_at = (SELECT MAX(created_at) FROM orders WHERE user_id = o.user_id);
-- ✅ 
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
  FROM orders
) t WHERE rn = 1;
```

---

## 九、监控与告警

### 9.1 关键指标

```
PostgreSQL 监控黄金指标:

  连接与会话:
    - 当前连接数 / max_connections
    - 活跃 vs idle vs idle in transaction
    - 等待事件 (锁/IO/网络)
    - 长事务数量

  查询性能:
    - QPS / TPS
    - 慢查询数
    - 缓存命中率 (>99% 良好)
    - 临时文件生成量 (work_mem 不足征兆)

  存储:
    - 数据库大小
    - 表大小 TOP N
    - 索引大小
    - WAL 生成速度
    - 磁盘使用率
    - 表膨胀率

  Vacuum:
    - 死元组比例
    - 最近 autovacuum 时间
    - XID age (环绕警告)
    - autovacuum 挤压情况

  复制:
    - 从库延迟 (lag_bytes / lag_seconds)
    - WAL Sender / Receiver 状态
    - 复制槽 WAL 保留量

  Checkpoint:
    - checkpoint 频率
    - 定时 vs 请求触发
    - buffer 写入量

  系统:
    - CPU / 内存 / 磁盘 IO / 网络
```

### 9.2 postgres_exporter + Prometheus

```yaml
# === 部署 postgres_exporter ===
# docker-compose.yml
services:
  postgres-exporter:
    image: quay.io/prometheuscommunity/postgres-exporter:v0.15.0
    container_name: postgres-exporter
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://monitor:Mon@2026!@postgres:5432/postgres?sslmode=disable
      - PG_EXPORTER_EXTEND_QUERY_PATH=/etc/queries.yaml
    volumes:
      - ./queries.yaml:/etc/queries.yaml

# === 自定义 queries.yaml (业务指标) ===
# 参见 https://github.com/prometheus-community/postgres_exporter/tree/master/queries
```

```yaml
# === Prometheus 抓取配置 ===
scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets:
          - 'pg-master:9187'
          - 'pg-slave1:9187'
          - 'pg-slave2:9187'
        labels:
          env: prod
```

```promql
# === 关键 PromQL ===

# 连接使用率
pg_stat_database_numbackends / pg_settings_max_connections * 100

# QPS
rate(pg_stat_database_xact_commit[1m]) + rate(pg_stat_database_xact_rollback[1m])

# 缓存命中率
sum(rate(pg_stat_database_blks_hit[5m])) 
/ (sum(rate(pg_stat_database_blks_hit[5m])) + sum(rate(pg_stat_database_blks_read[5m])))

# 复制延迟 (bytes)
pg_replication_lag_bytes

# 死锁
rate(pg_stat_database_deadlocks[5m])

# 长事务 (>1 分钟)
pg_stat_activity_max_tx_duration{state="active"} > 60

# 表膨胀
pg_stat_user_tables_n_dead_tup / pg_stat_user_tables_n_live_tup > 0.2

# XID age (环绕警告)
pg_database_xid_age > 1000000000

# WAL 生成速度
rate(pg_stat_wal_written_bytes[5m])
```

### 9.3 告警规则

```yaml
# prometheus-alerts.yml
groups:
  - name: postgres
    rules:
      - alert: PostgreSQLDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL {{ $labels.instance }} is down"

      - alert: PostgreSQLHighConnections
        expr: pg_stat_database_numbackends / on(instance) pg_settings_max_connections > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "连接使用率 > 85%"

      - alert: PostgreSQLReplicationLag
        expr: pg_replication_lag_bytes > 100 * 1024 * 1024   # 100MB
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "复制延迟 > 100MB"

      - alert: PostgreSQLReplicationBroken
        expr: pg_stat_replication_pg_current_wal_lsn - on(application_name) pg_stat_replication_replay_lsn > 500 * 1024 * 1024
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "复制严重滞后 > 500MB, 可能中断"

      - alert: PostgreSQLLowCacheHit
        expr: |
          sum(rate(pg_stat_database_blks_hit[5m])) by (instance)
          / (sum(rate(pg_stat_database_blks_hit[5m])) by (instance) 
             + sum(rate(pg_stat_database_blks_read[5m])) by (instance)) < 0.95
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "PG 缓存命中率 < 95%"

      - alert: PostgreSQLLongTransactions
        expr: pg_stat_activity_max_tx_duration{state="active"} > 300
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "长事务 > 5 分钟"

      - alert: PostgreSQLDeadlocks
        expr: increase(pg_stat_database_deadlocks[10m]) > 5
        labels:
          severity: warning
        annotations:
          summary: "10 分钟内 {{ $value }} 次死锁"

      - alert: PostgreSQLXIDWraparound
        expr: pg_database_xid_age > 1500000000    # 15 亿, 距离 21 亿危险
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "XID 环绕警告! 立即 VACUUM FREEZE"

      - alert: PostgreSQLTableBloat
        expr: |
          pg_stat_user_tables_n_dead_tup > 100000 
          and pg_stat_user_tables_n_dead_tup / pg_stat_user_tables_n_live_tup > 0.2
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "表 {{ $labels.relname }} 死元组 > 20%"

      - alert: PostgreSQLReplicationSlotLag
        expr: pg_replication_slot_current_wal_lsn - pg_replication_slot_confirmed_flush_lsn > 500 * 1024 * 1024
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "复制槽积压 > 500MB, 可能填满磁盘"
```

---

## 十、常见故障处理

### 10.1 故障速查表

| 故障 | 排查 | 解决 |
|:---|:---|:---|
| **连接被拒** | `psql: FATAL: sorry, too many clients` | 增大 max_connections / 用 pgBouncer |
| **磁盘满** | `df -h`, `pg_wal/` 增长 | 检查归档 / archive_command 失败 / 复制槽积压 |
| **表膨胀** | `pgstattuple` 检查 dead_pct | pg_repack / VACUUM FULL (停机) |
| **XID 环绕** | `age(datfrozenxid)` | 立即 VACUUM FREEZE, 严重时数据库停服 |
| **锁等待** | `pg_stat_activity + pg_locks` | 定位阻塞事务, 决定 kill 或等待 |
| **长事务** | `now() - xact_start` | idle_in_transaction_session_timeout / 手动 kill |
| **复制中断** | `pg_stat_replication` | 检查网络 / WAL 是否被删除 / 使用复制槽 |
| **主从延迟** | `pg_replication_lag_bytes` | 检查网络 / 从库 IO / hot_standby_feedback |
| **慢查询** | pg_stat_statements | 找 top / EXPLAIN / 加索引 |
| **OOM** | dmesg / log | 减小 work_mem / max_connections |
| **checksum 错误** | error log: page verification failed | 硬件故障 / 从副本恢复 |
| **role 不存在** | 迁移后应用连接失败 | pg_dumpall --globals-only 补 |

### 10.2 磁盘满紧急处理

```bash
# === WAL 目录爆满 ===

# 1. 确认是 WAL 问题
df -h /pgwal
du -sh /pgdata/16/data/pg_wal
ls /pgdata/16/data/pg_wal | wc -l

# 2. 查看归档进度
sudo -u postgres psql -c "SELECT * FROM pg_stat_archiver;"
# last_failed_wal / last_failed_time 有值 → 归档失败

# 3. 复制槽积压?
sudo -u postgres psql -c "
SELECT slot_name, active, 
       pg_size_pretty(pg_current_wal_lsn() - restart_lsn) AS lag
FROM pg_replication_slots;"

# 4. 紧急处理

# 方案 A: 修复归档 (推荐)
# 检查 archive_command 手工执行
# 如: cp /pgdata/16/data/pg_wal/xxx /pgarchive/16/xxx
# 空间不够就先扩容归档目录

# 方案 B: 删除不活跃的复制槽 (数据不重要时)
sudo -u postgres psql -c "SELECT pg_drop_replication_slot('slot_name');"

# 方案 C: 临时降低 wal_keep_size
sudo -u postgres psql -c "ALTER SYSTEM SET wal_keep_size = '512MB'; SELECT pg_reload_conf();"

# ⚠️ 严禁手动删除 pg_wal/ 里的文件! 除非用 pg_resetwal (数据丢失风险)

# === 数据目录满 ===

# 1. 找大表
sudo -u postgres psql -d myapp -c "
SELECT schemaname || '.' || relname AS table,
       pg_size_pretty(pg_total_relation_size(oid)) AS total,
       pg_size_pretty(pg_relation_size(oid)) AS data,
       pg_size_pretty(pg_indexes_size(oid)) AS index
FROM pg_class c JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE relkind = 'r' AND schemaname NOT IN ('pg_catalog','information_schema')
ORDER BY pg_total_relation_size(oid) DESC LIMIT 20;"

# 2. 找死元组多的表 (膨胀)
sudo -u postgres psql -d myapp -c "
SELECT schemaname || '.' || relname AS table, 
       n_dead_tup, n_live_tup,
       ROUND(n_dead_tup::numeric / NULLIF(n_live_tup, 0) * 100, 2) AS dead_pct
FROM pg_stat_user_tables 
ORDER BY n_dead_tup DESC LIMIT 10;"

# 3. 处理
# pg_repack 在线重组 (推荐)
pg_repack -h localhost -U postgres -d myapp -t big_table

# 或 VACUUM FULL (停机)
sudo -u postgres psql -d myapp -c "VACUUM FULL big_table;"

# 或删除旧数据
sudo -u postgres psql -d myapp -c "DELETE FROM logs WHERE created_at < '2024-01-01';"
sudo -u postgres psql -d myapp -c "VACUUM logs;"
```

### 10.3 XID 环绕紧急处理

```sql
-- === 场景: XID age 接近 20 亿, 数据库即将拒绝服务 ===

-- 1. 查看紧急程度
SELECT datname, age(datfrozenxid), 
       2147483647 - age(datfrozenxid) AS remaining
FROM pg_database
ORDER BY age(datfrozenxid) DESC;

-- 2. 找到 age 最高的表
SELECT c.oid::regclass AS table, age(c.relfrozenxid) AS age
FROM pg_class c
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE c.relkind IN ('r', 'm')
ORDER BY age(c.relfrozenxid) DESC LIMIT 20;

-- 3. 手动 VACUUM FREEZE (最高优先级表)
VACUUM (FREEZE, VERBOSE) big_table;

-- 4. 批量 (但可能持续多小时)
VACUUM FREEZE;

-- 5. 加速 autovacuum (临时)
ALTER SYSTEM SET autovacuum_vacuum_cost_delay = 0;
ALTER SYSTEM SET autovacuum_vacuum_cost_limit = 10000;
SELECT pg_reload_conf();

-- 6. 如已进入只读模式:
-- 需单用户模式启动: postgres --single -D /pgdata/16/data mydb
-- 然后: VACUUM FREEZE;

-- === 预防 ===
-- 定期监控 XID age (Prometheus 告警 > 15 亿)
-- 大表设置更激进的 vacuum:
ALTER TABLE huge_table SET (autovacuum_freeze_max_age = 100000000);
```

### 10.4 主从切换后 timeline 冲突

```bash
# === 场景: promote 后原主库无法直接作为从库 ===
# 错误: FATAL: highest timeline X of the primary is behind recovery timeline Y

# 使用 pg_rewind 修复
systemctl stop postgresql-16

# 1. 确保有 rewind 用户 (在新主库上)
sudo -u postgres psql -h new_master -c "
CREATE USER rewind WITH LOGIN PASSWORD 'Rewind@2026!';
GRANT EXECUTE ON function pg_ls_dir(text, boolean, boolean) to rewind;
GRANT EXECUTE ON function pg_stat_file(text, boolean) to rewind;
GRANT EXECUTE ON function pg_read_binary_file(text) to rewind;
GRANT EXECUTE ON function pg_read_binary_file(text, bigint, bigint, boolean) to rewind;
"

# 2. rewind (要求 wal_log_hints=on 或 data_checksums=true)
sudo -u postgres /usr/pgsql-16/bin/pg_rewind \
  --target-pgdata=/pgdata/16/data \
  --source-server='host=new_master port=5432 user=rewind password=Rewind@2026!' \
  --progress

# 3. 创建 standby.signal + primary_conninfo
sudo -u postgres touch /pgdata/16/data/standby.signal

cat >> /pgdata/16/data/postgresql.auto.conf << 'EOF'
primary_conninfo = 'user=repl password=*** host=new_master port=5432 application_name=old_master'
primary_slot_name = 'old_master_slot'
EOF

# 4. 新主库创建复制槽
sudo -u postgres psql -h new_master -c "SELECT pg_create_physical_replication_slot('old_master_slot');"

# 5. 启动
systemctl start postgresql-16

# 6. 验证
sudo -u postgres psql -c "SELECT pg_is_in_recovery();"    # t
```

---

## 十一、日常运维

### 11.1 pgBouncer 连接池

```bash
# === 场景: 应用连接数飙升, PG 撑不住 ===
# pgBouncer 帮助:
#   - 复用连接 (进程/事务级)
#   - 排队 (拒绝突发)
#   - 大幅降低 PG 后端数量

dnf install -y pgbouncer

# === 配置 ===
cat > /etc/pgbouncer/pgbouncer.ini << 'EOF'
[databases]
myapp = host=127.0.0.1 port=5432 dbname=myapp
* = host=127.0.0.1 port=5432

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
unix_socket_dir = /var/run/pgbouncer

auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# 池化模式
pool_mode = transaction         # session/transaction/statement
                                # transaction: 推荐, 事务结束返还连接

# 连接池大小
max_client_conn = 10000         # 客户端最大连接数
default_pool_size = 100         # 每个 db/user 后端连接数
min_pool_size = 20
reserve_pool_size = 20
reserve_pool_timeout = 5

# 后端连接管理
max_db_connections = 500
max_user_connections = 500
server_lifetime = 3600
server_idle_timeout = 600
server_connect_timeout = 15
server_login_retry = 15

# 客户端
client_login_timeout = 60
client_idle_timeout = 0
query_timeout = 0
query_wait_timeout = 120

# 日志
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid
admin_users = postgres
stats_users = postgres, monitor
EOF

# === 密码文件 ===
# 从 PG 拿密码 hash (scram-sha-256)
sudo -u postgres psql -tAc "SELECT '\"' || rolname || '\" \"' || rolpassword || '\"' FROM pg_authid" \
  > /etc/pgbouncer/userlist.txt

chmod 640 /etc/pgbouncer/*
chown pgbouncer:pgbouncer /etc/pgbouncer/*

# === 启动 ===
systemctl enable --now pgbouncer

# === 应用连接 ===
# 应用改连接 6432 端口 (pgBouncer 而非 PG)
psql -h pgbouncer_host -p 6432 -U app -d myapp

# === 监控 ===
psql -h 127.0.0.1 -p 6432 -U postgres pgbouncer -c "SHOW POOLS;"
psql -h 127.0.0.1 -p 6432 -U postgres pgbouncer -c "SHOW STATS;"
psql -h 127.0.0.1 -p 6432 -U postgres pgbouncer -c "SHOW CLIENTS;"
psql -h 127.0.0.1 -p 6432 -U postgres pgbouncer -c "SHOW SERVERS;"
```

### 11.2 常用命令速查

```sql
-- === 状态查看 ===
-- 版本
SELECT version();

-- 数据库/表大小
\l+                                                        -- 库大小
SELECT pg_size_pretty(pg_database_size('myapp'));          -- 单库
SELECT pg_size_pretty(pg_total_relation_size('users'));    -- 表 + 索引
SELECT pg_size_pretty(pg_relation_size('users'));          -- 仅表
SELECT pg_size_pretty(pg_indexes_size('users'));           -- 仅索引

-- 表 TOP 20
SELECT schemaname || '.' || relname AS table,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) AS size
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC LIMIT 20;

-- 活动会话
SELECT pid, usename, state, wait_event, query FROM pg_stat_activity 
WHERE state != 'idle';

-- 数据库统计
SELECT * FROM pg_stat_database WHERE datname NOT IN ('template0','template1');

-- 表统计
SELECT * FROM pg_stat_user_tables WHERE schemaname = 'public' LIMIT 5;

-- === 用户与权限 ===
\du+                                                       -- 用户
\dp table_name                                             -- 表权限

-- 修改密码
ALTER USER app WITH PASSWORD 'NewPass@2026!';

-- 授权
GRANT SELECT, INSERT, UPDATE ON users TO app;
GRANT USAGE ON SCHEMA public TO app;

-- 撤销
REVOKE INSERT ON users FROM app;

-- 默认权限 (对新建对象生效)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;

-- === 会话管理 ===
-- 结束 idle 事务
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'idle in transaction' AND now() - state_change > interval '5 min';

-- 取消运行中查询 (轻)
SELECT pg_cancel_backend(pid);

-- 强制结束会话 (重)
SELECT pg_terminate_backend(pid);

-- === 系统信息 ===
SHOW ALL;                                                  -- 所有参数
SHOW shared_buffers;
SELECT current_setting('work_mem');
SET work_mem = '64MB';                                     -- 会话级
ALTER SYSTEM SET work_mem = '32MB';                        -- 持久, 需 reload
SELECT pg_reload_conf();

-- 复制状态
SELECT * FROM pg_stat_replication;
SELECT * FROM pg_stat_wal_receiver;
SELECT pg_is_in_recovery();

-- 缓存命中率
SELECT 
  sum(blks_hit) * 100.0 / sum(blks_hit + blks_read) AS cache_hit_pct
FROM pg_stat_database WHERE datname = 'myapp';
```

### 11.3 巡检脚本

```bash
#!/bin/bash
# pg-check.sh — 每日巡检

LOG=/var/log/pg-check-$(date +%Y%m%d).log
export PGPASSWORD='Mon@2026!'
PSQL="psql -U monitor -h localhost -d postgres -t -A"

exec > ${LOG} 2>&1
echo "=== PostgreSQL Daily Check $(date) ==="

echo
echo "=== 1. 服务与版本 ==="
systemctl status postgresql-16 --no-pager | head -5
${PSQL} -c "SELECT version();"

echo
echo "=== 2. 连接情况 ==="
${PSQL} -c "
SELECT state, count(*) FROM pg_stat_activity GROUP BY state
UNION ALL SELECT 'MAX_CONN', current_setting('max_connections')::int;"

echo
echo "=== 3. 数据库大小 ==="
${PSQL} -c "
SELECT datname, pg_size_pretty(pg_database_size(datname))
FROM pg_database WHERE datistemplate = false
ORDER BY pg_database_size(datname) DESC;"

echo
echo "=== 4. 缓存命中率 ==="
${PSQL} -c "
SELECT ROUND(sum(blks_hit) * 100.0 / NULLIF(sum(blks_hit + blks_read), 0), 2) 
       AS cache_hit_pct FROM pg_stat_database;"

echo
echo "=== 5. 复制状态 ==="
${PSQL} -c "SELECT client_addr, state, sync_state, 
             pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)) AS lag
             FROM pg_stat_replication;"

echo
echo "=== 6. 长事务 (>1min) ==="
${PSQL} -c "
SELECT pid, usename, datname, now() - xact_start AS duration,
       substring(query, 1, 100) AS query
FROM pg_stat_activity 
WHERE xact_start IS NOT NULL AND now() - xact_start > interval '1 minute'
ORDER BY duration DESC LIMIT 10;"

echo
echo "=== 7. 死元组 TOP 10 ==="
${PSQL} -c "
SELECT schemaname || '.' || relname AS table, n_live_tup, n_dead_tup,
       ROUND(n_dead_tup::numeric / NULLIF(n_live_tup, 0) * 100, 2) AS dead_pct,
       last_autovacuum
FROM pg_stat_user_tables 
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC LIMIT 10;"

echo
echo "=== 8. XID age ==="
${PSQL} -c "
SELECT datname, age(datfrozenxid) AS xid_age,
       CASE WHEN age(datfrozenxid) > 1500000000 THEN 'CRITICAL'
            WHEN age(datfrozenxid) > 1000000000 THEN 'WARNING' 
            ELSE 'OK' END AS status
FROM pg_database ORDER BY xid_age DESC;"

echo
echo "=== 9. 复制槽 ==="
${PSQL} -c "
SELECT slot_name, slot_type, active, 
       pg_size_pretty(pg_current_wal_lsn() - restart_lsn) AS wal_retention
FROM pg_replication_slots;"

echo
echo "=== 10. 慢查询 TOP 5 ==="
${PSQL} -c "
SELECT substring(query, 1, 80) AS query, calls,
       ROUND(mean_exec_time::numeric, 2) AS mean_ms,
       ROUND(total_exec_time::numeric / 1000, 2) AS total_sec
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 5;"

echo
echo "=== 11. 磁盘 ==="
df -h /pgdata /pgwal /pgarchive /pgbackup

echo
echo "=== 巡检完成 $(date) ==="

mail -s "PG Daily Check $(hostname)" dba@example.com < ${LOG}
```

---

## 十二、生产最佳实践

### 12.1 高可用架构

```
┌──────────────────────────────────────────────────────────┐
│              生产 PostgreSQL 高可用架构                     │
│                                                          │
│                    应用集群                                │
│                        │                                 │
│              ┌─────────▼─────────┐                       │
│              │   HAProxy / Keep  │  VIP 漂移              │
│              │   RW:5432/RO:5433 │                       │
│              └─────────┬─────────┘                       │
│                        │                                 │
│                        ▼                                 │
│              ┌─────────────────┐                         │
│              │   pgBouncer     │  连接池 + 事务级复用       │
│              │  (transaction)  │                         │
│              └─────────┬───────┘                         │
│                        │                                 │
│         ┌──────────────┼──────────────┐                  │
│         │              │              │                  │
│         ▼              ▼              ▼                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │Patroni node1│ │Patroni node2│ │Patroni node3│        │
│  │ + PG Leader │ │ + PG Replica│ │ + PG Replica│        │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘        │
│         │               │               │                │
│         └───────────────┼───────────────┘                │
│                         ▼                                │
│              ┌─────────────────┐                         │
│              │  etcd 集群 (3)  │  DCS 一致性存储           │
│              └─────────────────┘                         │
│                                                          │
│  归档 & 备份:                                            │
│    - pgBackRest 每周全备 + 每日差异 + 每小时增量           │
│    - WAL 实时归档到 S3 (支持 PITR)                        │
│                                                          │
│  监控:                                                    │
│    - postgres_exporter + Prometheus + Grafana            │
│    - 关键: 连接/复制延迟/XID/死元组/慢查询                  │
└──────────────────────────────────────────────────────────┘
```

### 12.2 参数配置速查

| 参数 | 推荐值 | 说明 |
|:---|:---|:---|
| `shared_buffers` | 内存 25% | 最重要, 类 InnoDB BP |
| `effective_cache_size` | 内存 75% | 优化器提示 |
| `work_mem` | 32MB-64MB | 每连接每操作, 谨慎 |
| `maintenance_work_mem` | 1GB-2GB | VACUUM/INDEX |
| `wal_level` | replica/logical | 复制必需 |
| `synchronous_commit` | on | 事务持久性 |
| `max_wal_size` | 8GB-32GB | 影响 checkpoint 频率 |
| `checkpoint_timeout` | 15min | 频率 |
| `checkpoint_completion_target` | 0.9 | 平滑刷盘 |
| `max_connections` | 500 (配 pgBouncer) | 太多有害 |
| `random_page_cost` | SSD=1.1, HDD=4 | 优化器 IO 估算 |
| `effective_io_concurrency` | SSD=200, HDD=2 | 并发 IO |
| `autovacuum_vacuum_scale_factor` | 0.02-0.05 | 生产建议调小 |
| `max_worker_processes` | >= CPU 核数 | 并行查询 |
| `max_parallel_workers_per_gather` | 4 | 单查询并行度 |
| `archive_mode` | on | 归档必开 |
| `hot_standby` | on | 从库可读 |
| `hot_standby_feedback` | on | 减少查询冲突 |
| `wal_keep_size` | 4GB-16GB | 主库保留 WAL |
| `password_encryption` | scram-sha-256 | 安全 |

### 12.3 迁移与升级

```bash
# === 大版本升级方案 ===

# 方案 1: pg_upgrade (原地升级, 需停机)
# 优势: 快 (只重建 catalog), 无需拷贝数据
# 劣势: 需要停机 (通常 <10 分钟)

# 停机 → 装新版本 → pg_upgrade → 启动新版本
sudo -u postgres /usr/pgsql-16/bin/pg_upgrade \
  --old-datadir=/pgdata/15/data \
  --new-datadir=/pgdata/16/data \
  --old-bindir=/usr/pgsql-15/bin \
  --new-bindir=/usr/pgsql-16/bin \
  --link                                # 硬链接, 快 (无法回滚)
  # --check                             # 只检查兼容性, 不升级

# 方案 2: 逻辑复制升级 (零停机, 推荐核心业务)
# 见第五章 5.3

# 方案 3: pg_dump/restore (小库, 支持跨版本)
pg_dump -h old_host -Fc -d myapp | pg_restore -h new_host -d myapp

# === Schema 迁移工具 ===
# - Flyway:      SQL 版本化 (Java)
# - Liquibase:   XML/YAML/SQL, 支持多库
# - sqitch:      Perl, 灵活
# - Alembic:     Python (SQLAlchemy)
# - Bytebase:    带审批工作流
```

### 12.4 安全加固

```conf
# pg_hba.conf 最佳实践
# 1. 拒绝远程 postgres 登录
host all postgres 0.0.0.0/0 reject

# 2. 强制 SSL
hostssl all all 0.0.0.0/0 scram-sha-256

# 3. 限制来源 IP
host myapp app 10.0.1.0/24 scram-sha-256    # 只允许应用网段

# 4. 复制专用账号
host replication repl 10.0.1.0/24 scram-sha-256

# postgresql.conf
# 强制 SCRAM-SHA-256
password_encryption = scram-sha-256

# SSL
ssl = on
ssl_min_protocol_version = 'TLSv1.2'
ssl_cert_file = '/etc/postgres/server.crt'
ssl_key_file = '/etc/postgres/server.key'

# 数据加密 (需扩展)
CREATE EXTENSION pgcrypto;
UPDATE users SET password = crypt('secret', gen_salt('bf'));
SELECT * FROM users WHERE password = crypt('secret', password);

# 审计 (pgAudit 扩展)
# shared_preload_libraries = 'pgaudit'
# pgaudit.log = 'write, ddl'

# 定期漏洞扫描
# - CVE 关注 postgresql.org/support/security/
# - 备份数据加密 (pgBackRest --cipher-type)
```

---

## 十三、速查表

### 13.1 常用命令

| 场景 | 命令 |
|:---|:---|
| 连接 | `psql -h host -p 5432 -U user -d db` |
| 备份单库 | `pg_dump -Fc -Z9 -d db > db.dump` |
| 恢复 | `pg_restore -j 8 -d db db.dump` |
| 全局备份 | `pg_dumpall --globals-only` |
| 物理备份 | `pgbackrest --stanza=x --type=full backup` |
| 基础备份 | `pg_basebackup -D /path -Fp -Xs -P -R` |
| 慢查询分析 | `pg_stat_statements` 查询 |
| VACUUM | `VACUUM (VERBOSE, ANALYZE) tbl` |
| 复制状态 | `SELECT * FROM pg_stat_replication` |
| Promote | `pg_ctl promote` 或 `SELECT pg_promote()` |
| 长事务 | `pg_stat_activity` 查 xact_start |
| Kill 会话 | `SELECT pg_terminate_backend(pid)` |
| 重载配置 | `SELECT pg_reload_conf()` 或 `pg_ctl reload` |
| 表膨胀 | `pgstattuple` / `pg_repack` |

### 13.2 关键文件路径

| 文件 | 路径 | 用途 |
|:---|:---|:---|
| 主配置 | `$PGDATA/postgresql.conf` | 主配置 |
| 认证 | `$PGDATA/pg_hba.conf` | 客户端认证 |
| WAL | `$PGDATA/pg_wal/` | Write-Ahead Log |
| 数据 | `$PGDATA/base/` | 数据文件 |
| 归档 | `/pgarchive/` | WAL 归档 |
| 日志 | `/var/log/postgres/` | 运行日志 |
| Socket | `/tmp/.s.PGSQL.5432` | Unix socket |
| Pid | `$PGDATA/postmaster.pid` | 进程 ID |

### 13.3 psql 元命令

| 命令 | 用途 |
|:---|:---|
| `\l` / `\l+` | 列出数据库 |
| `\c dbname` | 切换数据库 |
| `\d` / `\d+` | 列出表 |
| `\d tbl` | 表结构 |
| `\di` | 索引 |
| `\dv` | 视图 |
| `\df` | 函数 |
| `\dn` | schema |
| `\du` | 用户 |
| `\dp` / `\z` | 权限 |
| `\x` | 竖排显示 (类 mysql \G) |
| `\timing` | 显示执行时间 |
| `\watch 5` | 每 5 秒重复上一条 |
| `\copy tbl FROM 'x.csv' CSV` | 客户端导入 |
| `\i script.sql` | 执行文件 |
| `\?` | 帮助 |
| `\q` | 退出 |

### 13.4 推荐工具清单

| 类别 | 工具 | 用途 |
|:---|:---|:---|
| 客户端 | psql / pgAdmin / DBeaver / DataGrip | 交互式查询 |
| 备份 | pgBackRest / Barman / WAL-G | 物理备份 + PITR |
| HA | Patroni / repmgr / pg_auto_failover | 高可用切换 |
| 连接池 | pgBouncer / PgCat / Odyssey | 连接池 |
| 迁移 | pgloader / pg_chameleon | 异构迁移 |
| 监控 | postgres_exporter / pgwatch2 / pganalyze | Prometheus / 商业 |
| SQL 分析 | pg_stat_statements / pgBadger / pg_hero | 慢查询 |
| 在线重组 | pg_repack / pg_squeeze | 消除膨胀 |
| 分库分表 | Citus / pg_partman | 分布式 / 分区 |
| 逻辑复制 | pglogical / Debezium | 变更捕获 |
| 压测 | pgbench / HammerDB | 性能测试 |
| Schema 迁移 | Flyway / Liquibase / sqitch | 版本管理 |
| 审计 | pgAudit | 操作审计 |

---

*最后更新: 2026-07-14*
