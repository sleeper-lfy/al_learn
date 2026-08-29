"""movie_store.py：电影文档存储——SQLite movies 表 + FTS5 分词索引。"""

import json
import os
import pathlib
import sqlite3

import jieba

from ..entity.models import Document
from ..ingestion.nfo_parser import NfoParser

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]  # 04-rag 根目录
DB_PATH = str(BASE_DIR / "data" / "movies.db")


class MoviesStore:
    """电影文档存储：movies 表 + movie_fts 全文索引。"""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._parser = NfoParser()
        self._init_tables()
        self._ensure_fts()

    def _init_tables(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nfo_path TEXT,
                title TEXT,
                year TEXT,
                page_content TEXT,
                metadata_json TEXT,
                file_mtime REAL
            )
            """
        )
        self.conn.commit()

    def _ensure_fts(self) -> None:
        """确保 movie_fts 可用：独立分词索引表，定义不对则重建。"""
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='movie_fts'"
        ).fetchone()
        sql = row["sql"] if row else ""
        if not ("search_text" in sql and "content=" not in sql):
            cursor.execute("DROP TABLE IF EXISTS movie_fts")
            cursor.execute(
                """
                CREATE VIRTUAL TABLE movie_fts USING fts5(title, search_text)
                """
            )
        self._rebuild_fts()
        self.conn.commit()

    def _rebuild_fts(self) -> None:
        """从 movies 表全量重建 FTS 索引。

        FTS5 默认分词器把连续中文当“一个整串 token”（'星际穿越'能查，
        '星际'查不到），所以索引前用 jieba 预分词，按词建索引。
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM movie_fts")
        rows = cursor.execute("SELECT id, title, page_content FROM movies").fetchall()
        cursor.executemany(
            "INSERT INTO movie_fts(rowid, title, search_text) VALUES (?, ?, ?)",
            [
                (row[0], self._segment(row[1]), self._segment(row[2]))
                for row in rows
            ],
        )
        self.conn.commit()

    @staticmethod
    def _segment(text: str) -> str:
        """jieba 分词，空格连接，供 FTS 索引使用。"""
        return " ".join(t for t in jieba.cut(text) if t.strip())

    # ---------------- 查询 ----------------

    def load_documents(self) -> list[Document]:
        """读取 movies 表全部文档。"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, page_content, metadata_json FROM movies")
        return [
            Document(
                id=row[0],
                title=row[1],
                page_content=row[2],
                metadata=json.loads(row[3]),
            )
            for row in cursor.fetchall()
        ]

    def select_by_id(self, doc_id: int) -> Document | None:
        """按 id 取单条文档。"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, title, page_content, metadata_json FROM movies WHERE id = ?",
            (doc_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Document(
            id=row[0],
            title=row[1],
            page_content=row[2],
            metadata=json.loads(row[3]),
        )

    # ---------------- NFO 目录同步 ----------------

    def sync_nfo_directory(self, directory: str) -> dict[str, int]:
        """增量同步目录下 .nfo 文件到 movies 表，同步后重建 FTS。"""
        cursor = self.conn.cursor()
        disk_files: dict[str, float] = {}
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(".nfo"):
                    full_path = os.path.join(root, file)
                    try:
                        disk_files[full_path] = os.path.getmtime(full_path)
                    except OSError:
                        continue

        cursor.execute("SELECT nfo_path, file_mtime FROM movies")
        db_files = {row[0]: row[1] for row in cursor.fetchall()}

        added = updated = deleted = 0
        for path, mtime in disk_files.items():
            if path not in db_files:
                try:
                    doc = self._parser.parse(path)
                    cursor.execute(
                        """
                        INSERT INTO movies (nfo_path, title, year, page_content, metadata_json, file_mtime)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            path,
                            doc.metadata["title"],
                            str(doc.metadata["year"]),
                            doc.page_content,
                            json.dumps(doc.metadata, ensure_ascii=False),
                            mtime,
                        ),
                    )
                    added += 1
                except Exception as exc:
                    print(f"  [错误] 解析新增文件失败 {path}: {exc}")
            elif mtime > db_files[path]:
                try:
                    doc = self._parser.parse(path)
                    cursor.execute(
                        """
                        UPDATE movies
                        SET title=?, year=?, page_content=?, metadata_json=?, file_mtime=?
                        WHERE nfo_path=?
                        """,
                        (
                            doc.metadata["title"],
                            str(doc.metadata["year"]),
                            doc.page_content,
                            json.dumps(doc.metadata, ensure_ascii=False),
                            mtime,
                            path,
                        ),
                    )
                    updated += 1
                except Exception as exc:
                    print(f"  [错误] 解析更新文件失败 {path}: {exc}")

        for path in db_files:
            if path not in disk_files:
                cursor.execute("DELETE FROM movies WHERE nfo_path=?", (path,))
                deleted += 1

        self.conn.commit()
        self._rebuild_fts()
        return {"added": added, "updated": updated, "deleted": deleted}
