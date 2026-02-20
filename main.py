import flet as ft
from src.ui.app import DarkoGramApp

def main(page: ft.Page):
    app = DarkoGramApp(page)

if __name__ == "__main__":
    ft.app(target=main)
