# 15. 渗透测试

> 渗透测试 = 授权红队的攻防工程。本章按 **基础 → 进阶 → 高级 → 最佳实践 → 发展与展望** 五层递进，聚焦 PTES + Kali 工具栈 + Web/AD/Cloud/K8s + Sliver/CS C2 + AI 红队 + HW 行动 + Bug Bounty + CTEM 14 大主线。

> ⚠️ **法律红线**: 渗透测试 **必须授权**。本章一切技术仅限授权范围 / CTF / 自有实验室。未授权渗透 = 网安法/刑法。

## 章节结构

| 章节 | 适合人群 | 核心内容 |
|:---|:---|:---|
| [01_基础](01_基础/README.md) | 入门 | 法律边界 + PTES + Kali 工具 + nmap/amass + Burp 入门 + Metasploit + Web 漏洞(SQLi/XSS/SSRF) + 密码破解 + 报告 + CTF + 20 题 |
| [02_进阶](02_进阶/README.md) | 中型授权渗透 | Web 进阶(认证/IDOR/反序列化/SSTI/XXE) + API + AD(BloodHound/Kerberoasting/Relay/PtH) + 内网横向(ligolo) + 提权(Linux/Win) + 免杀 + Sliver/CS + WAF Bypass + BBOT 自动化 |
| [03_高级](03_高级/README.md) | 红队/0day 研究 | APT 全链 + 红队基建 + EDR 对抗(syscall/BYOVD) + AD 深度(ADCS) + Cloud(AWS/Azure/GCP/阿里) + K8s 攻击 + DevOps 链 + 供应链 + AI/LLM 红队 + 0day 漏挖 + IoT/OT + 社工 |
| [04_最佳实践](04_最佳实践/README.md) | 红队负责人/渗透服务 | 12 金标 + 授权 SOW + ROE + 方法论 + 工具链 + Recon 资产 + 漏洞分级 + 报告标准 + SRC/Bug Bounty + 红蓝紫(Caldera) + HW 重保 + KPI + 团队 |
| [99_发展与展望](99_发展与展望.md) | 所有人 | AI 红队 + Agent 攻击 + LLM 辅助 + Cloud/K8s 主战 + 供应链 + AI vs EDR + HW + Bug Bounty + CTEM + OT/IoT/5G + PQC + 20 项 5 年信心矩阵 |

## 学习路径

```
入门（1-3 月）
  └─ 01_基础: 法律 + PTES + Kali + Burp + Metasploit + DVWA + 20 题

进阶（3-12 月）
  └─ 02_进阶: Web 深度 + AD + 内网 + 提权 + Sliver + BBOT + Bug Bounty

高级（1-2 年）
  └─ 03_高级: APT 全链 + EDR 对抗 + Cloud + K8s + 供应链 + AI 红队 + 0day

工程化（2-3 年）
  └─ 04_最佳实践: 授权 + ROE + 工具链 + 报告 + 红蓝紫 + HW 重保 + 团队

展望（持续）
  └─ 99_发展与展望: AI 红队 + Agent + Cloud/K8s + CTEM + 国密 + Sovereign
```

## 核心判断

```
心法:
  1. 法律先行: 授权 + 范围 + ROE 三件套
  2. PTES 七阶段, 系统化方法论
  3. ATT&CK 是攻防共同语言
  4. AI 红队(Garak/PyRIT) 是未来 5 年最大机遇
  5. Cloud + K8s 占红队 60%+, 必修
  6. AD 深度(BloodHound + Certipy + Impacket) 永远的核心
  7. 红队基建(Sliver/CS + Redirector + CDN) 是分水岭
  8. EDR 对抗(syscall + BYOVD + Sleep masking)
  9. 供应链(XZ/SolarWinds 模式) 是新方向
  10. HW + 关基 + 国密 + 信创 是央企硬需求
  11. CTEM + Continuous 替代年度渗透
  12. 报告写作 + Postmortem 决定专业度

红线:
  ❌ 未授权渗透 (违法)
  ❌ 超范围 (合同外)
  ❌ 破坏生产 (无升级)
  ❌ 客户数据外泄 (法律)
  ❌ 0day 不上报 (黑产)
  ❌ 持久化无清理 (违 ROE)
  ❌ 只用工具不懂原理
  ❌ 不学 AI + Cloud (5 年淘汰)
  ❌ 国密 + HW + 关基 不熟 (央企无用)
  ❌ 报告糊弄 (没价值)
```

## 相关章节

- 配合 [07_Kubernetes](../07_Kubernetes/index.md) 看 K8s 攻击 + RBAC + Pod 逃逸
- 配合 [11_AI基础设施](../11_AI基础设施/index.md) 看 LLM Guardrails + Confidential
- 配合 [13_认证与SSO](../13_认证与SSO/index.md) 看 钓鱼 + Token 窃取 + AD
- 配合 [14_安全](../14_安全/index.md) 看 SOC + EDR + SIEM + 等保 + 国密
- 配合 [16_故障排查](../16_故障排查/index.md) 看 IR + 取证 + Postmortem
