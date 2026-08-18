# MinIO 运维实战:故障恢复与数据备份

> MinIO 是 S3 兼容的对象存储,单盘坏了怎么办?节点宕机怎么恢复?数据怎么备份才能万无一失?本文覆盖 MinIO 运维全栈:纠删码原理、部署、驱动器/节点故障恢复、集群重建、数据备份方案(mirror/replicate/版本化)、恢复演练、监控与日常运维。

---

## 一、MinIO 架构与数据保护原理

### 1.1 MinIO 是什么

```
MinIO = 开源 S3 兼容对象存储

  - 单个二进制文件 (go 编写, 无依赖)
  - S3 API 100% 兼容 (aws cli / s3 SDK 直接可用)
  - 纠删码 (Erasure Coding) 数据保护
  - 版本控制 / 生命周期 / 桶策略
  - 站点复制 (Site Replication)
  - 极简运维: 一个进程

  适用场景:
    - 私有云对象存储 (OpenStack Swift 替代)
    - 大数据存储底座 (Spark/Hive 数据湖)
    - 备份存储 (备份到 S3)
    - 容器镜像仓库底层
    - AI 训练数据存储
    - 应用静态资源

  vs 其他存储:
  ┌────────────┬──────────────┬──────────────┬──────────────┐
  │            │ MinIO        │ Ceph RGW     │ 传统 SAN/NAS │
  ├────────────┼──────────────┼──────────────┼──────────────┤
  │ 接口       │ S3           │ S3/RADOSGW   │ 块/文件       │
  │ 部署       │ 极简 (1 进程)│ 复杂 (MON/OSD)│ 硬件绑定      │
  │ 数据保护   │ 纠删码       │ 多副本/EC    │ RAID          │
  │ 扩展       │ 加节点加盘    │ 加 OSD       │ 换硬件        │
  │ 运维       │ 简单          │ 中等          │ 厂商服务      │
  │ 适合       │ 中小/云原生   │ 大规模统一存储│ 传统企业      │
  └────────────┴──────────────┴──────────────┴──────────────┘
```

### 1.2 纠删码 (Erasure Coding) 原理

```
纠删码是 MinIO 数据保护的基石:

  概念:
    数据分片 (Data Shards) + 校验分片 (Parity Shards)
    任意丢失 ≤ Parity 个分片, 数据完整可读

  默认配置:
    分片数 = 节点数 × 每节点驱动器数
    数据块 = 分片数 / 2
    校验块 = 分片数 / 2          (默认 50% 冗余)

  示例: 4 节点 × 4 盘 = 16 个分片
    data = 8, parity = 8
    允许任意 8 个分片丢失 (≈ 2 个节点全挂)

  示例: 8 节点 × 8 盘 = 64 个分片
    data = 32, parity = 32
    允许任意 32 个分片丢失 (≈ 4 个节点全挂)

  可调参数 (--erasure-set-parity):
    2  / 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10 / 11 / 12 / 13 / 14 / 15 / 16
    默认 N/2 (N = 总盘数), 最小值 2

  容量计算:
    可用容量 = 总容量 × (data / (data + parity))
    默认 parity=N/2 → 可用 50%
    parity=4 (8+4) → 可用 66.7%
    parity=2 (6+2) → 可用 75%

  性能影响:
    parity 越高 → 冗余越高, 写入开销越大, 可用容量越小
    生产建议:
      - 冷数据: parity 高 (4-6)
      - 热数据: parity 低 (2-4)
      - 节点可靠性差: parity 高

  位衰减 (Bit Rot) 防护:
    每 30 天自动扫描数据块
    发现损坏自动用校验块修复 (无需人工)
```

### 1.3 数据写入路径

```
对象写入流程:

  Client → mc cp / S3 PUT
      ↓
  MinIO Server (任意节点, 自动路由)
      ↓
  对象分片: 数据 → data1..dataN, 校验 → parity1..parityM
      ↓
  分片分布 (每盘最多 1 个分片):
    node1/data1  node2/data2  node3/data3 ... nodeN/dataN
    node1/p1     node2/p2     ...              nodeM/pM
      ↓
  全部写入成功 → 返回 200 OK

  数据布局 (Erasure Set):
    - 每 16 个驱动器组成一个 Erasure Set (固定)
    - 数据分片分布在同一个 Erasure Set 内
    - 读数据: 只需 data+parity 中任意 data 个分片
    - 写数据: 需要 data+parity 全部成功? 否!
      → 最少需要 quorum = data+1 个分片成功即可写
```

### 1.4 Quorum 与一致性

```
Quorum (法定人数) 规则:

  写入 (Write Quorum):
    需要 N = data + 1 个分片成功
    示例 8+8: 9 个分片成功即可写成功

  读取 (Read Quorum):
    需要 data 个分片即可读
    示例 8+8: 8 个分片即可完整读取

  集群可用性判定:
    MinIO 集群可用 ⇔ 存活驱动器数 ≥ data + 1
    即: 最多容忍 (总盘数 - data - 1) 块盘故障

  节点可用性:
    节点故障 ≠ 集群故障!
    只要存活分片 ≥ data, 数据可读
    只要存活分片 ≥ data+1, 数据可写

  举例 4 节点 × 4 盘 (8+8):
    1 节点全挂 (4 盘)  → 仍可读可写 ✅
    2 节点全挂 (8 盘)  → 仍可读 (恰好 8 分片) ✅ 不可写 ❌
    3 节点全挂        → 数据不可读 ❌ (需 8+1)

  注意: 节点故障比盘故障更难恢复, 因为盘分布在同一节点
```

### 1.5 关键概念速览

```
术语:
  Erasure Set:  16 个盘一组, 数据分布单位
  Data Shard:   数据分片
  Parity Shard: 校验分片
  Quorum:       读写所需最少分片数
  Heal:         自愈过程 (用校验块修复数据块)
  Drive:        数据盘 (xfs 格式)
  Pool:         一个 server 命令行里的所有盘 = 1 个池
  Node:         一台服务器 = 一个 minio server 进程

关键限制:
  - 总盘数必须是 2 的倍数且 ≥ 4 (4, 8, 16, 32, 64...)
  - 每个节点盘数必须一致
  - 每节点最多 32 盘
  - 节点数 * 盘数 ≤ 总盘数上限 (生产 64 盘内)
  - 盘一旦格式化 (Format) 不可换位, 否则数据丢失!
```

---

## 二、部署

### 2.1 单机部署 (开发/测试)

```bash
# === 下载 ===
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
mv minio /usr/local/bin/

# === 创建数据目录 ===
mkdir -p /data/minio
useradd -r -s /sbin/nologin minio
chown -R minio:minio /data/minio

# === systemd ===
cat > /etc/systemd/system/minio.service << 'EOF'
[Unit]
Description=MinIO Object Storage
After=network.target

[Service]
User=minio
Group=minio
EnvironmentFile=-/etc/default/minio
ExecStart=/usr/local/bin/minio server $MINIO_VOLUMES --address $MINIO_ADDRESS --console-address $MINIO_CONSOLE
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/default/minio << 'EOF'
# 数据目录 (可多个)
MINIO_VOLUMES="/data/minio"

# 服务端口
MINIO_ADDRESS=":9000"
MINIO_CONSOLE=":9001"

# root 用户 (生产用 [REDACTED] 环境变量注入)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=ChangeMe@2026
EOF

systemctl daemon-reload
systemctl enable --now minio

# 验证
mc alias set local http://127.0.0.1:9000 minioadmin 'ChangeMe@2026'
mc admin info local
mc ls local
```

### 2.2 分布式部署 (生产, 4 节点)

```
生产推荐:
  - 4 节点起步 (每节点 4-8 盘)
  - 节点间万兆网络
  - 每节点独立 UPS / 独立电源
  - 盘使用 xfs 格式
  - 节点盘数一致!
```

```bash
# === 4 节点 × 4 盘 部署 ===
# 节点: node1~node4 (10.0.1.11~14)
# 每节点: /data1 /data2 /data3 /data4 (4 块 xfs 盘)

# 1. 各节点准备
# 挂载盘 (fstab 加 noatime)
/dev/sdb1  /data1  xfs  defaults,noatime  0 0
/dev/sdc1  /data2  xfs  defaults,noatime  0 0
/dev/sdd1  /data3  xfs  defaults,noatime  0 0
/dev/sde1  /data4  xfs  defaults,noatime  0 0

# 2. 各节点下载 minio 二进制 (同版本!)
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x /usr/local/bin/minio

# 3. 各节点 systemd (EnvironmentFile 相同)
cat > /etc/systemd/system/minio.service << 'EOF'
[Unit]
Description=MinIO Object Storage
After=network.target

[Service]
User=minio
Group=minio
EnvironmentFile=-/etc/default/minio
ExecStart=/usr/local/bin/minio server $MINIO_VOLUMES --address $MINIO_ADDRESS --console-address $MINIO_CONSOLE
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# 4. 节点1 配置 (其余节点同样配置)
cat > /etc/default/minio << 'EOF'
# 所有节点的所有盘 (重要! 每节点命令行一致)
MINIO_VOLUMES="http://node1:9000/data{1...4} http://node2:9000/data{1...4} http://node3:9000/data{1...4} http://node4:9000/data{1...4}"

MINIO_ADDRESS=":9000"
MINIO_CONSOLE=":9001"

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD='[REDACTED]'
EOF

# 5. 全部节点启动
systemctl daemon-reload
systemctl enable --now minio

# 6. 验证
mc alias set prod http://node1:9000 minioadmin '[REDACTED]'
mc admin info prod
# ●  node1:9000
#   UPTIME 3h, CPU 5%, MEM 12GB
#   4 drives online, 0 drives offline
#   ...
# ●  node2:9000
#   4 drives online, 0 drives offline
# ●  node3:9000
#   4 drives online, 0 drives offline
# ●  node4:9000
#   4 drives online, 0 drives offline
# 16 drives online, 0 drives offline
# RAW: 48 TiB, USED: 12 TiB (25%), QUOTA: 0
# EC: 8+8, 16 drives, 8 online
# 集群已就绪!

# 7. 客户端接入
mc config host add prod http://node1:9000 minioadmin '[REDACTED]'
# 或负载均衡: 前端 Nginx/HAProxy 代理 4 节点
```

### 2.3 K8s 部署 (Operator / Helm)

```bash
# === 方式 1: Helm Chart (简单) ===
helm repo add minio https://operator.min.io/
helm repo update

helm install minio minio/minio \
  --namespace minio --create-namespace \
  --set rootUser=minioadmin \
  --set rootPassword='[REDACTED]' \
  --set mode=distributed \
  --set replicas=4 \
  --set drivesPerNode=4 \
  --set persistence.size=500Gi \
  --set resources.requests.memory=4Gi \
  --set resources.requests.cpu=2

# 方式 2: MinIO Operator (生产推荐, 支持租户隔离/升级/扩缩)
kubectl apply -f https://raw.githubusercontent.com/minio/operator/master/operator-k8s.yaml
kubectl get pods -n minio-operator

# 创建租户 (Tenant = 独立 MinIO 集群)
cat > tenant.yaml << 'EOF'
apiVersion: minio.min.io/v2
kind: Tenant
metadata:
  name: prod-tenant
  namespace: minio-tenant
spec:
  image: quay.io/minio/minio:RELEASE.2026-07-14T00-00-00Z
  credsSecret:
    name: minio-creds
  exposeServices:
    console: true
  pools:
  - name: pool-0
    servers: 4
    volumesPerServer: 4
    volumeClaimTemplate:
      metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 500Gi
  metrics:
    console: true
    prometheus: true
  log:
    audit: true
EOF

kubectl -n minio-tenant create secret generic minio-creds \
  --from-literal=accesskey=minioadmin \
  --from-literal=secretkey='[REDACTED]'

kubectl apply -f tenant.yaml
kubectl get tenant -n minio-tenant
```

---

## 三、健康检查与监控

### 3.1 mc admin 命令全家桶

```bash
# === 集群状态 ===
mc admin info prod
# 最常用! 一眼看出:
# - 在线/离线节点
# - 在线/离线盘
# - 容量使用
# - EC 配置

# 只看盘
mc admin info prod --json | jq '.drives'

# 服务器信息
mc admin server info prod

# === 性能检查 ===
# 测速 (读写)
mc admin perf prod
# 分区测速
mc admin perf speedtest prod --size 64MiB

# 延迟测试
mc admin latency --latency-test-time 30s prod

# === 服务状态 ===
mc admin service status prod
mc admin service restart prod       # 重启
mc admin service stop prod          # 停止

# === 日志 ===
mc admin console log prod           # 实时控制台日志
mc admin console log prod --type api
mc admin trace prod                 # 实时 API 请求跟踪 (排障神器!)
mc admin trace prod --path '/bucket/*' --status-code 4xx,5xx

# === 配置管理 ===
mc admin config get prod
mc admin config set prod notify_webhook endpoint=http://10.0.1.100:8080/webhook
mc admin config reload prod
```

### 3.2 盘健康状态识别

```bash
# 盘离线 (offline) 判断
mc admin info prod
# 输出中:
#   16 drives online, 0 drives offline
#   或
#   15 drives online, 1 drives offline
#   ● node3:9000/data2   ← 离线盘

# 详细 JSON
mc admin info prod --json | jq '.info.servers[] | {name, drives: [.drives[].state]}'

# 判断标准:
#   ok:        盘正常
#   offline:   盘挂掉 (IO 错误/掉电/文件系统损坏)
#   missing:   盘不存在 (路径没了)
#   corrupted: 元数据损坏

# 查看某节点盘
mc admin info prod --json | jq '.info.servers[] | select(.endpoint|contains("node3"))'
```

### 3.3 Prometheus 监控

```yaml
# === Prometheus 抓取 ===
scrape_configs:
  - job_name: minio
    metrics_path: /minio/v2/metrics/cluster
    scheme: http
    static_configs:
      - targets:
          - node1:9000
          - node2:9000
          - node3:9000
          - node4:9000
        labels:
          env: prod
  - job_name: minio-bucket
    metrics_path: /minio/v2/metrics/bucket
    static_configs:
      - targets: ['node1:9000']
```

```promql
# === 关键指标 ===

# 离线盘数 (核心!)
minio_cluster_drive_offline_total > 0

# 在线盘总数
minio_cluster_drive_online_total

# 集群健康 (0=不健康)
minio_cluster_health > 0

# 写入 quorum 丢失 (数据不可写!)
minio_cluster_write_quorum < 1

# 节点离线
minio_node_health < 1

# 桶对象数
minio_bucket_usage_total_objects
# 桶容量
minio_bucket_usage_total_bytes

# S3 API 错误率
sum(rate(minio_s3_requests_errors_total[5m])) / sum(rate(minio_s3_requests_total[5m]))

# 网络
rate(minio_s3_requests_incoming_total[5m])
```

```yaml
# === 告警规则 ===
groups:
- name: minio
  rules:
  - alert: MinIODriveOffline
    expr: minio_cluster_drive_offline_total > 0
    for: 2m
    labels: { severity: warning }
    annotations:
      summary: "MinIO {{ $labels.instance }} 有盘离线: {{ $value }} 块"

  - alert: MinIOClusterUnhealthy
    expr: minio_cluster_health < 1
    for: 1m
    labels: { severity: critical }
    annotations:
      summary: "MinIO 集群不健康!"

  - alert: MinIOWriteQuorumLost
    expr: minio_cluster_write_quorum < 1
    for: 30s
    labels: { severity: critical }
    annotations:
      summary: "MinIO 写入 quorum 丢失, 数据不可写!"

  - alert: MinIONodeDown
    expr: up{job="minio"} == 0
    for: 2m
    labels: { severity: warning }
    annotations:
      summary: "MinIO 节点 {{ $labels.instance }} 不可达"

  - alert: MinIOBucketUsageHigh
    expr: minio_bucket_usage_total_bytes > 80 * 1024^4  # 80TiB
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "MinIO 容量使用 > 80 TiB, 关注扩容"

  - alert: MinIODiskSpaceLow
    expr: minio_cluster_capacity_usable_total_bytes - minio_cluster_capacity_usable_free_bytes < 10 * 1024^4
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "MinIO 可用空间 < 10 TiB"
```

---

## 四、驱动器 (Drive) 故障恢复

### 4.1 故障场景与恢复原则

```
驱动器故障场景:

  A. 单盘 IO 错误 (最常见)
     - 盘老化/坏道/掉电
     - 状态: offline
     - 影响: 无 (quorum 足够)
     - 恢复: 换盘自动重建

  B. 盘文件系统损坏
     - xfs 元数据损坏
     - 状态: corrupted / offline
     - 恢复: 检查 → 格式化换盘

  C. 多盘同时故障
     - 掉电/背板故障
     - 只要离线盘 < parity, 数据安全
     - 恢复: 逐盘更换

  D. 所有盘故障 (极端)
     - 数据不可读
     - 恢复: 从备份/其他站点恢复

恢复核心原则:
  ✅ 新盘必须: 空盘, 无分区, 无数据
  ✅ 换盘后: MinIO 自动检测并重建 (无需手动触发)
  ✅ 重建期间: 集群正常服务 (性能略降)
  ✅ 恢复判定: mc admin info 显示盘 online + mc admin heal 无损坏
  ❌ 不要把旧盘数据拷到新盘
  ❌ 不要随意格式化仍在线但有告警的盘
  ❌ 不要用损坏盘继续写数据
```

### 4.2 单盘故障恢复实操

```bash
# === 场景: node3:/data2 盘 offline ===

# 1. 确认故障
mc admin info prod
# ● node3:9000
#   4 drives online, 0 drives offline   ← 需要确认是哪块
# 或
#   3 drives online, 1 drives offline   ← /data2 离线

# 查看具体盘
mc admin info prod --json | jq '.info.servers[] | select(.endpoint|contains("node3")) | .drives'

# 2. SSH 到节点检查物理盘
ssh node3
lsblk -f
# sdb1 xfs  /data1
# sdc1 xfs  /data2   ← 异常
# sdd1 xfs  /data3
# sde1 xfs  /data4

# 查看磁盘错误
dmesg | tail -30 | grep -i "error\|sdc"
smartctl -a /dev/sdc   # 看 Reallocated_Sector_Ct / Pending

# 3. 确认盘确实坏了 (IO 错误/硬件故障)

# 4. 卸载故障盘
umount /data2

# 5. 物理更换新盘 (或格式化原盘)
# 新盘要求: 空盘! 直接格式化即可 (MinIO 自己会格式化成它的格式)
mkfs.xfs /dev/sdc1
mount /dev/sdc1 /data2
chown minio:minio /data2

# 6. 检查挂载 (fstab 确保开机自动)
# /etc/fstab 已配置则无需操作

# 7. MinIO 自动检测新盘并重建 (无需重启服务!)
# 等待几秒后:
mc admin info prod
# 16 drives online, 0 drives offline

# 8. 验证数据自愈
mc admin heal prod --recursive --verbose
# ✔ ✔ ✔ 100% complete

# 9. 如果盘没自动上线:
# 检查日志
mc admin console log prod | grep -i "data2\|drive"
# 重启 minio 服务 (安全)
mc admin service restart prod
# 或单节点
ssh node3 systemctl restart minio
```

### 4.3 盘文件系统损坏恢复

```bash
# === 场景: 盘能识别但数据读不了 / corrupted ===

# 1. 状态确认
mc admin info prod --json | jq '.info.servers[] | select(.endpoint|contains("node3")) | .drives[] | select(.state != "ok")'

# 2. 尝试修复文件系统 (先备份重要信息)
ssh node3
umount /data2

# xfs 修复 (危险操作, 先确认是 xfs)
xfs_repair -n /dev/sdc1        # 检查 (只读)
xfs_repair /dev/sdc1           # 修复 (可能丢失损坏文件)

# ext4
e2fsck -f /dev/sdc1

# 3. 修复后挂载尝试
mount /dev/sdc1 /data2
ls /data2

# 4. 如果 MinIO 数据目录损坏无法识别:
#   直接按"换新盘"处理 (数据会从其他盘重建)
umount /data2
mkfs.xfs /dev/sdc1
mount /dev/sdc1 /data2
chown minio:minio /data2
# MinIO 自动重建该盘分片

# 注意:
# - 单个盘损坏: 直接换盘, 数据从 parity 自动恢复
# - 不要尝试手动复制分片! 可能破坏 erasure set 一致性
# - 重建期间建议降低写入压力
```

### 4.4 盘更换注意事项

```
换盘纪律 (重要!):

  1. 换盘前确认:
     - 该盘确实 offline (mc admin info)
     - 物理位置对应 (灯/槽位)
     - 新盘容量 ≥ 原盘容量

  2. 换盘过程:
     - 记录盘序列号 / 槽位 (避免换错)
     - 新盘保持空盘 (mkfs.xfs 后直接挂载)
     - 权限: chown minio:minio

  3. 换盘后:
     - 等 MinIO 自动重建 (大容量盘可能数小时)
     - 期间监控: mc admin info 盘状态
     - 重建完成: mc admin heal --recursive 确认 100%

  4. 禁止:
     - ❌ 用 RAID 卡做 RAID 后再给 MinIO (MinIO 自己管理冗余!)
     - ❌ 把旧盘数据 cp 到新盘
     - ❌ 换盘后改变挂载点名称 (/data2 不能变 /data5)
     - ❌ 在盘状态 offline 时格式化其它正常盘

  5. 硬件建议:
     - 盘位插满, 预留冷备盘
     - 每节点盘型号一致 (容量一致)
     - 企业级 SSD/NVMe (持久写入)
```

---

## 五、节点故障恢复

### 5.1 节点故障类型

```
节点故障场景:

  A. 进程崩溃
     - minio 进程挂 (OOM/panic)
     - systemd 自动重启
     - 影响: 无 (quorum 足够)

  B. 节点宕机 (断电/硬件故障)
     - 节点离线, 盘离线
     - 影响: 取决于 quorum
     - 恢复: 恢复节点电源/硬件, 自动重新加入

  C. 节点永久损坏 (主板/硬盘全损)
     - 需要换新节点
     - 恢复: 新节点加入, 数据自动重建

  D. 多节点同时故障 (机架掉电/网络分区)
     - 影响: 严重, 取决于存活 quorum
     - 恢复: 逐节点恢复, 检查数据完整性

节点故障判定 (4 节点 8+8 配置):
  1 节点挂: 可读可写 ✅ (12 盘存活 ≥ 9)
  2 节点挂: 可读 ❌可写 (8 盘 = data, 读刚好够)
  3 节点挂: 数据不可读 ❌ (4 盘 < 8)
```

### 5.2 节点宕机恢复 (临时故障)

```bash
# === 场景: node2 断电宕机 ===

# 1. 确认集群状态 (从其他节点)
mc admin info prod
# ● node1:9000  4 drives online
# ● node2:9000  4 drives offline   ← 节点整体离线
# ● node3:9000  4 drives online
# ● node4:9000  4 drives online
# 12 drives online, 4 drives offline
# EC: 8+8, 16 drives, 12 online → 可用 (可读可写)

# 2. 检查节点硬件
# 机房/远程: BMC/IPMI 看电源状态
ipmitool -I lanplus -H node2-bmc -U admin -P xxx power status
ipmitool -I lanplus -H node2-bmc -U admin -P xxx power on

# 3. 节点恢复后
ssh node2
systemctl status minio
# 若没自启: systemctl start minio

# 4. 确认重新加入集群
mc admin info prod
# 16 drives online, 0 drives offline

# 5. 数据自愈 (节点离线期间写的数据分片)
mc admin heal prod --recursive --verbose
# 节点离线期间:
# - 其他节点写入的数据, 需要把分片补到 node2 的盘上
# - heal 自动完成

# 6. 特别检查: 节点离线期间删改的对象
mc admin info prod --json | jq '.info.objects'
```

### 5.3 节点永久损坏 (换新节点)

```bash
# === 场景: node3 主板烧毁, 需换新节点 ===

# 前提: 其余 3 节点 (12 盘) 存活, 数据可读
# EC 8+8: 12 盘在线 → 可读可写 (写入 quorum=9 满足)

# 1. 确认新节点就绪
# - 同版本 MinIO 二进制
# - 相同盘数 / 相同盘容量
# - 网络可达 (ping / 端口 9000)

# 2. 新节点配置
# 在 node3-new 上配置 /etc/default/minio
# 注意: MINIO_VOLUMES 必须与其他节点完全一致!
cat > /etc/default/minio << 'EOF'
MINIO_VOLUMES="http://node1:9000/data{1...4} http://node2:9000/data{1...4} http://node3-new:9000/data{1...4} http://node4:9000/data{1...4}"
MINIO_ADDRESS=":9000"
MINIO_CONSOLE=":9001"
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD='[REDACTED]'
EOF

# 3. 修改 DNS / hosts (如果使用主机名)
# 把 node3 解析到新 IP
# 或直接改其他节点 /etc/hosts
# 10.0.1.13  node3   ← 保持主机名不变最简单 (换 IP 不换名)

# 4. 启动新节点
systemctl daemon-reload
systemctl enable --now minio

# 5. 确认加入
mc admin info prod
# ● node3:9000
#   4 drives online, 0 drives offline   ← 新盘自动格式化并加入

# 6. 数据自动重建 (从其他 12 盘补分片)
mc admin heal prod --recursive --verbose
# 大集群重建可能需要数小时, 期间服务正常

# 7. 验证
mc ls prod/bucket | head
mc admin info prod | grep drives
```

### 5.4 多节点故障恢复策略

```bash
# === 场景: 2 节点同时挂 (4 节点集群 8+8) ===
# 存活 2 节点 = 8 盘 = 恰好 data 数 → 可读不可写!

# 1. 立即停止写入 (否则写失败堆积)
# 业务侧暂停写入任务

# 2. 优先恢复 1 个节点 (让集群恢复可写)
# 恢复 node2 后: 12 盘在线 → 可写

# 3. 再恢复第二个节点

# 4. 全节点恢复后 heal
mc admin heal prod --recursive --verbose

# 5. 如果 3 节点挂 (仅剩 1 节点 4 盘):
#   数据不可读 → 这不是"恢复"问题, 是"灾难恢复"问题
#   从备份恢复 (见第八章)
#   或等节点恢复后, 用残留数据 + 备份合并

# 关键经验:
# - 节点故障恢复顺序: 先恢复能恢复的, 保持 quorum
# - 不要在 quorum 不足时做任何写操作
# - 节点恢复后立即 heal
# - 建议 5 节点集群 (冗余更高): 5 节点挂 2 个仍可写 (15盘≥9)
```

### 5.5 节点故障期间的运维动作

```
节点故障期间 (单节点挂):

  读操作: 正常 (quorum 满足)
  写操作: 正常 (quorum 满足)
  性能:  下降 (分片从 12 盘读写)

  注意事项:
  ✅ 可以继续服务, 但建议降低写入 (重建压力)
  ✅ 观察其他节点盘健康 (避免二次故障)
  ✅ 监控磁盘空间 (重建需要空间)
  ❌ 不要重启其他正常节点 (减少风险窗口)
  ❌ 不要在这个窗口做扩容/降级操作

  恢复后:
  ✅ 立即 mc admin heal 全量检查
  ✅ 检查监控告警恢复
  ✅ 记录故障时间/原因/处理过程 (复盘)
```

---

## 六、数据完整性检查与修复 (Heal)

### 6.1 Heal 机制

```
Heal (自愈) 机制:

  自动 Heal:
    - 新盘加入后自动重建分片
    - 节点恢复后自动补齐
    - 定期位衰减扫描自动修复

  手动 Heal:
    - 集群恢复正常后建议全量检查
    - 怀疑数据损坏时

  Heal 检查内容:
    - 分片缺失 → 从其他分片重建
    - 分片损坏 (checksum 不匹配) → 用 parity 修复
    - 元数据不一致 → 修复

  Heal 类型:
    - 深度扫描 (deep): 读全部数据块校验
    - 常规扫描: 只检查元数据
```

### 6.2 Heal 命令

```bash
# === 全集群 heal ===
mc admin heal prod --recursive
# 输出进度:
# ✔ ✔ ✔ 100.0% complete

# 显示详细修复内容
mc admin heal prod --recursive --verbose
# ✔ node3:9000/data2/data/shards/...

# 深度扫描 (读所有数据, 慢但彻底)
mc admin heal prod --recursive --scan-deep

# 只 heal 某桶
mc admin heal prod --bucket mybucket --recursive

# heal 特定前缀
mc admin heal prod --bucket mybucket --prefix logs/ --recursive

# 指定并发
mc admin heal prod --recursive --max-io 8

# 只显示异常
mc admin heal prod --recursive --json | jq 'select(.heal != null and .heal.state != "ok")'

# === 查看 heal 状态 ===
mc admin heal prod
# 已修复对象数 / 待修复对象数

# === 定期 heal 建议 ===
# 每季度深度扫描一次 (低峰期)
# 每月常规扫描一次
# 有故障恢复后立即全量
```

### 6.3 Bit Rot 位衰减防护

```
位衰减 (Bit Rot):
  磁盘物理损坏导致数据翻转, 不报错但数据变了

  MinIO 防护:
    - 写入时: 数据块 + checksum (SHA-256)
    - 读取时: 校验 checksum, 不一致自动用 parity 重建
    - 定期: 30 天自动深度扫描 (bit rot 检测)

  验证:
    - 读对象时 MinIO 自动校验 (静默修复)
    - mc admin heal --scan-deep 主动发现

  实践:
    - 定期深度 heal (发现潜在 bit rot)
    - 重要数据开启版本控制 (可回滚)
    - 备份策略兜底 (多副本)
```

---

## 七、集群级故障与重建

### 7.1 集群完全不可用 (灾难)

```
场景: 全部节点宕机 / 数据中心事故 / 严重错误操作

  MinIO 数据本身不丢:
    - 数据在盘的 xfs 文件系统上 (MinIO 元数据也在盘上)
    - 只要盘还在, 数据就在
    - 集群重新启动即可恢复

  恢复路径:
    1. 恢复全部节点电源/网络 → 启动 minio → 集群自动重组
    2. 若盘没动, 数据直接可用 (无需重建)
    3. 若部分盘损坏 → 换盘自动重建
    4. 若节点永久损坏 → 新节点替换 (见 5.3)

  关键: 只要磁盘没有物理损坏, 集群可整体恢复
        真灾难 (全盘损毁) → 依赖备份 (第八章)
```

```bash
# === 集群重启恢复 ===

# 1. 恢复所有节点电源
# 2. 启动所有节点的 minio (顺序无所谓, 会自动发现)
for node in node1 node2 node3 node4; do
  ssh $node systemctl start minio
done

# 3. 确认集群
mc admin info prod
# 16 drives online, 0 drives offline

# 4. 数据完整性检查
mc admin heal prod --recursive --verbose

# 5. 业务验证
mc ls prod/mybucket
mc stat prod/mybucket/important-file
```

### 7.2 池 (Pool) 与扩容

```bash
# === MinIO 扩容: 加节点 ===
# 方式: 在 MINIO_VOLUMES 中追加新节点
# 注意: 扩容 = 新加一个 Pool, 旧数据不自动迁移!

# 原配置 (4 节点):
MINIO_VOLUMES="http://node1:9000/data{1...4} http://node2:9000/data{1...4} http://node3:9000/data{1...4} http://node4:9000/data{1...4}"

# 扩容到 6 节点 (追加):
MINIO_VOLUMES="http://node1:9000/data{1...4} http://node2:9000/data{1...4} http://node3:9000/data{1...4} http://node4:9000/data{1...4} http://node5:9000/data{1...4} http://node6:9000/data{1...4}"

# 所有节点同步修改配置并重启
# 新数据会写到新 Pool, 旧数据在原 Pool

# 查看 Pool 状态
mc admin info prod
# Pool 1: 16 drives
# Pool 2: 8 drives

# 迁移数据到新池 (可选)
mc admin rebalance prod    # 后台迁移
mc admin rebalance status prod

# 停用池 (下架)
mc admin decommission start prod pool-0
mc admin decommission status prod
mc admin decommission complete prod pool-0
```

### 7.3 节点替换的完整流程 (演练)

```bash
# === 节点替换演练 (node3 → node3-new) ===

# 阶段 1: 准备
# 1. 新节点装好系统 + MinIO 同版本二进制
# 2. 新节点盘数/容量与原节点一致
# 3. 网络互通

# 阶段 2: 旧节点下线
# 1. 业务低峰期操作
# 2. 停止旧节点
ssh node3 systemctl stop minio
# 3. 确认集群仍健康 (12 盘在线)
mc admin info prod

# 阶段 3: 新节点接入
# 1. hosts/DNS 把 node3 指向新 IP
# 2. 新节点启动 minio
ssh node3-new systemctl start minio
# 3. 确认加入
mc admin info prod | grep node3

# 阶段 4: 数据重建
# 1. 自动重建 (无需操作)
# 2. 监控重建进度
watch -n 30 'mc admin info prod | grep drives'
# 3. 完成后 heal 验证
mc admin heal prod --recursive --verbose

# 阶段 5: 清理
# 旧节点盘做数据销毁 (防止泄露)
# 记录变更
```

### 7.4 严重错误操作恢复

```
常见错误操作及恢复:

  1. 误删盘目录/格式化在线盘
     → 立即停止该盘服务, 用 parity 重建
     → 其他盘不要动

  2. 误改 MINIO_VOLUMES (盘路径变化)
     → 立即恢复原配置 (盘顺序不能变)
     → 若已启动: 可能产生新 Pool, 恢复配置后重启

  3. 误删 bucket / 对象
     → 开启版本控制可恢复 (见 8.4)
     → 或从备份恢复 (mc mirror --overwrite)

  4. 误改 root 密码
     → 停服务, 修改 /etc/default/minio, 重启

  5. 配置漂移 (各节点 MINIO_VOLUMES 不一致)
     → 立即统一配置, 重启所有节点
     → 检查: mc admin info 是否每个节点显示相同 Pool

  6. 时间不同步 (节点间时钟偏差 > 15 分钟)
     → 同步 NTP!
     → chronyc makestep

  7. 网络分区 (部分节点互不可达)
     → 检查防火墙/VLAN
     → 恢复网络, 自动重组

  统一恢复口诀:
    先看 quorum (mc admin info)
    再 heal (mc admin heal)
    最后验证 (mc ls / mc stat)
```

---

## 八、数据备份方案

### 8.1 备份策略总览

```
MinIO 备份层次:

  第一层 (存储内保护): 纠删码 (防盘故障)
  第二层 (存储内保护): 版本控制 (防误删/覆盖)
  第三层 (站点级):    mc mirror / rclone 镜像到第二站点
  第四层 (站点级):    mc replicate 实时站点复制
  第五层 (异地):      备份到云/磁带/归档

  备份目标矩阵:

  ┌──────────────┬──────────┬──────────┬──────────┬─────────┐
  │ 场景          │ 方案      │ 实时性    │ 恢复点   │ 成本    │
  ├──────────────┼──────────┼──────────┼──────────┼─────────┤
  │ 防误删        │ 版本控制  │ 即时      │ 秒级     │ 最低    │
  │ 容灾(第二站点) │ 站点复制  │ 近实时    │ 秒级     │ 中      │
  │ 日常备份      │ mc mirror │ 定时      │ 小时级   │ 低      │
  │ 异地备份      │ rclone    │ 定时      │ 小时级   │ 中      │
  │ 归档          │ 生命周期  │ 自动      │ 天级     │ 低      │
  └──────────────┴──────────┴──────────┴──────────┴─────────┘

  推荐组合 (生产):
    纠删码 8+8
    + 版本控制 (全部重要桶)
    + 每日 mc mirror 到备份服务器 (独立 MinIO)
    + 每周异地 (rclone 到云/磁带)
    + 每月恢复演练
```

### 8.2 mc mirror 镜像备份

```bash
# === 场景: 备份 prod 到 backup 集群 (异地 MinIO) ===
# prod: 生产集群 (10.0.1.x)
# backup: 备份集群 (10.0.2.x, 独立机房)

# 1. 配置别名
mc alias set prod http://node1:9000 minioadmin '[REDACTED]'
mc alias set backup http://backup1:9000 minioadmin '[REDACTED]'

# 2. 全量镜像 (一次性)
mc mirror --overwrite prod/mybucket backup/mybucket
# --overwrite: 覆盖目标已有文件
# --remove:    删除目标多余文件 (完全同步)
# --watch:     持续监听变更 (实时增量)

# 3. 增量同步 (日常定时)
mc mirror --overwrite --remove prod/mybucket backup/mybucket

# 4. 实时同步 (后台进程)
mc mirror --watch --overwrite prod/mybucket backup/mybucket &
# 或 systemd 服务

# 5. 只同步新增 (不删除目标)
mc mirror prod/mybucket backup/mybucket

# 6. 指定前缀
mc mirror prod/mybucket/logs/ backup/mybucket/logs/

# 7. 排除
mc mirror prod/mybucket backup/mybucket --exclude "*.tmp"

# 8. 定时任务
cat > /usr/local/bin/minio-backup.sh << 'EOF'
#!/bin/bash
set -euo pipefail

LOG=/var/log/minio-backup-$(date +%Y%m%d).log
export PATH=/usr/local/bin:$PATH

echo "=== MinIO Backup $(date) ===" >> ${LOG}

# 全量备份 (每日)
mc mirror --overwrite --remove \
  prod/backup-data backup/backup-data >> ${LOG} 2>&1

# 增量备份 (每小时由 cron 调)
# mc mirror --overwrite prod/hot backup/hot >> ${LOG} 2>&1

# 备份桶列表
mc ls prod | awk '{print $NF}' > /tmp/bucket-list.txt

echo "=== Done $(date) ===" >> ${LOG}

# 通知
# curl -X POST 'https://qyapi.weixin.qq.com/...' -d '{"msgtype":"text","text":{"content":"MinIO 备份完成"}}'
EOF
chmod +x /usr/local/bin/minio-backup.sh

# cron: 每日 2:00 全量, 每小时增量
# 0 2 * * * /usr/local/bin/minio-backup.sh
# 0 * * * * mc mirror --overwrite prod/hot backup/hot

# 9. 恢复 (反向)
mc mirror --overwrite backup/mybucket prod/mybucket

# 10. 验证备份
mc ls backup/mybucket
mc stat backup/mybucket/important/file
mc diff prod/mybucket backup/mybucket    # 对比差异
```

### 8.3 mc replicate 站点复制 (实时容灾)

```bash
# === 场景: 生产集群实时复制到灾备集群 ===
# 需求: RPO ≈ 0 (秒级), RTO 分钟级

# 1. 两个集群都要有复制用户 (admin 即可)

# 2. 目标集群创建复制专用桶
mc mb backup/site-repl
# 或复制全部桶 (--replicate 所有)

# 3. 配置复制规则
mc replicate add prod/mybucket \
  --remote-bucket http://backup1:9000/site-repl \
  --access-key minioadmin \
  --secret-key '[REDACTED]' \
  --replicate "delete,delete-marker,existing-objects"
# --replicate 选项:
#   delete:            复制删除操作
#   delete-marker:     复制删除标记
#   existing-objects:  复制已有对象
#   new-objects:       复制新对象 (默认)
#   replica-metadata:  复制元数据

# 4. 查看复制状态
mc replicate status prod/mybucket
mc replicate info prod/mybucket

# 5. 故障切换 (灾备集群接管)
# 备份集群读
mc ls backup/site-repl
# 把业务流量切到 backup 集群
# 原集群恢复后: 反向复制或重做 mirror

# 6. 双向复制 (多活, 需版本控制支持)
mc mb prod/bucket1 --with-versioning
mc mb backup/bucket2 --with-versioning
mc replicate add prod/bucket1 \
  --remote-bucket http://backup1:9000/bucket2 \
  --access-key minioadmin --secret-key '[REDACTED]' \
  --replicate "delete,delete-marker"
mc replicate add backup/bucket2 \
  --remote-bucket http://prod1:9000/bucket1 \
  --access-key minioadmin --secret-key '[REDACTED]' \
  --replicate "delete,delete-marker"

# 注意:
# - 站点复制 (Site Replication) 更高级: 管理层面也同步
mc admin replicate add prod backup --peer-name backup-peer
mc admin replicate info prod
```

### 8.4 版本控制 (防误删/覆盖)

```bash
# === 开启版本控制 ===
# 创建桶时开启
mc mb prod/mybucket --with-versioning

# 已有桶开启
mc version enable prod/mybucket
mc version info prod/mybucket

# === 版本管理 ===
# 查看对象版本
mc ls prod/mybucket --versions

# 查看历史版本
mc ls --versions prod/mybucket/file.txt
# [2026-07-14 10:00:00 CST] 12KB v1  file.txt
# [2026-07-14 12:30:00 CST] 12KB v2  file.txt

# 回滚到指定版本
mc cp prod/mybucket/file.txt@v1 ./file.txt
mc cp ./file.txt prod/mybucket/file.txt

# 删除指定版本
mc rm prod/mybucket/file.txt@v1

# 保留策略 (对象锁定, 防篡改)
mc retention set prod/mybucket --default GOVERNANCE 30d
# GOVERNANCE: 治理 (可临时解除)
# COMPLIANCE: 合规 (不可解除, 直到过期)

# 版本控制最佳实践:
# 1. 重要桶全部开启
# 2. 配置生命周期清理旧版本 (见 8.5)
# 3. 结合锁定防勒索 (Ransomware)
# 4. 版本数量监控 (避免膨胀)
mc ls prod/mybucket --versions --recursive | wc -l
```

### 8.5 生命周期管理

```json
// ilm.json — 生命周期规则
{
  "Rules": [
    {
      "ID": "logs-expire",
      "Status": "Enabled",
      "Filter": {"Prefix": "logs/"},
      "Expiration": {"Days": 30}
    },
    {
      "ID": "backup-tier",
      "Status": "Enabled",
      "Filter": {"Prefix": "archive/"},
      "Transition": {
        "Days": 90,
        "StorageClass": "GLACIER",
        "RequestedDate": true
      }
    },
    {
      "ID": "old-versions",
      "Status": "Enabled",
      "Filter": {"Prefix": "data/"},
      "NoncurrentVersionExpiration": {
        "NewerNoncurrentVersions": 5,
        "NoncurrentDays": 30
      }
    }
  ]
}

// 应用规则
mc ilm import prod/mybucket < ilm.json

// 查看/删除规则
mc ilm rule list prod/mybucket
mc ilm rule remove prod/mybucket --id logs-expire
```

### 8.6 rclone 备份到异地/云

```bash
# === rclone (万能同步工具) ===

# 1. 安装
curl https://rclone.org/install.sh | sudo bash

# 2. 配置 MinIO 远程
rclone config
# n) New remote
# name: minio-prod
# type: s3
# provider: Minio
# endpoint: http://node1:9000
# access_key_id: minioadmin
# secret_access_key: ...

# 3. 列出
rclone lsd minio-prod:

# 4. 备份到本地磁盘
rclone sync minio-prod:mybucket /backup/minio/mybucket \
  --progress --transfers 16 --checkers 16

# 5. 本地备份到 MinIO (反向)
rclone sync /backup/minio minio-backup:backup \
  --progress --transfers 16

# 6. 定时备份
cat > /etc/systemd/system/rclone-minio-backup.service << 'EOF'
[Unit]
Description=rclone MinIO backup
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/rclone sync minio-prod:backup-data /backup/minio/backup-data --transfers 16
EOF

cat > /etc/systemd/system/rclone-minio-backup.timer << 'EOF'
[Unit]
Description=Daily MinIO backup

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl enable --now rclone-minio-backup.timer

# 7. 备份验证
rclone check minio-prod:backup-data /backup/minio/backup-data
# 输出: 0 differences found

# 8. 恢复
rclone sync /backup/minio/backup-data minio-prod:backup-data --progress
```

### 8.7 元数据与配置备份

```bash
# === 配置文件备份 ===
# MinIO 配置存储在集群内 (通过 API), 但也应导出

# 导出配置
mc admin config export prod > minio-config-$(date +%Y%m%d).txt

# 导入配置
mc admin config import prod < minio-config.txt

# === 桶策略备份 ===
# 导出所有桶策略
for bucket in $(mc ls prod | awk '{print $NF}'); do
  mc anonymous get-json prod/${bucket} > policy-${bucket}.json 2>/dev/null
  mc replicate status prod/${bucket} > repl-${bucket}.txt 2>/dev/null
  mc ilm rule list prod/${bucket} > ilm-${bucket}.txt 2>/dev/null
done

# === 用户/权限备份 ===
mc admin user list prod > users.txt
mc admin policy list prod > policies.txt
# 定期归档到 git 仓库

# === 完整备份清单 (脚本) ===
cat > /usr/local/bin/minio-meta-backup.sh << 'EOF'
#!/bin/bash
# 配置 + 策略 + 用户备份
BACKUP=/backup/minio-meta
DATE=$(date +%Y%m%d)
mkdir -p ${BACKUP}/${DATE}

mc admin config export prod > ${BACKUP}/${DATE}/config.txt
mc admin user list prod > ${BACKUP}/${DATE}/users.txt
mc admin policy list prod > ${BACKUP}/${DATE}/policies.txt

for bucket in $(mc ls prod | awk '{print $NF}'); do
  mc anonymous get-json prod/${bucket} > ${BACKUP}/${DATE}/policy-${bucket}.json 2>/dev/null
  mc ilm rule list prod/${bucket} > ${BACKUP}/${DATE}/ilm-${bucket}.txt 2>/dev/null
done

# 同步到备份节点
rclone sync ${BACKUP} minio-backup:meta-backup
find ${BACKUP} -type d -mtime +30 -exec rm -rf {} +
EOF
```

---

## 九、备份恢复演练

### 9.1 单桶恢复

```bash
# === 场景: 误删 bucket 中对象 ===

# 有版本控制:
mc ls --versions prod/mybucket/deleted-file.txt
mc cp prod/mybucket/deleted-file.txt@v1 ./restored.txt
mc cp ./restored.txt prod/mybucket/deleted-file.txt

# 无版本控制 → 从备份恢复
mc mirror --overwrite backup/mybucket/deleted-file.txt prod/mybucket/deleted-file.txt

# === 场景: 误删整个 bucket ===
# 重新创建
mc mb prod/mybucket
# 从备份恢复
mc mirror --overwrite backup/mybucket prod/mybucket
# 恢复策略/生命周期 (见 8.7 备份的 meta)
```

### 9.2 整集群恢复 (从备份集群)

```bash
# === 场景: 生产集群完全损毁, 用备份集群恢复 ===

# 1. 准备新生产集群 (全新节点)
# 或直接用备份集群临时接管

# 2. 方案 A: 备份集群直接接管
# 修改 DNS/负载均衡指向 backup 集群
# 业务恢复 (只读优先)

# 3. 方案 B: 重建生产集群后从备份恢复
# 新集群部署完成
mc alias set new-prod http://new-node1:9000 minioadmin '[REDACTED]'

# 全量恢复
mc mirror --overwrite --remove backup/mybucket new-prod/mybucket

# 恢复元数据 (用户/策略/生命周期)
mc admin config export backup > config.txt
mc admin config import new-prod < config.txt

# 4. 验证
mc ls new-prod/mybucket
mc stat new-prod/mybucket/important/file
mc diff backup/mybucket new-prod/mybucket   # 应无差异

# 5. 恢复后:
# - 开启版本控制
# - 验证访问权限
# - 业务切流
```

### 9.3 恢复演练计划

```
定期演练 (建议每季度):

  演练 1: 盘故障演练
    - 拔一块盘 (或 stop 一个 minio 进程)
    - 验证: quorum 不受影响, 数据可读写
    - 换盘 → 自动重建 → heal 完成

  演练 2: 节点故障演练
    - 停一个节点 minio 服务 30 分钟
    - 验证: 读写正常 (性能下降)
    - 恢复节点 → heal

  演练 3: 备份恢复演练
    - 从备份集群恢复一个测试桶到临时集群
    - 验证: 数据完整性 (mc diff)
    - 记录 RTO (恢复时间)

  演练 4: 版本恢复演练
    - 修改一个文件 → 用版本回滚
    - 验证: 回滚正确

  演练 5: 完整容灾演练 (每半年)
    - 模拟生产集群全毁
    - 备份集群接管 → 业务验证
    - 恢复生产集群 → 数据回迁
    - 全程记录时间线

  演练记录:
    - 场景 / 操作 / 耗时 / 结果
    - 发现的问题 / 改进项
```

---

## 十、日常运维

### 10.1 巡检脚本

```bash
#!/bin/bash
# minio-check.sh — MinIO 每日巡检

LOG=/var/log/minio-check-$(date +%Y%m%d).log
MC=/usr/local/bin/mc
ALIAS=prod

exec > ${LOG} 2>&1
echo "=== MinIO Daily Check $(date) ==="

echo
echo "=== 1. 集群状态 ==="
${MC} admin info ${ALIAS}

echo
echo "=== 2. 盘健康 ==="
${MC} admin info ${ALIAS} --json | jq -r '
  .info.servers[] | .endpoint as $ep |
  .drives[] | select(.state != "ok") | 
  "\($ep) \(.path) state=\(.state)"'
echo "offline drives: $(${MC} admin info ${ALIAS} --json | jq '[.info.servers[].drives[] | select(.state != "ok")] | length')"

echo
echo "=== 3. 节点健康 ==="
${MC} admin info ${ALIAS} --json | jq -r '.info.servers[] | "\(.endpoint): drives=\(.drives | length) online=\([.drives[] | select(.state=="ok")] | length)"'

echo
echo "=== 4. 容量 ==="
${MC} admin info ${ALIAS} --json | jq '.info.storage'

echo
echo "=== 5. 桶列表 ==="
${MC} ls ${ALIAS}

echo
echo "=== 6. 大桶 TOP ==="
for b in $(${MC} ls ${ALIAS} | awk '{print $NF}'); do
  size=$(${MC} du ${ALIAS}/${b} 2>/dev/null | awk '{print $1}')
  echo "${b}: ${size}"
done | sort -t: -k2 -rh | head -10

echo
echo "=== 7. 最近错误日志 ==="
${MC} admin console log ${ALIAS} --json 2>/dev/null | jq -r '
  .[] | select(.message | test("error|failed|offline")) | 
  "\(.time) \(.api.name) \(.message)"' 2>/dev/null | tail -20

echo
echo "=== 8. 备份检查 ==="
ls -lh /backup/minio-meta/ | tail -5
${MC} ls backup/backup-data 2>/dev/null | head -5

echo
echo "=== 9. 版本/生命周期检查 ==="
for b in $(${MC} ls ${ALIAS} | awk '{print $NF}'); do
  v=$(${MC} version info ${ALIAS}/${b} 2>/dev/null | grep -c "enabled")
  [ "${v}" -eq 0 ] && echo "⚠ bucket ${b} 未开启版本控制"
done

echo
echo "=== 巡检完成 $(date) ==="
```

### 10.2 常用运维操作

```bash
# === 桶管理 ===
mc mb prod/mybucket                          # 建桶
mc mb prod/mybucket --with-versioning        # 建桶+版本化
mc ls prod                                   # 桶列表
mc du prod/mybucket                          # 桶大小
mc stat prod/mybucket/file.txt               # 对象信息
mc tree prod/mybucket                        # 树形
mc rm --recursive --force prod/mybucket      # 清空桶
mc rb --force prod/mybucket                  # 删桶

# === 对象管理 ===
mc cp local/file prod/mybucket/              # 上传
mc cp prod/mybucket/file ./                  # 下载
mc cp --recursive prod/mybucket/dir/ ./      # 递归
mc mv prod/b1/file prod/b2/                  # 移动
mc rm prod/mybucket/temp-*                   # 通配删除
mc find prod/mybucket --name "*.tmp" --exec "mc rm {}"

# === 用户与权限 ===
mc admin user add prod newuser 'Pass@2026'
mc admin user disable prod newuser
mc admin user list prod
mc admin policy attach prod readwrite --user newuser
mc admin policy create prod mypolicy policy.json

# 临时凭证 (STS)
mc admin user sts create prod --name temp-user

# === 桶策略 ===
mc anonymous set download prod/public-bucket    # 公共读
mc anonymous set none prod/public-bucket        # 移除

# === 对象锁定 ===
mc lock set prod/mybucket --default-retention GOVERNANCE 7d

# === 通知 ===
# 事件通知到 webhook/kafka
mc admin config set prod notify_kafka:primary brokers=10.0.1.70:9092 topic=minio-events
mc event add prod/mybucket arn:minio:sqs::primary:kafka --event put,delete
mc event list prod/mybucket
```

### 10.3 性能优化

```ini
# 内核/系统优化 (各节点)

# 1. 文件句柄
cat >> /etc/security/limits.conf << 'EOF'
minio soft nofile 1048576
minio hard nofile 1048576
EOF

# 2. 内核参数
cat >> /etc/sysctl.d/99-minio.conf << 'EOF'
# 网络优化 (万兆/25G)
net.core.rmem_max = 268435456
net.core.wmem_max = 268435456
net.ipv4.tcp_rmem = 4096 87380 268435456
net.ipv4.tcp_wmem = 4096 65536 268435456
net.core.netdev_max_backlog = 300000
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq

# 文件缓存
vm.dirty_ratio = 20
vm.dirty_background_ratio = 5
EOF
sysctl -p

# 3. 挂载参数
# /etc/fstab: noatime,nodiratime (禁用 atime)
/dev/sdb1  /data1  xfs  defaults,noatime,nodiratime  0 0

# 4. 关闭系统缓存目录写入
# MinIO 自带缓存, 不需要 OS 缓存目录写 (可忽略)

# 5. 网卡调优
ethtool -G eth0 rx 4096 tx 4096
ethtool -L eth0 combined 16

# 6. 性能测试
mc admin perf prod
# 输出: GET/PUT 吞吐

# 7. 客户端并发 (rclone/mc)
mc cp --recursive --concurrency 16 dir/ prod/bucket/
rclone sync dir/ minio-prod:bucket --transfers 32 --checkers 32

# 8. 大文件建议
# 分片上传 (mc 默认自动)
# 大对象建议 chunk 大小:
mc put --part-size 64MiB bigfile.tar prod/bucket/
```

### 10.4 版本升级

```bash
# === MinIO 版本升级 ===
# 原则: 先升级非核心节点验证, 再全量

# 1. 检查当前版本
mc admin info prod | head -5
minio --version

# 2. 官方支持直接替换二进制 (滚动升级)
# 各节点下载新版本
wget https://dl.min.io/server/minio/release/linux-amd64/minio -O /tmp/minio.new
chmod +x /tmp/minio.new

# 3. 逐节点升级 (先 1 个, 验证, 再其他)
ssh node1 "systemctl stop minio && cp /tmp/minio.new /usr/local/bin/minio && systemctl start minio"
mc admin info prod | grep node1

# 4. 全节点
for node in node2 node3 node4; do
  scp /tmp/minio.new $node:/tmp/
  ssh $node "systemctl stop minio && cp /tmp/minio.new /usr/local/bin/minio && systemctl start minio"
  sleep 10
  mc admin info prod | grep $node
done

# 5. 升级 mc
wget https://dl.min.io/client/mc/release/linux-amd64/mc -O /usr/local/bin/mc
chmod +x /usr/local/bin/mc

# 6. 验证
mc admin info prod
mc admin heal prod --recursive

# 注意:
# - 升级前备份配置 (mc admin config export)
# - 升级窗口: 低峰期
# - 跳版本升级先看 release notes
# - 大版本跨越多代: 建议测试环境验证
```

---

## 十一、故障速查表

### 11.1 驱动器故障速查

| 故障现象 | 判断 | 处理 |
|:---|:---|:---|
| 单盘 offline | `mc admin info` 显示 1 盘离线 | 换盘, 自动重建, heal 验证 |
| 盘 corrupted | 元数据损坏 | xfs_repair 尝试, 不行换盘 |
| 盘 missing | 路径不存在 | 检查挂载, 恢复挂载点 |
| 多盘 offline | 检查是否同一节点/背板 | 先恢复电源/背板, 再逐盘换 |
| 盘 IO 错误 | dmesg 大量 IO error | 换盘 (物理坏) |
| 盘容量不一致 | 换盘后状态异常 | 换同容量盘 |
| 盘顺序变化 | 启动后 erasure set 错乱 | 恢复原配置重启 |

### 11.2 节点故障速查

| 故障现象 | 判断 | 处理 |
|:---|:---|:---|
| 单节点离线 | `mc admin info` 节点 offline | 恢复电源/进程, 自动重连 |
| 节点永久损坏 | 硬件无法修复 | 新节点替换, 自动重建 |
| 2 节点离线 (8+8) | 可读不可写 | 先恢复 1 节点恢复写能力 |
| 网络分区 | 部分节点互不可达 | 检查防火墙/VLAN, 恢复网络 |
| 节点时间偏差 | 时钟不一致 | NTP 同步 (chronyc makestep) |
| 节点重启后未加入 | 配置不一致 | 检查 MINIO_VOLUMES 一致性 |

### 11.3 数据问题速查

| 故障现象 | 判断 | 处理 |
|:---|:---|:---|
| 对象读失败 | 分片不足 (盘故障多) | 恢复盘, heal |
| 对象 checksum 错误 | bit rot | heal 自动修复 |
| 对象不存在 | 误删/未提交 | 版本回滚 / 备份恢复 |
| 桶不存在 | 误删桶 | 重建 + 备份恢复 |
| 写入失败 | quorum 不足 | 恢复节点/盘 |
| 写入超时 | 网络/性能 | 检查网络, 降低并发 |

### 11.4 常用命令速查

| 场景 | 命令 |
|:---|:---|
| 集群状态 | `mc admin info <alias>` |
| 盘状态 | `mc admin info <alias> --json | jq .info.servers` |
| 数据修复 | `mc admin heal <alias> --recursive --verbose` |
| 深度扫描 | `mc admin heal <alias> --recursive --scan-deep` |
| 实时日志 | `mc admin console log <alias>` |
| 请求追踪 | `mc admin trace <alias>` |
| 性能测试 | `mc admin perf <alias>` |
| 配置导出 | `mc admin config export <alias>` |
| 全量镜像 | `mc mirror --overwrite --remove <src> <dst>` |
| 实时镜像 | `mc mirror --watch --overwrite <src> <dst>` |
| 复制配置 | `mc replicate add <bucket> --remote-bucket <url>` |
| 版本开启 | `mc version enable <bucket>` |
| 版本回滚 | `mc cp <bucket>/<file>@<ver> ./` |
| 生命周期 | `mc ilm import <bucket> < file.json>` |
| 桶大小 | `mc du <bucket>` |
| 差异对比 | `mc diff <src> <dst>` |
| 巡检 | 见第十章脚本 |

---

## 十二、常见问题 FAQ

**Q1: 一块盘坏了, 数据会丢吗?**
不会。纠删码 8+8 配置下允许任意 8 块盘故障。换盘后 MinIO 自动从其他分片重建。

**Q2: 换盘时需要注意什么?**
新盘必须空盘 (mkfs.xfs 后直接挂载), 挂载点不变, 权限 minio:minio。不要复制旧盘数据, 不要用 RAID。

**Q3: 节点宕机多久需要处理?**
越早越好。单节点 (4 节点 8+8) 宕机不影响服务, 但长期宕机会增加二次故障风险。建议 4 小时内恢复。

**Q4: 两个节点同时宕机怎么办?**
8+8 配置下可读不可写。先恢复任意一个节点恢复写能力, 再恢复另一个, 最后 heal。

**Q5: 集群全部宕机数据还在吗?**
在。MinIO 数据直接写在磁盘文件系统上, 只要盘没物理损坏, 重启集群即可恢复。

**Q6: 怎么备份 MinIO 最靠谱?**
组合: 版本控制 (防误删) + mc mirror 定时镜像 (异地集群) + mc replicate 实时复制 (核心桶) + 定期恢复演练。

**Q7: 备份恢复到什么程度?**
恢复演练确认: 单桶恢复 (分钟级), 整集群恢复 (小时级)。目标 RTO 由业务决定。

**Q8: mc mirror 和 mc replicate 的区别?**
mirror: 快照式定时同步, 简单可靠, RPO 小时级。
replicate: 实时复制, RPO 秒级, 配置稍复杂, 适合容灾。

**Q9: 需要开启版本控制吗?**
强烈建议重要桶开启。防止误删/覆盖/勒索, 成本是存储占用 (旧版本)。

**Q10: 重建需要多久?**
取决于数据量和网络: 小集群分钟级, 大数据量 (数十 TB) 可能数小时。期间服务正常。

**Q11: 扩容怎么加节点?**
在 MINIO_VOLUMES 追加节点 (新 Pool), 所有节点统一配置重启。新数据写新 Pool, 可用 mc admin rebalance 迁移。

**Q12: 可以用 RAID 卡吗?**
不建议。MinIO 自己管理数据冗余 (纠删码), RAID 会浪费容量且 RAID 卡故障反而引入单点。直通盘 (HBA) 最佳。

**Q13: 单节点 MinIO 能用于生产吗?**
不建议。单节点没有纠删码冗余, 数据无保护。生产至少 4 节点。

**Q14: 怎么确认数据完整?**
mc admin heal --scan-deep 深度扫描, 或 mc diff 与备份对比。

**Q15: 监控什么指标?**
离线盘数、集群健康、写入 quorum、容量、API 错误率、节点在线状态。

---

*最后更新: 2026-07-14*
