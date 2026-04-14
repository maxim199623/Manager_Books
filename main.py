import logging
from pathlib import Path

from UI.Router import Router
from core.Auth import AuthLogic
from core.Http_Client.client import ApiClient
from core.logging_setup import setup_logging
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
    ic()
    logger.info("логгер запущен")

def ui(page: ft.Page):
    page.title = "Book Manager"
    page.window.width = 1200
    page.window.height = 700
    page.window.min_width = 1200
    page.window.min_height = 400
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLUE

    state: AppState = AppState()
    url = f"https://{state.settings_API.address}:{state.settings_API.port}"
    api = ApiClient(url)

    page.session.store.set("state", state)
    page.session.store.set("auth", AuthLogic(state, api))
    page.session.store.set("api", api)

    load_fonts(page)

    router = Router(page)
    router.start()


def setting_parser(parser):
     parser.add_argument("--debug", action="store_true")
     parser.add_argument("--web", action="store_true")



def main():
    parser = argparse.ArgumentParser(description="Менеджер Книг")
    setting_parser(parser)
    args = parser.parse_args()

    apply_logger(debug=args.debug)

    if args.web:
        ft.app(target=ui, view = ft.AppView.WEB_BROWSER, port=8550, assets_dir="assets") # только браузер
    else:
        ft.run(ui, view=ft.AppView.FLET_APP, assets_dir="assets")  # только приложение


if __name__ == "__main__":
    main()



