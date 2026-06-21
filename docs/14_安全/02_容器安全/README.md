# 容器安全

## Trivy 扫描

```bash
# 镜像漏洞扫描
trivy image alpine:3.19

# 文件系统扫描
trivy fs .

# 仓库扫描
trivy repo https://github.com/org/repo
```

## 运行时安全

```bash
# Seccomp 限制系统调用
docker run --security-opt seccomp=/path/to/profile.json nginx

# AppArmor
docker run --security-opt apparmor=my-profile nginx

# Capabilities 最小化
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE nginx
```

## 镜像签名

```bash
# Cosign 签名
cosign sign --key cosign.key harbor.company.com/app:v1

# 验证
cosign verify --key cosign.pub harbor.company.com/app:v1
```
