# 进阶

> 故障排查进阶 = **K8s 全栈排查(Pod/Service/Ingress/CNI/CSI/DNS/调度) + Service Mesh + 容器(containerd/runc/cgroup) + 中间件深度(MySQL/PG/Kafka/Redis/ES/MongoDB) + JVM/Go/Python 应用层 + 性能分析(perf/eBPF/火焰图) + Trace(OpenTelemetry/Jaeger) + 分布式定位 + 慢查询治理 + 容量评估 + 灰度+回滚 SOP**。本章面向独立维护生产 K8s + 中间件 + 微服务的工程师。

## 一、K8s 全栈排查

### 1.1 Pod 不 Running

```bash
# Step 1: 现象
kubectl get pod -n ns
# STATUS: Pending / CrashLoopBackOff / ImagePullBackOff / Error / OOMKilled

# Step 2: describe (重点看 Events)
kubectl describe pod <pod> -n ns

# Step 3: 日志
kubectl logs <pod> -n ns
kubectl logs <pod> -n ns --previous          # 上次崩
kubectl logs <pod> -n ns -c <container>      # 多容器

# Step 4: exec 进入
kubectl exec -it <pod> -n ns -- sh
kubectl debug -it <pod> --image=busybox -n ns  # 临时调试容器

# 常见原因:
Pending:
  - 资源不足 (node 没 CPU/MEM)
  - PVC 未绑定
  - Selector 不匹配
  - taint 未容忍
  → kubectl describe node + kubectl get events

ImagePullBackOff:
  - 镜像不存在
  - imagePullSecret 缺/错
  - 镜像源访问慢
  → docker pull 测试 + check secret

CrashLoopBackOff:
  - 应用启动崩 (看 logs)
  - liveness 失败
  - 启动慢 (initialDelaySeconds)
  - 配置错 (env / configmap)
  → logs --previous + describe events

OOMKilled:
  - 内存超 limit
  - 调大 limit / 优化代码 / GC
  - 看 dmesg
  → kubectl describe + cgroup memory.peak
```

### 1.2 Service / Endpoints

```bash
# 不通常因
kubectl get svc / ep / pod -n ns -o wide

# 检查
kubectl get ep <svc>           # endpoints 是否有 IP
                                 # 空 → selector 不匹配 / pod 未 Ready

# 在 Pod 内测
kubectl exec -it <pod> -- nslookup <svc>
kubectl exec -it <pod> -- curl <svc>:<port>

# kube-proxy
iptables -t nat -L -n | grep <svc-ip>
ipvsadm -ln                    # IPVS 模式

# 跨 Namespace
<svc>.<ns>.svc.cluster.local
```

### 1.3 Ingress 不通

```bash
# 检查
kubectl get ing -n ns
kubectl describe ing <ing>     # backend / rules

# Controller
kubectl logs -n ingress-nginx <ctrl-pod>
kubectl exec -n ingress-nginx <ctrl-pod> -- cat /etc/nginx/nginx.conf | grep -A5 server_name

# DNS / 入口 IP
dig <host>
curl -v -H "Host: x.com" http://<lb-ip>

# 证书
openssl s_client -connect <host>:443 -servername <host>
```

### 1.4 CNI / 网络

```bash
# Pod 跨节点不通
kubectl exec -it <pod-a> -- ping <pod-b-ip>

# 检查 CNI (Calico/Cilium/Flannel)
calicoctl node status
cilium status
ip route                       # node 路由
ip link / ip addr               # 网卡

# IPAM
calicoctl ipam show
cilium endpoint list

# NetworkPolicy 拦截
kubectl get netpol -A
cilium policy trace ...

# DNS
kubectl get pod -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system <coredns-pod>
nslookup kubernetes.default.svc.cluster.local
```

### 1.5 调度

```bash
# Pod Pending
kubectl describe pod <pod>      # Events: 0/3 nodes available

# 原因排查
kubectl describe node           # Allocatable / Allocated
kubectl get pod -A -o wide      # 哪些 Pod 占资源
kubectl top pod / node           # 实时

# Taint / Toleration
kubectl describe node | grep Taint
# pod yaml:
  tolerations:
    - key: dedicated
      value: gpu
      effect: NoSchedule

# Affinity / AntiAffinity
# nodeSelector / required / preferred

# PDB
kubectl get pdb -A

# Priority
kubectl get priorityclass
```

### 1.6 持久化 (CSI / PVC)

```bash
kubectl get pvc / pv
kubectl describe pvc <pvc>

# 不绑定 → StorageClass 不匹配 / size / 后端
# Pending → CSI controller 问题
kubectl logs -n kube-system <csi-controller>

# Pod mount 失败
kubectl describe pod / events
# 看 kubelet 日志
journalctl -u kubelet -f
```

## 二、Service Mesh 排查

```
Istio 链路:
  Client → Istio Ingress → Envoy (sidecar) → 服务 → Envoy → 上游

排查工具:
  istioctl analyze              # 配置检查
  istioctl proxy-status         # 边车同步状态
  istioctl proxy-config cluster <pod>
  istioctl proxy-config route <pod>
  istioctl proxy-config endpoint <pod>
  istioctl x describe pod <pod>
  
Envoy 日志:
  kubectl logs <pod> -c istio-proxy
  
访问日志:
  - 0 - DC (Downstream Connection)
  - UH 无健康上游
  - UF 上游失败
  - UO 上游溢出
  - NR 无路由
  - URX upstream retry exhausted

mTLS 不通:
  PeerAuthentication 模式
  DestinationRule TLS 设置
  istioctl authn tls-check <pod>
```

## 三、容器层

```bash
# containerd / Docker
crictl ps / crictl pods         # CRI
crictl logs <id>
crictl exec -it <id> sh
crictl inspect <id>

systemctl status containerd
journalctl -u containerd -f

# cgroup
systemctl status <pod>.scope
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/cpu.max
cat /sys/fs/cgroup/memory.peak  # cgroup v2 内存峰值

# runc
runc list / runc events <id>

# 镜像 / 存储
ctr -n k8s.io image ls
crictl rmi $(crictl images -q)  # 清理
df -h /var/lib/containerd
```

## 四、中间件深度

### 4.1 MySQL（深度排查: 锁 / IO / 执行计划 / 调优）

> 基础连接 / 慢日志开启 / PROCESSLIST 见 [16_故障排查/01_基础 → 5.2 MySQL](../01_基础/README.md)。
> 本节基于基础层已开启的 slow log，进行根因分析与调优。

```sql
-- 慢查询深度分析 (基础层已开启 slow log)
mysqldumpslow -s t /var/log/mysql/slow.log
pt-query-digest /var/log/mysql/slow.log

-- 执行计划深度
EXPLAIN ANALYZE SELECT ...     -- 8.0+ 实际执行 + 行数 + 耗时
EXPLAIN FORMAT=TREE SELECT ...

-- 锁 / 死锁深度 (基础层 PROCESSLIST 已发现等待)
SHOW ENGINE INNODB STATUS\G    -- LATEST DETECTED DEADLOCK
SELECT * FROM performance_schema.data_locks;
SELECT * FROM performance_schema.metadata_locks;
SHOW OPEN TABLES WHERE In_use > 0;

-- IO / Buffer 调优
SHOW GLOBAL STATUS LIKE '%Innodb%';
SHOW GLOBAL VARIABLES LIKE '%buffer%';

-- 复制延迟
SHOW SLAVE STATUS\G            -- Seconds_Behind_Master
                                -- Last_IO_Error / Last_SQL_Error
SHOW MASTER STATUS;

-- 容量
SELECT table_schema, SUM(data_length+index_length)/1024/1024 size_MB
FROM information_schema.tables GROUP BY 1;

-- 工具 (深度)
pt-online-schema-change         -- 在线 DDL
pt-archiver                     -- 归档删
mysqltuner.pl                   -- 调优建议
```

### 4.2 PostgreSQL

```sql
-- 当前查询
SELECT pid, usename, state, query, query_start
FROM pg_stat_activity
WHERE state != 'idle' ORDER BY query_start;

-- 锁
SELECT * FROM pg_locks pl
LEFT JOIN pg_stat_activity a ON pl.pid = a.pid
WHERE NOT granted;

-- 慢查询 (pg_stat_statements)
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 20;

-- 复制
SELECT * FROM pg_stat_replication;
SELECT pg_last_wal_replay_lsn(), pg_last_xact_replay_timestamp();

-- 表 + 索引
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(...))
FROM pg_tables ORDER BY pg_total_relation_size(...) DESC LIMIT 20;

-- 工具
pgBadger (日志分析)
pg_stat_statements (扩展)
pgwatch2
```

### 4.3 Kafka

```bash
# 集群
kafka-broker-api-versions.sh --bootstrap-server kafka:9092
kafka-topics.sh --list --bootstrap-server kafka:9092
kafka-topics.sh --describe --topic my-topic ...
   # Leader / ISR / Replicas

# Consumer Lag
kafka-consumer-groups.sh --describe --group my-group ...
# LAG 持续高 → 消费跟不上 → 扩 consumer / 调 partition

# Burrow (lag 监控)
# Cruise Control (自动 rebalance)

# 排查
- Under-replicated partitions (ISR < replicas)
- Unclean leader election
- 磁盘满 (log.dirs)
- ZK 连接 (老版) / KRaft (3.x+)

# 工具
kafka-dump (offline 分析)
kafka-eagle / KnowStreaming (国产)
```

### 4.4 Redis（深度排查: 持久化 / 集群 / 大 Key / 热 Key）

> 基础连接 / 内存 / Key 检查见 [16_故障排查/01_基础 → 5.3 Redis](../01_基础/README.md)。
> 本节基于基础层已确认异常，进行持久化、集群与 Key 级深度定位。

```bash
# 大 Key 深度 (基础层已发现慢, 此处定位)
redis-cli --bigkeys
redis-cli --memkeys

# 热 Key (LFU 模式)
redis-cli --hotkeys

# 慢查询深度
redis-cli slowlog get 50

# 持久化 (AOF / RDB)
redis-cli config get save
redis-cli bgsave
redis-cli bgrewriteaof
redis-cli info persistence

# 集群
redis-cli cluster info
redis-cli cluster nodes
redis-cli --cluster check host:port

# Sentinel
redis-cli -p 26379 sentinel masters
redis-cli -p 26379 sentinel slaves mymaster

# 延迟深度
redis-cli --latency
redis-cli --latency-history -i 1
redis-cli --intrinsic-latency 30  # 系统底噪
```

### 4.5 Elasticsearch

```bash
curl localhost:9200/_cluster/health?pretty
   # status: green/yellow/red
curl localhost:9200/_cat/nodes?v
curl localhost:9200/_cat/indices?v&s=store.size:desc
curl localhost:9200/_cat/shards?v
curl localhost:9200/_cluster/allocation/explain?pretty

# 慢
curl localhost:9200/_nodes/hot_threads
curl localhost:9200/_tasks?detailed=true
curl localhost:9200/_cluster/pending_tasks

# 索引
curl localhost:9200/index/_stats
curl localhost:9200/index/_settings
curl localhost:9200/_cluster/settings

# 故障
- Yellow (副本未分配) → allocation explain
- Red (主分片丢) → 救数据
- Shard 倾斜 → rebalance
- 数据冷热 → ILM
- 内存压力 → fielddata / GC
```

### 4.6 MongoDB

```javascript
db.serverStatus()
db.currentOp()              // 正在执行
db.killOp(<id>)
db.coll.getIndexes()
db.coll.explain("executionStats").find(...)

rs.status()                 // Replica Set
rs.printSecondaryReplicationInfo()

// 慢查询
db.setProfilingLevel(1, {slowms: 100})
db.system.profile.find()

// 工具
mongostat / mongotop
Compass (GUI)
```

## 五、JVM 应用层

```bash
# 进程
jps -lv                       # JVM 进程
jstat -gcutil <pid> 1000      # GC 实时
jstat -gccause <pid>

# 线程 + 死锁
jstack <pid>                  # 线程栈
jstack -l <pid> | grep -A5 deadlock

# 堆
jmap -heap <pid>
jmap -histo:live <pid> | head -30
jmap -dump:live,format=b,file=heap.bin <pid>
   # 用 MAT / VisualVM / jhat 分析

# Async Profiler ⭐
./profiler.sh -d 30 -f flame.html <pid>

# Arthas ⭐ (阿里, 强烈推荐)
java -jar arthas-boot.jar <pid>
> dashboard         # 实时
> thread -n 3       # top CPU 线程
> heapdump
> watch <class> <method>  # 方法调用监控
> trace <class> <method>  # 调用栈耗时
> jad <class>        # 反编译
> ognl '...'         # 表达式
> profiler start
```

## 六、Go 应用

```go
// pprof 集成
import _ "net/http/pprof"
go http.ListenAndServe(":6060", nil)
```

```bash
# CPU
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
> top10 / web

# Heap
go tool pprof http://localhost:6060/debug/pprof/heap

# Goroutine
go tool pprof http://localhost:6060/debug/pprof/goroutine

# Trace
go tool trace http://localhost:6060/debug/pprof/trace?seconds=10

# 火焰图
go tool pprof -http=:8080 cpu.prof

# 检查
GODEBUG=schedtrace=1000,scheddetail=1 ./app
GOTRACEBACK=crash
GOGC=100  # GC 触发比

# Runtime
runtime.NumGoroutine()
runtime.GC()
runtime.MemStats
```

## 七、Python 应用

```bash
# 性能
py-spy top --pid <pid>         # top 风格 (无侵入) ⭐
py-spy dump --pid <pid>
py-spy record -o flame.svg --duration 30 --pid <pid>

# 内存
memray run app.py
memray flamegraph output.bin

# cProfile (开发)
python -m cProfile -o out.prof app.py
snakeviz out.prof

# 死锁/挂起
py-spy dump (无需侵入)
faulthandler.dump_traceback_later(5)

# uWSGI / Gunicorn
gunicorn --workers 4 --threads 2 app:app
   # 看 worker 数 + threads + 内存
```

## 八、性能分析（系统级）

### 8.1 perf

```bash
perf top
perf record -F 99 -ag sleep 30
perf report

# 火焰图 (Brendan Gregg)
perf record -F 99 -a -g -- sleep 30
perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg
```

### 8.2 eBPF (BCC / bpftrace) ⭐

```bash
# BCC
biotop                        # 进程级 IO
filetop                       # 文件级
opensnoop                     # open 调用
execsnoop                     # exec 监控
tcptop / tcptracer            # TCP
runqlat                       # 调度延迟
profile                       # CPU 采样

# bpftrace
bpftrace -e 'tracepoint:syscalls:sys_enter_open { printf("%s\n", str(args->filename)); }'

# 现代工具:
Pixie (K8s eBPF 神器) ⭐
Cilium Hubble (网络)
Inspektor Gadget
Coroot (eBPF 观测)
Parca (持续 profiling)
```

### 8.3 火焰图

```
on-CPU (CPU 时间):
  perf / Async Profiler / py-spy

off-CPU (等待):
  bpftrace + offcpu

差分火焰图 (对比版本):
  difffolded.pl

工具:
  flamegraph.pl
  speedscope
  Inferno (Rust)
```

## 九、Trace / 分布式定位

```
OpenTelemetry ⭐ (标准)
Jaeger ⭐ / Tempo / Zipkin (后端)
SkyWalking (国产, 全栈 APM)

排查:
  - 找慢调用 (P99 trace)
  - 定位上游 / 下游 / DB
  - 关联日志 (TraceID + LogID)
  - Metrics 关联 (Exemplar)

工具:
  Grafana + Tempo + Loki ⭐ (Trace + Log)
  Datadog APM (商业)
  阿里云 ARMS
```

## 十、慢查询治理

```
慢 SQL:
  pt-query-digest (MySQL)
  pgBadger (PG)
  Mongo profiler

ORM:
  N+1 查询 (joinedload / select_related)
  无索引扫
  事务过长

慢接口:
  Trace 找瓶颈
  压测复现 (k6 / locust / wrk)
  
治理:
  - 索引优化
  - 查询改写
  - 缓存 (Redis)
  - 异步 (MQ)
  - 拆表/分库
  - 读写分离
  - 物化视图
  - 列存 (ClickHouse 异构)
```

## 十一、容量评估

```
方法:
  压测 → 单机 QPS → 集群理论 → 留 buffer
  
压测工具:
  wrk ⭐ (HTTP)
  k6 ⭐ (现代, JS)
  locust (Python)
  JMeter (经典)
  ghz (gRPC)
  sysbench (DB)

公式:
  集群 QPS = 单机 QPS × 节点 × (1 - reserve)
  容量预留: 50% (峰值 2x)
  
监控趋势:
  历史 30/90 天
  增长率
  节假日峰值
```

## 十二、灰度+回滚 SOP

```
灰度策略:
  按权重 (10% → 50% → 100%)
  按用户 (内测 → 白名单 → 全量)
  按地域 (杭州 → 全国)
  Feature Flag (LaunchDarkly / 自研)

工具:
  Istio VirtualService weight
  Argo Rollouts (Canary + Blue/Green)
  Flagger
  K8s Deployment + maxSurge/maxUnavailable

回滚:
  kubectl rollout undo deployment/<x>
  Argo Rollouts abort
  Helm rollback <release> <revision>
  DB Schema (Liquibase rollback)
  
红线:
  ☐ 灰度必须能回滚 (不可逆变更红线!)
  ☐ DB Schema 加列只加不删 (兼容旧版本)
  ☐ API 改字段 → 双写 + Deprecated
  ☐ 配置/代码 一次只改一处
```

## 十三、Checklist（进阶）

```
K8s:
☐ Pod 7 状态 (Pending/Crash/Image/OOM/Error/Running/Ready)
☐ Service/EP/Ingress
☐ CNI/CSI/DNS
☐ Mesh (Istio + Envoy + istioctl)
☐ 调度 (Taint/Affinity/PDB)

容器:
☐ crictl + containerd
☐ cgroup v2

DB:
☐ MySQL: 慢查询分析 + EXPLAIN ANALYZE + 锁 + IO/Buffer + 复制
☐ PG: pg_stat_activity + pg_stat_statements + locks
☐ Mongo: currentOp + explain + replica
☐ Kafka: ISR + lag + offset
☐ Redis: bigkey + hotkey + 持久化 + 集群 + 延迟深度
☐ ES: cluster health + allocation + hot_threads

应用:
☐ JVM: Arthas ⭐ + jstack + jmap + Async Profiler
☐ Go: pprof + trace + flame
☐ Python: py-spy + memray
☐ Node: clinic.js + 0x

性能:
☐ perf record + 火焰图
☐ eBPF (BCC + bpftrace) ⭐
☐ Pixie / Coroot / Parca

Trace:
☐ OpenTelemetry + Jaeger/Tempo
☐ TraceID + LogID 关联

慢查询:
☐ pt-query-digest / pgBadger
☐ N+1 / 索引 / 缓存

容量:
☐ wrk / k6 / locust 压测
☐ 集群 QPS 公式

灰度+回滚:
☐ Argo Rollouts / Istio weight
☐ DB Schema 兼容
☐ Feature Flag
☐ 一次一变量
```

## 十四、推荐栈（进阶）

```
K8s:        kubectl + k9s + krew (插件) + Lens
Mesh:       istioctl + linkerd-cli
容器:        crictl + ctr + nerdctl
JVM:        Arthas ⭐ + Async Profiler ⭐ + Mat
Go:         pprof + speedscope + trace
Python:      py-spy ⭐ + memray
DB:         pt-toolkit (MySQL) + pgBadger (PG)
Kafka:      kafka-eagle + KnowStreaming
Redis:      RedisInsight
ES:         Cerebro + ElasticHQ
性能:        perf + flamegraph + Async Profiler
eBPF:       BCC + bpftrace + Pixie ⭐ + Coroot + Parca
Trace:      OpenTelemetry + Tempo + Jaeger ⭐ + SkyWalking
日志:        Loki ⭐ + 阿里 SLS
压测:        k6 ⭐ + wrk + locust + ghz
灰度:        Argo Rollouts ⭐ + Flagger + Feature Flag
监控:        Prometheus + Grafana + AlertManager ⭐
```

> 📖 **核心判断**：故障排查进阶 = **K8s 全栈(Pod/SVC/Ingress/CNI/CSI/DNS/调度) + Mesh(istioctl+Envoy) + 容器(crictl+cgroup) + DB 深度(MySQL/PG/Kafka/Redis/ES/Mongo 各专武) + 应用(Arthas/pprof/py-spy) + 性能(perf+eBPF+火焰图) + Trace(OTel+Jaeger/Tempo) + 慢查询治理 + 容量评估(k6/wrk) + 灰度+回滚 SOP(Argo Rollouts)**。能独立处理"K8s + Mesh + 中间件 + 微服务"全栈生产故障, 就具备资深 SRE 能力。
