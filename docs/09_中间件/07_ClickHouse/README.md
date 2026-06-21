# ClickHouse

## 概述

ClickHouse 是开源的列式 OLAP 数据库，适用于实时分析场景。

## 部署

```bash
# ClickHouse Operator
kubectl apply -f https://raw.githubusercontent.com/Altinity/clickhouse-operator/master/deploy/operator/clickhouse-operator-install.yaml

# ClickHouseInstallation 示例
apiVersion: "clickhouse.altinity.com/v1"
kind: "ClickHouseInstallation"
metadata:
  name: clickhouse
spec:
  configuration:
    clusters:
      - name: default
        layout:
          shards:
            - replicas:
              - name: replica1
                volumeClaimTemplate:
                  resources:
                    requests:
                      storage: 500Gi
```

## 表引擎

| 引擎 | 场景 | 说明 |
|:---|:---|:---|
| MergeTree | 通用 | 基础引擎，支持分区 |
| ReplacingMergeTree | 去重 | 相同排序键去重 |
| SummingMergeTree | 聚合 | 预聚合 |
| Distributed | 分布式 | 跨节点查询 |

## 优化

```sql
-- 分区设计
CREATE TABLE events (
  event_date Date,
  event_type String,
  data String
) ENGINE = MergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_type, event_date);

-- 物化视图
CREATE MATERIALIZED VIEW events_daily
ENGINE = SummingMergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_type, event_date)
AS SELECT
  event_date,
  event_type,
  count() as cnt
FROM events
GROUP BY event_date, event_type;
```
