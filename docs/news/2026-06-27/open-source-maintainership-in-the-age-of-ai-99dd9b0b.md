<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-27T02:00:00+08:00
source: Kubernetes Blog
domain: 云原生
url: https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 人工智能时代的开源维护

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-27 02:00 CST |
| 领域 | 云原生 |
| 来源 | Kubernetes Blog |
| 原文标题 | Open source maintainership in the age of AI |
| 原文 | [打开原文](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

人工智能确实改变了软件开发的游戏规则。越来越多的人利用人工智能为他们使用的项目提供补丁。对我来说，这是一件好事，因为更多的人会贡献补丁而不是分叉或不修复它们。主要问题是人工智能使代码生成速度加快，但在维护代码库方面却几乎没有什么改进。在这篇文章中，我们将重点介绍 Kubernetes 社区适应人工智能辅助编码世界的方式。这一旅程的第一步是制定人工智能政策。这看似平凡且官僚，但有许多 PR 偏离了有关人工智能使用的讨论。人工智能政策有助于引导围绕项目对人工智能立场的对话，并向贡献者提供关于如何负责任地使用这些工具的明确信号。 Kubernetes 人工智能政策 Kubernetes 项目为人工智能辅助贡献制定了明确的指导方针，平衡创新与责任。这些政策旨在维护代码质量并确保人工监督，同时承认人工智能工具可以在开发过程中提供宝贵的帮助。透明度第一 贡献者必须披露人工智能工具何时被使用

## 正文

## AI 时代的开源维护

作者：Kevin Hannon（红帽）| 2026 年 6 月 26 日星期五

人工智能确实改变了软件开发的游戏规则。越来越多的人利用人工智能为他们使用的项目提供补丁。对我来说，这是一件好事，因为更多的人会贡献补丁而不是分叉或不修复它们。主要问题是人工智能使代码生成速度加快，但在维护代码库方面却几乎没有什么改进。在这篇文章中，我们将重点介绍 Kubernetes 社区适应人工智能辅助编码世界的方式。

这一旅程的第一步是制定人工智能政策。这看似平凡且官僚，但有许多 PR 偏离了有关人工智能使用的讨论。人工智能政策有助于引导围绕项目对人工智能立场的对话，并向贡献者提供关于如何负责任地使用这些工具的明确信号。

### Kubernetes 

AI 策略[](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/#kubernetes-ai-policy)

Kubernetes 项目制定了[人工智能辅助贡献的明确指南](https://www.kubernetes.dev/docs/guide/pull-requests/#ai-guidance)，以平衡创新与问责制。这些政策旨在维护代码质量并确保人工监督，同时承认人工智能工具可以在开发过程中提供宝贵的帮助。

#### 透明度优先[](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/#transparency-first)

贡献者必须披露何时使用人工智能工具来协助拉取请求。 PR 描述中的简单声明（例如“此 PR 部分是在生成式 AI 的帮助下编写的”）就足够了。这种透明度有助于审阅者了解背景并进行适当的审查。

#### 人类责任[](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/#human-accountability)

虽然人工智能工具可以提供帮助，但人类贡献者仍然对每一个变化负全部责任。该政策明确禁止：

- 将 AI 列为提交的共同作者
- 在提交上使用人工智能共同签名
- 添加诸如“协助”或“共同开发”之类的预告片，将工作归因于人工智能这并不是要削弱人工智能作为工具的作用，而是要保持明确的责任。如果出现问题，需要有人了解原因并能够修复它。

#### 共同作者的 CLA 强制执行[](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/#cla-enforcement-for-co-authors)

CNCF 提供了一个[工具](https://github.com/cncf/cla)，用于验证每个拉取请求的贡献者许可协议。 AI 代理无法解决这些贡献者许可协议，因此该项目采取的一项强制措施是为共同作者启用 CLA 检查。这向审阅者提供了一个标志，表明 PR 尚未准备好合并。

#### 需要人工参与[](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/#human-engagement-required)

也许该政策最关键的方面是：审核者希望与人类互动，而不是与人工智能互动。贡献者不能依赖人工智能来回复评论意见。如果您无法亲自解释人工智能帮助产生的变化，您的 PR 将被关闭。此要求确保知识转移的发生，并且贡献者真正理解他们提交的代码。

#### 验证义务[](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/#verification-obligations)

贡献者必须通过代码审查、测试和个人理解来验证人工智能生成的更改。仅仅让代码工作是不够的——您需要知道它为什么工作并且能够维护它。

这些政策反映了一种成熟的人工智能方法：将其视为一种工具，但绝不让它取代Anthropic 的判断、理解或责任。

### 自动人工智能评论[](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/#automated-ai-reviews)

有许多工具可以帮助审查代码。 AI 拉取请求工具带来了治理挑战，因此社区承担的首要任务之一是[记录流程](https://github.com/kubernetes/community/blob/main/github-management/ai-code-review-tools.md)，了解引入新 AI 工具所需的内容。这些工具的主要评估标准之一是找到愿意在 kubernetes-sigs 存储库中测试它们的维护者。 Kueue、JobSet 和 Agent-Sandbox 一直在尝试使用这些工具来为维护人员提供更多支持。#### 副驾驶[](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/#copilot)

许多维护人员开始使用的工具之一是 GitHub Copilot。 CNCF 为维护者提供了[访问权限](https://contribute.cncf.io/blog/2025/12/16/github-copilot-enterprise-for-maintainers/)，因此这最终成为许多人开始使用的第一个工具。它在调整评论方面提供了一些很好的经验，但这个工具也存在一些成长的烦恼。社区采用的最大障碍是依赖贡献者拥有副驾驶执照。只有维护人员才能请求副驾驶审查，而社区无法自动审查拉取请求。 AI审查工具的目标之一是提供维护人员不需要请求的自动化审查工具。这表明需要组织控制，而不是依赖贡献者的访问权限。

#### CodeRabbit[](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/#coderabbit)

2026 年中，Kubernetes 社区已将 CodeRabbit 推广到了一些项目。与副驾驶一样，需要进行一些调整才能提供更好的评​​价，但总体反馈是积极的。该工具有很多可用的配置，该工具最有趣的用途之一来自代理沙箱。

AI 拉取请求工具可以成为质量关卡。贡献者至少可以得到快速的抽查审查，而无需等待维护人员。 Agent-sandbox 在 PR 上添加了标签，以反映仍然需要解决一些来自 AI 工具的评论。

### 后续步骤[](https://kubernetes.io/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai/#next-steps)

现实情况是，在开源项目中利用人工智能是一个积极探索的领域。社区可以利用您的帮助来调整评论工具、评估工具或评估人工智能领域的新兴技术。

我们正在探索更多的一些领域：

- 使用人工智能技能来减少维护人员的倦怠。
- 人工智能协助对失败的测试进行分类。
- 帮助 Kubernetes 操作方面的技能。

这是[原始文章](https://www.kubernetes.dev/blog/2026/06/26/open-source-maintainership-in-the-age-of-ai) 的镜像。

- [←上一页](https://kubernetes.io/blog/2026/06/25/headlamp-cluster-api-plugin/)
- 下一步→最后修改时间为太平洋标准时间 2026 年 6 月 23 日晚上 11:34：[发布：AI 政策 Kubernetes (709817df7c)](https://github.com/kubernetes/website/commit/709817df7c25a26eb185198f1e216dcb461335eb)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
