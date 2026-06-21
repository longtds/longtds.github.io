# 软件供应链安全

## SBOM

SBOM（Software Bill of Materials）是软件的物料清单，记录所有依赖组件。

```bash
# Syft 生成 SBOM
syft nginx:alpine -o cyclonedx-json > sbom.json

# Grype 漏洞扫描
grype nginx:alpine
```

## SLSA 框架

SLSA（Supply-chain Levels for Software Artifacts）是供应链安全等级框架。

| Level | 要求 | 说明 |
|:---:|:---|:---|
| L1 | 有构建过程 | 源码到制品可追溯 |
| L2 | 构建环境受控 | 构建过程有防篡改 |
| L3 | 构建完整性 | 所有依赖可验证 |
| L4 | 可复现构建 | 每次构建结果一致 |

## 依赖扫描

```bash
# npm
npm audit

# Python
pip-audit

# Go
govulncheck ./...
```
