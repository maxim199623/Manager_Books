from typing import Iterable

import flet as ft
from abc import ABC, abstractmethod

from core.Auth import AuthLogic
from core.Http_Client.client import ApiClient
from core.state import AppState, MessageLevel
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

        self.modal_dialog = ft.AlertDialog(modal=False)

        self.app_bar: ft.AppBar = ft.AppBar(bgcolor=ft.Colors.PRIMARY_CONTAINER)
        self.drawer = ft.NavigationDrawer()
        self._drawer_settings()


        # подписываемся на изменения state.message
        self.state.subscribe("message", self._on_message_change)



    def _on_message_change(self):
        """Логика отображения message"""
        ic()
        if self.state.message is not None:
            self._show_message(ic(self.state.message),
                               self.state.message_level)
            self.state.clear_message()

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

        self.modal_dialog.content =ft.Text(message, size=24, color=ft.Colors.ON_ERROR_CONTAINER)
        self.modal_dialog.bgcolor = bgcolor
        try:
            self.page.show_dialog(self.modal_dialog)
        except RuntimeError as e:
            msg = e.args[0] if e.args else ""
            if not (isinstance(msg, str) and msg == "Dialog is already opened"):
                raise e