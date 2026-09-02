import re

from langchain_core.documents import Document


class LegalArticleSplitter:

    ARTICLE_PATTERN = re.compile(
        r"(?=第[一二三四五六七八九十百千万零〇]+条)"
    )

    def split_documents(
        self,
        documents: list[Document]
    ) -> list[Document]:

        full_text = "\n".join(
            document.page_content
            for document in documents
        )

        parts = self.ARTICLE_PATTERN.split(
            full_text
        )

        chunks = []

        for part in parts:

            part = part.strip()

            if not part.startswith("第"):
                continue

            match = re.match(
                r"(第[一二三四五六七八九十百千万零〇]+条)",
                part
            )

            if not match:
                continue

            article_number = match.group(1)

            chunks.append(
                Document(
                    page_content=part,
                    metadata={
                        "source": "中华人民共和国立法法.pdf",
                        "article": article_number
                    }
                )
            )

        return chunks