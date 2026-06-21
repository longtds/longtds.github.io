# AI 推理篇故障排查

## GPU 显存泄漏

```bash
# 1. 查看显存
nvidia-smi
watch -n 1 nvidia-smi

# 2. 查看进程显存占用
fuser -v /dev/nvidia*
nvidia-smi --query-compute-apps=pid,used_memory --format=csv

# 3. 重置 GPU
nvidia-smi -r

# 4. 检查 ECC 错误
nvidia-smi -q -d ECC
```

## 推理延迟抖动

```bash
# 1. 检查 GPU 利用率
nvidia-smi -l 1

# 2. 检查网络延迟（多卡场景）
# NCCL 测试
nccl-tests

# 3. 检查模型排队
# vLLM metrics
curl http://localhost:8000/metrics | grep vllm

# 4. KV Cache 压力
# 查看 batch size
# vLLM 日志中 "Avg batch size"
```

## 模型 OOM

```bash
# 解决方案
1. 降低 max-model-len（减少上下文长度）
2. 降低 gpu-memory-utilization（如 0.85）
3. 使用量化（AWQ/GPTQ）
4. 增加 tensor-parallel-size（多 GPU 分片）
```
