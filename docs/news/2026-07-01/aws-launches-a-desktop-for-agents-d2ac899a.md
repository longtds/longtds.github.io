<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:01:00+08:00
source: The New Stack
domain: AI 基础设施
url: https://thenewstack.io/aws-workspaces-desktops-for-agents/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# AWS 推出面向代理的桌面

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:01 CST |
| 领域 | AI 基础设施 |
| 来源 | The New Stack |
| 原文标题 | AWS launches a desktop for agents |
| 原文 | [打开原文](https://thenewstack.io/aws-workspaces-desktops-for-agents/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

经过短暂的公开预览后，AWS 于周二推出了适用于代理的 Amazon WorkSpaces，您绝对不应该这样做 AWS 为代理推出桌面的帖子首先出现在 The New Stack 上。

## 正文

经过[简短的公开预览](https://aws.amazon.com/blogs/aws/modernize-your-workflows-amazon-workspaces-now-gives-ai-agents-their-own-desktop-preview/)，AWS 于周二正式推出了 [Amazon WorkSpaces for Agents](https://aws.amazon.com/workspaces/ai-agents/) — 您绝对不应该将其与 [Amazon Connect Agent Workspace](https://aws.amazon.com/products/connect/customer/agent-workspace/) 混淆。 Amazon WorkSpaces 是 AWS 基于云的持久桌面，适合希望为其员工配置虚拟桌面的企业。代理的工作空间也是虚拟桌面，但适用于需要在云中操作桌面应用程序的代理。

### 代理拥有自己的桌面

理想情况下，这意味着代理现在可以与公司的旧桌面应用程序进行交互，而无需构建自定义集成或对这些工具进行现代化改造。

AWS 此次发布的参考客户是荷兰跨国公司 Wolters Kluwer。

“我们的团队为世界各地的客户管理复杂的税务、法律和合规工作流程。Amazon WorkSpaces 现在让我们可以将 AI 代理直接放入这些工作流程中 — 他们可以访问和操作我们员工使用的相同业务应用程序，而我们无需重建任何内容，”Wolters Kluwer 工作场所技术总监 André Akkerman 在今天的声明中指出。 “对于我们如何看待自动化来说，这是有意义的一步。”

启用后，代理可以借助模型上下文协议 (MCP) 连接到这些桌面。从那里，他们可以根据需要流式传输会话并与桌面应用程序交互。访问由 AWS 的身份和访问管理服务管理，可审核性由 AWS CloudTrail 和 Amazon CloudWatch 处理。

### MCP + 计算机视觉

AWS 认为，MCP 和计算机使用代理的速度仍然相当慢（因为它们必须不断循环分析屏幕截图，然后采取行动），它们是互补的方法。

AWS 目前的做法是让用户在为服务创建主操作系统映像时在其工作区上安装文件系统 MCP 服务器。这样，代理就可以通过工具调用读取和写入文件，而不必经历屏幕截图循环。“正确的设计模式将每个子任务路由到最有效的可用界面 - 当存在 MCP 工具时调用 MCP 工具，只有当没有 API 覆盖该任务或与 GUI 交互本身就是目标时才回退到视觉驱动的操作，”该公司在其公告中解释道。 “这会带来复合效益：当大部分工作流通过 MCP 路由时，剩余的可视子任务会缩减为集中操作 — 更少的步骤、更短的序列、更少的故障。MCP 工具转发使这种模式在 WorkSpaces 应用程序实例中发挥作用。”

### 人类掌控

随着全面推出，AWS 还增加了人类监视代理并在需要时进行控制的能力。

“如果您观察到代理执行意外操作，停止按钮将为您提供直接干预，而无需重新启动会话或回滚状态。当您从开发转向生产时，您可以根据任务需要多少人工监督来决定适合每个工作流程的模式，”该公司解释道。

考虑到目前计算机使用代理的速度仍然很慢，没有人愿意长期照顾这些代理，这也不是对任何人工资的充分利用。因此，如果现在需要对给定任务进行大量监督，那么这对于该工作流程来说很可能不是一个很好的前进方向。

### 为代理提供身份

通过此次发布，AWS 还允许企业使用 Active Directory 为代理提供身份（以及相应的策略、访问控制和审核日志），这些公司已经将这些身份用于普通用户。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
