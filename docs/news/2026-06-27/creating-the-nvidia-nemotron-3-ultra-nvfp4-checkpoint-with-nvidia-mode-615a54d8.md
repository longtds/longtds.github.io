<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-27T00:00:35+08:00
source: NVIDIA Technical Blog
domain: AI 基础设施
url: https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 使用 NVIDIA 模型优化器创建 NVIDIA Nemotron 3 Ultra NVFP4 检查点 | NVIDIA 技术博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-27 00:00 CST |
| 领域 | AI 基础设施 |
| 来源 | NVIDIA Technical Blog |
| 原文标题 | Creating the NVIDIA Nemotron 3 Ultra NVFP4 Checkpoint with NVIDIA Model Optimizer \| NVIDIA Technical Blog |
| 原文 | [打开原文](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

随着上下文窗口变长，有效移动大型模型权重对于性能变得至关重要。解决这个问题的一个常见方法是量化，...

## 正文

[开发者工具和技术](https://developer.nvidia.com/blog/category/development/)

English中文

## 使用 

NVIDIA 模型优化器创建 NVIDIA Nemotron 3 Ultra NVFP4 检查点

![装饰图片。](https://developer-blogs.nvidia.com/wp-content/uploads/2026/06/Model-Optimizer.webp)

2026 年 6 月 26 日

作者：[Seonghee Lee](https://developer.nvidia.com/blog/author/seongheelee/)、[Sachin Beldona](https://developer.nvidia.com/blog/author/sbeldona/)、[Carlo del Mundo](https://developer.nvidia.com/blog/author/cdelmundo/)、[Chris Hoge](https://developer.nvidia.com/blog/author/choge/) 和 [Trenton Starkey](https://developer.nvidia.com/blog/author/tstarkey/)

喜欢

随着上下文窗口变长，有效移动大型模型权重对于性能变得至关重要。解决这个问题的常见方法是量化，这是一种将模型权重压缩为较小数据格式的优化技术。 NVFP4 是一种量化格式，它是 NVIDIA Blackwell 架构引入的一种创新的 4 位浮点格式。

这就是我们新的 Nemotron 3 Ultra NVFP4 检查点背后的方法：我们使用 NVIDIA 模型优化器将模型量化为 NVFP4。结果是，该模型在解码繁重的工作负载上的推理吞吐量比 GLM-5.1 754B FP4 模型高出 5.9 倍，同时几乎在每个基准测试中都达到 BF16 精度，如图 1 所示。

虽然 NVFP4 的性能优势已广为人知，但生成高质量 NVFP4 检查点的过程却并非如此。这篇文章介绍了我们如何使用 NVIDIA 模型优化器将 Nemotron 3 Ultra (550B) 量化为 NVFP4，并向开发人员展示如何为自己的模型生成最佳量化检查点。

![图 1 将每个 Nemotron 3 Ultra 层映射到其 BF16 基线和量化精度的表格，按层类型显示混合的 NVFP4、FP8、BF16 和 FP16 格式。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201999%201180%22%3E%3C/svg%3E) 图 1. Nemotron 3 Ultra NVFP4 与其他 NVFP4 模型相比的性能

### Nemotron 3 Ultra NVFP4 检查点[](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/#the_nemotron_3_ultra_nvfp4_checkpoint)一个常见的误解是 NVFP4 检查点的每一层都存储在 NVFP4 中。如表 1 所示，情况并非如此：不同的层被量化为不同的精度格式，根据每层对架构的敏感性及其对模型精度的影响进行选择。经过 NVFP4 量化后，Nemotron 3 Ultra 模型从 BF16 中的 1,121 GB 缩小到 352.3 GB，减少了 3.2 倍。回报是巨大的，将硬件占用空间减少了一半。

|层/运算符| BF16 基线 |量化检查点精度 |
|:---|:---|:---|
|嵌入、输出分类层、MTP 层 | BF16 | BF16 |
|教育部派遣专家| BF16 | NVFP4 |
|教育部共享专家| BF16 |每个张量 FP8 |
|曼巴搅拌机线性| BF16 |每个张量 FP8 |
|注意线性| BF16 | BF16 |
|潜在教育部 | BF16 | BF16 |
|曼巴 conv1d | BF16 | BF16 |
| KV缓存| BF16 | FP8 |
| Mamba SSM 缓存 | FP32 |具有随机舍入的 FP16 |

表 1. BF16 基线与每个层/运算符的量化检查点精度的比较 [来自 Nemotron 3 Ultra 论文](https://arxiv.org/abs/2606.15007)

Nemotron 3 Ultra NVFP4 的一项关键创新是单个检查点可以在 NVIDIA Hopper 和 Blackwell 上运行。它通过转换权重格式以匹配其运行的硬件来实现这一点。在缺少原生 FP4 张量核心的 Hopper 上，服务框架会自动切换到 W4A16。在 Blackwell 上，它使用本机 W4A4。

虽然 W8A8（8 位权重、8 位激活）似乎是 Hopper 的明显选择，但其较大的内存占用空间太小，无法适应多令牌预测 (MTP)。我们发现 MTP 只能与 W4A16 并驾齐驱（4 位权重，16 位激活），因此 W4A16 全面匹配或击败它。请阅读完整的 [Nemotron 3 Ultra 技术报告（第 4.6 节）](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Ultra-Technical-Report.pdf) 以了解更多信息。

### 我们如何找到最佳的 NVFP4 检查点[](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/#how_we_found_the_optimal_nvfp4_checkpoint)

找到最佳的 NVFP4 检查点需要一些迭代。在本节中，我们将深入探讨开发人员如何获得 NVFP4 检查点的故事。#### FP4[](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/#the_challenge_of_quantizing_at_fp4) 量化的挑战

对于 FP4 量化，只有 8 个正值 [0、0.5、1、1.5、2、3、4 和 6] 来表示整个权重块。我们需要确定如何映射原始值范围。这是由比例控制的，本质上是一个决定表示粒度的乘数。选择较差的比例意味着我们要么在小值上浪费精度，要么剪掉大值，这两者都会损害模型质量。那么我们应该如何选择最佳的比例因子呢？有几种方法。

##### 最大缩放

在这里，我们设置比例，以便块中的最大值映射到最大可表示的 FP4 值。然而，由于存在单个较大的权重异常值，最大缩放会将块中的所有其他值压缩到一个狭窄的范围内，这最终可能会将这些值刷新为零。这种信息丢失可能会对准确性产生不利影响。最大缩放保留块中的最高幅度值，具有将其他值刷新为零的潜在副作用。

![该图显示了在 absmax FP4 量化下六个小 FP32 权重崩溃至零，而单个离群值 (12.8) 幸存。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201290%201058%22%3E%3C/svg%3E) 图 2. 具有离群值的权重块上的最大 (absmax) 缩放。在 FP4 量化和反量化之后，异常值 (12.8) 设置的尺度将所有六个小权重压缩到接近 0。对于12.8，标度为absmax/6；离群值映射到 6.0 并反量化为该数字

使用 NVIDIA 模型优化器尝试一下：```
# W4A4 — NVFP4 的权重 + 激活（默认，最大缩放） model = mtq.quantize(model, mtq.NVFP4_DEFAULT_CFG,forward_loop=forward_loop)
```最大缩放（也称为“absmax”，因为缩放完全由块的绝对最大值设置）是最简单的选项，但对异常值的敏感性使其很少成为最佳选项。

这正是我们在之前的模型 NVIDIA Nemotron 3 Super 上遇到的差距：简单的“absmax”NVFP4 PTQ 留下了准确度差距，因此团队评估了一系列替代校准策略，这些策略不会让单个异常值决定尺度，从基于均方误差 (MSE) 的权重缩放到 [GPTQ](https://arxiv.org/abs/2210.17323)，这是一种使用二阶信息对权重进行编码的有效方法。

|算法|详情 | MMLU-专业版 | GPQA | LiveCodeBench | AA-LCR |
|:---|:---|:---|:---|:---|:---|
| BF16 | — | 83.49 | 79.92 | 72.907 | 72.907 53.00 |
|默认 NVFP4 PTQ（基线算法）|使用最大值校准计算静态每张量尺度；每个块的比例是根据块最大值动态计算的。 | 82.99 | 82.99 79.29 | 79.29 70.18 | 55.50 | 55.50
|每个块的重量规模最小化 MSE |扫描每个块的权重以最小化每个块的 MSE。 | 83.31 | 79.92 | 71.37 | 71.37 56.75 | 56.75
|每个块的权重可最小化输出 MSE |每个块的权重被独立扫描，以最小化 GEMM 输出 MSE。 | 83.05 | 78.98 | 71.00 | 57.06 | 57.06
| GPTQ | GPTQ (Frantar et al., 2023) 用于权重量化。 | 83.11 | 80.05 | 69.79 | 57.87 | 57.87

表 2. Nemotron 3 超级量化的实验结果。该团队尝试了多种量化方法，并评估了四项任务的准确性变化。如需了解更多信息，请参阅 [Nemotron 3 Super 论文](https://arxiv.org/abs/2604.12374)

#### 均方误差缩放[](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/#mean_squared_error_scaling)

另一种方法是均方误差（MSE）缩放，它搜索使整个块的平均重建误差最小化的缩放。

然而，较低的 MSE 并不总是意味着更好的模型精度。在我们的 Nemotron 3 Ultra 实验中，与六分之四缩放相比，MSE 校准将每个张量权重误差降低了 27.1%，但对下游基准测试没有产生一致的改进。![图表显示 MSE 缩放的 FP4 量化保留较小的权重，同时将离群值从 12.8 削减到 2.0。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201916%201210%22%3E%3C/svg%3E) 图 3. 同一块上基于 MSE 的缩放的图示，保留了具有可用分辨率的大量小权重，同时将离群值饱和到 2.0

尝试使用 NVIDIA 模型优化器进行基于 MSE 的缩放：```
model = mtq.quantize(model, mtq.NVFP4_W4A4_WEIGHT_MSE_FP8_SWEEP_CFG, forward_loop=forward_loop)
```对于我们之前的模型 NVIDIA Nemotron 3 Super，最终的量化方案将基于 MSE 的权重块缩放与每张量 FP8 扫描和基于动态最大值的激活缩放相结合。将 MSE 权重与 FP8 激活扫描相结合，可以在我们尝试过的所有方法中实现最佳的精度与尺寸权衡，并且它成为我们针对 Super 的最佳 NVFP4 配置。

Max 和 MSE 缩放都选择一个比例来最小化整体舍入误差，但都不关注误差来自网格上的位置。对于 Nemotron 3 Ultra，我们使用了一种缩放方法，该方法根据网格间隙的误差来选择范围。

#### 六分之四缩放[](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/#four-over-six_scaling)

请记住，NVFP4 只能表示 8 个正值：0、0.5、1、1.5、2、3、4 和 6。请注意，在 4 之后，下一个值会直接跳至 6。落在该范围内的任何权重都会被大幅舍入为 4 或 6，有时单个值会产生超过 13% 的误差。

![显示 FP4 可表示值在 4-6 之间的差距的范围。底部：FP4 数轴显示 4 到 6 的差距，以及随着量化阈值接近最大值而出现峰值的困惑度曲线。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201409%20858%22%3E%3C/svg%3E) 图 4. NVFP4 误差来自于舍入接近最大值。上图：FP4 可表示的值在 4 和 6 之间留下差距，舍入到该差距会导致大部分 NVFP4 错误。底部：来自[库克等人。 (2026)](https://arxiv.org/pdf/2512.02010)，Llama-3.1-8B FP4 上的模拟量化显示了量化阈值如何影响误差

六分之四解决了这个问题，因为每个权重块独立地在缩放到最大 M=4 或 M=6 之间进行选择，选择使重建误差最小化的那个。六分之四适用于权重，并在激活时回落到默认的 NVFP4。![比较 M=6 和 M=4 FP4 缩放的两个示例块，均方误差显示每个块更喜欢不同的网格。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201596%20592%22%3E%3C/svg%3E) 图 5. M=4 与 M=6 块缩放（四比六）。两个样本权重块在 M=6 和 M=4 处使用其 FP4 代码和均方误差进行量化，显示一个块倾向于 M=6，另一个块倾向于 M=4

当 M=6 获胜时，区块：[2, 4, 5.9, 6]

在 M=1 的比例下，值 2、4 和 6 精确映射到 FP4 网格点，并且只需 5.9 次舍入到 6，成本可以忽略不计。缩放到 M=4 将 2 推至 2.25，将 4 推至 4.5，从而引入误差。

当 M=4 赢得区块时：[10, 20, 30, 40]

缩放到 M=6 将 30 映射到 4.62，四舍五入为 4，误差为 13%。相反，缩放到 M=4 会将 10、20、30 和 40 精确映射到 1、2、3 和 4，整个块的舍入误差为零。 MSE：4.33 与 0.0。

Nemotron 3 Ultra 中使用四比六设置 FP4 路由专家权重尺度，将全局每个张量权重尺度提高了 1.75 倍，并且每个微块选择 M=4 或 M=6 网格。在模型的 48 个 MoE 专家层中的所有 49,152 个投影权重中，与标准最大校准相比，它将中值重建 MSE 降低了 16.4%，并在平衡的 5.03-BPE 设置中提供了最佳下游结果：相对于 BF16，中值恢复率为 98.5%，领先于最大值 (96.8%) 和 MSE (98.4%)。

尝试使用 NVIDIA 模型优化器进行四取六：```
模型= mtq.quantize（模型，mtq.NVFP4_FOUR_OVER_SIX_CFG，forward_loop=forward_loop）
````NVFP4_FOUR_OVER_SIX_CFG` 将于 7 月份在即将推出的 0.46 NVIDIA 模型优化器上发布。查看[Nemotron 3 Ultra PTQ 示例](https://github.com/NVIDIA/Model-Optimizer/tree/main/tools/launcher/examples/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16)。

#### 每个元素的位数[](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/#bits-per-element)

每个元素的有效位数（BPE）是指存储模型所有权重所需的平均位数。具有所有 BF16 权重的模型使用每个元素 16 个有效位，而半 FP8、半 BF16 模型仅使用 12 个。NVFP4 增加了每个块和每个张量的缩放开销，使其最小值达到每个元素 4.5 个有效位。每个张量尺度的 32 位在整个张量上摊销，并假设在整个 BPE 计算中可以忽略不计。

目标是寻找在不牺牲准确性的情况下尽可能降低有效 BPE 的量化配置。这很棘手，因为各层的鲁棒性并不相同。有些对量化敏感，必须保持较高的精度，这会提高有效 BPE。由于每一层都可以在不同的级别进行量化或不进行量化，因此可能的组合数量呈指数级增长，使得详尽的搜索变得不切实际，因此需要更智能的策略。

NVIDIA 模型优化器 AutoQuantize (`mtq.auto_quantize`) 会为您做到这一点。您可以为其指定目标位预算（例如“auto_quantize_bits=4.8”）和候选格式列表，例如“NVFP4_DEFAULT_CFG”和“FP8_DEFAULT_CFG”，而不是固定配置。然后，它对每个层的敏感度进行评分，并搜索以最佳精度满足预算的每层格式分配，将最敏感的层保留为更高精度的格式或完全跳过它们。```
import modelopt.torch.quantization as mtq model, search_state = mtq.auto_quantize( model, constraints={"auto_quantize_bits": 4.8}, quantization_formats=["NVFP4_DEFAULT_CFG", "FP8_DEFAULT_CFG"], data_loader=calib_dataloader, forward_step=forward_step, loss_func=loss_func,
```为了找到适合 Nemotron 3 Ultra 的每元件位数，我们扫描了从 4.85 到 7.19 有效位数每元件的五个工作点，比较了表 3 中几个基准的精度。关键信号来自 AA-LCR，从 4.85 到 5.03 将基准提高了 2.4 个点，基准性能随后再次趋于平缓，超过 5.03。这使得 5.03 BPE 成为最佳选择。

|  |量化（每个元素位数）|  |  |  |  |  |
|:---|:---|:---|:---|:---|:---|:---|
|任务|公制| 4.85 | 4.85 5.03† | 5.25 | 5.25 5.43 | 5.43 7.19 | 7.19
|编码 |  |  |  |  |  |  |
|科学代码 | pass@1 (avg-16)，子任务 acc | 43.82 | 43.88 | 43.45 | 43.45 43.27 | 43.27 43.44 | 43.44
|科学推理|  |  |  |  |  |  |
| GPQA 钻石 |通过@1（avg-32），符号。正确| 84.66 | 84.33 | 84.75 | 84.12 | 84.52 |
| HLE | pass@1，判断正确 | 24.24 | 24.24 24.84 | 24.84 25:00 | 24.98 | 24.98 25.44 | 25.44
|暴击点 | pass@1 (avg-8)，准确度 | 3.04 | 3.04 3.93 | 3.93 5.18 | 5.18 4.82 | 4.82 4.46 | 4.46
|一般|  |  |  |  |  |  |
| AA-全知| pass@1 (avg-20)，判断正确 | 29.21 | 29.21 29.75 | 29.75 29.18 | 29.18 29.29 | 29.29 29:00 |
| pass@1 (avg-20)，非幻觉 | 54.13 | 54.13 51.59 | 51.59 51.84 | 51.84 51.70 | 51.70 52.81 |  |
| IFBench |通过@1（平均8），平均。分数 | 79.34 | 79.26 | 79.83 | 79.53 | 79.83 |
|长上下文|  |  |  |  |  |  |
| AA-LCR | pass@1 (avg-16)，判断正确 | 62.25 | 62.25 64.69 | 64.69 64.19 | 64.94 | 64.94 65.00 | 65.00

表 3. 与 [Nemotron 3 Ultra 论文](https://arxiv.org/abs/2606.15007) 中的每元素有效位数相比的准确度

### 我们如何使用模型优化器将 Nemotron 3 Ultra 量化为 NVFP4 [](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/#how_we_quantized_nemotron_3_ultra_to_nvfp4_with_model_optimizer )

与 Nemotron 3 Super 120B 不同，Nemotron 3 Ultra 是 550B 型号，因此它可以从并行化量化过程中获益匪浅。因此，我们支持两种量化路径。

|两条路径均由 NVIDIA 模型优化器提供支持 |  |  |
|:---|:---|:---|
|公制|拥抱变形金刚|威震天-LM |
|计算| 4×B300 | 16×B300；专家并行度 = 数据并行度 = 16 |
|模型加载时间| 40 分钟 | < 2 分钟 |
|模型加载和校准时间| 85 分钟 | 9 分钟 |
|出口| 42 分钟 | 33 分钟 |
|总时间 | 120 分钟 | 45 分钟 |

表 4. Hugging Face Transformers 与 Megatron-LM 的量化时间比较将 Nemotron 3 Ultra 量化为 NVFP4 遵循 [NVIDIA Megatron-LM 中的 NVIDIA ModelOpt 训练后量化 (PTQ) 管道](https://github.com/NVIDIA/Megatron-LM/tree/main/examples/post_training/modelopt)。通过并行路线，预训练的检查点首先转换为 Megatron-LM 格式，然后通过一次调用“quantize.sh”进行量化，传递 NVFP4 量化配置作为配方。在后端，Megatron-LM 通过专家和数据并行性在 GPU 上对模型进行分片（16×B300 上的“EP = DP = 16”），因此校准正向传递分布在所有设备上运行。这将负载和校准从约 85 分钟减少到约 9 分钟。

校准运行“nemotron-post-training-dataset-v2”以适应每个块的比例，并且精度策略完全由配置驱动。通过将配置传递给 [`quantize.sh`](http://quantize.sh/) 来选择它。内置名称（例如“NVFP4_DEFAULT_CFG”、“FP8_DEFAULT_CFG”）或 YAML 配方路径（最终传递给“mtq.quantize(model, config,forward_loop)”来安装量化器并运行校准。

尝试使用 NVIDIA 模型优化器进行六分四缩放：```
HF_MODEL_CKPT=nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16 # 步骤 1 — 量化为 NVFP4 TP=4 \ MLM_MODEL_SAVE=/tmp/Nemotron-3-Ultra_quant \ ./quantize.sh nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16 Huggingface/models/nvidia/Nemotron-3-Ultra-550B-A55B/ptq/nvfp4-4o6 # 步骤 2 — 导出量化检查点 PP=1 \ MLM_MODEL_CKPT=/tmp/Nemotron-3-Ultra_quant \ EXPORT_DIR=/tmp/Nemotron-3-Ultra_NVFP4_46_HF \ ./export.sh nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16
```NVIDIA 模型优化器 0.46 中支持“NVFP4_FOUR_OVER_SIX_CFG”对六分之四的支持。适用于六分之四的 Nemotron 3 Ultra 配方可在 [GitHub 上获取](https://github.com/NVIDIA/Model-Optimizer/blob/db5497e2b1a5ab15a65aca9c2f157a56d5d6a276/modelopt_recipes/huggingface/models/nvidia/Nemotron-3-Ultra-550B-A55B/ptq/nvfp4-46-max.yaml)。六分之四适用于权重，并在激活时回退到默认的 NVFP4。

### 自定义量化配置[](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/#customizing_quantization_configs)

NVIDIA 模型优化器可通过不同的量化配置进行自定义。内置 NVFP4 配置范围从广泛量化的“NVFP4_DEFAULT_CFG”到更具选择性的预设，例如“NVFP4_MLP_ONLY_CFG”、“NVFP4_EXPERTS_ONLY_CFG”和“NVFP4_OMLP_ONLY_CFG”，这些预设将 FP4 限制为 MLP 和专家层，同时保持敏感注意力投影的精度。

在底层，配置是与模块名称模式匹配的规则的有序列表，“mtq.quantize()”应用它们。权重量化由针对“*weight_quantizer”模式的规则控制，您可以在其中设置格式（对于 NVFP4，具有 16 宽块和“E4M3”块比例的“E2M1”元素），而激活量化由“*input_quantizer”模式上的单独规则控制。

由于两者是独立的，因此您可以仅量化权重，也可以一起量化权重和激活，并且可以通过附加禁用特定模块的规则来为特定模块划分例外情况。对于内置预设之外的任何内容，您可以编写完整的 YAML 配方并使用“--recipe”加载它，然后完全定义定量配置。

以下 Nemotron-3 Ultra 配方将 NVFP4 与 4-6 应用于路由专家权重，将共享专家和 Mamba 投影保留在 FP8 中，使用 FP8 KV 缓存，并将其他所有内容保留在 BF16 中。完整的配方附带 NVIDIA 模型优化器的配方库：[`nvfp4-4o6.yaml`](https://github.com/NVIDIA/Model-Optimizer/blob/main/modelopt_recipes/huggingface/models/nvidia/Nemotron-3-Ultra-550B-A55B/ptq/nvfp4-4o6.yaml)```
# Nemotron 3 Ultra NVFP4 mixed-precision recipe with Four-Over-Six (4/6) # Example recipe for HuggingFace models, for Megatron-compatible recipe see the full recipe link quantize: algorithm: method: mse fp8_scale_sweep: false start_multiplier: 1.0 # M=6 (keep amax) stop_multiplier: 1.5 # M=4 (amax x 6/4) step_size: 0.5 # candidates [1.0, 1.5] quant_cfg: # Disable everything by default; later rules re-enable specific modules. - quantizer_name: '*' enable: false # MoE routed experts -> NVFP4 W4A4, block 16, e4m3 block scale. # 4/6 adaptive block scaling on weights only; not actvivations # HF names: backbone.layers.*.mixer.experts.*.{up,down}_proj - quantizer_name: '*mixer.experts.*weight_quantizer' enable: true cfg: block_sizes: {-1: 16, type: static, scale_bits: e4m3, four_over_six: true} num_bits: e2m1 - quantizer_name: '*mixer.experts.*input_quantizer' enable: true cfg: block_sizes: {-1: 16, type: dynamic, scale_bits: e4m3} num_bits: e2m1 # Shared experts + Mamba in/out_proj -> FP8 per-tensor (weights+activations). - quantizer_name: '*mixer.shared_experts*' enable: true cfg: {num_bits: e4m3, axis: null} - quantizer_name: '*mixer.in_proj*' enable: true cfg: {num_bits: e4m3, axis: null} - quantizer_name: '*mixer.out_proj*' enable: true cfg: {num_bits: e4m3, axis: null} # KV cache -> FP8. - quantizer_name: '*[kv]_bmm_quantizer' enable: true cfg: {num_bits: e4m3}
```当我们在 Nemotron 3 Ultra 上演练时，相同的管道适用于任何 Hugging Face 模型检查点。只需将模型优化器指向集线器或本地路径中的模型卡，选择一个配置（内置预设或您自己的配方），然后运行相同的量化和导出步骤即可。```
import modelopt.torch.quantization as mtq from modelopt.torch.export import export_hf_checkpoint from Transformers import AutoModelForCausalLM model = AutoModelForCausalLM.from_pretrained("<your-hf-model-card>") # 使用您选择的配置进行校准 + 量化 model = mtq.quantize(model, mtq.NVFP4_DEFAULT_CFG,forward_loop) #为TRT-LLM / vLLM / SGLang导出统一的HF检查点export_hf_checkpoint(model,export_dir="<export_path>")
```尝试一键启动器

为了简化部署，[模型优化器启动器](https://github.com/NVIDIA/Model-Optimizer/tree/main/tools/launcher) 会自动执行整个 Ultra PTQ 和导出工作流程。完成启动器自述文件中的设置步骤后，可以使用本地计算机上的单个命令通过 [Nemotron 3 Ultra YAML 配方](https://github.com/NVIDIA/Model-Optimizer/blob/main/tools/launcher/examples/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16/megatron_lm_ptq.yaml) 启动工作流程：```
uv run launch.py --yaml examples/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16/megatron_lm_ptq.yaml --yes
```启动后，假设访问具有足够 GPU 资源的 Slurm 集群，工作流程将自动处理剩余的量化和导出步骤。此示例在四个节点上进行了验证，每个节点配备了四个 NVIDIA Blackwell GPU。

对于较小规模的部署，Nemotron-3 Super 还提供了 PTQ 示例：```
uv run launch.py​​ --yaml Examples/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16
```### 开始使用[](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/#get_started)

可以使用开源 NVIDIA 模型优化器 GitHub 存储库中提供的完整配方来重现此过程。模型优化器是一个社区驱动的项目，鼓励贡献。可以提交问题来报告错误或请求功能，可以审查项目路线图以了解即将开展的工作，还可以提交拉取请求以做出改进。有关贡献指南和入门信息，请参阅“CONTRIBUTING.md”。

通过以下资源了解更多信息：

- [NVIDIA 模型优化器 GitHub](https://github.com/NVIDIA/Model-Optimizer)
- [NVIDIA 模型优化器 LLM PTQ 文档](https://github.com/NVIDIA/Model-Optimizer/tree/47a33db9b639c5d25baaa3e49526f9703491eb08/examples/llm_ptq)
- [带有 Megatron-LM 的 NVIDIA 模型优化器](https://github.com/NVIDIA/Megatron-LM/tree/main/examples/post_training/modelopt)
- [Nelotron 3 Ultra 技术报告](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Ultra-Technical-Report.pdf)
- [Nemotron 3 Ultra NVFP4 检查点](https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b/modelcard)

### 致谢[](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/#acknowledgments)

如果没有 NVIDIA 模型优化器团队和 Nemotron 团队之间的密切合作，这项工作就不可能完成。我们感谢两个团队的工程师为量化管道、评估基础设施和模型训练做出的贡献。特别感谢 Megatron-LM 团队实现大规模分布式量化，并感谢 Nemotron 团队提供用于验证 FP4 配方的基准套件。我们还感谢更广泛的 NVIDIA 研究和应用深度学习团队在整个项目中持续提供的支持和反馈。

我们特别感谢 Asma Kuriparambil Thekkumpate、Jenny Chen 和 Jinhang Choi 领导在 Nemotron 3 Ultra 上实施 NVFP4 量化。

喜欢

### 标签[代理人工智能/生成人工智能](https://developer.nvidia.com/blog/category/generative-ai/) | [开发人员工具和技术](https://developer.nvidia.com/blog/category/development/) | [MLOps](https://developer.nvidia.com/blog/category/mlops/) | [硬件/半导体](https://developer.nvidia.com/blog/recent-posts/?industry=Hardware+%2F+Semiconductor) | [Nemotron](https://developer.nvidia.com/blog/recent-posts/?products=Nemotron) | [中级技术](https://developer.nvidia.com/blog/recent-posts/?learning_levels=Intermediate+Technical) | [教程](https://developer.nvidia.com/blog/recent-posts/?content_types=Tutorial) | [NVFP4](https://developer.nvidia.com/blog/tag/nvfp4/)

### 关于作者

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于李成熙
Seonghee Lee 是 NVIDIA AI 平台软件团队的工程师，专注于 AI 推理相关产品。 Seonghee 拥有斯坦福大学计算机科学硕士学位和康奈尔大学人工智能专业理学学士学位。在加入 NVIDIA 之前，她在 Microsoft Research 工作，负责开发实时 AI 代理交互。

[查看 Seonghee Lee 的所有帖子](https://developer.nvidia.com/blog/author/seongheelee/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于萨钦·贝尔多纳
Sachin Beldona 是 NVIDIA AI 平台软件团队的工程师，专注于 LLM 推理框架和 LLM 培训库。萨钦拥有硕士学位卡内基梅隆大学机器学习博士学位和理学士学位他在德克萨斯大学奥斯汀分校获得计算机科学博士学位，专攻人工智能和机器学习。在加入 NVIDIA 之前，Sachin 曾在第一资本金融服务人工智能实验室工作，为金融服务客户开发代理人工智能解决方案。

[查看 Sachin Beldona 的所有帖子](https://developer.nvidia.com/blog/author/sbeldona/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)关于卡洛·德尔蒙多
Carlo del Mundo 是 NVIDIA 的工程总监，从事低精度数值推理和训练领域的工作。 Carlo 领导 Nemotron 量化工作。 Carlo 之前在 Apple 从事高效 ML 工作，以使性能关键的 ML 工作负载能够在 iPhone 和未来的设备上运行。卡洛拥有硕士学位拥有华盛顿大学计算机科学学士学位和理科学士学位弗吉尼亚理工大学计算机工程专业。

[查看 Carlo del Mundo 的所有帖子](https://developer.nvidia.com/blog/author/cdelmundo/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于克里斯·霍格
Chris Hoge 是 NVIDIA AI 平台软件技术营销工程团队的经理。 Chris 在开源软件领域工作了 10 多年，重点关注人工智能、高性能计算和基础设施。他拥有科罗拉多大学应用数学硕士学位和圣路易斯华盛顿大学系统科学和数学学士学位。

[查看 Chris Hoge 的所有帖子](https://developer.nvidia.com/blog/author/choge/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于特伦顿·斯塔基
Trenton Starkey 是 NVIDIA AI 平台软件团队的产品经理，专注于 NVIDIA 模型优化器。他专注于让全球的开发人员和推理合作伙伴能够使用 NVFP4 等最先进的模型优化技术。在加入 NVIDIA 之前，他曾在 Microsoft 和 Google 工作，领导平台和 AI/ML 计划。他拥有学士学位。蒙大拿大学管理信息系统专业。

[查看 Trenton Starkey 的所有帖子](https://developer.nvidia.com/blog/author/tstarkey/)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
