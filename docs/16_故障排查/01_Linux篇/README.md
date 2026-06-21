# Linux 篇故障排查

## CPU 100%

```bash
# 1. 定位高 CPU 进程
top -c
ps aux --sort=-%cpu | head -10

# 2. 查看线程
ps -T -p <PID>

# 3. 性能采样
perf top -p <PID>
perf record -p <PID> -a -g -- sleep 10
perf report

# 4. 生成火焰图
perf script > out.perf
./stackcollapse-perf.pl out.perf > out.folded
./flamegraph.pl out.folded > cpu.svg
```

## 内存泄漏

```bash
# 1. 查看内存使用
free -h
cat /proc/meminfo

# 2. 进程内存详情
top -o %MEM
pmap -x <PID>

# 3. OOM 检查
dmesg | grep -i oom
journalctl -k | grep -i oom
```

## 磁盘写满

```bash
# 1. 查看容量
df -h

# 2. 找大文件
du -sh /* 2>/dev/null | sort -rh | head -10
find / -xdev -type f -size +1G -exec ls -lh {} \; 2>/dev/null

# 3. 找已删除但未释放的文件（进程持有句柄）
lsof | grep deleted

# 4. 清理
# 日志、Docker 镜像、临时文件、内核包
```
