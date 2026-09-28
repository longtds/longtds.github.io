# OpenAI Codex CLI 实战指南（简介 / 参数说明 / 最佳实践）

> Codex 是 OpenAI 的编码 Agent 家族，涵盖 CLI、IDE 扩展、云端和桌面应用四种形态。核心形态 **Codex CLI** 是一个终端 Agent：读取仓库、修改文件、执行命令，并且用**操作系统级沙箱**（macOS Seatbelt / Linux Landlock+bubblewrap / Windows 原生沙箱）把"它能做什么"变成内核强制的边界，而不是靠模型自觉。本文分三部分：**简介**（它是什么、架构、和同类工具对比）、**参数说明**（CLI 全量参数 + config.toml 配置项 + 沙箱/审批模型 + 环境变量）、**最佳实践**（生产配置模板、权限最小化、exec 自动化、团队强制策略、排障）。
>
> 本文 CLI 参数部分基于**本机实测** `codex-cli 0.157.1` 的 `--help` 输出，配置与安全模型部分基于 OpenAI 官方文档（developers.openai.com/codex、learn.chatgpt.com/docs）。Codex 迭代较快，**具体参数以 `codex --help` 和官方配置 schema 为准**。

---

## 第一部分：简介

### 1.1 Codex 是什么

```text
Codex = OpenAI 的编码 Agent 家族

四种形态:
  ┌──────────────────────────────────────────────────┐
  │  ① Codex CLI       终端 TUI + codex exec 无头模式  │
  │  ② IDE 扩展        VS Code / JetBrains / Cursor   │
  │  ③ Codex cloud     云端隔离容器里跑任务            │
  │  ④ ChatGPT 桌面应用 macOS / Windows / Linux        │
  └──────────────────────────────────────────────────┘

基础信息:
  开源组件        : Codex CLI 有开源部分 (github.com/openai/codex)
  模型            : OpenAI 自研模型 (gpt-6 系列等), 也可接 OSS 本地模型
  配置格式        : TOML (config.toml), 支持 profile 分层
  认证方式        : Sign in with ChatGPT (订阅) 或 API Key
  状态目录        : $CODEX_HOME (默认 ~/.codex)
  沙箱            : OS 原生强制 — Seatbelt / Landlock+bwrap / Windows Sandbox
  审批模型        : on-request / never / granular 三档
  规则语言        : .rules 文件, Starlark 语法 (类 Python)
  核心卖点        : 沙箱是内核强制的, 不是提示词约束
```

### 1.2 与 OpenCode 的关键差异

两者都是终端 AI 编码 Agent，但设计哲学不同。了解差异有助于选型：

| 维度 | Codex CLI | OpenCode |
|:---|:---|:---|
| 出品方 | OpenAI | 开源社区 |
| 模型 | OpenAI 自研为主，可接 OSS 本地模型 | Provider 无关（Models.dev 目录） |
| **安全模型** | **OS 级沙箱**（Seatbelt/Landlock/Windows Sandbox），内核强制 | 权限系统（allow/ask/deny）+ glob，工具层拦截 |
| 权限粒度 | 沙箱模式 + 审批策略 + `.rules` 前缀规则 + 权限配置文件 | permission 键 + glob 模式匹配 |
| 规则匹配单元 | **命令参数列表**（`execvp` 语义），能安全拆分 shell 链 | glob 模式匹配整条命令字符串 |
| 配置文件 | TOML，支持 profile 分层文件 | JSON/JSONC，8 层合并 |
| 网络控制 | 域白名单 + 本地网络代理（SOCKS5/HTTP） | 无内置代理，靠 deny 规则 |
| 子 Agent | 内置 default/worker/explorer + 自定义 TOML | 内置 build/plan/general/explore/scout + MD/JSON |
| 钩子 | hooks.json / inline `[hooks]`，11 种事件 | JS/TS 插件 `tool.execute.before` 等 |
| 云端 | 原生 Codex cloud（隔离容器 + 两阶段运行时） | 无 |
| 团队强制 | `requirements.toml`（管理员可禁 danger 模式、限模型、限 profile） | managed settings（/etc/opencode + MDM） |
| 遥测 | 内置 OpenTelemetry（可接 OTLP） | 无内置 |
| 典型场景 | OpenAI 生态、要 OS 级隔离、要云端委派、企业合规 | 多模型、要自建推理服务、要插件扩展 |

**选型提示**：

```text
选 Codex 的理由:
  ✅ 要内核级隔离（不可被提示注入绕过的边界）
  ✅ 已经在用 ChatGPT/OpenAI 生态（订阅可覆盖额度）
  ✅ 要把任务委派到云（Codex cloud 隔离容器）
  ✅ 企业要强制策略（requirements.toml）与审计（OTel）

选 OpenCode 的理由:
  ✅ 要接多家模型或自建 vLLM 推理端点
  ✅ 要 JS/TS 插件深度定制工具行为
  ✅ 纯开源、可审计、可完全离线
```

### 1.3 架构概览

```text
                 ┌────────────────────────────────────────┐
   入口           │  CLI (TUI) │ IDE 扩展 │ 桌面应用 │ cloud │
                 └────────────────────┬───────────────────┘
                                      │
                 ┌────────────────────▼───────────────────┐
                 │      Codex Core (Rust)                  │
                 │  会话 / Agent 调度 / 工具执行 / 上下文压缩 │
                 └───┬──────────┬──────────┬──────────────┘
                     │          │          │
      ┌──────────────▼──┐  ┌────▼──────┐  ┌▼────────────────┐
      │ Agent 层         │  │ 工具层    │  │ 扩展层           │
      │ default / worker │  │ shell    │  │ MCP servers     │
      │ explorer         │  │ apply_   │  │ hooks (11 事件)  │
      │ 自定义 agent     │  │  patch   │  │ skills          │
      │ (TOML 定义)      │  │ read/web │  │ plugins/apps    │
      └────────┬─────────┘  └────┬─────┘  └─┬──────────────┘
               │                 │           │
      ┌────────▼─────────────────▼───────────▼────────────┐
      │           权限决策层 (两层协同)                     │
      │  ① 沙箱模式  = 技术上能做什么（文件/网络边界）       │
      │  ② 审批策略  = 什么时候必须先问你                  │
      │  ③ .rules   = 命令级前缀规则（allow/prompt/forbid） │
      └────────────────────┬─────────────────────────────┘
                           │
      ┌────────────────────▼─────────────────────────────┐
      │   OS 原生沙箱强制（不是提示词，是内核）             │
      │   macOS: Seatbelt                                 │
      │   Linux/WSL2: Landlock + seccomp + bubblewrap     │
      │   Windows: 原生 Sandbox (elevated/unelevated)     │
      └────────────────────┬─────────────────────────────┘
                           │
      ┌────────────────────▼─────────────────────────────┐
      │   LLM (OpenAI Responses API / OSS 本地 provider)   │
      └──────────────────────────────────────────────────┘
```

**关键认知**：沙箱和审批是**两个独立控制**，协同工作。

```text
沙箱   = 技术边界（哪些文件能写、能不能联网）
审批   = 何时必须停下来问你（越界时的兜底）

改审批策略不会扩大沙箱。
例: 从"问我"改成"自动审查"（auto_review），
    沙箱边界完全不变，只是把"越界请求"从"你审"改成"审查 agent 审"。
```

### 1.4 两种运行模式

| 模式 | 命令 | 特点 |
|:---|:---|:---|
| **交互式 TUI** | `codex` | 全套能力：`/` 斜杠命令、实时 steer、会话恢复、图片附件 |
| **无头非交互** | `codex exec` | 默认 **只读沙箱**；stdout 只输出最终消息，进度走 stderr，适合管道和 CI |

> `codex exec` 的进展信息走 **stderr**，最终结果走 **stdout** —— 这个设计让 `codex exec "..." > out.md` 只拿到干净结果。

### 1.5 安装

```bash
# 1) 官方独立安装脚本 (macOS / Linux)
curl -fsSL https://chatgpt.com/codex/install.sh | sh
# 更新也执行同一条命令

# 2) Windows
powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"

# 3) npm (跨平台)
npm install -g @openai/codex

# 4) Homebrew (macOS)
brew install --cask codex
brew upgrade --cask codex

# 无人值守安装 (脚本化)
curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh
```

**Linux/WSL2 前置条件**：需要 `bubblewrap` 才能用沙箱。

```bash
# Ubuntu / Debian
sudo apt install bubblewrap

# Fedora
sudo dnf install bubblewrap
```

**Ubuntu 24.04 的 AppArmor 坑**（装完 bwrap 仍报"无法创建 user namespace"）：

```bash
sudo apt update
sudo apt install apparmor-profiles apparmor-utils
sudo install -m 0644 \
  /usr/share/apparmor/extra-profiles/bwrap-userns-restrict \
  /etc/apparmor.d/bwrap-userns-restrict
sudo apparmor_parser -r /etc/apparmor.d/bwrap-userns-restrict
# 无需重启即生效
```

> Ubuntu 25.04 起，`apparmor` 包已自带 `bwrap-userns-restrict` 配置，装完 bubblewrap 即可用。
> 最后手段（不推荐，降低系统整体安全性）：`sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0`

### 1.6 三分钟上手

```bash
# 1. 进入项目目录 (Codex 要求 Git 仓库, 非 Git 目录默认降级为只读)
cd /path/to/project

# 2. 启动 (首次会让你选登录方式)
codex
#  → 选 Sign in with ChatGPT, 或配 API Key

# 3. 第一句话 - 先让它了解项目
> Tell me about this project

# 4. 让它生成项目规则文件
> /init          # 生成 AGENTS.md 骨架

# 5. 干活前先确认边界
> /status        # 看当前模型 / 审批策略 / 可写根目录 / 剩余上下文
> /permissions   # 调整"不用问就做什么"

# 6. 改完先自己看 diff
> /diff
```

**Git 检查点很重要**：

```bash
# Codex 会改你的工作树。开工前后各打一个 commit, 出问题能干净回退
git add -A && git commit -m "checkpoint: before codex task"
codex
git add -A && git commit -m "codex: <task>"
```

**非交互一句话**：

```bash
codex exec "summarize the repository structure and list the top 5 risky areas"
```

---

## 第二部分：参数说明

> 下表中的参数均来自本机 `codex-cli 0.157.1` 实测输出。

### 2.1 CLI 命令结构

```text
codex [OPTIONS] [PROMPT]           # 无子命令 → 启动交互式 TUI
codex [OPTIONS] <COMMAND> [ARGS]   # 执行子命令

子命令列表:
  交互类
    exec (别名 e)      非交互执行
    resume             恢复之前的交互会话
    fork               从之前的会话分叉出新会话
    review             非交互跑代码审查
    apply (别名 a)      把 Codex 产生的 diff 用 git apply 打到工作树
    agents             浏览共享 app-server 守护进程上的所有 agent 会话
    queue              给已存在的会话排队一条消息
    archive / unarchive / delete    会话归档 / 取消归档 / 删除
    migrate-rollouts   检查或迁移旧版本地会话到分页线程历史

  配置与账号
    login / logout     登录 / 登出
    mcp                管理外部 MCP server (list/get/add/remove/login/logout)
    plugin             管理插件 (add/list/remove/marketplace)
    features           查看与开关 feature flag (list/enable/disable)
    completion         生成 shell 补全脚本
    update             升级到最新版
    doctor             诊断安装/配置/认证/运行时健康状况
    debug              调试工具 (models / app-server / prompt-input / execpolicy check)
    sandbox            在 Codex 沙箱内跑命令 (macos/linux/windows)
    cloud              [实验] Codex Cloud 任务 (exec/status/list/apply/diff)
    app-server         [实验] 启动 app server 或相关工具
    remote-control     [实验] 管理开启远程控制的 app-server 守护进程
    exec-server        [实验] 启动独立 exec-server 服务
```

### 2.2 全局参数

| 参数 | 说明 |
|:---|:---|
| `-c, --config <key=value>` | 覆盖 `~/.codex/config.toml` 里的配置。支持点号路径（`foo.bar.baz`）；**值按 TOML 解析**，解析失败则当字面字符串。例：`-c model='"gpt-6-sol"'`、`-c sandbox_permissions='["disk-full-read-access"]'`、`-c shell_environment_policy.inherit=all` |
| `--enable <FEATURE>` | 启用一个 feature（可重复）。等价于 `-c features.<name>=true` |
| `--disable <FEATURE>` | 禁用一个 feature（可重复） |
| `--remote <ADDR>` | 把 TUI 接到远端 app server。格式：`ws://host:port`、`wss://host:port`、`unix://`、`unix://PATH` |
| `--remote-auth-token-env <ENV_VAR>` | WebSocket 认证用的 bearer token 所在的环境变量名 |
| `--strict-config` | 配置里出现**当前版本不认识的字段**就报错退出（升级后排查拼写错误很有用） |

> 交互式 `codex` 还额外支持图片附件、`--search`（切到实时联网搜索）等。全局参数大多会传递给子命令。

### 2.3 交互式启动可用的关键参数

| 参数 | 短写 | 说明 |
|:---|:---|:---|
| `--model <MODEL>` | `-m` | 指定模型 |
| `--sandbox <MODE>` | `-s` | 沙箱模式：`read-only` / `workspace-write` / `danger-full-access` |
| `--ask-for-approval <POLICY>` | `-a` | 审批策略：`on-request` / `never` |
| `--cd <DIR>` | `-C` | 指定工作根目录 |
| `--profile <NAME>` | `-p` | 叠加 `$CODEX_HOME/<name>.config.toml` 配置层 |
| `--image <FILE>` | `-i` | 附加图片到首个 prompt |
| `--oss` | | 使用开源 provider（本地模型） |
| `--local-provider <NAME>` | | 指定本地 provider：`lmstudio` 或 `ollama` |
| `--worktree` | | 在新的托管 Git worktree 里跑（并行隔离） |
| `--add-dir <DIR>` | | 额外可写目录 |
| `--search` | | 切到实时联网搜索（默认走缓存的搜索索引） |
| `--dangerously-bypass-approvals-and-sandbox` | `--yolo` | ⚠️ 跳过所有确认且不加沙箱。**极度危险**，仅用于外部已隔离的环境 |
| `--dangerously-bypass-hook-trust` | | ⚠️ 跳过 hook 信任校验直接运行 hook，仅用于已审计过 hook 来源的自动化 |

### 2.4 `codex exec` 参数详解（无头模式）

```bash
codex exec [OPTIONS] [PROMPT]
# 别名: codex e
```

| 参数 | 短写 | 说明 |
|:---|:---|:---|
| `[PROMPT]` | | 初始指令。不给（或用 `-`）则从 stdin 读；stdin 有管道输入且同时给了 prompt 时，stdin 作为附加 `<stdin>` 块 |
| `-m, --model <MODEL>` | `-m` | 模型 |
| `-s, --sandbox <MODE>` | `-s` | 沙箱模式（**默认 `read-only`**） |
| `--ask-for-approval <POLICY>` | `-a` | 审批策略 |
| `--profile <NAME>` | `-p` | 配置 profile |
| `-C, --cd <DIR>` | `-C` | 工作根目录 |
| `-i, --image <FILE>` | `-i` | 附加图片 |
| `--json` | | **stdout 输出 JSONL 事件流**（CI 解析用） |
| `-o, --output-last-message <FILE>` | `-o` | 把最后一条消息写入文件（同时仍打印到 stdout） |
| `--output-schema <FILE>` | | 传入 JSON Schema 文件，约束模型最终响应的结构 |
| `--color <MODE>` | | 颜色：`always` / `never` / `auto`（默认 `auto`） |
| `--ephemeral` | | 不把会话文件持久化到磁盘 |
| `--worktree` | | 在托管 Git worktree 里跑 |
| `--add-dir <DIR>` | | 额外可写目录 |
| `--skip-git-repo-check` | | 允许在非 Git 仓库里跑（默认要求 Git 仓库以防破坏性改动） |
| `--ignore-user-config` | | 不加载 `$CODEX_HOME/config.toml`（认证仍走 `CODEX_HOME`） |
| `--ignore-rules` | | 不加载用户或项目的 `.rules` 文件 |
| `--thread-source <SOURCE>` | | 给新建/分叉线程打来源标记 |
| `--oss` / `--local-provider <NAME>` | | 本地开源 provider |
| `--enable` / `--disable <FEATURE>` | | feature 开关 |
| `-c, --config <key=value>` | `-c` | 单次配置覆盖 |
| `--strict-config` | | 未知配置字段报错 |
| `--dangerously-bypass-approvals-and-sandbox` | | ⚠️ 见上 |
| `--dangerously-bypass-hook-trust` | | ⚠️ 见上 |

**exec 的子命令**：

| 命令 | 说明 |
|:---|:---|
| `codex exec resume [SESSION_ID] [PROMPT]` | 恢复之前的会话继续跑。`--last` 直接取最近的，不给 ID 则用 picker |
| `codex exec fork [SESSION_ID]` | 从已有会话分叉出新会话。`--last` 同上 |
| `codex exec review` | 对当前仓库跑代码审查（参数同 `codex review`） |

**输出格式说明**：

```text
默认:  stderr = 进度流,  stdout = 最终消息
--json: stdout = JSONL 事件流

事件类型: thread.started / turn.started / turn.completed / turn.failed / item.* / error
item 类型: agent_message, reasoning, command_execution, file_change,
          mcp_tool_call, web_search, plan_update 等

示例事件:
  {"type":"thread.started","thread_id":"0199a213-..."}
  {"type":"turn.started"}
  {"type":"item.started","item":{"id":"item_1","type":"command_execution","command":"bash -lc ls","status":"in_progress"}}
  {"type":"item.completed","item":{"id":"item_3","type":"agent_message","text":"Repo contains docs, sdk, and examples directories."}}
  {"type":"turn.completed","usage":{"input_tokens":24763,"cached_input_tokens":24448,"output_tokens":122,"reasoning_output_tokens":0}}
```

### 2.5 `codex review` 参数

| 参数 | 说明 |
|:---|:---|
| `[PROMPT]` | 自定义审查指令（`-` 从 stdin 读） |
| `--uncommitted` | 审查已暂存 + 未暂存 + 未跟踪的改动 |
| `--base <BRANCH>` | 对比指定基分支审查 |
| `--commit <SHA>` | 审查某个 commit 引入的改动 |
| `--title <TITLE>` | 审查摘要里显示的标题（**只能配合 `--commit` 用**） |

> `--uncommitted`、`--base`、`--commit`、自定义 `PROMPT` **四者互斥**，只能选一个。
> Codex 的审查是**只读**的：报告优先级排序的问题，不改你的工作树。

### 2.6 其他常用子命令参数

#### `codex login`

| 参数 / 子命令 | 说明 |
|:---|:---|
| `codex login status` | 查看登录状态 |
| `--with-api-key` | 从 stdin 读 API Key。用法：`printenv OPENAI_API_KEY \| codex login --with-api-key` |
| `--with-access-token` | 从 stdin 读访问令牌 |
| `--device-auth` | 设备码授权流程 |

#### `codex resume` / `codex fork`

| 参数 | 说明 |
|:---|:---|
| `[SESSION_ID]` | 会话 UUID 或会话名（能解析成 UUID 时 UUID 优先）；省略则配合 `--last` |
| `--last` | 直接用最近的会话，不弹 picker |
| `--all` | 显示所有会话（关闭 cwd 过滤，并显示 CWD 列） |
| `--include-non-interactive` | 把非交互会话也纳入 picker 和 `--last` 选择（`resume` 专有） |

#### `codex mcp`

| 命令 | 说明 |
|:---|:---|
| `codex mcp list` / `get` | 列出 / 查看 MCP server 配置 |
| `codex mcp add <NAME> (--url <URL> \| -- <COMMAND>...)` | 添加 MCP server |
| `codex mcp remove` | 移除 |
| `codex mcp login` / `logout` | OAuth 登录 / 登出 |

**`mcp add` 的参数**：

| 参数 | 说明 |
|:---|:---|
| `--env <KEY=VALUE>` | 启动 stdio server 时的环境变量（**只对 stdio 有效**） |
| `--url <URL>` | streamable HTTP MCP server 地址 |
| `--bearer-token-env-var <ENV_VAR>` | bearer token 所在环境变量名（只对 HTTP 有效） |
| `--oauth-client-id <ID>` | 预注册的 OAuth client ID |
| `--oauth-client-registration <auto\|cimd\|dcr>` | OAuth 客户端注册策略 |
| `--oauth-resource <RESOURCE>` | OAuth resource 参数 |

```bash
# stdio server
codex mcp add context7 -- npx -y @upstash/context7-mcp

# stdio + 环境变量
codex mcp add myserver --env FOO=bar --env TOKEN=xxx -- node /path/server.js

# streamable HTTP + bearer token
codex mcp add remote-docs --url https://mcp.example.com/mcp \
  --bearer-token-env-var MY_MCP_TOKEN
```

#### `codex plugin`

| 命令 | 说明 |
|:---|:---|
| `codex plugin add` | 从已配置或远程 marketplace 安装插件 |
| `codex plugin list` | 列出可用插件 |
| `codex plugin remove` | 卸载插件并清理本地缓存 |
| `codex plugin marketplace` | 添加 / 列出 / 升级 / 移除插件 marketplace |

#### `codex features`

| 命令 | 说明 |
|:---|:---|
| `codex features list` | 列出所有 feature 及其阶段与当前生效状态 |
| `codex features enable <name>` | 在 config.toml 里启用 |
| `codex features disable <name>` | 在 config.toml 里禁用 |

**实测输出片段**（0.157.1）：

```text
$ codex features list
apps                                     stable             true
browser_use                              stable             true
computer_use                             stable             true
code_mode                                under development  false
context_management                       under development  false
memories                                 experimental       false
multi_agent                              stable             true
personality                              stable             true
shell_snapshot                           stable             true
unified_exec                             stable             true
...
```

#### `codex doctor`

| 参数 | 说明 |
|:---|:---|
| `--json` | 输出脱敏的机器可读报告 |
| `--summary` | 只显示分组检查行和最终计数 |
| `--all` | 展开详细人类输出里的长列表 |
| `--no-color` / `--ascii` | 禁用颜色 / 用 ASCII 状态标签 |

```bash
$ codex doctor --summary
Codex Doctor v0.157.1 · linux-x86_64

Notes
   ✗ auth         no Codex credentials were found - Run codex login or provide an API key...
   ⚠ websocket    Responses WebSocket failed; HTTPS fallback may still work - Check proxy, VPN...
─────────────────────────────────────────────────────────────
Environment
  ✓ system       en-US
  ✓ disk         sufficient free disk space (22.2 GiB)
  ✓ runtime      npm (...)
  ✓ install      consistent
  ✓ search       file exists (bundled, .../rg)
  ✓ git          git executable found; execution not verified
  ✓ state        state paths and databases are inspectable
Configuration
  ✓ config       loaded
  ✗ auth         no Codex credentials were found
  ✓ mcp          no MCP servers configured
  ✓ sandbox      restricted fs + restricted network · approval OnRequest
Updates
  ✓ updates      update configuration is locally consistent
```

> 排障第一步就跑 `codex doctor`，它把认证、配置、沙箱、MCP、版本一致性一次性体检完。

#### `codex debug`

| 命令 | 说明 |
|:---|:---|
| `codex debug models` | 打印 Codex 看到的模型目录原始 JSON（`--bundled` 只看内置目录，不刷远端） |
| `codex debug prompt-input` | 打印**模型实际看到的** prompt 输入列表 JSON（调试指令发现、上下文拼装） |
| `codex debug app-server` | app server 调试工具 |

#### `codex sandbox`

| 参数 | 说明 |
|:---|:---|
| `-P, --permission-profile <NAME>` | 应用指定的权限配置文件 |
| `-p, --profile <NAME>` | 配置 profile |
| `-C, --cd <DIR>` | 工作目录（用于 profile 解析和命令执行） |
| `--sandbox-state-json <JSON>` | 直接应用 `codex/sandbox-state-meta` 给出的沙箱状态 |
| `--sandbox-state-readable-root <PATH>` | 追加可读根（可重复） |
| `--sandbox-state-disable-network` | 禁止直接网络访问 |
| `--include-managed-config` | 解析显式权限 profile 时包含托管 requirements |

```bash
# 平台相关用法
codex sandbox macos   [--permissions-profile <name>] [--log-denials] [COMMAND]...
codex sandbox linux   [--permissions-profile <name>] [COMMAND]...
codex sandbox windows [--permissions-profile <name>] [COMMAND]...
# 别名: codex sandbox seatbelt / landlock
```

> 想知道某条命令在沙箱里到底能不能跑，用它试——这是验证沙箱配置最直接的办法。

#### 其他

| 命令 | 参数 | 说明 |
|:---|:---|:---|
| `codex cloud exec` | | 不启动 TUI 直接提交云端任务 |
| `codex cloud status/list/diff/apply` | | 查看状态 / 列出任务 / 看 diff / 应用结果 |
| `codex completion [SHELL]` | | 生成补全脚本，`bash`（默认）/`elvish`/`fish`/`powershell`/`zsh` |
| `codex queue` | `--thread <ID>` `--message <TEXT>` | 给已有会话排队一条消息 |
| `codex apply <TASK_ID>` | | 应用 Codex cloud 任务的最新 diff |
| `codex archive/unarchive/delete` | | 按 id 或会话名归档 / 取消归档 / 删除会话 |
| `codex app-server` | `--listen <URL>` `--stdio` `--ws-auth <MODE>` 等 | [实验] app server（stdio / unix / ws 传输） |

### 2.7 TUI 斜杠命令

| 命令 | 说明 |
|:---|:---|
| `/permissions` | 设置"不用问就做什么"（会话内放宽或收紧审批） |
| `/model` | 切换模型（以及 reasoning effort） |
| `/fast` | 切换 Fast 服务档（模型目录支持时才有） |
| `/plan` | 切到 plan 模式（先出方案不实现） |
| `/goal` | 设置 / 编辑 / 暂停 / 恢复 / 查看 / 清除任务目标 |
| `/personality` | 选沟通风格（更简洁 / 更详尽 / 更协作） |
| `/status` | 显示会话配置与 token 用量（当前模型 / 审批策略 / 可写根 / 剩余上下文） |
| `/usage` | 查看账号 token 用量或使用限流重置 |
| `/diff` | 显示 Git diff（含未跟踪文件） |
| `/review` | 让 Codex 审查工作树 |
| `/compact` | 压缩可见对话以释放 token |
| `/clear` | 清屏并开新对话 |
| `/new` | 在同一 CLI 会话内开新对话 |
| `/resume` | 从会话列表恢复 |
| `/fork` | 把当前对话分叉成新对话 |
| `/rename` | 重命名当前对话 |
| `/archive` / `/delete` | 归档（保留转录）/ 彻底删除当前会话 |
| `/init` | 在当前目录生成 `AGENTS.md` 骨架 |
| `/memories` | 配置记忆的注入与生成开关 |
| `/skills` | 浏览并使用 skill |
| `/mcp` | 列出已配置的 MCP 工具（加 `verbose` 看 server 详情） |
| `/mention` | 把文件附加到对话 |
| `/ide` | 把 IDE 上下文（打开的文件、当前选中）带入下一个 prompt |
| `/apps` / `/plugins` | 浏览应用连接器 / 插件 |
| `/hooks` | 查看和管理生命周期 hook，信任新 hook，禁用非托管 hook |
| `/agent`, `/subagents` | 切换活动 agent 线程（看子 agent 的工作） |
| `/approve` | 批准一次被自动审查拒绝的最近操作（重试一次） |
| `/experimental` | 开关实验特性（如网络代理、防休眠） |
| `/ps` / `/stop` | 查看后台终端及输出 / 停止所有后台终端 |
| `/side`, `/btw` | 开一个临时侧边对话（不污染主转录） |
| `/raw` | 切换原始滚动模式（长输出时便于选择复制） |
| `/keymap` / `/vim` | 重映射快捷键 / 切换 Vim 编辑模式 |
| `/theme` / `/statusline` / `/title` | 语法主题 / 状态栏字段 / 终端标题字段 |
| `/import` | 导入 Claude Code 或 Cursor 的配置、项目、对话 |
| `/debug-config` | 打印配置层与 requirements 诊断（排查优先级冲突） |
| `/feedback` / `/logout` | 发送诊断日志 / 登出 |
| `/exit`, `/quit` | 退出 CLI（`/q` 亦可） |

**输入技巧**：

```text
Tab            Codex 正在工作时按 Tab, 把后续 prompt / 斜杠命令 / shell 命令排队到下一轮
              排队的斜杠命令在轮到它执行时才解析
Esc 两次       在空 composer 上按, 编辑上一条用户消息并从该点分叉对话
Ctrl+O        复制最近一条完成的 Codex 输出
Ctrl+C        中断 / 退出
```

### 2.8 config.toml 配置项

**位置与优先级**（从高到低）：

| 顺序 | 来源 |
|:---|:---|
| 1 | CLI 参数与 `-c` 覆盖 |
| 2 | 项目配置 `.codex/config.toml`（从项目根向下走到 cwd，**离 cwd 近的胜出**；仅信任项目加载） |
| 3 | Profile 文件 `~/.codex/<name>.config.toml`（`--profile <name>` 选中） |
| 4 | 用户配置 `~/.codex/config.toml` |
| 5 | 云端托管的 `config.toml` 默认值（登录工作区下发时） |
| 6 | 系统配置 `/etc/codex/config.toml`（Unix） |
| 7 | 内置默认值 |

> **项目配置不能覆盖**这些键（会被忽略）：`openai_base_url`、`chatgpt_base_url`、`model_provider`、`model_providers`、`notify`、`profile`、`profiles`、`otel` 等。provider、通知、遥测类配置请放用户级。

#### 核心配置项

| 配置项 | 类型 | 说明 |
|:---|:---|:---|
| `model` | string | 使用的模型（如 `gpt-6-sol`） |
| `review_model` | string | `/review` 用的模型覆盖（默认用当前会话模型） |
| `model_provider` | string | provider id（默认 `openai`） |
| `openai_base_url` | string | 内置 openai provider 的 base URL 覆盖（接 LLM 代理/网关用） |
| `model_context_window` | number | 上下文窗口 token 数 |
| `model_auto_compact_token_limit` | number | 触发自动历史压缩的 token 阈值 |
| `model_auto_compact_token_limit_scope` | `total` \| `body_after_prefix` | 阈值是否计入完整上下文（默认 `total`）还是只算压缩前缀之后的增量 |
| `oss_provider` | `lmstudio` \| `ollama` | `--oss` 时用的默认本地 provider |
| `model_reasoning_effort` | string | 推理强度（如 `low`/`medium`/`high`） |
| `plan_mode_reasoning_effort` | string | plan 模式的推理强度覆盖 |
| `model_reasoning_summary` | `auto`\|`concise`\|`detailed`\|`none` | 推理摘要风格 |
| `model_verbosity` | `low`\|`medium`\|`high` | 文本详略（GPT-5 家族） |
| `personality` | `none`\|`friendly`\|`pragmatic` | 默认沟通风格 |
| `service_tier` | string | 偏好的服务档（`fast` 映射到请求侧的 priority） |
| `approval_policy` | `on-request` \| `never` \| `{ granular = {...} }` | 审批策略 |
| `approvals_reviewer` | `user` \| `auto_review` | 谁来审审批请求 |
| `sandbox_mode` | `read-only` \| `workspace-write` \| `danger-full-access` | 沙箱模式 |
| `default_permissions` | string | 权限配置文件（beta，与 `sandbox_mode` **互斥**） |
| `web_search` | `cached`\|`indexed`\|`live`\|`disabled` | 联网搜索模式（默认 `cached`） |
| `allow_login_shell` | boolean | 是否允许 shell 工具用 login-shell 语义（默认 true，加固时设 false） |
| `developer_instructions` | string | 注入会话的额外开发者指令 |
| `model_instructions_file` | string (path) | 用文件替换内置基础指令（代替 AGENTS.md） |
| `compact_prompt` | string | 历史压缩 prompt 的内联覆盖 |
| `log_dir` | string (path) | 日志目录（默认 `$CODEX_HOME/log`；显式设置会**额外启用**明文 `codex-tui.log`） |
| `sqlite_home` | string (path) | SQLite 状态库目录 |
| `notify` | array&lt;string&gt; | 通知命令（收到 Codex 的 JSON payload） |
| `check_for_update_on_startup` | boolean | 启动时检查更新（集中管理更新时设 false） |
| `analytics.enabled` | boolean | 本机/本 profile 的遥测开关 |
| `feedback.enabled` | boolean | 是否允许 `/feedback` 提交反馈（默认 true） |
| `skills.max_context_tokens` | integer | 可用 skill 目录的 token 预算（默认模型上下文的 2%，上限 10000） |
| `mcp_optional_startup_grace_ms` | integer | 构建初始工具目录时等待可选 MCP 的共享时长（默认 1000ms） |

#### 沙箱子项

| 配置项 | 说明 |
|:---|:---|
| `sandbox_workspace_write.writable_roots` | `workspace-write` 模式下的额外可写根 |
| `sandbox_workspace_write.network_access` | 是否允许沙箱内出网（默认 **false**） |
| `sandbox_workspace_write.exclude_tmpdir_env_var` | 是否把 `$TMPDIR` 排除出可写根 |
| `sandbox_workspace_write.exclude_slash_tmp` | 是否把 `/tmp` 排除出可写根 |
| `windows.sandbox` | Windows 原生沙箱模式：`elevated`（推荐）/ `unelevated` / `mxc` |

#### 审批策略的 granular 子项

```toml
approval_policy = { granular = {
  sandbox_approval    = true,   # 允许沙箱升级审批弹窗
  rules               = true,   # 允许 execpolicy 规则触发的审批弹窗
  mcp_elicitations    = true,   # 允许 MCP elicitation 弹窗
  request_permissions = false,  # 自动拒绝 request_permissions 工具的弹窗
  skill_approval      = false   # 自动拒绝 skill 脚本审批弹窗
} }
```

> 用法：把**你想被问到的**类别设 `true`，把**希望默认 fail-closed 的**类别设 `false`。

#### Agent / 子 Agent

| 配置项 | 说明 |
|:---|:---|
| `agents.enabled` | 启用多 agent 工具（默认 true） |
| `agents.max_concurrent_threads_per_session` | 同时开启的 subagent 线程上限（不含主线程） |
| `agents.default_subagent_model` | subagent 默认模型 |
| `agents.default_subagent_reasoning_effort` | subagent 默认推理强度 |
| `agents.interrupt_message` | 中断 agent 轮次时是否记录模型可见消息（默认 true） |
| `agents.<name>.description` | 自定义角色说明（Codex 据此决定何时派生该 agent） |
| `agents.<name>.config_file` | 该角色的 TOML 配置层路径 |

#### MCP Server

| 配置项 | 说明 |
|:---|:---|
| `mcp_servers.<id>.command` / `args` | stdio server 的启动命令与参数 |
| `mcp_servers.<id>.env` / `env_vars` | 环境变量 / 额外环境变量白名单 |
| `mcp_servers.<id>.cwd` | server 进程工作目录 |
| `mcp_servers.<id>.url` | streamable HTTP server 地址 |
| `mcp_servers.<id>.auth` | 认证回退：`oauth`（默认）或 `chatgpt` |
| `mcp_servers.<id>.bearer_token_env_var` | bearer token 所在环境变量 |
| `mcp_servers.<id>.http_headers` / `env_http_headers` | 静态 HTTP 头 / 从环境变量填充的头 |
| `mcp_servers.<id>.enabled` | 不删配置的前提下禁用 |
| `mcp_servers.<id>.required` | true 时该 server 初始化失败会导致启动/resume 失败（**CI 里很有用**） |
| `mcp_servers.<id>.startup_timeout_sec` | 启动超时（默认 10s） |
| `mcp_servers.<id>.tool_timeout_sec` | 单工具超时（默认 60s） |
| `mcp_servers.<id>.enabled_tools` / `disabled_tools` | 工具白名单 / 黑名单（黑名单在白名单之后应用） |
| `mcp_servers.<id>.default_tools_approval_mode` | 默认审批：`auto`/`prompt`/`writes`/`approve` |
| `mcp_servers.<id>.tools.<tool>.approval_mode` | 单工具审批覆盖 |
| `mcp_servers.<id>.tools.<tool>.output_token_limit` | 单工具输出的 token 预算 |
| `mcp_servers.<id>.scopes` | OAuth scopes |

#### 网络代理（在沙箱内做域白名单）

```toml
[features.network_proxy]
enabled = true
[features.network_proxy.domains]
"api.openai.com" = "allow"
"*.github.com" = "allow"        # 仅子域
"**.example.com" = "allow"      # 顶级域 + 所有子域
"tracking.example.com" = "deny"
```

| 子项 | 说明 |
|:---|:---|
| `features.network_proxy.enabled` | 是否启用沙箱网络代理（默认 false）。**不开代理，权限配置里的域规则不生效** |
| `features.network_proxy.domains` | 域策略（未配置 = 不允许任何外部目标，需显式加 allow） |
| `features.network_proxy.unix_sockets` | Unix socket 策略 |
| `features.network_proxy.allow_local_binding` | 是否放宽本地/私网访问（默认 false） |
| `features.network_proxy.enable_socks5` / `_udp` | SOCKS5 支持（默认 true） |
| `features.network_proxy.proxy_url` | HTTP 监听地址（默认 `http://127.0.0.1:3128`） |
| `features.network_proxy.socks_url` | SOCKS5 监听地址（默认 `http://127.0.0.1:8081`） |
| `features.network_proxy.dangerously_allow_non_loopback_proxy` | 允许非回环监听地址（默认 false） |
| `features.network_proxy.dangerously_allow_all_unix_sockets` | 允许任意 Unix socket 目标（默认 false） |

#### 常改的 feature flag

| Key | 默认 | 阶段 | 说明 |
|:---|:---:|:---|:---|
| `apps` | true | stable | 应用（连接器）集成 |
| `goals` | true | stable | 持久化目标与自动续跑 |
| `hooks` | true | stable | 生命周期 hook（`hooks.json` 或内联 `[hooks]`） |
| `fast_mode` | true | stable | Fast 模式与服务档选择 |
| `memories` | false | experimental | 记忆 |
| `multi_agent` | true | stable | 子 agent 协作工具 |
| `personality` | true | stable | 沟通风格选择 |
| `shell_snapshot` | true | stable | shell 环境快照（加速重复命令） |
| `shell_tool` | true | stable | 默认 shell 工具 |
| `unified_exec` | true（Windows 除外） | stable | 统一 PTY exec 工具 |
| `network_proxy` | false | experimental | 沙箱网络代理（域白名单生效前提） |
| `enable_request_compression` | true | stable | zstd 压缩流式请求体 |
| `prevent_idle_sleep` | false | experimental | 轮次运行中防休眠 |

#### shell 环境变量策略

```toml
[shell_environment_policy]
ignore_default_excludes = false     # false 时启用对 KEY/SECRET/TOKEN 的自动过滤

[shell_environment_policy.filters]
"PATH" = "include"
"HOME" = "include"
```

> `ignore_default_excludes` 默认 `true`（即**跳过**自动过滤）。想自动过滤名字里含 `KEY`/`SECRET`/`TOKEN` 的变量，要显式设 `false`。

### 2.9 权限配置文件（beta）

三种内置 profile：

| Profile | 说明 |
|:---|:---|
| `:read-only` | 本地命令只读 |
| `:workspace` | 允许在活动 workspace 根和系统临时目录内写入 |
| `:danger-full-access` | 移除本地沙箱限制（**仅在你确实需要时用**） |

**重要约束**：profile 与旧的 sandbox 设置**不组合**。配了 `default_permissions`/`[permissions]` 就**不要**再配 `sandbox_mode`/`[sandbox_workspace_write]`；一旦任何加载的配置里有 `sandbox_mode`、你传了 `--sandbox`、或选中的 profile 设了 `sandbox_mode`，Codex 会**改用旧的 sandbox 设置**并忽略 `default_permissions`。

```toml
default_permissions = "project-edit"

[features]
network_proxy = true

[permissions.project-edit.workspace_roots]
"~/code/app" = true
"~/code/shared-lib" = true

[permissions.project-edit.filesystem]
":minimal" = "read"

[permissions.project-edit.filesystem.":workspace_roots"]
"." = "write"
".devcontainer" = "read"
"**/*.env" = "deny"

[permissions.project-edit.network]
enabled = true

[permissions.project-edit.network.domains]
"api.openai.com" = "allow"
"objects.githubusercontent.com" = "allow"
"*.github.com" = "allow"
"tracking.example.com" = "deny"
```

> `network.enabled = true` 只是**允许**命令联网，**不会**启动代理。要真正强制域规则，还得开 `features.network_proxy = true`（或由管理员托管的 `[experimental_network]` 要求启动）。

Profile 也遵循配置分层：组织级和用户级可以各自往同一个 profile 名下追加条目，不必重述整个 profile。

### 2.10 沙箱与审批组合速查

| 意图 | 参数 / 配置 | 效果 |
|:---|:---|:---|
| **Auto（预设）** | 无参数，或 `--sandbox workspace-write --ask-for-approval on-request` | 可读文件、可改工作区、可跑工作区内命令；**越界编辑或联网需审批** |
| **安全只读浏览** | `--sandbox read-only --ask-for-approval on-request` | 只读沙箱内可读可跑命令；越界操作可能要求审批 |
| **只读非交互（CI）** | `--sandbox read-only --ask-for-approval never` | 只读沙箱内运行，**从不询问** |
| **自动审查模式** | `--sandbox workspace-write --ask-for-approval on-request -c approvals_reviewer=auto_review` | 沙箱边界与标准 on-request 相同，但符合条件的审批请求交给 Auto-review 审 |
| **危险全权** | `--dangerously-bypass-approvals-and-sandbox`（别名 `--yolo`） | ⚠️ 无沙箱、无审批，**不推荐** |

**可写根里的受保护路径**（即使用 `workspace-write`，这些也是只读）：

```text
<writable_root>/.git      受保护 (无论它是目录还是文件)
                          若 .git 是指针文件 (gitdir: ...), 指向的目录也受保护
<writable_root>/.agents   存在为目录时受保护
<writable_root>/.codex    存在为目录时受保护

保护是递归的 —— 这些路径下的一切都只读。
```

> 这就是为什么 `git commit` 常常仍需要审批：`.git/` 是受保护的，写它属于越界。

### 2.11 AGENTS.md 指令发现

**发现顺序**：

```text
1. 全局作用域: $CODEX_HOME (默认 ~/.codex)
   优先 AGENTS.override.md, 否则 AGENTS.md —— 该层只用第一个非空文件

2. 项目作用域: 从项目根 (通常是 Git 根) 向下走到当前工作目录
   逐目录检查: AGENTS.override.md → AGENTS.md → project_doc_fallback_filenames
   每个目录最多纳入一个文件

3. 合并顺序: 从根向下拼接, 用空行分隔
   离当前目录近的文件在 prompt 里靠后 → 覆盖前面的指引
```

**上限**：`project_doc_max_bytes` 默认 **32 KiB**。超了会停止继续添加（空文件跳过）。超限就提高该限制，或把指令拆分到嵌套目录里。

**验证加载了哪些文件**：

```bash
codex --cd services/payments --ask-for-approval never "List the instruction sources you loaded."
```

**排障（看模型实际看到的 prompt）**：

```bash
codex debug prompt-input      # 打印模型可见的 prompt 输入列表 JSON
```

### 2.12 `.rules` 文件（命令前缀规则）

Rules 用来控制**哪些命令能在沙箱外运行**（实验特性）。

**位置**：`rules/` 目录下，紧邻某个活动配置层。

```text
~/.codex/rules/default.rules              用户层
<repo>/.codex/rules/                      项目层 (仅信任项目时加载)
```

**规则语法**（Starlark，类 Python 但无副作用）：

```python
prefix_rule(
    # 匹配的命令前缀 (必填, 非空列表)
    # 元素可以是字面量, 也可以是字面量联合 ["view","list"] 表示该位置是其中任一
    pattern = ["gh", "pr", "view"],

    # 匹配后的动作 (默认 "allow")
    #   allow     — 沙箱外直接跑, 不询问
    #   prompt    — 每次询问
    #   forbidden — 直接拦截, 不询问
    decision = "prompt",

    # 规则原因 (可选), 会出现在审批提示或拒绝消息里
    justification = "Viewing PRs is allowed with approval",

    # 可选内联"单元测试": Codex 加载规则时校验这些例子
    match = [
        "gh pr view 7888",
        "gh pr view --repo openai/codex",
    ],
    not_match = [
        # 不匹配: pattern 必须是精确前缀
        "gh pr --repo openai/codex view 7888",
    ],
)
```

**多规则冲突**：取**最严格**的结果，顺序为 `forbidden` > `prompt` > `allow`。

**通配与注意事项**：

- 添加命令到 TUI 白名单时，Codex 写用户层 `~/.codex/rules/default.rules`
- 开启 Smart approvals（默认）时，Codex 可能在你升级权限时**主动建议**一条 `prefix_rule`——接受前仔细审 pattern
- 管理员可通过 `requirements.toml` 强制下发限制性规则

**shell 包装与复合命令的处理**（这是 Codex 规则系统的关键设计）：

```text
危险场景:
  ["bash", "-lc", "git add . && rm -rf /"]

Codex 对 bash -lc / bash -c 及其 zsh / sh 等价形式特殊处理:

能安全拆分时 → 拆:
  条件是脚本只是"纯词 + 安全操作符(&& / || / ; / |)" 的线性链
  (无变量展开、无 VAR=...、无 $FOO、无通配符)
  → 用 tree-sitter 解析拆成独立命令逐个评估
  上例拆成: ["git","add","."] 和 ["rm","-rf","/"]
  即使你 allow 了 ["git","add"], 也不会放行整条 ——
  因为 rm -rf / 被单独评估, 阻止整体自动放行。
  ⇒ 这正是"危险命令混在安全命令里偷渡"的防线。

不能安全拆分时 → 不拆:
  含重定向(>/>>/<)、命令替换($(...))、环境变量(FOO=bar)、
  通配符(*/?)、控制流(if/for 等)
  → 整个调用当作 ["bash","-lc","<完整脚本>"] 单条评估
```

**测试规则**：

```bash
codex debug execpolicy check --pretty \
  --rules ~/.codex/rules/default.rules \
  -- gh pr view 7888 --json title,body,comments
# 多个 --rules 可叠加; 输出 JSON 含最严格决策和命中的规则及 justification
```

### 2.13 Hooks（生命周期钩子）

**三层结构**：hook 事件 → matcher 组 → 一个或多个 handler。

**支持的事件**：`SessionStart`、`SessionEnd`、`SubagentStart`、`SubagentStop`、`PreToolUse`、`PermissionRequest`、`PostToolUse`、`PreCompact`、`PostCompact`、`UserPromptSubmit`、`Stop`、`Interrupt`。

**配置文件**：`hooks.json`，或 config.toml 里内联 `[hooks]`。

```json
{
  "description": "Optional lifecycle hooks for this workspace.",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.codex/hooks/session_start.py",
            "statusMessage": "Loading session notes",
            "additionalContextLimit": 5000
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/pre_tool_use_policy.py\"",
            "statusMessage": "Checking Bash command"
          }
        ]
      }
    ],
    "Stop": [
      { "hooks": [
        { "type": "command",
          "command": "python3 ~/.codex/hooks/stop_continue.py",
          "timeout": 30 }
      ] }
    ]
  }
}
```

**handler 字段**：

| 字段 | 说明 |
|:---|:---|
| `type` | `command` 或 MCP tool hook（`prompt`/`agent` 类型会被解析但跳过） |
| `command` | 要执行的命令 |
| `statusMessage` | TUI 里显示的状态文本 |
| `timeout` | 超时（秒） |
| `additionalContextLimit` | 单个 handler 的 token 阈值：超限的 `additionalContext` 存盘，只给模型短预览。默认 2500；`0` 表示全文直传模型 |
| `async` | 后台执行不阻塞触发操作（默认 false；**`SessionEnd` 总是同步**） |
| `commandWindows` | Windows 专用命令覆盖（TOML 别名 `command_windows`） |

**安全**：hook 需要**信任**才能运行。`/hooks` 里查看、信任或禁用；`--dangerously-bypass-hook-trust` 可跳过校验（仅用于已审计来源的自动化）。

### 2.14 自定义 Agent（subagent）

**内置 agent**：

| Agent | 用途 |
|:---|:---|
| `default` | 通用兜底 |
| `worker` | 执行导向：实现与修复 |
| `explorer` | 重读取的代码库探索 |

**自定义位置**：`~/.codex/agents/*.toml`（个人）或 `.codex/agents/*.toml`（项目）。

**必填字段**：`name`、`description`、`developer_instructions`。识别以 `name` 字段为准（文件名对齐只是惯例）。

```toml
# .codex/agents/pr-explorer.toml
name = "pr_explorer"
description = "Read-only codebase explorer for gathering evidence before changes are proposed."
model = "gpt-6-luna"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
Stay in exploration mode.
Trace the real execution path, cite files and symbols, and avoid proposing fixes unless the parent agent asks for them.
Prefer fast search and targeted file reads over broad scans.
"""
```

> 自定义 agent 文件本质是**配置层**，可以覆盖 `model`、`model_reasoning_effort`、`sandbox_mode`、`mcp_servers`、`skills.config` 等会话配置。
> 自定义 agent 名与内置冲突时，**你的定义优先**。

### 2.15 环境变量全表

| 变量 | 用途 | 说明 |
|:---|:---|:---|
| `CODEX_HOME` | CLI/IDE/app-server/安装器 | Codex 状态根目录（配置、认证、日志、会话、skills、独立包元数据）。**默认 `~/.codex`，若设置该目录必须已存在** |
| `CODEX_SQLITE_HOME` | CLI 与 app-server 状态 | SQLite 状态库位置。`sqlite_home` 配置项优先。相对路径从 cwd 解析 |
| `CODEX_NON_INTERACTIVE` | 安装脚本 | 设 `1`/`true`/`yes` 跳过安装器交互（提示取默认值）。**用于脚本化安装/更新，不用于首次配置** |
| `CODEX_INSTALL_DIR` | 安装脚本 | 可见 `codex` 命令的安装位置（macOS/Linux 默认 `~/.local/bin`）。独立包缓存仍在 `CODEX_HOME/packages/standalone` |
| `CODEX_API_KEY` | exec、review、TS SDK、remote exec-server | 给非交互进程提供 API Key。跑仓库可控代码时**应内联设置**而非设为 job 级环境变量 |
| `CODEX_ACCESS_TOKEN` | CLI、app-server、可信自动化 | ChatGPT/Codex 访问令牌。持久登录用 `codex login --with-access-token` |
| `OPENAI_FEDERATION_RULE_ID` | 工作负载身份 | 选择为该工作负载配置的 federation 规则 |
| `OPENAI_IDENTITY_TOKEN_FILE` | 工作负载身份 | 指向当前 OIDC token 或 SPIFFE JWT-SVID 文件的绝对路径 |
| `OPENAI_WORKLOAD_IDENTITY_CONTEXT` | 工作负载身份 | 可选的有界 JSON 标识符，供客户端上报审计归因（不影响认证授权） |
| `CODEX_CA_CERTIFICATE` | HTTPS/登录/WebSocket | 企业 TLS 拦截或私有根证书场景的 PEM CA bundle 路径。**优先级高于 `SSL_CERT_FILE`** |
| `SSL_CERT_FILE` | HTTPS/登录/WebSocket | `CODEX_CA_CERTIFICATE` 未设时的回退 CA bundle 路径 |
| `RUST_LOG` | CLI 与 app-server | Rust 日志过滤与详细度。`codex exec` 默认 `error`。取值：`error`/`warn`/`info`/`debug`/`trace`，也支持定向过滤如 `codex_core=debug,codex_tui=debug` |

**provider 的 API Key 环境变量名不固定**——由 model provider 配置里的 `env_key` 指定。

### 2.16 状态文件位置

```text
$CODEX_HOME  (默认 ~/.codex)
  ├─ config.toml                    本地配置
  ├─ auth.json                      文件式凭证存储时的凭证 (或走 OS keychain)
  ├─ history.jsonl                  开启历史持久化时的历史
  ├─ log/                           日志 (codex-tui.log 需显式设 log_dir 才生成)
  ├─ rules/default.rules            用户层规则
  ├─ agents/*.toml                  自定义 agent
  ├─ <name>.config.toml             profile 文件
  └─ packages/standalone/           独立安装包缓存
```

> `auth.json` 要当**密码**对待：含访问令牌，不要提交、不要贴到工单或聊天里。

---

## 第三部分：最佳实践

### 3.1 落地前的四条底线

```text
底线 1: 理解"沙箱 ≠ 审批"
  沙箱是技术边界, 审批是越界时是否打断你。
  调审批不会扩大沙箱; 关沙箱才是真的把门拆了。

底线 2: 只在 Git 仓库里干活
  Codex 建议版本控制目录用 Auto 模式, 非 Git 目录默认 read-only。
  非 Git 目录能跑但默认只读 —— 这是设计, 不是 bug。

底线 3: 开工前后打 Git 检查点
  Codex 直接改工作树。checkpoint commit 是最便宜的回退手段。

底线 4: 永远不要在生产机 / 有真实凭证的机器上用 --yolo
  正确做法: 需要无限制时, 用容器或隔离 CI runner 提供外部隔离。
```

### 3.2 三套分环境配置模板

#### A. 个人开发环境（效率优先，仍有基本防护）

```toml
# ~/.codex/config.toml
model = "gpt-6-sol"
model_reasoning_effort = "medium"
personality = "pragmatic"        # 取值: none | friendly | pragmatic
sandbox_mode = "workspace-write"
approval_policy = "on-request"
allow_login_shell = false        # 加固: shell 工具不用 login shell

# 沙箱内允许出网 (默认是关的)
[sandbox_workspace_write]
network_access = true
exclude_slash_tmp = false

# 只放行当前项目 + 依赖目录, 不放开整台机器
# writable_roots = ["~/.pyenv/shims"]

[features]
network_proxy = true             # 想用域白名单就必须开

[features.network_proxy.domains]
"api.openai.com" = "allow"
"*.github.com" = "allow"
"registry.npmjs.org" = "allow"
"pypi.org" = "allow"
"*.pypi.org" = "allow"

[history]
persistence = "save-all"

# 更新提示而非静默更新 (集中管理时可设 false)
check_for_update_on_startup = true
```

#### B. 团队项目配置（入库，统一规范）

```toml
# <repo>/.codex/config.toml
# 注意: 不能放 provider/认证/遥测类键, 那些会被忽略

model = "gpt-6-sol"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
allow_login_shell = false

[sandbox_workspace_write]
network_access = false           # 项目级: 默认不出网, 要联网的任务让用户临时开

[agents]
enabled = true
max_concurrent_threads_per_session = 4
default_subagent_model = "gpt-6-luna"
default_subagent_reasoning_effort = "medium"

# 项目工具: 只暴露团队需要的
[mcp_servers.team-docs]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
enabled = true
required = true                  # 初始化失败就报错, 不静默降级
startup_timeout_sec = 20

[mcp_servers.team-docs.tools."resolve-library-id"]
approval_mode = "auto"
```

#### C. CI / 无人值守（严格，可复现）

```toml
# ci/.codex/config.toml 或通过 -c 内联传
sandbox_mode = "read-only"        # CI 默认只读; 需要改文件才升 workspace-write
approval_policy = "never"
check_for_update_on_startup = false
allow_login_shell = false

[sandbox_workspace_write]
network_access = false            # CI 默认不出网

[features]
memories = false                  # 不生成记忆
personality = false
rollout_budget = { enabled = true, limit_tokens = 500000 }  # 成本上限

[analytics]
enabled = false
```

### 3.3 沙箱与审批怎么选

**决策树**：

```text
这个任务需要改文件吗?
├─ 不需要 (只看/只审查/只出方案)
│   → --sandbox read-only --ask-for-approval on-request
│     还要更安静 → -a never
│
└─ 需要
    ├─ 改的是当前仓库内文件
    │   → --sandbox workspace-write --ask-for-approval on-request  (Auto)
    │     嫌审批太吵但想保留边界 → 加 approvals_reviewer=auto_review
    │     在隔离容器里 → 可以直接 -a never
    │
    └─ 需要改仓库外文件 / 需要出网
        → 不要用 --yolo。改为:
          ① workspace-write + network_access=true + 域白名单, 或
          ② --add-dir 精确追加可写目录, 或
          ③ 权限配置文件精确开权限
```

**常见误用**：

| 错误做法 | 问题 | 正确做法 |
|:---|:---|:---|
| 一上来就 `--yolo` | 无沙箱无审批，破坏不可逆 | 先用 Auto，确实被挡了再精确放宽 |
| CI 里用 `--dangerously-bypass-approvals-and-sandbox` | runner 上跑仓库可控代码 = 任意执行 | 用 `--sandbox read-only` 起步，需要写才升 workspace-write |
| 把 `.env` 放进可写根还开着网络 | 密钥可被外传 | 域白名单 + 只读项目根 + 密钥走 CI secret |
| 以为设了 `network_access = true` 就有域限制 | 只开了出网，**没开代理就没有域规则** | 同时设 `features.network_proxy = true` |
| 同时配 `sandbox_mode` 和 `default_permissions` | profile 被静默忽略 | 二选一，见 2.9 |

### 3.4 AGENTS.md 怎么写才有效

**结构建议**（四块，缺一不可）：

```markdown
# <项目名>

## 常用命令（精确到可复制粘贴）
- 安装依赖: `pnpm install`      # 必须用 pnpm, 别用 npm
- 跑测试: `pnpm test`            # 单文件: `pnpm test -- src/order/*.spec.ts`
- 类型检查: `pnpm typecheck`
- Lint: `pnpm lint --fix`
- 完整校验（等价 CI）: `pnpm verify`  ← 改完代码跑这个

## 项目结构与边界
- `src/domain/`      纯领域逻辑, 禁止引入框架依赖
- `src/application/` 用例编排, 事务边界在这层
- `src/infra/`       DB / 消息队列 / 外部 API 适配
- `src/api/`         HTTP 入口, 只做校验和转换
- 依赖方向只能是 api → application → domain

## 坑点（写那些"看起来对但本仓库不这么干"的地方）
- 跑集成测试前要先 `docker compose up -d postgres`, 否则连到空库
- 不要执行 `pnpm db:reset`, 会清掉本地开发数据且无备份
- `src/infra/mq/consumer.ts` 的重试逻辑与历史遗留耦合, 改前先看 `docs/mq-retry.md`

## 提交前自查
1. `pnpm verify` 通过
2. 新逻辑有对应测试
3. 没有遗留 `console.log` / `TODO: TEMP`
```

**分层放置**：

```text
~/.codex/AGENTS.md                  全局: 所有仓库都适用的工作约定
~/.codex/AGENTS.override.md         临时全局覆盖 (不改基文件, 删掉即恢复)

<repo>/AGENTS.md                    仓库级规范
<repo>/services/payments/AGENTS.override.md   团队专属覆盖 (优先级最高)
```

> 每个目录只取一个文件，且 `AGENTS.override.md` 优先于 `AGENTS.md`。

**要点与坑**：

| 要点 | 说明 |
|:---|:---|
| 命令要精确 | 写清装/测/验，含**必须用哪个包管理器** |
| 写反直觉的坑 | 这是 Agent 最容易踩的地方，价值最高 |
| 别写成架构文档 | 长篇说明价值低，**可执行规则 + 坑点**价值高 |
| 合并上限 32 KiB | 超了后面的文件被丢弃。拆分到嵌套目录或用 `project_doc_max_bytes` 提高 |
| 用 `/init` 起步 | 生成草稿后**人工删改**，比手写快 |
| 验证生效 | `codex debug prompt-input` 看模型实际拿到的 prompt |
| 提交到 Git | 团队共享，新人和 AI 第一天就按同一套规矩干活 |

### 3.5 用 `.rules` 编排命令权限

**推荐的一条完整规则文件**（`~/.codex/rules/default.rules`）：

```python
# ── 只读且频繁的命令: 直接放行, 减少审批疲劳 ──────────────
prefix_rule(
    pattern = ["git", ["status", "diff", "log", "show", "branch"]],
    decision = "allow",
    justification = "Read-only git inspection is safe outside the sandbox",
    match = ["git status", "git diff HEAD~1", "git log --oneline -20"],
    not_match = ["git push"],
)

prefix_rule(
    pattern = ["rg"],
    decision = "allow",
    justification = "ripgrep is read-only",
)

# ── 有副作用但常见的命令: 每次问 ────────────────────────
prefix_rule(
    pattern = ["git", ["commit", "push", "reset", "clean"]],
    decision = "prompt",
    justification = "History-mutating git operations need explicit approval",
)

prefix_rule(
    pattern = ["gh", "pr", "view"],
    decision = "prompt",
    justification = "Viewing PRs is allowed with approval",
    match = ["gh pr view 7888", "gh pr view --repo openai/codex"],
    not_match = ["gh pr --repo openai/codex view 7888"],   # pattern 必须是精确前缀
)

# ── 明确禁止: 直接拦截, 连审批都不给 ─────────────────────
prefix_rule(
    pattern = ["rm", "-rf"],
    decision = "forbidden",
    justification = "Use targeted deletions; broad recursive removal is blocked",
)

prefix_rule(
    pattern = ["git", "push", "--force"],
    decision = "forbidden",
    justification = "Force push is forbidden; open a PR instead",
)

prefix_rule(
    pattern = ["kubectl", "delete"],
    decision = "forbidden",
    justification = "Use GitOps to remove resources instead of imperative delete",
)

prefix_rule(
    pattern = ["terraform", "destroy"],
    decision = "forbidden",
    justification = "Production teardown must go through change management",
)

prefix_rule(
    pattern = ["npm", "publish"],
    decision = "forbidden",
    justification = "Publishing goes through the release pipeline",
)
```

**组合效果示例**：

```text
用户/Codex 请求: bash -lc "git add . && rm -rf /"

Codex 能安全拆分 → 拆为:
  ["git", "add", "."]      → 无匹配规则, 走默认
  ["rm", "-rf", "/"]       → 命中 forbidden

最终: 整条 invocation 被拦截 (最严格决策胜出)
⇒ 危险命令无法藏在安全命令后面偷渡
```

**测试规则再上线**：

```bash
codex debug execpolicy check --pretty \
  --rules ~/.codex/rules/default.rules \
  -- git push --force origin main
# 期望输出: 最严格决策 = forbidden, 并附上 justification
```

### 3.6 `codex exec` 自动化实战

#### 基础用法

```bash
# 进度走 stderr, 结果走 stdout
codex exec "generate release notes for the last 10 commits" | tee release-notes.md

# 不持久化会话文件
codex exec --ephemeral "triage this repository and suggest next steps"

# 管道输入作为附加上下文 (prompt 仍是指令)
curl -s https://example.com/data.json \
  | codex exec "format the top 20 items into a markdown table" \
  > table.md
```

#### 机器可读输出

```bash
# JSONL 事件流
codex exec --json "summarize the repo structure" | jq

# 关键事件字段
#   thread.started  → thread_id
#   turn.completed  → usage{input_tokens, cached_input_tokens, output_tokens, reasoning_output_tokens}
#   item.completed  → item{type: agent_message | command_execution | file_change | ...}

# 只取最终消息 (同时仍打印到 stdout)
codex exec "explain the auth flow" -o /tmp/answer.md
```

#### 结构化输出（下游消费）

```json
// schema.json
{
  "type": "object",
  "properties": {
    "project_name": { "type": "string" },
    "programming_languages": { "type": "array", "items": { "type": "string" } },
    "risk_areas": { "type": "array", "items": { "type": "string" } }
  },
  "required": ["project_name", "programming_languages"],
  "additionalProperties": false
}
```

```bash
codex exec "Extract project metadata and risk areas" \
  --output-schema ./schema.json \
  -o ./result.json
# 输出严格符合 schema 的 JSON, 可直接喂给下游步骤
```

#### 分阶段流水线

```bash
# 第一阶段: 审查发现问题
codex exec "review the change for race conditions"

# 第二阶段: 接着上一个会话修问题
codex exec resume --last "fix the race conditions you found"
```

#### CI 集成要点

```bash
# 只读审查 (不会改工作树)
codex exec --sandbox read-only --ask-for-approval never \
  --json "review the staged changes and output blockers as JSON" > review.json

# 需要改文件时升到 workspace-write
codex exec --sandbox workspace-write --ask-for-approval never \
  "fix the failing lint errors in src/"
```

**CI 检查单**：

```text
□ 沙箱从 read-only 起步, 需要写才升 workspace-write
□ 绝不使用 --dangerously-bypass-approvals-and-sandbox
□ 认证: 优先用官方 Codex GitHub Action (内置 API Key 代理, 减少密钥暴露)
□ 若手动传密钥: 只给 Codex 那一步内联 CODEX_API_KEY, 不要设为 job 级环境变量
   (job 级变量会被构建脚本/测试/依赖生命周期钩子/被攻陷的 action 读到)
□ 锁版本: 不要用 latest
□ check_for_update_on_startup = false
□ [analytics] enabled = false(按合规要求)
□ MCP 用 required = true, 让必需 server 初始化失败时直接报错而非静默降级
□ --output-schema + -o 拿到结构化结果, 便于门禁判断
□ 外层加 timeout, 防止 agent 卡死占住 runner
□ 需要联网的步骤与 Codex 步骤分开, 不给 Codex 步骤网络
```

**GitHub Actions 的推荐模式**（自动修 CI 失败）：

```text
1. 主 CI 失败时触发后续 workflow
2. 用只读权限 checkout 失败的 commit
3. 在 Codex 之前跑环境准备命令 —— 且不向这些步骤暴露 OpenAI API Key
4. 运行官方 Codex GitHub Action
5. 把 Codex 的本地改动存成 patch artifact
6. 在**独立 job** 里应用 patch 并开 PR

权限设计: Codex job 只有 contents: read, 只产出 diff artifact
          open_pr job 有写权限, 但拿不到 OPENAI_API_KEY
```

#### 认证方式

```bash
# 默认: 复用已保存的 CLI 认证

# 单次运行用不同 API Key (内联, 不要 job 级)
CODEX_API_KEY=<api-key> codex exec --json "triage open bug reports"

# CODEX_API_KEY 可用于: codex exec, codex review, TS SDK, codex exec-server --remote

# 想在 CI 里用 ChatGPT 账号额度 (进阶, 企业可信 runner)
#   → 把 auth.json 当密码处理, 走安全存储注入
#   → 绝不要用于公开/开源仓库
```

### 3.7 上下文与成本控制

| 手段 | 做法 | 效果 |
|:---|:---|:---|
| **及时 compact** | 长会话用 `/compact`，或让它自动触发 | 保留要点、释放窗口 |
| **调自动压缩阈值** | `model_auto_compact_token_limit` | 控制何时压缩 |
| **压缩范围选择** | `model_auto_compact_token_limit_scope = "body_after_prefix"` | 只算增量，避免过早压缩 |
| **限制工具输出** | `tool_output_token_limit`（如 12000） | 单次工具输出落盘上限 |
| **限制单 MCP 工具输出** | `mcp_servers.<id>.tools.<tool>.output_token_limit` | 掐住话痨的 MCP 工具 |
| **skills 目录预算** | `skills.max_context_tokens`（默认 2%，上限 10000） | 控制 skill 目录占用 |
| **模型分层** | `model` 主力 + `agents.default_subagent_model` 便宜模型 | 探索/杂活走轻模型 |
| **推理强度分层** | `model_reasoning_effort` + `plan_mode_reasoning_effort` | 难题才给高 effort |
| **给 agent 分角色** | 自定义 agent 指定 model/effort/sandbox | 精确控制每个角色的成本 |
| **用 `--ephemeral`** | CI 里不落盘会话 | 省磁盘 |
| **及时 `/new`** | 换任务就开新会话 | 避免无关历史拖累 |
| **查用量** | `/usage`、`/status` | 看 token 消耗和剩余额度 |
| **设预算上限** | `features.rollout_budget` | 硬性 token 上限 |

**模型分层示例**：

```toml
model = "gpt-6-sol"                          # 主力
model_reasoning_effort = "medium"
plan_mode_reasoning_effort = "high"           # 出方案时多想

[agents]
default_subagent_model = "gpt-6-luna"         # 子 agent 用轻模型
default_subagent_reasoning_effort = "medium"
max_concurrent_threads_per_session = 4        # 并行上限, 也是成本闸门

# 只读探索 agent: 便宜 + 快
# .codex/agents/explorer-fast.toml
#   name = "explorer_fast"
#   model = "gpt-6-luna"
#   model_reasoning_effort = "low"
#   sandbox_mode = "read-only"
```

**预算硬闸**：

```toml
[features.rollout_budget]
enabled = true
limit_tokens = 500000
reminder_interval_tokens = 50000    # 默认 limit 的 10%
```

### 3.8 企业强制与合规

#### 托管要求 `requirements.toml`

管理员可以强制约束，用户无法覆盖。典型用途：

```text
□ 禁止 approval_policy = "never"
□ 禁止 sandbox_mode = "danger-full-access"
□ 限制可用模型
□ 用 allowed_permission_profiles 限定可选权限模式
  (一旦设置, 未列出的 profile 全部拒绝 —— 包括内置的和未来新增的)
□ 强制下发限制性 prefix_rule
□ 托管 hook (managed hooks)
□ 强制网络代理与域白名单 ([experimental_network])
```

> `allowed_permission_profiles` 是例外：它会让 Codex **改用权限配置文件**。
> 部署托管 profile 白名单前，要移除 `sandbox_mode` 和 `[sandbox_workspace_write]` 等旧设置。
> 混合版本灰度期，可临时保留托管的 `allowed_sandbox_modes` 作为兼容约束，
> 直到所有客户端都升到支持权限配置的版本。

#### 统一本地配置

```text
用户层    ~/.codex/config.toml
          ~/.codex/rules/default.rules
          ~/.codex/agents/*.toml

系统层    /etc/codex/config.toml            (Unix)
项目层    <repo>/.codex/config.toml         (仅信任项目加载)
          <repo>/.codex/rules/
          <repo>/.codex/agents/
```

**验证合并结果**：

```bash
# TUI 内
> /debug-config

# 命令行
codex -c log_dir=./.codex-log ... 
codex doctor --summary
```

#### 可观测性（OpenTelemetry）

```toml
[otel]
environment = "production"          # 默认 "dev"
exporter = { otlp-http = {
  endpoint = "https://otel.example.com/v1/logs",
  protocol = "binary",
  headers = { "x-otlp-api-key" = "${OTLP_TOKEN}" }
}}
log_user_prompt = false             # 默认脱敏用户 prompt
```

**主要事件**：`codex.conversation_starts`、`codex.api_request`、`codex.sse_event`、`codex.websocket_request` / `_event`、`codex.user_prompt`（内容默认脱敏）、`codex.tool_decision`（批准/拒绝，以及决策来自配置还是用户）、`codex.tool_result`。

**主要指标**：`codex.api_request`（counter）、`codex.api_request.duration_ms`（histogram）、`codex.sse_event`、`codex.sse_event.duration_ms`、`codex.websocket.request`、`codex.websocket.request.duration_ms`、`codex.websocket.event`。

> 这是**审计的关键面**：`codex.tool_decision` 能回答"谁批准的、是配置放行还是人批的"。

#### 网络与安全加固清单

```text
□ 默认不出网 (sandbox_workspace_write.network_access = false)
□ 需要出网时: 开 network_proxy + 显式域白名单
  (不配 domains 等于不允许任何外部目标, 需逐条加 allow)
□ web_search 用 "cached"（默认）或 "indexed"，避免 "live" 被提示注入
□ allow_login_shell = false
□ shell_environment_policy.ignore_default_excludes = false
  (启用对 KEY/SECRET/TOKEN 命名变量的自动过滤)
□ auto_review.policy 写好组织审查策略
□ 敏感项目在 Dev Container / 隔离 runner 里跑
□ auth.json 走安全存储, 不落明文共享目录
□ 生产集群操作类命令进 .rules 的 forbidden
```

### 3.9 排障手册

| 症状 | 排查步骤 |
|:---|:---|
| **任何异常，先跑** | `codex doctor --summary`（一次体检认证/配置/沙箱/MCP/版本） |
| **登录/认证失败** | ①`codex doctor` 看 auth 检查项 ②`codex login` 重新登录 ③`codex login status` ④CI 里检查 `CODEX_API_KEY` 是否只注入到 Codex 那一步 |
| **WebSocket 连不上（但 HTTPS 还行）** | `codex doctor` 会提示；检查代理、VPN、防火墙、DNS、自定义 CA、WebSocket 策略 |
| **企业 TLS 拦截导致连不上** | 设 `CODEX_CA_CERTIFICATE=/path/ca.pem`（优先于 `SSL_CERT_FILE`） |
| **沙箱报无法创建 user namespace** | Linux/WSL2 装 `bubblewrap`；Ubuntu 24.04 还要额外加载 `bwrap-userns-restrict` AppArmor profile（见 1.5） |
| **某命令在沙箱里跑不通** | `codex sandbox linux --log-denials -- <command>` 看拒了什么；用 `--permissions-profile` 换 profile 试 |
| **想验证沙箱边界** | `codex sandbox <platform> <command>` 直接在里面试跑 |
| **`.git` 相关操作老要审批** | 预期行为：`<writable_root>/.git` 是受保护的只读路径。要免审批就在 `.rules` 里针对性放行 |
| **配置文件改了不生效** | ①`/debug-config` 看配置层与优先级 ②注意项目层会被忽略某些键（provider/认证/遥测） ③加 `--strict-config` 让拼写错误显式报错 |
| **配置字段名写错但不报错** | 加 `--strict-config`，当前版本不认识的字段会直接报错退出 |
| **AGENTS.md 没生效** | ①`codex debug prompt-input` 看真实的 prompt 输入 ②检查 32 KiB 上限 ③确认 override 文件是否意外遮蔽了正常文件 ④非信任项目时项目层不加载 |
| **skills/指令来源不明** | `codex --cd <dir> "List the instruction sources you loaded."` |
| **Agent 找不到项目根** | 项目根靠标记文件识别；确认仓库标记存在，或用 `project_root_markers` 配置 |
| **MCP server 连不上** | ①`codex mcp list` 看状态 ②`codex mcp login <name>` 处理 OAuth ③抬高 `startup_timeout_sec`（默认 10s） ④CI 里设 `required = true` 让它显式失败 |
| **MCP 工具不出现** | 检查 `enabled`、`enabled_tools`/`disabled_tools` 白黑名单 |
| **规则没按预期生效** | `codex debug execpolicy check --pretty --rules <file> -- <command>` 看命中哪条、最终决策是什么 |
| **规则加载失败** | 检查是否用了 Starlark 不支持的语法（不能有副作用）；用 `match`/`not_match` 做自检 |
| **hook 不执行** | hook 需要信任：`/hooks` 里查看并信任；改了内容要重新信任 |
| **子 agent 不派生** | 检查 `agents.enabled`、`agents.max_concurrent_threads_per_session`、以及自定义 agent 的 `description` 是否说清了用途 |
| **上下文总溢出** | `/compact`；调 `model_auto_compact_token_limit`；`tool_output_token_limit`；减少 MCP；关掉不用的 feature |
| **想省 token/钱** | `/usage` 看用量；`/status` 看剩余；给子 agent 配轻模型；给 agent 设 `steps`/effort；开 rollout budget |
| **Windows 各种怪问题** | ①`[windows] sandbox = "elevated"`（推荐）②不行才 `unelevated` ③优先考虑 WSL2 |
| **TUI 渲染/复制异常** | `/raw` 切原始滚动模式；`/theme` 换主题；检查终端模拟器 |
| **需要给支持人员发日志** | `RUST_LOG=debug codex -c log_dir=./.codex-log`，然后看 `./.codex-log/codex-tui.log` |

### 3.10 反模式清单

| # | 反模式 | 为什么危险 | 正确做法 |
|:---|:---|:---|:---|
| 1 | 上来就 `--yolo` | 无沙箱无审批，改动不可逆 | 从 Auto 起，被挡了再精确放宽 |
| 2 | CI 里用 `--dangerously-bypass-approvals-and-sandbox` | 在 runner 上跑仓库可控代码 = 任意执行 | `--sandbox read-only` 起步；需要写升 workspace-write |
| 3 | 把 API Key 设为 job 级环境变量 | 构建脚本/测试/依赖钩子/被攻陷的 action 都能读到 | 只内联到 Codex 那一步；优先用官方 Codex GitHub Action |
| 4 | 同时配 `sandbox_mode` 和 `default_permissions` | profile 被静默忽略，你以为在用的边界没生效 | 二选一 |
| 5 | 开了 `network_access` 就以为有域限制 | 只是开了出网，没开代理就没有域规则 | 同时开 `features.network_proxy = true` |
| 6 | web_search 用 `live` | 提示注入可以直接拉取并遵循恶意页面的指令 | 用默认 `cached` 或 `indexed` |
| 7 | 关掉 `ignore_default_excludes` 的过滤 | 含 KEY/SECRET/TOKEN 的变量被透传给命令 | 显式设 `false` 启用自动过滤 |
| 8 | 让 Codex 直接跑 `git push` / `kubectl delete` / `terraform destroy` | 不可逆的生产操作 | 进 `.rules` 的 `forbidden` |
| 9 | 把 `.rules` 当成提示词写 | Rules 是**命令参数列表**语义，不是自然语言 | 用 `pattern` 精确前缀 + `match`/`not_match` 自检 + `execpolicy check` 验证 |
| 10 | 不写 AGENTS.md，每次口头交代 | 规范和坑点无法复用，AI 产出不一致 | 写可执行的命令 + 坑点，提交 Git |
| 11 | AGENTS.md 写成架构文档 | 占 32 KiB 预算，还不产生行为约束 | 写命令、坑点、边界、自查项 |
| 12 | 把 auth.json 提交或贴到工单 | 等于把令牌公开 | 当密码对待，走安全存储 |
| 13 | 在非 Git 目录里干活还纳闷为什么不能写 | 非版本控制目录默认 read-only（设计如此） | 先 `git init` 或明确用 `--skip-git-repo-check` + 手动配置沙箱 |
| 14 | 用 `/undo` 心态依赖 Codex 自我回滚 | Codex 直接改工作树，没有内置全局回滚 | 开工前后打 Git 检查点 |
| 15 | MCP 全开、工具不限流 | 工具定义吃上下文，话痨工具拖爆窗口 | 按需启用；用 `enabled_tools`/`output_token_limit` 限流 |
| 16 | 所有任务都用最高 effort + 顶配模型 | 成本失控 | 模型与 effort 分层 |
| 17 | 不设预算上限 | 长任务可能烧掉大量额度 | `features.rollout_budget` |
| 18 | 不接 OTel，出了事没有审计记录 | 无法回答"谁批准了什么" | 接 OTLP；关注 `codex.tool_decision` |
| 19 | 让 Codex 在带真实云凭证的开发机上全权跑 | 一次误操作就能动生产 | 隔离容器/沙箱机；生产凭证不进开发机 |
| 20 | 升级后不跑 `--strict-config` | 配置字段悄悄失效，行为静默变化 | 升级后用 `--strict-config` + `codex doctor` 复核 |

### 3.11 速查卡

#### 最常用命令

```bash
codex                                    # 启动 TUI
codex "explain this repo"                # 带首个 prompt 启动
codex -m gpt-6-sol -s workspace-write -a on-request   # 显式指定边界
codex --profile deep-review              # 用 profile
codex -c log_dir=./.codex-log            # 单次覆盖配置
codex --strict-config                    # 未知配置字段直接报错

codex exec "task"                        # 无头执行 (默认只读沙箱)
codex exec --json "task" | jq            # JSONL 输出
codex exec -o out.md "task"              # 最后消息写文件
codex exec --output-schema s.json -o r.json "task"    # 结构化输出
codex exec resume --last "follow up"     # 恢复上一会话继续
codex exec --ephemeral "task"            # 不落盘

codex review --uncommitted               # 审查未提交改动
codex review --base main                 # 对比基分支审查
codex review --commit <SHA> --title "x"  # 审查指定 commit

codex resume --last                      # 恢复最近会话
codex fork --last                        # 从最近会话分叉
codex apply <TASK_ID>                    # 应用云端任务的 diff

codex mcp add <name> -- npx -y <pkg>     # 添加 MCP
codex mcp list                           # 看 MCP 状态
codex features list                      # 看 feature flag
codex doctor --summary                   # 体检
codex debug prompt-input                 # 看模型实际收到的 prompt
codex debug execpolicy check --pretty --rules R -- <cmd>   # 测规则
codex sandbox linux --log-denials -- <cmd>                 # 测沙箱
codex completion zsh > ~/.zsh/completions/_codex           # shell 补全
codex update                             # 升级
```

#### TUI 高频操作

```text
/permissions      调整"不用问就做什么"
/model            换模型
/plan             先出方案
/status           看配置与 token 用量
/usage            看账号用量
/diff             看改动
/review           让 Codex 审工作树
/compact          压缩上下文
/new /clear       开新对话
/resume /fork     恢复 / 分叉
/init             生成 AGENTS.md
/mcp /hooks /skills   看 MCP / hook / skill
/agent            切换子 agent 线程
/approve          批准一次被自动审查拒绝的操作
/debug-config     看配置层优先级
/exit /quit       退出

Tab               排队下一条输入
Esc ×2            编辑上一条消息并分叉
Ctrl+O            复制最近输出
```

#### 最小配置骨架

```toml
# ~/.codex/config.toml
model = "gpt-6-sol"
model_reasoning_effort = "medium"
sandbox_mode = "workspace-write"
approval_policy = "on-request"
allow_login_shell = false
web_search = "cached"                 # 别用 live

[sandbox_workspace_write]
network_access = false                # 需要时才开, 并配 network_proxy 白名单

[features]
network_proxy = false
memories = false

[agents]
default_subagent_model = "gpt-6-luna"
max_concurrent_threads_per_session = 4
```

#### 上线检查单

```text
安装与基础
□ codex doctor --summary 无 ✗
□ Linux/WSL2 已装 bubblewrap（Ubuntu 24.04 已加载 bwrap-userns-restrict）
□ 登录方式确定（ChatGPT 订阅 或 API Key），CI 用 CODEX_API_KEY 或官方 Action

边界与权限
□ 沙箱模式按环境选定（个人 Auto / CI read-only）
□ 审批策略选定（交互 on-request / CI never）
□ 未同时配 sandbox_mode 与 default_permissions
□ 需要出网时: network_access + features.network_proxy + domains 白名单 三者齐备
□ allow_login_shell = false
□ shell_environment_policy 已启用 KEY/SECRET/TOKEN 过滤
□ .rules 里 git push / kubectl delete / terraform destroy / rm -rf 已 forbidden
□ 规则已用 execpolicy check 验证过
□ web_search 不是 live

规则与上下文
□ AGENTS.md 已生成、人工校对、提交 Git
□ 嵌套目录的 override 按需放置，总量未超 32 KiB
□ codex debug prompt-input 确认指令加载正确

自动化
□ CI 锁版本、关自动更新、开 rollout budget
□ CI 用 --output-schema + -o 拿结构化结果
□ CI 步骤有超时兜底
□ 认证密钥只内联到 Codex 那一步

企业合规
□ requirements.toml 下发（禁 never / 禁 danger-full-access / 限模型）
□ 托管 hooks 与域白名单已配置
□ OTel 已接，重点关注 codex.tool_decision 审计面
□ auth.json 走安全存储，不在共享目录
```

---

## 附：和其他章节的配合

- 配合 [08_DevOps](../08_DevOps/index.md)：Codex 接入 CI/CD、自动修 CI 失败、开 PR
- 配合 [41-OpenCode实战指南](41-OpenCode实战指南.md)：同类工具对比选型，可并存（不同任务用不同 Agent）
- 配合 [11_AI基础设施](index.md)：自建推理服务作为 `model_providers` 接入（`base_url` + `env_key`）
- 配合 [07_Kubernetes](../07_Kubernetes/index.md)：`kubectl delete` 类命令进 `.rules` forbidden；K8s 排障用只读沙箱
- 配合 [12_AIOps](../12_AIOps/index.md)：Agent 做告警初诊，OTel 数据进统一可观测栈
- 配合 [14_安全](../14_安全/index.md)：沙箱边界设计、密钥管理、提示注入防护
- 配合 [15_渗透测试](../15_渗透测试/index.md)：AI Agent 的沙箱逃逸面与提示注入攻击面

*最后更新: 2026-09-06*
