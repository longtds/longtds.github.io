# 17. 测试

> 软件测试 = 质量保证的核心。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，覆盖测试金字塔 + xUnit + Mock + 覆盖率 + TDD/BDD + API/UI/移动 + 性能 + 契约 + DB + 安全 + Chaos + 平台化 + LLM 模型测试 + AI 加持 + DevSecOps + 信创合规 16 大主线，是研发质量的兜底章节。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入门 | 测试金字塔 + 四象限 + xUnit(JUnit/pytest/Go test/Jest) + Mock(Mockito/mock) + 覆盖率(JaCoCo/coverage) + TDD/BDD + 用例设计(等价类/边界值) + Selenium 入门 + Bug 生命周期 + 20 题 |
| [02_进阶](02_进阶/README.md) | 自动化负责人 | API(REST/GraphQL/gRPC + Bruno/Pact) + UI(Playwright/Cypress + POM) + 移动(Appium/Maestro) + 性能(k6/JMeter/locust) + DB(Testcontainers) + CI 集成 + Allure + Flaky 治理 + 国产化 |
| [03_高级](03_高级/README.md) | 测试架构师 | 大规模 CI(Bazel) + 平台化(MeterSphere) + 左移+右移 + 全链路压测(影子) + Chaos + DevSecOps(SAST/SCA/DAST/IAST/Fuzz) + 移动专项 + AI 加持 + LLM 模型测试 + Property/Mutation |
| [04_最佳实践](04_最佳实践/README.md) | QA Director | 12 金标 + Test Strategy + 金字塔 70/20/10 + Hermetic + CI 多级门禁 + Flaky < 1% + 性能基线 + DevSecOps 强制 + 缺陷 SLA + Postmortem + 团队组织 + KPI + 国产合规 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | LLM 用例生成 + AI 自愈 + AI Agent 探索 + LLM 模型测试单工种 + Continuous + Production Testing + Shift-Left 极致 + 信创+鸿蒙+小程序 + Sovereign + PQC + 24 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
  └─ 01_基础: xUnit + Mock + 覆盖率 + TDD/BDD + 用例设计 + 20 题

进阶（3-12 月）
  └─ 02_进阶: API + Playwright + k6 + Pact + Testcontainers + CI + Allure

高级（1-2 年）
  └─ 03_高级: Bazel + 平台化 + 全链路 + Chaos + DevSecOps + AI 加持 + LLM 测试

工程化（2-3 年）
  └─ 04_最佳实践: Strategy + 多级门禁 + Flaky < 1% + KPI + 团队 + 合规

展望（持续）
  └─ 99_发展与展望: LLM Agent + AI 自愈 + Production Testing + Sovereign
```

## 核心判断

```
心法:
  1. 测试是设计活动, 不是事后检查
  2. 金字塔分层 (单元 70% + 集成 20% + E2E 10%)
  3. Hermetic 测试 (独立 + 可重跑)
  4. CI 多级门禁 (PR + Merge + Pre-prod + Prod)
  5. Flaky < 1% 红线
  6. DevSecOps 五件套必修
  7. 左移+右移闭环
  8. AI 加持是分水岭 (Copilot + Codium)
  9. LLM 模型测试 单独工种
  10. 国产合规 (等保 / 关基 / HW / 密评)
  11. Continuous + Production Testing 替代阶段化
  12. 不学 AI + Cloud 5 年内淘汰

红线:
  ❌ 测试金字塔倒置 (E2E 多, 单元少)
  ❌ Flaky 不修, 只重试
  ❌ 覆盖率作为唯一 KPI (无 Mutation)
  ❌ 测试依赖生产 DB
  ❌ 真实第三方 API (Stripe / Twilio) → 用 Sandbox/Mock
  ❌ 缺乏 Test Strategy
  ❌ 安全测试不入 CI 强制
  ❌ 性能测试只在大促前
  ❌ Postmortem 不闭环 Action
  ❌ 不学 LLM 模型测试 (大企用人窗口期)
```

## 相关章节

- 配合 [08_DevOps](../08_DevOps/index.md) 看 CI/CD + 灰度 + 监控
- 配合 [11_AI 基础设施](../11_AI基础设施/index.md) 看 LLM 评估 + RAG
- 配合 [12_AIOps](../12_AIOps/index.md) 看 MLOps + Drift + 监控
- 配合 [14_安全](../14_安全/index.md) 看 DevSecOps + SAST/SCA/DAST
- 配合 [15_渗透测试](../15_渗透测试/index.md) 看 红队 + LLM 红队
- 配合 [16_故障排查](../16_故障排查/index.md) 看 SLO + Chaos + Postmortem
