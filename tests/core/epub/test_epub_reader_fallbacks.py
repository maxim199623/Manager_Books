import pytest
from pathlib import Path

from core.epub.reader import EpubReader


OPF_NS = "http://www.idpf.org/2007/opf"


class DummyBook:
    def __init__(self, metadata_map):
        self._metadata_map = metadata_map

    def get_metadata(self, namespace, key):
        return self._metadata_map.get((namespace, key), [])


class DummyItem:
    def __init__(
        self,
        item_id,
        content,
        media_type="image/jpeg",
        properties=None,
        item_type=None,
    ):
        self.id = item_id
        self._content = content
        self.media_type = media_type
        self.properties = properties or []
        if item_type is not None:
            self._item_type = item_type

            def get_type():
                return self._item_type

            self.get_type = get_type

    def get_content(self):
        return self._content


class DummyHtmlItem:
    def __init__(self, file_name, html):
        self.file_name = file_name
        self._html = html

    def get_body_content(self):
        return self._html.encode("utf-8")


class DummyLink:
    def __init__(self, title, href):
        self.title = title
        self.href = href


class DummyBookWithCover(DummyBook):
    def __init__(self, metadata_map, metadata, by_id, items):
        combined_metadata_map = dict(metadata_map)
        if metadata is not None:
            combined_metadata_map[("OPF", "meta")] = metadata.get(OPF_NS, {}).get(
                "meta", []
            )
        super().__init__(combined_metadata_map)
        self._by_id = by_id
        self._items = items

    def get_item_with_id(self, item_id):
        return self._by_id.get(item_id)

    def get_items(self):
        return iter(self._items)


class DummyBookWithChapters(DummyBook):
    def __init__(self, toc, href_map, spine, id_map):
        super().__init__({})
        self.toc = toc
        self._href_map = href_map
        self.spine = spine
        self._id_map = id_map

    def get_item_with_href(self, href):
        return self._href_map.get(href)

    def get_item_with_id(self, item_id):
        return self._id_map.get(item_id)


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


def test_load_cover_uses_meta_cover_id_when_coverimage_is_missing():
    reader = EpubReader()
    item = DummyItem("cover", b"cover-bytes")
    book = DummyBookWithCover(
        metadata_map={},
        metadata={OPF_NS: {"meta": [(None, {"name": "cover", "content": "cover"})]}},
        by_id={"cover": item},
        items=[item],
    )

    assert reader._load_cover(book) == b"cover-bytes"


def test_load_cover_uses_coverimage_id_when_meta_cover_is_missing():
    reader = EpubReader()
    item = DummyItem("CoverImage", b"coverimage-bytes")
    book = DummyBookWithCover(
        metadata_map={},
        metadata={OPF_NS: {"meta": []}},
        by_id={"CoverImage": item},
        items=[],
    )

    assert reader._load_cover(book) == b"coverimage-bytes"


def test_load_cover_prefers_coverimage_over_cover_image_property():
    reader = EpubReader()
    coverimage_item = DummyItem("CoverImage", b"coverimage-bytes")
    property_item = DummyItem(
        "image-1",
        b"property-cover-bytes",
        properties=["cover-image"],
    )
    book = DummyBookWithCover(
        metadata_map={},
        metadata={OPF_NS: {"meta": []}},
        by_id={"CoverImage": coverimage_item},
        items=[property_item],
    )

    assert reader._load_cover(book) == b"coverimage-bytes"


def test_load_cover_uses_get_type_for_coverimage_items():
    reader = EpubReader()
    item = DummyItem(
        "CoverImage",
        b"type-cover-bytes",
        media_type="text/plain",
        item_type=1,
    )
    book = DummyBookWithCover(
        metadata_map={},
        metadata={OPF_NS: {"meta": []}},
        by_id={"CoverImage": item},
        items=[],
    )

    assert reader._load_cover(book) == b"type-cover-bytes"


def test_load_cover_ignores_non_image_coverimage_item_and_uses_later_property_fallback():
    reader = EpubReader()
    coverimage_item = DummyItem("CoverImage", b"not-an-image", media_type="text/plain")
    property_item = DummyItem(
        "image-1",
        b"property-cover-bytes",
        properties=["cover-image"],
    )
    book = DummyBookWithCover(
        metadata_map={},
        metadata={OPF_NS: {"meta": []}},
        by_id={"CoverImage": coverimage_item},
        items=[property_item],
    )

    assert reader._load_cover(book) == b"property-cover-bytes"


def test_load_cover_prefers_cover_image_property_over_cover_prefixed_image():
    reader = EpubReader()
    property_item = DummyItem(
        "image-1",
        b"property-cover-bytes",
        properties=["cover-image"],
    )
    prefixed_item = DummyItem("cover-page", b"prefixed-cover-bytes")
    book = DummyBookWithCover(
        metadata_map={},
        metadata={OPF_NS: {"meta": []}},
        by_id={},
        items=[property_item, prefixed_item],
    )

    assert reader._load_cover(book) == b"property-cover-bytes"


def test_load_cover_uses_cover_image_property_when_ids_are_missing():
    reader = EpubReader()
    item = DummyItem("image-1", b"property-cover-bytes", properties=["cover-image"])
    book = DummyBookWithCover(
        metadata_map={},
        metadata={OPF_NS: {"meta": []}},
        by_id={},
        items=[item],
    )

    assert reader._load_cover(book) == b"property-cover-bytes"


def test_load_cover_uses_cover_prefixed_image_when_property_is_missing():
    reader = EpubReader()
    item = DummyItem("cover-page", b"prefixed-cover-bytes")
    book = DummyBookWithCover(
        metadata_map={},
        metadata={OPF_NS: {"meta": []}},
        by_id={},
        items=[item],
    )

    assert reader._load_cover(book) == b"prefixed-cover-bytes"


def test_load_cover_prefers_meta_cover_over_later_fallbacks():
    reader = EpubReader()
    meta_item = DummyItem("meta-cover", b"meta-bytes")
    coverimage_item = DummyItem("CoverImage", b"coverimage-bytes")
    property_item = DummyItem(
        "image-1",
        b"property-cover-bytes",
        properties=["cover-image"],
    )
    prefixed_item = DummyItem("cover-page", b"prefixed-cover-bytes")
    first_image_item = DummyItem("img-1", b"image-bytes")
    book = DummyBookWithCover(
        metadata_map={},
        metadata={
            OPF_NS: {
                "meta": [(None, {"name": "cover", "content": "meta-cover"})]
            }
        },
        by_id={"meta-cover": meta_item, "CoverImage": coverimage_item},
        items=[property_item, prefixed_item, first_image_item],
    )

    assert reader._load_cover(book) == b"meta-bytes"


def test_load_cover_falls_back_to_first_image_when_cover_specific_items_are_missing():
    reader = EpubReader()
    item = DummyItem("img-1", b"image-bytes")
    book = DummyBookWithCover(
        metadata_map={},
        metadata={OPF_NS: {"meta": []}},
        by_id={},
        items=[item],
    )

    assert reader._load_cover(book) == b"image-bytes"


def test_load_cover_uses_default_asset_when_epub_has_no_cover():
    reader = EpubReader()
    book = DummyBookWithCover(
        metadata_map={},
        metadata={OPF_NS: {"meta": []}},
        by_id={},
        items=[],
    )

    expected = (Path(__file__).resolve().parents[3] / "assets" / "cover.png").read_bytes()

    assert reader._load_cover(book) == expected


def test_load_chapters_strips_href_anchor_and_keeps_html():
    reader = EpubReader()
    item = DummyHtmlItem("chapter1.xhtml", "<h1>Глава 1</h1><p>Текст</p>")
    book = DummyBookWithChapters(
        toc=[DummyLink("Глава 1", "chapter1.xhtml#part-1")],
        href_map={"chapter1.xhtml": item},
        spine=[],
        id_map={},
    )

    chapters = reader._load_chapters(book)

    assert len(chapters) == 1
    assert chapters[0].title == "Глава 1"
    assert chapters[0].content == "<h1>Глава 1</h1><p>Текст</p>"


def test_load_chapters_falls_back_to_spine_and_adds_poster_with_normalized_cover():
    reader = EpubReader()
    spine_item = DummyHtmlItem("chapter2.xhtml", "<p>Текст главы</p>")
    book = DummyBookWithChapters(
        toc=[],
        href_map={},
        spine=[("chapter-2", "yes")],
        id_map={"chapter-2": spine_item},
    )

    chapters = reader._load_chapters(book, cover=b"default-cover")

    assert chapters[0].title == "Постер"
    assert chapters[0].content == ""
    assert chapters[1].title == "chapter2"
    assert chapters[1].content == "<p>Текст главы</p>"


def test_load_chapters_flattens_nested_toc_entries():
    reader = EpubReader()
    chapter_item = DummyHtmlItem("chapter1.xhtml", "<p>Вложенная глава</p>")
    book = DummyBookWithChapters(
        toc=[
            (
                DummyLink("Раздел", None),
                [DummyLink("Глава 1", "chapter1.xhtml#fragment")],
            )
        ],
        href_map={"chapter1.xhtml": chapter_item},
        spine=[],
        id_map={},
    )

    chapters = reader._load_chapters(book)

    assert len(chapters) == 1
    assert chapters[0].title == "Глава 1"
    assert chapters[0].content == "<p>Вложенная глава</p>"


def test_load_chapters_deduplicates_same_cleaned_href_from_multiple_toc_entries():
    reader = EpubReader()
    chapter_item = DummyHtmlItem("chapter1.xhtml", "<p>Общий XHTML</p>")
    book = DummyBookWithChapters(
        toc=[
            DummyLink("Глава 1", "chapter1.xhtml#part-1"),
            DummyLink("Глава 1 дубль", "chapter1.xhtml#part-2"),
        ],
        href_map={"chapter1.xhtml": chapter_item},
        spine=[],
        id_map={},
    )

    chapters = reader._load_chapters(book)

    assert len(chapters) == 1
    assert chapters[0].title == "Глава 1"
    assert chapters[0].content == "<p>Общий XHTML</p>"


def test_load_passes_normalized_cover_into_load_chapters(monkeypatch):
    reader = EpubReader()
    dummy_book = object()
    observed = {}

    def fake_load_book(path):
        observed["path"] = path
        return dummy_book, b"epub-bytes"

    def fake_load_metadata(read_book):
        observed["metadata_book"] = read_book
        return ["Название"], "Автор", "Описание"

    def fake_load_cover(read_book):
        observed["cover_book"] = read_book
        return b"normalized-cover"

    def fake_load_chapters(read_book, cover=None):
        observed["chapters_book"] = read_book
        observed["cover"] = cover
        return []

    monkeypatch.setattr(reader, "_load_book", fake_load_book)
    monkeypatch.setattr(reader, "_load_metadata", fake_load_metadata)
    monkeypatch.setattr(reader, "_load_cover", fake_load_cover)
    monkeypatch.setattr(reader, "_load_chapters", fake_load_chapters)

    book = reader.load(path="book.epub")

    assert observed["path"] == "book.epub"
    assert observed["metadata_book"] is dummy_book
    assert observed["cover_book"] is dummy_book
    assert observed["chapters_book"] is dummy_book
    assert observed["cover"] == b"normalized-cover"
    assert book.cover == b"normalized-cover"


def test_load_chapters_supplements_partial_toc_from_spine_without_duplicates():
    reader = EpubReader()
    chapter1 = DummyHtmlItem("chapter1.xhtml", "<p>Глава 1</p>")
    chapter2 = DummyHtmlItem("chapter2.xhtml", "<p>Глава 2</p>")
    book = DummyBookWithChapters(
        toc=[
            DummyLink("Глава 1", "chapter1.xhtml#toc"),
            DummyLink("Глава 2", "missing.xhtml#toc"),
        ],
        href_map={"chapter1.xhtml": chapter1},
        spine=[("chapter-1", "yes"), ("chapter-2", "yes")],
        id_map={"chapter-1": chapter1, "chapter-2": chapter2},
    )

    chapters = reader._load_chapters(book)

    assert [chapter.title for chapter in chapters] == ["Глава 1", "chapter2"]
    assert [chapter.content for chapter in chapters] == ["<p>Глава 1</p>", "<p>Глава 2</p>"]


def test_load_chapters_spine_fallback_skips_auxiliary_nav_toc_and_cover_items():
    reader = EpubReader()
    nav_item = DummyHtmlItem("nav.xhtml", "<nav>Навигация</nav>")
    toc_item = DummyHtmlItem("toc.xhtml", "<nav>Оглавление</nav>")
    cover_item = DummyHtmlItem("cover.xhtml", "<p>Обложка</p>")
    chapter_item = DummyHtmlItem("chapter3.xhtml", "<p>Основная глава</p>")
    book = DummyBookWithChapters(
        toc=[],
        href_map={},
        spine=[
            ("nav", "yes"),
            ("toc", "yes"),
            ("cover", "yes"),
            ("chapter-3", "yes"),
        ],
        id_map={
            "nav": nav_item,
            "toc": toc_item,
            "cover": cover_item,
            "chapter-3": chapter_item,
        },
    )

    chapters = reader._load_chapters(book)

    assert len(chapters) == 1
    assert chapters[0].title == "chapter3"
    assert chapters[0].content == "<p>Основная глава</p>"


def test_load_chapters_adds_synthetic_poster_when_real_poster_title_is_not_first():
    reader = EpubReader()
    intro_item = DummyHtmlItem("intro.xhtml", "<p>Вступление</p>")
    poster_named_item = DummyHtmlItem("poster-chapter.xhtml", "<p>Реальная глава</p>")
    book = DummyBookWithChapters(
        toc=[
            DummyLink("Вступление", "intro.xhtml"),
            DummyLink("Постер", "poster-chapter.xhtml"),
        ],
        href_map={
            "intro.xhtml": intro_item,
            "poster-chapter.xhtml": poster_named_item,
        },
        spine=[],
        id_map={},
    )

    chapters = reader._load_chapters(book, cover=b"default-cover")

    assert [chapter.title for chapter in chapters] == ["Постер", "Вступление", "Постер"]
    assert chapters[0].content == ""
    assert chapters[2].content == "<p>Реальная глава</p>"


def test_load_chapters_does_not_prepend_synthetic_poster_when_first_chapter_is_already_poster():
    reader = EpubReader()
    poster_item = DummyHtmlItem("poster.xhtml", "<p>Реальный постер</p>")
    chapter_item = DummyHtmlItem("chapter1.xhtml", "<p>Глава 1</p>")
    book = DummyBookWithChapters(
        toc=[
            DummyLink("Постер", "poster.xhtml"),
            DummyLink("Глава 1", "chapter1.xhtml"),
        ],
        href_map={
            "poster.xhtml": poster_item,
            "chapter1.xhtml": chapter_item,
        },
        spine=[],
        id_map={},
    )

    chapters = reader._load_chapters(book, cover=b"default-cover")

    assert [chapter.title for chapter in chapters] == ["Постер", "Глава 1"]
    assert chapters[0].content == "<p>Реальный постер</p>"
