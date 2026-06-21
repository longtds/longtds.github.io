# HBase

## 概述

HBase 是分布式的列式 NoSQL 数据库，适合实时随机读写海量数据。

## RowKey 设计

RowKey 设计是 HBase 最关键的设计决策：

| 原则 | 说明 | 示例 |
|:---|:---|:---|
| 散列性 | 避免 Region 热点 | `user_id_hash + timestamp` |
| 长度 | 越短越好 | 避免长字符串 |
| 相关性 | 相关数据连续存储 | 同一用户的记录前缀相同 |

```bash
# HBase Shell
create 'users', 'cf1', 'cf2'
put 'users', 'row1', 'cf1:name', 'Alice'
get 'users', 'row1'
scan 'users', {LIMIT => 10}
delete 'users', 'row1', 'cf1:name'
count 'users'
```

## 架构组件

| 组件 | 作用 |
|:---|:---|
| HMaster | 管理 Region 分配和负载均衡 |
| RegionServer | 处理数据读写请求 |
| Region | 表的分片单元 |
| MemStore | 内存缓存 |
| HFile | 磁盘存储文件 |
| WAL | 预写日志，故障恢复 |
