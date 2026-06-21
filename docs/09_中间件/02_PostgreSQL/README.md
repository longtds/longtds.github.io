# PostgreSQL

## 部署与高可用

PostgreSQL 使用 Patroni 实现高可用，搭配 ETCD/Consul/ZooKeeper 做分布式存储。

```yaml
# Patroni 配置示例
scope: postgres-cluster
namespace: /db/
name: pg-node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.0.1:8008

etcd:
  host: 10.0.0.10:2379

postgresql:
  data_dir: /data/postgresql
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: replicator
    superuser:
      username: postgres
      password: postgres
```

## 性能调优

```ini
# postgresql.conf 核心参数
shared_buffers = 4G          # 25% of total RAM
effective_cache_size = 12G   # 75% of total RAM
work_mem = 32MB              # 每个操作的内存限制
maintenance_work_mem = 1G    # 维护操作
wal_buffers = 64MB
random_page_cost = 1.1       # SSD 使用较低值
effective_io_concurrency = 200 # SSD
```

## 备份

```bash
# pg_dump 逻辑备份
pg_dump -h localhost -U postgres -d mydb -F c -f /backup/mydb.dump

# pg_basebackup 物理备份（用于恢复）
pg_basebackup -D /backup/pgbase -X stream -U replicator
```
