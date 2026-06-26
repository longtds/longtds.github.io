# 高级

> Linux 高级 = **eBPF/bpftrace + perf 火焰图 + 内核深度调优 + 高级网络（XDP/nftables/conntrack）+ 容器底座（namespace/cgroup v2）+ 内核模块/kpatch + 国产 OS 适配**。本章面向需要排查疑难杂症、做平台底座、跨多机房运维的高级工程师。

## 一、性能排查方法论

### 1.1 USE 方法（Brendan Gregg）

```
对每个资源问三个问题:
  U: Utilization 利用率 (%)
  S: Saturation  饱和度（排队/wait）
  E: Errors      错误数

资源:
  CPU / Memory / Disk / Network / Bus / Interconnect

错误调优:
  - 不测就调（拍脑袋）
  - 一次改多个参数（搞不清谁起作用）
  - 不留对照基线
```

### 1.2 Netflix 60 秒速查清单

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
  N → IO 慢？
       iostat -xz 看 %util / await
  N → 网络？
       ss / sar -n / tcpdump
  N → 锁竞争？
       perf lock / pidstat -t (线程)
  N → GC / Swap / 应用内部？
       free / sar -B / 应用日志
```

## 二、CPU 深度排查

### 2.1 上下文切换

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

### 2.2 perf 火焰图

```bash
# 采样 30s
perf record -F 99 -a -g -- sleep 30
perf report                               # 文本
perf report --stdio | head -40

# 火焰图（最直观）
git clone https://github.com/brendangregg/FlameGraph
perf record -F 99 -a -g -- sleep 30
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > flame.svg

# 特定进程
perf record -F 99 -p PID -g -- sleep 30

# 仅用户态 + dwarf 展开
perf record -F 99 -p PID -g --call-graph dwarf -- sleep 30

# 看热点系统调用
perf top -p PID
perf stat -p PID sleep 10                 # 性能计数器
```

### 2.3 CPU 高常见根因表

| 现象 | 可能原因 | 排查 |
|:---|:---|:---|
| %usr 高 + 单线程 | 算法死循环 / 单线程瓶颈 | top -H + perf |
| %usr 高 + 多线程 | 高 QPS / 计算 | perf 看热函数 |
| %sys 高 | 系统调用过多 | strace -c |
| %sys 高 + 高 cs | 锁竞争 / 上下文切换 | perf lock |
| %iowait 高 | 磁盘瓶颈 | iostat |
| %si 高 | 软中断（网络） | /proc/softirqs |
| %st 高 | 云上 CPU 被抢占 | 工单 |
| load 高 cpu 不忙 | D 状态进程多 | ps STAT D+ |

## 三、内存深度排查

### 3.1 真实内存占用

```bash
# free 看 available (不要看 free)
free -h
# available 才是真实可用（含 reclaimable cache）

# 进程级（区分 RSS / PSS / USS）
smem -tk
# RSS:  常驻内存（含共享，重复计算）
# PSS:  按比例计算 ⭐ 多进程共享场景准
# USS:  独占内存 ⭐ 真实"占了你多少"
# VSZ:  虚拟内存（不代表实际占用）

# 单进程
pmap -X PID                                # 含 PSS
cat /proc/PID/smaps_rollup                 # 汇总

# 谁在用 swap
for f in /proc/*/status; do
    pid=$(awk '/^Pid:/{print $2}' $f)
    swap=$(awk '/^VmSwap:/{print $2}' $f)
    [ "${swap:-0}" -gt 0 ] && echo "PID=$pid SWAP=${swap}kB CMD=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')"
done | sort -k2 -nr -t= | head
```

### 3.2 OOM 分析

```bash
# 历史 OOM
dmesg -T | grep -i oom
journalctl -k --grep="killed process"

# 关键信息
# Killed process 12345 (myapp) total-vm:8192000kB anon-rss:7000000kB
# - total-vm  虚拟内存
# - anon-rss  匿名物理内存

# OOM Killer 评分
cat /proc/PID/oom_score
cat /proc/PID/oom_score_adj                # -1000..1000, 越大越优先
echo -1000 > /proc/PID/oom_score_adj      # 永不杀（守护进程用）
```

### 3.3 内存压力（PSI）

```bash
# Pressure Stall Information (kernel 4.20+)
cat /proc/pressure/cpu
cat /proc/pressure/memory
cat /proc/pressure/io
# some  avg10=0.00 avg60=0.00 avg300=0.00 total=0
# full  avg10=0.00 avg60=0.00 avg300=0.00 total=0
# > 10% 持续 → 资源压力

# cgroup PSI（容器/K8s）
cat /sys/fs/cgroup/system.slice/myapp.service/memory.pressure
```

### 3.4 Page Cache 详细

```bash
# 看某文件占多少 cache
dnf install vmtouch
vmtouch /var/log/app.log
# Resident Pages: 12345/67890 ...

# 主动清缓存（生产慎用）
sync && echo 1 > /proc/sys/vm/drop_caches  # 1=PageCache, 2=dentry+inode, 3=all
```

## 四、磁盘 IO 深度

```bash
# iostat
iostat -xz 1 5
# 关键列:
# %util       设备繁忙度 (现代多队列 SSD 不要单看 %util)
# r/s w/s     读/写 IOPS
# r_await     读延迟 ms ⭐
# w_await     写延迟 ms ⭐
# aqu-sz      平均队列深度
# rareq-sz    平均请求大小 KB

# 判断:
# r_await > 20ms → 慢
# w_await > 50ms → 慢
# aqu-sz > 设备深度 → 排队

# 进程级
iotop -o
pidstat -d 1
# iodelay   等 IO 时间 (clock ticks)

# 某进程读写的文件
strace -e trace=read,write -p PID
lsof -p PID | grep REG

# BPF 工具（精准）
biolatency 1 10                            # 延迟分布
biosnoop                                    # 每个 IO 详情
ext4slower 10                              # 慢 IO (> 10ms)
xfsslower 10
biotop
```

## 五、网络深度排查

### 5.1 TCP 状态与队列

```bash
# 连接状态
ss -s                                      # 全局统计
ss -tnp state established
ss -tnp state time-wait | wc -l
ss -i                                       # 详细 (cwnd, rtt, retrans)

# 状态机
# LISTEN / SYN-SENT / SYN-RECV / ESTABLISHED
# FIN-WAIT-1 / FIN-WAIT-2 / TIME-WAIT
# CLOSE-WAIT / LAST-ACK / CLOSING

# TIME_WAIT 多 → tcp_tw_reuse=1
# CLOSE_WAIT 多 → 应用没 close socket（bug）

# accept 队列满
ss -ltn
# Send-Q  当前 accept 队列
# Recv-Q  最大 backlog（=somaxconn 或应用 listen backlog 较小者）

# 协议栈统计
netstat -s | head -40
nstat -az
# 关注:
# tcp_listen_overflows   accept 队列溢出 ⭐
# tcp_segments_retrans   重传
# udp_in_errors
```

### 5.2 TCP retransmit / RTT 分析

```bash
ss -tin                                    # 详细 TCP 信息
# rtt:5.2/3.1                              RTT 平均/方差 ms
# cwnd:10                                  拥塞窗口
# retrans:0/12                             retrans now/total

# 抓包
tcpdump -i eth0 -nn -s 0 -w trace.pcap host 1.2.3.4
tcpdump -i eth0 -nn 'tcp[tcpflags] & (tcp-syn|tcp-fin|tcp-rst) != 0'

# Wireshark 离线分析
```

### 5.3 conntrack（NAT/iptables 必看）

```bash
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max

conntrack -L
conntrack -L -p tcp --dst 1.2.3.4

# 满了报错: "nf_conntrack: table full, dropping packet"
echo 1048576 > /proc/sys/net/netfilter/nf_conntrack_max
echo 262144 > /sys/module/nf_conntrack/parameters/hashsize
```

### 5.4 nftables（现代防火墙）

```bash
nft list ruleset

# 基础 ruleset
cat > /etc/nftables.conf <<'EOF'
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
        iif lo accept
        icmp type echo-request accept
        tcp dport { 22, 80, 443 } accept
        ip saddr 192.168.1.0/24 accept
        log prefix "[nft drop] "
    }
    chain forward {
        type filter hook forward priority filter; policy drop;
    }
    chain output {
        type filter hook output priority filter; policy accept;
    }
}
EOF
nft -f /etc/nftables.conf
systemctl enable --now nftables

# iptables 转 nftables
iptables-translate -A INPUT -p tcp --dport 22 -j ACCEPT
```

### 5.5 多队列网卡 + RPS/XPS

```bash
ethtool -l eth0
ethtool -L eth0 combined 16

ethtool -S eth0 | grep -E 'rx_queue|tx_queue'

# RPS（软件多核分流）
echo 'ff' > /sys/class/net/eth0/queues/rx-0/rps_cpus
# XPS
echo 'ff' > /sys/class/net/eth0/queues/tx-0/xps_cpus

# 中断绑核
cat /proc/interrupts | grep eth0
echo 7 > /proc/irq/IRQ/smp_affinity_list

# offload / 环形缓冲 / coalescing
ethtool -k eth0 && ethtool -K eth0 tso on gso on gro on
ethtool -g eth0 && ethtool -G eth0 rx 4096 tx 4096
ethtool -C eth0 rx-usecs 100
```

## 六、eBPF & bpftrace

### 6.1 概念

```
eBPF = 在内核里安全运行小程序的 VM
  - tracepoint / kprobe / uprobe / USDT
  - 实时观测 + 流量过滤 + XDP 高性能转发

工具栈:
  bcc        Python/Lua + C，老牌
  bpftrace   类 awk DSL，一行排查 ⭐
  libbpf     CO-RE，工程化
  Cilium     基于 eBPF 的 K8s CNI / 服务网格
```

### 6.2 bpftrace 一行流

```bash
dnf install bpftrace
apt install bpftrace

# 谁在 openat()
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { @[comm] = count(); }'

# 谁在 vfs_read
bpftrace -e 'kprobe:vfs_read { @[comm] = count(); }'

# 块设备 IO 直方图
bpftrace -e 'tracepoint:block:block_rq_issue { @[args->bytes] = count(); }'

# 函数延迟（uprobe 用户态）
bpftrace -e '
uprobe:/usr/sbin/mysqld:dispatch_command { @start[tid] = nsecs; }
uretprobe:/usr/sbin/mysqld:dispatch_command /@start[tid]/ {
    @lat = hist(nsecs - @start[tid]); delete(@start[tid]);
}'

# TCP 重传谁触发
bpftrace -e 'kprobe:tcp_retransmit_skb { @[comm, pid] = count(); }'

# OOM 触发
bpftrace -e 'kprobe:oom_kill_process { printf("%s killed\n", str(arg1)); }'
```

### 6.3 BCC tools（现成脚本）

```bash
dnf install bcc-tools     # /usr/share/bcc/tools/

# 常用:
execsnoop          监视 exec()  ⭐ 看谁起子进程
opensnoop          监视 open()  ⭐ 文件被谁打开
biolatency         块设备延迟
tcptop / tcplife   TCP 流量 / 连接生命周期
tcpretrans          重传事件
ext4slower / xfsslower    慢 IO
runqlat            调度延迟
profile            CPU profile
funcslower         慢函数
killsnoop          kill 信号
oomkill            OOM 事件
mountsnoop          挂载操作
```

### 6.4 XDP（最快的数据面）

```
XDP = eXpress Data Path
  在网卡驱动 / 硬件层处理包，绕过协议栈
  适合: DDoS 防御 / LB / 防火墙 / Cilium

xdp-tools / Katran / Cilium 都在用
```

```bash
# 看 xdp 程序
ip link show
bpftool prog show

# Cilium 直接用 XDP 实现 K8s NetworkPolicy
```

## 七、namespace + cgroup v2（容器底座）

### 7.1 namespace（隔离）

```
8 类 namespace:
  mnt    挂载点
  pid    进程 ID
  net    网络栈
  ipc    System V IPC
  uts    hostname/domain
  user   用户/组 ID
  cgroup cgroup 视图
  time   单调时间

容器 = namespace 集合 + cgroup + rootfs + capability + seccomp
```

```bash
# 看一个进程的 namespace
ls -l /proc/PID/ns/

# 手工创建（unshare）
unshare --pid --fork --mount-proc /bin/bash    # 新 pid ns
unshare --net /bin/bash                         # 新 net ns
unshare --user --map-root-user /bin/bash       # 普通用户假装 root

# 进入已存在 ns
nsenter -t PID -n ip a                          # 进网络 ns
nsenter --target $(pidof nginx) --all bash
```

### 7.2 cgroup v2（资源限制）

```bash
# 看
mount | grep cgroup
ls /sys/fs/cgroup/
cat /sys/fs/cgroup/cgroup.controllers          # 可用控制器

# 创建
mkdir /sys/fs/cgroup/myapp
echo "+memory +cpu +io" > /sys/fs/cgroup/cgroup.subtree_control

# CPU
echo "200000 100000" > /sys/fs/cgroup/myapp/cpu.max     # 2 核
# Memory
echo "1G" > /sys/fs/cgroup/myapp/memory.max
echo "512M" > /sys/fs/cgroup/myapp/memory.low

# 加进程
echo $$ > /sys/fs/cgroup/myapp/cgroup.procs

# PSI（压力）
cat /sys/fs/cgroup/myapp/memory.pressure
cat /sys/fs/cgroup/myapp/cpu.pressure
```

### 7.3 systemd 用 cgroup v2 限制服务

```ini
[Service]
Slice=myapp.slice
MemoryMax=2G
MemoryHigh=1.8G
CPUQuota=200%
CPUWeight=100
IOWeight=100
TasksMax=512
```

```bash
systemd-cgls                                    # 看 cgroup 树
systemd-cgtop                                   # top 风格

# 实时调整（不重启）
systemctl set-property myapp.service MemoryMax=4G
```

### 7.4 容器原理一图

```
container = chroot + namespace + cgroup + capability + seccomp + AppArmor/SELinux
           ↑      ↑           ↑        ↑            ↑          ↑
           隔离 fs  隔离 PID/net   限资源    限 root 权限   过滤 syscall  MAC
```

```bash
# 不靠 docker 起一个"容器"
mkdir /tmp/myroot && debootstrap stable /tmp/myroot
unshare --mount --uts --ipc --pid --fork --net --user \
    --map-root-user --mount-proc \
    chroot /tmp/myroot /bin/bash
```

## 八、内核深度调优

### 8.1 通用关键参数

```ini
# /etc/sysctl.d/99-tuning.conf

# 文件 / 进程
fs.file-max = 4194304
fs.nr_open = 2097152
fs.inotify.max_user_watches = 1048576
kernel.pid_max = 4194304

# 内存
vm.swappiness = 1                              # 数据库/AI 推理用 1
vm.dirty_ratio = 10
vm.dirty_background_ratio = 5
vm.overcommit_memory = 1
vm.max_map_count = 1048576                     # ES/Redis 必加

# Transparent HugePage
# 数据库一般关
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag

# 网络
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_max_syn_backlog = 32768
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 600
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq

# conntrack
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 1200

# AI 推理 / GPU 节点常用
vm.nr_hugepages = 0                            # 看场景
kernel.numa_balancing = 0                      # NUMA 绑定时关
```

### 8.2 NUMA 绑定

```bash
numactl --hardware                              # 看 NUMA 拓扑
numastat -p PID                                 # 进程 NUMA 分布

# 绑核 + 内存
numactl --cpunodebind=0 --membind=0 ./myapp
numactl --interleave=all ./myapp                # 均分

# systemd 服务
[Service]
NUMAPolicy=preferred
NUMAMask=0
CPUAffinity=0-15
```

### 8.3 io_uring（现代 IO）

```
io_uring (kernel 5.1+) = 异步 IO 革命
  - 共享 ring 队列，零 syscall 开销
  - 替代 epoll + AIO
  - 应用: Ceph / NVMe / 高性能存储

用法:
  - liburing 库
  - Linux 6.x 大量内核子系统采用
```

## 九、内核模块 + kpatch

### 9.1 内核模块

```bash
# 看
lsmod
modinfo nvidia
modprobe br_netfilter
modprobe -r nvidia                              # 卸载

# 持久化
echo br_netfilter > /etc/modules-load.d/k8s.conf

# 参数
cat > /etc/modprobe.d/nvidia.conf <<EOF
options nvidia NVreg_PreserveVideoMemoryAllocations=1
EOF

# 黑名单
cat > /etc/modprobe.d/blacklist-nouveau.conf <<EOF
blacklist nouveau
EOF
dracut --force                                  # RHEL 重建 initramfs
update-initramfs -u                             # Ubuntu
```

### 9.2 kpatch（不重启打内核补丁）

```bash
# RHEL / openEuler 商用支持
dnf install kpatch kpatch-dnf

# 自动订阅: 内核更新时自动应用
dnf kpatch auto

# 手动
kpatch list
kpatch load patch.ko
kpatch install patch.ko                          # 持久化

# kexec（快速重启，跳过 BIOS）
kexec -l /boot/vmlinuz-NEW \
    --initrd=/boot/initramfs-NEW.img --reuse-cmdline
systemctl kexec
```

## 十、国产 OS 适配

### 10.1 主流国产 OS

| OS | 基础 | 包管理 | 核心场景 |
|:---|:---|:---|:---|
| **openEuler 24.03 LTS** | 自研 | dnf | 服务器主力（华为系） |
| **Anolis OS 23** | RHEL 兼容 | dnf | 阿里系；CentOS 替代 |
| **OpenCloudOS 9** | RHEL 兼容 | dnf | 腾讯系 |
| **麒麟 V10 SP3** | RHEL/Debian | dnf/apt | 党政军 / 信创 |
| **统信 UOS V20** | Debian | apt | 桌面 + 服务器 |

### 10.2 openEuler 实战

```bash
# 安装
# 同 RHEL 一样: dnf install
dnf install -y nginx postgresql

# 内核
# openEuler 23.03+ 自研 6.x 内核, 支持 ARM/RISC-V
uname -r

# 国密
# OpenSSL 3.x with SM2/SM3/SM4
openssl ciphers -v | grep SM

# A-Tune（自研调优）
atune-adm list
atune-adm tuning --project web_server

# secGear（机密计算）
# isulad（轻量容器引擎，可替 Docker）
isulad-shim
```

### 10.3 麒麟 / 统信 信创实战

```
特色:
  - 飞腾/鲲鹏 ARM64 / 龙芯 LoongArch / 申威 sw_64 多架构支持
  - PKS 体系（Phytium-Kylin-Sugon）
  - 国密 SM2/SM3/SM4 集成
  - 等保 2.0 合规
  - 银河麒麟服务器版 / 桌面版分立

注意:
  - rpm/deb 双形态都有
  - 内核版本相对保守（4.19 / 5.4）
  - 部分新工具（eBPF/bpftrace）支持滞后
```

### 10.4 适配 Checklist

```
☐ 内核版本是否支持目标特性
   bpftrace 需 4.9+, io_uring 需 5.1+
☐ glibc 兼容（升级到目标 OS 主线）
☐ 包依赖（部分包名不同：python3-XXX）
☐ SELinux / AppArmor 策略
☐ systemd 版本与 unit 兼容
☐ 防火墙工具（firewalld / nftables）
☐ 时间同步（chrony 默认）
☐ 国密 OpenSSL（部分场景必需）
☐ 容器 runtime（iSulad / docker / containerd）
☐ 镜像源切换（kylinos.cn / openeuler.org）
```

## 十一、典型场景案例

### 11.1 案例：突发 CPU 飙升

```bash
# Step 1: 确认负载
uptime                                         # load 50, CPU 16 核 → 严重

# Step 2: 哪类 CPU？
mpstat 1 3                                     # %usr 95 → 应用瓶颈

# Step 3: 哪个进程哪个线程？
top -o %CPU
top -H -p PID                                  # 看 TID

# Step 4: perf 看热函数
perf record -F 99 -p PID -g -- sleep 30
perf script | ./stackcollapse-perf.pl | ./flamegraph.pl > flame.svg

# 常见根因:
# - 死循环
# - 正则回溯（ReDoS）
# - 锁竞争 spinning
# - GC（Java）
```

### 11.2 案例：网络丢包

```bash
# Step 1: 接口错误
ip -s link show eth0                           # RX errors/dropped > 0

# Step 2: 协议栈
nstat -az | grep -E "Retrans|Drops"
# tcp_listen_overflows 暴涨 → accept 队列满 → 调 somaxconn

# Step 3: 队列
ss -ltn                                        # Send-Q > Recv-Q

# Step 4: 抓包确认
tcpdump -i eth0 -nn -c 100 'tcp port 80 and tcp[tcpflags] & tcp-rst != 0'

# Step 5: 内核日志
dmesg -T | grep -E "drop|softirq"
```

### 11.3 案例：load 高但 CPU 不忙

```bash
uptime                                          # load 30, CPU 8
top                                             # CPU 5% 空闲多

# load 包含 D 状态（不可中断睡眠，多为 IO 等待）
ps -eLo stat,pid,cmd | awk '$1 ~ /D/'

iostat -xz 1                                   # %iowait 高
cat /proc/PID/stack                             # 在哪等
cat /proc/PID/wchan
```

## 十二、典型坑（高级）

| 坑 | 建议 |
|:---|:---|
| **看 free 不看 available** | available 才是真实可用 |
| **看 %util 判断 SSD 饱和** | 多队列 SSD 看 await |
| **strace 生产慎用** | 用 bpftrace |
| **conntrack 满了不知道** | dmesg "table full" |
| **没火焰图直接调** | 不知道热点 |
| **跨 NUMA 没排查** | numastat -p PID |
| **THP 默认开导致延迟抖动** | 数据库一般关 |
| **swap 没设 swappiness=1** | DB/AI 节点必调 |
| **conntrack hash 没改** | 只改 max 不够 |
| **iptables vs nftables 混用** | iptables-nft 兼容层注意 |

## 十三、高级 Checklist

```
方法论:
☐ USE / 60s 速查熟练
☐ 火焰图能读 + 能做
☐ bpftrace 一行常用 5 条

CPU/内存/IO:
☐ perf record + report
☐ smem / PSS / USS 区别
☐ OOM Killer 评分懂
☐ iostat / iotop / biolatency
☐ NUMA 拓扑 + 绑核

网络:
☐ ss -tin 各字段读
☐ conntrack 监控 + 调
☐ nftables 写 ruleset
☐ XDP / RPS / RSS 概念

内核底座:
☐ namespace / unshare / nsenter
☐ cgroup v2 + systemd Slice
☐ 内核模块 + dracut/initramfs
☐ kpatch / kexec
☐ io_uring 概念

国产:
☐ openEuler / Anolis 装过
☐ 麒麟 / 统信 部署过
☐ ARM64 / LoongArch 适配
```

## 十四、推荐栈

```
观测:
  perf / bpftrace / BCC tools
  Brendan Gregg FlameGraph
  sar / sysstat (历史基线)

调优:
  sysctl.d / tuned profile
  numactl / cgroup v2

网络:
  ss / nftables / conntrack
  ethtool / Cilium (eBPF)

容器底座:
  unshare / nsenter / systemd-cgls
  iSulad (国产) / containerd

国产 OS:
  openEuler 24.03 LTS
  Anolis OS 23
  麒麟 V10 SP3 / 统信 UOS V20
```

## 十五、学习路径

```
高级（6-12 月）:
  1. USE 方法论 + 60s 速查
  2. perf record + 火焰图
  3. bpftrace 单行排查
  4. ss -tin / TCP 状态机 / conntrack
  5. namespace + cgroup v2 手撸
  6. NUMA + IRQ 绑核
  7. 内核模块 + initramfs
  8. nftables 完整 ruleset
  9. RHEL/Anolis/openEuler 切换
  10. ARM64 适配

专家:
  11. 内核源码读
  12. XDP / Cilium 数据面
  13. io_uring 应用
  14. kpatch / kexec
  15. 自研 eBPF 工具
```

## 十六、参考资料

```
大师:
  - Brendan Gregg: brendangregg.com ⭐
  - 《Systems Performance》
  - 《BPF Performance Tools》
  - 《Linux 性能优化实战》倪朋飞

官方:
  - kernel.org Documentation
  - perf wiki / bpftrace tutorial / BCC tools
  - openEuler / Anolis / Kylin 官方文档

社区:
  - LWN.net
  - r/linux / r/eBPF
  - 国内: 极客时间 / InfoQ 性能专栏
```

> 📖 **核心判断**：高级 = **bpftrace 一行排查 + 火焰图 + cgroup v2/namespace 手撸 + nftables/conntrack + NUMA 绑核 + 国产 OS**。会读火焰图比记 100 个工具值钱，会用 bpftrace 比 strace 强 10 倍。能在 openEuler/麒麟上排查生产疑难、能解释 cgroup v2 PSI、能手写 nftables ruleset，就有资格做 SRE 团队的技术担当。

