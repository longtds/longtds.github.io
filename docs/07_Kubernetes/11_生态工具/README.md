# 生态工具

## Helm

Helm 是 K8s 的包管理器。

```bash
# 常用命令
helm repo add bitnami https://charts.bitnami.com/bitnami
helm search repo nginx
helm install my-nginx bitnami/nginx -n default
helm list
helm upgrade my-nginx bitnami/nginx --set replicaCount=3
helm rollback my-nginx 1
helm uninstall my-nginx

# 创建 Chart
helm create my-chart
```

## K9s

K9s 是 K8s 的终端 UI 管理工具。

```bash
# 安装
brew install k9s    # macOS
# 或下载二进制

# 快捷键
:pod        # 查看 Pod
:deploy     # 查看 Deployment
:ns default # 切换命名空间
/nginx      # 搜索
d           # 查看详情
l           # 查看日志
e           # 编辑资源
```

## KubeSphere

KubeSphere 是开源 K8s 管理平台，提供多租户管理、DevOps、可观测性等功能。

## 常用 kubectl 插件

```bash
# krew 插件管理器
brew install krew
kubectl krew install tree   # 资源树
kubectl krew install sniff  # 抓包
kubectl krew install tail   # 日志 tail
kubectl krew install df-pv  # PV 使用量
```
