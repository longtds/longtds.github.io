# 最佳实践

> 故障排查最佳实践 = **方法论 + Runbook + On-call + 告警治理 + SLO + Postmortem 文化 + Chaos GameDay + Observability 三大件 + IR SOP + LLM SRE + AI 工作负载 + 信创+异地多活 + KPI + 团队 + Runbook 库**。本章把"会查 K8s"升级到"运营企业级 SRE 平台"。

## 一、12 项金标准

```
1. ✅ 监控可观测三大件 (Metrics + Logs + Traces) + Profile + eBPF
2. ✅ Runbook 每告警必须有 (链接告警 → 一键开)
3. ✅ On-call 制度 (主备 + Follow-the-Sun) + PagerDuty 等
4. ✅ 告警治理: 严重度分级 + 静默 + 抑制 + 聚合
5. ✅ SLO + Error Budget + Burn Rate 告警
6. ✅ Blameless Postmortem (P0/P1 必开 + Action 闭环 > 80%)
7. ✅ Chaos GameDay 季度演练 (RTO/RPO 验证)
8. ✅ IR SOP (PICERL) + 演练 + 通讯模板
9. ✅ DR (Disaster Recovery) 异地容灾 + 季度切换
10. ✅ Capacity Planning + 压测 + Headroom 50%
11. ✅ DB Schema 兼容 + 灰度 + 一键回滚
12. ✅ AI/GPU/LLM 工作负载专项 SRE
```

## 二、可观测性三大件

```
Metrics:
  Prometheus / VictoriaMetrics ⭐
  Thanos / Cortex / Mimir (长期)
  Grafana 可视化
  Recording Rules + Alerting Rules
  
Logs:
  Loki ⭐ (cost-effective)
  Elastic / OpenSearch (老)
  ClickHouse + Vector (新)
  阿里 SLS / 腾讯 CLS

Traces:
  OpenTelemetry ⭐ (统一标准)
  Tempo / Jaeger / SkyWalking
  Service Map 自动
  
关联:
  Exemplar (Metrics ↔ Trace)
  TraceID 注入 Logs
  Grafana 一键跳转

Profile (第四件):
  Parca / Pyroscope
  Continuous Profiling

eBPF (第五件):
  Pixie / Coroot / Hubble
  零代码采集
```

## 三、Runbook 库

```
模板:
## 告警名: ServiceHighErrorRate

### 触发条件
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05

### 影响
用户请求 5xx > 5%, 业务量 -10%

### 快速诊断 (5 分钟)
1. 看 Grafana Dashboard X (链接)
2. 看 Trace P99 (链接 Tempo)
3. 看上游/下游依赖 (Service Map Pixie)
4. 看最近发布: kubectl rollout history deployment/api

### 处置步骤
1. 如果是最近发布触发 → kubectl rollout undo
2. 如果是 DB → 看慢查询 / 连接池
3. 如果是上游 → 切换备用接口 / 降级
4. 如果是限流 → 临时调整阈值

### 联系人
- 主 on-call: oncall-api
- 业务方: PM-X
- 升级: Director

### Postmortem
- 是否触发 P1 复盘: 5xx > 10% 或 > 30min

Runbook 工具:
  Notion / Confluence / Obsidian
  Grafana annotation 链接
  PagerDuty Response Plays
  Runbooks.app
```

## 四、On-call 制度

```
模式:
  Primary + Secondary
  Follow-the-Sun (跨时区 - 国际)
  
轮值:
  周轮 (一周一换)
  班次 (工作时间 + 夜间)
  
工具:
  PagerDuty ⭐
  Opsgenie
  Splunk On-Call (VictorOps)
  FireHydrant
  Squadcast
  阿里云 ARMS 告警
  飞书/钉钉 + 自研

KPI:
  ACK 时间 < 5 min (Tier 1)
  Resolution P1 < 4h
  误报率 < 10%
  On-call 工作量 < 25% 时间
  Follow-up 完成率 > 80%

文化:
  - On-call 是责任 + 学习机会
  - 补休 (倒班补偿)
  - 工具友好 (手机 alert + 自动派)
  - 不惩罚 (无指责文化)
```

## 五、告警治理

```
分级:
  P0  严重 (用户面 down)        立即 phone call + IR
  P1  影响 (重要功能 / SLO 违反)  5min ack
  P2  警告 (即将影响)            工作时间
  P3  信息 (趋势 / 容量)         批量 review

去噪 (核心问题):
  - 阈值合理 (基于历史 + 业务)
  - 静默 (维护窗口)
  - 抑制 (上游告警 → 下游)
  - 聚合 (同类合并)
  - 时间窗 (持续 N 分钟才告)
  - 抖动过滤
  - For 子句 (Prometheus)
  - Burn Rate (SLO based)

工具:
  AlertManager (Prometheus)
  Karma (UI)
  PagerDuty AIOps (聚类)
  阿里 ARMS 告警

度量:
  误报率 < 10%
  夜间 P2/P3 = 0
  on-call 单周告警 < 30
```

## 六、SLO + Error Budget

```
SLO:
  P99 latency < 200ms (Tier 1)
  Availability > 99.95%
  
Error Budget:
  100% - 99.95% = 0.05% = 22 min / 月
  超支 → 冻结发布 (强制)
  剩余 70% → 灰度 + 压测加快

Burn Rate alerts ⭐:
  Fast burn (1h consume 5%): → P1
  Slow burn (6h consume 10%): → P2
  
工具:
  Sloth (Prometheus → SLO rules)
  Pyrra / Slok
  Nobl9 (商业)
  自建 + Grafana

实践:
  - Tier 1: 99.95% + Burn Rate
  - Tier 2: 99.9%
  - Tier 3: 99%
  - 季度 Review
  - 跨部门 (Product + SRE) 共识
```

## 七、Postmortem SOP 与频次标准

> Postmortem 的文化内核（Blameless 原则、跨团队共享、训练 Junior、年度 Top 复盘）
> 见 [16_故障排查/03_高级 → 四、Postmortem 文化](../03_高级/README.md)。
> 本节仅定义**触发标准、SOP 时限、模板与跟踪 KPI**，不重复文化论述。

触发标准:
  ☐ P0 (用户面 down / 数据泄露)       → 强制 Postmortem
  ☐ P1 (重要功能不可用 / SLO 违反)     → 强制 Postmortem
  ☐ P2 (单功能降级, 持续 > 30min)      → 建议 Postmortem
  ☐ 重复故障 (同根因季度内 ≥ 2 次)     → 强制升级复盘

SOP 时限:
  T+0     事故恢复 → 创建 Postmortem 文档
  T+24h   初稿完成 (时间线 + 影响 + 初步根因)
  T+48h   复盘会议 (IC 主持 + 业务 + SRE + 相关方)
  T+7d    Action Items 录入 Jira (P0/P1 + Owner + Deadline)
  T+30d   P0/P1 Action 闭环
  T+90d   季度复盘 (闭环率统计 + 重复故障核查)

模板 (标准 7 段, 详见 01_基础 第八章 Postmortem 模板):
  1. 摘要 (1 段)
  2. 影响 (用户 / 业务 / 时长 / 严重级)
  3. 时间线 (分钟级)
  4. 根因 (5 Whys + 修复)
  5. 检测 + 响应 + 修复 评估 (MTTD/MTTA/MTTR)
  6. Action Items (P0/P1/P2 + Owner + Deadline)
  7. Lessons Learned

跟踪 KPI:
  ☐ P0/P1 Postmortem 完成率 100% (48h 内)
  ☐ Action 闭环率 > 80% (季度)
  ☐ 重复故障 = 0 (季度, 红线)
  ☐ Lessons Learned 知识库入库率 100%

工具:
  Notion / Confluence / Obsidian (文档)
  FireHydrant ⭐ / Jeli / Rootly (IR + Postmortem 一体)
  PagerDuty Postmortem / Pulse Effect

## 八、Chaos GameDay

```
频次:
  季度 1 次 (各团队)
  年度 1 次 (全公司)
  
范围:
  Pod kill / Node drain / Network partition / CPU/MEM 注入
  AZ failover / Region failover (大型)
  DB master kill
  K8s upgrade 模拟
  DNS / Certificate / Vault 故障

工具:
  Chaos Mesh ⭐ (CNCF)
  ChaosBlade ⭐ (阿里)
  Litmus
  Gremlin (商业)
  自研

实践:
  T-1w: 通知 + 准备
  T-0:  执行 + 观察 + 响应
  T+1d: Postmortem
  T+7d: Action 闭环

KPI:
  RTO 实际 vs 目标
  RPO 实际 vs 目标
  发现问题数
  Action 闭环率

红线:
  ☐ 必通知 + 演练分组
  ☐ 控制爆炸半径
  ☐ 紧急停止机制
  ☐ 真实流量 vs 影子环境
```

## 九、IR (Incident Response) SOP

```
PICERL:
  Preparation     工具 + SOP + 演练
  Identification  发现 + 分级
  Containment     隔离 / 限流 / 降级
  Eradication     根因清理
  Recovery        恢复 + 验证
  Lessons Learned Postmortem

P0/P1 SOP:
  1. PagerDuty 触发
  2. 主 on-call ack < 5 min
  3. 召开 IC (Incident Commander) → 战时频道
  4. 拉通业务 + 客服 (对外通报)
  5. 分工 (诊断 + 修复 + 沟通)
  6. 实时更新 (每 15min)
  7. 恢复 + 验证
  8. Postmortem 24h 内

角色:
  IC (Incident Commander)
  OL (Operations Lead)
  CL (Communications Lead)
  SL (Subject Matter Lead)

工具:
  PagerDuty / FireHydrant / Rootly (IC + Timeline)
  Slack / 飞书 / 钉钉 (战时频道)
  Status Page (statuspage.io / Cachet 开源 / Atlassian)

对外通报:
  - 客户 (Status Page)
  - 内部 (邮件 / 群)
  - 监管 (关基 + 数据泄露 法定)
```

## 十、DR + 异地容灾

```
RTO (Recovery Time Objective):
  Tier 1: 15 min
  Tier 2: 1h
  Tier 3: 24h

RPO (Recovery Point Objective):
  Tier 1: < 1 min (同步复制)
  Tier 2: < 15 min (异步)
  Tier 3: < 24h (备份)

模式:
  双活 (Active-Active)        Tier 1
  主备 (Active-Standby + 热)  Tier 1/2
  冷备份                      Tier 3

技术:
  DB:    MySQL Group Replication / PG Patroni / TiDB / OceanBase
  Cache: Redis Sentinel + AOF
  MQ:    Kafka Mirror / RocketMQ DLedger
  Object: S3 跨 Region 复制 / OSS CRR
  K8s:   Karmada / Argo CD 多集群
  DNS:   GSLB / Anycast

演练:
  季度小切换 (业务低峰)
  年度大切换 (Region 级)
  无演练 = 无能力

工具:
  Velero (K8s 备份)
  Restic
  阿里云 HBR / 腾讯云 COS
```

## 十一、Capacity Planning

```
方法:
  1. 业务预测 (PM / 数据团队)
  2. 压测 (k6/wrk) → 单机 QPS
  3. 集群规划 → 留 50% buffer
  4. 趋势监控 → 季度 Review

压测:
  - 单接口 (基线)
  - 全链路 (生产容量)
  - 异地 (多 Region 协调)
  - 故障演练 (单集群挂)

工具:
  k6 ⭐ (现代)
  wrk / wrk2
  locust (Python)
  jmeter (老)
  ghz (gRPC)

监控趋势:
  Grafana 90d 历史
  增长率 → 提前扩容
  峰值预测 (双 11 / 618 / 春运)
```

## 十二、DB Schema + 灰度

```
Schema 兼容原则:
  ☐ 只加列, 不删列
  ☐ 加列必 nullable / default
  ☐ 删列 → 先 deprecated (3+ 版本)
  ☐ 改类型 → 双写迁移
  ☐ 重命名 → 加新列 + 双写 + 切流 + 删旧
  
工具:
  pt-online-schema-change (MySQL)
  gh-ost (GitHub)
  Liquibase / Flyway (版本化)
  Bytebase ⭐ (GUI + 审批)

灰度:
  Argo Rollouts (Canary)
  Istio VirtualService weight
  Feature Flag (LaunchDarkly / GrowthBook)

回滚:
  kubectl rollout undo
  Argo Rollouts abort
  Helm rollback
  DB 不可回滚 → 兼容是 唯一防御

红线:
  ☐ DB Schema 灰度发布
  ☐ 不可逆变更必 review (2 人 + DBA)
  ☐ 关键变更 maintenance window
  ☐ 一次一变量 (不要混并)
```

## 十三、AI/GPU/LLM SRE

```
监控:
  DCGM ⭐ + Prometheus
  nvtop / nvitop
  vLLM metrics (推理)
  PyTorch profiler (训练)
  W&B / MLflow

故障:
  - GPU 故障 (ECC / Xid / Health)
  - NCCL hang (训练) → 网卡 + 拓扑
  - 显存 OOM
  - 推理 QPS 抖动
  - 训练 NaN/Inf

工具:
  GPU Operator (NVIDIA)
  DCGM Exporter
  Volcano (Batch 调度)
  Kueue (Job Queue)
  Pixie GPU profiler

KPI:
  GPU 利用率 > 60%
  训练 MFU > 50%
  推理 tokens/s + P99
  GPU MTBF (无故障时长)
  ECC 故障率 < 0.5%/月
```

## 十四、信创 + 异地多活

```
信创:
  鲲鹏 + openEuler + 麒麟 + 通信
  TiDB / OceanBase / PolarDB / GaussDB
  RocketMQ / KafkaOnPulsar
  Tongsuo + 国密 + 等保 3 + 关基

异地多活:
  单元化 (LDC / OCTO / 自研)
  GSLB + Anycast
  数据中心 3+ (北/上/广)
  RTO < 5 min / RPO < 1 min

演练:
  ☐ 季度小切换 (一个单元)
  ☐ 半年大切换 (Region)
  ☐ 年度全切换 (战时)
  ☐ HW 重保期: 暂停演练 + 战时模式
```

## 十五、KPI + 度量

```
可观测:
☐ Metrics + Logs + Traces + Profile + eBPF 100% 覆盖
☐ Runbook 覆盖告警率 100%

On-call:
☐ ACK < 5 min (P0/P1)
☐ MTTR P0 < 30 min
☐ MTTR P1 < 4h
☐ 误报率 < 10%
☐ on-call 工作量 < 25% 时间
☐ 夜间 P2/P3 = 0

SLO:
☐ Tier 1 99.95% / P99 200ms
☐ Error Budget 监控 + 冻结
☐ Burn Rate alert 配置

Postmortem:
☐ P0/P1 100% 必开
☐ 24-48h 内完成
☐ Action 闭环 > 80%
☐ 重复故障 = 0 (季度)

Chaos:
☐ 季度 GameDay
☐ RTO/RPO 验证
☐ 改进项闭环

DR:
☐ Tier 1 异地多活
☐ 季度切换演练
☐ 年度 Region 演练

Capacity:
☐ 季度压测
☐ Headroom > 50%
☐ 节假日预测 + 扩容

变更:
☐ DB Schema 兼容
☐ 灰度 100%
☐ 一键回滚 100%

AI/GPU:
☐ DCGM 全覆盖
☐ GPU 利用 > 60%
☐ 推理 SLO 配置
```

## 十六、团队组织

```
SRE 团队 (中型 1000 人公司, 10-20 人):
  Tier 1 业务 SRE (3-5)
  平台 SRE (3-5)
  Observability + Tooling (2-3)
  Chaos + DR (1-2)
  On-call 协调 (1)

大型互联网 (100+ 人):
  按业务线 SRE
  + 平台 SRE
  + 可观测平台
  + Chaos Engineering
  + 调度 + 性能
  + 故障分析专家

岗位:
  L1: 工程师
  L2: 高级 (3-5y)
  L3: 资深 (5-8y)
  L4: 专家 (8+y)
  L5: 首席 / Staff
  
核心能力 (L3+):
  - K8s + 中间件 + 应用全栈
  - 编程 (Go/Python + IaC)
  - 监控平台 (Prom / Loki)
  - eBPF 基础
  - SLO + Postmortem 文化
  - On-call 经验
```

## 十七、推荐栈（最佳实践）

```
Metrics:    Prometheus + VictoriaMetrics ⭐ + Grafana + 夜莺 (国产)
Logs:       Loki ⭐ + ClickHouse + 阿里 SLS
Traces:     OpenTelemetry + Tempo ⭐ + SkyWalking (国产)
Profile:    Parca + Pyroscope ⭐
eBPF:       Pixie ⭐ + Coroot + Cilium Hubble
告警:        AlertManager + Karma + PagerDuty ⭐ + 飞书/钉钉
On-call:    PagerDuty ⭐ / Opsgenie / FireHydrant
Runbook:    Notion / Confluence + Grafana 跳转
SLO:        Sloth ⭐ + Burn Rate
Chaos:      Chaos Mesh ⭐ + ChaosBlade ⭐
DR:         Velero (K8s 备份) + 异地多活 + GSLB
IR:         FireHydrant ⭐ / Rootly / PagerDuty
Status Page: statuspage.io / Cachet (开源)
Capacity:   k6 ⭐ + Grafana 趋势
变更:        Argo Rollouts ⭐ + Bytebase + Liquibase
GPU/LLM:    DCGM + GPU Operator + Pixie + vLLM metrics
信创:        夜莺 + 国产 APM + 国产 SOC
团队:        SRE 10-20 (1000 人公司) / 100+ (10K 人)
KPI:         MTTD/MTTR/SLO/Burn Rate/Action 闭环率
```

> 📖 **核心判断**：故障排查最佳实践 = **12 项金标 + 五位一体可观测(Metrics+Logs+Traces+Profile+eBPF) + Runbook 覆盖 + On-call PagerDuty + 告警治理(降噪+Burn Rate) + SLO+Error Budget + Blameless Postmortem + 季度 Chaos GameDay + IR PICERL SOP + DR 异地多活 + Capacity 压测 + DB Schema 兼容+灰度+回滚 + AI/GPU SRE + 信创+多活 + 团队 10-20 人 + KPI(MTTR/SLO/闭环率)**。能给央企/大型互联网搭"VictoriaMetrics + Loki + Tempo + Pixie + PagerDuty + Chaos Mesh + Argo Rollouts + Karmada + 夜莺 + DCGM"完整 SRE 平台, 落地 On-call + Runbook + Postmortem + GameDay + DR + LLM SRE 全流程, 就具备 SRE 团队负责人/平台架构师能力。
