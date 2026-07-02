<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T06:38:42+08:00
source: IT之家
domain: 技术动态
url: https://www.ithome.com/0/971/393.htm
content_mode: full-translated
original_language: zh
extraction_status: html-heuristic
-->

# 苹果“Hide My Email”被曝安全漏洞：测试中 100% 可溯源真实邮箱

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 06:38 CST |
| 领域 | 技术动态 |
| 来源 | IT之家 |
| 原文标题 | 苹果“Hide My Email”被曝安全漏洞：测试中 100% 可溯源真实邮箱 |
| 原文 | [打开原文](https://www.ithome.com/0/971/393.htm) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

IT之家 7 月 2 日消息，据 404 Media 当地时间 7 月 1 日报道，苹果面向 iCloud+ 订阅用户提供的“Hide My Email”（隐藏我的邮件）功能存在安全漏洞，攻击者可利用该漏洞将匿名生成的转发地址逆向关联至用户的真实 Apple ID 邮箱。 该功能允许付费用户生成以 @ icloud.com 或 @ privaterelay.appleid.com 结尾的随机邮箱地址，发送至这些地址的邮件会自动转发至用户的真实私人邮箱，旨在帮助用户避免数据追踪和垃圾邮件。然而，数据清除服务公司 EasyOptOuts 联合创始人 Tyler Murphy 发现，该机制存在严重缺陷。 为验证漏洞严重性，404 Media 生成了一个全新的随机隐藏地址并交由 Murphy 测试。Murphy 在大约五分钟内成功提取出了该地址对应的真实 Apple ID 邮箱。 Murphy 表示，尽管测试范围有限，但截至目前该漏洞在其测试的所有隐藏邮箱上均成功复现，成功率达 100%。IT之家提醒，由于漏洞具体利用方法尚未公开，目前无法确认是否有其他组织或个人已利用该漏洞获取用户信息。 更令人担忧的是漏洞的修复时间线。EasyOptOuts 最早于 2025 年 6 月将该漏洞的复现步骤正式告知 Apple 安全团队。2026 年 3 月，Apple 支持人员声称已通过后台系统修改解决了该问题，但独立验证显示漏洞依然存在。同年 5 月，Apple 工程团队要求研究人员在继续调查期间保持公开沉默，并承诺“未来几周内”发布安全补丁。因不满长期拖延，且认为用户有权知晓其数据处于暴露风险中，研究团队最终选择公开披露。 Murphy 警告称，由于公开的人员搜索目录可轻易将邮箱凭证与家庭住址、电话号码等个人信息关联，依赖该匿名工具进行高风险活动（如记者、活动人士等）的用户正面临直接的身份暴露风险。 这并非 Apple 首次因隐私宣传与技术现实不符而受到质疑。近年来，该公司曾因诊断分析跟踪功能在用户关闭后仍在运行而面临法律压力；此外，有分析指出 Apple 用于隐藏设备在公共网络上物理足迹的本地 Wi-Fi MAC 地址随机化工具同样未能生效，仍会泄露真实标识符。 相关阅读： 《 苹果统一隐私邮件域名，Sign in with Apple 及 iCloud+ Hide My Email 同步切换 》

## 正文

[](https://www.ithome.com) [](https://img.ithome.com/app/songs/index.html)

[首页](https://www.ithome.com)

[IT圈](https://quan.ithome.com)

[最会买](https://www.zuihuimai.com)

[设置](https://www.ithome.com/0/971/393.htm###)

-  日夜间

随系统

浅色

深色

-  主题色

黑色

[投稿](https://dyn.ithome.com/tougao/)

[订阅](https://www.ithome.com/0/971/393.htm###)

- [RSS订阅](https://www.ithome.com/rss/)
- [收藏IT之家](https://www.ithome.com/0/971/393.htm)

[软媒应用](https://www.ruanmei.com)

- [App客户端](https://m.ruanmei.com/)
- [要知App](https://yaozhi.ruanmei.com/)
- [软媒魔方](https://mofang.ruanmei.com/)

[业界](https://it.ithome.com) [手机](https://mobile.ithome.com/) [电脑](https://www.ithome.com/pc/) [测评](https://www.ithome.com/labs/) [视频](https://www.ithome.com/video/) [AI](https://next.ithome.com/) [苹果](https://www.ithome.com/apple/) [iPhone](https://iphone.ithome.com/) [鸿蒙](https://hmos.ithome.com/) [软件](https://soft.ithome.com/)

[智车](https://auto.ithome.com) [数码](https://digi.ithome.com/) [学院](https://www.ithome.com/college/) [游戏](https://game.ithome.com/) [直播](https://www.ithome.com/live/) [5G](https://www.ithome.com/5g/) [微软](https://www.ithome.com/microsoft/) [Win10](https://win10.ithome.com/) [Win11](https://win11.ithome.com/) [专题](https://www.ithome.com/zt/)

搜索

[首页](https://www.ithome.com) > [IT资讯](https://it.ithome.com/)>[苹果](https://it.ithome.com/apple)

## 苹果“Hide My Email”被曝安全漏洞：测试中 100% 可溯源真实邮箱

2026/7/2 6:38:42 来源：[IT之家](https://www.ithome.com/0/971/393.htm) 作者：问舟 责编：问舟

[评论：](https://www.ithome.com/0/971/393.htm#post_comm)

[IT之家](https://www.ithome.com/) 7 月 2 日消息，据 404 Media 当地时间 7 月 1 日报道，苹果面向 iCloud+ 订阅用户提供的“Hide My Email”（隐藏我的邮件）功能存在安全漏洞，攻击者可利用该漏洞将匿名生成的转发地址逆向关联至用户的真实 Apple ID 邮箱。

该功能允许付费用户生成以 @icloud.com 或 @privaterelay.appleid.com 结尾的随机邮箱地址，发送至这些地址的邮件会自动转发至用户的真实私人邮箱，旨在帮助用户避免数据追踪和垃圾邮件。然而，数据清除服务公司 EasyOptOuts 联合创始人 Tyler Murphy 发现，该机制存在严重缺陷。

为验证漏洞严重性，404 Media 生成了一个全新的随机隐藏地址并交由 Murphy 测试。Murphy 在大约五分钟内成功提取出了该地址对应的真实 Apple ID 邮箱。

Murphy 表示，尽管测试范围有限，但截至目前该漏洞在其测试的所有隐藏邮箱上均成功复现，成功率达 100%。IT之家提醒，由于漏洞具体利用方法尚未公开，目前无法确认是否有其他组织或个人已利用该漏洞获取用户信息。

更令人担忧的是漏洞的修复时间线。EasyOptOuts 最早于 2025 年 6 月将该漏洞的复现步骤正式告知 Apple 安全团队。2026 年 3 月，Apple 支持人员声称已通过后台系统修改解决了该问题，但独立验证显示漏洞依然存在。同年 5 月，Apple 工程团队要求研究人员在继续调查期间保持公开沉默，并承诺“未来几周内”发布安全补丁。因不满长期拖延，且认为用户有权知晓其数据处于暴露风险中，研究团队最终选择公开披露。

Murphy 警告称，由于公开的人员搜索目录可轻易将邮箱凭证与家庭住址、电话号码等个人信息关联，依赖该匿名工具进行高风险活动（如记者、活动人士等）的用户正面临直接的身份暴露风险。

这并非 Apple 首次因隐私宣传与技术现实不符而受到质疑。近年来，该公司曾因诊断分析跟踪功能在用户关闭后仍在运行而面临法律压力；此外，有分析指出 Apple 用于隐藏设备在公共网络上物理足迹的本地 Wi-Fi MAC 地址随机化工具同样未能生效，仍会泄露真实标识符。

相关阅读：

-

《[苹果统一隐私邮件域名，Sign in with Apple 及 iCloud+ Hide My Email 同步切换](https://www.ithome.com/0/964/647.htm)》

广告声明：文内含有的对外跳转链接（包括不限于超链接、二维码、口令等形式），用于传递更多信息，节省甄选时间，结果仅供参考，IT之家所有文章均包含本声明。

投诉水文 我要纠错

[下载IT之家APP，签到赚金币兑豪礼](https://m.ithome.com/ithome/download/?popqr)

- [CVSS 8.8：Linux 漏洞 DirtyClone 披露，可提权至 root 最高权限](https://www.ithome.com/0/969/340.htm)
- [苹果为 Beats Studio Buds 耳机推送 1B211 固件更新，修复高危窃听漏洞](https://www.ithome.com/0/965/161.htm)
- [创新 Sound Blaster Katana V2X 游戏回音壁曝安全漏洞，15 米内可被劫持](https://www.ithome.com/0/961/034.htm)
- [黑客诱骗 Meta AI 客服，盗取多名 Instagram 用户账号](https://www.ithome.com/0/958/462.htm)
- [开源监控平台 Grafana 曝提示词漏洞，黑客可诱导 AI 助手泄露企业敏感数据](https://www.ithome.com/0/938/736.htm)
- [苹果督促用户更新 iPhone 至 iOS 26.2，以修复遭黑客利用的 WebKit 安全漏洞](https://www.ithome.com/0/914/309.htm)

软媒旗下网站： [IT之家](https://www.ithome.com/) [最会买 - 返利返现优惠券](https://www.zuihuimai.com/) [iPhone之家](https://iphone.ithome.com/) [Win7之家](https://www.win7china.com/) [Win10之家](https://win10.ithome.com/) [Win11之家](https://win11.ithome.com/)

软媒旗下软件： [软媒手机APP应用](https://m.ruanmei.com/) [魔方](https://mofang.ruanmei.com/) [最会买](https://www.zuihuimai.com) [要知](https://yaozhi.ruanmei.com/)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
