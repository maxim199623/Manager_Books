import base64

import flet as ft

from Http_Client.client import ApiClient
from UI.get_element.button import get_button
from state import AppState, MessageLevel
from users.models import UserRole
from pathlib import Path


class Book_cont:
    def __init__(self, page):
        self.page = page
        self.cont = ft.Container()
        self.state: AppState = page.session.store.get("state")
        self.api: ApiClient = page.session.store.get("api")
        self.dialog_del = ft.AlertDialog(modal=True)
        self.loader = ft.ProgressBar(bar_height=10, border_radius=10, visible=False)

    def _settings_dialog_del(self, message:str , _id: int):
        self.dialog_del.title = ft.Text("Удаление пользователя")
        self.dialog_del.content = ft.Text(message)
        self.dialog_del.actions.clear()
        self.dialog_del.actions.append(get_button(text="Да", func_but=self.dial_button, button_name={"id": _id,"button_name":"del_yes"}))
        self.dialog_del.actions.append(get_button(text="Нет", func_but=self.dial_button, button_name={"id": _id,"button_name": "del_not"}))

    def _settings_cont(self, index):
        self.cont.border = ft.border.all(2, ft.Colors.BLACK26)
        self.cont.border_radius = 10
        self.cont.margin=10
        self.cont.padding=10
        self.cont.bgcolor = ft.Colors.ON_PRIMARY
        self.cont.on_hover=self.on_hover
        self.cont.data = index
        self.cont.on_click = self.click_book

        self.cont.animate_scale = ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)

    def _base_container(self, content=None, padding=10, height=None, width=None, expand=False):
        if self.page.web:
            border = None
        else:
            border = ft.border.all(2, ft.Colors.BLACK26)
        return ft.Container(
            border=border,
            padding=padding,
            alignment=ft.Alignment.CENTER,
            content=content,
            height=height,
            width=width,
            expand=expand
        )

    def _get_cont_title(self, title):
        cont_title = self._base_container(content = ft.Text(title, color=ft.Colors.PRIMARY, size=20),
                                          padding = 6, expand = True)
        return cont_title

    def _get_cont_description(self, description):
        cont_description = self._base_container(content = ft.Text(description, color=ft.Colors.PRIMARY),
                                                expand = True, height = 145)
        return cont_description

    def _get_cont_button(self, index):
        button_coll = ft.Column()
        button_coll.controls.append(self.loader)
        button_coll.controls.append(get_button(button_name=index, text="Скачать", func_but=self.load_button))
        if self.state.user.role == UserRole.ADMIN:
            button_coll.controls.append(get_button(button_name=index, text="Удалить", func_but=self.del_button))

        cont_button = self._base_container(height = 200, width = 200, padding = 20, content=button_coll)
        return cont_button

    def _get_elements(self, cover, title, description, index):
        if cover is None:
            cover = open("UI/views/view_books/cover.png", "rb").read()
        all_row = ft.Row(expand=True)
        data_column = ft.Column(alignment = ft.MainAxisAlignment.CENTER, expand=True)

        image = ft.Image(src=base64.b64encode(cover).decode("utf-8"), height=200, fit=ft.BoxFit.CONTAIN)
        cont_title = self._get_cont_title(title)
        cont_description = self._get_cont_description(description)
        cont_button = self._get_cont_button(index)

        data_column.controls = [cont_title,cont_description]
        all_row.controls = [image,data_column,cont_button]

        return all_row


    def get_cont(self, cover=None, title="None", description="None", index=None, data=None):
        self._settings_cont(index)
        elemen = self._get_elements(cover, title,description,index)
        self.cont.data = {"book":data,
                            "index":index}
        self.cont.content = elemen
        return self.cont


    def on_hover(self,e):
        """Наведение курсора на контейнер"""
        ic()
        ic(e)
        if e.data:
            e.control.scale = 1.01
            e.control.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLUE_GREY_300)
        else:
            e.control.shadow = None
            e.control.scale = 1.0
        e.control.update()

    def del_button(self, e):
        """Кнопка удаления книги"""
        ic()  # type: ignore
        ic(e.control.data)
        self._settings_dialog_del(message=f"Удалить пользователя {e.control.data}", _id=e.control.data)
        self.page.show_dialog(self.dialog_del)
        #TODO

    def dial_button(self, e):
        ic(e.control.data)
        match e.control.data["button_name"]:
            case "del_not":
                self.page.pop_dialog()
            case "del_yes":
                self.page.pop_dialog()
                self.page.run_task(self._del_book, e.control.data["id"])

    async def _del_book(self, _id):
        try:
           await self.api.delete_book(_id)
           self.cont.visible = False
           self.cont.update()
        except Exception as exc:
            self.state.notify(message=f"ошибка удаления Книги: {exc}", level=MessageLevel.ERROR)

    def load_button(self, e):
        """Кнопка для скачивания книги"""
        ic(e.control.data)  # type: ignore
        book = self.cont.data["book"]
        path = Path("output") / f"{book.title.replace(' / ', '_')}.{book.format}"
        if path.exists():
            self.state.notify(message=f"Файл уже скачен", level=MessageLevel.INFO)
            e.control.visible = False
            e.control.update()
        else:
            self.page.run_task(self.load_book,button=e.control, book=book, path=path)

    async def load_book(self, button, book, path):
        button.visible = False
        self.loader.visible = True
        button.update()
        self.loader.update()
        try:
            with open(path, "wb") as f:
                 f.write(book.file)
        finally:
            self.loader.visible = False
            self.loader.update()

    def click_book(self,e):
        """Нажатие на контейнер"""
        ic(e.control.data["index"])  # type: ignore
        self.state.select_book(book_id=e.control.data["index"], book=e.control.data["book"])



