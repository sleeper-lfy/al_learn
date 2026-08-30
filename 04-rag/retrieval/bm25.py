"""bm25.py：关键词检索——SQLite FTS5 的 BM25 评分（jieba 分词适配中文）。"""

import logging
import pathlib
import sqlite3

import jieba

from entity.models import Document

logger = logging.getLogger(__name__)

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]  # 04-rag 根目录
DB_PATH = str(BASE_DIR / "data" / "movies.db")


class BM25Searcher:
    """基于 SQLite FTS5 的 BM25 关键词检索。"""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def search(self, query: str, limit: int = 10) -> list[Document]:
        """FTS5 检索：查询先 jieba 分词再 OR 拼接，按 bm25 分数排序返回前 limit 条。

        索引和查询必须用同一套分词逻辑（见 movie_store.py 的 _segment）。
        """
        tokens = [t for t in jieba.cut(query) if t.strip()]
        # 每个 token 加引号：既避免 FTS 保留字（OR/AND/NOT）被当成运算符，也支持含空格的词
        match_expr = " OR ".join(f'"{t}"' for t in tokens)
        if not match_expr:
            return []
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                SELECT m.id, m.title, m.page_content, bm25(movie_fts) AS score
                FROM movie_fts
                JOIN movies m ON m.id = movie_fts.rowid
                WHERE movie_fts MATCH ?
                ORDER BY bm25(movie_fts)
                LIMIT ?
                """,
                (match_expr, limit),
            )
            return [
                Document(
                    id=row[0],
                    title=row[1],
                    page_content=row[2],
                    score=row[3],
                )
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as exc:
            logger.warning("BM25 检索失败：%s", exc)
            return []
