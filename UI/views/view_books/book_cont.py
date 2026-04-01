import base64

import flet as ft

def create_cont_book(*, cover=None, title="None", description="None", index=None
):
    """Создание контейнера с книгой"""
    if cover is None:
        cover = open("UI/views/view_books/cover.png", "rb").read()

    def click_book(e):
        """Нажатие на контейнер"""
        ic(e.data["index"])  # type: ignore
        #TODO

    def on_hover(e):
        """Наведение курсора на контейнер"""
        ic()
        ic(e)
        if e.data:
            ic()
            e.control.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLUE_GREY_300,

            )
            #e.control.scale = 1.02  # Лёгкое увеличение
            #e.control.animate_scale = ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
        else:
            e.control.shadow = None
            #e.control.scale = 1.0
            #e.control.animate_scale = ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
        e.control.update()

    def del_button(e):
        """Кнопка удаления книги"""
        ic()  # type: ignore
        #TODO

    def load_button(e):
        """Кнопка для скачивания книги"""
        ic(e.data["index"])  # type: ignore
        #TODO

    element = ft.Container(
        border=ft.border.all(2, ft.Colors.BLACK26),
        on_hover=on_hover,
        shadow=None,  # Начальное состояние без тени
        border_radius=10,
        margin=10,  # Начальные отступы
        padding=10,
        data={"index": index},
        on_click=lambda e: click_book(element),
        bgcolor = ft.Colors.ON_PRIMARY,
        content=ft.Row(
            controls=[
                ft.Image(
                    src=base64.b64encode(cover).decode("utf-8"),
                    height=200,
                    fit=ft.BoxFit.CONTAIN,
                ),
                ft.Column(
                    controls=[
                        ft.Container(
                            border=ft.border.all(2, ft.Colors.BLACK26),
                            padding=6,
                            content=ft.Text(title, color=ft.Colors.PRIMARY, size=20),
                            alignment=ft.Alignment.CENTER,
                            expand=True,
                        ),
                        ft.Container(
                            border=ft.border.all(2, ft.Colors.BLACK26),
                            padding=10,
                            content=ft.Text(description, color=ft.Colors.PRIMARY),
                            alignment=ft.Alignment.CENTER,
                            expand=True,
                            height=145,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True,
                ),
                ft.Container(
                    border=ft.border.all(2, ft.Colors.BLACK26),
                    height=200,
                    width=200,
                    content=ft.Column(
                        controls=[
                            ft.Button(
                                content="Скачать",
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                on_click=lambda e: load_button(element),
                                disabled=False,
                            ),
                            ft.Button(
                                content="Удалить",
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                on_click=lambda e: del_button(element),
                                disabled=False,
                            ),
                        ]
                    ),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            expand=True,
        ),
    )
    return element