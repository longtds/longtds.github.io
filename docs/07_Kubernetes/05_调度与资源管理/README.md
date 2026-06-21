# 调度与资源管理

## QoS 服务质量

| 级别 | 配置 | 行为 |
|:---|:---|:---|
| Guaranteed | request=limit | 最优先，不驱逐 |
| Burstable | request < limit | 中等优先级 |
| BestEffort | 不设 request/limit | 最低优先级，先被驱逐 |

## 调度策略

```yaml
# NodeSelector
spec:
  nodeSelector:
    gpu-type: nvidia-a100

# 节点亲和性
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: topology.kubernetes.io/zone
            operator: In
            values:
            - us-east-1a

# Pod 反亲和
spec:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values:
              - web
          topologyKey: kubernetes.io/hostname
```

## HPA（水平扩缩容）

```bash
kubectl autoscale deployment web --cpu-percent=70 --min=3 --max=10
```

## GPU 调度

```yaml
# 请求 GPU
spec:
  containers:
  - name: inference
    image: nvidia/cuda:12.3
    resources:
      requests:
        nvidia.com/gpu: 1
      limits:
        nvidia.com/gpu: 1
```
