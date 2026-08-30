from src.embedding.local_embedding import LocalEmbeddingModel
from src.vector_store.faiss_store import FAISSVectorStore

if __name__ == "__main__":
    model = LocalEmbeddingModel()
    documents = [
        {"content": "中华人民共和国的首都是北京。", "metadata": {"source": "test.txt", "page": 1}},
        {"content": "北京是中华人民共和国的首都。", "metadata": {"source": "test.txt", "page": 2}},
        {"content": "苹果是一种水果。", "metadata": {"source": "test.txt", "page": 3}}
    ]
    texts = [doc["content"] for doc in documents]
    vectors = model.embed_documents(texts)
    dimension = len(vectors[0])
    
    store = FAISSVectorStore(dimension)
    store.add(documents, vectors)
    
    query = "中国的首都是哪里？"
    query_vector = model.embed(query)
    results = store.search(query_vector, top_k=3)
    
    for result in results:
        print("score:", result["score"])
        print("document:", result["document"])
        print("-" * 50)
