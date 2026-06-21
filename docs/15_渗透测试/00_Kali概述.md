# Kali Linux 概述

Kali Linux 是专业的渗透测试发行版，内置 600+ 安全工具。

## 安装

```bash
# 下载 ISO
wget https://cdimage.kali.org/kali-2026.1/kali-linux-2026.1-installer-netinst-amd64.iso

# Docker 方式（便捷）
docker run --rm -it kalilinux/kali-rolling bash

# WSL 方式（Windows）
wsl --install -d kali-linux
```

## 工具分类

| 类别 | 工具 |
|:---|:---|
| 信息收集 | Nmap/Masscan/WhatWeb/GoBuster |
| 漏洞扫描 | Nessus/OpenVAS/SQLMap/Nuclei |
| Web 攻击 | Burp Suite/SQLMap/XSStrike |
| 密码攻击 | Hydra/John/Hashcat |
| 无线攻击 | Aircrack-ng/Reaver |
| 后渗透 | Metasploit/Empire/CobaltStrike |

## 伦理边界

- 仅对授权的系统和网络进行测试
- 测试前签署书面授权文件
- 测试过程完整记录，不擅自扩散漏洞信息
- 发现漏洞后及时通知修复
