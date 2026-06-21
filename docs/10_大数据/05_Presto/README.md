# Presto / Trino

## 概述

Presto（现 Trino）是分布式 SQL 查询引擎，支持联邦查询多个数据源。

## 联邦查询

```sql
-- 同时查询 MySQL 和 Hive 的数据
SELECT
  u.name,
  o.order_amount
FROM mysql.company.users u
JOIN hive.analytics.orders o
  ON u.id = o.user_id
WHERE o.order_date > date '2026-01-01';
```

## Presto vs Spark SQL

| 维度 | Presto/Trino | Spark SQL |
|:---|:---|:---|
| 设计目标 | 低延迟交互式查询 | 大规模批处理 |
| 引擎 | 专有查询引擎 | Spark 执行引擎 |
| 连接器 | 30+ 数据源 | JDBC 为主 |
| 缓存 | 无内置缓存 | DataFrame cache |
| 适用场景 | BI/Ad-hoc 查询 | ETL/批处理 |
