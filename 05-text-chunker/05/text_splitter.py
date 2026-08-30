from document_parser import Document


class TextSplitter:

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, separators: list[str] | None = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.separators = separators or ["\n\n", "\n", "。", "！", "？", "；", "，", "、", " "]

    def split_text(self, text: str) -> list[str]:

        if len(text) <= self.chunk_size:
            return [text]

        return self._split_text_recursive(text, self.separators)

    def _split_text_recursive(self, text: str, separators: list[str]) -> list[str]:

        # 已经足够小
        if len(text) <= self.chunk_size:
            return [text]

        # 没有分隔符了，只能硬切
        if not separators:
            return self._hard_split(text)

        separator = separators[0]

        # 当前分隔符不存在
        if separator not in text:
            return self._split_text_recursive(text, separators[1:])

        # 按当前分隔符切
        parts = text.split(separator)

        chunks = []
        current = ""

        for part in parts:

            if not part:
                continue

            if len(current) + len(part) <= self.chunk_size:

                if current:
                    current += separator

                current += part

            else:

                if current:
                    chunks.append(current)

                # 当前 part 自己就超过 chunk_size
                if len(part) > self.chunk_size:

                    sub_chunks = self._split_text_recursive(part, separators[1:])

                    chunks.extend(sub_chunks)

                    current = ""

                else:
                    current = part

        if current:
            chunks.append(current)

        return self._add_overlap(chunks)

    def _hard_split(self, text: str) -> list[str]:

        chunks = []

        start = 0

        while start < len(text):
            end = start + self.chunk_size

            chunks.append(text[start:end])

            start = end - self.chunk_overlap

        return chunks

    def _add_overlap(self, chunks: list[str]) -> list[str]:

        if self.chunk_overlap <= 0:
            return chunks

        result = []

        for i, chunk in enumerate(chunks):

            if i == 0:
                result.append(chunk)
                continue

            previous = result[-1]

            overlap = previous[-self.chunk_overlap:]

            result.append(overlap + chunk)

        return result

    def split_documents(self, documents):

        chunks = []

        for document in documents:

            texts = self.split_text(document.content)

            for text in texts:
                chunks.append(Document(content=text, metadata=document.metadata.copy()))

        return chunks
