from src.embedding.local_embedding import LocalEmbeddingModel

if __name__ == "__main__":
    model = LocalEmbeddingModel()
    texts = [
        "中华人民共和国的首都是北京。",
        "北京是中华人民共和国的首都。",
        "苹果是一种水果。"
    ]
    vectors = model.embed_documents(texts)
    print("Vector 数量:", len(vectors))
    print("Vector 维度:", len(vectors[0]))
    print("第一个 Vector:", vectors[0])
