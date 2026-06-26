# 08_DevOps · 概述

> DevOps 是文化 + 实践 + 工具的总和。让开发和运维不再扯皮，让交付从月级到天级，再到分钟级。

## 一、DevOps 发展简史

| 阶段 | 时期 | 标志 |
|:---|:---:|:---|
| 概念提出 | 2009 | Patrick Debois 发起 DevOpsDays |
| 工具兴起 | 2011-2015 | Jenkins、Chef、Puppet、Docker |
| 容器化推动 | 2015-2018 | Docker、K8s、Microservices |
| GitOps 出现 | 2018-2020 | Argo CD、Flux、单一事实来源 |
| 平台工程 | 2022-至今 | IDP、Backstage、DevEx 抬头 |

## 二、DevOps 核心循环

```
        ┌──→ 计划 (Plan)
        │        ↓
   监控反馈    编码 (Code)
   (Monitor)      ↓
        ↑     构建 (Build)
        │        ↓
   运维 (Operate) ←──── 测试 (Test)
        ↑        ↑        ↓
        └─ 部署  ←─ 发布 (Release)
```

## 三、DevOps 核心实践

| 实践 | 价值 |
|:---|:---|
| **基础设施即代码** | 环境可复制、可审计 |
| **CI/CD 流水线** | 提交即测试、合并即发布 |
| **配置即代码** | 配置版本化、追溯 |
| **不可变基础设施** | 部署 = 替换，不修改 |
| **GitOps** | Git 是唯一事实来源 |
| **左移测试** | 在写代码时就测试 |
| **可观测性** | 度量驱动改进 |

## 四、典型 DevOps 工具栈

```
┌─── 代码 ─────┐
│ Git + GitLab/GitHub │
└──────────────┘
       ↓
┌─── CI ──────┐
│ Jenkins / GitHub Actions / GitLab CI / Tekton │
└──────────────┘
       ↓
┌─── 构建 ────┐
│ Docker / Kaniko / Buildah │
└──────────────┘
       ↓
┌─── 制品库 ──┐
│ Harbor / Nexus / Artifactory │
└──────────────┘
       ↓
┌─── CD ──────┐
│ Argo CD / Flux / Spinnaker │
└──────────────┘
       ↓
┌─── 环境 ────┐
│ K8s / Helm / Kustomize │
└──────────────┘
```

## 五、本章覆盖

| 子章节 | 内容 |
|:---|:---|
| **01_基础设施即代码** | Ansible / OpenTofu / Pulumi |
| **02_CICD** | Jenkins / GitLab CI / Tekton / GitHub Actions |
| **03_代码管理** | Git 工作流、代码审查、Monorepo |
| **04_容器化CI** | Dockerfile 优化、Kaniko、Trivy 扫描 |
| **05_部署策略** | 滚动 / 蓝绿 / 灰度 / Canary / GitOps |

## 六、DevOps 度量（DORA）

四大关键指标：

| 指标 | 含义 | 精英级 |
|:---|:---|:---|
| **部署频率** | 多久发一次 | 多次/天 |
| **变更前置时间** | 提交到上线时间 | < 1 天 |
| **变更失败率** | 发布造成故障的比例 | < 15% |
| **MTTR** | 故障恢复时间 | < 1 小时 |

## 七、学习路径

1. **基础**：Git + Linux + Shell
2. **CI/CD**：精通一个（Jenkins 或 GitLab CI）
3. **IaC**：Ansible + OpenTofu/Terraform
4. **K8s + GitOps**：Argo CD / Flux
5. **平台化**：内部开发者平台（IDP）

> 📖 DevOps 不是岗位，是**让团队跑得更快的方法论**。SRE 是 DevOps 的最佳实践之一。
