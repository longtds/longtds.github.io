# 部署策略

> 发布是 SRE 一年最危险的几十次操作。**让"上线"从"心惊胆战"变成"按下按钮"** = 蓝绿 / 金丝雀 / 滚动 / 影子 / Feature Flag 全套策略 + GitOps + 渐进式发布 + 自动回滚。

## 一、为什么部署策略重要

```
统计事实:
  - 60-80% 的生产事故由"发布变更"引起
  - 一次失败发布的平均损失 = 数小时业务 + 团队信任
  - 优秀团队: 上线 100 次失败 1 次（精英 < 15%）
  - 普通团队: 上线 100 次失败 30+ 次

部署策略的目标:
  ✅ 影响范围可控（金丝雀 1% → 10% → 100%）
  ✅ 失败快速止血（< 1 分钟回滚）
  ✅ 灰度数据可观测（业务指标 + SLO）
  ✅ 数据兼容（向前 + 向后）
  ✅ 流量切换平滑（不丢请求）
```

## 二、八大部署策略对比

| 策略 | 风险 | 速度 | 资源 | 数据兼容 | 适用 |
|:---|:---:|:---:|:---:|:---:|:---|
| **Recreate**（停机）| 🔴🔴🔴🔴🔴 | 快 | 1x | 灵活 | 临时 / 内部工具 |
| **Rolling**（滚动）| 🔴🔴 | 中 | 1x | 严格 | 默认 K8s |
| **Blue-Green**（蓝绿）| 🔴 | 快 | 2x | 严格 | 关键业务 |
| **Canary**（金丝雀）| 🔴 | 慢 | 1.1-2x | 严格 | 大流量 ⭐ |
| **A/B Testing** | 🟡 | 慢 | 1.1x | 灵活 | 业务实验 |
| **Shadow**（影子）| 🟢 | 慢 | 2x | 严格 | 高风险变更 |
| **Feature Flag** | 🟢 | 即时 | 1x | 灵活 | 功能开关 ⭐ |
| **Progressive Delivery** | 🟢 | 自动 | 1.1x | 严格 | 综合方案 ⭐⭐⭐ |

## 三、Recreate（停机部署）

```
流程:
  1. 停止所有旧版本
  2. 启动新版本

K8s 配置:
  strategy:
    type: Recreate

特点:
  ✅ 实现简单
  ✅ 资源最省
  ✅ 数据迁移可控
  ❌ 有停机时间
  ❌ 用户感知

适用:
  - 内部工具
  - 测试环境
  - 单实例临时服务
  - 状态机要求强一致升级
```

## 四、Rolling（滚动更新）⭐ K8s 默认

```
流程:
  逐个/批次替换 Pod
  Pod 1 → 新版本 → 健康 → Pod 2 → ... → 完成

K8s 配置:
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1           # 最多多 1 个
      maxUnavailable: 0     # 不允许任何不可用
  
  template:
    spec:
      containers:
        - name: app
          readinessProbe:                  # 必须有
            httpGet: { path: /healthz, port: 8080 }
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 3
          livenessProbe:
            httpGet: { path: /live, port: 8080 }
            initialDelaySeconds: 30
          startupProbe:                    # 长启动应用
            httpGet: { path: /startup, port: 8080 }
            failureThreshold: 30
            periodSeconds: 10
          lifecycle:
            preStop:                       # 优雅退出
              exec:
                command: ["/bin/sh", "-c", "sleep 15 && /app shutdown"]
      terminationGracePeriodSeconds: 60
```

### 4.1 关键参数

```
maxSurge:        启动时可超出的 Pod 数 / 百分比
maxUnavailable:  滚动中可不可用的 Pod 数 / 百分比

经验:
  小集群（< 10 副本）: maxSurge=1, maxUnavailable=0
  中集群: maxSurge=25%, maxUnavailable=0
  大集群: maxSurge=10%, maxUnavailable=10%
```

### 4.2 优雅退出（Graceful Shutdown）

```
正确流程:
  1. 收到 SIGTERM
  2. 标记 not ready (摘出 LB)
  3. 处理完已接入连接
  4. 关闭新连接监听
  5. 等所有连接关闭
  6. 退出

代码（Go）:
  signal.Notify(sigChan, syscall.SIGTERM)
  <-sigChan
  server.Shutdown(ctx)

K8s preStop sleep:
  - 给 endpoint 控制器 + service mesh 时间剔除 endpoint
  - 通常 10-30s
```

### 4.3 Rolling 局限

```
❌ 一旦发现问题，整批已部分更新（不易回滚）
❌ 不能基于业务指标决策
❌ 新旧版本并存期间需保证数据兼容
❌ 没有"灰度暂停"概念
```

## 五、Blue-Green（蓝绿部署）

```
原理:
  Blue (旧)   ← 流量
  Green (新)  ← 预备
  
  切换瞬间: Blue → Green
  
  ✅ 切换快（< 1 秒）
  ✅ 回滚秒级
  ❌ 资源 2x
  ❌ 长连接断开
```

### 5.1 K8s 蓝绿实现

```yaml
# Service 通过 selector 切换
apiVersion: v1
kind: Service
metadata: { name: app }
spec:
  selector:
    app: my-app
    version: blue        # 切到 green 时改这里
  ports: [{ port: 80, targetPort: 8080 }]
---
# Blue Deployment
apiVersion: apps/v1
kind: Deployment
metadata: { name: app-blue }
spec:
  replicas: 10
  template:
    metadata: { labels: { app: my-app, version: blue } }
    spec: ...
---
# Green Deployment
apiVersion: apps/v1
kind: Deployment
metadata: { name: app-green }
spec:
  replicas: 10
  template:
    metadata: { labels: { app: my-app, version: green } }
    spec: ...
```

### 5.2 Argo Rollouts 蓝绿

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: app }
spec:
  replicas: 10
  strategy:
    blueGreen:
      activeService: app-active
      previewService: app-preview
      autoPromotionEnabled: false        # 必须手动确认
      scaleDownDelaySeconds: 30
      prePromotionAnalysis:
        templates:
          - templateName: smoke-test
        args:
          - name: service
            value: app-preview
      postPromotionAnalysis:
        templates:
          - templateName: success-rate
```

### 5.3 蓝绿 vs 滚动选择

```
何时选蓝绿:
  ✅ 强需要瞬间切换
  ✅ 需要"全量预演"验证
  ✅ 数据库变更与代码同步切换
  ✅ 旧版本可快速回切

何时选滚动:
  ✅ 资源紧张
  ✅ 长连接服务（避免一次性断开）
  ✅ 大流量场景
  ✅ 无状态服务
```

## 六、Canary（金丝雀）⭐⭐⭐⭐⭐

```
原理:
  100% 流量 → 老版本
  
  发布 1% → 新版本（金丝雀）
  观察 10 分钟，指标 OK
  发布 10% → 新版本
  观察 30 分钟
  发布 50% → 新版本
  观察 1 小时
  发布 100% → 新版本

  ✅ 风险可控
  ✅ 真实业务流量验证
  ✅ 可基于指标自动决策
  ❌ 部署链路长（需要流量切分能力）
```

### 6.1 Argo Rollouts 金丝雀（推荐）

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: order-api }
spec:
  replicas: 20
  strategy:
    canary:
      canaryService: order-canary
      stableService: order-stable
      trafficRouting:
        istio:                     # 或 nginx / smi / alb
          virtualService:
            name: order-vs
            routes: [primary]
      steps:
        - setWeight: 1
        - pause: { duration: 5m }
        - analysis:
            templates: [{ templateName: success-rate }]
            args:
              - name: service
                value: order-canary
        - setWeight: 5
        - pause: { duration: 10m }
        - setWeight: 25
        - pause: { duration: 10m }
        - setWeight: 50
        - pause: { duration: 30m }
        - setWeight: 100
  template: ...
---
# AnalysisTemplate：基于 Prometheus 指标自动判断
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata: { name: success-rate }
spec:
  args: [{ name: service }]
  metrics:
    - name: success-rate
      interval: 30s
      successCondition: result[0] >= 0.99
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(istio_requests_total{destination_service=~"{{args.service}}.*", response_code!~"5.*"}[1m])) /
            sum(rate(istio_requests_total{destination_service=~"{{args.service}}.*"}[1m]))
    - name: p99-latency
      provider:
        prometheus:
          query: |
            histogram_quantile(0.99,
              sum(rate(istio_request_duration_milliseconds_bucket{destination_service=~"{{args.service}}.*"}[1m]))
              by (le)
            )
      successCondition: result[0] < 500
```

### 6.2 Flagger 金丝雀（备选）

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata: { name: order-api }
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-api
  service:
    port: 80
    targetPort: 8080
    gateways: [public-gateway.istio-system.svc]
    hosts: [order.example.com]
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        thresholdRange: { min: 99 }
        interval: 1m
      - name: request-duration
        thresholdRange: { max: 500 }
        interval: 30s
    webhooks:
      - name: pre-rollout
        url: http://flagger-tester/check-deps
      - name: load-test
        url: http://flagger-tester/load
```

### 6.3 流量切分能力

| 工具 | 流量切分粒度 | 适合 |
|:---|:---|:---|
| **Istio** | 任意比例 + Header | 全功能 ⭐ |
| **Linkerd** | 比例 | 简单场景 |
| **Nginx Ingress** | 比例 + Cookie/Header | 通用 |
| **Higress** | 比例 + 高级 | 阿里开源 |
| **APISIX** | 比例 + 灰度规则 | 国产首选 |
| **AWS ALB** | 比例 | AWS 原生 |
| **SMI**（Service Mesh Interface）| 抽象层 | 多 Mesh |

### 6.4 用户/Header 灰度（精细化）

```yaml
# Istio VirtualService - 按 Header 灰度
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata: { name: order-vs }
spec:
  hosts: [order.example.com]
  http:
    # 内部测试人员先用新版
    - match:
        - headers:
            x-canary-user: { exact: "true" }
      route:
        - destination: { host: order-api, subset: canary }
    
    # VIP 客户走稳定版（先不上灰度）
    - match:
        - headers:
            x-user-tier: { exact: "vip" }
      route:
        - destination: { host: order-api, subset: stable }
    
    # 其他用户按比例
    - route:
        - destination: { host: order-api, subset: stable }
          weight: 95
        - destination: { host: order-api, subset: canary }
          weight: 5
```

## 七、A/B Testing（实验型部署）

```
与金丝雀的区别:
  Canary:    判断"新版本是否稳定"
  A/B:       判断"新版本是否更好"
  
A/B 路由依据:
  - User ID hash
  - Cookie
  - 地域
  - 设备
  - 业务标签（新用户 vs 老用户）

工具:
  - Istio VirtualService (Header)
  - Unleash / GrowthBook / LaunchDarkly
  - Optimizely / Split.io
  - 内部实验平台
```

```yaml
# 实验配置示例
experiment:
  name: new-pricing-algorithm
  variants:
    - name: control
      weight: 50
      version: stable
    - name: treatment-a
      weight: 25
      version: pricing-v2
    - name: treatment-b
      weight: 25
      version: pricing-v3
  metrics:
    primary: revenue_per_user
    secondary: [conversion_rate, p99_latency]
  duration: 14d
  segments:
    include: ["country=cn"]
    exclude: ["user_tier=vip"]
```

## 八、Shadow（影子部署）

```
原理:
  生产流量 1:1 复制到新版本
  
  Stable 处理：返回真实响应
  Shadow 处理：丢弃响应（仅观测）
  
  ✅ 零用户风险
  ✅ 真实负载验证
  ✅ 性能压测真实化
  ❌ 资源 2x
  ❌ 副作用慎用（写操作 → 必须幂等或屏蔽写）
```

### 8.1 Istio Shadow（Mirror）

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
spec:
  http:
    - route:
        - destination: { host: order-api, subset: stable }
      mirror:
        host: order-api
        subset: canary
      mirrorPercentage: { value: 100.0 }
```

### 8.2 适用场景

```
✅ 大版本性能验证
✅ 新数据库切换前压测
✅ 算法 A/B 离线对比
✅ 缓存命中率验证

⚠️ 注意:
  - 写操作要么屏蔽要么导向影子库
  - 第三方调用要 mock 避免重复扣费
  - 日志要带 mirror 标记便于过滤
```

## 九、Feature Flag（特性开关）⭐⭐⭐⭐⭐

```
核心思想:
  "代码上线 ≠ 功能启用"
  
  发布 → 关闭开关 → 按需打开（小用户 → 全量）
  
  问题 → 关闭开关秒级回滚（不需重发版）

工具:
  ✅ LaunchDarkly（商业，行业标杆）
  ✅ Unleash（开源，国内可部署）⭐
  ✅ GrowthBook（开源 A/B + Flag）
  ✅ Flagsmith（开源）
  ✅ ConfigCat（SaaS）
  ✅ Split.io（商业）
  ✅ 字节 ABase / 阿里 AHAS / 自研
```

### 9.1 Unleash 实战

```python
from UnleashClient import UnleashClient

client = UnleashClient(
    url="https://unleash.company.com/api",
    app_name="order-service",
    custom_headers={"Authorization": API_KEY}
)
client.initialize_client()

# 简单开关
if client.is_enabled("new-checkout-flow"):
    return new_checkout()
else:
    return legacy_checkout()

# 带上下文（按用户分组）
ctx = {"userId": user.id, "country": user.country, "tier": user.tier}
if client.is_enabled("ai-recommendation", context=ctx):
    return ai_recommend(user)
```

### 9.2 Feature Flag 模式

```
1. Release Toggle      渐进发布（灰度）
2. Experiment Toggle   A/B 实验
3. Ops Toggle          运维开关（限流/降级）
4. Permission Toggle   按用户/角色启用
```

### 9.3 治理

```
✅ Flag 命名规范: <category>.<feature>.<env>
   release.new-checkout.prod
   experiment.ai-rec.all
   ops.rate-limit.china

✅ 生命周期管理
   - 创建时定 owner + 过期时间
   - 过期自动告警
   - 定期清理（避免代码逻辑爆炸）

✅ 默认值安全
   - 网络挂时默认值要安全
   - 多重 fallback

❌ 不要:
   - 用 Flag 改业务核心规则
   - 嵌套多层 Flag
   - 长期不清理
```

## 十、Progressive Delivery（渐进式交付）⭐⭐⭐⭐⭐

```
Progressive Delivery = Canary + Feature Flag + 自动化指标决策

完整流程:
  1. 代码合入 main → CI 构建 + 签名
  2. GitOps 推送到集群（功能 Flag 关闭）
  3. 小批 Pod 部署
  4. 自动观察指标 5-30 分钟
  5. 指标 OK → 逐步放大流量
  6. 指标差 → 自动回滚
  7. 100% 流量后 → 业务逐步打开 Flag
  8. 持续观察 + 完整放开

工具组合:
  Argo CD              GitOps
  Argo Rollouts        渐进发布
  Prometheus           指标
  Flagger / Argo       自动分析
  Unleash              Feature Flag
  Istio / Linkerd      流量切分
```

## 十一、数据库变更与发布

### 11.1 数据兼容三段式

```
任何新版本必须满足:
  1. 向前兼容（Forward）：旧代码能读新数据
  2. 向后兼容（Backward）：新代码能读旧数据
  3. 二者并存可读写

绝大多数事故来自:
  ❌ 改字段类型 + 代码用了新类型
  ❌ 删字段后立刻用
  ❌ 加 NOT NULL 列没给默认值
```

### 11.2 标准变更流程

```
Step 1: 加字段（NULL 或默认值）
        部署旧代码（不写不读新字段）
        
Step 2: 部署中间代码
        - 读: 同时读新旧
        - 写: 双写新旧
        - 验证一致性
        
Step 3: 数据回填（迁移旧数据到新格式）
        校验数据完整

Step 4: 部署新代码（只读新字段）
        旧字段保留

Step 5: 监控 N 周后清理旧字段
```

### 11.3 工具

| 工具 | 用途 |
|:---|:---|
| **Flyway / Liquibase** | SQL 迁移版本化 |
| **Atlas** | 现代 schema 迁移 |
| **gh-ost / pt-online-schema-change** | MySQL 在线 DDL |
| **pg_repack** | PG 在线 VACUUM |
| **Bytebase** | 数据库 DevOps |
| **SkyWalking BanyanDB / SchemaSpy** | 文档化 |

## 十二、回滚（最后一根稻草）

### 12.1 回滚原则

```
✅ 1 分钟内可执行
✅ 不需要 build / push
✅ 自动 + 一键命令
✅ 全程可观测
✅ 数据回滚有预案

❌ 不要:
  - 现想现做
  - 凌晨 3 点写代码回滚
  - 回滚操作需要 PR Review
```

### 12.2 K8s 回滚

```bash
# 查看 rollout 历史
kubectl rollout history deploy/app
# 回到上一版本
kubectl rollout undo deploy/app
# 回到指定版本
kubectl rollout undo deploy/app --to-revision=3
# Argo Rollouts
kubectl argo rollouts abort app          # 中止当前金丝雀
kubectl argo rollouts undo app          # 回滚
```

### 12.3 GitOps 回滚

```bash
# Git 标准回滚 → Argo CD 自动同步
git revert <bad-commit>
git push origin main
# Argo CD 检测 → 自动 sync → 回滚完成
```

### 12.4 数据回滚（最难）

```
预备:
  ✅ 备份: 上线前 snapshot
  ✅ 双写：旧字段不删除（至少 N 周）
  ✅ 数据库变更与代码解耦发布
  ✅ 灰度期间数据写入可关

灾难场景:
  - 写错数据：从备份 + binlog/wal 回放
  - 数据丢失：Point-in-Time Recovery
  - 跨服务不一致：异步对账修复
```

## 十三、可观测性（部署期间）

### 13.1 必看指标（金丝雀分析）

```
SLO 类:
  - 成功率（HTTP 2xx / 总数）
  - P99 / P95 / P50 延迟
  - 错误率（5xx）

业务类:
  - 下单成功率
  - 支付转化率
  - 关键 API 调用量

系统类:
  - CPU / 内存 / GC
  - 网络 / 磁盘
  - 数据库连接数

依赖类:
  - 下游服务调用错误率
  - 缓存命中率
  - 队列消息堆积
```

### 13.2 自动决策示例

```yaml
analysis:
  metrics:
    - name: success-rate
      threshold: 99           # 必须 >= 99%
    - name: p99
      threshold: 500          # 必须 <= 500ms
    - name: error-budget-burn
      threshold: 14.4         # 不能燃烧速率超 14.4x

每个 step 验证:
  - 通过: 进入下一步
  - 失败: 自动回滚
  - 警告: 人工介入
```

### 13.3 发布仪表盘

```
内容:
  - 当前金丝雀状态（步骤进度）
  - 实时指标对比（新 vs 旧）
  - 关键告警
  - 一键暂停 / 一键回滚 / 一键加速
  - 操作历史 + 审计
```

## 十四、典型坑（生产血泪）

| 坑 | 建议 |
|:---|:---|
| **没有 readiness probe** | 滚动出现 502 |
| **没有 preStop** | 长连接被切 |
| **数据不向后兼容** | 三段式变更 |
| **金丝雀指标没接入** | 必接 Prom + AnalysisTemplate |
| **回滚没人会** | 演练 + 文档 |
| **金丝雀比例太大** | 1% → 10% → 50% |
| **没观察够时间** | 至少 5-30 分钟 |
| **节假日/凌晨发版** | 严格规避业务高峰 |
| **缺少蓝绿/金丝雀工具** | Argo Rollouts 必装 |
| **依赖未准备好** | 依赖也要灰度 |
| **配置变更和代码绑定** | 拆开发布 |
| **缓存未预热** | 上线后请求飙错 |
| **数据库连接池暴击** | 控制并发上限 |
| **Service Mesh 未配** | 流量切分不细 |
| **Flag 没人管** | 治理 + 过期 |
| **没有 chaos 演练** | 季度故障注入 |

## 十五、最佳实践 Checklist

```
准备:
☐ readiness / liveness / startup probes
☐ preStop hook + 优雅退出
☐ resources request/limit
☐ HPA / VPA
☐ PodDisruptionBudget

策略:
☐ 蓝绿 / 金丝雀工具（Argo Rollouts / Flagger）
☐ Service Mesh 流量切分
☐ Feature Flag 平台
☐ 数据库变更三段式
☐ 不可变镜像 + Tag SHA

可观测:
☐ SLO 指标
☐ 业务指标
☐ AnalysisTemplate
☐ 发布仪表盘
☐ 告警自动接入

回滚:
☐ < 1 分钟一键回滚
☐ GitOps Revert 流程
☐ 数据库回滚预案
☐ 定期演练

治理:
☐ 变更窗口（避开高峰）
☐ 发布审批
☐ 发布通告
☐ Flag 生命周期
☐ 月度发布复盘
```

## 十六、工具推荐（2025）

### 16.1 渐进式发布

| 工具 | 特点 | 推荐度 |
|:---|:---|:---:|
| **Argo Rollouts** | 与 Argo CD 一体 | ⭐⭐⭐⭐⭐ |
| **Flagger** | Weaveworks，Mesh 友好 | ⭐⭐⭐⭐ |
| **Spinnaker** | Netflix 老牌 | ⭐⭐⭐ |
| **Ambassador Edge Stack** | API Gateway | ⭐⭐⭐ |
| **Kayenta** | 自动化金丝雀分析 | ⭐⭐⭐ |

### 16.2 Feature Flag

| 工具 | 类型 | 国内 |
|:---|:---|:---:|
| **LaunchDarkly** | 商业 SaaS | ⚠️ |
| **Unleash** | 开源 | ✅ |
| **GrowthBook** | 开源 A/B | ✅ |
| **Flagsmith** | 开源 | ✅ |
| **ConfigCat** | SaaS | ⚠️ |
| **Apollo Config**（携程）| 国产 | ✅ |
| **Nacos**（阿里）| 国产 | ✅ |

### 16.3 数据库变更

| 工具 | 用途 |
|:---|:---|
| **Flyway** | SQL 迁移 |
| **Liquibase** | 跨 DB 迁移 |
| **Atlas** | 现代化迁移 |
| **gh-ost** | MySQL 在线 DDL |
| **Bytebase** | DB DevOps 平台 |

## 十七、推荐组合（按规模）

### 17.1 小团队

```
工具: Argo Rollouts + Argo CD + Prometheus + Unleash
策略: 滚动为主 + 关键服务金丝雀
```

### 17.2 中型团队

```
工具: Argo Rollouts + Istio + Prometheus + Unleash/GrowthBook
策略: 金丝雀主路径 + Feature Flag + 蓝绿（关键）
DB:   Bytebase + Atlas
```

### 17.3 大型团队

```
工具: 自研发布平台 + Argo Rollouts + Istio + LaunchDarkly
策略: 渐进式 + 自动指标决策 + Chaos 演练
平台: Backstage IDP + 发布自服务
```

## 十八、学习路径

```
入门（2 周）:
  1. K8s 滚动更新 + Probes
  2. 优雅退出 + preStop
  3. 第一次蓝绿切换

中级（1 个月）:
  4. Argo Rollouts 金丝雀
  5. Prometheus + AnalysisTemplate
  6. Unleash Feature Flag
  7. 数据库三段式变更

高级（3 个月）:
  8. Istio 流量切分（Header / 用户灰度）
  9. Shadow 测试
  10. Progressive Delivery 全套
  11. 自动回滚机制
  12. Chaos Engineering

专家:
  13. 自研发布平台
  14. 多集群发布编排
  15. 跨业务发布治理
  16. AI 辅助发布决策
```

## 十九、参考资料

```
官方:
  - Argo Rollouts: https://argoproj.github.io/argo-rollouts/
  - Flagger: https://flagger.app/
  - Istio Traffic Management
  - Unleash: https://www.getunleash.io/
  - LaunchDarkly Docs

书:
  - 《Continuous Delivery》(Humble)
  - 《Release It!》(Michael Nygard)
  - 《Site Reliability Engineering》(Google)
  - 《Database Reliability Engineering》

博客:
  - Netflix Tech Blog（金丝雀/Spinnaker）
  - 阿里巴巴中间件博客
  - 字节跳动稳定性建设
  - Martin Fowler: BlueGreenDeployment / FeatureToggle

报告:
  - State of DevOps (DORA)
  - State of Progressive Delivery
```

> 📖 **核心判断**：2025 部署策略已经从"二选一"演进到"组合拳"：**Progressive Delivery = 金丝雀 + Feature Flag + GitOps + 自动指标决策**。**Argo Rollouts + Istio + Prometheus + Unleash** 是国内可落地的黄金组合。最容易翻车的不是策略，而是：**没有 probes、没有优雅退出、数据不兼容、回滚没演练**。把基础四件事做好，再谈进阶——**先做到 1 分钟回滚，再追求 100% 全自动发布**。
