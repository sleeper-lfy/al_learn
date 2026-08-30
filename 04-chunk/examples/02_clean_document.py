from src.document.document_parser import DocumentParser
from src.document.document_cleaner import DocumentCleaner

if __name__ == "__main__":
    parser = DocumentParser()
    documents = parser.parse("../data/raw/中华人民共和国立法法.pdf")
    cleaner = DocumentCleaner()
    documents = cleaner.clean_documents(documents)
    print(f"清洗后剩余 {len(documents)} 页")
    print(documents[0]["content"][:500])
