# 信息收集

## 被动信息收集

```bash
# DNS 枚举
dnsrecon -d example.com
dnsenum example.com

# 子域名收集
subfinder -d example.com
assetfinder --subs-only example.com

# 搜索引擎
# site:example.com inurl:admin
# Shodan
shodan search "org:Example Corp"
```

## 主动信息收集

```bash
# Nmap 扫描
nmap -sS -sV -p- 10.0.0.1                 # 全端口扫描
nmap -sC -sV -p 80,443,3306 10.0.0.1      # 常见端口+脚本
nmap -O 10.0.0.1                           # OS 识别

# Masscan（大规模快速扫描）
masscan 10.0.0.0/24 -p80,443,22 --rate=10000

# 目录扫描
gobuster dir -u http://example.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
dirb http://example.com
```
