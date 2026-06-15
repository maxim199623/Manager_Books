from html import unescape

import pytest

from core.epub.reader import EpubReader
from parametrize import books1, books2, books3


BOOKS = [books1, books2, books3]
BOOK_IDS = ["Release that Witch", "Solo Leveling", "The Legendary Mechanic"]


def _normalized_description(description: str) -> str:
    return unescape(description).rstrip()


@pytest.mark.parametrize(
    "book_data",
    BOOKS,
    ids=BOOK_IDS,
)
def test_epub_reader_returns_book_metadata(book_data):
    reader = EpubReader()

    book = reader.load(book_data["path"])

    assert book.title == book_data["title"]
    assert book.author == book_data["author"]
    assert book.description == _normalized_description(book_data["description"])
    assert book.format == book_data["file_format"]
    assert isinstance(book.cover, bytes)
    assert book.cover == book_data["cover"]
    assert isinstance(book.file, bytes)
    assert len(book.chapters) == book_data["chapters"]
    assert book.chapters
    assert book.series is None


@pytest.mark.parametrize(
    "book_data",
    BOOKS,
    ids=BOOK_IDS,
)
def test_epub_reader_preserves_chapter_order(book_data):
    reader = EpubReader()

    book = reader.load(book_data["path"])

    for index, expected_title in book_data["chapter_checkpoints"]:
        assert book.chapters[index].title == expected_title
