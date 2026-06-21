# OSI 七层模型与 TCP/IP 四层模型

## OSI 七层模型

| 层级 | 名称 | 功能 | 协议/设备示例 |
|:---:|:---|:---|:---|
| 7 | 应用层 | 应用间通信 | HTTP/FTP/SMTP/DNS |
| 6 | 表示层 | 数据格式转换 | SSL/TLS/JPEG |
| 5 | 会话层 | 会话管理 | RPC/NetBIOS |
| 4 | 传输层 | 端到端传输 | TCP/UDP |
| 3 | 网络层 | 路由与寻址 | IP/ICMP/OSPF/BGP |
| 2 | 数据链路层 | 帧传输 | Ethernet/ARP/VLAN |
| 1 | 物理层 | 比特流传输 | 网线/光纤/集线器 |

## TCP/IP 四层模型

| 层级 | 对应 OSI | 协议 |
|:---|:---:|:---|
| 应用层 | L5-L7 | HTTP/DNS/SSH |
| 传输层 | L4 | TCP/UDP |
| 网络层 | L3 | IP/ICMP |
| 网络接口层 | L1-L2 | Ethernet/ARP |

## 数据传输过程

```
应用层: HTTP Request
传输层: SYNC (源端口:随机, 目标端口:80)
网络层: IP 包 (源IP:A, 目标IP:B)
数据链路层: 帧 (源MAC:AA, 目标MAC:BB)
物理层: 比特流 → 网线
```
