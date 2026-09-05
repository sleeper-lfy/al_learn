from langchain_core.documents import Document
from document.legal_article_splitter import LegalArticleSplitter
from langchain_community.document_loaders import PyPDFLoader
from embedding.local_embedding import LocalEmbeddingModel
from retrieval.retriever import Retriever
from vector_store.faiss_store import FAISSVectorStore
from retrieval.transformers_reranker import TransformersReranker
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.keyword_retriever import KeywordRetriever


documents = []

TEST_CASES = [{"question": "全国人民代表大会有哪些立法权？", "expected_articles": ["第十条"]},
              {"question": "法律解释权属于谁？", "expected_articles": ["第四十八条"]},
              {"question": "立法应当遵循哪些原则？",
               "expected_articles": ["第五条", "第六条", "第七条", "第八条", "第九条"]}]


def recall_at_k(results, expected_articles, k):
    # retrieved_articles = {doc.metadata.get("article") for doc['document'] in results[:k]}
    retrieved_articles = []
    for result in results[:k]:
        retrieved_articles.append(result['document'].metadata['article'])
    matched = [article for article in expected_articles if article in retrieved_articles]

    return len(matched) / len(expected_articles)


def reciprocal_rank(results, expected_articles):
    for rank, doc in enumerate(results, start=1):
        article = doc['document'].metadata['article']

        if article in expected_articles:
            return 1 / rank

    return 0.0

def hybrid_search(query):
    reranker = TransformersReranker("E:/AI/models/bge-reranker-v2-m3")
    # test()
    # 读取PDF
    docs = PyPDFLoader('data/中华人民共和国立法法.pdf').load()
    for doc in docs:
        documents.append(Document(page_content=doc.page_content, metadata=doc.metadata))
    # 切割文档
    splitter = LegalArticleSplitter()
    chunks = splitter.split_documents(documents)
    embedding_model = LocalEmbeddingModel()
    # 向量化
    vector_store = FAISSVectorStore(dimension=len(embedding_model.embed(chunks[0].page_content)))
    vector_store.add_documents(documents=chunks, embedding_model=embedding_model)
    vector_retriever = Retriever(embedding_model=embedding_model, vector_store=vector_store, top_k=20)

    keyword_retriever = KeywordRetriever(chunks)
    hybrid = HybridRetriever(
        vector_retriever=vector_retriever,
        bak_retriever=keyword_retriever
    )

    results = hybrid.retrieve_key(
        query="法律解释权属于谁？",
        top_k=20,
        candidate_k=20
    )
    print("========== Retriever ==========")
    for i, result in enumerate(results, 1):
        print(i, result['document'].metadata, result["score"], result['document'].page_content)
    return

if __name__ == "__main__":
    hybrid_search("法律解释权属于谁？")


