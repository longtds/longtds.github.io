# LLM 告警

## 智能告警架构

```
告警触发
  │
  ▼
告警上下文采集器
  ├─ 当前指标快照（前后15min）
  ├─ 关联 Pod/Node 状态
  ├─ 最近日志
  ├─ 最近变更记录
  └─ 历史同类告警匹配
  │
  ▼
LLM 分析引擎（HolmesGPT）
  ├─ 根因推断
  ├─ 影响范围评估
  ├─ 严重等级（P0-P3）
  ├─ 修复建议
  └─ 经验匹配
  │
  ▼
行动决策
  ├─ 自动修复（已知模式）
  ├─ 人工确认（发送诊断报告）
  └─ 自动降噪（只记录不打扰）
```

## HolmesGPT

HolmesGPT 是 CNCF Sandbox 项目，开源的 AI 告警诊断 Agent。

```bash
# 部署 HolmesGPT
helm repo add robusta https://robusta-charts.storage.googleapis.com
helm install holmesgpt robusta/holmesgpt \
  --set openai.apiKey=<key> \
  --set sinks.prometheus.url=http://prometheus:9090
```

## 告警前后对比

```
传统告警：
  [P0] GPU 利用率 98% > 阈值 90%

LLM 告警：
  [P0 智能诊断] GPU 利用率突增 98%
  根因：decoded Pod 显存碎片化导致 batch size 下降
  影响：TPOT 上升 40%，P99 延迟 5.2s
  建议：重启 Pod（3min 恢复）
  关联：过去 2h 已有 3 次同类抖动
```
