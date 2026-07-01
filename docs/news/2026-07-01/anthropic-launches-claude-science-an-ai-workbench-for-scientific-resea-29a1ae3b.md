<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T01:00:00+08:00
source: The New Stack
domain: 技术动态
url: https://thenewstack.io/anthropic-claude-science-workbench/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# Anthropic 推出 Claude Science，一个用于科学研究的人工智能工作台

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 01:00 CST |
| 领域 | 技术动态 |
| 来源 | The New Stack |
| 原文标题 | Anthropic launches Claude Science, an AI workbench for scientific research |
| 原文 | [打开原文](https://thenewstack.io/anthropic-claude-science-workbench/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

周二，Anthropic 推出了 Claude Science，这是一款供科学家使用的新应用程序，可以在 macOS 和 Linux 上本地运行。

## 正文

周二，Anthropic 推出了 [Claude Science](https://claude.com/product/claude-science)，这是一款面向科学家的新应用程序，可以在 macOS 和 Linux 上本地运行，也可以在远程计算机上运行。 Anthropic 将其描述为人工智能工作台，“科学家可以在一个地方进行研究”。

无论从设计还是精神上来说，它都有点像科学家的Claude·科沃克（Claude Cowork）。

目前，处于测试阶段的 Claude Science 主要针对生命科学领域的研究人员，但从名称来看，该公司计划随着时间的推移扩大这一范围。

### 在 

Claude 的付费计划中可用

要使用它，您不必是科学家。它可在 macOS 和 Linux 上供 Claude Pro、Max、Team 和 Enterprise 计划的所有用户使用（但对于 Team 和 Enterprise 计划，管理员必须首先启用它）。 Anthropic 还为研究实验室提供折扣团队计划。

Anthropic 指出，科学家经常必须在众多数据库和工具（例如 PubMed、Jupyter、R 和终端）之间切换。 Claude Science 的承诺是通过将 Anthropic 的先进模型与这些研究人员已经使用的数据库、平台和工具连接起来，将所有这些结合在一起。

信用：人类

与大多数领域一样，科学研究涉及大量重复性工作，而这些工作实际上并不能推动科学的发展。 Anthropic 在其公告中写道，该工具旨在帮助“研究人员分析文献并执行多步骤研究，并且以工件为先，允许用户迭代地完善图表和手稿，直到准备好发表。每个输出都带有可审计的制作历史，以便科学家可以验证和重现结果。”

### 不是新型号

Anthropic 强调，它并不是为 Claude Science 推出新模型。相反，它受到标准 Claude 模型的支持。当用户使用该工具时，他们首先与一个通才协调代理进行交互，该代理可以访问 60 多个数据库和一组相关技能。这些工具还支持可以通过 MCP 连接到的任何其他服务。

Anthropic 实际上正在使用 Nvidia 新的 [BioNeMo Agent Toolkit](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit) 中的技能来连接生命科学模型和库，包括 Evo 2、Boltz-2 和 OpenFold3。

>

“专业科学属于构建它的合作伙伴。”值得注意的是，OpenAI 还[集成](https://nvidianews.nvidia.com/news/nvidia-launches-bionemo-agent-toolkit-giving-ai-agents-the-tools-to-accelerate-scientific-discovery) BioNeMo Agent 工具包。

信用：人类

正如 Anthropic 还指出的那样，Claude科学意味着推理层和结缔组织。 “专业科学属于构建它的合作伙伴，”该公司解释道。

与 Jupyter 笔记本和类似工具一样，Claude Science 也可以生成视觉效果，包括 3D 蛋白质结构和基因组浏览器轨迹。 “用户可以与代理讨论任何细节，在线注释图表和手稿，以便代理知道要解决什么问题，以便为出版做好准备，”Anthropic 解释道。

这些可视化的代码始终可用，其创建的完整消息历史记录也是如此。

### 连接到 HPC 和 Modal

由于 Claude 本身无法准确运行大型基因组学管道或蛋白质折叠作业，因此这些工具还可以通过 SSH 或 [Modal](https://modal.com) 帐户与现有的高性能计算集群进行交互。 Anthropic 认为，这可以确保研究人员不必浪费时间来编写这些作业并排除故障。相反，Claude将起草一份计划，研究人员将对其进行审查，然后Claude将其提交给实验室的现有资源。

然后，代理会密切关注工作及其输出，并标记任何问题。也可以随时分叉会话来尝试不同的方法。

### 比赛

LLM确实适合 Claude Science 这样的服务，而谷歌、OpenAI 和其他公司正在朝同一方向努力。

例如，在 5 月份的 I/O 会议上，谷歌推出了“Gemini for Science”，并明确[宣传](https://blog.google/innovation-and-ai/technology/research/gemini-for-science-io-2026/) 为“桌面上的科学工作台”，将 30 多个生命科学数据库及其“AI 联合科学家”假设引擎的科学技能捆绑在一起。当然，谷歌的 DeepMind 在利用人工智能进行生命科学研究方面也有着悠久的历史，并因此获得了诺贝尔奖。OpenAI 还通过 [Prism](https://openai.com/prism/)（其科学写作工具）和 [GPT-Rosalind](https://openai.com/index/introducing-gpt-rosalind/)（专门为加速科学研究和药物发现而构建的前沿模型）等服务来关注科学和早期焦点。然而，随着今年 4 月 [Kevin Weil](https://www.wired.com/story/openai-executive-kevin-weil-is-leaving-the-company/) 的离职，OpenAI 解散了 OpenAI for Science 和 Sunset Prism，将重点转向更多核心服务（和 Codex）。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
