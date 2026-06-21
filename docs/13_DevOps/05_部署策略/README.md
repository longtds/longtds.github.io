# 部署策略

## 滚动更新

K8s 默认策略，逐步替换 Pod。

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1       # 最多不可用 Pod 数
      maxSurge: 1             # 最多超量 Pod 数
```

## 蓝绿部署

同时运行两套环境，切换流量完成部署。

## 灰度发布（Canary）

逐步将流量切到新版本，监控指标正常后才全量。

## GitOps（ArgoCD）

以 Git 仓库作为单一事实来源，ArgoCD 自动同步集群状态。
