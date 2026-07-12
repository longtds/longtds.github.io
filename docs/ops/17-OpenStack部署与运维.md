# OpenStack 部署与运维

> OpenStack 怎么搭？Nova/Neutron/Cinder 怎么配？私有云怎么运维？本文覆盖架构、部署、网络、存储和生产实践。

---

## 一、OpenStack 架构

### 1.1 概述

```
OpenStack — 开源云计算平台

  定位: 私有云 / 混合云 IaaS (Infrastructure as a Service)
  目标: 用标准硬件构建 AWS 级别的云平台
  模式: API 驱动, 自服务, 多租户, 弹性伸缩

  OpenStack vs 其他虚拟化方案:
    传统虚拟化 (KVM/ESXi):  管理员手动创建 VM, 资源固定
    OpenStack:              用户通过 API/Dashboard 自助创建, 弹性伸缩

    传统: 虚拟化管理平台 (virsh/vCenter)
    OS:   云平台 (认证/网络/存储/计算/镜像 编排)

  版本发布: 每年 2 个版本 (Spring/Y, 秋季), 版本名按字母顺序
    2024.03: 2024.1 (Caracal)
    2024.10: 2024.2 (Dalmatian)
    2025.04: 2025.1 (Epoxy)
```

### 1.2 核心组件

```
┌─────────────────────────────────────────────────────────────────┐
│                      OpenStack 架构                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Horizon (Web Dashboard)                │  │
│  │              ┌──────────────┐                             │  │
│  │              │  :80/dashboard│                            │  │
│  │              └──────────────┘                             │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │ REST API                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Keystone │ │   Nova   │ │ Neutron  │ │ Glance   │          │
│  │ (认证)    │ │ (计算)   │ │ (网络)   │ │ (镜像)   │          │
│  │          │ │          │ │          │ │          │          │
│  │ 用户认证  │ │ VM 生命周期│ │ 虚拟网络  │ │ 镜像管理  │          │
│  │ 租户管理  │ │ 调度      │ │ 安全组    │ │ 快照管理  │          │
│  │ Token    │ │ 配额      │ │ 浮动 IP   │ │          │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Cinder   │ │  Swift   │ │  Heat    │ │ Manila   │          │
│  │ (块存储)  │ │ (对象存储)│ │ (编排)   │ │ (文件存储)│          │
│  │          │ │          │ │          │ │          │          │
│  │ 云硬盘    │ │ 对象存储  │ │ 模板部署  │ │ 共享文件  │          │
│  │ 快照      │ │ S3 兼容   │ │ 自动伸缩  │ │ NFS/CIFS │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Ceilometer│ │ gnocchi  │ │  Aodh    │ │ Octavia  │          │
│  │ (计量)    │ │ (指标)   │ │ (告警)   │ │ (LBaaS)  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    基础设施                                │  │
│  │  MySQL/Galera   RabbitMQ   Memcached   HAProxy/Pacemaker │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    计算节点                                │  │
│  │  KVM/QEMU   libvirt   OVS/OVN   LVM/Ceph                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 组件说明

| 组件 | 项目名 | 功能 | 类比 AWS |
|:---|:---|:---|:---|
| Keystone | Identity | 认证/授权/服务目录 | IAM |
| Nova | Compute | VM 生命周期/调度 | EC2 |
| Neutron | Networking | 虚拟网络/路由/安全组 | VPC |
| Glance | Image | 镜像管理 | AMI |
| Cinder | Block Storage | 云硬盘/快照 | EBS |
| Swift | Object Storage | 对象存储 | S3 |
| Horizon | Dashboard | Web UI | Console |
| Heat | Orchestration | 模板编排/自动伸缩 | CloudFormation |
| Manila | File Storage | 共享文件系统 | EFS |
| Octavia | LBaaS | 负载均衡 | ELB |
| Ceilometer | Telemetry | 数据采集 | CloudWatch |
| Gnocchi | Time Series | 指标存储 | - |
| Aodh | Alarming | 告警 | CloudWatch Alarms |
| Designate | DNS | DNS 服务 | Route53 |
| Barbican | Key Manager | 密钥管理 | KMS |
| Magnum | Containers | K8s on OpenStack | EKS |
| Trove | Database | 数据库服务 | RDS |
| Zun | Containers | 容器服务 | ECS (Fargate) |

### 1.4 部署方式对比

| 方式 | 复杂度 | 生产可用 | 适用场景 |
|:---|:---|:---|:---|
| **Kolla-Ansible** | ⭐ 中 | ⭐ 是 | **生产首选**, 容器化部署 |
| TripleO (OpenStack on OpenStack) | 高 | 是 | Red Hat 环境 |
| Packstack | ⭐ 低 | ❌ 否 | 快速原型/PoC |
| DevStack | ⭐ 低 | ❌ 否 | 开发测试 |
| Juju | 中 | 是 | Ubuntu 环境 |
| RDO | 中 | 是 | CentOS/RHEL |
| 手动 | ⭐ 高 | 是 | 深度定制 |

---

## 二、Kolla-Ansible 部署

### 2.1 架构规划

```
生产环境最小集群 (3 控制节点 + N 计算节点):

  ┌─────────────────────────────────────────────────────┐
  │                   外部网络 (External)                 │
  │              192.168.1.0/24 (管理+外部)               │
  └──────┬──────────┬──────────┬──────────┬─────────────┘
         │          │          │          │
  ┌──────▼──┐ ┌────▼────┐ ┌───▼─────┐ ┌──▼──────┐
  │control01│ │control02│ │control03│ │compute01│
  │  .10    │ │  .11    │ │  .12    │ │  .20    │
  │         │ │         │ │         │ │         │
  │ Keystone│ │ Keystone│ │ Keystone│ │ Nova-   │
  │ Nova-API│ │ Nova-API│ │ Nova-API│ │ Compute │
  │ Neutron │ │ Neutron │ │ Neutron │ │ Neutron │
  │ Glance  │ │ Glance  │ │ Glance  │ │ OVN     │
  │ Cinder  │ │ Cinder  │ │ Cinder  │ │ Ceph-OSD│
  │ Horizon │ │ Horizon │ │ Horizon │ │         │
  │ MariaDB │ │ MariaDB │ │ MariaDB │ │         │
  │ RabbitMQ│ │ RabbitMQ│ │ RabbitMQ│ │         │
  │ HAProxy │ │ HAProxy │ │ HAProxy │ │         │
  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
       │           │           │           │
       └───────────┴───────────┘           │
                    │                      │
           ┌────────▼────────┐    ┌────────▼────────┐
           │  Galera Cluster │    │  Ceph Cluster   │
           │  (MySQL HA)     │    │  (分布式存储)    │
           └─────────────────┘    └─────────────────┘

  网络:
    管理/外部网络: 192.168.1.0/24 (所有节点)
    存储网络:      192.168.2.0/24 (Ceph/存储)
    隧道网络:      192.168.3.0/24 (Geneve/VXLAN)
    API VIP:       192.168.1.100 (HAProxy VIP)
    内部 VIP:      192.168.1.101 (MariaDB/RabbitMQ VIP)

  存储规划:
    Ceph: 3 节点 × 4 块 OSD 磁盘 = 12 OSD
    Cinder: 使用 Ceph 后端
    Glance: 使用 Ceph 后端
    Nova: 使用 Ceph 后端 (ephemeral)

  高可用:
    控制面: 3 节点 Galera + RabbitMQ 集群 + HAProxy
    API:    HAProxy VIP (keepalived)
    计算:   故障时 VM 在其他节点重建 (Nova evacuate)
    存储:   Ceph 3 副本
```

### 2.2 环境准备

```bash
# === 所有节点通用配置 ===

# 1. 设置主机名
hostnamectl set-hostname control01.example.com
hostnamectl set-hostname control02.example.com
hostnamectl set-hostname control03.example.com
hostnamectl set-hostname compute01.example.com

# 2. /etc/hosts
cat >> /etc/hosts << 'EOF'
192.168.1.10  control01 control01.example.com
192.168.1.11  control02 control02.example.com
192.168.1.12  control03 control03.example.com
192.168.1.20  compute01 compute01.example.com
192.168.1.100 api-vip api.example.com
EOF

# 3. NTP 时间同步
dnf install -y chrony
cat > /etc/chrony.conf << 'EOF'
server ntp.aliyun.com iburst
server ntp1.aliyun.com iburst
driftfile /var/lib/chrony/drift
makestep 1.0 3
rtcsync
allow 192.168.1.0/24
EOF
systemctl enable --now chronyd

# 4. 关闭防火墙和 SELinux (Kolla 部署要求)
systemctl disable --now firewalld
setenforce 0
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config

# 5. 配置 SSH 免密 (部署节点 → 所有节点)
ssh-keygen -t ed25519
for host in control01 control02 control03 compute01; do
    ssh-copy-id $host
done

# 6. 安装基础软件
dnf install -y git python3-pip python3-devel libffi-devel \
    gcc openssl-devel python3-libselinux

# 7. 配置 Pip 源
mkdir -p /etc/pip.conf.d
cat > /etc/pip.conf << 'EOF'
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
trusted-host = mirrors.aliyun.com
EOF
```

### 2.3 部署节点安装

```bash
# === 在 control01 上安装 Kolla-Ansible ===

# 1. 创建虚拟环境 (避免系统 Python 包冲突)
python3 -m venv /opt/kolla-venv
source /opt/kolla-venv/bin/activate

# 2. 安装 Ansible 和 Kolla
pip install -U pip
pip install 'ansible-core>=2.15,<2.16'
pip install kolla-ansible==18.0.0
pip install kolla

# 3. 复制配置文件
mkdir -p /etc/kolla
cp -r /opt/kolla-venv/share/kolla-ansible/etc_examples/kolla/* /etc/kolla/
cp /opt/kolla-venv/share/kolla-ansible/ansible/inventory/* /etc/kolla/

# 4. 生成密码
kolla-genpwd

# 5. 配置 Ansible
mkdir -p /etc/ansible
cat > /etc/ansible/ansible.cfg << 'EOF'
[defaults]
host_key_checking = False
inventory = /etc/kolla/multinode
pipelining = True
forks = 100
EOF
```

### 2.4 配置文件

```bash
# === /etc/kolla/globals.yml ===
cat > /etc/kolla/globals.yml << 'EOF'
# === 基础 ===
kolla_base_distro: "rocky"            # rocky/ubuntu
kolla_install_type: "source"          # source/binary
openstack_release: "2024.1"           # 版本

# === 网络 ===
network_interface: "eth0"             # 管理/外部网络接口
kolla_external_vip_interface: "eth0"  # VIP 接口
api_interface: "eth0"                 # API 监听接口
storage_interface: "eth1"             # 存储网络接口
tunnel_interface: "eth2"              # 隧道网络接口
neutron_external_interface: "eth3"    # Neutron 外部网络 (不配 IP)

# VIP
kolla_internal_vip_address: "192.168.1.101"
kolla_external_vip_address: "192.168.1.100"

# === DNS ===
dnsmasq_servers: "223.5.5.5,8.8.8.8"

# === 内部 TLS (可选) ===
kolla_enable_tls_external: "no"

# === OpenStack 选项 ===
enable_openstack_core: "yes"

# 核心服务
enable_keystone: "yes"
enable_glance: "yes"
enable_nova: "yes"
enable_neutron: "yes"
enable_cinder: "yes"
enable_horizon: "yes"
enable_heat: "yes"

# 扩展服务
enable_octavia: "yes"                # 负载均衡
enable_manila: "no"                  # 文件存储
enable_designate: "no"               # DNS
enable_magnum: "no"                  # K8s
enable_barbican: "no"                # 密钥管理

# 监控
enable_prometheus: "yes"
enable_grafana: "yes"

# === Nova ===
nova_compute_virt_type: "kvm"        # kvm/qemu
nova_backend_ceph: "yes"

# === Glance ===
glance_backend_ceph: "yes"
glance_backend_file: "no"

# === Cinder ===
cinder_backend_ceph: "yes"
enable_cinder_backend_lvm: "no"

# === Neutron ===
neutron_plugin_type: "ml2.ovn"       # OVN (推荐) / ml2.ovs
neutron_tenant_network_types: "geneve"

# === Ceph ===
enable_ceph: "yes"
ceph_pool_pg_num: 64
ceph_pool_pgp_num: 64

# Ceph OSD 磁盘 (每块磁盘一个 OSD)
# 在 inventory 中通过 ceph_osd_devices 变量指定
ceph_osd_disk: "/dev/sdb"

# === Grafana 密码 ===
grafana_admin_password: "{{ password_grafana }}"
EOF

# === /etc/kolla/passwords.yml ===
# kolla-genpwd 已自动生成随机密码
# 可自定义关键密码:
# database_password: "YourDbPassword"
# keystone_admin_password: "YourAdminPassword"

# === Inventory: /etc/kolla/multinode ===
cat > /etc/kolla/multinode << 'EOF'
[control]
control01 ansible_host=192.168.1.10
control02 ansible_host=192.168.1.11
control03 ansible_host=192.168.1.12

[network]
control01 ansible_host=192.168.1.10
control02 ansible_host=192.168.1.11
control03 ansible_host=192.168.1.12

[compute]
compute01 ansible_host=192.168.1.20

[monitoring]
control01 ansible_host=192.168.1.10
control02 ansible_host=192.168.1.11
control03 ansible_host=192.168.1.12

[storage]
control01 ansible_host=192.168.1.10
control02 ansible_host=192.168.1.11
control03 ansible_host=192.168.1.12
compute01 ansible_host=192.168.1.20

[deployment]
localhost ansible_connection=local

[baremetal:children]
control
network
compute
monitoring
storage

[ceph:children]
storage
EOF
```

### 2.5 执行部署

```bash
# 激活虚拟环境
source /opt/kolla-venv/bin/activate

# 1. 检查依赖
kolla-ansible -i /etc/kolla/multinode bootstrap-servers

# 2. 环境检查
kolla-ansible -i /etc/kolla/multinode prechecks

# 3. 拉取镜像 (镜像较大, 耐心等待)
kolla-ansible -i /etc/kolla/multiname pull

# 4. 部署!
kolla-ansible -i /etc/kolla/multinode deploy

# 5. 生成 admin 凭据文件
kolla-ansible -i /etc/kolla/multinode post-deploy

# 6. 验证
cat /etc/kolla/admin-openrc.sh
source /etc/kolla/admin-openrc.sh
openstack service list
openstack compute service list
openstack network agent list
openstack volume service list

# 访问 Dashboard
# http://192.168.1.100/
# 用户: admin, 密码: grep keystone_admin_password /etc/kolla/passwords.yml

# === 部署后初始化 ===
# 创建网络和镜像
# Kolla 提供初始化脚本
kolla-ansible -i /etc/kolla/multinode deploy-ironic  # (可选)

# 或手动初始化:
source /etc/kolla/admin-openrc.sh

# 创建 cirros 测试镜像
wget http://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img
openstack image create "cirros" \
    --file cirros-0.6.2-x86_64-disk.img \
    --disk-format qcow2 \
    --container-format bare \
    --public

# 创建网络
openstack network create --external --provider-physical-network physnet1 \
    --provider-network-type flat public

openstack subnet create --network public \
    --allocation-pool start=192.168.1.150,end=192.168.1.200 \
    --gateway 192.168.1.1 --subnet-range 192.168.1.0/24 \
    public-subnet

openstack network create --internal private
openstack subnet create --network private \
    --subnet-range 10.0.0.0/24 --gateway 10.0.0.1 \
    --dns-nameserver 223.5.5.5 private-subnet

# 创建路由
openstack router create router1
openstack router set router1 --external-gateway public
openstack router add subnet router1 private-subnet

# 创建安全组规则
openstack security group rule create --ingress --protocol tcp --dst-port 22 default
openstack security group rule create --ingress --protocol tcp --dst-port 80 default
openstack security group rule create --ingress --protocol icmp default

# 创建密钥对
openstack keypair create mykey > ~/.ssh/mykey.pem
chmod 600 ~/.ssh/mykey.pem

# 创建 VM
openstack server create --flavor m1.small --image cirros \
    --network private --security-group default \
    --key-name mykey test-vm

# 创建浮动 IP
openstack floating ip create public
openstack server add floating ip test-vm <floating-ip>

# 验证
openstack server list
ssh -i ~/.ssh/mykey.pem cirros@<floating-ip>
```

---

## 三、Nova（计算）

### 3.1 Nova 架构

```
┌─────────────────────────────────────────────────────────┐
│                    Nova 架构                             │
│                                                         │
│  ┌──────────────────────────────────────────────┐       │
│  │              Nova API (:8774)                 │       │
│  │  接收 REST 请求 → 鉴权 (Keystone) → 调度      │       │
│  └──────────────────┬───────────────────────────┘       │
│                     │                                   │
│  ┌──────────────────▼───────────────────────────┐       │
│  │            Nova Scheduler                     │       │
│  │  选择计算节点:                                 │       │
│  │  - FilterScheduler (过滤+权重)                 │       │
│  │  - 内存/CPU/磁盘 过滤器                        │       │
│  │  -亲和性/反亲和性 过滤器                       │       │
│  └──────────────────┬───────────────────────────┘       │
│                     │ RPC (RabbitMQ)                     │
│  ┌──────────────────▼───────────────────────────┐       │
│  │            Nova Conductor                     │       │
│  │  数据库代理 (Nova-Compute 不直接连 DB)         │       │
│  │  长任务管理 (迁移/重建)                        │       │
│  └──────────────────┬───────────────────────────┘       │
│                     │                                   │
│  ┌──────────────────▼───────────────────────────┐       │
│  │            Nova Compute (计算节点)              │       │
│  │                                              │       │
│  │  ┌─────────────┐  ┌────────────────────┐    │       │
│  │  │ libvirt     │  │ Neutron Agent      │    │       │
│  │  │ (VM 管理)   │  │ (网络配置)          │    │       │
│  │  └─────────────┘  └────────────────────┘    │       │
│  │                                              │       │
│  │  ┌─────────────┐  ┌────────────────────┐    │       │
│  │  │ KVM/QEMU    │  │ Cinder Volume      │    │       │
│  │  │ (虚拟化)    │  │ (存储连接)          │    │       │
│  │  └─────────────┘  └────────────────────┘    │       │
│  └──────────────────────────────────────────────┘       │
│                                                         │
│  Nova Placement API (:8778)                             │
│    资源追踪 (CPU/内存/磁盘/PCIE), 供调度器查询           │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Flavor 管理

```bash
# === 创建 Flavor (实例规格) ===

openstack flavor create --vcpus 2 --ram 4096 --disk 50 \
    --ephemeral 0 --swap 0 \
    m1.medium

openstack flavor create --vcpus 4 --ram 8192 --disk 100 m1.large
openstack flavor create --vcpus 8 --ram 16384 --disk 200 m1.xlarge
openstack flavor create --vcpus 16 --ram 32768 --disk 500 m1.2xlarge

# GPU Flavor (需要 Nova 配置 PCI Passthrough)
openstack flavor create --vcpus 8 --ram 32768 --disk 100 \
    --property pci_passthrough:alias=nvidia-t4:1 \
    gpu.medium

# CPU 绑定 Flavor
openstack flavor set m1.large \
    --property hw:cpu_policy=dedicated \
    --property hw:cpu_thread_policy=require \
    --property hw:numa_nodes=1

# 超分比设置
openstack flavor set m1.small \
    --property quota:cpu_quota=10000 \
    --property quota:cpu_period=20000
# CPU 限制: 50% (10000/20000)

# 查看
openstack flavor list
openstack flavor show m1.medium
```

### 3.3 VM 生命周期管理

```bash
# === 创建 VM ===
openstack server create --flavor m1.medium --image centos9 \
    --network private --security-group default \
    --key-name mykey \
    --availability-zone nova \
    my-server

# 指定计算节点
openstack server create --flavor m1.medium --image centos9 \
    --network private --key-name mykey \
    --host compute01 \
    my-server

# 从启动卷创建
openstack volume create --size 50 --image centos9 boot-vol
openstack server create --flavor m1.medium \
    --volume boot-vol \
    --network private --key-name mykey \
    my-server

# 从快照创建
openstack server create --flavor m1.medium \
    --server-snapshot my-snapshot \
    --network private \
    my-server

# === VM 操作 ===
openstack server start my-server
openstack server stop my-server
openstack server reboot my-server                # 优雅重启
openstack server reboot --hard my-server         # 强制重启
openstack server pause my-server
openstack server unpause my-server
openstack server suspend my-server
openstack server resume my-server
openstack server lock my-server                  # 锁定 (防止误删)
openstack server unlock my-server
openstack server shelve my-server                # 归档 (释放资源, 保留磁盘)
openstack server unshelve my-server              # 恢复

# === 调整规格 ===
openstack server resize --flavor m1.large my-server
openstack server resize confirm my-server        # 确认
openstack server resize revert my-server         # 回退

# === 迁移 ===
# 冷迁移 (VM 关机)
openstack server stop my-server
openstack server migrate my-server
openstack server resize confirm my-server

# 热迁移 (VM 运行中)
openstack server migrate --live compute02 my-server
# 块迁移 (无共享存储)
openstack server migrate --live compute02 --block-migrate my-server

# === 快照 ===
openstack server image create --name my-snapshot my-server

# === 查询 ===
openstack server list
openstack server list --all-projects
openstack server show my-server
openstack server top my-server                   # 资源使用
openstack console url show my-server             # VNC 控制台
```

### 3.4 Nova 调度配置

```ini
# /etc/kolla/nova-scheduler/nova.conf (Kolla 容器内)

[filter_scheduler]
# 过滤器顺序 (从上到下)
enabled_filters = RetryFilter, AvailabilityZoneFilter, RamFilter,
    ComputeFilter, ComputeCapabilitiesFilter, ImagePropertiesFilter,
    ServerGroupAntiAffinityFilter, ServerGroupAffinityFilter,
    PciPassthroughFilter, NUMATopologyFilter

# 权重计算器
weight_classes = compute.ram.weight, compute.cpu.weight

# 调度重试次数
max_attempts = 3

# 内存超分比 (默认 1.5)
ram_allocation_ratio = 1.5

# CPU 超分比 (默认 16, 过高会导致 CPU 争抢)
cpu_allocation_ratio = 4.0

# 磁盘超分比 (默认 1.0)
disk_allocation_ratio = 1.0

# 每个主机的最大 VM 数
max_instances_per_host = 50
```

---

## 四、Neutron（网络）

### 4.1 Neutron 架构

```
┌─────────────────────────────────────────────────────────┐
│                   Neutron 架构 (OVN)                     │
│                                                         │
│  ┌──────────────────────────────────────────────┐       │
│  │            Neutron Server (:9696)             │       │
│  │  REST API → 鉴权 → ML2 插件 → OVN 驱动         │       │
│  └──────────────────┬───────────────────────────┘       │
│                     │                                   │
│  ┌──────────────────▼───────────────────────────┐       │
│  │            OVN Northbound DB                  │       │
│  │  逻辑网络/路由/ACL (存于 OVSDB)               │       │
│  └──────────────────┬───────────────────────────┘       │
│                     │                                   │
│  ┌──────────────────▼───────────────────────────┐       │
│  │            OVN Southbound DB                  │       │
│  │  物理网络映射 (chassis → 逻辑网络)             │       │
│  └──────┬──────────┬──────────┬─────────────────┘       │
│         │          │          │                          │
│  ┌──────▼──┐ ┌────▼────┐ ┌───▼─────┐                   │
│  │ Node 1  │ │ Node 2  │ │ Node 3  │                   │
│  │ ovn-    │ │ ovn-    │ │ ovn-    │                   │
│  │  controller│controller│controller│                   │
│  │  + OVS   │ │  + OVS  │ │  + OVS  │                   │
│  └─────────┘ └─────────┘ └─────────┘                   │
│                                                         │
│  OVN vs OVS (传统 Neutron ML2):                         │
│    OVS:  每个节点运行 neutron-l3-agent/neutron-dhcp     │
│          网络信息分散, DVR 解决东西向流量                 │
│    OVN:  集中式 OVN DB, 分布式 OVN Controller            │
│          无 L3/DHCP Agent, 更轻量, 性能更好               │
│          原生支持 ACL (安全组), 不需要 iptables           │
└─────────────────────────────────────────────────────────┘

  网络类型:
    Flat:   直接桥接到物理网络, 无 VLAN 封装
    VLAN:   802.1Q 封装 (最多 4094 个网络)
    VXLAN:  UDP 封装 (1600 万个网络, 跨三层)
    Geneve: OVN 默认 (类似 VXLAN, 支持元数据)
    GRE:    旧方案 (已被 VXLAN/Geneve 替代)

  OVS (Open vSwitch) 网桥:
    br-int:   集成网桥 (所有 VM 连接此处)
    br-tun:   隧道网桥 (VXLAN/Geneve 封装)
    br-ex:    外部网桥 (连接物理网络)
    br-provider: 提供商网桥 (Flat/VLAN)
```

### 4.2 网络模型

```
OpenStack 网络拓扑:

  ┌─────────────────────────────────────────────────────┐
  │                  外部网络 (Public)                    │
  │              192.168.1.0/24                          │
  │    浮动 IP 池: 192.168.1.150-200                    │
  └──────────────────────┬──────────────────────────────┘
                         │
                  ┌──────▼──────┐
                  │  虚拟路由器  │ (Neutron Router / OVN)
                  │  NAT/SNAT   │
                  └──────┬──────┘
                         │
  ┌──────────────────────▼──────────────────────────────┐
  │                 租户网络 (Private)                    │
  │              10.0.0.0/24                             │
  │                                                      │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
  │  │   VM1    │  │   VM2    │  │   VM3    │          │
  │  │ 10.0.0.4 │  │ 10.0.0.5 │  │ 10.0.0.6 │          │
  │  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
  │       │ tap         │ tap         │ tap              │
  │  ┌────▼─────────────▼─────────────▼─────┐           │
  │  │          br-int (OVS 集成网桥)         │           │
  │  └──────────────────────────────────────┘           │
  │                         │                            │
  │  ┌──────────────────────▼───────────────┐           │
  │  │     Geneve 隧道 (跨计算节点)          │           │
  │  └──────────────────────────────────────┘           │
  └─────────────────────────────────────────────────────┘

  流量路径:
    南北向 (VM → 外网):
      VM → br-int → 路由器 (DNAT/SNAT) → br-ex → 物理网络

    东西向 (VM → VM, 同节点):
      VM1 → br-int → VM2 (直接, 不出节点)

    东西向 (VM → VM, 跨节点):
      VM1 → br-int → br-tun (Geneve 封装) → 网络 → br-tun → br-int → VM2
```

### 4.3 网络配置

```bash
# === 创建网络 ===

# 外部网络 (Flat, 连接物理网络)
openstack network create --external \
    --provider-physical-network physnet1 \
    --provider-network-type flat \
    public

# 外部子网 (浮动 IP 池)
openstack subnet create --network public \
    --allocation-pool start=192.168.1.150,end=192.168.1.200 \
    --gateway 192.168.1.1 \
    --subnet-range 192.168.1.0/24 \
    --no-dhcp \
    public-subnet

# 租户网络 (Geneve)
openstack network create private
openstack subnet create --network private \
    --subnet-range 10.0.0.0/24 \
    --gateway 10.0.0.1 \
    --dns-nameserver 223.5.5.5 \
    private-subnet

# VLAN 网络
openstack network create --internal \
    --provider-physical-network physnet1 \
    --provider-network-type vlan \
    --provider-segment 100 \
    vlan100

# === 路由器 ===
openstack router create router1
openstack router set router1 --external-gateway public
openstack router add subnet router1 private-subnet

# 查看
openstack router show router1
openstack router port list router1

# === 安全组 ===
openstack security group create web-sg

# 允许 SSH
openstack security group rule create --ingress \
    --protocol tcp --dst-port 22 \
    --remote-ip 0.0.0.0/0 web-sg

# 允许 HTTP/HTTPS
openstack security group rule create --ingress \
    --protocol tcp --dst-port 80 --remote-ip 0.0.0.0/0 web-sg
openstack security group rule create --ingress \
    --protocol tcp --dst-port 443 --remote-ip 0.0.0.0/0 web-sg

# 允许 ICMP
openstack security group rule create --ingress \
    --protocol icmp --remote-ip 0.0.0.0/0 web-sg

# 允许同安全组互通
openstack security group rule create --ingress \
    --remote-group web-sg web-sg

# === 浮动 IP ===
openstack floating ip create public
openstack server add floating ip my-server 192.168.1.155

# === QoS (带宽限制) ===
openstack network qos policy create bandwidth-limit
openstack network qos rule create bandwidth-limit \
    --max-kbps 10000 --max-burst-kbits 10000 \
    --type bandwidth-limit

# 应用到端口
openstack port set --qos-policy bandwidth-limit <port-id>

# === Trunk (一个 VM 多个网络) ===
openstack network trunk create trunk1 \
    --parent-port <parent-port-id>
openstack network trunk subport add trunk1 \
    --port <subport-id> \
    --segmentation-type vlan \
    --segmentation-id 200
```

### 4.4 Octavia（负载均衡）

```bash
# Octavia = LBaaS v2 (替代旧 Neutron-LBaaS)

# 创建负载均衡器
openstack loadbalancer create --name lb1 \
    --vip-subnet-id private-subnet

# 创建监听器
openstack loadbalancer listener create --name listener1 \
    --protocol HTTP --protocol-port 80 lb1

# 创建池
openstack loadbalancer pool create --name pool1 \
    --lb-algorithm ROUND_ROBIN \
    --listener listener1 --protocol HTTP

# 添加成员 (后端 VM)
openstack loadbalancer member create --address 10.0.0.4 \
    --protocol-port 8080 pool1
openstack loadbalancer member create --address 10.0.0.5 \
    --protocol-port 8080 pool1

# 健康检查
openstack loadbalancer healthmonitor create \
    --name hm1 --type HTTP --delay 5 --timeout 3 \
    --max-retries 3 --url-path /health pool1

# 创建浮动 IP 关联 VIP
openstack floating ip create --port <lb-vip-port-id> public
```

---

## 五、Cinder（块存储）

### 5.1 Cinder 架构

```
┌─────────────────────────────────────────────────────────┐
│                    Cinder 架构                          │
│                                                         │
│  ┌──────────────────────────────────────────────┐       │
│  │            Cinder API (:8776)                 │       │
│  │  REST API → 鉴权 → 调度                       │       │
│  └──────────────────┬───────────────────────────┘       │
│                     │                                   │
│  ┌──────────────────▼───────────────────────────┐       │
│  │            Cinder Scheduler                   │       │
│  │  选择存储后端 (CapacityFilter/Capabilities)    │       │
│  └──────────────────┬───────────────────────────┘       │
│                     │ RPC                               │
│  ┌──────────────────▼───────────────────────────┐       │
│  │            Cinder Volume (存储节点)            │       │
│  │                                              │       │
│  │  后端驱动:                                    │       │
│  │  ├── Ceph (RBD)     ← 推荐, 分布式存储        │       │
│  │  ├── LVM (iSCSI)    ← 本地存储                │       │
│  │  ├── NFS            ← 简单共享存储            │       │
│  │  ├── Pure Storage   ← 商业存储                │       │
│  │  └── NetApp         ← 商业存储                │       │
│  └──────────────────────────────────────────────┘       │
│                                                         │
│  Volume 生命周期:                                        │
│    创建 → 挂载到 VM → 使用 → 卸载 → 快照 → 删除          │
│                                                         │
│  Volume 类型:                                            │
│    通过 type → extra_specs 映射到不同存储后端             │
│    如: ssd → Ceph SSD 池, hdd → Ceph HDD 池             │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Volume 管理

```bash
# === 创建 Volume ===
openstack volume create --size 50 my-vol
openstack volume create --size 100 --type ssd ssd-vol

# 从镜像创建 (启动盘)
openstack volume create --size 50 --image centos9 boot-vol

# 从快照创建
openstack volume create --size 50 --snapshot snap1 restored-vol

# 从其他 Volume 克隆
openstack volume create --size 50 --source-vol orig-vol cloned-vol

# === 挂载/卸载 ===
openstack server add volume my-server my-vol
openstack server remove volume my-server my-vol

# === 快照 ===
openstack volume snapshot create --name snap1 my-vol
openstack volume snapshot list
openstack volume snapshot show snap1

# 从快照恢复
openstack volume set --snapshot-snap snap1 my-vol

# === 扩容 ===
openstack volume set --size 100 my-vol

# === 迁移 ===
# 在线迁移 (存储后端不同)
openstack volume migrate my-vol --host compute01@ceph --force

# === Volume 类型 ===
openstack volume type create ssd
openstack volume type set ssd \
    --property volume_backend_name=ceph-ssd

openstack volume type create hdd
openstack volume type set hdd \
    --property volume_backend_name=ceph-hdd

# QoS
openstack volume qos create high-iops
openstack volume qos set high-iops \
    --property read_iops_sec=5000 \
    --property write_iops_sec=2000 \
    --property read_bytes_sec=104857600 \
    --property write_bytes_sec=52428800
openstack volume qos associate high-iops ssd
```

---

## 六、Glance（镜像）

```bash
# === 镜像管理 ===

# 创建镜像
openstack image create "CentOS-9" \
    --file CentOS-9-stream-x86_64.qcow2 \
    --disk-format qcow2 \
    --container-format bare \
    --public \
    --property hw_qemu_guest_agent=yes \
    --property os_type=linux \
    --property hw_firmware_type=bios \
    --property hw_machine_type=q35

# UEFI 镜像
openstack image create "Ubuntu-24-UEFI" \
    --file ubuntu-24.04-server-cloudimg.qcow2 \
    --disk-format qcow2 \
    --container-format bare \
    --public \
    --property hw_firmware_type=uefi \
    --property hw_machine_type=q35 \
    --property os_type=linux

# 镜像属性
openstack image set --property hw_cpu_policy=dedicated <image-id>
openstack image set --min-ram 4096 --min-disk 50 <image-id>
openstack image set --protected <image-id>             # 防删
openstack image set --unprotected <image-id>

# 查看镜像
openstack image list
openstack image show <image-id>

# 下载镜像
openstack image save --file backup.qcow2 <image-id>

# === 镜像制作 ===
# 使用 virt-install + cloud-init 制作镜像
virt-install --name img-build --ram 4096 --vcpus 2 \
    --disk path=/tmp/centos9.img,size=20,format=qcow2 \
    --network bridge=br0,model=virtio \
    --os-variant rocky9 \
    --cdrom /iso/CentOS-9-stream.iso \
    --graphics vnc --noautoconsole

# 安装完成后:
# 1. 安装 cloud-init
# 2. 安装 acpid (允许 ACPI 关机)
# 3. 设置 root 或 cloud-user 密码为空
# 4. 清理 SSH host key
# 5. 关机

# 压缩镜像
virt-sysprep -d img-build
qemu-img convert -O qcow2 -c /tmp/centos9.img /tmp/centos9-compressed.qcow2
```

---

## 七、Heat（编排）

```yaml
# heat-template.yaml — 编排模板
heat_template_version: 2024-04-10

description: Web 服务器集群

parameters:
  image_id:
    type: string
    default: centos9
    description: 镜像名
  flavor:
    type: string
    default: m1.medium
  network:
    type: string
    default: private
  count:
    type: number
    default: 3
    description: 实例数量

resources:
  # 安全组
  web_sg:
    type: OS::Neutron::SecurityGroup
    properties:
      rules:
        - protocol: tcp
          port_range_min: 22
          port_range_max: 22
        - protocol: tcp
          port_range_min: 80
          port_range_max: 80
        - protocol: icmp

  # VM 组
  web_servers:
    type: OS::Heat::ResourceGroup
    properties:
      count: { get_param: count }
      resource_def:
        type: OS::Nova::Server
        properties:
          name: web-%index%
          image: { get_param: image_id }
          flavor: { get_param: flavor }
          networks:
            - network: { get_param: network }
          security_groups:
            - { get_resource: web_sg }
          user_data: |
            #!/bin/bash
            dnf install -y httpd
            systemctl enable --now httpd
            echo "Hello from $(hostname)" > /var/www/html/index.html

outputs:
  server_ips:
    description: VM IP 地址
    value: { get_attr: [web_servers, first_address] }
```

```bash
# 部署
openstack stack create -t heat-template.yaml web-cluster \
    --parameter count=5

# 查看状态
openstack stack list
openstack stack show web-cluster
openstack stack resource list web-cluster

# 更新 (扩容)
openstack stack update -t heat-template.yaml web-cluster \
    --parameter count=8

# 删除
openstack stack delete web-cluster
```

---

## 八、Ceph 集成

### 8.1 Ceph 与 OpenStack

```
Ceph 为 OpenStack 提供 3 种存储:

  ┌───────────────────────────────────────────────────┐
  │                  Ceph 架构                        │
  │                                                   │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
  │  │   MON    │ │   MON    │ │   MON    │         │
  │  │ (监控)   │ │          │ │          │         │
  │  └──────────┘ └──────────┘ └──────────┘         │
  │                                                   │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
  │  │   MDS    │ │   MGR    │ │   RGW    │         │
  │  │ (CephFS) │ │ (管理)   │ │ (S3/Swift)│        │
  │  └──────────┘ └──────────┘ └──────────┘         │
  │                                                   │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
  │  │   OSD    │ │   OSD    │ │   OSD    │         │
  │  │  (disk)  │ │  (disk)  │ │  (disk)  │         │
  │  └──────────┘ └──────────┘ └──────────┘         │
  │                                                   │
  │  OpenStack 集成:                                  │
  │    Glance  → Ceph RBD (images 池)                 │
  │    Cinder  → Ceph RBD (volumes 池)                │
  │    Nova    → Ceph RBD (vms 池, ephemeral 磁盘)    │
  │    Swift   → Ceph RGW (S3 兼容 API)               │
  │    Manila  → CephFS (文件共享)                    │
  └───────────────────────────────────────────────────┘

  Ceph 池规划:
    .mgr:      Ceph 管理器 (自动创建)
    images:    Glance 镜像 (3 副本)
    volumes:   Cinder 云硬盘 (3 副本)
    vms:       Nova 临时磁盘 (3 副本)
    backups:   Cinder 备份 (3 副本)
    cephfs:    CephFS 元数据+数据 (Manila)

  PG 数量计算:
    总 PG = OSD 数 × 100 / 副本数
    例: 12 OSD × 100 / 3 = 400 PG (分给各池)
    images:  64 PG
    volumes: 128 PG
    vms:     128 PG
    backups: 32 PG
```

### 8.2 Ceph 配置

```bash
# === Kolla 部署的 Ceph (容器化) ===

# 查看 Ceph 集群状态
docker exec ceph_mon ceph -s
docker exec ceph_mon ceph osd tree
docker exec ceph_mon ceph df
docker exec ceph_mon ceph osd pool ls

# 查看 PG 状态
docker exec ceph_mon ceph pg stat

# === 池管理 ===
# 创建池
docker exec ceph_mon ceph osd pool create images 64
docker exec ceph_mon ceph osd pool create volumes 128
docker exec ceph_mon ceph osd pool create vms 128
docker exec ceph_mon ceph osd pool create backups 32

# 设置副本数
docker exec ceph_mon ceph osd pool set images size 3
docker exec ceph_mon ceph osd pool set images min_size 2

# 设置 PG 数
docker exec ceph_mon ceph osd pool set images pg_num 64
docker exec ceph_mon ceph osd pool set images pgp_num 64

# === 初始化 Ceph 客户端认证 ===
# Glance 用户
docker exec ceph_mon ceph auth get-or-create client.glance \
    mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=images'

# Cinder 用户
docker exec ceph_mon ceph auth get-or-create client.cinder \
    mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=volumes, allow rwx pool=vms, allow rx pool=images'

# Nova 用户
docker exec ceph_mon ceph auth get-or-create client.nova \
    mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=vms, allow rx pool=images'

# 查看
docker exec ceph_mon ceph auth list

# === Ceph 性能调优 ===
# /etc/kolla/config/ceph.conf
[global]
osd_pool_default_size = 3
osd_pool_default_min_size = 2
osd_pool_default_pg_num = 64
osd_pool_default_pgp_num = 64

# 性能
osd_op_threads = 32
osd_disk_threads = 4
osd_recovery_op_priority = 1
osd_recovery_max_active = 3
osd_max_backfills = 1

# 缓存
rbd_cache = true
rbd_cache_size = 268435456         # 256MB
rbd_cache_max_dirty = 134217728    # 128MB
rbd_cache_target_dirty = 67108864  # 64MB
rbd_cache_writethrough_until_flush = true
```

---

## 九、高可用

### 9.1 控制面高可用

```
OpenStack 控制面 HA (Kolla 默认架构):

  ┌─────────────────────────────────────────────────────┐
  │                    负载均衡                           │
  │              HAProxy + Keepalived                    │
  │              VIP: 192.168.1.100                      │
  └──────┬──────────┬──────────┬────────────────────────┘
         │          │          │
  ┌──────▼──┐ ┌────▼────┐ ┌───▼─────┐
  │control01│ │control02│ │control03│
  │         │ │         │ │         │
  │ 所有 API│ │ 所有 API│ │ 所有 API│  ← 3 副本无状态
  │ 服务    │ │ 服务    │ │ 服务    │
  └────┬────┘ └────┬────┘ └────┬────┘
       │           │           │
  ┌────▼───────────▼───────────▼────┐
  │        MariaDB Galera            │  ← 3 节点同步复制
  │        (MySQL HA)                │
  └─────────────────────────────────┘
  ┌─────────────────────────────────┐
  │        RabbitMQ Cluster          │  ← 3 节点镜像队列
  └─────────────────────────────────┘

  HA 层级:
    1. HAProxy + Keepalived: API VIP 高可用
    2. MariaDB Galera: 数据库高可用 (同步复制)
    3. RabbitMQ Cluster: 消息队列高可用 (镜像队列)
    4. 多副本 API: 无状态服务多实例
    5. Pacemaker (可选): 管理关键资源 VIP
```

### 9.2 计算节点高可用

```bash
# === 计算 HA (Nova evacuate) ===
# 当计算节点故障时, VM 在其他节点重建

# 1. 配置 Nova 驱逐
# /etc/kolla/nova/nova.conf
[DEFAULT]
# 主机故障检测超时
resume_guests_state_on_host_boot = True
# 驱逐时是否使用共享存储 (Ceph)
nova_compute_provider = true

# 2. 配置 Masakari (计算 HA 服务)
# Masakari 监控计算节点, 故障时自动触发驱逐

# 安装 Masakari (Kolla)
# globals.yml: enable_masakari: "yes"

# 配置监控
# /etc/kolla/masakari-monitors/masakarimonitors.conf
[libvirt]
connection = qemu:///system

# 3. 手动驱逐
# 标记主机为 down
openstack compute service set --disable --down \
    compute01.example.com nova-compute

# 驱逐 VM (在 Ceph 共享存储上重建)
openstack server evacuate compute01.example.com

# 4. 验证
openstack server list --host compute02.example.com
```

### 9.3 健康检查

```bash
# === 集群健康检查脚本 ===

#!/bin/bash
source /etc/kolla/admin-openrc.sh

echo "=== OpenStack 健康检查 ==="

# 1. 服务状态
echo "--- Compute Services ---"
openstack compute service list -f value | awk '{
    if ($4 == "up" && $6 == "enabled") print "✅ " $2 " " $6
    else print "❌ " $2 " " $4 " " $6
}'

echo "--- Network Agents ---"
openstack network agent list -f value | awk '{
    if ($4 == "True") print "✅ " $2
    else print "❌ " $2
}'

echo "--- Volume Services ---"
openstack volume service list -f value | awk '{
    if ($4 == "up" && $6 == "enabled") print "✅ " $2
    else print "❌ " $2
}'

# 2. Ceph
echo "--- Ceph ---"
docker exec ceph_mon ceph health

# 3. Galera
echo "--- Galera ---"
docker exec mariadb mysql -uroot -p"$(cat /etc/kolla/passwords.yml | grep database_password | awk '{print $2}')" \
    -e "SHOW STATUS LIKE 'wsrep_cluster_size'"

# 4. RabbitMQ
echo "--- RabbitMQ ---"
docker exec rabbitmq rabbitmqctl cluster_status

# 5. HAProxy
echo "--- HAProxy ---"
curl -s http://192.168.1.100:1984/haproxy_stats | grep -c "UP"
```

---

## 十、监控

### 10.1 Prometheus + Grafana

```bash
# Kolla 内置 Prometheus + Grafana
# globals.yml: enable_prometheus: "yes" / enable_grafana: "yes"

# 访问 Grafana
# http://192.168.1.100:3000
# 密码: grep grafana_admin_password /etc/kolla/passwords.yml

# Prometheus 抓取的 OpenStack 指标:
#   nova_*: VM 数量/调度/迁移
#   neutron_*: 网络/IP/端口
#   cinder_*: Volume/快照
#   glance_*: 镜像
#   keystone_*: 用户/租户

# Grafana 仪表盘:
# OpenStack Overview:  ID 1283
# Ceph:               ID 2842
# RabbitMQ:           ID 10991
# HAProxy:            ID 2428
# MariaDB:            ID 7364
```

### 10.2 日常巡检命令

```bash
source /etc/kolla/admin-openrc.sh

# === 宿主机 ===
openstack hypervisor list
openstack hypervisor stats show

# === VM ===
openstack server list --all-projects
openstack server list --host compute01

# 资源使用
openstack usage list
openstack usage show

# === 网络 ===
openstack network list
openstack router list
openstack port list
openstack floating ip list

# === 存储 ===
openstack volume list --all-projects
openstack volume snapshot list
openstack volume service list

# === 镜像 ===
openstack image list

# === 配额 ===
openstack quota show
openstack quota show --compute
openstack quota show --network
openstack quota show --volume

# 设置配额
openstack quota set --ram 51200 --cores 50 --instances 20 <project>
openstack quota set --gigabytes 5000 --volumes 50 <project>
openstack quota set --network 20 --subnet 20 --port 100 --floatingip 10 <project>

# === Ceph ===
docker exec ceph_mon ceph -s
docker exec ceph_mon ceph df
docker exec ceph_mon ceph osd df
docker exec ceph_mon ceph osd pool ls detail
```

---

## 十一、故障排查

### 11.1 常见问题

| 问题 | 排查 | 解决 |
|:---|:---|:---|
| VM 创建失败 | Nova 日志/调度器/资源 | 检查计算节点资源/镜像/网络 |
| VM 网络不通 | Neutron/OVS/OVN 日志 | 检查安全组/路由/端口 |
| Volume 挂载失败 | Cinder/Ceph 日志 | 检查 Ceph 状态/cinder-volume |
| API 503 | HAProxy/服务状态 | 检查服务容器/MariaDB/RabbitMQ |
| Galera 不同步 | wsrep 状态 | 重启节点/强制主 |
| RabbitMQ 队列积压 | rabbitmqctl | 重启消费者/清理队列 |
| Ceph PG 降级 | ceph -s | 等待恢复/检查 OSD |
| 镜像上传失败 | Glance 日志/Ceph | 检查 images 池/磁盘空间 |

### 11.2 日志查看

```bash
# === Kolla 容器日志 ===
# 所有 OpenStack 服务运行在 Docker 容器中

# 查看所有容器
docker ps --format "table {{.Names}}\t{{.Status}}"

# 查看日志
docker logs nova_api
docker logs nova_compute
docker logs neutron_server
docker logs cinder_volume
docker logs glance_api
docker logs horizon

# 实时日志
docker logs -f nova_api --tail 100

# === 查看特定错误 ===
docker logs nova_api 2>&1 | grep -i error
docker logs nova_scheduler 2>&1 | grep -i "no valid host"
docker logs neutron_server 2>&1 | grep -i error

# === VM 控制台日志 ===
openstack console log show my-server

# === VM VNC 控制台 ===
openstack console url show my-server
```

### 11.3 诊断命令

```bash
# === Nova 诊断 ===
# 查看调度详情
openstack server show my-server --fit-width

# 查看 VM XML
docker exec nova_compute virsh list --all
docker exec nova_compute virsh dumpxml <instance-uuid>

# 查看计算节点资源
openstack hypervisor show compute01

# === Neutron 诊断 ===
# 查看端口
openstack port list --server my-server

# OVN 诊断
docker exec ovn_controller ovn-nbctl show
docker exec ovn_controller ovn-sbctl show
docker exec ovn_controller ovn-trace <logical-switch> <port>

# OVS 诊断
docker exec openvswitch_vswitchd ovs-vsctl show
docker exec openvswitch_vswitchd ovs-ofctl dump-flows br-int

# === Ceph 诊断 ===
docker exec ceph_mon ceph -s
docker exec ceph_mon ceph osd tree
docker exec ceph_mon ceph pg dump_stuck
docker exec ceph_mon ceph health detail

# === 数据库诊断 ===
# Galera 集群状态
docker exec mariadb mysql -uroot -p<pwd> \
    -e "SHOW STATUS LIKE 'wsrep%'" | grep -E 'cluster_size|cluster_status|ready'

# === RabbitMQ 诊断 ===
docker exec rabbitmq rabbitmqctl cluster_status
docker exec rabbitmq rabbitmqctl list_queues | head -20
docker exec rabbitmq rabbitmqctl list_connections | wc -l
```

---

## 十二、运维操作

### 12.1 节点维护

```bash
# === 计算节点维护 (迁移 VM) ===

# 1. 禁用计算节点 (新 VM 不调度到此)
openstack compute service set --disable \
    compute01.example.com nova-compute

# 2. 迁移所有 VM
# 查看该节点上的 VM
openstack server list --host compute01.example.com --all-projects

# 逐个热迁移
for vm in $(openstack server list --host compute01.example.com -f value -c ID); do
    openstack server migrate --live compute02 $vm
done

# 3. 等待迁移完成
openstack server list --host compute01.example.com --all-projects
# 确认为空

# 4. 维护操作 (升级内核/重启等)
ssh compute01
dnf update -y
reboot

# 5. 恢复
openstack compute service set --enable \
    compute01.example.com nova-compute

# === Ceph OSD 维护 ===
# 1. 标记 OSD 为 out (数据迁移到其他 OSD)
docker exec ceph_mon ceph osd out <osd-id>

# 2. 等待数据迁移完成
docker exec ceph_mon ceph -s
# 等待 "recovery" 完成

# 3. 停止 OSD
docker exec ceph_mon ceph osd stop <osd-id>
docker exec ceph_mon ceph osd purge <osd-id> --yes-i-really-mean-it

# 4. 维护磁盘/更换磁盘

# 5. 重新添加 OSD
# (Kolla 会自动发现新磁盘)
```

### 12.2 备份与恢复

```bash
# === 数据库备份 ===
# MariaDB 备份
docker exec mariadb mysqldump -uroot -p<pwd> --all-databases --single-transaction \
    > /backup/openstack-db-$(date +%Y%m%d).sql

# 各服务数据库
for db in keystone nova nova_api nova_cell1 neutron cinder glance heat; do
    docker exec mariadb mysqldump -uroot -p<pwd> --single-transaction $db \
        > /backup/${db}-$(date +%Y%m%d).sql
done

# === 配置备份 ===
tar czf /backup/kolla-config-$(date +%Y%m%d).tar.gz /etc/kolla/

# === Ceph 配置备份 ===
docker exec ceph_mon ceph config dump > /backup/ceph-config-$(date +%Y%m%d).txt
docker exec ceph_mon ceph auth list > /backup/ceph-auth-$(date +%Y%m%d).txt

# === 镜像备份 ===
for img in $(openstack image list -f value -c ID); do
    openstack image save --file /backup/image-${img}.qcow2 $img
done
```

### 12.3 升级

```bash
# === Kolla-Ansible 升级 ===

# 1. 备份
# (执行上面的备份操作)

# 2. 更新 globals.yml 版本
sed -i 's/openstack_release: "2024.1"/openstack_release: "2024.2"/' /etc/kolla/globals.yml

# 3. 更新 Kolla-Ansible
source /opt/kolla-venv/bin/activate
pip install kolla-ansible==19.0.0

# 4. 更新配置文件
cp -r /opt/kolla-venv/share/kolla-ansible/etc_examples/kolla/* /etc/kolla/

# 5. 拉取新镜像
kolla-ansible -i /etc/kolla/multinode pull

# 6. 升级
kolla-ansible -i /etc/kolla/multinode upgrade

# 7. 验证
source /etc/kolla/admin-openrc.sh
openstack service list
openstack compute service list
```

---

## 十三、配置文件速查表

| 组件 | 配置路径 (Kolla 容器) | 端口 |
|:---|:---|:---|
| Keystone | `/etc/kolla/keystone/keystone.conf` | 5000 |
| Nova API | `/etc/kolla/nova-api/nova.conf` | 8774 |
| Nova Scheduler | `/etc/kolla/nova-scheduler/nova.conf` | - |
| Nova Compute | `/etc/kolla/nova-compute/nova.conf` | - |
| Neutron Server | `/etc/kolla/neutron-server/neutron.conf` | 9696 |
| Neutron OVN | `/etc/kolla/neutron-openvswitch-agent/` | - |
| Glance API | `/etc/kolla/glance-api/glance-api.conf` | 9292 |
| Cinder API | `/etc/kolla/cinder-api/cinder.conf` | 8776 |
| Cinder Volume | `/etc/kolla/cinder-volume/cinder.conf` | - |
| Horizon | `/etc/kolla/horizon/local_settings` | 80 |
| Heat API | `/etc/kolla/heat-api/heat.conf` | 8004 |
| Octavia | `/etc/kolla/octavia-api/octavia.conf` | 9876 |
| MariaDB | `/etc/kolla/mariadb/mariadb.conf` | 3306 |
| RabbitMQ | `/etc/kolla/rabbitmq/rabbitmq.conf` | 5672 |
| HAProxy | `/etc/kolla/haproxy/haproxy.cfg` | 80/443/VIP |
| Ceph MON | `/etc/kolla/ceph-mon/ceph.conf` | 6789 |
| Ceph OSD | `/etc/kolla/ceph-osd/ceph.conf` | 6800-7300 |
| Grafana | `/etc/kolla/grafana/grafana.ini` | 3000 |
| Prometheus | `/etc/kolla/prometheus/prometheus.yml` | 9091 |
| Kolla 全局 | `/etc/kolla/globals.yml` | - |
| Kolla 密码 | `/etc/kolla/passwords.yml` | - |
| Inventory | `/etc/kolla/multinode` | - |

---

*最后更新: 2026-07-11*
