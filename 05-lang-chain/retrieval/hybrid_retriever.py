class HybridRetriever:

    def __init__(self, vector_retriever, bak_retriever, rrf_k: int = 60):
        self.vector_retriever = vector_retriever
        self.bak_retriever = bak_retriever
        self.rrf_k = rrf_k

    def retrieve(self, query: str, top_k: int = 5, candidate_k: int = 20):

        # 1. Vector Search
        vector_results = self.vector_retriever.retrieve(query=query)

        # 2. BM25 Search
        bm25_results = self.bak_retriever.retrieve(query=query, top_k=candidate_k)

        # 3. RRF
        scores = {}
        documents = {}

        # Vector
        for rank, result in enumerate(vector_results, start=1):
            document = result["document"]

            key = self._get_document_key(document)

            documents[key] = document

            scores[key] = scores.get(key, 0.0)

            scores[key] += (1 / (self.rrf_k + rank))

        # BM25
        for rank, result in enumerate(bm25_results, start=1):
            document = result["document"]

            key = self._get_document_key(document)

            documents[key] = document

            scores[key] = scores.get(key, 0.0)

            scores[key] += (1 / (self.rrf_k + rank))

        # 4. 排序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # 5. 返回 Top K
        results = []

        for key, score in ranked[:top_k]:
            results.append({"document": documents[key], "score": score})

        return results

    def retrieve_key(self, query: str, top_k: int = 20, candidate_k: int = 20):

        vector_results = self.vector_retriever.retrieve(query=query)

        keyword_results = self.bak_retriever.retrieve(query=query, top_k=candidate_k)

        scores = {}
        documents = {}

        print("-----------vector_results--------------")
        # Vector Retrieval
        for rank, result in enumerate(vector_results, start=1):
            document = result["document"]
            article = result['document'].metadata["article"]
            documents[article] = document
            print(rank, result['document'].metadata, result["score"])
            scores[article] = scores.get(article, 0) + (1 / (60 + rank))

        print("-----------keyword_results--------------")
        # Keyword Retrieval
        for rank, result in enumerate(keyword_results, start=1):
            document = result["document"]
            article = result['document'].metadata["article"]
            documents[article] = document
            print(rank, result['document'].metadata, result["score"])
            scores[article] = scores.get(article, 0) + (1 / (60 + rank))

        # 按 RRF 分数排序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []

        for article, score in ranked[:top_k]:
            results.append({"document": documents[article], "score": score})

        return results

    @staticmethod
    def _get_document_key(document):

        metadata = document.metadata

        return (metadata.get("source"), metadata.get("article"))
