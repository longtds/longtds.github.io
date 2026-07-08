# Linux 服务器从按下开机到完全启动全过程

> 按下电源按钮后，服务器经历了什么？从上电自检到 systemd 拉起所有服务，逐阶段拆解每一步发生了什么、卡住了怎么排查。

---

## 一、启动全景图

```
按下电源按钮
    │
    ▼
┌─────────────────────────────────┐
│ 阶段 1: 硬件上电 (Power On)      │  ~1-3 秒
│ BMC 启动 → PSU 上电 → 主板通电    │
└──────────────┬──────────────────┘
               │
    ▼
┌─────────────────────────────────┐
│ 阶段 2: BMC/带外初始化            │  ~10-30 秒
│ BMC 固件加载 → 传感器初始化        │
└──────────────┬──────────────────┘
               │
    ▼
┌─────────────────────────────────┐
│ 阶段 3: BIOS/UEFI POST           │  ~10-60 秒
│ CPU 初始化 → 内存训练 → 设备扫描   │
└──────────────┬──────────────────┘
               │
    ▼
┌─────────────────────────────────┐
│ 阶段 4: 引导设备选择              │  ~1-3 秒
│ Boot Order → 选择启动设备         │
└──────────────┬──────────────────┘
               │
    ▼
┌─────────────────────────────────┐
│ 阶段 5: 引导加载器 (Bootloader)   │  ~2-10 秒
│ GRUB → 加载内核 + initramfs       │
└──────────────┬──────────────────┘
               │
    ▼
┌─────────────────────────────────┐
│ 阶段 6: 内核启动                  │  ~5-30 秒
│ 内核初始化 → 驱动加载 → 挂载根分区  │
└──────────────┬──────────────────┘
               │
    ▼
┌─────────────────────────────────┐
│ 阶段 7: systemd 初始化           │  ~10-60 秒
│ 拉起服务 → 网络配置 → 用户登录     │
└──────────────┬──────────────────┘
               │
    ▼
   系统就绪, 可以 SSH 登录
```

**总耗时：** 正常 1-3 分钟，首次上电或内存训练可能 5-10 分钟。

---

## 二、阶段 1-2：硬件上电与 BMC 初始化

### 2.1 按下电源按钮后发生了什么

```
1. 电源按钮触发 BMC 的 Power Button 信号
2. BMC 检查 PSU 状态 (电源冗余、功耗预算)
3. BMC 发送 PS_ON 信号给 PSU
4. PSU 开始输出 +12V/+5V/+3.3V
5. 主板 VRM (电压调节模块) 逐步加压:
   - 先给 BMC 供电 (3.3V STBY → 1.8V → 1.2V)
   - 再给 CPU 供电 (VCCIN → VCCSA → VCCIO)
   - 最后给内存供电 (VDDQ → VPP)
6. BMC 读取 CPLD/FPGA 状态确认各路电压就绪
7. BMC 发送 RST_PWRBTN 信号 → CPU 复位引脚释放
8. CPU 开始执行 (从 Flash/ROM 中取第一条指令)
```

### 2.2 BMC 先于系统启动

BMC（Baseboard Management Controller）是一个独立的小芯片（通常 ARM 处理器），有自己的固件、内存和网口。**BMC 和主 CPU 是并行运行的：**

```
┌─────────────────────────────────────────┐
│              服务器主板                   │
│                                         │
│  ┌─────────┐        ┌──────────────┐    │
│  │  BMC    │◄──────►│  主 CPU      │    │
│  │ (ARM)   │  IPMI  │  (x86/ARM)   │    │
│  │         │  SMBus  │              │    │
│  │ 独立固件 │  I2C   │  运行 Linux   │    │
│  │ 独立网口 │        │              │    │
│  └────┬────┘        └──────┬───────┘    │
│       │                    │             │
│  ┌────▼────┐        ┌──────▼───────┐    │
│  │传感器监控│        │   内存/磁盘    │    │
│  │温度/风扇 │        │   GPU/网卡     │    │
│  └─────────┘        └──────────────┘    │
└─────────────────────────────────────────┘
```

| BMC 功能 | 说明 |
|:---|:---|
| 远程开关机 | `ipmitool chassis power on/off/cycle` |
| 远程 KVM | 浏览器看到服务器画面 |
| 虚拟媒体 | 网络挂载 ISO |
| 传感器监控 | 温度/风扇/电压/功耗 |
| 事件日志 (SEL) | 硬件事件记录 |
| 告警通知 | SNMP Trap / Email / SMTP |

**BMC 卡住的表现：** BMC Web 打不开、IPMI 不通、远程 KVM 黑屏，但系统可能正常运行。

### 2.3 这个阶段卡住怎么排查

| 现象 | 可能原因 | 排查方法 |
|:---|:---|:---|
| 按电源没反应 | PSU 故障 / BMC 挂死 | 拔电源等 30 秒重新插上 → BMC 冷启动 |
| 电源灯闪琥珀色 | PSU 冗余失效 / 电压异常 | 检查 PSU 状态灯，更换 PSU |
| BMC Web 打不开 | BMC 固件损坏 / IP 冲突 | 直连 BMC 网口，默认 IP 尝试 |
| 风扇狂转不减速 | BMC 未完成初始化 | 等 2-3 分钟，或 BMC 固件升级 |
| 诊断灯亮红灯 | 硬件故障（CPU/内存/PCIe） | 看诊断灯代码对照手册 |

---

## 三、阶段 3：BIOS/UEFI POST

### 3.1 POST（Power-On Self-Test）流程

```
CPU 复位释放
    │
    ▼
1. CPU 从固定地址 (0xFFFFFFF0) 取第一条指令
   → 跳转到 BIOS/UEFI 固件入口
    │
    ▼
2. BIOS/UEFI 固件初始化
   → 初始化芯片组 (PCH/南桥)
   → 配置 CPU 微码 (Microcode)
   → 初始化 PCIe 总线
    │
    ▼
3. CPU 自检
   → 检测 CPU 型号/步进/频率
   → 多路 CPU 互连 (QPI/UPI) 拓扑发现
   → 加载微码更新
    │
    ▼
4. 内存训练 (Memory Training) ← 最耗时的步骤
   → 内存控制器初始化
   → 内存频率/时序协商
   → 内存通道映射 (1DPC/2DPC/3DPC)
   → 逐条内存测试 (Read/Write/Margin)
   → 128GB 内存约 30-60 秒
   → 1TB 内存可能 3-5 分钟
    │
    ▼
5. 设备扫描
   → PCIe 设备枚举 (分配 BAR/IRQ)
   → RAID 卡 / HBA 初始化
   → 网卡初始化 (PXE Option ROM)
   → NVMe 设备发现
   → USB 控制器初始化
    │
    ▼
6. Option ROM 执行
   → RAID 卡 BIOS (Ctrl+R 提示)
   → 网卡 PXE ROM (Ctrl+S 提示)
   → BMC 初始化完成 (BMC IP 显示)
    │
    ▼
7. POST 完成
   → 蜂鸣器一声短响 (正常)
   → 进入引导设备选择
```

### 3.2 UEFI vs Legacy BIOS

| 维度 | Legacy BIOS | UEFI |
|:---|:---|:---|
| 固件存储 | 512KB Flash | 16-64MB SPI Flash |
| 分区表 | MBR (≤2TB) | GPT (支持 >2TB) |
| 引导方式 | 16 位实模式 → MBR → bootloader | UEFI 应用 → EFI 分区 → bootloader |
| 驱动模型 | Option ROM (16 位) | UEFI Driver (64 位) |
| Secure Boot | ❌ | ✅ |
| 启动速度 | 慢 | 快 (并行初始化) |
| 网络引导 | PXE (TFTP) | HTTP Boot / PXE |
| 最大磁盘 | 2TB (MBR) | 9.4ZB (GPT) |
| Shell | ❌ | UEFI Shell |
| 图形界面 | 文字菜单 | 鼠标 GUI |

**2020 年后的服务器全部用 UEFI。** Legacy BIOS 仅用于兼容老系统和特殊硬件。

### 3.3 POST 阶段卡住的表现与排查

| 现象 | 可能原因 | 排查 |
|:---|:---|:---|
| 卡在内存训练 | 内存条故障 / 不兼容 / 插法不对 | 拔插内存，逐条测试 |
| 卡在 "Press Ctrl+R" | RAID 卡故障 / 磁盘冲突 | 拔掉所有磁盘看是否过 |
| 蜂鸣器长响 | 内存未正确安装 | 重新插拔内存 |
| 蜂鸣器 3 短 1 长 | 显卡/显示问题 | 检查 BMC KVM |
| POST 代码停在某个值 | 硬件故障 | 查主板诊断 LED 代码 |
| 反复重启 | CPU/内存/主板严重故障 | 最小化配置（1 CPU + 1 内存）测试 |

!!! tip "POST 诊断代码"
    服务器主板有 7 段数码管显示 POST 代码。不同厂商代码不同：
    - Lenovo: `01`=CPU, `19`=内存, `B2`=PCIe, `A0`=完成
    - Dell: `CPU`=CPU故障, `MEM`=内存故障, `PCIe`=PCIe故障
    - Supermicro: 查手册对应代码表

---

## 四、阶段 4：引导设备选择

### 4.1 Boot Order 流程

```
POST 完成
    │
    ▼
BIOS/UEFI 读取 Boot Order 配置
    │
    ├─① 尝试第一引导设备 → 设备不可用 → 继续下一个
    ├─② 尝试第二引导设备 → 设备不可用 → 继续下一个
    ├─③ 尝试第三引导设备 → 找到引导程序 → 执行
    │
    ▼
引导设备类型 (UEFI 模式):
  - \EFI\BOOT\BOOTX64.EFI  (默认 UEFI 引导文件)
  - \EFI\rocky\shimx64.efi  (Rocky 特定)
  - \EFI\ubuntu\grubx64.efi  (Ubuntu 特定)
  - \EFI\redhat\shimx64.efi  (RHEL 特定)

引导设备类型 (Legacy 模式):
  - MBR 第一扇区 (512 字节)
  → 跳转到引导代码 (如 GRUB Stage 1)
```

### 4.2 UEFI 引导项管理

```bash
# 查看 UEFI 引导项
efibootmgr

# 输出示例:
# BootCurrent: 0001
# BootOrder: 0001,0000,0002
# Boot0000* UiApp
# Boot0001* Rocky Linux   (HD(1,GPT,...)/File(\EFI\rocky\shimx64.efi))
# Boot0002* UEFI: USB Disk

# 添加引导项
efibootmgr -c -d /dev/nvme0n1 -p 1 \
    -L "Rocky Linux" \
    -l '\EFI\rocky\shimx64.efi'

# 修改引导顺序
efibootmgr -o 0001,0000,0002

# 删除引导项
efibootmgr -b 0002 -B

# 设置下次引导 (一次性)
efibootmgr -n 0002
```

### 4.3 这个阶段的问题

| 问题 | 原因 | 解决 |
|:---|:---|:---|
| No bootable device | 磁盘没有引导程序 | 重装 GRUB 或重装系统 |
| 找不到系统盘 | RAID 虚拟盘未设为引导盘 | RAID 配置中设 Boot Volume |
| PXE 引导但无系统 | Boot Order 网络优先 | BIOS 改为硬盘优先 |
| UEFI 找不到引导项 | NVRAM 引导项丢失 | `efibootmgr -c` 重建 |
| Secure Boot 阻止 | 内核未签名 | 关闭 Secure Boot 或注册 MOK |

---

## 五、阶段 5：引导加载器（GRUB2）

### 5.1 GRUB2 启动流程

```
UEFI 找到 shimx64.efi / grubx64.efi (Legacy: MBR → GRUB Stage 1.5 → Stage 2)
    │
    ▼
GRUB2 核心加载
    │
    ▼
读取 GRUB 配置文件:
  UEFI: /boot/efi/EFI/rocky/grub.cfg (指向真正的 grub.cfg)
  → /boot/grub2/grub.cfg (主配置)
    │
    ▼
显示引导菜单 (如果有多个内核)
    │
    ├─ 用户选择 → 倒计时 5 秒 → 自动选择默认
    │
    ▼
加载内核:
  linux16 /boot/vmlinuz-5.14.0-xxx root=/dev/mapper/rl-root ro crashkernel=auto ...
    │
    ▼
加载 initramfs:
  initrd16 /boot/initramfs-5.14.0-xxx.img
    │
    ▼
跳转到内核入口点 → GRUB 使命完成
```

### 5.2 GRUB 配置文件结构

```bash
# 主配置: /boot/grub2/grub.cfg (UEFI: /boot/efi/EFI/rocky/grub.cfg 指向它)
# 不要直接编辑！用 grub2-mkconfig 生成

# 源配置: /etc/default/grub
GRUB_TIMEOUT=5                          # 菜单倒计时
GRUB_DISTRIBUTOR="Rocky Linux"
GRUB_DEFAULT=saved                      # 默认启动项
GRUB_DISABLE_SUBMENU=true
GRUB_TERMINAL_OUTPUT="console"
GRUB_CMDLINE_LINUX="crashkernel=auto resume=/dev/mapper/rl-swap rd.lvm.lv=rl/root rd.lvm.lv=rl/swap"
GRUB_DISABLE_RECOVERY="true"
GRUB_ENABLE_BLSCFG="true"               # BLS (Boot Loader Spec) 模式

# 生成配置:
grub2-mkconfig -o /boot/grub2/grub.cfg
# UEFI:
grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg
```

### 5.3 内核命令行参数详解

```
linux16 /boot/vmlinuz-5.14.0-503.el9.x86_64 \
    root=/dev/mapper/rl-root \           ← 根分区设备
    ro \                                   ← 只读挂载 (systemd 后面重挂 rw)
    crashkernel=auto \                     ← 预留 kdump 内存
    resume=/dev/mapper/rl-swap \           ← 休眠恢复分区
    rd.lvm.lv=rl/root \                    ← initramfs 中激活 LVM
    rd.lvm.lv=rl/swap \                    ← initramfs 中激活 swap LV
    rd.luks.uuid=luks-xxx \               ← LUKS 加密分区 (如有)
    rhgb quiet \                           ← 图形启动动画 + 隐藏内核日志
    net.ifnames=0 \                        ← 网卡名用 eth0 (不用 eno1)
    biosdevname=0 \                        ← 同上
    systemd.unit=emergency.target \        ← 启动到紧急模式 (临时)
    enforcing=0 \                          ← 临时关闭 SELinux
    nomodeset \                            ← 不加载 GPU 驱动 (排障用)
    maxcpus=1 \                            ← 限制 CPU 数 (排障用)
    init=/bin/bash                         ← 跳过 systemd 直接进 bash (救急)
```

### 5.4 GRUB 阶段问题排查

```bash
# 进入 GRUB 命令行 (菜单按 'c')
# 手动引导 (当 grub.cfg 损坏时):

grub> ls                                    # 列出所有设备
grub> ls (hd0,gpt2)/                         # 查看 /boot 分区
grub> set root=(hd0,gpt2)
grub> linux /vmlinuz-5.14.0-503.el9.x86_64 root=/dev/mapper/rl-root ro
grub> initrd /initramfs-5.14.0-503.el9.x86_64.img
grub> boot

# 或者 UEFI:
grub> ls (hd0,gpt1)/EFI/rocky/
grub> configfile (hd0,gpt1)/EFI/rocky/grub.cfg
```

| 问题 | 原因 | 解决 |
|:---|:---|:---|
| GRUB 救援模式 `grub rescue>` | grub.cfg 丢失 / 分区变了 | 手动加载内核或重装 GRUB |
| error: unknown filesystem | 分区格式变了 (如 ext4→xfs) | 加载对应模块 `insmod xfs` |
| error: disk not found | 磁盘顺序变了 | `ls` 找到正确磁盘 |
| 卡在 GRUB 菜单不动 | GRUB_TIMEOUT 未设置 | 编辑 `/etc/default/grub` |

---

## 六、阶段 6：内核启动

### 6.1 内核初始化流程

```
GRUB 跳转到内核入口
    │
    ▼
1. 内核解压 (如果内核是压缩的)
   → vmlinuz = vmlinux (压缩) + 解压代码
   → x86_64 通常用 zstd/gzip 压缩
    │
    ▼
2. 内核早期初始化 (head_64.S)
   → 设置页表 (4级/5级分页)
   → 初始化 IDT (中断描述符表)
   → 检测 CPU 特性 (CPUID)
   → 设置 GDT (全局描述符表)
    │
    ▼
3. start_kernel() — C 语言入口
   → 初始化调度器
   → 初始化内存管理 (buddy system)
   → 初始化中断子系统
   → 解析内核命令行参数
   → 初始化控制台 (console_init) ← 此后能看到内核日志
    │
    ▼
4. 驱动初始化
   → 内置驱动 (built-in): 直接初始化
   → 模块驱动 (module): 在 initramfs 中加载
   → 设备树/ACPI 解析 → 发现硬件 → 加载对应驱动
    │
    ▼
5. 挂载 initramfs
   → 解压 initramfs 到 tmpfs
   → 执行 /init (通常是 dracut 生成的脚本)
    │
    ▼
6. initramfs 中的早期用户空间
   → 加载存储驱动 (megaraid_sas, nvme, ext4/xfs)
   → 激活 LVM / 解锁 LUKS
   → 找到 root= 指定的根分区
   → 挂载根分区 (先 ro 只读)
   → pivot_root / switch_root → 切换到真正的根文件系统
    │
    ▼
7. 执行 /sbin/init (systemd)
```

### 6.2 initramfs 的作用

```
为什么需要 initramfs?

内核本身只包含最基础的驱动。但根分区可能在:
  - RAID 虚拟盘上 (需要 megaraid_sas 驱动)
  - LVM 逻辑卷上 (需要 device-mapper)
  - LUKS 加密分区 (需要 dm-crypt)
  - NFS 网络存储 (需要网卡驱动 + NFS)

initramfs 就是一个微型根文件系统, 包含:
  - 存储驱动 (megaraid_sas, nvme, dm_mod, xfs)
  - 网络驱动 (mlx5_core, ixgbe) — 网络引导时需要
  - LVM/LUKS 工具
  - busybox/dracut 工具集
  - /init 脚本

它的工作:
  1. 加载必要的驱动
  2. 找到并挂载真正的根分区
  3. 把控制权交给 /sbin/init
```

### 6.3 查看内核启动日志

```bash
# 查看本次启动的完整内核日志
dmesg

# 或
journalctl -k

# 查看上次启动 (崩溃后排查)
journalctl -k -b -1

# 查看启动耗时分布
systemd-analyze
systemd-analyze blame | head -20
systemd-analyze critical-chain
```

### 6.4 内核阶段卡住的表现

| 现象 | 原因 | 排查 |
|:---|:---|:---|
| 黑屏无输出 | rhgb quiet 隐藏了日志 | GRUB 编辑去掉 `rhgb quiet` |
| 卡在 "Loading initial ramdisk" | initramfs 损坏 / 太大 | 重建 initramfs |
| kernel panic - not syncing: VFS | 根分区找不到 / 驱动缺失 | 检查 root= 参数和 initramfs 驱动 |
| kernel panic - not syncing: Attempted to kill init | init 进程崩溃 | `init=/bin/bash` 进入救急 |
| 卡在某个驱动加载 | 硬件故障 / 驱动 bug | `modprobe.blacklist=xxx` 禁用 |
| 反复重启 | kernel panic + 自动重启 | 去掉内核参数中的 `panic=` |

```bash
# 重建 initramfs (驱动问题)
# 先确认需要的驱动:
lsinitrd /boot/initramfs-$(uname -r).img | grep megaraid

# 添加驱动到 initramfs:
dracut --force --add-drivers "megaraid_sas nvme" /boot/initramfs-$(uname -r).img $(uname -r)

# 验证:
lsinitrd /boot/initramfs-$(uname -r).img | grep megaraid
```

---

## 七、阶段 7：systemd 初始化

### 7.1 systemd 启动流程

```
内核执行 /sbin/init → 实际是 systemd
    │
    ▼
1. systemd 读取默认启动目标
   → /etc/systemd/system/default.target
   → 通常链接到 multi-user.target (CLI) 或 graphical.target (GUI)
    │
    ▼
2. 按依赖关系拉起服务
   → 并行启动无依赖的服务
   → 按 After= / Requires= / Wants= 排序
    │
    ▼
3. 启动顺序 (大致):
   ┌──────────────────────────────────────────────┐
   │ 早期阶段 (sysinit.target)                     │
   │   - 挂载 /proc /sys /dev /tmp /var            │
   │   - 加载 SELinux 策略                          │
   │   - 设置主机名                                  │
   │   - 配置内核参数 (sysctl)                      │
   │   - 初始化 RNG (随机数生成器)                   │
   ├──────────────────────────────────────────────┤
   │ 网络阶段 (network.target)                      │
   │   - NetworkManager / networkd 启动              │
   │   - 网卡 UP → DHCP → 获取 IP                    │
   │   - DNS 配置                                   │
   │   - 防火墙规则 (firewalld/nftables)            │
   ├──────────────────────────────────────────────┤
   │ 存储阶段 (storage.target)                      │
   │   - 挂载 /etc/fstab 中的分区                    │
   │   - 激活 swap                                  │
   │   - LVM/RAID 检查                              │
   │   - 文件系统检查 (fsck)                        │
   ├──────────────────────────────────────────────┤
   │ 服务阶段 (multi-user.target)                   │
   │   - sshd (SSH 服务)                            │
   │   - crond (定时任务)                           │
   │   - rsyslog (系统日志)                         │
   │   - chronyd (时间同步)                         │
   │   - docker/containerd (容器运行时)              │
   │   - kubelet (K8s 节点代理)                     │
   │   - 应用服务...                                │
   ├──────────────────────────────────────────────┤
   │ 登录阶段 (getty.target)                        │
   │   - 启动 getty (终端登录提示)                   │
   │   - SSH 可接受连接                              │
   └──────────────────────────────────────────────┘
```

### 7.2 启动目标（Target）

```bash
# 查看默认目标
systemctl get-default
# multi-user.target  → 多用户命令行 (服务器标准)
# graphical.target   → 图形界面

# 查看当前运行的 target
systemctl list-units --type=target

# 切换目标 (临时)
systemctl isolate rescue.target      # 救援模式 (单用户, 需要密码)
systemctl isolate emergency.target   # 紧急模式 (只读根分区, 最小化)
systemctl isolate multi-user.target  # 多用户模式

# 修改默认目标
systemctl set-default multi-user.target

# Target 依赖关系:
#   emergency.target
#     ↑
#   rescue.target
#     ↑
#   multi-user.target
#     ↑
#   graphical.target
```

### 7.3 服务并行启动机制

```
传统 SysVinit (串行):
  ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
  │网络  │──►│SSH  │──►│日志 │──►│应用 │
  └─────┘   └─────┘   └─────┘   └─────┘
  总时间 = 网络 + SSH + 日志 + 应用

systemd (并行):
  ┌─────┐
  │网络  │
  └──┬──┘
     ├──────► ┌─────┐
     │        │SSH  │
     ├──────► └─────┘
     │
     ├──────► ┌─────┐
     │        │日志 │
     ├──────► └─────┘
     │
     └──────► ┌─────┐
              │应用 │
              └─────┘
  总时间 = max(网络) + max(SSH/日志/应用)
```

systemd 通过以下机制实现并行：
- **socket 激活**：服务没启动时先创建 socket，有连接时才启动服务
- **D-Bus 激活**：按需启动 D-Bus 服务
- **设备激活**：设备出现时启动对应服务
- **路径激活**：文件出现时启动服务

### 7.4 分析启动耗时

```bash
# 总启动时间
systemd-analyze
# 输出: Startup finished in 3.2s (kernel) + 5.1s (initrd) + 12.4s (userspace) = 20.7s

# 各服务耗时 (从慢到快)
systemd-analyze blame | head -20
# 5.2s NetworkManager-wait-online.service    ← 等网络完全就绪 (可禁用)
# 3.1s dnf-makecache.service
# 2.5s firewalld.service
# 1.8s sshd.service
# ...

# 关键路径 (哪些服务阻塞了后续启动)
systemd-analyze critical-chain
# └─multi-user.target @12.4s
#   └─sshd.service @10.6s +1.8s
#     └─network.target @10.5s
#       └─NetworkManager.service @8.1s +2.4s
#         └─basic.target @8.0s
#           └─sockets.target @8.0s

# 生成启动分析图 (SVG)
systemd-analyze plot > /tmp/boot.svg

# 查看某服务的启动日志
journalctl -u sshd.service -b
journalctl -u NetworkManager.service -b
```

### 7.5 常见启动慢的原因

```bash
# 1. NetworkManager-wait-online 等待网络超时 (最常见的慢启动原因)
systemctl disable NetworkManager-wait-online.service
# 或
systemctl mask NetworkManager-wait-online.service

# 2. SELinux relabel (首次启动或策略变更后)
# 会在启动时重新标记所有文件, 大文件系统要几十分钟
# 临时跳过: 内核参数加 selinux=0
# 查看: cat /.autorelabel

# 3. fsck 文件系统检查
# /etc/fstab 中第 6 列为 1 (根分区) 或 2 (其他分区) 会定期检查
# 大文件系统检查很慢, 可以临时设为 0

# 4. LVM 扫描
# 如果有很多 LVM 卷, 扫描会很慢
# 减少 vgscan 范围或用 lvmetad

# 5. 等待 BMC 初始化
# 有些服务器 IPMI 初始化慢, ipmi 服务会等待

# 6. 云服务器 metadata 获取
# cloud-init 等待 cloud metadata 服务响应
```

---

## 八、启动过程中的关键文件

### 8.1 文件清单

| 阶段 | 文件/路径 | 作用 |
|:---|:---|:---|
| BIOS/UEFI | SPI Flash 固件 | BIOS/UEFI 固件本身 |
| BIOS/UEFI | NVRAM | UEFI 引导项 (BootOrder) |
| 引导设备 | MBR (Legacy) / EFI 分区 (UEFI) | 第一阶段引导代码 |
| GRUB | `/boot/efi/EFI/rocky/grub.cfg` | UEFI GRUB 入口 |
| GRUB | `/boot/grub2/grub.cfg` | GRUB 主配置 |
| GRUB | `/etc/default/grub` | GRUB 源配置 (用户编辑) |
| GRUB | `/boot/loader/entries/*.conf` | BLS 内核条目 |
| 内核 | `/boot/vmlinuz-$(uname -r)` | 内核镜像 |
| initramfs | `/boot/initramfs-$(uname -r).img` | 初始内存盘 |
| systemd | `/sbin/init` → `/lib/systemd/systemd` | PID 1 |
| systemd | `/etc/systemd/system/default.target` | 默认启动目标 |
| systemd | `/etc/systemd/system/multi-user.target.wants/` | 启用的服务 |
| systemd | `/etc/fstab` | 文件系统挂载表 |
| systemd | `/etc/sysctl.conf` | 内核参数 |
| 登录 | `/etc/passwd` `/etc/shadow` | 用户账户 |
| 登录 | `/etc/ssh/sshd_config` | SSH 配置 |

### 8.2 /etc/fstab 详解

```bash
# /etc/fstab — 文件系统挂载表
# <设备>                <挂载点>    <类型>  <选项>          <dump> <pass>
/dev/mapper/rl-root     /           xfs     defaults         0      0
UUID=xxxx-xxxx          /boot       xfs     defaults         0      0
UUID=yyyy-yyyy          /boot/efi   vfat    umask=0077,shortname=winnt 0  2
/dev/mapper/rl-swap     none        swap    defaults         0      0
# 第 5 列 dump: 是否备份 (0=不备份, 现代系统都是 0)
# 第 6 列 pass: fsck 顺序 (0=不检查, 1=根分区先检查, 2=其他分区后检查)
```

---

## 九、救急与故障恢复

### 9.1 各阶段进入救急模式

| 阶段 | 方法 | 用途 |
|:---|:---|:---|
| BIOS | F2/Del → Boot Menu → 选 Rescue | 硬件级引导选择 |
| GRUB | 菜单按 `e` → 编辑内核参数 | 修改启动参数 |
| GRUB | 菜单按 `c` → 命令行 | 手动引导 |
| 内核 | 参数加 `systemd.unit=rescue.target` | 救援模式 (单用户, 要密码) |
| 内核 | 参数加 `systemd.unit=emergency.target` | 紧急模式 (只读根, 最小化) |
| 内核 | 参数加 `init=/bin/bash` | 绕过 systemd, 直接 bash |
| 内核 | 参数加 `rd.break` | 卡在 initramfs 阶段 (排障) |
| 运行时 | Ctrl+Alt+Del (三次) | systemd 触发 reboot |

### 9.2 忘记 root 密码

```bash
# 方法: GRUB 编辑内核参数

# 1. 重启 → GRUB 菜单按 'e'
# 2. 找到 linux16 行, 末尾追加:
    rd.break
#    或 (更彻底):
    init=/bin/bash

# 3. Ctrl+X 启动

# === 方式一: rd.break (推荐) ===
# 进入 initramfs 命令行, 根分区挂载在 /sysroot (只读)
switch_root:/# mount -o remount,rw /sysroot
switch_root:/# chroot /sysroot
sh-5.1# passwd root
New password: ...
sh-5.1# touch /.autorelabel    # SELinux 需要重新标记
sh-5.1# exit
switch_root:/# exit

# === 方式二: init=/bin/bash ===
# 直接进入 bash, 根分区是只读的
bash-5.1# mount -o remount,rw /
bash-5.1# passwd root
bash-5.1# touch /.autorelabel
bash-5.1# exec /sbin/init      # 继续 systemd 启动
```

### 9.3 GRUB 损坏修复

```bash
# 场景: 重装 Windows 后 MBR 被覆盖 / 误删 EFI 分区

# 用 Live USB/ISO 启动 → chroot 修复

# 1. 挂载系统分区
mount /dev/mapper/rl-root /mnt
mount /dev/nvme0n1p2 /mnt/boot       # /boot 分区
mount /dev/nvme0n1p1 /mnt/boot/efi   # EFI 分区

# 2. 挂载虚拟文件系统
mount --bind /dev /mnt/dev
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
mount --bind /run /mnt/run

# 3. chroot
chroot /mnt

# 4. 重装 GRUB
# UEFI:
grub2-install --target=x86_64-efi --efi-directory=/boot/efi
grub2-mkconfig -o /boot/grub2/grub.cfg
grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg

# Legacy BIOS:
grub2-install /dev/nvme0n1
grub2-mkconfig -o /boot/grub2/grub.cfg

# 5. 退出重启
exit
reboot
```

### 9.4 initramfs 损坏修复

```bash
# 用 Live USB/ISO 启动 → chroot 重建

# 1-3. 同上挂载 + chroot

# 4. 重建 initramfs
KVER=$(ls /lib/modules | sort -V | tail -1)
dracut --force /boot/initramfs-${KVER}.img ${KVER}

# 如果需要加入额外驱动:
dracut --force --add-drivers "megaraid_sas nvme" \
    /boot/initramfs-${KVER}.img ${KVER}

# 5. 验证
lsinitrd /boot/initramfs-${KVER}.img | head -20
```

---

## 十、启动优化

### 10.1 分析慢在哪

```bash
# 总览
systemd-analyze

# 各服务耗时
systemd-analyze blame | head -20

# 关键路径
systemd-analyze critical-chain

# 生成可视化图
systemd-analyze plot > /tmp/boot-analysis.svg
# 用浏览器打开 SVG 文件, 可以看到每个服务的启动时间线
```

### 10.2 常见优化项

```bash
# 1. 禁用不必要的服务
systemctl disable bluetooth
systemctl disable cups
systemctl disable avahi-daemon
systemctl disable NetworkManager-wait-online.service  # 最常见!
# 查看不用的服务:
systemctl list-unit-files --state=enabled

# 2. 网络配置优化
# 如果用静态 IP, 不需要等 DHCP 超时
# /etc/NetworkManager/system-connections/eth0.nmconnection
[ipv4]
method=manual          # 静态 IP, 不等 DHCP
address=192.168.1.100/24
gateway=192.168.1.1

# 3. 减少 fsck
# /etc/fstab 第 6 列设为 0 (跳过自动检查)
# 或用 tune2fs 调整检查间隔:
tune2fs -c 0 -i 0 /dev/sda1   # ext4: 禁用定期检查
xfs_admin -L "" /dev/sda1     # xfs: 本身很少需要 fsck

# 4. BIOS 优化
# - 关闭不必要的 Option ROM (如不需要 PXE 就关网卡 ROM)
# - 设置快速启动 (Fast Boot) — 跳过部分 POST 检测
# - 减少内存测试时间 (如 BIOS 有 Express Memory Test 选项)

# 5. 内核优化
# /etc/default/grub 中 GRUB_CMDLINE_LINUX 追加:
#   quiet loglevel=3           # 减少内核日志输出
#   rd.luks=0 rd.lvm=0         # 如果不用 LUKS/LVM 可以跳过扫描
#   raid=noautodetect           # 如果不用软 RAID
```

### 10.3 优化效果对比

| 优化前 | 优化后 | 优化项 |
|:---:|:---:|:---|
| 45s | 20s | 禁用 NetworkManager-wait-online |
| 20s | 15s | 禁用不必要服务 |
| 15s | 12s | 静态 IP 替代 DHCP |
| 12s | 10s | BIOS Fast Boot |
| 60s+ | 30s | fsck 跳过 / 间隔增大 |

---

## 十一、各阶段日志位置速查

| 阶段 | 日志位置 | 查看 |
|:---|:---|:---|
| BMC | BMC Web → System Event Log (SEL) | `ipmitool sel list` |
| BIOS/POST | 主板诊断 LED / 蜂鸣器 | 看物理指示 |
| GRUB | 屏幕显示 (无持久日志) | `cat /var/log/grub` (如有) |
| 内核 | `dmesg` / `journalctl -k` | `journalctl -k -b 0` |
| initramfs | `journalctl -b` | `journalctl -b --grep=dracut` |
| systemd | `journalctl -b` | `journalctl -b -p err` |
| 服务 | `journalctl -u <service>` | `journalctl -u sshd -b` |
| 启动总览 | `systemd-analyze` | `systemd-analyze blame` |
| 上次启动 | `journalctl -b -1` | 排查上次崩溃 |
| 全部历史 | `/var/log/journal/` | `journalctl --list-boots` |

```bash
# 查看所有启动记录
journalctl --list-boots
# 输出:
# IDX    BOOT ID    FIRST ENTRY                LAST ENTRY
# -3     abc123     Mon 2026-07-04 09:00:00    Mon 2026-07-04 18:00:00
# -2     def456     Tue 2026-07-05 09:00:00    Tue 2026-07-05 18:00:00
# -1     ghi789     Wed 2026-06-06 09:00:00    Wed 2026-06-06 09:05:00  ← 异常短, 可能崩溃
#  0     jkl012     Wed 2026-06-06 09:10:00    Wed 2026-06-06 14:00:00  ← 当前

# 查看某次启动的日志
journalctl -b -1          # 上一次
journalctl -b -1 -p err   # 上一次的错误
journalctl -b 0 --since "09:10" --until "09:15"  # 当前启动某时段
```

---

## 十二、完整启动时序图

```
时间轴 (秒)
0        1        5       10       20       30       60
│────────│────────│────────│────────│────────│────────│
│        │        │        │        │        │        │
│ BMC    │        │        │        │        │        │
│启动████│        │        │        │        │        │
│        │        │        │        │        │        │
│        │ POST   │        │        │        │        │
│        │CPU初始化│        │        │        │        │
│        │内存训练████████│        │        │        │
│        │        │设备扫描│        │        │        │
│        │        │Option  │        │        │        │
│        │        │ROM   ██│        │        │        │
│        │        │        │GRUB    │        │        │
│        │        │        │加载    │        │        │
│        │        │        │内核  ██│        │        │
│        │        │        │        │initramfs│       │
│        │        │        │        │加载驱动 │       │
│        │        │        │        │挂载根  ██│       │
│        │        │        │        │        │systemd│
│        │        │        │        │        │并行   │
│        │        │        │        │        │拉服务 │
│        │        │        │        │        │      │SSH
│        │        │        │        │        │      │就绪
│        │        │        │        │        │      │█
│        │        │        │        │        │      │
│────────│────────│────────│────────│────────│────────│
0        1        5       10       20       30       60

阶段耗时:
  BMC 初始化:     0 - 1s
  POST:           1 - 8s (内存训练是大头)
  GRUB:           8 - 10s (含 5s 菜单倒计时)
  内核:           10 - 15s
  initramfs:      15 - 20s
  systemd:        20 - 30s (并行启动)
  总计:           ~30s (优化后) ~60s (默认) ~5min (首次上电)
```

---

*最后更新: 2026-07-07*
