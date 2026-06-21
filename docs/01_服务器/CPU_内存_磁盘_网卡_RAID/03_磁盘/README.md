# 磁盘

## 概述

服务器存储设备从传统的 HDD 演进到 NVMe SSD，性能跨越式提升。

## 存储介质对比

| 类型 | 接口 | IOPS | 延迟 | 容量 | 价格 |
|:---|:---|:---:|:---:|:---:|:---:|
| HDD | SATA/SAS | ~200 | ~10ms | 4-20TB | 低 |
| SATA SSD | SATA | ~50K | ~0.1ms | 0.5-4TB | 中 |
| NVMe SSD | PCIe 4.0/5.0 | ~1M | ~0.01ms | 1-30TB | 高 |
| Optane | Intel 傲腾 | ~2M | ~0.005ms | 0.1-1.5TB | 极高 |

## 选型建议

| 场景 | 推荐方案 |
|:---|:---|
| 操作系统盘 | NVMe SSD 或 SATA SSD |
| 数据库存储 | NVMe SSD（高 IOPS） |
| 冷数据/备份 | HDD（大容量低成本） |
| 缓存层 | NVMe SSD / Optane |
| 容器/镜像 | NVMe SSD（频繁读写） |
