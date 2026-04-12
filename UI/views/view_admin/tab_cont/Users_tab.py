import flet as ft
from pydantic import ValidationError

from Http_Client.client import ApiClient
from core.Http_Client.schemas.users import UserRead, UserRole, UserCreate, UserPatch
from UI.get_element.button import get_button
from UI.get_element.text_field import get_text_field
from state import AppState, MessageLevel


class Users_Tab:
    def __init__(self, page):
        self.page = page
        self.api : ApiClient = page.session.store.get("api")
        self.state: AppState = page.session.store.get("state")
        self._built = False
        self.cont = ft.Container(expand=True)
        self.coll = ft.Column(expand=True)
        self.loader = ft.ProgressBar(bar_height=10, border_radius=10, visible=False)
        self.table = ft.DataTable(expand=True, columns=[])

        self.dialog_del = ft.AlertDialog(modal=True)

        self.dialog_change_user = ft.AlertDialog(modal=True)

        self.new_user = {"email": None,
                        "role": None,
                        "password": None}

    def _settings_dialog_del(self, message:str , user_id: int):
        self.dialog_del.title = ft.Text("Удаление пользователя")
        self.dialog_del.content = ft.Text(message)
        self.dialog_del.actions.clear()
        self.dialog_del.actions.append(get_button(text="Да", func_but=self._func_but, button_name={"id": user_id,"button_name":"del_yes"}))
        self.dialog_del.actions.append(get_button(text="Нет", func_but=self._func_but, button_name={"id": user_id,"button_name": "del_not"}))

    def _settings_dialog_change_user(self, message: str, user_id: int):
        self.dialog_change_user.title = ft.Text("Изменение пользователя")
        coll = ft.Column()
        coll.controls.append(ft.Text(message))
        coll.controls.append(
            get_text_field(label="email", func_field=self._func_field, field_name="email", width=250))
        coll.controls.append(
            ft.Dropdown(label="role", on_select=self._func_field, data="role", width=120, options=[
                ft.DropdownOption(key=UserRole.USER, text=UserRole.USER),
                ft.DropdownOption(key=UserRole.ADMIN, text=UserRole.ADMIN)
            ]))
        coll.controls.append(
            get_text_field(label="password", func_field=self._func_field, field_name="password", width=250, password=True))
        self.dialog_change_user.content = coll
        self.dialog_change_user.actions.clear()
        self.dialog_change_user.actions.append(
            get_button(text="Да", func_but=self._func_but, button_name={"id": user_id, "button_name": "change_yes"}))
        self.dialog_change_user.actions.append(
            get_button(text="Нет", func_but=self._func_but, button_name={"id": user_id, "button_name": "change_not"}))

    def _settings_collum(self):
        self.coll.alignment = ft.MainAxisAlignment.CENTER
        self.coll.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.coll.scroll = ft.ScrollMode.AUTO
        self.coll.spacing = 20

        self.coll.controls.append(self.loader)

        self._settings_table()


    def _settings_table(self):
        self.table.columns.append(ft.DataColumn(label=ft.Text("id", size=25)))
        self.table.columns.append(ft.DataColumn(label=ft.Text("Email", size=25)))
        self.table.columns.append(ft.DataColumn(label=ft.Text("Role", size=25)))
        self.table.columns.append(ft.DataColumn(label=ft.Text("created_at", size=25)))
        self.table.columns.append(ft.DataColumn(label=ft.Text("", size=25)))

        self.cont.content = self.table

    def add_row(self, user: UserRead):
        row = ft.DataRow(cells=[
            ft.DataCell(ft.Text(str(user.id), size=25)),
            ft.DataCell(ft.Text(str(user.email), size=25)),
            ft.DataCell(ft.Text(user.role, size=25)),
            ft.DataCell(ft.Text(str(user.created_at), size=25)),
            ft.DataCell(ft.Row([get_button(text="", icon=ft.Icons.PERSON_ADD_ALT, func_but=self._func_but, button_name={"id": user.id, "button_name":"change_user"}),
                                get_button(text="", icon=ft.Icons.DELETE_FOREVER_OUTLINED, func_but=self._func_but, button_name={"id": user.id, "button_name":"del_user"})]))
        ])

        self.table.rows.append(row)
        if self._built:
            self.table.update()

    def _add_new_row(self):
        row = ft.DataRow(cells=[
            ft.DataCell(ft.Text("", size=25)),
            ft.DataCell(get_text_field(label="email", func_field=self._func_field, field_name="email", width=250)),
            ft.DataCell(ft.Dropdown(label="role", on_select=self._func_field, data="role", width=120, options=[
                ft.DropdownOption(key=UserRole.USER, text=UserRole.USER),
                ft.DropdownOption(key=UserRole.ADMIN, text=UserRole.ADMIN)
            ])),
            ft.DataCell(get_text_field(label="password", func_field=self._func_field, field_name="password", width=250, password=True)),
            ft.DataCell(get_button(text="", icon=ft.Icons.PERSON_ADD_ALT, func_but=self._func_but, button_name={"id": 0, "button_name":"add_user"}))
        ])
        self.table.rows.append(row)
        if self._built:
            self.table.update()

    def _func_field(self, e):
        ic(e.control.data, e.control.value)
        self.new_user[e.control.data] = e.control.value

    def _func_but(self, e):
        ic(e.control.data)
        match e.control.data["button_name"]:
            case "add_user":
                self.page.run_task(self._add_user)
            case "change_user":
                self.new_user = dict.fromkeys(self.new_user, None)
                self._settings_dialog_change_user(message=f"Изменить пользователя {e.control.data["id"]}", user_id=e.control.data["id"])
                self.page.show_dialog(self.dialog_change_user)
            case "change_yes":
                    self.page.pop_dialog()
                    self.page.run_task(self._change_user, user_id=e.control.data["id"])
            case "change_not":
                    self.page.pop_dialog()
            case "del_user":
                self._settings_dialog_del(message=f"Удалить пользователя {e.control.data["id"]}", user_id=e.control.data["id"])
                self.page.show_dialog(self.dialog_del)
            case "del_yes":
                self.page.pop_dialog()
                if self.state.user.id == e.control.data["id"]:
                    self.state.notify(message=f"Себя удалить нельзя", level=MessageLevel.WARNING)
                else:
                    self.page.run_task(self._dell_user, user_id=e.control.data["id"])
            case "del_not":
                 self.page.pop_dialog()

    async def _change_user(self, user_id):
        try:
            await self.api.patch_user(user=UserPatch(**self.new_user), user_id=user_id)
            await self._get_rows()
        except Exception as exc:
            self.state.notify(message=f"ошибка изменения пользователя: {exc}", level=MessageLevel.ERROR)

    async def _dell_user(self, user_id):
        try:
            await self.api.delete_user(user_id=user_id)
            await self._get_rows()
        except Exception as exc:
            self.state.notify(message=f"ошибка удаления пользователя: {exc}", level=MessageLevel.ERROR)

    async def _add_user(self):
        try:
            user = UserCreate(**self.new_user)
            self.new_user = dict.fromkeys(self.new_user, None)
            ic(user)
            await self.api.add_user(user)
            await self._get_rows()
        except ValidationError as exc:
            self.state.notify(message=f"ошибка добавления пользователя: {exc}", level=MessageLevel.ERROR)



    async def _get_rows(self):
       users = await self.api.get_users()
       ic(users)
       self.table.rows.clear()
       for user in users:
           self.add_row(user)
       self._add_new_row()

    def get_content(self):
        if not self._built:
            self._settings_collum()
            self._built = True
        self.page.run_task(self._get_rows)
        return self.cont