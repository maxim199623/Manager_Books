import base64

import flet as ft

from UI.views.BaseView import BaseView
from state import MessageLevel
from users.models import UserRole

from UI.get_element.text_field import get_text_field

class ReadView(BaseView):

    route = "/read"
    requires_auth = True
    allowed_roles = [UserRole.USER, UserRole.ADMIN]
    vert_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.CENTER

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.drawer.visible = False
        self.page.on_resize = self._page_resize
        self._container = ft.Container(
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            padding=20,
            border_radius=30,
            height=self.page.height * 1.00763 - 96.193
        )
        self._pagelet = ft.Pagelet(content=ft.Container(alignment=ft.Alignment.CENTER),
                                   bgcolor=ft.Colors.ON_PRIMARY)

        self._pagelet_drawer = ft.NavigationDrawer(bgcolor = ft.Colors.PRIMARY_CONTAINER,
                                                   visible=False, on_change=self._change_drawer)
        self.current_chapter = None

        self.text_size = 15

        self.current_front = "JetBrainsMonoNerdFontMono-Italic"

        self._app_bar_settings()
        self._pagelet_settings()

    def _app_bar_settings(self):
        self.app_bar.title = ft.Text(self.state.current_book.title)
        self.app_bar.center_title = True
        self.app_bar.leading =ft.IconButton(icon = ft.Icons.ARROW_BACK, on_click=self.state.clear_selected_book)
        self.app_bar.actions = [ft.IconButton(icon = ft.Icons.LOGOUT, on_click=self.state.clear_user)]


    def _get_dropdown(self):
        drow = ft.Dropdown()
        drow.on_select = self._select_front
        for key in self.page.fonts.keys():
            drow.options.append(ft.DropdownOption(key))

        drow.value = self.current_front
        return drow

    def _select_front(self, e):
        ic(e.data)
        self.current_front = e.data
        new_content = self.get_chapter_description(self.current_chapter.description)
        self._pagelet.content.content = new_content
        self._pagelet.update()

    def _button_appbar(self):
        appbar = ft.AppBar()
        appbar.bgcolor =ft.Colors.PRIMARY_CONTAINER
        text_field = get_text_field(label="",func_field=self.set_size, width=100)
        text_field.value = str(self.text_size)
        text_field.max_length = 2

        appbar.actions = [ft.Text("Шрифт: ", size = 20),
                          self._get_dropdown(),
                            ft.Text("  ", size = 20),
                          ft.Text("Размер текста: ", size = 20),
                          text_field]
        return appbar

    def set_size(self,e):
        ic(e.data)
        new_size = 0
        if e.data == "":
            new_size = 0
        else:
            new_size = int(e.data)
        self.text_size = new_size
        if self.current_chapter is not None:
            new_content = self.get_chapter_description(self.current_chapter.description)
            self._pagelet.content.content = new_content
            self._pagelet.update()


    @staticmethod
    def _get_drawer_destination(label: str):
        return [ft.Container(height=12),
                ft.NavigationDrawerDestination(
                    label=label,
                    bgcolor=ft.Colors.ON_PRIMARY,
                ),
                ft.Divider(thickness=2, color=ft.Colors.ON_PRIMARY_CONTAINER)]

    async def get_chap(self):
        self._pagelet_drawer.controls.clear()
        try:
            capers_num = await self.api.get_chapters_num(self.state.current_book_id)
        except Exception as exc:
            self.state.notify(message=f"ошибка получения количества глав: {exc}", level=MessageLevel.ERROR)
        for caper in range(capers_num.chapters_count):
            self._pagelet_drawer.controls += self._get_drawer_destination(f"Глава {caper}")
        self._pagelet_drawer.visible = True
        self._pagelet_drawer.update()
        await self._get_chapter(0)

    async def _get_chapter(self, index):
        try:
            chapter = await self.api.get_chapter(self.state.current_book_id, index)
            self.current_chapter = chapter
            ic(chapter)
        except Exception as exc:
            self.state.notify(message=f"ошибка получения главы: {exc}", level=MessageLevel.ERROR)
        if chapter.chapter_name == "Постер":
            cover = self.state.current_book.cover
            if cover is not None:
                self._pagelet.content.content = ft.Image(src=base64.b64encode(cover).decode("utf-8"), fit=ft.BoxFit.CONTAIN)
        else:
            new_content = self.get_chapter_description(chapter.description)
            self._pagelet.content.content = new_content
        self._pagelet.update()

    def get_chapter_description(self, description):
        coll = ft.Column()
        coll.scroll=ft.ScrollMode.AUTO
        coll.margin=20
        for index, desc in enumerate(description):
            if index == 0:
                coll.controls.append(
                    ft.Container(
                        alignment=ft.Alignment.CENTER,
                        content = ft.Text(desc, size=self.text_size+15,
                                          text_align=ft.TextAlign.CENTER, font_family=self.current_front)
                    ))
            else:
                coll.controls.append(ft.Text(desc, size=self.text_size, font_family=self.current_front))
        return coll

    def _change_drawer(self, e):
        ic(e.data)
        self.page.run_task(self._get_chapter, e.data)


    def _pagelet_settings(self):
        self._pagelet.appbar=self._button_appbar()
        self.page.run_task(self.get_chap)
        self._pagelet.drawer=self._pagelet_drawer


    def _page_resize(self):
        ic(self.page.width, self.page.height)  # type: ignore
        self._container.height = ic(self.page.height * 1.00763 - 96.193)
        self._container.update()

    def build_content(self) -> ft.Control:
        """
        Возвращает View для Router.
        """
        ic()
        cont = self._container
        cont.content = self._pagelet
        return cont