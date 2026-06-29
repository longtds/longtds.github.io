# 10. 大数据

> 大数据 = 数据中台。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦 Hadoop/Spark/Flink + Iceberg/Paimon 湖仓 + Doris/StarRocks/ClickHouse 实时数仓 + Trino 即席 + Airflow/DolphinScheduler 调度 + SeaTunnel/Flink CDC 集成 + dbt/Soda/DataHub DataOps + Feast 特征 + Data Mesh/Contracts 治理 + AI Native(Text-to-SQL/RAG) + 国密合规 11 大主线。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入职 1 年内 | Lambda/Kappa/Lakehouse 架构 / HDFS 基础 / Hive / Spark PySpark / Flink SQL / Airflow / DolphinScheduler / DataX / SeaTunnel / 数据分层 + 维度建模 + 20 题 |
| [02_进阶](02_进阶/README.md) | 独立维护中型数据平台 | Spark Operator + Volcano + Celeborn / Flink K8s Operator + Application Mode + Savepoint / Paimon+Iceberg 湖仓 / Doris/StarRocks 实时数仓 / Flink CDC / Trino 即席 / DolphinScheduler 多租户 / DataHub 血缘 / Soda+Great Expectations 质量 / 监控告警 |
| [03_高级](03_高级/README.md) | 数据架构师 / 平台负责人 | Lakehouse 一体化 / Data Mesh / 流批一体深度(Paimon+Flink) / 内核调优(AQE+Incremental) / Trino+StarRocks 联邦 / Feast 特征 / DataHub+契约+质量 / AI Native(Text-to-SQL/RAG) / 多云+安全+国密+国产化 |
| [04_最佳实践](04_最佳实践/README.md) | 团队负责人 | 架构决策树 / 5 层分层规范 / 工程化基线(CI+RBAC+秘密) / 调度规范 / 数据治理体系 / SLA 量化 / 数据安全合规 / FinOps / 平台化(Backstage 数据 IDP+Golden Path) / Incident SOP / 3 种生产架构 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | Lakehouse 替代 / Iceberg/Paimon 主导 / Doris 爆发 / Data Mesh 落地 / DataOps 普及 / AI Native 数据栈 / Data Contracts / 多云数据 / 国密合规 / 国产开源 70% + 20 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
 └─ 01_基础: Spark/Flink/调度/采集 + 数据分层 + 20 题

进阶（3-12 月）
 └─ 02_进阶: K8s Operator + Paimon/Iceberg + Doris + Flink CDC + DataHub + Soda

高级（1-2 年）
 └─ 03_高级: Lakehouse + Data Mesh + 流批一体 + 内核调优 + 联邦 + Feast + AI Native + 国密

工程化（2-3 年）
 └─ 04_最佳实践: 决策树 + 工程基线 + 治理 + SLA + FinOps + Backstage IDP + 国产化 + 应急

展望（持续）
 └─ 99_发展与展望: Lakehouse + Paimon + Doris + Data Mesh + DataOps + AI Native + 国密 + 国产开源
```

## 核心判断

```
心法:
 1. 别再 Hadoop — Lakehouse (对象存储 + Iceberg/Paimon) 取代
 2. 别再 Lambda — 流批一体 (Paimon + Flink) 一套代码
 3. 实时数仓 — Doris/StarRocks 国产主导
 4. 多源 ETL — Flink CDC + SeaTunnel 是国产 Apache 黄金组合
 5. 治理 — DataHub + 契约 + Soda + Ranger 一栈
 6. Feast — 特征工程标配 (AI 必修)
 7. AI Native — Text-to-SQL 业务实用 (2026-2027)
 8. Data Mesh — 大企业组织变革
 9. DataOps — dbt 普及 + DORA 度量
 10. 国密 + 等保 + 信创 — 央企硬要求 (Paimon/Doris/DolphinScheduler 必修)

红线:
 还在堆 HDFS / Cloudera (老死)
 Lambda 双套维护
 数据无契约 / 无血缘 / 无质量
 单调度无重试无幂等
 Spark 无 AQE / 无动态分配
 Flink 无 Checkpoint / 无 Operator
 Doris 无 Routine Load / 无 Catalog
 数据脱敏不做 / 审计 < 180d
 跨地无灾备演练
 不接 DataHub / Backstage 平台
```

## 相关章节

- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 Spark/Flink Operator + Volcano + Karmada
- 配合 [08_DevOps](../08_DevOps/index.md) 看 GitOps + dbt CI/CD + DataOps
- 配合 [09_中间件](../09_中间件/index.md) 看 Kafka/Pulsar + Doris/ClickHouse + pgvector + TDengine
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 Feast + Milvus + LangChain SQL Agent
- 配合 [12_AIOps](../12_AIOps/index.md) 看 数据质量异常检测 + Soda + Prometheus
- 配合 [13_认证与SSO](../13_认证与SSO/index.md) 看 DataHub OIDC + Ranger LDAP
- 配合 [14_安全](../14_安全/index.md) 看 Ranger + Polaris + 字段加密 + 国密
- 配合 [15_渗透测试](../15_渗透测试/index.md) 看 Hive/Spark/Hadoop 渗透 + JDBC 注入
- 配合 [16_故障排查](../16_故障排查/index.md) 看 Spark OOM / Flink 反压 / Doris BE 高 Compaction
