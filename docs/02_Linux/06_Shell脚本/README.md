# Shell 脚本

## 脚本基础

```bash
#!/bin/bash
set -euo pipefail  # 安全模式：出错即停/未定义变量报错/管道错误捕获

# 变量
NAME="world"
echo "Hello, ${NAME}!"

# 函数
log() {
    local level=$1
    local msg=$2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${msg}"
}

log "INFO" "Script started"
```

## 文本处理三剑客

### grep（搜索）
```bash
grep -r "error" /var/log/    # 递归搜索
grep -v "^#" config.conf     # 排除注释行
grep -E "[0-9]{1,3}\.[0-9]{1,3}\."  # 正则
```

### sed（替换）
```bash
sed -i 's/old/new/g' file         # 全局替换
sed -n '10,20p' file              # 打印10-20行
sed -i '/pattern/d' file          # 删除匹配行
```

### awk（处理）
```bash
awk '{print $1}' file             # 打印第一列
awk -F: '{print $1}' /etc/passwd  # 指定分隔符
awk '{sum+=$1} END{print sum}'    # 求和
```

## 常用运维脚本集

### 1. 批量 SSH 执行
```bash
#!/bin/bash
for host in $(cat hosts.txt); do
    ssh ${host} "uptime"
done
```

### 2. 磁盘检查告警
```bash
#!/bin/bash
THRESHOLD=80
df -h | grep -v Filesystem | awk '{print $5 " " $1}' | while read output; do
    usage=$(echo $output | awk '{print $1}' | sed 's/%//')
    partition=$(echo $output | awk '{print $2}')
    if [ $usage -ge $THRESHOLD ]; then
        echo "WARNING: $partition is at ${usage}%"
    fi
done
```

### 3. 日志清理
```bash
#!/bin/bash
find /var/log -name "*.log" -mtime +30 -delete
find /var/log -name "*.gz" -mtime +90 -delete
```
