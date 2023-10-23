import pandas as pd
from consts import *
import numpy as np

file_name = 'Заказы.xlsx'


def calculating_length_piece(table, table_param):
    """
    Процедура параметры из table_param и вычисляет длину меди потраченной с каждой корзины на мультике. Все
    вычисленные длины записываются во временный массив, а потом добавляются столбцом в table
    :param table: основная таблица со всеми параметрами
    :param table_param: таблица для вычислений длин куска
    """

    # временный массив для длины кусков
    res = []
    for row in table_param.rows:
        order_length = row[0]
        count_veins = int(row[1])
        count_strands = int(row[2])
        delays_vein = int(row[3])
        diameter = row[4]

        # суммарная длина проволочек
        total_length_delays = delays_vein * count_strands * count_veins * order_length

        length_piece = total_length_delays * (diameter ** 2 / d_mult ** 2)

        if row[5] != '0':
            count_veins_plus = int(row[5])
            count_strands_plus = row[6]
            delays_vein_plus = row[7]
            diameter_plus = row[8]

            # суммарная длина проволочек плюсовой части
            total_length_delays_plus = delays_vein_plus * count_strands_plus * count_veins_plus * order_length

            length_piece_plus = total_length_delays_plus * (diameter_plus ** 2 / d_mult ** 2)
        else:
            length_piece_plus = 0

        length_piece = round(length_piece + length_piece_plus, 3)

        res.append(length_piece)

    table.add_column('Длина куска 1 корзины', res)


def create_tables():
    """
        Создание 2 таблиц:
        1. Основная, содержащая информацию о заказе
        2. Таблица с параметрами для вычисления "Длина куска 1 корзины"
    :return: result_table -- результирующая таблица с вычисленным столбцом "Длина куска 1 корзины"
    """
    # B - Номер счета
    # C - Номенклатура ERP
    # D - Дата выпуска по заказу
    # E - Количество километров в производство
    # F - Диаметр проволоки (волочение), мм
    # J - На волочение, мм
    # N - Диаметр проволоки (волочение), мм

    excel_data = pd.read_excel(file_name, usecols="B:F, J, N")
    data = pd.DataFrame(excel_data).fillna(0)
    for row in data.values:
        first_param_table.add_row(row)

    # E - Количество километров в производство
    # G  - Количество жил
    # H  - Кол-во стренг
    # I  - Всего проволочек в 1 стренге
    # J - Диаметр проволоки на волочении
    # K - Количество жил плюсовой
    # L - Кол-во стренг плюсовой
    # M - Всего проволочек в1 стренге плюсовой
    # N - Диаметр проволоки (волочение), мм

    excel_data_calculation = pd.read_excel(file_name, usecols="E,G:N")
    data = pd.DataFrame(excel_data_calculation).fillna(0)
    for row in data.values:
        second_param_table.add_row(row)

    calculating_length_piece(first_param_table, second_param_table)

    return first_param_table
