# 16. 故障排查

> 故障排查 / SRE = 实战兜底，覆盖方法论、Linux、K8s、中间件、应用、性能、AI 工作负载、Chaos、DR、Postmortem。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦 USE/RED/Golden Signals + Linux 五大子系统 + K8s 全栈 + Mesh + DB 深度 + JVM/Go/Python + eBPF + Pixie/Coroot + Chaos Mesh + SLO + LLM SRE Agent + GPU/LLM 排查 16 大主线，是全书的兜底章节。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入门 | USE/RED/Golden Signals + Linux 5 大子系统(CPU/MEM/DISK/NET/Process) + 日志 + 网络 + HTTP/MySQL/Redis 常见错 + Postmortem 入门 + 20 题 |
| [02_进阶](02_进阶/README.md) | 维护生产 K8s | K8s 全栈(Pod/SVC/Ingress/CNI/CSI/调度) + Service Mesh + 容器(crictl/cgroup) + DB 深度(MySQL/PG/Kafka/Redis/ES/Mongo) + JVM/Go/Python + perf/eBPF/火焰图 + Trace + 慢查询治理 + 灰度+回滚 |
| [03_高级](03_高级/README.md) | SRE 团队负责人 | 分布式定位 + Chaos Engineering(Chaos Mesh) + SLO 工程化(Sloth/Burn Rate) + Postmortem 文化 + Continuous Profiling + Pixie/Coroot + AIOps + LLM 辅助 + GPU/LLM SRE + 信创+多活 + 网络深度 + 内核 + 多集群 |
| [04_最佳实践](04_最佳实践/README.md) | 平台架构师 | 12 金标 + 可观测三大件+Profile+eBPF + Runbook + On-call(PagerDuty) + 告警治理 + SLO+Error Budget + Blameless Postmortem + Chaos GameDay + IR PICERL + DR 异地多活 + 团队 10-20 人 + KPI |
| [99_发展与展望](99_发展与展望.md) | 所有人 | LLM SRE Agent + MCP + AI 根因 + Continuous Profile 普及 + eBPF 第二春 + AIOps 自愈 + OTel 一统 + Karmada + AI/GPU/LLM SRE + 信创 + Sovereign + PQC + 20 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
  └─ 01_基础: USE/RED + Linux 5 大 + 日志 + 网络 + HTTP/SQL + Postmortem + 20 题

进阶（3-12 月）
  └─ 02_进阶: K8s 全栈 + Mesh + DB 深度 + JVM/Go/Python + perf/eBPF + Trace + 慢查询 + 灰度

高级（1-2 年）
  └─ 03_高级: Chaos + SLO + Continuous Profile + AIOps + LLM SRE + GPU/LLM + 多集群

工程化（2-3 年）
  └─ 04_最佳实践: 12 金标 + On-call + 告警治理 + GameDay + IR + DR + 团队 + KPI

展望（持续）
  └─ 99_发展与展望: LLM Agent + MCP + eBPF + AIOps 自愈 + Karmada + AI 工作负载
```

## 核心判断

```
心法:
  1. 方法论先行 (USE/RED/Golden Signals/MTTR)
  2. 可观测五大件 (Metrics + Logs + Traces + Profile + eBPF)
  3. Runbook 每告警必有 (一键跳转)
  4. On-call 制度化 (PagerDuty + 主备 + 轮值)
  5. 告警治理 (Burn Rate 替代静态阈值, 误报 < 10%)
  6. SLO + Error Budget 强制冻结发布
  7. Postmortem Blameless + Action 闭环 > 80%
  8. Chaos GameDay 季度 + DR 异地多活
  9. eBPF (Pixie/Coroot/Cilium) 零代码革命, 必修
  10. LLM SRE Agent 是未来 5 年最大机遇
  11. AI/GPU/LLM 工作负载是新蓝海 (DCGM + vLLM)
  12. 信创 + Sovereign 是央企硬需求

红线:
  ❌ 没有 Runbook 的告警 (= 噪音)
  ❌ 没有 SLO (= 无目标)
  ❌ Postmortem 互相指责 (= 文化崩)
  ❌ 没有 Chaos 演练 (= 不知韧性)
  ❌ DR 没切换演练 (= DR = 0)
  ❌ DB Schema 不兼容 (= 无法回滚)
  ❌ On-call 一人多次背锅 (= 团队问题)
  ❌ 不学 AI + eBPF (5 年淘汰)
  ❌ 信创 + 等保 不学 (央企无用)
  ❌ 救火型 SRE (无演练 + 无 Postmortem)
```

## 相关章节

- 配合 [02_Linux](../02_Linux/index.md) 看 系统排查基本功
- 配合 [03_网络](../03_网络/index.md) 看 网络深度
- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 K8s 全栈
- 配合 [08_DevOps](../08_DevOps/index.md) 看 SRE + DevOps + 灰度
- 配合 [09_中间件](../09_中间件/index.md) 看 DB / 缓存 / MQ 深度
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 GPU + vLLM + 训练
- 配合 [12_AIOps](../12_AIOps/index.md) 看 AIOps + LLM SRE Agent
- 配合 [14_安全](../14_安全/index.md) 看 SOC + EDR + IR
- 配合 [15_渗透测试](../15_渗透测试/index.md) 看 红蓝 + 取证 + Postmortem
