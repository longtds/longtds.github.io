# 模型部署

## KServe 推理编排

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: llama-8b
spec:
  predictor:
    model:
      modelFormat:
        name: pytorch
      storageUri: s3://models/llama-8b
    resources:
      requests:
        nvidia.com/gpu: "2"
      limits:
        nvidia.com/gpu: "2"
```

## 模型量化

| 精度 | 位宽 | 显存节省 | 精度损失 | 场景 |
|:---:|:---:|:---:|:---:|:---|
| FP16 | 16bit | 1x | 无 | 基准 |
| INT8 | 8bit | 2x | 极小 | 通用 |
| INT4 | 4bit | 4x | 轻微 | 低资源 |
| FP8 | 8bit | 2x | 极小 | H100 原生支持 |

```bash
# AWQ 量化
python -m awq.quantize --model-path meta-llama/Llama-3.1-8B
```

## 模型加载优化

- **FastAPI + 异步**：高并发场景
- **模型热加载**：多模型共享 GPU
- **LoRA 适配器**：快速切换领域模型
