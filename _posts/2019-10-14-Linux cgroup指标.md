#### cgroup pids、memory、cpu下的指标

#### 查看系统已挂载好的cgroup
```sh
ubuntu@builder:~$ mount |grep cgroup
tmpfs on /sys/fs/cgroup type tmpfs (ro,nosuid,nodev,noexec,mode=755)
cgroup on /sys/fs/cgroup/unified type cgroup2 (rw,nosuid,nodev,noexec,relatime)
cgroup on /sys/fs/cgroup/systemd type cgroup (rw,nosuid,nodev,noexec,relatime,xattr,name=systemd)
cgroup on /sys/fs/cgroup/blkio type cgroup (rw,nosuid,nodev,noexec,relatime,blkio)
cgroup on /sys/fs/cgroup/hugetlb type cgroup (rw,nosuid,nodev,noexec,relatime,hugetlb)
cgroup on /sys/fs/cgroup/memory type cgroup (rw,nosuid,nodev,noexec,relatime,memory)
cgroup on /sys/fs/cgroup/freezer type cgroup (rw,nosuid,nodev,noexec,relatime,freezer)
cgroup on /sys/fs/cgroup/cpuset type cgroup (rw,nosuid,nodev,noexec,relatime,cpuset)
cgroup on /sys/fs/cgroup/net_cls,net_prio type cgroup (rw,nosuid,nodev,noexec,relatime,net_cls,net_prio)
cgroup on /sys/fs/cgroup/rdma type cgroup (rw,nosuid,nodev,noexec,relatime,rdma)
cgroup on /sys/fs/cgroup/perf_event type cgroup (rw,nosuid,nodev,noexec,relatime,perf_event)
cgroup on /sys/fs/cgroup/cpu,cpuacct type cgroup (rw,nosuid,nodev,noexec,relatime,cpu,cpuacct)
cgroup on /sys/fs/cgroup/devices type cgroup (rw,nosuid,nodev,noexec,relatime,devices)
cgroup on /sys/fs/cgroup/pids type cgroup (rw,nosuid,nodev,noexec,relatime,pids)
```

#### 内存参数
```yml
 cgroup.event_control       #用于eventfd的接口
 memory.usage_in_bytes      #显示当前已用的内存
 memory.limit_in_bytes      #设置/显示当前限制的内存额度
 memory.failcnt             #显示内存使用量达到限制值的次数
 memory.max_usage_in_bytes  #历史内存最大使用量
 memory.soft_limit_in_bytes #设置/显示当前限制的内存软额度
 memory.stat                #显示当前cgroup的内存使用情况
 memory.use_hierarchy       #设置/显示是否将子cgroup的内存使用情况统计到当前cgroup里面
 memory.force_empty         #触发系统立即尽可能的回收当前cgroup中可以回收的内存
 memory.pressure_level      #设置内存压力的通知事件，配合cgroup.event_control一起使用
 memory.swappiness          #设置和显示当前的swappiness
 memory.move_charge_at_immigrate #设置当进程移动到其他cgroup中时，它所占用的内存是否也随着移动过去
 memory.oom_control         #设置/显示oom controls相关的配置
 memory.numa_stat           #显示numa相关的内存
```
#### 设置进程内存限制
```sh
# 当前cgroup下创建子cgroup（默认继承了上级cgroup）
root@builder:/sys/fs/cgroup/memory# mkdir test
root@builder:/sys/fs/cgroup/memory# cd test/
root@builder:/sys/fs/cgroup/memory/test# ls
cgroup.clone_children           memory.kmem.tcp.failcnt             memory.oom_control
cgroup.event_control            memory.kmem.tcp.limit_in_bytes      memory.pressure_level
cgroup.procs                    memory.kmem.tcp.max_usage_in_bytes  memory.soft_limit_in_bytes
memory.failcnt                  memory.kmem.tcp.usage_in_bytes      memory.stat
memory.force_empty              memory.kmem.usage_in_bytes          memory.swappiness
memory.kmem.failcnt             memory.limit_in_bytes               memory.usage_in_bytes
memory.kmem.limit_in_bytes      memory.max_usage_in_bytes           memory.use_hierarchy
memory.kmem.max_usage_in_bytes  memory.move_charge_at_immigrate     notify_on_release
memory.kmem.slabinfo            memory.numa_stat                    tasks
# 添加进程pid到cgroup(pids和cpu限制方法相同)
root@builder:/sys/fs/cgroup/memory/test# echo $PID > cgroup.procs
# 设置配额（修改memory.usage_in_bytes值）
root@builder:/sys/fs/cgroup/memory/test# cat memory.limit_in_bytes 
9223372036854771712
root@builder:/sys/fs/cgroup/memory/test# cat memory.usage_in_bytes 
974848
root@builder:/sys/fs/cgroup/memory/test# echo 500M > memory.limit_in_bytes 
root@builder:/sys/fs/cgroup/memory/test# cat memory.limit_in_bytes 
524288000
# 删除限制
root@builder:/sys/fs/cgroup/memory/test# echo -1 > memory.limit_in_bytes 
root@builder:/sys/fs/cgroup/memory/test# cat memory.limit_in_bytes 
9223372036854771712
```
#### CPU
```sh
root@builder:/sys/fs/cgroup/cpu# mkdir test 
root@builder:/sys/fs/cgroup/cpu# cd test/
root@builder:/sys/fs/cgroup/cpu/test# ls
cgroup.clone_children  cpu.shares     cpuacct.usage_all          cpuacct.usage_sys
cgroup.procs           cpu.stat       cpuacct.usage_percpu       cpuacct.usage_user
cpu.cfs_period_us      cpuacct.stat   cpuacct.usage_percpu_sys   notify_on_release
cpu.cfs_quota_us       cpuacct.usage  cpuacct.usage_percpu_user  tasks
```
cfs_period_us用来配置时间周期长度，cfs_quota_us用来配置当前cgroup在设置的周期长度内所能使用的CPU时间数，两个文件配合起来设置CPU的使用上限。两个文件的单位都是微秒（us），cfs_period_us的取值范围为1毫秒（ms）到1秒（s），cfs_quota_us的取值大于1ms即可，如果cfs_quota_us的值为-1（默认值），表示不受cpu时间的限制。下面是几个例子：
```yml
1. 限制只能使用1个CPU（每250ms能使用250ms的CPU时间）
    # echo 250000 > cpu.cfs_quota_us /* quota = 250ms */
    # echo 250000 > cpu.cfs_period_us /* period = 250ms */

2. 限制使用2个CPU（内核）（每500ms能使用1000ms的CPU时间，即使用两个内核）
    # echo 1000000 > cpu.cfs_quota_us /* quota = 1000ms */
    # echo 500000 > cpu.cfs_period_us /* period = 500ms */

3. 限制使用1个CPU的20%（每50ms能使用10ms的CPU时间，即使用一个CPU核心的20%）
    # echo 10000 > cpu.cfs_quota_us /* quota = 10ms */
    # echo 50000 > cpu.cfs_period_us /* period = 50ms */
```

cpu.shares 用来设置CPU的相对值，并且是针对所有的CPU（内核），默认值是1024，假如系统中有两个cgroup，分别是A和B，A的shares值是1024，B的shares值是512，那么A将获得1024/(1204+512)=66%的CPU资源，而B将获得33%的CPU资源。shares有两个特点：
1. 如果A不忙，没有使用到66%的CPU时间，那么剩余的CPU时间将会被系统分配给B，即B的CPU使用率可以超过33%
2. 如果添加了一个新的cgroup C，且它的shares值是1024，那么A的限额变成了1024/(1204+512+1024)=40%，B的变成了20%

从上面两个特点可以看出：
* 在闲的时候，shares基本上不起作用，只有在CPU忙的时候起作用，这是一个优点。
* 由于shares是一个绝对值，需要和其它cgroup的值进行比较才能得到自己的相对限额，而在一个部署很多容器的机器上，cgroup的数量是变化的，所以这个限额也是变化的，自己设置了一个高的值，但别人可能设置了一个更高的值，所以这个功能没法精确的控制CPU使用率。

cpu.stat 包含了下面三项统计结果:
1. nr_periods： 表示过去了多少个cpu.cfs_period_us里面配置的时间周期
2. nr_throttled： 在上面的这些周期中，有多少次是受到了限制（即cgroup中的进程在指定的时间周期中用光了它的配额）
3. throttled_time: cgroup中的进程被限制使用CPU持续了多长时间(纳秒)

#### PID
```sh
root@builder:/sys/fs/cgroup/pids# mkdir test
root@builder:/sys/fs/cgroup/pids# cd test/
root@builder:/sys/fs/cgroup/pids/test# ls
cgroup.clone_children  cgroup.procs  notify_on_release  pids.current  pids.events  pids.max  tasks
```
```yml
pids.current: 表示当前cgroup及其所有子孙cgroup中现有的总的进程数量
pids.max: 当前cgroup及其所有子孙cgroup中所允许创建的总的最大进程数量，在根cgroup下没有这个文件，因为我们没有必要限制整个系统所能创建的进程数量。
```
#### 限制进程数(配置当前bash最大进程数为1,即：无法运行子命令)
```sh
root@builder:/sys/fs/cgroup/pids/test# cat pids.max 
max
root@builder:/sys/fs/cgroup/pids/test# echo 1 >pids.max 
root@builder:/sys/fs/cgroup/pids/test# echo $$ >cgroup.procs
root@builder:/sys/fs/cgroup/pids/test# ls
bash: fork: retry: Resource temporarily unavailable
bash: fork: retry: Resource temporarily unavailable
bash: fork: retry: Resource temporarily unavailable
bash: fork: retry: Resource temporarily unavailable
bash: fork: Resource temporarily unavailable
```

#### 删除限制
```sh
root@builder:/sys/fs/cgroup/memory# rmdir test/
```