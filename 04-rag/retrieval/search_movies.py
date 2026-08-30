"""search_movies.py：混合检索——向量 + BM25 + RRF 融合。

RAG 的核心认知：单一检索方式不够稳——
- 向量检索抓语义（“类似星际穿越的宇宙科幻”）；
- BM25 抓关键词（“诺兰 导演”）；
- RRF（Reciprocal Rank Fusion）按“排名”而不是“分数”融合两路结果，
  因为两路的分数量纲完全不同（余弦相似度 vs bm25 负分）。
"""

import json

import pathlib

from ingestion.movie_store import MoviesStore
from retrieval.bm25 import BM25Searcher
from retrieval.chroma_store import ChromaStore
from retrieval.embedder import Embedder


RRF_K = 60  # RRF 常数，控制融合时排名的权重
CONTENT_LIMIT = 300  # 每条结果 page_content 最多给模型多少字（控制上下文体量）
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
CHROMA_DIR = str(BASE_DIR / "data" / "chroma")

class MovieSearcher:
    """电影混合检索：向量召回 + BM25 召回 + RRF 融合 + 回表取详情。"""

    def __init__(self, persist_dir: str = CHROMA_DIR) -> None:
        self.embedder = Embedder()
        self.chroma = ChromaStore(persist_dir = persist_dir)
        self.bm25 = BM25Searcher()
        self.store = MoviesStore()

    def search(self, query: str, top_k: int = 3) -> str:
        """混合检索，返回模型可直接读的 JSON 字符串。"""
        # 1. 向量召回（语义）
        query_vector = self.embedder.embed(query)
        vector_hits = [
            {"id": int(doc_id), "score": distance}
            for doc_id, distance in self.chroma.query(query_vector)
        ]

        # 2. BM25 召回（关键词）：分词逻辑封装在 BM25Searcher 内部
        bm25_hits = [
            {"id": doc.id, "score": doc.score}
            for doc in self.bm25.search(query)
        ]

        # 3. RRF 融合，取前 top_k 个 id
        fused = self.rrf([bm25_hits, vector_hits])[:top_k]

        # 4. 回表取详情并截断：工具结果过大是 Agent 上下文膨胀的常见原因
        docs = []
        for doc_id, _score in fused:
            doc = self.store.select_by_id(doc_id)
            if doc:
                docs.append(
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "page_content": doc.page_content[:CONTENT_LIMIT],
                        "metadata": {
                            "year": doc.metadata.get("year"),
                            "genre": doc.metadata.get("genre"),
                        },
                    }
                )

        return json.dumps(
            {
                "data": docs,
                "remark": "id 是数据库内部编号不用展示；title 是片名；"
                "page_content 是详细信息；metadata 是元数据",
            },
            ensure_ascii=False,
        )

    @staticmethod
    def rrf(results_list: list[list[dict]], k: int = RRF_K) -> list[tuple[int, float]]:
        """Reciprocal Rank Fusion：按排名融合多路检索结果。"""
        scores: dict[int, float] = {}
        for results in results_list:
            for rank, result in enumerate(results, start=1):
                doc_id = result["id"]
                scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
        return sorted(scores.items(), key=lambda item: item[1], reverse=True)
