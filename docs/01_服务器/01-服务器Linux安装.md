# 服务器 Linux 操作系统安装

> 从零开始在一台物理服务器上安装 Linux（以 Rocky Linux 9 / Ubuntu 22.04 为例），涵盖启动盘制作、RAID 配置、BIOS 引导设置、系统安装全流程。

---

## 一、前置准备

### 1.1 需要的东西

| 物品 | 说明 |
|:---|:---|
| 服务器 | 目标机器（带 BMC/IPMI 远程管理口更佳） |
| U 盘 | ≥ 8GB，USB 3.0 优先 |
| ISO 镜像 | Rocky-9.x-x86_64-dvd.iso / ubuntu-22.04.x-live-server-amd64.iso |
| 另一台电脑 | 用于制作启动盘 + 远程操控 BMC |
| 网线 | 接入 BMC 管理口和业务网口 |

### 1.2 下载镜像

```bash
# Rocky Linux 9 (RHEL 兼容, 国产化首选)
# 官方: https://rockylinux.org/download
wget https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.5-x86_64-dvd.iso

# Ubuntu 22.04 LTS
# 官方: https://ubuntu.com/download/server
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.5-live-server-amd64.iso

# 校验 (务必)
sha256sum Rocky-9.5-x86_64-dvd.iso
# 对比官网公布的 SHA256
```

### 1.3 确认服务器硬件信息

通过 BMC Web 界面或开机自检确认：

```
- 服务器型号 (如 Lenovo SR650 / Dell R750 / 浪潮 NF5280)
- CPU 型号 + 数量
- 内存容量 + 插法
- 磁盘数量 + 接口 (SAS/SATA/NVMe)
- RAID 卡型号 (如 MegaRAID 9560-8i / HBA330)
- 网卡型号 + 端口数
- BMC/IPMI IP 地址
```

---

## 二、启动盘制作

### 2.1 U 盘启动盘制作

#### 方式一：dd 命令（Linux/macOS，最通用）

```bash
# 1. 插入 U 盘，确认设备名
lsblk
# 假设 U 盘是 /dev/sdb

# 2. 卸载 U 盘（如果已自动挂载）
sudo umount /dev/sdb*

# 3. 写入镜像（⚠️ 确认设备名，写错盘会毁数据）
sudo dd if=Rocky-9.5-x86_64-dvd.iso of=/dev/sdb bs=4M status=progress conv=fsync

# 4. 同步并弹出
sync
sudo eject /dev/sdb
```

!!! warning "dd 写入注意事项"
    - `of=` 写的是设备名 `/dev/sdb`，**不是**分区 `/dev/sdb1`
    - 写入前用 `lsblk -f` 确认 U 盘设备名，**切勿写到系统盘**
    - `bs=4M` + `conv=fsync` 保证写入完整性
    - U 盘会被整个覆盖，里面的数据全部丢失

#### 方式二：Rufus（Windows，最常用）

1. 下载 [Rufus](https://rufus.ie/)
2. 插入 U 盘 → 选择 U 盘设备
3. 点击「选择」→ 加载 ISO 镜像
4. 分区类型：
   - **GPT** + **UEFI**（现代服务器，2015 年后推荐）
   - **MBR** + **BIOS**（老服务器 Legacy 模式）
5. 点击「开始」→ 选择 **DD 模式**（ISO 模式在某些服务器上无法引导）
6. 等待写入完成

#### 方式三：Ventoy（多镜像，推荐长期使用）

```bash
# 1. 下载 Ventoy
# https://www.ventoy.net/
wget https://github.com/ventoy/Ventoy/releases/download/v1.0.99/ventoy-1.0.99-linux.tar.gz
tar xzf ventoy-1.0.99-linux.tar.gz
cd ventoy-1.0.99

# 2. 安装到 U 盘（⚠️ 确认设备名）
sudo ./Ventoy2Disk.sh -i /dev/sdb
# 输入 y 确认

# 3. 把 ISO 直接拷贝到 U 盘
cp Rocky-9.5-x86_64-dvd.iso /media/$USER/Ventoy/
cp ubuntu-22.04.5-live-server-amd64.iso /media/$USER/Ventoy/
sync
```

Ventoy 的优势：一个 U 盘放多个 ISO，启动时选哪个装哪个。

### 2.2 光盘启动盘制作（仅老服务器 / 无 USB 引导场景）

```bash
# Linux 刻录
wodim dev=/dev/sr0 -v -eject Rocky-9.5-x86_64-dvd.iso

# Windows: 用 ImgBurn / CDBurnerXP
# 选最低速 (4x) 刻录，保证兼容性
```

!!! info "光盘 vs U 盘"
    - 现代服务器**优先用 U 盘**，速度快、可复用
    - 光盘仅用于：老服务器不支持 USB 引导、合规要求（金融/政府审计留痕）
    - 如果服务器有 BMC，可以直接用**虚拟媒体（Virtual Media）**挂载 ISO，不需要物理介质

### 2.3 通过 BMC 虚拟媒体安装（推荐，无需物理 U 盘）

```
1. 浏览器打开 BMC IP → 登录
2. 找到 "Virtual Media" / "远程媒体" 选项
3. 挂载本地 ISO 镜像 (CD/DVD)
4. 重启服务器 → 按 Del/F2 进 BIOS → 设置从 Virtual CD-ROM 启动
5. 安装完成后取消挂载
```

| 厂商 | BMC 名称 | 虚拟媒体路径 |
|:---|:---|:---|
| Lenovo | XCC (XClarity Controller) | Remote Control → Virtual Media |
| Dell | iDRAC | Virtual Console → Virtual Media |
| HPE | iLO | Remote Console → Media |
| 浪潮 | BMC | 远程控制 → 虚拟介质 |
| 华为 | iBMC | 虚拟介质 → ISO 挂载 |

---

## 三、服务器 RAID 配置

### 3.1 什么时候需要配 RAID

| 场景 | 是否需要手动配 RAID |
|:---|:---|
| 新服务器首次安装系统 | ✅ 必须 |
| 磁盘更换后 | ✅ 需重建 RAID |
| 已有 RAID 且只装系统 | ❌ 跳过 |
| HBA 直通模式（JBOD） | ❌ 不配 RAID，直通给 OS |
| 软 RAID（mdadm） | ❌ 在 OS 安装后配置 |

### 3.2 进入 RAID 配置界面

开机自检阶段，当 RAID 卡初始化时按快捷键：

| RAID 卡 | 快捷键 | 提示信息 |
|:---|:---|:---|
| Broadcom/LSI MegaRAID | `Ctrl+R` | "Press Ctrl+R to enter MegaRAID Configuration Utility" |
| Dell PERC | `Ctrl+R` | "Press Ctrl+R to enter PERC Configuration Utility" |
| HPE Smart Array | `F5` | "Press F5 to enter Smart Storage Administrator" |
| Lenovo RAID | `Ctrl+H` | "Press Ctrl+H to enter WebBIOS" |
| Broadcom HBA (IT/IR 模式) | `Ctrl+C` | "Press Ctrl+C for LSI Corp Configuration Utility" |

!!! tip "通过 BMC 操作"
    如果不在机房，可以通过 BMC 的远程 KVM（Remote Console）按这些快捷键，和物理键盘效果一样。

### 3.3 MegaRAID 配置实例（最常见）

以 Broadcom MegaRAID 9560-8i 为例，4 块 600GB SAS 盘做 RAID 10：

```
1. 开机 → Ctrl+R 进入 MegaRAID BIOS

2. 主菜单 → Virtual Drives → 按 F2 → Create Virtual Drive

3. Select RAID Level: RAID-10
   (RAID 10 = 4盘两两镜像再条带, 兼顾性能和安全)

4. Select Drives:
   勾选 4 块磁盘 (Drive 0 ~ Drive 3)

5. Advanced:
   - Strip Size: 256KB (数据库推荐, 大IO)
   - Read Policy: Read Ahead (预读)
   - Write Policy: Write Back (写缓存, 有BBU时用)
   - IO Policy: Direct IO
   - Access Policy: Read/Write
   - Default Cache: Enable

6. 保存 → 按 Ctrl+C 退出

7. 回到主菜单 → 选中刚创建的 VD → F2 → Initialize → Fast Init
   (快速初始化, 几秒钟; 全初始化要几小时)
```

### 3.4 常见 RAID 级别选择

| RAID 级别 | 最少盘数 | 可用容量 | 容错 | 适用场景 |
|:---:|:---:|:---|:---|:---|
| RAID 0 | 1 | 100% | ❌ 无 | 临时数据, 极致性能 |
| RAID 1 | 2 | 50% | ✅ 坏 1 盘 | 系统盘 (2 盘) |
| RAID 5 | 3 | (n-1)/n | ✅ 坏 1 盘 | 读多写少, 数据盘 |
| RAID 6 | 4 | (n-2)/n | ✅ 坏 2 盘 | 大容量, 安全要求高 |
| RAID 10 | 4 | 50% | ✅ 每组坏 1 盘 | 数据库, 读写均衡 |
| RAID 50 | 6 | 复杂 | ✅ 每组坏 1 盘 | 大容量+性能 |
| RAID 60 | 8 | 复杂 | ✅ 每组坏 2 盘 | 大容量+高安全 |

**运维经验选型：**

```
系统盘 (2 块):     RAID 1  — 两盘镜像, 坏一块不停机
数据库盘 (4+ 块):  RAID 10 — 性能和安全最佳平衡
日志/备份盘 (6+):  RAID 6  — 允许坏 2 盘, 重建压力小
热备盘:           配 1 块 Global Hot Spare, 自动顶替坏盘
```

### 3.5 通过 storcli 在线查看/配置（OS 已装时）

```bash
# 查看 RAID 卡信息
storcli64 /c0 show

# 查看所有物理盘
storcli64 /c0 /eall /sall show

# 查看虚拟盘
storcli64 /c0 /vall show

# 在线创建 RAID 1 (2 块盘)
storcli64 /c0 add vd r1 drives=252:0,252:1 pdperarray=1

# 在线创建 RAID 10 (4 块盘)
storcli64 /c0 add vd r10 drives=252:0,252:1,252:2,252:3 pdperarray=2

# 设置全局热备
storcli64 /c0 /e252 /s4 add hotsparedrive

# 查看重建进度
storcli64 /c0 /e252 /s4 show rebuild
```

### 3.6 关键注意事项

!!! danger "RAID 不是备份"
    - RAID 只防磁盘物理损坏，不防误删/勒索/逻辑错误
    - RAID 重建期间是**最脆弱**的，重建失败 = 全部数据丢失
    - 6TB 以上大盘重建可能要 24-48 小时，重建期间再坏一盘 = 灾难
    - **RAID 6 / RAID 60 优先于 RAID 5 / RAID 50**（大盘时代 RAID 5 太危险）

!!! warning "Write Back vs Write Through"
    - **Write Back**: 数据写到缓存就返回，性能高，但断电可能丢数据
    - **Write Through**: 数据写到磁盘才返回，安全但慢
    - 有 BBU（电池备份单元）或超级电容时才用 Write Back
    - 现代 RAID 卡支持 **CacheCade + BBU + Journaling**，断电不丢

---

## 四、服务器 BIOS 引导配置

### 4.1 进入 BIOS

| 厂商 | 快捷键 | 提示信息 |
|:---|:---|:---|
| Lenovo | `F1` | "Press F1 to enter Setup" |
| Dell | `F2` | "Press F2 to enter System Setup" |
| HPE | `F9` | "Press F9 for ROM-Based Setup Utility" |
| 浪潮 | `Del` | "Press DEL to enter Setup" |
| 华为 | `Del` / `F6` | "Press DEL to enter Setup" |
| Supermicro | `Del` | "Press DEL to run Setup" |

### 4.2 关键 BIOS 设置项

#### 4.2.1 引导模式

```
Boot Mode:
  - UEFI (推荐, 现代服务器必选)
    → 支持 GPT 分区, 支持 Secure Boot, 支持 >2TB 磁盘
  - Legacy BIOS (老系统兼容)
    → MBR 分区, 最大 2TB, 不支持 Secure Boot
  - UEFI + CSM (兼容模式)
    → 可同时引导 UEFI 和 Legacy 设备, 不推荐长期使用
```

!!! tip "UEFI vs Legacy 选择"
    - **2020 年后的服务器一律用 UEFI**
    - UEFI 支持 GPT 分区，可引导 >2TB 系统盘
    - Secure Boot 需要 UEFI
    - NVMe 启动盘必须 UEFI
    - 只有老服务器（2015 年前）才需要 Legacy

#### 4.2.2 引导顺序

```
Boot Order / Boot Sequence:
  1. USB CD-ROM   (虚拟介质安装时)
  2. USB Hard Disk (U 盘安装时)
  3. Hard Disk C:  (安装完成后设为第一)
  4. Network Boot  (PXE 批量安装时)
  5. Disabled      (不用的全部禁用)
```

安装系统时：把 USB 设备调到第一位。
安装完成后：把系统盘调到第一位，**禁用 USB 引导和网络引导**（防止意外从其他介质启动）。

#### 4.2.3 虚拟化支持

```
Intel VT-x / AMD-V:       Enabled  (虚拟化必开)
Intel VT-d / AMD-Vi:      Enabled  (IO 虚拟化, PCI 直通需要)
SR-IOV:                   Enabled  (网卡 VF 直通, 虚拟化/AI 推理用)
```

#### 4.2.4 硬件安全

```
Secure Boot:              Enabled  (安全启动, 防止 rootkit)
TPM 2.0:                  Enabled  (可信平台模块)
Boot Sector Virus Protect: Enabled  (引导区写保护)
```

!!! note "Secure Boot 与国产 OS"
    - Rocky/CentOS/Ubuntu 的官方内核签名证书被 UEFI 固件信任，可以正常 Secure Boot
    - 麒麟/统信等国产 OS 也有 Secure Boot 证书
    - 如果自编内核或加载第三方驱动，可能需要关闭 Secure Boot 或注册 MOK 证书

#### 4.2.5 电源管理

```
Power Profile:            Maximum Performance  (服务器不开节能)
C-States:                 Disabled (低延迟场景, 如数据库/交易)
P-State Coordination:     Hardware (OS 自管)
```

#### 4.2.6 其他推荐设置

```
Hyper-Threading:          Enabled  (超线程, 一般开)
NUMA:                     Enabled   (多路服务器必开)
SRAT:                     Enabled   (NUMA 亲和性)
Memory Interleaving:      Channel   (内存交错, 提升带宽)
Onboard RAID:             Disabled  (用独立 RAID 卡时关掉板载)
BMC Network:              Dedicated (独立 BMC 网口, 不共享业务口)
Watchdog Timer:           Enabled   (看门狗, 系统挂死自动重启)
```

### 4.3 保存并重启

```
F10 → Save and Exit → Yes
```

---

## 五、系统安装

### 5.1 Rocky Linux 9 安装（图形/文本模式）

#### 5.1.1 启动安装程序

```
1. 插入 U 盘 / 挂载虚拟媒体 → 重启服务器
2. 引导菜单选择:
   Install Rocky Linux 9.5
   (按 Tab 可编辑内核参数, 如指定安装源、网络配置)

3. 进入 Anaconda 安装界面
```

#### 5.1.2 安装配置（关键项）

```
┌─────────────────────────────────────────────┐
│  INSTALLATION SUMMARY                        │
├─────────────────────────────────────────────┤
│  ✅ 语言: 中文 (简体)                          │
│  ⚠️ 安装目标: 未选择      ← 必须设置            │
│  ⚠️ 软件选择: 未选择      ← 必须设置            │
│  ⚠️ 网络: 未连接          ← 必须设置            │
│  ⚠️ Root 密码: 未设置     ← 必须设置            │
│  ⚠️ 用户创建: 未创建      ← 建议设置            │
│  ✅ 时间日期: 已同步                           │
│  ✅ 键盘布局: 汉语                             │
└─────────────────────────────────────────────┘
```

**① 安装目标**

```
安装目标 → 选择磁盘:
  ☑ /dev/sda (RAID 虚拟盘, 如 600GB)

  存储配置:
    - 自动 (Automatic): 让安装器自动分区, 新手推荐
    - 自定义 (Custom): 手动分区, 生产环境推荐

  自定义分区方案 (600GB 系统盘):
  ┌──────┬────────┬─────────┬──────────────────┐
  │ 挂载 │ 大小    │ 文件系统 │ 说明              │
  ├──────┼────────┼─────────┼──────────────────┤
  │ /boot/efi │ 1GB │ EFI System Partition │ UEFI 引导 │
  │ /boot │ 1GB    │ xfs     │ 内核 + initramfs  │
  │ swap  │ 内存×1 │ swap    │ 交换分区           │
  │ /     │ 剩余   │ xfs     │ 根分区             │
  └──────┴────────┴─────────┴──────────────────┘

  注: UEFI 模式必须有 /boot/efi (FAT32, 512MB-1GB)
      Legacy 模式不需要 /boot/efi, 但需要 /boot (ext4/xfs)
```

**② 软件选择**

```
软件选择 → 基本环境:
  ○ 最小安装 (Minimal Install)     — 只有 CLI, 最精简, 生产推荐
  ○ 服务器 (Server)                — CLI + 基础网络服务
  ● 带GUI的服务器 (Server with GUI) — 带 GNOME 桌面, 一般不用
  ○ 虚拟化主机 (Virtualization Host) — KVM 虚拟化
  ○ 工作站 (Workstation)            — 开发用

  附加选项 (Minimal 基础上):
  ☑ 系统工具 (System Tools)    — 含 dmidecode, hwloc, lsscsi 等
  ☑ 网络存储 (Network Storage) — 含 iscsi-initiator, nfs-utils
```

**生产环境一律选「最小安装 + 系统工具 + 网络存储」**，不装桌面。

**③ 网络配置**

```
网络和主机名 → 选择网卡 (如 eno1):
  IPv4 配置:
    方法: 手动 (Manual)
    地址: 192.168.1.100
    子网掩码: 255.255.255.0 (/24)
    网关: 192.168.1.1
    DNS: 192.168.1.10 (内网 DNS)

  主机名: web-server-01.example.com

  开机自动连接: ☑ ON
```

**④ Root 密码 + 用户创建**

```
Root 密码:
  强密码 (≥12 位, 含大小写+数字+特殊字符)
  锁定 root 账户? → 生产环境建议锁定, 用 sudo 用户

用户创建:
  用户名: admin (或 ops / deploy)
  ☑ 使此用户成为管理员 (wheel 组, 可 sudo)
  密码: 同样强密码
```

#### 5.1.3 开始安装

```
全部 ⚠️ 变 ✅ 后 → 点击「开始安装」
  等待 10-30 分钟 (取决于磁盘速度和镜像大小)
  完成后 → 「重启系统」

重启后:
  - 拔掉 U 盘 / 取消虚拟媒体挂载
  - 从系统盘引导
```

### 5.2 Ubuntu 22.04 Server 安装

Ubuntu Server 使用 Cloud-Init 风格的安装程序，和 Rocky 略有不同：

```
1. 引导 → "Try or Install Ubuntu Server"

2. 仪表盘:
   [✅] Welcome        — 语言/键盘
   [⚠️] Installer update — 可跳过
   [⚠️] Keyboard       — 选 US
   [⚠️] Type of install — 选 Ubuntu Server (minimized 更精简)
   [⚠️] Network         — 配 IP + 网关 + DNS
   [⚠️] Proxy           — 无代理留空
   [⚠️] Mirror          — 改国内源: http://mirrors.aliyun.com/ubuntu
   [⚠️] Storage         — 选磁盘 + 分区 (同上)
   [⚠️] Profile         — 主机名 + 用户名 + 密码
   [⚠️] SSH Setup       — ☑ Install OpenSSH server
   [⚠️] Featured Snaps  — 全不选 (生产不用 snap)

3. 全部 ✅ → Install → 等待 → Reboot
```

### 5.3 安装后首次配置

```bash
# === 1. 验证系统 ===
cat /etc/os-release          # 确认发行版版本
uname -r                     # 内核版本
hostnamectl                  # 主机名
ip addr                      # IP 地址
lsblk                        # 磁盘分区
free -h                      # 内存
nproc                        # CPU 核心数
lscpu                        # CPU 详情
dmidecode -t system          # 服务器型号
dmidecode -t memory          # 内存条详情

# === 2. 更新系统 ===
# Rocky/RHEL
dnf update -y

# Ubuntu
apt update && apt upgrade -y

# === 3. 配置 SSH ===
# 禁止 root 登录 + 禁止密码登录 + 只允许密钥
sudo vi /etc/ssh/sshd_config
  PermitRootLogin no
  PasswordAuthentication no
  PubkeyAuthentication yes

# 重启 SSH
sudo systemctl restart sshd

# === 4. 配置防火墙 ===
# Rocky (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Ubuntu (ufw)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# === 5. 时间同步 ===
sudo timedatectl set-timezone Asia/Shanghai
sudo systemctl enable --now chronyd   # Rocky
sudo systemctl enable --now systemd-timesyncd  # Ubuntu

# === 6. 安装基础运维工具 ===
# Rocky
sudo dnf install -y vim git wget curl tmux htop \
    net-tools bind-utils telnet tcpdump \
    sysstat dnf-automatic epel-release

# Ubuntu
sudo apt install -y vim git wget curl tmux htop \
    net-tools dnsutils telnet tcpdump \
    sysstat unattended-upgrades

# === 7. 确认 RAID 状态 ===
sudo dnf install -y storcli    # 需手动下载
# 或
sudo /opt/MegaRAID/storcli/storcli64 /c0 /vall show

# === 8. 确认 BMC 可达 ===
ping <BMC_IP>
# 如需配置 BMC IP:
sudo ipmitool lan set 1 ipaddr <BMC_IP>
sudo ipmitool lan set 1 netmask <掩码>
sudo ipmitool lan set 1 defgw ipaddr <网关>
```

---

## 六、验证清单

安装完成后逐项确认：

| # | 检查项 | 命令 | 预期 |
|:---:|:---|:---|:---|
| 1 | 系统版本 | `cat /etc/os-release` | 正确发行版 + 版本 |
| 2 | 内核 | `uname -r` | 5.x+ (Rocky) / 5.15+ (Ubuntu) |
| 3 | 主机名 | `hostname -f` | 符合命名规范 |
| 4 | IP 配置 | `ip addr` | 静态 IP, 网关可达 |
| 5 | DNS | `nslookup github.com` | 解析正常 |
| 6 | 磁盘分区 | `lsblk` | 分区正确, /boot/efi 存在 |
| 7 | 文件系统 | `df -hT` | xfs/ext4, 挂载正确 |
| 8 | RAID 状态 | `storcli64 /c0 /vall show` | Optimal/Online |
| 9 | 内存 | `free -h` | 总量正确 |
| 10 | CPU | `lscpu` | 核心数/线程数正确 |
| 11 | 时间同步 | `timedatectl` | NTP synchronized: yes |
| 12 | SSH | `ssh admin@<IP>` | 密钥登录成功 |
| 13 | root SSH | `ssh root@<IP>` | 拒绝登录 |
| 14 | 防火墙 | `sudo firewall-cmd --list-all` | 仅放行需要端口 |
| 15 | BMC | `ping <BMC_IP>` | 可达 |
| 16 | 系统更新 | `dnf list --upgrades` | 无关键安全更新待装 |
| 17 | 虚拟化 | `grep -c vmx /proc/cpuinfo` | >0 (支持 VT-x) |
| 18 | SElinux | `getenforce` | Enforcing (Rocky) |

---

## 七、常见问题

### Q1: U 盘安装时找不到安装源

```
# 原因: U 盘设备名和安装程序预期不一致
# 解决: 在引导菜单按 Tab, 添加 inst.stage2=hd:LABEL=Rocky-9-5-x86_64-dvd
# 或将 U 盘 LABEL 改为安装程序期望的名称
```

### Q2: 安装后无法引导（黑屏/光标闪烁）

```
# 可能原因:
# 1. Boot Mode 不匹配 (UEFI 装的系统用 Legacy 引导, 或反之)
#    → 进 BIOS, 确认 Boot Mode = UEFI, Boot Order 选系统盘
# 2. /boot/efi 分区未创建 (UEFI 模式)
#    → 重新安装, 确保创建 EFI System Partition
# 3. RAID 虚拟盘未设为引导盘
#    → 进 RAID 配置, 将 VD 设为 Boot Volume
# 4. Secure Boot 阻止了内核签名
#    → 关闭 Secure Boot 或注册内核 MOK 证书
```

### Q3: 安装时看不到磁盘

```
# 可能原因:
# 1. RAID 未配置 (磁盘是 Unconfigured Good 状态)
#    → 进 RAID 配置界面创建 Virtual Drive
# 2. RAID 卡驱动未包含在安装镜像中
#    → 加载驱动 (dd 方式或 driverdisk)
#    → 或使用带更多驱动的 DVD 镜像 (不用 Minimal/NetInstall)
# 3. 磁盘被其他 RAID 卡锁定
#    → 清除Foreign配置: MegaRAID → Foreign → Clear
# 4. NVMe 盘未在 BIOS 中启用
#    → BIOS → Advanced → NVMe Configuration → Enable
```

### Q4: 安装后网络不通

```bash
# 检查网卡名 (可能不是 eth0, 是 eno1/enp3s0 等)
ip link show

# 检查网络配置文件
# Rocky: /etc/NetworkManager/system-connections/
nmcli connection show

# Ubuntu: /etc/netplan/
cat /etc/netplan/*.yaml
sudo netplan apply

# 检查网关
ip route

# 检查物理链路
ethtool eno1 | grep Link
```

### Q5: 安装后时区错误

```bash
sudo timedatectl set-timezone Asia/Shanghai
sudo systemctl restart chronyd  # 或 systemd-timesyncd
timedatectl  # 确认 NTP System Configuration: yes
```

---

## 八、附录

### 8.1 主流服务器 BIOS/RAID 快捷键速查

| 厂商 | BIOS | RAID | BMC | Boot Menu |
|:---|:---:|:---:|:---:|:---:|
| Lenovo ThinkSystem | F1 | Ctrl+H | XCC Web | F12 |
| Dell PowerEdge | F2 | Ctrl+R | iDRAC Web | F11 |
| HPE ProLiant | F9 | F5 | iLO Web | F11 |
| 浪潮 NF/SA | Del | Ctrl+H/Ctrl+R | BMC Web | F11 |
| 华为 TaiShan/RH | Del | Ctrl+R | iBMC Web | F7 |
| Supermicro | Del | Ctrl+H/Ctrl+R | IPMI Web | F11 |

### 8.2 网络安装（PXE）批量装机

单台用 U 盘，10 台以上用 PXE：

```
PXE 架构:
  DHCP Server → 分配 IP + 告知 TFTP 地址
  TFTP Server → 提供 pxelinux.0 / grubx64.efi 引导文件
  HTTP/FTP Server → 提供 OS 镜像
  Kickstart/Autoinstall → 自动化安装配置

工具:
  - Cobbler (自动化, 推荐)
  - MAAS (Ubuntu 生态, 云原生)
  - Foreman (企业级, 带 CMDB)
  - 手动搭 DHCP+TFTP+HTTP+Kickstart
```

详细 PXE 配置见 [18_硬件测试/03_高级](../18_硬件测试/03_高级/README.md) 章节。

### 8.3 国产 OS 安装差异

| 系统 | 基于 | 安装方式 | 差异 |
|:---|:---|:---|:---|
| 麒麟 V10 | CentOS | Anaconda (同 RHEL) | 需注册授权; Secure Boot 证书不同 |
| 统信 UOS | Debian | 自定义安装器 | 类似 Ubuntu; 软件源不同 |
| openEuler | 独立 | Anaconda (同 RHEL) | 完全开源; 国产化首选 |
| 龙蜥 Anolis | RHEL | Anaconda | CentOS 替代, 100% 兼容 |

---

*最后更新: 2026-07-06*
