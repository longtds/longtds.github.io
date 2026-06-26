# GPU 与硬件

> LLM 推理是硬件密集型工作，**显存带宽、显存容量、互联拓扑、量化精度**四要素决定服务上限。**理解硬件是性能调优的起点**——不懂 HBM 带宽，永远调不好 vLLM；不懂 NVLink，做不好张量并行。

## 一、GPU 选型矩阵（2025 主流）

### 1.1 NVIDIA 数据中心 GPU

| 型号 | 架构 | 显存 | 带宽 | FP16/BF16 | FP8 | INT8 | NVLink | 适用 |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|:---|
| **H200** ⭐⭐⭐⭐⭐ | Hopper | 141GB HBM3e | 4.8 TB/s | 989 TFLOPS | 1979 | 3958 | NVLink4 900GB/s | 大模型推理首选 |
| **H100 SXM** | Hopper | 80GB HBM3 | 3.35 TB/s | 989 | 1979 | 3958 | 900GB/s | 70B-405B 训练/推理 |
| **H100 PCIe** | Hopper | 80GB HBM3 | 2.0 TB/s | 756 | 1513 | 3026 | NVLink 600GB/s | 替代 SXM 性价比 |
| **L40S** ⭐⭐⭐⭐ | Ada | 48GB GDDR6 | 864 GB/s | 362 | 733 | 1466 | 无 | 中小模型 / 微调 |
| **L40** | Ada | 48GB GDDR6 | 864 GB/s | 181 | - | 724 | 无 | 推理 |
| **A100 80G SXM** | Ampere | 80GB HBM2e | 2.0 TB/s | 312 | - | 624 | 600GB/s | 老牌主力 |
| **A100 40G** | Ampere | 40GB HBM2 | 1.55 TB/s | 312 | - | 624 | 600GB/s | 7B-30B 推理 |
| **A10/A10G** | Ampere | 24GB GDDR6 | 600 GB/s | 125 | - | 250 | 无 | 小模型 |
| **L4** | Ada | 24GB GDDR6 | 300 GB/s | 121 | 242 | 485 | 无 | 边缘 / 中小批 |
| **T4** ⭐⭐⭐ | Turing | 16GB GDDR6 | 320 GB/s | 65 | - | 130 | 无 | 老旧但便宜 |

### 1.2 NVIDIA 消费级（推理可用）

| 型号 | 显存 | 带宽 | FP16 | 价格梯度 | 备注 |
|:---|:---:|:---:|:---:|:---:|:---|
| **RTX 5090** | 32GB GDDR7 | 1.79 TB/s | 419 | $$$$ | 2025 旗舰 |
| **RTX 4090** | 24GB GDDR6X | 1.0 TB/s | 165 | $$$ | 主流 LLM 部署 |
| **RTX 3090** | 24GB GDDR6X | 936 GB/s | 142 | $$ | 二手主力 |
| **RTX A6000** | 48GB GDDR6 | 768 GB/s | 155 | $$$$ | 工作站 48G |

### 1.3 国产 GPU 矩阵

| 型号 | 厂商 | 显存 | 带宽 | FP16 | 生态 | 状态 |
|:---|:---|:---:|:---:|:---:|:---|:---|
| **昇腾 910B/910C** ⭐ | 华为 | 64GB HBM2e | 1.6 TB/s | 320 | CANN/MindSpore/PyTorch+插件 | 主流 |
| **昇腾 910** | 华为 | 32GB | 1.2 TB/s | 256 | - | 老款 |
| **思元 MLU370-X8** | 寒武纪 | 24GB | 614 GB/s | 96 | Cambricon Neuware | 国密合规 |
| **思元 590** | 寒武纪 | 80GB | 2.0 TB/s | 256 | - | 2024+ |
| **天数智芯 BI-V100/V150** | 天数智芯 | 32GB | 1.2 TB/s | 147 | CUDA 兼容 | 算力中心 |
| **沐曦 C500** | 沐曦 | 64GB | 1.55 TB/s | 280 | CUDA 兼容 | 2024 |
| **燧原 邃思 2.5** | 燧原 | 32GB | 1.6 TB/s | 256 | TopsRider | 算力中心 |
| **海光 DCU K100/Z100** | 海光 | 64GB | 1.6 TB/s | 350 | DTK (ROCm fork) | 信创 |
| **摩尔线程 MTT S4000** | 摩尔线程 | 48GB | 768 GB/s | 100 | MUSA | 2024 |
| **壁仞 BR104** | 壁仞 | 32GB | 819 GB/s | 256 | BIRENSUPA | 训练 |

### 1.4 AMD / Intel

```
AMD MI300X    192GB HBM3, 5.3 TB/s, 1300 TFLOPS FP16 (强力 H100 替代)
AMD MI300A    APU + GPU 集成
AMD MI250X    128GB HBM2e
AMD MI210     64GB

Intel Gaudi 3  128GB HBM2e, 3.7 TB/s, 1835 TFLOPS BF16
Intel Gaudi 2  96GB HBM2e, 2.45 TB/s
Intel Max 1550 (PVC) 128GB HBM2e
```

## 二、显存带宽 vs 算力（核心矛盾）

### 2.1 推理是**显存带宽密集型**

```
LLM Decode 阶段:
  - 每生成 1 token 要把全部模型权重过一遍
  - 70B FP16 = 140 GB → H100 PCIe 2 TB/s → 单 token 70ms (理论)
  - 实际: ~50 token/s (单 batch)

→ 算力够，但带宽不够
→ Roofline 模型: 大多数 op 卡在 memory-bound 区
→ 这就是为什么 H200 (4.8TB/s) 比 H100 推理快 2x，算力却几乎一样
```

### 2.2 Prefill vs Decode

```
Prefill (Prompt 处理):
  - 计算密集 (compute-bound)
  - 算力越高越好
  - 大 batch / 长序列友好

Decode (生成):
  - 显存带宽密集 (memory-bound)
  - 带宽越高越好
  - 小 batch 难以利用算力

→ 这就是为什么搞 PD 分离 (Prefill/Decode Disaggregation)
→ Prefill 节点用 H100/L40S，Decode 节点用 H200/MI300X
```

### 2.3 算力利用率 (MFU/MBU)

```
MFU (Model FLOPs Utilization)
  实际 FLOPs / 理论峰值 FLOPs
  训练: 30-50% 算优秀
  推理: 通常 < 10%（memory-bound 决定）

MBU (Model Bandwidth Utilization) ⭐ 推理关键指标
  实际带宽用量 / 理论峰值带宽
  良好: > 60%
  优秀: > 80%

公式:
  Decode 单 token 理论耗时 = 模型大小 / GPU 带宽
  Llama-70B FP16 / H100 = 140GB / 3.35TB/s = 42 ms
  实测 70 ms → MBU = 60%
```

## 三、显存计算

### 3.1 模型权重

| 精度 | 字节/参数 | 7B | 13B | 70B | 175B | 405B |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| FP32 | 4 | 28GB | 52GB | 280GB | 700GB | 1620GB |
| FP16/BF16 | 2 | 14GB | 26GB | 140GB | 350GB | 810GB |
| FP8 | 1 | 7GB | 13GB | 70GB | 175GB | 405GB |
| INT4 | 0.5 | 3.5GB | 6.5GB | 35GB | 88GB | 203GB |

### 3.2 KV Cache 计算

```
单 token KV Cache = 2 × num_layers × num_heads × head_dim × dtype_size
                  = 2 × n_l × d_model × dtype_size

Llama2-70B (n_l=80, d_model=8192) FP16:
  单 token = 2 × 80 × 8192 × 2 = 2.6 MB
  4K context × 256 并发 = 4096 × 256 × 2.6 MB ≈ 2.6 TB
  → 这就是为什么需要 PagedAttention
  → 或者 KV Cache 量化 (INT8/FP8) 减半

GQA (Group Query Attention) 减少 KV:
  Llama3-70B (n_kv_heads=8, n_q_heads=64): 减少到 1/8
  Llama3-405B: 同 GQA, 减少到 1/8
```

### 3.3 显存预算公式

```
Total = Model_Weights + KV_Cache + Activations + Framework_Overhead

KV_Cache_Budget = Total_VRAM × 0.7 - Model_Weights
                  (保守 70%，留 30% 给激活和 fragmentation)

例: H100 80G 跑 Llama-70B FP16
  权重: 140 GB → 需要 2 × H100 (Tensor Parallel)
  剩余: 160 - 140 = 20 GB → KV Cache
  → 单 token 2.6 MB → 20GB / 2.6MB ≈ 7700 token
  → 4K context × 1.9 并发 (不够实用)

→ 必须量化:
  FP8: 权重 70GB → 单卡 + 10GB KV cache → 仍紧张
  INT4 (AWQ/GPTQ): 权重 35GB → 单卡 + 45GB KV cache → 16 并发可用
```

## 四、互联拓扑

### 4.1 节点内（Intra-Node）

```
PCIe 4.0  x16   32 GB/s (双向 64 GB/s)
PCIe 5.0  x16   64 GB/s
PCIe 6.0  x16   128 GB/s

NVLink 3 (A100)    600 GB/s/GPU (12 link × 50 GB/s)
NVLink 4 (H100)    900 GB/s/GPU (18 link × 50 GB/s)
NVLink 5 (Blackwell) 1.8 TB/s

NVSwitch (HGX/DGX H100):
  8 GPU 全互联，每对都是 900 GB/s
  → 张量并行 TP=8 友好
```

### 4.2 节点间（Inter-Node）

```
RoCE / IB:
  IB HDR 200 Gb/s = 25 GB/s
  IB NDR 400 Gb/s = 50 GB/s
  IB XDR 800 Gb/s = 100 GB/s (2024+)
  RoCE 400Gbps (Ethernet)
  Spectrum-X (NV) 800 Gbps

GPU Direct RDMA:
  GPU 内存 ↔ NIC 直接 DMA，不经 CPU
  延迟 < 2us

NCCL 集合通信:
  AllReduce/AllGather/ReduceScatter
  自动选 NVLink/PCIe/RDMA
```

### 4.3 拓扑亲和（关键）

```bash
# 看 GPU 拓扑
nvidia-smi topo -m

# 输出:
#         GPU0   GPU1   GPU2   ...
# GPU0    X      NV12   NV12   ...
# GPU1    NV12   X      NV12   ...
# 
# NV12: 12-link NVLink (满速)
# PIX:  PCIe + 1 hop
# PXB:  PCIe + bridge
# NODE: 跨 NUMA node
# SYS:  跨 socket

# 选 GPU 时 优先 NV12 连接
# 跨 NUMA = 性能腰斩
```

```bash
# 设置 CPU 亲和（NUMA 绑定）
# 看 GPU NUMA 归属
nvidia-smi topo -mp
# GPU0 NUMA: 0
# GPU1 NUMA: 0
# GPU2 NUMA: 1
# GPU3 NUMA: 1

# 启动时绑核
numactl --cpunodebind=0 --membind=0 python serve.py --gpu 0

# K8s
spec:
  containers:
    - resources:
        limits: { nvidia.com/gpu: 1 }
  nodeSelector: { nvidia.com/gpu.product: H100-SXM5-80GB }
  topologySpreadConstraints: ...
```

## 五、CUDA 软件栈

### 5.1 版本关系（必记）

```
NVIDIA Driver  ──→  CUDA Runtime  ──→  cuDNN/NCCL  ──→  PyTorch/vLLM
   570.x         ──→  CUDA 12.6      ──→   9.x          ──→  PyTorch 2.5+

向后兼容:
  Driver 兼容更老的 CUDA Runtime（但反之不行）
  CUDA Runtime 与 cuDNN 严格绑定

查询:
  nvidia-smi              → Driver 版本 + CUDA 兼容上限
  nvcc --version          → CUDA Toolkit 版本
  cat /usr/include/cudnn_version.h → cuDNN 版本
  python -c "import torch; print(torch.version.cuda, torch.backends.cudnn.version())"
```

### 5.2 容器化（推荐）

```bash
# 主机只装 Driver
apt install nvidia-driver-570 nvidia-container-toolkit

# 容器内带 CUDA Runtime
docker run --gpus all nvidia/cuda:12.6-runtime-ubuntu22.04 nvidia-smi
docker run --gpus all vllm/vllm-openai:latest

# Kubernetes
# 安装 NVIDIA GPU Operator
helm install gpu-operator nvidia/gpu-operator \
  -n gpu-operator --create-namespace
```

### 5.3 关键库

```
PyTorch       推理基座
Transformers  HuggingFace 模型 hub
Accelerate    多卡 / FSDP 工具
DeepSpeed     训练为主 + 推理 (ZeRO Inference)
Triton (OpenAI) GPU kernel DSL ⭐ 学一次，写自定义 op
CUTLASS       CUDA C++ GEMM 模板库
FlashAttention 注意力优化库 ⭐ 已并入 PyTorch SDPA
xFormers      Meta 优化库
TensorRT-LLM  NV 推理优化
vLLM/SGLang   推理引擎（详见 02_推理框架）
```

## 六、监控与诊断

### 6.1 nvidia-smi 基础

```bash
# 实时
nvidia-smi
watch -n 1 nvidia-smi
nvidia-smi -l 1                        # 刷新 1s
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw --format=csv -l 1

# 历史
nvidia-smi dmon -s pucvmet -i 0        # 实时多指标
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used --format=csv,nounits -lms 100 > log.csv

# 进程
nvidia-smi pmon                        # 各进程 GPU 占用
fuser -v /dev/nvidia*                   # 谁在用 GPU
```

### 6.2 DCGM (Data Center GPU Manager) ⭐

```bash
# 安装
apt install datacenter-gpu-manager

# 启动 nv-hostengine
systemctl start nvidia-dcgm

# CLI
dcgmi discovery -l                      # 列出 GPU
dcgmi health -g 0 -c                    # 健康检查
dcgmi diag -g 0 -r 3                    # 诊断（耗时几分钟）

# 持续监控 (Prometheus exporter)
docker run -d --gpus all --rm -p 9400:9400 \
  nvcr.io/nvidia/k8s/dcgm-exporter:3.3.7-3.4.0-ubuntu22.04

# Prometheus 抓取
- job_name: dcgm
  static_configs:
    - targets: ['gpu-host:9400']

# Grafana dashboard: 12239 (官方 DCGM)
```

### 6.3 关键 GPU 指标

```
基础:
  GPU Util %             → 看似活跃但不代表算力利用
  SM Util % (DCGM)        → 真实算力利用 ⭐
  Memory Util %          → 显存带宽利用
  Memory Used GB         → 显存占用
  Temp °C                → 温度（< 85°C）
  Power Draw W           → 功耗
  Clock SM/Mem MHz       → 频率（看是否降频）

进阶:
  PCIe RX/TX MB/s        → PCIe 流量
  NVLink RX/TX           → NVLink 流量
  ECC errors             → 显存 ECC 错误（关键！）
  XID errors             → 内核报告的 GPU 错误码

诊断:
  GPU Util 100% 但 SM Util 30%
  → kernel 启动开销大 / batch 太小
  
  Memory Util 100%
  → memory-bound，加大 batch / KV cache 量化
  
  PCIe TX 高
  → 跨卡通信瓶颈，检查 NVLink 利用
```

### 6.4 nsys / nsight-compute（Profile）

```bash
# nsys (system-wide profile)
nsys profile -o trace --trace=cuda,nvtx,cudnn python infer.py
nsys-ui trace.nsys-rep                  # GUI 看

# nsight-compute (kernel 级)
ncu --target-processes all -o profile python infer.py
ncu --section MemoryWorkloadAnalysis -o mem python infer.py

# Triton kernel
@triton.jit
def kernel(...): ...
# 内嵌 print/profile
```

## 七、故障与排查

### 7.1 常见错误

| 错误 | 原因 | 处理 |
|:---|:---|:---|
| **CUDA out of memory** | 显存不足 | 减小 batch / 量化 / 释放缓存 |
| **CUDA illegal memory access** | 越界 / 同步错 | 检查 indexing / 启用 `CUDA_LAUNCH_BLOCKING=1` |
| **NCCL timeout** | 通信阻塞 | 检查互联 / `NCCL_TIMEOUT` 调大 |
| **XID 13 / 31 / 79** | 硬件错误 | 重启 / 报修 |
| **XID 48 / 63 / 64** | ECC 错误 | 报修 GPU |
| **No CUDA-capable device** | 驱动 / 容器配置 | 检查 nvidia-container-toolkit |
| **kernel not callable** | CUDA / cuDNN 不匹配 | 检查版本兼容 |
| **Bus Error** | PCIe 不稳 / GPU 掉卡 | 重启 / 换插槽 |
| **Watchdog Timeout** | kernel 跑太久 | 优化 / 拆分 |

### 7.2 XID 错误码（重要）

```bash
dmesg | grep -i xid
journalctl -k | grep -i xid

# 常见:
# XID 13   显存 ECC 错误 → 报修
# XID 31   GPU memory page fault → app bug
# XID 43/45 内核重启 → driver 问题
# XID 63   ECC double-bit 错 → 报修（必须换卡）
# XID 64   ECC 阈值告警
# XID 79   GPU 从总线掉了 → 报修
# XID 109/110 GPU reset 失败

# 完整列表:
https://docs.nvidia.com/deploy/xid-errors/
```

### 7.3 GPU 掉卡

```bash
# 现象: nvidia-smi 找不到 / lspci 找不到
lspci | grep -i nvidia
ls /dev/nvidia*

# 排查:
# 1. dmesg | grep -i nvrm
# 2. 看 PCIe 状态: lspci -vvv -s <bus:dev.func>
# 3. fan / 温度: ipmitool sensor
# 4. 重启大法
# 5. 重置 PCIe: setpci -s <bus> CAP_PM+4.b=4
# 6. 修复模式: nvidia-smi -r （需要先 stop 所有 GPU 进程）

# 报修阈值:
# - XID 63/74/79/45 → 立即报修
# - Single-bit ECC > 阈值 → 报修
# - 温度持续 > 85°C → 检查散热
```

### 7.4 GPU 压测

```bash
# gpu-burn (检测稳定性，跑 1-24 小时)
git clone https://github.com/wilicc/gpu-burn
cd gpu-burn && make
./gpu_burn 3600                        # 1 小时

# DCGM 诊断 (官方)
dcgmi diag -g 0 -r 3                    # Level 3 (~10 min)
dcgmi diag -g 0 -r 4                    # Level 4 (~30 min, 完整)

# nccl-tests (多卡通信)
git clone https://github.com/NVIDIA/nccl-tests
make CUDA_HOME=/usr/local/cuda MPI=1
mpirun -np 8 ./build/all_reduce_perf -b 8 -e 256M -f 2 -g 1

# 期望 bandwidth:
# NVLink: > 200 GB/s busBW
# PCIe 4.0: ~12 GB/s
# Cross-node IB 200G: ~20 GB/s
```

## 八、GPU 调度（K8s）

### 8.1 NVIDIA GPU Operator

```bash
# 一键安装（生产推荐）
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm install gpu-operator nvidia/gpu-operator \
  -n gpu-operator --create-namespace \
  --set driver.enabled=false   # 主机已装则关闭

# 自动安装:
# - nvidia-device-plugin
# - DCGM exporter
# - Container Toolkit
# - MIG manager
# - GFD (GPU Feature Discovery)
```

### 8.2 GPU 共享方案

```
1. 整卡独占 (Exclusive)
   resources: { limits: { nvidia.com/gpu: 1 } }
   适合: 训练 / 大模型推理

2. MIG (Multi-Instance GPU) ⭐ A100/H100 专属
   一张 H100 → 7 个独立实例 (1g.10gb, 2g.20gb, ...)
   硬件级隔离，性能稳定
   适合: 中小模型多租户

3. Time-Slicing (时间片)
   多容器共享单卡，轮转使用
   配置: device-plugin replicas
   适合: 开发 / 测试

4. MPS (Multi-Process Service)
   多进程共享 GPU context
   并发计算，不隔离显存
   适合: 同租户多模型

5. vGPU (商业)
   NVIDIA AI Enterprise license
   软件级切分

6. 阿里 cGPU / 腾讯 qGPU / 华为 Volcano vGPU
   国产共享方案，按显存切片
```

### 8.3 MIG 配置实例

```bash
# 开启 MIG (需要 root)
nvidia-smi -i 0 -mig 1
nvidia-smi mig -lgip                    # 列出可用 profile
nvidia-smi mig -cgi 1g.10gb,1g.10gb,1g.10gb,1g.10gb,1g.10gb,1g.10gb,1g.10gb -C

# K8s 中
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: ai
      resources:
        limits: { nvidia.com/mig-1g.10gb: 1 }
```

### 8.4 Volcano / Yunikorn 调度

```yaml
# Gang Scheduling (训练必须)
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata: { name: llm-train }
spec:
  minAvailable: 8                     # 必须 8 个 Pod 同时就绪
  schedulerName: volcano
  tasks:
    - replicas: 8
      template:
        spec:
          containers:
            - resources: { limits: { nvidia.com/gpu: 1 } }
```

## 九、量化精度与推理

### 9.1 精度对比

| 精度 | 字节 | 训练 | 推理 | 精度损失 |
|:---|:---:|:---:|:---:|:---|
| **FP32** | 4 | ✅ | ❌ 太慢 | 无 |
| **BF16** | 2 | ✅ | ✅ | ~0 |
| **FP16** | 2 | ⚠️ 易溢出 | ✅ | ~0 |
| **FP8** | 1 | ✅ H100+ | ✅ H100+ | < 1% (E4M3) |
| **INT8** | 1 | ❌ | ✅ | 1-3% |
| **AWQ/GPTQ INT4** | 0.5 | ❌ | ✅ | 1-5% |
| **NF4 (QLoRA)** | 0.5 | LoRA | ✅ | ~1% |

### 9.2 量化方法

```
权重量化 (Weight-Only):
  AWQ (Activation-aware Weight Quantization)
    保留关键权重精度，最优 INT4
  GPTQ (Generative Pre-trained Transformer Quantization)
    OBQ 算法，逐层校准
  GGUF (llama.cpp)
    Q2_K, Q3_K, Q4_K_M, Q5_K_M, Q6_K, Q8_0
    CPU+GPU 混合推理

激活量化:
  SmoothQuant
    平滑激活分布，INT8 准确度高
  FP8 (H100 / MI300)
    硬件原生 FP8，E4M3 (推理) / E5M2 (训练)

KV Cache 量化:
  vLLM kv-cache-dtype=fp8
  INT4 KV Cache (实验)
  → 减半显存，几乎无损

后训练 vs 量化感知:
  PTQ (Post-Training)    无需重训，1-2% 精度损失
  QAT (Quantization-Aware) 训练时量化，损失 < 0.5%
```

### 9.3 实战量化命令

```bash
# llama.cpp GGUF 量化
./llama-quantize llama-7b-f16.gguf llama-7b-q4_k_m.gguf q4_k_m

# AWQ (autoawq)
python -m awq.entry --model_path llama-70b \
  --w_bit 4 --q_group_size 128 \
  --dump_quant llama-70b-awq

# GPTQ (auto-gptq)
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
quantize_config = BaseQuantizeConfig(bits=4, group_size=128, desc_act=False)
model = AutoGPTQForCausalLM.from_pretrained(model_path, quantize_config)
model.quantize(calibration_data)
model.save_quantized(output_dir)

# TensorRT-LLM FP8
trtllm-build --checkpoint_dir llama_fp8/ --output_dir engine_fp8/ \
  --gemm_plugin fp8 --use_fp8_context_fmha enable

# vLLM 部署量化模型
vllm serve TheBloke/Llama-2-70B-AWQ --quantization awq \
  --gpu-memory-utilization 0.9 -tp 1
```

## 十、电力 & 散热

### 10.1 功耗

```
H100 SXM5    700W
H100 PCIe    350W
H200          700W
A100 SXM      400W
A100 PCIe    300W
L40S          350W
RTX 4090     450W

8 × H100 SXM5 服务器 (DGX H100):
  GPU: 700 × 8 = 5.6 KW
  CPU + RAM + NIC: ~1 KW
  整机: ~6.5 KW
  → 单机柜放不下太多 (一般机柜 < 20 KW)
```

### 10.2 散热

```
风冷:
  - 入风温度 < 27°C (ASHRAE A2)
  - GPU 入风 < 32°C
  - 8 × H100 风冷需要强力风扇

液冷 (推荐):
  - D2C (Direct to Chip)
  - 单机柜可达 50-100 KW
  - PUE < 1.1

国内液冷主流: 浪潮 / 中科曙光 / 联想 / 华为 / 阿里灵骏
```

### 10.3 功耗调优

```bash
# 限功率（不限频可能更高）
nvidia-smi -i 0 -pl 600                 # 限制 GPU 0 到 600W

# 持久模式（避免频繁初始化）
nvidia-smi -pm 1

# 计算模式
nvidia-smi -i 0 -c 0                    # DEFAULT (允许多进程)
nvidia-smi -i 0 -c 3                    # EXCLUSIVE_PROCESS (独占)

# 频率锁定
nvidia-smi -i 0 -lgc 1980,1980          # 锁 GPU clock
nvidia-smi -i 0 -lmc 1593,1593          # 锁 mem clock

# 重置
nvidia-smi -i 0 -rgc
nvidia-smi -i 0 -rmc
```

## 十一、典型集群规格（参考）

### 11.1 训练集群

```
Llama-70B 训练:
  - 32 × H100 80G SXM5 (4 节点 × 8 GPU)
  - NVLink 4 + IB NDR 400Gb × 8/节点
  - PFS: WekaFS / Lustre / GPFS, 10 PB+
  - 网络: spine-leaf, 1:1 GPU-NIC

Llama-405B 训练:
  - 128 GPU+ (16 节点)
  - 同上 + 2× 网络
```

### 11.2 推理集群

```
中等规模 (日活 1M):
  - 16 × H100 80G (2 DGX or 2× 8卡服务器)
  - 跑 70B FP8 / TP=2
  - QPS 100+

大规模 (日活 100M):
  - 100+ × H100/H200
  - PD 分离: Prefill 节点 H100, Decode 节点 H200
  - 多副本负载均衡
  - 自动扩缩 (HPA + KEDA)
```

### 11.3 国产对标

```
华为 Atlas 900 SuperPoD
  - 1024 × 昇腾 910B/910C
  - 192 PFlops FP16

寒武纪 思元 集群
  - 通过 K8s + Operator 调度

阿里灵骏
  - HPN7 网络 (改良 RoCE, 200/400G)
  - PAI-Lingjun 弹性算力
  - GPU 集群即服务
```

## 十二、典型坑

| 坑 | 建议 |
|:---|:---|
| **看 GPU Util 90% 就以为饱和** | 看 SM Util / MBU |
| **PCIe Gen3 跑大模型** | 至少 Gen4 / NVLink |
| **跨 NUMA 用 GPU** | 绑核 + 同 NUMA 显卡 |
| **不开 ECC** | 数据中心必开 |
| **驱动版本乱** | 全集群统一 |
| **MIG 没 reconcile** | GPU Operator MIG Manager |
| **Docker 不带 nvidia-container-toolkit** | 必装 |
| **K8s Pod 抢 GPU** | Volcano gang scheduling |
| **温度不监控** | DCGM + Prometheus |
| **XID 错误不处置** | 监控告警 + 自动隔离 |
| **量化只 FP16** | INT4/FP8 显存翻 2-4 倍 |
| **共享 GPU 不隔离** | MIG > vGPU > Time-Slicing |
| **持续模式没开** | nvidia-smi -pm 1 (减少初始化) |
| **训练 batch 不够** | 用更大 GPU / 减小模型 / 梯度累加 |
| **跨节点用 PCIe 通信** | RDMA / NVLink Network |

## 十三、推荐栈（2025）

### 13.1 训练（仅参考）

```
硬件:    H100 / H200 / MI300X / 昇腾 910C
互联:    NVLink 4 + IB NDR 400Gb
存储:    Weka / Lustre / GPFS / 阿里 CPFS
框架:    PyTorch FSDP / Megatron-LM / DeepSpeed
调度:    K8s + Volcano / Slurm
```

### 13.2 推理（你的主战场）

```
硬件:    H100/H200 (主流) + L40S/L4 (中小)
        国产: 昇腾 910B / 海光 K100
存储:    NVMe local (KV cache spillover)
框架:    vLLM / SGLang / TGI / TensorRT-LLM
量化:    AWQ INT4 / FP8 / GGUF
调度:    K8s + GPU Operator + KEDA HPA
监控:    DCGM + Prometheus + Grafana
```

### 13.3 国产/信创

```
+ 昇腾 910B/910C + CANN + MindSpore-Lite
+ 海光 DCU + DTK (ROCm fork)
+ 寒武纪 思元 + Neuware
+ 摩尔线程 MTT + MUSA
+ 国密 / 等保合规集群
```

## 十四、学习路径

```
入门（1 月）:
  1. GPU 架构（SM/CUDA core/tensor core）
  2. nvidia-smi / DCGM 熟练
  3. PyTorch + Transformers 基本推理
  4. 显存计算 + 量化基础
  5. vLLM 跑通

中级（3 月）:
  6. CUDA C++ 基础 (sample)
  7. Triton kernel DSL
  8. FlashAttention / PagedAttention 原理
  9. TensorRT-LLM 部署
  10. MIG / GPU 共享调度

高级（6 月+）:
  11. 自定义 CUDA op
  12. NCCL / 分布式通信优化
  13. PD 分离推理架构
  14. 国产 GPU 适配 (昇腾 / 海光)
  15. 万卡集群运维

专家:
  16. Kernel fusion / 自动 codegen
  17. 推理服务 SLA 极致优化
  18. 故障预测 + 自愈
  19. 算力调度系统
```

## 十五、参考资料

```
官方:
  - NVIDIA Deep Learning Performance Guide
  - cuDNN / CUDA Programming Guide
  - NCCL Developer Guide
  - DCGM Documentation
  - PyTorch Profiler

学习:
  - GPU Mode 社区 (CUDA + Triton)
  - NVIDIA Deep Learning Institute (DLI)
  - HuggingFace Inference Optimization

社区:
  - r/LocalLLaMA
  - vLLM Slack
  - SGLang Discord
  - 国内: AIInfra / GPU Mode 中文

报告:
  - LMSys Chatbot Arena
  - MLPerf Inference
  - SemiAnalysis (硬件分析)
```

> 📖 **核心判断**：LLM 推理硬件选型是**带宽 × 显存 × 互联** 三维优化问题。**H200 > H100 > MI300X > A100 > L40S** 是 2025 推理首选梯度，但**国产替代（昇腾/海光）已可承担 70-90% 场景**——核心限制不在硬件，在 CUDA 生态。**先把 nvidia-smi、DCGM、XID 错误码、量化精度、KV Cache 计算这五项打牢，再谈框架优化**——上层 vLLM 的所有调参，本质都是在这五项之上。

