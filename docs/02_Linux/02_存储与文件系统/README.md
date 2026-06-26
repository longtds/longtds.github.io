# 存储与文件系统

> Linux 存储栈 = **块设备（磁盘/SSD/NVMe）→ RAID/MultiPath → LVM（卷管理）→ 文件系统（ext4/xfs/btrfs/zfs）→ 挂载（mount）→ 网络存储（NFS/CIFS/iSCSI）**。每一层都有运维细节，本章给完整手册。

## 一、磁盘基础

### 1.1 设备识别

```bash
# 看磁盘
lsblk                                          # 块设备树（最常用）
lsblk -f                                        # 含文件系统
lsblk -d -o NAME,SIZE,ROTA,MODEL                # 是否旋转盘 (SSD=0)
lsblk -e7                                       # 排除 loop

fdisk -l                                        # 全部磁盘 + 分区
parted -l                                        # GPT 友好

# 详细信息
hdparm -i /dev/sda                              # SATA/IDE
smartctl -a /dev/sda                            # SMART (健康)
smartctl -a /dev/nvme0                          # NVMe
nvme list                                        # NVMe 设备
nvme smart-log /dev/nvme0n1

# 总线
lspci | grep -i raid
lspci | grep -i nvme
lsscsi                                          # SCSI 设备

# 设备名约定
/dev/sda     SATA / SAS 第 1 块
/dev/nvme0n1 NVMe 第 1 块第 1 namespace
/dev/vda     virtio (KVM 虚拟盘)
/dev/xvda    Xen 虚拟盘
/dev/mapper/* LVM / dm-crypt / multipath
/dev/md0     mdadm RAID
```

### 1.2 SMART 健康检查

```bash
# 安装
dnf install smartmontools                       # RHEL
apt install smartmontools                       # Ubuntu

# 状态
smartctl -H /dev/sda                            # 健康 (PASSED/FAILED)
smartctl -a /dev/sda                            # 完整属性

# 关键 SMART 属性
# 5    Reallocated_Sector_Ct      重映射扇区 (> 0 警惕)
# 187  Reported_Uncorrect          报告未校正错误
# 188  Command_Timeout             命令超时
# 196  Reallocation_Event_Count
# 197  Current_Pending_Sector      待重映射扇区 ⭐
# 198  Offline_Uncorrectable
# 199  UDMA_CRC_Error_Count        线缆/接触问题

# 主动扫描
smartctl -t short /dev/sda                      # 短测试 (2 min)
smartctl -t long /dev/sda                       # 完整扫描 (几小时)
smartctl -l selftest /dev/sda                   # 看结果

# 后台服务
systemctl enable --now smartd
# 配置 /etc/smartd.conf
DEVICESCAN -a -o on -S on -n standby,q -s (S/../.././02|L/../../6/03) -m admin@example.com
```

### 1.3 NVMe 专用

```bash
nvme list
nvme id-ctrl /dev/nvme0
nvme smart-log /dev/nvme0n1                     # 健康/耐久度
# 关注:
# - percentage_used         消耗百分比
# - power_on_hours
# - critical_warning        != 0 时告警
# - media_errors

# 性能测试
nvme io-passthru ...                            # 高级
fio --name=test --filename=/dev/nvme0n1 --rw=randread --bs=4k --numjobs=4 --iodepth=64 --time_based --runtime=30 --direct=1
```

## 二、分区表

### 2.1 MBR vs GPT

| 特性 | MBR | GPT ⭐ |
|:---|:---|:---|
| 最大盘容量 | 2TB | 9.4 ZB |
| 分区数 | 4 主 / 扩展 | 128 |
| 备份 | 无 | 头尾各一份 |
| UEFI 启动 | 需 BIOS | 原生 |
| 校验 | 无 | CRC32 |
| 推荐 | 历史遗留 | 一律 GPT |

### 2.2 parted（GPT 推荐）

```bash
parted /dev/sda
(parted) print
(parted) mklabel gpt                            # 注意：擦写整盘
(parted) mkpart primary ext4 0% 100%            # 用百分比避免对齐问题
(parted) mkpart primary 1MiB 100GiB             # 显式对齐
(parted) name 1 root
(parted) set 1 boot on                          # 启动标志
(parted) align-check optimal 1                  # 检查对齐 ⭐
(parted) quit

# 非交互
parted -s /dev/sdb mklabel gpt mkpart data ext4 0% 100%
```

### 2.3 fdisk

```bash
fdisk /dev/sda
# m  help
# p  print
# n  new
# d  delete
# t  change type (8e LVM / 83 Linux / 8300 GPT Linux)
# w  write
# q  quit

# 自动化
echo -e "n\np\n\n\n\nw" | fdisk /dev/sdb
```

### 2.4 分区对齐（SSD/NVMe 重要）

```bash
# 4K 对齐：从扇区 2048 起（1MiB 边界）
fdisk -l /dev/sda
# 看 Start 是否 2048 的倍数 → 是 = 对齐

# parted 用百分比或 MiB 自动对齐
# fdisk 默认对齐到 2048
```

### 2.5 扩容分区（在线）

```bash
# 1. 扩容底层（云盘 / 物理盘）
# 2. 通知内核
echo 1 > /sys/class/block/sda/device/rescan
partprobe /dev/sda                              # 重读分区表

# 3. 扩容分区
growpart /dev/sda 1                             # cloud-utils-growpart

# 4. 扩容文件系统
resize2fs /dev/sda1                             # ext4
xfs_growfs /                                     # XFS (按挂载点)
btrfs filesystem resize max /                    # btrfs
```

## 三、文件系统

### 3.1 选型矩阵

| 文件系统 | 主导 | 最大文件/卷 | 特性 | 适合 |
|:---|:---|:---:|:---|:---|
| **ext4** ⭐⭐⭐⭐⭐ | Linux | 16TB / 1EB | 稳定通用 | 通用首选 |
| **XFS** ⭐⭐⭐⭐⭐ | SGI/RH | 8EB | 大文件 / 高吞吐 | RHEL 默认 |
| **Btrfs** ⭐⭐⭐⭐ | Oracle | 16EB | CoW / 快照 / 压缩 | 桌面 / SUSE |
| **ZFS** ⭐⭐⭐⭐ | Sun | 16EB | CoW / RAID-Z / dedup | 存储服务器 |
| **F2FS** | Samsung | 16TB | Flash 友好 | 移动 / SSD |
| **Ceph FS** | RH | 分布式 | 集群 | 大规模 |
| **GlusterFS** | RH | 分布式 | 集群 | 文件共享 |

### 3.2 ext4 实战

```bash
# 创建
mkfs.ext4 /dev/sdb1
mkfs.ext4 -L data -m 1 -b 4096 /dev/sdb1         # -m 保留 root 1% / -b 块大小

# 调优
tune2fs -l /dev/sdb1                              # 看参数
tune2fs -m 0 /dev/sdb1                            # 0% 保留（数据盘可省 5%）
tune2fs -c 0 -i 0 /dev/sdb1                       # 关闭周期性 fsck
tune2fs -L newlabel /dev/sdb1
tune2fs -U random /dev/sdb1                       # 重置 UUID

# 看信息
dumpe2fs -h /dev/sdb1
blkid /dev/sdb1                                   # UUID/LABEL

# 修复
e2fsck -f /dev/sdb1                               # 必须未挂载
e2fsck -y /dev/sdb1                               # 自动 yes
e2fsck -p /dev/sdb1                               # parallel 修复
e2fsck -B 4096 -b 32768 /dev/sdb1                 # 备份 superblock

# 扩缩容（在线）
resize2fs /dev/sdb1                               # 自动到底
resize2fs /dev/sdb1 50G                           # 缩到 50G (需先卸载并 fsck)
```

### 3.3 XFS（高性能）

```bash
# 创建
mkfs.xfs -f /dev/sdb1
mkfs.xfs -L data -f /dev/sdb1
mkfs.xfs -d agcount=8 -l size=64m /dev/sdb1       # 高级

# 信息
xfs_info /mountpoint
xfs_db -r -c "sb 0" -c "p" /dev/sdb1

# 扩容（仅扩，不能缩）
xfs_growfs /mountpoint                            # 自动到底

# 修复（卸载后）
xfs_repair /dev/sdb1
xfs_repair -L /dev/sdb1                           # 强制清 log（数据丢失风险）

# 配额（XFS 项目配额）
mount -o uquota,gquota,pquota /dev/sdb1 /data
xfs_quota -x -c 'limit bsoft=10g bhard=11g alice' /data

# 优势：
# - 高并发写入
# - 大文件友好
# - 在线碎片整理
# - RHEL 7+ 默认
# 缺点：不能缩容
```

### 3.4 Btrfs（CoW + 快照）

```bash
# 创建
mkfs.btrfs -L data /dev/sdb1
mkfs.btrfs -d raid1 -m raid1 /dev/sdb /dev/sdc    # RAID-1 mirror

# 子卷
btrfs subvolume create /mnt/data/sub1
btrfs subvolume list /mnt/data
btrfs subvolume delete /mnt/data/sub1

# 快照
btrfs subvolume snapshot /mnt/data /mnt/data/.snap-$(date +%F-%H%M)
btrfs subvolume snapshot -r /mnt/data /mnt/data/.snap-ro       # 只读

# 压缩 (zstd 推荐)
mount -o compress=zstd:3 /dev/sdb1 /mnt/data
# /etc/fstab: defaults,compress=zstd:3 0 0

# 配额
btrfs quota enable /mnt/data
btrfs qgroup limit 10G /mnt/data/sub1

# 扩缩容
btrfs filesystem resize +10G /mnt/data
btrfs filesystem resize -5G /mnt/data
btrfs filesystem resize max /mnt/data

# 平衡
btrfs balance start /mnt/data
btrfs balance status /mnt/data

# 健康
btrfs filesystem usage /mnt/data
btrfs scrub start /mnt/data                       # 周期扫描
btrfs scrub status /mnt/data

# 优势：CoW + 快照 + 透明压缩 + RAID
# 缺点：RAID-5/6 稳定性历史问题
```

### 3.5 ZFS（企业级）

```bash
# 安装（Ubuntu 默认支持）
apt install zfsutils-linux                        # Ubuntu
dnf install zfs-fuse                              # RHEL (DKMS)

# 创建 pool
zpool create -o ashift=12 -O compression=lz4 \
  -O atime=off tank mirror /dev/sdb /dev/sdc      # mirror = RAID-1
zpool create tank raidz2 /dev/sd{b,c,d,e}         # RAID-Z2

# Dataset
zfs create tank/data
zfs create tank/data/logs
zfs set compression=zstd tank/data
zfs set quota=100G tank/data/logs
zfs set recordsize=1M tank/bigfiles               # 大文件

# 快照
zfs snapshot tank/data@daily-$(date +%F)
zfs list -t snapshot
zfs rollback tank/data@daily-2026-06-26
zfs clone tank/data@daily tank/data-test

# 发送/接收（远程备份）
zfs send tank/data@daily | ssh backup-srv "zfs receive backup-pool/data"
zfs send -i @yesterday tank/data@today | ssh ... | zfs receive -F ...

# 健康
zpool status -v tank
zpool scrub tank
zpool list

# ARC 缓存监控
arc_summary
zpool iostat -v tank 1

# 优势:
# - 端到端校验
# - RAID-Z (省一块校验盘)
# - 内置压缩/dedup/加密
# - 发送/接收增量备份
# 缺点：内存消耗大（ARC 占 50% RAM）
```

## 四、LVM（逻辑卷管理）

### 4.1 概念

```
PV (Physical Volume)    物理卷    = 一块磁盘/分区
VG (Volume Group)       卷组      = 多个 PV 池化
LV (Logical Volume)     逻辑卷    = 从 VG 切出的"虚拟分区"

优势:
  - 动态扩缩容
  - 快照
  - 跨磁盘聚合
  - 镜像 / RAID
  - thin provisioning
```

### 4.2 标准流程

```bash
# 1. PV
pvcreate /dev/sdb /dev/sdc
pvs                                                # 简洁
pvdisplay                                          # 详细
pvscan

# 2. VG
vgcreate vg_data /dev/sdb /dev/sdc
vgs
vgdisplay
vgextend vg_data /dev/sdd                          # 加盘
vgreduce vg_data /dev/sdd                          # 移除（需先 pvmove）

# 3. LV
lvcreate -L 100G -n lv_logs vg_data
lvcreate -l 100%FREE -n lv_data vg_data           # 用全部空间
lvcreate -L 50G -n lv_mirror -m1 vg_data          # 镜像 (RAID-1)
lvcreate -L 100G -n lv_stripe -i 2 vg_data        # 条带 (RAID-0, 2 盘)

# 4. 格式化 + 挂载
mkfs.xfs /dev/vg_data/lv_logs
mkdir /var/log/app
mount /dev/vg_data/lv_logs /var/log/app

# 5. /etc/fstab
echo "/dev/vg_data/lv_logs /var/log/app xfs defaults 0 0" >> /etc/fstab
```

### 4.3 扩缩容

```bash
# 扩容（在线，ext4/xfs/btrfs）
lvextend -L +50G /dev/vg_data/lv_logs
lvextend -l +100%FREE /dev/vg_data/lv_logs        # 用剩余

# 同时扩文件系统
lvextend -r -L +50G /dev/vg_data/lv_logs          # -r 自动 resize fs
# 或分两步:
lvextend -L +50G /dev/vg_data/lv_logs
xfs_growfs /var/log/app                            # XFS
resize2fs /dev/vg_data/lv_logs                     # ext4

# 缩容（XFS 不支持！只能 ext4）
umount /var/log/app
e2fsck -f /dev/vg_data/lv_logs
resize2fs /dev/vg_data/lv_logs 80G                 # 先缩 fs
lvreduce -L 80G /dev/vg_data/lv_logs               # 再缩 LV
mount /var/log/app
```

### 4.4 快照

```bash
# 创建（CoW，原 LV 改动会写到 snapshot 空间）
lvcreate -L 10G -s -n snap1 /dev/vg_data/lv_data
# -L 10G = 预留 10G 给 CoW 数据（满了快照失效）

# 挂载快照
mkdir /mnt/snap
mount /dev/vg_data/snap1 /mnt/snap

# 备份后删除
rsync -av /mnt/snap/ /backup/
umount /mnt/snap
lvremove /dev/vg_data/snap1

# 回滚到快照
lvconvert --merge /dev/vg_data/snap1               # 下次重启自动 merge
```

### 4.5 Thin Provisioning（超分）

```bash
# 创建 thin pool
lvcreate -L 1T -T vg_data/tpool

# 创建 thin LV (虚拟容量可大于 pool)
lvcreate -V 500G -T vg_data/tpool -n lv_thin1
lvcreate -V 500G -T vg_data/tpool -n lv_thin2
lvcreate -V 500G -T vg_data/tpool -n lv_thin3
# 总虚拟 1.5T，但实际占用 < 1T
# 注意: pool 满了所有 thin LV 都崩

# 监控
lvs -o name,size,data_percent,metadata_percent
```

### 4.6 在线迁移（更换磁盘）

```bash
# 把数据从 /dev/sdb 挪到 /dev/sdd
pvcreate /dev/sdd
vgextend vg_data /dev/sdd
pvmove /dev/sdb /dev/sdd                           # 在线迁移
vgreduce vg_data /dev/sdb
pvremove /dev/sdb
# 然后可以拔掉 sdb
```

## 五、RAID（软 RAID / mdadm）

### 5.1 RAID 级别

| 级别 | 盘数 | 容量 | 性能 | 容错 | 用途 |
|:---|:---:|:---:|:---:|:---|:---|
| **RAID-0** | ≥2 | 100% | 读+写 ↑↑ | 无 | 临时数据 |
| **RAID-1** | 2 | 50% | 读 ↑ 写 = | 1 盘 | 系统盘 |
| **RAID-5** | ≥3 | N-1 | 读 ↑ 写 ↓ | 1 盘 | 通用 |
| **RAID-6** | ≥4 | N-2 | 读 ↑ 写 ↓↓ | 2 盘 | 大容量 |
| **RAID-10** | ≥4 (偶) | 50% | 读+写 ↑↑ | 多盘 | 数据库 ⭐ |

### 5.2 mdadm 实战

```bash
# 创建 RAID-10
mdadm --create /dev/md0 --level=10 --raid-devices=4 /dev/sd[b-e]
# 或
mdadm -C /dev/md0 -l 10 -n 4 /dev/sd{b,c,d,e}

# 看状态
cat /proc/mdstat
mdadm --detail /dev/md0
mdadm --examine /dev/sdb

# 保存配置（不然重启认不出）
mdadm --detail --scan >> /etc/mdadm.conf          # RHEL
mdadm --detail --scan >> /etc/mdadm/mdadm.conf    # Ubuntu
update-initramfs -u

# 故障盘处理
mdadm /dev/md0 --fail /dev/sdb                    # 标记故障
mdadm /dev/md0 --remove /dev/sdb                  # 移除
# 物理换盘
mdadm /dev/md0 --add /dev/sdb                     # 加入（自动 rebuild）

# 重建监控
watch cat /proc/mdstat
mdadm --monitor --mail=admin@example.com --daemonise /dev/md0

# 增加盘数（RAID-5/6 reshape）
mdadm --add /dev/md0 /dev/sdf
mdadm --grow /dev/md0 --raid-devices=5

# 停止
mdadm --stop /dev/md0
mdadm --zero-superblock /dev/sd[b-e]              # 清元数据
```

### 5.3 硬 RAID vs 软 RAID

```
硬 RAID:
  ✅ 性能强（独立缓存 + 电池）
  ✅ 可启动盘
  ❌ 卡坏需要同型号 / 兼容
  ❌ 故障定位难
  代表: LSI MegaRAID / PERC / HP Smart Array

软 RAID (mdadm):
  ✅ 通用 / 可移植
  ✅ 故障明显
  ❌ 性能略低
  ❌ 启动盘配置复杂

ZFS / Btrfs:
  ✅ 文件系统层 RAID
  ✅ 数据校验
  ❌ ZFS 用内存多

推荐:
  - 数据库 / 关键: 硬 RAID-10 + 电池
  - 大文件存储: ZFS RAID-Z2
  - K8s 节点系统盘: 软 RAID-1
```

## 六、挂载与 fstab

### 6.1 mount 命令

```bash
# 临时挂载
mount /dev/sdb1 /data
mount -t xfs -o noatime,nodiratime /dev/sdb1 /data
mount -o remount,rw /                              # 重新挂载（root rw）
mount -o remount,ro /home                          # 改为只读

# bind 挂载（同一目录挂到另一处）
mount --bind /src /dst

# tmpfs（内存盘）
mount -t tmpfs -o size=2G tmpfs /tmp

# 卸载
umount /data
umount -l /data                                    # lazy（占用时延迟卸载）
umount -f /data                                    # force（NFS 卡死时）
fuser -m /data                                     # 谁在用
lsof +D /data
```

### 6.2 /etc/fstab

```
# device  mountpoint  fstype  options  dump  fsck
UUID=xxx-xxx-xxx  /          ext4  defaults                          1 1
UUID=yyy-yyy-yyy  /boot      ext4  defaults                          1 2
UUID=zzz-zzz-zzz  /data      xfs   defaults,noatime,nodiratime       0 0
LABEL=swap        swap       swap  defaults                          0 0

/dev/vg/lv        /var/log   ext4  defaults                          0 0
tmpfs             /tmp       tmpfs defaults,size=4G,mode=1777        0 0

# NFS
nfs-srv:/export   /mnt/nfs   nfs   defaults,_netdev,vers=4.1         0 0

# 网络挂载关键：_netdev (等网络就绪)

# 检查 fstab
mount -a                                          # 挂载 fstab 全部
findmnt --verify --verbose                        # 检查语法
systemctl daemon-reload                           # systemd 重新生成 .mount unit
```

### 6.3 常用挂载选项

```
defaults        = rw,suid,dev,exec,auto,nouser,async
noatime         不更新访问时间 ⭐ 性能 +
nodiratime
relatime        仅每天更新一次访问时间（更宽容）
nodev           不解析设备文件（安全）
nosuid          忽略 suid 位
noexec          不允许执行
ro              只读

# 大数据 / DB / 容器:
noatime,nodiratime         性能 +
discard                    SSD TRIM（或定期 fstrim）
data=writeback             ext4 性能（牺牲一致性）

# NFS:
vers=4.1
hard / soft                死等 / 超时
intr                       可中断
rsize=1048576,wsize=1048576
```

### 6.4 自动挂载（systemd.automount）

```ini
# /etc/systemd/system/mnt-data.mount
[Unit]
Description=Mount /mnt/data

[Mount]
What=//server/share
Where=/mnt/data
Type=cifs
Options=credentials=/etc/samba/creds,vers=3.0

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/mnt-data.automount
[Unit]
Description=Automount /mnt/data

[Automount]
Where=/mnt/data
TimeoutIdleSec=600                                # 10 分钟不用就卸载

[Install]
WantedBy=multi-user.target
```

## 七、网络存储

### 7.1 NFS

```bash
# 服务端 (RHEL)
dnf install nfs-utils
systemctl enable --now nfs-server

# /etc/exports
/data         192.168.1.0/24(rw,sync,no_root_squash,no_subtree_check)
/backup       10.0.0.0/8(rw,async,no_root_squash)

# 应用
exportfs -ra                                       # 重载
exportfs -v                                        # 当前 export

# 客户端
dnf install nfs-utils
showmount -e nfs-srv                              # 查询
mount -t nfs -o vers=4.1 nfs-srv:/data /mnt/data

# /etc/fstab:
nfs-srv:/data /mnt/data nfs defaults,_netdev,vers=4.1,hard,intr 0 0

# 性能选项
vers=4.1                  # NFSv4 多
rsize=1048576,wsize=1048576  # 大块
async                     # 服务端
nconnect=4                # 多连接 (kernel 5.3+)

# 排查
nfsstat -c                # 客户端统计
nfsstat -s                # 服务端
rpcinfo -p nfs-srv
```

### 7.2 CIFS / SMB

```bash
# 客户端
dnf install cifs-utils
# 凭据
cat > /etc/samba/creds <<EOF
username=alice
password=xxx
domain=CORP
EOF
chmod 600 /etc/samba/creds

# 挂载
mount -t cifs //smb-srv/share /mnt/smb \
  -o credentials=/etc/samba/creds,vers=3.0,iocharset=utf8,uid=alice,gid=alice
```

### 7.3 iSCSI

```bash
# Initiator (客户端)
dnf install iscsi-initiator-utils

# 发现 target
iscsiadm -m discovery -t st -p 192.168.1.100

# 登录
iscsiadm -m node -T iqn.2024-01.com.example:target -l

# 看新设备
lsblk
# 出现 /dev/sda 之类

# 持久化
iscsiadm -m node -T iqn... -o update -n node.startup -v automatic

# 卸载
iscsiadm -m node -T iqn... -u
iscsiadm -m node -T iqn... -o delete
```

### 7.4 Ceph RBD / CephFS

```bash
# 块设备 RBD
rbd map mypool/myimage --id admin
mkfs.xfs /dev/rbd0
mount /dev/rbd0 /mnt/ceph

# CephFS
mount -t ceph mon1:6789:/ /mnt/cephfs -o name=admin,secretfile=/etc/ceph/admin.key

# K8s CSI 使用更标准
```

### 7.5 对象存储 FUSE（s3fs/goofys/rclone）

```bash
# s3fs（兼容 S3 协议）
s3fs my-bucket /mnt/s3 -o passwd_file=/etc/s3.pwd

# rclone mount
rclone mount s3:bucket /mnt/s3 --vfs-cache-mode writes --daemon

# 注意：FUSE 性能远不如本地，仅日志/备份场景
```

## 八、磁盘加密（LUKS）

### 8.1 全盘加密

```bash
# 创建
cryptsetup luksFormat /dev/sdb
# 输入密码

cryptsetup luksOpen /dev/sdb encrypted_data
# 出现 /dev/mapper/encrypted_data

mkfs.xfs /dev/mapper/encrypted_data
mount /dev/mapper/encrypted_data /data

# 关闭
umount /data
cryptsetup luksClose encrypted_data

# 备份 header（关键！）
cryptsetup luksHeaderBackup /dev/sdb --header-backup-file luks-header.bin
```

### 8.2 /etc/crypttab

```
# name          device          keyfile         options
encrypted_data  /dev/sdb        /etc/cryptkey   luks,timeout=30

# 然后 /etc/fstab:
/dev/mapper/encrypted_data /data xfs defaults 0 0
```

### 8.3 TPM 解锁（无密码）

```bash
# systemd-cryptenroll 集成 TPM 2.0
systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7+11 /dev/sdb
# 自动从 TPM 解锁，无需输密码
```

## 九、I/O 性能

### 9.1 监控

```bash
# 实时
iostat -xz 1                                       # 看 %util, await, svctm
iotop -o                                            # 谁在 I/O
nvme-stas / nvme list-subsys

# 历史
sar -d 1 10
sar -d -f /var/log/sa/sa12

# 关键指标
%util    设备繁忙时间 % (接近 100 满)
await    平均 I/O 等待 ms (高 = 慢)
svctm    平均服务时间 ms (硬件)
r/s w/s  读写 IOPS
rkB/s wkB/s 吞吐
aqu-sz   平均队列长度
```

### 9.2 fio 压测

```bash
# 顺序读
fio --name=seqread --filename=/dev/nvme0n1 --rw=read --bs=1M --numjobs=1 \
    --iodepth=32 --time_based --runtime=30 --direct=1 --group_reporting

# 随机读
fio --name=randread --filename=/data/test.dat --rw=randread --bs=4k \
    --numjobs=4 --iodepth=64 --size=10G --time_based --runtime=30 --direct=1

# 数据库典型（70% 读 30% 写）
fio --name=db --filename=/data/test.dat --rw=randrw --rwmixread=70 \
    --bs=8k --numjobs=4 --iodepth=32 --size=20G --time_based --runtime=120 --direct=1

# 完整 4 项基线
for rw in read write randread randwrite; do
  fio --name=$rw --filename=/dev/sdX --rw=$rw --bs=4k --numjobs=4 \
      --iodepth=64 --time_based --runtime=30 --direct=1 --group_reporting
done

# 注意:
# - --direct=1 绕过 page cache
# - --filename 不要打到生产数据
# - SSD 上 fio 一段时间后会进入稳态
```

### 9.3 I/O 调度器

```bash
# 看当前
cat /sys/block/sda/queue/scheduler
# [mq-deadline] kyber bfq none

# 临时切换
echo none > /sys/block/nvme0n1/queue/scheduler        # NVMe 推荐
echo mq-deadline > /sys/block/sda/queue/scheduler     # SSD/SATA

# 持久化（GRUB）
GRUB_CMDLINE_LINUX="elevator=mq-deadline"
# 或 udev:
cat > /etc/udev/rules.d/60-scheduler.rules <<EOF
ACTION=="add|change", KERNEL=="nvme*", ATTR{queue/scheduler}="none"
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="mq-deadline"
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="bfq"
EOF

# 选型:
# NVMe SSD: none / mq-deadline
# SATA SSD: mq-deadline
# HDD: bfq / mq-deadline
```

### 9.4 readahead / queue depth

```bash
# Readahead (KB)
blockdev --getra /dev/sda                          # 默认 256 (128KB)
blockdev --setra 4096 /dev/sda                     # 2MB (顺序大文件场景)

# Queue depth
cat /sys/block/sda/queue/nr_requests               # 默认 128
echo 256 > /sys/block/sda/queue/nr_requests        # 高并发

# 持久化：udev
```

## 十、磁盘配额

### 10.1 ext4 配额

```bash
# /etc/fstab 加 usrquota,grpquota
/dev/sdb1 /data ext4 defaults,usrquota,grpquota 0 0
mount -o remount /data

# 初始化
quotacheck -cum /data
quotaon -uv /data

# 设置
edquota -u alice                                   # 交互
setquota -u alice 1G 1.2G 0 0 /data                # soft hard

# 看
quota -u alice
repquota -a
```

### 10.2 XFS 项目配额

```bash
mount -o uquota,gquota,pquota /dev/sdb1 /data

# 用户/组
xfs_quota -x -c 'limit bsoft=1g bhard=2g alice' /data
xfs_quota -x -c 'report -u' /data

# 项目（按目录配额）⭐
echo "10:/data/project_a" >> /etc/projects
echo "project_a:10" >> /etc/projid
xfs_quota -x -c 'project -s project_a' /data
xfs_quota -x -c 'limit -p bsoft=10g bhard=12g project_a' /data
```

## 十一、备份与恢复

### 11.1 工具选型

```
rsync               增量同步，最常用 ⭐
tar                  归档
borg / restic ⭐     去重 + 加密 + 增量
rsnapshot           基于 rsync 的版本化备份
duplicity / duplicati  加密远程备份
zfs send/receive    ZFS 原生
btrfs send/receive  Btrfs 原生
LVM snapshot + rsync   常见组合
```

### 11.2 rsync 实战

```bash
# 本地
rsync -avh --delete /src/ /dst/

# 远程
rsync -avhP --delete -e "ssh -p 22" /src/ user@host:/dst/

# 增量 + 排除
rsync -avh --delete \
  --exclude=*.tmp --exclude=cache/ \
  /src/ /dst/

# 重要选项
-a    archive (=-rlptgoD)
-v    verbose
-h    human-readable
-P    --progress + --partial
--delete    删除 dst 多余的
--link-dest=/old/backup   硬链接到旧备份（节省空间，rsnapshot 用）
--bwlimit=10M             限速
-z    压缩传输（局域网不需要）

# 监控数据传输状态：cron + rsync + logrotate
```

### 11.3 restic（推荐）

```bash
# 初始化（S3 后端）
export RESTIC_REPOSITORY=s3:s3.amazonaws.com/bucket/backup
export RESTIC_PASSWORD=xxx
restic init

# 备份
restic backup /data /etc --exclude=/data/cache --tag prod

# 列快照
restic snapshots
restic stats

# 恢复
restic restore latest --target /restore --include /data

# 保留策略
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune

# 自动化（systemd timer + restic backup）
```

### 11.4 systemd timer 自动备份

```ini
# /etc/systemd/system/backup.service
[Service]
Type=oneshot
Environment=RESTIC_REPOSITORY=s3:s3.amazonaws.com/bucket
EnvironmentFile=/etc/restic.env
ExecStart=/usr/bin/restic backup /data --tag daily
ExecStart=/usr/bin/restic forget --keep-daily 7 --keep-weekly 4 --prune

# /etc/systemd/system/backup.timer
[Timer]
OnCalendar=*-*-* 02:00
RandomizedDelaySec=30min
Persistent=true

[Install]
WantedBy=timers.target
```

## 十二、典型坑

| 坑 | 建议 |
|:---|:---|
| **/etc/fstab 写错主机起不来** | 用 `mount -a` 测，UUID 别用设备名 |
| **NFS 死锁卡 ls** | hard,intr 或 soft + 重启 |
| **XFS 没法缩** | 设计时算清楚 / 用 ext4 |
| **LVM thin pool 满了崩** | 监控 data_percent + 报警 |
| **mdadm 没保存 config** | mdadm.conf + initramfs |
| **iostat %util 看错** | 现代多队列 SSD %util 接近 100 也正常 |
| **不开 noatime** | 频繁元数据写入影响性能 |
| **SSD 不开 TRIM** | fstrim weekly timer |
| **没监控 SMART** | smartd + 告警 |
| **大盘对齐错** | parted 用百分比 / GPT |
| **加密盘忘备份 header** | luksHeaderBackup |
| **跨主机挂同一磁盘** | 仅 OCFS2 / GFS2 集群 fs |
| **rsync --delete 误删** | 先 --dry-run |
| **删 LV 没卸载** | mount 状态删了一定崩 |
| **Ceph RBD 没多路径** | 单 mon 挂掉无法挂 |

## 十三、推荐栈（2025）

```
通用服务器:
  分区:     GPT
  逻辑卷:   LVM 或 物理直挂
  文件系统: XFS (RHEL) / ext4 (Ubuntu)
  挂载:     noatime,nodiratime
  备份:     restic + S3 / 兼容存储

数据库:
  RAID-10 硬件 RAID
  XFS (大表友好) / ext4
  LVM 留 20% 空间快照备份
  数据/日志/binlog 分盘

K8s 节点:
  系统盘 RAID-1 软 RAID
  数据盘 ext4 + LVM (动态扩)
  CSI: Ceph RBD / OpenEBS / Longhorn

存储节点:
  ZFS RAID-Z2 / Z3
  + ARC (大内存)
  + L2ARC (NVMe 二级缓存)
  + ZIL/SLOG (NVMe 写日志)
  或 Ceph 分布式
```

## 十四、国产化清单

```
存储产品:
  - 华为 OceanStor (集中式 + 分布式)
  - 浪潮 AS/HF 系列
  - 中科曙光 ParaStor
  - 紫光西部数据
  - DDN 国产代理

分布式存储:
  - 阿里云盘古
  - 腾讯 CFS / CBS
  - 华为 FusionStorage / DSS
  - 浪潮 AS13000

国产文件系统:
  - 龙蜥 OS 内核支持 ext4/XFS/Btrfs
  - openEuler 同上
  - 麒麟 V10 同上
```

## 十五、学习路径

```
入门（2 周）:
  1. 磁盘 + 分区基础 (fdisk/parted/lsblk)
  2. ext4 + XFS 创建/挂载/扩容
  3. fstab 配置
  4. SMART 监控

中级（1 月）:
  5. LVM 全套
  6. mdadm 软 RAID
  7. NFS / CIFS 客户端
  8. fio 性能压测
  9. rsync 备份

高级（3 月+）:
  10. ZFS / Btrfs CoW + 快照
  11. iSCSI / Ceph RBD
  12. LUKS 加密
  13. I/O 调度器调优
  14. restic 增量备份

专家:
  15. 自研分布式存储
  16. Ceph 集群运维
  17. 存储 SAN/NAS 架构
```

## 十六、参考资料

```
官方:
  - Linux Filesystems
  - LVM HOWTO
  - mdadm Wiki
  - ZFS on Linux
  - Btrfs Wiki
  - XFS Documentation
  - Ceph Documentation

书籍:
  - 《鸟哥的 Linux 私房菜 - 服务器篇》
  - 《Linux 存储管理实战》
  - Storage 性能基础 (Brendan Gregg)
```

> 📖 **核心判断**：Linux 存储 = **GPT + LVM + XFS（或 ext4）+ noatime + restic 备份**——这套组合扛 80% 生产场景。**XFS 不能缩**这一条记牢，规划时多留 20% 空间。**SMART + smartd** 是免费的硬盘故障预防——很多生产事故是早就预警没人看。**fio --direct=1** 是真实性能基准，看 %util 已经过时（多队列设备误导大）。

