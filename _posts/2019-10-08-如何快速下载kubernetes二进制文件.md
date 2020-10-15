#### 如何快速下载kubernetes安装包

##### 首先，浏览器访问到github上kubernetes项目主页:
```http
https://github.com/kubernetes/kubernetes
``` 
##### 然后选择对应版本的CHANGELOG-1.X.md文件，点击打开,找到对应二级制发行版比如:
```http
kubernetes-server-linux-amd64.tar.gz
```
##### 其链接地址为:
```http
https://dl.k8s.io/v1.15.0/kubernetes-server-linux-amd64.tar.gz
```
##### 国内无法下载到，将其中dl.k8s.io修改为:
```
storage.googleapis.com/kubernetes-release/release
```  
##### 新的下载地址：
```http
https://storage.googleapis.com/kubernetes-release/release/v1.15.0/kubernetes-server-linux-amd64.tar.gz
```