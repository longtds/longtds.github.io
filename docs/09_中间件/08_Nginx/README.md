# Nginx

> "互联网世界的看门人"。全球**最广泛部署的 Web 服务器、反向代理、负载均衡器、API 网关**。轻量、稳定、性能怪兽，几乎所有互联网公司流量入口都跑着 Nginx。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2002 | Igor Sysoev（俄罗斯）为 Rambler 公司启动 Nginx |
| 2004.10 | 开源发布 0.1.0 |
| 2011 | 成立 Nginx Inc. 商业公司 |
| 2015 | 全球 Web 服务器市占率超 Apache |
| 2019 | F5 Networks 以 6.7 亿美元收购 Nginx |
| 2022 | 1.22 主线、1.23 引入 HTTP/3 |
| 2024 | **1.27 HTTP/3 GA**、QUIC 稳定 |
| 2024 | 原作者 Maxim Dounin 因俄乌战争**Fork 出 freenginx** |
| 2025 | 1.28 持续演进 |

**主流版本**：1.24/1.26 LTS、1.27/1.28 主线。

## 二、Nginx 是什么

```
一个 C 语言写的多角色高性能服务器:
  ✅ Web 服务器（静态/动态）
  ✅ 反向代理
  ✅ 负载均衡器
  ✅ HTTP/HTTPS 终端 (TLS 卸载)
  ✅ 缓存服务器
  ✅ API 网关
  ✅ TCP/UDP 4 层代理（stream 模块）
  ✅ Mail 代理

核心特点:
  - Master/Worker 多进程
  - 单线程 + 异步事件驱动 (epoll/kqueue)
  - 内存极省（万级连接 ~10MB）
  - 模块化（编译时/动态加载）
  - 配置语法清晰
```

## 三、架构原理

```
┌──────────────── Master 进程 ────────────────┐
│  - 读配置 / 校验 / 重载                       │
│  - 管理 Worker 生命周期                      │
│  - 处理信号 (HUP/USR1/USR2/QUIT)             │
└──────────────────┬──────────────────────────┘
                   │ fork
   ┌───────────┬───┴───┬───────────┐
   ↓           ↓       ↓           ↓
 Worker 1   Worker 2  ...        Worker N    （CPU 核数）
   │           │                   │
   └ epoll → 处理 N 个连接 (异步)
   
   每个 Worker:
     - 独立处理客户端连接（不共享）
     - 长连接 keepalive
     - 上游连接池
     - 缓存共享内存（Master 分配）

特殊进程（可选）:
  - Cache Manager  缓存元数据管理
  - Cache Loader   启动时载入缓存
```

## 四、核心功能

```
HTTP 1.1 / 2 / 3
TLS 1.0-1.3 / OCSP / Session Cache
反向代理 + 负载均衡 (round-robin/ip_hash/least_conn/random/hash)
连接池 keepalive / keepalive_requests
缓存 proxy_cache / fastcgi_cache
压缩 gzip / br
SSL 卸载
WebSocket 代理
HTTP/2 Push (已 deprecate)
限速 limit_req / limit_conn
访问控制 allow/deny / auth_basic
Lua 扩展 (OpenResty)
模块化（核心 + 第三方）
Stream 模块（TCP/UDP 4 层代理）
gRPC 代理
HTTP/3 (QUIC) (1.25+)
```

## 五、使用场景

### ✅ 经典

| 场景 | 说明 |
|:---|:---|
| **反向代理** | 业务前置、TLS 卸载 |
| **负载均衡** | 多后端、健康检查 |
| **静态资源** | HTML/CSS/JS/图片 CDN 边缘 |
| **API 网关** | 路由 + 限流 + 鉴权（轻量） |
| **HTTPS 终端** | 统一 TLS + 证书管理 |
| **WebSocket 代理** | 长连接 |
| **gRPC 网关** | gRPC-Web 接入 |
| **图片处理服务** | + image_filter / ngx_lua |
| **HLS/DASH 视频** | 流媒体 |
| **4 层 TCP/UDP 代理** | 数据库代理、邮件、自定义协议 |

### ⚠️ 不推荐

- **复杂业务网关**（认证/限流/熔断/插件市场）→ APISIX / Kong / Higress
- **Service Mesh** → Istio / Linkerd
- **大规模 API 管理** → Apigee / Kong Enterprise

## 六、Nginx vs 其他

| 维度 | Nginx | Apache | HAProxy | Envoy | APISIX | Caddy |
|:---|:---|:---|:---|:---|:---|:---|
| HTTP | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| TCP/UDP 4 层 | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 配置易用 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 动态配置 | ⚠️（reload） | ⚠️ | ⚠️ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 自动 HTTPS | 需手工 | 需手工 | 需手工 | 需手工 | 需手工 | ⭐⭐⭐⭐⭐ |
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| K8s Ingress | 有 | 弱 | 有 | **首选** | 有 | 有 |
| 学习曲线 | 平 | 平 | 中 | 陡 | 平 | 极平 |

## 七、最佳实践

### 7.1 基础配置骨架

```nginx
# /etc/nginx/nginx.conf
user nginx;
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 10240;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志
    log_format main escape=json '{"time":"$time_iso8601","remote_addr":"$remote_addr",'
        '"request":"$request","status":$status,"body_bytes":$body_bytes_sent,'
        '"req_time":$request_time,"ups_time":"$upstream_response_time",'
        '"ua":"$http_user_agent","ref":"$http_referer"}';
    access_log /var/log/nginx/access.log main;

    # 性能
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    types_hash_max_size 4096;
    server_tokens off;       # 隐藏版本号

    # 缓冲/超时
    client_max_body_size 50m;
    client_body_buffer_size 128k;
    proxy_connect_timeout 5s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    proxy_buffer_size 8k;
    proxy_buffers 16 16k;

    # 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml image/svg+xml;
    gzip_comp_level 5;

    # 上游池
    upstream backend {
        zone backend 64k;
        keepalive 64;
        server 10.0.0.1:8080 max_fails=3 fail_timeout=10s;
        server 10.0.0.2:8080 max_fails=3 fail_timeout=10s;
    }

    include /etc/nginx/conf.d/*.conf;
}
```

### 7.2 反向代理 + HTTPS Server

```nginx
server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.example.com;

    ssl_certificate     /etc/ssl/api.crt;
    ssl_certificate_key /etc/ssl/api.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_session_cache   shared:SSL:50m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;

    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7.3 限流 + 黑白名单

```nginx
# 限速：每 IP 10 req/s，突发 20
limit_req_zone $binary_remote_addr zone=req_per_ip:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=conn_per_ip:10m;

server {
    # ...
    location /api/ {
        limit_req zone=req_per_ip burst=20 nodelay;
        limit_conn conn_per_ip 10;
        proxy_pass http://backend;
    }

    # 简单黑白名单
    location /admin/ {
        allow 10.0.0.0/8;
        allow 192.168.0.0/16;
        deny all;
        proxy_pass http://backend;
    }
}
```

### 7.4 缓存（proxy_cache）

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=mycache:100m
                 max_size=10g inactive=60m use_temp_path=off;

server {
    location /static/ {
        proxy_cache mycache;
        proxy_cache_key $scheme$host$request_uri;
        proxy_cache_valid 200 304 1h;
        proxy_cache_valid 404 1m;
        proxy_cache_lock on;
        proxy_cache_use_stale error timeout updating http_500;
        add_header X-Cache-Status $upstream_cache_status;
        proxy_pass http://backend;
    }
}
```

### 7.5 WebSocket 代理

```nginx
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;
}
```

### 7.6 gRPC 代理

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate ...;
    ssl_certificate_key ...;

    location / {
        grpc_pass grpcs://grpc_backend;
    }
}
```

### 7.7 4 层代理（stream 模块）

```nginx
# /etc/nginx/nginx.conf
stream {
    upstream mysql_backend {
        server 10.0.0.10:3306;
        server 10.0.0.11:3306;
    }
    server {
        listen 3306;
        proxy_pass mysql_backend;
        proxy_timeout 1h;
    }

    # UDP（如 DNS）
    server {
        listen 53 udp;
        proxy_pass dns_servers;
    }
}
```

### 7.8 负载均衡算法

```nginx
upstream backend {
    # 1. round-robin（默认）
    server 10.0.0.1;
    server 10.0.0.2;

    # 2. 加权
    # server 10.0.0.1 weight=5;
    # server 10.0.0.2 weight=1;

    # 3. ip_hash（同 IP 同后端）
    # ip_hash;

    # 4. least_conn（最少连接）
    # least_conn;

    # 5. hash（自定义 key 一致性哈希）
    # hash $request_uri consistent;

    # 6. random
    # random;
}
```

### 7.9 健康检查

```nginx
# 开源版只有被动健康检查（max_fails / fail_timeout）
upstream backend {
    server 10.0.0.1:8080 max_fails=3 fail_timeout=10s;
    server 10.0.0.2:8080 max_fails=3 fail_timeout=10s;
}

# 主动健康检查需要 Nginx Plus 或 OpenResty/Tengine
```

### 7.10 灰度发布

```nginx
# 按 cookie 或 header 分流
map $cookie_canary $upstream_pool {
    default      backend_stable;
    "1"          backend_canary;
}

upstream backend_stable { server 10.0.0.1:8080; }
upstream backend_canary { server 10.0.0.9:8080; }

server {
    location / {
        proxy_pass http://$upstream_pool;
    }
}
```

### 7.11 安全加固

```nginx
# 1. 隐藏版本
server_tokens off;

# 2. 限制请求方法
if ($request_method !~ ^(GET|HEAD|POST|PUT|DELETE|OPTIONS)$) { return 405; }

# 3. 禁止指定 User-Agent
if ($http_user_agent ~* (nikto|sqlmap|fimap|nessus|whatweb)) { return 403; }

# 4. 防 host 头攻击
if ($host !~* ^(api\.example\.com)$) { return 444; }

# 5. 安全 HTTP 头
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Strict-Transport-Security "max-age=63072000" always;

# 6. 隐藏敏感目录
location ~ /\.(ht|git|svn) { deny all; }

# 7. 上传大小限制
client_max_body_size 50m;
```

### 7.12 性能调优要点

```
✅ worker_processes auto + worker_cpu_affinity（绑核）
✅ worker_connections + ulimit -n 一致
✅ keepalive 上游 + keepalive_requests 高
✅ sendfile + tcp_nopush + tcp_nodelay
✅ gzip / brotli 静态压缩
✅ open_file_cache 缓存文件元数据
✅ HTTP/2 / HTTP/3
✅ TLS Session 缓存 + OCSP Stapling
✅ access_log 缓冲或关闭高频不需要的日志
✅ 日志切割（logrotate）
```

## 八、运维命令速查

```bash
# 测试配置
nginx -t

# 重载（不中断）
nginx -s reload
# 或 kill -HUP $(cat /var/run/nginx.pid)

# 平滑升级二进制
kill -USR2 $(cat /var/run/nginx.pid)
# 旧 master 退出
kill -WINCH $(cat /var/run/nginx.pid.oldbin)
kill -QUIT $(cat /var/run/nginx.pid.oldbin)

# 重新打开日志（logrotate 之后）
nginx -s reopen

# 优雅停止
nginx -s quit

# 信号
HUP   重载
USR1  重打日志
USR2  热升级
QUIT  优雅退出
TERM  强制退出

# 监控
nginx -V                            # 编译参数
curl http://127.0.0.1/nginx_status  # stub_status 模块

# 调试
strace -p <worker pid>
tail -f /var/log/nginx/error.log
```

## 九、常见坑

| 坑 | 建议 |
|:---|:---|
| **502 Bad Gateway** | 检查后端、超时、proxy_buffer |
| **504 Gateway Timeout** | proxy_read_timeout 调大 |
| **413 Request Too Large** | client_max_body_size |
| **upstream "no live"** | max_fails 触发后端全挂 |
| **配置 reload 不生效** | nginx -t 验证 + 重载 |
| **大文件下载断** | sendfile + 关闭压缩 |
| **WebSocket 30s 断** | proxy_read_timeout 设长 |
| **gzip 不工作** | gzip_types 漏了 + min_length |
| **TLS 握手慢** | session_cache + OCSP Stapling |
| **限速生效慢** | burst + nodelay |
| **客户端 IP 错** | X-Forwarded-For + set_real_ip_from |
| **日志卡 IO** | access_log buffer=64k flush=5s |
| **日志切割重启** | nginx -s reopen，别 reload |
| **HTTP/2 反代** | upstream 仍走 HTTP/1.1 keepalive |
| **大量短连接耗端口** | keepalive 上游必开 |
| **worker 占满 CPU** | 拆服务 / 调 worker_processes |

## 十、Nginx 周边生态

| 项目 | 特点 |
|:---|:---|
| **Nginx Open Source** | 官方开源版 |
| **Nginx Plus** | F5 商业版（主动健康检查、API） |
| **OpenResty** | Nginx + LuaJIT，可写 Lua 扩展 |
| **Tengine** | 阿里 Nginx Fork（动态后端、监控） |
| **Kong** | 基于 OpenResty 的 API 网关 |
| **APISIX** | 国产云原生 API 网关 |
| **freenginx** | 原作者 Fork |
| **angie** | 部分前 Nginx 团队成员 Fork |

## 十一、Nginx 作为 K8s Ingress

```yaml
# ingress-nginx Helm
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --set controller.replicaCount=3 \
  --set controller.metrics.enabled=true

# Ingress 示例
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-svc
                port:
                  number: 80
```

## 十二、监控指标

```
基础（stub_status）:
  Active connections
  Reading / Writing / Waiting

业务（日志统计）:
  QPS / 错误率 / 延迟 p50/p95/p99
  上游响应时间 upstream_response_time
  状态码分布 4xx/5xx
  TLS 握手时间

工具:
  - prometheus + nginx-prometheus-exporter
  - nginx-amplify（官方 SaaS）
  - vts-module（连接/带宽统计）
  - GoAccess（实时日志分析）
  - ELK / Loki（日志中心）
```

## 十三、HTTP/3 / QUIC（新热点）

```nginx
# 1.25+ 原生支持
server {
    listen 443 quic reuseport;
    listen 443 ssl http2;
    
    ssl_certificate ...;
    ssl_certificate_key ...;
    ssl_protocols TLSv1.3;
    
    add_header Alt-Svc 'h3=":443"; ma=86400';
}
```

**优势**：
- 0-RTT 握手
- 抗丢包（多路复用不阻塞）
- 移动网络切换更快

## 十四、学习路径

```
入门:
  1. 装一台 Nginx，跑通静态站点
  2. 反向代理 + HTTPS（Let's Encrypt）
  3. 基础日志/access_log/error_log

进阶:
  4. 负载均衡 + 健康检查
  5. 缓存 / 限流 / 黑白名单
  6. WebSocket / gRPC 代理
  7. 4 层 stream 模块

高阶:
  8. 性能调优 + 系统参数
  9. OpenResty + Lua 扩展
  10. K8s Ingress 部署
  11. HTTP/3 / QUIC
  12. 替代方案评估（APISIX/Higress）
  13. 日志分析与监控
```

## 十五、何时该换 APISIX/Kong/Higress

```
继续用 Nginx:
  - 简单反代 / 4 层代理
  - 静态资源加速
  - 老系统稳定运行
  - 团队熟悉

换 APISIX/Kong/Higress:
  - 需要插件市场（认证/限流/可观测）
  - 动态路由 + 热更新（不能 reload）
  - 多租户/多 API
  - 服务发现集成（Nacos/Consul/K8s）
  - 大量 API 治理
  - 流量切流 / 灰度
```

> 📖 **核心判断**：Nginx 是基础设施"水电煤"，**所有运维工程师必须熟练掌握**。简单反代/静态/4 层场景永远是第一选择；复杂 API 网关场景已经被 APISIX/Higress/Envoy 抢走半壁江山，但 Nginx 的存量和稳定性优势短期不会被取代。
