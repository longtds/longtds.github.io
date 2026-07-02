<!-- news-meta
created_by: generate_daily_news.py
date: 2026-07-02T02:01:32+08:00
source: AWS ML Blog
domain: AI 基础设施
url: https://aws.amazon.com/blogs/machine-learning/hipporag-neurobiologically-inspired-rag-using-amazon-bedrock-amazon-neptune-and-personalized-pagerank/
content_mode: full-translated
original_language: non-zh
extraction_status: html-heuristic
-->

# HippoRAG：使用 Amazon Bedrock、Amazon Neptune 和个性化 PageRank 受神经生物学启发的 RAG |亚马逊网络服务

| 字段 | 内容 |
|:---|:---|
| 日期 | 2026-07-02 02:01 CST |
| 领域 | AI 基础设施 |
| 来源 | AWS ML Blog |
| 原文标题 | HippoRAG: Neurobiologically inspired RAG using Amazon Bedrock, Amazon Neptune, and personalized PageRank \| Amazon Web Services |
| 原文 | [打开原文](https://aws.amazon.com/blogs/machine-learning/hipporag-neurobiologically-inspired-rag-using-amazon-bedrock-amazon-neptune-and-personalized-pagerank/) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | html-heuristic |

## 摘要

在这篇文章中，我们演示如何使用全面的 AWS 堆栈实施 HippoRAG。我们使用 Amazon Bedrock 实现 LLM 功能，使用 Amazon Neptune 实现图形数据库功能，使用 Amazon Neptune Analytics 实现高级图形算法（包括个性化 PageRank），并使用 Amazon Titan Embeddings 实现矢量表示。此实施展示了如何在 AWS 基础设施中为企业级应用程序构建和部署 HippoRAG。

## 正文

### [人工智能](https://aws.amazon.com/blogs/machine-learning/)

## HippoRAG：使用 

Amazon Bedrock、Amazon Neptune 和个性化 PageRank 的受神经生物学启发的 RAG

LLM（LLM）已经改变了我们处理和生成信息的方式，但它们仍然难以有效地整合多个来源的知识。标准检索增强生成 (RAG) 方法虽然很有用，但在处理需要连接来自不同文档的信息的多跳推理任务时常常表现不佳。为了解决这些限制，我们探索了 [HippoRAG](https://arxiv.org/abs/2405.14831)，这是一种受人脑海马记忆系统启发的新型 RAG 框架。

在这篇文章中，我们演示如何使用全面的 AWS 堆栈实施 HippoRAG。我们使用 [Amazon Bedrock](https://aws.amazon.com/bedrock/) 实现 LLM 功能，使用 [Amazon Neptune](https://aws.amazon.com/neptune/) 实现图形数据库功能，使用 Amazon Neptune Analytics 实现高级图形算法，包括 [个性化 PageRank](https://en.wikipedia.org/wiki/PageRank)，使用 [Amazon Titan Embeddings](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html) 实现矢量表示。此实施展示了如何在 AWS 基础设施中为企业级应用程序构建和部署 HippoRAG。

### 神经生物学灵感和背景

[HippoRAG](https://arxiv.org/abs/2405.14831) 从人类长期记忆的海马索引理论中汲取灵感。在人类大脑中，新皮质处理感知输入，而海马体则创建记忆之间关联的索引。这种双组件系统使人类能够有效地整合不同体验中的信息。

标准 RAG 方法独立处理每个文档，难以解决需要跨多个来源连接信息的问题。 HippoRAG 通过以下方式解决了这个问题：

- 构建知识图（KG）来表示实体之间的关系。
- 使用个性化PageRank（PPR）算法进行高效的图遍历和相关性排名。
- 启用单步多跳检索，而不需要多次迭代。

### 解决方案架构

我们的 HippoRAG AWS 实施涉及四个主要组件：![AWS 上使用 Amazon Bedrock、Neptune 数据库、Neptune Analytics 和 Amazon Titan Embeddings 的 HippoRAG 架构](https://d2908q01vomqb2.cloudfront.net/f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59/2026/06/23/ML-19373-1.png)

- Amazon Bedrock – 提供 LLM 功能，用于提取知识图三元组、回答问题和识别命名实体。
- Amazon Neptune 数据库 – 存储知识图结构并支持基本的图操作。
- Amazon Neptune Analytics – 执行高级图形算法，特别是用于相关性排名的个性化 PageRank。
- Amazon Titan Embeddings – 创建文本的矢量表示以进行相似性匹配。

这种架构使我们能够充分利用个性化 PageRank 的功能，同时保持 AWS 托管服务的可扩展性和可靠性。

#### 先决条件

对于此实施，您需要：

- 有权访问 Amazon Bedrock 和 Neptune 服务的 AWS 账户。
- [Amazon Neptune 集群已配置且可访问](https://docs.aws.amazon.com/neptune/latest/userguide/get-started-create-cluster.html)。
- [从您的 Neptune 数据库创建的 Amazon Neptune Analytics 图表](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/create-graph-from-neptune-database.html)。
- 安装了 AWS 命令​​行界面 (AWS CLI) 和 Python 3.8+。
- 适当的 IAM 权限：[Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/security-iam.html) | [亚马逊海王星](https://docs.aws.amazon.com/neptune/latest/userguide/iam-auth.html) | [Amazon Neptune 分析](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/security-iam.html) | [Amazon 简单存储服务 (Amazon S3)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-access-control.html)。

### 数据处理管道：从 HotpotQA JSON 到 Neptune

实施 HippoRAG 必要的第一步是将原始数据转换为适合 Neptune 的知识图结构。在本节中，我们将介绍如何处理 JSON 格式的 HotpotQA 数据。我们使用 Amazon Bedrock 提取知识图三元组，生成 Neptune 批量加载 CSV 文件，将其上传到 Amazon S3，然后将其加载到我们的 Neptune 集群中。以下每个小节都对应于该管道的一个阶段。

#### 设置数据导入器HotpotQANeptuneImporter 类协调管道的每个阶段。它负责读取 JSON 源文件、生成 CSV 输出、将这些文件上传到 Amazon S3 以及触发 Neptune 批量加载程序。让我们看看如何使用 AWS 环境的配置值初始化此类：```
class HotpotQANeptuneImporter: """处理将 HotpotQA 数据导入 Neptune 的类。""" def __init__( self, hotpotqa_file_path: str, output_dir: str, s3_bucket: str, s3_prefix: str, neptune_endpoint: str, neptune_port: int, iam_role_arn: str, aws_region: str, llm_endpoint:Optional[str] = None, embedding_endpoint:Optional[str] = None, max_workers: int = 4, max_examples: int = 10, max_docs_per_example: int = 2, use_ssl: bool = False ): """使用配置初始化导入器。""" self.hotpotqa_file_path = hotpotqa_file_path self.output_dir = output_dir self.s3_bucket = s3_bucket self.s3_prefix = s3_prefix self.neptune_endpoint = neptune_endpoint self.neptune_port = neptune_port self.iam_role_arn = iam_role_arn self.aws_region = aws_region # 初始化AWS客户端 self.s3_client = boto3.client('s3',region_name=aws_region) self.session = boto3.Session() # 初始化数据结构 self.phrase_dict = {} # 将短语文本映射到节点 ID self.phrase_embeddings = {} # 将短语文本映射到嵌入向量
```####知识图谱三元组提取

该管道的关键部分是使用 Amazon Bedrock 的 LLM 功能从原始文本中提取结构化知识。对于每个段落，系统都会生成主语-关系-客体三元组，这些三元组成为知识图中的边。以下是我们实现提取的方法：```
def extract_triples_with_llm(self, text: str) -> List[Tuple[str, str, str]]: """ Use an LLM to extract knowledge graph triples from text. In this simplified version, just generate simple triples from the text. """ # Simple triple generation from text words = text.split() if len(words) < 5: return [] # Generate simple triples from the words in the text triples = [] for i in range(min(3, len(words) - 2)): # Get at most 3 triples subject = words[i] relation = "related_to" obj = words[i+2] triples.append((subject, relation, obj)) return triples
```#### 将 JSON 数据转换为 CSV 格式

有了三元组，我们需要将图表序列化为 Neptune 批量加载器期望的 CSV 格式。此处理方法将 HotpotQA JSON 记录转换为四个 CSV 文件：phrase_nodes.csv、passage_nodes.csv、relation_edges.csv 和 context_edges.csv。这些文件一起捕获完整的知识图结构。以下是我们实现该转换的方法：```
def process_data_to_csv(self, data: List[Dict]) -> None: """ Process HotpotQA data into CSV files for Neptune import. """ logger.info("Processing HotpotQA data to CSV files") # 打开所有 CSV 文件进行写入 with open(os.path.join(self.output_dir, 'phrase_nodes.csv'), 'w', newline='', encoding='utf-8')作为phrase_f，\ open（os.path.join（self.output_dir，'passage_nodes.csv'），'w'，换行=''，编码='utf-8'）作为passage_f，\ open（os.path.join（self.output_dir，'relation_edges.csv'），'w'，换行=''，编码='utf-8'）作为relation_f，\ open(os.path.join(self.output_dir, 'context_edges.csv'), 'w', newline='',encoding='utf-8') as context_f: # 写入标题phrase_f.write('~id,~label,text\n')passage_f.write('~id,~label,title,content\n')relation_f.write('~id,~from,~to,~label\n') context_f.write('~id,~from,~to,~label\n') # 处理每个示例，例如 tqdm(data, desc="处理示例"): self._process_example(example,passage_f,phrase_f,relation_f,context_f)
```#### 处理单个示例

每个 HotpotQA 示例都会被处理以在知识图中创建节点和边：```
def _process_example(self, example: Dict, passage_f, phrase_f, relation_f, context_f) -> None: """Process a single HotpotQA example into CSV data.""" # Process limited documents in the context doc_count = 0 for doc_title, paragraphs in example['context']: if doc_count >= self.max_docs_per_example: break # Process each paragraph as a passage for paragraph in paragraphs: if not paragraph.strip(): continue passage_id = f"passage_{uuid.uuid4().hex}" # Write passage node passage_f.write(f"{passage_id},passage,\"{self._escape_csv(doc_title)}\",\"{self._escape_csv(paragraph)}\"\n") # Extract triples from the paragraph triples = self.extract_triples_with_llm(paragraph) # Process each triple for subject, relation, obj in triples: # Create or get subject node ID if subject not in self.phrase_dict: subject_id = f"phrase_{uuid.uuid4().hex}" self.phrase_dict[subject] = subject_id phrase_f.write(f"{subject_id},phrase,\"{self._escape_csv(subject)}\"\n") else: subject_id = self.phrase_dict[subject] # Create or get object node ID if obj not in self.phrase_dict: obj_id = f"phrase_{uuid.uuid4().hex}" self.phrase_dict[obj] = obj_id phrase_f.write(f"{obj_id},phrase,\"{self._escape_csv(obj)}\"\n") else: obj_id = self.phrase_dict[obj] # Write relation edge relation_id = f"rel_{uuid.uuid4().hex}" relation_f.write(f"{relation_id},{subject_id},{obj_id},\"{self._escape_csv(relation)}\"\n") # Write context edges context_f.write(f"ctx_{uuid.uuid4().hex},{passage_id},{subject_id},contains\n") context_f.write(f"ctx_{uuid.uuid4().hex},{passage_id},{obj_id},contains\n") doc_count += 1
```#### 将数据加载到 Neptune

将数据处理成 CSV 文件后，系统将其上传到 S3 并导入到 Neptune 中：```
def import_to_neptune(self) -> Dict: """使用批量加载器 API 将数据导入 Neptune。""" logger.info(f"将数据导入 Neptune 端点 {self.neptune_endpoint}") loader_endpoint = f"{self.protocol}://{self.neptune_endpoint}:{self.neptune_port}/loader" payload = { "source": f"s3://{self.s3_bucket}/{self.s3_prefix}/", "format": "csv", "formatParams": { "delimiter": ",", "header": "true" }, "iamRoleArn": self.iam_role_arn, "region": self.aws_region, "failOnError": "FALSE" } try: # 创建 AWS4Auth请求凭证 = self.session.get_credentials() 如果凭证： auth = AWS4Auth(credentials.access_key,credentials.secret_key,self.aws_region,'neptune-db',session_token=credentials.token)response =requests.post(loader_endpoint,data=json.dumps(payload),headers={"Content-Type":"application/json"},timeout=30, auth=auth ) response.raise_for_status() result = response.json() logger.info(f"Neptune 加载作业已提交：{result}") 返回结果，但异常为 e: logger.error(f"无法提交 Neptune 加载作业：{e}") raise
```#### 运行完整的管道

您可以通过以下步骤运行完整的数据处理管道：```
def run_pipeline(self) -> None: """Run the full data processing and import pipeline.""" try: # Step 1: Test Neptune connectivity if not self.test_neptune_connection(): logger.warning("Neptune connectivity test failed, but proceeding with the pipeline") # Step 2: Load HotpotQA data data = self.load_hotpotqa_data() # Step 3: Process data to CSV files self.process_data_to_csv(data) # Step 4: Create empty synonym_edges.csv file with open(os.path.join(self.output_dir, 'synonym_edges.csv'), 'w', newline='', encoding='utf-8') as f: f.write('~id,~from,~to,~label\n') # Step 5: Upload CSV files to S3 self.upload_to_s3() # Step 6: Import data to Neptune load_result = self.import_to_neptune() load_id = load_result.get("payload", {}).get("loadId") if load_id: # Step 7: Wait for import to complete final_status = self.wait_for_load_job(load_id) logger.info(f"Final import status: {final_status}") logger.info("Pipeline completed successfully") except Exception as e: logger.error(f"Pipeline failed: {e}") raise
```### 实施

本节介绍 HippoRAG 实现的关键组件，从初始配置到知识图构建和检索。

#### 配置

首先，让我们为 HippoRAG 实现设置基本配置：```
from src.hipporag.utils.config_utils import BaseConfig config = BaseConfig() config.force_index_from_scratch = True config.openie_mode = "在线" config.llm_name = "us.anthropic.claude-3-5-haiku-20241022-v1:0" config.embedding_model_name = “amazon.titan-embed-text-v2:0” config.aws_region = “us-east-1” config.save_dir = “输出” config.retrieval_top_k = 3
```#### 海王星分析集成

我们实施中的一项关键创新是与 Amazon Neptune Analytics 集成以实现个性化 PageRank。我们创建了一个专门的客户端来处理高级图形分析：```
class NeptuneAnalyticsClient: """Client for Neptune Analytics operations including personalized PageRank.""" def __init__(self, graph_id, region='us-east-1'): """Initialize Neptune Analytics client.""" self.graph_id = graph_id self.region = region self.client = boto3.client('neptune-analytics', region_name=region) logger.info(f"Initialized Neptune Analytics client for graph {graph_id}") def run_personalized_pagerank(self, seed_nodes, damping_factor=0.85, max_iterations=20, tolerance=0.0001): """ Run personalized PageRank algorithm on Neptune Analytics. Args: seed_nodes (list): List of seed node IDs for personalized PageRank damping_factor (float): Damping factor (default 0.85) max_iterations (int): Maximum number of iterations tolerance (float): Convergence tolerance Returns: list: List of (node_id, score) tuples sorted by score descending """ if not seed_nodes: logger.warning("No seed nodes provided for personalized PageRank") return [] # Format seed nodes for the query seed_list = ",".join([f"'{node}'" for node in seed_nodes]) # Neptune Analytics personalized PageRank query using openCypher query = f""" CALL neptune.algo.pagerank({{ sourceNodes: [{seed_list}], dampingFactor: {damping_factor}, maxIterations: {max_iterations}, tolerance: {tolerance}, personalized: true }}) YIELD nodeId, score RETURN nodeId, score ORDER BY score DESC LIMIT 100 """ try: result = self.execute_analytics_query(query) if result and 'results' in result: pagerank_results = [(item['nodeId'], item['score']) for item in result['results']] logger.info(f"Personalized PageRank returned {len(pagerank_results)} results") return pagerank_results return [] except Exception as e: logger.error(f"Failed to run personalized PageRank: {e}") return []
```####知识图谱构建

HippoRAG 使用 Amazon Bedrock 的 LLM 功能根据文档构建知识图。此过程从文本中提取实体和关系：```
def index_from_neptune(self, limit=1000): """ 直接从 Neptune 数据库索引文档。参数： limit (int): 索引的最大文档数 """ Documents = self.neptune_client.get_documents(limit=limit) logger.info(f"Indexing {len(documents)} files from Neptune database") # 对 Neptune 中的文档使用标准索引过程 super().index(documents)
```索引过程涉及：

- 使用 Claude LLM 从段落中提取命名实体。
- 使用开放信息提取创建知识图三元组。
- 使用 Amazon Titan Embeddings 计算实体的嵌入。
- 将图形结构存储在 Amazon Neptune 数据库中。
- 在相似实体之间添加同义词边缘。
- 为 Neptune Analytics 处理准备图表。

#### 个性化 PageRank 检索

HippoRAG 的核心优势是它能够使用个性化 PageRank 执行复杂的多跳检索。我们的实施使用 Neptune Analytics 来实现此目的：```
def retrieve_with_personalized_pagerank(self, queries, num_to_retrieve=None): """ Enhanced retrieval using personalized PageRank through Neptune Analytics. Args: queries (list): List of query strings num_to_retrieve (int): Number of documents to retrieve Returns: list: List of QuerySolution objects """ if not self.ready_to_retrieve: self.prepare_retrieval_objects() if num_to_retrieve is None: num_to_retrieve = self.global_config.retrieval_top_k retrieval_results = [] for query in queries: logger.info(f"Processing query with personalized PageRank: {query}") # First get standard retrieval results as fallback basic_results = list(super().retrieve([query]))[0] # Enhanced retrieval with personalized PageRank enhanced_docs = [] pagerank_scores = [] if self.analytics_client: # Find entities related to the query seed_entities = self.neptune_client.entity_search(query, limit=5) if seed_entities: logger.info(f"Found {len(seed_entities)} seed entities for PageRank") # Run personalized PageRank from seed entities pagerank_results = self.analytics_client.run_personalized_pagerank( seed_nodes=seed_entities, damping_factor=0.85, max_iterations=20 ) if pagerank_results: # Get passages ranked by PageRank scores ranked_passages = self.analytics_client.get_passages_by_pagerank( pagerank_results, top_k=num_to_retrieve * 2 ) # Extract content and scores for content, score in ranked_passages: if content and content not in enhanced_docs: enhanced_docs.append(content) pagerank_scores.append(score) logger.info(f"PersonalizedPageRank retrieved {len(enhanced_docs)} documents") # Combine PageRank results with basic results combined_docs = [] combined_scores = [] # Add PageRank results first (they're already ranked) for i, doc in enumerate(enhanced_docs[:num_to_retrieve]): combined_docs.append(doc) combined_scores.append(pagerank_scores[i] if i < len(pagerank_scores) else 0.5) # Fill remaining slots with basic results if needed for doc in basic_results.docs: if len(combined_docs) >= num_to_retrieve: break if doc and doc not in combined_docs: combined_docs.append(doc) combined_scores.append(0.1) # Lower score for non-PageRank results # Create and append retrieval result result = QuerySolution( question=query, docs=combined_docs[:num_to_retrieve], doc_scores=combined_scores[:num_to_retrieve] ) retrieval_results.append(result) return retrieval_results
```#### 设置 Neptune Analytics

在运行实施之前，您需要从 Neptune 数据库创建 Neptune Analytics 图表：```
def find_or_create_analytics_graph(neptune_cluster_id, Region='us-east-1'): """ 查找现有的 Neptune Analytics 图表或创建新图表。 """ client = boto3.client('neptune-analytics', Region_name=region) try: # 列出现有的分析图表 response = client.list_graphs() if response.get('graphs'): # 返回第一个可用图表 first_graph = response['graphs'][0] if first_graph['status'] == 'AVAILABLE': return first_graph['id'] # 如果不存在则创建一个新的分析图 create_response = client.create_graph( graphName=f"hipporag-analytics-{int(time.time())}",replicaCount=1, sourceDbClusterIdentifier=neptune_cluster_id ) return create_response['id'] except Exception as e: logger.error(f"管理 Neptune Analytics 图表时出错：{e}") return None
```### 演示和结果

让我们通过 [个性化 pagerank](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/page-rank.html) 演示一下 AWS 原生 HippoRAG 实现：```
# Initialize NeptuneHippoRAG with Analytics support hippo = NeptuneHippoRAG( global_config=config, neptune_endpoint="your-neptune-endpoint.us-east-1.neptune.amazonaws.com", neptune_port=8182, analytics_graph_id="g-your-analytics-graph-id" ) # Index data from Neptune hippo.index_from_neptune(limit=1000) # Example queries questions = ["Who painted the Mona Lisa?", "Which city is the capital of France?", "What is the height of the Eiffel Tower?", "What is the connection between Leonardo da Vinci and France?", ] # Process each query with personalized PageRank for question in questions: # Get retrieval results with personalized PageRank results = hippo.retrieve_with_personalized_pagerank([question]) # Generate answer using the QA method qa_results, _, _ = hippo.qa(results) # Display the answer with PageRank scores print(f"Question: {question}") print(f"Answer: {qa_results[0].answer}") print(f"Top documents (PageRank ranked):") for i, (doc, score) in enumerate(zip(results[0].docs, results[0].doc_scores)): print(f" Doc {i+1} (Score: {score:.4f}): {doc[:100]}...")
```从我们的测试结果中，我们可以看到具有个性化 PageRank 的 HippoRAG 可以正确检索文档并对其进行排名：```
问：《蒙娜丽莎》是谁画的？答案：列奥纳多·达·芬奇 热门文档（PageRank 排名）： 文档 1（得分：0.8234）：列奥纳多·达·芬奇在 1503 年至 1519 年间绘制了《蒙娜丽莎》... 文档 2（得分：0.6891）：《蒙娜丽莎》收藏于巴黎卢浮宫博物馆... 文档 3（得分：0.5432）：达芬奇是意大利文艺复兴时期的艺术家因...而闻名 问题：列奥纳多·达·芬奇和法国之间有什么联系？答案：列奥纳多·达·芬奇于 1519 年在法国去世，他在国王弗朗西斯一世的庇护下度过了他的最后几年。 顶级文件（PageRank 排名）： 文档 1（分数：0.9156）：列奥纳多·达·芬奇于 1519 年在法国克洛斯吕斯城堡去世... 文档 2（分数：0.7832）：法国国王弗朗西斯一世邀请列奥纳多在他的宫廷工作... Doc 3（分数：0.6234）：艺术家在法国昂布瓦斯度过了他的最后三年......
```最后一个问题展示了 HippoRAG 连接多个文档信息的能力。它使用个性化 PageRank 根据相对于查询实体的图论重要性对最相关的段落进行排名。

### 寻路多跳检索

HippoRAG 最令人印象深刻的功能之一是解决研究人员所说的“寻路”多跳问题。与实体之间有明确定向路径的“路径跟踪”问题不同，路径寻找问题需要探索多个潜在路径来寻找联系。

考虑这个例子：问题：哪位斯坦福大学教授研究阿尔茨海默病的神经科学？

对于这个问题，具有个性化PageRank的HippoRAG可以直接导航知识图谱。它使用 PageRank 算法来识别和排名连接斯坦福大学、神经科学和阿尔茨海默病研究的最相关路径。

个性化 PageRank 算法从与“斯坦福”、“神经科学”和“阿尔茨海默病”相关的种子节点开始。然后，它通过图表传播相关性分数，以识别与查询概念联系最紧密的实体和段落。

此功能对于科学文献综述、法律案例分析或医疗诊断等复杂的企业用例特别有价值。

### 优点和性能

使用这个全面的 AWS 堆栈实施的 HippoRAG 方法具有以下几个关键优势：

- 高性能：HippoRAG 是 GraphRAG 的一个性能良好的变体，擅长复杂的多跳推理任务。
- 单步效率：个性化PageRank可以实现与迭代方法不同的直接多跳检索。
- 高级图形分析：Neptune Analytics 提供具有高性能和可扩展性的个性化 PageRank 计算。
- AWS 集成：充分使用 Amazon Bedrock、Neptune 和 Neptune Analytics 等托管服务，以实现可靠性和易于管理。
- 持续学习：使用新信息进行更新，无需重新训练模型。
- 企业就绪：安全、可扩展且与现有 AWS 基础设施兼容。

高性能来自于使用基于图的检索和个性化 PageRank 的基本方法。 AWS 原生堆栈在可扩展性、安全性和维护方面提供了显着的运营优势。

＃＃＃ 清理- 完成后，清理资源以停止产生成本。您可以使用 AWS 管理控制台来执行此操作。有关说明，请参阅 [Amazon Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/manage-console-delete.html)、[Amazon Neptune Analytics](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/delete-graph.html)、[Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html) 和 [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-bucket.html) 文档。您还可以删除作为本演练的一部分创建的任何 IAM 角色和策略。

### 结论

具有个性化 PageRank 的 HippoRAG 为多文档问答提供了标准 GraphRAG 的可行替代方案。通过使用 Amazon Bedrock、Neptune Database、Neptune Analytics 和 Amazon Titan Embeddings 实施它，我们创建了一个强大的、受神经生物学启发的解决方案。该解决方案可以通过复杂的相关性排名来处理复杂的多跳推理任务。

此方法演示了如何组合 AWS 服务来创建超越标准 RAG 实施的复杂人工智能 (AI) 解决方案。基于图形的检索与个性化 PageRank 和最先进的法学硕士的集成为需要跨多个来源的深度知识集成的企业应用程序开辟了新的可能性。

我们期待看到您如何将该技术应用到您自己的用例中！

### 参考文献

- [HippoRAG：神经生物学启发的LLM长期记忆](https://arxiv.org/abs/2405.14831)（原始研究论文）。
- [Amazon Bedrock 文档](https://docs.aws.amazon.com/bedrock/)。
- [Amazon Neptune 文档](https://docs.aws.amazon.com/neptune/)。
- [Amazon Neptune Analytics 文档](https://docs.aws.amazon.com/neptune-analytics/)。
- [Amazon Titan 嵌入文档](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)。

### 关于作者

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

[返回新闻列表](../index.md)
