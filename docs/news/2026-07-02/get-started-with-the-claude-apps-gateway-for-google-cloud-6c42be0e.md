<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T00:00:00+08:00
source: Google Cloud Blog
domain: 云原生
url: https://cloud.google.com/blog/topics/developers-practitioners/announcing-claude-apps-gateway-for-google-cloud/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# 宣布推出适用于 Google Cloud 的 Claude 应用网关 |谷歌云博客

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 00:00 CST |
| 领域 | 云原生 |
| 来源 | Google Cloud Blog |
| 原文标题 | Announcing Claude apps gateway for Google Cloud \| Google Cloud Blog |
| 原文 | [打开原文](https://cloud.google.com/blog/topics/developers-practitioners/announcing-claude-apps-gateway-for-google-cloud/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

Anthropic 的代理编码工具 Claude Code 已经与 Google Cloud 合作了一段时间。个人开发人员可以轻松地将 CLAUDE_CODE_USE_VERTEX=1 指向 Google Cloud (GCP) 项目，授予角色 Roles/aiplatform.user ，并且推理将保留在 Google Cloud 范围内。当只有您或少数工程师时，这种流程非常有效。但在整个组织中推广它会迫使您应对企业摩擦：您必须管理每个开发人员的云凭据，通过 MDM 将 Managed-settings.json 推送到每台笔记本电脑，并且不能通过每个开发人员的零使用归因或易于强制执行的支出上限进行验证。Claude应用程序网关弥补了这一差距。它是一项自托管服务，附带相同的 claude 二进制文件，直接位于本地 Claude Code 客户端和 Google Cloud 之间。这篇文章详细介绍了您应该运行它的原因以及 Google Cloud 上的安全部署是什么样的。 （注意：如果您想直接跳到代码，完整的演练位于 Google Cloud 文档上的 Claude apps gateway 中。） 为什么运行网关 运行网关以集中开发人员和平台管理员各自单独进行的治理，例如

## 正文

开发者与从业者

##

开始使用适用于 

Google Cloud 的 Claude 应用网关

2026 年 7 月 2 日

###### 罗伊·阿桑

应用人工智能工程师，Anthropic

###### 伊万·纳尔迪尼

谷歌云人工智能工程师

###### 立即尝试 

Gemini Enterprise 商业版

Anthropic 的代理编码工具 Claude Code 已经与 Google Cloud 合作了一段时间。个人开发人员可以轻松地将“CLAUDE_CODE_USE_VERTEX=1”指向 Google Cloud (GCP) 项目，授予角色“roles/aiplatform.user”，推理将保留在 Google Cloud 范围内。

当只有您或少数工程师时，这种流程非常有效。但在整个组织中推广它会迫使您应对企业摩擦：您必须管理每个开发人员的云凭据，通过 MDM 将“托管设置.json”推送到每台笔记本电脑，并且不能通过每个开发人员的零使用归因或易于强制执行的支出上限进行验证。

Claude应用程序网关弥补了这一差距。它是一项自托管服务，附带相同的 claude 二进制文件，直接位于本地 Claude Code 客户端和 Google Cloud 之间。这篇文章详细介绍了您应该运行它的原因以及 Google Cloud 上的安全部署是什么样的。

（注意：如果您想直接跳到代码，完整的演练位于 [Google Cloud 文档上的 Claude apps gateway](https://code.claude.com/docs/en/claude-apps-gateway-on-gcp)。）

#### 为什么要运行网关

运行网关来集中开发人员和平台管理员各自进行的治理，例如身份、策略、成本和路由。这就是实际情况。

身份。 “/login” 请求通过您的身份提供商 (IdP) - Google Workspace 或任何 OIDC/OpenID Connect 进行路由 - 并且网关会交换令牌以进行短期会话。开发人员的笔记本电脑上不会出现敏感信息，例如服务帐户密钥、API 密钥或“ANTHROPIC_VERTEX_PROJECT_ID”。入职就像将用户添加到 IdP 组一样简单；通过删除它们来关闭，并且它们的下一个会话刷新当场失败。政策。您的 RBAC（基于角色的访问控制）规则在“gateway.yaml”中存在一次，按组解析并在服务器端强制执行。网关会在每次“/v1/messages”调用时重新检查“availableModels”，因此编辑本地“management-settings.json”不会改变任何内容，并且规则更新会在一小时内到达整个队列。

遥测。每个“claude_code.token.usage”指标都包含来自会话 JWT（签名会话令牌）的已验证电子邮件和组，而不是可欺骗的客户端集“OTEL_RESOURCE_ATTRIBUTES”。网关通过 OTLP/HTTP 将它们发送到您运行的收集器 - Cloud Monitoring、Grafana、Datadog，无论您使用什么。

支出限额。通过管理 API 设置每个用户、组或组织的每日、每周或每月上限；网关根据 Cloud SQL 分类账计量代币，并在上限处返回 429。成本按标价计算，因此请将其视为失控使用护栏，而不是账单对账（承诺使用折扣和协商费率不会显示）。

路由。呼叫以单个 Cloud Run 服务身份发出。为代理平台的全局端点设置“region: global”，或添加第二个“upstreams:”条目以按列表顺序在 5xx/429/timeout 上进行故障转移。无论哪种方式，推理都会保留在您的 GCP 项目中 - 配额、数据处理协议和计费均保持不变。

#### 它是如何组合在一起的

开发人员的本地或部署的“claude”进程通过 HTTPS 将推理流量发送到网关。网关是 Cloud Run 上的无状态容器，如下所示。

![https://storage.googleapis.com/gweb-cloudblog-publish/images/1_FY2cRbt.max-1200x1200.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/1_FY2cRbt.max-1200x1200.png)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/1_FY2cRbt.max-1200x1200.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/1_FY2cRbt.max-1200x1200.png)

网关验证其自己的会话承载（仅在登录和令牌刷新时联系 Google Workspace）检查策略，并使用 Cloud Run 服务帐号将请求转发到代理平台。 Cloud SQL 保存设备代码登录状态和支出分类帐； OTLP 收集器接收属性指标。

#### 在 

Google Cloud 上进行设置完整的演练、每个 gcloud 命令和完整的“gateway.yaml”参考位于 [Google Cloud 文档上的 Claude apps gateway](https://code.claude.com/docs/en/claude-gateway-on-gcp)。简短版本：

步骤 1：配置 GCP 基础
启用代理平台、Cloud SQL 和 Secret Manager API；使用“roles/aiplatform.user”创建“claude-gateway”服务帐户；为状态建立一个小型 Cloud SQL Postgres 数据库实例。网关以 Cloud Run 服务身份向 Agent Platform 进行身份验证 — 您无需创建服务帐户密钥。最后，在 Google Cloud 控制台中创建一个 [新 OAuth 客户端](https://support.google.com/cloud/answer/15549257?hl=en)（类型为 Web 应用程序）：在此示例中，网关将 Google Workspace 上的开发人员作为 OIDC 依赖方进行身份验证，并且该客户端为该握手颁发了“client_id”和“client_secret”。这两个值将在下一步中提供给 `oidc`: 块。一旦网关 URL 已知，您稍后将添加授权的重定向 URI。

步骤 2：配置网关
编写指向您的 Google Workspace OIDC 客户端、Postgres 连接字符串和代理平台的“gateway.yaml”作为上游。将其与 OIDC 客户端密钥、Postgres URL 和 JWT 签名密钥一起存储在 Secret Manager 中。

正在加载...

Listen: port: 8080 public_url: https://<your-cloud-run-service-url> # Cloud Run 服务网址 — 带有 --ingress=internal 时，仅在您的 VPC/企业网络内部进行解析 oidc: Issuer: https://accounts.google.com # Google Workspace client_id: <client-id>.apps.googleusercontent.com client_secret: ${OIDC_CLIENT_SECRET} # 来自 Secret Manager allowed_email_domains: [yourco.com]上游： - 提供商：顶点 区域：us-east5 项目 ID：<您的项目> 身份验证：{} # 通过 Cloud Run SA 进行 ADC，无密钥文件

然后将 `https://<public_url host>/oauth/callback` 注册为 Google OAuth 客户端上的授权重定向 URI — 它必须与listen.public_url 完全匹配：

![https://storage.googleapis.com/gweb-cloudblog-publish/images/2_MvuTCiS.max-700x700.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/2_MvuTCiS.max-700x700.png)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/2_MvuTCiS.max-700x700.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/2_MvuTCiS.max-700x700.png)第 3 步：部署到 Cloud Run
附加了服务帐户、VPC 上的 Cloud SQL 连接以及从 Secret Manager 挂载的配置的“gcloud run deploy”。该容器是无状态的，并在 Cloud Run 负载均衡器后面水平扩展。如果 GKE 已经是您的平台，并且只有部署清单发生变化，那么 GKE 也同样可以正常工作。

正在加载...

gcloud run deploy claude-gateway \ --service-account="claude-gateway@${PROJECT_ID}.iam.gserviceaccount.com" \ --set-secrets=/etc/claude/gateway.yaml=gateway-config:latest \ --ingress=internal \ # private — 开发人员通过企业网络到达网关（VPN/互连到 VPC） --no-invoker-iam-check # 网关运行自己的网络伊斯兰开发公司；客户端不携带 GCP 令牌

开发人员通过公司网络进行连接；您可以在服务前面使用内部应用程序负载均衡器 - [请参阅 Cloud Run 专用网络](https://cloud.google.com/run/docs/securing/private-networking)。

无论是公共还是内部，您的开发人员都必须能够访问您配置的任何 URL，或者您可以依赖 Cloud Run 中的默认 URL。对于下面的示例，我们将使用 [https://claude-gateway.example.internal](https://claude-gateway.example.internal)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/3_nlczWOp.max-1100x1100.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/3_nlczWOp.max-1100x1100.png)

![https://storage.googleapis.com/gweb-cloudblog-publish/images/3_nlczWOp.max-1100x1100.png](https://storage.googleapis.com/gweb-cloudblog-publish/images/3_nlczWOp.max-1100x1100.png)

第 4 步：加入开发人员
通过托管设置将 `forceLoginMethod: "gateway"` 和 `forceLoginGatewayUrl` 推送到开发人员计算机。这就是 ```/login` 知道连接到哪里的方式，无需手动输入 URL。对于组织部署，这就是您的 MDM 渠道。对于没有 MDM 的首次试用，如果开发人员具有本地管理员权限，则可以在 macOS 上的“/Library/Application Support/ClaudeCode/managed-settings.json”（或 Linux 上的“/etc/claude-code/management-settings.json”）中手动编写文件：

正在加载...

{ "forceLoginMethod": "网关", "forceLoginGatewayUrl": "https://claude-gateway.example.internal" }Claude Code 启动时，开发者会在预先填写的网关登录屏幕上按 Enter 键确认 URL。在浏览器中的网关验证页面上确认设备代码，然后重定向到 Google Workspace 进行登录。之后，开发者在浏览器中针对 Google Workspace 完成设备代码流程。如果安装正确结束，您将能够在终端视图中看到云网关，如下所示。

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/Claude_Code_login_flow_with_gateway.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/Claude_Code_login_flow_with_gateway.gif)

![https://storage.googleapis.com/gweb-cloudblog-publish/original_images/Claude_Code_login_flow_with_gateway.gif](https://storage.googleapis.com/gweb-cloudblog-publish/original_images/Claude_Code_login_flow_with_gateway.gif)

#### 接下来是什么

此时，您应该更好地了解如何配置和使用 [Google Cloud 上的 Claude apps gateway](https://code.claude.com/docs/en/claude-apps-gateway-on-gcp)。以下是您可能需要考虑的一些后续步骤：

-

完整配置参考：每个 `gateway.yaml` 字段都位于 [claude-apps-gateway-config](https://code.claude.com/docs/en/claude-apps-gateway-config) 中。每个 IdP 设置和 GKE 跟踪位于 [claude-apps-gateway-deploy](https://code.claude.com/docs/en/claude-apps-gateway-deploy) 和 [claude-apps-gateway-on-gcp](https://code.claude.com/docs/en/claude-apps-gateway-on-gcp) 中。

-

组范围的策略：在网关前面使用支持组的 IdP，设置“groups_claim”，并在所有内容之上添加“match: { groups: [...] }”策略，为不同的团队提供不同的模型列表和工具权限。

现在，感谢您的阅读！如果您有任何其他问题或反馈，请随时通过社交媒体联系（Roy Arsan - [Linkedin](https://www.linkedin.com/in/arsan/)、[X](https://x.com/RoyArsan) 和 Ivan Nardini - [LinkedIn](https://linkedin.com/)、[X](https://x.com/)）

快乐建设！

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
