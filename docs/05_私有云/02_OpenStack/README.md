# OpenStack

## 架构

OpenStack 由多个核心组件组成，通过消息队列和数据库协同工作。

## 核心组件

| 组件 | 功能 | 项目名 |
|:---|:---|:---|
| Keystone | 认证与授权 | 身份服务 |
| Nova | 计算资源管理 | 计算服务 |
| Neutron | 网络资源管理 | 网络服务 |
| Cinder | 块存储管理 | 存储服务 |
| Glance | 镜像管理 | 镜像服务 |
| Swift | 对象存储 | 对象存储 |
| Horizon | Web 管理面板 | 仪表盘 |

## 部署工具

- DevStack：开发测试环境
- Kolla-Ansible：容器化部署（推荐）
- TripleO：基于裸机的部署
- OpenStack-Helm：K8s 上部署
