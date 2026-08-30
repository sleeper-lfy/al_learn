from src.document.document_parser import DocumentParser
from src.document.document_cleaner import DocumentCleaner
from src.document.document_splitter import DocumentSplitter
from src.embedding.local_embedding import LocalEmbeddingModel
from src.vector_store.faiss_store import FAISSVectorStore
from src.retrieval.retriever import Retriever

if __name__ == "__main__":
    parser = DocumentParser()
    documents = parser.parse("../data/raw/中华人民共和国立法法.pdf")
    print("Parser:", len(documents), "documents")
    
    cleaner = DocumentCleaner()
    documents = cleaner.clean_documents(documents)
    print("Cleaner:", len(documents), "documents")
    
    splitter = DocumentSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split(documents)
    print("Splitter:", len(chunks), "chunks")
    
    embedding_model = LocalEmbeddingModel()
    texts = [chunk["content"] for chunk in chunks]
    vectors = embedding_model.embed_documents(texts)
    dimension = len(vectors[0])
    print("Embedding dimension:", dimension)
    
    vector_store = FAISSVectorStore(dimension)
    vector_store.add(chunks, vectors)
    print("FAISS vectors:", vector_store.index.ntotal)
    
    retriever = Retriever(
        embedding_model=embedding_model,
        vector_store=vector_store,
        top_k=5
    )
    
    query = "全国人民代表大会有哪些立法权？"
    results = retriever.retrieve(query)
    
    print()
    print("=" * 60)
    print("Query:", query)
    print("=" * 60)
    
    for index, result in enumerate(results, start=1):
        document = result["document"]
        print(f"\nTop {index}")
        print("Score:", result["score"])
        print("Content:", document["content"])
        print("Metadata:", document["metadata"])
