"""chroma_store.py：向量库——Chroma 持久化写入与相似度查询。"""

import pathlib

import chromadb

from entity.models import Document
from ingestion.movie_store import MoviesStore
from retrieval.embedder import Embedder

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]  # 04-rag 根目录
CHROMA_DIR = str(BASE_DIR / "data" / "chroma")
COLLECTION_NAME = "movies"


class ChromaStore:
    """电影文档的向量库：批量写入向量 + 按向量查询相似文档。"""

    def __init__(self, persist_dir: str = CHROMA_DIR) -> None:
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)

    @staticmethod
    def _clean_metadata(metadata: dict) -> dict:
        """清洗元数据：移除空列表值（Chroma 不接受空 list）。"""
        return {
            k: v
            for k, v in metadata.items()
            if not (isinstance(v, list) and len(v) == 0)
        }

    def upsert_documents(self, docs: list[Document], vectors: list[list[float]]) -> None:
        """批量写入向量，按 id 幂等：重复运行不会因为撞 id 报错。"""
        self.collection.upsert(
            ids=[str(doc.id) for doc in docs],
            documents=[doc.page_content for doc in docs],
            embeddings=vectors,
            metadatas=[self._clean_metadata(doc.metadata) for doc in docs],
        )

    def query(self, query_vector: list[float], n_results: int = 10) -> list[tuple[str, float]]:
        """返回 [(doc_id, distance), ...]，按距离升序（越近越相似）。"""
        res = self.collection.query(query_embeddings=[query_vector], n_results=n_results)
        return list(zip(res["ids"][0], res["distances"][0]))

    def count(self) -> int:
        return self.collection.count()


def build_index() -> int:
    """全量重建向量库：读取全部文档 -> 批量嵌入 -> upsert。返回写入条数。"""
    store = MoviesStore()
    embedder = Embedder()
    docs = store.load_documents()
    vectors = embedder.embed_batch([doc.page_content for doc in docs])
    ChromaStore().upsert_documents(docs, vectors)
    return len(docs)
