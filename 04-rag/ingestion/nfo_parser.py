"""nfo_parser.py：解析 Jellyfin 的 .nfo 文件（电影元数据 XML）为 Document。"""

import os
import xml.etree.ElementTree as ET

from entity.models import Document


class NfoParser:
    """纯解析器：.nfo 文件 -> Document，不接触数据库。"""

    def parse(self, file_path: str) -> Document:
        """解析一个 .nfo 文件。"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            root = ET.fromstring(content)
        except Exception as exc:
            raise ValueError(f"XML 解析失败: {exc}") from exc

        title = (root.findtext("title") or "未知电影").strip()
        year_text = (root.findtext("year") or "0").strip()
        year = int(year_text) if year_text.isdigit() else year_text

        directors = [elem.text.strip() for elem in root.findall("director") if elem.text]
        actors = [
            elem.findtext("name").strip()
            for elem in root.findall("actor")
            if elem.findtext("name")
        ]
        genres = [elem.text.strip() for elem in root.findall("genre") if elem.text]
        plot = (root.findtext("plot") or "暂无剧情简介").strip()

        page_content = f"""电影：《{title}》
导演：{'、'.join(directors) if directors else '未知'}
主演：{'、'.join(actors[:5]) if actors else '未知'}{'...' if len(actors) > 5 else ''}
类型：{'、'.join(genres) if genres else '未知'}
剧情简介：
{plot}
"""
        metadata = {
            "title": title,
            "year": year,
            "director": directors,
            "genre": genres,
            "source": "jellyfin",
            "nfo_path": os.path.abspath(file_path),
        }
        return Document(id=0, title=title, page_content=page_content, metadata=metadata)
