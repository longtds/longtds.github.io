# 最佳实践

> 中间件最佳实践 = **选型方法论 + 容量规划 + 高可用拓扑 + 性能调优基线 + 备份恢复 + 监控告警 + 安全合规 + 多租户 + 容器化(KubeBlocks 平台化) + 国产化路径 + 故障应急 + Postmortem**。本章把"会装中间件"升级到"运营企业级数据基础设施"。

## 一、选型方法论

### 1.1 关系型 DB 选型

| 场景 | 推荐 | 备选 |
|:---|:---|:---|
| 互联网通用 | MySQL ⭐ | PG |
| 复杂查询 / GIS / 向量 / JSONB | PostgreSQL ⭐ | - |
| 金融核心 | OceanBase ⭐ / GaussDB | Oracle (淘汰中) |
| 互联网超大表 | TiDB ⭐ | OceanBase / 分库分表 |
| HTAP 一体 | TiDB + TiFlash ⭐ | OceanBase |
| AI Embedding | PG + pgvector ⭐ | Milvus 独立 |
| 中小型 SaaS | PG ⭐ / MySQL | - |
| 信创 / 国央企 | 达梦 / 人大金仓 / 神舟 / OceanBase / GaussDB | - |

### 1.2 缓存选型

| 场景 | 推荐 |
|:---|:---|
| 通用 KV / 队列 | Redis 7 Cluster |
| 多线程超高 QPS | DragonflyDB / KeyDB |
| 持久化 + 海量 | Pika / Tair LDB |
| 阿里云 | Tair |
| LangChain / AI 缓存 | Redis |
| 短消息 / 限流 | Redis |

### 1.3 消息队列选型

| 场景 | 推荐 |
|:---|:---|
| 日志 / 事件 / 流处理 | Kafka ⭐ |
| 电商订单 / 事务 / 顺序 | RocketMQ ⭐ |
| 企业集成 / 复杂路由 | RabbitMQ |
| 存算分离 / 多租户 / 长留存 | Pulsar |
| 信创 / 国央企 | RocketMQ ⭐ |
| 边缘 / IoT | EMQ X (MQTT) |

### 1.4 搜索 / 分析选型

| 场景 | 推荐 |
|:---|:---|
| 通用全文检索 | Elasticsearch / OpenSearch ⭐ |
| 日志 / 大盘 | OpenSearch + Loki |
| 列存 OLAP / 单表 | ClickHouse ⭐ |
| 实时数仓 / 多表 JOIN | Apache Doris ⭐ / StarRocks |
| 数据湖 | Iceberg + Paimon ⭐ |
| 向量 (业务库共存) | pgvector ⭐ |
| 向量 (独立大规模) | Milvus ⭐ |

### 1.5 时序选型

| 场景 | 推荐 |
|:---|:---|
| IoT 物联网 (海量) | TDengine ⭐ |
| 工业互联网 (Apache) | IoTDB ⭐ |
| Prometheus 长存 | VictoriaMetrics ⭐ |
| 与 PG 共存 | TimescaleDB |
| 全球通用 | InfluxDB |

### 1.6 决策树（团队）

```
Step 1: 业务量 < 1k QPS / 数据 < 1TB → 单机 (MySQL/PG)
Step 2: 1k-10w QPS / 1-10TB → 主从 + 读写分离 + Redis 缓存
Step 3: 10w+ QPS / 10TB+ → 分库分表 (ShardingSphere) 或 分布式 (TiDB/OceanBase)
Step 4: 100w+ QPS / 100TB+ → 分布式 + 存算分离 + 数据湖

辅助决策:
  - 强一致 → MySQL/PG/TiDB/OceanBase
  - 最终一致 OK → Cassandra/Mongo/Dynamo
  - 写多读少 → Cassandra/HBase
  - 复杂查询 → PG/TiDB+TiFlash
  - 海量小写 (IoT) → TDengine
  - 向量 + 业务 → PG + pgvector
  - 向量 + 独立大 → Milvus
```

## 二、容量规划

### 2.1 计算容量

```
公式:
  QPS_peak = 日均请求 / 86400 × 3.5 (尖刺系数)
  数据量 = 日增量 × 保留天数
  连接数 = 服务实例数 × 单实例连接池 × 1.5 (突发)
  Memory = 数据热度 × Working Set + 索引内存 + 元数据 + 余量

示例 (中型电商订单):
  日活 100w
  订单 200w/天 (峰值 200/s, 高峰 1000/s)
  数据 200w × 2KB × 365 = 1.4TB/年
  Redis 缓存: 100w 用户 × 5KB = 5GB Working Set
  MySQL: 64GB 内存 + 16C, buffer pool 40GB
  
3 年规划: 5TB 数据 + 多副本 = 30TB 集群
```

### 2.2 各中间件内存/磁盘配比

```
MySQL:        内存 50-70% buffer pool, 数据/binlog 独立 SSD
PG:           shared_buffers 25%, effective_cache 75%
Redis:        内存 = Working Set × 1.5, 持久化盘 < 内存
Kafka:        内存 page cache 越大越好, 顺序写 HDD 也可
ES:           JVM heap < 32G (压缩指针), 物理 50%, 数据盘 SSD
ClickHouse:   内存 16-64G, 数据 NVMe + 列压缩 10:1
ZooKeeper:    1-4G 内存独占, 日志 SSD
etcd:         1-8G, 必须 NVMe + sync write
```

## 三、高可用基线

### 3.1 中间件 HA 最小副本

| 中间件 | 最小副本 | 推荐 |
|:---|:---:|:---:|
| MySQL MGR | 3 | 3-5 |
| PG Patroni | 3 (1主2从) | 3 |
| Redis Sentinel | 3 (1主2从+3哨兵) | 3-5 |
| Redis Cluster | 6 (3主3从) | 6+ |
| Kafka | 3 broker, 副本 3, min.isr 2 | 5+ |
| Pulsar | 3 broker + 5 bookie | 5+ |
| ES | 3 master + N data | 3 master + 3+ data |
| CK Replicated | 2 副本 × N 分片 | 2 × N |
| ClickHouse Keeper / ZK | 3 | 3-5 |
| etcd | 3 | 3-5 |
| Nacos | 3 | 3 |
| MinIO | 4 (EC 2+2) | 8+ |
| Nginx | 2 + Keepalived VIP | 2-3 |

### 3.2 故障域隔离

```
跨节点 podAntiAffinity
跨机柜 topologySpreadConstraints (rack)
跨可用区 topology.kubernetes.io/zone
跨 region Karmada / 异地多活
```

### 3.3 SLA 目标对照

| 业务 | SLA | 月可用 | 年可用 |
|:---|:---:|:---:|:---:|
| P0 (支付/订单核心) | 99.99% | 4m | 52m |
| P1 (主业务) | 99.9% | 43m | 8.7h |
| P2 (后台 / 内部) | 99.5% | 3.6h | 1.8d |
| P3 (开发 / 测试) | 99% | 7.2h | 3.6d |

## 四、性能调优基线

### 4.1 MySQL Top 10 调优

```
1.  innodb_buffer_pool_size 50-70% 内存
2.  innodb_log_file_size 1-2GB
3.  innodb_flush_log_at_trx_commit=1, sync_binlog=1 (强)
4.  innodb_flush_method=O_DIRECT
5.  innodb_io_capacity 看磁盘 (SSD: 5000-20000)
6.  并行复制: replica_parallel_workers=8+
7.  查询缓存关闭 (8.0 已去除)
8.  慢查询日志 long_query_time=0.5
9.  pt-query-digest 周分析
10. ProxySQL / MaxScale 读写分离
```

### 4.2 PG Top 10 调优

```
1.  shared_buffers 25% 内存
2.  effective_cache_size 75%
3.  work_mem 4-16MB (按并发)
4.  maintenance_work_mem 1-2GB
5.  max_wal_size 8-16GB
6.  checkpoint_completion_target 0.9
7.  autovacuum 调狠点 (大表 freeze)
8.  pg_stat_statements + auto_explain
9.  连接池 PgBouncer (transaction mode)
10. Patroni HA + WAL-G 备份
```

### 4.3 Redis Top 10 调优

```
1.  maxmemory + allkeys-lru 策略
2.  AOF + everysec
3.  禁危险命令 (KEYS / FLUSHALL / CONFIG / DEBUG)
4.  Big key 监控 + UNLINK 异步
5.  TCP keepalive 60s
6.  Cluster timeout 15s
7.  关闭 transparent_hugepage
8.  内核 vm.overcommit_memory=1
9.  Pipeline 批量 (减 RTT)
10. 主从延迟监控 + 自动 failover
```

### 4.4 Kafka Top 10 调优

```
1.  num.network.threads / io.threads 跟 CPU
2.  Producer batch.size=128KB, linger.ms=10
3.  Producer compression=lz4 / zstd
4.  acks=all + idempotence + max.in.flight=5
5.  Consumer max.poll.records=500-2000, fetch.min.bytes=64KB
6.  Replica num.replica.fetchers=8
7.  Page cache: 内存 大, 磁盘 SSD/HDD 顺序
8.  Disk: log.segment.bytes=1GB
9.  Tiered Storage / 冷数据归档
10. kafka-lag-exporter + 关键 alert
```

### 4.5 ES Top 10 调优

```
1.  JVM heap <= 32G (压缩指针)
2.  refresh_interval 30s (写多读少)
3.  bulk request 5-15MB
4.  分片 30-50GB, 数量 = 节点 × 1-3
5.  ILM rollover + shrink + force_merge
6.  master / data / ingest 角色分离
7.  禁 fielddata 滥用
8.  doc_values 默认开
9.  pre-shutdown drain (rolling restart)
10. Snapshot to S3 + 季度恢复演练
```

### 4.6 ClickHouse Top 10 调优

```
1.  ORDER BY 关键: 主键设计 (低基数 → 高基数)
2.  PARTITION BY 按时间 (toYYYYMM)
3.  TTL 自动清理
4.  Replicated + Distributed 双层
5.  LowCardinality 字段
6.  AggregatingMergeTree / SummingMergeTree 物化视图
7.  index_granularity 调
8.  压缩 ZSTD / LZ4
9.  max_threads / max_memory_usage
10. Keeper 替代 ZK
```

## 五、监控告警必备

```
Prometheus exporter:
  mysqld_exporter, postgres_exporter, redis_exporter
  kafka_exporter + kafka-lag-exporter
  elasticsearch_exporter
  clickhouse_exporter / clickhouse 内置 prom endpoint
  nginx-prometheus-exporter
  zookeeper-prometheus-exporter
  mongodb_exporter
  vault_exporter
  patroni_exporter

必备告警 (按类):
☐ MySQL: 主从延迟 / 连接数 / buffer hit / slow log 激增 / 复制中断
☐ PG: WAL lag / connection / autovacuum lag / bloat / replication slot
☐ Redis: maxmem / keyspace_miss / latency / cluster_state / 大key
☐ Kafka: lag / under-replicated / offline partitions / controller count
☐ ES: yellow/red status / JVM old gen / disk watermark / pending tasks
☐ CK: replica queue / parts count / merge失败 / disk
☐ Nginx: 5xx / upstream timeout / connections / SSL expire
☐ Nacos: cluster health / DB connection / token expire
☐ etcd: leader / slow apply / disk sync / quorum

Grafana Dashboard ID:
  7362  MySQL
  9628  PostgreSQL  
  763   Redis
  7589  Kafka
  266   Elasticsearch
  14192 ClickHouse
  12708 Nginx
  9967  ZooKeeper
  2747  MongoDB
  10000 etcd
```

## 六、备份恢复 SOP

### 6.1 三层备份

```
1. 物理快照 (XtraBackup / pg_basebackup) → 全 + 增 + Binlog/WAL
2. 逻辑备份 (mysqldump / pg_dump) → 周
3. Snapshot (Velero PV / RBD / OSS) → 日

频率:
  全:    周 1
  增:    日 1
  Binlog/WAL: 实时归档

存储:
  本地 + 异地 (OSS / S3 / 私有 MinIO)
  保留: 7d 本地 + 90d 异地
```

### 6.2 必备演练

```
☐ MySQL 单机恢复 < 30 min
☐ PG PITR 到任意时间点 < 1h
☐ Redis RDB / AOF 恢复 < 10 min
☐ Kafka Topic 恢复 / Tiered Storage 回放
☐ ES Snapshot 恢复
☐ CK Mutation 回滚
☐ 整集群跨 region 切换 < 30 min (P0)
☐ 季度演练 + Postmortem
```

## 七、安全合规

### 7.1 必备基线

```
☐ 强口令 (12+ 位, 90 天换)
☐ 网络隔离 (VPC / SG / NetworkPolicy)
☐ TLS 全栈 (传输加密)
☐ 数据加密 (透明加密 TDE / 列加密)
☐ Audit log → SIEM 留存 180 天
☐ 操作审计 + 双人审 (变更 / DROP / DELETE 全表)
☐ 权限最小化 (业务账号 ≠ root)
☐ 备份加密
☐ 防 SQL 注入 (业务侧)
☐ 慢查询 / 全表扫 告警
☐ Bastion / 跳板机 + 4A 审计
```

### 7.2 合规等级

```
等保三级 (国央企必):
  ☐ 国密算法 (SM2/3/4)
  ☐ 日志留存 6 个月
  ☐ 异地灾备 RTO < 4h, RPO < 1h
  ☐ 数据脱敏 / 加密
  ☐ 双人复核 + 审计独立
  ☐ 漏扫 + 渗透 半年

GDPR / 国内数据出境:
  ☐ 数据本地化
  ☐ 用户授权
  ☐ 跨境评估
  ☐ 数据删除接口

金融行业:
  ☐ 三地五中心
  ☐ RTO < 30 min, RPO ≈ 0
  ☐ 强一致 + 单元化
  ☐ 监管报送
```

## 八、多租户

```
租户隔离层次:
  软隔离: namespace + RBAC + Quota (单集群)
  半隔离: 独立 instance + 共享底层
  强隔离: 独立集群 + 独立 K8s namespace

多租户场景:
  ☐ Nacos Namespace
  ☐ ES tenant + index pattern + RBAC
  ☐ ClickHouse Database + Quota
  ☐ Pulsar tenant/namespace
  ☐ MySQL: 一库一租户 / 共享库分 schema
  ☐ KubeBlocks: Cluster per tenant
```

## 九、容器化深度（KubeBlocks 平台）

### 9.1 推荐架构

```
门户:        自研 Web UI + Backstage 插件
API:         Go/Java + KubeBlocks API
Operator:    KubeBlocks ⭐ (30+ DB)
存储:        Rook-Ceph / Longhorn / 阿里 ESSD / Topolvm
备份:        KubeBlocks Backup + Restic + S3
监控:        kube-prometheus-stack + 每 DB exporter
日志:        Loki / ELK
SSO:         Keycloak
工单:        自研 + Jira
计费:        OpenCost + 自研维度
```

### 9.2 自助申请流程

```
用户:
  门户 → 选 DB 类型 / 规模 / 备份策略
  → 工单审批
  → KubeBlocks Cluster CRD 提交
  → 5-10 min 集群就绪
  → 自动发邮件 (连接信息 + 监控大盘)

运维:
  策略 Kyverno 强制 (副本 / quota / 备份)
  自动接 Prometheus / Loki / SSO
  成本归属 label
```

### 9.3 国央企/信创 容器化路径

```
信创 K8s:    KubeSphere / 华为 CCE / 阿里 ACK 一种
信创 OS:    openEuler / 麒麟
信创 CPU:   鲲鹏 / 飞腾 / 海光
存储:        Rook-Ceph (国产可控) + 国密 TLS
中间件:     KubeBlocks (开源国产) + OceanBase / TiDB / Tair
监控:        DeepFlow + 夜莺
```

## 十、故障应急 SOP

### 10.1 通用 5 步

```
1. 接告警 → 确认 (ack 1-2 min)
2. 快速诊断 (大盘 / exporter / 日志, 5-10 min)
3. 决策 (回滚 / 切主 / 限流 / 重启, 必 SOP)
4. 执行 (按 runbook, 双人复核)
5. 恢复 → 观察 30 min → Postmortem
```

### 10.2 中间件常见 SOP

```
MySQL 主挂:
  1. 看 MGR 状态 / VIP
  2. patronictl failover / mysqlsh > cluster.forceQuorumUsingPartitionOf
  3. 验证业务恢复
  4. 修主节点重新加入

Kafka 集群 down:
  1. 看 controller / under-replicated
  2. 重启 broker 一个个
  3. 修磁盘 / 网络
  4. 验证业务 Producer/Consumer

Redis 主挂:
  1. Sentinel 自动 failover (15s)
  2. 验证 slave promote
  3. 修原主 (清数据 / 重新同步)

ES 全 Red:
  1. _cluster/health, _cat/shards
  2. 重启 master / 修磁盘 watermark
  3. allocate stale primary (最后)
  4. 恢复后 force_merge

ClickHouse Replica Queue 大:
  1. SYSTEM DROP REPLICA (异常副本)
  2. SYSTEM RESTART REPLICA
  3. 重 sync metadata

Nacos DB 挂:
  1. 切 MGR 主节点
  2. 重启 Nacos cluster
  3. 验证服务注册 + 配置
```

## 十一、Checklist（最佳实践）

```
选型:
☐ 选型决策树 (业务量 + 一致性 + 模型)
☐ Top 中间件矩阵 (MySQL/PG/Redis/Kafka/RocketMQ/ES/CK/Nginx/Nacos)
☐ 国产分布式 DB 替代评估 (TiDB/OceanBase/GaussDB)

容量:
☐ QPS / 数据 / 连接 / 内存 公式
☐ 3 年规划 + 弹性扩容
☐ 资源画像 (KRR / VPA)

HA:
☐ 最小副本表
☐ 跨节点/AZ/region 拓扑
☐ SLA 分级 + Pyrra SLO

调优:
☐ Top 10 调优清单 (按中间件)
☐ 基线模板 (config 模板)
☐ pt-query-digest / pg_stat_statements / slow log 周分析

监控:
☐ exporter 全覆盖
☐ Grafana 标准大盘
☐ 必备告警 + on-call 升级

备份:
☐ 三层备份 (物理 / 逻辑 / Snapshot)
☐ 异地 + 加密 + 保留策略
☐ 季度恢复演练 RTO/RPO

安全:
☐ 网络 + TLS + 加密
☐ Audit + SIEM 180d
☐ 等保三级 / 国密 / 国测

多租户:
☐ 强弱隔离矩阵
☐ Quota + RBAC + NP
☐ 成本归属

容器化:
☐ KubeBlocks 一站式
☐ Operator 主流 (Strimzi / CloudNativePG / ECK / Altinity)
☐ 自助 + 工单 + 监控
☐ Velero 备份

应急:
☐ 各 DB runbook
☐ 演练季度 + Postmortem
☐ 知识库归档
```

## 十二、典型生产架构

### 12.1 互联网中型电商

```
OLTP:        MySQL MGR + ProxySQL 读写分离
缓存:        Redis Cluster (6 节点) + 阿里 Tair (可选)
消息:        RocketMQ 双主双从同步 (订单/支付)
搜索:        ES 6 节点 (商品/订单)
注册/配置:   Nacos 3 节点 + MySQL MGR
日志:        Kafka + Loki + Grafana
OLAP:        ClickHouse 6 节点 (订单/行为)
向量:        PG + pgvector (推荐)
网关:        Higress (Envoy + Istio)
反代:        Nginx + Keepalived VIP
```

### 12.2 央企信创

```
OLTP:        OceanBase / GaussDB + KubeBlocks
缓存:        Redis Cluster + 国密 TLS
消息:        RocketMQ 同步双主双从
搜索:        OpenSearch + 国密
OLAP:        Doris / StarRocks (国产 MPP)
注册:        Nacos 集群 (内网部署)
存储:        Rook-Ceph + 国密
监控:        DeepFlow + 夜莺
反代:        APISIX 国密 + Keepalived
合规:        等保三级 + 国测 + 国密 + 加密机
```

### 12.3 AI 公司

```
OLTP:        PG 16 + pgvector (业务 + 向量)
向量大规模: Milvus + Qdrant 双栈
缓存:        Redis Cluster
消息:        Kafka KRaft + Pulsar (推理日志 / 长留存)
日志/事件:   ClickHouse (推理日志大宽表)
特征:        Feast + Redis + Cassandra
模型注册:   MLflow / Nexus / Harbor (大文件 LFS)
工作流:     Argo Workflows + Pulsar
```

### 12.4 党政关基

```
OLTP:        达梦 / 人大金仓 / OceanBase
缓存:        Redis (信创 OS + 鲲鹏)
消息:        RocketMQ
搜索:        OpenSearch
存储:        Rook-Ceph 国密
合规:        等保 + 商密 + 关基 + 国测 + 国密
```

## 十三、推荐栈（最佳实践）

```
OLTP:     MySQL ⭐ / PG ⭐ / TiDB ⭐ / OceanBase ⭐ / 达梦 (信创)
NoSQL:    MongoDB / Cassandra / DynamoDB
缓存:     Redis ⭐ / Tair / Dragonfly / KeyDB / Pika
消息:     Kafka ⭐ / RocketMQ ⭐ / Pulsar / RabbitMQ
注册/配置: Nacos ⭐
搜索:     Elasticsearch ⭐ / OpenSearch ⭐
OLAP:     ClickHouse ⭐ / Doris ⭐ / StarRocks ⭐
向量:     pgvector ⭐ + Milvus ⭐ / Qdrant
时序:     TDengine ⭐ / IoTDB ⭐ / VictoriaMetrics
数据湖:   Iceberg / Paimon ⭐
反代/网关: Nginx ⭐ / APISIX ⭐ / Higress ⭐
图:       Nebula ⭐ / Neo4j
DBaaS:    KubeBlocks ⭐ (一站式 30+ DB)
Operator: Strimzi / CloudNativePG / ECK / Altinity / Pulsar Op
监控:     kube-prometheus-stack + 各 exporter + DeepFlow + 夜莺
备份:     XtraBackup + WAL-G + Velero + S3 (异地)
安全:     国密 (Tongsuo) + 加密机 + Audit + SIEM
平台:     自研 + Backstage 插件 + Keycloak SSO
```

> 📖 **核心判断**：中间件最佳实践 = **选型决策树 + 容量规划 + HA 副本基线 + Top 10 调优 + 监控告警 + 三层备份 + 安全合规(国密/等保) + 多租户 + KubeBlocks 容器化 + 国产化路径 + 应急 SOP**。能给团队画"MySQL MGR / PG Patroni / Redis Cluster / Kafka KRaft / Nacos 集群 / ES + ILM / CK Replicated / Nginx VIP / KubeBlocks 一站式 + Prometheus 监控 + Velero 备份 + 国密合规"全栈架构、能 Q1 演练 + 灾备切换 + 多租户 + 国产化路径，就具备中间件平台负责人能力。
