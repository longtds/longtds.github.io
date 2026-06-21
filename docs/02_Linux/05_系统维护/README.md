# 系统维护

## 日志管理

```bash
# journalctl 常用命令
journalctl -u <service>              # 查看服务日志
journalctl -u <service> -f           # 实时跟踪
journalctl --since "1 hour ago"      # 最近一小时
journalctl --since today --until now # 今天日志
journalctl -k                        # 内核日志

# 日志轮转配置 /etc/logrotate.conf
/var/log/syslog {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        systemctl restart rsyslog
    endscript
}
```

## 定时任务

```bash
# Crontab 格式
# * * * * * command
# │ │ │ │ │
# │ │ │ │ └─ 星期 (0-7, 0=周日)
# │ │ │ └─── 月份 (1-12)
# │ │ └───── 日期 (1-31)
# │ └─────── 小时 (0-23)
# └───────── 分钟 (0-59)

# 常用示例
0 */2 * * * /usr/local/bin/backup.sh    # 每2小时
0 3 * * 1 /usr/local/bin/weekly.sh      # 每周一凌晨3点
*/5 * * * * /usr/local/bin/check.sh     # 每5分钟
```

## 包管理

```bash
# apt (Debian/Ubuntu)
apt update && apt upgrade -y
apt install -y <package>
apt remove <package>
apt autoremove

# dnf/yum (Rocky/CentOS)
dnf update -y
dnf install -y <package>
dnf remove <package>
```
