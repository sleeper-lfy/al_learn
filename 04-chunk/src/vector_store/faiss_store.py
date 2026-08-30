import faiss
import numpy as np

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
            results.append({
                "document": self.documents[index],
                "score": float(score),
                "index": int(index)
            })
        return results
