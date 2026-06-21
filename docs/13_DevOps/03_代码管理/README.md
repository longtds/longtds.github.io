# 代码管理

## Git 工作流

| 工作流 | 特点 | 适用场景 |
|:---|:---|:---|
| Trunk-based | 频繁合并到 main | CI/CD 成熟团队 |
| GitHub Flow | feature branch → PR → main | 通用 |
| GitFlow | develop/release/hotfix 多分支 | 版本发布型产品 |

## 代码审查规范

- 所有代码变更必须通过 MR/PR
- 至少 1 人 Review 通过才能合并
- Review 关注：逻辑正确性 / 安全性 / 性能 / 可维护性
- CI 流水线必须全部通过
