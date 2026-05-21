import flet as ft

from core.Http_Client.errors import SessionReplacedError
from UI.views.BaseView import BaseView
from UI.views.view_books.cont_book import Book_cont
from core.users.models import UserRole
from core.MessageLevel import MessageLevel

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
                height = self.page.height * 1.00763 - 96.193,
                width = self.page.width
                )
        self.loader = ft.ProgressBar(bar_height = 10, border_radius=10)
        self.search = ft.SearchBar(bar_hint_text="Поиск...", bar_bgcolor = ft.Colors.PRIMARY_CONTAINER,
                                   on_change=self._search, autofocus=True)
        self.drow = ft.Dropdown()

        self.search_row = ft.Row(controls=[self.drow,ft.Container(expand=True,content= self.search)])
        self._settings_drow()
        self._column = ft.ResponsiveRow(spacing=10,
                        run_spacing=10,
                        controls=[self.search_row, self.loader])

        self.cards = []
        self._get_books()

    def _settings_drow(self):
        self.drow.value = "name"
        self.drow.options.append(ft.DropdownOption(key="name", text="Название"))
        self.drow.options.append(ft.DropdownOption(key="author", text="Автор"))
        self.drow.options.append(ft.DropdownOption(key="series", text="Серия"))

    async def _search(self):
        search_value = self.search.value
        search_key = self.drow.value
        ic(search_value, search_key)
        for card in self.cards:
           book = card.get_book()
           card.change_visible(True)
           if search_value != "" and search_value is not None:
               query = search_value.strip().casefold()
               match search_key:
                    case "name":
                        title = book.title.strip().casefold()
                        card.change_visible(query in title)
                    case "author":
                        check = book.author is not None
                        author = book.author.strip().casefold() if check else ""
                        card.change_visible(query in author)
                    case "series":
                        check = book.series is not None
                        series = book.series.strip().casefold() if check else ""
                        card.change_visible(query in series)
               await self.search.focus()


    def _app_bar_settings(self):
        self.app_bar.title = ft.Text("Менеджер Книг")
        self.app_bar.center_title = True
        self.app_bar.actions.append(ft.IconButton(icon = ft.Icons.LOGOUT, on_click=self.auth_logic.logout))


    def _get_books(self):
        """Запуск async загрузки"""
        self.page.run_task(self._load_books_async)

    async def _load_books_async(self):
        try:
            books = await self.api.get_books()
        except SessionReplacedError:
            self.state.notify(message="Сессия закрыта", level=MessageLevel.WARNING)
            
            self.state.clear_user()
        except Exception as exc:
            self.state.notify(message=f"ошибка получения книг, {exc}", level=MessageLevel.WARNING)
        books.sort(key=lambda x: x.created_at, reverse=True)
        for index, book in enumerate(books):
            self.loader.value = (index + 1) / len(books)
            card = Book_cont(page=self.page)
            self.cards.append(card)
            cont_book = card.get_cont(
                title=book.title, description=book.description, index=book.id, cover=book.cover, data = book
                )
            cont_book.col = {ft.ResponsiveRowBreakpoint.XS: 6,
                             ft.ResponsiveRowBreakpoint.SM: 4,
                             ft.ResponsiveRowBreakpoint.MD: 3,
                             ft.ResponsiveRowBreakpoint.LG: 12
}
            self._column.controls.append(cont_book)

            self.page.update()
        self.loader.visible = False
        self.page.update()


    def _page_resize(self):
        ic(self.page.width, self.page.height)  # type: ignore
        self._container.height = ic(self.page.height * 1.00763 - 96.193)
        self._container.width = self.page.width
        self._container.update()
        for card in self.cards:
            card.apply_mode()
        self.page.update()


    def build_content(self) -> ft.Control:
        """
        Возвращает View для Router.
        """
        ic()
        cont = self._container
        cont.content = ft.Column(expand=True,
                  scroll=ft.ScrollMode.AUTO,
                  controls=[self._column])
        return cont