import flet as ft
from flet import Colors as colors, Icons as icons

# Cores do Tema
BG_COLOR = "#1E1E2E"
SURFACE_COLOR = "#27273A"
PRIMARY_ACCENT = "#6C5DD3"
SECONDARY_TEXT = "#A0A0B0"
WHITE = "#FFFFFF"


class StatsCard(ft.Container):
    def __init__(self, titulo, valor, icon_name, icon_color):
        super().__init__(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon_name, color=icon_color, size=24),
                        padding=10,
                        bgcolor=colors.WHITE_10,
                        border_radius=10,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(valor, size=20, weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Text(titulo, size=12, color=SECONDARY_TEXT),
                        ],
                        spacing=2,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=15,
            bgcolor=SURFACE_COLOR,
            border_radius=15,
            width=200,
        )


class SelectionTile(ft.Container):
    def __init__(self, titulo, subtitulo, icon_name, on_click=None):
        super().__init__(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon_name, color=PRIMARY_ACCENT),
                        padding=10,
                        bgcolor=colors.WHITE_10,
                        border_radius=10,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(titulo, size=16, weight=ft.FontWeight.W_500, color=WHITE),
                            ft.Text(subtitulo, size=12, color=SECONDARY_TEXT),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(icons.CHEVRON_RIGHT, color=SECONDARY_TEXT),
                ],
            ),
            padding=15,
            bgcolor=SURFACE_COLOR,
            border_radius=12,
            on_click=on_click,
            ink=True,
        )


class PrimaryButton(ft.Container):
    """Botao personalizado usando Container + Row (compativel com Flet 0.80+)."""
    def __init__(self, texto, on_click, icon=None, width=None):
        row_controls = []
        if icon:
            row_controls.append(ft.Icon(icon, color=WHITE, size=18))
        row_controls.append(ft.Text(texto, color=WHITE, size=14, weight=ft.FontWeight.BOLD))

        super().__init__(
            content=ft.Row(
                controls=row_controls,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=PRIMARY_ACCENT,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            on_click=on_click,
            ink=True,
            width=width,
        )


class LogItem(ft.Row):
    def __init__(self, mensagem, nivel="info"):
        icon = icons.INFO_ROUNDED
        color = colors.BLUE_200

        if nivel == "error":
            icon = icons.ERROR_ROUNDED
            color = colors.RED_400
        elif nivel == "success":
            icon = icons.CHECK_CIRCLE_ROUNDED
            color = colors.GREEN_400
        elif nivel == "warning":
            icon = icons.WARNING_ROUNDED
            color = colors.ORANGE_400

        super().__init__(
            controls=[
                ft.Icon(icon, color=color, size=14),
                ft.Text(mensagem, size=12, color=SECONDARY_TEXT, font_family="Consolas"),
            ],
            spacing=10,
        )
