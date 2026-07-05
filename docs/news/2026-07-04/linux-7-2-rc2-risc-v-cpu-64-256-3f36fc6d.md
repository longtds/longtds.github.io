<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-04T18:36:39+08:00
source: IT之家
domain: 数据中心 / 硬件
url: https://www.ithome.com/0/972/623.htm
content_mode: full-translated
original_language: zh
extraction_status: html-heuristic
-->

# Linux 7.2-rc2 合入 RISC-V 关键调整：默认 CPU 核心数从 64 提升至 256

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-04 18:36 CST |
| 领域 | 数据中心 / 硬件 |
| 来源 | IT之家 |
| 原文标题 | Linux 7.2-rc2 合入 RISC-V 关键调整：默认 CPU 核心数从 64 提升至 256 |
| 原文 | [打开原文](https://www.ithome.com/0/972/623.htm) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

IT之家 7 月 4 日消息，据 Phoronix，Linux 内核主线今日迎来了一项针对 RISC-V 架构的重要调整。 在即将发布的 Linux 7.2-rc2 版本中，RISC-V 64 位架构默认支持的 CPU 核心数上限从原有的 64 核提升至 256 核。这一变更已于本周作为 RISC-V 修复补丁的一部分合入 Linux Git 仓库。 此次调整源于 RISC-V 服务器硬件的实际需求。提出这一请求的是 RISC-V 芯片设计公司进迭时空（SpacemiT）。相关提交说明中明确提到，进迭时空已生产出 80 核的 RVA23 标准 RISC-V 服务器；而更早之前，基于算能（Sophgo）SG2042 芯片的双路服务器“Pisces”已拥有 128 核的配置。在此背景下，原有的 64 核默认上限显然已无法满足硬件发展需求。 这一内核配置参数“NR_CPUS”直接影响内核中各类静态内存分配的大小 —— 数值越高，内核内存占用也会相应增加。开发者在提交中将新阈值设定为 256，理由是“选取一个至少两倍于已知最大核心数的 2 的幂次数值”，并认为这能在“不浪费过多内存”与“无需频繁调整”之间取得合理平衡。 IT之家注意到，Ubuntu 发行版早已为 RISC-V 64 位架构配置了 512 的 NR_CPUS 值，而中国科学院计算技术研究所（ISCAS）内部测试 256 核配置时，也观察到“性能影响可忽略不计，未出现任何不良影响”。 与其他主流架构相比，RISC-V 此次调整后的默认值仍显得较为保守 ——Linux x86_64 架构下，多数发行版内核在启用 MAXSMP 后，NR_CPUS 可达 8192 以应对 AMD 和英特尔的高核心数服务器处理器；ARM64（AArch64）架构的默认值为 512，龙芯 LoongArch 架构更是达到了 2048。值得一提的是，这一变更在合并窗口期之后仍被 Linus Torvalds 本人接纳，反映出其风险较低、不会引入明显回退问题的判断。 随着 RISC-V 生态从低功耗嵌入式场景向高性能服务器领域持续扩展，内核基础配置的调整已成为必然。此次 NR_CPUS 的提升，标志着 Linux 内核正在为 RISC-V 架构迈向更高核心数的服务器市场做好底层准备。

## 正文

[](https://www.ithome.com) [](https://img.ithome.com/app/songs/index.html)

[首页](https://www.ithome.com)

[IT圈](https://quan.ithome.com)

[最会买](https://www.zuihuimai.com)

[设置](https://www.ithome.com/0/972/623.htm###)

-  日夜间

随系统

浅色

深色

-  主题色

黑色

[投稿](https://dyn.ithome.com/tougao/)

[订阅](https://www.ithome.com/0/972/623.htm###)

- [RSS订阅](https://www.ithome.com/rss/)
- [收藏IT之家](https://www.ithome.com/0/972/623.htm)

[软媒应用](https://www.ruanmei.com)

- [App客户端](https://m.ruanmei.com/)
- [要知App](https://yaozhi.ruanmei.com/)
- [软媒魔方](https://mofang.ruanmei.com/)

[业界](https://it.ithome.com) [手机](https://mobile.ithome.com/) [电脑](https://www.ithome.com/pc/) [测评](https://www.ithome.com/labs/) [视频](https://www.ithome.com/video/) [AI](https://next.ithome.com/) [苹果](https://www.ithome.com/apple/) [iPhone](https://iphone.ithome.com/) [鸿蒙](https://hmos.ithome.com/) [软件](https://soft.ithome.com/)

[智车](https://auto.ithome.com) [数码](https://digi.ithome.com/) [学院](https://www.ithome.com/college/) [游戏](https://game.ithome.com/) [直播](https://www.ithome.com/live/) [5G](https://www.ithome.com/5g/) [微软](https://www.ithome.com/microsoft/) [Win10](https://win10.ithome.com/) [Win11](https://win11.ithome.com/) [专题](https://www.ithome.com/zt/)

搜索

[首页](https://www.ithome.com) > [软件之家](https://soft.ithome.com/)>[Linux](https://soft.ithome.com/linux)

## Linux 7.2-rc2 合入 RISC-V 关键调整：默认 CPU 核心数从 64 提升至 256

2026/7/4 18:36:39 来源：[IT之家](https://www.ithome.com/0/972/623.htm) 作者：问舟 责编：问舟

[评论：](https://www.ithome.com/0/972/623.htm#post_comm)

[IT之家](https://www.ithome.com/) 7 月 4 日消息，据 Phoronix，Linux 内核主线今日迎来了一项针对 RISC-V 架构的重要调整。

在即将发布的 Linux 7.2-rc2 版本中，RISC-V 64 位架构默认支持的 CPU 核心数上限从原有的 64 核提升至 256 核。这一变更已于本周作为 RISC-V 修复补丁的一部分合入 Linux Git 仓库。

此次调整源于 RISC-V 服务器硬件的实际需求。提出这一请求的是 RISC-V 芯片设计公司进迭时空（SpacemiT）。相关提交说明中明确提到，进迭时空已生产出 80 核的 RVA23 标准 RISC-V 服务器；而更早之前，基于算能（Sophgo）SG2042 芯片的双路服务器“Pisces”已拥有 128 核的配置。在此背景下，原有的 64 核默认上限显然已无法满足硬件发展需求。

这一内核配置参数“NR_CPUS”直接影响内核中各类静态内存分配的大小 —— 数值越高，内核内存占用也会相应增加。开发者在提交中将新阈值设定为 256，理由是“选取一个至少两倍于已知最大核心数的 2 的幂次数值”，并认为这能在“不浪费过多内存”与“无需频繁调整”之间取得合理平衡。

IT之家注意到，Ubuntu 发行版早已为 RISC-V 64 位架构配置了 512 的 NR_CPUS 值，而中国科学院计算技术研究所（ISCAS）内部测试 256 核配置时，也观察到“性能影响可忽略不计，未出现任何不良影响”。

与其他主流架构相比，RISC-V 此次调整后的默认值仍显得较为保守 ——Linux x86_64 架构下，多数发行版内核在启用 MAXSMP 后，NR_CPUS 可达 8192 以应对 AMD 和英特尔的高核心数服务器处理器；ARM64（AArch64）架构的默认值为 512，龙芯 LoongArch 架构更是达到了 2048。值得一提的是，这一变更在合并窗口期之后仍被 Linus Torvalds 本人接纳，反映出其风险较低、不会引入明显回退问题的判断。

随着 RISC-V 生态从低功耗嵌入式场景向高性能服务器领域持续扩展，内核基础配置的调整已成为必然。此次 NR_CPUS 的提升，标志着 Linux 内核正在为 RISC-V 架构迈向更高核心数的服务器市场做好底层准备。

广告声明：文内含有的对外跳转链接（包括不限于超链接、二维码、口令等形式），用于传递更多信息，节省甄选时间，结果仅供参考，IT之家所有文章均包含本声明。

投诉水文 我要纠错

[下载IT之家APP，签到赚金币兑豪礼](https://m.ithome.com/ithome/download/?popqr)

- [曝谷歌 Pixel 系列手机将迎重大底层升级，Linux 内核有望更新](https://www.ithome.com/0/972/573.htm)
- [2026 上半年 CVE 漏洞榜单：Linux 以 2308 个数量居首](https://www.ithome.com/0/972/498.htm)
- [System76 推出 Linux 轻薄本 Lemur Pro：搭载 "Panther Lake"，可选 14" / 16"](https://www.ithome.com/0/971/432.htm)
- [Tenstorrent 发布 RISC-V CPU 设计 Ascalon S，单位面积性能达旗舰 IP 的 140%](https://www.ithome.com/0/970/866.htm)
- [Linux 7.2-rc1 内核发布：代码突破 4300 万行，新增缓存感知调度等功能](https://www.ithome.com/0/969/896.htm)
- [希奥端计算将基于赛昉 Dubhe-100 CPU IP 打造 RISC-V 服务器 CPU](https://www.ithome.com/0/969/849.htm)

软媒旗下网站： [IT之家](https://www.ithome.com/) [最会买 - 返利返现优惠券](https://www.zuihuimai.com/) [iPhone之家](https://iphone.ithome.com/) [Win7之家](https://www.win7china.com/) [Win10之家](https://win10.ithome.com/) [Win11之家](https://win11.ithome.com/)

软媒旗下软件： [软媒手机APP应用](https://m.ruanmei.com/) [魔方](https://mofang.ruanmei.com/) [最会买](https://www.zuihuimai.com) [要知](https://yaozhi.ruanmei.com/)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
