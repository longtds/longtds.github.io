# 性能排查

## CPU 性能排查

```bash
# 实时查看 CPU 使用率
top / htop

# 按 CPU 使用率排序进程
ps aux --sort=-%cpu | head -10

# 查看 CPU 上下文切换
vmstat 1 5

# 查看每个 CPU 的使用率
mpstat -P ALL 1

# 使用 perf 采样
perf top
perf record -a -g -- sleep 30
perf report

# 生成火焰图
perf script | ./stackcollapse-perf.pl | ./flamegraph.pl > cpu.svg
```

## 内存性能排查

```bash
# 内存使用概况
free -h

# 详细内存信息
cat /proc/meminfo

# 查看进程内存
top -o %MEM

# 查看内存映射
pmap -x <PID>

# Slab 缓存
slabtop

# OOM 日志
dmesg | grep -i oom
journalctl -k | grep -i oom
```

## 磁盘性能排查

```bash
# 磁盘 IO 实时监控
iostat -x 1

# IO 排队情况
iotop

# 磁盘吞吐/delay
sar -d 1

# 文件系统使用率
df -h

# 查看 IO 等待
top  # 看 wa%
```

## 网络性能排查

```bash
# 网络连接状态
ss -tuln
ss -state established

# 带宽测试
iperf3 -c <server>

# 抓包分析
tcpdump -i eth0 -w capture.pcap

# 网卡统计
ethtool -S eth0
ip -s link show eth0
```
