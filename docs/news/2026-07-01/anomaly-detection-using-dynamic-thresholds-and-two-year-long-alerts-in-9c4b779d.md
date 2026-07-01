<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-01T00:00:00+08:00
source: Google Cloud Blog
domain: AI 基础设施
url: https://cloud.google.com/blog/products/management-tools/cloud-monitoring-adds-long-lookback-alert-policies-for-promql/
-->

# Anomaly detection using dynamic thresholds and two-year-long alerts in Cloud Monitoring

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-01 00:00 CST |
| 领域 | AI 基础设施 |
| 来源 | Google Cloud Blog |
| 原文 | [打开原文](https://cloud.google.com/blog/products/management-tools/cloud-monitoring-adds-long-lookback-alert-policies-for-promql/) |

## 摘要

Choosing the threshold of an alert policy can be a headache. You have to analyze historical data, aggregate it into semantically meaningful time series, and choose a threshold that matters. If the workload grows, your previously set static threshold might become too low, and your alert might fire too frequently. New workloads might require setting new thresholds, and setting separate thresholds for separate workloads requires creating separate policies, resulting in the annoyance of managing a fleet of mostly similar policies. Not to mention, some metrics can’t even be alerted on using static thresholds. If your metric varies by time of day, like many e-commerce metrics do, then no single th

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 原文为外部来源，本站仅做技术动态归档与摘要索引，完整信息以原文为准。

[返回新闻列表](../index.md)
