import logging
from UI.Router import Router
from core.logging_setup import setup_logging
import flet as ft

from core.state import AppState

logger = logging.getLogger("app")

def apply_logger():
    setup_logging(debug=False)
    ic()
    logger.info("логгер запущен")

def ui(page: ft.Page):
    page.title = "Book Manager"
    page.window_width = 600
    page.window_height = 400
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLUE

    page.session.store.set("state", AppState())

    router = Router(page)
    router.start()

def main():
    apply_logger()
    #ft.app(target=ui, view = ft.AppView.WEB_BROWSER, port=8550) # только браузер
    #ft.app(target=ui, view = ft.AppView.FLET_APP_WEB, port=8550) #  браузер и приложение
    ft.app(target=ui, view = ft.AppView.FLET_APP) #  только приложение

if __name__ == "__main__":
    main()



