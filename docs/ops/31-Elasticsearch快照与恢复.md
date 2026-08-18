# Elasticsearch 快照与恢复实战

> ES 索引误删了怎么办?集群挂了怎么恢复?磁盘满了怎么迁移数据?快照仓库怎么搭?本文覆盖 Elasticsearch 快照与恢复全栈:仓库搭建(文件系统/S3/MinIO)、快照创建(SLM 自动快照)、恢复操作(全量/部分/跨集群)、灾难恢复、误删恢复、监控告警、故障排查。

---

## 一、快照与恢复原理

### 1.1 ES 数据模型速览

```
Elasticsearch 存储层级:

  Cluster (集群)
   └── Index (索引, 逻辑上 = 数据库表)
        └── Shard (分片, 每个分片 = 一个 Lucene 实例)
             ├── Primary Shard (主分片)
             └── Replica Shard (副本分片)
                  └── Segment (段, Lucene 数据文件)
                       └── 倒排索引 + 文档

  数据文件 (Lucene):
    .tim/.tip   倒排索引
    .fdt/.fdx   字段数据
    .dvd/.dvm   文档值
    .cfs        段文件合并
    .si         段信息
    translog    事务日志 (写入缓冲, 防丢数据)

  快照的本质:
    把索引的分片文件 (segment) 复制到仓库 (Repository)
    增量快照: 只备份变化的部分 (segment 级去重)
```

### 1.2 快照机制

```
快照 (Snapshot) 工作机制:

  1. 创建快照 → 向集群发请求
  2. 对每个分片: 生成一个"一致性点" (Lucene IndexCommit)
  3. 把该点之后新写入的 segment 复制到仓库
  4. 已存在于仓库的 segment 跳过 (增量)
  5. 快照元数据记录: 索引列表 + 分片清单 + segment 清单

  关键特性:
    - 增量备份: 每个 segment 只存一次, 后续快照只传新增
    - 一致性: 快照基于 Lucene commit, 数据一致 (非简单文件拷贝)
    - 不阻塞: 快照期间索引可正常读写
    - 版本兼容: 快照只能在 >= 创建版本的集群恢复
      (7.x 快照 → 8.x 可恢复; 8.x 快照 → 7.x 不行)

  快照包含:
    - 索引数据 (全部分片)
    - 索引设置 (settings)
    - 索引映射 (mappings)
    - 别名 (aliases)
    - 模板 (templates, 可选)
    - 集群状态 (feature states, 可选)

  segment 合并 (merge) 对快照的影响:
    - 合并会删除旧 segment → 旧快照的 segment 若被删, 快照失效?
      → 不会! 仓库里的 segment 文件快照持有引用, 不会被清理
    - force merge 后再快照: 文件少, 快照小 (但破坏增量)

  快照文件布局 (仓库目录):
    index-0 / index.latest      快照索引
    meta-<uuid>.dat             快照元数据
    snap-<uuid>.dat             快照清单
    indices/<index-uuid>/       各索引分片数据
      /0/seg-xxx.xxx            segment 文件
      /1/seg-xxx.xxx
      /meta-<uuid>.dat
```

### 1.3 恢复机制

```
恢复 (Restore) 工作机制:

  1. 从仓库读快照元数据
  2. 创建新索引 (或覆盖已有索引)
  3. 下载 segment 文件到节点
  4. 分配分片, 索引可读

  恢复注意事项:
    - 恢复操作: 从快照恢复的索引, 可以指定新索引名 (rename)
    - 覆盖恢复: 如果索引已存在且不 rename, 恢复会失败
      → 需要先删除原索引 (close 也可)
    - 恢复期间: 新写入的数据会合并进恢复的索引
    - 恢复是异步的: 可监控 _recovery 进度

  关闭索引恢复 (close → restore → open):
    - 用于原地恢复 (不 rename), 需要先 close 索引
    - 比删除安全: 恢复失败原数据还在

  恢复到新集群:
    - 快照包含所有需要的文件, 新集群直接注册同一仓库即可
    - 前提: 新集群版本 >= 快照版本
```
---

## 二、快照仓库搭建

### 2.1 仓库类型

```
仓库 (Repository) 类型:

  ┌────────────────┬───────────┬──────────┬───────────────┐
  │ 类型           │ 存储介质   │ 常用场景  │ 备注           │
  ├────────────────┼───────────┼──────────┼───────────────┤
  │ fs             │ 本地磁盘   │ 单机/测试 │ 所有节点共享路径│
  │ url            │ HTTP      │ 只读归档  │ 只支持读       │
  │ s3             │ S3 兼容   │ 生产主力  │ AWS/MinIO/OSS │
  │ gcs            │ GCS       │ 云        │ Google Cloud  │
  │ azure          │ Azure Blob│ 云        │ Microsoft     │
  │ hdfs           │ HDFS      │ 大数据    │ 需要插件       │
  │ source-only    │ 只读源    │ 迁移      │ 需重新索引     │
  └────────────────┴───────────┴──────────┴───────────────┘

  生产推荐:
    - 首选 S3 兼容 (MinIO/阿里云 OSS/AWS S3)
    - 自建: MinIO (便宜, 兼容 S3 API)
    - 或 NFS 共享目录 (所有 ES 节点挂载同一路径)
    - 不推荐: 本地盘做 fs 仓库 (节点挂了仓库也没了!)
```

### 2.2 文件系统仓库 (fs)

```yaml
# === 场景: 单机/测试/NFS 共享目录 ===

# 1. 各节点挂载共享目录 (NFS 示例)
# /etc/fstab
10.0.1.50:/data/es-backup   /mnt/es-backup   nfs   defaults,noatime  0 0
mount -a
# 注意: 所有 ES 节点必须挂载同一个仓库路径 (共享文件系统)
# 单节点集群可以本地目录

# 2. 配置 elasticsearch.yml (所有节点)
path.repo: ["/mnt/es-backup"]
# 或 "~/my_repo"
# 配置后需重启所有节点

# 3. 注册仓库 (REST API)
curl -X PUT "http://node1:9200/_snapshot/my_fs_repo" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/mnt/es-backup/my_repo",
      "compress": true,
      "max_restore_bytes_per_sec": "200mb",
      "max_snapshot_bytes_per_sec": "200mb",
      "chunk_size": "1g"
    }
  }'

# 参数说明:
#   location:   仓库路径 (必须被 path.repo 覆盖)
#   compress:   压缩 (默认 true)
#   chunk_size: 大文件分块 (如 1g), 便于存储
#   max_snapshot_bytes_per_sec: 快照写限速 (默认 40mb, 生产调大)
#   max_restore_bytes_per_sec:  恢复读限速 (默认无限制)

# 4. 验证
curl "http://node1:9200/_snapshot/my_fs_repo?pretty"
curl -X POST "http://node1:9200/_snapshot/my_fs_repo/_verify?pretty"
# {
#   "nodes" : {
#     "node1" : { "name" : "node-1" }
#   }
# }
```

### 2.3 S3/MinIO 仓库 (生产推荐)

```bash
# === 场景: 生产集群 + MinIO 仓库 ===

# 1. 安装 S3 仓库插件 (所有节点!)
sudo /usr/share/elasticsearch/bin/elasticsearch-plugin install repository-s3
# 或 Docker:
# docker exec es-node bin/elasticsearch-plugin install repository-s3

# 2. 重启所有节点使插件生效

# 3. 配置 S3 凭证 (keystore, 安全存储)
# 用 elasticsearch-keystore 添加凭证 (不会明文出现在配置)
sudo -u elasticsearch /usr/share/elasticsearch/bin/elasticsearch-keystore add s3.client.default.access_key
sudo -u elasticsearch /usr/share/elasticsearch/bin/elasticsearch-keystore add s3.client.default.secret_key
# 交互式输入密钥, 输入后重启节点

# 4. 注册 MinIO 仓库
curl -X PUT "http://node1:9200/_snapshot/s3_repo" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "s3",
    "settings": {
      "bucket": "es-backup",
      "endpoint": "http://minio1:9000",
      "base_path": "prod/es",
      "protocol": "http",
      "region": "us-east-1",
      "compress": true,
      "max_restore_bytes_per_sec": "500mb",
      "max_snapshot_bytes_per_sec": "500mb",
      "path_style_access": true
    }
  }'

# MinIO 场景必须:
#   path_style_access: true   (MinIO 用 path-style)
#   endpoint: MinIO 地址
#   protocol: http (MinIO 默认 http)

# 5. 验证
curl -X POST "http://node1:9200/_snapshot/s3_repo/_verify?pretty"

# 6. 检查 MinIO 桶
mc ls minio/es-backup/prod/es
```

### 2.4 仓库管理

```bash
# === 查看仓库 ===
curl "http://node1:9200/_snapshot?pretty"
curl "http://node1:9200/_snapshot/_all?pretty"

# === 删除仓库 (不删快照文件, 只解除注册) ===
curl -X DELETE "http://node1:9200/_snapshot/s3_repo"

# === 查看仓库状态 ===
curl "http://node1:9200/_snapshot/s3_repo/_status?pretty"

# === 仓库容量监控 ===
# 仓库里的快照大小
curl "http://node1:9200/_snapshot/s3_repo/*?pretty" | jq '.snapshots[] | {snapshot, state, indices: (.indices|length), start_time}'
```

---

## 三、创建快照

### 3.1 手动快照

```bash
# === 备份全部索引 ===
curl -X PUT "http://node1:9200/_snapshot/s3_repo/snapshot_20260714" -H 'Content-Type: application/json' -d '{
  "indices": "*",
  "ignore_unavailable": true,
  "include_global_state": false
}'
# 说明:
#   indices: "*" 全部索引
#   include_global_state: false → 不备份集群状态 (模板/ILM 等)
#     建议 false, 避免恢复时覆盖目标集群配置

# === 备份指定索引 ===
curl -X PUT "http://node1:9200/_snapshot/s3_repo/snap_nginx_logs" -H 'Content-Type: application/json' -d '{
  "indices": "nginx-*",
  "ignore_unavailable": true
}'

# 多个索引
curl -X PUT "http://node1:9200/_snapshot/s3_repo/snap_multi" -H 'Content-Type: application/json' -d '{
  "indices": "logs-2026.07.14,metrics-2026.07.14,audit-*",
  "ignore_unavailable": true
}'

# === 不指定 indices = 全部 ===
curl -X PUT "http://node1:9200/_snapshot/s3_repo/snap_all"

# === 查看快照状态 (立即返回, 异步执行) ===
curl "http://node1:9200/_snapshot/s3_repo/snap_nginx_logs/_status?pretty"

# === 等待快照完成 (阻塞直到完成) ===
curl -X PUT "http://node1:9200/_snapshot/s3_repo/snap_all?wait_for_completion=true&pretty"

# === 查看所有快照 ===
curl "http://node1:9200/_snapshot/s3_repo/_all?pretty"
# {
#   "snapshots": [
#     {
#       "snapshot": "snap_20260714",
#       "uuid": "xxx",
#       "state": "SUCCESS",
#       "start_time_in_millis": ...,
#       "end_time_in_millis": ...,
#       "duration_in_millis": ...,
#       "indices": ["nginx-2026.07.14"],
#       "shards": {"total": 5, "failed": 0, "successful": 5},
#       "stats": {"incremental": {...}, "total": {...}}
#     }
#   ]
# }
```

### 3.2 SLM 自动快照 (Snapshot Lifecycle Management)

```json
// slm-policy.json — 每日快照策略
{
  "schedule": "0 30 2 * * ?",          // 每天 02:30 (cron 格式, 6 段)
  "name": "daily-snap-{now/d}",         // 快照名模板, {now/d} 自动加日期
  "repository": "s3_repo",
  "config": {
    "indices": ["*"],
    "include_global_state": false,
    "ignore_unavailable": true,
    "expand_wildcards": "open"
  },
  "retention": {                         // 保留策略
    "expire_after": "30d",              // 超过 30 天
    "max_count": 30,                    // 最多 30 个
    "min_count": 5                      // 至少保留 5 个
  }
}

// 应用策略
curl -X PUT "http://node1:9200/_slm/policy/daily-backup" \
  -H 'Content-Type: application/json' \
  -d @slm-policy.json

// 立即执行一次 (不等调度)
curl -X POST "http://node1:9200/_slm/policy/daily-backup/_execute?pretty"

// 查看策略
curl "http://node1:9200/_slm/policy?pretty"
curl "http://node1:9200/_slm/policy/daily-backup?pretty"

// 策略执行历史
curl "http://node1:9200/_slm/stats?pretty"

// 修改策略 (重新 PUT 同 name)
// 删除策略 (不删已创建的快照)
curl -X DELETE "http://node1:9200/_slm/policy/daily-backup"

// 查看所有 SLM 快照
curl "http://node1:9200/_snapshot/s3_repo/_all?pretty" | jq '.snapshots[] | select(.snapshot|startswith("daily-snap")) | .snapshot'
```

### 3.3 增量快照原理与验证

```bash
# === 增量验证 ===
# 第一次快照 (全量)
curl -X PUT "http://node1:9200/_snapshot/s3_repo/snap_v1?wait_for_completion=true"

# 写点新数据
curl -X POST "http://node1:9200/nginx-2026.07.14/_doc" -H 'Content-Type: application/json' -d '{"message": "new log"}'

# 第二次快照 (增量, 秒级完成)
curl -X PUT "http://node1:9200/_snapshot/s3_repo/snap_v2?wait_for_completion=true"
# 观察 stats.incremental:
#   - 第二次的快照 incremental.file_count 远小于第一次
#   - 只备份了新增的 segment

# 快照大小对比
curl "http://node1:9200/_snapshot/s3_repo/_all?pretty" | jq '.snapshots[] | {snapshot, size: .stats.total.size_in_bytes, incr: .stats.incremental.size_in_bytes}'

# === 快照存储原理 ===
# segment 级去重:
#   - 第一次: 备份所有 segment (几 GB)
#   - 第二次: 只备份新增 segment (几 MB)
#   - 即使删除旧快照, 未引用的 segment 文件才被清理

# === 加速快照 (segment 调优) ===
# 快照前 force merge 能减少 segment 数 (快照更小更快)
# 注意: force merge 影响增量备份, 建议只对归档索引做
curl -X POST "http://node1:9200/archive-2025.06/_forcemerge?max_num_segments=1"
```

### 3.4 快照生命周期 (ILM + SLM 配合)

```json
// ILM 策略 — 热温冷架构 + 快照
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": { "max_age": "1d", "max_size": "50gb" }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": { "forcemerge": { "max_num_segments": 1 } }
      },
      "cold": {
        "min_age": "30d",
        "actions": { "searchable_snapshot": { "snapshot_repository": "s3_repo" } }
      },
      "delete": {
        "min_age": "90d",
        "actions": { "delete": {} }
      }
    }
  }
}
// 说明:
//   cold 阶段: 索引转成可搜索快照 (数据迁到仓库, 本地不留副本)
//   delete 阶段: 删除索引 (快照仍在仓库, 可随时恢复)

// 应用 ILM 策略
curl -X PUT "http://node1:9200/_ilm/policy/logs-policy" \
  -H 'Content-Type: application/json' -d @ilm.json
```

---

## 四、恢复操作

### 4.1 恢复全部索引 (新集群/灾难恢复)

```bash
# === 场景: 集群重建后恢复全部数据 ===

# 1. 新集群注册仓库 (同配置)
curl -X PUT "http://new-node1:9200/_snapshot/s3_repo" -H 'Content-Type: application/json' -d '{
  "type": "s3",
  "settings": { "bucket": "es-backup", "endpoint": "http://minio1:9000", "base_path": "prod/es", "path_style_access": true }
}'

# 2. 查看可用快照
curl "http://new-node1:9200/_snapshot/s3_repo/_all?pretty" | jq '.snapshots[-1].snapshot'

# 3. 恢复全部索引 (从指定快照)
curl -X POST "http://new-node1:9200/_snapshot/s3_repo/daily-snap-2026.07.14/_restore?wait_for_completion=false" \
  -H 'Content-Type: application/json' -d '{
    "indices": "*",
    "ignore_unavailable": true,
    "include_global_state": false,
    "rename_pattern": "(.+)",
    "rename_replacement": "restored_$1"
  }'

# 不 rename (原索引名, 若目标集群没有同名索引):
curl -X POST "http://new-node1:9200/_snapshot/s3_repo/daily-snap-2026.07.14/_restore" \
  -H 'Content-Type: application/json' -d '{
    "indices": "*",
    "include_global_state": false
  }'

# 4. 监控恢复进度
curl "http://new-node1:9200/_recovery?pretty" | jq '.[] | {index, stage, percent: .shards[0].index.percent, bytes_recovered}'

# 5. 等待所有分片恢复
curl "http://new-node1:9200/_cat/indices?v&s=index"
curl "http://new-node1:9200/_cluster/health?pretty"
# status: green = 全部恢复完成
```

### 4.2 恢复指定索引

```bash
# === 场景: 误删单个索引 ===

# 1. 查看快照里有啥
curl "http://node1:9200/_snapshot/s3_repo/snap_nginx_logs?pretty" | jq '.snapshots[0].indices'

# 2. 恢复指定索引 (带 rename, 安全)
curl -X POST "http://node1:9200/_snapshot/s3_repo/snap_nginx_logs/_restore" \
  -H 'Content-Type: application/json' -d '{
    "indices": "nginx-2026.07.14",
    "rename_pattern": "nginx-(.+)",
    "rename_replacement": "nginx-restored-$1"
  }'
# 恢复为 nginx-restored-2026.07.14, 验证后再决定是否换回原名

# 3. 原地恢复 (索引名不变, 先删原索引)
curl -X DELETE "http://node1:9200/nginx-2026.07.14"
curl -X POST "http://node1:9200/_snapshot/s3_repo/snap_nginx_logs/_restore" \
  -H 'Content-Type: application/json' -d '{
    "indices": "nginx-2026.07.14"
  }'

# 4. 原地恢复 (不删索引, 先 close) — 推荐安全做法
curl -X POST "http://node1:9200/nginx-2026.07.14/_close"
curl -X POST "http://node1:9200/_snapshot/s3_repo/snap_nginx_logs/_restore" \
  -H 'Content-Type: application/json' -d '{
    "indices": "nginx-2026.07.14"
  }'
# 恢复完成后索引自动 open
curl -X GET "http://node1:9200/nginx-2026.07.14/_count" 

# 5. 部分恢复 (恢复指定字段? 不支持, 但可以)
# 恢复后重新索引子集 (用 reindex):
curl -X POST "http://node1:9200/_reindex" -H 'Content-Type: application/json' -d '{
  "source": { "index": "nginx-restored-2026.07.14", "query": { "range": { "@timestamp": { "gte": "2026-07-14T00:00:00" } } } },
  "dest": { "index": "nginx-partial" }
}'
```

### 4.3 恢复到旧版本/跨集群迁移

```
版本兼容规则:
  快照恢复要求: 目标集群版本 >= 快照创建版本
  7.x 快照 → 8.x 恢复: ✅ 可以
  8.x 快照 → 7.x 恢复: ❌ 不行

跨版本恢复注意:
  - 7.x → 8.x: 需要先升级到 7.10+ 再跨 (官方建议逐版本)
  - 恢复后: 索引可能触发 reindex (新版本 API 变更)
  - 模板/ILM 需重新配置 (include_global_state: false 不恢复)
```

```bash
# === 跨集群迁移 (同版本) ===
# 场景: 旧集群 → 新集群 (换硬件/换机房)

# 方法 1: 共享 S3/MinIO 仓库
# 1. 旧集群注册仓库 → 打快照
# 2. 新集群注册同一仓库 (同一 base_path)
# 3. 新集群 restore
curl -X POST "http://new:9200/_snapshot/s3_repo/snap_full/_restore" \
  -H 'Content-Type: application/json' -d '{
    "indices": "*",
    "include_global_state": false
  }'

# 方法 2: 迁移 + 双写 (滚动迁移, 零停机)
# 1. 新集群建同结构索引 (从旧集群导出 mappings/settings)
curl "http://old:9200/index/_mapping?pretty" > mapping.json
# 2. 应用双写: 写旧集群 → 转发新集群 (应用层或 logstash 双输出)
# 3. 历史数据用 reindex 迁移
curl -X POST "http://new:9200/_reindex?wait_for_completion=false" \
  -H 'Content-Type: application/json' -d '{
    "source": { "remote": { "host": "http://old:9200" }, "index": "logs-2026.06", "size": 10000 },
    "dest": { "index": "logs-2026.06" }
  }'
# 4. 追平后切换

# 方法 3: 仓库 + 只读索引迁移 (searchable snapshots)
```

### 4.4 恢复验证

```bash
# === 恢复后必须验证 ===

# 1. 集群健康
curl "http://node1:9200/_cluster/health?pretty"
# green = 所有主副分片正常

# 2. 文档数对比 (源 vs 恢复)
# 快照里索引的文档数:
curl "http://node1:9200/_snapshot/s3_repo/snap_nginx_logs?pretty" | jq '.snapshots[0].index_details'
# 恢复后:
curl -X POST "http://node1:9200/nginx-restored-2026.07.14/_count?pretty"
curl -X POST "http://node1:9200/nginx-2026.07.14/_count?pretty"   # 原索引(如果还在)

# 3. 抽样查询验证数据正确性
curl "http://node1:9200/nginx-restored-2026.07.14/_search?pretty" -H 'Content-Type: application/json' -d '{
  "query": { "match_all": {} }, "size": 5
}'

# 4. 分片分配验证
curl "http://node1:9200/_cat/shards/nginx-restored-2026.07.14?v&s=prirep"

# 5. 别名/模板检查 (include_global_state: false 不会恢复别名? 实际会恢复索引别名)
curl "http://node1:9200/nginx-restored-2026.07.14/_alias?pretty"
```

---

## 五、快照删除与清理

### 5.1 删除快照

```bash
# === 删除单个快照 ===
curl -X DELETE "http://node1:9200/_snapshot/s3_repo/snap_old_20260701"

# === 批量删除 (保留最近 N 个) ===
# 获取快照列表, 删除过期
SNAPSHOTS=$(curl -s "http://node1:9200/_snapshot/s3_repo/_all?pretty" | jq -r '.snapshots[].snapshot' | sort)
KEEP=30
COUNT=$(echo "$SNAPSHOTS" | wc -l)
if [ "$COUNT" -gt "$KEEP" ]; then
  echo "$SNAPSHOTS" | head -n $((COUNT - KEEP)) | while read snap; do
    curl -X DELETE "http://node1:9200/_snapshot/s3_repo/$snap"
  done
fi

# === SLM 自动清理 (推荐用 retention) ===
# 已在策略里配置 retention 的, SLM 会自动删除过期快照
curl "http://node1:9200/_slm/stats?pretty" | jq '.retention_runs, .retention_deleted'

# === 删除仓库 (含快照? 只解除注册) ===
curl -X DELETE "http://node1:9200/_snapshot/s3_repo"
# 快照文件仍在存储, 重新注册同名仓库还能看到

# === 清理仓库物理文件 (危险! 需确认) ===
# 1. 先删所有快照
# 2. 删除仓库目录/base_path (MinIO 中删桶/前缀)
mc rm --recursive --force minio/es-backup/prod/es
# 3. 确认集群不再引用
```

### 5.2 磁盘空间管理

```bash
# === 快照仓库空间监控 ===
# MinIO/文件系统层面
mc du minio/es-backup
df -h /mnt/es-backup

# 集群层面: 各索引占用
curl "http://node1:9200/_cat/indices?v&s=store.size:desc&h=index,store.size,pri.store.size&bytes=gb" | head -20

# === 快照仓库满的处理 ===
# 1. 检查大快照
curl "http://node1:9200/_snapshot/s3_repo/_all?pretty" | jq '.snapshots[] | {snapshot, total: .stats.total.size_in_bytes} | select(.total > 100000000000)'

# 2. 删除最旧快照
curl -X DELETE "http://node1:9200/_snapshot/s3_repo/$(oldest_snap)"

# 3. 调低保留数量
curl -X PUT "http://node1:9200/_slm/policy/daily-backup" -H 'Content-Type: application/json' -d '{
  ...原有配置..., "retention": { "max_count": 15, "expire_after": "15d" }
}'

# 4. 增加仓库容量 (MinIO 扩桶/加盘)
```

---

## 六、灾难恢复 (DR)

### 6.1 集群级灾难恢复流程

```
灾难场景:
  A. 节点全部宕机 (断电/机房事故)
  B. 磁盘损坏 (数据丢失)
  C. 误删索引/误删数据
  D. 版本升级失败

恢复优先级:
  1. 先恢复集群本身 (节点/网络)
  2. 检查本地数据是否完好 (可能无需快照!)
  3. 本地数据损坏才用快照恢复
  4. 快照也没有 → 用其他备份 (HDFS/数仓) + 重新灌入
```

```bash
# === 场景 A: 集群全挂, 数据盘完好 ===

# 1. 启动所有节点
systemctl start elasticsearch
# 或 k8s: kubectl scale sts es --replicas=3

# 2. 等待集群恢复
curl "http://node1:9200/_cluster/health?pretty"
# 数据在本地盘, 分片自动恢复 (shard recovery)
# 恢复时间取决于数据量

# 3. 确认全部索引 green
curl "http://node1:9200/_cat/indices?v&h=index,health,status,pri,rep,docs.count,store.size&s=index"

# 4. 无需快照 (本地数据完好)
# 快照用于: 节点全损/盘损坏场景

# === 场景 B: 盘损坏, 数据丢失 ===

# 1. 确认损坏范围 (哪些索引受影响)
curl "http://node1:9200/_cat/shards?v&h=index,shard,prirep,state,node&s=index" | grep -v STARTED

# 2. 用快照恢复 (restore 会覆盖重建)
# 删除损坏索引 (或 close)
curl -X DELETE "http://node1:9200/logs-2026.07.*"

# 3. 从最近快照恢复
curl -X POST "http://node1:9200/_snapshot/s3_repo/daily-snap-2026.07.14/_restore" \
  -H 'Content-Type: application/json' -d '{
    "indices": "logs-2026.07.*",
    "include_global_state": false
  }'

# 4. 监控恢复
curl "http://node1:9200/_recovery?pretty" | jq '.[] | {index, stage, percent: .shards[0].index.percent}'
```

### 6.2 误删数据恢复

```bash
# === 场景: 误删了文档/索引 ===

# 1. 误删索引
# 快照恢复 (见 4.2)

# 2. 误删文档 (delete by query)
# 快照恢复到临时索引, 找回数据
curl -X POST "http://node1:9200/_snapshot/s3_repo/snap_20260714/_restore" \
  -H 'Content-Type: application/json' -d '{
    "indices": "myindex",
    "rename_pattern": "(.+)",
    "rename_replacement": "myindex-restored"
  }'

# 找回误删的文档 (对比 restored 与当前)
# 方法: 在 restored 索引里查, 把缺失文档 reindex 回原索引

# 3. 数据被覆盖 (update 覆盖字段)
# 需要时间点恢复: ES 快照不直接支持 PIT
# 方案: 恢复最近快照 + translog replay (不支持)
# 替代: 快照频率够高 (小时级) + 业务侧补偿

# 4. 集群状态误改 (误删 template/ILM)
# 快照 include_global_state: true 的快照可恢复集群状态
# 或从配置管理恢复 (GitOps)

# 防误删最佳实践:
# 1. 开启 delete protection (ES 8.6+)
curl -X PUT "http://node1:9200/myindex/_settings" -H 'Content-Type: application/json' -d '{
  "index.gateway.disable_delete": true
}'
# 2. 生产环境禁止 delete by query (用 reindex + 过滤)
# 3. SLM 快照频率: 核心索引每小时
# 4. 恢复操作先在测试环境演练
```

### 6.3 跨集群复制 (CCR) — 实时容灾

```bash
# === CCR (Cross-Cluster Replication) ===
# 实时复制, RPO 秒级 (与快照互补: 快照是 RPO 小时级兜底)

# 1. 两个集群都启用远程集群
# elasticsearch.yml:
# cluster.remote.connections: 3

# 2. 在目标集群注册源集群
curl -X PUT "http://dr-node:9200/_cluster/settings" \
  -H 'Content-Type: application/json' -d '{
    "persistent": {
      "cluster.remote.dr-cluster.seeds": ["source-node1:9300", "source-node2:9300"]
    }
  }'

# 3. 在目标集群创建 follower 索引
curl -X PUT "http://dr-node:9200/logs-2026.07.14/_ccr/follow" \
  -H 'Content-Type: application/json' -d '{
    "remote_cluster": "dr-cluster",
    "leader_index": "logs-2026.07.14"
  }'

# 4. 查看复制状态
curl "http://dr-node:9200/logs-2026.07.14/_ccr/info?pretty"
curl "http://dr-node:9200/_ccr/stats?pretty" | jq '.follow_stats.indices'

# 5. 故障切换: 源集群挂 → follower 提升为可写
curl -X POST "http://dr-node:9200/logs-2026.07.14/_ccr/unfollow"
curl -X POST "http://dr-node:9200/logs-2026.07.14/_open"

# 架构建议:
# 生产集群 (主) + 灾备集群 (follower, 异机房)
# 快照: 主集群每日 SLM → 仓库 (供恢复)
# CCR: 核心索引实时复制到灾备
# 双保险: CCR 挂时用快照补
```

---

## 七、监控与告警

### 7.1 快照相关指标

```promql
# Prometheus (elasticsearch_exporter) 关键指标

# 快照数
elasticsearch_snapshot_total

# 最近快照年龄 (小时) — 超时告警!
(time() - elasticsearch_snapshot_creation_date_seconds) / 3600

# SLM 执行状态
elasticsearch_slm_status

# 仓库快照失败
elasticsearch_snapshot_failed

# 集群分片恢复进度
elasticsearch_cluster_shards_initializing / elasticsearch_cluster_shards_active
```

### 7.2 告警规则

```yaml
# es-alerts.yml
groups:
- name: elasticsearch
  rules:
  - alert: ESSnapshotAge
    # 最近成功快照超过 26 小时 (每日快照)
    expr: (time() - max(elasticsearch_snapshot_creation_date_seconds) by (cluster)) / 3600 > 26
    for: 1h
    labels: { severity: critical }
    annotations:
      summary: "ES 快照超过 26 小时未成功创建!"

  - alert: ESSnapshotFailed
    expr: increase(elasticsearch_snapshot_failed[1h]) > 0
    labels: { severity: critical }
    annotations:
      summary: "ES 快照失败"

  - alert: ESClusterRed
    expr: elasticsearch_cluster_health_status == 2
    for: 5m
    labels: { severity: critical }
    annotations:
      summary: "ES 集群 RED (有分片丢失)"

  - alert: ESClusterYellow
    expr: elasticsearch_cluster_health_status == 1
    for: 15m
    labels: { severity: warning }
    annotations:
      summary: "ES 集群 YELLOW (副本分片未分配)"

  - alert: ESDiskWatermark
    expr: (elasticsearch_filesystem_data_available_bytes / elasticsearch_filesystem_data_total_bytes) * 100 < 10
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "ES 磁盘可用 < 10% (注意写入水印)"

  - alert: ESShardInitializing
    expr: elasticsearch_cluster_shards_initializing > 0
    for: 30m
    labels: { severity: warning }
    annotations:
      summary: "ES 有分片长时间初始化 (恢复卡住)"
```

### 7.3 快照失败排查

```bash
# === 快照失败常见原因 ===

# 1. 查看失败详情
curl "http://node1:9200/_snapshot/s3_repo/_all?pretty" | jq '.snapshots[] | select(.state=="FAILED" or .state=="PARTIAL")'

# 2. 查看失败原因
curl "http://node1:9200/_snapshot/s3_repo/failed_snap?pretty"
# "reason" 字段给出原因

# 常见失败原因:
#   - 仓库不可达 (MinIO 挂了/网络)
#   - 凭证失效 (S3 密钥轮换)
#   - 磁盘空间不足 (仓库所在存储满)
#   - 索引有 closed 分片 (ignore_unavailable: true 解决)
#   - 并发快照 (SLM + 手动同时执行, 默认只允许 1 个)
#   - 节点内存不足 (快照期间 OOM)

# 3. 并发限制查看/调整
curl "http://node1:9200/_cluster/settings?pretty" | jq '.persistent.snapshot'
# 默认: max_concurrent_snapshots: 1
# 集群级调整:
curl -X PUT "http://node1:9200/_cluster/settings" -H 'Content-Type: application/json' -d '{
  "persistent": { "snapshot.max_concurrent_operations": 4 }
}'

# 4. 仓库可用性测试
curl -X POST "http://node1:9200/_snapshot/s3_repo/_verify?pretty"

# 5. 手动重试
curl -X PUT "http://node1:9200/_snapshot/s3_repo/retry_snap" -H 'Content-Type: application/json' -d '{
  "indices": "*", "include_global_state": false
}'
```

---

## 八、生产最佳实践

### 8.1 备份策略设计

```
生产备份策略 (推荐):

  1. 快照频率:
     - 核心业务索引: 每小时 (SLM)
     - 一般索引: 每日 (SLM)
     - 归档索引: 每周

  2. 保留策略:
     - 每小时快照: 保留 24-48 个
     - 每日快照: 保留 30-90 个
     - 每月快照: 保留 12 个 (长期)
     - 容量核算: 每日增量约 1-5% 总量

  3. 仓库要求:
     - 与集群隔离 (不同机房/存储)
     - MinIO 至少 2 副本 (纠删码)
     - 容量: 集群总数据量 * 20% (日常增量)
     - 异地副本 (rclone 同步仓库到异地)

  4. 恢复目标:
     - RPO: 1 小时 (每小时快照)
     - RTO: 核心索引 < 30 分钟, 全量 < 4 小时

  5. 演练:
     - 每月: 恢复单个索引验证
     - 每季: 恢复全部索引到临时集群
     - 每年: 完整容灾演练

  6. 双保险:
     - 快照 (ES 原生) + CCR (实时复制)
     - 数据导出 (logstash/数仓) 兜底
```

### 8.2 快照调优

```json
// 仓库参数调优
{
  "type": "s3",
  "settings": {
    "bucket": "es-backup",
    "endpoint": "http://minio1:9000",
    "path_style_access": true,
    "compress": true,
    "chunk_size": "64mb",
    "max_restore_bytes_per_sec": "500mb",
    "max_snapshot_bytes_per_sec": "500mb",
    "base_path": "prod/es"
  }
}
// 要点:
//   chunk_size: 64mb 平衡并发与单文件
//   max_snapshot_bytes_per_sec: 生产调到 500mb+ (默认 40mb 太慢!)
//   max_restore_bytes_per_sec: 恢复限速 (避免压垮磁盘)
//   compress: 网络慢时开, 本地快时关 (CPU 换带宽)
```

```bash
# === 加速大集群快照 ===
# 1. 多分片并行: 快照按分片并行 (分片多自然快)
# 2. 仓库放 SSD/MinIO NVMe
# 3. 避开高峰 (SLM 调度到凌晨)
# 4. force merge 归档索引 (segment 少 → 快照小)
# 5. 只备份需要的索引 (不备份不重要的)
# 6. 磁盘快照限速适当放开

# === 加速恢复 ===
# 恢复时临时调高:
curl -X PUT "http://node1:9200/_cluster/settings" -H 'Content-Type: application/json' -d '{
  "transient": {
    "cluster.routing.allocation.node_concurrent_recoveries": 8,
    "indices.recovery.max_bytes_per_sec": "1gb"
  }
}'
# 恢复完成后恢复默认:
curl -X PUT "http://node1:9200/_cluster/settings" -H 'Content-Type: application/json' -d '{
  "transient": {
    "cluster.routing.allocation.node_concurrent_recoveries": 2,
    "indices.recovery.max_bytes_per_sec": "40mb"
  }
}'
```

### 8.3 快照安全

```
快照安全要点:

  1. 仓库凭证: 用 keystore (不落配置文件)
     elasticsearch-keystore add s3.client.default.access_key

  2. 网络隔离: 仓库与集群内部网段

  3. 加密: MinIO 桶加密 / S3 SSE

  4. 权限: 快照 API 限制
     - 给运维专用角色
     curl -X PUT "http://node1:9200/_security/role/snapshot_admin" -H 'Content-Type: application/json' -d '{
       "cluster": ["manage_slm", "create_snapshot", "manage_snapshots", "manage_ilm"],
       "indices": [{ "names": ["*"], "privileges": ["read"] }]
     }'

  5. 异地: 仓库 rclone 同步到异地 (防机房级灾难)

  6. 防勒索: 快照仓库只读挂载 (部分场景)
     - MinIO 桶设置 WORM/对象锁定
```

### 8.4 巡检脚本

```bash
#!/bin/bash
# es-backup-check.sh — ES 快照巡检

LOG=/var/log/es-backup-check-$(date +%Y%m%d).log
ES="http://node1:9200"

exec > ${LOG} 2>&1
echo "=== ES Snapshot Check $(date) ==="

echo
echo "=== 1. 集群健康 ==="
curl -s "${ES}/_cluster/health?pretty" | jq '{status, number_of_nodes, active_primary_shards, active_shards, relocating_shards, initializing_shards, unassigned_shards}'

echo
echo "=== 2. 仓库状态 ==="
curl -s "${ES}/_snapshot/_all?pretty" | jq 'keys'
for repo in $(curl -s "${ES}/_snapshot/_all?pretty" | jq -r 'keys[]'); do
  echo "--- ${repo} ---"
  curl -s -X POST "${ES}/_snapshot/${repo}/_verify?pretty" | jq '.nodes | keys'
done

echo
echo "=== 3. 最近快照 ==="
for repo in $(curl -s "${ES}/_snapshot/_all?pretty" | jq -r 'keys[]'); do
  curl -s "${ES}/_snapshot/${repo}/_all?pretty" | jq -r --arg r "${repo}" '
    .snapshots[-5:] | .[] | "\($r) \(.snapshot) state=\(.state) shards=\(.shards.successful)/\(.shards.total) time=\(.start_time)"'
done

echo
echo "=== 4. 快照年龄检查 (应 < 26h) ==="
NEWEST=$(curl -s "${ES}/_snapshot/s3_repo/_all?pretty" | jq -r '.snapshots[-1].start_time' 2>/dev/null)
echo "最近快照时间: ${NEWEST}"
if [ -n "${NEWEST}" ]; then
  NEWEST_EPOCH=$(date -d "${NEWEST}" +%s)
  NOW_EPOCH=$(date +%s)
  AGE_HOURS=$(( (NOW_EPOCH - NEWEST_EPOCH) / 3600 ))
  echo "快照年龄: ${AGE_HOURS} 小时"
  [ "${AGE_HOURS}" -gt 26 ] && echo "⚠️ 快照过旧! 检查 SLM"
fi

echo
echo "=== 5. SLM 状态 ==="
curl -s "${ES}/_slm/stats?pretty" | jq '{snapshots_created: .total_snapshots_taken, snapshots_failed: .total_snapshots_failed, snapshots_deleted: .total_snapshots_deleted, last_success: .policy_stats[-1].snapshot_create_last_success_time, last_failure: .policy_stats[-1].snapshot_create_last_failure_time}'

echo
echo "=== 6. SLM 策略 ==="
curl -s "${ES}/_slm/policy?pretty" | jq 'keys'

echo
echo "=== 7. 恢复中的分片 ==="
curl -s "${ES}/_cat/recovery?v&active_only=true&h=index,shard,stage,percent,bytes_percent" 2>/dev/null | head -20

echo
echo "=== 8. 仓库容量 (MinIO) ==="
mc du minio/es-backup 2>/dev/null

echo
echo "=== 9. 磁盘水位 ==="
curl -s "${ES}/_cat/allocation?v&h=node,disk.percent,disk.used,disk.avail&bytes=gb" | head -10

echo
echo "=== 巡检完成 $(date) ==="
```

---

## 九、故障速查表

### 9.1 常见故障与处理

| 故障 | 现象 | 排查 | 处理 |
|:---|:---|:---|:---|
| **快照创建失败** | state=FAILED | 看 reason 字段 | 仓库可达性/凭证/空间 |
| **恢复失败** | 索引未出现 | 看 _restore 返回 | 索引已存在需 rename 或先删 |
| **恢复慢** | 长时间 initializing | `_recovery` 看进度 | 调并发恢复/限速 |
| **仓库不可达** | _verify 报错 | ping MinIO/网络 | 恢复网络/重启插件 |
| **快照卡住** | state=IN_PROGRESS 长期 | 看哪个分片卡 | 取消快照 (DELETE) |
| **磁盘水位告警** | 写入被拒 | `_cat/allocation` | 清理/扩容/删旧索引 |
| **索引 red** | 主分片丢失 | `_cat/shards` 看 unassigned | 恢复副本/快照恢复 |
| **误删索引** | 索引没了 | 快照列表 | restore (见 4.2) |
| **跨版本恢复失败** | 版本不兼容报错 | 看报错 | 升级目标集群 |
| **SLM 不执行** | 无新快照 | `_slm/stats` | 检查调度/策略状态 |

### 9.2 常用命令速查

| 场景 | 命令 |
|:---|:---|
| 注册 fs 仓库 | `PUT /_snapshot/repo` (type=fs, location) |
| 注册 S3 仓库 | `PUT /_snapshot/repo` (type=s3, bucket/endpoint) |
| 验证仓库 | `POST /_snapshot/repo/_verify` |
| 查看仓库 | `GET /_snapshot/_all` |
| 手动快照 | `PUT /_snapshot/repo/snap_name` |
| 快照指定索引 | `PUT /_snapshot/repo/snap {"indices":"logs-*"}` |
| 等待完成 | `PUT ...?wait_for_completion=true` |
| 查看快照 | `GET /_snapshot/repo/_all` |
| 快照状态 | `GET /_snapshot/repo/snap/_status` |
| 删除快照 | `DELETE /_snapshot/repo/snap_name` |
| SLM 策略 | `PUT /_slm/policy/name` |
| 立即执行 SLM | `POST /_slm/policy/name/_execute` |
| 恢复全部 | `POST /_snapshot/repo/snap/_restore` |
| 恢复+改名 | `POST .../ _restore` + rename_pattern |
| 恢复进度 | `GET /_recovery` |
| 集群健康 | `GET /_cluster/health` |
| 分片状态 | `GET /_cat/shards?v` |
| 索引列表 | `GET /_cat/indices?v` |
| 集群设置 | `GET /_cluster/settings` |

### 9.3 关键 API 参考

```
快照 API:
  PUT    /_snapshot/{repo}/{snapshot}              创建快照
  GET    /_snapshot/{repo}/{snapshot}              查看快照
  GET    /_snapshot/{repo}/_all                    全部快照
  GET    /_snapshot/{repo}/{snapshot}/_status      快照执行状态
  DELETE /_snapshot/{repo}/{snapshot}              删除快照
  POST   /_snapshot/{repo}/_verify                 验证仓库
  PUT    /_snapshot/{repo}                         注册仓库
  POST   /_snapshot/{repo}/{snapshot}/_restore     恢复
  GET    /_recovery                                恢复进度
  GET    /_snapshot/_status                        当前快照操作

SLM API:
  PUT    /_slm/policy/{name}                       创建/更新策略
  GET    /_slm/policy/{name}                       查看策略
  DELETE /_slm/policy/{name}                       删除策略
  POST   /_slm/policy/{name}/_execute              立即执行
  GET    /_slm/stats                               SLM 统计
  POST   /_slm/_execute_retention                  立即执行保留清理

集群管理:
  GET    /_cluster/health                          集群健康
  GET    /_cat/shards?v                            分片分布
  GET    /_cat/indices?v                           索引状态
  GET    /_cat/allocation?v                        节点磁盘分配
  GET    /_cluster/settings                        集群设置
  GET    /_cat/recovery?v                          恢复进度
```

---

## 十、FAQ

**Q1: 快照和副本 (replica) 有什么区别?**
副本是集群内实时冗余,防节点故障;快照是持久化备份到独立存储,防集群级灾难/误删。副本不防误删索引,快照可以。

**Q2: 快照会影响线上性能吗?**
会轻微影响(IO/CPU/网络),但快照基于 Lucene commit 的增量复制,不阻塞写入。建议低峰期执行,仓库走独立网络。

**Q3: 快照能恢复到更早的时间点吗?**
快照本身是点备份。想恢复到任意时间点需要: 频繁快照(小时级) + CCR 复制 + 业务侧补偿。ES 没有 binlog 级 PITR。

**Q4: 为什么我的恢复报"index already exists"?**
目标集群已有同名索引。用 rename_pattern 恢复到新名字,或先删除/close 原索引。

**Q5: 快照仓库能同时被多个集群用吗?**
可以(共用同一 bucket),但要注意: 两个集群同时写同一仓库有冲突风险。推荐每个集群独立 base_path。

**Q6: 单节点 ES 需要快照吗?**
更需要! 单节点没有副本冗余,盘坏 = 数据全丢。必须快照 + 独立仓库。

**Q7: 快照仓库用本地盘可以吗?**
开发测试可以,生产不建议 (节点和仓库同时挂 = 全丢)。生产用 MinIO/S3/NFS 独立存储。

**Q8: 快照加密吗?**
默认不加密。用 MinIO 桶加密 / S3 SSE-KMS,或仓库启用加密插件。

**Q9: 恢复需要多长时间?**
取决于数据量和限速: 100GB 数据在 500MB/s 限速下约 3-5 分钟,加上分片分配,一般 10 分钟内。大集群(数 TB)数小时。

**Q10: 快照大小为什么比实际索引小很多?**
增量机制: 第二次快照只存新增 segment;另外压缩 (compress: true) 也有影响。另外备份的是存储大小不是逻辑大小。

**Q11: 删除快照后磁盘空间没释放?**
删除快照会触发仓库清理,但 segment 文件如果被其他快照引用则保留。全部快照删完空间才完全释放。MinIO 层可看对象列表确认。

**Q12: 可以只备份 mapping 不备份数据吗?**
可以: 用 `indices: "xxx"` + 快照后只取 mapping。或直接用 API 导出 mapping: `GET /index/_mapping`。快照本身没有"仅结构"模式,但可以恢复后只留结构。

**Q13: SLM 快照失败会自动重试吗?**
SLM 会记录失败,但不会自动重试。需要监控告警 + 手动补快照,或修复原因后等下一轮。

**Q14: 跨大版本升级(7→8)快照兼容吗?**
7.x 快照可以在 8.x 恢复(向前兼容),但 8.x 快照不能回 7.x。升级前打全量快照,升级失败可回滚。

**Q15: 快照仓库需要多大容量?**
经验值: 集群总数据量的 15-25%(保留 30 天每日快照 + 每小时快照 24 个)。如果数据量大且保留时间长,按增量 1-5%/天估算。

---

*最后更新: 2026-07-14*
