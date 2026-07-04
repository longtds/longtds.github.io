<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-04T08:00:58.739803+08:00
source: 美团技术团队
domain: AI 基础设施
url: https://tech.meituan.com/2026/06/18/2026-ASX.html
content_mode: full-translated
original_language: zh
extraction_status: html-heuristic
-->

# 美团技术团队顶会论文分享：搜索推荐ASX专场

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-04 08:00 CST |
| 领域 | AI 基础设施 |
| 来源 | 美团技术团队 |
| 原文标题 | 美团技术团队顶会论文分享：搜索推荐ASX专场 |
| 原文 | [打开原文](https://tech.meituan.com/2026/06/18/2026-ASX.html) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

美团业务研发平台/搜推 ASX (Agentic System X)团队聚焦构建大模型为基础的 Agent 技术体系，在大模型后训练、Agentic 强化学习以及多模态理解等核心前沿方向持续深耕，已在 ICLR、NeurIPS、CVPR、AAAI 等 AI 领域的国际顶会发表数十篇高质量研究成果。本文精选了6篇进行解读，希望对大家有所帮助或启发。

## 正文

![美团技术团队顶会论文分享：搜索推荐ASX专场](https://p0.meituan.net/meituantechblog/324af03d23fb20dbce75795e103d8f6f232410.jpg)

## 美团技术团队顶会论文分享：搜索推荐ASX专场

美团技术团队 2026-06-18

算法大模型论文解读

美团业务研发平台/搜推 ASX (Agentic System X)团队聚焦构建大模型为基础的 Agent 技术体系，在大模型后训练、Agentic 强化学习以及多模态理解等核心前沿方向持续深耕，已在 ICLR、NeurIPS、CVPR、AAAI 等 AI 领域的国际顶会发表数十篇高质量研究成果。本文精选了6篇进行解读，希望对大家有所帮助或启发。

### [01 Contextual Rollout Bandits for Reinforcement Learning with Verifiable Rewards](https://tech.meituan.com/2026/06/18/2026-ASX.html#_01-contextual-rollout-bandits-for-reinforcement-learning-with-verifiable-rewards)

上下文轨迹老虎机：面向可验证奖励的强化学习

论文下载：[PDF](https://arxiv.org/abs/2602.08499)

论文简介：现有基于规则奖励的强化学习后训练通常直接使用最近一轮 rollout 进行策略优化，其中，低质量样本会引入噪声，高质量样本又常在单次使用后被丢弃，导致训练不稳定、样本利用不足。本文提出在线样本调度算法 CBS，将样本选择建模为上下文多臂老虎机问题，把每个候选样本视为 arm，并以训练后带来的性能增益作为奖励；通过轻量神经网络预测样本价值，并结合在线反馈动态调度。实验表明，CBS 可与多种策略优化方法结合，在 6 个数学推理数据集上稳定提升性能和训练效率。

### [02 ResRL: Boosting 

LLM Reasoning via Negative Sample Projection Residual Reinforcement Learning](https://tech.meituan.com/2026/06/18/2026-ASX.html#_02-resrl-boosting-llm-reasoning-via-negative-sample-projection-residual-reinforcement-learning)

ResRL：通过负样本投影残差强化学习提升大语言模型推理能力

论文下载：[PDF](https://arxiv.org/abs/2605.00380)

论文简介：本文提出 ResRL，一个负样本强化学习的新算法，旨在解决RLVR 提升LLM推理能力却损伤了输出多样性的问题。我们发现根因是惩罚负样本时误伤了正负样本共享的有效语义。ResRL 用 SVD 正确子空间 +投影残差，让惩罚只打在“真正的错误方向”上--数学超 NSR 9.4%、代码刷新 CodeForces SOTA、ALFWorld 超 PPO 7.8%，且 Pass@1 与 Pass@k 兼得。

### [03 CDRRM: Contrast-Driven Rubric Generation for Reliable and Interpretable Reward Modeling](https://tech.meituan.com/2026/06/18/2026-ASX.html#_03-cdrrm-contrast-driven-rubric-generation-for-reliable-and-interpretable-reward-modeling)

CDRRM：对比驱动的评分准则生成以实现可靠且可解释的奖励建模

论文下载：[PDF](https://arxiv.org/abs/2603.08035)

论文简介：本文提出 CDRRM，一个对比驱动的评分准则生成与奖励建模框架，旨在提升LLM对齐中奖励模型的可靠性、可解释性与数据效率。传统奖励模型是“黑箱”且依赖昂贵标注；现有准则方法存在冗余与偏见。CDRRM采用“对比-聚合”流程：先对比好/差回答定位关键差异，再聚合为简洁的任务相关准则，指导评判模型。实验表明，CDRRM在三个基准上达最先进水平，缓解话痨、位置等偏见，且仅用3千样本让未微调模型超越全量微调基线，兼具高效与可解释性。

### [04 LocalSearchBench: Benchmarking Agentic Search in Real-World Local Life Services](https://tech.meituan.com/2026/06/18/2026-ASX.html#_04-localsearchbench-benchmarking-agentic-search-in-real-world-local-life-services)

LocalSearchBench:真实本地生活服务中的智能体搜索基准评测

论文下载：[PDF](https://arxiv.org/abs/2512.07436)

论文简介：本文针对本地生活服务领域智能体搜索的研究空白，构建LocalSearchBench评测基准。该基准涵盖国内 9 座城市、6 大服务品类，包含超 134 万商户数据与 900 道用户多跳问答任务，同时配套交互环境 LocalPlayground 与商户检索工具 LocalRAG。实验测评 16 款主流大语言推理模型后发现,当前模型在此类任务表现不佳，最优模型 DeepSeek-V3.2 答题正确率仅 35.60%，普遍存在信息完整性、可信度不足等问题。研究还剖析了模型工具调用、多跳推理等典型缺陷，为本地生活服务场景下智能体搜索的模型训练和基准测试提供了重要支撑。

### [05 DiningBench: A Hierarchical Multi-view Benchmark for Perception and Reasoning in the Dietary Domain](https://tech.meituan.com/2026/06/18/2026-ASX.html#_05-diningbench-a-hierarchical-multi-view-benchmark-for-perception-and-reasoning-in-the-dietary-domain)

DiningBench：饮食领域感知与推理的层次化多视角基准

论文下载：[PDF](https://arxiv.org/abs/2604.10425)

论文简介：本论文提出 DiningBench，一个面向饮食领域的层次化多视角 VLM 评测基准，旨在弥补现有数据集任务单一、视角有限和营养标注不足的问题。该基准包含细粒度分类、营养估计和视觉问答三类任务，覆盖 3,021 道菜品和多视角图像。通过评测 29 个主流VLM模型，揭示现有模型在细粒度识别、营养推理和多视角融合上的不足。

### [06 Mem²Evolve: Towards Self-Evolving Agents via Co-Evolutionary Capability Expansion and Experience Distillation](https://tech.meituan.com/2026/06/18/2026-ASX.html#_06-mem2evolve-towards-self-evolving-agents-via-co-evolutionary-capability-expansion-and-experience-distillation)

Mem2Evolve：通过协同进化能力扩展与经验蒸馏实现自进化智能体

论文下载：[PDF](https://arxiv.org/abs/2604.10923v1)

论文简介：本文提出 Mem2Evolve，一个面向大语言模型智能体的自进化框架，通过 Asset Memory 与 Experience Memory 双记忆机制，协同实现能力扩展与经验积累。该框架可在任务执行中动态复用或创建工具与专家智能体，并从成功和失败轨迹中蒸馏可迁移经验。实验覆盖 6 类任务、8 个基准，结果表明 Mem2Evolve 显著优于普通 LLM 及单一进化策略，展现出更强的持续学习与任务泛化能力。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
