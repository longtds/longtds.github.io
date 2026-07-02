<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T03:00:00+08:00
source: Google Cloud Blog
domain: AI 基础设施
url: https://cloud.google.com/blog/products/databases/socradar-powers-rapid-threat-detection-with-alloydb-and-gemini-enterprise/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# SORadar 通过 AlloyDB 和 Gemini Enterprise 实现快速威胁检测 |谷歌云博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 03:00 CST |
| 领域 | AI 基础设施 |
| 来源 | Google Cloud Blog |
| 原文标题 | SOCRadar powers rapid threat detection with AlloyDB and Gemini Enterprise \| Google Cloud Blog |
| 原文 | [打开原文](https://cloud.google.com/blog/products/databases/socradar-powers-rapid-threat-detection-with-alloydb-and-gemini-enterprise/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

编者注：SOCRadar 是一家领先的网络安全公司，为全球企业提供威胁情报。随着网络威胁数量持续增长，SOCRadar 需要对其数据基础设施进行现代化改造，以便更快地为客户提供洞察。通过从 PostgreSQL 迁移到 AlloyDB，SOCRadar 实现了 20 倍的性能提升，降低了运营开销，现在能够更好地创新和发展。 SOCRadar 如何利用 AlloyDB 增强快速威胁检测 SOCRadar 提供外部威胁情报，帮助 30 多个国家/地区的组织防御网络攻击。在网络安全的前线，及时的情报就是一切，几分钟的延迟就可能意味着被阻止的利用和全面的破坏之间的区别。随着 SOCRadar 的业务规模扩大和网络威胁数量激增，他们的本地自行管理 PostgreSQL 数据库遇到了困难。该数据库根本无法跟上高速数据摄取和繁重的实时分析查询的同时需求。这造成了严重的数据瓶颈，减慢了向客户提供关键见解的速度，并使工程师无法进行创新

## 正文

数据库

##

SORadar 通过 AlloyDB 和 

Gemini Enterprise 实现快速威胁检测

2026 年 7 月 2 日

###### 艾哈迈德·库鲁科斯

SORadar，联合创始人、首席技术官

###### 赛莱什·克里希那穆西

谷歌数据库副总裁

###### 立即尝试 

Gemini Enterprise 商业版

编者注：SOCRadar 是一家领先的网络安全公司，为全球企业提供威胁情报。随着网络威胁数量持续增长，SOCRadar 需要对其数据基础设施进行现代化改造，以便更快地为客户提供洞察。通过从 PostgreSQL 迁移到 AlloyDB，SOCRadar 实现了 20 倍的性能提升，降低了运营开销，现在能够更好地创新和发展。

#### SORadar 如何使用 AlloyDB 增强快速威胁检测

[SOCRadar](https://socradar.io/) 提供外部威胁情报，帮助 30 多个国家/地区的组织防御网络攻击。在网络安全的前线，及时的情报就是一切，几分钟的延迟就可能意味着被阻止的利用和全面的破坏之间的区别。

随着 SOCRadar 的业务规模扩大和网络威胁数量激增，他们的本地自行管理 PostgreSQL 数据库遇到了困难。该数据库根本无法跟上高速数据摄取和繁重的实时分析查询的同时需求。这造成了严重的数据瓶颈，减慢了向客户提供关键见解的速度，并使工程师远离创新，转而专注于不断的手动数据库调整。

#### 评估数据库替代方案：寻求可扩展性

工程团队意识到他们的传统 PostgreSQL 环境已经达到了其绝对性能极限。为了扩展规模，SOCRadar 需要一个高性能的完全托管数据库，该数据库可以大幅削减运营开销，同时优雅地处理复杂的混合工作负载。他们评估了替代方案并选择了 Google Cloud 的 [AlloyDB for PostgreSQL](https://cloud.google.com/alloydb)。由于 AlloyDB 完全兼容 PostgreSQL，因此它提供了低风险的迁移路径，同时承诺构建专门的架构来同时处理大容量事务和实时分析。为了加速过渡，SOCRadar 与高级业务合作伙伴 NGC 合作，NGC 在以最短的停机时间执行精确切换之前仔细验证了架构。

#### 应对“三重威胁”工作负载

迁移到 AlloyDB 改变了 SORadar 处理大规模、多样化网络遥测的方式。如今，AlloyDB 可以毫不费力地管理 SOCRadar 工程团队所称的“三重威胁”查询环境，即使在处理量扩大的情况下也能保持亚秒级的查找延迟。

要了解性能飞跃，有助于将系统的速度（处理实时数据流）与其深度（分析历史数据）分开：

-

高速事务摄取 (OLTP)：该平台不断从数千个不同的、快速移动的来源（包括暗网论坛、僵尸网络日志和社交媒体源）摄取实时遥测数据。 AlloyDB 可处理这些连续的 INSERT 和 UPSERT 操作，实时摄取速度提高 3.2 倍，确保立即记录最新的威胁指标并可用于检测。

-

实时操作点读取：当安全分析师积极调查实时事件时，速度就是一切。在零负载条件下对索引字段进行随机 ID 查找（例如，通过 ID 查询特定的妥协指标）的基线性能测试表明，需要 3 到 3.5 秒的标准查询在 AlloyDB 上只需 1 秒即可完成。

-

深度分析聚合 (OLAP)：当客户请求复杂的部门报告（例如将金融部门一整年中最流行的攻击向量关联起来）时，数据库必须对大量历史数据集执行深度扫描。利用 AlloyDB 的内置 [内存列式引擎](https://docs.cloud.google.com/alloydb/docs/columnar-engine/about)，这些分析查询的运行速度比标准 PostgreSQL 快 20 倍。

#### 不仅仅是速度：回收 45 TB 和 75% 的 DBA 时间虽然原始性能提升是巨大的，但运营和财务影响完全改变了 SORadar 工程团队的日常工作方式。

得益于 AlloyDB 的高级自动化功能，包括智能内存管理和预写日志 (WAL) 优化，不再需要持续手动数据库调整。数据库管理员（DBA）的工作量显着下降，“大约每两三天一次”就需要进行一次系统健康检查。这释放了 75% 的 SOCRadar DBA 资源，使他们能够摆脱维护工作，完全专注于核心平台创新。

从财务上来说，AlloyDB 的动态存储管理解决了巨大的成本效率问题。与传统的数据库环境不同，即使在数据被清除后，您仍需要为固定的预配置存储付费，AlloyDB 会自动缩小存储规模以匹配实际的数据占用空间。通过清除遗留的、不必要的日志，SOCRadar 能够立即回收超过 45 TB 的存储空间，实现大规模、自动化的成本优化。

#### 使用集成的 

Gemini Enterprise Agent 平台应对警报疲劳

除了扩展基础设施之外，AlloyDB 还允许 SORadar 使用人工智能重新定义其威胁响应的核心架构。

全球安全运营中心 (SOC) 都受到“警报疲劳”的困扰——大量的安全警报很容易错过关键攻击。为了解决这个问题，SOCRadar 将 Gemini Enterprise Agent Platform 集成为其解决方案架构的核心组件，将其直接链接到在 AlloyDB 上运行的警报管理框架。

通过直接在其活动数据工作负载上运行 Gemini AI 原生过滤，SOCRadar 可以自动区分真警报和良性误警报。人工智能在警报到达最终用户之前对其进行分类、过滤和路由。这可以确保安全分析师免受噪音影响，只收到最关键、经过验证且可操作的情报。通过直接在其活动数据工作负载上运行 Gemini AI 原生过滤，SOCRadar 可以自动区分真警报和良性误警报。人工智能在警报到达最终用户之前对其进行分类、过滤和路由。这可确保安全分析人员免受噪音影响，只接收最关键、经过验证且可操作的情报，为完全自主的安全操作奠定基础。

#### 扩展功能：代理威胁狩猎的未来

凭借牢固建立的高性能基础，SOCRadar 的专业 AI 团队正在从被动分析过渡到主动自动化。该公司目前正在测试 Agentic AI 工作负载，并计划在后续阶段将其投入生产。

通过将实时数据代理与 Gemini Enterprise 和 AlloyDB 集成，SOCRadar 正在利用自主代理进行转型，这些代理不仅存储数据，而且还主动寻找威胁、根据上下文进行推理并采取行动。他们即将推出的生产路线图包括：

-

自然语言查询（NLQ）：允许分析人员使用会话语言进行快速威胁搜寻，降低查询海量数据库集的技术障碍。

-

智能语义相似性搜索：利用本机向量嵌入和 Gemini Enterprise，允许数据代理独立地显示传统关键字搜索会错过的历史日志中的隐藏模式。

-

自动事件摘要：在重大事件期间，将数百行复杂、技术性很强的日志立即转换为简洁、语言平实的执行摘要，供安全分析师使用。

通过将交易速度、历史深度和内置人工智能整合到统一平台中，SOCRadar 消除了数据瓶颈，并为全球网络安全防御构建了高度自动化、面向未来的框架。

准备好现代化您的数据库基础设施了吗？ [AlloyDB](https://cloud.google.com/alloydb) 提供完全托管、兼容 PostgreSQL 的数据库，为事务、分析和 AI 工作负载提供高性能。 [了解如何](https://cloud.google.com/alloydb)您可以降低成本、消除管理开销并构建智能应用程序。

发表于- [数据库](https://cloud.google.com/blog/products/databases)
- [客户](https://cloud.google.com/blog/topics/customers)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
