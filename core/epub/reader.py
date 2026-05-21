import logging
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

        title = read_book.get_metadata("DC", "title")[0][0]
        title = [part.strip() for part in title.split("/")]

        author = read_book.get_metadata("DC", "creator")[0][0] \
                            if read_book.get_metadata("DC", "creator") \
                            else None

        description = read_book.get_metadata("DC", "description")[0][0]

        return title, author, description

    def _load_cover(self, read_book) -> str | None:
        """Получаем постер """
        cover = None
        item = read_book.get_item_with_id("CoverImage")
        if item.get_type() == 1: # 1 - изображение
            content = item.get_content()
            if isinstance(content, bytes):
                cover = content
        return cover

    def _normalize_epub_html(self, html: str) -> str:
        INLINE_TAGS = {"i", "em", "b", "strong", "span"}

        soup = BeautifulSoup(html, "html5lib")

        # EPUB часто тащит CR как отдельный мусор
        for node in soup.find_all(string=True):
            text = str(node).replace("\r", "")
            if text != str(node):
                node.replace_with(text)

        # Пробельные inline-обёртки превращаем в обычный текст
        for tag in list(soup.find_all(INLINE_TAGS)):
            if tag.attrs:
                continue
            if all(isinstance(c, NavigableString) for c in tag.contents):
                text = tag.get_text()
                if text and text.isspace():
                    tag.replace_with(NavigableString(text))

        # Сливаем соседние одинаковые inline-теги: <i>a</i><i> b</i> -> <i>a b</i>
        changed = True
        while changed:
            changed = False
            for tag in list(soup.find_all(INLINE_TAGS)):
                nxt = tag.next_sibling
                if isinstance(nxt, Tag) and nxt.name == tag.name and nxt.attrs == tag.attrs:
                    for child in list(nxt.contents):
                        tag.append(child.extract())
                    nxt.decompose()
                    changed = True

        body = soup.body or soup
        return "".join(str(x) for x in body.contents)

    def _get_chapter(self, href, read_book):
        """Получение текста главы"""
        item = read_book.get_item_with_href(href)
        if item is None:
            print(f"Элемент с href '{href}' не найден.")
            return None
        html = item.get_body_content().decode("utf-8", errors="ignore")
        text = self._normalize_epub_html(html)
        return text


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