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
