import re

from document_parser import Document


class LegalTextSplitter:

    ARTICLE_PATTERN = re.compile(
        r"第[一二三四五六七八九十百千万零〇两]+条"
    )

    def split_document(
        self,
        document: Document
    ) -> list[Document]:

        text = document.content

        matches = list(
            self.ARTICLE_PATTERN.finditer(text)
        )

        if not matches:
            return [document]

        chunks = []

        for i, match in enumerate(matches):

            start = match.start()

            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(text)

            content = text[start:end].strip()

            if not content:
                continue

            metadata = document.metadata.copy()

            metadata["article"] = match.group()

            chunks.append(
                Document(
                    content=content,
                    metadata=metadata
                )
            )

        return chunks

from document_parser import DocumentParser
from document_cleaner import DocumentCleaner
from legal_text_splitter import LegalTextSplitter


if __name__ == "__main__":

    parser = DocumentParser()
    cleaner = DocumentCleaner()
    splitter = LegalTextSplitter()

    documents = parser.parse(
        "../00_data/立法法.pdf"
    )

    all_chunks = []

    for document in documents:

        document.content = cleaner.clean(
            document.content
        )

        chunks = splitter.split_document(
            document
        )

        all_chunks.extend(chunks)

    print(
        "Chunk 数量：",
        len(all_chunks)
    )

    for chunk in all_chunks[:10]:

        print("=" * 70)

        print(chunk.metadata)

        print(chunk.content)