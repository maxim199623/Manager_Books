import logging
import ssl
import uuid
import asyncio
import mimetypes

import httpx
from typing import List, Optional, Literal

from core.Http_Client.base import map_http_error
from core.Http_Client.schemas.base_metod import HTTPMethod
from core.Http_Client.schemas.users import TokenResponse, UserCreate, UserRead, UserPatch
from core.Http_Client.schemas.books import BookCreate, BookRead, BookUpdate, BookCreateResponse, BookChapterListRead, \
    BookFilePayload
from core.Http_Client.schemas.chapter import ChapterCreate, ChapterRead, ChapterCount, ChapterReadCount, ChapterPatch, \
    ReadChaptersResponse

logger = logging.getLogger("app")


class ApiClient:
    """
    HTTP-клиент.
    """
    SortBy = Literal["created_at", "progress", "title"]
    SortDir = Literal["asc", "desc"]

    def __init__(self, base_url: str):
        try:
            ssl_context = ssl.create_default_context(cafile="cert.pem")
        except FileNotFoundError:
            logger.critical("Не найден файл сертификата по пути (cert.pem)")
            raise
        self._client = httpx.AsyncClient(base_url=base_url,verify=ssl_context, timeout=20.0)
        self.token: Optional[str] = None
        self.base_url = base_url.rstrip("/")

    async def login(self, email: str, password: str) -> TokenResponse:
        resp = await self._request(method=HTTPMethod.POST,
                                   url="/users/auth",
                                   json={"email": email, "password": password},
                                   expected_status=200)
        token = TokenResponse(**resp)
        self.token = token.access_token
        return token

    async def logout(self):
        await self._request(method=HTTPMethod.DELETE,
                                   url="/users/logout",
                                   expected_status=204)

    async def add_user(self, user: UserCreate) -> None:
        await self._request(method=HTTPMethod.POST,
                                   url="/users/add_user",
                                   json=user.model_dump(),
                                   expected_status=201)

    async def get_users(self) -> List[UserRead]:
        resp = await self._request(method=HTTPMethod.GET,
                            url="/users/get_users",
                            expected_status=200)
        return [UserRead(**u) for u in resp]

    async def delete_user(self, user_id: uuid.UUID) -> None:
        await self._request(method=HTTPMethod.DELETE,
                            url=f"/users/{user_id}",
                            expected_status=204)


    async def patch_user(self, user_id: uuid.UUID, user: UserPatch) -> None:
        await self._request(method=HTTPMethod.PATCH,
                                   url=f"/users/{user_id}",
                                   json=user.model_dump(exclude_none=True),
                                   expected_status=200)

    async def add_book(self, book: BookCreate) -> BookCreateResponse:
        data, files = self._build_book_payload(book)
        resp = await self._request(
            method=HTTPMethod.POST,
            url="/books/add_book",
            data=data,
            files=files,
            expected_status=201,
        )
        return BookCreateResponse(**resp)

    async def favorite_book(self, book_id: uuid.UUID) -> None:
       resp = await self._request(method=HTTPMethod.POST,
                            url=f"/books/{book_id}/favorite",
                            expected_status=204)

       return resp

    async def unfavorite_book(self, book_id: uuid.UUID) -> None:
       resp = await self._request(method=HTTPMethod.DELETE,
                            url=f"/books/{book_id}/favorite",
                            expected_status=204)

       return resp

    async def get_books(self,
                        author: Optional[str] = None,
                        series: Optional[str] = None,
                        offset: int = 0, limit: int = 100,
                        sort_by: SortBy = "created_at",
                        sort_dir: SortDir = "desc") -> List[BookRead]:
        params = {
            "offset": offset,
            "limit": limit,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
        }

        if author is not None:
            params["author"] = author
        if series is not None:
            params["series"] = series

        resp = await self._request(method=HTTPMethod.GET,
                                   url="/books/",
                                   params=params,
                                   expected_status=200)
        books = [BookRead(**b) for b in resp]
        await self._prefetch_book_covers(books)
        return books


    async def patch_book(self, book_id: uuid.UUID, book: BookUpdate) -> None:
        await self._request(method=HTTPMethod.PATCH,
                                   url=f"/books/{book_id}",
                                   json=book.model_dump(exclude_none=True),
                                   expected_status=200)


    async def delete_book(self, book_id: uuid.UUID) -> None:
        await self._request(method=HTTPMethod.DELETE,
                            url=f"/books/{book_id}",
                            expected_status=204)


    async def add_chapters(self, book_id: uuid.UUID, chapters: List[ChapterCreate]) -> None:
        resp = await self._request(method=HTTPMethod.POST,
                            url=f"/books/{book_id}/chapters",
                            json=[c.model_dump() for c in chapters],
                            expected_status=201)
        return resp

    async def get_chapter(self, book_id: uuid.UUID, chapter_num: int) -> ChapterRead:
        resp = await self._request(method=HTTPMethod.GET,
                                   url=f"/books/{book_id}/chapters/{chapter_num}",
                                   expected_status=200)
        return ChapterRead(**resp)

    async def get_chapters(self, book_id: uuid.UUID) -> List[BookChapterListRead]:
        resp = await self._request(
            method=HTTPMethod.GET,
            url=f"/books/{book_id}/chapters",
            expected_status=200,
        )
        return [BookChapterListRead(**chapter) for chapter in resp]

    async def get_chapters_num(self, book_id: uuid.UUID) -> ChapterCount:
        resp = await self._request(method=HTTPMethod.GET,
                                   url=f"/books/{book_id}/chapters/count",
                                   expected_status=200)
        return ChapterCount(**resp)

    async def get_count_read_chapters_in_book(self, book_id: uuid.UUID) -> ChapterReadCount:
        resp = await self._request(method=HTTPMethod.GET,
                                   url=f"/books/{book_id}/chapters/read/count",
                                   expected_status=200)
        return ChapterReadCount(**resp)

    async def get_read_chapters_in_book(self, book_id: uuid.UUID,
                                        offset: int = 0,
                                        limit: int = 100) -> ReadChaptersResponse:
        params = {"offset": offset,
                  "limit": limit}
        if book_id is not None:
            params["book_id"] = book_id
        resp = await self._request(method=HTTPMethod.GET,
                                   url=f"/books/chapters/read",
                                   params=params,
                                   expected_status=200)
        return ReadChaptersResponse(chapters=resp)

    async def delete_history_read_chapters_in_book(self, book_id: uuid.UUID) -> None:
        await self._request(method=HTTPMethod.DELETE,
                                   url=f"/books/{book_id}/history",
                                   expected_status=200)

    async def patch_chapter(self, book_id: uuid.UUID, chapter_num: int, chapter: ChapterPatch) -> None:
        await self._request(method=HTTPMethod.PATCH,
                            url=f"/books/{book_id}/chapters/{chapter_num}",
                            json=chapter.model_dump(exclude_none=True),
                            expected_status=200)

    async def get_book_cover(self, book_id: uuid.UUID):
        return await self._request(
            method=HTTPMethod.GET,
            url=f"/books/{book_id}/cover",
            expected_status=200,
            return_bytes=True,
        )

    async def update_book_cover(self, book_id: uuid.UUID, cover: bytes) -> None:
        cover_name, cover_mime = self._guess_cover_upload(cover)
        await self._request(
            method=HTTPMethod.PUT,
            url=f"/books/{book_id}/cover",
            files={"cover": (cover_name, cover, cover_mime)},
            expected_status=204,
        )

    async def get_book_file(self, book_id: uuid.UUID) -> BookFilePayload:
        content = await self._request(
            method=HTTPMethod.GET,
            url=f"/books/{book_id}/file",
            expected_status=200,
            return_bytes=True,
        )
        return BookFilePayload(content=content)

    async def update_book_file(self,book_id: uuid.UUID,
                                    file_payload: bytes,
                                    file_name: str,
                                    file_mime: str | None = None) -> None:
        mime = file_mime or mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        await self._request(
            method=HTTPMethod.PUT,
            url=f"/books/{book_id}/file",
            files={"file": (file_name, file_payload, mime)},
            expected_status=204,
        )


    def _auth_headers(self) -> dict:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    async def _prefetch_book_covers(self, books: List[BookRead]) -> None:
        semaphore = asyncio.Semaphore(5)

        async def load_cover(book: BookRead) -> None:
            if book.cover_size <= 0:
                return
            async with semaphore:
                book.cover = await self.get_book_cover(book.id)

        await asyncio.gather(*(load_cover(book) for book in books))

    @staticmethod
    def _build_book_payload(book: BookCreate):
        data = {"title": book.title}
        optional_fields = {
            "author": book.author,
            "description": book.description,
            "series": book.series,
            "genres": book.genres,
            "format": book.format,
        }
        for key, value in optional_fields.items():
            if value is not None:
                data[key] = value

        files: dict[str, tuple[str, bytes, str]] = {}
        if book.cover is not None:
            cover_name, cover_mime = ApiClient._guess_cover_upload(book.cover)
            files["cover"] = (cover_name, book.cover, cover_mime)
        if book.file is not None:
            file_name, file_mime = ApiClient._guess_book_upload(book)
            files["file"] = (file_name, book.file, file_mime)

        return data, files

    @staticmethod
    def _guess_cover_upload(cover: bytes) -> tuple[str, str]:
        if cover.startswith(b"\x89PNG\r\n\x1a\n"):
            return "cover.png", "image/png"
        if cover.startswith(b"\xff\xd8\xff"):
            return "cover.jpg", "image/jpeg"
        if cover.startswith((b"GIF87a", b"GIF89a")):
            return "cover.gif", "image/gif"
        if cover.startswith(b"RIFF") and cover[8:12] == b"WEBP":
            return "cover.webp", "image/webp"
        return "cover.bin", "application/octet-stream"

    @staticmethod
    def _guess_book_upload(book: BookCreate) -> tuple[str, str]:
        extension = (book.format or "bin").strip(".").lower()
        title = book.title.replace(" / ", "_").strip() or "book"
        file_name = f"{title}.{extension}" if extension else title
        guessed_mime = mimetypes.guess_type(file_name)[0]
        mime_by_extension = {
            "epub": "application/epub+zip",
            "fb2": "application/x-fictionbook+xml",
            "mobi": "application/x-mobipocket-ebook",
            "pdf": "application/pdf",
            "txt": "text/plain",
        }
        return file_name, mime_by_extension.get(extension, guessed_mime or "application/octet-stream")

    async def _request(self,
                       method: HTTPMethod,
                       url: str,
                       expected_status: int,
                       json: dict | list | None = None,
                       params: dict | None = None,
                       data: dict | None = None,
                       files: dict | None = None,
                       return_bytes: bool = False,
                       ):
        ic()
        ic(f"Запрос {method} на {url}")
        logger.debug("Запрос API", extra={"method": method.value, "url": url})
        resp = await self._client.request(
            method.value,
            url,
            json=json,
            params=params,
            data=data,
            files=files,
            headers=self._auth_headers(),
        )

        if resp.status_code != expected_status:
            logger.warning(f"От {resp.url} вернулся {resp.status_code}")
            map_http_error(resp)

        if return_bytes:
            return resp.content

        if resp.status_code == 204 or not resp.content:
            return None

        try:
            return resp.json()
        except ValueError:
            return None

    async def close(self):
        await self._client.aclose()
