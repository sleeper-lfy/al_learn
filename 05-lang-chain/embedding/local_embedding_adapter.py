from langchain_core.embeddings import Embeddings


class LocalEmbeddingAdapter(Embeddings):

    def __init__(self, model):
        self.model = model

    def embed_documents(
        self,
        texts: list[str]
    ) -> list[list[float]]:

        return [
            self.model.embed(text)
            for text in texts
        ]

    def embed_query(
        self,
        text: str
    ) -> list[float]:

        return self.model.embed(text)