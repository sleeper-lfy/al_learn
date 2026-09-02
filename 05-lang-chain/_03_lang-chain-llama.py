from langchain_core.documents import Document
from document.legal_article_splitter import LegalArticleSplitter
from langchain_community.document_loaders import PyPDFLoader
from embedding.local_embedding import LocalEmbeddingModel
from retrieval.retriever import Retriever
from vector_store.faiss_store import FAISSVectorStore
from retrieval.bm25_retriever import BM25Retriever
from retrieval.hybrid_retriever import HybridRetriever

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


if __name__ == "__main__":
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
    bm25_retriever = BM25Retriever(chunks)
    hybrid_retriever = HybridRetriever(vector_retriever=vector_retriever, bm25_retriever=bm25_retriever)
    all_results = []

    for case in TEST_CASES:
        # 查询向量相似度
        results = hybrid_retriever.retrieve(query = case["question"])

        all_results.append(results)

        print("=" * 70)

        print("Question:", case["question"])

        print("Expected:", case["expected_articles"])

        for i, result in enumerate(results[:20], start=1):
            article = result['document'].metadata['article']
            print(f"Top {i}:")
            print(f"score: {result['score']}")
            print("Metadata:", result['document'].metadata)
            print("Article:", article)
            print("Content:", result['document'].page_content)

        print("Recall@1:", recall_at_k(results, case["expected_articles"], 1))

        print("Recall@3:", recall_at_k(results, case["expected_articles"], 3))

        print("Recall@5:", recall_at_k(results, case["expected_articles"], 5))

        print("Recall@10:", recall_at_k(results, case["expected_articles"], 10))

        print("Recall@20:", recall_at_k(results, case["expected_articles"], 20))

        print("RR:", reciprocal_rank(results, case["expected_articles"]))
