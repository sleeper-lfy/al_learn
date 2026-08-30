from document_parser import DocumentParser
from text_splitter import TextSplitter
from document_cleaner import DocumentCleaner

if __name__ == "__main__":

    parser = DocumentParser()
    cleaner = DocumentCleaner()

    documents = parser.parse("../00_data/立法法.pdf")

    print("原始 Document 数量：")
    print(len(documents))

    for document in documents:
        document.content = cleaner.clean(document.content)

    splitter = TextSplitter(chunk_size=500, chunk_overlap=50)

    chunks = splitter.split_documents(documents)

    print("Chunk 数量：")
    print(len(chunks))

    for i, chunk in enumerate(chunks[:5]):
        print("=" * 60)

        print("Chunk:", i)

        print("Metadata:")
        print(chunk.metadata)

        print("Content:")
        print(chunk.content)
