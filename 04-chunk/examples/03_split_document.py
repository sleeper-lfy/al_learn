from src.document.document_parser import DocumentParser
from src.document.document_cleaner import DocumentCleaner
from src.document.document_splitter import DocumentSplitter

if __name__ == "__main__":
    parser = DocumentParser()
    cleaner = DocumentCleaner()
    documents = parser.parse("../data/raw/中华人民共和国立法法.pdf")
    documents = cleaner.clean_documents(documents)
    
    splitter = DocumentSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split(documents)
    print(f"最终得到 {len(chunks)} 个 Chunk")
    
    for chunk in chunks[:5]:
        print(chunk["metadata"])
        print(chunk["content"])
        print("-" * 50)
