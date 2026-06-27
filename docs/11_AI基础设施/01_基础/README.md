# 基础

> AI 基础设施基础 = **GPU/NPU 硬件 + CUDA/ROCm/CANN 软件栈 + PyTorch/TensorFlow + 模型格式(safetensors/GGUF/ONNX) + 推理引擎(vLLM/TGI/llama.cpp/Ollama) + 训练框架(Megatron/DeepSpeed/FSDP) + 数据集与 tokenizer + 分布式通信(NCCL/Gloo) + K8s GPU 调度 + Hugging Face 生态**。本章面向 AI 平台运维入门。

## 一、AI 基础设施全景

```
硬件层:
  GPU         Nvidia H100/H200/B200/A100 ⭐
  GPU 国产    华为昇腾 Ascend 910B/910C ⭐
              壁仞 BR100 / 寒武纪 MLU / 海光 DCU
              摩尔线程 MTT / 燧原 Enflame
  NPU         (Ascend / Edge TPU / 高通 NPU)
  网络        InfiniBand (NDR 400G) / RoCE v2
  存储        NVMe SSD / 并行文件系统 (Lustre/GPFS/JuiceFS)

软件栈:
  CUDA 12.x / cuDNN 9 / NCCL 2.x      Nvidia
  ROCm 6 / RCCL                        AMD
  CANN 8 / HCCL / MindSpore           华为昇腾 ⭐
  ToolKit / BangC                     寒武纪
  
框架:
  PyTorch 2.x ⭐  / TensorFlow 2 / JAX
  MindSpore (华为) / PaddlePaddle (百度) / OneFlow

模型格式:
  safetensors ⭐  (HuggingFace 推荐)
  GGUF ⭐ (llama.cpp 量化)
  GGML (旧)
  ONNX (跨框架)
  TensorRT engine (Nvidia 部署)

训练框架:
  PyTorch FSDP ⭐
  DeepSpeed (ZeRO 1/2/3) ⭐
  Megatron-LM ⭐ (大模型分布式)
  Horovod (老)
  Colossal-AI / Liger Kernel
  
推理引擎:
  vLLM ⭐ (高吞吐, PagedAttention)
  Text Generation Inference (TGI) ⭐
  TensorRT-LLM (Nvidia 极致)
  llama.cpp ⭐ (CPU/边缘 GGUF)
  Ollama ⭐ (个人/开发)
  SGLang ⭐ (新, 多模态强)
  llm-d ⭐ (CNCF, K8s 原生)
  LMDeploy (国产) / FastChat / OpenLLM

服务化:
  Triton Inference Server (Nvidia)
  KServe / Seldon Core (K8s)
  Modal / Replicate / Together (SaaS)

数据 + Embedding:
  Hugging Face Datasets ⭐
  Wandb / MLflow / Determined (实验)
  pgvector / Milvus / Qdrant (向量)
  LangChain / LlamaIndex (RAG)

调度:
  K8s + Volcano / Yunikorn ⭐
  Kueue (K8s 原生, kubernetes-sigs)
  Ray ⭐ (任务级)
  Slurm (HPC 老)
  
平台:
  Kubeflow ⭐ / Determined / MLflow
  阿里 PAI / 华为 ModelArts / 字节 Volcano Engine
  KAITO / vCluster (新)
```

## 二、GPU 硬件基础

### 2.1 Nvidia GPU 代际

```
代际             架构        FP16        FP8/BF16    HBM         典型卡
─────────────────────────────────────────────────────────────────────
2017 Volta       V100        ~125 TFLOPS  无         16/32 GB    V100
2020 Ampere      A100        ~312 TFLOPS  无         40/80 GB    A100  ⭐
2022 Hopper      H100        ~989 TFLOPS  ~1979      80 GB       H100  ⭐
2024 Blackwell   B100/B200   ~5000+       ~10000+    192 GB      B200, GB200
2025 Blackwell+  B300         (旗舰)                              GB300

关键参数:
  Tensor Core 算力 (FP16/BF16/FP8/INT8)
  HBM 容量 (训练大模型必备)
  NVLink / NVSwitch 带宽 (多卡互联)
  PCIe Gen / SXM 形态
```

### 2.2 国产 GPU/NPU

```
华为 Ascend 910B/910C ⭐ (国产之光)
  - 64GB HBM / NPU
  - CANN 8.0
  - MindSpore + PyTorch 兼容
  - 大模型训练 (PanGu / Qwen / 智谱)
  
壁仞 BR100/104    (国际化中)
寒武纪 MLU370/590 (商用)
海光 DCU Z100/K100 (类 CUDA, AMD ROCm 兼容)
摩尔线程 MTT S80/S4000 (消费 + 数据中心)
燧原 Enflame (云燧 T20/T21)
天数 Iluvatar (训推一体)

国产推理芯片:
  瀚博 (Hapac)
  比特大陆 BM1684X
  寒武纪 MLU220 (边缘)
```

### 2.3 nvidia-smi / 监控

```bash
nvidia-smi
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu \
           --format=csv -l 2
nvidia-smi topo -m                    # NVLink 拓扑
nvidia-smi nvlink -s                  # NVLink 状态

# DCGM (高级监控, 推荐生产)
docker run --gpus all nvcr.io/nvidia/k8s/dcgm-exporter:3.3.7-3.4.2-ubuntu22.04 \
  dcgm-exporter

# 华为昇腾
npu-smi info
```

## 三、PyTorch 基础

### 3.1 安装

```bash
# CUDA 12.1
pip install torch==2.4.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# ROCm
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0

# CPU
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 华为昇腾
pip install torch_npu
```

### 3.2 验证 GPU

```python
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.device_count())
print(torch.cuda.get_device_name(0))

# 简单矩阵乘
x = torch.randn(2048, 2048, device='cuda')
y = torch.randn(2048, 2048, device='cuda')
z = x @ y
print(z.shape, z.device)

# 华为昇腾
import torch_npu
print(torch.npu.is_available())
print(torch.npu.device_count())
```

### 3.3 数据并行 (DP / DDP / FSDP)

```python
# DistributedDataParallel (DDP) — 数据并行 (主流)
import torch, torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

dist.init_process_group(backend='nccl')
local_rank = int(os.environ['LOCAL_RANK'])
torch.cuda.set_device(local_rank)

model = MyModel().cuda(local_rank)
model = DDP(model, device_ids=[local_rank])
```

```bash
# 启动 (8 卡单机)
torchrun --nproc_per_node=8 train.py
# 多机 (2 节点 × 8 卡)
torchrun --nnodes=2 --nproc_per_node=8 \
  --rdzv_id=job1 --rdzv_backend=c10d --rdzv_endpoint=master:29500 \
  train.py
```

## 四、Hugging Face 生态

### 4.1 Transformers

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "Qwen/Qwen2.5-7B-Instruct"   # 通义千问 ⭐
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

messages = [{"role": "user", "content": "用 30 个字介绍 K8s"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=128)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### 4.2 模型下载

```bash
# HF CLI
pip install -U huggingface_hub
huggingface-cli login   # token
huggingface-cli download Qwen/Qwen2.5-7B-Instruct --local-dir ./qwen2.5-7b

# 国内镜像
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download Qwen/Qwen2.5-7B-Instruct

# ModelScope (阿里, 国内官方)
pip install modelscope
from modelscope import snapshot_download
snapshot_download('Qwen/Qwen2.5-7B-Instruct', cache_dir='./models')
```

### 4.3 主流开源模型（2026）

```
LLM (通用):
  Qwen 2.5 (阿里) ⭐⭐    7B/14B/32B/72B
  Qwen3 (阿里 2025) ⭐⭐
  DeepSeek V3 / R1 (深度求索) ⭐⭐   MoE 推理王者
  Llama 3.3/4 (Meta) ⭐
  Mistral / Mixtral
  GLM-4 (智谱) ⭐
  InternLM3 (上海 AI Lab) ⭐
  Yi (零一万物)
  
代码:
  DeepSeek-Coder V2 ⭐
  Qwen2.5-Coder ⭐
  StarCoder2

多模态:
  Qwen-VL ⭐
  InternVL ⭐
  LLaVA / CogVLM
  
Embedding:
  bge-large-zh ⭐ (北智源)
  M3E (国产)
  jina-embeddings-v3
```

## 五、模型格式

### 5.1 safetensors（推荐）

```
特点:
  - 安全 (无 pickle 反序列化漏洞)
  - 快 (mmap)
  - 通用 (PyTorch/TF/JAX)
  - 元数据 (BF16/FP16/INT8)

用法:
from safetensors.torch import load_file, save_file
state_dict = load_file("model.safetensors")
save_file(state_dict, "out.safetensors")
```

### 5.2 GGUF（llama.cpp）

```
特点:
  - 量化 (Q4_0 / Q4_K_M / Q5_K_M / Q8_0)
  - CPU/GPU 推理
  - 单文件
  - 边缘部署友好

转换:
python convert_hf_to_gguf.py /path/to/qwen2.5-7b --outfile qwen2.5-7b.f16.gguf
./llama-quantize qwen2.5-7b.f16.gguf qwen2.5-7b.Q4_K_M.gguf Q4_K_M
```

### 5.3 ONNX

```
特点:
  - 跨框架 (PyTorch → TF → 嵌入式)
  - ONNX Runtime 推理
  - 适合移动 / 边缘

转换:
torch.onnx.export(model, dummy_input, "model.onnx", opset_version=17)
```

### 5.4 TensorRT-LLM

```
特点:
  - Nvidia 极致性能 (compile-time optimization)
  - 多 GPU + FP8 + KV cache
  - Triton 集成

工作流:
HuggingFace → TensorRT-LLM Build (.engine) → Triton 部署
```

## 六、推理引擎

### 6.1 vLLM（高吞吐 ⭐）

```bash
pip install vllm

# 启动 OpenAI 兼容服务
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 32768 \
  --port 8000

# 调用 (OpenAI SDK 兼容)
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role":"user","content":"hi"}]
  }'
```

```
特性:
  PagedAttention (KV cache 分页)
  Continuous Batching
  支持 Tensor Parallel + Pipeline Parallel
  Speculative Decoding
  AWQ / GPTQ / FP8 量化
  Multi-LoRA
  Prefix Caching
```

### 6.2 TGI（Hugging Face）

```bash
docker run --gpus all -p 8080:80 \
  -v $PWD/data:/data \
  ghcr.io/huggingface/text-generation-inference:3.0 \
  --model-id Qwen/Qwen2.5-7B-Instruct \
  --num-shard 2 \
  --max-input-length 8192 \
  --max-total-tokens 32768
```

### 6.3 llama.cpp（CPU/边缘）

```bash
# 编译
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make -j

# 推理
./llama-server -m qwen2.5-7b.Q4_K_M.gguf \
  -c 32768 --port 8080 -ngl 99   # ngl=GPU layers
```

### 6.4 Ollama（最易用 ⭐）

```bash
# 安装
curl -fsSL https://ollama.com/install.sh | sh

# 拉模型
ollama pull qwen2.5:7b
ollama pull deepseek-v3
ollama pull llama3.2:3b

# 运行
ollama run qwen2.5:7b "用 50 字介绍 vLLM"

# OpenAI 兼容
curl http://localhost:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"hi"}]}'
```

### 6.5 SGLang（新势力）

```
特性:
  - 多模态 (图/视频)
  - 复杂控制流 (思维链 / 工具调用)
  - 比 vLLM 在某些场景快

用法:
pip install sglang[all]
python -m sglang.launch_server --model-path Qwen/Qwen2.5-VL-7B-Instruct --port 30000
```

### 6.6 选型

| 场景 | 推荐 |
|:---|:---|
| **生产高吞吐 / Multi-tenancy** | vLLM ⭐ |
| **Hugging Face 生态友好** | TGI |
| **Nvidia 极致性能 (FP8)** | TensorRT-LLM |
| **CPU / 边缘 / 个人** | llama.cpp |
| **开发 / 试用最简** | Ollama ⭐ |
| **多模态 / 复杂控制流** | SGLang |
| **K8s 原生 + 平台化** | llm-d ⭐ / KServe |
| **国产 NPU** | LMDeploy / MindIE |

## 七、训练框架

### 7.1 PyTorch FSDP

```python
# Fully Sharded Data Parallel (替代 DeepSpeed ZeRO)
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp.wrap import size_based_auto_wrap_policy

model = MyLargeModel()
model = FSDP(
    model,
    auto_wrap_policy=size_based_auto_wrap_policy,
    mixed_precision=MixedPrecision(param_dtype=torch.bfloat16),
)
```

### 7.2 DeepSpeed ZeRO

```yaml
# ds_config.json
{
  "train_micro_batch_size_per_gpu": 4,
  "gradient_accumulation_steps": 8,
  "bf16": {"enabled": true},
  "zero_optimization": {
    "stage": 3,
    "offload_optimizer": {"device": "cpu"},
    "offload_param": {"device": "cpu"}
  }
}
```

```bash
deepspeed --num_gpus 8 train.py --deepspeed ds_config.json
```

### 7.3 Megatron-LM

```
适合: 70B+ 大模型预训练
特性: TP (Tensor Parallel) + PP (Pipeline) + DP 三维并行
工具: NeMo (Nvidia) / Megatron-DeepSpeed
```

## 八、K8s GPU 调度

### 8.1 GPU Operator (Nvidia)

```bash
helm install nvidia/gpu-operator -n gpu-operator --create-namespace
```

部署后自动：

```
NVIDIA Driver
CUDA Container Toolkit
Device Plugin (GPU 资源 nvidia.com/gpu)
DCGM Exporter (监控)
GPU Feature Discovery
MIG Manager
```

### 8.2 Pod 申请 GPU

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: trainer
      image: pytorch/pytorch:2.4.0-cuda12.1
      resources:
        limits:
          nvidia.com/gpu: 2
      command: ["python", "train.py"]
```

### 8.3 国产昇腾

```bash
# CANN Operator
kubectl apply -f https://ascend.gitee.com/ascend-deployer.yaml

# Pod 申请
resources:
  limits:
    huawei.com/Ascend910: 2
```

### 8.4 Volcano 批调度

```yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata: { name: train-job }
spec:
  minAvailable: 4    # Gang scheduling
  schedulerName: volcano
  queue: ai-train
  tasks:
    - replicas: 4
      name: worker
      template:
        spec:
          containers:
            - name: trainer
              image: harbor.example.com/trainer:v1
              resources: { limits: { nvidia.com/gpu: 1 } }
              command: ["torchrun", "--nproc_per_node=1", "train.py"]
```

## 九、向量数据库 + RAG 入门

```python
# pgvector
import psycopg2
conn = psycopg2.connect("dbname=app")
cur = conn.cursor()
cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
cur.execute("""
  CREATE TABLE IF NOT EXISTS docs (
    id BIGSERIAL PRIMARY KEY,
    content TEXT,
    embedding VECTOR(768)
  )
""")
cur.execute("CREATE INDEX ON docs USING ivfflat (embedding vector_cosine_ops) WITH (lists=100)")

# Embedding (bge-large-zh)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
emb = model.encode("K8s 调度器原理")

cur.execute("INSERT INTO docs(content, embedding) VALUES (%s, %s)", ("文档内容", emb.tolist()))

# 检索
q_emb = model.encode("k8s 调度策略").tolist()
cur.execute("SELECT id, content FROM docs ORDER BY embedding <=> %s::vector LIMIT 5", (q_emb,))
print(cur.fetchall())
```

## 十、必会工具 / 命令清单

```bash
# 系统 + 监控
nvidia-smi
nvidia-smi dmon -i 0 -s u    # 利用率/带宽
dcgmi diag -r 4               # DCGM 健康检查
nvtop                         # 类 htop
gpustat -i 1

# Python / Pip
pip install torch transformers accelerate vllm
huggingface-cli download <model>

# 模型转换
python convert_hf_to_gguf.py  # llama.cpp
trtllm-build                  # TensorRT-LLM

# 推理
vllm serve <model>
ollama run <model>
docker run ghcr.io/huggingface/text-generation-inference

# K8s GPU
kubectl describe node <gpu-node> | grep nvidia
kubectl logs -n gpu-operator -l app=nvidia-device-plugin
kubectl get pods -A -o json | jq '.items[] | select(.spec.containers[].resources.limits."nvidia.com/gpu")'
```

## 十一、入门 20 题

```
1.  GPU 与 CPU 区别 / 何时用 GPU
2.  Nvidia H100 vs A100 关键差异
3.  FP32 / FP16 / BF16 / FP8 / INT8 区别
4.  HBM 是什么 / 为啥重要
5.  CUDA / cuDNN / NCCL 三者关系
6.  PyTorch DDP vs FSDP 区别
7.  DeepSpeed ZeRO 1/2/3 区别
8.  Megatron-LM 三维并行 (TP/PP/DP)
9.  safetensors 比 pickle 优势
10. GGUF / ONNX / TRT engine 区别
11. vLLM PagedAttention 原理
12. Continuous Batching 是什么
13. KV cache 是什么 / 多大
14. AWQ / GPTQ / SmoothQuant 量化区别
15. K8s 如何调度 GPU (Device Plugin)
16. MIG 是什么 / 何时用
17. RoCE / InfiniBand 区别
18. Volcano / Yunikorn / Kueue 调度器
19. Embedding / 向量数据库 (pgvector/Milvus)
20. RAG 流程 (Embedding + Retrieval + LLM)
```

## 十二、推荐栈（基础）

```
硬件:        Nvidia H100/A100 + InfiniBand + NVMe
国产硬件:    华为昇腾 910B/910C + RoCE
框架:        PyTorch 2.x ⭐
模型:        Qwen 2.5/3 ⭐ + DeepSeek V3/R1 ⭐ + Llama 3
格式:        safetensors (训练) + GGUF (边缘)
推理:        vLLM ⭐ (生产) + Ollama (开发)
训练:        DeepSpeed ZeRO / PyTorch FSDP
K8s:         GPU Operator + Volcano
向量:        pgvector / Milvus
监控:        DCGM Exporter + nvtop
```

## 十三、学习路径

```
入门（1-3 月）:
  1. PyTorch + Hugging Face 拉模型推理
  2. vLLM / Ollama 部署 (OpenAI 兼容)
  3. GPU Operator + K8s 调度
  4. pgvector + RAG demo
  5. 20 题
  
进阶（3-12 月, 见 02_进阶）:
  6. DDP / FSDP 多机训练
  7. DeepSpeed ZeRO 大模型
  8. 量化 (GPTQ / AWQ / FP8)
  9. vLLM 进阶 (TP/PP/Prefix Cache)
  10. Triton / KServe 推理平台
  11. Volcano / Kueue 调度
  12. 国产昇腾 MindIE / LMDeploy
```

> 📖 **核心判断**：AI 基础设施基础 = **GPU(H100/Ascend) + PyTorch/HF + 模型格式(safetensors/GGUF) + 推理(vLLM/Ollama) + 训练(DDP/FSDP/DeepSpeed) + K8s GPU 调度(Operator/Volcano) + 向量/RAG**。能跑通"K8s + GPU + vLLM + Qwen2.5 + pgvector + RAG demo"全链路，就具备 AI 平台运维入门能力。
