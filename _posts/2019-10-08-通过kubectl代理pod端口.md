#### 使用kubectl客户端代理pod端口

```sh
$ kubectl port-forward -n <namespace> <podname> <local_port>:<pod_port>
```
#### 通过保留端口查看应用状态，比如：
```sh
kubectl port-forward -n istio-system istio-pilot-76b76778dd-bbnf9 9875:9876
```
将istio-system下的istio-pilot-76b76778dd-bbnf9端口9876代理到本地9875上，通过浏览器访问http://localhost:9875