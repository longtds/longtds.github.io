# GPU 故障诊断

## 概述

GPU 是高功耗部件，故障率相对较高。掌握 GPU 故障诊断方法对 AI 基础设施运维至关重要。

## 诊断命令

```bash
# 查看 GPU 状态
nvidia-smi                         # 基础状态
nvidia-smi -q                      # 详细状态
nvidia-smi dmesg                   # GPU 内核日志
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used --format=csv

# 持续监控
watch -n 1 nvidia-smi
nvidia-smi -l 1

# NCCL 测试
nccl-tests                          # 通信带宽测试
```

## 常见故障

| 现象 | 可能原因 | 排查方法 |
|:---|:---|:---|
| GPU 报 ECC Error | 显存位翻转 | `nvidia-smi -q -d ECC` 查看 ECC 计数 |
| GPU 掉卡 | 电源/温度/硬件 | 查看系统日志 dmesg |
| 性能不达标 | 降频/功耗限制 | `nvidia-smi -q -d PERFORMANCE` |
| NCCL 通信超时 | 网络/NVLink 问题 | 运行 nccl-tests 验证带宽 |
| GPU 温度过高 | 散热故障 | 检查风扇/液冷系统 |
```

## 故障处理流程

1. 先用 `nvidia-smi` 确认 GPU 状态
2. 查看 dmesg 内核日志
3. 检查 ECC 错误计数
4. 重置 GPU（`nvidia-smi -r`）
5. 如无效，尝试重启服务器
6. 故障硬件需替换
