# 基础

> Linux 基础 = **命令行操作 + 用户权限 + 文件系统 + 进程管理 + 包管理 + 网络基础 + systemd 入门 + 日志查看**。掌握本章 50 个核心命令，能独立完成 80% 的日常运维操作。本章面向新手和入职 1 年内的工程师。

## 一、命令行环境

### 1.1 Shell 基础

```bash
# 看当前 shell
echo $SHELL
echo $0

# 常用 shell
/bin/bash       Bash (最通用)
/bin/zsh        Zsh (Mac/Arch 默认, 推荐)
/bin/sh         POSIX shell (容器内常见)
/bin/dash       Debian Almquist shell (Ubuntu sh)
/bin/fish       Fish (友好交互)

# 修改默认 shell
chsh -s /bin/zsh
cat /etc/shells              # 系统支持的 shell 列表

# 当前用户/主机/路径
whoami
hostname
hostnamectl                  # systemd 方式
pwd
```

### 1.2 命令查找

```bash
which ls                     # 命令路径
type ls                      # alias/builtin/function/external
type -a ls                   # 全部匹配
command -v docker           # POSIX 标准检查
whereis bash                 # 可执行文件 + man + source
locate nginx.conf           # 数据库查找（updatedb 更新）
find / -name "*.conf" 2>/dev/null    # 实时查找
```

### 1.3 历史与快捷键

```bash
history                      # 命令历史
history | tail -20
!!                           # 上一条
!cmd                         # 上一条 cmd 开头的
!$                           # 上条最后一个参数
ctrl+r                       # 反向搜索 ⭐
ctrl+a / ctrl+e             # 行首 / 行尾
ctrl+w / ctrl+u             # 删除一个单词 / 整行
ctrl+l                       # 清屏 (= clear)
ctrl+c / ctrl+d             # 中断 / EOF（退出）

# 历史配置 (~/.bashrc)
export HISTSIZE=10000
export HISTFILESIZE=20000
export HISTTIMEFORMAT="%F %T "      # 带时间戳
export HISTCONTROL=ignoreboth        # 忽略重复 + 空格开头
```

## 二、文件操作

### 2.1 基本操作

```bash
# 查看
ls
ls -la                       # 含隐藏 + 详细
ls -lh                       # 人类可读大小
ls -lt                       # 按时间排
ls -lS                       # 按大小排
ls -lR                       # 递归

# 移动 / 复制 / 删除
mv src dst
cp -a src dst                # archive：保留属性 + 递归
cp -r dir1 dir2
rm file
rm -rf dir                   # ⚠️ 不可恢复, 确认路径
rm -i file                   # 交互式
\rm                          # 绕过 alias

# 创建
mkdir -p /a/b/c              # 递归创建
touch newfile
> empty.txt                  # 创建空 / 清空

# 软硬链接
ln -s /target /linkname      # 软链接（symlink）
ln /target /linkname         # 硬链接
ls -l linkname               # 看链接

# 看路径
realpath /etc/localtime      # 解析软链
readlink -f /etc/localtime
basename /a/b/c.txt          # c.txt
dirname /a/b/c.txt           # /a/b
```

### 2.2 查看文件内容

```bash
cat file.txt                 # 全文
tac file.txt                 # 倒序
less file.txt                # 分页（推荐, q 退出, /搜索, n下个）
more file.txt                # 老式分页
head -n 20 file              # 前 20 行
tail -n 20 file              # 后 20 行
tail -f /var/log/app.log     # 跟踪 ⭐
tail -F /var/log/app.log     # 跟踪 + 处理 rotate

# 看大文件不卡
zcat file.gz                 # gzip
xzcat file.xz                # xz
bzcat file.bz2               # bz2
zless file.gz                # 分页看压缩
```

### 2.3 文件类型与属性

```bash
file /etc/passwd             # 类型识别
stat file.txt                # 详细 (大小/时间/权限)
ls -la                       # 简略

# 时间属性 (atime/mtime/ctime)
# atime  访问时间 (read)
# mtime  修改时间 (内容变更) ⭐
# ctime  状态变化 (元数据/inode 变更)
touch -t 202401011200 file   # 改时间
```

### 2.4 文件查找

```bash
# find（最强）
find / -name "*.conf" 2>/dev/null
find /home -type f -mtime -7         # 7 天内修改
find /tmp -size +1G                  # 大于 1G
find /var -type f -mmin -30          # 30 分钟内
find / -user alice                   # 属于 alice
find / -perm 4000                    # SUID 文件
find . -name "*.log" -delete         # 找并删
find . -name "*.tmp" -exec rm {} \;  # 执行
find . -name "*.tmp" -exec rm {} +   # 批量

# 替代品（更快）
fd "*.conf"                          # fd-find
locate nginx.conf                    # mlocate (定期更新)
```

## 三、文本处理基础

### 3.1 三剑客入门

```bash
# grep - 查
grep "error" file.log
grep -i "error" file                 # 忽略大小写
grep -v "DEBUG" file                 # 反向
grep -n "error" file                 # 行号
grep -c "error" file                 # 计数
grep -r "TODO" .                     # 递归
grep -A 2 -B 2 "error"               # 前后 2 行
grep -E "error|warn"                 # 扩展正则

# 推荐用 ripgrep（速度快 10×）
rg "error" .
rg -t py "import"                    # 仅 Python 文件

# sed - 改
sed 's/old/new/g' file               # 替换
sed -i 's/old/new/g' file            # in-place
sed -n '10,20p' file                 # 打印 10-20 行
sed '/^#/d' file                     # 删 # 开头

# awk - 提
awk '{print $1}' file                # 第 1 列
awk -F: '{print $1}' /etc/passwd     # : 分隔
awk '$3 > 100' file                  # 条件
awk '{sum+=$3} END{print sum}' file  # 求和
```

### 3.2 排序与去重

```bash
sort file                            # 字母序
sort -n file                         # 数字
sort -r file                         # 倒序
sort -u file                         # 去重
sort -k 3 -n file                    # 按第 3 列
sort -t: -k3 -n /etc/passwd          # : 分隔

uniq                                  # 仅相邻去重 (常配 sort)
uniq -c                              # 计数
sort file | uniq -c | sort -rn       # 经典 top-N
```

### 3.3 列处理

```bash
cut -d: -f1 /etc/passwd              # 第 1 字段
cut -c 1-10 file                     # 1-10 字符
tr 'a-z' 'A-Z' < file                # 转大写
tr -d '\r' < file                    # 删 \r
paste a.txt b.txt                    # 并列合并
join -t: -1 1 -2 1 a.txt b.txt       # 按字段连接
```

### 3.4 重定向与管道

```bash
cmd > file                           # 覆盖输出
cmd >> file                          # 追加
cmd 2> err.log                       # 仅错误
cmd > out.log 2>&1                   # 合并
cmd &> all.log                       # bash 简写
cmd > /dev/null 2>&1                 # 丢弃全部

cmd1 | cmd2                          # 管道
cmd1 | tee file                      # 输出到屏幕 + 文件
cmd1 | tee -a file                   # 追加

# 输入
cmd < file
cmd <<EOF                            # heredoc
line1
line2
EOF

cmd <<<"single line input"           # herestring
```

## 四、用户与权限

### 4.1 用户基础

```bash
# 当前
whoami
id
groups

# 切换
su - alice                           # 完整登录环境
sudo -u alice cmd                    # 以 alice 执行
sudo -i                              # root shell
sudo cmd                             # 单次提权

# 创建/修改
useradd -m -s /bin/bash alice        # -m 建 home
passwd alice                          # 设密码
usermod -aG docker alice             # ⚠️ 必须 -a
userdel -r alice                     # -r 同时删 home

# 看
cat /etc/passwd                      # 用户列表
cat /etc/group                       # 组列表
cat /etc/shadow                      # 密码（仅 root）
last -n 10                           # 最近登录
who; w                                # 当前在线
```

### 4.2 权限

```bash
# rwx 三组：所有者 / 同组 / 其他
ls -l
-rw-r--r--   1 alice  staff  1024  Jun 26  file.txt
 |  ↑   ↑    所有者权限 / 同组 / 其他

# 数字
r=4 w=2 x=1
755 = rwxr-xr-x     # 目录推荐
644 = rw-r--r--     # 文件推荐
600 = rw-------     # 私密 (key)
700 = rwx------     # 私密目录 (.ssh)
777 = rwxrwxrwx     # ⚠️ 永远不要

# 修改
chmod 755 file
chmod u+x file                       # 给所有者执行
chmod g-w file                       # 同组去写
chmod o= file                        # 其他清零
chmod -R 644 dir                     # 递归

# 所有权
chown user:group file
chown -R alice:devs /data
chgrp devs file
```

### 4.3 sudo 基础

```bash
# 测试 sudo 权限
sudo -l                              # 看自己有哪些

# 配置（用 visudo, 不要直接编辑）
sudo visudo

# /etc/sudoers
alice         ALL=(ALL) ALL
%wheel        ALL=(ALL) ALL
bob           ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx

# 别名（高级见进阶章）
User_Alias DEVOPS = alice, bob
Cmnd_Alias WEB = /usr/bin/systemctl restart nginx
DEVOPS ALL=(ALL) NOPASSWD: WEB
```

## 五、进程管理

### 5.1 看进程

```bash
ps aux                               # BSD 风格 (所有进程)
ps -ef                               # System V 风格
ps -ef --forest                      # 树形
ps -eo pid,user,%cpu,%mem,cmd --sort=-%cpu | head    # 按 CPU 排

# 看某用户的
ps -u alice

# 看某程序
ps -C nginx
pgrep -fl nginx
pgrep -u alice                       # 该用户全部
```

### 5.2 top / htop

```bash
top                                  # 系统监视
# 交互:
#   P  按 CPU 排
#   M  按内存
#   c  完整命令
#   1  各 CPU 分开
#   k  kill 进程
#   q  退出

htop                                 # 彩色 + 交互（推荐）
btop                                 # 更炫
```

### 5.3 信号与 kill

```bash
# 常用信号
1   SIGHUP    挂断（很多服务用来 reload）
2   SIGINT    Ctrl+C
9   SIGKILL   强杀（不可捕获）
15  SIGTERM   优雅终止（默认）
18  SIGCONT   继续
19  SIGSTOP   停止

# 发送
kill PID
kill -9 PID                          # 强杀
kill -HUP $(pidof nginx)             # reload
kill -l                              # 列出所有信号

killall nginx                        # 按名字
pkill -f "java.*MyApp"               # 模式
pgrep -f pattern                     # 仅找不杀
```

### 5.4 前后台与作业

```bash
cmd &                                # 后台
jobs                                 # 当前 shell 后台任务
fg %1                                # 前台
bg %1                                # 继续后台
ctrl+z                               # 暂停 → 后台

# nohup（防 SSH 断开杀进程）
nohup ./long-task.sh &

# 现代：用 tmux
tmux new -s work                     # 新会话
tmux ls                              # 列表
tmux a -t work                       # 接入
# Ctrl+B d   分离（保留进程）
# Ctrl+B c   新窗口
# Ctrl+B "   水平分屏
# Ctrl+B %   垂直分屏
```

## 六、包管理基础

### 6.1 RHEL/Rocky/Alma/openEuler（dnf/yum）

```bash
# 装/卸
dnf install nginx
dnf remove nginx
dnf upgrade                          # 全量升级
dnf update --security                # 仅安全更新

# 查
dnf search keyword
dnf list installed | grep nginx
dnf info nginx
dnf provides /usr/bin/python3        # 文件属于哪个包

# 仓库
dnf repolist
dnf config-manager --add-repo url
dnf install epel-release             # EPEL 软件源

# 历史 + 回滚
dnf history
dnf history undo 5

# 离线 / RPM 文件
rpm -ivh package.rpm
rpm -qa | grep nginx
rpm -ql nginx                        # 看包内文件
rpm -qf /etc/nginx/nginx.conf        # 文件属于哪个包
```

### 6.2 Debian/Ubuntu（apt）

```bash
apt update                           # 刷新元数据
apt upgrade                          # 升级
apt install nginx
apt remove nginx                     # 保留配置
apt purge nginx                      # 连配置删
apt autoremove                       # 清依赖
apt search keyword
apt show nginx
apt list --installed

# DEB 文件
dpkg -i package.deb
dpkg -l | grep nginx
dpkg -L nginx                        # 文件列表
dpkg -S /etc/nginx/nginx.conf        # 文件属哪个包
```

### 6.3 通用工具

```bash
# Snap (Ubuntu)
snap install code --classic

# Homebrew (Linux 也支持)
curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash

# Python
pipx install black                   # 隔离环境（推荐）
uv tool install black                # 现代（2024+）
```

## 七、systemd 入门

### 7.1 服务管理（最常用）

```bash
# 启停重启
systemctl start nginx
systemctl stop nginx
systemctl restart nginx
systemctl reload nginx               # 重新加载配置（不重启）
systemctl status nginx               # 状态

# 开机自启
systemctl enable nginx
systemctl disable nginx
systemctl enable --now nginx         # 启用 + 启动

# 状态判断
systemctl is-active nginx
systemctl is-enabled nginx
systemctl is-failed nginx

# 列出
systemctl list-units --type=service                  # 运行中
systemctl list-units --type=service --all            # 全部
systemctl list-unit-files --state=enabled            # 开机自启的
```

### 7.2 单元文件位置

```
/usr/lib/systemd/system/        系统包提供（不要改）
/etc/systemd/system/            管理员覆盖（推荐放这）
~/.config/systemd/user/         用户级
```

```bash
# 看 unit 文件
systemctl cat nginx
systemctl show nginx                 # 全部属性

# 改完必须
systemctl daemon-reload              # ⭐ 必做
```

### 7.3 关机/重启

```bash
systemctl reboot
systemctl poweroff
systemctl suspend

shutdown -h now
shutdown -r +10                      # 10 分钟后重启
shutdown -c                          # 取消

reboot
poweroff
```

### 7.4 启动分析

```bash
systemd-analyze                      # 启动总耗时
systemd-analyze blame                # 各服务耗时 ⭐
systemd-analyze critical-chain       # 关键路径
```

## 八、日志查看

### 8.1 journalctl（systemd 日志）

```bash
journalctl                           # 全部
journalctl -f                        # 实时跟踪 ⭐
journalctl -fu nginx                 # 跟踪某服务
journalctl -u nginx                  # 看某服务历史
journalctl -u nginx -n 100           # 最近 100 行
journalctl -u nginx --since "1 hour ago"
journalctl -u nginx --since today
journalctl -u nginx -p err           # 仅 error 以上

# 内核日志
journalctl -k                        # = dmesg
dmesg -T | tail                      # 带时间

# 本次启动
journalctl -b 0
journalctl -b -1                     # 上次启动
journalctl --list-boots
```

### 8.2 传统日志位置

```
/var/log/messages       通用 (RHEL)
/var/log/syslog         通用 (Ubuntu)
/var/log/secure         认证 (RHEL)
/var/log/auth.log       认证 (Ubuntu)
/var/log/cron           cron
/var/log/maillog        邮件
/var/log/dmesg          内核启动
/var/log/yum.log        yum 操作
/var/log/dpkg.log       dpkg 操作
/var/log/nginx/         应用日志
```

```bash
tail -f /var/log/messages
grep "error" /var/log/syslog
```

## 九、网络基础

### 9.1 接口与 IP

```bash
ip a                                  # 所有接口（推荐）
ip -br a                              # 简洁
ip a show eth0
ip link show
ip link set eth0 up
ip link set eth0 down

# 老命令（不推荐，但常见）
ifconfig
ifconfig eth0
```

### 9.2 路由

```bash
ip route                              # 路由表
ip r                                  # 简写
ip route get 8.8.8.8                  # 看走哪条
route -n                              # 老命令

# 默认网关
ip route add default via 192.168.1.1
ip route del default
```

### 9.3 监听与连接

```bash
ss -tln                               # TCP 监听
ss -tunlp                             # TCP+UDP+进程
ss -anp | grep :8080                  # 端口占用
ss -s                                 # 全局统计

# 老命令
netstat -tlnp                         # 已不推荐
netstat -an
```

### 9.4 连通性

```bash
ping -c 4 example.com
ping -i 0.5 host                      # 0.5s 间隔
ping6 ::1                             # IPv6

traceroute example.com
traceroute -T -p 443 example.com     # TCP 443
mtr -n example.com                    # 持续 trace（推荐）

# DNS
host example.com
dig example.com
dig @8.8.8.8 example.com +short
nslookup example.com                  # 老
```

### 9.5 curl / wget

```bash
curl https://api.example.com/
curl -sf https://api/health           # -s 静默 -f 失败退出
curl -o file.iso https://...          # 保存
curl -L https://example.com           # 跟随重定向
curl -I https://api/                  # 仅 header
curl -X POST -d 'data' https://api/

wget https://example.com/file.iso
wget -c https://...                   # 断点续传
```

## 十、压缩与归档

```bash
# tar (最常用)
tar czf archive.tar.gz dir/           # gzip
tar cjf archive.tar.bz2 dir/          # bzip2
tar cJf archive.tar.xz dir/           # xz (最高压缩比)
tar xzf archive.tar.gz                # 解 gzip
tar xf archive.tar.??                 # 自动识别 ⭐
tar tzf archive.tar.gz                # 列出内容
tar xzf x.tar.gz -C /tmp              # 解到指定目录

# zip
zip -r archive.zip dir/
unzip archive.zip
unzip -l archive.zip                  # 列内容

# gzip
gzip file                             # 压缩 (原文件没了)
gzip -k file                          # -k 保留原文件
gunzip file.gz
zcat file.gz                          # 不解压看

# 高效（多线程）
pigz -p 8 file                        # 多线程 gzip
pbzip2 file
xz -T0 file                           # xz 多线程
```

## 十一、文件传输

### 11.1 scp / rsync

```bash
# scp（简单）
scp file user@host:/tmp/
scp -r dir/ user@host:/tmp/
scp -P 2222 file user@host:/          # -P 大写指定端口

# rsync（增量, 推荐）
rsync -avh src/ dst/                  # 本地
rsync -avhP src/ user@host:dst/       # 远程, 显进度
rsync -avh --delete src/ dst/         # 同步删除
rsync -avh -e "ssh -p 2222" src/ user@host:dst/

# 常用 flag
-a   archive (=-rlptgoD)
-v   verbose
-h   human-readable
-P   --progress + --partial
-z   压缩传输
--delete   删除 dst 多余
```

### 11.2 SSH

```bash
ssh user@host
ssh -p 2222 user@host                 # 端口
ssh -i ~/.ssh/key user@host           # 指定 key
ssh user@host 'uptime'                # 单次命令

# 配置 ~/.ssh/config
Host bastion
    HostName 1.2.3.4
    User alice
    Port 22
    IdentityFile ~/.ssh/id_ed25519

# 密钥
ssh-keygen -t ed25519                 # 推荐
ssh-copy-id user@host                 # 部署公钥

# SCP/SFTP 跳板
sftp user@host                        # 交互文件传输
```

## 十二、磁盘与挂载基础

### 12.1 看磁盘

```bash
lsblk                                  # 块设备（最常用）
lsblk -f                               # 含文件系统
df -h                                  # 各分区占用
df -i                                  # inode 占用
du -sh /var/log                       # 目录大小
du -sh /* 2>/dev/null | sort -h        # 各根目录大小
```

### 12.2 挂载

```bash
mount                                  # 看当前挂载
mount -t xfs /dev/sdb1 /data
mount -o ro /dev/sdb1 /data            # 只读挂载
umount /data
umount -l /data                        # lazy

# 永久挂载（重启生效）
# /etc/fstab
UUID=xxx-xxx /data xfs defaults,noatime 0 0

mount -a                               # 测试 fstab
findmnt --verify                       # 检查 fstab 语法
```

### 12.3 临时创建文件系统

```bash
mkfs.ext4 /dev/sdb1                    # ext4
mkfs.xfs /dev/sdb1                     # XFS

# 别格式化错了！先确认 lsblk
```

## 十三、定时任务入门

### 13.1 cron

```bash
crontab -e                             # 编辑当前用户
crontab -l                             # 列出
crontab -r                             # 删全部（小心）
crontab -u alice -e                    # 编辑 alice 的

# 格式: 分 时 日 月 周 命令
# 0 2 * * *  /backup.sh   每天 2:00
# */5 * * * * /heartbeat   每 5 分钟
# 0 9 * * 1-5  /work       工作日 9:00

# 全局 cron
/etc/crontab
/etc/cron.d/*
/etc/cron.hourly/*
/etc/cron.daily/*
/etc/cron.weekly/*
/etc/cron.monthly/*

# 日志
journalctl -t crond
/var/log/cron                          # RHEL
/var/log/syslog                        # Ubuntu (grep cron)
```

### 13.2 at（一次性）

```bash
at 23:00
> /backup.sh
> Ctrl+D
atq                                    # 列任务
atrm 1                                 # 删
```

## 十四、环境变量

```bash
# 看
env
printenv
echo $PATH
echo $HOME

# 设置
export VAR=value
export PATH=$PATH:/opt/bin

# 持久化
~/.bashrc              # 用户 (Bash 交互非登录)
~/.bash_profile        # 用户 (Bash 登录)
~/.profile             # 通用 (POSIX)
~/.zshrc               # Zsh
/etc/environment       # 全局 (键值对)
/etc/profile           # 全局 (登录时)
/etc/profile.d/*.sh    # 全局 (常用扩展)

# 测试 PATH 是否生效
which python3
hash -r                # 刷新命令缓存
```

## 十五、时间与时区

```bash
date                                   # 当前时间
date '+%Y-%m-%d %H:%M:%S'
date -d "2 days ago"
date -d "next Monday"

# 时区
timedatectl                            # 整体
timedatectl set-timezone Asia/Shanghai
timedatectl set-ntp true               # 启用 NTP

# 时间同步
chronyc sources                        # chrony
chronyc tracking
ntpq -p                                # 老的 ntp
```

## 十六、常用小工具

```bash
# 计数
wc file                                # 行数 词数 字节
wc -l file                             # 行数
wc -l < file                           # 不显示文件名

# diff
diff a.txt b.txt
diff -u a.txt b.txt                    # 统一格式
diff -r dir1 dir2                      # 递归

# 校验
md5sum file
sha256sum file
sha256sum -c hashes.txt                # 校验

# 编码
base64 file
base64 -d encoded.txt > orig
hexdump -C file
od -c file

# 计算
echo "1 + 2" | bc -l
echo "scale=4; 10/3" | bc
awk 'BEGIN {print 3.14 * 2}'
expr 5 + 3                             # 简单整数

# 字符串处理
echo "hello" | tr 'a-z' 'A-Z'
echo "  spaces  " | xargs              # 去首尾空
echo "a,b,c" | tr ',' '\n'
```

## 十七、常用快捷参考

```bash
# 系统信息
uname -a                               # 内核 + 平台
uname -r                               # 仅内核版本
cat /etc/os-release                    # 发行版
hostnamectl                            # 主机 + 内核 + OS
lsb_release -a                         # 旧
uptime                                  # 启动时间 + load
free -h                                 # 内存
nproc                                   # CPU 核数
lscpu                                   # CPU 详细
lsmem                                   # 内存 banks
lspci                                   # PCI 设备
lsusb                                   # USB

# IO
df -h                                   # 磁盘空间
df -i                                   # inode
du -sh dir/
lsblk                                   # 块设备
free -h                                 # 内存

# 网络
ip a; ip r; ss -tln; ping -c 2 host

# 进程
ps aux; top; htop; pgrep -fl pattern

# 日志
journalctl -fu service
tail -f /var/log/messages
dmesg -T

# 包
dnf install / apt install pkg
which cmd; type cmd
```

## 十八、入门必练 30 题

```
1.  把 /etc/passwd 中 UID >= 1000 的用户名列出来
    awk -F: '$3>=1000 {print $1}' /etc/passwd

2.  统计 /var/log/syslog 中各级别（INFO/WARN/ERROR）出现次数
    grep -oE 'INFO|WARN|ERROR' /var/log/syslog | sort | uniq -c

3.  找出 /var/log 下大于 100M 的文件
    find /var/log -type f -size +100M

4.  把 /tmp 下 7 天前的 .tmp 文件删掉
    find /tmp -name "*.tmp" -mtime +7 -delete

5.  把 access.log 中各 IP 请求数 top 10
    awk '{print $1}' access.log | sort | uniq -c | sort -rn | head

6.  把 nginx 配置改完后 reload
    nginx -t && systemctl reload nginx

7.  实时跟踪 nginx 错误日志
    journalctl -fu nginx -p err  或  tail -f /var/log/nginx/error.log

8.  看 8080 端口是哪个进程占用
    ss -tlnp | grep :8080  或  lsof -i :8080

9.  把 dir1 完整复制到 user@host:/tmp/
    rsync -avh dir1 user@host:/tmp/

10. 当前哪些用户在线
    who; w

11. 系统启动到现在多久
    uptime

12. 看 alice 用户的密码过期策略
    chage -l alice

13. 把 alice 加入 docker 组
    usermod -aG docker alice

14. 解压 archive.tar.xz 到 /opt
    tar xf archive.tar.xz -C /opt

15. 创建 ssh 密钥并部署到远程
    ssh-keygen -t ed25519 && ssh-copy-id user@host

16. 把 /etc 备份压缩到 /backup/etc-$(date +%F).tgz
    tar czf /backup/etc-$(date +%F).tgz /etc

17. 每天凌晨 2 点跑 /backup.sh
    crontab -e → 0 2 * * * /backup.sh

18. 看 java 进程的 CPU 排行
    ps -eo pid,cmd,%cpu --sort=-%cpu | grep java | head

19. 限制某用户最大打开文件数 65535
    /etc/security/limits.conf → alice soft/hard nofile 65535

20. 查看 sda 磁盘 SMART 健康
    smartctl -H /dev/sda

21. 计算 file.iso 的 sha256
    sha256sum file.iso

22. 看哪些服务开机自启
    systemctl list-unit-files --state=enabled

23. 把 /etc/fstab 中 swap 行注释掉
    sed -i '/swap/s/^/#/' /etc/fstab

24. 看 nginx 监听端口
    ss -tlnp | grep nginx

25. 把日志中包含 "error" 的行写到 errors.log
    grep -i "error" app.log > errors.log

26. 找出 /home/alice 下最大的 5 个文件
    find /home/alice -type f -exec du -h {} + | sort -rh | head -5

27. 看 cron 是否正常运行
    systemctl status crond  或  systemctl status cron

28. 临时修改主机名
    hostnamectl set-hostname web01

29. 跑命令并测时间
    time ./long-task.sh

30. 同时跟踪 nginx access + error 日志
    tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

## 十九、典型坑

| 坑 | 建议 |
|:---|:---|
| **rm -rf 误删** | 别用 root 日常 / `alias rm='rm -i'` |
| **chmod 777** | 永远不要 |
| **直接 vim /etc/sudoers** | 必须 visudo |
| **usermod 没加 -a** | usermod -aG（追加）|
| **改 sshd 没 reload** | 别远程做这事 / 留个 root session |
| **直接编辑 /etc/fstab 重启起不来** | mount -a 测试 / 救援模式 |
| **解析 ls 输出** | 用 glob / find -print0 |
| **变量没引号** | "$var" 防空格 |
| **history 含敏感** | 命令前加空格 (HISTCONTROL=ignorespace) |
| **写完脚本不加 x** | chmod +x script.sh |
| **不看 man** | man cmd 是最权威文档 |

## 二十、学习资源

```
书籍:
  - 《鸟哥的 Linux 私房菜》⭐ 入门首选
  - 《Linux 命令行与 Shell 脚本编程大全》
  - 《Linux 就该这么学》

在线:
  - linuxcommand.org
  - explainshell.com (解释任意命令)
  - tldr.sh (简化 man)
  - Linux Journey

练习:
  - OverTheWire: bandit  (CTF 入门)
  - Linux Survival
  - cmdchallenge.com

国内:
  - 阿铭 Linux
  - 鸟哥私房菜中文版
  - 极客时间 Linux 性能优化实战
```

> 📖 **核心判断**：Linux 入门 = **50 个核心命令 + 基础流程**。`ls/cat/grep/sed/awk/find/ps/top/df/du/ssh/rsync/systemctl/journalctl/crontab` 这十几个是肌肉记忆。**别死记参数, 多 man 多 explainshell**。一个月练熟本章的 30 道题, 就具备了进阶资格。

