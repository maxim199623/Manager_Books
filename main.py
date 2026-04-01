import logging
from UI.Router import Router
from core.Auth import AuthLogic
from core.Http_Client.client import ApiClient
from core.logging_setup import setup_logging
import flet as ft

from core.state import AppState

logger = logging.getLogger("app")

def apply_logger():
    setup_logging(debug=True)
    ic()
    logger.info("логгер запущен")

def ui(page: ft.Page):
    page.title = "Book Manager"
    page.window.width = 900
    page.window.height = 700
    page.window.min_width = 700
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

    router = Router(page)
    router.start()

def main():
    apply_logger()
    #ft.app(target=ui, view = ft.AppView.WEB_BROWSER, port=8550) # только браузер
    #ft.app(target=ui, view = ft.AppView.FLET_APP_WEB, port=8550) #  браузер и приложение
    ft.run(ui, view = ft.AppView.FLET_APP) #  только приложение

if __name__ == "__main__":
    main()



