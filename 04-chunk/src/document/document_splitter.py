class DocumentSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, documents: list[dict]) -> list[dict]:
        chunks = []
        for document in documents:
            text = document["content"]
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunk_text = text[start:end]
                if chunk_text.strip():
                    metadata = dict(document["metadata"])
                    metadata["chunk_index"] = len(chunks)
                    chunks.append({
                        "content": chunk_text.strip(),
                        "metadata": metadata
                    })
                if end >= len(text):
                    break
                start = end - self.chunk_overlap
        return chunks
