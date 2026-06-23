# 高速网络与 AI 网络

> 大模型时代，**网络是数据中心的新瓶颈**。千卡训练 30%-40% 时间花在通信上，网络拓扑、带宽、延迟直接决定 GPU 利用率。

## 一、为什么 AI 训练对网络要求极高

### 1.1 通信开销的真实情况

```
单机训练:    GPU 计算 100%, 网络 0%
多机训练:    GPU 计算 60%, AllReduce 通信 40%
            ↓
万亿参数训练:  GPU 计算 50%, 通信 50%
            ↓
            → 网络越烂，GPU 越闲，训练越慢
```

### 1.2 主流并行策略对网络的需求

| 并行方式 | 通信模式 | 带宽需求 | 延迟敏感 |
|:---|:---|:---:|:---:|
| **数据并行（DP）** | AllReduce 梯度 | 极高 | 中 |
| **张量并行（TP）** | AllReduce 激活 | 极高 | 极高 |
| **流水并行（PP）** | Send/Recv 激活 | 中 | 高 |
| **专家并行（EP）** | All-to-All（MoE） | 极高 | 高 |
| **序列并行（SP）** | AllGather/Reduce | 高 | 高 |
| **3D/4D 混合并行** | 上述全部 | 极高 | 极高 |

> 🔑 **TP 通常限制在单机 8 卡内**（必须 NVLink），**DP/PP 跨机**（IB/RoCE）。

## 二、AI 集群三套网络

```
┌─────────────────────────────────────────┐
│  计算网络 (Compute / RDMA)              │
│  ↑ GPU-GPU 通信，承载 NCCL              │
│  ↑ InfiniBand 或 RoCEv2，每 GPU 400G+   │
├─────────────────────────────────────────┤
│  存储网络 (Storage)                     │
│  ↑ GPU ↔ 并行文件系统/对象存储          │
│  ↑ 100-400G 以太网                       │
├─────────────────────────────────────────┤
│  管理网络 (Management / OOB)             │
│  ↑ SSH/监控/IPMI 带外                    │
│  ↑ 1-25G 普通以太网                      │
└─────────────────────────────────────────┘
```

### 2.1 一台 8 卡 H100 服务器的典型网卡布局

| 网卡 | 数量 | 用途 |
|:---|:---:|:---|
| ConnectX-7 (400G IB/Eth) | **8** | 计算网络，每 GPU 一张 |
| ConnectX-7/6 (100-400G ETH) | 1-2 | 存储网络 |
| 1G/10G | 1-2 | 管理网络 |
| BMC | 1 | IPMI 带外 |

> 💡 **1:1 GPU-NIC 比例** 是 H100/H200 标准；B200 集群升级到 1:1 的 800G。

## 三、RDMA 技术深入

### 3.1 RDMA 核心价值

```
传统 TCP/IP:  App → Sock → Kernel → NIC
              ↑ 多次内存拷贝、CPU 中断、上下文切换
              延迟 50-100μs，CPU 占用 30%+

RDMA:        App → NIC 直接读写远端内存
              ↑ Zero-copy + Kernel Bypass + CPU Offload
              延迟 < 2μs，CPU 占用 ~0%
```

### 3.2 RDMA 三大流派

| 方案 | 网络层 | 延迟 | 成本 | 兼容性 | 主导厂商 |
|:---|:---|:---:|:---:|:---:|:---|
| **InfiniBand** | 专用 | < 1μs | 高 | 封闭 | NVIDIA（Mellanox）|
| **RoCEv2** | 以太网 UDP | ~2μs | 中 | 标准 | 多厂商 |
| iWARP | 以太网 TCP | ~10μs | 低 | 标准 | Intel/Chelsio |

> 现在的 AI 集群基本只在 **IB vs RoCEv2** 之间选。

### 3.3 关键 RDMA 操作

| 操作 | 含义 |
|:---|:---|
| RDMA Write | 直接写远端内存 |
| RDMA Read | 直接读远端内存 |
| Send/Recv | 双边操作（两端都需参与） |
| Atomic | 远程原子操作 |

### 3.4 关键概念

| 概念 | 说明 |
|:---|:---|
| **QP（Queue Pair）** | 通信端点（发送+接收队列）|
| **MR（Memory Region）** | 注册的可被 RDMA 访问的内存 |
| **PD（Protection Domain）** | 资源隔离单位 |
| **CQ（Completion Queue）** | 完成事件队列 |
| **WQE/CQE** | 工作请求/完成条目 |

## 四、InfiniBand 详解

### 4.1 速率演进

| 代号 | 单端口带宽 | 时间 | NVIDIA 网卡 |
|:---|:---:|:---:|:---|
| FDR | 56 Gbps | 2011 | ConnectX-3 |
| EDR | 100 Gbps | 2014 | ConnectX-4 |
| HDR | 200 Gbps | 2018 | ConnectX-6 |
| **NDR** | 400 Gbps | 2021 | **ConnectX-7（H100 标配）** |
| **XDR** | 800 Gbps | 2024+ | **ConnectX-8（B200）** |
| GDR | 1.6 Tbps | 规划 | 下一代 |

### 4.2 IB 网络组件

```
GPU 服务器 → HCA（主机通道适配器，即 ConnectX）
            ↓
            IB 交换机（NVIDIA Quantum / Quantum-2 / Quantum-X）
            ↓
            Subnet Manager（OpenSM 或硬件 SM）
            ↓
            Routing: 静态/自适应/AR（NVIDIA SHARP）
```

### 4.3 IB 特有加速

| 技术 | 作用 |
|:---|:---|
| **SHARP** | 交换机内做 AllReduce，省一半带宽 |
| **Adaptive Routing** | 拥塞时自动绕路 |
| **GPUDirect RDMA** | GPU 显存 ↔ 远端 GPU 显存，跳过 CPU/内存 |

## 五、RoCEv2 详解

### 5.1 工作原理

```
原始 RDMA 包  →  UDP 封装  →  IP 路由  →  以太网传输
              ↑ 标准以太网交换机即可承载
```

### 5.2 RoCE 部署挑战（必读）

| 挑战 | 解决方案 |
|:---|:---|
| **拥塞导致丢包** | **PFC（优先级流控）** 必须启用 |
| **PFC 死锁** | 配置 PFC Watchdog + Headroom |
| **微突发拥塞** | **ECN（显式拥塞通知）** + DCQCN 算法 |
| **MTU 不一致** | 全链路 9000+ Jumbo Frame |
| **路由不对称** | 多路径要等价负载（ECMP） |
| **多租户隔离** | DSCP 标记 + 队列调度 |

> ⚠️ **"无损以太网"是 RoCE 部署的最大坑**——只要哪一台交换机配错，整个集群就性能崩溃。

### 5.3 无损以太网组合拳

```
PFC (IEEE 802.1Qbb)      → 按优先级暂停
ECN (IETF RFC 3168)      → 提前告知拥塞
DCQCN                    → 端侧拥塞控制算法
ETS                      → 带宽分配保证
```

### 5.4 IB vs RoCE 怎么选

| 维度 | InfiniBand | RoCEv2 |
|:---|:---|:---|
| **训练性能** | 极致最优 | 接近 |
| **部署难度** | 低（傻瓜化） | 高（需调优） |
| **生态** | NVIDIA 独家 | 多厂商 |
| **价格** | 高 30-50% | 中等 |
| **存储/管理网络复用** | 不能 | 可以 |
| **千卡以上** | 推荐 | 需顶级团队 |

> 💡 **经验法则**：千卡训练 → IB 省心；中小集群或推理 → RoCEv2 性价比更高。

## 六、AI 集群网络拓扑

### 6.1 Fat-Tree（胖树）

```
        Spine
       /  |  \
   Leaf  Leaf  Leaf
   /|\   /|\   /|\
  服务器们
```

- 经典对称拓扑，任意节点带宽相等
- 阻塞比 1:1（非阻塞）或 1:2（适度收敛）

### 6.2 Rail-Optimized（轨优化，AI 标准）

```
8 卡服务器:
  GPU0 → Rail 0 网卡 → Rail 0 交换机
  GPU1 → Rail 1 网卡 → Rail 1 交换机
  ...
  GPU7 → Rail 7 网卡 → Rail 7 交换机

每个 GPU 对应一条独立"轨道"，通信不会跨轨。
```

**优势**：
- 减少跨交换机跳数
- 同号 GPU 间通信延迟最低（NCCL Ring/Tree 受益）
- 故障域隔离

> 现在万卡集群几乎全用 Rail-Optimized。

### 6.3 DragonFly+ / 3D-Torus（超大规模）

| 拓扑 | 适用 | 缺点 |
|:---|:---|:---|
| Fat-Tree | 4K 卡内 | 交换机数量爆炸 |
| Rail-Optimized | 万卡 | 设计严格 |
| DragonFly+ | 数万卡 | 路由复杂 |
| 3D-Torus | TPU 集群 | NVIDIA 不用 |

## 七、NCCL（GPU 间通信库）

### 7.1 NCCL 是什么

```
NCCL = NVIDIA Collective Communications Library
       多 GPU/多机集合通信库
       PyTorch / TensorFlow / Megatron 底层都用它
```

### 7.2 NCCL 通信模式

| 模式 | 用途 |
|:---|:---|
| **AllReduce** | 数据并行梯度汇总 |
| **AllGather** | 张量并行收集 |
| **ReduceScatter** | ZeRO 优化器 |
| **All-to-All** | MoE 专家并行 |
| **Broadcast / Reduce** | 参数同步 |

### 7.3 NCCL 关键调优参数

```bash
# 选择网络后端
export NCCL_IB_HCA=mlx5_0,mlx5_1,...   # IB 设备
export NCCL_SOCKET_IFNAME=eth0          # 走以太网时的接口

# 性能
export NCCL_IB_GID_INDEX=3              # RoCEv2 用
export NCCL_IB_TC=106                   # PFC 优先级
export NCCL_IB_SL=3                     # Service Level
export NCCL_NET_GDR_LEVEL=PHB           # GPUDirect RDMA 级别

# 调试
export NCCL_DEBUG=INFO                  # 详细日志
export NCCL_DEBUG_SUBSYS=INIT,NET       # 只看初始化和网络
```

### 7.4 NCCL 测试基准（必备）

```bash
# 单机内 8 卡
all_reduce_perf -b 8 -e 8G -f 2 -g 8

# 多机（H100 集群）：单 GPU AllReduce 应接近 250-350 GB/s
# RoCE 调优好的话 200-280 GB/s
# 低于 100 GB/s → 网络配置必有问题
```

## 八、GPUDirect 系列加速

| 技术 | 作用 |
|:---|:---|
| **GPUDirect RDMA** | GPU 显存 ↔ 远端 GPU 显存（跳过 CPU/系统内存） |
| **GPUDirect Storage (GDS)** | GPU ↔ NVMe SSD（跳过 CPU 拷贝） |
| **GPUDirect Async (Kernel-Init)** | GPU 核函数直接发起网络通信 |

**启用 GDR 后**：AllReduce 性能可提升 30%+，延迟降低 50%+。

## 九、推理对网络的需求（容易被忽视）

### 9.1 单机推理

- 单卡推理：网络要求低，1Gbps 即可
- 8 卡张量并行：必须 NVLink，对外网络只需 25-100G

### 9.2 PD 分离推理（新挑战）

```
传统:  Prefill + Decode 在同一卡 → KV 不出卡
PD 分离:  Prefill Pool → KV Cache → Decode Pool
            ↑ 跨节点高速传输（RDMA 关键）

代表方案: Mooncake（月之暗面）、DistServe、llm-d
要求:     RDMA 400G+，否则 KV 传输成新瓶颈
```

### 9.3 大模型多机推理

| 场景 | 网络要求 |
|:---|:---|
| 单机 8 卡 H100 推理 | 100G 以太网够用 |
| 多机张量并行（如 Llama-405B） | 必须 RDMA 200G+ |
| PD 分离 + KV 传输 | RDMA 400G+ |
| 多模态（图像/视频） | 存储网络要 100G+ |

## 十、国产高速网络

### 10.1 国产 RDMA 网卡

| 厂商 | 产品 | 带宽 |
|:---|:---|:---:|
| **新华三** | 25/100/200G RDMA NIC | 200G |
| **锐捷** | RG-N18000 系列 | 100G |
| **华为** | SP680 / SP681（昇腾内置 HCCS） | 400G HCCS |
| **中科驭数** | DPU NIC | 25-200G |
| **云豹智能** | DPU | 100-200G |

### 10.2 国产高性能交换机

| 厂商 | 代表 | 用途 |
|:---|:---|:---|
| **华为 CloudEngine** | CE16800/9800 | AI 训练（已支持 NDR 等效） |
| **新华三** | S12500R/S9820 | 数据中心 |
| **锐捷** | RG-N18000 | 数据中心 |
| **盛科** | TsingMa 系列 | 25-400G ASIC |

### 10.3 国产 AI 网络方案

```
华为方案: 昇腾 + HCCS + CloudEngine + UB Mesh
         ↑ 全国产闭环，万卡可达

混合方案: 国产 GPU + 国产 RoCE 网络
         ↑ 性能比 NVIDIA IB 弱 15-25%，但合规
```

## 十一、AI 网络故障排查

### 11.1 常见故障类型

| 现象 | 排查方向 |
|:---|:---|
| AllReduce 慢 | NCCL_DEBUG=INFO，看是否走 IB/SHM |
| 训练 NaN/挂起 | 网络丢包或 PFC 死锁 |
| 多机性能不如单机 8x | 网卡未绑核或拓扑不对 |
| 间歇性卡顿 | ECN/PFC 风暴 |
| GPU 利用率 60% | 通信占比高，扩链路或换 IB |

### 11.2 排查工具箱

```bash
# 链路状态
ibstat                          # IB 端口状态
ibv_devinfo                     # IB 设备信息
mlnx_qos -i mlx5_0              # PFC/ECN 配置

# 性能
ib_send_bw                      # IB 单向带宽
ib_send_lat                     # 延迟
nccl-tests / all_reduce_perf    # 集合通信
perftest 套件                    # IB 综合测试

# 拓扑
nvidia-smi topo -m              # GPU↔NIC↔PCIe 拓扑
ibnetdiscover                   # IB 拓扑发现

# 丢包/拥塞
ethtool -S mlx5_0 | grep -E "discard|drop|pause"
mlxlink -d mlx5_0               # 物理层质量

# RoCE 专项
mlnx_qos -i mlx5_0              # 看 PFC/ECN 是否打开
cma_roce_mode -d mlx5_0         # RoCEv2 模式
```

### 11.3 NCCL 调优 Checklist

```
✅ 网卡 NUMA 亲和（GPU 与 NIC 同 NUMA）
✅ GPUDirect RDMA 启用（dmesg | grep nv_peer_mem）
✅ MTU = 9000 全链路一致
✅ PFC/ECN 已配置（RoCE）
✅ Routing 等价多路径（ECMP）
✅ NCCL_IB_HCA 包含全部卡
✅ NCCL_NET_GDR_LEVEL=PHB 或 SYS
✅ all_reduce_perf 跑出预期带宽
```

## 十二、未来 3 年趋势

| 方向 | 预测 |
|:---|:---|
| **800G/1.6T 普及** | B200 用 800G，下一代 GB300 用 1.6T |
| **NVIDIA NVLink 跨机** | NVLink Switch 把多机变成"超级 GPU" |
| **CPO（共封装光学）** | 交换机和光模块融合，能耗大降 |
| **UEC（Ultra Ethernet）** | 联盟级新标准，挑战 IB |
| **DPU 普及** | BlueField-3/4 卸载网络与存储 |
| **国产 IB 类方案** | 华为 UB（Unified Bus）等替代方案 |
| **AI 调度感知网络** | 训练任务 + 网络拓扑协同调度 |

## 十三、关键设计原则总结

```
1. 计算/存储/管理三网分离
2. 计算网络优先级 P0，IB 或 RoCEv2 400G+
3. GPU:NIC = 1:1（H100/H200 标准）
4. Rail-Optimized 拓扑（万卡必用）
5. RoCE 必须配 PFC + ECN + DCQCN
6. GPUDirect RDMA 一定要启用
7. 全链路 MTU 9000+
8. NCCL_DEBUG 跑通后再上业务
9. 持续监控带宽利用率 + PFC 暂停帧
10. 故障演练：拔掉一根线集群仍能跑
```

> 📖 **核心结论**：AI Infra 时代，**网络从"管道"变成了"主角"**。你做 vLLM/训练运维，网络底子不扎实，再贵的 GPU 都跑不到设计性能。
