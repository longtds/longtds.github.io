# Linux 安全

## 安全基线

```bash
# 系统安全基线检查
1. 最小化安装（不必要的包不装）
2. 设置 SELinux/AppArmor
3. 配置防火墙（iptables/nftables）
4. 禁用 root 远程登录
5. 配置 SSH 密钥认证
6. 设置密码策略（复杂度/过期时间）
```

## SSH 加固

```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```

## 审计

```bash
# auditd 规则
auditctl -w /etc/passwd -p wa -k passwd_changes
auditctl -w /etc/shadow -p wa -k shadow_changes
auditctl -a exit,always -S execve -k shell_commands

# 查看审计日志
ausearch -k passwd_changes
aureport -k
```
