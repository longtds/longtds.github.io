# Docker 实践

## 安装与配置

```bash
# Ubuntu 安装 Docker
apt install -y docker.io
systemctl enable --now docker

# 配置 daemon.json
cat > /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF
systemctl restart docker
```

## Dockerfile 最佳实践

```dockerfile
# 多阶段构建
FROM golang:1.22 AS build
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o app .

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
COPY --from=build /app/app /app
USER 1001
EXPOSE 8080
ENTRYPOINT ["/app"]
```

## 常用命令

```bash
# 镜像管理
docker pull nginx:alpine
docker images
docker rmi <image>
docker system prune -f

# 容器管理
docker run -d --name web -p 80:80 nginx:alpine
docker exec -it <container> sh
docker logs -f <container>
docker stats

# 网络
docker network create --driver bridge app-net
docker network ls
```
