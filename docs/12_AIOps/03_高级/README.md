# 高级

> AIOps 高级 = **AIOps 平台架构(数据湖+特征工程+模型平台) + 大规模异常检测(深度学习+多维度) + 因果推理(Causal Inference)+智能根因 + 故障预测+预防式运维 + ChatOps + LLM Agent 运维 + LangGraph Agent 编排 + MCP 工具协议 + 自动化执行(Ansible/Argo+RBAC) + AIOps + GitOps 融合 + 多云+多集群统一 + 国产化 + 模型生命周期(MLOps for AIOps) + 红蓝对抗演练 + 系统级故障注入(Chaos Mesh)+ 自动学习闭环**。本章面向 AIOps 平台架构师 / SRE 平台负责人。

## 一、AIOps 平台架构

```
数据采集层:
  Metrics: Prometheus + VM + OpenTelemetry
  Logs: Vector + Kafka → ClickHouse / Loki
  Traces: OTel Collector → Tempo
  Events: K8s Events / 业务事件
  Topology: Coroot / Pixie eBPF
  Profile: Pyroscope

数据湖 / 仓:
  ClickHouse (日志 / 事件)
  Iceberg / Paimon (训练数据)
  VictoriaMetrics (Metrics)
  pgvector / Milvus (RAG 知识)

特征工程:
  Feast (特征注册 + 在线 / 离线)
  自研 (业务特征)

模型平台:
  MLflow (实验 + 模型注册)
  KServe (推理服务)
  Argo Workflow (训练 pipeline)
  
AIOps 服务:
  - 异常检测服务 (实时)
  - RCA 服务 (LLM + RAG)
  - 预测服务 (容量 + 故障)
  - 告警关联服务
  - LLM Agent (运维助手)
  
执行层:
  Ansible AWX
  Argo Workflows (复杂)
  Kubernetes Operator (业务)
  自研 API + RBAC

人机界面:
  Grafana / 夜莺 / Kibana
  ChatOps (钉钉 / 飞书 / Slack Bot)
  自研运维门户
```

## 二、大规模异常检测

### 2.1 多维度异常

```
单指标 (单一时序):
  Prophet / LSTM / ARIMA
  适用: 业务 KPI / 系统资源

多指标 (相关时序):
  VAR / Multivariate Anomaly
  Microsoft Anomaly Detector (多变量)
  适用: 服务依赖 / 联动指标

时序 + 拓扑:
  GNN (Graph Neural Network)
  适用: 微服务 / 网络

高维 (1000+ 指标):
  Autoencoder
  Isolation Forest
  适用: 监控大盘整体

LLM-based:
  TimeMachine (序列输入 LLM)
  KAN-TimeSeries
  实验性, 2025-2026 起势头
```

### 2.2 工业级实现

```
DeepFlow ⭐ (国产, eBPF + AIOps)
观测云 Guance + AI
阿里 MetisFI (异常检测)
腾讯 Hawkeye / 织云
华为 SRE OS
百度 BAIOps
滴滴 IOPS Star (开源)
京东 Plug-Alpha (开源)

参考论文:
  USAD (Autoencoder + Adversarial)
  AnomalyTransformer
  TranAD
  PatchTST
```

### 2.3 训练 Pipeline

```python
# 训练异常检测模型 (Argo Workflow)
from darts.models import RNNModel
from darts import TimeSeries
import mlflow

mlflow.set_tracking_uri("http://mlflow:5000")
mlflow.set_experiment("anomaly-detection")

with mlflow.start_run():
    df = load_metrics(service="api", days=90)
    series = TimeSeries.from_dataframe(df)
    train, val = series.split_before(0.8)
    
    model = RNNModel(model='LSTM', input_chunk_length=72, output_chunk_length=12, ...)
    model.fit(train, val_series=val)
    
    # 评测
    mae = mae_metric(val, model.predict(len(val)))
    mlflow.log_metric("mae", mae)
    mlflow.pytorch.log_model(model.model, "model")
```

## 三、因果推理 + 智能根因

```
因果发现:
  - PC / FCI 算法 (constraint-based)
  - LiNGAM (LinearNonGaussian)
  - NOTEARS (continuous optimization)
  - 微软 CausalML

应用:
  - 拓扑自动发现 (服务依赖 = 因果)
  - 异常根因 (因果链上溯)
  - 治理 (干预效果评估)

工具:
  CausalNex (英国电信)
  DoWhy (微软) ⭐
  EconML (微软)

实战:
  Coroot 自动 RCA (基于拓扑 + 时序)
  阿里 GoldenEye (Granger 因果)
  自研 + LLM (融合)
```

## 四、故障预测

```
方法:
  - 异常预测 (时序前置)
  - 健康度评分 (多指标融合)
  - Survival Analysis (寿命预测)
  - LLM + 历史故障 (RAG)

场景:
  ☐ 磁盘故障 (SMART 数据 + ML, 准确 > 90%)
  ☐ GPU Xid 故障预测
  ☐ 服务雪崩前置预警 (QPS 飙升 + 延迟攀升)
  ☐ K8s Node 故障预测

工具:
  - PyOD / Darts
  - SMART Analytics (磁盘)
  - GPU DCGM Health Check (Nvidia)
  - 自研 + 历史 incidents
```

## 五、ChatOps + LLM Agent 运维

```python
# LangGraph 运维 Agent
from langgraph.graph import StateGraph, END
from langchain.chat_models import ChatOpenAI
from langchain.tools import tool

llm = ChatOpenAI(base_url="http://vllm:8000/v1", model="qwen-72b")

@tool
def query_prometheus(query: str) -> str:
    """查询 Prometheus PromQL"""
    return prom.custom_query(query)

@tool
def get_pod_logs(namespace: str, pod: str) -> str:
    """获取 Pod 日志"""
    return subprocess.check_output(["kubectl", "logs", "-n", namespace, pod])

@tool
def restart_deployment(namespace: str, deployment: str) -> str:
    """重启 Deployment (需审批)"""
    if approved:
        subprocess.run(["kubectl", "rollout", "restart", "-n", namespace, "deploy/" + deployment])
        return "Restarted"
    return "Pending approval"

# 构建 Agent
agent_executor = create_react_agent(llm, [query_prometheus, get_pod_logs, restart_deployment])

# 调用
response = agent_executor.invoke({"messages": [("user", "api 服务 P99 延迟突然升高, 帮我分析")]})
```

```
能力:
  - 自然语言查询 (Prometheus / Loki / Tempo)
  - 自动 RCA (调用工具收集证据 + LLM 推理)
  - 自动化执行 (重启 / 扩容 / 配置 + RBAC)
  - 总结 + 知识库 (写入 Postmortem)
  - 多轮交互 (ChatOps)

工具:
  LangGraph ⭐ + MCP
  AutoGen / CrewAI
  阿里 PAI Agent
  豆包 / 元宝 + 工具调用
```

## 六、MCP 协议（运维工具标准化）

```
MCP (Model Context Protocol):
  - Anthropic 提出
  - 标准化工具 / 资源 / 提示
  - 类似 LSP

AIOps MCP Server:
  - Prometheus MCP Server (查询)
  - Loki MCP Server (日志)
  - K8s MCP Server (操作)
  - Grafana MCP Server (Dashboard)
  - Argo MCP Server (workflow)

实现 (Python):
from mcp.server import Server
from mcp.types import Tool

app = Server("prometheus-mcp")

@app.list_tools()
def list_tools():
    return [Tool(name="query", description="PromQL query", inputSchema={...})]

@app.call_tool()
def call_tool(name, arguments):
    if name == "query":
        return prom.custom_query(arguments["query"])

# Claude Code / 通义灵码 自动接 MCP Server
```

## 七、自动化执行 + RBAC

```
执行器:
  Ansible AWX (易用)
  Argo Workflows (云原生)
  自研 API + Operator
  Jenkins Pipeline

RBAC + 审批:
  - 风险分级 (read / write / destructive)
  - 自动 (read / 轻度 write)
  - 人工 (destructive / 生产)
  - 多人审批 (重要)

审计:
  - 所有操作记录
  - 输入 + 输出
  - 审批链
  - 责任人

工具:
  GitOps + ArgoCD (基础设施)
  Argo Workflow (任务)
  Backstage (审批 + 自服务)
  阿里 Cloud Shell (跳板)
  Teleport (审计 SSH)
```

## 八、Chaos + 红蓝对抗

```
Chaos 工程:
  Chaos Mesh ⭐ (国产 CNCF)
  Litmus (K8s)
  Gremlin (商业)

场景:
  - 节点宕机
  - Pod 杀
  - 网络分区 / 延迟 / 丢包
  - CPU / 内存 / 磁盘 占用
  - DNS / 时钟
  - K8s API down

AIOps + Chaos:
  - 故障注入触发 → AIOps 自动检测 + RCA
  - 验证告警覆盖率
  - 验证 SLO + Error Budget
  - 训练异常检测模型 (合成异常)

红蓝对抗:
  - 红队 (注故障) vs 蓝队 (响应)
  - 季度演练
  - Postmortem + 改进
```

## 九、AIOps + GitOps 融合

```
GitOps 配置 AIOps:
  - 告警规则 (Git managed)
  - SLO 定义 (Sloth YAML)
  - 异常检测模型 (MLflow registry)
  - LLM prompt 模板 (Git)

ArgoCD + GitLab:
  - Helm + Kustomize 部署 AIOps 服务
  - Recording Rules + Alerts as Code
  - Sloth SLO as Code
  - 自愈 webhook 配置 as Code
```

## 十、多云 + 多集群统一

```
痛点:
  - 多 K8s 集群 (生产 / 测试 / DR)
  - 多云 (阿里 + 腾讯 + 自建)
  - 多 region

方案:
  - 统一 VictoriaMetrics 多 vmselect 联邦
  - 统一 ClickHouse 集群 (跨地写)
  - 统一 Tempo + OTel 路由
  - 统一 Grafana (多数据源)
  - Karmada 跨集群部署 AIOps 服务
  - 自研 Federation (大厂)
```

## 十一、AIOps 国产化

```
硬件:        华为 Ascend 910B (LLM 推理 + Embedding)
平台:        夜莺 ⭐ / 观测云 Guance ⭐ / 阿里 ARMS / 华为 AOM
日志:        ClickHouse / Apache Doris / 阿里 SLS
LLM:        Qwen 2.5/3 / DeepSeek V3/R1 / GLM-4 / 文心
推理:        vLLM / MindIE / LMDeploy
向量:        Milvus / pgvector
告警:        飞书 / 钉钉 / 企业微信 Webhook
工具:        DeepFlow ⭐ + Hawkeye + GoldenEye
合规:        等保三级 + 国密 + 模型备案
信创:        鲲鹏 + openEuler + 国产 K8s
```

## 十二、模型生命周期（MLOps for AIOps）

```
异常检测模型 / RCA 模型:
  数据 → 训练 → 评测 → 部署 → 监控 → 再训练
  
Pipeline:
  1. 数据采集 (历史 metrics + 标注)
  2. 特征工程 (Feast)
  3. 训练 (Argo Workflow + MLflow)
  4. 评测 (业务集 + AUC / F1)
  5. 部署 (KServe + 灰度)
  6. 监控 (准确率 / 漂移)
  7. 反馈 (人工标注 / 自动)
  8. 再训练 (周 / 月)

挑战:
  - 标注成本 (异常稀疏)
  - 概念漂移 (业务变化)
  - 多服务定制
  - 自动学习闭环
```

## 十三、自动学习闭环

```
闭环:
  alert → 工程师标注 (是否真异常 / 根因) → 入库 → 再训练

工具:
  - Label Studio (标注)
  - MLflow (版本)
  - Feast (特征)
  - Argo Workflow (调度)
  - 自研反馈 API

价值:
  - 模型持续改进
  - 业务自适应
  - 减少误报
  - 推荐 SOP
```

## 十四、Checklist（高级）

```
平台:
☐ 数据湖 (ClickHouse + Iceberg)
☐ 特征工程 (Feast)
☐ 模型平台 (MLflow + Argo + KServe)

异常检测:
☐ 多模型 (Prophet + LSTM + Isolation Forest)
☐ 多维度 (单/多变量/拓扑/高维)
☐ 大规模部署 (KServe)
☐ 在线漂移检测

RCA:
☐ 因果推理 (DoWhy / Granger)
☐ Coroot 自动
☐ LLM + RAG 历史

故障预测:
☐ 磁盘 SMART + ML
☐ GPU Xid 预测
☐ 服务雪崩前置

ChatOps:
☐ LangGraph Agent
☐ MCP 工具协议
☐ 多轮交互
☐ 自动化执行 + RBAC

Chaos:
☐ Chaos Mesh + 季度演练
☐ 红蓝对抗
☐ Postmortem

GitOps:
☐ Alerts / SLO / Prompt as Code
☐ ArgoCD 同步

多云:
☐ VM / CH / Tempo 联邦
☐ Karmada AIOps 服务

国产化:
☐ Qwen / DeepSeek + Ascend
☐ 夜莺 / 观测云
☐ DeepFlow / Hawkeye
☐ 国密 + 等保

模型:
☐ MLflow 注册 + 版本
☐ Argo Workflow 训练
☐ KServe 部署
☐ 监控漂移

闭环:
☐ Label Studio 标注
☐ 反馈 API
☐ 自动再训练
☐ 准确率监控
```

## 十五、推荐栈（高级）

```
监控:        VictoriaMetrics + Grafana + Sloth
日志:        ClickHouse + Vector + Kafka + Grafana
链路:        Tempo + OTel + Coroot
eBPF:        Pixie + Coroot + Pyroscope + DeepFlow
告警:        Alertmanager + Karma + 飞书/钉钉
异常:        Prophet + Darts + Autoencoder + USAD
RCA:        Coroot + DoWhy + LLM (Qwen + RAG)
预测:        Prophet + Argo Workflow + MLflow
ChatOps:    LangGraph ⭐ + MCP + Qwen/DeepSeek
Chaos:       Chaos Mesh ⭐
执行:        Ansible AWX / Argo Workflow / 自研 API
特征:        Feast
存储:        ClickHouse / Iceberg / Milvus / pgvector
GitOps:      ArgoCD + Kustomize
合规:        国密 + 等保 + 备案
国产:        夜莺 + 观测云 + DeepFlow + Hawkeye
```

> 📖 **核心判断**：AIOps 高级 = **平台架构(数据湖+特征+模型) + 大规模异常检测(多维+深度学习) + 因果推理 RCA + 故障预测 + ChatOps + LangGraph Agent + MCP 协议 + 自动化执行 + Chaos 演练 + GitOps 融合 + 多云多集群 + 国产化 + MLOps 闭环**。能给企业画"VictoriaMetrics + ClickHouse + Tempo + Coroot + LLM Agent + LangGraph + MCP + Chaos Mesh + ArgoCD + Karmada + 国产化(Qwen/DeepFlow)"完整 AIOps 平台，并能落地"异常检测自动化 + LLM RCA + ChatOps 自愈 + 季度演练 + 模型闭环"，就具备 AIOps 平台架构师能力。
