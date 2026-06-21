# Spark

## Spark 架构

Spark 采用 Master/Worker 架构，Driver 负责任务调度，Executor 执行计算。

## Spark on K8s

```bash
# Spark Operator 部署
helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
helm install spark-operator spark-operator/spark-operator --namespace spark

# 提交 Spark 任务到 K8s
cat <<EOF | kubectl apply -f -
apiVersion: "sparkoperator.k8s.io/v1beta2"
kind: SparkApplication
metadata:
  name: spark-pi
  namespace: default
spec:
  type: Scala
  mode: cluster
  image: spark:3.5.0
  mainClass: org.apache.spark.examples.SparkPi
  mainApplicationFile: "local:///opt/spark/examples/jars/spark-examples.jar"
  sparkConf:
    spark.kubernetes.driverEnv.SPARK_USER: "spark"
  driver:
    cores: 1
    coreLimit: "1200m"
    memory: "512m"
    serviceAccount: spark
  executor:
    instances: 3
    cores: 1
    coreLimit: "1200m"
    memory: "512m"
EOF
```

## Spark SQL 优化

```python
# 关键配置
spark.conf.set("spark.sql.adaptive.enabled", "true")       # AQE
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.shuffle.partitions", "200")      # 调节

# 缓存
df.cache()
df.createOrReplaceTempView("cached_table")
```
