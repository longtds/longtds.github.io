# 推理可观测性

## 核心指标

| 指标 | 全称 | 含义 | 正常值 |
|:---|:---|:---|:---:|
| TTFT | Time to First Token | 首 Token 延迟 | < 500ms |
| TPOT | Time per Output Token | 每秒生成速度 | > 30 tokens/s |
| ITL | Inter-Token Latency | Token间延迟 | < 30ms |
| Throughput | 吞吐量 | 每秒请求数 | 取决于模型和 GPU |

## Token 计量与成本

```python
# Token 使用统计
{
    "model": "llama-3.1-8b",
    "input_tokens": 150,
    "output_tokens": 200,
    "total_tokens": 350,
    "cost_per_token": 0.000003,  # $/token
    "request_cost": 0.00105
}
```

## 模型质量监控

- 输出长度分布监控（突增可能指示异常）
- Embedding 相似度漂移（模型退化检测）
- 幻觉率评估（抽样检查）
- 用户反馈收集（赞/踩）
