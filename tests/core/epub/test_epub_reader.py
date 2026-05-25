from html import unescape

import pytest

from core.epub.reader import EpubReader
from parametrize import books1,books2,books3


def _normalized_description(description: str) -> str:
    return unescape(description).rstrip()


@pytest.mark.parametrize(
    "path, title, author, description, file_format, cover, chapters",[
        (
                books1["path"],
                books1["title"],
                books1["author"],
                books1["description"],
                books1["file_format"],
                books1["cover"],
                1501,

    ),
        (
                books2["path"],
                books2["title"],
                books2["author"],
                books2["description"],
                books2["file_format"],
                books2["cover"],
                478,

        ),(
                books3["path"],
                books3["title"],
                books3["author"],
                books3["description"],
                books3["file_format"],
                books3["cover"],
                1753,

    ),
    ],
    ids=["Release that Witch", "Solo Leveling", "The Legendary Mechanic"]
)
def test_epub_reader_returns_book(
    path, title, author, description, file_format, cover, chapters
):
    reader = EpubReader()

    book = reader.load(path)

    assert book.title == title
    assert book.author == author
    assert book.description == _normalized_description(description)
    assert book.format == file_format
    assert type(book.cover) == bytes
    assert book.cover == cover
    assert type(book.file) == bytes
    assert len(book.chapters) == chapters
    assert book.chapters[0].title == "Постер"

    assert book.series is None
