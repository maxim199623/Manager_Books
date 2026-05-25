import pytest

from core.epub.reader import EpubReader


class DummyBook:
    def __init__(self, metadata_map):
        self._metadata_map = metadata_map

    def get_metadata(self, namespace, key):
        return self._metadata_map.get((namespace, key), [])


def test_load_metadata_returns_safe_defaults_when_fields_missing():
    reader = EpubReader()
    book = DummyBook(
        {
            ("DC", "title"): [("Власть книжного червя", {})],
            ("DC", "creator"): [],
            ("DC", "description"): [],
        }
    )

    title, author, description = reader._load_metadata(book)

    assert title == ["Власть книжного червя"]
    assert author is None
    assert description == ""


def test_load_metadata_joins_multiple_description_fragments_as_plain_text():
    reader = EpubReader()
    book = DummyBook(
        {
            ("DC", "title"): [("Власть книжного червя", {})],
            ("DC", "creator"): [(" Казуки Мия ", {})],
            ("DC", "description"): [
                ("<div>Первая часть<br></div>", {}),
                ("Вторая часть", {}),
            ],
        }
    )

    title, author, description = reader._load_metadata(book)

    assert title == ["Власть книжного червя"]
    assert author == "Казуки Мия"
    assert description == "Первая часть\n\nВторая часть"


@pytest.mark.parametrize(
    "metadata_map",
    [
        {
            ("DC", "creator"): [("Автор", {})],
            ("DC", "description"): [],
        },
        {
            ("DC", "title"): [("   ", {})],
            ("DC", "creator"): [("Автор", {})],
            ("DC", "description"): [],
        },
    ],
)
def test_load_metadata_uses_safe_default_title_when_metadata_is_missing_or_blank(
    metadata_map,
):
    reader = EpubReader()
    book = DummyBook(metadata_map)

    title, author, description = reader._load_metadata(book)

    assert title == ["Без названия"]
    assert author == "Автор"
    assert description == ""


def test_load_metadata_keeps_inline_html_on_one_line():
    reader = EpubReader()
    book = DummyBook(
        {
            ("DC", "title"): [("Власть книжного червя", {})],
            ("DC", "creator"): [("Казуки Мия", {})],
            ("DC", "description"): [
                ("<p>Текст <strong>с жирным</strong> и <em>курсивом</em></p>", {}),
            ],
        }
    )

    title, author, description = reader._load_metadata(book)

    assert title == ["Власть книжного червя"]
    assert author == "Казуки Мия"
    assert description == "Текст с жирным и курсивом"
