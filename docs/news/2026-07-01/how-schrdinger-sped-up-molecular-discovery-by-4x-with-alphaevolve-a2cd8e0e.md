<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:00:00+08:00
source: Google Cloud Blog
domain: AI 基础设施
url: https://cloud.google.com/blog/products/ai-machine-learning/schrodinger-alphaevolve-molecular-discovery-accelerates-4x/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 薛定谔如何利用 Alphaevolve 将分子发现速度加快 4 倍 |谷歌云博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:00 CST |
| 领域 | AI 基础设施 |
| 来源 | Google Cloud Blog |
| 原文标题 | How Schrödinger sped up molecular discovery by 4x with Alphaevolve \| Google Cloud Blog |
| 原文 | [打开原文](https://cloud.google.com/blog/products/ai-machine-learning/schrodinger-alphaevolve-molecular-discovery-accelerates-4x/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

计算化学研究人员在模拟分子相互作用时传统上面临着令人沮丧的权衡：使用牺牲精度的快速经典力场或依赖在大型工作中运行速度太慢的精确量子力学方法。机器学习力场 (MLFF) 通过在高保真量子数据上训练神经网络来缩小这一差距。然而，当谈到现代药物发现和材料设计时，需要更快的处理速度来处理涉及的大量化学库。为了克服此类性能限制，薛定谔与 Google Cloud 合作部署了 AlphaEvolve，这是一种由 Google De 开发的进化 AI 编码代理。

## 正文

人工智能与机器学习

##

薛定谔如何利用 Alphaevolve 将分子发现速度加快 4 倍

2026 年 7 月 1 日

![https://storage.googleapis.com/gweb-cloudblog-publish/images/schrodinger-alphaevolve-molecular-discover.max-2500x2500.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/schrodinger-alphaevolve-molecular-discover.max-2500x2500.png)

###### 卡蒂克·萨努

谷歌项目经理

###### 阿南特·纳瓦尔加里亚

Google 集团人工智能产品经理兼工程师

###### 立即尝试 

Gemini Enterprise 商业版

机器学习力场 (MLFF) 通过在高保真量子数据上训练神经网络来缩小这一差距。然而，当谈到现代药物发现和材料设计时，需要更快的处理速度来处理涉及的大量化学库。为了克服此类性能限制，薛定谔与 Google Cloud 合作部署了 [AlphaEvolve](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)，这是一种由 Google DeepMind 开发的进化 AI 编码代理，可迭代生成和完善算法，以找到克服算法瓶颈的最有效的代码路径。

#### 与 AlphaEvolve 的合作二重唱

三十多年来，薛定谔一直是科学软件开发领域的领导者，他在 MLFF 训练流程中发现了两种限制性能的关键算法：邻居列表计算和埃瓦尔德求和。这些算法聚合来自原子邻居的数据并计算远程电位，但这两者都成为训练和推理速度的限制因素。

薛定谔的主要技术目标是加快能量和力计算的人工智能模型训练。具体来说，他们的目标是埃瓦尔德求和，这是分子力学中使用的一个关键但计算要求较高的函数。 Ewald 和是薛定谔 PyTorch 代码中的主要性能限制。它没有既定的矢量化算法，并且通常依赖于在大型模拟中运行缓慢的简单 for 循环。通过将 AlphaEvolve 合并到他们的模型中，系统可以使用并行批量矩阵乘法生成 Ewald 求和的批量实现。这将改进 PyTorch 代码，使其性能优于现有的自定义内核。

#### 评估指标

薛定谔使用严格的多层评估框架来确认进化后的代码既高性能又科学准确：

-

反时限（主要指标）：核心目标是通过减少计算时间来最大化吞吐量（基线得分为 7.9）。

-

功能正确性：所有进化的程序都必须通过完整的测试套件，包括对复杂系统（例如无序水模型）的回归测试。

-

成功率：这是通过功能正确且比基线更快的程序的比例来衡量的。

“AlphaEvolve 使我们能够比以往更快、更高效地探索更大的化学空间。更快的 MLFF 推理带来真正的业务影响，缩短药物发现、催化剂设计和材料开发的研发周期，并使公司能够在几天而不是几个月内筛选候选分子。” — Gabriel Marques，薛定谔机器学习技术主管

#### 结果：4 倍加速并打破瓶颈

通过应用 AlphaEvolve，薛定谔用并行批量矩阵乘法替换了 Ewald 求和代码中的简单 for 循环。这一优化将项目成功率从不到 1%（5,000 次评估中的 40 次）提高到 60% 以上，同时将性能指标从基线 7.9 提高到近 30。

优化这些基础算法使 MLFF 训练和推理速度提高了 4 倍。这种加速使研究人员能够压缩分子筛选时间，并直接有利于几个关键研究领域：

-

药物发现：快速识别可行的治疗候选药物以满足紧急医疗需求。

-

催化剂设计：开发适合工业应用的高效化学工艺。

-

材料开发：设计具有用于电子和能源存储的定制属性的下一代材料。

#### 下一个演变

薛定谔计划将这种进化方法应用于定制 GPU 内核，以测试人工智能生成的代码是否能够超越人类设计的实现。阅读 AlphaEvolve 上的[完整技术论文](https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/AlphaEvolve.pdf)，了解进化 AI 代理如何优化科学代码库，或联系 [Google Cloud AI 团队](https://cloud.google.com/resources/global-gen-ai-contact-sales) 讨论加速您的研究工作流程。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
