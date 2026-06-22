# CPU

> CPU 是服务器的计算核心。x86 长期主导，**ARM 正在数据中心崛起**，RISC-V 与国产架构紧追其后。

## 一、CPU 架构全景

```
┌─────────── 主流服务器 CPU 架构 ───────────┐
│                                          │
│   x86-64 (CISC)         ARM64 (RISC)     │
│   Intel / AMD           Ampere / 鲲鹏     │
│                         AWS Graviton     │
│                         阿里倚天 / Apple  │
│                                          │
│   RISC-V (RISC, 开源)    LoongArch / SW64 │
│   SiFive / 平头哥         国产自研          │
│                                          │
└──────────────────────────────────────────┘

主要差异:
  CISC: 指令复杂多变长，硬件解码翻译为 μops
  RISC: 指令定长简洁，软件编译器优化
```

## 二、核心概念

| 概念 | 说明 |
|:---|:---|
| **物理核** | 实际存在的硬件核心 |
| **逻辑核** | 超线程（SMT）模拟，x86 通常 1:2，ARM 多数 1:1 |
| **NUMA** | 多 Socket 服务器跨节点访存延迟不一致 |
| **L1/L2/L3 缓存** | 三级缓存层次，L1 最快、L3 共享 |
| **MMU/TLB** | 虚拟地址翻译 |
| **指令集扩展** | AVX-512 / AMX (x86)、SVE2 / SME (ARM) |
| **大小核** | Apple/ARM 移动端做法，服务器少见 |

## 三、x86 架构

### 3.1 Intel Xeon

| 系列 | 代号 | 时期 | 特点 |
|:---|:---|:---|:---|
| Xeon Scalable Gen2 | Cascade Lake | 2019 | DL Boost |
| Gen3 | Ice Lake-SP | 2021 | 10nm、PCIe 4.0 |
| Gen4 | Sapphire Rapids | 2023 | DDR5、CXL 1.1、AMX |
| Gen5 | Emerald Rapids | 2024 | 性能提升 21% |
| Gen6 | Granite Rapids / Sierra Forest | 2024-2025 | **288 核 E-core 服务器版** |

**AMX（Advanced Matrix Extensions）**：x86 首次内置矩阵加速，CPU 上跑 INT8/BF16 推理性能 ×3-8。

### 3.2 AMD EPYC

| 系列 | 代号 | 时期 | 关键特性 |
|:---|:---|:---|:---|
| EPYC 7002 | Rome | 2019 | 7nm、Chiplet 革命 |
| 7003 | Milan | 2021 | Zen3、3D V-Cache（X 版本） |
| 9004 | Genoa | 2022 | 96 核、DDR5、CXL |
| 9005 | Turin | 2024 | **192 核 Zen5c**、3nm |
| 9V64H 等 | Genoa-X | 2024 | 1.1GB L3，HPC 杀手 |

**Chiplet 架构**：用多颗小芯片拼接降低成本提升良率，AMD 借此实现性能反超 Intel。

### 3.3 x86 主流场景

| 场景 | 推荐 |
|:---|:---|
| 通用虚拟化 | EPYC 9004/9005（性价比高） |
| AI 推理（CPU） | Xeon Gen4+（AMX） |
| HPC | EPYC X 系列（大 L3） |
| 数据库 OLTP | Xeon Gen5（频率高） |
| 大规模容器 | EPYC（核多） |

## 四、ARM 架构（重点）

### 4.1 ARM 进入数据中心简史

| 年份 | 事件 |
|:---|:---|
| 2008 | ARMv8-A 发布，引入 64 位 |
| 2018 | AWS Graviton 1 发布（试水） |
| 2019 | Graviton 2 性能/价格比震惊业界 |
| 2020 | Apple M1 PC 转向 ARM |
| 2021 | Ampere Altra Max（128 核） |
| 2022 | 阿里倚天 710 上线 |
| 2024 | Graviton 4、Ampere One、NVIDIA Grace |
| 2025 | ARM 数据中心市占率突破 15% |

### 4.2 ARM 关键架构特性

```
ARMv8-A → ARMv9-A
   ↓
   ├── SVE / SVE2 (可伸缩向量，128-2048 bit)
   ├── SME (矩阵扩展，对标 AMX)
   ├── Confidential Compute Architecture (CCA)
   ├── Memory Tagging Extension (MTE，内存安全)
   ├── 大页 16K/64K 默认（x86 通常 4K）
   └── 弱内存模型（性能优势，但需软件适配）
```

### 4.3 主流服务器 ARM 产品

| 厂商 | 产品 | 核心数 | 工艺 | 应用 |
|:---|:---|:---:|:---:|:---|
| **AWS** | Graviton 4 | 96 | 4nm | AWS EC2 主力 |
| **NVIDIA** | Grace CPU | 72 | 4nm（Neoverse V2） | Grace Hopper、Grace Blackwell |
| **Ampere** | AmpereOne | 192 | 5nm | Oracle Cloud / Azure |
| **Microsoft** | Cobalt 100 | 128 | — | Azure 自研 |
| **Google** | Axion | — | — | GCP 自研 |
| **阿里** | 倚天 710 | 128 | 5nm | 阿里云 g8y 实例 |
| **华为** | 鲲鹏 920 | 64 | 7nm | 信创主力 |
| **飞腾** | S5000C | 64 | — | 政企信创 |
| **Apple** | M2/M3 Ultra | 24+ | 3nm | Mac Studio/Pro（边缘服务器） |

### 4.4 x86 vs ARM 服务器对比

| 维度 | x86（EPYC/Xeon） | ARM（Graviton/Ampere） |
|:---|:---|:---|
| **架构** | CISC，硬件解码 | RISC，编译器优化 |
| **核心数** | 64-192 | 96-192 |
| **单核性能** | 高（频率 3.0-4.0G） | 中（频率 2.5-3.0G） |
| **多核扩展** | 强 | 极强（每核功耗低）|
| **功耗** | 高（350W+） | 低（200-280W） |
| **性价比** | 一般 | 高（云上节省 20-40%） |
| **软件生态** | 极成熟 | 95% 已适配 |
| **AI 推理** | AMX 强 | SME 起步 |
| **NUMA 复杂度** | 多 Socket 复杂 | 单 Socket 大核足够 |
| **典型应用** | 兼容性优先场景 | 云原生、Web、JVM、Go |

### 4.5 ARM 软件生态现状

```
✅ 已完美适配:
  - Linux 主流发行版（Ubuntu/RHEL/openEuler/Anolis）
  - 容器生态：Docker/containerd/K8s 全部多架构镜像
  - JVM 语言：Java/Scala/Kotlin（性能等同甚至更好）
  - Go / Rust / Python / Node.js
  - 主流中间件：MySQL/PostgreSQL/Redis/Kafka/Nginx
  - 主流 CI/CD：Jenkins/GitLab CI/GitHub Actions

⚠️ 部分场景需关注:
  - Oracle DB（已支持但 License 注意）
  - 商业软件二进制（需厂商提供 ARM 版）
  - 老旧 C/C++ 项目（汇编/SSE 内联代码）
  - x86 only 的 Docker 镜像（构建多架构）
  - 部分 AI 库（CUDA 在 NVIDIA Grace 上可用）

❌ 兼容性差:
  - 闭源 x86 二进制商业软件
  - 老旧 Windows 应用（除非 Windows on ARM）
```

### 4.6 ARM 迁移要点（运维角度）

| 步骤 | 关键动作 |
|:---|:---|
| **1. 评估** | 列出全部依赖软件，确认 ARM 支持 |
| **2. 镜像** | `docker buildx` 构建 `linux/amd64,linux/arm64` 多架构 |
| **3. 编译** | C/C++ 项目重编译，注意 SSE/AVX 内联汇编 |
| **4. 测试** | 性能基准（不要只看 CPU 利用率） |
| **5. 监控** | CPU/Mem 指标语义一致，PMU 不同 |
| **6. 灰度** | 先无状态服务，再 JVM/中间件，最后数据库 |

### 4.7 鲲鹏适配（信创场景）

```bash
# 查看架构
uname -m              # aarch64
lscpu | grep -i arch  # ARM64

# 容器多架构
docker buildx build --platform linux/amd64,linux/arm64 -t app:v1 .

# 跨架构二进制运行（开发场景）
docker run --rm --platform linux/amd64 amd64-image  # qemu 模拟，慢
```

**鲲鹏专项**：
- 软件栈：openEuler / 麒麟 V10 / UOS
- 编译器：BiSheng Compiler（华为，基于 LLVM）
- 优化工具：Kunpeng DevKit（性能分析、迁移检测）

## 五、RISC-V（前瞻）

| 维度 | 状态 |
|:---|:---|
| **架构** | 开源指令集，模块化 |
| **服务器代表** | SiFive P870、阿里平头哥玄铁 C910/C920 |
| **生态** | Linux 内核支持完善，Debian/Fedora 已有 port |
| **现状** | 嵌入式主流，服务器起步 |
| **何时进数据中心** | 2027-2030 |

## 六、国产服务器 CPU

| 厂商 | 产品 | 架构 | 现状 |
|:---|:---|:---|:---|
| **华为** | 鲲鹏 920 | ARMv8 自研 | 信创主力 |
| **阿里** | 倚天 710 | ARMv9 | 阿里云内部大规模 |
| **飞腾** | 腾云 S5000C | ARMv8 | 政府/电信 |
| **海光** | C86 | x86（AMD 授权） | 金融 |
| **兆芯** | KH-40000 | x86 | 政企 |
| **龙芯** | 3C5000/6000 | LoongArch（自研） | 党政自主可控 |
| **申威** | SW26010 | SW64（自研） | 超算（神威·太湖之光） |

> 💡 **信创采购**：通常选 鲲鹏 / 飞腾 / 海光 / 龙芯 中至少 2 家，避免单一供应商。

## 七、关键指标

| 指标 | 说明 | 关注度 |
|:---|:---|:---:|
| 主频 (GHz) | 基础频率 + 睿频 | 高 |
| 物理核心数 | 多任务、多容器关键 | 高 |
| L3 缓存 | 数据库、HPC 敏感 | 中-高 |
| TDP (W) | 散热与电费 | 中 |
| 内存通道 | 8/12 通道，带宽决定 | 高 |
| PCIe 版本 | Gen4/Gen5，影响 GPU/NVMe | 高 |
| 指令集 | AVX-512/AMX/SVE2/SME | AI 场景关键 |
| Socket 数 | 1P/2P，NUMA 复杂度 | 中 |

## 八、CPU 选型决策树

```
是否信创/合规要求？
├── 是 → 鲲鹏 / 飞腾 / 海光 / 龙芯
└── 否
    ├── 公有云 → 优先 ARM 实例（性价比）
    │             AWS Graviton / 阿里倚天 / Azure Cobalt
    └── 自建机房
        ├── 极致单核（数据库主） → Intel Xeon 高频
        ├── 极致核数（容器密度） → AMD EPYC / Ampere
        ├── CPU 推理 → Intel Sapphire Rapids+（AMX）
        ├── HPC → AMD EPYC X 系列（3D V-Cache）
        └── 通用混合 → AMD EPYC 9004/9005
```

## 九、运维要点

```
# 通用查看
lscpu                     # 架构、核心、缓存
cat /proc/cpuinfo         # 详细信息
nproc                     # 核心数

# NUMA
numactl --hardware        # NUMA 拓扑
numastat                  # NUMA 命中率

# 性能
perf stat -- <cmd>        # 性能计数器
turbostat                 # 频率/功耗（Intel）

# ARM 特有
cat /proc/cpuinfo | grep Feature   # 查看 SVE/SVE2 支持
dmidecode -t processor              # SMBIOS 信息
```

## 十、未来 3 年趋势

| 方向 | 预测 |
|:---|:---|
| **ARM 占比** | 数据中心市占 15% → 30% |
| **核数竞赛** | 单 Socket 突破 256 核 |
| **CXL 普及** | CPU 内存池化（CXL 2.0/3.0） |
| **AI on CPU** | AMX/SME 让小模型推理回归 CPU |
| **能效优先** | 单核能效成关键指标 |
| **国产 ARM** | 鲲鹏/倚天等占信创 60%+ |
| **RISC-V 试水** | 边缘场景小规模生产 |

> 📖 **核心结论**：x86 仍是主流，但**新建系统强烈建议同步评估 ARM**。云上 ARM 实例已经是默认选项之一，自建机房 2-3 年内也会迎来 ARM 浪潮。
