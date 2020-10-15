#### kubernetes中各资源类型yaml定义模板

#### Pod
```yaml
apiVersion: v1            //API版本
kind: pod                 //类型，pod
metadata:                 //元数据
  name: String            //元数据，pod的名字
  namespace: String       //元数据，pod的命名空间
  labels:                 //元数据，标签列表
    - name: String        //元数据，标签的名字
  annotations:            //元数据,自定义注解列表
    - name: String        //元数据,自定义注解名字
spec:                     //pod中容器的详细定义
  containers:             //pod中的容器列表，可以有多个容器
  - name: String          //Pod中容器名称
    image: String         //容器中的镜像
    imagesPullPolicy: IfNotPresent   //获取镜像的策略[Always|Never|IfNotPresent]
    command: [String]     //容器的启动命令列表（不配置的话使用镜像内部的命令）
    args: [String]        //启动参数列表
    workingDir: String    //容器的工作目录
    volumeMounts:         //挂载到到容器内部的存储卷设置
    - name: String
      mountPath: String
      readOnly: boolean
    ports:                //容器需要暴露的端口号列表
    - name: String
      containerPort: int  //容器要暴露的端口
      hostPort: int       //容器所在主机监听的端口（容器暴露端口映射到宿主机的端口）
      protocol: String
    env:                  //容器运行前要设置的环境变量列表
    - name: String
      value: String
    resources:            //容器运行资源限制
      limits:             //限制资源
        cpu: Srting       //单位为核，最小0.1
        memory: String    //单位为Mi、Gi
      requeste:           //请求资源
        cpu: String
        memory: String
    livenessProbe:         //容器健康检查的设置
      exec:                //通过命令的方式
        command: [String]
      httpGet:             //通过httpget检查健康
        path: String
        port: number
        host: String
        scheme: Srtring
        httpHeaders:
        - name: Stirng
          value: String 
      tcpSocket:           //通过tcpSocket检查健康
        port: number
      initialDelaySeconds: 0  //首次检查时间
      timeoutSeconds: 0     //检查超时时间
      periodSeconds: 0      //检查间隔时间
      successThreshold: 0
      failureThreshold: 0
      securityContext:      //安全配置
        privileged: falae
    restartPolicy: Never    //容器重启策略[Always|Never|OnFailure]
    nodeSelector: object    //负载节点选择
    imagePullSecrets:       //镜像pull时认证密钥(如果需要)
    - name: String
    hostNetwork: false      //是否使用主机网络模式，默认否
  volumes:                  //在该pod上定义共享存储卷
  - name: String
    meptyDir: {}            //支持多种类型卷emptyDir、nfs、local-volume、ceph
    hostPath:
      path: string
    secret:                 //类型为secret的存储卷
      secretName: String
      item:
      - key: String
        path: String
    configMap:              //类型为configMap的存储卷
      name: String
      items:
      - key: String
        path: String
```
###### 一般情况下我们不会直接定义Pod来使用，基本都要配合编排来创建应用，但Pod模板部分配置依旧时按照上述情况配置的，下面给出一个经典的nginx应用Pod简化配置：
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
    version: v1.16
spec:
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
```
#### Service
```yaml
apiVersion: v1
kind: Service
metadata:           //服务元数据信息，与Pod定义一样
  name: nginx
  labels:
    app: nginx
    version: v1
spec:
  ports:            //配置对应容器端口组
  - port: 80
    name: http
  - port: 443
    name: https
  type: ClusterIP   //定义服务对外暴露的方式[ClusterIP,NodePort,LoadBalancer]
  selector:         //选择对应Pod所拥有的label
    app: nginx
```
#### PV
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv01
spec:  
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  nfs:
    path: /nfsshare
    server: 172.17.100.23
```
#### PVC
```yaml
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: pvc01
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
```
#### Deployment
###### 通用定义：
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
        version: v1.16
    spec:
      containers:
      - name: nginx
        image: nginx
        imagePullPolicy: IfNotPresent
        resources:
          limits:
            cpu: 1
            memory: 2Gi
          requests:
            cpu: 100m
            memory: 200Mi
        ports:
        - containerPort: 80
```
#### 挂载持久卷
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
        version: v1.16
    spec:
      containers:
      - name: nginx
        image: nginx
        imagePullPolicy: IfNotPresent
        resources:
          limits:
            cpu: 1
            memory: 2Gi
          requests:
            cpu: 100m
            memory: 200Mi
        ports:
        - containerPort: 80
        volumeMounts:
        - mountPath: /usr/share/nginx/html
          name: html
      volumes:
      - name: html
        persistentVolumeClaim:
          claimName: pvc01
```
#### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cm-jdbcproperties
data:
  key-jdbcproperties: |
    JDBC_DRIVER_CLASS_NAME=com.mysql.jdbc.Driver
    JDBC_URL=jdbc:mysql://localhost:3306/bz_argon?useUnicode=true&characterEncoding=utf8
    JDBC_USER_NAME=root
    JDBC_PASSWORD=maojiancai
    JDBC_INITIALSIZE=10
    JDBC_MAXACTIVE=20
    JDBC_MAXIDLE=20
    JDBC_MINIDLE=10
    JDBC_MAXWAIT=60000
    JDBC_VALIDATIONQUERY=SELECT 1 FROM DUAL
    JDBC_TESTONBORROW=false
    JDBC_TESTONRETURN=false
    JDBC_TESTWHILEIDLE=true
    JDBC_TIMEBETWEENEVICTIONRUNSMILLIS=6000
    JDBC_MINEVICTABLEIDLETIMEMILLIS=25200000
    JDBC_REMOVEABANDONED=true
    JDBC_REMOVEABANDONEDTIMEOUT=1800
    JDBC_LOGABANDONED=true
```
#### StatefulSet
```yaml
apiVersion: apps/v1beta2
kind: StatefulSet
metadata:
  name: ags
  labels:
    app: arcgisserver
    version: v1
spec:
  serviceName: server
  replicas: 2
  selector:
    matchLabels:
      app: arcgisserver
      version: v1
  template:
    metadata:
      labels:
        app: arcgisserver
        version: v1
    spec:
      containers:
      - name: ags
        image: 192.168.199.205:80/arcgis/ags:1071-noagent-v1
        resources:
          limits:
            cpu: 4
            memory: 8Gi
          requests:
            cpu: 100m
            memory: 2Gi
        ports:
        - containerPort: 6443
          name: https
        - containerPort: 6080
          name: http
        env:
        - name: "ECPPATH"
          value: "/opt/server.ecp"
        volumeMounts:
        - mountPath: /gisdata
          name: server
        - mountPath: /opt
          name: key
      volumes:
        - name: server
          persistentVolumeClaim:
            claimName: server
        - name: key
          secret:
            secretName: agskey
```
#### HPC
```yaml
apiVersion: autoscaling/v1
kind: HorizaontalPodAutoscaler
metadata:
  name: php-apache
spec:
  scaleTargetRef:
    apiVersion: v1
    kind: Deployment
    name: php-apache
  minReplicas: 1
  maxrReplicas: 10
  targetCPUUtilizationPercentage: 50
```
