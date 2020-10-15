#### gitlab-ce-9.2.6升级到gitlab-ce-14.4.2

#### 升级方案
1. 备份！备份！备份
2. 升级预研测试
3. 实际环境升级
4. 注意

#### 备份
```yaml
# 自动创建数据备份文件到/var/opt/gitlab/backup目录下
gitlab-rake gitlab:backup:create
# 备份完成后将数据转存到其它服务器上
```

#### 升级预研测试
1. 找一台测试服务器，部署相同版本的gitlab，即gitlab-ce-9.2.6
2. 初始化gitlab并创建几个测试仓库
3. 由于gitlab不能跨大版本直接升级，所以需要先升级到当前最高版本，然后依次升级到下一个版本的最高版本
4. 下载各版本安装包，以centos7为例
   * gitlab-ce-9.5.9-ce.0.el7.x86_64.rpm
   * gitlab-ce-10.8.7-ce.0.el7.x86_64.rpm
   * gitlab-ce-11.11.8-ce.0.el7.x86_64.rpm
   * gitlab-ce-12.4.2-ce.0.el7.x86_64.rpm
5. 开始升级

```yaml
# 升级安装gitlab-ce-9.5.9
yum install gitlab-ce-9.5.9-ce.0.el7.x86_64.rpm
# 安装完成后，重新载入配置
gitlab-ctl reconfigure
# 查看组件状态
gitlab-ctl status
# 登录dashboard查看，如果显示500或者502，需要等待一会，部分组件未启动完成
# 确保仓库和之前相同，未出现异常才可进行下次升级

# 升级安装gitlab-ce-10.8.7
yum install gitlab-ce-10.8.7-ce.0.el7.x86_64.rpm
gitlab-ctl reconfigure
gitlab-ctl status
# 后续重复上面升级过程
```

#### 实际环境升级
按照预研测试方法升级  
注意：由于环境上的差异，可能在实际升级过程中出现和测试中不一样的情况，所以出现异常要查看是否影响了仓库，有无数据丢失，一旦出现问题，不可强行继续升级

#### 注意
* 每次升级后都要查看gitlab是否正常，数据和配置有没有异常
* 使用webhook需要在Admin Area >Setting >Network >Outbound requests 勾选"Allow requests to the local network from web hooks and services"选项
* 不使用CI/CD功能，关闭默认自动pipline，Admin Area >Setting >CI/CD 去勾"Default to Auto DevOps pipeline for all projects"