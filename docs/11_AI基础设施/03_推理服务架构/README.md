# 推理服务架构

## 总体架构

```
用户请求
    │
    ▼
┌──────────┐
│  网关     │ ← 语义路由/负载均衡/鉴权
│(Kong/Nginx)│
└────┬─────┘
     │
     ▼
┌──────────┐
│  模型调度  │ ← 模型分发/灰度/版本管理
│(KServe)   │
└────┬─────┘
     │
     ▼
┌──────────┐   ┌──────────┐
│ Prefill  │──→│ Decode   │ ← 解耦式推理
│ Pods     │   │ Pods     │
└──────────┘   └──────────┘
     │              │
     └──────┬───────┘
            ▼
       ┌──────────┐
       │ vLLM     │
       │ TGI      │
       └──────────┘
```

## 解耦式推理

2026 年的主流架构，将 prefill 和 decode 分离：

| 阶段 | 资源需求 | 特点 |
|:---|:---|:---|
| Prefill | 计算密集（GPU Compute） | 并行处理输入 Token |
| Decode | 显存密集（Memory Bandwidth） | 逐个生成输出 Token |

## KV Cache 管理

KV Cache 是推理过程中缓存 Key-Value 对的技术，减少重复计算。

```bash
# vLLM 配置
--max-model-len 8192          # 最大上下文长度
--gpu-memory-utilization 0.9  # 显存利用率
--block-size 16               # KV Block 大小
```
