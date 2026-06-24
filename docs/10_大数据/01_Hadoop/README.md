# Hadoop

> 大数据时代的"地基"。**HDFS + YARN + MapReduce**三件套定义了"分布式存储+资源调度+批处理"的范式，**整个大数据生态都长在 Hadoop 之上**。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2003 | Google 发表 **GFS 论文** |
| 2004 | Google 发表 **MapReduce 论文** |
| 2006 | Doug Cutting 在 Nutch / Lucene 团队启动 Hadoop |
| 2008 | Apache 顶级项目，Yahoo 第一个大规模部署 |
| 2011 | 1.0 GA |
| 2012 | 2.0 引入 **YARN**（解耦资源管理） |
| 2017 | 3.0 引入 EC（Erasure Coding）省一半空间 |
| 2020 | 3.3 + Ozone（对象存储） |
| 2022 | Hadoop 老态毕现，**云原生 + 数据湖** 大幅蚕食市场 |
| 2024 | 3.4 / 3.5 慢迭代，国内私有化场景仍是主力 |
| 2025 | Cloudera CDP 7.x 商业版主导企业市场 |

> ⚠️ **行业趋势**：公有云大多用 **S3 + Spark on K8s + Iceberg/Delta/Hudi** 替代 Hadoop 三件套；私有化场景 Hadoop 仍是底盘。

## 二、Hadoop 是什么

```
"分布式系统底座" 三大组件:

  HDFS          分布式文件系统（存）
  YARN          资源调度（管）
  MapReduce     批处理框架（算）

外加配套:
  ZooKeeper     协调
  Hadoop Common 工具类库
```

**核心理念**：移动**计算**比移动**数据**便宜（计算下推到数据节点）。

## 三、核心组件

### 3.1 HDFS（存储）

```
NameNode (主):
  - 管理元数据（文件树、Block 位置）
  - 内存型 → 内存就是上限
  - HA: Active + Standby + ZKFC

DataNode (从):
  - 实际存数据（默认 128MB 一个 Block）
  - 3 副本（默认）/ EC 6+3
  - 心跳 + Block Report

JournalNode:
  - HA 模式下共享 EditLog（QJM）
```

**HDFS 特点**：
- 一次写入、多次读取
- 大文件友好（128MB-1GB Block）
- 小文件杀手（每个文件吃 NameNode 内存）
- 顺序读写（追加不友好）
- 副本机制 + 机架感知

### 3.2 YARN（调度）

```
ResourceManager (主):
  - 集群资源仲裁
  - 调度算法: Capacity / Fair / FIFO

NodeManager (从):
  - 节点资源管理（CPU/Mem）
  - 启动 Container

ApplicationMaster:
  - 每个 App 一个，向 RM 申请资源
  - 协调 Container 执行
```

### 3.3 MapReduce（计算）

```
输入 → Map → Shuffle → Reduce → 输出

特点:
  ✅ 极致容错（任务失败自动重跑）
  ✅ 处理 PB 级数据
  ❌ 慢（落盘多次）
  ❌ API 复杂

2025 现状:
  → 几乎被 Spark 完全替代
  → 留作历史教学和兼容
```

## 四、Hadoop 生态全景

```
存储层:
  HDFS / Ozone / S3 / OSS / OBS

调度层:
  YARN / K8s (新趋势)

计算层:
  MapReduce (老) / Tez / Spark / Flink

SQL 层:
  Hive / Impala / Presto / Trino / SparkSQL

NoSQL:
  HBase / Phoenix / Kudu

数据采集:
  Flume / Sqoop / Kafka

工作流:
  Oozie / Airflow / DolphinScheduler

机器学习:
  Mahout (老) / Spark MLlib

数据湖格式:
  Hive ACID / Iceberg / Delta / Hudi

安全:
  Kerberos / Ranger / Sentry

服务化:
  HUE / Knox / Atlas / Ambari
```

## 五、使用场景

### ✅ 仍然推荐

- **私有化大数据平台**（金融、政务、运营商）
- **PB 级冷数据归档**（替代磁带）
- **离线数据仓库**（Hive + Spark 跑 T+1）
- **Hadoop 周边生态依赖**（HBase / Hive / Atlas / Ranger）
- **国内私有化 Cloudera CDP / 国产发行版**

### ⚠️ 不推荐 / 慎选

- **新建项目（云上）** → 直接 S3 + Spark on K8s + Iceberg
- **流处理为主** → Flink + Kafka，不需要 Hadoop
- **OLAP 实时分析** → Doris / StarRocks / ClickHouse
- **小数据量（< 10TB）** → 单机 PG / DuckDB 完爆
- **AI/ML 训练存储** → S3 / 高速文件系统更合适

## 六、Hadoop vs 现代替代

| 维度 | Hadoop | S3 + Spark on K8s | Snowflake/Databricks |
|:---|:---|:---|:---|
| 存储 | HDFS | 对象存储 | 云原生分层 |
| 调度 | YARN | K8s | 托管 |
| 弹性 | ⚠️ 物理扩容 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 运维成本 | **高** | 中 | 极低 |
| 成本 | 自建省/规模大 | 中 | 贵 |
| 适合规模 | PB 私有化 | TB-PB 云 | 任意 |
| 主流度（2025）| 私有化 | 云上主流 | 海外 SaaS |
| 国内现状 | 仍主力 | 上升 | 几乎不用 |

## 七、最佳实践

### 7.1 集群规划

```
最小生产 HA 集群:
  3× Master 节点 (NN x 2 + JN x 3 + ZK x 3 + RM x 2)
  N× Worker 节点 (DN + NM 同机部署)
  独立 Edge 节点 (Hive Server / 客户端 / Hue)
  独立 Hue / Oozie / Ranger

硬件:
  Master: 128GB+ 内存（NN 吃内存）
  Worker: 256GB-512GB / 12-24 块 SATA HDD / 万兆双网
  网络:   万兆 + 机架感知 + 物理分布
```

### 7.2 HDFS 关键参数

```xml
<!-- hdfs-site.xml -->
<property>
  <name>dfs.replication</name>
  <value>3</value>
</property>
<property>
  <name>dfs.blocksize</name>
  <value>268435456</value>          <!-- 256MB -->
</property>
<property>
  <name>dfs.namenode.handler.count</name>
  <value>100</value>
</property>
<property>
  <name>dfs.datanode.balance.bandwidthPerSec</name>
  <value>104857600</value>          <!-- 100MB/s balancer -->
</property>
<property>
  <name>dfs.namenode.heartbeat.recheck-interval</name>
  <value>300000</value>
</property>
<!-- 多目录 -->
<property>
  <name>dfs.datanode.data.dir</name>
  <value>/data01/dn,/data02/dn,...,/data12/dn</value>
</property>
```

### 7.3 YARN 关键参数

```xml
<!-- yarn-site.xml -->
<property>
  <name>yarn.nodemanager.resource.memory-mb</name>
  <value>200000</value>             <!-- 单节点可分配 200G -->
</property>
<property>
  <name>yarn.nodemanager.resource.cpu-vcores</name>
  <value>48</value>
</property>
<property>
  <name>yarn.scheduler.minimum-allocation-mb</name>
  <value>1024</value>
</property>
<property>
  <name>yarn.scheduler.maximum-allocation-mb</name>
  <value>49152</value>
</property>
<property>
  <name>yarn.scheduler.capacity.maximum-am-resource-percent</name>
  <value>0.3</value>
</property>
```

### 7.4 队列设计（Capacity Scheduler）

```xml
<!-- capacity-scheduler.xml -->
root
├── default       10%
├── prod          50%
│   ├── etl       30%
│   └── adhoc     20%
└── dev           40%

每队列设:
  capacity / maximum-capacity
  user-limit-factor
  acl_submit_applications
  state ON/OFF
```

### 7.5 高可用要点

```
NameNode HA:
  2 个 NN + 3-5 JournalNode + ZKFC + 共享存储 EditLog
  自动故障切换 (failover)

ResourceManager HA:
  2 个 RM + ZK 状态存储
  自动故障切换

HDFS 副本:
  生产 3 副本起步
  EC 6+3 节省 50% 空间（冷数据）

机架感知:
  topology.script.file.name → 副本跨机架放置
```

### 7.6 小文件治理（杀手级问题）

```
HDFS 怕小文件:
  1 亿文件 = NameNode 30GB+ 内存
  → NN 内存爆，集群卡死

治理:
  1. 合并: Hive ALTER TABLE CONCATENATE / 自定义 MR
  2. 归档: HAR (Hadoop Archive)
  3. 改格式: ORC/Parquet 列存 + 大块
  4. 直接换存储: 用 Iceberg/Hudi/Delta + 对象存储
  5. 监控告警: 文件数 / 平均文件大小
```

### 7.7 数据安全

```
认证: Kerberos (KDC)
授权: Ranger / Sentry
加密:
  ✅ 传输: RPC SASL + TLS
  ✅ 静态: HDFS 透明加密 (EZ + KMS)
  ✅ 列级: Ranger Column Masking

审计: Ranger Audit → Solr/ES
```

### 7.8 存储格式选择

| 格式 | 适合 |
|:---|:---|
| TEXT | 原始日志（少用） |
| SequenceFile | 中间数据（老） |
| **ORC** | Hive 默认，压缩+索引强 |
| **Parquet** | Spark/Impala/Presto 默认 |
| Avro | 流式 + Schema 演进 |
| **Iceberg/Delta/Hudi** | 现代数据湖（**优先**）|

### 7.9 计算与存储分离（趋势）

```
传统 Hadoop:
  计算 + 存储同节点（移动计算）

现代趋势:
  存储: S3/OSS/MinIO/Ozone
  计算: Spark / Flink on K8s
  
优势:
  - 弹性伸缩独立
  - 多引擎共享存储
  - 成本下降（对象存储便宜）
  - 跨可用区可用
```

## 八、运维命令速查

```bash
# HDFS
hdfs dfs -ls /                       # 列目录
hdfs dfs -du -h /user                # 大小
hdfs dfs -count -q /                 # 配额
hdfs dfs -setrep -w 2 /path          # 改副本
hdfs dfs -setSpaceQuota 1T /user/foo # 配额

hdfs fsck /                          # 健康检查
hdfs dfsadmin -report                # 集群报告
hdfs dfsadmin -safemode get/enter/leave
hdfs dfsadmin -refreshNodes
hdfs balancer -threshold 10          # 平衡

# 故障
hdfs haadmin -getServiceState nn1    # 主备状态
hdfs haadmin -failover nn2 nn1       # 强制切换

# YARN
yarn application -list
yarn application -kill app_xxxx
yarn node -list
yarn rmadmin -refreshQueues

# 日志
yarn logs -applicationId app_xxxx
yarn logs -applicationId app_xxxx -containerId container_xxx
```

## 九、常见坑

| 坑 | 建议 |
|:---|:---|
| **NameNode 内存爆** | 治理小文件 + 升级 NN 内存 |
| **副本损坏** | hdfs fsck + 修复 |
| **磁盘满 90%** | balancer + 扩容 + 删冷数据 |
| **DataNode 频繁掉线** | 网络/磁盘检查 + 心跳调优 |
| **YARN App 卡 Pending** | 队列容量 + AM 资源 |
| **MR 任务慢** | 切换 Spark / Tez |
| **Kerberos 票据过期** | 自动 renew + 监控 |
| **机架感知没配** | 副本不跨机架，机架挂全丢 |
| **EC 误用热数据** | EC 仅适合冷数据 |
| **Balancer 拖慢业务** | 限速 bandwidthPerSec |
| **NN 升级双写问题** | 滚动升级 + 演练 |
| **HDFS API 性能差** | 用 SDK + 长连接 |
| **小集群跑大业务** | 升级硬件 / 切云原生 |

## 十、Hadoop 在 K8s（趋势）

```
方案:
  1. HDFS on K8s: 不推荐（存储 + StatefulSet 太复杂）
  2. YARN on K8s: 也不推荐
  3. **Spark on K8s + S3**: 主流方向
  4. **Flink on K8s + S3**: 主流方向
  5. Presto/Trino on K8s: 直查 S3

云原生大数据栈 (2025):
  存储:  S3 / OSS / MinIO / Ozone / JuiceFS
  计算:  Spark on K8s / Flink on K8s
  调度:  Argo Workflow / Airflow / DolphinScheduler
  目录:  Iceberg / Delta / Hudi + Catalog
  查询:  Trino / Presto / StarRocks / Doris
  元数据:Hive Metastore / Polaris / Unity Catalog
```

## 十一、国产 Hadoop 发行版

| 厂商 | 产品 |
|:---|:---|
| **星环科技 Inceptor / TDH** | 国内份额第一（金融） |
| **华为 FusionInsight MRS** | 公私云全栈 |
| **腾讯云 TBDS** | 腾讯托管 |
| **阿里云 EMR** | Hadoop 兼容 + 自研 |
| **Cloudera CDP（含 China）** | 国际版 |
| **百度 BMR** | 老 |
| **TDH-Manager** | 国产 Ambari |

## 十二、监控指标

```
HDFS:
  CapacityUsed / Free
  MissingBlocks / CorruptBlocks
  FilesTotal / BlocksTotal
  NumLiveDataNodes / NumDeadDataNodes
  NameNode RPC: AvgTime / QueueLen
  GC time / heap

YARN:
  AppsRunning / AppsPending / AppsCompleted
  Available/Allocated Memory/Vcores
  NodeManagers Active

工具:
  Prometheus + jmx_exporter
  Ambari / Cloudera Manager
  Grafana 社区 dashboard
```

## 十三、Hadoop 在大数据栈的角色（2025）

```
私有化场景（金融 / 政务 / 运营商）:
  ✅ Hadoop 仍是主力底盘
  ✅ Hive + Spark + HBase 主流
  ✅ Ranger + Atlas + Kerberos 安全合规
  ✅ Cloudera CDP / 星环 TDH 商业版

云上场景:
  ⚠️ 已被 S3 + Spark on K8s + Iceberg 替代
  ⚠️ EMR / DataProc / Synapse 提供托管 Hadoop 但客户在迁出

中等规模 / 创业公司:
  ⚠️ 直接上云原生数据湖
  ⚠️ 跳过 Hadoop 时代
```

## 十四、学习路径

```
入门:
  1. 单机伪分布式 Hadoop 跑通
  2. HDFS / YARN 基础命令
  3. 第一个 MR 程序 (WordCount)
  4. Hive 跑第一条 SQL

中级:
  5. 3 节点 HA 集群部署
  6. Kerberos + Ranger 安全
  7. Spark on YARN 跑大作业
  8. HBase / Phoenix
  9. Sqoop / Flume / Airflow

高级:
  10. NameNode HA / Federation 排查
  11. 性能调优 (RPC / GC / IO)
  12. EC + 多机架部署
  13. 迁移到 Iceberg / Spark on K8s
  14. 商业版选型评估
```

## 十五、未来展望

```
1-3 年:
  - 私有化场景 Hadoop 继续主力
  - 商业发行版（CDP / TDH / FI）稳定
  - 国产化加速替代国际版

3-5 年:
  - Hadoop 三件套被解耦
  - 存储层 → 对象存储 + 数据湖
  - 计算层 → Spark/Flink on K8s
  - YARN 被 K8s 替代

5 年+:
  - "Hadoop" 概念淡化
  - 留存：HDFS + HBase + Hive Metastore 老底
  - 主流：Lakehouse 一统天下
```

> 📖 **核心判断**：Hadoop 是大数据**第一代**底盘，是任何运维必学的基础。新建场景多数应该绕开 Hadoop 三件套，**直接奔向云原生 + 数据湖 + 存算分离**。但运营商/金融/政务私有化场景下，Hadoop 仍将存在很多年——这是你掌握它的现实理由。
