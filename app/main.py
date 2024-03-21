from flet import *
from views import views_handler

BG = '#041955'
FWG = '#97b4ff'
FG = '#3450a1'
PINK = '#eb06ff'


def main(page: Page):

    def route_change(route):
        page.views.clear()
        page.views.append(
            views_handler(page)[page.route]
        )

    page.on_route_change = route_change
    page.go('/')


app(main)
