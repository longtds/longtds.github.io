# PostgreSQL（大数据场景）

## Greenplum

Greenplum 是基于 PostgreSQL 的大数据 MPP 数据库。

## PostgreSQL vs ClickHouse

| 维度 | PostgreSQL | ClickHouse |
|:---|:---|:---|
| 类型 | OLTP + OLAP | OLAP |
| 存储 | 行式 | 列式 |
| 事务 | ACID 完整 | 有限 |
| 并发 | 高 | 中 |
| 聚合查询 | 较慢 | 极快 |
| 适用场景 | 业务系统 | 分析查询 |
