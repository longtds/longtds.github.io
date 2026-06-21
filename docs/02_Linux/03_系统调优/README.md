# 系统调优

## 内核参数调优

```bash
# /etc/sysctl.conf 常用参数

# 网络调优
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# 内存调优
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.dirty_ratio = 20
vm.dirty_background_ratio = 5

# 文件系统调优
fs.file-max = 6553500
fs.nr_open = 6553500

# 生效
sysctl -p /etc/sysctl.conf
```

## CPU 调优

- **CPU 频率调节器**：`cpupower frequency-set --governor performance`
- **进程绑定**：`taskset -c 0-3 <command>` 绑定到指定核心
- **中断亲和性**：`echo 1 > /proc/irq/<IRQ>/smp_affinity`

## 内存调优

- **大页（HugePages）**：减少 TLB Miss，提升数据库性能
- **内存预留**：通过 `kernelcore` 和 `movablecore` 参数

## IO 调优

```bash
# 查看 IO 调度器
cat /sys/block/sda/queue/scheduler

# 设置调度器
echo none > /sys/block/sda/queue/scheduler    # NVMe 推荐 none
echo kyber > /sys/block/sda/queue/scheduler   # SSD 推荐 kyber

# 队列深度
cat /sys/block/sda/queue/nr_requests
echo 256 > /sys/block/sda/queue/nr_requests
```
