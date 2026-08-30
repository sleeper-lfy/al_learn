from _03_recursive_chunk import recursive_split


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


def split_text(text, chunk_size, overlap):
    """
    Recursive Chunking + Overlap
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")

    if overlap >= chunk_size:
        raise ValueError(
            "overlap 必须小于 chunk_size"
        )

    # 第一步：递归切割
    chunks = recursive_split(
        text=text,
        chunk_size=chunk_size
    )

    # 第二步：增加 overlap
    chunks = add_overlap(
        chunks=chunks,
        overlap=overlap
    )

    return chunks


if __name__ == "__main__":

    text = """
第一章：人工智能

人工智能是一门研究如何让机器表现出智能行为的技术。
它涉及机器学习、深度学习、自然语言处理等多个领域。

第二章：RAG

RAG 是一种检索增强生成技术，可以让大语言模型访问外部知识。
它通常包含文档加载、文档切割、Embedding、向量数据库和检索等步骤。

第三章：Agent

Agent 可以根据用户的问题选择工具，并通过多轮推理完成任务。
"""

    chunks = split_text(
        text=text,
        chunk_size=50,
        overlap=10
    )

    for i, chunk in enumerate(chunks, start=1):

        print(f"\n===== Chunk {i} =====")
        print(chunk)
        print(f"长度：{len(chunk)}")
