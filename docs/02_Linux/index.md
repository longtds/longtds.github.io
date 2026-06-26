# 02. Linux

> Linux 是云原生 / AI / AIOps 的底座。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，覆盖从命令行到内核、从单机到集群、从开源到国产化的完整知识链。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入职 1 年内 | 命令行 / 文件 / 权限 / 进程 / systemd 入门 / 网络基础 / 包管理 / Shell 基础 |
| [02_进阶](02_进阶/README.md) | 独立运维 5-50 台 | systemd 深度 / LVM/RAID/XFS / ACL/Capability / SELinux / 网络配置 / 调优入门 / Shell 中级 |
| [03_高级](03_高级/README.md) | SRE 技术担当 | perf 火焰图 / bpftrace + BCC / cgroup v2 + namespace / nftables / NUMA / 内核调优 / 国产 OS 适配 |
| [04_最佳实践](04_最佳实践/README.md) | 团队负责人 | SRE 三件套 / Ansible IaC / Prometheus 监控 / 备份 DR / 安全基线 / 国产化选型 / Toolbox |
| [99_发展与展望](99_发展与展望.md) | 所有人 | eBPF + Rust + io_uring 三剑客 / 国产 OS + ARM/LoongArch / AI Native OS / 5 年趋势判断 |

## 学习路径

```
入门 (1-3 月)
  └─ 01_基础: 50 个核心命令 + 入门必练 30 题

进阶 (3-12 月)
  └─ 02_进阶: 写出生产级 systemd unit + LVM/RAID + Shell 严格模式

高级 (1-2 年)
  └─ 03_高级: bpftrace 一行排查 + 火焰图 + cgroup v2 手撸 + nftables + 国产 OS

工程化 (2-3 年)
  └─ 04_最佳实践: SLO + 告警 + 备份演练 + 平台化

展望 (持续)
  └─ 99_发展与展望: 紧跟内核新特性 + 国产化 + AI Native
```

## 核心判断

```
学习心法:
  1. 80% 问题用基础命令解决，别上来就 bpftrace
  2. 火焰图 + USE 方法论 比记 100 个工具有用
  3. Shell 写完用 shellcheck，过百行考虑 Python
  4. 国产 OS 必选一种深度掌握（推 openEuler / Anolis）
  5. 一切配置入 Git → 一切运维 IaC 化
  6. eBPF + Rust + io_uring 是下一代必学

红线:
  ❌ chmod 777, rm -rf /, 直接 vim /etc/sudoers
  ❌ Shell 不加 set -euo pipefail
  ❌ 备份不做恢复演练
  ❌ 告警不可操作 / 噪音泛滥
  ❌ SSH 用 root + 密码 + 无 fail2ban
  ❌ 业务高峰发布 / 无回滚预案
```

## 相关章节

- 配合 [01_服务器](../01_服务器/index.md) 看硬件基线
- 配合 [03_网络](../03_网络/index.md) 看协议栈
- 配合 [06_Docker](../06_Docker/index.md) / [07_Kubernetes](../07_Kubernetes/index.md) 看容器底座
- 配合 [08_DevOps](../08_DevOps/index.md) 看 CI/CD + Ansible
- 配合 [12_AIOps](../12_AIOps/index.md) 看智能运维
- 配合 [14_安全](../14_安全/index.md) 看 Linux 安全基线
- 配合 [16_故障排查](../16_故障排查/index.md) 看实战兜底

