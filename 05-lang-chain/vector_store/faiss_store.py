import faiss
import numpy as np
from langchain_core.documents import Document


class FAISSVectorStore:
    def __init__(self, dimension: int):
        self.index = faiss.IndexFlatIP(dimension)
        self.documents = []

    def add(self, documents: list[dict], vectors: list[list[float]]):
        if len(documents) != len(vectors):
            raise ValueError("documents 和 vectors 数量必须一致")
        if not vectors:
            return

        vectors = np.asarray(vectors, dtype="float32")
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.documents.extend(documents)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        if self.index.ntotal == 0:
            return []

        top_k = min(top_k, self.index.ntotal)
        query_vector = np.asarray([query_vector], dtype="float32")
        faiss.normalize_L2(query_vector)

        scores, indices = self.index.search(query_vector, top_k)
        results = []

        for score, index in zip(scores[0], indices[0]):
            if index == -1:
                continue
            results.append({"document": self.documents[index], "score": float(score), "index": int(index)})
        return results

    def add_documents(self, documents: list[Document], embedding_model) -> None:

        if not documents:
            return

        # 1. 提取 Chunk 文本
        texts = [document.page_content for document in documents]

        # 2. 批量 Embedding
        embeddings = embedding_model.embed_documents(texts)

        # 3. 转成 numpy
        vectors = np.asarray(embeddings, dtype=np.float32)

        # 4. 检查维度
        if vectors.shape[1] != self.index.d:
            raise ValueError(f"Embedding dimension mismatch: "
                             f"expected={self.index.d}, "
                             f"actual={vectors.shape[1]}")

        # 5. 添加到 FAISS
        self.index.add(vectors)

        # 6. 保存 Document
        self.documents.extend(documents)
