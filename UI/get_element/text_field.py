import flet as ft

def get_text_field(*, label: str, field_name: str, width: int = 30000, password: bool = False, multiline: bool = False,
                    func_field) -> ft.TextField:

    return ft.TextField(
        label=label,
        data=field_name,
        width=width,
        password=password,
        can_reveal_password=password,
        border_radius=15,
        on_change=func_field,
        multiline=multiline,
        min_lines=1,
    )