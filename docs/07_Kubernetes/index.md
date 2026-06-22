# 07_Kubernetes · 概述

> K8s 是云原生的事实标准，是分布式系统的"Linux 内核"。

## 一、K8s 发展简史

| 时期 | 里程碑 |
|:---:|:---|
| 2003-2014 | Google 内部 Borg/Omega，积累 10+ 年经验 |
| 2014.06 | K8s 开源（v0.1） |
| 2015.07 | v1.0 + CNCF 成立 |
| 2016 | Helm/Prometheus 加入 CNCF |
| 2017 | Kubernetes 击败 Docker Swarm 和 Mesos |
| 2018 | CRD + Operator 模式成型 |
| 2020 | 移除 in-tree volume，移除 dockershim 公告 |
| 2022 | dockershim 移除，containerd 主流 |
| 2024 | K8s 1.32，GA 用户超过 78% 财富 500 强 |

## 二、K8s 整体架构

```
┌─────────────────────── 控制平面 ───────────────────────┐
│                                                       │
│   kube-apiserver ←→ etcd                              │
│        ↓                                              │
│   kube-scheduler                                       │
│   kube-controller-manager                              │
│   cloud-controller-manager                             │
│                                                       │
└───────────────────────────────────────────────────────┘
                          ↑↓
┌──────────────────── 数据/工作节点 ─────────────────────┐
│                                                       │
│   kubelet ←→ 容器运行时 (containerd/CRI-O)             │
│   kube-proxy / Cilium                                  │
│   CNI 插件（网络） / CSI 插件（存储）                    │
│                                                       │
└───────────────────────────────────────────────────────┘
```

## 三、核心抽象层

```
最终目标:    应用稳定运行
              ↑
工作负载:    Deployment / StatefulSet / DaemonSet / Job
              ↑
基础抽象:    Pod (一个或多个紧密协作的容器)
              ↑
服务发现:    Service / Ingress / Gateway API
              ↑
配置存储:    ConfigMap / Secret / PVC
              ↑
平台层:      Namespace / RBAC / NetworkPolicy / ResourceQuota
              ↑
基础设施:    Node / 容器运行时 / CNI / CSI
```

## 四、为什么 K8s 赢了

| 维度 | K8s 优势 |
|:---|:---|
| **设计哲学** | 声明式 API + 控制器循环 = 最终一致性 |
| **扩展性** | CRD + Operator = 无限可编程 |
| **生态** | 6000+ CNCF 项目环绕 |
| **社区** | 200+ 厂商、500K+ 贡献者 |
| **API 稳定** | 1.0 后核心 API 极少破坏性变更 |
| **可移植** | 同一份 YAML 跑遍公有云/私有云 |

## 五、K8s 适合 vs 不适合

| 适合 ✅ | 不适合 ❌ |
|:---|:---|
| 微服务、无状态应用 | 单体 Windows 应用（除非 WSL/Hyper-V）|
| 弹性伸缩、滚动发布 | 数据库主节点（除非用 Operator） |
| 多环境一致部署 | 极致单机性能（裸金属 + DPDK） |
| 中大规模团队（10+ 开发） | 1-3 人小团队（学习成本高） |
| 微服务架构 | 紧耦合应用（先重构再上 K8s） |

## 六、本章组织

| 子章节 | 内容 |
|:---|:---|
| **01_基础概念** | Pod/Deployment/Service/标签/选择器 |
| **02_集群部署** | kubeadm/kops/Rancher/k3s |
| **03_网络** | CNI、Service、Ingress、Gateway API、Cilium |
| **04_存储** | CSI、StorageClass、PV/PVC、Rook/OpenEBS |
| **05_调度与资源管理** | requests/limits、亲和、污点、QoS、HPA/VPA |
| **06_Operator开发** | controller-runtime、kubebuilder、Helm |
| **07_安全** | RBAC、Pod Security、Network Policy、镜像扫描 |
| **08_CICD** | Argo CD/Flux、Tekton、GitOps |
| **09_可观测性** | Prometheus、Grafana、Loki、Tempo、OTel |
| **10_集群运维** | etcd 备份、升级、节点维护 |
| **11_生态工具** | Helm、Kustomize、kubectl 插件 |

## 七、学习路径（按经验分）

| 阶段 | 目标 | 推荐资源 |
|:---|:---|:---|
| 入门 (1月) | 跑通 Hello World、理解 Pod/Deployment/Service | 官方 tutorial、Killercoda |
| 进阶 (3月) | 部署应用集群、Helm、RBAC、网络策略 | CKAD 认证 |
| 生产 (6月) | 集群运维、故障排查、监控告警 | CKA 认证 |
| 高阶 (1年+) | Operator 开发、内核优化、多集群 | CKS / 阅读源码 |

> 📖 K8s 是一门"长期学科"，但回报巨大。这是本手册最大的章节，原因不言而喻。
