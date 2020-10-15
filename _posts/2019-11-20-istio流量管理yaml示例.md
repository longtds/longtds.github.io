#### destination rule、virtual service、subset、gateway

### destionationrule（服务注册）
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: productpage   # 注册的服务名称
spec:
  host: productpage   # kubernetes下对应的service
  subsets:            # 关联pod中version标签
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
  - name: v3
    labels:
      version: v3
# 查看destinationrules
wangw@DESKTOP:~$ kubectl get destinationrules -n istio-sample
NAME          HOST          AGE
details       details       10m
productpage   productpage   10m
ratings       ratings       10m
reviews       reviews       10m
```
### virtualservice（流量管理）
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: productpage    # 定义virtualservice名称
spec:
  hosts:
  - productpage        # kubernetes下service
  http:
  - route:
    - destination:
        host: productpage    # 已注册到istio的服务
        subset: v1           # 已注册服务中的subsets版本
# 查看virtualservice
wangw@DESKTOP:~$ kubectl get virtualservice -n istio-sample
NAME          GATEWAYS             HOSTS           AGE
bookinfo      [bookinfo-gateway]   [*]             17m
details                            [details]       16m
productpage                        [productpage]   16m
ratings                            [ratings]       16m
reviews                            [reviews]       16m
```
### gateway（流量入口）
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway  # 网关名称
spec:
  selector:
    istio: ingressgateway # 使用istio提供的ingress控制器
  servers:
  - port:
      number: 80          # 网关使用的端口
      name: http  
      protocol: HTTP      # 网络协议，支持http和https
    hosts:                # 定义网关用于访问的地址，可以是ip或者域名
    - "*"                 # *代表可用任何方式访问
# 查看gateway
wangw@DESKTOP:~$ kubectl get gateway -n istio-sample
NAME               AGE
bookinfo-gateway   23m
```
### 服务路由（配置服务在网关上的路由）
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "*"                     # 访问地址，这里允许任何方式
  gateways:
  - bookinfo-gateway        # 选择网关
  http:
  - match:                    # 定义服务匹配模式
    - uri:                    # 以uri的方式
        exact: /productpage   # exact代表绝对路径，只能匹配定义的字段
    - uri:
        prefix: /static       # prefix代表前缀，可以匹配到二级子目录上
    - uri:
        exact: /login
    - uri:
        exact: /logout
    - uri:
        prefix: /api/v1/products
    route:                    # 选择路由的服务        
    - destination:
        host: productpage     # 已注册istio服务
        port:
          number: 9080
# 查找istio-ingressgateway地址
wangw@DESKTOP:~$  kubectl get service istio-ingressgateway -n istio-system
NAME                   TYPE           CLUSTER-IP      EXTERNAL-IP       PORT(S)         AGE
istio-ingressgateway   LoadBalancer   10.43.138.125   192.168.199.140   80:32047/TCP,443:31406/TCP  17h
# 访问bookinfo
wangw@DESKTOP:~$ curl http://192.168.199.140/productpage -I
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8
content-length: 4183
server: istio-envoy
date: Wed, 20 Nov 2019 02:38:45 GMT
x-envoy-upstream-service-time: 30
# 验证prefix子路径支持
wangw@DESKTOP:~$ curl http://192.168.199.140/static/jquery.min.js -I
HTTP/1.1 200 OK
content-length: 84380
content-type: application/javascript
last-modified: Tue, 19 Mar 2019 18:04:24 GMT
cache-control: public, max-age=43200
expires: Wed, 20 Nov 2019 14:40:06 GMT
etag: "1553018664.0-84380-810225459"
date: Wed, 20 Nov 2019 02:40:06 GMT
accept-ranges: bytes
server: istio-envoy
x-envoy-upstream-service-time: 6
```
### 基于http header的服务访问控制
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - match:
    - headers:
        end-user:    # 如果请求header中有"end-user"，并且值为"jason"，就匹配此规则
          exact: jason
    route:
    - destination:   # 满足请求header条件后，流量导向到reviews的v2版本上
        host: reviews
        subset: v2
  - route:
    - destination:   # 普通请求流量导向到reviews的v3版本上
        host: reviews
        subset: v3
```
### 故障注入（测试微服务弹性）
#### 注入HTTP延迟故障
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: ratings
  ...
spec:
  hosts:
  - ratings
  http:
  - fault:     # 定义了一个7s延时的故障,实际上是sidecar将请求hold住了，
      delay:   # 时间一到请求转发到ratings服务，对原有服务没任何影响
        fixedDelay: 7s
        percentage:
          value: 100
    match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: ratings
        subset: v1
  - route:
    - destination:
        host: ratings
        subset: v1
```
#### 注入HTTP abort故障
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: ratings
  ...
spec:
  hosts:
  - ratings
  http:
  - fault:     # sidecar在遇到end-user:jason请求时，直接返回500，不会将流量发送到ratings
      abort:
        httpStatus: 500
        percentage:
          value: 100
    match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: ratings
        subset: v1
  - route:
    - destination:
        host: ratings
        subset: v1
```
### 流量转移
#### 基于权重的路由
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
  ...
spec:
  hosts:
  - reviews
  http:
  - route:      # 50%流量到v1，50%流量到v3
    - destination:
        host: reviews
        subset: v1
      weight: 50
    - destination:
        host: reviews
        subset: v3
      weight: 50
```
### 请求超时
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v2
    timeout: 0.5s       # 真实应用响应超过这个值，则sidecar判断为超时，返回5xx响应
```
### 熔断（限制并发）
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: httpbin
spec:
  host: httpbin
  trafficPolicy:                        # 流量传输策略
    connectionPool:                     # 定义链接池
      tcp:                              # tcp连接
        maxConnections: 1               # 最大连接数
      http:                             # http连接
        http1MaxPendingRequests: 1      # 最大Pending请求数
        maxRequestsPerConnection: 1     # 每个连接最大请求数
    outlierDetection:                   # 检测配置
      consecutiveErrors: 1
      interval: 1s
      baseEjectionTime: 3m
      maxEjectionPercent: 100
# 测试2并20请求
wangw@DESKTOP:~$ kubectl exec -n istio-sample -it $FORTIO_POD  -c fortio /usr/bin/fortio -- load  -c 2 -qps 0 -n 20 \
-loglevel Warning http://httpbin:8000/get
05:29:53 I logger.go:97> Log level is now 3 Warning (was 2 Info)
Fortio 1.3.1 running at 0 queries per second, 32->32 procs, for 20 calls: http://httpbin:8000/get
Starting at max qps with 2 thread(s) [gomax 32] for exactly 20 calls (10 per thread + 0)
Ended after 41.76631ms : 20 calls. qps=478.85
Aggregated Function Time : count 20 avg 0.0040754377 +/- 0.0007991 min 0.00322531 max 0.006563978 sum 0.081508754
# range, mid point, percentile, count
>= 0.00322531 <= 0.004 , 0.00361266 , 70.00, 14
> 0.004 <= 0.005 , 0.0045 , 90.00, 4
> 0.005 <= 0.006 , 0.0055 , 95.00, 1
> 0.006 <= 0.00656398 , 0.00628199 , 100.00, 1
# target 50% 0.00376163
# target 75% 0.00425
# target 90% 0.005
# target 99% 0.00645118
# target 99.9% 0.0065527
Sockets used: 2 (for perfect keepalive, would be 2)
Code 200 : 20 (100.0 %)                # 这里可以看到，所有请求都通过了,说明Istio-proxy 允许存在一些误差。
Response Header Sizes : count 20 avg 230 +/- 0 min 230 max 230 sum 4600
Response Body/Total Sizes : count 20 avg 601 +/- 0 min 601 max 601 sum 12020
All done 20 calls (plus 0 warmup) 4.075 ms avg, 478.9 qps
# 测试3并发30请求
wangw@DESKTOP:~$ kubectl exec -n istio-sample -it $FORTIO_POD  -c fortio /usr/bin/fortio -- load  -c 3 -qps 0 -n 30 \
-loglevel Warning http://httpbin:8000/get
05:30:09 I logger.go:97> Log level is now 3 Warning (was 2 Info)
Fortio 1.3.1 running at 0 queries per second, 32->32 procs, for 30 calls: http://httpbin:8000/get
Starting at max qps with 3 thread(s) [gomax 32] for exactly 30 calls (10 per thread + 0)
05:30:09 W http_client.go:679> Parsed non ok code 503 (HTTP/1.1 503)
05:30:09 W http_client.go:679> Parsed non ok code 503 (HTTP/1.1 503)
05:30:09 W http_client.go:679> Parsed non ok code 503 (HTTP/1.1 503)
05:30:09 W http_client.go:679> Parsed non ok code 503 (HTTP/1.1 503)
05:30:09 W http_client.go:679> Parsed non ok code 503 (HTTP/1.1 503)
05:30:09 W http_client.go:679> Parsed non ok code 503 (HTTP/1.1 503)
05:30:09 W http_client.go:679> Parsed non ok code 503 (HTTP/1.1 503)
05:30:09 W http_client.go:679> Parsed non ok code 503 (HTTP/1.1 503)
05:30:09 W http_client.go:679> Parsed non ok code 503 (HTTP/1.1 503)
05:30:09 W http_client.go:679> Parsed non ok code 503 (HTTP/1.1 503)
Ended after 81.134688ms : 30 calls. qps=369.76
Aggregated Function Time : count 30 avg 0.0056269946 +/- 0.005095 min 0.0003608 max 0.021076954 sum 0.168809838
# range, mid point, percentile, count
>= 0.0003608 <= 0.001 , 0.0006804 , 33.33, 10
> 0.005 <= 0.006 , 0.0055 , 53.33, 6
> 0.006 <= 0.007 , 0.0065 , 73.33, 6
> 0.007 <= 0.008 , 0.0075 , 86.67, 4
> 0.008 <= 0.009 , 0.0085 , 90.00, 1
> 0.012 <= 0.014 , 0.013 , 93.33, 1
> 0.02 <= 0.021077 , 0.0205385 , 100.00, 2
# target 50% 0.00583333
# target 75% 0.007125
# target 90% 0.009
# target 99% 0.0209154
# target 99.9% 0.0210608
Sockets used: 12 (for perfect keepalive, would be 3)
Code 200 : 20 (66.7 %)            # 熔断行为按照之前的设计生效了，只有 66.7% 的请求获得通过，剩余请求被断路器拦截了
Code 503 : 10 (33.3 %)
Response Header Sizes : count 30 avg 153.43333 +/- 108.5 min 0 max 231 sum 4603
Response Body/Total Sizes : count 30 avg 481.1 +/- 169.8 min 241 max 602 sum 14433
All done 30 calls (plus 0 warmup) 5.627 ms avg, 369.8 qps
```
### 流量镜像
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: httpbin
spec:
  hosts:
    - httpbin
  http:
  - route:
    - destination:    # 此路由规则将100％的流量发送到v1
        host: httpbin
        subset: v1
      weight: 100
    mirror:           #指定镜像到httpbin:v2服务
      host: httpbin
      subset: v2
# 当流量被镜像时，请求将通过其主机/授权报头发送到镜像服务附上 -shadow。例如，将cluster-1变为cluster-1-shadow
# 这些被镜像的请求是“即发即弃”的，也就是说这些请求引发的响应是会被丢弃的
```
### 边缘流量控制（Ingress Gateway）
#### 通过自动挂载文件模式
```yaml
1: 生成证书
2: 在istio-system下创建证书secret，名称只能使用istio-ingressgateway-certs，创建后会 \
自动挂载到istio-ingressgateway容器/etc/istio/istio-ingressgateway-certs目录下
kubectl create secret -n istio-system tls istio-ingressgateway-certs \
--key privkey1.pem --cert fullchain1.pem
3: 查看文件挂载情况
wangw@DESKTOP:$ kubectl exec -it -n istio-system $(kubectl -n istio-system get pods -l istio=ingressgateway \
-o jsonpath='{.items[0].metadata.name}') -- ls -al /etc/istio/ingressgateway-certs
total 0
drwxrwxrwt 3 root root 120 Nov 21 06:08 .
drwxr-xr-x 1 root root  78 Nov 21 06:04 ..
drwxr-xr-x 2 root root  80 Nov 21 06:08 ..2019_11_21_06_08_28.453045493
lrwxrwxrwx 1 root root  31 Nov 21 06:08 ..data -> ..2019_11_21_06_08_28.453045493
lrwxrwxrwx 1 root root  14 Nov 21 06:08 tls.crt -> ..data/tls.crt
lrwxrwxrwx 1 root root  14 Nov 21 06:08 tls.key -> ..data/tls.key
4: 修改网关配置
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  servers:
    - hosts:
        - '*'
      port:
        name: https
        number: 443
        protocol: HTTPS
      tls:
        mode: SIMPLE
        privateKey: /etc/istio/ingressgateway-certs/tls.key
        serverCertificate: /etc/istio/ingressgateway-certs/tls.crt
  selector:
    istio: ingressgateway
5: 请求网关（使用证书中的域名访问）
wangw@DESKTOP:~$ curl -I https://bookinfo.gisuni.dev/productpage
HTTP/2 200
content-type: text/html; charset=utf-8
content-length: 4183
server: istio-envoy
date: Thu, 21 Nov 2019 07:17:27 GMT
x-envoy-upstream-service-time: 37
```
#### 通过SDS为Gateway提供HTTPS加密支持
创建Ingress Gateway代理，通过SDS获取secret中的证书。  
Ingress Gateway代理和Ingress Gateway在同一个Pod中运行，监视Ingress Gateway所在命名空间中新建的Secret  
```yaml
# 重新生成ingress gateway配置
istioctl manifest generate \
--set values.gateways.istio-egressgateway.enabled=false \
--set values.gateways.istio-ingressgateway.sds.enabled=true > \
$HOME/istio-ingressgateway.yaml
# 应用新配置
kubectl apply -n istio-system -f $HOME/istio-ingressgateway.yaml
```
创建新的证书secret,并修改gateway引用证书
```yaml
# 创建名称为gistack-org的证书secret
kubectl create -n istio-system secret tls gisstack-org \
--key privkey1.pem --cert fullchain1.pem
# 修改gateway配置
kind: Gateway
apiVersion: networking.istio.io/v1alpha3
metadata:
  name: bookinfo-gateway
spec:
  servers:
    - hosts:
        - '*'
      port:
        name: https
        number: 443
        protocol: HTTPS
      tls:
        mode: SIMPLE                     # 单向认证，MUTUAL为双向认证
        credentialName: "gisstack-org"   # 此处直接指定证书secret名称
  selector:
    istio: ingressgateway
```
访问
```yaml
wangw@DESKTOP:~$ curl -I https://bookinfo.gisstack.org/productpage
HTTP/2 200
content-type: text/html; charset=utf-8
content-length: 4183
server: istio-envoy
date: Thu, 21 Nov 2019 07:43:44 GMT
x-envoy-upstream-service-time: 39
```
配置多个主机名
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: mygateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https-httpbin
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: "httpbin-credential"
    hosts:
    - "httpbin.example.com"
  - port:
      number: 443
      name: https-helloworld
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: "helloworld-credential"
    hosts:
    - "helloworld-v1.example.com"
```
#### 配置直通模式（直接认证后端应用的证书）
```yaml
# 网关
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: mygateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: PASSTHROUGH   # 直通模式不需要配置证书，网关按原样传递入口流量,不终止TLS
    hosts:
    - nginx.example.com
# 路由
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: nginx
spec:
  hosts:
  - nginx.example.com
  gateways:
  - mygateway
  tls:
  - match:
    - port: 443
      sni_hosts:          # 指定sni主机名
      - nginx.example.com
    route:
    - destination:
        host: my-nginx
        port:
          number: 443
```
### Egress流量
#### 引入外部服务
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: ServiceEntry          # 通过ServiceEntry创建外部服务代理（相当于注册到istio）
metadata:
  name: httpbin
spec:
  hosts:
  - httpbin.org          # 外部服务地址
  ports:
  - number: 443
    name: https
    protocol: HTTPS
  resolution: DNS
  location: MESH_EXTERNAL
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService        # 配置外部服务路由
metadata:
  name: httpbin
spec:
  hosts:
  - httpbin.org
  tls:
  - match:
    - port: 443
      sni_hosts:            # 指定通过SNI方式访问tls
      - httpbin.org
    route:
    - destination:
        host: httpbin.org
        port:
          number: 443
      weight: 100
```
#### 管理外部服务
```yaml
# 与网格内流量配置方法相同
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: httpbin-ext
spec:
  hosts:
    - httpbin.org
  http:
  - timeout: 3s
    route:
      - destination:
          host: httpbin.org
        weight: 100
```