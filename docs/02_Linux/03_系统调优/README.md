# 系统调优

> Linux 性能调优 = **理解负载（CPU/Memory/IO/Net）→ 找瓶颈 → 改内核参数 → 改 limit → 改应用配置**。**60% 性能问题靠 sysctl + ulimit + 文件系统挂载选项**就能解决。本章给完整内核参数手册和场景化模板。

## 一、调优方法论

### 1.1 USE 方法（Brendan Gregg）

```
对每个资源：
  Utilization   利用率 (%)
  Saturation    饱和度 (排队/wait)
  Errors        错误数

资源:
  CPU / Memory / Disk / Network / Bus / Interconnect

定位流程:
  1. 现象 → 哪个子系统？(用户感受 = 延迟/吞吐/错误)
  2. 抓数据 → top/vmstat/iostat/sar/perf
  3. 假设瓶颈 → CPU? Mem? IO? Net?
  4. 改参数 / 配置 → 再测
  5. 量化对比

错误调优:
  - 不测就调（拍脑袋）
  - 一次改多个参数（搞不清谁起作用）
  - 不留对照基线
```

### 1.2 调优前提：建立基线

```bash
# 性能基线脚本
#!/bin/bash
DATE=$(date +%F-%H%M)
DIR=/tmp/baseline-$DATE
mkdir -p $DIR

# 系统信息
uname -a > $DIR/sys.txt
cat /etc/os-release >> $DIR/sys.txt
free -h > $DIR/mem.txt
nproc >> $DIR/sys.txt
cat /proc/cpuinfo | grep "model name" | head -1 >> $DIR/sys.txt

# 负载基线
sar -A 1 60 > $DIR/sar.txt &
mpstat -P ALL 1 60 > $DIR/mpstat.txt &
iostat -xz 1 60 > $DIR/iostat.txt &
vmstat 1 60 > $DIR/vmstat.txt &
ss -s > $DIR/ss-start.txt
wait

# 应用基线（压测）
ab -n 10000 -c 100 http://localhost/ > $DIR/ab.txt
wrk -t 4 -c 100 -d 30s http://localhost/ > $DIR/wrk.txt

ss -s > $DIR/ss-end.txt
echo "✅ Baseline saved to $DIR"
```

## 二、内核参数（sysctl）

### 2.1 配置方式

```bash
# 临时
sysctl -w net.ipv4.ip_forward=1
echo 1 > /proc/sys/net/ipv4/ip_forward

# 持久化（推荐 /etc/sysctl.d/）
cat > /etc/sysctl.d/99-tuning.conf <<EOF
vm.swappiness = 10
net.core.somaxconn = 65535
EOF

sysctl --system                      # 应用全部
sysctl -p /etc/sysctl.d/99-tuning.conf

# 当前值
sysctl -a | grep somaxconn
cat /proc/sys/net/core/somaxconn
```

### 2.2 通用基础参数（全场景）

```ini
# /etc/sysctl.d/99-base.conf

# ============================================
# 文件句柄
# ============================================
fs.file-max = 2097152                # 系统级最大 fd
fs.nr_open = 1048576                 # 进程级最大 fd（< file-max）
fs.inotify.max_user_watches = 524288 # inotify (开发机 / dev 工具)
fs.inotify.max_user_instances = 8192
fs.aio-max-nr = 1048576              # 异步 IO

# ============================================
# 进程
# ============================================
kernel.pid_max = 4194304             # PID 上限
kernel.threads-max = 4194304
kernel.core_pattern = /var/core/core-%e-%p-%t
kernel.core_uses_pid = 1

# ============================================
# Panic / 恢复
# ============================================
kernel.panic = 10                    # panic 后 10s 自动重启
kernel.panic_on_oops = 1
vm.panic_on_oom = 0                  # OOM killer 处理（不 panic）

# ============================================
# Magic SysRq (救命用)
# ============================================
kernel.sysrq = 1
# Alt+SysRq+B 立刻重启 (REISUB 顺序救机)
```

### 2.3 内存调优

```ini
# /etc/sysctl.d/99-memory.conf

# ============================================
# Swap
# ============================================
vm.swappiness = 10                   # 0-100，越小越不愿用 swap
# 服务器/DB: 1-10  桌面: 60  K8s 节点: 0/关闭

vm.vfs_cache_pressure = 50           # 默认 100, 减小 = 倾向保留 dentry/inode 缓存
vm.min_free_kbytes = 1048576         # 强制保留 1G 物理内存

# ============================================
# OOM
# ============================================
vm.overcommit_memory = 0             # 0=启发, 1=允许过载, 2=严格 (cap)
vm.overcommit_ratio = 80             # vm.overcommit=2 时生效

# 进程级 oom_score 控制 (重要服务别被杀)
echo -1000 > /proc/PID/oom_score_adj   # 永不被 oom kill

# ============================================
# Dirty Pages (写回)
# ============================================
vm.dirty_background_ratio = 5        # 后台 flusher 触发阈值 % (默认 10)
vm.dirty_ratio = 20                  # 写阻塞阈值 % (默认 20)
vm.dirty_expire_centisecs = 3000     # 30s, 脏页最长存活
vm.dirty_writeback_centisecs = 500   # 5s, flusher 唤醒周期

# 写密集场景：调小阈值，避免突发大量写
# 数据库：用 O_DIRECT 绕过 page cache

# ============================================
# Huge Pages (DB / JVM)
# ============================================
vm.nr_hugepages = 1024               # 2MB × 1024 = 2GB
# 1GB Huge Page (kernel 启动参数 hugepagesz=1G)
vm.hugetlb_shm_group = 1001          # 允许某 group 使用

# Transparent Huge Pages (THP) - 数据库通常禁用
# /sys/kernel/mm/transparent_hugepage/enabled = never
# /etc/rc.local 或 systemd unit:
# echo never > /sys/kernel/mm/transparent_hugepage/enabled
# echo never > /sys/kernel/mm/transparent_hugepage/defrag

# ============================================
# 内存映射
# ============================================
vm.max_map_count = 262144            # Elasticsearch / Redis 必加
```

### 2.4 网络调优（核心）

```ini
# /etc/sysctl.d/99-network.conf

# ============================================
# Core
# ============================================
net.core.somaxconn = 65535           # listen() backlog ⭐ 必调
net.core.netdev_max_backlog = 65535  # 网卡 RX 队列
net.core.netdev_budget = 600         # NAPI 单次处理包数
net.core.optmem_max = 81920

# Socket buffer (默认 / 最大)
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.core.rmem_max = 16777216         # 16M
net.core.wmem_max = 16777216

# ============================================
# TCP buffer 自动调整
# ============================================
net.ipv4.tcp_rmem = 4096 87380 16777216    # min default max
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_mem = 786432 1048576 1572864
net.ipv4.tcp_moderate_rcvbuf = 1

# ============================================
# TCP 连接管理
# ============================================
net.ipv4.tcp_max_syn_backlog = 8192        # SYN 队列
net.ipv4.tcp_syncookies = 1                 # SYN flood 防护
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 3
net.ipv4.tcp_abort_on_overflow = 0
net.ipv4.tcp_max_tw_buckets = 1048576

# TIME_WAIT 控制（高并发 web 必调）
net.ipv4.tcp_tw_reuse = 1                  # 复用 TIME_WAIT 连接
# net.ipv4.tcp_tw_recycle - 4.12 内核已删除（NAT 下有问题）
net.ipv4.tcp_fin_timeout = 15

# 端口范围
net.ipv4.ip_local_port_range = 1024 65535

# Keep-alive
net.ipv4.tcp_keepalive_time = 600           # 默认 7200s, 太长
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3

# ============================================
# TCP 拥塞控制 (现代必用 BBR)
# ============================================
net.core.default_qdisc = fq                 # BBR 配合
net.ipv4.tcp_congestion_control = bbr       # 比 cubic 好

# 看可用算法
# sysctl net.ipv4.tcp_available_congestion_control
# 加载 bbr: modprobe tcp_bbr

# ============================================
# 转发 (路由器 / K8s 节点)
# ============================================
net.ipv4.ip_forward = 1
net.ipv4.conf.all.rp_filter = 1             # 反向路径校验
net.ipv4.conf.default.rp_filter = 1

# ============================================
# K8s / 容器必备
# ============================================
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.conf.all.forwarding = 1

# ============================================
# conntrack (NAT / iptables -m state)
# ============================================
net.netfilter.nf_conntrack_max = 1048576    # 默认 65536 太小
net.netfilter.nf_conntrack_tcp_timeout_established = 1200
net.netfilter.nf_conntrack_buckets = 262144  # 哈希桶（必须重启或 modprobe）

# 修改 buckets 的方法:
# echo 262144 > /sys/module/nf_conntrack/parameters/hashsize

# ============================================
# 安全 / 防 DDoS
# ============================================
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
```

### 2.5 文件系统 / IO 调优

```ini
# IO 调度（kernel cmd 或 udev）
# NVMe: none
# SATA SSD: mq-deadline  
# HDD: bfq

# vm.dirty_*  控制 page cache 写回
# 见 2.3 内存

# /etc/fstab 挂载选项（更重要）
# noatime,nodiratime    - 不更新访问时间
# discard              - SSD TRIM
# data=writeback (ext4) - 性能（牺牲一致性）
# 见 02_存储与文件系统
```

## 三、limits（ulimit）

### 3.1 limits.conf

```bash
# /etc/security/limits.conf
# domain  type   item     value
*        soft   nofile   65535        # 软限制（用户可调到 hard）
*        hard   nofile   65535        # 硬限制（root 才能改）
*        soft   nproc    65535
*        hard   nproc    65535

root     soft   nofile   1048576
root     hard   nofile   1048576

nginx    soft   nofile   100000
nginx    hard   nofile   100000

mysql    soft   nofile   200000
mysql    hard   nofile   200000
mysql    soft   memlock  unlimited    # 锁内存（不被 swap）
mysql    hard   memlock  unlimited

* soft core unlimited                  # core dump 不限大小
```

### 3.2 systemd 服务限制

```ini
# /etc/systemd/system/myapp.service
[Service]
LimitNOFILE=1048576
LimitNPROC=65535
LimitMEMLOCK=infinity
LimitCORE=infinity
```

```bash
# 也可改 systemd 默认（影响所有服务）
# /etc/systemd/system.conf
[Manager]
DefaultLimitNOFILE=1048576
DefaultLimitNPROC=65535

systemctl daemon-reexec
```

### 3.3 当前 limits 查看

```bash
ulimit -a                              # 当前 shell
cat /proc/PID/limits                   # 某进程
systemctl status myapp                 # systemd 服务
```

### 3.4 PAM 限制（注意）

```bash
# 如果 limits.conf 不生效，检查 PAM
grep pam_limits /etc/pam.d/*
# 应有: session required pam_limits.so

# SSH 登录还需:
# /etc/pam.d/sshd
# session required pam_limits.so
```

## 四、CPU 调优

### 4.1 CPU 频率 / 调度器

```bash
# 看当前
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# 常见: performance / powersave / ondemand / schedutil

# 临时切换
echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 持久化
# RHEL: tuned-adm profile throughput-performance
# Ubuntu: cpupower frequency-set -g performance

# tuned profile（RHEL/openEuler 推荐）
tuned-adm list
tuned-adm active
tuned-adm profile throughput-performance     # 服务器
tuned-adm profile latency-performance        # 低延迟
tuned-adm profile virtual-host                # KVM 宿主
tuned-adm profile virtual-guest               # 虚拟机内
tuned-adm profile network-throughput          # 网络密集
tuned-adm profile balanced                     # 默认

# 自定义 profile
# /etc/tuned/myprofile/tuned.conf
[main]
include=throughput-performance
[sysctl]
net.ipv4.tcp_congestion_control=bbr
[vm]
transparent_hugepages=never
```

### 4.2 NUMA 亲和

```bash
# 看 NUMA 拓扑
numactl --hardware
lscpu | grep NUMA

# 看进程 NUMA 分布
numastat -p PID

# 绑定（避免跨 NUMA 内存访问）
numactl --cpunodebind=0 --membind=0 ./myapp
numactl --physcpubind=0-7 --membind=0 ./myapp     # 绑 CPU 0-7

# 内存策略
numactl --interleave=all ./myapp                  # 跨 NUMA 均衡（Redis 建议）

# CPU 亲和（无 NUMA 也可）
taskset -cp 0-7 PID                                # 已运行进程
taskset -c 0-7 ./myapp                              # 启动时

# K8s
spec:
  containers:
    - resources:
        limits: { cpu: 4 }
      # CPU Manager static policy + Topology Manager 可自动 NUMA 亲和
```

### 4.3 isolcpus / 中断隔离

```bash
# 内核启动参数 (GRUB)
# 把 CPU 8-15 隔离出来给关键应用
isolcpus=8-15 nohz_full=8-15 rcu_nocbs=8-15

# 应用绑过去
taskset -c 8-15 ./latency-critical-app

# 网卡中断绑到非业务 CPU
# /proc/interrupts 看中断号
echo 7 > /proc/irq/IRQ/smp_affinity_list           # 绑到 CPU 7

# 自动化工具
irqbalance --policyscript=/etc/irqbalance.d/policy.sh
```

### 4.4 BIOS / 固件层

```
关闭省电（数据中心服务器必关）:
  - C-states (深度睡眠)
  - P-states 部分场景
  - Intel SpeedStep / AMD PowerNow（保留 performance governor）

启用:
  - Hyper-Threading (HT)（除数据库基线测试外）
  - VT-x / VT-d (虚拟化)
  - Turbo Boost

NUMA:
  - 启用 Node Interleaving = off（保留 NUMA 拓扑）
```

## 五、网络栈深入

### 5.1 多队列网卡

```bash
# 看队列数
ethtool -l eth0
# Combined: 8     当前队列数

# 调整队列数
ethtool -L eth0 combined 16

# 看每队列流量
mpstat -P ALL 1
# 或
ethtool -S eth0 | grep -E 'rx_queue|tx_queue'

# RSS (Receive Side Scaling) 自动分流到多队列
# 现代网卡默认开启

# RPS (Receive Packet Steering) 软件多核
echo 'ff' > /sys/class/net/eth0/queues/rx-0/rps_cpus     # 用 CPU 0-7

# XPS (Transmit Packet Steering)
echo 'ff' > /sys/class/net/eth0/queues/tx-0/xps_cpus
```

### 5.2 网卡 offload

```bash
ethtool -k eth0                                     # 当前 offload 状态
ethtool -K eth0 tso on gso on gro on lro on        # 启用所有
ethtool -K eth0 rx-checksumming on tx-checksumming on
```

### 5.3 网卡环形缓冲区

```bash
ethtool -g eth0                                     # 当前 ring buffer
ethtool -G eth0 rx 4096 tx 4096                    # 加大 (默认 256/512)

# 中断 coalescing
ethtool -c eth0
ethtool -C eth0 rx-usecs 100                        # 微调
```

### 5.4 MTU / Jumbo Frame

```bash
ip link set eth0 mtu 9000                           # Jumbo (需端到端支持)
ip a show eth0
ping -M do -s 8972 dest                             # 测试不分片
```

## 六、文件系统调优

### 6.1 挂载选项

```
通用:
  noatime,nodiratime               性能 +
  
SSD:
  noatime,discard                  TRIM
  # 或定期 fstrim weekly (更优)
  
ext4:
  data=writeback,journal_async_commit  极致性能（牺牲安全）
  data=ordered (默认，平衡)
  data=journal (最安全，最慢)
  barrier=0                         无电池保护时不要关 ⚠️
  commit=5                          journal 写回间隔 (默认 5s)
  
xfs:
  noatime,nodiratime,logbsize=256k,logbufs=8
  allocsize=64m                     防止小文件碎片
```

### 6.2 fstrim 定时

```bash
# RHEL/Ubuntu 默认有 fstrim.timer
systemctl status fstrim.timer
systemctl enable --now fstrim.timer
fstrim -v /                                        # 手动
```

### 6.3 inode 不够（小文件场景）

```bash
df -i                                              # 看 inode 用量
# 满了：
# - 清理小文件
# - 重新格式化 mkfs.ext4 -N 大量

# XFS 默认动态分配 inode，一般不会用尽
```

## 七、数据库调优模板

### 7.1 MySQL

```ini
# /etc/sysctl.d/99-mysql.conf
vm.swappiness = 1
vm.dirty_ratio = 80
vm.dirty_background_ratio = 5
vm.overcommit_memory = 1

# 关闭 THP
# /etc/rc.local:
echo never > /sys/kernel/mm/transparent_hugepage/enabled

# limits
mysql soft nofile 65535
mysql hard nofile 65535
mysql soft memlock unlimited
```

### 7.2 PostgreSQL

```ini
vm.swappiness = 1
vm.overcommit_memory = 2
vm.overcommit_ratio = 100              # 严格控制

# Huge Pages (推荐启用)
vm.nr_hugepages = 计算: shared_buffers / 2M + 缓冲
```

### 7.3 Redis

```ini
vm.overcommit_memory = 1               # 必须，否则 BGSAVE 报错
net.core.somaxconn = 65535
# THP off
echo never > /sys/kernel/mm/transparent_hugepage/enabled
```

### 7.4 Elasticsearch

```ini
vm.max_map_count = 262144              # 必须，否则启动失败
fs.file-max = 2097152
# limits
elasticsearch soft nofile 65535
elasticsearch hard nofile 65535
elasticsearch soft memlock unlimited
```

## 八、Web 服务器调优

### 8.1 Nginx 高并发

```ini
# /etc/sysctl.d/99-nginx.conf
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 600
net.ipv4.ip_local_port_range = 10000 65535
net.netfilter.nf_conntrack_max = 1048576

# limits
nginx soft nofile 100000
nginx hard nofile 100000
```

```nginx
# nginx.conf
worker_processes auto;
worker_rlimit_nofile 100000;
events {
    worker_connections 65535;
    use epoll;
    multi_accept on;
}
```

### 8.2 反向代理

```nginx
# 长连接 keep-alive 到上游
upstream backend {
    server 10.0.0.1:8080;
    keepalive 64;
    keepalive_requests 10000;
    keepalive_timeout 60s;
}
server {
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_buffering off;             # 大文件 / SSE 必关
}
```

## 九、K8s 节点调优

```ini
# /etc/sysctl.d/99-k8s.conf
# 转发
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1

# Conntrack（Pod 数多必调）
net.netfilter.nf_conntrack_max = 1048576

# 文件
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 8192

# 内存
vm.max_map_count = 262144
vm.swappiness = 0                     # K8s 1.22+ 支持 swap, 但默认仍关
vm.overcommit_memory = 1

# pid
kernel.pid_max = 4194304

# 加载 br_netfilter
echo br_netfilter > /etc/modules-load.d/k8s.conf
modprobe br_netfilter
```

```bash
# 关闭 swap（K8s 严格要求）
swapoff -a
sed -i '/swap/d' /etc/fstab

# limits
cat >> /etc/security/limits.conf <<EOF
* soft nofile 1048576
* hard nofile 1048576
EOF

# kubelet 配置中:
# eviction 阈值 / GC 策略 详见 K8s 章节
```

## 十、调优后验证

### 10.1 应用 + 验证

```bash
sysctl --system                       # 应用
sysctl -a | grep somaxconn            # 验证生效
ulimit -n                              # 验证 limits

# 重启服务 / 重新登录后生效
```

### 10.2 性能复测

```bash
# 网络
ab -n 100000 -c 1000 http://localhost/
wrk -t 8 -c 1000 -d 60s http://localhost/

# 磁盘
fio --name=test --filename=/data/t.dat --rw=randrw --bs=4k -size=4G \
    --numjobs=8 --iodepth=64 --time_based --runtime=60 --direct=1

# 内存 + CPU
stress-ng --cpu 8 --io 4 --vm 4 --vm-bytes 1G --timeout 60s
sysbench cpu --threads=8 --time=60 run
sysbench memory --threads=8 --memory-total-size=10G run

# 对比基线
diff baseline-before.txt baseline-after.txt
```

## 十一、调优 Profile 速查

### 11.1 通用服务器（默认）

```
- swappiness=10
- somaxconn=65535
- nofile=65535
- tcp_congestion=bbr
- governor=performance
```

### 11.2 Web 服务器（高并发）

```
+ tcp_tw_reuse=1
+ tcp_fin_timeout=15
+ ip_local_port_range=10000-65535
+ conntrack_max=1048576
+ nofile=100000
+ keepalive_intvl=30
```

### 11.3 数据库

```
+ swappiness=1
+ THP off
+ Huge Pages
+ memlock=unlimited
+ nofile=200000
+ overcommit_memory=2 (PG) / 1 (MySQL/Redis)
+ data 盘 noatime + 独立挂载
```

### 11.4 K8s 节点

```
+ swap off
+ br_netfilter
+ bridge-nf-call-iptables=1
+ conntrack_max=1048576
+ max_map_count=262144
+ inotify_watches=524288
+ pid_max=4194304
```

### 11.5 NFV / DPDK / 低延迟

```
+ isolcpus / nohz_full / rcu_nocbs
+ governor=performance
+ THP off / never
+ irqbalance off + 手动绑
+ HT off (BIOS)
+ Huge Pages 1G
```

## 十二、典型坑

| 坑 | 建议 |
|:---|:---|
| **sysctl 改了重启失效** | /etc/sysctl.d/*.conf 持久化 |
| **ulimit 不生效** | PAM 配置 + 重新登录 |
| **somaxconn 没调 backlog 满** | 默认 128 严重不够 |
| **TIME_WAIT 堆积** | tcp_tw_reuse=1（不要 tcp_tw_recycle）|
| **THP 数据库性能抖** | 数据库一律 disabled |
| **swappiness 服务器 60** | 调到 1-10 |
| **vm.max_map_count 默认** | ES/Redis 必加到 262144 |
| **conntrack_max 不够** | K8s/NAT 节点必调 |
| **关闭 swap K8s 没改 fstab** | 重启又回来 |
| **CPU governor powersave** | 服务器一律 performance |
| **NUMA 跨节点访问** | 显式 numactl 绑定 |
| **tuned-adm 没设 profile** | RHEL 系统未充分优化 |
| **改 sysctl 没重启服务** | 部分参数仅影响新连接 |
| **写 dirty_ratio 太大** | 突发刷盘抖 |
| **bbr 没启用** | 高延迟场景 cubic 落后 |

## 十三、最佳实践 Checklist

```
基础（必做）:
☐ /etc/sysctl.d/99-*.conf 持久化
☐ /etc/security/limits.conf 调高 nofile
☐ swappiness 调低
☐ THP 数据库场景禁用
☐ tcp_congestion_control = bbr
☐ governor = performance

通用服务:
☐ somaxconn=65535
☐ ip_local_port_range 扩大
☐ tcp_tw_reuse=1

数据库:
☐ Huge Pages 配置
☐ memlock=unlimited
☐ 独立 data 盘 + noatime
☐ swappiness=1

K8s 节点:
☐ swap off + fstab 删除
☐ br_netfilter 加载
☐ bridge-nf-call-iptables=1
☐ max_map_count=262144
☐ conntrack_max=1048576

监控:
☐ 调优前后基线对比
☐ 关键指标长期监控
☐ tuned profile 持久化
☐ 内核版本一致
```

## 十四、推荐栈（2025）

```
通用调优框架:
  - tuned (RHEL/openEuler)
  - tlp (Ubuntu 桌面/服务器)
  - 自定义 sysctl.d 文件

监控:
  - node-exporter (metric)
  - sar / sysstat (历史)
  - perf / bpftrace (深入)

压测:
  - ab / wrk / hey (HTTP)
  - fio (磁盘)
  - sysbench (CPU/Mem/MySQL)
  - iperf3 / netperf (网络)
  - stress-ng (综合)

配置管理:
  - Ansible playbook 一键调优
  - 各类 profile 模板化
```

## 十五、学习路径

```
入门（2 周）:
  1. USE 方法论
  2. 看懂 top/vmstat/iostat/sar
  3. sysctl 基础参数
  4. ulimit 配置

中级（1 月）:
  5. 网络栈调优（TCP/conntrack）
  6. 内存调优（swappiness/THP/dirty）
  7. tuned profile
  8. NUMA 亲和
  9. CPU governor + isolcpus

高级（3 月+）:
  10. 多队列网卡 + RPS/XPS
  11. perf / bpftrace
  12. 数据库专项调优
  13. K8s 节点深度调优
  14. NFV/DPDK 低延迟

专家:
  15. 内核参数源码阅读
  16. 自研 tuned profile
  17. 全栈性能基线建模
```

## 十六、参考资料

```
官方:
  - kernel.org Documentation/admin-guide/sysctl/
  - Red Hat Performance Tuning Guide
  - Brendan Gregg's blog
  - Linux Performance: brendangregg.com/linuxperf.html

书籍:
  - 《Systems Performance》Brendan Gregg
  - 《BPF Performance Tools》Brendan Gregg
  - 《Linux 性能优化实战》倪朋飞
  - 《深入理解 Linux 内核》

工具:
  - tuned: https://github.com/redhat-performance/tuned
  - perf-tools: https://github.com/brendangregg/perf-tools
  - bcc / bpftrace
```

> 📖 **核心判断**：Linux 调优 = **sysctl + ulimit + 挂载选项 + tuned profile + governor** 五件套。**80% 性能问题**靠 `somaxconn / tcp_tw_reuse / nofile / swappiness / THP off / vm.max_map_count` 这六个参数就能搞定。**调优前先建基线，调优后用压测复核**——不测不改是铁律。**数据库一律关 THP**，**K8s 一律关 swap**，**网络 BBR**——这三个是新机器开荒的必做项。

