# 最佳实践

> 测试最佳实践 = **测试策略 + 金字塔分层 + 用例规范 + 数据治理 + 环境治理 + CI/CD 多级门禁 + 左移+右移闭环 + Flaky/Quarantine + 性能基线 + 安全门禁 + 缺陷生命周期 + 报告+趋势 + 团队组织 + KPI + Postmortem + 国产合规**。本章把"会用 pytest"升级到"运营企业级 QA 体系"。

## 一、12 项金标准

```
1. ✅ 测试策略 (Strategy) 文档化 + 评审
2. ✅ 金字塔分层 (单元 70% + 集成 20% + E2E 10%)
3. ✅ Hermetic 测试 (无外部依赖, 可独立重跑)
4. ✅ CI 多级门禁 (PR + Merge + Pre-prod + Prod)
5. ✅ 覆盖率门禁 (核心 80% + 业务 60%)
6. ✅ Flaky 治理 (Quarantine + 1% 红线)
7. ✅ 性能基线 (SLO + Burn Rate + 大促演练)
8. ✅ DevSecOps 五件套 (SAST + SCA + DAST + IAST + Fuzzing) CI 强制
9. ✅ 测试数据管理 (脱敏 + Hermetic + Faker)
10. ✅ 缺陷生命周期 + Postmortem
11. ✅ 测试团队组织 + 责任矩阵 (开发负责单元, QA 负责集成+E2E)
12. ✅ KPI (左移率 / 自动化覆盖 / Flaky / MTTR-Bug / 逃逸率)
```

## 二、测试策略（Test Strategy）

```
模板:

# <项目>-测试策略

## 1. 目标 + 范围
- 业务目标 / 用户量级
- 质量目标 (SLO + Bug 阈值)
- 范围 (in / out)

## 2. 测试层次 (金字塔)
- 单元 (Dev 负责, 70%, 覆盖 ≥ 80%)
- 集成 (QA + Dev, 20%, Testcontainers)
- 契约 (Pact)
- E2E (QA, 10%, Playwright)
- 性能 (季度 + 大促)
- 安全 (SAST/SCA/DAST CI)

## 3. 环境
- Dev / Test / Staging / Prod
- 数据策略 (脱敏 + Faker)
- 隔离 (DB per worker)

## 4. 工具链
- 语言: pytest / Jest / JUnit / Go test
- API: Postman / Bruno / Pact
- UI: Playwright / Cypress
- 性能: k6
- 安全: Semgrep / Trivy / ZAP
- 平台: MeterSphere / ReportPortal

## 5. CI/CD 集成
- PR Gate (单元 + 静态 + 覆盖率)
- Merge Gate (集成 + 契约)
- Pre-prod (E2E + 性能基线)
- Prod (Smoke + Synthetic)

## 6. 缺陷管理
- Jira / Tapd workflow
- Severity + Priority
- SLA (Critical 24h)
- Postmortem

## 7. KPI
- 自动化覆盖 > 80%
- 左移率 > 70%
- 逃逸率 < 5%
- Flaky < 1%
- 性能 SLO 100%

## 8. 风险 + Mitigation
- 第三方依赖 → Mock + 契约
- 数据 → Faker + 脱敏
- 时间 → Freezegun / Fake clock

每季度评审 + 更新
```

## 三、金字塔分层 + 责任

```
单元 (70%):
  Owner: 开发 (TDD)
  Tool: pytest / Jest / JUnit / Go test + Mock
  Gate: PR 必通过 + 覆盖率 80%
  Speed: < 30s 全跑

集成 (20%):
  Owner: 开发 + QA
  Tool: Testcontainers + pytest + RestAssured
  Gate: Merge 必通过
  Speed: < 5min

契约 (5%):
  Owner: 开发 (Consumer + Provider)
  Tool: Pact + Broker
  Gate: 跨服务 PR

E2E (5%):
  Owner: QA
  Tool: Playwright + Cypress
  Gate: Pre-prod (定时 + 触发)
  Speed: < 30min

性能:
  Owner: QA + SRE
  Tool: k6 + locust
  频率: 周回归 + 季度大压 + 大促全链路

安全:
  Owner: 开发 + 安全 + QA
  Tool: Semgrep + Trivy + ZAP
  Gate: CI 强制 (Critical/High Block)

探索:
  Owner: QA + Stakeholders
  频率: 每个版本 (Session-Based)
```

## 四、用例规范

```
命名 (3 元素):
  test_<scope>__<scenario>__<expected>
  test_login__valid_creds__redirect_home
  test_payment__insufficient_balance__return_402

结构 (AAA):
  # Arrange
  user = create_user(...)
  # Act
  result = service.login(user)
  # Assert
  assert result.success
  assert result.token

原则:
  ☐ 一个测试一个断言点 (核心)
  ☐ 测试独立 + 顺序无关
  ☐ Hermetic (无外部依赖)
  ☐ 可重复 (随机 seed 固定)
  ☐ 快速 (< 100ms 单元)
  ☐ 自验证 (true/false 明确)
  ☐ 清晰意图 (读测试 = 读规约)
  ☐ Mock 边界 (DB / 网络 / 时间)
  ☐ 命名见即知意

反模式:
  ❌ test_1, test_2 (无意义命名)
  ❌ 长测试 (50+ 行)
  ❌ if/for 在测试里 (写参数化)
  ❌ 共享可变状态
  ❌ Sleep 等待 (用显式 wait)
  ❌ 真实第三方 API
  ❌ 多个无关断言
```

## 五、测试数据管理

```
策略:
  ☐ 静态 fixture (核心场景 / Yaml-JSON)
  ☐ 动态生成 (factory_boy + Faker)
  ☐ Hermetic per test (Testcontainers)
  ☐ 脱敏 (生产 → 测试)
  ☐ 不入 Git: 敏感数据用 Vault / .env.local

工具:
  Faker ⭐ (多语言, 假数据)
  factory_boy / Factory Bot
  fishery (TS)
  mimesis (Python, 高性能)
  Hypothesis (Property-Based)
  Snowfakery (Salesforce)
  Tonic.ai (商业脱敏)

DB 数据:
  - 迁移 (Liquibase / Flyway / Alembic)
  - 种子 (SQL / fixture)
  - 隔离 (Transaction Rollback / DB per worker)

外部依赖 Mock:
  WireMock (Java)
  MockServer
  msw (前端 Service Worker)
  nock (Node)
  vcrpy (Python, 录制回放)
  
红线:
  ❌ 测试依赖生产数据 (易变 + 敏感)
  ❌ 测试间共享 DB 行 (顺序敏感)
  ❌ 真实第三方 (Stripe / Twilio) → 用 Mock / Sandbox
```

## 六、环境治理

```
环境层:
  Dev      开发, 个人 / 团队
  Test     QA 集成
  Staging  Pre-prod, 类生产
  Prod     生产

特征:
  Dev:     快速反馈, Mock 多
  Test:    完整 + Testcontainers + 共享
  Staging: 镜像生产 + 真实数据脱敏
  Prod:    Smoke + Synthetic + Canary

工具:
  K8s 多 namespace / 多集群
  Argo CD GitOps (环境配置版本化)
  Helm + Kustomize (配置)
  ksonnet / Jsonnet (复杂)

数据隔离:
  - 每环境独立 DB
  - Staging 数据 = 生产脱敏快照
  - 不允许跨环境读写

红线:
  ❌ 测试直连生产 DB
  ❌ Staging 无脱敏
  ❌ 共享密码 / Secret
```

## 七、CI/CD 多级门禁

```
PR Gate (~3-5 min):
  ☐ Lint + Format
  ☐ 单元测试 + 覆盖率 > 80%
  ☐ 静态分析 (SonarQube / Semgrep)
  ☐ Secret 扫描 (gitleaks)
  ☐ SCA (Trivy / Snyk, Block Critical)

Merge Gate (~10-15 min):
  ☐ 集成测试 (Testcontainers)
  ☐ 契约测试 (Pact)
  ☐ 构建镜像
  ☐ SAST 深度扫
  ☐ 镜像 SCA (Trivy image)

Pre-prod (~30-60 min):
  ☐ Deploy Staging
  ☐ Smoke E2E (Playwright)
  ☐ 完整 E2E (按需 / nightly)
  ☐ 性能基线 (k6, 对比上版)
  ☐ DAST (ZAP / Nuclei)
  ☐ Chaos 轻量 (Pod Kill 1 个)

Prod Deploy:
  ☐ Canary 5% / 30 min 观察
  ☐ Smoke Prod
  ☐ Synthetic 24/7
  ☐ 错误率 < 0.1% → 全量
  ☐ 否则自动 Rollback

工具:
  GitHub Actions ⭐ / GitLab CI / Jenkins
  Argo Rollouts (灰度)
  Datadog CI Visibility
```

## 八、Flaky 治理

```
检测:
  - CI 重跑统计
  - 历史失败率
  - Datadog Flaky Detection
  - Launchable

处理:
  1. 自动标记 (3 次 / 7 天间歇失败)
  2. Quarantine (跳过 + 单独追踪)
  3. JIRA Ticket + Owner
  4. 修复 SLA: 7 天 (Critical 模块)
  5. KPI: Flaky 率 < 1%

修复:
  - 替换 sleep → 显式 wait
  - Mock 外部
  - 数据隔离 (random uuid)
  - 端口随机
  - 时间冻结 (Freezegun)
  - 并发安全

红线:
  ❌ 不修, 直接重试 (技术债)
  ❌ 关闭测试 (覆盖率掉)
  ❌ 没人 owner

工具:
  pytest-rerunfailures (慎用 + 标记)
  flaky (Python)
  Launchable
  Trunk Flaky Tests
  Datadog
```

## 九、性能基线

```
基线建立:
  ☐ 每接口 P50/P95/P99 基线
  ☐ 历史 30 天平均 + 偏差
  ☐ 大促前重设 (业务变化)

回归:
  ☐ 周回归 (主要场景, 30 min)
  ☐ PR 性能影响 (核心场景, 5 min)
  ☐ 大促前全链路 (周 / 月)

告警:
  ☐ P99 退化 > 20% → 告警
  ☐ QPS 下降 > 10% → 告警
  ☐ 错误率 > 0.5% → 阻塞

工具:
  k6 ⭐ + InfluxDB + Grafana
  阿里 PTS (全链路)
  JMeter + JMeterDsl
  Locust + InfluxDB

SLO:
  Tier 1: P99 < 200ms / 99.95%
  Tier 2: P99 < 500ms / 99.9%
  Tier 3: P99 < 1s / 99%

详见 [16_故障排查/04_最佳实践](../../16_故障排查/04_最佳实践/README.md) SLO 章节。
```

## 十、安全门禁

```
CI 强制:
  ☐ SAST: SonarQube + Semgrep (Critical Block)
  ☐ SCA: Trivy + Snyk (Critical Block)
  ☐ Secret: gitleaks (Block any)
  ☐ Container: Trivy image (Critical Block)
  ☐ License: FOSSA / ScanCode (合规)

Pre-prod:
  ☐ DAST: ZAP / Nuclei
  ☐ IAST: Contrast (Java) / Seeker
  ☐ Authentication / Authorization 矩阵

定期:
  ☐ 季度渗透 (内 / 外)
  ☐ 年度第三方
  ☐ HW 行动 重保

详见 [14_安全](../../14_安全/index.md) DevSecOps 章节。
```

## 十一、缺陷生命周期

```
工作流:
  Open → Triage → Assigned → InProgress
        → Resolved → Verified → Closed
        → Rejected / Duplicate
        → Reopened

Triage SLA:
  Critical: 1h
  High:     4h
  Medium:   1d
  Low:      3d

修复 SLA:
  Critical: 24h
  High:     7d
  Medium:   30d
  Low:      90d

模板必填:
  ☐ 标题 (现象 + 模块)
  ☐ 严重度 + 优先级
  ☐ 环境 (OS + 版本 + 配置)
  ☐ 步骤 (1, 2, 3)
  ☐ 预期 vs 实际
  ☐ 截图 / 日志 / 视频 / HAR
  ☐ 受影响版本
  ☐ 关联需求 / 测试用例

工具:
  Jira ⭐ + Xray + Zephyr
  Tapd / PingCode / Teambition (国产)
  Linear (现代)
  GitHub Issues + Projects
  禅道 (国产, 开源)
```

## 十二、报告 + 趋势

```
即时报告:
  Allure ⭐ (单次)
  ReportPortal ⭐ (聚合 + AI)
  Datadog CI / Launchable
  Cypress Cloud
  Currents

KPI 看板:
  ☐ 通过率 (按层 / 按模块)
  ☐ 覆盖率趋势
  ☐ Flaky 率
  ☐ 平均执行时间
  ☐ 缺陷数 + 严重度分布
  ☐ 缺陷修复时长
  ☐ 逃逸率 (生产 Bug / 总 Bug)
  ☐ 自动化覆盖

通知:
  - CI 失败 → 飞书 / 钉钉 群 + @owner
  - 性能退化 → 报告
  - 安全 Critical → 安全群 + IR

工具:
  Grafana + Prometheus
  阿里 ARMS
  自研 (LLM 加持归因)
```

## 十三、左移+右移闭环

```
左移:
  需求评审 (测试代表)
  设计评审 (可测性)
  TDD / ATDD
  契约测试
  单元 PR 门禁
  Code Review by QA
  
右移:
  Feature Flag
  Canary / Blue-Green
  A/B Testing
  Synthetic Monitoring
  RUM (前端真实)
  Sentry / Bugsnag
  生产错误率回流到 Test
  
闭环:
  生产 Bug → Postmortem → 新增回归用例 → 改进监控

KPI:
  ☐ 需求阶段缺陷率 > 30%
  ☐ Pre-prod 缺陷率 > 50%
  ☐ Prod 逃逸率 < 5%
```

## 十四、Postmortem

```
触发:
  - 生产 P0/P1 Bug
  - 重大测试漏过
  - 大规模回归失败
  - 安全事件
  
模板:
  - 时间线
  - 影响 (用户 / 业务 / 时长)
  - 根因 (5 Whys)
  - 测试漏点分析
  - Action: 加用例 / 改流程 / 工具改进
  - Owner + Deadline
  
跟踪:
  Action 闭环率 > 80%
  类似 Bug 是否复现 (季度)

详见 [16_故障排查/04_最佳实践](../../16_故障排查/04_最佳实践/README.md) Postmortem 章节。
```

## 十五、团队组织

```
小型 (10-50 人):
  QA Lead 1 + QA 2-3
  开发负责单元
  Lead 制定策略
  全员 E2E + 探索

中型 (100-500 人):
  QA Director
  按业务线 QA 团队 (3-5 人)
  平台 QA (2-3, 工具 / CI)
  性能 + 安全专项 (1-2)
  Test Architect (1)

大型 (1000+):
  VP Quality
  按业务线 QA 总监
  专项: 性能 / 安全 / 移动 / AI / 自动化
  Quality Engineering Lab (R&D)
  Tools / Platform 团队

岗位:
  L1: Junior QA (手工 + 入门自动化)
  L2: QA Engineer (自动化 + API)
  L3: Senior QA (架构 + 工具)
  L4: Test Architect (策略 + 平台)
  L5: Distinguished QE (跨团队 + AI 趋势)

核心能力 (L3+):
  - 编程 (Python / Java / Go / TS)
  - 自动化全栈 (API + UI + 性能 + 安全)
  - CI/CD + K8s
  - 测试理论 + 用例设计
  - 工具开发 + 平台
```

## 十六、KPI + 度量

```
质量 (核心):
☐ 生产逃逸率 < 5%
☐ Critical Bug = 0 / 季度
☐ 客户报告 Bug < 10 / 月
☐ NPS > 50

自动化:
☐ 单元覆盖率 > 80% (核心)
☐ E2E 自动化率 > 80%
☐ CI Gate 通过率 > 95%
☐ Flaky 率 < 1%

效率:
☐ PR 反馈 < 5 min
☐ Pre-prod 反馈 < 60 min
☐ 缺陷修复 SLA 达成 > 90%
☐ 自动化执行时长 (周对比)

左移:
☐ 需求阶段缺陷率 > 30%
☐ Pre-prod 缺陷率 > 50%
☐ Code Review 缺陷率

团队:
☐ QA / 开发比 (1:5 - 1:10)
☐ 培训完成率
☐ 工具采纳率

安全:
☐ SAST/SCA 通过率
☐ 安全 Bug 修复 SLA
☐ 季度渗透 0 Critical
```

## 十七、国产合规

```
等保:
  ☐ 等保 2 (一般)
  ☐ 等保 3 (重要)
  ☐ 关基 (国家级)
  
密评:
  ☐ 商用密码应用安全性评估
  ☐ 国密 SM2/3/4 实测

资质:
  ☐ CISP-PTE (渗透)
  ☐ CISP (信安)
  ☐ ISTQB / CSTE (测试)
  ☐ 软件评测师

HW 行动:
  ☐ 重保模式
  ☐ 安全回归 + 红蓝演练

信创:
  ☐ 兼容性矩阵 (鲲鹏/麒麟/UOS)
  ☐ TiDB / OceanBase / GaussDB
  ☐ 国密 + 等保 3 双重
```

## 十八、典型生产架构

### 18.1 中型互联网 (1000 人)

```
QA 团队: 30 人 (20 业务 + 5 平台 + 3 专项 + 2 Architect)
平台:        MeterSphere + 自研 (LLM 加持)
工具:        pytest + Playwright + k6 + Pact + Trivy + Semgrep
CI:         GitHub Actions / GitLab CI
报告:        Allure + ReportPortal AI
SRE:        Argo Rollouts + Sentry + Grafana
合规:        等保 2 + DevSecOps + 密评 (按需)
KPI:         自动化覆盖 85% + Flaky < 0.5% + 逃逸率 < 3%
```

### 18.2 央企信创关基

```
QA 团队: 50 人 (按业务线 + 信创专项 + 安全专项)
平台:        自研 + MeterSphere + 国产 (代码卫士 / 长亭)
工具:        pytest + Playwright + JMeter + 阿里 PTS + 雷池 + 奇安信
基建:        鲲鹏 + 麒麟 + openEuler 测试环境
DB:         TiDB + OceanBase + GaussDB 兼容矩阵
国密:        SM2/3/4 实测
等保:        3 级 + 关基 + 密评 + HW
HW:         季度演练 + 重保模式
KPI:         自动化覆盖 70% + 安全 Critical = 0 + 等保通过 100%
```

## 十九、推荐栈（最佳实践）

```
策略:        Test Strategy 文档 + 季度评审
分层:        70/20/10 + Hermetic
单元:        pytest ⭐ / Jest / JUnit / Go test
集成:        Testcontainers ⭐
契约:        Pact ⭐
E2E:        Playwright ⭐
性能:        k6 ⭐ + JMeter + 阿里 PTS (全链路)
安全:        Semgrep + Trivy + ZAP + gitleaks ⭐ (CI 强制)
移动:        WeTest + Appium + Maestro
平台:        MeterSphere ⭐ + 自研 + LLM 加持
报告:        Allure + ReportPortal ⭐ + Grafana
数据:        Faker + factory_boy + Vault
环境:        K8s + Argo CD + 多 namespace
CI:         GitHub Actions / GitLab CI / Jenkins + 多级门禁
监控:        Sentry + Datadog Synthetics + RUM
Flaky:      Quarantine + Launchable
缺陷:        Jira + Tapd + 禅道
左移:        TDD + SonarQube + Code Review
右移:        Feature Flag + Argo Rollouts + Synthetic
Chaos:      Chaos Mesh + ChaosBlade (季度 GameDay)
AI:         GitHub Copilot + Codium AI + Testim / Mabl (按需)
合规:        等保 + 密评 + 信创 + HW
团队:        QA / Dev = 1:5 (业务) - 1:10 (基础设施)
KPI:         逃逸率 < 5% + 自动化 > 80% + Flaky < 1% + SLO 100%
```

> 📖 **核心判断**：测试最佳实践 = **12 项金标 + Test Strategy 文档 + 金字塔分层(70/20/10) + Hermetic 用例 + CI 多级门禁(PR/Merge/Pre-prod/Prod) + 覆盖率 + Flaky < 1% + 性能基线 + DevSecOps 五件套 + 缺陷 SLA + Postmortem + 左移+右移闭环 + 团队组织 + KPI + 国产合规(等保/密评/信创/HW)**。能给央企/大型互联网搭"MeterSphere + pytest + Playwright + k6 + Pact + Semgrep + Trivy + Argo Rollouts + Allure + Chaos Mesh + LLM 加持"完整测试体系, 落地从需求→单元→集成→契约→E2E→性能→安全→Synthetic→Postmortem 全流程, 就具备 QA Director / Test Architect 能力。
