# MySQL 云原生运维实战

> MySQL 跑在 K8s 上到底靠不靠谱？Operator 怎么选？存储怎么规划？备份恢复怎么做？扩缩容、故障切换、性能调优和物理机有什么不一样？本文覆盖 MySQL 云原生运维全链路：Operator 选型、存储规划、部署架构、备份恢复、监控告警、性能调优、故障排查、多集群管理。

---

## 一、选型决策框架

### 1.1 什么时候适合上 K8s，什么时候不适合

| 场景 | 适合上 K8s | 不适合（建议物理机/VM） |
|------|-----------|----------------------|
| **业务类型** | 多租户 SaaS、微服务配套、开发测试环境 | 核心交易库、超大库（> 5TB）、极低延迟要求（< 1ms） |
| **团队能力** | 已有 K8s 平台运维能力、GitOps 工作流成熟 | 只有传统 DBA，无 K8s 经验 |
| **数据库规模** | 中小规模（单实例 < 2TB，实例数 5-50） | 超大规模、复杂分片拓扑 |
| **高可用要求** | RPO < 5s, RTO < 30s 可接受 | RPO = 0, RTO < 5s 的金融级 |
| **合规要求** | 一般行业合规 | 强审计、数据不出特定物理机 |

**一句话判断：** 如果你的 MySQL 已经跑在 VM 上用 Ansible 管了，且团队 K8s 能力成熟 → 可以上。如果是核心交易库且 DBA 团队不懂 K8s → 别急着上，先从非核心库试水。

### 1.2 Operator 选型对比

目前主流的 MySQL Operator 有四个：

| 维度 | Percona XtraDB Cluster (PXC) | MySQL Operator (Oracle 官方) | Presslabs MySQL Operator | MGR Operator |
|------|---------------------------|---------------------------|-------------------------|-------------|
| **高可用模式** | Galera 多主同步复制 | InnoDB Cluster / Group Replication | 异步主从 + Orchestrator | MGR 单主/多主 |
| **数据一致性** | 强一致（同步复制） | 最终一致（MGR 单主强一致） | 最终一致 | 强一致（组内） |
| **自动故障转移** | ✅ Galera 自管理 | ✅ 依赖 MySQL Router + MHA/Orchestrator | ✅ Orchestrator | ✅ MGR 自管理 |
| **备份恢复** | ✅ XtraBackup 集成 | ✅ MySQL Enterprise Backup | ✅ xtrabackup + 对象存储 | ⚠️ 需自建 |
| **读写扩展** | ✅ 多主都可写（有冲突代价） | ✅ Router 读写分离 | ✅ ProxySQL 读写分离 | ✅ 多主模式 |
| **存储接口** | PVC / StorageClass | PVC / LocalPV | PVC | PVC / LocalPV |
| **社区活跃度** | 高 | 中（官方但更新慢） | 中 | 低（多为自研） |
| **适用场景** | 强一致要求高、读多写少 | Oracle 技术栈统一 | 中小规模、运维简单 | 熟悉 MGR 的团队 |

**推荐选型路径：**

```
团队第一次上 MySQL on K8s？
├─ 强一致要求高 → Percona XtraDB Cluster Operator
├─ 读写分离、运维简单 → Presslabs MySQL Operator
└─ 已经在物理机用 MGR → Oracle MySQL Operator + MGR

超大规模（> 50 实例）？
→ 考虑 Vitess Operator（分库分表中间件级别的方案）

极简场景（单实例 + 定时备份）？
→ 甚至可以不用 Operator，直接 StatefulSet + CronJob 备份
```

### 1.3 部署架构选型

```
架构 1: 单实例 StatefulSet（最低复杂度）
  ── MySQL Pod
  └─ PVC
  适用: 开发测试、非核心小库

架构 2: 主从 + ProxySQL（最通用）
  ┌─ Master (StatefulSet-0) ─ PVC
  ├─ Slave-1 (StatefulSet-1) ─ PVC
  ├─ Slave-2 (StatefulSet-2) ─ PVC
  └─ ProxySQL (Deployment)  ─ Service
  适用: 大部分生产场景，读写分离

架构 3: PXC / MGR 多副本（高可用最强）
  ┌─ Node-0 ─ PVC
  ├─ Node-1 ─ PVC
  └─ Node-2 ─ PVC
  适用: 核心库、强一致要求

架构 4: Vitess 分片（超大规模）
  适用: 数据量大、水平分片需求
```

---

## 二、存储规划（最容易踩坑的环节）

### 2.1 存储类型选择

| 存储类型 | 性能 | 可靠性 | 成本 | 适用场景 |
|---------|------|--------|------|---------|
| **LocalPV（本地盘）** | ⭐⭐⭐⭐⭐ | ⭐⭐ | 低 | 核心库、延迟敏感 |
| **Rook-Ceph RBD** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中 | 通用场景、可动态扩容 |
| **Longhorn** | ⭐⭐ | ⭐⭐⭐⭐ | 中 | 中小规模、易用 |
| **云厂商 EBS/云盘** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 高 | 云上部署 |
| **NFS** | ⭐ | ⭐⭐⭐ | 低 | ❌ 绝对不要用在 MySQL 数据目录 |

**铁律：MySQL 的数据目录绝对不能用 NFS、GlusterFS、CephFS 这类分布式文件系统。** 原因：
- 文件锁语义不兼容
- 延迟抖动大
- InnoDB O_DIRECT 不支持或性能极差
- 容易数据损坏

### 2.2 StorageClass 配置要点

```yaml
# 推荐: LocalPV + WaitForFirstConsumer
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: mysql-local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer   # 关键：等 Pod 调度完再绑定
# WaitForFirstConsumer 保证 PV 和 Pod 在同一个节点上
```

```yaml
# 推荐: Ceph RBD (生产级)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ceph-rbd-mysql
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  pool: mysql-pool
  imageFormat: "2"
  imageFeatures: layering
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner
  csi.storage.k8s.io/fstype: xfs
reclaimPolicy: Retain        # 必须 Retain，防止误删数据
allowVolumeExpansion: true   # 允许在线扩容
volumeBindingMode: WaitForFirstConsumer
```

### 2.3 PVC 规划

```yaml
# MySQL PVC 模板（StatefulSet 中）
volumeClaimTemplates:
  - metadata:
      name: mysql-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: ceph-rbd-mysql
      resources:
        requests:
          storage: 100Gi      # 按预估 1-2 年数据量的 2 倍申请
```

**规划原则：**
- `reclaimPolicy: Retain`，防止 StatefulSet 被误删导致数据丢失
- `accessModes: ReadWriteOnce`，MySQL 是单写架构，不需要 RWO-Many
- 存储容量按**未来 1-2 年**预估，预留 50% 余量（binlog + 临时表 + 备份空间）
- IOPS 需求：读密集型 ≥ 3000 IOPS，写密集型 ≥ 5000 IOPS
- 文件系统用 **XFS**（ext4 大文件下性能略差，btrfs 不成熟）

### 2.4 挂载参数优化

```yaml
# StatefulSet spec.template.spec 中
containers:
  - name: mysql
    volumeMounts:
      - name: mysql-data
        mountPath: /var/lib/mysql
        # 禁用 atime，减少元数据写入
        mountPropagation: None
# 通过 StorageClass 的 mountOptions 或 CSI 参数
mountOptions:
  - noatime
  - nodiratime
  - discard          # SSD 支持 TRIM，回收空间
  - defaults
```

---

## 三、部署实战

### 3.1 Percona XtraDB Cluster Operator 部署

```bash
# 1. 安装 Operator
helm repo add percona https://percona.github.io/percona-helm-charts/
helm install pxc-operator percona/pxc-operator   --namespace pxc-operator   --create-namespace   --version 1.13.0

# 2. 部署 PXC 集群
kubectl apply -f - <<EOF
apiVersion: pxc.percona.com/v1
kind: PerconaXtraDBCluster
metadata:
  name: mysql-cluster
  namespace: database
spec:
  secretsName: mysql-cluster-secrets
  pause: false
  pxcs:
    size: 3
    image: percona/percona-xtradb-cluster:8.0.32-24.2
    volumeSpec:
      persistentVolumeClaim:
        storageClassName: ceph-rbd-mysql
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Gi
    resources:
      requests:
        cpu: "4"
        memory: "8Gi"
      limits:
        cpu: "8"
        memory: "16Gi"
    affinity:
      antiAffinityTopologyKey: "kubernetes.io/hostname"  # 跨节点分布
  haproxy:
    size: 3
    image: percona/percona-xtradb-cluster-operator:1.13.0-haproxy
    resources:
      requests:
        cpu: "1"
        memory: "1Gi"
  pmm:
    enabled: false
  backup:
    image: percona/percona-xtradb-cluster-operator:1.13.0-pxc8.0-backup-pxb8.0
    storages:
      s3:
        type: s3
        s3:
          bucket: mysql-backup
          credentialsSecret: aws-s3-secret
          region: ap-east-1
EOF
```

### 3.2 StatefulSet + 主从（无 Operator，最轻量）

如果不想引入 Operator，直接用 StatefulSet + InitContainer 做主从初始化：

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
  namespace: database
spec:
  serviceName: mysql-headless
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      initContainers:
        # Init 容器：判断是 Master 还是 Slave，做不同初始化
        - name: init-mysql
          image: mysql:8.0
          command:
            - bash
            - "-c"
            - |
              set -ex
              # 生成 server-id（基于 Pod 序号）
              [[ $(hostname) =~ -([0-9]+)$ ]] || exit 1
              ordinal=${BASH_REMATCH[1]}
              echo [mysqld] > /mnt/conf.d/server-id.cnf
              echo server-id=$((100 + ordinal)) >> /mnt/conf.d/server-id.cnf
              # master-0 为主库，其他为从库
              if [[ $ordinal -eq 0 ]]; then
                cp /mnt/config-map/master.cnf /mnt/conf.d/
              else
                cp /mnt/config-map/slave.cnf /mnt/conf.d/
              fi
          volumeMounts:
            - name: conf
              mountPath: /mnt/conf.d
            - name: config-map
              mountPath: /mnt/config-map
        # Clone 容器：从已有备份/S3 恢复数据（只有从库需要）
        - name: clone-mysql
          image: gcr.io/google-samples/xtrabackup:1.0
          command:
            - bash
            - "-c"
            - |
              set -ex
              # 如果数据目录已有数据，跳过
              [[ -d /var/lib/mysql/mysql ]] && exit 0
              # Master 的话跳过，Master 初始化空库
              [[ $(hostname) =~ -([0-9]+)$ ]] || exit 1
              ordinal=${BASH_REMATCH[1]}
              [[ $ordinal -eq 0 ]] && exit 0
              # 从 Master 克隆
              ncat --recv-only mysql-0.mysql-headless 3307 | xbstream -x -C /var/lib/mysql
              # 准备（crash recovery）
              xtrabackup --prepare --target-dir=/var/lib/mysql
          volumeMounts:
            - name: data
              mountPath: /var/lib/mysql
      containers:
        - name: mysql
          image: mysql:8.0
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: root-password
          ports:
            - name: mysql
              containerPort: 3306
          volumeMounts:
            - name: data
              mountPath: /var/lib/mysql
            - name: conf
              mountPath: /etc/mysql/conf.d
          livenessProbe:
            exec:
              command: ["mysqladmin", "ping", "-uroot", "-p$MYSQL_ROOT_PASSWORD"]
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
          readinessProbe:
            exec:
              command:
                - bash
                - "-c"
                - |
                  mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "SELECT 1"
            initialDelaySeconds: 5
            periodSeconds: 2
            timeoutSeconds: 1
      volumes:
        - name: conf
          emptyDir: {}
        - name: config-map
          configMap:
            name: mysql
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: ceph-rbd-mysql
        resources:
          requests:
            storage: 100Gi
```

### 3.3 Service 设计

```yaml
# Headless Service（StatefulSet 必须，用于 DNS 发现）
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
  namespace: database
spec:
  clusterIP: None
  selector:
    app: mysql
  ports:
    - port: 3306
---
# 主库读-写 Service（指向 master-0）
apiVersion: v1
kind: Service
metadata:
  name: mysql-master
  namespace: database
spec:
  selector:
    app: mysql
    statefulset.kubernetes.io/pod-name: mysql-0
  ports:
    - port: 3306
---
# 从库只读 Service（所有从库负载均衡）
apiVersion: v1
kind: Service
metadata:
  name: mysql-slave
  namespace: database
spec:
  selector:
    app: mysql
  ports:
    - port: 3306
```

---

## 四、高可用与故障转移

### 4.1 各方案 RPO/RTO 对比

| 方案 | RPO（数据丢失） | RTO（恢复时间） | 切换方式 | 适用场景 |
|------|----------------|----------------|---------|---------|
| PXC / MGR | ~0（同步复制） | < 30s | 自动 | 核心库 |
| 半同步主从 | < 5s | 1-5 min | 半自动（需提升从库） | 通用 |
| 异步主从 | 可能丢失 | 5-15 min | 手动 | 非核心 |
| 单实例 | 全部丢失（靠备份） | 取决于备份恢复速度 | 手动 | 开发测试 |

### 4.2 故障场景与处理流程

#### 场景 1: 单个 Pod 挂了

```
现象: mysql-1 Pod CrashLoopBackOff / NotReady

自动处理（StatefulSet 保证）:
  1. K8s 检测到 Pod 不健康
  2. 重建 Pod（同节点或不同节点）
  3. PVC 重新挂载
  4. MySQL 启动，通过 redo log 做 crash recovery
  5. 如果是从库 → 自动追主库 binlog
  6. 如果是 PXC 节点 → 自动加入集群做 SST/IST

人工介入条件:
  - 连续重启 > 3 次
  - PVC 挂载失败（存储故障）
  - crash recovery 失败（数据损坏）
```

#### 场景 2: 主库挂了（主从架构）

```
手动切换流程:

1. 确认主库不可用
   kubectl exec mysql-0 -- mysqladmin ping

2. 找一个数据最新的从库提升为主
   kubectl exec mysql-1 -- mysql -uroot -p$MYSQL_PWD -e "STOP SLAVE; RESET MASTER;"

3. 更新其它从库指向新主
   # 其它从库执行 CHANGE MASTER TO mysql-1

4. 更新 Service 指向新主
   kubectl patch service mysql-master -p      '{"spec":{"selector":{"statefulset.kubernetes.io/pod-name":"mysql-1"}}}'

5. 恢复旧主（修好后降为从库）
```

#### 场景 3: 整个节点挂了

```
现象: Node NotReady，上面的 MySQL Pod 状态未知

处理:
  1. 确认节点无法恢复（硬件故障 / 网络隔离）
  2. 强制删除 Pod + 解绑 PVC
     kubectl delete pod mysql-2 --force --grace-period=0
  3. StatefulSet 在其他节点重建 Pod
  4. PVC 重新绑定到新节点（取决于 StorageClass 是否支持跨节点）

⚠️ 注意: LocalPV 场景下 Pod 被绑定到特定节点，节点挂了数据就不可达
   → 必须用多副本架构（主从/PXC），不能依赖 LocalPV 单点
```

### 4.3 防脑裂机制

K8s 环境下脑裂比物理机更容易发生（网络分区 + 自动故障切换）：

| 机制 | 作用 |
|------|------|
| **Quorum（法定人数）** | PXC/MGR 必须 3 节点以上，2 节点无法形成 quorum 就拒绝写入 |
| **Pod 反亲和** | Pod 分布在不同节点/机架/可用区，降低同时故障概率 |
| **Pod Disruption Budget** | 限制同时不可用的副本数 |
| **fencing** | 确保旧主在切换前被真正隔离（K8s 环境下通常靠节点驱逐实现） |

```yaml
# PodDisruptionBudget 示例
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: mysql-pdb
  namespace: database
spec:
  minAvailable: 2      # 至少保证 2 个副本可用
  selector:
    matchLabels:
      app: mysql
```

---

## 五、备份与恢复

### 5.1 备份策略设计

```
备份层级:
├─ 全量备份 (xtrabackup)  ← 每天凌晨 1 次
├─ 增量备份 (xtrabackup)  ← 每 6 小时 1 次（可选）
├─ Binlog 归档            ← 实时上传到对象存储
└─ 快照备份 (CSI snapshot) ← 每天 1 次，用于快速回滚
```

**保留策略:**
- 每日全量：保留 7 天
- 每周全量：保留 4 周
- 每月全量：保留 6 个月
- Binlog：保留 7 天（支持 PITR 任意时间点恢复）

### 5.2 CronJob 定时备份（无 Operator 场景）

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: mysql-backup
  namespace: database
spec:
  schedule: "0 2 * * *"    # 每天凌晨 2 点
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: percona/percona-xtrabackup:8.0
              command:
                - bash
                - "-c"
                - |
                  set -e
                  BACKUP_DIR="/backup/$(date +%Y%m%d_%H%M%S)"
                  mkdir -p $BACKUP_DIR

                  # 1. 执行 xtrabackup 全量备份
                  xtrabackup --backup                     --host=mysql-master.database.svc.cluster.local                     --user=root                     --password=$MYSQL_ROOT_PASSWORD                     --target-dir=$BACKUP_DIR                     --parallel=4

                  # 2. 准备备份（crash recovery 后的一致性状态）
                  xtrabackup --prepare --target-dir=$BACKUP_DIR

                  # 3. 上传到对象存储
                  mc cp --recursive $BACKUP_DIR s3/mysql-backup/full/$(hostname -s)/

                  # 4. 清理本地（保留 3 天）
                  find /backup -type d -mtime +3 -exec rm -rf {} +
              env:
                - name: MYSQL_ROOT_PASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: mysql-secret
                      key: root-password
              volumeMounts:
                - name: backup-storage
                  mountPath: /backup
          restartPolicy: OnFailure
          volumes:
            - name: backup-storage
              persistentVolumeClaim:
                claimName: mysql-backup-pvc
```

### 5.3 Binlog 实时归档

```yaml
# sidecar 模式：和 MySQL 同 Pod，实时上传 binlog
containers:
  - name: mysql
    ...
  - name: binlog-uploader
    image: minio/mc:latest
    command:
      - bash
      - "-c"
      - |
        while true; do
          # 找到最新完成的 binlog 文件（当前正在写的不上传）
          latest_file=$(ls -t /var/lib/mysql/binlog.* 2>/dev/null | grep -v '.index' | head -1)
          for f in /var/lib/mysql/binlog.*; do
            [[ $f == *.index ]] && continue
            # 跳过最新的（正在写入）
            [[ $f == $latest_file ]] && continue
            # 上传（幂等，已上传则跳过）
            mc cp --no-color $f s3/mysql-backup/binlog/$(hostname -s)/
            # 上传成功后删除本地（确保有 3 份以上再删）
          done
          sleep 60
        done
    volumeMounts:
      - name: data
        mountPath: /var/lib/mysql
        readOnly: true
```

### 5.4 恢复流程

```bash
# 步骤 1: 停止应用写入（切只读 / 停服务）
kubectl scale deployment app --replicas=0

# 步骤 2: 下载全量备份
mc cp --recursive s3/mysql-backup/full/20260620_020000/ /tmp/restore/

# 步骤 3: 停止目标 MySQL
kubectl scale statefulset mysql --replicas=0

# 步骤 4: 备份数据移到 PVC 对应位置
# （先启动一个 helper Pod 挂载 PVC）
kubectl apply -f helper-pod.yaml
kubectl cp /tmp/restore/ helper-pod:/var/lib/mysql/

# 步骤 5: 应用 binlog 做 PITR（可选，恢复到指定时间点）
mysqlbinlog --stop-datetime="2026-06-20 10:30:00"   /var/lib/mysql/binlog.000* | mysql -uroot -p

# 步骤 6: 启动 MySQL，验证数据
kubectl scale statefulset mysql --replicas=3
kubectl exec mysql-0 -- mysql -e "SHOW DATABASES;"

# 步骤 7: 恢复应用
kubectl scale deployment app --replicas=3
```

---

## 六、监控与告警

### 6.1 指标采集架构

```
MySQL Pod
  └─ mysqld_exporter (sidecar)
       │  :9104/metrics
       ▼
  Prometheus (ServiceMonitor)
       │
       ▼
  Grafana Dashboard + Alertmanager
```

### 6.2 mysqld_exporter 部署

```yaml
# Sidecar 方式（推荐，和 MySQL 同生命周期）
containers:
  - name: mysql
    image: mysql:8.0
    ...
  - name: exporter
    image: prom/mysqld-exporter:v0.15.1
    env:
      - name: DATA_SOURCE_NAME
        value: "exporter:password@(localhost:3306)/"
    ports:
      - name: metrics
        containerPort: 9104
    args:
      - --collect.global_status
      - --collect.global_variables
      - --collect.slave_status
      - --collect.info_schema.innodb_metrics
      - --collect.info_schema.processlist
      - --collect.info_schema.query_response_time
      - --collect.perf_schema.eventsstatementssum
```

### 6.3 关键指标清单

| 类别 | 指标名 | 正常范围 | 告警阈值 | 说明 |
|------|--------|---------|---------|------|
| **可用性** | mysql_up | 1 | == 0 | MySQL 是否存活 |
| | mysql_slave_running | 1（从库） | == 0 | 从库同步线程 |
| **连接** | mysql_global_status_threads_connected | - | > 80% max_connections | 连接数 |
| | mysql_global_status_aborted_connects | - | 持续增长 | 连接失败 |
| **性能** | mysql_global_status_queries_rate | - | 突增/突降 50% | QPS |
| | mysql_slow_queries | 低 | > 100/s | 慢查询 |
| **InnoDB** | mysql_innodb_buffer_pool_hit_rate | > 99% | < 95% | Buffer Pool 命中率 |
| | mysql_innodb_row_lock_time_avg | < 10ms | > 100ms | 行锁等待 |
| | mysql_innodb_deadlocks_total | 0 | > 1/10min | 死锁 |
| **复制** | mysql_slave_seconds_behind_master | < 30s | > 300s | 主从延迟 |
| **存储** | mysql_disk_usage_pct | < 80% | > 85% warning, > 90% critical | 磁盘使用率 |
| **日志** | mysql_binlog_disk_usage_pct | < 50% | > 70% | Binlog 占用 |

### 6.4 核心告警规则（PrometheusRule）

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: mysql-alerts
  namespace: database
spec:
  groups:
    - name: mysql.rules
      rules:
        - alert: MySQLDown
          expr: mysql_up == 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "MySQL 实例 {{ $labels.instance }} 不可达"
            description: "mysql_up = 0 持续 1 分钟"

        - alert: MySQLReplicationLag
          expr: mysql_slave_status_seconds_behind_master > 300
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "MySQL 主从延迟 > 300s"
            description: "{{ $labels.instance }} 延迟 {{ $value }}秒"

        - alert: MySQLHighConnectionUsage
          expr: |
            (mysql_global_status_threads_connected /
             mysql_global_variables_max_connections) > 0.8
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "MySQL 连接使用率 > 80%"

        - alert: MySQLSlowQueriesSpike
          expr: rate(mysql_global_status_slow_queries[5m]) > 10
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "MySQL 慢查询激增"

        - alert: MySQLInnoDBBufferPoolLowHitRate
          expr: |
            (1 - rate(mysql_global_status_innodb_buffer_pool_reads[5m])
             / rate(mysql_global_status_innodb_buffer_pool_read_requests[5m])) < 0.95
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "InnoDB Buffer Pool 命中率 < 95%"

        - alert: MySQLDiskAlmostFull
          expr: |
            (kubelet_volume_stats_used_bytes{persistentvolumeclaim=~"mysql.*"}
             / kubelet_volume_stats_capacity_bytes{persistentvolumeclaim=~"mysql.*"}) > 0.85
          for: 30m
          labels:
            severity: warning
          annotations:
            summary: "MySQL PVC 使用率 > 85%"
```

---

## 七、性能调优

### 7.1 K8s 层调优

| 调优点 | 建议 | 原理 |
|--------|------|------|
| **资源请求/限制** | requests = limits（CPU 不设 limits 也行，看场景） | 避免被 throttled（cfs quota 导致性能抖动） |
| **CPU 绑定** | `cpuset: "0-3"` / CPU Manager static policy | 减少上下文切换，降低延迟抖动 |
| **大页内存** | 开启 HugePages 2M/1G | 减少 TLB miss，提高内存访问性能 |
| **调度优先级** | `priorityClassName: system-cluster-critical` | 资源紧张时优先保证 MySQL 不被驱逐 |
| **Pod 独占节点** | taint + toleration + 反亲和 | 避免 noisy neighbor |
| **禁用 AppArmor/SELinux** | 视安全要求而定 | 减少系统调用 overhead |

```yaml
# 高性能部署配置要点
spec:
  containers:
    - name: mysql
      resources:
        requests:
          cpu: "16"
          memory: "64Gi"
        limits:
          memory: "64Gi"
          # CPU 不设 limits → 使用整个节点的 CPU 份额，无 throttle
      securityContext:
        # 使用 hugepages（需节点预先配置）
        capabilities:
          add: ["IPC_LOCK"]
  nodeSelector:
    node-role.kubernetes.io/database: "true"
  tolerations:
    - key: "database"
      operator: "Equal"
      value: "mysql"
      effect: "NoSchedule"
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: mysql
          topologyKey: kubernetes.io/hostname
```

### 7.2 MySQL 参数调优（K8s 环境重点调整项）

```ini
[mysqld]
# === 内存相关 ===
# Buffer Pool 设为 Pod 内存限制的 50-70%
innodb_buffer_pool_size = 48G    # 64G 内存的 Pod，给 48G
innodb_buffer_pool_instances = 16  # 每个 instance 约 1-2G
innodb_log_file_size = 2G        # redo log 大小，写多就设大
innodb_log_buffer_size = 64M

# === 连接相关 ===
max_connections = 1000
back_log = 500
thread_cache_size = 64
table_open_cache = 4000
open_files_limit = 65535

# === 性能相关 ===
innodb_flush_log_at_trx_commit = 2  # 1=最安全, 2=性能好(丢1s数据)
sync_binlog = 1                      # 1=最安全, 0=性能好
innodb_flush_method = O_DIRECT       # 绕过 OS Page Cache
innodb_io_capacity = 2000            # 根据存储 IOPS 调整
innodb_io_capacity_max = 4000

# === 慢查询 ===
slow_query_log = ON
long_query_time = 1
log_queries_not_using_indexes = OFF  # 别全开，会爆日志

# === 复制相关（从库）===
relay_log_recovery = ON
slave_parallel_type = LOGICAL_CLOCK
slave_parallel_workers = 8

# === K8s 特殊调整 ===
# 不要用 hostname 作为 server-id（因为 Pod 重启 hostname 不变但 IP 可能变）
# server-id 由 InitContainer 生成，基于 ordinal 序号
```

**Buffer Pool 大小经验值:**
- 内存 ≤ 8G → 给 50%
- 内存 8-32G → 给 60%
- 内存 32G+ → 给 70%
- 永远留 20-30% 给 OS Page Cache、连接开销、临时表

### 7.3 存储性能调优

```
性能优先级:
  Local SSD > NVMe > Ceph RBD (3副本) > 云盘 SSD > 网络存储

K8s 上排查存储性能:
  1. kubectl exec mysql-0 -- iostat -x 1
     → 看 %util, await, r_await, w_await
  2. fio 测试 PVC 性能
  3. 对比 Pod 内延迟 vs 宿主机延迟
     → 如果差很多，可能是 CSI overhead 或网络问题
```

---

## 八、运维常见操作

### 8.1 扩容缩容

```bash
# 从库水平扩容（StatefulSet 直接加副本）
kubectl scale statefulset mysql --replicas=5
# 新 Pod 会自动：
#   1. 启动 MySQL
#   2. 从备份/现有主库克隆数据
#   3. 设置为从库，追 binlog
#   4. ready 后自动加入 mysql-slave Service

# 缩容
kubectl scale statefulset mysql --replicas=3
# ⚠️ 缩容前:
#   1. 确认要下线的从库没有应用连接
#   2. 备份数据（虽然 PVC 还在）
#   3. 缩容后 PVC 不会自动删除，需手动清理
```

### 8.2 滚动升级

```bash
# 更新镜像（StatefulSet 自带滚动更新）
kubectl set image statefulset mysql mysql=mysql:8.0.36

# 观察升级过程
kubectl rollout status statefulset mysql
kubectl get pods -l app=mysql -w

# 回滚
kubectl rollout undo statefulset mysql
```

**注意事项：**
- 升级顺序：从库先升，主库最后升
- 升之前做一次全量备份
- 大版本升级（5.7→8.0）不能直接滚动，需要走 mysqldump 或原地升级
- 观察复制延迟，确保升级过程不中断

### 8.3 密码变更

```bash
# 1. 更新 Secret
kubectl create secret generic mysql-secret   --from-literal=root-password='new_password'   --dry-run=client -o yaml | kubectl apply -f -

# 2. 在 MySQL 中更新密码
kubectl exec mysql-0 -- mysql -uroot -p'old_password' -e   "ALTER USER 'root'@'%' IDENTIFIED BY 'new_password';"

# 3. 重启 Pod 使环境变量生效（如果用环境变量）
kubectl rollout restart statefulset mysql
```

### 8.4 数据迁移（从物理机迁到 K8s）

```
方案 A: xtrabackup + 恢复（停机时间短，适合中大库）
  1. 物理机做全量 xtrabackup
  2. 传输备份到 K8s PVC
  3. 启动 MySQL（StatefulSet）
  4. 设置为物理机的从库，追 binlog
  5. 业务低峰期切换
  停机时间: < 5 分钟

方案 B: mysqldump（简单可靠，适合小库）
  1. mysqldump 导出
  2. 导入 K8s MySQL
  停机时间: 取决于数据量（10GB 约 30-60 分钟）

方案 C: 基于主从复制（不停机）
  1. K8s MySQL 作为物理机 MySQL 的从库
  2. 等数据追上
  3. 应用切读 → 切写 → 解除主从
  停机时间: 0（切换窗口 < 1 分钟）
```

---

## 九、常见故障排查

### 9.1 诊断思路框架

```
MySQL on K8s 故障排查四层模型:

Layer 4: MySQL 层   ──  SQL 慢 / 死锁 / 连接数满 / 主从延迟
Layer 3: K8s 层     ──  Pod 挂 / PVC 挂 / Service 不通
Layer 2: 存储层     ──  磁盘慢 / 存储满 / IO 错误
Layer 1: 节点层     ──  Node NotReady / 资源不足 / 网络分区

排查顺序: 从上往下看现象，从下往上排查根因
  现象是 MySQL 连不上 → 看 Pod → 看节点 → 看存储 → 看网络
```

### 9.2 常见故障速查表

| 现象 | 可能原因 | 排查命令 |
|------|---------|---------|
| **Pod 一直 Pending** | PVC 未绑定 / 资源不足 / 节点无容忍 | `kubectl describe pod` 看 Events |
| **Pod CrashLoopBackOff** | my.cnf 配置错误 / 数据损坏 / 权限问题 | `kubectl logs mysql-0` |
| **MySQL 启动很慢** | crash recovery 做大量 redo log 回放 / 大事务回滚 | `kubectl logs -f mysql-0` |
| **连接不上** | Service 错 / 网络策略 / 认证方式不兼容 | `telnet / mysql -h` 测试 |
| **主从延迟高** | 大事务 / 从库性能差 / 网络慢 | `SHOW SLAVE STATUS\G` |
| **IO 延迟高** | 存储性能不足 / 大量随机写 | `iostat -x`, `SHOW ENGINE INNODB STATUS` |
| **OOMKilled** | innodb_buffer_pool 设置太大，超内存 limit | `kubectl describe pod` 看 Restart Reason |
| **数据文件损坏** | 存储异常断电 / 内核 bug | `innodb_force_recovery` 尝试启动 |

### 9.3 应急工具箱

```bash
# MySQL on K8s 运维常备命令

# 1. 连进去
kubectl exec -it mysql-0 -- mysql -uroot -p

# 2. 看日志
kubectl logs -f mysql-0 --tail=200

# 3. 看慢查询
kubectl exec mysql-0 -- mysqldumpslow -s c -t 10 /var/lib/mysql/slow.log

# 4. 现场抓堆栈
kubectl exec mysql-0 -- mysqladmin debug

# 5. 杀慢查询
kubectl exec mysql-0 -- pt-kill   --user=root --password=$PWD --host=localhost   --busy-time=60 --kill

# 6. 查存储性能
kubectl exec mysql-0 -- iostat -x 1 10

# 7. 查连接
kubectl exec mysql-0 -- mysql -e "SHOW PROCESSLIST;"

# 8. 手动触发备份
kubectl create job --from=cronjob/mysql-backup manual-backup-$(date +%s)
```

---

## 十、最佳实践清单

### 10.1 必须做的（P0）

- [ ] 至少 3 副本（主从 1 主 2 从，或 PXC 3 节点）
- [ ] `reclaimPolicy: Retain`，防止误删数据
- [ ] 跨节点 Pod 反亲和，避免单点故障
- [ ] 定时备份 + 定期（每月）做恢复演练
- [ ] Binlog 归档到对象存储，支持 PITR
- [ ] 核心监控指标 + 告警
- [ ] PodDisruptionBudget 保证可用性
- [ ] 数据库账号最小权限原则

### 10.2 强烈建议的（P1）

- [ ] 使用 Operator 管理，避免手写 StatefulSet
- [ ] 读写分离（ProxySQL / HAProxy / MySQL Router）
- [ ] 慢查询分析系统（pt-query-digest / PMM）
- [ ] 数据库变更走 SQL Review + 灰度发布
- [ ] 专用数据库节点（taint + toleration）
- [ ] 资源 requests = limits（或不设 CPU limit）
- [ ] 定期做 DR 演练（灾备切换）

### 10.3 锦上添花的（P2）

- [ ] LLM 辅助的智能告警分析（AIOps 方向）
- [ ] 自动 SQL 审核 + 索引建议
- [ ] 容量预测与自动扩容
- [ ] 多区域 / 多集群部署
- [ ] Chaos Engineering 注入故障验证高可用

---

## 十一、决策速查表

| 问题 | 判断 | 答案 |
|------|------|------|
| MySQL 能不能上 K8s？ | 非核心 + 团队有 K8s 能力 | ✅ 能 |
| | 核心交易库 + 团队没经验 | ❌ 先从非核心试水 |
| 存储用什么？ | 延迟敏感 | LocalPV（但要多副本） |
| | 通用场景 + 动态扩缩 | Ceph RBD |
| | 云上 | 云厂商 SSD 云盘 |
| Operator 选哪个？ | 强一致要求高 | Percona PXC |
| | 运维简单、中小规模 | Presslabs |
| | 已经熟悉 MGR | Oracle MySQL Operator |
| | 超大规模分片 | Vitess |
| 备份方式？ | 数据量 < 100G | mysqldump 够用 |
| | 数据量 > 100G | xtrabackup 物理备份 |
| | 需要 PITR | + binlog 归档 |
| 性能不够怎么办？ | CPU 瓶颈 | 加核 / 分库分表 |
| | IO 瓶颈 | 换 SSD / 增大 Buffer Pool |
| | 读瓶颈 | 加从库 / 读写分离 |
| | 写瓶颈 | 分库分表 / PXC 多主 |

---

> **总结**：MySQL on K8s 的核心挑战不在「能不能跑」—— 早就可以跑了。真正的难点在于 **存储可靠性、故障转移的自动化程度、性能抖动的可控性**。选对 Operator、规划好存储、做好备份恢复演练、建立完整的监控告警，MySQL 在 K8s 上的稳定性可以逼近甚至超过传统 VM 部署，同时获得 GitOps、弹性扩缩、声明式管理等云原生红利。
