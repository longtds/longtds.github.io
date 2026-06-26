# Shell 脚本

> Shell 脚本 = **运维第一武器**。**严格模式 + 错误处理 + 参数解析 + 日志结构 + 幂等 + 锁** 这六件套是生产级脚本与玩具脚本的分水岭。Bash 仍是底座，复杂逻辑该上 Python/Go 别硬撑。

## 一、Bash 严格模式（必加）

### 1.1 标准开头

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# -e  任一命令失败立即退出 (失败 = 非 0 退出码)
# -u  使用未定义变量报错
# -o pipefail  管道中任一失败整体失败
# IFS  防止文件名空格被分词破坏
```

### 1.2 trap 清理

```bash
TMPDIR=$(mktemp -d)
LOCK=/var/lock/myapp.lock

cleanup() {
    local exit_code=$?
    rm -rf "$TMPDIR"
    rm -f "$LOCK"
    echo "Cleanup done, exit=$exit_code"
    exit $exit_code
}
trap cleanup EXIT INT TERM

# 捕获信号
trap 'echo "received SIGUSR1"; reload_config' USR1
```

### 1.3 ERR trap（详细错误）

```bash
set -E                                     # 让 ERR trap 在子函数也生效
trap 'on_error $? $LINENO "$BASH_COMMAND"' ERR

on_error() {
    local code=$1 line=$2 cmd="$3"
    echo "[ERROR] code=$code line=$line cmd=$cmd" >&2
    # 钉钉/飞书告警
    notify_alert "脚本失败: line $line: $cmd"
    exit $code
}
```

### 1.4 调试模式

```bash
# 启动时调试
bash -x script.sh                          # 整脚本
bash -n script.sh                          # 仅语法检查

# 脚本内开关
[ "${DEBUG:-}" = "1" ] && set -x

# 局部开调试
foo() {
    set -x
    复杂逻辑
    set +x
}

# 带行号
PS4='+ ${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]:-main}: '
set -x
```

## 二、变量与字符串

### 2.1 变量基础

```bash
# 赋值（= 两边不能有空格！）
name="alice"
age=30
readonly VERSION="1.0"                     # 只读

# 引用（双引号保留变量，单引号原样）
echo "Hello, $name"
echo 'Hello, $name'                        # 输出: Hello, $name

# 默认值
echo "${name:-anonymous}"                  # name 为空时用 anonymous
echo "${name:=anonymous}"                  # 同上 + 赋值给 name
echo "${name:?name required}"              # 为空时报错
echo "${name:+exists}"                     # 非空时用 exists

# 长度
echo "${#name}"

# 切片
str="hello world"
echo "${str:0:5}"                          # hello
echo "${str: -5}"                          # world (注意空格)
echo "${str:0:-6}"                         # hello

# 替换
echo "${str/world/bash}"                   # hello bash (第一个)
echo "${str//l/L}"                         # heLLo worLd (全部)
echo "${str/#hello/HI}"                    # 开头匹配
echo "${str/%world/WORLD}"                 # 结尾匹配

# 大小写
echo "${str^^}"                            # HELLO WORLD
echo "${str,,}"                            # hello world (小写)
echo "${str^}"                             # Hello world (首字母大写)

# 去前缀/后缀
file="archive.tar.gz"
echo "${file%.gz}"                         # archive.tar (短匹配)
echo "${file%%.*}"                         # archive (长匹配)
echo "${file#*.}"                          # tar.gz (短匹配)
echo "${file##*.}"                         # gz (长匹配)
```

### 2.2 数组

```bash
# 索引数组
arr=(apple banana cherry)
echo "${arr[0]}"                           # apple
echo "${arr[@]}"                           # all 元素
echo "${#arr[@]}"                          # 长度

arr+=(durian)                              # 追加
unset arr[1]                               # 删 banana

# 遍历
for item in "${arr[@]}"; do
    echo "$item"
done

# 关联数组（map）
declare -A user
user[name]="alice"
user[age]=30
echo "${user[name]}"
echo "${!user[@]}"                         # keys
echo "${user[@]}"                          # values

# 检查键存在
[[ -v user[name] ]] && echo "exists"
[[ "${user[name]:-}" ]] && echo "exists"

# 遍历关联
for k in "${!user[@]}"; do
    echo "$k = ${user[$k]}"
done
```

### 2.3 算术

```bash
# 整数
i=$((1 + 2))
((i++))
((i += 10))
i=$(( RANDOM % 100 ))

# let
let "i = i + 1"

# 浮点（bash 不支持，用 bc/awk）
result=$(echo "3.14 * 2" | bc -l)
result=$(awk "BEGIN { print 3.14 * 2 }")

# 进制
echo $((2#1010))                           # 二进制 → 10
echo $((16#ff))                            # 十六进制 → 255
printf "%x\n" 255                           # 10 进制 → 十六
printf "%d\n" 0xff                          # 十六 → 10 进制
```

## 三、条件与流程

### 3.1 测试

```bash
# 文件
[ -f /etc/passwd ]                         # 存在且是普通文件
[ -d /tmp ]                                # 目录
[ -L /etc/localtime ]                      # 软链接
[ -r file ]                                 # 可读
[ -w file ]                                 # 可写
[ -x file ]                                 # 可执行
[ -s file ]                                 # 非空
[ -e file ]                                 # 存在
[ file1 -nt file2 ]                         # file1 比 file2 新

# 字符串
[ -z "$s" ]                                 # 空
[ -n "$s" ]                                 # 非空
[ "$a" = "$b" ]                             # 等
[ "$a" != "$b" ]
[[ "$s" == *.gz ]]                          # 通配符（双 [[ 内）
[[ "$s" =~ ^[0-9]+$ ]]                      # 正则

# 数字
[ "$a" -eq 10 ]
[ "$a" -lt 10 ]                             # < (-le/-gt/-ge/-ne)
(( a > 10 ))                                # 算术语法（更直观）

# 复合（[[ ]] 内推荐）
[[ -f /etc/passwd && -r /etc/passwd ]]
[[ "$a" == "1" || "$a" == "2" ]]
```

### 3.2 if / case

```bash
if [[ -z "$name" ]]; then
    echo "empty"
elif [[ "$name" == "root" ]]; then
    echo "admin"
else
    echo "user: $name"
fi

# 一行
[[ -f "$f" ]] && rm -f "$f"
[[ -d /backup ]] || mkdir -p /backup

# case
case "$1" in
    start|run)  start_service ;;
    stop)        stop_service ;;
    restart)    stop_service && start_service ;;
    status)      show_status ;;
    *)           echo "usage: $0 {start|stop|restart|status}"; exit 1 ;;
esac

# 模式匹配
case "$file" in
    *.tar.gz|*.tgz)  tar xzf "$file" ;;
    *.zip)           unzip "$file" ;;
    *.7z)            7z x "$file" ;;
esac
```

### 3.3 循环

```bash
# for
for i in {1..10}; do echo $i; done
for i in $(seq 1 10); do echo $i; done     # 老式
for ((i=0; i<10; i++)); do echo $i; done    # C 风格

# 文件
for f in /var/log/*.log; do
    [ -f "$f" ] || continue                # 没匹配到通配
    echo "Processing $f"
done

# 按行读文件 ⭐ 标准姿势
while IFS= read -r line; do
    echo "Line: $line"
done < input.txt

# 多列
while IFS=: read -r user pass uid gid rest; do
    echo "$user uid=$uid"
done < /etc/passwd

# 管道喂入（注意：管道开 subshell, 变量隔离）
ls *.log | while read -r f; do
    # 变量在此 subshell 内
    process "$f"
done

# 等效（用 process substitution，变量可保留）
while read -r f; do
    process "$f"
done < <(ls *.log)

# break / continue
for i in {1..10}; do
    [ $i -eq 5 ] && continue
    [ $i -eq 8 ] && break
    echo $i
done
```

## 四、函数

```bash
# 定义
greet() {
    local name="${1:-anonymous}"           # local 必须！
    local age="${2:-0}"
    echo "Hello $name (age $age)"
    return 0                                # 0=成功, 1-255=失败
}

# 调用
greet "alice" 30
greet alice

# 拿返回码
greet "alice"; rc=$?

# 函数返回字符串（用 echo + 命令替换）
get_user() {
    echo "alice"
}
name=$(get_user)

# 关联数组传参 (bash 4.3+)
process_map() {
    local -n ref=$1                         # nameref
    for k in "${!ref[@]}"; do
        echo "$k = ${ref[$k]}"
    done
}
declare -A m
m[a]=1; m[b]=2
process_map m
```

## 五、参数解析

### 5.1 简单位置参数

```bash
#!/bin/bash
INPUT=$1
OUTPUT=$2

[[ -z "$INPUT" || -z "$OUTPUT" ]] && {
    echo "usage: $0 INPUT OUTPUT"
    exit 1
}

$0    脚本名
$1..  位置参数
$#    参数个数
$@    所有参数（数组）
$*    所有参数（单字符串）
$?    上条命令退出码
$$    本进程 PID
$!    最近后台 PID
$_    上条命令最后一个参数
```

### 5.2 getopts（POSIX，推荐）

```bash
#!/bin/bash
usage() {
    cat <<EOF
Usage: $0 [-h] [-v] [-o OUTPUT] INPUT

Options:
  -h         显示帮助
  -v         详细输出
  -o FILE    输出文件
EOF
    exit 0
}

verbose=0
output=""

while getopts "hvo:" opt; do
    case $opt in
        h) usage ;;
        v) verbose=1 ;;
        o) output="$OPTARG" ;;
        \?) echo "Invalid: -$OPTARG"; exit 1 ;;
        :) echo "Option -$OPTARG requires value"; exit 1 ;;
    esac
done
shift $((OPTIND-1))                         # 移除已处理的 flag

input=$1
[[ -z "$input" ]] && { usage; }
```

### 5.3 长选项（GNU getopt）

```bash
#!/bin/bash
OPTS=$(getopt -o hvo: --long help,verbose,output: -n "$0" -- "$@")
[[ $? -ne 0 ]] && { echo "解析失败"; exit 1; }
eval set -- "$OPTS"

verbose=0
output=""

while true; do
    case "$1" in
        -h|--help) usage; shift ;;
        -v|--verbose) verbose=1; shift ;;
        -o|--output) output="$2"; shift 2 ;;
        --) shift; break ;;
        *) echo "未知选项 $1"; exit 1 ;;
    esac
done
```

## 六、错误处理与重试

### 6.1 重试机制

```bash
retry() {
    local attempts=${1:-3}
    local delay=${2:-2}
    local cmd=("${@:3}")
    local i=0
    
    while (( i < attempts )); do
        if "${cmd[@]}"; then
            return 0
        fi
        i=$((i + 1))
        echo "尝试 $i/$attempts 失败，${delay}s 后重试..." >&2
        sleep $delay
        delay=$((delay * 2))                # 指数退避
    done
    return 1
}

# 用
retry 5 2 curl -sf http://api.example.com/health
retry 3 1 ssh user@host "uptime"
```

### 6.2 命令存在性检查

```bash
require() {
    for cmd in "$@"; do
        command -v "$cmd" >/dev/null 2>&1 || {
            echo "需要命令 $cmd, 请先安装" >&2
            exit 1
        }
    done
}
require curl jq git docker
```

### 6.3 超时

```bash
timeout 10s curl http://slow.example.com/

# 自定义
run_with_timeout() {
    local timeout=$1
    shift
    "$@" &
    local pid=$!
    (sleep $timeout && kill -TERM $pid) 2>/dev/null &
    local watcher=$!
    wait $pid 2>/dev/null
    local rc=$?
    kill $watcher 2>/dev/null
    return $rc
}
```

## 七、并发与并行

### 7.1 后台 & wait

```bash
# 简单并行
process file1.txt &
process file2.txt &
process file3.txt &
wait                                        # 等所有后台

# 收集退出码
pids=()
for f in *.txt; do
    process "$f" &
    pids+=($!)
done

failed=0
for pid in "${pids[@]}"; do
    wait $pid || failed=$((failed+1))
done
echo "失败 $failed 个"
```

### 7.2 限制并发数

```bash
# semaphore (FIFO)
MAX_PARALLEL=10
sem=$(mktemp -u)
mkfifo "$sem"
exec 3<>"$sem"
rm "$sem"

# 初始化令牌
for ((i=0; i<MAX_PARALLEL; i++)); do echo >&3; done

for f in /data/*.log; do
    read -u 3                              # 拿令牌
    {
        process "$f"
        echo >&3                            # 还令牌
    } &
done
wait
exec 3<&-
```

### 7.3 GNU parallel（推荐）

```bash
# 并行 jobs
ls *.log | parallel -j 10 'gzip {}'
parallel -j 16 process_one.sh ::: *.txt
parallel -j 8 --eta 'curl -sf {} > /dev/null' ::: $(cat urls.txt)

# xargs 也行（轻量）
ls *.log | xargs -P 8 -I {} gzip {}
find . -name '*.tmp' -print0 | xargs -0 -P 8 -n 100 rm
```

## 八、文件锁（防重入）

```bash
# flock 是标准方案
LOCKFILE=/var/run/myscript.lock

(
    flock -n 9 || { echo "已有实例在运行"; exit 1; }
    
    # 临界区
    do_work
) 9>"$LOCKFILE"

# -n 非阻塞 / -w 30 等 30s
# 9 是文件描述符 (>9 都可)

# 整脚本互斥写法
exec 9>"$LOCKFILE"
flock -n 9 || exit 0
```

## 九、日志与输出

### 9.1 结构化日志

```bash
LOG_FILE=/var/log/myapp.log

log() {
    local level=$1; shift
    local msg="$*"
    local ts=$(date '+%Y-%m-%d %H:%M:%S')
    printf '[%s] [%s] %s\n' "$ts" "$level" "$msg" | tee -a "$LOG_FILE"
}

info()  { log INFO  "$@"; }
warn()  { log WARN  "$@"; }
error() { log ERROR "$@" >&2; }
die()   { error "$@"; exit 1; }

# 用
info "Starting backup"
warn "Disk usage > 80%"
die "Database connection failed"
```

### 9.2 重定向技巧

```bash
# 全脚本输出重定向到日志（含子进程）
exec > >(tee -a /var/log/script.log) 2>&1

# 仅 stdout / 仅 stderr
command >stdout.log
command 2>stderr.log
command &>both.log                          # bash
command > both.log 2>&1                     # POSIX

# 抛弃
command >/dev/null 2>&1
command &>/dev/null

# 颜色（仅 tty 时）
if [ -t 1 ]; then
    RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; NC='\033[0m'
fi
echo -e "${GREEN}✅ OK${NC}"
echo -e "${RED}❌ FAIL${NC}"

# Here doc
cat <<EOF
配置文件
hostname=$HOSTNAME
date=$(date)
EOF

cat <<'EOF'                                # 单引号 = 不展开
$VAR 原样
EOF
```

## 十、文本处理（运维必杀）

### 10.1 grep

```bash
grep "error" /var/log/*.log
grep -i "error"                             # 忽略大小写
grep -v "DEBUG"                             # 反向
grep -E "error|warn"                        # 扩展正则
grep -P '\d{3}'                             # Perl 正则
grep -r "TODO" .                            # 递归
grep -l "pattern" *.txt                     # 仅文件名
grep -c "pattern" *.log                     # 计数
grep -A 2 -B 2 "error"                      # 前后 2 行
grep -n "pattern"                           # 行号
grep -m 5 "pattern"                         # 最多 5 个

# 现代替代: ripgrep (rg) ⭐ 比 grep 快 10x
rg "pattern" .
rg -t py "pattern"                          # 仅 Python 文件
```

### 10.2 sed

```bash
sed 's/old/new/' file                       # 第一个
sed 's/old/new/g' file                      # 全部
sed -i 's/old/new/g' file                   # in-place
sed -i.bak 's/old/new/g' file              # 带备份
sed 's|/path/old|/path/new|g'               # 用 | 避免转义 /
sed -n '5,10p' file                         # 打印 5-10 行
sed '/^#/d' file                            # 删除以 # 开头
sed -e 's/a/A/' -e 's/b/B/' file            # 多个命令
sed '/start/,/end/d' file                   # 删除 start 到 end
sed '$a追加到末尾' file
sed '1i插入到开头' file
```

### 10.3 awk

```bash
# 列处理
awk '{print $1}' file                       # 第 1 列
awk '{print $1, $NF}' file                  # 第 1 和最后列
awk -F: '{print $1}' /etc/passwd            # : 分隔

# 条件
awk '$3 > 100' file                         # 第 3 列 > 100
awk '/error/' file                          # 匹配 error 的行
awk '$1=="alice" {print $0}' file

# 计算
awk '{sum += $3} END {print sum}' file
awk '{a[$1]++} END {for (k in a) print k, a[k]}' file    # 计数
awk -F: 'BEGIN{n=0} $3>=1000 {n++} END{print n}' /etc/passwd

# 真实运维 oneliner
# 看 access log 各状态码数
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# 看慢请求 top
awk '$NF > 1.0 {print $7, $NF}' access.log | sort -k2 -rn | head

# 看每个 IP 请求数
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -20
```

### 10.4 jq（JSON 必备）

```bash
# 取字段
echo '{"name":"alice","age":30}' | jq '.name'

# 数组
echo '[{"a":1},{"a":2}]' | jq '.[].a'
echo '[{"a":1},{"a":2}]' | jq '.[] | .a'

# 过滤
curl -s api/users | jq '.[] | select(.age > 18) | .name'

# 修改
echo '{"a":1}' | jq '.b = 2'                # 添加字段
jq '.users[].active = true' data.json

# 输出格式
jq -c                                       # compact
jq -r                                       # raw (无引号)

# 实战
# 从 docker inspect 拿 IP
docker inspect mysql | jq -r '.[0].NetworkSettings.IPAddress'
# K8s
kubectl get pods -o json | jq -r '.items[] | "\(.metadata.name) \(.status.phase)"'
```

### 10.5 cut / sort / uniq / tr

```bash
cut -d: -f1 /etc/passwd                     # 第 1 字段
cut -c1-10 file                              # 第 1-10 字符
cut -f1,3 -d, data.csv

sort file
sort -n file                                 # 数字
sort -r file                                 # 倒序
sort -k 3 -n file                            # 按第 3 列
sort -u file                                 # 去重
sort -t: -k3 -n /etc/passwd                 # : 分隔, 按第 3 列

uniq                                         # 仅相邻去重
uniq -c                                       # 计数
uniq -d                                       # 仅重复

tr 'a-z' 'A-Z' < file                       # 转大写
tr -d '\r' < file.txt                       # 删 \r (DOS 换行)
tr -s ' '                                    # 压缩多空格
```

## 十一、网络与 API

### 11.1 curl

```bash
# GET
curl https://api.example.com/users
curl -sf https://api.example.com/health     # -s 静默 -f 失败退出
curl -L https://example.com                  # 跟随重定向
curl -k https://self-signed                  # 忽略证书

# POST JSON
curl -X POST -H "Content-Type: application/json" \
  -d '{"name":"alice","age":30}' \
  https://api.example.com/users

curl -X POST --data-binary @data.json https://api.example.com/

# 上传文件
curl -F "file=@/path/to/file" https://upload.example.com/

# 鉴权
curl -u user:pass https://api/
curl -H "Authorization: Bearer $TOKEN" https://api/

# 重试 + 超时
curl --retry 3 --retry-delay 2 \
  --connect-timeout 5 --max-time 30 \
  https://api/

# 输出
curl -o output.json https://api/             # 保存
curl -I https://api/                          # 仅 header
curl -w "%{http_code} %{time_total}\n" -o /dev/null -s https://api/
# Trick: -w 配 -o /dev/null -s 只看状态
```

### 11.2 健康检查模板

```bash
check_http() {
    local url=$1
    local expected=${2:-200}
    local timeout=${3:-5}
    
    local code=$(curl -s -o /dev/null \
        -w "%{http_code}" \
        --max-time $timeout \
        "$url")
    
    if [[ "$code" == "$expected" ]]; then
        return 0
    else
        echo "ERROR: $url → $code (expected $expected)" >&2
        return 1
    fi
}

check_http "https://api.example.com/health" 200 || die "API not healthy"
```

## 十二、SSH 与远程

```bash
# 单次
ssh user@host 'uptime'

# 多命令
ssh user@host <<'EOF'
cd /tmp
ls -la
df -h
EOF

# 不验证 host key（自动化）
ssh -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=10 \
    user@host 'cmd'

# 并行 ssh (parallel-ssh / pssh)
pssh -h hosts.txt -P -i "uptime"

# 文件
scp file user@host:/tmp/
scp -r dir/ user@host:/tmp/
rsync -avz file user@host:/tmp/             # 增量 + 压缩

# SSH 隧道
ssh -L 8080:internal:80 user@bastion         # 本地转发
ssh -R 9000:localhost:80 user@public         # 反向
ssh -D 1080 user@host                        # SOCKS5 代理

# 配置 ~/.ssh/config
Host bastion
    HostName 1.2.3.4
    User alice
    IdentityFile ~/.ssh/id_ed25519
    Port 22

Host *.internal
    ProxyJump bastion
    User ops
```

## 十三、幂等性

```bash
# 创建目录（幂等）
mkdir -p /data/myapp                         # 已存在不报错

# 创建用户（幂等）
id alice &>/dev/null || useradd -m alice

# 加用户到组（幂等）
groups alice | grep -q docker || usermod -aG docker alice

# 软链接（幂等）
ln -sfn /opt/app/v2 /opt/app/current        # -f 覆盖 -n 不跟随

# 添加配置行（幂等）
grep -qF "alias ll='ls -la'" ~/.bashrc || \
  echo "alias ll='ls -la'" >> ~/.bashrc

# 替换 / 添加配置
update_config() {
    local file=$1 key=$2 value=$3
    if grep -q "^$key=" "$file"; then
        sed -i "s|^$key=.*|$key=$value|" "$file"
    else
        echo "$key=$value" >> "$file"
    fi
}
update_config /etc/myapp.conf "MaxConn" "1000"
```

## 十四、生产级脚本模板

```bash
#!/usr/bin/env bash
# ================================================================
# 名称: deploy.sh
# 用途: 部署 myapp 到生产
# 用法: ./deploy.sh [-v] [-h] -e ENV VERSION
# ================================================================
set -euo pipefail
IFS=$'\n\t'

# ---------- 全局 ----------
readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
readonly LOG_FILE="/var/log/${SCRIPT_NAME%.sh}.log"
readonly LOCK_FILE="/var/run/${SCRIPT_NAME%.sh}.lock"

# ---------- 日志 ----------
ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { printf '[%s] [%s] %s\n' "$(ts)" "$1" "${@:2}" | tee -a "$LOG_FILE"; }
info()  { log INFO  "$@"; }
warn()  { log WARN  "$@"; }
error() { log ERROR "$@" >&2; }
die()   { error "$@"; exit 1; }

# ---------- 锁 ----------
acquire_lock() {
    exec 9>"$LOCK_FILE"
    flock -n 9 || die "已有 $SCRIPT_NAME 实例在运行"
}

# ---------- 清理 ----------
cleanup() {
    local rc=$?
    info "Cleanup with code $rc"
    # 临时文件 / lock
    exit $rc
}
trap cleanup EXIT
trap 'error "Interrupted"; exit 130' INT TERM

# ---------- ERR ----------
on_error() {
    error "Failed at line $1: $2"
    notify_alert "deploy.sh 失败: $2"
}
set -E
trap 'on_error $LINENO "$BASH_COMMAND"' ERR

# ---------- 参数 ----------
usage() {
    cat <<EOF
$SCRIPT_NAME - Deploy myapp

Usage: $SCRIPT_NAME [OPTIONS] VERSION

Options:
  -e ENV    Environment (dev/stage/prod) [必需]
  -v        Verbose
  -h        Show this help

Examples:
  $SCRIPT_NAME -e prod v1.2.3
  $SCRIPT_NAME -v -e dev v1.2.4-rc1
EOF
    exit "${1:-0}"
}

ENV=""
VERBOSE=0

while getopts "hve:" opt; do
    case $opt in
        h) usage ;;
        v) VERBOSE=1; set -x ;;
        e) ENV="$OPTARG" ;;
        \?) usage 1 ;;
    esac
done
shift $((OPTIND - 1))

VERSION="${1:-}"

# ---------- 校验 ----------
[[ -z "$ENV" ]] && { echo "缺少 -e ENV"; usage 1; }
[[ -z "$VERSION" ]] && { echo "缺少 VERSION"; usage 1; }
[[ ! "$ENV" =~ ^(dev|stage|prod)$ ]] && die "无效 ENV: $ENV"

# ---------- 依赖 ----------
for cmd in curl jq kubectl docker; do
    command -v "$cmd" >/dev/null || die "缺少命令: $cmd"
done

# ---------- 主流程 ----------
main() {
    acquire_lock
    info "开始部署 $VERSION 到 $ENV"
    
    pre_check
    backup
    deploy
    verify
    
    info "✅ 部署完成"
}

pre_check() {
    info "预检"
    # 检查目标环境可达
    curl -sf "https://api-$ENV.example.com/health" >/dev/null \
        || die "目标环境不可达"
}

backup() {
    info "备份当前版本"
    # ...
}

deploy() {
    info "部署 $VERSION"
    kubectl set image deployment/myapp app=myapp:$VERSION -n "$ENV"
    kubectl rollout status deployment/myapp -n "$ENV" --timeout=5m \
        || die "部署超时"
}

verify() {
    info "健康验证"
    retry 5 10 curl -sf "https://api-$ENV.example.com/health"
}

retry() {
    local attempts=$1 delay=$2
    shift 2
    for ((i=1; i<=attempts; i++)); do
        "$@" && return 0
        warn "Retry $i/$attempts in ${delay}s..."
        sleep $delay
    done
    return 1
}

notify_alert() {
    curl -X POST -H 'Content-Type: application/json' \
        -d "{\"text\": \"$1\"}" \
        "$WEBHOOK_URL" 2>/dev/null || true
}

main "$@"
```

## 十五、Bash 何时止步

```
✅ Bash 擅长:
  - 调用命令 / 流程编排
  - 文本管道
  - 简单条件 / 循环
  - 系统运维 / 部署

❌ Bash 不擅长（该换 Python/Go）:
  - 复杂数据结构（嵌套 JSON）
  - 数值计算 / 浮点
  - 单元测试 / 持续维护
  - 并发协程
  - HTTP 客户端复杂逻辑
  - > 500 行的脚本
  - 跨平台（Windows）

替代:
  - Python   通用编排（用 typer/click + httpx）
  - Go       高性能 / 跨平台二进制
  - Just     替代 Makefile
  - Taskfile YAML 任务定义
  - Hermes Agent / Ansible  声明式
```

## 十六、ShellCheck（必装）

```bash
# 安装
dnf install ShellCheck
apt install shellcheck

# 检查
shellcheck deploy.sh
shellcheck -x deploy.sh                     # 跟随 source

# 集成
# vim/vscode 插件
# CI: shellcheck **/*.sh

# 常见提示:
# SC2086  双引号防分词
# SC2046  $(...) 双引号
# SC2155  declare 与 export 同时赋值
# SC2034  变量未使用
```

## 十七、典型坑

| 坑 | 建议 |
|:---|:---|
| **变量没引号** | "$var" 必须，防空格分词 |
| **= 两边有空格** | name=alice (没空格) |
| **未加 set -euo pipefail** | 失败不退出 → 灾难 |
| **管道丢变量** | while-read 用 < <(cmd) |
| **测试用单 [ ]** | 推荐 [[ ]] |
| **数字比较用 =** | 用 -eq / (( )) |
| **rm -rf "$var/*"** | 没引号 + 变量空 = 灾难 |
| **chmod 777** | 永远不要 |
| **解析 ls 输出** | 用 find -print0 / glob |
| **不锁** | 多实例冲突 |
| **不写日志** | 出问题查不出 |
| **trap 不清理** | 临时文件留尸 |
| **export 滥用** | 子进程才需要 |
| **不用 shellcheck** | 必装 |
| **bash 写 1000 行** | 换 Python |

## 十八、最佳实践 Checklist

```
开头:
☐ #!/usr/bin/env bash
☐ set -euo pipefail
☐ IFS=$'\n\t'

错误处理:
☐ trap cleanup EXIT
☐ trap on_error ERR
☐ retry 包装
☐ 重要命令检查退出码

参数解析:
☐ getopts 处理
☐ usage 函数
☐ 必填校验

日志:
☐ 结构化 log/info/error
☐ 同时写文件 + stdout
☐ 颜色（仅 tty）

幂等:
☐ mkdir -p
☐ ln -sfn
☐ id || useradd
☐ grep -q || append

并发:
☐ flock 防重入
☐ 限制并行数
☐ wait + 退出码收集

工程:
☐ shellcheck 通过
☐ 函数化 + main()
☐ readonly 常量
☐ local 局部变量
☐ 单元测试 (bats)
```

## 十九、推荐栈（2025）

```
基础:
  bash 5+ / busybox (容器内)
  shellcheck (lint)
  shfmt (格式化)

测试:
  bats-core (Bash 单测)
  shunit2

参数:
  getopts (POSIX)
  argbash (代码生成)

工具替代:
  jq (JSON)
  yq (YAML)
  fx (交互 JSON)
  ripgrep (替 grep)
  fd-find (替 find)
  bat (替 cat)
  dust (替 du)

复杂逻辑切换:
  Python + typer / click
  Go + cobra
  Just / Taskfile (替 Makefile)
```

## 二十、学习路径

```
入门（2 周）:
  1. 严格模式 set -euo pipefail
  2. 变量 / 引号 / 数组
  3. if / for / while
  4. 函数 + local
  5. 参数解析 getopts
  6. shellcheck 修干净

中级（1 月）:
  7. trap + 错误处理
  8. flock 锁
  9. 并发 wait / parallel
  10. 文本三剑客 (grep/sed/awk)
  11. jq + curl + ssh
  12. 重试 / 超时

高级（3 月+）:
  13. 生产级模板
  14. bats 单测
  15. Hermes / Ansible 改造
  16. Python/Go 重写复杂脚本

专家:
  17. 自研运维 DSL
  18. 嵌入式 (busybox/ash)
  19. POSIX 跨 shell 兼容
```

## 二十一、参考资料

```
官方:
  - GNU Bash Reference Manual
  - POSIX.1-2017 (sh)
  - Bash Pitfalls: mywiki.wooledge.org/BashPitfalls

工具:
  - shellcheck.net
  - explainshell.com (解释命令)
  - shfmt
  - bats-core

书籍:
  - 《Linux 命令行与 Shell 脚本编程大全》
  - 《Shell 脚本学习指南》
  - 《Pro Bash Programming》
  - 阮一峰 Bash 教程

社区:
  - Bash Hackers Wiki
  - r/bash
  - Greg's Wiki (mywiki.wooledge.org)
```

> 📖 **核心判断**：Shell 脚本生产力 = **严格模式 + getopts + flock + trap + retry + 结构化日志 + shellcheck**。**未加 `set -euo pipefail` 的脚本基本属于玩具**。文本处理用 grep/sed/awk/jq 四件套，能解决 80% 运维数据问题。**超过 500 行 / 复杂数据结构 / 长期维护时，立刻换 Python**——Bash 是粘合剂，不是程序员。

