# 二层协议

## Ethernet 帧结构

```
┌────────┬──────┬────────┬──────────┬────────┬────────┐
│ 前导码 │SFD  │ 目标MAC │ 源MAC   │ 类型   │ 数据   │ FCS  │
│ 7B     │1B   │ 6B     │ 6B       │ 2B     │ 46-1500│ 4B   │
└────────┴──────┴────────┴──────────┴────────┴────────┘
```

## VLAN / 802.1Q

| 概念 | 说明 |
|:---|:---|
| VLAN | 虚拟局域网，逻辑隔离广播域 |
| 802.1Q | VLAN 标记标准，在帧中插入 4 字节 Tag |
| Tag 格式 | TPID(2B) + PCP(3bit) + DEI(1bit) + VID(12bit) |
| VID 范围 | 1-4094，其中 1 为默认 VLAN |
| Trunk | 交换机间的链路，承载多个 VLAN |

## 生成树协议（STP）

| 版本 | 收敛时间 | 特点 |
|:---|:---:|:---|
| STP (802.1D) | 30-50s | 基础，慢 |
| RSTP (802.1w) | ~6s | 快速收敛 |
| MSTP (802.1s) | ~6s | 多实例 |

## 常用命令

```bash
# Linux 查看二层信息
ip link show
bridge link show
bridge vlan show
arp -a

# 查看 MAC 地址表（交换机）
show mac address-table
show vlan brief
show spanning-tree
```
