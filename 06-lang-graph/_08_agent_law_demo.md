# _08_agent_law_demo.py — LangGraph 法律查询 Agent（混合检索）

用一个本地小模型（qwen3:1.7b）+ 本地向量库（Chroma），实现"LLM 自主决定是否查法条 → 混合检索 → 引用条文回答"的完整 Agent 流程。

## 一、整体架构

```
                    User
                      │
                      ▼
                  LangGraph
                      │
                      ▼
                    LLM（qwen3:1.7b + bind_tools）
                      │
                判断需要查法律 ────普通问题────→ 直接回答 → END
                      │
                      ▼
                 Tool Call（search_law）
                      │
                      ▼
               hybrid_search
                  /       \
                 ▼         ▼
          Vector Search   BM25 Search
          （Chroma 持久化）（jieba + rank_bm25）
                 \           /
                  ▼         ▼
             Score Fusion（RRF）
                       │
                       ▼
                     Top K
                       │
                       ▼
              Tool Result 回给 LLM
                       │
                       ▼
                 最终回答（引用条文）
```

对应 LangGraph 的图结构非常简单，就是一个 **Agent 循环**：

```
START → agent ⇄ tools → END
```

- `agent` 节点：LLM 推理。输出里带 Tool Call 就去 `tools`，否则直接结束。
- `tools` 节点：`ToolNode` 执行 `search_law`，结果以 ToolMessage 追加进消息列表，再回到 `agent`。
- 循环持续到 LLM 给出不带 Tool Call 的最终回答为止。

## 二、技术栈

| 组件 | 选型 | 说明 |
|---|---|---|
| Agent 编排 | LangGraph（StateGraph + ToolNode） | 消息状态 `MessagesState`，条件边路由 |
| 对话模型 | Ollama `qwen3:1.7b`（temperature=0） | 通过 `langchain-ollama` 的 `ChatOllama` |
| 向量模型 | Ollama `nomic-embed-text-v1.5` | `OllamaEmbeddings`，768 维 |
| 向量库 | Chroma（`langchain-chroma`） | 持久化到 `data/chroma/` |
| 关键词检索 | `rank_bm25`（BM25Okapi）+ `jieba` 分词 | 中文必须先分词才能算 BM25 |
| 分数融合 | RRF（Reciprocal Rank Fusion） | 按排名融合，k=60 |
| 文档加载 | `PyPDFLoader`（langchain-community） | 仅首次运行使用 |

## 三、运行方式

```bash
# 1. Ollama 需已启动，且已拉取模型
ollama pull qwen3:1.7b
ollama pull nomic-embed-text-v1.5

# 2. 用项目根目录的 uv 虚拟环境运行（不是系统 python）
cd 06-lang-graph
../.venv/Scripts/python.exe _08_agent_law_demo.py
```

**首次运行**：解析 `data/立法法.pdf` → 按法条切分 → 向量化 → 写入 Chroma。
**再次运行**：直接从 Chroma 加载法条（打印"从 Chroma 加载 120 条法条"），跳过 PDF 解析和向量化，启动明显变快。

> 如果换了 PDF 或修改了切分逻辑，删掉 `data/chroma/` 目录重新构建。

## 四、实现要点（按代码顺序）

### 1. 按法条切分：只在"行首"切

```python
ARTICLE_PATTERN = re.compile(r"(?m)^(?=第[一二三四五六七八九十百千万零〇]+条)")
```

法律文本天然按"第X条"组织，一个法条 = 一个 Chunk，粒度正好适合问答。

**关键坑**：法条正文里会交叉引用其他法条（如"依照本法第八十一条的规定执行"）。如果正则不锚定行首，引用处也会被切开，导致：

1. 产生重复的法条编号（Chroma 要求 id 唯一，直接抛 `DuplicateIDError`）；
2. 真实法条的正文被截断，引用后面的半句话变成一条"假法条"。

实测：任意位置切分得到 126 段（含 6 个重复编号），行首切分得到恰好 120 条连续无重复的法条（第一条 ~ 第一百二十条）。另外切分后还要清理 PDF 提取产物：去除所有空白字符、去掉末尾粘连的页码数字。

### 2. Chroma 持久化：贵的东西只做一次

```python
vector_store = Chroma(collection_name="lifafa",
                      embedding_function=embedding_model,
                      persist_directory=str(CHROMA_DIR))

stored = vector_store.get(include=["documents", "metadatas"])
if stored["ids"]:
    # 已有数据：直接加载，不再解析 PDF
else:
    # 首次：切分 → add_documents(ids=法条号)
```

设计逻辑是**按成本决定持久化策略**：

- **向量化（贵）**：126 条法条 × 768 维，首次运行批量算好后写入 Chroma，之后永远复用；查询时只需向量化 query 一条。
- **BM25 索引（便宜）**：jieba 分词 + 统计，毫秒级，每次运行在内存里重建即可，不值得持久化。

写入时用**法条号作为文档 id**（"第六十三条"...），既保证唯一，又让后续流程能按法条号对齐两路检索结果。

### 3. 双路检索：互补而不是重复

**向量检索**（Chroma `similarity_search_with_score`）：负责语义。用户问"立法原则"能命中第五、六条，即使条文里没有"原则"两个字的原话。

**BM25 检索**：负责精确词。用户问"第六十三条"时，向量检索只排到第 4 名（语义上"第六十一条"也很像），BM25 直接锁定第一名。这是向量检索的天然短板——对具体编号、专名不敏感。

注意 **Chroma 默认返回 L2 距离，越小越相似**，和"分数越大越好"的直觉相反；BM25 分数则是越大越好。两路分数方向和量纲都不同。

### 4. RRF 融合：只看排名，不看分数

```python
score(d) = Σ 1 / (k + rank_i(d))     # k = 60
```

向量分数（距离）和 BM25 分数**不能直接相加**——量纲完全不同，直接加等于让某一路主导结果。RRF 的做法是只取每一路的**排名**：两路都排靠前的文档累加出高分。`k=60` 是业界常用值，作用是平滑第 1 名和第 10 名的贡献差距，避免单路第一名独大。

融合后取 Top 5 条法条，格式化成 `【第六十三条】原文...` 返回给 LLM。

### 5. Tool 定义与 Agent 循环

```python
@tool
def search_law(query: str) -> str:
    """查询《中华人民共和国立法法》的法律条文。用户询问立法法相关内容时调用。"""
```

LLM 能看到的只有**函数名、参数签名、docstring**，它据此决定：要不要调工具、传什么 query（注意 query 是 LLM 自己改写过的检索词，不是用户原话——实测"我国立法应当遵循什么原则"被改写成"中华人民共和国立法原则"）。

路由就一行：最后一条消息有 `tool_calls` 就去 `tools`，否则结束。

### 6. System Prompt：小模型必须"强制"才调工具

实测 qwen3:1.7b 对"立法法第六十三条是什么"会调工具，但对"立法应当遵循什么原则"这种它**自以为会**的问题，会跳过工具直接用记忆回答（还会编造不存在的条文内容）。普通强度的"必须先检索"提示词也压不住。

最终有效的写法是否定它的记忆：

```python
SYSTEM_PROMPT = (
    "你是法律条文查询助手。你自己的记忆不可靠、可能过时，"
    "禁止凭记忆回答任何法律内容。"
    "只要问题涉及法律（包括原则、条文、程序），"
    "必须先调用 search_law 工具检索条文，再依据检索结果回答。"
)
```

这是小模型 Agent 的通用经验：**工具调用意愿要靠 prompt 明确强制**，否则模型会在"自己会"和"查一下"之间随机摇摆。

### 7. qwen3 的 `<think>` 输出

qwen3 默认开启思考模式，回答里带 `<think>...</think>`。展示前用正则剥离：

```python
answer = re.sub(r"<think>.*?</think>", "", content, flags=re.S).strip()
```

## 五、效果示例

```
# User: 我国立法应当遵循什么原则？

---------- Vector Search (Chroma) ----------
1. 第六条  dist=0.3537
2. 第七十条  dist=0.3605
...
---------- BM25 Search ----------
1. 第五条  score=5.0139
2. 第八十七条  score=4.3464
...
---------- Score Fusion (RRF) → Top K ----------
1. 第六条  rrf=0.0313
2. 第一百一十九条  rrf=0.0306
3. 第一条  rrf=0.0301
...

最终回答（节选）：
1. 宪法至上原则（第五条）立法必须符合宪法的规定、原则和精神……
2. 民主集中制原则（第六条）立法应当坚持和发展全过程人民民主，尊重和保障人权……
```

第五条、第六条正是立法原则的真正出处，答案从"模型幻觉"变成了"引用检索结果"。

## 六、注意点清单（速查）

1. **法条交叉引用** → 切分正则必须 `(?m)^` 锚定行首，否则重复 id + 原文截断。
2. **Chroma id 必须唯一**，重复会抛 `DuplicateIDError`；用天然唯一的法条号当 id。
3. **两路分数量纲不同** → 用 RRF 按排名融合，绝不能直接加分数。
4. **Chroma 返回 L2 距离（越小越好）**，BM25 分数越大越好，比较时注意方向。
5. **小模型不主动调工具** → system prompt 里明确"禁止凭记忆回答、必须先检索"。
6. **qwen3 的 `<think>`** → 展示层剥离，但不影响 tool_calls 解析。
7. **PDF 提取产物** → 中文间多余空格、末尾页码，切分后要清洗。
8. **按成本持久化** → 向量入库（贵、一次），BM25 内存重建（便宜、每次）。
9. **环境** → 依赖装在项目根 `.venv`（uv 管理），系统 python 没有这些包；Ollama 服务和两个模型需预先就绪。
10. **换语料/改切分** → 删 `data/chroma/` 重新构建，否则旧索引会一直被复用。

## 七、可扩展方向

- **重排（Rerank）**：Top K 之后再过一遍 `bge-reranker-v2-m3`（05 章节已有实现），精度更高。
- **多工具路由**：加 `search_movie` 等工具，让 LLM 在多个工具间选择。
- **记忆与检查点**：接 `InMemorySaver` checkpointer + thread_id，实现多轮追问（06 章节前几课的内容）。
- **流式输出**：`graph.stream()` 逐节点打印，观察 Agent 循环的每一步。
