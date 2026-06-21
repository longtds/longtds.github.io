# 系统管理

## 发行版选型

| 发行版 | 包管理器 | 特点 | 场景 |
|:---|:---|:---|:---|
| Ubuntu LTS | apt | 社区活跃，文档丰富 | 通用/开发/AI |
| Rocky Linux | yum/dnf | RHEL 兼容，稳定 | 生产/合规 |
| Debian | apt | 极其稳定 | 通用 |
| CentOS Stream | dnf | 滚动更新 | 开发 |

## 系统初始化 checklist

```bash
# 更新系统
apt update && apt upgrade -y

# 设置时区
timedatectl set-timezone Asia/Shanghai

# 设置主机名
hostnamectl set-hostname <hostname>

# 创建管理用户
useradd -m -s /bin/bash admin
usermod -aG sudo admin

# SSH 加固
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# 关闭 swap（K8s 要求）
swapoff -a
sed -i '/swap/d' /etc/fstab

# 开启 IP 转发
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.d/99-k8s.conf
sysctl -p /etc/sysctl.d/99-k8s.conf
```
