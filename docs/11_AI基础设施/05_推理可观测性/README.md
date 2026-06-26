# 推理可观测性

> LLM 推理可观测 = **三大支柱（Metrics + Logs + Traces）+ LLM 专有指标（TTFT/TPOT/Throughput/MBU）+ 业务指标（Quality/Cost/Hallucination）**。**Prometheus + Grafana + Langfuse + OpenTelemetry** 是 2025 标配。

## 一、LLM 可观测三维

```
传统应用:                LLM 应用:
  - CPU / 内存             - GPU 显存 / 显存带宽
  - QPS / 延迟              - TTFT / TPOT / Goodput
  - 错误率                  - 错误率 + 质量评估
                            - Token 消耗（成本）
                            - 模型漂移
                            - 幻觉率
                            - User Feedback
                            - 安全（Prompt Injection / Jailbreak）

→ LLM 多了 "成本 + 质量 + 安全" 三维
→ 传统 APM 不够用
```

## 二、核心指标（必监控）

### 2.1 性能指标

```
TTFT (Time-To-First-Token) ⭐
  首 token 延迟
  目标 P99 < 500ms (短 prompt)
  P99 < 2s (4K prompt)

TPOT (Time-Per-Output-Token) ⭐
  每生成 token 平均耗时
  目标 P99 < 50ms (流式聊天体验)

ITL (Inter-Token Latency)
  token 间隔抖动
  P99 - P50 < 30ms

E2E Latency
  端到端（=TTFT + N × TPOT）

Throughput
  Tokens/s (output) ⭐
  Tokens/s (input + output)
  Requests/s

Goodput
  有效吞吐（剔除超时 / 错误）

Queue Time
  请求排队时间
  P99 < 100ms 才合格
```

### 2.2 资源指标

```
GPU:
  SM Util %               真实算力利用
  Memory Util %           显存带宽利用 ⭐ memory-bound 关键
  Memory Used GB
  Temp / Power / Clock

KV Cache:
  Utilization %           ⭐ vLLM 核心指标
  Hit Rate (Prefix Cache) ⭐
  Spillover (CPU offload)

Engine:
  Running Requests
  Waiting Requests
  Preempted Requests      ⭐ 抢占说明过载
  Swapped Requests        ⭐ 显存不够换 CPU
  Generation Throughput
  Prefill Throughput
```

### 2.3 业务指标

```
Tokens 消耗:
  Input Tokens / 次
  Output Tokens / 次
  Total Tokens / 天 / 用户 / 模型

成本:
  Cost per 1K input tokens
  Cost per 1K output tokens
  Cost per user / day
  Cost per request

质量:
  User Feedback (thumbs up/down)
  Refusal Rate (模型拒答率)
  Hallucination Score (检测幻觉)
  Quality Score (LLM-as-judge)

安全:
  Prompt Injection 检出
  Jailbreak 尝试
  PII 泄漏
  毒性输出

业务:
  Conversion Rate
  Session Length
  Active Users
  Retention
```

## 三、Prometheus + vLLM Metrics

### 3.1 vLLM 内置 metrics

```bash
# vLLM 0.4+ 自带 /metrics endpoint
curl http://vllm:8000/metrics

# 关键指标（部分）:
vllm:num_requests_running              # 运行中请求数
vllm:num_requests_waiting              # 排队请求数
vllm:num_requests_swapped              # 换出的请求
vllm:gpu_cache_usage_perc              # KV cache 利用率 ⭐
vllm:cpu_cache_usage_perc              # CPU offload cache
vllm:num_preemptions_total             # 抢占次数

vllm:prompt_tokens_total                # input token 累计
vllm:generation_tokens_total            # output token 累计

vllm:time_to_first_token_seconds       # TTFT histogram
vllm:time_per_output_token_seconds     # TPOT histogram
vllm:e2e_request_latency_seconds       # E2E

vllm:request_prefill_time_seconds      # Prefill 时间
vllm:request_decode_time_seconds       # Decode 时间
vllm:request_queue_time_seconds        # 排队时间

vllm:request_success_total              # 成功请求数
vllm:cache_config_info                  # 配置信息

vllm:lora_requests_info                 # LoRA 使用情况
vllm:spec_decode_num_accepted_tokens   # 推测解码接受数
```

### 3.2 SGLang metrics

```bash
curl http://sglang:30000/metrics

# 关键:
sglang:num_running_reqs
sglang:num_waiting_reqs
sglang:cache_hit_rate                   # RadixCache 命中率 ⭐
sglang:gen_throughput
sglang:prefill_throughput
sglang:queue_time_seconds
```

### 3.3 Prometheus 配置

```yaml
# prometheus.yml
scrape_configs:
  - job_name: vllm
    scrape_interval: 5s
    static_configs:
      - targets:
          - vllm-1:8000
          - vllm-2:8000
    metrics_path: /metrics
  
  - job_name: dcgm
    scrape_interval: 5s
    static_configs:
      - targets: ['dcgm-exporter:9400']
  
  - job_name: sglang
    static_configs:
      - targets: ['sglang:30000']
  
  # 节点
  - job_name: node-exporter
    static_configs:
      - targets: ['node-exporter:9100']
```

### 3.4 K8s ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: vllm
  labels: { release: prometheus }
spec:
  selector:
    matchLabels: { app: vllm }
  endpoints:
    - port: http                          # service port name
      path: /metrics
      interval: 5s
```

## 四、Grafana 仪表盘

### 4.1 推理服务监控

```promql
# 实时 TTFT P99
histogram_quantile(0.99, 
  sum by(le, model) (rate(vllm:time_to_first_token_seconds_bucket[2m]))
)

# TPOT P99
histogram_quantile(0.99,
  sum by(le, model) (rate(vllm:time_per_output_token_seconds_bucket[2m]))
) * 1000   # ms

# Throughput (tokens/s)
sum by(model) (rate(vllm:generation_tokens_total[2m]))

# QPS
sum by(model) (rate(vllm:request_success_total[2m]))

# KV Cache 利用率
avg by(model) (vllm:gpu_cache_usage_perc)

# Queue Length
sum by(model) (vllm:num_requests_waiting)

# Preemption rate
sum by(model) (rate(vllm:num_preemptions_total[5m]))

# 各模型 QPS 分布
sum by(model) (rate(vllm:request_success_total[2m]))

# 用户级 Token 消耗（需打 user label）
sum by(user) (rate(vllm:generation_tokens_total[1h])) * 3600
```

### 4.2 GPU 监控（DCGM）

```promql
# GPU 利用率（SM Util）
DCGM_FI_PROF_SM_OCCUPANCY{gpu=~"$gpu"}

# 显存利用
DCGM_FI_DEV_MEM_COPY_UTIL{gpu=~"$gpu"}

# 显存占用
DCGM_FI_DEV_FB_USED{gpu=~"$gpu"} / DCGM_FI_DEV_FB_TOTAL{gpu=~"$gpu"}

# 温度
DCGM_FI_DEV_GPU_TEMP{gpu=~"$gpu"}

# 功耗
DCGM_FI_DEV_POWER_USAGE{gpu=~"$gpu"}

# XID 错误
DCGM_FI_DEV_XID_ERRORS{gpu=~"$gpu"}

# 已知 dashboard:
# - vLLM: Grafana ID 21130
# - DCGM: Grafana ID 12239
# - NVIDIA GPU: 14574
```

### 4.3 Dashboard 设计模板

```
推理服务概览页:
  ┌─────────────┬─────────────┬─────────────┐
  │ QPS         │ TTFT P99    │ TPOT P99    │
  │ 245 req/s   │ 187 ms       │ 28 ms        │
  ├─────────────┼─────────────┼─────────────┤
  │ Throughput  │ Queue Len   │ Error Rate  │
  │ 4520 tok/s  │ 5            │ 0.02%       │
  └─────────────┴─────────────┴─────────────┘
  
  时序图:
    - TTFT/TPOT 趋势（5min）
    - QPS by model
    - GPU 利用率（SM/Mem/Temp）
    - KV Cache 利用率
    - Queue Length
    - Token 累计（input/output）
  
  分布图:
    - Latency Heatmap
    - Token 长度分布
    - User TPM 分布
```

## 五、Langfuse / Helicone（LLM 业务监控）

### 5.1 为什么需要 LLM 专用监控

```
Prometheus + Grafana 解决:
  ✅ 性能 / 资源 / 错误率

但解决不了:
  ❌ 单次请求完整 prompt + response（追踪问题）
  ❌ 模型质量评估
  ❌ 用户反馈关联
  ❌ Agent 多步骤追踪
  ❌ 成本归因到用户/特性
  ❌ Prompt 版本管理 + A/B
  ❌ 数据集采集（fine-tune 用）

→ 需要 LLM 专用平台
```

### 5.2 Langfuse（开源 ⭐ 推荐）

```bash
# Docker 部署
git clone https://github.com/langfuse/langfuse
cd langfuse
docker-compose up -d
# Web: http://localhost:3000

# Python SDK
pip install langfuse

from langfuse.openai import openai          # 自动 trace

client = openai.OpenAI(
    base_url="http://vllm:8000/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="llama-3-70b",
    messages=[{"role": "user", "content": "Hi"}],
    name="my-trace",                      # 自定义名称
    user_id="user-123",                   # 用户归因
    session_id="sess-xyz",                # 会话归因
    metadata={"feature": "chatbot", "version": "v2"}
)
# 自动上报 prompt / response / tokens / cost / latency
```

```python
# 手动 trace (Agent / RAG)
from langfuse import Langfuse
lf = Langfuse()

trace = lf.trace(name="rag-query", user_id="user-123")

retrieval = trace.span(name="retrieval", input=query)
docs = retriever.retrieve(query)
retrieval.end(output=docs)

generation = trace.generation(
    name="answer",
    model="llama-3-70b",
    input=prompt,
    output=answer,
    usage={"input": 1200, "output": 350}
)
trace.end()

# Langfuse UI 上：
#   - 完整 trace tree
#   - 每个 span 耗时 / token / cost
#   - prompt + response 全文
#   - 关联用户 / session / metadata
```

### 5.3 Helicone（替代品）

```python
# Helicone 通过 proxy 自动 trace
client = OpenAI(
    base_url="https://oai.helicone.ai/v1",   # 走代理
    api_key=OPENAI_KEY,
    default_headers={
        "Helicone-Auth": f"Bearer {HELICONE_KEY}",
        "Helicone-User-Id": "user-123",
        "Helicone-Property-Feature": "chatbot",
    }
)

# 后台:
#   - dashboard.helicone.ai
#   - 自动监控所有 API 调用
#   - 缓存 + 限流 + 重试 + A/B
```

### 5.4 评估与 Dataset

```python
# Langfuse Datasets（自动评估）
from langfuse import Langfuse
lf = Langfuse()

# 1. 创建评估集
dataset = lf.create_dataset(name="customer-qa")
for item in seed_data:
    lf.create_dataset_item(
        dataset_name="customer-qa",
        input=item["question"],
        expected_output=item["answer"]
    )

# 2. 跑评估
for item in lf.get_dataset("customer-qa").items:
    answer = my_rag_pipeline(item.input)
    item.link(trace_id=current_trace_id, run_name="v2.0")

# 3. 在 Langfuse UI 看对比
#    - v1.0 vs v2.0 准确率
#    - 哪些 query 退化
#    - LLM-as-judge 自动评分
```

## 六、OpenTelemetry 集成

### 6.1 OTel 标准

```
2024+ LLM Semantic Conventions 已立标准
  - gen_ai.system               (openai, anthropic, vllm, ...)
  - gen_ai.request.model
  - gen_ai.request.max_tokens
  - gen_ai.request.temperature
  - gen_ai.response.model
  - gen_ai.usage.input_tokens
  - gen_ai.usage.output_tokens
  - gen_ai.response.finish_reasons

→ 所有 trace 系统可消费
```

### 6.2 OpenLLMetry（OTel for LLM）

```bash
pip install traceloop-sdk

from traceloop.sdk import Traceloop
Traceloop.init(api_endpoint="http://otel-collector:4317")

# 自动 instrument:
# - openai / anthropic / cohere / langchain / llamaindex / vllm
# - 自动产生 OTel trace
# - 任何 OTel-compatible backend 可消费 (Jaeger, Tempo, DataDog, ...)

import openai
response = openai.chat.completions.create(...)
# 自动 trace
```

### 6.3 OTel Collector 配置

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }

processors:
  batch:
  attributes:
    actions:
      - key: gen_ai.usage.cost
        action: insert
        from_attribute: gen_ai.usage.input_tokens
        # 计算成本（自定义 processor）

exporters:
  otlphttp/langfuse:
    endpoint: https://cloud.langfuse.com/api/public/otel
  prometheus:
    endpoint: 0.0.0.0:8889
  loki:
    endpoint: http://loki:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, attributes]
      exporters: [otlphttp/langfuse]
    metrics:
      receivers: [otlp]
      exporters: [prometheus]
```

## 七、日志

### 7.1 vLLM 日志配置

```bash
# 关闭请求日志（高并发降噪）
vllm serve --disable-log-requests

# 自定义日志级别
VLLM_LOGGING_LEVEL=DEBUG vllm serve ...

# 结构化日志
vllm serve ... 2>&1 | jq -c
```

### 7.2 Loki + Promtail

```yaml
# promtail-config.yaml
scrape_configs:
  - job_name: vllm
    static_configs:
      - targets: [localhost]
        labels:
          job: vllm
          __path__: /var/log/vllm/*.log
    pipeline_stages:
      - json:
          expressions:
            level:
            request_id:
            user_id:
            model:
            tokens:
      - labels:
          level:
          model:
      - timestamp:
          source: timestamp
          format: RFC3339
```

### 7.3 关键日志事件

```
✅ 记录:
  - 请求开始 / 结束（含 user, model, tokens）
  - 错误（4xx / 5xx）
  - GPU OOM
  - Preemption / Swap
  - 模型加载 / 卸载
  - LoRA 加载
  - Prompt injection 检测

❌ 不记录（合规）:
  - 完整 prompt（PII 风险）→ 摘要 / hash
  - 用户身份证 / 邮箱
  → 用 Langfuse 受控环境
```

## 八、告警规则（生产必备）

```yaml
# prometheus alerts
groups:
  - name: vllm
    rules:
      - alert: VllmTTFTHigh
        expr: |
          histogram_quantile(0.99,
            sum by(le, model) (rate(vllm:time_to_first_token_seconds_bucket[5m]))
          ) > 2
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "TTFT P99 > 2s on {{ $labels.model }}"
      
      - alert: VllmTPOTHigh
        expr: |
          histogram_quantile(0.99,
            sum by(le, model) (rate(vllm:time_per_output_token_seconds_bucket[5m]))
          ) > 0.1
        for: 5m
        labels: { severity: warning }
      
      - alert: VllmQueueTooLong
        expr: vllm:num_requests_waiting > 50
        for: 3m
        labels: { severity: critical }
      
      - alert: VllmPreemptionHigh
        expr: rate(vllm:num_preemptions_total[5m]) > 10
        for: 5m
        labels: { severity: critical }
      
      - alert: VllmGPUMemoryHigh
        expr: vllm:gpu_cache_usage_perc > 0.95
        for: 5m
        labels: { severity: warning }
      
      - alert: GPUTempHigh
        expr: DCGM_FI_DEV_GPU_TEMP > 85
        for: 5m
        labels: { severity: critical }
      
      - alert: GPUECCError
        expr: increase(DCGM_FI_DEV_XID_ERRORS[1h]) > 0
        labels: { severity: critical }
        annotations:
          summary: "XID error on GPU {{ $labels.gpu }}"
      
      - alert: VllmErrorRateHigh
        expr: |
          sum(rate(vllm:request_errors_total[5m])) /
          sum(rate(vllm:request_total[5m])) > 0.01
        for: 5m
        labels: { severity: critical }
```

## 九、SLI / SLO 设计

### 9.1 推理服务 SLI

```
可用性 SLI:
  Success Rate = success_requests / total_requests

性能 SLI:
  TTFT < 500ms 占比     (prompt < 1K)
  TTFT < 2s 占比         (prompt 1K-8K)
  TPOT < 50ms 占比

容量 SLI:
  Goodput (剔除超时)
  QPS 上限
```

### 9.2 SLO 目标（参考）

```
Chat 应用:
  Availability    99.5% / month
  TTFT P99        < 500ms (短) / 2s (长)
  TPOT P99        < 50ms
  Error Rate       < 0.5%

API 服务:
  Availability    99.9%
  TTFT P99        < 1s
  TPOT P99        < 30ms

Agent / 复杂任务:
  Availability    99.0%
  E2E P99          < 30s
  Success Rate     > 90%

→ 错误预算 = 1 - SLO
  99.5% → 1 月 3.6 小时不可用
  99.9% → 1 月 43 分钟
```

### 9.3 Error Budget 燃烧告警

```promql
# Burn Rate Alert（快烧 / 慢烧）
sum(rate(vllm:request_errors_total[5m])) / sum(rate(vllm:request_total[5m]))
  > 14.4 * (1 - 0.995)    # 14.4x 速率 = 1h 烧完 1 天预算
```

## 十、Trace（分布式追踪）

### 10.1 RAG / Agent 多步追踪

```python
# OpenTelemetry RAG trace
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("rag-pipeline")
def rag_query(question: str):
    with tracer.start_as_current_span("embed"):
        emb = embedder.embed(question)
    
    with tracer.start_as_current_span("retrieve") as span:
        docs = vector_db.search(emb, top_k=10)
        span.set_attribute("doc_count", len(docs))
    
    with tracer.start_as_current_span("rerank"):
        docs = reranker.rerank(question, docs)[:3]
    
    with tracer.start_as_current_span("generate") as span:
        prompt = format_prompt(question, docs)
        span.set_attribute("gen_ai.request.model", "llama-3-70b")
        response = llm.invoke(prompt)
        span.set_attribute("gen_ai.usage.input_tokens", count(prompt))
        span.set_attribute("gen_ai.usage.output_tokens", count(response))
    
    return response

# Jaeger UI 可视化:
# rag-pipeline (5.3s)
#   ├─ embed       (20ms)
#   ├─ retrieve    (80ms)
#   ├─ rerank      (200ms)
#   └─ generate    (5000ms)  ← 瓶颈
```

### 10.2 Jaeger / Tempo / Langfuse

```
工具选型:
  Jaeger          老牌通用 trace
  Tempo           Grafana 出品 (与 Loki/Prometheus 一体)
  Langfuse        LLM 业务级 ⭐
  Phoenix (Arize) LLM eval + trace
  LangSmith       LangChain 官方
```

## 十一、质量监控（Quality）

### 11.1 自动评估

```python
# LLM-as-judge
def quality_score(question, answer, ground_truth):
    judge_prompt = f"""
    Rate the answer quality (1-10) compared to ground truth.
    Question: {question}
    Answer: {answer}
    Ground Truth: {ground_truth}
    Score only:
    """
    score = judge_llm.invoke(judge_prompt)
    return float(score)

# 抽样 1% 流量评估
if random() < 0.01:
    quality = quality_score(q, a, gt)
    prometheus_metric.observe(quality)
```

### 11.2 漂移检测

```
模型质量漂移:
  ↓ Accuracy on benchmark
  ↑ Refusal rate
  ↑ Toxicity score
  ↑ Hallucination rate

工具:
  - Phoenix (Arize)
  - Evidently AI
  - Langfuse Evals
  - 自研周期评测

自动告警: 关键指标降 10% → 阻断发布 / 回滚
```

### 11.3 安全监控

```
Prompt Injection 检测:
  - LLM Guard
  - Rebuff
  - PromptArmor
  - LangKit (Whylabs)
  - 国产: 火山方舟内容安全

PII 检测:
  - Presidio (微软)
  - 关键词 + 正则 + NER

Jailbreak 检测:
  - 已知 jailbreak prompt 库
  - 行为异常基线

合规审计:
  - 全 prompt / response 留存（脱敏）
  - 国内: 等保 / 个保法
```

## 十二、典型坑

| 坑 | 建议 |
|:---|:---|
| **只看 TTFT 不看 TPOT** | 都看（用户感受是 TPOT 慢） |
| **histogram bucket 太粗** | 加 0.1/0.2/0.5/1/2/5/10s |
| **不监控 KV Cache 利用** | vLLM 核心指标 |
| **抢占发生不告警** | 必告警（说明过载） |
| **没监控 GPU XID** | DCGM exporter 必装 |
| **日志记完整 prompt** | PII / 合规风险 |
| **告警没分级** | warning vs critical 区分 |
| **SLO 拍脑袋** | 业务需求驱动 |
| **trace 采样率 100%** | 1-10% 已够 |
| **DataDog 全开** | 成本爆炸 / 采样 + 自托管 |
| **不监控成本** | 单 user / day token 监控 |
| **没质量监控** | 模型漂移无感知 |
| **多副本指标不聚合** | 加 model / version label |
| **Token 数与 cost 关联弱** | 接 Langfuse |
| **告警直接发开发** | 走 AlertManager 分级 |

## 十三、最佳实践 Checklist

```
基础（必须）:
☐ vLLM /metrics 接 Prometheus
☐ DCGM exporter 接 Prometheus
☐ Grafana dashboard 部署
☐ 关键告警规则（5个起）
☐ TTFT/TPOT/QPS/Error 监控

中级（推荐）:
☐ Langfuse / Helicone 接入
☐ User / Model / Feature 维度归因
☐ Token 消耗 + Cost 监控
☐ SLI/SLO 定义
☐ Error Budget 燃烧告警
☐ OpenTelemetry trace
☐ AlertManager 分级路由

高级（生产标杆）:
☐ 质量自动评估（LLM-as-judge）
☐ 漂移检测
☐ A/B 自动评测
☐ Prompt injection / PII 监控
☐ Dataset 自动采集
☐ 用户反馈关联
☐ 跨服务 RAG/Agent trace
☐ 等保审计留存
```

## 十四、推荐栈（2025）

### 14.1 中小团队

```
Metric:    Prometheus + Grafana + DCGM
LLM:       Langfuse 自托管
Log:       Loki + Promtail
Trace:     OpenTelemetry + Langfuse
Alert:     AlertManager + 飞书
```

### 14.2 中大企业

```
+ Mimir / Thanos (Prometheus 长期存储)
+ Tempo (Trace 长期存储)
+ Langfuse Enterprise / Helicone Pro
+ Arize Phoenix (评估)
+ DataDog / NewRelic (商业全栈)
+ PagerDuty / 国内: 派欧云
```

### 14.3 大规模

```
+ 自研监控平台
+ 自动质量评估流水线
+ 全栈关联（业务 + 推理 + GPU）
+ AIOps（详见 12_AIOps）
+ 实时漂移检测
+ 安全审计 + 国密合规
```

## 十五、学习路径

```
入门（2 周）:
  1. Prometheus + Grafana 部署
  2. vLLM metrics 接入
  3. DCGM exporter
  4. 基础 dashboard

中级（1 月）:
  5. Langfuse 部署 + SDK
  6. SLO / Error Budget
  7. AlertManager 分级
  8. OpenTelemetry trace

高级（3 月+）:
  9. RAG / Agent trace
  10. 质量评估 + A/B
  11. 漂移检测 + 自愈
  12. 跨集群聚合

专家:
  13. 自研评估平台
  14. AIOps 集成
  15. 安全 + 合规审计
```

## 十六、参考资料

```
官方:
  - vLLM Metrics: https://docs.vllm.ai/en/latest/serving/metrics.html
  - DCGM Exporter: https://github.com/NVIDIA/dcgm-exporter
  - OpenLLMetry: https://github.com/traceloop/openllmetry
  - Langfuse: https://langfuse.com/docs
  - OTel GenAI Conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/
  - Phoenix: https://docs.arize.com/phoenix

社区:
  - SRE Workbook (SLO)
  - Grafana Dashboards 21130 / 12239
  - r/LocalLLaMA (监控讨论)

报告:
  - The State of LLM Observability (Galileo)
  - LLM Reliability Survey (Microsoft)
```

> 📖 **核心判断**：LLM 可观测 = **传统三大支柱（Prometheus/Loki/Trace）+ LLM 专有维度（TTFT/TPOT/Token/Cost/Quality/Safety）**。**Prometheus+Grafana+DCGM** 解决性能与资源问题（基础设施层），**Langfuse / Helicone** 解决业务与质量问题（应用层）——**两层都要有**。最容易翻车的是只监控 TTFT 不监控 TPOT，导致用户感受卡顿但仪表盘"一切正常"；以及不监控 KV Cache 利用率，导致抢占暴增却找不到原因。

