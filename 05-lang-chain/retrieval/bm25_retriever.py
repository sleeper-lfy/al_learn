from rank_bm25 import BM25Okapi


class BM25Retriever:

    def __init__(self, chunks):
        self.chunks = chunks

        # 获取所有文档文本
        documents = [chunk.page_content for chunk in chunks]

        # 简单中文切分
        tokenized_documents = [list(document) for document in documents]

        self.bm25 = BM25Okapi(tokenized_documents)

    def retrieve(self, query: str, top_k: int = 5):
        # Query 同样按字符切分
        tokenized_query = list(query)

        scores = self.bm25.get_scores(tokenized_query)

        # 按分数从高到低排序
        ranked_indexes = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []

        for index in ranked_indexes[:top_k]:
            results.append({"document": self.chunks[index], "score": float(scores[index])})

        return results
