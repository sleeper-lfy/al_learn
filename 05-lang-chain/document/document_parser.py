from pathlib import Path
from pypdf import PdfReader

class DocumentParser:
    def parse(self, file_path: str) -> list[dict]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        reader = PdfReader(str(path))
        documents = []
        
        for page_number, page in enumerate(reader.pages, start=1):
            content = page.extract_text()
            if not content:
                continue
            
            documents.append({
                "content": content,
                "metadata": {
                    "source": path.name,
                    "page": page_number
                }
            })
        return documents
