# 进阶

> 虚拟化进阶 = **libvirt 深度 + 存储池(LVM/iSCSI/Ceph/NFS) + 网络(OVS/VLAN/SR-IOV) + 集群管理(Proxmox VE / oVirt / VMware vSphere) + 调优(NUMA/CPU pinning/HugePage) + 备份与恢复 + Windows VM + 安全加固**。本章面向独立运维 5-50 台 VM 的工程师，给可上生产的工程化方案。

## 一、libvirt 深度

### 1.1 架构

```
virsh / virt-manager / virt-install
         │
         ▼  (libvirt API)
      libvirtd
         │
   ┌─────┼──────┐
   ▼     ▼      ▼
  QEMU  LXC   storage
  KVM         pool/net
```

### 1.2 关键概念

```
Domain       虚拟机（VM）
Network      虚拟网络（NAT/Bridge/Routed）
Pool         存储池（dir/lvm/iscsi/rbd/nfs）
Volume       存储卷（pool 内的磁盘）
Secret       密钥（如 RBD/iSCSI auth）
Node Device  宿主机设备（PCI/USB/NIC）
NWFilter     基于规则的过滤防火墙
```

### 1.3 domain XML 范例

```xml
<domain type='kvm'>
  <name>vm01</name>
  <uuid>xxx</uuid>
  <memory unit='GiB'>16</memory>
  <currentMemory unit='GiB'>16</currentMemory>
  <vcpu placement='static' cpuset='0-3,8-11'>8</vcpu>
  <cpu mode='host-passthrough'>
    <topology sockets='1' cores='4' threads='2'/>
    <numa>
      <cell id='0' cpus='0-7' memory='16' unit='GiB'/>
    </numa>
  </cpu>
  <os>
    <type arch='x86_64' machine='q35'>hvm</type>
    <boot dev='hd'/>
  </os>
  <features>
    <acpi/>
    <apic/>
    <vmport state='off'/>
  </features>
  <clock offset='utc'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <devices>
    <emulator>/usr/libexec/qemu-kvm</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none' io='native' discard='unmap'/>
      <source file='/var/lib/libvirt/images/vm01.qcow2'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <interface type='bridge'>
      <source bridge='br0'/>
      <model type='virtio'/>
    </interface>
    <serial type='pty'><target port='0'/></serial>
    <console type='pty'><target type='serial' port='0'/></console>
    <channel type='unix'>
      <target type='virtio' name='org.qemu.guest_agent.0'/>
    </channel>
    <memballoon model='virtio'/>
    <rng model='virtio'><backend model='random'>/dev/urandom</backend></rng>
  </devices>
</domain>
```

### 1.4 常用 virsh 进阶

```bash
# 资源动态
virsh setvcpus vm01 8 --live
virsh setmem vm01 16G --live --config
virsh memtune vm01 --hard-limit 17G

# 网卡热插
virsh attach-interface vm01 bridge br1 --model virtio --live --config

# 磁盘热插
virsh attach-disk vm01 /var/lib/libvirt/images/data.qcow2 vdb \
  --driver qemu --subdriver qcow2 --cache none --live --config

# 监控
virsh domstats vm01 --vcpu --block --interface
virsh nodecpustats --percent
virsh nodememstats

# 控制台日志
virsh dumpxml vm01 | grep -A2 serial
# /var/log/libvirt/qemu/vm01.log
```

## 二、存储池

### 2.1 选型矩阵

| Pool 类型 | 后端 | 适用 |
|:---|:---|:---|
| **dir** | 本地目录 | 测试 / 单机 |
| **logical** (LVM) | VG | 单机性能 ⭐ |
| **fs** | 块设备 + 文件系统 | 通用 |
| **netfs** | NFS / CIFS | 集群共享 ⭐ |
| **iscsi** | iSCSI LUN | SAN |
| **rbd** | Ceph | 大规模集群 ⭐⭐ |
| **gluster** | GlusterFS | 中小集群 |
| **disk** | 整盘直通 | 高性能 |
| **scsi** | SCSI HBA | 直通 |

### 2.2 NFS 共享存储（集群基础）

```bash
# NFS 服务端
apt install nfs-kernel-server
mkdir -p /export/vmstore
echo "/export/vmstore 10.0.0.0/24(rw,sync,no_subtree_check,no_root_squash)" >> /etc/exports
exportfs -ra
systemctl restart nfs-server

# Host 挂载
mkdir -p /var/lib/libvirt/images-nfs
mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576,hard,intr nfs-srv:/export/vmstore /var/lib/libvirt/images-nfs

# 定义 pool
cat > nfs-pool.xml <<EOF
<pool type='netfs'>
  <name>nfs-pool</name>
  <source>
    <host name='nfs-srv'/>
    <dir path='/export/vmstore'/>
    <format type='nfs'/>
  </source>
  <target><path>/var/lib/libvirt/images-nfs</path></target>
</pool>
EOF
virsh pool-define nfs-pool.xml
virsh pool-start nfs-pool
virsh pool-autostart nfs-pool
```

### 2.3 LVM 池（单机高性能）

```bash
# 创建 VG
pvcreate /dev/sdb
vgcreate vmvg /dev/sdb

# 定义 pool
virsh pool-define-as vmlvm logical --target /dev/vmvg --source-name vmvg
virsh pool-build vmlvm
virsh pool-start vmlvm
virsh pool-autostart vmlvm

# 创建 volume (LV)
virsh vol-create-as vmlvm vm01.disk 50G --format raw

# 用 LV 启 VM
virsh attach-disk vm01 /dev/vmvg/vm01.disk vdb ...
```

### 2.4 Ceph RBD（大规模集群首选）

```bash
# Ceph 端
ceph osd pool create vms 128 128
rbd pool init vms
rbd create vms/vm01-disk --size 50G

# Libvirt 端
virsh secret-define --file <<EOF
<secret ephemeral='no' private='no'>
  <usage type='ceph'><name>client.libvirt</name></usage>
</secret>
EOF
virsh secret-set-value --secret <uuid> --base64 $(ceph auth get-key client.libvirt | base64)

# pool
cat > rbd-pool.xml <<EOF
<pool type='rbd'>
  <name>rbd-pool</name>
  <source>
    <name>vms</name>
    <host name='mon1' port='6789'/>
    <host name='mon2' port='6789'/>
    <host name='mon3' port='6789'/>
    <auth type='ceph' username='libvirt'>
      <secret usage='client.libvirt'/>
    </auth>
  </source>
</pool>
EOF
virsh pool-define rbd-pool.xml
virsh pool-start rbd-pool
```

### 2.5 磁盘高级特性

```xml
<disk type='file' device='disk'>
  <driver name='qemu' type='qcow2'
          cache='none'           ←  必设 none（O_DIRECT，避免 host page cache）
          io='native'            ←  线程模型: native(libaio) / threads / io_uring
          discard='unmap'        ←  支持 TRIM（thin provisioning）
          detect_zeroes='on'/>   ←  写 0 自动 unmap
  <source file='/path/disk.qcow2'/>
  <target dev='vda' bus='virtio'/>
</disk>
```

## 三、网络深度

### 3.1 OVS 取代 Linux Bridge

```bash
# 装
apt install openvswitch-switch
systemctl enable --now openvswitch-switch

# 创建 OVS bridge
ovs-vsctl add-br ovsbr0
ovs-vsctl add-port ovsbr0 eth0

# libvirt 用 OVS
cat > ovs-net.xml <<EOF
<network>
  <name>ovs-net</name>
  <forward mode='bridge'/>
  <bridge name='ovsbr0'/>
  <virtualport type='openvswitch'/>
</network>
EOF
virsh net-define ovs-net.xml
virsh net-start ovs-net
virsh net-autostart ovs-net

# VM 配置加 VLAN tag (XML)
<interface type='bridge'>
  <source bridge='ovsbr0'/>
  <virtualport type='openvswitch'/>
  <vlan><tag id='100'/></vlan>
  <model type='virtio'/>
</interface>
```

### 3.2 SR-IOV VF 直通

```bash
# 1. 开 SR-IOV (网卡支持)
echo 8 > /sys/class/net/eth1/device/sriov_numvfs

# 2. 看 VF
lspci | grep -i 'Virtual Function'

# 3. libvirt 用 VF（hostdev / 或 pool 网络）
<interface type='hostdev' managed='yes'>
  <source>
    <address type='pci' domain='0' bus='0x05' slot='0x10' function='0x0'/>
  </source>
  <vlan><tag id='100'/></vlan>
</interface>

# 或定义 pool 网络
<network>
  <name>sriov-net</name>
  <forward mode='hostdev' managed='yes'>
    <pf dev='eth1'/>
  </forward>
</network>
```

### 3.3 macvtap

```
特点:
  - 直连物理网卡（虚拟出 MAC）
  - 简单快速
  - 但 Host 与 VM 不能互通（同物理口）

XML:
<interface type='direct'>
  <source dev='eth0' mode='bridge'/>
  <model type='virtio'/>
</interface>
```

## 四、集群管理

### 4.1 Proxmox VE（开源首选）

```
特点:
  - 基于 Debian + KVM + LXC
  - Web UI 完善（5/8 节点起步）
  - 集群: corosync + pmxcfs (cluster fs)
  - 存储: ZFS / Ceph (内置) / NFS / iSCSI / LVM
  - HA: ha-manager + watchdog
  - 备份: vzdump + PBS (Proxmox Backup Server)
  
适合:
  - 中小企业
  - 教育/实验室
  - 私有云替代 VMware
  - 国产化基础
```

```bash
# 装包（Debian 12 上）
echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" \
  > /etc/apt/sources.list.d/pve.list
curl -fsSL https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg \
  -o /etc/apt/trusted.gpg.d/proxmox.gpg
apt update && apt install proxmox-ve postfix open-iscsi

# 集群
pvecm create cluster01                          # 第一节点
pvecm add 10.0.0.10                             # 其他节点
pvecm status

# 命令行
qm list                                          # KVM VM
qm create 100 --name vm01 --memory 8192 --cores 4 --net0 virtio,bridge=vmbr0
qm importdisk 100 disk.qcow2 local-lvm
qm set 100 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-100-disk-0
qm start 100
qm migrate 100 node2 --online                    # 在线迁移
```

### 4.2 oVirt (RHV / 红帽虚拟化)

```
特点:
  - 红帽企业级（已开源，对应 RHV）
  - 多 host 集群
  - 完整的 Web UI + REST API
  - Gluster / Ceph 后端
  
适合:
  - 大型企业 / 银行
  - 替代 VMware vSphere
  - 中科红旗 / 国产化版本：龙蜥 / openEuler
```

### 4.3 KubeVirt（在 K8s 跑 VM）

```
特点:
  - K8s 原生 VM 管理
  - VM 作为 CRD (VirtualMachine)
  - 共享 K8s 网络/存储 (CNI/CSI)
  - 适合 VM/容器混部
  
代表:
  Red Hat OpenShift Virtualization
  华为 SparkLink
  阿里云 ACK Edge
```

```bash
# 装
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.2.0/kubevirt-operator.yaml
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.2.0/kubevirt-cr.yaml

# 创建 VM
cat <<EOF | kubectl apply -f -
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata: { name: vm01 }
spec:
  running: true
  template:
    spec:
      domain:
        cpu: { cores: 2 }
        memory: { guest: 4Gi }
        devices:
          disks:
            - { name: rootdisk, disk: { bus: virtio } }
      volumes:
        - name: rootdisk
          containerDisk: { image: quay.io/kubevirt/cirros-container-disk-demo }
EOF
```

### 4.4 VMware vSphere 速查

```
组件:
  ESXi          Hypervisor (Type 1)
  vCenter       管理平面
  vSAN          超融合存储
  NSX           网络虚拟化
  
关键功能:
  vMotion       在线迁移
  DRS           动态资源调度
  HA            高可用
  FT            容错（双机镜像）
  
PowerCLI:
  Connect-VIServer / Get-VM / Start-VM / Move-VM
```

## 五、性能调优

### 5.1 CPU 调优

```bash
# 1. cpu mode = host-passthrough (透传指令集)
<cpu mode='host-passthrough'/>

# 2. CPU pinning (NUMA-aware)
<vcpu placement='static' cpuset='0-3'>4</vcpu>
<cputune>
  <vcpupin vcpu='0' cpuset='0'/>
  <vcpupin vcpu='1' cpuset='1'/>
  ...
</cputune>

# 3. emulator 与 iothread 也绑核
<cputune>
  <emulatorpin cpuset='4-7'/>
  <iothreadpin iothread='1' cpuset='8'/>
</cputune>

# 4. CPU governor
cpupower frequency-set -g performance

# 5. 关 KSM 对低延迟 VM
echo 0 > /sys/kernel/mm/ksm/run
```

### 5.2 内存调优

```xml
<!-- NUMA 绑定 -->
<numatune>
  <memory mode='strict' nodeset='0'/>
</numatune>

<!-- HugePage -->
<memoryBacking>
  <hugepages>
    <page size='1' unit='GiB' nodeset='0'/>
  </hugepages>
  <nosharepages/>
  <locked/>            <!-- mlock，防 swap -->
</memoryBacking>

<!-- 关 ballooning（数据库 VM 强烈建议） -->
<memballoon model='none'/>
```

### 5.3 IO 调优

```xml
<!-- 多 iothread -->
<iothreads>4</iothreads>

<disk>
  <driver name='qemu' type='qcow2'
          cache='none' io='native' discard='unmap'
          queues='4' iothread='1'/>
  <source file='/path/disk.qcow2'/>
  <target dev='vda' bus='virtio'/>
</disk>

<!-- virtio-scsi 多队列（推荐替代 virtio-blk）-->
<controller type='scsi' index='0' model='virtio-scsi'>
  <driver queues='4' iothread='1'/>
</controller>
```

### 5.4 网络调优

```xml
<!-- vhost-net 加速 -->
<interface type='bridge'>
  <source bridge='br0'/>
  <model type='virtio'/>
  <driver name='vhost' queues='4'/>
</interface>

<!-- 大 VM 建议 SR-IOV VF 直通 -->
```

```bash
# Host 侧
# 多队列开
ethtool -L eth0 combined 8

# 中断绑 NUMA 0 CPU
set_irq_affinity.sh 0-7 eth0

# 关 irqbalance 后手动
systemctl stop irqbalance
```

### 5.5 调优 Checklist

```
CPU:
☐ host-passthrough
☐ vcpu pinning + emulatorpin
☐ NUMA 不跨
☐ governor=performance

内存:
☐ HugePage 1G
☐ <locked/> 防 swap
☐ NUMA strict
☐ 关 balloon (低延迟)
☐ 关 KSM (DB)

存储:
☐ cache=none + io=native/io_uring
☐ virtio-scsi + 多队列
☐ iothread
☐ qcow2 → raw（极致）或 LVM

网络:
☐ virtio + vhost-net + 多队列
☐ SR-IOV VF (高吞吐)
☐ 中断绑核

测试:
☐ fio 测磁盘
☐ iperf3 测网络
☐ sysbench 测 CPU/Mem
```

## 六、备份与恢复

### 6.1 备份策略 3-2-1

```
3 份: 在线 + 近线 + 离线
2 介质: SSD/HDD + 对象存储
1 异地
```

### 6.2 工具

```
开源:
  virsh backup-begin                     增量 (libvirt 7.0+)
  blockcommit / blockpull                合并/还原
  PBS (Proxmox Backup Server) ⭐         去重 + 增量 + 加密
  bareos / bacula                         传统
  rbd export-diff                         Ceph 增量

商业:
  Veeam Backup
  Vinchin (国产) ⭐
  爱数 AnyBackup
  鼎甲科技
```

### 6.3 Proxmox Backup Server（首选开源）

```
特点:
  - 客户端去重（保留率 < 5%）
  - 增量 forever-incremental
  - 加密 + 签名
  - 验证完整性
  - Web UI 完善

部署:
  独立物理机 + ZFS RAIDZ2
  与 PVE/客户端 split
```

### 6.4 libvirt 增量备份

```bash
# 启 checkpoint
virsh checkpoint-create-as vm01 cp0

# 全量 (PUSH 给 NBD server)
virsh backup-begin vm01 --backupxml backup.xml

# 增量
virsh backup-begin vm01 --backupxml inc-backup.xml \
  --checkpointxml cp1.xml --reuse-external
```

## 七、Windows VM 实战

### 7.1 必备

```
1. virtio-win.iso (Red Hat)
   driver: viostor/netkvm/balloon/vioscsi

2. 装机时加载驱动:
   <disk type='file' device='cdrom'>
     <driver name='qemu' type='raw'/>
     <source file='/iso/virtio-win.iso'/>
     <target dev='sdc' bus='sata'/>
   </disk>

3. QEMU Guest Agent
   下载 virtio-win-guest-tools.exe 安装

4. 时钟
   <clock offset='localtime'>
     <timer name='hpet' present='yes'/>
   </clock>

5. 串口/控制台
   Windows 启用 EMS 后用 sac
```

### 7.2 性能优化

```
- 关 Defender 实时扫描（Host 已有）
- 视觉效果调"性能优先"
- 关 Indexing / SuperFetch
- 用 virtio-scsi（替代 viostor）
- 启用 RX/TX checksum offload
- 启用 SPICE 而非 VNC（远程）
```

## 八、安全加固

### 8.1 Host 层

```bash
# SELinux / sVirt
getenforce
setenforce 1                                     # 强制 sVirt 隔离

# AppArmor (Ubuntu/Debian)
aa-status
aa-enforce /usr/sbin/libvirtd

# 文件权限
chown root:libvirt-qemu /var/lib/libvirt/images/*.qcow2
chmod 660 /var/lib/libvirt/images/*.qcow2

# 网络隔离
# 管理网 / 业务网 / 存储网 物理隔离
```

### 8.2 nwfilter 范例（防 IP/MAC 欺骗）

```xml
<filter name='clean-vm' chain='root'>
  <filterref filter='no-mac-spoofing'/>
  <filterref filter='no-ip-spoofing'/>
  <filterref filter='no-arp-spoofing'/>
  <filterref filter='allow-incoming-ipv4'/>
  <filterref filter='no-other-l2-traffic'/>
</filter>

<interface>
  <filterref filter='clean-vm'>
    <parameter name='IP' value='10.0.0.10'/>
    <parameter name='MAC' value='52:54:00:11:22:33'/>
  </filterref>
</interface>
```

### 8.3 加密 VM 磁盘

```bash
# qcow2 LUKS 加密
qemu-img create -f qcow2 \
  --object secret,id=sec0,data=mypass \
  -o encrypt.format=luks,encrypt.key-secret=sec0 \
  vm01.qcow2 50G
```

## 九、监控

### 9.1 Prometheus libvirt_exporter

```bash
# github.com/Tinkoff/libvirt-exporter
docker run -d -p 9177:9177 \
  -v /var/run/libvirt:/var/run/libvirt \
  alekseizakharov/libvirt-exporter

# Prom 抓取
- job_name: libvirt
  static_configs:
    - targets: ['kvm-host:9177']
```

### 9.2 关键告警

```yaml
- alert: VMDown
  expr: libvirt_domain_state_code != 1
  for: 5m

- alert: VMHighCPU
  expr: rate(libvirt_domain_info_cpu_time_seconds_total[5m]) / 
        libvirt_domain_info_virtual_cpus > 0.9
  for: 15m

- alert: VMDiskFull
  expr: libvirt_domain_block_capacity_bytes - libvirt_domain_block_allocation_bytes < 5e9
  for: 5m

- alert: HostOvercommit
  expr: sum(libvirt_domain_info_virtual_cpus) by (host) / count(node_cpu_seconds_total{mode='idle'}) by (host) > 3
```

## 十、典型坑（进阶）

| 坑 | 建议 |
|:---|:---|
| **cache=writeback 数据丢** | 生产 cache=none |
| **没设 io_thread** | 多盘 VM IOPS 上不去 |
| **跨 NUMA 没绑** | 大 VM 性能跳水 |
| **balloon 没关 (DB)** | 内存被强收性能崩 |
| **virtio-blk 多队列差** | 改 virtio-scsi |
| **SR-IOV 不能 live migrate** | 关键 VM 不直通 |
| **快照链太长** | 定期 commit / 备份 |
| **NFS 没 hard, intr** | I/O hang VM |
| **共享存储无 fence** | 集群脑裂 |
| **vCPU 超分 1:8 + DB** | DB 永远低超分 |
| **没装 qemu-guest-agent** | 静默快照失败 |

## 十一、推荐栈

```
单机:        KVM + libvirt + LVM/qcow2 + virt-manager
小集群:      Proxmox VE + Ceph / ZFS + PBS
中大集群:    OpenStack (见 05_私有云) / oVirt / KubeVirt
国产替代:    华为 FusionCompute / 深信服 aSV / 浪潮 InCloud / 中科曙光
桌面:        VirtualBox / VMware Workstation
开发:        QEMU + cloud-init + Vagrant + Packer
备份:        PBS ⭐ / Vinchin / Veeam
监控:        Prometheus + libvirt_exporter + Grafana
```

## 十二、学习路径

```
进阶（3-6 月）:
  1. libvirt XML 完全读懂
  2. NFS / LVM / Ceph 存储池上线
  3. OVS + VLAN 接入
  4. CPU pinning + NUMA + HugePage 调优
  5. Proxmox VE 3 节点集群 + 共享存储
  6. PBS 备份 + 恢复演练
  7. Windows VM + 驱动调优
  8. SELinux/AppArmor 隔离
  9. 在线迁移（NFS / Ceph）
  10. 监控接入 + 告警规则
```

> 📖 **核心判断**：进阶 = **libvirt XML 熟练 + 存储池选型(NFS/LVM/Ceph) + OVS+VLAN/SR-IOV + Proxmox VE 集群 + CPU pinning+NUMA+HugePage + PBS 备份**。能搭出"3 节点 PVE + Ceph + PBS"开源全栈、能写出调过 NUMA/HugePage 的 XML、能恢复一次备份，就具备虚拟化平台运维资格。**别再恋战 VirtualBox / 单机 KVM**，从这里起就该集群化。
