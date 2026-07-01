<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-30T22:00:00+08:00
source: The New Stack
domain: 技术动态
url: https://thenewstack.io/aikido-acquires-root-security/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# Aikido 获取 Root 以向后移植开源修复程序，而无需强制升级

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-30 22:00 CST |
| 领域 | 技术动态 |
| 来源 | The New Stack |
| 原文标题 | Aikido acquires Root to backport open source fixes without forcing upgrades |
| 原文 | [打开原文](https://thenewstack.io/aikido-acquires-root-security/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

以开发人员为中心的网络安全平台 Aikido Security 宣布已收购 Root，这是一家直接修补已知漏洞的公司。 Aikido 收购 Root 以向后移植开源修复程序而不强制升级，这一消息首先出现在 The New Stack 上。

## 正文

以开发人员为中心的网络安全平台 [Aikido Security](https://www.aikido.dev/) 宣布已收购 [Root](https://www.root.io/)，该公司将已知漏洞直接修补到团队已经运行的开源软件包版本中，而不是强迫他们升级到较新的版本。

这笔价值 7000 万美元的交易将 Root 的补丁技术整合到了一款名为 Aikido Libraries 的新产品中。它还承诺在[公司支持](https://www.npmjs.com/package/@aikidosec/safe-chain)的每个生态系统（例如[npm](https://www.aikido.dev/protect/safe-chain)、PyPI和Maven）免费向开源社区反向移植关键的、被积极利用的漏洞修复程序。

Aikido 成立于 2022 年，提供涵盖代码扫描、云安全、供应链恶意软件检测和[人工智能驱动的渗透测试](https://thenewstack.io/aikido-self-securing-software/) 的单一平台。这家比利时公司早在 1 月份就跻身独角兽行列，筹集了 [6000 万美元，估值 10 亿美元](https://www.aikido.dev/blog/aikido-funding-series-b)，现在它正在寻求 [仅仅一年多](https://www.aikido.dev/blog/allseek-and-haicker-are-joining-aikido) 内的第四次 [收购](https://www.aikido.dev/blog/trag-is-now-part-of-aikido-secure-code-at-ai-speed)，以缩小发现和修复漏洞之间的差距。

Root 最初是 Slim.AI，成立于 2021 年，基于开源 DockerSlim 项目构建。该公司[于 2022 年筹集了 3100 万美元的 A 轮融资](https://www.insightpartners.com/ideas/slim-ai-closes-31-million-series-a-to-automate-best-practices-in-software-supply-chain-security-for-cloud-native-applications/)，之后更名为 Root，并从容器优化转向自动漏洞修复。

### 修复紧急缺陷

Aikido 的免费向后移植承诺特别适用于 [CISA](https://www.cisa.gov/) 已知被利用的漏洞 ([KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)) 目录中的漏洞 - 已确认在野外被利用的相对较短的缺陷列表。这只是所有已披露漏洞的一小部分，但却是最有可能造成真正损害的漏洞。一旦收购成本需要证明合理性，这种承诺就可能消失。 Aikido Security 联合创始人兼首席增长官 [Madeline Lawrence](https://www.linkedin.com/in/madelinelawren/) 告诉 The New Stack，这种情况不会发生在这里，因为决定名单内容的是 CISA，而不是 Aikido。免费修复与 Aikido 现有的付费产品并驾齐驱，该公司押注于一种单独的增长趋势：公司普遍面临着越来越大的合规压力，需要清除常见漏洞和暴露 (CVE)，无论任何特定缺陷是否实际上已被武器化。

劳伦斯表示：“这与我们的付费能力不同，我们的付费能力涵盖了监管机构现在要求公司修复的 CVE 长尾，而不仅仅是那些被积极利用的 CVE，而且那里的需求正在爆炸式增长。” “两者都来自同一家工厂。免费维修没有单独的预算线可以削减，因为生产它们的工作与我们的付费客户所依赖的工作相同。”

>

“该行业仍然陷入分类困境，列出了大量 CVE，并争论首先修复哪些问题。”

Root 首席执行官 [Ian Riopel](https://www.linkedin.com/in/ianriopel/) 提出了业界一直在避免的选择：要么将修复锁定在供应商自己的生态系统后面，要么将它们放回需要它们的项目手中。

Riopel 在一份声明中表示：“该行业仍然陷入分类困境，列出了一份巨大的 CVE 清单，并争论首先修复哪些。或者更糟糕的是，告诉团队扔掉他们的图像并从别人的图像开始。” “我们构建 Root 是为了跳过争论，直接解决问题。这是围墙花园和真正支持开源之间的选择。我们选择了开源。”

>

“这是围墙花园和真正支持开源之间的选择。我们选择了开源。”

### 安全争夺此次收购正值人工智能和网络安全更广泛的动荡时期。周五，[Linux 基金会推出了 Akrites](https://thenewstack.io/akrites-open-source-vulnerability-coordination/)，这是一个由 Anthropic、Google、Microsoft 和大约 20 个组织支持的协调漏洞披露机构，其成立主要是为了应对人工智能工具现在能够快速发现开源代码中的缺陷。反过来，Anthropic 经历了[紧张的几周](https://thenewstack.io/anthropic-fable-mess-explained/)：美国政府在 6 月[暂停访问](https://thenewstack.io/us-gov-orders-anthropic-to-pull-fable-5-and-mythos-5-three-days-after-launch/)其[Fable 5 和 Mythos 5 模型](https://thenewstack.io/anthropic-claude-mythos-fable-5/)，因为研究人员表示他们已经找到了使用它们来协助网络攻击的方法，然后在月底恢复了对关键基础设施组织的访问。

劳伦斯说，时机纯属巧合。她说，Root 交易已经酝酿了很长时间，建立在两家公司[于 2025 年中期建立的](https://www.aikido.dev/blog/aikido-x-root-io-harden-your-containers-without-the-headaches) 现有合作伙伴关系的基础上，将 Root 的强化容器镜像引入 Aikido 现有的 Autofix 产品中。

尽管如此，劳伦斯并没有否认人工智能给战斗双方带来的更广泛的压力。

劳伦斯说：“这个行业非常擅长发现漏洞，并坚持修复它们，而人工智能是第一个让修复工作以同样的速度真正实现的东西。” “先进的模型还使得发现和利用开源中的弱点变得更加容易和便宜，这也是当前紧迫性的一部分。读取代码来修复缺陷的能力也可以读取代码来利用缺陷，这正是每个补丁在发布之前都经过人工验证的原因。”

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
