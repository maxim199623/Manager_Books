import asyncio

import flet as ft

from UI.views.BaseView import BaseView
from UI.views.view_books.cont_book import Book_cont
from core.users.models import UserRole
from core.epub.models import BookGenre
from datetime import datetime


class BooksView(BaseView):

    route = "/books"
    requires_auth = True
    allowed_roles = [UserRole.USER, UserRole.ADMIN]
    vert_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.CENTER

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.sort_key = self.state.books_sort_key
        self.sort_desc = self.state.books_sort_desc

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
        self.text_search  = ft.SearchBar(bar_hint_text="Поиск...", bar_bgcolor = ft.Colors.PRIMARY_CONTAINER,
                                   on_change=self._search, autofocus=True)
        self.genre_field = ft.TextField(hint_text="",read_only=True,expand=True,border_radius=15)
        self.genre_button = ft.SubmenuButton(content=ft.Icon(ft.Icons.ARROW_DROP_DOWN), on_close=self._apply_genre_filter,)
        self.selected_genres: set[str] = set()
        self.search = ft.Container(expand=True, content=self.text_search)
        self.drow = ft.Dropdown(on_select=self._change_search_mode)

        self.show_only_favorites = False
        self.favorite_filter_button = ft.IconButton()
        self._setting_favorite_filter_button()

        self.sort_button = ft.SubmenuButton(content=ft.Icon(ft.Icons.SORT, color=ft.Colors.PRIMARY))
        self.sort_items = {}
        self._settings_sort_button()

        self.search_row = ft.Row(controls=[self.favorite_filter_button, self.sort_button, self.drow, self.search])
        self._settings_drow()
        self._settings_genre_button()

        self._column = ft.ResponsiveRow(spacing=10,
                        run_spacing=10,
                        controls=[self.search_row, self.loader])
        self.cards = []
        self._get_books()

    def _settings_sort_button(self):
        self.sort_button.controls.clear()
        self.sort_items["created_at"] = self._get_sort_menu_item("created_at", "Дата добавления")
        self.sort_items["progress"] = self._get_sort_menu_item("progress", "Прогресс чтения")
        self.sort_items["title"] = self._get_sort_menu_item("title", "Название")

        for item in self.sort_items.values():
            self.sort_button.controls.append(item)

        self._update_sort_button()

    def _get_sort_menu_item(self, sort_key: str, text: str) -> ft.MenuItemButton:
        item = ft.MenuItemButton(content=ft.Text(text))
        item.on_click = lambda e, key=sort_key: self._toggle_sort(key)
        return item

    def _toggle_sort(self, sort_key: str):
        if self.sort_key == sort_key:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_key = sort_key
            if sort_key in ("created_at", "progress"):
                self.sort_desc = True
            else:
                self.sort_desc = False

        self.state.books_sort_key = self.sort_key
        self.state.books_sort_desc = self.sort_desc

        self._update_sort_button()
        self._sort_cards()


    def _update_sort_button(self):
        names = {
            "created_at": "Дата добавления",
            "progress": "Прогресс чтения",
            "title": "Название",
        }

        self.sort_button.tooltip = f"Сортировка: {names[self.sort_key]} ({'убыв.' if self.sort_desc else 'возр.'})"

        for key, item in self.sort_items.items():
            if key == self.sort_key:
                item.leading = ft.Icon(
                    ft.Icons.ARROW_DOWNWARD if self.sort_desc else ft.Icons.ARROW_UPWARD,
                    size=18,
                )
            else:
                item.leading = None

            item.trailing = None

    def _get_sort_value(self, card: Book_cont):
        book = card.get_book()

        match self.sort_key:
            case "created_at":
                return book.created_at if book.created_at is not None else datetime.min
            case "progress":
                return card.get_read_progress()
            case "title":
                return (book.title or "").strip().casefold()

        return 0

    def _sort_cards(self, update:bool = True):
        self.cards.sort(key=self._get_sort_value, reverse=self.sort_desc)
        self._column.controls = [self.search_row, self.loader] + [card.cont for card in self.cards]

        if self._column.page is not None and update:
            self._column.update()

    def _setting_favorite_filter_button(self):
        self.favorite_filter_button.icon = ft.Icons.STAR_BORDER
        self.favorite_filter_button.selected_icon = ft.Icons.STAR
        self.favorite_filter_button.icon_color = ft.Colors.PRIMARY
        self.favorite_filter_button.selected_icon_color = ft.Colors.ON_PRIMARY
        self.favorite_filter_button.tooltip = "Показать только избранные"
        self.favorite_filter_button.on_click = self._toggle_favorite_filter
        self._update_favorite_filter_button()

    def _toggle_favorite_filter(self, e):
        self.show_only_favorites = not self.show_only_favorites
        self._update_favorite_filter_button()
        self.page.update()
        self.page.run_task(self._search)


    def _update_favorite_filter_button(self):
        self.favorite_filter_button.selected = self.show_only_favorites
        self.favorite_filter_button.tooltip = (
            "Показать все книги"
            if self.show_only_favorites
            else "Показать только избранные"
        )

    def _change_search_mode(self, e):
        if self.drow.value == "genres":
            self.search.content = ft.Row(
                controls=[self.genre_field, self.genre_button],
                tight=True,
            )
        else:
            self.search.content = self.text_search

        self.search.update()
        self.page.run_task(self._search)

    def _get_genre_menu_item(self, genre: str) -> ft.MenuItemButton:
        item = ft.MenuItemButton(
            content=ft.Text(genre),
            close_on_click=False,
        )
        item.on_click = lambda e, g=genre, i=item: self._toggle_genre(g, i)
        return item

    def _settings_genre_button(self):
        self.genre_button.controls.clear()
        for genre in BookGenre:
            self.genre_button.controls.append(self._get_genre_menu_item(genre.value))

    def _toggle_genre(self, genre: str, item: ft.MenuItemButton):
        if genre in self.selected_genres:
            self.selected_genres.remove(genre)
            item.leading = None
        else:
            self.selected_genres.add(genre)
            item.leading = ft.Icon(ft.Icons.CHECK, size=18)

        self.genre_field.value = ", ".join(sorted(self.selected_genres))
        self.genre_field.update()
        item.update()

    def _apply_genre_filter(self, e):
        self.page.run_task(self._search)

    def _settings_drow(self):
        self.drow.value = "name"
        self.drow.options.append(ft.DropdownOption(key="name", text="Название"))
        self.drow.options.append(ft.DropdownOption(key="description", text="Описание"))
        self.drow.options.append(ft.DropdownOption(key="author", text="Автор"))
        self.drow.options.append(ft.DropdownOption(key="series", text="Серия"))
        self.drow.options.append(ft.DropdownOption(key="genres", text="Жанры"))

    async def _search(self):
        search_key = self.drow.value
        search_value = (self.text_search.value or "").strip().casefold()
        selected_genres = {genre.casefold() for genre in self.selected_genres}

        ic(search_value, search_key, selected_genres)
        for card in self.cards:
            book = card.get_book()
            visible = True

            if self.show_only_favorites and not bool(getattr(book, "is_favorite", False)):
                visible = False
            elif search_key == "genres":
                if selected_genres:
                    book_genres = {
                        genre.strip().casefold()
                        for genre in (book.genres or "").split(",")
                        if genre.strip()
                    }
                    visible = selected_genres.issubset(book_genres)
            elif search_value:
                match search_key:
                    case "name":
                        title_source = book.title if isinstance(book.title, str) else " / ".join(book.title)
                        visible = search_value in title_source.strip().casefold()
                    case "author":
                        visible = search_value in (book.author or "").strip().casefold()
                    case "series":
                        visible = search_value in (book.series or "").strip().casefold()
                    case "description":
                        visible = search_value in (book.description or "").strip().casefold()
            card.change_visible(visible)
        self._sort_cards()



    def _app_bar_settings(self):
        self.app_bar.title = ft.Text("Менеджер Книг")
        self.app_bar.center_title = True
        self.app_bar.actions.append(ft.IconButton(icon = ft.Icons.LOGOUT, on_click=self.auth_logic.logout))


    def _get_books(self):
        """Запуск async загрузки"""
        self.page.run_task(self._load_books_async)

    def _on_favorite_change(self):
        self.page.run_task(self._search)

    def _on_delete_change(self, deleted_card: Book_cont):
        self.cards = [card for card in self.cards if card is not deleted_card]
        self._column.controls = [self.search_row, self.loader] + [card.cont for card in self.cards]

        if self._column.page is not None:
            self._column.update()

    def _on_progress_change(self):
        if self.sort_key == "progress":
            self._sort_cards()

    async def _load_books_async(self):
        books = await self.books_logic.get_books()
        if books is None:
            self.loader.visible = False
            self.page.update()
            return
        self.cards.clear()
        for index, book in enumerate(books):
            self.loader.value = (index + 1) / len(books)
            card = Book_cont(page=self.page)
            card.on_favorite_change = self._on_favorite_change
            card.on_delete_change = lambda deleted_card=card: self._on_delete_change(deleted_card)
            card.on_progress_change = self._on_progress_change

            cont_book = card.get_cont(
                title=book.title, description=book.description, index=book.id, cover=book.cover, data = book
            )

            cont_book.col = {ft.ResponsiveRowBreakpoint.XS: 6,
                             ft.ResponsiveRowBreakpoint.SM: 4,
                             ft.ResponsiveRowBreakpoint.MD: 3,
                             ft.ResponsiveRowBreakpoint.LG: 12
                             }

            self.cards.append(card)
            self._column.controls.append(cont_book)
            self._sort_cards()
            #self._column.update()
            self.loader.update()
            await asyncio.sleep(0.2)

        self.loader.visible = False
        self._sort_cards()
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
