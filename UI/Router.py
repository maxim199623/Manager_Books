import flet as ft

from UI.views.view_admin.admin import AdminView
from UI.views.view_books.books import BooksView
from UI.views.view_login.login import LoginView
from UI.views.view_read.read import ReadView
from core.state import AppState, MessageLevel


class Router:

    def __init__(self, page: ft.Page):
        self.page = page
        self.state: AppState = page.session.store.get("state")

        # registry маршрутов
        self.routes = {
            "/login": lambda: LoginView(page),
            "/books": lambda: BooksView(page),
            "/admin": lambda: AdminView(page),
            "/read": lambda: ReadView(page)
        }
        self.page.on_route_change = self._on_route_changes
        self.page.on_view_pop = self._on_view_pop

        # подписка на события state.router
        self.state.subscribe("route", self._state_route_change)

        # подписка на события state.is_authenticated
        self.state.subscribe("user", self._on_user_change)

        # подписка на события state.current_book_id
        self.state.subscribe("book", self._on_book_change)

    def start(self):
        """Запуск приложения"""
        self.restore_from_url()

    def restore_from_url(self):
        route = self.page.route or self.state.current_route or "/login"
        self._navigate_to(route)

    def _navigate_to(self, route: str):
        """Смена страницы"""
        if route not in self.routes:
            route = "/login"
        self.state.current_route = route

        if self.page.route == route:
            self._render_route(route)
        else:
            self.page.go(route)


    def _check_role(self, view) -> bool:
        if ic(view.allowed_roles) is not None and ic(self.state.role) not in ic(view.allowed_roles):
            return False
        else:
            return True

    def _on_user_change(self):
        ic()
        if self.state.is_authenticated:
            self.state.changes_route("/books")
        else:
            self.state.changes_route("/login")

    def _on_book_change(self):
        if self.state.current_book_id is not None and self.state.is_authenticated:
            self.state.changes_route("/read")
        else:
            self.state.changes_route("/books")



    def _render_route(self, route: str):
        view_factory = self.routes.get(route)
        if not view_factory:
            self.page.go("/login")
            return

        view = view_factory()

        if not self._check_role(view):
            self.state.notify(
                "Нет доступа к этому разделу.",
                level=MessageLevel.WARNING,
            )
            self.page.go("/books" if self.state.is_authenticated else "/login")
            return

        self.page.views.clear()
        self.page.views.append(view.build())
        self.page.update()

    def _on_route_changes(self, e: ft.RouteChangeEvent):
        route = e.route or "/"
        ic(f"Переход на: {route}")
        self.state.current_route = route

        view_factory = self.routes.get(route)
        if not view_factory:
            self.page.go("/login")
            return

        self.state.current_route = route
        self._render_route(route)

    def _on_view_pop(self, e: ft.ViewPopEvent):
        """Обработка кнопки Назад"""
        self.page.views.pop()
        top_view = self.page.views[-1]
        self.page.go(top_view.route)

    def _state_route_change(self):
        """Обработка смены маршрута"""
        self._navigate_to(self.state.current_route)