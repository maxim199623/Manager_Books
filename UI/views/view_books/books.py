import flet as ft

from UI.views.BaseView import BaseView
from core.users.models import UserRole
from UI.views.view_books.book_cont import create_cont_book

class BooksView(BaseView):

    route = "/books"
    requires_auth = True
    allowed_roles = [UserRole.USER, UserRole.ADMIN]
    vert_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.CENTER

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self._app_bar_settings()
        self.drawer.selected_index = 1
        self.page.on_resize = self._page_resize
        self._container = ft.Container(
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                padding=10,
                border_radius = 30,
                height = self.page.height * 1.00763 - 96.193
                )
        self.loader = ft.ProgressBar(bar_height = 10, border_radius=10)
        self._column = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                         scroll=ft.ScrollMode.AUTO,
                                 controls = [self.loader])
        self._get_books()


    def _app_bar_settings(self):
        self.app_bar.title = ft.Text("Менеджер Книг")
        self.app_bar.center_title = True
        self.app_bar.actions = [ft.IconButton(icon = ft.Icons.LOGOUT, on_click=self.state.clear_user)]

    def _get_books(self):
        """Запуск async загрузки"""
        self.page.run_task(self._load_books_async)

    async def _load_books_async(self):
        books = await self.api.get_books()
        for index, book in enumerate(books):
            self.loader.value = (index + 1) / len(books)
            cont_book = create_cont_book(title=book.title, description=book.description, index=book.id, cover=book.cover)
            if book.file is None:
                cont_book.content.controls[2].content.controls[0].content = "Нет файла"
                cont_book.content.controls[2].content.controls[0].disabled = True
            self._column.controls.append(cont_book)

            self.page.update()
        self.loader.visible = False
        self.page.update()


    def _page_resize(self):
        ic(self.page.width, self.page.height)  # type: ignore
        self._container.height = ic(self.page.height * 1.00763 - 96.193)
        self._container.update()


    def build_content(self) -> ft.Control:
        """
        Возвращает View для Router.
        """
        ic()
        cont = self._container
        cont.content = self._column
        return cont