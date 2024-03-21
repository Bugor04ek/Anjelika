from flet import *

BG = '#041955'
FWG = '#97b4ff'
FG = '#3450a1'
PINK = '#eb06ff'


class Home(UserControl):
    def __init__(self, page):
        super().__init__()
        self.page = page

    def build(self):
        categories_card = Row(
            scroll='auto'
        )
        categories = ['Мультивайер']
        for i, category in enumerate(categories):
            categories_card.controls.append(
                Container(
                    on_click=lambda _: self.page.go('/multik'),
                    border_radius=20,
                    bgcolor=BG,
                    width=170,
                    height=110,
                    padding=15,
                    content=ElevatedButton(
                        content=Column(
                            controls=[
                                Text('40 Tasks'),
                                Text(category),
                                Container(
                                    width=160,
                                    height=5,
                                    bgcolor='white12',
                                    border_radius=20,
                                    padding=padding.only(right=i * 30),
                                    content=Container(
                                        bgcolor=PINK,
                                    ),
                                )
                            ]
                        )
                    )
                )
            )

        return Container(
            content=Column(
                controls=[
                    Row(alignment='spaceBetween',
                        controls=[
                            Container(
                                on_click=lambda e: shrink(e),
                                content=Icon(
                                    icons.MENU)),
                            Row(
                                controls=[
                                    Icon(icons.SEARCH),
                                    Icon(icons.NOTIFICATIONS_OUTLINED)
                                ],
                            ),
                        ],
                        ),
                    Container(height=20),
                    Text(
                        value='What\'s up, Olivia!'
                    ),
                    Text(
                        value='CATEGORIES'
                    ),
                    Container(
                        padding=padding.only(top=10, bottom=20, ),
                        content=categories_card
                    ),
                ],
            ),
        )
