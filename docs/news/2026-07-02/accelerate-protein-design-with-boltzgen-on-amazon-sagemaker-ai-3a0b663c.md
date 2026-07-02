<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T01:44:08+08:00
source: AWS ML Blog
domain: 技术动态
url: https://aws.amazon.com/blogs/machine-learning/accelerate-protein-design-with-boltzgen-on-amazon-sagemaker-ai/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 在 Amazon SageMaker AI 上使用 BoltzGen 加速蛋白质设计 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 01:44 CST |
| 领域 | 技术动态 |
| 来源 | AWS ML Blog |
| 原文标题 | Accelerate protein design with BoltzGen on Amazon SageMaker AI \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/accelerate-protein-design-with-boltzgen-on-amazon-sagemaker-ai/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在这篇文章中，我们演示了如何在 SageMaker AI 上部署 BoltzGen 并运行端到端蛋白质设计实验。在演练结束时，您将拥有一个可从快速验证运行扩展到生产批处理的工作设置。该设置为不同的研究阶段提供了两种执行模式，并使用步骤级缓存来减少迭代工作流程期间的计算费用。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 在 

Amazon SageMaker AI 上使用 BoltzGen 加速蛋白质设计

[Amazon SageMaker AI](https://aws.amazon.com/sagemaker/ai/) 上的 [BoltzGen](https://github.com/HannesStark/boltzgen) 通过端到端管理 GPU 计算基础设施来加速蛋白质结合剂设计。 [BoltzGen](https://boltz.bio/boltzgen) 是一种基于扩散的生成模型，可设计能够与特定生物分子靶标结合的蛋白质和肽。典型的设计活动涉及多个 GPU 密集型步骤：主干生成、反向折叠、结构验证和候选排序。在数百、数千甚至数百万的设计候选中运行这些步骤会在配置实例、在步骤之间移动数据以及跟踪成本方面带来运营开销。 SageMaker AI 管理从实例配置到结果交付和资源清理的计算生命周期，因此您可以专注于设计迭代而不是基础设施运营。

在这篇文章中，我们演示了如何在 SageMaker AI 上部署 BoltzGen 并运行端到端蛋白质设计实验。在演练结束时，您将拥有一个可从快速验证运行扩展到生产批处理的工作设置。该设置为不同的研究阶段提供了两种执行模式，并使用步骤级缓存来减少迭代工作流程期间的计算费用。

本演练适用于学术研究实验室、生物技术初创公司、药物研发团队和教育项目，无论您从事蛋白质结合剂设计、治疗性蛋白质工程还是从头蛋白质结构工作。

#### SageMaker 

AI 如何解决蛋白质设计瓶颈

BoltzGen 活动中的每一步都在 GPU 硬件上运行，并一次处理一个设计规范。根据存储库的基准数据，在 4-GPU 实例 (`ml.g5.12xlarge`) 上，1,000 个样本的活动大约需要 375 小时才能完成。操作此基础设施涉及构建 CUDA 环境（例如安装 CUDA 驱动程序和设置工具包）、协调 GPU 实例生命周期、在步骤之间构建数据管道以及从长时间运行的作业中的故障中恢复。SageMaker AI 直接解决了这些瓶颈。提交作业后，SageMaker AI 会配置 GPU 实例并在容器内执行 BoltzGen。它将结果写入 [Amazon Simple Storage Service](https://aws.amazon.com/s3/) (Amazon S3)，并在处理完成时释放实例。按秒计费，因此没有闲置 GPU 成本。根据[按需定价](https://aws.amazon.com/sagemaker/pricing/)，在“ml.g4dn.xlarge”上运行 2 小时的设计费用约为 1.50 美元。

该实现支持单个实例内的多 GPU 并行化以及跨管道的多实例扩展。在管道模式下，每个步骤的输出都缓存在 Amazon S3 中，有效期为 7 天，因此当您迭代过滤参数时，占计算成本约 90% 的设计生成步骤不会重新运行。

存储库中的设置脚本构建容器并将其推送到 [Amazon Elastic Container Registry](https://aws.amazon.com/ecr/) (Amazon ECR)，工作示例可让您在几分钟内提交第一个设计作业。验证具有 10 个候选者的设计规范的相同配置可以扩展到更大的活动 - 只是参数值发生变化。实例类型范围从“ml.g4dn”（成本最低的 T4 GPU）到“ml.g6e”（NVIDIA L40S GPU），让您可以灵活地将吞吐量与预算相匹配。

#### BoltzGen 提供什么

BoltzGen 是一种全原子生成模型，用于设计可与多种生物分子靶标结合的蛋白质和肽。该模型通过扩散过程生成粘合剂骨架结构。然后，它使用称为 BoltzIF 的反向折叠模型生成氨基酸序列，并使用 [Boltz2 折叠预测](https://github.com/jwohlwend/boltz) 验证结构。

该实现可在 [GitHub 上的 Boltzgen on SageMaker 存储库](https://github.com/aws-samples/sample-biofm-quickstart/tree/main/models/boltzgen/inference/amazon-sagemaker/boltzgen-on-sagemaker-processing-job-cli) 中找到。该存储库包括设置脚本、两种执行模式、多 GPU 和多实例扩展支持以及快速入门指南。

#### 两种执行模式

我们在实施中提供了两种执行模式，针对不同的研究阶段进行了优化，因此您可以从快速实验开始，并随着需求的增长逐步过渡到生产工作流程。[SageMaker AI 处理作业](https://docs.aws.amazon.com/sagemaker/latest/dg/processing-job.html) 提供直接批处理执行以进行快速实验。提交作业后，SageMaker AI 会配置 GPU 实例、运行容器并在完成后关闭实例。单个 Python 脚本即可触发整个工作流程，无需多步骤编排。对于早期工作，其目标是在扩大规模之前测试设计规范，处理作业可以最大限度地减少设置时间。

[SageMaker AI Pipelines](https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines-overview.html) 在 SageMaker AI Studio 中提供了 5 步精心策划的工作流程，其中包括步骤级缓存、自动缩放和可视化监控。生产工作负载受益于参数迭代，而无需重新运行昂贵的计算步骤。每个步骤（设计、逆折叠、折叠、分析、过滤）都可以独立缩放，并且在输入未更改时重用缓存的结果。

两种模式都遵循相同的工作流程。 Amazon ECR 中的容器在预配置的 GPU 实例上运行，BoltzGen 处理设计规范，SageMaker AI 在关闭计算资源之前将结果存储在 Amazon S3 中。

#### 开始使用

首先，您需要一个 AWS 账户、本地安装的一些工具以及用于存储数据的 Amazon S3 存储桶。以下部分将引导您完成每个先决条件，然后指导您完成第一个蛋白质设计实验。

##### 先决条件

确保您拥有启用了计费功能的有效 AWS 账户，并且安装并配置了 [AWS 命令行界面](https://aws.amazon.com/cli/) (AWS CLI) (`aws configure`)。验证您的目标 AWS 区域（例如“us-east-1”）中的 GPU 实例（“ml.g4dn.xlarge”或更高）是否有足够的服务配额（例如，本演练为 1）。

接下来，为 SageMaker AI 创建 [AWS Identity and Access Management](https://aws.amazon.com/iam/) (IAM) 执行角色。附加“AmazonSageMakerFullAccess”托管策略，授予 Amazon S3 对数据存储桶的读/写访问权限，并授予 Amazon ECR 对 BoltzGen 容器映像的拉取权限。

在本地计算机上，安装带有 pip 的 Python 3.11+、最新的 Boto3 和 SageMaker SDK（“pip install boto3 sagemaker”）以及用于构建容器映像的 Docker。最后，在您的目标区域创建一个 Amazon S3 存储桶：```
aws s3 mb s3://amzn-s3-demo-bucket --region <aws-region>
```#### 运行你的第一个蛋白质设计

为了获得最简化的设置体验，我们建议使用 [Amazon SageMaker Studio](https://aws.amazon.com/sagemaker/ai/studio/) 或 [Amazon SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html) 实例。这些环境预配置了 AWS 凭证、SageMaker SDK 和 Docker 支持。

##### 启动 SageMaker 

AI Studio

首先打开 SageMaker AI Studio，您可以在其中运行设置和实验命令。

- 打开 [SageMaker AI 控制台](https://console.aws.amazon.com/sagemaker/)。
- 从左侧导航中选择 Studio。
- 创建一个新的 Studio 域（如果不存在）或打开现有域，使用 AWS CLI [通过本地模式启用 Docker 访问](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-local-get-started.html)。
- 使用实例启动 JupyterLab 空间（例如“ml.m5.2xlarge”）。
- 将“ml.g4dn.xlarge”和“ml.g5.xlarge”处理作业使用的配额限制提高到大于 0。

##### 克隆存储库

下载 BoltzGen on SageMaker AI 代码，其中包括设置脚本、执行模式和示例设计规范。```
git clone https://github.com/aws-samples/sample-biofm-quickstart.git cd sample-biofm-quickstart/models/boltzgen/inference/amazon-sagemaker/boltzgen-on-sagemaker-processing-job-cli
```##### 构建并推送容器镜像

您的容器映像将 BoltzGen 及其依赖项和 GPU 驱动程序打包在一起。构建一次并在实验中重复使用。设置您的区域并运​​行构建脚本：```
导出 AWS_REGION=<aws-region> ./sagemaker/build_and_push.sh
```##### 配置AWS凭证

SageMaker AI 需要您的 AWS 账户详细信息来预置计算资源并将结果存储在 Amazon S3 中。复制环境模板并填写您的设置：```
cp sagemaker/pipeline/.env.example sagemaker/pipeline/.env vim sagemaker/pipeline/.env
```示例 `.env`：```
AWS_REGION=us-east-1 AWS_S3_BUCKET=amzn-s3-demo-bucket AWS_ROLE_ARN=arn:aws:iam::<aws-account-id>:role/SageMakerExecutionRole AWS_IMAGE_URI=<aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/boltzgen-sagemaker:最新
```现在您已准备好运行您的第一个设计工作，有两个选项：

选项 A：快速试验单个处理作业中的所有步骤：```
python sagemaker/run_processing_job.py \ --design-spec example/vanilla_protein/1g13prot.yaml \ --s3-bucket amzn-s3-demo-bucket \ --instance-type ml.g4dn.xlarge \ --num-designs 10 \ --budget 2 \ --wait
```您可以使用扩散模型生成 10 个中间候选设计，它们是经过反向折叠、重新折叠、分析和过滤的原始主干结构。实际上，对于实际运行来说，这个数字应该更高，例如 10,000 到 60,000。最终的多样性优化输出集有两种设计。因此，在 10 个中间设计中，只有两个针对质量和序列多样性进行了优化的设计最终会出现在您的输出文件夹中。

选项 B：更加类似于生产的工作流程，编排管道中的不同步骤。

更改管道目录：```
cd sagemaker/pipeline
```创建管道：```
python run_pipeline.py --config pipeline_config.yaml create
```按设计规范运行：```
python run_pipeline.py --config pipeline_config.yaml 运行
```检查状态（将 Amazon 资源名称 (ARN) 替换为执行 ARN）：```
python run_pipeline.py --region us-east-1 status --execution-arn <ARN>
```##### 下载结果

对于加工作业：```
aws s3 同步 s3://amzn-s3-demo-bucket/boltzgen/output/boltzgen-TIMESTAMP ./results
```对于管道：```
aws s3 sync s3://amzn-s3-demo-bucket/boltzgen-pipeline/output/TIMESTAMP ./results
```输出目录包含多个子目录。 `final_ranked_designs/` 保存按预测的结合亲和力排名的顶级设计。 `intermediate_designs/` 包含生成的候选结构。 `metrics/` 存储结构分析数据，包括均方根偏差 (RMSD) 和接触分数。 “job_metadata.json”文件记录了完整的作业参数和状态。

以下目录树显示了针对 1G13 目标使用“--num-designs 100 --budget 10”运行的输出结构：```
results/1g13prot/ ├── Final_ranked_designs/ │ ├── Final_10_designs/ # 因多样性和质量而选出的最佳设计 (.cif) │ ├── middle_ranked_10_designs/ # 按质量得分排名的最佳设计 (.cif) │ ├── all_designs_metrics.csv # 所有设计的完整指标表 │ ├── Final_designs_metrics_10.csv # 最终选定设计的指标 │ └── results_overview.pdf # 包含过滤标准和绘图的摘要报告 ├── middle_designs/ # 所有生成的主干结构 (.cif) ├── middle_designs_inverse_folded/ # 序列设计和重新折叠后的结构 └── config/ # 用于重现性的步骤配置
```BoltzGen 自动过滤和排序所有生成的设计。每个设计在进入排名阶段之前都必须通过结构质量阈值，包括低于 2.5 埃的重折叠 RMSD 和平衡的氨基酸组成。在此运行中，100 个设计中有 3 个通过了所有筛选。然后，管道根据综合质量得分对设计进行排名，并应用多样性优化来选择最终的集合。

下表显示了具有关键指标的前五名设计。较高的“design_ptm”和“design_iptm”分数表示较高的结构置信度和结合强度。较低的“filter_rmsd”表示重折叠后更好的结构精度，较高的“delta_sasa”表示更大的结合界面。

|编号 |排名|设计_ptm |设计_iptm |过滤器均方根值 | delta_sasa |
|:---|:---|:---|:---|:---|:---|
| 1g13prot_24 | 1g13prot_24 1 | 0.760 | 0.760 0.304 | 0.304 2.24 | 2.24 584.7 | 584.7
| 1g13prot_37 | 1g13prot_37 2 | 0.732 | 0.732 0.275 | 0.275 1.98 | 1.98 657.4 | 657.4
| 1g13prot_21 | 1g13prot_21 3 | 0.748 | 0.748 0.159 | 0.159 2.49 | 2.49 535.7 | 535.7
| 1g13prot_06 | 1g13prot_06 4 | 0.736 | 0.736 0.426 | 0.426 1.34 | 1.34 1598.0 |
| 1g13prot_59 | 1g13prot_59 5 | 0.763 | 0.763 0.527 | 0.527 1.05 | 1.05 2369.0 | 2369.0

每个最终设计都保存为带有排名前缀的“.cif”结构文件（例如“rank001_1g13prot_24.cif”），为下游分析或实验验证做好准备。

现在您的第一个实验已经完成，以下部分将探讨 SageMaker AI 上的 BoltzGen 如何在幕后工作，以便您可以根据您的特定需求优化架构。

#### 它是如何工作的

了解两种执行模式背后的架构和扩展功能有助于您选择正确的实例类型并在单实例和多实例配置之间做出决定。它还可以帮助您充分利用缓存来降低成本。

##### 架构

通过处理作业模式（单步批处理），SageMaker AI 在您提交作业后协调实例配置、容器执行、Amazon S3 数据移动和清理。您的工作流程遵循以下步骤：

![处理作业模式的架构图，显示 SageMaker AI 预置 GPU 实例、针对 Amazon S3 输入数据执行 BoltzGen 容器以及将结果写回 Amazon S3](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/17/ML-20375-1.png)- 准备设计规范 (YAML) 和参考结构文件。
- 将您的文件上传到 Amazon S3。 SageMaker AI 将 Amazon S3 输入数据装载到您的容器中。
- BoltzGen 生成设计并将结果写回 Amazon S3。
- 从 Amazon S3 下载最终结果。

在管道模式（5 步工作流程）下，管道运行五个连续步骤，每个步骤都可以单独扩展：

![管道模式架构图显示五个连续步骤：设计、反向折叠、折叠、分析和过滤，以及 Amazon S3 中缓存的中间输出](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/17/ML-20375-2.png)

- 设计（GPU）：扩散模型生成粘合剂主干结构。
- 反向折叠 (GPU)：BoltzIF 生成氨基酸序列。
- 折叠 (GPU)：Boltz2 验证复杂结构。
- 分析 (CPU)：计算结构指标（RMSD、溶剂可及表面积 (SASA) 和接触）。
- 过滤（CPU）：排名并选择顶级设计。

您的管道将每个步骤的输出缓存在 Amazon S3 中，有效期为 7 天。当输入未更改时，会自动重用缓存的结果，因此当您迭代过滤参数时，将完全跳过昂贵的设计生成步骤。

##### 跨 

GPU 和实例扩展

SageMaker AI 上的 BoltzGen 支持两种互补的扩展策略，可帮助您平衡成本和吞吐量。

多 GPU 并行化通过循环调度在单个实例中跨 GPU 分配设计规范。每个 GPU 使用“ProcessPoolExecutor”（Python 的内置并行处理库）独立处理其指定的规格，并通过“ProgressTracker”类进行线程安全的进度跟踪。 GPU 检测是通过“nvidia-smi”自动进行的。

例如，在 4 个 GPU 的“ml.g5.12xlarge”实例上，10 个设计规范分布如下：```
10 design specs -> GPU0: specs 0,4,8 | GPU1: specs 1,5,9 | GPU2: specs 2,6 | GPU3: specs 3,7
```单个多 GPU 实例比多个单 GPU 实例更高效，因为 BoltzGen 加载大约 5 GB 的模型权重。一个多 GPU 实例可避免冗余模型加载，从而减少启动时间和内存开销。

多实例扩展将并行性扩展到单机之外。管道模式下，每个步骤都支持多实例执行。工作会自动分区。例如，实例0处理规格的前半部分，实例1处理规格的后半部分。然后，每个实例在其自己的 GPU 上进一步并行化。```
def get_worker_info() -> Tuple[int, int]: """从 SageMaker 环境中自动检测工作人员 ID。""" Hosts_str = os.environ.get("SM_HOSTS", "") current_host = os.environ.get("SM_CURRENT_HOST", "") 如果hosts_str 和 current_host：hosts = json.loads(hosts_str) instance_count = len(hosts)worker_id=hosts.index(current_host)returnworker_id,instance_countreturn0,1#默认单实例
```##### 步骤级缓存

管道模式根据输入哈希缓存每个步骤的输出，有效期为 7 天。由于设计步骤约占计算成本的 90%，因此缓存可以在迭代工作期间节省大量成本。仅更改过滤参数只会触发过滤步骤的重新运行，同时保留缓存的设计输出。```
# pipeline.py configuration cache_config=CacheConfig( enable_caching=True, expire_after="7d" # 7-day expiry )
```##### 容器、配置和实现

您的 Docker 映像 (`Dockerfile.sagemaker`) 是基于 NVIDIA CUDA 12.2 和 cuDNN 8 构建的。它包括 Python 3.10、构建工具（`cmake`、`gcc`）、科学库（HDF5、Boost）和支持 CUDA 12.1 的 PyTorch。 SageMaker AI 映射标准安装路径：用于输入数据的“/opt/ml/processing/input”、用于输出数据的“/opt/ml/processing/output”以及用于模型权重的“/opt/ml/processing/cache”。

通过使用环境变量替换的 YAML 文件配置管道：```
aws: 区域: ${AWS_REGION} # 来自 .env 文件 s3_bucket: ${AWS_S3_BUCKET} role_arn: ${AWS_ROLE_ARN} image_uri: ${AWS_IMAGE_URI} pipeline: name: BoltzGen-Protein-Design s3_prefix: Boltzgen-pipeline design: num_designs: 10000 Budget: 100 protocol: Protein-anythingspecs_dir: ./specsinstances:design:type:ml.g5.12xlarge#4个GPU用于并行处理instance_count:1#增加多实例扩展
```该语法支持从“.env”加载的变量“${VAR_NAME}”，以及具有默认值的变量“${VAR_NAME:default}”。

核心集成依赖于 SageMaker AI `ScriptProcessor` 类：```
processor = ScriptProcessor( role=role, # IAM role with Amazon S3 + Amazon ECR access image_uri=<image_uri>, # Amazon ECR image URI instance_count=1, # Single GPU instance instance_type='ml.g4dn.xlarge', # NVIDIA T4 GPU volume_size_in_gb=50, # EBS storage for models max_runtime_in_seconds=86400, # 24-hour timeout command=['python3'] # Execute Python scripts ) processor.run( code='processing_script.py', inputs=[ProcessingInput(source=s3_input, destination='/opt/ml/processing/input')], outputs=[ProcessingOutput(source='/opt/ml/processing/output', destination=s3_output)], arguments=['--design-spec', 'design.yaml', '--num-designs', '100', '--budget', '10'] )
```管道步骤之间的中间结果存储在 Amazon S3 中：```
Amazon S3 中间存储：+-- 设计/ <- 设计步骤输出 | +-- 规格名称/ | +-- middle_designs/*.cif +-- inverse_folded/ <- 反向折叠输出 +-- Folded/ <- 折叠验证输出 +-- 已分析/ <- 分析指标输出 +-- 元数据/ <- 步骤执行元数据
```在第一次运行 BoltzGen 时，会从 Hugging Face 下载大约 6 GB 的模型权重。缓存目录（`/opt/ml/processing/cache`）存储这些权重，并且同一容器中的后续运行重用缓存的模型。

#### 成本优化技巧

从小处开始。我们建议首先使用“--num-designs 10 --budget 2”进行测试，以验证您的设计规范在扩展之前是否正常工作。

将模式与您的舞台相匹配。处理作业非常适合快速实验和验证。管道适合生产运行，其中参数迭代受益于步骤级缓存。

我们建议您使用缓存。在管道模式下，仅在第一次运行时下载模型权重（大约 6 GB），并且当输入未更改时，步骤级缓存会跳过已完成的计算步骤。这两层缓存一起在迭代工作流程中节省了大量的时间和成本。

#### 清理

为了避免在完成实验后持续产生费用，请删除您在本演练中创建的资源。

删除 Amazon S3 数据：```
aws s3 rm s3://amzn-s3-demo-bucket/boltzgen --recursive
```删除 Amazon ECR 存储库：```
aws ecr删除存储库--存储库名称boltzgen-sagemaker--force
```删除 Amazon S3 存储桶（如果不再需要）：```
aws s3 rb s3://amzn-s3-demo-bucket
```删除 AWS IAM 角色（可选）：```
aws iam detach-role-policy --角色名称 BoltzGenSageMakerRole --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess aws iam delete-role --角色名称 BoltzGenSageMakerRole
```如果您按照前面的说明操作，请停止并删除 JupyterLab 空间。 SageMaker AI Studio 空间会产生成本，因为它们在专用实例上运行，在本例中为“ml.m5.2xlarge”实例。从 Studio UI 或 SageMaker AI 控制台停止空间。您还可以使用 AWS CLI 停止它。请参阅[SageMaker AI 文档中的说明](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-running-stop.html)。

### 结论

在这篇文章中，我们演示了如何在 SageMaker AI 上部署 BoltzGen、运行您的第一个蛋白质设计实验，以及从快速验证运行扩展到生产批量处理。托管 GPU 计算、步级缓存和按秒计费使得无需管理基础设施即可从设计规范转变为对候选蛋白质进​​行排名。两种执行模式可让您将计算与研究的每个阶段相匹配：用于快速实验的处理作业和用于生产工作流程的管道。多 GPU 并行化只需对数千个设计进行一次验证运行。

### 后续步骤

要开始使用，请访问 GitHub 上的 [sample-biofm-quickstart](https://github.com/aws-samples/sample-biofm-quickstart/tree/main) 存储库，并按照 [SageMaker 处理作业上的 Boltzgen](https://github.com/aws-samples/sample-biofm-quickstart/tree/main/models/boltzgen/inference/amazon-sagemaker/boltzgen-on-sagemaker-processing-job-cli) 的快速入门指南进行操作。有关 SageMaker AI 处理作业和管道的更多信息，请参阅 [Amazon SageMaker AI 文档](https://docs.aws.amazon.com/sagemaker/)。我们欢迎对该项目的反馈和贡献。有关使用 SageMaker AI 扩展蛋白质设计需求的问题，请联系 AWS 代表。

### 致谢

我们感谢 [BoltzGen 团队](https://boltz.bio/manifesto) 开发了这种蛋白质设计模型。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
