# 自动化修复

## 自动修复模式

| 模式 | 场景 | 实现 |
|:---|:---|:---|
| 重启 | Pod OOM/无响应 | kubectl delete pod |
| 回滚 | 新版本异常 | kubectl rollout undo |
| 扩容 | 负载突增 | kubectl scale |
| 迁移 | 节点异常 | cordon + drain |
| 清理 | 磁盘满 | 清理日志/临时文件 |

## 已知故障模式库

```yaml
# patterns.yaml
patterns:
  - name: gpu-oom
    symptoms:
      - metric: nvidia_smi_memory_used
        condition: "> 95%"
      - log: "CUDA out of memory"
    action:
      type: restart_pod
      command: "kubectl delete pod {{.pod_name}} -n {{.namespace}}"
  
  - name: pod-crashloop
    symptoms:
      - metric: kube_pod_container_status_restarts_total
        condition: "increase > 5 in 5m"
    action:
      type: describe_and_notify
```
