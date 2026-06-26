# 最佳实践

> Linux 最佳实践 = **SRE 方法论 + 自动化（Ansible/IaC）+ 监控告警（Prometheus/夜莺）+ 备份与 DR + 安全基线 + 国产 OS 选型 + Toolbox 推荐**。本章把"会用"升级到"会运营"，给可复制、可验证的工程化方案。

## 一、SRE 方法论（Google SRE）

### 1.1 核心原则

```
SLI / SLO / SLA
  SLI  Service Level Indicator  指标（如成功率 / P99 延迟）
  SLO  Service Level Objective  目标（如 99.95%）
  SLA  Service Level Agreement  合约（对客户的承诺）

错误预算 (Error Budget)
  100% - SLO = 允许失败比例
  耗尽 = 停止上新功能 → 修可靠性

黄金信号 (Golden Signals)
  Latency  延迟
  Traffic  流量
  Errors   错误率
  Saturation 饱和度

四个度量 (USE / RED)
  USE   Utilization / Saturation / Errors → 资源视角
  RED   Rate / Errors / Duration → 服务视角
```

### 1.2 On-Call 工程化

```
轮值 (rotation):
  - 主备双人，时区分散
  - 7×24 不堆同一人 → 倦怠

告警分级:
  P0  立即响应   服务全挂 / 大量用户感知
  P1  15min     部分功能挂
  P2  1h        异常但可用
  P3  工作时间  趋势性问题

告警纪律:
  - 告警必须可操作
  - 噪音 > 30%/周 = 必须治理
  - 复盘文档（blameless postmortem）
  - 每次故障 → action item 入 backlog
```

### 1.3 容量规划

```
方法:
  1. 基线采样（Prometheus 历史）
  2. 业务预测（QPS 增长曲线）
  3. 压测验证（wrk/jmeter）
  4. 留 30-50% buffer（突发）

红线:
  CPU      持续 > 70%   预警
  Mem      > 80%        预警
  Disk     > 80%        工单
  连接数   > 70% max    预警
```

## 二、自动化运维栈

### 2.1 选型矩阵

| 场景 | 推荐 | 说明 |
|:---|:---|:---|
| 配置批量下发 | **Ansible** ⭐ | agentless, YAML 简单, SSH |
| 大规模长期管理 | SaltStack / Puppet | agent，更快 |
| 基础设施声明式 | **Terraform / Pulumi** | 云资源 |
| K8s GitOps | **Argo CD / Flux** | 集群应用 |
| 任务编排 | **GitLab CI / Jenkins / Tekton** | 流水线 |
| 国产平台 | **蓝鲸 BlueKing / JumpServer** | 一体化运维 |

### 2.2 Ansible 生产模板

```yaml
# inventory/hosts.yml
all:
  children:
    web:
      hosts:
        web01.prod: { ansible_host: 10.0.1.10 }
        web02.prod: { ansible_host: 10.0.1.11 }
    db:
      hosts:
        db01.prod: { ansible_host: 10.0.2.10 }
  vars:
    ansible_user: ops
    ansible_ssh_private_key_file: ~/.ssh/ops_ed25519
    ansible_become: true
```

```yaml
# playbooks/web.yml
- hosts: web
  serial: 30%                                # 滚动 30%
  max_fail_percentage: 0
  roles:
    - common
    - nginx
    - app
  tasks:
    - name: 健康检查
      uri:
        url: "http://{{ inventory_hostname }}:8080/health"
        status_code: 200
      retries: 5
      delay: 3
```

```yaml
# roles/common/tasks/main.yml
- name: 安全更新
  dnf:
    name: '*'
    state: latest
    security: yes
  when: ansible_os_family == "RedHat"

- name: 标准 sysctl
  ansible.posix.sysctl:
    name: "{{ item.name }}"
    value: "{{ item.value }}"
    state: present
    reload: yes
  loop:
    - { name: net.core.somaxconn, value: 65535 }
    - { name: vm.swappiness, value: 10 }

- name: 部署 SSH 密钥
  ansible.posix.authorized_key:
    user: ops
    state: present
    key: "{{ lookup('file', 'public_keys/' + item) }}"
  loop:
    - alice.pub
    - bob.pub

- name: 启 chrony
  systemd:
    name: chronyd
    enabled: yes
    state: started
```

### 2.3 用法

```bash
ansible-inventory -i hosts.yml --graph
ansible all -m ping
ansible web -m shell -a "uptime"
ansible-playbook -i hosts.yml playbooks/web.yml --check        # dry-run
ansible-playbook -i hosts.yml playbooks/web.yml --tags nginx
ansible-playbook -i hosts.yml playbooks/web.yml --limit web01 -v
```

### 2.4 IaC：服务器初始化模板

```bash
# 一台新机进群必做（写成 playbook 化）
1. hostname / 时区 / NTP
2. sshd 加固（禁 root + 仅密钥）
3. 用户 + sudoers
4. fail2ban
5. firewall 基线
6. SELinux/AppArmor 策略
7. sysctl 标准
8. limits.conf
9. tuned profile
10. logrotate / journald 限大小
11. node_exporter + 监控接入
12. 备份目录 / 日志归集
13. CMDB 登记
```

## 三、监控告警栈

### 3.1 选型

```
开源主流:
  Prometheus + Grafana + Alertmanager  指标
  Loki / ELK                            日志
  Tempo / Jaeger                         链路
  OpenTelemetry                          统一采集

国产推荐:
  夜莺 Nightingale ⭐  Prom + 告警 + Grafana 整合
  阿里云 SLS         日志
  腾讯 CLS           日志
  Pinpoint / SkyWalking  国产 APM

主机采集:
  node_exporter      系统指标
  process_exporter   进程
  blackbox_exporter  探活
```

### 3.2 Prometheus 节点指标基线

```yaml
# 标配 alert rule
- alert: HighCPU
  expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 10m

- alert: HighMemory
  expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 90
  for: 5m

- alert: DiskFull
  expr: 100 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes * 100) > 85
  for: 5m

- alert: InodeFull
  expr: 100 - (node_filesystem_files_free / node_filesystem_files * 100) > 85
  for: 5m

- alert: HighIOWait
  expr: avg by(instance) (rate(node_cpu_seconds_total{mode="iowait"}[5m])) * 100 > 30
  for: 10m

- alert: TCPRetransHigh
  expr: rate(node_netstat_Tcp_RetransSegs[5m]) / rate(node_netstat_Tcp_OutSegs[5m]) > 0.05
  for: 10m

- alert: NodeDown
  expr: up{job="node"} == 0
  for: 1m
  labels: { severity: P0 }
```

### 3.3 告警路由（飞书/钉钉/PagerDuty）

```yaml
# alertmanager.yml
route:
  group_by: ['alertname','instance']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: feishu
  routes:
    - match: { severity: P0 }
      receiver: pagerduty
    - match_re: { service: ^(web|api)$ }
      receiver: feishu-web

receivers:
  - name: feishu
    webhook_configs:
      - url: https://open.feishu.cn/open-apis/bot/v2/hook/xxx
  - name: pagerduty
    pagerduty_configs:
      - service_key: ***
```

## 四、备份与灾备 DR

### 4.1 3-2-1 策略

```
3 份数据
2 种介质（本地 + 远程）
1 份异地
+ 1 份离线（防勒索）
```

### 4.2 分级 RTO/RPO

| 级别 | RPO | RTO | 方案 |
|:---|:---|:---|:---|
| Cold | 24h | 几小时 | 每日 dump + 对象存储 |
| Warm | 1h | 30min | 增量 + 备机就绪 |
| Hot | < 1min | 几分钟 | 主从同步 / 多活 |

### 4.3 工具栈

```
文件:       restic + S3 (兼容 MinIO/OSS/COS)
数据库:     mysqldump / pg_dump / Xtrabackup / WAL-G
块设备:     LVM 快照 / DRBD
对象存储:   rclone + 多 region
异地:       跨 IDC + 加密
合规:       WORM (Write Once Read Many) + 日志签名
```

### 4.4 演练频率

```
☐ 月度: 单文件恢复
☐ 季度: 整目录 + 数据库
☐ 半年: 跨主机恢复
☐ 年度: 灾备切换（异地主备切换）
```

### 4.5 备份脚本骨架

```bash
#!/usr/bin/env bash
set -euo pipefail
exec > >(tee -a /var/log/backup.log) 2>&1

DATE=$(date +%F)

# 1. 数据库 dump
mysqldump --single-transaction --routines --triggers \
  --all-databases | gzip > /backup/mysql-$DATE.sql.gz

# 2. 文件 (restic)
export RESTIC_PASSWORD_FILE=/etc/restic/pass
restic backup /etc /home /var/spool/cron /opt/myapp --tag daily

# 3. 保留策略
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune

# 4. 异地
rclone copy /backup s3:bucket/$DATE --bwlimit=20M

# 5. 校验
restic check

echo "✅ Backup $DATE done"
```

## 五、安全基线

### 5.1 CIS Benchmark（必参照）

```
项目大类:
  1. Initial Setup          时区 / chrony / banner
  2. Services              关掉非必要服务
  3. Network Configuration  内核 sysctl / iptables / IPv6
  4. Logging and Auditing  auditd / rsyslog / logrotate
  5. Access, Auth          PAM / SSH / sudo / cron
  6. System Maintenance    文件权限 / SUID 审计
```

### 5.2 自动加固工具

```bash
# Lynis 扫描
lynis audit system

# OpenSCAP（合规扫描）
oscap xccdf eval --profile cis_server_l1 \
  --report report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# 自动应用
oscap xccdf eval --profile cis_server_l1 --remediate \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# ansible-lockdown / dev-sec/ansible-collection-hardening
```

### 5.3 SSH 加固模板

```ini
# /etc/ssh/sshd_config
Port 22
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers alice bob
AllowGroups wheel devops
X11Forwarding no
PermitEmptyPasswords no
MaxSessions 5
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com
KexAlgorithms curve25519-sha256@libssh.org
LogLevel VERBOSE
```

### 5.4 fail2ban 必装

```bash
dnf install fail2ban
cat > /etc/fail2ban/jail.d/sshd.local <<EOF
[sshd]
enabled = true
port = 22
maxretry = 5
bantime = 3600
findtime = 600
EOF
systemctl enable --now fail2ban
```

### 5.5 audit 必开

```bash
# /etc/audit/rules.d/audit.rules
-w /etc/passwd -p wa -k passwd-changes
-w /etc/shadow -p wa -k shadow-changes
-w /etc/ssh/sshd_config -p wa -k sshd-changes
-w /var/log/audit/ -p wa -k audit-log

augenrules --load
ausearch -k passwd-changes
```

## 六、日志治理

### 6.1 journald 限大小

```ini
# /etc/systemd/journald.conf
[Journal]
SystemMaxUse=2G
SystemKeepFree=1G
MaxFileSec=1month
ForwardToSyslog=no
Compress=yes
Seal=yes                                       # 防篡改
```

### 6.2 logrotate 模板

```
/var/log/myapp/*.log {
    daily
    rotate 30
    compress
    delaycompress
    dateext
    missingok
    notifempty
    create 0640 myapp myapp
    sharedscripts
    postrotate
        kill -USR1 $(cat /var/run/myapp.pid 2>/dev/null) || true
    endscript
}
```

### 6.3 集中化（Loki / ELK）

```
推荐:
  Loki + Promtail        轻量首选（夜莺整合好）
  ELK (Elasticsearch + Logstash + Kibana)   功能全
  ClickHouse + Vector     高性能、低成本（自研常用）
  阿里 SLS / 腾讯 CLS     SaaS 化

合规留存:
  等保 2.0    ≥ 6 个月
  网络安全法  ≥ 6 个月
  关键操作日志要 WORM
```

## 七、堡垒机 / 集中身份

### 7.1 堡垒机

```
开源:
  JumpServer ⭐ 国产首选
  Teleport (gravitational)
  SSHGate / Apache Guacamole

特性:
  - 用户授权 / 资产管理
  - 多因素 MFA
  - 会话录屏
  - 命令审计
  - 数据库代理
  - 工单 + 工单单据
```

### 7.2 集中身份

```
LDAP / FreeIPA / OpenLDAP   传统
Keycloak                     现代 OIDC/SAML（开源首选）
GitLab / 企微 / 飞书 SSO   公司账号集成
```

## 八、容量与成本

### 8.1 容量看板

```
关键指标:
  CPU 利用率 (历史 P95)
  内存利用率
  Disk used / inode
  网卡带宽
  连接数 / TPS / QPS
  数据库连接池

预测:
  Prophet / Holt-Winters    时序预测
  线性回归（简化）

阈值触发:
  Disk 80%   工单
  Disk 90%   紧急
  Mem 85%    工单
```

### 8.2 成本优化

```
1. 关停僵尸资源（无流量 30 天）
2. RI / Saving Plan（云上预留）
3. Spot 实例（计算型）
4. 冷热分层（对象存储 IA / 归档）
5. 镜像瘦身 + 多阶段构建
6. 容器密度提升（K8s VPA + 调度）
7. 数据库读写分离
```

## 九、变更管理

### 9.1 变更分级

```
小变更   配置改动 / 重启服务   on-call
中变更   升级 / 扩容 / 改架构  审批 + 文档
大变更   架构重做 / 跨多团队   评审会 + 灰度
```

### 9.2 变更纪律

```
1. 工单先行（含回滚预案）
2. 备份 / 快照
3. 灰度（1% → 10% → 100%）
4. 监控 + on-call 跟班
5. 失败立刻回滚（先恢复，再查因）
6. 变更窗口（业务低峰）
7. 变更冻结（大促 / 节假日）
```

### 9.3 灰度模板

```bash
# Ansible serial 滚动
- hosts: web
  serial:
    - 1                                         # 单台试
    - "10%"                                     # 10%
    - "30%"
    - "100%"
  max_fail_percentage: 0
  pre_tasks:
    - name: 摘流量
      uri: { url: "http://lb/drain/{{ inventory_hostname }}" }
  tasks:
    - import_role: { name: deploy }
    - name: 健康检查
      uri: { url: "http://{{ inventory_hostname }}/health", status_code: 200 }
      retries: 10
  post_tasks:
    - name: 回流量
      uri: { url: "http://lb/up/{{ inventory_hostname }}" }
```

## 十、性能基线与压测

### 10.1 必跑基线

```bash
# CPU
sysbench cpu --threads=$(nproc) --time=60 run

# 内存
sysbench memory --threads=8 run

# 磁盘
fio --name=randrw --rw=randrw --bs=4k -size=10G --runtime=60 --time_based --direct=1

# 网络
iperf3 -s
iperf3 -c server -P 8 -t 60

# HTTP
wrk -t 8 -c 1000 -d 60s http://x/
hey -n 100000 -c 1000 http://x/
vegeta attack -rate=1000/s -duration=60s -targets=t.txt | vegeta report
```

### 10.2 基线档案模板

```
每月生成:
  - CPU: 平均 / 峰值 / 各核分布
  - 内存: avail / cache / swap
  - Disk: IOPS / 吞吐 / latency p50/p99
  - Net: bandwidth / pps / retrans
  - App: QPS / latency / error rate

存档 + 同比对比
```

## 十一、国产 OS 选型矩阵

| 场景 | 推荐 |
|:---|:---|
| 服务器（CentOS 替代） | **Anolis OS 23** ⭐ 阿里, 完全兼容 |
| 自研创新（新内核） | **openEuler 24.03 LTS** ⭐ 华为, 6.x 内核 |
| 信创 / 党政军 | **麒麟 V10 SP3** / **统信 UOS V20** |
| 腾讯系 | **OpenCloudOS 9** |
| 桌面 | **统信 UOS V20** / 优麒麟 |
| ARM 服务器 | openEuler / Anolis（鲲鹏 / 飞腾 适配最好） |
| LoongArch 龙芯 | 麒麟 V10 / 统信 UOS |

## 十二、Toolbox（精选）

```
监控:    Prometheus + Grafana + 夜莺
日志:    Loki + Promtail + Grafana
告警:    Alertmanager + 飞书机器人 / PagerDuty
配置:    Ansible + GitLab CI + Argo CD
备份:    restic + S3 + 跨地 region
凭据:    Vault / Bitwarden self-host
堡垒:    JumpServer
安全:    fail2ban + auditd + ClamAV + Lynis + OpenSCAP
补丁:    dnf-automatic / unattended-upgrades
混沌:    Chaos Mesh / Litmus
APM:    SkyWalking (国产) / Jaeger
作业:    Tekton / Argo Workflows
镜像:    Harbor (国产) / Quay
追踪:    OpenTelemetry
```

## 十三、典型坑（最佳实践）

| 坑 | 建议 |
|:---|:---|
| **告警噪音泛滥** | 月度治理 + 必须可操作 |
| **备份没演练** | 季度恢复演练 |
| **变更无回滚预案** | LVM 快照 / 灰度 |
| **手工运维不入 Git** | 一切 IaC（Ansible repo） |
| **CMDB 不维护** | 资产飘逸 → 故障定位难 |
| **on-call 单人** | 主备 + 跨时区 |
| **没有 postmortem** | 故障重复发生 |
| **业务高峰发布** | 严格变更窗口 |
| **日志不集中** | 节点挂日志没了 |
| **不做容量预测** | 突发容量挂 |
| **国产化没提前测** | 上线前最少 2 月联调 |

## 十四、推荐栈一图

```
监控        Prometheus + Grafana + 夜莺
日志        Loki + Promtail | ClickHouse + Vector
告警        Alertmanager + 飞书 / PagerDuty
配置管理    Ansible + GitOps
变更        GitLab CI / Argo CD
备份        restic + S3
身份        Keycloak / LDAP
堡垒        JumpServer
安全        fail2ban + auditd + Lynis + OpenSCAP
混沌        Chaos Mesh
APM         SkyWalking
追踪        OpenTelemetry + Tempo
镜像        Harbor
密钥        Vault
OS          Anolis 23 / openEuler 24.03 LTS / 麒麟 V10
```

## 十五、学习路径

```
工程化（6 月）:
  1. SLI/SLO/Error Budget 三件套
  2. Ansible 写 10 个 role
  3. Prometheus + Grafana + 告警体系
  4. restic 全套备份 + 恢复演练
  5. fail2ban / SSH 加固 / audit
  6. 日志集中化（Loki）
  7. JumpServer 上线
  8. 变更管理纪律（灰度 / 回滚）

国产化（3 月）:
  9. Anolis / openEuler / 麒麟 三选一深度
  10. 飞腾 / 鲲鹏 ARM 适配
  11. 信创合规（等保 2.0）

平台化（12 月+）:
  12. 自研巡检平台
  13. CMDB / 服务树
  14. ITSM 工单
  15. 智能告警（接 12_AIOps）
```

## 十六、参考资料

```
SRE 经典:
  - 《Site Reliability Engineering》Google
  - 《The SRE Workbook》Google
  - 《Seeking SRE》
  - 《Implementing Service Level Objectives》Alex Hidalgo

国内:
  - 阿里 SRE 体系白皮书
  - 腾讯蓝鲸运维白皮书
  - 华为 GTS 运维实践

社区:
  - SREcon （USENIX）
  - DBAplus / DevOps China
  - 极客时间 SRE 实战
  - InfoQ Cloud Native 专栏

国产 OS:
  - openeuler.org
  - openanolis.cn
  - kylinos.cn / chinauos.com

工具:
  - JumpServer 文档
  - 夜莺监控官网 n9e.github.io
  - Ansible Galaxy
```

> 📖 **核心判断**：最佳实践 = **SRE 三件套（SLO/告警/演练）+ Ansible IaC + Prometheus 监控 + restic 备份 + JumpServer 堡垒 + 安全基线 + 国产 OS 选型**。能用 Ansible 一键拉起新机入群、能写出"可操作的告警"、能跑通备份恢复演练、能用夜莺看完整指标，就是合格的运维负责人。**变更纪律 + 灰度回滚 + on-call 文化** 是从工程师到 SRE 团队的分水岭。
