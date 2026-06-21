# 网络安全基础

## 威胁模型

| 模型 | 说明 |
|:---|:---|
| STRIDE | Spoofing/Tampering/Repudiation/Info Disclosure/DoS/Elevation |
| DREAD | Damage/Reproducibility/Exploitability/Affected Users/Discoverability |

## 端口扫描

```bash
# 端口扫描（用户内网授权范围）
nmap -sS 10.0.0.0/24 -p 22,80,443,3306,6379
```

## IDS/IPS

- Snort：规则入侵检测
- Suricata：多线程高性能 IDS
- Zeek（Bro）：流量分析框架
