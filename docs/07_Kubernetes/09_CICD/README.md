# CI/CD on K8s

## Jenkins on K8s

Jenkins 通过 Kubernetes Plugin 实现动态 Agent，根据 Pipeline 负载自动创建和销毁 Agent Pod。

```bash
# Jenkins Operator 部署
helm repo add jenkins https://jenkins-infra.github.io/helm-charts
helm install jenkins-operator jenkins/jenkins-operator -n jenkins

# Jenkins Agent Pod 模板（动态创建）
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:latest
  - name: kubectl
    image: bitnami/kubectl:latest
  - name: trivy
    image: aquasec/trivy:latest
  serviceAccountName: jenkins-deployer
```

## ArgoCD GitOps

```bash
# 安装 ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 创建 Application
argocd app create web-app \
  --repo https://gitlab.company.com/web-app \
  --path k8s \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace production
```

## Harbor 镜像管理

Harbor 是 CNCF 毕业的镜像仓库项目，支持漏洞扫描、镜像复制和清理策略。

## Keptn 质量门

Keptn 在部署时评估 SLO，不达标自动回滚。
