# 存储与文件系统

## 文件系统对比

| 文件系统 | 最大文件 | 最大卷 | 特性 | 场景 |
|:---|:---:|:---:|:---|:---|
| ext4 | 16TB | 1EB | 成熟稳定 | 通用默认 |
| XFS | 8EB | 8EB | 高性能，适合大文件 | 大文件存储 |
| ZFS | 16EB | 256ZB | 数据完整性/压缩/快照 | 存储服务器 |
| Btrfs | 16EB | 16EB | Cow/快照/校验 | 高级存储 |

## LVM 逻辑卷管理

```bash
# 创建 PV
pvcreate /dev/sdb /dev/sdc

# 创建 VG
vgcreate data_vg /dev/sdb /dev/sdc

# 创建 LV
lvcreate -L 500G -n data_lv data_vg

# 格式化与挂载
mkfs.xfs /dev/data_vg/data_lv
mount /dev/data_vg/data_lv /data

# 扩容
lvextend -L +100G /dev/data_vg/data_lv
xfs_growfs /data

# 查看状态
pvdisplay
vgdisplay
lvdisplay
```

## 磁盘性能测试

```bash
# 顺序读写
dd if=/dev/zero of=/tmp/test bs=1M count=4096
dd if=/tmp/test of=/dev/null bs=1M count=4096

# fio 基准测试
fio --name=test --ioengine=libaio --rw=randread --bs=4k --numjobs=4 --size=1G --runtime=60
```
