# Nginx

## 概述

Nginx 是高性能的反向代理和 Web 服务器。

## 基础配置

```nginx
# 反向代理
server {
    listen 80;
    server_name app.company.com;

    location / {
        proxy_pass http://backend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# 负载均衡
upstream backend {
    least_conn;  # 最少连接
    server 10.0.0.1:8080 weight=3;
    server 10.0.0.2:8080 weight=2;
    server 10.0.0.3:8080 backup;
}
```

## 性能调优

```nginx
worker_processes auto;
worker_connections 65535;
use epoll;

# /etc/nginx/nginx.conf
sendfile on;
tcp_nopush on;
keepalive_timeout 65;
keepalive_requests 1000;
client_max_body_size 10m;
```

## SSL 配置

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```
