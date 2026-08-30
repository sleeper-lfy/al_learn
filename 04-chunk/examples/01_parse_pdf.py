from src.document.document_parser import DocumentParser

if __name__ == "__main__":
    parser = DocumentParser()
    documents = parser.parse("../data/raw/中华人民共和国立法法.pdf")
    print(f"解析得到 {len(documents)} 页")
    for document in documents[:3]:
        print(document["metadata"])
        print(document["content"][:300])
        print("-" * 50)
