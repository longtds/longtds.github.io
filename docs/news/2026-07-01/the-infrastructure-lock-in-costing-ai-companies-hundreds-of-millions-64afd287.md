<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T03:04:40+08:00
source: The New Stack
domain: 技术动态
url: https://thenewstack.io/future-proof-ai-infrastructure/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# 基础设施锁定导致人工智能公司损失数亿美元

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 03:04 CST |
| 领域 | 技术动态 |
| 来源 | The New Stack |
| 原文标题 | The infrastructure lock-in costing AI companies hundreds of millions |
| 原文 | [打开原文](https://thenewstack.io/future-proof-ai-infrastructure/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

Unsplash 的 Egor Komarov 这篇文章《基础设施锁定导致人工智能公司损失数亿美元》首先出现在 The New Stack 上。

## 正文

两年来，人工智能基础设施竞赛一直由一个问题主导：谁拥有最快的 GPU？吉姆·凯勒认为这个问题是错误的。

在 [最近接受 EE Times 采访](https://www.eetimes.com/jim-keller-on-tenstorrents-blackhole-scaling-and-ipo-ambitions) 中，Tenstorrent 首席执行官认为，组织目前可以采取的最危险的举措是针对当前运行的模型优化其人工智能基础设施。这并不是因为这些模型不好，而是因为它们将不再是 18 个月后运行的模型。 [Keller](https://www.linkedin.com/in/jimbkeller/) 援引租金法则和阿姆达尔法则来论证内存、网络和系统级平衡现在比峰值浮点性能更重要。

>

并不是因为这些模型不好，而是因为它们不会成为 18 个月后运行的模型。

这听起来像是凯勒产品宣传的开始，但它背后确实有分量，因为人工智能的发展速度比其底层基础设施更快。那些花费数亿美元打造一代模型的公司现在正在降低重新做这件事的成本。

这种恐惧被称为“锁定”，它正在重塑人工智能领域最大的参与者对硬件的看法。

### 工作负载超出了 

GPU 的能力

在 2023 年和 2024 年，人工智能基础设施是一个相对简单的采购问题：训练LLM，将其提供给用户，并购买 Nvidia 能够提供的尽可能多的 GPU。工作负载是可预测的，GPU 可以很好地处理它们。

然后人工智能的发展超出了它所构建的基础设施的范围。

推理模型花费更多时间来解决问题，而不是直接跳到答案。在完成任务之前，代理会在 API、数据库和代码之间切换。多模式模型将文本与图像、音频和视频混合在一起。这些工作负载对硬件的压力都不相同，这迫使基础设施团队重新思考两年前还很合理的假设。

>

人工智能的发展超出了其构建的基础设施的范围。

没有哪个单一芯片架构能够同样出色地处理所有这些问题。构建人工智能基础设施的组织开始意识到，问题不仅仅是哪个加速器速度最快，而是我们如何构建不需要在每次人工智能实现另一次飞跃时都被拆散的系统？

### Nvidia 已经在销售一种答案看看黄仁勋都在说什么，已经不是

GPU了。

在 GTC 2026 上，Nvidia [推出了 Vera Rubin 平台](https://nvidianews.nvidia.com/news/nvidia-vera-rubin-platform) — 七款设计为单个系统运行的芯片：Rubin GPU、Vera CPU、NVLink 6 交换机、ConnectX-9 网络、BlueField-4 DPU 等。 Vera CPU 已存在

用于代理 AI 的 CPU 密集型工作——工具调用、代码执行、编排。英伟达将这些部署称为“人工智能工厂”，这种语言是经过深思熟虑的。他们销售的是完整的基础设施，而不是单独的加速器。

当拥有 70% 市场份额的公司不再在 GPU 基准测试上处于领先地位并开始谈论系统级协同设计时，它就会告诉你这个市场的重心正在向何处移动。

重构很重要。当拥有 70% 市场份额的公司不再在 GPU 基准测试上处于领先地位并开始谈论系统级协同设计时，它就会告诉你这个市场的重心正在向何处移动。计算仍然很重要。但英伟达承认——通过其产品架构（如果不是其营销）——仅靠原始加速器性能不足以应对即将发生的事情。

### 超大规模

企业设计自己的芯片

AMD 也看到了同样的问题，尽管它采取了不同的路线。 [Helios](https://www.amd.com/en/newsroom/press-releases/2026-1-5-amd-and-its-partners-share-their-vision-for-ai-ev.html) 将 CPU、GPU 和网络整合到一个机架级平台中，反映出一种更广泛的转变，即不再将 GPU 视为宇宙中心。宣传语并不是“我们的加速器更快”。芯片周围的基础设施与芯片本身一样越来越重要。超大规模企业用他们的钱包来争论这个问题的时间甚至更长。谷歌花了十年时间共同设计其[TPU芯片、互连和软件框架](https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/)——其第七代Ironwood芯片现已普遍上市——使其能够对整个堆栈进行不同寻常的控制。亚马逊却反其道而行之，为不同的工作构建了[单独的芯片](https://aws.amazon.com/ai/machine-learning/trainium/)：Trainium 用于训练，Inferentia 用于推理，Trainium3 现已投入生产并为 Anthropic 等客户提供服务。微软的 [Maia 200](https://blogs.microsoft.com/blog/2026/01/26/maia-200-the-ai-accelerator-built-for-inference/) 以推理成本为目标，而该公司同时部署 Nvidia 的 Vera Rubin NVL72 进行训练和实验——可以说是市场上最务实的双轨策略。

在所有这些公司的背后都是 Broadcom，在定制加速器和数据中心交换机的惊人需求的推动下，其 AI 半导体收入最近突破了[单季度 100 亿美元](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-first-quarter-fiscal-year-2026-financial)。 Broadcom 为 Google、Meta 和其他公司设计定制加速器，同时提供在数据中心规模连接这些加速器的 Tomahawk 和 Jericho 交换机芯片。预计到 2026 年，定制 ASIC 出货量将同比增长约 45%，是商用 GPU 增长率的三倍。

还有一些公司认为构建更好的 GPU 并不是解决方案。

Cerebras 质疑是否需要数千个互连芯片，而是选择了晶圆级处理器，将更多的工作负载保留在一块硅上。 Groq 采用了相反的方法，几乎​​完全针对推理进行优化。 SambaNova 专注于企业人工智能，构建高效服务多个模型的系统，这比发布最快的基准更重要。

### 适应性胜过原始速度

第一波生成式人工智能将奖励那些能够购买最多计算能力的人。当大多数组织都在解决同样的问题时，这是有道理的。如今，人工智能工作负载变化如此之快，以至于基础设施团队开始针对不同的方面进行优化：适应性。凯勒的例子说明了这一点。 Tenstorrent 的 BlackHole 架构使用标准以太网而不是专有互连，允许其硬件与现有 GPU 部署并存，而不是取代它们。 Keller 告诉 [EE Times](https://www.eetimes.com/jim-keller-on-tenstorrents-blackhole-scaling-and-ipo-ambitions)，一位客户使用 Tenstorrent 的 Galaxy 服务器来增加他们已拥有的 GPU 上的令牌吞吐量，而不是从头开始重建基础设施。

Tenstorrent 的方法是否成为行业标准几乎已经不重要了。

更大的想法已经在传播。在整个行业中，公司花更少的时间询问如何构建最快的人工智能硬件，而花更多的时间询问如何构建每次人工智能再次飞跃时都不需要更换的硬件。

### 现在最重要的问题

没有人知道三五年后人工智能工作负载会是什么样子。这就是问题所在。

基础设施更新周期以年为单位。人工智能模型似乎每隔几个月就会自我重塑一次。当明天可能需要不同的东西时，围绕今天的工作负载进行构建开始看起来像是一个冒险的赌注。

>

基础设施更新周期以年为单位。人工智能模型似乎每隔几个月就会自我重塑一次。

每家公司都在以自己的方式做出回应。他们有不同的策略，但仍然问同样的问题：如何构建比其上运行的人工智能更耐用的基础设施？

事实证明，这可能是比建造下一个破纪录的加速器更重要的工程挑战。正是这一挑战推动着从 Nvidia 和 AMD 到 Google、Amazon、Broadcom 和 Tenstorrent 等公司。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
