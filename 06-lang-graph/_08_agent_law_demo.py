import re
import warnings
from pathlib import Path
import jieba
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from rank_bm25 import BM25Okapi

warnings.filterwarnings("ignore")

PDF_PATH = Path(__file__).parent / "data" / "立法法.pdf"
CHROMA_DIR = Path(__file__).parent / "data" / "chroma"

# ============================================================
# 1. LLM
# ============================================================

llm = ChatOllama(model="qwen3:1.7b", temperature=0)

# ============================================================
# 2. 文档切分（仅首次运行使用）
#
# 《立法法》的正文结构是“第X条”，所以按法条切分，
# 每个法条就是一个 Chunk，天然适合法律问答。
#
# 注意：只在“行首”切分。法条正文里也会引用其他法条
# （如“依照第八十一条的规定”），任意位置切分会把引用
# 误当成新法条，产生重复编号并截断原文。
# ============================================================

ARTICLE_PATTERN = re.compile(r"(?m)^(?=第[一二三四五六七八九十百千万零〇]+条)")


def load_law_articles() -> list[dict]:
    from langchain_community.document_loaders import PyPDFLoader

    docs = PyPDFLoader(str(PDF_PATH)).load()
    full_text = "\n".join(doc.page_content for doc in docs)

    articles = []
    for part in ARTICLE_PATTERN.split(full_text):
        part = part.strip()
        match = re.match(r"(第[一二三四五六七八九十百千万零〇]+条)", part)
        if not match:
            continue
        # 去掉 PDF 提取产生的空白和页码
        content = re.sub(r"\s+", "", part)
        content = re.sub(r"\d+$", "", content)
        articles.append({"article": match.group(1), "content": content})
    return articles


# ============================================================
# 3. Chroma 向量库
#
# 首次运行：PDF → 法条切分 → 向量化 → 写入 Chroma（持久化）
# 后续运行：直接从 Chroma 读取法条，查询时只向量化 query
# ============================================================

embedding_model = OllamaEmbeddings(model="nomic-embed-text-v1.5")

vector_store = Chroma(collection_name="lifafa", embedding_function=embedding_model, persist_directory=str(CHROMA_DIR), )

stored = vector_store.get(include=["documents", "metadatas"])

if stored["ids"]:
    ARTICLES = [{"article": meta["article"], "content": doc} for meta, doc in
        zip(stored["metadatas"], stored["documents"])]
    print(f"从 Chroma 加载 {len(ARTICLES)} 条法条（跳过 PDF 解析和向量化）")
else:
    print("首次运行：正在解析 PDF 并写入 Chroma ...")
    ARTICLES = load_law_articles()
    vector_store.add_documents(
        documents=[Document(page_content=f"{a['article']}{a['content']}", metadata={"article": a["article"]}, ) for a in
            ARTICLES], ids=[a["article"] for a in ARTICLES], )
    print(f"已写入 {len(ARTICLES)} 条法条到 Chroma")

# article → 原文，方便后面按法条号取内容
ARTICLE_MAP = {a["article"]: a["content"] for a in ARTICLES}


# ============================================================
# 4. Vector Search
#
# 语义检索：直接查 Chroma。
# 注意 Chroma 默认返回 L2 距离，越小越相似。
# ============================================================


def vector_search(query: str, top_n: int = 10) -> list[dict]:
    results = vector_store.similarity_search_with_score(query, k=top_n)
    return [{"article": doc.metadata["article"], "score": float(dist)} for doc, dist in results]


# ============================================================
# 5. BM25 Search
#
# 关键词检索：对精确词匹配（如“第六十三条”）特别有效，
# 正好补足向量检索在具体编号上的短板。
# ============================================================

CORPUS_TOKENS = [list(jieba.cut(f"{a['article']}{a['content']}")) for a in ARTICLES]
BM25_ARTICLES = [a["article"] for a in ARTICLES]
BM25 = BM25Okapi(CORPUS_TOKENS)


def bm25_search(query: str, top_n: int = 10) -> list[dict]:
    scores = BM25.get_scores(list(jieba.cut(query)))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]
    return [{"article": BM25_ARTICLES[i], "score": float(scores[i])} for i in ranked if scores[i] > 0]


# ============================================================
# 6. hybrid_search：Score Fusion + Top K
#
# 向量分数和 BM25 分数量纲不同，不能直接相加，
# 所以用 RRF（Reciprocal Rank Fusion）按“排名”融合：
#
#     score = Σ 1 / (k + rank)
#
# k = 60 是常用值，用来平滑第一名和后面名次的差距。
# ============================================================

RRF_K = 60


def hybrid_search(query: str, top_k: int = 5, candidate_n: int = 10) -> list[dict]:
    # 两路检索
    vector_results = vector_search(query, candidate_n)
    bm25_results = bm25_search(query, candidate_n)

    print("\n---------- Vector Search (Chroma) ----------")
    for rank, r in enumerate(vector_results[:5], 1):
        print(f"{rank}. {r['article']}  dist={r['score']:.4f}")

    print("\n---------- BM25 Search ----------")
    for rank, r in enumerate(bm25_results[:5], 1):
        print(f"{rank}. {r['article']}  score={r['score']:.4f}")

    # RRF 融合：按各自排名累加 1 / (k + rank)
    scores: dict[str, float] = {}
    for results in (vector_results, bm25_results):
        for rank, r in enumerate(results, 1):
            article = r["article"]
            scores[article] = scores.get(article, 0.0) + 1 / (RRF_K + rank)

    # Top K
    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    print("\n---------- Score Fusion (RRF) → Top K ----------")
    fused = []
    for rank, (article, score) in enumerate(top, 1):
        print(f"{rank}. {article}  rrf={score:.4f}")
        fused.append({"article": article, "content": ARTICLE_MAP[article]})
    return fused


# ============================================================
# 7. Tool：search_law
#
# LLM 看到的只有这个函数签名和 docstring，
# 判断“需要查法律”后发起 Tool Call。
# ============================================================


@tool
def search_law(query: str, top_k: int = 5) -> str:
    """
    查询中华人民共和国现行有效的法律法规和法律条文。
    参数：
    query: 要查询的法律问题或关键词。
    top_k: 返回的相关法条数量。
    适用于：
    1. 查询具体法律条文
    2. 查询法律条款内容
    3. 查询法律规定
    """
    print("\n========== Tool Call ==========")
    print("query:", query)
    print("top_k:", top_k)
    if top_k < 3:
        raise ValueError("top_k 必须大于等于 3")
    results = hybrid_search(query, top_k=top_k)
    return "\n\n".join(f"【{r['article']}】{r['content']}" for r in results)


# ============================================================
# 8. Agent Node
#
# System Prompt 约束：涉及立法法的问题必须先调用 search_law，
# 小模型才不会凭自己的（过时/幻觉）知识直接回答。
#
# LLM 绑定工具后自己决定：
#   - 需要查法律 → 发起 Tool Call
#   - 普通问题   → 直接回答
# ============================================================

SYSTEM_PROMPT = ("你是法律条文查询助手。你自己的记忆不可靠、可能过时，"
                 "禁止凭记忆回答任何法律内容。"
                 "只要问题涉及法律（包括原则、条文、程序），"
                 "必须先调用 search_law 工具检索条文，再依据检索结果回答。")

llm_with_tools = llm.bind_tools([search_law])


def agent(state: MessagesState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def route(state: MessagesState):
    if state["messages"][-1].tool_calls:
        return "tools"
    return "end"


# ============================================================
# 9. Graph
#
# START → agent ⇄ tools → END
#
# agent 有 Tool Call 就去 tools，执行完回到 agent，
# 直到 agent 给出最终回答。
# ============================================================

builder = StateGraph(MessagesState)

builder.add_node("agent", agent)
#handle_tool_errors=True 让Agent能处理错误
builder.add_node("tools", ToolNode([search_law], handle_tool_errors=True))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", route, {"tools": "tools", "end": END})
builder.add_edge("tools", "agent")

graph = builder.compile()


# ============================================================
# 10. 运行
# ============================================================

def ask(question: str):
    print("\n" + "#" * 60)
    print(f"# User: {question}")
    print("#" * 60)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}, ]
    #最大迭代次数recursion_limit
    result = graph.invoke({"messages": messages}, config={"recursion_limit": 10})

    # qwen3 会输出 <think> 思考过程，展示时去掉
    answer = re.sub(r"<think>.*?</think>", "", result["messages"][-1].content, flags=re.S).strip()

    print("\n========== 最终回答 ==========")
    print(answer)


if __name__ == "__main__":
    # 法律问题：LLM 判断需要查法律 → Tool Call → 混合检索 → 最终回答
    while True:
        ask("我国立法应当遵循什么原则？")

    # 普通问题：LLM 判断不需要查法律 → 直接回答
    # ask("你好，用一句话介绍一下你自己")
