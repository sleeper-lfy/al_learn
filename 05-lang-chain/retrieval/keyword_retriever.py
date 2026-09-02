from rank_bm25 import BM25Okapi
import jieba


class KeywordRetriever:

    def __init__(self, documents: list[dict]):
        self.documents = documents

        # BM25 需要 token 列表
        corpus = [self.tokenize(doc.page_content) for doc in documents]

        self.bm25 = BM25Okapi(corpus)

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """
        最简单的中文切词方案。

        第一版我们直接按照字符切分。
        """
        return list(jieba.cut(text))

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        query_tokens = self.tokenize(query)

        scores = self.bm25.get_scores(query_tokens)

        # 分数从高到低排序
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []

        for index in ranked_indices:
            results.append({"document": self.documents[index], "score": float(scores[index])})

        return results
