import logging
import ssl
import uuid

import httpx
from typing import List, Optional

from core.Http_Client.base import map_http_error
from core.Http_Client.schemas.base_metod import HTTPMethod
from core.Http_Client.schemas.users import TokenResponse, UserCreate, UserRead, UserPatch
from core.Http_Client.schemas.books import BookCreate, BookRead, BookUpdate
from core.Http_Client.schemas.chapter import ChapterCreate, ChapterRead, ChapterCount, ChapterReadCount, ChapterPatch

logger = logging.getLogger("app")

class ApiClient:
    """
    HTTP-клиент.
    """

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


    async def patch_user(self, user_id: int, user: UserPatch) -> None:
        await self._request(method=HTTPMethod.PATCH,
                                   url=f"/users/{user_id}",
                                   json=user.model_dump(),
                                   expected_status=200)

    async def add_book(self, book: BookCreate) -> None:
       resp = await self._request(method=HTTPMethod.POST,
                            url="/books/add_book",
                            json=book.model_dump(exclude_none=True),
                            expected_status=201)

       return resp

    async def get_books(self,
                        author: Optional[str] = None,
                        series: Optional[str] = None) -> List[BookRead]:
        params = {}
        if author is not None:
            params["author"] = author
        if series is not None:
            params["series"] = series

        resp = await self._request(method=HTTPMethod.GET,
                                   url="/books/",
                                   params=params,
                                   expected_status=200)
        return [BookRead(**b) for b in resp]

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

    async def get_read_chapters_in_book(self, book_id: uuid.UUID) -> List[int]:
        resp = await self._request(method=HTTPMethod.GET,
                                   url=f"/books/chapters/read",
                                   params={"book_id":book_id},
                                   expected_status=200)
        return resp

    async def delete_history_read_chapters_in_book(self, book_id: uuid.UUID) -> None:
        await self._request(method=HTTPMethod.DELETE,
                                   url=f"/books/{book_id}/history",
                                   expected_status=200)

    async def patch_chapter(self, book_id: uuid.UUID, chapter_num: int, chapter: ChapterPatch) -> None:
        await self._request(method=HTTPMethod.PATCH,
                            url=f"/books/{book_id}/chapters/{chapter_num}",
                            json=chapter.model_dump(exclude_none=True),
                            expected_status=200)


    def _auth_headers(self) -> dict:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    async def _request(self,
                       method: HTTPMethod,
                       url: str,
                       expected_status: int,
                       json: dict | list | None = None,
                       params: dict | None = None,
                       ):
        ic()
        ic(f"Запрос {method} на {url}")
        ic(f"json {"Есть" if json is not None else "Нету" }")
        resp = await self._client.request(
            method.value,
            url,
            json=json,
            params=params,
            headers=self._auth_headers(),
        )

        if resp.status_code != expected_status:
            logger.warning(f"От {resp.url} вернулся {resp.status_code}")
            map_http_error(resp)

        if resp.status_code == 204:
            return None

        return resp.json()

    async def close(self):
        await self._client.aclose()