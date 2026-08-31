# MinIO 集群 Kopf Operator 开发实战

> 为什么要写 Operator？MinIO 官方有 Operator 了还要自己写？因为企业里总有定制需求：和内部 CMDB 联动、和自家存储系统对接、自定义扩容/巡检/备份策略。本文从 0 到 1，用 Python + Kopf 框架开发一个生产可用的 MinIO 集群管理 Operator，覆盖 CRD 设计、Reconcile 循环、状态机、扩缩容、备份、监控、故障自愈、打包部署全流程。

---

## 一、为什么选 Kopf？架构总览

### 1.1 Operator 是什么

```text
K8s Operator = 把人类运维经验写成代码

  传统运维:
    人看告警 → 分析 → 执行运维操作 → 验证结果
    (依赖经验, 容易错, 不可复制)

  Operator:
    监听 CRD 变化 → Reconcile 循环 → 调整资源到期望状态 → 写回状态
    (自动化, 可复制, 可审计, 不睡觉)
```

### 1.2 为什么选 Kopf 而不是 Go (kubebuilder/operator-sdk)

| 对比项 | Kopf (Python) | kubebuilder (Go) |
|:---|:---|:---|
| 语言 | Python | Go |
| 上手速度 | 快 (Pythoner 一天能跑通) | 慢 (学 Go + 框架 + 代码生成) |
| 代码量 | 少 (装饰器风格, 声明式) | 多 (接口+结构体+reconciler 全套) |
| 类型安全 | 弱 (运行时发现) | 强 (编译期发现) |
| 性能 | 中 (Python GIL, 但 IO 密集型问题不大) | 高 (并发原生) |
| 生态 | 中 (Kopf 本身 + Python 库全) | 强 (K8s 原生生态) |
| 调试 | 容易 (Python pdb / 打印) | 需要 dlv / delve |
| 适用场景 | 内部工具 / 中小规模 / 快速迭代 | 公开发布 / 大规模 / 高性能 |

**一句话**：团队 Python 熟、做内部工具、快速迭代 → **Kopf**。要做开源产品、追求性能和生态 → **Go**。

### 1.3 本文要实现的 Operator 能力

我们要做的 MinIO Operator 支持以下能力：

| 能力 | 说明 |
|:---|:---|
| 集群创建 | 一条 CR 创建一套 MinIO 分布式集群 |
| 扩缩容 | 改 replicas 自动加/减节点，数据自动 Rebalance |
| 滚动升级 | 改 image 版本，逐节点滚动升级 |
| 配置管理 | 环境变量 / 配置文件统一管理 |
| 备份 | 定时备份到 S3 / NAS，保留策略 |
| 健康检查 | 节点级 + 集群级健康探测 |
| 故障自愈 | Pod 挂了自动拉起，数据盘损坏自动标记 |
| 用户/Bucket 管理 | 通过子 CR 创建用户和 Bucket |
| 监控指标 | /metrics 暴露 Prometheus 指标 |

### 1.4 整体架构

```text
MinIO Operator 架构:

┌────────────── K8s 集群 ───────────────────────────────────────┐
│                                                                │
│  ┌───────────────── 控制面 ──────────────────────────────┐    │
│  │                                                       │    │
│  │  minio-operator Deployment (Kopf)                     │    │
│  │    ├─ 监听 MinIOCluster CRD                           │    │
│  │    ├─ 监听 MinIOUser CRD                              │    │
│  │    ├─ 监听 MinIOBucket CRD                            │    │
│  │    └─ Reconcile → 创建/更新 StatefulSet / SVC / PVC  │    │
│  │                                                       │    │
│  └──────┬───────────────────────────┬────────────────────┘    │
│         │ 创建/管理                 │ 写回状态                │
│         ▼                           ▼                         │
│  ┌────────────────────┐  ┌────────────────────┐               │
│  │ MinIO 集群 A        │  │ MinIO 集群 B        │               │
│  │  StatefulSet        │  │  StatefulSet        │               │
│  │  Service (Headless) │  │  Service (Headless) │               │
│  │  PVC (每节点一块)    │  │  PVC (每节点一块)    │               │
│  │  4 节点纠删码        │  │  8 节点纠删码        │               │
│  └────────────────────┘  └────────────────────┘               │
│                                                                │
│  CRD:                                                          │
│    MinIOCluster   (集群级)                                     │
│    MinIOUser      (用户级)                                     │
│    MinIOBucket    (桶级)                                       │
└────────────────────────────────────────────────────────────────┘
```

---

## 二、环境搭建与项目结构

### 2.1 开发环境准备

```bash
# Python 版本 ≥ 3.10
python3 --version

# 虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装核心依赖
pip install kopf kubernetes pyyaml jinja2
pip install pytest pytest-mock black ruff mypy   # 开发工具

# 验证 kopf 能跑
kopf --version
```

**K8s 环境**：需要一个能访问的 K8s 集群（Kind/Minikube/测试集群都可以）。

```bash
# 用 kind 快速起一个本地集群 (可选)
kind create cluster --name minio-operator-dev
kubectl cluster-info
```

### 2.2 项目结构

```text
minio-operator/
├── src/
│   └── minio_operator/
│       ├── __init__.py
│       ├── main.py                 # 入口
│       ├── crds/
│       │   ├── __init__.py
│       │   ├── minio_cluster.py    # MinIOCluster CRD 定义
│       │   ├── minio_user.py       # MinIOUser CRD
│       │   └── minio_bucket.py     # MinIOBucket CRD
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── cluster.py          # 集群 reconcile 处理器
│       │   ├── user.py             # 用户处理器
│       │   └── bucket.py           # 桶处理器
│       ├── resources/
│       │   ├── __init__.py
│       │   ├── statefulset.py      # StatefulSet 模板生成
│       │   ├── service.py          # Service 模板
│       │   ├── pvc.py              # PVC 模板
│       │   └── configmap.py        # ConfigMap 模板
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── k8s.py              # K8s 客户端封装
│       │   ├── minio.py            # MinIO API 调用
│       │   └── metrics.py          # 指标收集
│       └── templates/
│           └── ...                 # Jinja2 模板 (可选)
├── config/
│   ├── crd.yaml                    # CRD 定义 (YAML)
│   ├── rbac.yaml                   # ClusterRole/Binding
│   ├── deployment.yaml             # Operator 部署
│   └── examples/
│       ├── miniocluster-sample.yaml
│       ├── miniouser-sample.yaml
│       └── miniobucket-sample.yaml
├── tests/
│   ├── test_cluster_handler.py
│   ├── test_resources.py
│   └── conftest.py
├── pyproject.toml
├── Dockerfile
└── README.md
```

### 2.3 CRD 定义

先定义 `MinIOCluster` CRD 的 YAML（注册到 K8s 用）：

```yaml
# config/crd.yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: minioclusters.storage.example.com
spec:
  group: storage.example.com
  names:
    kind: MinIOCluster
    listKind: MinIOClusterList
    plural: minioclusters
    singular: miniocluster
    shortNames:
      - mc
  scope: Namespaced
  versions:
    - name: v1alpha1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [replicas, storage, version]
              properties:
                replicas:
                  type: integer
                  minimum: 4              # MinIO 分布式最少 4 节点
                  maximum: 32
                version:
                  type: string
                  description: MinIO 镜像 tag
                  default: RELEASE.2024-08-17T01-10-17Z
                storage:
                  type: object
                  required: [size]
                  properties:
                    size:
                      type: string
                      description: 每个节点的存储大小
                    storageClass:
                      type: string
                      description: StorageClass 名称
                resources:
                  type: object
                  properties:
                    requests:
                      type: object
                      properties:
                        cpu: {type: string}
                        memory: {type: string}
                    limits:
                      type: object
                      properties:
                        cpu: {type: string}
                        memory: {type: string}
                env:
                  type: array
                  items:
                    type: object
                    properties:
                      name: {type: string}
                      value: {type: string}
                security:
                  type: object
                  properties:
                    rootUser:
                      type: string
                      default: minioadmin
                    rootPassword:
                      type: string
                    tls:
                      type: boolean
                      default: false
                backup:
                  type: object
                  properties:
                    enabled:
                      type: boolean
                      default: false
                    schedule:
                      type: string
                      default: "0 2 * * *"
                    target:
                      type: string
                    retentionDays:
                      type: integer
                      default: 30
            status:
              type: object
              x-kubernetes-preserve-unknown-fields: true
      subresources:
        status: {}
      additionalPrinterColumns:
        - name: Replicas
          type: integer
          jsonPath: .spec.replicas
        - name: Ready
          type: integer
          jsonPath: .status.readyReplicas
        - name: Phase
          type: string
          jsonPath: .status.phase
        - name: Age
          type: date
          jsonPath: .metadata.creationTimestamp
```

> **要点**：CRD 定义里必须开启 `subresources.status`，否则 Kopf 写状态会失败。`x-kubernetes-preserve-unknown-fields: true` 让 status 字段可以放任意结构。

```bash
# 注册 CRD
kubectl apply -f config/crd.yaml

# 验证
kubectl get crd minioclusters.storage.example.com
kubectl explain miniocluster.spec
```

### 2.4 最小可运行 Operator

先跑通一个"Hello World"级别的 Operator，验证开发链路。

```python
# src/minio_operator/main.py
import kopf
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("minio-operator")


@kopf.on.create("storage.example.com", "v1alpha1", "minioclusters")
def on_create(spec, name, namespace, logger, **kwargs):
    """MinIOCluster 创建处理器"""
    replicas = spec.get("replicas", 4)
    version = spec.get("version", "latest")
    logger.info(f"创建 MinIO 集群: {name} (replicas={replicas}, version={version})")

    # TODO: 真正的创建逻辑
    return {"message": f"集群 {name} 已创建 (待实现)"}


@kopf.on.update("storage.example.com", "v1alpha1", "minioclusters")
def on_update(spec, name, old, new, logger, **kwargs):
    """MinIOCluster 更新处理器"""
    logger.info(f"更新集群: {name}")
    logger.info(f"旧 spec replicas: {old.get('spec', {}).get('replicas')}")
    logger.info(f"新 spec replicas: {new.get('spec', {}).get('replicas')}")


@kopf.on.delete("storage.example.com", "v1alpha1", "minioclusters")
def on_delete(name, logger, **kwargs):
    """MinIOCluster 删除处理器"""
    logger.info(f"删除集群: {name}")


if __name__ == "__main__":
    kopf.run(
        clusterwide=False,        # 命名空间级
        namespace="default",      # 监听的命名空间
        verbose=True,
    )
```

```bash
# 本地运行 (需要 kubectl 有权限)
export PYTHONPATH=src
kopf run src/minio_operator/main.py --verbose

# 另一个终端: 创建一个 CR 测试
kubectl apply -f - <<EOF
apiVersion: storage.example.com/v1alpha1
kind: MinIOCluster
metadata:
  name: test-cluster
spec:
  replicas: 4
  version: RELEASE.2024-08-17T01-10-17Z
  storage:
    size: 10Gi
EOF

# 看 Operator 日志有没有输出 "创建 MinIO 集群"
kubectl get miniocluster
```

能看到日志输出 = 开发环境搭好了。接下来逐步填内容。

---

## 三、核心：Reconcile 循环与资源生成

### 3.1 为什么是 Reconcile 而不是 Create/Update/Delete

Kopf 提供两种风格：

| 风格 | 装饰器 | 触发时机 | 适用 |
|:---|:---|:---|:---|
| 事件驱动 | `@kopf.on.create` / `@kopf.on.update` / `@kopf.on.delete` | CR 创建/更新/删除时各调一次 | 简单场景 |
| 持续 Reconcile | `@kopf.daemon` / `@kopf.timer` / `@kopf.on.resume` | 持续比对期望状态和实际状态 | 生产推荐 |

**生产里必须用 Reconcile 模式**，因为：
1. Operator 重启后，已有的 CR 需要重新进入处理（resume）
2. 集群里的资源可能被人手动改了，要自动修正（漂移检测）
3. 状态机推进需要持续检查

```python
# src/minio_operator/handlers/cluster.py
import kopf
import kubernetes
from kubernetes.client import CoreV1Api, AppsV1Api
from ..resources.statefulset import build_statefulset
from ..resources.service import build_service
from ..utils.k8s import get_namespaced_name

v1 = CoreV1Api()
apps_v1 = AppsV1Api()


@kopf.daemon("storage.example.com", "v1alpha1", "minioclusters")
async def reconcile_cluster(
    stopped,
    name,
    namespace,
    spec,
    status,
    patch,
    logger,
    **kwargs,
):
    """
    每个 MinIOCluster 资源一个 daemon, 持续 reconcile。
    stopped 是一个 Event, Operator 退出时会 set, 用来结束循环。
    """
    logger.info(f"启动 reconcile 循环: {namespace}/{name}")

    while not stopped.is_set():
        try:
            # 1. 获取实际状态
            actual = get_actual_state(name, namespace)

            # 2. 比对期望状态 (spec) 和实际状态
            if needs_update(spec, actual):
                logger.info(f"检测到漂移, 开始 reconcile: {name}")
                desired = build_desired_resources(name, namespace, spec)
                apply_desired(desired, namespace, logger)
                update_status(patch, actual, spec, logger)

        except Exception as e:
            logger.error(f"Reconcile 失败: {e}", exc_info=True)
            # 出错了更新 status.conditions
            patch.status["conditions"] = [
                {
                    "type": "ReconcileFailed",
                    "status": "True",
                    "reason": "Exception",
                    "message": str(e),
                }
            ]

        # 每 30 秒 reconcile 一次
        await stopped.wait(30)


def get_actual_state(name, namespace):
    """获取集群实际状态"""
    try:
        sts = apps_v1.read_namespaced_stateful_set(name, namespace)
        return {
            "replicas": sts.spec.replicas,
            "ready_replicas": sts.status.ready_replicas or 0,
            "image": sts.spec.template.spec.containers[0].image,
            "exists": True,
        }
    except kubernetes.client.exceptions.ApiException as e:
        if e.status == 404:
            return {"exists": False, "replicas": 0, "ready_replicas": 0, "image": ""}
        raise


def needs_update(spec, actual):
    """判断是否需要更新"""
    if not actual["exists"]:
        return True
    if actual["replicas"] != spec["replicas"]:
        return True
    expected_image = f"minio/minio:{spec['version']}"
    if actual["image"] != expected_image:
        return True
    return False
```

> **Kopf 的 daemon 处理器**：每个 CR 实例启动一个协程（async）或线程（sync），生命周期和 CR 绑定，CR 删除时自动停掉。非常适合持续 reconcile 的场景。

### 3.2 StatefulSet 生成

MinIO 集群用 **StatefulSet** 部署（因为要稳定的网络标识 + 稳定的存储）。

```python
# src/minio_operator/resources/statefulset.py
from kubernetes.client import (
    V1StatefulSet,
    V1ObjectMeta,
    V1StatefulSetSpec,
    V1PodTemplateSpec,
    V1PodSpec,
    V1Container,
    V1VolumeMount,
    V1PersistentVolumeClaim,
    V1PersistentVolumeClaimSpec,
    V1ResourceRequirements,
    V1ServicePort,
    V1ContainerPort,
    V1EnvVar,
)


def build_statefulset(name: str, namespace: str, spec: dict) -> V1StatefulSet:
    """根据 MinIOCluster spec 生成 StatefulSet 对象"""
    replicas = spec["replicas"]
    version = spec.get("version", "RELEASE.2024-08-17T01-10-17Z")
    storage = spec["storage"]
    resources = spec.get("resources", {})
    env_list = spec.get("env", [])
    security = spec.get("security", {})
    root_user = security.get("rootUser", "minioadmin")
    root_pass = security.get("rootPassword", "minioadmin")

    # MinIO 分布式模式的命令
    # 格式: minio server http://{name}-{0..N-1}.{svc}.{ns}.svc.cluster.local/data
    svc_name = f"{name}-hl"
    servers = " ".join(
        f"http://{name}-{i}.{svc_name}.{namespace}.svc.cluster.local/data"
        for i in range(replicas)
    )

    # 环境变量
    env = [
        V1EnvVar(name="MINIO_ROOT_USER", value=root_user),
        V1EnvVar(name="MINIO_ROOT_PASSWORD", value=root_pass),
        V1EnvVar(name="MINIO_BROWSER_REDIRECT_URL", value=f"https://{name}.example.com/minio"),
    ]
    for e in env_list:
        env.append(V1EnvVar(name=e["name"], value=e.get("value", "")))

    # 资源
    resource_req = V1ResourceRequirements(
        requests=resources.get("requests", {}),
        limits=resources.get("limits", {}),
    )

    container = V1Container(
        name="minio",
        image=f"minio/minio:{version}",
        args=["server", servers, "--console-address", ":9001"],
        ports=[
            V1ContainerPort(name="api", container_port=9000),
            V1ContainerPort(name="console", container_port=9001),
        ],
        env=env,
        resources=resource_req,
        volume_mounts=[
            V1VolumeMount(name="data", mount_path="/data"),
        ],
        readiness_probe={
            "httpGet": {"path": "/minio/health/ready", "port": 9000},
            "initialDelaySeconds": 10,
            "periodSeconds": 5,
        },
        liveness_probe={
            "httpGet": {"path": "/minio/health/live", "port": 9000},
            "initialDelaySeconds": 30,
            "periodSeconds": 30,
        },
    )

    # PVC 模板 (每个节点一个 PVC)
    volume_claim_templates = [
        V1PersistentVolumeClaim(
            metadata=V1ObjectMeta(name="data"),
            spec=V1PersistentVolumeClaimSpec(
                access_modes=["ReadWriteOnce"],
                storage_class_name=storage.get("storageClass"),
                resources={"requests": {"storage": storage["size"]}},
            ),
        )
    ]

    sts = V1StatefulSet(
        api_version="apps/v1",
        kind="StatefulSet",
        metadata=V1ObjectMeta(
            name=name,
            namespace=namespace,
            labels={"app": "minio", "minio-cluster": name},
        ),
        spec=V1StatefulSetSpec(
            replicas=replicas,
            service_name=f"{name}-hl",
            selector={"matchLabels": {"app": "minio", "minio-cluster": name}},
            template=V1PodTemplateSpec(
                metadata=V1ObjectMeta(
                    labels={"app": "minio", "minio-cluster": name}
                ),
                spec=V1PodSpec(
                    containers=[container],
                    # MinIO 建议用 hostNetwork 提升性能 (可选)
                    # host_network=True,
                    # dns_policy: ClusterFirstWithHostNet
                ),
            ),
            volume_claim_templates=volume_claim_templates,
            pod_management_policy="OrderedReady",  # 有序启动
            update_strategy={"type": "RollingUpdate"},
        ),
    )
    return sts
```

### 3.3 Service 生成

```python
# src/minio_operator/resources/service.py
from kubernetes.client import (
    V1Service,
    V1ObjectMeta,
    V1ServiceSpec,
    V1ServicePort,
)


def build_headless_service(name: str, namespace: str) -> V1Service:
    """Headless Service: 给 StatefulSet 用, 每个 Pod 有稳定 DNS"""
    return V1Service(
        api_version="v1",
        kind="Service",
        metadata=V1ObjectMeta(
            name=f"{name}-hl",
            namespace=namespace,
            labels={"app": "minio", "minio-cluster": name},
        ),
        spec=V1ServiceSpec(
            cluster_ip="None",      # Headless
            selector={"app": "minio", "minio-cluster": name},
            ports=[
                V1ServicePort(name="api", port=9000, target_port=9000),
                V1ServicePort(name="console", port=9001, target_port=9001),
            ],
            publish_not_ready_addresses=True,   # 未就绪也有 DNS
        ),
    )


def build_cluster_service(name: str, namespace: str) -> V1Service:
    """普通 ClusterIP Service: 对外访问 API 和 Console"""
    return V1Service(
        api_version="v1",
        kind="Service",
        metadata=V1ObjectMeta(
            name=f"{name}-api",
            namespace=namespace,
            labels={"app": "minio", "minio-cluster": name},
        ),
        spec=V1ServiceSpec(
            selector={"app": "minio", "minio-cluster": name},
            ports=[
                V1ServicePort(name="api", port=9000, target_port=9000),
                V1ServicePort(name="console", port=9001, target_port=9001),
            ],
        ),
    )
```

### 3.4 应用资源到 K8s

```python
# src/minio_operator/utils/k8s.py
import kubernetes
from kubernetes.client import AppsV1Api, CoreV1Api
from kubernetes.client.exceptions import ApiException

apps_v1 = AppsV1Api()
core_v1 = CoreV1Api()


def create_or_update_statefulset(sts, namespace):
    """不存在就创建, 存在就 patch 更新 (类似 kubectl apply)"""
    try:
        apps_v1.read_namespaced_stateful_set(sts.metadata.name, namespace)
        # 已存在 → patch
        apps_v1.patch_namespaced_stateful_set(
            name=sts.metadata.name,
            namespace=namespace,
            body=sts,
        )
        return "updated"
    except ApiException as e:
        if e.status == 404:
            apps_v1.create_namespaced_stateful_set(namespace=namespace, body=sts)
            return "created"
        raise


def create_or_update_service(svc, namespace):
    try:
        core_v1.read_namespaced_service(svc.metadata.name, namespace)
        core_v1.patch_namespaced_service(
            name=svc.metadata.name, namespace=namespace, body=svc
        )
        return "updated"
    except ApiException as e:
        if e.status == 404:
            core_v1.create_namespaced_service(namespace=namespace, body=svc)
            return "created"
        raise


def delete_statefulset(name, namespace):
    try:
        apps_v1.delete_namespaced_stateful_set(name, namespace)
    except ApiException as e:
        if e.status != 404:
            raise
```

### 3.5 把 create/update/delete 串起来

```python
# 回到 handlers/cluster.py, 补全 apply_desired

from ..resources.statefulset import build_statefulset
from ..resources.service import build_headless_service, build_cluster_service
from ..utils.k8s import (
    create_or_update_statefulset,
    create_or_update_service,
    delete_statefulset,
)


def build_desired_resources(name, namespace, spec):
    """构建期望的资源列表"""
    return {
        "statefulset": build_statefulset(name, namespace, spec),
        "headless_svc": build_headless_service(name, namespace),
        "cluster_svc": build_cluster_service(name, namespace),
    }


def apply_desired(resources, namespace, logger):
    """应用期望资源到集群"""
    for kind, obj in resources.items():
        try:
            if kind == "statefulset":
                result = create_or_update_statefulset(obj, namespace)
            elif kind in ("headless_svc", "cluster_svc"):
                result = create_or_update_service(obj, namespace)
            logger.info(f"  {kind}: {result}")
        except Exception as e:
            logger.error(f"  {kind} 应用失败: {e}")
            raise
```

---

## 四、状态机与 Status 管理

### 4.1 Phase 状态机

```text
MinIOCluster Phase 状态机:

  Pending ──► Creating ──► Running ──► Updating ──► Running
                │             │           ▲
                ▼             ▼           │
              Failed ─────────┴───────────┘
                (出错就进 Failed, 修复后回 Running)
```

| Phase | 含义 |
|:---|:---|
| `Pending` | CR 刚创建，还没开始处理 |
| `Creating` | 正在创建资源 (StatefulSet/SVC/PVC) |
| `Running` | 所有副本就绪，正常运行 |
| `Updating` | 正在滚动更新 / 扩缩容 |
| `Failed` | 处理失败，人工介入 |
| `Deleting` | 正在删除 |

### 4.2 Status 字段设计

```python
# status 结构:
{
    "phase": "Running",
    "readyReplicas": 4,
    "replicas": 4,
    "conditions": [
        {
            "type": "Available",
            "status": "True",
            "reason": "AllReplicasReady",
            "message": "所有 4 个副本都就绪",
            "lastTransitionTime": "2024-08-20T10:00:00Z",
        }
    ],
    "endpoint": "test-cluster-api.default.svc.cluster.local:9000",
    "consoleEndpoint": "test-cluster-api.default.svc.cluster.local:9001",
    "version": "RELEASE.2024-08-17T01-10-17Z",
    "observedGeneration": 2,
}
```

### 4.3 更新 Status 的实现

Kopf 里更新 status 很简单，直接给 `patch.status` 字典赋值就行。

```python
# src/minio_operator/handlers/cluster.py
from datetime import datetime, timezone


def update_status(patch, actual, spec, logger):
    """根据实际状态更新 CR status"""
    replicas = spec["replicas"]
    ready = actual.get("ready_replicas", 0)

    # 判断 phase
    if not actual["exists"]:
        phase = "Creating"
    elif ready == 0:
        phase = "Failed"
    elif ready < replicas:
        phase = "Updating"
    else:
        phase = "Running"

    # 组装 conditions
    conditions = []
    if ready >= replicas:
        conditions.append({
            "type": "Available",
            "status": "True",
            "reason": "AllReplicasReady",
            "message": f"所有 {replicas} 个副本都就绪",
            "lastTransitionTime": datetime.now(timezone.utc).isoformat(),
        })
    else:
        conditions.append({
            "type": "Available",
            "status": "False",
            "reason": "NotAllReady",
            "message": f"就绪 {ready}/{replicas}",
            "lastTransitionTime": datetime.now(timezone.utc).isoformat(),
        })

    # 更新 status
    patch.status["phase"] = phase
    patch.status["readyReplicas"] = ready
    patch.status["replicas"] = replicas
    patch.status["conditions"] = conditions
    patch.status["endpoint"] = f"{patch['name']}-api.{patch['namespace']}.svc.cluster.local:9000"
    patch.status["version"] = spec["version"]
    patch.status["observedGeneration"] = patch["metadata"]["generation"]

    logger.info(f"状态更新: {phase} ({ready}/{replicas})")
```

> **Kopf 的 patch 对象**：这是 Kopf 提供的特殊字典，你往里填值，Kopf 会自动把它们 PATCH 到 K8s 的 CR 上。不需要手动调 API。

### 4.4 Status 子资源的调试

```bash
# 查看 CR 的 status 字段
kubectl get miniocluster test-cluster -o jsonpath='{.status}' | jq .
kubectl describe miniocluster test-cluster

# 快速看 phase
kubectl get mc test-cluster
# NAME            REPLICAS   READY   PHASE     AGE
# test-cluster    4          4       Running   5m
```

---

## 五、扩缩容与滚动升级

### 5.1 水平扩容（加节点）

MinIO 分布式集群支持**在线扩容**（加节点 + 加纠删码集），不需要重启。

```python
# src/minio_operator/handlers/cluster.py — 在 reconcile 中处理扩容

def handle_scale(name, namespace, spec, actual, logger):
    """处理扩缩容"""
    desired_replicas = spec["replicas"]
    current_replicas = actual["replicas"]

    if desired_replicas == current_replicas:
        return False

    if desired_replicas < current_replicas:
        # 缩容: MinIO 不支持缩容数据节点 (会丢数据)
        logger.error("MinIO 不支持缩容，请手动处理数据迁移后再操作")
        raise kopf.PermanentError(
            "MinIO distributed mode does not support scale-down. "
            "Data loss may occur."
        )

    # 扩容: 必须是纠删码集大小的整数倍
    # 默认纠删码集 = 4 节点
    ec_set_size = 4
    if desired_replicas % ec_set_size != 0:
        raise kopf.PermanentError(
            f"replicas 必须是 {ec_set_size} 的整数倍 (MinIO 纠删码集大小)"
        )

    logger.info(f"扩容: {current_replicas} → {desired_replicas}")

    # 1. 更新 StatefulSet replicas
    #    (StatefulSet 本身会按序加 Pod)
    apps_v1.patch_namespaced_stateful_set_scale(
        name=name,
        namespace=namespace,
        body={"spec": {"replicas": desired_replicas}},
    )

    # 2. 等 Pod 都起来后, 需要通知 MinIO 重新平衡数据
    #    (mc admin rebalance start 命令, 或调用 MinIO API)
    #    这步是异步的, 在后续 reconcile 里检查进度

    return True
```

**为什么不支持缩容？** MinIO 分布式模式下，数据是按纠删码集分布的，缩容意味着数据得重新分布，这个过程风险很大。官方推荐的是**只扩容不缩容**，真要缩就建新集群迁移数据。

### 5.2 滚动升级（版本更新）

StatefulSet 的 RollingUpdate 策略天然支持滚动升级，改 image 就行。但我们要加些保护。

```python
def handle_upgrade(name, namespace, spec, actual, logger):
    """处理版本升级"""
    desired_image = f"minio/minio:{spec['version']}"
    current_image = actual["image"]

    if desired_image == current_image:
        return False

    logger.info(f"升级版本: {current_image} → {desired_image}")

    # 安全检查: 升级前确保所有副本就绪
    if actual["ready_replicas"] < actual["replicas"]:
        raise kopf.TemporaryError(
            "不是所有副本都就绪，暂不升级", delay=30
        )

    # patch StatefulSet 的 image
    apps_v1.patch_namespaced_stateful_set(
        name=name,
        namespace=namespace,
        body={
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {"name": "minio", "image": desired_image}
                        ]
                    }
                }
            }
        },
    )

    # 更新 phase 为 Updating
    return True
```

**滚动升级保护机制**：

| 保护措施 | 作用 |
|:---|:---|
| 全部就绪才升级 | 避免本就不稳定的集群再升级 |
| `partition` 灰度升级 | StatefulSet 的 `rollingUpdate.partition` 可以只升序号 ≥ N 的 Pod，实现灰度 |
| 健康检查钩子 | `preStop` + `postStart` 做优雅停机和启动检查 |
| 升级速度控制 | `maxUnavailable` 控制同时停几个 |

### 5.3 灰度升级（分区升级）

```python
def canary_upgrade(name, namespace, desired_image, canary_count=1, logger):
    """
    灰度升级: 先升级最后 canary_count 个节点, 观察没问题再全量
    利用 StatefulSet 的 rollingUpdate.partition
    """
    partition = replicas - canary_count   # 只升级序号 >= partition 的 Pod
    apps_v1.patch_namespaced_stateful_set(
        name=name,
        namespace=namespace,
        body={
            "spec": {
                "updateStrategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate": {"partition": partition},
                },
                "template": {
                    "spec": {
                        "containers": [
                            {"name": "minio", "image": desired_image}
                        ]
                    }
                },
            }
        },
    )
    logger.info(f"灰度升级开始: partition={partition}, 先升 {canary_count} 个节点")
```

---

## 六、MinIO API 集成与子资源

### 6.1 MinIO Python SDK 封装

```python
# src/minio_operator/utils/minio.py
from minio import Minio
from minio.error import S3Error


class MinIOClient:
    """MinIO 管理 API 封装"""

    def __init__(self, endpoint, access_key, secret_key, secure=False):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    # ===== Bucket 管理 =====
    def create_bucket(self, bucket_name, object_lock=False):
        if self.client.bucket_exists(bucket_name):
            return False
        self.client.make_bucket(bucket_name, object_lock=object_lock)
        return True

    def delete_bucket(self, bucket_name):
        self.client.remove_bucket(bucket_name)

    def set_bucket_policy(self, bucket_name, policy_json):
        self.client.set_bucket_policy(bucket_name, policy_json)

    # ===== 用户管理 (admin API) =====
    def create_user(self, username, password):
        self.client.admin_user_add(username, password)

    def set_user_policy(self, username, policy_name):
        self.client.admin_policy_set(policy_name, user=username)

    def delete_user(self, username):
        self.client.admin_user_remove(username)

    # ===== 集群健康 =====
    def cluster_health(self):
        """集群健康状态"""
        try:
            # MinIO 健康检查
            health = self.client.cluster_health()
            return {
                "status": health.get("status"),
                "drives_total": health.get("drives", {}).get("total", 0),
                "drives_offline": health.get("drives", {}).get("offline", 0),
            }
        except Exception:
            return {"status": "unknown"}

    # ===== 数据再平衡 =====
    def rebalance_start(self):
        """启动数据再平衡 (扩容后用)"""
        return self.client.admin_rebalance_start()

    def rebalance_status(self):
        """再平衡进度"""
        return self.client.admin_rebalance_status()
```

### 6.2 MinIOBucket 子资源

定义一个子 CRD，让用户通过 K8s YAML 创建 Bucket。

```yaml
# CRD 片段 (MinIOBucket)
kind: CustomResourceDefinition
metadata:
  name: miniobuckets.storage.example.com
spec:
  group: storage.example.com
  names:
    kind: MinIOBucket
    plural: miniobuckets
  scope: Namespaced
  versions:
    - name: v1alpha1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [clusterRef, name]
              properties:
                clusterRef:        # 属于哪个 MinIOCluster
                  type: object
                  properties:
                    name: {type: string}
                    namespace: {type: string}
                name:               # Bucket 名称
                  type: string
                objectLock:
                  type: boolean
                  default: false
                policy:             # IAM policy JSON
                  type: string
                quota:              # 配额
                  type: string
            status:
              type: object
              x-kubernetes-preserve-unknown-fields: true
```

**处理器**：

```python
# src/minio_operator/handlers/bucket.py
import kopf
from ..utils.minio import MinIOClient
from ..utils.k8s import get_secret


@kopf.on.create("storage.example.com", "v1alpha1", "miniobuckets")
def create_bucket(spec, name, namespace, patch, logger, **kwargs):
    cluster_ref = spec["clusterRef"]
    cluster_name = cluster_ref["name"]
    cluster_ns = cluster_ref.get("namespace", namespace)

    # 1. 从 MinIOCluster 对应的 Secret 里取 root 凭据
    root_user, root_pass = get_minio_root_credentials(cluster_name, cluster_ns)
    endpoint = f"{cluster_name}-api.{cluster_ns}.svc.cluster.local:9000"

    # 2. 创建 MinIO 客户端
    mc = MinIOClient(endpoint, root_user, root_pass, secure=False)

    # 3. 创建 Bucket
    bucket_name = spec["name"]
    try:
        created = mc.create_bucket(bucket_name, spec.get("objectLock", False))
        if created:
            logger.info(f"Bucket {bucket_name} 创建成功")
        else:
            logger.info(f"Bucket {bucket_name} 已存在")
    except Exception as e:
        raise kopf.TemporaryError(f"创建 Bucket 失败: {e}", delay=30)

    # 4. 应用 Policy
    if spec.get("policy"):
        mc.set_bucket_policy(bucket_name, spec["policy"])

    # 5. 更新 status
    patch.status["state"] = "Ready"
    patch.status["bucketName"] = bucket_name
    patch.status["endpoint"] = endpoint


def get_minio_root_credentials(cluster_name, namespace):
    """从 MinIOCluster 关联的 Secret 获取 root 凭据"""
    # 这里简化处理: 约定 secret 名为 {cluster}-root-secret
    secret_name = f"{cluster_name}-root-secret"
    data = get_secret(secret_name, namespace)
    import base64
    user = base64.b64decode(data["MINIO_ROOT_USER"]).decode()
    password = base64.b64decode(data["MINIO_ROOT_PASSWORD"]).decode()
    return user, password
```

### 6.3 MinIOUser 子资源

```python
# src/minio_operator/handlers/user.py
import kopf
import base64
from ..utils.minio import MinIOClient
from ..utils.k8s import get_secret, create_secret


@kopf.on.create("storage.example.com", "v1alpha1", "miniousers")
def create_user(spec, name, namespace, patch, logger, **kwargs):
    cluster_ref = spec["clusterRef"]
    cluster_name = cluster_ref["name"]
    cluster_ns = cluster_ref.get("namespace", namespace)

    # 获取管理凭据
    root_user, root_pass = get_minio_root_credentials(cluster_name, cluster_ns)
    endpoint = f"{cluster_name}-api.{cluster_ns}.svc.cluster.local:9000"
    mc = MinIOClient(endpoint, root_user, root_pass, secure=False)

    username = spec.get("username", name)
    # 生成密码 (如果没指定)
    import secrets
    password = spec.get("password") or secrets.token_urlsafe(16)

    # 创建用户
    mc.create_user(username, password)

    # 附加 policy
    if spec.get("policy"):
        mc.set_user_policy(username, spec["policy"])

    # 把用户凭据存到 Secret
    secret_name = f"{name}-minio-credentials"
    create_secret(
        name=secret_name,
        namespace=namespace,
        data={
            "MINIO_ACCESS_KEY": base64.b64encode(username.encode()).decode(),
            "MINIO_SECRET_KEY": base64.b64encode(password.encode()).decode(),
        },
        labels={"minio-cluster": cluster_name},
    )

    patch.status["username"] = username
    patch.status["secretRef"] = secret_name
    patch.status["state"] = "Ready"
```

---

## 七、备份与故障自愈

### 7.1 定时备份

备份用 mc mirror / mc admin replicate 或者直接调 MinIO API。Operator 里用 CronJob 触发：

```python
# src/minio_operator/resources/backup.py
from kubernetes.client import (
    V1CronJob, V1ObjectMeta, V1CronJobSpec, V1JobTemplateSpec,
    V1PodTemplateSpec, V1PodSpec, V1Container, V1EnvVar,
)


def build_backup_cronjob(cluster_name, namespace, backup_spec):
    """生成备份 CronJob"""
    schedule = backup_spec.get("schedule", "0 2 * * *")
    target = backup_spec["target"]
    retention = backup_spec.get("retentionDays", 30)

    return V1CronJob(
        api_version="batch/v1",
        kind="CronJob",
        metadata=V1ObjectMeta(
            name=f"{cluster_name}-backup",
            namespace=namespace,
        ),
        spec=V1CronJobSpec(
            schedule=schedule,
            successful_jobs_history_limit=3,
            failed_jobs_history_limit=3,
            job_template=V1JobTemplateSpec(
                spec={
                    "template": V1PodTemplateSpec(
                        spec=V1PodSpec(
                            restart_policy="OnFailure",
                            containers=[
                                V1Container(
                                    name="backup",
                                    image="minio/mc:latest",
                                    command=["/bin/sh", "-c", """
                                        mc alias set local http://${CLUSTER}-api.${NAMESPACE}.svc.cluster.local:9000 \
                                            ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}
                                        mc alias set target ${TARGET} ${TARGET_ACCESS_KEY} ${TARGET_SECRET_KEY}
                                        mc mirror --overwrite --remove local/ target/${CLUSTER}/$(date +%Y%m%d)
                                        # 清理超过保留期的备份
                                        mc rm --recursive --force --older-than ${RETENTION}d target/${CLUSTER}/
                                    """.strip()],
                                    env=[
                                        V1EnvVar(name="CLUSTER", value=cluster_name),
                                        V1EnvVar(name="NAMESPACE", value=namespace),
                                        V1EnvVar(name="TARGET", value=target),
                                        V1EnvVar(name="RETENTION", value=str(retention)),
                                        # 从 Secret 取凭据
                                        {
                                            "name": "MINIO_ROOT_USER",
                                            "valueFrom": {
                                                "secretKeyRef": {
                                                    "name": f"{cluster_name}-root-secret",
                                                    "key": "MINIO_ROOT_USER",
                                                }
                                            },
                                        },
                                    ],
                                )
                            ],
                        )
                    )
                }
            ),
        ),
    )
```

### 7.2 故障自愈

Operator 检测到故障时自动修复。常见自愈场景：

| 故障 | 自愈方式 |
|:---|:---|
| Pod 挂了 | StatefulSet 自动拉起 (K8s 自带) |
| PVC 损坏 | 标记节点 + 剔除纠删码集 + 通知人工 |
| 配置漂移 | Reconcile 自动把资源改回去 |
| 节点宕机 | MinIO 自身纠删码保证可用性，Operator 告警 |
| 磁盘满了 | 触发扩容流程 / 告警 |

**故障检测 + 自愈示例**：

```python
def check_and_heal(name, namespace, logger):
    """检查集群健康并执行自愈"""
    # 1. 通过 MinIO API 获取集群健康
    mc = get_minio_client(name, namespace)
    health = mc.cluster_health()

    if health["status"] == "healthy":
        return False

    logger.warning(f"集群 {name} 不健康: {health}")

    # 2. 故障类型判断
    drives_offline = health.get("drives_offline", 0)

    if drives_offline > 0 and drives_offline < 4:
        # 少量磁盘离线: MinIO 自恢复 + 告警
        logger.warning(f"{drives_offline} 块盘离线, MinIO 仍可用")
        # 发告警 (Prometheus 指标 / webhook)
        trigger_alert(f"{name} 磁盘离线", drives_offline)
        return True

    if drives_offline >= 4:
        # 严重: 人工介入
        logger.error("严重故障: 超过纠删码容忍度, 需要人工介入")
        # 标记集群为 Degraded
        # 触发 PagerDuty / 钉钉 / 企业微信告警
        trigger_pagerduty(name, "CRITICAL", "MinIO cluster degraded")
        return True

    return False
```

---

## 八、监控与指标

### 8.1 MinIO 自带指标

MinIO 自带 Prometheus 指标端点：`/minio/v2/metrics/cluster`

```python
# 给 Service 加注解让 Prometheus 自动发现
def build_cluster_service(...):
    metadata = V1ObjectMeta(
        name=f"{name}-api",
        namespace=namespace,
        annotations={
            "prometheus.io/scrape": "true",
            "prometheus.io/port": "9000",
            "prometheus.io/path": "/minio/v2/metrics/cluster",
        },
        labels={"app": "minio", "minio-cluster": name},
    )
```

### 8.2 Operator 自身指标

Kopf 自带 `/metrics` 端点（Prometheus 格式），还可以加自定义指标：

```python
import kopf
from prometheus_client import Counter, Gauge

minio_clusters_total = Gauge(
    "minio_operator_clusters_total",
    "Total number of managed MinIO clusters",
)

minio_clusters_ready = Gauge(
    "minio_operator_clusters_ready",
    "Number of ready MinIO clusters",
)

reconcile_errors_total = Counter(
    "minio_operator_reconcile_errors_total",
    "Total reconcile errors",
    ["cluster"],
)


@kopf.on.startup()
async def startup(metrics_server, **kwargs):
    """启动时注册指标"""
    # Kopf 会自动挂指标服务到 8080/metrics
    pass
```

### 8.3 关键告警规则

```yaml
# PrometheusRule 示例
groups:
  - name: minio-operator
    rules:
      - alert: MinIOClusterNotReady
        expr: minio_operator_clusters_ready < minio_operator_clusters_total
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "MinIO 集群未全部就绪"

  - name: minio-cluster
    rules:
      - alert: MinIODriveOffline
        expr: minio_cluster_drives_offline > 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "MinIO 磁盘离线 ({{ $value }} 块)"

      - alert: MinIOClusterDegraded
        expr: minio_cluster_health_status != 1
        for: 5m
        labels:
          severity: critical

      - alert: MinIOStorageHighUsage
        expr: minio_cluster_storage_used_bytes / minio_cluster_storage_total_bytes > 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "存储使用率超过 85%"
```

---

## 九、RBAC 与部署

### 9.1 Operator 权限

Operator 需要的 K8s 权限清单：

```yaml
# config/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: minio-operator
  namespace: minio-operator-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: minio-operator
rules:
  # 自己的 CRD
  - apiGroups: ["storage.example.com"]
    resources: ["minioclusters", "miniousers", "miniobuckets"]
    verbs: ["get", "list", "watch", "patch", "update"]
  - apiGroups: ["storage.example.com"]
    resources:
      - "minioclusters/status"
      - "miniousers/status"
      - "miniobuckets/status"
    verbs: ["get", "patch", "update"]
  - apiGroups: ["storage.example.com"]
    resources: ["minioclusters/finalizers"]
    verbs: ["get", "update", "patch"]

  # 管理的资源
  - apiGroups: ["apps"]
    resources: ["statefulsets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["services", "configmaps", "secrets", "persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["batch"]
    resources: ["cronjobs", "jobs"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["pods", "pods/log", "events"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: minio-operator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: minio-operator
subjects:
  - kind: ServiceAccount
    name: minio-operator
    namespace: minio-operator-system
```

### 9.2 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 依赖
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 源码
COPY src/ ./src/

ENV PYTHONPATH=/app/src
ENV KOPF_NAMESPACE=""
ENV KOPF_CLUSTERWIDE=true

USER 65532:65532

ENTRYPOINT ["kopf", "run", "--standalone", "src/minio_operator/main.py"]
```

### 9.3 Operator Deployment

```yaml
# config/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio-operator
  namespace: minio-operator-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio-operator
  template:
    metadata:
      labels:
        app: minio-operator
    spec:
      serviceAccountName: minio-operator
      containers:
        - name: operator
          image: registry.example.com/minio-operator:v0.1.0
          args: ["--verbose"]
          ports:
            - name: metrics
              containerPort: 8080
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 30
```

---

## 十、测试与调试

### 10.1 本地调试

```bash
# 方式一: 本地直接跑 (需要 kubectl 权限)
export PYTHONPATH=src
kopf run src/minio_operator/main.py --verbose

# 方式二: 本地 Debug (VS Code)
# .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Kopf Operator",
      "type": "debugpy",
      "request": "launch",
      "module": "kopf",
      "args": ["run", "--verbose", "src/minio_operator/main.py"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src",
        "KOPF_NAMESPACE": "default"
      }
    }
  ]
}
```

### 10.2 单元测试

```python
# tests/test_cluster_handler.py
from unittest.mock import patch, MagicMock
from minio_operator.resources.statefulset import build_statefulset


def test_build_statefulset_basic():
    spec = {
        "replicas": 4,
        "version": "RELEASE.2024-08-17T01-10-17Z",
        "storage": {"size": "100Gi", "storageClass": "local-storage"},
    }
    sts = build_statefulset("test", "default", spec)

    assert sts.metadata.name == "test"
    assert sts.spec.replicas == 4
    assert len(sts.spec.volume_claim_templates) == 1
    assert sts.spec.template.spec.containers[0].image == "minio/minio:RELEASE.2024-08-17T01-10-17Z"


def test_build_statefulset_env():
    spec = {
        "replicas": 4,
        "version": "latest",
        "storage": {"size": "10Gi"},
        "env": [{"name": "MINIO_BROWSER", "value": "on"}],
        "security": {"rootUser": "admin", "rootPassword": "pass123456"},
    }
    sts = build_statefulset("test", "default", spec)
    env_names = [e.name for e in sts.spec.template.spec.containers[0].env]
    assert "MINIO_ROOT_USER" in env_names
    assert "MINIO_BROWSER" in env_names
```

### 10.3 E2E 测试

```bash
# 用 kind 起集群 → 装 CRD → 装 Operator → 创建 CR → 验证结果
# 推荐工具: pytest + pytest-kind / k3d

# 简化流程:
kind create cluster --name e2e
kubectl apply -f config/crd.yaml
kubectl apply -f config/rbac.yaml
kubectl apply -f config/deployment.yaml

# 等 Operator 起来
kubectl wait --for=condition=available deploy/minio-operator -n minio-operator-system --timeout=60s

# 创建测试集群
kubectl apply -f config/examples/miniocluster-sample.yaml

# 验证
kubectl wait --for=condition=available miniocluster/test-cluster --timeout=300s
kubectl get sts test-cluster
kubectl get mc test-cluster
```

---

## 十一、踩坑清单

| 坑 | 现象 | 解决 |
|:---|:---|:---|
| CRD 没开 status subresource | 写 status 失败 / 报 Forbidden | CRD 里加 `subresources.status: {}` |
| Kopf 版本和 K8s 版本不兼容 | 各种奇怪的 API 错误 | 看 Kopf 兼容性矩阵，升级/降级 |
| StatefulSet patch 失败 (422) | 某些字段 immutable (如 volumeClaimTemplates) | 不能改 PVC 大小和存储类，要改只能删了重建 |
| MinIO 扩容后数据不均衡 | 新节点空的，老节点满 | `mc admin rebalance start` 手动触发再平衡 |
| 缩容报错 / 数据丢失 | 用户改 replicas 为更小的值 | Operator 直接拒绝缩容 (PermanentError) |
| Reconcile 死循环 | patch status 又触发一次 update 事件 | 用 `observedGeneration` 防循环，或 daemon 模式（不受事件驱动） |
| Secret 被误删 | Operator 拿不到 root 密码 | ownerReferences 绑定到 CR，随 CR 生命周期 |
| 大量 CR 时 Operator OOM | 每个 CR 一个 daemon 协程，数量多了内存涨 | 调资源限制 / 用 timer 替代 daemon / 限制并发数 |
| Python GIL 影响性能 | 几千个 CR 时处理慢 | 用 async 处理器 + 单进程多协程，或者分片部署（按命名空间） |
| 升级时 StatefulSet rollingUpdate 不动 | partition 挡住了 | 检查 patch 里有没有把 partition 重置为 0 |

---

## 十二、扩展方向

### 12.1 可做的增强

- **Webhook 校验**：Kopf 支持 admission webhook，对 spec 做合法性校验（创建前就拒绝非法值）
- **多租户隔离**：每个命名空间的 Operator 实例，只能管自己命名空间的 CR
- **Tiered Storage**：支持热/冷分层，自动把冷数据迁到对象存储
- **ILM 生命周期**：通过 CR 配置 Bucket 的生命周期规则
- **Site Replication**：多站点复制，跨集群灾难恢复
- **Operator Framework 兼容**：打包成 OLM bundle，在 OperatorHub 发布

### 12.2 和官方 MinIO Operator 对比

| 对比项 | 官方 MinIO Operator | 自研 Kopf Operator |
|:---|:---|:---|
| 功能完整度 | 高 (官方维护) | 中 (按需实现) |
| 定制能力 | 弱 (只能用官方提供的字段) | 强 (想怎么改怎么改) |
| 维护成本 | 低 (升级就行) | 中 (自己养代码) |
| 内部系统集成 | 难 (要改源码) | 易 (直接写代码接 CMDB/监控/计费) |
| 语言 | Go | Python |
| 适用 | 标准需求 | 有定制需求的企业内部 |

> **建议**：如果官方 Operator 80% 满足需求，尽量用官方的，省下的精力花在业务上。只有当定制需求很多、改官方 Operator 成本高于自己写的时候，再考虑自研。

---

## 十三、速查表

### 13.1 Kopf 装饰器速查

| 装饰器 | 作用 | 场景 |
|:---|:---|:---|
| `@kopf.on.create` | CR 创建时触发 | 初始化资源 |
| `@kopf.on.update` | CR 更新时触发 | spec 变更处理 |
| `@kopf.on.delete` | CR 删除时触发 | 清理外部资源 |
| `@kopf.on.resume` | Operator 重启 / CR 已存在时 | 重入处理 (重要!) |
| `@kopf.on.field` | 某字段变化时触发 | 监听特定字段 |
| `@kopf.daemon` | 每个 CR 一个后台任务 | 持续 reconcile / 监控 |
| `@kopf.timer` | 每个 CR 一个定时器 | 周期性任务 |
| `@kopf.on.startup` | Operator 启动时 | 初始化全局资源 |
| `@kopf.on.cleanup` | Operator 退出时 | 清理 |
| `@kopf.index` | 建立内存索引 | 跨 CR 查询优化 |

### 13.2 常用异常类型

| 异常 | 效果 | 适用 |
|:---|:---|:---|
| `kopf.TemporaryError` | 会重试 (指数退避) | 临时故障 (网络超时 / 依赖没就绪) |
| `kopf.PermanentError` | 不再重试，标记失败 | 配置错误 / 不可能成功的操作 |
| `kopf.ObjectRetriableError` | 自定义重试延迟 | 指定 delay=30 秒后重试 |
| 普通 Exception | 默认当作 TemporaryError 重试 | 未捕获的异常 |

### 13.3 完整 CR 示例

```yaml
apiVersion: storage.example.com/v1alpha1
kind: MinIOCluster
metadata:
  name: data-lake
  namespace: data-platform
spec:
  replicas: 8
  version: RELEASE.2024-08-17T01-10-17Z
  storage:
    size: 2Ti
    storageClass: local-storage
  resources:
    requests:
      cpu: "4"
      memory: 16Gi
    limits:
      cpu: "16"
      memory: 64Gi
  security:
    rootUser: admin
    # rootPassword 实际建议用 secretRef
    rootPassword: super-secret-password
    tls: false
  env:
    - name: MINIO_BROWSER_REDIRECT_URL
      value: https://minio-console.example.com
  backup:
    enabled: true
    schedule: "0 2 * * *"
    target: s3.amazonaws.com/my-backup-bucket
    retentionDays: 30
```

### 13.4 开发命令速查

```bash
# 本地运行
export PYTHONPATH=src
kopf run src/minio_operator/main.py --verbose -n default

# 注册 CRD
kubectl apply -f config/crd.yaml

# 查看 CRD
kubectl get crd | grep minio
kubectl explain miniocluster

# 创建测试集群
kubectl apply -f config/examples/miniocluster-sample.yaml

# 查看状态
kubectl get mc -A
kubectl describe mc test-cluster
kubectl get mc test-cluster -o jsonpath='{.status.phase}'

# 看 Operator 日志
kubectl logs -f deploy/minio-operator -n minio-operator-system

# 删 CR
kubectl delete mc test-cluster

# 测试
pytest tests/ -v
black src/ tests/     # 格式化
ruff check src/        # lint
```

*最后更新: 2026-08-25*
