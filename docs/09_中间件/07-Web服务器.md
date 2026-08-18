# Web 服务器安装与配置

> 生产环境选哪个 Web 服务器？Nginx、Apache、Caddy 各有场景。本文覆盖安装、虚拟主机、HTTPS、反向代理、负载均衡、性能调优全流程。

---

## 一、Web 服务器选型

### 1.1 主流 Web 服务器对比

| 维度 | Nginx | Apache (httpd) | Caddy | HAProxy | Traefik |
|:---|:---|:---|:---|:---|:---|
| 定位 | Web/反代/负载均衡 | Web 服务器 | Web/反代 | 负载均衡/反代 | 云原生反代 |
| 并发模型 | 事件驱动 (epoll) | 进程/线程 (prefork/worker) | 事件驱动 | 事件驱动 | 事件驱动 |
| 静态文件 | ⭐ 极快 | 快 | 快 | N/A | N/A |
| 反向代理 | ⭐ 原生强大 | 需 mod_proxy | 原生 | ⭐ 专业级 | 原生 |
| HTTPS 自动 | 需手动 | 需手动 | ⭐ 自动 Let's Encrypt | 需手动 | ⭐ 自动 |
| 动态内容 | FastCGI/反代 | 原生 PHP (mod_php) | FastCGI/反代 | N/A | 反代 |
| 配置语法 | 自有语法 | XML 风格 | Caddyfile (简洁) | 自有语法 | YAML/动态 |
| 热重载 | ✅ `nginx -s reload` | ✅ `graceful` | ✅ `caddy reload` | ✅ | ✅ |
| 内存占用 | 低 | 中 | 低 | 低 | 中 |
| K8s/云原生 | 常用 Ingress | 少用 | 少用 | 常用入口 | ⭐ Ingress 标选 |
| 生态/模块 | 丰富 | ⭐ 极丰富 | 增长中 | 负载均衡最强 | 云原生最强 |
| 学习曲线 | 中 | 中 | 低 | 高 | 中 |

### 1.2 选型建议

| 场景 | 推荐 | 原因 |
|:---|:---|:---|
| 静态站点 + 反向代理 | **Nginx** | 性能强，配置成熟，生态大 |
| 传统 PHP 应用 (WordPress) | **Apache** | mod_php 原生支持，.htaccess 兼容 |
| 个人小站 + 快速 HTTPS | **Caddy** | 自动 TLS，配置极简 |
| 纯四层/七层负载均衡 | **HAProxy** | 专业负载均衡，健康检查强 |
| K8s Ingress / 微服务 | **Traefik** | 自动服务发现，动态配置 |
| 高并发 API 网关 | **Nginx** | 稳定 + 社区方案多 |
| 混合架构 (前端静态 + 后端 API) | **Nginx** | 静态直出 + API 反代 |

### 1.3 架构模式

```
模式一: Nginx 直出静态 + 反代动态
┌──────┐     ┌───────┐     ┌──────────┐
│ 用户  │────►│ Nginx │────►│ FastCGI  │ (PHP-FPM / Python / Go)
└──────┘     └───┬───┘     └──────────┘
                 │
                 ├── 静态文件直接返回 (/var/www/html/)
                 └── .php 交给 PHP-FPM

模式二: Nginx 反代后端应用
┌──────┐     ┌───────┐     ┌──────────┐
│ 用户  │────►│ Nginx │────►│ App:8080  │ (Node.js / Go / Java)
└──────┘     └───┬───┘     └──────────┘
                 │          ┌──────────┐
                 └─────────►│ App:8081  │ (负载均衡)
                            └──────────┘

模式三: HAProxy → Nginx → App
┌──────┐     ┌────────┐     ┌───────┐     ┌────────┐
│ 用户  │────►│HAProxy │────►│ Nginx │────►│ App    │
└──────┘     └────────┘     └───────┘     └────────┘
              (TLS卸载)     (静态/路由)    (动态)
```

---

## 二、Nginx

### 2.1 安装

```bash
# === 方式一: 发行版官方源 (稳定, 版本可能偏旧) ===
# Rocky / RHEL / CentOS
dnf install -y nginx

# Ubuntu / Debian
apt install -y nginx

# === 方式二: Nginx 官方源 (推荐, 版本新) ===
# Rocky / RHEL 9
cat > /etc/yum.repos.d/nginx.repo << 'EOF'
[nginx-stable]
name=nginx stable repo
baseurl=http://nginx.org/packages/centos/9/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://nginx.org/keys/nginx_signing.key
module_hotfixes=true
EOF
dnf install -y nginx

# Ubuntu 22.04
curl -fsSL https://nginx.org/keys/nginx_signing.key | gpg --dearmor -o /usr/share/keyrings/nginx-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/nginx-keyring.gpg] http://nginx.org/packages/ubuntu jammy nginx" \
    > /etc/apt/sources.list.d/nginx.list
apt update && apt install -y nginx

# === 方式三: 编译安装 (需要特定模块时) ===
dnf install -y gcc make pcre-devel zlib-devel openssl-devel
wget http://nginx.org/download/nginx-1.27.0.tar.gz
tar xzf nginx-1.27.0.tar.gz
cd nginx-1.27.0
./configure \
    --prefix=/etc/nginx \
    --sbin-path=/usr/sbin/nginx \
    --conf-path=/etc/nginx/nginx.conf \
    --with-http_ssl_module \
    --with-http_v2_module \
    --with-http_realip_module \
    --with-http_stub_status_module \
    --with-stream \
    --with-threads
make -j$(nproc)
make install

# === 启动 ===
systemctl enable --now nginx

# 验证
nginx -v
curl -I http://localhost
```

### 2.2 配置文件结构

```
/etc/nginx/
├── nginx.conf                 ← 主配置 (全局)
├── conf.d/                    ← 用户配置 (include 进 http 块)
│   ├── default.conf           ← 默认站点
│   ├── site-a.conf            ← 站点 A
│   └── site-b.conf            ← 站点 B
├── mime.types                 ← MIME 类型映射
├── fastcgi_params             ← FastCGI 参数
├── ssl/                       ← SSL 证书
│   ├── server.crt
│   └── server.key
└── snippets/                  ← 可复用片段
    ├── ssl-params.conf
    └── proxy-params.conf
```

```bash
# 主配置: /etc/nginx/nginx.conf

user  nginx;                           # 运行用户
worker_processes  auto;                # worker 进程数 (auto = CPU 核数)
worker_rlimit_nofile 65535;            # 每个 worker 最大文件描述符

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

# 事件模块
events {
    worker_connections  10240;         # 每个 worker 最大连接数
    use epoll;                         # 事件模型 (Linux 用 epoll)
    multi_accept on;                   # 一次接受所有连接
}

# HTTP 模块
http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # 日志格式
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for" '
                      'rt=$request_time uct=$upstream_connect_time '
                      'urt=$upstream_response_time';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;               # 零拷贝发送文件
    tcp_nopush      on;               # TCP_CORK (合并小包)
    tcp_nodelay     on;               # TCP_NODELAY (禁用 Nagle)
    keepalive_timeout  65;             # 长连接超时
    keepalive_requests 1000;           # 长连接最大请求数
    server_tokens off;                 # 隐藏 Nginx 版本号

    # Gzip 压缩
    gzip  on;
    gzip_min_length  1k;
    gzip_comp_level  6;
    gzip_types  text/plain text/css application/json application/javascript
                text/xml application/xml application/xml+rss text/javascript;
    gzip_vary on;

    # 客户端限制
    client_max_body_size  100m;        # 最大上传 100MB
    client_body_buffer_size 128k;
    client_header_timeout  30;
    client_body_timeout    30;
    send_timeout           30;

    # 包含用户配置
    include /etc/nginx/conf.d/*.conf;
}
```

### 2.3 虚拟主机

```bash
# /etc/nginx/conf.d/site-a.conf — 静态站点

server {
    listen 80;
    listen [::]:80;
    server_name site-a.example.com www.site-a.example.com;

    root /var/www/site-a;
    index index.html index.htm;

    access_log /var/log/nginx/site-a-access.log main;
    error_log  /var/log/nginx/site-a-error.log warn;

    location / {
        try_files $uri $uri/ =404;
    }

    # 自定义错误页
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
}

# /etc/nginx/conf.d/site-b.conf — 另一个站点 (不同端口/域名)

server {
    listen 80;
    server_name site-b.example.com;

    root /var/www/site-b;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 2.4 HTTPS / SSL

```bash
# === 获取证书 ===

# 方式一: Let's Encrypt (免费, 自动续期)
dnf install -y certbot python3-certbot-nginx
certbot --nginx -d site-a.example.com -d www.site-a.example.com
# certbot 自动修改 nginx 配置, 添加 HTTPS

# 方式二: 自签名 (测试用)
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/server.key \
    -out /etc/nginx/ssl/server.crt \
    -subj "/C=CN/ST=Zhejiang/L=Hangzhou/O=MyOrg/CN=site-a.example.com"
chmod 600 /etc/nginx/ssl/server.key

# === HTTPS 配置 ===
# /etc/nginx/conf.d/site-a-ssl.conf

server {
    listen 80;
    server_name site-a.example.com;
    # HTTP → HTTPS 重定向
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;                           # 启用 HTTP/2
    server_name site-a.example.com;

    ssl_certificate     /etc/letsencrypt/live/site-a.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/site-a.example.com/privkey.pem;

    # SSL 优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # HSTS (强制浏览器后续都走 HTTPS)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    root /var/www/site-a;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}

# === 证书自动续期 ===
# certbot 已自动添加 cron/systemd timer
# 测试续期:
certbot renew --dry-run
# 续期后重载 nginx:
# /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
#!/bin/bash
systemctl reload nginx
```

### 2.5 反向代理

```bash
# /etc/nginx/conf.d/api-proxy.conf

server {
    listen 80;
    server_name api.example.com;

    # 反代到后端应用
    location / {
        proxy_pass http://127.0.0.1:8080;

        # 传递客户端真实信息
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 代理超时
        proxy_connect_timeout 30s;
        proxy_send_timeout    60s;
        proxy_read_timeout    60s;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 不同路径代理到不同后端
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/v2/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态文件由 Nginx 直接处理 (不走后端)
    location /static/ {
        alias /var/www/api/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 文件上传
    location /upload {
        proxy_pass http://127.0.0.1:8080;
        client_max_body_size 500m;
        proxy_request_buffering off;     # 大文件不缓冲, 流式转发
    }
}
```

### 2.6 负载均衡

```bash
# /etc/nginx/conf.d/lb.conf

# === 后端池定义 ===
upstream backend_pool {
    # 负载均衡策略 (默认 round-robin 轮询):
    # least_conn;        ← 最少连接数
    # ip_hash;           ← 按 IP hash (会话保持)
    # random;            ← 随机

    server 192.168.1.10:8080 weight=3;    # 权重 3
    server 192.168.1.11:8080 weight=2;    # 权重 2
    server 192.168.1.12:8080 weight=1;    # 权重 1

    # 健康检查 (被动, 请求失败时自动剔除)
    max_fails=3 fail_timeout=30s;

    # 备用服务器 (主服务器全挂时启用)
    # server 192.168.1.99:8080 backup;

    # 宕机后多久重试
    # slow_start=30s;

    # 长连接到后端 (减少连接建立开销)
    keepalive 32;
    keepalive_requests 1000;
    keepalive_timeout 60s;
}

server {
    listen 80;
    server_name lb.example.com;

    location / {
        proxy_pass http://backend_pool;

        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 后端长连接
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        # 连接超时
        proxy_connect_timeout 5s;
        proxy_send_timeout    30s;
        proxy_read_timeout    30s;

        # 下一台重试 (容错)
        proxy_next_upstream error timeout http_502 http_503 http_504;
        proxy_next_upstream_tries 3;
    }

    # 健康检查端点 (主动检查需 nginx-plus 或第三方模块)
    location /health {
        access_log off;
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
```

### 2.7 PHP-FPM 配置

```bash
# 安装 PHP-FPM
dnf install -y php-fpm php-mysqlnd php-gd php-mbstring php-xml php-json

systemctl enable --now php-fpm

# Nginx + PHP-FPM 配置
# /etc/nginx/conf.d/php-site.conf

server {
    listen 80;
    server_name php.example.com;
    root /var/www/php-site;
    index index.php index.html;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    # PHP 文件交给 PHP-FPM
    location ~ \.php$ {
        fastcgi_pass   unix:/run/php-fpm/www.sock;   # 或 127.0.0.1:9000
        fastcgi_index  index.php;
        fastcgi_param  SCRIPT_FILENAME  $document_root$fastcgi_script_name;
        include        fastcgi_params;

        # 超时
        fastcgi_read_timeout 60s;
        fastcgi_buffers 16 16k;
        fastcgi_buffer_size 32k;
    }

    # 禁止访问隐藏文件
    location ~ /\.(?!well-known).* {
        deny all;
    }
}
```

### 2.8 性能调优

```bash
# /etc/nginx/nginx.conf 性能相关参数

worker_processes auto;               # 自动匹配 CPU 核数
worker_rlimit_nofile 65535;          # 文件描述符上限

events {
    worker_connections 10240;         # 每 worker 连接数
    use epoll;                        # Linux 事件模型
    multi_accept on;                  # 一次接受所有新连接
}

http {
    # 零拷贝
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    # 长连接
    keepalive_timeout 65;
    keepalive_requests 1000;

    # 缓冲区
    client_body_buffer_size 16k;
    client_header_buffer_size 4k;
    large_client_header_buffers 4 16k;

    # Gzip
    gzip on;
    gzip_min_length 1k;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # 静态文件缓存
    open_file_cache max=10000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;

    # 上游长连接
    upstream backend_pool {
        server 127.0.0.1:8080;
        keepalive 32;
    }
}

# === 系统层面调优 (sysctl) ===
cat > /etc/sysctl.d/99-nginx.conf << 'EOF'
# 文件描述符
fs.file-max = 1000000

# TCP 连接优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# TCP 快速回收
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15

# keepalive
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3

# 端口范围
net.ipv4.ip_local_port_range = 10000 65535
EOF
sysctl -p /etc/sysctl.d/99-nginx.conf

# 用户级文件描述符 (systemd)
mkdir -p /etc/systemd/system/nginx.service.d
cat > /etc/systemd/system/nginx.service.d/limits.conf << 'EOF'
[Service]
LimitNOFILE=65535
EOF
systemctl daemon-reload
systemctl restart nginx
```

### 2.9 日志与监控

```bash
# 访问日志分析
# Top 10 IP
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head 10

# Top 10 URL
awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head 10

# HTTP 状态码统计
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn

# 慢请求 (>1秒)
awk '($NF > 1){print}' /var/log/nginx/access.log

# 错误日志
tail -f /var/log/nginx/error.log

# === 状态页 (stub_status) ===
# /etc/nginx/conf.d/status.conf
server {
    listen 127.0.0.1:8080;
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
# curl http://127.0.0.1:8080/nginx_status
# Active connections: 15
# server accepts handled requests
# 8456 8456 32891
# Reading: 0 Writing: 3 Waiting: 12
```

---

## 三、Apache (httpd)

### 3.1 安装

```bash
# Rocky / RHEL 9
dnf install -y httpd httpd-tools mod_ssl

# Ubuntu (Apache 名为 apache2)
apt install -y apache2 apache2-utils ssl-cert

# 启动
systemctl enable --now httpd     # Ubuntu: apache2

# 验证
httpd -v                          # Ubuntu: apache2 -v
curl -I http://localhost
```

### 3.2 配置文件结构

```
Rocky / RHEL:
/etc/httpd/
├── conf/
│   └── httpd.conf                ← 主配置
├── conf.d/                       ← 用户配置
│   ├── ssl.conf                  ← HTTPS 配置
│   └── vhost.conf                ← 虚拟主机
├── conf.modules.d/               ← 模块配置
│   ├── 00-base.conf
│   └── 10-php.conf
└── modules/                      ← 模块文件 (.so)

Ubuntu / Debian:
/etc/apache2/
├── apache2.conf                  ← 主配置
├── ports.conf                    ← 端口配置
├── sites-available/              ← 可用站点
│   ├── 000-default.conf
│   └── default-ssl.conf
├── sites-enabled/                ← 启用站点 (软链接)
│   └── 000-default.conf → ../sites-available/000-default.conf
├── mods-available/               ← 可用模块
├── mods-enabled/                 ← 启用模块 (软链接)
└── conf-enabled/                 ← 启用的全局配置
```

```bash
# 主配置 /etc/httpd/conf/httpd.conf (Rocky)

ServerRoot "/etc/httpd"
Listen 80

# 模块加载
Include conf.modules.d/*.conf

# 用户
User apache
Group apache

# 管理员邮箱
ServerAdmin root@localhost

# 根目录权限 (全局禁止)
<Directory />
    AllowOverride none
    Require all denied
</Directory>

# 文档根目录
DocumentRoot "/var/www/html"
<Directory "/var/www">
    AllowOverride None
    Require all granted
</Directory>

# 目录索引
DirectoryIndex index.html index.php

# 日志
ErrorLog "logs/error_log"
LogLevel warn
LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined
CustomLog "logs/access_log" combined

# 包含额外配置
IncludeOptional conf.d/*.conf
```

### 3.3 MPM（多处理模块）

Apache 的并发模型由 MPM 决定：

| MPM | 模型 | 适用 | 特点 |
|:---|:---|:---|:---|
| **prefork** | 多进程, 每进程一个线程 | PHP (mod_php) | 稳定, 内存占用大 |
| **worker** | 多进程, 每进程多线程 | 静态/反代 | 内存占用小, 线程安全要求高 |
| **event** | 多进程, 异步线程 | 推荐 (现代 Apache) | 性能最优, 类似 Nginx |

```bash
# 查看 MPM
httpd -M | grep mpm
# Ubuntu: apache2ctl -M | grep mpm

# 切换 MPM (Rocky)
# /etc/httpd/conf.modules.d/00-mpm.conf
# 注释 prefork, 启用 event:
LoadModule mpm_event_module modules/mod_mpm_event.so
# LoadModule mpm_prefork_module modules/mod_mpm_prefork.so

# Ubuntu:
a2dismod mpm_prefork
a2enmod mpm_event
systemctl restart apache2

# === MPM 参数调优 ===
# /etc/httpd/conf.modules.d/00-mpm.conf (event MPM)
<IfModule mpm_event_module>
    StartServers            4        # 启动时子进程数
    ServerLimit            16        # 最大子进程数
    ThreadsPerChild       64        # 每进程线程数
    MaxRequestWorkers    1024        # 最大并发连接 (ServerLimit × ThreadsPerChild)
    MaxConnectionsPerChild 0         # 每子进程处理多少连接后重启 (0=不重启)
    AsyncRequestWorkerFactor 2       # 异步因子 (event 专用)
    KeepAliveTimeout       5         # 长连接超时
    MaxKeepAliveRequests 100         # 长连接最大请求
</IfModule>

# Ubuntu: /etc/apache2/mods-available/mpm_event.conf
```

### 3.4 虚拟主机

```bash
# /etc/httpd/conf.d/vhost.conf (Rocky)

# === 基于域名的虚拟主机 (HTTP) ===
<VirtualHost *:80>
    ServerName site-a.example.com
    ServerAlias www.site-a.example.com
    DocumentRoot /var/www/site-a

    ErrorLog  logs/site-a-error.log
    CustomLog logs/site-a-access.log combined

    <Directory /var/www/site-a>
        AllowOverride All             # 允许 .htaccess
        Require all granted
    </Directory>

    DirectoryIndex index.html index.php
</VirtualHost>

<VirtualHost *:80>
    ServerName site-b.example.com
    DocumentRoot /var/www/site-b
    ErrorLog  logs/site-b-error.log
    CustomLog logs/site-b-access.log combined

    <Directory /var/www/site-b>
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>

# === HTTPS 虚拟主机 ===
<VirtualHost *:443>
    ServerName site-a.example.com
    DocumentRoot /var/www/site-a

    SSLEngine on
    SSLCertificateFile      /etc/pki/tls/certs/site-a.crt
    SSLCertificateKeyFile   /etc/pki/tls/private/site-a.key
    SSLCertificateChainFile /etc/pki/tls/certs/site-a-chain.crt

    # SSL 优化
    SSLProtocol             all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite          ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
    SSLHonorCipherOrder     off
    SSLSessionTickets       off

    # 安全头
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"

    ErrorLog  logs/site-a-ssl-error.log
    CustomLog logs/site-a-ssl-access.log combined
</VirtualHost>
```

```bash
# Ubuntu 方式: sites-available + a2ensite
# /etc/apache2/sites-available/site-a.conf
<VirtualHost *:80>
    ServerName site-a.example.com
    DocumentRoot /var/www/site-a
    ...
</VirtualHost>

# 启用
a2ensite site-a
# 禁用
a2dissite site-a
# 重载
systemctl reload apache2
```

### 3.5 反向代理

```bash
# 启用模块
# Rocky: 编辑 conf.modules.d/00-proxy.conf
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so
LoadModule proxy_balancer_module modules/mod_proxy_balancer.so
LoadModule lbmethod_byrequests_module modules/mod_lbmethod_byrequests.so
LoadModule headers_module modules/mod_headers.so
LoadModule ssl_module modules/mod_ssl.so

# Ubuntu:
a2enmod proxy proxy_http proxy_balancer headers ssl

# /etc/httpd/conf.d/reverse-proxy.conf

# === 简单反代 ===
<VirtualHost *:80>
    ServerName api.example.com

    ProxyPreserveHost On
    ProxyPass        / http://127.0.0.1:8080/
    ProxyPassReverse / http://127.0.0.1:8080/

    # 传递客户端 IP
    ProxySet headers=X-Forwarded-For "%{REMOTE_ADDR}s"

    ErrorLog logs/api-proxy-error.log
    CustomLog logs/api-proxy-access.log combined
</VirtualHost>

# === 负载均衡 ===
<VirtualHost *:80>
    ServerName lb.example.com

    <Proxy balancer://backend>
        BalancerMember http://192.168.1.10:8080 loadfactor=3
        BalancerMember http://192.168.1.11:8080 loadfactor=2
        BalancerMember http://192.168.1.12:8080 loadfactor=1
        # 负载策略: byrequests(轮询) | bytraffic(流量) | bybusyness(忙碌度)
        ProxySet lbmethod=byrequests
        # 健康检查
        ProxySet retry=30
    </Proxy>

    ProxyPreserveHost On
    ProxyPass        / balancer://backend/
    ProxyPassReverse / balancer://backend/

    # 负载均衡管理界面 (可选)
    <Location /balancer-manager>
        SetHandler balancer-manager
        Require ip 192.168.1.0/24
    </Location>
</VirtualHost>
```

### 3.6 PHP (mod_php vs PHP-FPM)

```bash
# === 方式一: mod_php (传统, 仅 prefork MPM) ===
dnf install -y php php-mysqlnd
# /etc/httpd/conf.modules.d/15-php.conf 会自动配置
# 优点: 简单, .htaccess 直接生效
# 缺点: 每 worker 都加载 PHP, 内存占用大

# === 方式二: PHP-FPM (推荐, 兼容所有 MPM) ===
dnf install -y php-fpm
systemctl enable --now php-fpm

# /etc/httpd/conf.d/php-fpm.conf
<FilesMatch \.php$>
    SetHandler "proxy:fcgi://127.0.0.1:9000"
</FilesMatch>

# 如果用 Unix socket:
# <FilesMatch \.php$>
#     SetHandler "proxy:unix:/run/php-fpm/www.sock|fcgi://localhost"
# </FilesMatch>

# 优点: PHP 进程独立, 内存占用小, 可切 event MPM
# 缺点: .htaccess 中 php_value 不生效 (需在 php.ini 或 pool 配置)
```

### 3.7 .htaccess 常用配置

```apache
# /var/www/site-a/.htaccess (需 AllowOverride All)

# === URL 重写 (伪静态) ===
RewriteEngine On

# WordPress 固定链接
RewriteRule ^index\.php$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.php [L]

# HTTP → HTTPS 重定向
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]

# 防盗链
RewriteEngine On
RewriteCond %{HTTP_REFERER} !^$
RewriteCond %{HTTP_REFERER} !^https://(www\.)?example\.com/ [NC]
RewriteRule \.(jpg|jpeg|png|gif|css|js)$ - [F]

# 访问保护
# 保护 .htaccess 自身
<Files ".htaccess">
    Require all denied
</Files>

# 保护配置文件
<FilesMatch "(^\.|wp-config\.php|xmlrpc\.php)">
    Require all denied
</FilesMatch>

# 目录列表关闭
Options -Indexes

# 自定义错误页
ErrorDocument 404 /404.html
ErrorDocument 500 /500.html

# 缓存控制
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpg "access plus 30 days"
    ExpiresByType image/png "access plus 30 days"
    ExpiresByType text/css  "access plus 7 days"
    ExpiresByType application/javascript "access plus 7 days"
</IfModule>

# Gzip 压缩
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/css application/javascript application/json
</IfModule>
```

---

## 四、Caddy

### 4.1 安装

```bash
# 官方一键安装 (推荐)
dnf install -y 'dnf-command(copr)'
dnf copr enable @caddy/caddy
dnf install -y caddy

# Ubuntu
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy

# 启动
systemctl enable --now caddy

# 验证
caddy version
curl -I http://localhost
```

### 4.2 配置（Caddyfile）

```bash
# Caddyfile 位置: /etc/caddy/Caddyfile
# 语法极简, 这是最大优势

# === 最简静态站 (自动 HTTPS) ===
site-a.example.com {
    root * /var/www/site-a
    file_server
}

# === 多站点 ===
site-a.example.com {
    root * /var/www/site-a
    file_server
    encode gzip
}

site-b.example.com {
    root * /var/www/site-b
    file_server
    encode gzip zstd
}

# === 反向代理 + 自动 HTTPS ===
api.example.com {
    reverse_proxy 127.0.0.1:8080
}

# === 负载均衡 ===
lb.example.com {
    reverse_proxy {
        to 192.168.1.10:8080 192.168.1.11:8080 192.168.1.12:8080
        # 策略
        lb_policy round_robin          # 轮询 (默认)
        # lb_policy least_conn         # 最少连接
        # lb_policy ip_hash            # IP hash

        # 健康检查
        health_uri /health
        health_interval 10s
        health_timeout 5s

        # 头部
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
    }
}

# === PHP-FPM ===
php.example.com {
    root * /var/www/php-site
    php_fastcgi 127.0.0.1:9000
    file_server
}

# === 静态 + API 混合 ===
app.example.com {
    # 静态文件
    handle /static/* {
        root * /var/www/app
        file_server
        header Cache-Control "public, max-age=31536000, immutable"
    }

    # API 反代
    handle /api/* {
        reverse_proxy 127.0.0.1:8080
    }

    # SPA 前端
    handle {
        root * /var/www/app
        try_files {path} /index.html
        file_server
    }
}

# === 手动指定证书 (不用自动 HTTPS) ===
internal.example.com {
    root * /var/www/internal
    file_server
    tls /etc/ssl/internal.crt /etc/ssl/internal.key
}

# === 仅 HTTP (不自动 HTTPS, 内网用) ===
http://intranet.example.com {
    root * /var/www/intranet
    file_server
}

# === 常用指令 ===
example.com {
    root * /var/www/site

    # Gzip + Zstandard 压缩
    encode gzip zstd

    # 安全头
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        # 删除 Server 头
        -Server
    }

    # 日志
    log {
        output file /var/log/caddy/example.log
        format json
    }

    # 访问限制
    @blocked not remote_ip 192.168.1.0/24
    respond @blocked 403

    # 速率限制 (需 caddy-ratelimit 插件)
    # rate_limit { zone dynamic 10r/m }

    file_server
}
```

```bash
# 操作
caddy validate --config /etc/caddy/Caddyfile   # 验证配置
caddy reload --config /etc/caddy/Caddyfile      # 热重载
caddy adapt --config /etc/caddy/Caddyfile       # 查看 JSON 配置 (调试用)

# Caddy 自动管理证书:
# - 自动申请 Let's Encrypt 证书
# - 自动续期 (到期前 30 天)
# - HTTP→HTTPS 自动重定向
# - 需要域名指向服务器 + 80/443 端口可达
```

---

## 五、HAProxy

### 5.1 安装

```bash
# Rocky / RHEL
dnf install -y haproxy

# Ubuntu
apt install -y haproxy

systemctl enable --now haproxy
haproxy -v
```

### 5.2 配置

```bash
# /etc/haproxy/haproxy.cfg

global
    log         127.0.0.1 local2          # 日志到 rsyslog
    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     10000                      # 全局最大连接
    user        haproxy
    group       haproxy
    daemon

    # 性能
    nbproc      4                           # 进程数 (或用 nbthread)
    # nbthread   4                          # 线程数 (二选一)
    cpu-map     auto:1/1-4 0-3             # CPU 亲和 (nbthread 模式)

    # SSL
    tune.ssl.default-dh-param 2048

    stats socket /var/lib/haproxy/stats    # 统计 socket

defaults
    mode                    http            # http | tcp
    log                     global
    option                  httplog
    option                  dontlognull
    option http-server-close
    option forwardfor       except 127.0.0.0/8
    option                  redispatch
    retries                 3
    timeout http-request    10s
    timeout queue           1m
    timeout connect         5s
    timeout client          30s
    timeout server          30s
    timeout http-keep-alive 10s
    timeout check           5s
    maxconn                 10000

# === 统计页面 ===
listen stats
    bind *:8404
    mode http
    stats enable
    stats uri /stats
    stats realm HAProxy\ Statistics
    stats auth admin:haproxy123
    stats refresh 10s

# === 前端: HTTP (80) ===
frontend http-in
    bind *:80
    mode http

    # ACL 路由
    acl is_api    hdr(host) -i api.example.com
    acl is_web    hdr(host) -i www.example.com

    use_backend api_pool   if is_api
    use_backend web_pool   if is_web
    default_backend web_pool

# === 前端: HTTPS (443) — TLS 终止 ===
frontend https-in
    bind *:443 ssl crt /etc/haproxy/ssl/example.com.pem alpn h2,http/1.1
    mode http

    # HTTP/2 支持 (alpn h2)
    # 证书文件需要包含证书 + 私钥 (cat fullchain.pem privkey.pem > example.com.pem)

    acl is_api    hdr(host) -i api.example.com
    acl is_web    hdr(host) -i www.example.com

    use_backend api_pool   if is_api
    use_backend web_pool   if is_web
    default_backend web_pool

# === HTTP → HTTPS 重定向 ===
frontend http-redirect
    bind *:80
    mode http
    redirect scheme https code 301 if !{ ssl_fc }

# === 后端池 ===
backend web_pool
    mode http
    balance roundrobin                     # roundrobin | leastconn | source
    option httpchk GET /health             # 健康检查
    http-check expect status 200

    # 会话保持 (Cookie)
    cookie SERVERID insert indirect nocache

    server web-01 192.168.1.10:80 check cookie web-01
    server web-02 192.168.1.11:80 check cookie web-02
    server web-03 192.168.1.12:80 check cookie web-03 backup

backend api_pool
    mode http
    balance leastconn
    option httpchk GET /api/health
    http-check expect status 200

    server api-01 192.168.1.20:8080 check inter 2s rise 2 fall 3
    server api-02 192.168.1.21:8080 check inter 2s rise 2 fall 3
    server api-03 192.168.1.22:8080 check inter 2s rise 2 fall 3

# === 四层负载均衡 (TCP, 如数据库) ===
# frontend mysql-lb
#     bind *:3306
#     mode tcp
#     default_backend mysql_pool
#
# backend mysql_pool
#     mode tcp
#     balance leastconn
#     option tcp-check
#     tcp-check connect
#     server mysql-01 192.168.1.30:3306 check
#     server mysql-02 192.168.1.31:3306 check
```

```bash
# 验证配置
haproxy -c -f /etc/haproxy/haproxy.cfg

# 热重载 (不断连接)
systemctl reload haproxy

# 统计页面
# 浏览器访问: http://<ip>:8404/stats
```

### 5.3 HAProxy 健康检查详解

```
check              # 启用健康检查 (默认 TCP 连接检查)
inter 2s           # 检查间隔 2 秒
rise 2             # 连续 2 次成功标记为 UP
fall 3             # 连续 3 次失败标记为 DOWN
fall 3 rise 2      # 完整写法

# HTTP 检查
option httpchk GET /health              # 检查路径
http-check expect status 200            # 期望返回 200
http-check expect rstring OK            # 期望返回体包含 OK
http-check expect status 200-299        # 期望 2xx 范围

# TCP 检查
option tcp-check
tcp-check connect                       # TCP 连接检查
tcp-check send PING\r\n                 # 发送数据
tcp-check expect string PONG            # 期望返回

# 主动 vs 被动
# 主动: HAProxy 定期检查 (option httpchk)
# 被动: 请求失败时自动标记 DOWN (observe layer4 / observe layer7)
```

---

## 六、Nginx vs Apache 配置对照

| 功能 | Nginx | Apache |
|:---|:---|:---|
| 虚拟主机 | `server { server_name a.com; }` | `<VirtualHost *:80> ServerName a.com` |
| 根目录 | `root /var/www/a;` | `DocumentRoot /var/www/a` |
| 反向代理 | `proxy_pass http://upstream;` | `ProxyPass / http://upstream/` |
| PHP | `fastcgi_pass 127.0.0.1:9000;` | `SetHandler "proxy:fcgi://127.0.0.1:9000"` |
| URL 重写 | `rewrite ^/old/(.*) /new/$1 permanent;` | `RewriteRule ^/old/(.*) /new/$1 [R=301,L]` |
| HTTPS | `listen 443 ssl; ssl_certificate ...;` | `SSLEngine on; SSLCertificateFile ...` |
| Gzip | `gzip on; gzip_types ...;` | `AddOutputFilterByType DEFLATE ...` |
| 缓存 | `expires 30d;` | `ExpiresByType ... "access plus 30 days"` |
| 访问控制 | `allow 192.168.1.0/24; deny all;` | `Require ip 192.168.1.0/24` |
| 负载均衡 | `upstream { server ...; }` | `<Proxy balancer://> BalancerMember` |
| 日志 | `access_log /var/log/...;` | `CustomLog logs/... combined` |
| 错误页 | `error_page 404 /404.html;` | `ErrorDocument 404 /404.html` |
| 热重载 | `nginx -s reload` | `systemctl reload httpd` |
| 配置检查 | `nginx -t` | `httpd -t` |

---

## 七、生产部署架构

### 7.1 Nginx + PHP-FPM 架构

```
┌─────────────────────────────────────────────────┐
│                    用户                          │
└──────────────────┬──────────────────────────────┘
                   │ HTTPS
┌──────────────────▼──────────────────────────────┐
│  Nginx (:443)                                    │
│  ┌──────────────────────────────────────────┐   │
│  │ TLS 终止                                  │   │
│  │ 静态文件 → /var/www/html/ (直出)          │   │
│  │ .php → FastCGI → PHP-FPM                  │   │
│  │ /api → proxy_pass → 后端服务               │   │
│  │ /static → 本地缓存                         │   │
│  └──────────────────────────────────────────┘   │
└──────┬───────────────────────────────────┬──────┘
       │ FastCGI (:9000)                    │ HTTP (:8080)
┌──────▼──────────┐               ┌────────▼──────┐
│  PHP-FPM         │               │  App (Go/Java) │
│  ┌─────────────┐ │               │                │
│  │ worker pool │ │               └────────────────┘
│  │  16 个进程   │ │
│  └─────────────┘ │
└──────┬──────────┘
       │
┌──────▼──────────┐
│  MySQL / Redis   │
└──────────────────┘
```

### 7.2 HAProxy + Nginx + App 多层架构

```
用户
  │
  ▼
HAProxy (:443)          ← TLS 终止 + 四层/七层负载
  │
  ├──→ Nginx-01 (:80)   ← 静态文件 + 路由
  ├──→ Nginx-02 (:80)
  │      │
  │      ├── 静态 → 本地磁盘/NFS
  │      └── /api → App
  │             │
  │             ├── App-01 (:8080)
  │             ├── App-02 (:8080)
  │             └── App-03 (:8080)
  │
  └──→ (备用) Nginx-03
```

### 7.3 完整生产配置示例

```bash
# Nginx 全栈配置: 静态 + PHP + API 反代 + 负载均衡

# /etc/nginx/conf.d/production.conf

# === 上游 API 池 ===
upstream api_backend {
    least_conn;
    server 192.168.1.20:8080 max_fails=3 fail_timeout=30s;
    server 192.168.1.21:8080 max_fails=3 fail_timeout=30s;
    server 192.168.1.22:8080 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# === 上游 PHP-FPM ===
upstream php_backend {
    server 127.0.0.1:9000;
    keepalive 16;
}

# === HTTP → HTTPS ===
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}

# === HTTPS 主站 ===
server {
    listen 443 ssl;
    http2 on;
    server_name example.com www.example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    root /var/www/example;
    index index.php index.html;

    # 日志 (含上游响应时间)
    access_log /var/log/nginx/example-access.log main;
    error_log  /var/log/nginx/example-error.log warn;

    # 主路由
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    # PHP
    location ~ \.php$ {
        fastcgi_pass   php_backend;
        fastcgi_index  index.php;
        fastcgi_param  SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include        fastcgi_params;
        fastcgi_http_version 1.1;
        fastcgi_set_header Connection "";
        fastcgi_read_timeout 60s;
    }

    # API 反代
    location /api/ {
        proxy_pass http://api_backend/;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_connect_timeout 5s;
        proxy_read_timeout    30s;
        proxy_next_upstream   error timeout http_502 http_503 http_504;
    }

    # 静态资源缓存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff2?|svg|eot|ttf)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # 安全: 禁止访问敏感文件
    location ~ /\.(?!well-known) {
        deny all;
    }
    location ~ /\.(env|git|htaccess|htpasswd) {
        deny all;
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
```

---

## 八、运维操作速查

### 8.1 日常操作

```bash
# === Nginx ===
nginx -t                              # 检查配置
nginx -T                              # 打印完整配置
nginx -s reload                       # 热重载
nginx -s stop                         # 停止
systemctl restart nginx               # 重启 (会断开连接)
nginx -V                              # 编译参数 + 模块

# === Apache ===
httpd -t                               # 检查配置
httpd -M                               # 已加载模块
httpd -S                               # 虚拟主机列表
systemctl reload httpd                 # 优雅重载
apachectl graceful                     # 同上
# Ubuntu:
apache2ctl -t && apache2ctl configtest
a2enmod rewrite && systemctl reload apache2

# === Caddy ===
caddy validate --config /etc/caddy/Caddyfile
caddy reload --config /etc/caddy/Caddyfile
caddy stop
caddy start --config /etc/caddy/Caddyfile

# === HAProxy ===
haproxy -c -f /etc/haproxy/haproxy.cfg  # 检查
systemctl reload haproxy                # 热重载 (不断连接)
haproxy -vv                             # 版本 + 编译信息
```

### 8.2 压力测试

```bash
# ab (Apache Bench) — 简单压测
ab -n 10000 -c 100 https://example.com/
# -n: 总请求数  -c: 并发数
ab -n 10000 -c 100 -k https://example.com/   # -k: keepalive

# wrk — 更强大的压测
dnf install -y wrk
wrk -t4 -c100 -d30s https://example.com/
# -t: 线程数  -c: 连接数  -d: 持续时间

# wrk 自定义脚本
cat > /tmp/post.lua << 'EOF'
wrk.method = "POST"
wrk.body   = '{"key":"value"}'
wrk.headers["Content-Type"] = "application/json"
EOF
wrk -t4 -c100 -d30s -s /tmp/post.lua https://api.example.com/endpoint

# hey (Go 写的压测工具, 支持 JSON 输出)
dnf install -y hey
hey -n 10000 -c 100 https://example.com/
hey -n 10000 -c 100 -m POST -d '{"key":"value"}' -T application/json https://api.example.com/endpoint

# 持续观察服务端
watch -n 1 'ss -s && nginx -T 2>/dev/null | grep worker_connections'
```

### 8.3 证书管理

```bash
# Let's Encrypt (certbot)
certbot certificates                  # 查看证书
certbot renew --dry-run               # 测试续期
certbot renew                         # 实际续期
certbot delete --cert-name example.com # 删除证书

# 证书信息检查
openssl s_client -connect example.com:443 -servername example.com
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates -subject -issuer

# 证书到期检查 (监控用)
echo | openssl s_client -connect example.com:443 2>/dev/null | \
    openssl x509 -noout -enddate | cut -d= -f2
```

### 8.4 常见问题排查

```bash
# === 端口被占用 ===
ss -tlnp | grep :80
# 找到进程后:
systemctl stop <service>
# 或修改新服务端口

# === 502 Bad Gateway ===
# 原因: 后端服务挂了 / 端口不对 / 防火墙
# 排查:
curl http://127.0.0.1:8080          # 后端能否直接访问
ss -tlnp | grep 8080                # 后端是否在监听
tail /var/log/nginx/error.log       # Nginx 错误日志

# === 504 Gateway Timeout ===
# 原因: 后端响应太慢
# 解决: 增加 proxy_read_timeout
# proxy_read_timeout 120s;

# === 文件权限 ===
# Nginx 需要对静态文件有读取权限
# 检查路径上每一级目录的权限
namei -l /var/www/site-a/index.html

# === SELinux 拒绝 ===
# Nginx 访问非标准端口/目录
semanage port -a -t http_port_t -p tcp 8080
semanage fcontext -a -t httpd_sys_content_t "/var/www(/.*)?"
restorecon -Rv /var/www
setsebool -P httpd_can_network_connect on

# === 配置不生效 ===
nginx -t && systemctl reload nginx  # 确认检查 + 重载
nginx -T | grep "server_name"       # 确认配置已加载
```

---

## 九、配置文件速查表

| 服务 | 配置文件 | 说明 |
|:---|:---|:---|
| Nginx | `/etc/nginx/nginx.conf` | 主配置 |
| Nginx | `/etc/nginx/conf.d/*.conf` | 站点配置 |
| Nginx | `/etc/nginx/snippets/*.conf` | 复用片段 |
| Apache | `/etc/httpd/conf/httpd.conf` | 主配置 (RHEL) |
| Apache | `/etc/httpd/conf.d/*.conf` | 扩展配置 (RHEL) |
| Apache | `/etc/httpd/conf.modules.d/*.conf` | 模块配置 (RHEL) |
| Apache | `/etc/apache2/apache2.conf` | 主配置 (Ubuntu) |
| Apache | `/etc/apache2/sites-available/*.conf` | 站点 (Ubuntu) |
| Apache | `/etc/apache2/ports.conf` | 端口 (Ubuntu) |
| Caddy | `/etc/caddy/Caddyfile` | 唯一配置文件 |
| HAProxy | `/etc/haproxy/haproxy.cfg` | 唯一配置文件 |
| PHP-FPM | `/etc/php-fpm.d/www.conf` (RHEL) | FPM 池配置 |
| PHP-FPM | `/etc/php/*/fpm/pool.d/www.conf` (Ubuntu) | FPM 池配置 |
| 证书 | `/etc/letsencrypt/live/<domain>/` | Let's Encrypt |
| 证书 | `/etc/pki/tls/` (RHEL) | 系统 TLS 证书 |

---

*最后更新: 2026-07-09*
