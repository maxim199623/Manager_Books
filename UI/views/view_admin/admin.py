import functools
from pathlib import Path
from typing import List
import flet as ft

from Http_Client.errors import UnprocessableContentError, ConflictError
from Http_Client.schemas.books import BookCreate
from Http_Client.schemas.chapter import ChapterCreate
from UI.views.BaseView import BaseView
from UI.views.view_admin.tab_cont.Users_tab import Users_Tab
from UI.views.view_admin.tab_cont.add_book import Add_Book_Tab
from core.users.models import UserRole

from UI.get_element.button import get_button
from epub.reader import EpubReader
from state import MessageLevel


class AdminView(BaseView):
    route = "/admin"
    requires_auth = True
    allowed_roles = [UserRole.ADMIN]
    vert_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.CENTER

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self._container = ft.Container(
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            padding=10,
            border_radius=30,
            height=self.page.height * 1.00763 - 96.193
        )

        self.page.on_resize = self._page_resize

        self._column = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                 scroll=ft.ScrollMode.AUTO,
                                 controls=[])

        self._button_list = [
            get_button(text="Добавление книг", button_name="add_book", func_but=self._func_but_tab),
            get_button(text="Пользователи", button_name="users", func_but=self._func_but_tab)
        ]

        self.file_picker = ft.FilePicker()
        self.add_book_tab = Add_Book_Tab(page=self.page)
        self.users_tab = Users_Tab(page=self.page)
        self._active_tab = None

        self.form_data = {
            "title": "",
            "author": "",
            "description": "",
            "series": "",
            "format": "",
            "file": None,
            "cover": None,
        }
        self.book = None

    def _app_bar_settings(self):
        self.app_bar.title = ft.Text("Админ Панель")
        self.app_bar.center_title = True
        self.app_bar.actions = [ft.IconButton(icon = ft.Icons.LOGOUT, on_click=self.state.clear_user)]

    def _collum1_settings(self):
        self._column.controls.append(ft.Row(controls=self._button_list))
        self._button_list[0].color = ft.Colors.SECONDARY_CONTAINER
        self._button_list[0].disabled = True
        self._change_tab(self._button_list[0].data)


    def _func_but_tab(self,e):
        ic()
        ic(e)
        ic(e.control.data)
        for button in self._button_list:
            if button.data == e.control.data:
                button.color = ft.Colors.SECONDARY_CONTAINER
                button.disabled = True
                self._change_tab(button.data)
            else:
                button.color = ft.Colors.PRIMARY
                button.disabled = False

    def _change_tab(self, tab):
        ic(isinstance(self._column.controls[-1], ft.Container))
        if ic(self._active_tab in self._column.controls):
            self._column.controls.remove(self._active_tab)
            ic(self._active_tab in self._column.controls)
        match tab:
            case "add_book":
                self._active_tab = self.add_book_tab.get_content(func_field = self._func_field, func_but=self._func_but)
            case "users":
                self._active_tab = self.users_tab.get_content()
            case _:
                ic(tab)
                self._active_tab = None
        if self._active_tab is not None:
            self._column.controls.append(self._active_tab)

    def _func_field(self, e):
        ic(e.control.data, e.control.value)
        self.form_data[e.control.data] = e.control.value

    def _func_but(self, e):
        actions = {
            "load_book": functools.partial(self._run_with_loading,self._pick_files,key="load_book"),
            "cover": functools.partial(self._run_with_loading,self._pick_files,key="cover",
                                       allowed_extensions=["png"]),
            "add_book": functools.partial(self._run_with_loading,self._add_book),
        }
        ic()
        action = actions.get(e.control.data)
        if action:
            self.page.run_task(action)

    async def _run_with_loading(self, func, *args, **kwargs):
        self.add_book_tab.set_loading(True)
        try:
            return await func(*args, **kwargs)
        finally:
            self.add_book_tab.set_loading(False)

    async def _pick_files(self, allow_multiple:bool = False, allowed_extensions:List[str] = None, key:str = None):
        ic()
        files = await  self.file_picker.pick_files(
            allow_multiple=allow_multiple,
            allowed_extensions=allowed_extensions,
            with_data=True)
        if not files:
            return
        file = files[0]
        ext = Path(file.name).suffix.lower().lstrip(".")
        data = file.bytes
        ic(isinstance(data, bytes))
        match key:
            case "load_book":
                ic(key)
                self.form_data[key] = data
                if ext == "epub":
                   book = EpubReader().load(data=data)
                   ic(book.title)
                   self.book = book
                   if book.cover is not None:
                        self.add_book_tab.change_cover(book.cover)
                   self.add_book_tab.set_filed(book)
                else:
                    self.form_data["file"] = data
                    self.form_data["file_format"] = ext
            case "cover":
                ic(key)
                self.form_data[key] = data
                if data is not None:
                    self.add_book_tab.change_cover(data)
            case _:
                ic(key)

    async def _add_book(self):
        if self.book is not None:
            book, chapters = self.add_epub()
        else:
            book, chapters = self.add_other_books()
        id_book = None
        try:
            id_book = await self.api.add_book(book)
            ic(id_book)
        except UnprocessableContentError as exc:
            self.state.notify(message=f"Ошибка добавления книги: {exc}", level=MessageLevel.ERROR)
        except ConflictError as exc:
            self.state.notify(message=f"Ошибка добавления книги: {exc}", level=MessageLevel.ERROR)
        except Exception as exc:
            self.state.notify(message=f"Ошибка добавления книги: {exc}", level=MessageLevel.ERROR)

        try:
            if id_book is not None and chapters is not None:
                ic(chapters)
                await self.api.add_chapters(book_id=id_book["id"], chapters=chapters)
        except Exception as exc:
            self.state.notify(message=f"ошибка добавления глав: {exc}", level=MessageLevel.ERROR)

    def add_epub(self):
        book = BookCreate(title=self.book.title,
                          description=self.book.description,
                          author=self.book.author,
                          format=self.book.file_format,
                          series=self.book.series,
                          cover=self.book.cover,
                          file=self.book.file)

        chapters = []
        for index, chapter in enumerate(self.book.chapters):
            chapters.append(ChapterCreate(chapter=index,
                                          chapter_name=chapter.title,
                                          description=chapter.content))
        return book, chapters

    def add_other_books(self):
        book = BookCreate(**self.form_data)
        return book, None

    def build_content(self) -> ft.Control:
        """
        Возвращает View для Router.
        """
        ic()
        self._app_bar_settings()
        self._collum1_settings()
        cont = self._container
        cont.content = self._column
        return cont

    def _page_resize(self):
        ic(self.page.width, self.page.height)  # type: ignore
        self._container.height = ic(self.page.height * 1.00763 - 96.193)
        self._container.update()
        if isinstance(self._column.controls[-1], ft.Container):
            self._column.controls[-1].height = ic(self.page.height * 1.00763 - 160)
            self._column.controls[-1].update()