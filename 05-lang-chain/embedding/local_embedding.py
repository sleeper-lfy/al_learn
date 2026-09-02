import math
import requests

BATCH_SIZE = 64  # /api/embed 支持批量，一次请求多条文本


class LocalEmbeddingModel:
    """调用本地 Ollama 嵌入模型，把文本变成向量。"""
    dimension = 0

    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "nomic-embed-text-v1.5") -> None:
        self.url = f"{base_url}/api/embed"
        self.model = model_name
        self.dimension = len(self.embed("dimension test"))

    def embed(self, texts) -> list[float]:
        """单条文本返回一个向量，文本列表返回向量列表。"""
        response = requests.post(self.url, json={"model": self.model, "input": texts}, timeout=120)
        response.raise_for_status()
        embeddings = response.json()["embeddings"]
        return embeddings[0] if isinstance(texts, str) else embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        result: list[list[float]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            result.extend(self.embed(texts[i: i + BATCH_SIZE]))
        return result

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """余弦相似度：越接近 1 越相似。"""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        return dot / (norm1 * norm2) if norm1 and norm2 else 0.0
