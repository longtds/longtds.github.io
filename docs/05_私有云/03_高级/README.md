# 高级

> 私有云高级 = **大规模部署(Cells V2/Region/AZ) + NFV+DPDK+SR-IOV 数据面 + GPU/裸金属 多租户 + Ceph 极致调优 + 多集群联邦(Edge/Cluster API) + 私有云 + K8s 共生 + 机密计算 + GitOps OpenStack + LLM-OPS + 国产化深度**。本章面向需要支撑 1000+ 节点、运营商级 NFV、AI 训练云、信创主权云的高级工程师。

## 一、大规模部署：Cells V2 + Region + AZ

### 1.1 三级层次

```
Region          地理区域（北京/上海/广州）独立 Keystone/Glance/Cinder/...
  │
  ├─ AZ         机房 / 故障域 (az1, az2, az3) - 跨 AZ HA
  │
  └─ Cells V2   Nova 子集（多 cell 1 region） - 单 Nova-API 管 10w VM
```

### 1.2 Cells V2 架构

```
nova-api (top)
   │
   ├─ super-conductor (cell0 / cellN)
   │
   ├─ cell0  失败节点/调度失败 VM
   ├─ cell1  10000 VM
   ├─ cell2  10000 VM
   ├─ cellN  ...

每个 cell:
  - 独立 MySQL DB
  - 独立 RabbitMQ
  - N x nova-compute
  
收益:
  - 单 region 支撑 10w+ VM
  - 故障爆炸半径限单 cell
  - DB / MQ 性能可控
  
代表:
  AT&T / Verizon / 阿里 / 中国电信 cBSS
```

### 1.3 Placement Service

```
Placement = 资源调度数据库
特性:
  - Resource Provider 模型
  - Inventory / Allocation / Trait
  - 支撑 NUMA / PCI / VGPU / SR-IOV 复杂调度
  
查看:
  openstack resource provider list
  openstack resource provider inventory list <id>
  openstack allocation candidate list --resource VCPU=2

调优大集群:
  - placement-api 多副本
  - DB 分库 (per cell)
  - 缓存（Aggregate filter / Trait filter）
```

## 二、NFV / DPDK / SR-IOV 数据面

### 2.1 场景

```
- 5G UPF / vBNG / vCPE / vRouter
- VNF (Virtual Network Function)
- 高吞吐 LB / FW
- 工业边缘
```

### 2.2 OVS-DPDK

```bash
# nova-compute 节点
# Kolla globals.yml
enable_ovs_dpdk: "yes"
ovs_datapath: "netdev"
tunnel_interface: "dpdk0"
dpdk_ports: ["dpdk0", "dpdk1"]
ovs_dpdk_socket_memory: "1024,1024"
ovs_dpdk_pmd_cpu_mask: "0xC0"        # PMD 绑定 CPU
ovs_dpdk_lcore_mask: "0x01"

# HugePage
vm.nr_hugepages = 32768

# VM XML
<memoryBacking><hugepages><page size='1' unit='GiB'/></hugepages></memoryBacking>
<interface type='vhostuser'>
  <source type='unix' path='/var/run/openvswitch/vhuxxx' mode='client'/>
  <model type='virtio'/>
  <driver queues='4'/>
</interface>
```

### 2.3 SR-IOV with Nova

```bash
# 编译/加载 vfio + 网卡 sriov

# nova-compute /etc/nova/nova.conf
[pci]
passthrough_whitelist = [{"devname":"eth1","physical_network":"physnet1"}]

# Neutron sriov-agent
[ml2_sriov]
agent_required = True

# 创建 flavor
openstack flavor set m1.sriov \
  --property "hw:numa_nodes=1" \
  --property "hw:cpu_policy=dedicated" \
  --property "hw:mem_page_size=large"

# port
openstack port create --network sriov-net \
  --vnic-type direct sr-port01

# 启 VM
openstack server create --flavor m1.sriov \
  --image ubuntu \
  --port sr-port01 vm-sriov
```

### 2.4 vhost-user (DPDK app)

```
适合:
  - 客户 VM 自己跑 DPDK (5G UPF / VPP / Pktgen)
  - OVS-DPDK <-> Guest DPDK 零拷贝

关键:
  - cpu pinning + huge page
  - NUMA 对齐
  - pmd_cpu_mask 精准
  - 不能 live migrate (受限)
```

## 三、GPU 调度（AI 私有云）

### 3.1 PCI 直通

```bash
# /etc/nova/nova.conf
[pci]
passthrough_whitelist = [{"vendor_id":"10de","product_id":"2330"}]
alias = [{"name":"H100","vendor_id":"10de","product_id":"2330"}]

# Flavor
openstack flavor set gpu-h100 --property "pci_passthrough:alias"="H100:1"

# 启动
openstack server create --flavor gpu-h100 --image ubuntu-cuda gpu-vm01
```

### 3.2 vGPU / MIG

```bash
# Host: 设置 mdev (vGPU)
# /etc/nova/nova.conf
[devices]
enabled_vgpu_types = nvidia-558       # H100 7 切片 1g.10gb

# 或 MIG
# nvidia-smi mig -cgi 9,9,9 -C  → 3 个 2g.20gb 实例
# Nova 通过 mdev type 自动识别

# Flavor
openstack flavor set gpu-mig-1g \
  --property "resources:VGPU=1" \
  --property "resources:VGPU_DISPLAY_HEAD=0"

# 国产
昇腾 910B / 摩尔 S4000 / 沐曦 MXC500
  → 各厂 plugin / 与 Cyborg 整合
```

### 3.3 Cyborg（加速器框架）

```
Cyborg = Accelerator Service
管理:
  - GPU / FPGA / SmartNIC / NPU
  - 与 Nova/Placement 集成
  - 申请 / 释放 / 配额

应用:
  - 部分国产 NPU 集成
  - 多型号混部
```

## 四、Ceph 极致调优（私有云存储面核心）

### 4.1 集群基线

```
节点:    至少 5 OSD 主机
副本:    3 副本 (生产), 或 EC 4+2 (大集群)
网络:    25/100G 双网 (public + cluster)
盘:      Bluestore + NVMe (DB+WAL on SSD)
CPU:    每 OSD 2-4 vCPU
内存:    每 TB OSD 1 GB RAM
```

### 4.2 调优要点

```ini
# ceph.conf
[global]
osd_memory_target = 6442450944        # 6 GB per OSD
osd_op_num_threads_per_shard_hdd = 1
osd_op_num_threads_per_shard_ssd = 2

[osd]
bluestore_cache_size_ssd = 4G
bluestore_cache_size_hdd = 2G
bluestore_min_alloc_size_ssd = 4096

# CRUSH 故障域
ceph osd crush move osd.0 host=ceph01 rack=rack1
ceph osd crush rule create-replicated rack-rule default rack
```

### 4.3 RBD 性能

```bash
# 卷 image features
rbd feature disable volumes/vol01 object-map fast-diff deep-flatten

# 客户端 cache
[client]
rbd_cache = true
rbd_cache_writethrough_until_flush = true
rbd_cache_size = 64M
rbd_cache_target_dirty = 32M

# QEMU 端
<driver name='qemu' type='raw' cache='writeback' io='native' discard='unmap'/>
```

### 4.4 监控

```
ceph_exporter
ceph -s          (集群状态)
ceph osd df tree
ceph pg dump
rados bench -p volumes 60 write -t 16 -b 4096
```

## 五、多 Region / 多集群联邦

### 5.1 Region 同步

```
Keystone:  多 Region 共享一个 Keystone (Federation) 或独立
Glance:    主 Region 上传，其他 Region 同步 (rbd mirror / object replication)
Cinder:    跨 Region 不互通（每 Region 独立 Ceph）
Swift:     跨 Region 副本

操作:
  --os-region-name beijing
  --os-region-name shanghai
```

### 5.2 Cluster API + OpenStack provider

```
Cluster API (CAPI):
  K8s 上声明式管理 K8s 集群
  CAPI-openstack provider:
    通过 Nova/Neutron 自动创建 worker
    
未来替代 Magnum
```

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata: { name: prod, namespace: capi }
spec:
  infrastructureRef:
    kind: OpenStackCluster
    name: prod
  controlPlaneRef:
    kind: KubeadmControlPlane
    name: prod-cp
---
apiVersion: infrastructure.cluster.x-k8s.io/v1alpha7
kind: OpenStackCluster
metadata: { name: prod }
spec:
  cloudName: openstack
  identityRef: { name: openstack-creds, kind: Secret }
  externalNetwork: { id: <ext-net-id> }
```

### 5.3 边缘云

```
方案:
  StarlingX           Intel/Wind River，OpenStack + K8s 边缘
  MicroStack          Canonical 轻量 OpenStack
  OpenShift Edge
  KubeEdge / OpenYurt (云边协同) (见 07_K8s)
  
场景:
  - 5G CRAN/DU 边缘机房
  - 工厂 / 园区 / 高速 / 港口
  - 国产化优先 (华为 IES / 阿里 ENS / 火山引擎边缘云)
```

## 六、私有云 + K8s 共生

### 6.1 K8s 跑在 OpenStack 上

```
方式 A: Magnum (老)
方式 B: Cluster API + OpenStack provider ⭐ (推荐)
方式 C: 自定义 + Terraform + Kubeadm
方式 D: Rancher RKE2 部署在 OpenStack VM

关键:
  - Cinder CSI (PV 用 Cinder 卷)
  - OpenStack Octavia LBaaS (K8s Service LB)
  - OpenStack External Cloud Provider (节点 IP/Subnet)
  - Designate (DNS)
```

### 6.2 K8s 提供 OpenStack 控制面

```
OpenStack Operator (Kuryr/捕获项目):
  - OpenStack 组件作为 K8s Operator 运行
  - kolla-ansible 渐进退场
  - 升级 / 扩容 / HA 走 K8s 模式

Red Hat: OpenShift on OpenStack + Operator
SUSE Edge: K8s + KubeVirt + 部分 OpenStack
```

### 6.3 OpenStack VM 与 K8s 容器共存

```
案例:
  - 老 ERP / DB / Windows → OpenStack VM
  - 新业务 / 微服务 → K8s 容器
  - 共享: Ceph / OVN / Keystone(OIDC) / 监控
  - 网络: OVN-Kubernetes + Neutron OVN 共栈
```

## 七、机密计算（私有云级）

### 7.1 方案

```
SEV-SNP (AMD)       VM 内存加密 + 度量
TDX (Intel)         整 VM TEE
ARM CCA             早期
海光 CSV            国产 fork
SGX / TDX guest     容器/Pod 级 (Confidential Containers)
```

### 7.2 OpenStack 集成

```
# Flavor 加 extra spec
openstack flavor set conf-vm \
  --property "hw:mem_encryption=True" \
  --property "hw:firmware_type=uefi" \
  --property "hw:machine_type=q35"

# 镜像 metadata
openstack image set ubuntu-22.04-amd-sev \
  --property hw_mem_encryption=True \
  --property hw_machine_type=q35

# 节点必须 AMD EPYC + SEV/SEV-SNP 启用
```

### 7.3 场景

```
- 跨机构数据合作（医疗、金融）
- 主权云 / 跨境合规
- 机密 AI 训练 (模型/数据不泄露)
- 关基行业（电力 / 政务）
```

## 八、GitOps OpenStack

### 8.1 配置即代码

```
方案:
  - Kolla globals.yml + Ansible 入 Git
  - 自定义 config 覆盖 /etc/kolla/config/* 入 Git
  - Helm + Operator 模式 (K8s 部署 OpenStack)
  - ArgoCD 持续同步

最佳实践:
  - 每变更走 PR
  - CI 跑 kolla-ansible prechecks
  - Stage 集群灰度
  - 失败自动回滚 (Argo)
```

### 8.2 资源 IaC

```
Terraform:
  - VM / Network / Volume / LB / DNS / Stack
  - 团队 + 业务模板化
  - 接入 Vault 取密钥

Crossplane:
  - K8s CRD 管 OpenStack 资源
  - 与应用部署同栈
```

## 九、AI / LLM Ops

### 9.1 LLM 接入 OpenStack 运维

```
场景:
  - 自然语言变更（"帮我创建 3 台 16C32G VM 装 Nginx"）→ Terraform/Heat
  - 故障自动诊断（看日志/Prometheus → 给根因）
  - 容量预测 / 资源建议
  - 自动生成文档 / 工单

工具栈:
  - 私有 LLM (Qwen/DeepSeek/Llama3) on K8s + vLLM
  - LangChain / LangGraph
  - MCP / Function Calling 调 openstack CLI
  - 接 SkyLine / Watcher
```

### 9.2 AIOps（见 12_AIOps）

```
- 异常检测 (Prometheus + ML)
- 告警合并 / 根因分析
- 容量预测
- 工单自动分发
```

## 十、国产化深度

### 10.1 全栈方案样板

```
硬件:
  CPU:        鲲鹏 920 / 飞腾 S2500 / 海光 7390
  服务器:     华为 / 浪潮 / H3C / 中科曙光
  存储:       华为 OceanStor Dorado / 浪潮 AS / 同有
  网络:       华为 CE / H3C S12500 / 锐捷
  GPU:        昇腾 910B / 摩尔 S4000 / 沐曦 MXC500
  DPU:        中科驭数 K2 / 星云智联

OS / 中间件:
  OS:         openEuler 22.03/24.03 / 麒麟 V10 / UOS / Anolis
  容器 OS:    EulerOS / TencentOS / Anolis OS
  DB:        GaussDB / OceanBase / TiDB / 达梦 / 人大金仓
  消息队列:   RocketMQ / Pulsar / 国产 ActiveMQ
  
私有云:
  全栈:       华为 FusionSphere / EasyStack / 易捷行云 / 九州云
  开源:       ZStack / Kolla-Ansible + 国产 OS
  HCI:        深信服 / SmartX / 浪潮
  K8s:        KubeSphere / 华为 CCE / 阿里 ACK / 腾讯 TKEStack

加密:
  TLS:        Tongsuo (铜锁) / GmSSL
  KMS:        阿里 KMS / 华为 DEW / 国产 HSM
  
监控 / 运维:
  夜莺 / 阿里 ARMS / 华为 AOM
  鼎甲 / Vinchin 备份
```

### 10.2 等保 / 关基 / 数据安全法

```
☐ 等保 2.0 三级 (默认) / 四级 (关基)
☐ 关基保护条例
☐ 数据安全法 / 个保法
☐ 网络安全审查
☐ 国测中心 / 公安部测评
☐ 行业准入 (金融 / 电信 / 能源)
```

### 10.3 主权云 / 跨境

```
案例:
  - 阿里 / 华为为政府建主权云
  - 出海跨境合规（GDPR / SCC）
  - 与境外合作的"数据飞地"
关键技术:
  - 数据本地化
  - 机密计算
  - 跨境 VPN / 专线
```

## 十一、典型生产架构（参考）

### 11.1 大型国企信创私有云

```
- 3 控制 + 3 网络 + 3 存储 + 200 计算 + 20 GPU + 30 BM
- Kolla-Ansible (Caracal/Epoxy) + OVN + Ceph 主用 + 国产 SAN 灾备
- 信创全栈 (鲲鹏/海光 + openEuler + GaussDB)
- 海光 CSV 机密 VM 选项
- Cluster API + KubeSphere 自服务 K8s
- Skyline + Prometheus + 夜莺
- Vinchin / 爱数 备份 + 异地 S3
- Keycloak SSO + LDAP
```

### 11.2 运营商 NFV

```
- StarlingX / OpenStack 边缘
- DPDK + SR-IOV 数据面
- Cells V2 多 cell
- Tacker / NFVO
- 5G UPF / vBNG / vCPE VNF
- 国产网络硬件 (华为 / 中兴)
```

### 11.3 AI 训练云

```
- 200 节点 H100 + 100 节点 910B
- PCI 直通 + MIG + 国产 vGPU
- RoCE/IB + Spine-Leaf
- Cyborg + Cluster API + KubeVirt
- Cinder + Ceph (训练数据 lake)
- 多租户 + 配额 + 机密计算
- LLM-Ops 接入
```

### 11.4 金融私有云

```
- 同城双活 + 异地灾备 (RPO 0 / RTO 5min)
- Stretched Ceph / DRBD / SRM
- 国密 + Tongsuo
- 等保四级 + 关基
- 信创全栈 (海光/鲲鹏 + 麒麟 + OceanBase)
- 机密计算 (跨机构联合反欺诈)
- 持续合规扫描 (CIS / 国密合规)
```

## 十二、典型坑（高级）

| 坑 | 建议 |
|:---|:---|
| **单 region 跑 10w VM** | 上 Cells V2 |
| **DPDK 上跑普通负载** | 仅 NFV / 高速业务用 |
| **GPU 直通做不了热迁移** | 训练任务设计预案 |
| **Ceph 副本 < 3** | 至少 3 |
| **CRUSH 故障域弱** | 至少 rack / host |
| **Magnum 老 K8s** | 切 Cluster API |
| **边缘节点跑全 OpenStack** | 走 StarlingX / 轻量 |
| **机密计算没度量** | SEV-SNP 必须 attestation |
| **GitOps 不闭环** | 必须 ArgoCD/Flux 持续同步 |
| **信创没提前压测** | 上线前 3-6 月联调 |
| **没监控 OVN/Ceph** | 必要告警 |

## 十三、高级 Checklist

```
规模:
☐ Cells V2 / 多 Region
☐ Placement 多副本
☐ 网络分流 mgmt/tunnel/ext/storage/bmc

数据面:
☐ OVS-DPDK / SR-IOV 一种
☐ NUMA / HugePage / CPU pinning

AI:
☐ GPU 直通 / vGPU / MIG
☐ Cyborg 或国产 plugin
☐ Cluster API + KubeVirt

存储:
☐ Ceph 调优 + EC 池
☐ Cinder 多 backend (SSD/HDD/SAN)
☐ Glance/Nova/Cinder 全 RBD

K8s 共生:
☐ Cluster API + OS provider
☐ Cinder CSI + Octavia LB
☐ OpenShift / KubeSphere 选型

机密:
☐ SEV-SNP / TDX / 海光 CSV 试点
☐ Attestation + KMS

GitOps:
☐ Kolla 配置入 Git
☐ Terraform 资源 IaC
☐ ArgoCD/Flux 持续同步

国产化:
☐ 鲲鹏/海光 验证
☐ openEuler/麒麟 接管
☐ GaussDB/OceanBase 适配
☐ 国密 / 等保 / 关基
☐ 主权云方案
```

## 十四、参考资料

```
官方:
  docs.openstack.org ⭐
  releases.openstack.org (版本)
  docs.openshift.com (RH 系)
  
中文:
  EasyStack / ZStack / 华为云 / 阿里云白皮书
  CSDN OpenStack
  云原生社区
  openEuler / 龙蜥 SIG

经典:
  - 《OpenStack 设计与实现》英特尔团队
  - 《Mastering OpenStack》Packt
  - Cells V2 deep dive (Open Infrastructure Summit)
  - Ceph: The Definitive Guide

会议:
  - Open Infrastructure Summit
  - KubeCon (Cluster API track)
  - OpenStack PTG (社区双月)
```

> 📖 **核心判断**：高级 = **Cells V2 + Region/AZ + OVN-DPDK/SR-IOV + GPU 直通+MIG/Cyborg + Ceph 调优 + Cluster API + 机密计算 + GitOps + 国产化全栈**。能在白板上画 5000 节点 + 10w VM 架构、能跑通"NFV+DPDK+SR-IOV+CPU pinning"全链、能搭出"信创+机密计算+GitOps"主权云、能让 OpenStack 与 K8s 在同一集群优雅共生，就具备私有云架构师能力。**OpenStack 不是过时，而是回归本质**：当 K8s 不能管 VM/裸金属/电信级网络时，OpenStack 仍是答案，且越来越被国产化主权云需要。
