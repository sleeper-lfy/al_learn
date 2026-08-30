class Retriever:
    def __init__(self, embedding_model, vector_store, top_k: int = 5):
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(self, query: str) -> list[dict]:
        query_vector = self.embedding_model.embed(query)
        return self.vector_store.search(query_vector, self.top_k)
