import base64
from datetime import datetime, timedelta

import flet as ft

from core.BooksLogic import BooksLogic
from core.ChaptersLogic import ChaptersLogic
from UI.get_element.button import get_button
from core.state import AppState
from core.MessageLevel import MessageLevel
from core.users.models import UserRole


class Book_cont:
    def __init__(self, page):
        self.page = page
        self.cont = ft.Container(expand=False)
        self.state: AppState = page.session.store.get("state")
        self.books_logic: BooksLogic = page.session.store.get("books_logic")
        self.chapters_logic: ChaptersLogic = page.session.store.get("chapters_logic")
        self.dialog_del = ft.AlertDialog(modal=True)
        self.loader = ft.ProgressBar(bar_height=10, border_radius=10, visible=False)

        self.full_view = ft.Container(visible=True, expand=True)
        self.min_view = ft.Container(visible=False, expand=True)

        self.cont.content = ft.Stack([self.full_view, self.min_view], expand=True)
        self.file_picker = ft.FilePicker()
        self.book = None
        self.is_build = False
        self.is_chapers= False
        self.favorite_button = ft.IconButton()
        self.favorite_button_min=ft.IconButton()
        self.on_favorite_change = None
        self.read_progress = 0.0
        self.on_progress_change = None

    def get_read_progress(self):
        return self.read_progress


    def _is_favorite(self):
        return bool(getattr(self.book, "is_favorite", False))

    def _setting_favorite_button(self, button):
        button.icon =ft.Icons.STAR_BORDER
        button.selected_icon = ft.Icons.STAR
        button.icon_color = ft.Colors.PRIMARY
        button.selected_icon_color = ft.Colors.ON_PRIMARY
        button.tooltip="Убрать из избранного" if self._is_favorite() else "Добавить в избранное"
        button.on_click=self._favorite_click_async

    async def _favorite_click_async(self,e):
        success = False
        if self._is_favorite():
            success = await self.books_logic.unfavorite_book(self.book.id)
            if success:
                self.book.is_favorite = False
                self.state.notify(message=f"Книга «{self.book.title}» удалена из избранного.", level=MessageLevel.INFO)
        else:
            success = await self.books_logic.favorite_book(self.book.id)
            if success:
                self.book.is_favorite = True
                self.state.notify(message=f"Книга «{self.book.title}» добавлена в избранное.", level=MessageLevel.INFO)

        if not success:
            return

        self.cont.data["book"] = self.book
        self._update_favorite_buttons()
        if self.on_favorite_change is not None:
            self.on_favorite_change()

    def _update_favorite_buttons(self):
        is_favorite = self._is_favorite()
        tooltip = "Убрать из избранного" if is_favorite else "Добавить в избранное"

        for button in (self.favorite_button, self.favorite_button_min):
            if button is not None:
                button.selected = is_favorite
                button.tooltip = tooltip
                if self.is_build and button.page is not None:
                    button.update()

    def _settings_dialog_del(self, message:str , _id: int):
        self.dialog_del.title = ft.Text("Удаление")
        self.dialog_del.content = ft.Text(message)
        self.dialog_del.actions.clear()
        self.dialog_del.actions.append(get_button(text="Да", func_but=self.dial_button, button_name={"id": _id,"button_name":"del_yes"}))
        self.dialog_del.actions.append(get_button(text="Нет", func_but=self.dial_button, button_name={"id": _id,"button_name": "del_not"}))

    def _settings_cont(self, index, book):
        if book.created_at >= datetime.now() - timedelta(days=3):
            self.cont.border = ft.border.all(2, ft.Colors.PRIMARY)
        else:
            self.cont.border = ft.border.all(2, ft.Colors.ON_PRIMARY)
        self.cont.border_radius = 10
        self.cont.margin=10
        self.cont.padding=10
        self.cont.bgcolor = ft.Colors.ON_PRIMARY
        self.cont.on_hover=self.on_hover
        self.cont.data = {"index": index,
                          "book":book}
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
        if self.book.file is not None:
            button_coll.controls.append(get_button(button_name=index, text="Скачать", func_but=self.load_button))
        if self.state.user.role == UserRole.ADMIN:
            button_coll.controls.append(get_button(button_name=index, text="Удалить", func_but=self.del_button))

        cont_button = self._base_container(height = 200, width = 200, padding = 20, content=button_coll)
        return cont_button

    def _get_elements(self, cover, title, description, index):
        if cover is None:
            cover = open("UI/views/view_books/cover.png", "rb").read()
        all_colum = ft.Column()
        all_row = ft.Row(expand=True)
        data_column = ft.Column(alignment = ft.MainAxisAlignment.CENTER, expand=True)

        image_cover = ft.Image(src=base64.b64encode(cover).decode("utf-8"), height=200, fit=ft.BoxFit.CONTAIN)
        self._setting_favorite_button(self.favorite_button)
        self._update_favorite_buttons()
        image = ft.Container(height=200, content=ft.Stack(controls=[image_cover, self.favorite_button]))
        cont_title = self._get_cont_title(title)
        cont_description = self._get_cont_description(description)
        cont_button = self._get_cont_button(index)

        progressbar = ft.ProgressBar()
        self.page.run_task(self.get_progressbar, index=index, progressbar=progressbar)

        data_column.controls = [cont_title,cont_description]
        all_row.controls = [image,data_column,cont_button]
        all_colum.controls = [progressbar, all_row]

        return all_colum

    async def get_progressbar(self, index, progressbar):
        full = await self.chapters_logic.get_chapters_num(index)
        read = await self.chapters_logic.get_count_read_chapters_in_book(index)
        if full is None or read is None:
            progressbar.visible = False
            self.is_chapers = False
            self.read_progress = 0.0
            if self.is_build:
                progressbar.update()
            return

        if full.chapters_count == 0:
            progressbar.visible = False
            self.is_chapers = False
            self.read_progress = 0.0
        else:
            self.read_progress = read.read_chapters / full.chapters_count
            progressbar.value = self.read_progress
            self.is_chapers = True

        if self.on_progress_change is not None:
            self.on_progress_change()

        if self.is_build:
            progressbar.update()


    def _get_min_elements(self, cover, title,description, index):
        if cover is None:
            cover = open("cover.png", "rb").read()
        all_row = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,  tight=True,)
        image_cover = ft.Image(src=base64.b64encode(cover).decode("utf-8"), height=200, fit=ft.BoxFit.CONTAIN)
        self._setting_favorite_button(self.favorite_button_min)
        self._update_favorite_buttons()
        image = ft.Container(height=200, content=ft.Stack(controls=[image_cover, self.favorite_button_min]))
        des = ft.Container(alignment=ft.Alignment.BOTTOM_LEFT,padding=12)
        des.content = ft.Column(tight=True, spacing=4, controls=[
            ft.Text(title,max_lines=2,weight=ft.FontWeight.BOLD,color=ft.Colors.PRIMARY, overflow=ft.TextOverflow.ELLIPSIS)
        ])

        progressbar = ft.ProgressBar()
        self.page.run_task(self.get_progressbar, index=index, progressbar=progressbar)

        button = ft.Row(expand=True, alignment=ft.MainAxisAlignment.SPACE_AROUND,)
        if self.book.file is not None:
            button.controls.append(ft.IconButton(icon=ft.Icons.DOWNLOAD, on_click=self.load_button, data=index))
        if self.state.user.role == UserRole.ADMIN:
            button.controls.append(ft.IconButton(icon=ft.Icons.DELETE_FOREVER_ROUNDED, on_click=self.del_button, data=index))
        all_row.controls = [progressbar, image, des, button]
        return all_row

    def get_cont(self, cover=None, title="None", description="None", index=None, data=None):
        self.book = data
        self._settings_cont(index, data)
        self.full_view.content = self._get_elements(cover, title, description, index)
        self.min_view.content = self._get_min_elements(cover, title, description, index)
        self.apply_mode()
        self.is_build = True
        return self.cont

    def get_book(self):
        return self.book

    def change_visible(self, visible:bool = True):
        self.cont.visible = visible
        self.cont.update()

    def apply_mode(self):
        ic()
        is_small = self.page.width <= 992
        ic(is_small)
        self.full_view.visible = not is_small
        self.min_view.visible = is_small


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
        book = e.control.data if self.book is None else self.book.title
        self._settings_dialog_del(message=f"Удалить книгу {book}", _id=e.control.data)
        self.page.show_dialog(self.dialog_del)

    def dial_button(self, e):
        ic(e.control.data)
        match e.control.data["button_name"]:
            case "del_not":
                self.page.pop_dialog()
            case "del_yes":
                self.page.pop_dialog()
                self.page.run_task(self._del_book, e.control.data["id"])

    async def _del_book(self, _id):
        if await self.books_logic.delete_book(_id):
           pass

    async def load_button(self, e):
        """Кнопка для скачивания книги"""
        ic(e.control.data)  # type: ignore
        book = self.cont.data["book"]
        button = e.control
        button.visible = False
        self.loader.visible = True
        button.update()
        self.loader.update()
        try:
            await self.file_picker.save_file(
            dialog_title="Сохранить файл",
            file_name=f"{book.title.replace(' / ', '_')}.{book.format}",
            src_bytes=book.file
            )
        finally:
            self.loader.visible = False
            button.visible = True
            button.update()
            self.loader.update()

    def click_book(self,e):
        """Нажатие на контейнер"""
        ic(e.control.data["index"])  # type: ignore
        if self.is_chapers:
            self.state.select_book(book_id=e.control.data["index"], book=e.control.data["book"])
        else:
            self.state.notify(message=f"Для этой книги нет загруженных глав.", level=MessageLevel.INFO)



