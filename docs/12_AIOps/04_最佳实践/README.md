# 最佳实践

> AIOps 最佳实践 = **可观测性基线(全栈采集+标签规范+长期存储) + 告警工程化(SLO+分级+降噪+on-call) + 异常检测落地(选模型+训练+部署+监控) + RCA SOP + ChatOps Agent 落地 + 自愈守门(RBAC+审批+审计) + Chaos 演练 + 数据治理 + 团队组织(SRE+Platform+DataOps) + 国产化路径 + Incident SOP + Postmortem + KPI 度量 + 持续学习闭环**。本章把"会用 AIOps 工具"升级到"运营企业级可观测+AIOps 平台"。

## 一、可观测性基线

### 1.1 全栈采集

```
必采:
☐ Metrics:
  - Node Exporter (节点)
  - kube-state-metrics (K8s 对象)
  - cAdvisor (容器)
  - 应用 /metrics (业务)
  - 中间件 exporter (MySQL/Redis/Kafka)
  - DCGM Exporter (GPU)
  - Blackbox Exporter (黑盒探测)

☐ Logs:
  - 容器日志 (Promtail / Vector)
  - 应用日志 (JSON 格式化)
  - 审计日志 (K8s + DB)
  - 业务日志 (业务事件)

☐ Traces:
  - OpenTelemetry SDK 接入业务
  - Service Mesh (Istio) 自动注入
  - Gateway / API Gateway 注入

☐ Events:
  - K8s Events (Kafka 持久)
  - 业务事件
  - CI/CD 事件

☐ Profile:
  - 关键服务 持续 profiling (Pyroscope)

☐ RUM:
  - 前端业务 (Sentry / 阿里 ARMS)

☐ Topology:
  - eBPF (Coroot / Pixie)
```

### 1.2 标签规范

```
强制标签:
  - cluster
  - namespace
  - service
  - team / owner
  - cost_center
  - env (prod/staging/dev)

业务:
  - business_unit
  - tier (P0/P1/P2)
  - slo_id

Trace 关联:
  - trace_id (logs / metrics 都带)
  - span_id

避免:
  ❌ 高基数标签 (uuid / user_id)
  ❌ 自由文本
  ❌ 数值标签
```

### 1.3 长期存储

```
存储分层:
  Hot (7d):     SSD, Prometheus / VM 本地
  Warm (30d):   VictoriaMetrics 集群
  Cold (1y+):   S3 / OSS (Thanos / VM remote)

成本:
  - 降采样 (5m / 1h 聚合)
  - 删除高基数无用标签
  - 业务标签清理

日志:
  Hot (7d):     ClickHouse 集群
  Warm (30d):   ClickHouse + 冷存储
  Cold (180d): S3 / 归档
```

## 二、告警工程化

### 2.1 告警分级

```
P0 (page):
  - 业务 down / 错误率 > 50%
  - on-call 立即响应 (< 5 min)
  - 钉钉/飞书 @ + 电话
  
P1 (high):
  - SLO 烧损率快 (1h 用 5% budget)
  - 错误率 1-50%
  - on-call 1h 内
  
P2 (medium):
  - SLO 烧损率慢 (24h 用 budget)
  - 容量预警 (7d 内满)
  - 工作时间响应

P3 (info):
  - 容量 (30d 预测)
  - 趋势异常
  - 邮件 / 群通知
```

### 2.2 SLO 驱动告警（推荐）

```
理念:
  不要 "CPU > 90%" 这种基础告警 (噪音)
  按 SLO 烧损率告警 (业务感知)

Sloth 配置:
service: api
slos:
  - name: availability
    objective: 99.9
    sli:
      events:
        error_query: rate(http_requests_total{status=~"5.."}[5m])
        total_query: rate(http_requests_total[5m])
    alerting:
      name: ApiAvailability
      page_alert:
        labels: { severity: page, slo: api-availability }

# 自动生成:
  - 烧损率 14.4x / 1h ratio  (5% budget in 1h) → page
  - 烧损率 6x / 6h ratio     (5% budget in 6h) → high
  - 烧损率 1x / 24h ratio    (10% budget in 1d) → ticket
```

### 2.3 on-call 工程

```
要素:
☐ 轮值 (PagerDuty / Opsgenie / 自研)
☐ 主备 + 升级链
☐ 通知渠道 (钉钉 + 电话 + 短信)
☐ 静默期 (维护窗口)
☐ Acknowledge / Resolve 流程
☐ MTTA / MTTR / MTBF 指标
☐ 反馈闭环 (alert review)
```

### 2.4 告警降噪

```
☐ Alertmanager group_by (合并)
☐ Alertmanager inhibit (压制)
☐ 时间窗聚合 (5min)
☐ Karma dashboard (集中视图)
☐ LLM 摘要 (合并 + 总结)
☐ 季度 alert review (砍 30%+ 无效)
```

## 三、异常检测落地

```
步骤:
☐ 1. 选业务 (高价值 / 高噪音)
☐ 2. 数据 (90d 历史 metrics)
☐ 3. 选模型 (单一: Prophet; 多: Darts/AnomalyTransformer)
☐ 4. 训练 (Argo + MLflow)
☐ 5. 评测 (业务集 + AUC)
☐ 6. 部署 (KServe + 灰度)
☐ 7. 监控 (准确率 + 漂移)
☐ 8. 反馈闭环 (标注 + 再训练)
☐ 9. 上线生产 (替代静态阈值)
☐ 10. 推广其他业务

KPI:
  覆盖率: AIOps 覆盖 > 30% 关键指标
  误报率: < 5%
  漏报率: < 1%
  MTTR 降幅: > 30%
```

## 四、RCA SOP

```
人工 SOP:
  1. 确认告警 (5min)
  2. 看影响面 (业务 / 用户)
  3. 看依赖 (Service Map)
  4. 时序对齐 (异常时间窗 + 部署 / 变更)
  5. 上下游下钻 (从异常 leaf 向上)
  6. Trace 看错误调用链
  7. Log 看错误堆栈
  8. 决策 (回滚 / 重启 / 扩容 / 修改)
  9. 验证恢复
  10. Postmortem

AIOps 辅助:
  1. LLM 总结告警 (摘要)
  2. RAG 历史故障 (类似 incident)
  3. Coroot 自动 RCA (拓扑)
  4. ChatOps (人工 + Agent 协同)
  5. 推荐 SOP (RAG 知识库)
  6. 自动执行 (低风险)
```

## 五、ChatOps Agent 落地

```
试点路径:
  Phase 1 (read-only, 1 月):
    - LLM 查询 Prometheus / Loki / Tempo
    - 自动告警摘要
    - 工程师 ChatOps 对话
  
  Phase 2 (assist, 2-3 月):
    - LLM 推荐 SOP
    - RCA 辅助 (拉证据 + 推理)
    - 写 Postmortem
  
  Phase 3 (auto, 3-6 月):
    - 低风险自愈 (重启 / 扩容)
    - RBAC + 审批 + 审计
  
  Phase 4 (agent, 6+ 月):
    - 复杂 LangGraph Agent
    - 跨工具协同 (MCP)
    - 持续学习

风险控制:
  - 风险分级 (read / write / destructive)
  - 写操作必经审批
  - 双人审批 (高风险)
  - 全程审计 → SIEM
  - 一键回滚
  - 人工 override
```

## 六、自愈守门

```
原则:
  Read-only:    无审批 自动
  Soft-write:   日志记录 自动
  Hard-write:   单人审批 (业务负责人)
  Destructive:  双人审批 (业务 + SRE Lead)
  
工具:
  Backstage Self-service + Approval
  Argo Workflow + 审批节点
  自研 + 钉钉/飞书审批
  Teleport (SSH 审计)

审计:
  - 所有操作记录
  - 操作员 + 时间 + 输入 + 输出
  - 审批链
  - 责任人
  - SIEM 180d
  - 季度审计
```

## 七、Chaos 演练基线

```
频次:
  ☐ 周 (开发环境)
  ☐ 月 (准生产)
  ☐ 季度 (生产, 维护窗口)

场景:
  ☐ 节点宕机 (1 / 多)
  ☐ Pod 杀
  ☐ 网络分区
  ☐ 网络延迟 / 丢包
  ☐ CPU / 内存 / 磁盘 满
  ☐ DNS 解析失败
  ☐ K8s API down
  ☐ etcd 主节点 down
  ☐ 中间件 down (MySQL / Redis)
  ☐ 跨 AZ 故障

度量:
  ☐ MTTD (Mean Time To Detect)
  ☐ MTTA (Mean Time To Acknowledge)
  ☐ MTTR (Mean Time To Recover)
  ☐ 告警覆盖率
  ☐ 自愈成功率
```

## 八、数据治理

```
监控数据:
☐ Metrics retention 策略
☐ 高基数 prune
☐ 降采样
☐ 标签规范强制

日志:
☐ JSON 格式化
☐ trace_id 关联
☐ PII 脱敏 (合规)
☐ TTL 自动归档

模型数据:
☐ 训练数据来源 + 版本
☐ MLflow 注册
☐ Feast 特征
☐ 标注质量

合规:
☐ 等保三级
☐ 日志 180d
☐ 审计完整
☐ PII 脱敏
☐ 国密
```

## 九、团队组织

```
SRE (Site Reliability Engineering):
  - 业务可靠性 + SLO
  - on-call + Incident
  - Postmortem
  
Platform Engineering:
  - 可观测性平台
  - AIOps 服务
  - GitOps + CI/CD
  - Self-service Backstage

DataOps / MLOps for AIOps:
  - 异常检测模型
  - 训练 pipeline
  - 模型部署
  - 反馈闭环

DevSecOps:
  - 安全审计
  - 合规
  - 国密 / 备案

人员 (中型 100 人工程):
  - SRE: 5-8 人 (含 on-call 轮值)
  - Platform: 3-5 人
  - AIOps: 1-3 人 (数据 + 算法)
  - 安全: 1-2 人
```

## 十、国产化路径

```
监控:        VictoriaMetrics + Grafana ⭐ (国产社区活跃)
日志:        ClickHouse / Apache Doris
链路:        Tempo + OTel (国际)
eBPF:        DeepFlow ⭐ (国产)
平台:        夜莺 ⭐ / 观测云 / 阿里 ARMS / 华为 AOM
LLM:        Qwen / DeepSeek / GLM + Ascend
告警:        飞书 / 钉钉 / 企业微信
Chaos:       Chaos Mesh ⭐ (国产 CNCF)
合规:        等保三级 + 国密 + 备案
信创:        鲲鹏 + openEuler + 国产 K8s

商业平台:
  阿里云 ARMS / SLS
  华为云 AOM / LTS
  腾讯云 APM / CLS
  观测云 (国产 SaaS) ⭐
  云杉 DeepFlow Enterprise
  博睿 BlueOps
```

## 十一、Incident SOP

```
P0:
  RTO < 15 min
  全员动员
  公司公告

P1:
  RTO < 1h
  on-call + 业务负责人
  群通知

P2:
  RTO < 4h
  on-call

P3:
  RTO < 24h
  工作时间

模板:
  - 告警接收 → 5min ack
  - 5-15min: 影响面评估 + 通知
  - 15-30min: RCA + 决策
  - 30min-1h: 执行 + 验证
  - 1h+: 持续监控 + 升级
  - 24h: Postmortem 草稿
  - 1w: Postmortem 终稿 + Action Item
```

## 十二、Postmortem

```
模板 (Google SRE):
  ☐ Summary (1 句话)
  ☐ Timeline (分钟级)
  ☐ Impact (用户 / 业务 / 时长)
  ☐ Root Cause (5 Whys / Causal)
  ☐ Resolution (如何修复)
  ☐ What went well
  ☐ What went wrong
  ☐ Action Items (责任人 + 期限)
  ☐ Lessons Learned

文化:
  - 无指责 (Blameless)
  - 透明 (公开分享)
  - 改进 (Action Item 跟踪)
  - 知识库 (RAG 入)
```

## 十三、KPI 度量

```
平台 KPI:
  ☐ 监控覆盖率 > 95%
  ☐ AIOps 覆盖率 > 30%
  ☐ 告警噪音率 < 10% (有效告警 / 总告警)
  ☐ MTTD < 5 min
  ☐ MTTA < 5 min
  ☐ MTTR < 30 min (P1)
  ☐ MTBF > 30 d (P0)
  ☐ SLO 达成率 > 99%
  ☐ Postmortem 完成率 100% (P0/P1)
  ☐ Action Item 完成率 > 80% (季度)
  ☐ Chaos 演练 季度执行
  ☐ on-call 平均工作量 < 20% (一周)
  ☐ 自愈成功率 > 60% (低风险)

业务 KPI:
  ☐ 可用性 99.9%+
  ☐ 错误率 < 0.1%
  ☐ P99 延迟达 SLO
  ☐ 业务停时 < 1h / 年
```

## 十四、持续学习闭环

```
1. 告警接收
2. 人工标注 (真假 + 根因)
3. 入历史库 (Postmortem + Vector DB)
4. 训练数据增量 (新数据 + 新标签)
5. 月度再训练 (异常检测 / RCA 模型)
6. AB 测试 (新模型 vs 旧)
7. 上线 + 监控
8. 反馈 (准确率 / 误报率)
9. 季度回顾
10. 闭环优化
```

## 十五、典型生产架构

### 15.1 互联网中型

```
监控:        VictoriaMetrics 3 节点 + Grafana
日志:        ClickHouse 5 节点 + Vector + Kafka
链路:        Tempo + OTel Collector + Coroot
告警:        Alertmanager + Karma + 钉钉
AIOps:      Prophet (动态阈值) + Coroot (RCA) + LLM (摘要)
ChatOps:    LangGraph Agent + MCP (Prometheus/K8s/Loki Server)
Chaos:       Chaos Mesh 季度演练
平台:        Backstage + 夜莺
模型:        Qwen 2.5-72B (vLLM) + bge-large-zh + Milvus
```

### 15.2 央企信创

```
硬件:        鲲鹏 + 昇腾 + openEuler
监控:        夜莺 ⭐ + VictoriaMetrics
日志:        阿里 SLS / 华为 LTS / ClickHouse 国产
链路:        SkyWalking ⭐ (Apache 国产)
eBPF:        DeepFlow ⭐ (国产)
LLM:        Qwen / DeepSeek + MindIE / LMDeploy
告警:        飞书 / 企业微信
合规:        等保三级 + 国密 + 备案
平台:        华为 AOM / 阿里 ARMS / 自研
```

## 十六、Checklist（最佳实践）

```
可观测性:
☐ 全栈采集 (Metrics + Logs + Traces + Events + Profile + RUM + Topology)
☐ 标签规范 (cluster/team/cost_center/env)
☐ 长期存储 (Hot/Warm/Cold)
☐ 强制 trace_id 关联

告警:
☐ SLO 驱动 (Sloth) ⭐
☐ 分级 (P0-P3)
☐ on-call 轮值 + 升级链
☐ 降噪 (group/inhibit/时间窗/LLM 摘要)
☐ 季度 review

异常检测:
☐ 选业务 → 训练 → 部署 → 监控 → 反馈
☐ 误报 < 5% / 漏报 < 1%
☐ KServe 部署
☐ 模型版本 + 漂移监控

RCA:
☐ 人工 SOP + AIOps 辅助
☐ Coroot 拓扑 + LLM RAG 历史
☐ Postmortem 模板

ChatOps:
☐ 4 阶段路径 (read → assist → auto → agent)
☐ RBAC + 审批 + 审计
☐ 多渠道 (钉钉 / 飞书 / 群)

自愈:
☐ 风险分级 + 审批
☐ Backstage / Argo / 自研
☐ 一键回滚 + 人工 override

Chaos:
☐ 季度生产演练
☐ 多场景覆盖
☐ MTTD/MTTA/MTTR 度量

治理:
☐ Metrics retention + 标签规范
☐ Logs JSON + PII 脱敏
☐ 模型治理 (MLflow + Feast)
☐ 合规 (等保 + 国密 + 备案)

团队:
☐ SRE + Platform + AIOps + Security 四组
☐ on-call 工作量 < 20%
☐ Postmortem Blameless

国产化:
☐ 夜莺 / DeepFlow / 观测云
☐ Qwen / DeepSeek + Ascend
☐ Chaos Mesh + 国密
☐ 信创栈

KPI:
☐ 覆盖率 / 噪音率 / MTTD / MTTA / MTTR / 自愈率
☐ SLO 达成率
☐ Postmortem 完成率 + Action Item

学习闭环:
☐ 标注 + 入库 (RAG)
☐ 月度再训练
☐ 季度回顾
```

## 十七、推荐栈（最佳实践）

```
监控:        VictoriaMetrics ⭐ + Grafana + Sloth
日志:        ClickHouse + Vector + Kafka
链路:        Tempo + OTel + SkyWalking (国产)
eBPF:        Coroot ⭐ + DeepFlow ⭐ (国产) + Pyroscope
告警:        Alertmanager + Karma + 钉钉/飞书
异常:        Prophet + Darts + USAD + KServe
RCA:        Coroot + DoWhy + LLM (Qwen + LangGraph + RAG)
ChatOps:    LangGraph ⭐ + MCP + Qwen 72B
Chaos:       Chaos Mesh ⭐ + 季度演练
GitOps:      ArgoCD + Argo Workflow + Sloth/Alerts as Code
平台:        夜莺 ⭐ + Backstage IDP + 自研门户
合规:        等保三级 + 国密 + 备案 + 审计 180d
LLM:        Qwen 2.5-72B / DeepSeek-V3 + vLLM/MindIE
向量:        Milvus + pgvector + bge-large-zh
```

> 📖 **核心判断**：AIOps 最佳实践 = **可观测性基线(全栈+标签+长期) + 告警工程化(SLO+分级+降噪) + 异常检测落地路径 + RCA SOP + ChatOps Agent 4 阶段 + 自愈守门(RBAC+审批+审计) + Chaos 演练 + 数据治理 + 团队组织 + 国产化路径 + Incident SOP + Postmortem Blameless + KPI 度量 + 持续学习闭环**。能给企业画"VictoriaMetrics + ClickHouse + Tempo + Coroot + LangGraph Agent + MCP + Chaos Mesh + ArgoCD + Backstage + 国产化(夜莺/DeepFlow/Qwen)"完整 AIOps 平台、能 Q1 演练 + MTTD/MTTR 度量 + on-call 工程化 + Postmortem 知识库 + 闭环学习，就具备 AIOps 平台负责人能力。
