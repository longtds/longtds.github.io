# Nacos

## 部署

```bash
# K8s Helm 部署
helm repo add nacos https://nacos.io/nacos-operator
helm install nacos nacos/nacos -n nacos \
  --set mode=cluster \
  --set db.mode=mysql \
  --set db.url=jdbc:mysql://mysql:3306/nacos \
  --set db.username=root \
  --set db.password=root
```

## CP 与 AP 模式

Nacos 同时支持 CP 和 AP 模式，这是它与 Eureka 和 Consul 最大的区别。

| 模式 | 一致性 | 可用性 | 场景 |
|:---|:---:|:---:|:---|
| AP（默认） | 最终一致性 | 高 | 服务发现 |
| CP | 强一致性 | 中 | 配置中心 |

## 配置管理最佳实践

```yaml
# 配置格式建议
data-id: app-{profile}.{format}
group: DEFAULT_GROUP
# 示例
data-id: user-service-prod.yaml
```
