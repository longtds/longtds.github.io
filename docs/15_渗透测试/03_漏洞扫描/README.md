# 漏洞扫描

## Nessus

Nessus 是商业级漏洞扫描器（免费版可用）。

```bash
# 启动服务
systemctl start nessusd

# Web 访问
# https://localhost:8834
```

## SQLMap

```bash
# SQL 注入自动化检测
sqlmap -u "http://example.com/page?id=1" --batch

# 获取数据库
sqlmap -u "http://example.com/page?id=1" --dbs

# 获取表
sqlmap -u "http://example.com/page?id=1" -D database_name --tables

# 获取数据
sqlmap -u "http://example.com/page?id=1" -D database_name -T users --dump
```

## Nuclei

```bash
# 自动漏洞检测
nuclei -u http://example.com

# 使用特定模板
nuclei -u http://example.com -t cves/

# 输出结果
nuclei -u http://example.com -o results.json
```
