# 10_大数据 · 概述

> 大数据 = 海量 + 多样 + 实时。从 Hadoop 到湖仓一体，从批处理到流批一体，技术不断进化。

## 一、大数据发展简史

| 时期 | 阶段 | 代表 |
|:---|:---:|:---|
| 2004-2006 | 论文奠基 | Google GFS/MapReduce/BigTable |
| 2006-2012 | Hadoop 时代 | HDFS/MR/Hive/HBase |
| 2012-2018 | 内存计算 | Spark 取代 MR、Flink 流处理 |
| 2018-2022 | 数据湖兴起 | Iceberg/Hudi/Delta |
| 2022-至今 | 湖仓一体 | Snowflake/Databricks 引领 |

## 二、大数据 = 三个 V

| 维度 | 挑战 | 解决 |
|:---|:---|:---|
| **Volume**（量） | PB 级 | 分布式存储 |
| **Velocity**（速） | 实时流 | Flink/Spark Streaming |
| **Variety**（杂） | 结构/半结构/非结构 | 数据湖 + Schema-on-read |

## 三、整体技术栈

```
┌─────────── 应用层 ───────────┐
│  BI / 报表 / AI 训练 / 可视化  │
├─────────── 服务层 ───────────┤
│  Trino/Presto/Doris/ClickHouse│
│  (查询引擎)                  │
├─────────── 计算层 ───────────┤
│  Spark / Flink / Hive        │
├─────────── 存储层 ───────────┤
│  Iceberg/Hudi/Delta (表格式)  │
│  HDFS / S3 / OSS  (对象存储)  │
├─────────── 治理层 ───────────┤
│  Atlas / DataHub / Marquez   │
└─────────────────────────────┘
```

## 四、批处理 vs 流处理

| 维度 | 批 | 流 |
|:---|:---|:---|
| 延迟 | 小时 | 秒级 |
| 数据量 | 全量历史 | 增量 |
| 引擎 | Hive/Spark | Flink/Spark Streaming |
| 用途 | 报表、ETL、训练 | 监控、实时风控、推荐 |
| 复杂度 | 简单 | 高（窗口、状态、Exactly Once） |

**趋势**：流批一体（同一份 SQL 跑两种模式）。

## 五、数据湖 vs 数据仓库 vs 湖仓一体

| 概念 | 存储 | 计算 | Schema | 代表 |
|:---|:---|:---|:---|:---|
| 数据仓库 | 专用 | 紧耦合 | Write 时 | Teradata、Redshift |
| 数据湖 | 对象存储 | 解耦 | Read 时 | HDFS + Hive |
| 湖仓一体 | 对象存储 | 解耦 + ACID | 表格式管理 | Databricks、Iceberg |

```
2000s: 数据仓库（贵、僵化）
2015s: 数据湖（灵活但治理难）
2020s: 湖仓一体（兼具二者优点）
```

## 六、本章覆盖

| 子章节 | 内容 |
|:---|:---|
| **00_技术演进** | 整体趋势、生态变迁 |
| **01_Hadoop** | HDFS + YARN + MR |
| **02_Hive** | SQL on Hadoop |
| **03_HBase** | KV 列族数据库 |
| **04_Spark** | 内存计算、SparkSQL、Spark on K8s |
| **05_Presto** | MPP 查询引擎 |
| **06_ClickHouse** | OLAP 列存 |
| **07_PostgreSQL** | 关系型 + 数据集成 |
| **08_数据湖与存储** | Iceberg/Hudi/Delta + S3 + Paimon |

## 七、学习路径

1. **基础**：理解 HDFS + MR 编程模型
2. **进阶**：精通 Spark + Hive
3. **实时**：Flink + Kafka
4. **现代**：Iceberg + Trino + 湖仓架构

> 📖 大数据正在被 AI 包裹——数据是 AI 的燃料，存储和处理框架必须为 AI 优化。
