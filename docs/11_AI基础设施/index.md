# 11. AI 基础设施

> AI 基础设施 = GPU/NPU + 训推平台 + 模型生命周期。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦 H100/Ascend 硬件 + PyTorch/Megatron + vLLM/KServe + Volcano/Kueue + AWQ/FP8 量化 + LangChain/LangGraph + LiteLLM 网关 + MLflow + 国产昇腾 12 大主线。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入门 AI 平台 | GPU/NPU 硬件 + CUDA/CANN + PyTorch + Hugging Face + 模型格式(safetensors/GGUF) + 推理(vLLM/Ollama/llama.cpp) + 训练(DDP/FSDP) + K8s GPU 调度 + 向量+RAG + 20 题 |
| [02_进阶](02_进阶/README.md) | 独立维护 AI 平台 | vLLM 生产化(TP/PP/Prefix/FP8) + AWQ/GPTQ/FP8 量化 + KServe/Triton + DDP/FSDP/DeepSpeed/Megatron + Volcano/Kueue + MIG/MPS/HAMi + IB/RoCE+NCCL + JuiceFS + LangChain/LlamaIndex RAG + 国产昇腾 + MLflow/Harbor |
| [03_高级](03_高级/README.md) | AI 平台架构师 | 预训练全栈(数据+Tokenizer+Megatron 3D+Checkpoint) + Post-training(SFT/DPO/GRPO/RLHF) + LoRA/QLoRA + 推理优化(Speculative/Prefix/Chunked/DisAgg/MTP) + 长上下文(YaRN/RingAttention) + MoE + 多模态 + Agent(LangGraph/AutoGen) + LLM 网关(LiteLLM/Higress) + NCCL+IB+SHARP + DLRover 容错 + 蒸馏 + 边缘 + 国密 + 国产化 |
| [04_最佳实践](04_最佳实践/README.md) | 团队负责人 | 集群规模决策 + GPU 资源规划 + 训推平台分层 + 镜像/模型/数据治理 + MLOps GitOps + SLO 监控 + 多租户 + FinOps GPU + 容灾备份 + 升级 SOP + 国产化路径 + 内容审核 + 备案 + Incident SOP + 3 种生产架构 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | B100/B200/GB300 + Ascend 910C/920 + FP8/FP4 + MoE + DisAgg + Agent+MCP + Omni 多模态 + 1M Context + RAG+GraphRAG + 国产开源主导 + Sovereign AI + 模型备案 + 25 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
 └─ 01_基础: PyTorch + HF + vLLM/Ollama + K8s GPU + pgvector RAG + 20 题

进阶（3-12 月）
 └─ 02_进阶: vLLM 生产 + AWQ/FP8 + KServe + DDP/FSDP + Volcano + IB + RAG + 昇腾

高级（1-2 年）
 └─ 03_高级: Megatron 3D + Post-training + Speculative/DisAgg + 长上下文 + MoE + 多模态 + LangGraph + LiteLLM + DLRover + 蒸馏 + 国密

工程化（2-3 年）
 └─ 04_最佳实践: 规模决策 + 平台分层 + MLOps + SLO + FinOps GPU + 国产化 + 备案 + 应急

展望（持续）
 └─ 99_发展与展望: B100+Ascend + FP4 + DisAgg + MoE + GRPO + MCP+Agent + Omni + 1M Context + 国产开源 + Sovereign AI
```

## 核心判断

```
心法:
 1. PyTorch + Hugging Face 是入门基底
 2. vLLM 是当下推理王者; SGLang/TRT-LLM/llm-d 各有所长
 3. AWQ/GPTQ/FP8 量化是工程必修 (省卡 + 增吞吐)
 4. KServe + GitOps 是 K8s 推理标准路径
 5. Megatron + Volcano 是预训练栈
 6. LLaMA-Factory + DPO/GRPO 是微调高效栈
 7. LangGraph + MCP 是 Agent 下一波
 8. LiteLLM/Higress AI 是统一网关 + 治理
 9. 国产昇腾 + MindIE/LMDeploy + MindFormers 是央企必修
 10. 模型备案 + 内容审核 + 国密 是中国硬要求
 11. DisAgg Prefill-Decode + MoE + Speculative 是大规模必修
 12. RAG (Milvus/pgvector + bge + Reranker) + Long Context 双轨

红线:
 还在裸 PyTorch 推理 (无 vLLM)
 FP16 满显存却不量化
 训练无 Checkpoint 频次 / 无 Resume
 Volcano / 调度 / 多租户 缺失
 IB / RoCE 网络未调 NCCL
 模型无版本 / 无模型卡 / 无备案
 推理无 SLO + 无监控告警
 数据无 PII 脱敏 / 无合规检查
 国产 Ascend / MindIE 不学 (政企会被淘汰)
 不接 LLM 网关 (无计费 + 无路由)
 Agent 不学 LangGraph + MCP
```

## 相关章节

- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 GPU Operator + Volcano + Karmada
- 配合 [08_DevOps](../08_DevOps/index.md) 看 GitOps + Argo Workflows + MLOps
- 配合 [09_中间件](../09_中间件/index.md) 看 pgvector + Milvus + Kafka
- 配合 [10_大数据](../10_大数据/index.md) 看 Iceberg/Paimon 训练数据 + Feast 特征
- 配合 [12_AIOps](../12_AIOps/index.md) 看 LLM 用于异常告警 + Agent 运维
- 配合 [13_认证与SSO](../13_认证与SSO/index.md) 看 LLM 网关 OIDC + JWT
- 配合 [14_安全](../14_安全/index.md) 看 国密 + 模型加密 + 内容审核
- 配合 [15_渗透测试](../15_渗透测试/index.md) 看 Prompt 注入 + Red Team
- 配合 [16_故障排查](../16_故障排查/index.md) 看 GPU Xid / NCCL Hang / vLLM OOM
