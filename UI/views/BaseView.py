from typing import Iterable

import flet as ft
from abc import ABC, abstractmethod

from core.Logic.Auth import AuthLogic
from core.Logic.BooksLogic import BooksLogic
from core.Logic.ChaptersLogic import ChaptersLogic
from core.Http_Client.client import ApiClient
from core.state import AppState, MessageLevel
from core.Logic.UsersLogic import UsersLogic
from core.users.models import UserRole


class BaseView(ABC):
    """
    Базовый класс для всех View.
    - подписывается на AppState
    - обрабатывает ошибки
    """
    route: str = "/"
    requires_auth: bool = False
    allowed_roles: Iterable[UserRole] | None = None
    vert_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.START

    def __init__(self, page: ft.Page):
        self.page = page
        self.state: AppState = page.session.store.get("state")
        self.auth_logic: AuthLogic = page.session.store.get("auth")
        self.api : ApiClient = page.session.store.get("api")
        self.books_logic: BooksLogic = page.session.store.get("books_logic")
        self.chapters_logic: ChaptersLogic = page.session.store.get("chapters_logic")
        self.users_logic: UsersLogic = page.session.store.get("users_logic")

        self.modal_dialog = ft.AlertDialog(modal=False)
        self.info_dialog = ft.SnackBar(content=ft.Text(""))

        self.app_bar: ft.AppBar = ft.AppBar(bgcolor=ft.Colors.PRIMARY_CONTAINER)
        self.drawer = ft.NavigationDrawer()
        self.change_theme = ft.IconButton()
        self._change_theme_setting()
        self._drawer_settings()
        self._appbar_settings()


        # подписываемся на изменения state.message
        self.state.subscribe("message", self._on_message_change)



    def _on_message_change(self):
        """Логика отображения message"""
        ic()
        if self.state.message is not None:
            self._show_message(ic(self.state.message),
                               self.state.message_level)
            self.state.clear_message()

    def _get_pop_menu_item(self, color, text):
        def click():
            self.page.theme = ft.Theme(color_scheme_seed=color)
            self.page.update()
        item = ft.PopupMenuItem(content=ft.Row(
                    [
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=color),
                        ft.Text(text, color=color),
                    ]),on_click=click)
        return item



    def _get_popup_menu_button(self):
        button = ft.PopupMenuButton(icon=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=ft.Colors.PRIMARY),
                                    items =[
        self._get_pop_menu_item(color=ft.Colors.BLUE, text="Blue"),
        self._get_pop_menu_item(color=ft.Colors.DEEP_PURPLE, text="Deep purple"),
        self._get_pop_menu_item(color=ft.Colors.INDIGO, text="Indigo"),
        self._get_pop_menu_item(color=ft.Colors.GREEN, text="Green"),
        self._get_pop_menu_item(color=ft.Colors.YELLOW, text="Yellow"),
        self._get_pop_menu_item(color=ft.Colors.ORANGE, text="Orange"),
        ])
        return button

    def _change_theme_setting(self):
        def change_theme():
            if self.page.theme_mode == ft.ThemeMode.DARK:
               self.page.theme_mode = ft.ThemeMode.LIGHT
               self.change_theme.icon = ft.Icons.DARK_MODE_OUTLINED
            elif self.page.theme_mode == ft.ThemeMode.LIGHT:
                self.page.theme_mode = ft.ThemeMode.DARK
                self.change_theme.icon = ft.Icons.LIGHT_MODE_OUTLINED

        self.change_theme.icon = ft.Icons.LIGHT_MODE_OUTLINED if self.page.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE_OUTLINED
        self.change_theme.on_click = change_theme

    def _appbar_settings(self):
        self.app_bar.actions = [self.change_theme, self._get_popup_menu_button()]

    def _drawer_settings(self):
        self.drawer.bgcolor = ft.Colors.PRIMARY_CONTAINER
        if self.state.user is not None and self.state.user.role == UserRole.ADMIN:
            self.drawer.controls += self._get_drawer_destination("Админка")
        self.drawer.controls += self._get_drawer_destination("Список Книг")
        self.drawer.indicator_color = ft.Colors.PRIMARY_CONTAINER
        self.drawer.indicator_shape = ft.RoundedRectangleBorder()
        self.drawer.selected_index = 1
        self.drawer.on_change = self._change_drawer

    def _change_drawer(self, e):
        ic(e.data)
        match e.data:
            case 0:
                if self.state.user is not None and self.state.user.role == UserRole.ADMIN:
                    self.state.changes_route("/admin")
                else:
                    self.state.changes_route("/books")
            case 1:
                self.state.changes_route("/books")

    @staticmethod
    def _get_drawer_destination(label: str):
        return [ft.Container(height=12),
                ft.NavigationDrawerDestination(
                    label=label,
                    bgcolor=ft.Colors.ON_PRIMARY,
                ),
                ft.Divider(thickness=2, color=ft.Colors.ON_PRIMARY_CONTAINER)]

    def build(self) -> ft.View:
        """
        Финальный View.
        """
        return ft.View(
            route=self.route,
            bgcolor = ft.Colors.ON_PRIMARY,
            vertical_alignment=self.vert_alignment,
            horizontal_alignment=self.horizontal_alignment,
            controls=[self.build_content()],
            appbar = self.app_bar,
            drawer = self.drawer
        )

    @abstractmethod
    def build_content(self) -> ft.Control:
        """
        Контент конкретного экрана.
        """
        pass

    def _show_message(self, message: str, level: MessageLevel):
        ic()
        if level == MessageLevel.ERROR:
            bgcolor = ft.Colors.RED_700
        elif level == MessageLevel.WARNING:
            bgcolor = ft.Colors.ORANGE_700
        else:
            bgcolor = ft.Colors.BLUE_700

        self.modal_dialog.content = ft.Text(message, size=24, color=ft.Colors.ON_ERROR_CONTAINER)
        self.info_dialog.content = ft.Text(message, size=24, color=ft.Colors.ON_ERROR_CONTAINER)
        self.modal_dialog.bgcolor = bgcolor
        self.info_dialog.bgcolor = bgcolor
        try:
            if level == MessageLevel.INFO:
                self.page.show_dialog(self.info_dialog)
            else:
                self.page.show_dialog(self.modal_dialog)
        except RuntimeError as e:
            msg = e.args[0] if e.args else ""
            if not (isinstance(msg, str) and msg == "Dialog is already opened"):
                raise e
