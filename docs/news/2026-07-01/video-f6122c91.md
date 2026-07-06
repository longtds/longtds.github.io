<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T20:33:14+08:00
source: SegmentFault 思否
domain: 技术动态
url: https://segmentfault.com/q/1010000047951210
content_mode: full-translated
original_language: non-zh
extraction_status: fallback-summary (HTTPError)
-->

# 关于前端Video拍摄兼容性问题？

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 20:33 CST |
| 领域 | 技术动态 |
| 来源 | SegmentFault 思否 |
| 原文标题 | 关于前端Video拍摄兼容性问题？ |
| 原文 | [打开原文](https://segmentfault.com/q/1010000047951210) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | fallback-summary (HTTPError) |

## 摘要

前端使用video录制视频做人脸校验，关键代码如下： const videoConstraints = { facingMode: 'user', width: {ideal: 720, max: 1280}, height: {ideal: 720, max: 1280}, frameRate: {ideal: 24, min: 15, max: 30}, }; const stream: any = await navigator.mediaDevices.getUserMedia({ audio: false, video: videoConstraints, }); .capture-rect { position: relative; width: 520px; height: 520px; margin: 4vw auto; overflow: hidden; border-radius: 50%; // iOS WKWebView: video 走独立合成层,clip-path / 父级 transform 可能只裁一半 -webkit-mask-image: -webkit-radial-gradient(white, black); mask-image: radial-gradient(white, black); // iOS 17.x: transform 写在 video 上 + 圆形 overflow 会纵向只渲染半屏,镜像放到包裹层 .video-mirror-wrap { width: 100%; height: 100%; transform: scaleX(-1); -webkit-transform: scaleX(-1); video { width: 100%; display: block; height: 100%; object-fit: cover; object-position: center; box-sizing: border-box; -webkit-backface-visibility: hidden; backface-visibility: hidden; } } } 按照现在这种写法有两个兼容性bug： 1、IOS 17系统上预览就显示一半 2、部分安卓手机黑屏 有大佬知道这种情况怎么解决么

## 正文

前端使用video录制视频做人脸校验，关键代码如下： const videoConstraints = { facingMode: 'user', width: {ideal: 720, max: 1280}, height: {ideal: 720, max: 1280}, frameRate: {ideal: 24, min: 15, max: 30}, }; const stream: any = await navigator.mediaDevices.getUserMedia({ audio: false, video: videoConstraints, }); .capture-rect { position: relative; width: 520px; height: 520px; margin: 4vw auto; overflow: hidden; border-radius: 50%; // iOS WKWebView: video 走独立合成层,clip-path / 父级 transform 可能只裁一半 -webkit-mask-image: -webkit-radial-gradient(white, black); mask-image: radial-gradient(white, black); // iOS 17.x: transform 写在 video 上 + 圆形 overflow 会纵向只渲染半屏,镜像放到包裹层 .video-mirror-wrap { width: 100%; height: 100%; transform: scaleX(-1); -webkit-transform: scaleX(-1); video { width: 100%; display: block; height: 100%; object-fit: cover; object-position: center; box-sizing: border-box; -webkit-backface-visibility: hidden; backface-visibility: hidden; } } } 按照现在这种写法有两个兼容性bug： 1、IOS 17系统上预览就显示一半 2、部分安卓手机黑屏 有大佬知道这种情况怎么解决么

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
