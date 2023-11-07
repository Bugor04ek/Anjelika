import os
from datetime import datetime
from ast import slice
from typing import Type
import consts

import pandas as pd
from pandas.io.excel import ExcelWriter
from consts import *
import numpy as np

file_name = 'Заказы.xlsx'


def pack_cables(orders: list[Order], container_capacity: float):
    containers = []  # Список контейнеров

    for order in orders:
        placed = False
        for container in containers:
            if sum(item[2] for item in container) + order.full_bobbin[1] <= container_capacity:
                bobbin.add(order.full_bobbin[1])
                bobbin.append_order(order)
                container.append((order.account_number, bobbin, order.full_bobbin[1]))
                placed = True
                break
        if not placed:
            bobbin = Bobbin(order.full_bobbin[1], order.release_date)
            bobbin.append_order(order)
            containers.append([(order.account_number, bobbin, order.full_bobbin[1])])


    return len(containers)  # Возвращает количество используемых контейнеров


def sort_date(order):
    return order.release_date


def forming_file_with_groups(arr_orders: list[Order]):
    # Загрузка существующего файла Excel
    existing_file = 'output_class.xlsx'

    groups = max(order.num_group for order in arr_orders)  # максимальное число групп, для количества листов

    # Извлекаем заголовки столбцов
    headers = ["Номер счета", "Марка", "Дата выпуска", "Длина кабеля, км", "Километраж", "Время на мультике",
               "Длина стренг", "Барабаны (Кол-во полных катушек, Объем на частичной катушки)", "Параметры", "Группа",
               "Количество фильер"]
    data_res = []

    for group in range(groups + 1):
        # Инициализируем пустой список для хранения данных
        data = []
        # Извлекаем данные из PrettyTable и добавляем их в список
        for order in sorted(arr_orders, key=sort_date):
            if order.num_group == group:
                data.append(order)
                # data.append([order.account_number, order.mark, order.release_date, order.order_length,
                #              order.volume_bobbin, order.time_on_mult, order.length_strands, order.full_bobbin,
                #              order.group, order.num_group, order.spin])
                container_capacity = order.volume_bobbin

        pack_cables(data, container_capacity)
        data.append('')
        data_res.extend(data)
        data.clear()
        # Создаем DataFrame из списка данных и заголовков

    df = pd.DataFrame(data_res, columns=headers)

    mode = "w" if os.path.exists(existing_file) else "a"

    with ExcelWriter(existing_file, mode=mode, engine="openpyxl") as writer:
        df.to_excel(writer)


def create_orders():
    """
    Создание 2 таблиц:
    1. Основная, содержащая информацию о заказе
    2. Таблица с параметрами для вычисления "Длина куска 1 корзины"
    :return: result_table -- результирующая таблица с вычисленным столбцом "Длина куска 1 корзины"
    """
    # A - IDZak
    # B - Номер счета
    # C - Марка
    # D - Дата выпуска по заказу
    # E - Количество километров в производство
    # F - Количество жил
    # G - Перед мультиком -> d_mult = 2.08
    # H - Диаметр проволоки
    # J - Кол-во прядей
    # K - Кол-во проволок в пряди
    # L - Кол-во прядей доп
    # M - Кол-во проволок доп
    # N - Вид барабана
    # O - Количество заправок
    # P - Километраж масса VS Длина
    # Q - Время на мультике

    excel_data = pd.read_excel(file_name)
    excel_data['Дата выпуска по заказу'] = pd.to_datetime(excel_data['Дата выпуска по заказу'],
                                                          format='%d.%m.%Y').dt.date
    data = pd.DataFrame(excel_data).fillna(0)
    orders = list()

    for row in data.values:
        orders.append(Order(account_number=row[1], mark=row[2], release_date=row[3], order_length=row[4],
                            number_of_veins=row[5], diameter=row[7], number_of_strands=row[8], number_of_sliver=row[9],
                            wires_in_sliver=row[10], number_of_sliver_extra=row[11], wires_in_sliver_extra=row[12],
                            type_bobbin=row[13], volume_bobbin=row[15], time_on_mult=row[16]))

    return orders


if __name__ == '__main__':
    orders = create_orders()
    forming_file_with_groups(orders)

