# 三层协议

## IP 协议

IP 协议负责主机间的寻址和路由。IPv4 是目前的主流，IPv6 正在逐步普及。

## ARP 协议

ARP 将 IP 地址解析为 MAC 地址。ARP 欺骗是常见的中间人攻击手段。

## 路由协议

| 协议 | 类型 | 算法 | 适用场景 |
|:---|:---|:---|:---|
| RIP | 距离矢量 | Bellman-Ford | 小型网络 |
| OSPF | 链路状态 | Dijkstra SPF | 企业内网 |
| BGP | 路径矢量 | 路径属性 | 互联网/数据中心 |

## 常用命令

```bash
# 查看路由表
ip route show
route -n

# 排查连通性
ping -c 5 <target>
traceroute <target>

# BGP 检查（支持 BGP 的设备）
show bgp summary
show ip route bgp
```
