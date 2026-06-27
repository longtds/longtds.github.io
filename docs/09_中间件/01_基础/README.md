# 基础

> 中间件基础 = **关系型 DB(MySQL/PostgreSQL) + 缓存(Redis) + 消息队列(Kafka/RocketMQ) + 注册中心(Nacos) + 搜索(Elasticsearch) + 列存(ClickHouse) + 网关(Nginx)** 八大类的入门。每类只讲核心概念 + 单机部署 + 必会命令 + 选型对照。

## 一、中间件全景图

```
关系型 DB:    MySQL / PostgreSQL / Oracle / SQL Server / 国产 OceanBase/TiDB/GaussDB
NoSQL DB:    MongoDB / Cassandra / HBase / 国产 OpenGauss
KV/缓存:     Redis / Memcached / Tair / 国产 KeyDB
搜索:        Elasticsearch / OpenSearch / Meilisearch / 国产 Manticore
列存/OLAP:   ClickHouse / Druid / Doris / StarRocks / 国产 ⭐
图 DB:       Neo4j / Nebula Graph / JanusGraph / 国产 NebulaGraph ⭐
时序 DB:     InfluxDB / TimescaleDB / TDengine / IoTDB / 国产 TDengine ⭐ IoTDB ⭐
消息队列:    Kafka / RocketMQ / RabbitMQ / Pulsar / 国产 RocketMQ ⭐ Pulsar (StreamNative)
注册中心:    Nacos ⭐ / Consul / Eureka / Zookeeper
配置中心:    Nacos ⭐ / Apollo / Disconf
API 网关:    Nginx / Higress / APISIX / Kong / 国产 Higress/APISIX ⭐
反代:        Nginx ⭐ / HAProxy / Envoy
对象存储:    MinIO / Ceph RGW / 阿里 OSS / 华为 OBS / 腾讯 COS / 国产 MinIO ⭐
分布式存储:  Ceph / GlusterFS / JuiceFS / 国产 ⭐
流处理:      Flink / Spark Streaming / Kafka Streams / Pulsar Functions
ETL:        DataX / SeaTunnel / Airflow / DolphinScheduler / 国产 SeaTunnel/DolphinScheduler ⭐
```

## 二、MySQL 入门

### 2.1 单机部署

```bash
# Docker
docker run -d --name mysql -e MYSQL_ROOT_PASSWORD=root123 \
  -p 3306:3306 -v mysql-data:/var/lib/mysql \
  mysql:8.0 --default-authentication-plugin=mysql_native_password

# RPM
yum install mysql-server -y
systemctl enable --now mysqld
grep 'temporary password' /var/log/mysqld.log
mysql_secure_installation
```

### 2.2 必会命令

```sql
-- 库
CREATE DATABASE app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
DROP DATABASE app;

-- 用户
CREATE USER 'app'@'%' IDENTIFIED BY 'AppPass123!';
GRANT ALL PRIVILEGES ON app.* TO 'app'@'%';
FLUSH PRIVILEGES;

-- 表
CREATE TABLE users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  email VARCHAR(128) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 备份
mysqldump -uroot -p --single-transaction --routines --triggers app > app.sql
mysql -uroot -p app < app.sql
```

### 2.3 关键配置

```ini
# /etc/my.cnf
[mysqld]
bind-address = 0.0.0.0
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
default-time-zone = '+08:00'

innodb_buffer_pool_size = 4G   # 物理内存 50-70%
innodb_log_file_size = 1G
innodb_flush_log_at_trx_commit = 1
sync_binlog = 1
binlog_format = ROW
expire_logs_days = 7
max_connections = 1000
slow_query_log = ON
long_query_time = 1
```

## 三、PostgreSQL 入门

### 3.1 单机部署

```bash
docker run -d --name pg -e POSTGRES_PASSWORD=pg123 \
  -p 5432:5432 -v pg-data:/var/lib/postgresql/data \
  postgres:16

# RPM
dnf install postgresql-server postgresql-contrib -y
postgresql-setup --initdb
systemctl enable --now postgresql
```

### 3.2 必会命令

```sql
-- 角色 + 库
CREATE ROLE app LOGIN PASSWORD 'AppPass123!';
CREATE DATABASE app OWNER app ENCODING 'UTF8' LC_COLLATE 'zh_CN.UTF-8' LC_CTYPE 'zh_CN.UTF-8' TEMPLATE template0;
GRANT ALL ON DATABASE app TO app;

-- 连接
psql -h 127.0.0.1 -U app -d app

-- 表
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  email VARCHAR(128) UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_email ON users (email);

-- 扩展
CREATE EXTENSION pg_stat_statements;
CREATE EXTENSION pgcrypto;
CREATE EXTENSION postgis;     -- 地理
CREATE EXTENSION vector;      -- pgvector AI 向量
```

### 3.3 PG vs MySQL 一句话

```
MySQL:   互联网通用、生态全、单机/主从简单
PG:      标准 SQL、复杂查询强、扩展(GIS/向量/JSONB) ⭐ AI 时代首选
```

## 四、Redis 入门

### 4.1 单机部署

```bash
docker run -d --name redis -p 6379:6379 \
  -v redis-data:/data redis:7-alpine \
  redis-server --requirepass redis123 --appendonly yes
```

### 4.2 必会命令

```bash
redis-cli -h 127.0.0.1 -p 6379 -a redis123

# String
SET key value EX 60
GET key
INCR counter

# List
LPUSH queue task1 task2
RPOP queue

# Hash
HSET user:1 name Alice age 30
HGETALL user:1

# Set
SADD tag:tech k8s docker
SISMEMBER tag:tech k8s

# Sorted Set
ZADD rank 100 Alice 80 Bob
ZRANGE rank 0 -1 WITHSCORES

# Stream (5.0+)
XADD events * type login user Alice
XREAD COUNT 10 STREAMS events 0

# Pub/Sub
SUBSCRIBE channel
PUBLISH channel "msg"

# 持久化
BGSAVE              # RDB 快照
BGREWRITEAOF        # AOF 重写

# 监控
INFO
MONITOR
SLOWLOG GET 10
```

### 4.3 关键配置

```ini
# redis.conf
bind 0.0.0.0
protected-mode no
requirepass YourStrong@Pass

maxmemory 4gb
maxmemory-policy allkeys-lru

appendonly yes
appendfsync everysec

save 900 1
save 300 10
save 60 10000
```

## 五、Kafka 入门

### 5.1 单机部署（KRaft 模式）

```bash
docker run -d --name kafka -p 9092:9092 \
  -e KAFKA_NODE_ID=1 \
  -e KAFKA_PROCESS_ROLES=broker,controller \
  -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT \
  -e CLUSTER_ID=q1Sh-9_ISia_zwGINzRvyQ \
  apache/kafka:3.7.0
```

### 5.2 必会命令

```bash
# Topic
kafka-topics.sh --bootstrap-server localhost:9092 --create --topic test --partitions 3 --replication-factor 1
kafka-topics.sh --bootstrap-server localhost:9092 --list
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic test

# Producer
kafka-console-producer.sh --bootstrap-server localhost:9092 --topic test

# Consumer
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test --from-beginning --group g1

# Consumer Group
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group g1
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --reset-offsets --group g1 --topic test --to-earliest --execute
```

### 5.3 Kafka vs RocketMQ vs RabbitMQ

```
Kafka:        高吞吐 (100w+ msg/s)、日志/流处理、事件源 ⭐
RocketMQ:     国产、阿里、事务 + 顺序、电商订单首选 ⭐
RabbitMQ:     灵活路由 (Exchange/Routing Key)、企业集成
Pulsar:       存算分离、租户隔离、强一致、长留存
```

## 六、Nacos 入门（注册+配置中心）

### 6.1 单机部署

```bash
docker run -d --name nacos -p 8848:8848 -p 9848:9848 \
  -e MODE=standalone -e PREFER_HOST_MODE=hostname \
  nacos/nacos-server:v2.3.0
```

### 6.2 注册中心

```yaml
# Spring Boot 应用
spring:
  application: { name: order-service }
  cloud:
    nacos:
      discovery:
        server-addr: nacos.example.com:8848
        namespace: prod
        group: DEFAULT_GROUP
```

### 6.3 配置中心

```yaml
spring:
  cloud:
    nacos:
      config:
        server-addr: nacos.example.com:8848
        namespace: prod
        group: DEFAULT_GROUP
        file-extension: yaml
        refresh-enabled: true
```

```bash
# 创建配置 (Web UI 或 API)
curl -X POST "http://localhost:8848/nacos/v1/cs/configs" \
  -d "dataId=order-service-prod.yaml&group=DEFAULT_GROUP&tenant=prod&content=server.port=8080"
```

## 七、Elasticsearch 入门

### 7.1 单机部署

```bash
docker run -d --name es \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms2g -Xmx2g" \
  -e "xpack.security.enabled=false" \
  -p 9200:9200 -p 9300:9300 \
  elasticsearch:8.13.0
```

### 7.2 必会 API

```bash
# 健康
curl localhost:9200/_cluster/health?pretty
curl localhost:9200/_cat/indices?v
curl localhost:9200/_cat/nodes?v
curl localhost:9200/_cat/shards?v

# 创建索引
curl -X PUT localhost:9200/orders -H 'Content-Type: application/json' -d '{
  "settings": { "number_of_shards": 3, "number_of_replicas": 1 },
  "mappings": {
    "properties": {
      "user":   { "type": "keyword" },
      "amount": { "type": "float" },
      "ts":     { "type": "date" }
    }
  }
}'

# 写入
curl -X POST localhost:9200/orders/_doc -H 'Content-Type: application/json' -d '{
  "user": "alice", "amount": 100.5, "ts": "2026-06-27T10:00:00Z"
}'

# 查询
curl -X POST localhost:9200/orders/_search -H 'Content-Type: application/json' -d '{
  "query": { "match": { "user": "alice" } },
  "sort": [{ "ts": "desc" }],
  "size": 10
}'
```

## 八、ClickHouse 入门

### 8.1 单机部署

```bash
docker run -d --name ck \
  -p 8123:8123 -p 9000:9000 \
  -v ck-data:/var/lib/clickhouse \
  --ulimit nofile=262144:262144 \
  clickhouse/clickhouse-server:24.3
```

### 8.2 必会 SQL

```sql
-- 客户端
clickhouse-client --host 127.0.0.1

CREATE DATABASE app;
USE app;

CREATE TABLE events (
  ts        DateTime,
  user      String,
  action    LowCardinality(String),
  amount    Float64,
  ip        IPv4
) ENGINE = MergeTree
ORDER BY (ts, user)
PARTITION BY toYYYYMM(ts)
TTL ts + INTERVAL 90 DAY;

INSERT INTO events VALUES (now(), 'alice', 'login', 0, '1.2.3.4');

SELECT
  toStartOfHour(ts) AS hour,
  action,
  count() AS cnt,
  uniq(user) AS uv
FROM events
WHERE ts >= now() - INTERVAL 1 DAY
GROUP BY hour, action
ORDER BY hour DESC;
```

## 九、Nginx 入门

### 9.1 单机部署

```bash
docker run -d --name nginx -p 80:80 -p 443:443 \
  -v /data/nginx/conf.d:/etc/nginx/conf.d \
  -v /data/nginx/certs:/etc/nginx/certs \
  nginx:1.27-alpine
```

### 9.2 反代 + 负载

```nginx
upstream backend {
  least_conn;
  server 10.0.0.1:8080 max_fails=3 fail_timeout=10s;
  server 10.0.0.2:8080 max_fails=3 fail_timeout=10s;
  keepalive 64;
}

server {
  listen 443 ssl http2;
  server_name api.example.com;
  ssl_certificate     /etc/nginx/certs/api.example.com.pem;
  ssl_certificate_key /etc/nginx/certs/api.example.com.key;
  ssl_protocols TLSv1.2 TLSv1.3;

  client_max_body_size 50m;
  gzip on; gzip_types text/plain application/json;

  location / {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_connect_timeout 5s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
  }
}
```

### 9.3 常用命令

```bash
nginx -t                     # 检查
nginx -s reload              # 重载
nginx -s stop                # 停
tail -f /var/log/nginx/access.log
```

## 十、选型方法论（基础版）

```
关系型 DB:
  互联网通用     MySQL
  复杂查询/GIS/向量  PostgreSQL ⭐
  金融超大     OceanBase / TiDB / GaussDB

NoSQL:
  KV / 缓存     Redis
  文档         MongoDB
  列存大宽表    HBase / Cassandra

搜索:
  通用全文     Elasticsearch / OpenSearch
  小型快搜      Meilisearch / Manticore

OLAP / 列存:
  日志/事件     ClickHouse ⭐
  实时数仓      Doris / StarRocks
  历史长存      ClickHouse / 数据湖

消息:
  超高吞吐     Kafka
  电商订单/事务 RocketMQ
  企业集成     RabbitMQ
  存算分离     Pulsar

注册/配置:
  Spring Cloud Alibaba   Nacos ⭐
  服务网格              Istio / Cilium SM
  通用                  Consul

网关:
  Nginx 传统    Nginx
  云原生        APISIX / Higress / Kong
  Service Mesh  Istio Gateway
```

## 十一、入门 20 题

```
1.  ACID vs BASE / CAP / PACELC
2.  MySQL InnoDB vs MyISAM
3.  binlog / redo log / undo log 区别
4.  PostgreSQL MVCC 原理
5.  Redis 持久化 RDB vs AOF
6.  Redis 5 种数据类型典型用途
7.  Kafka 分区 / 副本 / ISR
8.  RocketMQ vs Kafka 异同
9.  Nacos AP vs CP
10. Elasticsearch 倒排索引
11. ClickHouse 为何快 (列存+MergeTree+SIMD+并行)
12. Nginx upstream 负载策略
13. 索引选择 (B+树 / Hash / 全文 / 倒排)
14. SQL 慢查询 5 大原因
15. Redis 缓存击穿/穿透/雪崩
16. Kafka 重复消费 / 顺序
17. CAP 三选二 实例
18. 主从复制 vs 多主
19. 读写分离 + 分库分表 思路
20. 高可用方案 (主从/主备/集群)
```

## 十二、推荐栈（基础）

```
关系型:      MySQL ⭐ / PostgreSQL ⭐ / 国产 OceanBase
KV/缓存:     Redis ⭐ / KeyDB
消息:        Kafka ⭐ + RocketMQ ⭐
注册/配置:   Nacos ⭐
搜索:        Elasticsearch ⭐ / OpenSearch
OLAP:        ClickHouse ⭐
网关:        Nginx ⭐ / APISIX / Higress
```

## 十三、学习路径

```
入门（1-3 月）:
  1. 单机部署 MySQL / PG / Redis / Kafka / ES / CK / Nginx / Nacos
  2. 必会命令/SQL/API 全部跑通
  3. 选型 + 20 题

进阶（3-12 月，见 02_进阶）:
  4. 主从 / 集群 / 分布式
  5. 性能调优 + 监控
  6. 容器化部署 (StatefulSet / Operator)
```

> 📖 **核心判断**：中间件基础 = **MySQL/PG + Redis + Kafka/RocketMQ + Nacos + ES + ClickHouse + Nginx 八件套**。能在单机跑通 + 写基础 SQL/API/配置，就具备业务开发与运维入门能力。
