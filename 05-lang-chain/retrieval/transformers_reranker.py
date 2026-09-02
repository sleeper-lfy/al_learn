import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class TransformersReranker:

    def __init__(self, model_path: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)

        self.model.eval()

    def score(self, query: str, document: str) -> float:

        inputs = self.tokenizer(query, document, return_tensors="pt", truncation=True, max_length=512)

        with torch.no_grad():
            outputs = self.model(**inputs)
            score = torch.sigmoid(outputs.logits[0]).item()
        return score

    def rerank(self, query: str, results: list[dict], top_k: int = 5) -> list[dict]:

        if not results:
            return []
        documents = [result['document'].page_content for result in results]

        inputs = self.tokenizer([query] * len(documents), documents,
                                padding=True, truncation=True, max_length=512,
                                return_tensors="pt")

        with torch.no_grad():
            outputs = self.model(**inputs)

            scores = torch.sigmoid(outputs.logits).squeeze(-1)

        reranked = []

        for result, score in zip(results, scores):
            result = result.copy()

            result["rerank_score"] = score.item()

            reranked.append(result)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

        return reranked[:top_k]


