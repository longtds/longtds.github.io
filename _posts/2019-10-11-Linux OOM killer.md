#### OOM killer机制

#### 当物理内存和交换空间都被用完时，如果还有进程来申请内存，内核将触发OOM killer，其行为如下：
1. 检查文件/proc/sys/vm/panic_on_oom，如果里面的值为2，那么系统一定会触发panic
2. 如果/proc/sys/vm/panic_on_oom的值为1，那么系统有可能触发panic
3. 如果/proc/sys/vm/panic_on_oom的值为0，或者上一步没有触发panic，那么内核继续检查文件/proc/sys/vm/oom_kill_allocating_task
4. 如果/proc/sys/vm/oom_kill_allocating_task为1，那么内核将kill掉当前申请内存的进程
5. 如果/proc/sys/vm/oom_kill_allocating_task为0，内核将检查每个进程的分数，分数最高的进程将被kill掉

#### 进程被kill掉之后，如果/proc/sys/vm/oom_dump_tasks为1，且系统的rlimit中设置了core文件大小，将会由/proc/sys/kernel/core_pattern里面指定的程序生成core dump文件，这个文件里将包含pid, uid, tgid, vm size, rss, nr_ptes, nr_pmds, swapents, oom_score_adj，score, name等内容，拿到这个core文件之后，可以做一些分析，看为什么这个进程被选中kill掉。

#### ubuntu18.04中默认设置：
```sh
# OOM后不panic
ubuntu@builder:~$ cat /proc/sys/vm/panic_on_oom
0
# OOM后kill掉分数最高的进程
ubuntu@builder:~$ cat /proc/sys/vm/oom_kill_allocating_task
0
# 进程由于OOM被kill掉后将生成core dump文件
ubuntu@builder:~$ cat /proc/sys/vm/oom_dump_tasks
1
# 默认max core file size是0,所以系统不会生成core文件
ubuntu@builder:~$ prlimit|grep CORE
CORE max core file size 0 unlimited blocks
# core dump文件的生成交给了apport
ubuntu@builder:~$ cat /proc/sys/kernel/core_pattern
|/usr/share/apport/apport %p %s %c %d %P
```
#### panic_on_oom
该文件的值可以取0/1/2，0是不触发panlic，2是一定触发panlic，如果为1的话就要看mempolicy和cpusets  
panic后内核的默认行为是死在那里，目的是给开发人员一个连上去debug的机会。但对于大多数应用层开发人员来说没啥用，倒是希望它赶紧重启。  
为了让内核panic后重启，可以修改文件/proc/sys/kernel/panic，里面表示的是panic多少秒后系统将重启，这个文件的默认值是0，表示永远不重启。
```sh
#设置panic后3秒重启系统
echo 3 > /proc/sys/kernel/panic
```
#### OOM killer触发后的日志
一旦OOM killer被触发，内核将会生成相应的日志，一般可以在/var/log/messages里面看到，如果配置了syslog，日志可能在/var/log/syslog里面，这里是ubuntu里的日志样例：
```sh
ubuntu@builder:~$ grep oom /var/log/syslog
Jan 23 21:30:29 ubuntu kernel: [  490.006836] eat_memory invoked oom-killer: gfp_mask=0x24280ca, order=0, oom_score_adj=0
Jan 23 21:30:29 ubuntu kernel: [  490.006871]  [<ffffffff81191442>] oom_kill_process+0x202/0x3c0
```
#### cgroup的OOM killer
除了系统的OOM killer之外，如果配置了memory cgroup，那么进程还将受到自己所属memory cgroup的限制，如果超过了cgroup的限制，将会触发cgroup的OOM killer.

#### 进程分数
1. 当oom_kill_allocating_task的值为0时（系统默认配置），系统会kill掉系统中分数最高的那个进程，这里的分数是怎么来的呢？该值由内核维护，并存储在每个进程的/proc/<pid>/oom_score文件中
2. 每个进程的分数受多方面的影响，比如进程运行的时间，时间越长表明这个程序越重要，所以分数越低；进程从启动后分配的内存越多，表示越占内存，分数会越高
##### 由于分数计算复杂，比较难控制，于是内核提供了另一个文件用来调控分数，那就是文件/proc/<pid>/oom_adj，这个文件的默认值是0，但它可以配置为-17到15中间的任何一个值，内核在计算了进程的分数后，会和这个文件的值进行一个计算，得到的结果会作为进程的最终分数写入/proc/<pid>/oom_score，计算方式大概如下：

1. 如果/proc/<pid>/oom_adj的值为正数，那么分数将会被乘以2的n次方，这里n是文件里面的值

2. 如果/proc/<pid>/oom_adj的值为负数，那么分数将会被除以2的n次方，这里n是文件里面的值

##### 由于进程的分数在内核中是一个16位的整数，所以-17就意味着最终进程的分数永远是0，也即永远不会被kill掉。