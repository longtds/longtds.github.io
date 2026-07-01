<!-- news-meta
created_by: generate_daily_news.py
date: 2026-06-30T19:00:00+08:00
source: CNCF Blog
domain: AI 基础设施
url: https://www.cncf.io/blog/2026/06/30/dragonfly-v2-5-0-is-released/
content_mode: full-translated
original_language: non-zh
extraction_status: wordpress-api
-->

# 蜻蜓 v2.5.0 发布

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-06-30 19:00 CST |
| 领域 | AI 基础设施 |
| 来源 | CNCF Blog |
| 原文标题 | Dragonfly v2.5.0 is released |
| 原文 | [打开原文](https://www.cncf.io/blog/2026/06/30/dragonfly-v2-5-0-is-released/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | wordpress-api |

## 摘要

Dragonfly v2.5.0 is released!感谢所有促成 Dragonfly 版本发布的贡献者。新功能和增强功能 从 Hugging Face 和 ModelScope 直接存储库下载 Dragonfly 客户端现在支持直接下载模型存储库...

## 正文

Dragonfly v2.5.0 发布了！

感谢所有促成 [Dragonfly](https://d7y.io/) 版本发布的[贡献者](https://github.com/dragonflyoss/dragonfly/graphs/contributors)。

### 新功能和增强功能

#### 从 Hugging Face 和 ModelScope 直接存储库下载

Dragonfly 客户端现在支持直接从 Hugging Face 和 ModelScope 下载模型存储库。用户可以运行“dfget hf://deepseek-ai/DeepSeek-OCR”和“dfget modelscope://models/deepseek-ai/DeepSeek-OCR”等命令来获取存储库。 Git LFS 数据通过 Dragonfly P2P 加速下载，而其他存储库元数据则通过 Git 协议获取。

![链接到 Git 协议的各种存储库的下载链接的图像。](https://www.cncf.io/wp-content/uploads/2026/06/image-8.png)

如需了解更多信息，请参阅[Hugging Face 存储库下载](https://github.com/dragonflyoss/dragonfly/issues/4419) 和[ModelScope 存储库下载](https://github.com/dragonflyoss/dragonfly/issues/4420)。

用于 Kubernetes Webhook 注入的 Dragonfly 注入器

Dragonfly 提供了 [dragonfly-injector](https://github.com/dragonflyoss/dragonfly-injector)，一个用于自动 P2P 能力注入的 Kubernetes Mutating Registration Webhook。它可以通过基于注释的策略将 Dragonfly 客户端二进制文件和配置、dfdaemon 套接字安装和 CLI 工具注入到应用程序 Pod 中，使 Pod 能够使用 Dragonfly 进行文件下载，而无需重建容器映像。 Helm Charts 现在还支持部署 Dragonfly 并启用 Webhook 注入。

更多详细信息，请参阅[使用 Dragonfly 进行 webhook 注入](https://d7y.io/docs/next/getting-started/installation/helm-charts/#using-dragonfly-with-webhook-injection)。

#### 下载控制阻止列表

Dragonfly 支持在 Manager 控制台中配置阻止列表以禁用特定下载。这可以作为紧急措施，减轻突发异常请求对服务的影响。当阻止的下载被拦截时，gRPC 下载会返回“PermissionDenied”错误代码，HTTP 代理下载会返回“FORBIDDEN”状态。

![Dragonfly 集群配置的屏幕截图](https://www.cncf.io/wp-content/uploads/2026/06/image-9.png)

如需了解更多信息，请参阅[阻止列表](https://d7y.io/docs/next/advanced-guides/blocklist/)。####综合速率限制

Dragonfly 在控制平面和客户端引入了更完整的速率限制功能。管理器和调度程序 gRPC 服务器现在支持一元请求和流连接的可配置请求速率限制。客户端支持出站带宽、入站带宽、回源带宽、预取带宽、上传请求、下载请求、自适应限速，更好地保护源端业务，提高高负载下的系统稳定性。

如需了解更多信息，请参阅[速率限制](https://d7y.io/docs/next/advanced-guides/rate-limit/)。

#### dfctl 命令行工具

Dragonfly Client引入了dfctl，这是一个命令行工具，用于管理客户端本地存储中的任务，包括任务、持久化任务和持久化缓存任务。它支持列出和删除本地资源，并可以通过调度程序预热文件和图像任务。

如需了解更多信息，请参阅 [dfctl](https://d7y.io/docs/next/reference/commands/client/dfctl/)。

#### 容器注册表代理配置简化

dfdaemon 现在可以从 containerd 注册表镜像请求附加的 ns 查询参数推断上游注册表。与 proxyAllRegistries: true 结合使用，用户可以使用单个 _default/hosts.toml 配置通过 Dragonfly 路由所有注册表，而不是维护单独的特定于注册表的 Hosts.toml 文件和 X-Dragonfly-Registry 标头。

有关更多信息，请参阅[从containerdns查询参数推断上游注册表](https://github.com/dragonflyoss/client/issues/1791)和[proxyAllRegistries文档更新](https://github.com/dragonflyoss/d7y.io/pull/410)。

#### 客户端下载和传输优化

Dragonfly Client 在多个方面提高了下载效率和文件传输可靠性。父选择器和片段收集器现在更紧密地协调，以便在调度决策之前收集足够的父对等点，从而提高带宽利用率，同时为不稳定的父对等点保持优雅的回退。文件导出和下载操作现在使用缓冲写入，并且 gRPC 流缓冲区大小和连接设置已经过调整，以获得更好的大文件传输性能。

#### HTTP 处理和重定向安全性改进HTTP 后端

现在使用 HTTP/1.1，并通过在响应具有传输编码但没有内容长度时重试 HEAD 请求来改进统计请求处理。在执行跨域重定向时，Dragonfly 还会剥离授权和 Cookie 等敏感标头，并避免缓存相对 HTTP 307 重定向位置，同时在请求处理期间仍能正确解析它们。

#### 其他增强功能

- 在 Manager 中添加ExternalRedis TLS 支持，包括 CA 证书、客户端证书、密钥和 insecureSkipVerify 选项。
- 删除已弃用的 V1 预热 API 端点并将运行状况检查合并到 /healthy 端点。
- 改进上传和下载指标收集并删除未使用的 gRPC 片段下载逻辑。
- 通过使用 Kubernetes 构建时环境变量并回退到系统主机名来改进 INSTANCE_NAME 生成。
- 添加 dfdaemon hickory_dns 选项以使 DNS 解析器行为可配置。
- 改进 OCI 注册表 blob 下载的任务 ID 计算，以减少跨注册表的冗余下载和存储。

### 重大错误修复

- 修复了对等 TTL 和并发_件_计数的 Redis Lua 脚本参数顺序，防止意外密钥过期和不正确的对等状态。
- 修复了播种默认调度程序集群和种子对等集群记录后的 PostgreSQL SERIAL 序列处理，避免创建新集群时发生主键冲突。
- 通过跳过相对位置值的缓存并在重定向之前根据基本 URL 解析它们，修复了相对 HTTP 307 重定向处理。

### 坑道

#### 新功能和增强功能

- 支持为按需数据构建预取优化的图层 blob。
- 支持将 Nydus 图像转换为 OCI 格式以及与本地存档之间的转换。
- Nydusify Copy 中支持零磁盘传输。
- 为 virtio-pmem DAX 后端引入基于 uffd 的支持，以在 Kata 场景中实现高性能的按需图像加载。
- 支持存储层从Proxy模式切换到Dragonfly SDK模式，以提高P2P缓存命中性能。
- 支持使用短容器 ID 进行提交并在提交前同步文件系统。
- 支持恢复 Nydusd 时重新发送 FUSE 请求，修复热升级测试。

#### 重大错误修复

- 修复了 Blobfs 与 fusion-backend-rs 0.12.0 的兼容性。
- 修复故障转移策略参数解析。
- 修复当符号链接覆盖目录时 Builder 中的恐慌。
- 修复 chunkdict 重复数据删除逻辑、DBSCAN 集群和块排序中的多个问题。
- 修复 Nydus 图像检测逻辑。
- 修复 fusione 中嵌套安装点的重新安装无效问题。
- 修复 Nydusctl 后端指标计数器重置时的异常值。
- 修复了修改图像名称时 Nydusify 无法找到 blob 的问题。
- 修复 Nydusify 中的纯 HTTP 转换。

### 其他

您可以查看 [CHANGELOG](https://github.com/dragonflyoss/dragonfly/blob/main/CHANGELOG.md) 了解更多详细信息。

### 链接

- 蜻蜓网站：[https://d7y.io/](https://d7y.io/)
- 蜻蜓存储库：[https://github.com/dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly)
- Dragonfly 客户端存储库：[https://github.com/dragonflyoss/client](https://github.com/dragonflyoss/client)
- Dragonfly 注射器存储库：[https://github.com/dragonflyoss/dragonfly-injector](https://github.com/dragonflyoss/dragonfly-injector)
- Dragonfly 控制台存储库：[https://github.com/dragonflyoss/console](https://github.com/dragonflyoss/console)
- Dragonfly 图表存储库：[https://github.com/dragonflyoss/helm-charts](https://github.com/dragonflyoss/helm-charts)
- Dragonfly 监视器存储库：[https://github.com/dragonflyoss/monitoring](https://github.com/dragonflyoss/monitoring)

### 蜻蜓 Github

![Github 存储库的二维码](https://www.cncf.io/wp-content/uploads/2026/06/image-10.png)

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
