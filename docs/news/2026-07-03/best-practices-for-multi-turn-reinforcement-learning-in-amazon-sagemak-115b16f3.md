<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-03T01:50:23+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/best-practices-for-multi-turn-reinforcement-learning-in-amazon-sagemaker-ai/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# Amazon SageMaker AI 中多轮强化学习的最佳实践 |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-03 01:50 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | Best practices for multi-turn reinforcement learning in Amazon SageMaker AI \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/best-practices-for-multi-turn-reinforcement-learning-in-amazon-sagemaker-ai/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在这篇文章中，我们分享了可靠的多轮强化学习训练的最佳实践。我们介绍了如何构建您可以信任的培训环境、设置外部评估、设计与最终任务一致的奖励、管理代理运行多轮后的变化，以及监控告诉您何时进行迭代的指标。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## Amazon SageMaker 

AI 中多轮强化学习的最佳实践

在 Amazon SageMaker AI 中训练多回合代理来解决支持请求或审核内容意味着要处理一系列相关步骤，而不是单个响应。这些代理读取指令、调用工具、读取结果、决定下一步操作，并在做出答案之前从错误中恢复。这种灵活性也使得代理强化学习 (RL) 具有挑战性。更多的行动方式意味着有更多的方式在不执行任务的情况下满足奖励，而代理训练的环境可能会悄悄地破坏训练信号。

在这篇文章中，我们分享了可靠的多轮强化学习训练的最佳实践。我们介绍了如何构建您可以信任的培训环境、设置外部评估、设计与最终任务一致的奖励、管理代理运行多轮后的变化，以及监控告诉您何时进行迭代的指标。我们从 [SOP-Bench](https://github.com/amazon-science/SOP-Bench) 数据集提取示例，这是一个 Amazon Science 基准，用于评估代理基于 12 个业务领域的复杂标准操作程序 (SOP) 解决任务的能力。

### SageMaker 

AI 多轮强化学习

[Amazon SageMaker AI 多轮 RL](https://aws.amazon.com/about-aws/whats-new/2026/06/multi-turn-reinforcement-learning-on-sagemaker-ai/) (SageMaker AI MTRL) 提供代理任务的训练循环。您的代理可以在 [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)、Amazon Elastic Kubernetes Service (Amazon EKS)、Amazon Elastic Compute Cloud (Amazon EC2)、AWS Fargate 或您选择的基础设施上运行。您可以通过一个小型适配器将其连接，该适配器将您的工具界面暴露给部署服务器，然后 SageMaker AI MTRL 处理其余的工作：- 模块化代理环境界面，可保持集成低代码，同时为您提供完整的算法控制。自定义奖励、自定义工具循环和多轮对话形状都由您定义。
- 无服务器执行可简化基础设施问题，因此您可以按代币定价获得生产规模的代理强化学习，而无需配置或管理 GPU 集群。
- 具有有限的离策略陈旧性的异步推出和轨迹收集。生成和梯度更新并行运行，不会偏离当前策略太远，从而加快训练速度。
- 涵盖近端策略优化 (PPO)、截断重要性采样策略优化 (CISPO) 和重要性采样 (IS) 损失的本机算法库，与多个基于组的优势估计器（GRPO、GRPO `pass@k`、RLOO 等）配对。这些涵盖了与多轮代理强化学习最相关的选择。
- 序列延伸训练，以减少长时间多转弯轨迹上的挂钟。
- [由 Amazon SageMaker AI 管理的 MLflow](https://aws.amazon.com/sagemaker-ai/experiments/) 中的轨迹和奖励可观测性，因此您可以跨训练步骤依次读取代理的操作。
- 在部署到 SageMaker AI 终端节点或 Amazon Bedrock 之前，评估作业会报告奖励、“pass@k”、轨迹指标等。

该服务提供训练循环、硬件和编排。决定您是否找到可靠代理人的选择取决于您。您构建代理训练的环境，衡量奖励之外的成功，设计奖励本身，并决定当曲线停滞时如何迭代。

![SageMaker AI 多轮强化学习服务的架构概述，显示代理、部署服务器和训练循环](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/29/ML-21260-1.jpg)

图 1：SageMaker AI 多轮强化学习服务概述

### 建立一个廉价、可重复、有代表性的培训环境

单轮强化学习需要提示和奖励函数。多轮强化学习为智能体增加了一个跨轮行动的环境：它调用的工具及其背后的系统。该环境是您的训练设置的一部分，您构建它的方式决定了模型可以学习的内容以及您是否可以信任您的指标。训练代理时，构建一个类似于生产环境但与实时流量隔离的沙盒或模拟环境。工具调用和响应保持相同的架构和业务逻辑。它们是由记录的响应或隔离状态驱动的，而不是实时呼叫。

模拟环境是建议的起点，因为典型的运行会产生数千次部署，每个部署都会调用多个工具。例如，批量大小为 128、组大小为 8 时，每步有 1,024 次部署。指出实时系统的流量可能会对客户产生影响。如果没有模拟环境，探索就会产生真实的副作用。例如，通过反复试验学习的代理将发出退款、删除记录或触发您不希望的工作流程。此外，实时数据会在您的身下发生变化，因此相同的轨迹在不同的跑步中得分不同。您必须知道计算奖励的正确结果，这意味着无论工具调用到哪里，都有一组固定的、标记的任务（或值得信赖的判断模型）。

如何构建模拟环境取决于您的工具的用途。三种模式涵盖了您将遇到的大多数用例：- 只读工具：重播由其输入键入的记录响应。这些工具帮助代理检索与任务相关的信息。例如，在 SOP-Bench 中，客户服务任务提供了十个模拟工具（“validateAccount”、“getAuthenticationDetails”、“createSessionAndOpenTicket”等），每个工具都从固定装置返回确定性响应，例如基于工具调用参数的 CSV 文件中的特定行。
- 有状态的工具：种子沙箱，在一个情节的长度内保持状态。当代理写入内容并将其读回时，环境需要内存。模式：在推出开始时分配每集资源，并注册代理创建的所有内容。当剧集结束时，无论是达到终端操作、达到“max_turns”还是崩溃，都可以在“try/finally”块中将其全部拆除。没有状态泄漏到下一次部署中。
- 可验证的结果：在隔离的模拟环境中真正执行。当代理的输出是代码、SQL 或数学时，您可以在隔离环境中运行它。使用 Docker `exec` 执行代码，每次部署时使用内存中的 SQLite 执行 SQL，使用纯 Python eval 执行数学运算。真正的执行，每个实例的确定性，相同的输入加上相同的沙箱状态等于相同的结果。例如，[AgentCore Code Interpreter](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html) 为代码执行提供托管隔离环境。

无论哪种模式适合，请固定两个属性：

- 再现性：使用相同参数调用的同一工具会返回相同的结果，因此相同轨迹的奖励是稳定的，并且您的评估在不同运行中具有可比性。
- 代表性：根据真实模式和数据分布构建环境，以便模型学习的行为转移到生产中。

在开始训练之前，请确认您的环境配置正确：

- 使用相同参数的工具调用给出相同的结果，通过运行相同的实例两次并比较推出消息来验证。
- 每个推出状态是隔离的（单独的临时目录、单独的 ID、单独的数据库连接）。
- 可用的工具与您的生产环境相匹配，以及工具请求/响应模式。

### 在训练前设置外部评估环境就位并经过验证后，在编写奖励函数之前构建一种衡量成功的方法。

该衡量标准应该直接反映您的最终目标。强化学习从字面上优化了奖励信号，因此如果奖励是你看到的唯一数字，你就无法将任务进度与满足奖励标准的进度分开。您需要一个值得信赖的外部评估来指导您的决策，同时迭代奖励、环境播种和超参数。

#### 模式

进行持续的评估，对您在部署时关心的结果进行评分，计算结果与奖励无关。实际上，这是一小段代码，它采用一个模型，在固定的测试分割上通过部署服务器运行它，并返回单个任务成功率。只要是诚实的，它可以是最小的。

对于 SOP-Bench，评估是对“<final_output>”内的最终 JSON 对象进行精确匹配：代理输出中的每个字段都必须与真实字段匹配，否则推出得分为零。奖励函数可以计算部分信用和加权分量。评价没有。

在任何培训之前，建立基线。通过相同的评估运行基本模型和参考模型（托管在 Amazon Bedrock 上的前沿模型非常合适）。这告诉您两件事：基本模型还需要走多远，以及此任务的效果如何。

#### 反模式

将培训奖励或从中派生的指标视为成功的衡量标准。这可能看起来很直观，但要捕获奖励黑客行为，您需要外部评估。多轮代理需要特别考虑：为工具调用支付的奖励教会代理调用尽可能多的工具。对回合计数进行惩罚的奖励会教导智能体在获得所需信息之前承诺给出答案。无论哪种方式，训练奖励都会增加，但智能体完成任务的真正成功率却会下降。

在开始培训之前，请确认您的评估值得信赖：

- 评估是一个函数，“score(rollout) -> float”，对您发布的内容进行准确评分。
- 您计划微调的基础模型的基线评估不为零（如果为零，请参阅下一节中的确保基础模型首先有立足点）。
- 针对前沿模型进行评估，以便您拥有可进行比较的高级基线。

### Design a good multi-turn RL reward function奖励设计是强化学习中最具挑战性的开放问题之一。让智能体解决实际任务的灵活性同样可以让它找到无需执行任务即可满足奖励的方法。您添加的每个组件、您调整的每个奖励权重、您分层的每个格式奖励都是代理可以在不解决任务的情况下攀登的另一个表面。该模型优化了你写下的内容，而不是你的意思。默认情况下，训练和评估使用相同的评分规则，并且只有在有具体原因时才会偏离。

采取 SOP-长凳。 The benchmark expects the answer as a JSON object inside `<final_output>` tags:```
{ "aircraft_ready": "true", "mechanical_inspection_result": "成功", "electrical_inspection_result": "成功", "component_incident_response": "成功", "component_mismatch_response": "成功", "cross_check_reporting_response": "成功" }
```如果每个字段都匹配，则基准得分为 1，否则得分为 0。培训和评估通常共享此评分规则，仅在您观察到的内容方面有所不同。训练员每次部署都会消耗一份奖励（标量或标量列表）。评估在固定分割上以较低的频率运行，因此您可以监控更多指标：每个字段的准确性、完成率（代理是否发出“<final_output>”）、工具调用分布、回合预算耗尽、格式合规性。

偏离默认基准评分规则有两个真正的原因，并且都需要更密集的奖励。

第一个是算法。强化学习使用基于组的优势方法（“advantage_method”）根据每个提示的一组“group_size”卷展的方差来计算学习信号。 The service default `group_based` is GRPO. Many other methods like `rloo` and `grpo_passk` are also available. See the [documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/model-customize-mtrl-hyperparams.html) for a full list.二进制分数可以消除这种方差：当组中的每个推出得分相同时，相对信号为零，并且该组不贡献任何梯度。当“rollout/reward/valid_mean”（非零优势群体的平均值）漂移到“rollout/reward/mean”以下并且模型停滞时，这种差距就是症状。

第二是收敛速度。即使群体方差是健康的，密集的奖励也会使模型在每次部署时都取得部分进展，而不仅仅是完全成功的模型。 A rollout that gets five of six fields right teaches the model what closer looks like.二进制分数对此一无所知。

SOP-Bench 任务的密集奖励对每个字段进行独立评分，并返回奖励标量或标量列表（每轮奖励）以及指标字典。```
class SOPBenchReward: """Dense per-field reward for the SOP-Bench aircraft-inspection task. Returns a scalar in [0, 1] plus a metrics dict surfaced in MLflow.""" ground_truth: dict[str, str] format_coef: float = 0.1 # format is a small shaping term, not the objective async def __call__(self, history: list[Message]) -> tuple[float, dict[str, float]]: fields = parse_final_output(last_assistant(history)) # JSON inside <final_output> emitted = float(fields is not None) if fields is None: # no parseable answer return self.format_coef * (emitted - 1), {"completion": 0.0, "field_acc": 0.0} matched = sum(1 for k, v in self.ground_truth.items() if str(fields.get(k)).strip().lower() == str(v).strip().lower()) field_acc = matched / len(self.ground_truth) # partial credit: 5/6 > 0 reward = field_acc + self.format_coef * (emitted - 1) # correctness dominates return reward, {"completion": emitted, "field_acc": field_acc}
```Your agent reports the reward through `update_reward`, and the metrics dictionary (`completion`, `field_acc`) appears in MLflow.为了奖励单个回合而不是整个轨迹，“update_reward”还接受每回合列表，与“group_based_per_turn”优势方法配对，因此您的奖励函数也可以每回合返回一个奖励值。

- Verify the reward on real outputs before you train on it. A reward parser more forgiving than your evaluation is its own kind of reward hack.在我们的一次 SOP-Bench 运行中，奖励接受了比基准得分更宽松的输出格式：即使基准仅读取“<final_output>”，裸露的“<final_response>”包装器也获得了积分。训练完全按照我们的要求进行：模型学会了放弃基准所需的标签，奖励上升，但外部评价下降。
- 首先确保基础模型有立足点。强化学习改进了基本模型在某些时间内已经可以完成的工作。它不会从无到有地发明能力。如果基本模型在您的任务中产生零成功轨迹，则奖励信号没有任何可放大的内容，训练就会停止。

SageMaker AI MTRL 可以将此类基线作为托管评估作业运行。 `MultiTurnRLEvaluator` replays your agent over a held-out prompt set and reports `eval/reward` and `pass@k`. If you have already trained a model, a single call with `evaluate_base_model=True` scores the base and fine-tuned model side by side.因为“pass@k”将奖励阈值设置为“success_threshold”，所以设置“success_threshold=1”会给出严格的成功率：在平均值之外获得完美奖励的部署比例。```
from sagemaker.train.evaluate import MultiTurnRLEvaluator # With Bedrock AgentCore evaluator_base = MultiTurnRLEvaluator( model="openai-reasoning-gpt-oss-20b", dataset="s3://my-bucket/eval-prompts.parquet", agent_config="arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/my-agent", s3_output_path="s3://my-bucket/eval-output/base/", mlflow_resource_arn =“arn：aws：sagemaker：us-west-2：123456789012：mlflow-tracking-server / my-mlflow”，角色=“arn：aws：iam :: 123456789012：角色/ SageMakerRole”，accept_eula = True，）执行= evaluator_base.evaluate（）执行.wait（）
```在指定的“s3_output_path”中，您将找到报告的评估指标以及评估轨迹，您也可以在 MLflow 中查看这些指标。有关微调模型和基础模型的基于奖励的评估，请参阅[模型评估](https://docs.aws.amazon.com/sagemaker/latest/dg/model-customize-mtrl-evaluation.html) 上的文档。

请记住一个区别：评估工作分数随代理自己的奖励函数一起推出，因此它衡量的是坚持的概括性，而不是独立于奖励。宽松的奖励解析器在这里看起来很健康，因为度量就是奖励本身。捕获奖励解析器错误的独立检查保持独立：使用更严格的独立解析器（对于 SOP-Bench，基准的精确匹配评分器）​​对相同的部署进行评分并进行比较。您甚至可以通过将“MultiTurnRLEvaluator”指向奖励为独立指标的代理来运行该严格评分器作为其自己的评估作业。

如需更深入地了解奖励设计、稀疏奖励与密集奖励、判断模型、多目标塑造以及它们之间的权衡，请参阅 [SageMaker AI 奖励设计最佳实践](https://docs.aws.amazon.com/sagemaker/latest/dg/model-customize-mtrl-assets.html#model-customize-mtrl-assets-best-practices)。

在您相信您的奖励之前，请确认：

- 培训奖励和评估共享相同的基本评分规则，除非您有明确的分歧原因（并且该原因已记录在案）。
- 奖励返回“[0, 1]”中的浮点数（如果允许负回归项，则返回“[-1, 1]”）。
- 超过 100 次基线部署的奖励存在差异（并非全部为 0，也并非全部为 1）。如果没有，那就是那种测量到的信号，证明塑造或设计专门的数据课程是合理的。
- 没有基线部署在训练奖励上的得分高于在评估上的得分。如果确实如此，那么奖励就是过度奖励外部评估所不认可的东西。
- 如果奖励有多个组成部分，请验证您在 MLflow 中单独记录每个组成部分，以便您可以读取每个术语的差异。

### 管理代理运行多轮时发生的变化

多轮代理必须处理单轮代理看不到的问题。在开始训练之前，这些值得明确设计。每回合背景都会增长，而回合预算是奖励设计的一部分。每个工具调用都扩展了对话：调用、其参数、结果以及模型在它们之间产生的推理。长轨迹可以快速积累上下文，MTRL 使用序列扩展训练来保持挂钟在增长时易于管理。需要依次调用八次的任务可能会在完成之前耗尽空间。 Two budgets bound this: `max_turns`, which your agent loop controls, and the per-turn token budget, which the service sets through `sampling_max_tokens` (rollout) and `val_sampling_params.sampling_max_tokens` (evaluation).选择两者来匹配您的任务需求以及您可以在部署时提供的服务。

For SOP-Bench, eight turns and a 2,048-token per-turn budget cover the canonical procedure with margin to spare (`sampling_max_tokens` allows up to 8,192).经验法则：如果任务的人工演练需要 N 轮，请在代理循环中设置“max_turns = ceil(N * 1.5)”。右转预算是最小的预算，可以让智能体以较小的安全裕度完成任务。观察“rollout/tokens/response_max”以了解上限处的响应集群。如果超过 5% 的首次部署达到了要求，则提高“sampling_max_tokens”。否则该信号就是无声丢失。该模型从截断的轨迹中学习，但看不到完成后会获得的奖励。

#### 将完成与正确性分开

以错误答案结束的轨迹和永远不会结束的轨迹是不同的失败，将它们混为一谈隐藏了模型的问题所在。 MLflow 中的“rollout”和“val”指标系列分别为您提供这两个信号：

|  |公制|它告诉你什么 |
|:---|:---|:---|
| 1 | `推出/奖励/平均值` |平均轨迹奖励，你的训练端信号 |
| 2 | `rollout/reward/zero_frac` | Fraction of trajectories that scored exactly 0 |
| 3 | `推出/转弯/平均` | Average turns per trajectory |
| 4 | `analysis/zero_adv_groups` |每次部署得分相同的组，浪费部署 |
| 5 | `价值/奖励/平均值` |平均验证奖励您保留的数据信号|
| 6 | `val/reward/pass_k_1`, `pass_k_8` | pass@1 and `pass@k` on the held-out set |低完成率下的高“val/reward/pass_k_1”（在发出“<final_output>”之前，推出达到“max_turns”）意味着模型获得了正确的简单路径，并在困难路径上停滞，建议调整回合预算。低“val/reward/pass_k_1”的高完成率意味着它回答流畅但错误，建议重新设计奖励。这两种故障模式需要不同的修复方法，因此有必要区分它们。

在提交回合预算之前，请确认：

- 代理循环中的“max_turns”根据任务进行校准，而不是任意默认值。
- 不到 5% 的训练在任何一个回合中都达到了“sampling_max_tokens”。
- 不到 10% 的训练达到“max_turns”但没有产生最终答案。
- 完成度（发出的最终答案）和正确性（最终答案正确）在 MLflow 中作为单独的指标进行跟踪。

### 监控训练指标

设置并验证评估、环境和奖励后，就可以开始训练了。 SageMaker AI MTRL 提供高级“MultiTurnRLTrainer”和“MultiTurnRLEvaluator”构造来训练您的代理并为其评分：```
from sagemaker.train import MultiTurnRLTrainer from sagemaker.train.evaluate import MultiTurnRLEvaluator trainer = MultiTurnRLTrainer(recipe="<per-model starter recipe>", role=..., dataset=...) trainer.train() # step 6: watch rollout/reward and completion in MLflow evaluator = MultiTurnRLEvaluator(model=trainer, dataset="<held-out split>", evaluate_base_model=True) # step 7: val/reward + pass@k, base vs fine-tuned evaluator.evaluate().wait() print(trainer.get_mlflow_url()) # read the trajectories where reward and evaluation disagree
```训练时，观察完成率旁边的“rollout/reward/mean”，并在 MLflow 中打开一些轨迹（在“Traces”选项卡下），这样平坦完成时增加的奖励就不会溜走。评估中重要的信号是分歧：当“rollout/reward/mean”上升但“val/reward/mean”保持平稳时，奖励就被黑客攻击了。打开这些轨迹并将奖励的计分与评估的得分进行比较。这种比较会推动您的奖励设计迭代：收紧奖励解析器、重塑组件或整理数据，然后再次运行。每次迭代都比上次更快，因为环境和评估保持固定。只有奖励和数据会发生变化，MTRL 的每个模型的入门食谱都会为您提供一个调整点来开始。

例如，在我们最早的尝试之一中，我们试图同时在所有 SOP-Bench 任务上训练代理，这导致任务竞争和奖励波动：

![当所有SOP-Bench任务一起训练时训练奖励曲线波动](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/29/ML-21260-2.jpg)

图 2：尝试一起训练所有 SOP-Bench 任务时奖励波动

在将我们的数据限制为专注于单个任务（“aircraft_inspection”）后，我们注意到验证奖励下降，而推出奖励已经饱和。在我们的奖励公式中，最大奖励是 5.0，但奖励停滞在 3.7 左右：

![验证奖励下降时奖励曲线停滞在 3.7 左右](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/29/ML-21260-3.jpg)

图 3：奖励停滞和验证奖励下降

该模型没有在“aircraft_inspection”上获得全额奖励，并且与基本模型相比，微调模型的外部基准任务成功率有所下降。我们需要审查推出轨迹以找出原因。 SOP 的一次性示例在两个方面与任务的真实数据不匹配。它省略了数据所需的“cross_check_response”字段，因此模型无法生成完整的答案，并且它将输出包装在与评估预期不同的标签中。我们将示例与数据对齐，并删除了无法回答的字段，这让奖励和评估衡量的是同一件事。![aircraft_inspection 任务健康上升的奖励和验证奖励曲线](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/29/ML-21260-4.jpg)

图 4：SOP-Bench 的 Aircraft_inspection 任务的健康奖励信号

当根据外部基准衡量经过微调的 GPT-OSS 20B 模型的任务成功率 (TSR) 时，我们发现“aircraft_inspection”任务的 TSR 提高了 13%，每场准确率提高了约 16%，这证实了我们的奖励函数与我们的外部评估一致。

### 将它们放在一起：迭代循环

前面描述的片段加起来形成一个训练循环，按照引入的顺序运行。您首先构建环境和评估，因为它们是后续步骤所依赖的固定脚手架。然后，您根据该评估设计奖励，只有在此之后，您才能训练和读取指标。保持早期的部分固定是让每次通过的速度更快的原因，所以你的大部分努力都花在了奖励和数据上。对我们来说效果很好的版本：

- 收集代表性任务数据并分为训练集、验证集和保留测试集。
- 根据生产模式构建培训环境：密封、种子、可重复。
- 根据测试集进行外部评估，独立于奖励进行计算。
- 通过评估运行基础模型和前沿参考模型来建立基线。如果基本模型得分为零，请在继续之前停止并简化。
- 设计奖励，然后在进行任何训练之前根据基线的真实模型输出对其进行验证。
- 训练、监控部署/奖励、完成率和轨迹样本，以了解模型在训练期间产生的结果。
- 通过外部评估来评估训练后的模型。阅读轨迹，尤其是奖励和评估不一致的轨迹。
- 调整奖励、环境或数据，然后再次运行。

当曲线停止或崩溃时，请在调整其他任何内容之前按顺序遍历这些内容：|  |症状|首先要改变的|诊断确认|
|:---|:---|:---|:---|
| 1 | Reward flat from step 0 |验证模型输出格式与奖励一致 |对不同奖励进行独立评估，以使奖励格式与模型的输出结构保持一致 |
| 2 | Train reward flat, all groups score the same |将“group_size”从 8 降至 4 并增加“batch_size” | Watch `analysis/zero_adv_groups`, should drop |
| 3 | Train reward rising but `val/reward/mean` flat |奖励被盗。重新读取轨迹，收紧奖励解析器 |针对新的基线部署重新运行离线奖励审核 |
| 4 |第 40-80 步后奖励崩溃（降至 ~0.0）| Set `async_config.max_steps_off_policy = 0`. If on CISPO, switch to PPO with `(0.8, 1.2)` | Reward should stabilize, even if lower |
| 5 |奖励改进有限的摊位，所有旋钮都健康 |双倍 LoRA 容量（`lora_rank=64`、`lora_alpha=128`）|如果有成长空间，50 级以内的更高天花板 |

一次进行一项更改，观察每个决策 25-50 个训练步骤（梯度更新）的指标。在我们的运行中，当有意调整这些参数时，大多数故障在大约 30 个步骤内即可识别。

### 结论

你的奖励质量和你的评估决定训练是否产生有用的代理，这比算法或超参数更重要。奖励是模型优化的唯一信号，与其分开的评估可以告诉您代理是在学习任务还是在学习奖励。精心设计的奖励和与最终任务相匹配的评估可以产生一个有用的智能体；如果没有它们，即使是强大的算法也会产生一个在训练中看起来不错但在生产中失败的模型。

SageMaker AI 多轮 RL 负责运行分布式代理 RL 训练的大部分操作工作和复杂性，抽​​象出硬件、编排和训练引擎。借助 SageMaker AI 多轮 RL，您可以专注于创建准确的环境，其中 [Strands Agent](https://strandsagents.com/) 和 [AgentCore](https://aws.amazon.com/bedrock/agentcore/) 可以帮助您将生产环境过渡到代理设置，并专注于奖励设计、评估和参数调整。要开始使用代理强化学习，您可以浏览[MTRL 设置示例笔记本](https://github.com/aws/sagemaker-python-sdk/blob/db63167c994ad85c959bc89fb4641b86c77fe432/v3-examples/model-customization-examples/mtrl_finetuning_example_notebook_v3_prod.ipynb)。请参阅 [SageMaker AI 多轮 RL 文档](https://docs.aws.amazon.com/sagemaker/latest/dg/model-customize-mtrl.html) 了解服务级别指南，并参阅[奖励设计最佳实践](https://docs.aws.amazon.com/sagemaker/latest/dg/model-customize-mtrl-assets.html#model-customize-mtrl-assets-best-practices) 了解对奖励主题的更深入处理，或查看[这篇有关 GRPO 的 AWS 博客文章，其中包含可验证的奖励](https://aws.amazon.com/blogs/machine-learning/overcoming-reward-signal-challenges-verifiable-rewards-based-reinforcement-learning-with-grpo-on-sagemaker-ai/)。最后，[SOP-Bench 论文和数据集](https://github.com/amazon-science/SOP-Bench) 是此处使用的运行示例的来源。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
