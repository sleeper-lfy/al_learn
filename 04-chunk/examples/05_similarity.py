from src.embedding.local_embedding import LocalEmbeddingModel
from src.retrieval.similarity import cosine_similarity

if __name__ == "__main__":
    model = LocalEmbeddingModel()
    texts = [
        "中华人民共和国的首都是北京。",
        "北京是中华人民共和国的首都。",
        "苹果是一种水果。"
    ]
    vectors = model.embed_documents(texts)
    
    score_ab = cosine_similarity(vectors[0], vectors[1])
    score_ac = cosine_similarity(vectors[0], vectors[2])
    
    print("A-B:", score_ab)
    print("A-C:", score_ac)
