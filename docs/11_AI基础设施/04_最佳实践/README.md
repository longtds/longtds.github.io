# 最佳实践

> AI 基础设施最佳实践 = **集群规模与拓扑设计 + GPU/NPU 资源规划 + 训推平台架构 + 镜像/模型/数据治理基线 + MLOps 流水线 + 监控/告警/SLO + 多租户隔离 + 容量+成本(FinOps GPU) + 容灾备份 + 升级 SOP + 国产化路径 + 模型生命周期 + 安全合规 + Incident SOP + 团队组织**。本章把"会跑训练 / 推理"升级到"运营企业级 AI 训推平台"。

## 一、集群规模 + 拓扑设计

### 1.1 规模决策

```
开发 / POC (< 8 GPU):
  单机 8 H100 / 8 Ascend 910B
  不需要 IB (NVLink 足够)
  本地 NVMe + 单节点 K8s (kind/minikube)

中型 (16-128 GPU):
  2-16 节点 × 8 GPU
  IB / RoCE 400G
  K8s 集群 + Volcano + GPU Operator
  JuiceFS / Lustre 共享存储

大型 (256-1024 GPU):
  32-128 节点 × 8 GPU
  IB NDR 400G + SHARP
  K8s + Volcano + Kueue + Karmada (跨集群)
  Lustre / OceanStor 高带宽
  多 Pod 拓扑 (Rail-optimized)

超大 (1024+ GPU):
  Megatron 3D 并行 + MoE
  专用网络平面 (训练 IB + 业务以太分离)
  自动容错 (DLRover)
  专业 AI 平台 (ModelArts / PAI / 自研)
```

### 1.2 网络拓扑

```
单 Pod (8 H100):
  NVSwitch 全互联 (内 600 GB/s)

跨 Pod (32-1024 H100):
  Rail-optimized:
    每 H100 → 1 IB NIC (NDR 400G)
    8 H100 → 8 IB → IB Spine 交换机
    Pod 间 → IB Super-spine
    
  Fat-tree 拓扑:
    Leaf / Spine / Super-spine
    无阻塞 / 多路径 ECMP

跨 Region:
  IB / RoCE 跨机房
  Federation (Karmada)
  
存储网络:
  训练存储独立 IB / 400 Gbps
  分离训练数据 / 模型 ckpt
```

### 1.3 拓扑感知调度

```yaml
# Volcano + topology-aware
apiVersion: scheduling.volcano.sh/v1beta1
kind: Queue
metadata: { name: llm-train }
spec:
  weight: 4
  reclaimable: false

---
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
spec:
  schedulerName: volcano
  queue: llm-train
  minAvailable: 16
  plugins:
    ssh: []
    env: []
    svc: []
  policies:
    - { event: PodEvicted, action: RestartJob }
  tasks:
    - replicas: 16
      template:
        metadata:
          annotations:
            volcano.sh/task-topology-policy: pack-host    # 同 host 优先
        spec:
          affinity:
            podAffinity:
              requiredDuringSchedulingIgnoredDuringExecution:
                - labelSelector: { matchLabels: { job: pretrain } }
                  topologyKey: kubernetes.io/hostname
```

## 二、GPU/NPU 资源规划

### 2.1 容量基线

```
推理 SLA (P95):
  small (7B):   1 卡 < 50 ms TTFT, > 50 tok/s
  medium (32B): 4 卡 < 100 ms TTFT, > 30 tok/s
  large (72B):  4 卡 < 200 ms TTFT, > 20 tok/s
  XL (DeepSeek V3): 8 卡 < 300 ms TTFT

训练规模 (token / day):
  7B SFT (LoRA): 单机 8 H100, ~5B tok/day
  70B 全参微调: 16-32 H100, ~1B tok/day
  70B 预训练: 128+ H100, ~10B tok/day
  万亿参数: 千卡 H100

显存预估:
  推理: param × 2 (BF16) 或 × 1 (FP8/Int8)
  训练: param × 16-20 (BF16 + Adam) → ZeRO-3 / FSDP
  KV cache: 2 × batch × seqlen × hidden × layers × 2 bytes
```

### 2.2 节点选型

```
Nvidia (单机 8 H100):
  8x H100 SXM5 80GB / 141GB (H200)
  Intel Xeon Platinum 8480C (56 core × 2)
  2-4 TB DDR5
  30-60 TB NVMe SSD (本地 cache)
  8x IB NDR 400G
  PCIe Gen5 ⭐

华为 Ascend (单机 8 910B):
  8x Ascend 910B (64GB HBM)
  鲲鹏 920 ⭐
  1-2 TB DDR4
  NVMe / OceanStor
  RoCE v2 / 100-400G
  
价格参考 (2026):
  8x H100: $300k+ (二手 $150k+)
  8x H200: $400k+
  8x Ascend 910B: ¥1.5-2M
  8x B200: $400-500k
```

### 2.3 GPU 池化 + 共享

```
共享场景 (开发 / 推理):
  MIG (H100/A100):  硬隔离
  MPS:              软共享
  HAMi (国产) ⭐:   显存 + 算力切片
  
独占场景 (训练):
  整卡分配
  NVLink 内通信
  IB 跨节点
```

## 三、训推平台架构

### 3.1 标准架构

```
应用层:
  RAG 系统 / Agent / 业务 API
  AI 助手 / 客服 / 内容生成

LLM 网关层 (LiteLLM / Higress AI):
  - 多模型路由
  - 限流 / 计费
  - 鉴权 / 审核

推理层 (KServe / Triton / llm-d):
  - vLLM / SGLang 后端
  - 自动扩缩 (KEDA + GPU 指标)
  - 模型版本 / Canary
  - Multi-LoRA

训练层 (Volcano + Megatron):
  - 多租户队列
  - Gang Scheduling
  - 容错 (DLRover)
  - 实验追踪 (W&B / MLflow)

数据层:
  - JuiceFS / Lustre 共享存储
  - Alluxio 缓存
  - 数据集 + Tokenizer
  - 模型 Registry (Harbor LFS / MLflow)

基础设施层:
  - K8s + GPU Operator + Volcano + Kueue
  - IB / RoCE + NCCL
  - Prometheus + DCGM Exporter
  - 监控告警 + 日志
```

### 3.2 关键决策

```
推理服务:
  小规模 (< 10 model):     vLLM 直接部署
  中规模 (10-50):          KServe + vLLM
  大规模 (50+):            llm-d (CNCF) ⭐
  Nvidia 极致:             Triton + TRT-LLM
  国产 Ascend:             MindIE / LMDeploy + KServe

训练 / 微调:
  实验 + LoRA:             单机 + LLaMA-Factory
  生产 SFT:                Volcano + LLaMA-Factory + DPO
  大模型预训练:            Megatron + Volcano + DLRover

数据 + RAG:
  PoC / 单库:              pgvector
  生产 / 多库:             Milvus / Weaviate
  企业级:                  专业向量库 + Reranker

Agent:
  简单:                    LangChain
  生产:                    LangGraph ⭐
  多 Agent:                AutoGen / CrewAI

LLM 网关:
  统一 API:                LiteLLM ⭐
  国产:                    OneAPI / Higress AI
```

## 四、镜像 / 模型 / 数据治理

### 4.1 镜像基线

```
基础镜像:
  pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime
  nvcr.io/nvidia/pytorch:24.10-py3
  nvcr.io/nvidia/tritonserver:24.10-py3
  vllm/vllm-openai:v0.6.0
  
国产:
  ascendhub.huawei.com/public-ascendhub/cann:8.0
  ascendhub.huawei.com/public-ascendhub/mindspore:2.3

镜像规则:
☐ harbor.example.com 私仓
☐ 不可变 tag (commit-sha)
☐ 分级 (training / inference / data-prep)
☐ Trivy 扫描 (无 Critical CVE)
☐ Cosign 签名 + Provenance
☐ Stargz 懒加载 (减启动延迟)
☐ p2p 加速 (Dragonfly / Spegel)
☐ 大模型 base + 模型 PVC 分离 (不打入镜像)
```

### 4.2 模型治理

```
存储:
  - Harbor + LFS / OCI Artifact ⭐
  - MLflow Model Registry
  - S3 / OSS 对象存储
  - JuiceFS / Lustre (PVC ReadWriteMany)

模型卡 (必填):
☐ 模型名 + 版本 + license
☐ 训练数据来源 + 规模
☐ 训练超参 + 框架
☐ 评测结果 (MMLU / HumanEval / 业务指标)
☐ 已知偏见 / 限制
☐ Owner / Steward
☐ 安全审核 + 备案号

版本管理:
  v1.0.0   语义版本
  prod / canary / staging   阶段
  
权限:
  - 只读 (业务团队)
  - 读写 (训练团队)
  - Admin (平台团队)
  - 国密 / 等保 模型加密
```

### 4.3 数据治理

```
数据集:
  - HF Datasets / 自建
  - Iceberg / Paimon (PB 级)
  - 去重 + 质量过滤 + 平衡
  
版本:
  - DVC ⭐ / lakeFS / Pachyderm
  - Git LFS (小数据)
  
合规:
  ☐ 来源合法 (爬虫 robots / 授权)
  ☐ PII 脱敏
  ☐ 版权检查
  ☐ 出境评估 (跨境)
  ☐ 模型备案附数据描述
```

## 五、MLOps 流水线

### 5.1 GitOps MLOps

```
git push (model code)
  → CI lint + test (pytest)
  → 训练 Job (Volcano + Megatron + LLaMA-Factory)
  → 评测 (lm-eval-harness + 业务集)
  → 模型注册 (MLflow + Harbor LFS)
  → 模型卡审核
  → KServe Canary (5%)
  → AB 测试 (4h-24h)
  → 全量上线 (ArgoCD Rollouts)
  → 监控 (业务指标 + GPU)
  → 回滚 (一键)

工具栈:
  GitLab CI / Argo Workflows / Tekton
  Volcano + Megatron
  MLflow + Weights & Biases
  ArgoCD + KServe
  Prometheus + Grafana + Loki
```

### 5.2 评测 + AB

```
能力评测:
  - lm-eval-harness ⭐ (MMLU / GSM8K / HumanEval)
  - OpenCompass (国产, 多任务)
  - C-Eval / CMMLU (中文)
  - LMSys Chatbot Arena
  
业务评测:
  - 业务任务集 (1000+ examples)
  - LLM-as-Judge (GPT-4 / Qwen-Max 评分)
  - 人工评测 (核心)
  - A/B (灰度 5% → 50% → 100%)

监控:
  - 业务指标 (回答质量评分)
  - 用户反馈 (👍👎)
  - 延迟 / 成本 / 错误率
  - 内容安全率
```

## 六、监控 / 告警 / SLO

### 6.1 关键指标

```
GPU 层:
  GPU 利用率 (utilization.gpu) > 70% (训练)
  显存占用 (memory.used) < 95%
  GPU 温度 < 85°C
  GPU 功耗 < 设计值
  NVLink / IB / RoCE 带宽

推理层:
  TTFT (Time To First Token) P95 < SLO
  TPOT (Time Per Output Token) P95 < SLO
  Throughput (tokens/s)
  Queue length / waiting requests
  KV cache 占用率
  Prefix cache 命中率
  Speculative decode 接受率
  
训练层:
  Loss / LR / Grad norm
  Step time / samples per second
  NCCL AllReduce 时间
  Checkpoint 保存时间

业务层:
  请求 RPS / 错误率
  内容审核拦截率
  用户满意度

成本:
  每千 tokens 成本
  GPU 利用率 → FinOps
```

### 6.2 SLO 模板

```yaml
# llm-inference-slo.yaml
apiVersion: sloth.slok.dev/v1
kind: PrometheusServiceLevel
metadata: { name: llm-qwen-72b-slo, namespace: monitoring }
spec:
  service: llm-qwen-72b
  slos:
    - name: availability
      objective: 99.9
      sli:
        events:
          error_query: rate(http_requests_total{job="vllm", status=~"5.."}[5m])
          total_query: rate(http_requests_total{job="vllm"}[5m])
      alerting:
        page_alert: { labels: { severity: page } }
    
    - name: latency-p95
      objective: 95
      sli:
        events:
          error_query: |
            histogram_quantile(0.95, rate(vllm_e2e_request_latency_seconds_bucket[5m])) > 5
          total_query: rate(vllm_requests_total[5m]) > 0
```

### 6.3 告警 Top 10

```
☐ GPU Xid 错误 (硬件)
☐ GPU 温度 > 90°C
☐ 显存 > 95% (推理 OOM 风险)
☐ vLLM /health 失败 > 1min
☐ TTFT P99 > 2 × SLO (5min)
☐ 训练 loss NaN
☐ NCCL hang (> 10min 无 progress)
☐ 节点 unschedulable (NoExecute taint)
☐ PVC 满 (> 90%)
☐ 模型加载失败 (镜像 / S3)
```

## 七、多租户隔离

```
Namespace + Queue:
  - team-a / team-b namespace
  - Volcano queue per team
  - Kueue ClusterQueue + LocalQueue + Cohort

资源配额:
  - ResourceQuota (gpu/memory/cpu)
  - LimitRange (per pod)
  - 借用 (Kueue Cohort)

网络隔离:
  - NetworkPolicy (default-deny + 团队子)
  - Cilium ClusterMesh

存储隔离:
  - PVC per namespace
  - JuiceFS 子目录 + 限流

模型隔离:
  - Harbor 项目级
  - MLflow workspace
  - 模型 RBAC

LLM 网关:
  - LiteLLM team key
  - Token 配额 + 限速
```

## 八、容量 + 成本（FinOps GPU）

```
成本组成:
  GPU 硬件 (60-70%)
  服务器 + 网络 (15%)
  电费 + 制冷 (10-15%)
  存储 + 软件 (5-10%)

GPU 利用率优化:
☐ MIG / MPS / HAMi 共享 (推理)
☐ Spot / 抢占 (训练实验, 非生产)
☐ Speculative + Prefix cache (推理吞吐 ↑)
☐ FP8 / Int4 量化 (容量 ↑ 2-4x)
☐ Multi-LoRA (单 GPU 多模型)
☐ 训练 / 推理峰谷错峰
☐ 闲置 GPU 自动回收 (Idle Detection)
☐ Volcano 抢占 (低优作业被高优抢)

成本归属:
☐ label team / project / cost-center
☐ Kubecost / OpenCost GPU
☐ LiteLLM token 计费
☐ 月度成本报告

KPI:
☐ GPU 利用率 > 70% (训练) / > 60% (推理)
☐ 单 token 成本 (¥/1k tok)
☐ TCO 月度趋势
```

## 九、容灾备份

```
模型:
  ☐ Harbor LFS replication (跨 region)
  ☐ S3 cross-region replication
  ☐ 关键模型本地副本 (3 副本)

数据集:
  ☐ S3 / OSS 多 region
  ☐ Iceberg / Paimon snapshot

Checkpoint:
  ☐ Lustre / JuiceFS + S3 异步备份
  ☐ 每个 step 增量
  ☐ 保留最近 N 个 + 关键节点

服务:
  ☐ vLLM 多副本跨 AZ
  ☐ LiteLLM 网关 Active-Active
  ☐ 备模型 (主模型 down 自动切)

灾备演练:
  ☐ 季度演练 (杀 1 GPU node / pod)
  ☐ 模型回滚演练 (Canary 失败)
  ☐ 训练 resume 演练 (杀 1 worker)
```

## 十、升级 SOP

```
模型升级 (新版本):
  1. 离线评测 (lm-eval + 业务集)
  2. 模型卡审核 + 备案
  3. Canary 5% (4h-24h)
  4. AB 50% (24h-72h)
  5. 全量
  6. 旧版保留 30d

平台升级 (vLLM / KServe):
  1. 测试环境验证
  2. 准生产 24h
  3. 灰度 (1 GPU node)
  4. 全量 (滚动)
  5. 回滚预案

GPU Driver / CUDA 升级:
  1. 测试节点验证
  2. 维护窗口 (周末)
  3. 滚动 cordon + drain + upgrade
  4. DCGM 验证
  5. 业务回归

K8s 升级 (主):
  - 见 07_Kubernetes
  - 注意 GPU Operator 兼容性
```

## 十一、Incident SOP

```
P0 (业务停):
  - 主推理服务 down
  - 全量错误率 > 50%
  RTO: 15 min

P1 (业务降级):
  - 单一模型 down
  - 错误率 5-50%
  RTO: 1h

P2 (体验下降):
  - 延迟 > 2× SLO
  - 错误率 < 5%
  RTO: 4h

常见 SOP:
  vLLM OOM:
    1. 减少 max-num-seqs
    2. 量化 (FP8 / Int4)
    3. 减 max-model-len
    4. 加 GPU

  GPU Xid 错误:
    1. cordon 节点
    2. 重启 GPU / 节点
    3. DCGM 健康检查
    4. 持续故障 → 报修
  
  NCCL Hang:
    1. 看 NCCL_DEBUG=INFO 日志
    2. 检查 IB / RoCE 状态 (ibstat)
    3. 重启 Job (DLRover 自动)
    4. 拓扑问题 → 调度切换
  
  模型加载失败:
    1. 检查 Harbor / S3 可达
    2. PVC / 磁盘 quota
    3. 镜像版本 / 模型路径
  
  推理高延迟:
    1. 看 KV cache / 等待队列
    2. 扩 replicas (KEDA / HPA)
    3. 检查上游 (LLM 网关 / Embedding)
```

## 十二、典型生产架构

### 12.1 互联网中型 AI 公司

```
集群:        2 套 K8s 1.31 (训练 + 推理)
硬件:        训练 64x H100 + 推理 32x H100 + IB NDR
平台:        KServe + vLLM + Volcano
模型:        Qwen 2.5 + DeepSeek V3 + 业务微调
网关:        LiteLLM (统一 API + 计费)
RAG:        Milvus + LangChain + bge
Agent:      LangGraph
监控:        kube-prometheus + DCGM + vLLM metrics
存储:        JuiceFS + S3
注册:        MLflow + Harbor LFS
合规:        国密 + 内容审核 + 备案
```

### 12.2 央企 / 政府 AI 平台

```
硬件:        华为 Ascend 910B/910C ⭐ (千卡)
平台:        华为 ModelArts / 自研 + Volcano
模型:        Qwen / GLM / 智谱 / 自研 (Ascend 适配)
推理:        MindIE + LMDeploy + KServe
训练:        MindFormers / Megatron + Ascend Adapter
网关:        Higress AI + 国密 SM2 TLS
RAG:        Milvus + bge-large-zh + Reranker
监控:        npu-smi + Ascend Exporter + Prometheus
合规:        等保三级 + 国密 + 模型备案 ⭐
信创:        鲲鹏 + openEuler + 飞腾备选
```

### 12.3 AI Lab / 研究院

```
硬件:        H100 / B100 + IB + Lustre
训练:        Megatron + NeMo + DeepSpeed + DLRover
预训练:      自研数据 + Tokenizer + 千卡
Post-train: TRL DPO/GRPO + 自评测
推理:        vLLM + SGLang + 多模态
评测:        OpenCompass + lm-eval + Chatbot Arena
开源:        Hugging Face + ModelScope 双发布
```

## 十三、Checklist（最佳实践）

```
集群:
☐ 规模决策 (8 / 32-128 / 256+ / 千卡)
☐ 拓扑设计 (NVLink + IB + Rail)
☐ 网络分离 (训练 IB + 业务以太)

资源:
☐ 容量基线 (推理 / 训练)
☐ 节点选型 (H100/H200/Ascend)
☐ 共享 (MIG/MPS/HAMi)

平台:
☐ K8s + GPU Operator + Volcano
☐ Kueue 配额借用
☐ KServe + vLLM / llm-d (推理)
☐ Volcano + Megatron / LLaMA-Factory (训练)
☐ LiteLLM / Higress AI 网关

治理:
☐ 镜像 (Harbor + Stargz + Cosign + Trivy)
☐ 模型 (Harbor LFS / MLflow + 模型卡)
☐ 数据 (DVC + 合规)
☐ MLOps GitOps (ArgoCD + Workflow)

监控:
☐ DCGM Exporter + Prometheus
☐ vLLM / KServe / Triton metrics
☐ SLO + Sloth + 告警
☐ Loki / SIEM 日志

多租户:
☐ Namespace + Queue + ResourceQuota
☐ NetworkPolicy + Cilium
☐ Harbor 项目 / MLflow workspace
☐ LiteLLM team key

FinOps:
☐ MIG/MPS/HAMi 共享
☐ 量化 (FP8/AWQ)
☐ Multi-LoRA
☐ Spot (实验)
☐ Kubecost / OpenCost
☐ token 计费 (LiteLLM)

容灾:
☐ 模型多 region
☐ Checkpoint S3 备份
☐ 多副本跨 AZ
☐ 季度演练

升级:
☐ Canary 5% → 50% → 全量
☐ 平台滚动 + 回滚
☐ GPU Driver 维护窗口

应急:
☐ P0-P2 分级 + RTO
☐ vLLM OOM / GPU Xid / NCCL Hang runbook
☐ 模型回滚 (一键)

国产化:
☐ Ascend 千卡集群 (政企必)
☐ MindIE + LMDeploy 推理
☐ MindFormers 训练
☐ Higress AI 网关
☐ 国密 + 等保三级 + 备案

合规:
☐ 模型备案 (网信办)
☐ 数据合规 (个保法)
☐ 内容审核 (国产 + NeMo)
☐ 日志 180d
☐ 国密 TLS

团队:
☐ 平台工程师 (K8s + GPU)
☐ ML Engineer (训练 + 推理)
☐ MLOps / DevOps
☐ 算法 / 模型工程师
☐ 安全 / 合规
☐ on-call 7×24
```

## 十四、推荐栈（最佳实践）

```
硬件:        Nvidia H100/H200/B100 + IB NDR + Lustre
            国产: Ascend 910B/910C + RoCE + OceanStor
K8s:         1.31+ + GPU Operator + Volcano + Kueue + Karmada
            国产: Ascend Operator
推理:        vLLM ⭐ + KServe ⭐ + llm-d (大规模) + SGLang
            国产: MindIE / LMDeploy
训练:        Megatron-LM ⭐ + DeepSpeed + DLRover + LLaMA-Factory
            国产: MindFormers
Post-train: TRL + OpenRLHF + LLaMA-Factory (DPO/GRPO)
量化:        AWQ / GPTQ / FP8
监控:        DCGM Exporter + Prometheus + Grafana + vLLM/KServe metrics
SLO:        Sloth + Pyrra
日志:        Loki / Elasticsearch + Fluent Bit
模型:        MLflow + Harbor LFS + W&B
数据:        DVC + Iceberg/Paimon + JuiceFS
RAG:        LangChain / LlamaIndex + Milvus + bge + Reranker
Agent:      LangGraph + AutoGen / CrewAI
LLM 网关:   LiteLLM ⭐ + Higress AI ⭐ (国产)
内容审核:   NeMo Guardrails + 国产 (阿里绿网/网易易盾)
GitOps:     ArgoCD + Argo Workflows / Tekton
FinOps:     Kubecost + OpenCost + LiteLLM token 计费
合规:        国密 (Tongsuo) + 等保三级 + 模型备案 + 审计 180d
信创:        鲲鹏 / 飞腾 + openEuler + 麒麟
平台:        Backstage IDP + 自研门户
```

> 📖 **核心判断**：AI 基础设施最佳实践 = **集群规模决策 + GPU 资源规划 + 训推平台分层 + 镜像/模型/数据治理 + MLOps GitOps + SLO 监控 + 多租户 + FinOps GPU + 容灾备份 + 升级 SOP + 国产化路径 + 模型生命周期 + 内容审核 + 备案 + Incident SOP + 团队组织**。能给企业画"Ascend/H100 集群 + Volcano/Kueue + Megatron 训练 + vLLM/MindIE/KServe 推理 + LiteLLM/Higress 网关 + RAG + Agent + MLflow + 监控 + 国密 + 模型备案 + Backstage IDP"完整 AI 训推平台，并能 Q1 演练 + DORA-like 度量 + 多租户 + FinOps + 信创路径，就具备 AI 平台负责人能力。
