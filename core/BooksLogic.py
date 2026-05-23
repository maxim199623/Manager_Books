from core.ApiLogic import ApiLogic
from core.Http_Client.schemas.books import BookCreate


class BooksLogic(ApiLogic):
    async def add_book(self, book: BookCreate):
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

    async def get_books(self, author=None, series=None):
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

    async def get_book_file(self, book_id):
        try:
            return await self.api.get_book_file(book_id)
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось скачать книгу. Повторите попытку.",
                not_found_message="Файл книги недоступен.",
            )
            return None
