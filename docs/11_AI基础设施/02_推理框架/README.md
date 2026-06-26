# 推理框架

> 推理框架是 GPU 与业务之间的核心。**vLLM、SGLang、TGI、TensorRT-LLM、llama.cpp** 是 2025 五大主流。**选错框架成本翻倍，吞吐量减半**。本章给完整选型矩阵 + 各家深度调优指南。

## 一、五大框架选型矩阵

| 框架 | 主导 | 长项 | 短板 | 适合 |
|:---|:---|:---|:---|:---|
| **vLLM** ⭐⭐⭐⭐⭐ | UC Berkeley | PagedAttention 鼻祖，生态最全 | 个别 op 落后 SGLang | 通用首选 |
| **SGLang** ⭐⭐⭐⭐⭐ | LMSYS | RadixAttention 复用 prefix，Structured output | 文档少，新 | 高吞吐 / Agent 场景 |
| **TGI** ⭐⭐⭐⭐ | HuggingFace | 工业级稳定，K8s 友好 | 性能略低于 vLLM | 企业级 |
| **TensorRT-LLM** ⭐⭐⭐⭐ | NVIDIA | FP8 极致优化，速度最快 | 模型支持少，部署复杂 | NV 死忠 + 大模型生产 |
| **llama.cpp** ⭐⭐⭐⭐ | ggerganov | CPU+GPU 混合，量化丰富 | 多卡支持弱 | 边缘 / 桌面 / 小规模 |
| **llm-d** | Google/IBM | PD 分离、多副本 | 早期 | 大规模分布式 (2025+) |
| **MLC-LLM** | TVM | 多端 (mobile/web/edge) | 上手陡 | 跨平台部署 |
| **DeepSpeed-FastGen** | Microsoft | Dynamic SplitFuse | 维护减少 | 老项目 |
| **Triton Inference Server** | NVIDIA | 通用推理服务 (CV/NLP/LLM) | LLM 特化少 | 多模型 / 多模态 |

## 二、核心技术对比

### 2.1 关键技术速查

| 技术 | vLLM | SGLang | TGI | TRT-LLM | llama.cpp |
|:---|:---:|:---:|:---:|:---:|:---:|
| PagedAttention | ✅ 原创 | ✅ | ✅ | ✅ | - |
| RadixAttention (prefix 复用) | 实验 | ⭐ 原创 | - | - | - |
| Continuous Batching | ✅ | ✅ | ✅ | ✅ | ✅ |
| Chunked Prefill | ✅ | ✅ | ✅ | ✅ | - |
| Prefix Caching | ✅ | ✅ RadixTree | ✅ | ✅ | - |
| Speculative Decoding | ✅ | ✅ | ✅ | ✅ EAGLE-3 | - |
| Tensor Parallel | ✅ | ✅ | ✅ | ✅ | ⚠️ 弱 |
| Pipeline Parallel | ✅ | ✅ | ✅ | ✅ | - |
| FP8 | ✅ H100+ | ✅ | ✅ | ⭐ 最强 | - |
| INT4 (AWQ/GPTQ) | ✅ | ✅ | ✅ | ✅ | ⭐ GGUF |
| KV Cache 量化 | ✅ FP8 | ✅ | ✅ | ✅ | - |
| LoRA 多适配 | ✅ Multi-LoRA | ✅ | ✅ | ⚠️ | - |
| 结构化输出 (JSON/Regex) | ✅ Outlines | ⭐ 原生 | ✅ | ⚠️ | ✅ Grammar |
| Function Calling | ✅ | ✅ | ✅ | - | - |
| Multimodal (Vision) | ✅ | ✅ | ✅ | ✅ | ✅ |
| OpenAI API | ✅ | ✅ | ✅ | ⚠️ 需 wrapper | ✅ |
| Disaggregated PD | ✅ 1.0+ | ✅ | 实验 | - | - |

### 2.2 性能 Benchmark（H100, Llama-3-70B）

```
单 H100 80G (TP=1, AWQ INT4):
  vLLM      1450 tok/s (输出)
  SGLang     1520 tok/s
  TGI        1380 tok/s
  TRT-LLM   1680 tok/s (FP8)
  
2 × H100 80G (TP=2, FP16):
  vLLM      2800 tok/s
  SGLang     2950 tok/s
  TGI        2650 tok/s
  TRT-LLM   3400 tok/s (FP8)
  
TTFT (Time-to-First-Token, 4K context):
  vLLM       150 ms
  SGLang     130 ms (RadixCache 命中时 < 50ms)
  TGI        180 ms
  TRT-LLM   140 ms

* 上述为参考值，与硬件/数据集/参数高度相关
```

## 三、vLLM 深度

### 3.1 安装

```bash
# pip (官方)
pip install vllm                       # 默认带 PyTorch
# 或 uv
uv pip install vllm

# Docker
docker run --gpus all -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model meta-llama/Meta-Llama-3-70B-Instruct \
  --tensor-parallel-size 2 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.9
```

### 3.2 启动参数（核心 30 个）

```bash
vllm serve <model> \
  # 模型
  --model meta-llama/Meta-Llama-3-70B-Instruct \
  --tokenizer-mode auto \
  --trust-remote-code \
  --revision main \
  --download-dir /data/models \
  
  # 并行
  --tensor-parallel-size 2 \           # TP, 单节点多卡
  --pipeline-parallel-size 1 \         # PP, 跨节点
  --data-parallel-size 1 \             # DP
  
  # 精度
  --dtype bfloat16 \                   # auto/half/float16/bfloat16/float
  --quantization awq \                 # awq/gptq/fp8/none
  --kv-cache-dtype fp8 \               # fp8 减半 KV
  
  # 上下文/批
  --max-model-len 32768 \              # 最大上下文（含 prompt+gen）
  --max-num-seqs 256 \                 # 最大并发请求
  --max-num-batched-tokens 8192 \      # 单步 batch 最大 token
  --gpu-memory-utilization 0.9 \       # 显存利用率（KV cache 占用）
  
  # 调度
  --enable-chunked-prefill \           # 长序列分块（推荐）
  --enable-prefix-caching \             # Prefix 缓存（多次相同 prompt 加速）
  --num-scheduler-steps 1 \            # multi-step scheduling
  
  # 推测解码
  --speculative-model facebook/opt-125m \
  --num-speculative-tokens 5 \
  
  # LoRA
  --enable-lora \
  --max-loras 8 \
  --max-lora-rank 64 \
  --lora-modules sql=path1 chat=path2 \
  
  # 服务
  --host 0.0.0.0 --port 8000 \
  --api-key your-key \
  --served-model-name llama3-70b \
  --chat-template /path/to/chat_template.jinja \
  --max-log-len 100 \                  # log 截断
  --disable-log-requests \             # 高并发关日志
  
  # 性能
  --disable-custom-all-reduce \        # 跨 NUMA 时
  --swap-space 16                      # CPU offload 大小 GB
```

### 3.3 PagedAttention 原理（必懂）

```
传统 KV Cache:
  每个请求分配大段连续显存 → 碎片严重 → 浪费 60-80%

PagedAttention (vLLM 原创):
  仿操作系统虚拟内存
  - Block (16 token / block)
  - Block Table (虚拟 → 物理映射)
  - 多个请求共享 prefix blocks

效果:
  显存利用率 60% → 96%
  吞吐量 2-4x
```

### 3.4 Chunked Prefill（长 context 必开）

```
问题:
  默认 prefill 一次性算完所有 prompt
  长 prompt (32K) → prefill 几秒钟
  期间所有 decode 请求被阻塞 → TPOT 飙升

Chunked Prefill:
  把长 prefill 切成多步
  与 decode 交错执行
  prefill 慢一点，decode 不阻塞

启用:
  --enable-chunked-prefill
  --max-num-batched-tokens 2048-8192
```

### 3.5 Prefix Caching

```
场景:
  - System prompt 长且固定
  - 多轮对话 history 重复
  - RAG context 部分相同

启用:
  --enable-prefix-caching

收益:
  TTFT 降 50-95%（前缀越长收益越大）
  RAG/Agent 场景效果最显著

策略:
  vLLM v1: LRU 自动淘汰
  SGLang RadixAttention: 更精细
```

### 3.6 Speculative Decoding

```
原理:
  小模型 draft → 大模型 verify (并行)
  接受率 60-80% → 加速 2-3x

配置:
  方式 1: 独立小模型
    --speculative-model facebook/opt-125m
    --num-speculative-tokens 5
  
  方式 2: EAGLE / Medusa (推荐)
    --speculative-model meta-llama/EAGLE-llama3-70b
  
  方式 3: N-gram (无需模型)
    --speculative-model "[ngram]"

注意:
  小 batch 加速明显
  大 batch (>32) 收益递减
```

### 3.7 Multi-LoRA 动态加载

```bash
# 启动时声明
vllm serve meta-llama/Meta-Llama-3-8B \
  --enable-lora --max-loras 8 \
  --lora-modules sql=/path/lora-sql code=/path/lora-code

# 运行时动态加载 (API)
curl -X POST http://localhost:8000/v1/load_lora_adapter \
  -d '{"lora_name": "math", "lora_path": "/path/lora-math"}'

# 请求时指定
curl http://localhost:8000/v1/chat/completions \
  -d '{"model": "sql", "messages": [...]}'

# 卸载
curl -X POST http://localhost:8000/v1/unload_lora_adapter \
  -d '{"lora_name": "math"}'
```

### 3.8 vLLM 调优 Cheatsheet

```bash
# 高吞吐配置
vllm serve Llama-3-70B-AWQ \
  -tp 2 \
  --quantization awq \
  --kv-cache-dtype fp8 \
  --max-num-seqs 512 \
  --max-num-batched-tokens 8192 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --gpu-memory-utilization 0.95 \
  --disable-log-requests

# 低延迟配置 (in-context learning)
vllm serve Llama-3-8B \
  --enable-prefix-caching \
  --max-num-seqs 32 \              # 小并发
  --max-num-batched-tokens 4096 \
  --speculative-model "[ngram]" \
  --num-speculative-tokens 5

# 极致长上下文 (1M token)
vllm serve gradientai/Llama-3-70B-Instruct-Gradient-1048k \
  --max-model-len 1048576 \
  -tp 8 \
  --enable-chunked-prefill \
  --max-num-batched-tokens 2048   # 小 chunk 防 OOM
```

## 四、SGLang 深度

### 4.1 安装

```bash
pip install "sglang[all]"
# 或
docker run --gpus all -p 30000:30000 \
  lmsysorg/sglang:latest \
  python3 -m sglang.launch_server \
    --model meta-llama/Meta-Llama-3-70B-Instruct \
    --tp 2 --port 30000
```

### 4.2 关键能力

```
RadixAttention ⭐
  Prefix 自动复用 (基于 Radix Tree)
  Agent / 多轮场景大幅提速
  比 vLLM prefix caching 更精细

Structured Generation ⭐
  原生支持 JSON Schema / Regex / 自定义语法
  无需外部库
  
Multi-Modal
  LLaVA / InternVL / Qwen-VL 一键

Function Calling
  原生 OpenAI API 兼容

EAGLE-2/3 推测解码 ⭐
  比 vLLM 实现更快
```

### 4.3 启动

```bash
python3 -m sglang.launch_server \
  --model-path Qwen/Qwen2.5-72B-Instruct \
  --tp 2 \
  --port 30000 \
  --host 0.0.0.0 \
  --mem-fraction-static 0.85 \
  --max-running-requests 256 \
  --enable-cache-report \              # 看 cache 命中率
  --disable-cuda-graph \                # 调试时关
  --schedule-policy lpm                  # lpm/random/fcfs
  --chunked-prefill-size 8192 \
  --speculative-algorithm EAGLE \
  --speculative-draft-model-path lmsys/sglang-EAGLE-llama3-instruct-70B \
  --speculative-num-steps 5
```

### 4.4 SGLang Python DSL（编排 Agent）

```python
import sglang as sgl

sgl.set_default_backend(sgl.RuntimeEndpoint("http://localhost:30000"))

@sgl.function
def multi_turn_question(s, q1, q2):
    s += "You are a helpful assistant.\n"
    s += "User: " + q1 + "\n"
    s += "Assistant:" + sgl.gen("answer1", max_tokens=256)
    s += "\nUser: " + q2 + "\n"
    s += "Assistant:" + sgl.gen("answer2", max_tokens=256)

state = multi_turn_question.run(
    q1="What is the capital of France?",
    q2="How about Germany?",
)
print(state["answer1"], state["answer2"])

# 自动复用 prefix（system prompt + q1）
# 多轮对话最快
```

### 4.5 结构化输出

```python
@sgl.function
def extract(s, text):
    s += "Extract person info from: " + text + "\n"
    s += "Name: " + sgl.gen("name", regex=r"[A-Z][a-z]+") + "\n"
    s += "Age: " + sgl.gen("age", regex=r"\d+") + "\n"

# 严格保证输出格式
# vLLM 同效果需要 outlines 库

# JSON Schema
@sgl.function
def json_out(s):
    s += sgl.gen("data", json_schema='{
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}
    }')
```

## 五、TGI 深度

### 5.1 工业级特性

```
✅ K8s 友好（HuggingFace 官方维护）
✅ Quantization 一键 (BitsAndBytes / AWQ / GPTQ / EETQ)
✅ Token Streaming + SSE
✅ Prometheus metrics 原生
✅ Tracing (OpenTelemetry)
✅ Safetensors 默认
✅ Sharding (Tensor Parallel)
✅ Watermarking
```

### 5.2 启动

```bash
# Docker
docker run --gpus all --shm-size 1g -p 8080:80 \
  -v $PWD/data:/data \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id meta-llama/Meta-Llama-3-70B-Instruct \
  --num-shard 2 \
  --max-input-length 8000 \
  --max-total-tokens 16000 \
  --max-batch-prefill-tokens 8192 \
  --max-batch-total-tokens 32768 \
  --quantize awq \
  --dtype float16

# Helm (生产)
helm install tgi huggingface/text-generation-inference \
  --set model.id=Meta-Llama-3-70B-Instruct \
  --set replicaCount=2 \
  --set resources.limits.nvidia.com/gpu=2
```

### 5.3 API

```bash
# Generate
curl http://localhost:8080/generate \
  -H 'Content-Type: application/json' \
  -d '{"inputs": "Hello", "parameters": {"max_new_tokens": 100, "temperature": 0.7}}'

# Stream
curl http://localhost:8080/generate_stream \
  -H 'Accept: text/event-stream' \
  -d '...'

# OpenAI API 兼容
curl http://localhost:8080/v1/chat/completions \
  -d '{"model": "tgi", "messages": [...]}'

# Metrics
curl http://localhost:8080/metrics      # Prometheus
```

## 六、TensorRT-LLM 深度

### 6.1 极致性能优势

```
- FP8 推理（H100 比 FP16 快 1.5-2x）
- Custom CUDA kernel（GEMM / Attention 优化）
- In-Flight Batching (Continuous Batching)
- Paged KV Cache
- Multi-LoRA
- Speculative Decoding (EAGLE-3)
- Multimodal (Vision/Audio)

劣势:
- 模型转换复杂（每个模型要 build engine）
- engine 不跨硬件（H100 build 的不能跑 A100）
- 部分模型支持滞后
- 单独编译，flexibility 差
```

### 6.2 工作流

```bash
# 1. Clone TensorRT-LLM
git clone https://github.com/NVIDIA/TensorRT-LLM
cd TensorRT-LLM
git lfs install

# 2. 转 checkpoint (HF → TRT-LLM format)
python examples/llama/convert_checkpoint.py \
  --model_dir meta-llama/Meta-Llama-3-70B-Instruct \
  --output_dir ./llama3_70b_ckpt \
  --dtype float16 \
  --tp_size 2

# 3. Build engine
trtllm-build \
  --checkpoint_dir ./llama3_70b_ckpt \
  --output_dir ./llama3_70b_engine \
  --gemm_plugin float16 \
  --gpt_attention_plugin float16 \
  --max_input_len 8192 \
  --max_seq_len 16384 \
  --max_batch_size 32 \
  --use_paged_context_fmha enable

# 4. Run
python examples/run.py \
  --engine_dir ./llama3_70b_engine \
  --max_output_len 256 \
  --tokenizer_dir meta-llama/Meta-Llama-3-70B-Instruct \
  --input_text "Hello"
```

### 6.3 FP8 量化 build

```bash
# 量化 (NVIDIA Quantization Toolkit)
python examples/quantization/quantize.py \
  --model_dir meta-llama/Meta-Llama-3-70B-Instruct \
  --output_dir ./llama3_70b_fp8_ckpt \
  --dtype float16 \
  --qformat fp8 \
  --calib_size 512 \
  --tp_size 2

trtllm-build \
  --checkpoint_dir ./llama3_70b_fp8_ckpt \
  --output_dir ./llama3_70b_fp8_engine \
  --gemm_plugin fp8 \
  --use_fp8_context_fmha enable \
  --max_batch_size 64
```

### 6.4 Triton Inference Server 部署

```bash
# 推荐生产部署方式：TRT-LLM engine + Triton Server
git clone https://github.com/triton-inference-server/tensorrtllm_backend

# 配置 model_repo
model_repo/
├── ensemble/
├── preprocessing/
├── postprocessing/
└── tensorrt_llm/
    └── 1/
        └── llama3_70b_fp8_engine/

# 启动
docker run --gpus all -p 8000-8002:8000-8002 \
  -v $PWD/model_repo:/models \
  nvcr.io/nvidia/tritonserver:24.10-trtllm-python-py3 \
  tritonserver --model-repository=/models
```

## 七、llama.cpp 深度

### 7.1 优势

```
- CPU + GPU 混合推理（GPU 不够用 CPU 顶）
- GGUF 格式生态最广
- 多种量化（Q2_K ~ Q8_0）
- 单机部署最简单（一个二进制）
- 跨平台（Linux/Mac/Win/iOS/Android）
- 适合家用 / 边缘 / 桌面
```

### 7.2 编译 + 运行

```bash
# 编译（带 CUDA）
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make GGML_CUDA=1 -j

# 或 cmake
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j

# 下载 GGUF
huggingface-cli download TheBloke/Llama-3-70B-Instruct-GGUF \
  llama-3-70b-instruct.Q4_K_M.gguf \
  --local-dir ./models

# 推理
./build/bin/llama-cli \
  -m ./models/llama-3-70b-instruct.Q4_K_M.gguf \
  -p "Hello" \
  -n 256 \
  -ngl 80                              # offload 80 层到 GPU

# Server (OpenAI API)
./build/bin/llama-server \
  -m ./models/llama-3-70b-instruct.Q4_K_M.gguf \
  --host 0.0.0.0 --port 8080 \
  -ngl 80 \
  -c 8192                              # context size
```

### 7.3 GGUF 量化等级

```
Q2_K     2.5 bit, 最激进, 损失明显
Q3_K_M   3.4 bit, 可用
Q4_K_S   4.0 bit, 标准
Q4_K_M   4.5 bit, 推荐 ⭐
Q5_K_M   5.5 bit, 高质量
Q6_K     6.5 bit, 接近无损
Q8_0     8 bit, 几乎无损
F16      16 bit, 原版

70B Q4_K_M ≈ 40GB → 单张 48G L40S/A6000 即可
70B Q5_K_M ≈ 48GB → A100 80G 余 32GB KV
```

## 八、Triton Inference Server

### 8.1 通用推理网关

```
不只 LLM，全模态:
  - LLM (TRT-LLM backend)
  - PyTorch / ONNX / TensorRT
  - CV / 音频 / 多模态
  - Python backend (任意自定义)

部署:
  - 多模型管理
  - 版本控制
  - Ensemble (流水线)
  - Business Logic Scripting

适合:
  - 平台型部署
  - 多模型混部
  - 与企业 ML 平台集成
```

### 8.2 Model Repo

```
model_repo/
├── llama3_70b/
│   ├── config.pbtxt
│   └── 1/                              # version 1
│       └── model.engine
├── embed_bge/
│   ├── config.pbtxt
│   └── 1/
│       └── model.onnx
└── rerank_bge/
    ├── config.pbtxt
    └── 1/
        └── model.py                     # Python backend
```

```bash
docker run --gpus all -p 8000-8002:8000-8002 \
  -v $PWD/model_repo:/models \
  nvcr.io/nvidia/tritonserver:24.10-py3 \
  tritonserver --model-repository=/models

# HTTP:  :8000
# gRPC:  :8001
# Metrics: :8002 (Prometheus)
```

## 九、性能调优总论

### 9.1 核心调优手柄

```
吞吐量优先:
  ↑ max_num_seqs (并发数)
  ↑ max_num_batched_tokens (单步 token 数)
  ↑ gpu_memory_utilization (0.9-0.95)
  ✅ Continuous Batching
  ✅ Prefix Caching
  ✅ Speculative Decoding (小 batch)
  ✅ FP8 / INT4 量化
  ✅ KV Cache FP8

延迟优先:
  ↓ max_num_seqs (减少排队)
  ↑ tensor-parallel (拆分模型, 减算时间)
  ✅ Speculative Decoding
  ✅ Prefix Caching
  ✅ Chunked Prefill
  ✅ EAGLE-2/3

长 context:
  ✅ Chunked Prefill (必开)
  ✅ Prefix Caching
  ↓ max_num_batched_tokens (防 OOM)
  ✅ KV Cache 量化 / 卸载
  
多 LoRA:
  vLLM/SGLang Multi-LoRA
  动态加载 / 卸载

多模型:
  Triton Server 平台
  或 多个 vLLM 实例 + Nginx
```

### 9.2 Benchmark 工具

```bash
# vLLM 自带
python -m vllm.entrypoints.benchmarks.benchmark_serving \
  --backend vllm \
  --base-url http://localhost:8000 \
  --model meta-llama/Meta-Llama-3-70B-Instruct \
  --num-prompts 1000 \
  --request-rate inf \
  --dataset-name sharegpt \
  --dataset-path /data/ShareGPT_V3_unfiltered_cleaned_split.json

# 输出关键指标:
# - Throughput: requests/s, tokens/s
# - TTFT: P50/P99 ms
# - TPOT: P50/P99 ms (Time Per Output Token)
# - E2E latency: P50/P99 ms

# 第三方
# - genai-perf (NVIDIA, 跨框架)
# - llmperf (Anyscale)
# - locust + custom (自定义业务)
```

### 9.3 关键指标定义

```
TTFT  Time To First Token         首 token 延迟
TPOT  Time Per Output Token        每 token 平均生成时间
ITL   Inter-Token Latency          相邻 token 间隔
TPS   Tokens Per Second            吞吐
RPS   Requests Per Second          请求吞吐
Goodput  实际有效吞吐（剔除超时）

合格目标 (2025):
  TTFT P99   < 500ms (短 prompt)
  TPOT P99   < 50ms (流式聊天)
  Throughput > 1500 tokens/s/H100 (70B AWQ)
```

## 十、模型兼容性

### 10.1 vLLM 支持模型

```
Llama 1/2/3/3.1/3.2/3.3
Qwen 1/2/2.5/3 (含 VL/Audio)
Mistral / Mixtral
DeepSeek V2/V3 (含 MoE)
Yi / InternLM / Baichuan
ChatGLM / GLM-4
Gemma 2/3
Phi 3/3.5/4
Command-R / Aya
Falcon
StableLM
BGE / E5 (embedding)
Reranker
Whisper (Audio)
LLaVA / InternVL / Qwen-VL / Pixtral (VLM)
...
完整列表: docs.vllm.ai/en/latest/models/supported_models.html
```

### 10.2 国产模型推荐部署

```
通用 LLM:
  Qwen2.5-72B-Instruct          vLLM/SGLang/TGI
  DeepSeek-V3                    SGLang (MoE 友好)
  GLM-4-9B/32B/Plus              vLLM
  Yi-1.5-34B                     vLLM
  Baichuan2-13B                  vLLM
  InternLM3-8B                   vLLM
  Telechat                       vLLM (中国电信)
  Hunyuan-Large                  vLLM (腾讯)

多模态:
  Qwen2-VL / Qwen2.5-VL         vLLM/SGLang
  InternVL2-/2.5                  vLLM
  CogVLM2                        vLLM

代码:
  DeepSeek-Coder-V2              vLLM
  Qwen2.5-Coder-32B              vLLM
  CodeLlama                       vLLM

数学:
  DeepSeek-Math                  vLLM
  Qwen2.5-Math                   vLLM
```

## 十一、典型坑

| 坑 | 建议 |
|:---|:---|
| **vLLM 启动 OOM** | 减小 `gpu_memory_utilization` / `max_model_len` |
| **vLLM 长 prompt TTFT 高** | 开 `chunked-prefill` |
| **Multi-LoRA 速度跳水** | `max_loras` 不要过大 |
| **量化精度差** | 用 AWQ > GPTQ > BNB |
| **TRT-LLM engine 不通用** | 同机型 build |
| **TGI 模型支持滞后** | 用 vLLM/SGLang 替代 |
| **llama.cpp 单 batch** | 高并发别用 |
| **prefix 命中低** | 检查 system prompt 是否完全一致 |
| **speculative 反而变慢** | 小 model 接受率低 → 关 |
| **K8s 重启 lose 缓存** | 上 Prefix Caching 持久化（实验） |
| **流式 SSE 卡顿** | 检查反向代理 buffering / 网络 |
| **多机 TP 慢** | 用 PP 替代 / 优化 NCCL |
| **bf16 vs fp16 选错** | A100 用 BF16, T4 用 FP16 |
| **TGI 性能低于 vLLM** | 切 vLLM/SGLang |

## 十二、最佳实践 Checklist

```
选型:
☐ 主用 vLLM 或 SGLang
☐ 极致性能用 TRT-LLM
☐ 边缘/桌面用 llama.cpp
☐ 多模型平台用 Triton

部署:
☐ Docker 容器化
☐ GPU 持久化模式
☐ 显存利用 0.9+
☐ Chunked Prefill 开
☐ Prefix Caching 开
☐ KV Cache FP8

调优:
☐ Benchmark 基线
☐ 量化（AWQ INT4 / FP8）
☐ Speculative Decoding（小 batch 场景）
☐ Multi-LoRA（多用户）
☐ 监控 TTFT/TPOT/Throughput

生产:
☐ Prometheus metrics
☐ K8s + HPA + KEDA
☐ 健康检查 + readiness
☐ 灰度发布
☐ A/B Testing
☐ 自动模型热更新
```

## 十三、推荐栈（2025）

### 13.1 中小团队

```
- vLLM 主部署
- Docker + 单机多卡
- Nginx 负载均衡
- Prometheus + Grafana
- 模型 HuggingFace 拉取
```

### 13.2 中型企业

```
- vLLM / SGLang 双栈
- K8s + GPU Operator
- KEDA HPA (按 QPS / TPOT)
- Triton 多模型平台
- Harbor 镜像 + Model Registry
- LiteLLM / OpenRouter 路由层
```

### 13.3 大型 / 大模型生产

```
- TRT-LLM FP8 极致优化
- vLLM Disaggregated PD (Prefill/Decode 分离)
- 跨集群多副本负载均衡
- 自动模型版本管理
- A/B / 灰度 / Canary
- 主备 (DR) + 跨 region
- 自研路由层（按用户/任务路由不同模型）
```

## 十四、学习路径

```
入门（1 月）:
  1. vLLM 跑通 Llama-3-8B
  2. OpenAI API 兼容
  3. Docker 部署
  4. Prometheus 监控
  5. AWQ / GPTQ 量化模型加载

中级（3 月）:
  6. PagedAttention 原理
  7. Continuous Batching
  8. Prefix Caching / RadixAttention
  9. SGLang 切换 / 对比
  10. Multi-LoRA
  11. K8s 部署 + HPA

高级（6 月+）:
  12. TRT-LLM build engine
  13. FP8 / SmoothQuant
  14. Speculative Decoding (EAGLE)
  15. PD 分离架构
  16. 自定义 CUDA kernel (Triton)
  17. 万卡推理集群

专家:
  18. 框架内核源码
  19. 自研推理引擎
  20. 多模态融合推理
```

## 十五、参考资料

```
官方:
  - vLLM: https://docs.vllm.ai/
  - SGLang: https://docs.sglang.ai/
  - TGI: https://huggingface.co/docs/text-generation-inference/
  - TensorRT-LLM: https://nvidia.github.io/TensorRT-LLM/
  - llama.cpp: https://github.com/ggerganov/llama.cpp
  - Triton Server: https://github.com/triton-inference-server

论文:
  - vLLM/PagedAttention (2023 SOSP)
  - FlashAttention 1/2/3
  - Continuous Batching (Orca, OSDI '22)
  - Sarathi-Serve (Chunked Prefill)
  - SGLang/RadixAttention
  - EAGLE-1/2/3
  - DeepSeek-V3 (Mixtral / MLA)

社区:
  - vLLM Slack
  - SGLang Discord
  - r/LocalLLaMA
  - 国内: GPU Mode 中文 / AI Infra
```

> 📖 **核心判断**：**vLLM 主战场（生态最强）+ SGLang 高吞吐 + TRT-LLM 极致性能 + llama.cpp 边缘**——这套组合覆盖 95% 推理场景。**先把 vLLM 的 30 个核心参数练熟**，然后再看 SGLang 的 RadixAttention 和 TRT-LLM 的 FP8。**性能上限是硬件决定的，但 70% 的潜力用错框架/调参就浪费了**——框架知识就是这 70% 的钥匙。

