# 系统维护

> Linux 日常运维 = **巡检 + 补丁 + 备份 + 日志 + 监控 + 容量规划 + 故障演练**。**事先维护成本 < 1，事后救火成本 > 100**。本章给完整的日常维护清单和自动化方案。

## 一、日常巡检 Checklist

### 1.1 每日巡检（5 分钟）

```bash
#!/bin/bash
# daily-check.sh

# 1. 系统负载
uptime
# 关注: load > CPU 核数 × 2 → 告警

# 2. 磁盘
df -h | awk 'NR>1 && $5+0 > 80 {print "[WARN] " $0}'
df -i | awk 'NR>1 && $5+0 > 80 {print "[WARN inode] " $0}'

# 3. 内存
free -h
# 检查: available < 10% → 告警

# 4. 关键服务
for svc in nginx mysql redis ssh; do
    systemctl is-active $svc >/dev/null || echo "[CRIT] $svc DOWN"
done

# 5. 关键错误
journalctl -p err --since "24 hours ago" --no-pager | wc -l
dmesg -T -l err,crit --since "24 hours ago" | head -20

# 6. SMART 健康
for d in /dev/sd?; do
    smartctl -H $d | grep -i "result\|status" || true
done

# 7. 登录异常
last -n 20
lastb -n 10                              # 失败登录

# 8. SSH 连接
ss -tnp state established '( dport = :22 or sport = :22 )'

# 9. 网络
ip a | grep -E "inet|state DOWN"
ping -c 2 -W 1 8.8.8.8

# 10. 时间同步
chronyc tracking | grep -E "Reference|Stratum|System time"
# 或 timedatectl

echo "✅ Daily check done at $(date)"
```

### 1.2 每周巡检

```bash
# 软件更新
dnf check-update --security              # RHEL 安全更新
apt list --upgradable                    # Ubuntu

# 安全审计
fail2ban-client status sshd              # 失败登录拦截
journalctl -p warning -u sshd --since "7 days ago" | grep -i "invalid\|fail"

# 容量趋势
sar -d -f /var/log/sa/sa$(date -d 'last week' +%d)    # 一周磁盘 IO
sar -r -f ...                             # 内存

# 日志归档
journalctl --vacuum-time=30d              # 清理 30 天前
logrotate -d /etc/logrotate.conf          # 检查 logrotate 配置

# 临时文件
find /tmp -type f -atime +7 -delete
find /var/tmp -type f -atime +30 -delete

# 备份验证
restic snapshots --tag daily              # 最近备份
```

### 1.3 每月巡检

```bash
# 补丁升级（先测试环境）
dnf upgrade --security --bugfix           # RHEL
apt upgrade

# 内核 / GRUB 清理
dnf remove --oldinstallonly --setopt installonly_limit=2 kernel
apt autoremove --purge

# 证书过期
for cert in /etc/ssl/certs/*.pem /etc/letsencrypt/live/*/cert.pem; do
    [ -f "$cert" ] && openssl x509 -in "$cert" -noout -enddate -subject
done | sort

# 容量规划
df -h | awk 'NR>1 {print $5 " " $6}' | sort -rn

# 备份恢复演练（关键）
restic restore latest --target /tmp/restore-test --include /etc

# 防火墙规则审计
firewall-cmd --list-all
nft list ruleset > /var/log/audit/firewall-$(date +%F).log

# 用户审计
awk -F: '$3 >= 1000 {print $1, $3}' /etc/passwd     # 普通用户
awk -F: '$2 == "" {print $1}' /etc/shadow            # 无密码（危险）
```

## 二、补丁与升级

### 2.1 升级策略

```
分级:
  Critical Security      → 24-48h 内 (CVE 高危)
  High                   → 1 周内
  Normal                 → 月度窗口
  Optional               → 季度评估

环境流转:
  dev → staging → canary (10%) → 全量

时机:
  - 业务低峰
  - 提前公告
  - 备份 + 快照
  - 回滚预案
```

### 2.2 RHEL 系升级

```bash
# 只查不装
dnf check-update
dnf updateinfo list security             # 看安全更新

# 安全更新
dnf upgrade --security                   # 仅安全
dnf upgrade --security --bugfix          # 安全+bug

# 锁定版本（生产）
dnf versionlock list
dnf versionlock add nginx-1.24.0
dnf versionlock delete nginx

# 单包升级
dnf upgrade nginx

# 跨大版本升级（leapp）
leapp preupgrade                         # CentOS 7 → 8
leapp upgrade

# 大版本升级 RHEL/Rocky 8 → 9
leapp upgrade --target 9.4
```

### 2.3 Debian/Ubuntu 升级

```bash
apt update && apt list --upgradable

# 仅安全
unattended-upgrade --dry-run             # 看会装啥
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
# 配置 /etc/apt/apt.conf.d/50unattended-upgrades

# 锁定版本
apt-mark hold nginx
apt-mark showhold

# 大版本升级
do-release-upgrade                       # 22.04 → 24.04
```

### 2.4 内核升级（不重启 → kpatch / kexec）

```bash
# 看可用内核
dnf list kernel --showduplicates

# 升级 + 保留旧内核
dnf install kernel
dnf list installed kernel

# 设默认
grubby --default-kernel
grubby --set-default /boot/vmlinuz-NEW

# 不停机 kpatch（RHEL 商用）
kpatch list
kpatch load patch.ko

# kexec（重启快 → 不走 BIOS）
kexec -l /boot/vmlinuz-NEW --initrd=/boot/initramfs-NEW.img --reuse-cmdline
systemctl kexec
```

### 2.5 升级前后必做

```bash
# 升级前
1. 看 changelog
   dnf updateinfo info <package>
2. 备份配置
   tar czf /backup/etc-$(date +%F).tgz /etc
3. 创建快照（虚拟机 / LVM）
   lvcreate -L 10G -s -n snap-pre-upgrade /dev/vg/lv_root
4. 通知业务
5. 关闭非必要服务

# 升级中
6. dnf upgrade -y
7. 重启（内核 / glibc 更新后必须）

# 升级后
8. systemctl --failed
9. 跑健康检查
10. 24h 观察期，不行就回滚
```

## 三、备份与恢复

### 3.1 3-2-1 备份策略

```
3 份数据
2 种介质（本地 + 远程）
1 份异地
+ 1 份离线（防勒索）

实际:
  - 主存储（线上）
  - 本地备份（不同盘 / 不同机柜）
  - 异地备份（云对象存储）
  - 离线归档（冷归档 / 磁带）
```

### 3.2 关键数据分类

```
系统类:
  /etc                  ⭐ 配置
  /var/spool/cron       定时任务
  /home                 用户数据
  /root                 root home
  installed packages   dnf list installed
  /var/log/audit       审计

应用类:
  数据库 dump
  应用数据目录
  /opt 自部署
  容器卷
  K8s manifests

不需要:
  /tmp /var/tmp
  /var/cache
  /var/log（按需）
  /proc /sys /dev
```

### 3.3 备份脚本模板

```bash
#!/bin/bash
# /usr/local/bin/backup.sh
set -euo pipefail

DATE=$(date +%F)
RETENTION_DAYS=30
LOG=/var/log/backup.log

exec > >(tee -a $LOG) 2>&1

echo "=== Backup started at $(date) ==="

# 1. 数据库 dump（先备库再 mysqldump 避免锁）
mysqldump --single-transaction --routines --triggers --events \
  --all-databases > /backup/mysql-$DATE.sql
gzip /backup/mysql-$DATE.sql

# 2. 文件备份（restic 推荐）
export RESTIC_PASSWORD_FILE=/etc/restic.pwd
restic backup /etc /home /var/spool/cron /opt/myapp \
  --exclude-file=/etc/restic-exclude.txt \
  --tag daily

# 3. 归档清理
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune

# 4. 同步到异地（rclone → 对象存储）
rclone copy /backup s3:my-bucket/server01/$DATE \
  --transfers=4 --bwlimit=20M

# 5. 校验
restic check

echo "=== Backup done at $(date) ==="
```

### 3.4 systemd timer 定时

```ini
# /etc/systemd/system/backup.service
[Service]
Type=oneshot
User=root
ExecStart=/usr/local/bin/backup.sh
Nice=10
IOSchedulingClass=idle
IOSchedulingPriority=7

# /etc/systemd/system/backup.timer
[Timer]
OnCalendar=*-*-* 02:00:00
RandomizedDelaySec=30min
Persistent=true                          # 错过会补跑

[Install]
WantedBy=timers.target
```

### 3.5 恢复演练（关键）

```bash
# 演练频率: 至少季度
# 演练内容:
#   - 单文件恢复
#   - 整目录恢复
#   - 数据库恢复
#   - 跨主机恢复

# restic 恢复
restic snapshots --tag daily
restic restore <id> --target /restore --include /etc/nginx

# MySQL 恢复
zcat /backup/mysql-2026-06-26.sql.gz | mysql -u root -p

# 跨主机
restic -r s3:bucket/server01 restore latest --target ./

# 验证恢复
diff -r /restore/etc/nginx /etc/nginx
```

### 3.6 灾难恢复（DR）

```
RTO (Recovery Time Objective)   恢复时间目标
RPO (Recovery Point Objective)  恢复点目标 (数据丢失上限)

分级:
  Cold (RPO 24h)   每日备份 + 手动恢复 ~ 几小时
  Warm (RPO 1h)    增量备份 + 备机就绪 ~ 几十分钟
  Hot  (RPO < 1m)  实时同步 + 主备切换 ~ 几分钟

工具:
  - DRBD (块级实时同步)
  - rsync + 增量
  - 数据库主从 / 半同步
  - 存储级同步 (SAN / Ceph)
  - 云上跨 Region 多活
```

## 四、日志治理

### 4.1 日志生命周期

```
产生 → 收集 → 解析 → 索引 → 存储 → 查询 → 归档 → 销毁
       ↓        ↓              ↓                ↓
   journald    Loki/ES     冷热分层         合规留存
   Filebeat                                  6个月-3年
```

### 4.2 logrotate 高级

```bash
# /etc/logrotate.d/myapp
/var/log/myapp/*.log {
    daily
    rotate 30
    compress
    delaycompress
    dateext                              # filename.log-20260626
    dateformat -%Y%m%d
    missingok
    notifempty
    create 0640 myapp myapp
    sharedscripts
    
    prerotate
        # 不需要时可省
    endscript
    
    postrotate
        # 通知应用 reopen 日志
        kill -USR1 $(cat /var/run/myapp.pid 2>/dev/null) || true
    endscript
}

# 测试
logrotate -d /etc/logrotate.d/myapp     # debug
logrotate -f /etc/logrotate.d/myapp     # 强制
```

### 4.3 系统日志归档（Loki / ELK）

```bash
# Promtail → Loki
# /etc/promtail/config.yml
scrape_configs:
  - job_name: system
    journal:
      max_age: 12h
      labels:
        job: systemd-journal
        host: server01
    relabel_configs:
      - source_labels: ['__journal__systemd_unit']
        target_label: 'unit'

# 或 rsyslog → Logstash → ES
# /etc/rsyslog.d/forward.conf
*.* @@logstash:5514;RSYSLOG_SyslogProtocol23Format
```

### 4.4 日志合规（等保 / 个保法）

```
留存要求:
  等保 2.0: ≥ 6 个月
  网络安全法: ≥ 6 个月
  个保法: 视场景

必留:
  - 系统登录 (last/lastb/wtmp)
  - sudo 操作 (auth.log)
  - SSH 会话 (sshd)
  - audit (auditd)
  - 应用关键操作

加固:
  - 日志远程集中（防本地删）
  - WORM (Write Once Read Many) 存储
  - 签名 / hash 校验
  - 访问审计
```

### 4.5 audit（操作审计）

```bash
# 启用
systemctl enable --now auditd

# 配置 /etc/audit/rules.d/audit.rules
-w /etc/passwd -p wa -k passwd-changes
-w /etc/shadow -p wa -k shadow-changes
-w /etc/ssh/sshd_config -p wa -k sshd-changes
-w /var/log/audit/ -p wa -k audit-log
-a always,exit -F arch=b64 -S execve -F uid>=1000 -F auid>=1000 -F auid!=4294967295 -k userexec
-a always,exit -F arch=b64 -S unlink -F dir=/etc -k etc-delete

augenrules --load
auditctl -l                              # 当前规则

# 查日志
ausearch -k passwd-changes
ausearch -ui 1000 --start today
aureport -u                              # 用户活动汇总
aureport -au                             # 认证报告
```

## 五、用户与凭据管理

### 5.1 SSH 密钥轮换

```bash
# 生成新 key（ed25519 推荐）
ssh-keygen -t ed25519 -C "alice@laptop-2026"
# 不推荐 RSA < 4096

# 部署到主机
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@host

# 批量 (Ansible)
- name: deploy ssh key
  ansible.posix.authorized_key:
    user: ops
    state: present
    key: "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"

# 撤销旧 key
sed -i '/old_key_fingerprint/d' ~/.ssh/authorized_keys
```

### 5.2 SSH 加固

```bash
# /etc/ssh/sshd_config
Port 22
PermitRootLogin no                       # 禁 root 直登
PasswordAuthentication no                # 仅密钥
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
AllowUsers alice bob                     # 白名单
AllowGroups wheel devops

# 限制 cipher（合规）
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com
KexAlgorithms curve25519-sha256@libssh.org

systemctl reload sshd
```

### 5.3 fail2ban（防暴力破解）

```bash
dnf install fail2ban
# /etc/fail2ban/jail.d/sshd.conf
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/secure
maxretry = 5
bantime = 3600
findtime = 600

systemctl enable --now fail2ban
fail2ban-client status sshd
fail2ban-client set sshd unbanip 1.2.3.4
```

### 5.4 跳板机 / 堡垒机

```
开源:
  - JumpServer (国产，最流行)
  - Teleport (gravitational)
  - SSH ProxyCommand (轻量)

JumpServer 特性:
  - 用户管理 / 资产授权
  - 多因素认证 (MFA)
  - 会话录屏
  - 命令审计
  - 数据库代理
```

## 六、容量规划

### 6.1 趋势分析

```bash
# 磁盘增长（每天采集）
df -h | awk -v date="$(date +%F)" 'NR>1 {print date, $1, $5, $6}' >> /var/log/df-trend.log

# 历史趋势分析
awk '/myapp/ {sub("%", "", $3); print $1, $3}' /var/log/df-trend.log

# 月度报告（Grafana / 自研）
```

### 6.2 增长预测

```python
# 简单线性预测
import numpy as np

days = [1, 30, 60, 90]
used_gb = [120, 145, 172, 200]

slope, intercept = np.polyfit(days, used_gb, 1)
threshold = 800              # 总容量 1TB, 警戒 80%
days_to_full = (threshold - intercept) / slope
print(f"预计 {days_to_full:.0f} 天后达到 {threshold} GB")
```

### 6.3 扩容窗口

```
触发阈值:
  Disk 80%  → 预警
  Disk 85%  → 工单
  Disk 90%  → 紧急扩容
  Disk 95%  → 战时

CPU 持续 > 70% / Memory > 80% 同理

云上自动:
  - 阿里云 ESS 弹性伸缩
  - AWS Auto Scaling
  - K8s HPA / VPA / Cluster Autoscaler
```

## 七、性能基线

### 7.1 sar 长期采集

```bash
# 启用
systemctl enable --now sysstat
# /etc/sysconfig/sysstat (RHEL)
HISTORY=28                                # 保留 28 天
COMPRESSAFTER=10
SADC_OPTIONS="-S DISK"

# 历史看板
sar -u 1 60                              # CPU
sar -r 1 60                              # 内存
sar -d 1 60                              # 磁盘
sar -n DEV 1 60                          # 网络
sar -q                                    # 负载

# 看历史
sar -u -f /var/log/sa/sa$(date -d 'yesterday' +%d)
sar -u -s 14:00:00 -e 15:00:00 -f /var/log/sa/sa15
```

### 7.2 基线档案

```
每月一次生成基线:
  - CPU 平均/峰值
  - 内存平均/峰值
  - 磁盘 IO IOPS / 吞吐
  - 网络 in/out
  - 应用 QPS / 延迟

存档对比，量化"是不是变慢了"
```

## 八、故障演练（混沌工程）

### 8.1 演练矩阵

| 场景 | 工具 | 频率 |
|:---|:---|:---|
| **CPU 满载** | stress-ng | 月 |
| **内存压力** | stress-ng --vm | 月 |
| **磁盘满** | dd / fallocate | 季 |
| **网络丢包** | tc netem | 月 |
| **网络延迟** | tc netem delay | 月 |
| **服务挂掉** | systemctl stop | 月 |
| **节点宕机** | ipmitool / 关机 | 季 |
| **机房断电** | 应急 | 年 |

### 8.2 工具

```bash
# 网络故障注入
tc qdisc add dev eth0 root netem delay 100ms 20ms loss 5%
tc qdisc del dev eth0 root                # 恢复

# 资源压力
stress-ng --cpu 8 --io 4 --vm 4 --vm-bytes 1G --timeout 5m

# K8s 混沌
chaos-mesh                                # 国产开源
litmus                                     # CNCF
chaoskube                                  # 随机杀 Pod
```

## 九、自动化运维

### 9.1 Ansible 维护剧本

```yaml
# maintenance.yml
- hosts: all
  tasks:
    - name: 安全更新
      dnf:
        name: '*'
        state: latest
        security: yes
      when: ansible_os_family == "RedHat"
    
    - name: 重启如内核变更
      reboot:
        msg: "kernel update"
      when: ansible_facts.kernel_required_reboot | default(false)
    
    - name: 清理 journal
      shell: journalctl --vacuum-time=30d
    
    - name: 清理旧内核
      shell: dnf remove --oldinstallonly --setopt installonly_limit=2 kernel -y

# 执行
ansible-playbook -i hosts maintenance.yml --limit canary
ansible-playbook -i hosts maintenance.yml --limit all -f 20
```

### 9.2 cron / systemd timer 任务

```bash
# 经典任务表
0 2 * * *  /usr/local/bin/backup.sh
0 3 * * 0  /usr/local/bin/weekly-report.sh
0 4 * * 1  /usr/local/bin/security-scan.sh
30 4 * * * /usr/local/bin/cleanup.sh

# 现代用 systemd timer (见前文)
```

### 9.3 巡检平台

```
开源:
  - Prometheus + Alertmanager + Grafana
  - Zabbix
  - Nagios / Icinga
  - NetData
  - 国产: 夜莺 Nightingale ⭐

自建巡检脚本:
  - Ansible ad-hoc
  - Python + paramiko
  - Bash + ssh + 并行
  - Salt
```

## 十、典型坑

| 坑 | 建议 |
|:---|:---|
| **备份只跑没恢复** | 必须做恢复演练 |
| **磁盘满了应用挂** | 早期告警 + 自动清理 |
| **不限 journal 大小** | SystemMaxUse 限制 |
| **直接 reboot 无预演** | 先 systemd-analyze critical-chain |
| **升级没回滚预案** | LVM 快照 / 虚拟机快照 |
| **日志全本地** | 远程集中 + WORM |
| **SSH 全 root + 密码** | 禁 root + 仅密钥 |
| **不轮换密钥** | 离职 / 周期轮换 |
| **fail2ban 没装** | 必装 (sshd / nginx) |
| **audit 没开** | 等保必装 |
| **cron 日志没监控** | 任务失败无感知 |
| **业务高峰窗口维护** | 必须有窗口期 |
| **演练只做一次** | 季度 / 半年 |
| **快照不清理** | LVM 快照满了原盘 IO 暴跌 |
| **大版本跨级升级** | 严格 leapp / do-release-upgrade |

## 十一、维护 Calendar

```
每日:
  ☐ 磁盘 / 内存 / 服务状态
  ☐ 日志错误浏览
  ☐ 告警检查

每周:
  ☐ 安全更新评估
  ☐ 失败登录审查
  ☐ 容量趋势
  ☐ 备份验证

每月:
  ☐ 补丁升级（测试 → 生产）
  ☐ 证书过期检查
  ☐ 备份恢复演练
  ☐ 防火墙规则审计
  ☐ 故障演练（单项）

每季度:
  ☐ 大版本评估
  ☐ DR 演练
  ☐ 安全扫描
  ☐ 容量规划
  ☐ 性能基线刷新

每年:
  ☐ 灾备切换演练
  ☐ 大版本升级窗口
  ☐ 等保测评
  ☐ 文档审计
```

## 十二、推荐栈（2025）

```
监控:        Prometheus + Grafana + 夜莺
日志:        Loki + Promtail + Grafana
告警:        Alertmanager + PagerDuty / 飞书机器人
配置管理:    Ansible + GitOps
备份:        restic + S3 / OSS / MinIO
凭据:        Vault / Bitwarden
跳板机:      JumpServer
安全:        fail2ban + auditd + ClamAV
补丁:        unattended-upgrades / dnf-automatic
混沌:        Chaos Mesh / Litmus
```

## 十三、国产化清单

```
国产工具替代:
  - 夜莺 Nightingale (替 Prometheus + Grafana)
  - 哲库 GoEdge (替 Cloudflare)
  - JumpServer (堡垒机国产首选)
  - 飞致云 DataEase (BI)
  - 蓝鲸 BlueKing (腾讯，运维平台)
  - 阿里 SLS / 腾讯 CLS (日志)
  - 腾讯 TPM / 阿里 ARMS (APM)
  - 安恒 / 奇安信 / 启明星辰 (安全)
  - 华三 / 锐捷 (网络)

合规:
  - 等保 2.0 三级
  - 信创 PKS (Phytium-Kylin-Sugon)
  - 国密 SM2/SM3/SM4
  - 数据出境合规
```

## 十四、学习路径

```
入门（1 月）:
  1. 日常巡检命令
  2. systemd 服务管理
  3. logrotate 配置
  4. cron / systemd timer
  5. 备份基础 (rsync / tar)

中级（3 月）:
  6. restic 增量备份
  7. Ansible 批量运维
  8. fail2ban / auditd
  9. SSH 加固 + JumpServer
  10. 监控告警 (Prometheus)

高级（6 月+）:
  11. 灾备方案设计
  12. 混沌演练
  13. 自动化巡检平台
  14. 合规审计（等保）
  15. 内核 / 大版本升级 (leapp)

专家:
  16. SRE 体系建设
  17. 自研运维平台
  18. 跨数据中心容灾
```

## 十五、参考资料

```
官方:
  - Red Hat System Administrator's Guide
  - Ubuntu Server Documentation
  - Ansible Documentation
  - restic.net

书籍:
  - 《Site Reliability Engineering》Google SRE
  - 《Linux 系统管理技术手册》
  - 《构建可扩展的 Web 站点》
  - 《SRE 工作手册》

社区:
  - SRE Workbook
  - 阿里巴巴运维平台白皮书
  - 国内运维社区 (DBAplus / DevOps China)
```

> 📖 **核心判断**：系统维护 = **巡检 + 补丁 + 备份 + 演练 + 自动化**。**备份只能称作"复制"，做过恢复演练的备份才是真备份**。**SSH 仅密钥 + fail2ban + JumpServer** 是堡垒线最低标准。补丁要分级（Critical 24h / High 1周 / Normal 月度），永远先在 canary 环境验证。**Ansible + 夜莺 + restic + JumpServer** 是 2025 国内自建运维栈的黄金组合。

