# 07. Kubernetes

> Kubernetes 是云原生的事实标准。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦核心对象 / kubeadm HA / Cilium+Calico CNI / Rook+Longhorn CSI / Ingress+Gateway API / kube-prometheus+Loki+Tempo / Operator+CRD / Karmada 多集群 / Istio Ambient / KubeVirt / GPU+HAMi / CoCo / GitOps + 国产化十二条主线。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入职 1 年内 | 核心对象 / Pod/Deployment/Service/Ingress / ConfigMap+Secret / PV/PVC / RBAC / kubectl / Helm / 调度模型 / HPA+Probe / CNI+CSI+CRI / 排障 + 20 题 |
| [02_进阶](02_进阶/README.md) | 独立运维平台 | kubeadm HA / Cilium 深度+NetworkPolicy / Rook-Ceph+Longhorn / Ingress+cert-manager+Gateway API / kube-prometheus-stack+Loki+Tempo / Helm+Kustomize+ArgoCD GitOps / Velero+etcd 备份 / PSS+多租户 / 集群升级 + CRD 基础 |
| [03_高级](03_高级/README.md) | 平台架构师 | Operator/kubebuilder / Volcano+Kueue+HAMi 调度 / Karmada+CAPI 多集群 / Istio Ambient / KubeVirt / GPU+MIG+国产 / CoCo / ArgoCD ApplicationSet+Image Updater+Rollouts/Workflows / Hubble+Tetragon+DeepFlow / 大规模调优(etcd/apiserver/CoreDNS) / KubeSphere 国产化深度 |
| [04_最佳实践](04_最佳实践/README.md) | 团队负责人 | 集群选型+多集群拓扑 / 节点基线 / 资源画像(VPA/KRR) / 多租户(RBAC+Quota+NP+PSS) / Kyverno 强制策略 / Deployment 团队基线 / 监控告警 SLO / 备份灾备演练 / 升级 SOP / FinOps / 国产化路径 / 故障排查体系 + 4 种生产架构模板 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | DRA/Gateway API/LTS / Operator 应用模型 / Karmada 多集群 / Istio Ambient / AI 调度成核心 / KubeEdge+OpenYurt / KubeVirt 替代 VMware / CoCo+机密 AI / eBPF 全栈 / Wasm 共生 / 国产开源 70% / Platform Engineering + 19 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
 └─ 01_基础: kubeadm 3 节点 + kubectl + Deployment/Service/Ingress + ConfigMap/Secret + StatefulSet/PVC + RBAC + Helm + HPA + 20 题

进阶（3-12 月）
 └─ 02_进阶: kubeadm HA + Cilium+NP + Rook-Ceph + cert-manager + kube-prometheus-stack + Loki + ArgoCD + Velero + PSS restricted

高级（1-2 年）
 └─ 03_高级: kubebuilder Operator + Volcano+HAMi 调度 + Karmada 多集群 + Istio Ambient + KubeVirt + GPU+MIG + CoCo + Argo Rollouts + DeepFlow eBPF + 大规模调优

工程化（2-3 年）
 └─ 04_最佳实践: 多集群拓扑 + 节点池 + VPA/KRR 画像 + 多租户 + Kyverno 强制 + 监控 SLO + 灾备演练 + 升级 SOP + FinOps + 国产化路径

展望（持续）
 └─ 99_发展与展望: DRA + Operator + Karmada + Ambient + AI 调度 + 边缘 + KubeVirt + CoCo + eBPF + Wasm + 国产 + 平台工程 十二条主线
```

## 核心判断

```
心法:
 1. K8s 是声明式 + 控制器 + Reconcile，理解这三个比记 kubectl 命令重要
 2. Pod 是最小调度单元，Service 是稳定 VIP，Operator/CRD 是应用模型
 3. 生产必 kubeadm HA + Cilium + Rook + ArgoCD + kube-prometheus
 4. 多集群是默认选项（dev/staging/prod 至少 3 集群）
 5. PSS restricted + NetworkPolicy 默认 deny + RBAC 最小权限 三件套
 6. requests/limits + Probe 三件套 + topology spread 不可缺
 7. Velero + etcd snapshot + 季度演练 是底线
 8. AI 训练 → Volcano/HAMi/vLLM 是必备分水岭
 9. 边缘 → KubeEdge/OpenYurt + k3s 国产首选
 10. 国产化 → KubeSphere + Karmada + HAMi + DeepFlow + Higress 全栈

红线:
 单 master 上生产
 etcd 共享盘 / 跑虚拟机
 没 requests/limits → BestEffort
 没 NetworkPolicy → 全网互通
 root 跑容器 + privileged
 :latest 上生产
 kubectl exec 改文件 (要全 IaC)
 Secret base64 当加密
 Audit log 没接 SIEM
 etcd 备份没演练
 minor 跨多版本升级
 单集群上 3000+ 节点（拆 Karmada 联邦）
 没 PDB → 滚动直接挂业务
```

## 相关章节

- 配合 [02_Linux](../02_Linux/index.md) 看 namespace / cgroup v2 / eBPF / 内核调优
- 配合 [03_网络](../03_网络/index.md) 看 BGP / VXLAN / OVN / iptables / IPVS
- 配合 [04_虚拟化](../04_虚拟化/index.md) 看 KubeVirt / Kata / KVM 直通
- 配合 [05_私有云](../05_私有云/index.md) 看 OpenStack 共生 + Magnum 调度 K8s
- 配合 [06_Docker](../06_Docker/index.md) 看 containerd / OCI / Buildx / Harbor / cosign
- 配合 [08_DevOps](../08_DevOps/index.md) 看 GitOps / ArgoCD / Tekton / Jenkins X
- 配合 [09_中间件](../09_中间件/index.md) 看 KubeBlocks / StatefulSet 中间件运维
- 配合 [10_大数据](../10_大数据/index.md) 看 Spark on K8s / Flink Operator / 数据湖
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 GPU+MIG+HAMi / vLLM / KServe / 训练调度
- 配合 [12_AIOps](../12_AIOps/index.md) 看 K8s 异常检测 + LLM 告警 + 知识库
- 配合 [13_认证与SSO](../13_认证与SSO/index.md) 看 OIDC + Keycloak + K8s SSO
- 配合 [14_安全](../14_安全/index.md) 看 Pod Security / Kyverno / Falco / Tetragon / CoCo
- 配合 [16_故障排查](../16_故障排查/index.md) 看 K8s 应急 SOP / Postmortem
