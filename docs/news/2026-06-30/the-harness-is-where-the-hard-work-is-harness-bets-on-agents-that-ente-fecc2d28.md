<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-30T23:00:00+08:00
source: The New Stack
domain: AI 基础设施
url: https://thenewstack.io/harness-autonomous-worker-agents/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# “线束就是辛苦所在”：线束押宝企业生产上可以信赖的代理商

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-30 23:00 CST |
| 领域 | AI 基础设施 |
| 来源 | The New Stack |
| 原文标题 | “The harness is where the hard work is”: Harness bets on agents that enterprises can trust in production |
| 原文 | [打开原文](https://thenewstack.io/harness-autonomous-worker-agents/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

代理平台 Harness 于周二推出了 Autonomous Worker Agents，使企业能够用 AI 替换交付管道中的固定脚本。《Harness 是艰苦工作所在》的帖子：Harness 押注于企业在生产中可以信任的代理，首先出现在 The New Stack 上。

## 正文

代理平台 Harness 于周二推出了 [Autonomous Worker Agents](https://www.harness.io/products/platform/worker-agents)，使企业能够用人工智能代理替换其交付管道中的固定脚本，这些代理通过部署、测试和安全扫描等任务进行推理，所有这些都在这些公司已经使用的治理和审计控制下。

Harness 的管道长期以来一直运行着一系列确定性步骤，例如将代码部署到 Kubernetes 或运行安全扫描。现在，这些步骤中的任何一个都可以作为代理运行，这使得它们更加灵活，同时保持相同的护栏。

当然，这家公司对代理商来说并不陌生。 Harness 的专家代理自去年开始正式上线，为开发人员提供建议并帮助从聊天窗口或 IDE 编写管道。自治工作代理更进一步：管道中的任何步骤现在都可以作为代理在客户控制的基础设施上运行。

>

“构建代理变得越来越容易，但最难的是利用工具。”

但正如 [Harness](http://harness.io) 首席执行官兼创始人 [Jyoti Bansal](https://www.linkedin.com/in/jyotibansal/) 告诉 The New Stack 的那样，“构建代理正变得越来越容易，但最困难的地方就是利用线束。”

“当我创办公司时，我给了 Harness 这个名字，因为我认为开发人员编写的所有代码都需要一个安全带，”Bansal 说。对他来说，工人代理标志着公司的第四阶段，在可靠的部署、[代码之后发生的其余工作](https://thenewstack.io/harness-ceo-jyoti-bansal-on-why-ai-coding-doesnt-help-you-ship-faster/) 和专家代理之后。

不过，他认为第四阶段有很大不同。

>

“在生产中运行代理与运行我们现在都使用的编码代理是非常不同的。”

“在生产中运行代理与运行我们现在都使用的编码代理是非常不同的，”Bansal 说。 “如果你使用编码代理，最糟糕的情况是你得到了一个糟糕的 PR，一些代码审查代理或一些进行代码审查的人会拒绝 PR，或者你的下游 CI/CD 管道会在某个地方捕获它。但如果你是下游 CI/CD 管道，就没有其他方法可以捕获它。”

### 就像 Markdown 一样简单构建代理与用 Markdown 编写技能文件没有太大区别。代理在单个 Markdown 文件中定义，开发人员用简单的英语编写指令。该版本称其为代理文件格式，已“成为整个行业的标准”。正如这些工具所常见的那样，不愿意编写文件的团队可以让 Harness AI 生成该文件。一旦启动并运行，代理就会利用 Harness [软件交付知识图](https://www.harness.io/blog/knowledge-graph-rag)，这是公司的客户服务、管道、部署、事件和安全发现的地图。

### 安全带

为了实现所有这些工作，Harness 正在构建过去几年构建的核心功能，事实证明，这些功能也适用于代理。 Worker Agent 在 [delegates](https://developer.harness.io/docs/category/delegate) 上运行，Harness 组件在客户自己的基础设施内运行，因此代理在生产系统所在的位置执行，而不是在 Harness 的云内执行。每个代理都在沙盒容器中运行，文件和网络访问受到限制，拥有自己的身份和权限，而且最重要的是，由控制人工部署的同一策略引擎进行管理。

对于要在[软件生命周期的这一部分](https://thenewstack.io/ai-has-become-integral-to-the-software-delivery-lifecycle/) 中部署代理的企业，他们必须能够验证代理所做的事情。几家初创公司已经将代理可审计性作为产品出售； Harness 正在将其融入到服务中。 Bansal 称其为“巨大的挑战”，因为涉及生产的管道必须记录触发代理的原因、运行的提示、轮转次数以及产生的内容。 Harness 已经在其脚本步骤中记录了所有这些，因此代理只是它已经跟踪的管道中的另一个操作。

Harness 还内置了成本控制功能，用于控制代理可以花费多少代币，Bansal 表示，现在每个客户对话中都会提到这一点。工作代理跟踪每个代理和每个管道的代币支出，并在运行失控之前暂停预算上限以供批准。

### 代理市场Harness 将框架与代理市场配对，

该市场包含三层中的数十个预构建代理：Harness 托管代理（公司通过 SLA 构建和支持）、由合作伙伴构建并由 Harness 审核的 Harness 认证代理，以及任何人都可以发布的社区代理。每个代理都可以被分叉。

社区层是信任变得更加困难的地方。 “如果你采用社区构建的代理，你就需要持保留态度，”班萨尔说。他说，无论代理来自哪里，沙箱、范围凭证和策略控制都会有效，而且社区代理是开源的，因此团队可以在运行之前读取代理并对其进行分叉以适应。对于大型企业来说，大门比目录更重要：公司可以批准少数托管代理进行生产并阻止其余代理。

Harness 并不是唯一将代理引入交付渠道的方法。 GitHub 在今年早些时候推出了 Agentic Workflows，它在 GitHub Actions 内运行 Markdown 定义的代理，并于今年早些时候推出预览版，GitLab 的 Duo Agent Platform 允许团队在整个软件生命周期中构建自己的代理。 GitHub 使用与 Harness 相同的代理文件约定。编码代理供应商也在向下游推进。

不过，班萨尔并不一定将他们视为竞争对手。他认为，编写代码后的工作是一个不同的问题，处理它的代理必须清除更高的标准。 Harness 拥有 1,000 多家企业客户，认为其优势是双重的：其知识图为其代理提供的上下文，以及其花费数年时间构建确保生产管道安全的机制。

### 第五阶段：自主软件工程

如果这是 Harness 的第四阶段，那么显而易见的问题是下一阶段会是什么样子。

>

“对我来说，第五阶段完全是关于自主软件工程。”

“对我来说，第五阶段完全是关于自主软件工程，”班萨尔说。 “我们的目标是，整个软件工程过程，从 Jira 票据一直到生产，都是一个自治过程，由一组代理执行所有任务，从编码代理到我们正在启动的交付代理，以及如何编排这一切。但是，根据存在的风险、变更的风险以及它对生产系统可能产生的影响，如何让人员参与到流程中？”

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
