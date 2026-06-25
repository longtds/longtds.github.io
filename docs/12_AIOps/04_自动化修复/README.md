# 自动化修复

> AIOps 终极目标：**机器知道、机器决定、机器执行**。从"告警 → 人工"到"告警 → 自愈"，是 SRE 进化的最高形态——但也是**最容易翻车的方向**。

## 一、为什么要自动化修复

```
痛点:
  - 半夜被叫醒做"教科书操作"（rollout restart / drain）
  - 重复同样的处置 N 次
  - 人手不够（一个 SRE 管 1000+ 服务）
  - MTTR 受限于"人响应时间"

目标:
  - 标准化处置 → 流程化
  - 流程化 → 脚本化
  - 脚本化 → 自动化（要审批）
  - 自动化 → 自愈（无人干预）

→ 自动化的核心不是"省人"，而是"标准化 + 一致性 + 速度"
```

## 二、自动化等级（L0-L5）

```
L0 全人工        手册操作，无脚本
L1 脚本化        有脚本，但需人工执行
L2 平台化        Web 平台一键执行，有审批
L3 半自动        监控触发推荐，人工确认
L4 受控自动      低风险场景自动执行，高风险审批
L5 全自动自愈    端到端无人干预

行业现状（2025）:
  - 中小团队: L1-L2
  - 头部互联网: L3-L4
  - Google SRE: L4-L5（特定场景）
```

**经验**：**不要跳级**。L0→L5 必须经过 L1-L4，每一级稳定半年再上下一级。

## 三、典型自愈场景

### 3.1 K8s / 云原生场景

| 场景 | 触发 | 修复动作 | 风险 |
|:---|:---|:---|:---:|
| Pod CrashLoopBackOff | K8s Event | rollout restart 上一稳定版本 | 🟡 |
| HPA 触底无效 | CPU/Mem 持续高 | 强制扩容 + 告警 | 🟢 |
| 节点 NotReady | kubelet 失联 | cordon + drain | 🟡 |
| 节点磁盘满 | disk > 90% | 清理日志/镜像 | 🟢 |
| Pod OOMKilled 3 次 | event 触发 | 自动增加 limit | 🟡 |
| Ingress 5xx 突增 | Prom 告警 | rollback 上一版本 | 🟡 |
| ConfigMap 误更新 | webhook | 校验 + 回滚 | 🟡 |

### 3.2 中间件场景

| 场景 | 触发 | 修复动作 | 风险 |
|:---|:---|:---|:---:|
| MySQL 主从延迟 | repl_lag > N | 重启 slave 线程 / kill 长事务 | 🟡 |
| Redis Master 挂 | Sentinel 检测 | 自动 failover | 🟢 |
| Kafka 消费滞后 | lag > N | 扩容消费者 | 🟢 |
| ES 红色 | cluster.health | 关闭异常 shard | 🔴 |
| ZK 节点掉线 | health check | kubectl restart | 🟡 |

### 3.3 应用层场景

| 场景 | 触发 | 修复动作 | 风险 |
|:---|:---|:---|:---:|
| JVM Full GC 频繁 | gc.time | dump + 重启 | 🟡 |
| 内存泄漏 | mem 线性增长 | rolling restart | 🟡 |
| 死锁 | thread dump | kill -3 + restart | 🟡 |
| 连接池耗尽 | connection pool exhausted | restart | 🟡 |
| 限流降级 | QPS 异常 | 自动降级开关 | 🟡 |

### 3.4 推理 / GPU 场景

| 场景 | 触发 | 修复 |
|:---|:---|:---|
| GPU XID 错误 | dcgm | 隔离节点 + 通知 |
| 显存碎片 | gpu_mem_frag | 重启推理 worker |
| TPOT 突增 | metric | 扩容 + 流量切换 |
| 模型 OOM | OOM event | 降 batch size |
| KV Cache 满 | cache_pressure | 限流 + 扩容 |

## 四、自动化修复的架构

```
┌────── 告警 / 信号源 ────────────────────┐
│ Prometheus / Loki / K8s Event / Custom │
└────────────┬────────────────────────────┘
             ↓
┌────── 决策引擎 ─────────────────────────┐
│  规则匹配 / LLM 推荐 / 模型决策          │
└────────────┬────────────────────────────┘
             ↓
┌────── 风险评估 ─────────────────────────┐
│  风险等级 / 影响范围 / 业务窗口          │
└────────────┬────────────────────────────┘
             ↓
┌────── 审批层（按风险）──────────────────┐
│ 🟢 自动执行                              │
│ 🟡 ChatOps 一键确认                      │
│ 🔴 强制人工审批                          │
└────────────┬────────────────────────────┘
             ↓
┌────── 执行引擎 ─────────────────────────┐
│ kubectl / Ansible / Salt / Custom API   │
└────────────┬────────────────────────────┘
             ↓
┌────── 验证 + 回滚 ──────────────────────┐
│ 监控 60s 是否恢复，未恢复自动回滚         │
└────────────┬────────────────────────────┘
             ↓
┌────── 审计 + 通知 ──────────────────────┐
│ 操作日志 + Slack/微信 通知 + 报表        │
└─────────────────────────────────────────┘
```

## 五、决策引擎：四种实现

### 5.1 规则引擎（最稳）

```yaml
# 简单 YAML 规则
rules:
  - name: PodCrashLoopRecover
    when:
      alertname: PodCrashLoopBackOff
      times_within: 10m >= 3
    do:
      - action: kubectl_rollout_undo
        params:
          namespace: "{{ .labels.namespace }}"
          deployment: "{{ .labels.deployment }}"
      - action: wait
        params: {duration: 60s}
      - action: verify_health
    on_failure: notify_oncall
    risk: medium

  - name: NodeDiskFullCleanup
    when:
      alertname: NodeDiskFull
      severity: P2
    do:
      - action: ssh_run
        params:
          command: "docker system prune -af && journalctl --vacuum-size=1G"
      - action: verify_disk_usage
    risk: low
```

### 5.2 流程图引擎（Argo Workflows / Tekton）

```yaml
# Argo Workflow 修复 Pod 不健康
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: pod-recovery-
spec:
  entrypoint: main
  arguments:
    parameters: [{name: pod_name}, {name: namespace}]
  templates:
    - name: main
      steps:
        - - {name: diagnose, template: kubectl-describe}
        - - {name: collect-logs, template: kubectl-logs}
        - - {name: restart, template: rollout-restart}
        - - {name: verify, template: check-health}
        - - {name: rollback, template: rollback, when: "verify.status != 'Healthy'"}
```

### 5.3 LLM Agent 决策（新势力）

```python
# 让 LLM 看告警 + 上下文，输出"操作计划"
result = llm.chat([
    {"role": "system", "content": "你是 SRE Agent，根据告警推荐处置步骤..."},
    {"role": "user", "content": alert_context}
], tools=[kubectl_get, kubectl_describe, kubectl_logs, kubectl_restart])

# LLM 自主调用工具诊断，最后给出建议
# 建议执行命令需经过 风险评估 + 审批
```

**强制约束**：LLM 推荐 ≠ LLM 执行。**严格分离**。

### 5.4 RL 强化学习（实验阶段）

```
仅适合:
  - 有海量历史数据
  - 可定义清晰奖励函数
  - 容忍探索成本
  
案例:
  - 自动调参（K8s HPA 参数）
  - 自适应限流
  - 容量预测决策

中小团队: 不推荐，过早优化
```

## 六、风险评估（自动化的"刹车"）

### 6.1 风险等级分类

| 等级 | 标志 | 例子 |
|:---:|:---|:---|
| 🟢 **可逆 + 影响小** | 自动执行 | 清理临时文件、扩容 |
| 🟡 **可逆 + 中等影响** | ChatOps 确认 | rollout restart、failover |
| 🔴 **不可逆 / 高影响** | 强制人工 | delete pvc、drop table |
| ⛔ **永久禁止** | 永远不自动 | rm -rf、kubectl delete ns |

### 6.2 风险评估器

```python
def assess_risk(action, context):
    risk_score = 0
    
    # 影响范围
    if action.scope == "single-pod":   risk_score += 1
    elif action.scope == "service":    risk_score += 3
    elif action.scope == "cluster":    risk_score += 5
    
    # 可逆性
    if action.reversible:              risk_score += 0
    else:                              risk_score += 5
    
    # 业务时段
    if is_peak_time():                 risk_score += 2
    
    # 当前是否在变更窗口
    if is_change_window():             risk_score -= 1
    
    # 历史成功率
    history_success = get_success_rate(action.type)
    if history_success < 0.9:          risk_score += 2
    
    if risk_score <= 2:    return "auto"
    elif risk_score <= 5:  return "chatops"
    else:                  return "manual"
```

### 6.3 黑白名单

```yaml
# 严禁自动执行的命令
blacklist:
  - "kubectl delete namespace"
  - "kubectl delete pvc"
  - "DROP TABLE"
  - "DROP DATABASE"
  - "rm -rf /"
  - "force-delete"
  - "kill -9 1"

# 完全可自动的白名单
whitelist:
  - "kubectl rollout restart"
  - "kubectl scale --replicas=*"
  - "kubectl cordon"
  - "kubectl drain --ignore-daemonsets"
  - "docker system prune"
  - "journalctl --vacuum-size=*"
```

### 6.4 频次限制（防止失控循环）

```python
# 同一服务 1 小时内自愈次数限制
rate_limits = {
    "rollout_restart": {"per_service_per_hour": 2},
    "scale_up": {"per_service_per_hour": 3},
    "node_drain": {"per_cluster_per_hour": 1},
}

def check_rate_limit(action, target):
    count = count_recent(action, target, 3600)
    limit = rate_limits[action]["per_service_per_hour"]
    if count >= limit:
        raise CircuitOpen("自愈次数超限，转人工")
```

## 七、执行引擎

### 7.1 Kubernetes 操作

```python
from kubernetes import client, config

config.load_incluster_config()
apps_v1 = client.AppsV1Api()
core_v1 = client.CoreV1Api()

# rollout restart
def rollout_restart(name, namespace):
    body = {"spec": {"template": {"metadata": {"annotations": {
        "kubectl.kubernetes.io/restartedAt": datetime.utcnow().isoformat()
    }}}}}
    apps_v1.patch_namespaced_deployment(name, namespace, body)

# scale
def scale(name, namespace, replicas):
    body = {"spec": {"replicas": replicas}}
    apps_v1.patch_namespaced_deployment_scale(name, namespace, body)

# cordon + drain
def drain_node(node_name):
    # 1. cordon
    body = {"spec": {"unschedulable": True}}
    core_v1.patch_node(node_name, body)
    # 2. evict pods
    pods = core_v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node_name}")
    for pod in pods.items:
        eviction = client.V1Eviction(metadata=client.V1ObjectMeta(name=pod.metadata.name, namespace=pod.metadata.namespace))
        core_v1.create_namespaced_pod_eviction(pod.metadata.name, pod.metadata.namespace, eviction)
```

### 7.2 SSH / Ansible 执行

```python
import paramiko, ansible_runner

# 简单 SSH
def ssh_run(host, cmd, timeout=60):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, key_filename='/keys/ops')
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode(), stderr.read().decode()

# Ansible Runner（批量）
result = ansible_runner.run(
    private_data_dir='/tmp/ans',
    playbook='cleanup_disk.yml',
    inventory={'all': {'hosts': {'node-101': {}, 'node-102': {}}}},
    extravars={'min_free_gb': 50}
)
```

### 7.3 第三方平台集成

```python
# 蓝鲸作业平台 / 公司 IT 自动化平台
def run_blueking_job(job_id, params):
    r = requests.post(f"{BK_URL}/api/v3/job_instance", json={
        "bk_biz_id": 100,
        "job_id": job_id,
        "global_var_list": params
    })
    return r.json()

# Jenkins
def trigger_jenkins(job, params):
    requests.post(f"{JENKINS_URL}/job/{job}/buildWithParameters", params=params, auth=(USER, TOKEN))
```

## 八、验证 + 回滚（自愈的安全网）

### 8.1 多维验证

```python
def verify_recovery(target, timeout=300):
    """自愈后必须验证"""
    start = time.time()
    while time.time() - start < timeout:
        # 1. K8s 状态
        if not check_k8s_healthy(target):
            time.sleep(10); continue
        
        # 2. 业务指标恢复
        error_rate = query_prom(f'rate(http_5xx{{service="{target}"}}[1m])')
        if error_rate > 0.01:
            time.sleep(10); continue
        
        # 3. 业务 SLO 不再 burn
        if is_slo_burning(target):
            time.sleep(10); continue
        
        # 4. 自定义健康检查
        if not custom_health_check(target):
            time.sleep(10); continue
        
        return True
    return False
```

### 8.2 自动回滚

```python
def safe_execute(action, target):
    snapshot = take_snapshot(target)   # 保存当前状态
    try:
        action.execute()
        if not verify_recovery(target):
            rollback(snapshot)
            notify("自愈失败，已回滚", target)
            return "rolled_back"
        return "success"
    except Exception as e:
        rollback(snapshot)
        notify(f"自愈异常 {e}，已回滚", target)
        raise
```

### 8.3 金丝雀自愈（Canary）

```
影响范围 > 1 节点时:
  1. 先在 1 个节点试
  2. 等 5 分钟观察
  3. 没问题再批量推

对应工具:
  - Argo Rollouts
  - Flagger
  - 自研发布编排
```

## 九、审计与可观测

### 9.1 必须记录的字段

```python
audit_log = {
    "timestamp": "...",
    "trigger": "alert/manual/scheduled",
    "alert_id": "...",
    "rule_id": "...",
    "action": "rollout_restart",
    "target": {...},
    "executor": "service-account-x",
    "approver": "system/zhangsan",
    "risk_assessment": "medium",
    "pre_state": {...},
    "post_state": {...},
    "verification": "passed/failed",
    "duration_sec": 45,
    "rollback": false,
    "outcome": "recovered"
}
```

### 9.2 看板指标

```
自愈次数趋势
自愈成功率
TOP 自愈场景
回滚率
人工干预率
平均自愈时长 (MTTR-A)
按风险等级分布
按业务/团队分布
```

### 9.3 周期性 Review

```
每周:
  - 检查回滚率 > 5% 的规则
  - 检查频次超限的规则
  
每月:
  - 评估新增自愈场景
  - 评估升降级（L2 → L3 / L3 → L4）
  
每季:
  - 自愈策略整体复盘
  - 黑白名单更新
```

## 十、开源工具

### 10.1 流程编排

| 工具 | 特点 |
|:---|:---|
| **Argo Workflows** | K8s 原生，DAG 编排 |
| **Tekton** | K8s 原生，CI/CD |
| **Apache Airflow** | DAG 通用 |
| **Temporal** | 持久化工作流 |
| **n8n** | 低代码 |
| **Activepieces** | 开源 Zapier |

### 10.2 K8s 自愈框架

| 工具 | 用途 |
|:---|:---|
| **Robusta** | K8s 告警 + 自愈 + 通知 |
| **KubeAuto** | K8s 自愈引擎 |
| **k8s-event-watcher** | 事件触发动作 |
| **Kured** | 节点自动重启 |
| **Descheduler** | 自动重新调度 |
| **GoldPinger** | 健康检查 + 自愈 |

### 10.3 配置/运维自动化

| 工具 | 类型 |
|:---|:---|
| **Ansible** | Agentless 配置 |
| **SaltStack** | 大规模 |
| **Puppet / Chef** | 老牌 |
| **Pulumi / Terraform** | IaC |
| **Crossplane** | K8s 控制平面 |

### 10.4 LLM Agent / 智能体

| 工具 | 用途 |
|:---|:---|
| **HolmesGPT** | K8s LLM 根因分析（开源） |
| **K8sGPT** | K8s 诊断 LLM |
| **Dify Agent** | LLMOps |
| **LangChain Agents** | 通用 |
| **AutoGen / CrewAI** | 多 Agent |

## 十一、典型实战：Pod 自愈流水线

```python
# robusta-action 示例
from robusta.api import *

@action
def crashloop_recover(event: PodEvent, config: GenParams):
    pod = event.get_pod()
    
    # 1. 收集证据
    logs = pod.get_logs(tail=200)
    events = pod.get_events()
    
    # 2. 风险评估
    if pod.metadata.namespace in ["kube-system", "production-core"]:
        send_alert("生产核心命名空间不自动处理", logs)
        return
    
    # 3. 频次检查
    if recent_restart_count(pod, hours=1) >= 2:
        send_alert("已多次自愈，转人工", pod)
        return
    
    # 4. 执行
    if pod.status.containerStatuses[0].restartCount >= 3:
        # 回滚到上一稳定版本
        deployment = pod.get_owner()
        deployment.rollout_undo()
        
        # 5. 验证
        if not wait_for_healthy(deployment, timeout=180):
            deployment.rollout_undo()  # 二次回滚
            send_alert("自愈失败，已二次回滚", deployment)
        else:
            send_info("自愈成功", deployment)
    
    # 6. 审计
    audit_log("crashloop_recover", pod, "success")
```

## 十二、典型实战：节点磁盘满清理

```yaml
# Ansible playbook 自动执行
- name: Clean node disk
  hosts: "{{ target_host }}"
  become: true
  tasks:
    - name: Check current disk usage
      shell: "df / | tail -1 | awk '{print $5}' | tr -d '%'"
      register: disk_before
    
    - name: Stop low-priority workload
      shell: "systemctl stop low-priority.service"
      ignore_errors: yes
    
    - name: Clean docker
      shell: "docker system prune -af --volumes"
    
    - name: Clean journal
      shell: "journalctl --vacuum-size=1G"
    
    - name: Clean apt cache
      shell: "apt-get clean"
    
    - name: Truncate /tmp old files
      shell: "find /tmp -type f -atime +7 -delete"
    
    - name: Verify
      shell: "df / | tail -1 | awk '{print $5}' | tr -d '%'"
      register: disk_after
    
    - name: Notify
      uri:
        url: "{{ webhook }}"
        method: POST
        body_format: json
        body: {"text": "{{ inventory_hostname }} disk: {{ disk_before.stdout }}% → {{ disk_after.stdout }}%"}
```

## 十三、常见坑（生产血泪）

| 坑 | 建议 |
|:---|:---|
| **自愈循环** | 频次限制 + 熔断 |
| **风险评估缺失** | 必上风险等级 + 黑白名单 |
| **没有验证就完事** | 必须 verify_recovery |
| **没有回滚** | 失败必回滚 |
| **审计不全** | 输入/输出/状态都记录 |
| **直接执行 LLM 建议** | LLM 推荐 ≠ 执行 |
| **静默执行** | 必通知 + ChatOps |
| **没有"叫停"按钮** | 一键暂停所有自动化 |
| **跨集群盲操作** | 集群隔离 + 单集群确认 |
| **凌晨自动改配置** | 变更窗口 + 业务时段限制 |
| **删除类操作上自动** | 永远人工 |
| **DB 自愈** | 数据库类操作慎用自动 |
| **测试不充分** | 必先在 staging / 演练验证 |
| **权限过大** | 最小权限 + 审计 |
| **依赖单点** | 自愈系统本身要高可用 |

## 十四、最佳实践清单（Checklist）

```
设计:
☐ 明确自动化等级（L0-L5）
☐ 风险评估有清晰规则
☐ 黑白名单完整
☐ 频次限制 + 熔断

执行:
☐ 严格审批（按风险）
☐ Pre/Post 快照
☐ 多维验证
☐ 自动回滚
☐ 金丝雀模式

可观测:
☐ 全量审计日志
☐ 自愈看板
☐ 周期 Review
☐ 异常告警（自愈失败/超限）

安全:
☐ 最小权限 (RBAC)
☐ 操作脱敏审计
☐ 一键 Kill Switch
☐ 跨集群隔离

人机协作:
☐ ChatOps 确认通道
☐ 失败必通知
☐ 成功也通知（可静默）
☐ 持续闭环改进
```

## 十五、学习路径

```
入门（1 周）:
  1. 写第一个 K8s 自愈脚本（rollout restart）
  2. Robusta 或 Argo 跑通
  3. 接入告警 → 触发自愈

中级（1 个月）:
  4. 风险评估 + 黑白名单
  5. 验证 + 回滚机制
  6. ChatOps 一键确认
  7. 审计 + 看板

高级（3 个月）:
  8. LLM Agent 推荐自愈
  9. 多场景规则库
  10. 自愈成功率优化
  11. 演练 + 故障注入

专家:
  12. RL / 自适应决策
  13. 自愈平台化
  14. 跨团队自愈生态
```

## 十六、参考资料

```
书:
  - 《Site Reliability Engineering》(Google)
  - 《Chaos Engineering》(O'Reilly)
  - 《Building Secure & Reliable Systems》(Google)

博客:
  - Netflix Chaos Engineering
  - Uber SRE Blog
  - 字节跳动稳定性建设
  - 阿里 SRE 实践

开源:
  - Robusta: https://github.com/robusta-dev/robusta
  - HolmesGPT: https://github.com/robusta-dev/holmesgpt
  - K8sGPT: https://github.com/k8sgpt-ai/k8sgpt
  - Argo Workflows: https://argoproj.github.io/
  - Ansible: https://ansible.com/

混沌工程:
  - ChaosMesh
  - LitmusChaos
  - Chaos Monkey
  - Gremlin
```

> 📖 **核心判断**：自动化修复是 **AIOps 的"高压电"**——做对了能省大量人力，做错了可能毁掉整个生产环境。**先标准化 → 脚本化 → 半自动 → 全自动**，每一步都要稳定半年。**风险评估 + 黑白名单 + 频次熔断 + 自动回滚** 是四大安全网，**LLM 推荐 ≠ LLM 执行** 是底线。中小团队建议从 **K8s Pod 自愈 + 磁盘清理 + Pod 扩容** 三个低风险场景起步，做稳一年再扩展。
