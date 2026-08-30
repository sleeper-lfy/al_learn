def recursive_split(text, chunk_size, separators=None):
    """
    递归切割文本

    优先级：
    段落 -> 句子 -> 字符
    """
    if separators is None:
        separators = ["\n\n",  # 段落
            "\n",  # 换行
            "。",  # 中文句号
            "！",  # 中文感叹号
            "？",  # 中文问号
            ".",  # 英文句号
            "!",  # 英文感叹号
            "?",  # 英文问号
            "",  # 最后按照字符切
        ]

    # 已经足够短
    if len(text) <= chunk_size:
        return [text]

    # 没有分隔符了，只能强制按照字符切
    if not separators:
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    separator = separators[0]
    remaining_separators = separators[1:]

    # 最后一层：按照字符切
    if separator == "":
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    # 按当前分隔符切割
    parts = text.split(separator)

    chunks = []
    current_chunk = ""

    for part in parts:

        # split 后把分隔符补回来
        if current_chunk:
            candidate = current_chunk + separator + part
        else:
            candidate = part

        # 当前组合没有超过限制
        if len(candidate) <= chunk_size:
            current_chunk = candidate
            continue

        # 当前组合超过限制
        if current_chunk:
            # 保存已经形成的 Chunk
            chunks.append(current_chunk)

        # 当前 part 自己就超过 chunk_size
        if len(part) > chunk_size:

            # 继续使用更细的分隔符递归切割
            sub_chunks = recursive_split(part, chunk_size, remaining_separators)

            chunks.extend(sub_chunks)

            current_chunk = ""

        else:
            current_chunk = part

    # 最后一个 Chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


if __name__ == "__main__":

    text = """第一章：人工智能

人工智能是一门研究如何让机器表现出智能行为的技术。它涉及机器学习、深度学习、自然语言处理等多个领域。

第二章：RAG

RAG 是一种检索增强生成技术，可以让大语言模型访问外部知识。它通常包含文档加载、文档切割、Embedding、向量数据库和检索等步骤。

第三章：Agent

Agent 可以根据用户的问题选择工具，并通过多轮推理完成任务。"""

    chunks = recursive_split(text=text, chunk_size=20)

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n===== Chunk {i} =====")
        print(chunk)
        print(f"长度：{len(chunk)}")
