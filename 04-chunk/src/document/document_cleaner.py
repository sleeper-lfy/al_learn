import re

class DocumentCleaner:
    def clean(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("\u3000", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def clean_documents(self, documents: list[dict]) -> list[dict]:
        results = []
        for document in documents:
            content = self.clean(document["content"])
            if not content:
                continue
            results.append({
                "content": content,
                "metadata": document["metadata"]
            })
        return results
