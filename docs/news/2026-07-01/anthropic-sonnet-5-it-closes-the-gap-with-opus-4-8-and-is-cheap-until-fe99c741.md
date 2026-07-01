<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T02:00:00+08:00
source: The New Stack
domain: AI 基础设施
url: https://thenewstack.io/claude-sonnet-5-launch/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# Anthropic Sonnet 5：它缩小了与 Opus 4.8 的差距，并且在 8 月之前都很便宜

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 02:00 CST |
| 领域 | AI 基础设施 |
| 来源 | The New Stack |
| 原文标题 | Anthropic Sonnet 5: It closes the gap with Opus 4.8, and is cheap until August |
| 原文 | [打开原文](https://thenewstack.io/claude-sonnet-5-launch/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

Anthropic on Tuesday launched Sonnet 5, the latest model in its mainstream Sonnet series.该公司将 Sonnet 5 称为“后 Anthropic Sonnet 5”：它缩小了与 Opus 4.8 的差距，并且价格便宜，直到 8 月首次出现在 The New Stack 上。

## 正文

Anthropic 于周二[推出了 Sonnet 5](https://www.anthropic.com/news/claude-sonnet-5)，这是其主流 Sonnet 系列的最新型号。

该公司将 Sonnet 5 称为“迄今为止最具代理性的 Sonnet 模型”，从基准来看，其性能接近 [Opus 4.8](https://thenewstack.io/claude-opus-48-release/)，并且比 [Sonnet 4.6](https://thenewstack.io/claude-sonnet-46-launch/) 有了显着改进。 Anthropic 特别指出，它在涉及推理、工具使用、软件编码和知识工作的任务上表现得更好。

与之前发布的一些 Sonnet 不同，它的性能并没有完全优于大型 Opus 型号的最新版本，但它已经足够接近，暂时可以成为 Opus 4.8 的更实惠的替代品 - 因为 Opus 5 不会落后太远（假设它没有 [像《Fable 5》那样受到阻碍](https://thenewstack.io/us-gov-orders-anthropic-to-pull-fable-5-and-mythos-5-three-days-after-launch/)）。

Anthropic 强调 Opus 4.8，尤其是在更高的推理水平上，仍将提供更高的准确性。但还指出，“Sonnet 5 为开发人员提供了价格较低的选择，但质量比以前可用的要高得多。”

Sonnet 5 基准测试。信用：人类

在其最高的超高推理水平下，Sonnet 5 在 OSWorld 验证和代理搜索 BrowseComp 基准测试中的表现与 Opus 4.8 的中到高设置大致一致。但由于在相当的推理水平上，它的运行成本也比 Opus 4.8 更高，因此 Opus 4.8 仍然是某些任务的更好选择。

信用：人类

Sonnet 5，至少在 Anthropic 迄今为止提供的基准上，总是优于 [Sonnet 4.6](https://thenewstack.io/claude-sonnet-46-launch/)。

不过，基准仅讲述了故事的一部分。模型行为也会影响用户如何看待模型，Anthropic 表示，其测试人员注意到该模型现在经常完成复杂的任务，
例如，“以前的十四行诗会在哪里停下来”。

### Sonnet 5 定价为了使 Sonnet 5 对开发人员更具吸引力（也许可以从运行 Opus 4.8 中释放一些容量），Anthropic 为 API 用户提供了一个介绍性价格，截至 8 月 31 日，每百万输入代币 2 美元，每百万输出代币 10 美元。它将上涨到每百万输入/输出代币 3 美元/15 美元，正如 Anthropic 之前对 Sonnet 模型的收费一样。

当被问及这是否是 Anthropic 第一次提供介绍性定价时，一位发言人告诉 The New Stack：“我们希望我们的客户在迁移窗口期间以尽可能低的成本针对其实际工作负载测试 Sonnet 5。”

目前，Anthropic 还提高了 Chat、Cowork 和 Claude Code 用户的速率限制，正如该公司所说，“以适应更高努力水平的更高代币使用量”。

### 十四行诗5安全

在人工智能安全方面，这显然是 Anthropic 关注的焦点，尤其是在《Fable 5》毫不客气地退出之后，Anthropic 指出，它并没有“刻意地训练 Sonnet 5 进行网络安全任务”，虽然它可以处理一些路由网络任务，但它在这些测试中的表现远远落后于 Opus 4.8，当然还有 Mythos。尽管如此，Anthropic 仍对该模型保留了网络保护措施，但由于风险较低，这些保护措施并不像《Fable 5》等模型那样严格。

例如，该公司明确指出，当试图在 [Firefox 147](https://www.firefox.com/en-US/firefox/147.0/releasenotes/) 中查找漏洞时，“Sonnet 5 从未能够开发出完整的可用漏洞，但它的部分成功率确实比其前身 Sonnet 4.6 略高。”

由此看来，美国政府将《十四行诗 5》停止流通的风险相当低。

信用：人类

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
