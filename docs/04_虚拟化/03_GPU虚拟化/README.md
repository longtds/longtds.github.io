# GPU 虚拟化

## GPU 直通（Passthrough）

将整张 GPU 直通给一台虚拟机，性能损失最小。

```bash
# 检查 GPU 直通支持
lspci -nn | grep -i nvidia
dmesg | grep -i vfio

# 绑定 vfio-pci 驱动
echo "vfio-pci" > /sys/bus/pci/devices/<pci-id>/driver_override
```

## GPU 共享

| 技术 | 厂商 | 颗粒度 | 场景 |
|:---|:---|:---:|:---|
| vGPU | NVIDIA | 1G显存 | 虚拟桌面 |
| MIG | NVIDIA Ampere+ | 1/7 GPU | AI 推理 |
| SR-IOV | Intel/NVIDIA | 可变 | 通用 |
| 时间切片 | NVIDIA | 全部 | 训练 |

## MIG（Multi-Instance GPU）

A100/H100 支持将一个 GPU 切分为最多 7 个独立实例，每个实例有独立的显存和缓存。
