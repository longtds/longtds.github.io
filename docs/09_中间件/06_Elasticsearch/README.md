# Elasticsearch

> 全球部署最广的开源搜索引擎。**日志/全文检索/可观测/向量检索的事实标准**。基于 Apache Lucene，分布式、近实时、Schema-less。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2010 | Shay Banon 发布 Elasticsearch 0.4，基于 Lucene |
| 2012 | 成立 Elastic 公司 |
| 2015 | ELK Stack 概念走红（ES + Logstash + Kibana） |
| 2018 | ELK → **Elastic Stack**（加 Beats）|
| 2021.1 | **改用 SSPL + Elastic License**（双 license） |
| 2021.1 | AWS Fork **OpenSearch**（基于 ES 7.10）|
| 2023 | 8.x 加 ELSER 向量稀疏检索 |
| 2024 | **8.13+ 重启 Apache 2.0 双 license**，与 OpenSearch 和解 |
| 2024 | **9.0** 进入存算分离 / Stateless ES |
| 2025 | OpenSearch 3.0 与 ES 8.13+ 并行 |

> ⚠️ **2021 license 风波后 AWS Fork 出 OpenSearch**，国内云厂商也大多用 OpenSearch。2024 后 ES 重新 Apache 2.0，但 OpenSearch 已自成生态。

## 二、Elasticsearch 是什么

```
基于 Apache Lucene 的"分布式搜索/分析引擎"

定位:
  - 全文检索引擎（中文/英文/拼音）
  - 日志存储与分析
  - 实时数据分析（Aggregation）
  - 可观测平台后端（Logs/Metrics/APM）
  - 向量检索（kNN，8.x+）
  - 安全分析（SIEM）

核心模型:
  Document（JSON）  ←  类似 NoSQL
  Index（库）       ←  类似 Database
  Mapping（结构）   ←  类似 Schema
  Shard（分片）     ←  水平扩展
  Replica（副本）   ←  高可用
```

## 三、核心组件

```
Elastic Stack:
  Elasticsearch    存储 + 检索 + 计算
  Kibana          可视化 + 管理
  Logstash        数据收集/转换（重）
  Beats           轻量采集（Filebeat/Metricbeat/Packetbeat/Auditbeat）
  APM Server      链路追踪
  Fleet           Beats 集中管理
```

## 四、核心功能

```
1. 倒排索引（全文检索快得吓人）
2. 分布式分片 + 副本（PB 级数据）
3. 近实时（NRT，1s 内可查）
4. RESTful JSON API
5. 强大 Aggregation（GROUP BY / 直方图 / Percentile）
6. 文档级 ACL
7. 索引生命周期管理 ILM（Hot/Warm/Cold/Frozen）
8. Cross-Cluster Search / Replication
9. SQL 接口（部分）
10. Vector Search (kNN, ELSER, Sparse)  ← AI 时代
11. Machine Learning (异常检测)
12. Snapshots → S3/HDFS 备份
```

## 五、架构原理

```
┌─────── 集群 ───────────────┐
│ Master 节点(2-3)            │  ← 元数据管理
│ Data 节点(3+, 按角色拆分)   │  ← 数据存储
│ Ingest 节点                 │  ← 数据预处理
│ Coordinating 节点           │  ← 查询协调
│ ML 节点                     │  ← 机器学习
└─────────────┬──────────────┘
              ↓
┌─────── 索引 ──────────────┐
│ Index (logs-2026.06)      │
│   ├── Shard 0 (Primary)   │
│   │   ├── Lucene Segment  │
│   │   └── ...             │
│   ├── Shard 0 (Replica)   │
│   ├── Shard 1 (Primary)   │
│   └── ...                 │
└────────────────────────────┘
              ↓
┌─────── Lucene 倒排索引 ────┐
│ 词 → [doc_id, position]    │
│ "elastic" → [1, 3, 5, ...] │
└────────────────────────────┘
```

### 节点角色（关键）

```
master:        集群元数据（少量、稳定）
data_hot:      最新数据，SSD
data_warm:     温数据，HDD
data_cold:     冷数据，对象存储
data_frozen:   归档，可搜
ingest:        数据预处理（Pipeline）
coordinating:  纯协调（无数据）
ml:            机器学习/异常检测
```

## 六、使用场景

### ✅ 强烈推荐

| 场景 | 说明 |
|:---|:---|
| **日志中心** | ELK 经典组合 |
| **APM / 链路追踪** | Elastic APM / Skywalking 后端 |
| **全文检索** | 商品搜索、文档搜索 |
| **可观测平台** | Logs + Metrics + Traces 统一 |
| **安全 SIEM** | 威胁检测、审计 |
| **业务搜索** | 站内搜索、人物档案搜索 |
| **向量检索 + RAG** | 8.x kNN / ELSER |
| **实时分析** | 大日志 GROUP BY、TopN |

### ⚠️ 不推荐 / 慎选

- **OLAP 重分析**（亿级 GROUP BY 多维）→ ClickHouse / Doris 更适合
- **强一致事务** → 用关系型数据库
- **高更新频率（每条文档秒级变更）** → 用 PostgreSQL/MySQL
- **超低延迟点查** → 用 Redis / KV
- **冷数据归档** → 用对象存储 + Trino 直查

## 七、Elasticsearch vs 其他

| 维度 | ES | OpenSearch | ClickHouse | Doris | Loki | Solr |
|:---|:---|:---|:---|:---|:---|:---|
| 全文检索 | 极强 | 同 ES | 弱 | 弱 | 弱 | 强 |
| 聚合分析 | 强 | 同 | **极强** | 极强 | 弱 | 中 |
| 写吞吐 | 中 | 同 | **极高** | 高 | 高 | 中 |
| 存储成本 | 高 | 同 | 低 | 中 | **极低** | 高 |
| 适合规模 | TB-PB | TB-PB | TB-PB | TB | PB | TB |
| 学习成本 | 中 | 中 | 高 | 中 | 低 | 中 |
| 国内主流 | 高 | 中 | 高 | 极高 | 中 | 低 |
| 商业模式 | 双 license | Apache 2.0 | Apache 2.0 | Apache 2.0 | AGPL | Apache 2.0 |

## 八、最佳实践

### 8.1 集群规划

```
最小生产:
  3× Master-Eligible（独立小机器）
  3+ × Data 节点（SSD，每节点 < 30TB 数据，64GB 内存）
  2× Coordinating（高并发查询场景）

避免:
  ❌ 1 节点集群（脑裂、单点）
  ❌ Master 和 Data 同节点（大集群）
  ❌ JVM 堆 > 30GB（指针压缩失效）
```

### 8.2 索引设计

```
✅ 按时间滚动: logs-2026.06.22-000001（ILM 管理）
✅ Mapping 显式定义，关闭 dynamic 或设为 strict
✅ 不查的字段 index: false
✅ 不存原文 _source.excludes
✅ keyword vs text 想清楚（keyword 不分词、text 分词）
✅ doc_values: false 对仅检索字段
✅ 用 Index Template + Composable Template
✅ 单分片大小 20-50GB（不要超 100GB）
✅ 分片数 = 节点数 × N（不要过多）

❌ 一个索引塞所有数据
❌ 分片成百上千个
❌ 时间字段用 text
❌ 主键用长字符串
```

### 8.3 Mapping 示例

```json
{
  "settings": {
    "number_of_shards": 6,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "codec": "best_compression"
  },
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "@timestamp": {"type": "date"},
      "level": {"type": "keyword"},
      "service": {"type": "keyword"},
      "message": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart"
      },
      "user_id": {"type": "keyword"},
      "metadata": {"type": "object", "enabled": false},
      "embedding": {
        "type": "dense_vector",
        "dims": 1024,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}
```

### 8.4 ILM（生命周期管理）

```json
PUT _ilm/policy/logs-policy
{
  "policy": {
    "phases": {
      "hot":   { "actions": { "rollover": {"max_size":"50gb","max_age":"1d"} } },
      "warm":  { "min_age":"7d",  "actions": { "shrink": {"number_of_shards":1}, "forcemerge":{"max_num_segments":1} } },
      "cold":  { "min_age":"30d", "actions": { "searchable_snapshot": {"snapshot_repository":"s3"} } },
      "delete":{ "min_age":"90d", "actions": { "delete": {} } }
    }
  }
}
```

### 8.5 查询调优

```
✅ filter 用 bool.filter（不计算评分，命中缓存）
✅ 分页深度 < 10000，深分页用 search_after / PIT
✅ 聚合用 composite aggregation（替代 partitioning）
✅ 避免 wildcard 通配符开头查询
✅ 复杂查询用 query_string 慎重
✅ 用 explain API 看为啥不走索引
✅ slow log 监控
```

### 8.6 写入调优

```ini
# 大批量导入临时调整
index.refresh_interval = 30s       # 默认 1s
index.number_of_replicas = 0       # 导入完再开
index.translog.durability = async
index.translog.sync_interval = 30s

# bulk 批量 5-15MB
# 客户端并发 = CPU 核心数
```

### 8.7 JVM 与系统

```ini
# jvm.options
-Xms31g                 # 不超过 32G 避免指针压缩失效
-Xmx31g
-XX:+UseG1GC

# 系统
ulimit -n 65535         # 文件描述符
vm.max_map_count = 262144
vm.swappiness = 1       # 关闭 swap
bootstrap.memory_lock: true
```

### 8.8 中文分词

```
默认 standard 分词器对中文很差
   ↓
推荐: IK Analyzer (medcl/elasticsearch-analysis-ik)
  ik_max_word: 最细粒度，搜索召回好
  ik_smart:    粗粒度，准确性好

进阶: 同义词、拼音、HanLP、jieba
```

### 8.9 向量检索（8.x+）

```json
PUT my-index/_search
{
  "knn": {
    "field": "embedding",
    "query_vector": [0.1, 0.2, ...],
    "k": 10,
    "num_candidates": 100
  }
}

// 混合检索 (Hybrid Search)
{
  "query": { "match": { "title": "AI" } },
  "knn": { ... },
  "rank": { "rrf": {} }
}
```

## 九、运维命令速查

```bash
# 集群健康
GET _cluster/health
GET _cluster/health?level=indices

# 节点
GET _cat/nodes?v
GET _cat/master?v

# 索引
GET _cat/indices?v&s=index
GET _cat/shards?v

# 分片分配
GET _cluster/allocation/explain
POST _cluster/reroute?retry_failed=true

# 任务
GET _tasks?detailed&actions=*search*

# 慢查询
PUT logs-*/_settings
{ "index.search.slowlog.threshold.query.warn": "1s" }

# 索引模板
GET _index_template
PUT _index_template/logs-template { ... }

# 快照
PUT _snapshot/my-s3 {"type":"s3","settings":{...}}
PUT _snapshot/my-s3/snap-1?wait_for_completion=true
POST _snapshot/my-s3/snap-1/_restore
```

## 十、常见坑

| 坑 | 建议 |
|:---|:---|
| **分片过多（shard 爆炸）** | 单节点 < 600 分片 |
| **JVM > 32GB** | 永远 < 31GB |
| **未关 swap** | swappiness=1 + memory_lock |
| **未用 ILM** | 必上 |
| **dynamic mapping 爆字段** | 设 strict |
| **深分页慢** | 用 search_after |
| **单点 Master** | ≥ 3 个 Master-Eligible |
| **数据节点扩缩容慢** | 控制 max_concurrent_shard_recoveries |
| **写入 GC 卡顿** | 减小 bulk、调 refresh_interval |
| **磁盘水位** | 85%/90%/95% 三档要监控 |
| **跨集群 / 跨网延迟** | 用 CCR 或 CCS |
| **没有备份** | Snapshot 定期到 S3 |
| **8.x 默认开 TLS** | 证书要管理好 |

## 十一、生态与工具

| 工具 | 用途 |
|:---|:---|
| **Kibana / OpenSearch Dashboards** | 可视化 |
| **Filebeat / Metricbeat** | 数据采集 |
| **Logstash** | ETL 转换 |
| **Elastic APM / OTel** | 链路追踪 |
| **Cerebro** | 集群管理 GUI |
| **Curator**（已 EOL） | 索引管理（换 ILM） |
| **ESRally** | 性能压测 |
| **ECK** | K8s Operator（官方） |
| **OpenSearch Operator** | K8s Operator（开源） |

## 十二、Elasticsearch in K8s

```
推荐方案: Elastic Cloud on K8s (ECK)
   apiVersion: elasticsearch.k8s.elastic.co/v1
   kind: Elasticsearch
   spec:
     version: 8.13.0
     nodeSets:
       - name: master
         count: 3
       - name: data-hot
         count: 6
         config:
           node.roles: [data_hot, ingest]
       - name: data-cold
         count: 3
         config:
           node.roles: [data_cold]

OpenSearch:
   OpenSearch Operator + StatefulSet
```

## 十三、监控指标（必看）

```
集群:
  cluster.status (green/yellow/red)
  unassigned_shards
  pending_tasks

节点:
  jvm.mem.heap_used_percent
  cpu.percent
  fs.disk.used_percent
  thread_pool.{write,search}.queue / rejected

索引:
  indexing.rate
  search.rate / latency
  segments.count / memory_in_bytes

慢日志:
  slow log / 阈值告警
```

**工具栈**：Metricbeat + Elasticsearch + Kibana，或 Prometheus + elasticsearch_exporter。

## 十四、国产替代

| 产品 | 厂商 | 说明 |
|:---|:---|:---|
| **easysearch** | INFINI Labs (极限科技) | ES 国产分支 |
| **OpenSearch** | AWS / 阿里云 | 兼容 ES 7.10 API |
| **TanLog** | 腾讯云 | 日志专用 |
| **SLS** | 阿里云 | 日志/分析云服务 |
| **Loki** | Grafana | 标签轻量日志（云原生） |
| **Manticore** | 开源 | 替代 Sphinx |

## 十五、ES vs OpenSearch 选型

```
选 ES 8.x:
  - 需要最新功能（向量、ML、ELSER）
  - 商业 SLA 看 Elastic 公司
  - 现有 ELK 老集群升级

选 OpenSearch:
  - 完全 Apache 2.0 license 要求
  - AWS 生态（Amazon OpenSearch Service）
  - 国内云厂商托管首选
  - 与 ES 7.10 兼容性极高
```

## 十六、学习路径

```
入门:
  1. 单机起 ES + Kibana
  2. REST API CRUD
  3. Mapping 与分词
  4. 基本查询 (match/term/bool/range)

进阶:
  5. Aggregation 五大类
  6. 多节点集群 + 副本/分片
  7. ILM + 索引模板
  8. Filebeat → ES → Kibana 全链路日志

高阶:
  9. JVM + 系统调优
  10. 慢日志 + 性能分析
  11. 快照 + 跨集群复制
  12. 向量检索 / RAG
  13. ECK / K8s 部署
  14. 安全（TLS + 角色）
```

> 📖 **核心判断**：日志/搜索/可观测的事实标准。**新建项目 8.13+ 或 OpenSearch 2.x 都行**，选哪个看你云厂商、license 偏好和团队熟悉度。重 OLAP 分析用 ClickHouse，超大日志用 Loki，向量优先 + 全文混合用 ES/OpenSearch。
