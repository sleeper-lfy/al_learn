import fitz


class PDFLoader:

    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        """
        读取 PDF 的所有页面。
        返回：
        [
            {
                "page": 1,
                "text": "第一页文本..."
            }
        ]
        """

        documents = []

        pdf = fitz.open(self.file_path)

        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text()

            documents.append({"page": page_number, "text": text})

        pdf.close()

        return documents


if __name__ == "__main__":

    loader = PDFLoader("../00_data/立法法.pdf")

    documents = loader.load()

    print(f"PDF 页数：{len(documents)}")
    f = open('../00_data/test.txt', 'w', encoding='utf-8')
    for document in documents:
        print("\n====================")
        print(f"Page: {document['page']}")
        print("====================")

        print(document["text"][:1000])
        f.write(str(document["text"]) + '\n')
