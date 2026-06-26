# 模型部署

> 模型部署 = **格式转换 + 量化 + 容器化 + 拉取分发 + 启动验证**。**HuggingFace + Safetensors + GGUF + AWQ** 是 2025 主流格式生态。**镜像内嵌 vs PVC vs 节点预热** 三方案各有适用场景。本章给完整部署落地工程。

## 一、模型格式

### 1.1 主流格式对比

| 格式 | 主导 | 用途 | 优点 | 缺点 |
|:---|:---|:---|:---|:---|
| **Safetensors** ⭐⭐⭐⭐⭐ | HuggingFace | 训练/推理通用 | 安全（无 pickle）、零拷贝、快加载 | - |
| **PyTorch (.bin/.pt)** | Meta | 训练 | 兼容性强 | pickle 漏洞 |
| **GGUF** ⭐⭐⭐⭐ | llama.cpp | CPU+GPU 量化推理 | 极致量化（Q2-Q8） | 仅 llama.cpp 生态 |
| **AWQ** | MIT | INT4 推理 | 精度最优 INT4 | 仅 vLLM/TGI 等支持 |
| **GPTQ** | - | INT4 推理 | 老牌 INT4 | 接近 AWQ |
| **ONNX** | 微软 | 跨框架 | 通用 / 跨平台 | LLM 支持差 |
| **TensorRT Engine** | NVIDIA | 极致优化 | 最快 | 不通用，需 build |
| **MLX** | Apple | Apple Silicon | M1/M2/M3 原生 | 仅 Mac |
| **CoreML** | Apple | iOS / Mac | 端侧 | 仅 Apple 平台 |
| **OpenVINO** | Intel | Intel 优化 | CPU / Intel GPU | 模型支持有限 |

### 1.2 Safetensors（首选）

```
为什么不用 .bin/.pt:
  - pickle 反序列化 → 远程代码执行漏洞
  - 加载慢（要解析 Python 对象）

Safetensors:
  - 纯二进制 + JSON header
  - 零拷贝（mmap）
  - 跨语言（Rust/Python/C++）
  - 加载快 5-10x
  - HF 2024+ 默认格式

# 转换
from safetensors.torch import save_file, load_file
state_dict = torch.load("model.bin")
save_file(state_dict, "model.safetensors")

# CLI
safetensors-cli check model.safetensors
```

### 1.3 GGUF 量化等级

```
Q2_K        2.5-bit   ~30% 损失   最小 / 最快
Q3_K_S/M/L  3-4 bit   10-20% 损失 
Q4_K_S      4.0 bit
Q4_K_M ⭐   4.5 bit   ~3% 损失    推荐
Q5_K_S/M    5-5.5 bit ~1% 损失
Q6_K        6.5 bit   ~0.5% 损失
Q8_0        8 bit     接近无损
F16/F32     原版

70B 模型：
  Q2_K     ~25 GB
  Q4_K_M   ~40 GB    一张 48GB GPU
  Q5_K_M   ~48 GB
  Q6_K     ~56 GB
  Q8_0     ~70 GB
  F16     ~140 GB
```

## 二、模型转换实战

### 2.1 PyTorch → Safetensors

```bash
# 用 transformers 直接 save
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("path/to/pytorch_model")
model.save_pretrained("./output", safe_serialization=True)
# 自动生成 model.safetensors

# 或 safetensors CLI
pip install safetensors
python -c "
from safetensors.torch import save_file
import torch
state = torch.load('pytorch_model.bin', map_location='cpu')
save_file(state, 'model.safetensors')
"
```

### 2.2 HF → GGUF

```bash
# llama.cpp 自带转换脚本
cd llama.cpp
python convert_hf_to_gguf.py \
  /path/to/Meta-Llama-3-70B-Instruct \
  --outfile llama3-70b-f16.gguf \
  --outtype f16

# 然后量化
./llama-quantize llama3-70b-f16.gguf llama3-70b-q4_k_m.gguf q4_k_m
./llama-quantize llama3-70b-f16.gguf llama3-70b-q5_k_m.gguf q5_k_m
./llama-quantize llama3-70b-f16.gguf llama3-70b-q8_0.gguf q8_0

# 上传 HF Hub
huggingface-cli upload your-user/llama3-70b-gguf \
  llama3-70b-q4_k_m.gguf llama3-70b-q4_k_m.gguf
```

### 2.3 HF → AWQ（INT4 推理）

```bash
pip install autoawq

# 量化脚本
python << 'EOF'
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

model_path = "meta-llama/Meta-Llama-3-70B-Instruct"
quant_path = "./llama3-70b-awq"

quant_config = {
    "zero_point": True,
    "q_group_size": 128,
    "w_bit": 4,
    "version": "GEMM"
}

# 加载
model = AutoAWQForCausalLM.from_pretrained(model_path, low_cpu_mem_usage=True)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# 量化（用 calibration data）
model.quantize(tokenizer, quant_config=quant_config)

# 保存
model.save_quantized(quant_path)
tokenizer.save_pretrained(quant_path)
EOF
```

### 2.4 HF → GPTQ

```bash
pip install auto-gptq

python << 'EOF'
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
from transformers import AutoTokenizer

model_path = "meta-llama/Meta-Llama-3-70B-Instruct"
quant_path = "./llama3-70b-gptq"

quantize_config = BaseQuantizeConfig(
    bits=4,
    group_size=128,
    desc_act=False,                       # actorder
)

model = AutoGPTQForCausalLM.from_pretrained(model_path, quantize_config)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# Calibration
import datasets
calib_data = datasets.load_dataset("wikitext", "wikitext-2-raw-v1", split="train").select(range(128))
examples = [
    tokenizer(d["text"], return_tensors="pt") for d in calib_data if d["text"].strip()
]

model.quantize(examples)
model.save_quantized(quant_path, use_safetensors=True)
tokenizer.save_pretrained(quant_path)
EOF
```

### 2.5 HF → TensorRT-LLM

```bash
# 见 02_推理框架 / 第六章
git clone https://github.com/NVIDIA/TensorRT-LLM
cd TensorRT-LLM

# Step 1: HF → TRT-LLM checkpoint
python examples/llama/convert_checkpoint.py \
  --model_dir Meta-Llama-3-70B-Instruct \
  --output_dir ./llama3_70b_ckpt \
  --dtype float16 \
  --tp_size 2

# Step 2: FP8 量化（可选）
python examples/quantization/quantize.py \
  --model_dir Meta-Llama-3-70B-Instruct \
  --output_dir ./llama3_70b_fp8_ckpt \
  --dtype float16 --qformat fp8 \
  --calib_size 512 --tp_size 2

# Step 3: Build engine
trtllm-build \
  --checkpoint_dir ./llama3_70b_fp8_ckpt \
  --output_dir ./llama3_70b_engine \
  --gemm_plugin fp8 \
  --max_batch_size 64 \
  --max_input_len 8192 --max_seq_len 16384
```

## 三、模型下载与镜像

### 3.1 HuggingFace 下载

```bash
# 安装新版 hf CLI (2024 推荐)
pip install -U huggingface_hub
hf auth login                            # token

# 下载完整仓库
hf download meta-llama/Meta-Llama-3-70B-Instruct \
  --local-dir /data/models/llama3-70b \
  --include "*.safetensors" "*.json" "tokenizer*"

# 单文件
hf download TheBloke/Llama-3-70B-GGUF \
  llama-3-70b-q4_k_m.gguf \
  --local-dir /data/models/gguf

# 并发加速 (max-workers)
hf download xxx --max-workers 16

# 断点续传内置
```

### 3.2 国内镜像加速

```bash
# HF 镜像（推荐）
export HF_ENDPOINT=https://hf-mirror.com
hf download xxx

# ModelScope（阿里）
pip install modelscope
modelscope download --model qwen/Qwen2.5-72B-Instruct \
  --local_dir /data/models/qwen2.5-72b

# OpenXLab（书生）
pip install openxlab
openxlab model get --model-repo OpenGVLab/InternVL2-Llama3-76B

# 镜像内嵌（CI 把模型打到镜像）
# 适合小模型 (< 30GB)
# Dockerfile:
FROM vllm/vllm-openai:latest
COPY ./models/Qwen2.5-7B /models/qwen
# vLLM 启动: --model /models/qwen
```

### 3.3 OCI 镜像规范（CNAI）

```
2025 趋势: 模型作为 OCI Artifact
  - 同 docker 仓库（Harbor / Registry）
  - 版本管理 / 签名 / 扫描
  - 标准化分发

工具:
  - oras (OCI Registry As Storage)
  - hf push 即将支持
  - KServe ModelMesh OCI

# 推
oras push registry.company.com/models/llama3-70b:v1 \
  --artifact-type application/vnd.ai.model.v1 \
  ./model.safetensors \
  ./config.json \
  ./tokenizer.json

# 拉
oras pull registry.company.com/models/llama3-70b:v1 -o /models/
```

## 四、K8s 模型分发方案

### 4.1 方案对比

| 方案 | 启动时间 | 适用 | 缺点 |
|:---|:---|:---|:---|
| **PVC 共享存储** | 中（首启拉取） | 多副本同模型 | PVC 单点 / 慢盘瓶颈 |
| **OCI 镜像内嵌** | 慢（镜像大） | 小模型 / 不变 | 镜像膨胀 |
| **Init Container 拉取** | 慢 | 每节点独立 | 重复下载 |
| **DaemonSet 预热** | 快 | 大模型 + 多节点 | 占用全节点存储 |
| **节点本地 NVMe** | 最快 | 生产推荐 | 需调度亲和 |
| **Fluid / JuiceFS 缓存** | 快 | 跨节点 | 复杂 |

### 4.2 PVC 共享存储

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: models-pvc }
spec:
  accessModes: [ReadWriteMany]            # RWM 必要
  resources: { requests: { storage: 2Ti } }
  storageClassName: cephfs                # 或 nfs / juicefs

---
apiVersion: apps/v1
kind: Deployment
metadata: { name: vllm }
spec:
  replicas: 4
  template:
    spec:
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          args:
            - --model=/models/Meta-Llama-3-70B-Instruct
            - -tp=2
          volumeMounts:
            - { name: models, mountPath: /models, readOnly: true }
          resources:
            limits: { nvidia.com/gpu: 2 }
      volumes:
        - name: models
          persistentVolumeClaim:
            claimName: models-pvc
```

### 4.3 DaemonSet 预热到节点

```yaml
# DaemonSet 在每个 GPU 节点预拉模型到 hostPath
apiVersion: apps/v1
kind: DaemonSet
metadata: { name: model-prefetch }
spec:
  selector: { matchLabels: { app: model-prefetch } }
  template:
    metadata: { labels: { app: model-prefetch } }
    spec:
      nodeSelector: { nvidia.com/gpu.present: "true" }
      hostNetwork: true                   # 用 host 网络下载快
      containers:
        - name: prefetch
          image: ghcr.io/huggingface/huggingface_hub:latest
          command:
            - sh
            - -c
            - |
              export HF_ENDPOINT=https://hf-mirror.com
              hf download meta-llama/Meta-Llama-3-70B-Instruct \
                --local-dir /host-models/llama3-70b
              sleep infinity              # 保持 Pod 活，避免重启
          volumeMounts:
            - { name: host-models, mountPath: /host-models }
      volumes:
        - name: host-models
          hostPath:
            path: /mnt/nvme/models
            type: DirectoryOrCreate

---
# vLLM Deployment 用 hostPath 读模型
apiVersion: apps/v1
kind: Deployment
metadata: { name: vllm }
spec:
  template:
    spec:
      nodeSelector: { nvidia.com/gpu.present: "true" }
      containers:
        - name: vllm
          args: [--model=/models/llama3-70b]
          volumeMounts:
            - { name: models, mountPath: /models, readOnly: true }
      volumes:
        - name: models
          hostPath:
            path: /mnt/nvme/models
            type: Directory
```

### 4.4 Fluid（数据编排）

```yaml
# Fluid 把远程模型缓存到本地 alluxio/jindofs
apiVersion: data.fluid.io/v1alpha1
kind: Dataset
metadata: { name: llama3-70b }
spec:
  mounts:
    - mountPoint: s3://bucket/models/llama3-70b
      name: llama3
      options:
        fs.s3a.endpoint: http://minio:9000

---
apiVersion: data.fluid.io/v1alpha1
kind: AlluxioRuntime
metadata: { name: llama3-70b }
spec:
  replicas: 2
  tieredstore:
    levels:
      - mediumtype: MEM
        path: /dev/shm
        quota: 200Gi
        high: "0.95"
        low: "0.7"
```

## 五、Docker 镜像最佳实践

### 5.1 LLM 推理镜像

```dockerfile
# 自建 vLLM 镜像（带模型）
FROM vllm/vllm-openai:v0.7.0 AS base

# 1. 模型预拉到镜像
RUN pip install -U huggingface_hub
ENV HF_ENDPOINT=https://hf-mirror.com
RUN hf download Qwen/Qwen2.5-7B-Instruct \
    --local-dir /models/qwen2.5-7b \
    --include "*.safetensors" "*.json" "tokenizer*"

# 2. 启动脚本
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
```

```bash
#!/bin/bash
# entrypoint.sh
exec vllm serve /models/qwen2.5-7b \
  --tensor-parallel-size ${TP:-1} \
  --max-model-len ${MAX_LEN:-32768} \
  --gpu-memory-utilization 0.9 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --port 8000 "$@"
```

### 5.2 多阶段构建（瘦身）

```dockerfile
# Stage 1: 模型下载
FROM huggingface/downloader:latest AS model-stage
RUN hf download Qwen/Qwen2.5-7B-Instruct --local-dir /models

# Stage 2: 运行时
FROM vllm/vllm-openai:latest
COPY --from=model-stage /models /models

# 一次性构建，不需重复下载
```

### 5.3 镜像优化技巧

```
✅ 用官方 vllm/vllm-openai 基础
✅ 模型 layer 单独（变更频次低）
✅ Squash 减少 layer
✅ Distroless 基底（更小）
✅ 不要打多份依赖
✅ pip --no-cache-dir
✅ .dockerignore 严格

镜像大小参考:
  vLLM base:        ~10 GB
  + 7B FP16 model:  ~24 GB
  + 70B AWQ model:  ~45 GB
  + 70B FP16 model: ~150 GB (不推荐内嵌)
```

## 六、推理服务启动

### 6.1 启动检查清单

```
✅ 模型完整性（hash 校验）
✅ Tokenizer 兼容
✅ Chat Template 正确
✅ Max Context 设置合理
✅ GPU 显存预算
✅ Health Endpoint 响应
✅ Metrics Endpoint 响应
✅ 第一个推理请求成功（warmup）
```

### 6.2 vLLM Health/Warmup

```bash
# 健康检查
curl http://localhost:8000/health
# {"status":"healthy"}

# Models list
curl http://localhost:8000/v1/models

# Warmup（第一次推理慢）
curl http://localhost:8000/v1/completions \
  -d '{"model": "x", "prompt": "hello", "max_tokens": 1}'

# 多 token 长度 warmup
for len in 100 1000 4000 8000; do
  curl -s http://localhost:8000/v1/completions \
    -d "{\"model\": \"x\", \"prompt\": \"$(yes 'word' | head -n $len | tr '\n' ' ')\", \"max_tokens\": 10}" \
    > /dev/null
  echo "Warmup $len done"
done
```

### 6.3 K8s 探针配置

```yaml
spec:
  containers:
    - name: vllm
      ports: [{ containerPort: 8000 }]
      startupProbe:                       # 启动慢，至少 5-10 分钟
        httpGet: { path: /health, port: 8000 }
        failureThreshold: 60               # 60 × 10s = 10min
        periodSeconds: 10
      readinessProbe:                     # 就绪
        httpGet: { path: /health, port: 8000 }
        periodSeconds: 5
        timeoutSeconds: 3
        failureThreshold: 3
      livenessProbe:                      # 死锁检测（保守）
        httpGet: { path: /health, port: 8000 }
        periodSeconds: 30
        timeoutSeconds: 10
        failureThreshold: 5               # 5 × 30s = 2.5min 才重启
      lifecycle:
        preStop:
          exec:
            command:
              - sh
              - -c
              - sleep 30                  # 优雅退出，等流量切走
```

## 七、Chat Template

### 7.1 为什么重要

```
不同模型对 system / user / assistant 标签格式不同
错误的 chat template = 输出乱码或质量崩溃

例:
  Llama-3: <|begin_of_text|><|start_header_id|>user<|end_header_id|>...
  Qwen-2.5: <|im_start|>user\n...\n<|im_end|>
  Mistral: [INST] ... [/INST]
  ChatGLM: <|user|>\n...\n<|assistant|>
```

### 7.2 vLLM 自定义 chat template

```bash
# 大多数主流模型 vLLM 已内置（tokenizer_config.json）
# 特殊模型需要传入 --chat-template

# Llama-3 默认
vllm serve meta-llama/Meta-Llama-3-70B-Instruct
# 直接 work

# 自定义
vllm serve mymodel --chat-template ./template.jinja
```

```jinja
{# template.jinja - Qwen ChatML 格式 #}
{% for message in messages %}
{% if message['role'] == 'system' %}<|im_start|>system
{{ message['content'] }}<|im_end|>
{% elif message['role'] == 'user' %}<|im_start|>user
{{ message['content'] }}<|im_end|>
{% elif message['role'] == 'assistant' %}<|im_start|>assistant
{{ message['content'] }}<|im_end|>
{% endif %}
{% endfor %}
{% if add_generation_prompt %}<|im_start|>assistant
{% endif %}
```

## 八、CI/CD 自动化部署

### 8.1 完整 Pipeline

```yaml
# .gitlab-ci.yml / GitHub Actions
stages:
  - convert
  - quantize
  - build-image
  - deploy
  - smoke-test
  - canary
  - rollout

convert:
  script:
    - hf download $MODEL --local-dir ./model
    - python convert.py model/ output/ --safe-serialization
    - aws s3 sync output/ s3://models/$VERSION/

quantize:
  script:
    - python awq_quantize.py s3://models/$VERSION/ s3://models/$VERSION-awq/

build-image:
  script:
    - docker build -t harbor/llm/$MODEL:$VERSION .
    - cosign sign --key cosign.key harbor/llm/$MODEL:$VERSION
    - docker push harbor/llm/$MODEL:$VERSION

deploy:
  script:
    - kubectl set image deployment/vllm-canary vllm=harbor/llm/$MODEL:$VERSION -n llm
    - kubectl rollout status deployment/vllm-canary

smoke-test:
  script:
    - python smoke_test.py http://vllm-canary

canary:
  script:
    - argocd app set vllm --kustomize-image=$MODEL:$VERSION
    - argo-rollouts set image vllm vllm=harbor/llm/$MODEL:$VERSION

rollout:
  when: manual
  script:
    - argo-rollouts promote vllm
```

### 8.2 模型评估门禁

```python
# pre-deploy evaluation
import openai, json
from datasets import load_dataset

client = openai.OpenAI(base_url="http://vllm-canary:8000/v1")

# 1. 基础 sanity
assert client.models.list()

# 2. 跑评测集
mmlu = load_dataset("hails/mmlu_no_train", split="test").select(range(200))
correct = 0
for q in mmlu:
    answer = client.chat.completions.create(
        model="x", messages=[{"role": "user", "content": format(q)}]
    ).choices[0].message.content
    correct += parse_answer(answer) == q["answer"]

acc = correct / 200
baseline = 0.65
assert acc >= baseline - 0.02, f"Quality regression: {acc:.2%} vs {baseline:.2%}"

# 3. 延迟门禁
p99_ttft = measure_ttft(samples=100)
assert p99_ttft < 500, f"TTFT regression: {p99_ttft}ms"

print("✅ All gates passed, proceeding to rollout")
```

## 九、版本管理与回滚

### 9.1 模型版本约定

```
版本号:
  v1.0.0    模型架构 + 训练
  v1.0.1    量化方案变更（FP16 → AWQ）
  v1.1.0    LoRA 微调更新
  v2.0.0    主版本（不兼容）

标签:
  stable     当前生产
  canary     灰度中
  latest     最新（开发用）
  legacy     旧版回滚备份
```

### 9.2 快速回滚

```bash
# Argo Rollouts
kubectl-argo-rollouts undo vllm
# 自动切回上一个稳定版

# Kubernetes 原生
kubectl rollout undo deployment/vllm
kubectl rollout history deployment/vllm
kubectl rollout undo deployment/vllm --to-revision=3

# Helm
helm rollback vllm 1
```

## 十、生产 Checklist

```
模型层:
☐ Safetensors 格式
☐ 校验和（sha256）
☐ Chat Template 正确
☐ Tokenizer 校验
☐ 量化精度评估

镜像层:
☐ 基础镜像 pin SHA
☐ Cosign 签名
☐ Trivy 扫描
☐ Layer 优化

部署层:
☐ K8s 探针（startup/readiness/liveness）
☐ 资源 request/limit
☐ 优雅退出 (preStop)
☐ GPU Operator
☐ DaemonSet 预热 OR PVC

发布层:
☐ 灰度（10% → 30% → 100%）
☐ 评估门禁（accuracy + latency）
☐ 自动回滚条件
☐ 流量切分（Istio / Argo Rollouts）

监控:
☐ Prometheus metrics
☐ Langfuse trace
☐ 模型 quality 离线评估
```

## 十一、典型坑

| 坑 | 建议 |
|:---|:---|
| **下载到一半挂** | hf 自动续传 + 校验 |
| **Safetensors header 损坏** | safetensors-cli check |
| **PVC 慢盘** | 上 NVMe / 节点本地 |
| **Init Container 超时** | startupProbe failureThreshold 调大 |
| **Chat Template 错** | curl 看真实 prompt → 对比官方 |
| **Tokenizer 不匹配** | 用模型自带 tokenizer |
| **量化精度差** | AWQ > GPTQ > BNB |
| **镜像太大** | 模型分层 / OCI Artifact |
| **K8s 滚动重启抖** | maxSurge=1, maxUnavailable=0 |
| **多副本同时拉模型** | DaemonSet 预热 |
| **PVC 单点失败** | RWM 改为 RWO + 节点亲和 |
| **GPU 抢占 OOM** | 严格 limit + MIG |
| **冷启动慢** | min replicas + warmup probe |
| **Helm 回滚漏改 ConfigMap** | GitOps Argo |
| **模型签名缺失** | Cosign keyless + Sigstore Policy |

## 十二、推荐栈（2025）

### 12.1 中小团队

```
模型源:     HF + 国内镜像
格式:       Safetensors / GGUF
量化:       AWQ INT4 / GGUF Q4_K_M
仓库:       Harbor (镜像 + 模型 OCI)
分发:       PVC + Init Container 拉取
部署:       Docker Compose / Helm
```

### 12.2 中大企业

```
模型源:     HF + ModelScope + 内部镜像
格式:       Safetensors + AWQ + GGUF + FP8
仓库:       Harbor + JFrog ML / 自研 Registry
分发:       DaemonSet 预热到 NVMe / Fluid
部署:       Argo CD GitOps + Argo Rollouts
评估:       离线评测 + Langfuse + 灰度门禁
```

### 12.3 大规模

```
+ 自研模型平台（训→评→量→部署→监控）
+ 跨集群多 region 同步
+ 自动模型 A/B
+ 持续评测 + 漂移检测
+ 国密 / 等保合规
```

## 十三、学习路径

```
入门（2 周）:
  1. HF 下载 / Safetensors 格式
  2. Docker 部署 vLLM
  3. AWQ 量化模型
  4. K8s Deployment 基础

中级（1 月）:
  5. GGUF 量化与 llama.cpp
  6. TRT-LLM engine build
  7. K8s 模型分发（PVC / DaemonSet）
  8. Chat Template 调试
  9. Helm + Argo Rollouts

高级（3 月+）:
  10. 模型评估自动化
  11. 灰度发布门禁
  12. OCI Artifact 模型仓库
  13. 跨集群分发 (Fluid)
  14. 自动化模型 Pipeline

专家:
  15. 自研模型平台
  16. 全栈版本管理
  17. 持续评测
```

## 十四、参考资料

```
官方:
  - HuggingFace Hub: https://huggingface.co/docs/hub
  - Safetensors: https://github.com/huggingface/safetensors
  - vLLM Deployment: https://docs.vllm.ai/en/latest/serving/deploying_with_k8s.html
  - GGUF: https://github.com/ggerganov/ggml/blob/master/docs/gguf.md
  - AWQ: https://github.com/mit-han-lab/llm-awq
  - GPTQ: https://github.com/AutoGPTQ/AutoGPTQ
  - ORAS: https://oras.land/
  - Fluid: https://github.com/fluid-cloudnative/fluid

社区:
  - HF Discord
  - r/LocalLLaMA (GGUF 量化讨论)
  - 国内: ModelScope 社区
```

> 📖 **核心判断**：模型部署 = **格式（Safetensors/GGUF/AWQ）+ 分发（DaemonSet 预热到 NVMe 是大模型最佳实践）+ 容器（镜像 + 模型分层）+ K8s（探针 + 优雅退出）+ 灰度（门禁 + 自动回滚）**。**冷启动 + 拉模型** 是最常见的生产瓶颈——单节点 70B 模型从 S3 拉取需要 5-10 分钟，DaemonSet 预热是必备方案。**Chat Template** 是被忽视最严重的细节，错一个字符整模型质量崩塌。

