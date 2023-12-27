import time

import flet as ft
from consts import check_list
import CreateTableClassAdaptive


def output(row):
    """
    0 - как есть
    1 - по дате
    :return:
    """

    data = []
    for bobbin in check_list.bobbins:
        i = 0
        for order in bobbin.orders:
            if i == 0:
                data.append(row(cells=list(
                    map(lambda x: ft.DataCell(ft.Text(x)), [order.num_group, bobbin.number, order.account_number,
                                                            bobbin.volume, bobbin.max_volume,
                                                            bobbin.date_first_order]))))
                i += 1
            else:
                data.append(row(cells=list(map(lambda x: ft.DataCell(ft.Text(x)),
                                               [order.num_group, bobbin.number, order.account_number, '', '', '']))))

    return data


def main(page: ft.Page):
    header = ['Номер группы', 'Номер катушки', 'Номер счета', 'Намотка', 'Max намотка', 'Дата']
    row = ft.DataRow
    page.scroll = True
    page.add(ft.DataTable(
        show_checkbox_column=True,
        columns=list(map(lambda x: ft.DataColumn(ft.Text(x)), header)),
        rows=output(row)
    ))


if __name__ == '__main__':
    CreateTableClassAdaptive.main()
    ft.app(target=main)