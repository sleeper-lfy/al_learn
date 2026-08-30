from pathlib import Path
from pypdf import PdfReader

import uuid


class Document:

    def __init__(self, content: str, metadata: dict | None = None, document_id: str | None = None):
        self.content = content

        self.metadata = metadata or {}

        self.document_id = (document_id or str(uuid.uuid4()))


class DocumentParser:

    def parse(self, file_path: str) -> list[Document]:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = path.suffix.lower()

        if suffix == ".txt":
            return self._parse_txt(path)

        elif suffix == ".pdf":
            return self._parse_pdf(path)

        else:
            raise ValueError(f"暂不支持的文件类型: {suffix}")

    def _parse_txt(self, path: Path) -> list[Document]:

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        document = Document(content=content, metadata={"file_name": path.name, "file_type": ".txt"})

        return [document]

    def _parse_pdf(self, path: Path) -> list[Document]:

        reader = PdfReader(str(path))

        document_id = str(uuid.uuid4())

        documents = []

        for page_number, page in enumerate(reader.pages, start=1):
            content = page.extract_text() or ""

            document = Document(content=content, document_id=document_id,
                metadata={"source": path.name, "file_type": ".pdf", "page": page_number})

            documents.append(document)

        return documents


if __name__ == "__main__":

    parser = DocumentParser()

    documents = parser.parse("../00_data/立法法.pdf")

    print("PDF页数：", len(documents))

    for document in documents[:3]:
        print("=" * 50)

        print("Metadata:")
        print(document.metadata)

        print("Content:")
        print(document.content[:500])
