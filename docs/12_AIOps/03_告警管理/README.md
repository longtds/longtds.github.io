# 告警管理

> 告警管理的真正难题不是"告警发出来"，而是"**告警发了被人看见、被人响应、不被滥用**"。**没有告警治理 + 收敛 + 分级 + 响应机制，AIOps 再强也救不回来**。

## 一、告警三大根本问题

```
1. 告警风暴
   一次故障 → 几十/几百条告警
   值班崩溃 / 关键告警淹没

2. 告警疲劳（Alert Fatigue）
   太多无意义告警 → 真告警也被忽略
   "狼来了"效应

3. 告警黑洞
   告警发出去，没人响应、没人复盘
   "告警 = 通知"而非"告警 = 行动"
```

## 二、告警治理金字塔

```
                  ┌─────────────────┐
                  │   行动 (Action)   │   ← 告警的归宿
                  ├─────────────────┤
                  │   响应 (Respond)  │   ← 谁、几分钟、怎么响应
                  ├─────────────────┤
                  │  分发 (Route)     │   ← 路由、分级、抑制
                  ├─────────────────┤
                  │   收敛 (Reduce)   │   ← 去重、聚合、关联
                  ├─────────────────┤
                  │   产生 (Emit)     │   ← 规则、阈值、SLO 驱动
                  └─────────────────┘

99% 团队的问题:
  ❌ 只投入"产生"层，往后越来越薄
  ✅ 真正成熟的团队投入分布: 产生 20% / 收敛 30% / 分发 20% / 响应 20% / 行动 10%
```

## 三、告警产生（Emit）：怎么定阈值

### 3.1 SLO 驱动的告警

```yaml
# 不要从指标定阈值，从用户体验出发
SLO: 订单 API 5xx 率 < 0.1%，p99 < 500ms

衍生 SLI（Indicator）:
  - http_request_errors_5xx_rate
  - http_request_duration_p99

告警规则:
  burn_rate > 14.4   → P1（1 小时烧完月度预算的 2%）
  burn_rate > 6      → P2（6 小时烧完）
  burn_rate > 1      → P3（趋势预警）
```

### 3.2 Prometheus Burn Rate 告警

```yaml
# Multi-Window Multi-Burn-Rate
- alert: SLOFastBurn
  expr: |
    (
      slo:burnrate1h{service="order"} > 14.4
      and
      slo:burnrate5m{service="order"} > 14.4
    )
  for: 2m
  labels:
    severity: P1
  annotations:
    summary: "订单 SLO 1h 燃烧速率超 14.4x"

- alert: SLOSlowBurn
  expr: |
    (slo:burnrate6h{service="order"} > 6 and slo:burnrate30m{service="order"} > 6)
  for: 15m
  labels:
    severity: P2
```

**经验**：用 burn rate 替代固定阈值，**误报率降 70%**，参考 Google SRE Workbook。

### 3.3 阈值告警的反模式

```
❌ 告警写法（典型错误）:
  - alert: HighCPU
    expr: cpu_usage > 80
  
  问题:
    1. 80% 是从哪来的？
    2. 持续多久才告？
    3. 谁应该响应？
    4. 影响什么业务？

✅ 改进版:
  - alert: NodeCPUSaturation
    expr: |
      (avg_over_time(node_cpu_usage[15m]) > 0.85)
      and
      (predict_linear(node_cpu_usage[30m], 1800) > 0.95)
    for: 10m
    labels:
      severity: P2
      team: infra
      runbook: https://wiki/runbooks/node-cpu
    annotations:
      summary: "节点 {{ $labels.instance }} CPU 持续高位，30 分钟内可能耗尽"
      impact: "可能影响该节点的所有业务 Pod"
      action: "1. kubectl describe node 看是哪个 Pod；2. 评估扩容/驱逐"
```

### 3.4 黄金信号 + RED + USE

```
Google 黄金四信号（每个服务必有）:
  1. Latency      延迟
  2. Traffic      流量
  3. Errors       错误
  4. Saturation   饱和度

RED（请求驱动型服务）:
  - Rate
  - Errors
  - Duration

USE（资源型）:
  - Utilization
  - Saturation
  - Errors

→ 每个服务覆盖这 3-4 类，告警规则数量自然就少了
```

## 四、告警收敛（Reduce）：核心战场

### 4.1 三段式收敛

```
告警风暴 100 条
   ↓ ① 去重 (Dedup)
   60 条（合并相同 fingerprint）
   ↓ ② 抑制 (Inhibit)
   20 条（父告警压制子告警）
   ↓ ③ 聚类 (Cluster)
   5 个事件组（同时间窗口/同业务）
   ↓
   1-2 条 LLM 摘要的通知
```

### 4.2 Alertmanager 配置最佳实践

```yaml
route:
  receiver: 'wechat-default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s              # 同组首次告警等 30s 合并
  group_interval: 5m           # 同组后续告警间隔 5m
  repeat_interval: 4h          # 未恢复 4h 重发一次

  routes:
    - matchers:
        - severity = P0
      receiver: 'phone-call'
      group_wait: 0s           # P0 立即
      repeat_interval: 30m
    
    - matchers:
        - severity = P1
      receiver: 'wechat-oncall'
      group_wait: 10s
      repeat_interval: 1h
    
    - matchers:
        - severity = P3
      receiver: 'email'
      group_wait: 5m
      repeat_interval: 24h

# 抑制规则（关键）
inhibit_rules:
  # 节点宕机时压制所有该节点上的 Pod 告警
  - source_matchers: [alertname=NodeDown]
    target_matchers: [alertname=PodNotReady]
    equal: [instance]
  
  # 集群整体故障时压制单服务告警
  - source_matchers: [alertname=ClusterDown]
    target_matchers: [severity=~"P[1-3]"]
    equal: [cluster]
  
  # 上游故障时压制下游
  - source_matchers: [alertname=DBDown, service=mysql]
    target_matchers: [severity=~"P[1-2]"]
    equal: [cluster]
```

### 4.3 关联与拓扑

```python
# 基于服务依赖图的关联
service_topology = {
    "order-api": ["mysql", "redis", "kafka", "user-api"],
    "user-api": ["mysql", "redis"],
    ...
}

def correlate_alerts(alerts):
    """如果根因服务也在告警，关联起来"""
    groups = []
    for alert in alerts:
        for parent in service_topology.get(alert.service, []):
            parent_alerts = [a for a in alerts if a.service == parent]
            if parent_alerts:
                groups.append({
                    "root": parent_alerts[0],
                    "affected": [alert]
                })
    return merge_groups(groups)
```

### 4.4 时间窗口聚类

```python
from sklearn.cluster import DBSCAN

def cluster_by_time(alerts, window=300):
    """5 分钟内同一业务的告警归一组"""
    features = np.array([[a.timestamp, hash(a.business)] for a in alerts])
    features[:,0] = (features[:,0] - features[:,0].min()) / window
    labels = DBSCAN(eps=0.5, min_samples=2).fit_predict(features)
    return labels
```

## 五、告警分级（Severity）

### 5.1 经典 4 级（推荐）

| 级别 | 含义 | 响应 | 通知方式 |
|:---:|:---|:---|:---|
| **P0** | 全站不可用 / 数据丢失 / 资损 | 立即 (≤ 5 min) | 电话 + 短信 + 群 @值班 |
| **P1** | 核心功能受损 / 大面积影响 | ≤ 15 min | 电话 + 群 @值班 |
| **P2** | 部分功能降级 / 性能下降 | ≤ 1 h | 群消息 + 邮件 |
| **P3** | 容量预警 / 趋势 | 工作时间 | 邮件 / 日报 |

### 5.2 分级的决定因素

```
影响范围
  + 用户量
  + 资损金额
  + 业务关键度
  + 当前时段（白天 vs 凌晨）
  + 是否有降级方案
   ↓
  动态分级（不要全静态）
```

### 5.3 动态升级（Escalation）

```yaml
# 第一通知人 5min 未响应 → 升级
escalation_policy:
  - level: 0
    notify: oncall-primary
    timeout: 5m
  - level: 1
    notify: oncall-secondary
    timeout: 5m
  - level: 2
    notify: oncall-manager
    timeout: 10m
  - level: 3
    notify: incident-commander
```

## 六、告警分发（Route）

### 6.1 路由维度

```
按 service     → 服务 owner
按 team        → 团队 webhook
按 cluster     → 区域值班
按 severity    → 通知方式分级
按 time        → 工作时间 vs 非工作时间
按 business    → 业务对应的责任人
```

### 6.2 通知通道选择

| 通道 | 适用 | 缺点 |
|:---|:---|:---|
| **电话** | P0 | 贵、噪声大 |
| **短信** | P0/P1 | 可能漏 |
| **企业微信/钉钉/飞书机器人** | 主力通道 | 群里容易刷屏 |
| **企微@特定人** | P0/P1 必备 | 没设置好就漏 |
| **PagerDuty / OpsGenie** | 国际化团队 | 国内贵 |
| **邮件** | P2/P3 | 时效差 |
| **Slack / 钉钉日历** | 日报/周报 | 不实时 |
| **Jira / Issue** | 后续跟踪 | 不主动 |

### 6.3 国内通知机器人

```python
# 企业微信
def send_wechat(msg):
    requests.post(WECHAT_WEBHOOK, json={
        "msgtype": "markdown",
        "markdown": {"content": msg},
        "mentioned_list": ["@all"]  # P0
    })

# 钉钉
def send_dingtalk(msg, at_phones=[]):
    requests.post(DING_WEBHOOK, json={
        "msgtype": "markdown",
        "markdown": {"title": "告警", "text": msg},
        "at": {"atMobiles": at_phones, "isAtAll": False}
    })

# 飞书
def send_feishu(msg):
    requests.post(FS_WEBHOOK, json={
        "msg_type": "interactive",
        "card": {...}
    })
```

### 6.4 卡片化通知（强烈推荐）

```python
# 把"一坨文本"变"结构化卡片"
def alert_card(alert, llm_result):
    return {
        "msgtype": "template_card",
        "template_card": {
            "card_type": "text_notice",
            "main_title": {"title": f"[{alert.severity}] {llm_result.summary}"},
            "emphasis_content": {
                "title": llm_result.impact_scope,
                "desc": "影响范围"
            },
            "sub_title_text": llm_result.root_causes[0].cause,
            "horizontal_content_list": [
                {"keyname": "服务", "value": alert.service},
                {"keyname": "实例", "value": alert.instance},
                {"keyname": "时间", "value": alert.timestamp},
                {"keyname": "Runbook", "value": "查看", "url": alert.runbook_url}
            ],
            "card_action": {"type": 1, "url": alert.dashboard_url},
            "jump_list": [
                {"type": 1, "url": GRAFANA_URL, "title": "看监控"},
                {"type": 1, "url": LOG_URL, "title": "看日志"},
                {"type": 1, "url": TRACE_URL, "title": "看链路"},
            ]
        }
    }
```

## 七、值班机制（On-call）

### 7.1 值班排班原则

```
✅ 公平轮换:
  - 工作日 / 周末分开排
  - 节假日轮值
  - 主备双岗

✅ 主备制:
  - Primary: 5 分钟响应
  - Secondary: Primary 失联兜底

✅ 工时管控:
  - 单人单周不超过 7×24
  - 月度值班 ≤ 2 周
  - 凌晨告警次日给调休

✅ 跨时区:
  - Follow the sun（亚/欧/美轮值）
  - 中国团队: 早班/晚班对接
```

### 7.2 PagerDuty 替代品

| 工具 | 类型 |
|:---|:---|
| **PagerDuty** | 国际主流，国内贵 |
| **OpsGenie** | Atlassian，已淡出 |
| **Squadcast** | 印度，便宜 |
| **FlashDuty 闪电值班** | 国产首选 |
| **夜莺 Nightingale + n9e-edge** | 开源国产 |
| **自建 Cron + 值班表** | 中小团队够用 |

### 7.3 值班 SOP

```
1. 收到告警（≤ 1 min）
2. 在值班群 ACK（"我在看 INC-xxxx"）
3. 评估严重度（确认/调整）
4. 拉群（P0/P1 拉故障群）
5. 调查 + 缓解（不一定先定位根因，先止血）
6. 进展同步（每 15 min 一次）
7. 恢复确认
8. 故障复盘
```

## 八、响应（Respond）：从告警到行动

### 8.1 ACK 机制

```python
# 告警卡片带 ACK 按钮
# 点击后:
#   - 标记为"调查中"
#   - 暂停 repeat
#   - 升级时钟开始计时
@app.post("/ack")
def ack(alert_id, user):
    alertmanager.silence(alert_id, duration="30m", creator=user)
    notify_group(f"{user} 已接手 {alert_id}")
```

### 8.2 SOP 自动展开

```python
# 告警时根据 alertname 自动展示步骤
def render_sop(alertname):
    sop = load_runbook(alertname)
    return f"""
    ## 处置步骤
    1. {sop.step1}
    2. {sop.step2}
    ...
    
    ## 一键操作
    [扩容] [重启] [限流] [降级]
    """
```

### 8.3 Webhook + ChatOps

```
在群里输入命令直接操作:

@bot kubectl rollout restart order-api
@bot scale order-api 10
@bot status mysql-prod
@bot drain node-101
```

实现：飞书/钉钉/企微机器人 + 后端 RBAC + 审计日志。

### 8.4 一键诊断

```python
# 在卡片上提供"一键诊断"按钮，调用 LLM Agent 取证
@app.post("/diagnose")
def diagnose(alert_id):
    alert = load_alert(alert_id)
    result = llm_agent_diagnose(alert)   # 见 02_LLM告警
    return result
```

## 九、复盘（Postmortem）

### 9.1 复盘模板

```markdown
# Incident Report: INC-2026-06-22-001

## 基本信息
- 故障开始: 2026-06-22 14:30
- 故障发现: 14:32（监控告警）
- 故障恢复: 14:55
- 持续时长: 25 分钟
- 影响范围: 订单 API 5xx，约 20% 用户下单失败
- 严重度: P1

## 时间线
14:30 - 上线 order-api v1.2.3
14:31 - p99 开始上升
14:32 - SLOFastBurn 告警触发
14:33 - 值班 ACK，开始调查
14:40 - 定位为 N+1 SQL 查询
14:45 - 决定回滚
14:55 - 回滚完成，监控恢复

## 根因分析（5 Why）
1. 为什么 p99 突增? → 订单详情 SQL 性能下降 100x
2. 为什么 SQL 性能下降? → 新加的关联表未走索引
3. 为什么未走索引? → 索引在线创建未完成就发版
4. 为什么未完成就发版? → 没有"前置依赖"check
5. 为什么没有 check? → CI 流程缺失

## 改进项 (Action Items)
| ID | 改进 | 负责人 | DDL |
|:---|:---|:---|:---|
| A1 | CI 添加 SQL 性能 check | 张三 | 2026-07-01 |
| A2 | 加索引创建状态依赖 | 李四 | 2026-06-30 |
| A3 | Runbook 添加 N+1 查询定位 | 王五 | 2026-06-25 |

## 经验沉淀
- 教训: 数据库 DDL 与代码发布要解耦
- 工具改进: 自动检测 N+1
- 流程改进: 大变更前自动 perf 测试
```

### 9.2 复盘原则

```
✅ Blameless（不指责个人）
✅ 24h 内必须开始
✅ 一周内必须出报告
✅ 改进项有 owner + DDL
✅ 改进项要跟踪到关闭
✅ 经验沉淀到 Wiki / RAG

❌ 不要变批斗会
❌ 不要只复盘 P0
❌ 不要"行动项"挂着不闭环
```

### 9.3 复盘评分

```python
# 给每个事故的"过程"打分（非结果）
metrics = {
    "MTTD": "...",            # Mean Time to Detect
    "MTTA": "...",            # Mean Time to ACK
    "MTTM": "...",            # Mean Time to Mitigate
    "MTTR": "...",            # Mean Time to Resolve
    "communication_score": ..., # 沟通是否及时
    "tooling_score": ...,      # 工具是否齐备
    "process_score": ...,      # 流程是否顺畅
}
```

## 十、SLO 与告警预算

### 10.1 错误预算（Error Budget）

```
SLO = 99.95%
30 天预算 = 21.6 分钟下线时间
   或 = 21,600 次失败请求（按 QPS）

烧完了:
  → 冻结非紧急发布
  → 投入稳定性 / 优化
```

### 10.2 多窗口多速率告警

```yaml
# Google SRE 推荐
快烧（短窗口高速率）: 1h × 14.4x 燃烧速率 → P1
中烧: 6h × 6x → P2
慢烧: 3d × 1x → P3
```

### 10.3 SLO 工具

| 工具 | 类型 |
|:---|:---|
| **Sloth** | 用 YAML 生成 Prom SLO 规则 |
| **OpenSLO** | 标准规范 |
| **Pyrra** | K8s SLO Controller |
| **Nobl9** | 商业 SLO 平台 |
| 阿里 ARMS SLO | 国内 |

## 十一、告警度量与质量管理

### 11.1 关键指标

```
告警总量趋势
  日均 / 周均 / 月均
  按服务 / 按团队 / 按严重度
  
告警质量
  - 误报率 (false positive rate)
  - 漏报率 (false negative)
  - 可执行率（有人操作了的比例）
  - 噪声告警 / 真告警比

响应指标
  - MTTD / MTTA / MTTM / MTTR
  - ACK 时长 p50/p99
  - 升级次数
  
人力影响
  - 值班次数 / 人 / 月
  - 凌晨告警数 / 人
  - 非工作时间响应时长
```

### 11.2 告警治理周报

```
本周告警数: 1234 (↓ 15%)
误报数: 80 (↓ 30%)
TOP 噪声源:
  1. CPU > 80% × 320 次 → 已优化阈值
  2. 磁盘 IO util × 180 次 → 已抑制
  3. ...

下周改进:
  - 删除 5 条历史无用规则
  - 调整 3 条阈值
  - 关联 2 个抑制规则
```

### 11.3 告警准入流程

```
新增告警规则必须:
  ✅ 关联 SLO 或明确业务影响
  ✅ 写明 Runbook 链接
  ✅ 明确 owner（哪个团队接）
  ✅ 已有抑制 / 关联规则
  ✅ 通过 review

→ 否则一律拒绝合入
```

## 十二、告警系统选型

### 12.1 开源栈

| 组件 | 推荐 |
|:---|:---|
| 指标采集 | Prometheus / VictoriaMetrics |
| 告警评估 | Prometheus / VMAlert |
| 路由通知 | Alertmanager / 夜莺 |
| 值班 | FlashDuty / 自建 |
| 复盘 | Wiki + Jira |
| LLM 加工 | 见 02_LLM告警 |

### 12.2 国产开源

```
夜莺 (Nightingale):
  ✅ 监控告警一体化
  ✅ 中文友好
  ✅ 内置值班 / 通知
  ✅ 接入 Prom / VM
  ✅ 国内主流替代品

蓝鲸:
  ✅ 腾讯开源
  ✅ 重型平台
  ✅ 适合大企业

观测云 / DataKit:
  ✅ 商业但有开源 Agent
```

### 12.3 商业产品

| 产品 | 厂商 |
|:---|:---|
| **PagerDuty** | 国际主流，国内贵 |
| **Datadog** | 全栈 |
| **Splunk** | 日志 + 告警 |
| **阿里云 ARMS** | 国内主流 |
| **腾讯云 APM** | 国内 |
| **观测云** | 国产 |
| **博睿数据** | 国产 |

## 十三、常见坑

| 坑 | 建议 |
|:---|:---|
| **告警没 owner** | 必填团队/服务 owner |
| **告警没 Runbook** | 必填 runbook URL |
| **没有抑制规则** | 父子告警必抑制 |
| **没有静默期** | 变更窗口必静默 |
| **告警和监控耦合** | 告警规则独立于 dashboard |
| **告警群没人** | 拉错群 / 全员屏蔽 |
| **凌晨告警全 P0** | 严格 SLO 分级 |
| **重启就完事** | 必复盘 + 改进项 |
| **改进项不跟踪** | Jira 看板 + 周会 |
| **没有静默 API** | 一键静默 + 审计 |
| **多通道刷屏** | 同事件只通知一次 |
| **告警含敏感信息** | 脱敏（密码/token） |
| **没有节流** | 同告警 1h 内最多 N 次 |
| **告警依赖被告警系统** | 告警系统独立部署 |
| **不演练** | 季度故障注入 + 演练 |

## 十四、最佳实践清单（Checklist）

```
告警规则:
☐ 关联 SLO 或明确业务影响
☐ 有 owner / team / runbook
☐ 有 severity 分级
☐ 包含影响范围、动作建议
☐ 持续时间 (for) 合理（避免抖动）

告警分发:
☐ Alertmanager 抑制规则齐全
☐ 路由按 severity / team 分流
☐ P0/P1 有电话/短信通道
☐ 变更窗口能静默
☐ 卡片化通知（不要纯文本）

告警响应:
☐ ACK 机制
☐ 升级策略
☐ Runbook 一键打开
☐ 一键诊断（LLM）
☐ ChatOps 集成

值班体系:
☐ 主备双岗
☐ 排班公开
☐ 凌晨调休
☐ 月度值班 ≤ 2 周

复盘:
☐ 24h 内启动
☐ 一周内出报告
☐ Blameless 原则
☐ 改进项有 owner / DDL
☐ 改进项跟踪到关闭

度量:
☐ 周报跟踪告警量
☐ 月度治理评审
☐ 误报率 / MTTR 看板
☐ TOP 噪声告警治理
```

## 十五、学习路径

```
入门（1 周）:
  1. Prometheus + Alertmanager 跑通
  2. 写 10 条基础告警规则
  3. 接入企业微信通知

中级（1 个月）:
  4. SLO + Burn Rate 告警
  5. 抑制 + 路由完善
  6. 值班轮换机制
  7. 复盘模板 + 流程

高级（3 个月+）:
  8. 告警治理周报 + 度量
  9. LLM 加工告警
  10. ChatOps 集成
  11. 一键诊断 / 自愈
  12. 故障注入 + 演练

专家:
  13. 多集群多区域告警
  14. SLO 平台化
  15. 跨团队告警生态
  16. AI 化告警治理（自动调阈值/收敛）
```

## 十六、参考资料

```
书:
  - 《Site Reliability Engineering》(Google SRE)
  - 《The Site Reliability Workbook》(Google)
  - 《Seeking SRE》(O'Reilly)
  - 《Implementing Service Level Objectives》(Alex Hidalgo)

博客:
  - Google SRE Workbook
  - Increment Magazine
  - 字节跳动 SRE 公众号
  - 阿里巴巴 SRE 实践
  - 腾讯运维社区

开源:
  - Sloth: https://github.com/slok/sloth
  - Pyrra: https://github.com/pyrra-dev/pyrra
  - Nightingale: https://github.com/ccfos/nightingale
  - FlashDuty: https://flashcat.cloud/

工具:
  - PromQL Cheatsheet
  - SLO Generator
  - Postmortem Templates (Google/Atlassian)
```

> 📖 **核心判断**：告警管理是 SRE 工作的"地基"。**SLO 驱动 + Burn Rate + 收敛三段式 + 分级路由 + Blameless 复盘** 是五大支柱。投入"产生"层 1 倍精力，往后每一层都要 1.5 倍投入，否则 LLM/AIOps 等高级能力建立在沙子上。**国内开源首选夜莺 + Alertmanager + 飞书/企微/钉钉机器人 + FlashDuty 值班**。
