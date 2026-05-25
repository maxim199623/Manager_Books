import logging
import re
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

    def _load_cover(self, read_book) -> str | None:
        """Получаем постер """
        cover = None
        item = read_book.get_item_with_id("CoverImage")
        if item.get_type() == 1: # 1 - изображение
            content = item.get_content()
            if isinstance(content, bytes):
                cover = content
        return cover



    def _get_chapter(self, href, read_book):
        """Получение текста главы"""
        item = read_book.get_item_with_href(href)
        if item is None:
            print(f"Элемент с href '{href}' не найден.")
            return None
        html = item.get_body_content().decode("utf-8", errors="ignore")
        return html


    def _load_chapters(self, read_book) -> List[Chapter]:
        """Получаем список глав с названием и содержимым"""
        chapters = []
        #Получаем оглавление
        tocs = read_book.toc
        for toc in tocs:
            name_chapter = toc.title # название главы
            chapter_ = self._get_chapter(toc.href, read_book)
            chapters.append(Chapter(title=name_chapter, content=chapter_))
        return chapters

    def load(self, path: str | None = None, data:bytes = None) -> Book:
        if path is None:
            self._get_path(data=data)
            path = self.temp_file_path
        read_book , file =  self._load_book(path)
        title, author, description = self._load_metadata(read_book)
        cover = self._load_cover(read_book)
        chapters = self._load_chapters(read_book)
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
