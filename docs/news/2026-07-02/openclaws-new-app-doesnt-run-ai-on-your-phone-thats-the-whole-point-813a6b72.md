<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T05:00:00+08:00
source: The New Stack
domain: 技术动态
url: https://thenewstack.io/openclaw-persistent-agent-architecture/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# OpenClaw 的新应用程序不会在你的手机上运行人工智能。这就是重点。

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 05:00 CST |
| 领域 | 技术动态 |
| 来源 | The New Stack |
| 原文标题 | OpenClaw’s new app doesn’t run AI on your phone. That’s the whole point. |
| 原文 | [打开原文](https://thenewstack.io/openclaw-persistent-agent-architecture/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

OpenClaw 本周终于放弃了 iOS 和 Android 应用程序，这意味着你现在可以放弃 Telegram 和 WhatsApp 方法了。 OpenClaw 的新应用程序不会在你的手机上运行人工智能。这就是重点。首先出现在 The New Stack 上。

## 正文

[OpenClaw](https://openclaw.ai) 终于在本周放弃了 iOS 和 [Android](https://play.google.com/store/apps/details?id=ai.openclaw.app&hl=en_IN) 应用程序，这意味着您现在可以放弃 Telegram 和 WhatsApp 方法，直接与您的个人 AI 代理对话。但可以说更令人兴奋的是，该应用程序实际上并没有在你的手机上运行人工智能。它只是连接到您已经在其他地方运行的代理。您的手机现在充当该代理的窗口，具有语音、通知和摄像头访问功能。

这是一个不错的设计选择，也正是个人人工智能代理的发展方向。

### 电话成为经过身份验证的端点

这款手机基本上正在成为 OpenClaw 的真正智能遥控器。开发人员不再将功能日益强大的代理塞到电池和内存有限的手机上，而是将手机视为居住在其他地方的代理的另一个屏幕。无论您的手机在手中还是在另一个房间充电，客服人员都会继续工作。

在此模型中，手机会批准操作，向您发送通知，让您与客服人员交谈，并在客服人员需要关注某些内容时共享您的相机。

### 持久运行时取代移动限制

但 OpenClaw 并不是第一个这样做的。 Anthropic 的 [Claude Cowork with Dispatch](https://thenewstack.io/claude-dispatch-versus-openclaw/) 遵循非常相似的模式。用户通过手机分配工作，但执行发生在持久的桌面运行时上。移动应用程序充当启动任务、监控进度和接收结果的伴侣，而不是成为代理本身。

OpenAI 也在朝着类似的方向发展。通过 [Codex](https://thenewstack.io/openai-codex-chatgpt-mobile/)，开发人员越来越多地与长期运行的编码代理进行交互，这些代理继续独立工作并可以从多个客户端进行检查，而不是将手机视为代理运行的地方。

不同的公司，不同的产品，但相似的架构赌注是让代理在持久运行时运行，并为人们提供轻量级客户端与其交互。

当多个团队独立地聚合到同一个架构模式时，这通常是一个早期信号，表明行业已经找到了解决实际工程问题的模型。

### 现在工程问题完全不同了

这种转变改变了开发人员花时间思考的事情。 Building mobile apps used to mean worrying about battery life, memory limits, offline mode, and squeezing the best performance out of a phone.如果代理在其他地方运行，那么大多数担忧就会消失。

现在，我想到了一系列新的问题，例如电话如何安全地连接到长期运行的代理？ How do you manage permissions across multiple devices? What happens if every client disconnects but the agent keeps working?

### 登录屏幕之外的代理身份

这里有下游效应。一旦电话只是与您的代理交谈的多个受信任端点之一，您就需要一种更强大的身份识别方法。您不再将用户登录到应用程序中。 You’re authenticating devices into an ongoing relationship with a persistent agent.

随着该代理获得读取文件、发送电子邮件、调用 API 和控制外部工具的能力，身份验证将成为承载基础设施。

### 分布式代理重塑开发者工具

稍微缩小一点，看看更大的图景，突显出个人人工智能代理越来越类似于分布式系统，而不是移动应用程序。智能存在于持久的运行时间中，而手机是多个经过身份验证的端点之一。

For developers, the mobile app is only part of the job.他们还必须构建保持代理运行的组件，将其连接到用户的设备，并确保这些连接保持安全。

代理保持独立运行，而手机只是另一个检查、批准操作或开始对话的地方。

将 OpenClaw 与 Anthropic 和 OpenAI 放在一起看，很难不注意到相同的模式。 The agent keeps running independently, while the phone is simply another place to check in, approve actions or start a conversation.该架构解决了许多实际问题，这也许可以解释为什么多家公司正朝着同一方向前进。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
