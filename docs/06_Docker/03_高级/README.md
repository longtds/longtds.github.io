# 高级

> Docker 高级 = **containerd/CRI-O 直驱 + 替代运行时(crun/youki/kata/gVisor/Firecracker) + Confidential Containers(CoCo) + Buildah/img/kaniko/nerdctl 工具栈 + Wasm 容器(WasmEdge/Wasmtime) + 国产 OCI(iSulad/PouchContainer) + 内核优化(cgroup v2/eBPF) + 多架构嵌入式 + GPU 容器(NVIDIA Container Toolkit/MIG) + 容器逃逸与加固**。本章面向需要构建底层容器平台、AI 训练镜像、机密计算、边缘嵌入式的高级工程师。

## 一、CRI 与运行时分层

### 1.1 三层结构

```
Orchestrator (K8s)
     │ CRI gRPC
     ▼
High-level Runtime
  containerd ⭐ (CNCF) / CRI-O (Red Hat)
     │ OCI Runtime API
     ▼
Low-level Runtime
  runc ⭐ (Go)     默认
  crun (C)        轻量、cgroup v2 原生
  youki (Rust)    现代、安全
  kata-runtime    microVM 隔离
  gVisor (runsc)  用户态内核
  Firecracker     AWS microVM
  cloud-hyperv.   Intel/MS Rust VMM
```

### 1.2 containerd 直接使用

```bash
# 客户端
ctr -n k8s.io images ls          # K8s 用 k8s.io namespace
ctr -n default run --rm -t docker.io/library/alpine:latest a1 sh

# nerdctl (Docker 兼容 CLI for containerd)
nerdctl pull nginx:1.27
nerdctl run -d -p 80:80 nginx:1.27
nerdctl build -t myapp:1.0 .
nerdctl compose up -d            # 兼容 compose
nerdctl namespace ls

# 配置 /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri"]
  systemd_cgroup = true
  sandbox_image = "registry.aliyuncs.com/k8sxio/pause:3.9"
[plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
  endpoint = ["https://docker.m.daocloud.io"]
```

### 1.3 CRI-O 直接使用

```bash
# Red Hat 系（OpenShift 默认）
dnf install -y cri-o
systemctl enable --now crio

crictl ps                        # CRI 客户端（K8s 也用它）
crictl images
crictl logs <container>
crictl exec -it <ctr> sh
```

### 1.4 替代低层运行时

```toml
# containerd 配置不同 runtime
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes]
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
    runtime_type = "io.containerd.runc.v2"
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.crun]
    runtime_type = "io.containerd.runc.v2"
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.crun.options]
      BinaryName = "/usr/bin/crun"
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
    runtime_type = "io.containerd.kata.v2"
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.gvisor]
    runtime_type = "io.containerd.runsc.v1"
```

K8s 端 `RuntimeClass`：

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata: { name: kata }
handler: kata
---
apiVersion: v1
kind: Pod
metadata: { name: secure-pod }
spec:
  runtimeClassName: kata
  containers:
    - { name: app, image: myapp:1.0 }
```

## 二、Kata Containers（强隔离）

### 2.1 原理

```
每 Pod 一个 microVM (QEMU / Cloud Hypervisor / Firecracker)
  - 独立内核
  - 共享 K8s 网络/存储
  - 容器 API + VM 隔离强度
  
启动: ~1s（vs runc <100ms）
内存开销: +50-150 MB / Pod
```

### 2.2 部署

```bash
# Kata 3.x
dnf install -y kata-containers
# 或 K8s operator: github.com/kata-containers/kata-deploy

# K8s 节点打 label
kubectl label node node1 katacontainers.io/kata-runtime=true

# 应用 RuntimeClass
kubectl apply -f https://raw.githubusercontent.com/kata-containers/kata-deploy/stable/runtimeclasses/kata-runtimeClasses.yaml
```

### 2.3 适用

```
- 多租户 SaaS / FaaS
- 不可信代码执行（CI / 在线 IDE）
- 机密计算（结合 SEV-SNP/TDX → Confidential Containers）
- K8s 平台严格隔离
```

## 三、gVisor / Firecracker / Cloud Hypervisor

### 3.1 gVisor (runsc)

```
原理:
  - 用户态内核（Sentry + Gofer）
  - 拦截 syscalls 重新实现
  - 不用 KVM
  
特点:
  +系统调用过滤 → 强安全
  -某些 syscall 不支持
  -性能损耗 5-30%
  
代表:
  Google Cloud Run / App Engine
  阿里函数计算 FC
```

```bash
dnf install -y runsc
# containerd config 加 runsc runtime
# K8s RuntimeClass: gvisor
```

### 3.2 Firecracker (AWS)

```
原理:
  - Rust microVM
  - 仅 5 个设备模型（极简）
  - 启动 < 125ms / 内存 ~5 MB

集成:
  firecracker-containerd
  Kata + Firecracker backend
  Fly.io 全球边缘
  AWS Lambda / Fargate
```

### 3.3 Cloud Hypervisor (Intel/MS)

```
特点:
  - Rust 重写 QEMU 部分功能
  - 比 Firecracker 功能多
  - 支持 live migration / NUMA / SR-IOV
  
应用:
  Cluster API
  Kata 后端
```

## 四、Confidential Containers (CoCo)

### 4.1 概念

```
CoCo = 容器 + TEE (Trusted Execution Environment)
机密计算硬件:
  AMD SEV-SNP
  Intel TDX
  ARM CCA
  海光 CSV (国产)
  Intel SGX (老，仅 enclave)
  
方式:
  - Pod-level (Kata + SEV-SNP/TDX → 整 Pod 在 TEE)
  - Process-level (SGX enclave) - 老路线

仓库: github.com/confidential-containers
```

### 4.2 实战架构

```
K8s Pod (RuntimeClass: kata-cc)
  ↓
Kata Containers + Cloud Hypervisor
  ↓
SEV-SNP / TDX 加密 VM
  ↓
Attestation Service (KBS) 验证 + 解密 secrets
```

```yaml
apiVersion: v1
kind: Pod
spec:
  runtimeClassName: kata-cc
  containers:
    - name: secure-ai
      image: harbor.example.com/ai/encrypted:1.0  # 加密镜像
      env:
        - name: ATTESTATION_SERVICE
          value: https://kbs.example.com
```

### 4.3 用途

```
- 机密 AI 训练 / 推理（模型 / 数据加密）
- 跨机构联合反欺诈
- 主权云 / 跨境合规
- 金融 / 医疗 / 政务
- 国产化: 海光 CSV CoCo（早期）
```

## 五、构建工具栈（非 Docker）

### 5.1 Buildah / podman

```bash
# Red Hat 系，无 daemon
buildah from alpine
buildah run <ctr> apk add curl
buildah copy <ctr> ./bin /usr/local/bin/bin
buildah commit <ctr> myapp:1.0

# podman build = buildah
podman build -t myapp:1.0 .
podman run -d --name web myapp:1.0
podman generate kube web > pod.yaml      # 直接生成 K8s YAML
```

### 5.2 kaniko（K8s 内构建）

```yaml
# CI 场景，在 K8s Pod 内构建镜像
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: kaniko
      image: gcr.io/kaniko-project/executor:latest
      args:
        - --dockerfile=Dockerfile
        - --context=git://github.com/org/repo.git
        - --destination=harbor.example.com/myproj/app:$TAG
        - --cache=true
        - --cache-repo=harbor.example.com/cache
      volumeMounts:
        - { name: docker-config, mountPath: /kaniko/.docker/ }
```

特点：

- **无 daemon**，无 root，K8s 内安全跑
- 替代 docker-in-docker
- CI/CD 主流

### 5.3 img (jess) / BuildKit standalone

```bash
# BuildKit 独立守护进程
buildkitd --addr unix:///run/buildkit/buildkitd.sock

buildctl build \
  --frontend dockerfile.v0 \
  --local context=. --local dockerfile=. \
  --output type=image,name=myapp:1.0,push=true
```

### 5.4 nerdctl（containerd CLI）

```bash
# 完全兼容 docker CLI
nerdctl ps / images / build / compose / login / push

# K8s 节点直接用
nerdctl -n k8s.io ps
nerdctl -n k8s.io images
```

## 六、Wasm 容器（前沿）

### 6.1 概念

```
Wasm (WebAssembly):
  - 跨平台字节码
  - 沙箱执行
  - 启动 < 1ms
  - 单文件 < 10MB

Wasm 容器 = OCI 镜像（payload 是 wasm 模块）
runtime:
  WasmEdge ⭐ (CNCF Sandbox，国产 Second State 主导)
  Wasmtime (Bytecode Alliance)
  Wasmer
  spin (Fermyon)
```

### 6.2 实战

```bash
# WasmEdge
curl -sSf https://raw.githubusercontent.com/WasmEdge/WasmEdge/master/utils/install.sh | bash

# 写 wasm
cat > hello.rs <<EOF
fn main() { println!("Hello Wasm Container!"); }
EOF
rustup target add wasm32-wasi
rustc --target wasm32-wasi hello.rs -o hello.wasm

# containerd + WasmEdge shim
nerdctl run --runtime io.containerd.wasmedge.v1 \
  --platform wasi/wasm \
  hello.wasm

# K8s RuntimeClass: wasmedge
```

### 6.3 应用场景

```
- 边缘 / IoT (极小资源)
- Serverless / FaaS (毫秒启动)
- 插件系统 (Envoy / Istio WASM filter)
- 安全沙箱 (浏览器外应用)
- AI 推理边缘部署
```

### 6.4 时间窗

```
2026 现状: 早期 / 试点 / WASI Preview 2
2027-2028: Serverless / 边缘扎根
2028+: 与容器形成互补 (重应用容器, 轻应用 Wasm)
```

## 七、GPU 容器（AI 标配）

### 7.1 NVIDIA Container Toolkit

```bash
# 安装
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt update && apt install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# 测试
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

### 7.2 资源切分

```bash
# 整卡
docker run --gpus all ...

# 指定卡
docker run --gpus '"device=0,1"' ...

# MIG 切片 (A100/H100)
nvidia-smi mig -lgip
docker run --gpus '"device=MIG-xxxxxxxx-..."' ...

# 时分共享 / MPS
NVIDIA_VISIBLE_DEVICES=0 + 应用层 MPS
```

### 7.3 containerd + nvidia

```toml
# /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia]
  privileged_without_host_devices = false
  runtime_engine = ""
  runtime_root = ""
  runtime_type = "io.containerd.runc.v2"
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia.options]
    BinaryName = "/usr/bin/nvidia-container-runtime"
```

### 7.4 国产 GPU 容器

```
昇腾 910B:    Ascend Docker Runtime / CANN
摩尔 S4000:   MUSA Container Runtime  
沐曦 MXC:     MX Container Runtime
寒武纪 MLU:   Cambricon MLU Toolkit
天数 BI:     ILUVATAR Container Toolkit
燧原:         Enflame Container Runtime

模式: 各厂 Device Plugin + 类 NVIDIA Toolkit 风格
```

## 八、国产 OCI 运行时

### 8.1 iSulad（华为/openEuler）

```
特点:
  - 轻量级 (内存 < 30MB)
  - 多架构支持 (x86/ARM/RISC-V)
  - openEuler 默认容器引擎
  - 嵌入式 / 边缘场景
  - CRI/OCI 兼容
  
对比 Docker:
  - 资源消耗 < 1/3
  - 启动快 30%
  - 命令兼容 docker
  
仓库: gitee.com/openeuler/iSulad
```

```bash
# openEuler 默认
yum install -y iSulad
systemctl enable --now isulad
isula ps
isula run -d --name web nginx:1.27
isula images
```

### 8.2 PouchContainer（阿里，停止维护）

```
2017-2020 阿里集团内部主流
现并入 containerd 生态
```

### 8.3 龙蜥 / 麒麟 / UOS

```
龙蜥 OS:     默认 containerd + runc
麒麟 V10:    containerd / Docker CE
UOS:        Docker CE / Podman
EulerOS:    iSulad / containerd
```

## 九、内核优化（cgroup v2 + eBPF）

### 9.1 cgroup v2 全面切换

```bash
# GRUB 启用
GRUB_CMDLINE_LINUX="systemd.unified_cgroup_hierarchy=1"
update-grub && reboot

mount | grep cgroup2
cat /sys/fs/cgroup/cgroup.controllers
# cpu io memory hugetlb pids rdma misc

# Docker / containerd 同步
{ "exec-opts": ["native.cgroupdriver=systemd"] }

# K8s kubelet:
--cgroup-driver=systemd
```

### 9.2 资源限额（cgroup v2）

```bash
# 1 CPU
echo "100000 100000" > /sys/fs/cgroup/.../cpu.max

# 内存
echo "536870912" > /sys/fs/cgroup/.../memory.max
echo "268435456" > /sys/fs/cgroup/.../memory.high      # 软上限
echo "0" > /sys/fs/cgroup/.../memory.swap.max          # 禁 swap

# I/O 限额
echo "8:0 rbps=10485760 wbps=10485760 riops=1000 wiops=1000" > /sys/fs/cgroup/.../io.max
```

### 9.3 eBPF 容器可观测

```
工具:
  bpftrace        命令行 eBPF
  Pixie           K8s 全栈可观测 ⭐
  Cilium Tetragon 容器安全监控
  Inspektor Gadget K8s eBPF 工具集
  DeepFlow ⭐     国产 eBPF APM
  
用法:
  - 容器系统调用追踪
  - 容器内网络抓包（无需 tcpdump）
  - 容器逃逸检测
  - 性能 profile
```

```bash
# bpftrace 看哪个容器在 fork
bpftrace -e 'tracepoint:syscalls:sys_enter_clone { @[comm,pid] = count(); }'

# Cilium Tetragon (K8s)
helm install tetragon cilium/tetragon -n kube-system
kubectl apply -f https://raw.githubusercontent.com/cilium/tetragon/main/examples/tracingpolicy/file-monitoring/file-monitoring-filtered.yaml
```

## 十、容器逃逸与加固

### 10.1 常见逃逸路径

```
1. --privileged 跑 + cgroup 释放 / 设备直挂 → 拿主机
2. 挂 /var/run/docker.sock → 控 docker daemon
3. 挂 / 或 /proc 到容器 → 修改 host
4. CAP_SYS_ADMIN / CAP_SYS_MODULE → 加载内核模块
5. user namespace 漏洞 (CVE-2022-0185 等)
6. runc CVE-2019-5736 / 2024-21626 → 必升级
7. Dirty Pipe / Dirty COW 内核漏洞
8. 共享内核漏洞 → 永远存在
```

### 10.2 加固清单

```
☐ runc / containerd 持续升级
☐ Kernel 持续升级（容器逃逸主要靠内核漏洞）
☐ --privileged 禁用（特殊用 Kata / gVisor）
☐ 不挂 docker.sock（除非 sidecar 模式 + 内部）
☐ user namespace 启用 (userns-remap / rootless)
☐ seccomp default profile
☐ AppArmor / SELinux enforce
☐ cap-drop=ALL，按需 add
☐ no-new-privileges:true
☐ pids-limit 防 fork bomb
☐ read-only rootfs
☐ tmpfs noexec,nosuid
☐ K8s 准入: OPA Gatekeeper / Kyverno
☐ Tetragon / Falco 运行时威胁监测
☐ 镜像扫描 + 签名 + Provenance 全链
☐ 高敏感业务: Kata / gVisor / Confidential Containers
```

### 10.3 Falco 运行时威胁监测

```yaml
# K8s DaemonSet
helm install falco falcosecurity/falco -n falco --create-namespace \
  --set tty=true --set driver.kind=ebpf

# 规则示例: 检测 shell in container
- rule: Terminal Shell in Container
  desc: A shell was used as the entrypoint or executed in a container
  condition: container.id != host and proc.name in (bash, sh, zsh, fish)
  output: "Shell in container (user=%user.name container=%container.name image=%container.image.repository)"
  priority: WARNING
```

## 十一、多架构与嵌入式

### 11.1 多架构基础

```
amd64 / arm64 / arm/v7 / ppc64le / s390x / riscv64

# 多平台镜像 = manifest list（fat manifest）
# docker pull 自动按主机 arch 选

docker buildx imagetools inspect nginx:1.27
```

### 11.2 ARM64 / RISC-V

```bash
# ARM64 (鲲鹏 / 飞腾 / 苹果 M / AWS Graviton)
docker buildx build --platform linux/arm64 -t myapp:arm64 --push .

# RISC-V (玄铁 / SiFive / 龙芯)
docker buildx build --platform linux/riscv64 -t myapp:riscv64 --push .

# QEMU 跨架构（开发用，生产用真机）
docker run --privileged tonistiigi/binfmt --install all
```

### 11.3 嵌入式

```
平台:
  - openEuler Embedded
  - Yocto Linux
  - Buildroot
  
容器引擎:
  - iSulad ⭐ (华为，最轻量)
  - balenaEngine (BalenaOS)
  - k3s + containerd (1-2 节点)
  
适用:
  - 工业控制
  - 边缘网关
  - 车载
  - 物联网
```

## 十二、典型生产架构（高级）

### 12.1 AI 训练镜像平台

```
Harbor + Trivy + Cosign
  ├─ pytorch:2.4-cuda12.4-cudnn9 (基础)
  ├─ company/ai-base:1.0 (公司基础)
  └─ project/llm-train:v0.1 (训练镜像)

K8s + NVIDIA GPU Operator + MIG
  ├─ RuntimeClass: nvidia
  ├─ ResourceClass: gpu.nvidia.com/A100-1g.10gb
  └─ 分布式训练: vLLM / Megatron-LM
```

### 12.2 多租户 SaaS

```
K8s 节点池
  ├─ 公共池: containerd + runc + AppArmor
  └─ 高敏池: containerd + kata-cc + SEV-SNP

每租户 namespace + Pod Security Standards
  + Cilium Network Policy
  + Tetragon 实时监控
  + Trivy 镜像扫描
  + cosign 签名准入
```

### 12.3 边缘 IoT

```
鲲鹏 / 飞腾 ARM64 节点
  ├─ openEuler Embedded + iSulad
  ├─ k3s + containerd
  └─ KubeEdge / OpenYurt 云边协同

镜像:
  - 多架构 (amd64+arm64)
  - 最小化 (Wolfi/distroless < 30MB)
  - 离线分发 (Harbor Proxy Cache)
```

### 12.4 信创合规

```
OS:        openEuler 22.03 LTS-SP3 / 麒麟 V10
引擎:      iSulad / containerd
仓库:      Harbor 国密 TLS
扫描:      奇安信 / 启明星辰 / 长亭
签名:      cosign + 国密 HSM
监控:      DeepFlow / 夜莺 + categraf
机密:      kata-cc + 海光 CSV
```

## 十三、典型坑（高级）

| 坑 | 建议 |
|:---|:---|
| **runc 老版本** | runc CVE 频发，必升级 |
| **kata + GPU 直通** | 配置复杂，PCI 直通要 IOMMU |
| **gVisor 性能差** | 仅给不可信代码用 |
| **wasm 生态早期** | 仅 边缘/插件 试点 |
| **CoCo 启动慢** | 内存度量 + KBS 网络可达 |
| **国产 GPU 容器适配差** | 锁版本 + 提前测 |
| **iSulad 命令兼容性** | 部分 docker 子命令缺失 |
| **eBPF 老内核不支持** | Kernel 5.10+，推荐 5.15+ |
| **多架构 build 慢** | QEMU 慢，用真 ARM 节点 |
| **Falco 规则误报多** | 调优 + 白名单 |
| **Tetragon 资源开销** | 高 PPS 节点要评估 |

## 十四、高级 Checklist

```
运行时:
☐ containerd + runc 主线
☐ crun 替代 runc 一节点测试
☐ Kata Containers 多租户
☐ gVisor 不可信代码
☐ Firecracker / Cloud Hypervisor 了解

机密计算:
☐ Confidential Containers PoC
☐ SEV-SNP / TDX / 海光 CSV
☐ 加密镜像 + KBS attestation

构建:
☐ Buildah / Kaniko CI 内
☐ nerdctl 替代 docker
☐ Wasm 边缘试点

GPU:
☐ NVIDIA Container Toolkit
☐ MIG / vGPU 切片
☐ 国产 GPU 一种 (昇腾/摩尔/沐曦)

内核:
☐ cgroup v2 全栈
☐ eBPF 可观测 (Pixie / DeepFlow)
☐ Tetragon / Falco 安全

加固:
☐ runc/containerd 持续升级
☐ user ns / rootless
☐ seccomp + AppArmor
☐ K8s 准入 (Gatekeeper/Kyverno)
☐ 镜像签名 + Provenance

多架构:
☐ amd64 + arm64 双推
☐ Buildx 多 builder
☐ ARM 真机构建池

国产化:
☐ iSulad 一节点
☐ 鲲鹏/飞腾 ARM64 适配
☐ 国产 OS + 国密 TLS
☐ DeepFlow / 夜莺监控
```

## 十五、推荐栈

```
高层运行时:  containerd ⭐ / CRI-O / iSulad (国产嵌入)
低层运行时:  runc (默认) + crun (轻量) + kata (隔离) + gVisor (沙箱) + runwasi (Wasm)
机密:        Kata + CoCo + SEV-SNP/TDX/海光 CSV
构建:        Buildx (本机) + Kaniko (K8s 内) + Buildah/podman + Wolfi base
仓库:        Harbor + Proxy Cache + 多 Region 复制
扫描:        Trivy + Grype + 长亭洞鉴
签名:        cosign + sigstore policy-controller + 国密 HSM
SBOM:        Syft / Trivy → CycloneDX
GPU:        NVIDIA Container Toolkit + GPU Operator + MIG / 昇腾 / 摩尔
内核:        cgroup v2 + eBPF (Pixie / DeepFlow / Tetragon)
安全:        Falco + Tetragon + Gatekeeper/Kyverno + Tetragon
多架构:      Buildx + ARM 真机池
Wasm:        WasmEdge ⭐ / Wasmtime / Spin + runwasi
国产:        iSulad + openEuler/麒麟 + DeepFlow + 国密 + 海光 CSV
```

## 十六、学习路径

```
高级（6-12 月）:
  1. containerd / CRI-O 替换 dockerd
  2. nerdctl / Buildah / podman 替代练习
  3. Kata Containers 部署 + K8s RuntimeClass
  4. gVisor / Firecracker 一种
  5. NVIDIA Container Toolkit + MIG
  6. 国产 GPU 容器（昇腾 / 摩尔）一种
  7. cgroup v2 + eBPF (Tetragon/DeepFlow)
  8. Wasm 容器 WasmEdge 试点
  9. Confidential Containers (PoC, SEV-SNP)
  10. Kaniko CI / Harbor Proxy Cache
  11. iSulad on openEuler 嵌入式
  12. 多架构 (amd64 + arm64) build & deploy
  13. Falco / Tetragon 运行时监控

专家:
  14. 改 runc / containerd 源码 + PR
  15. 国产 OCI 生态贡献 (iSulad / openEuler)
  16. 私有云 + 机密计算 平台架构
```

## 十七、参考资料

```
官方:
  containerd.io ⭐
  cri-o.io
  github.com/opencontainers
  katacontainers.io
  gvisor.dev
  firecracker-microvm.github.io
  confidentialcontainers.org
  wasmedge.org
  
国产:
  gitee.com/openeuler/iSulad
  openeuler.org 容器 SIG
  龙蜥 / 麒麟 容器文档
  DeepFlow github
  华为云 / 阿里云 / 腾讯云 GPU 容器白皮书

经典:
  - 《深入剖析 Kubernetes》(张磊)
  - 《Container Security》Liz Rice
  - 《Linux 内核观测技术 BPF》
  - Cloud Native Security 白皮书

会议:
  - KubeCon (containerd track)
  - CloudNativeCon
  - Open Source Summit
  - 中国容器大会
```

> 📖 **核心判断**：高级 = **containerd/CRI-O 直驱 + 替代低层运行时(crun/kata/gVisor/Firecracker) + Confidential Containers + Buildah/Kaniko/nerdctl + Wasm + GPU 容器(MIG/国产) + cgroup v2/eBPF + 国产 OCI(iSulad) + 多架构 + 加固**。能在白板上画出"containerd + kata-cc + SEV-SNP + KBS"机密计算栈、能配 GPU Operator + MIG + RuntimeClass、能给 K8s 套上 Falco+Tetragon+OPA 三道防线、能在 ARM64+openEuler+iSulad 上跑稳一套，就具备容器平台架构师能力。**容器的未来 = OCI 标准内的运行时多元化 + 机密计算 + Wasm + 国产化**，从一开始就别只盯着 Docker。
