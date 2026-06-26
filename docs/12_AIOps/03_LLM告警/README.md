# LLM 告警

> 用大模型把"告警风暴 + 海量上下文 + 多源信号"压缩成**一句人类能读懂的话 + 可执行建议**。**这是 2025 AIOps 落地最快、ROI 最高的方向**。

## 一、为什么需要 LLM 告警

```
传统告警的硬伤:
  - 一次故障 → 几十上百条告警
  - 信息碎片化（Prom 告警/Trace/日志/K8s 事件分散）
  - 缺乏上下文（值班看到"CPU 高"不知该不该处理）
  - 经验依赖人（老工程师离职 → 知识断层）
  - 跨团队语言不同（开发/运维/SRE/DBA 各说各的）

LLM 解决:
  ✅ 多源信号融合（指标 + 日志 + Trace + 变更 + Runbook）
  ✅ 自然语言摘要（一句话讲清故障）
  ✅ 根因建议（"很可能是 XXX 引起，建议先 YYY"）
  ✅ 自动调用工具（Function Calling 执行命令）
  ✅ 知识沉淀（Runbook + 历史故障 RAG）
```

## 二、LLM 告警的四代演进

| 代 | 形态 | 特点 |
|:---:|:---|:---|
| **0 代** | 模板拼接 | Prom 告警 + 邮件模板 |
| **1 代** | LLM 摘要 | 单条告警喂 LLM 生成自然语言 |
| **2 代** | RAG 增强 | 拼接 Runbook / 历史故障 / Wiki |
| **3 代** | Agent + Tools | LLM 自主调用 kubectl/SQL/HTTP 取证 |
| **4 代** | 多 Agent 协作 | 多角色 Agent（SRE/DBA/网络）协同 |

**当前主流：2-3 代**。4 代仅头部团队（字节、阿里、Google SRE）在试。

## 三、典型架构

```
┌────────── 告警源 ──────────────────────────┐
│ Prometheus Alertmanager / Zabbix /        │
│ Grafana / 日志告警 / K8s Events            │
└──────────┬─────────────────────────────────┘
           ↓
┌────────── 收敛层（必备）─────────────────────┐
│ 去重 / 抑制 / 聚类 / 关联（不做这步就废）   │
└──────────┬─────────────────────────────────┘
           ↓
┌────────── 上下文增强 ──────────────────────┐
│ 当前指标 + 日志 + Trace + 变更 + 拓扑 +    │
│ Runbook + 历史相似故障                    │
└──────────┬─────────────────────────────────┘
           ↓
┌────────── LLM Agent ───────────────────────┐
│ 系统提示词 + 上下文 + 工具                 │
│ Function Calling / Tool Use                │
│ RAG 检索（向量库）                         │
└──────────┬─────────────────────────────────┘
           ↓
┌────────── 输出 ────────────────────────────┐
│ 1. 自然语言摘要                            │
│ 2. 影响范围 / 严重度                       │
│ 3. 根因猜测（Top 3 + 置信度）              │
│ 4. 处置建议（Runbook 链接）                │
│ 5. 自动执行结果（如果允许）                │
└──────────┬─────────────────────────────────┘
           ↓
┌────────── 通知 ────────────────────────────┐
│ 企业微信 / 钉钉 / 飞书 / 短信 / 电话       │
└────────────────────────────────────────────┘
```

## 四、最小可用版本（MVP）

```python
# 100 行实现 LLM 告警，立即可用
from openai import OpenAI
import json, requests

client = OpenAI(base_url="http://vllm-server:8000/v1", api_key="EMPTY")

SYSTEM = """你是资深 SRE。收到一条监控告警 + 上下文，请：
1. 用一句话概括故障
2. 评估严重度（P0/P1/P2/P3）
3. 给出 Top 3 可能原因（带置信度）
4. 给出立即可执行的处置步骤
5. 如果无法判断，明确说"信息不足"
输出 JSON 格式。"""

def enrich(alert):
    """拉取上下文"""
    return {
        "alert": alert,
        "metrics_5min": query_prometheus(alert['labels']),
        "recent_logs": query_loki(alert['labels'], minutes=5),
        "recent_traces": query_tempo(alert['labels'], minutes=5),
        "recent_changes": query_changelog(alert['labels'], hours=24),
        "topology": query_topology(alert['labels']),
        "runbook": rag_search(alert['annotations'].get('description'))
    }

def llm_summarize(alert):
    ctx = enrich(alert)
    rsp = client.chat.completions.create(
        model="Qwen2.5-32B-Instruct",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(ctx, ensure_ascii=False)}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    return json.loads(rsp.choices[0].message.content)

# Alertmanager webhook
@app.post("/webhook")
def webhook(req):
    for alert in req['alerts']:
        result = llm_summarize(alert)
        send_to_wechat(format_card(result))
```

## 五、提示词工程（核心中的核心）

### 5.1 系统提示词模板

```
你是一名拥有 10 年经验的 SRE 工程师，负责生产环境告警分析。

【背景】
- 我们是一家 [行业] 公司
- 关键业务: [业务列表]
- 主要技术栈: K8s + 微服务 + MySQL + Redis + Kafka
- SLO: 99.95% 可用性

【告警分级标准】
- P0: 全站不可用 / 数据损坏
- P1: 核心功能受损 / 大面积影响
- P2: 部分功能降级 / 性能下降
- P3: 监控异常 / 容量预警

【你的任务】
基于提供的告警信息和上下文，输出 JSON：
{
  "summary": "一句话概括（≤ 50 字）",
  "severity": "P0/P1/P2/P3",
  "impact_scope": "影响范围描述",
  "root_causes": [
    {"cause": "...", "confidence": 0.8, "evidence": "..."},
    {"cause": "...", "confidence": 0.5, "evidence": "..."}
  ],
  "actions": [
    {"step": "...", "command": "kubectl ...", "risk": "low"},
    ...
  ],
  "need_escalate": false,
  "similar_incidents": ["INC-1234", "INC-1235"]
}

【输出原则】
1. 简洁优先：值班工程师 30 秒内能读完
2. 证据驱动：每个判断要引用上下文中的数据
3. 谨慎升级：除非有明确证据，不要随便建议重启
4. 知道你不知道：信息不足时直接说"信息不足"
```

### 5.2 上下文拼接策略

```python
def build_context(alert):
    ctx = []
    
    # 1. 告警本身（必有）
    ctx.append(f"# 告警\n{alert.summary}\n实例: {alert.instance}\n标签: {alert.labels}")
    
    # 2. 关联指标（最近 30 分钟）
    metrics = query_related_metrics(alert)
    ctx.append(f"# 相关指标趋势\n{format_metrics_ascii(metrics)}")
    
    # 3. 日志（错误 + 紧邻告警）
    logs = query_recent_errors(alert, minutes=5, limit=20)
    ctx.append(f"# 最近错误日志\n{logs}")
    
    # 4. Trace（慢请求）
    traces = query_slow_traces(alert, minutes=5, limit=5)
    ctx.append(f"# 慢调用链\n{traces}")
    
    # 5. 变更（24h 内）
    changes = query_changes(alert.service, hours=24)
    ctx.append(f"# 最近变更\n{changes}")
    
    # 6. 历史相似（RAG）
    similar = vector_search(alert.summary, top_k=3)
    ctx.append(f"# 历史相似故障\n{similar}")
    
    # 7. Runbook
    runbook = rag_get_runbook(alert.alertname)
    ctx.append(f"# Runbook\n{runbook}")
    
    return "\n\n".join(ctx)
```

### 5.3 输出格式约束

```python
# 方法 1: response_format=json_object（OpenAI/vLLM 支持）
response_format={"type": "json_object"}

# 方法 2: JSON Schema（更严格）
response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "alert_analysis",
        "schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "severity": {"enum": ["P0","P1","P2","P3"]},
                "root_causes": {"type": "array", "items": {...}}
            },
            "required": ["summary","severity","root_causes"]
        }
    }
}

# 方法 3: Guided Decoding（vLLM/SGLang 原生）
# guided_json=schema 强制约束输出
```

## 六、RAG 知识库建设

### 6.1 知识来源

| 来源 | 内容 | 更新频率 |
|:---|:---|:---|
| **Runbook** | 标准处置手册 | 月级 |
| **历史 Incident** | 已解决故障记录 | 实时（每次故障后）|
| **Wiki / Confluence** | 系统设计 / 架构文档 | 周级 |
| **变更工单** | 上线记录 | 实时 |
| **拓扑/CMDB** | 服务依赖关系 | 日级 |
| **聊天记录** | 复盘群对话 | 月级（脱敏）|

### 6.2 文档切分与索引

```python
# 推荐方案：LangChain + ChromaDB / Milvus / pgvector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n## ", "\n### ", "\n\n", "\n", "。", " "]
)

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-zh-v1.5"   # 中文首选
)

vectorstore = Chroma.from_documents(
    documents=splitter.split_documents(runbooks),
    embedding=embeddings,
    persist_directory="./vectorstore"
)

# 检索
def rag_search(query, top_k=5):
    return vectorstore.similarity_search(query, k=top_k)
```

### 6.3 中文 Embedding 选型

| 模型 | 维度 | 中文得分 | 推荐 |
|:---|:---:|:---:|:---:|
| **bge-large-zh-v1.5** | 1024 | ⭐⭐⭐⭐⭐ | **首选** |
| **bge-m3** | 1024 | ⭐⭐⭐⭐⭐ | 多语言+长文档 |
| **m3e-large** | 1024 | ⭐⭐⭐⭐ | 老牌 |
| **conan-embedding** | 1792 | ⭐⭐⭐⭐⭐ | 2024 新 |
| **stella-base-zh-v3** | 1024 | ⭐⭐⭐⭐ | 国产 |
| OpenAI text-embedding-3 | 3072 | ⭐⭐⭐ | 英文好 |

### 6.4 重排（Rerank）

```python
# 向量召回 50 条 → BGE-Reranker 精排 5 条
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-large")

def retrieve_with_rerank(query, top_k=5):
    candidates = vectorstore.similarity_search(query, k=50)
    pairs = [[query, c.page_content] for c in candidates]
    scores = reranker.predict(pairs)
    sorted_idx = scores.argsort()[::-1][:top_k]
    return [candidates[i] for i in sorted_idx]
```

**经验**：向量召回 + Rerank 精度提升 30%+，必装。

## 七、Function Calling / Tool Use（取证 Agent）

### 7.1 给 LLM 装"手"

```python
tools = [
  {
    "type": "function",
    "function": {
      "name": "query_prometheus",
      "description": "查询 Prometheus 指标",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "PromQL"},
          "start": {"type": "string"},
          "end": {"type": "string"}
        }
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "kubectl_describe",
      "description": "查看 K8s 资源详情",
      "parameters": {...}
    }
  },
  {
    "type": "function",
    "function": {
      "name": "query_logs",
      "description": "查询 Loki/ES 日志",
      "parameters": {...}
    }
  },
  {
    "type": "function",
    "function": {
      "name": "query_mysql_slow",
      "description": "查询 MySQL 慢日志",
      "parameters": {...}
    }
  },
]

# LLM 自主调用
rsp = client.chat.completions.create(
    model="qwen2.5-32b",
    messages=[...],
    tools=tools,
    tool_choice="auto"
)

# 处理工具调用循环
while rsp.choices[0].finish_reason == "tool_calls":
    for call in rsp.choices[0].message.tool_calls:
        result = dispatch_tool(call.function.name, call.function.arguments)
        messages.append({"role": "tool", "content": result, "tool_call_id": call.id})
    rsp = client.chat.completions.create(model="qwen2.5-32b", messages=messages, tools=tools)
```

### 7.2 工具白名单 + 风险分级

| 风险 | 操作 | 是否需审批 |
|:---:|:---|:---:|
| 🟢 Read-only | kubectl get/describe、PromQL 查询、日志查询 | ❌ |
| 🟡 Mid-risk | rollout restart、scale up | ⚠️ Slack 确认 |
| 🔴 High-risk | delete、apply、SQL 改写 | ❌ 禁止（仅建议）|

```python
TOOL_RISK = {
    "kubectl_get": "low",
    "kubectl_describe": "low",
    "query_prometheus": "low",
    "kubectl_restart": "mid",
    "kubectl_scale": "mid",
    "kubectl_delete": "high",  # 直接拒绝
}

def dispatch_tool(name, args):
    if TOOL_RISK[name] == "high":
        return "拒绝执行：高危操作需人工"
    if TOOL_RISK[name] == "mid":
        if not request_human_approval(name, args):
            return "用户未授权"
    return TOOLS[name](**args)
```

## 八、模型选型（2025）

### 8.1 主流模型对比

| 模型 | 参数 | 推理速度 | 中文 | 工具调用 | 私有化 | 推荐场景 |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **DeepSeek-V3** | 671B MoE | 中 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 私有化首选 |
| **Qwen3-32B/72B** | 32B/72B | 快 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | **强推** |
| **Qwen2.5-32B** | 32B | 快 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 性价比 |
| **GLM-4-9B/32B** | 9B/32B | 极快 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | 中等规模 |
| **DeepSeek-R1** | 671B 推理 | 慢 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | 复杂根因分析 |
| **Llama-3.3-70B** | 70B | 中 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 英文场景 |
| **GPT-4o / 4.1** | — | 中 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | 不可联网用 |
| **Claude 3.5 Sonnet** | — | 中 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | 公司外不用 |

### 8.2 推荐栈

```
中小团队（私有化）:
  推理:  vLLM 部署 Qwen3-32B
  Embed: BGE-large-zh / bge-m3
  Rerank: bge-reranker-large
  向量库: Milvus / pgvector
  框架:  LangChain / LlamaIndex / Dify

大型团队:
  推理:  vLLM/SGLang 集群 + Qwen3-72B + DeepSeek-V3
  路由:  简单告警 → 32B，复杂根因 → 72B/R1
  Embed: 多模型集成
  向量库: Milvus / Vespa
  框架:  自研 Agent 编排
```

### 8.3 何时上推理模型（R1/o1）

```
✅ 上 R1/推理模型:
  - 复杂多维根因分析
  - 历史故障对比推演
  - 容量/演练计划生成

❌ 不要上:
  - 单条告警摘要（普通模型够用）
  - 实时高频调用（贵+慢）
  - 简单分类任务
```

## 九、告警收敛（必须做在 LLM 之前）

### 9.1 三段式收敛

```
1. 去重 (Dedup)
   - 相同 fingerprint 在 5 分钟窗口内合并
   - alertmanager 自带

2. 抑制 (Inhibit)
   - 父告警触发时压制子告警
   - 例: 节点宕机 → 该节点所有 Pod 告警压制

3. 聚类 (Cluster)
   - 同时间窗口 + 同业务/同服务 → 一组
   - 算法: DBSCAN / 时间窗口 + 标签匹配
```

### 9.2 聚类实现

```python
from sklearn.cluster import DBSCAN
import numpy as np

def cluster_alerts(alerts, time_window=300):
    # 特征：时间戳 + 标签编码
    features = np.array([
        [a.timestamp.timestamp(),
         hash(a.service),
         hash(a.severity),
         hash(a.region)]
        for a in alerts
    ])
    # 归一化时间
    features[:,0] = (features[:,0] - features[:,0].min()) / time_window
    
    clusters = DBSCAN(eps=0.5, min_samples=2).fit_predict(features)
    return clusters
```

### 9.3 关联（Correlation）

```
基于拓扑:
  CMDB 中的服务依赖 → 上游异常时下游告警自动归并

基于因果:
  Granger Causality 检测指标因果链
  PCMCI 算法挖掘根因

基于历史:
  相似事件向量化 → 同模式归并
```

## 十、告警内容降噪与质量度量

### 10.1 LLM 告警质量评分

```python
metrics = {
    "actionability": "可执行性（能直接照做？）",   # 1-5
    "accuracy": "根因准确度",                  # 1-5
    "brevity": "简洁度（30s 能读完？）",         # 1-5
    "completeness": "信息完整（影响范围？）",     # 1-5
    "false_positive_rate": "误报率",            # %
}

# 周报跟踪 + 持续优化提示词
```

### 10.2 人工反馈闭环

```python
# 在通知卡片里加 👍 / 👎 按钮
# 反馈写回 → 微调数据 / RAG 增强

@app.post("/feedback")
def feedback(alert_id, rating, comment):
    save_feedback(alert_id, rating, comment)
    if rating == "👎":
        # 加入"反例库"，下次类似情况优先 RAG
        add_to_negative_examples(alert_id, comment)
```

### 10.3 离线评估

```python
# 准备金标准数据集（历史故障 + 专家答案）
gold_dataset = [
    {"alert": ..., "expected_severity": "P1", "expected_cause": "..."}
]

# LLM 跑一遍 → 对比
for case in gold_dataset:
    result = llm_summarize(case['alert'])
    score = evaluate(result, case)

# 关键指标:
#   - 严重度准确率
#   - 根因 Top-1/Top-3 命中率
#   - 摘要 ROUGE/BLEU（参考但不绝对）
```

## 十一、流式输出与延迟优化

```python
# 流式输出：值班看到第一行 < 1s
rsp = client.chat.completions.create(..., stream=True)
for chunk in rsp:
    content = chunk.choices[0].delta.content
    if content:
        send_to_wechat_stream(content)

# 优化点:
#   1. KV Cache 复用（同上下文重复查询）
#   2. Prefill 切片（大上下文分块）
#   3. 推理参数: max_tokens=512, temperature=0.1
#   4. 模型路由: 简单告警走 7B，复杂走 32B
#   5. 推理批处理（vLLM 自动）
```

## 十二、常见坑（生产血泪）

| 坑 | 建议 |
|:---|:---|
| **直接喂原始告警风暴** | 必先收敛去重抑制 |
| **上下文太长 token 爆** | 截断 + 摘要 + 重要信号优先 |
| **JSON 格式不稳定** | guided_json / response_format 强约束 |
| **幻觉乱推荐命令** | 工具白名单 + 风险分级 |
| **RAG 召回不准** | bge-reranker 必加 |
| **响应慢（10s+）** | 流式输出 + 路由小模型 |
| **告警和处置脱节** | 处置步骤要可点击直接执行 |
| **变更未关联** | 必拉 24h 变更记录 |
| **拓扑未关联** | CMDB / 服务图谱必接 |
| **没有人工反馈** | 反馈闭环是改进核心 |
| **盲目用 GPT-4** | 私有化大模型 + 本地推理省钱 |
| **prompt 写死** | 模板化 + 版本管理 |
| **告警语言不一致** | 风格统一（"已发现"vs"疑似"） |
| **打扰频率过高** | 分级通知（P0 电话/P3 邮件） |
| **无演练机制** | 故障注入 + 离线评估 |

## 十三、开源项目 / 商业产品

### 13.1 开源

| 项目 | 用途 |
|:---|:---|
| **Dify** | LLMOps 平台（国产，开箱即用） |
| **LangChain / LangGraph** | LLM 编排框架 |
| **LlamaIndex** | RAG 框架 |
| **AutoGen** | Microsoft 多 Agent |
| **MetaGPT** | 中国多 Agent |
| **Robusta** | K8s 告警 + LLM |
| **PagerDuty AIOps** | 商业 |
| **OpsBeacon** | LLM Ops 助手 |
| **HolmesGPT** | K8s LLM 根因分析 |

### 13.2 商业 / 闭源

| 产品 | 厂商 | 特点 |
|:---|:---|:---|
| **Datadog Bits AI** | Datadog | 全栈 AI |
| **New Relic AI** | New Relic | 摘要 + RCA |
| **Dynatrace Davis** | Dynatrace | 因果 + LLM |
| **Splunk AI** | Splunk | SOAR + LLM |
| **PagerDuty Copilot** | PagerDuty | 告警 + 处置 |
| **阿里 ARMS / 应用观测** | 阿里云 | 国内主流 |
| **腾讯云 APM AIOps** | 腾讯云 | 国内 |
| **观测云** | 观测云 | 国产 |

## 十四、完整代码示例（生产骨架）

```python
import os, json
from fastapi import FastAPI, Request
from openai import OpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Milvus
from prometheus_api_client import PrometheusConnect

app = FastAPI()
llm = OpenAI(base_url=os.getenv("LLM_URL"), api_key="EMPTY")
embed = HuggingFaceEmbeddings(model_name="BAAI/bge-large-zh-v1.5")
vs = Milvus(embed, connection_args={"uri": os.getenv("MILVUS_URL")})
prom = PrometheusConnect(url=os.getenv("PROM_URL"))

SYSTEM = open("prompts/sre.txt").read()

TOOLS = [...]  # 见第七节

@app.post("/alertmanager-webhook")
async def webhook(req: Request):
    data = await req.json()
    for alert in collapse_alerts(data['alerts']):     # 收敛
        ctx = build_context(alert)                     # 增强
        result = analyze(alert, ctx)                   # LLM
        send_notification(result)                      # 通知
        log_for_feedback(alert, result)                # 闭环
    return {"status": "ok"}

def collapse_alerts(alerts):
    # 去重 + 抑制 + 聚类
    ...

def build_context(alert):
    ctx = {"alert": alert}
    ctx["metrics"] = prom.custom_query(f"...{alert['labels']['service']}...")
    ctx["logs"] = query_loki(alert)
    ctx["traces"] = query_tempo(alert)
    ctx["changes"] = query_changelog(alert)
    ctx["similar"] = vs.similarity_search(alert['annotations']['summary'], k=3)
    ctx["runbook"] = get_runbook(alert['labels']['alertname'])
    return ctx

def analyze(alert, ctx):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": json.dumps(ctx, ensure_ascii=False)}
    ]
    while True:
        rsp = llm.chat.completions.create(
            model="Qwen3-32B-Instruct",
            messages=messages,
            tools=TOOLS,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        msg = rsp.choices[0].message
        messages.append(msg)
        if msg.tool_calls:
            for call in msg.tool_calls:
                result = dispatch_tool(call.function.name, json.loads(call.function.arguments))
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
        else:
            return json.loads(msg.content)

def send_notification(result):
    card = format_wechat_card(result)
    requests.post(WECHAT_WEBHOOK, json=card)
```

## 十五、ROI 数据（参考行业披露）

```
落地一年常见效果（参考 Google SRE / 字节 / 阿里）:
  ✅ 告警量减少 60-80%
  ✅ MTTR 缩短 30-50%
  ✅ 值班负担减少 50%
  ✅ 新人上手时间从月 → 周
  ✅ 跨团队沟通效率 +40%

成本（百节点规模）:
  - 推理服务（Qwen3-32B × 2 实例 × A100）: 8 万/年
  - 向量库 + Embedding: 2 万/年
  - 开发投入: 1-2 人月起步
  - ROI: 通常 3-6 个月回本（按节省值班 + 减少事故）
```

## 十六、学习路径

```
第 1 周（最小可用）:
  1. 装 vLLM + Qwen3-7B
  2. 写最小提示词
  3. Alertmanager webhook 接入
  4. 输出到企业微信

第 1 个月（生产可用）:
  5. 加 RAG（Runbook + 历史故障）
  6. 加告警收敛
  7. 加 Function Calling 取证
  8. 加用户反馈

第 3 个月（智能化）:
  9. 离线评估 + 提示词版本管理
  10. 多模型路由（小模型/大模型）
  11. Agent 化（多步推理）
  12. 自动化执行（低风险）

第半年+（进阶）:
  13. 多 Agent 协作（SRE/DBA/网络）
  14. 因果分析 + 故障预测
  15. 自训练故障摘要模型（LoRA）
  16. 自研平台化
```

## 十七、参考资料

```
论文:
  - "An Empirical Investigation of Practical Log Anomaly Detection"
  - "LM-PACE: Production AIOps with LLMs" (Google, 2024)
  - "OpsGPT: A Domain-Specific LLM for IT Operations"
  - "ReAct: Synergizing Reasoning and Acting in LLMs"

博客:
  - Google SRE Workbook（Site Reliability Engineering）
  - Netflix Tech Blog AIOps 系列
  - 字节跳动 SRE 公众号
  - 阿里云原生 AIOps 系列

开源:
  - Dify: https://github.com/langgenius/dify
  - HolmesGPT: https://github.com/robusta-dev/holmesgpt
  - LangChain: https://github.com/langchain-ai/langchain
  - bge-large-zh: https://huggingface.co/BAAI/bge-large-zh-v1.5
  - Qwen: https://github.com/QwenLM/Qwen
```

> 📖 **核心判断**：LLM 告警是 AIOps **最容易落地、ROI 最高的方向**。第一阶段（1 周）就能跑起来，第三阶段（3 个月）能见到明显业务价值。**最容易翻车的不是模型选错，而是没做告警收敛、没建 RAG 知识库、工具调用没有风险分级**。私有化首推 **vLLM + Qwen3-32B + bge-large-zh-v1.5 + Milvus**，这是 2025 中文 AIOps 的黄金组合。
