"""entity/models.py：RAG 链路共享的数据类。"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """一段可检索的文本（模拟 LangChain 的 Document 结构）。

    score 为检索评分（BM25 / 向量距离 / RRF 分数），未检索时为 None。
    """

    id: int
    title: str
    page_content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float | None = None
