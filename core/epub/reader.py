import logging
from typing import List

from ebooklib import epub
from core.epub.models import Book, Chapter
from bs4 import BeautifulSoup

logger = logging.getLogger("app")

class EpubReader:
    """
    Читает EPUB и возвращает Book.
    """
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

    def _get_chapter(self, href, read_book):
        """Получение текста главы"""
        item = read_book.get_item_with_href(href)
        if item is None:
            print(f"Элемент с href '{href}' не найден.")
            return None
        content = item.get_content()
        soup = BeautifulSoup(content, "html.parser")
        text_chapter = []
        for element in soup.body.descendants: # Проходим по всем элементам внутри <body>
            if element.name:  # Если это HTML-тег
                text = element.get_text(strip=True) # Извлекаем текст внутри тега
                if text: # Игнорируем пустые строки
                    text_chapter.append(text)
                    #text_chapter.append((element.name, text))
        return text_chapter


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

    def load(self, path: str) -> Book:
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