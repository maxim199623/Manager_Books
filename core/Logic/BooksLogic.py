from core.Logic.ApiLogic import ApiLogic
from core.Http_Client.schemas.books import BookCreate, BookUpdate, BookCreateResponse, BookRead, BookFilePayload


class BooksLogic(ApiLogic):
    async def add_book(self, book: BookCreate) -> BookCreateResponse | None:
        try:
            return await self.api.add_book(book)
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось добавить книгу. Повторите попытку позже.",
                forbidden_message="У вас нет прав на добавление книг.",
                conflict_message="Такая книга уже есть в базе.",
                validation_message="Не удалось добавить книгу. Проверьте название, описание, формат и файл.",
                unprocessable_message="Не удалось добавить книгу. Проверьте название, описание, формат и файл.",
            )
            return None

    async def favorite_book(self, book_id) -> bool:
        try:
            await self.api.favorite_book(book_id)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось обновить избранное. Повторите попытку.",
                not_found_message="Книга не найдена. Возможно, она уже удалена.",
            )
            return False

    async def unfavorite_book(self, book_id) -> bool:
        try:
            await self.api.unfavorite_book(book_id)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось обновить избранное. Повторите попытку.",
                not_found_message="Книга не найдена. Возможно, она уже удалена.",
            )
            return False

    async def get_books(self, author=None, series=None) -> list[BookRead] | None:
        try:
            return await self.api.get_books(author=author, series=series)
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось загрузить список книг. Проверьте подключение и повторите попытку.",
            )
            return None

    async def delete_book(self, book_id) -> bool:
        try:
            await self.api.delete_book(book_id)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось удалить книгу. Повторите попытку.",
                forbidden_message="У вас нет прав на удаление книг.",
                not_found_message="Книга не найдена. Возможно, она уже удалена.",
            )
            return False

    async def get_book_file(self, book_id) -> BookFilePayload | None:
        try:
            return await self.api.get_book_file(book_id)
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось скачать книгу. Повторите попытку.",
                not_found_message="Файл книги недоступен.",
            )
            return None

    async def patch_book(self, book_id, book: BookUpdate) -> bool:
        try:
            if not book.model_dump(exclude_none=True):
                self._notify("Нет данных для изменения книги.")
                return False
            await self.api.patch_book(book_id, book)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось изменить книгу. Повторите попытку.",
                forbidden_message="У вас нет прав на изменение книг.",
                not_found_message="Книга не найдена. Возможно, она уже удалена.",
                validation_message="Проверьте данные книги.",
                unprocessable_message="Проверьте данные книги.",
            )
            return False

    async def update_book_cover(self, book_id, cover: bytes) -> bool:
        try:
            await self.api.update_book_cover(book_id, cover)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось заменить обложку книги.",
                forbidden_message="У вас нет прав на изменение книг.",
                not_found_message="Книга не найдена.",
                validation_message="Проверьте файл обложки.",
                unprocessable_message="Проверьте файл обложки.",
            )
            return False

    async def update_book_file(self, book_id, file_payload: bytes,
                                              file_name: str,
                                              file_mime: str | None = None) -> bool:
        try:
            await self.api.update_book_file(book_id, file_payload, file_name, file_mime)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось заменить файл книги.",
                forbidden_message="У вас нет прав на изменение книг.",
                not_found_message="Книга не найдена.",
                validation_message="Проверьте файл книги.",
                unprocessable_message="Проверьте файл книги.",
            )
            return False
