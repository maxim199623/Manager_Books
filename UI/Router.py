import flet as ft

from UI.views.view_books.books import BooksView
from UI.views.view_login.login import LoginView
from core.Auth import AuthLogic
from core.Http_Client.client import ApiClient
from core.state import AppState, MessageLevel


class Router:
    """
    связывает route → View
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.state: AppState = page.session.store.get("state")
        # инфраструктура
        url = f"https://{self.state.settings_API.address}:{self.state.settings_API.port}"
        api = ApiClient(url)
        auth_logic = AuthLogic(self.state, api)

        # registry маршрутов
        self.routes = {
            "/login": lambda: LoginView(page, auth_logic),
            "/books": lambda: BooksView(page),
        }
        self.page.on_route_change = self._on_route_changes

        # подписка на события state.router
        self.state.subscribe("route", self._set_route)

        # подписка на события state.is_authenticated
        self.state.subscribe("user", self._on_user_change)

    def start(self):
        """
        Точка входа в навигацию.
        """
        self.page.go("/login")

    def _set_route(self):
        route = ic(self.state.current_route)
        view_factory = ic(self.routes.get(route))
        view = view_factory()
        if ic(view.allowed_roles) is not None and ic(self.state.role) not in ic(view.allowed_roles):
            self.state.notify(
                "Недостаточно прав доступа",
                level=MessageLevel.WARNING,
            )
        else:
            self.page.go(self.state.current_route)

    def _on_user_change(self):
        if not self.state.is_authenticated:
            self.state.current_route = "/login"
            return
        self.state.changes_route("/books")




    def _on_route_changes(self, e):
        route = self.page.route

        view_factory = self.routes.get(route)
        if not view_factory:
            self.page.go("/login")
            return

        view = view_factory()

        self.page.views.clear()
        self.page.views.append(view.build())
        self.page.update()