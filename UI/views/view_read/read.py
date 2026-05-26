import base64
import re

import flet as ft

from UI.get_element.button import get_button
from UI.views.BaseView import BaseView
from core.state import MessageLevel
from core.users.models import UserRole

from UI.get_element.text_field import get_text_field
from markdownify import markdownify as md

from bs4 import BeautifulSoup, NavigableString, Tag, Comment


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

        self.dialog_del = ft.AlertDialog(modal=True)
        self._app_bar_settings()
        self._pagelet_settings()

    def _settings_dialog_del(self, message:str , _id: int):
        self.dialog_del.title = ft.Text("Удаление")
        self.dialog_del.content = ft.Text(message)
        self.dialog_del.actions.clear()
        self.dialog_del.actions.append(get_button(text="Да", func_but=self.dial_button, button_name={"id": _id,"button_name":"del_yes"}))
        self.dialog_del.actions.append(get_button(text="Нет", func_but=self.dial_button, button_name={"id": _id,"button_name": "del_not"}))

    def _app_bar_settings(self):
        self.app_bar.title = ft.Text(self.state.current_book.title if self.state.current_book is not None else " ")
        self.app_bar.center_title = True
        self.app_bar.leading = ft.IconButton(icon = ft.Icons.ARROW_BACK, on_click=self.state.clear_selected_book)
        self.app_bar.actions.append(ft.IconButton(icon = ft.Icons.LOGOUT, on_click=self.auth_logic.logout))


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
        appbar.actions = self._build_appbar_actions()

        return appbar

    def _build_appbar_actions(self):
        ic()
        text_field = get_text_field(label="", func_field=self.set_size, width=100)
        text_field.value = str(self.text_size)
        text_field.max_length = 2
        if self.page.width < 992:
            return [
                ft.PopupMenuButton(menu_position=ft.PopupMenuPosition.UNDER,
                                   items=[ft.PopupMenuItem(content=self._get_dropdown()),
                                          ft.PopupMenuItem(content=text_field),
                                          ft.PopupMenuItem(content=ft.IconButton(icon=ft.Icons.DELETE_FOREVER_OUTLINED, on_click=self._cler_history))
                                        ]
                                   )
                ]
        else:
            return [ft.Text("Шрифт: ", size = 20),
                          self._get_dropdown(),
                            ft.Text("  ", size = 20),
                          ft.Text("Размер текста: ", size = 20),
                          text_field,
                    ft.Text("  ", size = 20),
                    ft.IconButton(icon=ft.Icons.DELETE_FOREVER_OUTLINED, on_click=self._cler_history)]

    def _cler_history(self, e):
        self._settings_dialog_del(message="Очистить Историю?", _id=0)
        self.page.show_dialog(self.dialog_del)

    def dial_button(self, e):
        ic(e.control.data)
        match e.control.data["button_name"]:
            case "del_not":
                self.page.pop_dialog()
            case "del_yes":
                self.page.pop_dialog()
                self.page.run_task(self.__cler_history)


    async def __cler_history(self):
        if not await self.chapters_logic.delete_history_read_chapters_in_book(self.state.current_book_id):
            return

        controls = self._pagelet_drawer.controls
        for c in controls:
            if isinstance(c, ft.NavigationDrawerDestination):
                c.icon = ft.Icons.CHROME_READER_MODE_OUTLINED

        self._pagelet_drawer.selected_index = 0
        await self._get_chapter(0)
        self._pagelet_drawer.update()



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
    def _get_drawer_destination(label: str, read=False):
        return [ft.Container(height=12),
                ft.NavigationDrawerDestination(
                    label=label,
                    bgcolor=ft.Colors.ON_PRIMARY,
                    icon = ft.Icons.CHROME_READER_MODE_ROUNDED if read else ft.Icons.CHROME_READER_MODE_OUTLINED
                ),
                ft.Divider(thickness=2, color=ft.Colors.ON_PRIMARY_CONTAINER)]

    async def get_chap(self):
        self._pagelet_drawer.controls.clear()
        capers_num = await self.chapters_logic.get_chapters_num(self.state.current_book_id)
        history = await self.get_history()
        if capers_num is None or history is None:
            return

        for caper in range(capers_num.chapters_count):
            read = caper in history
            self._pagelet_drawer.controls += self._get_drawer_destination(label=f"Глава {caper}", read=read)
        self._pagelet_drawer.selected_index = history[-1] if history != [] else 0
        self._pagelet_drawer.visible = True
        self._pagelet_drawer.update()

        await self._get_chapter(history[-1] if history != [] else 0)

    async def get_history(self):
        history = await self.chapters_logic.get_read_chapters_in_book(self.state.current_book_id)
        if history is None:
            return None
        ic(sorted(history))
        return sorted(history)


    async def _get_chapter(self, index):
        chapter = await self.chapters_logic.get_chapter(self.state.current_book_id, index)
        if chapter is None:
            return
        self.current_chapter = chapter
        if chapter.chapter_name == "Постер":
            cover = self.state.current_book.cover
            if cover is not None:
                self._pagelet.content.content = ft.Image(src=base64.b64encode(cover).decode("utf-8"), fit=ft.BoxFit.CONTAIN)
        else:
            new_content = self.get_chapter_description(chapter.description)
            self._pagelet.content.content = new_content
        self._pagelet.update()

    @staticmethod
    def _parser(description):
        html = description.replace("&#13;", "").replace("\r", "")
        soup = BeautifulSoup(html, "html5lib")
        for p in soup.find_all("p"):
            tags = [c for c in p.children if isinstance(c, Tag)]
            if tags and all(t.name == "i" for t in tags):
                parts = [" ".join(t.get_text().split()) for t in p.find_all("i")]
                text = " ".join(x for x in parts if x)
                text = " ".join(text.split())
                p.clear()
                p.append(soup.new_tag("i"))
                p.i.string = text
        for node in soup.find_all(string=True):
            if isinstance(node, NavigableString) and getattr(node.parent, "name", None) not in ("script", "style"):
                node.replace_with(" ".join(str(node).split()))
        for p in soup.find_all("p"):
            t = " ".join(p.get_text().split())
            if t.startswith("[") and t.endswith("]") and not p.find("i"):
                p.clear()
                p.append(soup.new_tag("i"))
                p.i.string = t
        return str(soup.body or soup)

    @staticmethod
    def _fix_markdown_brackets(markdown: str) -> str:
        def fix_line(line: str) -> str:
            if "[" not in line or "]" not in line or "](" in line:
                return line
            return re.sub(
                r"\[([^\]]*)\]",
                lambda m: "\uff3b " + m.group(1).strip() + " \uff3d",
                line,
            )
        return "\n".join(fix_line(line) for line in markdown.split("\n"))

    def get_chapter_description(self, description):
        coll = ft.Column()
        coll.scroll=ft.ScrollMode.AUTO
        coll.margin=20
        html = self._parser(description)
        markdown = self._fix_markdown_brackets(md(html,
                                                  wrap=False,
                                                  heading_style="ATX",
                                                  bullets="-"))

        body =ft.TextStyle(
                        size=self.text_size,
                        font_family=self.current_front,
                        height=1.6,
                    )
        system = body.copy(italic=False, color=ft.Colors.SECONDARY)

        center = ft.MainAxisAlignment.CENTER
        quote = body.copy(italic=True, color=ft.Colors.ON_PRIMARY_CONTAINER)
        md_style_sheet = ft.MarkdownStyleSheet(p_text_style=body,
                                               h1_text_style=body.copy(size=self.text_size + 12, weight=ft.FontWeight.BOLD),
                                               h1_alignment=center,
                                               h2_text_style=body.copy(size=self.text_size + 6, weight=ft.FontWeight.BOLD),
                                               h2_alignment=center,
                                               h3_text_style=body.copy(size=self.text_size + 4, weight=ft.FontWeight.W_600),
                                               h3_alignment=center,
                                               em_text_style=system,
                                               strong_text_style=body.copy(weight=ft.FontWeight.BOLD),
                                               blockquote_text_style=quote,
                                               blockquote_alignment=ft.MainAxisAlignment.START,
                                               blockquote_padding=ft.Padding.only(left=16, top=12, right=16, bottom=12),
                                               blockquote_decoration=ft.BoxDecoration(
                                                   bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                                   border=ft.Border.only(
                                                       left=ft.BorderSide(width=4, color=ft.Colors.PRIMARY),
                                                   ),
                                               ),
                                               block_spacing=10,
                                               p_padding=ft.padding.only(bottom=8)
                                               )
        coll.controls.append(ft.Markdown(
            value=markdown,
            soft_line_break=False,
            selectable=True,
            fit_content=False,
            extension_set=ft.MarkdownExtensionSet.COMMON_MARK,
            md_style_sheet=md_style_sheet
        ))
        return coll

    def _change_drawer(self, e):
        ic(e.data)
        ic(type(e.control.controls))
        cunt = [c for c in e.control.controls if isinstance(c, ft.NavigationDrawerDestination)]
        cunt[e.data].icon = ft.Icons.CHROME_READER_MODE_ROUNDED
        self._pagelet_drawer.update()
        self.page.run_task(self._get_chapter, e.data)

    def _pagelet_settings(self):
        self._button_appbar()
        self._pagelet.appbar=self._button_appbar()
        self.page.run_task(self.get_chap)
        self._pagelet.drawer=self._pagelet_drawer


    def _page_resize(self):
        ic(self.page.width, self.page.height)  # type: ignore
        self._container.height = ic(self.page.height * 1.00763 - 96.193)
        self._pagelet.appbar = self._button_appbar()
        self.page.update()

    def build_content(self) -> ft.Control:
        """
        Возвращает View для Router.
        """
        ic()
        cont = self._container
        cont.content = self._pagelet
        return cont
