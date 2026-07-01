<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T01:36:43+08:00
source: NVIDIA Technical Blog
domain: AI 基础设施
url: https://developer.nvidia.com/blog/designing-gpu-accelerated-query-engines-with-nvidia-gqe/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 使用 NVIDIA GQE 设计 GPU 加速查询引擎 | NVIDIA 技术博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 01:36 CST |
| 领域 | AI 基础设施 |
| 来源 | NVIDIA Technical Blog |
| 原文标题 | Designing GPU-Accelerated Query Engines with NVIDIA GQE \| NVIDIA Technical Blog |
| 原文 | [打开原文](https://developer.nvidia.com/blog/designing-gpu-accelerated-query-engines-with-nvidia-gqe/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

GPU 加速的查询引擎通常受到内存和 I/O 带宽的限制。 NVIDIA 硬件进步 — 包括高带宽内存 (HBM)、NVIDIA...

## 正文

[数据中心/云](https://developer.nvidia.com/blog/category/data-center-cloud/)

## 使用 

NVIDIA GQE 设计 GPU 加速的查询引擎

![装饰图片。](https://developer-blogs.nvidia.com/wp-content/uploads/2026/06/GQE-1024x576.png)

2026 年 6 月 30 日

作者：[Clemens Lutz](https://developer.nvidia.com/blog/author/clutz/)、[Tyler Allen](https://developer.nvidia.com/blog/author/tyallen/)、[Miloni Atal](https://developer.nvidia.com/blog/author/matal/)、[Viktor Rosenfeld](https://developer.nvidia.com/blog/author/vrosenfeld/) 和 [Eric Schmidt](https://developer.nvidia.com/blog/author/eschmidt/)

喜欢

AI 生成的摘要

喜欢

不喜欢

- GQE 利用现代 NVIDIA 硬件功能，例如高带宽内存、NVLink-C2C 和 NVIDIA GB200 NVL4 中的专用解压缩引擎，通过优化 CPU-GPU 数据移动、压缩和分区修剪来加速大规模 SQL 查询执行。
- 该架构采用 NVIDIA nvCOMP 库和 Blackwell 解压缩引擎的混合压缩策略，自动在每列级联和 LZ4 算法之间进行选择，以平衡解压缩吞吐量、压缩率和硬件资源利用率。
- GQE 先进的数据编排，包括高效的内存布局、管道传输、批处理 cudaMemcpyBatchAsync 和使用区域映射的主动分区修剪，最大限度地减少传输延迟和数据移动，从而在 TPC-H SF1000 基准上比最先进的 CPU 数据库实现 7.5 倍的聚合加速，每个查询增益高达 25.5 倍。

人工智能生成的内容可能会不完整地总结信息。验证重要信息。 [了解更多](https://www.nvidia.com/en-us/agreements/trustworthy-ai/terms/)

GPU 加速的查询引擎通常受到内存和 I/O 带宽的限制。 NVIDIA 硬件的进步 — 包括高带宽内存 (HBM)、[NVIDIA NVLink-C2C](https://www.nvidia.com/en-us/data-center/nvlink-c2c/) 和 [NVIDIA GB200 NVL4](https://www.nvidia.com/en-us/data-center/gb200-nvl72/) 中的专用解压缩引擎 — 通过增加有效存储容量、加速 CPU 和 GPU 之间的数据移动以及在不消耗流式多处理器 (SM) 资源的情况下加快数据访问速度，帮助消除这些瓶颈。在这篇文章中，我们将展示数据库如何使用这些技术来加速 GPU 查询执行。您将学习高效 CPU-GPU 数据移动、压缩、分区修剪以及与计算重叠数据传输的技术。

### GQE[](https://developer.nvidia.com/blog/designing-gpu-accelerated-query-engines-with-nvidia-gqe/#architecture_overview_of_gqe) 架构概述

GQE（GPU 查询引擎）是一种参考架构，旨在对现代 NVIDIA 硬件上的大型数据集执行高性能 SQL 查询。在底层，GQE 使用 [NVIDIA cuDF](https://developer.nvidia.com/topics/ai/data-science/cuda-x-data-science-libraries/cudf) 和其他 NVIDIA CUDA-X 库，包括 [CCCL](https://github.com/nvidia/cccl)、[nvCOMP](https://developer.nvidia.com/nvcomp) 和 [nvSHMEM](https://developer.nvidia.com/nvshmem)。

GQE 可以帮助影响查询引擎：

- 将执行转移到 GPU。
- 将解压移至 nvCOMP。
- 使数据格式对 GPU 友好。
- 在 GPU 上运行时缩小端到端性能差距。

![在 cuDF 和 nvCOMP 上构建的跟踪 SQL 查询的架构图，从解析和 Substrait 计划优化，到物理计划生成和任务图构建，一直到 GPU 加速的读取、连接和排序。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201920%201080%22%3E%3C/svg%3E) 图 1. SQL 查询流经 GQE 的三个架构层（查询、数据和执行），成为GPU加速

在图 1 中，我们通过将 GQE 分解为查询层、数据层和执行层来概述系统设计。它们管理从 SQL 查询和输入数据到硬件级执行的转换。这些层按如下方式组合在一起。

查询层通过 SQL 解析器和查询优化器来补充执行引擎。查询层本机接受 Substrait 计划（一种开源查询计划格式），以便在 GQE 中执行。 Substrait 可以通过从现有数据库产品导出查询计划并在 GQE 中运行该计划来评估 GPU 执行的优势。在图 2 中，Apache DataFusion 将 SQL 字符串转换为 Substrait 计划。 GQE 将该计划用作优化的逻辑查询计划，添加特定于 GQE 的细化，并将查询转换为物理计划。数据层存储和组织用户数据，以便执行器快速访问。在 GQE 中，存储被抽象为可插拔的专用读取器，可处理不同的数据格式和存储介质——目前支持 GPU 内存、CPU 内存和磁盘。在这篇文章中，我们重点关注高性能 GQE 内存表格式，并假设该数据存储在 CPU 内存中。 GQE 按需将数据块传输到 GPU，以使 GPU 充满工作，而无需将完整数据集存储在 GPU 内存中。当块到达 GPU 时，数据层将移交给执行层。

执行层针对数据执行物理查询计划以产生查询结果。 GQE 将物理计划生成为任务图，该任务图定义了执行计划。任务图包含基于开源 [NVIDIA cuDF 库](https://developer.nvidia.com/topics/ai/data-science/cuda-x-data-science-libraries/cudf) 构建的关系运算符，该运算符以高度优化的 CUDA C++ 代码实现。由于数据层以块的形式传输，GQE 可以分解运算符并在这些块上作为管道 CUDA 流同时执行任务。

综上所述，GQE 通过 GPU 原生设计释放了硬件的高吞吐量。

### 数据布局和传输编排[](https://developer.nvidia.com/blog/designing-gpu-accelerated-query-engines-with-nvidia-gqe/#data_layout_and_transfer_orchestration)

GQE 数据层经过优化，可有效地将数据从主机内存传输到设备内存。我们通过最大化吞吐量和减少移动的数据量来最小化数据传输延迟。下面，我们概述内存中的数据布局和主机到设备的传输编排，这有助于最大限度地减少传输延迟。

GQE设计目标

由于 GQE 建立在 cuDF 之上，因此设计假设 GPU 内数据的结构为 cuDF 原生表。但是，主机内存布局可以优化 NVIDIA NVLink C2C 和 PCIe 的传输。 cudaMemcpy 是标准传输方法。在这种方法中，CPU 协调 GPU 执行并以批量传输方式复制数据。这也构成了压缩传输的基础。

数据布局![内存表分为行组的图表，每个行组包含元数据和列式分区，箭头显示在 GPU 上转换为 cuDF 表。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201504%201120%22%3E%3C/svg%3E) 图 2. GQE 的内存表格式将列式数据组织为行组和分区，以便高效传输到 GPU

图 2 显示了表数据布局，它水平细分为行组。每个行组由列组成并封装元数据。在行组内，GQE 将列存储为非连续分区。在传输过程中，存储层将一组分区转换为 cuDF 列。因此，数据层向执行层隐藏了压缩和分区修剪的实现细节。

传输编排

![显示四个行组在重叠管道阶段移动的时间线，包括跨并发 CUDA 流的主机调度、H2D 传输、解压缩和 CUDA 内核执行。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20785%20306%22%3E%3C/svg%3E) 图 3. 管道并行性跨行组重叠调度、数据传输、解压缩和 GPU 执行，以加快传输速度

在图 3 中，我们展示了 CPU 如何协调传输。遵循最佳 CUDA 实践，传输使用管道并行性来有效利用硬件组件。管道传输由多个阶段组成。在压缩、分区的数据中，有四个阶段。

- 在阶段 0，主机线程执行调度。调度涉及计算要传输的内存范围、分配目标缓冲区以及调用必要的 CUDA 方法。
- 在第 1 阶段，GPU 执行 H2D 传输。
- 第 2 阶段解压缩数据。
- 第 3 阶段，添加到数据层之外，其中 CUDA 内核计算查询。

这四个阶段应该重叠。理想情况下，查询运行时间等于运行时间最长的阶段，并且所有剩余阶段都被管道隐藏。

### 数据传输优化[](https://developer.nvidia.com/blog/designing-gpu-accelerated-query-engines-with-nvidia-gqe/#data_transfer_optimizations)快速数据访问对于 GQE 实现的性能优势发挥着重要作用。采用的主要数据访问优化是压缩和分区修剪。下面，我们将描述这些优化的工作原理。

#### 压缩[](https://developer.nvidia.com/blog/designing-gpu-accelerated-query-engines-with-nvidia-gqe/#compression)

GQE 从压缩中获得两个主要好处：查询数据集容量和查询加速。压缩使查询引擎能够通过减少总体内存占用来扩展可以使用给定内存分配处理的数据集大小。压缩缓冲区的数据传输与 GPU 的快速解压缩相结合，即使在 NVLink C2C 等快速互连上也能加快传输速度。 GQE 使用 GPU 优化格式压缩数据集，与使用传统格式相比，可提高压缩率并提供卓越的 GPU 解压缩速度。

NVIDIA nvCOMP 库

[NVIDIA nvCOMP](https://developer.nvidia.com/nvcomp) 是一个用于 GPU 加速压缩和解压缩的库。它提供了一系列标准和 GPU 优化的压缩格式。用户可以从支持的算法中进行选择，以平衡压缩率、压缩和解压缩吞吐量。 nvCOMP 可以将 lz4hc 等 CPU 库封装在其高级接口中，从而提供额外的配置选项。 GQE 使用 nvCOMP 进行压缩和解压缩例程。

NVIDIA Blackwell 解压引擎

NVIDIA 在 [NVIDIA Blackwell](https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/) 架构中引入了新的解压缩引擎 (DE)，使 nvCOMP 能够快速解压缩基于 LZ77 的格式，例如 LZ4、Snappy 和 Deflate，而无需使用 SM 资源。使用多个 CUDA 流时，DE、SM 内核和 CE 副本的解压可以完全重叠。

在数据库应用程序中，单个 NVIDIA Blackwell B200 GPU 上的 DE 速度可达 400 GB/s。例如，在 4 倍压缩比下，它可实现大约 400 GB/s 的有效主机到设备吞吐量，同时保留 100 GB/s 的 C2C 主机到设备带宽可用。剩余带宽可用于传输其他数据，包括在 SM 上解压缩的编码数据。

NVIDIA GQE 的压缩方法图 4 显示了混合压缩方法，该方法使用轻量级算法（例如 [Cascaded](https://docs.nvidia.com/cuda/nvcomp/cascaded.html)）来尽可能使用结构化数据中的特定模式，并在需要基于 LZ 的算法来实现良好的压缩比时使用 DE。

![级联压缩的四面板演练：通过增量编码、游程长度编码和最后位打包成紧凑的二进制表示来减少 16 位值的原始列。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201400%20780%22%3E%3C/svg%3E) 图 4. nvCOMP 级联格式链增量编码、游程长度编码和位打包以高效压缩列式数据

当考虑如何压缩给定列时，查询引擎有几个选项。它可能要求用户为每一列指定一个算法，但这对于非常大的数据库来说很麻烦。我们采取的方法是尝试 LZ4 和 Cascaded。 LZ4 是我们针对通用数据的选择，因为与其他仅使用 LZ77 的压缩机相比，它具有较高的比率，并且受到解压引擎的支持。

为了确定要使用的压缩算法，我们使用 LZ4 和级联算法来压缩数据。级联可以实现极快的压缩率，在 B200 上约为 500 GB/s。这使我们能够尝试额外的算法，而不会在数据加载阶段产生大量开销。

我们使用两种启发法来平衡何时使用 Cascaded 与 LZ4：

- Cascaded 和 LZ4 有不同的压缩比阈值，这为我们使用该算法确定了最小值。
- 级联必须实现比 LZ4 更高的压缩比才能选择 LZ4。触发器是 LZ4 压缩比的可配置倍数。

我们使用算法的选择来帮助平衡C2C带宽、DE和SM资源。

### 分区修剪[](https://developer.nvidia.com/blog/designing-gpu-accelerated-query-engines-with-nvidia-gqe/#partition_pruning)

在将数据从 CPU 传输到 GPU 之前，GQE 采用过滤器修剪来跳过对查询结果没有贡献的分区。此机制依赖于汇总表内容和 SQL 查询中定义的谓词的元数据。

元数据和存储GQE 使用区域映射来支持过滤器修剪。当数据作为内存表加载时，GQE 将表水平拆分为行组和固定大小分区，默认为 10M 行。对于每个分区，GQE 计算每列的最小值和最大值，并将这些元数据作为 cuDF 表存储在 GPU 内存中，因此修剪可以运行而不会成为瓶颈。计算区域映射会使初始 Parquet 加载时间增加约 1%，并且仅发生一次，而不是在查询执行期间发生。

修剪和任务编排

![该图显示了查询谓词与每个分区的最小/最大区域映射元数据的比较。无法匹配的分区被剪枝；仅保留的分区会被传输并组装到 GPU 上的 cuDF 表中。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201886%201290%22%3E%3C/svg%3E) 图 5. 过滤器修剪根据分区级区域映射评估查询谓词，以在传输前跳过不相关的数据，从而减少向 GPU 的数据移动

图 5 显示了过滤器修剪过程。在任务图构建过程中，GQE 通过将查询谓词转换为与行组区域映射的比较来导出修剪表达式。无法对查询结果做出贡献的分区将被修剪。在此示例中，分区 1 被修剪，因为区域映射指示该分区中存储的所有值都小于 9，因此也小于下限 15。剩余分区将传输到 GPU 内存并在必要时解压缩。即使分区在修剪后在 CPU 内存中不连续（例如，因为它们包含在多个行组中），它们也会被传输并组装成一个连续的内存块，在 GPU 上包装为 cuDF 表。

GQE 中的过滤器修剪非常有效。在使用 1 TB 规模数据集的 TPC-H 基准测试中，过滤器修剪在所有 22 个查询中跳过了 31% 的数据。影响是端到端加速 1.43 倍。

对于 1 TB 数据的基准查询，区域映射的评估平均增加了 2.2 毫秒的最小开销。

数据传输优化

在 GQE 中，我们构思了一种新颖的分区批量传输优化。使用 cudaMemcpyBatchAsync 将多个分区一次性传输到 GPU，从而减少细粒度分区的开销。批处理还有助于避免交错 CUDA 流造成的延迟。当单独传输分区时，来自其他流的传输可能会延迟下一次内核启动。在同一批次中移动分区可以避免这种延迟。

### 性能亮点[](https://developer.nvidia.com/blog/designing-gpu-accelerated-query-engines-with-nvidia-gqe/#performance_highlights)

为了在完整的 Grace Blackwell 系统中评估上述 B200 GPU 功能，我们使用 NVIDIA GB200 NVL4 服务器中的两个 B200 GPU 之一，在比例因子 1000 (1TB) 的 TPC-H 上对 GQE 进行了基准测试，其中 B200 GPU 通过 NVLink-C2C 连接到 Grace CPU。我们使用 Turin Epyc 9755 CPU 上的 DuckDB 1.4.1 作为基准。每个查询在 5 次热缓存运行中进行平均，并在两侧启用压缩和修剪。我们调整每个查询的 GQE 参数，包括并行度和物理运算符规划。

TPC-H 数据集针对分区修剪和压缩进行了优化，方法是对 l_shipdate 上的 lineitem 表和 o_orderdate 上的订单表进行聚类，并按月对两个表进行分区。在内部，每个分区分别根据 l_orderkey 和 o_orderkey 排序。

在图 6 中，我们显示了 22 个查询的运行时间。 GQE 在 22 个查询中的 20 个上优于 DuckDB，其中在第 11 季度、第 14 季度和第 15 季度收益最大，其中分区修剪和压缩大幅减少了 NVLink C2C 上的数据移动。 GQE 展示了即使是像 Q1 和 Q6 这样的带宽密集型查询，也可以通过这些优化在 GPU 上快速执行。总之，GQE 在 9.0 秒内运行所有查询，而单插槽和双插槽配置中的 DuckDB 分别需要 74.0 秒和 70.6 秒。

![在 NVIDIA GB200 上使用 GQE 与在单路和双路 AMD Turin EPYC 9755 上使用 DuckDB 进行 TPC-H SF1000 查询第一季度至第二季度的每秒查询量的条形图比较，GQE 在超过 90% 的查询上实现了更高的吞吐量TPC-H.](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201200%20600%22%3E%3C/svg%3E) 图 6. NVIDIA 测试结果，在 1 TB 比例因子下基于 TPC-H 的超过 90% 的查询中，单个 GB200 GPU 上的 GQE 优于双路 AMD Turin CPU 上的 DuckDB![条形图显示了 NVIDIA GB200 上的 GQE 与 TPC-H SF1000 查询的最佳 CPU 配置相比的性能加速，说明了每个查询增益范围从接近奇偶校验到超过 25 倍的总计 7.5 倍加速。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201200%20600%22%3E%3C/svg%3E) 图 7. GQE 提供了 7.5 倍的总计加速超过最佳 CPU 配置，每个查询的增益范围从接近奇偶校验到超过 25 倍

我们在图 7 中展示了加速效果。与 DuckDB 的最佳 CPU 插槽配置相比，GQE 的速度提高了 25.5 倍，在 22 个查询中的 20 个上表现优于 DuckDB，并在 17 个查询上达到了 3 倍或更高。聚合所有查询后，GB200 上的 GQE 在总执行时间上实现了 7.5 倍的加速。

本博文中的测试结果源自 TPC-H 决策支持基准测试，与已发布的 TPC-H 结果不具有可比性，因为本博文中的测试结果不符合 TPC-H 规范。

### 将 GQE 最佳实践应用于数据平台[](https://developer.nvidia.com/blog/designing-gpu-accelerated-query-engines-with-nvidia-gqe/#apply_gqe_best_practices_to_data_platforms)

数据库引擎可以通过有针对性的优化将 NVIDIA Grace Blackwell 硬件功能转化为可衡量的查询性能提升。在 GQE 中，分区修剪和混合压缩可最大限度地减少传输量，而 NVLink-C2C 和 DE 硬件则可提高传输吞吐量。这些优化可减少传输时间，并使用 [NVIDIA cuDF](https://developer.nvidia.com/topics/ai/data-science/cuda-x-data-science-libraries/cudf)、[NVIDIA nvCOMP](https://developer.nvidia.com/nvcomp) 和其他 CUDA-X 库组成复杂的查询执行。

在 TPC-H SF1000 上，GQE 的总执行时间比最先进的 CPU 数据库提高了 7.5 倍，展示了如何为现代数据库引擎一起设计数据布局、压缩策略和执行。

利用 GQE [开源参考架构](https://github.com/rapidsai/gqe) 以及设计和性能优化，并探索 GQE 如何加速您的数据平台。

#### 致谢[](https://developer.nvidia.com/blog/designing-gpu-accelerated-query-engines-with-nvidia-gqe/#acknowledgements)作者要感谢 Tanmay Gujar 对 GQE 的技术贡献以及他对本文的审阅。我们还要感谢所有 GQE 贡献者——Hao Gau、Yadu Kiran、James Xia、Eyal Soha、Lingyan Yin、Daniel Juenger、Siyuan Lin、Bret Alfieri、Nico Iskos、Zhengru Wang、Rui Bao、Dhruv Sundararaman、Jiachun Li 和 Kate Cheng——的技术贡献。最后，我们要感谢 Nikolay Sakharnykh 和 Nuttiiya Seekhao 的审阅。

喜欢

### 标签

[数据中心/云](https://developer.nvidia.com/blog/category/data-center-cloud/) | [数据科学](https://developer.nvidia.com/blog/category/data-science/) | [一般](https://developer.nvidia.com/blog/recent-posts/?industry=General) | [cuDF](https://developer.nvidia.com/blog/recent-posts/?products=cuDF) | [nvComp](https://developer.nvidia.com/blog/recent-posts/?products=nvComp) | [中级技术](https://developer.nvidia.com/blog/recent-posts/?learning_levels=Intermediate+Technical) | [深入探讨](https://developer.nvidia.com/blog/recent-posts/?content_types=Deep+dive) | [CUDA-X](https://developer.nvidia.com/blog/tag/cuda-x/) | [数据分析/处理](https://developer.nvidia.com/blog/tag/accelerated-data-analytics/) | [数据库](https://developer.nvidia.com/blog/tag/databases/)

### 关于作者

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于克莱门斯·卢茨
Clemens Lutz 是 NVIDIA 的高级开发技术工程师，也是 GQE 项目的技术负责人。在加入 NVIDIA 之前，他获得了博士学位。在柏林工业大学攻读基于 GPU 的数据管理主题，并在苏黎世联邦理工学院和伦敦帝国理工学院学习。他发表的关于支持 GPU 的数据库的研究已获得 SIGMOD 和 BTW 的奖项。

[查看克莱门斯·卢茨的所有帖子](https://developer.nvidia.com/blog/author/clutz/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)关于泰勒·艾伦
Tyler Allen 是 NVIDIA 的高级开发技术工程师。在加入 NVIDIA 之前，他获得了博士学位。克莱姆森大学计算机科学博士，研究 GPU 加速系统的高性能虚拟内存管理。他的研究兴趣是利用大规模加速计算以及一般加速和分布式计算来实现新的计算能力。

[查看泰勒·艾伦的所有帖子](https://developer.nvidia.com/blog/author/tyallen/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于米洛尼阿塔尔
Miloni Atal 是 NVIDIA 的高级开发技术工程师。她的工作重点是并行计算、数据库系统和性能优化。她获得了硕士学位哥伦比亚大学计算机科学专业，主修软件系统，之前还获得了航空航天工程学士学位。

[查看 Miloni Atal 的所有帖子](https://developer.nvidia.com/blog/author/matal/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于维克多·罗森菲尔德
Viktor Rosenfeld 是 NVIDIA 的一名开发技术工程师，专注于加速 GPU 上的数据分析。在加入 NVIDIA 之前，他获得了博士学位。在柏林工业大学，主题是异构系统上的查询处理。

[查看 Viktor Rosenfeld 的所有帖子](https://developer.nvidia.com/blog/author/vrosenfeld/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

关于埃里克·施密特
Eric Schmidt 是 NVIDIA 的高级开发技术工程师。他专注于加速 GPU 上的数据分析应用程序。在 2021 年加入 NVIDIA 之前，Eric 在航空航天行业工作了 11 年，负责开发软件和研究应用数学算法。

[查看埃里克·施密特的所有帖子](https://developer.nvidia.com/blog/author/eschmidt/)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
