<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T08:08:34+08:00
source: The New Stack
domain: AI 基础设施
url: https://thenewstack.io/anthropic-fable-ban-lifted/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# 《Fable》卷土重来：联邦政府取消对 Anthropic人工智能模型的出口管制

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 08:08 CST |
| 领域 | AI 基础设施 |
| 来源 | The New Stack |
| 原文标题 | Fable is coming back: Federal government lifts export controls on Anthropic AI model |
| 原文 | [打开原文](https://thenewstack.io/anthropic-fable-ban-lifted/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

Anthropic 现在可以带回Fable。美国商务部正在取消对两种人工智能模型的出口管制，《Fable》的帖子又回来了：联邦政府取消了对 Anthropic AI模型的出口管制，首先出现在 The New Stack 上。

## 正文

Anthropic 现在可以带回Fable。美国商务部正在取消两周多前对《Fable 5》和《Mythos 5》这两款人工智能模型实施的出口管制。

美国商务部长霍华德·卢特尼克在周二发给 Anthropic 联合创始人汤姆·布朗的一封信中写道，“Anthropic 已同意主动检测和解决与模型相关的安全风险”，并“与美国政府就《Mythos》、《Fable》和未来模型的协议、标准和版本进行努力合作。”

信中称，Anthropic 还同意向美国政府通报任何恶意活动。

现在，Anthropic 可以自由地再次向用户提供《Fable》。

>

我们收到通知，商务部已取消对《Claude Fable 5》和《Mythos 5》的出口管制。

我们将于明天开始恢复访问，并将很快分享更新。

我们感谢用户的耐心，以及所有与我们合作的人……

— Anthropic (@AnthropicAI) [2026 年 6 月 30 日](https://x.com/AnthropicAI/status/2072106151890809341?ref_src=twsrc%5Etfw)

### 发生了什么？

6 月 12 日，美国政府对 Anthropic 迄今为止最强大的消费者模型《Fable》（Anthropic 迄今为止最强大的消费模型）推出三天后[实施出口管制](https://thenewstack.io/us-gov-orders-anthropic-to-pull-fable-5-and-mythos-5-three-days-after-launch/)，原因是当时所谓的“[越狱](https://thenewstack.io/fable-5-and-mythos-5-remain-suspended-the-ball-is-in-anthropics-court/)”。

由于 Anthropic 无法确保只有美国公民才能使用 Fable（更不受限制的 Mythos 模型的消费者版本），因此它别无选择，只能关闭所有人的访问权限，包括有权访问 Mythos 的一小部分组织。

引发这一事件的越狱的确切性质尚不清楚，但从那时起《Fable》就无法使用，政府施加的这些限制引起了整个行业的紧张，特别是在中国公司推出[竞争日益激烈](https://z.ai/blog/glm-5.2)模型的时候。

政府已于 6 月 26 日星期五取消了对 Mythos 模型的一些限制，使其再次可供专注于网络安全和基础设施的公司和机构使用。

#### Anthropic、Fable 和美国政府：

- [五角大楼的 Anthropic 问题是每个企业的人工智能问题](https://thenewstack.io/pentagon-anthropic-model-orchestration/)
- [Fable 5 vs Opus 4.8：真正的利害关系，而不是规格表](https://thenewstack.io/fable-5-opus-comparison/)
- [联邦政府命令 Anthropic 在发布三天后撤下《Fable 5》和《Mythos 5》](https://thenewstack.io/us-gov-orders-anthropic-to-pull-fable-5-and-mythos-5-three-days-after-launch/)
- [Fable 5 和 Mythos 5 仍然暂停：“球在 Anthropic 的球场上”](https://thenewstack.io/fable-5-and-mythos-5-remain-suspended-the-ball-is-in-anthropics-court/)
- [Anthropic Fable 的混乱，解释](https://thenewstack.io/anthropic-fable-mess-explained/)

在 Anthropic 拒绝取消美国国防部针对大规模国内监视和全自动武器的合同保障措施后，Anthropic 与美国政府已经[关系紧张](https://www.anthropic.com/news/where-stand-department-war)。

作为回报，国防部将 Anthropic 指定为供应链风险，实际上禁止该机构的所有承包商和供应商使用其服务。许多法律挑战至少维持了国防部的部分指定，但允许其他机构继续使用 Anthropic 的服务

虽然这两种情况没有直接联系，但很难不将 Fable 控制视为Anthropic 与特朗普政府之间现有敌意的延伸（在某种程度上，这似乎也是[个人](https://www.wired.com/story/the-trump-white-house-is-over-anthropics-dario-amodei/)）。

然而，自从对 Fable 实施出口管制以来，随着商务部长霍华德·卢特尼克及其工作人员会见了由 Anthropic 代表组成的[轮流小组](https://nypost.com/2026/06/25/business/anthropics-weirdo-ceo-dario-amodei-replaced-by-co-founder-in-high-stakes-white-house-meetings-report/)，Anthropic 与美国政府之间的关系逐渐解冻。

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
