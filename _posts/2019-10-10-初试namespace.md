#### 初试namespace

#### namespace概念
##### 通过 namespace 可以让一些进程只能看到与自己相关的一部分资源，而另外一些进程也只能看到与它们自己相关的资源，这两拨进程根本就感觉不到对方的存在。具体的实现方式是把一个或多个进程的相关资源指定在同一个 namespace 中。  
##### Linux namespaces 是对全局系统资源的一种封装隔离，使得处于不同 namespace 的进程拥有独立的全局系统资源，改变一个 namespace 中的系统资源只会影响当前 namespace 里的进程，对其他 namespace 中的进程没有影响。

#### 隔离能力
![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/952033-20180725130447798-998138444.png)

#### 通过/proc查看namespace
##### 查看进程ns信息  
![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/20191010172621.png)

这些namespace文件都是链接文件，链接文件的内容的格式为 xxx:[inode number]  
xxx为ns类型，inode number为ns的ID，上面两个进程相同类型ns ID一致，说明在同一ns下 
```yml
UTS namespace: 用来隔离系统的hostname以及NIS domain name.  
IPC namespace: 用来隔离System V IPC objects和POSIX message queues.
MNT namespace: 用来隔离文件系统的挂载点, 使得不同的mnt namespace拥有自己独立的挂载点信息，
不同的namespace之间不会相互影响,这对于构建用户或者容器自己的文件系统目录非常有用.
当前进程所在mnt namespace里的所有挂载信息可以在/proc/[pid]/mounts、
/proc/[pid]/mountinfo和/proc/[pid]/mountstats里面找到.  
PID namespaces: 用来隔离进程的ID空间，使得不同pid namespace里的进程ID可以重复且相互之间不影响.  
NETWORK namespace: 用来隔离网络设备,IP地址,端口等.每个namespace将会有
自己独立的网络栈、路由表、防火墙规则、socket等.  
User namespace: 用来隔离user权限相关的Linux资源，包括user IDs and group IDs，keys , 和capabilities.  
```
#### namespace相关API
```yml
clone: 创建一个新的进程并把他放到新的namespace中
setns: 将当前进程加入到已有的namespace中
unshare: 使当前进程退出指定类型的namespace，并加入到新创建的namespace
```