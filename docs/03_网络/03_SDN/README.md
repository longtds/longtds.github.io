# SDN（软件定义网络）

## 核心思想

SDN 将网络控制面与转发面分离，实现网络的集中化控制和可编程管理。

## OpenFlow 协议

OpenFlow 是 SDN 的核心协议，定义控制器与交换机之间的通信。

## SDN 控制器

| 控制器 | 语言 | 特点 |
|:---|:---|:---|
| ONOS | Java | 运营商级，高可用 |
| OpenDaylight | Java | 功能丰富 |
| Ryu | Python | 轻量级，学习成本低 |

## OVS（Open vSwitch）

OVS 是开源的虚拟交换机，广泛应用于虚拟化和容器场景。

```bash
# OVS 常用命令
ovs-vsctl add-br br0          # 创建网桥
ovs-vsctl add-port br0 eth0    # 添加端口
ovs-ofctl dump-flows br0       # 查看流表
ovs-vsctl show                 # 查看状态
```

## 与云原生的关系

Cilium 利用 eBPF 实现了类似 SDN 的功能，但性能更高、更灵活。
