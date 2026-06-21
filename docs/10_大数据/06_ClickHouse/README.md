# ClickHouse（大数据场景）

## 大数据场景下的列式存储

ClickHouse 在大数据场景中作为 OLAP 引擎，替代 Hive/ES 的部分场景。

## 适用场景

- 用户行为分析
- 实时指标聚合
- 日志分析（替代 ES）
- 监控指标存储（替代 Prometheus 长期存储）

## 替代方案对比

| 场景 | 传统方案 | ClickHouse 方案 | 优势 |
|:---|:---|:---|:---|
| 用户 PV/UV | Hive（分钟级） | ClickHouse（秒级） | 实时 |
| 日志检索 | ES（高存储成本） | ClickHouse（1/10 成本） | 成本 |
| 聚合报表 | Presto | ClickHouse（物化视图） | 性能 |
