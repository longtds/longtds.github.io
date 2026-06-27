# 高级

> 测试高级 = **大规模 CI 测试编排 + 测试平台化 + 测试左移右移 + 全链路压测(影子流量/影子库) + Chaos 测试(Chaos Mesh) + 安全测试(SAST/DAST/SCA/IAST/Fuzzing) + 移动专项(性能/兼容/弱网/电量) + AI 加持(LLM 用例生成/AI 自愈/AI 报告) + AI/LLM 模型测试(评估/红队/MLOps) + Property-Based Testing + Mutation Testing + 数据驱动 + 国产化合规测试 + 多端兼容(浏览器/小程序/鸿蒙)**。本章面向测试架构师 / 质量平台负责人。

## 一、CI 测试编排（大规模）

```
挑战:
  - 万级用例 + 分钟级反馈
  - 多语言 + 多端
  - 分布式执行
  - 数据隔离
  - 报告聚合
  - 缓存 + 选择性测试

架构:
  Test Selector → Scheduler → Worker Pool → Reporter
  
工具:
  Bazel ⭐ (Google, 精确依赖 + 测试选择)
  Buck2 (Meta)
  Nx / Turborepo (前端 monorepo)
  Pants (Python)
  
选择性测试 (Selective Testing):
  - 文件变更 → 影响的测试
  - 历史失败率
  - 风险评分
  
执行:
  K8s Job + Argo Workflows
  Tekton Pipelines
  Buildkite
  CircleCI Test Splitting
  Datadog CI Test Optimization (商业)

报告聚合:
  Allure Server
  ReportPortal ⭐ (开源, AI 加持)
  TestQuality
  Currents (Cypress 商业)
```

## 二、测试平台化

```
功能:
  - 用例管理 (CRUD + Tag + 关联需求)
  - 数据管理 (mock / fixture)
  - 执行调度 (定时 + 触发)
  - 报告 + 趋势
  - 缺陷集成 (Jira / Tapd)
  - CI/CD 集成
  - 多角色 (RBAC)
  - 通知 (钉钉 / 飞书 / Slack)
  - AI 加持 (用例生成 / 失败归因)

开源:
  MeterSphere ⭐ (国产, 一体化) 
  HttpRunner / HRP (国产, 接口)
  Apifox (国产, Postman 替代)
  ReportPortal (开源报告)
  Cypress Cloud (商业)
  
商业:
  TestRail / Zephyr / Xray / qTest
  PractiTest / Tricentis / SauceLabs
  
自研:
  - 中大厂普遍
  - 平台中台化
  - LLM 加持新趋势
```

## 三、测试左移（Shift-Left）

```
理念:
  缺陷越早发现, 修复成本越低 (1:10:100)
  测试参与: 需求 → 设计 → 编码 → 提测

实践:
  ☐ 需求评审 (测试代表参与)
  ☐ 设计评审 (可测性 / API 契约)
  ☐ 用例先行 (TDD / ATDD)
  ☐ 单元覆盖 PR 门禁
  ☐ 契约测试 (开发 + 测试)
  ☐ Pair Programming (开发 + QA)
  ☐ 静态分析 (SAST 入 CI)
  ☐ Code Review by QA
  ☐ Dev Test 责任 (开发负责单元)
  
工具:
  SonarQube ⭐ (代码质量 + SAST + 覆盖率)
  Checkstyle / SpotBugs (Java)
  ESLint + TypeScript (JS)
  Black + Ruff + Mypy (Python)
  golangci-lint (Go)
  
KPI:
  Pre-prod Bug 占比 > 70% (越早越好)
  生产 Bug 数 (越少越好)
  RCA 阶段分布 (找漏点)
```

## 四、测试右移（Shift-Right）

```
理念:
  生产是终极测试场景
  Observability + 灰度 + 回滚

实践:
  ☐ Feature Flag (LaunchDarkly / GrowthBook)
  ☐ Canary / Blue-Green (Argo Rollouts)
  ☐ A/B Testing
  ☐ Chaos Engineering (Chaos Mesh)
  ☐ Synthetic Monitoring (合成监控)
  ☐ Real User Monitoring (RUM) + Sentry
  ☐ 错误告警 (Sentry / Bugsnag)
  ☐ 灰度看板
  
工具:
  LaunchDarkly / GrowthBook (Feature Flag)
  Argo Rollouts / Flagger (灰度)
  Optimizely (A/B)
  Sentry / Datadog RUM (前端错误)
  Datadog Synthetics / Checkly
  Grafana Synthetic Monitoring
  
联动:
  - Pre-prod E2E 通过 → 部署 Canary
  - Canary 错误率 < 0.1% → 全量
  - 错误率 > 阈值 → 自动回滚
```

## 五、全链路压测

```
背景:
  双 11 / 春运 / 高考 / 黑五 流量预期 10-100x
  线下压测 ≠ 生产实际
  
方案 (阿里 / 美团 / 字节):
  - 影子流量 (生产真实流量 + 标识)
  - 影子库 / 影子表 (写隔离)
  - 影子中间件 (Redis / Kafka)
  - 流量录制 + 回放 + 改写

工具:
  阿里 PTS ⭐
  字节 ByteBase 全链路 (内部)
  美团 Quake (内部)
  
开源:
  TakinTalos (国产, 基于阿里 PTS 思路)
  ChaosBlade (压测 + 故障注入)
  
核心技术:
  - Agent 注入 (字节码) → 流量染色
  - 中间件改造 → 影子路由
  - Mock 第三方 (避免影响外部)
  - 数据自动清理

流程:
  1. 压测目标 (10x 流量 / SLO 验证)
  2. 数据准备 (脱敏 + 染色)
  3. 影子环境验证
  4. 演练 (低峰 / 凌晨)
  5. 报告 + 容量调整
```

## 六、Chaos 测试（韧性）

```
工具:
  Chaos Mesh ⭐ (CNCF)
  ChaosBlade ⭐ (阿里)
  Litmus (CNCF)
  Gremlin (商业)
  
故障类型:
  - Pod Kill / 网络分区 / 延迟 / 丢包
  - CPU / 内存 / 磁盘 / IO
  - DB 主备切换 / 中间件故障
  - K8s 节点故障 / AZ 故障
  - 时钟漂移

场景:
  - Pre-prod 自动化 (CI 集成)
  - 生产 GameDay (季度)
  - 演练 SLO / RTO / RPO

详见 [16_故障排查/04_最佳实践](../../16_故障排查/04_最佳实践/README.md) Chaos 章节。
```

## 七、安全测试（DevSecOps）

```
SAST (静态):
  SonarQube + Security Hotspots
  Snyk Code
  Semgrep ⭐ (开源, 规则丰富)
  CodeQL (GitHub)
  Checkmarx / Fortify (商业)
  奇安信代码卫士 (国产)

SCA (依赖):
  Snyk
  Dependabot (GitHub)
  Renovate
  OWASP Dependency-Check
  Trivy ⭐ (镜像 + 依赖)
  Grype

DAST (动态):
  OWASP ZAP ⭐
  Burp Suite Pro
  Nuclei ⭐ (templates 海量)
  长亭雷池 / Acunetix

IAST (混合):
  Contrast Security
  Synopsys Seeker
  
Fuzzing:
  AFL++ ⭐ / libFuzzer / Honggfuzz
  Atheris (Python)
  go-fuzz / Native fuzzing (Go 1.18+)
  Jazzer (JVM)
  OSS-Fuzz (Google, 开源项目)

Secret 扫描:
  gitleaks ⭐
  trufflehog
  detect-secrets
  
容器:
  Trivy / Grype / Clair / Anchore
  CIS Docker Benchmark
  
集成:
  CI 阶段强制 (Critical/High Block)
  IDE 实时 (SonarLint / Snyk plugin)
  PR 报告评论

详见 [14_安全](../../14_安全/index.md) DevSecOps 章节。
```

## 八、移动专项

### 8.1 性能

```
指标:
  启动时间 (冷启 / 热启)
  内存峰值 + 泄漏
  CPU 占用
  电量 (mAh / hour)
  网络 (流量 + 时延)
  帧率 (FPS / 卡顿率)
  ANR / Crash

Android:
  Profiler (Android Studio) ⭐
  Perfetto + Systrace
  GameBench
  Solopi (蚂蚁开源)

iOS:
  Instruments (Xcode) ⭐
  Time Profiler / Allocations / Leaks
  MetricKit (运行时)
  
跨平台:
  WeTest (腾讯)
  Solopi
  Newrelic Mobile / Sentry Mobile
  阿里云 EMAS / 华为 AppGallery Connect
```

### 8.2 兼容性

```
维度:
  OS 版本
  分辨率 + 屏幕密度
  CPU 架构 (ARM v7/v8/x86)
  RAM 大小
  网络 (2G/3G/4G/5G/WiFi)
  厂商定制 (MIUI / EMUI / OriginOS / OneUI)

云测平台:
  WeTest (腾讯) ⭐
  TestBird
  华为 DevTesting
  阿里 MQC
  Sauce Labs / BrowserStack (国际)
  
自动化:
  Appium 多机
  Maestro (YAML)
```

### 8.3 弱网测试

```
工具:
  Network Link Conditioner (iOS / macOS)
  Charles + Throttle
  Atc (Facebook)
  TC (Linux)
  Clumsy (Windows)
  WeTest 弱网模拟

场景:
  延迟 200ms+ / 丢包 10%+ / 带宽 < 100kbps
  网络切换 (WiFi ↔ 4G)
  飞行模式 / 信号弱
```

### 8.4 电量+温度

```
Android:
  Battery Historian (Google)
  GameBench
  
iOS:
  Instruments → Energy Log

阈值:
  待机 1h 电量 < 1%
  视频 1h < 15%
  游戏 1h < 25%
```

### 8.5 鸿蒙 / 国产

```
HarmonyOS:
  DevEco Testing
  ArkUI 测试
  HUAWEI DevEco Service

小程序:
  微信小程序自动化 (mini-program-automator) ⭐
  支付宝 / 抖音 / 百度
  Playwright + 小程序
  WeTest 小程序云测

车载:
  车机 (鸿蒙座舱 / 银河 / Apollo)
  CarPlay / Android Auto
```

## 九、AI 加持测试

### 9.1 LLM 用例生成

```
能力:
  代码 → 单元用例 (GitHub Copilot / Cursor / CodeWhisperer)
  需求 → 用例 (LLM + 知识库)
  接口文档 → 接口用例 (Swagger → 自动化)
  Bug → 回归用例

工具:
  GitHub Copilot Chat ⭐
  Cursor (强 AI IDE)
  Codium AI / CodiumAI
  Diffblue Cover (Java 单元)
  Tabnine
  阿里通义灵码
  
研究:
  ChatUniTest (基于 GPT)
  CodeT (Microsoft)
  TestPilot
  AthenaTest

5 年判断:
✅ LLM 单元生成普及 (2026-2027)
✅ 端到端用例生成 (2027-2028)
```

### 9.2 AI 自愈 (Self-Healing)

```
能力:
  - UI 定位失败 → AI 找替代
  - 数据变化 → AI 调整断言
  - 元素重命名 → AI 学习
  
工具:
  Testim ⭐ (商业, AI 自愈龙头)
  Mabl (商业)
  Functionize
  Applitools (视觉 AI)
  Playwright AI (新)
  TestSigma
  
中国:
  阿里通义 + 自研
  字节 / 美团 内部

5 年判断:
✅ AI 自愈大幅降低 Flaky (2026-2028)
✅ 商业 → 开源工具兴起
```

### 9.3 AI 测试报告 + 归因

```
能力:
  - 失败聚类 (相似根因)
  - 历史关联 (类似 Bug)
  - 优先级建议
  - 修复建议 (LLM)

工具:
  ReportPortal ⭐ (AI 加持)
  Datadog CI Visibility
  Launchable (AI 测试选择)
  Sealights
```

### 9.4 AI 探索性测试

```
理念:
  AI 像测试新手 → 自由探索 → 发现 Bug
  
工具:
  Test.ai
  Functionize
  研究: GPT-4V (视觉) + Playwright
  
5 年判断:
✅ 视觉 AI Agent 测试 (2027-2029)
```

## 十、AI / LLM 模型测试

### 10.1 模型评估

```
工具:
  lm-eval-harness ⭐ (Eleuther AI)
  HELM (Stanford)
  OpenCompass (上海 AI Lab, 国产 ⭐)
  FlagEval (智源)
  big-bench
  
评测:
  - 通用能力 (MMLU / GSM8K / ARC / HellaSwag)
  - 代码 (HumanEval / MBPP / LiveCodeBench)
  - 数学 (MATH / AIME)
  - 中文 (C-Eval ⭐ / CMMLU / SuperCLUE)
  - 推理 (BBH / GPQA)
  - 多模态 (MMMU / MMBench)

详见 [11_AI 基础设施](../../11_AI基础设施/index.md) 评估章节。
```

### 10.2 LLM 红队 / 安全测试

```
工具:
  Garak ⭐ (Nvidia)
  PyRIT ⭐ (Microsoft)
  Promptfoo
  llm-guard
  HouYi

测试:
  - Prompt Injection
  - Jailbreak
  - Data Poisoning
  - Bias (公平性)
  - Hallucination 率
  - Tool / Agent 安全
  - System Prompt 泄露

详见 [15_渗透测试/03_高级](../../15_渗透测试/03_高级/README.md) AI 红队章节。
```

### 10.3 MLOps 测试

```
数据测试:
  Great Expectations ⭐
  Soda Core
  Deepchecks (数据 + 模型)
  TFX Data Validation

模型测试:
  - 单元 (数据预处理 / 后处理)
  - 集成 (训练 pipeline)
  - 性能基线 (QPS / 时延)
  - A/B (新版 vs 旧)
  - Drift Detection (Evidently AI)
  - 公平性 (Fairlearn)

监控:
  Evidently AI ⭐
  WhyLabs
  Arize
  Fiddler
  阿里 PAI 监控

详见 [12_AIOps](../../12_AIOps/index.md) MLOps 章节。
```

## 十一、Property-Based Testing

```
理念:
  从断言"个例" → 断言"性质"
  框架自动生成 N 组输入

工具:
  Hypothesis ⭐ (Python)
  QuickCheck (Haskell / 全语言移植)
  jqwik (Java)
  fast-check (JS/TS)
  Proptest (Rust)
  ScalaCheck

示例 (Python Hypothesis):

from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)

@given(st.integers(), st.integers())
def test_add_commutative(a, b):
    assert add(a, b) == add(b, a)

收益:
  - 发现边界 (空 / 极端值 / Unicode)
  - 文档化性质
  - 减少手写用例

经典案例:
  AWS S3 (Property-Based 找一致性 Bug)
  TigerBeetle DB (大量 Property + Simulation)
```

## 十二、Mutation Testing

```
理念:
  改代码 (mutant) → 跑测试
  测试没挂 = 测试不够强 ⚠️
  
工具:
  Pitest (Java) ⭐
  mutmut (Python)
  Stryker (JS/TS/.NET) ⭐
  go-mutesting (Go)
  Mull (C/C++)

KPI:
  Mutation Score (杀掉变异 / 总变异)
  Core 库 > 70%
  
案例:
  Google + Facebook 在核心模块用
  比覆盖率更真实
```

## 十三、数据驱动 + 探索性

```
数据驱动:
  CSV / Excel / JSON / DB → 用例参数
  pytest @parametrize
  Jest test.each
  JUnit @ParameterizedTest
  
探索性测试:
  Session-Based (60-90 min 时段)
  Charter (任务定义)
  记录 + 反馈
  
工具:
  Rapid Reporter (老)
  TestBuddy
  自建 (Notion + Loom 录屏)
```

## 十四、国产化合规

```
等保测评:
  - 安全测试 + 资质 (CISP-PTE)
  - 报告 (公安部备案)

关基:
  - 国家关键信息基础设施
  - 强制年度测试

密评:
  - 商用密码应用安全性评估
  - 国密 SM2/3/4 实测
  
信创:
  - 鲲鹏 + 麒麟 + UOS + openEuler 兼容
  - TiDB / OceanBase / GaussDB
  - 测试机柜专用 (内网)
  - 厂商联调

工具:
  长亭雷池 / 安恒 / 绿盟
  奇安信代码卫士 / 安博通 / 启明
  CISP-PTE 体系
```

## 十五、多端兼容

```
浏览器:
  Chrome / Firefox / Safari / Edge / Opera
  国产: 360 / QQ / UC / 搜狗 / 红芯
  WebKit / Blink / Gecko 三大引擎
  
工具:
  BrowserStack / Sauce Labs ⭐
  LambdaTest
  CrossBrowserTesting
  Playwright + Selenium Grid

小程序:
  微信 / 支付宝 / 抖音 / 百度 / 京东 / 美团 / 钉钉 / 飞书
  Taro / uni-app 框架兼容
  
跨端框架:
  Flutter (Web/Mobile/Desktop) → flutter_driver / Maestro
  React Native → Detox / Maestro
  Tauri (Desktop) → 自研
  Electron → Playwright + Spectron
```

## 十六、Checklist（高级）

```
CI 编排:
☐ Bazel / Buck2 选择性测试
☐ K8s Job + Argo
☐ ReportPortal 聚合

平台:
☐ MeterSphere / HttpRunner / 自建
☐ RBAC + 通知 + 仪表盘

左移:
☐ SonarQube ⭐ + 静态分析
☐ TDD + 单元 PR 门禁
☐ 契约测试

右移:
☐ Feature Flag + Canary
☐ Synthetic + RUM
☐ Argo Rollouts

全链路压测:
☐ 影子流量 + 影子库 + 阿里 PTS
☐ 双 11 / 春运 / 大促演练

Chaos:
☐ Chaos Mesh + ChaosBlade
☐ GameDay 季度

安全:
☐ SAST + SCA + DAST + IAST + Fuzzing
☐ Trivy + Semgrep + ZAP + Burp + gitleaks
☐ CI 强制门禁

移动:
☐ 启动 + 内存 + 帧率 + 电量
☐ 兼容 + 弱网 + 鸿蒙 + 小程序

AI:
☐ Copilot + Codium AI 用例生成
☐ Testim / Mabl AI 自愈
☐ ReportPortal AI 归因
☐ Launchable 选择性测试

LLM 模型:
☐ lm-eval / OpenCompass ⭐
☐ Garak + PyRIT 红队
☐ Great Expectations 数据
☐ Evidently AI 监控

Property/Mutation:
☐ Hypothesis ⭐
☐ Pitest + Stryker
☐ Mutation Score > 70%

国产合规:
☐ 等保 / 关基 / 密评
☐ 信创 + 国密
☐ 长亭 / 奇安信

兼容:
☐ BrowserStack / WeTest
☐ 小程序 + Flutter / RN
```

## 十七、推荐栈（高级）

```
CI 编排:    Bazel + Argo + Tekton + Buildkite
平台:        MeterSphere ⭐ + 自研中台
左移:        SonarQube ⭐ + Semgrep + golangci-lint + SonarLint
右移:        LaunchDarkly + Argo Rollouts + Sentry + Datadog RUM
全链路:     阿里 PTS + TakinTalos + 自研
Chaos:      Chaos Mesh ⭐ + ChaosBlade ⭐ + Litmus
SAST:       Semgrep + CodeQL + SonarQube + 长亭/奇安信
SCA:        Trivy ⭐ + Snyk + Dependabot
DAST:       ZAP + Nuclei + 雷池
IAST:       Contrast + Seeker
Fuzz:       AFL++ + libFuzzer + Atheris + go-fuzz
Secret:     gitleaks + trufflehog
移动:        WeTest ⭐ + Solopi + Appium + Maestro
AI 加持:    GitHub Copilot ⭐ + Codium AI + Testim + ReportPortal AI
LLM 模型:   lm-eval + OpenCompass ⭐ + Garak + Evidently + Great Expectations
Property:   Hypothesis ⭐ + jqwik + fast-check
Mutation:   Pitest + Stryker ⭐ + mutmut
合规:        等保 + 关基 + 密评 + 长亭 / 奇安信
兼容:        BrowserStack + WeTest + 小程序云测
报告:        Allure ⭐ + ReportPortal ⭐ + Datadog CI
```

> 📖 **核心判断**：测试高级 = **CI 编排(Bazel/选择性) + 平台化(MeterSphere) + 左移(SonarQube+TDD) + 右移(Feature Flag+Synthetic) + 全链路压测(影子+PTS) + Chaos(Chaos Mesh) + DevSecOps 五件套(SAST/SCA/DAST/IAST/Fuzz) + 移动专项(性能/兼容/弱网/鸿蒙) + AI 加持(Copilot 生成/Testim 自愈/AI 归因) + LLM 模型测试(OpenCompass/Garak/Evidently) + Property/Mutation Testing + 国产合规(等保/密评) + 多端兼容**。能给央企/大型互联网搭"测试中台 + DevSecOps + 全链路压测 + Chaos + AI + LLM 测试"完整体系, 就具备测试架构师/质量平台负责人能力。
