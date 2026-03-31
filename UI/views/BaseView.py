from typing import Iterable

import flet as ft
from abc import ABC, abstractmethod
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

        self._snack_bar = ft.SnackBar(
            content=ft.Text(""),
        )
        self.page.snack_bar = self._snack_bar

        # подписываемся на изменения state.message
        self.state.subscribe("message", self._on_message_change)


    def _on_message_change(self):
        """Логика отображения message"""
        ic()
        if self.state.message is not None:
            self._show_message(ic(self.state.message),
                               self.state.message_level)
            self.state.clear_message()


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

        self._snack_bar.content = ft.Text(message, size=24, color=ft.Colors.ON_ERROR_CONTAINER)
        self._snack_bar.bgcolor = bgcolor

        try:
            self.page.show_dialog(self._snack_bar)
        except RuntimeError as e:
            msg = e.args[0] if e.args else ""
            if not (isinstance(msg, str) and msg == "Dialog is already opened"):
                raise e