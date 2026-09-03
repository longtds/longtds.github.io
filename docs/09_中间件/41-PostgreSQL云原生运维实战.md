# PostgreSQL 云原生运维实战

> PostgreSQL 跑在 K8s 上和 MySQL 有什么不同？Operator 怎么选？复制槽、WAL、扩展、流复制怎么和 K8s 结合？本文覆盖 PostgreSQL 云原生运维全链路：Operator 选型、存储规划、高可用部署、备份恢复、监控告警、性能调优、故障排查，重点突出 PG 特有的云原生挑战与解法。

---

## 一、选型决策框架

### 1.1 PG 云原生和 MySQL 云原生的本质差异

| 维度 | MySQL | PostgreSQL |
|------|-------|-----------|
| **复制模型** | 主从 binlog 复制 / Galera / MGR | 流复制（物理 / 逻辑） |
| **故障转移** | 相对成熟，工具多 | 需要 PG 自己的工具（Patroni / repmgr / pg_auto_failover） |
| **主备切换** | 切换后从库提升为主，机制简单 | 提升后老主需做 basebackup 重新加入，复杂 |
| **扩展能力** | 插件生态弱 | 扩展极强（pg_stat_statements / PostGIS / timescaledb / Citus） |
| **存储引擎** | 可插拔（InnoDB 为主） | 单引擎（堆表 + 多版本） |
| **真空（VACUUM）** | 无此概念 | PG 特有，死元组膨胀是云原生环境的重点运维项 |
| **连接管理** | 原生连接池弱 | 需要 PgBouncer（K8s 通常 sidecar 或单独部署） |
| **WAL 机制** | binlog + redo log 两套 | 一套 WAL，同时承担崩溃恢复和复制 |

**关键结论：** PG 云原生的复杂度高于 MySQL，主要在**故障转移自动化**和**膨胀管理**两件事上。好处是 PG 扩展生态强，云原生下可以按需动态加载扩展。

### 1.2 Operator 选型对比

| 维度 | Zalando Spilo / Postgres Operator | CrunchyData Postgres Operator | KubeDB PostgreSQL | CloudNativePG (CNCF) |
|------|--------------------------------|----------------------------|------------------|---------------------|
| **发起方** | Zalando | Crunchy Data | KubeDB（AppsCode） | EDBS + 社区（CNCF 孵化） |
| **底层 HA 工具** | Patroni + etcd | 自研（pgBackRest + Patroni 可选） | 自研 + repmgr | 自研（基于 K8s API） |
| **高可用模式** | 流复制 + Patroni 自动故障转移 | 流复制 + 自动故障转移 | 流复制 + 自动切换 | 流复制 + 内置 HA controller |
| **备份恢复** | WAL-G / pgBackRest | pgBackRest（功能最强） | WAL-G / 自定义 | pg_basebackup + 归档 |
| **连接池** | 内置 PgBouncer sidecar | 可选 PgBouncer | 内置 PgBouncer | 内置 PgBouncer |
| **监控** | Exporter 内置 | Exporter + 详细指标 | Exporter | Exporter + 自定义指标 |
| **扩展支持** | 支持（预编译扩展包） | 支持（自定义镜像） | 支持 | 支持 |
| **社区活跃度** | 高（GitHub 4.2k+ star） | 高 | 中（商业 + 开源双轨） | 上升快（CNCF 背书） |
| **生产成熟度** | ⭐⭐⭐⭐⭐（Zalando 大规模生产） | ⭐⭐⭐⭐⭐（企业级） | ⭐⭐⭐⭐ | ⭐⭐⭐（新但活跃） |
| **适用场景** | 通用生产环境 | 对备份恢复要求高的企业 | 多数据库统一管理 | 纯云原生理念、CNCF 生态对齐 |

**推荐选型路径：**

```
第一次上 PG on K8s？
├─ 团队有 K8s 经验但 PG 经验一般 → Zalando Spilo（文档多，踩坑经验丰富）
├─ 企业级、备份恢复要求高 → CrunchyData
├─ 已经在用 KubeDB 管其他数据库 → KubeDB
└─ 想要 CNCF 项目、社区驱动 → CloudNativePG

超大规模（> 100 实例）？
→ StackGres（专门做 PG 云原生平台）

极简场景（单实例 + 定时备份）？
→ 不用 Operator，StatefulSet + CronJob + pg_basebackup
```

### 1.3 部署架构选型

```
架构 1: 单实例 StatefulSet
  ── PostgreSQL Pod
  └─ PVC
  适用: 开发测试、非核心小库

架构 2: 主从 + PgBouncer（最通用）
  ┌─ Primary (StatefulSet-0) ─ PVC
  ├─ Replica-1 (StatefulSet-1) ─ PVC
  ├─ Replica-2 (StatefulSet-2) ─ PVC
  └─ PgBouncer (Deployment)  ─ Service
  适用: 大部分生产场景，读写分离

架构 3: Patroni 管理的高可用集群（Operator 标配）
  ┌─ Node-0 (Primary)  ─ PVC
  ├─ Node-1 (Replica)  ─ PVC
  ├─ Node-2 (Replica)  ─ PVC
  └─ Patroni Agent (每个 Pod 内置)
  适用: 核心库、自动故障转移

架构 4: Citus 分布式集群（水平扩展）
  ┌─ Coordinator Node
  ├─ Worker-1
  ├─ Worker-2
  └─ Worker-N
  适用: 超大库、多租户、时序数据
```

---

## 二、存储规划

### 2.1 存储类型选择（和 MySQL 基本一致，但 PG 有特殊要求）

| 存储类型 | 性能 | 可靠性 | 成本 | PG 适用性 |
|---------|------|--------|------|----------|
| **LocalNVMe** | ⭐⭐⭐⭐⭐ | ⭐⭐ | 高 | ✅ OLTP 核心库 |
| **Local SSD** | ⭐⭐⭐⭐ | ⭐⭐ | 中 | ✅ 通用生产 |
| **Ceph RBD** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中 | ⚠️ 注意 WAL 延迟 |
| **Longhorn** | ⭐⭐ | ⭐⭐⭐⭐ | 中 | ❌ 不建议核心库 |
| **云厂商 SSD 云盘** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 高 | ✅ 云上部署 |
| **NFS** | ⭐ | ⭐⭐⭐ | 低 | ❌ 绝对不能用 PG 数据目录 |

**PG 特有要求：**
- **WAL 和数据目录分盘**：PG 的 WAL 是顺序写，数据是随机读写。在云环境中，把 WAL 放到更快的盘（或单独 PV）可以显著提升性能
- **fsync 语义必须正确**：PG 依赖 fsync 保证持久性，存储层不能"假 fsync"（某些虚拟化存储有这个问题）
- **O_DIRECT 支持**：PG 12+ 支持 `io_method=fsync` / `open_datasync` / `syncfs`，O_DIRECT 在 K8s 某些 CSI 驱动下有兼容问题

### 2.2 PG 特有：WAL 和数据目录分离

```yaml
# StatefulSet 中定义两个 PVC
volumeClaimTemplates:
  - metadata:
      name: pg-data          # 数据目录（随机读写为主）
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: ceph-rbd-mysql   # 通用存储
      resources:
        requests:
          storage: 100Gi
  - metadata:
      name: pg-wal           # WAL 目录（顺序写，延迟敏感）
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: ssd-fast   # 更快的存储
      resources:
        requests:
          storage: 20Gi
```

对应 PG 配置：

```ini
# postgresql.conf
data_directory = '/var/lib/postgresql/data'
# WAL 通过 initdb 时的 --waldir 参数或软链接指定
# 或使用环境变量 PGDATA + 启动脚本创建符号链接
```

### 2.3 PVC 规划原则

| 项目 | 建议值 | 说明 |
|------|--------|------|
| **数据目录大小** | 预估 2 年数据量 × 1.5 | 留 50% 余量给膨胀、索引、临时表 |
| **WAL 大小** | 数据目录的 10-20% | 取决于 wal_keep_size / 复制槽 / 归档速度 |
| **reclaimPolicy** | Retain | 防止误删 |
| **accessModes** | ReadWriteOnce | PG 单写，不需要 RWO-Many |
| **文件系统** | XFS | 大文件下性能好，支持在线扩容 |
| **挂载参数** | noatime, nodiratime | 减少元数据写入 |

---

## 三、部署实战

### 3.1 Zalando Postgres Operator 部署（最成熟的开源方案）

```bash
# 1. 安装 Operator
helm repo add postgres-operator https://opensource.zalando.com/postgres-operator/charts/postgres-operator
helm install postgres-operator postgres-operator/postgres-operator   --namespace postgres-operator   --create-namespace   --version 1.10.0

# 2. 部署 PG 集群
kubectl apply -f - <<EOF
apiVersion: "acid.zalan.do/v1"
kind: postgresql
metadata:
  name: pg-cluster
  namespace: database
spec:
  teamId: "myteam"
  volume:
    size: 100Gi
    storageClass: "ceph-rbd-mysql"
  numberOfInstances: 3
  users:
    app_user:       # 业务用户
      - superuser
      - createdb
  databases:
    app_db: app_user   # 数据库名: 属主
  postgresql:
    version: "15"
    parameters:       # 自定义 PG 参数
      shared_buffers: "8GB"
      effective_cache_size: "24GB"
      work_mem: "16MB"
      maintenance_work_mem: "2GB"
      max_connections: "500"
  resources:
    requests:
      cpu: "4"
      memory: "8Gi"
    limits:
      cpu: "16"
      memory: "32Gi"
  sidecars:
    - name: "exporter"
      image: "prometheuscommunity/postgres-exporter:v0.12.0"
      ports:
        - name: exporter
          containerPort: 9187
  enableMasterLoadBalancer: false
  enableReplicaLoadBalancer: false
  enableConnectionPooler: true    # 启用 PgBouncer sidecar
  connectionPooler:
    numberOfInstances: 3
    mode: "transaction"
    resources:
      requests:
        cpu: "500m"
        memory: "256Mi"
EOF
```

**Zalando Operator 自动创建的资源：**
```
StatefulSet: pg-cluster（3 副本）
Service:
  ├─ pg-cluster            → 主库（写 + 读）
  ├─ pg-cluster-repl       → 从库（只读）
  └─ pg-cluster-pooler     → PgBouncer 连接池
ConfigMap: pg-cluster-config
Secret:
  ├─ pg-cluster.credentials.postgresql.acid.zalan.do  (超级用户)
  └─ app_user.credentials.postgresql.acid.zalan.do    (业务用户)
Endpoints: 自动维护主从节点列表
```

### 3.2 原生 StatefulSet + Patroni（无 Operator 场景）

如果你不想引入 Operator，可以用 StatefulSet + Patroni + DCS（Distributed Configuration Store）自己搭。Patroni 是 PG 高可用的事实标准：

```yaml
# DCS 用 K8s API（不需要单独部署 etcd）
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: database
spec:
  serviceName: postgres-headless
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      serviceAccountName: postgres-patroni  # 给 Patroni 访问 K8s API 的权限
      containers:
        - name: postgres
          image: patroni:3.2-pg15
          env:
            - name: PATRONI_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: PATRONI_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
            - name: PATRONI_SCOPE
              value: "pg-cluster"
            - name: PATRONI_KUBERNETES_LABELS
              value: '{"app": "postgres"}'
            - name: PATRONI_KUBERNETES_USE_ENDPOINTS
              value: "true"
            - name: PATRONI_REPLICATION_USERNAME
              value: "replicator"
            - name: PATRONI_REPLICATION_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: replication-password
            - name: PATRONI_SUPERUSER_USERNAME
              value: "postgres"
            - name: PATRONI_SUPERUSER_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: superuser-password
          ports:
            - name: postgres
              containerPort: 5432
            - name: patroni
              containerPort: 8008
          volumeMounts:
            - name: pg-data
              mountPath: /var/lib/postgresql/data
            - name: pg-wal
              mountPath: /var/lib/postgresql/wal
          livenessProbe:
            httpGet:
              path: /liveness
              port: 8008
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /readiness
              port: 8008
            initialDelaySeconds: 5
            periodSeconds: 3
  volumeClaimTemplates:
    - metadata:
        name: pg-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ceph-rbd-mysql
        resources:
          requests:
            storage: 100Gi
    - metadata:
        name: pg-wal
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ssd-fast
        resources:
          requests:
            storage: 20Gi
```

**Patroni 自动管理的事情：**
- 自动选主（基于 Raft / K8s API / etcd）
- 自动创建从库（pg_basebackup 初始化）
- 主库故障自动切换（RTO < 30s）
- 自动处理复制槽（避免 WAL 堆积）
- 提供 REST API 供监控和管理

### 3.3 Service 设计

```yaml
# Headless Service（StatefulSet 必须 + Patroni 节点发现）
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
  namespace: database
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
    - port: 5432
      name: postgres

---
# 主库 Service（写流量）
# 用 label selector 指向当前主节点（Patroni 会给主 Pod 打 role=master 标签）
apiVersion: v1
kind: Service
metadata:
  name: postgres-master
  namespace: database
spec:
  selector:
    app: postgres
    role: master      # Patroni 自动维护这个标签
  ports:
    - port: 5432
      name: postgres

---
# 从库只读 Service
apiVersion: v1
kind: Service
metadata:
  name: postgres-slave
  namespace: database
spec:
  selector:
    app: postgres
    role: replica
  ports:
    - port: 5432
      name: postgres

---
# PgBouncer 连接池 Service（推荐业务侧连这个）
apiVersion: v1
kind: Service
metadata:
  name: pgbouncer
  namespace: database
spec:
  selector:
    app: pgbouncer
  ports:
    - port: 5432
      name: pgbouncer
```

---

## 四、高可用与故障转移

### 4.1 各方案 RPO/RTO 对比

| 方案 | RPO | RTO | 切换方式 | 适用场景 |
|------|-----|-----|---------|---------|
| Patroni + 同步流复制 | ~0 | < 30s | 自动 | 核心库 |
| Patroni + 异步流复制 | 可能丢失几秒数据 | < 30s | 自动 | 通用生产 |
| 手动手动主从 | 可能丢失 | 5-15 min | 手动 | 非核心 |
| 单实例 + 备份 | 取决于备份频率 | 取决于恢复速度 | 手动 | 开发测试 |

### 4.2 PG 故障转移的特殊性（和 MySQL 的区别）

| 特性 | MySQL | PostgreSQL |
|------|-------|-----------|
| **提升从库** | `CHANGE MASTER TO` + `START SLAVE` | `promote` 命令（需要触发） |
| **老主重新加入** | 直接 change master 即可 | 需要做 basebackup 重新初始化（时间取决于数据量） |
| **复制中断检测** | 延迟增大 / IO thread 停 | WAL 接收停止，需要看复制槽状态 |
| **脑裂防护** | 靠 MHA / Orchestrator | 靠 DCS（etcd/K8s API）做 lease，天然防脑裂 |
| **复制槽** | 无此概念 | 有 replication slot，防止从库断开后 WAL 被删 |

### 4.3 故障场景与处理流程

#### 场景 1: 从库 Pod 挂了

```
现象: postgres-1 Pod CrashLoop / NotReady

自动处理:
  1. K8s 检测到 Pod 不健康
  2. 重建 Pod，重新挂载 PVC
  3. Patroni Agent 启动
  4. 检查本地数据是否有效
     ├─ 有效 → 连接主库，重新加入复制
     └─ 数据损坏/落后太多 → 自动做 pg_basebackup 从主库重新拉
  5. 追上后就绪，流量回到 Service
```

#### 场景 2: 主库挂了（Patroni 自动切换）

```
1. Patroni 检测到主库心跳超时（默认 10s）
2. DCS 中的 leader key 过期释放
3. 从库之间发起选举（哪个从库数据最新，哪个被提升）
4. 被选中的从库执行 promote，变为主库
5. 其他从库自动 change master 指向新主
6. Patroni 更新 Pod 标签（role=master / replica）
7. Service 自动把流量切到新主
8. 老主恢复后 → 自动作为新主的从库加入

整个过程 RTO < 30s，RPO ≈ 0（同步模式）
```

#### 场景 3: WAL 堆积（复制槽问题）

```
现象: 磁盘空间持续增长，WAL 文件越来越多

常见原因:
  1. 从库长时间断开（复制槽还在）
  2. 逻辑复制消费端卡住
  3. 归档失败（archive_command 一直返回非 0）

排查:
  -- 查复制槽状态
  SELECT slot_name, slot_type, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) as lag
  FROM pg_replication_slots;

  -- 查归档状态
  SELECT * FROM pg_stat_archiver;

处理:
  1. 先找到并修复根本原因（从库恢复 / 归档修复）
  2. 紧急情况下删除不再需要的复制槽（⚠️ 谨慎操作）
     SELECT pg_drop_replication_slot('slot_name');
```

### 4.4 防脑裂：DCS + Pod 反亲和 + PDB

```yaml
# PodDisruptionBudget
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: postgres-pdb
  namespace: database
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: postgres

# 节点反亲和（强制跨节点分布）
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: postgres
        topologyKey: kubernetes.io/hostname

# 最佳实践: 跨可用区分布
# topologyKey: topology.kubernetes.io/zone
```

---

## 五、备份与恢复

### 5.1 PG 备份方式对比

| 方式 | 工具 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|---------|
| **逻辑备份** | pg_dump / pg_dumpall | 简单可靠，可跨版本恢复，可选择性恢复 | 大库慢，恢复慢 | 小库 (< 50GB)、跨版本迁移 |
| **物理备份** | pg_basebackup | 快，全量一致 | 只能同版本同架构恢复，不能选表恢复 | 全量备份基线 |
| **增量备份** | pgBackRest / WAL-G | 支持增量，压缩好，并行恢复 | 需要额外工具 | 生产环境首选 |
| **存储快照** | CSI Snapshot | 秒级快照，不影响 DB 性能 | 依赖存储，不能做 PITR | 快速回滚、开发克隆 |

### 5.2 生产推荐：pgBackRest

pgBackRest 是 PG 备份的事实标准，比原生 pg_basebackup 强大很多：

```
特性:
├─ 全量 / 增量 / 差异 三种备份模式
├─ 并行备份 / 并行恢复
├─ 内置压缩（gzip / bzip2 / lz4 / zstd）
├─ 备份到本地 / S3 / Azure / GCS
├─ PITR（时间点恢复）
├─ 自动过期清理
└─ 备份校验
```

### 5.3 CronJob + pgBackRest 备份方案

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pg-backup
  namespace: database
spec:
  schedule: "0 2 * * 0"     # 周日凌晨 2 点全量
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: pgbackrest/pgbackrest:2.47
              command:
                - bash
                - "-c"
                - |
                  set -e
                  # 全量备份
                  pgbackrest --stanza=main --type=full backup
                  # 显示备份信息
                  pgbackrest info
                  # 清理过期备份（保留 7 天）
                  pgbackrest --stanza=main --retention-full=4 expire
              env:
                - name: PGBACKREST_REPO1_PATH
                  value: "/backup"
                - name: PGBACKREST_DB_HOST
                  value: "postgres-master.database.svc.cluster.local"
                - name: PGBACKREST_DB_PORT
                  value: "5432"
                - name: PGBACKREST_DB_USER
                  value: "postgres"
                - name: PGBACKREST_DB_PASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: postgres-secret
                      key: superuser-password
              volumeMounts:
                - name: backup-storage
                  mountPath: /backup
          restartPolicy: OnFailure
          volumes:
            - name: backup-storage
              persistentVolumeClaim:
                claimName: pg-backup-pvc
---
# 增量备份（每周一到周六）
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pg-backup-incr
  namespace: database
spec:
  schedule: "0 2 * * 1-6"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: pgbackrest/pgbackrest:2.47
              command: ["pgbackrest", "--stanza=main", "--type=incr", "backup"]
              env: ...  # 同上
          restartPolicy: OnFailure
```

### 5.4 WAL 归档（PITR 基础）

```ini
# postgresql.conf
archive_mode = on
archive_command = 'pgbackrest --stanza=main archive-push %p'
# 或用基本方式
# archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'
restore_command = 'pgbackrest --stanza=main archive-get %f %p'
```

### 5.5 恢复流程

```bash
# 方式 1: pgBackRest 恢复（推荐）

# 1. 停止目标 PG
kubectl exec postgres-0 -- pg_ctl stop -m fast

# 2. 恢复到指定时间点
pgbackrest --stanza=main   --type=time "--target=2026-06-20 10:30:00"   --target-action=promote   restore

# 3. 启动 PG，自动 replay WAL 到目标点
kubectl exec postgres-0 -- pg_ctl start

# 4. 验证
psql -c "SELECT pg_is_in_recovery();"  # 应该是 false（已 promote）
psql -c "SELECT now();"                # 时间对不对
```

```bash
# 方式 2: pg_basebackup + WAL 恢复（基础方式）

# 1. 拉取全量基础备份
pg_basebackup -h 主库地址 -D /var/lib/postgresql/data   -U replicator -Fp -Xs -P -R

# 2. 配置 recovery.conf（PG 12+ 用 recovery.signal）
touch /var/lib/postgresql/data/recovery.signal
echo "restore_command = 'cp /archive/%f %p'" >> postgresql.conf
echo "recovery_target_time = '2026-06-20 10:30:00'" >> postgresql.conf
echo "recovery_target_action = 'promote'" >> postgresql.conf

# 3. 启动，自动回放
pg_ctl start
```

### 5.6 CSI 快照备份（快速克隆）

```yaml
# K8s VolumeSnapshot（需存储支持 CSI Snapshot）
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: pg-data-snapshot-20260620
  namespace: database
spec:
  volumeSnapshotClassName: csi-rbd-snapclass
  source:
    persistentVolumeClaimName: pg-data-postgres-0
```

**适用场景：**
- 快速创建开发/测试库（秒级）
- 大版本升级前做快照兜底
- 注意：快照不是完整备份，不能替代 pgBackRest

---

## 六、监控与告警

### 6.1 指标采集架构

```
PostgreSQL Pod
  └─ postgres_exporter (sidecar)
       │  :9187/metrics
       ▼
  Prometheus (ServiceMonitor)
       │
       ▼
  Grafana Dashboard + Alertmanager
```

### 6.2 postgres_exporter 部署

```yaml
containers:
  - name: postgres
    image: postgres:15
    ...
  - name: exporter
    image: prometheuscommunity/postgres-exporter:v0.15.0
    env:
      - name: DATA_SOURCE_NAME
        value: "postgresql://exporter:password@localhost:5432/postgres?sslmode=disable"
    ports:
      - name: metrics
        containerPort: 9187
    args:
      - --extend.query-path=/etc/postgres_exporter/queries.yaml
    volumeMounts:
      - name: exporter-queries
        mountPath: /etc/postgres_exporter
volumes:
  - name: exporter-queries
    configMap:
      name: postgres-exporter-queries
```

### 6.3 关键指标清单（PG 特有）

| 类别 | 指标名 | 正常范围 | 告警阈值 | 说明 |
|------|--------|---------|---------|------|
| **可用性** | pg_up | 1 | == 0 | PG 是否存活 |
| | pg_replication_is_replica | 0/1 | 主库应为 0 | 是否在恢复模式 |
| **复制** | pg_replication_lag_bytes | < 100MB | > 1GB | 复制延迟（字节） |
| | pg_replication_lag_seconds | < 30s | > 300s | 复制延迟（时间） |
| | pg_replication_slot_active | 1 | == 0（非预期） | 复制槽是否活跃 |
| **连接** | pg_stat_database_numbackends | < 80% max_conn | > 80% | 活跃连接数 |
| | pg_stat_database_xact_commit_rate | - | 突降 50% | 事务提交速率 |
| **性能** | pg_stat_database_tup_returned_rate | - | 突增 | 全表扫描激增可能索引失效 |
| | pg_stat_statements_total_time | - | 慢查询 | SQL 执行时间 |
| **膨胀** | pg_stat_user_tables_n_dead_tup | < 10% live_tup | > 30% | 死元组比例 |
| | pg_stat_user_tables_autovacuum_count | - | 长时间为 0 | autovacuum 不工作 |
| **WAL** | pg_wal_size_bytes | < 20GB | > 80% 磁盘空间 | WAL 占用 |
| | pg_stat_archiver_failed_count | 0 | > 0 | 归档失败 |
| **缓存** | pg_stat_database_blks_hit_ratio | > 99% | < 95% | Buffer Cache 命中率 |
| **锁** | pg_locks_count | - | > 50 | 等待锁数量 |
| **事务** | pg_stat_activity_long_running | < 5 分钟 | > 30 分钟 | 长事务（会导致 WAL 堆积、膨胀） |

### 6.4 核心告警规则

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: postgres-alerts
  namespace: database
spec:
  groups:
    - name: postgresql.rules
      rules:
        - alert: PostgreSQLDown
          expr: pg_up == 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "PostgreSQL {{ $labels.instance }} 不可达"

        - alert: PostgreSQLReplicationLag
          expr: pg_replication_lag_seconds > 300
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "PG 主从延迟 > 300 秒"

        - alert: PostgreSQLReplicationSlotInactive
          expr: pg_replication_slots_active == 0
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "复制槽 {{ $labels.slot_name }} 不活跃，可能导致 WAL 堆积"

        - alert: PostgreSQLHighConnectionUsage
          expr: |
            (pg_settings_max_connections - pg_stat_activity_count)
            / pg_settings_max_connections < 0.2
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "PG 连接数使用率 > 80%"

        - alert: PostgreSQLWALGrowing
          expr: |
            predict_linear(pg_wal_size_bytes[1h], 4*3600)
            > 8 * 1024 * 1024 * 1024
          for: 30m
          labels:
            severity: critical
          annotations:
            summary: "WAL 空间按当前增长速度 4 小时内将超过 8GB"

        - alert: PostgreSQLBloatHigh
          expr: |
            (pg_stat_user_tables_n_dead_tup / pg_stat_user_tables_n_live_tup)
            > 0.3
          for: 30m
          labels:
            severity: warning
          annotations:
            summary: "表 {{ $labels.relname }} 死元组比例 > 30%，需要 VACUUM"

        - alert: PostgreSQLLongTransaction
          expr: pg_stat_activity_max_tx_duration > 1800
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "存在运行超过 30 分钟的长事务，可能导致膨胀和 WAL 堆积"

        - alert: PostgreSQLArchiveFailed
          expr: increase(pg_stat_archiver_failed_count[10m]) > 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "WAL 归档失败，存在数据丢失风险"
```

---

## 七、性能调优

### 7.1 K8s 层调优（和 MySQL 基本一致，PG 有几个重点）

| 调优点 | 建议 | PG 特殊说明 |
|--------|------|------------|
| **资源请求** | requests.memory = limits.memory | PG 内存占用相对稳定，适合设为相等 |
| **CPU limit** | 不设 limit 或等于 requests | PG 不适合 CPU burst，throttle 会导致查询抖动 |
| **CPU 绑定** | cpuset / static policy | 高并发下减少抖动 |
| **大页内存** | 开启 HugePages | shared_buffers 大的时候效果明显（> 8GB） |
| **调度优先级** | system-cluster-critical | 防止被驱逐 |
| **节点独占** | taint + toleration | noisy neighbor 对 PG 性能影响很大 |
| **PG 专用标签** | node-role.db/postgres=true | 调度到专用节点 |

### 7.2 PG 参数调优（K8s 环境重点）

```ini
[postgresql.conf]

# === 内存相关 ===
# shared_buffers: 设为 Pod 内存的 25%（经典经验值，K8s 环境建议稍保守）
shared_buffers = 8GB            # 32G 内存的 Pod，给 8G
# effective_cache_size: 查询优化器估算可用缓存，设为内存的 50-75%
effective_cache_size = 24GB
# work_mem: 每个排序/哈希操作的内存，注意是「每操作」不是全局
work_mem = 16MB                 # 保守值，高并发下注意别设太大
# maintenance_work_mem: VACUUM / 建索引 等维护操作
maintenance_work_mem = 2GB

# === 连接数 ===
max_connections = 500
# 注意: 配合 PgBouncer 使用，不要让应用直接连 PG

# === WAL ===
wal_level = replica
max_wal_size = 8GB
min_wal_size = 2GB
wal_buffers = 64MB
checkpoint_completion_target = 0.9    # 平滑 checkpoint，减少 IO 尖刺

# === 复制 ===
synchronous_commit = on               # 同步复制设为 on，本地可设为 local
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on
hot_standby_feedback = on             # 防止从库查询冲突（但可能导致主库膨胀）

# === 日志 ===
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y%m%d.log'
log_min_duration_statement = 1000     # 慢查询（1秒）
log_checkpoints = on
log_connections = off
log_disconnections = off
log_lock_waits = on
log_temp_files = 0                    # 记录所有临时文件（诊断内存不够）

# === Autovacuum ===
# PG 的「垃圾回收」，云原生环境特别重要
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 30s
autovacuum_vacuum_cost_delay = 2ms    # 设小一点，让 vacuum 更快
autovacuum_vacuum_cost_limit = 2000

# === 统计 ===
track_activities = on
track_counts = on
track_io_timing = on                  # 统计 IO 时间（有轻微 overhead）
shared_preload_libraries = 'pg_stat_statements'
```

**PG 调优三大铁律：**
1. **shared_buffers 不是越大越好**：太大了会和 OS Page Cache 双缓存，反而浪费
2. **work_mem 谨慎设置**：100 个连接同时排序 = 100 × work_mem，可能 OOM
3. **autovacuum 不是越快越好**：太激进会占 IO，太保守会膨胀

### 7.3 PgBouncer 连接池（K8s 必备）

PG 每个连接是一个进程，成本比 MySQL 高很多。K8s 环境下应用 Pod 数量多，连接池必不可少：

```ini
# pgbouncer.ini
[databases]
app_db = host=postgres-master port=5432 dbname=app_db

[pgbouncer]
listen_port = 5432
listen_addr = *
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# 连接池模式:
#   session     → 客户端断开才释放连接（最安全，兼容所有特性）
#   transaction → 事务结束就释放（推荐，性能最好）
#   statement   → 每条语句结束释放（最激进，不能用事务）
pool_mode = transaction

max_client_conn = 10000     # 客户端最大连接数
default_pool_size = 20      # 每个 DB 的后端连接数
reserve_pool_size = 5       # 备用连接数
reserve_pool_timeout = 3    # 备用连接超时时间

log_connections = 0
log_disconnections = 0
log_pooler_errors = 1
```

**K8s 部署形式：**
- **Sidecar 模式**：每个 PG Pod 带一个 PgBouncer（Zalando Operator 用这种）
- **独立 Deployment**：独立的 PgBouncer 服务集群，更灵活，水平扩缩方便

推荐：中小规模用 sidecar，大规模用独立 Deployment。

### 7.4 膨胀管理（PG 云原生运维的必修课）

PG 的 MVCC 机制会产生死元组，autovacuum 负责清理。云原生环境下膨胀问题更突出：

```
常见原因:
  1. 长事务（长事务会阻止 vacuum 清理它之后的死元组）
  2. autovacuum 参数太保守
  3. 大表大量更新 / 删除
  4. 复制槽不活跃（WAL 堆积的同时也可能导致 vacuum 延迟）

监控指标:
  - pg_stat_user_tables_n_dead_tup / n_live_tup
  - pg_stat_user_tables_last_autovacuum
  - pg_stat_activity 中的长事务

处理手段:
  1. 找到并杀掉长事务
     SELECT pg_terminate_backend(pid)
     FROM pg_stat_activity
     WHERE now() - xact_start > interval '30 minutes';

  2. 手动 VACUUM ANALYZE（在线，不锁表）
     VACUUM ANALYZE big_table;

  3. VACUUM FULL（会锁表！慎用！）
     -- 会重写整个表，释放磁盘空间给 OS
     -- 生产环境要用 pg_repack / pg_squeeze 替代

  4. pg_repack（推荐，在线重组表，不阻塞 DML）
     pg_repack -d app_db --table big_table
```

---

## 八、运维常见操作

### 8.1 扩缩容

```bash
# 只读副本扩容
kubectl edit postgresql pg-cluster
# 修改 numberOfInstances: 3 → 5

# 原理:
#   1. Operator 创建新的 Pod + PVC
#   2. Patroni 初始化实例
#   3. pg_basebackup 从主库拉数据
#   4. 加入流复制
#   5. Ready 后加入 Service

# 缩容
kubectl edit postgresql pg-cluster
# numberOfInstances: 5 → 3
# ⚠️ 注意:
#   - 缩容后 PVC 不会自动删除（需要手动清理）
#   - 缩容前删除对应的复制槽（否则 WAL 堆积）
#   - 确保不会缩到 1 个以下（高可用要求至少 3 节点）
```

### 8.2 主备切换（手动演练）

```bash
# 方式 1: Patroni 切换（最安全）
# 查看集群状态
kubectl exec postgres-0 -- patronictl list

# 手动切换主库到 postgres-2
kubectl exec postgres-0 -- patronictl switchover --master postgres-0 --candidate postgres-2

# 方式 2: 直接 promote 从库（不推荐，应走 Patroni）
kubectl exec postgres-1 -- pg_ctl promote

# 验证
kubectl exec postgres-1 -- psql -c "SELECT pg_is_in_recovery();"
# 应该返回 false
```

### 8.3 版本升级

```bash
# 小版本升级（15.3 → 15.4）→ 直接滚动升级
# PG 小版本二进制兼容，升级后自动启动
kubectl set image statefulset postgres postgres=postgres:15.4
kubectl rollout status statefulset postgres

# 大版本升级（14 → 15）→ 需要走 pg_upgrade 或逻辑复制
# 方案 A: pg_upgrade（原地升级，停机时间短）
#   1. 停业务
#   2. 启动新版本镜像
#   3. 执行 pg_upgrade
#   4. analyze 数据库
#   5. 恢复业务
#   停机时间: 取决于数据量（一般几分钟到几十分钟）

# 方案 B: 逻辑复制（不停机）
#   1. 部署一套新版本的从库
#   2. 配置逻辑复制，同步数据
#   3. 等数据追上
#   4. 切读 → 切写
#   5. 下线旧集群
#   停机时间: < 1 分钟（切换窗口）
```

### 8.4 扩存储

```bash
# 前提: StorageClass 支持 allowVolumeExpansion: true

# 1. 修改 PVC 大小
kubectl patch pvc pg-data-postgres-0 -p   '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'

# 2. 重启 Pod（触发文件系统扩容）
kubectl delete pod postgres-0

# 3. 验证
kubectl exec postgres-0 -- df -h /var/lib/postgresql/data
```

### 8.5 参数变更

```bash
# 方式 1: 修改 Operator CR
kubectl edit postgresql pg-cluster
# 修改 spec.postgresql.parameters
# Operator 会滚动重启 Pod 使参数生效

# 方式 2: 修改 ConfigMap + 滚动重启
kubectl edit configmap postgres-config
kubectl rollout restart statefulset postgres

# 注意: PG 参数分三类
#   - internal: 编译时决定，不能改
#   - postmaster: 需要重启才能生效（如 shared_buffers）
#   - superuser / user: 可以 reload 生效（如 work_mem）
#   - SIGHUP 级别: 直接 reload（大多数参数）
# 查看哪些参数需要重启:
# SELECT name, context FROM pg_settings WHERE context = 'postmaster';
```

---

## 九、常见故障排查

### 9.1 PG on K8s 四层诊断模型

```
Layer 4: PostgreSQL 层
  ├─ 连接数满 / 慢查询 / 锁等待
  ├─ 复制延迟 / WAL 堆积
  ├─ 表膨胀 / 索引膨胀
  └─ autovacuum 异常

Layer 3: K8s 层
  ├─ Pod CrashLoopBackOff
  ├─ PVC 挂载失败
  ├─ Service 不通
  └─ Operator  reconcile 失败

Layer 2: 存储层
  ├─ 磁盘慢 / IO 延迟高
  ├─ 磁盘空间满
  └─ 存储快照/克隆问题

Layer 4 → Layer 1: 从现象往下找根因
  现象: 查询慢 → 看 PG 等待事件 → 看 IO 指标 → 看存储
```

### 9.2 常见故障速查表

| 现象 | 可能原因 | 排查命令 |
|------|---------|---------|
| **Pod 一直 Pending** | PVC 未绑定 / 资源不足 / 无匹配节点 | `kubectl describe pod` |
| **Pod CrashLoopBackOff** | PG 配置错误 / 数据目录损坏 / 权限 | `kubectl logs`, `kubectl describe` |
| **连不上数据库** | Service 错 / PgBouncer 挂了 / 认证失败 | `psql -h 测试`, 看 PgBouncer 日志 |
| **主从延迟高** | 大事务 / 从库 IO 慢 / 网络 / vacuum 冲突 | `pg_stat_replication`, `pg_wal_lsn_diff()` |
| **磁盘持续增长** | WAL 堆积（复制槽/归档）/ 表膨胀 / 临时文件 | `pg_wal_lsn_diff()`, 膨胀检查 |
| **查询变慢** | 索引失效 / 统计信息过期 / 锁等待 / IO | `EXPLAIN ANALYZE`, `pg_stat_statements` |
| **连接数飙升** | 应用连接池配置错 / 慢查询堆积 / 死锁 | `pg_stat_activity`, PgBouncer 状态 |
| **OOMKilled** | shared_buffers 太大 / work_mem × 并发数超了 / 大量临时文件 | `kubectl describe`, PG 日志 |
| **Patroni 选主失败** | DCS 不可用 / 网络分区 / 节点数不够 quorum | `patronictl list`, 检查 etcd/K8s API |

### 9.3 应急工具箱

```bash
# 1. 连进去
kubectl exec -it postgres-0 -- psql -U postgres

# 2. 看日志
kubectl logs -f postgres-0 --tail=200

# 3. 看连接状态
kubectl exec postgres-0 -- psql -c   "SELECT pid, state, wait_event_type, wait_event, query FROM pg_stat_activity ORDER BY state;"

# 4. 查复制延迟
kubectl exec postgres-0 -- psql -c   "SELECT client_addr, state, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), write_lsn)) AS write_lag,
   pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), flush_lsn)) AS flush_lag,
   pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)) AS replay_lag
   FROM pg_stat_replication;"

# 5. 查慢查询（需要 pg_stat_statements）
kubectl exec postgres-0 -- psql -c   "SELECT query, calls, total_time, mean_time, rows
   FROM pg_stat_statements
   ORDER BY total_time DESC LIMIT 10;"

# 6. 查膨胀
kubectl exec postgres-0 -- psql -c   "SELECT schemaname, relname, n_live_tup, n_dead_tup,
   round(n_dead_tup::numeric / NULLIF(n_live_tup,0) * 100, 2) AS dead_pct
   FROM pg_stat_user_tables
   ORDER BY n_dead_tup DESC LIMIT 10;"

# 7. 杀慢查询 / 长事务
kubectl exec postgres-0 -- psql -c   "SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state != 'idle' AND now() - xact_start > interval '30 minutes';"

# 8. Patroni 状态
kubectl exec postgres-0 -- patronictl list
kubectl exec postgres-0 -- patronictl topology

# 9. 手动触发备份
kubectl create job --from=cronjob/pg-backup manual-backup-$(date +%s)
```

---

## 十、最佳实践清单

### 10.1 必须做的（P0）

- [ ] 至少 3 副本（主 + 2 从，Patroni 管理 quorum）
- [ ] `reclaimPolicy: Retain`
- [ ] Pod 跨节点反亲和，有条件跨可用区
- [ ] 定时全量备份（pgBackRest）+ WAL 归档 → 对象存储
- [ ] 定期（每月）做恢复演练
- [ ] PgBouncer 连接池（应用不直连 PG）
- [ ] pg_stat_statements 扩展 + 慢查询监控
- [ ] 复制槽监控（防止 WAL 堆积爆磁盘）
- [ ] autovacuum 监控 + 膨胀告警
- [ ] PodDisruptionBudget 保证可用性

### 10.2 强烈建议的（P1）

- [ ] 使用 Operator 管理（Zalando / CrunchyData / CloudNativePG）
- [ ] WAL 和数据目录分盘
- [ ] 读写分离（主写，从库读）
- [ ] pgBackRest 增量备份（每天增量 + 每周全量）
- [ ] 数据库变更走迁移工具（Flyway / Liquibase）+ 灰度
- [ ] 专用数据库节点（taint + toleration）
- [ ] resources.requests = limits（或不设 CPU limit）
- [ ] 大版本升级前做 CSI 快照兜底
- [ ] DR 演练（季度级）

### 10.3 锦上添花的（P2）

- [ ] 自动索引推荐（pg_stat_statements + auto_explain + LLM 分析）
- [ ] pg_repack 在线表重组（处理大表膨胀）
- [ ] 容量预测 + 自动扩盘
- [ ] 多区域 / 多集群部署
- [ ] Chaos Engineering（故意杀主库测切换）
- [ ] LLM 辅助的慢查询分析（AIOps 方向）

---

## 十一、PG vs MySQL 云原生差异速查表

| 维度 | MySQL | PostgreSQL |
|------|-------|-----------|
| **Operator 首选** | Percona PXC / Presslabs | Zalando Spilo / CrunchyData |
| **HA 机制** | Galera / MGR / MHA | Patroni（DCS 选主） |
| **故障转移** | 快，老主易重新加入 | 稍慢，老主需重新 basebackup |
| **连接池** | 可选 | 几乎必须（PgBouncer） |
| **存储优化** | Buffer Pool + redo log | shared_buffers + WAL 分盘 |
| **特色运维问题** | 主从一致性校验 | 表膨胀 / 复制槽 / vacuum |
| **扩展生态** | 相对弱 | 极强（扩展是 PG 的灵魂） |
| **备份工具** | xtrabackup | pgBackRest |
| **快照恢复** | 快 | 快 |
| **K8s 成熟度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

> **总结**：PostgreSQL 在 K8s 上的运维复杂度高于 MySQL，核心差异在于 **Patroni 管理的流复制 + 复制槽 + 表膨胀** 这三件事。选对 Operator（推荐 Zalando 或 CrunchyData）、配好 PgBouncer、做好备份恢复（pgBackRest + WAL 归档）、建立完整的膨胀和复制槽监控，PG 完全可以在 K8s 上稳定运行，同时获得云原生的声明式管理、弹性扩缩容和 GitOps 能力。
