# 高级

> 故障排查高级 = **大规模分布式定位 + Chaos Engineering + 全链路 SLO 工程化 + Postmortem 文化 + Continuous Profiling(Parca/Pyroscope) + Pixie/Coroot eBPF 平台 + AI 加持 AIOps 根因 + LLM 辅助排查 + 国产化故障(信创/麒麟/openEuler) + AI 工作负载排查(GPU/LLM 推理) + Confidential Computing 故障 + 异地多活+脑裂 + 网络深度(BGP/MTU/RPS/eBPF XDP) + 内核(crash dump/perf trace) + 大规模监控(VictoriaMetrics/Thanos) + 多集群多云**。本章面向 SRE 团队负责人 / 平台架构师。

## 一、大规模分布式定位

```
现象 → 排查矩阵:
  
延时突增:
  上游 / 下游 / DB / 缓存 / 网络 / GC / 锁 / 流量
  Trace 找 P99 慢调用
  Metrics 关联 (Exemplar)
  日志 (TraceID 串联)

5xx 突增:
  上游 health
  DB 连接池满
  线程池满
  限流触发
  灰度版本

可用性下降:
  节点失效 (K8s drain / cordon)
  网络分区 (BGP / 跨 AZ)
  存储 (CSI / 后端 EBS / 云硬盘)
  DNS (CoreDNS / 上游)

容量瓶颈:
  CPU/MEM/DISK/NET
  连接数 / FD
  Threadpool / Goroutine
  GC Pause
  IO util

工具协同:
  Metrics: Prom + VictoriaMetrics + Thanos
  Trace: OTel + Tempo / Jaeger
  Logs: Loki + ClickHouse
  Continuous Profile: Parca + Pyroscope
  eBPF: Pixie + Cilium Hubble + Coroot
  K8s: Lens + k9s + Kubernetes Dashboard
```

## 二、Chaos Engineering

```
理念:
  主动注入故障, 验证韧性
  
原则:
  1. 假设系统稳态
  2. 真实事件 (网络 / CPU / 磁盘 / Pod kill)
  3. 在生产 (小范围 + 控制)
  4. 持续 + 自动
  5. 控制爆炸半径

工具:
  Chaos Mesh ⭐ (CNCF, K8s native)
  Litmus (CNCF)
  Chaos Monkey (Netflix)
  Gremlin (商业)
  ChaosBlade (阿里, 国产) ⭐
  PowerfulSeal

实验:
  pod-kill / pod-failure
  network-delay / network-loss / network-partition
  io-delay / io-error
  cpu-burn / mem-burn
  time-skew
  kernel-fault

落地:
  GameDay (季度演练)
  灾备演练 (Region failover)
  混沌平台 (自动化)
  组合实验 (多故障)

KPI:
  RTO/RPO 验证
  MTTD/MTTR 演练值
  韧性评分
  Action Items 闭环
```

## 三、SLO 工程化

```
SLI (Indicator):
  Latency: P50/P95/P99
  Availability: 成功率
  Throughput: QPS
  Quality: 业务正确率
  
SLO (Objective):
  P99 < 200ms
  Availability > 99.95%
  
Error Budget:
  100% - 99.95% = 0.05% = 22 min / 月
  超支 → 冻结发布

工具:
  Sloth ⭐ (Prometheus SLO)
  OpenSLO (规范)
  Pyrra / Slok
  Nobl9 (商业)
  Google SRE Workbook

实践:
  - Tier 1: 99.95% / P99 100ms
  - Tier 2: 99.9% / P99 300ms
  - Tier 3: 99% / P99 1s

告警:
  Burn Rate ⭐ (替代固定阈值)
    Fast burn: 1h 烧 5% budget → P1
    Slow burn: 6h 烧 10% → P2
```

## 四、Postmortem 文化

```
原则:
  Blameless (无指责)
  系统问题 > 个人
  根因 (5 Whys)
  Action Items 必闭环
  Lessons Learned 共享

结构:
  1. 摘要 (1 段)
  2. 影响 (用户 / 业务 / 时长)
  3. 时间线 (分钟级)
  4. 根因 (5 Whys + 修复)
  5. 检测 + 响应 + 修复 评估
  6. Action Items (P0/P1/P2 + Owner + Deadline)
  7. Lessons Learned

工具:
  Notion / Confluence + 模板
  PagerDuty / FireHydrant (IR 平台)
  Jeli (Postmortem 商业)
  
跟踪:
  季度复盘
  Action 闭环 KPI > 80%
  重复故障 = 红线

文化建设:
  - Postmortem 必开 (P0/P1)
  - 跨团队 share
  - 季度 / 年度 review
  - 训练 Junior
```

## 五、Continuous Profiling

```
理念:
  生产持续 profile (低开销 < 1% CPU)
  从 火焰图 找代码瓶颈

工具:
  Parca ⭐ (Prometheus-style)
  Pyroscope ⭐ (Grafana, 现代)
  Polar Signals (商业 Parca)
  Datadog Continuous Profiler

支持:
  Go / Rust / C++ / Java / Python / Node / Ruby
  
集成:
  K8s DaemonSet (eBPF)
  Sidecar (语言 SDK)
  Prometheus 风格采集

效益:
  - 长期趋势 (退化检测)
  - 跨版本对比 (差分 FlameGraph)
  - 找微优化点 (CPU/内存)
  - 关联 Trace + Metrics
```

## 六、Pixie / Coroot / eBPF 平台

### 6.1 Pixie (New Relic)

```
能力:
  - 自动 eBPF 采集 (零代码)
  - HTTP/MySQL/Redis/DNS/MongoDB 协议解析
  - Service Map 自动
  - Latency / Throughput / Errors
  - PxL (Pixie Query Language)

部署:
  px deploy        # 一行 K8s 部署
  px run px/cluster

适用:
  K8s 必装 (新手友好)
  Service Map / Top SQL / 5xx 排查 神器
```

### 6.2 Coroot

```
能力:
  - eBPF 自动拓扑
  - SLO 自动推导
  - 异常自动检测
  - 根因建议 (Inspections)
  - 部署对比

适用:
  中小团队 SRE 平台 (low effort + high value)
```

### 6.3 Cilium Hubble

```
能力:
  - 网络流量 (eBPF)
  - Service Map
  - L7 协议
  - NetworkPolicy 验证 + 调试

排查:
  hubble observe --pod prod/api
  hubble observe --verdict DROPPED
  hubble ui
```

## 七、AIOps 加持

```
能力:
  - 异常检测 (替代静态阈值)
  - 告警降噪 + 聚类
  - 根因 (Top-K Suspects)
  - 影响面预测
  - LLM Postmortem 草稿

平台:
  阿里 ARMS (AIOps 模块) ⭐
  腾讯 TMP
  华为 AOps
  Coroot (开源)
  Microsoft Sentinel + Defender AI

LLM 加持:
  - 告警 → LLM 摘要 + 处理建议
  - 日志 → LLM 模式抽取
  - Postmortem → LLM 起草
  - Runbook → LLM 检索 + 执行
  
工具:
  阿里 通义 SRE (内部)
  Datadog Bits AI
  PagerDuty AIOps
  Grafana LLM Plugin

5 年判断:
✅ LLM Postmortem 普及 (2027+)
✅ Agent 自愈 (限制范围, 2028+)
```

## 八、LLM 辅助排查

```
工具:
  Grafana LLM (开源, 免费 OSS)
  Datadog Bits AI
  阿里通义 SRE
  自建: OpenAI / DeepSeek + Function Call + 内部 API

典型流程:
  告警 → LLM 总结 + 关联 (Logs/Trace/Metrics) → 建议 → Runbook
  
能力:
  - 告警分类 + 严重度
  - 关联事件 (跨系统)
  - Logs 摘要 + 异常抽取
  - SQL 慢查询解读 + 索引建议
  - 历史相似事件 (RAG)
  - Postmortem 起草

注意:
  - 训练数据隐私
  - 工具调用鉴权 (MCP)
  - 决策权 (建议 ≠ 执行)
  - Hallucination 防御
```

## 九、AI 工作负载排查

### 9.1 GPU 故障

```bash
# 监控
nvidia-smi
nvidia-smi dmon -s pucvmet   # 持续
nvidia-smi --query-gpu=temperature.gpu,power.draw,utilization.gpu --format=csv -l 1

# DCGM (Datacenter GPU Manager) ⭐
dcgmi diag -r 4               # 全诊断
dcgmi health --check-all
dcgm-exporter (Prometheus)

# NCCL (多卡通信)
NCCL_DEBUG=INFO
NCCL_DEBUG_SUBSYS=ALL
nccl-tests (allreduce_perf)

# 错误
- ECC 错误 → 硬件
- Xid (kernel 错) → dmesg | grep -i nvidia
- Out of memory → batch_size / KV cache
- 训练 hang → NCCL timeout + 网卡

工具:
  DCGM + Prometheus
  GPU Operator (NVIDIA K8s)
  Pixie GPU profiler (eBPF)
```

### 9.2 LLM 推理

```
vLLM / SGLang 排查:
  - GPU 显存满 → 调 KV cache / 模型量化
  - QPS 低 → 调 batch / continuous batching
  - P99 高 → speculative decoding / chunked prefill
  - OOM → max_model_len / dtype / quant

监控:
  /metrics (Prometheus)
  tokens/s, P99, KV usage, 队列长度

工具:
  vLLM 自带 metrics
  llm-d (生产化)
  llmperf (压测)
  benchmark (HF 官方)
```

### 9.3 训练故障

```
常见:
  - NaN/Inf loss → 学习率 / 数据 / 混合精度
  - 训练 hang → NCCL timeout / 死锁
  - 检查点过大 → ZeRO / Sharded
  - 显存不够 → ZeRO-Offload / Gradient Checkpoint

工具:
  PyTorch Profiler
  TensorBoard
  DeepSpeed monitor
  Weights & Biases
  ML Flow
```

## 十、国产化故障（信创）

```
OS:
  openEuler / 麒麟 / UOS
  rpm 兼容 → 部分包不在源
  内核版本 (5.10 / 4.19)
  
DB:
  TiDB / OceanBase / PolarDB / GaussDB
  TiUP / OceanBase OAT 工具
  慢日志 / Schema 兼容
  
中间件:
  RocketMQ (阿里 → Apache)
  DolphinScheduler / Seatunnel
  
排查难点:
  - 文档少, 社区小
  - 工具栈与开源略异
  - 兼容性 (老应用)
  - 厂商支持 (合同)

应对:
  - 内部知识库
  - 厂商技术支持合同
  - 升级路径规划
```

## 十一、Confidential Computing 故障

```
TEE:
  Intel TDX / AMD SEV-SNP / 海光 CSV
  
故障:
  - Attestation 失败 (证书 / Quote 过期)
  - 性能下降 (TEE 开销 5-15%)
  - 内存限制 (EPC / SEV 容量)
  - 调试困难 (Enclave 内不可观测)

工具:
  TEE Attestation Service
  Confidential Containers (Kata-cc) 日志
  occlum / inclavare (国产)

排查:
  - 启动验证 (PCR / Quote)
  - 内存性能 (EPC paging)
  - 网络 mTLS + Attestation 联动
```

## 十二、异地多活 + 脑裂

```
单元化:
  按用户 / 区域 / 业务 分单元
  写本单元 + 异步同步
  容灾切换 (分钟级)

技术:
  阿里 LDC (Logical Data Center)
  美团 OCTO
  字节 GLB

故障:
  - 单元间网络 (延迟 / 丢包)
  - 数据冲突 (双写)
  - 切换不一致 (DNS / 配置中心 / Service)
  - 脑裂 (集群分区)

工具:
  Consul / Nacos (服务发现)
  DNS based GSLB
  Anycast IP

排查:
  - 流量 (谁拿请求)
  - 数据 (主单元一致)
  - 配置 (哪个版本)
  - 演练 (季度切换)
```

## 十三、网络深度

```
BGP:
  路由不通 → 邻居关系 / AS-path / 路由策略
  工具: gobgp / bird / Quagga
  Cilium BGP

MTU:
  ping -M do -s 1472 host   # 1472+28=1500
  mtu mismatch → 大包丢
  GRE/VXLAN overhead

RPS / RSS / RFS / XPS:
  多队列 / NUMA 亲和
  ethtool -l / -L 设置
  /proc/irq/<n>/smp_affinity
  set_irq_affinity.sh

XDP / eBPF:
  Cilium XDP (load balancer)
  Katran (Facebook)
  bpftrace XDP

DPDK / SmartNIC:
  低延迟金融 / NFV
  
排查:
  ss -ti                       # tcp_info (拥塞窗口/rtt)
  ethtool -S eth0              # 网卡统计 (drops/errors)
  ip -s link                   # 包 / 字节 / 错误
  tc qdisc show                # 流控
  conntrack -L                  # NAT 表
```

## 十四、内核 + crash dump

```bash
# kdump 配置
yum install kexec-tools
systemctl enable kdump --now

# 触发 crash (测试)
echo c > /proc/sysrq-trigger

# 分析
crash /usr/lib/debug/lib/modules/<kernel>/vmlinux /var/crash/<ts>/vmcore
crash> bt           # 调用栈
crash> log          # dmesg
crash> ps           # 进程
crash> mod          # 模块

# 工具
crash + vmlinux + debuginfo
kgdb (在线调试)
ftrace / trace-cmd
SystemTap (老)
eBPF (现代)

# perf trace
perf trace -p <pid>
perf trace -e syscalls:sys_enter_open
perf ftrace
```

## 十五、大规模监控

```
单 Prometheus 限制:
  - 千万级时间序列瓶颈
  - 长期存储难

方案:
  VictoriaMetrics ⭐ (单二进制, 高压缩, 国产化友好)
  Thanos (Sidecar / Receive + 对象存储)
  Cortex / Mimir
  M3 (Uber)

国产:
  阿里 ARMS / 腾讯 TPS / 华为 AOM
  夜莺 Nightingale ⭐ (滴滴)

日志:
  Loki ⭐ (label 索引 + 全文 grep)
  ClickHouse + Vector
  Elastic + Hot/Warm/Cold ILM
  阿里 SLS
  
Trace:
  Tempo (大规模) ⭐
  Jaeger + Cassandra/ES
  ClickHouse + OpenObserve
```

## 十六、多集群+多云

```
多集群挑战:
  统一观测 / 跨集群 RBAC / Failover

工具:
  Argo CD (GitOps 多集群)
  Karmada (国产, 中信银行/华为) ⭐
  Clusterpedia (跨集群查询)
  Open Cluster Management (RH)
  Fleet (Rancher)

观测:
  Prom Federation / Thanos
  Grafana 多 datasource
  Loki 多 cluster

故障:
  - Cluster federation 同步
  - Cross-cluster network (Submariner / Cilium ClusterMesh)
  - Identity (SPIFFE 跨集群)
  - DNS (CoreDNS + ExternalDNS)
```

## 十七、Checklist（高级）

```
分布式:
☐ Metrics + Trace + Logs + Profile + eBPF 五位一体
☐ Pixie + Coroot + Hubble (eBPF 平台)
☐ Continuous Profiling (Parca/Pyroscope)

Chaos:
☐ Chaos Mesh / ChaosBlade
☐ GameDay 季度
☐ RTO/RPO 验证

SLO:
☐ Sloth + Burn Rate alert
☐ 三级 SLO (Tier1/2/3)
☐ Error Budget 冻结发布

Postmortem:
☐ Blameless 文化
☐ 5 Whys + Action 闭环 > 80%
☐ 季度复盘

AIOps:
☐ 异常检测替代静态
☐ 告警聚类降噪
☐ LLM Postmortem 起草

AI 工作负载:
☐ DCGM + GPU Operator
☐ NCCL debug + Xid 错误
☐ vLLM metrics + llm-d

信创:
☐ openEuler/麒麟 排查工具
☐ TiDB/OceanBase 慢日志
☐ 厂商支持合同

Confidential:
☐ TEE Attestation
☐ TEE 调试限制理解

异地多活:
☐ 单元化 + 季度切换演练
☐ 脑裂保护
☐ GSLB

网络:
☐ BGP + MTU + RPS + XDP
☐ ss tcp_info + ethtool

内核:
☐ kdump + crash
☐ perf trace + ftrace + eBPF

大规模监控:
☐ VictoriaMetrics + Thanos + Loki + Tempo
☐ 国产 ARMS / 夜莺

多集群:
☐ Argo CD + Karmada
☐ ClusterMesh + Hubble
```

## 十八、推荐栈（高级）

```
Metrics:    VictoriaMetrics ⭐ / Thanos / 夜莺
Logs:       Loki ⭐ + ClickHouse + 阿里 SLS
Trace:      OTel + Tempo ⭐ / Jaeger / SkyWalking
Profile:    Parca + Pyroscope ⭐
eBPF:       Pixie ⭐ + Coroot + Cilium Hubble + Inspektor Gadget
Chaos:      Chaos Mesh ⭐ + ChaosBlade ⭐ + LitmusChaos
SLO:        Sloth + OpenSLO + Burn Rate
AIOps:      阿里 ARMS / 腾讯 TMP / 华为 AOps / Coroot
LLM SRE:    Grafana LLM + Datadog Bits AI + 自建 (DeepSeek)
GPU:        DCGM ⭐ + nvitop + GPU Operator
LLM 推理:   vLLM metrics + llm-d + llmperf
信创:        TiDB/OceanBase 自有工具 + 厂商支持
Confidential: Kata-cc + Attestation Service
多活:        阿里 LDC + Nacos + Sentinel + GSLB
网络深度:    Cilium ⭐ + BPF + XDP + Hubble
内核:        kdump + crash + perf + bpftrace
多集群:     Karmada ⭐ + Argo CD + ClusterMesh
管理:        PagerDuty / FireHydrant ⭐ + Notion / Confluence
```

> 📖 **核心判断**：故障排查高级 = **分布式定位(Metrics+Trace+Logs+Profile+eBPF 五位一体) + Chaos Engineering(Chaos Mesh/ChaosBlade) + SLO 工程化(Sloth/Burn Rate) + Blameless Postmortem + Continuous Profiling(Parca/Pyroscope) + Pixie/Coroot 平台 + AIOps + LLM SRE + GPU/LLM 推理排查(DCGM/vLLM) + 信创+Confidential + 异地多活 + 网络深度(BGP/MTU/XDP) + 内核(kdump/perf/eBPF) + 大规模监控(VM/Thanos/Loki/Tempo) + 多集群(Karmada)**。能给"大型互联网/央企信创 K8s + AI + 多活 + 多云"画完整可观测平台并主导 IR + Postmortem 文化, 就具备 SRE 团队负责人/平台架构师能力。
