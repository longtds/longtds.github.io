# 可观测性

## Prometheus + VictoriaMetrics

```bash
# Prometheus Stack 部署
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus prometheus-community/kube-prometheus-stack

# VictoriaMetrics 长期存储
helm install victoria-metrics vm/victoria-metrics \
  --set server.retentionPeriod=90d
```

## 核心告警规则

```yaml
# PrometheusRule 示例
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: k8s-rules
spec:
  groups:
  - name: k8s.rules
    rules:
    - alert: PodCrashLooping
      expr: increase(kube_pod_container_status_restarts_total[5m]) > 0
      for: 1m
      labels:
        severity: warning
      annotations:
        summary: "Pod {{ $labels.pod }} is crash looping"
    - alert: NodeMemoryPressure
      expr: kube_node_status_condition{condition="MemoryPressure",status="true"} == 1
      labels:
        severity: critical
```

## OpenObserve（统一可观测性）

OpenObserve 将日志、指标和链路追踪统一在一个平台中，存储成本比 ELK 低 140 倍。

```bash
# 部署
docker run -d --name openobserve -p 5080:5080 \
  -e ZO_DATA_DIR="/data" \
  -v /data/openobserve:/data \
  public.ecr.aws/zinclabs/openobserve:latest
```

## Grafana 面板

Grafana 是可视化面板之王，可对接 Prometheus/OpenObserve/Loki 等多数据源。
