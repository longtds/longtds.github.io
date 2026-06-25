# 成本优化（FinOps + AI 成本）

> 云原生 + AI 时代的最大命题：**算力既贵又紧缺**。CPU 算力靠 FinOps 治理，**GPU 算力靠精细化调度 + 模型优化**。一个 SRE 不懂成本就只是"半个 SRE"。

## 一、成本治理金字塔

```
                    ┌─────────────────┐
                    │   决策 (Decide)  │   ← 砍/合并/降配
                    ├─────────────────┤
                    │   归因 (Allocate) │   ← 哪个团队/业务花的
                    ├─────────────────┤
                    │   分析 (Analyze) │   ← 趋势/异常/浪费
                    ├─────────────────┤
                    │   可见 (Visible) │   ← 数据看板
                    ├─────────────────┤
                    │   采集 (Collect) │   ← 账单/Tag/利用率
                    └─────────────────┘

→ 没有"可见"就没有"治理"，先把数据建好
```

## 二、FinOps 三阶段

```
1. Inform（信息透明）
   - 看到花了多少钱
   - 按团队/业务/环境归因
   - 异常账单告警

2. Optimize（持续优化）
   - 闲置资源识别
   - Rightsize（合理规格）
   - 预留实例 / Spot
   - 自动调度

3. Operate（持续运营）
   - 成本指标 KPI
   - FinOps 团队
   - 跨部门治理
```

**经验**：大部分团队卡在阶段 1，因为**没有 Tag + 没有看板 + 没有 Owner**。

## 三、传统云成本优化（CPU/存储/网络）

### 3.1 闲置资源识别

```promql
# 7 天 CPU 平均 < 5% 的 EC2/VM
avg_over_time(node_cpu_usage[7d]) < 0.05

# 闲置磁盘（30 天无 IO）
rate(disk_read_bytes[30d]) == 0 and rate(disk_write_bytes[30d]) == 0

# 未挂载的 EBS / 云硬盘
aws ec2 describe-volumes --filters Name=status,Values=available

# K8s 中未被任何 Pod 引用的 PVC
kubectl get pvc --all-namespaces -o json | jq '...'

# Idle Load Balancer
aws elbv2 describe-load-balancers + 没有 active target
```

### 3.2 Rightsizing（合理规格）

```python
# 收集 7 天峰值利用率
def rightsize_recommendation(instance):
    cpu_p95 = query_prom_p95(f"node_cpu_usage{{instance='{instance}'}}", "7d")
    mem_p95 = query_prom_p95(f"node_mem_usage{{instance='{instance}'}}", "7d")
    
    current_specs = describe_instance(instance)
    target_specs = pick_smallest_fit(cpu_p95 * 1.2, mem_p95 * 1.2)
    
    if target_specs.price < current_specs.price * 0.8:
        return {
            "current": current_specs,
            "recommend": target_specs,
            "monthly_saving": current_specs.price - target_specs.price
        }
```

### 3.3 预留实例（RI）/ Savings Plan / Spot

| 方案 | 折扣 | 适合 |
|:---|:---:|:---|
| **按需 (On-Demand)** | 0% | 临时 / 不确定负载 |
| **预留实例 1 年** | 30-40% | 长期稳定负载 |
| **预留实例 3 年** | 50-60% | 极度稳定 |
| **Savings Plan** | 30-72% | 灵活（AWS 跨实例族） |
| **Spot / 抢占** | **70-90%** | **批处理 / 容错** |

**实战配比**：基线负载 70% RI + 弹性负载 30% On-Demand + 任务负载 100% Spot。

### 3.4 K8s 集群成本优化

```
✅ Cluster Autoscaler 自动扩缩
✅ HPA / VPA 自动伸缩
✅ Karpenter（AWS）/ 国产替代品：自动选最便宜机型
✅ Bin-packing 调度（节点装满再开新节点）
✅ 多 NodePool（按需/Spot 混部）
✅ Spot Pool + 优雅退出
✅ Pod 资源 request/limit 校准
✅ 闲时 hibernate（开发/测试集群）
```

### 3.5 存储成本

```
分层存储:
  热数据  SSD            $0.10/GB
  温数据  HDD            $0.04/GB
  冷数据  对象存储 / 归档  $0.004/GB
  
对象存储分层（S3）:
  Standard         热
  Intelligent      AI 自动迁移
  IA (Infrequent)  温
  Glacier          冷（提取慢）
  Deep Archive     极冷（提取 12h+）

策略:
  ✅ 生命周期规则自动迁移
  ✅ 删除孤儿 Snapshot
  ✅ 压缩 + 去重（ZFS/Btrfs/对象存储天然）
  ✅ 数据保留期严格
```

### 3.6 网络成本（最容易被忽略）

```
公网流量出口最贵:
  AWS: $0.09/GB
  GCP: $0.12/GB
  阿里云: ¥0.5-0.8/GB

优化:
  ✅ CDN 缓存（流量便宜 10x）
  ✅ 私有连接（VPC Peering / Direct Connect）
  ✅ 跨可用区流量收敛
  ✅ 压缩 + HTTP/2 / QUIC
  ✅ 出口流量监控（哪个服务在烧钱）
  
PrivateLink / VPC Endpoint:
  → 替代 NAT 网关访问 S3/RDS，省 NAT 成本
```

## 四、Tag / Label 体系（一切的基础）

### 4.1 推荐标签

```
必填:
  cost-center      成本中心
  team             团队
  business         业务线
  env              环境 (prod/staging/dev)
  service          服务名
  owner            责任人
  
推荐:
  project          项目
  ticket           关联工单
  expire           销毁时间（临时资源）
  data-classification 数据等级
```

### 4.2 Tag 治理

```python
# Tag 合规扫描（每日）
def scan_tag_compliance(resources):
    REQUIRED = ['cost-center', 'team', 'env', 'owner']
    violations = []
    for r in resources:
        missing = [t for t in REQUIRED if t not in r.tags]
        if missing:
            violations.append({"resource": r.id, "missing": missing})
    return violations

# 违规处理:
#   - 通知 owner
#   - 一周宽限
#   - 仍不补 → 标记 ToBeDeleted
#   - 月底彻底删除
```

### 4.3 K8s Label / Annotation

```yaml
metadata:
  labels:
    app: order-api
    team: payment
    cost-center: cc-001
    env: prod
  annotations:
    cost.cncf.io/business: "电商核心"
    cost.cncf.io/owner: "zhangsan@company.com"
```

## 五、可见性工具

### 5.1 多云成本管理

| 工具 | 类型 |
|:---|:---|
| **AWS Cost Explorer** | AWS 原生 |
| **GCP Cost Management** | GCP 原生 |
| **Azure Cost Management** | Azure 原生 |
| **阿里云费用中心** | 国内 |
| **CloudHealth / Cloudability** | 商业 |
| **Apptio Cloudability** | 商业 |
| **Spot.io / NetApp** | 商业 |

### 5.2 K8s 成本可视化（开源）

| 工具 | 特点 |
|:---|:---|
| **OpenCost** ⭐⭐⭐⭐⭐ | CNCF, K8s 成本归因事实标准 |
| **Kubecost** | OpenCost 商业版 + UI |
| **CAST AI** | 自动优化平台 |
| **PerfectScale** | K8s rightsizing |
| **Komiser** | 多云成本可视化 |
| **CloudCarbonFootprint** | 碳足迹 + 成本 |

### 5.3 OpenCost 部署示例

```bash
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm install opencost opencost/opencost \
  --namespace opencost --create-namespace \
  --set opencost.prometheus.internal.enabled=true

# 查看按 namespace 成本
opencost --window 7d --aggregate namespace
```

### 5.4 自建账单分析（推荐）

```
账单导出（CUR/账单 API）
   ↓
S3 / OSS
   ↓
Spark / DuckDB ETL
   ↓
PG / ClickHouse
   ↓
Superset / Grafana
   ↓
团队/业务/产品看板
```

## 六、AI / GPU 成本优化（2025 主战场）

### 6.1 GPU 是新的"成本黑洞"

```
单卡价格（2025）:
  A100 80GB:  ¥10万+/年（云上租）
  H100 80GB:  ¥20万+/年
  H200:        ¥25万+/年
  4090 24GB:  ¥1.5万/年（消费级，灰色市场）
  L20 / L40:  ¥5-8万/年

100 张 H100 集群:
  硬件折旧:  ¥2000万 / 3年
  电费:     ¥120万 / 年
  机房:     ¥100万 / 年
  人力:     ¥300万 / 年
  
→ 一年烧 ¥1000 万很常见
→ 利用率从 30% 提到 70% = 省 ¥400 万
```

### 6.2 GPU 利用率监控

```promql
# DCGM Exporter 关键指标
DCGM_FI_DEV_GPU_UTIL              # SM 利用率
DCGM_FI_DEV_FB_USED               # 显存使用
DCGM_FI_DEV_FB_FREE               # 显存空闲
DCGM_FI_DEV_POWER_USAGE           # 功耗
DCGM_FI_DEV_GPU_TEMP              # 温度
DCGM_FI_PROF_PIPE_TENSOR_ACTIVE   # Tensor Core 利用率
DCGM_FI_PROF_SM_OCCUPANCY         # SM 占用率
DCGM_FI_DEV_PCIE_TX/RX_THROUGHPUT # PCIe 吞吐

# 推理利用率指标
vllm:gpu_cache_usage_perc         # KV Cache 利用率
vllm:num_requests_running         # 并发请求数
vllm:e2e_request_latency_seconds  # 端到端延迟
```

### 6.3 训练成本优化

```
1. 算力调度
   ✅ Gang Scheduling（一组 Pod 同时启动，避免抢资源死锁）
   ✅ Topology-Aware（NVLink/IB 拓扑感知）
   ✅ 优先级队列（在线推理 > 训练 > 测试）

2. 训练加速
   ✅ Mixed Precision (FP16/BF16) → 2x 速度
   ✅ Gradient Checkpointing → 省 50% 显存
   ✅ ZeRO-3 / FSDP → 大模型分片
   ✅ DeepSpeed / Megatron-LM
   ✅ Flash Attention 2 / 3
   ✅ Liger Kernel / Unsloth → 单卡微调 2x

3. 数据加速
   ✅ NVMe + DataLoader 多 worker
   ✅ 预处理离线化
   ✅ 数据格式: WebDataset / MosaicML StreamingDataset

4. Checkpoint 优化
   ✅ 异步 checkpoint
   ✅ 增量 checkpoint
   ✅ 分布式 checkpoint
```

### 6.4 推理成本优化（重头戏）

```
A. 模型层面
   - 量化 (INT8/INT4/FP8)        → 显存省 4-8x，速度 +50%
   - 蒸馏 (大模型 → 小模型)        → 成本省 5-10x
   - LoRA / QLoRA 微调            → 训练成本省 10x
   - 推测解码 (Speculative Decoding) → 速度 +30-50%

B. 推理引擎
   - vLLM ⭐                       → PagedAttention，吞吐 +5-10x
   - SGLang                       → RadixAttention，KV 复用
   - TensorRT-LLM                 → NVIDIA 极致优化
   - llama.cpp / MLC              → CPU/边缘
   - TGI (HuggingFace)            → 老牌

C. 调度层面
   - 连续批处理 (Continuous Batching)
   - Prefill-Decode 分离 (PD 分离)
   - 多模型共置 (Model Routing)
   - 动态 LoRA 加载
   - KV Cache 跨请求复用

D. 路由策略
   - 简单请求 → 小模型 (7B)
   - 复杂请求 → 大模型 (72B)
   - 长上下文 → 专用模型
   - 多模态 → 专用模型

E. 缓存
   - Response Cache (Redis)       → 重复 query 命中
   - Prompt Cache                 → 系统提示词复用
   - KV Cache Persistence
```

### 6.5 vLLM 推理成本示例

```yaml
# vLLM 部署：单 H100 跑 Qwen3-32B-AWQ
# 量化前: H100 单卡跑不下 32B（160GB FP16）
# 量化后: AWQ-INT4 仅需 ~20GB，单卡跑 + 大量 KV

containers:
- name: vllm
  image: vllm/vllm-openai:latest
  args:
    - --model=Qwen/Qwen3-32B-AWQ
    - --quantization=awq
    - --max-model-len=32768
    - --gpu-memory-utilization=0.9
    - --max-num-seqs=128
    - --enable-prefix-caching     # KV Cache 复用
    - --enable-chunked-prefill    # Prefill 切片
  resources:
    limits:
      nvidia.com/gpu: 1
```

**成本对比**：
| 部署 | 显存 | 吞吐 | 单 token 成本 |
|:---|:---:|:---:|:---:|
| FP16 不量化 | 64GB × 2 卡 | 100 token/s | ¥0.01 |
| AWQ INT4 | 20GB × 1 卡 | 80 token/s | **¥0.0015** |
| 量化 + Prefix Cache | 20GB × 1 卡 | 200 token/s | **¥0.0006** |

→ **优化 16x**

### 6.6 GPU 调度（K8s）

```
框架:
  ✅ Volcano（CNCF, 中国主导）
  ✅ Kueue（Kubernetes 原生）
  ✅ KubeRay（Ray on K8s）
  ✅ Run.AI（商业）

特性:
  - Gang scheduling
  - 多队列优先级
  - 公平调度 (DRF / Capacity)
  - GPU 拓扑感知
  - MPS / MIG 切分
```

### 6.7 GPU 切分（MIG / MPS / TimeSlicing）

| 方式 | 隔离 | 适合 |
|:---|:---|:---|
| **MIG** | 硬隔离 (A100/H100) | 多租户推理 |
| **MPS** | 进程级 | 多任务共享 |
| **Time Slicing** | 时间片 | 开发测试 |
| **HAMI** | 国产 vGPU 方案 | 国内主流 |

```yaml
# MIG 切 1 张 A100 80GB 为 7 个 10GB 实例
apiVersion: v1
kind: ConfigMap
metadata:
  name: mig-config
data:
  config.yaml: |
    version: v1
    mig-configs:
      all-1g.10gb:
        - devices: all
          mig-enabled: true
          mig-devices:
            "1g.10gb": 7
```

### 6.8 共享 GPU 池

```
HAMI / 阿里 cGPU / 腾讯 qGPU / vCUDA:
  ✅ 显存软切分（按 MB）
  ✅ 算力按比例
  ✅ 适合：多个小模型部署 / 测试环境
  ❌ 不适合: 强隔离场景

效果:
  原本 1 卡 1 服务 → 1 卡 4-8 服务
  利用率 30% → 70%
  
中国头部团队（字节、阿里、商汤）大量在用
```

## 七、推理成本看板（生产实战）

### 7.1 关键指标

```
利用率:
  - GPU SM 利用率（按服务）
  - KV Cache 利用率
  - 显存利用率
  - 平均 batch size
  - QPS

成本:
  - 单 token 成本
  - 单请求成本
  - 单用户日成本
  - 模型 ROI

业务:
  - 命中率（缓存）
  - 模型路由分布
  - 长尾请求占比
```

### 7.2 单 token 成本计算

```python
def cost_per_token(deployment):
    gpu_cost_per_hour = 12     # H100 云上 ¥12/h
    num_gpus = deployment.num_gpus
    tokens_per_hour = deployment.throughput * 3600
    
    return (gpu_cost_per_hour * num_gpus) / tokens_per_hour

# 例:
#   单 H100 + Qwen3-32B-AWQ, 200 token/s
#   = ¥12 / (200 * 3600) = ¥0.0000167/token
#   1M token ≈ ¥16.7
```

### 7.3 模型路由省钱

```python
# 路由策略示例
def route(request):
    # 简单分类问题 → 小模型
    if request.intent == "classify" or len(request.prompt) < 100:
        return "Qwen3-7B"           # ¥0.5/1M token
    
    # 长上下文 RAG
    if request.context_len > 32k:
        return "Qwen3-32B-AWQ"      # ¥5/1M token
    
    # 复杂推理 / 代码生成
    if request.task in ["code", "math", "reasoning"]:
        return "DeepSeek-V3"        # ¥20/1M token
    
    # 默认
    return "Qwen3-14B"              # ¥2/1M token

# 实测: 路由后平均成本下降 60%（多数请求被小模型接住）
```

## 八、KV Cache 优化（成本关键点）

```
KV Cache 决定一切:
  - 显存最大占用就是它
  - 决定最大并发
  - 决定吞吐天花板

优化技术:
  1. PagedAttention（vLLM）        分页管理，碎片降为 0
  2. Prefix Caching（前缀缓存）     系统提示词复用
  3. KV Cache 量化（FP8）          显存省 2x
  4. RadixAttention（SGLang）      前缀树共享
  5. KV Cache 跨请求持久化          多轮对话省
  6. KV Cache 异步换出（CPU/磁盘）   长会话超长上下文
```

## 九、PD 分离（Prefill-Decode 分离）

```
传统方式:
  Prefill 和 Decode 共用 GPU
  → Prefill 长请求阻塞 Decode 短请求
  → P99 TTFT 抖动

PD 分离:
  Prefill 节点 (计算密集) 和 Decode 节点 (内存带宽密集) 分开部署
  → 互不干扰
  → 各自优化

效果:
  - TTFT P99 降 50%
  - TPOT 更稳定
  - 总吞吐 +30%

工具:
  - vLLM 0.6+ 实验性 PD
  - DistServe (论文)
  - llm-d (Hugging Face)
  - Mooncake (月之暗面开源)
```

## 十、成本异常检测

```python
# 用 1 章异常检测的方法做成本监控
import numpy as np

def detect_cost_anomaly(daily_costs, dim='service'):
    """日均成本突增 >50% = 异常"""
    df = pd.DataFrame(daily_costs)
    yesterday = df.iloc[-1]
    baseline = df.iloc[-8:-1].median()
    
    spike = (yesterday - baseline) / baseline
    return df[spike > 0.5]

# 触发条件:
#  - 某服务日成本环比 +50%
#  - 某 region 网络出口流量 +100%
#  - 某团队总成本突破预算
#  - 某 GPU 利用率突降 + 成本未降 (浪费)
```

## 十一、FinOps 组织机制

### 11.1 角色

```
FinOps 团队（2-5 人）:
  - 成本数据工程师
  - 成本分析师
  - FinOps 实践者
  - SRE / 平台工程师

合作角色:
  - 财务 (Finance)
  - 业务负责人 (Business Owner)
  - 平台/SRE
  - 采购
```

### 11.2 KPI

```
公司级:
  ✅ 单位收入成本（成本/营收）
  ✅ 月度云成本增长率 vs 业务增长率
  ✅ 浪费率（闲置 + 低利用）

团队级:
  ✅ 业务单价成本（每订单 / 每用户 / 每 token）
  ✅ 资源利用率
  ✅ Tag 合规率
  ✅ 预算执行率
```

### 11.3 治理流程

```
月度:
  - 各团队成本月报
  - TOP 浪费项整改
  - Spot/RI 比例评估
  - 新业务成本评估

季度:
  - 全公司 FinOps 复盘
  - 预算调整
  - 工具/流程升级

年度:
  - 多年合同 / RI 续约
  - 厂商谈判
  - 架构决策（多云 vs 单云）
```

## 十二、常见坑

| 坑 | 建议 |
|:---|:---|
| **没有 Tag** | 强制 + 扫描 + 处罚 |
| **看不到** | 先建看板，再谈优化 |
| **数据延迟 1 天** | 接近实时（小时级） |
| **没有 owner** | 每个资源必有 owner |
| **优化没人执行** | KPI 绑定 + 复盘 |
| **盲目用 Spot** | 弹性 / 可重试场景才用 |
| **预留过头** | 业务变化快需求时谨慎 RI |
| **存储忘了清** | 生命周期规则 |
| **网络出口爆炸** | 出口流量监控 |
| **GPU 利用率低** | 监控 + 共享 + 路由 |
| **训练不量化** | 必上 MP/BF16 |
| **推理不量化** | INT4/INT8 / FP8 必上 |
| **没有 KV Cache 复用** | 必开 prefix caching |
| **大小模型混用** | 模型路由 |
| **多云分散** | 集中归一 / 厂商谈判 |
| **Carbon 不算** | ESG 时代要算碳 |

## 十三、最佳实践清单

```
基础设施:
☐ Tag 体系 + 强制扫描
☐ 多云账单统一入库
☐ 实时看板（成本 + 利用率）
☐ 异常告警

CPU/存储/网络:
☐ Rightsizing 周期评审
☐ RI/SP 比例规划
☐ Spot 适用场景识别
☐ 闲置资源月度清理
☐ 网络出口监控
☐ 存储分层 + 生命周期

K8s:
☐ HPA/VPA 启用
☐ Cluster Autoscaler
☐ Karpenter（如适用）
☐ Bin-packing 调度
☐ 资源 request/limit 校准

AI / GPU:
☐ DCGM Exporter
☐ GPU 利用率看板
☐ 推理量化（INT4/INT8）
☐ vLLM + Prefix Cache
☐ 模型路由（大小模型）
☐ MIG / MPS / HAMI 切分
☐ PD 分离（高级）
☐ 单 token 成本指标
☐ Spot GPU 用于训练

组织:
☐ FinOps 团队
☐ 月度成本评审
☐ 业务成本 KPI
☐ 浪费奖惩制度
```

## 十四、学习路径

```
入门（1 个月）:
  1. 装 OpenCost + Grafana
  2. 建 Tag 体系
  3. 写 5 条浪费告警
  4. 第一次 Rightsizing

中级（3 个月）:
  5. K8s HPA/VPA/CAS 全开
  6. Karpenter / Spot 混部
  7. 存储 / 网络专项
  8. 月度成本月报机制

高级（半年+）:
  9. GPU 利用率优化
  10. vLLM 量化 + Prefix Cache
  11. 模型路由 + 大小模型混部
  12. MIG / HAMI 共享
  13. PD 分离实战
  14. FinOps 组织建设
```

## 十五、参考资料

```
书:
  - 《Cloud FinOps》(O'Reilly)
  - 《The Cost of Cloud》(Andreessen Horowitz)
  - 《Designing ML Systems》(Huyen) - 推理成本章节

社区:
  - FinOps Foundation: https://www.finops.org/
  - CNCF FinOps SIG
  - 国内 FinOps 联盟（云原生计算基金会）

开源:
  - OpenCost: https://www.opencost.io/
  - Karpenter: https://karpenter.sh/
  - Volcano: https://volcano.sh/
  - HAMI: https://github.com/Project-HAMi/HAMi
  - vLLM: https://github.com/vllm-project/vllm
  - SGLang: https://github.com/sgl-project/sglang

商业:
  - CloudHealth / Apptio Cloudability
  - Spot.io / NetApp
  - CAST AI
  - Densify
  - 阿里云 FinOps / 腾讯云 TCM Cost
```

> 📖 **核心判断**：2025 SRE 的两大成本主战场——**FinOps（CPU/存储/网络）** 已经成熟，**AI 成本（GPU/推理/训练）** 才刚刚开始。**GPU 单卡 ¥10-25 万/年**，利用率从 30% 提到 70% 直接省百万。**量化（INT4/FP8）+ vLLM + Prefix Cache + 模型路由 + HAMI/MIG** 是 AI 成本优化的五大支柱，把这五点做透，推理成本能压到原来的 1/10。
