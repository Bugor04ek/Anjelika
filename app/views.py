from flet import View, ThemeMode
from pages.home import Home


def views_handler(page):
    page.theme_mode = ThemeMode.DARK

    return {
        '/': View(
            '/',
            controls=[Home(page)]
        )
    }