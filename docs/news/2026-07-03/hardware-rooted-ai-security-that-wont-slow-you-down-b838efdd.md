<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-03T05:25:42+08:00
source: NVIDIA Technical Blog
domain: 技术动态
url: https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 植根于硬件的人工智能安全不会让您慢下来 | NVIDIA 技术博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-03 05:25 CST |
| 领域 | 技术动态 |
| 来源 | NVIDIA Technical Blog |
| 原文标题 | Hardware-Rooted AI Security That Won’t Slow You Down \| NVIDIA Technical Blog |
| 原文 | [打开原文](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

人工智能改变了组织的运作方式，推动了前所未有的生产力和创新水平。然而，人工智能的采用可能会因担忧而受到阻碍……

## 正文

[Trustworthy AI / Cybersecurity](https://developer.nvidia.com/blog/category/cybersecurity/)

## 根植于硬件的人工智能安全不会让您慢下来

NVIDIA 机密计算可提供不启用 CC 的解决方案性能 98% 的安全性

![装饰图片。](https://developer-blogs.nvidia.com/wp-content/uploads/2025/02/cybersecurity-ai-featured-1024x576.png)

2026 年 7 月 2 日

作宇：[Sheel Pethe](https://developer.nvidia.com/blog/author/spethe/)、[Vidhya Krishnan](https://developer.nvidia.com/blog/author/vidhyak/)、[Aruna Manjunatha](https://developer.nvidia.com/blog/author/amanjunatha/)、[Matheen Raza](https://developer.nvidia.com/blog/author/matheenr/) 和 [Jamie Li](https://developer.nvidia.com/blog/author/jameli/)

喜欢

AI 生成的摘要

喜欢

不喜欢

- NVIDIA 机密计算 (CC) 跨 Blackwell GPU 集成了硬件级安全性，利用融合私人签名密钥、NVLink 加密和通过 NVIDIA 远程认证服务 (NRAS) 进行远程认证等功能，确保推理过程中数据、代码和模型的完整性。
- 使用 Qwen 3.5-397B-A17B-FP8 模型对 HGX B300 进行基准测试表明，在不同的并发、批量大小和令牌长度下，启用 CC 会产生最小的吞吐量和每个令牌延迟开销（通常低于 8%），从而保持接近本机的推理性能。
- 性能优化，包括 FlashInfer 中的 CC 安全自动调整、异步 D2H 复制工作程序以及 SGLang 中的分段 CUDA 图形支持，减轻了安全工作提交和加密带宽限制的影响，从而实现适合生产规模部署且符合法规要求的安全、高性能 AI 推理。

人工智能生成的内容可能会不完整地总结信息。验证重要信息。 [了解更多](https://www.nvidia.com/en-us/agreements/trustworthy-ai/terms/)

人工智能改变了组织的运作方式，推动了前所未有的生产力和创新水平。然而，人工智能的采用可能会因数据隐私、主权以及如何在使用数据时或在人工智能模型的推理和参与过程中保护数据的担忧而受到阻碍。 NVIDIA 机密计算 (CC) 旨在成为代理 AI 时代的安全且高性能的解决方案，以安全地扩展任何模型。CC 能够在主动推理过程中保护企业数据和专有模型权重以及模型本身。 In this post, we will provide an overview of CC and demonstrate benchmarks that show its inference performance is nearly identical (up to 98%) to solutions that don’t enable CC security.

### 数据、代码和模型完整性[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#data_code_and_model_integrity)

CC 提供了一个涵盖芯片、互连和系统软件的安全层。它的工作原理如下：

![该图展示了机密计算安全层，强调了其跨芯片、互连和系统软件的集成，以确保数据和代码的完整性和机密性。](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%201824%20874%22%3E%3C/svg%3E) 图 1. 机密计算提供数据和代码的完整性和机密性

#### Hardware root of trust[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#hardware_root_of_trust)

NVIDIA Blackwell GPU（包括 NVIDIA RTX PRO 6000、HGX B200 和 HGX B300）均采用硬件中嵌入的 CC 进行设计。 HGX B200 和 HGX B300 GPU 支持通过 NVIDIA NVLink 加密跨多个 GPU（最多 8 个）进行机密计算。在芯片层面，GPU 维护着一个私有签名密钥，该密钥在制造时融合，并且永远不会暴露给软件、固件或主机系统。该密钥是证明链的基础。

#### 证明：执行前验证[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#attestation_verification_before_execution)

在机密工作负载收到任何秘密之前，它会经过远程证明。 The NVIDIA Remote Attestation Service (NRAS) verifies a signed evidence bundle—the GPU’s hardware report combined with CPU TEE measurements (AMD SEV-SNP or Intel TDX)—against a known-good reference integrity manifest (RIM).

一旦机密虚拟机 (CVM) 处于经过验证、未修改的状态，模型解密密钥等机密就可以部署到 CVM 中。证明握手通常是一次性启动事件。一旦工作负载运行，证明就不会增加单个推理请求的延迟。![Diagram showing the attestation process, where the NVIDIA Remote Attestation Service (NRAS) verifies the hardware report and CPU TEE measurements against a reference integrity manifest to validate the Trusted Execution Environment before secrets are deployed.](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20625%20267%22%3E%3C/svg%3E)

图 2. 证明服务远程验证可信执行环境的身份、配置和完整性并颁发加密证明

### Optimizing 

机密计算中的人工智能推理性能[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#optimizing_ai_inference_performance_in_confidential_computing)

CC 对 Blackwell GPU 上的 AI 推理性能的改变可能来自两个方面：

- Secure work submission latency:  For inference, secure work submission latency is often the larger factor and due to the added overhead from encryption and kernel launches, smaller units of work are more affected.增加每次 GPU 工作启动执行的工作量可以减少安全启动开销的影响。
- 减少主机到设备的 CPU 到 GPU 带宽：如果工作负载严重依赖于将输入传输到 GPU，则性能将取决于保持 GPU 充分利用所需的带宽是否超过 CC 模式下可用的加密传输带宽。

多项创新通过 CC 优化了推理性能，包括：

- CC 安全自动调谐器计时：FlashInfer 使用 GPU 全局定时器寄存器替换 CC 模式下的事件定时器，使自动调谐器能够准确比较候选内核并为每个形状选择最快的实现。
- Async D2H copy worker: SGLang moves per-step token readback off the scheduler’s critical path.这有助于恢复计算/复制重叠，因为 CC 可以在 cudaMemcpyAsync 期间使许多主机到设备和设备到主机副本有效同步。
- 分段 CUDA 图形支持：SGLang 添加了用于预填充和混合批次的 CUDA 图形重播，减少了在 CC 模式下放大的内核启动开销。

NVIDIA 继续与推理框架的上游社区合作，以确保这些框架的性能得到优化。我们测量了 CC 在不同关键指标上的推理性能。以下是有关测试设置和测量的详细信息。

### Benchmark results[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#benchmark_results)

在测试的所有工作负载配置中，启用 CC 模式在稳态推理期间产生最小的吞吐量和每个输出令牌的时间开销。

下表总结了 Blackwell Ultra (HGX B300) 型号 Qwen/Qwen3.5-397B-A17B-FP8 上的 CC 吞吐量、TTFT、TPOT 开销

#### 机密计算的相对性能[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#relative_performance_of_confidential_computing)

|并发 | ISL/OSL = 1024 / 1024 | ISL/OSL = 8192 / 1024 |  |  |
|:---|:---|:---|:---|:---|
|吞吐量/GPU (tok/s) |中位 TPOT（毫秒）|吞吐量/GPU (tok/s) |中位 TPOT（毫秒）|  |
| Δ% 与关闭 | Δ% 与关闭 | Δ% 与关闭 | Δ% 与关闭 |  |
| 4 | -2.0% | -1.6% | -3.5% | -3.6% |
| 8 | -2.6% | -2.4% | -2.8% | -2.9% |
| 16 | 16 -5.3% | -4.9% | -2.8% | -3.0% |
| 32 | 32 -6.3% | -7.8% | -1.0% | -0.9% |
| 64 | 64 -6.2% | -6.8% | -2.3% | -2.4% |
| 128 | 128 -7.5% | -8.1% | -3.5% | -3.5% |
| 256 | 256 -4.6% | -4.1% | -3.6% | -3.7% |

表 1. 启用 NVIDIA 机密计算对性能的相对影响

### Test Setup[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#test_setup)

基准：Qwen 3.5 397B-A17B 型号，FP8 精度
环境：具有 GPU 直通功能的虚拟机
基线：机密计算关闭
实验：机密计算开启

所有其他变量保持不变。

#### Hardware Configurations[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#hardware_configurations)

HGX B300 与 Blackwell Ultra。

#### Software Stack[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#software_stack)|组件|版本/详细信息 |
|:---|:---|
|平台|英特尔 TDX |
| Host OS | Ubuntu 25.10 |
|主机内核 | 6.17.0-20-generic |
|来宾操作系统 | Ubuntu 24.04.4 LTS | Ubuntu 24.04.4 LTS
|访客内核 | 6.8.0-124-通用 |
| Guest vCPUs | 256 | 256
|客座 NUMA | 2 个节点 |
| NVIDIA 驱动程序 | 595.71.05 |
| VBIOS | FW 1.4.x [97.10.64.00.0C] |
| GPU 功率限制 | 1100.00 |
| CUDA | 13.2 | 13.2
| SGlang | [docker.io/lmsysorg/sglang:v0.5.12-cu130](http://docker.io/lmsysorg/sglang:v0.5.12-cu130)PR：[28251](https://github.com/sgl-project/sglang/pull/28251) (SGLang) 和 [3638](https://github.com/flashinfer-ai/flashinfer/pull/3638) (FlashInfer) |
| NCCL | v2.28.9-1 |
| OpenSSL | 3.6.0 |
|编排| Docker Container + NVIDIA Container Toolkit |

表 2. 测试设置的软件配置

注意：请遵循本[文档](https://docs.nvidia.com/cc-deployment-guide-tdx.pdf)中描述的CPU电源和vCPU固定配置。

#### Workload Parameters[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#workload_parameters)

每个配置都在代表真实企业推理工作负载的一系列条件下进行了测试：

输入/输出令牌长度：8192/1024、1024/1024
批量大小：4、8、16、32、64、128 和 256 个并发请求。
推理框架（模式）：SGLang（服务器）
基线：不带-enable-symm-mem

#### Metrics Collected[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#metrics_collected)

每个 GPU 的输出吞吐量（令牌/秒/GPU）
获得第一个令牌的中位时间 (TTFT) — 从请求提交到生成第一个令牌的延迟（以毫秒为单位）
每个输出令牌的中位时间 (TPOT) — 稳态流中每个令牌生成延迟，以毫秒为单位

### Path forward[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#path_forward)

CC 的硬件级安全性可保护敏感的 AI 工作负载，同时保留生产 AI 工作负载所需的性能。

CC 以最小的性能开销为生产推理工作负载提供更强大的安全基础。在我们使用 SGLang 上的 Qwen 3.5 进行评估时，我们在一系列并发级别、输入序列长度和输出序列长度中观察到了这一点，证明组织可以保护其 AI 工作负载和数据，并在不影响性能的情况下保持合规性。访问以下资源，加入 NVIDIA 和我们的合作伙伴，通过 Blackwell 上的 CC 保护您的 AI 工作负载。

### Resources[](https://developer.nvidia.com/blog/hardware-rooted-ai-security-that-wont-slow-you-down/#resources)

[NVIDIA 机密计算文档](http://developer.nvidia.com/confidential-computing)
[NVIDIA Blackwell 架构白皮书](http://resources.nvidia.com/en-us-blackwell-architecture)
[NVIDIA GPU 操作员和容器工具包](http://docs.nvidia.com/datacenter/cloud-native/)
[NVIDIA 远程认证服务 (NRAS)](http://developer.nvidia.com/docs/security/attestation-sdk)
[NIST SP 800-207 零信任架构](http://csrc.nist.gov/publications/detail/sp/800-207/final)
[HIPAA 安全规则 (HHS)](http://hhs.gov/hipaa/for-professionals/security)
[GDPR 第 32 条 — 处理安全](http://gdpr.eu/article-32-security-of-processing)

喜欢

### 标签[Agentic 

AI / Generative AI](https://developer.nvidia.com/blog/category/generative-ai/) | [Data Center / Cloud](https://developer.nvidia.com/blog/category/data-center-cloud/) | [Trustworthy AI / Cybersecurity](https://developer.nvidia.com/blog/category/cybersecurity/) | [General](https://developer.nvidia.com/blog/recent-posts/?industry=General) | [Blackwell](https://developer.nvidia.com/blog/recent-posts/?products=Blackwell) | [Dynamo](https://developer.nvidia.com/blog/recent-posts/?products=Dynamo) | [NVLink](https://developer.nvidia.com/blog/recent-posts/?products=NVLink) | [TensorRT](https://developer.nvidia.com/blog/recent-posts/?products=TensorRT) | [中级技术](https://developer.nvidia.com/blog/recent-posts/?learning_levels=Intermediate+Technical) | [Best practice](https://developer.nvidia.com/blog/recent-posts/?content_types=Best+practice) | [深入探讨](https://developer.nvidia.com/blog/recent-posts/?content_types=Deep+dive) | [AI Agent](https://developer.nvidia.com/blog/tag/ai-agent/) | [人工智能推理](https://developer.nvidia.com/blog/tag/ai-inference-microservices/) | [云服务](https://developer.nvidia.com/blog/tag/cloud/) | [Code / Software Generation](https://developer.nvidia.com/blog/tag/code-software-generation/) | [Inference Performance](https://developer.nvidia.com/blog/tag/inference-performance/) | [Security for AI](https://developer.nvidia.com/blog/tag/security-ai/) | [软件定义数据中心](https://developer.nvidia.com/blog/tag/software-defined-data-center/) | [TensorRT-LLM](https://developer.nvidia.com/blog/tag/tensorrtllm/)

### 关于作者

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

About Sheel Pethe
Sheel Pethe 是 NVIDIA GPU 内核操作系统团队的高级系统软件工程师。 Drawing on a background in virtualization and memory management, he develops the low-level systems that underpin secure, high-performance confidential computing.他拥有哥伦比亚大学计算机科学硕士学位。

[查看 Sheel Pethe 的所有帖子](https://developer.nvidia.com/blog/author/spethe/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)About Vidhya Krishnan
Vidhya Krishnan 是一位杰出的架构师，也是 NVIDIA GPU 机密计算领域的首席硬件架构师。她职业生涯的大部分时间都在从事 GPU 工作。她对机密计算作为一种技术充满热情，并期待它成为默认的部署模式。

[查看 Vidhya Krishnan 的所有帖子](https://developer.nvidia.com/blog/author/vidhyak/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

About Aruna Manjunatha
Aruna Manjunatha 是 NVIDIA 系统软件总监，领导团队为高级 GPU 平台和加速计算构建基础软件。她在系统软件、软硬件协同设计、大规模平台支持方面拥有近二十年的经验，是 NVIDIA 首款保密 GPU 的关键贡献者。她拥有硕士学位in electrical and computer engineering from Carnegie Mellon University.

[查看 Aruna Manjunatha 的所有帖子](https://developer.nvidia.com/blog/author/amanjunatha/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)

About Matheen Raza
Matheen 是 NVIDIA 企业产品团队的首席产品营销经理，专注于加速计算工作负载的 NVIDIA 软件组合。 Matheen 是一名产品和 GTM 专业人士，拥有在多家公司工作的经验，包括 Amazon Web Services、Hewlett Packard Enterprise、Qubole、Infosys 和 Intel。他拥有电气工程学士学位和硕士学位（来自马德拉斯大学和科罗拉多州立大学），以及加州大学伯克利分校的 MBA 学位。

[查看 Mathen Raza 的所有帖子](https://developer.nvidia.com/blog/author/matheenr/)

![头像照片](data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%20131%20131%22%3E%3C/svg%3E)关于杰米·李
Jamie Li 是 NVIDIA 的高级技术营销工程师，专注于人工智能推理领域的最新技术。他在人工智能软件工程和客户管理方面拥有深厚的背景，能够将创新转化为实际的客户成果。在加入 NVIDIA 之前，他曾在企业技术领域担任过开发、破坏和修复 AI 解决方案的职务。他还进行了医学成像研究，并拥有专注于人工智能的计算机科学硕士学位。

[查看杰米·李的所有帖子](https://developer.nvidia.com/blog/author/jameli/)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
