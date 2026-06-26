# 推理服务架构

> 单机 vLLM 起步，**生产架构需要 8 层**：路由 → 鉴权 → 限流 → 负载均衡 → 推理副本 → KV Cache 共享 → 模型仓库 → 监控。**llm-d / vLLM Production Stack / AIBrix** 是 2025 推理生产架构事实标准。**PD 分离 + Prefix Cache 共享** 是新一代核心。

## 一、推理服务架构演进

```
v1 单机 vLLM
  client → vLLM (单 Pod) → GPU

v2 多副本 + LB
  client → LB → [vLLM A, vLLM B, ...] → GPU

v3 多模型 + 路由
  client → API Gateway → Router → [70B, 7B, embed, ...]

v4 PD 分离 + Cache 共享 (2024+)
  client → Router → Prefill Pool (H100)
                  → Decode Pool (H200)
                  ↔ Shared KV Cache (RDMA/Mooncake)

v5 全栈分布式 (llm-d / 2025)
  + 智能路由（prefix-aware / load-aware）
  + 多级 cache（GPU HBM → CPU RAM → SSD）
  + 模型版本管理 + 灰度
  + 跨集群多 region
  + 自动扩缩 + Spot 抢占
```

## 二、PD 分离（Prefill/Decode Disaggregation）

### 2.1 为什么要 PD 分离

```
Prefill 阶段:
  - Compute-bound
  - 一次性算完 N 个 prompt token
  - 用算力强的卡 (H100, MI300X)
  - 时间 ~ O(N²) (attention)

Decode 阶段:
  - Memory-bound
  - 逐 token 生成
  - 用带宽高的卡 (H200, MI300X)
  - 单 token ~ 几十 ms

混在一起的问题:
  - Prefill 长 prompt 会阻塞 decode
  - 两者资源需求不同，GPU 利用率低
  - SLA TTFT / TPOT 难同时优化
```

### 2.2 PD 分离架构

```
                  Router
                   │
        ┌──────────┴───────────┐
        ▼                      ▼
    Prefill Pool          Decode Pool
    [H100 × N]            [H200 × M]
    高算力                 高带宽
        │                      │
        └────► KV Cache ◄──────┘
              (RDMA transfer
              or shared memory)

流程:
  1. Router 收请求
  2. Prefill 节点算完 prompt → KV Cache
  3. KV Cache 通过 RDMA 传到 Decode 节点 (微秒级)
  4. Decode 节点边生成边返回流式 token
```

### 2.3 主流实现

```
Mooncake (Kimi/月之暗面 开源)
  - 业界首个开源 PD 分离系统
  - KVCache 中心化池 + Cache-aware Routing
  - RDMA / NVLink Networking
  - 论文 FAST '25
  - https://github.com/kvcache-ai/Mooncake

DistServe (UCSD)
  - 学术派
  - 论文 OSDI '24

vLLM Disaggregated Prefill (v0.6+)
  - 内置 PD 模式
  - --kv-transfer-config

SGLang PD (v0.4+)
  - 内置 RDMA / NCCL 传输

NVIDIA Dynamo (2025)
  - NVIDIA 官方分布式推理
  - 替代 TRT-LLM Triton 经典栈
  - 集成 KV-aware routing
```

### 2.4 vLLM PD 分离启动

```bash
# Prefill 节点
vllm serve meta-llama/Meta-Llama-3-70B-Instruct \
  --port 8100 \
  --kv-transfer-config '{"kv_connector":"PyNcclConnector","kv_role":"kv_producer","kv_rank":0,"kv_parallel_size":2}' \
  -tp 2

# Decode 节点
vllm serve meta-llama/Meta-Llama-3-70B-Instruct \
  --port 8200 \
  --kv-transfer-config '{"kv_connector":"PyNcclConnector","kv_role":"kv_consumer","kv_rank":1,"kv_parallel_size":2}' \
  -tp 2

# Router (vLLM 自带 / 自研)
# 转 prompt → prefill → 收 KV → 转 decode
```

## 三、KV Cache 共享与多级缓存

### 3.1 痛点

```
单机 prefix cache → 仅在本副本命中
多副本架构 → 同 prefix 在不同副本被重复计算
长 system prompt + RAG → 大量浪费
```

### 3.2 多级缓存设计

```
L1 GPU HBM Cache       ~80 GB    ns 级
L2 CPU RAM Cache        ~1 TB     us 级 (通过 PCIe)
L3 NVMe Local SSD       ~10 TB    100us-ms 级
L4 Distributed Cache    >100 TB   ms 级 (RDMA)

策略:
  热 prefix (system / 常用) 留 L1
  温 prefix (一次会话) 落 L2/L3
  冷 prefix 直接重算

vLLM v1 / SGLang 都支持多级
```

### 3.3 LMCache（开源 KV 共享）

```bash
pip install lmcache

# 启动 LMCache server
lmcache serve --port 8888 --backend redis://...

# vLLM 集成
export LMCACHE_USE_EXPERIMENTAL_FEATURES=1
vllm serve meta-llama/Meta-Llama-3-8B \
  --kv-transfer-config '{
    "kv_connector": "LMCacheConnector",
    "kv_role": "kv_both",
    "lmcache_url": "lmcache://lmcache-server:8888"
  }'

# 效果:
# - Prefix 跨副本共享
# - RAG 场景 TTFT 降 60-90%
# - Agent 场景多轮加速
```

### 3.4 Mooncake 部署

```bash
# Clone
git clone https://github.com/kvcache-ai/Mooncake

# Mooncake Store (KV Cache Pool)
docker run -d --name mooncake-store \
  -p 50051:50051 \
  mooncake/store:latest \
  --hbm-size 40 \                       # GB
  --dram-size 200 \
  --ssd-size 1000 \
  --backend rdma

# vLLM with Mooncake
vllm serve model \
  --kv-transfer-config '{
    "kv_connector": "MooncakeConnector",
    "kv_role": "kv_consumer",
    "mooncake_url": "mooncake://store:50051"
  }'
```

## 四、智能路由

### 4.1 路由策略

```
Round-Robin (RR)         无脑轮询
  ❌ 无 cache 感知 / 无 load 感知

Least Connections (LC)   最少连接
  ❌ 不能区分长短请求

Hash by SessionID         会话粘性
  ✅ 同会话同副本（cache 友好）
  ❌ 副本宕机丢 cache

Prefix Hash               prefix 一致性哈希
  ✅ 同 prefix 路由同副本
  ✅ Cache 友好
  ⭐ 推荐

Load-Aware                负载感知
  - Pending Queue Length
  - GPU Util
  - KV Cache 占用
  - TTFT 预测

Cost-Aware                成本感知
  - 简单 query → 小模型 (7B)
  - 复杂 query → 大模型 (70B)
  - LLM Router / RouteLLM

Cache-Aware (最优)
  + Prefix Hash
  + Load-Aware
  + 跨副本 KV 转移
```

### 4.2 LiteLLM Router

```python
from litellm import Router

model_list = [
    {
        "model_name": "llama-70b",
        "litellm_params": {
            "model": "openai/llama-3-70b",
            "api_base": "http://vllm-1:8000/v1",
            "api_key": "anything"
        },
        "tpm": 100000,
    },
    {
        "model_name": "llama-70b",
        "litellm_params": {
            "model": "openai/llama-3-70b",
            "api_base": "http://vllm-2:8000/v1",
            "api_key": "anything"
        },
        "tpm": 100000,
    }
]

router = Router(
    model_list=model_list,
    routing_strategy="least-busy",          # or simple-shuffle / usage-based-routing-v2 / latency-based-routing
    num_retries=3,
    timeout=30,
    fallbacks=[{"llama-70b": ["llama-8b"]}],
    cache_responses=True,
    redis_host="redis", redis_port=6379,
)

response = router.completion(
    model="llama-70b",
    messages=[{"role": "user", "content": "hi"}]
)
```

### 4.3 LiteLLM Proxy（生产推荐）

```yaml
# config.yaml
model_list:
  - model_name: llama-70b
    litellm_params:
      model: openai/Meta-Llama-3-70B-Instruct
      api_base: http://vllm-1:8000/v1
      api_key: dummy
  
  - model_name: qwen-72b
    litellm_params:
      model: openai/Qwen2.5-72B-Instruct
      api_base: http://sglang-1:30000/v1

  - model_name: gpt-4o
    litellm_params:
      model: gpt-4o
      api_key: os.environ/OPENAI_API_KEY

router_settings:
  routing_strategy: usage-based-routing-v2
  redis_host: redis
  
general_settings:
  master_key: sk-xxx
  database_url: postgres://...           # 用户管理
  
litellm_settings:
  set_verbose: false
  callbacks: [prometheus, langfuse]      # 监控
```

```bash
litellm --config config.yaml --port 4000

# 客户端用统一 OpenAI 协议
curl http://litellm:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -d '{"model": "llama-70b", "messages": [...]}'
```

### 4.4 KServe + ModelMesh

```yaml
# K8s 原生模型服务
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: llama3-70b }
spec:
  predictor:
    minReplicas: 2
    maxReplicas: 10
    scaleTarget: 80                       # GPU util
    containers:
      - image: vllm/vllm-openai:latest
        args:
          - --model=meta-llama/Meta-Llama-3-70B-Instruct
          - -tp=2
        resources:
          limits: { nvidia.com/gpu: 2 }
```

## 五、负载均衡

### 5.1 L7 网关选型

```
Nginx              简单 / 静态配置
HAProxy            高性能 / 复杂规则
Envoy              动态配置 / 服务网格
APISIX             插件丰富 / 国产
Traefik            K8s 原生
LiteLLM Proxy ⭐    LLM 专用 / OpenAI 协议
Gateway API        K8s 标准
Istio + Envoy      服务网格内
```

### 5.2 Nginx LLM 配置

```nginx
upstream vllm_pool {
    least_conn;                                # 最少连接
    # 或 hash $http_x_session_id consistent;   # 会话粘性
    
    server vllm-1:8000 max_fails=2 fail_timeout=30s;
    server vllm-2:8000 max_fails=2 fail_timeout=30s;
    server vllm-3:8000 backup;                 # 备份节点
    
    keepalive 32;                              # 连接复用
}

server {
    listen 80;
    
    location /v1/ {
        proxy_pass http://vllm_pool;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        
        # SSE 流式必加
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        chunked_transfer_encoding on;
        
        # WebSocket (可选)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /health {
        access_log off;
        proxy_pass http://vllm_pool/health;
    }
}
```

### 5.3 Envoy Rate Limit + Retry

```yaml
# rate limiting filter
http_filters:
  - name: envoy.filters.http.ratelimit
    typed_config:
      domain: llm-api
      rate_limit_service:
        grpc_service:
          envoy_grpc:
            cluster_name: rate-limit-cluster

route_config:
  virtual_hosts:
    - name: llm
      domains: ["*"]
      routes:
        - match: { prefix: "/v1/" }
          route:
            cluster: vllm_cluster
            timeout: 600s                  # 流式长连接
            retry_policy:
              retry_on: "gateway-error,retriable-status-codes"
              num_retries: 2
              retriable_status_codes: [503]
            rate_limits:
              - actions:
                  - request_headers:
                      header_name: "x-user-id"
                      descriptor_key: "user_id"
```

## 六、自动扩缩

### 6.1 HPA 基础

```yaml
# 按 CPU/GPU
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: vllm-hpa }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 70 }
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300       # 5min 防抖
```

### 6.2 KEDA（按业务指标）

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: vllm-scaler }
spec:
  scaleTargetRef:
    name: vllm
  minReplicaCount: 2
  maxReplicaCount: 20
  cooldownPeriod: 300
  triggers:
    # 按 QPS（Prometheus）
    - type: prometheus
      metadata:
        serverAddress: http://prom:9090
        threshold: '100'
        query: sum(rate(vllm:request_total[2m]))
    
    # 按 GPU pending queue（vLLM metric）
    - type: prometheus
      metadata:
        serverAddress: http://prom:9090
        threshold: '20'                     # 排队 20 个就扩
        query: avg(vllm:num_requests_waiting)
    
    # 按 TPOT P99
    - type: prometheus
      metadata:
        serverAddress: http://prom:9090
        threshold: '100'                    # 100ms
        query: histogram_quantile(0.99, vllm:time_per_output_token_seconds_bucket) * 1000
```

### 6.3 GPU Spot 弹性

```yaml
# 主用 Reserved + Spot 弹性峰值
nodeSelector:
  node.kubernetes.io/instance-type: gpu-spot
tolerations:
  - key: spot
    operator: Equal
    value: "true"
    effect: NoSchedule

# 应对中断
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh","-c","sleep 30"]  # 优雅退出 (drain)
```

## 七、模型仓库与版本管理

### 7.1 Model Registry

```
开源:
  - MLflow Model Registry
  - DVC (Data Version Control)
  - Hugging Face Hub (自建版本)
  - JFrog ML / 自研

商业:
  - Weights & Biases Model
  - Neptune.ai
  - Vertex AI Model Registry
  - SageMaker Model Registry
```

### 7.2 K8s 模型分发

```yaml
# 方案 A: PVC 共享存储
volumes:
  - name: models
    persistentVolumeClaim:
      claimName: models-pvc
# 优点：拉取一次，多副本共享
# 缺点：PVC 单点

# 方案 B: Init Container 预拉
initContainers:
  - name: model-pull
    image: huggingface/downloader
    command: ["hf", "download", "Meta-Llama-3-70B", "/models"]
    volumeMounts:
      - { name: models, mountPath: /models }
# 优点：节点本地
# 缺点：启动慢

# 方案 C: OCI 镜像内嵌
# 把模型打进镜像（小模型 OK，大模型不推荐）

# 方案 D: 节点 NVMe + DaemonSet 预热
# 大模型 + 多节点最佳实践
```

### 7.3 模型灰度发布

```yaml
# Istio VirtualService 流量切分
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata: { name: llama }
spec:
  hosts: [llama-api]
  http:
    - route:
        - destination: { host: llama-v1, port: { number: 8000 } }
          weight: 90
        - destination: { host: llama-v2, port: { number: 8000 } }
          weight: 10
```

```yaml
# 或 Argo Rollouts 渐进发布
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: vllm }
spec:
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: { duration: 10m }
        - setWeight: 30
        - pause: { duration: 30m }
        - setWeight: 100
      analysis:
        templates:
          - templateName: success-rate
          - templateName: latency-p99
```

## 八、多模型多租户

### 8.1 模型路由策略

```
策略 1: 按模型名（最简单）
  /v1/chat → model: llama-70b → vLLM-1
  /v1/chat → model: qwen-72b → SGLang-1

策略 2: 按 API key 配额
  user_A → 70B
  user_B → 8B（成本控制）

策略 3: 按任务路由（RouteLLM）
  简单 QA → 8B 模型
  复杂推理 → 70B
  代码 → coder model

策略 4: 按负载动态切换
  主模型超时 → 备用模型 fallback
```

### 8.2 LLM Router / RouteLLM

```bash
pip install routellm

from routellm.controller import Controller

client = Controller(
    routers=["mf"],                       # matrix factorization
    strong_model="gpt-4o",
    weak_model="ollama_chat/llama3"
)

response = client.chat.completions.create(
    model="router-mf-0.11593",            # threshold 0.11593
    messages=[...]
)
# 自动按 query 难度路由
# 简单 → weak / 难 → strong
# 70% 请求路由到 weak，成本降 80%
```

### 8.3 多租户隔离

```
方案 A: 物理隔离
  每租户独立 GPU 池 / Deployment
  成本高但最隔离

方案 B: 资源配额
  K8s ResourceQuota + LimitRange
  按租户分配 GPU 配额

方案 C: API Key 限流
  LiteLLM rate-limit per key
  QPS / TPM 配额

方案 D: MIG 切片
  H100 切成 7 个 MIG → 7 租户
  硬件级隔离 + 共享主机
```

## 九、推理网关全栈

### 9.1 推荐架构（2025）

```
                ┌──────────────────────┐
Internet ──→  WAF/CDN (Cloudflare/雷池)
                ↓
                ┌──────────────────────┐
                Ingress (Nginx/Envoy)
                ↓
                ┌──────────────────────┐
                Auth Gateway (Keycloak)
                ↓
                ┌──────────────────────┐
                LiteLLM Proxy (路由+限流+计费)
                ↓
                ┌──────────────────────┐
                Inference Pool
                ├── vLLM × N (主推理)
                ├── SGLang × M (备用 / agent)
                ├── Embedding × K (BGE)
                └── Reranker × L
                ↓
                ┌──────────────────────┐
                Shared KV Cache
                (LMCache / Mooncake)
                ↓
                ┌──────────────────────┐
                Model Registry
                (HF / MLflow / OCI)
```

### 9.2 完整组件清单

```
入口层:
  WAF:              Cloudflare / 雷池
  CDN:              Cloudflare / 阿里云
  DDoS:             高防 IP
  
网关层:
  Ingress:         Nginx Ingress / Envoy
  Auth:            Keycloak / Authelia
  Rate Limit:      Envoy / Kong / APISIX

路由层:
  LLM Router:     LiteLLM Proxy / OpenRouter
  Cost Routing:    RouteLLM
  
推理层:
  Engine:          vLLM / SGLang / TGI / TRT-LLM
  Embedding:       BGE / E5 / TEI (HF Text Embeddings Inference)
  Reranker:        BGE Reranker / Cohere
  
存储层:
  KV Cache:       LMCache / Mooncake
  Model:          PVC / OCI / S3 / Harbor
  
可观测:
  Metric:         Prometheus + vLLM/SGLang exporter
  Trace:          OpenTelemetry / Langfuse / Helicone
  Log:            Loki / ELK
  Dashboard:      Grafana

平台:
  K8s + GPU Operator + KEDA + Argo Rollouts
```

## 十、典型坑

| 坑 | 建议 |
|:---|:---|
| **单机性能 OK，多副本不线性** | 检查 cache 命中 / 路由策略 |
| **流式 SSE 卡顿** | Nginx `proxy_buffering off` |
| **HPA 扩缩抖动** | `stabilizationWindowSeconds` 调大 |
| **冷启动慢** | Init Container + 预热 + min replicas ≥ 2 |
| **GPU 利用率低** | 看 SM Util / KV Cache 利用率 |
| **PD 分离 KV 传输瓶颈** | RDMA / NVLink Networking |
| **多副本 cache 不共享** | LMCache / Mooncake |
| **TPOT 抖动** | 长 prompt 阻塞，开 chunked prefill |
| **路由没有 cache awareness** | LiteLLM least-busy 不够，需 Prefix Hash |
| **模型下载慢** | 镜像源 / 预拉 / 镜像内嵌 |
| **K8s 单 Pod 拉模型** | DaemonSet 节点预热 |
| **客户端长连接超时** | Nginx/Envoy timeout > vLLM 流式上限 |
| **多模型抢 GPU** | MIG / 显存配额 |
| **A/B 没指标决策** | Langfuse + 离线评测 |
| **没有 fallback** | LiteLLM fallbacks 配置 |

## 十一、最佳实践 Checklist

```
入口:
☐ WAF + Rate Limit
☐ TLS 1.3 + HTTP/2
☐ SSE 流式配置正确

路由:
☐ LiteLLM Proxy 统一入口
☐ Prefix-aware routing
☐ Cost-aware routing (大小模型)
☐ Health Check / Fallback

推理:
☐ vLLM / SGLang 主部署
☐ PD 分离（大规模）
☐ Multi-LoRA
☐ FP8 / INT4 量化

缓存:
☐ Prefix Caching 开
☐ KV Cache FP8
☐ LMCache / Mooncake 跨副本共享

扩缩:
☐ HPA + KEDA
☐ min replicas ≥ 2
☐ 冷启动 < 60s
☐ Spot 弹性

监控:
☐ TTFT / TPOT / Throughput
☐ KV Cache 利用率
☐ Queue Length
☐ 模型 quality (Langfuse)
☐ Cost per 1K tokens

发布:
☐ 灰度 / Canary
☐ 自动回滚
☐ A/B 评测
☐ 模型版本管理
```

## 十二、推荐栈（2025）

### 12.1 中小团队

```
- vLLM 主推理 (Docker / K8s)
- Nginx 负载均衡
- HPA CPU 触发
- Prometheus + Grafana
- Harbor 模型 / 镜像
```

### 12.2 中大企业

```
- vLLM + SGLang 双栈
- LiteLLM Proxy 统一入口
- K8s + GPU Operator + KEDA
- LMCache 跨副本 KV 共享
- Argo Rollouts 灰度
- Langfuse 业务级监控
- MIG 多租户切片
- 模型仓库 (HF + 内部 OCI)
```

### 12.3 大规模 / 大模型

```
- vLLM Disaggregated PD + Mooncake
- 跨 region 多活
- llm-d / NVIDIA Dynamo
- 自研路由层（业务 / cost / cache）
- 自动模型版本 + A/B
- HSM / 国密 / 合规审计
- 弹性 Spot + Reserved 混合
```

## 十三、学习路径

```
入门（1 月）:
  1. 单机 vLLM 部署
  2. K8s Deployment + Service
  3. Prometheus 接入
  4. HPA 配置

中级（3 月）:
  5. KEDA 业务指标扩缩
  6. LiteLLM Proxy 路由
  7. 多模型部署
  8. 灰度发布
  9. Multi-LoRA

高级（6 月+）:
  10. PD 分离 (vLLM / SGLang)
  11. LMCache / Mooncake 部署
  12. 跨集群多活
  13. 自研路由 + cache 策略
  14. SLA 极致优化 (TTFT P99 < 200ms)

专家:
  15. 自研推理网关
  16. 万卡推理集群运维
  17. 推理调度系统设计
```

## 十四、参考资料

```
官方:
  - vLLM Production Stack: https://github.com/vllm-project/production-stack
  - llm-d: https://github.com/llm-d/llm-d
  - LiteLLM: https://docs.litellm.ai/
  - KServe: https://kserve.github.io/
  - NVIDIA Dynamo: https://github.com/triton-inference-server/dynamo
  - Mooncake: https://github.com/kvcache-ai/Mooncake
  - LMCache: https://github.com/LMCache/LMCache

论文:
  - Mooncake (FAST '25)
  - DistServe (OSDI '24)
  - Splitwise (ISCA '24)
  - RouteLLM
  - SkyServe (UCB)

社区:
  - vLLM/SGLang Slack
  - LMSys
  - Anyscale Ray Serve
  - 国内: AI Infra 中文社区
```

> 📖 **核心判断**：2025 推理生产架构 = **LiteLLM Proxy（路由）+ vLLM/SGLang（推理）+ LMCache/Mooncake（缓存）+ KEDA（扩缩）+ Langfuse（监控）**。**PD 分离 + Prefix Cache 跨副本共享** 是新一代核心，能把成本降 30-50%。最容易翻车的不是性能，而是：**冷启动慢、流式 SSE 配错、HPA 扩缩抖、多副本不共享 cache**——把这四个工程问题解决，比框架内核优化收益大十倍。

