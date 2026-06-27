# 基础

> AIOps 基础 = **可观测性三大支柱(Metrics/Logs/Traces) + Prometheus + Grafana + Loki + Tempo + OpenTelemetry + 告警 + 异常检测入门 + 日志分析入门 + Root Cause Analysis 入门 + 容量预测入门**。本章面向运维工程师入门 AIOps。

## 一、AIOps 全景

```
传统运维 (Manual / Scripted)
  ↓
监控告警 (Prometheus / Zabbix)
  ↓
可观测性 (Metrics + Logs + Traces)
  ↓
AIOps:
  - 异常检测 (Anomaly Detection)
  - 根因分析 (Root Cause Analysis)
  - 告警降噪 / 关联
  - 容量预测 / 资源优化
  - 故障预测 / 自愈
  - LLM 智能问答 / 决策辅助
  - Agent 自动化运维 ⭐
```

## 二、可观测性三大支柱

```
Metrics (指标):
  - 数值时序 (CPU/Memory/QPS)
  - Prometheus / VictoriaMetrics ⭐
  - 用途: 仪表板 + 告警

Logs (日志):
  - 文本 (App/Audit/System)
  - Loki ⭐ / Elasticsearch / ClickHouse
  - 用途: 排错 + 审计

Traces (链路):
  - 分布式调用链 (microservice)
  - Tempo ⭐ / Jaeger / SkyWalking
  - 用途: 性能 + 依赖分析

新增:
  Profiles (持续性能剖析): Pyroscope ⭐
  Events (业务事件)
  RUM (前端用户监控): Sentry / 阿里 ARMS
```

## 三、Prometheus 基础

### 3.1 部署

```yaml
# kube-prometheus-stack (Helm)
helm install kube-prom prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.resources.requests.memory=4Gi
```

```
组件:
  Prometheus Operator
  Prometheus Server
  Alertmanager
  Grafana
  Node Exporter
  kube-state-metrics
```

### 3.2 PromQL 必会

```
# 当前 CPU 利用率 (节点)
100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 5 分钟错误率
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 延迟
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))

# 内存预测 (4h 后是否超 90%)
predict_linear(node_memory_MemAvailable_bytes[1h], 4*3600) < 0

# 同环比
(metric - metric offset 1d) / metric offset 1d
```

### 3.3 告警规则

```yaml
groups:
  - name: node
    rules:
      - alert: HighCPU
        expr: 100 - (avg by(instance)(irate(node_cpu_seconds_total{mode="idle"}[5m]))*100) > 90
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "{{ $labels.instance }} CPU > 90%"
      
      - alert: PodCrashLoop
        expr: rate(kube_pod_container_status_restarts_total[5m]) > 0
        for: 10m
        labels: { severity: page }
```

## 四、Grafana 基础

```
数据源:
  - Prometheus ⭐
  - Loki (日志)
  - Tempo (链路)
  - PostgreSQL / MySQL
  - Elasticsearch
  - InfluxDB

Dashboard:
  - JSON 导入 (官方 + grafana.com)
  - 变量 (Variable, $namespace)
  - 模板复用
  - 告警 + Annotation

国产替代:
  阿里云 Grafana
  夜莺 (Nightingale, 国产) ⭐
  观测云 Guance
```

## 五、Loki + 日志

```yaml
# Loki + Promtail (Helm)
helm install loki grafana/loki-stack \
  -n monitoring \
  --set grafana.enabled=true \
  --set promtail.enabled=true

# LogQL 查询
{namespace="api", pod=~"web-.*"} |= "error" | json | line_format "{{.msg}}"

# 错误率
sum(rate({namespace="api"} |~ "ERROR" [5m]))

# 关联 trace
{namespace="api"} | json | trace_id="abc123"
```

```
对比:
  Loki         便宜, 标签索引 (Grafana 推荐)
  Elasticsearch 全文索引 (重 + 贵)
  ClickHouse    SQL 日志查询 (国内大厂主流)
  阿里 SLS     云日志服务
```

## 六、Tempo + 链路追踪

```yaml
# OpenTelemetry Collector
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
spec:
  config: |
    receivers:
      otlp: { protocols: { grpc: {}, http: {} } }
    processors:
      batch: {}
    exporters:
      otlp: { endpoint: tempo:4317, tls: { insecure: true } }
    service:
      pipelines:
        traces: { receivers: [otlp], processors: [batch], exporters: [otlp] }
```

```
应用接入 (Go 示例):
import "go.opentelemetry.io/otel"
otel.Tracer("svc").Start(ctx, "operation")
```

## 七、OpenTelemetry

```
统一标准 (Metrics + Logs + Traces):
  - SDK (Go/Java/Python/JS)
  - Collector (转发 + 处理)
  - 兼容 Prometheus / Loki / Tempo / Jaeger

主流后端:
  Grafana + Tempo + Loki
  Datadog (商业)
  New Relic / Splunk
  
国产:
  阿里云 ARMS / SLS / Prometheus
  腾讯 APM
  华为 AOM
  观测云 Guance
```

## 八、传统告警瓶颈

```
痛点:
  ☐ 告警风暴 (single 故障引发 100+ 告警)
  ☐ 告警重复 (相同问题告警多次)
  ☐ 告警漂移 (阈值跟不上业务)
  ☐ 关联性差 (人脑 root cause)
  ☐ on-call 疲劳

AIOps 解法 (5 大场景):
  1. 异常检测 (动态阈值)
  2. 告警降噪 / 关联
  3. 根因分析
  4. 容量预测
  5. LLM Agent (智能 SOP)
```

## 九、异常检测入门

```
方法:
  1. 统计 (3-sigma / IQR / Z-score)
  2. 时序预测 (Prophet / ARIMA / Holt-Winters)
  3. ML (Isolation Forest / One-class SVM)
  4. 深度学习 (LSTM / Autoencoder / Transformer)
  5. 业务规则 + 同环比

工具:
  - Prophet (Facebook) ⭐
  - statsmodels (Python)
  - PyOD (异常检测库)
  - Prometheus + predict_linear / holt_winters
  - 滴滴 IOPS Star (国产)
  - 阿里 MetisFI / 蚂蚁 ChatOps

示例 (Prophet):
```python
from prophet import Prophet
import pandas as pd

df = pd.read_csv("metrics.csv")   # ds, y
m = Prophet(interval_width=0.95, daily_seasonality=True)
m.fit(df)
future = m.make_future_dataframe(periods=24, freq='H')
forecast = m.predict(future)
# yhat_lower / yhat_upper 即动态阈值
```
```

## 十、日志分析入门

```
模式发现:
  - LogReduce (Splunk)
  - Drain (Tsinghua 开源) ⭐
  - LogCluster
  
异常检测:
  - 日志频率突变
  - 日志类型 entropy 升
  - 错误关键词聚合
  - LLM 总结 + 分类

实战 (Drain):
pip install logparser
python -c "
from logparser.Drain import LogParser
parser = LogParser(log_format='<Date> <Time> <Pid> <Level> <Content>', ...)
parser.parse('app.log')
"
```

## 十一、Root Cause Analysis 入门

```
方法:
  1. 拓扑 (Service Topology + 关联)
  2. 时序对齐 (告警时间 + 指标变化)
  3. 调用链 (Trace + Span error)
  4. 历史 (相同故障历史)
  5. LLM + Agent (大模型推理)

工具:
  PromQL (异常时间窗 + 拓扑下钻)
  Jaeger / Tempo Trace 分析
  Pixie (eBPF 实时)
  Sentry (异常聚合)
  阿里 Goldeneye / 蚂蚁 ChatOps
```

## 十二、容量预测入门

```
方法:
  - 线性回归 (Prometheus predict_linear)
  - Prophet (周期性 + 节假日)
  - ARIMA / SARIMA
  - LSTM (深度学习)

场景:
  - 磁盘 (容量 + 增长率) → "10 天后满" 预测
  - CPU / 内存 (QPS × 单请求开销)
  - GPU 显存 (业务模型容量)
  - 数据库连接 / 慢 SQL 趋势

PromQL:
predict_linear(node_filesystem_avail_bytes[1d], 7*86400) < 0
# 7 天后磁盘是否会满
```

## 十三、必会工具清单

```
监控:        Prometheus + Grafana + Alertmanager ⭐
日志:        Loki ⭐ / Elasticsearch / ClickHouse
链路:        Tempo / Jaeger ⭐ / SkyWalking
统一:        OpenTelemetry ⭐
Profile:    Pyroscope / Parca
RUM:        Sentry / 阿里 ARMS
异常检测:   Prophet + PyOD + statsmodels
日志解析:   Drain / LogCluster
工作流:     Airflow / Argo Workflows
通知:        Alertmanager + PagerDuty / Opsgenie + 钉钉 + 飞书
平台:        夜莺 (国产) ⭐ / 阿里 ARMS / 观测云 Guance
LLM:        Qwen / DeepSeek + LangChain
```

## 十四、入门 20 题

```
1.  可观测性三大支柱
2.  Metrics / Logs / Traces 区别
3.  Prometheus 数据模型 (label + sample)
4.  PromQL rate / increase / irate 区别
5.  predict_linear 用法
6.  histogram vs summary
7.  Recording Rule vs Alerting Rule
8.  Alertmanager 路由 + silence
9.  Loki vs Elasticsearch
10. OpenTelemetry 架构
11. Tempo Trace 是什么
12. 异常检测 3-sigma 原理
13. Prophet 模型组件 (trend + seasonality + holiday)
14. Isolation Forest 原理
15. predict_linear 容量预测
16. 告警风暴 / 告警关联 解决
17. Root Cause Analysis 流程
18. Drain 日志解析原理
19. AIOps 5 大场景
20. LLM 在 AIOps 角色 (问答 + 总结 + Agent)
```

## 十五、推荐栈

```
监控:        kube-prometheus-stack ⭐
日志:        Loki + Promtail / Fluent Bit
链路:        Tempo + OpenTelemetry
Profile:    Pyroscope
告警:        Alertmanager + Webhook + 钉钉/飞书/PagerDuty
仪表板:     Grafana ⭐
异常检测:   Prophet + PyOD
LLM:        Qwen / DeepSeek + LangChain
平台:        夜莺 (国产) ⭐ / 阿里 ARMS / 观测云
```

> 📖 **核心判断**：AIOps 基础 = **Prometheus + Grafana + Loki + Tempo + OpenTelemetry 可观测性 + 异常检测(Prophet/PyOD) + 日志分析(Drain) + RCA + 容量预测 + LLM 智能问答**。能跑通"kube-prometheus + Loki + Tempo + Alertmanager + Prophet 动态阈值 + LLM 告警摘要"全链路，就具备 AIOps 入门能力。
