import logging
import re
from pathlib import Path
from typing import List

from ebooklib import epub
from core.epub.models import Book, Chapter
from bs4 import BeautifulSoup, NavigableString, Tag

import tempfile

logger = logging.getLogger("app")

class EpubReader:
    """
    Читает EPUB и возвращает Book.
    """
    def __init__(self):
        self.temp_file_path = None

    def _load_book(self,  path: str):
        """Загружаем файл книги"""
        ic()
        ic(path)
        try:
            read_book = epub.read_epub(path)
        except FileNotFoundError:
            logger.exception(f"Файл книги не найден /n {path}")
        with open(path, "rb") as f:
            file = f.read()
        file = file
        return read_book , file

    def _load_metadata(self, read_book):
        """Получаем данные о книги"""

        titles = self._meta_values(read_book, "DC", "title")
        raw_title = titles[0].strip() if titles else ""
        title = self._split_title(raw_title)

        authors = self._meta_values(read_book, "DC", "creator")
        author = authors[0].strip() if authors else None
        if not author:
            author = None

        description_parts = [
            self._html_to_text(value)
            for value in self._meta_values(read_book, "DC", "description")
        ]
        description_parts = [part for part in description_parts if part]
        description = "\n\n".join(description_parts)

        return title, author, description

    def _meta_values(self, read_book, namespace: str, key: str) -> list[str]:
        return [
            value
            for value, _attrs in read_book.get_metadata(namespace, key)
            if value and value.strip()
        ]

    def _html_to_text(self, value: str | None) -> str:
        if not value:
            return ""
        soup = BeautifulSoup(value, "html5lib")
        root = soup.body or soup
        parts: list[str] = []
        block_tags = {
            "article",
            "blockquote",
            "div",
            "footer",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "header",
            "li",
            "ol",
            "p",
            "section",
            "table",
            "tbody",
            "td",
            "tfoot",
            "th",
            "thead",
            "tr",
            "ul",
        }

        def walk(node):
            if isinstance(node, NavigableString):
                parts.append(str(node))
                return

            if not isinstance(node, Tag):
                return

            name = (node.name or "").lower()
            if name == "br":
                parts.append("\n")
                return

            is_block = name in block_tags
            if is_block and parts and not parts[-1].endswith("\n"):
                parts.append("\n")

            for child in node.children:
                walk(child)

            if is_block:
                parts.append("\n")

        for child in root.children:
            walk(child)

        text = "".join(parts)
        text = re.sub(r"[ \t\r\f\v]*\n[ \t\r\f\v]*", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    def _split_title(self, title: str) -> list[str]:
        normalized = title.replace(" / ", "/")
        parts = [part.strip() for part in normalized.split("/") if part.strip()]
        return parts or ["Без названия"]

    def _load_default_cover(self) -> bytes:
        cover_path = Path(__file__).resolve().parents[2] / "assets" / "cover.png"
        return cover_path.read_bytes()

    def _is_image_item(self, item) -> bool:
        if item is None:
            return False

        get_type = getattr(item, "get_type", None)
        if callable(get_type):
            try:
                return get_type() == 1
            except TypeError:
                pass

        media_type = getattr(item, "media_type", "") or ""
        return media_type.startswith("image/")

    def _load_cover(self, read_book) -> bytes | None:
        """Получаем постер """

        def content_from_item(item):
            if not self._is_image_item(item):
                return None
            content = item.get_content()
            if isinstance(content, bytes):
                return content
            return None

        get_item_with_id = getattr(read_book, "get_item_with_id", None)
        meta_entries = read_book.get_metadata("OPF", "meta")
        for _value, attrs in meta_entries:
            attrs = attrs or {}
            if attrs.get("name") == "cover" and attrs.get("content") and callable(
                get_item_with_id
            ):
                content = content_from_item(get_item_with_id(attrs["content"]))
                if content is not None:
                    return content

        if callable(get_item_with_id):
            content = content_from_item(get_item_with_id("CoverImage"))
            if content is not None:
                return content

        get_items = getattr(read_book, "get_items", None)
        items = list(get_items()) if callable(get_items) else []

        for item in items:
            properties = set(getattr(item, "properties", []) or [])
            if "cover-image" in properties:
                content = content_from_item(item)
                if content is not None:
                    return content

        for item in items:
            item_id = (getattr(item, "id", "") or "").lower()
            media_type = getattr(item, "media_type", "") or ""
            if item_id.startswith("cover") and media_type.startswith("image/"):
                content = content_from_item(item)
                if content is not None:
                    return content

        for item in items:
            media_type = getattr(item, "media_type", "") or ""
            if media_type.startswith("image/"):
                content = content_from_item(item)
                if content is not None:
                    return content

        return self._load_default_cover()



    def _get_chapter(self, href, read_book):
        """Получение текста главы"""
        clean_href = self._clean_href(href)
        item = read_book.get_item_with_href(clean_href)
        if item is None:
            return None
        return item.get_body_content().decode("utf-8", errors="ignore")

    def _clean_href(self, href: str | None) -> str:
        return (href or "").split("#", 1)[0]

    def _iter_toc_entries(self, entries):
        for entry in entries:
            if isinstance(entry, tuple) and len(entry) == 2:
                section, children = entry
                href = getattr(section, "href", None)
                title = getattr(section, "title", None)
                if href:
                    yield title, href
                yield from self._iter_toc_entries(children)
                continue

            href = getattr(entry, "href", None)
            title = getattr(entry, "title", None)
            if href:
                yield title, href

    def _is_auxiliary_spine_item(self, item, item_id: str) -> bool:
        file_name = getattr(item, "file_name", item_id) or item_id
        stem = Path(file_name).stem.lower()
        normalized = re.sub(r"[^a-z0-9]+", "", stem)
        return normalized in {"nav", "toc", "contents", "cover", "coverpage", "titlepage"}

    def _load_spine_chapters(self, read_book, seen_hrefs: set[str] | None = None) -> List[Chapter]:
        chapters = []
        seen_hrefs = seen_hrefs or set()
        for item_id, linear in getattr(read_book, "spine", []):
            if str(linear).lower() == "no":
                continue
            item = read_book.get_item_with_id(item_id)
            if item is None or not hasattr(item, "get_body_content"):
                continue
            if self._is_auxiliary_spine_item(item, item_id):
                continue
            file_name = self._clean_href(getattr(item, "file_name", item_id))
            if file_name in seen_hrefs:
                continue
            html = item.get_body_content().decode("utf-8", errors="ignore")
            title = Path(file_name).stem
            seen_hrefs.add(file_name)
            chapters.append(Chapter(title=title, content=html))
        return chapters

    def _load_chapters(self, read_book, cover: bytes | None = None) -> List[Chapter]:
        """Получаем список глав с названием и содержимым"""
        chapters = []
        seen_hrefs = set()
        for title, href in self._iter_toc_entries(getattr(read_book, "toc", [])):
            clean_href = self._clean_href(href)
            if clean_href in seen_hrefs:
                continue
            chapter_html = self._get_chapter(href, read_book)
            if chapter_html is None:
                continue
            seen_hrefs.add(clean_href)
            chapters.append(
                Chapter(title=title or Path(clean_href).stem, content=chapter_html)
            )

        chapters.extend(self._load_spine_chapters(read_book, seen_hrefs=seen_hrefs))

        if cover is not None and (not chapters or chapters[0].title != "Постер"):
            chapters.insert(0, Chapter(title="Постер", content=""))
        return chapters

    def load(self, path: str | None = None, data:bytes = None) -> Book:
        if path is None:
            self._get_path(data=data)
            path = self.temp_file_path
        read_book , file =  self._load_book(path)
        title, author, description = self._load_metadata(read_book)
        cover = self._load_cover(read_book)
        chapters = self._load_chapters(read_book, cover=cover)
        return Book(cover=cover,
                    title=title,
                    author=author,
                    description=description,
                    chapters=chapters,
                    file=file)

    def _get_path(self, data):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            f.write(data)
            self.temp_file_path = f.name
            ic(self.temp_file_path)
