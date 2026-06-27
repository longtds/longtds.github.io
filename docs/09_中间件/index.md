# 09. 中间件

> 中间件 = 数据基础设施。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦关系型(MySQL/PG/TiDB/OceanBase) + 缓存(Redis/Tair/Dragonfly) + 消息(Kafka/RocketMQ/Pulsar) + 注册配置(Nacos) + 搜索(ES/OpenSearch) + OLAP(ClickHouse/Doris) + 反代网关(Nginx/APISIX/Higress) + 向量(pgvector/Milvus) + 时序(TDengine/IoTDB) + 数据湖(Iceberg/Paimon) + DBaaS(KubeBlocks) 十一大主线。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入职 1 年内 | 中间件全景 / MySQL/PG/Redis/Kafka/Nacos/ES/CK/Nginx 单机部署 + 必会命令 + 选型基础 + 20 题 |
| [02_进阶](02_进阶/README.md) | 独立运维生产 | MySQL MGR+InnoDB Cluster / PG Patroni / Redis Sentinel+Cluster / Kafka KRaft / RocketMQ 集群 / Nacos 集群 / ES 分角色+ILM / CK Replicated+Keeper / Nginx Keepalived / 分库分表 / KubeBlocks+Operator / 备份+监控+演练 |
| [03_高级](03_高级/README.md) | DBA / 平台架构师 | TiDB+OceanBase NewSQL / 内核(MVCC/Raft/2PC) / 海量治理(分库分表+冷热+数据湖) / Kafka 千万 TPS / Pulsar 存算分离 / Redis 替代生态 / 多模(图/向量/时序) / pgvector+Milvus / TDengine+IoTDB / Iceberg+Paimon / KubeBlocks 平台化 / 跨地多活 / 国密合规 |
| [04_最佳实践](04_最佳实践/README.md) | 团队负责人 | 选型决策树 / 容量规划 / HA 最小副本 / Top 10 调优 / 监控告警 / 三层备份 / 安全合规(国密/等保) / 多租户 / KubeBlocks 容器化 / 国产化路径 / 应急 SOP / 4 种生产架构 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | NewSQL 替代 Oracle / 数据库容器化 / 向量爆发 / IoT 时序爆发 / 存算分离 / 数据湖统一 / AI Native DB(Text-to-SQL) / Serverless DB / 国密合规 / 国产开源 70% + 20 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
  └─ 01_基础: MySQL/PG/Redis/Kafka/Nacos/ES/CK/Nginx 单机跑通 + 必会命令 + 20 题

进阶（3-12 月）
  └─ 02_进阶: MGR/Patroni/Cluster/Strimzi/Replicated/Keepalived 集群 + KubeBlocks 容器化

高级（1-2 年）
  └─ 03_高级: TiDB/OceanBase + 内核 + 千万 TPS Kafka + Pulsar + 向量 + 时序 + 数据湖 + 跨地多活

工程化（2-3 年）
  └─ 04_最佳实践: 选型 + 容量 + HA + 调优 + 备份 + 监控 + 合规 + 多租户 + DBaaS + 国产化

展望（持续）
  └─ 99_发展与展望: NewSQL + 容器化 + AI Native + Serverless + 数据湖 + 国密 + 国产开源
```

## 核心判断

```
心法:
  1. 中间件无银弹 — 选型决策树驱动 (业务量+一致性+模型)
  2. 强一致 → MySQL/PG/TiDB/OceanBase; 最终一致 → Cassandra/Mongo/Kafka
  3. AI 时代向量是必修 (pgvector 业务库 / Milvus 大规模 双栈)
  4. IoT 时代时序是必修 (TDengine / IoTDB / VictoriaMetrics)
  5. 容器化趋势 — KubeBlocks 一站式 30+ DB
  6. 存算分离是未来 (Pulsar / RocketMQ 5.0 / 数据湖 / Serverless DB)
  7. Iceberg / Paimon 是数据湖统一格式
  8. 国密 + 等保 + 信创 是央企硬要求 (TiDB/OceanBase/GaussDB/达梦 必修)
  9. 备份与演练 — 三层备份 + 季度恢复 + RTO/RPO 量化
  10. 监控告警 — exporter 全覆盖 + 关键告警 + on-call 升级

红线:
  ❌ Oracle 新建系统 (国央企)
  ❌ 单机生产数据库
  ❌ 无备份 / 不演练
  ❌ 跨库 JOIN / 强耦合
  ❌ 大事务跨分片
  ❌ Kafka unclean=true
  ❌ Redis 单点 + 无持久化
  ❌ Nginx 单点
  ❌ Nacos 共享 DB 单点
  ❌ 日志 / 审计 < 180 天
  ❌ 不接 SIEM / 监控
  ❌ 跨地无切换演练
```

## 相关章节

- 配合 [06_Docker](../06_Docker/index.md) / [07_Kubernetes](../07_Kubernetes/index.md) 看 StatefulSet / Operator / KubeBlocks
- 配合 [08_DevOps](../08_DevOps/index.md) 看 GitOps + Argo + 数据库版本化
- 配合 [10_大数据](../10_大数据/index.md) 看 Spark/Flink + Iceberg/Paimon + Kafka/Pulsar
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 pgvector + Milvus + Feast 特征
- 配合 [12_AIOps](../12_AIOps/index.md) 看 Prometheus + VictoriaMetrics + 异常检测
- 配合 [13_认证与SSO](../13_认证与SSO/index.md) 看 DB OIDC + Vault Database Secrets
- 配合 [14_安全](../14_安全/index.md) 看 数据脱敏 + 国密 + 加密机
- 配合 [15_渗透测试](../15_渗透测试/index.md) 看 SQL 注入 + Redis 未授权 + DB 漏扫
- 配合 [16_故障排查](../16_故障排查/index.md) 看 DB 慢查询 / 锁等待 / 复制断裂 / 大 key
