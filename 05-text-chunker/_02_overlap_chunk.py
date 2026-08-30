import re


def split_sentences(text):
    """
    将文本按照中文/英文常见标点切分成句子
    """
    sentences = re.split(r'(?<=[。！？.!?])', text)

    # 去掉空字符串和首尾空格
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    return sentences


def split_text(text, chunk_size, overlap):
    """
    按句子进行 Chunk 切割，并保留 overlap 个句子的重叠

    chunk_size: 一个 Chunk 最大字符数
    overlap: Chunk 之间重叠的句子数量
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")

    if overlap < 0:
        raise ValueError("overlap 不能小于 0")

    sentences = split_sentences(text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:

        # 当前 Chunk 加入这个句子之后的长度
        new_length = current_length + len(sentence)

        # 如果加入后超过 chunk_size
        if current_chunk and new_length > chunk_size:
            # 保存当前 Chunk
            chunks.append("".join(current_chunk))

            # 保留最后 overlap 个句子
            current_chunk = current_chunk[-overlap:] if overlap > 0 else []

            current_length = sum(len(s) for s in current_chunk)

        # 加入当前句子
        current_chunk.append(sentence)
        current_length += len(sentence)

    # 保存最后一个 Chunk
    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks


def add_overlap(chunks, overlap):
    """
    给已经切好的 Chunk 添加字符级 Overlap
    """

    if overlap < 0:
        raise ValueError("overlap 不能小于 0")

    result = []

    for i, chunk in enumerate(chunks):

        # 第一个 Chunk 不需要前置 overlap
        if i == 0:
            result.append(chunk)
            continue

        previous_chunk = chunks[i - 1]

        # 取前一个 Chunk 最后 overlap 个字符
        prefix = previous_chunk[-overlap:] if overlap > 0 else ""

        result.append(prefix + chunk)

    return result


# 最简单的Overlap 重叠切割
def simple_split_text(text, chunk_size, overlap):
    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    if overlap < 0:
        raise ValueError("overlap 不能小于 0")

    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]
        chunks.append(chunk)

        start = end - overlap

    return chunks


if __name__ == '__main__':
    test_text = ("人工智能正在快速发展，RAG作为一种常见技术，能让大模型访问外部知识从而减少幻觉。"
                 "因此学习RAG是掌握人工智能的重要一环。而Chunking（文本分块）则是构建RAG系统离线索引流程中的关键第一步。")
    chunks = simple_split_text(text=test_text, chunk_size=26, overlap=12)
    print("最简单的Overlap 重叠切割：")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}: {chunk}")

    chunks = split_text(text=test_text, chunk_size=30, overlap=2)
    print("根据分割符进行Overlap 重叠切割")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}: {chunk}")
