# 网络排查工具

## 连通性排查

```bash
# ICMP 连通性
ping -c 10 <target>
mtr <target>             # 持续追踪路径
traceroute <target>      # 路由路径

# 端口连通性
nc -zv <host> <port>     # TCP 端口扫描
nc -uzv <host> <port>    # UDP 端口扫描
```

## 抓包分析

```bash
# tcpdump
tcpdump -i eth0                          # 监听 eth0
tcpdump -i eth0 host 10.0.0.1            # 特定主机
tcpdump -i eth0 port 80                  # 特定端口
tcpdump -i eth0 -w capture.pcap          # 保存到文件
tcpdump -i eth0 -s 0 -v -c 1000         # 详细输出

# Wireshark 命令行分析
tshark -r capture.pcap
tshark -Y "http.request" -r capture.pcap
```

## 带宽与性能

```bash
# iperf3 带宽测试
iperf3 -s                        # 服务端
iperf3 -c <server> -t 30         # 客户端，测试30秒
iperf3 -c <server> -P 4         # 并行流

# ethtool 网卡信息
ethtool eth0                     # 链路协商状态
ethtool -i eth0                  # 驱动信息
ethtool -S eth0                  # 网卡统计计数器
```
