from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from embedding.local_embedding import LocalEmbeddingModel
from embedding.local_embedding_adapter import LocalEmbeddingAdapter
from document.legal_article_splitter import LegalArticleSplitter
from langchain_community.document_loaders import PyPDFLoader
from embedding.local_embedding import LocalEmbeddingModel
from retrieval.retriever import Retriever
from vector_store.faiss_store import FAISSVectorStore

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


if __name__ == '__main__':
    docs = PyPDFLoader('data/中华人民共和国立法法.pdf').load()
    for doc in docs:
        documents.append(Document(page_content=doc.page_content, metadata=doc.metadata))

    # 1. Splitter
    # splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=500,
    #     chunk_overlap=50
    # )
    splitter = LegalArticleSplitter()
    chunks = splitter.split_documents(documents)

    print("Chunk 数量:", len(chunks))

    # 2. Embedding
    local_model = LocalEmbeddingModel()

    embedding = LocalEmbeddingAdapter(local_model)

    # 3. FAISS
    vector_store = FAISS.from_documents(documents=chunks, embedding=embedding)

    # 4. Retriever
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    # "全国人民代表大会有哪些立法权？"
    # 5. Retrieval
    for case_data in TEST_CASES:
        print("问题：" + case_data["question"])
        results = retriever.invoke(case_data["question"])
        print("recall_at_k:" + str(recall_at_k(results, case_data["expected_articles"])))
        for i, doc in enumerate(results):
            print()
            print("Top:", i + 1)
            print("Score 无法直接从当前 retriever 结果看到")
            print("Article:", doc.metadata.get("article"))
            print("Content:", doc.page_content[:500])