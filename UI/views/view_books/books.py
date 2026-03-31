import flet as ft

from UI.views.BaseView import BaseView
from core.users.models import UserRole


class BooksView(BaseView):

    route = "/books"
    requires_auth = True
    allowed_roles = [UserRole.USER, UserRole.ADMIN]
    vert_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.CENTER

    def __init__(self, page: ft.Page):
        super().__init__(page)


    def build_content(self) -> ft.Control:
        """
        Возвращает View для Router.
        """
        return ft.Container(
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                padding=10,
                border_radius = 30
                )