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

    print('Выберите сортировку:')
    print('0 - как есть')
    print('1 - по дате')
    k = int(input())
    if k == 1:
        check_list.bobbins = sorted(check_list.bobbins, key=check_list.sort_date)

    # ft.DataRow(
    #         cells=[
    #             ft.DataCell(ft.Text("John")),
    #             ft.DataCell(ft.Text("Smith")),
    #             ft.DataCell(ft.Text("43")),
    #         ]
    data = []
    for bobbin in check_list.bobbins:
        i = 0
        for order in bobbin.orders:
            if i == 0:
                data.append(row(cell=list(
                    map(lambda x: ft.DataCell(ft.Text(x)), [order.num_group, bobbin.number, order.account_number,
                                                            bobbin.volume, bobbin.max_volume,
                                                            bobbin.date_first_order]))))
                i += 1
            else:
                data.append(row(cell=list(map(lambda x: ft.DataCell(ft.Text(x)),
                                              [order.num_group, bobbin.number, order.account_number, '', '', '']))))

    return data


def main(page: ft.Page):
    header = ['Номер группы', 'Номер катушки', 'Номер счета', 'Намотка', 'Max намотка', 'Дата']
    row = ft.DataRow

    page.add(ft.DataTable(
        columns=list(map(lambda x: ft.DataColumn(ft.Text(x)), header)),
        rows=[output(row)]
        #     ft.DataRow(
        #         cells=[
        #             ft.DataCell(ft.Text("John")),
        #             ft.DataCell(ft.Text("Smith")),
        #             ft.DataCell(ft.Text("43")),
        #         ],
        #     ),
        #     ft.DataRow(
        #         cells=[
        #             ft.DataCell(ft.Text("Jack")),
        #             ft.DataCell(ft.Text("Brown")),
        #             ft.DataCell(ft.Text("19")),
        #         ],
        #     ),
        #     ft.DataRow(
        #         cells=[
        #             ft.DataCell(ft.Text("Alice")),
        #             ft.DataCell(ft.Text("Wong")),
        #             ft.DataCell(ft.Text("25")),
        #         ],
        #     ),
        # ],
    ))


if __name__ == '__main__':
    CreateTableClassAdaptive.main()
    ft.app(target=main)
