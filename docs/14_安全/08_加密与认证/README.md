# 加密与认证

> 密码学是网络安全的"数学地基"。**对称加密 + 非对称加密 + 哈希 + KDF + 数字签名 + PKI** 共同支撑了 HTTPS、SSH、VPN、区块链、零信任等所有现代安全协议。**用对算法 + 配对参数 + 正确使用方式**——三者缺一不可。

## 一、密码学基础

### 1.1 三大目标 (CIA)

```
Confidentiality  保密性    数据不被未授权读取  ← 加密
Integrity         完整性    数据不被未授权修改  ← 哈希 / MAC
Availability      可用性    系统可被访问         ← 不属密码学

+ 后续:
  Authenticity      真实性    确认身份         ← 签名
  Non-Repudiation   不可否认  签名后无法抵赖    ← 签名 + 时间戳
  Privacy            隐私性    匿名 / 零知识     ← 零知识证明
```

### 1.2 Kerckhoffs 原则

```
"密码系统的安全性应建立在密钥的保密上，
 而非算法的保密上"
 
→ 自研加密算法 ≈ 自杀
→ 公开标准算法 + 严格管理密钥 = 安全
→ "我们用了自研加密" 应该是负面信号
```

## 二、对称加密

### 2.1 算法对比

| 算法 | 类型 | 密钥 | 状态 | 速度 |
|:---|:---|:---:|:---:|:---:|
| **AES-128/256-GCM** | 分组 | 128/256 | ⭐⭐⭐⭐⭐ | 快（AES-NI 硬件加速）|
| **ChaCha20-Poly1305** | 流 | 256 | ⭐⭐⭐⭐⭐ | 移动端快 |
| AES-CBC + HMAC | 分组 | 128/256 | ⭐⭐⭐ | 需手动 MAC |
| 3DES | 分组 | 168 | ❌ 弃用 | 慢 |
| RC4 | 流 | 40-2048 | ❌ 不安全 | - |
| DES | 分组 | 56 | ❌ 已破 | - |
| Blowfish | 分组 | 32-448 | ⚠️ 老 | - |
| **SM4** | 分组 | 128 | ⭐⭐⭐ 国密 | - |

### 2.2 AES 详解

```
AES (Advanced Encryption Standard, 2001)
  - 分组大小: 128 bit
  - 密钥: 128 / 192 / 256 bit
  - 轮数: 10 / 12 / 14
  - 数学基础: 有限域 GF(2^8) 上的 SubBytes / ShiftRows / MixColumns / AddRoundKey

性能:
  - Intel AES-NI 硬件加速：可达 GB/s 级
  - 不上 AES-NI 的 ARM 等：考虑 ChaCha20
```

### 2.3 加密模式（关键！）

```
ECB (Electronic Codebook)
  ❌ 永远不要用
  相同明文 → 相同密文（图像加密泄漏轮廓）

CBC (Cipher Block Chaining)
  ✅ 与 HMAC 配合
  ⚠️ Padding Oracle 风险
  ⚠️ 不并行

CTR (Counter)
  ✅ 并行
  ✅ 流式
  ⚠️ Nonce 不可重复

GCM (Galois/Counter Mode)
  ⭐⭐⭐⭐⭐ 推荐
  AEAD（加密 + 认证一体）
  并行 / 高性能
  Nonce 12-byte，不重用

CCM
  AEAD，IoT 常用
  
OCB
  AEAD，专利限制（已开放）
```

### 2.4 AEAD（必学）

```
AEAD = Authenticated Encryption with Associated Data
  
  传统: 加密 + MAC（容易写错顺序，Bleichenbacher 攻击）
  AEAD: 一步搞定，难写错
  
推荐:
  ✅ AES-GCM
  ✅ ChaCha20-Poly1305
  ✅ AES-OCB

应用:
  - TLS 1.3 只允许 AEAD
  - WireGuard 用 ChaCha20-Poly1305
  - SSH ChaCha20-Poly1305
```

### 2.5 Python AEAD 实战

```python
# Python 标准方法
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
import os

# AES-GCM
key = AESGCM.generate_key(bit_length=256)
aesgcm = AESGCM(key)
nonce = os.urandom(12)                    # 12-byte 随机 nonce
plaintext = b"Sensitive data"
associated_data = b"context info"

ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
# nonce + ciphertext 一起存

# 解密
recovered = aesgcm.decrypt(nonce, ciphertext, associated_data)

# ChaCha20-Poly1305
key = ChaCha20Poly1305.generate_key()
chacha = ChaCha20Poly1305(key)
ciphertext = chacha.encrypt(nonce, plaintext, associated_data)
```

### 2.6 国密 SM4

```python
# gmssl 库
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT

key = b'0123456789abcdef'
iv = b'0123456789abcdef'
data = b'Hello SM4 World!'

cipher = CryptSM4()
cipher.set_key(key, SM4_ENCRYPT)
ct = cipher.crypt_cbc(iv, data)

cipher.set_key(key, SM4_DECRYPT)
pt = cipher.crypt_cbc(iv, ct)
```

## 三、非对称加密

### 3.1 算法对比

| 算法 | 用途 | 安全等级 | 密钥长度 | 推荐 |
|:---|:---|:---|:---:|:---:|
| **RSA** | 加密 + 签名 | 2048 → 112 bit | 2048-4096 | ⭐⭐⭐⭐ |
| **DSA** | 签名 | 弃用 | - | ❌ |
| **ECDSA** | 签名 | P-256 → 128 bit | 256-521 | ⭐⭐⭐⭐ |
| **Ed25519** ⭐⭐⭐⭐⭐ | 签名 | ~128 bit | 256 | 首选 |
| **DH** | 密钥交换 | 弱 | - | ❌ |
| **ECDH** | 密钥交换 | P-256 | 256 | ⭐⭐⭐⭐ |
| **X25519** ⭐⭐⭐⭐⭐ | 密钥交换 | ~128 bit | 256 | 首选 |
| **SM2** | 加密 + 签名 | ~128 bit | 256 国密 | ⭐⭐⭐ |
| **Kyber / Dilithium** | PQC | 后量子 | - | 渐进采用 |

### 3.2 RSA

```
原理: 大整数分解难
密钥: (n, e) 公钥, (n, d) 私钥, n = p*q
加密: c = m^e mod n
解密: m = c^d mod n
签名: s = m^d mod n
验签: m = s^e mod n

注意:
  ✅ ≥ 2048-bit
  ✅ 用 OAEP padding（不要 PKCS#1 v1.5）
  ✅ 签名用 PSS padding
  ❌ RSA 不要直接加密大数据（用混合加密）
  ❌ 同一密钥不要既加密又签名
```

### 3.3 ECC / Ed25519

```
椭圆曲线:
  - 同等安全级别下 密钥更短
  - 计算更快
  - 适合 IoT / 移动端

P-256 = 128-bit 安全（≈ RSA-3072）
P-384 = 192-bit 安全（≈ RSA-7680）
P-521 = 256-bit 安全

Ed25519:
  - 现代曲线（Curve25519）
  - 签名快、密钥短（32 byte）
  - 无 RNG 失败风险
  - 推荐: SSH/ TLS/ VPN/ Sigstore

X25519: 同曲线，用于 ECDH 密钥交换
```

### 3.4 RSA vs ECC vs Ed25519

```bash
# 生成对比
openssl genrsa -out rsa.key 4096           # ~1.6 KB
openssl ecparam -name prime256v1 -genkey -noout -out ec.key   # ~120 B
ssh-keygen -t ed25519                       # 256-bit 私钥

# 签名速度
$ openssl speed rsa4096 ecdsap256 ed25519
RSA 4096:    sign  4500 ops/s    verify 220000 ops/s
ECDSA P-256: sign 80000 ops/s    verify 25000 ops/s
Ed25519:    sign 95000 ops/s    verify  35000 ops/s
```

### 3.5 混合加密（必懂）

```
为什么:
  非对称慢，对称快
  非对称只能加密很小数据（< 密钥长）

方案: 
  1. 生成随机对称密钥 K
  2. 用对称算法加密大数据 → ciphertext
  3. 用接收方公钥加密 K → encrypted_key
  4. 发送 (encrypted_key, ciphertext)
  5. 接收方用私钥解 K，再用 K 解密 ciphertext

应用:
  TLS / PGP / S/MIME / 加密文件 / 端到端 IM
```

### 3.6 后量子密码（PQC）

```
量子计算威胁:
  Shor 算法 → 多项式时间分解大整数 → RSA / ECC / DH 全完蛋
  Grover 算法 → 对称密钥强度减半 → AES-256 仍安全

NIST PQC 标准（2024 终选）:
  - Kyber (CRYSTALS-Kyber)      密钥封装 ⭐ 推荐
  - Dilithium                   签名 ⭐ 推荐
  - SPHINCS+                   备用签名
  - Falcon                       小空间签名

迁移建议:
  2025-2028: Hybrid（经典 + PQC 双签名）
  2030+: 渐进切换
  关键: 长寿命数据（医疗、政府）现在就要 PQC
```

## 四、哈希函数

### 4.1 算法对比

| 算法 | 输出 | 状态 | 用途 |
|:---|:---:|:---:|:---|
| MD5 | 128 | ❌ 碰撞 | 文件指纹（非安全）|
| SHA-1 | 160 | ❌ 碰撞 | 已弃用 |
| **SHA-256** | 256 | ⭐⭐⭐⭐⭐ | 通用首选 |
| **SHA-384/512** | 384/512 | ⭐⭐⭐⭐ | 强需求 |
| **SHA-3** | 224-512 | ⭐⭐⭐⭐ | 备用 |
| **BLAKE3** | 256 | ⭐⭐⭐⭐⭐ | 高性能 |
| **SM3** | 256 | ⭐⭐⭐ 国密 | 中国合规 |

### 4.2 用法

```python
import hashlib

# 文件指纹
def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

# 内存数据
hashlib.sha256(b'data').hexdigest()
hashlib.blake2b(b'data', digest_size=32).hexdigest()
```

### 4.3 HMAC（消息认证）

```python
import hmac
import hashlib

# HMAC = 哈希 + 密钥 → 防伪造
key = b'shared_secret'
data = b'message'

mac = hmac.new(key, data, hashlib.sha256).hexdigest()

# 验证（防时序攻击：用 compare_digest）
hmac.compare_digest(mac, received_mac)   # ✅ 常量时间比较
# 不要用 == 比较 MAC！
```

## 五、密码哈希（KDF）

### 5.1 为什么不能用 SHA 直接哈密码

```
SHA-256("password") 太快了:
  GPU 可以每秒计算 10^9 次
  10^9 × 86400 ≈ 10^14 次/天
  → 弱密码秒破
  
密码哈希要"故意慢" + "内存硬"：
  让攻击者花时间 × 内存 = 钱
```

### 5.2 推荐算法

| 算法 | 推荐参数 | 状态 |
|:---|:---|:---:|
| **Argon2id** ⭐⭐⭐⭐⭐ | t=2, m=64MB, p=1 | 2025 首选 |
| **scrypt** | N=2^17, r=8, p=1 | 强 |
| **bcrypt** | cost=12 | 老牌可靠 |
| **PBKDF2-HMAC-SHA256** | iterations=600,000 | 仅合规要求 |
| MD5 / SHA 直接哈希 | ❌ | 永远不要 |

### 5.3 Argon2id 实战

```python
# pip install argon2-cffi
from argon2 import PasswordHasher

ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=4)

# 注册时
hash_str = ph.hash("user_password")
# 存数据库（包含算法参数 + salt + hash）
# $argon2id$v=19$m=65536,t=2,p=4$<salt>$<hash>

# 登录时
try:
    ph.verify(hash_str, "user_password")
    # 检查是否需要 rehash（参数升级）
    if ph.check_needs_rehash(hash_str):
        new_hash = ph.hash("user_password")
        # update db
except VerifyMismatchError:
    pass    # 密码错误
```

### 5.4 bcrypt（仍可用）

```python
# pip install bcrypt
import bcrypt

# 注册
hashed = bcrypt.hashpw(b"user_password", bcrypt.gensalt(rounds=12))

# 登录
bcrypt.checkpw(b"user_password", hashed)
```

### 5.5 密码哈希架构

```
✅ 永远存 hash，不存明文
✅ 每用户独立 salt（随机）
✅ 算法参数 + salt + hash 一起存（标准格式）
✅ 不要预计算（Rainbow table）
✅ 周期升级参数（硬件升级时）
✅ 不要 hash 多次 SHA（不增加安全）
✅ 不要"加点料"（自创算法）

数据泄漏后:
  ✅ Argon2id/bcrypt: 强密码可能撑几天
  ❌ MD5/SHA1: 弱密码秒破
```

## 六、数字签名

### 6.1 签名 vs MAC

```
HMAC（对称）:
  - 双方共享 key
  - 任一方都能生成签名
  - 不能仲裁（不知谁签）

数字签名（非对称）:
  - 签名方用私钥签
  - 验证方用公钥验
  - 不可抵赖
  - 可证明给第三方

应用:
  HMAC: API 签名、JWT
  签名: 软件包、证书、文档、区块链
```

### 6.2 签名算法

```
RSA-PSS              推荐 RSA 签名
ECDSA P-256          常见 ECC 签名
Ed25519              ⭐ 现代首选
SM2                  国密
EdDSA (Ed25519 / Ed448)  推荐
DSA                  弃用
```

### 6.3 Python 签名实战

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

# 生成
private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# 签名
signature = private_key.sign(b"message")

# 验证
try:
    public_key.verify(signature, b"message")
    print("Valid")
except:
    print("Invalid")

# 导出
pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
```

## 七、JWT (JSON Web Token)

### 7.1 结构

```
xxxxx.yyyyy.zzzzz
   |     |     |
 Header  Payload  Signature

Header (Base64URL):
  { "alg": "HS256", "typ": "JWT" }

Payload (Base64URL):
  { "sub": "user123", "exp": 1716998400, "iat": 1716994800, ... }

Signature:
  HMAC-SHA256(base64(header) + "." + base64(payload), secret)
  或非对称: RS256/ES256/EdDSA
```

### 7.2 算法选择

```
HS256 (HMAC)
  ✅ 简单
  ❌ 双方共享密钥 → 不适合分布式
  
RS256 (RSA)
  ✅ 私钥签 / 公钥验
  ✅ 分布式（公钥可分发）
  ⚠️ 历史 alg=none 漏洞、密钥混淆漏洞
  
ES256 (ECDSA)
  ✅ 短签名
  ✅ 同 RSA 优势

EdDSA (Ed25519)
  ⭐ 推荐 2025
  ✅ 短 / 快 / 安全
```

### 7.3 常见漏洞

```
1. alg=none
   攻击者改 header alg=none → 不需签名
   防御: 服务端严格校验 alg
   
2. 算法混淆（RS256 → HS256）
   攻击者把 RSA 公钥当作 HMAC secret 伪造签名
   防御: 严格指定 alg
   
3. weak secret
   爆破 HMAC secret
   防御: 强随机 ≥ 256-bit
   
4. JWT 过期不验
   exp 不校验 → 永久 token
   
5. 信息泄漏
   Payload 不是加密的，敏感数据不要放（base64≠加密）
```

### 7.4 推荐配置

```python
# PyJWT
import jwt
import datetime

# 生成
payload = {
    "sub": "user123",
    "iat": datetime.datetime.utcnow(),
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    "iss": "company.com",
    "aud": "api"
}

# Ed25519
private_pem = open('private.pem', 'rb').read()
token = jwt.encode(payload, private_pem, algorithm='EdDSA')

# 验证
public_pem = open('public.pem', 'rb').read()
try:
    payload = jwt.decode(
        token, public_pem,
        algorithms=['EdDSA'],         # 严格指定
        issuer='company.com',
        audience='api'
    )
except jwt.ExpiredSignatureError: ...
except jwt.InvalidSignatureError: ...
```

### 7.5 JWT vs Session

```
JWT:
  ✅ 无状态（服务端无需存储）
  ✅ 跨服务（微服务）
  ❌ 不能即时吊销（要 blacklist 或短过期）
  ❌ 体积大（每请求都带）
  ❌ 客户端易泄漏

Session:
  ✅ 即时吊销
  ✅ 体积小（cookie 一个 ID）
  ❌ 需要存储（DB / Redis）
  ❌ 跨服务麻烦

混合:
  - 短期 JWT（access token, 15 min）
  - 长期 Refresh Token（在服务端存）
  - 注销时 revoke refresh token
```

## 八、OAuth 2.0 / OIDC

详见 `08_认证与SSO`，此处只列密码学相关：

```
OAuth 2.0 流程依赖:
  - HTTPS (TLS)
  - State 参数（CSRF 防护）
  - PKCE (Code Verifier hash)
  - JWT token

OIDC 增加:
  - ID Token (JWT 签名)
  - 必校验 iss / aud / exp / signature
  - Userinfo endpoint
```

## 九、PKI 实战

### 9.1 X.509 证书结构

```
Certificate:
  Data:
    Version: 3
    Serial Number: 12345
    Signature Algorithm: sha256WithRSAEncryption
    Issuer: CN=Let's Encrypt R3, O=Let's Encrypt
    Validity:
      Not Before: Jun 1 00:00:00 2025
      Not After:  Aug 30 00:00:00 2025
    Subject: CN=example.com
    Subject Public Key Info:
      Public Key Algorithm: ECDSA P-256
      Public Key: 04:abc...
    X509v3 extensions:
      Subject Alternative Name: DNS:example.com, DNS:www.example.com
      Key Usage: Digital Signature, Key Encipherment
      Extended Key Usage: TLS Web Server Authentication
      ...
  Signature Algorithm: sha256WithRSAEncryption
  Signature: 0a:bc:...
```

### 9.2 证书操作

```bash
# 看证书
openssl x509 -in cert.pem -text -noout
openssl s_client -connect example.com:443 -showcerts < /dev/null 2>&1 | openssl x509 -text

# 创建 Root CA
openssl genrsa -aes256 -out ca.key 4096
openssl req -x509 -new -key ca.key -days 7300 -sha256 -out ca.crt \
  -subj "/C=CN/ST=Beijing/O=Company/CN=Root CA"

# Intermediate CA
openssl genrsa -out intermediate.key 4096
openssl req -new -key intermediate.key -out intermediate.csr \
  -subj "/C=CN/ST=Beijing/O=Company/CN=Intermediate CA"
openssl x509 -req -in intermediate.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -days 3650 -sha256 -out intermediate.crt \
  -extensions v3_intermediate_ca -extfile openssl.cnf

# Server 证书（带 SAN）
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
  -subj "/C=CN/ST=Beijing/O=Company/CN=api.company.com" \
  -addext "subjectAltName = DNS:api.company.com, DNS:*.api.company.com"

openssl x509 -req -in server.csr -CA intermediate.crt -CAkey intermediate.key \
  -CAcreateserial -days 365 -sha256 -out server.crt \
  -extfile <(echo "subjectAltName=DNS:api.company.com,DNS:*.api.company.com")

# 验证链
openssl verify -CAfile ca.crt -untrusted intermediate.crt server.crt

# 转格式
openssl x509 -in cert.pem -out cert.der -outform DER
openssl pkcs12 -export -in cert.pem -inkey key.pem -out cert.pfx
```

### 9.3 ACME (Let's Encrypt)

```bash
# certbot（Nginx 自动）
certbot --nginx -d example.com -d www.example.com

# 通配符（DNS 验证）
certbot certonly --manual --preferred-challenges dns -d '*.example.com'

# acme.sh（轻量）
acme.sh --issue --dns dns_ali -d '*.example.com'
acme.sh --install-cert -d '*.example.com' \
  --key-file /etc/nginx/ssl/key.pem \
  --fullchain-file /etc/nginx/ssl/fullchain.pem \
  --reloadcmd "nginx -s reload"

# 自动续期
certbot renew --dry-run    # 测试
# /etc/cron.d/certbot
0 0,12 * * * root certbot renew -q
```

### 9.4 Certificate Transparency

```
CT Log: 公开的证书签发日志
  → 所有公网证书必须上链
  → 攻击者偷偷给你的域名签发证书 → 你能发现

监控:
  - crt.sh
  - Cert Spotter (sslmate)
  - 阿里云 / 腾讯云 CT 监控
  
告警: 发现陌生证书 → 立即吊销 + 调查
```

## 十、密钥派生与 Key Wrapping

### 10.1 KDF（密钥派生函数）

```
作用: 从一个种子派生多个独立密钥

HKDF (HMAC-based KDF) ⭐ 推荐
  HKDF-Extract → HKDF-Expand
  应用: TLS 1.3 / Signal / Noise

PBKDF2 / Argon2 / scrypt
  从密码派生密钥（慢哈希）
```

```python
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

# 从主密钥派生多个用途密钥
hkdf = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=b"unique-salt",
    info=b"encryption-key",      # 不同用途 info 不同
)
key1 = hkdf.derive(master_key)

hkdf2 = HKDF(algorithm=hashes.SHA256(), length=32, salt=b"unique-salt", info=b"mac-key")
key2 = hkdf2.derive(master_key)
```

### 10.2 Key Wrapping

```
用主密钥（KEK, Key Encryption Key）加密数据密钥（DEK, Data Encryption Key）
  
应用:
  - 信封加密（AWS KMS、阿里 KMS）
  - 每条数据独立 DEK
  - DEK 用 KEK 包裹后存储
  - 轮换 KEK 只重新包裹（不重新加密数据）

算法:
  - AES-KW (RFC 3394)
  - AES-GCM-KW
```

## 十一、随机数（关键）

```
✅ 必须用密码学安全随机数源:
  Linux:  /dev/urandom (不是 /dev/random)
  Python: secrets 模块 (不是 random)
  Node:   crypto.randomBytes (不是 Math.random)
  Go:     crypto/rand (不是 math/rand)
  Java:   SecureRandom

❌ 永远不要用:
  - 时间戳作种子
  - PID
  - 自己写"伪随机"
  - 弱 RNG 生成密钥 / token / IV / nonce / salt

测试 RNG:
  - rngtest
  - dieharder
  - NIST STS
```

```python
import secrets
import os

# 生成 token
secrets.token_hex(16)              # 32 字符 hex
secrets.token_urlsafe(32)          # URL-safe base64
secrets.token_bytes(32)            # 原始字节

# 生成 key
os.urandom(32)                     # 256-bit key

# 范围
secrets.randbelow(100)             # 0-99
secrets.choice(['a', 'b', 'c'])
```

## 十二、常见错误与陷阱

| 错误 | 后果 | 正确 |
|:---|:---|:---|
| 用 MD5/SHA1 哈密码 | 弱密码秒破 | Argon2id |
| 用 ECB 模式 | 明文模式泄漏 | GCM |
| 重用 IV/Nonce | 全完蛋 | 每次随机 |
| 自研算法 | 自杀 | 标准库 |
| `==` 比较 MAC | 时序攻击 | `compare_digest` |
| 密码明文存 | 数据库泄漏 = 全裸 | 永远哈希 |
| RSA 直接加密大数据 | 不安全 / 慢 | 混合加密 |
| 不验证证书 | MITM | 严格校验 |
| Hardcoded key | Git 一搜全有 | Vault |
| 不轮换密钥 | 长期暴露风险 | 定期轮换 |
| 同一密钥多用途 | 跨协议攻击 | 一密钥一用途 |
| JWT alg=none | 任意伪造 | 严格指定算法 |
| Math.random 生成 token | 可预测 | crypto.randomBytes |
| TLS 1.0/1.1 | 已弃用 | TLS 1.2+ |
| 自签 CA 但客户端无信任 | 一直 warning | 分发 Root CA |

## 十三、安全编码 Checklist

```
对称加密:
☐ 用 AES-GCM 或 ChaCha20-Poly1305 (AEAD)
☐ 12-byte 随机 nonce，每次不同
☐ 密钥 ≥ 256-bit，crypto.randomBytes 生成
☐ 不用 ECB

非对称:
☐ RSA ≥ 2048, ECDSA P-256+, Ed25519
☐ 用 OAEP/PSS padding
☐ 同密钥不同时签名+加密
☐ 私钥安全存储（HSM / Vault）

哈希:
☐ SHA-256/384/512 或 BLAKE3
☐ 不用 MD5/SHA1
☐ 密码用 Argon2id（不要 SHA）
☐ 文件指纹用 SHA-256

签名:
☐ Ed25519 / ECDSA / RSA-PSS
☐ 严格校验 alg
☐ 防 timing attack（compare_digest）

PKI:
☐ TLS 1.2+, 强 cipher suite
☐ HSTS / OCSP Stapling
☐ 证书 SAN
☐ ACME 自动续期
☐ CT 监控

KDF:
☐ HKDF 派生多用途密钥
☐ Argon2id/bcrypt 哈密码

随机:
☐ 用 secrets / crypto.randomBytes
☐ 不用 random / Math.random

JWT:
☐ 严格指定 alg
☐ exp / iss / aud 全校验
☐ Refresh + Revoke
☐ 敏感数据不放 payload
```

## 十四、推荐工具与库

```
通用:
  - cryptography (Python)
  - libsodium (跨语言)
  - tink (Google, 多语言)
  - OpenSSL / BoringSSL / LibreSSL
  - NaCl (Networking and Cryptography library)

PKI:
  - certbot / acme.sh
  - cfssl (CloudFlare)
  - smallstep step-ca
  - HashiCorp Vault PKI

JWT:
  - jjwt / PyJWT / jose-jwt

国密:
  - GMSSL / gmssl-python
  - 国密 OpenSSL fork
  - tongsuo (铜锁)

工具:
  - testssl.sh / sslscan / nmap ssl-enum
  - hashcat (爆破)
  - John the Ripper
  - Cryptii / CyberChef (在线工具)
```

## 十五、参考资料

```
书:
  - 《Cryptography Engineering》(Schneier, Ferguson)
  - 《Serious Cryptography》(Aumasson) ⭐ 现代化
  - 《Applied Cryptography》(Schneier) 经典
  - 《Real-World Cryptography》(Wong)

标准:
  - NIST SP 800-57 Key Management
  - FIPS 140-2/3
  - RFC 5246 / 8446 (TLS)
  - RFC 7519 (JWT)
  - RFC 5869 (HKDF)
  - GM/T 系列（国密）

在线:
  - Cryptography I (Coursera, Boneh)
  - Crypto 101 (免费 PDF)
  - The Cryptopals Crypto Challenges
  - latacora.singles/cryptography-right-answers
```

> 📖 **核心判断**：密码学的灵魂不是算法本身，而是**用对算法 + 用对参数 + 用对方式**。**AEAD（AES-GCM/ChaCha20）+ Ed25519 + Argon2id + HKDF + 强 RNG + 标准库** 是 2025 默认选择。**自创算法 = 自杀**。**算法过时 = 系统过时**——所以**保留升级路径**（密码哈希参数可升级、TLS 协议升级、PQC 渐进迁移）比某次完美选型更重要。
