<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-30T01:52:33+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/pair-nova-2-lite-with-claude-for-cost-optimized-document-processing/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 将 Nova 2 Lite 与 Claude 配对，实现成本优化的文档处理 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-30 01:52 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | Pair Nova 2 Lite with Claude for cost-optimized document processing \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/pair-nova-2-lite-with-claude-for-cost-optimized-document-processing/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在这篇文章中，我们展示了如何将 Amazon Nova 2 Lite 与 Anthropic 的 Claude Sonnet 4.6 结合使用，为大规模扫描文档数字化提供高效的解决方案。我们在 Amazon Bedrock 上构建了两个模型管道，用于数字化扫描的年鉴页面。 Amazon Nova 2 Lite 在一次调用中处理本机多模式提取：检测照片、提取带有坐标的可见名称以及返回页面级元数据。然后，Claude Sonnet 4.6 执行空间推理，根据页面布局将姓名与面孔进行匹配。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## 将 Nova 2 Lite 与 

Claude 配对，以实现成本优化的文档处理

扫描的年鉴页面包含 176 个印刷姓名、4 张肖像照片以及零个链接它们的机器可读结构。要将此页面数字化，您需要带有边界框的可靠照片检测和准确的名称提取。您还需要一种方法来根据页面布局确定哪个名称属于哪个面。

在这篇文章中，我们展示了如何将 Amazon Nova 2 Lite 与 Anthropic 的 Claude Sonnet 4.6 结合使用，为大规模扫描文档数字化提供高效的解决方案。我们在 Amazon Bedrock 上构建了两个模型管道，用于数字化扫描的年鉴页面。 Amazon Nova 2 Lite 在一次调用中处理本机多模式提取：检测照片、提取带有坐标的可见名称以及返回页面级元数据。然后，Claude Sonnet 4.6 执行空间推理，根据页面布局将姓名与面孔进行匹配。

我们针对 336 个扫描的年鉴页面运行了此管道，并生成了 3,122 个姓名与面孔的关联，其中 93% 的得分等于或高于 0.95 置信度。这种双模型方法每页的成本比将整个任务发送到一个视觉语言模型的单模型替代方案低约三分之二。有关详细信息，请参阅成本考虑因素部分。

### 解决方案概述

该管道有两个阶段。每个阶段都使用不同的模型，根据其执行的特定任务进行选择。

![Amazon Bedrock 上两阶段年鉴文档处理管道的架构图：扫描的页面图像流入第 1 阶段（Amazon Nova 2 Lite，用于照片检测和姓名提取），然后进入第 2 阶段（Claude Sonnet 4.6，用于具有自适应思维的空间推理），生成姓名与面孔关联的结构化 JSON。](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/19/ML-20681-1.png)

图 1. 两种模型管道架构。扫描的页面图像经过两个连续的阶段。在第 1 阶段，Amazon Nova 2 Lite 在单个 API 调用中执行本机多模式提取。它使用边界框检测照片并对其进行分类，读取页面上的可见名称并返回其大致位置，并发出页面级元数据。在第 2 阶段，Claude Sonnet 4.6 执行空间推理，使用组合的 Nova 输出将姓名与面孔进行匹配。Amazon Nova 2 Lite 首先运行。因为它本身处理交错的文本和图像，所以单个 Converse 调用会返回三件事：

- 检测到的照片带有边界框和分类。
- 页面上可见的名称及其大致位置。
- 页面级元数据，例如标题和类别。

我们通过在 Converse API 调用中包含推理配置来将此任务的推理设置为 LOW。请参阅下面的步骤 1 代码中的推理块。对所有 336 个页面的测试表明，对于这种结构化提取，低、中和高推理级别之间没有有意义的准确性差异，而低是最便宜的选择。 Nova 通过 `reasoning_config` 字段公开此设置。Claude在步骤 2 中使用了单独的“思考”字段，因此两个模型以不同的名称控制推理。

仅向 Nova 2 Lite 询问名称，而不是页面上的每个 OCR 令牌，这使得第一阶段的成本较低。下游空间推理步骤不需要班级名册或事件描述的全文。它需要出现在照片附近的名称。将 Nova 输出限制为名称可将输出令牌成本保持在每页大约 1,000 个令牌，而不是完整 OCR 通行证将产生的大约 4,500 个令牌。

Claude Sonnet 4.6 仅在第 2 阶段进入空间推理步骤。给定 Nova 名称、位置和照片边界框，Claude确定哪些名称对应哪些面孔。此步骤需要处理页面布局可变性，因为年鉴布局因页面而异。标题可能会出现在照片上方或下方，并且某些页面将肖像网格与集体照混合在一起。Claude自适应思维可以处理这种可变性，而无需针对每种布局类型进行额外的即时工程。

在此解决方案中，Nova 2 Lite 在一次调用中本地处理大量提取工作。每页调用一次 Claude 来进行空间推理步骤。

#### Nova 2 Lite 按图像固定定价：大规模可预测成本

Amazon Nova 2 Lite 最近对图像输入计费方式进行了更改，使得每页成本可以大规模预测，这在您处理数十万页时很重要。

按图像固定定价：Amazon Nova 2 Lite 按固定的按图像费率对图像和文档页面输入进行计费，无论分辨率或文件大小如何。这一变化对于文档处理管道来说意义重大。以前，图像令牌成本根据分辨率而变化，因此如果不对代表性样本进行概念验证，就很难预测每页成本。通过固定计费，Nova 2 Lite 处理的每张图像都按相同的每张图像费率计费，无论分辨率如何。

对于包括提示和输出的整页提取，每页成本细分如下：

|组件|代币/页 |评分 |成本/页 |
|:---|:---|:---|:---|
|图像标记（固定）| 230 | 230 $0.30/月输入 | 0.000069 美元 |
|提示令牌（估计）| 500 | 500 $0.30/月输入 | $0.000150 |
|输出代币（估计）| 1,000 | $2.50/M 产出 | 0.0025 美元 |
|总计 | ~$0.0027 |  |  |

按照公布的 Nova 2 Lite 输入令牌率，图像输入仅占每页总成本的一小部分。有关当前费率，请参阅 [Amazon Bedrock 定价页面](https://aws.amazon.com/bedrock/pricing/)。

对于年鉴规模的工作负载（每年数十万页），这种固定定价使成本预测变得简单，因为图像输入成本与页数成线性比例，并且与页面分辨率无关。不需要分辨率标准化。

### 空间推理的适应性思维

Amazon Bedrock 上的 Claude 支持自适应思维，该功能使模型根据输入的复杂性决定应用多少内部推理。您可以通过在 Converse API 的“thinking”配置中将“type”设置为“adaptive”来启用它：```
响应 = bedrock_runtime.converse( modelId='us.anthropic.claude-sonnet-4-6', messages=[{ '角色': '用户', '内容': [{'image': {'format': 'jpeg', 'source': {'bytes': image_bytes}}}, {'text': Spatial_reasoning_prompt} ] }], extraModelRequestFields={ '思考': { '类型': '自适应' } } )
```启用自适应思维后，Claude会根据收到的信息调整推理深度。一个简单的肖像网格，八个名字整齐地排列在八张面孔上方，以最少的推理得到直接的回应。三张集体照片共享一个标题块并且名称出现在侧边栏中的页面会触发逐步空间分析。

在我们的 336 页运行中，Claude 在每一页上都使用了扩展推理，推理痕迹范围从 544 到 1,658 个字符。即使是更简单的页面也能从一些空间分析中受益，因为年鉴的布局很少是完全统一的。推理痕迹显示Claude处理列对齐以及姓名位置和面部位置之间的垂直偏移，并在页面上出现集体照片时检查标题的接近度。

对于这种类型的结构化空间任务，自适应思维可以为您提供每页适量的推理，而无需手动调整。您不需要设置固定的令牌预算或编写特定于布局的提示。模型读取输入并做出决定。

关于适应性思维的成本说明：启用适应性思维时，请牢记三个成本因素。

- 推理代币按标准输出率作为输出代币计费（通过跨区域推理，Claude Sonnet 4.6 的输出代币为 15.00 美元/M）。
- 推理跟踪在单独的“思考”内容块下的 API 响应中返回，但不会向最终用户显示。
- 监视响应元数据中的“inputTokens”和“outputTokens”以跟踪每个页面的实际成本，因为推理可以显着增加复杂页面上的输出令牌计数。

### 实施演练

完整源代码、示例图像和 Jupyter Notebook 可在 [GitHub 上的 AWS 示例存储库](https://github.com/aws-samples/amazon-nova-samples/tree/main/multimodal-understanding/repeatable-patterns/35-hybrid-vision-spatial-reasoning) 中获取。

#### 先决条件

在运行管道之前，请确保满足以下条件：- 在提供 Amazon Nova 2 Lite 和 Claude Sonnet 4.6 的 AWS 区域中拥有可访问 Amazon Bedrock 的 AWS 账户。
- 在 Amazon Bedrock 控制台中为“us.amazon.nova-2-lite-v1:0”和“us.anthropic.claude-sonnet-4-6”启用模型访问。
- AWS Identity and Access Management (IAM) 委托人有权在上述两个模型上调用“bedrock:InvokeModel”和“bedrock:Converse”。
- 安装了“boto3” SDK 的 Python 3.10 或更高版本。示例笔记本还使用“rapidfuzz”进行模糊名称匹配，并使用 Pillow 进行可视化覆盖。
- 扫描的页面图像（JPEG 或 PNG）。对于通过 Converse API 输入的图像，图像字节在请求中内联传递。

#### 步骤 1：使用 

Amazon Nova 2 Lite 检测照片并提取名称

将扫描的页面发送到 Amazon Nova 2 Lite，并显示请求检测到的照片（带有边界框和分类）和可见名称（带有页面上的大致位置）的提示。 Nova 原生多模式理解在单个 Converse 调用中返回两者。

Nova 返回照片和名称的 0-1000 坐标范围内的边界框。将两者直接传递到步骤 2。当提示中给出时，Claude 读取相同的坐标空间，因此不需要转换。```
def extract_photos_and_names(image_bytes): """Detect photos and extract visible names with Amazon Nova 2 Lite.""" # Using the Converse API consistently for all Bedrock calls response = bedrock_runtime.converse( modelId='us.amazon.nova-2-lite-v1:0', # Note: cross-region inference profile (us.amazon.nova-2-lite-v1:0) messages=[{ 'role': 'user', 'content': [{ 'image': { 'format': 'jpeg', 'source': {'bytes': image_bytes} } }, {'text': PHOTO_AND_NAME_EXTRACTION_PROMPT} ] }], inferenceConfig={ 'maxTokens': 8000, 'temperature': 0 }, additionalModelRequestFields={ 'reasoning_config': { 'type': 'enabled', 'level': 'LOW' } } ) raw = response['output']['message']['content'][0]['text'] return json.loads(raw)
```该提示指示 Nova 返回一个 JSON 对象，其中包含页面上可见的照片和名称。```
{ "page_title": "初级军官", "photos": [{ "bbox": [245, 180, 410, 520], "type": "portrait", "category": "class_officers", "summary": "个人肖像照" } ], "names": [{ "text": "Cecilia Phillips", "bbox": [260, 540, 395, 570] }, { "text": "约翰·科兰德", "bbox": [420, 540, 555, 570] } ] }
```每张照片都有一个边界框、一个类型（肖像、团体或抓拍）、一个类别标签和一个简短的描述。每个名称都有其可见文本及其在页面上的边界框。 “page_title”和“category”字段还服务于第二个用例：元数据提取。只需一次 API 调用，Nova 2 Lite 即可为您提供照片检测、匹配管道的名称与位置以及结构化元数据。您可以使用此元数据进行搜索索引、按事件类型过滤或构建跨数百页的目录。

#### 步骤 2：与 

Claude 匹配名字和面孔

现在将 Nova 名称与位置和照片边界框传递给 Claude 进行空间推理。两者都使用相同的 0-1000 坐标空间，因此不需要标准化：```
spatial_prompt = f"""Given these names with page coordinates: {json.dumps(ocr_tokens)} And these detected photos with bounding boxes: {json.dumps(photo_detections)} Match each person's name to their photo based on spatial position. Return JSON: {{"associations": [{{"name": str, "face_idx": int, "confidence": float, "reasoning": str}}]}}""" response = bedrock_runtime.converse( modelId='us.anthropic.claude-sonnet-4-6', messages=[{ 'role': 'user', 'content': [{'image': {'format': 'jpeg', 'source': {'bytes': image_bytes}}}, {'text': spatial_prompt} ] }], additionalModelRequestFields={ 'thinking': {'type': 'adaptive'} } )
```在我们的测试集的第 50 页上，Nova 返回了 176 个姓名条目和 4 个照片边界框。其中大多数名字都是页面其他地方的名册和正文文本。只有 4 张照片旁边的名字是可以匹配的，因此 Claude 产生了 5 个关联：```
{ "associations": [{"name": "Cecilia Phillips", "face_idx": 0, "confidence": 0.95, "reasoning": "第 0 行，位置 1，共 3 个 - 与照片上方的标题匹配"}, {"name": "John Kolander", "face_idx": 1, "confidence": 0.95, "reasoning": "Row 0,位置 2（共 3 个）- 与照片上方的标题匹配"}, {"name": "Julie Ostrander", "face_idx": 2, "confidence": 0.95, "reasoning": "第 0 行，位置 3（共 3 个）- 与照片上方的标题匹配"} ] }
```每个关联都包含一个解释空间逻辑的推理字符串。这对于调试关联失败的页面非常有用。

#### 步骤 3：验证并汇总结果

最后一步应用置信度阈值和模糊名称匹配（使用rapidfuzz）来过滤掉低质量关联。该管道每页写入两个输出：一个包含关联数据的 JSON 文件和一个显示匹配名称和面孔之间绘制的线条的可视化图像。

### 结果

我们通过此管道处理了 336 个扫描年鉴页面。该管道总共产生了 3,122 个姓名与面对面的关联，其中 93.3% 的关联得分等于或高于 0.95。只有 0.3% 的置信度低于 0.90 阈值。

![置信度得分分布直方图显示 2,912 个关联度等于或高于 0.95 置信度，202 个关联度介于 0.90 和 0.94 之间，8 个关联度低于 0.90。](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/19/ML-20681-2.png)

图 2. 根据 336 个扫描年鉴页面生成的 3,122 个姓名与面孔关联的置信度得分分布。这种分布严重偏向于高置信度：2,912 个协会 (93.3%) 的得分等于或高于 0.95，202 个协会 (6.5%) 的得分在 0.90 到 0.94 之间，只有 8 个协会 (0.3%) 的得分低于 0.90。 Claude Sonnet 4.6 在空间推理步骤中产生置信度分数。它们反映了模型的确定性，即给定的名称标记映射到特定的面部边界框。

- 纵向网格页面（336 页中的 282 页）平均每页有 10.9 个关联。这些页面具有规则的布局，其中名称直接出现在相应照片的上方或下方，并且管道可靠地处理它们。
- 纯文本页面（班级名单、活动描述、索引页面）没有要检测的照片，因此被正确跳过。
- 同一页面上带有肖像和集体照片的混合布局页面产生了部分关联。该管道将​​姓名与肖像照片进行匹配，但当标题不明确时，集体照片无法匹配。

该管道输出每个页面的 JSON 报告和可视化结果。可视化从每个名称标记到其匹配的面孔绘制了彩色线条，这使得在手动检查期间很容易发现错误。

#### 成本考虑两种模型的拆分意味着您需要为合并的提取调用（照片、姓名与位置、元数据）支付 Nova 2 Lite 费率，并为每页一次推理调用支付 Claude 费率。根据 Nova 2 Lite 的固定每图像定价，第一阶段成本是可预测的并且与输入分辨率无关。Claude推理步骤主导每页成本。

每页成本明细

|舞台|服务 |成本驱动因素|每页大约成本 |
|:---|:---|:---|:---|
|照片+姓名提取 |亚马逊 Nova 2 Lite |修复了 230 个图像标记 + ~500 个提示 + ~1,000 个输出 | ~$0.0027 |
|空间推理|Claude十四行诗 4.6 |图像 + Nova JSON + 自适应推理令牌 | ~$0.030 |
|管道总数 | ~$0.033 |  |  |

下表将管道与单模型方法进行了比较，其中每个页面都发送给 Claude，以在一次调用中完成所有三项任务（OCR、照片检测和空间匹配）。

|尺寸|两种模型管道 |单模Claude|
|:---|:---|:---|
|输入令牌 |图像（Nova：230 已修复）+ Nova JSON → Claude |图像 @ ~1,500 个代币 + 提示 @ ~1,300 = ~2,800 个代币 @ $3/M = ~$0.008 |
|输出代币 | Nova：~1,000 个名称-JSON；Claude推理：~1,700 @ $15/M = ~$0.026 | ~6,000 个代币 @ $15/M = ~$0.09 |
|每页成本| ~$0.033 | ~$0.10 |
|每 10 万页成本 | 〜$3,300 | 〜$ 9,800 |
| OCR 质量 | Nova 原生多式联运（无单独的 OCR 服务）|通用视觉语言模型|
|可调性|独立交换或调整每个阶段 |整体提示；全有或全无的改变|

如果页数为 100,000 页，则相差约 6,500 美元。除了成本之外，分割管道还使您能够独立交换或调整每个阶段，而无需触及其他阶段。例如，当更好的Claude等级发布时，您可以仅升级推理模型。

确切的每页成本取决于三个因素：

- 您的 Amazon Bedrock 定价等级。
- Nova 发出的名称数量（随页面密度缩放）。
- Claude使用的推理标记的数量（随布局复杂性缩放）。

为了进行粗略估计，请添加一个 Nova 2 Lite Converse 调用，其中包含单个图像输入和姓名和照片提示。然后添加一个 Claude Converse 调用，其中输入包括图像和 Nova JSON 输出。查看 Amazon Bedrock 定价以了解当前费率。

336 页测试运行的实际成本

基于我们的管道运行（336 页，平均每页 10.9 个关联）：|组件|预计成本|
|:---|:---|
| Nova 2 Lite 照片 + 姓名提取（336 页 × 0.0027 美元）| ~$0.91 |
|Claude空间推理（336 页 × 0.030 美元）| ~$10.08 |
|总计 | 336 页约 10.99 美元（约 0.033 美元/页）|

额外的成本优化杠杆

对于大容量或非实时工作负载：

- Amazon Bedrock 批量推理：Nova 2 Lite 享受 50% 的折扣，Claude 要求可在夜间处理工作负载。将请求的 JSONL 文件提交到 Amazon Simple Storage Service (Amazon S3)，让 Amazon Bedrock 异步处理，并在第二天早上读取结果。按批量定价，Nova 2 Lite 组合阶段从每页约 0.0027 美元降至约 0.0014 美元。
- 提示缓存：如果您在数千个页面上使用相同的照片检测提示（正如此管道所做的那样），提示缓存可以将缓存提示令牌成本降低高达 90%。
- 推理预算控制：对于 Claude，您可以在“thinking”上设置“budgetTokens”上限，以限制较简单页面上的推理令牌成本，同时在需要时仍允许进行更深入的推理。

#### 延迟

每个页面都会经历两次连续的 API 调用，因此每个页面的总延迟是两者的总和。在我们的测试运行中，由于图像输入和自适应推理，Claude 空间推理步骤花费的时间最长，每页大约 20-30 秒。 Nova 2 Lite 在几秒钟内完成。对于批处理，您可以跨页面并行化，因为每个页面都是独立的。

|舞台|典型延迟 |
|:---|:---|
| Nova 2 Lite（照片+姓名提取）| 2–5 秒 |
|Claude空间推理（适应性思维）| 20–30 秒 |
|每页总计 |约 22–35 秒 |

### 清理

该管道使用无服务器 AWS 服务，无需管理持久基础设施：

- Amazon Bedrock：Nova 2 Lite 和 Claude 按次付费，无需删除预配置端点。
- Amazon S3：如果您将年鉴图像上传到 Amazon S3 进行处理，请在完成后删除存储桶或对象。 Amazon S3 删除是永久且不可逆的。删除前请确认您有备份或不再需要数据。
- IAM 角色：删除专门为此管道创建的任何角色（Nova 2 Lite 和 Claude Sonnet 4.6 的 Amazon Bedrock 调用权限）。

＃＃＃ 结论在这篇文章中，我们展示了在 Amazon Bedrock 上跨两个模型进行文档处理如何在 336 个年鉴页面中产生 3,122 个姓名与面孔关联，其中 93% 的置信度很高。 Amazon Nova 2 Lite 在单个本机多模式调用中处理照片检测和名称提取。 Claude Sonnet 4.6 使用自适应思维处理空间推理，将名字与正确的面孔相匹配。

这种模式不仅适用于年鉴。任何包含照片和相关文本的文档（历史档案、人员目录、房地产清单、产品目录）都需要相同的功能：检测视觉元素、提取相关文本，并通过空间推理将两者连接起来。我们在这篇文章中描述的解决方案结合了照片检测、文本提取和空间推理，以实现成本效益和高精度。

完整的笔记本和示例输出可在 [GitHub 上的 AWS 示例存储库](https://github.com/aws-samples/amazon-nova-samples/tree/main/multimodal-understanding/repeatable-patterns/35-hybrid-vision-spatial-reasoning) 中获取。

要了解有关本文中使用的服务的更多信息，请参阅以下资源：

- [亚马逊基岩上的亚马逊 Nova](https://docs.aws.amazon.com/nova/latest/userguide/)
- [与 Claude 在 Amazon Bedrock 上进行适应性思维](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-adaptive-thinking.html)

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
