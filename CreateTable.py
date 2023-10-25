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
        # "Длина кабеля, км", "Количество жил", "Кол-во стренг" * -- длина стренги, количество прядей определяет
        # количество барабанов. Однако важно учитывать еще и кратность заказа полным намоткам (40 км заказ на барабан,
        # вместимостью 32 км, дает один полный барабан и один, вместимостью 8 км, но если прядей 4, то будет 4 полных
        # барабана, и 4 вместимостью 8 км).

        # 0 - Кол-во километров в производство
        # 1 - Кол-во жил
        # 2 - Перед мультиком -> d_mult = 2.08
        # 3 - Диаметр проволоки
        # 4 - Кол-во стренг
        # 5 - Кол-во прядей
        # 6 - Кол-во проволок в пряди
        # 7 - Кол-во прядей доп
        # 8 - Кол-во проволок доп

        order_length = row[0]
        number_of_veins = int(row[1])
        number_of_strands = int(row[4])
        number_of_sliver = int(row[5])
        wires_in_sliver = int(row[6])
        number_of_sliver_extra = int(row[7])
        wires_in_sliver_extra = int(row[8])
        diameter = row[3]

        # суммарная длина проволочек
        total_length_delays = ((number_of_sliver * wires_in_sliver + number_of_sliver_extra * wires_in_sliver_extra)
                               * number_of_strands * number_of_veins * order_length)

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
    # A - IDZak
    # B - Номер счета
    # C - Марка
    # D - Дата выпуска по заказу
    # E - Количество километров в производство
    # F - Количество жил
    # G - Перед мультиком -> d_mult = 2.08
    # H - Диаметр проволоки
    # N - Вид барабана
    # O - Количество заправок
    # P - Километраж масса VS Длина

    excel_data = pd.read_excel(file_name, usecols="A:H, N:P")
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

    print(main_table)

    excel_data_calculation = pd.read_excel(file_name, usecols="E, F, H:M")
    data = pd.DataFrame(excel_data_calculation).fillna(0)
    for row in data.values:
        second_param_table.add_row(row)

    calculating_length_piece(main_table, second_param_table)

    #return first_param_table
