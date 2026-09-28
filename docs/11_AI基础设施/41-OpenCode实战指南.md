# OpenCode 实战指南（简介 / 参数说明 / 最佳实践）

> OpenCode 是开源的 AI 编码 Agent，以终端 TUI 为主界面，同时提供桌面应用、IDE 扩展和 HTTP Server 三种形态。它把"读代码、改文件、跑命令"的循环封装成可配置的 Agent 体系，支持任意 LLM Provider、细粒度权限控制、MCP 扩展和插件钩子。本文分三部分：**简介**（它是什么、架构、和同类工具对比）、**参数说明**（CLI 命令、全局参数、配置项全表、环境变量）、**最佳实践**（生产落地的配置模板、Agent 编排、权限安全、CI 集成、排障）。
>
> 本文基于 OpenCode 官方文档（opencode.ai/docs）整理，文档最后更新 2026-09。版本迭代较快，**具体参数以 `opencode --help` 和官方在线 schema（https://opencode.ai/config.json）为准**。

---

## 第一部分：简介

### 1.1 OpenCode 是什么

```text
OpenCode = 开源 AI 编码 Agent (open source AI coding agent)

定位:
  在终端里和 LLM 结对编程, 让模型直接读代码/改文件/跑命令

三种形态:
  ┌────────────────────────────────────────────┐
  │  ① TUI (主形态)  终端交互界面, 默认入口      │
  │  ② Desktop App   桌面应用 (自带本地 server)  │
  │  ③ IDE Extension VS Code / JetBrains 等     │
  └────────────────────────────────────────────┘
  + 无头形态: opencode serve / web / acp (给脚本和第三方集成用)

基础信息:
  Provider 无关  : 官方称 "any LLM provider", 内置 Models.dev 供应商目录
  模型格式        : provider/model, 例如 anthropic/claude-sonnet-4-5
  官方网关        : OpenCode Zen (可选, 经过测试验证的模型清单)
  配置格式        : JSON / JSONC
  凭证存放        : ~/.local/share/opencode/auth.json
  会话数据        : ~/.local/share/opencode/project/
  日志            : ~/.local/share/opencode/log/
```

### 1.2 核心能力

| 能力 | 说明 |
|:---|:---|
| **代码理解与修改** | 读文件、搜索、编辑、打补丁；支持跨文件重构 |
| **命令执行** | 跑 shell 命令、测试、构建，输出进上下文 |
| **Agent 体系** | 主 Agent（Build/Plan）+ 子 Agent（General/Explore/Scout），可自定义 |
| **权限系统** | allow / ask / deny 三级，支持按 glob 模式做细粒度控制 |
| **会话与撤销** | 会话持久化、`/undo` `/redo`，基于内置 Git 快照实现回滚 |
| **MCP 扩展** | 本地/远程 MCP Server 接入，OAuth 自动处理 |
| **插件钩子** | JS/TS 插件，可挂 `tool.execute.before` 等事件钩子 |
| **Skills** | `SKILL.md` 形式的按需加载能力包 |
| **共享** | 会话可分享为链接（可配置为 manual / auto / disabled） |
| **无头服务** | `opencode serve` 提供 HTTP API，可接 CI、脚本、自研前端 |

### 1.3 架构概览

```text
                    ┌─────────────────────────────────┐
   用户入口          │  TUI  /  Desktop  /  IDE 扩展    │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      OpenCode Server (本地)      │
                    │  会话管理 / Agent 调度 / 工具执行 │
                    │  HTTP API (serve / web / acp)    │
                    └───┬──────────┬──────────┬───────┘
                        │          │          │
        ┌───────────────▼──┐  ┌────▼─────┐  ┌─▼──────────────┐
        │  Agent 层         │  │ 工具层   │  │ 扩展层          │
        │  build / plan     │  │ read     │  │ MCP servers    │
        │  general/explore  │  │ edit     │  │ Plugins        │
        │  scout / 自定义    │  │ bash     │  │ Skills         │
        │                  │  │ grep/glob │  │ Custom tools   │
        └────────┬─────────┘  └────┬─────┘  └─┬──────────────┘
                 │                 │           │
        ┌────────▼─────────────────▼───────────▼─────────┐
        │              权限系统 (permission)              │
        │   allow (直接跑) / ask (问你) / deny (拦住)      │
        └────────────────────┬───────────────────────────┘
                             │
        ┌────────────────────▼───────────────────────────┐
        │        LLM Provider (任意, 经 Models.dev)       │
        │  Anthropic / OpenAI / Google / Bedrock / 兼容   │
        └────────────────────────────────────────────────┘
```

### 1.4 内置 Agent 一览

| Agent | 模式 | 工具权限 | 用途 |
|:---|:---|:---|:---|
| **build** | primary（默认） | 全开 | 正常开发工作，可改文件跑命令 |
| **plan** | primary | edit/bash 默认 ask | 只分析与出方案，不做实际修改 |
| **general** | subagent | 全开（除 todo） | 复杂问题研究、多步任务，可并行 |
| **explore** | subagent | 只读 | 快速探索代码库、按模式找文件 |
| **scout** | subagent | 只读 | 外部文档与依赖研究、克隆依赖仓库 |
| compaction | primary（隐藏） | - | 上下文压缩，自动运行 |
| title | primary（隐藏） | - | 生成会话标题，自动运行 |
| summary | primary（隐藏） | - | 生成会话摘要，自动运行 |

**用法**：
- 主 Agent 之间用 `Tab` 键切换
- 子 Agent 用 `@` 手动召唤：`@general 帮我搜一下这个函数`
- 子会话导航：`session_child_first`（默认 `<Leader>+Down`）、`session_child_cycle`（`Right`）、`session_parent`（`Up`）

### 1.5 与同类工具对比

| 维度 | OpenCode | Claude Code | Cursor | Aider |
|:---|:---|:---|:---|:---|
| 开源 | ✅ 开源 | ❌ 闭源 | ❌ 闭源 | ✅ 开源 |
| 主要形态 | 终端 TUI + 桌面 + IDE | 终端 CLI | IDE（编辑器本体） | 终端 CLI |
| Provider | 任意（Models.dev 目录） | 仅 Anthropic | 多模型 | 多模型 |
| 子 Agent 体系 | ✅ 内置 + 自定义 | ✅ | 部分 | ❌ |
| 权限模型 | allow/ask/deny + glob | 权限提示 | 编辑器内审批 | 手动确认 |
| MCP 支持 | ✅ 本地 + 远程 + OAuth | ✅ | ✅ | 部分 |
| 插件系统 | ✅ JS/TS 钩子 | Hooks | 扩展市场 | ❌ |
| 无头/API | ✅ serve / web / acp | 有限 | ❌ | 有限 |
| 会话共享 | ✅ 链接分享 | ❌ | ❌ | ❌ |
| 配置可版本化 | ✅ opencode.json 入库 | 部分 | ❌ | 部分 |
| 典型场景 | 团队标准化、多模型、CI 集成 | Anthropic 生态重度用户 | 编辑器内协作 | 轻量命令行改代码 |

**选型提示**：

```text
选 OpenCode 的理由:
  ✅ 要开源、要自己掌控（可审计、可内网部署）
  ✅ 团队要统一 Agent/权限/规则（配置入库 + managed settings）
  ✅ 要接多家模型/自建推理服务（provider 无关）
  ✅ 要接 CI/CD 或自研平台（serve HTTP API）

不适合的场景:
  ❌ 只想在 IDE 里点点鼠标 → 编辑器类工具更顺手
  ❌ 团队强制要求某家厂商全家桶 → 生态一致性更重要
```

### 1.6 安装

```bash
# 官方安装脚本 (推荐)
curl -fsSL https://opencode.ai/install | bash

# Node.js 生态
npm install -g opencode-ai
bun install -g opencode-ai
pnpm install -g opencode-ai
yarn global add opencode-ai

# Homebrew (macOS / Linux)
brew install anomalyco/tap/opencode
# 官方 tap 更新更及时, Homebrew 官方 formula 更新较慢

# Arch Linux
sudo pacman -S opencode        # 稳定版
paru -S opencode-bin           # AUR 最新版

# Windows
choco install opencode         # Chocolatey
scoop install opencode         # Scoop
mise use -g github:anomalyco/opencode
# 官方推荐 Windows 用 WSL, 体验最好

# Docker
docker run -it --rm ghcr.io/anomalyco/opencode

# 也可从 GitHub Releases 直接下载二进制
```

**前置条件**：一个现代终端模拟器（WezTerm / Alacritty / Ghostty / Kitty 等）+ 你要用的 LLM Provider 的 API Key。

### 1.7 三分钟上手

```bash
# 1. 进入项目
cd /path/to/project

# 2. 启动 TUI
opencode

# 3. 先连接 Provider (TUI 内执行)
/connect
#  → 选 provider (如 OpenCode Zen) → 前往 opencode.ai/auth 登录
#  → 复制 API Key → 粘贴回 TUI

# 4. 初始化项目规则 (生成 AGENTS.md)
/init
#  → 分析项目结构, 生成 AGENTS.md
#  → 建议把 AGENTS.md 提交到 Git, 团队成员共享

# 5. 干活
> 解释一下 @packages/functions/src/api/index.ts 里的鉴权是怎么做的

# 6. 想让它出方案而不动手 → Tab 切到 plan
#    想让它动手 → Tab 切回 build
```

**非交互用法**：

```bash
opencode run "解释 Go 里 context 的用法"
```

---

## 第二部分：参数说明

### 2.1 CLI 命令结构

```text
opencode                        # 无参数 → 启动 TUI
opencode [project]              # 指定目录启动 TUI
opencode <command> [options]    # 执行子命令

子命令列表:
  agent      管理 Agent (create / list)
  attach     把终端接到已运行的 backend server
  auth       凭证与登录 (login / list / logout)
  github     GitHub agent (install / run)
  mcp        MCP server 管理 (add / list / auth / logout / debug)
  models     列出可用模型
  run        非交互模式跑一个 prompt
  serve      启动无头 HTTP server
  session    会话管理 (list / delete)
  stats      token 用量与成本统计
  export     导出会话为 JSON
  import     导入会话 (本地文件或 share URL)
  web        启动带 Web 界面的 server
  acp        启动 ACP (Agent Client Protocol) server
  plugin     安装插件并更新配置 (别名 plug)
  pr         拉取并切换 GitHub PR 分支后启动 opencode
  db         数据库工具 (path / query)
  debug      调试排障工具
  uninstall  卸载并清理相关文件
  upgrade    升级到最新或指定版本
```

### 2.2 TUI 启动参数（`opencode` / `opencode [project]`）

| 参数 | 短写 | 说明 |
|:---|:---|:---|
| `--continue` | `-c` | 继续上一个会话 |
| `--session` | `-s` | 指定要恢复的会话 ID |
| `--fork` | | 继续会话时创建分支（配合 `--continue` / `--session`） |
| `--prompt` | | 启动时使用的 prompt |
| `--model` | `-m` | 指定模型，格式 `provider/model` |
| `--agent` | | 指定 Agent |
| `--auto` | | 自动批准未被显式 deny 的权限请求 |
| `--port` | | 监听端口 |
| `--hostname` | | 监听主机名 |
| `--mdns` | | 启用 mDNS 服务发现 |
| `--mdns-domain` | | 自定义 mDNS 域名 |
| `--cors` | | 允许的额外浏览器来源（CORS） |

### 2.3 全局参数

| 参数 | 短写 | 说明 |
|:---|:---|:---|
| `--help` | `-h` | 显示帮助 |
| `--version` | `-v` | 打印版本号 |
| `--print-logs` | | 把日志打到 stderr（排障用） |
| `--log-level` | | 日志级别：`DEBUG` / `INFO` / `WARN` / `ERROR` |
| `--pure` | | 不加载任何外部插件运行（排查插件冲突用） |

### 2.4 各子命令参数详解

#### `opencode run` —— 非交互执行

```bash
opencode run [message..]
```

| 参数 | 短写 | 说明 |
|:---|:---|:---|
| `--command` | | 要运行的命令，参数用 message 传 |
| `--continue` | `-c` | 继续上一个会话 |
| `--session` | `-s` | 指定会话 ID |
| `--fork` | | 继续时分叉会话 |
| `--share` | | 分享该会话 |
| `--model` | `-m` | 模型（`provider/model`） |
| `--agent` | | Agent |
| `--file` | `-f` | 附加文件到消息 |
| `--format` | | 输出格式：`default`（格式化）或 `json`（原始 JSON 事件） |
| `--title` | | 会话标题（不给值则用截断的 prompt） |
| `--attach` | | 附加到已运行的 server，例如 `http://localhost:4096` |
| `--password` | `-p` | Basic Auth 密码（默认取 `OPENCODE_SERVER_PASSWORD`） |
| `--username` | `-u` | Basic Auth 用户名（默认 `OPENCODE_SERVER_USERNAME` 或 `opencode`） |
| `--dir` | | 运行目录；attach 时为远端 server 上的路径 |
| `--port` | | 本地 server 端口（默认随机） |
| `--variant` | | 模型变体（provider 相关的 reasoning effort） |
| `--thinking` | | 显示 thinking 块 |
| `--auto` | | 自动批准未显式 deny 的权限 |

**关键技巧**：用 `--attach` 复用常驻 server，避免每次 run 都冷启动 MCP server。

```bash
# 终端 A: 起常驻 server
opencode serve

# 终端 B: 复用
opencode run --attach http://localhost:4096 "解释一下 async/await"
```

#### `opencode serve` —— 无头 HTTP 服务

| 参数 | 说明 |
|:---|:---|
| `--port` | 监听端口 |
| `--hostname` | 监听主机名 |
| `--mdns` | 启用 mDNS 发现 |
| `--mdns-domain` | 自定义 mDNS 域名 |
| `--cors` | 额外允许的浏览器来源 |

设置 `OPENCODE_SERVER_PASSWORD` 启用 HTTP Basic Auth（用户名默认 `opencode`）。

#### `opencode attach` —— 接到远端 backend

| 参数 | 短写 | 说明 |
|:---|:---|:---|
| `--dir` | | TUI 启动的工作目录 |
| `--continue` | `-c` | 继续上一会话 |
| `--session` | `-s` | 会话 ID |
| `--fork` | | 继续时分叉 |
| `--password` | `-p` | Basic Auth 密码 |
| `--username` | `-u` | Basic Auth 用户名 |

```bash
# 服务端: 给 Web/移动端用的 backend
opencode web --port 4096 --hostname 0.0.0.0
# 客户端: 把 TUI 接上去
opencode attach http://10.20.30.40:4096
```

#### `opencode agent` —— Agent 管理

```bash
opencode agent create     # 交互式创建自定义 Agent
opencode agent list       # 列出所有可用 Agent
```

| 参数（create） | 短写 | 说明 |
|:---|:---|:---|
| `--path` | | Agent 文件写入目录（默认按提示落到全局或 `.opencode/agent`） |
| `--description` | | Agent 的用途描述 |
| `--mode` | | Agent 模式：`all` / `primary` / `subagent` |
| `--permissions` | | 逗号分隔的允许权限，默认全部。可选值：`bash` `read` `edit` `glob` `grep` `webfetch` `task` `todowrite` `websearch` `lsp` `skill`；**未列出的即被拒绝**。别名 `--tools` |
| `--model` | `-m` | 模型（`provider/model`） |

> `--path` `--description` `--mode` `--permissions` 四个都传齐时，命令以非交互方式运行（适合脚本化）。

#### `opencode auth` —— 凭证管理

```bash
opencode auth login     # 登录 Provider
opencode auth list      # 列出已认证 Provider (别名: ls)
opencode auth logout    # 退出某个 Provider
```

| 参数（login） | 短写 | 说明 |
|:---|:---|:---|
| `--provider` | `-p` | Provider ID 或名称 |
| `--method` | `-m` | 登录方式标签，跳过方式选择 |

凭证存放在 `~/.local/share/opencode/auth.json`。启动时还会加载环境变量和项目 `.env` 中的 Key。

#### `opencode models` —— 列出模型

| 参数 | 说明 |
|:---|:---|
| `--refresh` | 从 models.dev 刷新模型缓存（Provider 上新模型后用） |
| `--verbose` | 更详细的输出（含成本等元数据） |

```bash
opencode models                # 全部
opencode models anthropic      # 按 provider 过滤
opencode models --refresh      # 刷新缓存
```

#### `opencode session` —— 会话管理

| 命令 / 参数 | 短写 | 说明 |
|:---|:---|:---|
| `opencode session list` | | 列出所有会话 |
| `--max-count` | `-n` | 限制最近 N 个会话 |
| `--format` | | 输出格式：`table` / `json` |
| `opencode session delete <sessionID>` | | 删除会话 |

#### `opencode stats` —— 用量与成本

| 参数 | 说明 |
|:---|:---|
| `--days` | 统计最近 N 天（默认全部时间） |
| `--tools` | 显示多少个工具的用量（默认全部） |
| `--models` | 显示模型用量明细（默认隐藏），传数字显示 Top N |
| `--project` | 按项目过滤（默认全部；空字符串 = 当前项目） |

> 这是做成本治理（FinOps）的入口，可以拿它统计团队 AI 编码成本。

#### `opencode export` / `import` —— 会话迁移

| 命令 | 参数 | 说明 |
|:---|:---|:---|
| `opencode export [sessionID]` | `--sanitize` | 导出会话为 JSON；不给 ID 会提示选择。`--sanitize` 脱敏 transcript/文件数据 |
| `opencode import <file>` | | 从本地 JSON 或 share URL 导入 |

```bash
opencode import session.json
opencode import https://opncd.ai/s/abc123
```

> `--sanitize` 在把会话发给外部（比如报 Bug、做培训材料）时必用，避免泄露代码和密钥。

#### `opencode mcp` —— MCP Server 管理

| 命令 | 说明 |
|:---|:---|
| `opencode mcp add` | 交互式添加本地或远程 MCP Server |
| `opencode mcp list` | 列出已配置 MCP 及其连接状态（别名 `ls`） |
| `opencode mcp auth [name]` | 对支持 OAuth 的 MCP 认证（不给名字则让你选） |
| `opencode mcp auth list` | 列出支持 OAuth 的 MCP 及认证状态（别名 `ls`） |
| `opencode mcp logout [name]` | 移除某 MCP 的 OAuth 凭证 |
| `opencode mcp debug <name>` | 调试 MCP 的 OAuth 连接问题 |

#### `opencode github` —— GitHub Agent

| 命令 / 参数 | 说明 |
|:---|:---|
| `opencode github install` | 在仓库安装 GitHub Agent（配置 GitHub Actions workflow） |
| `opencode github run` | 运行 GitHub Agent（通常由 Actions 调用） |
| `--event` | 要运行的 GitHub mock event |
| `--token` | GitHub Personal Access Token |

#### 其他子命令

| 命令 | 参数 | 说明 |
|:---|:---|:---|
| `opencode web` | `--port` `--hostname` `--mdns` `--mdns-domain` `--cors` | 起 Web 界面的 server |
| `opencode acp` | `--cwd` `--port` `--hostname` `--mdns` `--mdns-domain` `--cors` | ACP server（stdin/stdout ND-JSON） |
| `opencode plugin <module>` | `--global/-g` `--force/-f` | 安装插件并更新配置；`-g` 装到全局配置，`-f` 替换已有版本 |
| `opencode pr <number>` | | 拉取并 checkout 该 PR 分支后启动 |
| `opencode db [query]` | `--format json\|tsv` | 数据库工具；`opencode db path` 打印库路径 |
| `opencode debug <command>` | | 调试工具（如 `opencode debug config` 看解析后的配置） |
| `opencode uninstall` | `--keep-config/-c` `--keep-data/-d` `--dry-run` `--force/-f` | 卸载；`-c` 保留配置，`-d` 保留会话数据和快照，`--dry-run` 只看会删什么 |
| `opencode upgrade [target]` | `--method/-m curl\|npm\|pnpm\|bun\|brew` | 升级；可指定版本如 `opencode upgrade v0.1.48` |

### 2.5 TUI 斜杠命令

| 命令 | 别名 / 快捷键 | 说明 |
|:---|:---|:---|
| `/connect` | | 添加 Provider、填 API Key |
| `/init` | | 生成/更新 `AGENTS.md` |
| `/models` | `ctrl+x m` | 列出可用模型 |
| `/new` | `/clear`、`ctrl+x n` | 开新会话 |
| `/sessions` | `/resume`、`/continue`、`ctrl+x l` | 列出并切换会话 |
| `/compact` | `/summarize`、`ctrl+x c` | 压缩当前会话上下文 |
| `/undo` | | 撤销（含文件改动，需 Git 仓库） |
| `/redo` | `ctrl+x r` | 重做上次撤销 |
| `/share` | | 分享会话 |
| `/unshare` | | 取消分享 |
| `/export` | `ctrl+x x` | 导出对话为 Markdown 并打开编辑器 |
| `/editor` | `ctrl+x e` | 用外部编辑器写消息（取 `$EDITOR`） |
| `/details` | | 切换工具执行详情显示 |
| `/themes` | | 切换主题 |
| `/thinking` | | 切换 thinking 显示 |
| `/help` | | 帮助对话框 |
| `/exit` | `/quit`、`/q`、`ctrl+x q` | 退出 |

**TUI 输入技巧**：

| 语法 | 作用 |
|:---|:---|
| `@` | 模糊搜索并引用项目文件（内容自动入上下文） |
| `@alias` / `@alias/` | 引用已配置的引用根，或补全其下文件 |
| `!command` | 以 `!` 开头执行 shell 命令，输出作为 tool result 进上下文 |
| 拖拽图片到终端 | 图片加入 prompt（自动识别与缩放） |

### 2.6 配置文件

**格式**：支持 JSON 和 JSONC（带注释）。

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "autoupdate": true,
  "server": { "port": 4096 }
}
```

**配置加载顺序（后者覆盖前者，且是"合并"不是"替换"）**：

| 顺序 | 来源 | 用途 |
|:---|:---|:---|
| 1 | 远程配置（`.well-known/opencode`） | 组织默认值 |
| 2 | 全局配置 `~/.config/opencode/opencode.json` | 个人偏好 |
| 3 | 自定义配置（`OPENCODE_CONFIG` 环境变量） | 自定义覆盖 |
| 4 | 项目配置 `<project>/opencode.json` | 项目专属（优先级最高的常规配置） |
| 5 | `.opencode` 目录 | agents / commands / plugins 等 |
| 6 | 内联配置（`OPENCODE_CONFIG_CONTENT`） | 运行时覆盖 |
| 7 | 托管配置（Linux `/etc/opencode/`） | 管理员控制 |
| 8 | macOS managed preferences（`.mobileconfig` / MDM） | 最高优先级，用户不可覆盖 |

> **重要**：多个配置文件是**合并**的。全局设了 `autoupdate: true`，项目设了 `model`，最终两者都生效；只有冲突的键才由后面的覆盖。
>
> `.opencode` 和 `~/.config/opencode` 的子目录用**复数**：`agents/` `commands/` `modes/` `plugins/` `skills/` `tools/` `themes/`（单数形式如 `agent/` 也兼容）。

### 2.7 配置项全表

#### 顶层核心项

| 配置项 | 类型 | 说明 |
|:---|:---|:---|
| `$schema` | string | schema 地址，编辑器用它做校验和补全 |
| `model` | string | 主模型，格式 `provider/model` |
| `small_model` | string | 轻量任务模型（如生成标题）。不设则优先用 Provider 的便宜模型，否则回落主模型 |
| `provider` | object | Provider 及其模型、选项配置 |
| `agent` | object | Agent 定义（可覆盖内置或新建） |
| `default_agent` | string | 默认 Agent，必须是 primary（`build` / `plan` / 自定义）；不存在或是 subagent 时警告并回落 `build` |
| `subagent_depth` | number | 子 Agent 嵌套深度。默认 `1`（主可启子，子不能再启）；`2` 允许多一层；`0` 禁止 |
| `permission` | object / string | 权限配置，可整体设为 `"allow"` |
| `tools` | object | 工具开关（**已废弃**，改用 `permission`） |
| `instructions` | array | 额外指令文件路径或 glob，支持远程 URL（5 秒超时） |
| `mcp` | object | MCP Server 配置 |
| `plugin` | array | npm 插件包名列表 |
| `command` | object | 自定义命令（TUI 里 `/name` 调用） |
| `formatter` | bool / object | 代码格式化。`true` 启用内置；对象可禁用内置或加自定义 |
| `lsp` | bool / object | LSP 服务器。`true` 启用；对象可禁用或加自定义 |
| `share` | string | 分享模式：`"manual"`（默认）/ `"auto"` / `"disabled"` |
| `snapshot` | bool | 是否启用快照（默认启用）。大仓库/多 submodule 卡顿时可关，但关了就无法回滚 |
| `autoupdate` | bool / string | `true`（默认自动更新）/ `false` / `"notify"`（只提醒）。注意包管理器安装的（如 Homebrew）不适用 |
| `compaction` | object | 上下文压缩：`auto`（默认 true）、`prune`（默认 false，删旧工具输出省 token）、`reserved`（压缩时预留的 token 缓冲） |
| `watcher` | object | 文件监听忽略模式，如 `{"ignore": ["node_modules/**", "dist/**", ".git/**"]}` |
| `server` | object | `serve` / `web` 的服务配置 |
| `shell` | string | 交互终端与 Agent 工具调用用的 shell（如 `pwsh`），不指定则按 OS 自动选 |
| `attachment` | object | 图片附件处理：`auto_resize`、`max_width`、`max_height`、`max_base64_bytes` |
| `disabled_providers` | array | 禁用某些自动加载的 Provider。**优先级高于 `enabled_providers`** |
| `enabled_providers` | array | Provider 白名单，设置后只用列出的 |
| `experimental` | object | 实验特性（不稳定，随时可能变） |

#### `server` 子项

| 项 | 说明 |
|:---|:---|
| `port` | 监听端口 |
| `hostname` | 监听主机名。启用 mdns 且未设 hostname 时默认 `0.0.0.0` |
| `mdns` | 是否启用 mDNS 服务发现（让同网设备发现你的 server） |
| `mdnsDomain` | 自定义 mDNS 域名，默认 `opencode.local`（同网跑多实例时有用） |
| `cors` | 额外允许的 CORS 来源，必须是完整 origin（scheme + host + 可选 port），如 `https://app.example.com` |

#### `provider` 子项

| 项 | 说明 |
|:---|:---|
| `options.timeout` | 请求超时（毫秒），默认 `300000`；设 `false` 禁用 |
| `options.headerTimeout` | 等待响应头的超时（毫秒），默认 `300000`。头到了就停，不限制流式响应体；设 `false` 禁用 |
| `options.chunkTimeout` | 流式响应块之间的超时（毫秒），默认 `300000`。超时未收到块则中断；设 `false` 禁用 |
| `options.setCacheKey` | 确保为该 Provider 始终设置 cache key |
| `options.apiKey` | API Key，支持 `{env:XXX}` / `{file:path}` 变量替换 |
| `options.baseURL` | 自定义端点（自建推理服务用） |
| `options.region` / `profile` / `endpoint` | Amazon Bedrock 专用：区域 / AWS profile / VPC endpoint（`endpoint` 优先级高于 `baseURL`） |

**Bedrock 示例**：

```json
{
  "provider": {
    "amazon-bedrock": {
      "options": {
        "region": "us-east-1",
        "profile": "my-aws-profile",
        "endpoint": "https://bedrock-runtime.us-east-1.vpce-xxxxx.amazonaws.com"
      }
    }
  }
}
```

> Bedrock 的 Bearer token（`AWS_BEARER_TOKEN_BEDROCK` 或 `/connect`）优先于 profile 认证。

#### `permission` 子项

| 权限键 | 管制的工具 | 支持细粒度对象 |
|:---|:---|:---|
| `read` | `read` | ✅ |
| `edit` | `write` `edit` `apply_patch` | ✅ |
| `glob` | `glob` | ✅ |
| `grep` | `grep` | ✅ |
| `list` | `list` | ✅ |
| `bash` | `bash` | ✅ |
| `task` | `task`（子 Agent） | ✅ |
| `external_directory` | 读写项目工作区外文件的所有工具 | ✅ |
| `todowrite` | `todowrite` `todoread` | ❌ 仅简写 |
| `webfetch` | `webfetch` | ❌ |
| `websearch` | `websearch` | ❌ |
| `lsp` | `lsp` | ✅ |
| `skill` | `skill` | ✅ |
| `question` | `question`（执行中提问） | ❌ |
| `doom_loop` | 同一工具用相同输入重复 3 次时的恢复提示 | ❌ |

**默认值**：大多数权限默认 `"allow"`；`doom_loop` 和 `external_directory` 默认 `"ask"`；`read` 是 `"allow"` 但 `.env` 系列默认拒绝：

```json
{
  "permission": {
    "read": {
      "*": "allow",
      "*.env": "deny",
      "*.env.*": "deny",
      "*.env.example": "allow"
    }
  }
}
```

**通配符规则**：`*` 匹配任意字符（含空），`?` 匹配单个字符，其他字符字面匹配。`~` 和 `$HOME` 开头的模式会做家目录展开。

**匹配顺序**：按模式匹配，**最后一条命中的规则生效**。所以常见写法是把兜底 `"*"` 放最前，具体规则放后面。

#### `compaction` 子项

| 项 | 默认 | 说明 |
|:---|:---|:---|
| `auto` | `true` | 上下文满了自动压缩 |
| `prune` | `false` | 删除旧工具输出以省 token |
| `reserved` | - | 压缩用的 token 缓冲，避免压缩过程本身溢出 |

#### `attachment.image` 子项

| 项 | 默认 | 说明 |
|:---|:---|:---|
| `auto_resize` | `true` | 超限图片自动缩放；设 `false` 则超限直接拒绝 |
| `max_width` | `2000` | 最大宽度（像素），超出则缩放或拒绝 |
| `max_height` | `2000` | 最大高度（像素） |
| `max_base64_bytes` | `5242880` | base64 载荷上限（不是原文件大小） |

#### TUI 专属配置（`tui.json`）

TUI 设置单独放 `~/.config/opencode/tui.json`（或项目里的 `tui.json`），用 `OPENCODE_TUI_CONFIG` 可指定自定义路径。

```json
{
  "$schema": "https://opencode.ai/tui.json",
  "scroll_speed": 3,
  "scroll_acceleration": { "enabled": true },
  "diff_style": "auto",
  "cursor": { "style": "block", "blinking": true },
  "mouse": true,
  "theme": "tokyonight",
  "attention": {
    "enabled": true,
    "notifications": true,
    "sound": true,
    "volume": 0.4
  },
  "keybinds": { "command_list": "ctrl+p" }
}
```

| 项 | 说明 |
|:---|:---|
| `theme` | 主题名 |
| `keybinds` | 快捷键，与内置默认**合并**，只需写要改的 |
| `cursor.style` | `"default"` 时恢复终端默认光标，此时 `cursor.blinking` 无效 |
| `attention` | 桌面通知与提示音 |
| `scroll_speed` / `scroll_acceleration` / `diff_style` / `mouse` | 滚动与 diff 显示行为 |

> `opencode.json` 里的旧版 `theme` / `keybinds` / `tui` 键已废弃，会尽可能自动迁移到 `tui.json`。

#### `formatter` 示例

```json
{
  "formatter": {
    "prettier": { "disabled": true },
    "custom-prettier": {
      "command": ["npx", "prettier", "--write", "$FILE"],
      "environment": { "NODE_ENV": "development" },
      "extensions": [".js", ".ts", ".jsx", ".tsx"]
    }
  }
}
```

#### `lsp` 示例

```json
{
  "lsp": {
    "typescript": { "disabled": true }
  }
}
```

#### 变量替换

| 语法 | 说明 |
|:---|:---|
| `{env:VAR_NAME}` | 替换为环境变量值；未设置则替换为空字符串 |
| `{file:path/to/file}` | 替换为文件内容。路径可相对配置文件，或以 `/` `~` 开头 |

```json
{
  "model": "{env:OPENCODE_MODEL}",
  "provider": {
    "anthropic": {
      "options": { "apiKey": "{env:ANTHROPIC_API_KEY}" }
    }
  },
  "instructions": ["./custom-instructions.md"]
}
```

> 把密钥放独立文件（`{file:~/.secrets/openai-key}`）比自己写进配置更安全。

### 2.8 Agent 配置参数

| 参数 | 必填 | 说明 |
|:---|:---|:---|
| `description` | ✅ | Agent 用途描述（决定子 Agent 何时被自动调用） |
| `mode` | | `primary` / `subagent` / `all` |
| `model` | | 覆盖模型。不设时：主 Agent 用全局配置，子 Agent 用调用它的主 Agent 的模型 |
| `prompt` | | 系统提示词文件，支持 `{file:./prompts/xxx.txt}`；路径相对配置文件 |
| `temperature` | | 0.0-1.0。`0.0-0.2` 聚焦确定（分析/规划）、`0.3-0.5` 平衡、`0.6-1.0` 创意发散。不设则用模型默认（多数为 0，Qwen 类通常 0.55） |
| `steps` | | Agent 最大迭代步数；达到上限会收到系统提示要求总结并列出剩余任务。不设则持续迭代到模型停止或用户中断 |
| `disable` | | `true` 禁用该 Agent |
| `permission` | | 该 Agent 的权限，与全局合并且 **Agent 规则优先** |
| `tools` | | **已废弃**，改用 `permission`。`true` 等价 `{"*": "allow"}`，`false` 等价 `{"*": "deny"}`；支持 `mymcp_*` 之类通配 |

> 旧字段 `maxSteps` 已废弃，用 `steps`。

**JSON 定义 Agent**：

```json
{
  "agent": {
    "build": {
      "mode": "primary",
      "model": "anthropic/claude-sonnet-4-20250514",
      "prompt": "{file:./prompts/build.txt}",
      "permission": { "edit": "allow", "bash": "allow" }
    },
    "plan": {
      "mode": "primary",
      "model": "anthropic/claude-haiku-4-20250514",
      "permission": { "edit": "deny", "bash": "deny" }
    },
    "code-reviewer": {
      "description": "审查代码最佳实践与潜在问题",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-20250514",
      "prompt": "你是代码审查者，关注安全、性能、可维护性。",
      "permission": { "edit": "deny" }
    }
  }
}
```

**Markdown 定义 Agent**（`~/.config/opencode/agents/` 或 `.opencode/agents/`，**文件名即 Agent 名**）：

```markdown
---
description: 审查代码质量与最佳实践
mode: subagent
model: anthropic/claude-sonnet-4-20250514
temperature: 0.1
permission:
  edit: deny
  bash: deny
---
你处于代码审查模式，关注：
- 代码质量与最佳实践
- 潜在 Bug 与边界情况
- 性能影响
- 安全考量
只给建设性反馈，不做直接修改。
```

### 2.9 MCP Server 配置

#### 本地 MCP

| 项 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| `type` | string | ✅ | 必须为 `"local"` |
| `command` | array | ✅ | 启动 MCP server 的命令与参数，如 `["npx","-y","my-mcp-command"]` |
| `cwd` | string | | MCP 进程工作目录，相对路径从 workspace 解析 |
| `environment` | object | | 环境变量 |
| `enabled` | boolean | | 是否启动时启用 |
| `timeout` | number | | 拉取工具列表的超时（毫秒），默认 `5000` |

#### 远程 MCP

| 项 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| `type` | string | ✅ | 必须为 `"remote"` |
| `url` | string | ✅ | 远程 MCP server 地址 |
| `enabled` | boolean | | 是否启用 |
| `headers` | object | | 请求头（如 `Authorization`） |
| `oauth` | object / false | | OAuth 配置；设 `false` 关闭自动 OAuth（改用 API Key 等） |
| `timeout` | number | | 拉取工具列表超时（毫秒），默认 `5000` |

```jsonc
{
  "mcp": {
    "mcp_everything": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-everything"],
      "enabled": true
    },
    "my-remote-mcp": {
      "type": "remote",
      "url": "https://my-mcp-server.com",
      "enabled": true,
      "headers": { "Authorization": "Bearer MY_API_KEY" }
    },
    "my-oauth-server": {
      "type": "remote",
      "url": "https://mcp.example.com/mcp",
      "oauth": {
        "clientId": "{env:MY_MCP_CLIENT_ID}",
        "clientSecret": "{env:MY_MCP_CLIENT_SECRET}",
        "scope": "tools:read tools:execute"
      }
    }
  }
}
```

**OAuth 行为**：OpenCode 检测到 401 会自动发起 OAuth 流程，支持动态客户端注册（RFC 7591），token 存在 `~/.local/share/opencode/mcp-auth.json`。

> **注意**：MCP server 会往上下文里塞工具定义，工具多了很吃 token。像 GitHub MCP 这种很容易撑爆上下文，**按需启用，不要全开**。

### 2.10 自定义命令配置

| 项 | 说明 |
|:---|:---|
| `template` | prompt 模板（必填），内容发给 LLM |
| `description` | TUI 里显示的描述 |
| `agent` | 用哪个 Agent 执行 |
| `model` | 覆盖模型 |
| `subtask` | 是否作为子任务执行 |

**模板占位符**：

| 语法 | 说明 |
|:---|:---|
| `$ARGUMENTS` | 全部参数 |
| `$1` `$2` `$3` … | 位置参数 |
| `!command` | 注入 bash 命令输出 |
| `@file` | 文件引用 |

```markdown
---
description: 创建一个新组件
---
创建一个名为 $ARGUMENTS 的 React 组件，用 TypeScript，包含完整类型和基础结构。
```

```markdown
---
description: 在目录 $2 下创建文件 $1，内容为 $3
---
创建文件 $1 在目录 $2 下，内容为：$3
```

调用：`/create-file config.json src "{ \"key\": \"value\" }"`

### 2.11 Rules（AGENTS.md）与指令优先级

| 位置 | 作用域 |
|:---|:---|
| `<project>/AGENTS.md` | 项目级（当前目录及子目录生效），**建议提交到 Git** |
| `~/.config/opencode/AGENTS.md` | 全局个人规则（不入库、不共享） |
| `<project>/CLAUDE.md` | Claude Code 兼容回退（无 AGENTS.md 时才用） |
| `~/.claude/CLAUDE.md` | Claude Code 兼容回退 |

**查找优先级**：先按当前目录向上遍历找 `AGENTS.md` / `CLAUDE.md`（同类中第一个命中的胜出，即 `AGENTS.md` 优先于 `CLAUDE.md`），然后全局 `~/.config/opencode/AGENTS.md`，最后 `~/.claude/CLAUDE.md`。

**关闭 Claude Code 兼容**：

```bash
export OPENCODE_DISABLE_CLAUDE_CODE=1          # 全部关闭
export OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1   # 只关 ~/.claude/CLAUDE.md
export OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1   # 只关 .claude/skills
```

**`instructions` 配置**（复用已有规则，含 glob 和远程 URL）：

```json
{
  "instructions": [
    "CONTRIBUTING.md",
    "docs/guidelines.md",
    ".cursor/rules/*.md",
    "packages/*/AGENTS.md",
    "https://raw.githubusercontent.com/my-org/shared-rules/main/style.md"
  ]
}
```

> `instructions` 里的文件会与 `AGENTS.md` **合并**（不是替换）。远程 URL 5 秒超时。

### 2.12 Skills（SKILL.md）

**放置位置**（OpenCode 会逐个查找）：

| 位置 | 说明 |
|:---|:---|
| `.opencode/skills/<name>/SKILL.md` | 项目 |
| `~/.config/opencode/skills/<name>/SKILL.md` | 全局 |
| `.claude/skills/<name>/SKILL.md` | Claude 兼容（项目） |
| `~/.claude/skills/<name>/SKILL.md` | Claude 兼容（全局） |
| `.agents/skills/<name>/SKILL.md` | agents 兼容（项目） |
| `~/.agents/skills/<name>/SKILL.md` | agents 兼容（全局） |

**frontmatter 字段**（只认这几个，未知字段忽略）：

| 字段 | 必填 | 约束 |
|:---|:---|:---|
| `name` | ✅ | 1-64 字符，小写字母数字 + 单个连字符分隔，不以 `-` 开头/结尾，不含连续 `--`，且必须与所在目录名一致。正则：`^[a-z0-9]+(-[a-z0-9]+)*$` |
| `description` | ✅ | 1-1024 字符，要足够具体以便 Agent 正确选择 |
| `license` | | 可选 |
| `compatibility` | | 可选 |
| `metadata` | | 可选，string→string 映射 |

> Skill 加载是**按需**的：Agent 先看到 skill 的名字和描述，需要时再调 `skill({name: "..."})` 加载全文。这比把全文塞进 system prompt 省很多 token。

### 2.13 环境变量全表

| 变量 | 类型 | 说明 |
|:---|:---|:---|
| `OPENCODE_AUTO_SHARE` | boolean | 自动分享会话 |
| `OPENCODE_GIT_BASH_PATH` | string | Windows 上 Git Bash 可执行文件路径 |
| `OPENCODE_CONFIG` | string | 自定义配置文件路径 |
| `OPENCODE_TUI_CONFIG` | string | 自定义 TUI 配置文件路径 |
| `OPENCODE_CONFIG_DIR` | string | 自定义配置目录（会像 `.opencode` 一样查找 agents/commands/plugins） |
| `OPENCODE_CONFIG_CONTENT` | string | 内联 JSON 配置内容 |
| `OPENCODE_DISABLE_AUTOUPDATE` | boolean | 关闭自动更新检查 |
| `OPENCODE_DISABLE_PRUNE` | boolean | 关闭旧数据清理 |
| `OPENCODE_DISABLE_TERMINAL_TITLE` | boolean | 关闭终端标题自动更新 |
| `OPENCODE_PERMISSION` | string | 内联 JSON 权限配置 |
| `OPENCODE_DISABLE_DEFAULT_PLUGINS` | boolean | 关闭默认插件 |
| `OPENCODE_DISABLE_LSP_DOWNLOAD` | boolean | 关闭 LSP 自动下载 |
| `OPENCODE_DISABLE_CLAUDE_CODE` | - | 关闭全部 `.claude` 兼容支持 |
| `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` | - | 只关 `~/.claude/CLAUDE.md` |
| `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` | - | 只关 `.claude/skills` |
| `OPENCODE_SERVER_PASSWORD` | string | server Basic Auth 密码 |
| `OPENCODE_SERVER_USERNAME` | string | server Basic Auth 用户名（默认 `opencode`） |
| `OPENCODE_PORT` | number | 端口（Desktop 也会读它） |

> 变量清单以 `opencode --help` 与官方文档为准，版本间可能增减。

### 2.14 数据与日志位置

| 内容 | 路径 |
|:---|:---|
| 凭证（API Key、OAuth token） | `~/.local/share/opencode/auth.json` |
| 应用数据根目录 | `~/.local/share/opencode/` |
| 日志 | `~/.local/share/opencode/log/`（保留最近 10 个，文件名带时间戳） |
| 会话/消息数据 | `~/.local/share/opencode/project/`；Git 仓库内则在 `./<project-slug>/storage/`，非 Git 项目在 `./global/storage/` |
| MCP OAuth token | `~/.local/share/opencode/mcp-auth.json` |
| npm 插件缓存 | `~/.cache/opencode/node_modules/` |
| 桌面应用缓存 | `~/.cache/opencode`（Linux/macOS） |
| Windows 日志/数据 | `%USERPROFILE%\.local\share\opencode\` |

---

## 第三部分：最佳实践

### 3.1 落地前的三条底线

```text
底线 1: 权限从紧到松, 不要一上来全 allow
  默认配置大多数权限是 allow, 出厂即"全权"
  生产环境第一步应该是收窄: bash 改 ask, 危险命令 deny

底线 2: 规则和配置进 Git, 个人偏好留本地
  团队共享: opencode.json / AGENTS.md / .opencode/
  个人私有: ~/.config/opencode/opencode.json

底线 3: 密钥不入库
  用 {env:VAR} 或 {file:~/.secrets/xxx}, 不放明文
  .env 默认已被 read 权限拒绝, 别手动放开
```

### 3.2 分环境配置模板

#### 个人开发环境（宽松，效率优先）

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "small_model": "anthropic/claude-haiku-4-5",
  "autoupdate": "notify",
  "share": "manual",
  "permission": {
    "*": "allow",
    "read": {
      "*": "allow",
      "*.env": "deny",
      "*.env.*": "deny",
      "*.env.example": "allow",
      "**/secrets/**": "deny",
      "**/*.pem": "deny",
      "**/id_rsa*": "deny"
    },
    "bash": {
      "*": "allow",
      "git push *": "ask",
      "git commit *": "ask",
      "curl *": "ask"
    }
  },
  "compaction": { "auto": true, "prune": true, "reserved": 10000 },
  "watcher": { "ignore": ["node_modules/**", "dist/**", ".git/**", "**/*.log"] }
}
```

#### 团队项目配置（入库，统一规范）

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "small_model": "anthropic/claude-haiku-4-5",
  "default_agent": "build",
  "subagent_depth": 1,
  "share": "manual",
  "instructions": ["CONTRIBUTING.md", "docs/coding-standards.md", "packages/*/AGENTS.md"],
  "permission": {
    "edit": "allow",
    "bash": {
      "*": "ask",
      "git status*": "allow",
      "git diff*": "allow",
      "git log*": "allow",
      "grep *": "allow",
      "ls *": "allow",
      "cat *": "allow",
      "npm run lint*": "allow",
      "npm run test*": "allow",
      "npm run build*": "allow",
      "rm -rf *": "deny",
      "git push *": "deny",
      "git push --force*": "deny",
      "curl * | *sh": "deny"
    },
    "webfetch": "ask",
    "websearch": "ask"
  },
  "agent": {
    "plan": {
      "mode": "primary",
      "model": "anthropic/claude-sonnet-4-5",
      "permission": { "edit": "deny", "bash": { "*": "ask" } }
    },
    "code-reviewer": {
      "description": "代码审查，只读不改",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-5",
      "temperature": 0.1,
      "prompt": "{file:./prompts/code-review.txt}",
      "permission": {
        "edit": "deny",
        "webfetch": "deny",
        "bash": { "git diff*": "allow", "git log*": "allow", "grep *": "allow", "*": "deny" }
      }
    },
    "security-auditor": {
      "description": "安全审计：检查密钥泄露、注入风险、越权",
      "mode": "subagent",
      "temperature": 0.1,
      "prompt": "你是安全审计者。检查：硬编码密钥、SQL 注入、命令注入、路径穿越、越权访问、依赖漏洞。只报告，不修改。",
      "permission": { "edit": "deny", "bash": "deny" }
    }
  }
}
```

#### CI / 无人值守环境（严格，可复现）

```json
{
  "$schema": "https://opencode.ai/config.json",
  "autoupdate": false,
  "share": "disabled",
  "snapshot": false,
  "model": "{env:OPENCODE_MODEL}",
  "permission": {
    "read": { "*": "allow", "*.env*": "deny" },
    "edit": { "*": "deny", "src/**": "allow", "tests/**": "allow", "docs/**": "allow" },
    "bash": {
      "*": "deny",
      "npm run test*": "allow",
      "npm run lint*": "allow",
      "npm run build*": "allow",
      "git diff*": "allow",
      "git status*": "allow"
    },
    "external_directory": "deny",
    "webfetch": "deny",
    "websearch": "deny",
    "task": "deny"
  },
  "agent": {
    "ci-fixer": {
      "description": "修复 CI 失败，改动范围受限",
      "mode": "primary",
      "steps": 20,
      "permission": { "edit": { "src/**": "allow", "tests/**": "allow", "*": "deny" } }
    }
  }
}
```

> CI 里还要注意：`share: "disabled"` 防止代码外泄；`snapshot: false` 省磁盘；用 `--auto` 时**显式 deny 的规则依然生效**（auto 只影响原本要 ask 的请求）。

### 3.3 AGENTS.md 怎么写才有效

**坏榜样（写了等于没写）**：

```markdown
# 项目说明
这是一个 Node.js 项目，请写出高质量代码。
```

**好榜样（可执行、可验证、有坑点）**：

```markdown
# 订单服务 (order-service)

## 构建 / 测试 / 校验
- 安装依赖: `pnpm install`（**必须用 pnpm，不要用 npm，会破坏 workspace 锁文件**）
- 跑测试: `pnpm test`（全量）/ `pnpm test -- src/order/*.spec.ts`（单文件）
- 类型检查: `pnpm typecheck`（提交前必须过）
- Lint: `pnpm lint --fix`
- 完整校验（等价 CI）: `pnpm verify` ← 改完代码跑这个

## 项目结构
- `src/domain/`     领域模型，纯逻辑，**禁止引入框架依赖**
- `src/application/` 用例编排，事务边界在这层
- `src/infra/`      数据库、消息队列、外部 API 适配
- `src/api/`        HTTP 入口，只做参数校验和转换
- `migrations/`     DB 变更，**新增必须按时间戳命名**

## 约定
- 分层依赖只能从外向内：`api → application → domain`，反向依赖用接口倒置
- 所有 DB 访问走 repository，禁止在 application 层直接写 SQL
- 金额一律用 `Decimal`，禁止 float
- 时间统一 UTC 存储，展示层再转时区
- 新增公开 API 必须同时更新 `docs/openapi.yaml`

## 坑点
- 本地跑集成测试前要先 `docker compose up -d postgres`，否则会连到空库报错
- `src/infra/mq/consumer.ts` 里的重试逻辑和历史遗留耦合，改动前先看 `docs/mq-retry.md`
- 不要执行 `pnpm db:reset`，会清掉本地开发数据（无备份）

## 提交前自查
1. `pnpm verify` 通过
2. 新增/修改的逻辑有对应测试
3. 没有提交调试用的 `console.log` / `TODO: TEMP`
```

**写作要点**：

| 要点 | 说明 |
|:---|:---|
| 命令要精确 | 写清"怎么装、怎么测、怎么验"，含**必须用哪个包管理器** |
| 写反直觉的坑 | Agent 最容易踩的是"看起来对但项目不这么干"的地方 |
| 分层和边界 | 明确哪些目录能依赖哪些，防止它把框架代码塞进领域层 |
| 别写成文档 | 长篇架构说明价值低，**可执行规则 + 坑点**价值高 |
| 用 `/init` 起步 | 先跑 `/init` 生成草稿，再人工删改——比手写快 |
| 提交到 Git | 团队共享，新人（和 AI）第一天就按同一套规矩干活 |

### 3.4 Agent 编排实践

#### 用 plan → build 两阶段替代"一句话让它改完"

```text
反模式:
  "帮我把支付模块重构成事件驱动"
  → Agent 直接改 20 个文件, 你想回滚都来不及

推荐流程:
  ① Tab 切到 plan
     "分析支付模块当前结构, 给出改造成事件驱动的方案,
      包括涉及的模块、风险点、迁移步骤, 不要改代码"
  ② 检查方案, 提反馈迭代 2-3 轮
     "第 3 步的兼容性方案有问题, 老接口要保留 30 天"
  ③ Tab 切回 build
     "按上面的方案执行第 1-2 步"
  ④ /undo 兜底: 单步不满意随时撤销
```

#### 子 Agent 的合理分工

| 场景 | 用什么 | 原因 |
|:---|:---|:---|
| 快速摸清陌生代码库 | `@explore` | 只读、快、不污染工作区 |
| 并行研究多个问题 | `@general` | 可并行，有完整工具权限 |
| 研究上游依赖实现 | `@scout` | 克隆依赖到受控缓存，不碰你的 workspace |
| 代码审查 | 自定义 `code-reviewer`（`edit: deny`） | 杜绝"审查时顺手改了代码" |
| 安全审计 | 自定义 `security-auditor`（`edit/bash: deny`） | 纯报告，避免误操作 |

#### 成本控制：用 `steps` 设上限

```json
{
  "agent": {
    "quick-fix": {
      "description": "小修复，不做大重构",
      "steps": 5,
      "temperature": 0.2,
      "prompt": "只做最小改动修复问题。不要重构，不要改无关文件。"
    }
  }
}
```

达到 `steps` 上限时，Agent 会收到系统提示，要求总结已完成工作并列出剩余任务——这比"跑到 token 烧完"可控得多。

#### 模型分层：贵模型干难活，便宜模型干杂活

```json
{
  "model": "anthropic/claude-sonnet-4-5",
  "small_model": "anthropic/claude-haiku-4-5",
  "agent": {
    "plan": { "model": "anthropic/claude-sonnet-4-5" },
    "quick-fix": { "model": "anthropic/claude-haiku-4-5" },
    "deep-refactor": { "model": "anthropic/claude-opus-4-5" }
  }
}
```

配合 `opencode stats --models --days 30` 定期看模型成本分布。

### 3.5 权限安全实践

#### 按"危险程度"分层的 deny 清单

```json
{
  "permission": {
    "bash": {
      "*": "ask",

      "rm -rf /*": "deny",
      "rm -rf ~*": "deny",
      "rm -rf .*": "deny",
      ":(){ :|:& };:": "deny",
      "dd if=* of=/dev/*": "deny",
      "mkfs*": "deny",
      "chmod -R 777 /*": "deny",
      "> /dev/sda*": "deny",
      "shutdown*": "deny",
      "reboot*": "deny",

      "git push*": "deny",
      "git push --force*": "deny",
      "git reset --hard*": "ask",
      "git clean -*": "ask",

      "curl * | bash": "deny",
      "curl * | sh": "deny",
      "wget * | bash": "deny",

      "npm publish*": "deny",
      "kubectl delete*": "deny",
      "kubectl apply*": "ask",
      "terraform apply*": "ask",
      "terraform destroy*": "deny",
      "aws *delete*": "deny"
    },
    "read": {
      "*": "allow",
      "**/.env": "deny",
      "**/.env.*": "deny",
      "**/*.pem": "deny",
      "**/*.key": "deny",
      "**/id_rsa*": "deny",
      "**/credentials*": "deny",
      "**/.aws/**": "deny",
      "**/.ssh/**": "deny",
      "**/secrets/**": "deny"
    },
    "external_directory": "ask",
    "webfetch": "ask",
    "doom_loop": "ask"
  }
}
```

> **规则顺序很重要**：**最后命中的规则生效**。所以 `"*"` 兜底放最前，具体规则放后面。

#### 用 Agent 做"只读审查员"

```markdown
---
description: 代码审查，绝不修改
mode: subagent
temperature: 0.1
permission:
  edit: deny
  webfetch: deny
  bash:
    "*": deny
    "git diff*": allow
    "git log*": allow
    "grep *": allow
---
只审查不修改。输出格式：
1. 阻塞性问题（必须改）
2. 建议改进（可选）
3. 亮点（值得保留的做法）
每条附文件路径 + 行号 + 理由。
```

#### 危险操作前先 `--dry-run` 类检查

```text
把这类规则写进 AGENTS.md:
  "执行任何删除、迁移、发布命令前, 先展示将要执行的命令和影响范围, 等我确认"
  "数据库变更必须先生成 SQL 并展示, 不要直接执行"

这类指令 + bash 权限的 ask 组合, 是防止 AI 误删数据最便宜的双保险。
```

### 3.6 上下文与成本优化

| 手段 | 做法 | 效果 |
|:---|:---|:---|
| **及时 compact** | 长会话用 `/compact`（或让它自动触发） | 避免上下文溢出、降低单请求成本 |
| **开启 prune** | `"compaction": {"prune": true}` | 删旧工具输出，省 token |
| **控制 MCP 数量** | 只启用当前任务需要的 MCP | MCP 工具定义很吃上下文 |
| **用 skills 代替常驻指令** | 大段流程写进 `SKILL.md`，按需加载 | 比塞 system prompt 省很多 |
| **用 `@` 精确引用** | 引用具体文件而非"看整个项目" | 减少无关文件扫描 |
| **设 `steps` 上限** | 给低成本 Agent 限步数 | 防失控迭代 |
| **模型分层** | `small_model` + Agent 级 `model` | 杂活走便宜模型 |
| **定期看 stats** | `opencode stats --models --days 30` | 定位成本大头 |
| **`watcher.ignore` 排除噪音** | 忽略 `node_modules` / `dist` / `*.log` | 减少无效索引 |
| **大仓库关 snapshot** | `"snapshot": false` | 省磁盘；代价是失去 `/undo` 回滚 |

**自适应成本策略示例**：

```text
简单问答 / 查代码     → cheap model
日常开发             → 主力模型 (sonnet 级)
架构重构 / 难题攻坚   → 顶级模型 (opus 级, 按需)
批量重复任务         → cheap model + steps 限制
```

### 3.7 团队协作与规范化

#### 哪些该进 Git、哪些留本地

| 文件 | 进 Git | 说明 |
|:---|:---|:---|
| `<project>/opencode.json` | ✅ | 团队统一模型、权限、Agent 定义 |
| `AGENTS.md` | ✅ | 项目规则，新人第一天就受益 |
| `.opencode/agents/*.md` | ✅ | 自定义 Agent |
| `.opencode/commands/*.md` | ✅ | 自定义命令 |
| `.opencode/skills/**` | ✅ | 项目技能包 |
| `.opencode/plugins/**` | ✅ | 项目插件 |
| `~/.config/opencode/opencode.json` | ❌ | 个人偏好 |
| `~/.config/opencode/AGENTS.md` | ❌ | 个人习惯 |
| `auth.json` / `mcp-auth.json` | ❌ **绝不出库** | 含密钥与 token |
| `.env` | ❌ | 已被 read 权限默认拒绝 |

#### 企业级强制配置（managed settings）

要给全公司强制统一（用户不可覆盖），用托管配置：

| 平台 | 路径 |
|:---|:---|
| Linux | `/etc/opencode/` |
| macOS | `/Library/Application Support/opencode/` |
| Windows | `%ProgramData%\opencode` |

放一个 `opencode.json` / `opencode.jsonc` 进去即可，需要管理员权限写入，用户改不了。

**macOS 还能用 MDM 下发**（Jamf / Kandji / FleetDM），用 `ai.opencode.managed` preference domain：

```xml
<key>PayloadType</key>
<string>ai.opencode.managed</string>
<key>share</key>
<string>disabled</string>
<key>server</key>
<dict><key>hostname</key><string>127.0.0.1</string></dict>
<key>permission</key>
<dict>
  <key>*</key><string>ask</string>
  <key>bash</key>
  <dict>
    <key>*</key><string>ask</string>
    <key>rm -rf *</key><string>deny</string>
  </dict>
</dict>
```

验证是否生效：

```bash
opencode debug config    # 解析后的配置里能看到 managed 键, 且无法被用户配置覆盖
```

#### 自定义命令沉淀团队流程

```markdown
<!-- .opencode/commands/review-pr.md -->
---
description: 按团队清单审查当前分支改动
agent: code-reviewer
---
审查 `!git diff main...HEAD --stat` 列出的改动，按团队清单逐项检查：
1. 是否有硬编码密钥或连接串
2. 错误处理是否完整（不能只 log 不处理）
3. 是否有 N+1 查询
4. 新增接口是否有鉴权
5. 数据库变更是否可回滚
输出：阻塞项 / 建议项 / 已符合项。
```

调用：`/review-pr`。这样团队的最佳实践就被固化成一个命令，不依赖人的记性。

### 3.8 CI/CD 集成

#### 非交互跑一次审查（GitHub Actions 概念示例）

```bash
# 1) 用环境变量注入密钥（不要写进配置）
export OPENCODE_MODEL="anthropic/claude-sonnet-4-5"
export ANTHROPIC_API_KEY="${{ secrets.ANTHROPIC_API_KEY }}"

# 2) 非交互执行，JSON 输出便于后续处理
opencode run \
  --model "$OPENCODE_MODEL" \
  --agent code-reviewer \
  --format json \
  "审查本次 PR 的改动，输出阻塞性问题清单" > review.json

# 3) 提取结论（jq 处理）
jq -r '.events[] | select(.type=="text") | .content' review.json
```

#### 可复现的 CI 要点

```text
□ 固定版本: 用 opencode upgrade <version> 或镜像 tag 锁定, 不要 latest
□ 关自动更新: "autoupdate": false
□ 关分享: "share": "disabled"   ← 防止代码/会话外泄
□ 关快照: "snapshot": false     ← 省磁盘
□ 权限白名单制: bash 默认 deny, 只放 CI 必需命令
□ 密钥走环境变量: {env:VAR} 而不是明文
□ 用 --format json: 结构化输出, 便于门禁判断
□ 超时兜底: 外层加 timeout, 防止 Agent 卡死占用 runner
```

#### 无头服务模式（自研平台集成）

```bash
# 服务端: 起 HTTP server, 设 Basic Auth
export OPENCODE_SERVER_PASSWORD='strong-password'
opencode serve --port 4096 --hostname 127.0.0.1

# 客户端: 复用已运行的 server (避免每次冷启动 MCP)
opencode run --attach http://localhost:4096 \
  --username opencode --password "$OPENCODE_SERVER_PASSWORD" \
  "分析这次构建失败的原因"
```

> HTTP 接口的完整定义见官方 Server 文档。给浏览器客户端用时记得配 `server.cors`（必须是完整 origin）。

### 3.9 排障手册

| 症状 | 排查步骤 |
|:---|:---|
| **启动不了** | ①看日志 `~/.local/share/opencode/log/` ②`opencode --print-logs` 看终端输出 ③`opencode upgrade` 升到最新 |
| **认证失败** | ①TUI 里 `/connect` 重新认证 ②检查 API Key 有效性 ③确认网络能连到 Provider API |
| **模型不可用** | ①确认已认证该 Provider ②核对配置里的模型名（`opencode models` 查准确名称）③有些模型需要特定订阅/权限 |
| **模型列表不对** | `opencode models --refresh` 刷新 models.dev 缓存 |
| **插件导致异常** | ①`--pure` 启动不加载外部插件 ②把 `plugin` 置空 `[]` ③逐个重新启用以定位 |
| **缓存损坏** | 清 `~/.cache/opencode`（含 npm 插件缓存），重启 |
| **Desktop 连不上 server** | ①Server picker 里 Default server 点 Clear ②移除配置里的 `server.port` / `server.hostname` ③检查 `OPENCODE_PORT` 环境变量 |
| **大仓库很卡** | ①`watcher.ignore` 排除 `node_modules` / `dist` ②`"snapshot": false`（代价：失去回滚） |
| **上下文经常满** | ①`/compact` ②`"compaction": {"prune": true}` ③减少启用的 MCP ④把长流程改写成 skills |
| **命令没按预期跑** | 权限模式匹配问题：`"grep *"` 允许"带参数的 grep"，单独的 `"grep"` 会拦住 `grep x file`。带参数的命令要用 `cmd *` 形式 |
| **MCP OAuth 连不上** | `opencode mcp debug <name>` 调试；`opencode mcp auth list` 看认证状态 |
| **Windows 各种怪问题** | 优先改用 WSL；Desktop 需装 WebView2 Runtime |
| **Linux Desktop 白屏** | Wayland 下试 `OC_ALLOW_WAYLAND=1`；不行就换 X11 会话 |
| **复制粘贴不工作(Linux)** | 检查终端模拟器设置；用 `/editor` 走外部编辑器兜底 |

**看解析后的最终配置**（排查"我明明配了怎么没生效"）：

```bash
opencode debug config
```

### 3.10 反模式清单

| # | 反模式 | 为什么危险 | 正确做法 |
|:---|:---|:---|:---|
| 1 | 生产环境用默认权限（全 allow） | Agent 可任意删文件、推代码、改生产 | 从紧开始，`bash` 默认 ask，危险命令 deny |
| 2 | 一句话让它"重构整个模块" | 改动面巨大，无法审查，回滚成本高 | plan 模式先出方案 → 确认 → 分步 build |
| 3 | 把 API Key 写进 `opencode.json` 并提交 | 密钥泄露，可能被刷账单 | `{env:VAR}` 或 `{file:~/.secrets/xxx}`；`auth.json` 绝不入库 |
| 4 | MCP 全开 | 工具定义吃爆上下文，响应变慢变差 | 按任务启用，用完关掉 |
| 5 | 所有任务都用顶级模型 | 成本高得离谱 | 模型分层：杂活用 small_model |
| 6 | AGENTS.md 写成架构文档 | 占上下文还不产生行为约束 | 写命令、坑点、分层边界、提交前自查 |
| 7 | 不设 `steps` 上限 | Agent 死循环烧 token | 低成本 Agent 设 `steps: 5~20` |
| 8 | CI 里用 latest 版本 | 版本漂移导致构建不可复现 | 锁版本；`autoupdate: false` |
| 9 | CI 里开着 share | 代码和会话可能被分享出去 | `"share": "disabled"` |
| 10 | 用 ask 权限但开了 `--auto` 以为万事大吉 | auto 只影响 ask，**deny 依然生效**；反过来以为 deny 会失效也是错的 | 理解 auto 语义：只自动批准"原本要 ask"的 |
| 11 | 让 Agent 直接跑数据库迁移/发布 | 不可逆操作，出问题就是事故 | 这类命令 deny 或强制人工确认 |
| 12 | 把 `/undo` 当版本控制 | 依赖 Git 快照，只覆盖 Agent 的文件改动 | 正常用 Git 分支 + 提交 |
| 13 | 团队各配一套 | 规则不统一，AI 产出风格各异 | 项目配置 + AGENTS.md 入库，托管配置兜底 |
| 14 | 只看输出不看 diff | 漏掉 Agent 顺手改的无关文件 | 每次改动后 `git diff`，用 `/details` 看工具执行细节 |
| 15 | 忽略 `doom_loop` | 同一工具相同输入重复 3 次往往是死循环前兆 | 保持 `ask`，及时介入 |

### 3.11 速查卡

#### 最常用命令

```bash
opencode                          # 启动 TUI
opencode run "..."                # 非交互跑一句
opencode run --continue "..."     # 接着上次会话跑
opencode run --format json "..."  # JSON 输出 (CI 用)
opencode serve --port 4096        # 无头 server
opencode run --attach http://localhost:4096 "..."  # 复用 server
opencode agent list               # 看所有 Agent
opencode models --refresh         # 刷新模型列表
opencode auth list                # 看已认证 Provider
opencode mcp list                 # 看 MCP 状态
opencode session list -n 10       # 最近 10 个会话
opencode stats --days 30 --models 5  # 成本统计
opencode upgrade                  # 升级
opencode debug config             # 看最终合并配置
opencode --pure                   # 不加载插件启动 (排障)
```

#### TUI 高频操作

```text
Tab            切换主 Agent (build ↔ plan)
@              引用文件
@agent         召唤子 Agent (如 @explore)
!cmd           执行 shell 命令并把输出进上下文
/init          生成 AGENTS.md
/connect       连接 Provider
/models        看模型
/new           新会话
/sessions      切换会话
/compact       压缩上下文
/undo /redo    撤销 / 重做
/export        导出对话
/details       看工具执行详情
/help          帮助
ctrl+x q       退出
```

#### 配置文件最小骨架

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "small_model": "anthropic/claude-haiku-4-5",
  "default_agent": "build",
  "autoupdate": "notify",
  "share": "manual",
  "instructions": ["CONTRIBUTING.md"],
  "permission": {
    "read": { "*": "allow", "*.env*": "deny" },
    "edit": "allow",
    "bash": { "*": "ask", "git diff*": "allow", "git status*": "allow", "rm -rf *": "deny", "git push *": "deny" },
    "external_directory": "ask"
  },
  "compaction": { "auto": true, "prune": true },
  "watcher": { "ignore": ["node_modules/**", "dist/**", ".git/**"] }
}
```

#### 上线检查单

```text
□ Provider 已认证 (opencode auth list 有输出)
□ 密钥不落库 ({env:} / {file:} 方式)
□ AGENTS.md 已生成并人工校对, 已提交 Git
□ 项目 opencode.json 已入库, 团队规范统一
□ permission 已从紧: bash 默认 ask, 危险命令 deny
□ 敏感路径 read 已 deny (.env / *.pem / secrets / .ssh)
□ 大仓库 watcher.ignore 已配, snapshot 按需关闭
□ MCP 按需启用, 数量控制在必要范围
□ 自定义 Agent 已定义 (审查 / 安全审计等只读角色)
□ 自定义命令已沉淀团队流程
□ CI 场景: 锁版本 / autoupdate false / share disabled / --format json
□ 成本监控: opencode stats 定期看, Agent 有 steps 上限
□ 团队知道遇到问题的排查路径 (日志位置 / --print-logs / debug config)
```

---

## 附：和其他章节的配合

- 配合 [08_DevOps](../08_DevOps/index.md)：AI 编码 Agent 接入 CI/CD 流水线、代码审查门禁
- 配合 [07_Kubernetes](../07_Kubernetes/index.md)：`serve` 模式在集群里跑无头 Agent 服务
- 配合 [11_AI基础设施](index.md)：自建推理服务作为 provider（`options.baseURL`）接进来
- 配合 [12_AIOps](../12_AIOps/index.md)：Agent 做告警分析与故障初诊
- 配合 [14_安全](../14_安全/index.md)：权限最小化、密钥管理、会话脱敏导出
- 配合 [15_渗透测试](../15_渗透测试/index.md)：AI Agent 的 Prompt 注入面与沙箱隔离

*最后更新: 2026-08-26*
