<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T00:00:00+08:00
source: Google Cloud Blog
domain: 云原生
url: https://cloud.google.com/blog/topics/inside-google-cloud/whats-new-google-cloud/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# Google Cloud 最新新闻和公告 |谷歌云博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 00:00 CST |
| 领域 | 云原生 |
| 来源 | Google Cloud Blog |
| 原文标题 | Google Cloud latest news and announcements \| Google Cloud Blog |
| 原文 | [打开原文](https://cloud.google.com/blog/topics/inside-google-cloud/whats-new-google-cloud/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

想了解 Google Cloud 的最新动态吗？在一个方便的位置找到它。定期查看我们的最新更新、公告、资源、活动、学习机会等。提示：不确定在 Google Cloud 博客上哪里可以找到您要查找的内容？从这里开始：Google Cloud 博客 101：主题、链接和资源的完整列表。 aside_block 6 月 29 日 - 7 月 3 日 Anthropic 的最新模型 Claude Sonnet 5 现已在 Agent Platform 上提供。这一新增功能可作为 Sonnet 4.6 的直接替代品，为组织提供跨企业工作流程完成任务的更多选择。它具有增强的推理、更清晰的代码生成以及桌面和浏览器工作流程的计算机使用功能。通过继续快速将前沿模型引入我们的平台，Google Cloud 为构建、测试和扩展企业级 AI 提供了业界最佳技术的不折不扣的选择。今天就开始吧。 6 月 22 日 - 6 月 26 日 加速 TPU 模型加载，同时节省 GKE 上的 RAM。大型模型冷启动通常会停止扩展并导致高价值 TPU 闲置。开源 Run:ai Model Streamer 现在在 TPU vLLM 0.18.0 中原生支持带有 Google Cloud Storage 的 TPU。这在

## 正文

Inside Google Cloud

##

Google Cloud 的新增功能

2026 年 7 月 2 日

![https://storage.googleapis.com/gweb-cloudblog-publish/images/whats_new_2026_CfhxFWX.max-2500x2500.jpg](https://storage.googleapis.com/gweb-cloudblog-publish/images/whats_new_2026_CfhxFWX.max-2500x2500.jpg)

###### Google Cloud 内容和社论

###### 立即尝试 

Gemini Enterprise 商业版

提示：不确定在 Google Cloud 博客上哪里可以找到您要查找的内容？从这里开始：[Google Cloud 博客 101：主题、链接和资源的完整列表](https://cloud.google.com/blog/topics/inside-google-cloud/complete-list-google-cloud-blog-links-2021)。

#### 6 月 29 日

- 7 月 3 日

- Anthropic 的最新模型 Claude Sonnet 5 现已在 Agent Platform 上提供。这一新增功能可作为 Sonnet 4.6 的直接替代品，为组织提供跨企业工作流程完成任务的更多选择。它具有增强的推理、更清晰的代码生成以及桌面和浏览器工作流程的计算机使用功能。

通过继续快速将前沿模型引入我们的平台，Google Cloud 为构建、测试和扩展企业级 AI 提供了业界最佳技术的不折不扣的选择。

[今天就开始吧。](https://console.cloud.google.com/agent-platform/publishers/anthropic/model-garden/claude-sonnet-5?hl=en)

#### Jun 22

- Jun 26- 加速 TPU 模型加载，同时节省 GKE 上的 RAM。
大型模型冷启动通常会停止扩展并导致高价值 TPU 闲置。开源 Run:ai Model Streamer 现在在 [TPU vLLM 0.18.0.](https://github.com/vllm-project/tpu-inference) 中原生支持带有 Google Cloud Storage 的 TPU。这种集成通过将张量直接流式传输到 CPU 内存中，绕过本地磁盘瓶颈和“双缓冲”陷阱，加速了 GKE 上的推理管道。在基准测试中，加载 480B 参数模型的速度提高了 2 倍以上，同时峰值主机内存使用量减少了一半。 [阅读完整指南并立即开始](https://discuss.google.dev/t/accelerate-tpu-model-loading-while-saving-ram-on-gke/374835)。
- 停止盲目训练：使用新的基于 OpenTelemetry 的 TPU AI 遥测收集器代理扩展 AI
Google Cloud 的新 AI Telemetry Collector 代理使用 OpenTelemetry 标准化 TPU 监控。它通过识别无声故障并提供零成本运营指标来优化企业机器学习工作负载，而不会耗尽主机 CPU 周期。该代理将遥测数据无缝路由到 Google Cloud Monitoring 或 Prometheus 以及自定义 Grafana 设置。它预安装在 Google 优化的 Ubuntu 映像上或通过 Docker 提供，可跟踪内存、网络延迟和核心利用率，以最大限度地提高多节点训练效率。

您可以通过单击此[链接](https://discuss.google.dev/t/stop-training-blind-scaling-ai-with-the-new-opentelemetry-based-tpu-ai-telemetry-collector-agent/375210) 阅读有关此功能的更多信息。

#### 6 月 15 日

- 6 月 19 日

- 加入我们，通过 AppyThings 深入了解代理 AI 控制
您的集成并没有失败——它们正在不断发展。当用户与 AI 代理交互时，他们不再直接到达您的站点，从而导致体验脱离您的背景、专业知识和预期体验。请于 6 月 25 日星期四参加我们与 AppyThings 合作的社区技术讲座，了解如何解决这一新的网关挑战。我们将探讨 MTN 如何奠定与模型上下文协议 (MCP) 的集成基础，以提供准确、一致的体验。我们的技术专家将演示如何利用 Apigee 作为集中式工具管理解决方案来管理代理访问。[注册参加会议](https://goo.gle/3Sfle0y)
- 使用 Spot 容量顾问优化 Spot 虚拟机部署，现已推出公共预览版
Google Compute Engine 推出了用于 Spot 到公共预览版的Capacity Advisor，现已向所有客户开放。该工具通过提供实时部署建议，将 Spot 容量发现转变为数据驱动的流程，以最大限度地提高可用性并最大限度地降低抢占风险。查询 [Capacity Advisor API](https://docs.cloud.google.com/compute/docs/instances/view-vm-availability) 了解可用性和最短预计正常运行时间，或使用新的 [控制台 UI](https://console.cloud.google.com/compute/capacityAdvisor)，其中包含全球可用性地图、现货价格查找和历史抢占率趋势，以直观地查找最具成本效益的计算容量。

[立即开始](https://docs.cloud.google.com/compute/docs/instances/view-vm-availability) 开始优化您的 Spot VM 部署！
- 构建多租户代理AI系统
在跨不同业务部门扩展生成式 AI 时，您的团队需要具有独特操作规则和工具的专业 AI 代理。我们的新参考架构可帮助您构建集中式多租户平台，以防止分散的孤岛、消除数据暴露风险并保持统一的合规性。阅读在 Google Cloud 中[设计和部署多租户代理 AI 系统](https://docs.cloud.google.com/architecture/multi-tenant-agentic-ai-system) 的指南。
- 如何配置 Gemini Enterprise 连接到自定义 MCP 服务器
Gemini Enterprise MCP 连接器是 Google Cloud Next 上的一项重大发布，因为它引入了将 Gemini Enterprise 连接到 MCP 服务器的功能。此博客 [帖子](https://medium.com/google-cloud/how-to-configure-gemini-enterprise-to-connect-to-a-custom-mcp-server-2e28adc96420) 提供了有关如何使用 Google Maps Ground Lite MCP 服务器作为示例来配置第一个自定义 MCP 服务器连接器的分步指南。一旦您了解了此流程，您就可以使用 Gemini Enterprise 配置多个 MCP 服务器来提供您需要的所有上下文。

#### 6 月 8 日

- 6 月 12 日- 使用云位置查找器简化多云规划，现已全面推出
Cloud Location Finder 提供有关跨 Google Cloud、AWS、Azure 和 OCI 的公共区域、专区和 Google 分布式云连接位置的最新数据。现在，您可以根据提供商、邻近度、地域和碳足迹以编程方式发现位置，以优化您的全球基础设施策略，以实现性能、合规性和可持续性。

[立即免费开始](https://cloud.google.com/location-finder/docs)

#### 6 月 1 日

- 6 月 5 日

- 使用 BigQuery Graph 对物理世界进行建模
管理复杂的供应链需要的不仅仅是电子表格；它需要物理世界的数字复制品。在这篇 [博文](https://cloud.google.com/blog/products/data-analytics/modeling-a-digital-twin-using-bigquery-graph) 中，Guru Rangavittal 和 Candice Chen 探讨了 BigQuery Graph 如何通过将物理资产转变为节点和边缘的互连地图来帮助组织构建数字孪生。通过超越传统的关系数据库，企业可以实时清晰地了解运营情况——从执行外科手术原料召回到分析天气驱动的物流风险。了解 BigQuery Graph 如何将被动救火转变为主动、精确建模，让您能够在几秒钟内看到关键连接并确保您的供应链面向未来。
- Apigee for AI：管理 LLM 和 MCP 服务器（以西班牙语呈现）
了解如何将您的 AI 计划从实验原型安全地过渡到企业就绪部署。 6 月 18 日与 Luis Cuellar 一起进行技术深入探讨（以西班牙语演讲），探索 Apigee 的最新 AI 网关功能。了解如何对模型上下文协议 (MCP) 服务器进行集中治理，通过强大的 API 网关安全策略保护LLM (LLM)，以及管理基于令牌的配额。

[报名参加 6 月 18 日西班牙社区 TechTalk](https://goo.gle/4dyC2Ie)

#### 5 月 25 日

- 5 月 29 日

-[Anthropic 的 Claude Opus 4.8](https://www.anthropic.com/news/claude-opus-4-8) 现已在 [Gemini Enterprise Agent Platform](https://console.cloud.google.com/vertex-ai/publishers/anthropic/model-garden/claude-opus-4-8) 上提供。随着我们不断扩展平台的模型产品，这一新增功能为组织提供了更多处理复杂、多阶段企业工作流程的选择。 Claude Opus 4.8 带来了强大的代理编码功能，允许开发人员管理广泛的重构并跟踪扩展会话的依赖关系。

- API Horizon 慕尼黑，2026 年 7 月 6 日：精心策划 AI 和 API 的下一个时代
掌握下一代人工智能和数字生态系统的编排。 7 月 6 日与 Google Cloud 专家和 DACH 技术领导者一起独家了解 Apigee 路线图、代理管理和模型上下文协议 (MCP)。获得现实世界的见解并与区域一体化社区建立联系。

[立即注册](https://goo.gle/4dTxQmo)
- 保护 AI 代理：扩展代理网关模式
了解如何防止自主 AI 代理调用未经授权的 API。 6 月 4 日与 Apigee 专家 Joel Gauci 一起深​​入了解扩展代理网关模式的技术。本次会议涵盖实施细粒度授权 (FGA)、实施安全令牌交换以及在 API 网关层建立模型上下文协议 (MCP) 治理以保护企业后端服务。

[注册参加 6 月 4 日社区技术讲座](https://goo.gle/4fbAsxg)
- API 到代理的安全性：通过 MCP 向 Gemini Enterprise 公开 REST API
将 Gemini Enterprise 代理连接到核心数据，而不会造成安全隐患。 6 月 11 日加入 Google Cloud 专家 Nigel Walters，了解如何立即将旧版 REST API 转换为安全的模型上下文协议 (MCP) 服务器。我们将介绍如何安全地向 Gemini 注册工具，同时实施网关级防护（例如速率限制和访问控制策略）。

[注册参加 6 月 11 日社区技术讲座](https://goo.gle/4nVyjIr)

#### 5 月 18 日

- 5 月 22 日- 中文网络研讨会| 6 月 4 日：人工智能指挥与控制
随着人工智能代理从实验试点转向核心企业职能，治理已成为下一步关键。北京时间 6 月 4 日上午 10:00 加入 Google Cloud，了解如何构建安全的 AI 管理层架构。我们将探索如何开发受管理的 MCP（模型上下文协议）端点、管理工具对企业数据的访问以及利用强大的审计日志来实施 AI。本次会议还包括 Google Cloud 上这些治理框架的实际演示。

[在此注册](https://goo.gle/4dx4Lf5)
- GCP 宣布针对设备上用例对法学硕士进行基准测试和优化的新功能
由于硬件分散，将经过微调的 LLM 从 GCP 部署到智能手机等边缘设备非常复杂。 Google AI Edge Portal 弥补了这一差距，使 GCP 开发人员能够在 120 多种 Android 设备上测试 AI 性能，这些设备代表了当今市场上高、中、低端智能手机的全部多样性。本周在 I/O 上，我们宣布了全新的[功能](https://cloud.google.com/blog/products/ai-machine-learning/benchmark-llms-on-device-with-ai-edge-portal)，用于跨这些设备进行 LLM 性能基准测试和调试。立即[注册](https://docs.google.com/forms/d/e/1FAIpQLSfTcGPycQve8TLAsfH46pBlXBZe9FrgJAClwbF7DeL1LgVn4Q/viewform) 以在私人预览版中使用这些新功能。

#### 5 月 11 日

- 5 月 15 日

- 构建您的 AI 和 MCP 控制塔以实现普遍治理
借助 Apigee 掌握代理安全的未来。参加 5 月 21 日的社区 TechTalk，了解 Apigee 如何充当模型上下文协议 (MCP) 的中央“控制塔”。我们将探讨新的 JSON-RPC 工具授权如何在整个组织中实现细粒度的访问策略，从而确保安全且可扩展的 AI 部署。无论是管理内部工具还是外部用户，都要学会绝对精确地管理您的代理生态系统。本次会议旨在覆盖欧洲、中东和非洲和美洲地区的全球范围。

[注册参加 5 月 21 日的社区技术讲座](https://goo.gle/4u9slWF)

#### 4 月 27 日

- 5 月 1 日- 掌控您的发布：Apigee Production 上线清单
使用 Apigee 生产指南确保安全启动。 5 月 28 日加入 Nicola Cardace，探索安全护栏，包括 IAM 角色、mTLS 配置和加密 KVM 迁移。该技术讲座计划于美国东部夏令时间上午 11 点/中欧夏令时间下午 5 点为欧洲、中东和非洲 (EMEA) 和美洲地区团队提供支持，提供您需要的技术路线图，让您充满信心地进行转换。

[报名参加 5 月 28 日社区技术讲座](https://goo.gle/4elMCTI)
-

将 API 转变为 Google Cloud Agentic Platform 上的受管代理工具
将您的 API 转变为 Google Cloud Agentic Platform 上安全、受监管的代理工具。 5 月 7 日与专家 Christophe Lalevée 一起深入探讨人工智能产品化的技术。本次会议安排在欧洲中部夏令时间下午 5 点/美国东部时间上午 11 点，以最大程度地覆盖欧洲、中东和非洲和美洲地区的开发人员，该会议将探讨自信地扩展企业级人工智能所需的集成和治理框架。

[注册参加 5 月 7 日的社区技术讲座](https://goo.gle/3PfWm7M)

- [Fractional G4 VM](https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines#g4-machine-types) 已普遍可用，为 AI 和图形工作负载提供高效且经济高效的切入点。这些新配置采用 NVIDIA 虚拟 GPU (vGPU) 技术，让您能够以灵活、较小的增量利用 NVIDIA RTX PRO 6000 Blackwell 服务器版 GPU 的强大功能，从而可以调整基础设施的规模，以满足应用程序的特定需求。通过提供对高级硬件的更精细的访问，部分 G4 虚拟机可让您优化资源分配并减少开销，而无需牺牲性能。您现在可以根据您的特定需求选择其他 GPU 切片大小：

- 1/2 GPU：非常适合更密集的任务，例如 LLM 推理、机器人传感器模拟和高保真 3D 渲染。
- 1/4 GPU：针对主流工作负载进行优化，包括中端创意设计、视频转码和实时数据可视化。
- 1/8 GPU：非常适合轻量级应用程序，例如远程桌面、生产力工具和入门级流媒体服务。
-将人工智能从沙箱原型过渡到企业级系统是一个主要障碍。单一脚本不足以广泛部署。为了通过 Gemini 实现真正的规模和可靠性，组织必须采用面向服务的微代理架构，建立零信任安全性，并实施严格的 EvalOps。掌握“Agentic 成熟度阶梯”，确保您的 AI 和 Agentic 解决方案稳健、安全，并为现实世界做好准备。

[观看深入探讨](https://lnkd.in/gHBH8cTv) 和[阅读开发者博客](https://discuss.google.dev/t/beyond-the-prototype-scaling-production-grade-agents-with-gemini/356140) 了解更多信息。

- 使用 Google Cloud Power 在 VS Code 中进行机器学习开发：工作台扩展现已推出
数据科学家和开发人员现在可以将 VS Code 的本地生产力与 Google Cloud 的可扩展基础设施结合起来。新的 Google Cloud Workbench Notebooks 扩展允许您直接在本地 IDE 中连接到托管云环境并在其上运行笔记本。这种集成通过消除上下文切换并在熟悉的界面中为复杂的工作负载提供高性能计算来简化机器学习生命周期。作为我们对开发者生态系统承诺的一部分，该扩展完全开源，以支持社区驱动的创新。

- 从市场安装：[GoogleCloudTools.workbench-notebooks](https://marketplace.visualstudio.com/items?itemName=GoogleCloudTools.workbench-notebooks)
- 在 GitHub 上贡献：[colab-enterprise-vscode](https://github.com/GoogleCloudPlatform/colab-enterprise-vscode)

#### 4 月 20 日

- 4 月 24 日

- 公布 2026 年度 Google Cloud 合作伙伴
Google Cloud 很荣幸地庆祝 2026 年度合作伙伴奖的获奖者！这些奖项表彰了人工智能、安全、基础设施等领域的一群杰出合作伙伴，他们表现出了对客户成功的承诺。从全球系统集成商到专业初创公司，这些获胜者正在利用 Google Cloud 的力量来解决复杂的挑战并推动全球数字化转型。与我们一起祝贺这些组织在过去一年中的创新、协作和富有影响力的成果。

查看 [2026 年合作伙伴奖获奖者](https://cloud.google.com/blog/topics/partners/2026-partners-of-the-year-winners-next26)

#### 4 月 13 日

- 4 月 17 日- 我们很高兴地宣布推出 Datastream 元数据与 Knowledge Catalog 集成的公共预览版。这是我们为所有 Datastream 资产提供集中式“单一管理平台”的愿景的第一步。该增强功能会自动同步流、连接配置文件和专用连接，从而消除数据孤岛。它增强了可发现性，允许您使用与 BigQuery 表相同的界面来搜索 Datastream 资产。还提供集中治理，使您的实时数据资产更加透明且更易于管理。
- 通过操作系统现代化将 Apigee OPDK 升级到 4.53
使用 Google 的官方顺序升级路径对您的基础设施进行现代化改造。我们的技术专家 Rakesh Talanki 概述了如何将 Apigee OPDK 升级到 v4.53，同时迁移到受支持的操作系统 (RHEL 8.x/9.x)。本指南涵盖“构建”方法，包括多数据中心同步，以确保稳定、零停机的过渡

[阅读指南](https://goo.gle/3Oa8uqy)
- Cloud Run Worker Pools 和 CREMA：大规模支持无服务器 AI
Google Cloud 宣布全面推出 Cloud Run 工作线程池，这是一种专为基于拉取的非 HTTP 工作负载而设计的新资源类型。与根据请求流量进行扩展的传统 Cloud Run 服务不同，工作线程池为处理消息队列或运行大规模 AI 推理等后台任务提供“始终在线”的环境。为了支持这一点，Google Cloud 还开源了 Cloud Run external Metrics Autoscaler (CREMA)。 CREMA 基于 KEDA 构建，支持工作池的队列感知自动扩展，允许它们根据 Pub/Sub 积压或 Kafka 滞后等外部信号动态扩展。
- Apigee 模型上下文协议 (MCP) 现已全面可用
通过 Apigee 中 MCP 的通用可用性，将企业 API 作为代理 AI 应用程序的 MCP 工具公开。此更新允许开发人员使用 OpenAPI 规范将 API 转换为 AI 就绪工具，从而无需本地 MCP 服务器或其他基础设施。借助 API 中心中的托管端点和语义搜索，您现在可以为 AI 代理提供对企业数据的大规模安全、受管控访问。

[探索 MCP 概述](https://goo.gle/3QfoEQ4)

#### 4 月 6 日

- 4 月 10 日- 社区 TechTalk：利用 ADK、UCP 和 Apigee X 为零售代理商提供支持
超越基本的聊天机器人，转向安全的事务性人工智能体验。参加 4 月 16 日的社区 TechTalk，了解 Apigee X 和 Gemini 如何使用 UCP 标准为 AI 购物助理构建“信任层”。我们将演示如何使用 Model Armor 阻止即时注入，并通过代币限制实施成本治理，以确保从发现到购买的路径安全。

[注册参加技术讲座](https://goo.gle/41ocUgq)
- 在您的人工智能代理中实现多模式功能
探索三种新的参考架构，用于构建可以处理和分析多模态数据的复杂多智能体人工智能系统。要分析不同的多模态数据并生成高置信度分类，请参阅[对多模态数据进行分类](https://docs.cloud.google.com/architecture/agentic-ai-classify-multimodal-data)。要创建实时处理音频和视频流的流畅对话式 AI，请参阅[启用实时双向多模式流](https://docs.cloud.google.com/architecture/agentic-ai-bidirectional-multimodal-streaming)。要将碎片化的多模态数据整合到可搜索的知识图谱中，请参阅[多模态 GraphRAG 资源编排](https://docs.cloud.google.com/architecture/agentic-ai-multimodal-graph-rag-resource-orchestration)。
- 使用代理 AI 系统自动化 SecOps 工作流程
为了加速事件响应并减少安全团队的手动工作，您需要一个可以自动执行补救行动手册的系统。我们的新参考架构可帮助您构建 AI 代理，通过单一界面跨不同的安全工具（例如 SIEM、CSPM 和 EDR）协调复杂的分类和调查工作流程。请参阅[编排安全操作工作流程](https://docs.cloud.google.com/architecture/agentic-ai-orchestrate-security-ops-workflows) 的完整指南。

#### 3 月 30 日

- 4 月 3 日- 东盟网络研讨会| 4 月 30 日：通过 GCP 掌握大规模代理治理
随着人工智能代理从实验试点转向核心企业职能，治理是下一步关键。与 Google Cloud 专家 Shilpi Puri 和 Wely Lau 一起参加 4 月 30 日上午 11:00（新加坡标准时间）的网络研讨会，了解如何构建安全的 AI 管理层。我们将探索开发受管理的 MCP 端点、管理工具对企业数据的访问以及通过强大的审核日志来操作 AI。该会议包括这些框架在 Google Cloud 上运行的现场演示。

[在此回复。](https://goo.gle/47FX1Wn)

#### 3 月 23 日

- 3 月 27 日

-

将庞大的 API 转变为可供代理使用的目录
随着组织规模的扩大，API 通常会分散在多个网关中，从而产生阻碍 AI 采用的“盲点”。为了解决这个问题，我们为 Apigee API 中心引入了两项新功能：与 API Gateway 的新集成，可自动将 API 元数据集中到单个控制平面中，以及规范提升插件（现已提供公共预览版）。该附加组件使用 AI 来增强您的 API 文档，并提供 AI 代理可靠运行所需的精确示例和错误代码。

[阅读完整的博客文章以开始使用。](https://goo.gle/47dEYqc)

-

网络研讨会 | 4 月 16 日：AI 命令与控制
随着人工智能代理从实验试点转向核心企业职能，治理是下一步关键。与 Google Cloud 专家 Satyam Maloo 一起参加 4 月 16 日上午 11:00（美国标准时间）的网络研讨会，了解如何构建安全的 AI 管理层。我们将探索开发受管理的 MCP 端点、管理工具对企业数据的访问以及通过强大的审核日志来操作 AI。该会议包括这些框架在 Google Cloud 上运行的现场演示。

[在此回复。](https://goo.gle/4t43Vg4)

-

使用 Apigee 实现事件摄取的现代化和解耦
在现代云原生架构中，将生产者与消费者分离对于构建弹性系统至关重要。虽然 Google Cloud Pub/Sub 提供了可扩展的主干网，但将其直接暴露给外部客户端可能会带来安全和管理开销。本新指南探讨了如何利用 Apigee 作为智能 HTTP 提取点。了解如何使用 PublishMessage 策略或 Pub/Sub API 在消息到达内部总线之前处理安全性、中介和流量控制。

[阅读完整指南。](https://goo.gle/3POgsWF)#### 3 月 16 日 - 3 月 20 日

- BigQuery Studio 中由 Gemini 支持的助手获得上下文感知升级
BigQuery Studio 中由 Gemini 支持的助手已转变为完全上下文感知的分析合作伙伴，支持您的整个数据生命周期。新功能包括智能资源发现，它使用 Dataplex 通用目录搜索跨项目查找资源，并使用自然语言深入研究元数据。您现在可以自动执行任务，例如直接通过聊天界面安排生产级查询，并通过根本原因分析和成本控制审核立即对长时间运行或失败的作业进行故障排除。

[探索](https://docs.cloud.google.com/bigquery/docs/use-cloud-assist) 助理可以执行的全部操作。

#### 3 月 9 日

- 3 月 13 日

-

想使用Gemini来开发代码却不知道从哪里开始？
这篇[文章](https://medium.com/google-cloud/supercharge-your-spark-development-with-gemini-1540f1cb47d4) 包含几个使用 Gemini 提示开发代码的示例；它确定了使代码正常运行所需的更改。本文还参考了 github 上提供的其他示例。

#### 3 月 2 日

- 3 月 6 日

-

隆重推出 Gemini 3.1 Flash-Lite，这是我们速度最快且最具成本效益的 Gemini 3 系列型号。 3.1 Flash-Lite 专为大规模开发人员工作负载而构建，在其价格和型号级别上提供了高质量。 Gemini 3.1 Flash-Lite 可以处理大规模任务，例如大批量翻译和内容审核，其中成本是优先考虑的。它还可以处理需要更深入推理的更复杂的工作负载，例如生成用户界面和仪表板、创建模拟或遵循指令。

从今天开始，3.1 Flash-Lite 将通过 [Vertex AI](https://console.cloud.google.com/vertex-ai/studio/multimodal?mode=prompt&model=gemini-3.1-flash-lite-preview) 向企业推出预览版，并通过 [Google AI Studio](https://aistudio.google.com/prompts/new_chat?model=gemini-3.1-flash-lite-preview) 中的 Gemini API 向开发人员推出预览版。

-TechTalk：为 Apigee 实施设备授权 (RFC 8628)
了解如何授权没有键盘和浏览器的“无头”设备，例如智能电视或 AI 代理。参加 3 月 19 日（欧洲中部时间下午 5 点/美国东部时间中午 12 点）参加我们的社区技术讲座，深入了解 Apigee X/Hybrid。我们将介绍设备和自主代理的状态管理、轮询和人机循环安全模式的现实机制。

[注册参加技术讲座](https://goo.gle/4r6o6Zi)

#### 2 月 23 日

- 2 月 27 日

-

Nano Banana 2 使专业级图像生成变得更快、更容易
Nano Banana 2 是我们最先进的图像生成和编辑模型。它以您期望的 Flash 速度提供专业级图像生成和编辑 — 使您更容易获得您喜爱的 Nano Banana Pro 的质量、推理和世界知识。了解有关该模型的更多信息[此处](https://blog.google/innovation-and-ai/technology/ai/nano-banana-2)。

-

实现合规的智能之路：利用 Google Cloud 转变监管 QC
减少“拒绝归档”(RTF) 风险和提交周期时间对于生命科学领导者至关重要。 Google Cloud 的监管提交语义 QC 审核员利用 Gemini 和 RAG 架构将质量控制从手动负担转变为主动、智能的工作流程。

通过自动化语义交叉引用、叙述一致性检查和基于动态指导的审核，该解决方案可确保严格的准确性和可审核性。它在安全的 GxP 就绪环境中运行，使团队能够检测细微的不一致并生成补救计划，而无需牺牲数据隐私。

[了解更多](https://discuss.google.dev/t/the-intelligent-path-to-compliance-transforming-regulatory-quality-control-with-google-cloud/335276)。

- 停止打字，开始互动！ Gemini Live Agent 挑战赛就在这里。使用 Gemini 和 Google Cloud 构建沉浸式代理，帮助您看到、听到和说话。争夺超过 80,000 美元的奖金以及参加 Google Cloud Next '26 的机会！

提交开放时间为 2026 年 2 月 16 日至 2026 年 3 月 16 日。了解更多信息并在 [geminiliveagentchallenge.devpost.com](http://geminiliveagentchallenge.devpost.com/) 上注册

#### 2 月 9 日

- 2 月 13 日

-

在 Google Cloud 上推出 Gemini 3.1 Pro。3.1 Pro 是解决复杂问题的明显更智能、更有能力的基准。我们正在大规模发布 3.1 Pro，以我们的[目标](https://cloud.google.com/blog/products/ai-machine-learning/gemini-3-is-available-for-enterprise?e=48754805) 为基础，帮助您实现业务转型，迈向代理未来。了解有关模型功能的更多信息[此处](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-pro)。 Gemini 3.1 Pro 从今天开始在 [Vertex AI](https://cloud.google.com/vertex-ai?e=48754805) 和 [Gemini Enterprise](https://cloud.google.com/gemini-enterprise?e=48754805) 中提供预览版。开发人员可以通过 [Google AI Studio](https://aistudio.google.com/prompts/new_chat?model=gemini-3.1-pro-preview)、[Android Studio](https://developer.android.com/studio)、[Google Antigravity](https://antigravity.google/blog/gemini-3-1-in-google-antigravity) 和 [Gemini CLI](https://geminicli.com/) 中的 Gemini API 访问预览版模型。

- 自动实现与 GKE 动态默认存储类的存储兼容性
在 GKE 中管理跨混合代虚拟机集群的存储变得更加容易。借助新的动态默认存储类，Google Kubernetes Engine 根据节点的特定硬件兼容性自动在持久磁盘 (PD) 和 Hyperdisk 之间进行选择。这种抽象消除了对复杂的调度规则和手动配对的需要，确保您的卷“正常工作”，无论底层基础设施如何。通过在单个类中定义这两个变体，您可以减少运营开销，同时保持整个集群的最佳性能和成本效率。

[探索自动磁盘类型选择](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/hyperdisk#automated_disk_type_selection)
-

社区 TechTalk：使用 strofa.io 进行人工智能驱动的 Apigee 开发
2 月 26 日加入 Apigee 社区，深入了解 [strofa.io](https://www.google.com/search?q=http://strofa.io)。演讲嘉宾 Denis Kalitviansky 将演示这一新的人工智能工具如何自动化和协调 Apigee 开发，从本地模拟器到大规模混合环境。了解如何使用最新的人工智能驱动的自动化来扩展 API 管理并简化团队协作。

[立即注册以保留席位。](https://goo.gle/3Oerns3)

#### 1 月 26 日

- 1 月 30 日- 通过本机 OpenAPI v3 支持简化 API 治理
借助对 API 网关和云端点的 OpenAPI v3 (OASv3) 支持的全面可用性，消除集成债务并加快部署速度。您不再需要将现代规范降级到 OASv2。相反，您现在可以直接在 OASv3 文件中使用本机 Google 特定扩展来定义 API 合同并强制执行关键策略（包括遥测、配额和安全性）。此更新可确保您的 API 设计安全，同时保持与现代开发者生态系统和 Google Cloud 的 AI 服务完全兼容。

[开始在 API 网关和 Cloud Endpoints 上使用 OpenAPI v3。](https://goo.gle/49Wx58Z)

- 使用新的开源 API 测试器加速 API 测试
开始使用 API Tester 验证您的 API，这是一个简单的、基于 YAML 的测试驱动开发 (TDD) 框架。该工具专为 Apigee 社区设计，允许您编写人类可读的测试，通过 Web 客户端或 CLI 立即运行它们，并在 Apigee 代理上执行深度单元测试。借助对 JSONPath 断言和 Apigee 共享流的原生支持，您无需离开终端即可验证从负载数据到“proxy.basepath”等内部变量的所有内容。

[探索 API 测试器指南并立即开始测试您的代理。](https://goo.gle/4q5WDGK)
- 在 Apigee Hybrid 中使用 Kubernetes Secret 保护敏感数据
通过直接在 API 代理中访问 Kubernetes Secret，增强 Apigee Hybrid 的安全性。这种混合专有功能将敏感凭据保留在集群边界内，并防止复制到管理平面。它支持严格的职责分离：操作员通过“kubectl”管理机密，而开发人员将它们引用为安全流变量——非常适合高合规性和 GitOps 工作流程。[在混合代理中实施 Kubernetes Secrets。](https://goo.gle/4qEVffo)
- 以全新的视角看待控制台：Google Cloud 现已全面提供深色模式
使用深色模式提升您的云管理工作流程，该模式现已在 Google Cloud 控制台中普遍提供。我们提供了现代、有凝聚力且易于使用的体验，经过重新设计，可实现最大程度的舒适度和生产力，尤其是在长时间工作和弱光环境下。可以根据操作系统的偏好自动启用深色模式，也可以通过“设置”->“外观”菜单手动启用。

[立即切换到深色模式，享受现代、舒适、高效的环境！](https://docs.cloud.google.com/docs/get-started/console-appearance)
- Apigee X 网络：PSC 或 VPC 对等互连？
决定如何连接 Apigee X？观看此视频以比较 Private Service Connect 和 VPC 对等互连。我们详细分析了北向和南向路由、IP 消耗以及如何在本地或云端实现目标。了解如何简化架构并避免常见的网络“陷阱”，以实现更顺利的部署。

[观看视频。](https://goo.gle/4bWBGdV)

#### 1 月 19 日

- 1 月 23 日

- 弥合差距：Apigee 门户中的 Excel 到 API 转换
为您的客户提供更多联系方式！ Tyler Ayers 的这篇新文章探讨了如何扩展 Apigee Integrated Portal 以支持直接 Excel 文件上传。通过利用 SheetJS 和自定义门户脚本，您可以让用户上传电子表格、预览数据并将其直接提交到您的 API，而无需自己编写一行集成代码。对于那些尚未准备好 API 的人来说，这是一种简化入门的强大方法。[了解如何构建它](https://goo.gle/3Nq3Pjo)。
- 使用 Firestore 的全新高级查询引擎提升您的应用程序
我们从根本上重新构想了 Firestore 的企业版管道操作。体验强大的新引擎，具有一百多个新查询功能、无索引查询、新索引类型和可观测性工具，以提高查询性能。使用内置工具无缝迁移，并利用 Firestore 现有的差异化无服务器基础、几乎无限的规模和行业领先的 SLA。加入由 60 万开发人员组成的社区，打造富有表现力的应用程序，最大限度地发挥丰富的可查询性、实时监听查询、强大的离线缓存和尖端的人工智能辅助编码集成的优势。

[详细了解 Firestore 管道操作。](https://cloud.google.com/blog/products/data-analytics/new-firestore-query-engine-enables-pipelines?e=48754805)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
