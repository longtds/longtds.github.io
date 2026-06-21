# 容器运行时

## 运行时对比

| 运行时 | 类型 | 特点 |
|:---|:---|:---|
| runc | OCI 标准 | 当前最广泛使用 |
| containerd | 高级运行时 | K8s CRI 默认 |
| CRI-O | K8s CRI 原生 | 轻量级 |
| gVisor | 安全容器 | 额外隔离层 |
| Kata Containers | 安全容器 | VM 级隔离 |

## containerd

```bash
# containerd 常用命令（通过 ctr）
ctr images pull docker.io/library/nginx:alpine
ctr images ls
ctr run --rm docker.io/library/nginx:alpine nginx

# 通过 nerdctl（Docker 兼容 CLI）
nerdctl run -d --name web -p 80:80 nginx:alpine
nerdctl ps
```

## 镜像仓库

Harbor 是企业级的镜像仓库，支持漏洞扫描、镜像复制和访问控制。

```bash
# 登录 Harbor
docker login harbor.company.com

# 推送镜像
docker tag nginx:alpine harbor.company.com/library/nginx:alpine
docker push harbor.company.com/library/nginx:alpine

# 配置信任
# /etc/docker/daemon.json
{ "insecure-registries": ["harbor.company.com"] }
```
