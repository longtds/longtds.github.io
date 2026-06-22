# 16_故障排查 · 概述

> 排查能力 = 知识 × 方法 × 工具。学知识可以快，但排查方法需要练。

## 一、故障排查方法论

### 1.1 核心原则

```
1. 先恢复，后定位       ← 业务优先
2. 一个变量一个变量改   ← 避免叠加效应
3. 看数据，不靠猜       ← 工具说话
4. 假设 → 验证 → 调整   ← 科学方法
5. 复盘 + Runbook      ← 不重蹈覆辙
```

### 1.2 USE 方法（Brendan Gregg）

针对每个资源，关注三个维度：

| 维度 | 含义 |
|:---|:---|
| **U**tilization | 使用率 |
| **S**aturation | 饱和度 / 队列 |
| **E**rrors | 错误数 |

**资源**：CPU、内存、网络、磁盘、文件系统、连接池、线程池……

### 1.3 RED 方法（服务视角）

| 维度 | 含义 |
|:---|:---|
| **R**ate | 请求速率 |
| **E**rrors | 错误率 |
| **D**uration | 响应时间分布 |

### 1.4 排查路线图

```
故障告警 → 确认现象
   ↓
查监控（指标 + 日志 + 链路）
   ↓
假设故障原因
   ↓
缩小范围（时间、机器、服务）
   ↓
工具验证（top/strace/tcpdump/eBPF）
   ↓
修复 → 验证 → 复盘
```

## 二、Linux 性能排查六字诀

| 字 | 工具 | 关注 |
|:---|:---|:---|
| 看 | uptime/top/htop | 总负载 |
| 数 | vmstat/mpstat | CPU 细节 |
| 内 | free/sar/slabtop | 内存 |
| 盘 | iostat/iotop/pidstat | IO |
| 网 | sar/ss/iftop/tcpdump | 网络 |
| 追 | strace/perf/bpftrace | 系统调用 |

## 三、本章覆盖

| 子章节 | 内容 |
|:---|:---|
| **故障日志模板** | 标准化故障记录 |
| **01_Linux篇** | OOM / 高负载 / 网络 / IO |
| **02_K8s篇** | Pod 异常 / 网络 / 存储 / API |
| **03_中间件篇** | MySQL/Redis/Kafka/ES |
| **04_大数据篇** | Spark / Flink / HDFS 排查 |
| **05_AI推理篇** | GPU OOM / NCCL / 慢响应 |

## 四、必备工具箱

### 4.1 主机工具

```
- top / htop / atop          # 整体负载
- vmstat / mpstat            # CPU/内存
- iostat / iotop             # 磁盘 IO
- free / sar                 # 内存
- ss / netstat / iftop       # 网络连接
- tcpdump / Wireshark        # 抓包
- strace / ltrace            # 系统调用追踪
- perf / FlameGraph          # 性能分析
- bpftrace / bcc-tools       # eBPF 深度
```

### 4.2 容器/K8s

```
- kubectl describe pod       # 事件
- kubectl logs --previous    # 上一次容器日志
- kubectl debug              # 临时调试容器
- crictl ps / inspect        # 节点容器
- k9s / k0s                  # 交互式
- stern / kail               # 多 Pod 日志聚合
```

### 4.3 网络

```
- ping / mtr / traceroute    # 链路
- dig / nslookup             # DNS
- curl -v / httpie           # HTTP
- nc / socat                 # 端口
- iperf3                     # 带宽
```

### 4.4 内核态/eBPF

```
- bpftrace one-liners
- bcc-tools (execsnoop, tcpconnect, etc.)
- perf record / report
- ftrace
```

## 五、故障案例分析方法

每个故障建议按以下结构记录（详见"故障日志模板"）：

```
1. 故障现象（症状、影响、时间）
2. 处理过程（每一步、时间戳）
3. 根因（直接 + 根本）
4. 修复方案（临时 + 长期）
5. 影响评估（业务、用户、数据）
6. 改进项（预防、监控、流程）
7. Runbook 化（让下一次更快）
```

## 六、学习路径

1. **基础**：Linux 工具六字诀
2. **进阶**：eBPF / perf / 火焰图
3. **专项**：每个中间件一个真实案例
4. **K8s**：Pod 故障图谱 + 网络/存储排查
5. **方法论**：USE/RED + 复盘文化

> 📖 故障是免费的老师。**写不出复盘的故障，等于白经历**。
