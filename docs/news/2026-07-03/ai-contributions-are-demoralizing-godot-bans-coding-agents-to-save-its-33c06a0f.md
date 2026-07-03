<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-03T04:31:26+08:00
source: The New Stack
domain: AI 基础设施
url: https://thenewstack.io/godot-bans-ai-coding-agents/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# “人工智能的贡献令人士气低落”：Godot 禁止编码代理以挽救其指导模型

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-03 04:31 CST |
| 领域 | AI 基础设施 |
| 来源 | The New Stack |
| 原文标题 | “AI contributions are demoralizing”: Godot bans coding agents to save its mentoring model |
| 原文 | [打开原文](https://thenewstack.io/godot-bans-ai-coding-agents/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

Godot 引擎是 Unity 等游戏引擎的开源替代品，正在重写其贡献政策，以禁止大多数 AI 生成的帖子“AI 贡献令人士气低落”：Godot 禁止编码代理以保存其指导模型，该帖子首先出现在 The New Stack 上。

## 正文

[Godot Engine](https://godotengine.org/) 是 Unity 等游戏引擎的开源替代品，正在重写其[贡献政策](https://contributing.godotengine.org/en/latest/pull_requests/pull_request_guidelines.html)，以禁止其存储库中大多数人工智能生成的代码。

在此之前，管理该项目的非营利组织 [Godot Foundation](https://godot.foundation/) 进行了数月的内部讨论，维护人员表示，他们无法再跟上积压的拉取请求（其中许多是人工智能编写的）的步伐。

然而，基金会还指出，压力不仅仅在于管理人工智能生成的大量垃圾，还在于审查拉取请求应该完成的任务。它的论点是，审查代码一直是一项艰巨的任务，但它也是培训未来维护人员的一种方式，一旦另一端的贡献者是机器而不是人，这种情况就不再成立。

>

“人工智能的贡献还会带来令人士气低落的额外痛苦。”

正如基金会所说，“人工智能的贡献会带来士气低落的额外痛苦”，因为拉取请求上留下的反馈不会改变模型下次的行为方式，而且基金会表示不能相信人工智能的重度用户能够很好地理解自己的代码，从而自己根据反馈采取行动。

“审查 PR 已经是一项乏味的工作，但它是有益的，因为审查者普遍认为他们的努力有助于培养新的贡献者——他们可能会成为未来的维护者/审查者），”基金会[写道](https://godotengine.org/article/contribution-policy-2026/)。 “如果你对 PR 的反馈只是被机器吸收，而不是用于指导潜在的未来维护者，那么你就很难证明将你的空闲时间花在 PR 审查上是合理的。”

>

“审查 PR 已经是一项乏味的工作，但它是有益的，因为审查者普遍认为他们的努力有助于培养新的贡献者。”

### 缩小差距据基金会称，自主人工智能代理和“vibe-coded”拉取请求已经触发了 Godot GitHub 存储库的自动禁令，尽管目前尚未写入 Godot 发布的贡献指南中。目前仍在进行中的这一新更新将更进一步：它通过禁止人工智能生成任何实质性代码片段来缩小这一差距，无论请求来自机器人还是粘贴在人工智能输出中的人类——即使人类随后对其进行审查和披露。

贡献者仍然可以使用人工智能来完成狭窄的、低风险的任务，例如代码完成、正则表达式或查找和替换，只要他们在拉取请求中披露它。除了人类书写文本的机器翻译之外，与维护人员讨论时人工智能生成的文本也是禁止的。

值得注意的是，新贡献者（定义为具有三个或更少合并拉取请求的任何人）现在必须在提交新功能或大型重构之前获得明确的签字。

### ‘贡献者扑克’

戈多的导师论点对于开源领域来说并不是全新的。早在四月份，[系统编程语言 Zig](https://thenewstack.io/introduction-to-zig-a-potential-heir-to-c/) 对人工智能辅助贡献采取了[类似的零容忍政策](https://kristoff.it/blog/contributor-poker-and-ai/)，Zig 软件基金会社区副总裁 [Loris Cro](https://kristoff.it/) 认为审查拉取请求的全部目的是投资于提交请求的人，而不仅仅是代码本身。他将这种动态称为“贡献者扑克”，并写道“在贡献者扑克中，你赌的是贡献者，而不是他们第一个公关的内容”——他借用了扑克格言“你玩的是人，而不是牌”。

克罗认为，人工智能生成的拉取请求完全打破了这种计算，因为如果另一端没有人从中学习，维护者的审查时间对于构建未来的贡献者没有任何帮助。

其他项目，包括终端仿真器 [Ghostty](https://github.com/ghostty-org/ghostty/pull/10412) 和 C 库 [curl](https://daniel.haxx.se/blog/2025/07/14/death-by-a-thousand-slops/)，针对相同的潜在问题限制或关闭了部分贡献管道，其推理更多地关注审查负担和虚假错误报告，而不是具体的指导。

### 人才管道Godot 和 Zig 的政策与人们对人工智能对软件初级人才管道影响的更广泛担忧并存，而且潜在的担忧大致​​相同，只是在不同的时间点发生。这种担忧的企业版本是入门级工作消失，因为人工智能现在承担了曾经分配给初级开发人员的任务。

正如 The New Stack [4 月报道](https://thenewstack.io/agentic-ai-junior-developer-crisis/) 所示，微软的 Mark Russinovich 和 Scott Hanselman [警告](https://cacm.acm.org/opinion/redefining-the-software-engineering-profession-for-ai/) 一旦公司依靠高级工程师与 AI 工具搭配而不是雇用初级开发人员，“该行业的人才管道就会崩溃，组织将面临没有下一代经验丰富的工程师的未来。”

>

“我们需要采取措施减轻维护人员的负担，同时确保我们仍然有渠道指导新贡献者成为未来的维护人员。”

即使没有人被解雇，同一问题的开源版本也会出现。初级贡献者仍然存在并且仍然愿意提交代码 - 但如果该代码是由人工智能而不是他们编写的，那么维护者的反馈仍然无处可去，并且将首次贡献者转变为未来维护者的非正式管道将停止运行，就像贡献者根本没有出现一样。

戈多基金会表示，随着人工智能工具的变化，预计将继续重新审视该政策，并将其当前的做法描述为“保守”。

该基金会表示：“我们需要采取措施减轻维护者的负担，同时确保我们仍然有渠道指导新贡献者成为未来的维护者。”

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
