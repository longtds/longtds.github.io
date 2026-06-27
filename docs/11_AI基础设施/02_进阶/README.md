# 进阶

> AI 基础设施进阶 = **vLLM/SGLang 生产化(TP+PP+Prefix Cache+Speculative Decoding) + 量化深度(AWQ/GPTQ/SmoothQuant/FP8) + Triton+KServe 推理平台 + Continuous Batching/PagedAttention 内核 + 训练分布式(DDP/FSDP/DeepSpeed/Megatron-3D) + 数据集 + Tokenizer + Volcano/Kueue/Karmada 多集群调度 + MIG/MPS/虚拟化 + RoCE/IB 网络 + 分布式存储(JuiceFS/Lustre) + LangChain/LlamaIndex RAG + 国产昇腾(CANN/MindIE/LMDeploy) + 模型注册(MLflow/Harbor)**。本章面向独立维护 AI 平台的工程师。

## 一、vLLM 生产化深度

### 1.1 关键特性

```
PagedAttention:
  - KV cache 分页 (类 OS 虚拟内存)
  - 内存碎片减少 90%
  - 允许 100+ 并发

Continuous Batching:
  - 不等整 batch 完成
  - 完成的请求立刻返回
  - 新请求随时插入
  - 吞吐 ↑ 5-10x

Speculative Decoding:
  - 小模型预测 + 大模型验证
  - 加速 1.5-3x

Prefix Caching:
  - 相同 prompt 前缀复用 KV cache
  - 系统提示场景 ↑ 30-50%

Multi-LoRA:
  - 单基座 + N 个 LoRA 同服务
  - 适合多租户微调

Chunked Prefill:
  - 长输入分块处理
  - 减少 first-token 延迟
```

### 1.2 生产参数

```bash
vllm serve Qwen/Qwen2.5-72B-Instruct \
  --tensor-parallel-size 4 \
  --pipeline-parallel-size 2 \
  --gpu-memory-utilization 0.92 \
  --max-model-len 65536 \
  --max-num-seqs 256 \
  --enable-prefix-caching \
  --enable-chunked-prefill \
  --quantization fp8 \
  --kv-cache-dtype fp8_e5m2 \
  --enable-lora \
  --max-loras 8 \
  --max-lora-rank 64 \
  --speculative-model Qwen/Qwen2.5-1.5B-Instruct \
  --num-speculative-tokens 5 \
  --served-model-name qwen-72b \
  --api-key sk-xxx \
  --port 8000
```

### 1.3 性能调优 Top 10

```
1.  TP × PP = GPU 总数 (TP 优先, 单机)
2.  max-model-len 按业务 (越大 KV 越大)
3.  enable-prefix-caching (系统 prompt 场景必开)
4.  enable-chunked-prefill (长输入)
5.  FP8 量化 (H100 / Ada / B100)
6.  KV cache dtype FP8_E5M2 (省显存)
7.  gpu-memory-utilization 0.92 (留 8%)
8.  AWQ / GPTQ Int4 (A100/V100 友好)
9.  Speculative decoding (小模型加速)
10. Multi-LoRA (多租户共享基座)
```

### 1.4 vLLM on K8s

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: vllm-qwen72b, namespace: llm }
spec:
  replicas: 2
  selector: { matchLabels: { app: vllm-qwen72b } }
  template:
    metadata: { labels: { app: vllm-qwen72b } }
    spec:
      runtimeClassName: nvidia
      containers:
        - name: vllm
          image: vllm/vllm-openai:v0.6.0
          args:
            - --model=Qwen/Qwen2.5-72B-Instruct
            - --tensor-parallel-size=4
            - --enable-prefix-caching
            - --quantization=fp8
          env:
            - { name: HF_HOME, value: /models }
            - { name: HF_HUB_OFFLINE, value: "1" }
          resources:
            limits: { nvidia.com/gpu: 4, memory: 200Gi, cpu: 32 }
            requests: { nvidia.com/gpu: 4, memory: 200Gi, cpu: 16 }
          volumeMounts:
            - { name: models, mountPath: /models }
            - { name: shm, mountPath: /dev/shm }
          readinessProbe:
            httpGet: { path: /health, port: 8000 }
            initialDelaySeconds: 60
            periodSeconds: 10
      volumes:
        - name: models
          persistentVolumeClaim: { claimName: models-pvc }
        - name: shm
          emptyDir: { medium: Memory, sizeLimit: 16Gi }
      nodeSelector: { gpu-type: h100 }
      tolerations:
        - { key: nvidia.com/gpu, operator: Exists, effect: NoSchedule }
```

## 二、量化深度

### 2.1 量化对比

| 方法 | 精度 | 速度 | 显存 | 适合 |
|:---|:---:|:---:|:---:|:---|
| **FP16/BF16** | ⭐⭐⭐⭐⭐ | 1x | 2 bytes/param | 训练 + 推理基线 |
| **FP8 (E4M3/E5M2)** | ⭐⭐⭐⭐ | 1.5-2x | 1 byte | H100 / B100 ⭐ |
| **INT8 / W8A8** | ⭐⭐⭐⭐ | 1.5-2x | 1 byte | 通用推理 |
| **GPTQ (W4A16)** | ⭐⭐⭐⭐ | 1.5-2x | 0.5 byte | A100 / 单卡 ⭐ |
| **AWQ (W4A16)** | ⭐⭐⭐⭐ | 1.5-2x | 0.5 byte | A100 / 单卡 ⭐ |
| **GGUF Q4_K_M** | ⭐⭐⭐ | 中 | 0.4 byte | CPU / 边缘 ⭐ |
| **GGUF Q5_K_M** | ⭐⭐⭐⭐ | 中 | 0.5 byte | CPU / 边缘 |
| **GGUF Q8_0** | ⭐⭐⭐⭐⭐ | 中 | 1 byte | CPU 高精 |
| **SmoothQuant** | ⭐⭐⭐⭐ | 1.5x | 1 byte | 大模型 W8A8 |

### 2.2 AWQ 量化（推荐）

```python
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

model_path = "Qwen/Qwen2.5-7B-Instruct"
quant_path = "qwen2.5-7b-awq"

model = AutoAWQForCausalLM.from_pretrained(model_path, low_cpu_mem_usage=True)
tokenizer = AutoTokenizer.from_pretrained(model_path)

quant_config = {
    "zero_point": True,
    "q_group_size": 128,
    "w_bit": 4,
    "version": "GEMM"
}

model.quantize(tokenizer, quant_config=quant_config)
model.save_quantized(quant_path)
tokenizer.save_pretrained(quant_path)
```

```bash
# vLLM 加载 AWQ
vllm serve qwen2.5-7b-awq --quantization awq
```

### 2.3 GPTQ 量化

```python
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig

quantize_config = BaseQuantizeConfig(bits=4, group_size=128, desc_act=True)
model = AutoGPTQForCausalLM.from_pretrained(model_path, quantize_config)
model.quantize(calibration_dataset)
model.save_quantized("qwen2.5-7b-gptq")
```

### 2.4 FP8（H100 必修）

```bash
vllm serve Qwen/Qwen2.5-72B-Instruct \
  --quantization fp8 \
  --kv-cache-dtype fp8_e5m2 \
  --tensor-parallel-size 4
```

```
FP8 vs FP16:
  显存:  减半
  速度:  ~2x (H100 Tensor Core)
  精度:  下降 <0.5% (业务可接受)
  
E4M3:  推理 (精度高)
E5M2:  KV cache (范围大)
```

## 三、Triton + KServe 平台

### 3.1 Triton Inference Server

```
特性:
  - Nvidia 官方推理服务
  - 多框架 (PyTorch / TF / ONNX / TRT-LLM / vLLM 后端)
  - 动态批处理
  - 模型版本 + AB
  - Metrics / gRPC / HTTP

部署:
docker run --gpus all --rm -p 8000:8000 -p 8001:8001 -p 8002:8002 \
  -v $PWD/model-repo:/models \
  nvcr.io/nvidia/tritonserver:24.10-py3 \
  tritonserver --model-repository=/models

模型仓库格式:
model-repo/
  qwen2.5-72b/
    config.pbtxt          # 模型配置
    1/                     # 版本号
      model.engine         # TensorRT-LLM 引擎
```

### 3.2 KServe（K8s 推理平台 ⭐）

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: qwen2-5-72b, namespace: llm }
spec:
  predictor:
    minReplicas: 1
    maxReplicas: 4
    scaleTarget: 80
    scaleMetric: concurrency
    containers:
      - name: kserve-container
        image: vllm/vllm-openai:v0.6.0
        args:
          - --model=Qwen/Qwen2.5-72B-Instruct
          - --tensor-parallel-size=4
          - --enable-prefix-caching
          - --quantization=fp8
        resources:
          limits: { nvidia.com/gpu: 4, memory: 200Gi, cpu: 32 }
        ports:
          - containerPort: 8000
            protocol: TCP
```

```
KServe 特性:
  - 自动扩缩 (KEDA / Knative)
  - 滚动 / 蓝绿 / Canary
  - Transformer + Predictor 解耦
  - Pipeline (前/后处理 + 推理)
  - 推理图 (InferenceGraph)
  - 集成 Istio / Knative
```

### 3.3 llm-d（CNCF, K8s 原生 ⭐）

```
理念:
  - K8s 原生大模型推理
  - 分布式 KV cache
  - 多副本智能调度 (KV affinity)
  - 与 vLLM / TRT-LLM 集成

主推:
  - Red Hat / IBM / Google
  - 2025 起势头 ⭐

部署:
helm install llm-d llm-d/llm-d -n llm-d
```

## 四、训练分布式

### 4.1 DDP 详解

```python
# DDP 启动
import os
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

def main():
    dist.init_process_group(backend="nccl")
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)
    
    model = MyModel().to(local_rank)
    model = DDP(model, device_ids=[local_rank], find_unused_parameters=False)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    
    train_sampler = torch.utils.data.distributed.DistributedSampler(dataset)
    train_loader = torch.utils.data.DataLoader(dataset, batch_size=4, sampler=train_sampler)
    
    for epoch in range(10):
        train_sampler.set_epoch(epoch)
        for batch in train_loader:
            outputs = model(batch.to(local_rank))
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
    
    dist.destroy_process_group()
```

### 4.2 FSDP（PyTorch 原生大模型）

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import MixedPrecision, BackwardPrefetch
from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy
from functools import partial
from transformers.models.llama.modeling_llama import LlamaDecoderLayer

mp_policy = MixedPrecision(
    param_dtype=torch.bfloat16,
    reduce_dtype=torch.bfloat16,
    buffer_dtype=torch.bfloat16,
)

auto_wrap_policy = partial(
    transformer_auto_wrap_policy,
    transformer_layer_cls={LlamaDecoderLayer},
)

model = LlamaForCausalLM.from_pretrained("meta-llama/Llama-3-70B")
model = FSDP(
    model,
    auto_wrap_policy=auto_wrap_policy,
    mixed_precision=mp_policy,
    backward_prefetch=BackwardPrefetch.BACKWARD_PRE,
    sharding_strategy=ShardingStrategy.FULL_SHARD,
    device_id=torch.cuda.current_device(),
)
```

### 4.3 DeepSpeed ZeRO（高级）

```json
{
  "train_batch_size": 256,
  "train_micro_batch_size_per_gpu": 1,
  "gradient_accumulation_steps": 16,
  "bf16": { "enabled": true },
  "zero_optimization": {
    "stage": 3,
    "offload_optimizer": { "device": "cpu", "pin_memory": true },
    "offload_param": { "device": "cpu", "pin_memory": true },
    "overlap_comm": true,
    "contiguous_gradients": true,
    "reduce_bucket_size": 5e8,
    "stage3_prefetch_bucket_size": 5e8,
    "stage3_param_persistence_threshold": 1e6
  },
  "gradient_clipping": 1.0,
  "wall_clock_breakdown": false,
  "steps_per_print": 10
}
```

```bash
deepspeed --num_gpus 8 --num_nodes 2 \
  --hostfile hostfile \
  train.py --deepspeed ds_config.json
```

### 4.4 Megatron-LM 三维并行

```
TP (Tensor Parallel):
  单层切多卡 (e.g. linear weight 切)
  通信: AllReduce in-layer
  通常 TP=8 (单机)

PP (Pipeline Parallel):
  层切多卡 (block 1-10 on GPU 0-7)
  通信: P2P
  通常 PP=2-4

DP (Data Parallel):
  数据切多卡
  通信: AllReduce gradient
  
组合 (Llama 3 70B 例):
  TP=8 × PP=4 × DP=4 = 128 GPU
```

## 五、训练框架对比

| 框架 | 适合 | 强项 | 弱项 |
|:---|:---|:---|:---|
| **PyTorch DDP** | 小-中模型 (< 10B) | 简单, 官方 | 大模型 OOM |
| **PyTorch FSDP** | 中-大模型 (10-70B) | 官方原生, ZeRO-3 等价 | 调参复杂 |
| **DeepSpeed** | 中-大模型 + CPU offload | ZeRO-Infinity, 老牌 | 与 PyTorch 集成依赖版本 |
| **Megatron-LM** | 70B+ 巨大模型 | 三维并行 TP/PP/DP | 上手陡 |
| **NeMo** | Nvidia 生态 | TP/PP/SP + 多模态 | 锁定 Nvidia |
| **Colossal-AI** | 国产, 70B+ | 多并行 + GeminI 内存 | 社区相对小 |
| **Liger Kernel** | 显存优化 | 内核级优化 | 实验性 |
| **MindSpore** | 华为 Ascend | 国产, MindFormers | 生态较小 |
| **PaddlePaddle** | 百度 + 中文 | 中文场景 + 工具链 | 跨厂兼容 |

## 六、Volcano / Kueue 调度

### 6.1 Volcano（华为, 主流）

```yaml
apiVersion: scheduling.volcano.sh/v1beta1
kind: Queue
metadata: { name: ai-train }
spec:
  weight: 4
  capability:
    nvidia.com/gpu: 32
    cpu: 256
    memory: 1024Gi

---
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata: { name: llama3-70b-pretrain }
spec:
  minAvailable: 16        # Gang scheduling
  schedulerName: volcano
  queue: ai-train
  policies:
    - event: PodEvicted
      action: RestartJob
  tasks:
    - replicas: 16
      name: trainer
      template:
        spec:
          containers:
            - name: trainer
              image: harbor.example.com/trainer:v1
              resources:
                limits: { nvidia.com/gpu: 8, rdma/hca: 1 }
              command: ["torchrun", "--nproc_per_node=8", "train.py"]
          nodeSelector: { gpu-type: h100, ib: "true" }
```

### 6.2 Kueue（kubernetes-sigs ⭐）

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata: { name: h100 }
spec:
  nodeLabels: { gpu-type: h100 }

---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata: { name: ai-train }
spec:
  resourceGroups:
    - coveredResources: [nvidia.com/gpu, cpu, memory]
      flavors:
        - name: h100
          resources:
            - { name: nvidia.com/gpu, nominalQuota: 32 }
            - { name: cpu, nominalQuota: 256 }
            - { name: memory, nominalQuota: 1024Gi }

---
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata: { namespace: ml-team-a, name: queue-a }
spec:
  clusterQueue: ai-train
```

```
Kueue 特性:
  - K8s 官方 (kubernetes-sigs)
  - Cohort / Preemption / Borrowing
  - Multi-cluster (Kueue + Karmada)
  - 与 Volcano 互补
```

### 6.3 调度对比

| 调度器 | 适合 | 强项 |
|:---|:---|:---|
| **Volcano** | 训练 + HPC | Gang sched, 全功能, 国产 |
| **Kueue** | 现代 K8s | 官方, 配额借用, Cohort |
| **Yunikorn** | 类 YARN | 多租户队列 |
| **Slurm Operator** | HPC 迁移 | 兼容性好 |

## 七、MIG / MPS / GPU 虚拟化

### 7.1 MIG (Multi-Instance GPU)

```bash
# 启用 MIG (H100 / A100)
nvidia-smi -i 0 -mig 1

# 列举 GPU Instance profile
nvidia-smi mig -lgip

# 创建 7 个 1g.10gb 实例
nvidia-smi mig -cgi 19,19,19,19,19,19,19 -C
```

```
适合:
  - 多租户推理 (小模型)
  - 开发 / 测试
  - 隔离 (硬件级)

不适合:
  - 大模型训练 (隔离低利用率)
  - NVLink 通信场景
```

### 7.2 MPS (Multi-Process Service)

```bash
# 启动 MPS 守护
nvidia-cuda-mps-control -d

# 共享 GPU (软隔离)
CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps nvidia-smi
```

### 7.3 GPU Virtualization（高级）

```
HAMi (国产, 阿里) ⭐
  - 软虚拟化 (显存 + 算力切片)
  - 适合开发 / 推理共享
  - K8s 原生
  
vGPU (Nvidia 商业)
NebulaGraph 拓扑感知
```

## 八、网络 (RoCE / IB)

### 8.1 InfiniBand

```
特性:
  - HDR 200G / NDR 400G ⭐
  - RDMA 零拷贝
  - SHARP (在网计算)
  - 大模型必备

软件:
  Mellanox OFED / MOFED
  NCCL 自动使用 (NCCL_IB_DISABLE=0)

测试:
ib_write_bw -F --report_gbits
```

### 8.2 RoCE v2

```
特性:
  - 走以太网 (100/200/400GbE)
  - RDMA over Converged Ethernet
  - 比 IB 便宜
  - 需 DCB / PFC / ECN

NCCL 环境:
export NCCL_IB_DISABLE=0
export NCCL_IB_HCA=mlx5_0,mlx5_1
export NCCL_IB_GID_INDEX=3
export NCCL_NET_GDR_LEVEL=2
```

### 8.3 NCCL 调优

```
环境变量:
  NCCL_DEBUG=INFO
  NCCL_IB_HCA=mlx5
  NCCL_SOCKET_IFNAME=eth0
  NCCL_NET_GDR_LEVEL=2     # GPUDirect RDMA
  NCCL_P2P_LEVEL=NVL       # NVLink 直连
  NCCL_ALGO=Ring,Tree
  
工具:
  nccl-tests (官方 benchmark)
  all_reduce_perf -b 8 -e 8G -f 2 -g 8
```

## 九、分布式存储

```
JuiceFS ⭐         POSIX + 对象后端 (Redis 元数据), 简单
CubeFS              国产 CNCF, 高性能
Lustre              传统 HPC, 极致带宽
GPFS / Spectrum Scale  IBM 商业
BeeGFS              开源 HPC
Alluxio             缓存层 (热加速)

挂载:
juicefs mount redis://meta:6379/1 /mnt/ai-data
```

```yaml
# K8s PV (JuiceFS CSI)
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: models-pvc }
spec:
  accessModes: [ReadWriteMany]
  storageClassName: juicefs-sc
  resources: { requests: { storage: 10Ti } }
```

## 十、LangChain / LlamaIndex（RAG 进阶）

### 10.1 LangChain

```python
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-zh-v1.5")
vectorstore = PGVector(
    embedding_function=embeddings,
    collection_name="docs",
    connection_string="postgresql+psycopg2://app:pwd@pg:5432/rag"
)

llm = ChatOpenAI(
    base_url="http://vllm-qwen:8000/v1",
    api_key="sk-xxx",
    model="Qwen/Qwen2.5-72B-Instruct"
)

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
)

print(qa.run("如何配置 K8s GPU?"))
```

### 10.2 LlamaIndex

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.vector_stores.postgres import PGVectorStore

documents = SimpleDirectoryReader("docs/").load_data()

vector_store = PGVectorStore.from_params(
    database="rag", host="pg", port=5432,
    user="app", password="pwd",
    table_name="llamaindex_docs",
    embed_dim=1024,
)

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-zh-v1.5")
llm = OpenAILike(api_base="http://vllm-qwen:8000/v1", api_key="sk-xxx", model="qwen-72b")

index = VectorStoreIndex.from_documents(
    documents, vector_store=vector_store, embed_model=embed_model
)
query_engine = index.as_query_engine(llm=llm)
print(query_engine.query("K8s 调度策略有哪些?"))
```

## 十一、国产昇腾栈

```
硬件:        华为 Ascend 910B/910C ⭐ (国产之光)
驱动:        Ascend HDK + CANN 8.0
框架:        MindSpore (国产) / PyTorch + torch_npu / PaddlePaddle
分布式:      MindFormers / DeepSpeed (适配)
推理:        MindIE / LMDeploy ⭐
量化:        MindIE 量化 + GPTQ-style
模型:        Qwen, DeepSeek, GLM 都已适配 Ascend ⭐

K8s:
  Ascend Operator (类 Nvidia GPU Operator)
  资源: huawei.com/Ascend910

监控:
  npu-smi + Ascend Exporter
```

```bash
# LMDeploy on Ascend
pip install lmdeploy
lmdeploy serve api_server Qwen/Qwen2.5-7B-Instruct \
  --backend pytorch --device ascend --tp 1 --port 23333

# MindIE (华为官方)
mindie-server --model-path /path/to/qwen2.5-7b \
  --tensor-parallel-size 2 --port 1025
```

## 十二、模型注册 + 治理

```
模型注册:
  MLflow Model Registry ⭐
  Harbor (LFS, OCI Artifact) ⭐
  Hugging Face Hub Enterprise
  Nexus / 阿里 PAI Model Registry

实验追踪:
  Weights & Biases (W&B) ⭐
  MLflow ⭐
  Determined AI
  ClearML

模型卡 (Model Card):
  - 训练数据 / 评测
  - 偏见 / 公平性
  - 版本 / Owner
  - 上线状态

工作流:
  实验 → W&B/MLflow → 注册 → 推理服务
  CI/CD: GitOps (ArgoCD + KServe)
```

## 十三、监控告警必备

```
Prometheus exporter:
  dcgm-exporter ⭐         GPU
  nvidia-mig-exporter
  npu-exporter (昇腾)
  triton-prometheus       Triton 内置
  vllm-prometheus         vLLM /metrics
  
关键指标:
☐ GPU 利用率 / 显存占用
☐ Tensor Core / SM utilization
☐ GPU 温度 / 功耗
☐ NVLink / IB / RoCE 带宽
☐ vLLM: time_to_first_token, time_per_output_token, throughput, num_requests_running, num_requests_waiting
☐ Triton: inference_count, queue_time, compute_time
☐ KV cache 占用 / hit rate
☐ NCCL 通信时间
☐ 训练: loss / lr / grad norm

告警:
☐ GPU 温度 > 85°C
☐ 显存 > 95%
☐ 训练 loss NaN
☐ 推理 P99 latency > SLO
☐ GPU Xid 错误 (硬件)
☐ NCCL 超时
```

## 十四、典型坑（进阶）

| 坑 | 建议 |
|:---|:---|
| **vLLM OOM** | gpu-memory-utilization 调低 / 量化 / 减 max-model-len |
| **vLLM 启动慢** | 模型预加载 / 镜像内置 / 共享 PVC |
| **DDP 通信慢** | 检查 IB/RoCE + NCCL 配置 |
| **FSDP 显存不省** | 调 sharding_strategy = FULL_SHARD |
| **DeepSpeed ZeRO-3 慢** | offload 关闭 / 调 bucket size |
| **Megatron NCCL hang** | 检查 GPU 拓扑 + NVLink |
| **量化后精度掉太多** | 校准集多样化 / 换 AWQ / 降量化层 |
| **Triton 模型加载失败** | config.pbtxt 不对 / TRT-LLM 版本 |
| **KServe 滚动失败** | maxReplicas 不足 / 镜像拉取慢 |
| **GPU 节点不平衡** | Volcano / topology-aware |
| **存储 IO 瓶颈** | JuiceFS + Alluxio / NVMe local cache |
| **昇腾兼容性** | torch_npu 版本 + MindFormers / LMDeploy |

## 十五、Checklist（进阶）

```
推理:
☐ vLLM 生产参数 (TP/PP/quant/prefix/chunked)
☐ AWQ / GPTQ / FP8 量化路径
☐ KServe + GitOps 上线
☐ Multi-LoRA 多租户
☐ Speculative decoding 加速

训练:
☐ DDP 单机 + FSDP 中大模型
☐ DeepSpeed ZeRO-3 (CPU offload)
☐ Megatron 3D 并行 (70B+)
☐ 数据流: HF Datasets + Tokenizer + DataLoader

调度:
☐ Volcano / Kueue 一种
☐ Gang scheduling + Queue
☐ Topology aware

GPU 共享:
☐ MIG (硬隔离) / HAMi (软切片)
☐ MPS 推理共享

网络:
☐ IB 或 RoCE v2 + NCCL 调优
☐ nccl-tests 基准
☐ GPUDirect RDMA

存储:
☐ JuiceFS / CubeFS / Lustre 一种
☐ Alluxio 缓存
☐ 模型 PVC ReadWriteMany

平台:
☐ Triton + KServe / llm-d 选一
☐ MLflow / W&B 实验追踪
☐ Harbor + LFS 模型注册
☐ ArgoCD GitOps 上线

国产:
☐ Ascend 910B + CANN + MindIE / LMDeploy
☐ 国产模型适配 (Qwen / DeepSeek / GLM)

RAG:
☐ LangChain + pgvector / Milvus
☐ Embedding (bge-large-zh)
☐ Reranker

监控:
☐ dcgm-exporter + vLLM /metrics + Triton metrics
☐ GPU 温度 / 显存 / 利用率 关键告警
```

## 十六、推荐栈（进阶）

```
硬件:        Nvidia H100/H200 SXM5 + InfiniBand NDR 400G + JuiceFS
国产硬件:    华为 Ascend 910B/910C + RoCE
框架:        PyTorch 2.x + FSDP / DeepSpeed / Megatron-LM
推理:        vLLM ⭐ + SGLang / TGI / TRT-LLM
量化:        AWQ / GPTQ / FP8
平台:        KServe ⭐ / Triton / llm-d (CNCF)
调度:        Volcano + Kueue 双栈
模型注册:    MLflow + Harbor LFS
实验追踪:    W&B / MLflow
监控:        DCGM Exporter + Prometheus + Grafana
存储:        JuiceFS + Alluxio 缓存
RAG:        LangChain / LlamaIndex + pgvector / Milvus
国产推理:   LMDeploy / MindIE
模型:        Qwen 2.5/3 + DeepSeek V3/R1 + GLM-4
```

> 📖 **核心判断**：AI 基础设施进阶 = **vLLM 生产化(TP/PP/Prefix/FP8) + 量化(AWQ/GPTQ/FP8) + KServe/Triton 推理平台 + DDP/FSDP/DeepSpeed/Megatron 训练 + Volcano/Kueue 调度 + IB/RoCE 网络 + JuiceFS 存储 + RAG(LangChain/pgvector) + 国产昇腾(MindIE/LMDeploy) + MLflow/Harbor 模型注册**。能跑通"K8s + GPU Operator + Volcano + vLLM + KServe + 量化模型 + RAG + pgvector + 监控告警"完整 LLM 推理平台，就具备 AI 平台运维工程师能力。
