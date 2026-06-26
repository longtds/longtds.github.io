# 推理成本优化

> LLM 推理成本结构：**GPU 折旧（70%）+ 电力散热（15%）+ 网络存储（10%）+ 软件运营（5%）**。**量化 + KV Cache 优化 + 批处理 + 路由 + 缓存** 五招能把成本降 60-90%。本章给完整成本模型和实战手册。

## 一、成本结构分析

### 1.1 总拥有成本（TCO）

```
本地集群 (自建 8 × H100 / 24个月):
  GPU 服务器: 8 × $400k = $3.2M (整机包括 GPU/CPU/NVMe/网络)
  机柜 + 电力: $40k/年 × 2 = $80k
  运维人员: $200k/年 × 2 = $400k
  网络/存储: $300k
  
  TCO = $3.98M / 24月 = $166k/月

vs 云上 (8 × H100 按需):
  $98/h × 24 × 30 = $70k/月
  
  → 持续负载 → 自建省钱
  → 弹性负载 → 云上灵活
  → 混合 → 最优
```

### 1.2 推理单位成本（Per-Token Cost）

```
公式:
  Cost/token = GPU 成本/小时 / 输出 token/秒 / 3600

H100 80G ($30/h) + Llama-3-70B AWQ:
  输出 ~1500 tokens/s
  Cost/token = $30 / 1500 / 3600 = $5.5 × 10⁻⁶
            = $5.5 / 1M tokens

商业 API 对比 (per 1M tokens):
  GPT-4o:           $5-15
  Claude 3.5 Sonnet: $3-15
  Gemini 1.5 Pro:   $1.25-5
  自建 70B:         $5.5
  自建 8B AWQ:      $0.5
  自建 405B FP8:    ~$30

→ 自建 70B 与 API 同价位
→ 自建 8B 比 API 便宜 10x
→ 自建大模型不省钱，但保数据 + SLA
```

### 1.3 成本归因

```
Token 维度:
  Input tokens vs Output tokens
  Prefill 计算 vs Decode 计算 (Decode 占 80%)

请求维度:
  短请求 (<100 token)
  中请求 (100-1000)
  长请求 (1000-10000)
  超长请求 (>10000)

用户/特性维度:
  谁在烧钱
  哪个 feature 烧钱
  Agent 调用次数

模型维度:
  70B vs 8B
  FP16 vs FP8 vs INT4
  base vs LoRA
```

## 二、优化招数总览

### 2.1 五大优化方向

```
1. 模型层
   ✅ 量化 (FP16 → AWQ INT4 / FP8) → 显存 ↓ 3-4x，速度 ↑ 1.5-2x
   ✅ 模型蒸馏 (70B → 8B Distilled)
   ✅ MoE (Mixtral / DeepSeek) 激活部分参数
   ✅ Speculative Decoding (EAGLE) 加速

2. 引擎层
   ✅ Continuous Batching
   ✅ PagedAttention / RadixAttention
   ✅ KV Cache FP8
   ✅ Prefix Caching 跨副本
   ✅ Chunked Prefill
   ✅ PD 分离

3. 调度层
   ✅ 智能路由 (难度路由：简单→小模型)
   ✅ 用户分级 (高级用户大模型，普通用户小模型)
   ✅ 缓存 (Prompt Cache / Response Cache)
   ✅ Spec 接受率优化

4. 基础设施层
   ✅ Spot / 抢占式实例 (-60%)
   ✅ 跨 region 错峰
   ✅ HPA / KEDA 弹性
   ✅ MIG 共享 (GPU 切片)
   ✅ 国产 GPU 替代 (-30%)

5. 应用层
   ✅ Prompt 压缩 (LLMLingua, RAG 抽取)
   ✅ 流式提前停止
   ✅ Max Tokens 严格限制
   ✅ 多轮上下文摘要
   ✅ 用户配额管理
```

### 2.2 优化优先级 ROI

| 优化 | 难度 | 收益 | ROI |
|:---|:---:|:---:|:---:|
| **AWQ INT4 量化** | ⭐ | 显存 ↓ 75% / 吞吐 ↑ 2x | ⭐⭐⭐⭐⭐ |
| **KV Cache FP8** | ⭐ | 显存 ↓ 50% | ⭐⭐⭐⭐⭐ |
| **Prefix Caching** | ⭐⭐ | RAG/Agent TTFT ↓ 80% | ⭐⭐⭐⭐⭐ |
| **Continuous Batching** | - | 框架默认 | ⭐⭐⭐⭐⭐ |
| **Response Cache** | ⭐ | FAQ 命中率 30% | ⭐⭐⭐⭐ |
| **难度路由** | ⭐⭐ | 70% 请求 → 小模型 | ⭐⭐⭐⭐⭐ |
| **Spot 实例** | ⭐⭐⭐ | -60% 成本 | ⭐⭐⭐⭐ |
| **MoE 模型** | ⭐ | 同质量减半成本 | ⭐⭐⭐⭐ |
| **Speculative** | ⭐⭐ | -30% latency | ⭐⭐⭐ |
| **PD 分离** | ⭐⭐⭐⭐ | -20% 资源 | ⭐⭐⭐ |
| **Prompt 压缩** | ⭐⭐ | input tokens ↓ 50% | ⭐⭐⭐⭐ |
| **MIG 切片** | ⭐⭐ | GPU 复用 | ⭐⭐⭐ |
| **国产 GPU** | ⭐⭐⭐⭐ | -30% 成本 | ⭐⭐⭐ |

## 三、量化优化（成本第一刀）

### 3.1 AWQ INT4

```
70B 模型:
  FP16:    140 GB → 2 × H100 (TP=2) → 双卡 30 token/s
  AWQ:      35 GB → 1 × H100 (单卡)  → 单卡 35 token/s
  
  成本: 1/2 卡 + 速度更快
  精度: 损失 1-3%（通常可接受）
```

### 3.2 FP8（H100+ 必开）

```
Llama-3-70B FP8 (H100 / TRT-LLM):
  显存: 70 GB → 单卡
  吞吐: ~2x FP16
  精度: < 1% 损失

启用:
  TRT-LLM:    --gemm_plugin fp8 --use_fp8_context_fmha
  vLLM:       --quantization fp8 --kv-cache-dtype fp8
  SGLang:    自动 fp8
```

### 3.3 KV Cache 量化

```
单 token KV (Llama-70B): 2.6 MB FP16
  FP8:                    1.3 MB
  INT4 (实验):            0.65 MB

启用:
  vllm: --kv-cache-dtype fp8
  
效果:
  KV 容量翻倍 → 并发翻倍 → 吞吐 ↑
  精度损失: 通常 <1%
```

## 四、批处理（吞吐第二刀）

### 4.1 Continuous Batching

```
传统 static batch:
  等齐 32 个请求 → 一起 forward
  长短不一时:
    短请求等长请求 → 浪费
  
Continuous Batching:
  动态加入 / 离开 batch
  GPU 永不闲
  吞吐 ↑ 3-5x

→ vLLM / SGLang / TGI 默认开启
```

### 4.2 调优参数

```bash
# 显存吃尽
--gpu-memory-utilization 0.95

# 大 batch
--max-num-seqs 256-512        # 并发
--max-num-batched-tokens 8192 # 单步处理 token 总数

# 平衡
若 OOM 抢占多：降并发
若 GPU 闲：升并发
```

## 五、Prefix Cache（命中率第三刀）

### 5.1 收益场景

```
System prompt 1K + 短问题:
  原 TTFT: 200ms
  命中: 30ms
  收益: -85%

RAG (3K context):
  原 TTFT: 800ms
  命中: 50ms
  收益: -94%

Agent 多轮 (history 10K):
  原 TTFT: 2.5s
  命中: 100ms
  收益: -96%

→ Agent / RAG / 长 system prompt 场景必开
```

### 5.2 跨副本共享（LMCache / Mooncake）

```
单副本 prefix cache 在重启 / 扩缩时丢失
多副本相同 prefix 重复计算

解决:
  LMCache: Redis 后端，共享 prefix
  Mooncake: 中心化 KV pool，跨集群共享

部署:
  Decode pool 共享 GPU HBM Cache
  + CPU RAM 多级
  + NVMe 持久化
```

## 六、智能路由（大小模型搭配）

### 6.1 路由策略

```
难度路由（Cost Routing）:
  简单问题 → 8B 模型      ($0.5/1M)
  复杂问题 → 70B 模型     ($5.5/1M)
  代码 → CodeLlama
  数学 → DeepSeek-Math
  推理 → o1 / DeepSeek-R1

  70% 请求路由到小模型 → 成本降 80%

用户分级:
  免费用户 → 8B
  Pro 用户 → 70B
  Enterprise → 405B / API

业务路由:
  Agent 思考 → 大模型
  工具调用 → 小模型
```

### 6.2 RouteLLM 实战

```python
from routellm.controller import Controller

client = Controller(
    routers=["mf"],
    strong_model="Meta-Llama-3-70B",
    weak_model="Meta-Llama-3-8B"
)

# threshold 控制大模型占比
# 0.0 → 100% 弱模型
# 1.0 → 100% 强模型
# 0.116 → 50/50

response = client.chat.completions.create(
    model="router-mf-0.116",
    messages=[...]
)

# 离线评测 MT-Bench:
# 50% 路由到 70B → 同 100% 强模型 95% 质量 → 成本降 50%
```

### 6.3 自建路由

```python
import re

def route(query: str) -> str:
    """Heuristic routing"""
    # 1. 业务标签
    if "code" in query.lower() or re.search(r"```\w+", query):
        return "qwen-coder-32b"
    if any(k in query for k in ["证明", "数学", "推导", "求解"]):
        return "deepseek-math"
    
    # 2. 长度
    if len(query) > 4000:
        return "llama-70b"
    
    # 3. 难度（小 LLM 判断）
    difficulty = classifier_llm.classify(query)
    if difficulty == "easy":
        return "llama-8b"
    elif difficulty == "hard":
        return "llama-70b"
    else:
        return "llama-8b"          # 默认便宜

model = route(query)
response = openai_client.chat.completions.create(model=model, ...)
```

## 七、Response Cache（响应缓存）

### 7.1 适用场景

```
✅ FAQ / 客服
   "退货政策？" → 命中
   缓存命中率 20-50%
   响应 < 50ms

✅ 静态查询
   "Python 语法"
   
❌ 个性化
   "我的订单状态"
   
❌ 时效性
   "今天天气"
```

### 7.2 实现

```python
import hashlib
import redis

r = redis.Redis()

def cached_inference(prompt, model, ttl=3600):
    # Hash key（包含 model + system + prompt）
    key = f"llm:{model}:{hashlib.sha256(prompt.encode()).hexdigest()}"
    
    cached = r.get(key)
    if cached:
        # 命中 → 直接返回（< 1ms）
        return cached.decode()
    
    # Miss → 调推理
    response = llm.invoke(prompt, model=model)
    r.setex(key, ttl, response)
    return response

# 命中率监控
@app.middleware
def cache_metrics():
    if hit: cache_hits.inc()
    else: cache_misses.inc()
```

### 7.3 Semantic Cache（更进阶）

```python
# 不仅完全匹配，相似 query 也命中
from langchain.cache import RedisSemanticCache
from langchain.embeddings import HuggingFaceEmbeddings

cache = RedisSemanticCache(
    embedding=HuggingFaceEmbeddings(model_name="BAAI/bge-small-en"),
    redis_url="redis://localhost",
    score_threshold=0.95          # 余弦相似度 > 0.95 视为命中
)

# 命中率 提升至 40-70%
# 注意：threshold 太低会乱命中
```

## 八、Spot 实例（基础设施降本）

### 8.1 成本对比

```
AWS H100 (p5.48xlarge, 8 × H100):
  On-Demand:  $98/h
  Reserved:   $30/h  (1yr) / $20/h (3yr)
  Spot:       $25-40/h  (浮动)
  
  Spot 单卡: ~$4/h
  按需单卡: ~$12/h
  → 节省 60-70%
```

### 8.2 Spot 中断应对

```yaml
# K8s Pod 优雅退出
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: vllm
          lifecycle:
            preStop:
              exec:
                command:
                  - sh
                  - -c
                  - |
                    # 1. 通知 LB 摘除
                    curl http://lb/drain -d "host=$HOSTNAME"
                    # 2. 等流量切走
                    sleep 30
                    # 3. 优雅停止
                    kill -TERM 1
                    sleep 20
```

### 8.3 混合策略

```
Reserved (base load):  确保 50% 容量稳定
Spot (峰值):           弹性 0-200%
On-Demand (回退):      Spot 不足时

工具:
  - Karpenter (AWS)
  - Cluster Autoscaler + 多 nodegroup
  - 阿里云 SCS / 腾讯云 Spot
```

## 九、Prompt 压缩

### 9.1 LLMLingua

```python
# 智能压缩 prompt（保留关键信息）
from llmlingua import PromptCompressor
compressor = PromptCompressor(model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank")

original = """
You are a helpful assistant. Given the context: ... (10K tokens) ...
Answer the question: What is the capital of France?
"""

compressed = compressor.compress_prompt(original, rate=0.3)
# 压缩到 30%（约 3K tokens）
# 答案质量保持 95%+
# Cost 降 70%
```

### 9.2 RAG 重排去重

```python
# 不要把 top-10 全塞 LLM
docs = retriever.retrieve(query, k=20)
docs = reranker.rerank(query, docs)[:3]   # top-3 真正相关

# 去重
docs = list(dict.fromkeys(docs))

# 截断
docs = [d[:500] for d in docs]            # 每段 < 500 tokens

# 最终 prompt:
# system + 1.5K context + question
# vs 原 10K context → 节省 85% input tokens
```

### 9.3 多轮上下文摘要

```python
# 不要每轮都带完整 history
def truncate_history(history, max_tokens=2000):
    if count_tokens(history) > max_tokens:
        # 旧的 N 轮摘要 + 最近 3 轮原文
        summary = summarize_llm.invoke(history[:-3])
        return f"Summary: {summary}\n\n" + format(history[-3:])
    return format(history)
```

## 十、Speculative Decoding（加速降本）

### 10.1 原理

```
Draft Model (小) 生成 K 个 token
Target Model (大) 并行 verify
接受率 60-80% → 一次 forward 出 K 个 token
速度 ↑ 2-3x

成本含义:
  - 大模型 FLOPs 相同
  - 但 wall-clock 时间 / token 降 50%+
  - 同 GPU 同时间内吞吐更高
  - 单 token 成本 ↓
```

### 10.2 启用

```bash
# vLLM + EAGLE
vllm serve meta-llama/Meta-Llama-3-70B-Instruct \
  --speculative-model "lmsys/sglang-EAGLE-llama3-70B" \
  --num-speculative-tokens 5 \
  --speculative-draft-tensor-parallel-size 1

# vLLM + N-gram (无需训练)
vllm serve ... \
  --speculative-model "[ngram]" \
  --num-speculative-tokens 5 \
  --ngram-prompt-lookup-max 4

# TRT-LLM EAGLE-3
trtllm-build --use_speculative_decoding ...
```

### 10.3 适用场景

```
✅ 适合:
  - 小 batch（speculative 收益大）
  - 重复性输出（code / 结构化）
  - 短输出（验证开销小）

❌ 不适合:
  - 大 batch (> 32)
  - 创意写作（接受率低）
```

## 十一、MoE 模型（架构降本）

### 11.1 Mixture of Experts

```
Mixtral 8x7B = 47B 总参数 / 13B 激活
DeepSeek-V3 = 671B 总参数 / 37B 激活
Qwen-MoE = 14B 总 / 2.7B 激活

优势:
  - 同质量 LLM，激活参数小 1/5
  - 速度 + 成本接近小模型
  - 质量接近大模型

部署:
  - vLLM / SGLang MoE 优化
  - Expert Parallelism
  - 比稠密模型部署复杂
```

### 11.2 DeepSeek-V3 部署

```bash
# SGLang MoE 友好
python -m sglang.launch_server \
  --model-path deepseek-ai/DeepSeek-V3 \
  --tp 8 --ep 8 \              # Tensor + Expert Parallel
  --enable-dp-attention \
  --port 30000

# 单 H100 节点跑 671B（FP8 量化）
# 同质量比 Llama-405B FP16 快 3x
```

## 十二、MIG / GPU 共享

### 12.1 适用场景

```
✅ 多租户 / 多模型
✅ 小模型 (< 20B)
✅ 流量稀疏的服务

❌ 单租户 / 大模型
❌ 高吞吐需求
```

### 12.2 H100 MIG 配置

```bash
# 7 个 1g.10gb 实例
nvidia-smi mig -cgi 1g.10gb,1g.10gb,1g.10gb,1g.10gb,1g.10gb,1g.10gb,1g.10gb -C

# K8s 中
resources:
  limits:
    nvidia.com/mig-1g.10gb: 1

# 适合跑 7B / 8B 模型
# 一张 H100 服务 7 个独立租户
```

## 十三、国产 GPU 替代

### 13.1 性价比对比（参考）

```
8 × H100 80G:     ~$200k (整机)
8 × 昇腾 910B:    ~$120k (-40%)
8 × 海光 K100:    ~$100k (-50%)
8 × 寒武纪 590:   ~$130k (-35%)

注意:
  - 软件生态成本高（适配 / 维护）
  - 性能略低（70-90%）
  - 信创合规价值高
```

### 13.2 昇腾迁移成本

```python
# Llama / Qwen 模型在昇腾 910B 上
# 通过 MindSpore-Lite / vLLM-Ascend / TGI-Ascend

# 适配工作:
# 1. 模型转换（HF → MindSpore / OM）
# 2. 量化（INT8 over W4A8）
# 3. 性能调优（kernel 重写）
# 4. 兼容性测试

# 建议:
# - 通用场景：等社区 vLLM-Ascend 成熟（2024+ 已可用）
# - 信创合规：直接用 MindIE / 昇腾官方部署框架
```

## 十四、成本监控与归因

### 14.1 关键指标

```
全局:
  Total Cost / day
  Tokens / dollar
  Cost / 1M input tokens
  Cost / 1M output tokens

按用户:
  Top 10 users by cost
  Avg cost / user / day
  Cost vs revenue

按特性:
  Feature A: $X / day
  Feature B: $Y / day
  → 砍掉低 ROI 特性

按模型:
  Cost by model
  Quality vs Cost
```

### 14.2 Langfuse 成本归因

```python
# 每个 trace 自动算 cost
from langfuse import Langfuse
lf = Langfuse()

# 自定义 model pricing
lf.create_model(
    name="my-llama-70b",
    input_price=0.000005,    # $5/1M tokens
    output_price=0.000005,
)

# trace 自动算 cost
trace = lf.trace(name="qa", user_id="user-123")
generation = trace.generation(
    model="my-llama-70b",
    usage={"input": 1500, "output": 300}
)
# 自动算 cost = 1500 * 0.000005 + 300 * 0.000005 = $0.009

# Dashboard 看:
# - 各用户成本
# - 各 feature 成本
# - 各 model 成本
# - 时间趋势
```

### 14.3 配额管理

```python
# LiteLLM Proxy 自带用户/key 配额
# config.yaml:
general_settings:
  database_url: postgres://...
  max_budget: 100        # 每个用户每月 $100

# 超额拒绝 / 降级到便宜模型
```

## 十五、成本优化案例

### 15.1 RAG 客服系统降本

```
原配置:
  - GPT-4o 全场景
  - 月成本: $15,000

优化路径:
  1. 接入 70B 自建 (50% 流量) → 月省 $4,000
  2. FAQ Response Cache (40% 命中) → 月省 $3,000
  3. 难度路由 (60% 简单 → 8B) → 月省 $2,500
  4. Prompt 压缩 (input -50%) → 月省 $1,500
  5. Prefix Cache (system prompt) → 月省 $800
  
最终月成本: $3,200 (-78%)
质量: 90% 不变
```

### 15.2 Agent 工作流降本

```
原:
  Agent 每次调用 GPT-4 → $0.5/次
  日 10,000 次 → $5,000/天

优化:
  1. 思考用 70B 自建 (0.0055)
  2. 工具调用判断用 8B (0.0005)
  3. 结构化输出 SGLang 严格 schema → 减少重试
  4. Cache history → input -60%

最终: $0.08/次 → $800/天 (-84%)
```

### 15.3 长文档摘要降本

```
原:
  100页 PDF → 50K tokens prompt → GPT-4o
  $0.5/次 × 100次/天 = $50/天

优化:
  1. RAG 抽取关键段 → 5K tokens
  2. 70B 自建摘要
  3. Map-Reduce 分块（小模型先 map → 大模型 reduce）
  4. 摘要 cache（同文档重复请求）

最终: $0.02/次 × 100 = $2/天 (-96%)
```

## 十六、典型坑

| 坑 | 建议 |
|:---|:---|
| **盲目自建** | 算 TCO，小规模用 API |
| **不量化** | AWQ INT4 / FP8 必上 |
| **不开 Prefix Cache** | RAG/Agent 必开 |
| **所有请求一个模型** | 路由 + 大小搭配 |
| **不监控成本** | Langfuse + 配额 |
| **Cache 太激进** | 个性化场景慎用 |
| **Spot 没回退** | Reserved + Spot 混合 |
| **国产 GPU 没适配** | 提前 POC |
| **MoE 部署没优化** | EP 并行 |
| **Speculative 大 batch** | 收益反而低 |
| **Agent 全程 70B** | 简单步骤换 8B |
| **不限 max_tokens** | 用户烧爆预算 |
| **History 不截断** | 内存爆 + 烧 input |
| **全文档 RAG 不抽取** | top-K + rerank |
| **同 prompt 重复算** | Response cache |

## 十七、Checklist

```
模型:
☐ AWQ INT4 或 FP8 量化
☐ KV Cache FP8
☐ MoE 候选评估
☐ Speculative Decoding

引擎:
☐ Continuous Batching
☐ Prefix Caching (跨副本 LMCache)
☐ Chunked Prefill (长 context)
☐ PD 分离 (大规模)

调度:
☐ 难度路由 (RouteLLM)
☐ 用户分级
☐ Response Cache
☐ Semantic Cache

基础设施:
☐ Spot + Reserved 混合
☐ HPA / KEDA 弹性
☐ MIG 共享 (合适场景)
☐ 国产 GPU POC

应用:
☐ Prompt 压缩 (LLMLingua)
☐ RAG rerank + 抽取
☐ History 摘要
☐ Max tokens 严格
☐ 流式提前停止

监控:
☐ Cost per user / feature
☐ Token 消耗看板
☐ 配额管理
☐ 月度成本复盘
```

## 十八、推荐栈（2025）

### 18.1 中小团队

```
模型:    Llama-3-70B-AWQ / Qwen2.5-72B-AWQ
引擎:    vLLM + Prefix Cache + FP8 KV
路由:    LiteLLM Proxy + 简单规则
缓存:    Redis Response Cache
监控:    Langfuse + Cost dashboard
```

### 18.2 中大企业

```
+ RouteLLM 难度路由
+ LMCache 跨副本 prefix
+ MoE 模型混部 (DeepSeek-V3)
+ Spot + Reserved 混合
+ Semantic Cache
+ A/B 自动评测 (Langfuse Eval)
+ MIG 多租户切片
```

### 18.3 大规模

```
+ PD 分离 + Mooncake
+ 自研 cost-aware 路由
+ 跨集群弹性
+ 国产 GPU 混合
+ Prompt 压缩 pipeline
+ 离线评测 + 持续优化
```

## 十九、学习路径

```
入门（2 周）:
  1. 量化（AWQ + FP8）
  2. KV Cache FP8
  3. Prefix Caching
  4. 基础 Response Cache

中级（1 月）:
  5. 难度路由 (RouteLLM)
  6. LMCache 部署
  7. Spot 实例 + 回退
  8. Langfuse Cost 归因

高级（3 月+）:
  9. PD 分离
  10. MoE 部署优化
  11. Semantic Cache
  12. Prompt 压缩 pipeline
  13. 自动 A/B

专家:
  14. 国产 GPU 适配
  15. 自研路由 + cache 框架
  16. 全栈成本治理
```

## 二十、参考资料

```
论文:
  - LLMLingua / LongLLMLingua (Prompt 压缩)
  - RouteLLM (Anyscale)
  - DeepSeek-V3 / Mixtral MoE
  - EAGLE-3 (Speculative)
  - Mooncake (FAST '25)

工具:
  - LLMLingua: https://github.com/microsoft/LLMLingua
  - RouteLLM: https://github.com/lm-sys/RouteLLM
  - LMCache: https://github.com/LMCache/LMCache
  - Langfuse: https://langfuse.com/
  - LiteLLM: https://docs.litellm.ai/

数据:
  - Artificial Analysis (model 性能对比)
  - LLM Pricing Comparison
  - SemiAnalysis (硬件成本)
```

> 📖 **核心判断**：LLM 推理降本 = **量化 + KV 量化 + Prefix Cache + 难度路由 + Cache** 五招打底，能把成本降 60-80%。大模型场景再上 **PD 分离 + MoE + Spot + 国产 GPU**。**最常被忽视的不是性能，而是 Response Cache 和难度路由——同一句"hello"被算 1000 次，60% 简单问题被发到 70B 模型**——把这两个补上，立竿见影。**永远监控 Token 消耗，按用户/特性归因**，不然降本就是无头苍蝇。

