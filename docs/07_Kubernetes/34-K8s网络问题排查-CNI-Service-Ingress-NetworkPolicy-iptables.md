# Kubernetes 网络问题排查（CNI / Service / Ingress / NetworkPolicy / iptables）

> Pod 访问不通？Service 连不上？Ingress 502？NetworkPolicy 不生效？K8s 网络问题排查的核心是「分层定位 + 逐段验证」。本文覆盖 CNI、Service、Ingress、NetworkPolicy、iptables 五大网络栈，从原理、工具、命令、案例到排障 SOP，一站讲透。

---

## 一、K8s 网络全景与排障方法论

### 1.1 K8s 网络四层模型

```text
K8s 网络四层模型 (从下往上):

  ┌─────────────────────────────────────────────────────────┐
  │  第 4 层: 入口层  Ingress / Gateway API                 │
  │         (外部 → 集群内 Service, 七层路由)                │
  ├─────────────────────────────────────────────────────────┤
  │  第 3 层: 服务层  Service / kube-proxy                  │
  │         (ClusterIP / NodePort / LB, 四层负载)           │
  ├─────────────────────────────────────────────────────────┤
  │  第 2 层: 连通层  CNI (Pod ↔ Pod / Pod ↔ Service)       │
  │         (flannel / calico / cilium / weave...)          │
  ├─────────────────────────────────────────────────────────┤
  │  第 1 层: 基础层  节点网络 + iptables + 路由 + DNS       │
  │         (节点互通 / IP 转发 / 内核参数)                  │
  └─────────────────────────────────────────────────────────┘

排障心法: 从下往上查, 先确认底层通再看上一层
       "底层不通, 上层都是虚的"
```

**各层对应组件**：

| 层级 | 核心组件 | 关键资源 | 常见问题 |
|:---|:---|:---|:---|
| 基础层 | kubelet / iptables / ipvs / sysctl | - | 内核参数不对、ip_forward 关闭、节点防火墙 |
| CNI 层 | CNI plugin + daemonset(flannel/calico/cilium) | Pod、IPAM | Pod 无 IP、跨节点不通、IP 冲突 |
| Service 层 | kube-proxy / iptables/ipvs/nftables | Service、Endpoints | ClusterIP 不通、NodePort 不通、负载不均 |
| Ingress 层 | ingress-controller(nginx/traefik) | Ingress、TLS Secret | 502/503/504、路由不匹配、TLS 握手失败 |
| 策略层 | kube-proxy + CNI + NetworkPolicy controller | NetworkPolicy | 策略不生效、该通不通、该断不断 |

### 1.2 分层排查法

```text
Pod A 访问 Pod B 不通的排查路径:

  起点: Pod A
    │
    ▼  1. Pod 内 DNS 正常吗?  (nslookup / dig)
    ├─ 不正常 → CoreDNS / 节点 resolv.conf / ndots
    └─ 正常 → 继续
         │
         ▼  2. Pod A → Pod B IP 直接通吗?  (curl / ping / nc)
         ├─ 不通 → 跳到「二、CNI 层排查」
         └─ 通 → 继续
              │
              ▼  3. Pod A → Service ClusterIP 通吗?
              ├─ 不通 → 跳到「三、Service 层排查」
              └─ 通 → 继续
                   │
                   ▼  4. 集群外 → NodePort / LoadBalancer 通吗?
                   ├─ 不通 → 看节点防火墙 / LB 配置 / externalTrafficPolicy
                   └─ 通 → 继续
                        │
                        ▼  5. 域名 → Ingress 通吗?
                        ├─ 不通 → 跳到「四、Ingress 层排查」
                        └─ 通 →  问题解决 ✓
```

### 1.3 排障工具链

| 工具 | 用途 | 在哪用 |
|:---|:---|:---|
| `kubectl exec` + `curl/wget/nc` | Pod 内连通性测试 | Pod 内(或 ephemeral container) |
| `kubectl debug` | 临时调试容器 | 有问题的 Pod 旁边 |
| `ping / mtr / traceroute` | 网络连通与路径 | 节点 / Pod |
| `ip addr / ip route / ip link` | 查看本机网络栈 | 节点 |
| `iptables-save / iptables -L` | 查看 iptables 规则 | 节点 |
| `ipvsadm -Ln` | 查看 ipvs 模式 | 节点(ipvs 模式) |
| `tcpdump` | 抓包分析 | 节点 / Pod |
| `conntrack` | 连接跟踪表 | 节点 |
| `dig / nslookup / host` | DNS 解析 | Pod / 节点 |
| `ss / netstat` | 端口监听 | 节点 / Pod |
| `cilium monitor` / `calicoctl` | CNI 专有工具 | 节点 / cilium/calico 环境 |
| `kubectl get events` | K8s 事件 | 任意位置 |
| `kubectl describe pod/svc/ing` | 资源详情 | 任意位置 |

**万能排查 Pod**(每个节点上放一个,方便调试):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: net-debug
  labels:
    app: net-debug
spec:
  containers:
    - name: debug
      image: nicolaka/netshoot    # 预装了 dig/nc/tcpdump/iperf/...
      command: ["sleep", "infinity"]
      securityContext:
        capabilities:
          add: ["NET_ADMIN", "NET_RAW"]
```

```bash
# 进入调试
kubectl exec -it net-debug -- bash
# 里面有: dig, nslookup, curl, wget, nc, tcpdump, iperf, mtr, traceroute...
```

### 1.4 验证命令速查模板

每次遇到网络问题,先跑这组命令,输出贴出来问题就定位了 80%:

```bash
# === Pod 内执行 (kubectl exec -it <pod> -- /bin/sh) ===
# 1. DNS
cat /etc/resolv.conf
nslookup kubernetes.default.svc.cluster.local
dig +short google.com

# 2. Pod 自身网络
ip addr
ip route
ip link show eth0

# 3. 到目标 Pod 的连通性
ping -c 3 <目标 Pod IP>
nc -vz <目标 Pod IP> <端口>
curl -s -o /dev/null -w "%{http_code}\n" http://<目标 Pod IP>:<端口>/healthz

# 4. 到 Service 的连通性
curl -sI http://<service-name>.<ns>.svc.cluster.local:8080/

# === 节点上执行 ===
# 5. CNI 状态
ip addr show cni0 2>/dev/null || ip addr show flannel.1 2>/dev/null || echo "no bridge, check CNI"
ip route | grep -E '10\.|172\.'
cat /etc/cni/net.d/10-*.conf | head -30

# 6. Service iptables/ipvs
iptables-save | grep -A5 <service-name> | head -20
# 或 ipvs 模式:
ipvsadm -Ln | grep -A5 <ClusterIP>

# 7. kube-proxy 日志
kubectl logs -n kube-system -l k8s-app=kube-proxy --tail=50
```

---

## 二、CNI 层排查（Pod ↔ Pod 不通）

### 2.1 CNI 工作原理

```text
Pod 网络创建流程 (以 bridge CNI 为例):

  kubelet 调用 CNI
  ├─ 1. 创建 veth pair: vethXXX(主机) + eth0(Pod netns)
  ├─ 2. 把 veth 一端放进 Pod netns, 命名为 eth0
  ├─ 3. 给 eth0 分配 Pod IP (IPAM: flannel/calico/dhcp)
  ├─ 4. 把 veth 另一端接到网桥 (cni0 / docker0)
  ├─ 5. 设置默认路由 (走网桥网关)
  └─ 6. 写 iptables MASQUERADE 规则 (访问外部时 SNAT)

跨节点流量路径 (flannel VXLAN 为例):
  Pod A ─→ veth ─→ cni0 ─→ flannel.1 (VXLAN 封装) ─→ eth0
                                                           │
                                                           ▼ 物理网络
  Pod B ←─ veth ←─ cni0 ←─ flannel.1 (VXLAN 解封装) ←─ eth0 (B节点)
```

### 2.2 Pod 拿不到 IP

**现象**：`kubectl get pod` 显示 `ContainerCreating`，describe 看到 `Failed to assign IP` 或 `network namespace` 相关错误。

**排查步骤**：

```bash
# 1. 看 Pod 事件 (最快定位)
kubectl describe pod <pod-name> | tail -30
# 找 Events 里的错误信息

# 2. 看 CNI DaemonSet 状态
kubectl get ds -n kube-system
kubectl get pods -n kube-system -l k8s-app=calico-node   # 或 flannel / cilium
kubectl logs -n kube-system <cni-pod> --tail=100          # 看 CNI 组件日志

# 3. 看节点上的 CNI 配置文件
ls -la /etc/cni/net.d/
cat /etc/cni/net.d/10-*.conf* | head -50

# 4. 看 IPAM 资源池是否耗尽
# Calico:
kubectl get ipamblocks.crd.projectcalico.org -o wide
calicoctl ipam show

# Flannel / host-local:
cat /var/lib/cni/networks/*/last_reserved_ip.0 2>/dev/null
ls /var/lib/cni/networks/*/  | wc -l
```

**常见原因与解决**：

| 原因 | 现象 | 解决 |
|:---|:---|:---|
| CNI pod 没起来 | Pod 全挂 / CrashLoopBackOff | 看日志，通常是节点网络不通 / RBAC 权限 |
| IP 地址池耗尽 | IPAM 报 `no available IPs` | 扩大 CIDR / 清理僵尸 Pod IP / 检查泄漏 |
| CNI 二进制缺失 | `failed to find plugin` | 重新安装 CNI / 节点镜像不完整 |
| kubelet --network-plugin 不对 | `cni config uninitialized` | 确认 kubelet 启动参数含 `--network-plugin=cni` |
| 节点 NotReady | Pod 调度不上去 / CNI 心跳失败 | 先查节点状态和节点网络 |

### 2.3 同节点 Pod 不通

同节点两 Pod 互 ping 不通 → 问题在本节点网桥 / iptables / NetworkPolicy。

```bash
# 1. 两个 Pod 的 IP 和 veth 找出来
kubectl get pod pod-a -o wide    # 记下 IP_A
kubectl get pod pod-b -o wide    # 记下 IP_B

# 2. 在节点上看网桥 (bridge / cni0 / docker0)
brctl show cni0        # 或 bridge link
ip link show type bridge
ip addr show cni0

# 3. Pod 的 veth 是否在网桥上
bridge link show

# 4. 直接从节点 ping Pod IP (验证 Pod 网络层可达)
ping -c 2 <Pod IP>

# 5. iptables 有没有 DROP 规则 (NetworkPolicy / 安全组)
iptables -S | grep -i drop | head -20
iptables -L FORWARD -nv --line-numbers | head -30
```

**同节点常见问题**：

| 现象 | 原因 | 解决 |
|:---|:---|:---|
| 同节点 Pod ping 不通 | 网桥没工作 / veth 没挂上 | 重启 CNI pod / 检查 br_netfilter 模块 |
| 能 ping 但 TCP 不通 | iptables DROP / NetworkPolicy | `iptables -L FORWARD -nv` 看计数器增长 |
| 访问时断时续 | MAC 地址冲突 / ARP 表异常 | `arp -a` 看，`ip neigh flush` 清一下 |

### 2.4 跨节点 Pod 不通

跨节点不通是**最常见**的问题, 90% 出在底层网络或防火墙。

```bash
# 1. 节点本身互通吗?
ping -c 3 <对端节点 IP>
mtr --report -w 2 <对端节点 IP>    # 丢包率 / 路径

# 2. Pod 网段路由对吗? (在节点上看)
ip route | grep <对端 Pod 网段>
# 应该有一条路由指向对端节点 (flannel) 或 bird (calico)

# 3. 节点间 VXLAN / IPIP 隧道正常吗?
# Flannel VXLAN:
ip link show flannel.1
ip -d link show flannel.1 | grep vxlan
bridge fdb show dev flannel.1 | head -10

# Calico IPIP:
ip tunl0
ip route | grep tunl0

# Calico BGP:
birdc show protocol
birdc show route

# 4. 节点防火墙/安全组放通了 CNI 端口吗?
# Flannel VXLAN: UDP 8472
# Calico BGP: TCP 179
# Calico IPIP: IP 协议 4 (不是端口!)
# Weave: UDP 6783 + TCP 6783
ss -lnu | grep 8472     # 看 VXLAN 监听
iptables -L INPUT -nv   # 看 INPUT 链有没有挡

# 5. 抓包看流量到哪了
# 在 A 节点上抓 VXLAN 包:
tcpdump -i eth0 -nn port 8472 and host <对端节点 IP>
# 在 B 节点上抓 Pod 接口:
tcpdump -i caliXXXX -nn host <源 Pod IP>
```

**跨节点不通的常见原因(按概率排序)**：

| 排名 | 原因 | 特征 | 解决 |
|:---|:---|:---|:---|
| 1 | 云安全组 / 防火墙挡了 VXLAN/BGP 端口 | 同节点通、跨节点完全不通 | 放通对应端口 / 协议 |
| 2 | 节点间网络本身不通 | ping 节点 IP 都不通 | 先修物理/虚拟网络 |
| 3 | CNI 路由没下发 | `ip route` 里没有对端 Pod 网段 | 重启 CNI pod / 看 CNI 日志 |
| 4 | Pod CIDR 与底层网络重叠 | 部分 IP 通部分不通 | 改 Pod CIDR / 规划网段 |
| 5 | `net.ipv4.ip_forward = 0` | 节点能 Ping Pod,Pod 出不去 | `sysctl -w net.ipv4.ip_forward=1` |
| 6 | VXLAN MTU 问题 | 小包通大包不通 / curl 慢 | 调小 MTU (1450 以下) |
| 7 | 网卡多队列 / RPS 问题 | 流量大才出问题 | 看网卡 ring buffer |

**MTU 问题典型现象**: `ping -s 1472 <Pod IP>`(刚好 MTU 大小) 不通, 但小 ping 通。解决: CNI 配置里把 MTU 调到 1450 或更小(考虑 VXLAN/IPIP 封装头)。

### 2.5 Pod 访问外部不通

```bash
# 1. Pod 内访问公网
kubectl exec -it <pod> -- curl -s -m 3 http://ifconfig.me

# 2. 节点上能访问公网吗? (先排除节点本身问题)
curl -s -m 3 http://ifconfig.me

# 3. 看节点上的 MASQUERADE 规则
iptables -t nat -L POSTROUTING -nv | head -30
iptables -t nat -S POSTROUTING | grep -i masquerade

# 4. 看 kube-proxy 模式下的 KUBE-MARK-MASQ
iptables -t nat -S | grep KUBE-MARK-MASQ | head -10
```

**常见原因**:
- `net.ipv4.ip_forward` 没开 → Pod 出站流量节点不转发
- 节点没外网 → Pod 自然也没有
- MASQUERADE 规则没了 → 源地址是 Pod IP 回不来
- 节点 iptables FORWARD 默认 DROP → CNI 没加 ACCEPT 规则

---

## 三、Service 层排查（ClusterIP / NodePort / LoadBalancer）

### 3.1 Service 原理（iptables 模式）

```text
Service (ClusterIP) 流量路径 (iptables 模式):

  Pod A → 访问 Service ClusterIP → 进入 netfilter
                                       │
                                       ▼
  ┌──────── PREROUTING (DNAT 阶段) ────────────────┐
  │  KUBE-SERVICES (按 ClusterIP:Port 匹配)          │
  │    ├─ KUBE-SVC-XXXX (对应具体 Service)           │
  │    │   ├─ KUBE-SEP-XXXX (Endpoint 1) → DNAT 到 Pod1 │
  │    │   ├─ KUBE-SEP-XXXX (Endpoint 2) → DNAT 到 Pod2 │
  │    │   └─ ... (按概率轮选, 不是真正负载均衡)       │
  │    └─ 不匹配 → 继续往下走                        │
  └──────────────────────────────────────────────────┘
                                       │
                                       ▼
  路由决策 → FORWARD → POSTROUTING (MASQUERADE, 需要的话)
                                       │
                                       ▼
                                      Pod B (真实后端)
```

### 3.2 ClusterIP 不通

ClusterIP 是 Service 的基础, 它不通时, NodePort / LoadBalancer 也不会通。

```bash
# 1. Service 存在吗? 配置对吗?
kubectl get svc <svc-name> -n <ns>
kubectl describe svc <svc-name> -n <ns>
# 看:
#   - ClusterIP 是多少
#   - Port / TargetPort 对不对
#   - Endpoints 有没有后端 Pod IP

# 2. Endpoints 正常吗? (90% 的 Service 问题都是 Endpoints 空)
kubectl get endpoints <svc-name> -n <ns>
kubectl describe endpoints <svc-name> -n <ns>
# 如果为空 → 下一步查为什么没后端

# 3. Endpoints 为空的原因排查
kubectl get pod -n <ns> --show-labels | grep <label>
# 和 Service selector 对比:
kubectl get svc <svc-name> -n <ns> -o jsonpath='{.spec.selector}'
# 标签对不上 → 改 label 或 selector
```

**Endpoints 为空的常见原因**：

| 原因 | 检查 | 解决 |
|:---|:---|:---|
| selector 写错 | 对比 svc.spec.selector 和 pod.labels | 改对 |
| Pod 没 Ready | Pod READY 列是 0/1, 健康检查失败 | 修健康检查 / 应用启动问题 |
| 端口不对 | targetPort 与 containerPort 不一致 | 对齐 |
| Pod 在别的 ns | selector 只在同 namespace 选 | 跨 ns 用 ExternalName 或手动写 Endpoints |
| headless service | ClusterIP: None | 正常, Endpoints 直接是 Pod IP |

**Endpoints 有值但还是不通**：

```bash
# 4. 直接 curl 后端 Pod IP 通吗? (先把 Service 排除掉)
kubectl exec -it <客户端 Pod> -- curl -s -m 3 http://<Pod IP>:<端口>/healthz
# 不通 → 返回二章查 CNI / Pod 本身问题
# 通了 → 继续查 Service 层

# 5. 节点上看 iptables 里的 Service 规则
# 先找 Service 对应的 chain:
iptables -t nat -S KUBE-SERVICES | grep <ClusterIP>
# 或模糊找:
iptables -t nat -S | grep <Service 名>

# 6. 看对应 KUBE-SVC-XX 链里的 Endpoints
iptables -t nat -S KUBE-SVC-XXXXX
# 每个 Endpoint 对应一个 KUBE-SEP-XX 链

# 7. 计数器法: 看规则有没有命中
iptables -t nat -L KUBE-SVC-XXXXX -nv
# pkts 和 bytes 列增长 = 流量到过这里但被转发了
# 不增长 = 流量压根没走到这个链

# 8. kube-proxy 日志
kubectl logs -n kube-system -l k8s-app=kube-proxy --tail=50 | grep -i 'error\|fail\|sync'
```

**常见 Service 层问题**：

| 现象 | 原因 | 解决 |
|:---|:---|:---|
| curl ClusterIP 超时 | Pod 不通 / iptables 没下发 | 先查 Pod, 再看 kube-proxy |
| curl ClusterIP Connection refused | targetPort 写错 / Pod 没监听 | 进 Pod 内 `ss -ltn` 看端口 |
| 时通时不通 | 只有部分后端好 / 连接跟踪表满 | 看哪个后端挂了 / `conntrack -S` |
| 新建连接慢 / 第一个包丢 | conntrack 表满 + 新连接被丢 | `sysctl net.netfilter.nf_conntrack_max` 调大 |

### 3.3 NodePort 不通

NodePort = ClusterIP + 节点上开端口 + DNAT。ClusterIP 通了 NodePort 才可能通。

```bash
# 1. ClusterIP 通了吗? (先跳过 NodePort, 直接测 ClusterIP)
# 不通 → 按 3.2 查
# 通了 → 继续

# 2. 节点上监听了吗?
# iptables 模式: 不是真的监听端口, 是 iptables 规则, 所以 ss 看不到
# 验证 iptables 规则:
iptables -t nat -S KUBE-NODEPORTS | grep <NodePort 端口>
iptables -t nat -L KUBE-NODEPORTS -nv --line-numbers | grep <端口>

# 3. 从集群外 curl 节点 IP:NodePort
curl -v http://<节点 IP>:<NodePort>/

# 4. 节点防火墙 / 安全组放行了吗?
# 云环境最常见: 安全组没放行 NodePort 端口范围 (默认 30000-32767)
iptables -L INPUT -nv | grep <NodePort 端口>
# 或直接看云控制台安全组

# 5. externalTrafficPolicy 影响
# Local: 只转发给本节点上的 Pod, 保留源 IP, 但本节点没 Pod 会丢包
kubectl get svc <svc> -o jsonpath='{.spec.externalTrafficPolicy}'
```

**externalTrafficPolicy = Local 的坑**:

```text
externalTrafficPolicy: Local 模式:
  客户端 → NodePort → 只转发给本节点上的 Pod
  优点: 保留客户端源 IP
  缺点: 本节点没 Pod → 直接丢包 (表现为连接超时/被拒)

Cluster (默认):
  客户端 → NodePort → 可能转发到其他节点的 Pod → 会再跳一次
  优点: 后端在任何节点都能通
  缺点: 源 IP 变成了中转节点的 IP
```

### 3.4 ipvs 模式排查

kube-proxy 用 ipvs 模式时, 负载均衡在内核 ipvs 模块做, 性能更好但排查命令不同。

```bash
# 1. 确认 ipvs 模式
kubectl get cm kube-proxy -n kube-system -o yaml | grep mode
# 或看节点上:
lsmod | grep ip_vs
ipvsadm -Ln | head -20

# 2. Service 对应的 Virtual Server
ipvsadm -Ln | grep -A10 <ClusterIP>:<Port>
# 输出类似:
#  TCP  10.96.0.1:443 rr
#   -> 10.244.1.5:6443            Masq    1      0          0
#   -> 10.244.2.6:6443            Masq    1      0          0

# 3. 后端列表对吗? 权重对吗?
ipvsadm -Ln --sort | grep -A10 <svc-name>

# 4. 连接数/活跃连接
ipvsadm -Ln --stats
# ConnPkts CPS InPPS OutPPS InBPS OutBPS
```

### 3.5 负载不均衡

```text
iptables 模式为什么不是"真正的负载均衡"?

  iptables 用 -m statistic --mode random --probability=0.5
  概率分配, 不是轮询。
  后端数少 (2-3 个) 时偏差较大, 流量小的时候可能很不均匀。

ipvs 模式:
  支持 rr/lc/dh/sh/sed/nq 等多种算法, 是真负载均衡。
```

**负载不均排查**:

```bash
# 看各后端的连接数
# iptables 模式: 看 KUBE-SEP 各链的计数器
iptables -t nat -L KUBE-SVC-XXXX -nv | grep KUBE-SEP

# ipvs 模式:
ipvsadm -Ln --stats | grep -A10 <ClusterIP>

# 偏差大吗? (iptables 模式 6:4 到 7:3 都是正常的)
# 解决:
#   - 小流量 + 高均匀度要求 → 切 ipvs 模式
#   - 后端 Pod 数多了自然趋向均匀 (大数定律)
```

### 3.6 连接跟踪表满了

```bash
# 查看 conntrack 状态
conntrack -S
# 或:
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max

# 满了的现象:
#   - dmesg 里有 "nf_conntrack: table full, dropping packet"
#   - 新建连接超时 / 随机丢包
dmesg | grep -i conntrack | tail -10

# 调大:
sysctl -w net.netfilter.nf_conntrack_max=262144
echo "net.netfilter.nf_conntrack_max = 262144" >> /etc/sysctl.d/99-k8s.conf

# 缩短超时时间 (让表条目尽快回收)
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=3600
```

---

## 四、Ingress 层排查（5xx / 路由不匹配）

### 4.1 Ingress 工作原理

```text
Ingress 流量路径 (以 nginx-ingress 为例):

  浏览器 → 公网 DNS → LB IP → NodePort (或 LB 直通)
                                    │
                                    ▼
  ┌────── Ingress Controller Pod (nginx) ────────┐
  │                                                │
  │  1. TLS 终止 (如果有 HTTPS)                    │
  │  2. 匹配 Ingress 规则 (host + path)            │
  │  3. 路由到后端 Service (ClusterIP)            │
  │  4. 反向代理到真实 Pod IP                      │
  │                                                │
  └──────────────────┬─────────────────────────────┘
                     │
                     ▼
                 Service → Endpoints → Pod
```

### 4.2 502 Bad Gateway

502 是 nginx 收不到后端响应 (连不上后端 / 后端直接 reset)。

```bash
# 1. 看 ingress-controller 日志
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller --tail=50 | grep -i '502\|error\|upstream'
# 典型错误:
#   connect() failed (111: Connection refused) while connecting to upstream
#   upstream prematurely closed connection while reading response header

# 2. 后端 Service 直接通吗? (绕过 Ingress)
kubectl exec -it <任意 Pod> -- curl -sI http://<svc>.<ns>.svc.cluster.local:<port>/
# 也不通 → Service 问题, 按第三章查
# 通 → 是 Ingress 配置的问题

# 3. Ingress 配置对吗?
kubectl get ing <ingress-name> -n <ns> -o yaml
kubectl describe ing <ingress-name> -n <ns>
# 检查:
#   - host 域名对吗?
#   - path 匹配吗? (前缀匹配 / 精确匹配)
#   - service.name / service.port.name 对吗?
#   - tls 配置的 secret 存在吗?

# 4. nginx 里实际生成的 upstream 是什么?
kubectl exec -n ingress-nginx <controller-pod> -- cat /etc/nginx/nginx.conf | grep -A20 <域名>
# 看 upstream 指向的 IP:Port 对不对

# 5. 后端 Pod 的健康状况
kubectl get pod -n <ns> -l <selector>
kubectl describe pod <pod> | tail -20
```

**502 常见原因**：

| 原因 | 日志表现 | 排查 |
|:---|:---|:---|
| 后端 Pod 挂了 / 端口没监听 | `Connection refused` | curl 后端 Pod IP 验证 |
| 后端处理超时 | `upstream timed out` | 看应用日志 / 调大 proxy-read-timeout |
| 后端主动断开 | `prematurely closed connection` | 应用异常退出 / keepalive 配置错 |
| Service 配置错 | upstream 里 IP 不对 / 端口不对 | 看 nginx.conf 的 upstream |
| TLS 配置错 (后端 HTTPS) | `SSL_do_handshake() failed` | 后端证书 / 协议不匹配 |
| Pod 刚启动还没 Ready | 随机 502, 很快恢复 | 配好 readinessProbe |

### 4.3 503 Service Temporarily Unavailable

503 = nginx 知道这个 upstream, 但后端全挂了 / 没健康后端。

```bash
# 1. Endpoints 有值吗?
kubectl get endpoints <svc> -n <ns>
# 空 → 按 3.2 查

# 2. 后端 Pod 都 NotReady?
kubectl get pod -n <ns> -l <selector>
# READY 列 0/1 → 健康检查失败

# 3. nginx ingress 的 upstream 里 backend 是 down?
kubectl exec -n ingress-nginx <pod> -- grep -A10 'upstream.*<svc>' /etc/nginx/nginx.conf

# 4. 是不是 session affinity / 一致性 hash 的问题?
# 导致请求被分配到一个挂了的后端
```

### 4.4 504 Gateway Timeout

504 = nginx 等后端响应超时了。

```bash
# 1. 应用响应真的慢吗?
kubectl exec -it <pod> -- time curl -s http://<Pod IP>:<port>/慢接口
# 慢 → 优化应用 / 调大 nginx 超时

# 2. 调大 nginx 超时
# 通过 annotation:
kubectl annotate ingress <ingress-name> \
  nginx.ingress.kubernetes.io/proxy-read-timeout=300 \
  nginx.ingress.kubernetes.io/proxy-send-timeout=300 \
  -n <ns>
```

### 4.5 404 Not Found

404 = Ingress 规则没匹配上。

```bash
# 1. 看 Ingress 规则的 host/path
kubectl get ing -n <ns> -o wide
# Host 列 / Address 列对吗?

# 2. 域名解析对吗? 指向的是 Ingress 入口 IP 吗?
nslookup <域名>
dig +short <域名>

# 3. path 是前缀匹配还是精确匹配?
# pathType: Prefix / Exact / ImplementationSpecific
kubectl get ing <ing> -n <ns> -o jsonpath='{.spec.rules[0].http.paths[0].pathType}'

# 4. Ingress Class 对吗?
kubectl get ingclass
kubectl get ing <ing> -n <ns> -o jsonpath='{.spec.ingressClassName}'
# 多个 ingress controller 共存时最容易配错 class

# 5. 看 controller 日志里有没有 "ignoring" / "skipping"
kubectl logs -n ingress-nginx <controller-pod> --tail=100 | grep -i 'ignore\|skip\|invalid'
```

**常见 404 原因**：

| 原因 | 特征 | 解决 |
|:---|:---|:---|
| host 写错 (含 www / 不含 www) | 直接输 IP 能通, 域名 404 | 写对 / 加通配 |
| path 前缀不匹配 | `/api` 能通 `/api/` 不通 或反着 | 统一尾部斜杠 / 用正则 |
| ingressClassName 不对 | 规则对的但 nginx 里完全没这条 | 改成正确的 class |
| 多 Ingress 冲突同名 host | 一会儿 404 一会儿 200 | 合并到一个 Ingress |
| TLS 配置错 | HTTP 正常, HTTPS 404 / 421 | 检查 secret + cert |

### 4.6 TLS / HTTPS 问题

```bash
# 1. 证书还在有效期内吗?
kubectl get secret <tls-secret> -n <ns> -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -dates -subject -issuer

# 2. 证书链完整吗?
openssl s_client -connect <域名>:443 -servername <域名> </dev/null | head -30
# 看 Verify return code: 0 (ok)

# 3. 私钥和证书匹配吗?
kubectl get secret <tls-secret> -n <ns> -o jsonpath='{.data.tls\.key}' | base64 -d | openssl rsa -check -noout
# 模数对比:
CRT_MOD=$(kubectl get secret <tls> -n <ns> -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -modulus -noout | md5sum)
KEY_MOD=$(kubectl get secret <tls> -n <ns> -o jsonpath='{.data.tls\.key}' | base64 -d | openssl rsa -modulus -noout | md5sum)
echo "CRT: $CRT_MOD"; echo "KEY: $KEY_MOD"
# 不一样 = 证书私钥不匹配

# 4. Ingress 引用的 secret 存在吗?
kubectl describe ing <ing> -n <ns> | grep -i tls
kubectl get secret <tls-secret> -n <ns>
# secret 不在同一 ns → 必须在同一 ns (Ingress 设计)
```

### 4.7 Ingress Controller 常用调试

```bash
# 查看 nginx 配置 (最有价值)
kubectl exec -n ingress-nginx <controller-pod> -- cat /etc/nginx/nginx.conf > nginx.conf
grep -A20 'server_name <域名>' nginx.conf
grep -A10 'upstream' nginx.conf | head -40

# 开启 debug 日志 (排查路由匹配)
kubectl annotate ingress <ingress-name> nginx.ingress.kubernetes.io/enable-access-log=true -n <ns>
kubectl logs -n ingress-nginx <pod> -f | grep '<你的 IP>'

# 查看虚拟主机列表
kubectl exec -n ingress-nginx <pod> -- nginx -T 2>/dev/null | grep 'server_name'

# reload 了几次? 有没有失败?
kubectl exec -n ingress-nginx <pod> -- nginx -t     # 测试配置语法
kubectl logs -n ingress-nginx <pod> | grep -i 'reload\|error' | tail -20

# 后端健康检查 (nginx ingress 的 upstream 健康状态)
kubectl exec -n ingress-nginx <pod> -- cat /etc/nginx/nginx.conf | grep -B2 -A10 'upstream'
```

---

## 五、DNS 问题排查

### 5.1 K8s DNS 原理

```text
Pod DNS 解析流程:

  Pod /etc/resolv.conf
  ├─ nameserver 10.96.0.10    ← CoreDNS Service ClusterIP
  ├─ search default.svc.cluster.local svc.cluster.local cluster.local
  └─ options ndots:5

  解析顺序 (以访问 "service-a" 为例):
  1. service-a.default.svc.cluster.local   (命中 → 返回 ClusterIP)
  2. service-a.svc.cluster.local           (找不到)
  3. service-a.cluster.local               (找不到)
  4. service-a                              (作为绝对域名查)
```

### 5.2 DNS 解析失败 / 慢

```bash
# 1. Pod 内的 resolv.conf 对吗?
kubectl exec -it <pod> -- cat /etc/resolv.conf
# 应该有 nameserver = CoreDNS Service IP
# search 域应该有 3 个 (svc 相关)
# ndots: 5 是默认的

# 2. CoreDNS pod 在吗?
kubectl get pod -n kube-system -l k8s-app=kube-dns
kubectl get svc kube-dns -n kube-system

# 3. 直接解析集群内域名
kubectl exec -it <pod> -- nslookup kubernetes.default.svc.cluster.local
kubectl exec -it <pod> -- dig +short kubernetes.default.svc.cluster.local

# 4. 解析公网域名
kubectl exec -it <pod> -- nslookup google.com

# 5. CoreDNS 日志
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50
# 开启 CoreDNS 详细日志 (排查用):
kubectl -n kube-system edit configmap coredns
# 在 .:53 { 下加一行 log
```

**常见 DNS 问题**：

| 现象 | 原因 | 解决 |
|:---|:---|:---|
| 所有解析都超时 | CoreDNS 挂了 / 连不上 Service | 查 CoreDNS pod / kube-dns Service |
| 集群内域名不通公网通 | CoreDNS 配置错 / 没有 Kubernetes 插件 | 看 CoreDNS ConfigMap |
| 公网不通集群内通 | 上游 DNS 有问题 | 看 forward 插件配置的上游 |
| 解析很慢 (5s 左右) | ndots:5 + 搜索域逐个试 + 超时重试 | 服务名写全 (带 `.svc.cluster.local.` 结尾点号) |
| 个别解析随机失败 | CoreDNS 负载不均 / conntrack 表满 | 加 CoreDNS 副本 / 调 conntrack |
| Alpine 镜像解析异常 | musl 的 DNS 实现和 glibc 不同 | 用 debian-slim / 升级 musl / 用 fully qualified domain |

**Alpine DNS 的经典坑**：

```text
Alpine + musl 的 DNS 行为差异:
  - 搜索域 (search) 行为与 glibc 不同
  - 多个 nameserver 时并发请求, 用先回的那个
  - /etc/resolv.conf 最多读 3 个 nameserver, 且 search 最多 6 个
  - 老版本不支持 options ndots:5

典型现象: 同一个域名, debian 镜像解析正常, alpine 镜像偶发失败。
解决:
  - 用 fully qualified 域名 (末尾加 .), 跳过搜索域
  - 换基础镜像 (debian-slim / distroless)
  - 升级 alpine 到 3.18+
```

---

## 六、NetworkPolicy 排查（该通不通 / 该断不断）

### 6.1 NetworkPolicy 工作原理

```text
NetworkPolicy 工作方式:

  1. 你创建 NetworkPolicy 资源
  2. NetworkPolicy controller (Calico / Cilium / kube-router ...) 监听
  3. 在节点上生成对应的 iptables / eBPF / OpenFlow 规则
  4. Pod 进出流量被规则匹配

  ⚠️  没有 NetworkPolicy controller 的集群, NetworkPolicy 资源创建了也不生效
     (flannel 默认不带网络策略实现, 需要配合 calico / cilium 等)
```

### 6.2 NetworkPolicy 不生效

```bash
# 1. 集群有 NetworkPolicy 实现吗?
kubectl get crd | grep -i networkpolicy
# 检查 CNI 插件:
#   - Calico: 支持
#   - Cilium: 支持
#   - Flannel 单独: 不支持 (需配合 Canal / Calico 策略模式)
#   - Weave: 支持

# 2. NetworkPolicy 创建了吗?
kubectl get networkpolicy -n <ns>
kubectl describe netpol <policy-name> -n <ns>

# 3. PodSelector 选中了哪些 Pod?
# 查 policy 的 podSelector, 然后看哪些 Pod 被选中:
kubectl get pod -n <ns> --show-labels | grep <label-key>=<label-value>

# 4. 默认拒绝 / 默认允许?
# 有一个 policy 匹配到 Pod → 默认拒绝所有未明确允许的流量
# 没有任何 policy 匹配 → 默认全通
```

### 6.3 该通不通（策略挡了正常流量）

```bash
# 1. 先确认是不是 NetworkPolicy 的锅
# 临时把相关 policy 全删了再测:
kubectl get netpol -n <ns> -o name | xargs kubectl delete -n <ns>
# 还是不通 → 不是 NetworkPolicy 的问题, 按前面章节查
# 通了 → 是 NetworkPolicy 挡的, 继续定位哪条规则

# 2. 看 policy 里允许了哪些流量
kubectl get netpol <policy> -n <ns> -o yaml
# policyTypes: Ingress / Egress / Both
# ingress.from / egress.to 规则

# 3. Calico 环境: 看实际生成的规则
calicoctl get policy -o wide
calicoctl get profile <profile-name> -o yaml

# 4. iptables 方式: 看计数器
# 在节点上, 找被挡的流量对应链的 DROP 计数:
iptables -L INPUT -nv | head -30
iptables -L FORWARD -nv | head -30
# 或者:
iptables-save | grep -i 'drop\|reject' | head -20

# 5. Cilium 环境: 用 cilium 工具查
cilium monitor --type drop    # 实时看被丢的包
cilium policy get             # 当前策略
```

**常见"该通不通"原因**：

| 原因 | 现象 | 解决 |
|:---|:---|:---|
| policyType 只写了 Ingress 没写 Egress | 入站好出站挂 | policyTypes 加 Egress 或不写(默认有规则就启用) |
| from/to 标签写错 | 选不到源/目的 Pod | 用 `kubectl get pod -l` 验证 |
| 漏了 DNS 端口 | 应用能 ping 但域名解析失败 | Egress 规则放通 UDP 53 到 kube-system |
| 端口是 targetPort 不是 containerPort | 应用监听 8080, policy 写了 80 | policy 写 containerPort 号 |
| namespaceSelector 缺 ns 标签 | 跨 ns 访问不通 | 给 namespace 打 label |

### 6.4 该断不断（策略没挡住）

```bash
# 1. Policy 真的选中 Pod 了吗?
# 给 Pod 打标看 policy 有没生效
# 或者看 Calico profile 是否关联

# 2. 默认允许还是默认拒绝?
# 验证: 发一条完全不在 policy 里的流量测试
# 通了 = 默认允许 (说明 policy 没覆盖到这个 Pod)
# 不通 = 默认拒绝 (policy 已经在管了)

# 3. 是不是有其他 policy 反而放行了?
kubectl get netpol -A -o wide
# 多个 policy 是 OR 关系: 任何一个放行就放行了

# 4. 使用的 CNI 真支持 NetworkPolicy 吗?
# 最坑的一种: 集群跑的 flannel, 以为有 NetworkPolicy, 实际没有
# 验证: 建一条 deny all policy, 测试是否被挡
```

### 6.5 零信任基线（推荐直接用）

```yaml
# 默认拒绝: 每个命名空间先建一个默认全拒
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: <ns>
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
# 放行 DNS (Egress 必须的)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: <ns>
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

---

## 七、iptables 深度排查

### 7.1 K8s 相关 iptables 表与链

```text
K8s 使用的 iptables 表:

  nat 表 (地址转换):
    PREROUTING    ← 入站 DNAT (Service/NodePort)
    INPUT         ← 本机的 DNAT
    OUTPUT        ← 本机进程发出的 DNAT
    POSTROUTING   ← 出站 SNAT/MASQUERADE

  filter 表 (过滤):
    INPUT         ← 入站流量过滤
    FORWARD       ← 转发流量过滤 (Pod ↔ Pod)
    OUTPUT        ← 出站流量过滤

K8s 自定义链:
  KUBE-SERVICES      → 所有 Service 入口
  KUBE-SVC-XXXXX     → 单个 Service (跳转到各 SEP)
  KUBE-SEP-XXXXX     → 单个 Endpoint (DNAT + 标记)
  KUBE-NODEPORTS     → NodePort 入口
  KUBE-LOAD-BALANCER → LoadBalancer 入口
  KUBE-MARK-MASQ     → 打 MASQUERADE 标记 (0x4000)
  KUBE-MARK-DROP     → 打 DROP 标记
  KUBE-POSTROUTING   → POSTROUTING 里的 K8s 处理
  KUBE-FORWARD       → FORWARD 里的 K8s 处理
  KUBE-NWPLCY-XXX    → NetworkPolicy (如果用 iptables 实现)
```

### 7.2 常用 iptables 排查命令

```bash
# 1. 看所有 Service 的 NAT 规则 (nat 表)
iptables -t nat -S KUBE-SERVICES | head -50

# 2. 找特定 Service:
iptables -t nat -S | grep <Service 名称>
iptables -t nat -S | grep <ClusterIP>

# 3. 看单个 Service 的 SVC 链 (列出所有后端)
iptables -t nat -S KUBE-SVC-XXXXXX

# 4. 看规则命中计数 (看流量有没有走到这里)
iptables -t nat -L KUBE-SVC-XXXXXX -nv --line-numbers
# pkts 列增长 = 流量到过
# pkts = 0 = 流量没走到, 往前查

# 5. 看 FORWARD 链 (Pod 转发流量)
iptables -L FORWARD -nv --line-numbers | head -40

# 6. 看 POSTROUTING (SNAT/MASQUERADE)
iptables -t nat -L POSTROUTING -nv --line-numbers | head -30

# 7. 看 NetworkPolicy 相关链 (如果是 iptables 实现的)
iptables -S | grep -i 'nwpolicy\|cali\|kube-netpol' | head -20
```

**用计数器法定位断点**:

```text
思路: 从外往里, 逐条链看计数器有没有增长。

例: 访问 NodePort 不通

  1. KUBE-NODEPORTS 计数器 + 了吗?
     ├─ 没 + → 流量没到节点 (防火墙 / LB / 网络)
     └─ + 了 → 继续

  2. KUBE-SVC-XX (Service 链) + 了吗?
     ├─ 没 + → NodePort 跳 SVC 有问题 (规则写错 / 配置不对)
     └─ + 了 → 继续

  3. KUBE-SEP-XX (某个后端) + 了吗?
     ├─ 没 + → Endpoints 有问题 / 概率分配没到
     └─ + 了 → 继续

  4. DNAT 到 Pod IP 后, FORWARD 链 + 了吗?
     ├─ 没 + → 路由问题 / Pod 不在本节点
     └─ + 了 → 继续

  5. Pod 内应用收到了吗?
     ├─ 没收到 → CNI / veth / iptables DROP
     └─ 收到了 → 应用层问题 (返回错误 / 超时)
```

### 7.3 抓包神器 tcpdump

```bash
# 1. 在 Pod 所在节点上抓 Pod 的 veth 口
# 先找 Pod 的 veth:
kubectl get pod <pod> -n <ns> -o jsonpath='{.status.podIP}'
# 或在节点上:
ip link show | grep -E 'cali|veth|eth0'

# 抓到 Pod 接口上 (Calico 为例, 接口名 caliXXXXXX):
tcpdump -i caliXXXX -nn host <源 IP> and port <端口>
tcpdump -i caliXXXX -nn -A 'tcp port 80'   # 看 HTTP 内容

# 2. 抓节点物理网卡 (看流量进出节点)
tcpdump -i eth0 -nn host <对端 IP> and port <端口>

# 3. 抓 VXLAN 封装包 (flannel/calico VXLAN)
tcpdump -i eth0 -nn udp port 8472

# 4. 按方向过滤
tcpdump -i any -nn 'src host 10.244.1.10 and dst port 80'
tcpdump -i any -nn 'dst host 10.96.0.10 and port 53'   # DNS 请求

# 5. 保存到文件用 Wireshark 分析
tcpdump -i eth0 -w /tmp/capture.pcap -s 0 host <IP>
# -s 0 抓完整包
```

### 7.4 抓包 + iptables 组合定位

**经典组合拳**：流量从 A 到 B 不通,不知道断在哪。

```bash
# 同时在 A Pod 接口、节点 eth0、B 节点 eth0、B Pod 接口抓包
# 看到包出现在哪一层, 断在哪一层, 问题就定位了

# 节点 A:
tcpdump -i <A的veth> host <B的IP> and port 80    # Pod A 侧
tcpdump -i eth0 host <节点B的IP> and port 80     # 节点 A 出网

# 节点 B:
tcpdump -i eth0 host <节点A的IP> and port 80     # 节点 B 入网
tcpdump -i <B的veth> host <A的IP> and port 80    # Pod B 侧

# 四层都有包 → 应用层问题 (应用回包失败 / 防火墙)
# 到第 2 层有第 3 层没 → 物理网络 / 安全组
# 到第 3 层有第 4 层没 → CNI / iptables FORWARD / NetworkPolicy
```

---

## 八、经典故障案例

### 8.1 案例一: 新集群 Service 完全不通

**现象**: 新建集群, Pod 之间 Ping 通,但 Service ClusterIP 全不通。

**排查**:
1. `kubectl get endpoints` → 有后端 ✓
2. `iptables -t nat -L KUBE-SERVICES -n` → 空 ❌
3. `kubectl logs -n kube-system kube-proxy-xxx` → `failed to sync iptables rules`
4. `lsmod | grep ip_tables` → 模块没加载
5. 节点 OS 是最小化安装,缺 iptables 相关内核模块

**解决**:
```bash
modprobe ip_tables iptable_nat iptable_filter xt_conntrack
echo "ip_tables" >> /etc/modules-load.d/k8s.conf
# 重启 kube-proxy
kubectl delete pod -n kube-system -l k8s-app=kube-proxy
```

### 8.2 案例二: 凌晨流量高峰期随机 502

**现象**: 业务低峰正常,高峰期随机 502,日志显示 upstream connect timeout。

**排查**:
1. nginx 日志显示 `upstream timed out (110: Connection timed out)`
2. 后端 Pod 正常, CPU/内存都低
3. 节点上 `dmesg | grep conntrack` → `nf_conntrack: table full, dropping packet`
4. `cat /proc/sys/net/netfilter/nf_conntrack_count` → 已经到 max 了

**解决**:
```bash
sysctl -w net.netfilter.nf_conntrack_max=524288
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=300
# 同时加进 /etc/sysctl.d/ 持久化
```

### 8.3 案例三: 跨节点调用忽快忽慢

**现象**: 同节点调用快,跨节点调用时快时慢,慢的时候 curl 要等 5 秒。

**排查**:
1. 大文件传不动,小文件可以 → 怀疑 MTU
2. `ping -s 1472 -M do <跨节点 Pod IP>` → 不通 ❌
3. `ping -s 1400 -M do <跨节点 Pod IP>` → 通 ✓
4. 确认是 VXLAN 封装后超过物理网卡 MTU 导致分片丢包
5. 检查 CNI 配置 → MTU 设的 1500 (默认),但 VXLAN 要占 50 字节

**解决**: CNI 配置里把 MTU 调到 1450 (1500 - 50 VXLAN 头)。Calico: `calicoctl config set mtu 1450`; Flannel: 改 daemonset 的 `--iface` 和 `vni` 旁的 `--mtu 1450`。

### 8.4 案例四: NetworkPolicy 配了 DNS 还是不通

**现象**: 命名空间建了默认拒绝 + 放行 53 端口 DNS,但应用还是解析失败。

**排查**:
1. Policy 只放行了 UDP 53,没放行 TCP 53
2. 大响应时 DNS 会走 TCP (响应 > 512 字节走 TCP)
3. 应用在做大量 SRV 记录查询,响应大用 TCP,被挡住了

**解决**: Egress 规则同时放 UDP 和 TCP 的 53 端口。

### 8.5 案例五: Ingress 404 但规则看着对

**现象**: Ingress 规则创建了,describe 看着没问题,访问就是 404。

**排查**:
1. `kubectl get ingressclass` → 有两个 class (`nginx` 和 `nginx-internal`)
2. `kubectl get ing <name> -o yaml` → `ingressClassName` 是 `nginx-internal`
3. 但访问的是外部 LB IP(对应 `nginx` 那个 controller)
4. 两个 ingress controller 各管各的,规则配到内部那个了

**解决**: 把 `ingressClassName` 改成正确的 `nginx`。

---

## 九、速查表

### 9.1 常见端口

| 端口 | 协议 | 用途 |
|:---|:---|:---|
| 6443 | TCP | K8s API Server |
| 2379-2380 | TCP | etcd |
| 10250 | TCP | kubelet API |
| 10257 | TCP | kube-controller-manager |
| 10259 | TCP | kube-scheduler |
| 8472 | UDP | Flannel VXLAN |
| 179 | TCP | Calico BGP |
| 4789 | UDP | Calico VXLAN / Weave |
| 6783-6784 | TCP/UDP | Weave Net |
| 30000-32767 | TCP/UDP | NodePort 默认范围 |
| 53 | UDP/TCP | DNS (CoreDNS) |
| 44134 | TCP | Cilium Hubble |

### 9.2 常用内核参数

```text
net.ipv4.ip_forward = 1                    # 必须开 (Pod 转发)
net.bridge.bridge-nf-call-iptables = 1     # 网桥流量过 iptables
net.bridge.bridge-nf-call-ip6tables = 1    # IPv6 版
net.netfilter.nf_conntrack_max = 262144    # 连接跟踪表大小 (根据机器调整)
net.netfilter.nf_conntrack_tcp_timeout_established = 86400  # 建立连接超时 (默认 5 天)
net.ipv4.tcp_tw_reuse = 1                  # TIME_WAIT 复用
fs.inotify.max_user_instances = 8192       # inotify 实例数 (容器多时要调大)
fs.inotify.max_user_watches = 524288       # inotify 监听数
net.ipv4.conf.all.rp_filter = 0            # 反向路径过滤 (多网卡环境要关)
```

### 9.3 排障 SOP 清单

```text
Pod 之间不通:
  □ Pod 有 IP 吗? (kubectl get pod -o wide)
  □ Pod 是 Ready 吗?
  □ 同节点通吗?  (同节点不通 → 本节点 iptables / 网桥)
  □ 跨节点通吗?  (跨节点不通 → 物理网络 / 防火墙 / CNI 路由)
  □ 节点 IP 之间通吗?
  □ CNI pod 正常吗?
  □ iptables FORWARD 链 DROP 计数涨吗?

Service 不通:
  □ Endpoints 有值吗?
  □ 直接 curl Pod IP:Port 通吗?
  □ iptables/ipvs 里有 Service 对应规则吗?
  □ kube-proxy 日志有报错吗?
  □ conntrack 表满了吗?

Ingress 5xx:
  □ 直接访问 Service 通吗? (先排除后端)
  □ Ingress 规则匹配吗? (host + path)
  □ controller 日志显示什么错误?
  □ nginx upstream 配置对吗?
  □ 后端 Pod Ready 吗?

DNS 不通:
  □ resolv.conf 对吗?
  □ CoreDNS pod 正常吗?
  □ 直接 nslookup 集群域名?
  □ nslookup 公网域名?
  □ 是不是 Alpine 的坑?

NetworkPolicy 问题:
  □ 集群有 NetworkPolicy 实现吗?
  □ Policy 选中了 Pod 吗?
  □ 删除所有 policy 后还不通吗? (排除法)
  □ Egress 放通 DNS 了吗?
  □ 跨 ns 的 namespaceSelector 对吗?
```

### 9.4 一句话定位法

```text
Pod 间不通看 CNI,
Service 不通看 Endpoints,
Ingress 5xx 看后端,
404 看 host+path,
解析慢看 ndots,
时通时断看 conntrack,
跨节点慢看 MTU,
全部挂了看节点。
```

*最后更新: 2026-08-25*
