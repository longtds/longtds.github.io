# 防御加固

## Linux 安全加固

```bash
# 系统加固检查项
1. 最小化服务（关闭不需要的服务）
2. 防火墙配置（只开放必要端口）
3. SSH 密钥认证 + 禁用密码登录
4. Fail2ban 防暴力破解
5. 日志远程存储（避免被删）
6. 文件完整性检查（AIDE）
```

## HIDS

```bash
# Wazuh（开源 HIDS）
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | apt-key add -
apt install wazuh-agent
```

## 蜜罐

```bash
# 部署 SSH 蜜罐
docker run -d -p 22:22 cowrie/cowrie:latest
```
