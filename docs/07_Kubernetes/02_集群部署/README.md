# 集群部署

## kubeadm 集群安装

```bash
# 1. 安装 kubeadm/kubelet/kubectl
apt update
apt install -y kubeadm=1.30.0-00 kubelet=1.30.0-00 kubectl=1.30.0-00

# 2. 初始化控制面
kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --service-cidr=10.96.0.0/12 \
  --control-plane-endpoint=10.0.0.10:6443

# 3. 配置 kubectl
mkdir -p $HOME/.kube
cp /etc/kubernetes/admin.conf $HOME/.kube/config

# 4. 安装 CNI（Cilium）
helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium --namespace kube-system

# 5. 加入工作节点
kubeadm join 10.0.0.10:6443 --token <token> --discovery-token-ca-cert-hash <hash>
```

## 集群 HA 设计

| 组件 | 高可用方案 |
|:---|:---|
| API Server | 多副本 + 负载均衡（SLB/HAProxy） |
| ETCD | 3/5 节点集群，奇数节点 |
| Controller Manager | Leader Election |
| Scheduler | Leader Election |

## 版本升级

```bash
# 控制面升级
apt install -y kubeadm=1.31.0-00
kubeadm upgrade plan
kubeadm upgrade apply v1.31.0

# 节点升级
apt install -y kubelet=1.31.0-00 kubectl=1.31.0-00
systemctl restart kubelet
```
