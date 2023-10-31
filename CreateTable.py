import os
from datetime import datetime
from ast import slice
from typing import Type

import pandas as pd
from pandas.io.excel import ExcelWriter
from consts import *
import numpy as np

file_name = 'Заказы.xlsx'


def forming_file_with_groups(table):
    # Загрузка существующего файла Excel
    existing_file = 'output.xlsx'

    groups = max(row[9] for row in table.rows) # максимальное число групп, для количества листов

    # Извлекаем заголовки столбцов
    headers = table.field_names
    data = []

    for group in range(groups + 1):
        # Инициализируем пустой список для хранения данных

        # Извлекаем данные из PrettyTable и добавляем их в список
        for row in table.rows:
            if row[9] == group:
                data.append(row)
        else:
            data.append('')

        # Создаем DataFrame из списка данных и заголовков

    df = pd.DataFrame(data, columns=headers)

    with ExcelWriter(existing_file, mode="a" if os.path.exists(existing_file) else "w", engine="openpyxl") as writer:
        df.to_excel(writer)


def calculating_bobbin(length_strands, volume_bobbin, sliver):
    number_full_bobbin = length_strands // volume_bobbin # количество полных катушек в расчете на 1 прядь
    volume_half_bobbin = round(length_strands % volume_bobbin, 2)  # меди на неполной катушки на 1 прядь

    all_full_bobbin = number_full_bobbin * sliver
    all_half_bobbin = sliver  # = количеству прядей, т.к. последняя заправка

    #res = [[volume_bobbin for _ in range(sliver)] for _ in range(int(number_full_bobbin))]
    #res.append([volume_half_bobbin for _ in range(sliver)])

    return int(number_full_bobbin), volume_half_bobbin


def calculating(table, table_param):
    """
    Процедура параметры из table_param и вычисляет длину меди потраченной с каждой корзины на мультике. Все
    вычисленные длины записываются во временный массив, а потом добавляются столбцом в table
    :param table: основная таблица со всеми параметрами
    :param table_param: таблица для вычислений длин куска
    """

    # временные массивы для длины кусков, длины прядей и полных катушек
    res_length_piece = []
    res_length_strands = []
    res_full_bobbin = []
    groups_key = []
    groups_num = []
    sum_time = []

    for row in table_param.rows:
        # "Длина кабеля, км", "Количество жил", "Кол-во стренг" * -- длина стренги, количество прядей определяет
        # количество барабанов. Однако важно учитывать еще и кратность заказа полным намоткам (40 км заказ на барабан,
        # вместимостью 32 км, дает один полный барабан и один, вместимостью 8 км, но если прядей 4, то будет 4 полных
        # барабана, и 4 вместимостью 8 км).

        # 0 - Кол-во километров в производство
        # 1 - Кол-во жил
        # Перед мультиком -> d_mult = 2.08
        # 2 - Диаметр проволоки
        # 3 - Кол-во стренг (strand)
        # 4 - Кол-во прядей (sliver)
        # 5 - Кол-во проволок в пряди
        # 6 - Кол-во прядей доп
        # 7 - Кол-во проволок доп
        # 8 - Вид барабана
        # 9 - Километраж масса VS Длина
        # 10 - Время на мультике

        order_length = row[0]
        number_of_veins = int(row[1])
        diameter = row[2]
        number_of_strands = int(row[3])
        number_of_sliver = int(row[4])
        wires_in_sliver = int(row[5])
        number_of_sliver_extra = int(row[6])
        wires_in_sliver_extra = int(row[7])
        type_bobbin = row[8]

        key = (diameter, number_of_sliver, wires_in_sliver, number_of_sliver_extra, wires_in_sliver_extra, type_bobbin)

        if dict_key_group.get(key) is None:
            dict_key_group[key] = len(dict_key_group)

        groups_key.append(key)
        groups_num.append(dict_key_group[key])

        # суммарная длина проволочек
        total_length_delays = ((number_of_sliver * wires_in_sliver + number_of_sliver_extra * wires_in_sliver_extra)
                               * number_of_strands * number_of_veins * order_length)

        length_piece = round(total_length_delays * (diameter ** 2 / d_mult ** 2), 3)

        # длина заказа в расчете на одну прядь (весь заказ это length_strands *
        # (number_of_sliver + number_of_sliver_extra))
        length_strands = round((order_length * number_of_veins * number_of_strands), 2)

        # подсчет барабанов
        res_full_bobbin.append(calculating_bobbin(length_strands, row[9], number_of_sliver + number_of_sliver_extra))

        # Здесь был плюсовой, мб потом что-то доработаем

        # res_length_piece.append(length_piece)
        res_length_strands.append(length_strands)

    # table.add_column('Длина куска 1 корзины', res_length_piece)
    table.add_column('Длина стренг', res_length_strands)

    table.add_column('Барабаны (Кол-во полных катушек, Объем на частичной катушки)', res_full_bobbin)
    table.add_column('Параметры', groups_key)
    table.add_column('Группа', groups_num)
    table.align["Барабаны (Кол-во полных катушек, Объем на частичной катушки)"] = "r"


def create_tables():
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

    excel_data = pd.read_excel(file_name, usecols="B:E, P, Q")
    excel_data['Дата выпуска по заказу'] = pd.to_datetime(excel_data['Дата выпуска по заказу'], format='%d.%m.%Y').dt.date
    data = pd.DataFrame(excel_data).fillna(0)

    for row in data.values:
        main_table.add_row(row)

    # E - Количество километров в производство
    # F - Количество жил
    # G - Перед мультиком -> d_mult = 2.08
    # H - Диаметр проволоки
    # I - Количество стренг
    # J - Кол-во прядей
    # K - Кол-во проволок в пряди
    # L - Кол-во прядей доп
    # M - Кол-во проволок доп
    # N - Вид барабана
    # P - Километраж масса VS Длина
    # Q - Время на мультике

    excel_data_calculation = pd.read_excel(file_name, usecols="E, F, H:M, N, P:Q")
    data = pd.DataFrame(excel_data_calculation).fillna(0)
    for row in data.values:
        second_param_table.add_row(row)

    calculating(main_table, second_param_table)

    return main_table
