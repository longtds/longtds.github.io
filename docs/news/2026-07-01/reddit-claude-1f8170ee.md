<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T18:37:00+08:00
source: 雷峰网 / AI科技评论
domain: AIOps / 可观测性
url: https://www.leiphone.com/category/ai/rzmbSvqty7wRNC3N.html
content_mode: full-translated
original_language: zh
extraction_status: html-heuristic
-->

# Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 18:37 CST |
| 领域 | AIOps / 可观测性 |
| 来源 | 雷峰网 / AI科技评论 |
| 原文标题 | Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？ |
| 原文 | [打开原文](https://www.leiphone.com/category/ai/rzmbSvqty7wRNC3N.html) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

Claude Code 负责人已回应：只是为了防止模型蒸馏！ 作者丨 樊天骄 编辑丨 郑佳美 昨天，一个 Reddit 大佬逆向了一下 Claude Code，发现为了防止中国用户，Anthropic 居然在最近更新的 Claude Code 2.1.196 版本中放了个 监控程序！ 于是爆料者立刻追溯时间，发现这个程序不是最近才有的，早在 2026 年 4 月 2 日的 2.1.91 版本该程序就已上线，却从未写入官方更新日志。雷峰网 要知道，不久之前 Claude Code 还被曝出在用户的通知邮件内安装追踪器。 用户们本以为这就是 Anthropic 的底线，紧接着 Anthropic 就被曝出安装了回传用户信息的间谍程序，用实际行动告诉你：我不光没有底线，我还没有下限。 让人咂舌的是这个间谍程序的运行机制的确设计的足够精妙。它会通过篡改系统提示词的日期格式、替换细微特殊标点等肉眼完全无法识别的隐写手段对中国的用户进行秘密标记，并且回传用户信息。 这就是说，Claude Code 在神不知鬼不觉的情况下，已经偷偷回传了所有中国用户信息近 3 个月。也难怪今年会爆发一轮接一轮的 Claude Code 封号热潮：甭管你的 IP 地址在国内还是国外，也甭管调用 API 的方式多么高明，只要是中国人，Anthropic 都能做到精准封杀。 依稀记得前段时间社区里的中国网友们都苦兮兮，技术人员谈论的主题不超过三句话： 你号封了吗?我号封了吗？我号怎么又被封了？ 看完这份逆向实锤，也难怪不少网友感慨：绝了，Anthropic，可真有你的。雷峰网 01 为了防止中国用户使用， Anthropic 有多努力 Anthropic 究竟怎么通过这套间谍程序 （Spyware）, 精准封号中国网用户的？经 Reddit 大神的逆向拆解，这套内置程序设置了两套技术： 一种是基于系统提示词的文本隐写（Steganography）技术，负责对用户进行身份标记与隐秘回传； 另一种是代码压缩与 XOR 加密混淆手段，用于隐藏检测逻辑本身的痕迹。 第一种用于识别 “是否为中国用户”，然后给所有中国用户打上特定标记，把这些用户信息回传；第二种则负责掩盖第一步的操作，防止用户发现。 ▎ 先来说第一种核心标记技术：系统提示词隐写溯源（Steganography） 一旦用户开启代理，程序将执行双重维度的校验： 系统时区校验。即通过读取你个人设备本地的时间，判断用户是否处于“上海——乌鲁木齐”中国属地标准时区； 代理域名核验：解析用户使用的代理网址，确认其是否为中国域名、是否命中预设黑名单域名列表，以及是否关联国内 AI 实验室。 这套程序的作用在于识别用户身份：即用户是否为中国属地，是普通用户还是 AI 机构主体。 那么，在完成用户身份识别后，Anthropic 是如何在用户完全无感知的情况

## 正文

您正在使用IE低版浏览器，为了您的雷峰网账号安全和更好的产品体验，强烈建议使用更快更安全的浏览器

此为临时链接，仅用于文章预览，将在时失效

[](https://www.leiphone.com)  [人工智能](https://www.leiphone.com/category/ai)  [正文](https://www.leiphone.com/category/ai/rzmbSvqty7wRNC3N.html)

[](javascript:;)

发私信给樊天骄

[发送](javascript:;)

[0](https://www.leiphone.com/category/ai/rzmbSvqty7wRNC3N.html#lph-comment-211291)

##  Reddit 上爆出大猛料，

Claude 为何封号中国用户又快又准？

| 本文作者： [樊天骄](https://www.leiphone.com/author/fantianjiao715) | 2026-07-01 18:37 |
|:---|:---|

导语：Claude Code 负责人已回应：只是为了防止模型蒸馏！

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf721661.jpg?imageMogr2/quality/90)

Claude Code 负责人已回应：只是为了防止模型蒸馏！

作者丨樊天骄

编辑丨郑佳美

昨天，一个 Reddit 大佬逆向了一下 Claude Code，发现为了防止中国用户，Anthropic 居然在最近更新的 Claude Code 2.1.196 版本中放了个监控程序！

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf747a2e.png?imageMogr2/quality/90)

于是爆料者立刻追溯时间，发现这个程序不是最近才有的，早在 2026 年 4 月 2 日的 2.1.91 版本该程序就已上线，却从未写入官方更新日志。雷峰网

要知道，不久之前 Claude Code 还被曝出在用户的通知邮件内安装追踪器。

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf79690b.png?imageMogr2/quality/90)

用户们本以为这就是 Anthropic 的底线，紧接着 Anthropic 就被曝出安装了回传用户信息的间谍程序，用实际行动告诉你：我不光没有底线，我还没有下限。

让人咂舌的是这个间谍程序的运行机制的确设计的足够精妙。它会通过篡改系统提示词的日期格式、替换细微特殊标点等肉眼完全无法识别的隐写手段对中国的用户进行秘密标记，并且回传用户信息。

这就是说，Claude Code 在神不知鬼不觉的情况下，已经偷偷回传了所有中国用户信息近 3 个月。也难怪今年会爆发一轮接一轮的 Claude Code 封号热潮：甭管你的 IP 地址在国内还是国外，也甭管调用 API 的方式多么高明，只要是中国人，Anthropic 都能做到精准封杀。

依稀记得前段时间社区里的中国网友们都苦兮兮，技术人员谈论的主题不超过三句话：你号封了吗?我号封了吗？我号怎么又被封了？

看完这份逆向实锤，也难怪不少网友感慨：绝了，Anthropic，可真有你的。雷峰网

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf7d5856.jpg?imageMogr2/quality/90)

01

###
为了防止中国用户使用，

### Anthropic 有多努力

Anthropic 究竟怎么通过这套间谍程序 （Spyware）, 精准封号中国网用户的？经 Reddit 大神的逆向拆解，这套内置程序设置了两套技术：

-

一种是基于系统提示词的文本隐写（Steganography）技术，负责对用户进行身份标记与隐秘回传；

-

另一种是代码压缩与 XOR 加密混淆手段，用于隐藏检测逻辑本身的痕迹。

第一种用于识别 “是否为中国用户”，然后给所有中国用户打上特定标记，把这些用户信息回传；第二种则负责掩盖第一步的操作，防止用户发现。

▎先来说第一种核心标记技术：系统提示词隐写溯源（Steganography）

一旦用户开启代理，程序将执行双重维度的校验：

-

系统时区校验。即通过读取你个人设备本地的时间，判断用户是否处于“上海——乌鲁木齐”中国属地标准时区；

-

代理域名核验：解析用户使用的代理网址，确认其是否为中国域名、是否命中预设黑名单域名列表，以及是否关联国内 AI 实验室。

这套程序的作用在于识别用户身份：即用户是否为中国属地，是普通用户还是 AI 机构主体。

那么，在完成用户身份识别后，Anthropic 是如何在用户完全无感知的情况下，将这些身份信息神不知鬼不觉地回传至后台的？

这就涉及到本次爆料最让人大跌眼镜的操作—— 程序会先通过修改系统提示词的细节特征完成隐形标记，再进行回传。

而怎么才能标记的更隐蔽？Anthropic 想到的方法是——改日期。

如若检测到中国时区，程序会将提示词中默认的横杠式日期格式（2026-06-30）替换为斜杠格式（2026/06/30），完成基础属地标记。

甚至，程序还会根据代理域名的属性，用三种外观高度相似、Unicode 编码完全不同的特殊字符，对用户进行更为精细化的分层标记：

-

如为普通国内代理用户（中国域名但非 AI 实验室主体），则替换为右单引号 ’（Unicode 编码 \u2019）

-

如为中国境外链路的国内 AI 机构（非中国域名但可匹配国内 AI 实验室名单），则替换为修饰字母撇号 ʼ（Unicode 编码 \u02BC）

-

如为中国境内 AI 机构主体（中国域名且匹配国内 AI 实验室名单），则替换为修饰重音符号 ʹ（Unicode 编码 \u02B9）

这样，Anthropic 就完成了从属地识别、身份分层到无感回传的全流程操作 —— 全程没有用户授权提示，字符差异肉眼几乎不可辨。

毕竟，谁会去关注日期显示是 6/30 日还是 6-30 日呢？

用户和模型都感知不到任何异常，官方后端却能根据预设的编码规则精准解码出用户身份，为后续定向封禁提供数据依据。

▎第二步——通过代码混淆与版本特征

显然 Anthropic 是知道这样的做法是不被允许的。因此，为了不被用户的逆向排查与安全扫描发现，Anthropic 对整套检测逻辑进行了高强度代码压缩与XOR加密混淆，隐藏在程序二进制文件中。

经常做代码的朋友们应该都知道，为了方便维护，正常开发的代码函数都会起有实际含义的名字（比如检测时区的函数命名为 checkTimeZone ）。

但 Anthropic 对风控代码做了压缩混淆处理，把所有有语义的函数名都替换成了 Crt、e0t 这类毫无含义的短字符。

这就导致普通人哪怕看到源码片段，也根本猜不出这些函数的真实作用。

而在 2.1.196 版本中，该风控逻辑的核心函数包含 Crt()、Rrt(e)、e0t()、Zup()、edp、Vla 等。这类函数都为压缩混淆后的动态命名，会随版本迭代自动变更，具有极强的隐蔽性。

先是用肉眼完全无法察觉的方式标记了用户身份并回传数据，然后给检测代码“加密伪装”，避免其被常规工具扫描识别。

最后再叠加代理触发式的运行机制 —— 程序仅在用户开启网络代理时自动启动检测，直连用户完全不受影响。

这一套 “组合拳” 下来，Anthropic 美美收集了用户信息，而用户压根察觉不到。

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf820a33.jpg?imageMogr2/quality/90)

02

###

### 信任的崩塌只需一瞬间

Claude Code 是什么？

这可是一个运行在你本地系统的 AI 编程工具。它拥有你电脑文件系统的所有读写权限，能直接读取、增删、修改本地所有项目代码与文档，甚至能调用系统终端执行指令、操控本地开发环境。

相当于你花钱买家具，商家上门安装时偷偷在屋里装了摄像头，还顺手在门口贴了只有同伙能看懂的标记，暗示这家人可以去大偷特偷。

最可笑的是，就连 Anthropic 自己的安全白皮书里，都在反复强调 Claude Code 的 “透明”和“可信”。

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf85897e.png?imageMogr2/quality/90)

目前这篇帖子的浏览量也已达到了100 W 级别，评论区也很嘈杂，概括起来就两种现象：中国网友很愤慨，外国网友很恐慌。

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf87f288.png?imageMogr2/quality/90)

而 Claude Code负责人 Thariq 也对此信息做出回应：

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf89d9b7.png?imageMogr2/quality/90)

Thariq 表示，这套检测机制是团队于当年 3 月启动的一项实验，初衷只是为了防范未经授权的账号转售滥用与模型蒸馏行为。

团队后续已落地更强力的风控缓解方案，该检测功能本就计划下线，目前相关移除代码已完成合并，预计会在次日发布的版本中完全回滚该检测逻辑。

可问题是，真的会回滚吗？没有人知道。

毕竟 “信任的成本只会越来越高。” 雷峰网(公众号：雷峰网)

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf8c30ae.png?imageMogr2/quality/90)

参考链接：

https://www.reddit.com/r/ClaudeAI/comments/1ujila1/anthropic_embedded_spyware_in_claude_code_and/

https://x.com/trq212/status/2072079729331777817

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf8eabd6.jpg?imageMogr2/quality/90)

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf917e40.jpg?imageMogr2/quality/90)

上车，带你看遍全球 AI 顶会精华

可独家畅览：

专家演讲PPT

大会报告全文

热门论文解读

学术新星访谈

![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/images/20260701/6a44eaf9440ad.jpg?imageMogr2/quality/90)

扫描上方二维码

或点击「阅读原文」关注专区。

雷峰网原创文章，未经授权禁止转载。详情见[转载须知](https://r.xiumi.us/board/v5/3qhbI/392977584)。

[![Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://static.leiphone.com/uploads/new/category/pic/202103/604edce946126.jpg?imageMogr2/thumbnail/!740x140r/gravity/Center/crop/740x140/quality/90)](https://vip.yanxishe.com/?from=leiphonearticle)

[0人收藏](javascript:;)

[](https://www.leiphone.com/author/fantianjiao715)

[樊天骄](https://www.leiphone.com/author/fantianjiao715)

编辑

| [](mailto:fantianjiao@leiphone.com) |
|:---|

[发私信](javascript:;)

当月热门文章

-  [Karpathy 65 行文档狂砍 17.6 万星，阻止 Coding 犯大错只需这四点](https://www.leiphone.com/category/ai/F04bdF68h7QJTFUl.html)
-  [单用户提速 60-85% ！DeepSeek 联手北大开源 DSpark ，突破推理加速工程问题](https://www.leiphone.com/category/ai/3QqhbnrdnlxcrD1R.html)
-  [马斯克悄悄改了战场：Grok Build 0.2.60 剑指 Agent Runtime](https://www.leiphone.com/category/ai/9NVnWMuqKHrViS35.html)
-  [Reddit 上爆出大猛料，Claude 为何封号中国用户又快又准？](https://www.leiphone.com/category/ai/rzmbSvqty7wRNC3N.html)

最新文章

-  [中国信通院牵头，首个智算运维智能体评测基准正式落地，覆盖 5 款主流国产芯片](https://www.leiphone.com/category/ai/i94gGHABXfqBbfYn.html)
-  [单用户提速 60-85% ！DeepSeek 联手北大开源 DSpark ，突破推理加速工程问题](https://www.leiphone.com/category/ai/3QqhbnrdnlxcrD1R.html)
-  [Karpathy 65 行文档狂砍 17.6 万星，阻止 Coding 犯大错只需这四点](https://www.leiphone.com/category/ai/F04bdF68h7QJTFUl.html)
-  [市场份额从41%掉到26%，Cursor凭什么还值600亿？](https://www.leiphone.com/category/ai/IuG8AWhW3lhmQFPR.html)
-  [一句「Make it better」，Fable 5 直接把贪吃蛇炼成「逆反人格」](https://www.leiphone.com/category/ai/rM0uSgeIJJ5477ZC.html)
-  [美媒：快手可灵拟引入泛大西洋投资，投后估值1300亿](https://www.leiphone.com/category/ai/awNbSNygrWrx5PLw.html)

热门搜索

[Uber](https://www.leiphone.com/tag/Uber) [收购](https://www.leiphone.com/tag/收购) [淘宝](https://www.leiphone.com/tag/淘宝) [Siri](https://www.leiphone.com/tag/Siri) [可穿戴](https://www.leiphone.com/tag/可穿戴) [Windows](https://www.leiphone.com/tag/Windows) [黑科技](https://www.leiphone.com/tag/黑科技) [抖音](https://www.leiphone.com/tag/抖音) [paypal](https://www.leiphone.com/tag/paypal) [反垄断](https://www.leiphone.com/tag/反垄断) [deepseek](https://www.leiphone.com/tag/deepseek)

[](javascript:;)

为了您的账户安全，请[验证邮箱](javascript:;)

您的邮箱还未验证,完成可获20积分哟！

[重发邮箱](javascript:;)[修改邮箱](javascript:;)

请验证您的邮箱

[立即验证](javascript:;)

完善账号信息

您的账号已经绑定，现在您可以[设置密码](javascript:;)以方便用邮箱登录

[立即设置](javascript:;) [以后再说](javascript:;)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
