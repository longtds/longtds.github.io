# 网络项目与实验

## 搭建小型企业网络

```
拓扑：
    [Internet]
        │
    [防火墙/NAT]
        │
    [核心交换机] ─── [汇聚交换机] ─── [接入交换机] ─── [服务器]
        │
    [DMZ 交换机] ─── [Web 服务器群]

实验内容：
1. VLAN 划分（VLAN 10-数据/20-DMZ/30-管理）
2. 三层路由（OSPF）
3. ACL 访问控制
4. NAT 端口映射
```

## Cilium 网络策略实验

```bash
# 部署测试应用
kubectl create deployment app --image=nginx
kubectl expose deployment app --port=80

# 应用网络策略
cat <<EOF | kubectl apply -f -
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-frontend
spec:
  endpointSelector:
    matchLabels:
      app: app
  ingress:
  - fromEndpoints:
    - matchLabels:
        role: frontend
EOF
```
