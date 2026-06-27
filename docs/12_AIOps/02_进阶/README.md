# 进阶

> AIOps 进阶 = **VictoriaMetrics/Mimir/Thanos 大规模时序 + ClickHouse 日志栈 + eBPF 可观测性(Pixie/Coroot/Parca) + 异常检测生产化(动态阈值+Prophet/LSTM/ARIMA) + 多源关联告警(KEDA/告警关联引擎) + Root Cause Analysis 服务化 + 容量预测自动化 + LLM 告警摘要+SOP 推荐 + RAG 知识库 + Webhook 自愈 + Service Map + SLO/Error Budget + Sentry/RUM 接入**。本章面向独立维护可观测平台 + AIOps 试点的工程师。

## 一、大规模 Prometheus（VictoriaMetrics）

```
痛点:
  Prometheus 单机 (>1k targets / >1M series) 内存爆

方案:
  1. Federation (老, 不推荐)
  2. Thanos (Sidecar + Store Gateway + Compactor) ⭐
  3. VictoriaMetrics ⭐⭐ (国产 + 性能 + 简单)
  4. Mimir (Grafana 商业开源)
  5. Cortex (Prometheus 衍生)

VictoriaMetrics 优势:
  - 10x 性能 / 50% 存储 (vs Prom)
  - 集群 (vmstorage + vmselect + vminsert)
  - PromQL 兼容 + MetricsQL 扩展
  - 国产社区活跃 ⭐
```

### 1.1 VictoriaMetrics 集群

```yaml
# Helm
helm install vm vm/victoria-metrics-cluster \
  --set vmstorage.replicaCount=3 \
  --set vmstorage.retentionPeriod=180d \
  --set vmselect.replicaCount=2 \
  --set vminsert.replicaCount=2 \
  --set vmstorage.persistentVolume.size=1Ti
```

### 1.2 Thanos 架构

```
Prometheus + Sidecar → S3
                   ↓
              Store Gateway ← Query (多 Prom 聚合)
                   ↓
              Compactor (压缩 + 降采样)
                   ↓
              Ruler (Recording Rules)
```

## 二、日志大规模（ClickHouse）

```
痛点:
  - Loki 大量日志 → 慢
  - Elasticsearch 贵 + 重

方案:
  ClickHouse + Vector / Fluent Bit
  腾讯 / 字节 / 美团 数十 TB/day 日志栈

架构:
  app → Vector → Kafka → ClickHouse (HDFS / S3)
  Grafana / Superset 查询
  Plausible / 自研 UI

Schema:
CREATE TABLE logs (
  ts DateTime64(3),
  level LowCardinality(String),
  service LowCardinality(String),
  pod String,
  trace_id String,
  message String,
  fields Map(String, String)
) ENGINE = MergeTree
PARTITION BY toYYYYMMDD(ts)
ORDER BY (service, ts, level)
TTL ts + INTERVAL 30 DAY;
```

## 三、eBPF 可观测性

```
工具:
  Pixie ⭐ (CNCF)        实时观测无 instrument
  Coroot ⭐              零侵入 K8s 拓扑
  Parca / Pyroscope      持续 profiling
  Cilium Hubble          网络观测
  Tetragon              安全 + 运行时
  Beyla (Grafana)        Auto-instrument

特点:
  - 零代码侵入
  - 内核级
  - 性能开销小 (< 1%)
  - K8s 友好

部署 (Pixie):
helm install pixie pixie-operator/pixie-operator-chart \
  -n px-operator --create-namespace
```

## 四、异常检测生产化

### 4.1 动态阈值 (Prophet)

```python
# 实时检测 service
from prophet import Prophet
import pandas as pd
import prometheus_api_client as p

# 拉取 30d 数据
prom = p.PrometheusConnect(url="http://prom:9090")
df = prom.custom_query_range(
    query='sum(rate(http_requests_total{service="api"}[5m]))',
    start_time=parse_datetime("30d"),
    end_time=parse_datetime("now"),
    step="60s"
)
df = ... # 转 ds/y
m = Prophet(interval_width=0.99, daily_seasonality=True, weekly_seasonality=True)
m.fit(df)

future = m.make_future_dataframe(periods=1, freq='1min')
forecast = m.predict(future)
yhat_lower = forecast["yhat_lower"].iloc[-1]
yhat_upper = forecast["yhat_upper"].iloc[-1]

# 当前值
current = prom.custom_query('sum(rate(http_requests_total{service="api"}[1m]))')
if current < yhat_lower or current > yhat_upper:
    alert("Anomaly!")
```

### 4.2 LSTM / Transformer

```python
# Darts (时序库) ⭐
from darts import TimeSeries
from darts.models import RNNModel
series = TimeSeries.from_dataframe(df, 'ds', 'y')
model = RNNModel(model='LSTM', input_chunk_length=24, output_chunk_length=1)
model.fit(series)
pred = model.predict(n=1)
```

### 4.3 工具

```
Prophet ⭐                简单 + 周期
Darts                    多模型
PyOD                     传统 ML 异常
Anomaly Detector (Azure) 商业
Hawkular / OpenNMS 等
滴滴 IOPS Star + 蚂蚁 ChatOps + 阿里 MetisFI
```

## 五、告警关联引擎

```
解决告警风暴:
  1. 时间窗聚合 (5min 内同 service 合并)
  2. 拓扑关联 (Service Topology 上下游)
  3. Label 关联 (相同 namespace / cluster)
  4. 模板降噪 (相似告警合并)
  5. LLM 总结 (生成 incident 概览)

工具:
  Alertmanager group_by ⭐ (基础)
  Karma (告警 dashboard)
  Squadcast / Opsgenie / PagerDuty (商业)
  自研 + Kafka + LLM

Alertmanager:
route:
  group_by: [alertname, service]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
inhibit_rules:
  - source_match: { severity: critical }
    target_match: { severity: warning }
    equal: [service]
```

## 六、Root Cause Analysis

### 6.1 拓扑驱动

```
Service Map (Tempo / SkyWalking / Coroot):
  api → user-service → db
  
异常出现时:
  1. 找最末端异常服务 (leaf)
  2. 看依赖 (上下游)
  3. 时序对齐 (异常时间窗)
  4. 错误率 / 延迟 / 资源 三视角

工具:
  Coroot ⭐ (eBPF + 自动 RCA)
  Pixie (实时观测)
  Sentry + 链路
  SkyWalking
```

### 6.2 LLM + RAG RCA

```python
# 检索历史故障 + LLM 推理
import langchain
from langchain.vectorstores import Milvus
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chat_models import ChatOpenAI

embed = HuggingFaceEmbeddings(model_name="BAAI/bge-large-zh-v1.5")
vstore = Milvus(embedding_function=embed, ...)

# 历史故障入库 (postmortem)
docs = [...]
vstore.add_documents(docs)

# 当前告警 RCA
alert = "api P99 latency 5s, 2025-12-25 14:00"
context = vstore.similarity_search(alert, k=5)
prompt = f"告警: {alert}\n类似历史故障: {context}\n请分析可能根因, 给出排查步骤"

llm = ChatOpenAI(base_url="http://vllm:8000/v1", model="Qwen2.5-72B")
print(llm.invoke(prompt))
```

## 七、容量预测自动化

```yaml
# Argo Workflow 每天预测 + 告警
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
spec:
  schedule: "0 2 * * *"
  workflowSpec:
    entrypoint: predict
    templates:
      - name: predict
        container:
          image: aiops/forecast:v1
          command: ["python"]
          args: ["forecast.py", "--metric", "disk", "--days", "30"]
```

```python
# forecast.py
import pandas as pd
from prophet import Prophet
import prometheus_api_client as p
import requests

prom = p.PrometheusConnect(url="http://prom:9090")
df = prom.custom_query_range(...)
m = Prophet().fit(df)
fc = m.predict(m.make_future_dataframe(periods=30, freq='D'))
if fc["yhat"].iloc[-1] > 0.9 * capacity:
    requests.post(webhook, json={"msg": "Disk will full in 30d"})
```

## 八、LLM 智能告警摘要

```python
# Alertmanager Webhook → LLM 摘要
from fastapi import FastAPI, Request
from langchain.chat_models import ChatOpenAI

app = FastAPI()
llm = ChatOpenAI(base_url="http://vllm:8000/v1", model="qwen-72b")

@app.post("/webhook")
async def webhook(req: Request):
    alerts = (await req.json())["alerts"]
    text = "\n".join([f"{a['labels']['alertname']}: {a['annotations'].get('summary')}" for a in alerts])
    summary = llm.invoke(f"以下告警发生在 5 分钟内, 总结根因并给出 3 条排查步骤:\n{text}")
    # 发送钉钉 / 飞书
    return summary
```

## 九、Webhook 自愈

```yaml
# Alertmanager → 自愈
receivers:
  - name: autoremediate
    webhook_configs:
      - url: http://autoremediate:8080/heal
        send_resolved: true
```

```python
# autoremediate 服务
@app.post("/heal")
def heal(alerts):
    for a in alerts["alerts"]:
        if a["labels"]["alertname"] == "PodOOM":
            # 重启 + 加内存请求
            subprocess.run(["kubectl", "rollout", "restart", "deploy/", a["labels"]["deployment"]])
            # 通知人工
```

## 十、Service Map

```
工具:
  Coroot ⭐ (eBPF)
  Pixie (eBPF)
  Tempo Service Map
  SkyWalking
  Apache HertzBeat (国产)
  Kiali (Istio)
  
价值:
  - 自动发现服务依赖
  - 实时调用图
  - 异常下钻
  - 根因辅助
```

## 十一、SLO + Error Budget

```yaml
# Sloth ⭐ (PromOps SLO)
service: api
slos:
  - name: latency
    objective: 99
    sli:
      events:
        error_query: rate(http_request_duration_seconds_bucket{le="0.5"}[5m])
        total_query: rate(http_request_duration_seconds_count[5m])

# 自动生成:
  - SLI Recording Rule
  - SLO 烧损率告警 (1h / 6h / 24h / 3d)
  - Grafana Dashboard
```

```
工具:
  Sloth ⭐ (PromOps)
  Pyrra (类似)
  Nobl9 (商业)
  Google SRE Book (理论)
```

## 十二、Sentry + RUM

```
错误聚合 (前端 / 后端):
  Sentry ⭐ (开源 + 商业)
  Bugsnag / Rollbar

前端用户监控 (RUM):
  Sentry Performance
  阿里 ARMS RUM
  Datadog RUM

集成:
  - 前端 SDK (JS/iOS/Android)
  - 自动捕获错误 + 性能
  - 用户行为回放 (Session Replay)
```

## 十三、Checklist（进阶）

```
监控:
☐ VictoriaMetrics / Thanos / Mimir 一种
☐ 多集群 + 长期存储 (S3 / OSS)
☐ Recording Rules (常用聚合)

日志:
☐ Loki 或 ClickHouse (TB+)
☐ Vector / Fluent Bit 采集
☐ 关联 trace_id

链路:
☐ Tempo + OpenTelemetry SDK
☐ Service Map (Tempo / Coroot)
☐ 异常 trace 告警

eBPF:
☐ Pixie / Coroot 一种
☐ Parca / Pyroscope 持续 profiling

异常检测:
☐ Prophet / LSTM 生产化
☐ 动态阈值取代静态
☐ 多周期 (日 / 周 / 节假日)

告警关联:
☐ Alertmanager group_by + inhibit
☐ 时间窗合并
☐ LLM 摘要 (大模型 webhook)

RCA:
☐ 拓扑 + 时序对齐
☐ LLM + RAG 历史故障
☐ Coroot 自动 RCA

容量:
☐ Prophet 自动预测
☐ Argo Workflow 调度
☐ predict_linear 即时
☐ 7d / 30d / 90d 三级

自愈:
☐ Alertmanager webhook 自愈
☐ 简单场景 (重启 / 扩容)
☐ 复杂场景 人工

SLO:
☐ Sloth / Pyrra
☐ 业务核心 SLO 量化
☐ Error Budget 烧损率告警

RUM:
☐ Sentry / 阿里 ARMS
☐ 前端 + 后端
```

## 十四、推荐栈（进阶）

```
监控:        VictoriaMetrics ⭐ (国产) + Grafana
日志:        Loki (小) / ClickHouse (大) + Vector / Fluent Bit
链路:        Tempo + OpenTelemetry
eBPF:        Pixie / Coroot ⭐ + Pyroscope
异常:        Prophet + Darts + PyOD
告警:        Alertmanager + 国产钉钉/飞书 + Karma
RCA:        Coroot + LLM (Qwen + RAG)
容量:        Prophet + Argo Workflow
SLO:        Sloth ⭐ + Pyrra
RUM:        Sentry / 阿里 ARMS RUM
LLM:        Qwen-72B / DeepSeek-V3 + LangChain
平台:        夜莺 ⭐ / 观测云 / 阿里 ARMS
```

> 📖 **核心判断**：AIOps 进阶 = **VictoriaMetrics 大规模指标 + ClickHouse/Loki 日志栈 + Tempo+OTel 链路 + eBPF(Pixie/Coroot) + Prophet/LSTM 动态阈值 + 告警关联 + LLM RCA + Argo 容量预测 + Webhook 自愈 + Sloth SLO + Sentry RUM**。能跑通"K8s + VictoriaMetrics + Loki + Tempo + Coroot + Sloth + LLM Webhook 告警摘要 + 历史故障 RAG RCA"完整可观测+AIOps 平台，就具备 AIOps 工程师能力。
