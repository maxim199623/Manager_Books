import flet as ft

from UI.get_element.button import get_button
from UI.get_element.text_field import get_text_field


class Add_Book_Tab:
    def __init__(self, page):
        self.page = page
        self._built = False
        self.name = "Добавление книг"
        self.cont = ft.Container(expand=True)
        self.row = ft.Row(expand=True)
        self.coll1 = ft.Column(expand=True)
        self.coll2 = ft.Column(expand=True)
        self.cover = ft.Image(src=open("UI/views/view_books/cover.png", "rb").read())
        self.loader = ft.ProgressBar(bar_height = 10, border_radius=10, visible = False)


    def _setting_coll1(self, func_field, func_but):
        self.coll1.alignment = ft.MainAxisAlignment.CENTER
        self.coll1.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.coll1.scroll = ft.ScrollMode.AUTO
        self.coll1.spacing = 20

        self.coll1.controls.append(self.loader)

        self.coll1.controls.append(get_text_field(label="Название", func_field=func_field, field_name="title"))
        self.coll1.controls.append(get_text_field(label="Автор", func_field=func_field, field_name="author"))
        self.coll1.controls.append(get_text_field(label="Серия", func_field=func_field, field_name="series"))
        self.coll1.controls.append(get_text_field(label="Формат", func_field=func_field, field_name="format"))
        self.coll1.controls.append(get_text_field(label="Описание", func_field=func_field, field_name="description", multiline=True))

        self.coll1.controls.append(get_button(text="Загрузить файл книги", func_but=func_but, button_name="load_book", width=90000))
        self.coll1.controls.append(get_button(text="Загрузить файл изображения", func_but=func_but, button_name="cover", width=90000))
        self.coll1.controls.append(get_button(text="Добавить книгу в БД", func_but=func_but, button_name="add_book", width=90000))

    def _setting_coll2(self):
        self.coll2.alignment = ft.MainAxisAlignment.CENTER
        self.coll2.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.coll2.scroll = ft.ScrollMode.AUTO
        self.coll2.controls.append(self.cover)

    def _setting_row(self):
        self.row.controls.append(self.coll1)
        self.row.controls.append(self.coll2)

    def _setting_container(self):
        self.cont.height = self.page.height * 1.00763 - 160
        self.cont.content=self.row

    def change_cover(self, data:bytes):
        self.cover.src = data
        self.cover.update()

    def set_loading(self, value: bool):
        self.loader.visible = value
        self.loader.update()
        for c in self.coll1.controls:
            c.disabled = value
            c.update()

    def set_filed(self, book):
        targets = {"title", "author", "series", "format", "description"}
        mapping = {
            "title": lambda b: ", ".join(b.title),
            "author": lambda b: b.author,
            "series": lambda b: b.series,
            "format": lambda b: b.file_format,
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