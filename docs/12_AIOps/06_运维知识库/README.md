# 运维知识库

> 老工程师的经验 = 公司最值钱也最容易流失的资产。**知识库 + RAG + LLM = 让经验沉淀成可被 AI 检索的"机器记忆"**，新人 3 天上手老 SRE 半年的活儿。

## 一、为什么需要运维知识库

```
痛点:
  ❌ Wiki 写了没人看（结构差/搜不到）
  ❌ 老工程师离职带走一切
  ❌ 故障复盘归档了等于没归档
  ❌ Runbook 过期但还在用
  ❌ 新人入职没人带，靠群问
  ❌ 多套系统知识割裂

目标:
  ✅ 知识沉淀 → 结构化 → 可检索
  ✅ 问题 → 答案 < 30 秒
  ✅ Runbook、复盘、Wiki、Slack/微信对话 → 统一入口
  ✅ LLM 直接给答案（不只是"匹配文档"）
  ✅ 反馈闭环 → 知识自动更新
```

## 二、知识库的四代演进

| 代 | 形态 | 检索 | 痛点 |
|:---:|:---|:---|:---|
| **1 代** | Wiki/Confluence | 关键词 | 找不到 |
| **2 代** | 全文搜索 (ES/Solr) | 倒排索引 | 同义词差 |
| **3 代** | 向量检索 (RAG) | 语义召回 | 召回粗 |
| **4 代** | RAG + LLM Agent | 多跳 + 工具 | 现在主流 |

## 三、知识来源（多源融合）

| 来源 | 内容 | 重要度 |
|:---|:---|:---:|
| **Confluence / Notion / Wiki** | 系统设计、流程 | ⭐⭐⭐⭐⭐ |
| **Runbook** | 标准处置手册 | ⭐⭐⭐⭐⭐ |
| **Postmortem** | 故障复盘 | ⭐⭐⭐⭐⭐ |
| **Jira / 工单** | 历史问题处置记录 | ⭐⭐⭐⭐ |
| **Slack/钉钉/企微对话** | 实战经验（脱敏后） | ⭐⭐⭐⭐ |
| **Git 提交说明** | 代码变更原因 | ⭐⭐⭐ |
| **代码注释 + README** | 技术细节 | ⭐⭐⭐ |
| **CMDB / 拓扑** | 系统资产 | ⭐⭐⭐⭐ |
| **告警规则 + 日志样本** | 异常模式 | ⭐⭐⭐⭐ |
| **培训材料** | 入门 / 进阶 | ⭐⭐⭐ |
| **公开技术博客** | 业界经验 | ⭐⭐⭐ |

## 四、知识库整体架构

```
┌────── 知识源 ─────────────────────────────┐
│ Confluence / Notion / Wiki / Git /        │
│ Jira / Slack / 企微 / 飞书 / 监控元数据   │
└────────────┬──────────────────────────────┘
             ↓
┌────── 采集层 ─────────────────────────────┐
│ Connector / Crawler / Webhook              │
│ - Confluence API                          │
│ - Notion API                              │
│ - Git Webhook                             │
│ - Slack Web API                           │
└────────────┬──────────────────────────────┘
             ↓
┌────── 处理层 ─────────────────────────────┐
│ 清洗 / 脱敏 / 切分 / 提取                  │
│ - 去 HTML / 提取代码块                    │
│ - PII / Secret 检测                       │
│ - 文档切片（chunk）                       │
│ - 元数据提取（标签、时间、作者）           │
└────────────┬──────────────────────────────┘
             ↓
┌────── 索引层 ─────────────────────────────┐
│ Vector DB + Full-text + Knowledge Graph    │
│ - Milvus / pgvector / Qdrant              │
│ - Elasticsearch / OpenSearch              │
│ - Neo4j / Nebula（实体关系）              │
└────────────┬──────────────────────────────┘
             ↓
┌────── 检索层 ─────────────────────────────┐
│ Hybrid Retrieval                           │
│ - 向量召回 + BM25 + KG                    │
│ - Rerank                                   │
│ - 多查询改写                              │
└────────────┬──────────────────────────────┘
             ↓
┌────── 生成层 ─────────────────────────────┐
│ LLM + RAG + Tool                           │
│ - 引用源（必须）                          │
│ - 多步推理                                │
│ - 工具调用（查实时数据）                  │
└────────────┬──────────────────────────────┘
             ↓
┌────── 入口层 ─────────────────────────────┐
│ ChatBot / Web / API / IDE 插件 / 告警系统  │
└───────────────────────────────────────────┘
```

## 五、文档采集与清洗

### 5.1 Confluence 同步

```python
from atlassian import Confluence

conf = Confluence(url='https://wiki.company.com',
                  username='bot', password='token')

def sync_confluence(space_key):
    pages = conf.get_all_pages_from_space(space=space_key, limit=500)
    for p in pages:
        page = conf.get_page_by_id(p['id'], expand='body.storage,version,history')
        save_to_kb({
            "source": "confluence",
            "id": p['id'],
            "title": p['title'],
            "url": f"{CONF_BASE}/pages/{p['id']}",
            "content": html_to_markdown(page['body']['storage']['value']),
            "updated_at": page['version']['when'],
            "author": page['version']['by']['displayName'],
            "labels": get_labels(p['id'])
        })
```

### 5.2 通用文档清洗

```python
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def clean_document(raw_html_or_md):
    # HTML → Markdown
    if "<html" in raw_html_or_md:
        content = md(raw_html_or_md)
    else:
        content = raw_html_or_md
    
    # 去掉 Confluence 宏 / 模板字段
    content = re.sub(r'\{[a-z\-]+:[^}]*\}', '', content)
    
    # 脱敏
    content = redact_secrets(content)
    
    # 去除多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()

def redact_secrets(text):
    patterns = [
        (r'(password|passwd|pwd|token|secret|key)["\s:=]+([A-Za-z0-9+/=]{20,})', r'\1=***REDACTED***'),
        (r'(?i)bearer\s+[A-Za-z0-9._-]+', '***REDACTED***'),
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', lambda m: anonymize_ip(m.group(0))),
        (r'(?:[0-9]{4}[ -]?){3}[0-9]{4}', '***CARD***'),
        (r'1[3-9]\d{9}', '***PHONE***'),
    ]
    for pat, repl in patterns:
        text = re.sub(pat, repl, text)
    return text
```

### 5.3 PII / 敏感信息检测

```python
# 用 Microsoft Presidio 或开源方案
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def anonymize(text):
    results = analyzer.analyze(text=text, entities=[
        "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
        "IP_ADDRESS", "PERSON", "LOCATION"
    ], language='en')
    return anonymizer.anonymize(text=text, analyzer_results=results).text
```

## 六、文档切分策略（chunking）

### 6.1 切分原则

```
✅ 语义完整（不要切断段落）
✅ 大小适中（300-800 token）
✅ 重叠 10-20%（chunk_overlap=100）
✅ 结构感知（按标题/列表/代码块）
✅ 元数据携带（chunk 来自哪个 doc/section）
```

### 6.2 Markdown 结构化切分

```python
from langchain.text_splitter import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter
)

# 第一层：按 Markdown 标题切
headers_to_split_on = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]
md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
md_docs = md_splitter.split_text(markdown_content)

# 第二层：太长的 chunk 再切
char_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "；", "！", "？", " "]
)
chunks = []
for doc in md_docs:
    sub = char_splitter.split_text(doc.page_content)
    for s in sub:
        chunks.append({
            "content": s,
            "metadata": {**doc.metadata, "source_doc": doc_id}
        })
```

### 6.3 代码 / 配置专用切分

```python
# 不要把代码块切散
def smart_split(content):
    parts = []
    in_code = False
    buffer = []
    for line in content.split('\n'):
        if line.startswith('```'):
            in_code = not in_code
        buffer.append(line)
        if not in_code and len('\n'.join(buffer)) > 600:
            parts.append('\n'.join(buffer))
            buffer = []
    if buffer:
        parts.append('\n'.join(buffer))
    return parts
```

### 6.4 父子分块（Parent-Child）

```python
# 子块用于召回（短、精）
# 父块用于上下文（长、完整）
parent_chunks = split_by_section(doc, size=2000)
child_chunks  = split_by_paragraph(doc, size=300)

# 召回 child，返回 parent
for c in child_chunks:
    parent = find_parent(c, parent_chunks)
    vectorstore.add(c.content, metadata={"parent_id": parent.id, "child_id": c.id})

def retrieve(query):
    children = vectorstore.search(query, k=20)
    parents  = [load_parent(c.metadata["parent_id"]) for c in children]
    return unique(parents)
```

## 七、向量化（Embedding）

### 7.1 中文 Embedding 选型

| 模型 | 维度 | 适合 | 推荐 |
|:---|:---:|:---|:---:|
| **bge-large-zh-v1.5** | 1024 | 中文通用 | ⭐⭐⭐⭐⭐ |
| **bge-m3** | 1024 | 多语言+长文档 | ⭐⭐⭐⭐⭐ |
| **conan-embedding-v1** | 1792 | 2024 中文新 SOTA | ⭐⭐⭐⭐⭐ |
| **stella-base-zh-v3** | 1024 | 轻量 | ⭐⭐⭐⭐ |
| **m3e-large** | 1024 | 老牌 | ⭐⭐⭐ |
| **text-embedding-3-large** | 3072 | 英文 | ⭐⭐⭐ |
| **Cohere embed-multilingual** | 1024 | 多语言 | ⭐⭐⭐ |

### 7.2 部署 Embedding 服务

```python
# FastAPI + sentence-transformers
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

app = FastAPI()
model = SentenceTransformer("BAAI/bge-large-zh-v1.5", device="cuda")

@app.post("/embed")
def embed(req: dict):
    texts = req['texts']
    # 文档加 passage: 前缀，query 加 query:
    if req.get('type') == 'query':
        texts = [f"query: {t}" for t in texts]
    vectors = model.encode(texts, normalize_embeddings=True)
    return {"vectors": vectors.tolist()}
```

更推荐 **TEI（HuggingFace Text Embeddings Inference）** 或 **Infinity**，吞吐高 5-10x：

```bash
docker run -d --gpus all \
  -p 8080:80 -v $PWD/models:/data \
  ghcr.io/huggingface/text-embeddings-inference:1.5 \
  --model-id BAAI/bge-large-zh-v1.5
```

### 7.3 向量数据库选型

| DB | 规模 | 部署 | 适合 |
|:---|:---:|:---|:---|
| **Milvus / Zilliz** | 亿+ | K8s 复杂 | 大规模 |
| **pgvector** | 千万 | 极简 | 已有 PG |
| **Qdrant** | 千万 | 简单 | 中等 |
| **Chroma** | 百万 | 极简 | POC / 小 |
| **Weaviate** | 千万 | 中 | 多模态 |
| **Vespa** | 亿+ | 复杂 | 搜索引擎级 |
| **ES with kNN** | 千万 | 中 | 已有 ES |
| **OpenSearch** | 千万 | 中 | ES Fork |

**经验**：
- POC: pgvector（千万级以下完全够）
- 生产中等规模: Qdrant
- 生产大规模: Milvus

### 7.4 pgvector 实战

```sql
CREATE EXTENSION vector;

CREATE TABLE kb_chunks (
  id BIGSERIAL PRIMARY KEY,
  content TEXT,
  source VARCHAR(50),
  doc_id VARCHAR(100),
  title TEXT,
  url TEXT,
  tags TEXT[],
  updated_at TIMESTAMP,
  embedding VECTOR(1024)
);

-- HNSW 索引（推荐，比 IVFFlat 召回更好）
CREATE INDEX ON kb_chunks USING hnsw (embedding vector_cosine_ops)
  WITH (m=16, ef_construction=64);

-- 元数据索引
CREATE INDEX ON kb_chunks (source, updated_at);
CREATE INDEX ON kb_chunks USING gin (tags);

-- 全文索引（混合检索）
ALTER TABLE kb_chunks ADD COLUMN content_tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED;
CREATE INDEX ON kb_chunks USING gin (content_tsv);

-- 检索：向量 + 全文 混合
WITH vec AS (
  SELECT id, content, 1 - (embedding <=> $1) AS vec_score
  FROM kb_chunks ORDER BY embedding <=> $1 LIMIT 50
),
ft AS (
  SELECT id, content, ts_rank(content_tsv, plainto_tsquery($2)) AS ft_score
  FROM kb_chunks WHERE content_tsv @@ plainto_tsquery($2) LIMIT 50
)
SELECT v.id, v.content, COALESCE(v.vec_score, 0) * 0.7 + COALESCE(ft_score, 0) * 0.3 AS score
FROM vec v FULL JOIN ft USING (id) ORDER BY score DESC LIMIT 10;
```

## 八、检索（Retrieval）

### 8.1 混合检索（Hybrid）⭐⭐⭐⭐⭐

```
向量召回 (Dense)   语义匹配，但语义相近 ≠ 答案相关
   +
BM25 (Sparse)      关键词匹配，准但召回低
   +
知识图谱 (KG)       实体关系，多跳推理
   ↓
合并 + 去重 + Rerank
```

### 8.2 多查询改写（Query Rewriting）

```python
def rewrite_query(original):
    """生成多个语义等价的查询，提高召回"""
    prompt = f"""把这个运维问题改写成 3 个不同表述：
原: {original}
要求: 一个偏技术、一个偏现象、一个偏术语
"""
    queries = llm.generate(prompt).split('\n')
    return [original] + queries

# 检索时把多个查询的结果合并去重
def multi_query_retrieve(original):
    queries = rewrite_query(original)
    all_results = []
    for q in queries:
        all_results += vectorstore.search(q, k=20)
    return dedup_and_merge(all_results)
```

### 8.3 HyDE（Hypothetical Document Embeddings）

```python
# 让 LLM 先生成一段"假设的答案"，再用它去检索
def hyde_retrieve(query):
    fake_answer = llm.generate(f"假设你知道答案，写一段对这个问题的简短回答：{query}")
    return vectorstore.search(fake_answer, k=10)

# 效果：召回更精准（特别是问得很短时）
```

### 8.4 Rerank（重排）⭐⭐⭐⭐⭐

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-large")

def retrieve_with_rerank(query, top_k=5):
    candidates = hybrid_retrieve(query, k=50)
    pairs = [[query, c.content] for c in candidates]
    scores = reranker.predict(pairs, batch_size=32)
    
    # 按重排分数排序
    sorted_idx = scores.argsort()[::-1][:top_k]
    return [candidates[i] for i in sorted_idx]
```

**性价比**：rerank 让 RAG 精度提升 20-40%，必装。

### 8.5 元数据过滤

```python
# 检索时按时间、来源、标签过滤
results = vectorstore.search(
    query,
    k=20,
    filter={
        "source": {"$in": ["runbook", "postmortem"]},
        "updated_at": {"$gte": "2025-01-01"},
        "tags": {"$contains": "mysql"}
    }
)
```

### 8.6 自我反思（Self-RAG / CRAG）

```python
# 检索结果不够好时，自动调整
def smart_retrieve(query, max_iter=3):
    for i in range(max_iter):
        results = hybrid_retrieve(query)
        relevance = llm.evaluate_relevance(query, results)
        
        if relevance > 0.7:
            return results
        elif relevance < 0.3:
            # 太烂，扩搜或换策略
            query = llm.rewrite(query)
        else:
            # 部分有用，挑出好的继续
            return [r for r in results if llm.is_relevant(query, r)]
    return results
```

## 九、生成（Generation）

### 9.1 提示词模板

```python
RAG_PROMPT = """你是公司的资深 SRE 助理，基于知识库回答运维问题。

【检索到的相关文档】
{context}

【用户问题】
{question}

【回答要求】
1. 只基于上述文档作答，文档没有的就明确说"知识库中暂无"
2. 每个关键事实必须标注引用，格式: [doc:doc_id]
3. 如果是处置类问题，给出可执行的步骤
4. 如果问题涉及风险操作，必须给出风险提示
5. 保持简洁，但完整覆盖关键点

【回答】
"""

def rag_answer(question):
    docs = retrieve_with_rerank(question, top_k=5)
    context = "\n\n".join([f"[doc:{d.id}] {d.title}\n{d.content}" for d in docs])
    
    return llm.generate(RAG_PROMPT.format(context=context, question=question))
```

### 9.2 引用源（强制）

```
✅ 必须引用源
✅ 引用源可点击跳转
✅ 找不到答案就说找不到
❌ 不要"编"答案
❌ 不要混用知识库 + 通用知识（要标明）
```

### 9.3 拒答 / 引导

```python
# 召回为空 → 引导反馈
if not docs:
    return f"""
    📚 知识库中没有找到相关内容。
    
    建议:
    - 换个说法再问？
    - 这个问题需要由值班 SRE 协助
    - 解决后请补充进知识库 → [新建文档]
    
    [我来回答] [转值班] [跳过]
    """
```

### 9.4 流式输出 + 引用渲染

```python
@app.post("/ask")
async def ask(request):
    docs = retrieve(request.question)
    
    async for chunk in llm.stream(RAG_PROMPT.format(...)):
        yield {"type": "answer", "content": chunk}
    
    yield {
        "type": "sources",
        "sources": [{"title": d.title, "url": d.url} for d in docs]
    }
```

## 十、入口 / 接入方式

### 10.1 ChatBot

```python
# 企业微信 / 钉钉 / 飞书机器人
@bot.on_message
async def handle(msg):
    # 群里 @ 机器人 或 私聊
    answer = await rag_answer(msg.text, user=msg.from_user)
    await msg.reply(answer)
```

### 10.2 Web 入口

```
独立 Web UI:
  - 搜索框 + 分类
  - 高频问题 Top 10
  - 答案 + 引用源 + 点赞 / 踩

集成入口:
  - 内部门户 / 工单系统
  - Grafana 面板嵌入
```

### 10.3 告警卡片集成

```
告警通知卡片中:
  "可能相关的知识库:
   - [INC-2024-001] 类似的 MySQL 主从延迟
   - [Runbook] MySQL 主从延迟排查 SOP"
  
→ 一键打开 / 一键问 LLM
```

### 10.4 IDE / 终端插件

```
VSCode / IntelliJ 插件:
  - 选中报错 → 右键"查知识库"
  - 自动关联当前服务的 Runbook

终端 fzf/ai-shell 集成:
  - 输入命令前 LLM 提示历史踩坑
```

### 10.5 API

```python
# RESTful API
POST /api/v1/ask
  {"question": "...", "user": "...", "filters": {...}}
  → {"answer": "...", "sources": [...], "confidence": 0.8}

# 给其他系统调用（告警、工单等）
```

## 十一、反馈闭环（自我进化）

### 11.1 用户反馈

```
每个回答下都有:
  👍 有用    → 加入正例
  👎 没用    → 加入负例 + 收集原因
  📝 补充    → 触发新知识录入
  🔍 查源    → 跳转到原文
```

### 11.2 自动化更新

```python
# 1. 反馈数据驱动检索调优
def update_retrieval_from_feedback():
    positive = load_feedback(rating='positive')
    negative = load_feedback(rating='negative')
    
    # Fine-tune reranker
    train_pairs = [(p.query, p.doc, 1) for p in positive] + \
                  [(n.query, n.doc, 0) for n in negative]
    train_reranker(train_pairs)

# 2. 知识断层检测
def detect_gaps():
    """连续 N 次找不到答案 = 知识断层"""
    queries_no_answer = load_queries(no_answer=True)
    clusters = cluster_queries(queries_no_answer)
    for c in clusters:
        if c.size > 5:
            create_task(f"补充知识: {c.topic}")
```

### 11.3 文档新鲜度治理

```python
def doc_freshness_check():
    """老旧文档自动标记"""
    for doc in all_docs:
        if doc.updated_at < now() - 365 days:
            tag_as_stale(doc)
            notify_owner(doc, "请审核或归档")
```

## 十二、安全与权限

### 12.1 权限模型

```python
class KBPermission:
    """文档级 RBAC"""
    def __init__(self, doc):
        self.doc = doc
        self.allowed_users = doc.metadata.get('allowed_users', [])
        self.allowed_groups = doc.metadata.get('allowed_groups', [])
        self.sensitivity = doc.metadata.get('sensitivity', 'normal')

    def can_access(self, user):
        if self.sensitivity == 'public':
            return True
        if user.id in self.allowed_users:
            return True
        if any(g in user.groups for g in self.allowed_groups):
            return True
        return False

# 检索时过滤
def retrieve_with_acl(query, user):
    candidates = vectorstore.search(query, k=50)
    filtered = [c for c in candidates if KBPermission(c).can_access(user)]
    return filtered[:5]
```

### 12.2 审计与水印

```
✅ 所有查询入库（审计）
✅ 文档级访问日志
✅ 答案带"AI 生成"水印
✅ 敏感问题告警（如"如何 DROP 生产库"）
```

### 12.3 防数据泄漏

```
✅ Embedding 模型本地部署
✅ LLM 本地部署（vLLM）
✅ 知识库不出公司
✅ 不调用公网 API（GPT/Claude）
✅ PII / 密钥脱敏
✅ 提示词注入防护
```

## 十三、评估（怎么知道好不好）

### 13.1 离线评估

```python
# 准备金标准数据集（问答对 + 标准答案）
test_set = [
    {"question": "MySQL 主从延迟怎么排查",
     "expected_answer": "...",
     "expected_docs": ["doc-101", "doc-205"]}
]

# 自动评估指标
def evaluate(test_set):
    metrics = {
        "hit_rate": [],         # 召回中是否有正确文档
        "mrr": [],              # Mean Reciprocal Rank
        "ndcg": [],             # 排序质量
        "answer_relevance": [], # LLM 评估答案
        "faithfulness": [],     # 答案是否忠于文档
        "context_recall": [],   # 上下文覆盖度
    }
    for case in test_set:
        docs = retrieve(case["question"])
        ans = generate(case["question"], docs)
        metrics["hit_rate"].append(any(d.id in case["expected_docs"] for d in docs))
        metrics["faithfulness"].append(llm_judge_faithfulness(ans, docs))
        ...
    return {k: np.mean(v) for k, v in metrics.items()}
```

### 13.2 在线指标

```
覆盖率:
  - 提问总数
  - "找不到答案"占比
  - 知识断层数

质量:
  - 👍/👎 比
  - 平均回答时间
  - 重复提问率

业务:
  - 转人工率 ↓
  - MTTR ↓
  - 新人上手时间 ↓
```

### 13.3 框架推荐

```
RAGAs:        RAG 自动评估框架
TruLens:      LLM 应用评估
DeepEval:     LLM 评估
LlamaIndex Evaluation: 内置
```

## 十四、技术栈推荐（2025）

### 14.1 极简栈（POC / 中小团队）

```
文档源:     Wiki + 飞书云文档
切分:       LangChain TextSplitter
Embedding:  bge-large-zh-v1.5（本地 GPU）
向量库:     pgvector（已有 PG）
LLM:        vLLM + Qwen3-32B-AWQ
框架:       LangChain / LlamaIndex
UI:         Streamlit / Chatbot UI
入口:       企业微信机器人

成本: 1 张 GPU + 现有 PG，5 万 / 年
```

### 14.2 生产栈（中型团队）

```
采集:       自研 Connector + 调度
切分:       LangChain + 自定义规则
Embedding:  bge-large-zh + TEI 服务
向量库:     Milvus / Qdrant
全文:       Elasticsearch
Rerank:     bge-reranker-large
LLM:        vLLM + Qwen3-72B（主）+ Qwen3-7B（路由小流量）
框架:       LangChain + Dify / 自研
UI:         Web + IDE 插件 + ChatBot
评估:       RAGAs
权限:       RBAC

成本: 4-8 张 GPU + 中等基础设施，30-80 万 / 年
```

### 14.3 开箱即用平台

| 平台 | 类型 | 国产 |
|:---|:---|:---:|
| **Dify** | LLMOps 全家桶 | ✅ |
| **FastGPT** | 知识库 + 工作流 | ✅ |
| **MaxKB** | 开源知识库 | ✅ |
| **AnythingLLM** | 个人 + 团队 | ❌ |
| **Quivr** | 第二大脑 | ❌ |
| **RAGFlow** | RAG 引擎 | ✅ |
| **LangFlow** | 可视化编排 | ❌ |
| **Coze** (扣子) | 字节 | ✅ |
| **GraphRAG** | 微软知识图谱 RAG | ❌ |

**中文场景强推**：Dify / FastGPT / RAGFlow / MaxKB。

## 十五、常见坑

| 坑 | 建议 |
|:---|:---|
| **文档质量差** | 先治理 Wiki，否则 GIGO |
| **没切分好** | 结构化切分 + 重叠 |
| **Embedding 选错** | 中文必用 bge / conan |
| **不做 Rerank** | 精度差很多 |
| **不做混合检索** | 召回低 |
| **不做引用源** | 出错没法追责 |
| **召回 = 答案** | 加 Rerank + LLM |
| **直接用通用 LLM 回答** | 必须 RAG 限制范围 |
| **没有反馈闭环** | 知识库会衰退 |
| **没有权限** | 敏感信息全员可见 |
| **chunk 太大** | LLM 找不到重点 |
| **chunk 太小** | 失去上下文 |
| **Embedding 服务慢** | 用 TEI / Infinity 加速 |
| **向量库选错** | 不要一上来就 Milvus，先 pgvector |
| **多源不去重** | URL / title 去重 |
| **没有时效性** | 旧文档要标记 + 降权 |
| **没有评估** | RAGAs 必跑 |
| **公网 LLM** | 数据合规风险 |

## 十六、最佳实践清单

```
内容治理:
☐ 文档标签 + 分类体系
☐ 文档归属（owner）
☐ 时效性管理（更新/归档）
☐ 质量审核机制
☐ PII / 密钥脱敏

技术架构:
☐ 多源采集
☐ 结构化切分
☐ 混合检索（向量 + BM25）
☐ Rerank 精排
☐ LLM 强制引用
☐ 流式输出
☐ RAGAs 评估

入口:
☐ ChatBot
☐ Web UI
☐ API
☐ 告警卡片集成
☐ IDE / 终端

闭环:
☐ 用户反馈（👍/👎/补充）
☐ 知识断层检测
☐ 文档新鲜度
☐ 月度运营报表

安全:
☐ RBAC 权限
☐ 全链路审计
☐ 本地化部署
☐ 提示词注入防护
```

## 十七、学习路径

```
入门（1 周）:
  1. 装 Dify / FastGPT
  2. 喂 100 篇 Wiki
  3. 体验问答

中级（1 个月）:
  4. 接 Confluence/Notion
  5. 切换 bge-large-zh
  6. 加 Rerank
  7. 接企业微信机器人

高级（3 个月）:
  8. 自定义切分策略
  9. 混合检索（向量 + BM25）
  10. RAGAs 评估
  11. RBAC 权限
  12. 反馈闭环

专家:
  13. Self-RAG / CRAG / GraphRAG
  14. Agent 化（多步 + 工具）
  15. Fine-tune Embedding/Rerank
  16. 自研知识库平台
```

## 十八、参考资料

```
论文:
  - "RAG: Retrieval-Augmented Generation" (Meta, 2020)
  - "HyDE: Hypothetical Document Embeddings" (2022)
  - "Self-RAG" (UW, 2023)
  - "CRAG: Corrective RAG" (2024)
  - "GraphRAG" (Microsoft, 2024)
  - "RAGAs: Automated Evaluation of RAG" (2023)

博客:
  - LangChain Blog
  - LlamaIndex Blog
  - 智源 BGE 系列
  - Dify Engineering Blog

开源:
  - Dify: https://github.com/langgenius/dify
  - FastGPT: https://github.com/labring/FastGPT
  - RAGFlow: https://github.com/infiniflow/ragflow
  - MaxKB: https://github.com/1Panel-dev/MaxKB
  - BGE: https://github.com/FlagOpen/FlagEmbedding
  - Milvus: https://github.com/milvus-io/milvus
  - LangChain: https://github.com/langchain-ai/langchain
  - RAGAs: https://github.com/explodinggradients/ragas
```

> 📖 **核心判断**：运维知识库是 AIOps 价值最被低估的方向——它不直接灭火，但**让所有人灭火更快**。**最大投入应该在"文档治理"而非"技术栈"**：再好的 RAG 也救不了一坨烂 Wiki。中文私有化场景的黄金组合是 **Dify/FastGPT + bge-large-zh + vLLM + Qwen3-32B + Milvus/pgvector**，落地 1 周内见效，3 个月内 ROI 明显。
