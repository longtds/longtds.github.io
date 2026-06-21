# 推理框架

## 框架对比

| 框架 | 核心算法 | 性能 | 社区 | 云原生 | 特色 |
|:---|:---|:---:|:---:|:---:|:---|
| vLLM | PagedAttention | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 最成熟，社区最大 |
| TGI | 连续批处理 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | HuggingFace 出品 |
| SGLang | RadixAttention | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | 结构化输出 |
| llm-d | 分布式推理 | ⭐⭐⭐ | ⭐⭐ | CNCF Sandbox | K8s 原生 |

## vLLM 部署

```bash
# Docker 部署
docker run --gpus all -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --tensor-parallel-size 2 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9

# API 调用
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## 选型建议

- **通用场景**：vLLM（最成熟，生态最好）
- **K8s 原生**：llm-d（CNCF Sandbox，分布式原生）
- **结构化输出**：SGLang（函数调用/JSON 模式）
- **快速实验**：TGI（部署最简单）
