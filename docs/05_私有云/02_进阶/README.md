# 进阶

> 私有云进阶 = **OpenStack 多节点部署(Kolla-Ansible) + HA 架构(MariaDB Galera/RabbitMQ/HAProxy/Keepalived) + Neutron OVN 落地 + Cinder+Ceph 整合 + Octavia LBaaS + Magnum K8s + Ironic 裸金属 + Heat/Terraform 编排 + 配额与多租户运维 + 监控(Prometheus+SkyLine)**。本章面向独立部署私有云 50-500 节点的工程师。

## 一、生产部署：Kolla-Ansible

### 1.1 节点规划

```
3x 控制节点   控制面 + DB + MQ + API (HA 三副本)
2x 网络节点   Neutron L3 agent + DHCP (HA 双活，或 OVN 取消)
N x 计算节点   nova-compute + libvirt + KVM
3x 存储节点   Ceph mon + mgr + N OSD
1x 部署节点   Kolla-Ansible 工作机

网络:
  mgmt        10.0.0.0/24       管理 API
  tunnel      10.1.0.0/24       VXLAN/Geneve
  external    10.2.0.0/24       浮动 IP / 公网
  storage     10.3.0.0/24       Ceph
  bmc         10.99.0.0/24      IPMI（运维）
```

### 1.2 部署节点准备

```bash
# 部署节点 (kolla deployer)
apt install -y python3-pip python3-venv git
python3 -m venv ~/kolla
source ~/kolla/bin/activate

pip install ansible==8.* "kolla-ansible[ansible]==18.*"      # 对应 Caracal (2024.1)
mkdir -p /etc/kolla
cp -r ~/kolla/share/kolla-ansible/etc_examples/kolla/* /etc/kolla/
cp ~/kolla/share/kolla-ansible/ansible/inventory/multinode /etc/kolla/

# 生成密码
kolla-genpwd
```

### 1.3 globals.yml 关键配置

```yaml
kolla_base_distro: "rocky"
openstack_release: "2024.1"

# VIP
kolla_internal_vip_address: "10.0.0.250"
kolla_external_vip_address: "10.2.0.250"

# 网卡（部署节点和 controllers 上的接口名）
network_interface: "eth0"           # mgmt
neutron_external_interface: "eth1"  # ext
tunnel_interface: "eth2"            # vxlan
storage_interface: "eth3"           # ceph

# Hypervisor
nova_compute_virt_type: "kvm"

# Neutron
neutron_plugin_agent: "ovn"                  # OVN ⭐ 主流
neutron_ovn_distributed_fip: "yes"

# 存储（外部 Ceph，本例不集成 Ceph-Ansible）
enable_ceph: "no"
glance_backend_ceph: "yes"
cinder_backend_ceph: "yes"
nova_backend_ceph: "yes"
ceph_glance_user: "glance"
ceph_cinder_user: "cinder"
ceph_nova_user: "nova"

# 服务开关
enable_haproxy: "yes"               # 内置 LB
enable_keepalived: "yes"
enable_mariadb: "yes"
enable_rabbitmq: "yes"
enable_memcached: "yes"
enable_redis: "yes"

enable_neutron_provider_networks: "yes"
enable_octavia: "yes"
enable_magnum: "yes"
enable_heat: "yes"
enable_designate: "yes"
enable_barbican: "yes"
enable_skyline: "yes"               # 新 Web UI（取代 Horizon）
enable_horizon: "yes"
enable_cinder_backup: "yes"

# TLS
kolla_enable_tls_internal: "yes"
kolla_enable_tls_external: "yes"
kolla_copy_ca_into_containers: "yes"
```

### 1.4 inventory（节点划分）

```ini
# /etc/kolla/multinode 关键段
[control]
ctrl01
ctrl02
ctrl03

[network]
ctrl01
ctrl02
ctrl03

[compute]
cmp01
cmp02
cmp03

[monitoring]
ctrl01
ctrl02
ctrl03

[storage]            # cinder-volume / cinder-backup
ctrl01
ctrl02
ctrl03
```

### 1.5 一键部署

```bash
kolla-ansible -i /etc/kolla/multinode bootstrap-servers
kolla-ansible -i /etc/kolla/multinode prechecks
kolla-ansible -i /etc/kolla/multinode deploy
kolla-ansible -i /etc/kolla/multinode post-deploy

# 生成 openrc
source /etc/kolla/admin-openrc.sh
openstack catalog list
```

### 1.6 升级（SLURP 跨版）

```bash
# Caracal → Epoxy → Flamingo
pip install -U "kolla-ansible==19.*"
sed -i 's/2024.1/2024.2/' /etc/kolla/globals.yml
kolla-ansible -i /etc/kolla/multinode prechecks
kolla-ansible -i /etc/kolla/multinode upgrade
```

## 二、HA 架构

### 2.1 控制面 HA 全景

```
External LB / 客户端
       │
   HAProxy (3 节点) + Keepalived (VIP)
       │
   ┌───┼───────┬───────┬──────┐
   │   │       │       │      │
 Nova  Neutron Cinder Glance Heat ... (各服务多副本)
   │   │       │       │
   └───┴───┬───┴───────┘
           │
   ┌───────┴───────────┐
   │                   │
 MariaDB Galera     RabbitMQ Cluster
 (3 副本同步)       (3 副本镜像/quorum queue)
   │                   │
   └─── memcached + Redis ─┘
```

### 2.2 MariaDB Galera 注意

```
3 节点同步复制 (write set)
注意:
  - WSREP 集群完整性
  - 写性能不如单节点（适用 OLTP 中小）
  - kolla 默认配好，每月观察 wsrep_cluster_status
  - 备份: mariabackup + 定时入对象存储

调优:
  - innodb_buffer_pool_size = 60% RAM
  - innodb_log_file_size = 1G
  - wsrep_provider_options 缓冲
```

### 2.3 RabbitMQ 集群

```
模式:
  - Classic 镜像队列（旧，将弃）
  - Quorum Queue ⭐（推荐，Raft）
  - Streams（事件流）
  
kolla 默认: classic mirror，可改 quorum

注意:
  - 网络抖动会导致脑裂
  - 必须独立子网或低延迟
  - 节点 ≥ 3
  - 定时清空 stuck 队列
```

### 2.4 HAProxy / Keepalived

```
HAProxy:
  - 监听各 OpenStack API 端口 (5000/8774/9696/...)
  - mode tcp 或 http
  - 健康检查 /healthcheck
  
Keepalived:
  - VRRP VIP 浮动
  - 3 节点 priority 100/99/98
  
建议:
  - 内外 VIP 分开
  - TLS 终结在 HAProxy
  - 外部加 F5 / Octavia / 国产 LB 兜底
```

## 三、Neutron OVN 深度

### 3.1 为什么 OVN

```
传统 ML2+OVS:
  - L3-agent 单点 (DVR 复杂)
  - 控制面靠 RPC，规模差
  - Iptables 性能跳水
  
OVN (Open Virtual Network):
  - OVS 上的分布式 SDN 控制器
  - 北向 (OVN-NB) + 南向 (OVN-SB) DB
  - 分布式 L3 + 分布式 NAT
  - 性能/规模/可观测 显著好
  - 与 K8s ovn-kubernetes 共享栈
  
2026 主流推荐: 一律 OVN
```

### 3.2 关键操作

```bash
# 看 OVN 数据库
ovn-nbctl show
ovn-sbctl show
ovn-sbctl list chassis

# Logical Switch / Router
ovn-nbctl ls-list
ovn-nbctl lr-list

# 排查
ovn-trace --detailed --ovs ls-int 'inport=="lsp1" && eth.src==... && ip.dst==..'
ovs-appctl ofproto/trace br-int in_port=...
ovn-appctl -t ovn-controller list-commands
```

### 3.3 网络类型

```
Provider Network (扁平 / VLAN)
  - 直接对接物理网络
  - 一般给 admin/ops 用
  - 高性能、低开销

Self-service (VXLAN / Geneve)
  - 租户隔离
  - Geneve ⭐ 主流（OVN 默认）
  - 跨节点 overlay

External Network
  - 浮动 IP / SNAT 出口
  - 一般对接公网或 DMZ
```

### 3.4 浮动 IP / NAT / SecurityGroup

```bash
# 浮动 IP
openstack floating ip create ext-net
openstack server add floating ip vm01 10.2.0.100

# 安全组
openstack security group create web
openstack security group rule create --proto tcp --dst-port 80 web
openstack server add security group vm01 web

# SNAT
# 在 router 启用 SNAT (默认开)
openstack router set --external-gateway ext-net r1

# DVR (Distributed Virtual Router)
# OVN 默认每个节点都做 L3 → 走 DVR
```

## 四、Cinder + Ceph 整合

### 4.1 Ceph 集群（前置）

```bash
# cephadm 部署（详见 09_中间件 或 Ceph 章节）
ceph osd pool create images 32 32
ceph osd pool create volumes 64 64
ceph osd pool create vms 64 64
ceph osd pool create backups 32 32

rbd pool init images
rbd pool init volumes
rbd pool init vms

# 创建用户
ceph auth get-or-create client.glance \
  mon 'profile rbd' osd 'profile rbd pool=images' > /etc/ceph/ceph.client.glance.keyring
ceph auth get-or-create client.cinder \
  mon 'profile rbd' osd 'profile rbd pool=volumes,profile rbd pool=vms,profile rbd-read-only pool=images' \
  > /etc/ceph/ceph.client.cinder.keyring
ceph auth get-or-create client.nova \
  mon 'profile rbd' osd 'profile rbd pool=vms' > /etc/ceph/ceph.client.nova.keyring
```

### 4.2 kolla 配置 Ceph

```yaml
# /etc/kolla/globals.yml
enable_ceph: "no"
glance_backend_ceph: "yes"
cinder_backend_ceph: "yes"
nova_backend_ceph: "yes"
nova_libvirt_disk_cachemodes: '"network=writeback,block=none"'

ceph_glance_user: "glance"
ceph_glance_pool_name: "images"

ceph_cinder_user: "cinder"
ceph_cinder_pool_name: "volumes"
ceph_cinder_backup_user: "cinder-backup"
ceph_cinder_backup_pool_name: "backups"

ceph_nova_user: "cinder"
ceph_nova_pool_name: "vms"

# 把 ceph.conf 和 keyring 放到部署节点
mkdir -p /etc/kolla/config/{glance,cinder,nova}
# 拷贝 ceph.conf + keyring 进去
kolla-ansible -i multinode reconfigure -t glance,cinder,nova
```

### 4.3 卷类型 / 多 backend

```bash
# 卷类型
openstack volume type create ceph-ssd
openstack volume type set --property volume_backend_name=ceph-ssd ceph-ssd
openstack volume type create ceph-hdd
openstack volume type set --property volume_backend_name=ceph-hdd ceph-hdd

# cinder.conf
[ceph-ssd]
volume_driver = cinder.volume.drivers.rbd.RBDDriver
rbd_pool = volumes-ssd
rbd_user = cinder
volume_backend_name = ceph-ssd

[ceph-hdd]
volume_driver = cinder.volume.drivers.rbd.RBDDriver
rbd_pool = volumes-hdd
rbd_user = cinder
volume_backend_name = ceph-hdd
```

### 4.4 SAN / 国产存储

```
Cinder 支持 200+ 驱动:
  华为 OceanStor (Dorado/V6)
  浪潮 AS / HS
  同有 / 杉岩 / 中科曙光
  HPE 3PAR / Nimble
  Pure Storage
  Dell EMC PowerStore
  NetApp ONTAP

配置:
  /etc/cinder/cinder.conf 加 [backend-name] 段
  enabled_backends = ceph-ssd,huawei-dorado,...
```

## 五、Octavia (LBaaS)

### 5.1 架构

```
用户创建 LB
  → Octavia API
  → 起一台 Amphora VM (HAProxy/Keepalived)
  → Amphora 给租户提供 LB 服务
  → 健康检查 / SSL / L4-L7
  
变体:
  - 单 Amphora
  - Active-Standby (HA)
  - OVN-Octavia (轻量，eBPF 数据面)
```

### 5.2 实战

```bash
openstack loadbalancer create --name lb01 --vip-subnet-id int-subnet
openstack loadbalancer listener create --protocol HTTP --protocol-port 80 \
  --name lst01 lb01
openstack loadbalancer pool create --listener lst01 --lb-algorithm ROUND_ROBIN \
  --protocol HTTP --name pool01
openstack loadbalancer member create --subnet-id int-subnet \
  --address 10.0.0.10 --protocol-port 80 pool01
openstack loadbalancer healthmonitor create --delay 5 --timeout 3 \
  --max-retries 3 --type HTTP --url-path /health pool01

# 浮动 IP
openstack floating ip create ext-net --port <lb-vip-port>
```

## 六、Magnum (K8s 即服务)

### 6.1 模板与集群

```bash
# 模板
openstack coe cluster template create k8s-1.30 \
  --image fedora-coreos-39 \
  --keypair mykey \
  --external-network ext-net \
  --master-flavor m1.medium \
  --flavor m1.large \
  --coe kubernetes \
  --network-driver calico \
  --docker-volume-size 50

# 集群
openstack coe cluster create my-k8s \
  --cluster-template k8s-1.30 \
  --master-count 3 \
  --node-count 5

# kubeconfig
openstack coe cluster config my-k8s
export KUBECONFIG=$PWD/config
kubectl get nodes
```

### 6.2 适用 / 替代

```
适合: 在 OpenStack 上自服务 K8s
对比:
  - Cluster API (更现代，主流)
  - Rancher / OKD / 阿里 ACK 私有版
2026 趋势: Cluster API + OpenStack provider 渐进取代 Magnum
```

## 七、Ironic（裸金属）

### 7.1 用途

```
- 物理机即服务（按需 PXE 装机）
- HPC / 数据库 / GPU 训练
- K8s 物理节点池
- 国产 ARM/海光 物理机交付
```

### 7.2 部署模式

```
Conductor + iPXE + IPA (Ironic Python Agent)
        │
        ▼
   PXE / iLO / iDRAC / IPMI / Redfish 控制开关机
        │
        ▼
   IPA 在内存盘里抄镜像到本盘 → 重启从本盘启
```

### 7.3 注册 + 部署

```bash
openstack baremetal node create --driver redfish \
  --driver-info redfish_address=https://idrac.example.com \
  --driver-info redfish_username=root \
  --driver-info redfish_password=*** \
  --driver-info redfish_system_id=/redfish/v1/Systems/System.Embedded.1

openstack baremetal port create --node <node-id> aa:bb:cc:dd:ee:ff
openstack baremetal node set <node-id> \
  --resource-class baremetal-large \
  --property cpus=64 --property memory_mb=524288 --property local_gb=2000

openstack baremetal node manage <node-id>
openstack baremetal node provide <node-id>

# 用 Nova flavor 把 BM 当 VM 调度
openstack flavor create bm-large --ram 524288 --disk 2000 --vcpus 64
openstack flavor set bm-large --property resources:CUSTOM_BAREMETAL_LARGE=1

openstack server create --flavor bm-large --image ubuntu22.04-bm-uefi \
  --network int-net --key-name mykey bm01
```

## 八、Heat 编排深度

### 8.1 进阶模板

```yaml
heat_template_version: 2018-08-31
description: 3-tier 应用

parameters:
  image:
    type: string
    default: ubuntu-22.04
  flavor_web:
    type: string
    default: m1.small
  flavor_db:
    type: string
    default: m1.medium

resources:
  net:
    type: OS::Neutron::Net
    properties: { name: app-net }
  subnet:
    type: OS::Neutron::Subnet
    properties:
      network: { get_resource: net }
      cidr: 10.10.0.0/24
      dns_nameservers: [8.8.8.8]
  
  db:
    type: OS::Nova::Server
    properties:
      name: db01
      image: { get_param: image }
      flavor: { get_param: flavor_db }
      networks: [{ network: { get_resource: net } }]
      user_data_format: RAW
      user_data: |
        #cloud-config
        packages: [mysql-server]
  
  web_asg:
    type: OS::Heat::AutoScalingGroup
    properties:
      min_size: 2
      max_size: 5
      resource:
        type: OS::Nova::Server
        properties:
          name: web
          image: { get_param: image }
          flavor: { get_param: flavor_web }
          networks: [{ network: { get_resource: net } }]

outputs:
  db_ip:
    value: { get_attr: [db, first_address] }
```

### 8.2 对比 Terraform

| 维度 | Heat | Terraform |
|:---|:---|:---|
| 多云 | OpenStack 专属 | 多云 ⭐ |
| 状态 | 服务端 | 客户端 (state) |
| 生态 | OpenStack 内部 | 全行业 ⭐ |
| 编排 | 强（含自动伸缩） | 强 |

推荐：**Terraform 做日常 IaC，Heat 保留特殊编排（如 ASG 与 Ceilometer 联动）**。

## 九、Designate (DNS)

```bash
# zone
openstack zone create --email admin@example.com example.com.
openstack recordset create example.com. www --type A --record 10.0.0.10

# Nova 自动注册
[nova.conf]
notify_on_state_change = vm_state
[notifications]
notification_format = both

# Designate sink 监听 Nova 事件 → 自动创/删 A 记录
```

## 十、Barbican（密钥管理）

```bash
# 用途: TLS 证书 / 加密卷密钥 / SSH 密钥
openstack secret store --name web-tls --payload-content-type 'application/octet-stream' \
  --payload "$(cat /path/cert.pem)"

# 与 Cinder 加密卷
openstack volume type create encrypted
openstack volume type set encrypted \
  --encryption-provider luks \
  --encryption-cipher aes-xts-plain64 \
  --encryption-key-size 256 \
  --encryption-control-location front-end
```

## 十一、监控与可观测

### 11.1 监控栈

```
Prometheus + Grafana 主力
  - openstack-exporter           ⭐
  - libvirt_exporter
  - rabbitmq_exporter
  - mariadb_exporter
  - node_exporter
  - haproxy_exporter
  - ceph_exporter
  - ovn_exporter

集成 SkyLine (新 UI 取代 Horizon)
集成 OpenStack Watcher (资源优化建议)

国产:
  夜莺 Nightingale + categraf
  阿里云 ARMS
```

### 11.2 关键告警

```yaml
# 控制节点 API 失败率
- alert: APIErrorRate
  expr: rate(openstack_api_errors_total[5m]) > 0.5
  for: 5m

# RabbitMQ 队列堆积
- alert: RabbitMQQueueLong
  expr: rabbitmq_queue_messages > 5000
  for: 10m

# MariaDB Galera 集群不健康
- alert: GaleraClusterUnhealthy
  expr: mysql_global_status_wsrep_cluster_size < 3
  for: 5m

# Compute node down
- alert: NovaComputeDown
  expr: openstack_nova_agent_state{service='nova-compute'} == 0
  for: 5m

# Hypervisor 资源
- alert: HypervisorMemFull
  expr: openstack_nova_memory_used_bytes / openstack_nova_memory_available_bytes > 0.9
  for: 10m

# Volume backup 失败
- alert: CinderBackupFailed
  expr: openstack_cinder_backups_status{status='error'} > 0
```

### 11.3 日志

```
集中: Fluentd / Vector → ELK / Loki

关键日志:
  /var/log/kolla/<service>/*.log    每组件
  
查日志:
  kollacli logs <service>           或 docker logs <container>
  journalctl -u <service>           物理机方式
```

## 十二、配额与多租户

### 12.1 配额（Quota）

```bash
# 看
openstack quota show <project>

# 改
openstack quota set --instances 50 --cores 200 --ram 409600 \
  --volumes 100 --gigabytes 5000 \
  --floating-ips 20 --networks 10 --subnets 20 --ports 200 \
  --secgroup-rules 200 --security-groups 50 \
  <project>

# Cinder 多 backend 配额
openstack quota set --volume-type ceph-ssd --volumes 30 <project>
```

### 12.2 域 / 项目 / 用户

```bash
openstack domain create dept-a
openstack project create --domain dept-a finance
openstack user create --domain dept-a --password-prompt alice
openstack role add --project finance --user alice member

# 自助 RC
cat > alice-openrc.sh <<EOF
export OS_AUTH_URL=https://api.example.com:5000/v3
export OS_USERNAME=alice
export OS_PASSWORD=***
export OS_PROJECT_NAME=finance
export OS_USER_DOMAIN_NAME=dept-a
export OS_PROJECT_DOMAIN_NAME=dept-a
export OS_IDENTITY_API_VERSION=3
EOF
```

### 12.3 RBAC 自定义

```bash
# policy.yaml (覆盖默认 policy.json)
# 例: 允许 finance 项目的某角色看所有 server
"os_compute_api:servers:index:get_all_tenants": "role:finance_admin"

# 放到 /etc/<service>/policy.yaml
# kolla reconfigure 生效
```

### 12.4 SSO / LDAP

```
Keystone 后端联邦:
  - LDAP / AD
  - SAML 2.0 (Shibboleth / mod_auth_mellon)
  - OIDC (mod_auth_openidc + Keycloak)
  
# /etc/keystone/keystone.conf
[identity]
driver = ldap

[ldap]
url = ldap://ldap.example.com
user = cn=admin,dc=example,dc=com
password = ***
suffix = dc=example,dc=com
user_tree_dn = ou=users,dc=example,dc=com
```

国产: 接 Keycloak / 北森 / 网易瀚海 / OneLogin / 飞书 SSO。

## 十三、备份策略

```
- DB:        mariabackup 每日 + binlog 15 分钟
- 配置:      /etc/kolla 入 Git
- 卷:        Cinder backup → Ceph backups pool → S3 异地
- 镜像:      Glance + Ceph，多副本，离线快照
- 控制平面: kolla container 配置入 Git + reconfigure 重建
- 监控数据:  Prometheus + Thanos / VictoriaMetrics 长期留存
```

## 十四、典型坑（进阶）

| 坑 | 建议 |
|:---|:---|
| **kolla 单 inventory 跑 controller+compute** | 角色拆分清晰 |
| **Galera 网络抖断** | 心跳网独立 + 低延迟 |
| **RabbitMQ 内存 oom** | quorum queue + 设 max-length |
| **OVN-NB 数据库膨胀** | 监控 + 定期 compact |
| **Cinder Ceph 没分 SSD/HDD pool** | 多 backend 起步 |
| **Glance 直接装本地 file** | 一律 Ceph RBD |
| **没装 Octavia 用 LVS 兜底** | 至少把 API 走 HAProxy |
| **Magnum + K8s 老版本** | 用 Cluster API 替代 |
| **Ironic 不上 Redfish** | 老 IPMI 性能/可靠差 |
| **配额没规划** | 提前给域/项目分配 |
| **没监控 RabbitMQ / Galera** | 必要告警 |
| **升级跳跃过版本** | 走 SLURP LTS |

## 十五、进阶 Checklist

```
HA:
☐ 控制节点 ≥ 3
☐ MariaDB Galera + 同步
☐ RabbitMQ Quorum Queue
☐ HAProxy + Keepalived VIP
☐ TLS 内外双向

网络:
☐ OVN 数据面
☐ self-service + provider network 并存
☐ Octavia LBaaS
☐ Designate DNS

存储:
☐ Cinder + Ceph 多 backend
☐ Glance / Nova / Cinder 都 RBD
☐ 备份独立 pool

服务:
☐ Magnum 或 Cluster API
☐ Ironic 已注册物理机
☐ Heat / Terraform 至少一项
☐ Barbican 加密卷 / TLS

运维:
☐ Skyline + Horizon 双 UI
☐ Prometheus + 关键告警
☐ 集中日志
☐ 配额 + RBAC + SSO
☐ DB / 卷 / 配置 备份
☐ SLURP LTS 升级演练
```

## 十六、推荐栈

```
部署:        Kolla-Ansible ⭐ / TripleO (RH 系) / OpenStack-Ansible
HA:         MariaDB Galera + RabbitMQ + HAProxy + Keepalived
SDN:        OVN ⭐
存储:        Ceph (Glance/Cinder/Nova) + 国产 SAN (混合)
LB:         Octavia + Amphora
K8s:        Magnum (老) / Cluster API (新) ⭐
裸金属:      Ironic + Redfish + IPA
编排:        Heat (内部) + Terraform (跨云) ⭐
UI:         Skyline ⭐ + Horizon
监控:        Prometheus + Grafana + openstack-exporter + 夜莺
日志:        Fluentd / Vector + Loki / ELK
SSO:        Keycloak / LDAP / 飞书
备份:        mariabackup + Cinder backup + Velero (K8s 工作负载)
```

## 十七、学习路径

```
进阶（6-12 月）:
  1. Kolla-Ansible 多节点装满
  2. MariaDB Galera + RabbitMQ Quorum HA
  3. OVN 落地 + 排障 (ovn-trace)
  4. Cinder + Ceph 多 backend
  5. Octavia + 自服务 LB
  6. Magnum 或 Cluster API
  7. Ironic 上 5 台物理机
  8. Heat + Terraform 整合
  9. Skyline + Prometheus 监控
  10. SLURP 升级演练
  
团队工程化:
  11. 全栈 Git 化 / IaC 化
  12. SSO 接入 (Keycloak)
  13. 多租户配额自服务流程
  14. 备份恢复演练
  15. 国产化适配 (鲲鹏 / 海光 / GaussDB / OceanStor)
```

> 📖 **核心判断**：进阶 = **Kolla-Ansible 多节点 + HA 全栈(Galera/RabbitMQ/HAProxy) + OVN + Cinder+Ceph + Octavia + Magnum/Ironic + Heat/Terraform + Skyline+Prometheus**。能搭出"3 控制+5 计算+3 存储"完整集群、能用 OVN 排障、能用 Heat+Terraform 一键起 3-tier 栈、能跑通 SLURP 升级演练，就具备私有云平台运维资格。**OVN + Ceph + Kolla + Terraform** 是 2026 主流四件套，往这上聚焦。
