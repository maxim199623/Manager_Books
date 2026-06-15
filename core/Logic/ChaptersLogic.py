from core.Http_Client.schemas.chapter import ChapterPatch, BookChapterListRead, ReadChaptersResponse
from core.Logic.ApiLogic import ApiLogic


class ChaptersLogic(ApiLogic):
    async def add_chapters(self, book_id, chapters):
        try:
            return await self.api.add_chapters(book_id=book_id, chapters=chapters)
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Книга добавлена, но главы загрузить не удалось.",
                not_found_message="Книга не найдена. Главы не были добавлены.",
                unprocessable_message="Не удалось загрузить главы книги. Проверьте данные EPUB.",
                validation_message="Не удалось загрузить главы книги. Проверьте данные EPUB.",
            )
            return None

    async def get_chapter(self, book_id, chapter_num):
        try:
            return await self.api.get_chapter(book_id=book_id, chapter_num=chapter_num)
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось открыть главу.",
                not_found_message="Глава не найдена.",
            )
            return None

    async def get_chapters(self, book_id) -> list[BookChapterListRead] | None:
        try:
            return await self.api.get_chapters(book_id=book_id)
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось загрузить список глав.",
                not_found_message="Книга не найдена.",
            )
            return None

    async def get_chapters_num(self, book_id):
        try:
            return await self.api.get_chapters_num(book_id=book_id)
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось загрузить список глав.",
                not_found_message="Книга не найдена.",
            )
            return None

    async def get_count_read_chapters_in_book(self, book_id):
        try:
            return await self.api.get_count_read_chapters_in_book(book_id=book_id)
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось загрузить прогресс чтения.",
                not_found_message="Книга не найдена.",
            )
            return None

    async def get_read_chapters_in_book(self, book_id) -> ReadChaptersResponse | None:
        try:
            return await self.api.get_read_chapters_in_book(book_id=book_id)
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось загрузить историю чтения.",
                not_found_message="Книга не найдена.",
            )
            return None

    async def delete_history_read_chapters_in_book(self, book_id) -> bool:
        try:
            await self.api.delete_history_read_chapters_in_book(book_id=book_id)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось очистить историю чтения. Повторите попытку.",
                not_found_message="Книга не найдена.",
            )
            return False

    async def patch_chapter(self, book_id, chapter_num: int, chapter: ChapterPatch) -> bool:
        try:
            if not chapter.model_dump(exclude_none=True):
                self._notify("Нет данных для изменения главы.")
                return False
            await self.api.patch_chapter(book_id, chapter_num, chapter)
            return True
        except Exception as exc:
            self._handle_api_error(
                exc,
                default_message="Не удалось изменить главу.",
                forbidden_message="У вас нет прав на изменение глав.",
                not_found_message="Глава не найдена.",
                validation_message="Проверьте данные главы.",
                unprocessable_message="Проверьте данные главы.",
            )
            return False
