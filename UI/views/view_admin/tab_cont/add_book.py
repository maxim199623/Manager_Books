import base64

import flet as ft

from UI.get_element.button import get_button
from UI.get_element.text_field import get_text_field
from core.epub.models import BookGenre


class Add_Book_Tab:
    def __init__(self, page):
        self.page = page
        self._built = False
        self.name = "Добавление книг"
        self.cont = ft.Container(expand=True)
        self.row = ft.ResponsiveRow(spacing=20,run_spacing=20)
        self.coll1 = ft.Column(expand=True)
        self.coll2 = ft.Column(expand=True)
        with open("assets/cover.png", "rb") as f:
            default_cover_base64 = base64.b64encode(f.read()).decode("utf-8")
        self.cover = ft.Image(src=f"data:image/png;base64,{default_cover_base64}")
        self.loader = ft.ProgressBar(bar_height = 10, border_radius=10, visible = False)
        self.genres = get_text_field(label="Жанры", field_name="genres", multiline=True)
        self.genres.read_only = True
        self.genres.expand = True
        self.button_genres = ft.SubmenuButton(content=ft.Icon(ft.Icons.ADD))
        self.selected_genres = set()

        self.title_field = None
        self.description_field = None


    def _selected_genres(self, genre, item, e):
        if genre in self.selected_genres:
            self.selected_genres.remove(genre)
            item.checked = False
            item.leading = None
        else:
            self.selected_genres.add(genre)
            item.leading = ft.Icon(ft.Icons.CHECK, size=18)
        self.genres.value=', '.join(self.selected_genres)
        self.genres.update()
        self.button_genres.update()


    def _get_popup_menu_item(self, genre):
        item = ft.MenuItemButton(genre, close_on_click=False)
        item.on_click = lambda e, g=genre, i=item: self._selected_genres(g, i, e)
        return item

    def _setting_button_genres(self):
        for genre in BookGenre:
            self.button_genres.controls.append(self._get_popup_menu_item(genre.value))


    def clear_field_error(self, field_name: str):
        field = self.title_field if field_name == "title" else self.description_field
        if field is not None:
            field.error = None
            field.update()

    def set_field_error(self, field_name: str, message: str):
        field = self.title_field if field_name == "title" else self.description_field
        if field is not None:
            field.error = message
            field.update()



    def _setting_coll1(self, func_field, func_but):
        self.coll1.alignment = ft.MainAxisAlignment.CENTER
        self.coll1.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.coll1.spacing = 20

        self.coll1.controls.append(self.loader)

        self.title_field = get_text_field(label="Название", func_field=func_field, field_name="title")
        self.description_field = get_text_field(label="Описание", func_field=func_field, field_name="description", multiline=True)

        self.coll1.controls.append(self.title_field)
        self.coll1.controls.append(get_text_field(label="Автор", func_field=func_field, field_name="author"))
        self.coll1.controls.append(get_text_field(label="Серия", func_field=func_field, field_name="series"))
        self.coll1.controls.append(get_text_field(label="Формат", func_field=func_field, field_name="format"))
        self.coll1.controls.append(self.description_field)
        self.genres.on_selection_change = func_field

        self._setting_button_genres()

        self.coll1.controls.append(ft.Row(controls=[self.genres, self.button_genres], expand=False,tight=True,))

        self.coll1.controls.append(get_button(text="Загрузить файл книги", func_but=func_but, button_name="load_book", width=90000))
        self.coll1.controls.append(get_button(text="Загрузить файл изображения", func_but=func_but, button_name="cover", width=90000))
        self.coll1.controls.append(get_button(text="Добавить книгу в БД", func_but=func_but, button_name="add_book", width=90000))

    def _setting_coll2(self):
        self.coll2.alignment = ft.MainAxisAlignment.CENTER
        self.coll2.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.coll2.controls.append(self.cover)

    def _setting_row(self):
        self.row.controls.append(ft.Container(self.coll1, col={ ft.ResponsiveRowBreakpoint.XS: 12,
                                                                ft.ResponsiveRowBreakpoint.MD: 6 }))
        self.row.controls.append(ft.Container(self.coll2, col={ft.ResponsiveRowBreakpoint.XS: 12,
                                                               ft.ResponsiveRowBreakpoint.MD: 6}))


    def _setting_container(self):
        self.cont.height = self.page.height * 1.00763 - 160
        self.cont.content = ft.Column(expand=True,
                                      scroll=ft.ScrollMode.AUTO,
                                      controls=[self.row])


    def change_cover(self, data:bytes):
        if data:
            b64 = base64.b64encode(data).decode("utf-8")
            self.cover.src = f"data:image/png;base64,{b64}"
            self.cover.update()

    def set_loading(self, value: bool):
        self.loader.visible = value
        self.loader.update()
        for c in self.coll1.controls:
            c.disabled = value
            c.update()

    def set_filed(self, book):
        ic()
        targets = {"title", "author", "series", "genres", "format", "description"}
        mapping = {
            "title": lambda b: ", ".join(b.title),
            "author": lambda b: b.author,
            "series": lambda b: b.series,
            "genres": lambda b: b.genres,
            "format": lambda b: b.format,
            "description": lambda b: b.description,
        }
        for c in self.coll1.controls:
            if c.data in targets:
                value = mapping[c.data](book)
                c.value = value
                c.update()

    def get_content(self, func_field, func_but) -> ft.Container:
        if not self._built:
            self._setting_coll1(func_field, func_but)
            self._setting_coll2()
            self._setting_row()
            self._setting_container()
            self._built = True
        return self.cont