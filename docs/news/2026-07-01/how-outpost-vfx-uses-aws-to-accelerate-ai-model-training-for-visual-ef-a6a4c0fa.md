<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:37:09+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/how-outpost-vfx-uses-aws-to-accelerate-ai-model-training-for-visual-effects/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# Outpost VFX 如何使用 AWS 加速视觉效果 AI 模型训练 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:37 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | How Outpost VFX Uses AWS to Accelerate AI Model Training for Visual Effects \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/how-outpost-vfx-uses-aws-to-accelerate-ai-model-training-for-visual-effects/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在这篇文章中，我们将探讨 Outpost VFX 如何使用 AWS 基础设施将训练速度提高 8 倍，以转变其面部替换工作流程、他们为克服单 GPU 限制而实施的技术架构，以及通过 AWS 多 GPU 训练实现的可衡量结果。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## Outpost VFX 如何使用 

AWS 加速视觉效果 AI 模型训练

这篇文章是与 Outpost VFX 的 Tim Chauncey 和 Dheeraj Bhadani 共同撰写的。

视觉效果 (VFX) 的 AI 模型训练可能需要数周时间，从而造成生产时间瓶颈。 Outpost VFX 在英国、加拿大和印度设有工作室，提供高端电影和剧集内容，每天的延迟都会影响客户的交付成果和项目进度。

在这篇文章中，我们将探讨 Outpost VFX 如何使用 AWS 基础设施将训练速度提高 8 倍，以转变其面部替换工作流程、他们为克服单 GPU 限制而实施的技术架构，以及通过 AWS 多 GPU 训练实现的可衡量结果。

### 挑战：

AI 训练中的单 GPU 瓶颈

视觉效果制作中的传统面部替换工作流程需要超过 5 天的合成或专业美容和去老化支持才能创建初始版本以供导演批准。这些方法虽然有效，但会在迭代审批流程的早期（对生产时间线最关键的阶段）造成瓶颈。对于视觉特效专业人士来说，缓慢的人工智能培训会直接导致错过最后期限、增加成本和延迟客户反馈周期。

Outpost VFX 开发了一种人工智能模型，能够对现场镜头进行训练，以加速面部替换过程。然而，效率受到单 GPU 计算限制的限制。现有的换脸工具一次只能使用一个 GPU，限制了视频随机存取存储器 (VRAM) 的访问和模型训练操作的处理能力。这使得团队无法充分发挥人工智能辅助方法的潜力。

### 设计考虑

Outpost VFX 确定了优化 AI 工作流程的三个关键技术要求：- 计算可扩展性——团队需要跨多个 GPU 并行进行面部替换模型训练，以实现有意义的效率提升。单 GPU 训练导致模型迭代周期延迟一周。
- 基础设施安全 – 作为自 2022 年以来拥有完全虚拟化技术堆栈的 AWS 客户，Outpost VFX 需要该解决方案能够满足其处理高度敏感生产数据的严格安全要求。
- 性能优化——除了原始速度的提高之外，该架构还需要支持更大的数据集和更高分辨率的图像，以提高输出质量。

为了满足这些要求，Outpost VFX 与 AWS Generative AI Innovation Center 开发人员合作，这些开发人员作为其技术部门的延伸，以实现 AI 学习算法的现代化。 AWS 生成式 AI 创新中心是一个由战略家、数据科学家、工程师和解决方案架构师组成的团队，他们与客户逐步合作，构建利用生成式 AI 力量的定制解决方案。在 [生成式 AI 创新中心](https://aws.amazon.com/ai/generative-ai/innovation-center/) 网页上详细了解如何与团队互动。

### 架构实现

该解决方案涉及调整 Outpost VFX 现有的面部交换模型代码库，以支持跨多个 GPU 的分布式 GPU 训练。该实施在符合 Outpost VFX 现有基础设施要求的隔离、安全云环境中使用了 AWS 多 GPU Amazon Elastic Compute Cloud (Amazon EC2) P5 实例。

最初，Outpost VFX 在 GPU 加速工作站上训练他们的面部交换模型。这涉及收集演员及其特技替身的小型数据集，并在 RTX 3090 GPU 上微调基本模型。虽然这种方法有效，但 Outpost 团队发现训练时间很慢，每次微调大约需要 1-2 周。由于这些云工作站的管理开销，扩大规模会很困难。此时，他们研究了 P5 实例的训练。P5 实例配备 NVIDIA H100 GPU，专为分布式训练工作负载而构建。与在 GPU 之间使用 PCIe 通信的 G 系列实例不同，P5 实例提供 NV Link 互连，为梯度同步提供显着更高的带宽，这是跨多个 GPU 进行训练时的关键因素。 H100 的 14,592 个 CUDA 核心和 80GB 高带宽 HBM3 内存也代表了对其本地 RTX 3090 设置的重大升级。

Outpost VFX 与 Generative AI Innovation Center 合作，帮助他们在 P5 实例上运行模型。在为期 6 周的咨询期内，AWS 科学家将模型代码转换为使用 PyTorch 分布式数据并行 (DDP) 训练策略。 DDP 是一种并行化技术，可将模型权重复制到每个 GPU，从而允许系统在每个训练批次中处理更多图像。这种方法增加了每批可容纳的图像数量，直接加速了训练过程。

技术实施包括面部替换模型训练的多 GPU 并行化、敏感生产数据的增强安全架构以及与 Outpost VFX 现有的基于 AWS 的技术堆栈的集成。随着 Outpost VFX 不断发展其 AI 管道，该团队看到了 Amazon SageMaker AI 等服务的潜力，这些服务具有托管培训、模型版本控制和托管推理功能，可进一步简化他们在全球工作室中开发和部署模型的方式。

### 衡量性能改进

为了测试多 GPU 训练的速度提升，Outpost VFX 收集了用于训练的图像数据集，固定了模型超参数，并测量了训练达到特定损失阈值的时间。与在 P5 实例上运行模型相比，他们将基准设置为 G5 实例上的一个 GPU。

Outpost VFX 和 AWS 的联合开发工作使面部替换模型学习速度提高了 8 倍。这种性能的提高直接转化为更快的迭代周期，从而使早期版本的主管审批流程更加快速。在更高分辨率的图像和更大的数据集上训练模型的能力提高了输出质量。最重要的是，v001 交付给客户进行初步审查现在只需 2 天，而之前的时间表需要 1-2 周。

>“由于我们的并行工作流程以及同时利用多个高端 GPU 的能力，我们现在能够更快地迭代，”Outpost VFX 首席技术官 Tim Chauncey 解释道。 “迭代速度对于视觉特效工作至关重要，这种架构为未来的开发提供了更强大和可扩展的功能。”

未来的改进可能包括提高图像输出的质量。 Outpost 可以提高传递给模型的图像分辨率，并使用具有更多 VRAM 的新一代 Amazon EC2 P5 实例来处理这些更大的图像和更大的数据集。

### 结论

AWS 优化的架构使 Outpost VFX 能够为客户提供增强的人工智能辅助面部替换功能，同时保持高端视觉效果制作的安全性和可扩展性要求。并行工作流程架构包括从本地消费者 NVIDIA GPU 到企业 NVIDIA GPU 的迁移，为未来 AI 工具的开发和 Outpost VFX 全球工作室运营的扩展奠定了基础。

>

“最令我兴奋的是，这些模型不再是研究实验；它们正在成为现代 VFX 流程中不可或缺的一部分，”Outpost VFX 首席软件架构师 Dheeraj Bhadani 说道。 “多 GPU 加速是构建下一代创意工具的基础。”

### 后续步骤

如果您希望加速自己的 AI 训练工作流程，请考虑以下步骤：

- 评估您当前的 GPU 利用率：确定单 GPU 限制是否限制您的训练性能
- 探索多 GPU 架构：Amazon EC2 P5 实例为分布式训练工作负载提供可扩展计算
- 与 AWS Generative AI Innovation Center 合作：该团队曾帮助 Outpost VFX 并行化其培训工作流程

您可以通过实施根据您的特定用例和基础设施要求量身定制的分布式培训策略来实现类似的结果。

#### 致谢

作者要感谢以下贡献者对该项目的支持 Josh Chappatte、Laksh Puri 和 Ruchi Bhatia。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
