#### Linux下cgroup的认识

#### cgroup是Linux下的一种将进程按组进行管理的机制，在用户层看来，cgroup技术就是把系统中的所有进程组织成一颗一颗独立的树，每棵树都包含系统的所有进程，树的每个节点是一个进程组，而每颗树又和一个或者多个subsystem关联，树的作用是将进程分组，而subsystem的作用就是对这些组进行操作。cgroup主要包括下面两部分：
* subsystem： 一个subsystem就是一个内核模块，他被关联到一颗cgroup树之后，就会在树的每个节点（进程组）上做具体的操作。subsystem经常被称作"resource controller"，因为它主要被用来调度或者限制每个进程组的资源，但是这个说法不完全准确，因为有时我们将进程分组只是为了做一些监控，观察一下他们的状态，比如perf_event subsystem。到目前为止，Linux支持12种subsystem，比如限制CPU的使用时间，限制使用的内存，统计CPU的使用情况，冻结和恢复一组进程等。

* hierarchy： 一个hierarchy可以理解为一棵cgroup树，树的每个节点就是一个进程组，每棵树都会与零到多个subsystem关联。在一颗树里面，会包含Linux系统中的所有进程，但每个进程只能属于一个节点（进程组）。系统中可以有很多颗cgroup树，每棵树都和不同的subsystem关联，一个进程可以属于多颗树，即一个进程可以属于多个进程组，只是这些进程组和不同的subsystem关联。目前Linux支持12种subsystem，如果不考虑不与任何subsystem关联的情况（systemd就属于这种情况），Linux里面最多可以建12颗cgroup树，每棵树关联一个subsystem，当然也可以只建一棵树，然后让这棵树关联所有的subsystem。当一颗cgroup树不和任何subsystem关联的时候，意味着这棵树只是将进程进行分组，至于要在分组的基础上做些什么，将由应用程序自己决定，systemd就是一个这样的例子。

#### 查看subsystem支持的类型
```sh
ubuntu@builder:~$ cat /proc/cgroups 
#subsys_name	hierarchy	num_cgroups	enabled
cpuset	        6	1	1
cpu	            10	45	1
cpuacct	        10	45	1
blkio	        2	45	1
memory	        4	96	1
devices	        11	45	1
freezer	        5	1	1
net_cls	        7	1	1
perf_event	    9	1	1
net_prio	    7	1	1
hugetlb	        3	1	1
pids	        12	50	1
rdma	        8	1	1
```

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

#### 如何查看当前进程属于哪些cgroup
```sh
ubuntu@builder:~$ cat  /proc/25796/cgroup 
11:cpuset:/
10:freezer:/
9:memory:/system.slice/cron.service
8:blkio:/system.slice/cron.service
7:perf_event:/
6:net_cls,net_prio:/
5:devices:/system.slice/cron.service
4:hugetlb:/
3:cpu,cpuacct:/system.slice/cron.service
2:pids:/system.slice/cron.service
1:name=systemd:/system.slice/cron.service
```
##### 每一行包含用冒号隔开的三列，他们的意思分别是:

1. cgroup树的ID， 和/proc/cgroups文件中的ID一一对应。
2. 和cgroup树绑定的所有subsystem，多个subsystem之间用逗号隔开。这里name=systemd表示没有和任何subsystem绑定，  
只是给他起了个名字叫systemd。
3. 进程在cgroup树中的路径，即进程所属的cgroup，这个路径是相对于挂载点的相对路径。


#### 目前Linux支持下面12种subsystem
```yml
cpu (since Linux 2.6.24; CONFIG_CGROUP_SCHED)
用来限制cgroup的CPU使用率。

cpuacct (since Linux 2.6.24; CONFIG_CGROUP_CPUACCT)
统计cgroup的CPU的使用率。

cpuset (since Linux 2.6.24; CONFIG_CPUSETS)
绑定cgroup到指定CPUs和NUMA节点。

memory (since Linux 2.6.25; CONFIG_MEMCG)
统计和限制cgroup的内存的使用率，包括process memory, kernel memory, 和swap。

devices (since Linux 2.6.26; CONFIG_CGROUP_DEVICE)
限制cgroup创建(mknod)和访问设备的权限。

freezer (since Linux 2.6.28; CONFIG_CGROUP_FREEZER)
suspend和restore一个cgroup中的所有进程。

net_cls (since Linux 2.6.29; CONFIG_CGROUP_NET_CLASSID)
将一个cgroup中进程创建的所有网络包加上一个classid标记，用于tc和iptables。
只对发出去的网络包生效，对收到的网络包不起作用。

blkio (since Linux 2.6.33; CONFIG_BLK_CGROUP)
限制cgroup访问块设备的IO速度。

perf_event (since Linux 2.6.39; CONFIG_CGROUP_PERF)
对cgroup进行性能监控

net_prio (since Linux 3.3; CONFIG_CGROUP_NET_PRIO)
针对每个网络接口设置cgroup的访问优先级。

hugetlb (since Linux 3.5; CONFIG_CGROUP_HUGETLB)
限制cgroup的huge pages的使用量。

pids (since Linux 4.3; CONFIG_CGROUP_PIDS)
限制一个cgroup及其子孙cgroup中的总进程数。
```

#### 引用：https://segmentfault.com/a/1190000006917884