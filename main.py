import logging
import sys
from pathlib import Path

from core.Http_Client.websocket_client import WebSocketClient
from UI.Router import Router
from core.Logic.Auth import AuthLogic
from core.Logic.BooksLogic import BooksLogic
from core.Logic.ChaptersLogic import ChaptersLogic
from core.Http_Client.client import ApiClient
from core.logging_setup import setup_logging
from core.Logic.UsersLogic import UsersLogic
import flet as ft

from core.state import AppState

import argparse

logger = logging.getLogger("app")

def load_fonts(page: ft.Page, fonts_dir="assets/fonts"):
    fonts = {}
    for file in Path(fonts_dir).glob("*.ttf"):
        font_name = file.stem
        fonts[font_name] = f"/fonts/{file.name}"
    page.fonts = fonts

def apply_logger(debug):
    setup_logging(debug=debug)
    logger.info("Логирование настроено", extra={"debug_mode": debug})

def ui(page: ft.Page):
    page.title = "Book Manager"
    page.window.width = 1200
    page.window.height = 700
    page.window.min_width = 1200
    page.window.min_height = 400
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    page.theme_mode = ft.ThemeMode.DARK


    state: AppState = AppState()
    ws = WebSocketClient(page=page, state=state)
    url = f"https://{state.settings_API.address}:{state.settings_API.port}"
    api = ApiClient(url)
    page.session.store.set("state", state)
    page.session.store.set("auth", AuthLogic(state, api, ws))
    page.session.store.set("api", api)
    page.session.store.set("books_logic", BooksLogic(state, api))
    page.session.store.set("chapters_logic", ChaptersLogic(state, api))
    page.session.store.set("users_logic", UsersLogic(state, api))

    router = Router(page)

    async def on_disconnect(e):
        await ws.close()

    def on_connect(e):
        router.start()
        if state.is_authenticated and api.token:
            page.run_task(ws.connect, api.token, api.base_url)

    load_fonts(page)


    page.on_disconnect = on_disconnect
    page.on_connect = on_connect
    router.start()


def setting_parser(parser):
     parser.add_argument("--debug", action="store_true")
     parser.add_argument("--web", action="store_true")

def get_assets_dir() -> str:
    if getattr(sys, "frozen", False):
        # запущено из exe
        return str(Path(sys.executable).resolve().parent / "assets")
    # обычный запуск из python
    return str(Path(__file__).resolve().parent / "assets")

def main():
    parser = argparse.ArgumentParser(description="Менеджер Книг")
    setting_parser(parser)
    args = parser.parse_args()
    apply_logger(debug=args.debug)
    if args.web:
        ft.app(target=ui, view = ft.AppView.WEB_BROWSER, port=8550, assets_dir=get_assets_dir()) # только браузер
    else:
        ft.run(ui, view=ft.AppView.FLET_APP, assets_dir=get_assets_dir())  # только приложение


if __name__ == "__main__":
    main()



