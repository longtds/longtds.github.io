# 高级

> AI 基础设施高级 = **大模型预训练全栈(数据→Tokenizer→3D 并行→Checkpoint→Resume) + Post-training(SFT/DPO/RLHF/GRPO/PPO) + LoRA/QLoRA/全参微调 + 高级推理优化(Speculative/Prefix/Chunked/MTP/DisAgg Prefill-Decode) + 多机训推一体平台 + 长上下文(YaRN/RoPE/RingAttention) + MoE 训推 + 多模态(VL/Audio/Video) + Agent 框架(LangGraph/AutoGen/CrewAI) + LLM 网关(LiteLLM/OneAPI/Higress) + GPU 网络极致调优(NCCL+IB+SHARP) + 分布式 Checkpoint + 大规模训练故障容错 + 模型蒸馏 + 边缘部署 + 国密合规 + 大规模国产化(昇腾+鲲鹏+MindFormers)**。本章面向 AI 平台架构师 / 训推平台负责人。

## 一、大模型预训练全栈

### 1.1 数据 Pipeline

```
原始数据 (PB 级)
  → 数据采集 (Common Crawl / 业务 / 开源)
  → 数据清洗 (去重 / 质量过滤 / 安全过滤)
  → 数据混合 (业务: 中英文比例 / 代码 / 数学)
  → 分词 (Tokenizer: SentencePiece / Tiktoken / BBPE)
  → 数据集打包 (索引 + memmap)
  → 训练加载 (HF Datasets / Megatron Dataset)

工具:
  - dedup (MinHash / SimHash) ⭐
  - 去毒 (Detoxify / 自研分类器)
  - 质量评分 (Perplexity / 教育水平)
  - 数据平衡 (rebalance per domain)

国产参考:
  - Wanjuan (上海 AI Lab) ⭐
  - CCI 3.0 (北智源 / 智源)
  - Skywork-700B / Yi-1T
```

### 1.2 Tokenizer

```python
# SentencePiece (Llama / Qwen)
import sentencepiece as spm
spm.SentencePieceTrainer.train(
    input="corpus.txt",
    model_prefix="qwen",
    vocab_size=152064,
    model_type="bpe",
    byte_fallback=True,
    character_coverage=0.9999,
    normalization_rule_name="identity",
)

# Tiktoken (OpenAI BBPE)
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
print(enc.encode("hello world"))
```

### 1.3 3D 并行配置（Llama3-70B 示例）

```
集群:       16 节点 × 8 H100 = 128 GPU
全局 BS:    1024 sequences × 8K tokens = 8M tokens/step
TP=8        (单机内, NVLink)
PP=4        (跨 4 机 pipeline, IB)
DP=4        (4 个 model replica)
微 BS:      1
梯度累积:   32

工具:
  Megatron-LM ⭐
  NeMo (Nvidia)
  Colossal-AI (国产)
  MindFormers (Ascend)
```

### 1.4 训练命令

```bash
torchrun \
  --nnodes 16 --nproc_per_node 8 \
  --rdzv_id llama3-70b --rdzv_backend c10d \
  --rdzv_endpoint master:29500 \
  pretrain_gpt.py \
    --tensor-model-parallel-size 8 \
    --pipeline-model-parallel-size 4 \
    --micro-batch-size 1 \
    --global-batch-size 1024 \
    --num-layers 80 --hidden-size 8192 \
    --num-attention-heads 64 \
    --max-position-embeddings 8192 --seq-length 8192 \
    --tokenizer-type Llama3Tokenizer \
    --bf16 --use-flash-attn \
    --recompute-granularity selective \
    --distributed-optimizer \
    --save /ckpt/llama3-70b --save-interval 500 \
    --load /ckpt/llama3-70b
```

### 1.5 Checkpoint 与 Resume

```
Megatron 分布式 Checkpoint:
  - 每 rank 存自己的 shard
  - 元数据 (metadata.json)
  - 异步保存 (后台线程)
  - 大模型: 250GB-2TB / checkpoint
  
存储:
  - 共享存储 (Lustre / GPFS / JuiceFS) ⭐
  - 备份到对象存储 (S3 / OSS)
  - 季度清理 (保留 N 个)

Resume:
  - 拓扑变化时 (TP/PP 调整) → convert_checkpoint.py
  - 容错 (节点故障) → 减少 DP / 自动 resume
```

## 二、Post-training（SFT/RLHF/DPO/GRPO）

### 2.1 SFT（指令微调）

```bash
# LLaMA-Factory ⭐ (最易用国产)
llamafactory-cli train \
  --stage sft \
  --do_train True \
  --model_name_or_path Qwen/Qwen2.5-7B \
  --dataset alpaca_gpt4_zh \
  --template qwen \
  --finetuning_type lora \
  --lora_target all \
  --output_dir saves/qwen2.5-7b-sft \
  --overwrite_output_dir \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 4 \
  --lr_scheduler_type cosine \
  --logging_steps 10 \
  --save_steps 200 \
  --learning_rate 5e-5 \
  --num_train_epochs 3.0 \
  --bf16 \
  --plot_loss True
```

### 2.2 DPO（直接偏好优化, 替代 RLHF）

```python
# trl (Hugging Face)
from trl import DPOTrainer
trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    args=training_args,
    beta=0.1,
    train_dataset=dataset,    # {prompt, chosen, rejected}
    tokenizer=tokenizer,
    max_length=2048,
)
trainer.train()
```

### 2.3 GRPO（DeepSeek 用于 R1, 主流 2026）

```
GRPO (Group Relative Policy Optimization):
  - DeepSeek 提出
  - 替代 PPO (无 Value Model)
  - 单 prompt 多 sample 组内归一化
  - 内存 / 显存大幅减少
  - 数学 / 推理 任务效果好 ⭐

工具:
  TRL (HuggingFace, GRPO trainer)
  Verl (国产, ByteDance) ⭐
  OpenRLHF
```

### 2.4 RLHF (PPO, 老传统)

```
组件:
  Actor (策略)
  Reference (冻结 SFT)
  Reward Model (奖励)
  Critic (价值)

工具:
  OpenRLHF ⭐
  TRL
  DeepSpeed-Chat (老)
  Megatron-RLHF (Nvidia)
```

### 2.5 LoRA / QLoRA / 全参微调

```
全参微调:
  显存: 70B × 16 = 1.1TB (BF16) + Adam 状态
  
LoRA (Low-Rank Adaptation):
  显存: ~1/10
  Hub: rank 8/16/32/64
  adapter 几十 MB
  
QLoRA (4bit 量化基座 + LoRA):
  显存: 7B 单卡 (24GB) 可微调
  适合: 个人开发 / 实验

DoRA / LoRA+ / PiSSA (LoRA 改进):
  更好的初始化 / 收敛
```

## 三、推理高级优化

### 3.1 Speculative Decoding

```
原理:
  小模型 (draft) 一次预测 K 个 token
  大模型 (target) 一次验证 K 个
  接受 → 跳 K 步; 拒绝 → 大模型 forward

vLLM 配置:
--speculative-model Qwen/Qwen2.5-1.5B-Instruct
--num-speculative-tokens 5

加速:
  数学 / 代码: 2-3x
  通用: 1.3-1.8x
```

### 3.2 Prefix Caching

```
原理:
  系统 prompt / 业务上下文 KV cache 复用
  hash(prompt prefix) → KV blocks
  
场景:
  RAG 系统提示 (节省 30-50%)
  Agent 工具描述
  Few-shot 学习

vLLM:
--enable-prefix-caching
```

### 3.3 Chunked Prefill

```
原理:
  长 prompt 分块处理
  减少 first-token 延迟
  混合 prefill + decode batch

vLLM:
--enable-chunked-prefill
--max-num-batched-tokens 2048
```

### 3.4 Disaggregated Prefill-Decode

```
原理:
  Prefill (CPU 密集) + Decode (内存密集) 分集群
  
工具:
  llm-d ⭐ (CNCF)
  Mooncake (Moonshot) ⭐
  DistServe
  vLLM disagg prefill (实验)

收益:
  - GPU 利用率 ↑ 30-50%
  - SLO 更可控
  - 适合超大规模 (千卡 +)
```

### 3.5 MTP（Multi-Token Prediction）

```
理念:
  一次预测多 token (DeepSeek V3 用)
  推理时类似 speculative
  
适合:
  DeepSeek 类已训练 MTP head 的模型
```

### 3.6 推理优化矩阵

| 技术 | 加速 | 显存 | 适合 |
|:---|:---:|:---:|:---|
| **FP8 量化** | 2x | -50% | H100 / B100 ⭐ |
| **AWQ / GPTQ INT4** | 1.5-2x | -75% | A100 / 单卡 ⭐ |
| **Prefix Caching** | 1.3-1.5x | - | RAG / Agent ⭐ |
| **Chunked Prefill** | 1.2x | - | 长输入 |
| **Speculative** | 1.5-3x | + | 通用 ⭐ |
| **MTP** | 1.5-2x | - | DeepSeek |
| **PagedAttention** | 5-10x | - | 高并发 ⭐ |
| **Continuous Batching** | 5-10x | - | 多请求 ⭐ |
| **DisAgg Prefill-Decode** | 30-50% (利用率) | - | 千卡 ⭐ |
| **FlashAttention 3** | 1.5x | -10% | H100 |

## 四、长上下文（128K+）

### 4.1 位置编码扩展

```
RoPE 原始: 4K
方法:
  - PI (Position Interpolation): 直接拉伸
  - NTK-aware: 不同频率不同拉伸
  - YaRN ⭐: 当前最优
  - LongRoPE / SelfExtend
  
工具:
  vLLM: --rope-scaling '{"type":"yarn","factor":4.0,"original_max_position_embeddings":32768}'
```

### 4.2 RingAttention / RingFlashAttention

```
理念:
  跨多 GPU/节点切 K-V (序列维度)
  Ring 传输

适合:
  > 1M token 推理 (Gemini 类)
  
工具:
  Ring Attention 论文实现
  Megatron-LM Sequence Parallel
  XServer Long Context
```

### 4.3 KV Cache 压缩

```
方法:
  - StreamingLLM (保头 + 滑窗) ⭐
  - H2O / Heavy-Hitter Oracle
  - KIVI (4bit KV)
  - Quest (KV scattering)
  
适合:
  Agent 长记忆 / 客服多轮
```

## 五、MoE 训推

### 5.1 MoE 原理

```
专家混合:
  N 个专家网络 + 1 个 router
  每 token 激活 K 个专家 (top-K)
  参数大 / 计算小

代表:
  DeepSeek V3 ⭐ (671B 总, 37B 激活)
  Mixtral 8x7B / 8x22B
  Qwen MoE
  GLM-4 MoE
```

### 5.2 MoE 训练

```
专家并行 (EP):
  N 个专家分布到 N 个 GPU
  All-to-All 通信 (router → 专家)
  
工具:
  Megatron-Core MoE ⭐
  DeepSpeed-MoE
  Tutel (微软)
  vLLM MoE 推理

挑战:
  - 负载不均 (router 偏好)
  - All-to-All 网络瓶颈 (IB / SHARP)
  - Checkpoint 大 (专家多)
```

### 5.3 MoE 推理优化

```
DeepSeek V3 推理:
  - 671B 总参数 / 37B 激活
  - 单 inference 只用 part of weights
  - 8 卡 H100 可跑 (vLLM)
  - 量化 (FP8 / Int4) 进一步压缩

vLLM 配置:
  --max-num-seqs 256
  --enable-prefix-caching
  --quantization fp8
```

## 六、多模态训推

### 6.1 主流多模态架构

```
LLaVA:        ViT + Projector + LLM
Qwen-VL:      ViT + Cross-Attention
InternVL:     ViT + MLP + LLM
GPT-4V / Gemini: 端到端
SAM:          分割
Whisper:      语音
Sora:         视频生成 (DiT)
```

### 6.2 多模态推理

```bash
# vLLM 多模态
vllm serve Qwen/Qwen2.5-VL-7B-Instruct \
  --tensor-parallel-size 2 \
  --max-model-len 32768 \
  --limit-mm-per-prompt image=4,video=1

# SGLang 多模态
python -m sglang.launch_server \
  --model-path Qwen/Qwen2.5-VL-72B-Instruct \
  --tp 4 --mm-attention-backend flashinfer
```

### 6.3 端到端多模态训练

```
框架:
  LLaVA-Factory
  InternVL-Chat-1.5+
  Qwen-VL-Finetune
  LLaMA-Factory (多模态扩展)

数据:
  LAION-5B / OBELICS / SAM-Caption
  ShareGPT4V / LLaVA-OneVision
```

## 七、Agent 框架

```
LangGraph ⭐:
  - 基于 LangChain
  - DAG 状态机
  - 支持工具 + 多 Agent 协作
  - 最主流 (2026)

AutoGen ⭐:
  - Microsoft, 多 Agent 对话
  - GroupChat / Code Execution
  
CrewAI:
  - 角色 / 任务驱动
  - 简单上手
  
MetaGPT:
  - 国产, 多 Agent 软件开发
  - PM / Engineer / QA
  
OpenManus / Owl (国产开源)
通义灵码 Agent / Claude Computer Use
```

```python
# LangGraph 例
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next: str

def planner(state):
    # LLM 规划
    return {"messages": [...], "next": "tool_executor"}

def tool_executor(state):
    # 工具调用
    return {"messages": [...], "next": "checker"}

def checker(state):
    return {"messages": [...], "next": END if done else "planner"}

graph = StateGraph(AgentState)
graph.add_node("planner", planner)
graph.add_node("tool_executor", tool_executor)
graph.add_node("checker", checker)
graph.set_entry_point("planner")
graph.add_conditional_edges("checker", lambda s: s["next"])
app = graph.compile()
```

## 八、LLM 网关

```
LiteLLM ⭐:
  - 统一 API (OpenAI 格式)
  - 接 100+ LLM (OpenAI/Anthropic/vLLM/Ollama/Azure/Bedrock)
  - 路由 / 限流 / 重试 / 缓存
  - 用量统计 / 成本归属
  - K8s 部署

OneAPI / NewAPI ⭐ (国产):
  - 类似 LiteLLM
  - 中文友好
  - Token 管理 + 计费

Higress / APISIX AI Gateway ⭐:
  - Envoy / Nginx 网关 + AI 插件
  - 限流 + 鉴权 + 路由
  - 国产
  
Portkey AI Gateway
Cloudflare AI Gateway

特性:
  ☐ 多模型路由 (Failover / Round-robin / Weighted)
  ☐ 限流 (RPS / RPM / TPM)
  ☐ 鉴权 (API Key + JWT + OIDC)
  ☐ 缓存 (相同请求复用)
  ☐ 内容审核 (NeMo Guardrails / 国产)
  ☐ 用量统计 / 计费
  ☐ Prompt 注入防护
```

## 九、GPU 网络极致调优

### 9.1 拓扑感知

```
NVLink (单机内, 600-900 GB/s):
  TP 通信 (AllReduce)
  
InfiniBand (跨节点, NDR 400G ~50 GB/s):
  PP / DP 通信
  
PCIe (CPU ↔ GPU, 64 GB/s Gen5):
  data loader → GPU
  
NCCL 拓扑:
  nvidia-smi topo -m
  nvidia-smi nvlink -s
```

### 9.2 SHARP（在网计算）

```
原理:
  IB 交换机内置 AllReduce
  GPU 不消耗算力
  
工具:
  NCCL_SHARP_ENABLE=1
  Mellanox SHARP plugin

收益:
  大集群 (256+ GPU) AllReduce ↑ 30%
```

### 9.3 NCCL 终极调优

```bash
export NCCL_DEBUG=INFO
export NCCL_IB_HCA=mlx5_0,mlx5_1,mlx5_2,mlx5_3
export NCCL_IB_GID_INDEX=3
export NCCL_NET_GDR_LEVEL=2          # GPUDirect RDMA
export NCCL_P2P_LEVEL=NVL             # NVLink P2P
export NCCL_ALGO=Ring,Tree
export NCCL_PROTO=Simple,LL,LL128
export NCCL_NSOCKS_PERTHREAD=4
export NCCL_SOCKET_NTHREADS=8
export NCCL_BUFFSIZE=8388608
export NCCL_SHARP_ENABLE=1            # SHARP
export NCCL_TIMEOUT=600

# 测试
./build/all_reduce_perf -b 8 -e 8G -f 2 -g 8
```

### 9.4 网络拓扑设计（千卡 H100）

```
单 Pod (8 H100):
  NVSwitch 全互联

跨 Pod (16-256 H100):
  Rail-optimized
  每 H100 → 1 IB NIC
  8 H100 → 8 IB → IB Spine

跨 Region:
  IB / RoCE 跨机房
  网络平面分离 (训练 IB + 业务以太)
```

## 十、训练故障容错

```
常见故障:
  - GPU Xid 错误 (硬件)
  - NVLink down
  - IB link flap
  - 节点 OOM / 进程崩溃
  - 网络分区
  - 存储 IO 抖动

对策:
☐ Megatron --auto-detect-ckpt-format + auto resume
☐ DeepSpeed Elastic (动态伸缩)
☐ Volcano restart-policy
☐ Pod priority class (重要 Job 不被驱逐)
☐ Liveness probe + 自动重启
☐ DCGM 健康检查 (硬件)
☐ Slack 告警 + on-call
☐ Checkpoint frequency 调 (10-100 step)
☐ 异步 checkpoint (后台保存)

工具:
  DLRover (蚂蚁) ⭐
  TorchX
  Volcano + Kueue
  ByteCheckpoint (字节)
```

## 十一、模型蒸馏

```
蒸馏类型:
  - Hard label (Logit 蒸馏)
  - Soft label (KL Divergence)
  - Feature distillation (中间层)
  - Self-distillation
  - Sequence-level (生成式)

工具:
  trl + DPO/SFT
  DeepSeek-R1 → 小模型蒸馏 (热门 2025)
  自研

代表:
  DeepSeek-R1-Distill-Qwen-7B/32B ⭐
  Phi 系列 (微软蒸馏 GPT-4)
```

## 十二、边缘部署

```
硬件:
  Jetson Orin (Nvidia) ⭐
  瑞芯微 RK3588 / RK3576
  高通骁龙 X Elite
  寒武纪 MLU220
  
框架:
  llama.cpp ⭐ (GGUF)
  Ollama
  MLC-LLM (Tensor Compiler)
  TFLite / ONNX Runtime
  
量化:
  Q4_K_M (4bit) ⭐
  INT8

场景:
  - 边缘网关
  - 移动端 (手机)
  - IoT
  - 离线助手
```

## 十三、国密 + 合规

```
模型 + 数据合规:
☐ 模型登记备案 (网信办 ⭐ 强制)
☐ 数据合规 (个保法 + 数据安全法)
☐ 训练数据来源合法
☐ 模型卡 / 透明
☐ 安全评估 + 内容审核
☐ 用户授权 + 数据脱敏
☐ 日志留存 6 个月

国密 + 等保:
☐ 服务接口 国密 TLS (SM2)
☐ 数据加密 (KMS / 国密)
☐ Audit log → SIEM 180d
☐ 等保三级 (政企)

内容审核:
☐ NeMo Guardrails
☐ 国产: 阿里绿网 / 网易易盾 / 腾讯天御
☐ 关键词 + 语义双过滤
```

## 十四、大规模国产化

```
硬件:        华为 Ascend 910B/910C ⭐ (千卡集群)
              海光 DCU / 寒武纪 / 摩尔线程 (备选)
驱动:        CANN 8 + Driver + HCCL
框架:        PyTorch + torch_npu / MindSpore
训练:        MindFormers ⭐ / Megatron + Ascend Adapter
推理:        MindIE ⭐ / LMDeploy
模型:        Qwen / DeepSeek / GLM / InternLM (全适配 Ascend)
K8s:         Ascend Operator + Volcano
网络:        RoCE v2 + HCCL
存储:        JuiceFS / OceanStor (华为存储)
监控:        npu-smi + Ascend Exporter + Prometheus
合规:        国密 + 等保三级 + 模型备案
平台:        ModelArts (华为) / PAI (阿里) / Volcano Engine (火山) / 自研

参考案例:
  PanGu (华为, 千亿) ⭐
  Qwen 在 Ascend 大规模训练 ⭐
  DeepSeek V3 在 Ascend 推理验证
  上海 AI Lab InternLM 在 Ascend 训练
```

## 十五、Checklist（高级）

```
预训练:
☐ 数据 Pipeline (清洗 / 去重 / 平衡)
☐ Tokenizer (SP / BBPE)
☐ Megatron 3D 并行
☐ 分布式 Checkpoint + Resume
☐ DLRover 容错

Post-training:
☐ SFT (LLaMA-Factory)
☐ DPO / GRPO (TRL / Verl)
☐ LoRA + DoRA + PiSSA
☐ Reward Model 训练

推理:
☐ Speculative Decoding
☐ Prefix Caching + Chunked Prefill
☐ FP8 量化 + KV cache FP8
☐ Disaggregated Prefill-Decode (大规模)
☐ MTP (DeepSeek)

长上下文:
☐ YaRN / RoPE 扩展
☐ Ring Attention (>1M token)
☐ StreamingLLM / H2O / KIVI

MoE:
☐ Megatron-Core MoE EP
☐ All-to-All + SHARP
☐ DeepSeek V3 推理 (671B/37B)

多模态:
☐ Qwen-VL / InternVL 推理
☐ vLLM / SGLang 多模态后端
☐ ViT + Projector + LLM 微调

Agent:
☐ LangGraph 编排
☐ AutoGen / CrewAI / MetaGPT 备选
☐ 工具调用 + Memory + RAG

LLM 网关:
☐ LiteLLM / OneAPI / Higress AI
☐ 路由 / 限流 / 鉴权 / 缓存 / 审核 / 计费

网络:
☐ NVLink + NVSwitch + IB NDR
☐ NCCL 调优 + SHARP
☐ 拓扑感知调度

容错:
☐ DLRover / DeepSpeed Elastic
☐ Auto Resume + Async Checkpoint
☐ DCGM 健康检查

蒸馏:
☐ DeepSeek-R1 → 小模型 (热)
☐ 业务模型蒸馏

边缘:
☐ Jetson / RK 部署
☐ GGUF Q4 量化 + llama.cpp

国密合规:
☐ 模型备案
☐ 国密 TLS + 字段加密
☐ 内容审核 (NeMo Guardrails / 国产)
☐ Audit 180d

国产化:
☐ Ascend 910B 千卡训练
☐ MindFormers / MindIE / LMDeploy
☐ 信创 K8s + RoCE
☐ ModelArts / PAI 平台
```

## 十六、推荐栈（高级）

```
训练:        Megatron-LM ⭐ + NeMo + DeepSpeed + DLRover (容错)
            国产: MindFormers (Ascend) + Colossal-AI
Post-training: TRL (DPO/GRPO) + OpenRLHF + LLaMA-Factory + Verl
推理:        vLLM 0.6+ ⭐ + SGLang + TRT-LLM + llm-d (CNCF)
            国产: MindIE + LMDeploy
量化:        AWQ + GPTQ + FP8 + SmoothQuant
调度:        Volcano + Kueue + Karmada (多集群)
网络:        IB NDR 400G + NCCL + SHARP
存储:        JuiceFS + Lustre + Alluxio + OceanStor (国产)
模型注册:    MLflow + Harbor LFS + 自研
实验追踪:    W&B + MLflow
RAG:        LangChain / LlamaIndex + pgvector / Milvus
            Reranker: bge-reranker / Cohere
Agent:      LangGraph ⭐ + AutoGen + CrewAI
LLM 网关:    LiteLLM ⭐ + Higress AI ⭐ (国产)
监控:        DCGM + Triton + vLLM + Grafana
合规:        国密 + 内容审核 + 等保 + 模型备案
```

> 📖 **核心判断**：AI 基础设施高级 = **预训练全栈(Megatron+3D+Checkpoint) + Post-training(SFT/DPO/GRPO) + 推理优化(Speculative/Prefix/FP8/DisAgg) + 长上下文(YaRN/Ring) + MoE 训推 + 多模态 + Agent(LangGraph) + LLM 网关(LiteLLM/Higress) + 网络极致(IB+SHARP+NCCL) + 容错(DLRover) + 边缘 + 国密合规 + 大规模国产化(Ascend+MindFormers)**。能给企业画"Ascend/H100 集群 + Megatron 训练 + DPO/GRPO + vLLM/MindIE 推理 + LangGraph Agent + LiteLLM 网关 + RAG + 国密合规"完整 AI 训推平台，就具备 AI 平台架构师能力。
