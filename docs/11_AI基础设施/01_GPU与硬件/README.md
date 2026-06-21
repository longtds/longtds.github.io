# GPU 与硬件

## GPU 架构演进

| 架构 | 发布时间 | 代表卡 | 关键特性 |
|:---|:---:|:---|:---|
| Ampere | 2020 | A100 | MIG、TF32、80GB HBM2e |
| Hopper | 2022 | H100 | Transformer Engine、FP8、NVLink 4.0 |
| Blackwell | 2024 | B200 | 第二代 Transformer Engine、FP4 |

## GPU 选型：推理 vs 训练

| 场景 | 推荐卡 | 原因 |
|:---|:---|:---|
| 在线推理（低延迟） | L40S / A100-80G | 大显存、高吞吐 |
| 离线批量推理 | A100 / H100 | 高吞吐量 |
| 大模型训练 | H100 / B200 | NVLink、高带宽 |
| 边缘推理 | T4 / L4 | 功耗低、体积小 |

## GPU 驱动与 CUDA

```bash
# 查看 GPU 信息
nvidia-smi
nvidia-smi topo -m       # GPU 拓扑
nvidia-smi -q -d MEMORY  # 显存信息

# CUDA 版本管理
nvcc --version
ls /usr/local/cuda/

# NCCL 检查
nccl-tests
```
