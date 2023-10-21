import pandas as pd
from consts import *
import numpy as np

file_name = 'Заказы.xlsx'


def merge_table(table1, table2):

    temp_table = PrettyTable()
    temp_table_rows = []
    counter = 0
    for i in table1.rows:
        i.extend(table2.rows[counter])
        counter += 1
        temp_table_rows.append(i)

    field = []
    field.extend(table1.field_names)
    field.extend(table2.field_names)

    temp_table_rows.field_names = field
    temp_table_rows.add_rows(temp_table_rows)

def calculating_length_piece(table):

    for row in table.rows:
        a = row

# 1 - Номер счета
# 2 - Номенклатура ERP
# 3 - Дата выпуска по заказу
# 4 - Диаметр проволоки (волочение), мм
# 5 - Диаметр проволоки на волочении
# 6 - Количество километров в производство

# excel_data = pd.read_excel(file_name, usecols=[1, 2, 3, 4, 5, 6])
# data = pd.DataFrame(excel_data)

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
data = pd.DataFrame(excel_data_calculation)
for row in data.values:
    second_param_table.add_row(row)

calculating_length_piece(second_param_table)
print("The content of the file is:\n", second_param_table)
