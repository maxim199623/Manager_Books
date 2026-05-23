import flet as ft

def get_text_field(*, label: str, field_name: str = None, width: int = 30000, password: bool = False,
                   multiline: bool = False,input_filter=None,
                    func_field = None) -> ft.TextField:

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
        input_filter=input_filter,
        helper=" ",
        helper_max_lines=1,
        error_max_lines=2,
    )