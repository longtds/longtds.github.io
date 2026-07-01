<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:00:00+08:00
source: NVIDIA Technical Blog
domain: AI 基础设施
url: https://developer.nvidia.com/blog/optimizing-a-neural-reconstruction-pipeline-using-nvidia-nsight-developer-tools/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 使用 NVIDIA Nsight 开发者工具优化神经重建流程 | NVIDIA 技术博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:00 CST |
| 领域 | AI 基础设施 |
| 来源 | NVIDIA Technical Blog |
| 原文标题 | Optimizing a Neural Reconstruction Pipeline Using NVIDIA Nsight Developer Tools \| NVIDIA Technical Blog |
| 原文 | [打开原文](https://developer.nvidia.com/blog/optimizing-a-neural-reconstruction-pipeline-using-nvidia-nsight-developer-tools/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

NVIDIA Omniverse NuRec 是一种神经重建管道，用于根据多传感器数据构建真实世界环境的高保真 3D 表示，例如...

## 正文

[开发者工具和技术](https://developer.nvidia.com/blog/category/development/)

## 使用 

NVIDIA Nsight 开发者工具优化神经重建流程

2026 年 6 月 30 日

作者：[Jackson Marusarz](https://developer.nvidia.com/blog/author/jmarusarz/) 和 [Martin Bisson](https://developer.nvidia.com/blog/author/mabisson/)

喜欢

AI 生成的摘要

喜欢

不喜欢

- NuRec 神经重建管道利用神经渲染技术（包括高斯分布）与 GPU 加速模拟集成，为模拟和机器学习工作流程创建动态场景的高保真数字孪生，但由于传感器数据量大、复杂的 PyTorch 训练和专门的 CUDA 内核，计算成本很高。
- 使用 NVIDIA Nsight Systems 和 NVIDIA Nsight Compute 进行分析，发现内核启动效率低下、同步过度以及 GPU 资源利用不足，因此需要进行重大优化，例如融合小内核、删除不必要的同步点以及拆分相机和激光雷达数据的 renderBackward 内核以提高占用率和运行时间。
- 优化减少了寄存器和共享内存的使用，将占用率从大约 15% 提高到 30-50%，并将最重内核的运行时间减半；正在进行的工作正在解决详细的扭曲活动分析所揭示的工作负载不平衡和长尾执行效应。

人工智能生成的内容可能会不完整地总结信息。验证重要信息。 [了解更多](https://www.nvidia.com/en-us/agreements/trustworthy-ai/terms/)

[NVIDIA Omniverse NuRec](https://docs.nvidia.com/nurec/) 是一种神经重建管道，用于根据摄像头和激光雷达等多传感器数据构建真实世界环境的高保真 3D 表示。它用于将[自动驾驶车辆 (AV)](https://www.nvidia.com/en-us/solutions/autonomous-vehicles/) 和机器人平台捕获的动态场景重建为模拟就绪的数字环境，可以在 [NVIDIA Omniverse](https://www.nvidia.com/en-us/omniverse/) 和相关模拟工作流程中进行渲染、重播和分析。这些重建在[物理人工智能](https://www.nvidia.com/en-us/glossary/generative-physical-ai/)和自治系统的发展中发挥着关键作用。工程师可以捕捉现实世界的驾驶或机器人场景，重建环境，然后检查或重放场景。这使他们能够更好地理解模型行为、验证感知结果、生成综合观点或为下游机器学习工作流程创建训练数据。

NuRec 将高斯泼溅等神经渲染技术与 GPU 加速渲染和模拟管道相结合，以生成高度逼真的场景重建。然而，这种保真度水平伴随着巨大的计算成本。重建和渲染工作负载涉及大量传感器数据、复杂的基于 PyTorch 的训练循环以及高度专业化的 CUDA 内核，这些内核会大量占用 GPU 资源。

本文通过一个示例来展示如何使用 [NVIDIA Nsight 开发人员工具](https://developer.nvidia.com/tools-overview) 优化 NuRec 神经重建管道。

### 解决性能优化挑战 [](https://developer.nvidia.com/blog/optimizing-a-neural-reconstruction-pipeline-using-nvidia-nsight-developer-tools/#solving_performance_optimization_challenges )

性能对于 NuRec 工作流程至关重要，因为重建周转时间直接影响工程生产力。常见的工作流程包括识别有趣或有问题的 AV 运行（例如，感知或规划堆栈表现异常的场景）并启动重建，以便工程师可以尽快检查场景。等待几个小时进行重建会显着降低迭代和调试速度。

在优化工作开始时，重建即使相对较短的捕获也可能需要一个多小时到几个小时，具体取决于场景和配置。该团队的长期目标更加雄心勃勃：实时重建性能，30 秒的捕获可以在大约 30 秒内重建。除了重建本身之外，性能也很重要。场景重建后，仅渲染工作流程可能会生成大量帧，用于强化学习 (RL)、合成数据生成 (SDG) 和大规模模拟。在这种规模下，即使是适度的性能改进也可以直接转化为 GPU 时间和基础设施成本的大幅减少。

为了应对这些挑战，使用了 NVIDIA 分析和优化工具，主要是 [NVIDIA Nsight Systems](https://developer.nvidia.com/nsight-systems) 和 [NVIDIA Nsight Compute](https://developer.nvidia.com/nsight-compute)，来分析 NuRec 工作负载、识别整个软件堆栈的瓶颈，并迭代优化应用程序级工作流程和底层 CUDA 内核。

### 使用 Nsight Systems[](https://developer.nvidia.com/blog/optimizing-a-neural-reconstruction-pipeline-using-nvidia-nsight-developer-tools/#profiling_and_optimization_using_nsight_systems) 进行分析和优化

[Nsight Systems](https://developer.nvidia.com/nsight-systems) 是一款平台分析工具，可帮助您可视化和了解工作负载的性能行为和资源利用率，包括 CPU、GPU、存储、网络等。许多性能优化工作流程的第一步是运行 Nsight Systems 配置文件来建立基线并尝试识别一些初始瓶颈或需要改进的关键领域。

为了优化训练循环，我们使用了 Nsight Systems 内置函数支持和 PyTorch 中包含的 [NVIDIA 工具扩展 SDK (NVTX)](https://github.com/NVIDIA/NVTX) 来放大图 1 中所示的前向传递的单次迭代。最初的假设是渲染内核将占用大部分运行时间，并且将是优化的最佳起点。然而，顶部的 CUDA 硬件时间线显示，大多数时间 GPU 未得到充分利用或根本没有使用。请注意顶行缺少蓝色。该应用程序还使用了比预期更多的小内核。

![Nsight Systems 配置文件时间线屏幕截图，显示一次前向传递迭代的嵌套 NVTX 范围。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201999%20500%22%3E%3C/svg%3E) 图 1. 一次前向传递迭代的 Nsight Systems 配置文件时间线初步认识之后，重要的是要更深入地研究前向传播的各个阶段，以确定时间花在哪里以及哪些阶段没有充分利用 GPU。代码中添加了额外的 NVTX 注释来描述各个阶段和功能。新的配置文件（图 2）显示“collect_gaussian_parameters”在渲染开始之前就占用了大部分时间，并且在每个前向传递中被多次调用。

![Nsight Systems 时间线屏幕截图，显示通过 NVTX 工具收集高斯参数函数占执行时间的很大一部分。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201524%20760%22%3E%3C/svg%3E) 图 2. 将“collect_gaussian_parameters”识别为执行时间的很大一部分

更深入的挖掘揭示了“插值”函数花费了多个时间（4.148 毫秒）并调用许多小内核和内存操作，这些操作导致 GPU 陷入困境，如图 3 中底部 CUDA API 行所示。

![Nsight Systems 时间线屏幕截图显示了收集高斯参数函数下的插值函数及其执行的许多小内核和内存操作。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201999%20449%22%3E%3C/svg%3E) 图 3. 将插值函数的许多小内核作为优化机会

我们深入研究了 interpolate 函数下的代码，重点关注融合小内核并向 GPU 提交更大的工作块。我们能够将所有这些工作压缩到一个内核中，将插值函数从 4.184 ms 减少到 83.81 us（图 4）。这几乎是 50 倍的加速。

![Nsight Systems 时间线屏幕截图显示插值函数下的单个融合内核。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201999%20486%22%3E%3C/svg%3E) 图 4. CUDA API 行上具有单个融合内核的插值函数接下来，我们发现了很长的“cudaStreamSynchroniz”API（在时间轴上显示为绿色条），这些 API 在 GPU 处于活动状态时会延迟 CPU 将许多小内核排队。这导致在调度和启动小内核时同步 API 返回后，顶部 CUDA 硬件行中显示的 GPU 利用率不均匀（图 5）。

![Nsight Systems 时间线屏幕截图显示了一个长 CUDA 流同步 API，后跟不完整的 GPU 执行。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201608%20950%22%3E%3C/svg%3E) 图 5. 长“cudaStreamSynchronize”（底部绿行），然后是不完整的 GPU 执行（顶部蓝行）

删除一个同步点后，其他同步点将成为瓶颈。这个过程一直持续到删除了足够多的数据，以便在 GPU 繁忙时 CPU 可以有效地将工作排入队列。这使得微小的内核能够紧凑地运行，因为它们不再受 CPU 启动时间的限制。

![Nsight Systems 时间线屏幕截图显示以前不完整的 GPU 执行现在更加精简，并且 cuda 流同步 API 消失了。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20702%20378%22%3E%3C/svg%3E) 图 6. 删除同步点后紧凑的 GPU 利用率（顶部蓝行）

减少收集参数所花费的时间并删除导致瓶颈的同步点可以深入研究一些内核优化。 Nsight Systems 使您能够识别哪些内核是最热门的。在这种情况下，“renderBackward”内核显然是最佳候选者。

![Nsight Systems 屏幕截图，显示时间线 CUDA 硬件行中的顶级内核。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20699%20144%22%3E%3C/svg%3E) 图 7. Nsight Systems 中按执行时间排列的顶级内核

### 使用 Nsight Compute[](https://developer.nvidia.com/blog/optimizing-a-neural-reconstruction-pipeline-using-nvidia-nsight-developer-tools/#kernel_optimization_using_nsight_compute) 进行内核优化[Nsight Compute](https://developer.nvidia.com/nsight-compute) 是分析和优化单个内核的最佳工具。它可以自动重放内核，使用各种类型的硬件计数器、软件补丁和仪器以非常细的粒度收集大量性能数据。它包括内置的规则系统和引导分​​析，以帮助用户识别和理解问题。

“renderBackward”内核用于相机和激光雷达数据处理。使用 Nsight Compute 对该内核的多个实例进行分析后发现，它的占用率只有约 15%，并且该内核的行为和资源需求根据正在处理的输入的不同而显着不同。

最长的三个“renderBackward”内核来自激光雷达数据，其他三个来自相机数据。尽管存在这些差异，两者都为每个线程分配 167 个寄存器（图 8）。

![Nsight Compute 摘要页面的屏幕截图，显示前 6 个内核、持续时间和资源分配。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201600%20239%22%3E%3C/svg%3E) 图 8. Nsight Compute 中 `renderBackward` 内核的六个分析实例

将顶部激光雷达内核设置为 [Nsight 计算基线](https://docs.nvidia.com/nsight-compute/NsightCompute/index.html#id8) 并比较相机内核会自动发现，虽然两者在共享内存中进行绝大多数访问，但相机内核发出的请求减少了约 75%，即使内核的激光雷达和相机实例为每个块静态分配相同数量的共享内存。

![Nsight 计算内存统计表显示激光雷达和相机内核之间共享内存访问的差异。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201288%20291%22%3E%3C/svg%3E) 图 9. 激光雷达和相机数据内核之间共享内存访问的差异

注意到“renderBackward”内核是否用于相机或激光雷达数据之间的这些行为差异，以及寄存器和共享内存分配对于两者来说都是静态且相同的事实，下一步是尝试根据是否处理相机或激光雷达数据来拆分内核。对于每个版本的内核，团队都使用 [`launch_bounds`](https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/cpp-language-extensions.html#launch-bounds) 限定符以及我们为每个块分配的共享内存量进行实验和调整寄存器分配。 [`cudaFuncSetCacheConfig`](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__EXECUTION.html#group__CUDART__EXECUTION) 运行时 API 用于设置两个内核的首选项，以拥有更大的共享内存和更小的 L1 缓存。

经过这次测试和优化，激光雷达和相机内核的寄存器分配需求分别从 167 个减少到 64 个和 128 个，并且两者都能够使用最初分配的共享内存的大约一半来高效运行。这显着提高了占用率从约 15% 到 30-50% 和整体运行时间，最长的激光雷达内核从 31 毫秒减少到 18 毫秒。

![Nsight 计算摘要页面显示将激光雷达与相机处理分离后的六个内核的性能和资源使用情况。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201866%20242%22%3E%3C/svg%3E) 图 10. 分离激光雷达和相机处理后的内核性能和配置

但仍有改进的空间。发布时正在解决的下一个问题是工作负载不平衡引起的内核长尾效应。这可以在 Nsight Compute 的 PM 采样部分中看到（图 11）。内核的前半部分显示平均有 32 个活动扭曲，这些扭曲开始逐渐减少，并且在最后几毫秒内，每个周期的活动扭曲少于一个。理想情况下，所有扭曲对于整个内核都是活跃的。

![Nsight Compute PM 采样部分显示活动扭曲的长尾，表明存在负载不平衡问题。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201999%20254%22%3E%3C/svg%3E) 图 11. Nsight Compute 中显示的长尾效应表明存在负载不平衡问题

### NVIDIA Nsight 开发者工具入门[](https://developer.nvidia.com/blog/optimizing-a-neural-reconstruction-pipeline-using-nvidia-nsight-developer-tools/#get_started_with_nvidia_nsight_developer_tools)性能分析和优化是一个迭代过程，包括运行配置文件、识别问题、修复问题以及重新开始。您可以使用 Nsight Systems 和 Nsight Compute 等工具来简化整个流程，以便在 NVIDIA GPU 上进行开发和优化。这两个工具都是免费的

- 下载 [Nsight Systems](https://developer.nvidia.com/nsight-systems) 和 [Nsight Compute](https://developer.nvidia.com/nsight-compute) 并在您自己的用例中尝试它们。如果您有疑问或想要分享您的发现，请在 [NVIDIA 开发者论坛](https://forums.developer.nvidia.com/c/developer-tools/106) 上发表评论。

#### 致谢[](https://developer.nvidia.com/blog/optimizing-a-neural-reconstruction-pipeline-using-nvidia-nsight-developer-tools/#acknowledgments)

特别感谢 NVIDIA 贡献者 Francois Trudel、Joey Lai 和 Rodolfo Lima。

喜欢

### 标签

[开发人员工具和技术](https://developer.nvidia.com/blog/category/development/) | [模拟/建模/设计](https://developer.nvidia.com/blog/category/simulation-modeling-design/) | [一般](https://developer.nvidia.com/blog/recent-posts/?industry=General) | [CUDA](https://developer.nvidia.com/blog/recent-posts/?products=CUDA) | [Nsight 工具 - 计算](https://developer.nvidia.com/blog/recent-posts/?products=Nsight+Tools+-+Compute) | [全宇宙](https://developer.nvidia.com/blog/recent-posts/?products=Omniverse) | [中级技术](https://developer.nvidia.com/blog/recent-posts/?learning_levels=Intermediate+Technical) | [最佳实践](https://developer.nvidia.com/blog/recent-posts/?content_types=Best+practice) | [自动驾驶汽车](https://developer.nvidia.com/blog/tag/autonomous-vehicles/) | [激光雷达](https://developer.nvidia.com/blog/tag/lidar/) | [物理人工智能](https://developer.nvidia.com/blog/tag/physical-ai/)

### 关于作者

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于杰克逊·马鲁萨兹
Jackson Marusarz 是 NVIDIA 计算开发工具的产品经理。他重点关注如何使用工具使所有开发人员能够轻松高效地分析、调试和优化 CUDA 代码。 Jackson 拥有科罗拉多大学博尔德分校计算机工程硕士学位。[查看 Jackson Marusarz 的所有帖子](https://developer.nvidia.com/blog/author/jmarusarz/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于马丁·比森
Martin Bisson 是 NVIDIA 的一名软件开发人员，致力于 NuRec。他的工作重点是 3D 重建和新颖视图合成的 GPU 性能，包括 3D 高斯表示、CUDA 优化和创新算法。他拥有蒙特利尔理工学院的硕士学位，他的研究重点是 3D 可视化、相机校准、多模态融合、配准和增强现实。

[查看马丁·比森的所有帖子](https://developer.nvidia.com/blog/author/mabisson/)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
