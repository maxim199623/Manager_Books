import flet as ft

from core.Auth import AuthLogic
from UI.views.BaseView import BaseView

class LoginView(BaseView):
    """Класс-контроллер экрана авторизации."""

    route = "/login"
    requires_auth = False
    allowed_roles = None
    vert_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.CENTER

    def __init__(self, page: ft.Page, auth_logic: AuthLogic):
        super().__init__(page)

        self.auth_logic = auth_logic

        # -------- controls --------
        self.email  = self._get_text_field(label="Email")
        self.password = self._get_text_field(label="Password", password=True)
        self.login_button = self._get_button(text="Войти", func=self._on_login_click)
        self.loader = ft.ProgressRing(visible=False)



    @staticmethod
    def _get_text_field(label:str, width:int = 300, password:bool = False) -> ft.TextField:
        return ft.TextField(
            label=label,
            width=width,
            password=password,
            can_reveal_password=password,
            border_radius = 15
        )

    @staticmethod
    def _get_button(text:str, func):
        return ft.Button(
            text,
            on_click=func,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                color={
                    ft.ControlState.HOVERED: ft.Colors.SECONDARY,
                    ft.ControlState.FOCUSED: ft.Colors.ON_PRIMARY_CONTAINER,
                    ft.ControlState.DEFAULT: ft.Colors.PRIMARY,
                },
                bgcolor={
                    ft.ControlState.FOCUSED: ft.Colors.PRIMARY_CONTAINER,
                    ft.ControlState.DEFAULT: ft.Colors.ON_PRIMARY,
                },
            ),

        )


    def _get_collum(self):
        return ft.Column(
                    width=400,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "Авторизация",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                        self.email,
                        self.password,
                        self.login_button,
                        self.loader,
                    ],
                )


    def build_content(self) -> ft.Control:
        """
        Возвращает View для Router.
        """
        return ft.Container(
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                content=self._get_collum(),
                padding=10,
                border_radius = 30
                )

    async def _on_login_click(self, e):
        self._set_loading(True)
        try:
            await self.auth_logic.login(
                self.email.value,
                self.password.value,
            )
        finally:
            self._set_loading(False)

    def _set_loading(self, value: bool):
        self.loader.visible = value
        self.login_button.disabled = value
        self.page.update()