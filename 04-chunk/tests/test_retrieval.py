from document.document_parser import DocumentParser
from document.document_cleaner import DocumentCleaner
from document.document_splitter import DocumentSplitter

from embedding.local_embedding import LocalEmbeddingModel
from retrieval.retriever import Retriever
from vector_store.faiss_store import FAISSVectorStore

TEST_CASES = [
        {"question": "全国人民代表大会有哪些立法权？", "expected_keywords": ["全国人民代表大会", "制定", "修改", "基本法律"]},

        {"question": "法律解释权属于谁？", "expected_keywords": ["法律解释权", "全国人民代表大会常务委员会"]},

        {"question": "立法应当遵循哪些原则？", "expected_keywords": ["立法", "宪法", "法治原则"]}
    ]


def check_keywords(results: list[dict], keywords: list[str]):
    content = "\n".join(result['document']["content"] for result in results)

    return [keyword for keyword in keywords if keyword in content]


if __name__ == "__main__":

    # ==================================
    # 1. Parser
    # ==================================

    parser = DocumentParser()

    documents = parser.parse("../data/raw/中华人民共和国立法法.pdf")

    # ==================================
    # 2. Cleaner
    # ==================================

    cleaner = DocumentCleaner()

    documents = cleaner.clean_documents(documents)

    # ==================================
    # 3. Splitter
    # ==================================

    splitter = DocumentSplitter(chunk_size=500, chunk_overlap=50)

    chunks = splitter.split(documents)

    print("Chunk 数量:", len(chunks))

    # ==================================
    # 4. Embedding Model
    # ==================================

    embedding_model = LocalEmbeddingModel()

    # ==================================
    # 5. Embedding Chunks
    # ==================================

    texts = [chunk["content"] for chunk in chunks]

    vectors = embedding_model.embed_documents(texts)

    # ==================================
    # 6. 创建 FAISS
    # ==================================

    dimension = len(vectors[0])

    vector_store = FAISSVectorStore(dimension=dimension)

    # ==================================
    # 7. 添加知识库
    # ==================================

    vector_store.add(chunks, vectors)

    print("FAISS Vector 数量:", vector_store.index.ntotal)

    # ==================================
    # 8. 创建 Retriever
    # ==================================

    retriever = Retriever(embedding_model=embedding_model, vector_store=vector_store, top_k=5)

    # ==================================
    # 9. 开始测试
    # ==================================

    for case in TEST_CASES:

        results = retriever.retrieve(case["question"])

        matched = check_keywords(results, case["expected_keywords"])

        recall = (len(matched) / len(case["expected_keywords"]))

        print()
        print("=" * 70)

        print("Question:", case["question"])

        print("Matched:", matched)

        print("Recall:", recall)

        print("=" * 70)

        for index, result in enumerate(results, start=1):
            item = result['document']

            print(f"\nTop {index}")

            print("Score:", result["score"])

            print("Content:", item["content"])

            print("Metadata:", item["metadata"])
