<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T05:59:59+08:00
source: AWS Containers Blog
domain: 技术动态
url: https://aws.amazon.com/blogs/containers/announcing-zone-aware-routing-in-amazon-ecs-service-connect/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# Announcing zone-aware routing in Amazon ECS Service Connect |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 05:59 CST |
| 领域 | 技术动态 |
| 来源 | AWS Containers Blog |
| 原文标题 | Announcing zone-aware routing in Amazon ECS Service Connect \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/containers/announcing-zone-aware-routing-in-amazon-ecs-service-connect/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在这篇文章中，我们将解释区域感知路由的工作原理，并引导您设置多可用区 ECS 集群以查看其实际情况。

## 正文

### [Containers](https://aws.amazon.com/blogs/containers/)

## 在 

Amazon ECS Service Connect 中宣布区域感知路由

在微服务架构中，流量模式和服务放置决策直接影响成本和性能。借助 Amazon ECS Service Connect 的区域感知路由，Amazon Elastic Container Service (Amazon ECS) 现在优先考虑对与客户端位于同一可用区中的健康终端节点的请求。这有助于降低跨区域数据传输成本并最大限度地减少延迟，而不会影响可用性。

2022 年，[ECS 推出了 Amazon ECS Service Connect](https://aws.amazon.com/blogs/aws/new-amazon-ecs-service-connect-enabling-easy-communication-between-microservices/)，这是一种托管服务网格，可简化构建弹性分布式应用程序。 Service Connect 允许您使用 AWS Cloud Map 命名空间按逻辑名称引用服务，并在 ECS 任务之间自动分配流量，而无需部署负载均衡器。每个任务都运行一个 Envoy sidecar 代理，该代理处理服务发现、负载平衡以及现在的区域感知路由。服务使用客户端别名进行通信，客户端别名是抽象底层网络详细信息的逻辑名称。

Service Connect 支持两种服务类型：

- 客户端-服务器服务既可以发起也可以接收连接，在某些交互中充当客户端，在另一些交互中充当服务器。
- 仅客户端服务只能发起到其他服务的出站连接。

Amazon ECS Service Connect 默认为新服务和现有服务启用区域感知路由，您无需进行任何基础设施或应用程序代码更改。现有服务（客户端和服务器服务）需要您执行一次性重新部署才能激活新的路由行为。在这篇文章中，我们将解释区域感知路由的工作原理，并引导您设置多可用区 ECS 集群以查看其实际情况。

![显示 Amazon ECS Service Connect 中的区域感知路由的架构图，其中客户端任务路由到跨多可用区集群的同一可用区中的后端终端节点](https://d2908q01vomqb2.cloudfront.net/fe2ef495a1152561572949784c16bf23abb28057/2026/06/30/CONTAINERS-231-1.png)

Amazon ECS Service Connect 中的区域感知路由

### 它是如何工作的ECS Service Connect routes most traffic to endpoints in the same AZ, reducing cross-AZ network calls. The algorithm uses Envoy’s zone-aware routing feature to:

- 发现端点 – 代理维护目标服务中所有端点的最新视图，包括它们的可用区位置。
- 优先考虑本地可用区 – 路由请求时，代理会优先将流量发送到与发起请求的客户端任务位于同一可用区中的端点。
- 基于剩余容量的路由 – 该算法不是计算本地权重，而是比较每个可用区中源集群和目标集群之间的端点分布百分比。当目标 AZ 的端点数量按比例多于源时，剩余容量（“剩余”）会吸收来自过载 AZ 的跨区域流量，因此不会有任何单个区域被压垮。
- 优雅地回退 – 如果本地可用区中没有足够的健康端点，流量会根据剩余容量自动溢出到其他可用区中的健康端点，因此可用性不会受到影响。
- 动态重新平衡 – 随着端点扩大或缩小，路由决策会实时更新，无需重新部署。

### 区域感知路由的优点

- 降低数据传输成本

- 跨可用区数据传输[产生额外费用](https://docs.aws.amazon.com/cur/latest/userguide/cur-data-transfers-charges.html)。
- 通过优先考虑同一可用区内超过 80% 的流量[当端点在可用区之间平衡时](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-rebalancing.html)，区域感知路由可以显着减少跨可用区网络调用量。 This leads to direct cost savings, especially for data-intensive workloads.
- 更低的延迟

- 每次AZ遍历都会增加网络延迟。
- 通过将流量保持在可用区本地，区域感知路由可以在端点平衡时将多可用区部署中的网络延迟中值降低大约 24%。 Intra-AZ communication latency can be as low as 300 to 400 μs, compared to 1.5 ms or more for cross-AZ calls.
- No application code changes

- Envoy sidecar 代理处理区域感知路由。您无需更改应用程序代码。
- 使用 ECS Service Connect 时，默认处于开启状态，无需额外配置。
- Preserved high availability- 如果本地端点不健康或不足，流量会自动溢出到其他可用区中的健康端点。

### 区域感知路由入门

以下演练在 EC2 实例上设置多可用区 Amazon ECS 集群，使用 Service Connect 部署前端和后端服务，并验证区域感知路由是否将流量保留在每个可用区域内。

#### 先决条件

- AWS 命令行界面 (AWS CLI) v2 [已安装并配置](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)。
- IAM 角色：[ecsInstanceRole](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/instance_IAM_role.html) 和 [ecsTaskExecutionRole](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)。
- 子网位于至少 3 个可用区的 [VPC](https://docs.aws.amazon.com/vpc/latest/userguide/create-vpc.html)（默认 VPC 有效）。

#### 第 1 步：设置环境变量

定义整个演练中使用的环境变量。这些标识跨默认 VPC 中 3 个可用区的子网：```
export REGION="us-east-1" #根据需要更新区域 - 本演练使用 us-east-1 export CLUSTER_NAME="az-aware-cluster-ec2" export LB_NAME="az-aware-routing-ec2-lb" export NAMESPACE_NAME="az-aware-routing-ec2-ns" export ASG_NAME="az-aware-ec2-asg" 导出TASK_COUNT="${TASK_COUNT:-6}" export ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)" # 获取默认 VPC ID VPC_ID=$(aws ec2 --region $REGION describe-vpcs \ --filters "Name=isDefault,Values=true" \ --query "Vpcs[0].VpcId" --output text) # 从 3 个不同的子网获取子网可用区 SUBNETS=$(aws ec2 --region $REGION 描述子网 \ --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=true" \ --query "Subnets | sort_by(@, &AvailabilityZone) | [].[SubnetId, AvailabilityZone]" \ --output text) SUBNET_1=$(echo "$SUBNETS" | awk 'NR==1 {print $1}') AZ_1=$(echo "$SUBNETS" | awk 'NR==1 {print $2}') SUBNET_2=$(echo "$SUBNETS" | awk -v az="$AZ_1" '$2 != az {print $1; exit}') AZ_2=$(echo "$SUBNETS" | awk -v az="$AZ_1" '$2 != az {print $2; exit}') SUBNET_3=$(echo "$SUBNETS" | awk -v az1="$AZ_1" -v az2="$AZ_2" '$2 != az1 && $2 != az2 {print $1; exit}') AZ_3=$(echo "$SUBNETS" | awk -v az1="$AZ_1" -v az2="$AZ_2" '$2 != az1 && $2 != az2 {print $2; exit}') echo "VPC ID: $VPC_ID" echo "子网 1: $SUBNET_1 (AZ: $AZ_1)" echo "子网 2: $SUBNET_2 (AZ: $AZ_2)" echo "子网 3: $SUBNET_3 (AZ: $AZ_3)"
```#### Step 2: Create security groups

为负载均衡器、前端（客户端）和后端（服务器）创建安全组。配置入口规则以允许从 ALB 到前端端口 8080 以及从前端到后端端口 8090 的流量。```
# LB security group LB_SG=$(aws ec2 --region $REGION create-security-group \ --group-name az-aware-routing-lb-sg \ --description "Security group for az aware routing LB" \ --vpc-id $VPC_ID \ --query "GroupId" --output text) # Client (frontend) security group CLIENT_SG=$(aws ec2 --region $REGION create-security-group \ --group-name az-aware-routing-client-sg \ --description "Security group for az aware routing client" \ --vpc-id $VPC_ID \ --query "GroupId" --output text) # Server (backend) security group SERVER_SG=$(aws ec2 --region $REGION create-security-group \ --group-name az-aware-routing-server-sg \ --description "Security group for az aware routing server" \ --vpc-id $VPC_ID \ --query "GroupId" --output text) # Ingress rules aws ec2 --region $REGION authorize-security-group-ingress \ --group-id $LB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0 aws ec2 --region $REGION authorize-security-group-ingress \ --group-id $CLIENT_SG --protocol tcp --port 8080 --source-group $LB_SG aws ec2 --region $REGION authorize-security-group-ingress \ --group-id $SERVER_SG --protocol tcp --port 8090 --source-group $CLIENT_SG
```

#### 步骤 3：创建具有 Service Connect 命名空间的 ECS 集群

创建具有 Service Connect 默认命名空间的 ECS 集群。此命名空间允许服务通过逻辑名称相互发现：

```
aws ecs --region $REGION create-cluster \ --cluster-name $CLUSTER_NAME \ --service-connect-defaults '{ "namespace": "az-aware-routing-ec2-ns" }'
```#### 步骤 4：创建启动模板和 Auto Scaling 组

使用 ECS 优化的 AMI 创建启动模板。实例通过“UserData”自动注册到集群。然后创建一个跨越所有 3 个可用区的 Auto Scaling 组，该组具有足够的容量来完成您的任务（至少是要激活区域感知路由的可用区数量的 2 倍）：```
# 获取 ECS 优化的 AMI AMI_ID=$(aws ssm get-parameter \ --region $REGION \ --name /aws/service/ecs/optimized-ami/amazon-linux-2/recommended \ --query 'Parameter.Value' --output text | jq -r '.image_id') # 创建用户数据脚本 USER_DATA=$(cat <<'EOF' #!/bin/bash set -e echo ECS_CLUSTER=az-aware-cluster-ec2 >> /etc/ecs/ecs.config echo AWS_DEFAULT_REGION=us-east-1 >> /etc/ecs/ecs.config EOF ) # 创建启动模板 LT_ID=$(aws ec2 --region $REGION create-launch-template \ --launch-template-name az-aware-ec2-launch-template \ --version-description "ECS 优化启动模板" \ --launch-template-data "{ \"ImageId\": \"$AMI_ID\", \"InstanceType\": \"t3.medium\", \"IamInstanceProfile\": { \"Arn\": \"arn:aws:iam::${ACCOUNT_ID}:instance-profile/ecsInstanceRole\" }, \"SecurityGroupIds\": [\"$CLIENT_SG\", \"$SERVER_SG\"], \"MetadataOptions\": { \"HttpEndpoint\": \"enabled\", \"HttpTokens\": \"required\", \"HttpPutResponseHopLimit\": 2 }, \"UserData\": \"$(echo "$USER_DATA" | base64 | tr -d '\n')\", \"TagSpecifications\": [{ \"ResourceType\": \"instance\", \"Tags\": [{ \"Key\": \"Name\", \"Value\": \"az-aware-ecs-instance\" }] }] }" \ --query 'LaunchTemplate.LaunchTemplateId' \ --output text) # 创建 ASG --- 所需容量 = TASK_COUNT * 2 （每个任务一个实例） aws autoscaling --region $REGION create-auto-scaling-group \ --auto-scaling-group-name $ASG_NAME \ --launch-template "LaunchTemplateId=$LT_ID" \ --min-size 1 \ --max-size 30 \ --desired-capacity $((TASK_COUNT * 2)) \ --vpc-zone-identifier "$SUBNET_1,$SUBNET_2,$SUBNET_3" \ --health-check-type EC2 \ --health-check-grace-period 300 \ --tags "Key=Name,Value=az-aware-ecs-instance,PropagateAtLaunch=true"
```注意：“desired-capacity”=“TASK_COUNT”*2 = 12，因为本演练中使用的每个“t3.medium”适合一项任务（1024 CPU / 2048 MB），并且您运行 6 个后端任务和 6 个前端任务。

#### Step 5: Create a load balancer

创建应用程序负载均衡器 (ALB) 以将外部流量路由到前端服务：```
# Create ALB ALB_ARN=$(aws elbv2 --region $REGION create-load-balancer \ --name $LB_NAME \ --subnets $SUBNET_1 $SUBNET_2 $SUBNET_3 \ --security-groups $LB_SG \ --query "LoadBalancers[0].LoadBalancerArn" --output text) # Create target group TG_ARN=$(aws elbv2 --region $REGION create-target-group \ --name $LB_NAME \ --protocol HTTP --port 80 \ --vpc-id $VPC_ID \ --target-type ip \ --health-check-path /ping \ --health-check-interval-seconds 10 \ --query "TargetGroups[0].TargetGroupArn" --output text) # Create listener aws elbv2 --region $REGION create-listener \ --load-balancer-arn $ALB_ARN \ --protocol HTTP --port 80 \ --default-actions Type=forward,TargetGroupArn=$TG_ARN
```#### 步骤 6：注册任务定义

Register task definitions for backend and frontend services. “portMappings”包括命名端口和“appProtocol”（Service Connect 所需），“command”字段将容器配置为作为 HTTP 服务器运行。```
# 后端任务定义 aws ecs register-task-definition \ --region $REGION \ --family az-aware-backend-service-ec2 \ --requires-compatibility EC2 \ --network-mode awsvpc \ --cpu 1024 \ --memory 2048 \ --execution-role-arn arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskExecutionRole \ --runtime-platform cpuArchitecture=X86_64,operatingSystemFamily=LINUX \ --container-definitions '[{ "name": "backend-app", "image": “public.ecr.aws/h5t0a8k7/serviceconnect/az-aware-routing-test:latest”，“cpu”：512，“内存”：1024，“portMappings”：[{“name”：“http”，“containerPort”：8090，“协议”：“tcp”，“appProtocol”：“http”}]，“essential”：true， "command": ["server","-port=8090","-protocol=http","-name=product","-routes=[]"], "logConfiguration": { "logDriver": "awslogs", "options": { "awslogs-group": "/ecs/az-aware-backend-service-ec2", "awslogs-region": "us-east-1", "awslogs-stream-prefix": "ecs", "awslogs-create-group": "true" } } } ]'
```前端配置了一个出口路由，通过 Service Connect 的 DNS 别名 (`sc.test.az.aware.backend:8090`) 将请求代理到后端服务。 This is triggered when the `azAwareRouting` header is present:```
# Frontend Task Definition aws ecs register-task-definition \ --region $REGION \ --family az-aware-fe-service-ec2 \ --requires-compatibilities EC2 \ --network-mode awsvpc \ --cpu 1024 \ --memory 2048 \ --execution-role-arn arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskExecutionRole \ --runtime-platform cpuArchitecture=X86_64,operatingSystemFamily=LINUX \ --container-definitions '[{ "name": "fe-app", "image": "public.ecr.aws/h5t0a8k7/serviceconnect/az-aware-routing-test:latest", "cpu": 512, "memory": 1024, "portMappings": [{ "name": "http", "containerPort": 8080, "protocol": "tcp", "appProtocol": "http" } ], "essential": true, "command": ["server","-port=8080","-protocol=http","-name=fe","-routes=[{\"match\":\"product\", \"destination\": \"http://sc.test.az.aware.backend:8090\",\"method\":\"Egress\"}]"], "logConfiguration": { "logDriver": "awslogs", "options": { "awslogs-group": "/ecs/az-aware-fe-service-ec2", "awslogs-region": "us-east-1", "awslogs-stream-prefix": "ecs", "awslogs-create-group": "true" } } } ]'
```#### 第 7 步：创建服务

在启用 Service Connect 的情况下部署这两项服务。关键配置是“serviceConnectConfiguration”块，它在命名空间中注册每个服务并使其可通过客户端别名发现：```
# 后端服务 aws ecs --region $REGION create-service \ --cluster $CLUSTER_NAME \ --service-name az-aware-backend-service-ec2 \ --task-definition az-aware-backend-service-ec2 \ --desired-count $TASK_COUNT \ --launch-type EC2 \ --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2,$SUBNET_3],securityGroups=[$SERVER_SG]}" \ --service-connect-configuration '{ "enabled": true, "logConfiguration": { "logDriver": "awslogs", "options": { "awslogs-group": "/ecs/az-aware-backend-service-ec2", "awslogs-region": "us-east-1", "awslogs-stream-prefix": "service-connect" } }, "services": [{ "portName": "http", "discoveryName": "sc-test-az-aware-backend", "clientAliases": [{ "port": 8090, "dnsName": "sc.test.az.aware.backend" }] }] }'
```前端服务使用 Service Connect 作为客户端，将出口流量路由到后端。它还附加到 ALB 以供外部访问：```
# Frontend Service aws ecs --region $REGION create-service \ --cluster $CLUSTER_NAME \ --service-name az-aware-fe-service-ec2 \ --task-definition az-aware-fe-service-ec2 \ --desired-count $TASK_COUNT \ --launch-type EC2 \ --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2,$SUBNET_3],securityGroups=[$CLIENT_SG]}" \ --load-balancers "[{ \"targetGroupArn\": \"$TG_ARN\", \"containerName\": \"fe-app\", \"containerPort\": 8080 }]" \ --service-connect-configuration '{ "enabled": true, "logConfiguration": { "logDriver": "awslogs", "options": { "awslogs-group": "/ecs/az-aware-fe-service-ec2", "awslogs-region": "us-east-1", "awslogs-stream-prefix": "service-connect" } }, "services": [{ "portName": "http", "discoveryName": "sc-test-az-aware-fe", "clientAliases": [{ "port": 8080, "dnsName": "sc.test.az.aware.fe" }] }] }'
```#### 步骤 8：验证部署

检查这两个服务是否正在运行并检索 ALB DNS 名称：```
# 检查集群状态 aws ecs --region $REGION describe-clusters \ --clusters $CLUSTER_NAME \ --query "clusters[0].registeredContainerInstancesCount" # 检查服务 aws ecs --region $REGION describe-services \ --cluster $CLUSTER_NAME \ --services az-aware-backend-service-ec2 az-aware-fe-service-ec2 \ --query "services[].[serviceName, runningCount,desiredCount]" # 获取 ALB DNS 名称 ALB_DNS=$(aws elbv2 --region $REGION describe-load-balancers \ --names $LB_NAME \ --query "LoadBalancers[0].DNSName" --output text) echo $ALB_DNS
```要测试端点，请使用“azAwareRouting”标头将流量发送到 ALB。这会触发前端通过 Service Connect 代理到后端：```
# Send traffic --- must include the azAwareRouting header to trigger backend proxy curl -H "azAwareRouting: true" -H "Connection: keep-alive" http://$ALB_DNS/
```响应是 JSON，显示哪个可用区处理前端和后端请求。

#### 步骤 9：验证区域感知路由

默认情况下，所有 Service Connect 服务均启用区域感知路由。发送多个请求并观察前端和后端 AZ 是否匹配（流量保持本地）：```
对于 $(seq 1 20) 中的 i； do curl -s -H "azAwareRouting: true" -H "Connection: keep-alive" http://$ALB_DNS/ | jq .完毕
```响应字段：

- `availabilityZoneId` — 前端任务处理请求的可用区。
- `upstreamAvailabilityZoneId` — 后端任务处理它的可用区。

在端点均匀分布的情况下（每个可用区有 2 个任务），两个字段应该匹配，这表明区域感知路由处于活动状态。

#### Step 10: Test failover behavior

要了解区域感知路由如何处理可用区不平衡，请缩小后端规模，使一个可用区没有端点。这演示了自动跨可用区溢出：```
# Scale backend to 2 tasks --- one AZ will have zero backend endpoints aws ecs update-service \ --region $REGION \ --cluster $CLUSTER_NAME \ --service az-aware-backend-service-ec2 \ --desired-count 2 # Wait for tasks to drain echo "Waiting for backend to scale down..." sleep 60 # Now send traffic --- you should see some cross-AZ routing for i in $(seq 1 20); do curl -s -H "azAwareRouting: true" -H "Connection: keep-alive" http://$ALB_DNS/ | jq '{frontend: .availabilityZoneId, backend: .upstreamAvailabilityZoneId}' done
```AZ 中的前端任务没有后端路由跨区域，因此这些请求的前端和后端 AZ 不同。

恢复平衡状态：```
aws ecs update-service \ --region $REGION \ --cluster $CLUSTER_NAME \ --service az-aware-backend-service-ec2 \ --desired-count $TASK_COUNT
```#### Step 11: Inspect Envoy stats

本演练中使用的容器映像直接在 HTTP 响应中公开可用区信息（“availabilityZoneId”和“upstreamAvailabilityZoneId”）。对于您自己的不公开可用区数据的应用程序容器，您可以直接检查 Envoy 统计信息以确认区域感知路由正在工作。

Connect to an EC2 instance through SSM and query the Envoy admin endpoint through its Unix socket:```
# Get an EC2 instance running frontend tasks CONTAINER_INSTANCE=$(aws ecs --region $REGION list-container-instances \ --cluster $CLUSTER_NAME \ --query 'containerInstanceArns[0]' --output text) INSTANCE_ID=$(aws ecs describe-container-instances \ --region $REGION \ --cluster $CLUSTER_NAME \ --container-instances $CONTAINER_INSTANCE \ --query 'containerInstances[0].ec2InstanceId' --output text) # Connect via SSM aws ssm start-session --region $REGION --target $INSTANCE_ID
```

连接到 EC2 实例后，找到 Service Connect 代理容器并通过 Unix 套接字查询 Envoy 统计信息：

```
sudo -i # Find the Service Connect agent container SC_AGENT_CONTAINER_ID=$(docker ps --filter "name=ecs-service-connect" -q | head -1) # Query Envoy stats via Unix socket docker exec -it $SC_AGENT_CONTAINER_ID \ curl --unix-socket /tmp/envoy_admin.sock http://unix/stats | grep -E "zone\."
```Key metrics:

|公制|检查什么 |
|:---|:---|
| `lb_zone_routing_cross_zone` | “0”表示所有流量都位于同一可用区。 |
| `lb_zone_cluster_too_small` |启动期间的非零值就可以了。 It should stabilize after all tasks are healthy. |

健康的部署显示“lb_zone_routing_cross_zone: 0”。

＃＃＃＃ 清理```
# 删除服务 aws ecs --region $REGION delete-service \ --cluster $CLUSTER_NAME --service az-aware-fe-service-ec2 --force aws ecs --region $REGION delete-service \ --cluster $CLUSTER_NAME --service az-aware-backend-service-ec2 --force # 等待任务耗尽睡眠 60 # 删除集群 aws ecs --region $REGION delete-cluster --cluster $CLUSTER_NAME # 删除 ASG aws autoscaling --region $REGION delete-auto-scaling-group \ --auto-scaling-group-name $ASG_NAME --force-delete # 删除启动模板 aws ec2 --region $REGION delete-launch-template \ --launch-template-name az-aware-ec2-launch-template # 删除负载均衡器 aws elbv2 --region $REGION delete-load-balancer --load-balancer-arn $ALB_ARN aws elbv2 --region $REGION delete-target-group --target-group-arn $TG_ARN # 删除安全组（等待 ENI 分离） sleep 30 aws ec2 --region $REGION delete-security-group --group-id $LB_SG aws ec2 --region $REGION delete-security-group --group-id $CLIENT_SG aws ec2 --region $REGION 删除安全组 --group-id $SERVER_SG
```### 关键考虑因素

- Minimum cluster size – To activate zone-aware routing, the total number of endpoints in the destination service must be at least 2× the number of Availability Zones (for example, at least 6 tasks for a 3-AZ deployment).该阈值由 Envoy 代理内部强制执行，客户不可配置。
- Automatic fallback – If the endpoint count falls below this threshold, zone-aware routing is automatically disabled, and traffic is distributed evenly across all AZs to preserve availability.
- Works with existing Service Connect features – Zone-aware routing works with existing Service Connect capabilities, including service discovery, cross-account connectivity, and traffic metrics.

### 结论

区域感知路由现已在所有支持 Amazon ECS 的 AWS 区域推出。

区域感知路由可降低跨可用区数据传输成本和延迟。由于它默认处于启用状态，因此您无需修改​​应用程序代码或部署其他基础设施。对于现有服务，重新部署一次即可激活该功能。

首先，打开 [Amazon ECS 控制台](https://console.aws.amazon.com/ecs/) 并重新部署现有服务以激活区域感知路由。要了解更多信息，请参阅 Amazon ECS 开发人员指南中的 [Service Connect](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect.html)。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
