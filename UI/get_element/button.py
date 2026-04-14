import flet as ft

def get_button(*, text: str, size:int = 15, button_name=None, width=None, icon=None, func_but=None):
    return ft.Button(
        content=ft.Text(text, size=size),
        on_click=func_but,
        data = button_name,
        width=width,
        expand=True,
        icon = icon,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            color={
                ft.ControlState.HOVERED: ft.Colors.SECONDARY,
                ft.ControlState.FOCUSED: ft.Colors.ON_PRIMARY_CONTAINER,
                ft.ControlState.DEFAULT: ft.Colors.PRIMARY,
            },
            bgcolor={
                ft.ControlState.FOCUSED: ft.Colors.PRIMARY_CONTAINER,
                ft.ControlState.DEFAULT: ft.Colors.ON_PRIMARY,
            },
        ),
    )