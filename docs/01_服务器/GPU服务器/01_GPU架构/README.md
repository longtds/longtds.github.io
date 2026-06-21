# GPU 架构

## 概述

GPU（Graphics Processing Unit）最初用于图形渲染，现已成为 AI 计算的核心硬件。NVIDIA 是目前 AI 领域 GPU 的主导供应商。

## GPU 架构演进

| 架构 | 发布时间 | 代表产品 | 关键特性 |
|:---|:---:|:---|:---|
| Volta | 2017 | V100 | Tensor Core 初代 |
| Turing | 2018 | T4 | RT Core + INT8 |
| Ampere | 2020 | A100 | MIG + TF32 |
| Hopper | 2022 | H100 | Transformer Engine + FP8 |
| Blackwell | 2024 | B200 | 第二代 Transformer Engine |

## GPU 组件

- **CUDA Core**：通用计算单元
- **Tensor Core**：矩阵运算加速单元，AI 计算核心
- **RT Core**：光线追踪单元
- **HBM**：高带宽显存
- **NVLink**：GPU 间高速互联
