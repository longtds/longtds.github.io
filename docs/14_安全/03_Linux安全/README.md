# Linux 安全

> 没有"安全的 Linux"，只有"被加固到一定程度的 Linux"。**系统加固 = 最小权限 + 日志审计 + 内核加固 + 入侵检测**，是所有上层安全的地基。

## 一、Linux 攻击面全景

```
1. 网络层      开放端口 / 弱协议 / 暴露服务
2. 账户层      弱密码 / sudo 滥用 / root 远程
3. 权限层      SUID/SGID 滥用 / 文件权限松 / Capability
4. 内核层      0day / 内核模块 / eBPF 滥用
5. 应用层      老旧软件 / 配置错误 / 0day
6. 供应链      软件包来源 / 依赖污染
7. 物理/启动   未加密磁盘 / Bootloader 篡改
8. 内部威胁    员工跳板 / 横向移动 / 后门
```

## 二、加固框架与基线

### 2.1 业界标准

| 标准 | 来源 | 适用 |
|:---|:---|:---|
| **CIS Benchmarks** ⭐⭐⭐⭐⭐ | Center for Internet Security | 全行业事实标准 |
| **DISA STIG** | 美军 | 政府 / 军用 |
| **NIST 800-53 / 800-171** | NIST | 美企合规 |
| **PCI-DSS** | 支付卡组织 | 金融支付 |
| **等保 2.0** | 中国 | 国内合规必备 |
| **GB/T 22239** | 中国 | 等保配套 |

### 2.2 自动化加固工具

```bash
# OpenSCAP（最主流）
yum install -y openscap-scanner scap-security-guide
oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_cis \
  --results scan.xml --report report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Lynis（轻量审计）
apt install -y lynis
lynis audit system

# CIS-CAT Pro（商业，覆盖最全）

# Ansible-lockdown（开源 CIS Ansible Role）
ansible-galaxy install ansible-lockdown.rhel9_cis
ansible-playbook -i inventory site.yml -e rhel9cis_section1=true

# 国内: 麒麟基线、统信基线
```

## 三、账户与认证

### 3.1 密码策略

```bash
# /etc/security/pwquality.conf
minlen = 14
minclass = 4               # 大写+小写+数字+特殊
maxrepeat = 3
maxclassrepeat = 4
dictcheck = 1
usercheck = 1
enforcing = 1
remember = 5

# /etc/login.defs
PASS_MAX_DAYS   90
PASS_MIN_DAYS   1
PASS_MIN_LEN    14
PASS_WARN_AGE   7

# /etc/pam.d/system-auth (账户锁定)
auth required pam_faillock.so preauth silent deny=5 unlock_time=900
auth required pam_faillock.so authfail audit deny=5 unlock_time=900
```

### 3.2 禁用 root 远程登录

```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no           # 强制密钥
PubkeyAuthentication yes
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
MaxAuthTries 3
MaxSessions 5
ClientAliveInterval 300
ClientAliveCountMax 0
LoginGraceTime 30
AllowUsers ops sre admin            # 白名单
Protocol 2
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
```

### 3.3 SSH 密钥规范

```bash
# 生成 ed25519（推荐，比 RSA 安全且快）
ssh-keygen -t ed25519 -C "user@company.com" -f ~/.ssh/id_ed25519

# RSA 至少 4096
ssh-keygen -t rsa -b 4096 -C "..."

# 私钥强制加密
chmod 600 ~/.ssh/id_*
chmod 700 ~/.ssh

# Authorized keys 加限制
# /home/user/.ssh/authorized_keys
from="10.0.0.0/8",command="/usr/local/bin/restricted-cmd",no-port-forwarding,no-X11-forwarding ssh-ed25519 AAA...
```

### 3.4 sudo 最小化

```bash
# /etc/sudoers.d/ops
%ops ALL=(ALL) /usr/bin/systemctl status *, /usr/bin/journalctl -u *

# DBA 只能改特定服务
%dba ALL=(postgres) /usr/bin/psql, /usr/bin/pg_dump, !/usr/bin/su

# 全部 sudo 必须记录密码 + 日志
Defaults logfile="/var/log/sudo.log"
Defaults log_input,log_output
Defaults iolog_dir="/var/log/sudo-io"

# 禁止 sudo su -
%ops ALL=(ALL) !/usr/bin/su*

# 限制时间窗口
%ops ALL=(ALL) NOPASSWD: ALL  # 千万不要
```

### 3.5 多因素认证（MFA）

```bash
# Google Authenticator
apt install libpam-google-authenticator
google-authenticator

# /etc/pam.d/sshd
auth required pam_google_authenticator.so

# /etc/ssh/sshd_config
ChallengeResponseAuthentication yes
AuthenticationMethods publickey,keyboard-interactive

# 企业级:
#   - Duo Security
#   - Okta
#   - 国内: 数字证书 + 短信 / U-Key
```

## 四、文件系统安全

### 4.1 权限基线

```bash
# 关键文件权限
chmod 644 /etc/passwd
chmod 000 /etc/shadow                # 实际 0600 由 PAM 管
chmod 644 /etc/group
chmod 600 /etc/ssh/sshd_config
chmod 600 /root/.ssh/authorized_keys
chmod 700 /root/.ssh

# 全系统检查
find / -perm -002 -type f -not -path "/proc/*"     # 全局可写
find / -nouser -o -nogroup                         # 无主文件
find / -perm -4000 -type f                         # SUID
find / -perm -2000 -type f                         # SGID
```

### 4.2 SUID / SGID 治理

```bash
# 列出所有 SUID（攻击面）
find / -perm -4000 -type f 2>/dev/null

# 高危 SUID（gtfobins 中的二进制）
#   /bin/su        正常
#   /bin/sudo      正常
#   /usr/bin/passwd 正常
#   /usr/bin/find  ❌ 应该去 SUID
#   /usr/bin/vim   ❌
#   /usr/bin/awk   ❌

# 去 SUID
chmod u-s /usr/bin/find
chmod u-s /usr/bin/vim
```

### 4.3 挂载选项

```bash
# /etc/fstab 加 nosuid/nodev/noexec
/dev/sdb1 /home    ext4 defaults,nosuid,nodev 0 2
tmpfs    /tmp      tmpfs defaults,nosuid,nodev,noexec,size=2G 0 0
tmpfs    /var/tmp  tmpfs defaults,nosuid,nodev,noexec,size=1G 0 0
/dev/sdb2 /var/log ext4 defaults,nosuid,nodev,noexec 0 2

# /dev/shm 也要锁定
tmpfs /dev/shm tmpfs defaults,nosuid,nodev,noexec 0 0
```

### 4.4 LUKS 全盘加密

```bash
# 安装时启用 / 后期加密
cryptsetup luksFormat /dev/sdb1
cryptsetup luksOpen /dev/sdb1 secure
mkfs.ext4 /dev/mapper/secure
mount /dev/mapper/secure /secure

# /etc/crypttab + TPM 2.0 自动解锁
secure /dev/sdb1 none tpm2-device=auto
```

### 4.5 文件完整性监控（FIM）

```bash
# AIDE
apt install aide
aideinit                              # 初始化基线
mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
aide --check                          # 每日定时检查

# 关键路径:
#   /etc/passwd, /etc/shadow
#   /etc/ssh/*
#   /etc/sudoers*
#   /etc/cron*
#   /usr/bin, /usr/sbin, /bin, /sbin
#   /boot

# Tripwire（商业版功能多）
# Wazuh / OSSEC（含 FIM + HIDS）
```

## 五、Capability 与最小权限

### 5.1 Linux Capability

```bash
# 不要 root 全权，按 capability 拆分
# 38 个 capabilities 列表
getcap /usr/bin/ping        # cap_net_raw=ep
setcap cap_net_bind_service=+ep /usr/local/bin/myapp     # 允许 80 端口绑定（非 root）
setcap -r /usr/local/bin/myapp                            # 撤销

# 常见高危 capability
#   CAP_SYS_ADMIN     全能力等价 root
#   CAP_SYS_PTRACE    可调试任何进程
#   CAP_DAC_OVERRIDE  绕过 DAC
#   CAP_NET_RAW       原始套接字
#   CAP_NET_ADMIN     网络管理
#   CAP_SYS_MODULE    加载内核模块
```

### 5.2 systemd 服务硬化

```ini
# /etc/systemd/system/myapp.service
[Service]
ExecStart=/usr/local/bin/myapp
User=myapp
Group=myapp

# 文件系统
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/myapp /var/log/myapp
PrivateTmp=true
PrivateDevices=true

# 网络
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
PrivateNetwork=false                # 隔离网络的话 true

# 进程
NoNewPrivileges=true
RestrictSUIDSGID=true
LockPersonality=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectKernelLogs=true
ProtectControlGroups=true
RestrictNamespaces=true
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# Capability
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
```

```bash
# 评分检查
systemd-analyze security myapp.service
# 0 (perfect) - 10 (UNSAFE)
```

## 六、内核安全

### 6.1 关键 sysctl

```bash
# /etc/sysctl.d/99-security.conf

# 网络
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_rfc1337 = 1
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_source_route = 0

# 内核
kernel.randomize_va_space = 2       # ASLR
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 2        # 限制 ptrace
kernel.unprivileged_bpf_disabled = 1
kernel.kexec_load_disabled = 1
kernel.sysrq = 0
kernel.core_uses_pid = 1
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.suid_dumpable = 0

# 模块
kernel.modules_disabled = 1         # 极严格时启用（生产前测试）

sysctl --system
```

### 6.2 SELinux / AppArmor

```bash
# SELinux（RHEL 系）
sestatus                            # 查看
setenforce 1                        # 启用强制
# /etc/selinux/config
SELINUX=enforcing
SELINUXTYPE=targeted

# 排查
ausearch -m AVC -ts recent
audit2allow -a                      # 生成策略

# AppArmor（Debian/Ubuntu 系）
apparmor_status
aa-enforce /etc/apparmor.d/usr.bin.myapp
aa-complain /etc/apparmor.d/usr.bin.myapp     # 调试模式
aa-logprof                          # 自动学习
```

### 6.3 seccomp（系统调用过滤）

```c
// systemd / Docker / K8s 已经内置
// 应用层用 libseccomp 直接限制 syscalls

#include <seccomp.h>
scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_KILL);
seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read), 0);
seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 0);
seccomp_load(ctx);
```

### 6.4 内核更新策略

```bash
# 自动安全更新
# Ubuntu
apt install unattended-upgrades
dpkg-reconfigure unattended-upgrades

# RHEL/CentOS
dnf install dnf-automatic
systemctl enable --now dnf-automatic-install.timer

# 关键: 漏洞披露后 7 天内打补丁
# 0day 紧急 24-48 小时

# 内核热补丁（不重启）
# - kpatch (Red Hat)
# - kgraft (SUSE)
# - 阿里云 / 腾讯云 KSplice
```

## 七、网络访问控制

### 7.1 iptables / nftables / firewalld

```bash
# nftables（替代 iptables，2025 标准）
nft list ruleset

# /etc/nftables.conf
table inet filter {
  chain input {
    type filter hook input priority filter; policy drop;
    ct state established,related accept
    ct state invalid drop
    iif lo accept
    ip protocol icmp limit rate 5/second accept
    
    # SSH 限速防爆破
    tcp dport 22 ct state new limit rate 3/minute accept
    
    tcp dport { 80, 443 } accept
    
    # 业务端口仅内网
    ip saddr 10.0.0.0/8 tcp dport 5432 accept
    
    log prefix "DROP: " limit rate 5/minute
  }
  chain forward { type filter hook forward priority 0; policy drop; }
  chain output  { type filter hook output  priority 0; policy accept; }
}
```

### 7.2 端口治理

```bash
# 列出监听端口
ss -tulnp
ss -tuln4
netstat -tulnp                       # 老命令

# 关闭无用服务
systemctl disable --now rpcbind cups avahi-daemon

# 仅监听本地
# 改 /etc/mysql/mysql.conf.d/mysqld.cnf
bind-address = 127.0.0.1
```

### 7.3 主机入侵检测（HIDS）

```
✅ Wazuh           开源 SIEM + HIDS，功能最全
✅ OSSEC           老牌
✅ AIDE / Tripwire 文件完整性
✅ Falco           容器/K8s 运行时
✅ Suricata        网络 IDS
✅ Auditd          内核审计

国产:
  ✅ 安全狗
  ✅ 云锁
  ✅ 360 主机卫士
  ✅ 雷池 / 长亭洞鉴
```

### 7.4 fail2ban（爆破防护）

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 86400
findtime = 600
maxretry = 5
ignoreip = 127.0.0.1/8 10.0.0.0/8

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
```

## 八、日志与审计

### 8.1 Linux 审计子系统（auditd）

```bash
apt install -y auditd
systemctl enable --now auditd

# /etc/audit/rules.d/audit.rules
# 监控关键文件
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k privilege
-w /etc/ssh/sshd_config -p wa -k ssh
-w /root/.ssh -p wa -k ssh

# 监控关键命令
-a always,exit -F arch=b64 -S execve -F path=/bin/su -k su
-a always,exit -F arch=b64 -S execve -F path=/usr/bin/sudo -k sudo

# 监控权限变更
-a always,exit -F arch=b64 -S chmod,fchmod,fchmodat -F auid>=1000 -k perm_mod
-a always,exit -F arch=b64 -S chown,fchown,fchownat -F auid>=1000 -k perm_mod

# 监控文件删除（异常清痕）
-a always,exit -F arch=b64 -S unlink,unlinkat,rename,renameat -F auid>=1000 -k delete

# 监控网络相关
-a always,exit -F arch=b64 -S socket,bind,connect -F success=1 -k net

augenrules --load

# 查日志
ausearch -k identity --start today
aureport -au -i               # 认证报告
aureport -e -i                # 事件统计
```

### 8.2 systemd-journald

```bash
# /etc/systemd/journald.conf
[Journal]
Storage=persistent              # 持久化到磁盘
Compress=yes
SystemMaxUse=2G
RuntimeMaxUse=200M
ForwardToSyslog=yes
MaxLevelStore=info

# 查日志
journalctl -u sshd -f
journalctl --since "1 hour ago" -p err
journalctl --boot=-1
```

### 8.3 集中日志（必备）

```
本地审计 → 集中化:
  - Filebeat / Fluentd / Vector 采集
  - rsyslog → Loki / ELK
  - Wazuh Agent 上报 SIEM
  
保留周期:
  - 等保要求 ≥ 6 个月
  - PCI-DSS ≥ 1 年
  - 金融行业 ≥ 3 年
  
不可篡改:
  - 离线归档（S3 Object Lock）
  - 集中 + 仅追加
```

## 九、进程与运行时检测

### 9.1 异常进程发现

```bash
# 找异常进程
ps auxf
ps -eo user,pid,ppid,cmd | grep -v "^USER" | awk '{print $1}' | sort -u   # 用户列表

# 进程网络连接
lsof -i -P -n
ss -tulnp

# 隐藏进程（rootkit）
ps aux | wc -l
ls /proc | grep -E '^[0-9]+$' | wc -l    # 不一致 = 可疑

# 检查 /proc/<pid>/exe 是否删除
ls -l /proc/*/exe 2>/dev/null | grep deleted
```

### 9.2 rkhunter / chkrootkit

```bash
apt install -y rkhunter chkrootkit
rkhunter --update
rkhunter --check --skip-keypress
chkrootkit
```

### 9.3 Falco（运行时威胁检测）

```yaml
# falco_rules.yaml 示例
- rule: Run as root in container
  desc: Container running as root
  condition: container.id != host and proc.uid = 0 and not user_known_root_containers
  output: "Root container detected (user=%user.name container_id=%container.id)"
  priority: WARNING

- rule: Shell spawned in container
  desc: Suspicious shell in container
  condition: spawned_process and container and shell_procs
  output: "Shell in container (user=%user.name shell=%proc.name)"
  priority: CRITICAL

- rule: Sensitive file accessed
  condition: open_read and fd.name in (/etc/shadow, /etc/sudoers)
  output: "Sensitive file %fd.name accessed by %user.name"
  priority: WARNING
```

### 9.4 eBPF 现代检测

```
Tetragon (Cilium)        基于 eBPF 全栈观测 + 阻断
Tracee (Aqua)            基于 eBPF 行为分析
KubeArmor                K8s 运行时安全
Pixie                    eBPF 观测
bpftrace                 调试 + 动态追踪

优势:
  - 内核级可见性
  - 性能开销低
  - 不需修改应用
```

## 十、补丁与漏洞管理

### 10.1 漏洞扫描

```bash
# 主机漏洞扫描
✅ OpenVAS / GVM       开源
✅ Nessus              商业，行业标杆
✅ Lynis               轻量
✅ Vuls                Go 写的轻量 CVE 扫描

# CIS 合规扫描
✅ OpenSCAP
✅ CIS-CAT
✅ Lynis

# 国内
✅ 绿盟 / 启明 / 安恒 漏扫
✅ 长亭 安全方舟
✅ 阿里云态势感知
```

### 10.2 patch 流程

```
1. 漏洞情报
   - CVE 订阅: NVD, MITRE
   - 厂商通告: Ubuntu/Red Hat USN
   - 国内: CNNVD / CNVD

2. 评级
   - CVSS >= 9.0: 24h 内
   - 7.0-8.9: 7 天
   - 4.0-6.9: 30 天
   - < 4.0: 季度

3. 测试 → 灰度 → 全量
4. 验证 + 留痕
```

### 10.3 自动更新策略

```bash
# Ubuntu
cat > /etc/apt/apt.conf.d/50unattended-upgrades <<EOF
Unattended-Upgrade::Allowed-Origins {
  "\${distro_id}:\${distro_codename}-security";
  "\${distro_id}ESMApps:\${distro_codename}-apps-security";
  "\${distro_id}ESM:\${distro_codename}-infra-security";
};
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:30";
EOF

# RHEL
dnf install -y dnf-automatic
sed -i 's/apply_updates = no/apply_updates = yes/' /etc/dnf/automatic.conf
systemctl enable --now dnf-automatic.timer
```

## 十一、应急响应（IR）速查

### 11.1 入侵迹象排查

```bash
# 登录/会话
last -a | head
lastb | head                    # 失败登录
w
who -a
cat /var/log/auth.log | grep -i fail

# 用户/账户
awk -F: '$3 == 0 {print}' /etc/passwd           # 多个 UID=0
awk -F: '$2 != "x" {print}' /etc/passwd          # 空密码
grep -v '^[#$/]' /etc/sudoers /etc/sudoers.d/*

# 计划任务
crontab -l
ls -la /etc/cron.* /var/spool/cron/
cat /etc/crontab
systemctl list-timers --all

# 网络连接
netstat -antp | grep ESTAB
ss -tnp
lsof -i :22

# 进程
ps auxf | grep -v "^\[\|^USER"
ls -la /proc/*/exe 2>/dev/null | grep deleted

# 文件
find / -ctime -7 -type f -not -path "/proc/*" -not -path "/sys/*" 2>/dev/null   # 7 天内变化
find / -mtime -1 -name "*.sh" -type f 2>/dev/null
find / -size +50M -type f 2>/dev/null

# 启动项
ls /etc/init.d/ /etc/rc*.d/
systemctl list-unit-files --state=enabled
ls -la /etc/systemd/system/*.service

# 历史命令
cat ~/.bash_history
cat /root/.bash_history
last | head

# 隐藏文件 / 大文件
find / -name ".*" -type f -mtime -7 2>/dev/null
ls -laR /tmp /var/tmp /dev/shm /home/*/.* 2>/dev/null
```

### 11.2 IR 处置步骤

```
1. 隔离（断网或加策略）
   iptables -I INPUT -j DROP
   或停业务保留现场

2. 取证（不要重启！）
   - 镜像磁盘（dd / dc3dd）
   - 内存 dump（LiME / AVML）
   - 网络流量包（tcpdump）
   - 关键日志归档

3. 初步分析
   - 入侵时间窗口
   - 入侵路径（CVE / 弱密码 / 钓鱼）
   - 横向移动范围
   - 数据外泄评估

4. 清除（按 IR 流程）
   - 修补漏洞
   - 重置密码 / 密钥
   - 清除 webshell / 后门
   - 重做系统（推荐，比清更可靠）

5. 恢复 + 加强
   - 业务恢复
   - 加强监控
   - 补 IDS 规则

6. 复盘
   - 时间线
   - 改进项
   - 经验沉淀
```

### 11.3 取证工具

```
镜像:     dd, dc3dd, FTK Imager
内存:     LiME (Linux), AVML (Linux), Volatility (分析)
分析:     Sleuthkit, Autopsy, plaso/log2timeline
网络:     Wireshark, tshark, NetworkMiner
全套:     SIFT Workstation, CAINE, REMnux
国产:     美亚柏科、奇安信、绿盟
```

## 十二、合规与等保

### 12.1 等保 2.0 三级要求要点

```
1. 身份鉴别       双因素 / 复杂密码 / 锁定策略
2. 访问控制       最小权限 / 强制访问控制
3. 安全审计       日志保留 ≥ 6 个月 / 不可篡改
4. 入侵防范       入侵检测 / 漏洞扫描
5. 恶意代码防范   防病毒
6. 数据完整性     传输 / 存储加密
7. 数据保密性     重要数据加密
8. 数据备份恢复   异地备份
9. 剩余信息保护   存储介质擦除
10. 个人信息保护   合规收集 / 使用
```

### 12.2 工具映射

```
身份: PAM / Keycloak / LDAP / MFA
访问: SELinux / AppArmor / sudo
审计: auditd / Wazuh / ELK / SIEM
入侵: Falco / Suricata / OSSEC / Wazuh
反病毒: ClamAV (Linux) / 国产
加密: LUKS / TLS / Vault
备份: BorgBackup / Restic / Duplicity
```

## 十三、典型坑

| 坑 | 建议 |
|:---|:---|
| **root 远程 ssh** | 必禁 |
| **密码登录** | 强制密钥 |
| **默认密码不改** | install 后立即 |
| **未启 SELinux/AppArmor** | enforcing |
| **sudo 全开** | 命令白名单 |
| **未禁高危 SUID** | 月度审计 |
| **裸 firewalld 默认 allow** | drop |
| **未启 auditd** | 等保红线 |
| **日志只本地** | 集中 + 离线 |
| **补丁拖延** | 自动更新 |
| **共用密钥** | 一人一钥 |
| **凭证写脚本** | Vault |
| **/tmp 可执行** | noexec |
| **dmesg / kallsyms 暴露** | 限制 |
| **/proc 全开** | hidepid=2 |
| **历史命令不入审计** | sudo I/O log |
| **裸跑 SSH 22** | 改端口 + fail2ban + MFA |
| **未隔离管理网** | 管理面独立 VLAN |

## 十四、加固 Checklist（生产可对照）

```
账户:
☐ root 不可远程
☐ 密码策略（14+ / 复杂度 / 90 天）
☐ MFA 启用
☐ SSH 仅密钥
☐ SSH AllowUsers 白名单
☐ sudo 最小化 + 日志
☐ 默认密码全清

系统:
☐ SELinux/AppArmor enforcing
☐ sysctl 安全基线
☐ 内核自动更新
☐ 移除无用服务
☐ noexec/nosuid 挂载
☐ /tmp 限制大小

网络:
☐ nftables/firewalld 默认 drop
☐ 仅必要端口
☐ 监听 ip 限制
☐ fail2ban
☐ 管理网/业务网隔离

文件:
☐ 关键文件权限正确
☐ SUID/SGID 审计
☐ FIM (AIDE)
☐ LUKS 全盘加密

日志:
☐ auditd 启用
☐ journald 持久化
☐ 集中日志（≥ 6 月）
☐ 日志不可篡改

检测:
☐ Wazuh/OSSEC 部署
☐ Falco 容器侧
☐ 周度漏扫
☐ 月度 CIS 扫描

应急:
☐ IR 流程文档
☐ 取证工具就位
☐ 备份 + 异地
☐ 演练（季度）
```

## 十五、技术栈推荐（2025）

### 15.1 小团队

```
基线:     OpenSCAP + ansible-lockdown
HIDS:    Wazuh
FIM:     AIDE
日志:    journald → Loki
漏扫:    Lynis + Vuls
防火墙:  nftables
MFA:     Google Authenticator
```

### 15.2 中大企业

```
SIEM:     Wazuh / Splunk / 长亭 雷池
HIDS:     Wazuh Agent / Tetragon / Falco
漏扫:    Nessus + 自动化补丁
合规:    OpenSCAP + CIS-CAT + 等保
EDR:     SentinelOne / 奇安信
密钥:    Vault
身份:    Keycloak + MFA + SSO
应急:    SIFT + 内部 IR 团队
```

## 十六、学习路径

```
入门（2 周）:
  1. 装一台 RHEL/Ubuntu，跑 Lynis
  2. CIS 基础加固
  3. SSH 密钥 + sshd 加固
  4. 防火墙基础

中级（1 个月）:
  5. SELinux/AppArmor 实战
  6. auditd 规则编写
  7. Wazuh 部署 + 接入
  8. AIDE / FIM
  9. 自动补丁

高级（3 个月）:
  10. Falco / eBPF 运行时
  11. Capability 应用硬化
  12. systemd 服务硬化
  13. IR + 取证流程
  14. 等保合规
  15. 大规模自动化加固
```

## 十七、参考资料

```
标准:
  - CIS Benchmarks
  - NIST SP 800-53
  - DISA STIG
  - 等保 2.0 / GB/T 22239
  - PCI-DSS

书:
  - 《Linux Hardening》(O'Reilly)
  - 《Practical Linux Forensics》
  - 《The Linux Audit System》

工具:
  - OpenSCAP: https://www.open-scap.org/
  - Wazuh: https://wazuh.com/
  - Lynis: https://cisofy.com/lynis/
  - Falco: https://falco.org/
  - Tetragon: https://tetragon.io/

社区:
  - r/linuxhardening
  - awesome-linux-security GitHub
  - 国内: 看雪 / FreeBuf / 安全客
```

> 📖 **核心判断**：Linux 安全 = **基线加固 + 最小权限 + 集中日志 + HIDS 检测 + 快速补丁 + 应急响应**。**CIS Benchmarks** 是事实标准，**OpenSCAP + Ansible 自动化加固 + Wazuh SIEM** 是国内可落地的黄金组合。最容易翻车的不是技术，而是：**root 远程没禁、密码登录没关、日志不集中、补丁拖延**——这四条做不到，所有上层安全都是空中楼阁。
