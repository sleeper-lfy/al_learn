"""tools.py：工具注册表（RAG 版）。

与 03-tool-calling/tools.py 同构：schema + 校验 + 执行。
Agent 只依赖 TOOLS（有哪些工具）和 execute_tool（执行工具）。
"""

from retrieval.search_movies import MovieSearcher

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_movies",
            "description": (
                "影视检索。当用户询问电影、电视剧、演员、导演、类型、标签、剧情等"
                "影视信息时使用。content 填写用户真正想查询的自然语言条件，"
                "支持模糊描述，例如“类似星际穿越的宇宙科幻电影”。"
            ),
            "parameters": {
                "type": "object",
                "required": ["content"],
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "自然语言检索条件（标题/演员/导演/类型/剧情等）",
                    }
                },
            },
        },
    }
]

_movie_searcher: MovieSearcher | None = None


def _get_searcher() -> MovieSearcher:
    """惰性单例：检索链（embedding/chroma/bm25/db）只初始化一次。"""
    global _movie_searcher
    if _movie_searcher is None:
        _movie_searcher = MovieSearcher()
    return _movie_searcher


def execute_tool(name: str, arguments: dict) -> str:
    """执行工具：成功返回结果文本，参数问题返回错误文本，不抛异常。"""
    if name == "search_movies":
        query = arguments.get("content", "").strip()
        if not query:
            return "缺少参数 content，请提供要查询的影视信息"
        return _get_searcher().search(query)
    return f"未知工具：{name}"
