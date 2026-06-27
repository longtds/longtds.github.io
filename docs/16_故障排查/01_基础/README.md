# 基础

> 故障排查基础 = **方法论(USE/RED/Four Golden Signals/MTTR) + Linux 基础排查(top/iostat/vmstat/netstat) + 网络基础(ping/traceroute/dig/curl/tcpdump) + 日志分析(journalctl/grep/awk) + 进程+文件+磁盘+内存 + 应用层(HTTP/MySQL/Redis 常见错) + Postmortem 入门**。本章面向初次接触故障排查的运维/开发。

## 一、核心方法论

```
USE 方法 (Brendan Gregg, 硬件):
  Utilization 利用率 (CPU/MEM/DISK/NET %)
  Saturation  饱和度  (队列 / 等待)
  Errors      错误率
  
  → 每资源 三看

RED 方法 (服务):
  Rate     请求率 (RPS)
  Errors   错误率 (5xx %)
  Duration 延时 (P50/P95/P99)

Four Golden Signals (Google SRE):
  Latency    延时
  Traffic    流量
  Errors     错误
  Saturation 饱和度

MTTR 拆解:
  MTTD (Detect)     发现
  MTTA (Acknowledge) 接收
  MTTI (Investigate) 调查
  MTTR (Repair/Resolve) 修复

故障排查 5 步:
  1. 现象 (用户报 / 监控告警)
  2. 缩小范围 (二分 / 排除法)
  3. 假设 + 验证 (一次一变量)
  4. 修复 + 回归
  5. Postmortem
```

## 二、Linux 基础排查

### 2.1 CPU

```bash
top / htop                    # 实时
top -H -p <pid>              # 线程
mpstat -P ALL 1              # 各核
pidstat -u 1                 # 每进程
uptime                       # load
sar -u 1                     # 历史
perf top                     # 火焰图前置
```

关键指标：
- **load** 持续 > 核数 → 排队
- **us** 高 → 业务代码
- **sy** 高 → 内核 / 系统调用
- **wa** 高 → IO 等待
- **st** 高 → 虚拟化 steal

### 2.2 内存

```bash
free -h                       # 总览
cat /proc/meminfo            # 详细
vmstat 1                     # 含 swap
ps aux --sort=-%mem | head   # TOP 进程
pmap -x <pid>                # 进程内存图
slabtop                       # 内核 slab
dmesg | grep -i oom          # OOM Killer
smem -r                       # PSS (真实占用)
```

关键：
- **available** 才是真实可用 (free 包含 cache)
- **swap used** 高 → OOM 风险
- **OOM Killer** 看 `dmesg | grep killed`

### 2.3 磁盘

```bash
df -hT                        # 容量 + 文件系统
du -sh /* | sort -h          # 大目录
iostat -xz 1                 # IO 速率 + util
iotop                         # 进程 IO
lsof | grep deleted          # 已删除但未释放
ncdu /                       # 交互浏览大文件
fuser -v /path                # 谁在用
```

关键：
- **%util** 持续 > 80% → 磁盘瓶颈
- **await** 高 (>10ms HDD / >1ms SSD) → 排队
- inode 满 (`df -i`) → 小文件多

### 2.4 网络

```bash
# 连通
ping -c 4 host
mtr -n -c 30 host
traceroute host

# DNS
dig +short google.com
nslookup google.com
host google.com

# 端口
ss -tlnp                      # 监听端口
ss -tnp | head                # 已建立连接
netstat -ano | grep ESTABLISHED
nc -zv host 80               # 端口探测

# 抓包
tcpdump -i eth0 -nn 'port 80' -w cap.pcap
tcpdump -i any -nn 'host 1.2.3.4 and port 443'
wireshark cap.pcap

# HTTP
curl -v https://example.com
curl -w "@curl-format.txt" -o /dev/null -s https://example.com
  # 看 dns/connect/tls/transfer 分段耗时

# 速率
iftop -nP                     # 实时
nload                         # 简洁
nethogs                       # 进程级
sar -n DEV 1                 # 历史

# 路由
ip route
ip rule
ip neigh
```

## 三、日志分析

```bash
# Systemd
journalctl -u nginx -f                    # follow
journalctl -u nginx --since "1 hour ago"
journalctl -p err -b                      # 错误 + 本次启动
journalctl -k                              # kernel

# 文件
tail -f /var/log/messages
less +F /var/log/syslog                   # less follow
grep -i error /var/log/app.log | tail
awk '$9>=500 {print}' access.log          # nginx 5xx
zgrep -c "ERROR" /var/log/app.log.*.gz

# 时间过滤
sed -n '/2026-06-27 10:/,/2026-06-27 11:/p' app.log

# JSON 日志
jq 'select(.level=="error")' app.json.log
jq -s 'group_by(.path) | map({path: .[0].path, count: length})' app.json.log

# 集中 (生产)
Loki + Grafana
Elastic + Kibana
阿里 SLS
```

## 四、进程

```bash
ps auxf                      # 树
pstree -p <pid>
pidstat 1                    # 资源
strace -f -p <pid>           # 系统调用 (慎用 生产)
strace -e openat,connect ... # 过滤
lsof -p <pid>                # 文件描述符
ls /proc/<pid>/              # /proc 树
cat /proc/<pid>/limits
cat /proc/<pid>/status
cat /proc/<pid>/environ | tr '\0' '\n'
```

## 五、应用层常见错

### 5.1 HTTP

```
4xx (客户端):
  400 请求格式
  401 未鉴权
  403 已鉴权但无权限
  404 不存在
  408 超时
  429 限流
  
5xx (服务端):
  500 内部错误
  502 上游错误 (Gateway)
  503 服务不可用 (overload)
  504 上游超时
  
排查:
  - 5xx 突增 → 上游 / DB / 依赖
  - 502 → 后端进程死/慢/Connection refused
  - 504 → 后端处理超时 (慢 SQL?)
  - 429 → 限流策略 / 客户端 retry
  - 401/403 → 鉴权配置
```

### 5.2 MySQL

```sql
-- 慢查询
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
SHOW PROCESSLIST;             -- 当前
SHOW FULL PROCESSLIST;
EXPLAIN SELECT ...;            -- 执行计划
SHOW ENGINE INNODB STATUS;     -- 锁 + 事务

-- 锁
SELECT * FROM performance_schema.data_locks;
SHOW OPEN TABLES WHERE In_use > 0;
KILL <id>;                     -- 杀连接

-- 工具
pt-query-digest slow.log       -- Percona
mysqltuner.pl                   -- 调优建议
```

### 5.3 Redis

```bash
redis-cli ping
redis-cli info                # 全信息
redis-cli info clients
redis-cli info memory
redis-cli info stats
redis-cli slowlog get 10
redis-cli --bigkeys           # 大 key
redis-cli --hotkeys           # 热 key (LFU)
redis-cli --latency           # 延迟
redis-cli monitor              # 实时命令 (慎用生产)
```

常见：
- maxmemory 满 → OOM / 驱逐
- 大 key (>1MB) → 命令阻塞
- 热 key → 单分片瓶颈
- bgsave 慢 → 内存大 / fork 慢

## 六、网络故障 5 大场景

```
场景 1: 连不上 (端口未通)
  → ping (L3)
  → telnet/nc (L4)
  → curl (L7)
  → 防火墙 / 安全组 / iptables -L

场景 2: 慢
  → mtr (路径丢包)
  → curl -w 看耗时分段
  → tcpdump 看重传
  → MTU (大包丢)

场景 3: 间歇性
  → mtr 长时
  → 抓包 grep RST/重传
  → 监控 (Grafana 历史)

场景 4: DNS 慢/错
  → dig +short / +time=2 +tries=1
  → /etc/resolv.conf
  → systemd-resolved (Ubuntu)
  → 缓存 (nscd / dnsmasq)

场景 5: HTTPS 错
  → curl -vk
  → openssl s_client -connect host:443
  → 证书过期 / SNI / TLS 版本
```

## 七、磁盘+IO 排查

```
磁盘满:
  df -h → 找满分区
  du -sh /* | sort -h → 大目录
  lsof | grep deleted → 未释放
  ncdu / → 交互
  
inode 满:
  df -i
  for i in *; do echo "$i: $(find $i | wc -l)"; done

IO 慢:
  iostat -xz 1 → %util / await
  iotop → 进程
  blktrace / biotop (eBPF)
  pidstat -d 1 → 进程 IO

文件系统:
  dmesg | grep -i error
  fsck (离线)
  smartctl -a /dev/sda → 硬盘健康
```

## 八、Postmortem 模板

```markdown
## 故障概要
- 时间: 2026-06-27 10:30 - 11:15 (45min)
- 影响: API P99 > 5s, 5xx 错误率 30%
- 受影响: 2000 用户
- 严重级: P1

## 时间线
10:30  监控告警 (P99 突增)
10:32  On-call ack
10:35  扩容尝试 → 无效
10:45  发现 MySQL slow query 阻塞
10:50  KILL 慢查询 + 调整索引
11:00  服务恢复
11:15  监控全绿

## 根因
慢查询: SELECT 大表 + 无索引 + 全表扫
触发: 当天上线新接口, EXPLAIN 未审

## 修复
- 加索引 (生产 + 测试)
- pt-online-schema-change 在线
- 索引审核流程

## Action Items
☐ [P0] 索引审核 流程 (周一前)
☐ [P0] EXPLAIN 准入门禁 CI
☐ [P1] Pre-prod 影子流量
☐ [P2] DBA 培训
☐ [P2] 慢查询告警阈值降至 500ms

## 5 Whys
1. 为什么 P99 高? → MySQL 慢
2. 为什么 MySQL 慢? → 慢查询全表扫
3. 为什么全表扫? → 无索引
4. 为什么无索引? → 上线未审 + 监控未触发
5. 为什么未审? → 流程不完善 → AI 门禁
```

## 九、Checklist（基础）

```
方法论:
☐ USE + RED + Four Golden Signals
☐ MTTD/MTTA/MTTR 度量

Linux:
☐ CPU (top/mpstat/pidstat)
☐ MEM (free/vmstat/dmesg OOM)
☐ DISK (df/du/iostat/iotop)
☐ NET (ss/netstat/tcpdump/mtr)
☐ Process (ps/strace/lsof/proc)

日志:
☐ journalctl (systemd)
☐ tail/grep/awk/jq
☐ 集中日志 (Loki/Elastic/SLS)

网络:
☐ ping/mtr/dig/curl
☐ tcpdump + Wireshark
☐ 5 大场景

应用:
☐ HTTP 状态码语义
☐ MySQL slowlog + EXPLAIN
☐ Redis bigkey/hotkey/slowlog

Postmortem:
☐ 5 步流程
☐ 5 Whys
☐ Action 闭环
```

## 十、入门 20 题

```
1.  USE / RED / Golden Signals
2.  MTTD vs MTTR
3.  load > 核数 含义
4.  us/sy/wa/st 区别
5.  available vs free (内存)
6.  OOM Killer 触发 + 调整
7.  iostat %util / await
8.  lsof deleted (未释放)
9.  inode 满
10. tcpdump 抓 80
11. mtr 看丢包
12. curl -v / -w
13. dig 含义
14. HTTP 502 vs 504
15. MySQL EXPLAIN 关键列
16. Redis bigkey 危害
17. journalctl -u + -p err
18. systemctl status / restart
19. strace 用途 + 风险
20. Postmortem 必含项
```

## 十一、推荐栈（基础）

```
监控:        Prometheus + Grafana + Loki ⭐
APM:        SkyWalking / Pixie / OpenTelemetry
日志:        journalctl / Loki / 阿里 SLS
网络:        mtr + tcpdump + Wireshark + curl
进程:        top + htop + strace + lsof
DB:         MySQL slowlog + pt-query-digest
Redis:      redis-cli + RedisInsight
告警:        AlertManager + 钉钉 / 飞书 / 短信
Postmortem: Notion / Confluence + 模板
```

> 📖 **核心判断**：故障排查基础 = **方法论(USE+RED+Golden Signals+MTTR) + Linux 5 大子系统(CPU/MEM/DISK/NET/Process) + 日志(journalctl+tail+grep+jq) + 网络(ping+mtr+dig+tcpdump+curl) + 应用(HTTP+MySQL+Redis) + Postmortem(5 Whys + Action)**。掌握这 6 条线，就具备日常故障排查能力。**先有方法论, 再用工具。**
