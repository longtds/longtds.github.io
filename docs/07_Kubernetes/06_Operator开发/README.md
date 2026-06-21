# Operator 开发

## Operator 模式

Operator 将运维人员的知识编码为自动化逻辑，通过 CRD + Controller 模式实现。

## kubebuilder 快速开始

```bash
# 安装 kubebuilder
curl -L -o kubebuilder https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)
chmod +x kubebuilder && mv kubebuilder /usr/local/bin/

# 初始化项目
kubebuilder init --domain company.com --repo github.com/company/my-operator
kubebuilder create api --group apps --version v1 --kind MyApp --resource --controller

# 生成的目录结构
├── api                    # CRD API 定义
│   └── v1/
│       ├── myapp_types.go
│       └── zz_generated.deepcopy.go
├── config                  # K8s 清单
├── controllers             # Reconciler 逻辑
│   └── myapp_controller.go
├── main.go
```

## Reconciler 核心逻辑

```go
func (r *MyAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // 1. 获取 CR 实例
    var app myappv1.MyApp
    if err := r.Get(ctx, req.NamespacedName, &app); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // 2. 检查期望状态 vs 当前状态
    // 3. 执行调和动作（创建/更新/删除资源）
    // 4. 更新状态
    return ctrl.Result{RequeueAfter: 30 * time.Second}, nil
}
```

## 部署

```bash
make docker-build docker-push IMG=harbor.company.com/operator/my-operator:v1
make deploy IMG=harbor.company.com/operator/my-operator:v1
```
