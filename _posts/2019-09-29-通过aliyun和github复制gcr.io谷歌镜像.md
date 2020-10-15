前置条件：

1.  注册阿里云账户

2.  注册github账户

github准备：

1.  创建任意仓库，比如docker

2.  在仓库下创建镜像名称文件夹，比如，heapster

3.  在heapster下创建Dockerfile文件，内容如下：

FROM k8s.gcr.io/heapster-amd64:v1.6.0-beta.1

![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/7d7892faeec06dfcada7184b5b63ab77.png)

阿里云操作：

1.  进入容器镜像服务

2.  创建镜像仓库

![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/19b59005767ee34cb7e7e1f7eba3cb94.png)

1.  选择github作为代码源并配置使用的仓库，勾选海外机器构建

![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/75af352b986514c1b96505fa3eb4608e.png)

1.  点击heapster管理按钮，选择左侧构建

![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/3e90f0eee0a79d7b3cefcb3de3b85211.png)

1.  在构建规则设置中点击添加规则，选择对应镜像目录，镜像版本要与Dockerfile中一致

![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/d929277b15fd709b357a37b6492496a2.png)

1.  在创建的规则下点击立即构建，查看构建日志是否成功

![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/99315f18a8635680c0f201ea5339d63c.png)

![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/c78819403dadef888b92115ec70d9389.png)

1.  成功将谷歌容器镜像复制到阿里云，查看镜像基本信息获取镜像地址

![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/606812cfe8b7850a57645c7cb11a7094.png)

镜像pull测试：

![clipboard.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/b98f8c9f7899a9505e8fffa09681dbea.png)
