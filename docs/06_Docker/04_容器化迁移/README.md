# 容器化迁移

## 迁移 Checklist

- [ ] 应用支持 12-Factor（配置外置/无状态/日志 stdout）
- [ ] 配置分离（环境变量/ConfigMap）
- [ ] 日志输出到 stdout/stderr
- [ ] 健康检查接口（/healthz）
- [ ] 优雅关闭（SIGTERM 处理）
- [ ] 持久化数据分离（PV/PVC）
- [ ] 构建 Dockerfile（多阶段构建）
- [ ] .dockerignore 优化构建上下文
- [ ] 镜像瘦身（Alpine 基础镜像）

## 常见注意事项

| 场景 | 问题 | 方案 |
|:---|:---|:---|
| 配置文件 | 镜像内硬编码 | 环境变量注入 |
| 日志 | 写入文件 | stdout |
| 定时任务 | crontab 丢失 | K8s CronJob |
| Session | 本地存储 | Redis 外部化 |
| 文件上传 | 本地磁盘 | 对象存储/MinIO |
| 网络 | IP 硬编码 | 服务发现/DNS |
