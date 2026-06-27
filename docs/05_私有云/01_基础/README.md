# 基础

> 私有云基础 = **公私混合云概念 + IaaS/PaaS/SaaS 分层 + 主流私有云方案选型 + OpenStack 全家桶认知 + Nova/Neutron/Cinder/Keystone/Glance 五大核心组件 + 单节点 DevStack/PackStack 上手 + 国产化全景**。本章面向新手和入职 1 年内的工程师，先认清"私有云不是装一堆 VM 就完了"。

## 一、云计算分类

### 1.1 部署模型

```
公有云 (Public Cloud)
  AWS / Azure / GCP / 阿里 / 腾讯 / 华为 / 火山
  按需付费、共享
  
私有云 (Private Cloud) ⭐ (本章重点)
  企业自建（IDC 或托管）
  独占、合规、可控
  
混合云 (Hybrid Cloud)
  公私结合 + 数据跨界
  应对突发流量 / 备份 / 灾备 / 信创
  
社区云 (Community Cloud)
  行业/政府专属共享 (政务云、金融云、教育云)
  
分布式云 / 边缘云
  公有云在客户机房延伸
  AWS Outposts / Azure Stack / 阿里 ECS Edge / 华为 IES
```

### 1.2 服务模型

```
SaaS    软件即服务      用户用应用 (Office 365, Salesforce, 钉钉)
PaaS    平台即服务      用户开发应用 (K8s, Heroku, 阿里云 EDAS)
IaaS    基础设施服务    用户用 VM/网络/存储 (EC2, ECS, OpenStack Nova)
FaaS    函数即服务      事件驱动 (Lambda, FC, K-native)
BaaS    后端即服务      DB/Auth/Storage (Firebase)
CaaS    容器即服务      K8s/容器 (ACK, TKE, EKS)
```

### 1.3 私有云 vs 公有云

| 维度 | 私有云 | 公有云 |
|:---|:---|:---|
| 控制权 | 强 ⭐ | 弱 |
| 合规 | 易等保/国密 | 看厂商 |
| 成本 | 前期重 | 弹性 |
| 弹性 | 受限 | 强 ⭐ |
| 运维 | 自负 | 厂商 |
| 数据主权 | 强 ⭐ | 受地域影响 |
| 信创 | 易落地 ⭐ | 看厂商 |

## 二、私有云核心能力

```
计算    VM / 裸金属 / 容器 / 函数 / GPU
存储    块存储 / 对象存储 / 文件存储 / 备份归档
网络    VLAN / VXLAN / VPC / LB / DNS / VPN / 防火墙
身份    多租户 / RBAC / SSO / MFA
镜像    模板 / 仓库 / 加密
监控    指标 / 日志 / 告警 / 拓扑
计费    资源计量 / 配额 / 工单
门户    自服务 Web UI / Open API / CLI / SDK
编排    Heat / Terraform / Helm / Ansible
合规    审计 / 加密 / 国密 / 等保
```

## 三、主流私有云平台

### 3.1 选型矩阵

| 平台 | 类型 | 商业/开源 | 适用 |
|:---|:---|:---|:---|
| **OpenStack** | IaaS | 开源 ⭐⭐⭐ | 大规模企业 / 信创 / 运营商 |
| **OpenShift / OKD** | PaaS | 商业/开源 | K8s + 应用平台 |
| **Rancher / RKE2 / k3s** | PaaS | 商业/开源 | K8s 多集群 |
| **Harvester** | HCI + K8s | 开源 ⭐ | 中小企业 K8s 化 HCI |
| **VMware vCloud / vSphere** | 全栈 | 商业 | 老企业存量 |
| **Microsoft Azure Stack** | 全栈 | 商业 | Windows 系 |
| **CloudStack** | IaaS | 开源 | 中小企业 |
| **Eucalyptus** | IaaS | 开源 | 历史 / AWS API 兼容 |
| **OpenNebula** | IaaS | 开源 | 中小 / HPC |
| **华为 FusionSphere** | 全栈 | 商业 | 国产 ⭐ |
| **深信服 EDS Cloud** | 全栈 | 商业 | 国产 |
| **浪潮 InCloud Sphere/Stack** | 全栈 | 商业 | 国产 |
| **ZStack** | IaaS | 开源 ⭐ | 国产开源 |
| **EasyStack** | OpenStack 发行 | 商业 | 信创 |
| **QingCloud / 易捷行云** | OpenStack | 商业 | 信创 |
| **SmartX** | HCI | 商业 | 国产 HCI |
| **Cloudpods / OneCloud** | 多云 | 开源 | 多云统管 |

### 3.2 选型决策

```
< 10 主机 / 学习    → Proxmox VE / Harvester / ZStack 开源
10-100 主机       → ZStack / SmartX / 深信服 EDS / OpenStack Kolla
100-1000 主机     → OpenStack (Kolla/Tripleo) / FusionSphere / EasyStack
1000+ 主机        → 自研 + OpenStack 内核 / 大厂订制
信创合规          → FusionSphere / EasyStack / ZStack / 深信服
混合云            → Cloudpods / VMware Aria / 华为 ManageOne
K8s-only          → OpenShift / Rancher / Harvester
```

## 四、OpenStack 全家桶（必学）

### 4.1 项目地图

```
计算
  Nova            VM 生命周期 (KVM/QEMU/Xen/Hyper-V)
  Ironic          裸金属
  Zun             容器（已少用）
  Magnum          K8s 集群即服务

网络
  Neutron         L2/L3/LB/FW (OVS / Linux Bridge / OVN ⭐)
  Octavia         LBaaS
  Designate       DNS
  Tacker          NFV

存储
  Cinder          块存储 (LVM/Ceph/SAN)
  Swift           对象存储
  Manila          文件 (NFS/CephFS/GlusterFS)

镜像
  Glance          镜像服务

身份
  Keystone        认证授权 / 多租户

编排 / 自动化
  Heat            CloudFormation 风格编排
  Mistral         工作流

可观测
  Ceilometer      计量
  Gnocchi         时序
  Aodh            告警
  Panko           事件 (已废)
  Watcher         资源优化
  
其他
  Horizon         Web UI ⭐
  Trove           DBaaS
  Sahara          Hadoop/Spark
  Murano          应用市场
  Senlin          集群自愈
  Vitrage         根因分析
  Cloudkitty      计费
```

### 4.2 历史版本时间线（关键节点）

```
2010-10  Austin (诞生)
2013-04  Grizzly
2015-04  Kilo
2016-10  Newton
2017-10  Pike     (重要里程碑，正式企业级)
2018-08  Rocky
2020-05  Ussuri
2021-04  Wallaby
2021-10  Xena
2022-03  Yoga      ⭐ 主流
2022-10  Zed
2023-03  Antelope  (SLURP LTS)
2023-10  Bobcat
2024-04  Caracal   (SLURP LTS)
2024-10  Dalmatian
2025-04  Epoxy
2025-10  Flamingo
2026-04  Grand Tour (规划)

SLURP = 跳跃式升级 LTS（每年一个）
```

### 4.3 五大核心组件

#### 4.3.1 Keystone（身份）

```
功能:    认证 + 授权 + Service Catalog
对象:    User / Project / Domain / Role / Token

# CLI
openstack token issue
openstack user list
openstack project list
openstack role assignment list --names

# 配置:
/etc/keystone/keystone.conf
后端: SQL / LDAP / OIDC / SAML / OAuth2
```

#### 4.3.2 Glance（镜像）

```
功能: 上传 / 管理 / 分发 VM 镜像
格式: qcow2 / raw / vmdk / iso / aki/ari/ami / ova
后端: file / Swift / Ceph RBD ⭐ / S3

# CLI
openstack image create "ubuntu-22.04" --file ubuntu.img --disk-format qcow2 \
  --container-format bare --public
openstack image list
openstack image show ubuntu-22.04
```

#### 4.3.3 Nova（计算）

```
组件:
  nova-api          API
  nova-conductor    DB 代理
  nova-scheduler    调度
  nova-compute      Hypervisor 适配 (KVM/Xen/Hyper-V/VMware/Ironic)
  nova-novncproxy   控制台

# CLI
openstack server create --flavor m1.small --image ubuntu \
  --network int-net --key-name mykey vm01
openstack server list
openstack server show vm01
openstack console url show vm01
openstack server migrate --live --block-migration vm01
```

#### 4.3.4 Neutron（网络）

```
plugin:
  OVS (传统)         ovs-agent + linuxbridge-agent
  OVN ⭐ (主流)       Open Virtual Network，云原生
  Tungsten Fabric    NFV 重型
  
驱动:
  L2: VLAN / VXLAN / GRE / Geneve
  L3: 路由器 / 浮动 IP / NAT
  服务: LBaaS / FWaaS / VPNaaS

# CLI
openstack network create int-net --provider-network-type vxlan
openstack subnet create int-subnet --network int-net --subnet-range 10.0.0.0/24
openstack router create r1
openstack router add subnet r1 int-subnet
openstack floating ip create public-net
openstack server add floating ip vm01 192.168.1.100
```

#### 4.3.5 Cinder（块存储）

```
driver:
  LVM             单机
  Ceph RBD ⭐      生产首选
  NFS             共享
  iSCSI / FC      SAN
  国产 SAN: 华为 OceanStor / 浪潮 / 同有

# CLI
openstack volume create --size 100 data01
openstack server add volume vm01 data01
openstack volume snapshot create --volume data01 snap01
openstack volume backup create data01
```

### 4.4 架构图速记

```
    User / Horizon / CLI
            │
        Keystone (Auth)
            │
   ┌────────┼──────────────────────────┐
   │        │          │       │       │
 Nova     Neutron    Cinder  Glance  Octavia
   │        │          │       │       │
 Hypervisor OVS/OVN  Ceph    Ceph    HAProxy/F5
 (KVM)
            │
       共享数据库 + 消息队列
       (MySQL HA + RabbitMQ HA)
```

## 五、单节点上手（DevStack / PackStack）

### 5.1 DevStack（开发/学习）

```bash
# Ubuntu 22.04 / CentOS Stream 9 单机
# 至少 16C 32G 200G 磁盘

useradd -s /bin/bash -d /opt/stack -m stack
echo "stack ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
su - stack

git clone https://opendev.org/openstack/devstack -b stable/2024.1
cd devstack

cat > local.conf <<EOF
[[local|localrc]]
ADMIN_PASSWORD=password
DATABASE_PASSWORD=\$ADMIN_PASSWORD
RABBIT_PASSWORD=\$ADMIN_PASSWORD
SERVICE_PASSWORD=\$ADMIN_PASSWORD

HOST_IP=192.168.1.10
FLOATING_RANGE=192.168.1.224/27

enable_plugin neutron https://opendev.org/openstack/neutron stable/2024.1
EOF

./stack.sh

# 装完: http://<HOST_IP>/dashboard 用 admin/password
```

### 5.2 PackStack（CentOS/RHEL 准生产）

```bash
# CentOS Stream 9
dnf install -y centos-release-openstack-caracal
dnf update -y
dnf install -y openstack-packstack

packstack --gen-answer-file=ans.txt
# 编辑 ans.txt (启用 Nova/Neutron/Cinder/Glance/Heat 等)
packstack --answer-file=ans.txt

# 启动后:
source /root/keystonerc_admin
openstack service list
```

### 5.3 Kolla-Ansible（生产推荐）

```bash
# 容器化部署 OpenStack（所有组件在 Docker）
pip install kolla-ansible
kolla-ansible install-deps
mkdir -p /etc/kolla
cp -r /usr/share/kolla-ansible/etc_examples/kolla/* /etc/kolla/

# 改 /etc/kolla/globals.yml + passwords.yml
kolla-genpwd

kolla-ansible -i inventory bootstrap-servers
kolla-ansible -i inventory prechecks
kolla-ansible -i inventory deploy
kolla-ansible -i inventory post-deploy

# 优点:
# - 容器化，便于升级/回滚
# - 多节点扩展性好
# - 现代主流
```

## 六、客户端工具

### 6.1 openstack CLI

```bash
# 装
pip install python-openstackclient

# 配置（admin RC）
cat > admin-openrc.sh <<EOF
export OS_AUTH_URL=http://controller:5000/v3
export OS_USERNAME=admin
export OS_PASSWORD=password
export OS_PROJECT_NAME=admin
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_DOMAIN_NAME=Default
export OS_IDENTITY_API_VERSION=3
EOF
source admin-openrc.sh

# 常用
openstack catalog list
openstack endpoint list
openstack flavor list
openstack image list
openstack server list --all-projects
openstack network list
openstack volume list
openstack quota show <project>
```

### 6.2 Horizon Web UI

```
URL: http://<controller>/dashboard
默认登录: admin / <password>

模块:
  - 项目（Compute/Network/Volumes/Orchestration）
  - Admin（System overview/Hypervisors/Quota）
  - Identity（Users/Projects/Roles）
```

### 6.3 Heat（编排）

```yaml
# stack.yaml
heat_template_version: 2018-08-31
parameters:
  flavor: { type: string, default: m1.small }
resources:
  vm01:
    type: OS::Nova::Server
    properties:
      name: vm01
      flavor: { get_param: flavor }
      image: ubuntu-22.04
      networks:
        - network: int-net
```

```bash
openstack stack create -t stack.yaml mystack
openstack stack list
openstack stack delete mystack
```

### 6.4 Terraform Provider

```hcl
terraform {
  required_providers {
    openstack = { source = "terraform-provider-openstack/openstack" }
  }
}

provider "openstack" {
  user_name   = "admin"
  password    = "password"
  auth_url    = "http://controller:5000/v3"
  region      = "RegionOne"
  user_domain_name = "Default"
  project_name     = "admin"
}

resource "openstack_compute_instance_v2" "vm01" {
  name      = "vm01"
  image_name = "ubuntu-22.04"
  flavor_name = "m1.small"
  key_pair  = "mykey"
  network { name = "int-net" }
}
```

## 七、国产化全景

### 7.1 三大梯队

```
第一梯队 (大厂全栈):
  华为 FusionSphere / FusionCloud
  深信服 EDS Cloud
  浪潮 InCloud / InCloud Stack
  阿里飞天 (公有云内核衍生)
  腾讯 TStack
  中兴 GoldenDB Cloud
  紫光华山 H3C UniCloud

第二梯队 (OpenStack 发行):
  EasyStack ⭐
  易捷行云 QingCloud
  九州云 Animbus
  云宏 CNware
  红帽 (RHOSP / OpenShift on OS)

第三梯队 (开源):
  ZStack ⭐
  Cloudpods / OneCloud (多云统管)
  开源 OpenStack (Kolla/Tripleo)
```

### 7.2 信创合规清单

```
☐ CPU 信创: 鲲鹏 / 飞腾 / 海光 / 龙芯 / 申威
☐ OS 信创: openEuler / 麒麟 / UOS / Anolis
☐ 数据库: GaussDB / OceanBase / TiDB / 达梦 / 人大金仓
☐ 中间件: 东方通 / 普元 / Apache 体系
☐ 国密: SM2/SM3/SM4 + Tongsuo
☐ 等保 2.0 三级 / 关基 / 数据安全法
☐ 测评: 国测中心 / 公安部安全测评 / CNAS
```

### 7.3 选型样板

```
党政 / 关基:        华为 FusionSphere + 鲲鹏 + openEuler + GaussDB
金融:               EasyStack + 海光 + 麒麟 + OceanBase + 国密
电信:               OpenStack 自研 + 鲲鹏/飞腾
大型央企:           ZStack 商业版 + 海光 + 信创全栈
中型企业:           深信服 EDS / SmartX / Proxmox + 国产 OS
教育 / 科研:        开源 OpenStack Kolla + 鲲鹏/海光
医疗:               华为 FusionSphere / 易捷行云
```

## 八、入门必练 20 题

```
1.  公私混合云区别？SaaS/PaaS/IaaS 各举一例
2.  OpenStack 5 个核心组件是？各管什么？
3.  Keystone 中 Domain / Project / User 关系？
4.  Glance 镜像 qcow2 与 raw 区别？
5.  Nova 调度器主要按什么排 host？
6.  Neutron 中 self-service vs provider network 区别
7.  浮动 IP (Floating IP) 工作原理
8.  Cinder 卷快照 vs 备份区别
9.  Heat / Terraform / Ansible 各擅长什么？
10. OpenStack 与 K8s 关系？
11. 一台机器装 DevStack 最低配置
12. Kolla-Ansible 比 PackStack 强在哪？
13. OVS vs OVN 区别
14. Magnum 是什么？
15. Ironic 适用什么场景？
16. SLURP LTS 是什么？
17. 一行命令创建 VM
18. 国产开源 OpenStack 替代 3 个
19. 信创合规检查清单
20. 私有云监控大盘必有的 5 个指标
```

## 九、典型坑（基础）

| 坑 | 建议 |
|:---|:---|
| **学习用 DevStack 当生产** | 生产用 Kolla-Ansible |
| **单网卡装 OpenStack** | 最少 mgmt/tunnel/external 3 网 |
| **不规划 IP 段** | 提前规划 mgmt / tenant / ext |
| **Keystone 密码裸跑** | TLS + Fernet token |
| **跨版本跳过升级** | SLURP LTS 跳跃 |
| **OVS 上生产** | 新装一律 OVN |
| **不熟 RC 文件** | source openrc 是基本功 |
| **不看 catalog** | 第一个排查动作就是 `openstack catalog list` |
| **不预留 quota** | 配额提前算 |
| **直接装最新主干** | 装稳定 LTS（Yoga/Antelope/Caracal）|

## 十、学习资源

```
官方:
  docs.openstack.org ⭐
  /etc/<service>/*.conf 注释超详细
  bug 跟踪: launchpad.net

国内:
  EasyStack 官方文档
  ZStack 官方文档 ⭐
  华为云开发者社区
  CSDN OpenStack 专题
  
书籍:
  - 《OpenStack 设计与实现》英特尔团队 ⭐
  - 《OpenStack 部署运维实战》肖力
  - 《精通 OpenStack》Packt
  - 《Kubernetes 权威指南》(配合 K8s)

视频:
  - OpenStack Summit / Open Infra Summit
  - 51CTO / 极客时间
  - B 站搜 "OpenStack 实战"
```

> 📖 **核心判断**：私有云基础 = **认清公私混合 / IaaS-PaaS-SaaS / 主流平台选型 / OpenStack 5 大组件 / 装一遍 DevStack 或 Kolla 单节点**。能在白板上画出 Keystone+Nova+Neutron+Cinder+Glance 关系、能用 CLI 一气呵成创建 VM+卷+网络+浮动 IP、能背出选型决策树，就具备私有云入门。**国产化 + 信创** 现在就要进入视野，不要等到上线才补。
