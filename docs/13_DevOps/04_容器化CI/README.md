# 容器化 CI

## Dockerfile 最佳实践

```dockerfile
# 多阶段构建
FROM golang:1.22 AS build
COPY . .
RUN CGO_ENABLED=0 go build -o app

FROM alpine:3.19
COPY --from=build /go/app /app
USER 1001
ENTRYPOINT ["/app"]
```

## Kaniko 安全构建

Kaniko 无需 Docker daemon，在容器内构建镜像，适合 CI/CD 环境。

```bash
/kaniko/executor \
  --context=dir://. \
  --dockerfile=Dockerfile \
  --destination=harbor.company.com/app:v1
```

## Trivy 镜像扫描

```bash
# 扫描漏洞
trivy image harbor.company.com/app:v1
trivy image --severity CRITICAL,HIGH harbor.company.com/app:v1

# 输出格式
trivy image --format json -o report.json harbor.company.com/app:v1
```
