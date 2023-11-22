import os
from ast import slice
from typing import Type
import consts

import pandas as pd
from pandas.io.excel import ExcelWriter
from consts import *
import numpy as np

from optimization.test import *

file_name = '../excel/Заказы.xlsx'


def pack_cables(orders: list[Order], container_capacity: float):
    check_list_temp = Check_List()

    for order in orders:
        placed = False
        for container in check_list_temp.bobbins:
            if container.volume + order.full_bobbin[1] <= container.max_volume:
                container.add(order.full_bobbin[1], order)
                placed = True
                break
        if not placed:  # Ветка в которой начинается новая намотка на катушку
            bobbin = Bobbin(order.full_bobbin[1], order.volume_bobbin, order.release_date, order)
            check_list_temp.append(bobbin)

    return check_list_temp  # Возвращает массив катушек, на которых сидят заказы


def formation_of_orders_in_the_date_range(orders: list[Order], date_range: int, groups_by_dates: dict):
    """
    Формирование заказов в диапазоне дат
    :return:
    """

    min_date = orders[0].release_date

    for i in range(1, len(orders)):
        if (orders[i].release_date - min_date).days > date_range:
            groups_by_dates[min_date] = orders[0:i]
            formation_of_orders_in_the_date_range(orders[i:], date_range, groups_by_dates)
            break
    else:
        groups_by_dates[min_date] = orders
        return


def sort_date(order):
    return order.release_date


def forming_file_with_groups(arr_orders: list[Order]):
    # Загрузка существующего файла Excel
    existing_file = 'excel/output_class.xlsx'

    groups = max(order.num_group for order in arr_orders)  # максимальное число групп, для количества листов

    # Извлекаем заголовки столбцов
    headers = ["Номер счета", "Марка", "Дата выпуска", "Длина кабеля, км", "Километраж", "Время на мультике",
               "Длина стренг", "Барабаны (Кол-во полных катушек, Объем на частичной катушки)", "Параметры", "Группа",
               "Количество фильер"]
    data_res = []
    bin = 0

    print("Хотите компоновать на катушки кабели в пределах даты?"
          "\n1. Да"
          "\n2. Нет")
    k = int(input())


    sort_orders = sorted(arr_orders, key=sort_date)
    for group in range(groups + 1):
        # Инициализируем пустой список для хранения данных
        data = []
        # Извлекаем данные из PrettyTable и добавляем их в список
        data = [order for order in sort_orders if order.num_group == group]

        container_capacity = data[0].volume_bobbin

        if k == 1:
            groups_by_dates = {}
            date_range = int(input('Введите диапазон дат: '))
            formation_of_orders_in_the_date_range(data, date_range, groups_by_dates)

            for key in groups_by_dates.keys():
                bin += create_solution(groups_by_dates[key], container_capacity, release_date=key)
            else:
                groups_by_dates.clear()
        else:
            bin += create_solution(data, container_capacity, release_date=data[0].release_date)

        data.append('')
        data_res.extend(data)
        data.clear()

    print("Всего катушек", bin)


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


#
def main():
    orders = create_orders()
    forming_file_with_groups(orders)
    # check_list.output_in_excel()

