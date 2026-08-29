"""embedder.py：向量化——Ollama /api/embed + 余弦相似度。"""

import math

import requests

EMBED_MODEL = "modelscope.cn/nomic-ai/nomic-embed-text-v1.5-GGUF"
BATCH_SIZE = 64  # /api/embed 支持批量，一次请求多条文本


class Embedder:
    """调用本地 Ollama 嵌入模型，把文本变成向量。"""

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.url = f"{base_url}/api/embed"
        self.model = EMBED_MODEL

    def embed(self, texts):
        """单条文本返回一个向量，文本列表返回向量列表。"""
        response = requests.post(
            self.url, json={"model": self.model, "input": texts}, timeout=120
        )
        response.raise_for_status()
        embeddings = response.json()["embeddings"]
        return embeddings[0] if isinstance(texts, str) else embeddings

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """分批批量嵌入，避免一次请求太多文本。"""
        result: list[list[float]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            result.extend(self.embed(texts[i : i + BATCH_SIZE]))
        return result

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """余弦相似度：越接近 1 越相似。"""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        return dot / (norm1 * norm2) if norm1 and norm2 else 0.0


if __name__ == "__main__":
    tool = Embedder()
    v1 = tool.embed("一部关于宇宙探索和时间的科幻电影")
    v2 = tool.embed("宇航员穿越虫洞探索遥远的宇宙")
    v3 = tool.embed("两个年轻人之间的爱情故事")
    print("科幻 vs 宇宙探索:", round(tool.cosine_similarity(v1, v2), 4))
    print("科幻 vs 爱情故事:", round(tool.cosine_similarity(v1, v3), 4))
