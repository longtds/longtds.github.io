<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-29T18:46:12+08:00
source: CNCF Blog
domain: 云原生
url: https://www.cncf.io/blog/2026/06/29/etcd-operator-joins-cozystack-with-a-new-v1alpha2-api/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# etcd-operator 通过新的 v1alpha2 API 加入 Cozystack

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-29 18:46 CST |
| 领域 | 云原生 |
| 来源 | CNCF Blog |
| 原文标题 | etcd-operator joins Cozystack with a new v1alpha2 API |
| 原文 | [打开原文](https://www.cncf.io/blog/2026/06/29/etcd-operator-joins-cozystack-with-a-new-v1alpha2-api/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

etcd-operator 项目开发了一个用于在 Kubernetes 上部署和维护 etcd 集群的操作器，已捐赠给 Cozystack 项目。除了捐赠之外，运营商的从头开始的实现也已在...下发布。

## 正文

[etcd-operator](https://github.com/cozystack/etcd-operator) 项目开发了一个用于在 Kubernetes 上部署和维护 [etcd](https://etcd.io/) 集群的操作符，已捐赠给 [Cozystack](https://cozystack.io/) 项目。除了捐赠之外，该操作符的从头开始的实现也已在新的 API 版本下发布 - etcd-operator.cozystack.io/v1alpha2，取代了之前的 etcd.aenix.io/v1alpha1。新的实现不是通过 StatefulSet 管理成员，而是直接驱动 etcd 的本机成员资格 API（MemberAdd、MemberPromote 和 MemberRemove 操作），使操作员能够完全控制集群成员资格。新的实现由 [Timofei Larkin](https://github.com/lllamnyp) 编写，他是先前代码库的维护者之一，保留在 [v1alpha1](https://github.com/cozystack/etcd-operator/tree/v1alpha1) 分支中。该项目是用 Go 编写的，并根据 Apache 2.0 许可证分发。

该项目由 Ænix 发起，它召集了 Kubernetes 社区的一个倡议小组来构建该项目。基础实现完成后，尝试将项目捐赠给CNCF。在这一举措的推动下，etcd 项目得出结论，需要一个官方运营商，并成立了自己的工作组，在评估现有实现后，选择从头开始开发代码库 - 这就是 [etcd-io/etcd-operator](https://github.com/etcd-io/etcd-operator) 的由来。从功能上来说，官方运营商还没有赶上 aenix etcd-operator，后者已经被社区以及 Cozystack 和 [Kamaji](https://github.com/clastix/kamaji) 等项目用于生产，因此该项目继续了自己独立的开发路线（本文最后给出了与官方运营商的对比）。Operator 通过两种资源管理 etcd 集群：EtcdCluster 描述集群的所需状态（副本数、etcd 版本、存储参数、TLS、身份验证、etcd 调整），而 EtcdMember 由 Operator 自己为每个集群成员创建并拥有其 Pod 和 PVC。与典型的解决方案不同，Operator 不使用 StatefulSet — 每个成员的 Pod 和 PVC 都是独立协调的，集群成员资格更改通过 etcd 的成员资格 API 进行：新成员作为学习者加入 (MemberAdd)，随后晋升为投票成员 (MemberPromote)，从仲裁中正常退出 (MemberRemove) 来执行删除，暂停集群可保留成员身份。 [concepts.md](https://github.com/cozystack/etcd-operator/blob/main/docs/concepts.md) 中描述了此架构背后的基本原理。

### 主要特点

- 集群引导和双向扩展，一次一个成员：学习者模式加入，从仲裁中退出并优雅地删除；
- 暂停集群而不丢失数据（spec.replicas：0）并使用相同的集群和成员标识符恢复集群；
- PVC（默认）或 tmpfs 中的数据存储 — 用于可重构的数据；当 Pod 丢失时，内存支持的成员会自动重新创建；
- 客户端和对等连接的独立 TLS 配置：自带 Secrets 或让运营商通过 cert-manager 颁发并自动续订证书；
- 通过 Secret 提供凭据的单个 root 用户的身份验证；
- 通过 EtcdSnapshot 资源快照到 S3 或 PVC，并在初始引导时从快照进行集群恢复；
- 自动创建的 PodDisruptionBudget，可防止耗尽操作破坏仲裁；
- apiserver 进行规范验证（CRD 中的 CEL 表达式），无需 Webhooks 或证书管理器依赖项；
- /scale 子资源，它使 kubectl 缩放和 VerticalPodAutoscaler 工作，2381 上的指标端口，直通亲和力和 topologySpreadConstraints；
- kubectl-etcd 插件，用于在集群部署后执行的第 2 天操作。

### 与 v1alpha1 相比有何变化

与旧的 etcd.aenix.io/v1alpha1 实现相比，进行了以下更改：- API组从etcd.aenix.io更改为etcd-operator.cozystack.io；
- 使用单独的每个成员 EtcdMember 资源而不是 StatefulSet；
- 自由格式的spec.options映射被一组类型化的参数（配额后端字节、自动压缩模式和保留、快照计数）取代——自由格式的映射允许传递与操作符逻辑冲突的标志；
- EtcdBackup 资源已重命名为 EtcdSnapshot，并保留其语义；
- 验证从 Webhook 转移到 CRD 中的 CEL 规则；
- 集群服务已切换到无头模式，这是稳定的每个成员 DNS 名称所必需的。

迁移是使用 etcd-migrate 工具就地执行的：采用旧操作员的运行集群，无需移动数据、重新启动 Pod 或丢失仲裁 — 仅更改对象所有权、标签和注释，之后新操作员接管。通过 DNS 名称到达集群的客户端保持不变。该过程在 [migration.md](https://github.com/cozystack/etcd-operator/blob/main/docs/migration.md) 中描述。

### 与官方运营商对比

该实现涵盖了 etcd 项目开发的官方 [etcd-operator](https://github.com/etcd-io/etcd-operator) 的 [路线图](https://github.com/etcd-io/etcd-operator/blob/main/docs/roadmap.md) 的大部分内容。按路线图项目划分的状态：

- 创建一个新的 etcd 集群，例如指定 etcd 版本的 3 或 5 成员集群 — 已实施。
- 了解集群的健康状况 - 已实施。
- 启用 TLS 通信，包括证书更新 — 已实施。
- 跨补丁或一个次要版本升级 - 部分实现：spec.version 仅适用于新创建的成员。
- 扩大和缩小，例如 1 -> 3 -> 5 个成员，反之亦然 — 已实施。
- 支持自定义 etcd 选项（通过标志或环境变量）——作为类型化的封闭参数集实现。
- 恢复单个失败的集群成员（仍然具有仲裁）——部分实现：PVC 损坏的成员还不会自动替换。
- 从多个失败的集群成员中恢复（仲裁丢失）——未实施，工作已计划。
- 创建集群的按需备份 — 已实施。
- 创建集群的定期备份 - 故意超出范围：定期快照预计由标准 CronJob 驱动。除了该路线图之外，v1alpha2 还提供了官方计划未列举的功能，由 Cozystack 和 Kamaji 多租户用例驱动：

- 缩放至零（暂停/恢复），保留集群和成员身份；
- 内存支持（tmpfs）存储，具有操作员驱动的成员替换；
- api 服务器端 CEL 验证 — 无 webhook，无证书依赖；
- 自动发出的 PodDisruptionBudget 范围仅限于投票成员；
- /scale 子资源带有填充的 status.selector，因此 kubectl scale 和 VerticalPodAutoscaler.targetRef 可以直接工作；
- 直通调度（亲和性、topologySpreadConstraints）并合并每个拥有对象的附加元数据；
- 来自传统运营商的就地迁移工具；
- 用于第 2 天操作的 kubectl-etcd 插件。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
