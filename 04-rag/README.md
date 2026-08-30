# 04-rag · 自学笔记

> 2026-08-29 ｜ RAG 检索链路 跑通 ✅

## 目标

RAG（Retrieval-Augmented Generation）：让 Agent 能回答“知识库里有、但模型未必
知道”的问题。检索不是终点，**检索结果的最终用途是作为上下文喂给模型**。

本机语料：100 部经典电影（NFO 元数据 + 剧情简介），存 SQLite，向量库在 Chroma。

## 组织（沿用 03 的分层）

```text
04-rag/
├── entity/             # 数据模型：models.py（Document，score 可选）
├── ingestion/          # 数据接入：NfoParser, MoviesStore
│   ├── nfo_parser.py
│   └── movie_store.py
├── retrieval/          # 检索能力：向量化 / 向量库 / 关键词 / 混合检索
│   ├── embedder.py
│   ├── chroma_store.py
│   ├── bm25.py
│   └── search_movies.py
├── agent/              # 应用层：工具注册 + Agent 循环
│   ├── tools.py
│   └── agent.py
└── data/
    ├── movies.db       # SQLite 文档库
    └── chroma/         # Chroma 向量库
```

按功能域分包（package by feature，对应 Java 的包思维）：

```text
agent ──> retrieval ──> ingestion ──> entity
```

`agent`（应用）依赖 `retrieval`（检索服务），`retrieval` 依赖 `ingestion`（数据接入），
数据模型 `entity` 被所有人共享。命名规范：文件名用领域名词（不带 `_tool` 后缀），
类名与文件一一对应；入口 `../main.py` 自带 sys.path 引导，从仓库任意目录
`python 04-rag/main.py "问题"` 都能运行。

## RAG 核心链路

```text
文档入库 → 双路检索 → 融合 → 回表取详情 → 拼进工具结果 → LLM 总结回答
             ├─ 向量检索（语义）
             └─ BM25（关键词）
```

### 1. 向量检索：抓语义

`/api/embed` 用 nomic-embed-text-v1.5 把文本变成向量，Chroma 存 100 部电影的
向量，查询时按距离排序。实测：“类似星际穿越的宇宙科幻电影” top1 就是
《星际穿越》——这是关键词检索做不到的（查询里根本没有“星际穿越”这个词）。

### 2. BM25：抓关键词

SQLite FTS5 的 `bm25()` 评分。修复前它是坏的（见踩坑记录），修复后实测：

```text
BM25['肖申克'] -> 肖申克的救赎
BM25['穿越']   -> 星际穿越、回到未来、疯狂的麦克斯4
```

关键词精确命中，和向量语义互补。

### 3. RRF：按排名融合，而不是按分数

两路检索的分数量纲完全不同（余弦相似度 ≈ 0~1，bm25 是负分），不能直接相加。
RRF（Reciprocal Rank Fusion）只看排名：

```python
score[doc_id] += 1 / (k + rank)   # k=60
```

实测“类似星际穿越的宇宙科幻电影”融合后前 3 名：
《星际穿越》《蜘蛛侠：平行宇宙》《异形》——两路结果互相补强。

### 4. 回表 

RRF 出来的是 id，回 SQLite 取 `page_content` 详情。

## 实测：Agent 端到端

**场景 1：需要检索**

```text
[第 1 步] search_movies({'content': '类似星际穿越的科幻电影'})
[第 2 步] 推荐《异形》《星际穿越》……
          其他推荐如《少林足球》虽非科幻但类型匹配，但不符合用户需求。
```

模型基于工具返回回答，还主动排除了类型不符的结果——RAG 的价值在这体现：
模型的知识 + 检索到的事实，组合出可信答案。

**场景 2：闲聊（不需要检索）**

```text
[第 1 步] 模型直接回答：你好！今天天气不错，有什么想看的电影或电视剧推荐吗？
```

按 system 规则正确跳过工具，没有滥用检索。

## 踩坑记录

- **FTS5 默认分词器对中文“整串成词”**：`MATCH '星际穿越'` 能命中，
  但 `MATCH '星际'` 零命中——连续汉字被当成一个 token。
  修复：索引前用 jieba 预分词（`星际穿越` → `星际 穿越`），查询同样分词后
  `OR` 拼接，每个 token 加引号避免 FTS 保留字（`OR`/`AND`）被当运算符；
- **外部内容 FTS5 表不能 DELETE**：SQLite 3.53 上 `DELETE FROM movie_fts`
  报的是误导性的 `database disk image is malformed`，实际是操作不支持。
  干脆改用独立 FTS 表（不带 external content），DELETE 重建都正常；
- **`bm25.py` 的 `self.conn` 从未赋值**：原代码把连接赋给了局部变量，
  BM25 检索从头到尾没工作过，异常还被吞成空列表，属于“静默失败”；
- **中文 embedding 语义有限**：nomic-embed 对中文理解一般，实测“测试”检索
  返回《肖申克的救赎》这类语义不相关结果——向量检索不是万能的，
  关键词兜底（BM25）因此是必要的。

## 疑问 / 待探索

- [ ] rerank（CrossEncoder）在显存允许时的效果，和 RRF 的配合方式；
- [ ] 把 Chroma 距离和 BM25 分数归一化后加权融合，对比纯 RRF 的差异；
- [ ] 长文档的切分策略（按段落/固定窗口）对检索质量的影响；
- [ ] 更强的中文 embedding（bge-m3 等）和 nomic-embed 的对比；
- [ ] 查询改写：LLM 先把用户问题改写成适合检索的 query，再接双路检索；
- [ ] 知识库更新后的索引增量维护（当前每次启动全量重建 FTS）。
