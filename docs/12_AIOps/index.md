# 12. AIOps

> AIOps = 可观测性 + AI/LLM 智能运维。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦 Prometheus/VictoriaMetrics + Loki/ClickHouse + Tempo/Coroot + OpenTelemetry + eBPF(Pixie/DeepFlow) + Prophet/Darts 异常检测 + LangGraph Agent + MCP 协议 + Chaos Mesh + Sloth SLO + 国产化(夜莺/Qwen) 11 大主线。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入门 AIOps | 可观测性三大支柱 + Prometheus + Grafana + Loki + Tempo + OpenTelemetry + 异常检测(Prophet) + 日志分析(Drain) + RCA + 容量预测 + 20 题 |
| [02_进阶](02_进阶/README.md) | 独立维护可观测平台 | VictoriaMetrics/Thanos + ClickHouse 日志 + eBPF(Pixie/Coroot) + Prophet 动态阈值 + 告警关联 + LLM 摘要 + Webhook 自愈 + Sloth SLO + Sentry RUM |
| [03_高级](03_高级/README.md) | AIOps 平台架构师 | AIOps 平台架构 + 大规模异常检测(Autoencoder/Transformer) + 因果推理 RCA + 故障预测 + ChatOps + LangGraph Agent + MCP 协议 + Chaos + GitOps + 多云 + 国产化 + MLOps for AIOps |
| [04_最佳实践](04_最佳实践/README.md) | 平台负责人 | 可观测基线 + 告警工程化(SLO+分级+降噪+on-call) + 异常检测落地 + RCA SOP + ChatOps 4 阶段路径 + 自愈守门 + Chaos 演练 + 团队组织 + 国产化路径 + Incident SOP + Postmortem + KPI + 闭环 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | OTel 一统 + eBPF 默认 + VM/CH 大规模 + Foundation Model for TS + LLM RCA + LangGraph+MCP + Agent 自愈 + SLO 驱动 + 国产(夜莺/DeepFlow/Qwen) + 20 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
  └─ 01_基础: Prom + Grafana + Loki + Tempo + OTel + Prophet + 20 题

进阶（3-12 月）
  └─ 02_进阶: VM + CH + eBPF + 动态阈值 + 告警关联 + LLM 摘要 + Sloth SLO + RUM

高级（1-2 年）
  └─ 03_高级: 平台架构 + 深度学习异常检测 + LLM RCA + LangGraph + MCP + Chaos + 多云 + 国产

工程化（2-3 年）
  └─ 04_最佳实践: 基线 + 告警 + 异常落地 + RCA SOP + ChatOps 4 阶段 + 自愈守门 + 演练 + 团队 + Postmortem + KPI

展望（持续）
  └─ 99_发展与展望: OTel + eBPF + Foundation Model + Agent + Sovereign 可观测
```

## 核心判断

```
心法:
  1. Prom + Grafana 是基础, 但要早转 VictoriaMetrics
  2. Loki (小) / ClickHouse (大) 选一种, 不要 ELK 重栈
  3. OpenTelemetry 是统一未来 (SDK + Collector)
  4. eBPF (Coroot/Pixie/DeepFlow) 是 K8s 可观测默认 (2026+)
  5. Prophet 起步 + Darts/USAD 升级 (异常检测)
  6. SLO 驱动告警 (Sloth) 代替静态阈值, 砍噪音
  7. LLM 告警摘要 + RAG RCA 是当下最易落地的 AIOps
  8. LangGraph + MCP 是 ChatOps Agent 主流栈
  9. Chaos Mesh 季度演练是必修 (国产 CNCF)
  10. 国产: 夜莺 + DeepFlow + Qwen + Ascend (央企必)
  11. on-call 工程化 (轮值 + 升级 + 静默 + KPI)
  12. Postmortem Blameless + Action Item + 知识库

红线:
  ❌ 还在用静态阈值告警 (噪音 + 漏报)
  ❌ Prometheus 单机 (扩展性 + 长期存储)
  ❌ 无 trace_id 关联 logs/metrics
  ❌ 无 SLO 量化业务
  ❌ on-call 无升级 / 无静默 / 无 KPI
  ❌ 无 Postmortem / 无 Action Item 跟踪
  ❌ AIOps 不接 LLM (落后了)
  ❌ 国产 (夜莺 / DeepFlow / Qwen) 不学 (政企会淘汰)
  ❌ 自愈无 RBAC / 无审计 (合规风险)
  ❌ 无 Chaos 演练 (灾备不靠谱)
```

## 相关章节

- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 kube-prometheus + Volcano + Cilium 可观测
- 配合 [08_DevOps](../08_DevOps/index.md) 看 GitOps + Argo Workflow + Backstage
- 配合 [09_中间件](../09_中间件/index.md) 看 ClickHouse 日志 + Kafka 事件
- 配合 [10_大数据](../10_大数据/index.md) 看 Iceberg/Paimon 训练数据 + Feast 特征
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 vLLM 推理 + LangGraph + bge + Milvus
- 配合 [13_认证与SSO](../13_认证与SSO/index.md) 看 Keycloak + 平台 RBAC
- 配合 [14_安全](../14_安全/index.md) 看 SIEM + Audit + 国密 + 等保
- 配合 [15_渗透测试](../15_渗透测试/index.md) 看 红蓝对抗 + Chaos
- 配合 [16_故障排查](../16_故障排查/index.md) 看 RCA SOP + Postmortem
