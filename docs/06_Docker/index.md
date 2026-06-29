# 06. Docker

> Docker / OCI 容器是云原生的底座。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦 namespace+cgroup+overlay2 原理、dockerd+containerd+runc 三层架构、Buildx 多架构、Harbor 仓库治理、cosign 签名+SBOM、Kata/gVisor/Wasm 替代运行时、GPU/MIG 容器、国产化 iSulad 八条主线。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入职 1 年内 | namespace/cgroup/overlay2 / dockerd+containerd+runc / OCI 三规范 / Dockerfile 多阶段 / docker CLI / 网络+存储 / Compose 单机 / 安全基线 / 国产化镜像 + 20 题 |
| [02_进阶](02_进阶/README.md) | 独立运维容器化平台 | BuildKit+Buildx 多架构 / 远程缓存 / 镜像优化(dive/distroless) / Harbor+Replication+Proxy Cache / cosign+SBOM+Provenance / macvlan+iptables / daemon.json 调优 / Compose 生产 / cAdvisor+Prometheus / rootless+seccomp |
| [03_高级](03_高级/README.md) | 平台架构师 | containerd/CRI-O 直驱 / crun+youki+kata+gVisor+Firecracker / Confidential Containers / Buildah+Kaniko+nerdctl / Wasm 容器(WasmEdge) / GPU+MIG+国产 GPU / cgroup v2+eBPF(Tetragon/DeepFlow) / iSulad / 多架构嵌入式 / 容器逃逸加固 |
| [04_最佳实践](04_最佳实践/README.md) | 团队负责人 | 运行时选型 / 镜像规范+分级 / Harbor 治理 / CI/CD 流水线(lint+scan+sign+SBOM+Provenance) / 监控告警 SOP / CIS+等保自查 / 资源容量 / K8s 接管节奏 / 国产化路径 / 故障排查 SOP |
| [99_发展与展望](99_发展与展望.md) | 所有人 | Docker 收缩 / containerd 标准化 / Kata-cc / Wasm / GPU 国产化 / SLSA+Sigstore / OCI Artifacts / 边缘/嵌入式 / iSulad / 18 项 5 年信心矩阵 |

## 学习路径

```
入门（1-2 月）
 └─ 01_基础: 装 docker + 镜像加速器 + Compose 单机 + 多阶段 distroless + Harbor + Trivy + 20 题

进阶（3-12 月）
 └─ 02_进阶: Buildx 多架构 + 远程缓存 + 镜像 < 50MB + Harbor Replication+Proxy Cache + cosign+SBOM + macvlan + cAdvisor 监控 + rootless

高级（1-2 年）
 └─ 03_高级: containerd 直驱 + Kata + gVisor + CoCo + Buildah/Kaniko + Wasm + GPU/MIG + 国产 iSulad + eBPF(Tetragon) + 容器逃逸加固

工程化（2-3 年）
 └─ 04_最佳实践: 镜像规范+分级 + CI/CD 全链(lint+scan+sign+SBOM+Provenance) + Harbor 治理 + 监控告警 + CIS+等保 + GitOps + 国产化路径

展望（持续）
 └─ 99_发展与展望: containerd 标准 + Kata-cc + Wasm + GPU 国产 + Sigstore + 边缘 + iSulad 八条主线
```

## 核心判断

```
心法:
 1. 容器 = namespace+cgroup+rootfs，不是"轻量 VM"，是受限进程
 2. dockerd/containerd/runc 三层都要懂
 3. OCI 三规范 (Image/Runtime/Distribution) 才是核心，不是 Docker
 4. 生产 K8s 一律 containerd（dockershim 已退场）
 5. 镜像 < 50 MB 是基本功 (distroless + 多阶段)
 6. Harbor + cosign + Trivy + SBOM 是供应链四件套
 7. 多架构 amd64 + arm64 一次推
 8. rootless / userns / seccomp / AppArmor 安全四件套
 9. Kata / gVisor / Wasm / CoCo 是 OCI 内的多元未来
 10. 国产化 = openEuler + iSulad + 鲲鹏 ARM + Harbor 国密

红线:
 :latest 上生产
 root 跑容器
 --privileged 滥用
 挂 /var/run/docker.sock 到容器
 没 HEALTHCHECK + 没 livenessProbe
 日志写容器内
 /var/lib/docker 不分区不 GC
 K8s 1.24+ 还用 dockershim
 CI 用 admin 账号 push
 Trivy 扫不阻断
 不签名 / 不验签
 没 SBOM 供应链审计无据
```

## 相关章节

- 配合 [02_Linux](../02_Linux/index.md) 看 namespace / cgroup v2 / eBPF 内核基础
- 配合 [03_网络](../03_网络/index.md) 看 bridge / macvlan / iptables / OVN
- 配合 [04_虚拟化](../04_虚拟化/index.md) 看 KubeVirt / Kata-microVM / Firecracker
- 配合 [05_私有云](../05_私有云/index.md) 看 OpenStack 与 K8s 共生
- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 CRI / RuntimeClass / GPU Operator / Pod Security
- 配合 [08_DevOps](../08_DevOps/index.md) 看 GitOps / Buildkit-in-K8s / Kaniko / ArgoCD
- 配合 [09_中间件](../09_中间件/index.md) 看容器化 DB / 消息队列
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 GPU 容器 / vLLM / 训练镜像
- 配合 [12_AIOps](../12_AIOps/index.md) 看容器异常检测 / eBPF 可观测
- 配合 [14_安全](../14_安全/index.md) 看 CIS + NIST 800-190 + 机密计算 + 等保
- 配合 [16_故障排查](../16_故障排查/index.md) 看容器 OOM / 网络 / Pull / OOM-killer 排障
