# 最佳实践

> 大数据最佳实践 = **数据架构选型(Lakehouse vs 传统数仓) + 数据分层标准 + 命名规范 + Spark/Flink 工程化基线 + 实时数仓基线 + 调度+ETL 规范 + 数据治理体系 + 数据质量+SLA + 数据安全合规 + FinOps + 平台化 + 团队组织 + Incident SOP**。本章把"会跑 Spark/Flink"升级到"运营企业级数据中台"。

## 一、架构选型

### 1.1 决策树

```
业务规模 → 架构推荐:

小型 (单表 < 10TB, QPS < 100):
  PG / MySQL + Superset
  无需大数据

中型 (TB-100TB, QPS 100-1k):
  Kafka + Flink + ClickHouse/Doris + Superset
  调度: Airflow / DolphinScheduler
  
大型 (100TB-PB, QPS 1k-10k):
  Kafka + Flink + Paimon/Iceberg + Doris/StarRocks + Trino
  Spark 批 + Hudi/Iceberg 历史
  DataHub + Soda 治理
  
超大 (10PB+):
  完整湖仓 + 数据网格
  多源 + 多云 + AI Native
  Snowflake-like 商业 / 自建
```

### 1.2 引擎组合最佳实践

| 场景 | 主引擎 | 备选 |
|:---|:---|:---|
| **实时数仓 (主键 + 联邦)** | Doris ⭐ / StarRocks ⭐ | TiDB+TiFlash |
| **日志大单表 / 高并发** | ClickHouse ⭐ | Druid |
| **湖仓 (多引擎共享)** | Iceberg + Trino ⭐ | Hudi |
| **流批一体 (CDC 入湖)** | Paimon + Flink ⭐ | Hudi + Spark |
| **Ad-hoc 跨源** | Trino ⭐ | StarRocks Catalog |
| **数据集成** | SeaTunnel ⭐ | Flink CDC, DataX |
| **调度** | Airflow / DolphinScheduler | Argo Workflows, Dagster |
| **特征工程** | Feast ⭐ | Tecton (商业) |

## 二、数据分层标准

### 2.1 标准 5 层

```
ODS (Operational Data Store)
  - 原始数据 1:1
  - 来源: Kafka / MySQL CDC / 日志
  - 表名: ods_<source>_<table>_<freq>
  - 例: ods_mysql_orders_d, ods_kafka_clicks_h
  - 存储: Paimon / Iceberg (主键表)
  - 保留: 长 (1-3 年)

DWD (Data Warehouse Detail)
  - 清洗 + 标准化 + 维度退化
  - 单事实表 / 单事件
  - 表名: dwd_<domain>_<event>_<freq>
  - 例: dwd_trd_order_pay_d
  - 存储: Paimon / Iceberg
  - 保留: 长 (3 年+)

DIM (Dimension)
  - 维度表 (用户/商品/地区/时间)
  - 表名: dim_<entity>
  - 例: dim_user, dim_item
  - SCD Type 2 (保留历史)
  - 存储: Paimon (主键 / SCD2)

DWS (Data Warehouse Summary)
  - 轻度聚合 / 主题宽表
  - 业务可用 (但不直面应用)
  - 表名: dws_<domain>_<metric>_<freq>
  - 例: dws_trd_user_order_d (用户日订单宽表)
  - 存储: Paimon / Doris (双写)

ADS (Application Data Service)
  - 面向业务应用
  - 高聚合
  - 表名: ads_<biz>_<metric>_<freq>
  - 例: ads_dashboard_gmv_d
  - 存储: Doris / ClickHouse (查询加速)

(可选) TMP (临时层)
  - tmp_xxx
  - 7 天自动清理
```

### 2.2 命名规范

```
数据库 (Iceberg / Paimon catalog):
  iceberg.<domain>_<layer>   例: iceberg.trd_dwd
  
表:
  <layer>_<domain>_<event/metric>_<freq>
  例: dwd_trd_order_pay_d
  
字段:
  下划线 snake_case
  关键字段: id, name, status, create_time, update_time
  统一: ts (事件时间), etl_ts (ETL 时间), dt (分区日期)
  
任务:
  <layer>_<domain>_<table>
  例: dwd_trd_order_pay
```

## 三、Spark/Flink 工程化基线

### 3.1 项目结构

```
data-platform/
├── airflow/dags/             # 调度
├── flink-jobs/               # Flink Job
│   ├── pom.xml / build.gradle
│   ├── src/main/java/
│   ├── src/main/resources/    # SQL / config
│   └── docker/
├── spark-jobs/               # Spark Job
│   ├── pyproject.toml
│   ├── jobs/
│   └── tests/
├── dbt/                      # dbt 模型 (SQL)
│   ├── models/
│   ├── tests/
│   └── dbt_project.yml
├── lake/                     # 数据湖 DDL (Paimon/Iceberg)
│   ├── ods/
│   ├── dwd/
│   ├── dim/
│   └── dws/
├── platform/                 # 平台组件
│   ├── helm/
│   └── kustomize/
└── docs/                     # MkDocs
```

### 3.2 CI/CD 基线

```
.gitlab-ci.yml:
  stages:
    - lint        (sqlfluff / black / scalafmt)
    - unit        (pytest / scalatest)
    - build       (spark image + flink jar)
    - integration (TestContainers Kafka/Flink/Paimon)
    - deploy-dev  (Argo Workflows + Spark/Flink Operator)
    - deploy-prod (gate + Argo Rollouts)

Image:
  base: harbor.example.com/spark/spark:3.5
  base: harbor.example.com/flink/flink:1.19
  各 Job 镜像继承 base + deps
```

### 3.3 配置 + 秘密

```
配置:
  环境变量 + ConfigMap
  Nacos / Apollo (动态)
  
秘密:
  Vault + ESO ⭐
  - DB 密码
  - S3 Access Key
  - Kafka SASL

K8s ServiceAccount:
  - spark-driver / spark-executor
  - flink (RBAC: 创建 deploy/cm/pod)
  - 最小权限
```

## 四、实时数仓基线

### 4.1 推荐架构

```
Source:
  - Kafka (业务事件 / 日志)
  - MySQL CDC (Flink CDC / Debezium)
  - 文件 (S3 watch)

Stream:
  - Flink Job: CDC → Paimon ODS
  - Flink SQL: ODS → DWD → DWS (流式)
  
Lake:
  - Paimon (流批一体) ⭐
  - Iceberg (批 + 联邦)
  
Serving:
  - Doris/StarRocks (实时数仓加速)
  - ClickHouse (大宽表)
  - Trino (即席)
  
应用:
  - Superset/FineBI (BI)
  - 业务 API (Doris MySQL 协议)
```

### 4.2 KPI 与 SLA

```
新鲜度 (Freshness):
  ODS:   < 30s
  DWD:   < 1 min
  DWS:   < 5 min
  ADS:   < 5 min
  T+1 表: 凌晨 6:00 前

可用性:
  ODS / DWD: 99.9%
  DWS / ADS: 99.95% (业务关键)

延迟 P99:
  Flink end-to-end: < 30s
  Doris 查询: < 200 ms

数据质量:
  完整性: > 99.99%
  准确性: > 99.95%
  及时性: 同新鲜度
```

## 五、调度 + ETL 规范

### 5.1 调度选型基线

```
Python 团队 + 高灵活:   Airflow ⭐
国央企 + 可视化:        DolphinScheduler ⭐
K8s 原生 + 微服务化:    Argo Workflows
现代 Python + Asset:    Dagster
```

### 5.2 任务规范

```
☐ 命名: <layer>_<domain>_<table>
☐ 资源: requests/limits 显式
☐ 重试: 最多 3 次 + 指数退避
☐ 超时: 业务 SLO × 2
☐ 依赖: 显式 (Airflow >> 或 DolphinScheduler 依赖节点)
☐ 幂等: 必备 (重跑同结果)
☐ 数据契约 CI 验证
☐ 数据质量 (Soda) 后置
☐ 血缘 (DataHub) 自动
☐ 告警 (Slack/钉钉) on-call
☐ Postmortem 模板
☐ 监控大盘
```

### 5.3 失败 / 重跑 SOP

```
失败:
  1. 告警接收
  2. 看任务日志 (Airflow / Spark UI / Flink Web)
  3. 判断: 临时 (网络/资源) vs 持久 (代码/数据)
  4. 临时 → 重跑; 持久 → 修代码 / 数据
  
重跑:
  - 幂等任务: 直接 retry
  - 非幂等: 先 delete partition / TRUNCATE / 反向操作
  - 大表 重跑 → 影子库 / 蓝绿
```

## 六、数据治理体系

### 6.1 三层治理

```
战略层:
  - 数据愿景 / KPI
  - 数据安全合规
  - 数据资产化

战术层:
  - DataHub / OpenMetadata 元数据
  - 数据契约 + Schema 注册
  - 数据所有权 (Domain Owner)
  - 数据质量基线

执行层:
  - dbt + Soda + Great Expectations CI
  - Spark/Flink listener (血缘)
  - Iceberg/Paimon Schema Evolution
  - Backstage Self-service
```

### 6.2 必备角色

```
Chief Data Officer (CDO):     战略 / 投资
Data Architect:              架构 / 选型
Data Engineer:               ETL / 实时
Data Steward:                业务术语 / 质量
Data Owner:                  Domain 责任人
Analyst / Scientist:         BI / 模型
Platform Engineer:           平台
DBA / FinOps:                成本
```

### 6.3 元数据 + 血缘必备

```
☐ DataHub / OpenMetadata 部署
☐ Spark Listener / Flink Lineage 接入
☐ dbt / Airflow / DolphinScheduler 集成
☐ Iceberg / Paimon Catalog 接入
☐ Domain + Glossary + Owner
☐ 列级血缘 (DataHub)
☐ 自动通知 (新字段 / 弃用)
```

## 七、数据质量 + SLA

### 7.1 质量规则示例（Soda）

```yaml
# checks/dwd_orders.yml
checks for dwd_trd_order_pay_d:
  - missing_count(user_id) = 0
  - missing_count(amount) = 0
  - duplicate_count(id) = 0
  - row_count > 1000
  - row_count anomaly score < 3   # ML 异常检测
  - freshness(etl_ts) < 1h
  - failed rows:
      name: amount must be positive
      fail condition: amount <= 0
```

### 7.2 SLA 监控

```
新鲜度 SLA:
  - Soda freshness check
  - DataHub Freshness Assertions
  - Prometheus + 自定义 exporter
  
完整性 SLA:
  - row_count anomaly
  - 关键字段 missing_count

准确性 SLA:
  - 业务规则 (amount > 0 / status 枚举)
  - 跨表一致性 (订单总额 = 明细汇总)

告警:
  - on-call (钉钉/飞书)
  - Slack data-quality 频道
  - DataHub 标记 Stale / Failed
```

## 八、数据安全合规

```
☐ 数据分级 (公开/内部/敏感/绝密 L0-L3)
☐ 敏感数据自动识别 (PII Scanner)
☐ 列级权限 (Apache Ranger + LDAP)
☐ 行级权限 (Trino / Doris Row Policy)
☐ 动态脱敏 (查询时 mask)
☐ 静态脱敏 (ETL 时)
☐ 字段加密 (KMS / 国密)
☐ 操作审计 → SIEM 180d
☐ 跨境合规 (评估)
☐ 等保三级 / 国测
☐ 国密 SM2/3/4
☐ 隐私计算 (秘塔 / 蚂蚁 SecretFlow)
```

## 九、FinOps

```
成本归属:
  ☐ 强制 label cost-center / team / domain
  ☐ Kubecost / OpenCost 汇总
  ☐ Spark/Flink 任务级成本 (历史 + 实时)
  ☐ 存储成本 (S3 / 对象存储)
  ☐ 计算成本 (Spark / Flink 实例时长)

优化:
  ☐ 小文件治理 (rewrite_data_files)
  ☐ Snapshot expire (减元数据)
  ☐ TTL 自动归档/删除
  ☐ Spot / 抢占实例 (test / 非关键)
  ☐ 动态分配 / scaling
  ☐ 冷热分层 (热 SSD / 冷 OSS Archive)
  ☐ 列存压缩 (zstd / lz4)
  ☐ Bloom Filter Index
  ☐ Z-Order / Cluster
  ☐ Doris MV 替代重复查询
  
KPI:
  ☐ 单 TB 数据成本 < ¥/月
  ☐ 任务时长 P95 < SLO
  ☐ 集群利用率 > 65%
```

## 十、平台化

### 10.1 自服务门户

```
Backstage 数据 IDP:
  - 数据集 Catalog (自动从 DataHub)
  - 业务术语 (Glossary)
  - 数据申请 (审批 + RBAC 自动)
  - 任务监控 (Airflow / DS / Flink UI 集成)
  - 成本归属 (OpenCost 集成)
  - 数据质量 (Soda Dashboard)
  - 黄金路径 (Software Template: 新 ETL 任务 / 新湖表 / 新 Flink Job)

工具:
  - Backstage + dbt plugin + DataHub plugin
  - 阿里 DataWorks (商业)
  - 字节 Las (内部)
  - 自研门户 (Go/Java + DataHub API)
```

### 10.2 黄金路径模板

```
模板 1: 新 ETL 任务 (Airflow)
  - DAG template + 资源配置 + Soda check + DataHub upstream

模板 2: 新 Flink Job
  - Flink Operator YAML + Paimon catalog + Checkpoint to S3

模板 3: 新湖表 (Iceberg/Paimon)
  - 分区 / 主键 / TTL / Owner / 业务术语

模板 4: 新 Doris/StarRocks 表
  - 分桶 / 副本 / 物化视图建议

模板 5: 新 dbt 模型
  - source + test + Sphinx 文档
```

## 十一、Incident SOP

### 11.1 数据故障分级

```
P0 (业务停止):
  - 数据完全不可用
  - 大盘空 / 业务报表无数据
  - GMV 错算 → 资金风险
  RTO: 30 min

P1 (业务部分):
  - 单一表 / DAG 失败
  - 数据延迟 > 1h
  RTO: 2h

P2 (体验下降):
  - 数据延迟 < 1h
  - 单一报表小问题
  RTO: 1d

P3 (内部 / 测试):
  - dev / staging 故障
  RTO: 周内
```

### 11.2 应急步骤

```
0-5 min: 确认 + 告警群通知
5-15 min: 看大盘 (Airflow / Flink UI / Doris BE)
15-30 min: 决策 (回滚 / 重跑 / 切备)
30 min-2h: 执行 + 验证
2h-24h: 修复根因 + Postmortem
24h+: 知识库 + Action Item
```

### 11.3 常见 SOP

```
Kafka Consumer Lag 突增:
  1. kafka-lag-exporter 告警
  2. 看 Consumer Group 进度
  3. 扩 Consumer 实例 / 增分区
  4. 检查下游 (sink) 是否慢

Flink Job 失败 + Checkpoint 损坏:
  1. 从最近 savepoint 启动
  2. 修代码 + 测试
  3. 灰度上 (Application 模式)

Spark 任务 OOM:
  1. 看 driver / executor 日志
  2. 调内存 / 减少分区 / 倾斜处理
  3. 重跑

Doris BE down:
  1. 看 Compaction Score / 磁盘
  2. 重启 BE
  3. 修磁盘 / 加节点

数据质量异常 (字段为空):
  1. Soda check 告警
  2. 上游业务联系 (是否上线变更)
  3. 临时 mask / 默认值
  4. 修上游
```

## 十二、典型生产架构

### 12.1 互联网中型电商

```
Kafka KRaft 5 + Strimzi
Flink CDC (MySQL → Kafka → Paimon ODS)
Paimon DWD + DWS (流式)
Spark 历史回刷 + Iceberg
Doris 实时数仓 (Routine Load + Catalog)
ClickHouse 大宽表 (用户行为)
Trino 跨源 BI
DolphinScheduler 调度 + Soda 质量
DataHub 血缘
Superset BI
Backstage 数据 IDP
Vault + ESO 秘密
Prometheus + Grafana 监控
```

### 12.2 央企信创

```
Kafka / RocketMQ (国产)
Flink + Paimon (国产 Apache)
Doris / StarRocks (国产 MPP)
DolphinScheduler (国产 Apache)
SeaTunnel (国产 Apache)
DataHub / OpenMetadata
Apache Ranger 权限
国密 + 等保三级
FineBI / Quick BI (国产 BI)
信创 K8s + 鲲鹏 + openEuler
```

### 12.3 AI 公司

```
Kafka + Flink + Paimon
Doris (业务) + ClickHouse (日志/事件)
Feast 特征 (Online: Redis, Offline: Iceberg)
Milvus + pgvector 向量
LangChain SQL Agent (Text-to-SQL)
DataHub + Vanna AI (智能查询)
Argo Workflows 训练 pipeline
Spark + Iceberg 离线训练
MLflow + Harbor 模型注册
```

## 十三、Checklist（最佳实践）

```
架构:
☐ 决策树 (规模 / 实时 / 联邦)
☐ 引擎组合 (Kafka+Flink+Paimon+Doris+Trino+Superset)
☐ 5 层分层 + 命名规范

工程:
☐ 项目模板 (Backstage Golden Path)
☐ CI/CD (lint+test+build+Operator deploy)
☐ ServiceAccount + 最小 RBAC
☐ Vault + ESO 秘密
☐ Checkpoint / Savepoint 到 S3
☐ 镜像 Stargz 懒加载

调度:
☐ 任务规范 (命名/资源/重试/超时/幂等)
☐ Soda 质量后置
☐ DataHub 血缘
☐ on-call 告警 + Postmortem

治理:
☐ DataHub + Domain + Glossary
☐ 数据契约 (CI)
☐ Soda + Great Expectations
☐ Ranger 权限 + 国密

SLA:
☐ 新鲜度 / 可用性 / 延迟 / 质量 量化
☐ Pyrra / 自研 SLO

FinOps:
☐ cost-center label + Kubecost
☐ 小文件 / Snapshot / TTL 维护
☐ Spot / 动态分配
☐ MV 替代重复查询

安全:
☐ 数据分级 + PII 识别
☐ Ranger 列权限 + Row Policy
☐ 国密 + 等保 + 国测
☐ 审计 SIEM 180d
☐ 跨境评估

平台:
☐ Backstage 数据 IDP
☐ Golden Path 模板 (ETL/Flink/dbt/湖表/Doris)
☐ Self-service 申请
☐ 多租户隔离

国产化:
☐ Paimon + Doris + DolphinScheduler + SeaTunnel
☐ FineBI / Quick BI
☐ 信创 K8s + OS + CPU
☐ 国密合规

应急:
☐ P0-P3 分级
☐ 各引擎 runbook
☐ 季度演练
☐ Postmortem 模板
```

## 十四、推荐栈（最佳实践）

```
计算:        Spark 3.5 + Flink 1.19
湖仓:        Paimon ⭐ + Iceberg
实时数仓:    Doris ⭐ + StarRocks ⭐ + ClickHouse
即席:        Trino
消息:        Kafka KRaft + Strimzi + Schema Registry
CDC:        Flink CDC + Debezium
调度:        DolphinScheduler ⭐ / Airflow
采集:        SeaTunnel ⭐
存储:        MinIO / OSS / Ceph
治理:        DataHub ⭐ / OpenMetadata
质量:        Soda + Great Expectations
权限:        Apache Ranger / Polaris
特征:        Feast
监控:        kube-prometheus + 各 exporter
BI:          Superset + FineBI / Quick BI
平台:        Backstage 数据 IDP + 自研门户
国密合规:   Tongsuo + Ranger + 等保三级
```

> 📖 **核心判断**：大数据最佳实践 = **架构决策树 + 5 层分层规范 + 工程化基线(CI+RBAC+秘密) + 调度规范 + 数据治理(DataHub+契约+质量) + SLA 量化 + 数据安全(脱敏+国密+审计) + FinOps + 平台化(Backstage 数据 IDP+Golden Path) + 国产化路径 + Incident SOP**。能给企业画"Kafka → Flink CDC → Paimon → Doris/StarRocks → Trino → Superset/FineBI + DataHub 血缘 + Soda 质量 + Ranger 权限 + 国密合规 + Backstage IDP"完整数据中台、能 Q1 演练 + 数据契约 + DORA-like 度量 + 多租户 + 信创路径，就具备数据中台负责人能力。
