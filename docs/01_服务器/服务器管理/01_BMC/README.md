# BMC/IPMI

## 概述

BMC（Baseboard Management Controller）是服务器主板上的独立管理控制器，提供带外管理能力，不依赖操作系统即可远程管理服务器。

## 常用接口

| 厂商 | 管理接口 | 默认端口 |
|:---|:---|:---:|
| HP | iLO | HTTPS 443/SSH 22 |
| Dell | iDRAC | HTTPS 443 |
| Supermicro | IPMI | 623 UDP |
| Lenovo | IMM | HTTPS 443 |

## 常用操作

```bash
# IPMI 命令行工具
ipmitool -H <BMC_IP> -U <user> power status    # 查看电源状态
ipmitool -H <BMC_IP> -U <user> power on         # 开机
ipmitool -H <BMC_IP> -U <user> power reset      # 重启
ipmitool -H <BMC_IP> -U <user> chassis status   # 机箱状态
ipmitool -H <BMC_IP> -U <user> sensor list      # 传感器信息

# 远程控制台
ipmitool -H <BMC_IP> -U <user> sol activate     # 串口控制台
```
