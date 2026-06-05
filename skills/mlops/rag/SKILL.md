---
name: rag
description: RAG (检索增强生成) 系统设计、优化与落地 — 文档解析、向量检索、召回排序、混合搜索、评估调优。when the user asks about building/optimizing/implementing a RAG system, or questions about retrieval-augmented generation.
triggers:
  - RAG 优化
  - 检索增强生成
  - 向量数据库
  - 知识库问答
  - RAG evaluation
  - 召回率提升
category: mlops
tags: [rag, vector-search, embeddings, retrieval, llm, knowledge-base]
version: 1.0
created: 2026-06-05
---

# RAG 实战技能

## 核心架构

```
用户 query
  └─→ 检索层（Embedding + Vector DB）
        ├─ 稀疏检索（BM25 /.keyword）
        └─ 稠密检索（Embedding / dense）
  └─→ 融合层（RRF / score weighted merge）
  └─→ 重排序层（Cross-Encoder / Cohere Rerank）
  └─→ 生成层（LLM + context）
```

---

## 1. 文档解析（Chunking）

**原则：** chunk 大小影响召回精度，需平衡完整性与匹配率。

| 策略 | chunk_size | 适用场景 |
|---|---|---|
| 固定窗口 | 512 tokens | 通用场景，快速简单 |
| 语义分割 | 句子/段落 | 保留语义完整性的文档 |
| 层次分割 | 标题层级 → 块 | PDF/网页，保留层级结构 |
| Late-chunking | 重叠 + pooling | 需要保留上下文时 |

**关键参数：**
- `chunk_overlap`：通常 10-20% overlap，防止边界截断关键信息
- `separator`：保持句子完整性，避免在句子中间截断
- 中文分词：使用 `jieba` / `ltp` 做语义分词，不要纯字符级切分

**代码示例（Python）：**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", "。", "！", "？", " "],
    chunk_size=500,
    chunk_overlap=50,
)
docs = splitter.split_text(text)
```

---

## 2. Embedding 模型选型

**主流选择：**

| 模型 | 维度 | 中文支持 | 备注 |
|---|---|---|---|
| `text-embedding-3-small` (OpenAI) | 1536 | ✅ | 成本低，效果好 |
| `bge-large-zh-v1.5` (BAAI) | 1024 | ✅✅ | 中文最优开源 |
| `m3e-base` (Moka) | 768 | ✅ | 中文，支持微调 |
| `e5-mistral-7b` | 1024 | ⚠️ | 英文为主，高精度 |

**选型建议：**
- 通用场景 → `bge-large-zh-v1.5`（中文开源首选）
- 对话/搜索 → 用 `e5` 系列（需要加 query prefix）
- 需要微调 → `m3e-base`

---

## 3. 向量数据库

| DB | 场景 | 特点 |
|---|---|---|
| `Qdrant` | 生产级 | Rust，高性能，支持混合搜索 |
| `Milvus` | 超大规模 | 分布式，适合亿级向量 |
| `Chroma` | 轻量/原型 | 简单易用，持久化 |
| `Pinecone` | 云托管 | 无基础设施负担 |
| `FAISS` | 单机/小规模 | Facebook，CPU 可用 |

**选型建议：**
- < 100 万向量 → `Chroma` 或 `Qdrant`
- > 100 万向量 → `Milvus` / `Qdrant` 集群
- 云原生/无维护 → `Pinecone`

---

## 4. 检索策略

### 4.1 混合搜索（Hybrid Search）

稀疏 + 稠密融合，显著提升召回质量：

```python
# 稀疏：BM25 分数
bm25_score = bm25(query, docs)

# 稠密：向量相似度
vec_score = cosine(embedding(query), embedding(doc))

# 融合：RRF (Reciprocal Rank Fusion)
def rrf(docs, k=60):
    scores = {}
    for doc in docs:
        for rank, d in enumerate(sorted_docs[doc]):
            scores[d] = scores.get(d, 0) + 1 / (k + rank + 1)
    return scores
```

### 4.2 查询扩展（Query Expansion）

- **HyDE（Hypothetical Document Embeddings）**：让 LLM 生成假设答案，用假设答案去检索
- **多查询检索**：用 LLM 生成多个同义 query，并行检索后合并

### 4.3 元数据过滤

在检索时加过滤器，减少搜索空间：
```
向量检索（top_k=50） + metadata_filter={category: "金融", year: 2024}
→ 再重排序
```

---

## 5. 重排序（Reranking）

检索结果用 Cross-Encoder 再排序，精度大幅提升：

| 模型 | 用途 |
|---|---|
| `bge-reranker-large` (BAAI) | 中文重排首选 |
| `Cohere Rerank 3` | 云端 API，多语言 |
| `cross-encoder/ms-marco` | 通用英文 |

**Pipeline：**
```
向量检索 top_k=100 → Cross-Encoder rerank → top_k=10 → LLM 生成
```

---

## 6. 评估方法

### 6.1 RAG 评估指标

| 指标 | 含义 |
|---|---|
| **Context Precision** | 检索到的 context 有多少与 query 相关 |
| **Context Recall** | 正确答案是否出现在检索到的 context 中 |
| **Faithfulness** | LLM 生成内容是否忠实于 context（无幻觉） |
| **Answer Relevancy** | 答案对 query 的相关程度 |

**工具：** `RAGAS` / `Trulens` / `LangSmith`

### 6.2 快速评估流程

```python
# 用 LLM-as-Judge 做快速评估
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

evaluate(dataset, metrics=[faithfulness, answer_relevancy])
```

### 6.3 失败模式诊断

| 失败模式 | 原因 | 解决方案 |
|---|---|---|
| 召回内容无关 | embedding 模型不匹配中文 | 换 `bge-large-zh-v1.5` |
| 答案不完整 | chunk 太小，上下文中断 | 增大 chunk 或用 parent-doc retrieval |
| 幻觉严重 | context 不够/模型太弱 | 加入 citation + 换更强模型 |
| 检索为空 | query 与文档不匹配 | 加 HyDE / 多查询扩展 |

---

## 7. 高级技巧

### 7.1 Parent-Document Retrieval

大块检索，小块引用：

```
大块（parent）：整篇文章 → 检索用
小块（child）：段落 → 进入 LLM context
```

检索到大块后，取出对应的子块送入 LLM。

### 7.2 知识图谱增强（KG-RAG）

```
实体识别 → 知识图谱 → 子图检索 → 与向量检索结果融合
```

适合需要多跳推理的问答场景（如"某公司CEO之前在哪家公司工作？"）。

### 7.3 自动向量索引更新

生产环境用增量更新而非全量重建：

```python
# 增量写入 Qdrant
client.upsert(
    collection_name="docs",
    points=[{"id": doc_id, "vector": emb, "payload": metadata}]
)
```

---

## 8. 常见陷阱

1. **不要用 MD5/id 之类无意义的 chunk ID** → 用内容哈希 + 序号，方便排查
2. **中文字符 embedding 不要用纯英文模型** → 效果差 30%+
3. **top_k 不是越大越好** → 过多干扰 context，增加幻觉风险，通常 5-15
4. **不要忽略检索延迟** → embedding 推理延迟可能比向量检索高 10x
5. **chunk 不是越小越好** → 太碎破坏语义完整性，需要语义分块

---

## 验证步骤

1. 写 20 条测试 query（含简单/多跳/模糊/对抗）
2. 手动标注期望召回的 context
3. 运行评估，对比修改前后指标
4. 检查生成答案是否在 context 内（Faithfulness）