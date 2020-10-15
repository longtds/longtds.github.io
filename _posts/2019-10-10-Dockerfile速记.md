#### Dockerfile常用指令及注意点

#### FROM 引用镜像
```dockerfile
FROM Centos7
```
#### RUN 执行镜像环境下的命令,尽量使用&&连接多个命令以减少镜像层
```dockerfile
RUN yum makecache && yum install net-tools && yum clean all
```
#### COPY 拷贝文件到镜像
```dockerfile
COPY ./package.json /app/
```
此文件并非从本地拷贝，而是在docker build时生成的上下文中,比如：
```sh
$ docker build -t nginx:v3 .
Sending build context to Docker daemon 2.048 kB
```
#### ADD 拷贝文件到镜像,与COPY的区别在于自动解压tar压缩包，支持url拷贝
```dockerfile
ADD test.tar.gz /tmp/
ADD http://test.com/q.tar.gz /tmp/

```
#### CMD 指定容器默认启动命令
```dockerfile
# shell
CMD tail -f /var/log/messages
# exec
CMD [ "sh", "-c", "tail -f /var/log/messages" ]
```
#### ENTRYPOINT 启动容器命令
```dockerfile
ENTRYPOINT [ "curl", "-s", "https://ip.cn" ]
```
ENTRYPOINT可以接受用户输入的CMD或者Dockerfile中的CMD做为参数运行，比如：  
```dockerfile
# 用户输入 -i,相当于执行 curl -s https://ip.cn -i
docker run mypod -i
# Dockerfile中加CMD,相当于执行docker-entrypoint.sh redis-server
ENTRYPOINT [ "docker-entrypoint.sh" ]
CMD [ "redis-server" ]
```
#### ENV 设置环境变量(容器运行时还存在)
```dockerfile
# 通过=指定，一行可多个
ENV VERSION=1.0
# 单个
ENV NODE_VERSION v8.2.0
```
#### ARG 与ENV类似（仅服务于构建）
#### VOLUME 定义匿名存储卷
```dockerfile
VOLUME ["<路径1>", "<路径2>"...]
VOLUME /data
```
在运行时如果用户不指定挂载，其应用也可以正常运行，不会向容器存储层写入大量数据，  
这里的 /data 目录就会在运行时自动挂载为匿名卷，任何向 /data 中写入的信息都不会  
记录进容器存储层，从而保证了容器存储层的无状态化。
#### EXPOSE 暴露端口
```dockerfile
EXPOSE 80 8080 443
```
#### WORKDIR 指定运行目录
```dockerfile
WORKDIR /app
CMD startup.sh
```
容器启动后，当前目录在/app下，执行/app下的startup.sh文件
#### USER 指定当前用户
```dockerfile
USER arcgis
CMD start-arcgis.sh
```
容器启动后以arcgis用户运行start-arcgis.sh
#### HEALTHCHECK 健康检查
```dockerfile
HEALTHCHECK [选项] CMD <命令>：设置检查容器健康状况的命令
HEALTHCHECK 支持下列选项：
--interval=<间隔>：两次健康检查的间隔，默认为 30 秒；
--timeout=<时长>：健康检查命令运行超时时间，如果超过这个时间，本次健康检查就被视为失败，默认 30 秒；
--retries=<次数>：当连续失败指定次数后，则将容器状态视为 unhealthy，默认 3 次.
```
例子：
```dockerfile
FROM nginx
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
HEALTHCHECK --interval=5s --timeout=3s \
  CMD curl -fs http://localhost/ || exit 1
```
每隔5秒请求80端口服务，3s超时