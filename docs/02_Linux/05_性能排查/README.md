# 性能排查

> Linux 性能排查 = **USE 方法论 + 60s 速查清单 + 五大子系统（CPU/Mem/Disk/Net/Process）+ 内核黑科技（perf/bpftrace/ftrace）**。Brendan Gregg 的方法论 + 工具矩阵就是答案。本章给完整排查路径和实战命令。

## 一、USE 方法论 & 60 秒速查

### 1.1 USE（Utilization / Saturation / Errors）

```
对每个资源问三个问题:
  U: 利用率多少？（接近 100% = 满）
  S: 饱和度多少？（队列、等待时间）
  E: 错误数？

资源清单:
  CPU            mpstat / vmstat / pidstat
  Memory         free / vmstat / sar -r
  Disk           iostat / iotop / sar -d
  Network        sar -n / ss / netstat / ip -s
  Bus / Cache    perf
```

### 1.2 Netflix 60s 排查清单（Brendan Gregg）

```bash
uptime                                  # 1. 负载
dmesg | tail -20                         # 2. 内核错
vmstat 1 5                               # 3. 进程 / 内存 / IO / CPU
mpstat -P ALL 1 5                        # 4. 各 CPU 利用
pidstat 1 5                              # 5. 进程级 CPU
iostat -xz 1 5                           # 6. 磁盘 IO
free -h                                  # 7. 内存
sar -n DEV 1 5                           # 8. 网卡
sar -n TCP,ETCP 1 5                      # 9. TCP
top                                      # 10. 综合
```

### 1.3 决策树

```
现象：响应慢
  ↓
load 高？
  Y → mpstat 看 CPU 哪类高
       %usr 高 → 应用 CPU 瓶颈 → perf / pidstat
       %sys 高 → 内核 / 系统调用 → strace / perf
       %iowait 高 → 磁盘瓶颈 → iostat / iotop
       %si 高 → 软中断 → /proc/softirqs / 网卡
  N → 是不是慢在 IO？
       iostat -xz 看 %util / await
  N → 网络？
       ss / sar -n / tcpdump
  N → 锁竞争？
       perf lock / pidstat -t (线程)
  N → GC / Swap / 应用内部？
       free / sar -B / 应用日志
```

## 二、CPU 排查

### 2.1 全局

```bash
# 负载
uptime
# load average: 5.2, 4.8, 3.1   1m, 5m, 15m
# 经验: load > 核数 → 排队，> 核数 × 2 → 严重

cat /proc/loadavg
nproc                                   # CPU 核数

# vmstat
vmstat 1 10
# r       runnable 进程（含运行 + 排队）
# b       阻塞进程
# us/sy/id/wa/st  用户/系统/空闲/iowait/虚拟化偷
# r > 核数 → CPU 排队
# wa > 10% → 等磁盘
# st > 0 → 虚拟化资源被偷

# mpstat 各 CPU 视角
mpstat -P ALL 1
# 单核 100% 其他空闲 → 单线程瓶颈 / 中断不均
```

### 2.2 进程级

```bash
# top 排序
top -o %CPU
top -H -p PID                            # 看线程
# Shift+P 按 CPU / Shift+M 按内存

# pidstat
pidstat 1 5
pidstat -t -p PID 1                      # 含线程
pidstat -d 1                              # 进程级 IO
pidstat -w 1                              # 上下文切换

# ps
ps -eo pid,user,%cpu,%mem,stat,cmd --sort=-%cpu | head
```

### 2.3 上下文切换

```bash
vmstat 1
# cs   每秒 context switch
# in   每秒中断
# cs > 10000 = 高（可能锁竞争 / 大量小请求）

pidstat -w 1
# cswch/s    自愿切换（等 IO / 锁）
# nvcswch/s  被迫切换（时间片到 / 抢占）

# 锁竞争
perf lock record sleep 10
perf lock report
```

### 2.4 perf 火焰图

```bash
# 安装
dnf install perf
apt install linux-tools-generic

# 采样 30s
perf record -F 99 -a -g -- sleep 30
perf report                               # 文本
perf report --stdio | head -40            # 看热函数

# 火焰图（最直观）
git clone https://github.com/brendangregg/FlameGraph
perf record -F 99 -a -g -- sleep 30
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > flame.svg

# 特定进程
perf record -F 99 -p PID -g -- sleep 30

# 仅用户态 / 仅内核态
perf record -F 99 -a -g --call-graph dwarf -- sleep 30
perf record --call-graph fp -p PID

# 看热点系统调用
perf top -p PID
perf stat -p PID sleep 10                 # 性能计数器
```

### 2.5 CPU 高常见根因

| 现象 | 可能原因 | 排查 |
|:---|:---|:---|
| %usr 高 + 单线程 | 算法死循环 / 单线程瓶颈 | top -H + perf |
| %usr 高 + 多线程 | 高 QPS / 计算 | 看 QPS, perf |
| %sys 高 | 系统调用过多 | strace -c |
| %sys 高 + 高 cs | 锁竞争 / 上下文切换 | perf lock |
| %iowait 高 | 磁盘瓶颈 | iostat |
| %si 高 | 软中断（网络） | /proc/softirqs |
| %st 高 | 云上 CPU 被抢占 | 工单 |
| load 高 cpu 不忙 | D 状态进程多 | ps 看 STAT D+ |

## 三、内存排查

### 3.1 全局

```bash
# free
free -h
#               total     used      free    shared  buff/cache  available
# Mem:          32G       8G        2G      300M    22G          24G
# available  ⭐ 真实可用（含 reclaimable cache）
# free       完全空闲（误导）
# buff/cache 可被回收的缓存

# 误区: "为什么 free 这么小？" → 看 available

# /proc/meminfo
cat /proc/meminfo
# MemTotal/MemFree/MemAvailable
# Buffers/Cached
# SwapTotal/SwapFree
# Slab / SReclaimable / SUnreclaim
# HugePages_Total/Free
```

### 3.2 进程级

```bash
# 按内存排序
ps -eo pid,user,%mem,rss,vsz,cmd --sort=-%mem | head
top -o %MEM

# 详细
pmap -x PID                               # 进程内存映射
pmap -X PID                                # 含 PSS

# 单进程的 RSS / VSZ / PSS / USS
cat /proc/PID/status | grep -E "VmRSS|VmSize|VmPeak"
cat /proc/PID/smaps_rollup                 # 汇总

# smem (推荐, 区分 PSS/USS)
smem -tk
smem -p
# RSS:  常驻内存（含共享，重复计算）
# PSS:  按比例计算的常驻 ⭐
# USS:  独占内存 ⭐ 最准
# VSZ:  虚拟内存（不代表实际占用）
```

### 3.3 swap 与回收

```bash
# 谁在用 swap
for f in /proc/*/status; do
    pid=$(awk '/^Pid:/{print $2}' $f)
    swap=$(awk '/^VmSwap:/{print $2}' $f)
    [ "${swap:-0}" -gt 0 ] && echo "PID=$pid SWAP=${swap}kB CMD=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')"
done | sort -k2 -nr -t= | head

# 整体
sar -W 1 5                                # swap in/out
vmstat 1
# si/so   swap in/out (>0 表示有 swap 活动)

# 关闭某进程的 swap (放回内存)
# 暂无单进程命令，可 swapoff -a; swapon -a (整体)

# 内存回收压力
sar -B 1 5
# pgscank/s     kswapd 扫描
# pgscand/s     直接回收
# pgsteal/s     回收成功
# %vmeff        效率（理想 100%）
# 数字大 → 内存压力
```

### 3.4 Page Cache 详细

```bash
# 看每个文件占多少 cache
dnf install vmtouch
vmtouch /var/log/app.log
# Resident Pages: 12345/67890 ...

# 主动清缓存（不影响应用，慎用）
sync && echo 1 > /proc/sys/vm/drop_caches  # 1=PageCache, 2=dentry+inode, 3=all
```

### 3.5 OOM 分析

```bash
# 历史 OOM
dmesg -T | grep -i oom
journalctl -k --grep="killed process"

# 关键信息
# Killed process 12345 (myapp) total-vm:8192000kB, anon-rss:7000000kB
# - total-vm  虚拟内存
# - anon-rss  匿名物理内存
# - oom_score 算法分

# OOM Killer 评分逻辑
cat /proc/PID/oom_score
cat /proc/PID/oom_score_adj                # -1000..1000, 越大越优先杀
echo -1000 > /proc/PID/oom_score_adj      # 永不杀

# 防止内核日志被截断
dmesg --kernel --level=err,crit
```

### 3.6 内存泄漏排查

```bash
# Java
jmap -dump:live,format=b,file=heap.hprof PID
jcmd PID GC.heap_info
# MAT / VisualVM 分析

# Go
go tool pprof http://localhost:6060/debug/pprof/heap

# Native（C/C++）
valgrind --leak-check=full --show-leak-kinds=all ./myapp
# AddressSanitizer (编译时加 -fsanitize=address)

# 持续上涨观察
while true; do
    ps -o pid,rss,cmd -p PID >> /tmp/rss.log
    sleep 60
done
```

## 四、磁盘 IO 排查

### 4.1 全局

```bash
iostat -xz 1 5
# 关键列:
# %util       设备繁忙度 % (现代多队列 SSD 不要单看 %util)
# r/s w/s     读/写 IOPS
# rkB/s wkB/s 吞吐 KB
# r_await     读延迟 ms ⭐
# w_await     写延迟 ms ⭐
# aqu-sz      平均队列深度
# rareq-sz    平均请求大小 KB

# 判断:
# r_await > 20ms → 慢
# w_await > 50ms → 慢
# aqu-sz > 设备深度 → 排队

# 整体
sar -d 1 5
sar -b 1 5                                 # tps / bread/s / bwrtn/s
```

### 4.2 进程级 IO

```bash
# iotop
iotop -o                                   # 只显示有 IO 的
iotop -ao                                   # 累计

# pidstat
pidstat -d 1
# kB_rd/s   读速率
# kB_wr/s   写速率
# kB_ccwr/s 取消的写（dirty 被覆盖）
# iodelay   等 IO 时间 (clock ticks)

# 看某进程读写的文件
lsof -p PID | grep REG
strace -e trace=read,write -p PID         # 系统调用层
strace -e trace=openat,read,write -p PID
```

### 4.3 文件级

```bash
# 谁在读某文件
fuser -v /var/log/big.log
lsof /var/log/big.log

# 大文件
find / -type f -size +1G 2>/dev/null
du -sh /* 2>/dev/null | sort -h
ncdu /                                     # 交互式

# 已删但占空间（进程没释放）
lsof | grep deleted
# 修复: 重启占用进程 / truncate
```

### 4.4 inode 用尽

```bash
df -i                                      # inode 使用率
# 满了：
find / -xdev -type f | cut -d/ -f1-3 | sort | uniq -c | sort -rn | head
# 看哪个目录最多小文件
```

### 4.5 fio 压测（基线）

```bash
# 4K 随机读 IOPS
fio --name=randread --filename=/data/t.dat --rw=randread --bs=4k \
    --numjobs=4 --iodepth=64 --time_based --runtime=30 --direct=1

# 1M 顺序读吞吐
fio --name=seqread --filename=/data/t.dat --rw=read --bs=1M \
    --numjobs=1 --iodepth=32 --time_based --runtime=30 --direct=1
```

### 4.6 BPF 高级

```bash
# biolatency - 块设备延迟分布
biolatency 1 10                            # 1s 间隔

# biosnoop - 每个 IO 请求详情
biosnoop

# ext4slower / xfsslower - 慢 IO
ext4slower 10                              # > 10ms

# 进程级 IO
biotop
```

## 五、网络排查

### 5.1 连接与套接字

```bash
# ss 替代 netstat
ss -s                                      # 全局统计
ss -tln                                     # TCP listening
ss -tnp state established                   # ESTABLISHED + 进程
ss -tnp state time-wait | wc -l            # TIME_WAIT 数
ss -tnp '( dport = :80 or sport = :80 )'   # 端口过滤
ss -i                                       # 详细 (cwnd, rtt, retrans)

# 状态机
# LISTEN / SYN-SENT / SYN-RECV / ESTABLISHED
# FIN-WAIT-1 / FIN-WAIT-2 / TIME-WAIT
# CLOSE-WAIT / LAST-ACK / CLOSING

# TIME_WAIT 多 → tcp_tw_reuse=1
# CLOSE_WAIT 多 → 应用没 close socket（bug）
```

### 5.2 流量

```bash
# 全局
sar -n DEV 1 5
# rxkB/s, txkB/s, rxpck/s, txpck/s
# %ifutil  接口利用率

# nload / iftop / bmon
nload eth0                                  # 实时图
iftop -i eth0 -nNP                          # 各连接流量
bmon                                        # 多接口

# nethogs - 按进程
nethogs eth0
```

### 5.3 错包 / 丢包

```bash
# 接口统计
ip -s link show eth0
ethtool -S eth0 | grep -E "drop|error"
cat /proc/net/dev

# 内核协议栈
netstat -s | head -40
nstat -az
# 关注:
# tcp_segments_retrans   重传
# tcp_listen_overflows   accept 队列溢出 ⭐
# tcp_listen_drops
# udp_in_errors

# accept 队列满
ss -ltn
# Send-Q  当前 accept 队列
# Recv-Q  最大 backlog（=somaxconn）
```

### 5.4 TCP retransmit / RTT

```bash
ss -tin                                    # 详细 TCP 信息
# rtt:5.2/3.1                              RTT 平均/方差 ms
# cwnd:10                                  拥塞窗口
# retrans:0/12                             retrans now/total

# 抓包
tcpdump -i eth0 -nn -s 0 -w trace.pcap host 1.2.3.4
tcpdump -i eth0 -nn 'tcp[tcpflags] & (tcp-syn|tcp-fin|tcp-rst) != 0'   # 仅控制包
tcpdump -i any -nn 'port 80 and tcp[((tcp[12:1] & 0xf0) >> 2):4] = 0x47455420'  # GET 请求

# Wireshark 离线分析
```

### 5.5 DNS / 路由

```bash
dig @8.8.8.8 example.com +short
dig +trace example.com                     # 完整解析路径
host example.com

# DNS 缓存
resolvectl flush-caches
nscd -i hosts                              # NSCD

# 路由
ip route
ip route get 1.2.3.4                        # 走哪条
traceroute 1.2.3.4
mtr -n 1.2.3.4                              # 持续 trace ⭐

# MTU
ping -M do -s 1472 1.2.3.4                  # 测最大 MTU (1472+28=1500)
ip route get 1.2.3.4 | grep mtu
```

### 5.6 conntrack

```bash
# 看连接数
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max

# 详细
conntrack -L
conntrack -L -p tcp --dst 1.2.3.4

# 满了报错 "nf_conntrack: table full, dropping packet"
# 调大 nf_conntrack_max （见 03_系统调优）
```

### 5.7 BPF 高级网络

```bash
tcplife                                     # TCP 连接生命周期
tcptop                                      # 实时 TCP 流量 by PID
tcpretrans                                  # 重传事件
tcpconnect                                  # 主动连接
tcpaccept                                   # 被动连接
```

## 六、综合工具

### 6.1 perf

```bash
# 性能事件计数
perf stat ./myapp
perf stat -e cycles,instructions,cache-misses,branch-misses ./myapp

# 系统调用
perf trace -p PID
perf trace -e openat,read,write -p PID

# kernel function tracing
perf record -e 'sched:*' -a sleep 5
perf script

# 火焰图（见 2.4）
```

### 6.2 strace（系统调用追踪）

```bash
strace -p PID
strace -p PID -f                            # 含 fork 子进程
strace -p PID -e trace=network              # 仅网络
strace -p PID -e trace=openat,read,write
strace -p PID -c                            # 统计（多少次/总时间）
strace -p PID -T -tt                        # 每行带时间
strace -p PID -k                            # 带栈

# 攻击性 (生产慎用，会减慢)
# 替代: bpftrace
```

### 6.3 ltrace（库函数追踪）

```bash
ltrace -p PID
ltrace -e 'malloc+free' -p PID              # 仅 malloc/free
```

### 6.4 bpftrace（BPF DSL，超强）

```bash
# 安装
dnf install bpftrace
apt install bpftrace

# 单行
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { @[comm] = count(); }'
# 5s 后 Ctrl+C 看哪个进程 openat 最多

bpftrace -e 'kprobe:vfs_read { @[comm] = count(); }'
bpftrace -e 'tracepoint:block:block_rq_issue { @[comm, args->bytes] = count(); }'

# 函数延迟
bpftrace -e 'uprobe:/usr/sbin/mysqld:dispatch_command { @start[tid] = nsecs; }
             uretprobe:/usr/sbin/mysqld:dispatch_command /@start[tid]/ { @[args->thd] = hist(nsecs - @start[tid]); delete(@start[tid]); }'
```

### 6.5 BCC tools（一组现成 BPF 脚本）

```bash
dnf install bcc-tools                       # /usr/share/bcc/tools/

# 常用:
execsnoop           监视 exec()
opensnoop           监视 open()
biolatency          块设备延迟
tcptop / tcplife    TCP
ext4slower          慢 ext4 IO
runqlat             调度延迟
profile             CPU profile (类似 perf)
funcslower          慢函数
killsnoop           kill 信号
oomkill             OOM 事件
mountsnoop          挂载操作
```

## 七、典型场景案例

### 7.1 案例：CPU 飙升

```bash
# Step 1: 确认负载
uptime
# load 50, CPU 16 核 → 严重排队

# Step 2: 哪类 CPU？
mpstat 1 3
# %usr 95 → 应用 CPU 高

# Step 3: 哪个进程？
top -o %CPU
# myapp PID 12345 cpu 1500%

# Step 4: 哪个线程？
top -H -p 12345
# 看 cpu 高的 TID

# Step 5: perf 看热函数
perf record -F 99 -p 12345 -g -- sleep 30
perf report
# 或火焰图
perf script | ./stackcollapse-perf.pl | ./flamegraph.pl > flame.svg

# 常见根因:
# - 死循环
# - 正则回溯
# - 锁竞争 spinning
# - GC（Java）
```

### 7.2 案例：内存爆炸

```bash
# Step 1: free 看
free -h
# available 不到 1G

# Step 2: 谁吃内存
smem -tk
# myapp PSS 25G

# Step 3: 是否泄漏
while true; do
    awk '/VmRSS/ {print $2}' /proc/12345/status
    sleep 60
done
# RSS 持续上涨 → 泄漏

# Step 4: 应用层 dump
# Java: jmap, Go: pprof, native: valgrind

# Step 5: 是不是 swap 在 swap
sar -W 1 5
# si/so > 0 → 有 swap 活动

# Step 6: OOM 风险
dmesg -T | grep -i oom
cat /proc/12345/oom_score
```

### 7.3 案例：磁盘慢

```bash
# Step 1: iostat
iostat -xz 1 5
# nvme0n1 await 200ms %util 100%

# Step 2: 哪个进程
iotop -o
# postgresql 1500MB/s 读

# Step 3: 哪些文件
strace -e trace=read,write -p PID 2>&1 | head -100
lsof -p PID | grep REG

# Step 4: SQL / 应用层
EXPLAIN ANALYZE ...                          # 慢 SQL
pg_stat_statements
```

### 7.4 案例：网络丢包

```bash
# Step 1: 接口错误
ip -s link show eth0
# RX errors / dropped > 0

# Step 2: 协议栈
nstat -az | grep -E "Retrans|Drops"
# tcp_listen_overflows 暴涨 → accept 队列满

# Step 3: 队列
ss -ltn
# Send-Q > Recv-Q (somaxconn)
# 调大 somaxconn + 应用 backlog

# Step 4: 抓包确认
tcpdump -i eth0 -nn -c 100 'tcp port 80 and tcp[tcpflags] & tcp-rst != 0'

# Step 5: 内核日志
dmesg -T | grep -E "drop|softirq"
```

### 7.5 案例：load 高但 CPU 不忙

```bash
uptime                                      # load 30, CPU 8
top                                          # CPU 5% 空闲多

# load 包含 D 状态（不可中断睡眠，多为 IO 等待）
ps -eLo stat,pid,cmd | awk '$1 ~ /D/'

# 看 IO
iostat -xz 1
# %iowait 高 → 磁盘瓶颈

# 看 D 状态进程的栈
cat /proc/PID/stack
cat /proc/PID/wchan                          # 在哪个内核函数等
```

## 八、压测工具

```bash
# CPU
stress-ng --cpu 8 --timeout 60s
sysbench cpu --threads=8 --time=60 run

# 内存
stress-ng --vm 4 --vm-bytes 1G --timeout 60s
sysbench memory --threads=8 run

# 磁盘
fio --name=randrw --rw=randrw --bs=4k -size=10G --runtime=60 --time_based --direct=1
sysbench fileio --file-total-size=10G prepare
sysbench fileio --file-total-size=10G --file-test-mode=rndrw run

# 网络
iperf3 -s                                    # server
iperf3 -c server -P 8 -t 60                  # client 8 并发 60s

# HTTP
ab -n 100000 -c 1000 http://x/
wrk -t 8 -c 1000 -d 60s http://x/
hey -n 100000 -c 1000 http://x/              # Go 写的，推荐
vegeta attack -rate=1000/s -duration=60s -targets=t.txt | vegeta report
```

## 九、监控指标参考阈值

```
CPU:
  load_avg / cores         > 2 警告，> 4 严重
  %usr                     持续 > 80% 警告
  %sys                     > 30% 警告
  %iowait                  > 10% 警告
  context switch           > 50k/s 警告
  软中断（si）             > 30% 警告

Memory:
  available_mem / total    < 10% 警告
  swap_used                > 0 警告（数据库节点）
  pgscand                  > 0 警告（直接回收）
  oom_kill                 > 0 严重

Disk:
  %util                    持续 > 80% 警告（机械盘）
  await                    > 20ms 警告
  inode used               > 80% 警告

Network:
  packet_drop              > 0 警告
  tcp_retrans / segs_sent  > 1% 警告
  tcp_listen_overflow      > 0 警告
  conntrack_count / max    > 70% 警告

应用:
  P99 latency              SLO
  QPS                       基线对比
  error rate               > 0.1% 警告
```

## 十、典型坑

| 坑 | 建议 |
|:---|:---|
| **看 free 不看 available** | available 才是真实可用 |
| **load 高就以为 CPU 忙** | D 状态 + IO 也算 load |
| **看 %util 判断 SSD 饱和** | 多队列 SSD 不准，看 await |
| **strace 生产慎用** | 用 bpftrace |
| **netstat 已过时** | 用 ss |
| **不看 TIME_WAIT 含义** | 高并发 short conn 必有 |
| **CLOSE_WAIT 多** | 应用 bug 不 close socket |
| **OOM 不开 dmesg -T** | 时间戳重要 |
| **swap 没监控** | 暗杀性能 |
| **conntrack 满了不知道** | dmesg "nf_conntrack: table full" |
| **没火焰图直接调** | 不知道热点在哪 |
| **抓包不限大小** | 占满磁盘 |
| **不做基线** | 不知道"以前多快" |
| **看单点不看历史** | sar 长期数据 |
| **跨 NUMA 没排查** | numastat -p PID |

## 十一、最佳实践 Checklist

```
快速诊断（60s）:
☐ uptime / load
☐ dmesg | tail
☐ vmstat 1 5
☐ mpstat -P ALL 1 5
☐ pidstat 1 5
☐ iostat -xz 1 5
☐ free -h
☐ sar -n DEV/TCP 1 5
☐ top

深入排查:
☐ perf record + 火焰图
☐ bpftrace / BCC tools
☐ smem / vmtouch
☐ ss -tnp + iftop
☐ tcpdump 抓包

长期:
☐ sar 历史数据
☐ Prometheus + node-exporter
☐ 业务 SLO/SLI
☐ 火焰图归档
☐ 故障复盘文档
```

## 十二、推荐栈（2025）

```
基础:    sar / mpstat / iostat / vmstat / ss
进程:    top / htop / btop / pidstat
内存:    free / smem / vmtouch
磁盘:    iostat / iotop / fio
网络:    ss / iftop / tcpdump / mtr
内核:    perf / bpftrace / BCC
应用:    应用自带 profile (pprof / jstack / py-spy)
监控:    Prometheus + Grafana + 夜莺
火焰图:  Brendan Gregg FlameGraph
压测:    wrk / hey / fio / sysbench / stress-ng
```

## 十三、学习路径

```
入门（1 月）:
  1. USE 方法论
  2. 60s 速查熟练
  3. top / vmstat / iostat / sar
  4. ss / lsof / tcpdump 基础
  5. dmesg / journalctl 看错误

中级（3 月）:
  6. perf record + report
  7. 火焰图生成 + 分析
  8. strace / pidstat 深入
  9. fio 压测基线
  10. ss -tin / TCP 状态机
  11. 内存模型 (RSS/PSS/USS)

高级（6 月+）:
  12. bpftrace / BCC tools
  13. 内核 tracepoint / kprobe
  14. 锁竞争 / 死锁排查
  15. 跨 NUMA / cache miss 分析
  16. NIC offload / 软中断调度

专家:
  17. 内核源码阅读
  18. 自研性能分析工具
  19. 大规模分布式性能根因定位
  20. AIOps 异常检测（详见 12_AIOps）
```

## 十四、参考资料

```
官方:
  - kernel.org Documentation
  - perf wiki
  - bpftrace tutorial
  - BCC tools

大师:
  - Brendan Gregg: brendangregg.com ⭐
  - 《Systems Performance》Brendan Gregg
  - 《BPF Performance Tools》Brendan Gregg
  - 《Linux 性能优化实战》倪朋飞

经典:
  - http://www.brendangregg.com/linuxperf.html
  - http://www.brendangregg.com/USEmethod/use-linux.html
  - http://www.brendangregg.com/FlameGraphs/

社区:
  - r/linux
  - LWN.net
  - 国内: GeekTime / InfoQ 性能专栏
```

> 📖 **核心判断**：性能排查 = **USE 方法论 + 60s 速查 + 火焰图**。**80% 问题靠 top/vmstat/iostat/ss/sar 就能定位**，剩下的硬骨头才需 perf/bpftrace。**iowait 高 → 磁盘；retrans 多 → 网络；context switch 高 → 锁；OOM → memory leak**。学会读火焰图比记 100 个工具更值钱——一张图直接看出热点函数，比所有 metric 都直观。**先建基线再优化**是铁律。

