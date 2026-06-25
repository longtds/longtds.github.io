# 代码管理

> Git 是开发者的"母语"，但**90% 的人只会 add/commit/push/pull 这四招**。代码管理 = Git 工作流 + 分支策略 + 代码托管平台 + 协作流程 + 安全治理，是 DevOps 第一公里。

## 一、为什么代码管理重要

```
代码管理决定:
  - 团队协作效率（合并冲突、Review 时长）
  - 发布节奏（一周一次 vs 一天 N 次）
  - 故障回滚速度（找到那次提交多久）
  - 知识传承（commit message 就是项目史）
  - 安全合规（谁改了什么、什么时候）
  - 工程文化（PR 文化 / Trunk-Based）

→ 烂的代码管理会拖死再好的 CI/CD
```

## 二、Git 核心概念再梳理

### 2.1 Git 内部模型

```
4 种对象:
  Blob       文件内容
  Tree       目录结构
  Commit     提交（指向 tree + parent commit）
  Tag        标签

3 个区域:
  Working Directory  工作区
  Index/Staging      暂存区
  Repository         本地仓库
  
+ Remote             远程仓库

引用:
  HEAD               当前指向（commit/branch）
  branch             分支引用（指向 commit）
  tag                标签（不可变）
  reflog             本地操作历史（救命）
```

### 2.2 关键命令分层

```
基础（每天用）:
  add commit push pull status diff log

进阶（每周用）:
  branch checkout merge rebase reset
  stash cherry-pick tag

高阶（救命用）:
  reflog reset --hard
  rebase -i (interactive)
  bisect (二分查找)
  filter-branch / filter-repo
  worktree
  submodule / subtree
```

### 2.3 命令速查

```bash
# 配置
git config --global user.name "Your Name"
git config --global user.email "you@company.com"
git config --global core.autocrlf input    # Linux/Mac
git config --global pull.rebase true       # pull 用 rebase
git config --global init.defaultBranch main

# 日志查看
git log --oneline --graph --all --decorate
git log -p path/file                       # 文件历史
git log --author="zhangsan" --since="1 month ago"
git log --grep="bug"
git shortlog -sn                            # 提交者排名

# 比较
git diff                                    # 工作区 vs 暂存区
git diff --staged                           # 暂存区 vs HEAD
git diff main..feature                      # 分支间
git diff main...feature                     # feature 自分叉以来的

# 撤销
git restore <file>                          # 撤销工作区改动
git restore --staged <file>                 # 撤销暂存
git reset --soft HEAD~1                     # 回退保留改动
git reset --mixed HEAD~1                    # 回退保留工作区
git reset --hard HEAD~1                     # 回退完全丢弃 ⚠️
git revert <commit>                         # 反向提交（安全）

# 分支
git switch main                             # 切换
git switch -c feature                       # 创建并切换
git branch -d branch                        # 删除已合并
git branch -D branch                        # 强删
git branch -m old new                       # 重命名

# 合并
git merge feature                           # 普通合并
git merge --squash feature                  # 压缩合并
git merge --no-ff feature                   # 保留合并节点
git rebase main                             # 变基

# 拉取与推送
git fetch --all --prune                     # 抓取并清理失效远程
git pull --rebase origin main
git push origin main
git push --force-with-lease                 # 安全的强推

# 暂存
git stash push -m "WIP"
git stash list
git stash pop / apply / drop
```

## 三、Git 工作流（团队的根本选择）

### 3.1 GitFlow（重型）

```
master                ←  生产
  ↑
release/x.y.z          ←  发布分支
  ↑
develop               ←  集成分支
  ↑
feature/xxx           ←  特性分支
  ↑
hotfix/xxx            ←  热修

适合:
  ✅ 强版本节奏（每月/季度）
  ✅ 多版本并存
  ✅ 客户端产品
  ✅ ToB / 私有化部署

不适合:
  ❌ 持续交付（每天发布）
  ❌ SaaS 单一版本
  ❌ 小团队（流程太重）
```

### 3.2 GitHub Flow（简化版）

```
main                  ← 唯一长期分支
  ↑
feature/xxx           ← 短命特性分支
  ↑
PR + Review + CI
  ↑
合入 main → 自动部署

适合:
  ✅ SaaS / 持续交付
  ✅ 小到中型团队
  ✅ 开源项目

注意:
  - feature 分支寿命 < 1 周
  - 必须 PR + Review
  - main 永远可发布
```

### 3.3 GitLab Flow（折中）

```
main                  ← 持续集成
  ↓
production            ← 生产追主线
  ↓
release/x.y            ← 老版本维护

或者环境分支:
  main → pre-prod → production

适合:
  ✅ 多环境 + 持续交付
  ✅ ToC 业务
```

### 3.4 Trunk-Based Development（精英推荐）⭐⭐⭐⭐⭐

```
main (trunk)          ← 唯一长期分支
  ↑↓ 
short-lived branch    ← 寿命 < 1 天
  ↑
PR + CI 通过 → 合 main
  ↑
Feature Flag 控制启用

特征:
  ✅ 极短分支生命（< 24h）
  ✅ Trunk 永远可发布
  ✅ Feature Flags 替代分支
  ✅ 持续集成（每天合数次）
  ✅ 强测试覆盖

为什么是"精英方法":
  - Google / Facebook / Netflix / Amazon 都用
  - DORA 报告显示与高绩效正相关
  - 减少合并冲突
  - 减少集成地狱

挑战:
  ⚠️ 需要强 CI + 单元测试覆盖
  ⚠️ 需要 Feature Flags 系统
  ⚠️ 需要良好工程文化
```

### 3.5 选型决策表

| 团队 / 业务 | 推荐 |
|:---|:---|
| **开源项目** | GitHub Flow |
| **小团队 SaaS** | GitHub Flow / Trunk-Based |
| **中型 SaaS** | Trunk-Based + Feature Flags |
| **大型互联网** | Trunk-Based + Monorepo |
| **强版本 ToB** | GitFlow |
| **多环境 + 法规重** | GitLab Flow |

## 四、提交规范（Conventional Commits）

### 4.1 标准格式

```
<type>(<scope>): <subject>

<body>

<footer>

type:
  feat:     新功能
  fix:      修 bug
  docs:     文档
  style:    格式（不影响代码运行）
  refactor: 重构（既不是新功能也不是修 bug）
  perf:     性能优化
  test:     测试
  build:    构建系统/依赖
  ci:       CI 配置
  chore:    其他杂项
  revert:   回滚

scope: 影响范围（auth/api/db/...）
subject: 简短描述（≤ 50 字符）
body: 详细说明（可选）
footer: BREAKING CHANGE / Closes #123（可选）
```

### 4.2 示例

```
feat(order): 支持优惠券抵扣下单

- 新增 coupon_id 字段到订单表
- 抵扣金额计入订单 promotion_amount
- 兼容老 API（无 coupon_id 时按原逻辑）

Closes #1024
Co-authored-by: lisi <lisi@company.com>

---

fix(payment): 修复退款金额超过订单金额的边界 Bug

退款金额计算时未考虑历史退款，导致可能超额。
现加上历史退款累计校验。

Closes #1180

---

feat(api)!: 重构用户接口，移除已过时字段

BREAKING CHANGE: GET /v1/user 不再返回 deprecated_field
迁移至 GET /v2/user 或使用 GET /v1/user?legacy=true
```

### 4.3 工具

```bash
# Commitizen（交互式提交）
npm install -g commitizen cz-conventional-changelog
echo '{"path": "cz-conventional-changelog"}' > ~/.czrc
git cz

# commitlint + husky（提交前校验）
npm install --save-dev @commitlint/cli @commitlint/config-conventional husky
echo "module.exports = {extends: ['@commitlint/config-conventional']};" > commitlint.config.js
npx husky add .husky/commit-msg 'npx --no -- commitlint --edit $1'
```

### 4.4 自动生成 Changelog + 版本号

```bash
# release-please / standard-version / semantic-release
npm install -g standard-version
standard-version    # 自动按 commit 类型 bump 版本 + 生成 CHANGELOG.md
```

## 五、PR / MR 文化（Code Review）

### 5.1 Code Review 原则

```
作者要做:
  ✅ 描述清楚（What + Why）
  ✅ 关联 Issue
  ✅ 控制 diff 大小（< 400 行最佳）
  ✅ 自审一遍再发
  ✅ 截屏 + 测试结果

Reviewer 要做:
  ✅ 24h 内响应
  ✅ 看设计、不只看语法
  ✅ 提建议而非命令
  ✅ 抓出可读性 / 风险 / 测试
  ✅ Approve / Request Changes 明确
  
共同遵守:
  ❌ 不要 LGTM 万岁（必须实质 Review）
  ❌ 不要个人攻击
  ❌ 不要堵塞低级问题（拼写交给 Lint）
  ❌ 不要小问题打回整个 PR
```

### 5.2 PR 模板

```markdown
## What
本次改动做了什么（一句话）

## Why
为什么要这么做（业务背景 / 性能 / Bug）

## How
关键设计/实现思路

## Test
- [ ] 单元测试 已加
- [ ] 集成测试 已加
- [ ] 手工测试 已过
- [ ] 性能影响 已评估

## Risk
风险点 / 回滚方案

## Screenshots
（如有 UI 改动）

## Checklist
- [ ] 自测通过
- [ ] CHANGELOG 已更新
- [ ] 文档已更新
- [ ] 是否需要 DBA 介入
- [ ] 是否需要灰度

Closes #xxx
```

### 5.3 自动化辅助

```yaml
# CODEOWNERS（谁该 review）
# .github/CODEOWNERS
/services/order/        @order-team
/services/payment/      @payment-team @security-team
/infra/                 @sre-team
*.go                    @backend-leads

# Branch Protection 规则
require_approvals: 2
require_codeowners: true
require_status_checks: [ci/lint, ci/test, ci/security]
require_signed_commits: true
restrict_push: true
delete_after_merge: true
```

### 5.4 自动化 Reviewer

| 工具 | 用途 |
|:---|:---|
| **Reviewer-lottery** | 自动指派 |
| **Dangerfile** | 自动审查规则 |
| **Sourcery / CodeRabbit** | AI Review |
| **GitHub Copilot for PR** | AI Review |
| **DeepCode / Snyk** | 安全 Review |

## 六、代码托管平台对比

### 6.1 主流平台

| 平台 | 类型 | 私有化 | 国内主流 | 特点 |
|:---|:---|:---:|:---:|:---|
| **GitHub** | SaaS | Enterprise | ⭐⭐ | 国际主流，社区最大 |
| **GitLab CE/EE** | 自建/SaaS | ✅ | ⭐⭐⭐⭐⭐ | 国内私有化首选 |
| **Bitbucket** | SaaS / Data Center | ✅ | ⭐⭐ | Atlassian 系 |
| **Gitea** | 开源轻量 | ✅ | ⭐⭐⭐ | 小团队私有 |
| **Gogs** | 开源 | ✅ | ⭐⭐ | Gitea 前身 |
| **Forgejo** | Gitea Fork | ✅ | ⭐⭐ | 社区驱动 |
| **AWS CodeCommit** | 云服务 | AWS | ⭐ | AWS 生态 |
| **腾讯 CODING** | 国产 | SaaS | ⭐⭐⭐⭐ | 一体化 |
| **阿里云 Codeup** | 国产 | SaaS | ⭐⭐⭐⭐ | 与云效集成 |
| **华为云 CodeArts Repo** | 国产 | SaaS | ⭐⭐⭐ | 信创 |
| **极狐 GitLab** | GitLab 中国版 | ✅ | ⭐⭐⭐⭐ | 合规版 |
| **Gitee** | 国产 | SaaS / 企业版 | ⭐⭐⭐⭐ | 国内开源社区 |

### 6.2 GitLab 私有化部署（国内主流）

```bash
# 单节点（小团队）
docker run -d \
  --hostname gitlab.company.com \
  -p 443:443 -p 80:80 -p 22:22 \
  --restart always \
  --volume /srv/gitlab/config:/etc/gitlab \
  --volume /srv/gitlab/logs:/var/log/gitlab \
  --volume /srv/gitlab/data:/var/opt/gitlab \
  --shm-size 256m \
  gitlab/gitlab-ce:latest

# 集群（中大团队）参考 GitLab Reference Architecture:
# - PostgreSQL HA (Patroni)
# - Redis Sentinel
# - Gitaly cluster (3+ 节点)
# - Sidekiq workers
# - Praefect
# - MinIO/S3 对象存储
# - Nginx LB
```

### 6.3 极狐 GitLab vs GitLab CE/EE

```
极狐 GitLab = GitLab 中国合规版
  ✅ 数据本地化
  ✅ 中文支持
  ✅ 信创适配
  ✅ 与国内云厂深度合作
  ⚠️ 部分功能与上游有差异

中国大陆部署选:
  - 极狐 GitLab（合规要求高）
  - GitLab CE（开源够用）
  - Gitea（小团队/边缘）
```

## 七、Monorepo vs Polyrepo

### 7.1 对比

| 维度 | Monorepo | Polyrepo |
|:---|:---|:---|
| 代码共享 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 跨服务重构 | ⭐⭐⭐⭐⭐ | ⭐ |
| 权限隔离 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 工具复杂度 | 高 | 低 |
| CI 工作量 | 高（增量 build）| 低 |
| 代码所有权 | CODEOWNERS | 仓库级 |
| 国内主流度 | 字节/阿里走 Monorepo | 大多数 |
| 工具 | Bazel/Nx/Pants/Lerna | 无需 |

### 7.2 Monorepo 工具

| 工具 | 适合 |
|:---|:---|
| **Bazel** | Google 系，最重最强 |
| **Pants** | 类似 Bazel |
| **Buck2** | Meta 出品（Bazel 替代）|
| **Nx** | Node/TS 主流 |
| **Lerna** | npm 早期 |
| **Turbo** | Vercel 出品，简单 |
| **Rush** | Microsoft 出品 |
| **Pnpm Workspaces** | 简单依赖 |

### 7.3 Monorepo 实战要点

```
✅ 增量构建（只 build 改变的）
✅ 增量测试（只测改变影响的）
✅ 跨包依赖图
✅ CODEOWNERS 细化（路径级权限）
✅ Git sparse-checkout（按需 clone）
✅ Git LFS（大文件）
✅ Bot 自动维护（依赖升级）

工具:
  - Bazel Remote Cache
  - Nx Cloud
  - Buck2 daemon
```

## 八、大仓库优化技术

### 8.1 性能问题

```
仓库大了:
  - clone 慢（GB 级）
  - 历史长（百万 commit）
  - 文件多（万级文件）
  - 二进制资产（图片/视频）

解决方案:
  1. Shallow Clone        --depth=1（最快）
  2. Partial Clone        --filter=blob:none（按需）
  3. Sparse Checkout      只 checkout 部分路径
  4. Git LFS              大文件外挂
  5. Bare Repository      镜像同步
```

### 8.2 Shallow + Sparse 示例

```bash
# 只 clone 最新 commit
git clone --depth=1 --filter=blob:none https://github.com/big/repo.git

# 进入 + 启用 sparse
cd repo
git sparse-checkout init --cone
git sparse-checkout set services/order docs/

# 后续按需加路径
git sparse-checkout add services/payment
```

### 8.3 Git LFS

```bash
# 安装
git lfs install

# 跟踪大文件类型
git lfs track "*.psd"
git lfs track "*.mp4"
git add .gitattributes
git commit -m "Track binaries with LFS"

# 服务端: GitLab/GitHub 自带，或自建 lfs-server
```

### 8.4 替代方案：DVC（数据 + 模型 版本）

```bash
# ML/AI 项目数据版本
pip install dvc
dvc init
dvc remote add origin s3://bucket/dvc-store
dvc add data/big-dataset.parquet
dvc push

# Git 只存元数据
```

## 九、安全治理

### 9.1 必装清单

```
✅ Branch Protection
  - main/master 禁止直接 push
  - 强制 PR + Review
  - 强制 CI 通过
  
✅ Signed Commits
  - GPG / SSH 签名
  - 配合 Sigstore / Vigilant Mode

✅ Secret Scan
  - 在 push 时 + 在仓库历史中
  - gitleaks / trufflehog / detect-secrets
  - GitHub Secret Scanning（免费给公开仓库）
  - GitLab Secret Detection

✅ 依赖扫描
  - Dependabot / Renovate / Snyk
  - 自动 PR 升级漏洞依赖

✅ Code Scanning（SAST）
  - GitHub CodeQL
  - SonarQube / Semgrep
  - Snyk Code

✅ License 扫描
  - FOSSA / Snyk License
  - 防止 GPL 污染商业代码

✅ 审计日志
  - 谁 push / merge / 修改设置
  - 季度审计
```

### 9.2 Pre-commit 钩子

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: detect-private-key
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
  - repo: https://github.com/golangci/golangci-lint
    rev: v1.58.0
    hooks:
      - id: golangci-lint
```

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### 9.3 Secret 已泄漏怎么办

```
不要只是 reset / push --force！历史仍在！

正确步骤:
  1. 立即撤销该 Secret（改密码 / rotate token）
  2. 用 git-filter-repo 从历史中彻底删除
  3. 通知所有 fork / clone 者重新 clone
  4. 审计是否已被访问

# 删除历史中的文件
git filter-repo --path secrets.json --invert-paths
git push --force --all
git push --force --tags
```

## 十、Hooks 自动化

### 10.1 客户端钩子

```
pre-commit            提交前（lint/test）
prepare-commit-msg    生成提交信息
commit-msg            校验信息（commitlint）
post-commit           提交后通知
pre-push              推送前（重测试）
post-checkout         切换分支后
post-merge            合并后
```

### 10.2 服务端钩子（GitLab Server-side / GitHub App）

```
pre-receive           推送前校验（拒绝大文件、敏感词）
update                按引用校验
post-receive          推送后触发 webhook / CI

实战:
  - 强制 commit message 规范
  - 禁止 force-push 到 main
  - 禁止 push 大于 100MB 的文件
  - 推送时自动触发 Argo CD 同步
```

## 十一、版本与发布

### 11.1 语义化版本（SemVer）

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容变更
MINOR: 向下兼容的功能
PATCH: 向下兼容的修复

预发布: 1.0.0-alpha.1 / 1.0.0-beta.2 / 1.0.0-rc.1
构建号: 1.0.0+20260622.git.abcdef
```

### 11.2 Tag 策略

```bash
# 创建带注释的 tag（推荐）
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3

# 列出
git tag -l 'v1.*'

# 删除
git tag -d v1.2.3
git push origin --delete v1.2.3
```

### 11.3 自动发布

```yaml
# .github/workflows/release.yml
on:
  push:
    branches: [main]

jobs:
  release:
    permissions:
      contents: write
      pull-requests: write
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          release-type: simple
```

`release-please` 自动：
- 分析 conventional commits
- 计算下个版本号
- 生成 CHANGELOG
- 开 Release PR
- 合入后打 tag + 发布

## 十二、协作流程（团队）

### 12.1 分支保护示例

```yaml
# GitHub branch protection
main:
  require_pull_request: true
  required_approvals: 2
  require_codeowner_reviews: true
  dismiss_stale_reviews: true
  require_status_checks:
    - ci/lint
    - ci/test
    - ci/security
    - ci/coverage
  require_branches_up_to_date: true
  require_signed_commits: true
  enforce_admins: false      # 紧急情况可绕过
  allow_force_pushes: false
  allow_deletions: false
  
release/*:
  require_pull_request: true
  required_approvals: 3      # 更严
  restrictions:
    users: []
    teams: [release-managers]
```

### 12.2 分支命名规范

```
feature/<jira-id>-short-desc      feature/PROJ-123-add-coupon
fix/<jira-id>-short-desc          fix/PROJ-456-refund-bug
hotfix/<id>-<desc>                 hotfix/CRIT-001-payment-down
release/<version>                  release/1.2.0
chore/<desc>                       chore/update-deps
experiment/<desc>                  experiment/new-ml-model

❌ 不规范:
  - test / fix / my-branch
  - dev_zhangsan_20260622
  - feature1
```

### 12.3 大型变更（RFC 流程）

```
重大变更先写 RFC:
  1. /docs/rfc/0001-new-arch.md
  2. 描述: 背景 + 方案 + 备选 + 风险
  3. PR 给团队讨论
  4. 决议后开始实现

例子:
  - RFC 选型新框架
  - RFC 数据库迁移
  - RFC API 大改
  - RFC 服务拆分
```

## 十三、Git LFS / Submodule / Subtree

### 13.1 Submodule（子模块）

```bash
# 加子模块
git submodule add https://github.com/lib/utils.git libs/utils
git submodule init
git submodule update --remote

# Clone 带子模块的仓库
git clone --recurse-submodules <url>
git submodule update --init --recursive

特点:
  ✅ 引用特定 commit
  ✅ 子模块独立维护
  ❌ 子模块管理复杂
  ❌ CI 处理麻烦
```

### 13.2 Subtree（更简单的替代）

```bash
# 加子树
git subtree add --prefix=libs/utils https://github.com/lib/utils.git main --squash

# 拉子树更新
git subtree pull --prefix=libs/utils https://github.com/lib/utils.git main --squash

特点:
  ✅ 子代码合入本仓库
  ✅ 用户无感
  ❌ 历史略乱
  
经验: 内部团队首选 Subtree / Monorepo，开源依赖用 Submodule。
```

## 十四、Git 常见操作场景

### 14.1 撤销错误推送

```bash
# 强制回滚（团队商议后）
git reset --hard <good-commit>
git push --force-with-lease origin main

# 更安全: revert（保留历史）
git revert <bad-commit>
git push origin main
```

### 14.2 把 commit 拆分

```bash
git rebase -i HEAD~5
# 选择 commit 标 'edit'
# git reset HEAD^
# git add -p <逐块加>
# git commit -m "split commit 1"
# git commit -m "split commit 2"
# git rebase --continue
```

### 14.3 合并 commit

```bash
git rebase -i HEAD~5
# 把 pick 改成 squash 或 fixup
# 保存退出
```

### 14.4 二分查找 bug

```bash
git bisect start
git bisect bad                    # 当前坏
git bisect good v1.0              # 1.0 是好的
# Git 自动 checkout 中间 commit
# 测试 → git bisect good/bad
# 直到找到引入 bug 的 commit
git bisect reset
```

### 14.5 救命 reflog

```bash
# 误删分支 / hard reset 救回
git reflog
# 找到 HEAD@{N} 是想要的状态
git reset --hard HEAD@{5}
```

### 14.6 仅 cherry-pick 部分提交

```bash
git cherry-pick <commit>
git cherry-pick A..B              # 范围
git cherry-pick -x <commit>       # 附加来源
git cherry-pick --continue        # 解决冲突后
```

### 14.7 暂存当前工作

```bash
git stash push -u -m "WIP feature"
git stash list
git stash show stash@{0} -p
git stash pop / apply
git stash drop stash@{0}
```

## 十五、AI 辅助代码管理（2025）

### 15.1 AI 写 commit message

```bash
# OpenCommit / aicommit2 / git-aicommit
npm install -g opencommit
oco

# 或自建 LLM
git diff --staged | curl ... -d @- 
# → 自动生成 conventional commit
```

### 15.2 AI Code Review

| 工具 | 用途 |
|:---|:---|
| **CodeRabbit** | PR AI 审查 |
| **Sourcery** | AI 优化建议 |
| **GitHub Copilot for PR** | AI 总结 + 审查 |
| **Codium PR-Agent** | 开源 AI Reviewer |
| **CodeAnt AI** | 全栈 AI 审查 |

### 15.3 AI 总结仓库

```
"这个仓库做什么的？"
"最近 30 天 TOP 5 改动？"
"谁负责 payment 模块？"

工具:
  - GitHub Copilot Workspace
  - Sourcegraph Cody
  - Mutable AI
  - Aider
```

## 十六、典型坑（生产血泪）

| 坑 | 建议 |
|:---|:---|
| **直接 push main** | 必上 branch protection |
| **大量 force-push** | --force-with-lease |
| **secret 入仓** | pre-commit + gitleaks + 历史扫描 |
| **二进制文件入 Git** | LFS / 外部存储 |
| **长寿命 feature 分支** | Trunk-Based + Feature Flags |
| **MR 巨大无法 Review** | < 400 行 |
| **多个无关改动一个 PR** | 拆分 |
| **commit 写啥的随便** | Conventional Commits |
| **无 tag 无 release** | release-please / semantic-release |
| **没人 Review** | CODEOWNERS + 多人审 |
| **rebase vs merge 乱用** | 公开分支永远不 rebase |
| **直接编辑公共历史** | 别动！ |
| **fork + 私自合并** | 用 GitHub Flow 标准化 |
| **没有 CI 强制** | 必上 required status checks |
| **submodule 抓死** | 改 subtree / monorepo |
| **跨仓库改动协调** | RFC / 重构需要平台支持 |

## 十七、最佳实践 Checklist

```
仓库设置:
☐ Branch protection（main 必保护）
☐ Required reviewers + CODEOWNERS
☐ Required CI checks
☐ 强制 conventional commits
☐ Signed commits（高安全要求）
☐ Secret scanning
☐ Dependency scanning
☐ SAST scanning

工作流:
☐ Trunk-Based 或明确 GitFlow/GitHub Flow
☐ 短命分支（< 1 周）
☐ 小 PR（< 400 行）
☐ PR 模板
☐ 24h Review SLA
☐ Feature Flags 替代长寿命分支

提交:
☐ Conventional Commits
☐ pre-commit 钩子（lint + secret）
☐ commitlint 校验
☐ 一次提交一件事

发布:
☐ SemVer 版本号
☐ 自动 CHANGELOG (release-please)
☐ Signed tags
☐ Release notes

度量:
☐ PR 平均关闭时间
☐ PR 平均大小
☐ Review 响应时间
☐ Lead Time for Changes
```

## 十八、技术栈推荐（2025）

### 18.1 小团队（< 30 人）

```
托管:        Gitea / Gitee 私有 / GitLab CE
工作流:      GitHub Flow
提交规范:    Conventional Commits + commitlint
PR Review:   2 个 Approval + CODEOWNERS
安全:        pre-commit + gitleaks + Dependabot
版本:        release-please
```

### 18.2 中型团队（30-300 人）

```
托管:        GitLab EE / 极狐 GitLab
工作流:      Trunk-Based + Feature Flags
提交:        commitlint + Husky 强制
Review:      CODEOWNERS + 2 个 Approval + AI Reviewer
安全:        GitLab Secret Detection + SAST + Dependency
监控:        DORA 度量
仓库管理:    Monorepo or Polyrepo 明确选择
```

### 18.3 大型 / Monorepo（> 300 人）

```
托管:        自建 GitLab 集群 / GitHub Enterprise
策略:        Monorepo + Bazel/Nx
工作流:      Trunk-Based + Strict CI
工具:        增量 build/test 缓存（Bazel Remote Cache / Nx Cloud）
权限:        CODEOWNERS 细粒度
开发者门户:  Backstage
AI:          Copilot for Business + 自训练
治理:        RFC 流程
```

## 十九、学习路径

```
入门（1 周）:
  1. Git 基础命令熟练
  2. 一次 PR 走完
  3. 基础 rebase + merge

中级（1 个月）:
  4. Conventional Commits
  5. Trunk-Based / GitFlow 选型
  6. Branch protection
  7. CODEOWNERS
  8. pre-commit hooks

高级（3 个月）:
  9. Monorepo 工具（Nx/Bazel）
  10. Git LFS / Submodule / Subtree
  11. release-please 自动发布
  12. 复杂 rebase / cherry-pick / bisect
  13. AI Code Review

专家:
  14. 自定义 server-side hooks
  15. 仓库审计 / 合规
  16. 跨组织治理
  17. Backstage / 自研开发者平台
```

## 二十、参考资料

```
书:
  - 《Pro Git》(Scott Chacon) - 中文版在线免费
  - 《Trunk-Based Development》(Paul Hammant)
  - 《Accelerate》(DORA 系列)

官方:
  - Git: https://git-scm.com/doc
  - GitHub Docs
  - GitLab Docs
  - Conventional Commits: https://www.conventionalcommits.org/

社区:
  - Trunk Based Development: https://trunkbaseddevelopment.com/
  - Atlassian Git Tutorials
  - Oh My Git!（互动游戏学 Git）

工具:
  - https://learngitbranching.js.org（可视化练习）
  - https://ohmyz.sh + oh-my-zsh git 插件
  - GitLens (VSCode 插件)
  - lazygit / tig（终端 UI）
  - delta（更好看的 diff）
```

> 📖 **核心判断**：代码管理是 DevOps 的"第一公里"。**选对工作流（推荐 Trunk-Based + Feature Flags）+ 配齐规范（Conventional Commits + CODEOWNERS + Branch Protection）+ 强化安全（Secret Scanning + Signed Commits）+ 拥抱 AI（Copilot + AI Review）** = 团队效率指数级提升。最容易翻车的不是 Git 命令，而是：**没有 PR 文化、没有提交规范、没有分支保护**——这三条做不到，再先进的 CI/CD 都是花架子。
