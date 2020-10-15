#### 相关词：kubernetes、operator、云原生、kubebuilder

### kubernetes operator能干什么
* 扩展了kubernetes功能
* 更快速的交付复杂应用
* 更好的管理有状态应用
* 组件升级、节点恢复、调整集群规模

### operator是什么
kubernetes其实是一个期望管理器，我们定义一个应用yaml文件，制定了我们期望用到的镜像、规格、磁盘空间、实例数等，然后kubernetes就会尝试把应用维持在这种状态下。  
kubernetes主要通过controller-manager组件来调和应用达到期望状态：  
![img.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/7a58e38f8329ac2a7f044cae176e76ff.png)

如果我们自己实现了类似controller-manager的功能，这就叫做kubernetes的operator，我们称之为Custom Controller。创建的应用被定义为Kubernetes对象：Custom Resource（CR），它包含yaml spec和被API服务接受对象类型（K8s kind）。虽然Operator controller主要使用自定义组件，但它与原生Kubernetes controller协调方式非常类似。  

![img2.png](https://raw.githubusercontent.com/longtds/longtds.github.io/master/_posts/media/16931404-c245c24a5d766d06.png)
### operator工具
* operator-sdk
* kubebuilder

operator-sdk支持三种方式构建operator，即：golang、ansible、helm  
kubebuilder目前仅支持golang构建  
