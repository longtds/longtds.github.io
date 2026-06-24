# Nacos

> 阿里开源的"配置中心 + 服务发现 + 服务管理"三合一中间件。**国内 Java 微服务事实标准**，特别是 Spring Cloud Alibaba 生态。

## 一、来历与发展

| 年份 | 事件 |
|:---:|:---|
| 2018.7 | 阿里巴巴开源 Nacos 0.1.0（脱胎于阿里内部 ConfigServer + Diamond） |
| 2019.4 | 1.0.0 GA |
| 2020.6 | Spring Cloud Alibaba 毕业，Nacos 成为默认注册/配置中心 |
| 2022 | 2.0 改用 gRPC 通信、长连接（性能数量级提升） |
| 2023 | 2.2 增强 K8s 集成、多语言客户端 |
| 2024 | **2.3** 安全增强、JRaft 一致性升级 |
| 2025 | 3.x 规划，云原生方向 |

**当前主流**：2.3.x / 2.4.x。

## 二、定位与功能

```
Nacos = 配置中心（替代 Spring Cloud Config）
      + 服务发现（替代 Eureka / Consul）
      + 服务元数据 / 健康检查 / DNS
      + 流量管理（部分能力）
```

### 三大核心能力

| 能力 | 替代品 |
|:---|:---|
| **动态配置** | Spring Cloud Config + Bus、Apollo、ZK |
| **服务发现** | Eureka、Consul、ZK、ETCD |
| **服务管理** | Service Mesh 部分场景 |

## 三、架构原理

```
┌─────────────── 客户端 ─────────────┐
│ SDK (Java/Go/Python/Node/.NET)    │
│ Spring Cloud Alibaba              │
│ Dubbo                             │
└──────────────┬────────────────────┘
               ↓ gRPC（2.0+ 长连接）/HTTP
┌─────────────── Nacos Server ──────┐
│ Naming Service（服务发现）         │
│ Config Service（配置中心）         │
│ Console（Web UI）                 │
│ 鉴权 / 命名空间 / 分组            │
└──────────────┬────────────────────┘
               ↓
┌────────────── 存储 ───────────────┐
│ MySQL（持久化） + JRaft（一致性）  │
│ Derby（默认，仅单机）              │
└───────────────────────────────────┘
```

### 核心概念

| 概念 | 说明 |
|:---|:---|
| **Namespace** | 多环境隔离（dev/test/prod） |
| **Group** | 配置/服务分组（默认 DEFAULT_GROUP） |
| **DataId** | 配置唯一 ID（如 `app.properties`） |
| **Service** | 服务名（如 `order-service`） |
| **Cluster** | 服务实例的逻辑集群 |
| **Instance** | 服务实例（IP+Port） |
| **Tenant** | 租户（=Namespace ID） |

## 四、使用场景

### ✅ 推荐

| 场景 | 说明 |
|:---|:---|
| **Spring Cloud Alibaba 项目** | 默认配置/注册中心 |
| **Dubbo 服务治理** | 注册中心首选 |
| **多环境配置统一管理** | dev/test/staging/prod |
| **动态配置** | 改完即生效，免重启 |
| **多语言微服务发现** | 比 Eureka 多语言支持好 |
| **K8s 外服务发现** | 混合架构（K8s + VM） |
| **国产化场景** | 替代 Eureka/Consul，信创友好 |

### ⚠️ 慎选

- **纯 K8s + Service Mesh**：K8s Service + Istio 已足够
- **超大规模配置（> 10 万 DataId）**：Apollo 在大配置量下更稳
- **强一致 KV 存储**：用 etcd

## 五、Nacos vs 其他

| 维度 | Nacos | Apollo | Consul | Eureka | etcd | ZK |
|:---|:---|:---|:---|:---|:---|:---|
| 配置中心 | ✅ | ✅ | ✅ | ❌ | ⚠️ | ⚠️ |
| 服务发现 | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 易用性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| 国内生态 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Web 控制台 | 自带 | 自带 | 自带 | 简陋 | ❌ | ❌ |
| 多语言 | 中 | 中 | 强 | 弱 | 强 | 中 |
| K8s 友好 | 中 | 中 | 强 | 弱 | 强 | 中 |
| 适合规模 | 中-大 | 大 | 大 | 中 | 大 | 中 |

> 💡 **国内 Java 微服务首选 Nacos，超大规模配置管理可选 Apollo，多语言/K8s 优先 Consul**。

## 六、最佳实践

### 6.1 部署架构

```
最小生产配置:
  - 3 节点集群（奇数，JRaft 仲裁）
  - MySQL 主从 + 共享存储
  - VIP / Nginx 反向代理
  - 独立 Namespace 隔离环境

推荐:
  - 3-5 节点
  - 单独网络区域
  - 监控接入 Prometheus
  - 持久化 MySQL 8.0
```

### 6.2 部署模式

```bash
# 单机模式（仅测试）
sh startup.sh -m standalone

# 集群模式
# 1. 修改 conf/cluster.conf 加入所有节点
192.168.1.1:8848
192.168.1.2:8848
192.168.1.3:8848

# 2. 配置 application.properties 指向 MySQL
spring.datasource.platform=mysql
db.num=1
db.url.0=jdbc:mysql://mysql-host:3306/nacos?...
db.user.0=nacos
db.password.0=...

# 3. 启动
sh startup.sh
```

### 6.3 命名空间设计

```
推荐结构:
  Namespace: dev / test / staging / prod
    Group:   <业务线>-<子系统>
      DataId: <app-name>.<env>.<ext>
                例: payment.prod.yaml

❌ 不要全部塞 DEFAULT_GROUP
❌ 不要用 Namespace 区分业务（用 Group）
```

### 6.4 配置最佳实践

```yaml
# Spring Cloud Alibaba 接入
spring:
  application:
    name: order-service
  cloud:
    nacos:
      config:
        server-addr: nacos-cluster:8848
        namespace: prod
        group: payment-line
        file-extension: yaml
        refresh-enabled: true
        username: nacos
        password: ${NACOS_PWD}
      discovery:
        server-addr: nacos-cluster:8848
        namespace: prod
        metadata:
          version: v1
          region: cn-east-1

management:
  endpoints:
    web:
      exposure:
        include: '*'
```

```java
// 监听配置变化（无需重启）
@NacosValue(value = "${threshold:100}", autoRefreshed = true)
private int threshold;

// Spring Boot @RefreshScope
@RestController
@RefreshScope
public class OrderController { ... }
```

### 6.5 安全加固

```
✅ 修改默认 nacos/nacos 密码
✅ 开启鉴权: nacos.core.auth.enabled=true
✅ 设置鉴权密钥: 
   nacos.core.auth.plugin.nacos.token.secret.key=<base64-32B>
   nacos.core.auth.server.identity.key/value=<custom>
✅ 客户端必须传 username/password
✅ 网络访问控制（白名单）
✅ HTTPS（前置 Nginx 终止）
✅ 命名空间隔离
✅ 定期审计变更日志
```

### 6.6 高可用要点

```
✅ 3 节点集群（JRaft 必须奇数）
✅ MySQL 主从 + 备份
✅ 配置 SQL 定期备份
✅ 客户端配置多 server-addr
✅ 监控集群健康（/nacos/v1/console/health）
✅ Server 节点机器分布在不同物理机/可用区
✅ 灰度升级
```

## 七、常见配置文件结构

```yaml
# 通用配置 common.yaml (DEFAULT_GROUP)
spring:
  datasource:
    username: ${DB_USER}
    password: ${DB_PWD}

logging:
  level:
    root: INFO

---
# 应用专属 order-service.yaml
server:
  port: 8080

biz:
  order:
    timeout: 3000
    retry: 3

---
# 共享文件（shared-configs）
shared:
  redis:
    host: redis.cluster
    port: 6379
```

## 八、运维命令速查

```bash
# 健康检查
curl http://nacos:8848/nacos/v1/console/health

# 配置 API
curl -X POST 'http://nacos:8848/nacos/v1/cs/configs' \
  -d 'dataId=app.yaml&group=DEFAULT_GROUP&content=...'

curl 'http://nacos:8848/nacos/v1/cs/configs?dataId=app.yaml&group=DEFAULT_GROUP'

# 服务列表
curl 'http://nacos:8848/nacos/v1/ns/service/list?pageNo=1&pageSize=100'

# 实例
curl 'http://nacos:8848/nacos/v1/ns/instance/list?serviceName=order-service'

# 注册实例（手动）
curl -X POST 'http://nacos:8848/nacos/v1/ns/instance?serviceName=demo&ip=1.2.3.4&port=8080'

# 集群状态
curl 'http://nacos:8848/nacos/v1/core/cluster/nodes'
```

## 九、常见坑

| 坑 | 建议 |
|:---|:---|
| **默认 nacos/nacos** | 立即改！互联网常被打 |
| **未开鉴权** | 必开 + 强密钥 |
| **Derby 当生产存储** | 改 MySQL |
| **单机当生产** | 至少 3 节点集群 |
| **Namespace 滥用** | 严格按环境 |
| **2.x 服务不稳定** | gRPC 端口要通（默认 9848/9849） |
| **客户端版本不匹配** | 2.x Server + 2.x Client |
| **K8s 部署 PVC 丢失** | 必须挂持久卷或外接 MySQL |
| **配置爆炸** | 治理 + 命名规范 |
| **大配置（> 100KB）** | 拆分或改用文件存储 |
| **没有备份** | MySQL 定期备份 + 配置导出 |

## 十、监控

```
关键指标:
  - JVM 堆 / GC
  - 配置变更频率
  - 服务实例数量
  - 心跳异常 / 健康检查失败率
  - JRaft Leader 切换
  - MySQL 慢查询

工具:
  - Nacos 内置 actuator 端点
  - Prometheus + Grafana（社区 dashboard）
  - SkyWalking / Pinpoint 链路追踪
```

## 十一、Nacos in K8s

### 11.1 Helm 部署

```bash
helm repo add nacos https://nacos-group.github.io/nacos-k8s/
helm install nacos nacos/nacos \
  --set mode=cluster \
  --set replicaCount=3 \
  --set persistence.enabled=true \
  --set mysql.enabled=true
```

### 11.2 Operator

```
官方 Nacos Operator (CRD):
   apiVersion: nacos.io/v1alpha1
   kind: Nacos
   spec:
     replicas: 3
     image: nacos/nacos-server:v2.3.2
     storage: ...
```

## 十二、与 Spring Cloud Alibaba 整合

```
Spring Cloud Alibaba 推荐版本组合 (2024+):
  Spring Boot 3.2.x
  Spring Cloud 2023.x
  Spring Cloud Alibaba 2023.0.x
  Nacos Client 2.3.x

关键 starter:
  spring-cloud-starter-alibaba-nacos-config
  spring-cloud-starter-alibaba-nacos-discovery
  spring-cloud-starter-alibaba-sentinel  ← 限流熔断
  spring-cloud-starter-alibaba-seata     ← 分布式事务
```

## 十三、迁移建议

| 来源 | 目标 | 工具 |
|:---|:---|:---|
| Eureka → Nacos | nacos-eureka-sync 双向同步 |
| Consul → Nacos | nacos-sync 工具 |
| Apollo → Nacos | 导出 → API 批量导入 |
| ZK → Nacos | 客户端逐步迁移 |

## 十四、学习路径

```
入门:
  1. 单机起一个 Nacos（Docker）
  2. Spring Boot Demo 接入配置 + 注册
  3. 控制台操作（命名空间 / 分组 / 配置 / 服务）

进阶:
  4. 3 节点集群 + MySQL
  5. 鉴权 + HTTPS
  6. Sentinel + Seata 整合
  7. K8s Helm 部署

高阶:
  8. 灰度发布 / 配置加密
  9. 多机房容灾
  10. 监控告警
  11. 迁移 Eureka / Apollo 实战
```

## 十五、国产化与生态

| 替代 / 周边 | 说明 |
|:---|:---|
| **Polaris**（腾讯） | 国产替代竞品，含治理 |
| **Apollo**（携程） | 配置中心专精 |
| **Sentinel**（阿里） | 限流熔断 |
| **Seata**（阿里） | 分布式事务 |
| **Higress** | 云原生 API 网关 |
| **Spring Cloud Tencent** | 腾讯系微服务全家桶 |

> 📖 **核心判断**：Spring Cloud Alibaba 项目无脑选 Nacos；多语言场景看团队偏好（Nacos 客户端覆盖 Java/Go/Python/Node/.NET）；纯 K8s 场景可用 K8s Service + ConfigMap 替代部分能力。
